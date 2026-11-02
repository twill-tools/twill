"""Various ugly utility functions for twill.

Apart from various simple utility functions, twill's robust parsing
code is implemented in the ConfigurableParsingFactory class.
"""

import codecs
import os
import re
from collections.abc import Collection, Iterator, Sequence
from contextlib import suppress
from email.message import Message
from email.utils import collapse_rfc2231_value
from pathlib import Path
from typing import Any, Literal, NamedTuple, TypeAlias, TypeVar
from urllib.parse import unquote, urlsplit

from httpx import Headers, Response
from lxml.html import (
    XHTML_NAMESPACE,
    CheckboxValues,
    FormElement,
    HtmlElement,
    HtmlElementClassLookup,
    HTMLParser,
    InputElement,
    SelectElement,
    TextareaElement,
    fromstring,
)
from lxml.html import CheckboxGroup as _CheckboxGroup
from lxml.html import RadioGroup as _RadioGroup
from lxml.html import tostring as tree_to_html

try:
    import tidylib  # type: ignore[import-untyped]
except (ImportError, OSError):
    # ImportError can be raised when PyTidyLib package is not installed and
    # OSError can be raised when the HTML Tidy shared library is not installed
    tidylib = None

from . import log, twill_ext
from .errors import TwillException

__all__ = [
    "CheckboxGroup",
    "FieldElement",
    "FormElement",
    "HtmlElement",
    "InputElement",
    "Link",
    "RadioGroup",
    "Response",
    "ResultWrapper",
    "SelectElement",
    "Singleton",
    "TextareaElement",
    "UrlWithRealm",
    "filename_from_content_disposition",
    "gather_filenames",
    "get_equiv_refresh_interval",
    "html_to_tree",
    "is_hidden_filename",
    "is_twill_filename",
    "make_boolean",
    "make_int",
    "make_twill_filename",
    "print_form",
    "run_tidy",
    "safe_filename",
    "tree_to_html",
    "trunc",
    "unique_match",
]


class _InputElement(InputElement):
    """Input element with a fixed value property.

    For a checked checkbox or radio button, lxml returns "on" not only when
    the value attribute is missing, but also when it is empty, see
    https://bugs.launchpad.net/lxml/+bug/1600773. According to the HTML
    standard, browsers send an empty string in the latter case.

    Apart from this fix, the value property behaves exactly as in lxml.
    """

    @property
    def value(self) -> str | None:
        """Get the value of this element, using the value attribute.

        For a checkbox or radio button that is not checked, this is None.
        If it is checked and has no value attribute, this defaults to "on".
        """
        value = self.get("value")
        if self.checkable:
            if not self.checked:
                return None
            if value is None:
                return "on"
        return value

    @value.setter
    def value(self, value: str | bytes | bytearray | bool | None) -> None:
        """Set the value of this element.

        A checkbox or radio button is checked if the value is truthy and
        unchecked otherwise, and its value attribute is only changed if the
        value is a string. For all other inputs, the value must be a string.
        """
        if self.checkable:
            self.checked = bool(value)
            if value and isinstance(value, str):
                self.set("value", value)
        elif isinstance(value, (str, bytes, bytearray)):
            self.set("value", value)
        else:
            raise TypeError(f"Cannot set the value of an input to {value!r}")

    @value.deleter
    def value(self) -> None:
        """Uncheck a checkbox or radio button or remove the value attribute."""
        if self.checkable:
            self.checked = False
        elif "value" in self.attrib:
            del self.attrib["value"]


def _get_checkable_value(el: InputElement) -> str:
    """Get the value attribute of a checkbox or radio button.

    If the value attribute is missing, this is "on" like in a browser.
    """
    return el.get("value", "on")


class RadioGroup(_RadioGroup):
    """Group of radio buttons with the same name.

    Unlike in lxml, a radio button without a value attribute has the value
    "on" here, which is the default value used by browsers.
    """

    @property
    def value(self) -> str | None:
        """Get the value of the checked radio button, if any."""
        for el in self:
            if el.checked:
                return _get_checkable_value(el)
        return None

    @value.setter
    def value(self, value: str | None) -> None:
        """Check the radio button with the given value, uncheck the others."""
        checked_el = None
        if value is not None:
            for el in self:
                if _get_checkable_value(el) == value:
                    checked_el = el
                    break
            else:
                raise ValueError(
                    f"There is no radio input with the value {value!r}"
                )
        for el in self:
            el.checked = el is checked_el

    @value.deleter
    def value(self) -> None:
        """Uncheck all radio buttons."""
        self.value = None

    @property
    def value_options(self) -> list[str]:
        """Get the values of all radio buttons."""
        return [_get_checkable_value(el) for el in self]


class _CheckboxValues(CheckboxValues):
    """Values of the checked checkboxes in a group.

    Unlike in lxml, a checkbox without a value attribute has the value "on"
    here, which is the default value used by browsers.
    """

    def __iter__(self) -> Iterator[str]:
        """Iterate over the values of the checked checkboxes."""
        return iter(
            [_get_checkable_value(el) for el in self.group if el.checked]
        )

    def add(self, value: str) -> None:
        """Check the checkbox with the given value."""
        for el in self.group:
            if _get_checkable_value(el) == value:
                el.checked = True
                break
        else:
            raise KeyError(f"No checkbox with value {value!r}")

    def remove(self, value: str) -> None:
        """Uncheck the checkbox with the given value."""
        for el in self.group:
            if _get_checkable_value(el) == value:
                if not el.checked:
                    raise KeyError(
                        f"The checkbox with value {value!r}"
                        " was already unchecked"
                    )
                el.checked = False
                break
        else:
            raise KeyError(f"No checkbox with value {value!r}")


class CheckboxGroup(_CheckboxGroup):
    """Group of checkboxes with the same name.

    Unlike in lxml, a checkbox without a value attribute has the value
    "on" here, which is the default value used by browsers.
    """

    @property
    def value(self) -> _CheckboxValues:
        """Get a set-like object with the values of the checked checkboxes.

        The object can be modified to check or uncheck individual checkboxes.
        """
        return _CheckboxValues(self)

    @value.setter
    def value(self, value: str | Collection[str]) -> None:
        """Check the checkboxes with the given values, uncheck the others."""
        values = self.value
        values.clear()
        for item in value:
            values.add(item)

    @value.deleter
    def value(self) -> None:
        """Uncheck all checkboxes."""
        self.value.clear()

    @property
    def value_options(self) -> list[str]:
        """Get the values of all checkboxes."""
        return [_get_checkable_value(el) for el in self]


FieldElement: TypeAlias = (
    CheckboxGroup | InputElement | RadioGroup | SelectElement | TextareaElement
)


class _HtmlElementClassLookup(HtmlElementClassLookup):
    """Element class lookup that creates input elements with a fixed value."""

    def lookup(
        self,
        node_type: Literal["element", "comment", "PI", "entity"] | None,
        document: object,
        namespace: object,
        name: str,
    ) -> type[HtmlElement] | None:
        """Look up the element class for the given node."""
        if node_type == "element" and name.lower() == "input":
            return _InputElement
        return super().lookup(node_type, document, namespace, name)


_html_parser = HTMLParser()
_html_parser.set_element_class_lookup(_HtmlElementClassLookup())


def html_to_tree(
    html: str | bytes, base_url: str | None = None
) -> HtmlElement:
    """Parse the given HTML into an element tree.

    This works like lxml.html.fromstring(), but uses a parser that creates
    input elements with a fixed value property, see _InputElement above.
    """
    return fromstring(html, base_url=base_url, parser=_html_parser)


class Link(NamedTuple):
    """A link with some text and a URL."""

    text: str
    url: str


# Depending on the configuration, realms can be ignored
UrlWithRealm: TypeAlias = str | tuple[str, str]


# Stand-in for typing.Self, which needs Python 3.11.
# With Python >= 3.11, annotate Singleton.__new__ with "-> Self" instead.
SingletonType = TypeVar("SingletonType", bound="Singleton")


class Singleton:
    """A mixin class to create singleton objects."""

    def __new__(cls: type[SingletonType], *_args, **_kw) -> SingletonType:
        """Create a new instance."""
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        return it

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton."""
        cls.__it__ = None


class ResultWrapper:
    """Deal with request results, and present them in a unified form.

    These objects are returned by browser._journey()-wrapped functions.
    """

    def __init__(self, response: Response) -> None:
        """Initialize the result wrapper."""
        self.response = response
        self.encoding = response.encoding
        try:
            self.tree = html_to_tree(self.text)
        except ValueError:
            # may happen when there is an XML encoding declaration
            self.tree = html_to_tree(self.content)
        self.xpath = self.tree.xpath
        self._fix_forms()

    @property
    def url(self) -> str:
        """Get the URL of the result page."""
        return str(self.response.url)

    @property
    def http_code(self) -> int:
        """Get the HTTP status code of the result page."""
        return self.response.status_code

    @property
    def text(self) -> str:
        """Get the text of the result page."""
        return self.response.text

    @property
    def content(self) -> bytes:
        """Get the binary content of the result page."""
        return self.response.content

    @property
    def headers(self) -> Headers:
        """Get the headers of the result page."""
        return self.response.headers

    @property
    def filename(self) -> str | None:
        """Get a safe filename for the result page suggested by the server.

        The filename is taken from the Content-Disposition header if present,
        otherwise from the last segment of the URL path. Only the final path
        component is used, and hidden or empty names are rejected.
        """
        disposition = self.headers.get("Content-Disposition")
        if disposition:
            filename = safe_filename(
                filename_from_content_disposition(disposition)
            )
            if filename:
                return filename
        return safe_filename(unquote(urlsplit(self.url).path))

    @property
    def title(self) -> str | None:
        """Get the title of the result page."""
        try:
            return self.xpath("//title[1]/text()")[0]
        except IndexError:
            return None

    @property
    def links(self) -> list[Link]:
        """Get all links in the result page."""
        return [
            Link(a.text_content(), a.get("href"))
            for a in self.xpath("//a[@href]")
        ]

    def find_link(self, pattern: str) -> Link | None:
        """Find a link with a given pattern on the result page."""
        regex = re.compile(pattern)
        for link in self.links:
            if regex.search(link.text) or regex.search(link.url):
                return link
        return None

    def find_links(self, pattern: str) -> list[Link]:
        """Find all links with a given pattern on the result page."""
        regex = re.compile(pattern)
        return [
            link
            for link in self.links
            if regex.search(link.text) or regex.search(link.url)
        ]

    def form(self, name_or_num: str | int = 1) -> FormElement | None:
        """Get the form with the given name or number on the result page.

        Returns None if no such form can be found on the result page.
        """
        forms = self.forms

        if isinstance(name_or_num, str):
            # first, try ID
            for form in forms:
                form_id = form.get("id")
                if form_id and form_id == name_or_num:
                    return form

            # next, try regex with name
            regex = re.compile(name_or_num)
            for form in forms:
                name = form.get("name")
                if name and regex.search(name):
                    return form

        # last, try number
        try:
            num = int(name_or_num) - 1
            if not 0 <= num < len(forms):
                raise IndexError
        except (ValueError, IndexError):
            return None
        else:
            return forms[num]

    def _fix_forms(self) -> None:
        """Fix forms on the page for use with twill."""
        # put all stray fields into a form
        orphans = self.xpath("//input[not(ancestor::form)]")
        if orphans:
            form_parts = (
                [b"<form>"]
                + [tree_to_html(orphan) for orphan in orphans]
                + [b"</form>"]
            )
            self.forms = html_to_tree(b"".join(form_parts)).forms
            self.forms.extend(self.tree.forms)
        else:
            self.forms = self.tree.forms
        # convert all submit button elements to input elements, since
        # otherwise lxml will not recognize them as form input fields
        for form in self.forms:
            for button in form.xpath("//button[@type='submit']"):
                button.tag = "input"


def trunc(s: str | None, length: int) -> str:
    """Truncate a string to a given length.

    The string is truncated by cutting off the last (length-4) characters
    and replacing them with ' ...'
    """
    if s and len(s) > length:
        return s[: length - 4] + " ..."
    return s or ""


def print_form(form: FormElement, n: int) -> None:
    """Pretty-print the given form, with the assigned number."""
    info = log.info
    name = form.get("name")
    info("\nForm name=%s (#%d)", name, n) if name else info("\nForm #%d", n)

    if form.inputs is not None:
        info(
            "## __Name__________________"
            " __Type___ __ID________ __Value__________________"
        )

        for i, field in enumerate(form.inputs, 1):
            value = field.value
            value_options = getattr(field, "value_options", None)
            if value_options:
                items = ", ".join(
                    f"'{getattr(opt, 'name', opt)}'" for opt in value_options
                )
                value_displayed = f"{value} of {items}"
            else:
                value_displayed = f"{value}"
            field_name = field.name
            field_type = getattr(field, "type", "select")
            field_id = field.get("id")
            strings = (
                f"{i:2}",
                f"{trunc(field_name, 24):24}",
                f"{trunc(field_type, 9):9}",
                f"{trunc(field_id, 12):12}",
                trunc(value_displayed, 40),
            )
            info(" ".join(strings))
    info("")


def make_boolean(value: Any) -> bool:
    """Convert the input value into a boolean."""
    value = str(value).lower().strip()

    # true/false
    if value in ("true", "false"):
        return value == "true"

    # 0/nonzero
    try:
        ival = int(value)
    except ValueError:
        pass
    else:
        return bool(ival)

    # +/-
    if value in ("+", "-"):
        return value == "+"

    # on/off
    if value in ("on", "off"):
        return value == "on"

    raise TwillException(f"unable to convert '{value}' into true/false")


def make_int(value: Any) -> int:
    """Convert the input value into an int."""
    try:
        ival = int(value)
    except Exception as error:
        raise TwillException(
            f"unable to convert '{value}' into an int"
        ) from error
    return ival


def set_form_control_value(control: FieldElement, value: str) -> None:
    """Set the given control to the given value.

    The controls can be checkboxes, select elements etc.
    """
    if isinstance(control, InputElement):
        if control.checkable:
            try:
                boolean_value = make_boolean(value)
            except TwillException:
                # if there's more than one checkbox,
                # it should be a CheckboxGroup, see below.
                pass
            else:
                control.checked = boolean_value
        elif control.type not in ("submit", "image"):
            control.value = value

    elif isinstance(control, (TextareaElement, RadioGroup)):
        control.value = value

    elif isinstance(control, CheckboxGroup):
        if value.startswith("-"):
            value = value[1:]
            with suppress(KeyError):
                control.value.remove(value)
        else:
            control.value.add(value.removeprefix("+"))

    elif isinstance(control, SelectElement):
        # a value with a leading "+" or "-" selects or deselects an option,
        # unless the value matches an option as it is (such as "-1")
        options = _get_options(control)
        add = True
        option = _find_option(options, value)
        if option is None and value.startswith(("+", "-")):
            add = value.startswith("+")
            option = _find_option(options, value[1:], selected=not add)
        if option is None:
            raise TwillException("Attempt to set an invalid value")
        _select_option(control, options, option, add=add)

    else:
        raise TwillException("Attempt to set value on invalid control")


_xhtml_option_tag = f"{{{XHTML_NAMESPACE}}}option"


def _get_options(control: SelectElement) -> list[HtmlElement]:
    """Get all option elements of a select element.

    The options may be nested in optgroups and may have a namespace.
    """
    return [
        option
        for option in control.iter("option", _xhtml_option_tag)
        if isinstance(option, HtmlElement)
    ]


def _option_value(option: HtmlElement) -> str:
    """Get the value of an option element in the same way as lxml."""
    value = option.get("value")
    if value is None:
        value = (option.text or "").strip()
    return value


def _option_disabled(option: HtmlElement) -> bool:
    """Check whether the option element or its optgroup is disabled."""
    if option.get("disabled") is not None:
        return True
    parent = option.getparent()
    return (
        parent is not None
        and not isinstance(parent, SelectElement)
        and parent.get("disabled") is not None
    )


def _match_option(option: HtmlElement, value: str) -> int | None:
    """Check how well an option element matches the given value.

    Return 0 for an exact match of the option value, 1 for a match of the
    stripped option value, 2 for a match of the label or the visible text
    of the option, and None if the option does not match at all.
    """
    option_value = _option_value(option)
    if option_value == value:
        return 0
    if option_value.strip() == value:
        return 1
    if value:
        text = " ".join(option.text_content().split())
        if value in (option.get("label"), text):
            return 2
    return None


def _find_option(
    options: list[HtmlElement], value: str, *, selected: bool = False
) -> HtmlElement | None:
    """Find the option matching the given value.

    Disabled options are ignored, like in a browser. A match of the exact
    option value takes precedence over a match of the stripped option value,
    and this over a match of the label or the visible text of the option.
    Among equally good matches, the first one is used, unless selected
    options shall be preferred and one of them is selected.
    """
    matches: list[tuple[tuple[int, bool, int], HtmlElement]] = []
    for index, option in enumerate(options):
        if _option_disabled(option):
            continue
        rank = _match_option(option, value)
        if rank is not None:
            unselected = selected and option.get("selected") is None
            matches.append(((rank, unselected, index), option))
    if not matches:
        return None
    return min(matches, key=lambda match: match[0])[1]


def _select_option(
    control: SelectElement,
    options: list[HtmlElement],
    option: HtmlElement,
    *,
    add: bool,
) -> None:
    """Select or deselect the given option of a select element.

    When the selected option of a single select is deselected,
    the first option will be used, like in a browser.
    """
    if control.multiple:
        if add:
            option.set("selected", "")
        else:
            option.attrib.pop("selected", None)
        return
    selected = [opt for opt in options if opt.get("selected") is not None]
    if add or (selected and selected[-1] is option):
        for opt in selected:
            del opt.attrib["selected"]
        if add:
            option.set("selected", "")


def _all_the_same_submit(matches: Sequence[FieldElement]) -> bool:
    """Check if a list of controls all belong to the same control.

    For use with checkboxes, hidden, and submit buttons.
    """
    name = value = None
    for match in matches:
        if not isinstance(match, InputElement):
            return False
        if match.type not in ("submit", "hidden"):
            return False
        if name is None:
            name = match.name
            value = match.value
        elif match.name != name or match.value != value:
            return False
    return True


def _all_the_same_checkbox(matches: Sequence[FieldElement]) -> bool:
    """Check if a list of controls all belong to the same checkbox.

    Hidden controls can combine with checkboxes, to allow form
    processors to ensure a False value is returned even if user
    does not check the checkbox. Without the hidden control, no
    value would be returned.
    """
    name = None
    for match in matches:
        if not isinstance(match, InputElement):
            return False
        if match.type not in ("checkbox", "hidden"):
            return False
        if name is None:
            name = match.name
        elif match.name != name:
            return False
    return True


def unique_match(matches: Sequence[FieldElement]) -> bool:
    """Check whether a match is unique."""
    return (
        len(matches) == 1
        or _all_the_same_checkbox(matches)
        or _all_the_same_submit(matches)
    )


def run_tidy(html: str) -> tuple[str | None, str | None]:
    """Run HTML Tidy on the given HTML string.

    Return a 2-tuple (output, errors).  (None, None) will be returned if
    PyTidyLib (or the required shared library for tidy) isn't installed.
    """
    from .commands import options  # noqa: PLC0415

    require_tidy = options.get("require_tidy")

    if not tidylib:
        if require_tidy:
            raise TwillException(
                "Option require_tidy is set, but PyTidyLib is not installed"
            )
        return None, None

    opts = {
        key[5:].replace("_", "-"): value
        for key, value in options.items()
        if key.startswith("tidy_")
    }
    clean_html, errors = tidylib.tidy_document(html, opts)
    return clean_html, errors


def get_equiv_refresh_interval() -> int | None:
    """Get the longest interval for which the browser should follow redirects.

    Redirection happens if the given interval is shorter than this.
    """
    from .commands import options  # noqa: PLC0415

    return options.get("equiv_refresh_interval")


def is_hidden_filename(filename: str) -> bool:
    """Check if this is a hidden file (starting with a dot)."""
    return filename not in (os.curdir, os.pardir) and Path(
        filename
    ).name.startswith(".")


def filename_from_content_disposition(value: str) -> str | None:
    """Get the filename from the value of a Content-Disposition header.

    An extended filename parameter with RFC 5987 encoding takes precedence
    over a plain filename parameter as demanded by RFC 6266.
    """
    message = Message()
    message["Content-Disposition"] = value
    params = message.get_params(header="Content-Disposition") or []
    filenames = [value for key, value in params if key == "filename"]
    # the extended parameter is returned as a tuple (charset, language, value)
    filenames.sort(key=lambda value: not isinstance(value, tuple))
    for filename in filenames:
        if isinstance(filename, tuple):
            try:  # fall back to the plain parameter if charset is unknown
                codecs.lookup(filename[0] or "us-ascii")
            except LookupError:
                continue
        collapsed = collapse_rfc2231_value(filename)
        if collapsed:
            return collapsed
    return None


_reserved_filenames = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


_max_filename_bytes = 255  # limit of most file systems
_max_extension_bytes = 16


def safe_filename(filename: str | None) -> str | None:
    """Make a filename suggested by a server safe for saving a local file.

    Only the final path component is used, characters not allowed in
    filenames on common platforms are replaced with underscores, reserved
    device names on Windows are prefixed with an underscore, and empty or
    hidden filenames (starting with a dot) are rejected. Overlong filenames
    are truncated to 255 bytes, keeping the extension if possible.
    """
    if not filename:
        return None
    filename = re.split(r"[/\\]", filename)[-1]
    filename = re.sub(r'[\x00-\x1f\x7f<>:"|?*]', "_", filename)
    filename = filename.strip().rstrip(". ")
    if not filename or filename.startswith("."):
        return None
    if filename.split(".", 1)[0].rstrip().upper() in _reserved_filenames:
        filename = f"_{filename}"  # reserved device names on Windows
    if len(filename.encode()) > _max_filename_bytes:
        ext = Path(filename).suffix
        if len(ext.encode()) > _max_extension_bytes:
            ext = ""
        stem = filename.removesuffix(ext)
        max_stem_bytes = _max_filename_bytes - len(ext.encode())
        stem = stem.encode()[:max_stem_bytes].decode(errors="ignore")
        filename = stem.rstrip(". ") + ext
    return filename


def is_twill_filename(filename: str) -> bool:
    """Check if the given filename has the twill file extension."""
    return filename.endswith(twill_ext) and not is_hidden_filename(filename)


def make_twill_filename(name: str) -> str:
    """Add the twill extension to the name of a script if necessary."""
    if name not in (os.curdir, os.pardir):
        path = Path(name)
        if not (path.suffix or (path.exists() and not path.is_dir())):
            twill_path = path.with_suffix(twill_ext)
            if twill_path.exists() and not twill_path.is_dir():
                path = twill_path
        name = str(path)
    return name


def gather_filenames(args: Sequence[str]) -> list[str]:
    """Collect script files from within directories."""
    collected_names: list[str] = []
    append, extend = collected_names.append, collected_names.extend
    is_dir, walk, sep = os.path.isdir, os.walk, os.sep
    for arg in args:
        name = make_twill_filename(arg)
        if is_dir(name):
            for dir_path, dir_names, names in walk(name):
                dir_names[:] = [
                    name for name in dir_names if not is_hidden_filename(name)
                ]
                path = dir_path + sep
                extend(
                    path + name for name in names if is_twill_filename(name)
                )
        else:
            append(name)
    return collected_names
