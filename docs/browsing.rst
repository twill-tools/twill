.. _browsing:

=======================
Web browsing with twill
=======================

twill strives to be a complete implementation of a web browser,
omitting only JavaScript support. It includes support for cookies,
basic authentication, and trickery such as "meta refresh" redirects.

twill implements a variety of :ref:`commands <commands>`.
With the built-in language, you can do things like go to a specific URL;
follow links; fill out forms and submit them; save, load,
and delete cookies; and change the user agent string. You can also
easily extend twill with new and specialized commands using Python.

.. _commands: commands.html

Using twill interactively
~~~~~~~~~~~~~~~~~~~~~~~~~

The twill command line script lets you interactively browse the Web.
It features built-in help, e.g. "help go" will describe the command 'go'
to you; command-line completion with the TAB key; and history browsing
with the UP/DOWN arrow keys.

Command-line options
~~~~~~~~~~~~~~~~~~~~

When you pass one or more twill scripts on the command line, twill runs
them one after another and reports how many of them succeeded. Without
scripts, or with the ``-i`` option, it starts the interactive shell::

   usage: twill [-h] [-d DUMPFILE] [-f] [-i] [-l LOGLEVEL] [-n] [-o OUTFILE]
                [-q] [-s NAME=VALUE] [-u URL] [-v] [-w]
                [SCRIPT ...]

   positional arguments:
     SCRIPT                the twill script to execute

   options:
     -h, --help            show this help message and exit
     -d, --dump-html DUMPFILE
                           dump HTML to this file on error
     -f, --fail            fail exit on first file to fail
     -i, --interactive     drop into an interactive shell (after running files)
     -l, --loglevel LOGLEVEL
                           set the logging level
     -n, --never-fail      continue executing scripts past errors
     -o, --output OUTFILE  print log to output file
     -q, --quiet           do not show normal output
     -s, --set NAME=VALUE  set a global variable (can be repeated)
     -u, --url URL         start at the given URL before each script
     -v, --version         show version information and exit
     -w, --show-error-in-browser
                           show dumped HTML in a web browser

Passing values to scripts
~~~~~~~~~~~~~~~~~~~~~~~~~

With ``-s NAME=VALUE`` or ``--set NAME=VALUE`` you can set global variables
on the command line, exactly as the 'setglobal' command does. The variables
are set before the first script runs, so they can be used in all scripts
and in the interactive shell. For instance, if the script ``save.twill``
contains the line ``save_html ${D}/page.html``, you can run it as::

   $ twill -s D=/tmp/output save.twill

The option can be repeated. The name must be a valid Python identifier that
is not also the name of a twill command. The value can be empty and can
contain equal signs.

There are two alternatives:

 * Arguments after ``--`` are passed to the scripts as positional arguments.
   You can load them into the variables ``arg1``, ``arg2``, ... with the
   :ref:`argparse extension <extensions>`.

 * Environment variables can be read via Python's ``os.environ``, since
   expressions in ``${...}`` are evaluated as Python code::

      run "import os"
      save_html "${os.environ['D']}/page.html"

Proxy servers
~~~~~~~~~~~~~

twill understands the ``http_proxy`` environment variable generically
used to set proxy server information. To use a proxy in UNIX or
Windows, just set the ``http_proxy`` environment variable, e.g.::

   % export http_proxy="http://www.someproxy.com:3128"

or::

   % setenv http_proxy="http://www.someotherproxy.com:3148"

Recording scripts
~~~~~~~~~~~~~~~~~

Writing twill scripts is boring. One simple way to get at least a
rough initial script is to use the MaxQ_ recorder to generate a twill
script. MaxQ_ acts as an HTTP proxy and records all HTTP traffic; I
have written a simple twill script generator for it. The script
generator and installation docs are included in the twill distribution
under the directory ``extras/maxq``.

.. _MaxQ: http://maxq.tigris.org/

Miscellaneous implementation details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 * twill ignores robots.txt.

 * http-equiv=refresh headers are handled immediately, independent of the
   'pause' component of the 'content' attribute.

 * twill ignores JavaScript.

Using HTML Tidy to check for broken HTML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `HTML Tidy`_ tool can be used to check and clean up broken HTML
pages. You can use it with the 'tidy_ok' command to assert that it
reports no warnings or errors. In order to use this command in twill,
you need to install the `PyTidyLib`_ package. If it is not installed,
twill will silently ignore it. It may be desirable to *require* a
functioning ``PyTidyLib`` installation; so, to fail when it *isn't*
installed, set ``config require_tidy 1``.

.. _HTML Tidy: http://www.html-tidy.org/
.. _PyTidyLib: https://pythonhosted.org/pytidylib/
