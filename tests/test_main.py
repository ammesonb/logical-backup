"""
Test main script entry point
"""
import os.path
from pytest import raises

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import run_command, auto_set_testing
import logical_backup.db as db
import logical_backup.main as main  # for input mocking
from logical_backup.main import __check_devices
from tests.test_arguments import (
    make_arguments,
    MOCK_FILE,
    make_mock_folder,
    remove_mock,
)


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
    monkeypatch.setattr(db, "get_devices", lambda: [])
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
    assert "devices...Adding" in output.out, "Adding device message did not print"

    make_mock_folder()
    monkeypatch.setattr(os.path, "ismount", lambda path: path == MOCK_FILE)
    monkeypatch.setattr(
        db,
        "get_devices",
        lambda: [
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

    monkeypatch.setattr(
        db,
        "get_devices",
        lambda: [
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
