"""Organise the rocket library for a picker, and describe how much to trust a number.

Two jobs the app needs and a report might want too:

1. Group the vehicles so a beginner meets the ones the article discusses first,
   and can tell a rocket that flew from one that only ever existed on paper.
2. Say in plain words how solid a number is, so a contested estimate is never
   presented as though someone measured it.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from rocketry.library import Library
from rocketry.models import Provenance, VehicleCategory


@dataclass(frozen=True, slots=True)
class Group:
    """A named set of vehicles in a picker.

    Attributes:
        name: Heading shown above the group.
        keys: Vehicle keys, in display order.
        hint: Optional one-line explanation of what the group is.
    """

    name: str
    keys: tuple[str, ...]
    hint: str = ""

    def label(self, library: Library, key: str) -> str:
        """Display name for one vehicle in this group.

        Args:
            library: The rocket library.
            key: Vehicle key.

        Returns:
            The vehicle's name.

        Raises:
            KeyError: If the key is not in the library.
        """
        return library.vehicle(key).name


@dataclass(frozen=True, slots=True)
class ProvenanceWording:
    """How to present a number of a given provenance.

    Attributes:
        badge: A short marker for a chip or a table cell.
        explanation: One sentence a beginner can act on.
        trustworthy: Whether the number may be stated as fact.
    """

    badge: str
    explanation: str
    trustworthy: bool


_WORDING: dict[Provenance, ProvenanceWording] = {
    Provenance.PUBLISHED: ProvenanceWording(
        badge="published",
        explanation="Stated by the people who built it, or by a primary reference.",
        trustworthy=True,
    ),
    Provenance.ESTIMATED: ProvenanceWording(
        badge="estimated",
        explanation=(
            "Worked out from evidence by somebody outside the programme. "
            "Defensible, but not authoritative."
        ),
        trustworthy=False,
    ),
    Provenance.CONTESTED: ProvenanceWording(
        badge="contested",
        explanation=(
            "Credible sources disagree, and the disagreement is large enough to "
            "change the answer. Treat this as a dial to turn, not a fact."
        ),
        trustworthy=False,
    ),
    Provenance.DERIVED: ProvenanceWording(
        badge="derived",
        explanation="Computed from other numbers in this library rather than measured.",
        trustworthy=False,
    ),
    Provenance.ANNOUNCED: ProvenanceWording(
        badge="announced",
        explanation="A stated intention for the future. Nothing has demonstrated it yet.",
        trustworthy=False,
    ),
}


def describe_provenance(provenance: Provenance) -> ProvenanceWording:
    """How to present a number of a given provenance.

    Args:
        provenance: Where the number came from.

    Returns:
        The wording to use.
    """
    return _WORDING[provenance]


def browse(library: Library) -> list[Group]:
    """Group every vehicle for a picker, article entries first.

    A beginner arriving from the article should find its rockets immediately,
    and should be able to tell at a glance which of them ever left the ground.

    Args:
        library: The rocket library.

    Returns:
        Non-empty groups, in display order. Every vehicle appears exactly once.
    """
    real = _keys(library, in_article=True, exclude=(VehicleCategory.CONCEPT,))
    concepts = _keys(library, in_article=True, only=(VehicleCategory.CONCEPT,))
    others = _keys(library, in_article=False)

    groups = [
        Group(
            name="From the article: real rockets",
            keys=real,
            hint="Vehicles the source article analyses. Flown, retired or announced.",
        ),
        Group(
            name="From the article: thought experiments",
            keys=concepts,
            hint=(
                "Rockets that never existed. Each keeps the same liftoff mass as "
                "Starship and changes only where the stages separate."
            ),
        ),
        Group(
            name="Further comparisons",
            keys=others,
            hint="Not discussed in the article, included because the data is public.",
        ),
    ]
    return [group for group in groups if group.keys]


def _keys(
    library: Library,
    *,
    in_article: bool,
    only: Sequence[VehicleCategory] = (),
    exclude: Sequence[VehicleCategory] = (),
) -> tuple[str, ...]:
    """Vehicle keys matching a filter, in library order.

    Args:
        library: The rocket library.
        in_article: Whether to take entries the article discusses.
        only: If given, keep only these categories.
        exclude: Drop these categories.

    Returns:
        Matching keys.
    """
    return tuple(
        key
        for key, vehicle in library.vehicles.items()
        if vehicle.in_article is in_article
        and (not only or vehicle.category in only)
        and vehicle.category not in exclude
    )
