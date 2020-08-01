"""
Tests base action
"""
from pytest import raises

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.strings import Errors


def test_run_not_implemented():
    """
    .
    """
    action = BaseAction()
    with raises(NotImplementedError) as error:
        action.run()
        assert str(error) == str(
            Errors.ACTION_RUN_NOT_IMPLEMENTED
        ), "Correct error message"


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
    assert action.success == None, "Success not set"
    action._fail("Fatal")
    assert action.success == False, "Success is False"
    assert action.errors == ["Fatal"], "Failure reason added"