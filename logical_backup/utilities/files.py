"""
File-based helpers
"""
from collections import namedtuple
import grp
import hashlib
import os
import os.path as os_path
import pwd
from time import time

from logical_backup.pretty_print import PrettyStatusPrinter
from logical_backup.utilities import process

DirectoryEntries = namedtuple("directory_entries", "files folders")


def get_file_size(path: str) -> int:
    """
    Get file size, in bytes
    Returns None if not a file

    Parameters
    ----------
    path : str
        Path to check

    Returns
    -------
    int
    """
    return None if not os_path.isfile(path) else os.stat(path).st_size


def get_abs_path(path: str) -> str:
    """
    Returns absolute path

    Parameters
    ----------
    path : str
        .
    """
    return os_path.abspath(path) if path else None


def checksum_file(path: str) -> str:
    """
    Gets the checksum of a file

    Parameters
    ----------
    path : str
        The path to checksum

    Returns
    -------
    string
        Checksum
    """
    message = PrettyStatusPrinter("Getting MD5 hash of " + path).print_start()
    result = process.run_piped_command([["md5sum", path], ["awk", "{ print $1 }"]])
    if result["exit_code"]:
        message.with_message_postfix_for_result(
            False, "Failed! Exit code: {0}".format(result["exit_code"])
        ).print_complete(False)
        checksum = None  # pragma: no mutate
    else:
        message.print_complete()
        checksum = result["stdout"].strip().decode()

    return checksum


def create_backup_name(path: str) -> str:
    """
    Creates a unique name to back up a file to

    Parameters
    ----------
    path : str
        Path to creat a unique name for

    Returns
    -------
    string
        A unique name
    """
    # Include time to guarantee uniqueness
    path_hash = hashlib.sha256((path + str(time)).encode())
    file_name = os_path.basename(path)
    return path_hash.hexdigest() + "_" + file_name


def get_file_security(path: str) -> dict:
    """
    Get security details for a file

    Parameters
    ----------
    path : str
        File path to get details about

    Returns
    -------
    dict
        Containing owner, group, and permissions
    """
    message = PrettyStatusPrinter("Checking file permissions").print_start()
    file_stats = os.stat(path)
    permission_mask = oct(file_stats.st_mode)[-3:]
    owner = pwd.getpwuid(file_stats.st_uid).pw_name
    group = grp.getgrgid(file_stats.st_gid).gr_name
    message.print_complete()

    return {"permissions": permission_mask, "owner": owner, "group": group}


def list_entries_in_directory(path: str) -> DirectoryEntries:
    """
    Lists files in a directory

    Parameters
    ----------
    path : str
        Path to list files in

    Returns
    -------
    DirectoryEntries
        Contents of the directory
    """
    entries = DirectoryEntries([], [])
    system_path = get_abs_path(path)

    for parent_path, directories, files in os.walk(system_path, followlinks=True):
        for file_name in files:
            entries.files.append(os_path.join(parent_path, file_name))

        for directory in directories:
            entries.folders.append(os_path.join(parent_path, directory))

    return entries


def sum_file_size(files: list) -> int:
    """
    Sums size of list of files

    Parameters
    ----------
    files : list
        List of file paths to sum

    Returns
    -------
    int
        Total bytes
    """
    total_size = 0
    for file_path in files:
        total_size += get_file_size(file_path)

    return total_size
