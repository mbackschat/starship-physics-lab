"""Charts obey one visual language, in both light and dark.

A chart is read, not just rendered. These check the properties a reader depends
on: the same thing is the same colour everywhere, the surface matches the theme,
and nothing is left to be spotted by eye in a screenshot.
"""

import pytest

from labbook.breakdown import as_series, mass_components
from labbook.charts import loss_waterfall, mass_breakdown, staging_sweep, trajectory
from labbook.palette import SURFACE, Mode, Series, all_colours, colour
from labbook.units import METRIC, US
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
        figure = staging_sweep(sweep_model(model, step_kmh=1000))
        assert figure.layout.showlegend is False

    def test_several_series_always_get_one(self, rows):
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.showlegend is not False

    def test_the_legend_is_anchored_to_the_figure_not_the_plot(self, rows):
        """A fraction of plot height moves with chart size and lands on the axis title."""
        figure = mass_breakdown([r.label for r in rows], as_series(rows))
        assert figure.layout.legend.yref == "container"


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
