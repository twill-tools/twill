"""Code parsing and evaluation for the twill mini-language."""

import re
import sys

from io import StringIO

from pyparsing import (
    alphas, alphanums, CharsNotIn, Combine, Group, Literal, Optional,
    ParseException, printables, removeQuotes, restOfLine, Word, ZeroOrMore)

from . import browser, commands, log, namespaces
from .errors import TwillNameError

try:
    basestring
except NameError:  # Python 3
    basestring = str


# pyparsing stuff

# basically, a valid Python identifier:
command = Word(alphas + '_', alphanums + '_')
command = command.setResultsName('command')
command.setName('command')

# arguments to it.

# we need to reimplement all this junk from pyparsing because pcre's
# idea of escapable characters contains a lot more than the C-like
# thing pyparsing implements
_bslash = '\\'
_sglQuote = Literal("'")
_dblQuote = Literal('"')
_escapables = printables
_escapedChar = Word(_bslash, _escapables, exact=2)
dblQuotedString = Combine(
    _dblQuote + ZeroOrMore(CharsNotIn('\\"\n\r') | _escapedChar | '""') +
    _dblQuote).streamline().setName("string enclosed in double quotes")
sglQuotedString = Combine(
    _sglQuote + ZeroOrMore(CharsNotIn("\\'\n\r") | _escapedChar | "''") +
    _sglQuote).streamline().setName('string enclosed in single quotes')
quotedArg = (dblQuotedString | sglQuotedString)
quotedArg.setParseAction(removeQuotes)
quotedArg.setName('quotedArg')

plainArgChars = printables.replace('#', '').replace('"', '').replace("'", "")
plainArg = Word(plainArgChars)
plainArg.setName('plainArg')

arguments = Group(ZeroOrMore(quotedArg | plainArg))
arguments = arguments.setResultsName('arguments')
arguments.setName('arguments')

# comment line.
comment = Literal('#') + restOfLine
comment = comment.suppress()
comment.setName('comment')

full_command = comment | (command + arguments + Optional(comment))
full_command.setName('full_command')


command_list = []  # filled in by namespaces.init_global_dict().


def process_args(args, globals_dict, locals_dict):
    """Process string arguments.

    Take a list of string arguments parsed via pyparsing and evaluate
    the special variables ('__*').

    Return a new list.
    """
    newargs = []
    for arg in args:
        # __variable substitution
        if arg.startswith('__'):
            try:
                val = eval(arg, globals_dict, locals_dict)
            except NameError:  # not in dictionary; don't interpret
                val = arg

            log.info('VAL IS %s FOR %s', val, arg)

            if isinstance(val, basestring):
                newargs.append(val)
            else:
                newargs.extend(val)

        # $variable substitution
        elif arg.startswith('$') and not arg.startswith('${'):
            try:
                val = str(eval(arg[1:], globals_dict, locals_dict))
            except NameError:  # not in dictionary; don't interpret
                val = arg
            newargs.append(val)
        else:
            newargs.append(variable_substitution(arg, globals_dict, locals_dict))

    newargs = [arg.replace('\\n', '\n') for arg in newargs]
    return newargs


def execute_command(cmd, args, globals_dict, locals_dict, cmdinfo):
    """Actually execute the command.

    Side effects: __args__ is set to the argument tuple, __cmd__ is set to
    the command.
    """
    global command_list  # all supported commands
    # execute command
    locals_dict['__cmd__'] = cmd
    locals_dict['__args__'] = args
    if cmd not in command_list:
        raise TwillNameError("unknown twill command: '%s'" % (cmd,))

    eval_str = "%s(*__args__)" % (cmd,)

    # compile the code object so that we can get 'cmdinfo' into the
    # error tracebacks
    codeobj = compile(eval_str, cmdinfo, 'eval')

    # eval the codeobj in the appropriate dictionary
    result = eval(codeobj, globals_dict, locals_dict)

    # set __url__
    locals_dict['__url__'] = browser.url

    return result


_log_commands = log.debug


def parse_command(line, globals_dict, locals_dict):
    """Parse command."""
    try:
        res = full_command.parseString(line)
    except ParseException as e:
        log.error('PARSE ERROR: %s', e)
        res = None
    if res:
        _log_commands("twill: executing cmd '%s'", line.strip())
        args = process_args(res.arguments.asList(), globals_dict, locals_dict)
        return res.command, args
    return None, None  # e.g. a comment


def execute_string(buf, **kw):
    """Execute commands from a string buffer."""
    if isinstance(buf, bytes):  # Python 2
        try:
            buf = buf.decode('utf-8')
        except UnicodeDecodeError:
            buf = buf.decode('latin-1')

    fp = StringIO(buf)

    kw['source'] = ['<string buffer>']
    if 'no_reset' not in kw:
        kw['no_reset'] = True

    _execute_script(fp, **kw)


def execute_file(filename, **kw):
    """Execute commands from a file."""
    inp = sys.stdin if filename == '-' else open(filename)

    log.info('\n>> Running twill file %s', filename)

    kw['source'] = filename
    _execute_script(inp, **kw)


def _execute_script(inp, **kw):
    """Execute lines taken from a file-like iterator."""
    # initialize new local dictionary and get global and current local
    namespaces.new_local_dict()
    globals_dict, locals_dict = namespaces.get_twill_glocals()

    locals_dict['__url__'] = browser.url

    # reset browser
    if not kw.get('no_reset'):
        commands.reset_browser()

    # go to a specific URL?
    init_url = kw.get('initial_url')
    if init_url:
        commands.go(init_url)
        locals_dict['__url__'] = browser.url

    # should we catch exceptions on failure?
    catch_errors = kw.get('never_fail')

    # sourceinfo stuff
    sourceinfo = kw.get('source', "<input>")

    try:

        for n, line in enumerate(inp, 1):
            line = line.strip()
            if not line:  # skip empty lines
                continue

            cmdinfo = '%s:%d' % (sourceinfo, n)
            log.info('AT LINE: %s', cmdinfo)

            cmd, args = parse_command(line, globals_dict, locals_dict)
            if cmd is None:
                continue

            try:
                execute_command(cmd, args, globals_dict, locals_dict, cmdinfo)
            except SystemExit:
                # abort script execution if a SystemExit is raised
                return
            except Exception as e:
                error_type = e.__class__.__name__ or 'Error'
                error = "%s raised on line %d of '%s'" % (
                    error_type, n, sourceinfo)
                if line:
                    error += " while executing\n>> %s" % (line,)
                log.error("\nOops! %s", error)
                if not browser.first_error:
                    browser.first_error = error
                log.error("\nError: %s", str(e).strip())
                if not catch_errors:
                    raise

    finally:
        cleanups = locals_dict.get('__cleanups__')
        if cleanups:
            error = browser.first_error
            result = browser.result
            for filename in reversed(cleanups):
                log.info('\n>> Running twill cleanup file %s', filename)
                try:
                    inp = open(filename)
                    _execute_script(inp, source=filename, no_reset=True)
                except Exception as e:
                    log.error('>> Cannot run cleanup file %s: %s', filename, e)
            browser.reset()
            browser.first_error = error
            browser.result = result
        namespaces.pop_local_dict()


def log_commands(flag):
    """Turn printing of commands as they are executed on or off."""
    global _log_commands
    old_flag = _log_commands is log.info
    _log_commands = log.info if flag else log.debug
    return old_flag


_re_variable = re.compile("\${(.*?)}")


def variable_substitution(raw_str, globals_dict, locals_dict):
    s = []
    pos = 0
    for m in _re_variable.finditer(raw_str):
        s.append(raw_str[pos:m.start()])
        try:
            s.append(str(eval(m.group(1), globals_dict, locals_dict)))
        except NameError:
            s.append(m.group())
        pos = m.end()
    s.append(raw_str[pos:])
    return ''.join(s)
