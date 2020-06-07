"""
Test less-complex library functions
"""
from logical_backup.library import list_devices

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from logical_backup.utility import auto_set_testing

# This is an auto-run fixture, so importing is sufficient
# pylint: disable=unused-import
from tests.test_db import auto_clear_db
from tests.mock_db import mock_devices


def test_list_devices(monkeypatch, capsys):
    """
    Test listing of devices
    """
    mock_devices(monkeypatch, [])
    list_devices()
    output = capsys.readouterr()
    assert "No devices saved!" in output.out, "No devices should be present in list"

    mock_devices(
        monkeypatch,
        [
            {
                "device_name": "test_device",
                "device_path": "/mnt/dev1",
                "identifier_name": "Device Serial",
                "device_identifier": "ABCDEF1234",
            },
            {
                "device_name": "seagate_drive",
                "device_path": "/mnt/dev2",
                "identifier_name": "System UUID",
                "device_identifier": "123456-ABCDEF-654321",
            },
        ],
    )
    list_devices()
    output = capsys.readouterr()
    assert (
        "| test_device   | /mnt/dev1   | Device Serial   | ABCDEF1234" in output.out
    ), "Test device 1 missing"
    assert (
        "| seagate_drive | /mnt/dev2   | System UUID     | 123456-ABCDEF-654321"
        in output.out
    ), "Seagate test device 2 missing"
