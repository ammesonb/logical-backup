"""
Contains state about the queues, executors, etc for parallel execution
"""
import multiprocessing
from multiprocessing import synchronize
import socket
import time
from typing import List

from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.interactive.action_executor import ActionExecutor
from logical_backup.utilities import device_manager
from logical_backup.pretty_print import print_error, PrettyStatusPrinter
from logical_backup.strings import Errors, Info

# pylint: disable=too-many-instance-attributes
class QueueStateManager:
    """
    Contains state for the device/process managers
    """

    # pylint: disable=too-many-arguments,bad-continuation
    def __init__(
        self,
        device_mgr: device_manager.DeviceManager,
        thread_manager: multiprocessing.Manager,
        device_manager_sock: socket.socket,
        device_manager_lock: synchronize.Lock,
        queue_lock: synchronize.Lock,
        process_context_reference: dict = None,
    ):
        self.device_manager = device_mgr
        self.manager = thread_manager
        self.device_mgr_sock = device_manager_sock
        self.device_mgr_lock = device_manager_lock
        self.queue_lock = queue_lock

        self.__executors = []
        self.__action_queue = []
        self.__processed_actions = []

        self._process_context = (
            process_context_reference
            if process_context_reference is not None
            else thread_manager.dict()
        )
        self._process_context["thread_count"] = multiprocessing.cpu_count()
        self._process_context["queue"] = self.__action_queue
        self._process_context["completion_queue"] = self.__processed_actions
        self._process_context["queue_lock"] = self.queue_lock

    def enqueue_actions(self, actions: List[BaseAction]) -> None:
        """
        Add one or more actions to the queue
        """
        with self.queue_lock:
            self.__action_queue.extend(actions)

    def add_executor(self) -> None:
        """
        Adds a new executor to the pool
        """
        executor = ActionExecutor(self._process_context, self.executor_count + 1,)
        executor.start()
        self.__executors.append(executor)

    def prune_dead_executors(self) -> None:
        """
        Remove any executors which are no longer active
        """
        dead_executors = list(
            filter(lambda executor: not executor.is_alive(), self.__executors)
        )
        for executor in list(dead_executors):
            self.__executors.remove(executor)

    @property
    def executor_count(self) -> int:
        """
        How many executors are currently running
        """
        return len(self.__executors)

    @property
    def thread_count(self) -> int:
        """
        How many threads are we currently using
        """
        return self._process_context["thread_count"]

    @property
    def action_count(self) -> int:
        """
        How many actions have been added
        """
        return self.completed_action_count + self.queue_length

    @property
    def queue_length(self) -> int:
        """
        Length of queued actions
        """
        return len(self.__action_queue)

    @property
    def completed_action_count(self) -> int:
        """
        How many actions have been completed
        """
        return len(self.__processed_actions)

    @property
    def queued_action_names(self) -> List[str]:
        """
        Returns names of queued actions
        """
        with self.queue_lock:
            return [str(action) for action in self.__action_queue]

    @property
    def average_action_ns(self) -> float:
        """
        Returns average nanoseconds to process an action
        """
        with self.queue_lock:
            return (
                (
                    sum(
                        [
                            action.completion_nanoseconds
                            for action in self.__processed_actions
                        ]
                    )
                    / self.completed_action_count
                )
                if self.completed_action_count
                else None
            )

    @property
    def completed_actions(self) -> dict:
        """
        Returns details about completed actions
        """
        with self.queue_lock:
            actions = []
            for action in self.__processed_actions:
                actions.append(
                    {
                        "name": action.name,
                        "succeeded": action.success,
                        "error_count": len(action.errors),
                        "message_count": len(action.messages),
                    }
                )

            return actions

    def set_thread_count(self, thread_count: int):
        """
        Sets thread execution count'
        """
        self._process_context["thread_count"] = thread_count

    def move_queue_entries(self, from_indices: list, to_index: int):
        """
        Reorders queued actions
        """
        if self.queue_lock.acquire(False):
            # To get indices correct, remove the last entry first,
            # and the same for insertion - must insert the last first, since others
            # will be added _before_ the chronologically-earlier entries
            from_indices.sort()
            from_indices.reverse()

            actions = [self.__action_queue[index - 1] for index in from_indices]

            # Don't remove until after caching all actions,
            # since that would reorder indices and mean wrong actions get selected
            for action in actions:
                self.__action_queue.remove(action)

            # When removing entries from a list, re-indexing means
            # the entries below it shift. So, to ensure the destination index
            # is correct, decrement it by the number of entries that were removed
            # _before_ it, e.g.
            # Move 3 between 4 and 5, index calculated as 5
            # 1 2 3 4 dest 5
            # Remove "3"
            # 1 2 4 dest 5
            # Index 5 is now out of bounds of the array, so need to shift it
            # down to "4"
            # If another entry such as "2" was also removed, then would need to
            # decrement by 2, since two entries removed
            to_index -= sum([1 if to_index > index else 0 for index in from_indices])

            # Then re-insert them, to ensure indices are consistent
            for action in actions:
                # To insert at 0, user will specify "1"
                self.__action_queue.insert(to_index - 1, action)

            self.queue_lock.release()
        else:
            print_error(str(Errors.UNABLE_TO_ACQUIRE))

    def clear_completed_actions(self) -> None:
        """
        Clear processed actions, regardless of success/failure
        """
        if self.queue_lock.acquire(False):
            finished_actions = list(
                filter(
                    lambda action: action.success is not None, self.__processed_actions
                )
            )
            for action in finished_actions:
                self.__processed_actions.remove(action)

            self.queue_lock.release()
        else:
            print_error(str(Errors.UNABLE_TO_ACQUIRE))

    def dequeue_actions(self, indices: List[int]) -> None:
        """
        Remove the given actions from the queue
        """
        # Ensure the indices don't overwrite themselves
        # e.g., if index 1 (3) is removed, then 2 (4), this would be the result:
        # start: [1, 3, 4, 5, 2]
        # remove 1: [1, 4, 5, 2]
        # remove 2: [1, 4, 2] -- 5 is removed, instead of 4
        # instead of the expected end result of:
        # [1, 5, 2]
        indices.sort()
        indices.reverse()

        if self.queue_lock.acquire(False):
            for index in indices:
                # Indices will be 1-indexed from user input
                self.__action_queue.remove(self.__action_queue[index - 1])
            self.queue_lock.release()
        else:
            print_error(str(Errors.UNABLE_TO_ACQUIRE))

    def get_queued_action(self, index: int) -> BaseAction:
        """
        Get a pending action
        """
        return self.__action_queue[index] if index < len(self.__action_queue) else None

    def get_completed_action(self, index: int) -> BaseAction:
        """
        Get a completed action from the queue
        """
        return (
            self.__processed_actions[index]
            if index < len(self.__processed_actions)
            else None
        )

    def exit(self):
        """
        Gracefully allows all pending actions to complete and cleans up handles
        """
        self.set_thread_count(0)
        PrettyStatusPrinter(
            Info.EXITING("Cleared threads, waiting for processing actions to complete")
        ).print_message(True, clear_line_first=True)

        while len(self.__executors):
            self.prune_dead_executors()
            time.sleep(1)

        PrettyStatusPrinter(Info.EXITING("Device manager cleaning up")).print_message(
            True, clear_line_first=True
        )
        self.device_manager.stop()
        device_manager.close_server(self.device_manager)
        PrettyStatusPrinter(Info.EXITING("complete")).print_message(
            clear_line_first=True
        )
