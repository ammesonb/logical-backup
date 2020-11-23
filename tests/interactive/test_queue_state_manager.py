"""
Test manager of state queue/context
"""
import multiprocessing
import time

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.interactive.action_executor import ActionExecutor
from logical_backup.interactive.queue_state_manager import QueueStateManager
from logical_backup.utilities.fake_lock import FakeLock
from logical_backup.utilities.testing import counter_wrapper


class SuccessAction(BaseAction):
    """
    A successful fake action
    """

    def _run(self) -> None:
        """
        Runs
        """
        self._add_message("A message")
        self._succeed()

    @property
    def name(self) -> str:
        """
        Name
        """
        return "Successful test"


class FailureAction(BaseAction):
    """
    A failed fake action
    """

    def _run(self) -> None:
        """
        Runs
        """
        self._fail("Thing went wrong")

    @property
    def name(self) -> str:
        """
        Name
        """
        return "Failed test"


def __mock_two_cpu_count(monkeypatch):
    """
    Sets CPU count to two
    """
    monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 2)


def test_creation(monkeypatch):
    """
    .
    """
    __mock_two_cpu_count(monkeypatch)
    queue = QueueStateManager(None, multiprocessing.Manager(), None, None, None)
    assert queue.thread_count == 2, "Thread count set"


def test_enqueue_action():
    """
    .
    """
    lock = FakeLock()
    queue = QueueStateManager(None, multiprocessing.Manager(), None, None, lock)
    queue.enqueue_actions([2, 1, 3])
    assert lock.acquired == 1 and lock.released == 1, "Lock acquired and released"

    assert queue.queue_length == 3, "Three actions added"
    assert queue.action_count == 3, "Three actions total"
    assert queue.queued_action_names == [
        "2",
        "1",
        "3",
    ], "Names are string versions of the actions"
    assert not queue.completed_action_count, "No actions completed"


def test_adding_removing_executors(monkeypatch):
    """
    .
    """
    __mock_two_cpu_count(monkeypatch)

    monkeypatch.setattr(ActionExecutor, "start", lambda self: None)
    monkeypatch.setattr(ActionExecutor, "is_alive", lambda self: True)
    queue = QueueStateManager(None, multiprocessing.Manager(), None, None, None)
    assert not queue.executor_count, "No executors yet"

    queue.add_executor()
    assert queue.executor_count == 1, "One executor"

    queue.add_executor()
    assert queue.executor_count == 2, "Two executors"

    queue.prune_dead_executors()
    assert queue.executor_count == 2, "No live executors removed"

    monkeypatch.setattr(ActionExecutor, "is_alive", lambda self: False)
    queue.prune_dead_executors()
    assert queue.executor_count == 0, "Dead executors get pruned"


def test_context_injection_via_set_threads(monkeypatch):
    """
    .
    """
    __mock_two_cpu_count(monkeypatch)

    context = {}
    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )
    assert context["thread_count"] == 2, "Thread count starts correct"
    queue.set_thread_count(4)
    assert context["thread_count"] == 4, "Thread count set correctly"


def test_average_action_ns(monkeypatch):
    """
    .
    """
    time_values = [100, 150, 350, 450]

    @counter_wrapper
    def get_time():
        return time_values[get_time.counter - 1]

    monkeypatch.setattr(time, "time_ns", get_time)

    context = {}

    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )

    action1 = SuccessAction()
    action1.process()
    action2 = SuccessAction()
    action2.process()

    context["completion_queue"].extend([action1, action2])

    assert queue.average_action_ns == 75, "Average completion time returned"


def test_get_completed_actions():
    """
    .
    """
    context = {}

    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )

    action1 = SuccessAction()
    action1.process()
    action2 = FailureAction()
    action2.process()

    context["completion_queue"].extend([action1, action2])

    assert queue.get_completed_action(0) == action1, "Action 1 returned"
    assert queue.get_completed_action(1) == action2, "Action 1 returned"

    completed = queue.completed_actions
    assert completed == [
        {
            "name": "Successful test",
            "succeeded": True,
            "error_count": 0,
            "message_count": 1,
        },
        {
            "name": "Failed test",
            "succeeded": False,
            "error_count": 1,
            "message_count": 0,
        },
    ], "Completed actions returned"
