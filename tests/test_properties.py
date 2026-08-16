"""Invariants that must hold for any inputs, not just the documented cases.

Golden numbers catch drift at known points. These catch it everywhere else.
"""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rocketry.constants import V_EQUATORIAL
from rocketry.orbit import is_reachable, rotation_bonus
from rocketry.payload import dry_mass_for_payload, payload_for_stage
from rocketry.reuse import Burn, recovery_propellant
from rocketry.scaling import scaled_dry_mass
from rocketry.staging import two_stage_payload
from rocketry.tsiolkovsky import (
    delta_v,
    final_mass,
    mass_after_burn,
    mass_ratio,
    propellant_from_final,
    propellant_from_initial,
)

masses = st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False)
velocities = st.floats(min_value=1.0, max_value=12_000.0, allow_nan=False)
isps = st.floats(min_value=100.0, max_value=500.0, allow_nan=False)
fractions = st.floats(min_value=0.01, max_value=0.99, allow_nan=False)


class TestRocketEquationInvariants:
    @given(m0=masses, ratio=fractions, isp=isps)
    def test_delta_v_rises_with_mass_ratio(self, m0, ratio, isp):
        smaller_burn = delta_v(m0, m0 * ratio, isp)
        bigger_burn = delta_v(m0, m0 * ratio * 0.9, isp)
        assert bigger_burn > smaller_burn

    @given(m0=masses, ratio=fractions, isp=isps)
    def test_delta_v_rises_with_efficiency(self, m0, ratio, isp):
        assert delta_v(m0, m0 * ratio, isp * 1.1) > delta_v(m0, m0 * ratio, isp)

    @given(m0=masses, dv=velocities, isp=isps)
    def test_the_two_propellant_forms_describe_the_same_burn(self, m0, dv, isp):
        burnt = propellant_from_initial(m0, dv, isp)
        assert propellant_from_final(m0 - burnt, dv, isp) == pytest.approx(burnt, rel=1e-9)

    @given(m0=masses, dv=velocities, isp=isps)
    def test_final_mass_and_delta_v_are_inverses(self, m0, dv, isp):
        mf = final_mass(m0, dv, isp)
        assert delta_v(m0, mf, isp) == pytest.approx(dv, rel=1e-9)

    @given(mf=masses, dv=velocities, isp=isps)
    def test_weighing_a_burn_recovers_the_mass_that_produced_it(self, mf, dv, isp):
        burnt = propellant_from_final(mf, dv, isp)
        assert mass_after_burn(burnt, dv, isp) == pytest.approx(mf, rel=1e-9)

    @given(dv=velocities, isp=isps)
    def test_mass_ratio_always_exceeds_one(self, dv, isp):
        assert mass_ratio(dv, isp) > 1.0

    @given(m0=masses, mf=masses, isp=isps)
    def test_a_burn_never_increases_mass(self, m0, mf, isp):
        if mf > m0:
            with pytest.raises(ValueError, match="cannot increase mass"):
                delta_v(m0, mf, isp)
        else:
            assert delta_v(m0, mf, isp) >= 0


class TestPayloadInvariants:
    @given(
        dry=st.floats(min_value=1.0, max_value=500.0),
        prop=st.floats(min_value=10.0, max_value=3000.0),
        isp=isps,
        dv=velocities,
    )
    def test_payload_solver_inverts_its_own_forward_model(self, dry, prop, isp, dv):
        payload = payload_for_stage(dry_mass=dry, propellant=prop, isp=isp, delta_v=dv)
        recovered = dry_mass_for_payload(
            target_payload=payload, propellant=prop, isp=isp, delta_v=dv
        )
        assert recovered == pytest.approx(dry, rel=1e-6, abs=1e-9)

    @given(
        dry=st.floats(min_value=1.0, max_value=500.0),
        prop=st.floats(min_value=10.0, max_value=3000.0),
        isp=isps,
        dv=velocities,
    )
    def test_heavier_stage_always_means_less_payload(self, dry, prop, isp, dv):
        light = payload_for_stage(dry_mass=dry, propellant=prop, isp=isp, delta_v=dv)
        heavy = payload_for_stage(dry_mass=dry + 1.0, propellant=prop, isp=isp, delta_v=dv)
        assert heavy == pytest.approx(light - 1.0, rel=1e-9, abs=1e-9)


class TestReuseInvariants:
    @given(dry=masses, dv=velocities, isp=isps)
    def test_a_bigger_manoeuvre_always_costs_more(self, dry, dv, isp):
        cheap = recovery_propellant(dry, [Burn(dv, isp)])
        dear = recovery_propellant(dry, [Burn(dv * 1.1, isp)])
        assert dear > cheap

    @given(dry=masses, dv=velocities, isp=isps)
    def test_burns_compose_multiplicatively(self, dry, dv, isp):
        """Two half-sized burns cost exactly the same as one full-sized burn."""
        one = recovery_propellant(dry, [Burn(dv, isp)])
        two = recovery_propellant(dry, [Burn(dv / 2, isp), Burn(dv / 2, isp)])
        assert two == pytest.approx(one, rel=1e-9)

    @given(dry=masses)
    def test_no_burns_costs_nothing(self, dry):
        assert recovery_propellant(dry, []) == pytest.approx(0.0, abs=1e-12)


class TestOrbitInvariants:
    @given(
        inc=st.floats(min_value=0.0, max_value=180.0),
        lat=st.floats(min_value=0.0, max_value=80.0),
    )
    def test_rotation_bonus_never_exceeds_earths_surface_speed(self, inc, lat):
        if not is_reachable(inc, lat):
            return
        assert abs(rotation_bonus(inc, lat)) <= V_EQUATORIAL + 1e-9

    @given(lat=st.floats(min_value=0.0, max_value=80.0))
    def test_polar_orbits_get_no_help_from_any_launch_site(self, lat):
        assert rotation_bonus(90.0, lat) == pytest.approx(0.0, abs=1e-9)

    @given(
        inc=st.floats(min_value=0.0, max_value=90.0),
        lat=st.floats(min_value=0.0, max_value=80.0),
    )
    def test_bonus_depends_only_on_inclination_not_latitude(self, inc, lat):
        """A non-obvious consequence of the geometry, worth locking down."""
        if not is_reachable(inc, lat) or not is_reachable(inc, 0.0):
            return
        assert rotation_bonus(inc, lat) == pytest.approx(rotation_bonus(inc, 0.0), rel=1e-9)


class TestScalingInvariants:
    @given(dry=masses, ref_prop=masses, prop=masses)
    def test_zero_exponent_freezes_the_mass(self, dry, ref_prop, prop):
        result = scaled_dry_mass(
            reference_dry=dry, reference_propellant=ref_prop, propellant=prop, exponent=0.0
        )
        assert result == pytest.approx(dry, rel=1e-9)

    @given(dry=masses, ref_prop=masses)
    def test_scaling_to_the_same_size_is_the_identity(self, dry, ref_prop):
        for exponent in (0.0, 0.5, 0.8, 1.0):
            result = scaled_dry_mass(
                reference_dry=dry,
                reference_propellant=ref_prop,
                propellant=ref_prop,
                exponent=exponent,
            )
            assert result == pytest.approx(dry, rel=1e-9)


class TestTheCentralInsight:
    """Correction C15, as an invariant rather than a claim.

    The rocket equation fixes what arrives in orbit. Building a lighter upper
    stage does not change the total that gets there; it changes how much of that
    total is cargo. This is the single idea the whole application exists to
    convey, so it gets a property test rather than one example.
    """

    @given(
        booster=st.floats(min_value=2000.0, max_value=5000.0),
        ship=st.floats(min_value=500.0, max_value=2500.0),
        exponent=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=50)
    def test_mass_in_orbit_ignores_upper_stage_dry_mass(self, booster, ship, exponent):
        baseline = two_stage_payload(
            booster_propellant=booster, ship_propellant=ship, scaling_exponent=exponent
        )
        lighter = two_stage_payload(
            booster_propellant=booster,
            ship_propellant=ship,
            scaling_exponent=exponent,
            ship_reference_dry=110.0,
        )
        assert lighter.mass_in_orbit == pytest.approx(baseline.mass_in_orbit, rel=1e-6)
        assert lighter.payload > baseline.payload

    @given(
        booster=st.floats(min_value=2000.0, max_value=5000.0),
        ship=st.floats(min_value=500.0, max_value=2500.0),
    )
    @settings(max_examples=50)
    def test_every_tonne_saved_on_the_stage_becomes_a_tonne_of_cargo(self, booster, ship):
        baseline = two_stage_payload(booster_propellant=booster, ship_propellant=ship)
        lighter = two_stage_payload(
            booster_propellant=booster, ship_propellant=ship, ship_reference_dry=219.0
        )
        saved = baseline.ship_dry - lighter.ship_dry
        gained = lighter.payload - baseline.payload
        assert gained == pytest.approx(saved, rel=1e-6)

    @given(
        booster=st.floats(min_value=2500.0, max_value=5000.0),
        ship=st.floats(min_value=500.0, max_value=2500.0),
    )
    @settings(max_examples=50)
    def test_the_stages_always_add_up_to_the_mission_budget(self, booster, ship):
        result = two_stage_payload(booster_propellant=booster, ship_propellant=ship)
        assert result.booster_delta_v + result.ship_delta_v == pytest.approx(9404.0, rel=1e-6)
        assert math.isfinite(result.payload)


class TestRecoveryBurnsAreRealManoeuvres:
    """A burn that creates propellant is not a burn.

    `Burn` was a plain dataclass with no domain validation, so a negative
    delta-v produced a negative reserve and a stage carrying 10 t could report
    13 t available for ascent. `Stage` already refuses to promise away more
    propellant than it holds; this closes the same hole one layer down.
    """

    def test_a_burn_cannot_take_the_vehicle_backwards(self):
        with pytest.raises(ValueError, match="delta_v"):
            Burn(delta_v=-100.0, isp=300.0)

    @pytest.mark.parametrize("isp", [0.0, -1.0])
    def test_a_burn_needs_a_real_engine(self, isp: float):
        with pytest.raises(ValueError, match="isp"):
            Burn(delta_v=100.0, isp=isp)

    def test_an_ordinary_burn_is_still_accepted(self):
        assert Burn(delta_v=350.0, isp=300.0, label="landing burn").delta_v == 350.0
        assert Burn(delta_v=0.0, isp=300.0).delta_v == 0.0

    @given(
        dry=st.floats(min_value=1.0, max_value=1000.0),
        delta_v=st.floats(min_value=0.0, max_value=4000.0),
        isp=st.floats(min_value=50.0, max_value=500.0),
    )
    def test_recovery_propellant_is_never_negative(self, dry, delta_v, isp):
        assert recovery_propellant(dry, [Burn(delta_v=delta_v, isp=isp)]) >= 0.0
