"""
Database interactions for the utility
"""

from enum import Enum
import sqlite3

from logical_backup.utility import is_test

DB_FILE = "files.db"
DEV_FILE = "files.db.test"


class DatabaseError(Enum):
    """
    Database error codes
    """

    UNKNOWN_ERROR = -1
    SUCCESS = 0
    DEVICE_NAME_EXISTS = 1
    DEVICE_PATH_EXISTS = 2
    DEVICE_IDENTIFIER_EXISTS = 3
    INVALID_IDENTIFIER_TYPE = 4


class SQLiteCursor(sqlite3.Cursor):
    """
    A wrapper around the SQLite cursor
    """

    def __init__(self, commit_on_close: bool = True):
        """
        Initialize the object

        Parameters
        ----------
        commit_on_close : bool
            Whether to automatically commit on close
        """
        super()
        self.__connection = None
        self.__commit_on_close = commit_on_close
        self.__db_file = DEV_FILE if is_test() else DB_FILE

    def __enter__(self):
        self.__connection = sqlite3.connect(self.__db_file)
        return self.__connection.cursor()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.__commit_on_close:
            self.__connection.commit()

        self.__connection.close()


def initialize_database():
    """
    Initialize the database for use
    """
    with SQLiteCursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tblplDeviceIdentifier ("
            "  IdentifierID   INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  IdentifierName TEXT NOT NULL UNIQUE"
            ");"
        )

        cursor.execute(
            "INSERT INTO tblplDeviceIdentifier (IdentifierName)"
            "SELECT Name "
            "FROM ("
            "  SELECT 'System UUID' AS Name"
            "  UNION"
            "  SELECT 'Device Serial'"
            "  UNION"
            "  SELECT 'User Specified'"
            " ) t "
            "WHERE NOT EXISTS ("
            "  SELECT *"
            "  FROM   tblplDeviceIdentifier"
            ")"
            "ORDER BY t.Name;"
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tblDevice ("
            "  DeviceID           INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  DeviceName         TEXT NOT NULL UNIQUE,"
            "  DeviceIdentifierID INT  NOT NULL,"
            "  DeviceIdentifier   TEXT NOT NULL UNIQUE,"
            "  DevicePath         TEXT NOT NULL UNIQUE,"
            "  FOREIGN KEY (DeviceIdentifierID)"
            "    REFERENCES tblplDeviceIdentifier (IdentifierID)"
            ");"
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tblFile ("
            "  FileID          INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  FileName        TEXT NOT NULL,"
            "  FilePath        TEXT NOT NULL,"
            "  FilePermissions TEXT NOT NULL,"
            "  FileOwnerName   TEXT NOT NULL,"
            "  FileGroupName   TEXT NOT NULL,"
            "  FileChecksum    TEXT NOT NULL,"
            "  FileDeviceID    INT  NOT NULL,"
            "  FOREIGN KEY (FileDeviceID) REFERENCES tblDevice (DeviceID)"
            ");"
        )


def get_devices() -> list:
    """
    Return configured devices
    """
    with SQLiteCursor() as cursor:
        cursor.execute(
            "SELECT     d.DeviceName, "
            "           d.DevicePath, "
            "           i.IdentifierName, "
            "           d.DeviceIdentifier "
            "FROM       tblDevice d "
            "INNER JOIN tblplDeviceIdentifier i "
            "ON         i.IdentifierID = d.DeviceIdentifierID"
        )
        rows = cursor.fetchall()
        devices = []
        for row in rows:
            columns = [
                "device_name",
                "device_path",
                "identifier_name",
                "device_identifier",
            ]
            device = {}
            index = 0
            for column in columns:
                device.update({column: row[index]})
                index += 1
            devices.append(device)

        return devices


def add_device(name: str, path: str, identifier_name: str, identifier: str) -> int:
    """
    Add a device

    Parameters
    ----------
    name : string
        The name of the device
    path: string
        The mount path of the device
    identifier_name : string
        Friendly description of the identifier - must be in picklist
    identifier : string
        The identifier for the device

    Returns
    -------
    integer
        True if added, False if it already exists
    """
    with SQLiteCursor() as cursor:
        result = DatabaseError.UNKNOWN_ERROR
        try:
            cursor.execute(
                "INSERT INTO tblDevice ("
                "  DeviceName, "
                "  DevicePath, "
                "  DeviceIdentifierID, "
                "  DeviceIdentifier"
                ") "
                "SELECT ?, "
                "       ?, "
                "       i.IdentifierID, "
                "       ? "
                "FROM   tblplDeviceIdentifier i "
                "WHERE  i.IdentifierName = ?",
                (name, path, identifier, identifier_name),
            )
            result = (
                DatabaseError.SUCCESS
                if cursor.rowcount > 0
                else DatabaseError.INVALID_IDENTIFIER_TYPE
            )
        except sqlite3.IntegrityError as error:
            if "DevicePath" in error.args[0]:
                result = DatabaseError.DEVICE_PATH_EXISTS
            elif "DeviceName" in error.args[0]:
                result = DatabaseError.DEVICE_NAME_EXISTS
            elif "DeviceIdentifier" in error.args[0]:
                result = DatabaseError.DEVICE_IDENTIFIER_EXISTS
            else:
                result = DatabaseError.UNKNOWN_ERROR

        return result
