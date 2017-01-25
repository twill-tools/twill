#!/usr/bin/env python

"""Quixote test app for twill."""

from __future__ import print_function

import os

try:
    from base64 import decodebytes
except ImportError:  # Python 2
    from base64 import decodestring as decodebytes

from quixote.publish import Publisher
from quixote.errors import AccessError
from quixote.session import Session, SessionManager
from quixote.directory import Directory, AccessControlled
from quixote.form import widget
from quixote import (
    get_session, get_session_manager, get_path,
    redirect, get_request, get_response)

try:
    basestring
except NameError:  # Python 3
    basestring = str


HOST = '127.0.0.1'
PORT = 8080


class AlwaysSession(Session):

    def __init__(self, session_id):
        Session.__init__(self, session_id)
        self.n = 0
        
    def has_info(self):
        """Always save."""
        return True

    is_dirty = has_info


class UnauthorizedError(AccessError):
    """The request requires user authentication.

    This subclass of AccessError sends a 401 instead of a 403,
    hinting that the client should try again with authentication.

    (from http://quixote.ca/qx/HttpBasicAuthentication)
    """

    status_code = 401
    title = "Unauthorized"
    description = "You are not authorized to access this resource."

    def __init__(self, realm='Protected', public_msg=None, private_msg=None):
        self.realm = realm
        AccessError.__init__(self, public_msg, private_msg)
        
    def format(self):
        request = get_request()
        request.response.set_header(
            'WWW-Authenticate', 'Basic realm="%s"' % self.realm)
        return AccessError.format(self)


def create_publisher():
    """Create a publisher for TwillTest, with session management added on."""
    session_manager = SessionManager(session_class=AlwaysSession)
    return Publisher(TwillTest(), session_manager=session_manager,
                     display_exceptions='plain')


def message(session):
        return """\
<html>
<head>
<title>Hello, world!</title>
</head>
<body>
Hello, world!
<p>
These are the twill tests.
<p>
Your session ID is %s; this is visit #%d.
<p>
You are logged in as "%s".
<p>
<a href="./increment">increment</a> | <a href="./incrementfail">incrementfail</a>
<p>
<a href="logout">log out</a>
<p>
(<a href="test spaces">test spaces</a> / <a href="test_spaces">test spaces2</a>)
</body>
</html>
""" % (session.id, session.n, session.user)


class TwillTest(Directory):
    """The actual test app."""

    _q_exports = [
        'logout', 'increment', 'incrementfail', "", 'restricted',
        'login', ('test spaces', 'test_spaces'), 'test_spaces',
        'simpleform', 'upload_file', 'http_auth', 'formpostredirect',
        'exit', 'multisubmitform', "exception", "plaintext",
        "testform", "testformaction",
        "test_refresh", "test_refresh2",
        "test_refresh3", "test_refresh4", "test_refresh5",
        "test_checkbox", "test_simple_checkbox", "echo",
        "test_checkboxes", 'test_global_form',
        'broken_form_1', 'broken_form_2', 'broken_form_3',
        'broken_form_4', 'broken_form_5', 'broken_linktext',
        'exit', 'display_post', 'display_environ']

    def test_global_form(self):
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

  <form name="login" method="post">
  <input type=text name=hello>
  <input type=submit>
  </form>

  <form name="login" method="post" action="http://iorich.caltech.edu:8080/display_post">
  <input type=text name=hello>
  <input type=submit>
  </form>

 </body>
</html>
"""

    def display_post(self):
        s = ""
        request = get_request()
        for k, v in request.form.items():
            s += "k: '''%s''' : '''%s'''<p>\n" % (k, v,)
        return s

    def display_environ(self):
        s = ""
        request = get_request()
        for k, v in request.environ.items():
            s += "k: '''%s''' : '''%s'''<p>\n" % (k, v,)
        return s

    def exit(self):
        raise SystemExit

    def __init__(self):
        self.restricted = Restricted()
        self.http_auth = HttpAuthRestricted()

    def _q_index(self):
        session = get_session()
        return message(session)

    def broken_form_1(self):
        return """\
<form>
<input type=text name=blah value=thus>
"""

    def broken_form_2(self):
        return """\
<form>
<table>
<tr><td>
<input name='broken'>
</td>
</form>
</tr>
</form>
"""

    def broken_form_3(self):
        return """\
<table>
<tr><td>
<input name='broken'>
</td>
</form>
</tr>
</form>
"""

    def broken_form_4(self):
        return """\
<font>
<INPUT>

<FORM>
<input type="blah">
</form>
"""

    def broken_form_5(self):
        return """\
<div id="loginform">
   <form method="post" name="loginform" action="ChkLogin">
   <h3>ARINC Direct Login</h3>
   <br/>
   <strong>User ID</strong><br/>
   <input name="username" id="username" type="text" style="width:80%;"><br/>
   <strong>Password</strong><br/>
   <input name="password" type="password" style="width:80%;"><br/>
   <div id="buttonbar">
   <input value="Login" name="login" class="button" type="submit">
   </div>
   </form>
</div>
"""

    def broken_linktext(self):
        return """
<a href="/">
<span>some text</span>
</a>
"""
    
    def test_refresh(self):
        """test simple refresh"""
        return """\
<meta http-equiv="refresh" content="2; url=./login">
hello, world.
"""

    def test_refresh2(self):
        """test refresh with upper case"""
        return """\
    <META HTTP-EQUIV="REFRESH" CONTENT="2; URL=./login">
    hello, world.
    """

    def test_refresh3(self):
        """test circular refresh"""
        return """\
    <meta http-equiv="refresh" content="2; url=./test_refresh3">
    hello, world.
    """

    def test_refresh4(self):
        """test refresh together with similar meta tags"""
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

    def test_refresh5(self):
        """check for situation where given URL is quoted."""
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

    def exception(self):
        raise Exception("500 error -- fail out!")

    def test_spaces(self):
        return "success"

    def increment(self):
        session = get_session()
        session.n += 1
        return message(session)

    def incrementfail(self):
        session = get_session()
        session.n += 1
        raise Exception(message(session))

    def login(self):
        request = get_request()
        username_widget = widget.StringWidget(name='username', value='')
        submit_widget = widget.SubmitWidget(name='submit', value='submit me')
        submit_widget2 = widget.SubmitWidget(
            name='nosubmit2', value="don't submit")
        
        if request.form:
            assert not submit_widget2.parse(request)
            username = username_widget.parse(request)
            if username:
                session = get_session()
                session.set_user(username)
                return redirect('./')

        image_submit = '''<input type=image name='submit you' src=DNE.gif>'''
                
        return "<form method=POST>Log in: %s<p>%s<p>%s<p>%s</form>" % (
            username_widget.render(), submit_widget2.render(),
            submit_widget.render(), image_submit)

    def simpleform(self):
        """No submit button..."""
        request = get_request()
        
        w1 = widget.StringWidget(name='n', value='')
        w2 = widget.StringWidget(name='n2', value='')
        
        return ("%s %s <form method=POST>'"
            "<input type=text name=n><input type=text name=n2></form>") % (
            w1.parse(request), w2.parse(request))

    def multisubmitform(self):
        request = get_request()
        
        submit1 = widget.SubmitWidget('sub_a', value='sub_a')
        submit2 = widget.SubmitWidget('sub_b', value='sub_b')

        s = ""
        if request.form:
            used = False
            if submit1.parse(request):
                used = True
                s += "used_sub_a"
            if submit2.parse(request):
                used = True
                s += "used_sub_b"

            if not used:
                assert False

            # print out the referer, too.
            referer = request.environ.get('HTTP_REFERER')
            if referer:
                s += "<p>referer: %s" % (referer,)

        return "<form method=POST>%s %s %s</form>" % (
            s, submit1.render(), submit2.render())

    def testformaction(self):
        request = get_request()
        keys = [k for k in request.form if request.form[k]]
        keys.sort()
        return "==" + " AND ".join(keys) + "=="

    def testform(self):
        request = get_request()

        s = ""
        if not request.form:
            s = "NO FORM"
            
        if request.form and 'selecttest' in request.form:
            values = request.form['selecttest']
            if isinstance(values, basestring):
                values = [values]
            s += "SELECTTEST: ==%s==<p>" % " AND ".join(values)

        if request.form:
            l = []
            for name in ('item', 'item_a', 'item_b', 'item_c'):
                if request.form.get(name):
                    value = request.form[name]
                    l.append('%s=%s' % (name, value))
            s += "NAMETEST: ==%s==<p>" % " AND ".join(l)

        return """\
%s
<form method=POST id=the_form>
<select name=selecttest multiple>
<option> val
<option value='selvalue1'> value1 </option>
<option value='selvalue2'> value2 </option>
<option value='selvalue3'> value3 </option>
<option value='test.value3'> testme.val </option>
<option value=Test.Value4> testme4.val </option>
</select>

<input type=text name=item>
<input type=text name=item_a>
<input type=text name=item_b>
<input type=text name=item_c>

<input type=text id=some_id>

<input type=submit value=post id=submit_button>
</form>
""" % (s,)

    def test_checkbox(self):
        request = get_request()

        s = ""
        if request.form and 'checkboxtest' in request.form:
            value = request.form['checkboxtest']
            if not isinstance(value, basestring):
                value = value[0]

            s += "CHECKBOXTEST: ==%s==<p>" % value

        return """\
%s
<form method=POST>

<input type="checkbox" name="checkboxtest" value="True">
<input type="hidden" name="checkboxtest" value="False">

<input type=submit value=post>
</form>
""" % (s,)

    def test_checkboxes(self):
        request = get_request()

        s = ""
        if request.form and 'checkboxtest' in request.form:
            value = request.form['checkboxtest']
            if not isinstance(value, basestring):
                value = ','.join(value)

            s += "CHECKBOXTEST: ==%s==<p>" % value

        return """\
%s
<form method=POST>
<input type="checkbox" name="checkboxtest" value="one">
<input type="checkbox" name="checkboxtest" value="two">
<input type="checkbox" name="checkboxtest" value="three">
<input type=submit value=post>
</form>
""" % (s,)

    def test_simple_checkbox(self):
        request = get_request()

        s = ""
        if request.form and 'checkboxtest' in request.form:
            value = request.form['checkboxtest']

            if not isinstance(value, basestring):
                value = value[0]

            s += "CHECKBOXTEST: ==%s==<p>" % value

        return """\
%s
<form method=POST>

<input type="checkbox" name="checkboxtest">

<input type=submit value=post>
</form>
""" % (s,)

    def formpostredirect(self):
        """Test redirect after a form POST."""
        request = get_request()

        if not request.form:
            return """\
<form method=POST enctype=multipart/form-data>
<input type=text name=test>
<input type=submit value=submit name=submit>
</form>
"""
        return redirect(get_path(1) + '/')

    def logout(self):
        # expire session
        session_manager = get_session_manager()
        session_manager.expire_session()

        # redirect to index page.
        return redirect(get_path(1) + '/')

    def plaintext(self):
        response = get_response()
        response.set_content_type("text/plain")
        return "hello, world"

    def echo(self):
        request = get_request()
        if request.form and 'q' in request.form:
            return request.form['q']
        return "<html><body>No Content</body></html>"

    def upload_file(self):
        request = get_request()
        if request.form:
            contents = request.form['upload'].fp.read()
            return contents
        else:
            return """"\
<form enctype=multipart/form-data method=POST>
<input type=file name=upload>
<input type=submit value=submit>
</form>"""

    def exit(self):
        os._exit(0)


class Restricted(AccessControlled, Directory):

    _q_exports = [""]

    def _q_access(self):
        session = get_session()
        if not session.user:
            raise AccessError("you must have a username")

    def _q_index(self):
        return "you made it!"


class HttpAuthRestricted(AccessControlled, Directory):

    _q_exports = [""]

    def _q_access(self):
        r = get_request()

        login = passwd = None
        ha = r.get_environ('HTTP_AUTHORIZATION', None)
        if ha:
            auth_type, auth_string = ha.split(None, 1)
            if auth_type.lower() == 'basic':
                if not isinstance(auth_string, bytes):  # Python 3
                    auth_string = auth_string.encode('utf-8')
                auth_string = decodebytes(auth_string)
                login, passwd = auth_string.split(b':', 1)
                if not isinstance(login, str):  # Python 3
                    login = login.decode('utf-8')
                if not isinstance(passwd, str):  # Python 3
                    passwd = passwd.decode('utf-8')

                if (login, passwd) != ('test', 'password'):
                    passwd = None

        if passwd:
            print("Successful login as '%s'" % (login,))
        elif login:
            print("Invalid login attempt as '%s'" % (login,))
        else:
            print("Access has been denied")
        print()
        if not passwd:
            raise UnauthorizedError

    def _q_index(self):
        return "you made it!"


if __name__ == '__main__':
    from quixote.server.simple_server import run
    port = int(os.environ.get('TWILL_TEST_PORT', PORT))
    print('starting twill test server on port %d.' % (port,))
    try:
        run(create_publisher, host=HOST, port=port)
    except KeyboardInterrupt:
        pass
