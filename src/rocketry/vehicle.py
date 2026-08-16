"""Analyse a complete vehicle from the library: what each stage contributes.

This is the bridge between the data library and the physics primitives. Given a
vehicle key and a payload, it walks the stack bottom-up and reports what every
stage does, including what a reusable stage spends on coming home.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from rocketry.library import Library
from rocketry.models import Stage, Vehicle
from rocketry.reuse import recovery_propellant
from rocketry.tsiolkovsky import delta_v


@dataclass(frozen=True, slots=True)
class StageAnalysis:
    """What one stage contributes to a flight.

    Attributes:
        stage: The stage analysed.
        mass_above_t: Everything this stage must lift, tonnes.
        ignition_mass_t: Mass at ignition, tonnes.
        burnout_mass_t: Mass at burnout, tonnes.
        recovery_reserve_t: Propellant held back to come home, tonnes.
        ascent_propellant_t: Propellant actually spent accelerating, tonnes.
        delta_v: Velocity this stage contributes, m/s.
    """

    stage: Stage
    mass_above_t: float
    ignition_mass_t: float
    burnout_mass_t: float
    recovery_reserve_t: float
    ascent_propellant_t: float
    delta_v: float

    @property
    def reuse_cost_fraction(self) -> float:
        """Share of this stage's propellant spent on recovery rather than ascent."""
        total = self.stage.propellant_t
        return self.recovery_reserve_t / total if total else 0.0


@dataclass(frozen=True, slots=True)
class VehicleAnalysis:
    """A whole flight, stage by stage.

    Attributes:
        key: Vehicle key.
        name: Vehicle name.
        payload_t: Payload carried, tonnes.
        fairing_t: Payload fairing mass, tonnes. Zero when the vehicle has none.
        stages: Per-stage results, bottom-up.
    """

    key: str
    name: str
    payload_t: float
    fairing_t: float
    stages: tuple[StageAnalysis, ...]

    @property
    def liftoff_mass_t(self) -> float:
        """Fully fuelled stack mass at liftoff, tonnes."""
        return self.stages[0].ignition_mass_t if self.stages else 0.0

    @property
    def total_delta_v(self) -> float:
        """Ideal velocity the whole stack can produce, m/s."""
        return sum(result.delta_v for result in self.stages)

    @property
    def first_stage_share(self) -> float:
        """Fraction of the total velocity the first stage contributes.

        Theory says roughly half is optimal for identical stages, and slightly
        less than half when the first stage has the lower-efficiency engines.
        Real vehicles run well below that.
        """
        total = self.total_delta_v
        return self.stages[0].delta_v / total if total and self.stages else 0.0

    @property
    def payload_fraction(self) -> float:
        """Payload as a fraction of liftoff mass."""
        return self.payload_t / self.liftoff_mass_t if self.liftoff_mass_t else 0.0

    @property
    def mass_to_orbit_t(self) -> float:
        """Everything that arrives: payload, the last stage, and what it still holds.

        Four things arrive: the payload, the stage's own structure, the
        propellant it could not use, and the propellant it is holding back to
        come home. The last of those is 38 t on Starship and is unambiguously in
        orbit. The fairing is not among them, because it was released on the way
        up.

        That is precisely what the last stage weighs when its engines stop, so
        this reads that rather than adding the four up again. The two used to
        differ by the fairing, and this is the one place the claim "the mass
        reaching orbit barely moves" is expressed.

        Returns:
            Mass reaching orbit, tonnes.
        """
        return self.stages[-1].burnout_mass_t if self.stages else 0.0


def analyse(library: Library, vehicle_key: str, payload_t: float | None = None) -> VehicleAnalysis:
    """Work out what each stage of a vehicle contributes.

    Args:
        library: The rocket library.
        vehicle_key: Vehicle to analyse.
        payload_t: Payload to carry, tonnes. Defaults to the operator's
            published claim, which is a claim being tested and not an input to
            trust.

    Returns:
        The stage-by-stage analysis.

    Raises:
        ValueError: If the vehicle has no payload figure and none was given.
    """
    vehicle = library.vehicle(vehicle_key)
    payload = payload_t if payload_t is not None else vehicle.payload_leo_t
    if payload is None:
        raise ValueError(f"vehicle {vehicle_key!r} has no payload figure; pass payload_t")

    return _analyse_stages(vehicle, library.stages_of(vehicle_key), payload)


def _analyse_stages(
    vehicle: Vehicle, stages: list[Stage], payload: float
) -> VehicleAnalysis:
    """Walk an already-resolved stack bottom-up.

    **The fairing is released when the last stage ignites.** Every stage below it
    lifts it; the stage that reaches orbit does not. Carrying it the whole way
    used to cost Falcon 9 1.7 t of payload, which is out of all proportion to its
    1.9 t because it is shed when the upper stage is nearly empty.

    Real fairings go a little later than modelled here: Falcon 9 sheds its about
    35 s into a 360 s second-stage burn. Charging the last stage for that 10 % of
    its burn moves the solved payload by 0.03 t, or 0.16 %, so the extra
    parameter it would take to say so per vehicle buys nothing at this project's
    few-per-cent precision. The three-stage vehicles here shed theirs before
    upper-stage ignition anyway, which is exactly what this models.

    Args:
        vehicle: The vehicle being analysed.
        stages: Its stages, in launch order, already resolved and possibly
            altered.
        payload: Payload to carry, tonnes.

    Returns:
        The stage-by-stage analysis.
    """
    results: list[StageAnalysis] = []
    last_index = len(stages) - 1
    for index, stage in enumerate(stages):
        above = payload + sum(s.wet_mass_t for s in stages[index + 1 :])
        if index < last_index:
            above += vehicle.fairing_t
        reserve = _recovery_reserve(stage)
        ignition = above + stage.wet_mass_t
        burnout = above + stage.dry_mass_t + stage.residual_propellant_t + reserve
        results.append(
            StageAnalysis(
                stage=stage,
                mass_above_t=above,
                ignition_mass_t=ignition,
                burnout_mass_t=burnout,
                recovery_reserve_t=reserve,
                ascent_propellant_t=ignition - burnout,
                delta_v=delta_v(ignition, burnout, stage.isp_ascent_s),
            )
        )
    return VehicleAnalysis(
        key=vehicle.key,
        name=vehicle.name,
        payload_t=payload,
        fairing_t=vehicle.fairing_t,
        stages=tuple(results),
    )


def solve_payload(
    library: Library, vehicle_key: str, target_delta_v: float, tolerance: float = 1e-6
) -> float:
    """Find the payload a vehicle can carry for a given mission budget.

    Args:
        library: The rocket library.
        vehicle_key: Vehicle to solve.
        target_delta_v: Velocity the whole stack must produce, m/s.
        tolerance: Convergence tolerance on payload, tonnes.

    Returns:
        Payload, tonnes. Negative means the vehicle cannot reach this budget
        even empty, which is a real answer worth showing rather than an error.
    """
    low, high = -500.0, 10_000.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if analyse(library, vehicle_key, mid).total_delta_v > target_delta_v:
            low = mid
        else:
            high = mid
        if high - low < tolerance:
            break
    return 0.5 * (low + high)


def altered(stage: Stage, changes: Mapping[str, object]) -> Stage:
    """A copy of a stage with some fields changed, validated as if newly loaded.

    Rebuilt rather than copied. ``model_copy(update=...)`` writes fields without
    validating them, which let this seam accept a negative dry mass, a zero
    specific impulse, and worst of all a misspelled field name, which was
    silently ignored so the caller got the unchanged baseline back and nothing
    about the answer looked wrong.

    Args:
        stage: The stage to base the copy on.
        changes: Fields to change.

    Returns:
        The altered stage.

    Raises:
        ValueError: If the result is not a valid stage, including when a field
            name is not one a stage has. `Stage` forbids extra fields, so a typo
            is rejected here rather than quietly doing nothing.
    """
    return Stage(**{**stage.model_dump(), **changes})


def _recovery_reserve(stage: Stage) -> float:
    """Propellant a stage must hold back for its recovery burns.

    Args:
        stage: The stage.

    Returns:
        Reserved propellant, tonnes. Zero for expendable stages.
    """
    if stage.recovery is None:
        return 0.0
    return recovery_propellant(stage.dry_mass_t, list(stage.recovery.burns))


LEO_MISSION_DELTA_V = 9404.0
"""Velocity a stack must produce to reach low Earth orbit, m/s.

Calibrated in docs/physics-reference.md section 3.3 and cross-checked against
Falcon 9 and the Space Shuttle, both of which land inside the normal 9300 to
9600 m/s band at their published payloads.
"""


@dataclass(frozen=True, slots=True)
class Scenario:
    """A vehicle with some of its stages altered, ready to be asked questions.

    Two different questions get asked of the same vehicle and they are not
    interchangeable:

    - *What velocity does it produce carrying this payload?* Use `at_payload`.
    - *What payload can it carry on this mission?* Use `solve_payload`.

    Confusing the two is easy and produces answers that look plausible, so they
    are separate methods rather than one function with a flag.

    Attributes:
        vehicle: The vehicle being modelled.
        stages: Its stages in launch order, already resolved and possibly
            altered.
    """

    vehicle: Vehicle
    stages: tuple[Stage, ...]

    def at_payload(self, payload_t: float) -> VehicleAnalysis:
        """Analyse this vehicle carrying a given payload.

        Args:
            payload_t: Payload, tonnes.

        Returns:
            The stage-by-stage analysis.
        """
        return _analyse_stages(self.vehicle, list(self.stages), payload_t)

    def solve_payload(self, target_delta_v: float = LEO_MISSION_DELTA_V) -> float:
        """Find the payload this vehicle can carry on a given mission.

        Args:
            target_delta_v: Velocity the whole stack must produce, m/s.

        Returns:
            Payload, tonnes. A negative result is meaningful and is returned
            rather than clamped: it says the vehicle falls short of this mission
            even with an empty payload bay, and by how much.
        """
        low, high = self._lightest_payload(), 10_000.0
        if self.at_payload(high).total_delta_v > target_delta_v:
            return high
        for _ in range(200):
            mid = 0.5 * (low + high)
            if self.at_payload(mid).total_delta_v > target_delta_v:
                low = mid
            else:
                high = mid
            if high - low < 1e-6:
                break
        return 0.5 * (low + high)

    def reaches(self, target_delta_v: float = LEO_MISSION_DELTA_V) -> bool:
        """Whether this vehicle can do the mission at all, carrying nothing.

        Args:
            target_delta_v: Velocity the whole stack must produce, m/s.

        Returns:
            True if an empty payload bay is enough.
        """
        return self.at_payload(0.0).total_delta_v >= target_delta_v

    def _lightest_payload(self) -> float:
        """Most negative payload the mass bookkeeping still stays positive at.

        A payload cannot really be negative. Allowing it here is a modelling
        convenience that lets the solver express "short by this much" instead of
        silently bottoming out at zero.

        Returns:
            Lower bound for the payload search, tonnes.
        """
        last = self.stages[-1]
        floor = last.dry_mass_t + last.residual_propellant_t + last.recovery_reserve_t
        return -floor + 0.001


def scenario(
    library: Library, vehicle_key: str, **overrides: Mapping[str, object]
) -> Scenario:
    """Build a scenario from the library, optionally altering some stages.

    Args:
        library: The rocket library.
        vehicle_key: Vehicle to model.
        **overrides: Stage key to the fields to change on it.

    Returns:
        The scenario.

    Raises:
        ValueError: If a named stage is not part of this vehicle.
    """
    vehicle = library.vehicle(vehicle_key)
    for stage_key in overrides:
        if stage_key not in vehicle.stages:
            flying = ", ".join(vehicle.stages)
            raise ValueError(
                f"stage {stage_key!r} does not fly on {vehicle_key!r}. It has: {flying}"
            )
    stages = tuple(
        altered(library.stage(key), overrides[key]) if key in overrides else library.stage(key)
        for key in vehicle.stages
    )
    return Scenario(vehicle=vehicle, stages=stages)


def with_stage(
    library: Library, vehicle_key: str, stage_key: str, **changes: object
) -> VehicleAnalysis:
    """Re-analyse a vehicle with one of its stages altered.

    The seam for every "what if" the app asks: what if this booster came home a
    different way, what if this ship were lighter. The library itself is never
    modified, so two scenarios on the same page cannot interfere.

    Args:
        library: The rocket library.
        vehicle_key: Vehicle to analyse.
        stage_key: Which of its stages to alter.
        **changes: Fields to override on that stage.

    Returns:
        The analysis of the altered vehicle.

    Raises:
        ValueError: If that stage is not part of this vehicle, which is almost
            always a typo rather than an intention.
    """
    vehicle = library.vehicle(vehicle_key)
    if stage_key not in vehicle.stages:
        flying = ", ".join(vehicle.stages)
        raise ValueError(f"stage {stage_key!r} does not fly on {vehicle_key!r}. It has: {flying}")

    changed = altered(library.stage(stage_key), changes)
    stages = [changed if key == stage_key else library.stage(key) for key in vehicle.stages]
    return _analyse_stages(vehicle, stages, vehicle.payload_leo_t or 0.0)
