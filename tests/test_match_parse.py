from .utils import execute_script


def test_match_parse(url):
    execute_script('test_match_parse.twill', initial_url=url)

