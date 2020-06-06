"""
Some helper functions
"""
from os import getenv, environ
from subprocess import run, PIPE
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


def run_command(command: list) -> dict:
    """
    Executes a simple command

    Parameters
    ----------
    command : list
        The command to execute, grouped by parameters

    Returns
    -------
    dict
        With "exit_code", "stdout" and "stderr" properties
    """
    process = run(command, stdout=PIPE, stderr=PIPE, check=False)
    stdout, stderr = process.stdout, process.stderr
    return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr}


@fixture(autouse=True)
def auto_set_testing():
    """
    Will automatically set environment to testing
    """
    set_testing()
    yield "test"
    remove_testing()
