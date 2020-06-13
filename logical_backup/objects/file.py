class File:
    """
    Represents a backup file
    """

    def __init__(self):
        """
        .
        """
        self.__file_name = None
        self.__file_path = None
        self.__permissions = None
        self.__user = None
        self.__group = None
        self.__checksum = None
        self.__device_name = None

    @property
    def file_name(self) -> str:
        """
        .
        """
        return self.__file_name

    @file_name.setter
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

    @file_path.setter
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

    @permissions.setter
    def permissions(self, permissions: str):
        """
        .
        """
        self.__permissions = permissions

    @property
    def user(self) -> str:
        """
        .
        """
        return self.__user

    @user.setter
    def user(self, user: str):
        """
        .
        """
        self.__user = user

    @property
    def group(self) -> str:
        """
        .
        """
        return self.__group

    @group.setter
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

    @checksum.setter
    def checksum(self, checksum: str):
        """
        .
        """
        self.__checksum = checksum

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
