"""
Tests for the database files
"""
from os import remove
from os.path import exists
from pytest import fixture

from logical_backup.db import initialize_database, SQLiteCursor, DEV_FILE, get_devices

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
        for name in ["System UUID", "Device Serial"]:
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
