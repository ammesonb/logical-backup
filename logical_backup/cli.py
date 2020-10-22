"""
CLI for interactive mode
"""
from typing import List

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.command_completion import set_completion

# Actions being or awaiting execution
QUEUED_ACTIONS = []
# Actions that have been completed
COMPLETED_ACTIONS = []

# How many threads to use
THREAD_COUNT = 1
# How many threads are active
# Should equal thread_count, excepting decreases in thread count
# which will not kill running processes
ACTIVE_THREADS = 1


def _generate_prompt() -> str:
    """
    Input prompt to use for read step of REPL
    """
    return "[{0}/{1}:{2}] >".format(
        len(QUEUED_ACTIONS), len(QUEUED_ACTIONS) + len(COMPLETED_ACTIONS), THREAD_COUNT
    )


def _read_input() -> str:
    """
    Reads input for REPL
    """
    return input(_generate_prompt())


def _parse_input(arguments: dict) -> List[BaseAction]:
    """
    Evaluates inputs for REPL
    """
    return []


def run():
    """
    Loop portion of REPL
    """
    set_completion()

    stop = False
    while not stop:
        arguments = _read_input()

        if arguments["exit"]:
            stop = True
        else:
            actions = _parse_input(arguments)
            QUEUED_ACTIONS.extend(actions)


def _set_thread_count(threads: int) -> None:
    """
    Sets thread count for background actions running
    """
    global THREAD_COUNT
    THREAD_COUNT = threads
