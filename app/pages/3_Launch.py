"""Chapter 3: fly it, and watch where the speed goes."""

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
    sidebar,
    try_this,
    vehicle_picker,
    why,
)

from labbook.charts import loss_waterfall, trajectory
from rocketry.ascent import AscentResult, AscentSettings, simulate
from rocketry.vehicle import analyse

page("3 · Launch", "A rocket never gets what the equation promises. Here is who takes the cut.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
The rocket equation gave the ideal: what the engines could do in empty space. A
real launch is fought against gravity and air the whole way up, and the
difference is not small. Roughly a fifth of everything the engines produce never
becomes speed.
"""
)

chapter_link(1)


@st.cache_data(show_spinner=False)
def fly(key: str, turn_shape: float, drag: float, payload: float | None) -> AscentResult | str:
    """Simulate a launch, cached so sliders stay responsive.

    The picker offers every vehicle in the library, and not all of them can be
    flown by this model. A vehicle whose boosters burn in parallel is walked as
    a sequence of stages, which computes a thrust-to-weight below 1 and makes
    `simulate` refuse. That refusal is correct; showing the reader its traceback
    is not.

    Args:
        key: Vehicle key.
        turn_shape: How eagerly the rocket pitches over.
        drag: Drag coefficient.
        payload: Payload override in tonnes, or None for the published figure.

    Returns:
        The ascent result, or the reason it could not be simulated.
    """
    vehicle = analyse(library(), key, payload)
    try:
        return simulate(vehicle, AscentSettings(turn_shape=turn_shape, drag_coefficient=drag))
    except ValueError as refusal:
        return str(refusal)


controls, readout = st.columns([1, 2], gap="large")

with controls:
    key = vehicle_picker(default="falcon9_droneship")
    vehicle = lib.vehicle(key)
    st.markdown("#### How to fly it")
    turn_shape = st.slider(
        "Pitch-over",
        min_value=0.5,
        max_value=1.3,
        value=1.0,
        step=0.05,
        help=(
            "How eagerly the rocket tips over. Low values hang on to the "
            "vertical and pay for it. High values tip too early and fly into "
            "thick air."
        ),
    )
    drag = st.slider(
        "Drag coefficient",
        min_value=0.2,
        max_value=0.9,
        value=0.5,
        step=0.05,
        help="How slippery the rocket is. A blunter shape pushes more air aside.",
    )

result = fly(key, turn_shape, drag, None)

if isinstance(result, str):
    with readout:
        st.error(
            f"**{vehicle.name} cannot be flown by this model.** {result}\n\n"
            "This is a limit of the simulation rather than of the rocket. Its "
            "boosters and core burn at the same time, and this model walks a "
            "stack one stage after another, so it never sees them firing "
            "together. The analytic chapters still handle it; only the flight "
            "does not.",
            icon="🧮",
        )
        chapter_link(4)
    st.stop()

with readout:
    if result.crashed:
        st.error(
            "**It came back down.** The pitch program tipped it over before it had "
            "the altitude to survive the thick air. Raise the pitch-over slider, or "
            "lower it if the rocket is climbing straight up and running out of "
            "propellant.",
            icon="💥",
        )
    one, two, three, four = st.columns(4)
    one.metric("Speed at cutoff", formatter.velocity(result.final_speed, digits=0))
    two.metric("Altitude", formatter.altitude_km(result.final_altitude_m, digits=0))
    three.metric("Max q", f"{result.max_dynamic_pressure_pa / 1000:,.0f} kPa")
    four.metric("Lost to losses", formatter.percent(result.loss_fraction))

    st.plotly_chart(
        trajectory(
            result.samples,
            events=[
                (event.name, event.downrange_m, event.altitude_m) for event in result.events
            ],
            formatter=formatter,
            mode=chart_mode,
            title=f"{vehicle.name}: the path it flies",
            subtitle=(
                "Straight up at first, then almost entirely sideways. "
                "Orbit is speed, not height."
            ),
        ),
        width="stretch",
    )

st.divider()

st.subheader("Where the engines' work went")

st.plotly_chart(
    loss_waterfall(
        result.breakdown,
        formatter=formatter,
        mode=chart_mode,
        title="",
        subtitle=(
            f"The engines produced {formatter.velocity(result.ideal_delta_v, digits=0)}. "
            f"Only {formatter.velocity(result.final_speed, digits=0)} of it became speed."
        ),
    ),
    width="stretch",
)

columns = st.columns(4)
columns[0].metric("Engines produced", formatter.velocity(result.ideal_delta_v, digits=0))
columns[1].metric("Gravity took", formatter.velocity(result.gravity_loss, digits=0))
columns[2].metric("Air took", formatter.velocity(result.drag_loss, digits=0))
columns[3].metric("Steering took", formatter.velocity(result.steering_loss, digits=0))

why(
    "Why is gravity loss so much bigger than drag?",
    """
Because gravity never stops pulling, and air runs out fast.

Every second the rocket spends climbing, gravity removes about 9.8 m/s from its
vertical speed. A launch that takes 500 seconds and spends much of it pointing
upwards hands over well over a thousand m/s that way.

Air, by contrast, is essentially gone above 60 km, and the rocket is only moving
fast enough to care about it for about a minute. That is why launches look
strange: they tip over almost immediately. Every second spent going straight up
is expensive, and altitude is not the goal. **Orbit is sideways speed.** Height
only buys you thin air to build that speed in.
""",
)

why(
    "Why does gravity loss shrink towards the end of the flight?",
    """
Because going sideways fast holds you up.

The faster the rocket travels horizontally, the more the curve of the Earth falls
away beneath it, and the less of its thrust it needs to spend fighting its own
weight. At orbital speed the two cancel exactly, which is the entire definition
of being in orbit.

The simulation models this, which is why a rocket that is already fast can fly
almost horizontally without falling.
""",
)

try_this(
    "Drag the pitch-over slider down to 0.6 and watch gravity loss climb by "
    "several hundred m/s. Then push it up past 1.2 and watch the rocket fly into "
    "thick air and lose everything to drag instead. Somewhere in between is the "
    "trade every launch flies."
)

st.caption(
    "Model note: a single drag coefficient for the whole stack, a prescribed "
    "pitch program rather than a free gravity turn, and a non-rotating Earth. "
    "Good enough to be right about the size and ordering of the losses, not a "
    "trajectory design tool."
)

chapter_footer(3)
