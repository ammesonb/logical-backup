"""
Tests CLI functionality
"""
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
