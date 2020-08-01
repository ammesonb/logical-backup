"""
A helper for validating commands
"""
import os
from os import path as os_path

from logical_backup.strings import Arguments


class CommandValidator:
    """
    Helps validate command arguments
    """

    def __init__(self, arguments: dict):
        self.__arguments = arguments

    def get_file(self) -> str:
        """
        Get file from arguments
        """
        return self.__arguments.get(str(Arguments.FILE), None)

    def get_folder(self) -> str:
        """
        Get folder from arguments
        """
        return self.__arguments.get(str(Arguments.FOLDER), None)

    def get_all(self) -> str:
        """
        Get "all" from arguments
        """
        return self.__arguments.get(str(Arguments.ALL), None)

    def get_device(self) -> str:
        """
        Get device from arguments
        """
        return self.__arguments.get(str(Arguments.DEVICE), None)

    def has_file(self) -> bool:
        """
        Whether file is set in the arguments
        """
        return bool(self.get_file())

    def file_exists(self) -> bool:
        """
        Whether file is set, and exists on the FS
        """
        return self.has_file() and os_path.isfile(self.get_file())

    def has_folder(self) -> bool:
        """
        Whether folder is set in the arguments
        """
        return bool(self.get_folder())

    def folder_exists(self) -> bool:
        """
        Whether folder is set, and exists on the FS
        """
        return self.has_folder() and os_path.isdir(self.get_folder())

    def is_all(self) -> bool:
        """
        Whether "all" is set in the arguments
        """
        return bool(self.get_all())

    def has_device(self) -> bool:
        """
        Whether device is set in the arguments
        """
        return bool(self.get_device())

    def device_exists(self) -> bool:
        """
        Whether device is set, and is mounted on the FS
        """
        return self.has_device() and os_path.ismount(self.get_device())

    def device_writeable(self) -> bool:
        """
        Whether we can write to the device
        """
        return self.device_exists() and os.access(self.get_device(), os.W_OK)
