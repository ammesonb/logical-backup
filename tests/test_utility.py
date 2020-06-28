"""
Tests for utility functions
"""
from collections import namedtuple
import hashlib
import os
import os.path as os_path
import psutil
import pwd
import grp
from pathlib import Path
import shutil
import tempfile

from logical_backup.utility import __get_device_path
import logical_backup.utility as utility
from logical_backup.pretty_print import readable_bytes

DiskPartition = namedtuple("sdiskpart", "device mountpoint fstype opts")
DiskUsage = namedtuple("diskusage", "total used free percent")
StatResult = namedtuple(
    "stat_result",
    "st_mode st_ino st_dev st_nlink st_uid st_gid st_size st_atime st_mtime st_ctime",
)

PwUID = namedtuple(
    "struct_passwd", "pw_dir pw_gecos pw_gid pw_name pw_passw pw_shell pw_uid"
)
GrID = namedtuple("struct_group", "gr_name gr_passwd gr_gid gr_mem")


def __compare_lists(list1: list, list2: list) -> bool:
    return len(list1) == len(list2) and all(
        [True if item in list2 else False for item in list1]
    )


def patch_input(monkeypatch, module, func) -> None:
    """
    Patch the input function for a given module

    Parameters
    ----------
    monkeypatch
        -
    module
        The module to patch input on
    func
        Function to replace input
    """
    # The __builtins__ isn't _officially_ a part of a class, so pylint is mad
    # _Should_ be safe though, I would expect
    # pylint: disable=no-member
    monkeypatch.setitem(module.__builtins__, "input", func)


def test_is_test():
    """
    Should always be testing, since this is a test
    """
    assert not utility.is_test(), "Test variable should not be set yet"
    utility.set_testing()
    assert (
        utility.is_test()
    ), "Test utility does not return test environment, what has the world come to"
    utility.remove_testing()
    assert not utility.is_test(), "Test variable should have been cleared"


def test_run_command():
    """
    .
    """
    result = utility.run_command(["echo", "hello world"])
    assert result["stdout"] == b"hello world\n", "Echo should output hello world"
    assert result["exit_code"] == 0, "Echo should not fail"

    result = utility.run_command(["cat", "no_such_file"])
    assert result["exit_code"] != 0, "Can't cat non-existent file"


def test_run_piped_command():
    """
    .
    """
    result = utility.run_piped_command([["echo", "hello_world"], ["sed", "s/_/ /"]])
    assert result["stdout"] == b"hello world\n", "Echo should output hello world"
    assert result["exit_code"] == 0, "Echo should not fail"

    result = utility.run_piped_command([["echo", "hello_world"], ["cat", "no_file"]])
    assert result["exit_code"] != 0, "Can't cat non-existent file"


def test_get_device_path(monkeypatch):
    """
    Test getting device paths from mount point
    """
    root_partition = DiskPartition("/dev/sda", "/", "ext4", "rw")
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: [root_partition])
    result = __get_device_path("/test")
    assert not result, "Nothing returned if no mounted partitions"

    result = __get_device_path("/")
    assert result == "/dev/sda", "Only mounted partition should return device"

    other_partition_one = DiskPartition("/dev/sdb", "/test1", "ext3", "ro")
    other_partition_two = DiskPartition("/dev/sdc", "/test2", "ext4", "r2")
    monkeypatch.setattr(
        psutil,
        "disk_partitions",
        lambda all=False: [root_partition, other_partition_one, other_partition_two],
    )

    result = __get_device_path("/test1")
    assert result == "/dev/sdb", "Multiple mounted partitions"


def test_get_device_serial(capsys, monkeypatch):
    """
    .
    """
    monkeypatch.setattr(utility, "__get_device_path", lambda path: None)
    result = utility.get_device_serial("/test")
    output = capsys.readouterr()
    assert "No serial found" in output.out, "Missing device printed for serial"
    assert not result, "No serial returned for missing device"

    monkeypatch.setattr(utility, "__get_device_path", lambda path: "/dev/sda")
    monkeypatch.setattr(
        utility, "run_piped_command", lambda commands: {"stdout": b"12345\n"}
    )

    result = utility.get_device_serial("/test")
    output = capsys.readouterr()
    assert result == "12345", "Serial returned for device"
    assert "Found 12345" in output.out, "Serial printed for device"


def test_get_device_uuid(capsys, monkeypatch):
    """
    .
    """
    monkeypatch.setattr(utility, "__get_device_path", lambda path: None)
    result = utility.get_device_uuid("/test")
    output = capsys.readouterr()
    assert "No UUID found" in output.out, "Missing device printed for UUID"
    assert not result, "No UUID returned for missing device"

    monkeypatch.setattr(utility, "__get_device_path", lambda path: "/dev/sda")
    monkeypatch.setattr(
        utility,
        "run_piped_command",
        lambda commands: {"stdout": b"12345-ABCDEF-98765\n"},
    )

    result = utility.get_device_uuid("/test")
    output = capsys.readouterr()
    assert result == "12345-ABCDEF-98765", "UUID returned for device"
    assert "Found 12345-ABCDEF-98765" in output.out, "UUID printed for device"


def test_get_disk_space(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(psutil, "disk_usage", lambda path: DiskUsage(125, 25, 100, 80))
    result = utility.get_device_space("/test")
    assert result == 100, "Available disk space wasn't returned correctly"


def test_get_file_size(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(os_path, "isfile", lambda x: False)
    result = utility.get_file_size("nonexistent")
    assert not result, "File size should fail if not a file"

    monkeypatch.setattr(os_path, "isfile", lambda x: True)
    monkeypatch.setattr(
        os,
        "stat",
        lambda path: StatResult(
            33188,
            7738624,
            65028,
            1,
            1000,
            1000,
            36864,
            1591838246,
            1591838131,
            1591838131,
        ),
    )

    result = utility.get_file_size("exists")
    assert result == 36864, "File size should be returned"


def test_get_abs_path(monkeypatch):
    """
    .
    """
    result = utility.get_abs_path(None)
    assert not result, "None should return None"

    # NOTE: this is an internal use of getcwd by abspath, and may change
    # NOTE: if it does, this will require a different mock, possibly of abspath itself
    monkeypatch.setattr(os, "getcwd", lambda: "/home/foo")
    result = utility.get_abs_path("test")
    assert result == "/home/foo/test", "Test directory returned"


def test_get_checksum(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(
        utility,
        "run_piped_command",
        lambda command: {"exit_code": 1, "stdout": b"", "stderr": ""},
    )
    output = utility.checksum_file("test")
    assert not output, "Checksum fail should be empty"

    monkeypatch.setattr(
        utility,
        "run_piped_command",
        lambda command: {"exit_code": 0, "stdout": b"abc123", "stderr": ""},
    )
    output = utility.checksum_file("test")
    assert output == "abc123", "Faux checksum should match"


def test_create_backup_name(monkeypatch):
    """
    .
    """
    hash_result = hashlib.sha256("abc123".encode())
    monkeypatch.setattr(hashlib, "sha256", lambda text: hash_result)
    name = utility.create_backup_name("test")
    assert name == hash_result.hexdigest() + "_test", "Basic file name should match"

    hash_result_2 = hashlib.sha256("/foo/test".encode())
    name = utility.create_backup_name("/foo/test")
    assert (
        name == hash_result_2.hexdigest() + "_test"
    ), "Test file name with path should match"


def test_byte_printing():
    """
    Check printing library output
    """
    assert readable_bytes(100) == "100.0B", "Bytes output"
    assert readable_bytes(2 * 1024) == "2.0KiB", "KiloBytes output"
    assert readable_bytes(3 * 1024 * 1024) == "3.0MiB", "MegaBytes output"
    assert readable_bytes(4.056 * 1024 * 1024) == "4.1MiB", "MegaBytes output"
    assert readable_bytes(4.056 * 1024 * 1024) == "4.1MiB", "MegaBytes output"
    assert readable_bytes(1 * 1024 ** 8) == "1.0YiB", "Super huge output"
    assert readable_bytes(1 * 1024 ** 9) == "1024.0YiB", "Super super huge output"


def test_get_file_security(monkeypatch, capsys):
    """
    .
    """
    monkeypatch.setattr(
        os,
        "stat",
        lambda path: StatResult(
            33188,
            7738624,
            65028,
            1,
            1000,
            1000,
            36864,
            1591838246,
            1591838131,
            1591838131,
        ),
    )

    user = PwUID("/home/user", "user,,,,", 1000, "user", "x", "/usr/zsh", 1000)
    group = GrID("group", "x", 1000, [])
    monkeypatch.setattr(pwd, "getpwuid", lambda uid: user)
    monkeypatch.setattr(grp, "getgrgid", lambda gid: group)

    result = utility.get_file_security("/test")
    output = capsys.readouterr()
    assert result == {
        "permissions": "644",
        "owner": "user",
        "group": "group",
    }, "Expected permissions were returned"
    assert (
        "Checking file permissions...Complete" in output.out
    ), "Expected text was printed"


def test_list_files():
    """
    .
    """
    temp_file_path = lambda name, intermediary=None: os_path.join(
        test_directory, intermediary if intermediary else "", name
    )

    test_directory = tempfile.mkdtemp()
    fd, filename = tempfile.mkstemp(dir=test_directory)
    file1 = temp_file_path(filename)

    nested_directory_1 = temp_file_path(tempfile.mkdtemp(dir=test_directory))
    nested_directory_2 = temp_file_path(tempfile.mkdtemp(dir=test_directory))

    entries = utility.list_entries_in_directory(test_directory)
    assert entries.files == [file1], "Empty directories should not be included"
    assert __compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2]
    ), "Directory and empty directories should be included"

    fd, filename = tempfile.mkstemp(dir=nested_directory_2)
    file2 = temp_file_path(filename)

    entries = utility.list_entries_in_directory(test_directory)
    assert entries.files == [
        file1,
        file2,
    ], "Files in nested directory should be included"
    assert __compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2,]
    ), "Nested files in directory"

    nested_directory_3 = temp_file_path(tempfile.mkdtemp(dir=nested_directory_1))
    fd, filename = tempfile.mkstemp(dir=nested_directory_1)
    file3 = temp_file_path(filename)

    entries = utility.list_entries_in_directory(test_directory)
    assert len(entries.files) == 3, "All files included"
    assert __compare_lists(
        entries.files, [file1, file2, file3]
    ), "Includes file in double-nested directories"
    assert __compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2, nested_directory_3]
    ), "All nested directories should be included"

    shutil.rmtree(test_directory)


def test_sum_files():
    """
    .
    """

    test_directory = tempfile.mkdtemp()
    fd, filename = tempfile.mkstemp(dir=test_directory)
    fd = open(filename, "wb")
    fd.write(os.urandom(100))
    fd.close()

    file_list = [os_path.join(test_directory, filename)]
    print(file_list)

    assert utility.sum_file_size(file_list) == 100, "Single file size summed"

    fd, filename = tempfile.mkstemp(dir=test_directory)
    fd = open(filename, "wb")
    fd.write(os.urandom(50))
    fd.close()
    file_list.append(os_path.join(test_directory, filename))

    assert utility.sum_file_size(file_list) == 150, "Two files summed"

    shutil.rmtree(test_directory)
