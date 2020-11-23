"""
Utility functions for interacting with arguments
"""

import argparse

from logical_backup.strings import Arguments, Commands, Info, Targets


def get_argument_parser(interactive: bool = False) -> argparse.ArgumentParser:
    """
    Gets valid arguments for environment

    Parameters
    ----------
    interactive = False : bool
        Whether running interactively or from CLI

    Returns
    -------
    argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=(str(Info.PROGRAM_DESCRIPTION)),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    actions = [
        str(Commands.ADD),
        str(Commands.MOVE),
        str(Commands.REMOVE),
        str(Commands.UPDATE),
        str(Commands.VERIFY),
        str(Commands.RESTORE),
        str(Commands.LIST_DEVICES),
        str(Commands.SEARCH),
    ]

    if interactive:
        actions.extend(
            [
                str(Commands.STATUS),
                str(Commands.SET_THREADS),
                str(Commands.REORDER),
                str(Commands.CLEAR),
                str(Commands.HELP),
                str(Commands.MESSAGES),
                str(Commands.EXIT),
            ]
        )
        parser.add_argument("values", nargs="*", default=[])
    else:
        actions.append(str(Commands.INTERACTIVE))

    parser.add_argument("action", help=str(Info.ACTION), choices=actions)
    parser.add_argument(
        str(Targets.FILE), help=str(Info.TARGET_FILE_HELP), required=False
    )
    parser.add_argument(
        str(Targets.FOLDER), help=str(Info.TARGET_FOLDER_HELP), required=False
    )
    parser.add_argument(
        str(Targets.DEVICE), help=str(Info.TARGET_DEVICE_HELP), required=False
    )
    parser.add_argument(
        str(Targets.FROM_DEVICE),
        dest=str(Arguments.FROM_DEVICE),
        help=str(Info.TARGET_FROM_DEVICE_HELP),
        required=False,
    )
    parser.add_argument(
        str(Targets.ALL),
        help=str(Info.TARGET_ALL_HELP),
        action="store_true",
        required=False,
    )
    parser.add_argument(
        str(Targets.MOVE_PATH),
        dest=str(Arguments.MOVE_PATH),
        help=str(Info.TARGET_MOVE_PATH_HELP),
        required=False,
    )
    parser.add_argument(
        str(Targets.THREADS),
        dest=str(Arguments.THREADS),
        help=str(Info.ARGUMENT_THREADS_HELP),
        required=False,
    )

    return parser
