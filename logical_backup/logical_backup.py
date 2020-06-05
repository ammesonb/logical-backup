# pylint: disable=fixme
"""
A utility which allows for customized backing up of files
spread across multiple hard disks

This allows expansion over time without having to reorganize data
and will allow generic restoration of data, as long as the hard drives
are maintained
"""

import argparse

from db import initialize_database


def __prepare():
    """
    Set up database if needed, and check if hard drives are present
    """
    # This is non-destructive; will only create tables if needed
    initialize_database()

    # TODO: get existing hard drives, see if any are present
    # TODO: provide output for that


def __parse_arguments() -> argparse.ArgumentParser:
    """
    Parses command line arguments

    Returns
    -------
        An ArgumentParser instance
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
    parser.parse_args()
    return parser


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
    return True


def __dispatch_command(arguments: argparse.ArgumentParser):
    """
    Actually process the command

    Parameters
    ----------
    arguments : argparse.ArgumentParser
        -
    """
    if not __validate_arguments(vars(arguments)):
        return

    # TODO: this


if __name__ == "__main__":
    args = __parse_arguments()
    __dispatch_command(args)
