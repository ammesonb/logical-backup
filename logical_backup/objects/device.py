class Device:
    """
    Represents a backup device
    """

    def __init__(self):
        """
        .
        """
        self.__device_name = None
        self.__device_path = None
        self.__identifier_type_id = None
        self.__identifier_type = None
        self.__identifier = None

    @property
    def device_name(self) -> str:
        """
        .
        """
        return self.__device_name

    @device_name.setter
    def device_name(self, device_name: str):
        """
        .
        """
        self.__device_name = device_name

    @property
    def device_path(self) -> str:
        """
        .
        """
        return self.__device_path

    @device_path.setter
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

    @identifier_type_id.setter
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

    @identifier_type.setter
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

    @identifier.setter
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
        if type(other) is dict:
            print("dict")
            for key, value in other.items():
                if getattr(self, key) != value:
                    return False
        elif type(other) is Device:
            return (
                self.device_name == other.device_name
                and self.device_path == other.device_path
                and self.identifier_type == other.identifier_type
                and self.identifier_type_id == other.identifier_type_id
                and self.identifier == other.identifier
            )

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
        if identifier_id:
            self.identifier_type_id = identifier_id
