"""Asking 'what if this stage were different' without editing the library.

Chapter 5 varies how a booster comes home; chapter 7 will vary how heavy a ship
is. Both need the same seam, so it is built once and tested here.
"""

import pytest

from rocketry.library import load
from rocketry.reuse import RECOVERY_PROFILES, RecoveryProfile, profile_for
from rocketry.vehicle import analyse, scenario, with_stage


@pytest.fixture(scope="module")
def lib():
    return load()


class TestRecoveryProfiles:
    def test_every_profile_is_described(self):
        for profile in RecoveryProfile:
            described = profile_for(profile)
            assert described.label
            assert described.explanation

    def test_expendable_keeps_nothing_back(self):
        assert profile_for(RecoveryProfile.EXPENDABLE).burns == ()

    def test_returning_to_the_pad_costs_the_most(self):
        rtls = sum(burn.delta_v for burn in profile_for(RecoveryProfile.RTLS).burns)
        ship = sum(burn.delta_v for burn in profile_for(RecoveryProfile.DRONESHIP).burns)
        assert rtls > ship > 0

    def test_profiles_cover_the_enum(self):
        assert set(RECOVERY_PROFILES) == set(RecoveryProfile)


class TestStageOverride:
    def test_overriding_a_stage_changes_the_answer(self, lib):
        baseline = analyse(lib, "falcon9_droneship")
        lighter = with_stage(lib, "falcon9_droneship", "falcon9_stage2", dry_mass_t=2.0)
        assert lighter.total_delta_v > baseline.total_delta_v

    def test_overriding_leaves_the_library_untouched(self, lib):
        before = lib.stage("falcon9_stage2").dry_mass_t
        with_stage(lib, "falcon9_droneship", "falcon9_stage2", dry_mass_t=2.0)
        assert lib.stage("falcon9_stage2").dry_mass_t == before

    def test_a_stage_not_on_this_vehicle_is_refused(self, lib):
        with pytest.raises(ValueError, match="does not fly"):
            with_stage(lib, "falcon9_droneship", "starship_v3", dry_mass_t=1.0)

    def test_recovery_can_be_swapped_wholesale(self, lib):
        expendable = with_stage(
            lib,
            "falcon9_droneship",
            "falcon9_stage1",
            recovery=profile_for(RecoveryProfile.EXPENDABLE).as_recovery(),
        )
        assert expendable.stages[0].recovery_reserve_t == 0.0


class TestWhatReuseCosts:
    """The chapter 5 result: coming home is paid for on the way up."""

    def test_payload_falls_as_recovery_gets_more_demanding(self, lib):
        payloads = []
        for profile in (
            RecoveryProfile.EXPENDABLE,
            RecoveryProfile.DRONESHIP,
            RecoveryProfile.RTLS,
        ):
            vehicle = with_stage(
                lib,
                "falcon9_droneship",
                "falcon9_stage1",
                recovery=profile_for(profile).as_recovery(),
            )
            payloads.append(vehicle.total_delta_v)
        assert payloads == sorted(payloads, reverse=True)

    def test_droneship_recovery_costs_falcon9_about_a_fifth_of_its_orbital_mass(self, lib):
        """Published figures: 22.8 t expendable against 17.5 t recovered."""
        expendable = analyse(lib, "falcon9_expendable")
        recovered = analyse(lib, "falcon9_droneship")
        assert expendable.payload_t / recovered.payload_t == pytest.approx(1.30, rel=0.05)


class TestOverridesAreValidated:
    """The what-if seam must reject nonsense rather than answer it confidently.

    `model_copy(update=...)` does not validate, so this seam accepted anything:
    a negative dry mass produced a confident payload, and a misspelled field was
    silently ignored and returned the baseline unchanged. The second is the
    worse of the two, because nothing about the answer looks wrong.
    """

    def test_a_negative_dry_mass_is_rejected(self, lib):
        with pytest.raises(ValueError):
            scenario(lib, "starship_v3", starship_v3={"dry_mass_t": -100.0})

    def test_a_zero_specific_impulse_is_rejected(self, lib):
        with pytest.raises(ValueError):
            scenario(lib, "starship_v3", starship_v3={"isp_ascent_s": 0.0})

    def test_a_misspelled_field_is_rejected_rather_than_ignored(self, lib):
        # Silently returning the baseline is the failure mode that hides.
        with pytest.raises(ValueError, match="dry_mass"):
            scenario(lib, "starship_v3", starship_v3={"dry_mass": 165.0})

    def test_with_stage_validates_the_same_way(self, lib):
        with pytest.raises(ValueError):
            with_stage(lib, "starship_v3", "starship_v3", dry_mass_t=-1.0)
        with pytest.raises(ValueError, match="dry_mass"):
            with_stage(lib, "starship_v3", "starship_v3", dry_mass=165.0)

    def test_a_valid_override_still_works(self, lib):
        case = scenario(lib, "starship_v3", starship_v3={"dry_mass_t": 165.0})
        assert case.stages[-1].dry_mass_t == pytest.approx(165.0)
        assert case.solve_payload() > 0

    def test_an_override_that_over_commits_propellant_is_caught(self, lib):
        # Stage already validates this at load time; the seam must not be a way
        # around it.
        with pytest.raises(ValueError, match="propellant"):
            scenario(lib, "starship_v3", starship_v3={"propellant_t": 1.0})
