import re
from io import StringIO

import pytest

from twill import commands, namespaces
from twill.errors import TwillAssertionError

from .utils import execute_script


def test(url: str):
    execute_script("test_headers.twill", initial_url=url)


@pytest.fixture
def headers_page(url: str) -> None:
    """Go to a page that is sent with some custom response headers."""
    commands.go(
        f"{url}response_headers"
        "?X-Version=twill-3.4.0&X-Multi=one&X-Multi=two&X-Empty="
    )
    commands.code(200)


def get_match() -> str:
    """Get the value of the local variable __match__."""
    return namespaces.get_twill_glocals()[1]["__match__"]


@pytest.mark.usefixtures("headers_page")
def test_header_matches():
    assert commands.header("Content-Type", "^text/html") == "text/html"
    assert get_match() == "text/html"


@pytest.mark.usefixtures("headers_page")
def test_header_with_group():
    assert commands.header("X-Version", r"-(\d+\.\d+)") == "3.4"
    assert get_match() == "3.4"


@pytest.mark.usefixtures("headers_page")
def test_header_name_is_case_insensitive():
    assert commands.header("x-version", "twill") == "twill"
    assert commands.header("X-VERSION", "twill") == "twill"


@pytest.mark.usefixtures("headers_page")
def test_header_does_not_match():
    with pytest.raises(
        TwillAssertionError,
        match=re.escape(
            "response header 'X-Version' is 'twill-3.4.0';\n"
            "does not match 'mechanize'"
        ),
    ):
        commands.header("X-Version", "mechanize")


@pytest.mark.usefixtures("headers_page")
def test_header_is_missing():
    with pytest.raises(
        TwillAssertionError, match="no response header 'X-Missing'"
    ):
        commands.header("X-Missing", ".*")
    with pytest.raises(
        TwillAssertionError, match="no response header 'X-Missing'"
    ):
        commands.header("X-Missing")


@pytest.mark.usefixtures("headers_page")
def test_header_without_pattern():
    assert commands.header("X-Version") == "twill-3.4.0"
    assert get_match() == "twill-3.4.0"
    assert not commands.header("X-Empty")
    assert get_match() == ""


@pytest.mark.usefixtures("headers_page")
def test_header_sent_multiple_times():
    assert commands.header("X-Multi") == "one, two"
    assert commands.header("X-Multi", "^one, two$") == "one, two"
    assert commands.header("X-Multi", "two") == "two"


@pytest.mark.usefixtures("headers_page")
def test_show_headers(output: StringIO):
    commands.show_headers()
    lines = output.getvalue().splitlines()
    assert "Content-Type: text/html; charset=utf-8" in lines
    assert "X-Version: twill-3.4.0" in lines
    assert lines.index("X-Multi: one") + 1 == lines.index("X-Multi: two")
    assert "X-Empty: " in lines
    output.seek(0)
    output.truncate()
    commands.show("headers")
    assert output.getvalue().splitlines() == lines
