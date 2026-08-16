"""The standard atmosphere, checked against published reference values.

Implemented rather than imported, so it is worth proving it agrees with the
tables everyone else uses.
"""

import pytest

from rocketry.atmosphere import (
    SEA_LEVEL_DENSITY,
    SEA_LEVEL_PRESSURE_PA,
    TOP_OF_ATMOSPHERE_M,
    conditions,
    density,
    geometric_altitude,
    pressure_ratio,
)

# Published ISA tables are indexed by GEOPOTENTIAL altitude, which differs from
# the geometric altitude a rocket actually flies at by about 0.5 % at 30 km.
# Geopotential m, temperature K, pressure Pa, density kg/m^3.
REFERENCE = [
    (0, 288.15, 101_325.0, 1.2250),
    (5_000, 255.68, 54_048.0, 0.73643),
    (11_000, 216.65, 22_632.0, 0.36392),
    (20_000, 216.65, 5_474.9, 0.088035),
    (32_000, 228.65, 868.02, 0.013225),
    (47_000, 270.65, 110.91, 0.0014275),
    (71_000, 214.65, 3.9564, 0.000064211),
]


@pytest.mark.parametrize(("altitude", "temperature", "pressure", "rho"), REFERENCE)
def test_matches_the_isa_tables(altitude, temperature, pressure, rho):
    result = conditions(geometric_altitude(altitude))
    assert result.temperature_k == pytest.approx(temperature, rel=1e-3)
    assert result.pressure_pa == pytest.approx(pressure, rel=2e-3)
    assert result.density == pytest.approx(rho, rel=3e-3)


def test_sea_level_constants_agree_with_the_model():
    assert conditions(0).pressure_pa == pytest.approx(SEA_LEVEL_PRESSURE_PA)
    assert conditions(0).density == pytest.approx(SEA_LEVEL_DENSITY, rel=1e-3)


def test_density_falls_monotonically():
    values = [density(h) for h in range(0, 80_000, 500)]
    assert values == sorted(values, reverse=True)


def test_above_the_model_it_is_vacuum():
    assert density(TOP_OF_ATMOSPHERE_M + 1) == 0.0
    assert pressure_ratio(200_000) == 0.0


def test_pressure_ratio_spans_one_to_zero():
    assert pressure_ratio(0) == pytest.approx(1.0)
    assert 0.0 < pressure_ratio(20_000) < 0.1


def test_below_sea_level_is_clamped_rather_than_extrapolated():
    assert density(-500) == pytest.approx(density(0))


def test_geopotential_conversion_round_trips():
    from rocketry.atmosphere import geopotential_altitude

    for geometric in (0, 1_000, 11_019, 50_000, 80_000):
        assert geometric_altitude(geopotential_altitude(geometric)) == pytest.approx(
            geometric, rel=1e-9
        )


def test_the_two_altitude_scales_diverge_with_height():
    assert geometric_altitude(30_000) - 30_000 == pytest.approx(142, abs=5)
