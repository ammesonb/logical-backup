"""
Tests action executor
"""
import multiprocessing
import threading
import time

from logical_backup.interactive.action_executor import ActionExecutor
from logical_backup.utilities.fake_lock import FakeLock
from logical_backup.utilities.testing import counter_wrapper

# pylint: disable=protected-access,no-self-use


def test_get_action(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(multiprocessing.Process, "__init__", lambda self: None)
    queue = []
    completion_queue = []
    lock = FakeLock()
    executor = ActionExecutor(
        {"queue": queue, "completion_queue": completion_queue, "queue_lock": lock}, 1
    )

    assert executor._get_action() is None, "No action returned"
    assert not completion_queue, "Nothing added to the completion queue"
    assert lock.acquired == 1 and lock.released == 1, "Lock acquired and released"

    queue.append(123)
    assert executor._get_action() == 123, "Task returned"
    assert not queue, "Task removed from queue"
    assert completion_queue == [], "Task not added to completion until completed"
    assert (
        lock.acquired == 2 and lock.released == 2
    ), "Lock acquired and released, again"


def test_run(monkeypatch):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeTask:
        """
        A fake task
        """

        @counter_wrapper
        def process(self):
            """
            Do a thing
            """
            return None

    _sleep = time.sleep

    # pylint: disable=unused-argument
    @counter_wrapper
    def fake_sleep(length):
        """
        Sleep replacement
        """
        _sleep(0.1)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(multiprocessing.Process, "__init__", lambda self: None)
    task = FakeTask()
    queue = [task]
    completion_queue = []
    lock = FakeLock()
    context = {
        "queue": queue,
        "completion_queue": completion_queue,
        "queue_lock": lock,
        "thread_count": 1,
    }
    executor = ActionExecutor(context, 1)
    thread = threading.Thread(target=executor.run)
    thread.start()
    _sleep(0.1)

    assert task.process.counter == 1, "Process executed"
    assert completion_queue == [task], "Task moved to completed queue"
    # Added by the decorator
    # pylint: disable=no-member
    assert fake_sleep.counter > 0, "Sleep called if no task"

    context["thread_count"] = 0
    _sleep(0.5)
    assert not thread.is_alive(), "Thread ends if parallelism lowered"
