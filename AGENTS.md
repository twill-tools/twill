# AGENTS.md

Instructions for coding agents working on the twill code base. For *using*
twill (writing and running twill scripts), see the skill in
`skills/twill/SKILL.md` and the docs at https://twill-tools.github.io/twill/.

## What twill is

twill is a simple scripting language and Python library for browsing the web
and testing web sites without a real browser. It is built on httpx (HTTP),
lxml (HTML parsing) and pyparsing (script parsing). It does not run
JavaScript.

## Layout

- `src/twill/`
  - `commands.py`: all twill commands as plain functions; `__all__` is the
    list of commands known to the parser and the interactive shell.
  - `browser.py`: `TwillBrowser`, the browser state (page, forms, cookies,
    history) on top of httpx.
  - `parse.py`: script parsing, variable substitution, script execution.
  - `shell.py`: the `twill` command line (`main`) and the interactive shell.
  - `utils.py`: HTML parsing, form handling, filename helpers.
  - `namespaces.py`: global and local variable dictionaries.
  - `errors.py`, `agents.py` (User-Agent shortcuts), `unit.py` (helper for
    unit tests), `fork.py` (`twill-fork` for parallel runs).
  - `extensions/`: optional command modules loaded with `extend_with`.
- `tests/`: pytest test suite and its Flask test app.
- `docs/`: Sphinx documentation (reStructuredText).
- `extras/`: example scripts and the MaxQ script generator.
- `skills/twill/`: agent skill for twill users; `.claude-plugin/` makes the
  repository installable as a Claude Code plugin.
- `.github/workflows/`: tests on every push; docs deployed on push to `main`.

## Setup

The development dependencies are dependency groups in `pyproject.toml`:
`test`, `docs`, `lint`, `typing`, `manifest`, and `dev` (all of them).

```sh
uv sync --all-groups               # or: pip install -e . --group dev
```

## Checks

Run `tox` before considering a change done; everything must pass:

- `py310` to `py315`: the tests with each supported Python version
- `ruff`: `ruff check` and `ruff format --check` on `src/twill`, `tests`,
  `extras`
- `mypy`: type checks on the same directories
- `docs`: Sphinx build with `-nEW` (warnings are errors)
- `manifest`: `check-manifest`, i.e. new files must be covered by
  `MANIFEST.in` or ignored in `[tool.check-manifest]`

During development, run single environments (`tox -e ruff,mypy`) or tests
directly: `pytest tests/test_cli.py` or `pytest tests/test_cli.py -k name`.

## Tests

- Tests that need HTTP use the session fixture `url` from
  `tests/conftest.py`, which starts the Flask app in `tests/server.py` on
  port 8080 (or `TWILL_TEST_PORT`). Add new routes there when needed.
- Many tests are a pair `test_<topic>.py` and `test_<topic>.twill`: the
  Python file runs the script with `execute_script` from `tests/utils.py`.
  Use a script when testing twill language behavior, plain Python for
  functions and edge cases.
- CLI tests use `execute_main` from `tests/utils.py` (see `test_cli.py`).

## Conventions

- Code must run on Python 3.10 and newer; no syntax or library features
  from later versions.
- Ruff has nearly all rule sets enabled (see `pyproject.toml`), with
  line length 79. Don't add blanket `noqa` comments; if a targeted one is
  unavoidable, keep it specific (`# noqa: PLR0913`).
- Code in `src/twill` has type hints and docstrings, following the
  existing style; tests need neither docstrings nor return types (see the
  per-file ignores in `pyproject.toml`). Command docstrings in `commands.py` start with a `>> command
  <args>` line, because they are the help text of the interactive shell.

## When adding or changing a command

Update all of these:

1. The function in `src/twill/commands.py`, with its `>>` docstring.
2. `__all__` in `src/twill/commands.py`, including aliases; parser and shell
   take the command list from there.
3. `docs/commands.rst` (and other docs pages that mention the command);
   `tests/test_docs.py` checks the `>>` help lines and that every command
   documented there exists.
4. The cheat sheet in `skills/twill/SKILL.md`; `tests/test_skill.py` fails
   if it does not list exactly the commands in `__all__`.
5. Tests, and an entry in `docs/changelog.rst`.

## Changelog and docs

- Every user-visible change gets an entry in the topmost `(unreleased)`
  section of `docs/changelog.rst`.
- `llms.txt` and `llms-full.txt` are generated from the docs by
  `sphinx-llms-txt`; there is nothing to maintain separately.

## Git and releases

- Work on a branch, not on `main`: pushing `main` deploys the docs.
- Commit messages have a short imperative subject, like the existing
  history.
- Releases are done by the maintainer. The version is set only in
  `pyproject.toml` (and in `.claude-plugin/plugin.json` for the plugin).
