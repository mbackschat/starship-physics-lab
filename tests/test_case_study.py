"""Chapter 6 and 7: weighing Starship, and what its weight implies.

The whole argument rests on one unpublished number, so the code that presents it
gets tested harder than the code that presents anything else.
"""

import pytest

from labbook.casestudy import (
    ESTIMATES,
    DryMassEstimate,
    payload_curve,
    weigh_from_burn,
)
from rocketry.library import load


@pytest.fixture(scope="module")
def lib():
    return load()


class TestWeighingFromABurn:
    """The article's method: measure a vehicle from an observed burn."""

    def test_reproduces_the_articles_bracket(self):
        low = weigh_from_burn(propellant_t=10.0, delta_v=138.9, isp=350)
        high = weigh_from_burn(propellant_t=10.7, delta_v=138.9, isp=350)
        assert low.mass_after_t == pytest.approx(242, abs=2)
        assert high.mass_after_t == pytest.approx(259, abs=2)

    def test_a_longer_burn_means_a_heavier_vehicle(self):
        short = weigh_from_burn(propellant_t=8.0, delta_v=138.9, isp=350)
        long = weigh_from_burn(propellant_t=12.0, delta_v=138.9, isp=350)
        assert long.mass_after_t > short.mass_after_t

    def test_it_measures_total_mass_not_dry_mass(self):
        """The distinction the article glides over, and it decides everything."""
        result = weigh_from_burn(propellant_t=10.7, delta_v=138.9, isp=350)
        assert result.mass_after_t > result.dry_mass_t(residual_t=40.0)
        assert result.dry_mass_t(residual_t=40.0) == pytest.approx(
            result.mass_after_t - 40.0, rel=1e-9
        )

    def test_burn_duration_and_propellant_agree(self):
        result = weigh_from_burn(propellant_t=10.7, delta_v=138.9, isp=350)
        assert result.burn_seconds(thrust_tf=250.0, engine_isp=327.0) == pytest.approx(
            14.0, rel=0.02
        )


class TestPayloadAgainstDryMass:
    """The single interaction the whole app exists for."""

    def test_mass_reaching_orbit_barely_moves(self, lib):
        """Build a lighter ship and the same total still arrives.

        The point of the whole chapter: only the split between vehicle and cargo
        changes. Not bit-for-bit identical, because a lighter stack lets the booster do
        marginally more. Under 1 % across a range where payload changes fourfold.
        """
        curve = payload_curve(lib, "starship_v3", dry_masses=[120, 160, 190, 220])
        arriving = [point.mass_in_orbit_t for point in curve]
        spread = (max(arriving) - min(arriving)) / (sum(arriving) / len(arriving))
        assert spread < 0.01
        payloads = [point.payload_t for point in curve]
        assert max(payloads) > 4 * min(payloads)

    def test_a_heavier_ship_costs_more_than_its_own_weight(self, lib):
        """Adding a tonne to the ship costs over a tonne of payload.

        The extra tonne has to be landed as well as lifted, so it drags a share
        of landing propellant up with it.
        """
        curve = payload_curve(lib, "starship_v3", dry_masses=[160, 161])
        cost = curve[0].payload_t - curve[1].payload_t
        assert 1.0 < cost < 1.5

    def test_the_articles_estimate_gives_about_forty_tonnes(self, lib):
        curve = payload_curve(lib, "starship_v3", dry_masses=[220])
        assert curve[0].payload_t == pytest.approx(40, abs=6)

    def test_spacex_claim_needs_a_much_lighter_ship(self, lib):
        curve = payload_curve(lib, "starship_v3", dry_masses=range(100, 261, 10))
        hundred = min(curve, key=lambda point: abs(point.payload_t - 100.0))
        assert 140 < hundred.dry_mass_t < 185

    def test_the_curve_is_sorted_and_complete(self, lib):
        curve = payload_curve(lib, "starship_v3", dry_masses=[220, 120, 160])
        assert [point.dry_mass_t for point in curve] == [120, 160, 220]


class TestPublishedEstimates:
    """Every number a reader is shown must say where it came from."""

    def test_the_estimates_span_the_real_disagreement(self):
        values = [estimate.dry_mass_t for estimate in ESTIMATES]
        assert min(values) <= 100
        assert max(values) >= 220

    def test_every_estimate_cites_a_source(self):
        for estimate in ESTIMATES:
            assert estimate.label
            assert estimate.source
            assert isinstance(estimate, DryMassEstimate)

    def test_estimates_are_ordered_lightest_first(self):
        values = [estimate.dry_mass_t for estimate in ESTIMATES]
        assert values == sorted(values)
