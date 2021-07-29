"""
CLI for interactive mode
"""
import multiprocessing
import re
import shlex
import socket
import threading
import time
from typing import List

from logical_backup.commands import AddCommand
from logical_backup.commands.base_command import BaseCommand
from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.interactive import command_completion
from logical_backup.interactive.queue_state_manager import QueueStateManager
from logical_backup.utilities import arguments, device_manager
from logical_backup.pretty_print import (
    Color,
    Format,
    PrettyStatusPrinter,
    print_error,
    readable_duration,
    CROSS_UNICODE,
    CHECK_UNICODE,
    INFO_UNICODE,
    WARN_UNICODE,
    BULLET,
)
from logical_backup.strings import Commands, Errors, Info, InputPrompts

OPERATIONAL_COMMANDS = [
    str(Commands.REORDER),
    str(Commands.CLEAR),
    str(Commands.MESSAGES),
    str(Commands.STATUS),
    str(Commands.SET_THREADS),
    str(Commands.HELP),
]

START_TIME = None


def run(start_time: int = None):
    """
    Loop portion of REPL
    """
    global START_TIME
    START_TIME = start_time or time.time_ns()

    command_completion.set_completion()
    queue_manager = _initialize_multiprocessing()

    stop = False
    while not stop:
        # Remove dead executors, then add any needed to get back
        # to the desired parallelism
        queue_manager.prune_dead_executors()
        while queue_manager.thread_count > queue_manager.executor_count:
            queue_manager.add_executor()

        input_arguments = _read_input(queue_manager)

        try:
            parsed = vars(
                arguments.get_argument_parser(True).parse_args(
                    shlex.split(input_arguments)
                )
            )
        except:
            continue

        if parsed["action"] == "exit":
            stop = True
        elif parsed["action"] in OPERATIONAL_COMMANDS:
            _process_operational_input(parsed, queue_manager)
        else:
            queue_manager.enqueue_actions(_process_command_input(parsed, queue_manager))

    queue_manager.exit()


def _initialize_multiprocessing() -> QueueStateManager:
    """
    Sets up multiprocessing communications - task queue, device manager, etc
    """
    # Don't copy environment state - avoid deadlock due to
    # acquiring an already-acquired lock, etc.
    # Must explicitly be passed in to work
    multiprocessing.set_start_method("spawn")

    manager = multiprocessing.Manager()
    # Pylint incorrectly thinks Lock doesn't exist on the manager
    # pylint: disable=no-member
    device_lock = manager.Lock()
    # pylint: disable=no-member
    queue_lock = manager.Lock()

    sock = device_manager.get_server_connection()
    dev_manager = device_manager.DeviceManager(sock)
    manager_thread = threading.Thread(target=dev_manager.loop)
    manager_thread.start()

    return QueueStateManager(dev_manager, manager, sock, device_lock, queue_lock)


def _read_input(queue_manager: QueueStateManager) -> str:
    """
    Reads input for REPL
    """
    return input(_generate_prompt(queue_manager)).strip()


def _generate_prompt(queue_manager: QueueStateManager) -> str:
    """
    Input prompt to use for read step of REPL
    """
    return InputPrompts.CLI_STATUS(
        queue_manager.completed_action_count,
        queue_manager.action_count,
        queue_manager.thread_count,
    )


# pylint: disable=bad-continuation
def _process_operational_input(
    parsed_arguments: dict, manager_context: QueueStateManager
) -> None:
    """
    Evaluates an operational input, e.g. queue actions, changing parallelism
    """
    if parsed_arguments["action"] == str(Commands.HELP):
        print(str(Info.CLI_HELP))
    elif parsed_arguments["action"] == str(Commands.SET_THREADS):
        _set_thread_count(parsed_arguments["values"], manager_context)
    elif parsed_arguments["action"] == str(Commands.REORDER):
        _reorder_queue(parsed_arguments["values"], manager_context)
    elif parsed_arguments["action"] == str(Commands.CLEAR):
        _clear_actions(parsed_arguments["values"], manager_context)
    elif parsed_arguments["action"] in [str(Commands.MESSAGES), str(Commands.STATUS)]:
        _parse_print_command(parsed_arguments, manager_context)


def _set_thread_count(values: list, manager_context: QueueStateManager) -> None:
    """
    Modify how many commands can be run in parallel
    """
    if not values or not values[0].isnumeric():
        print_error(str(Errors.THREAD_COUNT_NUMERIC))
    else:
        manager_context.set_thread_count(int(values[0]))


def _reorder_queue(positions: list, manager_context: QueueStateManager) -> None:
    """
    Change the order of things in the queue
    Indices specified will start from "1"

    Positions contains a string of "from" locations and a single "to" location
    """
    if len(positions) < 2:
        print_error(str(Errors.INSUFFICIENT_REORDER_POSITIONS))
    elif not re.match(r"^[0-9,\-]+$", positions[0]):
        print_error(str(Errors.INVALID_SOURCE_POSITION))
    elif not positions[1].isnumeric() and positions[1] not in ["top", "bottom"]:
        print_error(str(Errors.INVALID_DESTINATION_POSITION))
    else:
        # Use 1 and queue length here, since user input won't be zero-indexed
        destination = (
            1
            if positions[1] == "top"
            else manager_context.queue_length
            if positions[1] == "bottom"
            else int(positions[1])
        )
        manager_context.move_queue_entries(
            _get_numbers_from_string(positions[0]), destination
        )


def _clear_actions(positions: list, manager_context: QueueStateManager) -> None:
    """
    Remove one or more actions from the list
    By default removes only completed actions, unless one or more indices is specified
    """
    if not positions:
        manager_context.clear_completed_actions()
    elif re.match(r"^[0-9,\-]+$", positions):
        indices = _get_numbers_from_string(positions)
        manager_context.dequeue_actions(indices)
    else:
        print_error(str(Errors.INVALID_SOURCE_POSITION))


def _get_numbers_from_string(items: str) -> List[int]:
    """
    Takes a comma-separated list of numbers and/or ranges,
    and returns the plain numbers
    """
    all_indices = items.split(",")
    ranged_indices = list(filter(lambda index: "-" in index, all_indices))
    # pylint: disable=expression-not-assigned
    [all_indices.remove(index) for index in ranged_indices]
    all_indices = [int(i) for i in all_indices]
    for index in ranged_indices:
        start = int(index.split("-")[0])
        stop = int(index.split("-")[1]) + 1
        all_indices.extend(range(start, stop))

    all_indices.sort()
    return all_indices


def _parse_print_command(
    parsed_arguments: dict, manager_context: QueueStateManager
) -> None:
    """
    Determine what to print - a summary of statuses, messages from an action, etc
    """
    args = parsed_arguments["values"]
    if args:
        if (
            len(args) < 2
            or args[0].lower() not in ["c", "q", "complete", "queued"]
            or not args[1].isnumeric()
        ):
            print(str(Errors.INSUFFICIENT_STATUS_OPTIONS))
            return

        action = (
            manager_context.get_completed_action(int(args[1]) - 1)
            if args[0][0].lower() == "c"
            else manager_context.get_queued_action(int(args[1]) - 1)
        )
        _print_action_details(action)
    elif parsed_arguments["action"] == str(Commands.STATUS):
        _print_summary(manager_context)
    else:
        print(str(Errors.INSUFFICIENT_STATUS_OPTIONS))


def _print_summary(manager_context: QueueStateManager) -> None:
    """
    Prints summary of all actions so far
    """
    with manager_context.queue_lock:
        queued_actions = manager_context.queued_action_names
        completed_actions = manager_context.completed_actions
        average_time_seconds = manager_context.average_action_ns / 1000000000

    elapsed_time = (time.time_ns() - START_TIME) / 1000000000
    # Leave precision loss to end, since half a second times a thousand actions
    # is a signficant amount of time
    naive_eta = readable_duration(int(average_time_seconds * len(queued_actions)))

    total_completed = len(completed_actions)
    action_count = total_completed + len(queued_actions)

    print(Format.BOLD)
    print(
        "Actions completed/in progress: {0}/{1} ({2})".format(
            total_completed,
            action_count,
            round(total_completed / action_count * 100, 2),
        )
    )
    print("Time elapsed so far: {0}".format(readable_duration(elapsed_time)))
    print(
        "Average completion time: {0}".format(readable_duration(average_time_seconds))
    )
    print("Projected ETA (using average): {0}".format(naive_eta))
    print(Format.END)

    print("")
    print("-" * 80)
    print("")

    print("{0}Processed actions:{1}".format(Format.BOLD, Format.END))
    print("")
    for action in completed_actions:
        print(_make_processed_action_summary(action))

    print("")
    print("-" * 80)
    print("")

    print("{0}Pending actions:{1}".format(Format.BOLD, Format.END))
    print("")
    idx = 1
    for action in queued_actions:
        print("{0}. {1}".format(idx, str(action)))
        idx += 1


def _make_processed_action_summary(action: BaseAction) -> str:
    """
    Makes a pretty formatted string with details about a processed action
    """
    prefix = (
        (Color.GREEN + CROSS_UNICODE)
        if action.success
        else (Color.ERROR + CHECK_UNICODE)
        if action.success is not None
        else (Color.MAGENTA + BULLET)
    )
    body = str(action)
    postfix = (
        "({info_color}{info_unicode} {info_count}{end_format}:"  # pragma: no mutate
        "{error_color}{error_unicode} {error_count})"  # pragma: no mutate
    ).format(
        info_color=Color.BLUE,
        info_unicode=INFO_UNICODE,
        info_count=len(action.messages),
        end_format=Format.END,
        error_color=Color.ERROR,
        error_unicode=WARN_UNICODE,
        error_count=len(action.errors),
    )

    return str(Format.END).join([prefix, body, postfix])


def _print_action_details(action: BaseAction) -> None:
    """
    Prints details about an action
    """
    print("Action: {0}".format(str(action)))
    print(
        "Status: {0}".format(
            "Completed"
            if action.success is not None
            else "In progress"
            if action.started
            else "Queued"
        )
    )
    if action.started:
        print("")
        print("{0}Messages:{1}".format(Format.BOLD, Format.END))
        # pylint: disable=expression-not-assigned
        [print(str(message)) for message in action.logs]


# pylint: disable=bad-continuation
def _process_command_input(
    parsed_arguments: dict, manager_context: QueueStateManager
) -> List[BaseAction]:
    """
    Evaluates command inputs for REPL, to enqueue for asynchronous processing
    """
    if parsed_arguments["action"] == str(Commands.ADD):
        command = AddCommand(
            parsed_arguments,
            manager_context.device_manager,
            manager_context.device_mgr_sock,
            manager_context.device_mgr_lock,
        )

    actions = command.actions
    _print_command_results(command, actions)
    return actions


def _print_command_results(command: BaseCommand, actions: List[BaseAction]) -> None:
    """
    Outputs details of success or failure to create actions from a command
    """
    if command.has_actions:
        PrettyStatusPrinter(Info.COMMAND_CREATED_ACTIONS(len(actions))).print_complete()
    else:
        PrettyStatusPrinter(Errors.FAILED_TO_CREATE_ACTIONS).print_complete(False)
        for log in command.logs:
            print("- " + log)
