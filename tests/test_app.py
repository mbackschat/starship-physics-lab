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
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from labbook.units import UnitSystem
from rocketry.reuse import RecoveryProfile

APP = Path(__file__).resolve().parents[1] / "app"
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
