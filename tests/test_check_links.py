"""Test the check_links extension."""

from .utils import execute_script


def test(url):

    execute_script('test_check_links.twill', initial_url=url)
