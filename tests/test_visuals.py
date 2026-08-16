"""The mark, and the cutaway chapter 1 is built around.

SVG is awkward to assert on, so the arithmetic that decides what gets drawn is
pulled out into :class:`labbook.visuals.MassSplit` and tested directly. What is
left for the markup is the handful of properties a reader actually depends on:
it carries a text alternative, it paints from the palette rather than from
invented colours, and it can be turned still for anyone who asked for that.
"""

import xml.etree.ElementTree as ET

import pytest

from labbook.logo import ASSET_NAME, mark, source
from labbook.palette import INK_PRIMARY, SURFACE, Mode, Series, colour
from labbook.visuals import MassSplit, inline, rocket_cutaway, table_style


def test_mass_split_reports_the_shares():
    split = MassSplit(dry_t=10.0, propellant_t=90.0)
    assert split.wet_t == pytest.approx(100.0)
    assert split.propellant_fraction == pytest.approx(0.9)
    assert split.mass_ratio == pytest.approx(10.0)


def test_a_rocket_with_no_propellant_is_all_structure():
    split = MassSplit(dry_t=10.0, propellant_t=0.0)
    assert split.propellant_fraction == pytest.approx(0.0)
    assert split.mass_ratio == pytest.approx(1.0)


def test_an_empty_vehicle_does_not_divide_by_zero():
    split = MassSplit(dry_t=0.0, propellant_t=0.0)
    assert split.propellant_fraction == 0.0
    assert split.mass_ratio == 0.0


@pytest.mark.parametrize("mode", list(Mode))
def test_the_cutaway_paints_from_the_palette(mode: Mode):
    svg = rocket_cutaway(dry_t=10.0, propellant_t=90.0, mode=mode)
    assert colour(Series.PROPELLANT, mode) in svg
    assert colour(Series.STRUCTURE, mode) in svg


def test_the_cutaway_carries_a_text_alternative():
    svg = rocket_cutaway(dry_t=10.0, propellant_t=90.0)
    assert 'role="img"' in svg
    assert "90% propellant" in svg


def test_a_rocket_with_empty_tanks_draws_no_flame():
    # The flame group, not the keyframes: the stylesheet is emitted either way
    # and it is the drawn element that a reader would see.
    assert '<g class="cutaway-flame">' not in rocket_cutaway(dry_t=10.0, propellant_t=0.0)
    assert '<g class="cutaway-flame">' in rocket_cutaway(dry_t=10.0, propellant_t=1.0)


def test_the_fill_rises_with_the_propellant_fraction():
    # The fill is a rect whose height is what the reader actually reads, so a
    # fuller rocket must produce a taller one.
    def fill_height(propellant: float) -> float:
        svg = rocket_cutaway(dry_t=10.0, propellant_t=propellant, uid="probe")
        after = svg.split('class="probe-level"', 1)[1]
        return float(after.split('height="', 1)[1].split('"', 1)[0])

    assert fill_height(1.0) < fill_height(90.0) < fill_height(900.0)


def test_two_cutaways_on_one_page_do_not_share_keyframes():
    first = rocket_cutaway(dry_t=10.0, propellant_t=90.0, uid="alpha")
    second = rocket_cutaway(dry_t=10.0, propellant_t=90.0, uid="beta")
    assert "alpha-" in first and "beta-" not in first
    assert "beta-" in second and "alpha-" not in second


def test_cutaway_motion_can_be_turned_off_entirely():
    assert "@keyframes" not in rocket_cutaway(dry_t=10.0, propellant_t=90.0, animated=False)
    assert "@keyframes" in rocket_cutaway(dry_t=10.0, propellant_t=90.0, animated=True)


@pytest.mark.parametrize(
    "svg",
    [rocket_cutaway(dry_t=10.0, propellant_t=90.0), source()],
    ids=["cutaway", "mark"],
)
def test_readers_who_asked_for_less_motion_get_none(svg: str):
    assert "prefers-reduced-motion" in svg


def test_the_mark_is_well_formed_xml():
    # It is shipped as a file and inlined into a page, so a stray unclosed tag
    # would break the document around it rather than merely itself.
    root = ET.fromstring(source())
    assert root.tag.endswith("svg")
    assert root.get("viewBox")


def test_the_mark_takes_its_body_colour_from_whatever_holds_it():
    # The body inherits rather than hard-coding a colour. That is the whole
    # reason this can be one file rather than a light copy and a dark copy.
    assert "currentColor" in source()


def test_the_mark_still_reads_as_a_plain_image():
    # In the README it is an <img>, so there is no page to inherit from and
    # currentColor would come out black against a dark theme. The file has to
    # name a colour for that case, in both schemes.
    assert "prefers-color-scheme: dark" in source()
    assert "#0b0b0b" in source() and "#ffffff" in source()


@pytest.mark.parametrize("mode", list(Mode))
def test_the_app_overrides_that_default_rather_than_inheriting(mode: Mode):
    # A declared value blocks inheritance, so the app has to state both. It
    # knows better than the file does: Streamlit's theme is the reader's own
    # choice and need not agree with what the operating system reports.
    styled = mark(mode=mode)
    assert f"color:{INK_PRIMARY[mode]}" in styled
    assert f"--ship-gap:{SURFACE[mode]}" in styled


@pytest.mark.parametrize("mode", list(Mode))
def test_the_override_is_specific_enough_to_win(mode: Mode):
    # The file styles itself through `.ship-mark`, one class deep. The app's
    # rule has to be deeper or the mark ignores it and follows the OS instead.
    assert f".ship-mark-{'mark'} svg{{" in mark(mode=mode)
    assert ".ship-mark {" in source()


def test_two_marks_at_different_sizes_keep_their_own_dimensions():
    small = mark(height=28, uid="small")
    large = mark(height=140, uid="large")
    assert ".ship-mark-small svg{height:28px" in small
    assert ".ship-mark-large svg{height:140px" in large


def test_the_mark_is_named_for_the_project():
    assert "Starship Physics Lab" in source()
    assert ASSET_NAME == "logo.svg"


class TestSurvivesTheMarkdownRenderer:
    """Drawings have to survive the markdown renderer they are handed to.

    ``st.markdown`` parses markdown first and only then honours
    ``unsafe_allow_html``. Any line indented four spaces or more is taken for a
    code block, so multi-line SVG reaches the page as literal source. That is
    not a hypothetical: both the mark and the cutaway shipped that way until a
    browser check caught them, and nothing in the unit tests noticed, because
    the strings were perfectly correct SVG.
    """

    def test_flattening_drops_comments_and_newlines(self):
        flattened = inline("<svg>\n  <!-- a note -->\n    <rect/>\n</svg>")
        assert flattened == "<svg> <rect/> </svg>"

    @pytest.mark.parametrize(
        "markup",
        [mark(), rocket_cutaway(dry_t=10.0, propellant_t=90.0)],
        ids=["mark", "cutaway"],
    )
    def test_nothing_reaches_the_page_on_more_than_one_line(self, markup: str):
        assert "\n" not in markup

    @pytest.mark.parametrize(
        "markup",
        [mark(), rocket_cutaway(dry_t=10.0, propellant_t=90.0)],
        ids=["mark", "cutaway"],
    )
    def test_no_run_of_spaces_could_be_read_as_an_indent(self, markup: str):
        assert "    " not in markup


class TestTableStriping:
    """Markdown tables get alternating row shading, applied once per page.

    Nine chapters render a table through `labbook.tables`, and Streamlit turns
    each into a plain HTML `<table>` with no banding at all. Long rows are hard
    to read across without it, and the fleet table is thirteen rows by up to
    twenty-one columns.
    """

    def test_it_is_a_single_line(self):
        # st.markdown parses markdown before it honours unsafe_allow_html, and
        # four spaces of indentation would turn the whole thing into a code block.
        style = table_style()
        assert "\n" not in style
        assert "    " not in style

    def test_it_shades_alternate_rows(self):
        assert "nth-child(even)" in table_style()

    def test_it_works_in_both_themes_without_being_told_which(self):
        """A translucent grey darkens a light row and lightens a dark one.

        The alternative is passing the mode in, which would make every caller
        responsible for something the browser already knows.
        """
        style = table_style()
        assert "rgba(" in style
        assert "#" not in style, "a fixed colour would be wrong in one theme"

    def test_it_only_touches_tables(self):
        assert style_targets_only_tables(table_style())


def style_targets_only_tables(style: str) -> bool:
    """Every selector in the block must be scoped to a table element.

    A stray global selector in a style injected on every page is the kind of
    thing that quietly restyles a widget three chapters away.
    """
    body = style[style.index(">") + 1 : style.rindex("</style>")]
    selectors = [rule.split("{")[0].strip() for rule in body.split("}") if "{" in rule]
    return all("table" in selector for selector in selectors)
