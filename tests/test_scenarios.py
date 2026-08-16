"""Asking 'what if this stage were different' without editing the library.

Chapter 5 varies how a booster comes home; chapter 7 will vary how heavy a ship
is. Both need the same seam, so it is built once and tested here.
"""

import pytest

from rocketry.library import load
from rocketry.reuse import RECOVERY_PROFILES, RecoveryProfile, profile_for
from rocketry.vehicle import analyse, with_stage


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
