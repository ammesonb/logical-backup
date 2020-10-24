"""
Test argument utilities
"""
from pytest import raises

from logical_backup.strings import Commands
from logical_backup.utilities import arguments


def test_interactive_arguments():
    """
    .
    """
    parser = arguments.get_argument_parser(True)

    parsed = parser.parse_args([str(Commands.ADD)])
    assert parsed.action == str(Commands.ADD), "Shared action parsed"

    parsed = parser.parse_args([str(Commands.EXIT)])
    assert parsed.action == str(Commands.EXIT), "Exit action parsed"

    with raises(SystemExit):
        parsed = parser.parse_args([str(Commands.INTERACTIVE)])


def test_command_line_arguments():
    """
    .
    """
    parser = arguments.get_argument_parser(False)

    parsed = parser.parse_args([str(Commands.ADD)])
    assert parsed.action == str(Commands.ADD), "Shared action parsed"

    parsed = parser.parse_args([str(Commands.INTERACTIVE)])
    assert parsed.action == str(Commands.INTERACTIVE), "Interactive action parsed"

    with raises(SystemExit):
        parsed = parser.parse_args([str(Commands.EXIT)])
