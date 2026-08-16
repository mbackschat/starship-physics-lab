"""Chapter 6: how to weigh a rocket you have never touched."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import library, page, sidebar, try_this, why

from labbook.casestudy import weigh_from_burn
from labbook.tables import Col, table
from labbook.units import Quantity

page("6 · Weighing Starship", "You can weigh a rocket from the ground, by watching it burn.")
formatter = sidebar()
lib = library()

st.markdown(
    """
SpaceX has not published Starship's empty weight since 2019. That is awkward,
because as the next chapter shows, it is the number that decides everything.

So it has to be measured from outside. The rocket equation works backwards: if
you know how much propellant a burn used and how much it changed the vehicle's
speed, you know what the vehicle weighed.
"""
)

st.divider()
st.subheader("Flight 13, 24 July 2026")

flight = lib.flight(13)
st.markdown(
    f"""
Thirty-nine minutes after launch, Starship relit a single Raptor and slowed
down. The burn was visible, it was timed, and the speed change was reported.
That is enough.

*{flight.ship_outcome.strip() if flight.ship_outcome else ""}*
"""
)

controls, result_column = st.columns([1, 1.6], gap="large")

with controls:
    seconds = st.slider(
        "How long the engine ran",
        min_value=8.0,
        max_value=20.0,
        value=14.0,
        step=0.5,
        format="%.1f s",
        help="Observed at 14 seconds on Flight 13.",
    )
    thrust = st.slider(
        "Engine thrust",
        min_value=200.0,
        max_value=280.0,
        value=250.0,
        step=5.0,
        format="%.0f tf",
        help="A Raptor 3 runs at about 250 tf, throttled down from its 280 tf rating.",
    )
    speed_change = st.slider(
        "How much it slowed down",
        min_value=100.0,
        max_value=180.0,
        value=138.9,
        step=1.0,
        format="%.0f m/s",
        help="Reported as 500 km/h, which is 139 m/s.",
    )
    engine_isp = 327.0
    vacuum_isp = 350.0
    propellant = thrust / engine_isp * seconds

with result_column:
    weighing = weigh_from_burn(propellant_t=propellant, delta_v=speed_change, isp=vacuum_isp)
    one, two, three = st.columns(3)
    one.metric("Propellant burnt", formatter.mass(propellant, digits=1))
    two.metric("Ship weighed", formatter.mass(weighing.mass_after_t, digits=0))
    three.metric("Before the burn", formatter.mass(weighing.mass_before_t, digits=0))
    st.markdown(
        f"""
Burning **{formatter.mass(propellant, digits=1)}** of propellant to lose
**{formatter.velocity(speed_change, digits=0)}** means the ship weighed
**{formatter.mass(weighing.mass_after_t, digits=0)}** when the burn finished.

That is a measurement, not an estimate. It needs no access to the vehicle and no
cooperation from anybody.
"""
    )

st.warning(
    "**But it measures the total.** Ship plus whatever propellant was still in "
    "the tanks. Splitting that into an empty weight requires assuming how much "
    "was left, and that is where honest people start to disagree.",
    icon="⚠️",
)

residual = st.slider(
    "Assume this much propellant was still aboard",
    min_value=0.0,
    max_value=80.0,
    value=40.0,
    step=1.0,
    format="%.0f t",
    help="For the landing burn and manoeuvring. Nobody outside SpaceX knows this number.",
)
st.metric("Implied empty weight", formatter.mass(weighing.dry_mass_t(residual), digits=0))

st.divider()
st.subheader("Three ways of measuring, and where they land")

rows = [
    {
        "method": "The 14 s relight on Flight 13",
        "low": weigh_from_burn(propellant_t=10.0, delta_v=138.9, isp=350).mass_after_t,
        "high": weigh_from_burn(propellant_t=10.7, delta_v=138.9, isp=350).mass_after_t,
        "measures": "Total mass before reentry",
    },
    {
        "method": "Hovering on its engines",
        "low": 200.0,
        "high": 250.0,
        "measures": "Mass at landing",
    },
    {
        "method": "Musk, September 2019",
        "low": 200.0,
        "high": 200.0,
        "measures": "Dry mass of a prototype, without a heat shield",
    },
]
st.markdown(
    table(
        rows,
        [
            Col("method", "How"),
            Col("low", "Lowest", Quantity.MASS, digits=0),
            Col("high", "Highest", Quantity.MASS, digits=0),
            Col("measures", "What it actually measures"),
        ],
        formatter=formatter,
    )
)

why(
    "How does hovering weigh anything?",
    """
By bracketing it between two thrust limits.

The landing burn is flown on two engines, which together cannot throttle below
roughly 180 tonnes of thrust. If the ship can hover on them without being pushed
back up, it weighs at least that much.

At the other end, a single Raptor at full throttle produces about 250 tonnes of
thrust, and one engine has been enough to hold it briefly. So it weighs less
than that.

Two crude observations, and between them the answer has to lie: somewhere
between 200 and 250 tonnes at landing.
""",
)

try_this(
    "Set the burn to 10 seconds and then to 14. The measured mass moves by about "
    "70 tonnes. This is why the exact burn duration matters so much, and why the "
    "source article is careful to give a range rather than a single number."
)

st.caption(
    "Every number on this page is observable from the ground. The one number "
    "that is not, the propellant still in the tanks, is the one the next chapter "
    "turns into a slider."
)
