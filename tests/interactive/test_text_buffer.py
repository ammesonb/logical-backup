"""
Test text buffer
"""
import curses
from typing import List

from logical_backup.interactive.text_buffer import TextBuffer
from logical_backup.utilities.testing import counter_wrapper

# Disable no member for the counter wrapper functions
# pylint: disable=no-member


def test_buffer_creation():
    """
    .
    """
    buf = TextBuffer(["1", "2"], ["3", "456"])

    assert buf.headers == ["1", "2"], "Headers correct"
    assert buf.rows == ["3", "456"], "Rows correct"
    assert buf.row_data_start == 3, "Row start line correct"
    assert buf.max_line_length == 7, "Max row line length correct"
    assert buf.loop, "Loop not exited"


def test_write_pad_rows(monkeypatch):
    """
    .
    """
    buf = TextBuffer(["1", "2"], ["3", "456", "789"])
    buf.current_pad_row = 1

    # pylint: disable=too-few-public-methods
    class FakePad:
        """
        .
        """

        @counter_wrapper
        def clear(self):
            """
            .
            """

        @counter_wrapper
        def addstr(self, row, col, line):
            """
            .
            """

        @counter_wrapper
        def border(self):
            """
            .
            """

    buf.pad = FakePad()

    buf.write_pad_rows()

    assert FakePad.clear.counter == 1, "Clear called"
    assert FakePad.addstr.counter == 3, "Two rows written, plus footer"
    assert FakePad.border.counter == 1, "Border added"


def test_exit(monkeypatch):
    """
    .
    """
    buf = TextBuffer(["1", "2"], ["3", "456", "789"])

    # pylint: disable=too-few-public-methods
    class FakeScreen:
        """
        .
        """

        # pylint: disable=unused-argument
        @counter_wrapper
        def keypad(self, enable: bool):
            """
            .
            """

    buf.screen = FakeScreen()

    @counter_wrapper
    def echo():
        """
        .
        """

    @counter_wrapper
    def nocbreak():
        """
        .
        """

    @counter_wrapper
    def endwin():
        """
        .
        """

    monkeypatch.setattr(curses, "echo", echo)
    monkeypatch.setattr(curses, "nocbreak", nocbreak)
    monkeypatch.setattr(curses, "endwin", endwin)

    buf.exit()
    assert FakeScreen.keypad.counter == 1, "Screen keypad reset"
    assert echo.counter + nocbreak.counter + endwin.counter == 3, "Curses config reset"


def test_refresh(monkeypatch):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeScreen:
        """
        .
        """

        # pylint: disable=unused-argument
        @counter_wrapper
        def refresh(self):
            """
            .
            """

    # pylint: disable=too-few-public-methods
    class FakePad:
        """
        .
        """

        # pylint: disable=unused-argument
        @counter_wrapper
        def refresh(self, *args, **kwargs):
            """
            .
            """

    # pylint: disable=unused-argument
    @counter_wrapper
    def write_pad_rows(self):
        """
        .
        """

    monkeypatch.setattr(TextBuffer, "write_pad_rows", write_pad_rows)

    buf = TextBuffer(["1", "2"], ["3", "456", "789"])
    buf.screen = FakeScreen()
    buf.pad = FakePad()
    buf.scrollable_height = 0

    buf.refresh()
    assert FakeScreen.refresh.counter == 1, "Screen refreshed"
    assert write_pad_rows.counter == 0, "Pad not written"
    assert FakePad.refresh.counter == 0, "Pad not refreshed"

    buf.scrollable_height = 15
    buf.screen_height = 100

    buf.refresh()
    assert FakeScreen.refresh.counter == 2, "Screen refreshed"
    assert write_pad_rows.counter == 1, "Pad written"
    assert FakePad.refresh.counter == 1, "Pad refreshed"


def test_show(monkeypatch):
    """
    .
    """

    # pylint: disable=too-few-public-methods
    class FakeScreen:
        """
        .
        """

        def __init__(self, characters: List[str]):
            """
            .
            """
            self.strings = []
            self.characters_returned = 0
            self.characters = characters

        # pylint: disable=unused-argument
        @counter_wrapper
        def keypad(self, enable: bool):
            """
            .
            """

        # pylint: disable=unused-argument
        @counter_wrapper
        def refresh(self):
            """
            .
            """

        # pylint: disable=unused-argument,no-self-use
        @counter_wrapper
        def getmaxyx(self):
            """
            .
            """
            return (8, 8)

        # pylint: disable=unused-argument
        @counter_wrapper
        def addstr(self, row, column, text, style=None):
            """
            .
            """
            self.strings.append(text)

        def getch(self):
            """
            .
            """
            character = self.characters[self.characters_returned]
            self.characters_returned += 1
            return character

    class FakePad:
        """
        .
        """

        # pylint: disable=unused-argument
        def __init__(self, cols, lines):
            """
            .
            """

        # pylint: disable=unused-argument, no-self-use
        @counter_wrapper
        def scrollok(self, enable: bool):
            """
            .
            """
            assert enable, "Scrolling should be enabled"

        # pylint: disable=unused-argument
        @counter_wrapper
        def idlok(self, enable: bool):
            """
            .
            """

        # pylint: disable=unused-argument
        @counter_wrapper
        def scroll(self, position: int):
            """
            .
            """

    @counter_wrapper
    def noecho():
        """
        .
        """

    @counter_wrapper
    def cbreak():
        """
        .
        """

    @counter_wrapper
    def initscr():
        """
        .
        """
        keys = [
            [curses.KEY_DOWN, curses.KEY_UP, ord("j"), ord("q")],
            [curses.KEY_DOWN, curses.KEY_UP, ord("j"), ord("q")],
        ]
        return FakeScreen(keys[initscr.counter - 1])

    monkeypatch.setattr(curses, "noecho", noecho)
    monkeypatch.setattr(curses, "cbreak", cbreak)
    monkeypatch.setattr(curses, "initscr", initscr)

    monkeypatch.setattr(
        curses, "newpad", lambda *args, **kwargs: FakePad(*args, **kwargs)
    )

    # pylint: disable=unused-argument
    @counter_wrapper
    def write_pad_rows(self):
        """
        .
        """

    # pylint: disable=unused-argument
    @counter_wrapper
    def refresh(self):
        """
        .
        """

    # pylint: disable=unused-argument
    @counter_wrapper
    def exit_buf(self):
        """
        .
        """

    monkeypatch.setattr(TextBuffer, "write_pad_rows", write_pad_rows)
    monkeypatch.setattr(TextBuffer, "refresh", refresh)
    monkeypatch.setattr(TextBuffer, "exit", exit_buf)

    buf = TextBuffer(["1", "2"], ["3", "456", "789"])

    buf.show()

    assert initscr.counter == 1, "Screen created"
    assert noecho.counter == 1, "No echo"
    assert cbreak.counter == 1, "Cbreak"
    assert FakeScreen.getmaxyx.counter == 1, "Screen size returned"
    assert buf.scrollable_height == 0, "Scroll height set correctly"
    assert buf.screen.strings == ["1", "2", "3", "456", "789"], "Text added to screen"
    assert buf.pad is None, "No pad set"
    assert FakePad.scrollok.counter == 0, "No scroll configured on pad"
    assert FakePad.idlok.counter == 0, "No idl configured on pad"
    assert write_pad_rows.counter == 0, "No rows written to pad"
    assert FakePad.scroll.counter == 0, "Pad not scrolled"
    assert refresh.counter == 5, "Refresh called five times"
    assert exit_buf.counter == 1, "Exit called"
    assert buf.current_pad_row == 0, "Pad row not changed"

    buf = TextBuffer(["1", "2"], ["3", "456", "789", "foo", "bar", "baz"])
    buf.show()

    assert initscr.counter == 2, "Screen created"
    assert noecho.counter == 2, "No echo"
    assert cbreak.counter == 2, "Cbreak"
    assert FakeScreen.getmaxyx.counter == 2, "Screen size returned"
    assert buf.scrollable_height == 3, "Scroll height set correctly"
    assert buf.screen.strings == ["1", "2"], "Only headers written to screen"
    assert buf.pad is not None, "Pad set"
    assert FakePad.scrollok.counter == 1, "Scroll configured on pad"
    assert FakePad.idlok.counter == 1, "Idle configured on pad"
    assert (
        write_pad_rows.counter == 1
    ), "Rows written to pad once (since refresh stubbed)"
    assert FakePad.scroll.counter == 3, "Pad scrolled thrice"
    assert refresh.counter == 10, "Refresh called five more times"
    assert exit_buf.counter == 2, "Exit called"
    assert buf.current_pad_row == 1, "Pad row down one at end"
