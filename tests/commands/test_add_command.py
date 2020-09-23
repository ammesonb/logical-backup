"""
Tests the add file command
"""
from logical_backup.commands import AddCommand
from logical_backup.commands.command_validator import CommandValidator
from logical_backup import db
from logical_backup.utilities import device_manager

from logical_backup.strings import Errors

# pylint: disable=protected-access


# pylint: disable=bad-continuation,too-many-arguments
def __make_file_folder_case(
    description: str,
    argument_present: bool,
    entry_present: bool,
    in_db: bool,
    errors: list,
    adding_file: bool,
) -> dict:
    return {
        "description": description,
        "has_argument": argument_present,
        "in_fs": entry_present,
        "in_db": in_db,
        "errors": errors,
        "adding_file": adding_file,
    }


def test_validate_file(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(device_manager, "get_connection", lambda: (None, None,))
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
        command._validate_file()

        assert command._adding_file == test["adding_file"], (
            "Adding file set for: " + test["description"]
        )
        assert command.errors == test["errors"], (
            "Errors set for: " + test["description"]
        )
