"""Skills and the agent-facing aliases have to survive being moved.

Everything here is instructions rather than code, so nothing about it fails
loudly. A skill whose links rotted still loads, and sends whoever reads it to a
file that is not there. That happened once already: moving a slash command into
a skill put it one directory deeper and every relative link broke silently.
"""

import re
from pathlib import Path
from typing import ClassVar

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


class TestTheReadmeDescribesTheRepositoryThatExists:
    """A hand-written directory listing goes stale the first time one is added.

    The knowledge base was built, and the README went on describing a repository
    without one: `raw/` and `docs/knowledge/` were missing from its layout block
    while `studies/` and `assets/` were listed. Nothing failed, because prose
    does not fail.
    """

    ROOT = Path(__file__).resolve().parents[1]

    IGNORED: ClassVar[set[str]] = {"docs", "src", "tests"}
    """Directories the layout block deliberately does not name at the top level.

    `docs/` and `src/` appear through their subdirectories instead, which the
    block names individually because that is where the meaning is. Tests need no
    tour.

    Everything beginning with a dot is skipped as well, without listing it:
    tooling, caches and agent configuration all live there, and enumerating them
    would rot every time a tool changed its cache directory.
    """

    def _layout(self) -> str:
        readme = (self.ROOT / "README.md").read_text()
        start = readme.index("## Layout")
        return readme[start : readme.index("```", readme.index("```", start) + 3)]

    def test_every_top_level_directory_is_described(self):
        missing = [
            path.name
            for path in sorted(self.ROOT.iterdir())
            if path.is_dir()
            and not path.name.startswith(".")
            and path.name not in self.IGNORED
            and f"{path.name}/" not in self._layout()
        ]
        assert missing == [], f"README's layout block does not mention {missing}"

    def test_the_knowledge_base_is_described_where_a_reader_would_look(self):
        readme = (self.ROOT / "README.md").read_text()
        assert "docs/knowledge/" in readme
        assert "raw/" in readme
        assert "docs/knowledge-base.md" in readme, "link to the design, not just the pages"

    def test_it_does_not_describe_directories_that_are_gone(self):
        layout = self._layout()
        named = [
            line.split("/")[0].strip()
            for line in layout.splitlines()
            if "/" in line and not line.startswith("#") and not line.startswith("`")
        ]
        for name in named:
            if not name or name.startswith("("):
                continue
            assert (self.ROOT / name).exists(), f"README names {name}, which is not here"
