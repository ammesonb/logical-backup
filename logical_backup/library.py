# pylint: disable=fixme
"""
Library files for adding, moving, verifying files ,etc
"""
import os
import os.path as os_path
import shutil
from texttable import Texttable

from logical_backup.objects.device import Device
from logical_backup.objects.file import File
from logical_backup.objects.folder import Folder
from logical_backup.db import DatabaseError
from logical_backup import db
from logical_backup import utility
from logical_backup.pretty_print import (
    Color,
    readable_bytes,
    PrettyStatusPrinter,
    print_error,
)


def add_directory(folder_path: str, mount_point: str = None) -> bool:
    """
    Adds a directory to the backup
    See add_file
    """
    entries = utility.list_entries_in_directory(folder_path)
    folder_size = utility.sum_file_size(entries.files)
    total_available_space = __get_total_device_space()

    device_has_space = (
        mount_point and folder_size <= utility.get_device_space(mount_point)
        if mount_point
        else True
    )
    sufficient_space = folder_size <= total_available_space

    # If the given mount point is too small for the folder,
    # but there is enough space across all drives to fit the folder
    if not device_has_space and sufficient_space:
        PrettyStatusPrinter(
            "Selected device will not fit all files!"
        ).with_specific_color(Color.YELLOW).print_message()
        switch_device = input(
            "Continue with any available device? (y/N, 'n' will exit)"
        )
        if switch_device == "y":
            mount_point = None
        else:
            print_error("Exiting since unable to fit all files on selected device")
            return False

    if not sufficient_space:
        print_error(
            "Sum of available devices' space is insufficient, "
            "need {0} additional space! Exiting".format(
                readable_bytes(folder_size - total_available_space)
            )
        )
        return False

    parent_details = utility.get_file_security(folder_path)
    parent_folder = Folder()
    parent_folder.set(
        folder_path,
        parent_details["permissions"],
        parent_details["owner"],
        parent_details["group"],
    )
    all_success = db.add_folder(parent_folder)
    for subfolder in entries.folders:
        folder = Folder()
        folder_details = utility.get_file_security(subfolder)
        folder.set(
            subfolder,
            folder_details["permissions"],
            folder_details["owner"],
            folder_details["group"],
        )
        all_success = all_success and db.add_folder(folder)
    for file_path in entries.files:
        all_success = all_success and add_file(file_path, mount_point)

    return all_success


def remove_directory(folder_path: str) -> bool:
    """
    Removes a directory from the backup
    See remove_file

    Note: does NOT remove anything on disk, since backed-up folders
    are just organizational, for use in restoration only
    """
    entries = db.get_entries_for_folder(folder_path)
    file_removal = PrettyStatusPrinter(
        "Removing files"
    ).with_message_postfix_for_result(False, "Failures")
    file_removal.print_start()

    files_removed = all([remove_file(file_path) for file_path in entries.files])
    all_removed = files_removed
    if files_removed:
        file_removal.print_complete()

        folder_removal = PrettyStatusPrinter(
            "Removing folders"
        ).with_message_postfix_for_result(False, "Failures")
        folder_removal.print_start()

        all_removed = files_removed and all(
            [db.remove_folder(folder) for folder in entries.folders]
        )

        if all_removed:
            folder_removal.print_complete()
        else:
            folder_removal.print_complete(False)
    else:
        file_removal.print_complete(False)

    return all_removed


# pylint: disable=unused-argument
def move_directory(current_path: str, new_path: str) -> bool:
    """
    Moves a directory in the backup
    See move_file
    """


def __get_total_device_space() -> int:
    """
    Gets total available space on all devices

    Returns
    -------
    int
        Bytes available
    """
    devices = db.get_devices()
    total_space = 0
    for device in devices:
        if os_path.ismount(device.device_path):
            total_space += utility.get_device_space(device.device_path)

    return total_space


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
        space_message = PrettyStatusPrinter(
            "Checking drive space"
        ).with_message_postfix_for_result(False, "Insufficient space!")
        space_message.print_start()

        drive_space = utility.get_device_space(mount_point)
        if file_size >= drive_space:
            space_message.print_complete(False)
            confirm = input("Switch drive? (Y/n, n exits) ")
            if confirm != "n":
                mount_point = None
            else:
                return None, None
        else:
            space_message.print_complete()

    device_name = None
    # This also needs to happen if we unset it due to space problems
    if not mount_point:
        auto_select_device = PrettyStatusPrinter(
            "Auto-selecting device"
        ).with_message_postfix_for_result(False, "None found!")
        auto_select_device.print_start()

        devices = db.get_devices()
        for device in devices:
            space = utility.get_device_space(device.device_path)
            if space > file_size:
                auto_select_device.with_message_postfix_for_result(
                    True, "Selected " + device.device_name
                ).print_complete()
                mount_point = device.device_path
                device_name = device.device_name
                break

        if not mount_point:
            auto_select_device.print_complete(False)

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
        print_error("File is already backed up!")
        return False

    security_details = utility.get_file_security(file_path)
    checksum = utility.checksum_file(file_path)
    if not checksum:
        print_error("Failed to get checksum!")
        return False

    file_size_message = PrettyStatusPrinter("Getting file size")
    file_size_message.print_start()

    file_size = utility.get_file_size(file_path)
    file_size_message.with_message_postfix_for_result(
        True, "Read. File is " + readable_bytes(file_size)
    ).print_complete()

    device_name, mount_point = __get_device_with_space(
        file_size, mount_point, size_checked
    )
    if not device_name:
        print_error("No device with space available!")
        return False

    new_name = utility.create_backup_name(file_path)
    new_path = os_path.join(mount_point, new_name)
    shutil.copyfile(file_path, new_path)

    checksum2 = utility.checksum_file(new_path)

    if checksum != checksum2:
        print_error("Checksum mismatch after copy!")
        os.remove(new_path)
        return False

    file_obj = File()
    file_obj.device_name = device_name
    file_obj.set_properties(os_path.basename(file_path), file_path, checksum)
    file_obj.set_security(**security_details)

    db_save = PrettyStatusPrinter("Saving file record to DB").print_start()

    succeeded = db.add_file(file_obj)
    if succeeded == DatabaseError.SUCCESS:
        db_save.print_complete()
    else:
        db_save.print_complete(False)
        os.remove(new_path)

    return succeeded


def remove_file(file_path: str) -> bool:
    """
    Will remove a file in the backup archive

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
    validate_message = (
        PrettyStatusPrinter("Validating file removal")
        .with_message_postfix_for_result(True, "File removed")
        .with_custom_result(2, False)
        .with_message_postfix_for_result(2, "File not registered in database!")
        .with_custom_result(3, False)
        .with_message_postfix_for_result(3, "Unable to find device")
        .with_custom_result(4, False)
        .with_message_postfix_for_result(4, "File path does not exist!")
        .with_custom_result(5, False)
        .with_message_postfix_for_result(5, "Failed to remove file from database!")
        .print_start()
    )

    file_entry = db.get_files(file_path)
    if file_entry and len(file_entry) > 0:
        file_entry = file_entry[0]

    device = None
    if file_entry:
        device = db.get_devices(file_entry.device_name)

    if device and len(device) > 0:
        device = device[0]

    path_on_device = None
    if file_entry and device:
        path_on_device = os_path.join(device.device_path, file_entry.file_name)

    valid = bool(file_entry) and bool(device) and os_path.exists(path_on_device)

    db_entry_removed = False
    if valid:
        db_entry_removed = db.remove_file(file_path)

    if db_entry_removed:
        os.remove(path_on_device)
        validate_message.print_complete()
    elif not file_entry:
        validate_message.print_complete(2)
    elif not device:
        validate_message.print_complete(3)
    elif not os_path.exists(path_on_device):
        validate_message.print_complete(4)
    else:
        validate_message.print_complete(5)

    return db_entry_removed


# pylint: disable=unused-argument
def move_file(original_path: str, new_path: str) -> bool:
    """
    Will move a file in the archive to a new path, or to a different device

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

    save_message = (
        PrettyStatusPrinter("Saving device")
        .print_start()
        .with_custom_result(2, False)
        .with_message_postfix_for_result(2, "Failed. Unrecognized device identifier!")
        .with_custom_result(3, False)
        .with_message_postfix_for_result(3, "Failed. Name already taken!")
        .with_custom_result(4, False)
        .with_message_postfix_for_result(
            4, "Failed. Device already registered at mount point!"
        )
        .with_custom_result(5, False)
        .with_message_postfix_for_result(
            5, "Failed. Serial already registered for another device!"
        )
        .with_custom_result(6, False)
        .with_message_postfix_for_result(6, "Failed. Unknown error occurred!")
        .with_custom_result(7, False)
        .with_message_postfix_for_result(7, "Failed. Super-unknown error occurred!")
    )

    device = Device()
    device.set(device_name, mount_point, identifier_type, identifier)
    result = db.add_device(device)

    if result == DatabaseError.SUCCESS:
        save_message.print_complete()
    elif result == DatabaseError.INVALID_IDENTIFIER_TYPE:
        save_message.print_complete(2)
    elif result == DatabaseError.DEVICE_NAME_EXISTS:
        save_message.print_complete(3)
    elif result == DatabaseError.DEVICE_PATH_EXISTS:
        save_message.print_complete(4)
    elif result == DatabaseError.DEVICE_IDENTIFIER_EXISTS:
        save_message.print_complete(5)
    elif result == DatabaseError.UNKNOWN_ERROR:
        save_message.print_complete(6)
    else:
        save_message.print_complete(7)

    return result == DatabaseError.SUCCESS


def verify_all(for_restore: bool) -> bool:
    """
    Verify all findable files on drives
    """
    files = db.get_files()
    all_verified = True
    for file_path in files:
        all_verified = all_verified and verify_file(file_path, for_restore)

    return all_verified


def verify_folder(folder_path: str, for_restore: bool) -> bool:
    """
    Checks a folder integrity based on the DB
    See verify_file
    """
    entries = db.get_entries_for_folder(folder_path)
    all_verified = True
    for file_path in entries.files:
        all_verified = all_verified and verify_file(file_path, for_restore)

    return all_verified


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
    file_result = db.get_files(file_path)
    if not file_result:
        print_error("File record not in database")
        return False

    file_obj = file_result[0]

    path_to_check = (
        os_path.join(file_obj.device.device_path, file_obj.file_name)
        if for_restore
        else file_path
    )
    actual_checksum = utility.checksum_file(path_to_check)
    if actual_checksum != file_obj.checksum:
        print_error("Checksum mismatch for " + file_path)

    return actual_checksum == file_obj.checksum


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


def update_file(file_path: str) -> bool:
    """
    Checks if a file has changed, and if it has, replaces the backed-up file
    """
    file_result = db.get_files(file_path)
    file_registered = bool(file_result)
    # If these checks are irrelevant, then allow them to pass
    # checksum is relevant if file is registered, otherwise
    # success is solely dependent on file being added
    checksum_match = file_registered
    file_removed = True
    file_added = True

    # Only need to compare checksums if the file is registered
    # Otherwise will simply add it
    if file_registered:
        file_obj = file_result[0]
        checksum_match = utility.checksum_file(file_path) == file_obj.checksum

    # Only need to remove the file if
    #   - The file is registered already
    #   - and the checksum has changed
    if file_registered and not checksum_match:
        file_removed = remove_file(file_obj.file_path)
        if not file_removed:
            print_error("Failed to remove file, so cannot update!")

    # Add the file if:
    #   - file is NOT already registered
    #   - file did not match and was removed
    if not file_registered or (not checksum_match and file_removed):
        file_added = add_file(file_path)
        if not file_added:
            print_error("Failed to add file during update!")

    # outcome must be one of:
    #   - no change to file
    #   - file is updated - removed AND added
    return (file_added and file_removed) or checksum_match


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
        print_error("No devices saved!")
