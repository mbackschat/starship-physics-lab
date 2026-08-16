"""The glossary and the fact check.

The fact check recomputes the article's numbers live rather than quoting a
stored answer, so it cannot drift away from the physics core. If someone changes
an Isp in the library, this page changes with it or the tests fail.
"""

import pytest

from labbook.factcheck import CLAIMS, Verdict, check_all
from labbook.glossary import TERMS, define, search


class TestGlossary:
    def test_the_words_a_beginner_will_trip_over_are_all_there(self):
        for word in (
            "delta-v",
            "specific impulse",
            "mass ratio",
            "staging",
            "gravity loss",
            "payload fraction",
            "dry mass",
            "thrust-to-weight ratio",
        ):
            assert define(word) is not None, f"{word} is missing"

    def test_every_definition_avoids_defining_a_word_with_itself(self):
        for term in TERMS:
            first = term.plain.split(".")[0].lower()
            assert term.word.lower() not in first, f"{term.word} defines itself"

    def test_every_term_has_a_plain_language_definition(self):
        for term in TERMS:
            assert len(term.plain) > 30
            assert term.plain[0].isupper()

    def test_terms_are_alphabetical(self):
        words = [term.word.lower() for term in TERMS]
        assert words == sorted(words)

    def test_lookup_is_case_and_space_insensitive(self):
        assert define("Delta-V") is define("delta-v")
        assert define("  specific impulse ") is define("specific impulse")

    def test_unknown_words_return_nothing_rather_than_raising(self):
        assert define("warp drive") is None

    def test_search_finds_by_definition_as_well_as_by_name(self):
        assert any(term.word == "Gravity loss" for term in search("holding"))
        assert search("nonsense phrase that appears nowhere") == []

    def test_related_terms_all_exist(self):
        known = {term.word.lower() for term in TERMS}
        for term in TERMS:
            for related in term.related:
                assert related.lower() in known, f"{term.word} points at missing {related}"

    def test_a_term_does_not_relate_to_itself(self):
        for term in TERMS:
            assert term.word not in term.related


@pytest.fixture(scope="module")
def results():
    return check_all()


class TestFactCheck:

    def test_every_claim_is_checked(self, results):
        assert len(results) == len(CLAIMS)
        assert len(results) >= 12

    def test_the_article_mostly_holds_up(self, results):
        confirmed = [r for r in results if r.verdict is Verdict.CONFIRMED]
        assert len(confirmed) / len(results) > 0.7

    def test_the_three_known_errors_are_still_flagged(self, results):
        wrong = {r.claim.topic for r in results if r.verdict is Verdict.WRONG}
        assert "Binary velocity constant" in wrong
        assert "Falcon 9 acceleration at T+40 s" in wrong

    def test_computed_values_come_from_the_physics_core(self, results):
        """Not stored answers: the page must recompute or it will drift."""
        for result in results:
            assert isinstance(result.computed, float)

    def test_every_claim_cites_where_it_is_verified(self):
        for claim in CLAIMS:
            assert claim.section, f"{claim.topic} does not say where it is verified"

    def test_verdicts_match_the_stated_tolerance(self, results):
        for result in results:
            error = abs(result.computed - result.claim.article_value)
            relative = error / abs(result.claim.article_value)
            expected = Verdict.CONFIRMED if relative <= result.claim.tolerance else Verdict.WRONG
            assert result.verdict is expected, (
                f"{result.claim.topic} verdict disagrees with its own arithmetic"
            )
