"""Test the unit-test support framework using (naturally) a unit test."""

import os
import time
from pathlib import Path

import twill.unit

from .server import app
from .utils import test_dir

HOST = "127.0.0.1"
PORT = 8080
SLEEP = 0.25
DEBUG = False
RELOAD = False


def run_server() -> None:
    """Function to run the server"""
    port = int(os.environ.get("TWILL_TEST_PORT", PORT))
    app.run(host=HOST, port=port, debug=DEBUG, use_reloader=RELOAD)


def just_wait() -> None:
    """Just wait instead of starting the server."""
    while True:
        time.sleep(SLEEP or 1)


def test(url: str) -> None:
    """Test wrapper for unit support."""
    # abspath to the script
    script = str(Path(test_dir, "test_unit_support.twill"))

    # the port that shall be used for running the server
    port = int(os.environ.get("TWILL_TEST_PORT", PORT))

    # create a TestInfo object
    test_info = twill.unit.TestInfo(script, run_server, HOST, port, SLEEP)

    if test_info.url == url:
        # server already running, run a dummy server function that just waits
        test_info = twill.unit.TestInfo(script, just_wait, HOST, port, SLEEP)

    # run the tests!
    twill.unit.run_test(test_info)
