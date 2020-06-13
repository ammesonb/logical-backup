"""
Tests for the database files
"""
from os import remove
from os.path import exists
from pytest import fixture

from logical_backup.objects.device import Device
from logical_backup.objects.file import File
import logical_backup.db as db

from logical_backup.db import (
    initialize_database,
    SQLiteCursor,
    DEV_FILE,
    DatabaseError,
)

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing


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


def test_get_devices():
    """
    Test device retrieval
    """
    initialize_database()

    assert db.get_devices() == [], "No devices by default"

    with SQLiteCursor() as cursor:
        cursor.execute(
            "INSERT INTO tblDevice ("
            "  DeviceName, "
            "  DevicePath, "
            "  DeviceIdentifierID, "
            "  DeviceIdentifier"
            ")"
            "VALUES ("
            "  'Test-Device', "
            "  '/mnt', "
            "  1, "
            "  'ABCDEF'"
            ")"
        )

    device = Device()
    device.set("Test-Device", "/mnt", "Device Serial", "ABCDEF", 1)
    assert db.get_devices() == [device]


def test_add_device():
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

    device.set("test4", "/test4", "System UUID", "External HDD")
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


def test_check_file():
    """
    .
    """
    initialize_database()

    assert not db.file_exists("/test"), "File should not exist"

    device = Device()
    device.set("test", "/test", "Device Serial", "12345")
    result = db.add_device(device)
    assert result == DatabaseError.SUCCESS, "Insert of test device should succeed"

    file_obj = File()
    file_obj.set_properties("test", "/test", "not-real")
    file_obj.set_security("755", "root", "root")
    file_obj.device_name = "test"
    added = db.add_file(file_obj)
    assert added == DatabaseError.SUCCESS, "Insert of file should succeed"

    assert db.file_exists("/test"), "Added file should exist"
