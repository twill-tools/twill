---
name: twill
description: Write, run and debug twill scripts (.twill files) and use the twill Python package. twill is a scripting language and Python library for browsing web sites without a real browser - following links, filling in and submitting forms, keeping cookies, checking status codes, page content and response headers, and saving pages and downloads. Use it when the user mentions twill or .twill files, or wants scripted smoke, regression or acceptance tests or simple automation for server-rendered web applications and HTML forms without JavaScript.
license: MIT
---

# twill

twill is a small language for browsing the web from the command line, built on
httpx and lxml. Each line of a script is one command; the script stops at the
first failing command. The same commands are available as Python functions.

Use twill for server-rendered HTML: navigation, forms, logins with cookies,
HTTP basic auth, status codes, content and header checks, downloads. It does
**not** run JavaScript, so it cannot test pages that build their content or
submit forms via JavaScript. Use a real browser tool (e.g. Playwright) for
those.

Install with `pip install twill` (Python 3.10 or newer). Validate HTML with
`tidy_ok` only if the extra `twill[tidy]` and the HTML Tidy library are
installed.

## Running scripts

```sh
twill script.twill                     # run one script
twill tests/                           # run all *.twill files below a directory
twill -u https://example.org a.twill   # go to this URL before each script
twill -s BASE=http://localhost:8080 -s USER=alice login.twill  # set variables
twill                                  # interactive shell ("help <command>")
```

Useful options: `-n` continue past errors, `-f` stop at the first failing
file, `-q` quiet, `-o FILE` write output to a file, `-d FILE` dump the HTML of
the page where an error happened, `-i` drop into the shell after the scripts,
`-l DEBUG` more logging. Arguments after `--` are passed to the scripts (see
the `argparse` extension). The exit code is 1 if any script failed, else 0.

Each script file starts with a fresh browser (no cookies, no current page).

## Script syntax

```text
# comments start with '#', also at the end of a line
go https://example.org/login          # arguments are separated by spaces
fv 1 comment "text with spaces"       # quote arguments with spaces
find 'He said "hi"'                   # single or double quotes
setglobal user alice
fv 1 username $user                   # $name: whole argument is a variable
go ${BASE}/items?owner=${user}        # ${expr}: Python expression, inline
find "logged in as (\w+)"
echo "found user ${__match__}"
run "import os"                       # run a Python statement
go "${BASE}/${os.environ['ITEM']}"      # quote if ${...} contains quotes
```

- `setlocal` sets a variable for the current file only, `setglobal` for all
  files; local variables win.
- `${...}` is evaluated as Python in the twill namespace; unknown names are
  left as they are.
- `__match__` holds the result of the last `find`, `url`, `title` or
  `header`: the first group, or the whole match.
- `__url__` holds the current URL.
- `go` accepts URLs relative to the current page.
- `\n` in an argument is converted to a newline.
- Quotes split arguments even inside `${...}`, so put an argument whose
  expression contains quotes into the other kind of quotes as a whole.

## Command cheat sheet

Signatures as shown by `help <command>`. Arguments in `[...]` are optional.
Most commands have aliases without underscores (`show_forms` = `showforms`).

<!-- commands:start -->
| Command | Aliases | Purpose |
| --- | --- | --- |
| `go <url>` | | Visit the URL (absolute or relative to the current page). |
| `back` | | Go back to the previous page. |
| `reload` | | Reload the current page. |
| `follow <regex>` | | Follow the first link whose text or URL matches. |
| `code <status>` | | Assert the HTTP status of the last response. |
| `find <regex> [<flags>]` | | Assert the HTML matches; flags `i`, `m`, `s`, `x` (XPath). |
| `not_find <regex> [<flags>]` | `notfind` | Assert the HTML does not match. |
| `url <regex>` | | Assert the current URL matches. |
| `title <regex>` | | Assert the page title matches. |
| `header <name> [<regex>]` | | Assert a response header exists (and matches). |
| `tidy_ok` | | Assert HTML Tidy reports no errors or warnings. |
| `show_forms` | `showforms` | Show the forms and fields with their numbers. |
| `form_value <form> <field> <value>` | `fv`, `formvalue` | Set a form field. |
| `submit [<button> [<form>]]` | | Submit the form last used with `fv`. |
| `form_clear <form>` | `formclear` | Clear all fields of a form. |
| `form_file <form> <field> <file> [<type>]` | `formfile` | Attach a file for upload. |
| `form_action <form> <url>` | `fa`, `formaction` | Change the action URL of a form. |
| `show [<what>]` | | Show `html` (default), `forms`, `links`, `history`, `cookies`, `headers`. |
| `show_html` | `showhtml` | Show the HTML of the current page. |
| `show_links` | `showlinks` | Show all links on the page. |
| `show_history` | `showhistory` | Show the browser history. |
| `show_headers` | | Show the response headers of the current page. |
| `info` | | Show URL, status, content type and other page info. |
| `echo <text> ...` | | Print text. |
| `save_html [<file>]` | | Save the page as text (HTML). |
| `save_content [<file>]` | | Save the raw bytes, e.g. a PDF or XLSX download. |
| `redirect_output <file>` | | Append all output, including error messages, to a file. |
| `reset_output` | | Send output to the screen again. |
| `redirect_error <file>` | | Append Python's stderr (warnings, `run` output) to a file. |
| `reset_error` | | Send stderr to the screen again. |
| `show_cookies` | `showcookies` | Show the current cookies. |
| `save_cookies <file>` | | Save the cookies to a file. |
| `load_cookies <file>` | | Load cookies from a file. |
| `clear_cookies` | | Delete all cookies. |
| `add_auth <realm> <uri> <user> <password>` | | Add HTTP basic auth credentials. |
| `add_extra_header <name> <value>` | | Send this header with every request. |
| `show_extra_headers` | | Show the extra request headers. |
| `clear_extra_headers` | | Remove all extra request headers. |
| `agent <name-or-string>` | | Set the User-Agent (e.g. `firefox_106`, see `twill.agents`). |
| `timeout [<seconds>]` | | Set the request timeout (default 10, 0 for none). |
| `sleep [<seconds>]` | | Wait (default 1 second). |
| `reset_browser [<base_url>]` | | Reset browser, cookies and options. |
| `set_global <name> <value>` | `setglobal` | Set a global variable. |
| `set_local <name> <value>` | `setlocal` | Set a variable for the current file. |
| `run <python>` | | Execute a Python statement. |
| `run_file <file> ...` | `runfile`, `rf` | Run other twill scripts or directories, keeping the browser state. |
| `add_cleanup <file> ...` | | Run these scripts when the current file ends. |
| `extend_with <module>` | | Import commands from a Python module. |
| `get_input <prompt>` | `getinput` | Read input into `__input__`. |
| `get_password <prompt>` | `getpassword` | Read hidden input into `__password__`. |
| `config [<key> [<value>]]` | | Show or set options, e.g. `tidy_*`. |
| `debug <what> <0/1>` | | Trace `http`, `equiv-refresh` or `commands`. |
| `exit [<code>]` | | Stop the script with this exit code. |
<!-- commands:end -->

## Pitfalls

1. **`go` does not fail on 404 or 500.** Follow it with `code 200` (or the
   expected code). Redirects are followed; `code` and `url` see the final
   response.
2. **`find` searches the HTML source with a Python regex**, case-sensitively,
   not the rendered text. Escape `.`, `?`, `(`, `+` etc. with `\` and match
   entities as they appear in the source (`&amp;`), or use XPath:
   `find "//h1[contains(., 'Welcome')]" x`.
3. **`follow` takes a regex**, searched in the link text (including nested
   markup) and in the `href`. In the URL, entities are already decoded:
   for `<a href="list?page=2&amp;sort=name">` use `follow "page=2&sort=name"`,
   and escape `?` (`follow "list\?page=2"`).
4. **Forms and fields in `fv`.** Run `show_forms` first. The form is matched
   by `id`, then by a regex on its `name`, then by number (1-based). The field
   is matched by exact `id`, exact `name`, number, regex on the `name`, and
   finally by the value of a submit button. A regex that matches several
   fields is an error ("multiple matches"). Fields outside any `<form>` form
   their own form, which shifts the numbering, so check `show_forms`.
5. **Field values in `fv`:**
   - Single checkbox: `on`/`off`, `true`/`false`, `1`/`0` or `+`/`-`.
   - Several checkboxes with the same name: `fv 1 tags red` or `+red` checks,
     `-red` unchecks; other boxes keep their state.
   - Select: an option's value, label or visible text; for multi-selects
     `+value` adds and `-value` removes. A value that exists as given (such
     as `-1`) is never read as a prefix. Disabled options cannot be selected.
   - Radio buttons: the value of the button to select.
   - Read-only fields are skipped silently unless
     `config readonly_controls_writeable 1`.
   - File fields need `form_file`, not `fv`.
6. **`submit`** submits the form last touched by `fv`. Without a button
   name it uses the button last "clicked" via `fv`, else the first submit
   button of the form, else submits without a button. With several submit
   buttons, name the one you want: `submit save`.
7. **Downloads:** use `save_content`, not `save_html`, for binary files.
   Without a filename it uses `Content-Disposition` or the URL. Check the
   type first with `header content-type ^application/pdf`.
8. **`tidy_ok` is strict.** For example, empty icon elements
   (`<i class="icon"></i>`) fail with "trimming empty <i>"; allow them with
   `config tidy_drop_empty_elements no`. Any HTML Tidy option can be set as
   `config tidy_<option_with_underscores> <value>`. Without PyTidyLib the
   check passes silently unless `config require_tidy 1`.
9. **Debugging a failing step:** `show`, `show_forms`, `show_links`,
   `show_headers`, `info`, `debug http 1`, or run with `-d page.html`.

## Examples

Log in and check the result:

```text
# run with: twill -s BASE=http://localhost:8080 login.twill
go ${BASE}/login
code 200
fv 1 username alice
submit
code 200
title "Hello"
find "logged in as (\w+)"
echo "user is ${__match__}"
follow "log out"
find "logged in as guest"
```

Check and save a download:

```text
# run with: twill -s BASE=http://localhost:8080 -s OUT=/tmp download.twill
go ${BASE}/download/report.pdf
code 200
header content-type ^application/pdf
save_content ${OUT}/report.pdf
```

Follow a link with a query string:

```text
go ${BASE}/query_links
follow "page=2&sort=name"
url "/echo\?page=2"
find "page=2, sort=name"
```

## Using twill from Python

```python
from twill import browser
from twill.commands import code, find, fv, go, submit

go("http://localhost:8080/login")
fv("1", "username", "alice")
submit()
code(200)
user = find(r"logged in as (\w+)")  # returns the match, here "alice"
print(browser.url, browser.title, browser.code)
```

- All command functions take string arguments.
- `browser` exposes `url`, `code`, `title`, `html`, `dump` (raw bytes),
  `links`, `forms`, `cookies`, `response_headers` and `history`.
- `twill.execute_file(path)` runs a script (with a fresh browser);
  `twill.execute_string(text)` runs commands and keeps the browser state.
- `twill.set_output(StringIO())` captures the output.
- Failed assertions raise `twill.errors.TwillAssertionError`, other errors
  `twill.errors.TwillException`.

## More

- Documentation: https://twill-tools.github.io/twill/
- Everything in one file, for agents:
  https://twill-tools.github.io/twill/llms-full.txt
- Command reference: https://twill-tools.github.io/twill/commands.html
