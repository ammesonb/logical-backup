"""
Test main script entry point
"""

from logical_backup.utility import run_command


def test_help():
    """
    Test help is printed and exits normally
    """
    result = run_command(["python3", "logical_backup_script.py", "-h"])
    assert result["exit_code"] == 0, "Result should pass for help flag"
    assert "usage: logical_backup_script.py" in result["stdout"].decode(
        "utf-8"
    ), "Usage should be printed"


def test_missing_action():
    """
    Test missing the action
    """
    result = run_command(["python3", "logical_backup_script.py"])
    assert result["exit_code"] == 2, "Result should fail if missing the acton"


def test_unrecognized_action():
    """
    Test an action which isn't in the command set
    """
    result = run_command(["python3", "logical_backup_script.py", "unrecognized"])
    assert result["exit_code"] == 2, "Result should fail if the action is unrecognized"


def test_invalid_command():
    """
    Test an invalid command
    """
    result = run_command(["python3", "logical_backup_script.py", "add"])
    assert result["exit_code"] == 1, "Result should fail if missing file/folder"
