"""Test the command line options of the twill main function."""

import pytest

from twill import namespaces

from .utils import execute_main

ECHO_SCRIPT = 'echo "a=[${a}] b=[${b}]"\n'


def test_set_one_variable():
    code, output = execute_main(["-s", "a=foo"], ECHO_SCRIPT)
    assert code == 0
    assert "a=[foo] b=[${b}]" in output
    assert "a" not in namespaces.global_dict


def test_set_several_variables():
    code, output = execute_main(
        ["-s", "a=foo", "--set", "b=bar baz"], ECHO_SCRIPT
    )
    assert code == 0
    assert "a=[foo] b=[bar baz]" in output


def test_set_variables_for_all_scripts():
    code, output = execute_main(
        ["-s", "a=foo", "-s", "b=bar"], ECHO_SCRIPT, ECHO_SCRIPT
    )
    assert code == 0
    assert output.count("a=[foo] b=[bar]") == 2
    assert "2 of 2 files SUCCEEDED." in output


def test_set_variable_twice():
    code, output = execute_main(["-s", "a=foo", "-s", "a=bar"], ECHO_SCRIPT)
    assert code == 0
    assert "a=[bar]" in output


def test_set_variable_with_equal_sign():
    code, output = execute_main(["--set=a=b=c", "-s", "b=="], ECHO_SCRIPT)
    assert code == 0
    assert "a=[b=c] b=[=]" in output


def test_set_variable_to_empty_value():
    code, output = execute_main(["-s", "a=", "-s", "b=bar"], ECHO_SCRIPT)
    assert code == 0
    assert "a=[] b=[bar]" in output


def test_set_variable_in_python_code():
    script = "run \"assert a == 'foo' and b == ''\"\n"
    code, output = execute_main(["-s", "a=foo", "-s", "b="], script)
    assert code == 0
    assert "1 of 1 files SUCCEEDED." in output


def test_set_variable_can_be_overridden_by_script():
    script = "setglobal a bar\n" + ECHO_SCRIPT
    code, output = execute_main(["-s", "a=foo"], script)
    assert code == 0
    assert "a=[bar]" in output


@pytest.mark.parametrize(
    ("arg", "message"),
    [
        ("1a=foo", "invalid variable name '1a'"),
        ("a-b=foo", "invalid variable name 'a-b'"),
        ("=foo", "invalid variable name ''"),
        ("class=foo", "invalid variable name 'class'"),
        ("__builtins__=foo", "invalid variable name '__builtins__'"),
        ("url=foo", "'url' is the name of a twill command"),
        ("a", "missing '=' in 'a'"),
    ],
)
def test_set_variable_with_invalid_argument(
    arg: str, message: str, capsys: pytest.CaptureFixture[str]
):
    code, output = execute_main(["-s", arg], ECHO_SCRIPT)
    assert code == 2
    assert not output
    assert f"argument -s/--set: {message}" in capsys.readouterr().err
