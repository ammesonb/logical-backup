"""
Test main script entry point
"""
import os.path
from types import FunctionType
from pytest import raises

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import run_command, auto_set_testing
import logical_backup.main as main  # for input mocking
import logical_backup.library as library  # for input mocking
from logical_backup.main import __check_devices
from tests.test_arguments import (
    make_arguments,
    MOCK_FILE,
    make_mock_folder,
    remove_mock,
)
from tests.mock_db import mock_devices


# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from tests.test_db import auto_clear_db


def test_help():
    """
    Test help is printed and exits normally
    """
    result = run_command(["python3", "logical_backup_script.py", "-h"])
    assert result["exit_code"] == 0, "Result should pass for help flag"
    assert "usage: logical_backup_script.py" in result["stdout"].decode(
        "utf-8"
    ), "Usage should be printed"


def test_missing_action():
    """
    Test missing the action
    """
    result = run_command(["python3", "logical_backup_script.py"])
    assert result["exit_code"] == 2, "Result should fail if missing the acton"


def test_unrecognized_action():
    """
    Test an action which isn't in the command set
    """
    result = run_command(["python3", "logical_backup_script.py", "unrecognized"])
    assert result["exit_code"] == 2, "Result should fail if the action is unrecognized"


def test_check_devices(capsys, monkeypatch):
    """
    Test device checking code
    """
    # DB should return nothing, to start
    mock_devices(monkeypatch, [])
    arguments = make_arguments("verify")
    with raises(SystemExit) as pytest_exception:
        __check_devices(arguments)

    assert (
        pytest_exception.type is SystemExit
    ), "No device exception should be system exit"
    assert pytest_exception.value.code == 3, "No device exit status should be 3"
    output = capsys.readouterr()
    assert (
        "A device must be added before" in output.out
    ), "No device message was not printed"

    # Adding only is not sufficient
    arguments["action"] = "add"

    with raises(SystemExit) as pytest_exception:
        __check_devices(arguments)

    assert (
        pytest_exception.type is SystemExit
    ), "No device exception for add should be system exit"
    assert pytest_exception.value.code == 3, "No device for add exit status should be 3"
    output = capsys.readouterr()
    assert (
        "A device must be added before" in output.out
    ), "No device for add message was not printed"

    arguments["device"] = MOCK_FILE

    __check_devices(arguments)
    output = capsys.readouterr()
    assert (
        "devices...Missing, but OK" in output.out
    ), "Adding device message did not print"

    make_mock_folder()
    monkeypatch.setattr(os.path, "ismount", lambda path: path == MOCK_FILE)
    mock_devices(
        monkeypatch,
        [
            {
                "device_name": "test1",
                "device_path": MOCK_FILE,
                "identifier_name": "Device Serial",
                "device_identifier": "12345",
            }
        ],
    )
    __check_devices(arguments)
    output = capsys.readouterr()
    assert (
        "All devices found" in output.out
    ), "All devices found did not print expected message"

    mock_devices(
        monkeypatch,
        [
            {
                "device_name": "test1",
                "device_path": MOCK_FILE,
                "identifier_name": "Device Serial",
                "device_identifier": "12345",
            },
            {
                "device_name": "test2",
                "device_path": MOCK_FILE + "_nonexistent",
                "identifier_name": "Device Serial",
                "device_identifier": "54321",
            },
        ],
    )
    # The __builtins__ isn't _officially_ a part of a class, so pylint is mad
    # _Should_ be safe though, I would expect
    # pylint: disable=no-member
    monkeypatch.setitem(main.__builtins__, "input", lambda message: "n")

    with raises(SystemExit) as pytest_exception:
        __check_devices(arguments)

    assert (
        pytest_exception.type is SystemExit
    ), "Some device found (n) exception should be system exit"
    assert (
        pytest_exception.value.code == 3
    ), "Soem device found (n) exit status should be 3"
    output = capsys.readouterr()
    assert (
        "Found some devices" in output.out
    ), "Some devices found (n) did not print expected message"

    # The __builtins__ isn't _officially_ a part of a class, so pylint is mad
    # _Should_ be safe though, I would expect
    # pylint: disable=no-member
    monkeypatch.setitem(main.__builtins__, "input", lambda message: "y")
    __check_devices(arguments)
    output = capsys.readouterr()
    assert (
        "Found some devices" in output.out
    ), "Some devices found (y) did not print expected message"
    assert (
        "Continuing without all devices" in output.out
    ), "Some devices found (y) did not print expected continuation message"
    remove_mock()


def test_parse_arguments():
    """
    .
    """
    parsed = main.__parse_arguments(["add", "--device", "/mnt"])
    expected = make_arguments("add")
    expected["device"] = "/mnt"
    assert parsed == expected, "Add device arguments should match"

    parsed = main.__parse_arguments(["add", "--file", "/mnt"])
    expected["device"] = None
    expected["file"] = "/mnt"
    assert parsed == expected, "Add file arguments should match"

    parsed = main.__parse_arguments(["remove", "--folder", "/mnt"])
    expected["action"] = "remove"
    expected["file"] = None
    expected["folder"] = "/mnt"
    assert parsed == expected, "Remove folder arguments should match"

    parsed = main.__parse_arguments(["verify", "--folder", "/mnt", "--device", "/foo"])
    expected["action"] = "verify"
    expected["folder"] = "/mnt"
    expected["device"] = "/foo"
    assert parsed == expected, "Verify folder on device should match"

    parsed = main.__parse_arguments(["update", "--folder", "/home/foo/test",])
    expected["action"] = "update"
    expected["folder"] = "/home/foo/test"
    expected["device"] = None
    assert parsed == expected, "Update folder should match"

    parsed = main.__parse_arguments(
        ["move", "--file", "/root/bar.txt", "--move-path", "/home/user/"]
    )
    expected["action"] = "move"
    expected["file"] = "/root/bar.txt"
    expected["folder"] = None
    expected["move_path"] = "/home/user/"
    assert parsed == expected, "Move file should match"


def test_invalid_arguments():
    """
    Check system exits on invalid arguments
    """
    # Add requires, something to add
    with raises(SystemExit) as pytest_exception:
        main.process(["add"])
        assert pytest_exception.value.code == 1, "Invalid arguments should exit 1"


def test_command_run(monkeypatch, capsys):
    """
    Checks which command was run, end-to-end analysis
    """
    library_attrs = library.__dict__.keys()
    for attr in library_attrs:
        if type(getattr(library, attr) is FunctionType):
            monkeypatch.setattr(library, attr, lambda *args, **kwargs: None)

    # Pretend everything is valid, because it should be for this test
    monkeypatch.setattr(main, "__validate_arguments", lambda args: True)
    # Bypass device check
    monkeypatch.setattr(main, "__check_devices", lambda args: True)

    arguments = ["add", "--device", "/mnt"]
    assert main.process(arguments) == "add-device", "Add device"

    arguments = ["add", "--file", "foo"]
    assert main.process(arguments) == "add-file", "Add file"

    arguments = ["add", "--file", "foo", "--device", "/mnt"]
    assert main.process(arguments) == "add-file", "Add file with device"

    arguments = ["add", "--folder", "foo"]
    assert main.process(arguments) == "add-folder", "Add folder"

    arguments = ["remove", "--file", "foo"]
    assert main.process(arguments) == "remove-file", "Remove file"

    arguments = ["remove", "--folder", "foo"]
    assert main.process(arguments) == "remove-folder", "Remove folder"

    arguments = ["update", "--file", "foo"]
    assert main.process(arguments) == "update-file", "Update file"

    arguments = ["update", "--folder", "foo"]
    assert main.process(arguments) == "update-folder", "Update folder"

    arguments = ["restore", "--file", "foo"]
    assert main.process(arguments) == "restore-file", "Restore file"

    arguments = ["restore", "--folder", "foo"]
    assert main.process(arguments) == "restore-folder", "Restore folder"

    arguments = ["restore", "--file", "foo"]
    assert main.process(arguments) == "restore-file", "Restore file"

    arguments = ["restore", "--folder", "foo"]
    assert main.process(arguments) == "restore-folder", "Restore folder"

    arguments = ["restore", "--all"]
    assert main.process(arguments) == "restore-all", "Restore all"

    arguments = ["verify", "--file", "foo"]
    assert main.process(arguments) == "verify-file", "Verify file"

    arguments = ["verify", "--folder", "foo"]
    assert main.process(arguments) == "verify-folder", "Verify folder"

    arguments = ["verify", "--all"]
    assert main.process(arguments) == "verify-all", "Verify all"

    arguments = ["move", "--file", "foo", "--move-path", "/root"]
    assert main.process(arguments) == "move-file", "Move file"

    arguments = ["move", "--folder", "foo", "--device", "/mnt"]
    assert main.process(arguments) == "move-folder", "Move folder"

    arguments = ["move", "--folder", "foo", "--move-path", "/home/user/"]
    assert main.process(arguments) == "move-folder", "Move folder"

    arguments = ["list-devices"]
    assert main.process(arguments) == "list-devices", "List devices"
