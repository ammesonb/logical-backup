"""
Contains action base class
"""


class BaseAction:
    """
    A basic action
    This should be a concrete thing that needs to occur, such as:
      - checksum a file, then copy it somewhere, storing that information in the DB
      - verify the checksum of a backed-up file
    """

    # pylint: disable=unused-argument
    # Derivative classes may need any number of arguments,
    # so let them take what they need
    def __init__(self, *args, **kwargs) -> None:
        """
        Must always be called, but will accept any number of arguments
        This just sets up a few expected properties
        """
        self.__success = None
        self.__errors = []

    def run(self):
        """
        Runs the content of the specific action
        """
        raise NotImplementedError("Strategy must override run function")

    @property
    def success(self) -> bool:
        """
        Whether this action succeeded
        """
        return self.__success

    @property
    def errors(self) -> list:
        """
        Any errors encountered
        """
        return self.errors
