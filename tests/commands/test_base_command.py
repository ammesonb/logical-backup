"""
Test base command
"""
import socket

from pytest import raises

from logical_backup.commands.base_command import BaseCommand
from logical_backup.strings import Errors

# pylint: disable=protected-access


# Intentionally omitted for testing here
# pylint: disable=abstract-method
class Command(BaseCommand):
    """
    Test command
    """

    def _validate(self):
        """
        Overrides validate
        """
        return


class ImplementedCommand(Command):
    """
    Command that won't error
    """

    def _create_actions(self):
        """
        Overrides create actions
        """
        self._actions = ["stuff"]


def test_validate_not_implemented():
    """
    Ensures validate throws not implemented
    """
    sock = socket.socket()
    command = BaseCommand([], None, sock, None)
    with raises(NotImplementedError) as error:
        command._validate()
        assert (
            str(error) == Errors.COMMAND_VALIDATE_NOT_IMPLEMENTED
        ), "Exception message is correct"


def test_create_action_not_implemented():
    """
    Ensures create action throws not implemented
    """

    sock = socket.socket()
    command = Command([], None, sock, None)
    with raises(NotImplementedError) as error:
        command._create_actions()
        assert (
            str(error) == Errors.COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED
        ), "Exception message is correct"


def test_messages():
    """
    .
    """
    sock = socket.socket()
    command = ImplementedCommand([], None, sock, None)
    assert command.messages == [], "No messages in list"
    command._add_message("foo")
    assert command.messages == ["foo"], "Message added"


def test_errors():
    """
    .
    """
    sock = socket.socket()
    command = ImplementedCommand([], None, sock, None)
    assert command.errors == [], "No errors in list"
    command._add_error("err")
    assert command.errors == ["err"], "Error added"


def test_actions():
    """
    Get actions in happy case
    """
    sock = socket.socket()
    command = ImplementedCommand([], None, sock, None)
    assert not command.has_actions, "No actions yet"
    assert command._actions == [], "Does not have actions"

    assert command.actions == ["stuff"], "Action added when called"


def test_actions_with_errors():
    """
    No actions if errors
    """
    sock = socket.socket()
    command = ImplementedCommand([], None, sock, None)
    command._add_error("Err")
    assert not command.has_actions, "No actions yet"
    assert command._actions == [], "Does not have actions"

    assert command.actions == [], "No actions if errors"
