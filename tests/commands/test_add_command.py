"""
Tests the add file command
"""
from pytest import fixture

from logical_backup.commands import AddCommand
from logical_backup.commands.add_command import AddConfig
from logical_backup.commands.command_validator import CommandValidator
from logical_backup import db
from logical_backup.objects import Device
from logical_backup.utilities import device_manager, files

from logical_backup.pretty_print import readable_bytes
from logical_backup.strings import DeviceArguments, Errors, Info
from logical_backup.utilities.testing import counter_wrapper

# pylint: disable=protected-access


@fixture(autouse=True)
def patch_connection(monkeypatch):
    """
    Sets device manager get connection to a no-op for tests
    """
    monkeypatch.setattr(device_manager, "get_connection", lambda: (None, None,))


# pylint: disable=bad-continuation,too-many-arguments
def __make_file_folder_case(
    description: str,
    argument_present: bool,
    entry_present: bool,
    in_db: bool,
    errors: list,
    adding_entry: bool,
) -> dict:
    return {
        "description": description,
        "has_argument": argument_present,
        "in_fs": entry_present,
        "in_db": in_db,
        "errors": errors,
        "adding_entry": adding_entry,
    }


def test_validate_file(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(CommandValidator, "get_file", lambda self: "/test")

    tests = [
        __make_file_folder_case(
            "Path does not exist", True, False, False, [Errors.NONEXISTENT_FILE], True
        ),
        __make_file_folder_case("File should be added", True, True, False, [], True),
        __make_file_folder_case(
            "File already backed up",
            True,
            True,
            True,
            [Errors.FILE_ALREADY_BACKED_UP_AT("/test")],
            True,
        ),
    ]

    for test in tests:
        monkeypatch.setattr(
            CommandValidator, "has_file", lambda self, test=test: test["has_argument"]
        )
        monkeypatch.setattr(
            CommandValidator, "file_exists", lambda self, test=test: test["in_fs"]
        )
        monkeypatch.setattr(db, "file_exists", lambda path, test=test: test["in_db"])

        command = AddCommand(None, None, None, None)
        config = command._validate_file()

        assert config.adding_file == test["adding_entry"], (
            "Adding file set for: " + test["description"]
        )
        assert command.errors == test["errors"], (
            "Errors set for: " + test["description"]
        )


def test_validate_folder(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(CommandValidator, "get_folder", lambda self: "/test")

    tests = [
        __make_file_folder_case(
            "Path does not exist", True, False, False, [Errors.NONEXISTENT_FOLDER], True
        ),
        __make_file_folder_case("Folder should be added", True, True, False, [], True),
        __make_file_folder_case(
            "Folder already backed up",
            True,
            True,
            True,
            [Errors.FOLDER_ALREADY_ADDED_AT("/test")],
            True,
        ),
    ]

    for test in tests:
        monkeypatch.setattr(
            CommandValidator, "has_folder", lambda self, test=test: test["has_argument"]
        )
        monkeypatch.setattr(
            CommandValidator, "folder_exists", lambda self, test=test: test["in_fs"]
        )
        monkeypatch.setattr(db, "get_folders", lambda path, test=test: test["in_db"])

        command = AddCommand(None, None, None, None)
        config = command._validate_folder(AddConfig())

        assert config.adding_folder == test["adding_entry"], (
            "Adding folder set for: " + test["description"]
        )
        assert command.errors == test["errors"], (
            "Errors set for: " + test["description"]
        )


def test_validate_device_missing(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(CommandValidator, "has_device", lambda self: False)
    command = AddCommand(None, None, None, None)
    config = command._validate_device(AddConfig())

    assert not config.adding_device, "No device added if not set"
    assert not config.to_specific_device, "Command not for a specific device if not set"


def test_validate_device_adding(monkeypatch):
    """
    .
    """

    empty_config = AddConfig()

    monkeypatch.setattr(CommandValidator, "has_device", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: False)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: False)

    command = AddCommand(None, None, None, None)
    config = command._validate_device(empty_config)
    assert (
        not config.adding_device
    ), "Should be adding device, but fail since nonexistent"
    assert not config.to_specific_device, "Not for a specific device, since adding"
    assert command.errors == [Errors.DEVICE_PATH_NOT_MOUNTED], "Device path not mounted"

    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: False)
    monkeypatch.setattr(CommandValidator, "get_device", lambda self: "/test")

    command = AddCommand(None, None, None, None)
    config = command._validate_device(empty_config)
    assert config.adding_device, "Should be adding device"
    assert not config.to_specific_device, "Not for a specific device, since adding"
    assert command.errors == [
        Errors.DEVICE_NOT_WRITEABLE_AT("/test")
    ], "Device path not writeable"

    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: True)

    command = AddCommand(None, None, None, None)
    config = command._validate_device(empty_config)
    assert config.adding_device, "Should be adding device"
    assert not config.to_specific_device, "Not for a specific device, since adding"
    assert not command.errors, "No errors"


def test_validate_specific_device(monkeypatch):
    """
    .
    """

    def make_file_config() -> AddConfig:
        return AddConfig(adding_file=True)

    monkeypatch.setattr(CommandValidator, "has_device", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: False)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: False)

    command = AddCommand(None, None, None, None)
    config = command._validate_device(make_file_config())
    assert not config.adding_device, "Not adding a new device"
    assert not config.to_specific_device, "Is a specific device, but invalid"
    assert command.errors == [Errors.DEVICE_PATH_NOT_MOUNTED], "Device path not mounted"

    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: False)
    monkeypatch.setattr(CommandValidator, "get_device", lambda self: "/test")

    command = AddCommand(None, None, None, None)
    config = command._validate_device(make_file_config())
    assert not config.adding_device, "Not adding a new device"
    assert not config.to_specific_device, "Is a specific device, but invalid"
    assert command.errors == [
        Errors.DEVICE_NOT_WRITEABLE_AT("/test")
    ], "Device path not writeable"

    monkeypatch.setattr(CommandValidator, "device_exists", lambda self: True)
    monkeypatch.setattr(CommandValidator, "device_writeable", lambda self: True)

    command = AddCommand(None, None, None, None)
    config = command._validate_device(make_file_config())
    assert not config.adding_device, "Not adding a new device"
    assert config.to_specific_device, "Is a specific device, but invalid"
    assert not command.errors, "Adding file to device is valid"

    command = AddCommand(None, None, None, None)
    config = command._validate_device(AddConfig(adding_folder=True))
    assert not config.adding_device, "Not adding a new device"
    assert config.to_specific_device, "Is a specific device, but invalid"
    assert not command.errors, "Adding folder to device is valid"


def test_validate(monkeypatch):
    """
    .
    """

    @counter_wrapper
    def validate_file(self):
        """
        .
        """
        return AddConfig()

    @counter_wrapper
    def validate_folder(self, config):
        """
        .
        """
        return config

    @counter_wrapper
    def validate_device(self, config):
        """
        .
        """
        return config

    monkeypatch.setattr(AddCommand, "_validate_file", validate_file)
    monkeypatch.setattr(AddCommand, "_validate_folder", validate_folder)
    monkeypatch.setattr(AddCommand, "_validate_device", validate_device)

    command = AddCommand(None, None, None, None)
    command._validate()

    assert validate_file.counter == 1, "File validation called once"
    assert validate_folder.counter == 1, "Folder validation called once"
    assert validate_device.counter == 1, "Device validation called once"


def test_create_actions(monkeypatch):
    """
    .
    """
    file_config = AddConfig(adding_file=True)

    monkeypatch.setattr(
        AddCommand, "_make_file_object", lambda self, path, config: None
    )
    monkeypatch.setattr(CommandValidator, "get_file", lambda self: "test")

    command = AddCommand(None, None, None, None)
    assert len(command._create_actions(file_config)) == 0, "No actions if no file made"

    monkeypatch.setattr(
        AddCommand, "_make_file_object", lambda self, path, config: "abc"
    )
    assert command._create_actions(file_config) == ["abc"], "Action returned"


def test_make_file_object_quick_fails(monkeypatch):
    """
    .
    """
    file_config = AddConfig(adding_file=True)

    monkeypatch.setattr(db, "file_exists", lambda path: True)

    command = AddCommand(None, None, None, None)
    assert (
        command._make_file_object("/test", file_config) is None
    ), "Fails if file already in db"
    assert command.errors == [Errors.FILE_ALREADY_BACKED_UP_AT("/test")], "Error added"

    monkeypatch.setattr(db, "file_exists", lambda path: False)

    def get_file_security(path):
        raise PermissionError("No access")

    monkeypatch.setattr(files, "get_file_security", get_file_security)

    command = AddCommand(None, None, None, None)
    assert (
        command._make_file_object("/test", file_config) is None
    ), "Fails if file already in db"
    assert command.errors == [Errors.CANNOT_READ_FILE_AT("/test")], "Error added"


def test_make_file_object_specific_device(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(
        files,
        "get_file_security",
        lambda path: {"permissions": "755", "owner": "test", "group": "grp"},
    )
    monkeypatch.setattr(files, "get_file_size", lambda path: 123)
    monkeypatch.setattr(CommandValidator, "get_device", lambda self: "/device")
    config = AddConfig(adding_file=True, to_specific_device=True)

    monkeypatch.setattr(AddCommand, "_check_device", lambda self, path, size: None)

    command = AddCommand(None, None, None, None)
    assert command._make_file_object("/test", config) is None, "No result returned"
    assert not len(command.errors), "No errors added, since check device would log them"
    assert command.messages == [
        Info.FILE_SIZE_OUTPUT_AT("/test", readable_bytes(123))
    ], "File size message added"

    monkeypatch.setattr(AddCommand, "_check_device", lambda self, path, size: path)

    device1 = Device()
    device1.set("dev1", "/device", "Device Serial", "12345", 1)
    device2 = Device()
    device2.set("dev2", "/dev2", "Device Serial", "23456", 1)

    # Ensure device 2 is skipped, since no match
    monkeypatch.setattr(db, "get_devices", lambda dev=None: [device2, device1])

    command = AddCommand(None, None, None, None)
    file_obj = command._make_file_object("/test", config)
    assert file_obj.device == device1, "Device 1 should be selected"
    assert file_obj.device_name == "dev1", "Device 1 chosen"
    assert not len(command.errors), "No errors added, since check device would log them"
    assert command.messages == [
        Info.FILE_SIZE_OUTPUT_AT("/test", readable_bytes(123))
    ], "File size message added"


def test_make_file_object_any_device(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(
        files,
        "get_file_security",
        lambda path: {"permissions": "755", "owner": "test", "group": "grp"},
    )
    monkeypatch.setattr(files, "get_file_size", lambda path: 123)
    monkeypatch.setattr(CommandValidator, "get_device", lambda self: "/device")
    config = AddConfig(adding_file=True, to_specific_device=False)
    monkeypatch.setattr(device_manager, "send_message", lambda *args, **kwargs: None)

    # Failure case
    class FailSocket:
        def recv(self, size: int):
            return str(DeviceArguments.RESPONSE_INVALID).encode()

    class FailDeviceManager:
        def errors(self, txid):
            return ["Bad command", "Invalid file size"]

    command = AddCommand(None, FailDeviceManager(), FailSocket(), None, "test-txid")
    assert command._make_file_object("/test", config) is None, "Error returned"
    assert (
        str(Info.AUTO_SELECT_DEVICE) in command.messages
    ), "Device being auto-selected"
    assert command.errors == [
        Errors.INVALID_COMMAND(
            device_manager.format_message(DeviceArguments.COMMAND_GET_DEVICE, ["123"])
        ),
        "Bad command",
        "Invalid file size",
    ], "Error message added"

    # Success case
    class SuccessSocket:
        def recv(self, size: int):
            return device_manager.format_message(
                DeviceArguments.RESPONSE_SUBSTITUTE, ["/device"]
            ).encode()

    class SuccessDeviceManager:
        def errors(self, txid):
            return []

    device1 = Device()
    device1.set("dev1", "/device", "Device Serial", "12345", 1)
    device2 = Device()
    device2.set("dev2", "/dev2", "Device Serial", "23456", 1)

    # Ensure device 2 is skipped, since no match
    monkeypatch.setattr(db, "get_devices", lambda dev=None: [device2, device1])

    command = AddCommand(
        None, SuccessDeviceManager(), SuccessSocket(), None, "test-txid"
    )
    file_obj = command._make_file_object("/test", config)
    assert not len(command.errors), "No errors added"
    assert file_obj.device == device1, "Device 1 selected"
    assert file_obj.device_name == "dev1", "Device name correct"
    assert (
        str(Info.AUTO_SELECT_DEVICE) in command.messages
    ), "Device being auto-selected"
