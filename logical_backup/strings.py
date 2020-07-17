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

    FOLDER_ALREADY_ADDED = "Folder already added!"
    INSUFFICIENT_SPACE_FOR_DIRECTORY = lambda bytes_needed: (
        "Sum of available devices' space is insufficient, "
        "need {0} additional space! Exiting".format(bytes_needed)
    )
    SELECTED_DEVICE_FULL = "Exiting since unable to fit all files on selected device"
    DEVICE_HAS_INSUFFICIENT_SPACE = "Selected device will not fit all files!"


# pragma: no mutate
class InputPrompts(Enum):
    """
    Input prompt messages
    """

    ALLOW_DEVICE_CHANGE = "Continue with any available device? (y/N, 'n' will exit) "
