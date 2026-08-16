"""Series for the teaching charts, built from the physics core rather than drawn.

Two of these answer questions that look identical and are not:

``burn_trace``
    *What happens while a rocket burns?* The vehicle gets lighter, so the last
    tonne of propellant is worth far more speed than the first. The curve
    steepens.

``loading_sweep``
    *What does loading more propellant buy a designer?* The logarithm flattens,
    so each extra tonne on the pad is worth less than the one before. The curve
    bends the other way.

Both are consequences of the same equation and readers routinely fuse them into
one wrong intuition, which is why chapter 1 now shows them side by side.
"""

from dataclasses import dataclass

from rocketry.tsiolkovsky import delta_v


@dataclass(frozen=True, slots=True)
class BurnSample:
    """One instant during a burn.

    Attributes:
        burnt_t: Propellant burnt so far, tonnes.
        mass_t: What the vehicle weighs at this instant, tonnes.
        velocity_ms: Speed gained since ignition, m/s.
    """

    burnt_t: float
    mass_t: float
    velocity_ms: float


@dataclass(frozen=True, slots=True)
class LoadingSample:
    """One design, on the question of how much propellant to load.

    Attributes:
        propellant_t: Propellant loaded, tonnes.
        delta_v_ms: What the finished vehicle could achieve, m/s.
    """

    propellant_t: float
    delta_v_ms: float


def burn_trace(
    *, dry_t: float, propellant_t: float, isp_s: float, steps: int = 60
) -> list[BurnSample]:
    """Follow one vehicle through its burn, in equal steps of propellant.

    Sampled by propellant burnt rather than by time, so that every step spends
    the same mass. Any change in the speed gained per step is then the physics
    and not an artefact of the sampling.

    Args:
        dry_t: What the vehicle weighs empty, tonnes.
        propellant_t: What it burns, tonnes.
        isp_s: Specific impulse, seconds.
        steps: How many intervals to divide the burn into.

    Returns:
        ``steps + 1`` samples, from ignition to burnout.

    Raises:
        ValueError: If the vehicle has no dry mass or the burn has no steps.
    """
    _check(dry_t, steps)
    wet = dry_t + propellant_t
    samples = []
    for index in range(steps + 1):
        burnt = propellant_t * index / steps
        mass = wet - burnt
        samples.append(
            BurnSample(burnt_t=burnt, mass_t=mass, velocity_ms=delta_v(wet, mass, isp_s))
        )
    return samples


def loading_sweep(
    *, dry_t: float, isp_s: float, up_to_t: float, steps: int = 60
) -> list[LoadingSample]:
    """Ask what each extra tonne of propellant on the pad is worth.

    Args:
        dry_t: What the vehicle weighs empty, tonnes.
        isp_s: Specific impulse, seconds.
        up_to_t: Largest propellant load to consider, tonnes.
        steps: How many intervals to divide that range into.

    Returns:
        ``steps + 1`` samples, from an empty rocket upwards.

    Raises:
        ValueError: If the vehicle has no dry mass or the sweep has no steps.
    """
    _check(dry_t, steps)
    return [
        LoadingSample(
            propellant_t=(loaded := up_to_t * index / steps),
            delta_v_ms=delta_v(dry_t + loaded, dry_t, isp_s),
        )
        for index in range(steps + 1)
    ]


def _check(dry_t: float, steps: int) -> None:
    """Reject the two inputs that would otherwise fail deep inside a loop.

    Args:
        dry_t: What the vehicle weighs empty, tonnes.
        steps: How many intervals were asked for.

    Raises:
        ValueError: If the dry mass is not positive or there are no steps.
    """
    if dry_t <= 0:
        raise ValueError(f"a rocket needs a positive dry mass, got {dry_t}")
    if steps < 1:
        raise ValueError(f"a curve needs at least one step, got {steps}")
