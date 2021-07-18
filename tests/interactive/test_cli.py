"""
Tests CLI functionality
"""
import multiprocessing

from logical_backup.interactive import cli, command_completion, queue_state_manager
from logical_backup.pretty_print import PrettyStatusPrinter, Color
from logical_backup.strings import Info, Errors, InputPrompts, Commands
from logical_backup.utilities import device_manager
from logical_backup.utilities.testing import counter_wrapper
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


def test_set_thread_count(monkeypatch, capsys):
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


def test_reorder_queue(monkeypatch, capsys):
    """
    .
    """


def test_clear_actions(monkeypatch, capsys):
    """
    .
    """


def test_get_numbers_from_string(monkeypatch, capsys):
    """
    .
    """


def test_parse_print_command(monkeypatch, capsys):
    """
    .
    """


def test_print_summary(monkeypatch, capsys):
    """
    .
    """


def test_make_processed_action_summary(monkeypatch, capsys):
    """
    .
    """


def test_print_action_details(monkeypatch, capsys):
    """
    .
    """


def test_process_command_input(monkeypatch, capsys):
    """
    .
    """


def test_print_command_results(monkeypatch, capsys):
    """
    .
    """
