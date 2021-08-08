"""
Contains a way to buffer text without having to print to stdout or stderr,
using a curses-based window/pad
"""
import curses
from typing import List, Any

BORDER_WIDTH = 1
PADDING_WIDTH = 1

TEXT_OFFSET = 1


# pylint: disable=too-many-instance-attributes
class TextBuffer:
    """
    A window-based text buffer, to avoid cluttering stdout
    Prints a set of headers followed by a list of rows, which are scrollable
    """

    screen_height: int = 0
    screen_width: int = 0
    scrollable_height: int = 0
    # _curses.window
    screen: Any = None
    # _curses.window
    pad: Any = None
    current_pad_row: int = 0

    def __init__(self, header_lines: List[str], rows: List[str]):
        self.headers = header_lines
        self.rows = rows

        # Padding and border are on each side
        self.max_line_length = (
            max([len(row) for row in self.rows]) + (BORDER_WIDTH + PADDING_WIDTH) * 2
        )

        self.row_data_start = TEXT_OFFSET + len(self.headers)

        self.loop = True

    def show(self):
        """
        Show the window
        """
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()

        self.screen.refresh()
        self.screen.keypad(True)

        self.screen_height, self.screen_width = self.screen.getmaxyx()
        # The number of rows HIDDEN, which will need scrolling to show
        # Scrollable height is:
        self.scrollable_height = (
            # Number of rows less the size of the screen
            # (no scrolling if it fills the screen)
            len(self.rows)
            - self.screen_height
            # Add BACK to the amount needing scrolling:
            # the text offset from the top
            + TEXT_OFFSET
            # How many headers are shown
            + len(self.headers)
            # Plus twice the width of the border
            + BORDER_WIDTH * 2
        )

        header_row = 0
        for header in self.headers:
            self.screen.addstr(
                TEXT_OFFSET + header_row, TEXT_OFFSET, header, curses.A_BOLD
            )
            header_row += 1

        if self.scrollable_height > 0:
            self.pad = curses.newpad(
                len(self.rows) + BORDER_WIDTH * 2, self.max_line_length
            )
            # Final 1 is gap between headers and rows
            self.pad.scrollok(len(self.rows) > self.screen_height - self.row_data_start)
            self.pad.idlok(True)

            self.write_pad_rows()
        else:
            row_num = 0
            for row in self.rows:
                self.screen.addstr(
                    TEXT_OFFSET + len(self.headers) + row_num, TEXT_OFFSET, row
                )
                row_num += 1

        self.refresh()

        while self.loop:
            character = self.screen.getch()
            # For q and enter, exit
            if character in [ord("q"), curses.KEY_ENTER]:
                self.loop = False
            # pylint: disable=bad-continuation
            # Scroll the pad if scrolling is enabled, stays in bounds of data,
            # and either vi bindings or arrow keys used
            elif (
                self.scrollable_height > 0
                and character in [curses.KEY_UP, ord("k")]
                and self.current_pad_row > 0
            ):
                self.current_pad_row -= 1
                self.pad.scroll(-1)

            # pylint: disable=bad-continuation
            elif (
                self.scrollable_height > 0
                and character in [curses.KEY_DOWN, ord("j")]
                and self.current_pad_row < self.scrollable_height
            ):
                self.current_pad_row += 1
                self.pad.scroll(1)

            # Refresh to ensure updated state
            self.refresh()

        self.exit()

    def refresh(self):
        """
        Refresh the curses screen
        """
        self.screen.refresh()

        if self.scrollable_height > 0:
            # Scrolling down always works, but anything above the top of the buffer
            # is permanently lost, so just rewrite all the rows each time, to be safe
            self.write_pad_rows()

            self.pad.refresh(
                0,
                0,
                self.row_data_start,
                TEXT_OFFSET,
                self.screen_height - BORDER_WIDTH * 2,
                self.max_line_length + TEXT_OFFSET,
            )

    def write_pad_rows(self):
        """
        Write the data to the pad
        """
        self.pad.clear()
        row_num = 0
        for line in self.rows[self.current_pad_row :]:
            # Plus one to leave row between border and text
            self.pad.addstr(row_num, TEXT_OFFSET + 1, line)
            row_num += 1

        # Add bottom border to pad, since seems curses does not do this
        # if rows larger than screen
        self.pad.addstr(row_num, TEXT_OFFSET + 1, "_" * (self.max_line_length - 2))
        self.pad.border()

    def exit(self):
        """
        Close the screen and reset echo and key states
        """
        self.screen.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
