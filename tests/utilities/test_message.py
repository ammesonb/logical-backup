"""
Tests the message encapsulation
"""
from logical_backup.utilities.message import Message


def test_string():
    """
    .
    """
    msg = Message("foo", 1603919896)
    assert str(msg) == "2020-10-28 17:18:16 foo", "Message string matches"
