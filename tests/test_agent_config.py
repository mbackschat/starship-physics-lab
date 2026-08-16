"""Skills and the agent-facing aliases have to survive being moved.

Everything here is instructions rather than code, so nothing about it fails
loudly. A skill whose links rotted still loads, and sends whoever reads it to a
file that is not there. That happened once already: moving a slash command into
a skill put it one directory deeper and every relative link broke silently.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
LINK = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#\s]+)\)")


def front_matter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---\n"), f"{path} has no front matter"
    closing = text.index("\n---\n", 3)
    return yaml.safe_load(text[4:closing])


def test_there_are_skills_to_check():
    assert SKILLS, "no skills found"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_a_skill_declares_a_name_matching_its_directory(skill: Path):
    declared = front_matter(skill).get("name")
    assert declared == skill.parent.name, (
        f"{skill} declares {declared!r} but lives in {skill.parent.name!r}"
    )


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_a_skill_says_when_to_use_it(skill: Path):
    # Skills load on description match, so a description that only says what
    # the skill is will never be reached by the task that needs it.
    description = front_matter(skill).get("description", "")
    assert len(description) > 80, f"{skill} needs a fuller description to be discoverable"
    assert "use" in description.lower(), f"{skill} does not say when to use it"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_every_link_in_a_skill_resolves(skill: Path):
    broken = [
        target
        for target in LINK.findall(skill.read_text())
        if not (skill.parent / target).resolve().exists()
    ]
    assert not broken, f"{skill} links to files that do not exist: {broken}"


def test_the_agent_aliases_are_symlinks_rather_than_copies():
    # Copies drift. Both of these exist so other agents read the same file, and
    # a copy would quietly become a second, wrong source of truth.
    for alias, target in (("AGENTS.md", "CLAUDE.md"), (".codex", ".claude")):
        path = ROOT / alias
        assert path.is_symlink(), f"{alias} should be a symlink to {target}"
        assert path.readlink().as_posix() == target, f"{alias} points somewhere unexpected"
        assert path.exists(), f"{alias} is a symlink to nothing"
