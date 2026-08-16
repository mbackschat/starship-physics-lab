"""The physics core speaks one unit per quantity, and says so in its names.

Rule 2 in CLAUDE.md is that `src/rocketry/` is SI throughout and conversion
happens exactly once, at the presentation edge. Two functions had quietly opted
out: `orbital_velocity` took kilometres and `StagingModel` took km/h. Nothing
computed wrongly for a caller who read the signature, but `payload_at(1666.7)`
returned -84.8 t where the same speed as 6,000 km/h returned 56.7 t, and a rule
the code does not follow is not a rule.

This walks the source rather than checking those two, because the next one will
be somewhere else.
"""

import ast
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[1] / "src" / "rocketry"

FOREIGN_SUFFIXES = ("_km", "_kmh", "_mph", "_ft", "_mi", "_lb", "_lbf", "_kn", "_kg")
"""Unit suffixes that mean a name is not in this project's house units.

House units are tonnes, m/s, metres, seconds and tonnes-force. Tonnes and
tonnes-force are not SI either, which is the honest reading of rule 2: one unit
per quantity, chosen once, and converted only at the edge.
"""

DATA_BOUNDARY = {
    "staging_speed_kmh",
    "max_velocity_kmh",
    "mass_kg",
}
"""Fields that store what a source published, in the unit it published it in.

The library normalises most source units on the way in. These three are
descriptive rather than inputs to any calculation: nothing in the stage walk or
the ascent integrator reads them, so a wrong one can move a chart label and
never a result. Naming the unit is then the point rather than the problem.

That is the test for anything added here. If a value reaches a calculation, it
converts at the library boundary instead.
"""


def _annotated_names(tree: ast.Module) -> list[tuple[str, int]]:
    """Every name that carries a type annotation, with its line.

    Covers function parameters and class-level fields alike, which is what makes
    this catch a dataclass attribute as readily as an argument.

    Args:
        tree: Parsed module.

    Returns:
        Pairs of name and line number.
    """
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.append((node.target.id, node.lineno))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                found.append((arg.arg, arg.lineno))
    return found


@pytest.mark.parametrize("path", sorted(CORE.glob("*.py")), ids=lambda p: p.name)
def test_the_core_names_nothing_in_foreign_units(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders = [
        f"{path.name}:{line} {name}"
        for name, line in _annotated_names(tree)
        if name not in DATA_BOUNDARY and name.endswith(FOREIGN_SUFFIXES)
    ]
    assert offenders == [], (
        "these take or store a unit the core does not use. Convert at the call "
        f"site, or add the name to DATA_BOUNDARY with a reason: {offenders}"
    )


def test_the_allowlist_is_still_needed():
    """An exemption that no longer applies should be deleted, not carried."""
    source = "\n".join(p.read_text(encoding="utf-8") for p in CORE.glob("*.py"))
    for name in DATA_BOUNDARY:
        assert name in source, f"{name} is gone; drop it from DATA_BOUNDARY"
