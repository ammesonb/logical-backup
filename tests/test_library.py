"""
Test less-complex library functions
"""
import hashlib
from os import path, urandom, remove
import tempfile

from logical_backup.main import __dispatch_command
from logical_backup import library
from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.db import initialize_database, DatabaseError
from logical_backup import db

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing, DirectoryEntries
from logical_backup import utility
from tests.test_utility import patch_input

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from tests.test_db import auto_clear_db
from tests.test_arguments import make_arguments
from tests.mock_db import mock_devices


def __make_temp_file(size: int = 1024, directory: str = None) -> tuple:
    """
    Makes a random temp file and files it with random data, by default 1kB

    Parameters
    ----------
    size = 1024 : int
        Size to make the file
    directory : str
        The directory to make the file in

    Returns
    -------
    tuple
        Path to the file, MD5 checksum of input data
    """
    descriptor, name = tempfile.mkstemp(dir=directory)
    file_handle = open(descriptor, "wb")
    data = urandom(size)
    file_handle.write(data)
    file_handle.close()

    checksum = hashlib.md5(data).hexdigest()

    return (name, checksum)


def __make_temp_directory(parent: str = None) -> str:
    """
    Makes a temporary directory

    Parameters
    ----------
    parent : str
        Optionally, parent directory to create this one in

    Returns
    -------
    str
        Path to the directory
    """
    return tempfile.mkdtemp(dir=parent)


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

    patch_input(monkeypatch, library, lambda message: "device-1")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12345")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Saving device...Done" in output.out
    ), "First device, by serial, should be saved"

    # Happy path two
    arguments["device"] = "/mnt/test2"
    patch_input(monkeypatch, library, lambda message: "device-2")
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
    patch_input(
        monkeypatch,
        library,
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
    patch_input(monkeypatch, library, lambda message: "device-1")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12346")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Name already taken" in output.out
    ), "Fourth device should fail due to name conflict"

    # Sad path two
    arguments["device"] = "/mnt/test1"
    patch_input(monkeypatch, library, lambda message: "device-5")
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "12346")

    command = __dispatch_command(arguments)
    assert command == "add-device", "Command called should be add device"
    output = capsys.readouterr()
    assert (
        "Device already registered at mount point" in output.out
    ), "Fifth device should fail due to path conflict"

    # Sad path three
    arguments["device"] = "/mnt/test6"
    patch_input(monkeypatch, library, lambda message: "device-6")
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


def test_get_device_with_space(monkeypatch, capsys):
    """
    Check device resolution for given space constraints
    """
    db.initialize_database()

    # Path has insufficient space, and user exits
    monkeypatch.setattr(
        utility, "get_device_space", lambda path: 0 if path == "/mnt1" else 100
    )
    patch_input(monkeypatch, library, lambda message: "n")

    name, path = library.__get_device_with_space(1, "/mnt1")
    output = capsys.readouterr()
    assert not name and not path, "Insufficient space with exit should be empty"
    assert (
        "Checking drive space...Insufficient space" in output.out
    ), "insufficient space message printed"

    # Path has insufficient space, user continues
    patch_input(monkeypatch, library, lambda message: "y")
    device = Device()
    device.set("test1", "/mnt1", "Device Serial", "ABCDEF", 1)
    device2 = Device()
    device2.set("test2", "/mnt2", "Device Serial", "123456", 1)

    monkeypatch.setattr(db, "get_devices", lambda: [device, device2])

    name, path = library.__get_device_with_space(1, "/mnt1")
    output = capsys.readouterr()
    assert (
        "Insufficient space" in output.out
    ), "Initial device should have insufficient space"
    assert "Auto-selecting device" in output.out, "Should fall back to auto-selection"
    assert "Selected test2" in output.out, "Selected device should be printed"
    assert name == "test2", "Second device should be selected"
    assert path == "/mnt2", "Second path should be selected"

    # No devices have enough space
    monkeypatch.setattr(utility, "get_device_space", lambda path: 0)
    name, path = library.__get_device_with_space(1, "/mnt1")
    output = capsys.readouterr()
    assert "Auto-selecting device" in output.out, "Should fall back to auto-selection"
    assert "None found!" in output.out, "No device found printed"
    assert not name, "No device name should be returned"
    assert not path, "No device path should be returned"

    # Requested device is full, falls back to second (not third)
    device3 = Device()
    device3.set("test3", "/mnt3", "Device Serial", "112233", 1)

    monkeypatch.setattr(db, "get_devices", lambda: [device, device2, device3])
    monkeypatch.setattr(
        utility, "get_device_space", lambda path: 0 if path == "/mnt1" else 100
    )

    name, path = library.__get_device_with_space(1, "/mnt1")
    output = capsys.readouterr()

    assert "Auto-selecting device" in output.out, "Should fall back to auto-selection"
    assert "Selected test2" in output.out, "Selected device should be printed"
    assert name == "test2", "Second device should be selected"
    assert path == "/mnt2", "Second path should be selected"

    name, path = library.__get_device_with_space(1, "/mnt3")
    output = capsys.readouterr()

    assert (
        "Checking drive space...Done" in output.out
    ), "Should check provided mount point"
    assert name == "test3", "Provided device name should be selected"
    assert path == "/mnt3", "Provided device path should be selected"


def test_add_file_success(monkeypatch, capsys):
    """
    Test successful adding of file
    """
    db.initialize_database()

    test_mount_1 = __make_temp_directory()
    monkeypatch.setattr(utility, "get_device_serial", lambda path: "test-serial-1")
    patch_input(monkeypatch, library, lambda message: "test-device-1")
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
    monkeypatch.setattr(
        library,
        "__get_device_with_space",
        lambda size, mount=None, checked=False: ("test-device-1", test_mount_1),
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

    # Check a failed checksum exits
    monkeypatch.setattr(db, "file_exists", lambda path: False)
    monkeypatch.setattr(utility, "get_file_security", lambda path: "unimportant")
    monkeypatch.setattr(utility, "checksum_file", lambda path: "")

    added = library.add_file("/file")
    output = capsys.readouterr()
    assert not added, "Failed checksum should exit"
    assert (
        "Failed to get checksum" in output.out
    ), "Failed checksum should print message"

    # Check no device available exits
    test_file, test_checksum = __make_temp_file()
    test_mount_1 = __make_temp_directory()

    monkeypatch.setattr(db, "file_exists", lambda path: False)
    monkeypatch.setattr(utility, "get_file_size", lambda path: 1)
    monkeypatch.setattr(utility, "checksum_file", lambda path: "unimportant")
    monkeypatch.setattr(utility, "get_file_security", lambda path: "unimportant")
    monkeypatch.setattr(
        library, "__get_device_with_space", lambda size, mount, checked: (None, None)
    )

    added = library.add_file(test_file, test_mount_1)
    output = capsys.readouterr()
    assert not added, "No device available should fail"
    assert (
        "No device with space available" in output.out
    ), "No device available message printed"

    # Checksum mismatch after copy - file should be removed
    monkeypatch.setattr(
        utility, "checksum_file", lambda path: "123" if path == test_file else "321"
    )
    monkeypatch.setattr(
        library,
        "__get_device_with_space",
        lambda size, mount, checked: ("test-device-1", test_mount_1),
    )
    monkeypatch.setattr(
        utility, "create_backup_name", lambda file_path: path.basename(test_file)
    )
    added = library.add_file(test_file, test_mount_1)
    output = capsys.readouterr()

    assert not added, "Mismatched checksum should fail"
    assert (
        "Checksum mismatch after copy" in output.out
    ), "Mismatch checksum message should print"
    output_file = path.join(test_mount_1, path.basename(test_file))
    assert not path.isfile(
        output_file
    ), "Output file should be deleted after mismatched checksum"
    assert (
        not db.get_files()
    ), "No file should be saved to database given mismatched checksum"

    # Database save failure, file should be removed
    monkeypatch.setattr(utility, "checksum_file", lambda path: "123")
    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda path: {
            "permissions": "644",
            "owner": "test-owner",
            "group": "test-group",
        },
    )
    monkeypatch.setattr(db, "add_file", lambda file_obj: DatabaseError.UNKNOWN_ERROR)
    added = library.add_file(test_file, test_mount_1)
    output = capsys.readouterr()

    assert not added, "Database exception should fail"
    assert (
        "Saving file record to DB...Failed" in output.out
    ), "Database exception message should print"
    output_file = path.join(test_mount_1, path.basename(test_file))
    assert not path.isfile(
        output_file
    ), "Output file should be deleted after database failure"
    assert (
        not db.get_files()
    ), "No file should be saved to database given database failure"


def test_add_directory(monkeypatch, capsys):
    """
    .
    """
    # Happy path
    monkeypatch.setattr(
        utility,
        "list_entries_in_directory",
        lambda directory: DirectoryEntries(["/test/file1", "/test/file2"], []),
    )
    monkeypatch.setattr(utility, "sum_file_size", lambda files: 5)
    monkeypatch.setattr(library, "__get_total_device_space", lambda: 10)
    monkeypatch.setattr(library, "add_file", lambda file_path, mount_point=None: True)
    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda path: {"permissions": "755", "owner": "test", "group": "test"},
    )
    monkeypatch.setattr(db, "add_folder", lambda folder: DatabaseError.SUCCESS)

    assert library.add_directory("/test"), "Adding folder of files should succeed"

    # Failed to add folder
    monkeypatch.setattr(db, "add_folder", lambda folder: DatabaseError.UNKNOWN_ERROR)
    assert not library.add_directory(
        "/test"
    ), "Should fail if unable to add parent folder"
    monkeypatch.setattr(db, "add_folder", lambda folder: DatabaseError.SUCCESS)

    # Failed to add subfolders
    monkeypatch.setattr(
        utility,
        "list_entries_in_directory",
        lambda directory: DirectoryEntries(
            ["/test/file1", "/test/file2"], ["/test/foo", "/test/bar"]
        ),
    )
    monkeypatch.setattr(
        db,
        "add_folder",
        lambda folder: DatabaseError.SUCCESS
        if folder.folder_path == "/test"
        else DatabaseError.UNKNOWN_ERROR,
    )
    assert not library.add_directory("/test"), "Should fail if unable to add subfolder"

    # Subfolders added successfully
    monkeypatch.setattr(db, "add_folder", lambda folder: DatabaseError.SUCCESS)
    assert library.add_directory("/test"), "Adding files and subfolders should succeed"

    # Not enough space across all devices
    monkeypatch.setattr(library, "__get_total_device_space", lambda: 0)
    assert not library.add_directory(
        "/test"
    ), "Insufficient total device space should fail"
    out = capsys.readouterr()
    assert (
        "Sum of available devices' space is insufficient" in out.out
    ), "Insufficient total space message should print"

    # In this case, the selected device does not have enough space
    # nor do the sum of all devices, so do not even prompt to reassign selected device
    monkeypatch.setattr(utility, "get_device_space", lambda files: 0)
    assert not library.add_directory("/test", "/mnt"), (
        "Adding directory to mount point should fail, "
        "insufficient total space not device space"
    )
    out = capsys.readouterr()
    assert (
        "Sum of available devices' space is insufficient" in out.out
    ), "Insufficient total space message should print"

    # Insufficient space on selected device but enough on all drives,
    # User exits on prompt
    monkeypatch.setattr(library, "__get_total_device_space", lambda: 10)
    patch_input(monkeypatch, library, lambda prompt: "n")
    assert not library.add_directory(
        "/test", "/mnt"
    ), "Insufficient space on selected device, with exit input should fail"
    out = capsys.readouterr()
    assert (
        "Selected device will not fit all files" in out.out
    ), "Insufficient device space message should print"
    assert (
        "Exiting since unable to fit all files on selected device" in out.out
    ), "Insufficient device space exit message should print"

    # Check success if user does allow reassigning of device
    patch_input(monkeypatch, library, lambda prompt: "y")
    assert library.add_directory(
        "/test", "/mnt"
    ), "Insufficient space on selected device, with exit input should fail"
    out = capsys.readouterr()
    assert (
        "Selected device will not fit all files" in out.out
    ), "Insufficient device space message should print"


def test_get_total_device_space(monkeypatch):
    """
    .
    """
    device = Device()
    device.set("test1", "/mnt1", "Device Serial", "ABCDEF", 1)
    device2 = Device()
    device2.set("test2", "/mnt2", "Device Serial", "123456", 1)

    monkeypatch.setattr(db, "get_devices", lambda: [device, device2])
    monkeypatch.setattr(path, "ismount", lambda file_path: True)
    monkeypatch.setattr(
        utility,
        "get_device_space",
        lambda mount_point: 15 if mount_point == "/mnt1" else 5,
    )

    assert library.__get_total_device_space() == 20, "Two mounted devices add"

    monkeypatch.setattr(path, "ismount", lambda file_path: file_path == "/mnt1")
    assert library.__get_total_device_space() == 15, "Filters unmounted devices"
