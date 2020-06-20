"""
Test less-complex library functions
"""
import hashlib
from os import path, urandom, remove
import tempfile

from logical_backup.main import __dispatch_command
from logical_backup import library
from logical_backup.objects.file import File
from logical_backup.db import initialize_database, DatabaseError
import logical_backup.db as db

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing
from logical_backup import utility

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from tests.test_db import auto_clear_db
from tests.test_arguments import make_arguments
from tests.mock_db import mock_devices


def __make_temp_file(size: int = 1024) -> tuple:
    """
    Makes a random temp file and files it with random data, by default 1kB

    Parameters
    ----------
    size = 1024 : int
        Size to make the file

    Returns
    -------
    tuple
        Path to the file, MD5 checksum of input data
    """
    descriptor, name = tempfile.mkstemp()
    file_handle = open(descriptor, "wb")
    data = urandom(size)
    file_handle.write(data)
    file_handle.close()

    checksum = hashlib.md5(data).hexdigest()

    return (name, checksum)


def __make_temp_directory() -> str:
    """
    Makes a temporary directory

    Returns
    -------
    str
        Path to the directory
    """
    return tempfile.mkdtemp()


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

    # Invalid identifier, should only happen on DB corruption
    monkeypatch.setattr(
        db, "add_device", lambda device: DatabaseError.INVALID_IDENTIFIER_TYPE
    )
    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Unrecognized device identifier" in output.out
    ), "Invalid identifier for device should fail to add"

    # Unknown error can occur in weird circumstances
    monkeypatch.setattr(db, "add_device", lambda device: DatabaseError.UNKNOWN_ERROR)
    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Unknown error occurred" in output.out
    ), "Unknown error should cause a failure"

    # Some bizarre return value
    monkeypatch.setattr(db, "add_device", lambda device: -999)
    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Super-unknown error occurred" in output.out
    ), "Bizarre return value should cause a failure"


def test_add_file_success(monkeypatch, capsys):
    """
    Test successful adding of file
    """
    db.initialize_database()

    test_mount_1 = __make_temp_directory()
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "test-serial-1")
    # Builtins should be patchable
    # pylint: disable=no-member
    monkeypatch.setitem(utility.__builtins__, "input", lambda prompt: "test-device-1")
    assert library.add_device(test_mount_1), "Making test device should succeed"

    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda path: {
            "permissions": "644",
            "owner": "test-owner",
            "group": "test-group",
        },
    )

    test_file, test_checksum = __make_temp_file()
    # Use actual sizes/checksum, since that will be fine
    # If temp runs out of space, that would be an actual issue for system stability
    # so don't mock that
    assert library.add_file(test_file), "Test file should be added"
    files = db.get_files()
    assert len(files) == 1, "Exactly one file should be in the database"

    hashlib.md5()
    expected = File()
    expected.set_properties(path.basename(test_file), test_file, test_checksum)
    expected.set_security("644", "test-owner", "test-group")
    expected.device_name = "test-device-1"
    assert files[0] == expected, "Only one file is added so far"

    test_output_path = path.join(test_mount_1, test_file)
    assert path.isfile(test_output_path), "Output path should be a file"
    assert test_checksum == utility.checksum_file(
        test_output_path
    ), "Output checksum should match input"

    remove(test_file)
    assert db.remove_file(test_file), "Test file should be removed"


def test_add_file_failures(monkeypatch, capsys):
    """
    .
    """
    db.initialize_database()

    monkeypatch.setattr(db, "file_exists", lambda path: True)
    added = library.add_file("/file")
    output = capsys.readouterr()
    assert not added, "Existing path should not be added"
    assert (
        "File is already backed up" in output.out
    ), "Existing path output should be printed"

    # Path has insufficient space, and user exits
    monkeypatch.setattr(db, "file_exists", lambda path: False)
    monkeypatch.setattr(utility, "get_file_size", lambda path: 1)
    monkeypatch.setattr(utility, "get_device_space", lambda path: 0)
    # Builtins should be patchable
    # pylint: disable=no-member
    monkeypatch.setitem(library.__builtins__, "input", lambda text: "n")

    added = library.add_file("/file", "/mnt")
    output = capsys.readouterr()
    assert not added, "Insufficient space with exit should fail"
    assert (
        "Checking drive space...Insufficient space" in output.out
    ), "insufficient space message printed"

    # Check a failed checksum exits
    monkeypatch.setattr(utility, "get_file_security", lambda path: "unimportant")
    monkeypatch.setattr(utility, "checksum_file", lambda path: "")

    added = library.add_file("/file")
    output = capsys.readouterr()
    assert not added, "Failed checksum should exit"
    assert (
        "Failed to get checksum" in output.out
    ), "Failed checksum should print message"

    # Adding a file to a device should work, with only one available device
    monkeypatch.undo()


def test_add_file_device_fallbacks(monkeypatch, capsys):
    """
    .
    """
    # Specified device doesn't have enough space and drops back to auto selection
    # Device without enough space is skipped for one that does, stops at second of three devices
    # Specified device is used, even if it isn't first in the list
    # Checksum mismatch after copy - file should be removed
