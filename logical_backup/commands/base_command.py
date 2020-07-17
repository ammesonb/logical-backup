"""
Contains command base class
"""


class BaseCommand:
    """
    Represents the basics of a command
    This is a set of actions needed to run to interact with the file system
    """

    def __init__(self, arguments: dict) -> None:
        """
        Initialize

        Parameters
        ----------
        arguments : dictionary
            Command line arguments
        """
        self.arguments = arguments
        self.__errors = []
        self.__actions = []

        if self.__validate():
            self.__create_actions()

    def __validate(self) -> bool:
        """
        Validate that this action has a correct configuration
        """
        raise NotImplementedError("Validate must be overridden")

    def __create_actions(self) -> None:
        """
        Creates the component actions needing to be completed for this command
        """
        raise NotImplementedError("Create actions must be overridden")

    @property
    def actions(self) -> list:
        """
        Return the actions needed to run to complete this command
        """
        return self.__actions

    @property
    def errors(self) -> list:
        """
        Get errors that occurred
        """
        return self.__errors
