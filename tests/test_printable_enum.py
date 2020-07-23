"""
Tests printing enum values
"""
from logical_backup.utilities.printable_enum import PrintableEnum

VALUE = "Hello world"


class FakeEnum(PrintableEnum):
    """
    A test enum class
    """

    TEST_VALUE = VALUE


def test_basic_stringify():
    """
    String concatenation, equivalence
    """
    padding = "Ipsum lorem"

    assert str(FakeEnum.TEST_VALUE) == VALUE, "String comparison works"
    assert (FakeEnum.TEST_VALUE + padding) == (VALUE + padding), "String addition works"
    assert (padding + FakeEnum.TEST_VALUE) == (
        padding + VALUE
    ), "Reverse string addition works"


def test_iteration_containment():
    """
    Conversion for iteration, containing other strings
    """
    characters = []
    for char in FakeEnum.TEST_VALUE:
        characters.append(char)

    assert characters == list(VALUE), "Iteration works as expected"

    assert "Hello" in FakeEnum.TEST_VALUE, "Basic 'in' works"
    assert "foobar" not in FakeEnum.TEST_VALUE, "Basic 'in' fails"
    assert str(FakeEnum.TEST_VALUE) in "Hello world!", "Basic reverse 'in' works"
    assert str(FakeEnum.TEST_VALUE) not in "Hello", "Basic reverse 'in' fails"
