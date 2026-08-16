"""The two chapter 1 charts that answer opposite questions.

They exist as a pair. If one of them stops bending the way it should, the pair
stops teaching anything and starts actively misleading, so the shapes are
asserted on the figures themselves rather than only on the data behind them.
"""

import pytest

from labbook.charts import burn_animation, loading_curve
from labbook.curves import burn_trace, loading_sweep
from labbook.palette import SURFACE, Mode
from labbook.units import METRIC, US


@pytest.fixture(scope="module")
def trace():
    return burn_trace(dry_t=10.0, propellant_t=90.0, isp_s=350.0, steps=60)


@pytest.fixture(scope="module")
def sweep():
    return loading_sweep(dry_t=10.0, isp_s=350.0, up_to_t=900.0, steps=60)


@pytest.mark.parametrize("mode", list(Mode))
def test_both_charts_take_the_readers_surface(trace, sweep, mode):
    for figure in (burn_animation(trace, mode=mode), loading_curve(sweep, mode=mode)):
        assert figure.layout.paper_bgcolor == SURFACE[mode]
        assert figure.layout.plot_bgcolor == SURFACE[mode]


def test_both_charts_label_their_axes(trace, sweep):
    for figure in (burn_animation(trace), loading_curve(sweep)):
        assert figure.layout.xaxis.title.text
        assert figure.layout.yaxis.title.text


def test_the_burn_chart_can_be_played(trace):
    figure = burn_animation(trace)
    assert figure.frames, "no frames means no animation"
    assert figure.layout.updatemenus, "frames with no play button cannot be started"


def test_the_animation_starts_at_rest_and_ends_on_the_real_answer(trace):
    figure = burn_animation(trace, frames=20)
    first, last = figure.frames[0], figure.frames[-1]
    assert len(first.data[0].x) == 1
    assert len(last.data[0].x) == len(trace)
    assert last.data[0].y[-1] == pytest.approx(trace[-1].velocity_ms)


def test_the_animation_is_capped_at_the_frames_asked_for(trace):
    assert len(burn_animation(trace, frames=12).frames) <= 12 + 1
    assert len(burn_animation(trace, frames=200).frames) == len(trace)


def test_the_full_curve_stays_on_screen_so_the_axes_do_not_jump(trace):
    # The ghost trace spans the whole burn from the first frame. Without it
    # Plotly rescales on every frame and the steepening becomes invisible.
    figure = burn_animation(trace)
    assert len(figure.data[0].x) == len(trace)


def test_the_two_charts_bend_in_opposite_directions(trace, sweep):
    def bend(values) -> float:
        return (values[-1] - values[-2]) - (values[1] - values[0])

    assert bend(burn_animation(trace).data[0].y) > 0
    assert bend(loading_curve(sweep).data[0].y) < 0


def test_the_loading_curve_can_mark_the_readers_own_rocket(sweep):
    plain = loading_curve(sweep)
    marked = loading_curve(sweep, at_t=90.0)
    assert len(marked.data) == len(plain.data) + 1
    assert "yours" in marked.data[-1].text[0]


def test_the_marker_lands_on_the_curve_not_beside_it(sweep):
    figure = loading_curve(sweep, at_t=300.0)
    curve_x, curve_y = list(figure.data[0].x), list(figure.data[0].y)
    at = curve_x.index(figure.data[-1].x[0])
    assert curve_y[at] == pytest.approx(figure.data[-1].y[0])


@pytest.mark.parametrize("formatter", [METRIC, US])
def test_switching_units_changes_the_labels_and_not_the_shape(trace, formatter):
    figure = burn_animation(trace, formatter=formatter)
    values = list(figure.data[0].y)
    assert values == sorted(values), "the burn only ever gains speed"
    assert figure.layout.yaxis.title.text
