"""
Tests for device helpers
"""
from collections import namedtuple

import psutil

from logical_backup.utility import __get_device_path
from logical_backup.utilities import device, process

DiskPartition = namedtuple("sdiskpart", "device mountpoint fstype opts")
DiskUsage = namedtuple("diskusage", "total used free percent")


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
    monkeypatch.setattr(device, "__get_device_path", lambda path: None)
    result = device.get_device_serial("/test")
    output = capsys.readouterr()
    assert "No serial found" in output.out, "Missing device printed for serial"
    assert not result, "No serial returned for missing device"

    monkeypatch.setattr(device, "__get_device_path", lambda path: "/dev/sda")
    monkeypatch.setattr(
        process, "run_piped_command", lambda commands: {"stdout": b"12345\n"}
    )

    result = device.get_device_serial("/test")
    output = capsys.readouterr()
    assert result == "12345", "Serial returned for device"
    assert "Found 12345" in output.out, "Serial printed for device"


def test_get_device_uuid(capsys, monkeypatch):
    """
    .
    """
    monkeypatch.setattr(device, "__get_device_path", lambda path: None)
    result = device.get_device_uuid("/test")
    output = capsys.readouterr()
    assert "No UUID found" in output.out, "Missing device printed for UUID"
    assert not result, "No UUID returned for missing device"

    monkeypatch.setattr(device, "__get_device_path", lambda path: "/dev/sda")
    monkeypatch.setattr(
        process,
        "run_piped_command",
        lambda commands: {"stdout": b"12345-ABCDEF-98765\n"},
    )

    result = device.get_device_uuid("/test")
    output = capsys.readouterr()
    assert result == "12345-ABCDEF-98765", "UUID returned for device"
    assert "Found 12345-ABCDEF-98765" in output.out, "UUID printed for device"


def test_get_disk_space(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(psutil, "disk_usage", lambda path: DiskUsage(125, 25, 100, 80))
    result = device.get_device_space("/test")
    assert result == 100, "Available disk space wasn't returned correctly"
