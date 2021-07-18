"""
Test manager of state queue/context
"""
import multiprocessing
import time

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.interactive.action_executor import ActionExecutor
from logical_backup.interactive.queue_state_manager import QueueStateManager
from logical_backup.utilities import device_manager
from logical_backup.utilities.fake_lock import FakeLock
from logical_backup.strings import Errors, Info
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


def test_clear_completed_actions(monkeypatch, capsys):
    """
    .
    """
    context = {}

    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: False)

    queue.clear_completed_actions()
    output = capsys.readouterr()
    assert str(Errors.UNABLE_TO_ACQUIRE) in output.out, "Lock acquire failure prints"

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: True)

    action1 = SuccessAction()
    action1.process()
    action2 = FailureAction()
    action2.process()

    context["completion_queue"].extend([action1, action2])
    context["queue"].append(action1)

    assert queue.completed_action_count == 2, "Actions marked as completed"
    assert queue.queue_length == 1, "Action in queue"
    assert queue.action_count == 3, "Total actions correct"

    queue.clear_completed_actions()

    assert queue.completed_action_count == 0, "No actions in completed queue"
    assert queue.queue_length == 1, "Still one action in queue"
    assert queue.action_count == 1, "Total action count lowered"
    assert queue.completed_actions == [], "Completed actions cleared"
    assert queue.get_queued_action(0) == action1, "Action 1 still in queue"


def test_dequeue_action(monkeypatch, capsys):
    """
    .
    """
    context = {}

    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: False)

    action1 = SuccessAction()
    action1.process()
    action2 = FailureAction()
    action2.process()
    action3 = SuccessAction()
    action3.process()
    action4 = FailureAction()
    action4.process()
    action5 = FailureAction()
    action5.process()

    context["queue"].extend([action1, action2, action3, action4, action5])

    queue.dequeue_actions([2, 3])
    output = capsys.readouterr()
    assert str(Errors.UNABLE_TO_ACQUIRE) in output.out, "Lock acquire failure prints"

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: True)

    queue.dequeue_actions([2, 4])
    assert queue.action_count == 3, "Three actions left"
    assert queue.get_queued_action(0) == action1, "First entry is action 1"
    assert queue.get_queued_action(1) == action3, "Second entry is action 3"
    assert queue.get_queued_action(2) == action5, "Third entry is action 5"

    queue.dequeue_actions([2, 1])
    assert queue.action_count == 1, "One action left"
    assert queue.get_queued_action(0) == action5, "Entry is action 5"


def test_reorder_queue(monkeypatch, capsys):
    """
    .
    """
    context = {}

    lock = FakeLock()
    queue = QueueStateManager(
        None, multiprocessing.Manager(), None, None, lock, context
    )

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: False)

    class NumberedAction(BaseAction):
        """
        A numbered fake action
        """

        def __init__(self, number: int, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            self.__number = number

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
            return str(self.__number)

    action1 = NumberedAction(1)
    action1.process()
    action2 = NumberedAction(2)
    action2.process()
    action3 = NumberedAction(3)
    action3.process()
    action4 = NumberedAction(4)
    action4.process()
    action5 = NumberedAction(5)
    action5.process()

    context["queue"].extend([action1, action2, action3, action4, action5])

    queue.move_queue_entries([2, 3], 4)
    output = capsys.readouterr()
    assert str(Errors.UNABLE_TO_ACQUIRE) in output.out, "Lock acquire failure prints"

    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: True)

    queue.move_queue_entries([2, 3], 5)
    assert queue.queued_action_names == [
        "1",
        "4",
        "2",
        "3",
        "5",
    ], "Queue entries moved backwards"

    queue.move_queue_entries([4, 3], 1)
    assert queue.queued_action_names == [
        "2",
        "3",
        "1",
        "4",
        "5",
    ], "Queue entries moved to front"

    queue.move_queue_entries([2, 1], 6)
    assert queue.queued_action_names == [
        "1",
        "4",
        "5",
        "2",
        "3",
    ], "Queue entries moved to end"

    queue.move_queue_entries([3], 2)
    assert queue.queued_action_names == [
        "1",
        "5",
        "4",
        "2",
        "3",
    ], "Queue entry swapped forwards"


def test_exit(monkeypatch, capsys):
    """
    .
    """

    class FakeDevManager:
        """
      """

        @counter_wrapper
        def stop(self):
            """
          .
          """

    lock = FakeLock()
    context = {}
    queue = QueueStateManager(
        FakeDevManager(), multiprocessing.Manager(), None, None, lock, context
    )
    monkeypatch.setattr(lock, "acquire", lambda self=None, block=True: False)

    # pylint: disable=unused-argument
    @counter_wrapper
    def close_server(device_manager):
        """
        .
        """

    monkeypatch.setattr(device_manager, "close_server", close_server)

    queue.exit()
    printed = capsys.readouterr()

    assert queue.thread_count == 0, "Threads set to zero"
    assert queue.executor_count == 0, "All executors stopped"
    assert FakeDevManager.stop.counter == 1, "Device manager stopped"
    assert close_server.counter == 1, "Device manager server closed"

    expected = (
        # "\0ee[K  " + Info.EXITING("") + "\033[0m\r"
        "\033[K  "
        + Info.EXITING("Cleared threads, waiting for processing actions to complete")
        + "\033[0m\r"
        + "\033[K  "
        + Info.EXITING("Device manager cleaning up")
        + "\033[0m\r"
        + "\033[K  "
        + Info.EXITING("complete")
        + "\033[0m\n"
    )

    assert printed.out == expected, "Exit message printed"
