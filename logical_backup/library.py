# pylint: disable=fixme
"""
Library files for adding, moving, verifying files ,etc
"""
import grp
import os
import os.path as os_path
import pwd
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
        ).lower()
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


def move_directory_local(current_path: str, new_path: str) -> bool:
    """
    Moves a directory in the backup
    See move_file_local
    """
    entries = db.get_entries_for_folder(current_path)

    all_success = True
    absolute_new_path = new_path
    # If new path already exists, add name of current path to it
    if os_path.isdir(new_path):
        absolute_new_path = os_path.join(
            absolute_new_path, os_path.basename(current_path)
        )
    elif os_path.isfile(new_path):
        print_error("Cannot move folder over existing file!")
        return False

    # Should include base folder as well
    for folder in entries.folders:
        new_folder = folder.replace(current_path, absolute_new_path)
        result = db.update_folder_path(folder, new_folder)
        if result == DatabaseError.FOLDER_EXISTS:
            print_error("Folder already backed up at path '{0}'!".format(new_folder))
            all_success = False
        elif result == DatabaseError.NONEXISTENT_FOLDER:
            print_error("Specified folder not backed up: '{0}'!".format(new_folder))
            all_success = False

    for file_path in entries.files:
        new_file = file_path.replace(current_path, absolute_new_path)
        if not move_file_local(file_path, new_file):
            all_success = False

    return all_success


def move_directory_device(current_path: str, device: str) -> bool:
    """
    Moves a directory in the backup
    See move_file_device
    """
    entries = db.get_entries_for_folder(current_path)
    total_file_size = utility.sum_file_size(entries.files)
    device_space = utility.get_device_space(device)

    if total_file_size >= device_space:
        print_error("Selected device cannot fit all the requested files!")
        return False

    return all([move_file_device(file_path, device) for file_path in entries.files])


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


def __remove_missing_database_entries(entries: utility.DirectoryEntries) -> bool:
    """
    Checks a given list of files and folders for existence on the file system
    Will prompt to remove them

    Parameters
    ----------
    entries : DirectoryEntries
        The list of entries to check

    Returns
    -------
    bool
        True if all attempted removals succeed
    """
    recursive_prompted = False
    remove_recursive = False
    files_prompted = False
    remove_files = False

    success = True

    for folder_path in entries.folders:
        if not os_path.isdir(folder_path):
            if not recursive_prompted:
                remove_recursive = (
                    input(
                        "Found one or more backed-up folders that no longer exist! "
                        "Remove ALL missing directories recursively? "
                        "Type REMOVE uppdercase to do so "
                    )
                    == "REMOVE"
                )
                recursive_prompted = True

            if remove_recursive:
                success = success and remove_directory(folder_path)

    for file_path in entries.files:
        if not os_path.isfile(file_path):
            if not files_prompted:
                remove_files = (
                    input(
                        "Found one or more backed-up files that no longer exist! "
                        "Remove all missing files? Type YES uppercase to do so "
                    )
                    == "YES"
                )
                files_prompted = True

            if remove_files:
                success = success and remove_file(file_path)

    return success


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


def move_file_local(original_path: str, new_path: str) -> bool:
    """
    Will move a file in the archive to a new path

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
    # Add file path if destination is a directory
    if os_path.isdir(new_path):
        new_path = os_path.join(new_path, os_path.basename(original_path))

    result = db.update_file_path(original_path, new_path)
    if result == DatabaseError.NONEXISTENT_FILE:
        print_error("File path not backed up!")
    elif result == DatabaseError.FILE_EXISTS:
        print_error("File already backed up at new location!")

    return bool(result)


def move_file_device(original_path: str, device: str) -> bool:
    """
    Will move a file in the archive to a specified device

    Parameters
    ----------
    original_path : str
        The current file path to remove
    device : str
        The path of the device to move it onto

    Returns
    -------
    bool
        True if moved, False otherwise
          - due to database failure, or if it does not exist
    """
    file_size = utility.get_file_size(original_path)
    device_space = utility.get_device_space(device)

    if file_size >= device_space:
        print_error("Device selected has insufficient space!")
        return False

    file_result = db.get_files(original_path)
    if not file_result:
        print_error("Selected path does not exist in back up!")
        return False

    backup_name = file_result[0].file_name
    current_path = os_path.join(file_result[0].device.device_path, backup_name)

    file_valid = True
    if not os_path.ismount(file_result[0].device.device_path):
        print_error("Device for backed-up file is not attached!")
        file_valid = False
    elif not os_path.isfile(current_path):
        print_error("Cannot find back up of file!")
        file_valid = False

    if not file_valid:
        return False

    copy_printer = PrettyStatusPrinter("Copying file to new device").print_start()
    new_path = os_path.join(device, backup_name)
    shutil.copyfile(current_path, new_path)
    copy_printer.print_complete()

    new_checksum = utility.checksum_file(new_path)

    device_updated = False
    file_updated = False

    checksum_match = file_result[0].checksum == new_checksum
    if checksum_match:
        device_updated = db.update_file_device(original_path, device)
    else:
        print_error("Checksum verification mismatch!")

    if checksum_match and device_updated:
        file_updated = db.update_file_path(original_path, new_path)
        if file_updated:
            os.remove(current_path)
        else:
            print_error("Failed to update path in database!")
    else:
        print_error("Failed to update device for file in database!")

    if not checksum_match or not device_updated or not file_updated:
        os.remove(new_path)

    return checksum_match and device_updated and file_updated


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
    # Check path is valid for restoring
    if os_path.isfile(file_path):
        print_error("Path to restore already exists!")
        return False

    if not verify_file(file_path, True):
        print_error("Backed-up file has mismatched checksum!")
        return False

    file_result = db.get_files(file_path)
    if not file_result:
        print_error("Requested path was not backed up!")
        return False

    file_obj = file_result[0]

    # Copy the file
    backup_path = os_path.join(file_obj.device.device_path, file_obj.file_name)
    shutil.copyfile(backup_path, file_path)

    # Verify it copied successfully
    if utility.checksum_file(file_path) != file_obj.checksum:
        print_error("Restored file has mismatched checksum!")
        # Can remove file here because we just created it
        # MAy not be true after this, once we restore file permissions and ownership
        os.remove(file_path)
        return False

    # Get security details to set
    # Using names so can persist across sytem recreations where IDs may change
    os.chmod(file_path, int(file_obj.permissions, 8))
    uid = pwd.getpwnam(file_obj.owner).pw_uid
    gid = grp.getgrnam(file_obj.group).gr_gid
    os.chown(file_path, uid, gid)

    security_verification = utility.get_file_security(file_path)
    security_verified = security_verification == {
        "permissions": file_obj.permissions,
        "owner": file_obj.owner,
        "group": file_obj.group,
    }

    if not security_verified:
        try:
            os.remove(file_path)
            print_error("Failed to set file permissions/owner, but able to remove file")
        except PermissionError:
            print_error(
                "Failed to set file permissions/owner, manual removal required!"
            )

    return security_verified


def update_file(file_path: str) -> bool:
    """
    Checks if a file has changed, and if it has, replaces the backed-up file

    Parameters
    ----------
    file_path : str
        The file path to update

    Returns
    -------
    bool
        True if file updated or is current
        False if, e.g.:
          - failed to remove file
          - failed to re-add file
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

    # pylint: disable=consider-using-ternary
    # outcome must be one of:
    #   - no change to file
    #   - file is updated - removed AND added
    #
    # NOT equivalent using a ternary
    # which would return checksum_match if not file_removed
    return (file_added and file_removed) or checksum_match


def update_folder(folder: str) -> bool:
    """
    Updates a folder to match what is currently on disk
    """
    registered_files = db.get_entries_for_folder(folder)
    disk_files = utility.list_entries_in_directory(folder)

    # Too many conditions, so add explicit success flag here
    all_success = __remove_missing_database_entries(registered_files)

    # An existing folder just need to be purged from the DB to be added back
    # No recursive file checks or anything, since the listing already handled that
    for folder_path in disk_files.folders:
        folder = Folder()
        folder_details = utility.get_file_security(folder_path)
        folder.set(
            folder_path,
            folder_details["permissions"],
            folder_details["owner"],
            folder_details["group"],
        )

        if folder_path in registered_files.folders:
            db_folder = db.get_folders(folder_path)
            # If folders are equivalent, do nothing
            if db_folder[0] == folder:
                continue

            if not db.remove_folder(folder_path):
                print_error(
                    "Failed to remove folder {0} from database!".format(folder_path)
                )
                all_success = False
                continue

        if not db.add_folder(folder):
            print_error(
                "Failed to add folder {0} back to database!".format(folder_path)
            )
            all_success = False

    for file_path in disk_files.files:
        all_success = all_success and update_file(file_path)

    return all_success


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
