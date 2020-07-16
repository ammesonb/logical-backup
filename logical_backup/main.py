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

from logical_backup import db
from logical_backup import library
from logical_backup import utility
from logical_backup.pretty_print import PrettyStatusPrinter, Color, print_error


def __prepare():
    """
    Set up database if needed, and check if hard drives are present
    """
    # This is non-destructive; will only create tables if needed
    db.initialize_database()


def __parse_arguments(command_line_arguments: list) -> tuple:
    """
    Parses command line arguments

    Parameters
    ----------
    command_line_arguments : list
        Command line arguments, in list form

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
            "update",
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
    args = parser.parse_args(command_line_arguments)
    arguments = vars(args)
    arguments["file"] = utility.get_abs_path(arguments["file"])
    arguments["folder"] = utility.get_abs_path(arguments["folder"])
    arguments["device"] = utility.get_abs_path(arguments["device"])
    return arguments


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
        "update": [["file", "folder"]],
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
        path_exists = isfile(arguments["file"]) or arguments["action"] in [
            "restore",
            "verify",
        ]
    elif arguments["folder"]:
        path_exists = isdir(
            arguments["folder"] or arguments["action"] in ["restore", "verify"]
        )

    if arguments["device"] or arguments["from_device"]:
        devices = db.get_devices()

    if arguments["device"]:
        path_exists = path_exists and path.ismount(arguments["device"])
        if arguments["action"] != "add":
            path_exists = path_exists and [
                device
                for device in devices
                if device.device_path == arguments["device"]
            ]

    if arguments["from_device"]:
        path_exists = path_exists and path.ismount(arguments["from_device"])
        path_exists = path_exists and [
            device
            for device in devices
            if device.device_path == arguments["from_device"]
        ]

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
    device_message = (
        PrettyStatusPrinter("Checking for devices")
        .with_message_postfix_for_result(True, "All devices found")
        .with_message_postfix_for_result(False, "None!")
        .with_custom_result(2, True)
        .with_color_for_result(2, Color.YELLOW)
        .with_message_postfix_for_result(2, "None found, but OK")
        .with_custom_result(3, True)
        .with_color_for_result(3, Color.YELLOW)
        .with_message_postfix_for_result(3, "Found some devices:")
    )
    device_message.print_start()

    devices = db.get_devices()
    if not devices:
        # pylint: disable=bad-continuation
        if (args["action"] != "add" or not args["device"]) and args[
            "action"
        ] != "list-devices":
            device_message.print_complete(False)
            print_error("A device must be added before any other actions can occur")
            sys.exit(3)
        else:
            device_message.print_complete(2)
    else:
        missing_devices = []
        for device in devices:
            if not path.ismount(device.device_path):
                missing_devices.append(device)

        if not missing_devices:
            device_message.print_complete(True)
        else:
            device_message.print_complete(3)

            for device in devices:
                message = (
                    "{device_name} (Path: {device_path})\n"
                    "  {identifier_name}: {device_identifier}"
                ).format(
                    device_name=device.device_name,
                    device_path=device.device_path,
                    identifier_name=device.identifier_type,
                    device_identifier=device.identifier,
                )
                PrettyStatusPrinter(message).with_message_postfix_for_result(
                    True, ""
                ).with_message_postfix_for_result(False, "").print_complete(
                    device not in missing_devices
                )

            confirm = input("Proceed? (y/N) ")
            if confirm != "y":
                sys.exit(3)
            PrettyStatusPrinter("Continuing without all devices").with_specific_color(
                Color.YELLOW
            ).print_message()


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
    command = ""
    if arguments["action"] == "add":
        command = __dispatch_add_command(arguments)
    elif arguments["action"] == "move":
        command = __dispatch_move_command(arguments)
    elif arguments["action"] == "remove":
        command = __dispatch_remove_command(arguments)
    elif arguments["action"] == "update":
        command = __dispatch_update_command(arguments)
    elif arguments["action"] == "restore":
        command = __dispatch_restore_command(arguments)
    elif arguments["action"] == "verify":
        command = __dispatch_verify_command(arguments)
    elif arguments["action"] == "list-devices":
        command = "list-devices"
        library.list_devices()

    return command


def __dispatch_add_command(arguments: dict) -> str:
    """
    Dispatches a command to add something
    Returns command run
    """
    command = ""
    if arguments["file"]:
        command = "add-file"
        library.add_file(arguments["file"], arguments["device"])
    elif arguments["folder"]:
        command = "add-folder"
        library.add_directory(arguments["file"], arguments["device"])
    elif arguments["device"]:
        command = "add-device"
        print("add")
        library.add_device(arguments["device"])

    return command


def __dispatch_move_command(arguments: list) -> str:
    """
    Dispatches command to move file/folder or between devices
    Returns command that was run
    """
    command = ""
    if arguments["file"]:
        if arguments["move_path"]:
            command = "move-file"
            library.move_file_local(arguments["file"], arguments["move_path"])
        else:
            command = "move-file-to-device"
            library.move_file_device(arguments["file"], arguments["device"])
    elif arguments["folder"]:
        if arguments["move_path"]:
            command = "move-folder"
            library.move_directory_local(arguments["folder"], arguments["move_path"])
        else:
            command = "move-folder-to-device"
            library.move_directory_device(arguments["folder"], arguments["device"])

    return command


def __dispatch_remove_command(arguments: list) -> str:
    """
    Dispatches command to remove file/folder
    Returns command that was run
    """
    command = ""
    if arguments["file"]:
        command = "remove-file"
        library.remove_file(arguments["file"])
    elif arguments["folder"]:
        command = "remove-folder"
        library.remove_directory(arguments["folder"])

    return command


def __dispatch_update_command(arguments: list) -> str:
    """
    Dispatches command to update a file or folder
    Returns command that was run
    """
    command = ""
    if arguments["file"]:
        command = "update-file"
        library.update_file(arguments["file"])
    elif arguments["folder"]:
        command = "update-folder"
        library.update_folder(arguments["folder"])

    return command


def __dispatch_restore_command(arguments: list) -> str:
    """
    Dispatches command to restore a file, folder, or everything
    Returns command that was run
    """
    command = ""
    if arguments["file"]:
        command = "restore-file"
        library.restore_file(arguments["file"])
    elif arguments["folder"]:
        command = "restore-folder"
        library.restore_folder(arguments["folder"])
    elif arguments["all"]:
        command = "restore-all"
        library.restore_all()

    return command


def __dispatch_verify_command(arguments: list) -> str:
    """
    Dispatches command to verify a file, folder, or everything
    Returns command that was run
    """
    command = ""
    if arguments["file"]:
        command = "verify-file"
        library.verify_file(arguments["file"], False)
    elif arguments["folder"]:
        command = "verify-folder"
        library.verify_folder(arguments["folder"], False)
    elif arguments["all"]:
        command = "verify-all"
        library.verify_all(False)

    return command


def process(arguments: list = None) -> str:
    """
    Run the process

    Parameters
    ----------
    arguments : list
        Injectable arguments to execute

    Returns
    -------
    str
        The name of the library command to execute
    """
    if not arguments:
        arguments = []
    __prepare()
    args = __parse_arguments(arguments if arguments else sys.argv[1:])
    if not __validate_arguments(args):
        print_error("Argument combination not valid!")
        sys.exit(1)

    __check_devices(args)
    return __dispatch_command(args)
