"""
Tests base action
"""
from pytest import raises

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.strings import Errors

# pylint: disable=protected-access


def test_methods_not_implemented():
    """
    .
    """
    action = BaseAction()
    with raises(NotImplementedError) as error:
        action.process()
        assert str(error) == str(
            Errors.ACTION_RUN_NOT_IMPLEMENTED
        ), "Correct error message for run"

    with raises(NotImplementedError) as error:
        name = action.name
        assert str(error) == str(
            Errors.ACTION_NAME_NOT_IMPLEMENTED
        ), "Correct error message for set name"


def test_messages():
    """
    .
    """
    action = BaseAction()
    assert action.messages == [], "No messages yet"
    action._add_message("foo")
    assert action.messages == ["foo"], "Message added"


def test_errors():
    """
    .
    """
    action = BaseAction()
    assert action.errors == [], "No errors yet"
    action._add_error("err")
    assert action.errors == ["err"], "Error added"


def test_fail():
    """
    .
    """
    action = BaseAction()
    # Ensure value is actually None
    # pylint: disable=singleton-comparison
    assert action.success == None, "Success not set"
    action._fail("Fatal")
    # Ensure value is False, not None
    # pylint: disable=singleton-comparison
    assert action.success == False, "Success is False"
    assert action.errors == ["Fatal"], "Failure reason added"


def test_timing_and_started(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(BaseAction, "_run", lambda *args, **kwargs: None)
    action = BaseAction()
    assert not action.started, "Action not started"
    assert action.completion_nanoseconds == -1, "Completion time not set"
    action.process()
    assert action.completion_nanoseconds > 0, "Completion time set"
    assert action.started, "Action started"
