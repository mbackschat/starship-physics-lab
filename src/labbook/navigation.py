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


@dataclass(frozen=True, slots=True)
class Chapter:
    """One chapter of the tour.

    Attributes:
        number: Its position, which is also the numeric prefix of its file.
        slug: The rest of the file name, and the last segment of its URL.
        title: Chapter title, without its number.
        question: The one question it answers, for the landing page.
        tag: Optional short label marking a chapter out as special.
    """

    number: int
    slug: str
    title: str
    question: str
    tag: str = ""

    @property
    def page_file(self) -> str:
        """Path to this chapter, as Streamlit refers to pages.

        Returns:
            A path relative to the entrypoint, such as ``pages/4_Stages.py``.
        """
        return f"pages/{self.number}_{self.slug}.py"

    @property
    def nav_label(self) -> str:
        """What Streamlit calls this page in its own navigation.

        Streamlit builds the sidebar link text from the *file name*, not from
        anything the page says about itself, so this is the slug with its
        underscores opened out: ``8_Bigger_is_better.py`` becomes ``8 Bigger is
        better``. Anything driving the app from outside, such as the browser
        acceptance check, has to find links by this rather than by `title`.

        Returns:
            For example ``Bigger is better``.
        """
        return self.slug.replace("_", " ")

    @property
    def label(self) -> str:
        """Numbered title, the way chapters are named on screen.

        Returns:
            For example ``4 · Stages``.
        """
        return f"{self.number} · {self.title}"


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        1, "Rocket_equation", "The rocket equation",
        "Why is going fast so expensive?", "Start here",
    ),
    Chapter(
        2, "Anatomy", "Anatomy",
        "What is a rocket made of, and how little of it is cargo?",
    ),
    Chapter(3, "Launch", "Launch", "Where does all the velocity actually go?"),
    Chapter(
        4, "Stages", "Stages",
        "Why throw half the rocket away, and where?", "The big one",
    ),
    Chapter(5, "Reuse", "Reuse", "What does it cost to get the booster back?"),
    Chapter(
        6, "Weighing_Starship", "Weighing Starship",
        "How do you weigh a rocket you have never touched?",
    ),
    Chapter(
        7, "The_payload_question", "The payload question",
        "100 tonnes, or 38?", "The point of it all",
    ),
    Chapter(
        8, "Bigger_is_better", "Bigger is better?",
        "Starship V4 grows the ship. Does that help?",
    ),
    Chapter(9, "Build_your_own", "Build your own", "Now you try."),
    Chapter(10, "Fact_check", "Fact check", "Was the article this came from right?"),
    Chapter(11, "Glossary", "Glossary", "What did that word mean?"),
    Chapter(12, "Fleet", "Fleet data", "How does every rocket here actually compare?"),
)

FOUNDATIONS = 5
"""Chapters 1 to 5 are the physics. Everything after them applies it.

The only thing a newcomer needs to know about the ordering.
"""

REPOSITORY_URL = "https://github.com/mbackschat/starship-physics-lab"
"""Where the source lives. Shown on every page, because the working is the point."""


def chapter(number: int) -> Chapter:
    """Look up a chapter by its number.

    Args:
        number: Chapter number, 1 to 11.

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


def foundations() -> tuple[Chapter, ...]:
    """The chapters that teach the mechanics.

    Returns:
        Chapters 1 to 5.
    """
    return CHAPTERS[:FOUNDATIONS]


def applications() -> tuple[Chapter, ...]:
    """The chapters that apply the mechanics to Starship.

    Returns:
        Chapter 6 onwards.
    """
    return CHAPTERS[FOUNDATIONS:]
