"""Test that the agent skill lists exactly the available twill commands."""

import re
from pathlib import Path

import pytest

from twill import commands

SKILL_FILE = Path(__file__).parent.parent / "skills" / "twill" / "SKILL.md"

# names in commands.__all__ that are not twill commands
NOT_COMMANDS = {"browser", "options"}


def skill_commands() -> set[str]:
    """Get all commands and aliases listed in the cheat sheet of the skill."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- commands:start -->\n(.*?)<!-- commands:end -->", text, re.S
    )
    assert match, "command cheat sheet not found"
    names: set[str] = set()
    for row in match.group(1).splitlines()[2:]:  # skip header and separator
        cells = row.split("|")
        assert len(cells) == 5, f"invalid row: {row}"
        # first column: signature, second column: aliases
        for code in re.findall(r"`([^`]+)`", cells[1] + cells[2]):
            names.add(code.split()[0])
    return names


@pytest.mark.skipif(not SKILL_FILE.exists(), reason="skill not available")
def test_skill_lists_all_commands():
    available = set(commands.__all__) - NOT_COMMANDS
    listed = skill_commands()
    assert not listed - available, "unknown commands in the skill"
    assert not available - listed, "commands missing in the skill"
