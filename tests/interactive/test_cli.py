"""
Tests CLI functionality
"""
import multiprocessing

from logical_backup.utilities import device_manager
from logical_backup.utilities.testing import counter_wrapper
from logical_backup.interactive import cli, command_completion


# Pylint doesn't recognize the decorator adding the "counter" member
# to the functions, so ignore that
# pylint: disable=no-member
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

    # pylint: disable=unused-argument
    @counter_wrapper
    def read_input_action(context):
        """
        Returns command first time, then exit
        """
        return "add --file foo" if read_input_action.counter == 1 else "exit"

    monkeypatch.setattr(cli, "_read_input", read_input_action)
    monkeypatch.setattr(cli, "_process_command_input", lambda parsed, context: [])

    cli.run()
    assert Context.enqueue_actions.counter == 1, "Actions added"
    assert read_input_action.counter == 2, "Input read twice"


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

    class FakeManager:
        """
        .
        """

        created = 0
        started = False

        def __init__(self, socket):
            """
            .
            """
            self.created += 1

        def loop(self) -> None:
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
