"""
Database interactions for the utility
"""

from enum import Enum
from os.path import dirname, join
import sqlite3

from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.objects.folder import Folder


from logical_backup.utility import is_test, DirectoryEntries

DB_FILE = join(dirname(__file__), "../files.db")
print(DB_FILE)
DEV_FILE = join(dirname(__file__), "../files.db.test")


def __row_to_dict(row: list, column_names: list) -> dict:
    """
    Converts a row from the database to a dictionary

    Parameters
    ----------
    row : list
        Data to convert
    column_names : list
        Ordered list of column headers

    Returns
    -------
    dict
        Row data, as dictionary
    """
    row_dict = {}
    for column, data in zip(column_names, row):
        row_dict[column[0]] = data

    return row_dict


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
    NONEXISTENT_DEVICE = 5
    NONEXISTENT_FILE = 6
    NONEXISTENT_FOLDER = 7
    FILE_EXISTS = 8
    FOLDER_EXISTS = 9

    def __bool__(self):
        """
        .
        """
        return self == self.SUCCESS


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
        self.__cursor = None

    def __enter__(self):
        """
        .
        """
        self.__connection = sqlite3.connect(self.__db_file)
        self.__cursor = self.__connection.cursor()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        .
        """
        if self.__commit_on_close:
            self.__connection.commit()

        self.__connection.close()

    def execute(self, *args, **kwargs):
        """
        Wrapper for sqlite execute
        """
        return self.__cursor.execute(*args, **kwargs)

    def fetchone(self):
        """
        Wrapper for sqlite fetchone
        """
        return self.__cursor.fetchone()

    def fetchall(self):
        """
        Wrapper for sqlite fetchall
        """
        return self.__cursor.fetchall()

    @property
    def rowcount(self) -> int:
        """
        Wrapper for sqlite cursor rowcount
        """
        return self.__cursor.rowcount

    @property
    def description(self):
        """
        Wrapper for sqlite cursor description
        """
        return self.__cursor.description


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
            "  FilePath        TEXT NOT NULL UNIQUE,"
            "  FilePermissions TEXT NOT NULL,"
            "  FileOwnerName   TEXT NOT NULL,"
            "  FileGroupName   TEXT NOT NULL,"
            "  FileChecksum    TEXT NOT NULL,"
            "  FileDeviceID    INT  NOT NULL,"
            "  FOREIGN KEY (FileDeviceID) REFERENCES tblDevice (DeviceID)"
            ");"
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tblFolder ("
            "  FolderID          INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  FolderPath        TEXT NOT NULL UNIQUE,"
            "  FolderPermissions TEXT NOT NULL,"
            "  FolderOwnerName   TEXT NOT NULL,"
            "  FolderGroupName   TEXT NOT NULL"
            ");"
        )


def get_devices(device_name: str = None) -> list:
    """
    Return configured devices
    """
    with SQLiteCursor() as cursor:
        query = (
            "SELECT     d.DeviceName, "
            "           d.DevicePath, "
            "           i.IdentifierID, "
            "           i.IdentifierName, "
            "           d.DeviceIdentifier "
            "FROM       tblDevice d "
            "INNER JOIN tblplDeviceIdentifier i "
            "ON         i.IdentifierID = d.DeviceIdentifierID"
        )

        if device_name:
            query += " WHERE d.DeviceName = ?"
            cursor.execute(query, (device_name,))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        devices = []
        for row in rows:
            device = Device()
            device.set(row[0], row[1], row[3], row[4], row[2])
            devices.append(device)

        return devices


def add_device(device: Device) -> int:
    """
    Add a device

    Parameters
    ----------
    device : Device
        The device to add

    Returns
    -------
    integer
        True if added, False if it already exists
    """
    result = DatabaseError.UNKNOWN_ERROR

    try:
        with SQLiteCursor() as cursor:
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
                (
                    device.device_name,
                    device.device_path,
                    device.identifier,
                    device.identifier_type,
                ),
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


def file_exists(file_path: str) -> bool:
    """
    Check if a file already exists

    Parameters
    ----------
    file_path : str
        File path to check

    Returns
    -------
    bool
        True if file exists
    """
    with SQLiteCursor() as cursor:
        cursor.execute(
            "SELECT 1 " "FROM   tblFile " "WHERE  FilePath = ?", (file_path,)
        )
        result = cursor.fetchone()
        return bool(result)


def add_file(file_obj: File) -> DatabaseError:
    """
    Add a file
    """
    with SQLiteCursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO tblFile ("
                "  FileName, "
                "  FilePath, "
                "  FilePermissions, "
                "  FileOwnerName, "
                "  FileGroupName, "
                "  FileChecksum, "
                "  FileDeviceID "
                ")"
                "SELECT ?, "
                "       ?, "
                "       ?, "
                "       ?, "
                "       ?, "
                "       ?, "
                "       d.DeviceID "
                "FROM   tblDevice d "
                "WHERE  d.DeviceName = ?",
                (
                    file_obj.file_name,
                    file_obj.file_path,
                    file_obj.permissions,
                    file_obj.owner,
                    file_obj.group,
                    file_obj.checksum,
                    file_obj.device_name,
                ),
            )
            return (
                DatabaseError.SUCCESS
                if cursor.rowcount > 0
                else DatabaseError.NONEXISTENT_DEVICE
            )
        except sqlite3.IntegrityError:
            return DatabaseError.FILE_EXISTS


def get_files(path: str = None) -> list:
    """
    .
    """
    with SQLiteCursor() as cursor:
        query = (
            "SELECT     FileName, "
            "           FilePath, "
            "           FilePermissions, "
            "           FileOwnerName, "
            "           FileGroupName, "
            "           FileChecksum, "
            "           DeviceName, "
            "           DevicePath, "
            "           DeviceIdentifier, "
            "           IdentifierID, "
            "           IdentifierName "
            "FROM       tblFile f "
            "INNER JOIN tblDevice d "
            "ON         f.FileDeviceID = d.DeviceID "
            "INNER JOIN tblplDeviceIdentifier i "
            "ON         i.IdentifierID = d.DeviceIdentifierID"
        )

        if path:
            query += " WHERE f.FilePath = ?"
            cursor.execute(query, (path,))
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        files = []
        for result in results:
            row = __row_to_dict(result, cursor.description)
            device = Device()
            device.set(
                row["DeviceName"],
                row["DevicePath"],
                row["DeviceIdentifier"],
                row["IdentifierName"],
                row["IdentifierID"],
            )

            file_obj = File()
            file_obj.device = device
            file_obj.device_name = device.device_name
            file_obj.set_properties(
                row["FileName"], row["FilePath"], row["FileChecksum"]
            )
            file_obj.set_security(
                row["FilePermissions"], row["FileOwnerName"], row["FileGroupName"]
            )

            files.append(file_obj)

        return files


def remove_file(path: str) -> bool:
    """
    Removes a file

    Parameters
    ----------
    path : str
        Path to remove

    Returns
    -------
    bool
        True if removed, false if failed or doesn't exist
    """
    with SQLiteCursor() as cursor:
        cursor.execute("DELETE FROM tblFile WHERE FilePath = ? ", (path,))
        return (
            DatabaseError.SUCCESS
            if cursor.rowcount > 0
            else DatabaseError.NONEXISTENT_FILE
        )


def add_folder(folder: Folder) -> bool:
    """
    Adds a folder to the DB

    Parameters
    ----------
    folder : Folder
        Folder to add

    Returns
    -------
    bool
        True if added False otherwise
    """
    with SQLiteCursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tblFolder (
              FolderPath,
              FolderPermissions,
              FolderOwnerName,
              FolderGroupName
            )
            SELECT ?,
                   ?,
                   ?,
                   ?
            """,
            (
                folder.folder_path,
                folder.folder_permissions,
                folder.folder_owner,
                folder.folder_group,
            ),
        )

        return (
            DatabaseError.SUCCESS
            if cursor.rowcount > 0
            else DatabaseError.UNKNOWN_ERROR
        )
        # TODO: try/catch error handling


def get_folders(folder_path: str = None) -> list:
    """
    Gets folders from the DB

    Parameters
    ----------
    folder_path : str
        Optionally, folder path to look for

    Returns
    -------
    list
        of folders
    """
    with SQLiteCursor() as cursor:
        query = """
            SELECT FolderPath,
                   FolderPermissions,
                   FolderOwnerName,
                   FolderGroupName
            FROM   tblFolder
            """

        if folder_path:
            query += " WHERE FolderPath = ?"
            cursor.execute(query, (folder_path,))
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        folders = []
        for result in results:
            row = __row_to_dict(result, cursor.description)
            folder = Folder()
            folder.set(
                row["FolderPath"],
                row["FolderPermissions"],
                row["FolderOwnerName"],
                row["FolderGroupName"],
            )
            folders.append(folder)

        return folders


def get_entries_for_folder(folder_path: str) -> DirectoryEntries:
    """
    Gets the files and folders registered under a given path

    Parameters
    ----------
    folder_path : str
        Path to find stuff under

    Returns
    -------
    DirectoryEntries
        A list of files and folders in the DB that match
    """

    entries = DirectoryEntries([], [])
    with SQLiteCursor() as cursor:
        cursor.execute(
            """
            SELECT FolderPath
            FROM   tblFolder
            WHERE  FolderPath LIKE ? || '%'
            """,
            (folder_path,),
        )

        results = cursor.fetchall()
        for result in results:
            entries.folders.append(result[0])

        cursor.execute(
            """
            SELECT FilePath
            FROM   tblFile
            WHERE  FilePath LIKE ? || '%'
            """,
            (folder_path,),
        )

        results = cursor.fetchall()
        for result in results:
            entries.files.append(result[0])

    return entries


def remove_folder(folder_path: str) -> bool:
    """
    Removes folder from the database

    Parameters
    ----------
    folder_path : str
        Path to remove

    Returns
    -------
    bool
        True if removed, False otherwise
    """
    with SQLiteCursor() as cursor:
        cursor.execute(
            """
            DELETE FROM tblFolder WHERE FolderPath = ?
            """,
            (folder_path,),
        )

        return (
            DatabaseError.SUCCESS
            if cursor.rowcount > 0
            else DatabaseError.NONEXISTENT_FOLDER
        )


def update_file_path(current_path: str, new_path: str) -> DatabaseError:
    """
    Updates path of a file

    Parameters
    ----------
    current_path : string
        Current file path
    new_path :  string
        New file path (including name)

    Returns
    -------
    DatabaseError
        Database result code
    """
    try:
        with SQLiteCursor() as cursor:
            cursor.execute(
                """
                UPDATE tblFile
                SET    FilePath = ?
                WHERE  FilePath = ?
                """,
                (new_path, current_path,),
            )
            return (
                DatabaseError.SUCCESS
                if cursor.rowcount
                else DatabaseError.NONEXISTENT_FILE
            )
    except sqlite3.IntegrityError:
        return DatabaseError.FILE_EXISTS


def update_folder_path(current_path: str, new_path: str) -> DatabaseError:
    """
    Updates path of a folder

    Parameters
    ----------
    current_path : string
        Current folder path
    new_path :  string
        New folder path (including name)

    Returns
    -------
    DatabaseError
        Database result code
    """
    try:
        with SQLiteCursor() as cursor:
            cursor.execute(
                """
                UPDATE tblFolder
                SET    FolderPath = ?
                WHERE  FolderPath = ?
                """,
                (new_path, current_path,),
            )
            return (
                DatabaseError.SUCCESS
                if cursor.rowcount
                else DatabaseError.NONEXISTENT_FOLDER
            )
    except sqlite3.IntegrityError:
        return DatabaseError.FOLDER_EXISTS


def update_file_device(file_path: str, device_mount_path: str) -> DatabaseError:
    """
    Updates the device a given file path is backed up on

    Parameters
    ----------
    file_path : str
        Path to the file to update device for
    device_mount_path : str
        Mount path of the device to use for this file

    Returns
    -------
    DatabaseError
        Result
    """
    try:
        with SQLiteCursor() as cursor:
            cursor.execute(
                """
                UPDATE     tblFile
                SET        FileDeviceID = (
                    SELECT DeviceID
                    FROM   tblDevice
                    WHERE  DevicePath = ?
                )
                WHERE      FilePath = ?
                """,
                (device_mount_path, file_path,),
            )

            return (
                DatabaseError.SUCCESS
                if cursor.rowcount > 0
                else DatabaseError.NONEXISTENT_FILE
            )
    except sqlite3.IntegrityError:
        return DatabaseError.NONEXISTENT_DEVICE
