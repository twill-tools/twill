import pytest

import twill
from twill import browser, commands, namespaces
from twill.errors import TwillException


def test_select_multiple(url: str):
    namespaces.new_local_dict()
    commands.reset_browser()

    with pytest.raises(TwillException):
        browser.title  # noqa: B018

    commands.go(url)
    commands.go("/test_checkboxes")

    commands.fv("1", "checkboxtest", "one")
    commands.fv("1", "checkboxtest", "two")
    commands.fv("1", "checkboxtest", "three")

    commands.fv("1", "checkboxtest", "-one")
    commands.fv("1", "checkboxtest", "-two")
    commands.fv("1", "checkboxtest", "-three")

    commands.submit()
    assert "CHECKBOXTEST" not in browser.html

    commands.fv("1", "checkboxtest", "+one")
    commands.fv("1", "checkboxtest", "+two")
    commands.fv("1", "checkboxtest", "+three")

    commands.submit()
    assert "CHECKBOXTEST: ==one,two,three==" in browser.html

    commands.fv("1", "checkboxtest", "-one")
    commands.fv("1", "checkboxtest", "-two")
    commands.fv("1", "checkboxtest", "-three")

    commands.submit()
    assert "CHECKBOXTEST" not in browser.html


def test_select_single(url: str):
    namespaces.new_local_dict()
    commands.reset_browser()
    browser = twill.browser
    with pytest.raises(TwillException):
        browser.title  # noqa: B018

    commands.go(url)
    commands.go("/test_checkboxes")

    # Should not be able to use a bool style for when
    # there are multiple checkboxes
    for x in ("1", "0", "True", "False"):
        with pytest.raises(KeyError):
            commands.fv("1", "checkboxtest", x)


def test_empty_value(url: str):
    namespaces.new_local_dict()
    commands.reset_browser()

    commands.go(url)
    commands.go("/test_empty_values")

    # a checked checkbox with an empty value sends an empty string,
    # a checked checkbox without a value attribute sends "on"
    commands.submit()
    assert "CHECKBOXTEST: ====" in browser.html
    assert "DEFAULTTEST: ==on==" in browser.html

    commands.fv("1", "checkboxtest", "+one")
    commands.fv("1", "defaulttest", "False")
    commands.submit()
    assert "CHECKBOXTEST: ==,one==" in browser.html
    assert "DEFAULTTEST" not in browser.html

    # the checkbox with the empty value can also be unchecked,
    # the checkbox without a value attribute has the value "on"
    commands.fv("1", "checkboxtest", "+one")
    commands.fv("1", "checkboxtest", "-")
    commands.fv("1", "checkboxtest", "+on")
    commands.fv("1", "defaulttest", "True")
    commands.submit()
    assert "CHECKBOXTEST: ==one,on==" in browser.html
    assert "DEFAULTTEST: ==on==" in browser.html
