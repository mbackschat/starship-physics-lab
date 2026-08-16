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

    The body colour is not set here. The file paints it in ``currentColor``, so
    it inherits the surrounding text colour and follows the reader's theme
    without this having to know which theme that is.

    Args:
        mode: Light or dark surface. Used only for the hairline gap between the
            mark's parts, which has to match the paper it sits on.
        height: Rendered height in pixels.
        uid: Class suffix, so two marks at different sizes on one page do not
            take each other's dimensions.

    Returns:
        A sized ``<span>`` wrapping the inlined SVG.
    """
    return inline(
        f"<style>.ship-mark-{uid} svg{{height:{height}px;width:auto;display:block}}</style>"
        f'<span class="ship-mark-{uid}" style="--ship-gap:{SURFACE[mode]}">{source()}</span>'
    )
