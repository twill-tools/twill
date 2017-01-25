"""
A command-line interpreter for twill.

This is an implementation of a command-line interpreter based on the
'Cmd' class in the 'cmd' package of the default Python distribution.
"""

from __future__ import print_function

import os
import sys
import traceback

from cmd import Cmd
from optparse import OptionParser

try:
    import readline
except ImportError:
    readline = None

from . import (
    browser, commands, execute_file, log, loglevels, set_loglevel, set_output,
    namespaces, parse, shutdown, __url__, __version__)
from .utils import gather_filenames, Singleton

version_info = """
twill version: %s
Python Version: %s

See %s for more info.
""" % (__version__, sys.version.split(None, 1)[0], __url__)


def make_cmd_fn(cmd):
    """Make a command function.

    Dynamically define a twill shell command function based on an imported
    function name.  (This is where the twill.commands functions actually
    get executed.)
    """

    def do_cmd(rest_of_line, cmd=cmd):
        global_dict, local_dict = namespaces.get_twill_glocals()

        args = []
        if rest_of_line.strip():
            try:
                args = parse.arguments.parseString(rest_of_line)[0]
                args = parse.process_args(args, global_dict, local_dict)
            except Exception as e:
                log.error('\nINPUT ERROR: %s\n', e)
                return

        try:
            parse.execute_command(
                cmd, args, global_dict, local_dict, '<shell>')
        except SystemExit:
            raise
        except Exception as e:
            log.error('\nERROR: %s\n', e)
            log.debug(traceback.format_exc())

    return do_cmd


def make_help_cmd(cmd, docstring):
    """Make a help command function.

    Dynamically define a twill shell help function for the given
    command/docstring.
    """
    def help_cmd(message=docstring, cmd=cmd):
        message = message.strip()
        width = 7 + len(cmd)
        for line in message.splitlines():
            w = len(line.rstrip())
            if w > width:
                width = w
        info = log.info
        info('\n%s' % ('=' * width,))
        info('\nHelp for command %s:\n', cmd)
        info(message)
        info('\n%s\n' % ('=' * width,))

    return help_cmd


def add_command(cmd, docstring):
    """Add a command with given docstring to the shell."""
    shell = get_command_shell()
    if shell:
        shell.add_command(cmd, docstring)


def get_command_shell():
    """Get the command shell."""
    return getattr(TwillCommandLoop, '__it__', None)


class TwillCommandLoop(Singleton, Cmd):
    """The command-line interpreter for twill commands.

    This is a Singleton object: you can't create more than one
    of shell at a time.

    Note: most of the do_ and help_ functions are dynamically created
    by the metaclass.
    """

    def __init__(self,  stdin=None, initial_url=None, fail_on_unknown=False):
        Cmd.__init__(self, stdin=stdin)

        self.use_rawinput = stdin is None

        # initialize a new local namespace.
        namespaces.new_local_dict()

        # import readline history, if available.
        if readline:
            try:
                readline.read_history_file('.twill-history')
            except IOError:
                pass

        # fail on unknown commands? for test-shell, primarily.
        self.fail_on_unknown = fail_on_unknown

        # handle initial URL argument
        if initial_url:
            commands.go(initial_url)

        self._set_prompt()

        self.names = []

        global_dict, local_dict = namespaces.get_twill_glocals()

        # add all of the commands from twill
        for command in parse.command_list:
            fn = global_dict.get(command)
            self.add_command(command, fn.__doc__)

    def add_command(self, command, docstring):
        """Add the given command into the lexicon of all commands."""
        do_name = 'do_%s' % (command,)
        do_cmd = make_cmd_fn(command)
        setattr(self, do_name, do_cmd)

        if docstring:
            help_cmd = make_help_cmd(command, docstring)
            help_name = 'help_%s' % (command,)
            setattr(self, help_name, help_cmd)

        self.names.append(do_name)

    def get_names(self):
        """Return the list of commands."""
        return self.names

    def complete_formvalue(self, text, line, begin, end):
        """Command arg completion for the formvalue command.

        The twill command has the following syntax:

        formvalue <formname> <field> <value>
        """
        cmd, args = parse.parse_command(line + '.', {}, {})
        place = len(args)
        if place == 1:
            return self.provide_formname(text)
        elif place == 2:
            formname = args[0]
            return self.provide_field(formname, text)
        return []

    complete_fv = complete_formvalue  # alias

    def provide_formname(self, prefix):
        """Provide the list of form names on the given page."""
        names = []
        forms = browser.forms
        for form in forms:
            id = form.attrib.get('id')
            if id and id.startswith(prefix):
                names.append(id)
                continue
            name = form.attrib.get('name')
            if name and name.startswith(prefix):
                names.append(name)
        return names

    def provide_field(self, formname, prefix):
        """Provide the list of fields for the given formname or number."""
        names = []
        form = browser.form(formname)
        if form is not None:
            for field in form.inputs:
                id = field.attrib.get('id')
                if id and id.startswith(prefix):
                    names.append(id)
                    continue
                name = field.name
                if name and name.startswith(prefix):
                    names.append(name)
        return names

    def _set_prompt(self):
        """"Set the prompt to the current page."""
        url = browser.url
        if url is None:
            url = " *empty page* "
        self.prompt = "current page: %s\n>> " % (url,)

    def precmd(self, line):
        """Run before each command; save."""
        return line

    def postcmd(self, stop, line):
        """"Run after each command; set prompt."""
        self._set_prompt()
        return stop

    def default(self, line):
        """"Called when an unknown command is executed."""

        # empty lines ==> emptyline(); here we just want to remove
        # leading whitespace.
        line = line.strip()

        # look for command
        global_dict, local_dict = namespaces.get_twill_glocals()
        cmd, args = parse.parse_command(line, global_dict, local_dict)

        # ignore comments & empty stuff
        if cmd is None:
            return

        try:
            parse.execute_command(
                cmd, args, global_dict, local_dict, '<shell>')
        except SystemExit:
            raise
        except Exception as e:
            log.error('\nERROR: %s\n', e)
            if self.fail_on_unknown:
                raise

    def emptyline(self):
        """Handle empty lines (by ignoring them)."""
        pass

    def do_EOF(self, *args):
        """Exit on CTRL-D"""
        if readline:
            readline.write_history_file('.twill-history')
        raise SystemExit()

    def help_help(self):
        """Show help for the help command."""
        log.info("\nWhat do YOU think the command 'help' does?!?\n")

    def do_version(self, *args):
        """Show the version number of twill."""
        log.info(version_info)

    def help_version(self):
        """Show help for the version command."""
        log.info("\nPrint version information.\n")

    def do_exit(self, *args):
        """Exit the twill shell."""
        raise SystemExit()

    def help_exit(self):
        """Show help for the exit command."""
        log.info("\nExit twill.\n")

    do_quit = do_exit
    help_quit = help_exit


twillargs = []       # contains sys.argv *after* last '--'
interactive = False  # 'True' if interacting with user


def main():
    global twillargs, interactive

    # show the shorthand name for usage
    if sys.argv[0].endswith('-script.py'):
        sys.argv[0] = sys.argv[0].rsplit('-', 1)[0]

    # make sure that the current working directory is in the path
    if '' not in sys.path:
        sys.path.append('')

    parser = OptionParser()
    add = parser.add_option

    add('-d', '--dump-html', action='store', dest='dumpfile',
        help="dump HTML to this file on error")
    add('-f', '--fail', action='store_true', dest='fail',
        help='fail exit on first file to fail')
    add('-i', '--interactive', action='store_true', dest='interactive',
        help='drop into an interactive shell (after running files)')
    add('-l', '--loglevel', nargs=1, action='store', dest='loglevel',
        help='set the logging level')
    add('-n', '--never-fail', action='store_true', dest='never_fail',
        help='continue executing scripts past errors')
    add('-o', '--output', nargs=1, action='store', dest='outfile',
        help="print log to output file")
    add('-q', '--quiet', action='store_true', dest='quiet',
        help='do not show normal output')
    add('-u', '--url', nargs=1, action='store', dest='url',
        help='start at the given URL before each script')
    add('-v', '--version', action='store_true', dest='show_version',
        help='show version information and exit')
    add('-w', '--show-error-in-browser', action='store_true',
        dest='show_browser', help="show dumped HTML in a web browser ")

    # parse arguments
    sysargs = sys.argv[1:]
    if '--' in sysargs:
        for last in range(len(sysargs) - 1, -1, -1):
            if sysargs[last] == '--':
                twillargs = sysargs[last + 1:]
                sysargs = sysargs[:last]
                break

    options, args = parser.parse_args(sysargs)

    if options.show_version:
        log.info(version_info)
        sys.exit(0)

    quiet = options.quiet
    show_browser = options.show_browser
    dumpfile = options.dumpfile
    outfile = options.outfile
    loglevel = options.loglevel
    interactive = options.interactive or not args

    if outfile:
        outfile = outfile.lstrip('=').lstrip() or None
        if outfile == '-':
            outfile = None

    if interactive and (quiet or outfile or dumpfile or show_browser):
            sys.exit("Interactive mode is incompatible with -q, -o, -d and -w")

    if options.show_browser and (not dumpfile or dumpfile == '-'):
        sys.exit("Please also specify a dump file with -d")

    if outfile:
        try:
            outfile = open(outfile, 'w')
        except IOError as e:
            sys.exit("Invalid output file '%s': %s", options.outfile, e)

    if loglevel:
        loglevel = loglevel.lstrip('=').lstrip() or None
        if loglevel.upper() not in loglevels:
            sys.exit("Valid log levels are %s" % ', '.join(sorted(loglevels)))
        set_loglevel(loglevel)

    if quiet:
        outfile = open(os.devnull, 'w')

    set_output(outfile)

    # first find and run any scripts put on the command line

    failed = False
    if args:
        success = []
        failure = []

        filenames = gather_filenames(args)
        dump = None

        for filename in filenames:
            try:
                interactive = False
                execute_file(filename, initial_url=options.url,
                             never_fail=options.never_fail)
                success.append(filename)
            except Exception as e:
                if dumpfile:
                    dump = browser.dump
                if options.fail:
                    raise
                else:
                    if browser.first_error:
                        log.error('\nFirst error: %s', browser.first_error)
                    log.error('\n*** ERROR: %s', e)
                    log.debug(traceback.format_exc())
                    failure.append(filename)

        log.info('--')
        if dump:
            if dumpfile == '-':
                log.info('HTML when error was encountered:\n\n%s\n--',
                         dump.strip())
            else:
                try:
                    with open(dumpfile, 'wb') as f:
                        f.write(dump)
                except IOError as e:
                    log.error('Could not dump to %s: %s\n', dumpfile, e)
                else:
                    log.info('HTML has been dumped to %s\n', dumpfile)

        log.info('%d of %d files SUCCEEDED.',
                 len(success), len(success) + len(failure))
        if len(failure):
            log.error('Failed:\n\t%s', '\n\t'.join(failure))
            failed = True

        if dump and show_browser:
            import webbrowser

            url = 'file:///%s' % (
                os.path.abspath(dumpfile).replace(os.sep, '/'),)
            log.debug('Running web browser on %s', url)
            webbrowser.open(url)

    # if no scripts to run or -i is set, drop into an interactive shell

    if interactive:
        welcome_msg = "" if args else "\n -= Welcome to twill =-\n"

        shell = TwillCommandLoop(initial_url=options.url)

        while True:
            try:
                shell.cmdloop(welcome_msg)
            except KeyboardInterrupt:
                print()
                break
            except SystemExit:
                raise

            welcome_msg = ""

    shutdown()

    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
