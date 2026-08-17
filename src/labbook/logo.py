"""Load the project's mark and inline it into a page.

The mark itself is [`assets/logo.svg`](../../assets/logo.svg), a hand-editable
file rather than markup assembled here. It is also the favicon and the artwork
on the boot screen, so it has to stand on its own without Python.

This module exists only because the app has nowhere to fetch it from. stlite
serves the app from a virtual filesystem with no HTTP origin behind it, so an
``<img src=...>`` would have nothing to resolve against. The file is therefore
read and inlined into the page instead.
"""

from functools import lru_cache
from pathlib import Path

from labbook.palette import SURFACE, Mode
from labbook.visuals import inline

ASSET_NAME = "logo.svg"

_STEEL_SHADOW: dict[Mode, str] = {
    Mode.LIGHT: "#4d555a",
    Mode.DARK: "#697176",
}
_STEEL_MIDTONE: dict[Mode, str] = {
    Mode.LIGHT: "#9da5aa",
    Mode.DARK: "#b2b9bd",
}
_STEEL_HIGHLIGHT: dict[Mode, str] = {
    Mode.LIGHT: "#f2f5f5",
    Mode.DARK: "#f7f9f9",
}
_HEAT_SHIELD: dict[Mode, str] = {
    Mode.LIGHT: "#22272b",
    Mode.DARK: "#111416",
}


@lru_cache(maxsize=1)
def _assets_dir() -> Path:
    """Locate the assets directory by searching upward from this module.

    The repository keeps it at ``<root>/assets``, but a WebAssembly build mounts
    the packages at a different root, so counting parent directories is fragile.
    Searching for the directory that actually holds the mark works in both. This
    mirrors :func:`rocketry.library._find_data_dir`, for the same reason.

    Returns:
        The assets directory.

    Raises:
        FileNotFoundError: If the mark cannot be found from here, which means
            the build did not ship it.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "assets"
        if (candidate / ASSET_NAME).is_file():
            return candidate
    raise FileNotFoundError(
        f"cannot find assets/{ASSET_NAME} from {here}. If this is the browser "
        "build, deploy/build.py has stopped shipping the assets tree."
    )


@lru_cache(maxsize=1)
def source() -> str:
    """The mark's SVG source, exactly as it sits on disk.

    Returns:
        The contents of ``assets/logo.svg``.
    """
    return (_assets_dir() / ASSET_NAME).read_text().strip()


def mark(*, mode: Mode = Mode.LIGHT, height: int = 96, uid: str = "mark") -> str:
    """The mark, sized and ready for ``st.markdown(..., unsafe_allow_html=True)``.

    The file carries a default steel palette for each colour scheme so that it
    stands up as a plain image. The app states the palette again because
    Streamlit's active theme need not agree with the operating system setting.

    Args:
        mode: Light or dark surface. Decides the steel reflections, heat shield
            and the hairline gap between parts.
        height: Rendered height in pixels.
        uid: Class and gradient suffix, so two marks on one page do not share
            dimensions or paint definitions.

    Returns:
        A sized ``<span>`` wrapping the inlined SVG.
    """
    # One class deeper than the file's own rules, which is what makes this win.
    gradient_id = f"ship-steel-{uid}"
    svg = source().replace('id="ship-steel"', f'id="{gradient_id}"').replace(
        "url(#ship-steel)", f"url(#{gradient_id})"
    )
    return inline(
        f"<style>.ship-mark-{uid} svg{{"
        f"height:{height}px;width:auto;display:block;"
        f"--ship-steel-shadow:{_STEEL_SHADOW[mode]};"
        f"--ship-steel-midtone:{_STEEL_MIDTONE[mode]};"
        f"--ship-steel-highlight:{_STEEL_HIGHLIGHT[mode]};"
        f"--ship-tile:{_HEAT_SHIELD[mode]};"
        f"--ship-gap:{SURFACE[mode]}"
        f"}}</style>"
        f'<span class="ship-mark-{uid}">{svg}</span>'
    )
