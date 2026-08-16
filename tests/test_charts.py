"""Charts obey one visual language, in both light and dark.

A chart is read, not just rendered. These check the properties a reader depends
on: the same thing is the same colour everywhere, the surface matches the theme,
and nothing is left to be spotted by eye in a screenshot.
"""

from typing import ClassVar

import pytest

from labbook.breakdown import as_series, mass_components
from labbook.charts import (
    LEGEND_HINT,
    loss_waterfall,
    mass_breakdown,
    payload_against_dry_mass,
    staging_sweep,
    trajectory,
)
from labbook.palette import AXIS, INK_MUTED, INK_PRIMARY, SURFACE, Mode, Series, all_colours, colour
from labbook.units import METRIC, US, from_kmh
from rocketry.ascent import simulate
from rocketry.library import load
from rocketry.staging import StagingModel
from rocketry.staging import staging_sweep as sweep_model
from rocketry.vehicle import analyse


@pytest.fixture(scope="module")
def rows():
    return mass_components(analyse(load(), "starship_v3"))


@pytest.mark.parametrize("mode", list(Mode))
class TestBothThemes:
    def test_the_surface_matches_the_theme(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.paper_bgcolor == SURFACE[mode]
        assert figure.layout.plot_bgcolor == SURFACE[mode]

    def test_series_wear_their_assigned_colour(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        drawn = {trace.name: trace.marker.color for trace in figure.data}
        for series in (Series.PAYLOAD, Series.PROPELLANT, Series.STRUCTURE, Series.RECOVERY):
            assert drawn[series.label] == colour(series, mode)

    def test_no_two_series_share_a_colour(self, mode):
        values = list(all_colours(mode).values())
        assert len(values) == len(set(values)) or values.count("#898781") == 1

    def test_axis_titles_are_always_present(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.xaxis.title.text


class TestUnitsReachTheCharts:
    def test_axis_label_follows_the_unit_system(self, rows):
        metric = mass_breakdown([r.label for r in rows], as_series(rows), formatter=METRIC)
        imperial = mass_breakdown([r.label for r in rows], as_series(rows), formatter=US)
        assert "(t)" in metric.layout.xaxis.title.text
        assert "(lb)" in imperial.layout.xaxis.title.text

    def test_values_are_converted_not_just_relabelled(self, rows):
        metric = mass_breakdown([r.label for r in rows], as_series(rows), formatter=METRIC)
        imperial = mass_breakdown([r.label for r in rows], as_series(rows), formatter=US)
        assert max(imperial.data[0].x) > 1000 * max(metric.data[0].x) / 1000
        assert max(imperial.data[0].x) == pytest.approx(max(metric.data[0].x) * 2204.62, rel=1e-3)


class TestLegends:
    def test_a_single_series_needs_no_legend_box(self):
        model = StagingModel()
        figure = staging_sweep(sweep_model(model, step=from_kmh(1000)))
        assert figure.layout.showlegend is False

    def test_several_series_always_get_one(self, rows):
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.showlegend is not False

    def test_the_legend_is_anchored_to_the_figure_not_the_plot(self, rows):
        """A fraction of plot height moves with chart size and lands on the axis title."""
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.legend.yref == "container"

    def test_every_chart_that_shows_a_legend_says_it_can_be_clicked(self, rows, flight):
        """The gap was in every chapter at once, so the fix has to be as well.

        Said in `base_layout` rather than chart by chart, because the behaviour
        belongs to Plotly and not to any one figure. A builder that grew its
        own layout would slip out of this silently, which is what this catches.
        """
        built = (
            mass_breakdown([r.label for r in rows], as_series(rows)),
            trajectory(flight.samples),
            loss_waterfall(flight.breakdown),
            payload_against_dry_mass([(80.0, 220.0), (260.0, 40.0)]),
        )
        for figure in built:
            if figure.layout.showlegend is not False:
                assert figure.layout.legend.title.text == LEGEND_HINT

    def test_the_legend_says_it_can_be_clicked(self, rows):
        """Plotly hides a series when its name is clicked, and shows no sign of it.

        Four squares in a row look like a key, not like controls, so the one
        genuinely useful interaction on a stacked chart went unfound. The hint
        belongs on every legend rather than in a caption under one chart,
        because the behaviour is Plotly's and applies to all of them.
        """
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.legend.title.text == LEGEND_HINT

    @pytest.mark.parametrize("mode", list(Mode))
    def test_the_hint_stays_quieter_than_the_series_it_labels(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.legend.title.font.color == INK_MUTED[mode]
        assert figure.layout.legend.title.font.size < figure.layout.font.size

    @pytest.mark.parametrize("mode", list(Mode))
    def test_the_legend_never_paints_its_own_panel(self, rows, mode):
        """Plotly's default legend background is near-white.

        Invisible on the light theme and a glaring slab across the dark one,
        which is how it shipped: a colour nothing set explicitly, so nothing
        checked it in the theme it was wrong in.
        """
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.legend.bgcolor == "rgba(0,0,0,0)"
        assert figure.layout.legend.bordercolor == "rgba(0,0,0,0)"


@pytest.mark.parametrize("mode", list(Mode))
class TestNothingIsLeftForPlotlyToColour:
    """Every panel Plotly draws for itself defaults to near-white.

    Two shipped that way and both were invisible to anyone reading in light
    mode: the legend painted a slab across the dark surface, and the hover
    tooltip put the theme's white text on its own white panel, which made the
    numbers unreadable exactly when a reader went looking for them. They are
    the same defect twice, so they are tested the same way, in both themes.
    """

    def test_the_hover_panel_matches_the_surface(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.hoverlabel.bgcolor == SURFACE[mode]

    def test_the_hover_text_is_readable_against_it(self, rows, mode):
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.hoverlabel.font.color == INK_PRIMARY[mode]
        assert figure.layout.hoverlabel.font.color != figure.layout.hoverlabel.bgcolor

    def test_the_panel_is_separated_from_the_chart_behind_it(self, rows, mode):
        """Same colour as the surface, so without a border it has no edges."""
        figure = mass_breakdown([r.label for r in rows], as_series(rows), mode=mode)
        assert figure.layout.hoverlabel.bordercolor == AXIS[mode]


class TestASweepSaysWhereTheReaderIs:
    """A chart sweeping a value the reader sets has to mark their own setting.

    Chapters 7 and 8 both put a slider above a curve swept across exactly what
    that slider changes, and neither marked the reader's position. The numbers
    above the chart moved, the chart did not, and the two stopped looking like
    they were about the same thing.
    """

    POINTS: ClassVar[list[tuple[float, float]]] = [(m, 300.0 - m) for m in range(80, 261, 5)]
    ARRIVING: ClassVar[list[tuple[float, float]]] = [(m, 300.0) for m in range(80, 261, 5)]

    def test_it_marks_nothing_when_nobody_is_reading(self):
        """A study sweeping the same range for a report has no reader."""
        plain = payload_against_dry_mass(self.POINTS, arriving=self.ARRIVING)
        assert not [trace for trace in plain.data if "yours" in "".join(trace.text or [])]
        assert _verticals(plain) == []

    def test_a_line_ties_the_two_dots_to_one_reading(self):
        marked = payload_against_dry_mass(self.POINTS, arriving=self.ARRIVING, at_t=150.0)
        assert _verticals(marked) == [150.0]

    def test_it_marks_both_curves_at_the_readers_value(self):
        marked = payload_against_dry_mass(self.POINTS, arriving=self.ARRIVING, at_t=150.0)
        dots = [trace for trace in marked.data if trace.mode and "markers" in trace.mode]
        placed = [(trace.x[0], trace.y[0]) for trace in dots]
        assert (150.0, 150.0) in placed, "the payload curve is not marked"
        assert (150.0, 300.0) in placed, "the arriving curve is not marked"

    def test_the_dot_wears_the_colour_of_the_curve_it_sits_on(self):
        """Two dots on two curves are two answers, not a new series."""
        marked = payload_against_dry_mass(self.POINTS, arriving=self.ARRIVING, at_t=150.0)
        by_place = {
            trace.y[0]: trace.marker.color
            for trace in marked.data
            if trace.mode and "markers" in trace.mode
        }
        assert by_place[150.0] == colour(Series.PAYLOAD, Mode.LIGHT)
        assert by_place[300.0] == colour(Series.OTHER, Mode.LIGHT)

    def test_it_follows_the_reader_rather_than_sitting_still(self):
        low = payload_against_dry_mass(self.POINTS, at_t=100.0)
        high = payload_against_dry_mass(self.POINTS, at_t=240.0)
        assert _marked(low) != _marked(high)

    def test_it_converts_like_everything_else(self):
        imperial = payload_against_dry_mass(self.POINTS, at_t=150.0, formatter=US)
        assert _marked(imperial)[0] == pytest.approx(150.0 * 2204.62, rel=1e-3)


def _verticals(figure) -> list[float]:
    """Where the chart draws a vertical line.

    The zero rule is a horizontal line and is always there, so a shape counts
    only when both its ends share an x.

    Args:
        figure: Any chart.

    Returns:
        The x of each vertical line, in draw order.
    """
    return [shape.x0 for shape in figure.layout.shapes if shape.x0 == shape.x1]


def _marked(figure) -> tuple[float, float]:
    """Where a swept chart says the reader is.

    Args:
        figure: A chart built with `at_t`.

    Returns:
        The marked point, in whatever units the chart was drawn in.
    """
    dot = next(trace for trace in figure.data if trace.mode and "text" in trace.mode)
    return (dot.x[0], dot.y[0])


@pytest.fixture(scope="module")
def flight():
    return simulate(analyse(load(), "falcon9_droneship"))


class TestTrajectoryChart:
    def test_it_plots_the_whole_flight_by_default(self, flight):
        figure = trajectory(flight.samples)
        assert len(figure.data[0].x) == len(flight.samples)

    def test_scrubbing_truncates_it(self, flight):
        figure = trajectory(flight.samples, up_to_seconds=60.0)
        assert 0 < len(figure.data[0].x) < len(flight.samples)

    def test_stage_events_are_marked(self, flight):
        events = [(e.name, e.downrange_m, e.altitude_m) for e in flight.events]
        plain = trajectory(flight.samples)
        marked = trajectory(flight.samples, events=events)
        assert len(marked.data) > len(plain.data)


class TestLossWaterfall:
    def test_small_losses_do_not_round_away_to_zero(self):
        flight = simulate(analyse(load(), "falcon9_droneship"))
        figure = loss_waterfall(flight.breakdown)
        names = " ".join(trace.name for trace in figure.data)
        assert "(0%)" not in names, "a real loss must never be labelled zero"

    def test_every_part_of_the_budget_is_drawn(self):
        flight = simulate(analyse(load(), "falcon9_droneship"))
        figure = loss_waterfall(flight.breakdown)
        assert len(figure.data) == len(flight.breakdown)


class TestTheStackReadsLikeAStack:
    """The rows are top-down; the chart was drawing them bottom-up.

    `mass_components` promises "the last stage to fire at the top, the one that
    leaves the pad at the bottom", and a rocket diagram is read that way by
    everybody. Plotly puts the first category on a horizontal bar chart at the
    *bottom*, so the booster was on top and the orbital stage underneath it,
    upside down, with nothing asserting otherwise.
    """

    def test_the_first_row_is_drawn_at_the_top(self, rows):
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.yaxis.autorange == "reversed"

    def test_the_labels_keep_the_order_they_were_given(self, rows):
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        for trace in figure.data:
            assert list(trace.y) == [r.label for r in rows]
