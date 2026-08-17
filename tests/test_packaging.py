"""What the published wheel contains, which is not what the repository contains.

Both packages find their data by searching upward from their own module, which
works in a checkout and in the browser build because in both of those a parent
directory holds the tree. In an installed wheel there is no such parent: the
search walks out of ``site-packages`` and finds nothing. So the wheel has to
carry ``data/`` and ``assets/`` inside the packages themselves, and it shipped
without them.

Nothing about that fails at build time. It fails on the reader's first
``load()``, which is the worst possible place for it, so the contents of the
distribution are asserted here rather than trusted.
"""

import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def wheel(tmp_path_factory: pytest.TempPathFactory) -> zipfile.ZipFile:
    """Build the wheel the release publishes and open it for inspection."""
    out = tmp_path_factory.mktemp("dist")
    built = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        pytest.fail(f"uv build failed:\n{built.stderr}")
    wheels = list(out.glob("*.whl"))
    assert len(wheels) == 1, f"expected one wheel, got {[w.name for w in wheels]}"
    return zipfile.ZipFile(wheels[0])


@pytest.fixture(scope="session")
def shipped(wheel: zipfile.ZipFile) -> set[str]:
    return set(wheel.namelist())


def test_the_whole_rocket_library_travels_with_the_physics(shipped: set[str]):
    """Adding a YAML file to ``data/`` and not to the wheel breaks ``load()``."""
    missing = [
        yaml.name
        for yaml in sorted((ROOT / "data").glob("*.yaml"))
        if f"rocketry/data/{yaml.name}" not in shipped
    ]
    assert missing == [], f"the wheel does not carry {missing}"


def test_the_mark_travels_with_the_presentation_layer(shipped: set[str]):
    assert "labbook/assets/logo.svg" in shipped


def test_an_installed_package_finds_its_data_where_the_finders_look(shipped: set[str]):
    """The finders start at the package directory, so that is where these land.

    Asserting the paths rather than only the presence of the files: shipped
    somewhere else in the archive, they would satisfy a naive membership check
    and still be invisible to :func:`rocketry.library._find_data_dir`.
    """
    assert "rocketry/data/engines.yaml" in shipped
    assert "labbook/assets/logo.svg" in shipped


def test_the_authoring_tooling_stays_out_of_the_reader_s_download(shipped: set[str]):
    """``knowledge`` is for writing the corpus, and no consumer of the wheel needs it."""
    assert not [name for name in shipped if name.startswith("knowledge")]


def test_the_distribution_carries_its_licence(shipped: set[str]):
    """An artifact published without one is all-rights-reserved by default."""
    assert [name for name in shipped if name.endswith((".dist-info/licenses/LICENSE", "/LICENSE"))]
