"""Every rocket in the library, reduced to one row each.

The numbers that decide whether this project's model is any good were only ever
visible by writing a throwaway script: what each vehicle stages at, what it
reaches, where its velocity went. This puts them all in one place, computed
once, and hands the same rows to the app and to scripted analysis so a figure on
a page cannot disagree with a figure in a report.

Building a row runs a full ascent simulation, so build them in bulk and cache
the result rather than calling this per vehicle in a loop.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from labbook.catalog import Group
from labbook.tables import Align, Col
from labbook.units import Quantity
from rocketry.ascent import AscentSettings, simulate
from rocketry.library import Library
from rocketry.limits import limit_for
from rocketry.vehicle import LEO_MISSION_DELTA_V, analyse, scenario


@dataclass(frozen=True, slots=True)
class FleetRow:
    """One vehicle, as flown and as solved.

    Attributes:
        key: Library key, which is also what a shared link carries.
        name: Display name.
        operator: Who flies it.
        category: Flown, announced, concept or historic.
        liftoff_t: Fully fuelled stack mass, tonnes.
        payload_claimed_t: The operator's published figure, tonnes.
        payload_solved_t: What this model says it can carry, tonnes.
        payload_error: Solved minus claimed, as a fraction of claimed.
        staging_speed_ms: Speed at first separation, m/s. None if it never
            stages.
        staging_altitude_km: Height at first separation, km. None if it never
            stages.
        cutoff_speed_ms: Speed when the last engine stops, m/s.
        cutoff_altitude_km: Height when the last engine stops, km.
        climb_rate_ms: Rate of climb at cutoff, m/s. Near zero is a clean
            insertion; a large negative number means it is still falling.
        ideal_delta_v: What the engines produced, m/s.
        gravity_loss: Spent holding it up, m/s.
        drag_loss: Spent pushing air aside, m/s.
        steering_loss: Spent thrusting off the direction of travel, m/s.
        loss_fraction: Share of the engines' work that never became speed.
        max_q_kpa: Worst aerodynamic loading, kilopascals.
        max_q_time_s: When that happened, seconds after liftoff.
        first_stage_share: Fraction of the ideal velocity the first stage
            supplies.
        crashed: Whether it reached the ground before its engines stopped.
        limits: What the model cannot represent about it, or empty.
    """

    key: str
    name: str
    operator: str
    category: str
    liftoff_t: float
    payload_claimed_t: float
    payload_solved_t: float
    payload_error: float
    staging_speed_ms: float | None
    staging_altitude_km: float | None
    cutoff_speed_ms: float
    cutoff_altitude_km: float
    climb_rate_ms: float
    ideal_delta_v: float
    gravity_loss: float
    drag_loss: float
    steering_loss: float
    loss_fraction: float
    max_q_kpa: float
    max_q_time_s: float
    first_stage_share: float
    crashed: bool
    limits: str

    @property
    def haystack(self) -> str:
        """Everything :func:`matching` searches, lowercased."""
        return " ".join((self.key, self.name, self.operator, self.category)).lower()


CORE_COLUMNS: tuple[Col, ...] = (
    Col("name", "Vehicle"),
    Col("liftoff_t", "Liftoff", Quantity.MASS, digits=0),
    Col("payload_claimed_t", "Payload claimed", Quantity.MASS, digits=1),
    Col("payload_solved_t", "Payload modelled", Quantity.MASS, digits=1),
    Col("staging_speed_ms", "Stages at", Quantity.VELOCITY, digits=0),
    Col("cutoff_speed_ms", "Speed at cutoff", Quantity.VELOCITY, digits=0),
    Col("loss_fraction", "Lost to losses", Quantity.PERCENT),
)
"""The seven a reader can hold in their head at once."""

EXTRA_COLUMNS: tuple[Col, ...] = (
    Col("operator", "Operator"),
    Col("category", "Kind"),
    Col("payload_error", "Model vs claim", Quantity.PERCENT),
    Col("staging_altitude_km", "Staging height", Quantity.DISTANCE, digits=0),
    Col("cutoff_altitude_km", "Cutoff height", Quantity.DISTANCE, digits=0),
    Col("climb_rate_ms", "Climbing at cutoff", Quantity.VELOCITY, digits=0),
    Col("ideal_delta_v", "Engines produced", Quantity.VELOCITY, digits=0),
    Col("gravity_loss", "Gravity took", Quantity.VELOCITY, digits=0),
    Col("drag_loss", "Air took", Quantity.VELOCITY, digits=0),
    Col("steering_loss", "Steering took", Quantity.VELOCITY, digits=0),
    Col("first_stage_share", "First stage's share", Quantity.PERCENT),
    Col("max_q_kpa", "Max q (kPa)", digits=0, align=Align.RIGHT),
    Col("max_q_time_s", "Max q at (s)", digits=0, align=Align.RIGHT),
    Col("limits", "Modelled as it flies?"),
)
"""The rest, behind a toggle. Nothing here is less true, only less central."""


def fleet(library: Library, settings: AscentSettings | None = None) -> list[FleetRow]:
    """Build a row for every vehicle that publishes a payload.

    A vehicle without a published payload has nothing to be checked against and
    is left out, which is the same rule the calibration test uses.

    Args:
        library: The rocket library.
        settings: How to fly them. Defaults to a competently flown ascent.

    Returns:
        One row per vehicle, in library order.
    """
    config = settings or AscentSettings()
    return [
        _row(library, key, config)
        for key, vehicle in library.vehicles.items()
        if vehicle.payload_leo_t is not None
    ]


def in_groups(rows: Sequence[FleetRow], groups: Sequence[Group]) -> list[FleetRow]:
    """Keep only the rows belonging to a selection of groups.

    The groups are the ones :func:`labbook.catalog.browse` already builds for
    the vehicle picker, rather than a second set invented here, so a rocket
    cannot be filed under one heading in the picker and another in this table.

    Composes with :func:`matching`, and preserves row order rather than group
    order: a reader ticking two groups expects the table to keep the order it
    already had, not to be resorted underneath them.

    Args:
        rows: Rows to filter.
        groups: Groups to keep. Empty keeps everything, which is what a picker
            with nothing ticked should mean.

    Returns:
        The matching rows, in the order given.
    """
    if not groups:
        return list(rows)
    wanted = {key for group in groups for key in group.keys}
    return [row for row in rows if row.key in wanted]


def matching(rows: Sequence[FleetRow], query: str) -> list[FleetRow]:
    """Filter rows by a free-text query.

    Matches name, operator, category and key, so pasting a key out of a shared
    link finds exactly one row.

    Args:
        rows: Rows to filter.
        query: What the reader typed. Empty keeps everything.

    Returns:
        The matching rows, in the order given.
    """
    needle = query.strip().lower()
    if not needle:
        return list(rows)
    return [row for row in rows if needle in row.haystack]


def _row(library: Library, key: str, settings: AscentSettings) -> FleetRow:
    """Compute one vehicle's row.

    Args:
        library: The rocket library.
        key: Vehicle key.
        settings: How to fly it.

    Returns:
        The row.
    """
    vehicle = library.vehicle(key)
    claimed = vehicle.payload_leo_t or 0.0
    analysis = analyse(library, key)
    solved = scenario(library, key).solve_payload(LEO_MISSION_DELTA_V)
    flight = simulate(analysis, settings)
    separation = flight.events[0] if flight.events else None
    peak = max(flight.samples, key=lambda sample: sample.dynamic_pressure_pa)

    return FleetRow(
        key=key,
        name=vehicle.name,
        operator=vehicle.operator,
        category=vehicle.category.value,
        liftoff_t=analysis.liftoff_mass_t,
        payload_claimed_t=claimed,
        payload_solved_t=solved,
        payload_error=(solved - claimed) / claimed if claimed else 0.0,
        staging_speed_ms=separation.speed_ms if separation else None,
        staging_altitude_km=separation.altitude_m / 1000.0 if separation else None,
        cutoff_speed_ms=flight.final_speed,
        cutoff_altitude_km=flight.final_altitude_m / 1000.0,
        climb_rate_ms=flight.samples[-1].vertical_speed_ms,
        ideal_delta_v=flight.ideal_delta_v,
        gravity_loss=flight.gravity_loss,
        drag_loss=flight.drag_loss,
        steering_loss=flight.steering_loss,
        loss_fraction=flight.loss_fraction,
        max_q_kpa=peak.dynamic_pressure_pa / 1000.0,
        max_q_time_s=peak.time_s,
        first_stage_share=analysis.first_stage_share,
        crashed=flight.crashed,
        limits="; ".join(limit_for(x).label for x in vehicle.modelling_limits),
    )
