"""
Process interaction/output helpers
"""
from subprocess import run, Popen, PIPE


def run_command(command: list) -> dict:
    """
    Executes a simple command

    Parameters
    ----------
    command : list
        The command to execute, grouped by parameters

    Returns
    -------
    dict
        With "exit_code", "stdout" and "stderr" properties
    """
    process = run(command, stdout=PIPE, stderr=PIPE, check=False)
    stdout, stderr = process.stdout, process.stderr
    return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr}


def run_piped_command(commands: list) -> dict:
    """
    Executes a list of list of commands, piping one into the next

    Parameters
    ----------
    commands : list
        A list of list of commands, to chain

    Returns
    -------
    dict
        With "exit_code", "stdout" and "stderr" properties
    """
    previous = None
    for command in commands:
        previous = Popen(
            command,
            stdout=PIPE,
            stdin=previous.stdout if previous else None,
            stderr=previous.stderr if previous else None,
        )

    out, err = previous.communicate()
    return {"exit_code": previous.returncode, "stdout": out, "stderr": err}
