"""Chapter 5: what it costs to get the rocket back."""

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
    vehicle_picker,
    why,
)

from labbook.breakdown import as_series, mass_components
from labbook.charts import mass_breakdown
from labbook.tables import Col, table
from labbook.units import Quantity
from rocketry.reuse import RecoveryProfile, profile_for
from rocketry.vehicle import with_stage

page("5 · Reuse", "A rocket that comes home carries the fuel for the trip back all the way up.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
Landing a booster is not free, and the cost is not paid at landing. It is paid at
liftoff, because every tonne of propellant reserved for coming home is a tonne
that had to be lifted off the pad in the first place.
"""
)

picker, summary = st.columns([1, 2], gap="large")

with picker:
    key = vehicle_picker(default="falcon9_droneship", key="reuse_vehicle")
    vehicle = lib.vehicle(key)
    first_stage = lib.stage(vehicle.stages[0])
    st.markdown("#### How should the booster come home?")
    profile = st.radio(
        "Recovery",
        options=list(RecoveryProfile),
        format_func=lambda item: profile_for(item).label,
        index=1,
        key="recovery_profile",
        label_visibility="collapsed",
        help=(
            "How the first stage gets back. Each one asks more of it than the "
            "last, and every metre per second of that is paid for on the way up."
        ),
    )
    reset_button("reuse_vehicle", "recovery_profile")
    described = profile_for(profile)
    st.caption(described.explanation)

scenario = with_stage(lib, key, first_stage.key, recovery=described.as_recovery())
expendable = with_stage(
    lib, key, first_stage.key, recovery=profile_for(RecoveryProfile.EXPENDABLE).as_recovery()
)
booster = scenario.stages[0]
lost = expendable.total_delta_v - scenario.total_delta_v

with summary:
    one, two, three, four = st.columns(4)
    one.metric("Held back for the trip home", formatter.mass(booster.recovery_reserve_t, digits=0))
    two.metric("Share of the booster's tanks", formatter.percent(booster.reuse_cost_fraction))
    three.metric("Per tonne of booster", f"{described.propellant_per_tonne():.2f} t/t")
    four.metric(
        "Δv given up",
        formatter.velocity(lost, digits=0),
        delta=f"-{lost:,.0f}" if lost else "0",
        delta_color="inverse",
    )
    if described.burns:
        st.markdown(
            table(
                [
                    {"label": burn.label.capitalize(), "dv": burn.delta_v, "isp": burn.isp}
                    for burn in reversed(described.burns)
                ],
                [
                    Col("label", "Manoeuvre"),
                    Col("dv", "Δv", Quantity.VELOCITY, digits=0),
                    Col("isp", "Isp", Quantity.ISP, digits=0),
                ],
                formatter=formatter,
            )
        )
    else:
        st.info(
            "Nothing is held back. Every tonne of propellant accelerates the "
            "payload, and the booster is lost.",
            icon="🗑️",
        )

st.divider()

rows = mass_components(scenario)
st.plotly_chart(
    mass_breakdown(
        [row.label for row in rows],
        as_series(rows),
        formatter=formatter,
        mode=chart_mode,
        title=f"{vehicle.name}: {described.label.lower()}",
        subtitle="The yellow band is propellant carried to orbit purely to come back down.",
    ),
    width="stretch",
)

st.divider()

st.subheader("The same rocket, every way of getting it back")

comparison = []
for candidate in RecoveryProfile:
    description = profile_for(candidate)
    result = with_stage(lib, key, first_stage.key, recovery=description.as_recovery())
    reserve = result.stages[0].recovery_reserve_t
    comparison.append(
        {
            "mode": description.label,
            "reserve": reserve,
            "fraction": result.stages[0].reuse_cost_fraction,
            "delta_v": result.total_delta_v,
            "cost": expendable.total_delta_v - result.total_delta_v,
        }
    )

st.markdown(
    table(
        comparison,
        [
            Col("mode", "How it comes home"),
            Col("reserve", "Propellant held back", Quantity.MASS, digits=0),
            Col("fraction", "Share of its tanks", Quantity.PERCENT),
            Col("delta_v", "Δv the stack still has", Quantity.VELOCITY, digits=0),
            Col("cost", "Δv given up", Quantity.VELOCITY, digits=0),
        ],
        formatter=formatter,
    )
)

why(
    "Why does flying back cost so much more than landing on a ship?",
    """
Because the booster is already travelling downrange at over 2,000 m/s when it
separates, and returning means cancelling all of that and then travelling back.

Landing on a ship asks far less: keep going the way you were already going, slow
down enough to survive the air, and stop. No turn, no return trip.

Super Heavy takes the expensive option because SpaceX wants to catch it on the
launch tower and fly it again within the hour. That is a choice about turnaround
time, and it is paid for in payload on every single flight.

China's Long March 10B showed another answer in July 2026: catch the booster at
sea, in a net of tensioned cables on a ship, with no landing legs at all.
""",
)

why(
    "Is reuse worth it, then?",
    """
For Falcon 9, clearly. It gives up roughly a quarter of its payload and gets the
most expensive part of the rocket back, many times over.

The interesting question is not whether to reuse but how much to pay for it. A
booster that lands on a ship gives up far less than one that flies home, and the
difference buys nothing except a faster turnaround.
""",
)

try_this(
    "Switch between **Land on a ship downrange** and **Fly back to the launch "
    "site** and watch the yellow band grow. Then switch the rocket to Starship "
    "and see what the same choice costs a vehicle ten times the size."
)

chapter_footer(5)
