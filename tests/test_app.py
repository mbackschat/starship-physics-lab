"""The Streamlit pages must actually run, not merely import.

Uses Streamlit's own headless harness. These are smoke tests with teeth: they
execute each page top to bottom the way a browser session would, so a broken
widget or a bad library lookup fails here rather than in front of a reader.

Every page is reached by starting the real app and navigating, rather than by
running the page file on its own. A page run in isolation is the only page the
app knows about, so its links to other chapters have nothing to resolve against
and raise. That is an artefact of the harness and not of the product, and
booting properly removes it while also covering the links themselves.
"""

import ast
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from labbook.units import UnitSystem
from rocketry.library import load
from rocketry.reuse import RecoveryProfile

APP = Path(__file__).resolve().parents[1] / "app"

# The pages reach their shared components the same way, and the reset button's
# key has to come from the one place that sets it: a copy here would go stale
# silently, leaving these tests clicking a button that no longer exists.
sys.path.insert(0, str(APP))

from components.shell import RESET_KEY  # noqa: E402

ENTRYPOINT = APP / "Home.py"
PAGES = sorted(APP.glob("pages/*.py"))


def boot(path: Path) -> AppTest:
    """Start the app at a given chapter, without running it yet.

    Args:
        path: The page file to land on.

    Returns:
        The harness, ready for query parameters to be set before it runs.
    """
    app = AppTest.from_file(str(ENTRYPOINT), default_timeout=60)
    if path != ENTRYPOINT:
        app.switch_page(f"pages/{path.name}")
    return app


def run(path: Path) -> AppTest:
    """Start the app at a given chapter and run it.

    Args:
        path: The page file to land on.

    Returns:
        The harness, having rendered that page.
    """
    app = boot(path)
    app.run()
    return app


def test_home_runs():
    app = run(ENTRYPOINT)
    assert not app.exception
    assert any("Starship Physics Lab" in block.value for block in app.title)


def test_every_page_is_discovered():
    assert len(PAGES) >= 2


@pytest.mark.parametrize("path", [*PAGES, ENTRYPOINT], ids=lambda p: p.stem)
def test_no_page_prints_a_docstring_at_the_reader(path: Path):
    """Streamlit's magic renders a bare string expression as page content.

    The rest of the project documents a module-level constant with a docstring
    underneath it, which is an expression statement and therefore lands on the
    page as a stray paragraph. It reads as a bug to everyone except the person
    who wrote it, and nothing else catches it: the page runs perfectly.
    """
    body = ast.parse(path.read_text()).body
    stray = [
        node.lineno
        for index, node in enumerate(body)
        if index != 0
        and isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    assert not stray, f"{path.name} would print a bare string at lines {stray}; use #"


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.stem)
def test_page_runs(path: Path):
    app = run(path)
    assert not app.exception, f"{path.name} raised: {app.exception}"
    assert app.title, f"{path.name} rendered no title"


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.stem)
def test_page_offers_the_unit_toggle(path: Path):
    app = run(path)
    assert app.sidebar.radio, f"{path.name} has no unit toggle"


def test_rocket_equation_responds_to_its_sliders():
    app = run(APP / "pages" / "1_Rocket_equation.py")
    before = app.metric[0].value
    app.slider[1].set_value(500.0).run()
    assert not app.exception
    assert app.metric[0].value != before, "more propellant must mean more speed"


def test_launch_says_what_it_cannot_represent_about_a_vehicle():
    """Design rule 5: no dead ends, and no unlabelled distortions either.

    The Space Shuttle used to hand the reader a traceback, because its boosters
    named a placeholder engine and the resulting thrust-to-weight of 0.19 made
    `simulate()` refuse. With a real solid motor in the library it flies, and the
    remaining distortion is the one nothing can fix by better data: its boosters
    and its main engines burn together, and this model walks a stack one stage at
    a time. Flying it silently would be worse than refusing it.
    """
    app = run(APP / "pages" / "3_Launch.py")
    app.selectbox[0].set_value("space_shuttle").run()
    assert not app.exception, "picking a vehicle must never show a traceback"
    said = " ".join(element.value for element in app.info)
    assert "alongside" in said, "a vehicle the model misrepresents must say so"
    assert "too high" in said, "and must say which way the error goes"


def test_launch_stays_quiet_about_a_vehicle_it_models_honestly():
    app = run(APP / "pages" / "3_Launch.py")
    app.selectbox[0].set_value("falcon9_droneship").run()
    assert not any("alongside" in element.value for element in app.info)


@pytest.mark.parametrize(
    "key",
    [key for key, vehicle in load().vehicles.items() if vehicle.payload_leo_t is not None],
)
def test_every_vehicle_on_offer_can_be_selected_without_crashing(key: str):
    app = run(APP / "pages" / "3_Launch.py")
    app.selectbox[0].set_value(key).run()
    assert not app.exception, f"{key} raised in the launch chapter: {app.exception}"


def test_anatomy_switches_vehicle():
    app = run(APP / "pages" / "2_Anatomy.py")
    liftoff_starship = app.metric[0].value
    app.selectbox[0].set_value("falcon9_droneship").run()
    assert not app.exception
    assert app.metric[0].value != liftoff_starship


def test_units_toggle_changes_what_is_displayed():
    app = run(APP / "pages" / "2_Anatomy.py")
    metric_before = app.metric[0].value
    app.sidebar.radio[0].set_value(UnitSystem.US).run()
    assert not app.exception
    assert app.metric[0].value != metric_before
    assert "lb" in app.metric[0].value


def test_stages_page_responds_to_the_upper_stage_weight():
    """A lighter upper stage must move the optimum and the payload."""
    app = run(APP / "pages" / "4_Stages.py")
    before = app.metric[1].value
    app.slider[0].set_value(0.10).run()
    assert not app.exception
    assert app.metric[1].value != before


def test_stages_page_shows_the_optimum_far_above_starships_split():
    app = run(APP / "pages" / "4_Stages.py")
    best = app.metric[0].value
    assert "km/h" in best
    assert int(best.split()[0].replace(",", "")) > 9000


def test_reuse_page_switches_recovery_mode():
    app = run(APP / "pages" / "5_Reuse.py")
    droneship_reserve = app.metric[0].value
    app.radio[0].set_value(RecoveryProfile.RTLS).run()
    assert not app.exception
    assert app.metric[0].value != droneship_reserve


def test_reuse_page_says_expendable_holds_nothing_back():
    app = run(APP / "pages" / "5_Reuse.py")
    app.radio[0].set_value(RecoveryProfile.EXPENDABLE).run()
    assert not app.exception
    assert app.metric[0].value.startswith("0 ")


def test_flying_back_costs_more_than_landing_on_a_ship():
    app = run(APP / "pages" / "5_Reuse.py")
    app.radio[0].set_value(RecoveryProfile.DRONESHIP).run()
    ship = float(app.metric[0].value.split()[0].replace(",", ""))
    app.radio[0].set_value(RecoveryProfile.RTLS).run()
    home = float(app.metric[0].value.split()[0].replace(",", ""))
    assert home > ship


def test_sandbox_builds_a_working_rocket_by_default():
    app = run(APP / "pages" / "9_Build_your_own.py")
    assert not app.exception
    twr = float(app.metric[2].value)
    assert twr > 1.0


def test_sandbox_refuses_a_rocket_that_cannot_leave_the_pad():
    """Cutting the engines down must produce a clear refusal, not a silent number."""
    app = run(APP / "pages" / "9_Build_your_own.py")
    app.slider[2].set_value(11).run()
    assert not app.exception
    assert float(app.metric[2].value) < 1.0
    assert app.error, "a rocket with too little thrust must say so"


def test_sandbox_rewards_shrinking_the_upper_stage():
    """The article's whole argument, reachable in two slider drags.

    Only true because a smaller stage is also allowed to be a lighter one. That
    is the default, and this test is what guarantees it stays the default.
    """
    app = run(APP / "pages" / "9_Build_your_own.py")
    before = float(app.metric[4].value.split()[0].replace(",", ""))
    app.slider[3].set_value(900.0).run()   # upper stage propellant
    app.slider[0].set_value(4300.0).run()  # booster propellant
    after = float(app.metric[4].value.split()[0].replace(",", ""))
    assert after > before, "shrinking the upper stage should pay off"


def test_sandbox_shows_the_trap_when_a_smaller_stage_is_not_lighter():
    """Untick the scaling and the same change becomes a bad one."""
    app = run(APP / "pages" / "9_Build_your_own.py")
    app.checkbox[0].set_value(False).run()
    before = float(app.metric[4].value.split()[0].replace(",", ""))
    app.slider[3].set_value(900.0).run()   # upper stage propellant
    after = float(app.metric[4].value.split()[0].replace(",", ""))
    assert after < before


def test_payload_page_reads_its_state_from_the_url():
    """A shared link must land the next reader on the same number."""
    app = boot(APP / "pages" / "7_The_payload_question.py")
    app.query_params["dry"] = "165"
    app.run()
    assert not app.exception
    assert app.metric[1].value.startswith("165")


def test_payload_page_survives_a_hand_edited_url():
    """The URL is the one input a reader can type into. It must not break the page."""
    for junk in ("rubbish", "", "-40", "99999"):
        app = boot(APP / "pages" / "7_The_payload_question.py")
        app.query_params["dry"] = junk
        app.run()
        assert not app.exception, f"query dry={junk!r} broke the page"


def _param(app: AppTest, key: str) -> str:
    """Read one query parameter.

    AppTest hands them back as lists where the live app gives strings, so both
    shapes are accepted here rather than in the code under test.

    Args:
        app: The running app.
        key: Parameter name.

    Returns:
        The value.
    """
    value = app.query_params[key]
    return value[0] if isinstance(value, list) else value


def test_moving_the_slider_updates_the_shareable_url():
    app = run(APP / "pages" / "7_The_payload_question.py")
    app.slider[0].set_value(160).run()
    assert _param(app, "dry") == "160"


def test_the_url_and_the_slider_never_disagree():
    app = run(APP / "pages" / "7_The_payload_question.py")
    for value in (100, 165, 240):
        app.slider[0].set_value(value).run()
        assert _param(app, "dry") == str(value)
        assert app.metric[1].value.startswith(str(value))


def test_reset_leaves_the_unit_choice_alone():
    """It resets the page's controls, not the reader's settings."""
    app = run(APP / "pages" / "1_Rocket_equation.py")
    app.radio[0].set_value(UnitSystem.US).run()
    app.button(key=RESET_KEY).click().run()
    assert app.radio[0].value is UnitSystem.US


NO_RESET = {"2_Anatomy", "10_Fact_check", "11_Glossary"}
"""Pages where a general reset would be noise.

Chapter 2 has only the vehicle picker and chapter 10 has no controls at all. A
button to undo a single dropdown is clutter, not a kindness. The glossary has
one control and already offers "Show all" beside it, which is the same idea
worded for what it actually does.
"""


RESETTABLE = [p for p in PAGES if p.stem not in NO_RESET]


@pytest.mark.parametrize("path", RESETTABLE, ids=lambda p: p.stem)
def test_every_page_with_controls_offers_a_reset(path: Path):
    assert "reset_button(" in path.read_text(), f"{path.stem} has controls but no way back"


# The unit system is a reader setting rather than one of the page's controls,
# and a reset deliberately leaves it alone. `test_reset_leaves_the_unit_choice_alone`
# is what holds that. The radio is excluded here for a second reason too: its
# options arrive formatted for display, so nothing generic can name another one
# to select. Chapter 5's is moved by hand in the tests above.
SETTINGS = {"unit_system"}


def movable(app: AppTest) -> list:
    """Every control on the page a reader can move.

    Args:
        app: A rendered page.

    Returns:
        The widgets, in the order the page draws them. Disabled ones are left
        out: the sandbox greys out the ship's empty weight while it is being
        scaled automatically, and a control the reader cannot move is not one
        a reset has to put back.
    """
    everything = [
        *app.slider,
        *app.selectbox,
        *app.checkbox,
        *app.toggle,
        *app.multiselect,
        *app.text_input,
    ]
    return [
        widget
        for widget in everything
        if widget.key and widget.key not in SETTINGS and not widget.disabled
    ]


def move(widget) -> None:
    """Put one control somewhere other than where it is sitting.

    Args:
        widget: The control to move.
    """
    match widget.type:
        case "slider":
            widget.set_value(widget.min if widget.value == widget.max else widget.max)
        case "selectbox":
            widget.select_index((widget.index + 1) % len(widget.options))
        case "checkbox" | "toggle":
            widget.set_value(not widget.value)
        case "multiselect":
            # Sound only because this app's multiselect options are plain
            # strings: the harness reports options already formatted for
            # display, and selecting needs the underlying value.
            widget.set_value([] if widget.value else [widget.options[0]])
        case "text_input":
            widget.set_value("" if widget.value else "a")
        case _:
            raise AssertionError(f"no way to move a {widget.type} is defined")


def positions(app: AppTest) -> dict[str, object]:
    """Where every control on the page currently sits.

    Args:
        app: A rendered page.

    Returns:
        Control key to current value.
    """
    return {widget.key: widget.value for widget in movable(app)}


@pytest.mark.parametrize("path", RESETTABLE, ids=lambda p: p.stem)
def test_reset_puts_every_moved_control_back(path: Path):
    """A reader who has moved four sliders had no way back except reloading.

    Reloading also loses the chapter, so people were cautious with the controls,
    which is the opposite of what this app is for.

    Every control is moved in turn rather than only the first, because the
    failure this catches is a reset button drawn *above* one of the controls it
    names. It cannot remember a starting value for a control it has not met
    yet, so what it eventually records is the reader's value rather than the
    page's, and that one control then resets to wherever the reader first put
    it. Checking a single control would leave the rest of the page unguarded.

    One at a time and **on a freshly loaded page each time**, which is what
    makes this catch anything. Moving the controls in sequence on one page lets
    an earlier move warm the record up with the right starting values, and the
    page then passes while still being broken for the reader whose *first*
    action is the control drawn below the button. So each control is treated as
    the first thing this reader touched. One at a time also keeps the states
    reachable: filtering the fleet down to one rocket while selecting a
    different rocket is not something a reader can do.

    The other half of this feature is beyond any harness that does not open a
    browser, and is checked in `deploy/acceptance.py`. Restoring the value
    Python holds does not by itself move the slider the reader is looking at.
    """
    started = positions(run(path))
    assert started, f"{path.stem} offers a reset but has no control to check it with"

    for key in started:
        app = run(path)
        move(next(widget for widget in movable(app) if widget.key == key))
        app.run()
        assert not app.exception, f"{path.stem} raised on moving {key}: {app.exception}"
        assert positions(app) != started, f"{key} did not move"

        app.button(key=RESET_KEY).click().run()
        assert not app.exception, f"{path.stem} raised on reset: {app.exception}"
        assert positions(app) == started, f"{key} did not come back"


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.stem)
def test_every_control_explains_itself(path: Path):
    """The (?) tooltip is the only place a control can say what it means.

    A slider labelled "Propellant" tells a beginner nothing about what moving it
    will do, and the page has no room to explain each one in prose.
    """
    widgets = {
        "slider", "select_slider", "selectbox", "radio", "checkbox", "toggle",
        "multiselect", "text_input", "number_input",
    }
    tree = ast.parse(path.read_text())
    missing = [
        f"line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in widgets
        and "help" not in {kw.arg for kw in node.keywords}
    ]
    assert missing == [], f"{path.stem} has controls with no tooltip: {missing}"
