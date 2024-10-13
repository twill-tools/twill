from pathlib import Path

import pytest

from twill import utils
from twill.errors import TwillException


def test_is_hidden_filename():
    is_hidden_filename = utils.is_hidden_filename
    assert not is_hidden_filename("foo")
    assert is_hidden_filename(".foo")
    assert not is_hidden_filename(".foo/bar")
    assert is_hidden_filename("foo/.bar")


def test_is_twill_filename():
    is_twill_filename = utils.is_twill_filename
    assert not is_twill_filename("foo")
    assert is_twill_filename("foo.twill")
    assert not is_twill_filename(".foo.twill")


def test_make_boolean():
    make_boolean = utils.make_boolean
    assert make_boolean(True)  # noqa: FBT003
    assert not make_boolean(False)  # noqa: FBT003
    assert make_boolean("true")
    assert not make_boolean("false")
    assert make_boolean(1)
    assert not make_boolean(0)
    assert make_boolean("1")
    assert not make_boolean("0")
    assert make_boolean("+")
    assert not make_boolean("-")
    with pytest.raises(TwillException):
        make_boolean("no")


def test_make_twill_filename():
    make_twill_filename = utils.make_twill_filename
    assert make_twill_filename("test_foo") == "test_foo"
    assert make_twill_filename("../tests/test_foo") == str(
        Path("../tests/test_foo")
    )
    assert make_twill_filename("test_basic") == "test_basic.twill"
    assert make_twill_filename("../tests/test_basic") == str(
        Path("../tests/test_basic.twill")
    )


def test_trunc():
    trunc = utils.trunc
    assert trunc("hello, world!", 12) == "hello, w ..."
    assert trunc("hello, world!", 13) == "hello, world!"
