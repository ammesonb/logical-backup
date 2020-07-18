"""
Contains printed messages, errors, etc
"""

from enum import Enum

# pragma: no mutate
class Errors(Enum):
    """
    Printed error messages
    """

    COMMAND_VALIDATE_NOT_IMPLEMENTED = "Validate must be overridden"
    COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED = "Create actions must be overridden"

    ACTION_RUN_NOT_IMPLEMENTED = "Action must override run function"

    FILE_ALREADY_BACKED_UP = "File is already backed up!"
    FILE_NOT_BACKED_UP = "File path not backed up!"
    NEW_FILE_ALREADY_BACKED_UP = "File already backed up at new location!"
    CANNOT_FIND_BACKUP = "Cannot find back up of file!"

    FOLDER_ALREADY_ADDED = "Folder already added!"
    FOLDER_BACKED_UP_AT = lambda path: (
        "Folder already backed up at path '{0}'!".format(path)
    )
    FOLDER_NOT_BACKED_UP = "Folder not backed up!"
    FOLDER_NOT_BACKED_UP_AT = lambda path: (
        "Specified folder not backed up: '{0}'!".format(path)
    )
    FOLDER_NOT_CREATED = lambda path: ("Failed to create folder: {0}".format(path))
    CANNOT_OVERWRITE_EXISTING_FOLDER = "Cannot move folder over existing file!"

    NO_SAVED_DEVICES = "No devices saved!"
    SELECTED_DEVICE_FULL = "Exiting since unable to fit all files on selected device"
    DEVICE_HAS_INSUFFICIENT_SPACE = "Selected device will not fit all files!"
    NO_DEVICE_WITH_SPACE_AVAILABLE = "No device with space available!"
    INSUFFICIENT_SPACE_FOR_DIRECTORY = lambda bytes_needed: (
        "Sum of available devices' space is insufficient, "
        "need {0} additional space! Exiting".format(bytes_needed)
    )
    FILE_DEVICE_NOT_MOUNTED = "Device for backed-up file is not mounted!"

    FAILED_GET_CHECKSUM = "Failed to get checksum"
    CHECKSUM_MISMATCH = "File checksum does not match"
    CHECKSUM_MISMATCH_AFTER_COPY = "Checksum mismatch after copy!"
    NONE_FOUND = "None found!"

    FAILED_FILE_DEVICE_DB_UPDATE = "Failed to update device for file in database!"
    RESTORE_PATH_EXISTS = "Path to restore already exists!"
    FAIL_SET_PERMISSIONS_REMOVED = (
        "Failed to set file permissions/owner, but able to remove file"
    )
    FAIL_SET_PERMISSIONS_MANUAL = (
        "Failed to set file permissions/owner, manual removal required!"
    )

    FAILED_REMOVE_FILE_UPDATE = "Failed to remove file, so cannot update!"
    FAILED_ADD_FILE_UPDATE = "Failed to add file during update!"


# pragma: no mutate
class InputPrompts(Enum):
    """
    Input prompt messages
    """

    ALLOW_DEVICE_CHANGE = "Continue with any available device? (y/N, 'n' will exit) "

    RECURSIVE_REMOVE_DIRECTORY = (
        "Found one or more backed-up folders that no longer exist! "
        "Remove ALL missing directories recursively? "
        "Type REMOVE uppdercase to do so "
    )
    RECURSIVE_REMOVE_FILE = (
        "Found one or more backed-up files that no longer exist! "
        "Remove all missing files? Type YES uppercase to do so "
    )


# pragma: no mutate
class Info(Enum):
    """
    Informational messages
    """

    AUTO_SELECT_DEVICE = "Auto-selecting device"
    GET_FILE_SIZE = "Getting file size"
    FILE_SIZE_OUTPUT = lambda size: "Read. File size is " + size

    SAVING_FILE_TO_DB = "Saving file record to DB"

    COPYING_FILE_DEVICE = "Copying file to new device"
