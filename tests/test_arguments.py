"""
Test main script entry point
"""

from os import mkdir, remove, rmdir
from os.path import isdir, isfile
from pathlib import Path

from pytest import fixture

from logical_backup.main import __validate_arguments

MOCK_FILE = "mock.test"


def make_mock_file():
    """
    Makes the mock file
    """
    Path(MOCK_FILE).touch()


def make_mock_folder():
    """
    Makes the mock folder
    """
    mkdir(MOCK_FILE)


def remove_mock():
    """
    Remove mock file/folder
    """
    if isdir(MOCK_FILE):
        rmdir(MOCK_FILE)
    elif isfile(MOCK_FILE):
        remove(MOCK_FILE)


@fixture(autouse=True)
def auto_clear_mock():
    """
    Auto-clear the mock before each test
    """
    remove_mock()


def check_generic_file_folder(action: str):
    """
    Most (all?) commands expect _at most_ one of file/folder
    Abstract this to simplify the code

    Parameters
    ----------
    action : str
        The action to check
    """
    arguments = {
        "action": action,
        "file": None,
        "folder": None,
        "all": None,
        "move_path": None,
    }

    assert not __validate_arguments(arguments), "Nothing except action should fail"
    arguments["file"] = "foo"
    assert not __validate_arguments(arguments), "Missing file specified should fail"

    arguments["file"] = MOCK_FILE
    make_mock_file()
    assert __validate_arguments(arguments), "Existing file specified should pass"
    arguments["file"] = None
    arguments["folder"] = MOCK_FILE
    assert not __validate_arguments(arguments), "File cannot be used as folder"
    remove_mock()

    # Cannot have both specified
    arguments["file"] = "bar"
    assert not __validate_arguments(arguments), "Cannot specify both file and folder"

    arguments["file"] = None
    assert not __validate_arguments(arguments), "Missing folder specified should fail"
    make_mock_folder()
    assert __validate_arguments(arguments), "Existing folder specified should pass"

    arguments["file"] = MOCK_FILE
    arguments["folder"] = None
    assert not __validate_arguments(arguments), "Folder cannot be used as file"
    remove_mock()


def check_generic_all(action: str):
    """
    Commands that accept "all" as an argument will not accept file/folder
    Abstract this to simplify the code

    Parameters
    ----------
    action : str
        The action to check
    """
    arguments = {
        "action": action,
        "file": None,
        "folder": None,
        "all": None,
        "move_path": None,
    }

    arguments["all"] = True
    assert __validate_arguments(arguments), "Only 'all' should be valid"

    arguments["move_path"] = "test/"
    assert __validate_arguments(arguments), "move_path should be ignored"

    make_mock_file()
    arguments["file"] = MOCK_FILE
    assert not __validate_arguments(
        arguments
    ), "'All' plus file (even if existing) should fail"

    remove_mock()
    make_mock_folder()
    arguments["folder"] = MOCK_FILE
    assert not __validate_arguments(
        arguments
    ), "'All' plus folder (even if existing) should fail"


def test_add():
    """
    Test the "add" action branch of arguments
    """
    check_generic_file_folder("add")

    arguments = {
        "action": "remove",
        "file": MOCK_FILE,
        "folder": None,
        "all": None,
        "move_path": None,
    }

    make_mock_file()

    # Set irrelevant arguments, should still be valid since ignored
    arguments["all"] = True
    arguments["move_path"] = "test/"
    assert __validate_arguments(
        arguments
    ), "Irrelevant arguments should be ignored, and pass"

    remove_mock()


def test_remove():
    """
    Test the "remove" action branch of arguments
    """
    check_generic_file_folder("remove")

    arguments = {
        "action": "remove",
        "file": MOCK_FILE,
        "folder": None,
        "all": None,
        "move_path": None,
    }

    make_mock_file()

    # Set irrelevant arguments, should still be valid since ignored
    arguments["all"] = True
    arguments["move_path"] = "test/"
    assert __validate_arguments(
        arguments
    ), "Irrelevant arguments should be ignored, and pass"

    remove_mock()


def test_restore():
    """
    Test the restore parameter validation
    """
    check_generic_file_folder("restore")
    check_generic_all("restore")


def test_verify():
    """
    Test the verify parameter validation
    """
    check_generic_file_folder("verify")
    check_generic_all("verify")


def test_move():
    """
    Test the move functionality
    """
    arguments = {
        "action": "move",
        "file": None,
        "folder": None,
        "all": None,
        "move_path": None,
    }

    assert not __validate_arguments(arguments), "Only specifying action should fail"
    make_mock_file()
    arguments["file"] = MOCK_FILE
    assert not __validate_arguments(arguments), "Missing move_path should fail"

    arguments["move_path"] = "dest_folder/"
    assert __validate_arguments(arguments), "File and destination should pass"
    arguments["all"] = True
    assert __validate_arguments(
        arguments
    ), "File and destination should pass, 'all' is ignored"

    arguments["folder"] = MOCK_FILE
    assert not __validate_arguments(arguments), "Specifying file and folder should fail"
    arguments["file"] = False
    assert not __validate_arguments(arguments), "File cannot be used as folder"

    remove_mock()
    make_mock_folder()
    assert __validate_arguments(arguments), "Folder and destination should pass"
    remove_mock()
