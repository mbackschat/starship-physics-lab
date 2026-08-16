"""Why bringing a big stage back is harder than bringing a small one back.

The square-cube law: mass grows with the cube of size, frontal area only with
the square. See docs/physics-reference.md section 2.8.
"""

import math


def frontal_area(diameter: float) -> float:
    """Cross-sectional area of a cylindrical stage falling base-first.

    Args:
        diameter: Stage diameter, m.

    Returns:
        Frontal area, m^2.
    """
    return math.pi * (diameter / 2.0) ** 2


def area_ratio(diameter: float, reference_diameter: float) -> float:
    """How much more frontal area one stage has than another.

    Args:
        diameter: Stage diameter, m.
        reference_diameter: Diameter of the stage compared against, m.

    Returns:
        Ratio of frontal areas, dimensionless.

    Raises:
        ValueError: If the reference diameter is non-positive.
    """
    if reference_diameter <= 0:
        raise ValueError(f"reference diameter must be positive, got {reference_diameter}")
    return (diameter / reference_diameter) ** 2


def ballistic_coefficient(mass_t: float, diameter: float, drag_coefficient: float = 1.0) -> float:
    """How hard a body is to slow down in the atmosphere.

    A higher value means the vehicle punches deeper into thick air before
    slowing, so it arrives faster and has less time and less surface over which
    to shed its energy.

    Args:
        mass_t: Vehicle mass, tonnes.
        diameter: Vehicle diameter, m.
        drag_coefficient: Drag coefficient, dimensionless.

    Returns:
        Ballistic coefficient, kg/m^2.
    """
    return mass_t * 1000.0 / (drag_coefficient * frontal_area(diameter))


def diameter_for_equal_loading(*, reference_diameter: float, mass_ratio: float) -> float:
    """Diameter a heavier vehicle needs to reenter as gently as a lighter one.

    Follow this thought far enough and you arrive at the flying saucer: for
    reentry you want the most area per unit mass you can get.

    Args:
        reference_diameter: Diameter of the vehicle being matched, m.
        mass_ratio: How many times heavier the new vehicle is.

    Returns:
        Required diameter, m.

    Raises:
        ValueError: If the mass ratio is negative.
    """
    if mass_ratio < 0:
        raise ValueError(f"mass ratio must be non-negative, got {mass_ratio}")
    return reference_diameter * math.sqrt(mass_ratio)
