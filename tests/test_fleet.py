"""Every vehicle in the library, on one page, computed once.

The numbers behind this table were only ever visible by writing a throwaway
script. Two consumers now share the same rows, which is the point: a figure in
the app and a figure in a study must not be able to disagree.
"""

import pytest

from labbook.catalog import browse
from labbook.fleet import (
    CORE_COLUMNS,
    EXTRA_COLUMNS,
    FleetRow,
    fleet,
    in_groups,
    matching,
)
from labbook.tables import table
from rocketry.library import load


@pytest.fixture(scope="module")
def lib():
    return load()


@pytest.fixture(scope="module")
def rows(lib):
    return fleet(lib)


@pytest.fixture(scope="module")
def groups(lib):
    return browse(lib)


class TestTheRows:
    def test_every_vehicle_with_a_claim_appears(self, lib, rows):
        expected = {key for key, v in lib.vehicles.items() if v.payload_leo_t is not None}
        assert {row.key for row in rows} == expected

    def test_they_come_out_in_a_stable_order(self, lib):
        assert [row.key for row in fleet(lib)] == [row.key for row in fleet(lib)]

    def test_the_calibration_reference_reads_right(self, rows):
        falcon9 = next(row for row in rows if row.key == "falcon9_droneship")
        assert falcon9.liftoff_t == pytest.approx(544, rel=0.02)
        assert falcon9.payload_claimed_t == 17.5
        assert 50 < falcon9.staging_altitude_km < 100
        assert 7000 < falcon9.cutoff_speed_ms < 8200
        assert not falcon9.crashed

    def test_a_vehicle_that_never_stages_has_no_staging_figures(self, lib):
        # Nothing in the library today, but the row must not invent one.
        row = next(row for row in fleet(lib) if row.key == "falcon9_droneship")
        assert row.staging_speed_ms is not None

    def test_losses_add_up_to_what_the_engines_produced(self, rows):
        for row in rows:
            total = row.cutoff_speed_ms + row.gravity_loss + row.drag_loss + row.steering_loss
            assert total == pytest.approx(row.ideal_delta_v, rel=1e-3), row.key

    def test_it_carries_the_modelling_limits_across(self, rows):
        shuttle = next(row for row in rows if row.key == "space_shuttle")
        assert "boosters" in shuttle.limits.lower()
        falcon9 = next(row for row in rows if row.key == "falcon9_droneship")
        assert falcon9.limits == ""


class TestFiltering:
    def test_an_empty_query_keeps_everything(self, rows):
        assert matching(rows, "") == rows

    def test_it_matches_the_name(self, rows):
        found = matching(rows, "falcon")
        assert found
        assert all("falcon" in row.name.lower() for row in found)

    def test_it_ignores_case_and_surrounding_space(self, rows):
        assert matching(rows, "  FALCON ") == matching(rows, "falcon")

    def test_it_matches_the_operator_too(self, rows):
        assert {row.key for row in matching(rows, "nasa")} >= {"saturn_v", "space_shuttle"}

    def test_it_matches_the_key_so_a_shared_link_can_be_pasted_in(self, rows):
        assert [row.key for row in matching(rows, "raptor33_expendable")] == [
            "raptor33_expendable"
        ]

    def test_no_match_is_an_empty_list_rather_than_everything(self, rows):
        assert matching(rows, "zeppelin") == []


class TestTheColumns:
    def test_the_core_set_is_short_enough_to_read(self):
        assert len(CORE_COLUMNS) <= 8

    def test_the_two_sets_do_not_overlap(self):
        assert {col.key for col in CORE_COLUMNS} & {col.key for col in EXTRA_COLUMNS} == set()

    def test_every_column_names_a_real_field(self):
        known = set(FleetRow.__dataclass_fields__)
        for col in (*CORE_COLUMNS, *EXTRA_COLUMNS):
            assert col.key in known, f"{col.key} is not a FleetRow field"

    def test_every_column_has_a_heading(self):
        for col in (*CORE_COLUMNS, *EXTRA_COLUMNS):
            assert col.label

    def test_it_renders_as_a_markdown_table(self, rows):
        rendered = table(rows, list(CORE_COLUMNS))
        assert rendered.startswith("|")
        assert "Falcon 9" in rendered
        assert len(rendered.splitlines()) == len(rows) + 2


class TestGroups:
    """The same grouping the vehicle picker uses, so the two cannot disagree."""

    def test_no_groups_keeps_everything(self, rows):
        assert in_groups(rows, []) == rows

    def test_one_group_keeps_only_its_vehicles(self, rows, groups):
        concepts = next(g for g in groups if "thought experiment" in g.name)
        found = in_groups(rows, [concepts])
        assert {row.key for row in found} == set(concepts.keys)

    def test_groups_compose_without_duplicating(self, rows, groups):
        found = in_groups(rows, list(groups))
        assert [row.key for row in found] == [row.key for row in rows]

    def test_it_composes_with_the_text_filter(self, rows, groups):
        concepts = next(g for g in groups if "thought experiment" in g.name)
        found = matching(in_groups(rows, [concepts]), "expendable")
        assert [row.key for row in found] == ["raptor33_expendable"]

    def test_order_is_the_row_order_not_the_group_order(self, rows, groups):
        shuffled = in_groups(rows, list(reversed(groups)))
        assert [row.key for row in shuffled] == [row.key for row in rows]
