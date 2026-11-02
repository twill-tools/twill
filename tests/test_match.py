"""Test setting __match__ with the assertion commands."""

import pytest

from twill import commands, namespaces


def get_match() -> str:
    """Get the value of the local variable __match__."""
    return namespaces.get_twill_glocals()[1]["__match__"]


@pytest.fixture
def root_page(url: str) -> None:
    """Go to the root page of the test server."""
    commands.go(url)
    commands.code(200)


@pytest.mark.usefixtures("root_page")
def test_match_with_group():
    assert commands.url(r"^(https?)://") == "http"
    assert get_match() == "http"
    assert commands.title(r"(\w+), world") == "Hello"
    assert get_match() == "Hello"
    assert commands.find(r"These are the (\w+) tests") == "twill"
    assert get_match() == "twill"
    assert commands.header("Content-Type", r"text/(\w+)") == "html"
    assert get_match() == "html"


@pytest.mark.usefixtures("root_page")
def test_match_with_optional_group_not_participating():
    assert commands.url("(ftp)?://") == ""
    assert get_match() == ""
    assert commands.title("(Bye)?world") == ""
    assert get_match() == ""
    assert commands.find("(not)?twill tests") == ""
    assert get_match() == ""
    assert commands.header("Content-Type", "(foo)?html") == ""
    assert get_match() == ""


@pytest.mark.usefixtures("root_page")
def test_match_with_xpath_results_that_are_not_elements():
    assert commands.find("//title", "x") == "Hello, world!"
    assert get_match() == "Hello, world!"
    assert commands.find("//title/text()", "x") == "Hello, world!"
    assert get_match() == "Hello, world!"
    assert commands.find("string(//title)", "x") == "Hello, world!"
    assert get_match() == "Hello, world!"
    assert commands.find("count(//title)", "x") == "1"
    assert get_match() == "1"
    with pytest.raises(commands.TwillAssertionError):
        commands.find("count(//nothing)", "x")
