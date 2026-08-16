"""Drawn explanations: pictures that carry an argument a chart cannot.

A chart puts a number in a position. These put it in a shape. Chapter 1 can say
"your rocket is 90 % propellant" in a metric, and the reader nods; showing them a
vehicle that is almost entirely tank lands the same fact in one look.

Everything here returns standalone SVG for
``st.markdown(..., unsafe_allow_html=True)``, styled from
:mod:`labbook.palette` so a drawing and a chart of the same thing agree.
"""

import re
from dataclasses import dataclass

from labbook.palette import INK_MUTED, INK_SECONDARY, SURFACE, Mode, Series, colour
from labbook.units import METRIC, Formatter

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_WHITESPACE = re.compile(r"\s+")


def inline(markup: str) -> str:
    """Flatten markup so Streamlit renders it as markup rather than as text.

    ``st.markdown`` runs the markdown parser before it honours
    ``unsafe_allow_html``, and markdown claims any line indented four spaces or
    more as a code block. Multi-line SVG therefore arrives on the page as
    literal source, which is exactly what it did before this existed. Collapsing
    it onto one line takes the question away from the parser.

    Args:
        markup: SVG or HTML, formatted for a human to read.

    Returns:
        The same markup on a single line, with its comments dropped.
    """
    return _WHITESPACE.sub(" ", _COMMENT.sub("", markup)).strip()

_VIEWBOX = (250, 300)
_NOSE_TIP_Y = 12
_SHOULDER_Y = 64
_BASE_Y = 250
_LEFT = 34
_RIGHT = 78
_CENTRE = 56

_SILHOUETTE = (
    f"M {_LEFT} {_BASE_Y} L {_LEFT} {_SHOULDER_Y} "
    f"Q {_LEFT} 26 {_CENTRE} {_NOSE_TIP_Y} "
    f"Q {_RIGHT} 26 {_RIGHT} {_SHOULDER_Y} L {_RIGHT} {_BASE_Y} Z"
)
_FORE_FLAP_LEFT = f"M {_LEFT} 74 L 18 104 L {_LEFT} 110 Z"
_FORE_FLAP_RIGHT = f"M {_RIGHT} 74 L 94 104 L {_RIGHT} 110 Z"
_AFT_FLAP_LEFT = f"M {_LEFT} 196 L 12 {_BASE_Y} L {_LEFT} {_BASE_Y} Z"
_AFT_FLAP_RIGHT = f"M {_RIGHT} 196 L 100 {_BASE_Y} L {_RIGHT} {_BASE_Y} Z"
_FLAME = f"M {_LEFT + 6} {_BASE_Y - 1} Q {_CENTRE} 296 {_RIGHT - 6} {_BASE_Y - 1} Z"


@dataclass(frozen=True, slots=True)
class MassSplit:
    """How a vehicle's mass divides between what it burns and what it carries.

    Attributes:
        dry_t: Structure, engines and cargo, tonnes.
        propellant_t: What gets burnt, tonnes.
    """

    dry_t: float
    propellant_t: float

    @property
    def wet_t(self) -> float:
        """Mass on the pad, tonnes."""
        return self.dry_t + self.propellant_t

    @property
    def propellant_fraction(self) -> float:
        """Share of the vehicle that is propellant, 0 to 1."""
        return self.propellant_t / self.wet_t if self.wet_t else 0.0

    @property
    def mass_ratio(self) -> float:
        """How much heavier it is full than empty."""
        return self.wet_t / self.dry_t if self.dry_t else 0.0


def rocket_cutaway(
    *,
    dry_t: float,
    propellant_t: float,
    mode: Mode = Mode.LIGHT,
    formatter: Formatter = METRIC,
    height: int = 300,
    uid: str = "cutaway",
    animated: bool = True,
) -> str:
    """Draw the reader's rocket, filled to show what it is mostly made of.

    The whole silhouette is the vehicle and the fill rises from its base, so the
    orange reaching high into the nose is not artistic licence: a launch vehicle
    really is mostly tank.

    Args:
        dry_t: What it weighs empty, tonnes.
        propellant_t: What it burns, tonnes.
        mode: Light or dark surface.
        formatter: Unit system for the labels.
        height: Rendered height in pixels.
        uid: Prefix for CSS class names, so two drawings on one page do not
            share keyframes.
        animated: Whether the flame burns and the propellant surface moves.

    Returns:
        An ``<svg>`` element with its styles inlined.
    """
    split = MassSplit(dry_t=dry_t, propellant_t=propellant_t)
    width = round(height * _VIEWBOX[0] / _VIEWBOX[1])
    span = _BASE_Y - _NOSE_TIP_Y
    fill_top = _BASE_Y - span * split.propellant_fraction

    structure = colour(Series.STRUCTURE, mode)
    propellant = colour(Series.PROPELLANT, mode)
    flame = colour(Series.PROPELLANT, mode)
    flame_core = colour(Series.RECOVERY, mode)
    surface = SURFACE[mode]
    ink = INK_SECONDARY[mode]
    muted = INK_MUTED[mode]

    flame_layer = (
        f'<g class="{uid}-flame">'
        f'<path d="{_FLAME}" fill="{flame}" opacity="0.9"/>'
        f'<path class="{uid}-core" d="{_FLAME}" fill="{flame_core}" opacity="0.55"'
        f' transform="translate({_CENTRE} {_BASE_Y}) scale(0.5 0.62)'
        f' translate({-_CENTRE} {-_BASE_Y})"/>'
        "</g>"
        if propellant_t > 0
        else ""
    )

    return inline(f"""{_cutaway_styles(uid, animated)}
<svg class="{uid}-svg" width="{width}" height="{height}"
     viewBox="0 0 {_VIEWBOX[0]} {_VIEWBOX[1]}" role="img"
     aria-label="A rocket that is {split.propellant_fraction:.0%} propellant by mass">
  <title>{formatter.mass(split.wet_t, digits=0)} on the pad,
    {split.propellant_fraction:.0%} of it propellant</title>
  <defs>
    <clipPath id="{uid}-hull"><path d="{_SILHOUETTE}"/></clipPath>
  </defs>
  {flame_layer}
  <g fill="{structure}" stroke="{surface}" stroke-width="2" stroke-linejoin="round">
    <path d="{_FORE_FLAP_LEFT}"/>
    <path d="{_FORE_FLAP_RIGHT}"/>
    <path d="{_AFT_FLAP_LEFT}"/>
    <path d="{_AFT_FLAP_RIGHT}"/>
  </g>
  <g clip-path="url(#{uid}-hull)">
    <rect x="0" y="0" width="{_VIEWBOX[0]}" height="{_BASE_Y}" fill="{structure}"/>
    <rect class="{uid}-level" x="0" y="{fill_top:.1f}"
          width="{_VIEWBOX[0]}" height="{_BASE_Y - fill_top:.1f}" fill="{propellant}"/>
  </g>
  <path d="{_SILHOUETTE}" fill="none" stroke="{surface}" stroke-width="2"/>
  {_callouts(split, fill_top, ink, muted, structure, propellant, formatter)}
</svg>""")


def _callouts(
    split: MassSplit,
    fill_top: float,
    ink: str,
    muted: str,
    structure: str,
    propellant: str,
    formatter: Formatter,
) -> str:
    """Label the two parts, each beside the band it names.

    Direct labels rather than a legend, which is the rule every chart in this
    project follows.

    Args:
        split: The mass division being drawn.
        fill_top: Y coordinate of the propellant surface.
        ink: Colour for label text.
        muted: Colour for secondary text.
        structure: Colour of the structure swatch.
        propellant: Colour of the propellant swatch.
        formatter: Unit system for the numbers.

    Returns:
        SVG text and leader lines.
    """
    structure_y = max(_NOSE_TIP_Y + 22, fill_top / 2 + 10)
    propellant_y = min(_BASE_Y - 16, (fill_top + _BASE_Y) / 2 + 5)
    rows = [
        (structure_y, structure, "Empty rocket", split.dry_t, 1.0 - split.propellant_fraction),
        (propellant_y, propellant, "Propellant", split.propellant_t, split.propellant_fraction),
    ]
    parts = []
    for y, swatch, label, tonnes, share in rows:
        parts.append(
            f'<line x1="104" y1="{y - 4:.1f}" x2="116" y2="{y - 4:.1f}" '
            f'stroke="{swatch}" stroke-width="3" stroke-linecap="round"/>'
            f'<text x="122" y="{y:.1f}" font-size="13" font-weight="600"'
            f' fill="{ink}">{label}</text>'
            f'<text x="122" y="{y + 16:.1f}" font-size="12" fill="{muted}">'
            f"{formatter.mass(tonnes, digits=0)} · {share:.0%}</text>"
        )
    parts.append(
        f'<text x="122" y="{_BASE_Y + 28}" font-size="12" fill="{muted}">Mass ratio</text>'
        f'<text x="122" y="{_BASE_Y + 48}" font-size="17" font-weight="600" fill="{ink}">'
        f"{split.mass_ratio:.1f} : 1</text>"
    )
    return "".join(parts)


def _cutaway_styles(uid: str, animated: bool) -> str:
    """Keyframes for the flame and the propellant surface.

    Args:
        uid: Class name prefix.
        animated: Whether to emit any animation at all.

    Returns:
        A ``<style>`` block.
    """
    if not animated:
        return ""
    return f"""<style>
@keyframes {uid}-burn {{
  0%, 100% {{ transform: scaleY(0.82); opacity: 0.85; }}
  50%      {{ transform: scaleY(1.18); opacity: 1; }}
}}
@keyframes {uid}-slosh {{
  0%, 100% {{ transform: translateY(0px); }}
  50%      {{ transform: translateY(-2.5px); }}
}}
.{uid}-flame {{
  transform-origin: {_CENTRE}px {_BASE_Y}px;
  animation: {uid}-burn 0.85s ease-in-out infinite;
}}
.{uid}-core {{
  transform-origin: {_CENTRE}px {_BASE_Y}px;
  animation: {uid}-burn 0.58s ease-in-out infinite reverse;
}}
.{uid}-level {{ animation: {uid}-slosh 3.1s ease-in-out infinite; }}
@media (prefers-reduced-motion: reduce) {{
  .{uid}-flame, .{uid}-core, .{uid}-level {{ animation: none; }}
}}
</style>"""
