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


def test_nothing_from_src_leaks_into_the_paths(files):
    """Packages are flattened out of src/ so they import at the mount root."""
    assert not any(name.startswith("src/") for name in files)


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
