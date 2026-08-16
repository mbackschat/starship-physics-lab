"""How a stage's dry mass grows when you make it bigger.

The single most consequential hidden assumption in any launch vehicle argument.
See docs/physics-reference.md section 3.8 and model M9.
"""

LINEAR = 1.0
"""Dry mass grows in proportion to propellant. Conservative for large stages."""

REALISTIC = 0.8
"""A reasonable guess for a real stage.

Tanks and structural loads scale with size, but engines, nose, fins and heat
shield largely do not, so the true exponent sits below linear.
"""

FIXED = 0.0
"""Dry mass does not grow at all. What optimistic payload claims implicitly require."""


def scaled_dry_mass(
    *,
    reference_dry: float,
    reference_propellant: float,
    propellant: float,
    exponent: float = LINEAR,
) -> float:
    """Estimate a stage's dry mass by scaling a known stage.

    Args:
        reference_dry: Dry mass of the stage being scaled from, tonnes.
        reference_propellant: Propellant load of that same stage, tonnes.
        propellant: Propellant load of the stage being estimated, tonnes.
        exponent: Scaling exponent. 1.0 is fully linear, 0.0 holds mass fixed.
            Real stages sit around 0.7 to 0.9.

    Returns:
        Estimated dry mass, tonnes.

    Raises:
        ValueError: If the reference propellant load is non-positive.
    """
    if reference_propellant <= 0:
        raise ValueError(f"reference propellant must be positive, got {reference_propellant}")
    return float(reference_dry * (propellant / reference_propellant) ** exponent)
