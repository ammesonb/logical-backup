"""
Test custom SQLite cursor functionality
"""
import sqlite3

from logical_backup.db import SQLiteCursor

# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing


def test_creation():
    """
    .
    """
    sqlite_cursor = SQLiteCursor()
    assert sqlite_cursor.connection is None, "No connection set yet"
    assert sqlite_cursor.cursor is None, "No cursor yet"


def test_enter_exit():
    """
    .
    """
    with SQLiteCursor() as cursor:
        assert isinstance(cursor.connection, sqlite3.Connection), "Connection is set"
        assert isinstance(cursor.cursor, sqlite3.Cursor), "Cursor is set"
