"""Landing page: what this is, and where to start.

Run with: uv run streamlit run app/Home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components.shell import SLOGAN, TITLE, chapter_pages, library, sidebar

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

left, middle, right = st.columns(3)
left.metric("Rockets to explore", len(lib.vehicles))
middle.metric("Engines", len(lib.engines))
right.metric("Flights on record", sum(1 for flight in lib.flights if flight.has_flown))

st.divider()
st.subheader("The tour")
st.caption("Eleven chapters, in order. Each answers one question and takes a few minutes.")

# The first five are the physics; the rest apply it. That split is the only
# thing a newcomer needs to know about the ordering.
FOUNDATIONS = 5

CHAPTERS = [
    ("1 · The rocket equation", "Why is going fast so expensive?", "Start here"),
    ("2 · Anatomy", "What is a rocket made of, and how little of it is cargo?", ""),
    ("3 · Launch", "Where does all the velocity actually go?", ""),
    ("4 · Stages", "Why throw half the rocket away, and where?", "The big one"),
    ("5 · Reuse", "What does it cost to get the booster back?", ""),
    ("6 · Weighing Starship", "How do you weigh a rocket you have never touched?", ""),
    ("7 · The payload question", "100 tonnes, or 38?", "The point of it all"),
    ("8 · Bigger is better?", "Starship V4 grows the ship. Does that help?", ""),
    ("9 · Build your own", "Now you try.", ""),
    ("10 · Fact check", "Was the article this came from right?", ""),
    ("11 · Glossary", "What did that word mean?", ""),
]

first, second = st.columns(2, gap="large")
for index, (title, question, tag) in enumerate(CHAPTERS):
    column = first if index < 6 else second
    with column, st.container(border=True):
        heading = f"**{title}**"
        if tag:
            heading += f" · :grey[{tag}]"
        st.markdown(heading)
        st.caption(question)
    if index == FOUNDATIONS - 1:
        first.caption("Those five are the physics. Everything after applies it.")

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

st.caption(
    "Every number in the library carries its provenance: published, estimated or "
    "contested. Nothing contested is ever shown as if somebody had measured it. "
    "Units switch between metric and US customary in the sidebar."
)
