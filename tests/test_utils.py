from pathlib import Path

import pytest
from lxml.etree import fromstring
from lxml.html import FormElement, InputElement, SelectElement, xhtml_parser
from lxml.html import fromstring as lxml_fromstring

from twill import utils
from twill.errors import TwillException
from twill.utils import (
    CheckboxGroup,
    RadioGroup,
    html_to_tree,
    set_form_control_value,
)


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


def test_make_twill_filename(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(Path(__file__).parent)
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


def _form(html: str) -> FormElement:
    """Get the form element created from the given form HTML."""
    form = html_to_tree(f"<form>{html}</form>")
    assert isinstance(form, FormElement)
    return form


def _select(html: str) -> SelectElement:
    """Get the select element with the name "s" from the given form HTML."""
    control = _form(html).inputs["s"]
    assert isinstance(control, SelectElement)
    return control


def test_set_select_value_with_whitespace():
    html = (
        '<select name="s"><option value="a">A</option>'
        '<option value=" ">Benutzerstoffe</option></select>'
    )
    control = _select(html)
    assert control.value == "a"
    set_form_control_value(control, " ")
    assert control.value == " "
    control = _select(html)
    set_form_control_value(control, "Benutzerstoffe")
    assert control.value == " "
    control = _select(html)
    set_form_control_value(control, "")
    assert control.value == " "


def test_set_select_value_with_padded_value():
    html = (
        '<select name="s"><option value="a">A</option>'
        '<option value=" b ">B</option></select>'
    )
    for value in ("b", " b ", "B"):
        control = _select(html)
        set_form_control_value(control, value)
        assert control.value == " b "


def test_set_select_value_without_value_attribute():
    html = (
        '<select name="s"><option value="a">A</option>'
        "<option> Text only </option></select>"
    )
    control = _select(html)
    set_form_control_value(control, "Text only")
    assert control.value == "Text only"


def test_set_select_value_in_optgroup():
    html = (
        '<select name="s"><optgroup label="G"><option value="x">X</option>'
        '</optgroup><option value="y">Y</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "X")
    assert control.value == "x"
    control = _select(html)
    set_form_control_value(control, "y")
    assert control.value == "y"
    set_form_control_value(control, "x")
    assert control.value == "x"
    set_form_control_value(control, "Y")
    assert control.value == "y"


def test_set_select_value_in_optgroup_not_shifted():
    # options and optgroups were previously paired with the wrong values
    html = (
        '<select name="s"><option value="a">A</option>'
        '<optgroup label="G"><option value="b">B</option>'
        '<option value="c">C</option></optgroup>'
        '<option value="d">D</option></select>'
    )
    for name, value in zip("ABCD", "abcd", strict=True):
        control = _select(html)
        set_form_control_value(control, name)
        assert control.value == value
        control = _select(html)
        set_form_control_value(control, value)
        assert control.value == value


def test_set_select_invalid_value():
    html = (
        '<select name="s"><optgroup label="G"><option value="x">X</option>'
        '</optgroup><option value="y">Y</option></select>'
    )
    control = _select(html)
    for value in ("G", "z", "-z", "+z"):
        with pytest.raises(TwillException, match="invalid value"):
            set_form_control_value(control, value)
    assert control.value == "x"


def test_set_multiselect_value():
    html = (
        '<select name="s" multiple><optgroup label="G">'
        '<option value=" a ">A</option><option value="b">B</option>'
        '</optgroup><option value="c">C</option></select>'
    )
    control = _select(html)
    assert set(control.value) == set()
    set_form_control_value(control, "A")
    assert set(control.value) == {" a "}
    set_form_control_value(control, "+c")
    assert set(control.value) == {" a ", "c"}
    set_form_control_value(control, "B")
    assert set(control.value) == {" a ", "b", "c"}
    set_form_control_value(control, "-a")
    assert set(control.value) == {"b", "c"}
    set_form_control_value(control, "-C")
    assert set(control.value) == {"b"}
    set_form_control_value(control, "-c")
    assert set(control.value) == {"b"}
    set_form_control_value(control, "+ a ")
    assert set(control.value) == {" a ", "b"}


def test_deselect_single_select_value():
    html = (
        '<select name="s"><option value="">Choose</option>'
        '<option value="a">A</option><option value="b">B</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "b")
    assert control.value == "b"
    set_form_control_value(control, "-a")
    assert control.value == "b"
    set_form_control_value(control, "-B")
    assert control.value == ""
    html = (
        '<select name="s"><option value="a">A</option>'
        '<option value="b" selected>B</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "-b")
    assert control.value == "a"
    set_form_control_value(control, "-a")
    assert control.value == "a"
    with pytest.raises(TwillException, match="invalid value"):
        set_form_control_value(control, "-c")


def test_set_select_value_prefers_exact_match():
    html = (
        '<select name="s"><option value="b ">X</option>'
        '<option value="b">Y</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "b")
    assert control.value == "b"
    set_form_control_value(control, "b ")
    assert control.value == "b "
    html = (
        '<select name="s"><option value="a">A</option>'
        '<option value=" ">Space</option><option value="">None</option>'
        "</select>"
    )
    control = _select(html)
    set_form_control_value(control, "")
    assert control.value == ""


def test_set_select_value_with_leading_minus():
    html = (
        '<select name="s"><option value="-1">Choose</option>'
        '<option value="1">One</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "1")
    assert control.value == "1"
    set_form_control_value(control, "-1")
    assert control.value == "-1"
    set_form_control_value(control, "+1")
    assert control.value == "1"
    set_form_control_value(control, "--1")
    assert control.value == "1"


def test_set_select_value_with_duplicate_values():
    html = (
        '<select name="s" multiple><option value="x">X1</option>'
        '<option value="x" selected>X2</option></select>'
    )
    control = _select(html)
    assert set(control.value) == {"x"}
    set_form_control_value(control, "-X2")
    assert set(control.value) == set()
    set_form_control_value(control, "X2")
    assert set(control.value) == {"x"}
    first_option, second_option = control
    assert first_option.get("selected") is None
    assert second_option.get("selected") is not None
    # deselecting by value must find the selected option
    set_form_control_value(control, "-x")
    assert set(control.value) == set()
    assert second_option.get("selected") is None
    # selecting by value uses the first option
    set_form_control_value(control, "x")
    assert set(control.value) == {"x"}
    assert first_option.get("selected") is not None
    assert second_option.get("selected") is None
    html = (
        '<select name="s"><option value="x">X1</option>'
        '<option value="x" selected>X2</option></select>'
    )
    control = _select(html)
    first_option, second_option = control
    set_form_control_value(control, "-x")
    assert first_option.get("selected") is None
    assert second_option.get("selected") is None
    set_form_control_value(control, "X2")
    assert first_option.get("selected") is None
    assert second_option.get("selected") is not None
    set_form_control_value(control, "x")
    assert first_option.get("selected") is not None
    assert second_option.get("selected") is None


def test_set_select_value_by_visible_text_or_label():
    html = (
        '<select name="s"><option value="a"> A </option>'
        '<option value="b"><b>Bold</b>  text</option>'
        '<option value="c" label="Cee">C</option></select>'
    )
    control = _select(html)
    set_form_control_value(control, "Bold text")
    assert control.value == "b"
    set_form_control_value(control, "Cee")
    assert control.value == "c"
    set_form_control_value(control, "C")
    assert control.value == "c"
    with pytest.raises(TwillException, match="invalid value"):
        set_form_control_value(control, "")
    assert control.value == "c"


def test_set_select_value_ignores_disabled_options():
    html = (
        '<select name="s"><option value="a">A</option>'
        '<option value="b" disabled>B</option>'
        '<optgroup label="G" disabled><option value="c">C</option></optgroup>'
        "</select>"
    )
    control = _select(html)
    for value in ("b", "B", "c", "C", "-b"):
        with pytest.raises(TwillException, match="invalid value"):
            set_form_control_value(control, value)
    assert control.value == "a"


def test_set_select_value_with_xhtml_namespace():
    xhtml = (
        '<form xmlns="http://www.w3.org/1999/xhtml"><select name="s">'
        '<option value="a">A</option><option value="b">B</option>'
        "</select></form>"
    )
    form = fromstring(xhtml, xhtml_parser)
    control = form[0]
    assert isinstance(control, SelectElement)
    set_form_control_value(control, "B")
    assert control.value == "b"


def test_value_of_checkable_inputs():
    form = _form(
        '<input type="checkbox" name="a" value="x" checked>'
        '<input type="checkbox" name="b" value="" checked>'
        '<input type="checkbox" name="c" checked>'
        '<input type="checkbox" name="d" value="x">'
        '<input type="radio" name="e" value="" checked>'
        '<input type="radio" name="f" checked>'
        '<input type="radio" name="g" value="">'
        '<input type="text" name="h" value="">'
        '<input type="text" name="i">'
    )
    inputs = form.inputs
    assert inputs["a"].value == "x"
    assert inputs["b"].value == ""
    assert inputs["c"].value == "on"
    assert inputs["d"].value is None
    assert inputs["e"].value == ""
    assert inputs["f"].value == "on"
    assert inputs["g"].value is None
    assert inputs["h"].value == ""
    assert inputs["i"].value is None


def test_set_value_of_checkable_inputs():
    form = _form(
        '<input type="checkbox" name="a" value="" checked>'
        '<input type="radio" name="b" value="">'
        '<input type="text" name="c" value="x">'
    )
    inputs = form.inputs
    a, b, c = inputs["a"], inputs["b"], inputs["c"]
    assert isinstance(a, InputElement)
    assert isinstance(b, InputElement)
    assert isinstance(c, InputElement)
    a.value = None
    assert not a.checked
    assert a.value is None
    a.value = "y"
    assert a.checked
    assert a.value == "y"
    del a.value
    assert not a.checked
    assert a.get("value") == "y"
    b.value = True
    assert b.checked
    assert b.value == ""
    c.value = "y"
    assert c.value == "y"
    del c.value
    assert c.value is None
    assert c.get("value") is None
    with pytest.raises(TypeError):
        c.value = None


def test_values_of_checkable_groups():
    form = _form(
        '<input type="radio" name="r" value="" checked>'
        '<input type="radio" name="r" value="one">'
        '<input type="radio" name="r">'
        '<input type="checkbox" name="c" value="" checked>'
        '<input type="checkbox" name="c" value="one" checked>'
        '<input type="checkbox" name="c">'
    )
    inputs = form.inputs
    assert inputs["r"].value == ""
    assert set(inputs["c"].value) == {"", "one"}
    radios = RadioGroup(
        el for el in inputs if isinstance(el, InputElement) and el.name == "r"
    )
    assert radios.value == ""
    assert radios.value_options == ["", "one", "on"]
    radios.value = "on"
    assert radios.value == "on"
    assert form.form_values() == [("r", "on"), ("c", ""), ("c", "one")]
    radios.value = ""
    assert radios.value == ""
    with pytest.raises(ValueError, match="no radio input"):
        radios.value = "two"
    assert radios.value == ""
    del radios.value
    assert radios.value is None
    checkboxes = CheckboxGroup(
        el for el in inputs if isinstance(el, InputElement) and el.name == "c"
    )
    assert set(checkboxes.value) == {"", "one"}
    assert checkboxes.value_options == ["", "one", "on"]
    checkboxes.value.add("on")
    checkboxes.value.remove("")
    assert set(checkboxes.value) == {"one", "on"}
    assert form.form_values() == [("c", "one"), ("c", "on")]
    with pytest.raises(KeyError, match="already unchecked"):
        checkboxes.value.remove("")
    with pytest.raises(KeyError, match="No checkbox"):
        checkboxes.value.add("two")
    checkboxes.value = ["", "on"]
    assert set(checkboxes.value) == {"", "on"}
    del checkboxes.value
    assert not set(checkboxes.value)


def test_form_values_with_empty_checkable_values():
    form = _form(
        '<input type="radio" name="r" value="" checked>'
        '<input type="radio" name="r" value="one">'
        '<input type="checkbox" name="c" value="" checked>'
        '<input type="checkbox" name="c" value="one" checked>'
        '<input type="checkbox" name="d" checked>'
        '<input type="checkbox" name="e" value="x">'
    )
    assert form.form_values() == [
        ("r", ""),
        ("c", ""),
        ("c", "one"),
        ("d", "on"),
    ]


@pytest.mark.xfail(
    reason="lxml bug 1600773 is not fixed in the installed version",
    strict=False,
)
def test_form_values_with_empty_checkable_values_in_lxml():
    # when this test passes, the workaround in twill may be removed
    form = lxml_fromstring(
        '<form><input type="radio" name="r" value="" checked></form>'
    )
    assert isinstance(form, FormElement)
    assert form.form_values() == [("r", "")]
