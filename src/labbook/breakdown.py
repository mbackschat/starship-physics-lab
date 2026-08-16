"""Split a vehicle into the four things it is made of, ready to chart.

Small enough to look trivial, which is exactly why it lives here with tests
rather than inline in a page: the payload has to be attached to the one stage
that actually carries it to orbit, and getting that wrong makes the chart say
the opposite of what it means.
"""

from dataclasses import dataclass

from labbook.palette import Series
from rocketry.models import Stage
from rocketry.vehicle import VehicleAnalysis


@dataclass(frozen=True, slots=True)
class MassRow:
    """One stage's mass, split by what the mass is for.

    Attributes:
        stage: The stage.
        label: Display name.
        propellant: Propellant spent accelerating the payload, tonnes.
        structure: Stage dry mass, tonnes.
        recovery: Propellant held back to come home, tonnes.
        payload: Useful cargo, tonnes. Non-zero only for the stage that reaches
            the target.
    """

    stage: Stage
    label: str
    propellant: float
    structure: float
    recovery: float
    payload: float
    fairing: float = 0.0
    """Payload fairing, tonnes. Counted as structure; non-zero only on the row
    that carries the payload. Small, and exactly the kind of thing that goes
    missing without anyone noticing."""

    @property
    def total(self) -> float:
        """Everything in this row, tonnes."""
        return self.propellant + self.structure + self.recovery + self.payload + self.fairing


def mass_components(analysis: VehicleAnalysis) -> list[MassRow]:
    """Break a vehicle down for a stacked chart, top stage first.

    Rows come out in the order a horizontal chart should read them: the last
    stage to fire at the top, the one that leaves the pad at the bottom.

    Args:
        analysis: A vehicle already run through :func:`rocketry.vehicle.analyse`.

    Returns:
        One row per stage, top-down. The sum of every row's total is the
        vehicle's liftoff mass.
    """
    top_down = list(reversed(analysis.stages))
    carrier = top_down[0].stage.key if top_down else ""
    return [
        MassRow(
            stage=result.stage,
            label=result.stage.name,
            propellant=result.ascent_propellant_t,
            structure=result.stage.dry_mass_t,
            recovery=result.recovery_reserve_t + result.stage.residual_propellant_t,
            payload=analysis.payload_t if result.stage.key == carrier else 0.0,
            fairing=analysis.fairing_t if result.stage.key == carrier else 0.0,
        )
        for result in top_down
    ]


def as_series(rows: list[MassRow]) -> dict[Series, list[float]]:
    """Arrange rows for :func:`labbook.charts.mass_breakdown`.

    Stacking order reads left to right as the rocket burns: propellant first,
    then what is left over, with the payload last so it reads as the remainder.

    Args:
        rows: Output of :func:`mass_components`.

    Returns:
        Series to per-row values, in stacking order.
    """
    return {
        Series.PROPELLANT: [row.propellant for row in rows],
        Series.STRUCTURE: [row.structure + row.fairing for row in rows],
        Series.RECOVERY: [row.recovery for row in rows],
        Series.PAYLOAD: [row.payload for row in rows],
    }
