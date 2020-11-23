"""
Test base command
"""
from datetime import datetime
import socket
import time

from dateutil import tz
from pytest import raises

from logical_backup.commands.base_command import BaseCommand, Config
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

    def _create_actions(self, config: Config):
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
        command._create_actions(Config())
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


def test_logs(monkeypatch):
    """
    .
    """
    sock = socket.socket()
    command = ImplementedCommand([], None, sock, None)
    assert command.logs == [], "No logs added"
    first_epoch_timestamp = 1603919796
    second_epoch_timestamp = 1603919896
    third_epoch_timestamp = 1603919996

    local = tz.tzlocal()
    eastern = tz.gettz("America/New_York")

    monkeypatch.setattr(time, "time", lambda: first_epoch_timestamp)
    first_timestamp = (
        datetime.fromtimestamp(time.time())
        .replace(tzinfo=local)
        .astimezone(eastern)
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    command._add_message("foo")

    monkeypatch.setattr(time, "time", lambda: second_epoch_timestamp)
    second_timestamp = (
        datetime.fromtimestamp(time.time())
        .replace(tzinfo=local)
        .astimezone(eastern)
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    command._add_error("bar")

    monkeypatch.setattr(time, "time", lambda: third_epoch_timestamp)
    third_timestamp = (
        datetime.fromtimestamp(time.time())
        .replace(tzinfo=local)
        .astimezone(eastern)
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    command._add_message("baz")

    assert command.logs == [
        first_timestamp + " foo",
        second_timestamp + " bar",
        third_timestamp + " baz",
    ], "Messages and timestamp match"
