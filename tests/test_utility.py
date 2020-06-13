"""
Tests for utility functions
"""
from collections import namedtuple
import os
import os.path as os_path
import psutil

from logical_backup.utility import __get_device_path
import logical_backup.utility as utility

DiskPartition = namedtuple("sdiskpart", "device mountpoint fstype opts")
DiskUsage = namedtuple("diskusage", "total used free percent")
StatResult = namedtuple(
    "stat_result",
    "st_mode st_ino st_dev st_nlink st_uid st_gid st_size st_atime st_mtime st_ctime",
)


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
