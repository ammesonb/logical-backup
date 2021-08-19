"""
Handles text autocompletion for inputs
"""
from os import path as os_path
import glob
import readline

from logical_backup.strings import Commands, Targets

commands = [
    str(Commands.ADD),
    str(Commands.RESTORE),
    str(Commands.MOVE),
    str(Commands.UPDATE),
    str(Commands.VERIFY),
    str(Commands.REMOVE),
    str(Commands.STATUS),
    str(Commands.SET_THREADS),
    str(Commands.REORDER),
    str(Commands.CLEAR),
    str(Commands.HELP),
    str(Commands.MESSAGES),
    str(Commands.EXIT),
]

command_parameters = {
    str(Commands.ADD): [str(Targets.FILE), str(Targets.FOLDER), str(Targets.DEVICE)],
    str(Commands.RESTORE): [str(Targets.FILE), str(Targets.FOLDER), str(Targets.ALL)],
    str(Commands.VERIFY): [str(Targets.FILE), str(Targets.FOLDER), str(Targets.ALL)],
    str(Commands.UPDATE): [str(Targets.FILE), str(Targets.FOLDER)],
    str(Commands.REMOVE): [str(Targets.FILE), str(Targets.FOLDER)],
    str(Commands.MOVE): [
        str(Targets.FILE),
        str(Targets.FOLDER),
        str(Targets.DEVICE),
        str(Targets.MOVE_PATH),
    ],
}


def _append_slash_to_directory(path: str) -> str:
    """
    Checks if path is a directory, and if so, appends a slash
    Makes for easier auto-completion of file system directories
    """
    return path + ("/" if os_path.isdir(path) else "")


def _get_files(text: str) -> list:
    """
    Match a file input
    """
    return [path for path in glob.glob(text + "*") if path.startswith(text)]


def _get_folders(text: str) -> list:
    """
    Match a folder input
    """
    return [
        path
        for path in glob.glob(text + "*")
        if os_path.isdir(path) and path.startswith(text)
    ]


def _get_device(text: str) -> list:
    """
    Match a device input
    """
    return [
        path
        for path in glob.glob(text + "*")
        if (os_path.isdir(path) or os_path.ismount(path)) and path.startswith(text)
    ]


def match_input(text: str, state: int) -> list:
    """
    Matches input to possible options
    """
    text = readline.get_line_buffer()
    options = []
    if " " not in text:
        options = [command for command in commands if command.startswith(text)]
    elif text.count(" ") < 2:
        tokens = text.split(" ")
        command = tokens[0]
        path = tokens[1] if len(tokens) > 1 else ""
        if command not in commands:
            options = []
        else:
            for parameter in command_parameters[command]:
                if parameter.startswith(path):
                    options.append(parameter)
    else:
        detail = text.split(" ")[-2]
        path = text.split(" ")[-1]

        if detail == "--file":
            options = _get_files(path)
        elif detail in ["--folder", "--move-path"]:
            options = _get_folders(path)
        elif detail == "--device":
            options = _get_device(path)

        options = [_append_slash_to_directory(path) for path in options]

    return None if state >= len(options) else options[state]


def set_completion() -> None:
    """
    Set input completion
    """
    readline.parse_and_bind("tab: complete")
    readline.set_completer(match_input)
    readline.set_completer_delims(" \t")
