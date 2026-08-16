"""What bringing a stage home costs, in propellant carried uphill.

See docs/physics-reference.md section 2.7.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from rocketry.constants import G0
from rocketry.tsiolkovsky import mass_ratio


@dataclass(frozen=True, slots=True)
class Burn:
    """One propulsive manoeuvre.

    Attributes:
        delta_v: Velocity change of the manoeuvre, m/s.
        isp: Specific impulse achieved during it, seconds. Landing burns run
            deeply throttled and should use a lower value than the engine's
            rating.
        label: Optional human-readable name, used by the UI.
    """

    delta_v: float
    isp: float
    label: str = ""


def recovery_propellant(dry_mass: float, burns: Sequence[Burn]) -> float:
    """Propellant a stage must hold back to perform a sequence of burns.

    Burns compose multiplicatively, and each one has to lift the propellant for
    every burn that comes after it. Pass them in reverse chronological order,
    last burn first, which is how the maths naturally unwinds.

    Args:
        dry_mass: Stage mass once everything is burnt, tonnes.
        burns: Manoeuvres in reverse order, last burn first.

    Returns:
        Propellant that must be reserved, tonnes.
    """
    ratio = 1.0
    for burn in burns:
        ratio *= mass_ratio(burn.delta_v, burn.isp)
    return dry_mass * (ratio - 1.0)


def mass_at_separation(dry_mass: float, burns: Sequence[Burn]) -> float:
    """Total stage mass at separation, including everything it needs to get home.

    Args:
        dry_mass: Stage mass once everything is burnt, tonnes.
        burns: Recovery manoeuvres in reverse order, last burn first.

    Returns:
        Stage mass at the moment of separation, tonnes.
    """
    return dry_mass + recovery_propellant(dry_mass, burns)


def landing_delta_v(
    residual_velocity: float, burn_seconds: float, throttle_penalty: float = 0.0
) -> float:
    """Build a landing budget from its parts rather than quoting one number.

    A landing burn pays for three things: killing the speed it arrives with,
    fighting gravity for the whole duration of the burn, and running engines
    deeply throttled where they are least efficient.

    Args:
        residual_velocity: Speed at the start of the landing burn, m/s.
        burn_seconds: Duration of the burn, seconds.
        throttle_penalty: Extra velocity budget covering throttling and
            manoeuvring inefficiency, m/s.

    Returns:
        Total landing budget, m/s.
    """
    return residual_velocity + G0 * burn_seconds + throttle_penalty
