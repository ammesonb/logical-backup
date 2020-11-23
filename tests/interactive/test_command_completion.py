"""
Tests the intelligent completion of commands
"""
import glob
from os import path as os_path
import readline

from logical_backup.interactive import command_completion
from logical_backup.utility import counter_wrapper
from logical_backup.strings import Commands

# pylint: disable=protected-access


def test_get_files_filters(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(glob, "glob", lambda path: ["bar", "baz", "foo"])
    print(command_completion._get_files("ba"))
    assert command_completion._get_files("ba") == [
        "bar",
        "baz",
    ], "get_files filters appropriately"
    assert command_completion._get_files("no match") == [], "get_files returns no match"


def test_get_folders_filters(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(glob, "glob", lambda path: ["bar", "baz", "foo"])
    monkeypatch.setattr(os_path, "isdir", lambda path: path in ["bar", "foo"])
    assert command_completion._get_folders("ba") == [
        "bar"
    ], "get_folders filters appropriately"
    assert (
        command_completion._get_folders("no match") == []
    ), "get_folders returns no match"


def test_get_device(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(glob, "glob", lambda path: ["bar", "baz", "foo"])
    monkeypatch.setattr(os_path, "isdir", lambda path: path == "bar")
    monkeypatch.setattr(os_path, "ismount", lambda path: path in ["baz", "foo"])
    # pylint: disable=bad-continuation
    assert command_completion._get_device("ba") == [
        "bar",
        "baz",
    ], "get_device filters appropriately"
    assert (
        command_completion._get_device("no match") == []
    ), "get_device returns no match"


def test_set_completion(monkeypatch):
    """
    .
    """

    @counter_wrapper
    # pylint: disable=unused-argument
    def parse_func(key_binding):
        """
        .
        """
        return

    @counter_wrapper
    # pylint: disable=unused-argument
    def completer_func(func):
        """
        .
        """
        return

    @counter_wrapper
    # pylint: disable=unused-argument
    def delims_func(delims):
        """
        .
        """
        return

    monkeypatch.setattr(readline, "parse_and_bind", parse_func)
    monkeypatch.setattr(readline, "set_completer", completer_func)
    monkeypatch.setattr(readline, "set_completer_delims", delims_func)

    command_completion.set_completion()
    assert parse_func.counter == 1, "Parse and bind called"
    assert completer_func.counter == 1, "Completion setter called"
    assert delims_func.counter == 1, "Completion delims set"


def __patch_readline_input(monkeypatch, text: str):
    """
    Modifies readline buffer to return given text
    """
    monkeypatch.setattr(readline, "get_line_buffer", lambda: text)


def test_command_completion(monkeypatch):
    """
    .
    """
    __patch_readline_input(monkeypatch, "")
    for index in range(len(command_completion.commands)):
        assert command_completion.match_input("", index) == str(
            command_completion.commands[index]
        )

    __patch_readline_input(monkeypatch, "ad")
    assert command_completion.match_input("ad", 0) == str(
        Commands.ADD
    ), "Partial match works"

    __patch_readline_input(monkeypatch, "add")
    assert command_completion.match_input("add", 0) == str(
        Commands.ADD
    ), "Exact match works"

    __patch_readline_input(monkeypatch, "addinvalid")
    assert not command_completion.match_input("addinvalid", 0), "Invalid command fails"

    __patch_readline_input(monkeypatch, "add")
    assert not command_completion.match_input("add", 1), "Going past result set fails"


def test_command_parameters_correct(monkeypatch):
    """
    .
    """
    # pylint: disable=bad-continuation
    for command in [
        str(Commands.ADD),
        str(Commands.RESTORE),
        str(Commands.VERIFY),
        str(Commands.UPDATE),
        str(Commands.REMOVE),
        str(Commands.MOVE),
    ]:
        __patch_readline_input(monkeypatch, str(command) + " ")
        parameter_options = []
        command_parameters = command_completion.command_parameters[command]
        for index in range(len(command_parameters)):
            parameter_options.append(
                command_completion.match_input(command + " ", index)
            )

        assert (
            parameter_options == command_parameters
        ), "Correct parameters returned as options"

    __patch_readline_input(monkeypatch, "wrong ")
    assert not command_completion.match_input(
        "wrong ", 0
    ), "Nothing returned for unknown command"


def test_command_parameter_filtering(monkeypatch):
    """
    .
    """
    __patch_readline_input(monkeypatch, "add --")
    options = command_completion.command_parameters[str(Commands.ADD)]
    i = 0
    for opt in options:
        assert (
            command_completion.match_input(str(Commands.ADD) + " --", i) == opt
        ), "Add parameter matches with dash inputs"
        i += 1

    __patch_readline_input(monkeypatch, "add --f")
    options = [
        param
        for param in command_completion.command_parameters[str(Commands.ADD)]
        if param.startswith("--f")
    ]
    i = 0
    for opt in options:
        assert (
            command_completion.match_input(str(Commands.ADD) + " --f", i) == opt
        ), "Parameters match with filtered input"
        i += 1

    assert (
        not command_completion.match_input(str(Commands.ADD) + " --", i) == opt
    ), "No extra options after end of filtered results"


def test_file_system_completion(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(command_completion, "_get_files", lambda path: ["bar", "baz"])
    monkeypatch.setattr(command_completion, "_get_folders", lambda path: [])
    monkeypatch.setattr(command_completion, "_get_device", lambda path: [])

    __patch_readline_input(monkeypatch, "add --file ")
    assert (
        command_completion.match_input("add --file ", 0) == "bar"
    ), "First file returned"
    assert (
        command_completion.match_input("add --file ", 1) == "baz"
    ), "Second file returned"
    __patch_readline_input(monkeypatch, "add --folder ")
    assert not command_completion.match_input("add --folder ", 0), "No folder returned"
    __patch_readline_input(monkeypatch, "add --device ")
    assert not command_completion.match_input("add --device ", 0), "No device returned"

    monkeypatch.setattr(command_completion, "_get_files", lambda path: [])
    monkeypatch.setattr(command_completion, "_get_folders", lambda path: ["tmp", "var"])

    __patch_readline_input(monkeypatch, "add --file ")
    assert (
        not command_completion.match_input("add --file ", 0) == "bar"
    ), "No file returned"
    __patch_readline_input(monkeypatch, "add --folder ")
    assert (
        command_completion.match_input("add --folder ", 0) == "tmp"
    ), "First folder returned"
    assert (
        command_completion.match_input("add --folder ", 1) == "var"
    ), "Second folder returned"
    __patch_readline_input(monkeypatch, "add --device ")
    assert not command_completion.match_input("add --device ", 0), "No device returned"

    monkeypatch.setattr(command_completion, "_get_folders", lambda path: [])
    monkeypatch.setattr(
        command_completion, "_get_device", lambda path: ["/dev1", "/dev2"]
    )

    __patch_readline_input(monkeypatch, "add --file ")
    assert (
        not command_completion.match_input("add --file ", 0) == "bar"
    ), "No file returned"
    __patch_readline_input(monkeypatch, "add --folder ")
    assert not command_completion.match_input("add --folder ", 0), "No folder returned"
    __patch_readline_input(monkeypatch, "add --device ")
    assert (
        command_completion.match_input("add --device ", 0) == "/dev1"
    ), "First device returned"
    assert (
        command_completion.match_input("add --device ", 1) == "/dev2"
    ), "Second folder returned"
