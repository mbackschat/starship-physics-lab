"""Chapter 4: why throw half the rocket away, and where to do it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import library, mode, page, sidebar, try_this, why

from labbook.charts import staging_sweep
from labbook.tables import Col, table
from labbook.units import Quantity
from rocketry.staging import StagingModel, optimal_delta_v_split, optimal_staging_speed
from rocketry.staging import staging_sweep as sweep_model
from rocketry.vehicle import analyse

page("4 · Stages", "Where the stages separate is worth a factor of two in payload.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
A single-stage rocket carries its empty tanks all the way to orbit. Staging
throws them away halfway, which resets the mass ratio and is the only reason
orbit is reachable at all.

But *where* you separate is a real choice, and it turns out to matter enormously.
"""
)


@st.cache_data(show_spinner=False)
def sweep(shape: float, entry_speed: float) -> list[tuple[float, float]]:
    """Payload against staging speed, cached so the slider stays responsive.

    Args:
        shape: Upper stage inert mass per tonne of its propellant.
        entry_speed: Speed the booster must slow to before reentry, km/h.

    Returns:
        Pairs of staging speed in km/h and payload in tonnes.
    """
    model = StagingModel(ship_inert_per_propellant=shape, entry_speed_kmh=entry_speed)
    return sweep_model(model, low_kmh=6000, high_kmh=16000, step_kmh=250)


controls, chart = st.columns([1, 2.4], gap="large")

with controls:
    st.markdown("#### The rocket stays the same")
    st.caption(
        "5,850 tonnes on the pad every time, the same engines, the same mission. "
        "Only the speed at which the two stages separate changes."
    )
    inert = st.slider(
        "Upper stage weight",
        min_value=0.10,
        max_value=0.22,
        value=250.0 / 1600.0,
        step=0.005,
        format="%.3f",
        help=(
            "Tonnes of upper stage, including its landing propellant, per tonne "
            "of propellant it carries. Lower means a better-built stage."
        ),
    )
    entry_speed = st.slider(
        "Speed the booster can survive reentry at",
        min_value=4000.0,
        max_value=9000.0,
        value=5300.0,
        step=100.0,
        format="%.0f km/h",
        help=(
            "Faster means less braking propellant, which frees the booster to "
            "stage later. Better heat shielding buys this directly."
        ),
    )

curve = sweep(inert, entry_speed)
model = StagingModel(ship_inert_per_propellant=inert, entry_speed_kmh=entry_speed)
best = optimal_staging_speed(model)
as_flown = model.payload_at(6000.0)
at_best = model.payload_at(best)

with chart:
    one, two, three = st.columns(3)
    one.metric("Best staging speed", formatter.speed(best, digits=0))
    two.metric("Payload there", formatter.mass(at_best, digits=0))
    three.metric(
        "Starship's actual split",
        formatter.mass(as_flown, digits=0),
        delta=f"{as_flown - at_best:,.0f} t",
    )
    st.plotly_chart(
        staging_sweep(
            curve,
            markers=[
                ("Starship as flown", 6000.0, model.payload_at(6000.0)),
                ("Falcon 9's split", 8000.0, model.payload_at(8000.0)),
                ("Article's redesign", 10000.0, model.payload_at(10000.0)),
            ],
            formatter=formatter,
            mode=chart_mode,
            title="Same rocket, different staging speed",
            subtitle=(
                "Everything is held constant except where the stages part company. "
                "Diamonds mark real and proposed vehicles."
            ),
        ),
        width="stretch",
    )

st.divider()

st.subheader("How real rockets divide the work")

rows = []
for key in ("starship_v3", "falcon9_droneship", "ariane_64", "space_shuttle", "raptor33_raptor4"):
    vehicle = lib.vehicle(key)
    result = analyse(lib, key)
    rows.append(
        {
            "name": ("★ " if vehicle.in_article else "") + vehicle.name,
            "share": result.first_stage_share,
            "staging": vehicle.staging_speed_kmh or None,
            "payload": result.payload_t,
        }
    )
rows.append({"name": "Theory, for two identical stages", "share": 0.5, "staging": None,
             "payload": None})

st.markdown(
    table(
        rows,
        [
            Col("name", "Vehicle"),
            Col("share", "First stage's share of Δv", Quantity.PERCENT),
            Col("staging", "Staging speed", Quantity.SPEED),
            Col("payload", "Payload", Quantity.MASS, digits=1),
        ],
        formatter=formatter,
    )
)

split = optimal_delta_v_split(isp=350, structural_coefficient=0.08, total_delta_v=9404)
st.caption(
    f"For two stages built the same way and using the same engines, payload peaks "
    f"at a {split:.0%} split. Every real rocket sits well below that, and Starship "
    "sits lowest of all."
)

why(
    "Why is an even split best?",
    """
Because the cost of speed is exponential, and exponential costs punish
concentration.

Asking one stage to do most of the work means that stage needs a huge mass
ratio, and mass ratio is what gets expensive fastest. Splitting the job evenly
keeps both mass ratios modest, and two modest mass ratios multiply to less mass
than one enormous one.

Real rockets skew below an even split for two honest reasons: first stages use
less efficient sea-level engines, and a reusable first stage has to keep
propellant back. Both argue for the first stage doing slightly less. Neither
explains dropping to 30 %.
""",
)

why(
    "So why does the curve come back down at the far end?",
    """
Because a booster that stages at 15,000 km/h has to survive coming home from
15,000 km/h.

Everything it does not spend on the payload it spends on braking, and that
braking propellant grows exponentially too. Push far enough and the booster is
carrying more propellant for itself than for the mission.

The peak is where those two exponentials balance. Notice how flat it is: you do
not have to hit it exactly, you just have to be somewhere near it.
""",
)

try_this(
    "Drag the reentry speed slider to the right. A booster with better heat "
    "shielding can stage later without paying for as much braking, and the whole "
    "curve shifts. This is the single change that would help Starship most."
)
