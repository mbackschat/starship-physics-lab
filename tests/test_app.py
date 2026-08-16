"""The Streamlit pages must actually run, not merely import.

Uses Streamlit's own headless harness. These are smoke tests with teeth: they
execute each page top to bottom the way a browser session would, so a broken
widget or a bad library lookup fails here rather than in front of a reader.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from labbook.units import UnitSystem

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = sorted(APP.glob("pages/*.py"))


def run(path: Path) -> AppTest:
    app = AppTest.from_file(str(path), default_timeout=60)
    app.run()
    return app


def test_home_runs():
    app = run(APP / "Home.py")
    assert not app.exception
    assert any("Starship Physics Lab" in block.value for block in app.title)


def test_every_page_is_discovered():
    assert len(PAGES) >= 2


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
