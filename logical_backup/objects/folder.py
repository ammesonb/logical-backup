"""
A backed-up folder
"""

# pylint: disable=too-many-instance-attributes
class Folder:
    """
    A backup folder
    """

    def __init__(self):
        """
        .
        """
        self.__folder_path = None  # pragma: no mutate
        self.__folder_permissions = None  # pragma: no mutate
        self.__folder_owner = None  # pragma: no mutate
        self.__folder_group = None  # pragma: no mutate

    @property
    def folder_path(self) -> str:
        """
        .
        """
        return self.__folder_path

    @folder_path.setter  # pragma: no mutate
    def folder_path(self, folder_path: str):
        """
        .
        """
        self.__folder_path = folder_path

    @property
    def folder_permissions(self) -> str:
        """
        .
        """
        return self.__folder_permissions

    @folder_permissions.setter  # pragma: no mutate
    def folder_permissions(self, folder_permissions: str):
        """
        .
        """
        self.__folder_permissions = folder_permissions

    @property
    def folder_owner(self) -> str:
        """
        .
        """
        return self.__folder_owner

    @folder_owner.setter  # pragma: no mutate
    def folder_owner(self, folder_owner: str):
        """
        .
        """
        self.__folder_owner = folder_owner

    @property
    def folder_group(self) -> str:
        """
        .
        """
        return self.__folder_group

    @folder_group.setter  # pragma: no mutate
    def folder_group(self, folder_group: str):
        """
        .
        """
        self.__folder_group = folder_group

    def set(self, path: str, permissions: str, owner: str, group: str):
        """
        .
        """
        self.folder_path = path
        self.folder_permissions = permissions
        self.folder_owner = owner
        self.folder_group = group

    def __eq__(self, other: "Folder") -> bool:
        """
        Compare two folders

        Parameters
        ----------
        other : Folder
            To compare against

        Returns
        -------
        bool
            True if equal, otherwise False
        """
        properties = [
            "folder_path",
            "folder_permissions",
            "folder_owner",
            "folder_group",
        ]
        return all([getattr(self, prop) == getattr(other, prop) for prop in properties])
