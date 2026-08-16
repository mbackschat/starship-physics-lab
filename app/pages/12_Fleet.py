"""Chapter 12: every rocket in the library, on one page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.shell import (
    chapter_footer,
    chapter_link,
    library,
    mode,
    modelling_note,
    page,
    reset_button,
    sidebar,
    try_this,
    why,
)

from labbook.breakdown import as_series, mass_components
from labbook.catalog import browse
from labbook.charts import mass_breakdown, trajectory
from labbook.fleet import (
    CORE_COLUMNS,
    EXTRA_COLUMNS,
    FleetRow,
    fleet,
    in_groups,
    matching,
)
from labbook.tables import Col, table
from labbook.visuals import rocket_cutaway
from rocketry.ascent import AscentResult, simulate
from rocketry.vehicle import analyse

page("12 · Fleet data", "Every rocket this project models, and how it flies, in one table.")
formatter = sidebar()
chart_mode = mode()
lib = library()

st.markdown(
    """
Each row is a whole launch: the vehicle is analysed, solved for payload, then
flown from the pad to engine cutoff. **Every number on this page is computed
from [`data/`](https://github.com/mbackschat/starship-physics-lab/tree/main/data),
not typed in**, which is why the modelled payload and the operator's claim can
disagree in front of you.
"""
)


@st.cache_data(show_spinner="Flying every rocket in the library…")
def rows() -> list[FleetRow]:
    """Every vehicle, flown. Cached: this runs a full ascent simulation each.

    Returns:
        One row per vehicle that publishes a payload.
    """
    return fleet(library())


@st.cache_data(show_spinner=False)
def flight(key: str) -> AscentResult:
    """Fly one vehicle, for the diagram below the table.

    Kept apart from `rows` so picking a vehicle does not re-fly the fleet, and
    so the table does not have to carry a few hundred samples per row it never
    shows.

    Args:
        key: Vehicle key.

    Returns:
        Its ascent.
    """
    return simulate(analyse(library(), key))


GROUPS = browse(lib)

by_text, by_group = st.columns([1, 1.4], gap="large")

with by_text:
    query = st.text_input(
        "Filter",
        key="c12.filter",
        placeholder="falcon, nasa, concept, starship…",
        help="Matches the name, the operator, the kind, and the library key.",
    )
    everything = st.toggle(
        "Show every column",
        key="c12.columns",
        help=(
            "The full ascent breakdown: where the velocity went, how high it "
            "staged, what the air did to it, and what the model cannot "
            "represent about it."
        ),
    )

with by_group:
    chosen = st.multiselect(
        "Groups",
        key="c12.groups",
        options=[group.name for group in GROUPS],
        help="The same grouping the vehicle pickers use. None ticked means all of them.",
    )
    # Drawn here, filled in once the vehicle picker further down exists: a
    # reset button can only restore a control it has already seen.
    reset_slot = st.container()
    for group in GROUPS:
        if group.name in chosen and group.hint:
            st.caption(group.hint)

columns: list[Col] = [*CORE_COLUMNS, *EXTRA_COLUMNS] if everything else list(CORE_COLUMNS)
shown = matching(in_groups(rows(), [g for g in GROUPS if g.name in chosen]), query)

if not shown:
    st.info(
        "Nothing matches that. Try a shorter word, clear the box, or untick a group.",
        icon="🔍",
    )
else:
    st.markdown(table(shown, columns), unsafe_allow_html=False)
    st.caption(
        f"{len(shown)} of {len(rows())} vehicles. "
        "Payload modelled is solved against a 9,404 m/s mission budget. "
        "Speed at cutoff comes from the flown simulation, so it is what is left "
        "after gravity, air and steering have taken their cut."
    )

def naming(rows: list[FleetRow], singular: str, plural: str) -> str:
    """Name some vehicles in bold, with a verb that agrees with how many.

    One row is the common case here, and "Saturn V are still descending" is the
    kind of sentence that makes a reader trust the numbers less.

    Args:
        rows: The vehicles to name.
        singular: Sentence remainder when there is exactly one.
        plural: Sentence remainder otherwise.

    Returns:
        Markdown ready for a callout.
    """
    names = ", ".join(row.name for row in rows)
    return f"**{names}** {singular if len(rows) == 1 else plural}"


SHORTFALL = (
    " when the engines stop, so the budget is short of the orbit this model aims "
    "at. That is the model's honest answer, not a display bug."
)

falling = [row for row in shown if row.climb_rate_ms < -100]
if falling:
    st.warning(
        naming(falling, "is still descending", "are still descending") + SHORTFALL,
        icon="📉",
    )

limited = [row for row in shown if row.limits]
if limited:
    st.info(
        naming(
            limited,
            "is not modelled exactly as it flies. Read that row as a shape rather "
            "than as a figure.",
            "are not modelled exactly as they fly. Read those rows as shapes rather "
            "than as figures.",
        ),
        icon="🧮",
    )

st.divider()

st.subheader("One of them, close up")

if shown:
    picked = st.selectbox(
        "Vehicle",
        key="c12.vehicle",
        options=[row.key for row in shown],
        help="Which vehicle the flight path and mass breakdown below describe.",
        format_func=lambda key: lib.vehicle(key).name,
        label_visibility="collapsed",
    )
    row = next(entry for entry in shown if entry.key == picked)
    result = flight(picked)
    analysis = analyse(lib, picked)

    modelling_note(lib.vehicle(picked))

    figures, drawing = st.columns([3, 1], gap="large")

    with figures:
        one, two, three, four = st.columns(4)
        one.metric("On the pad", formatter.mass(row.liftoff_t, digits=0))
        two.metric("Payload modelled", formatter.mass(row.payload_solved_t, digits=1))
        three.metric("Speed at cutoff", formatter.velocity(row.cutoff_speed_ms, digits=0))
        four.metric("Lost to losses", formatter.percent(row.loss_fraction))

        st.plotly_chart(
            trajectory(
                result.samples,
                events=[
                    (event.name, event.downrange_m, event.altitude_m)
                    for event in result.events
                ],
                formatter=formatter,
                mode=chart_mode,
                title=f"{row.name}: the path it flies",
                subtitle=(
                    "Height against distance downrange. Almost all of the work is "
                    "sideways, which is why the line flattens so early."
                ),
            ),
            width="stretch",
        )

        parts = mass_components(analysis)
        st.plotly_chart(
            mass_breakdown(
                [part.label for part in parts],
                as_series(parts),
                formatter=formatter,
                mode=chart_mode,
                title="What it is made of, stage by stage",
                subtitle=(
                    "Read it like the rocket: the top bar reaches orbit, the "
                    "bottom one leaves the pad. Payload is the blue sliver."
                ),
            ),
            width="stretch",
        )

    with drawing:
        # Everything in the tanks counts as propellant here, including what a
        # returning stage holds back: the drawing is about what the vehicle is
        # made of, not about what it spends going up.
        loaded = sum(entry.stage.propellant_t for entry in analysis.stages)
        st.caption("**The whole stack**, filled to show how much of it is propellant.")
        st.markdown(
            rocket_cutaway(
                dry_t=row.liftoff_t - loaded,
                propellant_t=loaded,
                mode=chart_mode,
                formatter=formatter,
                height=340,
                uid=f"fleet-{picked}",
            ),
            unsafe_allow_html=True,
        )

with reset_slot:
    reset_button("c12.filter", "c12.columns", "c12.groups", "c12.vehicle")

st.divider()

why(
    "Why does the modelled payload disagree with the claim?",
    """
Because the claim is what is being tested, not what is being assumed.

Every row solves the same question the same way: hold the mission fixed at the
velocity it takes to reach low Earth orbit, and ask what payload the vehicle can
carry to it. Where that lands within a few per cent of the published figure, the
method is working. Where it does not, the reason is worth knowing rather than
hiding.

Three reasons show up here. A vehicle whose boosters burn **alongside** the core
is flown as a sequence of stages and comes out flattered. A vehicle flying an
unusually flat or unusually lofted trajectory does not match a single mission
budget. And Starship's own row rests on a dry mass nobody has published, which
is the whole subject of the case study.
""",
)

why(
    "Why is speed at cutoff below orbital velocity for almost everything?",
    """
Because the simulation stops when the propellant does, and a real flight does
not have to.

Reaching orbit needs about 7,800 m/s at 200 km. Several rows land a few hundred
short, and that gap is real rather than cosmetic: it is the same few per cent by
which this model's payloads differ from the published ones. Read the column as a
comparison between vehicles, which it is good at, rather than as a verdict on
whether a particular rocket reaches orbit, which it is not.
""",
)

try_this(
    "Turn on every column and sort your eye down the gravity column. The vehicles "
    "that lose the most are the ones with the least thrust for their weight: they "
    "spend longer holding themselves up, and pay for every second of it."
)

chapter_link(3)

chapter_footer(12)
