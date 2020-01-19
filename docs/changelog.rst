.. _changelog:

=========
ChangeLog
=========

2.0 (released ... 2020)
-----------------------

This version is based on twill 1.8, which was a refactoring
of version 0.9 that used requests_ and lxml_ instead of mechanize,
done by Ben Taylor in April 2014.  It also integrates ideas and
code from Flunc_ which was created by Luke Tucker and Robert Marianski
in 2006-2007, and from ReTwill_ which was created in April 2012
as a fork from twill 0.9 by Adam Victor Brandizzi.
The following improvements and changes were made in this version:

* Larger refactoring, clean-up and modernization efforts to support
  Python 2.7, 3.5 and higher.
* The console script has been renamed from 'twill-sh' to just 'twill'.
* We assume the default file extension '.twill' for twill scripts now.
* Uses lxml_ and requests_ instead of mechanize (like in version 1.8),
  but doesn't need cssselect and BeautifulSoup any more (unlike 1.8).
* Removed bundled packages which have become unnecessary (mechanize)
  or are available in newer versions on PyPI (pyparsing, wsgi_intercept)
  or in the standard library (subprocess).
* Removed parsing options (use_tidy, use_BeautifulSoup, allow_parse_errors)
  which have become insignificant due to the use of lxml.html.
* We use py.test instead of nosetests for testing twill now.
* Optimized the order of the URLs that are tried out by the twill browser.
* Added an option '-d' to dump the last HTML to a file or standard output
  and an option '-w' to show the HTML directly in the web browser (this
  feature was taken over from Flunc).
* Add alias 'rf' for 'runfiles' and made runfiles run directories of
  scripts as well. This helps writing test suites for twill scripts.
* Add command 'add_cleanup' to unconditionally run cleanup scripts after
  the current script finished. This allows resetting the state of the
  tested server, so that tests will always re-run on a clean state.
  Together with a small init.twill script, this creates a test fixture.
  (This idea was taken from Flunc, which supports cleanup scripts for
  test suites, although in a somewhat different way.)
* Accept non string values in variable substitution (this feature has
  been backported from ReTwill).
* Support XPath expressions in find/notfind commands (this feature has
  been backported from ReTwill).
* Make output better controllable by using log levels (this feature has
  been backported from ReTwill). See options '-l' and '-o'.
* Updated the map of predefined user agent strings.
* Support basic authentication with realm again (with_default_realm option
  switched off, which was broken in version 1.8).
* Server certificates are not verified by default, since they are usually
  not valid on test and staging servers.
* Improved handling of meta refresh. Circular redirects are detected and
  'debug equiv-refresh' is functional again. A limit for the refresh time
  interval can be set with the 'equiv_refresh_interval' option. By default
  this is set to 2, so refresh intervals of 2 or more seconds are ignored.
* Moved the  examples and additional stuff into an 'extras' directory.
* Made sure everything (except twill-forks) also works on Windows.
* Fixed a lot of smaller and larger bugs and problems.

.. _lxml: https://lxml.de/
.. _requests: https://2.python-requests.org/en/master/
.. _Flunc: https://www.coactivate.org/projects/flunc/project-home
.. _Retwill: https://bitbucket.org/brandizzi/retwill/