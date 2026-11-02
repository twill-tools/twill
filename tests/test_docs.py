"""Test that the help texts and docs use the correct command names."""

import re
from pathlib import Path

import pytest

from twill import commands

COMMANDS_DOC = Path(__file__).parent.parent / "docs" / "commands.rst"

# names in commands.__all__ that are not twill commands
NOT_COMMANDS = {"browser", "options"}

COMMAND_NAMES = sorted(set(commands.__all__) - NOT_COMMANDS)


@pytest.mark.parametrize("name", COMMAND_NAMES)
def test_help_text_starts_with_command_name(name: str):
    fn = getattr(commands, name)
    if fn.__name__ != name:
        return  # an alias, the help text belongs to the original command
    first_line = fn.__doc__.lstrip().splitlines()[0]
    assert first_line.split()[:2] == [">>", name]


@pytest.mark.skipif(not COMMANDS_DOC.exists(), reason="docs not available")
def test_documented_commands_exist():
    text = COMMANDS_DOC.read_text(encoding="utf-8")
    # command entries look like "**name** -- ..." or "**name** *<arg>* ..."
    documented = set(
        re.findall(r"^\*\*(\w+)\*\* (?:--|\*)", text, re.MULTILINE)
    )
    documented = {name for name in documented if not name.startswith("__")}
    assert documented, "no commands found in the docs"
    assert not documented - set(COMMAND_NAMES), "unknown commands in the docs"
