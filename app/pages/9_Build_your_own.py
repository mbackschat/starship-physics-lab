"""Chapter 9: build a rocket and find out whether it works."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import library, mode, page, sidebar, try_this, vehicle_picker, why

from labbook.breakdown import as_series, mass_components
from labbook.charts import mass_breakdown
from labbook.tables import Col, table
from labbook.units import Quantity
from rocketry.dynamics import thrust_to_weight
from rocketry.reuse import RecoveryProfile, profile_for
from rocketry.scaling import REALISTIC, scaled_dry_mass
from rocketry.vehicle import LEO_MISSION_DELTA_V, analyse, scenario

page(
    "9 · Build your own",
    "You have the same physics everyone else has. See what you can do with it.",
)
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
Start from a real rocket and change it. The physics underneath is the same
engine that produced every other chapter, so anything you build here is being
judged by exactly the same rules as Falcon 9 and Saturn V.
"""
)

base_key = vehicle_picker("Start from", default="starship_v3", key="sandbox_base")
base = lib.vehicle(base_key)
stages = lib.stages_of(base_key)
booster, ship = stages[0], stages[-1]

st.divider()
first, second, mission = st.columns(3, gap="large")

with first:
    st.markdown(f"#### First stage · {booster.name}")
    booster_prop = st.slider(
        "Propellant",
        min_value=float(round(booster.propellant_t * 0.4)),
        max_value=float(round(booster.propellant_t * 1.6)),
        value=float(booster.propellant_t),
        step=10.0,
        format="%.0f t",
        key="sb_bp",
    )
    booster_dry = st.slider(
        "Empty weight",
        min_value=float(round(booster.dry_mass_t * 0.5)),
        max_value=float(round(booster.dry_mass_t * 1.8)),
        value=float(booster.dry_mass_t),
        step=5.0,
        format="%.0f t",
        key="sb_bd",
    )
    engines = st.slider(
        "Engines",
        min_value=max(1, booster.engine_count // 3),
        max_value=booster.engine_count * 2,
        value=booster.engine_count,
        step=1,
        key="sb_be",
    )
    profile = st.selectbox(
        "How it comes home",
        options=list(RecoveryProfile),
        format_func=lambda item: profile_for(item).label,
        index=list(RecoveryProfile).index(RecoveryProfile.TOWER_CATCH),
        key="sb_rec",
    )

with second:
    st.markdown(f"#### Upper stage · {ship.name}")
    ship_prop = st.slider(
        "Propellant",
        min_value=float(round(ship.propellant_t * 0.2)),
        max_value=float(round(ship.propellant_t * 1.6)),
        value=float(ship.propellant_t),
        step=10.0,
        format="%.0f t",
        key="sb_sp",
    )
    # Without this, shrinking a stage keeps all its weight and makes the rocket
    # worse, which teaches the opposite of the truth. A smaller stage really is
    # lighter.
    auto_scale = st.checkbox(
        "Let a smaller stage be lighter",
        value=True,
        key="sb_scale",
        help=(
            "A stage with less propellant has smaller tanks. Leave this on "
            "unless you specifically want to model a stage that was shrunk "
            "without saving any weight."
        ),
    )
    scaled = scaled_dry_mass(
        reference_dry=ship.dry_mass_t,
        reference_propellant=ship.propellant_t,
        propellant=ship_prop,
        exponent=REALISTIC,
    )
    ship_dry = st.slider(
        "Empty weight",
        min_value=float(round(ship.dry_mass_t * 0.2)),
        max_value=float(round(ship.dry_mass_t * 1.6)),
        value=float(round(scaled)) if auto_scale else float(ship.dry_mass_t),
        step=5.0,
        format="%.0f t",
        key="sb_sd" if not auto_scale else f"sb_sd_{round(scaled)}",
        disabled=auto_scale,
    )
    if auto_scale:
        st.caption(
            f"Scaled automatically to {formatter.mass(scaled, digits=0)}. "
            "Untick to set it yourself."
        )

with mission:
    st.markdown("#### The mission")
    budget = st.slider(
        "Velocity needed",
        min_value=8800.0,
        max_value=10400.0,
        value=LEO_MISSION_DELTA_V,
        step=50.0,
        format="%.0f m/s",
        help=(
            "Low Earth orbit costs about 9,400 m/s once losses are counted. A "
            "higher orbit, or a polar one, costs more."
        ),
        key="sb_budget",
    )

design = scenario(
    lib,
    base_key,
    **{
        booster.key: {
            "propellant_t": booster_prop,
            "dry_mass_t": booster_dry,
            "engine_count": engines,
            "recovery": profile_for(profile).as_recovery(),
        },
        ship.key: {"propellant_t": ship_prop, "dry_mass_t": ship_dry},
    },
)
payload = design.solve_payload(budget)
result = design.at_payload(max(payload, 0.0))
engine = lib.engine(booster.engine)
liftoff_thrust = (engine.thrust_sl_tf or engine.thrust_vac_tf) * engines
twr = thrust_to_weight(liftoff_thrust, result.liftoff_mass_t)

st.divider()
one, two, three, four, five = st.columns(5)
one.metric("Liftoff mass", formatter.mass(result.liftoff_mass_t, digits=0))
two.metric("Liftoff thrust", formatter.thrust(liftoff_thrust, digits=0))
three.metric("Thrust to weight", f"{twr:.2f}")
four.metric("First stage's share of Δv", formatter.percent(result.first_stage_share))
five.metric("Payload", formatter.mass(payload, digits=1))

if twr <= 1.0:
    st.error(
        f"**It cannot leave the pad.** Thrust to weight is {twr:.2f}; anything at "
        "or below 1.00 just sits there burning propellant. Add engines or take "
        "mass out.",
        icon="🚫",
    )
elif payload <= 0:
    st.error(
        f"**It cannot reach orbit**, even carrying nothing. It is short by about "
        f"{formatter.mass(-payload, digits=0)} worth of vehicle.",
        icon="📉",
    )
elif twr < 1.2:
    st.warning(
        f"It flies, but only just: a thrust-to-weight of {twr:.2f} means it "
        "climbs slowly and hands a great deal of velocity to gravity. Chapter 3 "
        "shows what that costs.",
        icon="⚠️",
    )
else:
    st.success(
        f"It works, and carries {formatter.mass(payload, digits=1)} to orbit.",
        icon="✅",
    )

if payload > 0:
    rows = mass_components(result)
    st.plotly_chart(
        mass_breakdown(
            [row.label for row in rows],
            as_series(rows),
            formatter=formatter,
            mode=chart_mode,
            title="Your rocket",
            subtitle=f"Payload is {payload / result.liftoff_mass_t:.2%} of what leaves the pad.",
        ),
        width="stretch",
    )

st.divider()
st.subheader("How it stacks up")

board = [
    {
        "name": "★ Yours",
        "liftoff": result.liftoff_mass_t,
        "payload": max(payload, 0.0),
        "fraction": max(payload, 0.0) / result.liftoff_mass_t,
        "share": result.first_stage_share,
    }
]
for key in ("starship_v3", "falcon9_droneship", "saturn_v", "new_glenn", "raptor33_raptor4"):
    other = analyse(lib, key)
    board.append(
        {
            "name": lib.vehicle(key).name,
            "liftoff": other.liftoff_mass_t,
            "payload": other.payload_t,
            "fraction": other.payload_fraction,
            "share": other.first_stage_share,
        }
    )
board.sort(key=lambda row: -row["fraction"])

st.markdown(
    table(
        board,
        [
            Col("name", "Rocket"),
            Col("liftoff", "Liftoff mass", Quantity.MASS, digits=0),
            Col("payload", "Payload", Quantity.MASS, digits=1),
            Col("fraction", "Payload fraction", Quantity.PERCENT, digits=2),
            Col("share", "First stage's share of Δv", Quantity.PERCENT),
        ],
        formatter=formatter,
    )
)
st.caption(
    "Payload fraction is the fairest single measure: how much of what left the "
    "pad turned out to be useful. Anything above 2 % is very good, and anything "
    "above 4 % means you gave up on getting the rocket back."
)

why(
    "What should I actually try?",
    """
Three things, in order.

**Shrink the upper stage.** Take propellant out of it and put it into the first
stage. This is chapter 4's lesson and it is the single biggest lever here.

**Then make the upper stage lighter.** Every tonne comes straight off the
vehicle and lands on the payload, as chapter 7 showed.

**Then change how the booster comes home.** Landing on a ship instead of flying
back frees up a surprising amount, and costs nothing except a slower turnaround.

What will not help much: adding engines. Past a thrust-to-weight of about 1.4
you are mostly carrying engines rather than cargo.
""",
)

try_this(
    "Start from Starship, cut the upper stage's propellant roughly in half, and "
    "add the same amount to the booster. That is the source article's whole "
    "argument in two slider drags. Then untick **Let a smaller stage be lighter** "
    "and watch the payload collapse: a smaller stage only helps if it is also a "
    "lighter one."
)
