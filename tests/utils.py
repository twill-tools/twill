"""Utility functions for testing twill"""

from __future__ import print_function

import os
import sys
import getpass
import subprocess
import time

from io import StringIO

import requests

test_dir = os.path.dirname(__file__)
print('the test directory is:', test_dir)
sys.path.insert(0, os.path.abspath(os.path.join(test_dir, '..')))

import twill  # import twill from the right directory


HOST = '127.0.0.1'  # interface to run the server on
PORT = 8080  # default port to run the server on
SLEEP = 0.5  # time to wait for the server to start

START = True  # whether to automatically start the quixote server
LOG = None  # name of the server log file or None

_cwd = '.'  # current working directory
_url = None  # current server url


def get_url():
    """Get the current server URL."""
    if _url is None:
        raise Exception("server has not yet been started")
    return _url


def cd_test_dir():
    """Make the test directory the current directory."""
    global _cwd
    _cwd = os.getcwd()
    os.chdir(test_dir)


def pop_test_dir():
    """Restore the current directory before running the tests."""
    os.chdir(_cwd)


def mock_getpass(*args):
    """A mock getpass function."""
    return "pass"


def execute_script(filename, inp=None, initial_url=None):
    """Execute twill script with the given filename."""
    if filename != '-':
        filename = os.path.join(test_dir, filename)

    if inp:
        # use inp as the std input for the actual script commands
        if isinstance(inp, bytes):  # Python 2
            inp = inp.decode('utf-8')
        inp_fp = StringIO(inp)
        old_stdin, sys.stdin = sys.stdin, inp_fp
        old_getpass, getpass.getpass = getpass.getpass, mock_getpass
    try:
        twill.execute_file(filename, initial_url=initial_url)
    finally:
        if inp:
            sys.stdin = old_stdin
            getpass.getpass = old_getpass


def execute_shell(filename, inp=None, initial_url=None,
                  fail_on_unknown=False):
    """Execute twill script with the given filename using the shell."""
    # use filename as the stdin *for the shell object only*
    if filename != '-':
        filename = os.path.join(test_dir, filename)

    cmd_inp = open(filename).read()
    if isinstance(cmd_inp, bytes):  # Python 2
        cmd_inp = cmd_inp.decode('utf-8')
    cmd_inp += u'\nquit\n'
    cmd_inp = StringIO(cmd_inp)
    cmd_loop = twill.shell.TwillCommandLoop

    if inp:
        # use inp as the std input for the actual script commands
        if isinstance(inp, bytes):  # Python 2
            inp = inp.decode('utf-8')
        inp_fp = StringIO(inp)
        old_stdin, sys.stdin = sys.stdin, inp_fp
        old_getpass, getpass.getpass = getpass.getpass, mock_getpass
    try:
        s = cmd_loop(initial_url=initial_url, stdin=cmd_inp,
                     fail_on_unknown=fail_on_unknown)
        s.cmdloop()
    except SystemExit:
        pass
    finally:
        if inp:
            sys.stdin = old_stdin
            getpass.getpass = old_getpass
        cmd_loop.reset()  # do not keep as singleton


def start_server(port=None):
    """Start a simple test web server.

    Run a Quixote simple_server on HOST:PORT with subprocess.
    All output is captured and thrown away.

    The parent process returns the URL on which the server is running.
    """
    global _url

    if port is None:
        port = int(os.environ.get('TWILL_TEST_PORT', PORT))

    if START:
        out = open(LOG or os.devnull, 'w', buffering=1)
        print('STARTING:', sys.executable, 'tests/server.py', os.getcwd())
        subprocess.Popen(
            [sys.executable, '-u', 'server.py'],
            stderr=subprocess.STDOUT, stdout=out)
        time.sleep(SLEEP)  # wait until the server is up and running

    _url = 'http://%s:%d/' % (HOST, port)


def stop_server():
    """Stop a previously started test web server."""
    global _url

    if _url:
        if START:
            try:
                requests.get('%sexit' % (_url,))
            except Exception:
                print('Could not stop the server')
        _url = None
