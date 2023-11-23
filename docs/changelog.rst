.. _changelog:

=========
ChangeLog
=========

3.2.1 (released 2023-11-23)
---------------------------
* Increased the default request timeout of the twill browser to 10 seconds
  (from 5 seconds in 3.2) and added a command to change the timeout (#18).

3.2 (released 2023-11-02)
-------------------------
* The supported Python versions are now 3.8 to 3.12.
* A new method 'find_links' was added to the twill browser (#17).
* Twill now uses httpx_ instead of requests_.
* WSGI apps are now supported via httpx, wsgi_intercept is not needed anymore.
* We now use 'pyproject.toml' instead of 'setup.py'.
* Type hints and code style have been improved and are checked with ruff.
* Internal code was reformatted using ruff format (compatible with black).

3.1 (released 2022-10-30)
-------------------------
* The submit command now takes an additional parameter to specify a form
  that can be used in rare cases when there are no form fields (#7).
* Most commands do not return values any more, they are just commands.
  If you are using twill from Python, you should check browser properties
  like 'forms' or 'url' instead of using the return values of commands
  like 'show_forms' or 'back' (see #13, #14).
* Two-word commands now consistently have underscores in their names,
  (e.g. 'form_action', 'get_input', 'show_links'). However, for convenience
  and backward compatibility, you can still use the names without underscores
  (e.g. 'formaction', 'getinput', 'showlinks'), and the old two-letter
  abbreviations (e.g. 'fa' for 'form_action') (#13, #14).
* Instead of 'showforms' or 'show_forms' you can now also write 'show forms',
  and similarly for 'cookies', 'links', 'history' and 'html'. The command
  'show html' does the same as 'show' without any arguments.
* Renamed shortcuts for user agent strings, and added some more existing ones.
* Added type hints (#15).
* Support Python 3.11.
* Many minor fixes and improvements.

3.0.3 (released 2022-10-12)
---------------------------

* Form numbers are now printed correctly with 'showforms' (#12).

3.0.2 (released 2022-04-10)
---------------------------

* Save HTML file with browser encoding or as UTF-8 (#9).
* Do not modify root logger any more (#10).

3.0.1 (released 2021-12-04)
---------------------------

* This version now also supports Python 3.10.
* The twill language now allows 8-bit letters to appear in strings unquoted.

3.0 (released 2021-02-25)
-------------------------

* In this version we require Python 3.6 to 3.9.
  If you still need support for Python 2 or Python 3.5,
  then please use the latest version from the 2.x branch.
* The code has been optimized for Python 3 now.
* Some minor fixes.

2.0.3 (released 2021-02-25)
---------------------------

* Backported the fixes in version 3.0.

2.0.2 (released 2021-02-13)
---------------------------

* This version now also supports Python 3.9.
* 'tidy_should_exist' has been renamed ot 'require_tidy'.
* Support for setting options to be used with HTML Tidy.
* Cleanup scripts are now also read as UTF-8 in Python 3.

2.0.1 (released 2020-07-12)
---------------------------

* Fixes an issue with encoding declarations (#5).

2.0 (released 2020-04-04)
-------------------------

This version is based on twill 1.8, which was a refactoring
of version 0.9 that used requests_ and lxml_ instead of mechanize_,
done by Ben Taylor in April 2014. It also integrates ideas and
code from Flunc_ which was created by Luke Tucker and Robert Marianski
in 2006-2007, and from ReTwill_ which was created in April 2012
as a fork from twill 0.9 by Adam Victor Brandizzi.
The following improvements and changes were made in this version:

* Larger refactoring, clean-up and modernization efforts to support
  Python 2.7, 3.5 and higher.
* The console script has been renamed from 'twill-sh' to just 'twill'.
* We assume the default file extension '.twill' for twill scripts now.
* Uses lxml_ and requests_ instead of mechanize_ (like in version 1.8),
  but doesn't need cssselect_ and `Beautiful Soup`_ any more (unlike 1.8).
* Removed bundled packages which have become unnecessary (mechanize)
  or are available in newer versions on PyPI (pyparsing, wsgi_intercept)
  or in the standard library (subprocess).
* Removed parsing options (use_tidy, use_BeautifulSoup, allow_parse_errors)
  which have become insignificant due to the use of lxml.html.
* We use pytest_ instead of nose_ for testing twill now.
* A tox_ configuration file for running tests with different Python versions
  has been added.
* Optimized the order of the URLs that are tried out by the twill browser.
* Added an option '-d' to dump the last HTML to a file or standard output
  and an option '-w' to show the HTML directly in the web browser (this
  feature was taken over from Flunc).
* Added alias 'rf' for 'runfiles' and made runfiles run directories of
  scripts as well. This helps writing test suites for twill scripts.
* Added command 'add_cleanup' to unconditionally run cleanup scripts after
  the current script finished. This allows resetting the state of the
  tested server, so that tests will always re-run on a clean state.
  Together with a small init.twill script, this creates a test fixture.
  (This idea was taken from Flunc, which supports cleanup scripts for
  test suites, although in a somewhat different way.)
* Non string values are now accepted in variable substitution (this feature
  has been backported from ReTwill).
* XPath expressions are now supported in find/notfind commands (this feature
  has been backported from ReTwill).
* Made output better controllable by using log levels (this feature has
  been backported from ReTwill). See options '-l' and '-o'.
* Updated the map of predefined user agent strings.
* Basic authentication with realm is now supported again
  (the 'with_default_realm' option, which was broken in version 1.8,
  has been switched off).
* Server certificates are not verified by default any more, since they are
  usually not valid on test and staging servers.
* Improved handling of meta refresh. Circular redirects are detected and
  'debug equiv-refresh' is functional again. A limit for the refresh time
  interval can be set with the 'equiv_refresh_interval' option. By default
  this is set to 2, so refresh intervals of 2 or more seconds are ignored.
* Moved the  examples and additional stuff into an 'extras' directory.
* The documentation in the 'docs' directory has been updated and is now
  created with Sphinx_.
* Made sure everything (except twill-forks) also works on Windows.
* Fixed a lot of smaller and larger bugs and problems.

.. _lxml: https://lxml.de/
.. _requests: https://requests.readthedocs.io/
.. _httpx: https://www.python-httpx.org/
.. _mechanize: https://mechanize.readthedocs.io/
.. _cssselect: https://github.com/scrapy/cssselect
.. _Beautiful Soup: https://www.crummy.com/software/BeautifulSoup/
.. _Flunc: https://www.coactivate.org/projects/flunc/project-home
.. _Retwill: https://bitbucket.org/brandizzi/retwill/
.. _Sphinx: https://www.sphinx-doc.org/
.. _pytest: https://pytest.org/
.. _nose: https://nose.readthedocs.io/
.. _tox: https://tox.readthedocs.io/
