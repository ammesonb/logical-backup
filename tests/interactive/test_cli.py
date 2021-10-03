"""
Tests CLI functionality
"""
import multiprocessing
import time
from typing import Optional, List

from logical_backup.interactive import cli, command_completion, queue_state_manager
from logical_backup.pretty_print import (
    PrettyStatusPrinter,
    Color,
    Format,
    CROSS_UNICODE,
    CHECK_UNICODE,
    BULLET,
    INFO_UNICODE,
    WARN_UNICODE,
)
from logical_backup.strings import Info, Errors, InputPrompts, Commands
from logical_backup.utilities import device_manager
from logical_backup.utilities.testing import counter_wrapper
from logical_backup.utilities.fake_lock import FakeLock
from tests.test_utility import patch_input


# Pylint doesn't recognize the decorator adding the "counter" member
# to the functions, so ignore that
# pylint: disable=no-member,protected-access
def test_run(monkeypatch):
    """
    .
    """

    @counter_wrapper
    def set_completion():
        """
        .
        """

    class Context:
        """
        Context placeholder class
        """

        thread_count = 2
        executor_count = 0

        @counter_wrapper
        def prune_dead_executors(self):
            """
            .
            """

        @counter_wrapper
        def add_executor(self):
            """
            .
            """
            self.executor_count += 1

        @counter_wrapper
        def enqueue_actions(self, actions: list):
            """
            .
            """

        @counter_wrapper
        def exit(self):
            """
            .
            """

    @counter_wrapper
    def fake_multiprocess():
        """
        .
        """
        return Context()

    monkeypatch.setattr(command_completion, "set_completion", set_completion)
    monkeypatch.setattr(cli, "_initialize_multiprocessing", fake_multiprocess)
    monkeypatch.setattr(cli, "_read_input", lambda context: "exit")

    cli.run()

    assert set_completion.counter == 1, "Completion set"
    assert Context.prune_dead_executors.counter == 1, "Dead executors pruned"
    assert Context.add_executor.counter == 2, "Two executors added"
    assert Context.enqueue_actions.counter == 0, "No actions added yet"
    assert Context.exit.counter == 1, "Exit is called"

    # pylint: disable=unused-argument
    @counter_wrapper
    def read_input_action(context):
        """
        Returns command first time, then exit
        """
        results = ["add --file foo", "invalid", str(Commands.CLEAR), "exit"]
        return results[read_input_action.counter - 1]

    @counter_wrapper
    def process_operational_input(parsed: dict, queue_manager):
        """
        .
        """

    monkeypatch.setattr(cli, "_read_input", read_input_action)
    monkeypatch.setattr(cli, "_process_operational_input", process_operational_input)
    monkeypatch.setattr(cli, "_process_command_input", lambda parsed, context: [])

    cli.run()
    assert Context.enqueue_actions.counter == 1, "Actions added"
    assert process_operational_input.counter == 1, "Operational command processed"
    assert read_input_action.counter == 4, "Input read four times"
    assert Context.exit.counter == 2, "Exit is called"


def test_initialize_multiprocessing(monkeypatch):
    """
    .
    """

    def mock_set_start_method(method: str):
        """
        .
        """
        mock_set_start_method.method = method

    mock_set_start_method.method = None

    @counter_wrapper
    def get_server_connection():
        """
        .
        """

    # pylint: disable=too-few-public-methods
    class FakeManager:
        """
        .
        """

        created = 0
        started = False

        # pylint: disable=unused-argument
        def __init__(self, socket):
            """
            .
            """
            self.created += 1

        def loop(self) -> None:
            """
            .
            """
            self.started = True

    monkeypatch.setattr(multiprocessing, "set_start_method", mock_set_start_method)
    monkeypatch.setattr(device_manager, "get_server_connection", get_server_connection)
    monkeypatch.setattr(device_manager, "DeviceManager", FakeManager)

    queue_manager = cli._initialize_multiprocessing()
    assert mock_set_start_method.method == "spawn", "Spawn method set"
    assert get_server_connection.counter == 1, "Server connection retrieved"
    assert (
        queue_manager.device_manager.created == 1
    ), "One instance of device manager created"
    assert queue_manager.device_manager.started, "Device Manager loop started"


def test_read_input(monkeypatch):
    """
    .
    """

    # pylint: disable=unused-argument
    def get_input(prompt: str) -> str:
        return " stuff \n"

    patch_input(monkeypatch, cli, get_input)

    monkeypatch.setattr(cli, "_generate_prompt", lambda context: "")

    assert cli._read_input(None) == "stuff", "Command properly stripped and returned"


def test_generate_prompt():
    """
    .
    """

    context = {}
    manager = queue_state_manager.QueueStateManager(
        None, multiprocessing.Manager(), None, None, None, context
    )
    manager.set_thread_count(4)
    context["queue"].append("task")
    context["completion_queue"].append("done")

    assert cli._generate_prompt(manager) == InputPrompts.CLI_STATUS(1, 2, 4)


def test_process_operational_input(monkeypatch, capsys):
    """
    .
    """
    # pylint: disable=unused-argument
    @counter_wrapper
    def set_thread_count(*args, **kwargs):
        """
        .
        """

    @counter_wrapper
    def reorder_queue(*args, **kwargs):
        """
        .
        """

    @counter_wrapper
    def clear_actions(*args, **kwargs):
        """
        .
        """

    @counter_wrapper
    def parse_print_command(*args, **kwargs):
        """
        .
        """

    monkeypatch.setattr(cli, "_set_thread_count", set_thread_count)
    monkeypatch.setattr(cli, "_reorder_queue", reorder_queue)
    monkeypatch.setattr(cli, "_clear_actions", clear_actions)
    monkeypatch.setattr(cli, "_parse_print_command", parse_print_command)

    cli._process_operational_input(
        {"action": str(Commands.SET_THREADS), "values": {}}, None
    )
    assert set_thread_count.counter == 1, "Set threads called"
    assert (
        reorder_queue.counter + clear_actions.counter + parse_print_command.counter == 0
    ), "No other functions called"

    cli._process_operational_input(
        {"action": str(Commands.REORDER), "values": {}}, None
    )
    assert reorder_queue.counter == 1, "Reorder queue called"
    assert (
        set_thread_count.counter + clear_actions.counter + parse_print_command.counter
        == 1
    ), "No other functions called"

    cli._process_operational_input({"action": str(Commands.CLEAR), "values": {}}, None)
    assert clear_actions.counter == 1, "Clear actions called"
    assert (
        set_thread_count.counter + reorder_queue.counter + parse_print_command.counter
        == 2
    ), "No other functions called"

    cli._process_operational_input(
        {"action": str(Commands.MESSAGES), "values": {}}, None
    )
    assert parse_print_command.counter == 1, "Print message called"
    assert (
        set_thread_count.counter + reorder_queue.counter + clear_actions.counter == 3
    ), "No other functions called"

    cli._process_operational_input({"action": str(Commands.STATUS), "values": {}}, None)
    assert parse_print_command.counter == 2, "Print message called"
    assert (
        set_thread_count.counter + reorder_queue.counter + clear_actions.counter == 3
    ), "No other functions called"

    cli._process_operational_input({"action": str(Commands.HELP), "values": {}}, None)
    printed = capsys.readouterr()
    assert printed.out == str(Info.CLI_HELP) + "\n", "Correct output printed"
    assert (
        set_thread_count.counter
        + reorder_queue.counter
        + clear_actions.counter
        + parse_print_command.counter
        == 5
    ), "No other functions called"


def test_set_thread_count(capsys):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeManager:
        """
        A fake queue state manager
        """

        @counter_wrapper
        def set_thread_count(self, count: int):
            """
            .
            """

    cli._set_thread_count([], FakeManager())
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.THREAD_COUNT_NUMERIC)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Correct error message printed"
    assert FakeManager.set_thread_count.counter == 0, "Thread count not set"

    cli._set_thread_count(["abc"], FakeManager())
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.THREAD_COUNT_NUMERIC)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Correct error message printed"
    assert FakeManager.set_thread_count.counter == 0, "Thread count not set"

    cli._set_thread_count(["1abc2"], FakeManager())
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.THREAD_COUNT_NUMERIC)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Correct error message printed"
    assert FakeManager.set_thread_count.counter == 0, "Thread count not set"

    cli._set_thread_count(["123"], FakeManager())
    printed = capsys.readouterr()
    assert printed.out == "", "No errors printed"
    assert FakeManager.set_thread_count.counter == 1, "Thread count set"


def test_reorder_queue(capsys):
    """
    .
    """
    cli._reorder_queue("", None)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.INSUFFICIENT_REORDER_POSITIONS)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Error is correct"

    cli._reorder_queue([123], None)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.INSUFFICIENT_REORDER_POSITIONS)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Error is correct"

    cli._reorder_queue(["abc", "123"], None)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.INVALID_SOURCE_POSITION)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Error is correct"

    cli._reorder_queue(["123", "bad"], None)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.INVALID_DESTINATION_POSITION)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Error is correct"

    class FakeQueueManager:
        """
        .
        """

        # pylint: disable=unused-argument
        @counter_wrapper
        def move_queue_entries(self, *args, **kwargs):
            """
            .
            """

        @property
        def queue_length(self):
            """
            .
            """

    cli._reorder_queue(["123", "234"], FakeQueueManager())
    printed = capsys.readouterr()
    assert printed.out == "", "No error"
    assert FakeQueueManager.move_queue_entries.counter == 1, "Queue entries moved"

    cli._reorder_queue(["123", "top"], FakeQueueManager())
    printed = capsys.readouterr()
    assert printed.out == "", "No error"
    assert FakeQueueManager.move_queue_entries.counter == 2, "Queue entries moved"

    cli._reorder_queue(["123", "bottom"], FakeQueueManager())
    printed = capsys.readouterr()
    assert printed.out == "", "No error"
    assert FakeQueueManager.move_queue_entries.counter == 3, "Queue entries moved"


def test_clear_actions(capsys):
    """
    .
    """

    class FakeQueueManager:
        """
        .
        """

        @counter_wrapper
        def clear_completed_actions(self):
            """
            .
            """

        @counter_wrapper
        def dequeue_actions(self, indices):
            """
            .
            """

    cli._clear_actions("abc", FakeQueueManager())

    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.INVALID_SOURCE_POSITION)
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Correct error message"
    assert not FakeQueueManager.clear_completed_actions.counter, "No actions cleared"
    assert not FakeQueueManager.dequeue_actions.counter, "No actions removed"

    cli._clear_actions(None, FakeQueueManager())

    assert FakeQueueManager.clear_completed_actions.counter == 1, "All actions cleared"
    assert not FakeQueueManager.dequeue_actions.counter, "No actions removed"

    cli._clear_actions("1,2-3,6,10-12", FakeQueueManager())

    assert FakeQueueManager.clear_completed_actions.counter == 1, "All actions cleared"
    assert FakeQueueManager.dequeue_actions.counter == 1, "Actions removed"


def test_get_numbers_from_string():
    """
    .
    """
    assert cli._get_numbers_from_string("1,3,4,5") == [
        1,
        3,
        4,
        5,
    ], "Comma-separated numbers correct"
    assert cli._get_numbers_from_string("1,3-5") == [
        1,
        3,
        4,
        5,
    ], "Numbers with range correct"
    assert cli._get_numbers_from_string("1,3-5,6-8") == [
        1,
        3,
        4,
        5,
        6,
        7,
        8,
    ], "Numbers with dual range correct"
    assert cli._get_numbers_from_string("1,3-5,7-9,11") == [
        1,
        3,
        4,
        5,
        7,
        8,
        9,
        11,
    ], "Multi range and comma numbers"
    assert cli._get_numbers_from_string("1-3,5,7-10,12,13,15-17") == [
        1,
        2,
        3,
        5,
        7,
        8,
        9,
        10,
        12,
        13,
        15,
        16,
        17,
    ], "Complex list correct"


def test_parse_print_command(monkeypatch, capsys):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeManager:
        """
        .
        """

        # pylint: disable=unused-argument
        @counter_wrapper
        def get_completed_action(self, index):
            """
            .
            """
            return None if self.get_completed_action.counter == 1 else True

        # pylint: disable=no-self-use,unused-argument
        @counter_wrapper
        def get_queued_action(self, index):
            """
            .
            """
            return True

    # pylint: disable=unused-argument
    @counter_wrapper
    def print_action(*args, **kwargs):
        """
        .
        """

    monkeypatch.setattr(cli, "_print_action_details", print_action)

    # pylint: disable=unused-argument
    @counter_wrapper
    def print_summary(*args, **kwargs):
        """
        .
        """

    monkeypatch.setattr(cli, "_print_summary", print_summary)

    # This action wouldn't actually get routed to this function, but will emulate other
    # invalid argument combinations, to check this error
    cli._parse_print_command({"action": "unknown", "values": ["foo"]}, FakeManager())
    printed = capsys.readouterr()
    assert (
        printed.out == str(Errors.INSUFFICIENT_STATUS_OPTIONS) + "\n"
    ), "Correct error prints"

    cli._parse_print_command({"action": "messages", "values": ["foo"]}, FakeManager())
    printed = capsys.readouterr()
    assert (
        printed.out == str(Errors.INSUFFICIENT_STATUS_OPTIONS) + "\n"
    ), "Correct error prints"

    cli._parse_print_command(
        {"action": "messages", "values": ["m", "2"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert (
        printed.out == str(Errors.INSUFFICIENT_STATUS_OPTIONS) + "\n"
    ), "Correct error prints"

    cli._parse_print_command(
        {"action": "messages", "values": ["m", "2"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert (
        printed.out == str(Errors.INSUFFICIENT_STATUS_OPTIONS) + "\n"
    ), "Correct error prints"

    cli._parse_print_command(
        {"action": "messages", "values": ["c", "a"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert (
        printed.out == str(Errors.INSUFFICIENT_STATUS_OPTIONS) + "\n"
    ), "Correct error prints"

    assert not print_action.counter, "No action details printed"
    assert not FakeManager.get_completed_action.counter, "No completed actions fetched"
    assert not FakeManager.get_queued_action.counter, "No queued actions fetched"

    cli._parse_print_command(
        {"action": "messages", "values": ["c", "1"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(str(Errors.NO_SUCH_ACTION))
        .with_specific_color(Color.ERROR)
        .get_styled_message()
    ), "Error printed if action is missing"

    cli._parse_print_command(
        {"action": "messages", "values": ["c", "1"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert printed.out == "", "No error printed"

    assert FakeManager.get_completed_action.counter == 2, "Completed action fetched"
    assert print_action.counter == 1, "Action details printed"
    assert not FakeManager.get_queued_action.counter, "No queued actions fetched"

    cli._parse_print_command(
        {"action": "messages", "values": ["q", "2"]}, FakeManager()
    )
    printed = capsys.readouterr()
    assert printed.out == "", "No error message"

    assert FakeManager.get_completed_action.counter == 2, "Completed action fetched"
    assert print_action.counter == 2, "Action details printed"
    assert FakeManager.get_queued_action.counter == 1, "Queued action fetched"

    cli._parse_print_command({"action": "status", "values": ["q", "2"]}, FakeManager())
    printed = capsys.readouterr()
    assert printed.out == "", "No error message"
    assert print_summary.counter == 1, "Summary printed"


def test_print_summary(monkeypatch, capsys):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeManager:
        """
        .
        """

        queue_lock = FakeLock()
        completed_actions = ["1", "2"]
        queued_action_names = ["3"]
        average_action_ns = 75000000000

    @counter_wrapper
    def print_processed_action(action):
        """
        .
        """
        return action

    monkeypatch.setattr(cli, "_make_processed_action_summary", print_processed_action)

    cli._print_summary(FakeManager(), time.time_ns() - 150000000000)
    printed = capsys.readouterr()

    assert printed.out == "\n".join(
        [
            str(Format.BOLD),
            "Actions completed/in progress: 2/3 (66.67%)",
            "Time elapsed so far: 2 minutes, 30.0 seconds",
            "Average completion time: 1 minute, 15.0 seconds",
            "Projected ETA (using average): 1 minute, 15 seconds",
            str(Format.END),
            "",
            "-" * 80,
            "",
            f"{Format.BOLD}Processed actions:{Format.END}",
            "",
            "1",
            "2",
            "",
            "-" * 80,
            "",
            f"{Format.BOLD}Pending actions:{Format.END}",
            "",
            "1. 3",
            "",
        ]
    ), "Correct output printed"


def test_make_processed_action_summary():
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class Action:
        """
        .
        """

        success: None
        messages: []
        errors: []

        # pylint: disable=bad-continuation
        def __init__(
            self,
            name: str,
            success: Optional[bool] = None,
            messages: Optional[List[str]] = None,
            errors: Optional[List[str]] = None,
        ):
            """
            .
            """
            self.name = name
            self.success = success
            self.messages = messages or []
            self.errors = errors or []

        def __str__(self) -> str:
            """
            .
            """
            return self.name

    output = cli._make_processed_action_summary(Action("name", None, ["abc"]))
    assert output == str(Format.END).join(
        [
            Color.MAGENTA + BULLET,
            " name",
            f"  ({Color.BLUE}{INFO_UNICODE} 1{Format.END} : "
            f"{Color.ERROR}{WARN_UNICODE} 0)",
        ]
    ), "Pending action summary correct"

    output = cli._make_processed_action_summary(
        Action("name", False, ["abc"], ["def", "ghi"])
    )
    assert output == str(Format.END).join(
        [
            Color.ERROR + CROSS_UNICODE,
            " name",
            f"  ({Color.BLUE}{INFO_UNICODE} 1{Format.END} : "
            f"{Color.ERROR}{WARN_UNICODE} 2)",
        ]
    ), "Failed action summary correct"

    output = cli._make_processed_action_summary(
        Action("name", True, ["abc", "def"], [])
    )
    assert output == str(Format.END).join(
        [
            Color.GREEN + CHECK_UNICODE,
            " name",
            f"  ({Color.BLUE}{INFO_UNICODE} 2{Format.END} : "
            f"{Color.ERROR}{WARN_UNICODE} 0)",
        ]
    ), "Completed action summary correct"


def test_print_action_details(capsys):
    """
    .
    """
    # pylint: disable=too-few-public-methods
    class FakeAction:
        """
        .
        """

        # pylint: disable=bad-continuation
        def __init__(
            self,
            name: str,
            started: Optional[bool] = False,
            status: Optional[str] = None,
            logs: List[str] = None,
        ):
            self.name = name
            self.started = started
            self.success = status
            self.logs = logs or []

        def __str__(self) -> str:
            """
            .
            """
            return self.name

    cli._print_action_details(FakeAction("queue"))
    assert (
        capsys.readouterr().out == "Action: queue\nStatus: Queued\n"
    ), "Expected output correct"

    cli._print_action_details(FakeAction("queue", True, None, ["abc", "def"]))
    assert (
        capsys.readouterr().out
        == "Action: queue\nStatus: In progress\n\nMessages:\nabc\ndef\n"
    ), "Expected output correct"

    cli._print_action_details(FakeAction("queue", True, False, []))
    assert (
        capsys.readouterr().out == "Action: queue\nStatus: Failed\n"
    ), "Expected output correct"

    cli._print_action_details(FakeAction("queue", True, True, ["foo"]))
    assert (
        capsys.readouterr().out == "Action: queue\nStatus: Complete\n\nMessages:\nfoo\n"
    ), "Expected output correct"


def test_process_command_input():
    """
    .
    """


def test_print_command_results(capsys):
    """
    .
    """

    class Command:
        """
        Fake command
        """

        def __init__(self, actions: List[str] = None, errors: List[str] = None):
            self.actions = actions or []
            self.errors = errors or []

        @property
        def has_actions(self) -> bool:
            """
            If the command has actions
            """
            return len(self.actions) > 0

        @property
        def logs(self) -> List[str]:
            """
            Command logs
            """
            return self.errors + ["log"]

    actions_command = Command(["abc", "def"])

    cli._print_command_results(actions_command)
    printed = capsys.readouterr()
    assert printed.out == PrettyStatusPrinter(
        Info.COMMAND_CREATED_ACTIONS(2)
    ).with_message_postfix_for_result(True, "").with_ellipsis(False).get_styled_message(
        True
    ), "Message printed action count"

    errors_command = Command(errors=["issue", "problem"])
    cli._print_command_results(errors_command)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Errors.FAILED_TO_CREATE_ACTIONS)
        .with_message_postfix_for_result(False, "")
        .with_ellipsis(False)
        .get_styled_message(False)
        + "- issue\n- problem\n- log\n"
    ), "Failed messages print correctly"

    completed_command = Command()
    cli._print_command_results(completed_command)
    printed = capsys.readouterr()
    assert (
        printed.out
        == PrettyStatusPrinter(Info.COMMAND_COMPLETED)
        .with_ellipsis(False)
        .get_styled_message()
    ), "Command completed results print"
