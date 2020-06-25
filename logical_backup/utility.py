"""
Some helper functions
"""
import grp
import hashlib
from os import getenv, environ
import os
import os.path as os_path
import pwd
from subprocess import run, Popen, PIPE
from time import time

from pytest import fixture
import psutil

from logical_backup.pretty_print import pprint_start, pprint_complete, Color

TEST_VARIABLE = "IS_TEST"


def is_test() -> bool:
    """
    Returns whether code is run for a test
    Set via environment variables

    Returns
    -------
    bool
        True if being run as a test
    """
    return bool(getenv(TEST_VARIABLE))


def set_testing() -> None:
    """
    Set testing environment variable
    """
    environ[TEST_VARIABLE] = "1"


def remove_testing() -> None:
    """
    Remove the testing environment variable
    """
    del environ[TEST_VARIABLE]


def run_command(command: list) -> dict:
    """
    Executes a simple command

    Parameters
    ----------
    command : list
        The command to execute, grouped by parameters

    Returns
    -------
    dict
        With "exit_code", "stdout" and "stderr" properties
    """
    process = run(command, stdout=PIPE, stderr=PIPE, check=False)
    stdout, stderr = process.stdout, process.stderr
    return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr}


def run_piped_command(commands: list) -> dict:
    """
    Executes a list of list of commands, piping one into the next

    Parameters
    ----------
    commands : list
        A list of list of commands, to chain

    Returns
    -------
    dict
        With "exit_code", "stdout" and "stderr" properties
    """
    previous = None
    for command in commands:
        previous = Popen(
            command,
            stdout=PIPE,
            stdin=previous.stdout if previous else None,
            stderr=previous.stderr if previous else None,
        )

    out, err = previous.communicate()
    return {"exit_code": previous.returncode, "stdout": out, "stderr": err}


@fixture(autouse=True)
def auto_set_testing():
    """
    Will automatically set environment to testing
    """
    set_testing()
    yield "test"
    remove_testing()


def __get_device_path(mount_point: str) -> str:
    """
    Resolve the /dev/ path for a given mounted device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    partitions = psutil.disk_partitions()
    partition = [part for part in partitions if part.mountpoint == mount_point]
    return partition[0].device if partition else None


def get_device_serial(mount_point: str) -> str:
    """
    Get the serial ID for a device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    message = "Checking device serial..."
    pprint_start(message)

    serial = None
    partition = __get_device_path(mount_point)
    if partition:
        commands = [
            ["udevadm", "info", "--query=all", "--name=" + partition],
            ["grep", "ID_SERIAL_SHORT"],
            ["sed", "s/.*=//"],
        ]
        output = run_piped_command(commands)

        if output["stdout"].strip():
            serial = output["stdout"].strip().decode("utf-8")

    if serial:
        pprint_complete(message + "Found " + serial, True, Color.GREEN)
    else:
        pprint_complete(message + "No serial found!", False, Color.ERROR)

    return serial


def get_device_uuid(mount_point: str) -> str:
    """
    Get the system UUID for a device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    message = "Checking device UUID..."
    pprint_start(message)

    uuid = None
    partition = __get_device_path(mount_point)
    if partition:
        commands = [["blkid", partition, "-o", "value"], ["head", "-1"]]
        output = run_piped_command(commands)

        if output["stdout"].strip():
            uuid = output["stdout"].strip().decode("utf-8")

    if uuid:
        pprint_complete(message + "Found " + uuid, True, Color.GREEN)
    else:
        pprint_complete(message + "No UUID found!", False, Color.ERROR)

    return uuid


def get_device_space(mount_point: str) -> int:
    """
    Return available drive space, in bytes

    Parameters
    ----------
    mount_point : str
        The mount point

    Returns
    -------
    float
        Bytes of available space
    """
    available = psutil.disk_usage(mount_point)
    return available.free


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
    message = "Getting MD5 hash..."
    pprint_start(message)
    result = run_piped_command([["md5sum", path], ["awk", "{ print $1 }"]])
    if result["exit_code"]:
        pprint_complete(
            message + "Failed! Exit code: {0}".format(result["exit_code"]),
            False,
            Color.ERROR,
        )
        checksum = None
    else:
        pprint_complete(message + "Complete", True)
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
    message = "Checking file permissions..."
    pprint_start(message)
    file_stats = os.stat(path)
    permission_mask = oct(file_stats.st_mode)[-3:]
    owner = pwd.getpwuid(file_stats.st_uid).pw_name
    group = grp.getgrgid(file_stats.st_gid).gr_name
    pprint_complete(message + "Done.", True)

    return {"permissions": permission_mask, "owner": owner, "group": group}


def list_files_in_directory(path: str) -> list:
    """
    Lists files in a directory

    Parameters
    ----------
    path : str
        Path to list files in

    Returns
    -------
    list
        The files
    """
    all_files = []
    system_path = get_abs_path(path)

    for parent_path, directories, files in os.walk(system_path, followlinks=True):
        for file_name in files:
            all_files.append(os_path.join(parent_path, file_name))

    return all_files


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
        print(file_path)
        total_size += get_file_size(file_path)
        print(total_size)

    return total_size
