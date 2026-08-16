"""The rocket library: named presets so nothing has to be retyped.

This is the entry point for scripted analysis. A one-off question should start
like this and not with a wall of magic numbers::

    from rocketry.library import load

    lib = load()
    ship = lib.stage("starship_v3")
    print(ship.dry_mass_fraction)

Data lives in editable YAML under ``data/``. Adding a rocket is a data change,
never a code change.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from rocketry.models import Engine, Flight, Stage, Vehicle


def _find_data_dir() -> Path:
    """Locate the YAML library by searching upward from this module.

    The repository has it at ``<root>/data``, but a WebAssembly build mounts the
    packages at a different root, so a fixed number of parent hops is fragile.
    Searching for the directory that actually contains the data works in both.

    Returns:
        The data directory.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "data"
        if (candidate / "engines.yaml").is_file():
            return candidate
    return here.parents[2] / "data"


DATA_DIR = _find_data_dir()


class Library:
    """Every engine, stage, vehicle and flight, validated and cross-checked.

    Attributes:
        engines: Engines by key.
        stages: Stages by key.
        vehicles: Vehicles by key.
        flights: Flights in ascending flight number.
    """

    def __init__(
        self,
        engines: dict[str, Engine],
        stages: dict[str, Stage],
        vehicles: dict[str, Vehicle],
        flights: list[Flight],
    ) -> None:
        """Build a library from already-validated entries.

        Args:
            engines: Engines by key.
            stages: Stages by key.
            vehicles: Vehicles by key.
            flights: Flights, any order.
        """
        self.engines = engines
        self.stages = stages
        self.vehicles = vehicles
        self.flights = sorted(flights, key=lambda flight: flight.number)
        self._check_references()

    def engine(self, key: str) -> Engine:
        """Look up an engine.

        Args:
            key: Engine key, for example ``raptor_3``.

        Returns:
            The engine.

        Raises:
            KeyError: If no such engine exists, listing what does.
        """
        return _get(self.engines, key, "engine")

    def stage(self, key: str) -> Stage:
        """Look up a stage.

        Args:
            key: Stage key, for example ``starship_v3``.

        Returns:
            The stage.

        Raises:
            KeyError: If no such stage exists, listing what does.
        """
        return _get(self.stages, key, "stage")

    def vehicle(self, key: str) -> Vehicle:
        """Look up a vehicle.

        Args:
            key: Vehicle key, for example ``falcon9_droneship``.

        Returns:
            The vehicle.

        Raises:
            KeyError: If no such vehicle exists, listing what does.
        """
        return _get(self.vehicles, key, "vehicle")

    def flight(self, number: int) -> Flight:
        """Look up a flight by its number.

        Args:
            number: Flight number.

        Returns:
            The flight.

        Raises:
            KeyError: If no such flight is recorded.
        """
        for candidate in self.flights:
            if candidate.number == number:
                return candidate
        known = ", ".join(str(f.number) for f in self.flights)
        raise KeyError(f"no flight {number}. Recorded flights: {known}")

    def stages_of(self, vehicle_key: str) -> list[Stage]:
        """Resolve a vehicle's stages, bottom-up.

        Args:
            vehicle_key: Vehicle key.

        Returns:
            Stages in launch order, first stage first.
        """
        return [self.stage(key) for key in self.vehicle(vehicle_key).stages]

    def engine_of(self, stage_key: str) -> Engine:
        """Resolve the engine a stage uses.

        Args:
            stage_key: Stage key.

        Returns:
            The engine.
        """
        return self.engine(self.stage(stage_key).engine)

    def _check_references(self) -> None:
        """Fail loudly at load time if the data files disagree with each other.

        Raises:
            ValueError: If a stage names an unknown engine or a vehicle names an
                unknown stage.
        """
        problems: list[str] = []
        for key, stage in self.stages.items():
            if stage.engine not in self.engines:
                problems.append(f"stage {key!r} names unknown engine {stage.engine!r}")
        for key, vehicle in self.vehicles.items():
            for stage_key in vehicle.stages:
                if stage_key not in self.stages:
                    problems.append(f"vehicle {key!r} names unknown stage {stage_key!r}")
        for flight in self.flights:
            if flight.vehicle not in self.vehicles:
                problems.append(f"flight {flight.number} names unknown vehicle {flight.vehicle!r}")
        if problems:
            raise ValueError("rocket library is inconsistent:\n  " + "\n  ".join(problems))


@lru_cache(maxsize=1)
def load(data_dir: Path | None = None) -> Library:
    """Load and validate the rocket library.

    Cached, so calling it repeatedly in a script or a Streamlit rerun is free.

    Args:
        data_dir: Directory holding the YAML files. Defaults to the repository's
            ``data/``.

    Returns:
        The library.
    """
    root = data_dir or DATA_DIR
    engines = {
        key: Engine(key=key, **body) for key, body in _read_mapping(root / "engines.yaml").items()
    }
    stages = {
        key: Stage(key=key, **body) for key, body in _read_mapping(root / "stages.yaml").items()
    }
    vehicles = {
        key: Vehicle(key=key, **body) for key, body in _read_mapping(root / "vehicles.yaml").items()
    }
    flights = [Flight(**body) for body in _read_sequence(root / "flights.yaml")]
    return Library(engines, stages, vehicles, flights)


def _read_mapping(path: Path) -> dict[str, dict[str, Any]]:
    """Read a YAML file expected to hold a mapping of keys to entries.

    Args:
        path: File to read.

    Returns:
        The parsed mapping.

    Raises:
        ValueError: If the file does not contain a mapping.
    """
    loaded = yaml.safe_load(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} should contain a mapping, got {type(loaded).__name__}")
    return loaded


def _read_sequence(path: Path) -> list[dict[str, Any]]:
    """Read a YAML file expected to hold a list of entries.

    Args:
        path: File to read.

    Returns:
        The parsed list.

    Raises:
        ValueError: If the file does not contain a list.
    """
    loaded = yaml.safe_load(path.read_text())
    if not isinstance(loaded, list):
        raise ValueError(f"{path} should contain a list, got {type(loaded).__name__}")
    return loaded


def _get[T](entries: dict[str, T], key: str, kind: str) -> T:
    """Look up a key, failing with a useful message rather than a bare KeyError.

    Args:
        entries: Mapping to search.
        key: Key to find.
        kind: Human-readable name of the entry type, for the error message.

    Returns:
        The entry.

    Raises:
        KeyError: If the key is absent, listing the available keys.
    """
    try:
        return entries[key]
    except KeyError:
        available = ", ".join(sorted(entries))
        raise KeyError(f"no {kind} {key!r}. Available: {available}") from None
