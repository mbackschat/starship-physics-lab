"""Landing page: what this is, and where to start.

Run with: uv run streamlit run app/Home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components.shell import (
    SLOGAN,
    TITLE,
    chapter_card,
    chapter_link,
    chapter_pages,
    library,
    mode,
    sidebar,
)

from labbook.logo import mark
from labbook.navigation import REPOSITORY_URL, applications, foundations
from labbook.sharing import CHAPTER_PARAM, carry, route_for
from labbook.units import Quantity

st.set_page_config(page_title=TITLE, page_icon="🚀", layout="wide")

# Streamlit writes a chapter's own path into the address bar as the reader
# moves, but a static host has no route back for it, so reloading, bookmarking
# or sharing a chapter all arrive here instead. The bootstrap page leaves that
# chapter in the query string, since the path itself never reaches Python.
# Forward to it, carrying the reader's settings by hand because switching page
# throws the query string away.
_chapter = route_for(st.query_params.get(CHAPTER_PARAM, ""), chapter_pages())
if _chapter:
    carry(st.session_state, dict(st.query_params))
    st.switch_page(_chapter)

formatter = sidebar()
lib = library()

badge, headline = st.columns([1, 6], gap="medium", vertical_alignment="center")
with badge:
    st.markdown(mark(mode=mode(), height=132, uid="hero"), unsafe_allow_html=True)
with headline:
    st.title(TITLE)
    st.markdown(f"##### {SLOGAN}")

st.markdown(
    """
Rocketry has a reputation for being impenetrable. It mostly is not. Almost
everything that matters follows from one equation written down in 1903, and from
one uncomfortable fact: **the propellant you need grows exponentially with the
speed you want.**

This is not a lecture with sliders bolted on. Every number on every page runs
through a real physics engine. Move one and watch what it does to the rest.
"""
)

left, middle, right, source = st.columns(4, vertical_alignment="center")
left.metric("Rockets to explore", len(lib.vehicles))
middle.metric("Engines", len(lib.engines))
right.metric("Flights on record", sum(1 for flight in lib.flights if flight.has_flown))
with source:
    st.link_button(
        "Source on GitHub",
        REPOSITORY_URL,
        icon=":material/code:",
        width="stretch",
    )
    st.caption("Physics core, tests and data. All of it.")

st.divider()
st.subheader("The tour")
st.caption(
    f"{len(chapter_pages())} chapters, in order. Each answers one question and "
    "takes a few minutes. Click any of them."
)

# The chapters themselves live in labbook.navigation, so this list cannot drift
# away from the pages on disk. A test holds the two together.
first, second = st.columns(2, gap="large")

with first:
    st.caption("**The physics.** Start here and read in order.")
    for entry in foundations():
        chapter_card(entry)

with second:
    st.caption("**Applied to Starship.** The case study, and your turn.")
    for entry in applications():
        chapter_card(entry)

st.divider()
st.subheader("A worked example runs through all of it")
st.markdown(
    f"""
In August 2026 a German article argued that SpaceX's Starship carries far less
payload than claimed. Its physics turned out to be sound: of the numbers checked
in chapter 10, almost all reproduce independently.

But the argument rests on one number nobody outside SpaceX knows: **how much the
ship itself weighs**. The rocket equation fixes roughly
{formatter.format(296.0, Quantity.MASS)} arriving in orbit no matter what.
Whether {formatter.format(38.0, Quantity.MASS)} or
{formatter.format(100.0, Quantity.MASS)} of that is cargo depends only on how
heavy the ship is.

So this app does not tell you the answer. It hands you the slider.
"""
)

start, verify = st.columns(2)
with start:
    chapter_link(7)
with verify:
    chapter_link(10)

st.caption(
    "Every number in the library carries its provenance: published, estimated or "
    "contested. Nothing contested is ever shown as if somebody had measured it. "
    "Units switch between metric and US customary in the sidebar."
)
