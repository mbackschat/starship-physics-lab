"""Chapter 7b: SpaceX plans to make the ship bigger. Does that help?"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import library, mode, page, sidebar, try_this, why

from labbook.charts import payload_against_dry_mass
from labbook.tables import Col, table
from labbook.units import Quantity
from rocketry.scaling import FIXED, REALISTIC, scaled_dry_mass
from rocketry.staging import two_stage_payload

page("8 · Bigger is better?", "Starship V4 grows the ship again. The physics says that hurts.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
Starship V4, planned for 2027, keeps the same booster proportions and makes the
ship much bigger: 2,300 tonnes of propellant on a 4,050 tonne booster. That
pushes the split between the stages further in the direction chapter 4 showed to
be expensive.

How much it hurts depends almost entirely on one assumption nobody can settle:
**does a bigger ship weigh proportionally more?**
"""
)

exponent = st.slider(
    "How much heavier does a bigger ship get?",
    min_value=0.0,
    max_value=1.0,
    value=REALISTIC,
    step=0.05,
    help=(
        "0 means stretching the tanks adds no weight at all. 1 means weight "
        "grows in exact proportion to propellant. Reality is in between, because "
        "tanks scale with size while engines, nose and fins largely do not."
    ),
)

v4 = two_stage_payload(booster_propellant=4050, ship_propellant=2300, scaling_exponent=exponent)
v3 = two_stage_payload(booster_propellant=3650, ship_propellant=1600, scaling_exponent=exponent)
ship_dry = scaled_dry_mass(
    reference_dry=220, reference_propellant=1600, propellant=2300, exponent=exponent
)

one, two, three, four = st.columns(4)
one.metric("V4 ship weighs", formatter.mass(ship_dry, digits=0))
two.metric("V4 payload", formatter.mass(v4.payload, digits=0))
three.metric("V3 payload, same assumption", formatter.mass(v3.payload, digits=0))
four.metric(
    "What the stretch buys",
    formatter.mass(v4.payload - v3.payload, digits=0),
    delta=f"{v4.payload - v3.payload:+,.0f} t",
)

if v4.payload < v3.payload:
    st.error(
        f"Under this assumption the stretch makes things worse: a "
        f"{v4.liftoff_mass / v3.liftoff_mass - 1:.0%} heavier rocket carrying "
        f"{formatter.mass(v3.payload - v4.payload, digits=0)} less.",
        icon="📉",
    )
else:
    st.success("Under this assumption the stretch pays off.", icon="📈")

span = [round(FIXED + step * 0.05, 2) for step in range(21)]
curve = [
    (
        scaled_dry_mass(
            reference_dry=220, reference_propellant=1600, propellant=2300, exponent=value
        ),
        two_stage_payload(
            booster_propellant=4050, ship_propellant=2300, scaling_exponent=value
        ).payload,
    )
    for value in span
]
arriving = [
    (
        point[0],
        two_stage_payload(
            booster_propellant=4050, ship_propellant=2300, scaling_exponent=value
        ).mass_in_orbit,
    )
    for point, value in zip(curve, span, strict=True)
]

st.plotly_chart(
    payload_against_dry_mass(
        sorted(curve),
        arriving=sorted(arriving),
        markers=[
            ("mass grows in proportion", curve[-1][0], curve[-1][1]),
            ("mass does not grow at all", curve[0][0], curve[0][1]),
        ],
        formatter=formatter,
        mode=chart_mode,
        title="Starship V4, under every assumption about how weight scales",
        subtitle=(
            "One assumption, and the answer swings by a factor of nine. "
            "The dotted line, as always, barely moves."
        ),
    ),
    width="stretch",
)

st.divider()
st.subheader("How the stages divide the propellant")

rows = [
    {"name": "Falcon 9 Block 5", "first": 395.7, "second": 107.0},
    {"name": "Starship V3, flying now", "first": 3650.0, "second": 1600.0},
    {"name": "Starship V4, announced", "first": 4050.0, "second": 2300.0},
    {"name": "The article's redesign", "first": 4250.0, "second": 1022.0},
]
for row in rows:
    row["ratio"] = row["first"] / row["second"]

st.markdown(
    table(
        rows,
        [
            Col("name", "Vehicle"),
            Col("first", "First stage", Quantity.MASS, digits=0),
            Col("second", "Second stage", Quantity.MASS, digits=0),
            Col("ratio", "Ratio", digits=2),
        ],
        formatter=formatter,
    )
)
st.caption(
    "Falcon 9's first stage holds nearly four times the propellant of its second. "
    "Starship's holds barely twice. V4 makes that worse, not better."
)

why(
    "Is there anything that rescues V4?",
    """
Two things, and neither is enough on its own.

**Weight probably does not scale in proportion.** A longer tank is mostly extra
cylinder, while the nose, fins, heat shield and engines barely change. Somewhere
around 0.8 on the slider is a fair guess, and that already helps a lot.

**V4's ship gets six vacuum engines instead of three.** Bigger nozzles are more
efficient in vacuum, which is worth roughly 23 tonnes of payload by itself.

Put both together and V4 looks survivable rather than good. What would actually
help is the thing chapter 4 pointed at: separating the stages later, not making
the upper stage bigger.
""",
)

try_this(
    "Set the slider to 1.0 and then to 0.0. Same announced rocket, same physics, "
    "and the payload goes from about 12 tonnes to over 100. That gap is not "
    "uncertainty about rocketry. It is uncertainty about one company's welding."
)
