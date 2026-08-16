"""Golden numbers from docs/physics-reference.md section 7.

Every value here was recomputed independently during the verification of the
source article. If one of these moves, either the model changed on purpose and
this file must be updated deliberately, or something broke. There is no third
option.

Default tolerance is 1 % unless a test says otherwise.
"""

import pytest

from rocketry.constants import KMH_TO_MS
from rocketry.dynamics import (
    acceleration_after,
    gravity_thrust_fraction,
    net_acceleration_g,
    thrust_to_weight,
)
from rocketry.orbit import InclinationUnreachableError, orbital_velocity, rotation_bonus
from rocketry.payload import payload_for_stage
from rocketry.reentry import area_ratio, diameter_for_equal_loading
from rocketry.reuse import Burn, mass_at_separation, recovery_propellant
from rocketry.scaling import scaled_dry_mass
from rocketry.staging import (
    REFERENCE_STAGING,
    StagingModel,
    optimal_delta_v_split,
    optimal_staging_speed,
    two_stage_payload,
)
from rocketry.tsiolkovsky import (
    binary_velocity,
    delta_v,
    exhaust_velocity,
    final_mass,
    mass_after_burn,
    mass_ratio,
    propellant_burnt,
    propellant_from_final,
    propellant_from_initial,
)

pytestmark = pytest.mark.golden

PCT_1 = 0.01
PCT_3 = 0.03
PCT_5 = 0.05


class TestRocketEquation:
    """Section 7, block 1: ideal delta-v and its inverse forms."""

    def test_starship_ideal_delta_v(self):
        assert delta_v(m0=1900, mf=300, isp=365) == pytest.approx(6609.3, rel=PCT_1)

    def test_super_heavy_ideal_delta_v(self):
        assert delta_v(m0=5850, mf=2530, isp=340) == pytest.approx(2796.1, rel=PCT_1)

    def test_falcon9_second_stage_delta_v(self):
        assert delta_v(m0=128.5, mf=21.5, isp=348) == pytest.approx(6104.3, rel=PCT_1)

    def test_falcon9_second_stage_with_deorbit_reserve(self):
        assert delta_v(m0=128.5, mf=22.0, isp=348) == pytest.approx(6025.4, rel=PCT_1)

    def test_mass_ratio(self):
        assert mass_ratio(6609, isp=365) == pytest.approx(6.333, rel=PCT_1)

    def test_propellant_from_final_mass(self):
        assert propellant_from_final(300, 6609, isp=365) == pytest.approx(1600.0, rel=PCT_1)

    def test_propellant_from_initial_mass(self):
        assert propellant_from_initial(5850, 2796, isp=340) == pytest.approx(3320.0, rel=PCT_1)

    def test_final_mass(self):
        assert final_mass(1293, 5600, isp=365) == pytest.approx(270.6, rel=PCT_1)

    def test_exhaust_velocity(self):
        assert exhaust_velocity(350) == pytest.approx(3433.3, rel=PCT_1)

    def test_binary_velocity_uses_the_correct_constant(self):
        """Correction C1: the article prints 2428 m/s, which uses a wrong constant."""
        assert binary_velocity(350) == pytest.approx(2379.6, rel=PCT_1)
        assert binary_velocity(350) != pytest.approx(2428, rel=PCT_1)

    def test_forms_agree(self):
        """propellant_from_initial and propellant_from_final describe the same burn."""
        m0, dv, isp = 5850.0, 2796.0, 340.0
        burnt = propellant_from_initial(m0, dv, isp)
        assert propellant_from_final(m0 - burnt, dv, isp) == pytest.approx(burnt, rel=1e-9)


class TestWeighingByBurn:
    """Section 7, block 4: how the article weighs Starship from a 14 s relight."""

    def test_propellant_burnt_in_14_seconds(self):
        assert propellant_burnt(thrust_tf=250, isp=327, seconds=14) == pytest.approx(
            10.70, rel=PCT_1
        )

    def test_mass_after_burn_low_estimate(self):
        assert mass_after_burn(propellant=10.0, dv=138.9, isp=350) == pytest.approx(
            242.2, rel=PCT_1
        )

    def test_mass_after_burn_high_estimate(self):
        assert mass_after_burn(propellant=10.7, dv=138.9, isp=350) == pytest.approx(
            259.2, rel=PCT_1
        )


class TestPayloadSolver:
    """Section 7, block 2, and correction C15: the number that decides everything."""

    def test_articles_dry_mass_estimate_gives_40_tonnes(self):
        payload = payload_for_stage(
            dry_mass=220, propellant=1600, isp=365, delta_v=6609, residual_propellant=40
        )
        assert payload == pytest.approx(40.0, abs=1.0)

    def test_spacex_claim_requires_160_tonnes_dry(self):
        payload = payload_for_stage(
            dry_mass=160, propellant=1600, isp=365, delta_v=6609, residual_propellant=40
        )
        assert payload == pytest.approx(100.0, abs=1.0)

    def test_mass_in_orbit_is_fixed_regardless_of_dry_mass(self):
        """The rocket equation fixes what arrives; only its composition is negotiable."""
        arrivals = {
            payload_for_stage(
                dry_mass=dry, propellant=1600, isp=365, delta_v=6609, residual_propellant=40
            )
            + dry
            + 40
            for dry in (220, 190, 160, 120, 85)
        }
        assert max(arrivals) - min(arrivals) < 0.5


class TestReuse:
    """Section 7, block 3: what coming home costs."""

    def test_super_heavy_return_budget_pessimistic_isp(self):
        burns = [Burn(delta_v=600, isp=330), Burn(delta_v=1800, isp=330)]
        assert recovery_propellant(dry_mass=300, burns=burns) == pytest.approx(330.0, rel=PCT_1)

    def test_super_heavy_return_budget_optimistic_isp(self):
        burns = [Burn(delta_v=600, isp=327), Burn(delta_v=1800, isp=350)]
        assert recovery_propellant(dry_mass=300, burns=burns) == pytest.approx(311.0, rel=PCT_1)

    def test_per_tonne_of_dry_mass(self):
        burns = [Burn(delta_v=600, isp=330), Burn(delta_v=1800, isp=330)]
        assert recovery_propellant(dry_mass=1.0, burns=burns) == pytest.approx(1.10, rel=PCT_1)

    def test_booster_mass_at_separation(self):
        """Article's Raptor 33: brake 10 000 -> 5300 km/h, then a 500 m/s landing."""
        burns = [Burn(delta_v=500, isp=327), Burn(delta_v=1305.6, isp=350)]
        assert mass_at_separation(dry_mass=300, burns=burns) == pytest.approx(512.8, rel=PCT_1)


class TestThrustAndLosses:
    """Section 7, block 5, and correction C4."""

    def test_starship_liftoff_twr(self):
        assert thrust_to_weight(thrust_tf=8250, mass_t=5850) == pytest.approx(1.410, rel=PCT_1)

    def test_net_acceleration_at_liftoff(self):
        assert net_acceleration_g(1.410) == pytest.approx(0.410, rel=PCT_1)

    def test_gravity_eats_most_of_the_thrust(self):
        assert gravity_thrust_fraction(1.410) == pytest.approx(0.709, rel=PCT_1)

    def test_starship_acceleration_after_40_seconds(self):
        assert acceleration_after(
            seconds=40, twr_initial=1.410, mass_flow_fraction=0.00431
        ) == pytest.approx(0.704, rel=PCT_1)

    def test_falcon9_acceleration_after_40_seconds(self):
        """Correction C4: the article says 0.875 g. At equal liftoff TWR it is 0.766 g."""
        result = acceleration_after(seconds=40, twr_initial=1.412, mass_flow_fraction=0.00501)
        assert result == pytest.approx(0.766, rel=PCT_1)
        assert result != pytest.approx(0.875, rel=PCT_1)


class TestOrbitAndInclination:
    """Section 7, block 6."""

    def test_orbital_velocity_at_200_km(self):
        assert orbital_velocity(altitude_m=200_000) == pytest.approx(7784, rel=PCT_1)

    def test_rotation_bonus_due_east(self):
        assert rotation_bonus(inclination_deg=25.997, latitude_deg=25.997) == pytest.approx(
            418.2, rel=PCT_1
        )

    def test_rotation_bonus_starlink_inclination(self):
        assert rotation_bonus(inclination_deg=53.0, latitude_deg=25.997) == pytest.approx(
            280.0, rel=PCT_1
        )

    def test_rotation_bonus_polar(self):
        assert rotation_bonus(inclination_deg=90.0, latitude_deg=25.997) == pytest.approx(
            0.0, abs=1.0
        )

    def test_sun_synchronous_costs_extra(self):
        assert rotation_bonus(inclination_deg=97.4, latitude_deg=25.997) < 0

    def test_inclination_below_launch_latitude_is_unreachable(self):
        with pytest.raises(InclinationUnreachableError):
            rotation_bonus(inclination_deg=10.0, latitude_deg=25.997)


class TestRedesignChain:
    """Section 7, block 7: the article's Raptor 33 / Raptor 4, staging at 10 000 km/h."""

    BOOSTER_DV = 3907.0

    def test_mass_left_at_staging(self):
        assert final_mass(5850, self.BOOSTER_DV, isp=340) == pytest.approx(1813, rel=PCT_1)

    def test_mass_available_for_upper_stage(self):
        left = final_mass(5850, self.BOOSTER_DV, isp=340)
        booster = mass_at_separation(
            dry_mass=300, burns=[Burn(delta_v=500, isp=327), Burn(delta_v=1305.6, isp=350)]
        )
        assert left - booster == pytest.approx(1293, rel=PCT_1)

    def test_upper_stage_reaches_orbit(self):
        assert final_mass(1293, 5600, isp=365) == pytest.approx(270.6, rel=PCT_1)

    def test_payload_beats_the_promise(self):
        """160 t of stage plus landing propellant leaves over 100 t of payload."""
        in_orbit = final_mass(1293, 5600, isp=365)
        assert in_orbit - 160 == pytest.approx(110, rel=PCT_3)


class TestStagingOptimum:
    """Section 3.7 and 7: the article's central thesis, checked independently."""

    @pytest.fixture
    def model(self) -> StagingModel:
        return StagingModel()

    def test_optimum_is_far_above_the_as_flown_split(self, model: StagingModel):
        # The article's numbers are km/h; the model computes in m/s.
        assert optimal_staging_speed(model) == pytest.approx(
            11500 * KMH_TO_MS, abs=1000 * KMH_TO_MS
        )

    def test_optimum_roughly_doubles_the_payload(self, model: StagingModel):
        as_flown = model.payload_at(REFERENCE_STAGING)
        best = model.payload_at(optimal_staging_speed(model))
        assert best > 2 * as_flown

    def test_as_flown_split_reproduces_the_articles_ballpark(self, model: StagingModel):
        assert model.payload_at(REFERENCE_STAGING) == pytest.approx(57, rel=0.15)

    def test_equal_stages_are_optimal_when_stages_are_identical(self):
        share = optimal_delta_v_split(isp=350, structural_coefficient=0.08, total_delta_v=9404)
        assert share == pytest.approx(0.50, abs=0.02)


class TestScalingLaw:
    """Section 7, block 9, and section 3.8: the V4 stretch."""

    def test_linear_scaling(self):
        assert scaled_dry_mass(
            reference_dry=220, reference_propellant=1600, propellant=2300, exponent=1.0
        ) == pytest.approx(316.2, rel=PCT_1)

    def test_no_scaling(self):
        assert scaled_dry_mass(
            reference_dry=220, reference_propellant=1600, propellant=2300, exponent=0.0
        ) == pytest.approx(220.0, rel=PCT_1)

    def test_v4_as_announced_with_linear_scaling(self):
        result = two_stage_payload(
            booster_propellant=4050, ship_propellant=2300, scaling_exponent=1.0
        )
        assert result.payload == pytest.approx(12, abs=3)

    def test_v4_if_dry_mass_does_not_grow(self):
        result = two_stage_payload(
            booster_propellant=4050, ship_propellant=2300, scaling_exponent=0.0
        )
        assert result.payload == pytest.approx(108, rel=PCT_5)

    def test_v4_booster_with_todays_ship(self):
        result = two_stage_payload(
            booster_propellant=4050, ship_propellant=1600, scaling_exponent=1.0
        )
        assert result.payload == pytest.approx(54, rel=PCT_5)

    def test_v3_control_reproduces_the_articles_model(self):
        result = two_stage_payload(
            booster_propellant=3650, ship_propellant=1600, scaling_exponent=1.0
        )
        assert result.payload == pytest.approx(40, abs=2)
        assert result.liftoff_mass == pytest.approx(5850, rel=PCT_1)
        assert result.mass_in_orbit == pytest.approx(300, abs=5)


class TestReentry:
    """Section 7, block 10: the square-cube law."""

    def test_super_heavy_frontal_area_versus_falcon9(self):
        assert area_ratio(9.0, 3.66) == pytest.approx(6.047, rel=PCT_1)

    def test_diameter_needed_for_equal_ballistic_loading(self):
        assert diameter_for_equal_loading(reference_diameter=3.66, mass_ratio=12) == pytest.approx(
            12.68, rel=PCT_1
        )


class TestCalibration:
    """Integration-level guard from section 7.

    If either of these drifts outside its band the model is miscalibrated and
    every downstream conclusion is worthless.
    """

    def test_starship_stack_total_delta_v_is_in_the_normal_band(self):
        ship = delta_v(m0=1900, mf=300, isp=365)
        booster = delta_v(m0=5850, mf=2530, isp=340)
        assert ship + booster == pytest.approx(9400, abs=100)

    def test_falcon9_total_delta_v_is_in_the_normal_band(self):
        stage2 = delta_v(m0=128.5, mf=22.0, isp=348)
        stage1 = delta_v(m0=541.0, mf=181.0, isp=301)
        assert stage1 + stage2 == pytest.approx(9250, abs=150)

    def test_super_heavy_provides_only_30_percent_of_the_delta_v(self):
        ship = delta_v(m0=1900, mf=300, isp=365)
        booster = delta_v(m0=5850, mf=2530, isp=340)
        assert booster / (ship + booster) == pytest.approx(0.30, abs=0.01)
