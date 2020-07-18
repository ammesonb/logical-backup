"""
Contains printed messages, errors, etc
"""

from enum import Enum


class Errors(Enum):
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


# pragma: no mutate
class InputPrompts(Enum):
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


# pragma: no mutate
class Info(Enum):
    """
    Informational messages
    """

    AUTO_SELECT_DEVICE = "Auto-selecting device"  # pragma: no mutate
    GET_FILE_SIZE = "Getting file size"  # pragma: no mutate
    FILE_SIZE_OUTPUT = lambda size: "Read. File size is " + size  # pragma: no mutate

    SAVING_FILE_TO_DB = "Saving file record to DB"  # pragma: no mutate

    COPYING_FILE_DEVICE = "Copying file to new device"  # pragma: no mutate

    VALIDATE_FILE_REMOVAL = "Validating file removal"  # pragma: no mutate
    FILE_REMOVED = "File removed"  # pragma: no mutate
