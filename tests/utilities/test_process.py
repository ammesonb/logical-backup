"""
Tests for process input/output functions
"""
from logical_backup.utilities import process


def test_run_command():
    """
    .
    """
    result = process.run_command(["echo", "hello world"])
    assert result["stdout"] == b"hello world\n", "Echo should output hello world"
    assert result["exit_code"] == 0, "Echo should not fail"

    result = process.run_command(["cat", "no_such_file"])
    assert result["exit_code"] != 0, "Can't cat non-existent file"


def test_run_piped_command():
    """
    .
    """
    result = process.run_piped_command([["echo", "hello_world"], ["sed", "s/_/ /"]])
    assert result["stdout"] == b"hello world\n", "Echo should output hello world"
    assert result["exit_code"] == 0, "Echo should not fail"

    result = process.run_piped_command([["echo", "hello_world"], ["cat", "no_file"]])
    assert result["exit_code"] != 0, "Can't cat non-existent file"
