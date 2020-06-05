"""
Tests for the database files
"""
from os import remove
from os.path import exists

from logical_backup.db import initialize_database, SQLiteCursor, DEV_FILE


def test_initialization():
    """
    Test database initialization
    """
    if exists(DEV_FILE):
        remove(DEV_FILE)

    with SQLiteCursor(True) as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        assert len(tables) == 0, "New testing database already has tables"

        initialize_database(True)

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
