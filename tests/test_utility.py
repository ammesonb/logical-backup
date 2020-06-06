"""
Tests for utility functions
"""
import logical_backup.utility as utility


def test_is_test():
    """
    Should always be testing, since this is a test
    """
    assert not utility.is_test(), "Test variable should not be set yet"
    utility.set_testing()
    assert (
        utility.is_test()
    ), "Test utility does not return test environment, what has the world come to"
    utility.remove_testing()
    assert not utility.is_test(), "Test variable should have been cleared"
