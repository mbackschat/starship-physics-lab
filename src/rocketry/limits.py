"""Ways in which the model does not represent a vehicle as it actually flies.

Reproducing a published payload and being honestly modelled are two different
questions, and a vehicle can pass the first while failing the second. The Space
Shuttle did exactly that: it recovered its 27.5 t to within 6 %, which is the
test that decides whether anything else here can be believed, while its boosters
and its main engines were being flown one after the other instead of together.

So the limitation is recorded on the vehicle, in the data, alongside its
provenance. Both answer "how much weight can this bear", one about a number and
one about the model that produced it, and neither substitutes for the other.

The direction matters as much as the existence, which is why every entry states
it. A parallel burn flown as a sequence always *flatters* the vehicle, so a
payload that comes out high is the expected error and not a discovery.
"""

from dataclasses import dataclass
from enum import StrEnum


class ModellingLimit(StrEnum):
    """A modelling assumption a vehicle violates."""

    PARALLEL_BURN = "parallel_burn"
    """Boosters and core fire together, and are flown here as a sequence."""

    MIXED_ENGINES = "mixed_engines"
    """A stage carries more than one engine type, and a stage may name only one."""


@dataclass(frozen=True, slots=True)
class LimitDescription:
    """What a limitation does to the numbers, in words a reader can act on.

    Attributes:
        limit: Which limitation this describes.
        label: Short name for a badge.
        explanation: What the model does instead, and why.
        direction: Which way the error goes, named explicitly so an unexpected
            result is not mistaken for a finding.
        affects_payload: Whether it distorts the analytic payload, and so
            whether reproducing a published figure counts as evidence.
        affects_ascent: Whether it distorts the flown simulation.
    """

    limit: ModellingLimit
    label: str
    explanation: str
    direction: str
    affects_payload: bool
    affects_ascent: bool


MODELLING_LIMITS: dict[ModellingLimit, LimitDescription] = {
    ModellingLimit.PARALLEL_BURN: LimitDescription(
        limit=ModellingLimit.PARALLEL_BURN,
        label="Boosters burn alongside the core",
        explanation=(
            "This vehicle fires its boosters and its core stage at the same "
            "time. The model flies them one after the other, which lets the "
            "core burn its propellant at the low mass it only really reaches "
            "once the boosters are gone."
        ),
        direction="Payload comes out too high.",
        affects_payload=True,
        affects_ascent=True,
    ),
    ModellingLimit.MIXED_ENGINES: LimitDescription(
        limit=ModellingLimit.MIXED_ENGINES,
        label="More than one engine type in a stage",
        explanation=(
            "This stage carries two kinds of engine, and a stage in this "
            "library names only one. The velocity budget still uses the stage's "
            "blended efficiency and is unaffected; the flown simulation runs "
            "every engine as if it were the named one."
        ),
        direction="Thrust and the loss split are wrong; the payload is not.",
        affects_payload=False,
        affects_ascent=True,
    ),
}


def limit_for(limit: ModellingLimit) -> LimitDescription:
    """Look up what a limitation costs.

    Args:
        limit: Which limitation.

    Returns:
        Its description.
    """
    return MODELLING_LIMITS[limit]
