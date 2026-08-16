"""The knowledge base has to keep its promises, or it is just a folder of notes.

Two kinds of check. The first is that pages are well formed: parseable, typed,
sourced and dated, which is what OKF conformance amounts to here. The second is
the one that matters, and the reason this exists at all: a page that declares
itself the evidence for a library entry must actually point at an entry that
exists. Prose and numbers drifting apart silently is the failure this prevents.
"""

import datetime as dt
from pathlib import Path

import pytest

from knowledge import (
    KNOWLEDGE_DIR,
    Page,
    Status,
    Trust,
    contradicted_claims,
    load_pages,
    split_front_matter,
    unresolved_feeds,
)
from rocketry.models import Provenance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pages() -> list[Page]:
    return load_pages(KNOWLEDGE_DIR)


def page(front: str, body: str = "Body.") -> Page:
    """Build a page from frontmatter written inline, for the parsing tests."""
    return Page.parse(Path("test.md"), f"---\n{front}\n---\n\n{body}\n")


class TestParsing:
    def test_front_matter_and_body_are_separated(self):
        front, body = split_front_matter("---\ntype: Reference\n---\n\nThe body.\n")
        assert front == {"type": "Reference"}
        assert body.strip() == "The body."

    def test_a_page_without_front_matter_is_rejected(self):
        with pytest.raises(ValueError, match="front matter"):
            split_front_matter("# Just a heading\n")

    def test_unterminated_front_matter_is_rejected(self):
        with pytest.raises(ValueError, match="front matter"):
            split_front_matter("---\ntype: Reference\n\nno closing fence\n")


class TestOkfConformance:
    def test_type_is_the_only_required_field(self):
        # OKF v0.2: a concept carrying just `type` is fully conformant.
        assert page("type: Reference").type == "Reference"

    def test_a_page_without_a_type_is_rejected(self):
        with pytest.raises(ValueError, match="type"):
            _ = page("title: Nameless").type

    def test_unknown_keys_are_preserved(self):
        # OKF requires consumers to keep fields they do not recognise. The
        # project's own extensions depend on that being true.
        assert page("type: Reference\nnonsense: keep me").front["nonsense"] == "keep me"


class TestTrustTiers:
    """OKF derives trust from `verified` rather than storing a score."""

    def test_a_page_nobody_verified_is_unverified(self):
        assert page("type: Reference").trust is Trust.UNVERIFIED

    def test_a_page_only_a_machine_checked_is_machine_confirmed(self):
        front = "type: Reference\nverified:\n  - {by: agent/model-1, at: 2026-08-16T10:00:00Z}"
        assert page(front).trust is Trust.MACHINE_CONFIRMED

    def test_a_page_a_person_checked_is_human_reviewed(self):
        front = (
            "type: Reference\nverified:\n"
            "  - {by: agent/model-1, at: 2026-08-16T10:00:00Z}\n"
            "  - {by: 'human:mbackschat', at: 2026-08-16T11:00:00Z}"
        )
        assert page(front).trust is Trust.HUMAN_REVIEWED

    def test_a_bare_mapping_counts_as_one_entry(self):
        # The spec requires consumers to treat a single mapping as a one-element
        # list rather than rejecting it.
        front = "type: Reference\nverified: {by: 'human:mbackschat', at: 2026-08-16T11:00:00Z}"
        assert page(front).trust is Trust.HUMAN_REVIEWED


class TestLifecycle:
    def test_status_defaults_to_stable(self):
        assert page("type: Reference").status is Status.STABLE

    def test_status_is_read_when_given(self):
        assert page("type: Reference\nstatus: deprecated").status is Status.DEPRECATED

    def test_an_unknown_status_is_rejected(self):
        with pytest.raises(ValueError, match="status"):
            _ = page("type: Reference\nstatus: probably-fine").status

    def test_staleness_is_a_plain_date_comparison(self):
        fresh = page("type: Reference\nstale_after: 2026-12-31")
        assert not fresh.is_stale(dt.date(2026, 8, 16))
        assert fresh.is_stale(dt.date(2026, 12, 31))

    def test_a_page_with_no_expiry_never_goes_stale(self):
        assert not page("type: Reference").is_stale(dt.date(2099, 1, 1))


class TestClaims:
    """A page may assert what a library entry says, and then be held to it.

    This is the check the corpus exists to make possible. Prose is not parsed
    for numbers, because that is unreliable and fails silently; a page states
    the values it stands behind, and those are compared exactly.
    """

    def test_a_feed_may_be_a_plain_reference_with_nothing_asserted(self):
        entry = page("type: Vehicle\nfeeds: [data/stages.yaml#starship_v3]")
        assert entry.feeds[0].target == "data/stages.yaml#starship_v3"
        assert entry.feeds[0].asserts == {}
        assert not unresolved_feeds(entry, ROOT)
        assert not contradicted_claims(entry, ROOT)

    def test_matching_claims_pass(self):
        entry = page(
            "type: Vehicle\nfeeds:\n"
            "  - target: data/stages.yaml#starship_v3\n"
            "    asserts: {dry_mass_t: 220.0, propellant_t: 1600.0}"
        )
        assert not contradicted_claims(entry, ROOT)

    def test_a_claim_the_library_contradicts_is_reported(self):
        entry = page(
            "type: Vehicle\nfeeds:\n"
            "  - target: data/stages.yaml#starship_v3\n"
            "    asserts: {dry_mass_t: 999.0}"
        )
        found = contradicted_claims(entry, ROOT)
        assert len(found) == 1
        assert "dry_mass_t" in found[0] and "999" in found[0] and "220" in found[0]

    def test_a_claim_about_a_field_that_does_not_exist_is_reported(self):
        entry = page(
            "type: Vehicle\nfeeds:\n"
            "  - target: data/stages.yaml#starship_v3\n"
            "    asserts: {invented_field: 1.0}"
        )
        assert contradicted_claims(entry, ROOT)

    def test_claims_work_against_list_shaped_files_too(self):
        # Flights are a list whose entries identify themselves by number, not a
        # keyed mapping. A reference should read the same either way.
        entry = page(
            "type: Flight\nfeeds:\n"
            "  - target: data/flights.yaml#13\n"
            "    asserts: {payload_t: 34.1}"
        )
        assert not contradicted_claims(entry, ROOT)

    def test_a_claim_against_a_missing_entry_is_reported_as_unresolved(self):
        entry = page("type: Vehicle\nfeeds: [data/stages.yaml#no_such_stage]")
        assert unresolved_feeds(entry, ROOT) == ["data/stages.yaml#no_such_stage"]


class TestTheLibraryPages:
    """The real pages in docs/knowledge/, checked as a body of work."""

    def test_there_are_pages_to_check(self, pages):
        assert pages, "no knowledge pages found; the corpus is empty"

    def test_every_page_declares_a_type(self, pages):
        for entry in pages:
            assert entry.type, f"{entry.path} has no type"

    def test_every_page_cites_a_dated_source(self, pages):
        for entry in pages:
            assert entry.sources, f"{entry.path} cites no source"
            for source in entry.sources:
                assert source.get("resource"), f"{entry.path} has a source with no resource"
                assert source.get("last_modified"), (
                    f"{entry.path} has a source with no retrieval date, so nobody can tell "
                    "how old it is"
                )

    def test_no_page_has_gone_stale(self, pages):
        stale = [entry.path.name for entry in pages if entry.is_stale(dt.date.today())]
        assert not stale, f"past their stale_after date and need rechecking: {stale}"

    def test_every_page_states_how_much_weight_its_numbers_bear(self, pages):
        for entry in pages:
            assert entry.front.get("provenance") in set(Provenance), (
                f"{entry.path} needs a provenance from {[p.value for p in Provenance]}"
            )

    def test_every_page_that_claims_to_feed_the_library_points_at_something_real(self, pages):
        # The whole point of the corpus. A page saying it is the evidence for
        # data/vehicles.yaml#starship_v3 must point at an entry that exists.
        for entry in pages:
            missing = unresolved_feeds(entry, ROOT)
            assert not missing, f"{entry.path} feeds entries that do not exist: {missing}"

    def test_no_page_contradicts_the_library_it_stands_behind(self, pages):
        # The guarantee. If an operator restates a figure and only one of the
        # two places is updated, this is what fails.
        for entry in pages:
            wrong = contradicted_claims(entry, ROOT)
            assert not wrong, f"{entry.path} disagrees with the library: {wrong}"

    def test_at_least_one_page_actually_asserts_something(self, pages):
        # A corpus where every feed is a bare reference would pass the check
        # above while guaranteeing nothing at all.
        asserted = sum(len(feed.asserts) for entry in pages for feed in entry.feeds)
        assert asserted, "no page asserts any value, so the consistency check is vacuous"

    def test_every_page_is_listed_in_the_index(self, pages):
        index = (KNOWLEDGE_DIR / "index.md").read_text()
        for entry in pages:
            relative = entry.path.relative_to(KNOWLEDGE_DIR).as_posix()
            assert relative in index, f"{relative} is not listed in index.md"
