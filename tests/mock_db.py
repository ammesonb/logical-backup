"""
Functions to mock database results
"""
import logical_backup.db as db


def mock_devices(monkeypatch, devices: list) -> None:
    """
    Mock the devices being passed to the database
    """
    monkeypatch.setattr(db, "get_devices", lambda: devices)
