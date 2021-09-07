"""
Executes actions from the provided queue
"""
import multiprocessing
import time
from typing import Optional

from logical_backup.commands.actions.base_action import BaseAction


class ActionExecutor(multiprocessing.Process):
    """
    Takes actions from a queue and executes them, moves between the queue when completed
    Will auto-exit after action completion if thread count decreases
    """

    def __init__(self, context: dict, task_number: int):
        """
        Parameters
        ----------
        queue : list
            A queue containing actions to execute
        queue_lock : Lock
            A semaphore ensuring no contention with the queue
        context : dict
            Context for running, such as number of processes, etc
        task_number : int
            The number of tasks created so far, to use in determining if this
            instance needs to stop processing
        """
        multiprocessing.Process.__init__(self)
        self.__queue = context["queue"]
        self.__completion_queue = context["completion_queue"]
        self.__queue_lock = context["queue_lock"]
        self.__context = context
        self.__number = task_number

    def _get_action(self) -> Optional[BaseAction]:
        """
        Get next action off the top of the queue
        """
        entry = None
        if self.__queue_lock.acquire(True, 0.1):
            entry = self.__queue.pop(0) if self.__queue else None
            self.__queue_lock.release()

        return entry

    def run(self):
        """
        Run loop for the process
        """
        while True:
            try:
                # If thread count modified while running, and this task
                # surpasses count of threads, gracefully exit
                if self.__context["thread_count"] < self.__number:
                    break

                task = self._get_action()
                if task:
                    task.process()
                    self.__completion_queue.append(task)

                else:
                    time.sleep(0.5)
            except KeyboardInterrupt:  # pragma: no cover
                pass
