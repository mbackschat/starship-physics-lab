"""Put the reader's settings in the URL, so a finding can be sent to somebody.

Somebody who drags the dry-mass slider to 165 t and sees the payload hit 100
should be able to paste a link that lands the next person on exactly that.

Everything here assumes the URL is hostile. It is the one input a reader can
edit by hand, and a page that throws a stack trace because someone typed a word
where a number goes is a page that cannot be shared.
"""

import math
from collections.abc import Mapping


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
