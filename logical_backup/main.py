# pylint: disable=fixme
"""
A utility which allows for customized backing up of files
spread across multiple hard disks

This allows expansion over time without having to reorganize data
and will allow generic restoration of data, as long as the hard drives
are maintained
"""

import argparse
from os.path import isfile, isdir
import sys

from logical_backup.db import initialize_database


def __prepare():
    """
    Set up database if needed, and check if hard drives are present
    """
    # This is non-destructive; will only create tables if needed
    initialize_database()

    # TODO: get existing hard drives, see if any are present
    # TODO: provide output for that


def __parse_arguments() -> tuple:
    """
    Parses command line arguments

    Returns
    -------
    dict
        arguments
    """
    parser = argparse.ArgumentParser(
        description="Back up and restore files across multiple hard drives"
    )
    parser.add_argument(
        "action",
        help="The action to take",
        choices=["add", "move", "remove", "verify", "restore"],
    )
    parser.add_argument("--file", help="The file to take action on", required=False)
    parser.add_argument("--folder", help="The file to take action on", required=False)
    parser.add_argument(
        "--all",
        help="Perform operation on all files",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--move-path",
        dest="move_path",
        help="Target for move operation",
        required=False,
    )
    args = parser.parse_args()
    return vars(args)


# pylint: disable=unused-argument
def __validate_arguments(arguments: dict) -> bool:
    """
    Determines if the given command-line arguments are valid

    Parameters
    ----------
    arguments : dict
        Configured arguments from the command line,
        in dictionary form for easier injection with testing

    Returns
    -------
    bool
        True if argument combination is valid
    """
    # Exactly one of each sub-array must be specified for the given action
    required_parameter_set_by_action = {
        "add": [["file", "folder"]],
        "move": [["file", "folder"], ["move_path"]],
        "remove": [["file", "folder"]],
        "restore": [["file", "folder", "all"]],
        "verify": [["file", "folder", "all"]],
    }

    command_valid = True
    # Check at least one of each command set required is in the arguments
    for command_set in required_parameter_set_by_action[arguments["action"]]:

        commands_in_set_found = 0
        for command in command_set:
            if arguments[command]:
                commands_in_set_found += 1

        if commands_in_set_found != 1:
            command_valid = False
            break

    path_exists = True
    if arguments["file"]:
        path_exists = isfile(arguments["file"])
    elif arguments["folder"]:
        path_exists = isdir(arguments["folder"])
    return command_valid and path_exists


def __dispatch_command(arguments: dict) -> str:
    """
    Actually process the command

    Parameters
    ----------
    arguments : dict
        The command-line arguments

    Returns
    -------
    str
        The command being called
    """
    if not __validate_arguments(arguments):
        sys.exit(1)

    # TODO: this


def process():
    """
    Run the process
    """
    args = __parse_arguments()
    __dispatch_command(args)
