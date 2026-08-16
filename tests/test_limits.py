"""Reproducing a payload and being honestly modelled are two different questions.

The Space Shuttle answered the first and failed the second, and the calibration
framework had no way to say so: it had one axis where the problem has two. It
passed `MUST_REPRODUCE` at 29.1 t against a published 27.5 t while its boosters
and its main engines, which fire together in reality, were being flown one after
the other.

So a vehicle now declares what the model cannot represent about it, in the data
next to its provenance, and that declaration decides whether its agreement counts
as evidence.
"""

import pytest

from rocketry.library import load
from rocketry.limits import MODELLING_LIMITS, ModellingLimit, limit_for
from rocketry.vehicle import analyse, scenario


@pytest.fixture(scope="module")
def lib():
    return load()


class TestTheVocabulary:
    def test_every_limit_is_described(self):
        for limit in ModellingLimit:
            described = limit_for(limit)
            assert described.label
            assert described.explanation
            assert described.direction, f"{limit} must say which way the error goes"

    def test_descriptions_cover_the_enum(self):
        assert set(MODELLING_LIMITS) == set(ModellingLimit)

    def test_a_limit_that_distorts_nothing_would_not_be_one(self):
        for described in MODELLING_LIMITS.values():
            assert described.affects_payload or described.affects_ascent


class TestWhatTheLibraryDeclares:
    """The declarations are claims about the model, and are checked like any other."""

    def test_a_parallel_burn_vehicle_is_not_evidence(self, lib):
        assert not lib.vehicle("space_shuttle").payload_is_evidence
        assert not lib.vehicle("ariane_64").payload_is_evidence

    def test_a_serial_vehicle_is(self, lib):
        assert lib.vehicle("falcon9_droneship").payload_is_evidence
        assert lib.vehicle("saturn_v").payload_is_evidence

    def test_mixed_engines_do_not_disqualify_the_payload(self, lib):
        # The velocity budget uses the stage's blended Isp, which is right. Only
        # the flown simulation cares which engines produce it.
        starship = lib.vehicle("starship_v3")
        assert ModellingLimit.MIXED_ENGINES in starship.modelling_limits
        assert starship.payload_is_evidence

    def test_the_declared_direction_is_the_observed_one(self, lib):
        """A parallel burn flown as a sequence must flatter the vehicle."""
        for key in ("space_shuttle", "ariane_64"):
            vehicle = lib.vehicle(key)
            claimed = vehicle.payload_leo_t
            assert claimed is not None
            assert scenario(lib, key).solve_payload() > claimed, (
                f"{key} declares parallel_burn, which should come out high"
            )

    def test_an_unknown_limit_is_refused_at_load_time(self, lib):
        from rocketry.models import Vehicle

        with pytest.raises(ValueError):
            Vehicle(
                name="Nonsense",
                operator="test",
                stages=("falcon9_stage1",),
                modelling_limits=("hand_waving",),
            )


class TestEveryStageHasAnEngineItActuallyUses:
    """The Shuttle's boosters named the RS-25 because the schema needed a key.

    That is a placeholder standing in a field the ascent model reads for thrust,
    so it computed a liftoff thrust-to-weight of 0.19 and refused to fly the
    vehicle at all. The velocity budget never noticed, because it reads the
    stage's own `isp_ascent_s`.
    """

    def test_the_boosters_are_solid_motors(self, lib):
        stage = lib.stage("shuttle_srb_pair")
        engine = lib.engines[stage.engine]
        assert "solid" in engine.propellants.lower()

    def test_the_stack_can_now_leave_the_pad(self, lib):
        from rocketry.ascent import simulate

        result = simulate(analyse(lib, "space_shuttle"))
        assert not result.crashed
        assert result.final_speed > 5000

    def test_the_velocity_budget_did_not_move(self, lib):
        # Engines supply thrust; the stage supplies Isp. Swapping one must not
        # touch the other, or the two models are entangled.
        assert scenario(lib, "space_shuttle").solve_payload() == pytest.approx(29.1, rel=0.01)
