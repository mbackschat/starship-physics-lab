"""How much useful cargo is left once the rocket has paid for itself.

See docs/physics-reference.md correction C15. The rocket equation fixes what
arrives in orbit almost independently of what that mass consists of; only the
split between vehicle and cargo is negotiable.
"""

from rocketry.tsiolkovsky import mass_ratio


def mass_delivered(propellant: float, delta_v: float, isp: float) -> float:
    """Total mass a stage puts into orbit, vehicle and cargo together.

    This is the number that surprises people: it depends on the propellant load,
    the engine and the velocity target, and not at all on how heavy the stage
    itself is. Build a lighter stage and the same total still arrives, just with
    more of it being cargo.

    Args:
        propellant: Usable propellant burnt during the ascent, tonnes.
        delta_v: Velocity change the stage must provide, m/s.
        isp: Specific impulse, seconds.

    Returns:
        Mass arriving at the target, tonnes.
    """
    return propellant / (mass_ratio(delta_v, isp) - 1.0)


def payload_for_stage(
    *,
    dry_mass: float,
    propellant: float,
    isp: float,
    delta_v: float,
    residual_propellant: float = 0.0,
) -> float:
    """Payload a single stage can deliver.

    Args:
        dry_mass: Stage mass with empty tanks, tonnes.
        propellant: Usable propellant burnt during the ascent, tonnes.
        isp: Specific impulse, seconds.
        delta_v: Velocity change the stage must provide, m/s.
        residual_propellant: Propellant still aboard on arrival, for
            deorbit, manoeuvring and landing, tonnes.

    Returns:
        Payload mass, tonnes. Negative means the stage cannot even deliver
        itself, which is a real and instructive answer rather than an error.
    """
    return mass_delivered(propellant, delta_v, isp) - dry_mass - residual_propellant


def dry_mass_for_payload(
    *,
    target_payload: float,
    propellant: float,
    isp: float,
    delta_v: float,
    residual_propellant: float = 0.0,
) -> float:
    """Dry mass a stage would need in order to deliver a claimed payload.

    Inverts `payload_for_stage`. Useful for testing a manufacturer's claim
    against the physics: if the required dry mass is implausible, so is the
    claim.

    Args:
        target_payload: Claimed payload, tonnes.
        propellant: Usable propellant burnt during the ascent, tonnes.
        isp: Specific impulse, seconds.
        delta_v: Velocity change the stage must provide, m/s.
        residual_propellant: Propellant still aboard on arrival, tonnes.

    Returns:
        Required stage dry mass, tonnes. Negative means the claim is impossible
        at any construction quality.
    """
    return mass_delivered(propellant, delta_v, isp) - target_payload - residual_propellant
