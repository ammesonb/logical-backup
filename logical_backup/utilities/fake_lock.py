"""
A fake atomic lock, counting number of calls
"""
from logical_backup.utilities.testing import counter_wrapper


class FakeLock:
    """
    Fake synchronization lock
    """

    def __init__(self):
        """
        .
        """
        self.__acquired = 0
        self.__released = 0

    def __enter__(self):
        """
        When this used in a context manager
        """
        self.acquire()

    def __exit__(self, *args, **kwargs):
        """
        When a context manager is exited
        """
        self.release()

    def acquire(self, block: bool = True):
        """
        Acquire lock
        """
        self.__acquired += 1
        return True

    @counter_wrapper
    def release(self):
        """
        Release lock
        """
        self.__released += 1

    @property
    def acquired(self):
        """
        Number times acquired
        """
        return self.__acquired

    @property
    def released(self):
        """
        Number times released
        """
        return self.__released
