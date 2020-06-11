"""
Test less-complex library functions
"""
from os import path

from logical_backup.main import __dispatch_command
from logical_backup import library
from logical_backup.db import initialize_database

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing
from logical_backup import utility

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from tests.test_db import auto_clear_db
from tests.test_arguments import make_arguments
from tests.mock_db import mock_devices


def test_list_devices(monkeypatch, capsys):
    """
    Test listing of devices
    """
    arguments = make_arguments("list-devices")
    mock_devices(monkeypatch, [])
    __dispatch_command(arguments)
    output = capsys.readouterr()
    assert "No devices saved!" in output.out, "No devices should be present in list"

    mock_devices(
        monkeypatch,
        [
            {
                "device_name": "test_device",
                "device_path": "/mnt/dev1",
                "identifier_name": "Device Serial",
                "device_identifier": "ABCDEF1234",
            },
            {
                "device_name": "seagate_drive",
                "device_path": "/mnt/dev2",
                "identifier_name": "System UUID",
                "device_identifier": "123456-ABCDEF-654321",
            },
        ],
    )
    command = __dispatch_command(arguments)
    output = capsys.readouterr()
    assert command == "list-devices", "Command called should be list devices"
    assert (
        "| test_device   | /mnt/dev1   | Device Serial   | ABCDEF1234" in output.out
    ), "Test device 1 missing"
    assert (
        "| seagate_drive | /mnt/dev2   | System UUID     | 123456-ABCDEF-654321"
        in output.out
    ), "Seagate test device 2 missing"


def test_add_device(capsys, monkeypatch):
    """
    Test output of adding a device
    """
    initialize_database()

    arguments = make_arguments("add")

    # Happy path one
    arguments["device"] = "/mnt/test1"
    monkeypatch.setattr(path, "ismount", lambda path: True)

    # The __builtins__ isn't _officially_ a part of a class, so pylint is mad
    # _Should_ be safe though, I would expect
    # pylint: disable=no-member
    monkeypatch.setitem(library.__builtins__, "input", lambda message: "device-1")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12345")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Saving device...Done" in output.out
    ), "First device, by serial, should be saved"

    # Happy path two
    arguments["device"] = "/mnt/test2"
    monkeypatch.setitem(library.__builtins__, "input", lambda message: "device-2")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: None)
    monkeypatch.setattr(
        utility, "get_device_uuid", lambda path: "2ba7b22c-89c6-4125-a4e0-ed5609b81b14"
    )

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Saving device...Done" in output.out
    ), "Second device, by UUID, should be saved"

    # Happy path three
    monkeypatch.setitem(
        library.__builtins__,
        "input",
        lambda message: "device-3" if message == "Device name: " else "External HDD-1",
    )
    monkeypatch.setattr(utility, "get_device_serial", lambda path: None)
    monkeypatch.setattr(utility, "get_device_uuid", lambda path: None)

    arguments["device"] = "/mnt/test3"
    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Saving device...Done" in output.out
    ), "Third device, specified by user, should be saved"

    # Sad path one
    arguments["device"] = "/mnt/test4"
    monkeypatch.setitem(library.__builtins__, "input", lambda message: "device-1")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12346")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Name already taken" in output.out
    ), "Fourth device should fail due to name conflict"

    # Sad path two
    arguments["device"] = "/mnt/test1"
    monkeypatch.setitem(library.__builtins__, "input", lambda message: "device-5")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12346")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Device already registered at mount point" in output.out
    ), "Fifth device should fail due to path conflict"

    # Sad path three
    arguments["device"] = "/mnt/test6"
    monkeypatch.setitem(library.__builtins__, "input", lambda message: "device-6")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12345")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Serial already registered" in output.out
    ), "Sixth device should fail due to serial conflict"
