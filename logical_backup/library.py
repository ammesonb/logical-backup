# pylint: disable=fixme
"""
Library files for adding, moving, verifying files ,etc
"""


# pylint: disable=unused-argument
def add_directory(folder_path: str) -> bool:
    """
    Adds a directory to the backup
    See add_file
    """


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
def add_file(file_path: str) -> bool:
    """
    Will add a file to the backup archive

    Parameters
    ----------
    file_path : str
        The file path to add

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
# pylint: disable=bad-continuation
def add_device(
    device_path: str,
    device_name: str,
    device_identifier_type: str,
    device_identifier: str,
) -> bool:
    """
    Adds a device to the database

    Parameters
    ----------
    device_path : str
        The mounted path to the device
    device_name : str
        A friendly name for the device
    device_identifier_type : str
        The type of identifier for the device
    device_identifier : str
        The actual identifier of the device

    Returns
    -------
    bool
        True if added, False otherwise
          - due to database failure, or if it path does not exist
    """


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
