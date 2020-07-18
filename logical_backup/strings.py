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
    FAILED_GET_CHECKSUM = "Failed to get checksum"
    FOLDER_ALREADY_ADDED = "Folder already added!"
    INSUFFICIENT_SPACE_FOR_DIRECTORY = lambda bytes_needed: (
        "Sum of available devices' space is insufficient, "
        "need {0} additional space! Exiting".format(bytes_needed)
    )
    SELECTED_DEVICE_FULL = "Exiting since unable to fit all files on selected device"
    DEVICE_HAS_INSUFFICIENT_SPACE = "Selected device will not fit all files!"
    CANNOT_OVERWRITE_EXISTING_FOLDER = "Cannot move folder over existing file!"
    FOLDER_BACKED_UP_AT = lambda path: (
        "Folder already backed up at path '{0}'!".format(path)
    )
    FOLDER_NOT_BACKED_UP_AT = lambda path: (
        "Specified folder not backed up: '{0}'!".format(path)
    )
    NONE_FOUND = "None found!"
    NO_DEVICE_WITH_SPACE_AVAILABLE = "No device with space available!"
    CHECKSUM_MISMATCH = "Checksum mismatch after copy!"


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
