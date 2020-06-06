"""
Some helper functions
"""
from os import getenv, environ
from pytest import fixture

TEST_VARIABLE = "IS_TEST"


def is_test() -> bool:
    """
    Returns whether code is run for a test
    Set via environment variables

    Returns
    -------
    bool
        True if being run as a test
    """
    return bool(getenv(TEST_VARIABLE))


def set_testing() -> None:
    """
    Set testing environment variable
    """
    environ[TEST_VARIABLE] = "1"


def remove_testing() -> None:
    """
    Remove the testing environment variable
    """
    del environ[TEST_VARIABLE]


@fixture(autouse=True)
def auto_set_testing():
    """
    Will automatically set environment to testing
    """
    set_testing()
    yield "test"
    remove_testing()
