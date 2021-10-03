"""
Contains command base class
"""
from __future__ import annotations

from multiprocessing import synchronize
import socket
import time
from typing import List

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.commands.command_validator import CommandValidator
from logical_backup.utilities.message import Message
from logical_backup.utilities.device_manager import DeviceManager
from logical_backup.strings import Errors

# pylint: disable=too-few-public-methods
class Config:
    """
    Command configuration
    """


# pylint: disable=too-many-instance-attributes
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

    def _validate(self) -> Config:
        """
        Validate that this action has a correct configuration
        """
        raise NotImplementedError(Errors.COMMAND_VALIDATE_NOT_IMPLEMENTED)

    def _add_message(self, message: str) -> None:
        """
        Add a message
        """
        self.__messages.append(Message(message, time.time()))

    def _add_error(self, error: str) -> None:
        """
        Add an error
        """
        self.__errors.append(Message(error, time.time()))

    def _create_actions(self, config: Config) -> None:
        """
        Creates the component actions needing to be completed for this command
        """
        raise NotImplementedError(Errors.COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED)

    @property
    def has_actions(self) -> bool:
        """
        Check if there are actions created
        """
        return len(self._actions) > 0

    @property
    def actions(self) -> List[BaseAction]:
        """
        Return the actions needed to run to complete this command
        """
        config = self._validate()
        if self.errors:
            return []
        self._create_actions(config)
        return self._actions

    @property
    def errors(self) -> List[str]:
        """
        Get errors that occurred
        """
        return [error.message for error in self.__errors]

    @property
    def messages(self) -> List[str]:
        """
        Recorded messages
        """
        return [message.message for message in self.__messages]

    @property
    def logs(self) -> List[str]:
        """
        Show timestamped logs of events
        """
        all_logs = self.__messages + self.__errors
        all_logs.sort(key=lambda message: message.epoch_timestamp)
        return [str(log) for log in all_logs]
