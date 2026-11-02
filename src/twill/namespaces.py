"""Global and local dictionaries, and initialization/utility functions."""

from typing import Any

from . import errors

global_dict: dict[str, Any] = {}  # the global dictionary


def init_global_dict() -> None:
    """Initialize the global dictionary with twill commands.

    This must be done after all the other modules are loaded, so that all
    the commands are already defined.
    """
    from . import commands, parse  # noqa: PLC0415

    cmd_list = commands.__all__
    global_dict.update((cmd, getattr(commands, cmd)) for cmd in cmd_list)
    parse.command_list.extend(cmd_list)


_local_dict_stack: list[dict[str, Any]] = []  # local dictionaries


def new_local_dict() -> dict[str, Any]:
    """Initialize a new local dictionary and push it onto the stack."""
    local_dict: dict[str, Any] = {}
    _local_dict_stack.append(local_dict)
    return local_dict


def pop_local_dict() -> dict[str, Any]:
    """Get rid of the current local dictionary."""
    return _local_dict_stack.pop()


def get_twill_glocals() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return both global and current local dictionary."""
    if global_dict is None:
        raise errors.TwillException("Must initialize global namespace first!")
    if not _local_dict_stack:
        new_local_dict()
    return global_dict, _local_dict_stack[-1]
