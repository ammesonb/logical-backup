"""
Testing helper functions
"""
import functools
from os import getenv, environ

from pytest import fixture

TEST_VARIABLE = "IS_TEST"


def compare_lists(list1: list, list2: list) -> bool:
    """
    Compares two lists for an exact match, order-agnostic
    """
    return len(list1) == len(list2) and all([item in list2 for item in list1])


def is_test() -> bool:
    """
    Returns whether code is run for a test
    Set via environment variables

    Returns
    -------
    bool
        True if being run as a test
    """
    return getenv(TEST_VARIABLE) == "1"


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
    yield
    remove_testing()


def counter_wrapper(func):
    """
    Adds a "counter" variable to the function, incrementing each time it is called
    """

    @functools.wraps(func)  # pragma: no mutate
    def execute(*args, **kwargs):
        """
        Adds a "counter" variable to the function, incrementing each time it is called
        """
        execute.counter += 1
        return func(*args, **kwargs)

    execute.counter = 0

    return execute
