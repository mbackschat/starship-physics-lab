"""Air temperature, pressure and density against altitude.

The International Standard Atmosphere, implemented directly. It is seven
piecewise barometric layers and about forty lines, which is a better trade than
a dependency that drags scipy into a browser-hosted build for the sake of it.

Valid to 84.852 km geopotential. Above that there is so little air left that
treating it as vacuum changes nothing a reader would notice.
"""

import math
from typing import NamedTuple

R_SPECIFIC = 287.0528
"""Specific gas constant for dry air, J/(kg·K)."""

G_ISA = 9.80665
"""Standard gravity used by the ISA definition, m/s^2."""

EARTH_RADIUS_ISA_M = 6_356_766.0
"""Radius used to convert geometric to geopotential altitude, metres."""

SEA_LEVEL_PRESSURE_PA = 101_325.0
SEA_LEVEL_DENSITY = 1.225
TOP_OF_ATMOSPHERE_M = 84_852.0
"""Above this the model returns vacuum. The ISA is not defined higher."""


class _Layer(NamedTuple):
    """One ISA layer.

    Attributes:
        base_altitude_m: Geopotential altitude where the layer starts.
        lapse_rate: Temperature change per metre, K/m. Zero for isothermal layers.
        base_temperature_k: Temperature at the base of the layer.
        base_pressure_pa: Pressure at the base of the layer.
    """

    base_altitude_m: float
    lapse_rate: float
    base_temperature_k: float
    base_pressure_pa: float


_LAYERS: tuple[_Layer, ...] = (
    _Layer(0.0, -0.0065, 288.15, 101_325.0),
    _Layer(11_000.0, 0.0, 216.65, 22_632.06),
    _Layer(20_000.0, 0.001, 216.65, 5_474.889),
    _Layer(32_000.0, 0.0028, 228.65, 868.0187),
    _Layer(47_000.0, 0.0, 270.65, 110.9063),
    _Layer(51_000.0, -0.0028, 270.65, 66.93887),
    _Layer(71_000.0, -0.002, 214.65, 3.956420),
)


class Conditions(NamedTuple):
    """The state of the air at one altitude.

    Attributes:
        temperature_k: Temperature, K.
        pressure_pa: Pressure, Pa.
        density: Density, kg/m^3.
    """

    temperature_k: float
    pressure_pa: float
    density: float


def geopotential_altitude(altitude_m: float) -> float:
    """Convert geometric altitude to the geopotential altitude the ISA uses.

    The ISA is defined against an altitude scale that already accounts for
    gravity weakening with height, so the two differ by about 0.5 % at 30 km.

    Args:
        altitude_m: Geometric altitude above sea level, metres.

    Returns:
        Geopotential altitude, metres.
    """
    return EARTH_RADIUS_ISA_M * altitude_m / (EARTH_RADIUS_ISA_M + altitude_m)


def geometric_altitude(geopotential_m: float) -> float:
    """Convert a geopotential altitude back to a geometric one.

    Published ISA tables are indexed by geopotential altitude, so this is what
    you need to look up a reference value at a stated table height.

    Args:
        geopotential_m: Geopotential altitude, metres.

    Returns:
        Geometric altitude above sea level, metres.
    """
    return EARTH_RADIUS_ISA_M * geopotential_m / (EARTH_RADIUS_ISA_M - geopotential_m)


def conditions(altitude_m: float) -> Conditions:
    """Temperature, pressure and density at an altitude.

    Args:
        altitude_m: Geometric altitude above sea level, metres.

    Returns:
        The air's state. Vacuum above the top of the modelled atmosphere.
    """
    if altitude_m >= TOP_OF_ATMOSPHERE_M:
        return Conditions(186.946, 0.0, 0.0)
    height = geopotential_altitude(max(0.0, altitude_m))

    layer = _LAYERS[0]
    for candidate in _LAYERS:
        if height >= candidate.base_altitude_m:
            layer = candidate
        else:
            break

    delta = height - layer.base_altitude_m
    if layer.lapse_rate == 0.0:
        temperature = layer.base_temperature_k
        pressure = layer.base_pressure_pa * math.exp(
            -G_ISA * delta / (R_SPECIFIC * temperature)
        )
    else:
        temperature = layer.base_temperature_k + layer.lapse_rate * delta
        exponent = -G_ISA / (layer.lapse_rate * R_SPECIFIC)
        pressure = layer.base_pressure_pa * (temperature / layer.base_temperature_k) ** exponent

    return Conditions(temperature, pressure, pressure / (R_SPECIFIC * temperature))


def density(altitude_m: float) -> float:
    """Air density at an altitude.

    Args:
        altitude_m: Geometric altitude above sea level, metres.

    Returns:
        Density, kg/m^3. Zero above the top of the modelled atmosphere.
    """
    return conditions(altitude_m).density


def pressure(altitude_m: float) -> float:
    """Ambient air pressure at an altitude.

    Args:
        altitude_m: Geometric altitude above sea level, metres.

    Returns:
        Pressure, Pa. Zero above the top of the modelled atmosphere.
    """
    return conditions(altitude_m).pressure_pa


def pressure_ratio(altitude_m: float) -> float:
    """Ambient pressure as a fraction of sea level pressure.

    Used to blend an engine between its sea-level and vacuum performance: at
    ratio 1 it delivers its sea-level thrust, at ratio 0 its vacuum thrust.

    Args:
        altitude_m: Geometric altitude above sea level, metres.

    Returns:
        A value from 1.0 at sea level down to 0.0 in vacuum.
    """
    return pressure(altitude_m) / SEA_LEVEL_PRESSURE_PA
