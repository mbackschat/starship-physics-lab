"""The chapter registry must describe the chapters that actually exist.

The registry is the single source of truth for the tour: the landing page builds
its cards from it, prose links point through it, and the router matches against
it. If it drifts away from ``app/pages/`` every one of those breaks at once, so
the two are held together here rather than by anyone remembering.
"""

from pathlib import Path

import pytest

from labbook.navigation import (
    CHAPTERS,
    FOUNDATIONS,
    REPOSITORY_URL,
    applications,
    chapter,
    foundations,
    page_files,
)
from labbook.sharing import page_slug, route_for

PAGES_DIR = Path(__file__).resolve().parents[1] / "app" / "pages"


def test_every_registered_chapter_has_a_file():
    missing = [
        entry.page_file
        for entry in CHAPTERS
        if not (PAGES_DIR / Path(entry.page_file).name).is_file()
    ]
    assert not missing, f"registry names chapters with no page file: {missing}"


def test_every_file_is_a_registered_chapter():
    on_disk = {path.name for path in PAGES_DIR.glob("*.py")}
    registered = {Path(entry.page_file).name for entry in CHAPTERS}
    assert on_disk == registered


def test_numbers_are_a_gapless_run_from_one():
    assert [entry.number for entry in CHAPTERS] == list(range(1, len(CHAPTERS) + 1))


def test_page_files_are_in_chapter_order_not_file_order():
    # Sorting the file names as strings puts 10 and 11 ahead of 2, which is why
    # the order comes from the registry rather than from a glob.
    assert page_files()[:3] == [
        "pages/1_Rocket_equation.py",
        "pages/2_Anatomy.py",
        "pages/3_Launch.py",
    ]
    assert page_files()[-1] == "pages/11_Glossary.py"


def test_chapter_looks_up_by_number():
    assert chapter(4).title == "Stages"
    assert chapter(4).page_file == "pages/4_Stages.py"


def test_unknown_chapter_says_what_exists():
    with pytest.raises(KeyError, match="no chapter 99"):
        chapter(99)


def test_label_is_the_numbered_title():
    assert chapter(1).label == "1 · The rocket equation"


def test_foundations_and_applications_partition_the_tour():
    assert foundations() + applications() == CHAPTERS
    assert len(foundations()) == FOUNDATIONS


def test_every_chapter_is_reachable_by_its_own_slug():
    # The router has to resolve the URL each chapter's own page_file implies,
    # or a shared link lands on the front door instead of the chapter.
    for entry in CHAPTERS:
        slug = page_slug(entry.page_file)
        assert route_for(f"https://example.com/app/{slug}", page_files()) == entry.page_file


def test_repository_url_points_at_a_github_project():
    assert REPOSITORY_URL.startswith("https://github.com/")
