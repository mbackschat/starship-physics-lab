"""Thrust, weight and the gravity loss that the rocket equation ignores.

See docs/physics-reference.md section 2.4.
"""


def thrust_to_weight(thrust_tf: float, mass_t: float) -> float:
    """Ratio of thrust to weight.

    Below 1.0 the vehicle cannot leave the pad. At exactly 1.0 it hovers,
    burning propellant and going nowhere.

    Args:
        thrust_tf: Thrust, tonnes-force.
        mass_t: Vehicle mass, tonnes.

    Returns:
        Thrust-to-weight ratio, dimensionless.

    Raises:
        ValueError: If mass is non-positive.
    """
    if mass_t <= 0:
        raise ValueError(f"mass must be positive, got {mass_t}")
    return thrust_tf / mass_t


def net_acceleration_g(twr: float) -> float:
    """Acceleration actually available after gravity takes its cut, in g.

    Args:
        twr: Thrust-to-weight ratio.

    Returns:
        Net acceleration in multiples of standard gravity. Negative means the
        vehicle is falling.
    """
    return twr - 1.0


def gravity_thrust_fraction(twr: float) -> float:
    """Fraction of thrust spent merely holding the vehicle up.

    At the typical liftoff ratio of 1.41 this is 71 %, which is why low
    thrust-to-weight is expensive even though nothing appears to be wasted.

    Args:
        twr: Thrust-to-weight ratio.

    Returns:
        Fraction of thrust consumed by gravity, 0 to 1.

    Raises:
        ValueError: If the ratio is non-positive.
    """
    if twr <= 0:
        raise ValueError(f"thrust-to-weight must be positive, got {twr}")
    return min(1.0, 1.0 / twr)


def acceleration_after(
    seconds: float, twr_initial: float, mass_flow_fraction: float
) -> float:
    """Net acceleration after burning at constant thrust for a while.

    Thrust is held constant while mass falls, so the ratio climbs. How fast it
    climbs depends on what fraction of its own mass the vehicle burns per
    second, which is why a higher-Isp engine paradoxically spends longer in the
    expensive low-acceleration regime.

    Args:
        seconds: Time since liftoff, seconds.
        twr_initial: Thrust-to-weight ratio at liftoff.
        mass_flow_fraction: Propellant burnt per second as a fraction of
            liftoff mass, per second.

    Returns:
        Net acceleration in multiples of standard gravity.

    Raises:
        ValueError: If the vehicle would have burnt all of its mass by then.
    """
    remaining = 1.0 - mass_flow_fraction * seconds
    if remaining <= 0:
        raise ValueError(f"vehicle is out of propellant after {seconds} s")
    return twr_initial / remaining - 1.0
