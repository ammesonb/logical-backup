"""
Tests automating setting of testing
"""
from logical_backup.utilities.testing import auto_set_testing, is_test


def test_is_test():
    """
    Should always be testing, since this is a test
    """
    assert is_test(), "Auto-set testing worked"
