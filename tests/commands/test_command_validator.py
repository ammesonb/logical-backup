"""
Tests the command validator
"""
import os
from os import path as os_path
import tempfile

from logical_backup.commands.command_validator import CommandValidator
from logical_backup.strings import Arguments


def __make_arguments(*args, **kwargs):
    """
    Makes arguments based off of kwargs
    """
    arguments = {
        Arguments.FILE: None,
        Arguments.FOLDER: None,
        Arguments.DEVICE: None,
        Arguments.FROM_DEVICE: None,
        Arguments.MOVE_PATH: None,
        Arguments.ALL: None,
    }

    arguments.update(**kwargs)
    return arguments


def test_all():
    """
    .
    """
    validator = CommandValidator(__make_arguments())
    assert validator.get_all() is None, "All is not set"
    assert not validator.is_all(), "Is not all"

    validator = CommandValidator(__make_arguments(all=True))
    assert validator.get_all(), "All is True"
    assert validator.is_all(), "Is all"


def test_file():
    """
    .
    """
    validator = CommandValidator(__make_arguments())
    assert validator.get_file() is None, "File not set"
    assert not validator.has_file(), "No file"
    assert not validator.file_exists(), "Empty file does not exist"

    validator = CommandValidator(__make_arguments(file="foo"))
    assert validator.get_file() == "foo", "File matches"
    assert validator.has_file(), "File is added"
    assert not validator.file_exists(), "File does not exist"

    descriptor, filename = tempfile.mkstemp()
    validator = CommandValidator(__make_arguments(file=filename))
    assert validator.get_file() == filename, "File matches"
    assert validator.has_file(), "File is added"
    assert validator.file_exists(), "File exists"

    os.remove(filename)


def test_folder():
    """
    .
    """
    validator = CommandValidator(__make_arguments())
    assert validator.get_folder() is None, "Folder not set"
    assert not validator.has_folder(), "No folder"
    assert not validator.folder_exists(), "Empty folder does not exist"

    validator = CommandValidator(__make_arguments(folder="foo"))
    assert validator.get_folder() == "foo", "Folder matches"
    assert validator.has_folder(), "Folder is added"
    assert not validator.folder_exists(), "Folder does not exist"

    foldername = tempfile.mkdtemp()
    validator = CommandValidator(__make_arguments(folder=foldername))
    assert validator.get_folder() == foldername, "Folder matches"
    assert validator.has_folder(), "Folder is added"
    assert validator.folder_exists(), "Folder exists"

    os.removedirs(foldername)


def test_device(monkeypatch):
    """
    .
    """
    validator = CommandValidator(__make_arguments())
    assert validator.get_device() is None, "Device not set"
    assert not validator.has_device(), "No device"
    assert not validator.device_exists(), "Empty device does not exist"

    device_path = tempfile.mkdtemp()
    monkeypatch.setattr(os_path, "ismount", lambda path: path == device_path)
    validator = CommandValidator(__make_arguments(device="foo"))
    assert validator.get_device() == "foo", "Device matches"
    assert validator.has_device(), "Device is added"
    assert not validator.device_exists(), "Device does not exist"

    validator = CommandValidator(__make_arguments(device=device_path))
    assert validator.get_device() == device_path, "Device matches"
    assert validator.has_device(), "Device is added"
    assert validator.device_exists(), "Device exists"

    monkeypatch.setattr(os, "access", lambda path, mode: False)
    assert not validator.device_writeable(), "Device not writeable"
    monkeypatch.setattr(os, "access", lambda path, mode: True)
    assert validator.device_writeable(), "Device writeable"

    os.removedirs(device_path)
