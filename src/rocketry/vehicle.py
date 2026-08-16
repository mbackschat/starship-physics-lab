"""Analyse a complete vehicle from the library: what each stage contributes.

This is the bridge between the data library and the physics primitives. Given a
vehicle key and a payload, it walks the stack bottom-up and reports what every
stage does, including what a reusable stage spends on coming home.
"""

from dataclasses import dataclass

from rocketry.library import Library
from rocketry.models import Stage
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
        """Everything that arrives, payload plus the last stage and its residuals."""
        if not self.stages:
            return 0.0
        last = self.stages[-1]
        return self.payload_t + last.stage.dry_mass_t + last.stage.residual_propellant_t


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

    stages = library.stages_of(vehicle_key)
    results: list[StageAnalysis] = []
    for index, stage in enumerate(stages):
        above = payload + vehicle.fairing_t + sum(s.wet_mass_t for s in stages[index + 1 :])
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
