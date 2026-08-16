"""Landing page: what this is, and where to start.

Run with: uv run streamlit run app/Home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components.shell import library, sidebar

from labbook.units import Quantity

formatter = sidebar()
st.set_page_config(page_title="Starship Physics Lab", page_icon="🚀", layout="wide")

st.title("Starship Physics Lab")
st.markdown("##### Why rockets perform the way they do, worked out by moving the numbers yourself.")

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

lib = library()
left, middle, right = st.columns(3)
left.metric("Rockets to explore", len(lib.vehicles))
middle.metric("Engines", len(lib.engines))
right.metric("Flights on record", sum(1 for flight in lib.flights if flight.has_flown))

st.divider()

st.subheader("Start here")
st.markdown(
    """
| Chapter | The question it answers |
|---|---|
| **1 · The rocket equation** | Why is going fast so expensive? |
| **2 · Anatomy of a rocket** | What is a rocket actually made of, and how little of it is cargo? |

More chapters are being built: the launch simulator, the staging split, what
reuse costs, and the Starship payload question.
"""
)

st.divider()

st.subheader("A worked example runs through all of it")
st.markdown(
    f"""
In August 2026 a German article argued that SpaceX's Starship carries far less
payload than claimed. Its physics turned out to be sound: of 64 checkable
numbers, 61 reproduce independently within 2 %.

But the argument rests on one number nobody outside SpaceX knows: **how much the
ship itself weighs**. The rocket equation fixes roughly
{formatter.format(300.0, Quantity.MASS)} arriving in orbit no matter what. Whether
{formatter.format(40.0, Quantity.MASS)} or {formatter.format(100.0, Quantity.MASS)}
of that is cargo depends only on how heavy the ship is.

So this app does not tell you the answer. It hands you the slider.
"""
)

st.caption(
    "Every number in the library carries its provenance: published, estimated or "
    "contested. Nothing contested is ever shown as if somebody had measured it."
)
