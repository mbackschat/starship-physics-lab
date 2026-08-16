"""The project's one visual language, validated rather than chosen by taste.

Propellant, structure and payload wear the same colour in every chart, on every
page, in the app and in a one-off analysis script. A reader who learns the
colours on chapter one can read chapter eight without a legend.

Validated with the dataviz palette checker in both modes::

    light  #2a78d6,#eb6834,#1baf7a,#eda100  surface #fcfcfb  -> all checks pass
    dark   #3987e5,#d95926,#199e70,#c98500  surface #1a1a19  -> all checks pass

Light mode returns a contrast warning for the aqua and yellow slots, which
obligates visible labels or a table view. Both are standard here: every chart
carries direct labels, and every analysis script emits a markdown table beside
its figure.
"""

from enum import StrEnum


class Mode(StrEnum):
    """Which surface the chart will be drawn on."""

    LIGHT = "light"
    DARK = "dark"


class Series(StrEnum):
    """The four things a rocket is made of, in fixed categorical order.

    Never cycled, never reassigned. A fifth category folds into OTHER rather
    than inventing a hue.
    """

    PAYLOAD = "payload"
    """What the rocket is for. Categorical slot 1."""

    PROPELLANT = "propellant"
    """What it burns to get there. Slot 2."""

    STRUCTURE = "structure"
    """The vehicle itself: tanks, engines, heat shield. Slot 3."""

    RECOVERY = "recovery"
    """Propellant carried uphill purely to come back down. Slot 4."""

    OTHER = "other"
    """Anything that does not fit. Drawn in muted ink, never a new hue."""

    @property
    def label(self) -> str:
        """Human-readable name for legends and labels."""
        match self:
            case Series.PAYLOAD:
                return "Payload"
            case Series.PROPELLANT:
                return "Ascent propellant"
            case Series.STRUCTURE:
                return "Structure (dry mass)"
            case Series.RECOVERY:
                return "Recovery propellant"
            case Series.OTHER:
                return "Other"


_LIGHT: dict[Series, str] = {
    Series.PAYLOAD: "#2a78d6",
    Series.PROPELLANT: "#eb6834",
    Series.STRUCTURE: "#1baf7a",
    Series.RECOVERY: "#eda100",
    Series.OTHER: "#898781",
}

_DARK: dict[Series, str] = {
    Series.PAYLOAD: "#3987e5",
    Series.PROPELLANT: "#d95926",
    Series.STRUCTURE: "#199e70",
    Series.RECOVERY: "#c98500",
    Series.OTHER: "#898781",
}

SURFACE: dict[Mode, str] = {Mode.LIGHT: "#fcfcfb", Mode.DARK: "#1a1a19"}
INK_PRIMARY: dict[Mode, str] = {Mode.LIGHT: "#0b0b0b", Mode.DARK: "#ffffff"}
INK_SECONDARY: dict[Mode, str] = {Mode.LIGHT: "#52514e", Mode.DARK: "#c3c2b7"}
INK_MUTED: dict[Mode, str] = {Mode.LIGHT: "#898781", Mode.DARK: "#898781"}
GRIDLINE: dict[Mode, str] = {Mode.LIGHT: "#e1e0d9", Mode.DARK: "#2c2c2a"}
AXIS: dict[Mode, str] = {Mode.LIGHT: "#c3c2b7", Mode.DARK: "#383835"}

HIGHLIGHT = "#d03b3b"
"""Reserved for one thing only: marking the vehicle under discussion.

Status red from the validated status palette. Never used as a series colour.
"""


def colour(series: Series, mode: Mode = Mode.LIGHT) -> str:
    """Colour for a series on a given surface.

    Args:
        series: What is being drawn.
        mode: Which surface it will be drawn on.

    Returns:
        A hex colour.
    """
    return (_LIGHT if mode is Mode.LIGHT else _DARK)[series]


def all_colours(mode: Mode = Mode.LIGHT) -> dict[Series, str]:
    """Every series colour for a mode.

    Args:
        mode: Which surface.

    Returns:
        Mapping of series to hex colour.
    """
    return dict(_LIGHT if mode is Mode.LIGHT else _DARK)
