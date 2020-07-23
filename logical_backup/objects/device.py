"""
A device for backing up files
"""

DEVICE_SERIAL = "Device Serial"  # pragma: no mutate
SYSTEM_UUID = "System UUID"  # pragma: no mutate
USER_SPECIFIED = "User Specified"  # pragma: no mutate


# pylint: disable=too-many-instance-attributes
class Device:
    """
    Represents a backup device
    """

    def __init__(self):
        """
        .
        """
        self.__device_name = None  # pragma: no mutate
        self.__device_path = None  # pragma: no mutate
        self.__identifier_type_id = None  # pragma: no mutate
        self.__identifier_type = None  # pragma: no mutate
        self.__identifier = None  # pragma: no mutate

    @property
    def device_name(self) -> str:
        """
        Returns name of device
        """
        return self.__device_name

    @device_name.setter  # pragma: no mutate
    def device_name(self, device_name: str):
        """
        Sets name of device
        """
        self.__device_name = device_name

    @property
    def device_path(self) -> str:
        """
        .
        """
        return self.__device_path

    @device_path.setter  # pragma: no mutate
    def device_path(self, device_path: str):
        """
        .
        """
        self.__device_path = device_path

    @property
    def identifier_type_id(self) -> int:
        """
        .
        """
        return self.__identifier_type_id

    @identifier_type_id.setter  # pragma: no mutate
    def identifier_type_id(self, identifier_type_id: int):
        """
        .
        """
        self.__identifier_type_id = identifier_type_id

    @property
    def identifier_type(self) -> str:
        """
        .
        """
        return self.__identifier_type

    @identifier_type.setter  # pragma: no mutate
    def identifier_type(self, identifier_type: str):
        """
        .
        """
        self.__identifier_type = identifier_type

    @property
    def identifier(self) -> str:
        """
        .
        """
        return self.__identifier

    @identifier.setter  # pragma: no mutate
    def identifier(self, identifier: str):
        """
        .
        """
        self.__identifier = identifier

    def __eq__(self, other) -> bool:
        """
        Compare this to something else

        Parameters
        ----------
        other : dict|Device
            What to compare against
        """
        equal = False
        if isinstance(other, dict):
            # Use "not any" to exit early on a mismatch
            equal = not any(
                [getattr(self, key) != value for key, value in other.items()]
            )
        elif isinstance(other, Device):
            equal = (
                self.device_name == other.device_name
                and self.device_path == other.device_path
                and self.identifier_type == other.identifier_type
                and self.identifier_type_id == other.identifier_type_id
                and self.identifier == other.identifier
            )

        return equal

    # pylint: disable=bad-continuation,too-many-arguments
    def set(
        self,
        name: str,
        path: str,
        identifier_name: str,
        identifier: str,
        identifier_id: int = None,
    ) -> int:
        """
        Set common properties

        Parameters
        ----------
        name : string
            The name of the device
        path: string
            The mount path of the device
        identifier_name : string
            Friendly description of the identifier - must be in picklist
        identifier : string
            The identifier for the device
        identifier_id : int
            The identifier ID for the device
        """
        self.device_name = name
        self.device_path = path
        self.identifier_type = identifier_name
        self.identifier = identifier
        if identifier_id is not None:
            self.identifier_type_id = identifier_id
