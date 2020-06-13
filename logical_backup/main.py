# pylint: disable=fixme
"""
A utility which allows for customized backing up of files
spread across multiple hard disks

This allows expansion over time without having to reorganize data
and will allow generic restoration of data, as long as the hard drives
are maintained
"""

import argparse
import os.path as path
from os.path import isfile, isdir
import sys

import logical_backup.db as db
import logical_backup.library as library
from logical_backup.pretty_print import pprint, pprint_start, pprint_complete, Color


def __prepare():
    """
    Set up database if needed, and check if hard drives are present
    """
    # This is non-destructive; will only create tables if needed
    db.initialize_database()

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
        description=(
            "Back up and restore files across multiple hard drives\n\n"
            "Actions:\n"
            "         add: add a file or folder to the backup selection\n"
            "      remove: remove a file or folder from the backup selection\n"
            "        move: move a file or folder in the backup selection, "
            "OR files/folders between devices\n"
            "     restore: restore a file/folder/all files to their original location\n"
            "      verify: check a backed-up file/folder/all files for integrity "
            "(this will NOT check the local filesystem copy, "
            "as that is assumed to be correct)\n"
            "list-devices: list all the registered backup devices\n"
            "Example uses:\n"
            "  # Will add a new device\n"
            "  add --device /mnt/dev1\n"
            "  # Will add this file to the backup set\n"
            "  add --file /home/user/foo.txt\n"
            "  # Will remove the /etc folder recursively from backup\n"
            "  remove --folder /etc\n"
            "  # Will check all backed up files for integrity\n"
            "  verify --all\n"
            "  # Will restore the documents folder from backup\n"
            "  restore /home/user/documents\n"
            "  # Will rehome the file, "
            "updating the backup archive with the new location\n"
            "  move --file /backups/large.bak --move-path /backups/archive/\n"
            "  # Will move the backed up folder from its current drive to another, "
            "if one particular drive is too full to take a needed operation\n"
            "  move --file /backups --device dev2\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "action",
        help="The action to take",
        choices=[
            "add",
            "move",
            "remove",
            "verify",
            "restore",
            "list-devices",
            "search",
        ],
    )
    parser.add_argument("--file", help="The file to take action on", required=False)
    parser.add_argument("--folder", help="The file to take action on", required=False)
    parser.add_argument("--device", help="Mount path for a device", required=False)
    parser.add_argument(
        "--from-device",
        dest="from_device",
        help="Use to restrict operation to a specific device",
        required=False,
    )
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
        "add": [["file", "folder", "device"]],
        "move": [["file", "folder"], ["move_path", "device"]],
        "remove": [["file", "folder"]],
        "restore": [["file", "folder", "all"]],
        "verify": [["file", "folder", "all"]],
    }

    command_valid = True
    path_exists = True
    # Check at least one of each command set required is in the arguments
    for command_set in required_parameter_set_by_action.get(arguments["action"], []):

        commands_in_set_found = 0
        for command in command_set:
            if arguments[command]:
                commands_in_set_found += 1

        if commands_in_set_found != 1:
            command_valid = False
            break

    if arguments["file"]:
        path_exists = isfile(arguments["file"])
    elif arguments["folder"]:
        path_exists = isdir(arguments["folder"])

    if arguments["device"]:
        path_exists = path_exists and path.ismount(arguments["device"])

    if arguments["from_device"]:
        path_exists = path_exists and path.ismount(arguments["from_device"])

    return command_valid and path_exists


def __check_devices(args: dict):
    """
    Check if any devices are defined, and if not, ensure command is adding one

    Parameters
    ----------
    arguments : dict
        Configured arguments from the command line,
        in dictionary form for easier injection with testing
    """
    message = "Checking for devices..."
    pprint_start(message, Color.BLUE)

    devices = db.get_devices()
    if not devices:
        # pylint: disable=bad-continuation
        if (args["action"] != "add" or not args["device"]) and args[
            "action"
        ] != "list-devices":
            pprint_complete(message + "None", False, Color.ERROR)
            pprint(
                "A device must be added before any other actions can occur", Color.ERROR
            )
            sys.exit(3)
        else:
            pprint_complete(message + "Missing, but OK", True, Color.YELLOW)
    else:
        for device in devices:
            device["found"] = path.ismount(device["device_path"])

        if all([device["found"] for device in devices]):
            pprint_complete(message + "All devices found", True, Color.GREEN)
        else:
            pprint_complete(message + "Found some devices:", True, Color.YELLOW)
            for device in devices:
                message = (
                    "{device_name} (Path: {device_path})\n"
                    "  {identifier_name}: {device_identifier}"
                ).format(**device)
                if device["found"]:
                    pprint_complete(message, True, Color.GREEN)
                else:
                    pprint_complete(message, False, Color.ERROR)

            confirm = input("Proceed? (y/N) ")
            if confirm != "y":
                sys.exit(3)
            pprint("Continuing without all devices", Color.YELLOW)


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

    command = ""
    if arguments["action"] == "add":
        command = "add-"
        if arguments["file"]:
            library.add_file(arguments["file"], arguments["device"])
        elif arguments["folder"]:
            library.add_folder(arguments["file"], arguments["device"])
        elif arguments["device"]:
            library.add_device(arguments["device"])

    elif arguments["action"] == "remove":
        command = "remove-"

    elif arguments["action"] == "move":
        command = "move-"

    elif arguments["action"] == "restore":
        command = "restore-"

    elif arguments["action"] == "verify":
        command = "verify-"

    elif arguments["action"] == "list-devices":
        command = "list-devices"
        library.list_devices()

    # If command is targeting a specific set of things,
    # add the thing it is targeting
    if command[-1] == "-":
        if arguments["file"]:
            command += "file"
        elif arguments["folder"]:
            command += "folder"
        elif arguments["device"]:
            command += "device"
        elif arguments["all"]:
            command += "all"

    return command


def process():
    """
    Run the process
    """
    __prepare()
    args = __parse_arguments()
    __check_devices(args)
    __dispatch_command(args)
