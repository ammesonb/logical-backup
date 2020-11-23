"""
A logged message/error
"""
from datetime import datetime


class Message:
    """
    A logged message/error
    """

    def __init__(self, message: str, epoch_timestamp: int):
        self.__message = message
        self.__epoch_timestamp = epoch_timestamp

    def __str__(self):
        return (
            datetime.fromtimestamp(self.epoch_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            + " "
            + self.message
        )

    @property
    def message(self) -> str:
        """
        Returns the content of the message
        """
        return self.__message

    @property
    def epoch_timestamp(self) -> int:
        """
        Returns the epoch timestamp of this message
        """
        return self.__epoch_timestamp
