"""Orbital velocity, launch site geometry and the Earth-rotation bonus.

See docs/physics-reference.md section 2.5.
"""

import math

from rocketry.constants import MU_EARTH, R_EARTH_M, V_EQUATORIAL


class InclinationUnreachableError(ValueError):
    """Raised when a target inclination cannot be reached directly from a launch site.

    A rocket cannot reach an orbit whose inclination is lower than its launch
    latitude without an expensive plane change, because its starting position is
    already tilted that far off the equator.
    """


def orbital_velocity(altitude_m: float) -> float:
    """Speed needed for a circular orbit at a given altitude.

    Args:
        altitude_m: Altitude above mean sea level, metres.

    Returns:
        Circular orbital velocity, m/s.
    """
    return math.sqrt(MU_EARTH / (R_EARTH_M + altitude_m))


def is_reachable(inclination_deg: float, latitude_deg: float) -> bool:
    """Whether an inclination can be reached directly from a launch latitude.

    Args:
        inclination_deg: Target orbital inclination, degrees.
        latitude_deg: Launch site latitude, degrees.

    Returns:
        True if a direct ascent can reach this inclination.
    """
    return abs(math.cos(math.radians(inclination_deg))) <= math.cos(math.radians(latitude_deg))


def rotation_bonus(inclination_deg: float, latitude_deg: float) -> float:
    """Free velocity contributed by Earth's rotation for a given target orbit.

    Worth noticing: the bonus depends only on the target inclination, not on the
    launch latitude. Latitude only decides whether the inclination is reachable
    at all. A retrograde orbit such as sun-synchronous gets a negative bonus,
    because the rocket has to cancel the eastward motion it started with.

    Args:
        inclination_deg: Target orbital inclination, degrees.
        latitude_deg: Launch site latitude, degrees.

    Returns:
        Velocity contributed by Earth's rotation, m/s. Negative for retrograde
        orbits.

    Raises:
        InclinationUnreachableError: If the inclination is below the launch
            latitude.
    """
    if not is_reachable(inclination_deg, latitude_deg):
        raise InclinationUnreachableError(
            f"inclination {inclination_deg} deg is unreachable from latitude "
            f"{latitude_deg} deg without a plane change"
        )
    return V_EQUATORIAL * math.cos(math.radians(inclination_deg))


def launch_azimuth(inclination_deg: float, latitude_deg: float) -> float:
    """Compass heading a rocket must fly to reach a given inclination.

    Args:
        inclination_deg: Target orbital inclination, degrees.
        latitude_deg: Launch site latitude, degrees.

    Returns:
        Azimuth measured clockwise from north, degrees. 90 is due east.

    Raises:
        InclinationUnreachableError: If the inclination is below the launch
            latitude.
    """
    if not is_reachable(inclination_deg, latitude_deg):
        raise InclinationUnreachableError(
            f"inclination {inclination_deg} deg is unreachable from latitude "
            f"{latitude_deg} deg without a plane change"
        )
    sin_azimuth = math.cos(math.radians(inclination_deg)) / math.cos(math.radians(latitude_deg))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_azimuth))))


def inclination_penalty(
    inclination_deg: float, latitude_deg: float, reference_inclination_deg: float | None = None
) -> float:
    """Extra velocity a target inclination costs versus the cheapest one available.

    The cheapest inclination from any site equals its latitude, which is a due
    east launch.

    Args:
        inclination_deg: Target orbital inclination, degrees.
        latitude_deg: Launch site latitude, degrees.
        reference_inclination_deg: Inclination to compare against. Defaults to
            the launch latitude, that is, a due east launch.

    Returns:
        Additional velocity required, m/s. Zero for a due east launch.
    """
    reference = latitude_deg if reference_inclination_deg is None else reference_inclination_deg
    return rotation_bonus(reference, latitude_deg) - rotation_bonus(inclination_deg, latitude_deg)
