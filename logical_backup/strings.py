"""
Contains printed messages, errors, etc
"""

from enum import Enum

# pragma: no mutate
class Errors(Enum):
    """
    Printed error messages
    """

    ERROR_COMMAND_VALIDATE_NOT_IMPLEMENTED = "Validate must be overridden"
    ERROR_COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED = "Create actions must be overridden"

    ERROR_ACTION_RUN_NOT_IMPLEMENTED = "Strategy must override run function"
