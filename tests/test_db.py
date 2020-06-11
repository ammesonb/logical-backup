"""
Tests for the database files
"""
from os import remove
from os.path import exists
from pytest import fixture

from logical_backup.db import (
    initialize_database,
    SQLiteCursor,
    DEV_FILE,
    get_devices,
    add_device,
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

    assert get_devices() == [], "No devices by default"

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

    assert get_devices() == [
        {
            "device_name": "Test-Device",
            "device_path": "/mnt",
            "identifier_name": "Device Serial",
            "device_identifier": "ABCDEF",
        }
    ]


def test_add_device():
    """
    Test function for adding a device
    """
    initialize_database()

    result = add_device("test1", "/test1", "Not real", "12345")
    assert (
        result == DatabaseError.INVALID_IDENTIFIER_TYPE
    ), "Invalid identifier shoud fail"

    result = add_device("test1", "/test1", "Device Serial", "12345")
    assert result == DatabaseError.SUCCESS, "Valid identifier should work"

    result = add_device("test1", "/test", "Device Serial", "12346")
    assert result == DatabaseError.DEVICE_NAME_EXISTS, "Cannot reuse name"

    result = add_device("test2", "/test1", "Device Serial", "12346")
    assert result == DatabaseError.DEVICE_PATH_EXISTS, "Cannot reuse mount point"

    result = add_device("test2", "/test2", "Device Serial", "12345")
    assert result == DatabaseError.DEVICE_IDENTIFIER_EXISTS, "Cannot reuse identifier"

    result = add_device("test2", "/test2", "Device Serial", "12346")
    assert result == DatabaseError.SUCCESS, "Second device added by serial"

    result = add_device(
        "test3", "/test3", "System UUID", "664ea743-3aa5-4aec-bafe-feb62c39b4c4"
    )
    assert result == DatabaseError.SUCCESS, "Third device added by UUID"

    result = add_device("test4", "/test4", "System UUID", "External HDD")
    assert result == DatabaseError.SUCCESS, "Fourth device added manually"

    devices = get_devices()
    device_identifiers = [device["device_identifier"] for device in devices]
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
