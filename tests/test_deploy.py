"""The static build has logic, so it gets tested like anything else.

A broken build produces a page that loads and then does nothing, which is the
worst failure mode to debug from a browser console.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deploy"))

import build


@pytest.fixture(scope="module")
def files():
    return build.collect()


def test_the_entrypoint_is_collected(files):
    assert build.ENTRYPOINT in files


def test_the_physics_core_is_collected(files):
    assert "rocketry/ascent.py" in files
    assert "rocketry/library.py" in files


def test_the_presentation_layer_is_collected(files):
    assert "labbook/units.py" in files
    assert "labbook/charts.py" in files


def test_the_rocket_library_data_is_collected(files):
    assert "data/engines.yaml" in files
    assert "data/vehicles.yaml" in files


def test_every_chapter_page_is_collected(files):
    pages = [name for name in files if name.startswith("app/pages/")]
    assert len(pages) >= 3


def test_the_mark_is_collected(files):
    """The app inlines it from the virtual filesystem, so it has to be mounted.

    Without it every page raises on import rather than merely losing a picture.
    """
    assert "assets/logo.svg" in files


def test_the_app_can_find_the_mark_the_way_the_browser_build_lays_it_out(files, tmp_path):
    """The lookup walks upward for an ``assets`` directory, so the shape matters.

    Locally that finds ``<repo>/assets``. In the browser the packages are
    flattened to the mount root and ``assets`` sits beside them, which is a
    different shape reached by the same search.
    """
    for virtual in files:
        target = tmp_path / virtual
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")
    assert (tmp_path / "assets" / "logo.svg").is_file()
    assert (tmp_path / "labbook" / "logo.py").is_file()


def test_nothing_from_src_leaks_into_the_paths(files):
    """Packages are flattened out of src/ so they import at the mount root."""
    assert not any(name.startswith("src/") for name in files)


def test_authoring_tooling_is_not_shipped_to_the_reader(files):
    """The knowledge base is written locally and never read by the app.

    Every file here is downloaded into the browser before anything appears, so
    tooling that only an author runs has no business being among them.
    """
    shipped = "\n".join(files)
    assert "knowledge" not in shipped
    assert "raw/" not in shipped


def test_no_bytecode_is_shipped(files):
    assert not any("__pycache__" in name for name in files)


def test_index_marks_exactly_one_entrypoint(files):
    html = build._index(sorted(files))
    assert html.count(" entrypoint>") == 1
    assert f'name="{build.ENTRYPOINT}" url="./{build.ENTRYPOINT}" entrypoint>' in html


def test_index_mounts_every_collected_file(files):
    html = build._index(sorted(files))
    for name in files:
        assert f'name="{name}"' in html


def test_index_lists_the_runtime_requirements(files):
    html = build._index(sorted(files))
    for requirement in build.REQUIREMENTS:
        assert requirement in html


def test_index_refuses_to_build_without_its_entrypoint():
    with pytest.raises(ValueError, match="entrypoint"):
        build._index(["rocketry/ascent.py"])


def test_the_site_answers_unknown_paths_with_the_app(tmp_path, monkeypatch, files):
    """GitHub Pages serves 404.html for any path that is not a file on disk.

    Streamlit puts a chapter's own path in the address bar, so without this the
    reader's URL bar is full of links that answer with GitHub's error page:
    reloading a chapter, bookmarking one, or sharing one all fail.
    """
    monkeypatch.setattr(build, "SITE", tmp_path / "site")
    build.write_site(files)

    fallback = tmp_path / "site" / "404.html"
    assert fallback.exists(), "no 404.html, so every deep link lands on GitHub's error page"
    assert fallback.read_text() == (tmp_path / "site" / "index.html").read_text()


def test_the_fallback_page_finds_its_files_from_a_chapter_url(tmp_path, monkeypatch, files):
    """Relative URLs in the fallback resolve against the chapter path, not the root.

    A chapter URL is one segment deep, so ``./app/Home.py`` still resolves to the
    site root only because the segment is not a directory. Anything absolute
    would break under the project sub-path Pages serves from.
    """
    monkeypatch.setattr(build, "SITE", tmp_path / "site")
    build.write_site(files)

    html = (tmp_path / "site" / "404.html").read_text()
    assert 'url="/app/' not in html, "absolute paths break under the /repo-name/ sub-path"
    assert f'url="./{build.ENTRYPOINT}"' in html


def test_the_bootstrap_page_forwards_the_path_to_the_app(files):
    """The browser runtime hides the URL path from Python.

    It reports its own mount point as the URL and passes on only the query
    string, so the chapter has to be moved there before the app starts.
    """
    html = build._index(sorted(files))
    assert "replaceState" in html, "nothing moves the chapter path into the query string"
    assert f'searchParams.set("{build.CHAPTER_PARAM}"' in html


def test_the_boot_screen_shows_the_mark_while_python_downloads(files):
    """The first visit downloads an interpreter. Something has to be on screen.

    Inlined rather than linked: this same page answers unmatched paths such as
    /repo/The_payload_question, so a relative href would resolve against the
    wrong directory in exactly the case the 404 copy exists for.
    """
    html = build._index(sorted(files))
    boot = html.split('<div id="boot">', 1)[1].split("</div>", 1)[0]
    assert "<svg" in boot
    assert "<img" not in boot, "a relative src resolves wrongly on the 404 copy"
    assert 'rel="icon" href="data:image/svg+xml,' in html


def test_the_build_and_the_app_agree_on_the_chapter_parameter():
    """Two halves of one handshake, in two languages. A typo would be silent."""
    from labbook.sharing import CHAPTER_PARAM

    assert build.CHAPTER_PARAM == CHAPTER_PARAM


def test_the_bundle_stays_small(files):
    """Every kilobyte here is downloaded before the reader sees anything."""
    total_kb = sum(path.stat().st_size for path in files.values()) / 1024
    assert total_kb < 1024, f"{total_kb:.0f} kB of app code is too much to ship"


def test_heavy_dependencies_stay_out_of_the_runtime():
    """Scipy and ambiance were dropped deliberately. Keep them out."""
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        declared = tomllib.load(handle)["project"]["dependencies"]
    names = {entry.split(">")[0].split("=")[0].split("[")[0].strip() for entry in declared}
    for heavy in ("scipy", "ambiance", "numpy", "pandas"):
        assert heavy not in names, f"{heavy} is back in the runtime dependencies"
