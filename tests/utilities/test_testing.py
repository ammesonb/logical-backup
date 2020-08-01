"""
Tests testing functions
"""
from logical_backup.utilities import testing


def test_is_test():
    """
    Should always be testing, since this is a test
    """
    assert not testing.is_test(), "Test variable should not be set yet"
    testing.set_testing()
    assert (
        testing.is_test()
    ), "Test utility does not return test environment, what has the world come to"
    testing.remove_testing()
    assert not testing.is_test(), "Test variable should have been cleared"


def test_compare_lists():
    """
    .
    """
    assert testing.compare_lists([], []), "Empty lists identical"
    assert not testing.compare_lists([], ["abc"]), "Lists differ, one empty"
    assert not testing.compare_lists(["def"], ["abc"]), "Lists differ"
    assert not testing.compare_lists(["def"], ["abc", 4]), "Lists differ, mixed lengths"
    assert not testing.compare_lists(
        [3, "def"], ["abc", 4]
    ), "Lists differ, mixed types"
    assert testing.compare_lists([4, "abc"], ["abc", 4]), "Lists match, out of order"
    assert testing.compare_lists(["abc", 4], ["abc", 4]), "Lists match, in order"


def test_counter_wrapper():
    """
    .
    """

    @testing.counter_wrapper
    def fake():
        pass

    assert fake.counter == 0, "Counter set to zero"
    fake()
    assert fake.counter == 1, "Counter incremented"
    fake()
    fake()
    assert fake.counter == 3, "Counter incremented twice"
