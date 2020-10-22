"""
Tests for the add file action
"""
import hashlib
import os
from os import path as os_path
import tempfile

from logical_backup import db
from logical_backup.commands.actions import AddFileAction
from logical_backup.objects import File, Device
from logical_backup.strings import Errors, Info
from logical_backup.utilities import files
from logical_backup.utilities.testing import counter_wrapper


def get_file_obj(create_file: bool = False, data: str = None, size: int = 1024):
    """
    Makes a file object, optionally creating a real file
    """
    device = Device()
    device.set("device", "", "Device Serial", "12345", 1)
    if create_file:
        device.device_path = tempfile.mkdtemp()
        descriptor, name = tempfile.mkstemp(dir=device.device_path)
        file_handle = open(descriptor, "wb")
        if not data:
            data = os.urandom(size)
        file_handle.write(data)
        file_handle.close()

        checksum = hashlib.md5(data).hexdigest()
    else:
        name = "foo"
        checksum = ""

    file_obj = File()
    file_obj.set_properties(name + ".bak", name, checksum)
    file_obj.set_security("644", "user", "group")
    file_obj.device = device
    file_obj.device_name = "device"

    return file_obj


def test_failed_first_checksum(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(files, "checksum_file", lambda path: "")
    file_obj = get_file_obj()
    action = AddFileAction(file_obj)
    action.process()
    assert action.errors == [
        Errors.FAILED_GET_CHECKSUM_FOR(file_obj.file_path)
    ], "Error set as expected"
    # Ensure False, not None
    # pylint: disable=singleton-comparison
    assert action.success == False, "Action set to failed"


def test_mismatched_checksum(monkeypatch):
    """
    .
    """
    checksum_func = files.checksum_file

    @counter_wrapper
    def checksum_file(file_path: str) -> str:
        """
        Overrides checksum file for second call
        """
        return checksum_func(file_path) if checksum_file.counter == 1 else ""

    monkeypatch.setattr(files, "checksum_file", checksum_file)
    file_obj = get_file_obj(True)
    action = AddFileAction(file_obj)
    action.process()

    os.remove(file_obj.file_path)

    assert action.messages == [Info.COPYING_FILE(file_obj.file_path)], "Messages added"
    assert action.errors == [
        Errors.CHECKSUM_MISMATCH_AFTER_COPY_FOR(file_obj.file_path)
    ], "Error set as expected"
    # Ensure False, not None
    # pylint: disable=singleton-comparison
    assert action.success == False, "Action set to failed"
    assert not os_path.isfile(
        os_path.join(file_obj.device.device_path, file_obj.file_name)
    ), "Back up file should be removed"

    os.removedirs(file_obj.device.device_path)


def test_db_save_failure(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "add_file", lambda file_obj: False)
    file_obj = get_file_obj(True)
    action = AddFileAction(file_obj)
    action.process()

    os.remove(file_obj.file_path)

    assert action.messages == [
        Info.COPYING_FILE(file_obj.file_path),
        str(Info.SAVING_FILE_TO_DB),
    ], "Messages added"
    assert action.errors == [
        str(Errors.FAILED_ADD_FILE_DB(file_obj.file_path))
    ], "Error set is DB fail"
    # Ensure False, not None
    # pylint: disable=singleton-comparison
    assert action.success == False, "Action set to failed"
    assert not os_path.isfile(
        os_path.join(file_obj.device.device_path, file_obj.file_name)
    ), "Back up file should be removed"

    os.removedirs(file_obj.device.device_path)


def test_action_success(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "add_file", lambda file_obj: db.DatabaseError.SUCCESS)
    file_obj = get_file_obj(True)
    action = AddFileAction(file_obj)
    action.process()

    os.remove(file_obj.file_path)

    backup_path = os_path.join(file_obj.device.device_path, file_obj.file_name)
    assert action.messages == [
        Info.COPYING_FILE(file_obj.file_path),
        str(Info.SAVING_FILE_TO_DB),
        Info.FILE_SAVED(file_obj.file_path),
    ], "Messages added"
    assert action.errors == [], "No errors set"
    # Ensure True, not some other value
    # pylint: disable=singleton-comparison
    assert action.success == True, "Action succeeded"
    assert os_path.isfile(backup_path), "Back up file should be present"

    os.remove(backup_path)
    os.removedirs(file_obj.device.device_path)


def test_name(monkeypatch):
    """
    .
    """
    file_obj = get_file_obj(True)
    action = AddFileAction(file_obj)
    assert action.name == Info.ADD_FILE_NAME(
        file_obj.file_path
    ), "File name set correctly"
