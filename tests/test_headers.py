from .utils import execute_script


def test(url):
    execute_script('test_headers.twill', initial_url=url)
