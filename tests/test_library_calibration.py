"""Does the model reproduce what each rocket is actually known to lift?

This is the test that decides whether anything else in the project can be
believed. A model that cannot recover Falcon 9's published payload has no
business making claims about Starship's.

**There are two axes here and they are not the same question.** A vehicle can
land on its published payload while being modelled as something it is not, and
then the agreement is a coincidence rather than a calibration. So the vehicles
split three ways, and only the first way is evidence:

- **Not honestly modelled.** It declares a `modelling_limits` entry that
  distorts payload, so what it computes is not asked to mean anything. The
  declaration lives in `data/vehicles.yaml`, not here, because it is a fact
  about the vehicle rather than about this test file.
- **Excused.** Honestly modelled, but its published figure is not one this model
  should be expected to match, for a reason given by name.
- **Everything else must reproduce.**

Nothing may be silently absent from all three, and an excuse that has stopped
being needed must be deleted rather than carried.
"""

import pytest

from rocketry.library import Library, load
from rocketry.vehicle import LEO_MISSION_DELTA_V, scenario

TOLERANCE = 0.15
"""Fifteen per cent. Published payloads are quoted for specific orbits and
specific trajectories; a single mission budget cannot match all of them exactly.
"""

KNOWN_EXCEPTIONS = {
    "starship_v3": (
        "The claim IS the subject of the dispute. Reproducing it would mean "
        "assuming the answer to chapter 7."
    ),
    "starship_v4": "Announced, never flown, and rests on the same contested dry mass.",
    "raptor33_raptor3": (
        "The article's own bookkeeping for this concept differs from the "
        "library's; see docs/physics-reference.md section 3.6."
    ),
    "raptor33_pessimistic": "Same as raptor33_raptor3, the sensitivity case of it.",
}


@pytest.fixture(scope="module")
def lib():
    return load()


def _claimants(library: Library) -> set[str]:
    """Every vehicle that publishes a payload, and so owes this test an answer.

    Args:
        library: The rocket library.

    Returns:
        Vehicle keys.
    """
    return {key for key, v in library.vehicles.items() if v.payload_leo_t is not None}


def _not_evidence(library: Library) -> set[str]:
    """Vehicles the model cannot represent well enough for agreement to mean anything.

    Args:
        library: The rocket library.

    Returns:
        Vehicle keys.
    """
    return {key for key in _claimants(library) if not library.vehicle(key).payload_is_evidence}


def _must_reproduce(library: Library) -> set[str]:
    """Vehicles whose published payload this model is expected to recover.

    Args:
        library: The rocket library.

    Returns:
        Vehicle keys.
    """
    return _claimants(library) - _not_evidence(library) - set(KNOWN_EXCEPTIONS)


MUST_REPRODUCE = sorted(_must_reproduce(load()))
"""Resolved once at import so each vehicle gets its own named test."""


@pytest.mark.parametrize("key", MUST_REPRODUCE)
def test_vehicle_reproduces_its_published_payload(lib, key):
    claimed = lib.vehicle(key).payload_leo_t
    assert claimed is not None
    computed = scenario(lib, key).solve_payload(LEO_MISSION_DELTA_V)
    assert computed == pytest.approx(claimed, rel=TOLERANCE)


def test_every_vehicle_is_either_checked_or_excused(lib):
    """No vehicle may quietly avoid this test by not being mentioned."""
    accounted = _must_reproduce(lib) | _not_evidence(lib) | set(KNOWN_EXCEPTIONS)
    assert _claimants(lib) - accounted == set(), "unaccounted for"
    assert set(KNOWN_EXCEPTIONS) - _claimants(lib) == set(), (
        "these no longer exist or lost their payload figure"
    )


def test_no_vehicle_is_both_excused_and_unmodelled(lib):
    """An excuse and a modelling limit are different claims, not two words for one.

    A vehicle the model cannot represent needs no excuse for missing, and giving
    it one hides which of the two is actually true. Ariane 64 was carrying both.
    """
    assert set(KNOWN_EXCEPTIONS) & _not_evidence(lib) == set()


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
    """Falcon 9 has the best public data, so it should fit tighter than the rest.

    A short history, because the number moved twice and only one of those was an
    improvement at the time. It sat at 0.54 t while the model flew the fairing to
    orbit, which was worth 1.7 t of payload in the flattering direction; removing
    that error pushed it to 1.18 t and this bound had to be widened to 1.25 t to
    say so honestly.

    What the fairing had been hiding was the recovery reserve, set at the bottom
    of every range in docs/physics-reference.md section 2.7 instead of at the
    ~1.0 t/t the same section concludes. Correcting it brings the error to
    0.35 t, tighter than it has ever been, so the bound comes back to 0.5 t.

    **Tighten this when the model earns it, never widen it to make it pass.**
    """
    error = abs(
        scenario(lib, "falcon9_droneship").solve_payload(LEO_MISSION_DELTA_V)
        - (lib.vehicle("falcon9_droneship").payload_leo_t or 0)
    )
    assert error < 0.5


def test_multi_stage_vehicles_are_supported(lib):
    """Saturn V and Ariane 64 have three stages. The walk must handle any depth."""
    assert len(scenario(lib, "saturn_v").stages) == 3
    assert len(scenario(lib, "ariane_64").stages) == 3
