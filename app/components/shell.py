"""Page furniture shared by every chapter: the sidebar, badges, formula blocks.

Streamlit glue only. Anything with logic in it belongs in :mod:`labbook` so it
can be tested without a browser.
"""

from collections.abc import Sequence

import streamlit as st

from labbook.catalog import Group, browse, describe_provenance
from labbook.formula import Formula
from labbook.logo import mark
from labbook.navigation import CHAPTERS, REPOSITORY_URL, Chapter, chapter, page_files
from labbook.palette import Mode
from labbook.units import METRIC, US, Formatter, UnitSystem
from rocketry.library import Library, load
from rocketry.models import Provenance

TITLE = "Starship Physics Lab"
SLOGAN = "Understand Starship. Then build a better one."


def page(title: str, teaser: str, *, icon: str = "🚀") -> None:
    """Start a chapter: page config, title and the one-line promise.

    Every chapter opens by saying what the reader will learn. No preamble.

    Args:
        title: Chapter title.
        teaser: One sentence saying what this page teaches.
        icon: Browser tab icon.
    """
    st.set_page_config(page_title=f"{title} · {TITLE}", page_icon=icon, layout="wide")
    st.title(title)
    st.markdown(f"##### {teaser}")


@st.cache_resource
def library() -> Library:
    """The rocket library, loaded once per session.

    Returns:
        The library.
    """
    return load()


def sidebar() -> Formatter:
    """Draw the sidebar and return the reader's chosen unit system.

    Args:
        None.

    Returns:
        The formatter every number on the page should go through.
    """
    with st.sidebar:
        badge, wordmark = st.columns([1, 3], vertical_alignment="center")
        with badge:
            st.markdown(mark(mode=mode(), height=52, uid="side"), unsafe_allow_html=True)
        with wordmark:
            st.markdown(f"### {TITLE}")
        st.caption(SLOGAN)
        st.page_link("Home.py", label="The tour", icon=":material/home:")
        st.link_button(
            "Source on GitHub",
            REPOSITORY_URL,
            icon=":material/code:",
            width="stretch",
        )
        st.caption("Every number here is computed by code you can read.")
        st.divider()
        choice = st.radio(
            "Units",
            options=[UnitSystem.METRIC, UnitSystem.US],
            format_func=lambda system: system.label,
            key="unit_system",
            help=(
                "Changes how numbers are displayed only. The physics underneath "
                "is always metric, so switching can never change an answer."
            ),
        )
        st.caption(
            "Specific impulse stays in seconds either way. It is the same number "
            "in both systems, which is exactly why engineers quote it."
        )
        st.divider()
    return METRIC if choice is UnitSystem.METRIC else US


def chapter_pages() -> list[str]:
    """Every chapter page, as Streamlit refers to them, in chapter order.

    Delegated to :mod:`labbook.navigation`, which is the one place the tour is
    described. Globbing the directory instead would sort 10 and 11 ahead of 2,
    and would let the landing page's list drift away from the files on disk.

    Returns:
        Page paths relative to the entrypoint, in chapter order.
    """
    return page_files()


def chapter_link(number: int, *, question: bool = False) -> None:
    """A link to another chapter, for prose that refers to one.

    Chapters used to cite each other in plain text, which left the reader to
    find them by hand.

    Args:
        number: Which chapter to point at.
        question: Show the chapter's question rather than its title.
    """
    entry = chapter(number)
    st.page_link(
        entry.page_file,
        label=entry.question if question else entry.label,
        icon=":material/arrow_forward:",
    )


def chapter_footer(number: int) -> None:
    """Move the reader on, which is what makes a set of pages a tour.

    Args:
        number: The chapter currently being read.
    """
    entry = chapter(number)
    st.divider()
    back, forward = st.columns(2)
    with back:
        if entry.number > CHAPTERS[0].number:
            previous = chapter(entry.number - 1)
            st.caption("Previous")
            st.page_link(
                previous.page_file,
                label=previous.label,
                icon=":material/arrow_back:",
            )
    with forward:
        if entry.number < CHAPTERS[-1].number:
            following = chapter(entry.number + 1)
            st.caption("Next")
            st.page_link(
                following.page_file,
                label=following.label,
                icon=":material/arrow_forward:",
            )


def chapter_card(entry: Chapter) -> None:
    """One chapter on the landing page, as something the reader can click.

    Args:
        entry: The chapter to offer.
    """
    with st.container(border=True):
        st.page_link(entry.page_file, label=f"**{entry.label}**", icon=":material/play_arrow:")
        st.caption(entry.question if not entry.tag else f"{entry.question} · :grey[{entry.tag}]")


def mode() -> Mode:
    """Chart surface matching the reader's Streamlit theme.

    Returns:
        Light or dark.
    """
    base = st.get_option("theme.base")
    return Mode.DARK if base == "dark" else Mode.LIGHT


def provenance_badge(provenance: Provenance, *, inline: bool = False) -> None:
    """Show how much weight a number can bear.

    Never let a contested estimate look like a measurement. This is the whole
    reason the library tracks provenance.

    Args:
        provenance: Where the number came from.
        inline: Render as a caption rather than a full callout.
    """
    wording = describe_provenance(provenance)
    if inline:
        st.caption(f"**{wording.badge}** · {wording.explanation}")
    elif wording.trustworthy:
        st.success(f"**{wording.badge}** · {wording.explanation}", icon="✅")
    elif provenance is Provenance.CONTESTED:
        st.warning(f"**{wording.badge}** · {wording.explanation}", icon="⚠️")
    else:
        st.info(f"**{wording.badge}** · {wording.explanation}", icon="ℹ️")


def formula_block(formula: Formula, formatter: Formatter) -> None:
    """Show an equation in symbols and again with the reader's numbers in it.

    Args:
        formula: The equation.
        formatter: Unit system to display in.
    """
    st.markdown(f"**{formula.name}**")
    st.code(formula.symbolic, language=None)
    st.code(formula.substituted(formatter), language=None)
    if formula.note:
        st.caption(formula.note)


def why(question: str, answer: str) -> None:
    """A collapsed explanation for readers who want the depth.

    Progressive disclosure: the surface stays uncluttered, the reasoning is
    always one click away.

    Args:
        question: The question a curious reader would ask.
        answer: The answer, in markdown.
    """
    with st.expander(f"Why? {question}"):
        st.markdown(answer)


def try_this(suggestion: str) -> None:
    """Nudge the reader towards the interaction that teaches the point.

    Args:
        suggestion: What to try, in markdown.
    """
    st.info(f"**Try this.** {suggestion}", icon="🔬")


def vehicle_picker(
    label: str = "Rocket",
    *,
    default: str = "starship_v3",
    key: str = "vehicle",
    groups: Sequence[Group] | None = None,
) -> str:
    """Choose a vehicle, with the article's rockets offered first.

    A beginner should never face an empty form, so this always has a selection.

    Args:
        label: Widget label.
        default: Vehicle key to start on.
        key: Streamlit widget key.
        groups: Override the grouping, for pages that need a subset.

    Returns:
        The chosen vehicle key.
    """
    lib = library()
    all_groups = list(groups) if groups is not None else browse(lib)
    options: list[str] = []
    captions: dict[str, str] = {}
    for group in all_groups:
        for vehicle_key in group.keys:
            options.append(vehicle_key)
            captions[vehicle_key] = group.name

    def render(vehicle_key: str) -> str:
        vehicle = lib.vehicle(vehicle_key)
        marker = "★ " if vehicle.in_article else ""
        return f"{marker}{vehicle.name}"

    index = options.index(default) if default in options else 0
    chosen = st.selectbox(label, options, index=index, format_func=render, key=key)
    st.caption(f"{captions[chosen]} · ★ marks rockets the source article analyses")
    return chosen
