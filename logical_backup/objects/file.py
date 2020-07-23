"""
A backed-up file
"""

from logical_backup.objects.device import Device

# pylint: disable=too-many-instance-attributes
class File:
    """
    Represents a backup file
    """

    def __init__(self):
        """
        .
        """
        self.__file_name = None  # pragma: no mutate
        self.__file_path = None  # pragma: no mutate
        self.__permissions = None  # pragma: no mutate
        self.__owner = None  # pragma: no mutate
        self.__group = None  # pragma: no mutate
        self.__checksum = None  # pragma: no mutate
        self.__device_name = None  # pragma: no mutate
        self.__device = None  # pragma: no mutate

    @property
    def file_name(self) -> str:
        """
        .
        """
        return self.__file_name

    @file_name.setter  # pragma: no mutate
    def file_name(self, file_name: str):
        """
        .
        """
        self.__file_name = file_name

    @property
    def file_path(self) -> str:
        """
        .
        """
        return self.__file_path

    @file_path.setter  # pragma: no mutate
    def file_path(self, file_path: str):
        """
        .
        """
        self.__file_path = file_path

    @property
    def permissions(self) -> str:
        """
        .
        """
        return self.__permissions

    @permissions.setter  # pragma: no mutate
    def permissions(self, permissions: str):
        """
        .
        """
        self.__permissions = permissions

    @property
    def owner(self) -> str:
        """
        .
        """
        return self.__owner

    @owner.setter  # pragma: no mutate
    def owner(self, owner: str):
        """
        .
        """
        self.__owner = owner

    @property
    def group(self) -> str:
        """
        .
        """
        return self.__group

    @group.setter  # pragma: no mutate
    def group(self, group: str):
        """
        .
        """
        self.__group = group

    @property
    def checksum(self) -> str:
        """
        .
        """
        return self.__checksum

    @checksum.setter  # pragma: no mutate
    def checksum(self, checksum: str):
        """
        .
        """
        self.__checksum = checksum

    @property
    def device_name(self) -> str:
        """
        Returns file's device name
        """
        return self.__device_name

    @device_name.setter  # pragma: no mutate
    def device_name(self, device_name: str):
        """
        Sets file's device name
        """
        self.__device_name = device_name

    @property
    def device(self) -> Device:
        """
        .
        """
        return self.__device

    @device.setter  # pragma: no mutate
    def device(self, device: Device) -> None:
        """
        .
        """
        self.__device = device

    def set_properties(self, name: str, path: str, checksum: str) -> None:
        """
        Set properties about the file

        Parameters
        ----------
        name : str
            Name of the file
        path : str
            Path to the file
        checksum : str
            .
        """
        self.file_name = name
        self.file_path = path
        self.checksum = checksum

    def set_security(self, permissions: str, owner: str, group: str) -> None:
        """
        Set security details about the file

        Parameters
        ----------
        permissions : str
            Permission string, e.g. 644/755
        owner : str
            System username that owns the file
        group : str
            System group that owns the file
        """
        self.permissions = permissions
        self.owner = owner
        self.group = group

    def __eq__(self, other: "File") -> bool:
        """
        Equality check
        """
        properties = [
            "file_name",
            "file_path",
            "device_name",
            "owner",
            "group",
            "permissions",
            "checksum",
        ]

        return all([getattr(self, prop) == getattr(other, prop) for prop in properties])
