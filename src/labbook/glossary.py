"""Plain-language definitions for every word the app uses without warning.

Two rules, both enforced by tests. A definition never uses the word it is
defining, and it never assumes another entry has already been read. A reader who
lands on "gravity loss" from chapter 3 has not necessarily met "delta-v" yet.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Term:
    """One entry in the glossary.

    Attributes:
        word: The term itself.
        plain: A definition a beginner can read cold, in one or two sentences.
        detail: Optional extra for a reader who wants more.
        related: Other terms worth reading next.
    """

    word: str
    plain: str
    detail: str = ""
    related: tuple[str, ...] = field(default_factory=tuple)


TERMS: tuple[Term, ...] = (
    Term(
        word="Delta-v",
        plain=(
            "The total change in speed a rocket can produce, measured in metres "
            "per second. Think of it as the fuel gauge for space travel: not how "
            "far you can go, but how much you can change where you are going."
        ),
        detail=(
            "Reaching low Earth orbit costs roughly 9,400 m/s once gravity and "
            "air have taken their share. Every manoeuvre after that has a price "
            "in the same currency."
        ),
        related=("Mass ratio", "Rocket equation", "Gravity loss"),
    ),
    Term(
        word="Dry mass",
        plain=(
            "What a rocket stage weighs with empty tanks: metal, engines, "
            "plumbing and anything bolted to it. Everything that has to be "
            "carried but does not get burnt."
        ),
        detail=(
            "It is the number that decides how much cargo is left over, and the "
            "one SpaceX has not published for Starship since 2019."
        ),
        related=("Payload", "Payload fraction", "Staging"),
    ),
    Term(
        word="Gravity loss",
        plain=(
            "The speed a rocket never gets because it spent the effort holding "
            "itself up instead. Every second spent climbing, the Earth takes "
            "about 9.8 m/s back."
        ),
        detail=(
            "Typically 1,000 to 1,800 m/s on a launch, which is far more than "
            "air resistance costs. It is why rockets tip over so early: going "
            "straight up is expensive and altitude is not the goal."
        ),
        related=("Delta-v", "Thrust-to-weight ratio"),
    ),
    Term(
        word="Isp",
        plain=(
            "Short for specific impulse. See that entry; the two words mean the "
            "same thing and both get used."
        ),
        related=("Specific impulse",),
    ),
    Term(
        word="Mass ratio",
        plain=(
            "How much heavier a rocket is when full than when empty. A vehicle "
            "that weighs 10 tonnes empty and 40 tonnes fuelled has a ratio of 4."
        ),
        detail=(
            "It is the number the rocket equation actually cares about. Speed "
            "goes up with its logarithm, which is a polite way of saying that "
            "going faster gets expensive very quickly."
        ),
        related=("Rocket equation", "Delta-v", "Dry mass"),
    ),
    Term(
        word="Max q",
        plain=(
            "The moment of hardest aerodynamic pounding during a launch, when "
            "speed and air thickness together are at their worst. Usually about "
            "a minute in, around 10 to 15 km up."
        ),
        detail="Roughly 30 to 35 kPa for most launchers, and often the point of throttle-down.",
        related=("Gravity loss",),
    ),
    Term(
        word="Payload",
        plain=(
            "The useful cargo: satellites, a spacecraft, people. The only part "
            "of the whole machine that the launch actually exists to deliver."
        ),
        related=("Payload fraction", "Dry mass"),
    ),
    Term(
        word="Payload fraction",
        plain=(
            "How much of what left the launch pad turned out to be useful cargo, "
            "as a percentage. Under 1 % is normal, and around 4 % is exceptional."
        ),
        detail=(
            "The fairest single measure of a launch vehicle, because it compares "
            "what you got against everything it took to get it."
        ),
        related=("Payload", "Staging"),
    ),
    Term(
        word="Propellant",
        plain=(
            "What the engines burn and throw out of the back, both the fuel and "
            "the oxidiser it is burnt with. Rockets carry both, because there is "
            "no air in space to supply the second."
        ),
        detail="It is usually 85 to 95 % of everything on the launch pad.",
        related=("Specific impulse", "Mass ratio"),
    ),
    Term(
        word="Rocket equation",
        plain=(
            "The formula, written down in 1903, that ties how fast a vehicle can "
            "go to how much of it was propellant and how good its engines are. "
            "Almost everything in launch vehicle design follows from it."
        ),
        detail="Written out: the speed change equals exhaust velocity times ln(mass ratio).",
        related=("Mass ratio", "Delta-v", "Specific impulse"),
    ),
    Term(
        word="Specific impulse",
        plain=(
            "How efficient an engine is, quoted in seconds. Higher means less is "
            "burnt for the same push. A kerosene engine manages about 300, "
            "hydrogen about 450."
        ),
        detail=(
            "The seconds are real: an engine rated at 350 could hold up one tonne "
            "for 350 seconds while burning one tonne. It is quoted in seconds "
            "because the number is then the same in every unit system, which is "
            "why this app never converts it."
        ),
        related=("Propellant", "Rocket equation", "Isp"),
    ),
    Term(
        word="Stage",
        plain=(
            "One self-contained section of a rocket, with its own tanks and "
            "engines, thrown away once it is empty."
        ),
        related=("Staging", "Dry mass"),
    ),
    Term(
        word="Staging",
        plain=(
            "Throwing away the part of the rocket you have finished with, so the "
            "rest no longer has to carry empty tanks. It is a crude trick and it "
            "is the only reason orbit is reachable at all."
        ),
        detail=(
            "Where the split happens matters enormously: on the same vehicle it "
            "can be worth a factor of two in cargo."
        ),
        related=("Stage", "Mass ratio", "Payload fraction"),
    ),
    Term(
        word="Thrust-to-weight ratio",
        plain=(
            "How hard the engines push compared with how heavy the vehicle is. "
            "Below 1 it cannot leave the ground. At exactly 1 it hovers, burning "
            "propellant and going nowhere."
        ),
        detail=(
            "Launchers typically lift off at about 1.4, meaning roughly 70 % of "
            "the push is spent simply not falling."
        ),
        related=("Gravity loss",),
    ),
)


def define(word: str) -> Term | None:
    """Look up a term, forgiving about case and spacing.

    Args:
        word: The term to find.

    Returns:
        The entry, or None if the glossary does not cover it.
    """
    wanted = word.strip().lower()
    for term in TERMS:
        if term.word.lower() == wanted:
            return term
    return None


def search(text: str) -> list[Term]:
    """Find every term whose name or definition mentions some text.

    Args:
        text: What to look for.

    Returns:
        Matching entries, in glossary order. Empty if nothing matches.
    """
    wanted = text.strip().lower()
    if not wanted:
        return list(TERMS)
    return [
        term
        for term in TERMS
        if wanted in term.word.lower()
        or wanted in term.plain.lower()
        or wanted in term.detail.lower()
    ]
