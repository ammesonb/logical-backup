"""
Tests for the database files
"""
from os import remove
from os.path import exists, join
import sqlite3

from pytest import fixture

from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.objects.folder import Folder
from logical_backup import db

from logical_backup.db import (
    initialize_database,
    SQLiteCursor,
    DEV_FILE,
    DatabaseError,
)

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing

from tests.test_utility import __compare_lists


@fixture(autouse=True)
def auto_clear_db():
    """
    Remove the dev database file if needed, and recreate it
    """
    if exists(DEV_FILE):
        remove(DEV_FILE)

    yield "Running test"

    if exists(DEV_FILE):
        remove(DEV_FILE)


def test_initialization():
    """
    Test database initialization
    """
    with SQLiteCursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        assert len(tables) == 0, "New testing database already has tables"

        initialize_database()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        tables = [table[0] for table in tables]
        for table in ["tblplDeviceIdentifier", "tblDevice", "tblFile"]:
            assert table in tables, "Missing " + table

        cursor.execute("SELECT IdentifierName FROM tblplDeviceIdentifier")
        names = cursor.fetchall()
        names = [name[0] for name in names]
        for name in ["System UUID", "Device Serial", "User Specified"]:
            assert name in names, "Missing device identifier type: " + name


def test_database_errors():
    """
    .
    """
    assert DatabaseError.SUCCESS, "Success should be truthy"
    assert not DatabaseError.UNKNOWN_ERROR, "Unknown error should be falsy"
    assert not DatabaseError.DEVICE_NAME_EXISTS, "Device name error should be falsy"


def test_get_devices():
    """
    Test device retrieval
    """
    initialize_database()

    assert db.get_devices() == [], "No devices by default"

    device = Device()
    device.set("Test-Device", "/mnt", "Device Serial", "ABCDEF", 1)
    db.add_device(device)
    assert db.get_devices() == [device]


def test_add_device(monkeypatch):
    """
    Test function for adding a device
    """
    initialize_database()

    device = Device()
    device.set("test1", "/test1", "Not real", "12345")
    result = db.add_device(device)
    assert (
        result == DatabaseError.INVALID_IDENTIFIER_TYPE
    ), "Invalid identifier shoud fail"

    device.set("test1", "/test1", "Device Serial", "12345")
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Valid identifier should work"

    device.set("test1", "/test", "Device Serial", "12346")
    result = db.add_device(device)
    assert result == DatabaseError.DEVICE_NAME_EXISTS, "Cannot reuse name"

    device.set("test2", "/test1", "Device Serial", "12346")
    result = db.add_device(device)
    assert result == DatabaseError.DEVICE_PATH_EXISTS, "Cannot reuse mount point"

    device.set("test2", "/test2", "Device Serial", "12345")
    result = db.add_device(device)
    assert result == DatabaseError.DEVICE_IDENTIFIER_EXISTS, "Cannot reuse identifier"

    device.set("test2", "/test2", "Device Serial", "12346")
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Second device added by serial"

    device.set("test3", "/test3", "System UUID", "664ea743-3aa5-4aec-bafe-feb62c39b4c4")
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Third device added by UUID"

    # Check unknown failure by falsely calling an exception
    exec_func = db.SQLiteCursor.execute

    def raise_integrity_exception(message: str) -> None:
        """
        Raises an exception
        """
        raise sqlite3.IntegrityError(message)

    monkeypatch.setattr(
        db.SQLiteCursor,
        "execute",
        lambda self, query, args=None: raise_integrity_exception("something else"),
    )
    device.set("test4", "/test4", "System UUID", "External HDD", 2)
    result = db.add_device(device)
    assert (
        result == DatabaseError.UNKNOWN_ERROR
    ), "Fourth device fails due to unknown error"

    # Test successful adding of fourth device
    monkeypatch.setattr(db.SQLiteCursor, "execute", exec_func)
    device.set("test4", "/test4", "System UUID", "External HDD", 2)
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Fourth device added manually"

    devices = db.get_devices()
    device_identifiers = [device.identifier for device in devices]
    assert len(devices) == 4, "All devices retrieved from the database"
    # pylint: disable=bad-continuation
    for identifier in [
        "12345",
        "12346",
        "664ea743-3aa5-4aec-bafe-feb62c39b4c4",
        "External HDD",
    ]:
        assert (
            identifier in device_identifiers
        ), "Identifier {0} should be in the database".format(identifier)

    assert db.get_devices("test4") == [device], "Device 4 retrieved by name"


def test_add_and_check_file():
    """
    .
    """
    initialize_database()

    assert not db.file_exists("/test"), "File should not exist"

    file_obj = File()
    file_obj.set_properties("test", "/test", "not-real")
    file_obj.set_security("755", "root", "root")
    file_obj.device_name = "test"
    assert (
        db.add_file(file_obj) == DatabaseError.NONEXISTENT_DEVICE
    ), "Missing device causes file to not be added"

    device = Device()
    device.set("test", "/test", "Device Serial", "12345", 1)
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Insert of test device should succeed"

    assert (
        db.add_file(file_obj) == DatabaseError.SUCCESS
    ), "Insert of file should succeed"

    assert db.file_exists("/test"), "Added file should exist"

    db_files = db.get_files()
    assert db_files == [file_obj], "File should be in the DB"
    assert db_files[0].device == device, "Retrieved file's device matches"

    file_obj2 = File()
    file_obj2.set_properties("test", "/test", "not-real")
    file_obj2.set_security("755", "root", "root")
    file_obj2.device_name = "test"
    assert db.add_file(file_obj2) == DatabaseError.FILE_EXISTS, "Can't add file twice"

    file_obj2.file_path = "/test2"
    file_obj2.identifier = "not-real-2"
    assert db.add_file(file_obj2) == DatabaseError.SUCCESS, "Second file added"

    assert db.get_files() == [file_obj, file_obj2], "Two files returned from DB"

    assert db.get_files("/test2") == [file_obj2], "Second file returned with input"
    assert db.get_files("/test") == [file_obj], "First file returned with input"

    # Test for basic get/set on file device,
    # because it doesn't have anywhere else to live right now
    file_obj.device = device
    assert file_obj.device == device, "Device set on file should match"


def test_add_folder(monkeypatch):
    """
    .
    """
    initialize_database()

    assert db.get_folders() == [], "Initially should be empty"

    folder1 = Folder()
    folder1.set("/test", "755", "test", "test")
    assert db.add_folder(folder1), "First folder should add successfully"

    assert db.get_folders() == [folder1], "Single folder matches"

    folder2 = Folder()
    folder2.set("/test2", "700", "test2", "test2")
    assert db.add_folder(folder2), "Second folder should add successfully"

    assert db.get_folders() == [folder1, folder2], "Two folders match"

    assert db.get_folders(folder2.folder_path) == [
        folder2
    ], "Specific folder retrieval works"

    assert (
        db.add_folder(folder2) == DatabaseError.FOLDER_EXISTS
    ), "Should fail to add second folder twice"

    folder3 = Folder()
    folder3.set("/test3", "700", "test3", "test3")
    monkeypatch.setattr(SQLiteCursor, "rowcount", 0)
    assert (
        db.add_folder(folder3) == DatabaseError.UNKNOWN_ERROR
    ), "Unknown error is thrown if no rows added"


def test_remove_file():
    """
    .
    """
    initialize_database()

    assert not db.remove_file("/test"), "Deleting nonexistent file fails"

    device = Device()
    device.set("test", "/mnt", "Device Serial", "ABCDEF", 1)
    assert db.add_device(device), "Adding device should succeed"

    file_obj = File()
    file_obj.set_properties("test", "/test", "not-real")
    file_obj.set_security("755", "root", "root")
    file_obj.device_name = "test"
    assert db.add_file(file_obj), "Adding file to remove should succeed"
    file_obj.file_path = "/test2"
    file_obj.identifier = "not-real-2"
    assert db.add_file(file_obj), "Adding second file to remove should succeed"

    assert db.remove_file("/test"), "Deleting existing file succeeds"

    assert db.get_files() == [file_obj], "Second file should still be in the database"


def test_get_entries_for_folder():
    """
    .
    """
    initialize_database()

    set_file_security = lambda file_obj: file_obj.set_security("644", "test", "test")
    set_folder_details = lambda folder, path: folder.set(path, "644", "test", "test")

    test_path = "/test"
    test_sub_path = "bar"
    other_path = "/other"

    device = Device()
    device.set("test", "/mnt", "Device Serial", "ABCDEF", 1)
    assert db.add_device(device), "Device should be added successfully"

    file1 = File()
    set_file_security(file1)
    file1.set_properties("test", test_path + "foo", "abc")
    file2 = File()
    set_file_security(file2)
    file2.set_properties("test2", join(test_path, test_sub_path, "baz"), "def")
    file3 = File()
    set_file_security(file3)
    file3.set_properties("test3", join(other_path, "ipsum"), "ghi")

    for file_obj in [file1, file2, file3]:
        file_obj.device_name = "test"
        assert db.add_file(file_obj), "Files should be added successfully"

    folder1 = Folder()
    set_folder_details(folder1, test_path)
    folder2 = Folder()
    set_folder_details(folder2, join(test_path, test_sub_path))
    folder3 = Folder()
    set_folder_details(folder3, other_path)

    for folder_obj in [folder1, folder2, folder3]:
        assert db.add_folder(folder_obj), "Folders should be added successfully"

    entries = db.get_entries_for_folder(test_path)
    assert __compare_lists(
        entries.files, [file1.file_path, file2.file_path]
    ), "Files under directory should be returned"
    assert __compare_lists(
        entries.folders, [folder1.folder_path, folder2.folder_path]
    ), "Selected and subfolder should be returned"


def test_remove_folder():
    """
    .
    """
    initialize_database()

    folder1 = Folder()
    folder2 = Folder()

    folder1.set("/test/foo", "755", "test", "test")
    folder2.set("/bar", "755", "test", "test")

    assert db.add_folder(folder1), "Folder one should be added"
    assert db.add_folder(folder2), "Folder two should be added"

    assert __compare_lists(
        db.get_folders(), [folder1, folder2]
    ), "Folders should be retrieved"

    assert db.remove_folder(folder1.folder_path), "Folder one should be removed"
    assert (
        db.remove_folder(folder1.folder_path) == DatabaseError.NONEXISTENT_FOLDER
    ), "Cannot remove nonexistent folder"

    assert db.get_folders() == [folder2], "Folder two still in DB"
    assert db.remove_folder(folder2.folder_path), "Folder two should be removed"

    assert db.get_folders() == [], "No folders in DB"


def test_update_folder_path():
    """
    .
    """
    initialize_database()
    folder = Folder()
    folder.set("/test", "644", "owner", "group")
    folder2 = Folder()
    folder2.set("/test2", "644", "owner2", "group2")

    assert db.add_folder(folder), "Folder should be added"
    assert db.add_folder(folder2), "Second folder should be added"

    assert (
        db.update_folder_path("/test", "/test2") == DatabaseError.FOLDER_EXISTS
    ), "Integrity constraint should be violated"
    assert (
        db.update_folder_path("/foo", "/foo2") == DatabaseError.NONEXISTENT_FOLDER
    ), "Cannot update nonexistent folder"
    assert (
        db.update_folder_path("/test", "/mnt/device") == DatabaseError.SUCCESS
    ), "Folder update works"

    folder.folder_path = "/mnt/device"
    assert __compare_lists(
        [folder, folder2], db.get_folders()
    ), "Folder update persists"


def test_update_file_path():
    """
    .
    """
    initialize_database()
    device = Device()
    device.set("test device", "/mnt/device", "Device Serial", "ABCDEF123", 1)
    db.add_device(device)
    file_obj = File()
    file_obj.set_properties("/test", "/test", "abc123")
    file_obj.set_security("644", "owner", "group")
    file_obj.device_name = "test device"
    file_obj2 = File()
    file_obj2.set_properties("/test2", "/test2", "abc123")
    file_obj2.set_security("644", "owner2", "group2")
    file_obj2.device_name = "test device"

    assert db.add_file(file_obj), "File should be added"
    assert db.add_file(file_obj2), "Second file should be added"

    assert (
        db.update_file_path("/test", "/test2") == DatabaseError.FILE_EXISTS
    ), "Integrity constraint should be violated"
    assert (
        db.update_file_path("/foo", "/foo2") == DatabaseError.NONEXISTENT_FILE
    ), "Cannot update nonexistent file"
    assert (
        db.update_file_path("/test", "/mnt/device/test") == DatabaseError.SUCCESS
    ), "File update works"

    file_obj.file_path = "/mnt/device/test"
    assert __compare_lists(
        [file_obj, file_obj2], db.get_files()
    ), "File update persists"


def test_update_file_device():
    """
    .
    """
    initialize_database()
    device = Device()
    device.set("test", "/foo", "Device Serial", "foo", 1)
    assert db.add_device(device), "Device should be added successfully"
    device.set("test2", "/bar", "Device Serial", "bar", 1)
    assert db.add_device(device), "Second device should be added successfully"

    file_obj = File()
    file_obj.set_properties("test", "/test/foo", "abc123")
    file_obj.set_security("644", "test", "test")
    file_obj.device_name = "test"
    assert db.add_file(file_obj), "File should be added successfully"

    assert (
        db.update_file_device("/nonexistent", "/foo") == DatabaseError.NONEXISTENT_FILE
    ), "Nonexistent file returned"
    assert (
        db.update_file_device("/test/foo", "/foo2") == DatabaseError.NONEXISTENT_DEVICE
    ), "Nonexistent device returned"
    assert (
        db.update_file_device("/test/foo", "/bar") == DatabaseError.SUCCESS
    ), "File device updates"
