"""
Tests printing enum values
"""
from logical_backup.utilities.printable_enum import PrintableEnum


def test_basic_stringify():
    """
    String concatenation, equivalence
    """
    test_string = "Hello world"
    padding = "Ipsum lorem"
    PrintableEnum.TEST_VALUE = test_string

    assert PrintableEnum.TEST_VALUE == test_string, "String comparison works"
    assert (PrintableEnum.TEST_VALUE + padding) == (
        test_string + padding
    ), "String addition works"
    assert (padding + PrintableEnum.TEST_VALUE) == (
        padding + test_string
    ), "Reverse string addition works"


def test_iteration_containment():
    """
    Conversion for iteration, containing other strings
    """
    test_value = "foo"
    PrintableEnum.TEST_VALUE = test_value
    characters = []
    for char in PrintableEnum.TEST_VALUE:
        characters.append(char)

    assert characters == ["f", "o", "o"], "Iteration works as expected"

    assert "foo" in PrintableEnum.TEST_VALUE, "Basic 'in' works"
    assert "foobar" not in PrintableEnum.TEST_VALUE, "Basic 'in' fails"
    assert PrintableEnum.TEST_VALUE in "foobar", "Basic reverse 'in' works"
    assert PrintableEnum.TEST_VALUE not in "fo", "Basic reverse 'in' fails"
