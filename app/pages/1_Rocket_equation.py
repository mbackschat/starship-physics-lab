"""Chapter 1: why going fast is so expensive."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st
from components.shell import (
    chapter_footer,
    chapter_link,
    formula_block,
    mode,
    page,
    sidebar,
    try_this,
    why,
)

from labbook.charts import base_layout, burn_animation, loading_curve
from labbook.curves import burn_trace, loading_sweep
from labbook.formula import Formula, Term
from labbook.palette import SURFACE, Series, colour
from labbook.units import Quantity
from labbook.visuals import rocket_cutaway
from rocketry.orbit import orbital_velocity
from rocketry.tsiolkovsky import binary_velocity, delta_v, exhaust_velocity

page("1 · The rocket equation", "One equation decides what every rocket can and cannot do.")
formatter = sidebar()
chart_mode = mode()

st.markdown(
    """
A rocket engine works by throwing mass backwards. Nothing else. How fast the
rocket ends up going depends on just two things: **how efficiently the engine
throws** and **how much of the rocket was propellant to begin with.**
"""
)

left, drawing, right = st.columns([1, 0.85, 1.25], gap="large")

with left:
    st.markdown("#### Build a rocket")
    dry = st.slider(
        "Empty rocket",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
        help="Everything that is not propellant: tanks, engines, structure, cargo.",
        format="%.0f t",
    )
    propellant = st.slider(
        "Propellant",
        min_value=1.0,
        max_value=900.0,
        value=90.0,
        step=1.0,
        help="What it burns.",
        format="%.0f t",
    )
    isp = st.slider(
        "Engine efficiency (specific impulse)",
        min_value=200,
        max_value=460,
        value=350,
        step=1,
        help=(
            "Seconds. An engine with 350 s could hold up 1 tonne for 350 seconds "
            "while burning 1 tonne of propellant. Higher is better."
        ),
        format="%d s",
    )

    wet = dry + propellant
    ratio = wet / dry
    achieved = delta_v(wet, dry, isp)
    orbital = orbital_velocity(200)

    st.metric("Speed this rocket reaches", formatter.velocity(achieved, digits=0))
    st.progress(
        min(1.0, achieved / orbital),
        text=f"{achieved / orbital:.0%} of the {formatter.velocity(orbital, digits=0)} "
        "needed to orbit",
    )

with drawing:
    st.markdown("#### What you built")
    st.markdown(
        rocket_cutaway(
            dry_t=dry,
            propellant_t=propellant,
            mode=chart_mode,
            formatter=formatter,
            height=330,
            uid="ch1",
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        "Drawn to scale by mass. Push the propellant slider and watch the orange "
        "take over: a real launcher is about 95 % propellant on the pad."
    )

with right:
    st.markdown("#### The equation, with your numbers in it")
    formula_block(
        Formula(
            name="Tsiolkovsky's rocket equation, 1903",
            symbolic="Δv = v_e × ln( m₀ / m_f )",
            terms=[
                Term("v_e", exhaust_velocity(isp), Quantity.VELOCITY, digits=0),
                Term("m₀", wet, Quantity.MASS, digits=0),
                Term("m_f", dry, Quantity.MASS, digits=0),
            ],
            result=Term("Δv", achieved, Quantity.VELOCITY, digits=0),
            note=(
                f"Your mass ratio is {ratio:.2f}. That single number, put through a "
                "logarithm, decides almost everything."
            ),
        ),
        formatter,
    )

    why(
        "Why a logarithm, of all things?",
        """
Because the rocket has to accelerate its own propellant too. The propellant you
burn at the end had to be carried, and accelerated, by the propellant you burnt
at the start.

That feedback is what turns a straightforward push into a logarithm. Going twice
as fast does not cost twice as much propellant. It costs the *square* of the mass
ratio.
""",
    )
    try_this(
        "Push the propellant slider to its maximum and watch how little extra speed "
        "the last few tonnes buy you. Then raise the engine efficiency by 30 s "
        "instead, and compare."
    )

st.divider()

st.subheader("Two questions that sound identical, and bend opposite ways")
st.markdown(
    """
Almost everyone fuses these into one wrong intuition, so it is worth separating
them deliberately. **Press play on the left.**
"""
)

during, before = st.columns(2, gap="large")

with during:
    st.plotly_chart(
        burn_animation(
            burn_trace(dry_t=dry, propellant_t=propellant, isp_s=isp),
            formatter=formatter,
            mode=chart_mode,
            title="While it burns",
            subtitle="Equal chunks of propellant. The line gets steeper.",
        ),
        width="stretch",
    )
    st.caption(
        "**Speeding up.** Each tonne burnt leaves a lighter rocket, so the next "
        "tonne pushes harder. The final tonne is worth many times the first, "
        "which is why crews are pressed hardest into their seats just before the "
        "engines cut."
    )

with before:
    st.plotly_chart(
        loading_curve(
            loading_sweep(dry_t=dry, isp_s=isp, up_to_t=900.0),
            formatter=formatter,
            mode=chart_mode,
            at_t=propellant,
            title="Before it flies",
            subtitle="Equal chunks of propellant. The line flattens out.",
        ),
        width="stretch",
    )
    st.caption(
        "**Slowing down.** Every tonne you add on the pad has to be carried and "
        "accelerated by all the propellant beneath it. Load twice as much and "
        "you do not go twice as fast. This is the wall the whole subject runs "
        "into."
    )

why(
    "How can both be true at once?",
    """
Because they are answers to different questions.

The left chart follows **one rocket through one burn**. Its mass is falling, so
its acceleration is rising. Nothing is being added.

The right chart compares **different rockets on the launch pad**, each loaded
with more propellant than the last. The extra propellant has to lift itself, and
that self-carrying cost is what flattens the curve.

Same equation. The left one moves along a fixed curve; the right one asks what
happens when you change the rocket. Chapter 4 is what you do about the wall on
the right, and the answer is not "more propellant".
""",
)

st.divider()

st.subheader("Every doubling buys the same amount of speed, and costs twice as much")

step = binary_velocity(isp)
rows = []
for n in range(1, 7):
    mass_ratio = 2**n
    rows.append(
        {
            "doublings": n,
            "ratio": mass_ratio,
            "propellant": (mass_ratio - 1) * 1.0,
            "added": (mass_ratio // 2) * 1.0,
            "speed": n * step,
        }
    )

ladder_left, ladder_right = st.columns([1.2, 1], gap="large")

with ladder_left:
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=[row["speed"] for row in rows],
            y=[formatter.value(row["propellant"], Quantity.MASS) for row in rows],
            marker={
                "color": colour(Series.PROPELLANT, chart_mode),
                "line": {"color": SURFACE[chart_mode], "width": 2},
            },
            text=[formatter.mass(row["propellant"], digits=0) for row in rows],
            textposition="outside",
            hovertemplate="%{x:,.0f} → %{y:,.0f}<extra></extra>",
            showlegend=False,
        )
    )
    base_layout(
        figure,
        title="Propellant needed for a 1 t rocket",
        subtitle="Each step up is the same gain in speed. Look at what it costs.",
        x_label=formatter.axis_label("Speed reached", Quantity.VELOCITY),
        y_label=formatter.axis_label("Propellant", Quantity.MASS),
        mode=chart_mode,
        show_legend=False,
    )
    st.plotly_chart(figure, width="stretch")

with ladder_right:
    st.markdown(
        f"""
Take a rocket weighing {formatter.mass(1.0, digits=0)} empty. At
{isp} s of engine efficiency, every doubling of the mass ratio buys it exactly
**{formatter.velocity(step, digits=0)}** more speed.

| Speed | Mass ratio | Propellant |
|---:|---:|---:|
"""
        + "\n".join(
            f"| {formatter.velocity(row['speed'], digits=0)} | {row['ratio']}:1 "
            f"| {formatter.mass(row['propellant'], digits=0)} |"
            for row in rows
        )
    )
    st.caption(
        "The speed column climbs in equal steps. The propellant column doubles "
        "every time. That gap is the entire difficulty of spaceflight."
    )

why(
    "So why does anyone manage it at all?",
    """
Two answers, and the app spends the rest of its chapters on them.

**Better engines.** Every extra second of specific impulse moves the whole curve.
This is why a hydrogen upper stage at 450 s can do things a kerosene one at 340 s
cannot.

**Staging.** Stop carrying the empty tanks. Throw away the part you have finished
with and the mass ratio resets. It is a crude trick and it is the only reason
orbit is reachable at all.
""",
)

chapter_link(4, question=True)

chapter_footer(1)
