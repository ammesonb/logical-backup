# pylint: disable=fixme
"""
Library files for adding, moving, verifying files ,etc
"""
from texttable import Texttable

from logical_backup.db import DatabaseError
import logical_backup.db as db
import logical_backup.utility as utility
from logical_backup.pretty_print import (
    pprint,
    Color,
    Background,
    Format,
    pprint_start,
    pprint_complete,
)


# pylint: disable=unused-argument
def add_directory(folder_path: str, mount_point: str = None) -> bool:
    """
    Adds a directory to the backup
    See add_file
    """
    # Note: if want to proceed with specific device, will need to null that out
    # after capacity is consumed


# pylint: disable=unused-argument
def remove_directory(folder_path: str) -> bool:
    """
    Removes a directory from the backup
    See remove_file
    """


# pylint: disable=unused-argument
def move_directory(current_path: str, new_path: str) -> bool:
    """
    Moves a directory in the backup
    See move_file
    """


# pylint: disable=unused-argument
def add_file(
    file_path: str, mount_point: str = None, size_checked: bool = False
) -> bool:
    """
    Will add a file to the backup archive

    Parameters
    ----------
    file_path : str
        The file path to add
    mount_point : str
        Optionally, the mount point to prefer
    size_checked : bool
        Used for folder addition to specific device
        True if the size of the specified device has already been checked
        for required capacity of file/s

    Returns
    -------
    bool
        True if added, False otherwise
          - due to database failure, hard drive failure, etc
          - or if it already exists
    """


# pylint: disable=unused-argument
def remove_file(file_path: str) -> bool:
    """
    Will remove a file to the backup archive

    Parameters
    ----------
    file_path : str
        The file path to remove

    Returns
    -------
    bool
        True if removed, False otherwise
          - due to database failure, hard drive failure, etc
          - or if it does not exist
    """


# pylint: disable=unused-argument
def move_file(original_path: str, new_path: str) -> bool:
    """
    Will remove a file to the backup archive

    Parameters
    ----------
    original_path : str
        The current file path to remove
    new_path : str
        The new path to the file

    Returns
    -------
    bool
        True if moved, False otherwise
          - due to database failure, or if it does not exist
    """


# pylint: disable=unused-argument
def add_device(mount_point: str) -> bool:
    """
    Adds a device to the database

    Parameters
    ----------
    mount_point : str
        The path to where the device is mounted

    Returns
    -------
    bool
        True if added, False otherwise
          - due to database failure, or if it path does not exist
    """
    device_name = input("Device name: ")
    identifier = utility.get_device_serial(mount_point)
    identifier_type = "Device Serial"
    if not identifier:
        identifier = utility.get_device_uuid(mount_point)
        identifier_type = "System UUID"

    if not identifier:
        identifier = input(
            "Unable to find systemic identifier. "
            "Please provide a unique identifier for the device: "
        )
        identifier_type = "User Specified"

    message = "Saving device..."
    pprint_start(message)
    result = db.add_device(device_name, mount_point, identifier_type, identifier)
    if result == DatabaseError.SUCCESS:
        pprint_complete(message + "Done", True, Color.GREEN)
    else:
        message += "Failed. "
        if result == DatabaseError.INVALID_IDENTIFIER_TYPE:
            pprint_complete(
                message + "Unrecognized device identifier!", False, Color.ERROR
            )
        elif result == DatabaseError.DEVICE_NAME_EXISTS:
            pprint_complete(message + "Name already taken!", False, Color.ERROR)
        elif result == DatabaseError.DEVICE_PATH_EXISTS:
            pprint_complete(
                message + "Device already registered at mount point!",
                False,
                Color.ERROR,
            )
        elif result == DatabaseError.DEVICE_IDENTIFIER_EXISTS:
            pprint_complete(
                message + "Serial already registered for another device!",
                False,
                Color.ERROR,
            )
        elif result == DatabaseError.UNKNOWN_ERROR:
            pprint_complete(message + "Unknown error occurred!", False, Color.ERROR)
        else:
            pprint_complete(
                message + "Super-unknown error occurred!",
                False,
                Color.ERROR,
                formats=[Format.UNDERLINE],
            )

        return False

    return True


# pylint: disable=unused-argument
def check_device(device_path: str) -> bool:
    """
    Checks if a device exists on the system path

    Parameters
    ----------
    device_path : str
        The path of the device to check

    Returns
    -------
    bool
        True if the device exists
    """


# pylint: disable=unused-argument
def verify_all(for_restore: bool) -> bool:
    """
    Verify all findable files on drives
    """


# pylint: disable=unused-argument
def verify_folder(folder_path: str, for_restore: bool) -> bool:
    """
    Checks a folder integrity based on the DB
    See verify_file
    """


# pylint: disable=unused-argument
def verify_file(file_path: str, for_restore: bool) -> bool:
    """
    Check a file path for consistency

    Parameters
    ----------
    file_path : str
        The file path to verify checksum for
    for_restore : bool
        If verification is for restoration
        If True, checks device path, otherwise checks system

    Returns
    -------
    bool
        True if checksum match
        False otherwise, e.g. file does not exist
    """


# pylint: disable=unused-argument
def restore_all() -> bool:
    """
    Restore all files
    See restore_files
    """


# pylint: disable=unused-argument
def restore_folder(folder_path: str) -> bool:
    """
    Restores a specific folder
    See restore_files
    """


# pylint: disable=unused-argument
def restore_file(file_path: str) -> bool:
    """
    Restore a file from backup
    Will perform a verification of the device first
    In case of conflict, will provide prompt - no auto-selection yet

    Parameters
    ----------
    file_path : str
        The file path to restore

    Returns
    -------
    bool
        True if file restored
        False if, e.g.:
          - backed up file checksum doesn't match database
          - copied file checksum mismatches
          - device unavailable
    """


def list_devices():
    """
    List all the devices registered
    """
    devices = db.get_devices()
    if devices:

        table = Texttable()
        headers = devices[0].keys()
        table.add_row(headers)

        for device in devices:
            row = []
            for header in headers:
                row.append(device[header])
            table.add_row(row)

        print(table.draw())
    else:
        pprint("No devices saved!", Color.ERROR, Background.BLACK, [Format.BOLD])
