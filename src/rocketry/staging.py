"""Where to split a two-stage rocket, and what the split is worth.

See docs/physics-reference.md sections 2.6, 3.7 and 3.8.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, field

from rocketry.constants import KMH_TO_MS
from rocketry.reuse import Burn, mass_at_separation
from rocketry.scaling import LINEAR, scaled_dry_mass
from rocketry.tsiolkovsky import delta_v, final_mass, mass_ratio


@dataclass(frozen=True, slots=True)
class TwoStageResult:
    """Outcome of solving a two-stage vehicle for its payload.

    Attributes:
        liftoff_mass: Fully fuelled stack mass, tonnes.
        booster_dry: Booster mass with empty tanks, tonnes.
        booster_delta_v: Velocity the booster contributes, m/s.
        booster_recovery_propellant: Propellant the booster holds back, tonnes.
        ship_dry: Upper stage mass with empty tanks, tonnes.
        ship_delta_v: Velocity the upper stage contributes, m/s.
        mass_in_orbit: Everything arriving at the target, tonnes.
        payload: Useful cargo, tonnes.
    """

    liftoff_mass: float
    booster_dry: float
    booster_delta_v: float
    booster_recovery_propellant: float
    ship_dry: float
    ship_delta_v: float
    mass_in_orbit: float
    payload: float

    @property
    def booster_delta_v_share(self) -> float:
        """Fraction of total velocity the booster contributes, 0 to 1."""
        total = self.booster_delta_v + self.ship_delta_v
        return self.booster_delta_v / total if total else 0.0

    @property
    def payload_fraction(self) -> float:
        """Payload as a fraction of liftoff mass."""
        return self.payload / self.liftoff_mass if self.liftoff_mass else 0.0


def two_stage_payload(
    *,
    booster_propellant: float,
    ship_propellant: float,
    scaling_exponent: float = LINEAR,
    booster_scaling_exponent: float = LINEAR,
    booster_reference_dry: float = 300.0,
    booster_reference_propellant: float = 3650.0,
    ship_reference_dry: float = 220.0,
    ship_reference_propellant: float = 1600.0,
    booster_isp: float = 340.0,
    ship_isp: float = 365.0,
    total_delta_v: float = 9404.0,
    recovery_ratio: float = 1.10,
    ship_residual_reference: float = 40.0,
) -> TwoStageResult:
    """Solve a two-stage vehicle for the payload it delivers.

    The velocity split between the stages is not chosen; it falls out. Both
    stages must together supply `total_delta_v`, and the booster's share is
    fixed by how much propellant it has and how much it must hold back to come
    home. Solving that constraint gives the mass arriving in orbit, and the
    payload is whatever is left after the upper stage pays for itself.

    Defaults reproduce the source article's Starship model. Change
    `booster_propellant` and `ship_propellant` to explore other configurations.

    Args:
        booster_propellant: Booster propellant capacity, tonnes.
        ship_propellant: Upper stage propellant capacity, tonnes.
        scaling_exponent: How upper stage dry mass grows with its propellant.
            See `rocketry.scaling`.
        booster_scaling_exponent: Same, for the booster.
        booster_reference_dry: Known booster dry mass to scale from, tonnes.
        booster_reference_propellant: Propellant load of that booster, tonnes.
        ship_reference_dry: Known upper stage dry mass to scale from, tonnes.
        ship_reference_propellant: Propellant load of that upper stage, tonnes.
        booster_isp: Flight-average booster specific impulse, seconds.
        ship_isp: Flight-average upper stage specific impulse, seconds.
        total_delta_v: Mission budget both stages must supply together, m/s.
        recovery_ratio: Propellant the booster holds back per tonne of its own
            dry mass, tonnes per tonne.
        ship_residual_reference: Propellant still aboard the reference upper
            stage on arrival, tonnes. Scaled with propellant load.

    Returns:
        The solved vehicle.

    Raises:
        ValueError: If the booster cannot even lift itself, which means the
            recovery reserve exceeds its propellant load.
    """
    booster_dry = scaled_dry_mass(
        reference_dry=booster_reference_dry,
        reference_propellant=booster_reference_propellant,
        propellant=booster_propellant,
        exponent=booster_scaling_exponent,
    )
    ship_dry = scaled_dry_mass(
        reference_dry=ship_reference_dry,
        reference_propellant=ship_reference_propellant,
        propellant=ship_propellant,
        exponent=scaling_exponent,
    )
    reserved = recovery_ratio * booster_dry
    burnt = booster_propellant - reserved
    if burnt <= 0:
        raise ValueError(
            f"booster holds back {reserved:.0f} t of its {booster_propellant:.0f} t, "
            "leaving nothing to launch with"
        )
    fixed_mass = booster_propellant + booster_dry + ship_propellant

    def stage_velocities(mass_in_orbit: float) -> tuple[float, float]:
        liftoff = fixed_mass + mass_in_orbit
        return (
            delta_v(liftoff, liftoff - burnt, booster_isp),
            delta_v(mass_in_orbit + ship_propellant, mass_in_orbit, ship_isp),
        )

    def shortfall(mass_in_orbit: float) -> float:
        return sum(stage_velocities(mass_in_orbit)) - total_delta_v

    mass_in_orbit = _bisect(shortfall, 0.001, 10 * fixed_mass)
    liftoff = fixed_mass + mass_in_orbit
    booster_dv, ship_dv = stage_velocities(mass_in_orbit)
    residual = ship_residual_reference * ship_propellant / ship_reference_propellant

    return TwoStageResult(
        liftoff_mass=liftoff,
        booster_dry=booster_dry,
        booster_delta_v=booster_dv,
        booster_recovery_propellant=reserved,
        ship_dry=ship_dry,
        ship_delta_v=ship_dv,
        mass_in_orbit=mass_in_orbit,
        payload=mass_in_orbit - ship_dry - residual,
    )


@dataclass(frozen=True, slots=True)
class StagingModel:
    """A rocket whose staging velocity can be moved, with everything else fixed.

    Defaults reproduce the Starship stack, so `payload_at(6000)` is roughly what
    it flies today and the optimum is elsewhere. Used for the sweep in
    docs/physics-reference.md section 3.7.

    Attributes:
        liftoff_mass: Fully fuelled stack mass, tonnes.
        booster_dry: Booster dry mass, held fixed across the sweep, tonnes.
        booster_isp: Flight-average booster specific impulse, seconds.
        ship_isp: Flight-average upper stage specific impulse, seconds.
        total_delta_v: Mission budget both stages supply together, m/s.
        reference_staging_kmh: Staging speed at which the booster supplies
            `reference_booster_delta_v`, km/h.
        reference_booster_delta_v: Booster velocity at the reference staging
            speed, m/s.
        ship_inert_per_propellant: Upper stage inert mass, including its landing
            propellant, per tonne of its own propellant.
        entry_speed_kmh: Speed the booster must slow to before reentry, km/h.
        brake_isp: Specific impulse of the braking burn, seconds.
        landing: The booster's landing burn.
    """

    liftoff_mass: float = 5850.0
    booster_dry: float = 300.0
    booster_isp: float = 340.0
    ship_isp: float = 365.0
    total_delta_v: float = 9404.0
    reference_staging_kmh: float = 6000.0
    reference_booster_delta_v: float = 2796.0
    ship_inert_per_propellant: float = 250.0 / 1600.0
    entry_speed_kmh: float = 5300.0
    brake_isp: float = 350.0
    landing: Burn = field(default_factory=lambda: Burn(delta_v=500.0, isp=327.0, label="landing"))

    def booster_delta_v_at(self, staging_speed_kmh: float) -> float:
        """Velocity the booster must supply to stage at a given speed.

        Args:
            staging_speed_kmh: Speed at separation, km/h.

        Returns:
            Booster velocity contribution, m/s.
        """
        extra = (staging_speed_kmh - self.reference_staging_kmh) * KMH_TO_MS
        return self.reference_booster_delta_v + extra

    def booster_mass_at_separation(self, staging_speed_kmh: float) -> float:
        """Booster mass at separation, including everything it needs to get home.

        Args:
            staging_speed_kmh: Speed at separation, km/h.

        Returns:
            Booster mass at separation, tonnes.
        """
        brake_dv = max(0.0, (staging_speed_kmh - self.entry_speed_kmh) * KMH_TO_MS)
        burns = [self.landing, Burn(delta_v=brake_dv, isp=self.brake_isp, label="entry braking")]
        return mass_at_separation(self.booster_dry, burns)

    def payload_at(self, staging_speed_kmh: float) -> float:
        """Payload delivered when the stages separate at a given speed.

        Args:
            staging_speed_kmh: Speed at separation, km/h.

        Returns:
            Payload, tonnes. Negative means this split cannot reach orbit at all.
        """
        booster_dv = self.booster_delta_v_at(staging_speed_kmh)
        ship_dv = self.total_delta_v - booster_dv
        after_ascent = final_mass(self.liftoff_mass, booster_dv, self.booster_isp)
        available = after_ascent - self.booster_mass_at_separation(staging_speed_kmh)
        if available <= 0 or ship_dv <= 0:
            return float("-inf")
        in_orbit = final_mass(available, ship_dv, self.ship_isp)
        ship_inert = self.ship_inert_per_propellant * (available - in_orbit)
        return in_orbit - ship_inert


def staging_sweep(
    model: StagingModel, low_kmh: float = 6000.0, high_kmh: float = 16000.0, step_kmh: float = 500.0
) -> list[tuple[float, float]]:
    """Payload as a function of staging speed.

    Args:
        model: The vehicle to sweep.
        low_kmh: Lowest staging speed to try, km/h.
        high_kmh: Highest staging speed to try, km/h.
        step_kmh: Grid spacing, km/h.

    Returns:
        Pairs of staging speed in km/h and payload in tonnes, in ascending
        order of speed. Configurations that cannot reach orbit are omitted.
    """
    results: list[tuple[float, float]] = []
    steps = round((high_kmh - low_kmh) / step_kmh)
    for i in range(steps + 1):
        speed = low_kmh + i * step_kmh
        payload = model.payload_at(speed)
        if math.isfinite(payload):
            results.append((speed, payload))
    return results


def optimal_staging_speed(
    model: StagingModel, low_kmh: float = 6000.0, high_kmh: float = 16000.0
) -> float:
    """Staging speed that maximises payload.

    Args:
        model: The vehicle to optimise.
        low_kmh: Lowest staging speed to consider, km/h.
        high_kmh: Highest staging speed to consider, km/h.

    Returns:
        Best staging speed, km/h, resolved to 10 km/h.

    Raises:
        ValueError: If no staging speed in the range can reach orbit.
    """
    sweep = staging_sweep(model, low_kmh, high_kmh, step_kmh=10.0)
    if not sweep:
        raise ValueError("no staging speed in this range reaches orbit")
    return max(sweep, key=lambda pair: pair[1])[0]


def optimal_delta_v_split(
    *, isp: float, structural_coefficient: float, total_delta_v: float
) -> float:
    """Best share of the velocity budget for the first stage of two identical stages.

    The classical result: when both stages have the same engine efficiency and
    the same structural quality, payload is maximised by splitting the velocity
    equally. Real stages differ, and then the better engine and the better
    structure should each do more of the work.

    Args:
        isp: Specific impulse of both stages, seconds.
        structural_coefficient: Stage dry mass divided by stage total mass,
            the same for both stages.
        total_delta_v: Combined velocity budget, m/s.

    Returns:
        First stage share of the total velocity, 0 to 1.
    """

    def payload_fraction(share: float) -> float:
        top = 1.0
        for dv in (total_delta_v * (1.0 - share), total_delta_v * share):
            ratio = mass_ratio(dv, isp)
            denominator = 1.0 - structural_coefficient * ratio
            if denominator <= 0:
                return 0.0
            top = top * ratio * (1.0 - structural_coefficient) / denominator
        return 1.0 / top

    best_share, best_value = 0.5, -1.0
    for i in range(1, 1000):
        share = i / 1000.0
        value = payload_fraction(share)
        if value > best_value:
            best_share, best_value = share, value
    return best_share


def _bisect(
    f: Callable[[float], float], low: float, high: float, iterations: int = 200
) -> float:
    """Find a root of a monotonic function by bisection.

    Args:
        f: Function whose root is sought.
        low: Lower bracket.
        high: Upper bracket.
        iterations: Number of halvings.

    Returns:
        Approximate root.

    Raises:
        ValueError: If the bracket does not contain a sign change.
    """
    f_low, f_high = f(low), f(high)
    if f_low * f_high > 0:
        raise ValueError("bracket does not contain a solution")
    for _ in range(iterations):
        mid = 0.5 * (low + high)
        f_mid = f(mid)
        if f_low * f_mid <= 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return 0.5 * (low + high)
