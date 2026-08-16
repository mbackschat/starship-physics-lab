"""Does the model reproduce what each rocket is actually known to lift?

This is the test that decides whether anything else in the project can be
believed. A model that cannot recover Falcon 9's published payload has no
business making claims about Starship's.

Vehicles that do not reproduce are listed explicitly with a reason, because a
silent exclusion is indistinguishable from a bug.
"""

import pytest

from rocketry.library import load
from rocketry.vehicle import LEO_MISSION_DELTA_V, scenario

TOLERANCE = 0.15
"""Fifteen per cent. Published payloads are quoted for specific orbits and
specific trajectories; a single mission budget cannot match all of them exactly.
"""

MUST_REPRODUCE = [
    "falcon9_droneship",
    "space_shuttle",
    "saturn_v",
    "new_glenn",
    "long_march_10b",
    "raptor33_raptor4",
    "raptor33_expendable",
]

KNOWN_EXCEPTIONS = {
    "starship_v3": (
        "The claim IS the subject of the dispute. Reproducing it would mean "
        "assuming the answer to chapter 7."
    ),
    "starship_v4": "Announced, never flown, and rests on the same contested dry mass.",
    "falcon9_expendable": (
        "22.8 t is flown on a flatter, more efficient trajectory than the single "
        "mission budget used here, which is calibrated for recovery profiles."
    ),
    "ariane_64": (
        "Boosters and core burn together. Representing a parallel burn as a "
        "sequence of stages always flatters the vehicle."
    ),
    "raptor33_raptor3": (
        "The article's own bookkeeping for this concept differs from the "
        "library's; see docs/physics-reference.md section 3.6."
    ),
    "raptor33_pessimistic": "Same as raptor33_raptor3, the sensitivity case of it.",
}


@pytest.fixture(scope="module")
def lib():
    return load()


@pytest.mark.parametrize("key", MUST_REPRODUCE)
def test_vehicle_reproduces_its_published_payload(lib, key):
    claimed = lib.vehicle(key).payload_leo_t
    assert claimed is not None
    computed = scenario(lib, key).solve_payload(LEO_MISSION_DELTA_V)
    assert computed == pytest.approx(claimed, rel=TOLERANCE)


def test_every_vehicle_is_either_checked_or_excused(lib):
    """No vehicle may quietly avoid this test by not being mentioned."""
    with_claims = {key for key, v in lib.vehicles.items() if v.payload_leo_t is not None}
    accounted = set(MUST_REPRODUCE) | set(KNOWN_EXCEPTIONS)
    assert with_claims - accounted == set(), "add these to MUST_REPRODUCE or KNOWN_EXCEPTIONS"
    assert accounted - with_claims == set(), "these no longer exist or lost their payload figure"


def test_every_exception_gives_a_reason(lib):
    for key, reason in KNOWN_EXCEPTIONS.items():
        assert len(reason) > 40, f"{key} needs a real explanation, not a shrug"


def test_excused_vehicles_really_do_miss(lib):
    """If an excuse stops being needed, the excuse should be deleted."""
    still_needed = []
    for key in KNOWN_EXCEPTIONS:
        claimed = lib.vehicle(key).payload_leo_t
        computed = scenario(lib, key).solve_payload(LEO_MISSION_DELTA_V)
        if claimed and abs(computed - claimed) / claimed > TOLERANCE:
            still_needed.append(key)
    assert set(still_needed) == set(KNOWN_EXCEPTIONS), (
        "some excused vehicles now reproduce; move them to MUST_REPRODUCE"
    )


def test_the_calibration_reference_is_the_tightest(lib):
    """Falcon 9 has the best public data, so it should fit best."""
    error = abs(
        scenario(lib, "falcon9_droneship").solve_payload(LEO_MISSION_DELTA_V)
        - (lib.vehicle("falcon9_droneship").payload_leo_t or 0)
    )
    assert error < 1.0


def test_multi_stage_vehicles_are_supported(lib):
    """Saturn V and Ariane 64 have three stages. The walk must handle any depth."""
    assert len(scenario(lib, "saturn_v").stages) == 3
    assert len(scenario(lib, "ariane_64").stages) == 3
