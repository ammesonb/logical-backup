"""
Contains action base class
"""
import time
from typing import Optional

from logical_backup.strings import Errors


class BaseAction:
    """
    A basic action
    This should be a concrete thing that needs to occur, such as:
      - checksum a file, then copy it somewhere, storing that information in the DB
      - verify the checksum of a backed-up file
    """

    # pylint: disable=unused-argument,bad-continuation
    # Derivative classes may need any number of arguments,
    # so let them take what they need
    def __init__(self, *args, **kwargs) -> None:
        """
        Must always be called, but will accept any number of arguments
        This just sets up a few expected properties
        """
        self.__success = None
        self.__errors = []
        self.__messages = []
        self.__completion_ns = -1

    def _run(self) -> None:
        """
        Runs the content of the specific action
        """
        raise NotImplementedError(str(Errors.ACTION_RUN_NOT_IMPLEMENTED))

    def process(self) -> None:
        """
        Times the running of this action
        """
        start = time.time_ns()
        self._run()
        self.__completion_ns = time.time_ns() - start

    @property
    def success(self) -> Optional[bool]:
        """
        Whether this action succeeded
        """
        return self.__success

    @property
    def errors(self) -> list:
        """
        Any errors encountered
        """
        return self.__errors

    @property
    def messages(self) -> list:
        """
        Any messages logged
        """
        return self.__messages

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

    def _fail(self, error: str) -> None:
        """
        Mark this action as failed, with a given error
        """
        self._add_error(error)
        self.__success = False

    def _succeed(self) -> None:
        """
        Mark this action as succeeded
        """
        self.__success = True

    @property
    def completion_nanoseconds(self) -> int:
        """
        Length of runtime of action
        Will return -1 if not completed yet
        """
        return self.__completion_ns

    @property
    def name(self) -> str:
        """
        .
        """
        raise NotImplementedError(str(Errors.ACTION_NAME_NOT_IMPLEMENTED))
