"""
Tests for file utilities
"""
from collections import namedtuple
import hashlib
import os
import os.path as os_path
import pwd
import grp
import shutil
import tempfile

from logical_backup.utilities import files, process, testing

StatResult = namedtuple(
    "stat_result",
    "st_mode st_ino st_dev st_nlink st_uid st_gid st_size st_atime st_mtime st_ctime",
)

PwUID = namedtuple(
    "struct_passwd", "pw_dir pw_gecos pw_gid pw_name pw_passw pw_shell pw_uid"
)
GrID = namedtuple("struct_group", "gr_name gr_passwd gr_gid gr_mem")


def test_get_file_size(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(os_path, "isfile", lambda x: False)
    result = files.get_file_size("nonexistent")
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

    result = files.get_file_size("exists")
    assert result == 36864, "File size should be returned"


def test_get_abs_path(monkeypatch):
    """
    .
    """
    result = files.get_abs_path(None)
    assert not result, "None should return None"

    # NOTE: this is an internal use of getcwd by abspath, and may change
    # NOTE: if it does, this will require a different mock, possibly of abspath itself
    monkeypatch.setattr(os, "getcwd", lambda: "/home/foo")
    result = files.get_abs_path("test")
    assert result == "/home/foo/test", "Test directory returned"


def test_get_checksum(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(
        process,
        "run_piped_command",
        lambda command: {"exit_code": 1, "stdout": b"", "stderr": ""},
    )
    output = files.checksum_file("test")
    assert not output, "Checksum fail should be empty"

    monkeypatch.setattr(
        process,
        "run_piped_command",
        lambda command: {"exit_code": 0, "stdout": b"abc123", "stderr": ""},
    )
    output = files.checksum_file("test")
    assert output == "abc123", "Faux checksum should match"


def test_create_backup_name(monkeypatch):
    """
    .
    """
    hash_result = hashlib.sha256("abc123".encode())
    monkeypatch.setattr(hashlib, "sha256", lambda text: hash_result)
    name = files.create_backup_name("test")
    assert name == hash_result.hexdigest() + "_test", "Basic file name should match"

    hash_result_2 = hashlib.sha256("/foo/test".encode())
    name = files.create_backup_name("/foo/test")
    assert (
        name == hash_result_2.hexdigest() + "_test"
    ), "Test file name with path should match"


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

    result = files.get_file_security("/test")
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
    descriptor, filename = tempfile.mkstemp(dir=test_directory)
    file1 = temp_file_path(filename)

    nested_directory_1 = temp_file_path(tempfile.mkdtemp(dir=test_directory))
    nested_directory_2 = temp_file_path(tempfile.mkdtemp(dir=test_directory))

    entries = files.list_entries_in_directory(test_directory)
    assert entries.files == [file1], "Empty directories should not be included"
    assert testing.compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2]
    ), "Directory and empty directories should be included"

    descriptor, filename = tempfile.mkstemp(dir=nested_directory_2)
    file2 = temp_file_path(filename)

    entries = files.list_entries_in_directory(test_directory)
    assert entries.files == [
        file1,
        file2,
    ], "Files in nested directory should be included"
    assert testing.compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2,]
    ), "Nested files in directory"

    nested_directory_3 = temp_file_path(tempfile.mkdtemp(dir=nested_directory_1))
    descriptor, filename = tempfile.mkstemp(dir=nested_directory_1)
    file3 = temp_file_path(filename)

    entries = files.list_entries_in_directory(test_directory)
    assert len(entries.files) == 3, "All files included"
    assert testing.compare_lists(
        entries.files, [file1, file2, file3]
    ), "Includes file in double-nested directories"
    assert testing.compare_lists(
        entries.folders, [nested_directory_1, nested_directory_2, nested_directory_3]
    ), "All nested directories should be included"

    shutil.rmtree(test_directory)


def test_sum_files():
    """
    .
    """

    test_directory = tempfile.mkdtemp()
    descriptor, filename = tempfile.mkstemp(dir=test_directory)
    file_handle = open(filename, "wb")
    file_handle.write(os.urandom(100))
    file_handle.close()

    file_list = [os_path.join(test_directory, filename)]
    print(file_list)

    assert files.sum_file_size(file_list) == 100, "Single file size summed"

    descriptor, filename = tempfile.mkstemp(dir=test_directory)
    file_handle = open(filename, "wb")
    file_handle.write(os.urandom(50))
    file_handle.close()
    file_list.append(os_path.join(test_directory, filename))

    assert files.sum_file_size(file_list) == 150, "Two files summed"

    shutil.rmtree(test_directory)
