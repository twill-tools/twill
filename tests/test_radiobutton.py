import pytest

from twill import browser, commands, namespaces
from twill.errors import TwillException


def test_switch_buttons(url: str):
    namespaces.new_local_dict()
    commands.reset_browser()

    with pytest.raises(TwillException):
        browser.title  # noqa: B018

    commands.go(url)
    commands.go("/test_radiobuttons")

    commands.submit()
    assert "RADIOBUTTONTEST" not in browser.html

    for x in ("one", "two", "three"):
        commands.fv("1", "radiobuttontest", x)
        commands.submit()
        assert f"RADIOBUTTONTEST: =={x}==" in browser.html


def test_empty_value(url: str):
    namespaces.new_local_dict()
    commands.reset_browser()

    commands.go(url)
    commands.go("/test_empty_values")

    # a checked radio button with an empty value sends an empty string
    commands.submit()
    assert "RADIOTEST: ====" in browser.html

    commands.fv("1", "radiotest", "one")
    commands.submit()
    assert "RADIOTEST: ==one==" in browser.html

    # the radio button without a value attribute has the value "on"
    commands.fv("1", "radiotest", "on")
    commands.submit()
    assert "RADIOTEST: ==on==" in browser.html

    # the radio button with the empty value can also be selected
    commands.fv("1", "radiotest", "")
    commands.submit()
    assert "RADIOTEST: ====" in browser.html
