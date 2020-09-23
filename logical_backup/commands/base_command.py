"""
Contains command base class
"""
from __future__ import annotations

import multiprocessing
from multiprocessing import synchronize
import socket

from logical_backup.commands.command_validator import CommandValidator
from logical_backup.utilities.device_manager import DeviceManager
from logical_backup.strings import Errors


class BaseCommand:
    """
    Represents the basics of a command
    This is a set of actions needed to run to interact with the file system
    """

    # pylint: disable=bad-continuation
    def __init__(
        self,
        arguments: dict,
        device_manager: DeviceManager,
        device_manager_socket: socket.socket,
        device_manager_lock: synchronize.Lock,
    ) -> None:
        """
        Initialize

        Parameters
        ----------
        arguments : dictionary
            Command line arguments
        """
        self.arguments = arguments
        self._device_manager = device_manager
        self._device_manager_socket = device_manager_socket
        self._device_manager_lock = device_manager_lock
        self._validator = CommandValidator(arguments)
        self.__messages = []
        self.__errors = []
        self._actions = []

    def _validate(self):
        """
        Validate that this action has a correct configuration
        """
        raise NotImplementedError(Errors.COMMAND_VALIDATE_NOT_IMPLEMENTED)

    def _add_message(self, message: str) -> None:
        """
        Add a message
        """
        self.__messages.append(message)

    def _add_error(self, error: str) -> None:
        """
        Add an error
        """
        self.__errors.append(error)

    def _create_actions(self) -> None:
        """
        Creates the component actions needing to be completed for this command
        """
        raise NotImplementedError(Errors.COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED)

    @property
    def has_actions(self) -> bool:
        """
        Check if there are actions created
        """
        return bool(self._actions)

    @property
    def actions(self) -> list:
        """
        Return the actions needed to run to complete this command
        """
        self._validate()
        if self.errors:
            return []
        self._create_actions()
        return self._actions

    @property
    def errors(self) -> list:
        """
        Get errors that occurred
        """
        return self.__errors

    @property
    def messages(self) -> list:
        """
        Recorded messages
        """
        return self.__messages
