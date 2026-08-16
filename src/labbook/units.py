"""Unit systems for display. The physics core is SI and stays SI.

Nothing in :mod:`rocketry` knows this module exists. Conversion happens at the
edge, once, when a number is about to be shown to somebody. That keeps every
calculation reproducible and means a unit bug can never change a result, only
its label.

Specific impulse is deliberately unconverted: it is in seconds in both systems,
which is precisely why engineers quote it that way.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class UnitSystem(StrEnum):
    """Which units to display."""

    METRIC = "metric"
    """Tonnes, m/s, km/h, metres, kilometres, degrees Celsius."""

    US = "us"
    """Pounds, mph, feet, miles, degrees Fahrenheit."""

    @property
    def label(self) -> str:
        """Human-readable name for a UI toggle."""
        match self:
            case UnitSystem.METRIC:
                return "Metric (t, km/h, m)"
            case UnitSystem.US:
                return "US customary (lb, mph, ft)"


class Quantity(StrEnum):
    """A physical quantity, which determines how a number converts."""

    MASS = "mass"
    """Stored in tonnes."""

    VELOCITY = "velocity"
    """Stored in m/s. Used for delta-v and instantaneous speed."""

    SPEED = "speed"
    """Stored in km/h. Used where the source quotes km/h, such as staging speed.

    The *core* never stores km/h. Values reaching this quantity have already
    crossed the edge, either from a library field that names its unit or through
    :func:`to_kmh`.
    """

    ALTITUDE = "altitude"
    """Stored in metres."""

    DISTANCE = "distance"
    """Stored in kilometres."""

    THRUST = "thrust"
    """Stored in tonnes-force."""

    TEMPERATURE = "temperature"
    """Stored in degrees Celsius."""

    AREA = "area"
    """Stored in square metres."""

    MASS_FLOW = "mass_flow"
    """Stored in tonnes per second."""

    ISP = "isp"
    """Stored in seconds. Identical in both systems."""

    DIMENSIONLESS = "dimensionless"
    """A ratio. Never converted."""

    PERCENT = "percent"
    """A fraction from 0 to 1, displayed as a percentage."""


_MS_PER_KMH = 1.0 / 3.6


def from_kmh(kmh: float) -> float:
    """A speed a reader or a source gave in km/h, in the m/s the core takes.

    Args:
        kmh: Speed, km/h.

    Returns:
        The same speed, m/s.
    """
    return kmh * _MS_PER_KMH


def to_kmh(ms: float) -> float:
    """A speed the core produced in m/s, in the km/h a reader recognises.

    Args:
        ms: Speed, m/s.

    Returns:
        The same speed, km/h, ready for :attr:`Quantity.SPEED`.
    """
    return ms / _MS_PER_KMH


_LB_PER_TONNE = 2204.622622
_MPH_PER_MS = 2.236936292
_MPH_PER_KMH = 0.621371192
_FT_PER_M = 3.280839895
_MI_PER_KM = 0.621371192
_SQFT_PER_SQM = 10.76391042


@dataclass(frozen=True, slots=True)
class Measurement:
    """A number with the unit it should be shown in.

    Attributes:
        value: The converted number.
        unit: Its unit symbol.
    """

    value: float
    unit: str

    def __str__(self) -> str:
        """Render with a sensible default precision."""
        return format_measurement(self)


def convert(value: float, quantity: Quantity, system: UnitSystem) -> Measurement:
    """Convert a stored SI value into the requested display system.

    Args:
        value: The number, in this library's storage unit for that quantity.
        quantity: What the number measures.
        system: Target display system.

    Returns:
        The converted value and its unit symbol.
    """
    if system is UnitSystem.METRIC:
        return Measurement(value, _METRIC_UNITS[quantity])
    match quantity:
        case Quantity.MASS:
            return Measurement(value * _LB_PER_TONNE, "lb")
        case Quantity.VELOCITY:
            return Measurement(value * _MPH_PER_MS, "mph")
        case Quantity.SPEED:
            return Measurement(value * _MPH_PER_KMH, "mph")
        case Quantity.ALTITUDE:
            return Measurement(value * _FT_PER_M, "ft")
        case Quantity.DISTANCE:
            return Measurement(value * _MI_PER_KM, "mi")
        case Quantity.THRUST:
            return Measurement(value * _LB_PER_TONNE, "lbf")
        case Quantity.TEMPERATURE:
            return Measurement(value * 9.0 / 5.0 + 32.0, "°F")
        case Quantity.AREA:
            return Measurement(value * _SQFT_PER_SQM, "sq ft")
        case Quantity.MASS_FLOW:
            return Measurement(value * _LB_PER_TONNE, "lb/s")
        case Quantity.ISP | Quantity.DIMENSIONLESS | Quantity.PERCENT:
            return Measurement(value, _METRIC_UNITS[quantity])


_METRIC_UNITS: dict[Quantity, str] = {
    Quantity.MASS: "t",
    Quantity.VELOCITY: "m/s",
    Quantity.SPEED: "km/h",
    Quantity.ALTITUDE: "m",
    Quantity.DISTANCE: "km",
    Quantity.THRUST: "tf",
    Quantity.TEMPERATURE: "°C",
    Quantity.AREA: "m²",
    Quantity.MASS_FLOW: "t/s",
    Quantity.ISP: "s",
    Quantity.DIMENSIONLESS: "",
    Quantity.PERCENT: "%",
}


def format_measurement(measurement: Measurement, digits: int | None = None) -> str:
    """Render a measurement with thousands separators and a unit.

    Args:
        measurement: The value and unit to render.
        digits: Decimal places. Defaults to a precision chosen from magnitude,
            so 5850 t reads as "5,850 t" and 0.43 reads as "0.43".

    Returns:
        A display string.
    """
    places = digits if digits is not None else _default_digits(measurement.value)
    number = f"{measurement.value:,.{places}f}"
    return f"{number} {measurement.unit}".strip()


def _default_digits(value: float) -> int:
    """Choose a sensible number of decimal places for a magnitude.

    Args:
        value: The number about to be shown.

    Returns:
        Decimal places.
    """
    magnitude = abs(value)
    if magnitude >= 1000:
        return 0
    if magnitude >= 100:
        return 0
    if magnitude >= 10:
        return 1
    if magnitude >= 1:
        return 2
    return 3


@dataclass(frozen=True, slots=True)
class Formatter:
    """Formats numbers in one unit system, for tables, charts and the UI.

    Create one per report or per UI session and pass it around, rather than
    threading a `UnitSystem` enum through every call site::

        fmt = Formatter(UnitSystem.US)
        fmt.mass(5850)          # '12,896,048 lb'
        fmt.axis_label('Mass', Quantity.MASS)   # 'Mass (lb)'

    Attributes:
        system: The unit system being displayed.
    """

    system: UnitSystem = UnitSystem.METRIC

    def value(self, value: float, quantity: Quantity) -> float:
        """Convert a number without formatting it, for chart axes.

        Args:
            value: The stored value.
            quantity: What it measures.

        Returns:
            The converted number.
        """
        return convert(value, quantity, self.system).value

    def values(self, values: Sequence[float], quantity: Quantity) -> list[float]:
        """Convert a whole series, for chart axes.

        Args:
            values: Stored values.
            quantity: What they measure.

        Returns:
            Converted numbers.
        """
        return [self.value(v, quantity) for v in values]

    def unit(self, quantity: Quantity) -> str:
        """Unit symbol for a quantity in this system.

        Args:
            quantity: What is being measured.

        Returns:
            The unit symbol, possibly empty.
        """
        return convert(0.0, quantity, self.system).unit

    def axis_label(self, name: str, quantity: Quantity) -> str:
        """Build a chart axis label with its unit.

        Args:
            name: What the axis shows, for example "Payload".
            quantity: What it measures.

        Returns:
            A label such as "Payload (t)".
        """
        unit = self.unit(quantity)
        return f"{name} ({unit})" if unit else name

    def format(self, value: float, quantity: Quantity, digits: int | None = None) -> str:
        """Convert and render a number.

        Args:
            value: The stored value.
            quantity: What it measures.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string including the unit.
        """
        if quantity is Quantity.PERCENT:
            return f"{value * 100:.{digits if digits is not None else 1}f} %"
        return format_measurement(convert(value, quantity, self.system), digits)

    def mass(self, tonnes: float, digits: int | None = None) -> str:
        """Format a mass stored in tonnes.

        Args:
            tonnes: Mass, tonnes.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(tonnes, Quantity.MASS, digits)

    def velocity(self, ms: float, digits: int | None = None) -> str:
        """Format a velocity stored in m/s.

        Args:
            ms: Velocity, m/s.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(ms, Quantity.VELOCITY, digits)

    def speed(self, kmh: float, digits: int | None = None) -> str:
        """Format a speed stored in km/h.

        Args:
            kmh: Speed, km/h.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(kmh, Quantity.SPEED, digits)

    def thrust(self, tf: float, digits: int | None = None) -> str:
        """Format a thrust stored in tonnes-force.

        Args:
            tf: Thrust, tonnes-force.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(tf, Quantity.THRUST, digits)

    def altitude(self, metres: float, digits: int | None = None) -> str:
        """Format an altitude stored in metres.

        Args:
            metres: Altitude, m.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(metres, Quantity.ALTITUDE, digits)

    def altitude_km(self, metres: float, digits: int | None = None) -> str:
        """Format an altitude in kilometres or miles rather than metres or feet.

        Above a few kilometres, metres stop being readable: "107,557 m" is a
        number to decode, "108 km" is a fact.

        Args:
            metres: Altitude, m.
            digits: Decimal places, or None to choose automatically.

        Returns:
            A display string.
        """
        return self.format(metres / 1000.0, Quantity.DISTANCE, digits)

    def percent(self, fraction: float, digits: int = 1) -> str:
        """Format a fraction as a percentage.

        Args:
            fraction: A value from 0 to 1.
            digits: Decimal places.

        Returns:
            A display string such as "12.1 %".
        """
        return self.format(fraction, Quantity.PERCENT, digits)


METRIC = Formatter(UnitSystem.METRIC)
"""Ready-made metric formatter, the default for reports."""

US = Formatter(UnitSystem.US)
"""Ready-made US customary formatter."""
