"""
Contains a printable enum class
"""

from enum import Enum


class PrintableEnum(Enum):
    """
    A printable enum
    """

    def __str__(self, arg: str = None):
        """
        String
        """
        return self.value if isinstance(self.value, str) else self(arg)

    def __add__(self, other):
        """
        String postfixed to this one
        """
        return str(self) + other

    def __radd__(self, other):
        """
        String prefixed to this one
        """
        return other + str(self)

    def __iter__(self):
        """
        Iterable
        """
        for char in str(self):
            yield char

    def __contains__(self, other):
        """
        OTher thing is in this
        """
        return other in str(self)
