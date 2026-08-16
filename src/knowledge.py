"""Read and check the knowledge base in ``docs/knowledge``.

Pages are markdown with YAML front matter in `Open Knowledge Format v0.2
<https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>`_,
plus two extensions this project needs. The design and the reasoning are in
docs/knowledge-base.md.

This is authoring tooling, not application code. It is deliberately outside both
shipped packages and outside ``deploy/build.py``'s trees, so it never becomes a
wheel the reader has to download. A test in tests/test_deploy.py holds that.

Two OKF details drive most of what is here. Trust tiers are *derived* from who
signed a page off rather than stored as a score, so there is nothing to keep in
sync and nothing to inflate. And unknown keys must be preserved rather than
rejected, which is what makes ``provenance`` and ``feeds`` legal extensions
rather than a private fork of the format.
"""

import datetime as dt
import math
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "docs" / "knowledge"
"""Where the compiled pages live."""

RESERVED = {"index.md", "log.md"}
"""Files in the knowledge directory that are not pages."""

_FENCE = "---"


class Status(StrEnum):
    """Where a page is in its life. Absent means :attr:`STABLE`."""

    DRAFT = "draft"
    """Not yet reviewed. May be incomplete."""

    STABLE = "stable"
    """Ready to be relied on."""

    DEPRECATED = "deprecated"
    """Kept for its links and its history, no longer current."""


class Trust(StrEnum):
    """How thoroughly a page was checked. Derived from ``verified``, never stored."""

    UNVERIFIED = "unverified"
    """Nobody has confirmed it against its sources."""

    MACHINE_CONFIRMED = "machine-confirmed"
    """Checked, but only by a machine."""

    HUMAN_REVIEWED = "human-reviewed"
    """At least one person put their name to it."""


HUMAN_PREFIX = "human:"
"""OKF actor format marking a person rather than an agent or a process."""


@dataclass(frozen=True, slots=True)
class Feed:
    """A library entry a page stands behind, and what it says about it.

    Attributes:
        target: A reference of the form ``<file>#<key>``, for example
            ``data/stages.yaml#starship_v3``.
        asserts: Field name to the value the page claims that entry holds.
            Empty when the page only claims the entry exists.
    """

    target: str
    asserts: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, declared: Any) -> "Feed":
        """Read a feed written either as a bare reference or as a claim.

        A page that only wants to record which entries it explains writes a
        string. One prepared to be held to the numbers writes a mapping.

        Args:
            declared: The entry as it appears in the front matter.

        Returns:
            The feed.
        """
        if isinstance(declared, dict):
            asserts = declared.get("asserts") or {}
            return cls(target=str(declared.get("target", "")), asserts=dict(asserts))
        return cls(target=str(declared))


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Separate a page's front matter from its body.

    Args:
        text: The whole file.

    Returns:
        The parsed front matter, and the body that followed it.

    Raises:
        ValueError: If the file does not open with a front matter block, or
            never closes it. Both mean the page cannot be checked at all, so
            they fail loudly rather than being treated as an empty page.
    """
    if not text.startswith(f"{_FENCE}\n"):
        raise ValueError("page does not start with a front matter fence")
    rest = text[len(_FENCE) + 1 :]
    closing = rest.find(f"\n{_FENCE}\n")
    if closing == -1:
        raise ValueError("front matter is never closed")
    loaded = yaml.safe_load(rest[:closing]) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"front matter should be a mapping, got {type(loaded).__name__}")
    return loaded, rest[closing + len(_FENCE) + 2 :]


@dataclass(frozen=True, slots=True)
class Page:
    """One compiled page.

    Attributes:
        path: Where it lives.
        front: Its front matter, unknown keys included.
        body: Everything after the front matter.
    """

    path: Path
    front: dict[str, Any]
    body: str

    @classmethod
    def parse(cls, path: Path, text: str) -> "Page":
        """Build a page from a file's contents.

        Args:
            path: Where it came from, for error messages.
            text: The whole file.

        Returns:
            The page.
        """
        front, body = split_front_matter(text)
        return cls(path=path, front=front, body=body)

    @classmethod
    def read(cls, path: Path) -> "Page":
        """Build a page from a file on disk.

        Args:
            path: The file.

        Returns:
            The page.
        """
        return cls.parse(path, path.read_text())

    @property
    def type(self) -> str:
        """What kind of thing this page describes.

        Returns:
            The declared type.

        Raises:
            ValueError: If absent. It is OKF's one required field.
        """
        declared = self.front.get("type")
        if not declared:
            raise ValueError(f"{self.path} has no type, which OKF requires")
        return str(declared)

    @property
    def title(self) -> str:
        """Display name, falling back to the file name as OKF permits.

        Returns:
            The title.
        """
        return str(self.front.get("title") or self.path.stem)

    @property
    def sources(self) -> list[dict[str, Any]]:
        """What this page was built from.

        Returns:
            The source entries, empty if none were declared.
        """
        declared = self.front.get("sources") or []
        return [entry for entry in declared if isinstance(entry, dict)]

    @property
    def feeds(self) -> list[Feed]:
        """Library entries this page is the evidence for.

        A project extension, not OKF.

        Returns:
            The feeds, empty if this page backs nothing.
        """
        declared = self.front.get("feeds") or []
        return [Feed.parse(entry) for entry in declared]

    @property
    def status(self) -> Status:
        """Where this page is in its life.

        Returns:
            The status, defaulting to stable as OKF specifies.

        Raises:
            ValueError: If the declared status is not one OKF defines.
        """
        declared = self.front.get("status")
        if declared is None:
            return Status.STABLE
        try:
            return Status(str(declared))
        except ValueError:
            allowed = ", ".join(entry.value for entry in Status)
            raise ValueError(
                f"{self.path} has status {declared!r}; OKF allows: {allowed}"
            ) from None

    @property
    def trust(self) -> Trust:
        """How thoroughly this page was checked.

        Derived rather than read. A page carrying no ``verified`` key is
        unverified, and that absence is itself the signal.

        Returns:
            The tier.
        """
        actors = [str(entry.get("by", "")) for entry in self._verifications()]
        if not actors:
            return Trust.UNVERIFIED
        if any(actor.startswith(HUMAN_PREFIX) for actor in actors):
            return Trust.HUMAN_REVIEWED
        return Trust.MACHINE_CONFIRMED

    @property
    def stale_after(self) -> dt.date | None:
        """The date this page should be rechecked.

        Returns:
            The date, or None if the page carries no expiry.

        Raises:
            ValueError: If the value is not a date.
        """
        declared = self.front.get("stale_after")
        if declared is None:
            return None
        if isinstance(declared, dt.datetime):
            return declared.date()
        if isinstance(declared, dt.date):
            return declared
        try:
            return dt.date.fromisoformat(str(declared))
        except ValueError:
            raise ValueError(
                f"{self.path} has stale_after {declared!r}, which is not a YYYY-MM-DD date"
            ) from None

    def is_stale(self, today: dt.date) -> bool:
        """Whether this page has passed its recheck date.

        A plain comparison against an absolute date, which is why OKF uses one
        rather than a time-to-live: there is no reference time to get wrong.

        Args:
            today: The date to compare against.

        Returns:
            True if the page is due a recheck.
        """
        expiry = self.stale_after
        return expiry is not None and today >= expiry

    def _verifications(self) -> list[dict[str, Any]]:
        """Sign-offs on this page.

        OKF allows a single mapping where a list is expected, and requires
        consumers to treat it as a one-element list.

        Returns:
            The verification entries.
        """
        declared = self.front.get("verified")
        if declared is None:
            return []
        if isinstance(declared, dict):
            return [declared]
        return [entry for entry in declared if isinstance(entry, dict)]


def load_pages(root: Path) -> list[Page]:
    """Read every page under a directory.

    Args:
        root: The knowledge directory.

    Returns:
        The pages, in path order. Empty if the directory does not exist yet.
    """
    if not root.is_dir():
        return []
    return [
        Page.read(path)
        for path in sorted(root.rglob("*.md"))
        if path.name not in RESERVED
    ]


def unresolved_feeds(page: Page, repo_root: Path) -> list[str]:
    """Which of a page's ``feeds`` references point at nothing.

    A page claiming to be the evidence for a library entry has to point at an
    entry that is really there, or the two can drift apart unnoticed.

    Args:
        page: The page to check.
        repo_root: Repository root, which the references are relative to.

    Returns:
        The references that could not be resolved, empty if all of them were.
    """
    return [feed.target for feed in page.feeds if _resolve(feed.target, repo_root) is None]


def contradicted_claims(page: Page, repo_root: Path) -> list[str]:
    """Where a page's asserted values disagree with the library.

    The guarantee the corpus exists to provide. Prose is deliberately not
    scanned for numbers: that is unreliable and fails silently. A page states
    what it stands behind under ``asserts`` and is held to exactly that.

    Args:
        page: The page to check.
        repo_root: Repository root, which the references are relative to.

    Returns:
        One readable line per disagreement, empty if the page and the library
        agree everywhere they both speak.
    """
    problems: list[str] = []
    for feed in page.feeds:
        entry = _resolve(feed.target, repo_root)
        if entry is None:
            continue
        for name, claimed in feed.asserts.items():
            if name not in entry:
                problems.append(f"{feed.target} has no field {name!r}")
            elif not _same(claimed, entry[name]):
                problems.append(
                    f"{feed.target} field {name!r}: page says {claimed!r}, "
                    f"library says {entry[name]!r}"
                )
    return problems


def _resolve(reference: str, repo_root: Path) -> dict[str, Any] | None:
    """Find the library entry a ``<file>#<key>`` reference names.

    The library is a mixture of shapes: engines, stages and vehicles are keyed
    mappings, while flights are a list whose entries identify themselves by
    number. Both are accepted so a reference reads the same either way.

    Args:
        reference: The reference to resolve.
        repo_root: Repository root, which it is relative to.

    Returns:
        The entry, or None if the file or the key does not exist.
    """
    target, _, key = reference.partition("#")
    path = repo_root / target
    if not key or not path.is_file():
        return None
    loaded = yaml.safe_load(path.read_text())
    if isinstance(loaded, dict):
        found = loaded.get(key)
        return found if isinstance(found, dict) else None
    if isinstance(loaded, list):
        for entry in loaded:
            if isinstance(entry, dict) and any(
                str(entry.get(name)) == key for name in ("key", "number", "name")
            ):
                return entry
    return None


def _same(claimed: Any, actual: Any) -> bool:
    """Whether an asserted value matches what the library holds.

    Numbers are compared with a tolerance because both sides pass through YAML
    and a page writing 220 for a stored 220.0 is agreement, not a discrepancy.

    Args:
        claimed: What the page says.
        actual: What the library says.

    Returns:
        True if they agree.
    """
    if isinstance(claimed, bool) or isinstance(actual, bool):
        return claimed is actual
    if isinstance(claimed, int | float) and isinstance(actual, int | float):
        return math.isclose(claimed, actual, rel_tol=1e-9, abs_tol=1e-12)
    return bool(claimed == actual)
