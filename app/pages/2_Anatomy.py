"""Chapter 2: what a rocket is actually made of."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import (
    chapter_footer,
    chapter_link,
    library,
    mode,
    page,
    provenance_badge,
    sidebar,
    try_this,
    vehicle_picker,
    why,
)

from labbook.breakdown import as_series, mass_components
from labbook.charts import mass_breakdown
from labbook.tables import Col, table
from labbook.units import Quantity
from rocketry.models import Provenance
from rocketry.vehicle import analyse

page("2 · Anatomy of a rocket", "Almost none of a rocket is cargo. Here is where it all goes.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
Pick a rocket and look at what it is made of. The proportions are the point: the
payload is the thin sliver at the end, and that is not a design failure, it is
what the rocket equation demands.
"""
)

picker, summary = st.columns([1, 1.6], gap="large")

with picker:
    key = vehicle_picker()
    vehicle = lib.vehicle(key)
    result = analyse(lib, key)
    st.markdown(f"**{vehicle.operator}** · {vehicle.launch_site or 'no launch site on record'}")
    provenance_badge(vehicle.provenance, inline=True)

with summary:
    one, two, three, four = st.columns(4)
    one.metric("Liftoff mass", formatter.mass(result.liftoff_mass_t, digits=0))
    two.metric("Payload", formatter.mass(result.payload_t, digits=1))
    three.metric("Payload fraction", formatter.percent(result.payload_fraction, digits=2))
    four.metric("Ideal Δv", formatter.velocity(result.total_delta_v, digits=0))
    if vehicle.note:
        st.caption(vehicle.note.strip())

st.divider()

st.subheader("Where the mass goes")

stages = list(result.stages)
rows_by_mass = mass_components(result)
labels = [row.label for row in rows_by_mass]
components = as_series(rows_by_mass)

figure = mass_breakdown(
    labels,
    components,
    formatter=formatter,
    mode=chart_mode,
    title=f"{vehicle.name}: every tonne accounted for",
    subtitle="Payload is the blue sliver. Everything else exists to move it.",
)
st.plotly_chart(figure, width="stretch")

if any(analysis.recovery_reserve_t > 0 for analysis in stages):
    reserved = sum(analysis.recovery_reserve_t for analysis in stages)
    st.caption(
        f"{formatter.mass(reserved, digits=0)} of propellant is carried all the way up "
        "purely so the rocket can come back down again."
    )
    chapter_link(5)

st.divider()

st.subheader("Stage by stage")

rows = [
    {
        "name": analysis.stage.name,
        "dry": analysis.stage.dry_mass_t,
        "propellant": analysis.stage.propellant_t,
        "fraction": analysis.stage.dry_mass_fraction,
        "delta_v": analysis.delta_v,
        "share": analysis.delta_v / result.total_delta_v if result.total_delta_v else 0.0,
        "provenance": analysis.stage.provenance.value,
    }
    for analysis in stages
]

st.markdown(
    table(
        rows,
        [
            Col("name", "Stage"),
            Col("dry", "Empty mass", Quantity.MASS),
            Col("propellant", "Propellant", Quantity.MASS),
            Col("fraction", "Empty mass fraction", Quantity.PERCENT),
            Col("delta_v", "Δv contributed", Quantity.VELOCITY, digits=0),
            Col("share", "Share of total Δv", Quantity.PERCENT),
            Col("provenance", "Source"),
        ],
        formatter=formatter,
    )
)

contested = [
    analysis.stage for analysis in stages if analysis.stage.provenance is Provenance.CONTESTED
]
for stage in contested:
    st.warning(
        f"**{stage.name}** rests on a contested number. {stage.source.strip()}",
        icon="⚠️",
    )

why(
    "What is an empty mass fraction, and what counts as good?",
    """
It is the stage's own weight divided by its weight when full. Lower is better:
it means more of what you lifted was propellant doing useful work.

Around **5 %** is excellent for an expendable stage. **12 %** sounds bad until you
remember the stage is also carrying a heat shield, fins and a nose so it can come
home again.

Here is the trap, and it is worth carrying into the chapter on staging. The
Ariane 6 upper stage has an empty mass fraction of about **16 %**, worse than
Starship's, and it still delivers more payload. Build quality is not what
separates them. Where the stages separate is.
""",
)

chapter_link(4)

try_this(
    "Compare **Falcon 9 (droneship recovery)** with **Falcon 9 (expendable)**. Same "
    "rocket, same stages. The only difference is whether the first stage keeps "
    "propellant back to land, and it costs about a quarter of the payload."
)

chapter_footer(2)
