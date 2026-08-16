"""Tests for the presentation helpers the app leans on.

The Streamlit pages are thin glue. Anything with logic in it lives in
:mod:`labbook` so it can be tested here without a browser.
"""

import pytest

from labbook.catalog import Group, browse, describe_provenance
from labbook.formula import Formula, Term
from labbook.units import METRIC, US, Quantity
from rocketry.library import load
from rocketry.models import Provenance


class TestFormulaRendering:
    """A formula shown twice, symbolically and with the reader's numbers in it.

    This is the single device that makes equations stop being frightening, so it
    gets tested rather than eyeballed.
    """

    def test_renders_symbols_and_numbers_side_by_side(self):
        formula = Formula(
            name="Rocket equation",
            symbolic="Δv = v_e · ln(m₀ / m_f)",
            terms=[
                Term("v_e", 3580.6, Quantity.VELOCITY),
                Term("m₀", 1900.0, Quantity.MASS),
                Term("m_f", 300.0, Quantity.MASS),
            ],
            result=Term("Δv", 6609.3, Quantity.VELOCITY),
        )
        assert formula.symbolic == "Δv = v_e · ln(m₀ / m_f)"
        substituted = formula.substituted(METRIC)
        assert "3,581" in substituted
        assert "1,900" in substituted
        assert "300" in substituted
        assert "6,609" in substituted

    def test_substitution_follows_the_unit_system(self):
        formula = Formula(
            name="Mass",
            symbolic="m = a + b",
            terms=[Term("a", 100.0, Quantity.MASS), Term("b", 100.0, Quantity.MASS)],
            result=Term("m", 200.0, Quantity.MASS),
        )
        assert "t" in formula.result_text(METRIC)
        assert "lb" in formula.result_text(US)
        assert "440,925" in formula.result_text(US)  # 200 t = 440,925 lb

    def test_longest_term_is_not_truncated(self):
        formula = Formula(
            name="Big",
            symbolic="m = a",
            terms=[Term("a", 5850.0, Quantity.MASS)],
            result=Term("m", 5850.0, Quantity.MASS),
        )
        assert "5,850" in formula.substituted(METRIC)

    def test_a_formula_needs_at_least_one_term(self):
        with pytest.raises(ValueError, match="at least one term"):
            Formula(name="Empty", symbolic="x = y", terms=[], result=Term("x", 1.0))


class TestCatalog:
    """The preset picker. Article vehicles come first and are marked."""

    @pytest.fixture
    def lib(self):
        return load()

    def test_article_vehicles_are_grouped_first(self, lib):
        groups = browse(lib)
        assert groups
        assert groups[0].name.startswith("From the article")

    def test_every_vehicle_appears_exactly_once(self, lib):
        keys = [key for group in browse(lib) for key in group.keys]
        assert sorted(keys) == sorted(lib.vehicles)
        assert len(keys) == len(set(keys))

    def test_groups_are_never_empty(self, lib):
        assert all(group.keys for group in browse(lib))

    def test_concepts_are_separated_from_things_that_flew(self, lib):
        by_name = {group.name: group.keys for group in browse(lib)}
        concepts = next(keys for name, keys in by_name.items() if "hought experiment" in name)
        assert "raptor33_raptor4" in concepts
        assert "starship_v3" not in concepts

    def test_group_labels_carry_the_vehicle_name(self, lib):
        group = browse(lib)[0]
        assert group.label(lib, group.keys[0]) == lib.vehicle(group.keys[0]).name


class TestProvenanceWording:
    """Contested numbers must never be presented as if they were measured."""

    def test_every_provenance_has_wording(self):
        for provenance in Provenance:
            described = describe_provenance(provenance)
            assert described.badge
            assert described.explanation

    def test_contested_wording_says_so_plainly(self):
        described = describe_provenance(Provenance.CONTESTED)
        assert "disagree" in described.explanation.lower()

    def test_published_is_not_dressed_up_as_certainty(self):
        described = describe_provenance(Provenance.PUBLISHED)
        assert described.badge != describe_provenance(Provenance.ESTIMATED).badge


class TestGroupModel:
    def test_a_group_rejects_an_unknown_key(self):
        lib = load()
        group = Group(name="Test", keys=("no_such_vehicle",))
        with pytest.raises(KeyError, match="no vehicle"):
            group.label(lib, "no_such_vehicle")


class TestMassBreakdown:
    """Splitting a vehicle into propellant, structure, recovery and payload.

    Regression guard: the payload was once attached to the booster row, which
    made the chart quietly say the opposite of what it meant.
    """

    @pytest.fixture
    def rows(self):
        from labbook.breakdown import mass_components
        from rocketry.vehicle import analyse

        return mass_components(analyse(load(), "starship_v3"))

    def test_rows_are_top_down(self, rows):
        assert rows[0].label == "Starship V3"
        assert rows[-1].label == "Super Heavy V3"

    def test_payload_rides_on_the_stage_that_reaches_orbit(self, rows):
        assert rows[0].payload > 0
        assert all(row.payload == 0.0 for row in rows[1:])

    @pytest.mark.parametrize(
        "key", ["starship_v3", "falcon9_droneship", "space_shuttle", "raptor33_raptor4"]
    )
    def test_every_tonne_is_accounted_for(self, key):
        """Including the fairing, which is easy to drop and hard to notice."""
        from labbook.breakdown import mass_components
        from rocketry.vehicle import analyse

        result = analyse(load(), key)
        rows = mass_components(result)
        assert sum(row.total for row in rows) == pytest.approx(result.liftoff_mass_t, rel=1e-9)

    def test_recovery_is_separated_from_ascent_propellant(self, rows):
        booster = rows[-1]
        assert booster.recovery > 0
        assert booster.propellant + booster.recovery == pytest.approx(
            booster.stage.propellant_t, rel=1e-9
        )
