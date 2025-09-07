#!/usr/bin/env python3

"""Flask based test app for twill."""

import os
from base64 import decodebytes
from time import sleep
from typing import Any, MutableMapping, NoReturn, Optional

from flask import (
    Flask,
    Response,
    abort,
    make_response,
    redirect,
    request,
    session,
)

HOST = "127.0.0.1"
PORT = 8080
DEBUG = False
RELOAD = False

app = Flask(__name__)

app.secret_key = "not-a-secret-since-this-is-a-test-app-only"  # noqa: S105


class SessionManager:
    """Session manager."""

    _next_session_id = 1

    @classmethod
    def message(cls, session: MutableMapping) -> str:
        """Create a message with session information."""
        sid = cls.session_id(session) or "undefined"
        visit = session.get("visit", 0)
        user = session.get("user", "guest")
        return f"""\
<html>
<head>
    <title>Hello, world!</title>
</head>
<body>
    <p>Hello, world!</p>
    <p>These are the twill tests.</p>
    <p>Your session ID is {sid}; this is visit #{visit}.</p>
    <p>You are logged in as {user}.</p>
    <p>
        <a href="increment">increment</a> |
        <a href="incrementfail">incrementfail</a>
    </p>
    <p><a href="logout">log out</a></p>
    <p>
        (<a href="test spaces">test spaces</a> /
        <a href="test_spaces">test spaces2</a>)
    </p>
</body>
</html>
"""

    @classmethod
    def session_id(cls, session: MutableMapping) -> Optional[int]:
        """Get the session ID or set it if it does not exist."""
        sid = session.get("sid")
        if sid is None:
            session["sid"] = cls._next_session_id
            cls._next_session_id += 1
        return sid


message = SessionManager.message


# HTML helpers


def field(type_: str = "text", name: str = "", value: str = "") -> str:
    """Create an HTML field."""
    return f'<input type="{type_}" name="{name}" value="{value}">'


def par(text: str = "") -> str:
    """Create an HTML paragraph."""
    return f"<p>{text}</p>"


# Flask routes


@app.route("/")
def view_root() -> str:
    """Show index page."""
    return message(session)


@app.route("/exception")
def view_exception() -> NoReturn:
    """Raise a server error."""
    raise RuntimeError("500 error -- fail out!")


@app.route("/test_spaces")
@app.route("/test spaces")
def view_test_spaces() -> str:
    """Test spaces."""
    return "success"


@app.route("/sleep")
def view_sleep() -> str:
    """Test timeouts."""
    sleep(0.5)
    return "sorry for the delay"


@app.route("/increment")
def view_increment() -> str:
    """Visit session."""
    session["visit"] = session.get("visit", 0) + 1
    return message(session)


@app.route("/incrementfail")
def view_incrementfail() -> NoReturn:
    """Visit session with failure."""
    session["visit"] = session.get("visit", 0) + 1
    raise RuntimeError(message(session))


@app.route("/simpleform", methods=["GET", "POST"])
def view_simpleform() -> str:
    """Test non-existing submit button."""
    s1, s2 = field(name="n"), field(name="n2")
    values = par(" ".join(request.form.values()))
    return f'{values}</p><form method="POST">{s1} {s2}</form>'


@app.route("/getform")
def view_getform() -> str:
    """Test form with get method."""
    s = field("hidden", name="n", value="v")
    return f'<form method="GET">{s}<input type="submit"></form>'


@app.route("/login", methods=["GET", "POST"])
def view_login() -> Any:
    """Test login."""
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect("./")

    login = field(name="username", value="")
    s = field("submit", name="submit", value="submit me")
    s2 = field("submit", name="nosubmit2", value="don't submit")
    img = '<input type=image name="submit you" src="DNE.gif">'

    return (
        '<form method="POST"><p>Log in:</p>'
        f"<p>{login}</p><p>{s2} {s}</p><p>{img}</p></form>"
    )


@app.route("/logout")
def view_logout() -> Any:
    """Test logout."""
    session.clear()
    return redirect("./")


@app.route("/upload_file", methods=["GET", "POST"])
def view_upload_file() -> str:
    """Test file upload."""
    if request.method == "POST" and "upload" in request.files:
        return request.files["upload"].read()
    return """\
<form enctype="multipart/form-data" method="POST">
<input type="file" name="upload">
<input type="submit" value="submit">
</form>"""


@app.route("/formpostredirect", methods=["GET", "POST"])
def view_formpostredirect() -> Any:
    """Test redirect after a form POST."""
    if request.method != "POST":
        return """\
<form method="POST" enctype="multipart/form-data">
<input type="text" name="test">
<input type="submit" value="submit" name="submit">
</form>
"""
    return redirect("./")


@app.route("/display_post", methods=["POST"])
def view_display_post() -> str:
    """Show the form items."""
    return "".join(par(f"{k!s}: {v!r}") for k, v in request.form.items())


@app.route("/display_environ")
def view_display_environ() -> str:
    """Show the environment variables."""
    return "".join(par(f"{k!s}: {v!r}") for k, v in request.environ.items())


@app.route("/echo")
def view_echo() -> str:
    """Show query parameters."""
    show = ", ".join(f"{k}={v}" for k, v in request.args.items()) or "nothing"
    return f"<html><body>{show}</body></html>"


@app.route("/plaintext")
def view_plaintext() -> Response:
    """Test plain text response."""
    response = make_response("hello, world")
    response.headers["Content-Type"] = "text/plain"
    return response


@app.route("/xml")
def view_xml() -> Response:
    """Test XML response."""
    response = make_response(
        '<?xml version="1.0" encoding="utf-8" ?><foo>bår</foo>'
    )
    response.headers["Content-Type"] = "text/xml"
    return response


@app.route("/restricted")
def view_restricted() -> str:
    """Test restricted access."""
    if "user" not in session:
        response = make_response("you must have a username", 403)
        abort(response)
    return "you made it!"


@app.route("/http_auth")
def view_http_auth() -> str:
    """Test restricted access using HTTP authentication."""
    login = passwd = None
    ha = request.environ.get("HTTP_AUTHORIZATION")
    if ha:
        auth_type, auth_string = ha.split(None, 1)
        if auth_type.lower() == "basic":
            auth_string = decodebytes(auth_string.encode("utf-8"))
            login_bytes, passwd_bytes = auth_string.split(b":", 1)
            login = login_bytes.decode("utf-8")
            passwd = passwd_bytes.decode("utf-8")
            if (login, passwd) != ("test", "password"):
                passwd = None

    if passwd:
        print(f"Successful login as {login}")
    elif login:
        print(f"Invalid login attempt as {login}")
    else:
        print("Access has been denied")
    print()
    if not passwd:
        response = make_response(
            "you are not authorized to access this resource", 401
        )
        response.headers["WWW-Authenticate"] = 'Basic realm="Protected"'
        abort(response)
    return "you made it!"


@app.route("/broken_linktext")
def view_broken_linktext() -> str:
    """Get broken link text."""
    return """
<a href="/">
<span>some text</span>
</a>
"""


@app.route("/broken_form_1")
def view_broken_form_1() -> str:
    """Get broken form 1."""
    return """\
<form>
<input type="text" name="blah" value="thus">
"""


@app.route("/broken_form_2")
def view_broken_form_2() -> str:
    """Get broken form 2."""
    return """\
<form>
<table>
<tr><td>
<input name="broken">
</td>
</form>
</tr>
</form>
"""


@app.route("/broken_form_3")
def view_broken_form_3() -> str:
    """Get broken form 3."""
    return """\
<table>
<tr><td>
<input name="broken">
</td>
</form>
</tr>
</form>
"""


@app.route("/broken_form_4")
def view_broken_form_4() -> str:
    """Get broken form 4."""
    return """\
<font>
<INPUT>

<FORM>
<input type="blah">
</form>
"""


@app.route("/broken_form_5")
def view_broken_form_5() -> str:
    """Get broken form 5."""
    return """\
<div id="loginform">
<form method="post" name="loginform" action="ChkLogin">
<h3>ARINC Direct Login</h3>
<br/>
<strong>User ID</strong><br/>
<input name="username" id="username" type="text" style="width:80%"><br/>
<strong>Password</strong><br/>
<input name="password" type="password" style="width:80%"><br/>
<div id="buttonbar">
<input value="Login" name="login" class="button" type="submit">
</div>
</form>
</div>
"""


@app.route("/test_checkbox", methods=["GET", "POST"])
def view_test_checkbox() -> str:
    """Test single checkbox."""
    s = ""
    if request.method == "POST" and "checkboxtest" in request.form:
        value = request.form["checkboxtest"]

        s += par(f"CHECKBOXTEST: =={value}==")

    return f"""\
{s}
<form method="POST">

<input type="checkbox" name="checkboxtest" value="True">
<input type="hidden" name="checkboxtest" value="False">

<input type="submit" value="post">
</form>
"""


@app.route("/test_checkboxes", methods=["GET", "POST"])
def view_test_checkboxes() -> str:
    """Test multiple checkboxes."""
    s = ""
    if request.method == "POST" and "checkboxtest" in request.form:
        value = ",".join(request.form.getlist("checkboxtest"))

        s += par(f"CHECKBOXTEST: =={value}==")

    return f"""\
{s}
<form method="POST">
<input type="checkbox" name="checkboxtest" value="one">
<input type="checkbox" name="checkboxtest" value="two">
<input type="checkbox" name="checkboxtest" value="three">
<input type="submit" value="post">
</form>
"""


@app.route("/test_simple_checkbox", methods=["GET", "POST"])
def view_test_simple_checkbox() -> str:
    """Test simple checkbox."""
    s = ""
    if request.method == "POST" and "checkboxtest" in request.form:
        value = request.form["checkboxtest"]

        s += par(f"CHECKBOXTEST: =={value}==")

    return f"""\
{s}
<form method="POST">

<input type="checkbox" name="checkboxtest">

<input type="submit" value="post">
</form>
"""


@app.route("/test_radiobuttons", methods=["GET", "POST"])
def view_test_radiobuttons() -> str:
    """Test radio buttons."""
    s = ""
    if request.method == "POST" and "radiobuttontest" in request.form:
        value = request.form["radiobuttontest"]

        s += par(f"RADIOBUTTONTEST: =={value}==")

    return f"""\
{s}
<form method="POST">
<input type="radio" name="radiobuttontest" value="one">
<input type="radio" name="radiobuttontest" value="two">
<input type="radio" name="radiobuttontest" value="three">
<input type="submit" value="post">
</form>
"""


@app.route("/testformaction", methods=["POST"])
def view_testformaction() -> str:
    """Test form actions."""
    keys = sorted(k for k in request.form if request.form[k])
    return "==" + " AND ".join(keys) + "=="


@app.route("/testform", methods=["GET", "POST"])
def view_testform() -> str:
    """Test form."""
    s = ""
    if not request.form:
        s = "NO FORM"

    if request.form and "selecttest" in request.form:
        values = " AND ".join(request.form.getlist("selecttest"))
        s += par(f"SELECTTEST: =={values}==")

    if request.form:
        items = []
        for name in ("item", "item_a", "item_b", "item_c"):
            if request.form.get(name):
                value = request.form[name]
                items.append(f"{name}={value}")
        values = " AND ".join(items)
        s += par(f"NAMETEST: =={values}==")

    return f"""\
{s}
<form method="POST" id="the_form">
<select name="selecttest" multiple>
<option>val</option>
<option value="selvalue1">value1</option>
<option value="selvalue2">value2</option>
<option value="selvalue3">value3</option>
<option value="test.value3">testme.val</option>
<option value="Test.Value4">testme4.val</option>
</select>

<input type="text" name="item">
<input type="text" name="item_a">
<input type="text" name="item_b">
<input type="text" name="item_c">

<input type="text" id="some_id">

<input type="submit" value="post" id="submit_button">
</form>
"""


@app.route("/multisubmitform", methods=["GET", "POST"])
def view_multisubmitform() -> str:
    """Test form with multiple submit buttons."""
    s1 = field("submit", "sub_a", value="sub_a")
    s2 = field("submit", "sub_b", value="sub_b")

    s = ""
    if request.method == "POST":
        used = False
        if "sub_a" in request.form:
            used = True
            s += "used_sub_a"
        if "sub_b" in request.form:
            used = True
            s += "used_sub_b"

        if not used:
            raise RuntimeError("Not button was used.")

        referer = request.environ.get("HTTP_REFERER")
        if referer:
            s += par(f"referer: {referer}")

    return f'<form method="POST">{s} {s1} {s2}</form>'


@app.route("/two_forms", methods=["GET", "POST"])
def view_two_forms() -> str:
    """Test two forms."""
    if request.form:
        form = request.form.get("form")
        item = request.form.get("item")
        s = f"FORM={form} ITEM={item}"
    else:
        s = "NO FORM"

    return f"""\
<h1>Two Forms</h1>
<p>== {s} ==</p>
<form method="POST" id="form1">
<input type="text" name="item">
<input type="hidden" name="form" value="1">
<input type="submit" value="post">
</form>
<form method="POST" id="form2">
<input type="text" name="item">
<input type="hidden" name="form" value="2">
<input type="submit" value="post">
</form>
"""


@app.route("/test_global_form", methods=["GET", "POST"])
def view_test_global_form() -> str:
    """Test the global form."""
    return """
<html>
<head>
<title>Broken</title>
</head>
<body>
<div>
<input name="global_form_entry" type="text">
<input name="global_entry_2" type="text">
</div>

<form name="login" method="post" action="display_post">
<input type="text" name="hello">
<input type="hidden" name="form" value="1">
<input type="submit">
</form>

<form name="login" method="post" action="display_post">
<input type="text" name="hello">
<input type="hidden" name="form" value="2">
<input type="submit">
</form>

</body>
</html>
"""


@app.route("/test_refresh")
def view_test_refresh() -> str:
    """Test simple refresh."""
    return """\
<meta http-equiv="refresh" content="2; url=./login">
hello, world.
"""


@app.route("/test_refresh2")
def view_test_refresh2() -> str:
    """Test refresh with upper case."""
    return """\
<META HTTP-EQUIV="REFRESH" CONTENT="2; URL=./login">
hello, world.
"""


@app.route("/test_refresh3")
def view_test_refresh3() -> str:
    """Test circular refresh."""
    return """\
<meta http-equiv="refresh" content="2; url=./test_refresh3">
hello, world.
"""


@app.route("/test_refresh4")
def view_test_refresh4() -> str:
    """Test refresh together with similar meta tags."""
    return """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>o2.ie</title>
<meta http-equiv="refresh" content="0;URL=/login">
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<body>
</body>
</html>
hello, world.
"""


@app.route("/test_refresh5")
def view_test_refresh5() -> str:
    """Check for situation where given URL is quoted."""
    return """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>o2.ie</title>
<meta http-equiv="refresh" content="0;'URL=/login'">
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<body>
</body>
</html>
hello, world.
"""


if __name__ == "__main__":
    port = int(os.environ.get("TWILL_TEST_PORT", PORT))
    print(f"starting twill test server on port {port}.")
    try:
        app.run(host=HOST, port=port, debug=DEBUG, use_reloader=RELOAD)
    except KeyboardInterrupt:
        print("Keyboard interrupt ignored.")
