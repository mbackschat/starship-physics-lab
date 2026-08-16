"""Rocket physics core for Starship Physics Lab.

A small, fully tested library of launch vehicle physics. It has no user
interface dependencies by design: every function here is a plain calculation
that can be checked against the golden numbers in
docs/physics-reference.md section 7.

Units are tonnes, m/s, tonnes-force and seconds throughout.
"""

from rocketry.constants import G0, KMH_TO_MS, MU_EARTH, R_EARTH_M, V_EQUATORIAL
from rocketry.tsiolkovsky import delta_v, exhaust_velocity, mass_ratio

__all__ = [
    "G0",
    "KMH_TO_MS",
    "MU_EARTH",
    "R_EARTH_M",
    "V_EQUATORIAL",
    "delta_v",
    "exhaust_velocity",
    "mass_ratio",
]
