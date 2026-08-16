"""Recording an observation must be a data change, never a code change.

CLAUDE.md promises this and `data/flights.yaml` is written on the strength of
it: a flight that has not happened sits there as a row of nulls, waiting. The
promise has never been tested, because no flight has happened since the file was
written.

So it is tested here against the row that is actually waiting. Flight 14 is the
first orbital attempt and will produce the first real measurement of what
Starship delivers, which is the number the whole case study turns on. Finding
out on the day that it needs a schema change would be finding out too late.
"""

import shutil
from pathlib import Path

import pytest
import yaml

from rocketry.library import load
from rocketry.vehicle import analyse

ROOT = Path(__file__).resolve().parents[1]

OBSERVED = {
    "date": "2026-08-29",
    "date_precision": "day",
    "payload_t": 40.9,
    "payload_description": "24 operational Starlink V3 satellites",
    "reached_orbit": True,
    "trajectory": "low Earth orbit, 53 degrees",
    "max_velocity_kmh": 27400.0,
    "booster_outcome": "Returned to the launch site and was caught by the tower.",
    "ship_outcome": "Deployed its payload, deorbited and was caught by the tower.",
    "provenance": "published",
    "source": "Placeholder for the test. Not a prediction and not a claim.",
}
"""A plausible flown Flight 14, invented purely to exercise the schema.

Deliberately unremarkable. The point is that the fields fit, not that these are
the numbers; the real prediction is pre-registered in
studies/flight-14-prediction/ and this must never be mistaken for it.
"""


@pytest.fixture
def flown(tmp_path: Path):
    """A copy of the library with Flight 14 filled in as though it had flown."""
    data = tmp_path / "data"
    shutil.copytree(ROOT / "data", data)

    flights_file = data / "flights.yaml"
    flights = yaml.safe_load(flights_file.read_text())
    fourteen = next(entry for entry in flights if entry["number"] == 14)
    fourteen.update(OBSERVED)
    fourteen.pop("note", None)
    flights_file.write_text(yaml.safe_dump(flights, sort_keys=False))

    load.cache_clear()
    library = load(data)
    yield library
    load.cache_clear()


def test_the_waiting_row_exists_and_is_marked_unflown():
    # If this ever fails, the row was filled in for real and this whole file
    # should be replaced by a study comparing predicted against observed.
    flight = load().flight(14)
    assert not flight.has_flown, "Flight 14 has flown; retire this test and write the study"
    assert flight.payload_t is None


def test_a_flown_flight_needs_only_the_yaml(flown):
    flight = flown.flight(14)
    assert flight.has_flown
    assert flight.payload_t == pytest.approx(40.9)
    assert flight.reached_orbit is True
    assert flight.date is not None


def test_the_rest_of_the_library_still_loads_around_it(flown):
    # A new observation must not disturb anything else. The cross-reference
    # check runs at load time, so reaching this line already proves a lot.
    assert len(flown.vehicles) >= 10
    assert flown.flight(13).has_flown
    result = analyse(flown, "starship_v3")
    assert result.total_delta_v > 0


def test_the_flight_record_stays_in_order(flown):
    numbers = [flight.number for flight in flown.flights]
    assert numbers == sorted(numbers)


def test_an_observation_naming_an_unknown_vehicle_is_rejected(tmp_path: Path):
    """The guard that makes the promise safe rather than merely convenient."""
    data = tmp_path / "data"
    shutil.copytree(ROOT / "data", data)
    flights_file = data / "flights.yaml"
    flights = yaml.safe_load(flights_file.read_text())
    next(entry for entry in flights if entry["number"] == 14)["vehicle"] = "starship_v9"
    flights_file.write_text(yaml.safe_dump(flights, sort_keys=False))

    load.cache_clear()
    with pytest.raises(ValueError, match="unknown vehicle"):
        load(data)
    load.cache_clear()
