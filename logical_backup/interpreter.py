"""
Handles text autocompletion for inputs
"""
from os import path as os_path
import glob
import readline

from logical_backup.strings import Commands, Targets

commands = [
    Commands.ADD.value,
    Commands.RESTORE.value,
    Commands.MOVE.value,
    Commands.UPDATE.value,
    Commands.VERIFY.value,
    Commands.REMOVE.value,
]

command_parameters = {
    "add": [Targets.FILE.value, Targets.FOLDER, Targets.DEVICE.value],
    "restore": [Targets.FILE.value, Targets.FOLDER, Targets.ALL.value],
    "verify": [Targets.FILE.value, Targets.FOLDER, Targets.ALL.value],
    "update": [Targets.FILE.value, Targets.FOLDER.value],
    "remove": [Targets.FILE.value, Targets.FOLDER.value],
    "move": [
        Targets.FILE.value,
        Targets.FOLDER,
        Targets.DEVICE,
        Targets.MOVE_PATH.value,
    ],
}


def get_files(text: str) -> list:
    """
    Match a file input
    """
    return [path for path in glob.glob(text + "*") if path.startswith(text)]


def get_folders(text: str) -> list:
    """
    Match a folder input
    """
    return [
        path
        for path in glob.glob(text + "*")
        if os_path.isdir(path) and path.startswith(text)
    ]


def get_device(text: str) -> list:
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
            options = get_files(path)
        elif detail in ["--folder", "--move-path"]:
            options = get_folders(path)
        elif detail == "--device":
            options = get_device(path)

    return None if state >= len(options) else options[state]


def set_completion() -> None:
    """
    Set input completion
    """
    readline.parse_and_bind("tab: complete")
    readline.set_completer(match_input)
    readline.set_completer_delims(" \t")
