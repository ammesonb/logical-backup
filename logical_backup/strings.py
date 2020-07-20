"""
Contains printed messages, errors, etc
"""

from enum import Enum

from logical_backup.utilities.printable_enum import PrintableEnum


class Errors(PrintableEnum):
    """
    Printed error messages
    """

    COMMAND_VALIDATE_NOT_IMPLEMENTED = (
        "Validate must be overridden"  # pragma: no mutate
    )
    COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED = (
        "Create actions must be overridden"  # pragma: no mutate
    )

    ACTION_RUN_NOT_IMPLEMENTED = (
        "Action must override run function"  # pragma: no mutate
    )

    FILE_ALREADY_BACKED_UP = "File is already backed up!"  # pragma: no mutate
    FILE_NOT_BACKED_UP = "File path not backed up!"  # pragma: no mutate
    NEW_FILE_ALREADY_BACKED_UP = (
        "File already backed up at new location!"  # pragma: no mutate
    )
    CANNOT_FIND_BACKUP = "Cannot find back up of file!"  # pragma: no mutate
    FILE_DEVICE_INVALID = "Unable to find device for file"  # pragma: no mutate

    FOLDER_ALREADY_ADDED = "Folder already added!"  # pragma: no mutate
    FOLDER_BACKED_UP_AT = lambda path: (  # pragma: no mutate
        "Folder already backed up at path '{0}'!".format(path)  # pragma: no mutate
    )
    FOLDER_NOT_BACKED_UP = "Folder not backed up!"  # pragma: no mutate
    FOLDER_NOT_BACKED_UP_AT = lambda path: (  # pragma: no mutate
        "Specified folder not backed up: '{0}'!".format(path)  # pragma: no mutate
    )
    FOLDER_NOT_CREATED = lambda path: (
        "Failed to create folder: {0}".format(path)
    )  # pragma: no mutate
    CANNOT_OVERWRITE_EXISTING_FOLDER = (
        "Cannot move folder over existing file!"  # pragma: no mutate
    )
    FAILED_FOLDER_REMOVE = lambda folder: (
        "Failed to remove folder '{0}' "  # pragma: no mutate
        "from database!".format(folder)  # pragma: no mutate
    )
    FAILED_FOLDER_ADD = lambda folder: (
        "Failed to add folder '{0}' "  # pragma: no mutate
        "back to the database!".format(folder)  # pragma: no mutate
    )

    DEVICE_MUST_BE_ADDED = "A device must be added before any other actions can occur!"  # pragma: no mutate
    NO_DEVICES_FOUND = "None!"  # pragma: no mutate
    SOME_DEVICES_FOUND = "Found some devices:"
    UNRECOGNIZED_DEVICE_IDENTIFIER = (
        "Failed. Unrecognized device identifier!"  # pragma: no mutate
    )
    DEVICE_NAME_TAKEN = "Failed. Name already taken!"  # pragma: no mutate
    DEVICE_MOUNT_POINT_USED = (
        "Failed. Device already registered at mount point!"  # pragma: no mutate
    )
    DEVICE_SERIAL_USED = (
        "Failed. Serial already registered for another device!"  # pragma: no mutate
    )
    DEVICE_UNKNOWN_ERROR = "Failed. Unknown error occurred!"  # pragma: no mutate
    DEVICE_SUPER_UNKNOWN_ERROR = (
        "Failed. Super-unknown error occurred!"  # pragma: no mutate
    )

    NO_SAVED_DEVICES = "No devices saved!"  # pragma: no mutate
    SELECTED_DEVICE_FULL = (
        "Exiting since unable to fit all files on selected device"  # pragma: no mutate
    )
    DEVICE_HAS_INSUFFICIENT_SPACE = (
        "Selected device will not fit all files!"  # pragma: no mutate
    )
    NO_DEVICE_WITH_SPACE_AVAILABLE = (
        "No device with space available!"  # pragma: no mutate
    )
    INSUFFICIENT_SPACE_FOR_DIRECTORY = lambda bytes_needed: (  # pragma: no mutate
        "Sum of available devices' space is insufficient, "  # pragma: no mutate
        "need {0} additional space! Exiting".format(bytes_needed)  # pragma: no mutate
    )
    FILE_DEVICE_NOT_MOUNTED = (
        "Device for backed-up file is not mounted!"  # pragma: no mutate
    )

    FAILED_GET_CHECKSUM = "Failed to get checksum"  # pragma: no mutate
    CHECKSUM_MISMATCH = "File checksum does not match"  # pragma: no mutate
    CHECKSUM_MISMATCH_AFTER_COPY = "Checksum mismatch after copy!"  # pragma: no mutate
    NONE_FOUND = "None found!"  # pragma: no mutate

    FAILED_FILE_DEVICE_DB_UPDATE = (
        "Failed to update device for file in database!"  # pragma: no mutate
    )
    RESTORE_PATH_EXISTS = "Path to restore already exists!"  # pragma: no mutate
    FAIL_SET_PERMISSIONS_REMOVED = (
        "Failed to set file permissions/owner, "  # pragma: no mutate
        "but able to remove file"  # pragma: no mutate  # pragma: no mutate
    )
    FAIL_SET_PERMISSIONS_MANUAL = (
        "Failed to set file permissions/owner, "  # pragma: no mutate
        "manual removal required!"  # pragma: no mutate  # pragma: no mutate
    )

    FAILED_REMOVE_FILE_UPDATE = (
        "Failed to remove file, so cannot update!"  # pragma: no mutate
    )
    FAILED_ADD_FILE_UPDATE = "Failed to add file during update!"  # pragma: no mutate

    FAILED_REMOVE_FILE = "Failed to remove file from the database!"  # pragma: no mutate


class InputPrompts(PrintableEnum):
    """
    Input prompt messages
    """

    ALLOW_DEVICE_CHANGE = (
        "Continue with any available device? (y/N, 'n' will exit) "  # pragma: no mutate
    )

    RECURSIVE_REMOVE_DIRECTORY = (  # pragma: no mutate
        "Found one or more backed-up folders "  # pragma: no mutate
        "that no longer exist! "  # pragma: no mutate
        "Remove ALL missing directories recursively? "  # pragma: no mutate
        "Type REMOVE uppdercase to do so "  # pragma: no mutate
    )
    RECURSIVE_REMOVE_FILE = (  # pragma: no mutate
        "Found one or more backed-up files that no longer exist! "  # pragma: no mutate
        "Remove all missing files? Type YES uppercase to do so "  # pragma: no mutate
    )

    DEVICE_NAME = "Device name: "  # pragma: no mutate
    DEVICE_IDENTIFIER = (
        "Unable to find systemic identifier. "  # pragma: no mutate
        "Please provide a unique identifier for the device: "  # pragma: no mutate
    )


class Info(PrintableEnum):
    """
    Informational messages
    """

    CHECKING_DEVICES = "Checking for devices"  # pragma: no mutate
    ALL_DEVICES_FOUND = "All devices found"  # pragma: no mutate
    NO_DEVICES_FOUND = "None found, but command can continue"
    CONTINUING_WITHOUT_DEVICE = "Continuing without all devices"  # pragma: no mutate

    AUTO_SELECT_DEVICE = "Auto-selecting device"  # pragma: no mutate
    GET_FILE_SIZE = "Getting file size"  # pragma: no mutate
    FILE_SIZE_OUTPUT = lambda size: "Read. File size is " + size  # pragma: no mutate

    SAVING_DEVICE = "Saving device"  # pragma: no mutate
    SAVING_FILE_TO_DB = "Saving file record to DB"  # pragma: no mutate

    COPYING_FILE_DEVICE = "Copying file to new device"  # pragma: no mutate

    VALIDATE_FILE_REMOVAL = "Validating file removal"  # pragma: no mutate
    FILE_REMOVED = "File removed"  # pragma: no mutate

    PROGRAM_DESCRIPTION = (
        "Back up and restore files across multiple hard drives\n\n"  # pragma: no mutate
        "Actions:\n"  # pragma: no mutate
        "         add: add a file or folder "  # pragma: no mutate
        "to the backup selection\n"  # pragma: no mutate
        "      remove: remove a file or folder "  # pragma: no mutate
        "from the backup selection\n"  # pragma: no mutate
        "        move: move a file or folder "  # pragma: no mutate
        "in the backup selection, "  # pragma: no mutate
        "OR files/folders between devices\n"  # pragma: no mutate
        "     restore: restore a file/folder/all files "  # pragma: no mutate
        "to their original location\n"  # pragma: no mutate
        "      verify: check a backed-up file/folder/all "  # pragma: no mutate
        "files for integrity "  # pragma: no mutate
        "(this will NOT check the local filesystem copy, "  # pragma: no mutate
        "as that is assumed to be correct)\n"  # pragma: no mutate
        "list-devices: list all the registered backup devices\n"  # pragma: no mutate
        "Example uses:\n"  # pragma: no mutate
        "  # Will add a new device\n"  # pragma: no mutate
        "  add --device /mnt/dev1\n"  # pragma: no mutate
        "  # Will add this file to the backup set\n"  # pragma: no mutate
        "  add --file /home/user/foo.txt\n"  # pragma: no mutate
        "  # Will remove the /etc folder recursively from backup\n"  # pragma: no mutate
        "  remove --folder /etc\n"  # pragma: no mutate
        "  # Will check all backed up files for integrity\n"  # pragma: no mutate
        "  verify --all\n"  # pragma: no mutate
        "  # Will restore the documents folder from backup\n"  # pragma: no mutate
        "  restore /home/user/documents\n"  # pragma: no mutate
        "  # Will rehome the file, "  # pragma: no mutate
        "updating the backup archive with the new location\n"  # pragma: no mutate
        "  move --file /backups/large.bak "  # pragma: no mutate
        "--move-path /backups/archive/\n"  # pragma: no mutate
        "  # Will move the backed up folder from "  # pragma: no mutate
        "its current drive to another, "  # pragma: no mutate
        "if one particular drive is too full to "  # pragma: no mutate
        "take a needed operation\n"  # pragma: no mutate
        "  move --file /backups --device dev2\n"  # pragma: no mutate
    )

    TARGET_FILE_HELP = "The file to take action on"  # pragma: no mutate
    TARGET_FOLDER_HELP = "The folder to take action on"  # pragma: no mutate
    TARGET_DEVICE_HELP = "Mount path for a device"  # pragma: no mutate
    TARGET_FROM_DEVICE_HELP = (
        "Use to restrict operation to a specific device"  # pragma: no mutate
    )
    TARGET_ALL_HELP = "Perform operation on all files"  # pragma: no mutate
    TARGET_MOVE_PATH_HELP = "Target for move operaetion"  # pragma: no mutate


class Commands(PrintableEnum):
    """
    Possible commands
    """

    ADD = "add"  # pragma: no mutate
    MOVE = "move"  # pragma: no mutate
    REMOVE = "remove"  # pragma: no mutate
    UPDATE = "update"  # pragma: no mutate
    VERIFY = "verify"  # pragma: no mutate
    RESTORE = "restore"  # pragma: no mutate
    LIST_DEVICES = "list-devices"  # pragma: no mutate
    SEARCH = "search"  # pragma: no mutate


class Targets(PrintableEnum):
    """
    Possible target of a command
    """

    ALL = "--all"  # pragma: no mutate
    FILE = "--file"  # pragma: no mutate
    FOLDER = "--folder"  # pragma: no mutate
    DEVICE = "--device"  # pragma: no mutate
    FROM_DEVICE = "--from-device"  # pragma: no mutate
    MOVE_PATH = "--move-path"  # pragma: no mutate
