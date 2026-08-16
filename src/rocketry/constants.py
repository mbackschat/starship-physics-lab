"""Physical constants, in the units used throughout this library.

Units convention for the whole package: mass in tonnes, velocity in m/s,
thrust in tonnes-force, specific impulse in seconds, distance in metres unless
a name says otherwise.
"""

from typing import Final

G0: Final[float] = 9.80665
"""Standard gravity, m/s^2. Used for the Isp-to-exhaust-velocity conversion.

The source article uses 9.81. The difference is 0.03 %, well inside every
tolerance here, but the library commits to one value so results are
reproducible.
"""

R_EARTH_M: Final[float] = 6_371_000.0
"""Mean Earth radius, m."""

MU_EARTH: Final[float] = 3.986004418e14
"""Earth's standard gravitational parameter, m^3/s^2."""

V_EQUATORIAL: Final[float] = 465.1
"""Earth's surface speed at the equator, m/s."""

KMH_TO_MS: Final[float] = 1.0 / 3.6
"""Multiply km/h by this to get m/s."""
