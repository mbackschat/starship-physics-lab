"""The tour: which chapters exist, what they ask, and how to link to one.

One registry, so a cross-reference cannot drift away from the page it points at.
Before this existed the landing page kept its own hard-coded list of chapters
while the shell globbed ``app/pages/`` for the real ones, and nothing held the
two together. Every reference to another chapter was therefore prose, because
there was nothing to link to.

The page file is derived from the entry rather than stored beside it, so a
renamed chapter is a one-line change here and a test catches the rename if the
file is not renamed with it.
"""

from dataclasses import dataclass
from enum import StrEnum


class Section(StrEnum):
    """Which part of the tour a chapter belongs to.

    There were two parts until a glossary and a data table joined the end, and
    the sidebar ended up captioned "Applied to Starship, and reference", which
    told a reader nothing about either. A chapter declares its own part now, so
    a new one cannot be swept into whichever group happens to run to the end.
    """

    PHYSICS = "physics"
    """Chapters 1 to 5. The mechanics, with no agenda, read in order."""

    STARSHIP = "starship"
    """The case study: applying the mechanics to the argument being checked."""

    REFERENCE = "reference"
    """Look-up material. No order, no argument, read whenever."""

    @property
    def label(self) -> str:
        """Short heading, for the sidebar."""
        match self:
            case Section.PHYSICS:
                return "The physics"
            case Section.STARSHIP:
                return "Applied to Starship"
            case Section.REFERENCE:
                return "Reference"

    @property
    def blurb(self) -> str:
        """One line saying how to read this part, for the landing page."""
        match self:
            case Section.PHYSICS:
                return "Start here and read in order."
            case Section.STARSHIP:
                return "The case study, and your turn."
            case Section.REFERENCE:
                return "Look things up, in any order."


@dataclass(frozen=True, slots=True)
class Chapter:
    """One chapter of the tour.

    Attributes:
        number: Its position, which is also the numeric prefix of its file.
        slug: The rest of the file name, and the last segment of its URL.
        title: Chapter title, without its number.
        question: The one question it answers, for the landing page.
        section: Which part of the tour it belongs to.
        tag: Optional short label marking a chapter out as special.
    """

    number: int
    slug: str
    title: str
    question: str
    section: Section
    tag: str = ""

    @property
    def page_file(self) -> str:
        """Path to this chapter, as Streamlit refers to pages.

        Returns:
            A path relative to the entrypoint, such as ``pages/4_Stages.py``.
        """
        return f"pages/{self.number}_{self.slug}.py"

    @property
    def label(self) -> str:
        """Numbered title, the way chapters are named on screen.

        This is also the text of the sidebar link, because the sidebar
        navigation is drawn by hand in `components.shell`. Anything driving the
        app from outside, such as the browser acceptance check, finds a chapter
        by this.

        Returns:
            For example ``4 · Stages``.
        """
        return f"{self.number} · {self.title}"


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        1, "Rocket_equation", "The rocket equation",
        "Why is going fast so expensive?", Section.PHYSICS, "Start here",
    ),
    Chapter(
        2, "Anatomy", "Anatomy",
        "What is a rocket made of, and how little of it is cargo?", Section.PHYSICS,
    ),
    Chapter(
        3, "Launch", "Launch",
        "Where does all the velocity actually go?", Section.PHYSICS,
    ),
    Chapter(
        4, "Stages", "Stages",
        "Why throw half the rocket away, and where?", Section.PHYSICS, "The big one",
    ),
    Chapter(
        5, "Reuse", "Reuse",
        "What does it cost to get the booster back?", Section.PHYSICS,
    ),
    Chapter(
        6, "Weighing_Starship", "Weighing Starship",
        "How do you weigh a rocket you have never touched?", Section.STARSHIP,
    ),
    Chapter(
        7, "The_payload_question", "The payload question",
        "100 tonnes, or 38?", Section.STARSHIP, "The point of it all",
    ),
    Chapter(
        8, "Bigger_is_better", "Bigger is better?",
        "Starship V4 grows the ship. Does that help?", Section.STARSHIP,
    ),
    Chapter(9, "Build_your_own", "Build your own", "Now you try.", Section.STARSHIP),
    Chapter(
        10, "Fact_check", "Fact check",
        "Was the article this came from right?", Section.STARSHIP,
    ),
    Chapter(11, "Glossary", "Glossary", "What did that word mean?", Section.REFERENCE),
    Chapter(
        12, "Fleet", "Fleet data",
        "How does every rocket here actually compare?", Section.REFERENCE,
    ),
)

REPOSITORY_URL = "https://github.com/mbackschat/starship-physics-lab"
"""Where the source lives. Shown on every page, because the working is the point."""

ARTICLE_URL = (
    "https://www.golem.de/news/spacex-wie-das-starship-den-kampf-gegen-die-physik-"
    "verliert-2608-211916.html"
)
"""The article this whole project set out to check.

Cited by link and never redistributed, which is the only way a copyrighted
source can be handled here. It is public, so a reader who wants to disagree with
the fact-check should be one click from the thing being checked. Hiding it would
undercut the point of publishing the working.
"""

ARTICLE_TITLE = "SpaceX: Wie das Starship den Kampf gegen die Physik verliert"
"""Its own title, in its own language. Golem.de, 14 August 2026."""

REFERENCE_URL = f"{REPOSITORY_URL}/blob/main/docs/physics-reference.md"
"""The claim-by-claim verification log, for a reader who wants all 64 numbers."""


def chapter(number: int) -> Chapter:
    """Look up a chapter by its number.

    Args:
        number: Chapter number.

    Returns:
        The chapter.

    Raises:
        KeyError: If there is no such chapter, listing the ones there are.
    """
    for entry in CHAPTERS:
        if entry.number == number:
            return entry
    known = ", ".join(str(entry.number) for entry in CHAPTERS)
    raise KeyError(f"no chapter {number}. The tour has: {known}")


def page_files() -> list[str]:
    """Every chapter page, in chapter order.

    Ordered by chapter number rather than by file name, which would otherwise
    sort 10 and 11 ahead of 2.

    Returns:
        Page paths relative to the entrypoint.
    """
    return [entry.page_file for entry in CHAPTERS]


def in_section(section: Section) -> tuple[Chapter, ...]:
    """Every chapter in one part of the tour, in order.

    Args:
        section: Which part.

    Returns:
        Its chapters.
    """
    return tuple(entry for entry in CHAPTERS if entry.section is section)


def sections() -> list[tuple[Section, tuple[Chapter, ...]]]:
    """The tour, grouped, in reading order.

    Both the sidebar and the landing page render from this, so a chapter cannot
    appear under one heading in one place and another elsewhere.

    Returns:
        Each section with its chapters. Empty sections are dropped, so removing
        the last reference chapter removes the heading with it.
    """
    grouped = [(section, in_section(section)) for section in Section]
    return [(section, chapters) for section, chapters in grouped if chapters]
