"""The rocket equation and its inverse forms.

Everything else in this package is built on these eight functions. See
docs/physics-reference.md section 2.2.
"""

import math

from rocketry.constants import G0


def exhaust_velocity(isp: float) -> float:
    """Effective exhaust velocity in m/s for a given specific impulse in seconds.

    Args:
        isp: Specific impulse, seconds.

    Returns:
        Effective exhaust velocity, m/s.
    """
    return isp * G0


def delta_v(m0: float, mf: float, isp: float) -> float:
    """Velocity change from burning a vehicle down from `m0` to `mf`.

    This is Tsiolkovsky's equation. It assumes a burn with no gravity, no
    atmosphere and no steering, so it is an upper bound on what a real launch
    achieves.

    Args:
        m0: Mass before the burn, tonnes.
        mf: Mass after the burn, tonnes.
        isp: Specific impulse, seconds.

    Returns:
        Velocity change, m/s.

    Raises:
        ValueError: If either mass is non-positive or the vehicle gains mass.
    """
    if m0 <= 0 or mf <= 0:
        raise ValueError(f"masses must be positive, got m0={m0}, mf={mf}")
    if mf > m0:
        raise ValueError(f"a burn cannot increase mass: m0={m0}, mf={mf}")
    return exhaust_velocity(isp) * math.log(m0 / mf)


def mass_ratio(dv: float, isp: float) -> float:
    """Mass ratio needed to achieve a given velocity change.

    The exponential that makes rocketry hard: this grows without bound as `dv`
    rises.

    Args:
        dv: Desired velocity change, m/s.
        isp: Specific impulse, seconds.

    Returns:
        Ratio of mass before the burn to mass after it, dimensionless.
    """
    return math.exp(dv / exhaust_velocity(isp))


def propellant_from_final(final_mass: float, dv: float, isp: float) -> float:
    """Propellant needed, expressed as a fraction of what remains at the end.

    Answers "how much do I burn, relative to what I will have left?". The
    companion form is `propellant_from_initial`. Both are correct and they
    answer different questions; see docs/physics-reference.md section 2.2.

    Args:
        final_mass: Mass after the burn, tonnes.
        dv: Desired velocity change, m/s.
        isp: Specific impulse, seconds.

    Returns:
        Propellant mass, tonnes.
    """
    return final_mass * (mass_ratio(dv, isp) - 1.0)


def propellant_from_initial(initial_mass: float, dv: float, isp: float) -> float:
    """Propellant needed, expressed as a fraction of what the vehicle has now.

    Args:
        initial_mass: Mass before the burn, tonnes.
        dv: Desired velocity change, m/s.
        isp: Specific impulse, seconds.

    Returns:
        Propellant mass, tonnes.
    """
    return initial_mass * (1.0 - 1.0 / mass_ratio(dv, isp))


def final_mass(initial_mass: float, dv: float, isp: float) -> float:
    """Mass remaining after burning for a given velocity change.

    Args:
        initial_mass: Mass before the burn, tonnes.
        dv: Desired velocity change, m/s.
        isp: Specific impulse, seconds.

    Returns:
        Mass after the burn, tonnes.
    """
    return initial_mass / mass_ratio(dv, isp)


def binary_velocity(isp: float) -> float:
    """Velocity gained per doubling of the mass ratio.

    A teaching device: every time you double the mass ratio you buy exactly one
    more of these. Note the correct constant is `G0 * ln(2)`; the source article
    prints 6.937, which is 2 % too high (correction C1).

    Args:
        isp: Specific impulse, seconds.

    Returns:
        Velocity change per mass-ratio doubling, m/s.
    """
    return exhaust_velocity(isp) * math.log(2.0)


def propellant_burnt(thrust_tf: float, isp: float, seconds: float) -> float:
    """Propellant consumed by an engine running at constant thrust.

    Args:
        thrust_tf: Thrust, tonnes-force.
        isp: Specific impulse, seconds.
        seconds: Burn duration, seconds.

    Returns:
        Propellant mass, tonnes.
    """
    return thrust_tf / isp * seconds


def mass_after_burn(propellant: float, dv: float, isp: float) -> float:
    """Weigh a vehicle from an observed burn.

    Given how much propellant a burn consumed and how much it changed the
    vehicle's velocity, this returns what the vehicle weighed once the burn
    finished. This is the method the source article uses to weigh Starship from
    a 14-second relight, and it measures *total* mass, not dry mass.

    Args:
        propellant: Propellant consumed, tonnes.
        dv: Observed velocity change, m/s.
        isp: Specific impulse of the engine used, seconds.

    Returns:
        Vehicle mass after the burn, tonnes.
    """
    return propellant / (mass_ratio(dv, isp) - 1.0)
