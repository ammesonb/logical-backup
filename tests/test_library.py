"""
Test less-complex library functions
"""
import grp
import hashlib
import os
from os import path, urandom, remove, getuid, getegid
import pwd
import shutil
import tempfile

from logical_backup.main import __dispatch_command
from logical_backup import library
from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.objects.folder import Folder
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


# pylint: disable=bad-continuation
def __make_temp_file(
    size: int = 1024, directory: str = None, data: bytes = None
) -> tuple:
    """
    Makes a random temp file and files it with random data, by default 1kB

    Parameters
    ----------
    size = 1024 : int
        Size to make the file
    directory : str
        The directory to make the file in
    data : bytes
        Optionally, the data to put in the file

    Returns
    -------
    tuple
        Path to the file, MD5 checksum of input data
    """
    descriptor, name = tempfile.mkstemp(dir=directory)
    file_handle = open(descriptor, "wb")
    if not data:
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
        "Saving device...Completed" in output.out
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
        "Saving device...Completed" in output.out
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
        "Saving device...Completed" in output.out
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
        "Checking drive space...Completed" in output.out
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
    monkeypatch.setattr(
        utility, "create_backup_name", lambda file_path: path.basename(file_path)
    )
    assert library.add_file(test_file), "Test file should be added"
    files = db.get_files()
    assert len(files) == 1, "Exactly one file should be in the database"

    hashlib.md5()
    expected = File()
    expected.set_properties(path.basename(test_file), test_file, test_checksum)
    expected.set_security("644", "test-owner", "test-group")
    expected.device_name = "test-device-1"
    assert files == [expected], "Only one file is added so far"

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
    monkeypatch.setattr(db, "get_folders", lambda folder_path: ["anything"])
    assert library.add_directory("/test"), "Succeeds if folder already exists"
    out = capsys.readouterr()
    assert "Folder already added" in out.out, "Already exists message prints"

    # Happy path
    monkeypatch.setattr(db, "get_folders", lambda folder_path: [])
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


def test_remove_file(monkeypatch, capsys):
    """
    .
    """
    # No file returned
    monkeypatch.setattr(db, "get_files", lambda path=None: [])

    assert not library.remove_file("/test"), "Unadded file cannot be removed"
    out = capsys.readouterr()
    assert (
        "Validating file removal...File not registered in database" in out.out
    ), "Unadded file prints message"

    # Having a file, but no device, fails
    test_file, checksum = __make_temp_file()

    file1 = File()
    file1.set_properties("test", "test", "abcdef123")
    file1.set_security("644", "test", "test")
    file1.device_name = "dev"
    monkeypatch.setattr(db, "get_files", lambda path=None: [file1])
    monkeypatch.setattr(db, "get_devices", lambda name=None: [])

    assert not library.remove_file(test_file), "Missing device causes failure"
    out = capsys.readouterr()
    assert (
        "Validating file removal...Unable to find device" in out.out
    ), "Missing device message printed"

    # A device exists, but the file is not there
    device1 = Device()
    device1.set("dev", "/dev1", "Device Serial", "fake", "1")
    monkeypatch.setattr(db, "get_devices", lambda device: [device1])

    assert not library.remove_file(test_file), "Nonexistent system path causes failure"
    out = capsys.readouterr()
    assert (
        "Validating file removal...File path does not exist" in out.out
    ), "Nonexistent system path message prints"

    # Database removal failure, with a file in a directory
    test_directory = __make_temp_directory()
    test_file_2, checksum_2 = __make_temp_file(directory=test_directory)
    # pylint: disable=unused-variable
    actual_file_path, actual_checksum = __make_temp_file()

    device2 = Device()
    device2.set("dev", test_directory, "Device Serial", "fake", "1")
    monkeypatch.setattr(db, "get_devices", lambda device: [device2])

    file2 = File()
    file2.set_properties(test_file_2, actual_file_path, checksum_2)
    file2.set_security("644", "test", "test")
    monkeypatch.setattr(db, "get_files", lambda path: [file2])

    monkeypatch.setattr(db, "remove_file", lambda path: DatabaseError.UNKNOWN_ERROR)
    assert not library.remove_file(test_file), "Database failure causes failure"
    out = capsys.readouterr()
    assert (
        "Validating file removal...Failed to remove file from database" in out.out
    ), "Database failure message prints"
    assert path.exists(test_file_2), "Test file should not be removed yet"

    # File removal is successful
    monkeypatch.setattr(db, "remove_file", lambda path: DatabaseError.SUCCESS)
    assert library.remove_file(test_file), "File removed successfully"
    out = capsys.readouterr()
    assert (
        "Validating file removal...File removed" in out.out
    ), "File removal success message should print"

    assert not path.exists(test_file_2), "Test file is removed"
    assert path.exists(actual_file_path), "Actual file should NOT be deleted"

    remove(test_file)
    remove(actual_file_path)


def test_remove_folder(monkeypatch, capsys):
    """
    .
    """
    monkeypatch.setattr(library, "remove_file", lambda file_path: False)
    monkeypatch.setattr(
        db,
        "get_entries_for_folder",
        lambda folder: DirectoryEntries(["abc", "def"], ["foo", "bar"]),
    )

    assert not library.remove_directory("/test"), "Should fail if files not removed"
    out = capsys.readouterr()
    assert "Removing files...Failures" in out.out, "File removal failure message prints"

    monkeypatch.setattr(library, "remove_file", lambda file_path: True)
    monkeypatch.setattr(db, "remove_folder", lambda folder_path: False)

    assert not library.remove_directory("/test"), "Should fail if folders not removed"
    out = capsys.readouterr()
    assert "Removing files...Complete" in out.out, "File removal success prints"
    assert (
        "Removing folders...Failures" in out.out
    ), "Folder removal failure message prints"

    monkeypatch.setattr(db, "remove_folder", lambda folder_path: True)

    assert library.remove_directory("/test"), "Should succeed if all removed"
    out = capsys.readouterr()
    assert (
        "Removing files...Complete" in out.out
    ), "File removal success message prints (two)"
    assert (
        "Removing folders...Complete" in out.out
    ), "Folder removal success message prints"


def test_verify_file(monkeypatch, capsys):
    """
    .
    """
    device = Device()
    device.set("device", "/dev", "Device Serial", "ABCDEF", 1)

    file_obj = File()
    file_obj.set_properties("test", "path", "abc")
    file_obj.set_security("644", "owner", "group")
    file_obj.device_name = device.device_name
    file_obj.device = device
    monkeypatch.setattr(db, "get_files", lambda path: [file_obj])
    monkeypatch.setattr(
        utility,
        "checksum_file",
        lambda file_path: "abc"
        if file_path == path.join(device.device_path, file_obj.file_name)
        else "def",
    )

    assert library.verify_file(
        file_obj.file_path, True
    ), "Device path verification works"
    assert not library.verify_file(
        file_obj.file_path, False
    ), "Local file path verification fails"

    out = capsys.readouterr()
    assert "Checksum mismatch" in out.out, "Device verifcation failed message printed"

    monkeypatch.setattr(db, "get_files", lambda path: [])
    assert not library.verify_file("/test", False), "Nonexistent file should fail"
    out = capsys.readouterr()
    assert "File record not in database" in out.out, "Missing file message prints"


def test_verify_folder(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(
        db,
        "get_entries_for_folder",
        lambda folder: DirectoryEntries(["/foo/test", "/foo/test2"], []),
    )

    monkeypatch.setattr(
        library, "verify_file", lambda file_path, for_restore: file_path == "/foo/test"
    )
    assert not library.verify_folder("/foo", True), "Partial verification fails"

    monkeypatch.setattr(library, "verify_file", lambda file_path, for_restore: True)
    assert library.verify_folder("/foo", True), "Folder verification succeeds"


def test_verify_all(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "get_files", lambda: ["/foo/test", "/foo/test2"])

    monkeypatch.setattr(
        library, "verify_file", lambda file_path, for_restore: file_path == "/foo/test"
    )
    assert not library.verify_all(False), "Partial verification fails"

    monkeypatch.setattr(library, "verify_file", lambda file_path, for_restore: True)
    assert library.verify_all(False), "Folder verification succeeds"


def test_update_file(monkeypatch, capsys):
    """
    .
    """
    # Test unregistered file, successfully
    monkeypatch.setattr(db, "get_files", lambda file_path: [])
    monkeypatch.setattr(library, "add_file", lambda file_path: True)
    assert library.update_file("/test"), "New file added via update successfully"
    # Fail this time
    monkeypatch.setattr(library, "add_file", lambda file_path: False)
    assert not library.update_file("/test"), "New file fails to add via update"
    out = capsys.readouterr()
    assert (
        "Failed to add file during update" in out.out
    ), "New file failure prints message"

    # Registered file has checksum match, so no need to update
    file_checksum = "abc123"
    file_path = "/foo/test"
    file_obj = File()
    file_obj.set_properties("/test", file_path, file_checksum)
    file_obj.set_security("644", "user", "group")
    monkeypatch.setattr(db, "get_files", lambda file_path: [file_obj])
    monkeypatch.setattr(utility, "checksum_file", lambda file_path: file_checksum)
    # Force these to fail, so if they are called the execution will fail
    monkeypatch.setattr(library, "remove_file", lambda file_path: False)
    monkeypatch.setattr(library, "add_file", lambda file_path: False)
    assert library.update_file("/test"), "Updating file with matching checksum succeeds"

    # Checksum mismatch cases work as expected - removal success/fail, add success/fail
    monkeypatch.setattr(utility, "checksum_file", lambda file_path: "mismatch")
    monkeypatch.setattr(library, "remove_file", lambda file_path: True)
    monkeypatch.setattr(library, "add_file", lambda file_path: True)
    assert library.update_file("/test"), "Updating file works"

    monkeypatch.setattr(library, "add_file", lambda file_path: False)
    assert not library.update_file("/test"), "Fails to add updated file"
    out = capsys.readouterr()
    assert (
        "Failed to add file during update" in out.out
    ), "Failure to add updated file prints message"

    monkeypatch.setattr(library, "remove_file", lambda file_path: False)
    assert not library.update_file("/test"), "Fails to remove updated file"
    out = capsys.readouterr()
    assert (
        "Failed to remove file, so cannot update" in out.out
    ), "Failure to remove updated file prints message"


def test_remove_missing_database_entries(monkeypatch):
    """
    .
    """
    entries = DirectoryEntries(["/test", "/test2"], ["/var", "/var2"])

    # Test everything exists
    monkeypatch.setattr(library, "remove_directory", lambda path: False)
    monkeypatch.setattr(library, "remove_file", lambda path: False)
    monkeypatch.setattr(path, "isdir", lambda path: True)
    monkeypatch.setattr(path, "isfile", lambda path: True)

    assert library.__remove_missing_database_entries(
        entries
    ), "Everything exists should pass"

    # Removing nothing should pass
    patch_input(monkeypatch, library, lambda prompt: "n")
    assert library.__remove_missing_database_entries(
        entries
    ), "Nothing being removed should pass"

    # Removing only folders should fail if removal fails, and succeed otherwise
    monkeypatch.setattr(path, "isdir", lambda path: False)
    patch_input(
        monkeypatch, library, lambda prompt: "REMOVE" if "folders" in prompt else "n"
    )
    assert not library.__remove_missing_database_entries(
        entries
    ), "Removing only folders should fail if not removed"
    monkeypatch.setattr(library, "remove_directory", lambda path: True)
    assert library.__remove_missing_database_entries(
        entries
    ), "Removing only folders should succeed"

    # Removing everything should fail
    monkeypatch.setattr(path, "isfile", lambda path: False)
    patch_input(
        monkeypatch, library, lambda prompt: "REMOVE" if "folders" in prompt else "YES"
    )
    assert not library.__remove_missing_database_entries(
        entries
    ), "Removing everything should fail if file fails"
    monkeypatch.setattr(library, "remove_file", lambda path: True)
    assert library.__remove_missing_database_entries(
        entries
    ), "Removing everything should succeed"

    # Removing only files should fail if removal fails
    monkeypatch.setattr(path, "isdir", lambda path: True)
    monkeypatch.setattr(library, "remove_file", lambda path: False)
    patch_input(
        monkeypatch, library, lambda prompt: "n" if "folders" in prompt else "YES"
    )
    assert not library.__remove_missing_database_entries(
        entries
    ), "Removing only files should fail if not removed"
    monkeypatch.setattr(library, "remove_file", lambda path: True)
    assert library.__remove_missing_database_entries(
        entries
    ), "Removing only files should succeed"


def test_update_folder(monkeypatch, capsys):
    """
    .
    """
    folder_entries = DirectoryEntries(["bar"], [])
    both_entries = DirectoryEntries(["foo"], ["bar"])

    # First, test files only
    monkeypatch.setattr(db, "get_entries_for_folder", lambda folder: folder_entries)
    monkeypatch.setattr(
        utility, "list_entries_in_directory", lambda folder: folder_entries
    )

    # If removing missing entries fails, should fail
    monkeypatch.setattr(
        library, "__remove_missing_database_entries", lambda entries: False
    )
    monkeypatch.setattr(library, "update_file", lambda file_path: True)
    assert not library.update_folder(
        "/test"
    ), "Failure to remove missing entries should fail"

    # Results of update_file should match output of update folder
    monkeypatch.setattr(
        library, "__remove_missing_database_entries", lambda entries: True
    )
    monkeypatch.setattr(library, "update_file", lambda file_path: False)
    assert not library.update_folder("/test"), "Failure to update file should fail"
    monkeypatch.setattr(library, "update_file", lambda file_path: True)
    assert library.update_folder(
        "/test"
    ), "Updating folder if files update should succeed"

    # Now test both, but files is stubbed out so irrelevant
    monkeypatch.setattr(db, "get_entries_for_folder", lambda folder: both_entries)
    monkeypatch.setattr(
        utility, "list_entries_in_directory", lambda folder: both_entries
    )
    monkeypatch.setattr(db, "remove_folder", lambda folder_path: False)
    monkeypatch.setattr(db, "add_folder", lambda folder: False)

    # First, test equivalence for folder succeeds
    folder = Folder()
    folder_path, folder_permissions, folder_owner, folder_group = (
        "bar",
        "755",
        "user",
        "group",
    )
    folder.set(folder_path, folder_permissions, folder_owner, folder_group)

    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda folder_path: {
            "permissions": folder_permissions,
            "owner": folder_owner,
            "group": folder_group,
        },
    )
    monkeypatch.setattr(db, "get_folders", lambda folder_path: [folder])

    assert library.update_folder(folder_path), "Directory unchanged should succeed"

    # Check removal/adding of folder causes failures
    folder.folder_group = "other"
    assert not library.update_folder(folder_path), "Folder removal failure should error"
    out = capsys.readouterr()
    assert (
        "Failed to remove folder" in out.out
    ), "Folder removal failure should print message"

    monkeypatch.setattr(db, "remove_folder", lambda folder_path: True)
    monkeypatch.setattr(db, "add_folder", lambda folder_path: False)
    assert not library.update_folder(
        folder_path
    ), "Folder addition failure should error"
    out = capsys.readouterr()
    assert (
        "Failed to add folder" in out.out
    ), "Folder adding failure should print message"

    monkeypatch.setattr(db, "add_folder", lambda folder_path: True)
    assert library.update_folder(folder_path), "Folder updating should succeed"


def test_move_file_local(monkeypatch, capsys):
    """
    .
    """
    # Test error cases
    monkeypatch.setattr(
        db, "update_file_path", lambda current, new: DatabaseError.NONEXISTENT_FILE
    )
    assert not library.move_file_local(
        "/test/foo", "/test2"
    ), "Un backed-up file should fail"
    out = capsys.readouterr()
    assert "File path not backed up" in out.out, "Un backed-up file message prints"

    # This ensures that it accepts a directory as output, as well as a specific file
    monkeypatch.setattr(
        db,
        "update_file_path",
        lambda current, new: DatabaseError.SUCCESS
        if new == "/test2/foo"
        else DatabaseError.FILE_EXISTS,
    )
    assert not library.move_file_local(
        "/test/foo", "/failure"
    ), "Backed up to duplicate file should fail"
    out = capsys.readouterr()
    assert (
        "File already backed up at new location" in out.out
    ), "Backed up to duplicate file message prints"

    # Success cases
    monkeypatch.setattr(path, "isdir", lambda directory: True)
    assert library.move_file_local(
        "/test/foo", "/test2"
    ), "Change to backed up file should work with directory destination"
    monkeypatch.setattr(path, "isdir", lambda directory: False)
    assert library.move_file_local(
        "/test/foo", "/test2/foo"
    ), "Change to backed up file should work with file destination"


def test_move_directory_local(monkeypatch, capsys):
    """
    .
    """
    monkeypatch.setattr(
        db,
        "get_entries_for_folder",
        lambda folder: DirectoryEntries(["/test/foo"], ["/test/foo"]),
    )
    # Test error cases
    monkeypatch.setattr(library, "move_file_local", lambda current, new: True)
    monkeypatch.setattr(
        db, "update_folder_path", lambda current, new: DatabaseError.NONEXISTENT_FOLDER
    )
    assert not library.move_directory_local(
        "/test/foo", "/test2"
    ), "Un backed-up folder should fail"
    out = capsys.readouterr()
    assert (
        "Specified folder not backed up" in out.out
    ), "Un backed-up folder message prints"

    # This ensures that it accepts a directory as output, as well as a specific folder
    monkeypatch.setattr(
        db,
        "update_folder_path",
        lambda current, new: DatabaseError.SUCCESS
        if new == "/test2/foo"
        else DatabaseError.FOLDER_EXISTS,
    )
    assert not library.move_directory_local(
        "/test/foo", "/failure"
    ), "Backed up to duplicate folder should fail"
    out = capsys.readouterr()
    assert (
        "Folder already backed up at path" in out.out
    ), "Backed up to duplicate folder message prints"

    # Success cases
    monkeypatch.setattr(path, "isdir", lambda directory: True)
    assert library.move_directory_local(
        "/test/foo", "/test2"
    ), "Change to backed up folder should work with directory destination"

    # If file, don't back up
    monkeypatch.setattr(path, "isdir", lambda directory: False)
    monkeypatch.setattr(path, "isfile", lambda directory: True)
    assert not library.move_directory_local(
        "/test/foo", "/test2/foo"
    ), "Folder back up to file location should fail"
    out = capsys.readouterr()
    assert (
        "Cannot move folder over existing file"
    ), "Folder back up to file message prints"

    # If file fails, should fail move
    monkeypatch.setattr(library, "move_file_local", lambda current, new: False)
    monkeypatch.setattr(path, "isfile", lambda directory: False)
    assert not library.move_directory_local(
        "/test/foo", "/test2/foo"
    ), "File move failure should fail"


def test_move_file_device(monkeypatch, capsys):
    """
    .
    """
    dev1 = __make_temp_directory()
    dev2 = __make_temp_directory()

    origin_file, origin_checksum = __make_temp_file()
    origin_data = open(origin_file, "rb").read()
    backup_file, backup_checksum = __make_temp_file(directory=dev1, data=origin_data)
    assert (
        origin_checksum == backup_checksum
    ), "Origin and backup file should be identical"

    monkeypatch.setattr(utility, "get_file_size", lambda path: 1024)
    monkeypatch.setattr(utility, "get_device_space", lambda file_path: 0)
    assert not library.move_file_device(
        origin_file, dev2
    ), "Insufficient space should fail"
    out = capsys.readouterr()
    assert (
        "Device selected has insufficient space" in out.out
    ), "Insufficient space message prints"

    monkeypatch.setattr(utility, "get_device_space", lambda file_path: 100000)
    monkeypatch.setattr(db, "get_files", lambda file_path: [])
    assert not library.move_file_device(
        origin_file, dev2
    ), "Non-backed up file should fail"
    out = capsys.readouterr()
    assert (
        "Selected path does not exist in back up" in out.out
    ), "Non-backed up file message prints"

    file_obj = File()
    file_obj.set_properties(path.basename(backup_file), origin_file, origin_checksum)
    file_obj.set_security("644", "test", "test")
    device1 = Device()
    device1.set("dev1", dev1, "Device Serial", "ABC123", 1)
    device2 = Device()
    device2.set("dev2", dev2, "Device Serial", "ABC123", 1)
    file_obj.device = device1
    monkeypatch.setattr(db, "get_files", lambda file_path: [file_obj])
    monkeypatch.setattr(path, "ismount", lambda mount_path: False)
    assert not library.move_file_device(origin_file, dev2), "Missing mount should fail"
    out = capsys.readouterr()
    assert (
        "Device for backed-up file is not attached" in out.out
    ), "Missing mount message prints"

    monkeypatch.setattr(path, "ismount", lambda mount_path: True)
    isfile_func = path.isfile
    monkeypatch.setattr(path, "isfile", lambda file_path: False)
    assert not library.move_file_device(
        origin_file, dev2
    ), "Missing backup file should fail"
    out = capsys.readouterr()
    assert (
        "Cannot find back up of file" in out.out
    ), "Missing backup file message prints"

    monkeypatch.setattr(
        db, "update_file_device", lambda file_path, device: DatabaseError.SUCCESS
    )

    checksum_func = utility.checksum_file
    monkeypatch.setattr(utility, "checksum_file", lambda file_path: "wrong")
    monkeypatch.setattr(path, "isfile", isfile_func)
    assert not library.move_file_device(
        origin_file, dev2
    ), "Invalid checksum verification fails"
    out = capsys.readouterr()
    assert (
        "Checksum verification mismatch" in out.out
    ), "Invalid checksum verification message prints"

    moved_path = path.join(dev2, path.basename(backup_file))
    assert path.isfile(
        backup_file
    ), "Original backup file NOT deleted after checksum mismatch"
    assert not path.isfile(moved_path), "File deleted after checksum mismatch"

    monkeypatch.setattr(utility, "checksum_file", checksum_func)
    monkeypatch.setattr(db, "update_file_device", lambda file_path, device: False)
    assert not library.move_file_device(
        origin_file, dev2
    ), "Fail to update file device in database fails"
    out = capsys.readouterr()
    assert (
        "Failed to update device for file in database" in out.out
    ), "Update file device in DB message prints"
    assert path.isfile(
        backup_file
    ), "Original backup file NOT deleted after device update failure"
    assert not path.isfile(
        moved_path
    ), "File deleted after checksum mismatch after device update filure"

    monkeypatch.setattr(db, "update_file_device", lambda file_path, device: True)
    assert library.move_file_device(origin_file, dev2), "File move works"
    assert not path.isfile(backup_file), "Original backup file deleted after move"
    assert path.isfile(moved_path), "New backup file exists after move"
    assert (
        utility.checksum_file(moved_path) == origin_checksum
    ), "Checksum still matches"


def test_move_directory_device(monkeypatch, capsys):
    """
    .
    """
    monkeypatch.setattr(
        db,
        "get_entries_for_folder",
        lambda folder: DirectoryEntries(["abc", "def"], ["ghi"]),
    )
    monkeypatch.setattr(utility, "sum_file_size", lambda files: 1)
    monkeypatch.setattr(utility, "get_device_space", lambda device_path: 0)

    assert not library.move_directory_device(
        "/test", "/dev"
    ), "Insufficient device space fails"
    out = capsys.readouterr()
    assert (
        "Selected device cannot fit all the requested files" in out.out
    ), "Insufficient device space message prints"

    monkeypatch.setattr(utility, "get_device_space", lambda device_path: 10)
    monkeypatch.setattr(
        library, "move_file_device", lambda file_path, device: file_path == "abc"
    )

    assert not library.move_directory_device(
        "/test", "/dev"
    ), "Partial failures should fail"

    monkeypatch.setattr(library, "move_file_device", lambda file_path, device: True)
    assert library.move_directory_device("/test", "/dev"), "All success should succeed"


def test_restore_file(monkeypatch, capsys):
    """
    .
    """
    original_file, original_checksum = __make_temp_file()
    dev_folder = __make_temp_directory()

    device = Device()
    device.set("device", dev_folder, "Device Serial", "ABCDEF", 1)

    shutil.copyfile(original_file, path.join(dev_folder, path.basename(original_file)))

    assert library.restore_file(
        original_file
    ), "Restore succeeds if file already exists"
    out = capsys.readouterr()
    assert (
        "Path to restore already exists" in out.out
    ), "File already exists message prints"
    remove(original_file)

    monkeypatch.setattr(library, "verify_file", lambda file_path, for_restore: False)
    assert not library.restore_file(
        original_file
    ), "Restore fails if back up of file has invalid checksum"
    out = capsys.readouterr()
    assert (
        "Backed-up file has mismatched checksum" in out.out
    ), "Invalid back-up checksum message prints"

    monkeypatch.setattr(library, "verify_file", lambda file_path, for_restore: True)
    monkeypatch.setattr(db, "get_files", lambda file_path: [])
    assert not library.restore_file(
        original_file
    ), "Restore fails if file not backed up"
    out = capsys.readouterr()
    assert (
        "Requested path was not backed up" in out.out
    ), "Not backed-up file message prints"

    file_obj = File()
    file_obj.set_properties(
        path.basename(original_file), original_file, original_checksum
    )
    file_obj.set_security(
        "600", pwd.getpwuid(getuid()).pw_name, grp.getgrgid(getegid()).gr_name
    )
    file_obj.device = device

    monkeypatch.setattr(db, "get_files", lambda file_path: [file_obj])
    checksum_func = utility.checksum_file
    monkeypatch.setattr(utility, "checksum_file", lambda file_path: "bad-checksum")

    assert not library.restore_file(
        original_file
    ), "Checksum verification after copy fails"
    out = capsys.readouterr()
    assert (
        "Restored file has mismatched checksum" in out.out
    ), "Checksum verification after copy prints message"
    assert not path.isfile(
        original_file
    ), "Restored file should be deleted after checksum failure"

    monkeypatch.setattr(utility, "checksum_file", checksum_func)
    security_func = utility.get_file_security
    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda file_path: {"permissions": "bad", "owner": "wrong", "group": "wrong"},
    )
    assert not library.restore_file(
        original_file
    ), "Fails permission verification after copy files"
    out = capsys.readouterr()
    assert (
        "Failed to set file permissions/owner, but able to remove file" in out.out
    ), "Permission verification after copy prints message"
    assert not path.isfile(
        original_file
    ), "Restored file should be deleted after permission set failure"

    def throw_error(file_path):
        """
        Throws an error
        """
        raise PermissionError()

    remove_func = os.remove
    monkeypatch.setattr(os, "remove", throw_error)
    assert not library.restore_file(
        original_file
    ), "Fails permission verification after copy files"
    out = capsys.readouterr()
    assert (
        "Failed to set file permissions/owner, manual removal required" in out.out
    ), "Permission verification after copy prints message, cannot remove file"
    assert path.isfile(
        original_file
    ), "Restored file should NOT be deleted after permission set failure"

    monkeypatch.setattr(utility, "get_file_security", security_func)
    monkeypatch.setattr(os, "remove", remove_func)
    os.remove(original_file)

    assert library.restore_file(original_file), "Successful file restoration"
    assert path.isfile(original_file), "File exists at original location"
    assert original_checksum == utility.checksum_file(
        original_file
    ), "Restored file matches original checksum"


def test_restore_folder(monkeypatch, capsys):
    """
    .
    """
    monkeypatch.setattr(
        db, "get_entries_for_folder", lambda folder: DirectoryEntries([], [])
    )
    assert not library.restore_folder("/test"), "No returned entries should fail"
    out = capsys.readouterr()
    assert "Folder not backed up" in out.out, "No entries returned message printed"

    folder1 = __make_temp_directory()
    folder2 = __make_temp_directory(folder1)
    # Also removes parent directory, since it is empty
    os.removedirs(folder2)

    entries = DirectoryEntries(["/test", "/foo"], [folder1, folder2])
    monkeypatch.setattr(db, "get_entries_for_folder", lambda folder: entries)

    def throw_error(file_path, exist_ok):
        """
        Throws a permission error
        """
        raise PermissionError

    makedirs_func = os.makedirs
    monkeypatch.setattr(os, "makedirs", throw_error)
    assert not library.restore_folder(folder1), "Should fail due to permissions"
    out = capsys.readouterr()
    assert "Failed to create folder" in out.out, "Permission failure message prints"
    assert not path.isdir(folder1), "Folders should not be created yet"

    monkeypatch.setattr(os, "makedirs", makedirs_func)
    monkeypatch.setattr(library, "restore_file", lambda file_path: False)
    assert not library.restore_folder(
        folder1
    ), "Should fail due to file restoration failure"
    assert path.isdir(folder1), "Folder one still created"
    assert path.isdir(folder2), "Folder two still created"
    # Also removes parent directory
    os.removedirs(folder2)

    user_name = pwd.getpwuid(getuid()).pw_name
    group_name = grp.getgrgid(getegid()).gr_name
    folder = Folder()
    folder.set("unnecessary", "700", user_name, group_name)
    monkeypatch.setattr(db, "get_folders", lambda folder_path: [folder])
    monkeypatch.setattr(library, "restore_file", lambda file_path: True)
    security_func = utility.get_file_security
    monkeypatch.setattr(
        utility,
        "get_file_security",
        lambda folder_path: {"permissions": "bad", "owner": "wrong", "group": "wrong"},
    )
    assert not library.restore_folder(folder1), "Should fail due to permission mismatch"
    out = capsys.readouterr()
    assert (
        "Failed to set folder security options for" in out.out
    ), "Permission mismatch message prints"
    assert path.isdir(folder1), "Folder one still created after permission mismatch"
    assert path.isdir(folder2), "Folder two still created after permission mismatch"

    # Also removes parent directory
    os.removedirs(folder2)
    assert not path.isdir(folder1), "Verify parent directory removed"

    monkeypatch.setattr(utility, "get_file_security", security_func)
    assert library.restore_folder(folder1), "Folder restoration should succeed"
    assert path.isdir(folder1), "Folder one created"
    assert path.isdir(folder2), "Folder two created"
    assert (
        utility.get_file_security(folder1)["permissions"] == "700"
    ), "Folder one permissions set"
    assert (
        utility.get_file_security(folder2)["permissions"] == "700"
    ), "Folder two permissions set"


def test_get_unique_folders(monkeypatch):
    """
    .
    """
    folder1 = Folder()
    folder1.folder_path = "/foo"
    folder2 = Folder()
    folder2.folder_path = "/foo/test"
    folder3 = Folder()
    folder3.folder_path = "/bar"
    folder4 = Folder()
    folder4.folder_path = "/bar/baz/ipsum"
    folder5 = Folder()
    folder5.folder_path = "/f"

    monkeypatch.setattr(
        db, "get_folders", lambda: [folder1, folder2, folder3, folder4, folder5]
    )
    assert library.__get_unique_folders() == [
        "/foo",
        "/bar",
        "/f",
    ], "Reduced folder set returned"

    root_folder = Folder()
    root_folder.folder_path = "/"
    monkeypatch.setattr(
        db,
        "get_folders",
        lambda: [folder1, folder2, folder3, folder4, folder5, root_folder],
    )
    assert library.__get_unique_folders() == ["/"], "Root returns only itself"


def test_get_external_files(monkeypatch):
    """
    .
    """
    file1 = File()
    file1.file_path = "/foo/test"
    file2 = File()
    file2.file_path = "/foo/bar/baz"

    file3 = File()
    file3.file_path = "/home.txt"

    monkeypatch.setattr(library, "__get_unique_folders", lambda: ["/foo", "/home"])
    monkeypatch.setattr(db, "get_files", lambda: [file1, file2, file3])
    assert library.__get_files_outside_directories() == ["/home.txt"], "One returned"

    monkeypatch.setattr(library, "__get_unique_folders", lambda: ["/foo/bar", "/home"])
    assert library.__get_files_outside_directories() == [
        "/foo/test",
        "/home.txt",
    ], "Two returned"

    monkeypatch.setattr(
        library, "__get_unique_folders", lambda: ["/foo/bar", "/home", "/"]
    )
    assert library.__get_files_outside_directories() == [], "Root returns no files"


def test_restore_all(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(library, "__get_unique_folders", lambda: ["/foo", "/bar"])
    monkeypatch.setattr(
        library, "__get_files_outside_directories", lambda: ["/ipsum", "/lorem"]
    )

    monkeypatch.setattr(library, "restore_folder", lambda folder_path: False)
    monkeypatch.setattr(library, "restore_file", lambda file_path: True)
    assert not library.restore_all(), "Folder restoration failure, fails"

    monkeypatch.setattr(library, "restore_folder", lambda folder_path: True)
    monkeypatch.setattr(library, "restore_file", lambda file_path: False)
    assert not library.restore_all(), "File restoration failure, fails"

    monkeypatch.setattr(library, "restore_folder", lambda folder_path: True)
    monkeypatch.setattr(library, "restore_file", lambda file_path: True)
    assert library.restore_all(), "Success case"
