"""Put the reader's settings in the URL, so a finding can be sent to somebody.

Somebody who drags the dry-mass slider to 165 t and sees the payload hit 100
should be able to paste a link that lands the next person on exactly that.

Everything here assumes the URL is hostile. It is the one input a reader can
edit by hand, and a page that throws a stack trace because someone typed a word
where a number goes is a page that cannot be shared.

There is a second, less obvious job here. Streamlit writes the chapter's own
path into the address bar as the reader navigates, but a static host has no
route for it and the browser never asks the app to restore it. So the landing
page reads that path itself and forwards, which is what :func:`route_for` is
for. Streamlit clears the query string when it switches page, so the settings
have to be carried across by hand.
"""

import math
import re
from collections.abc import Iterable, Mapping, MutableMapping

_LEADING_ORDER = re.compile(r"^\d+[_-]")
"""Chapter files are numbered to fix their order; the number is not in the URL."""

_CARRIED = "_shared_params"
"""Where settings wait while Streamlit throws the query string away."""

CHAPTER_PARAM = "chapter"
"""Where the bootstrap page leaves the chapter it found in the URL path.

The app cannot read that path itself: the browser runtime reports its own mount
point as the URL and forwards only the query string. See ``deploy/build.py``,
which sets this and is held to the same name by a test.
"""


def read_number(
    params: Mapping[str, str],
    key: str,
    *,
    default: float,
    low: float | None = None,
    high: float | None = None,
) -> float:
    """Read a number out of URL parameters, falling back rather than failing.

    Args:
        params: The query parameters.
        key: Which one to read.
        default: What to use when it is absent, unparseable or not finite.
        low: Clamp to at least this, if given.
        high: Clamp to at most this, if given.

    Returns:
        A usable number, always within the bounds when they are given.
    """
    raw = params.get(key)
    if raw is None:
        return _clamp(default, low, high)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _clamp(default, low, high)
    if not math.isfinite(value):
        return _clamp(default, low, high)
    return _clamp(value, low, high)


def read_choice(
    params: Mapping[str, str], key: str, *, default: str, allowed: Mapping[str, object] | set[str]
) -> str:
    """Read one of a fixed set of options out of URL parameters.

    Args:
        params: The query parameters.
        key: Which one to read.
        default: What to use when it is absent or not one of the options.
        allowed: The acceptable values.

    Returns:
        One of the allowed values.
    """
    raw = params.get(key)
    return raw if raw is not None and raw in allowed else default


def write_state(state: Mapping[str, object]) -> dict[str, str]:
    """Render settings as query parameters a person can read.

    Numbers lose a pointless trailing zero, so a shared link reads ``dry=165``
    rather than ``dry=165.0``.

    Args:
        state: Setting name to value.

    Returns:
        Parameters ready to assign to the page URL.
    """
    written: dict[str, str] = {}
    for key, value in state.items():
        if isinstance(value, bool):
            written[key] = "1" if value else "0"
        elif isinstance(value, float):
            written[key] = f"{value:g}"
        else:
            written[key] = str(value)
    return written


def page_slug(page_file: str) -> str:
    """The URL segment Streamlit gives a page file.

    Derived rather than listed, so renaming a chapter cannot leave a stale
    routing table behind.

    Args:
        page_file: Path to the page, as Streamlit refers to it.

    Returns:
        The last part of the URL for that page.
    """
    stem = page_file.rsplit("/", 1)[-1].removesuffix(".py")
    return _LEADING_ORDER.sub("", stem)


def route_for(url: str, pages: Iterable[str]) -> str | None:
    """Which chapter, if any, a URL is asking for.

    Args:
        url: The address the browser is showing.
        pages: The chapter page files to match against.

    Returns:
        The page file to switch to, or None to stay on the landing page. An
        unknown path is not an error: it just means the front door.
    """
    path = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    segment = path.rsplit("/", 1)[-1].lower()
    if not segment:
        return None
    for page in pages:
        if page_slug(page).lower() == segment:
            return page
    return None


def carry(session: MutableMapping[str, object], params: Mapping[str, str]) -> None:
    """Hold settings across a page switch.

    Args:
        session: Streamlit's session state.
        params: The query parameters to preserve.
    """
    if params:
        session[_CARRIED] = dict(params)


def collect(
    session: MutableMapping[str, object], params: Mapping[str, str]
) -> Mapping[str, str]:
    """Take the settings a page should start from, wherever they came from.

    A live URL always wins: the reader is looking at it. Anything carried over
    is consumed, so a stale link cannot keep overriding them on every rerun.

    Args:
        session: Streamlit's session state.
        params: The query parameters on the current page.

    Returns:
        The settings to read defaults from.
    """
    carried = session.pop(_CARRIED, None)
    if params:
        return params
    return dict(carried) if isinstance(carried, dict) else {}


def _clamp(value: float, low: float | None, high: float | None) -> float:
    """Hold a value inside its bounds.

    Args:
        value: The number.
        low: Lower bound, if any.
        high: Upper bound, if any.

    Returns:
        The bounded value.
    """
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value
