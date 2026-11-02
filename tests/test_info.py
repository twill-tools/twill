from io import StringIO

import pytest

from twill import commands
from twill.errors import TwillAssertionError

from .utils import execute_script


def test(url: str):
    execute_script("test_info.twill", initial_url=url)


def test_info_without_content_type(url: str, output: StringIO):
    commands.go(f"{url}no_content_type")
    commands.code(200)
    with pytest.raises(TwillAssertionError):
        commands.header("Content-Type")
    commands.info()
    assert "\tContent type: None\n" in output.getvalue()
