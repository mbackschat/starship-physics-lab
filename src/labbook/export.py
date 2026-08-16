"""Write results to disk so an investigation leaves something behind.

A study's output goes in an ``out/`` directory beside its own ``run.py``, which
is what :func:`beside` returns. Figures are written as both PNG and interactive
HTML: the PNG so it can be read back and looked at, embedded in a document or
pasted into a conversation, the HTML so the numbers behind it stay inspectable.
"""

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from plotly.graph_objects import Figure

OUT_DIR = Path(__file__).resolve().parents[2] / "studies" / "out"
"""Fallback output directory, used when a caller does not say where to write.

Prefer :func:`beside`, so each study's output lands next to the script that
produced it.
"""


def beside(script: str) -> Path:
    """Output directory for a study, next to the script that produces it.

    Call as ``beside(__file__)`` from a study's ``run.py``. Keeps the method,
    the result and the generated figures in one folder.

    Args:
        script: The calling module's ``__file__``.

    Returns:
        The ``out`` directory beside that script.
    """
    return Path(script).resolve().parent / "out"


def save_figure(
    figure: "Figure",
    name: str,
    *,
    out_dir: Path | None = None,
    width: int = 1000,
    height: int = 600,
    scale: int = 2,
) -> list[Path]:
    """Write a figure as PNG and interactive HTML.

    Args:
        figure: The plotly figure.
        name: Base filename without extension, for example ``staging-sweep``.
        out_dir: Destination directory. Pass ``beside(__file__)``.
        width: PNG width in pixels.
        height: PNG height in pixels.
        scale: PNG resolution multiplier. 2 gives a crisp image on a retina
            display and in a document.

    Returns:
        The paths written, PNG first.
    """
    target = _prepare(out_dir)
    png = target / f"{name}.png"
    html = target / f"{name}.html"
    figure.write_image(png, width=width, height=height, scale=scale)
    figure.write_html(html, include_plotlyjs="cdn", full_html=True)
    return [png, html]


def save_table(markdown: str, name: str, *, out_dir: Path | None = None) -> Path:
    """Write a markdown table to disk.

    Args:
        markdown: Rendered markdown, typically from :func:`labbook.tables.table`.
        name: Base filename without extension.
        out_dir: Destination directory. Pass ``beside(__file__)``.

    Returns:
        The path written.
    """
    target = _prepare(out_dir)
    path = target / f"{name}.md"
    path.write_text(markdown.rstrip() + "\n")
    return path


def save_data(rows: list[dict[str, Any]], name: str, *, out_dir: Path | None = None) -> Path:
    """Write raw results as CSV, so a result can be re-examined without re-running.

    Args:
        rows: Records to write. Keys of the first row define the columns.
        name: Base filename without extension.
        out_dir: Destination directory. Pass ``beside(__file__)``.

    Returns:
        The path written.

    Raises:
        ValueError: If there is nothing to write.
    """
    if not rows:
        raise ValueError("nothing to write")
    target = _prepare(out_dir)
    path = target / f"{name}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _prepare(out_dir: Path | None) -> Path:
    """Resolve and create the output directory.

    Args:
        out_dir: Requested directory, or None for the default.

    Returns:
        The directory, guaranteed to exist.
    """
    target = out_dir or OUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target
