# pylint: disable=fixme
"""
Library files for adding, moving, verifying files ,etc
"""
import glob
import os
import os.path as os_path
import shutil
from texttable import Texttable

from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.db import DatabaseError
from logical_backup import db
from logical_backup import utility
from logical_backup.pretty_print import (
    pprint,
    Color,
    Background,
    Format,
    pprint_start,
    pprint_complete,
    readable_bytes,
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


# pylint: disable=bad-continuation
def __get_device_with_space(
    file_size: int, mount_point: str = None, size_checked: bool = False
) -> tuple:
    """
    Finds a device with given amount of space

    Parameters
    ----------
    file_size : int
        Size of the file
    mount_point : str
        Optional mount point to prefer
    size_checked : bool
        Used for folder addition to specific device
        True if the size of the specified device has already been checked
        for required capacity of file/s

    Returns
    -------
    tuple
        Name of the device to use, and mount point
    """
    if mount_point and not size_checked:
        message = "Checking drive space..."
        pprint_start(message)
        drive_space = utility.get_device_space(mount_point)
        if file_size >= drive_space:
            pprint_complete(message + "Insufficient space!", False, Color.ERROR)
            confirm = input("Switch drive? (Y/n, n exits) ")
            if confirm != "n":
                mount_point = None
            else:
                return None, None
        else:
            pprint_complete(message + "Done.", True, Color.BLUE)

    device_name = None
    # This also needs to happen if we unset it due to space problems
    if not mount_point:
        message = "Auto-selecting device..."
        pprint_start(message)

        devices = db.get_devices()
        for device in devices:
            space = utility.get_device_space(device.device_path)
            if space > file_size:
                pprint_complete(message + "Selected " + device.device_name, True)
                mount_point = device.device_path
                device_name = device.device_name
                break

        if not mount_point:
            pprint_complete(message + "None found!", False, Color.ERROR)

    else:
        devices = db.get_devices()
        device_name = [
            device.device_name
            for device in devices
            if device.device_path == mount_point
        ][0]

    return device_name, mount_point


# pylint: disable=bad-continuation
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
    if db.file_exists(file_path):
        pprint("File is already backed up!", Color.ERROR)
        return False

    security_details = utility.get_file_security(file_path)
    checksum = utility.checksum_file(file_path)
    if not checksum:
        pprint("Failed to get checksum!", Color.ERROR)
        return False

    message = "Getting file size..."
    pprint_start(message)
    file_size = utility.get_file_size(file_path)
    pprint_complete(message + "Read. File is " + readable_bytes(file_size), True)

    device_name, mount_point = __get_device_with_space(
        file_size, mount_point, size_checked
    )
    if not device_name:
        pprint("No device with space available!", Color.ERROR)
        return False

    new_name = utility.create_backup_name(file_path)
    new_path = os_path.join(mount_point, new_name)
    shutil.copyfile(file_path, new_path)

    checksum2 = utility.checksum_file(new_path)

    if checksum != checksum2:
        pprint("Checksum mismatch after copy!", Color.ERROR)
        os.remove(new_path)
        return False

    file_obj = File()
    file_obj.device_name = device_name
    file_obj.set_properties(os_path.basename(file_path), file_path, checksum)
    file_obj.set_security(**security_details)

    message = "Saving file record to DB..."
    pprint_start(message)
    succeeded = db.add_file(file_obj)
    if succeeded == DatabaseError.SUCCESS:
        pprint_complete(message + "Done.", True, Color.GREEN)
    else:
        pprint_complete(message + "Failed!", False, Color.ERROR)
        os.remove(new_path)

    return succeeded


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

    device = Device()
    device.set(device_name, mount_point, identifier_type, identifier)
    result = db.add_device(device)

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
