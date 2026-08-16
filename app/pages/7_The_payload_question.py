"""Chapter 7: does Starship carry 100 tonnes?"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import (
    chapter_footer,
    library,
    mode,
    page,
    reset_button,
    sidebar,
    try_this,
    why,
)

from labbook.casestudy import ESTIMATES, PayloadPoint, payload_curve
from labbook.charts import payload_against_dry_mass
from labbook.sharing import collect, read_number, write_state
from labbook.tables import Col, table
from labbook.units import Quantity

page(
    "7 · The payload question",
    "The rocket equation decides what arrives. You decide how much of it is cargo.",
)
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
This is the chapter the whole app was built for, and it does not have an answer.
It has a slider.
"""
)


@st.cache_data(show_spinner=False)
def curve(low: float, high: float) -> list[PayloadPoint]:
    """Payload against assumed dry mass, cached.

    Args:
        low: Lightest dry mass to try, tonnes.
        high: Heaviest dry mass to try, tonnes.

    Returns:
        The curve points.
    """
    span = [low + (high - low) * i / 60 for i in range(61)]
    return payload_curve(library(), "starship_v3", span)


points = curve(80.0, 260.0)

LOW, HIGH, DEFAULT, STEP = 80, 260, 220, 5

# Seed the control from the URL once, then let the reader own it. Passing a
# changing `value=` instead would make Streamlit treat this as a new widget
# every time the URL moved, silently throwing away what they just set.
if "dry_mass" not in st.session_state:
    shared = read_number(
        collect(st.session_state, st.query_params),
        "dry",
        default=float(DEFAULT),
        low=float(LOW),
        high=float(HIGH),
    )
    st.session_state["dry_mass"] = int(round(shared / STEP) * STEP)

chosen = st.slider(
    "How much does Starship weigh empty?",
    min_value=LOW,
    max_value=HIGH,
    step=STEP,
    format="%d t",
    key="dry_mass",
    help="Nobody outside SpaceX knows. Published views span this whole range.",
)
reset_button("dry_mass", label="Back to the article's estimate")
# Only write when it actually changed. Rewriting the URL on every run churns
# the address bar and, in Streamlit, can leave it a step behind the control.
_shared = write_state({"dry": float(chosen)})
if st.query_params.get("dry") != _shared["dry"]:
    st.query_params.update(_shared)
# Solve the reader's exact value rather than snapping to the nearest sampled
# point, or the metrics disagree with the slider they were just dragged from.
nearest = payload_curve(library(), "starship_v3", [float(chosen)])[0]

one, two, three, four = st.columns(4)
one.metric("Reaches orbit", formatter.mass(nearest.mass_in_orbit_t, digits=0))
two.metric("The ship itself", formatter.mass(nearest.dry_mass_t, digits=0))
three.metric(
    "Propellant to land", formatter.mass(nearest.analysis.stages[-1].recovery_reserve_t, digits=0)
)
four.metric("Left for cargo", formatter.mass(nearest.payload_t, digits=1))

if nearest.payload_t < 0:
    st.error(
        f"At {formatter.mass(nearest.dry_mass_t, digits=0)} empty, this vehicle cannot "
        "reach orbit at all, even carrying nothing.",
        icon="🚫",
    )
elif nearest.payload_t >= 100:
    st.success(
        f"At {formatter.mass(nearest.dry_mass_t, digits=0)} empty, the 100 tonne claim holds.",
        icon="✅",
    )
else:
    st.info(
        f"At {formatter.mass(nearest.dry_mass_t, digits=0)} empty, it carries "
        f"{formatter.mass(nearest.payload_t, digits=0)}, not the 100 tonnes claimed.",
        icon="ℹ️",
    )

st.plotly_chart(
    payload_against_dry_mass(
        [(point.dry_mass_t, point.payload_t) for point in points],
        arriving=[(point.dry_mass_t, point.mass_in_orbit_t) for point in points],
        markers=[
            (
                estimate.label,
                estimate.dry_mass_t,
                min(points, key=lambda p: abs(p.dry_mass_t - estimate.dry_mass_t)).payload_t,
            )
            for estimate in ESTIMATES
        ],
        formatter=formatter,
        mode=chart_mode,
        title="The same rocket, under every published belief about its weight",
        subtitle=(
            "The dotted line is what arrives in orbit. It barely moves. "
            "Everything saved on the ship becomes cargo instead."
        ),
    ),
    width="stretch",
)

st.divider()
st.subheader("Who says what")

st.markdown(
    table(
        [
            {
                "label": estimate.label,
                "dry": estimate.dry_mass_t,
                "payload": min(
                    points, key=lambda p: abs(p.dry_mass_t - estimate.dry_mass_t)
                ).payload_t,
                "source": estimate.source,
            }
            for estimate in ESTIMATES
        ],
        [
            Col("label", "Whose figure"),
            Col("dry", "Empty weight", Quantity.MASS, digits=0),
            Col("payload", "Payload it implies", Quantity.MASS, digits=1),
            Col("source", "Where it comes from"),
        ],
        formatter=formatter,
    )
)

why(
    "Why does the total reaching orbit not change?",
    """
Because the rocket equation does not care what the mass is made of.

Given the propellant Starship carries, its engines, and the speed it has to
reach, the arithmetic fixes the mass that arrives. Whether that mass is mostly
vehicle or mostly cargo is a question about construction, not about physics.

Which is why this argument is not really about rockets. Everyone agrees on the
equation. The disagreement is entirely about one unpublished number, and the
difference between the highest and lowest credible value for it is the
difference between a rocket that revolutionises spaceflight and one that
does not.
""",
)

why(
    "So who is right?",
    """
This app deliberately does not say, because the honest answer is that nobody
outside SpaceX can know yet.

What can be said: the 100 tonne claim requires a ship of about 165 tonnes empty.
Musk stated 200 tonnes for a prototype in 2019, before its heat shield, fins and
header tanks. Getting from there to 165 tonnes while adding all of that is a
large engineering achievement, and SpaceX has not claimed it publicly.

**Flight 14 will settle it.** It is the first orbital attempt, expected within
weeks, and it will deploy real satellites to a real orbit. That is a direct
measurement of the number this whole chapter is arguing about.
""",
)

st.caption(
    "The address bar follows the slider, so a link to this page carries whatever "
    "you set it to. Send someone the number you think is right."
)

try_this(
    "Drag the slider to 165 t and watch the payload reach 100 tonnes. Then drag "
    "it to 220 t, the source article's estimate. The rocket did not change. Only "
    "what you believe about it did."
)

chapter_footer(7)
