"""
Some pretty-printing stuff
"""
from __future__ import annotations

from enum import Enum

CHECK_UNICODE = "\u2714"  # pragma: no mutate
CROSS_UNICODE = "\u274c"  # pragma: no mutate
CLEAR_LINE = "\033[K"
INFO_UNICODE = u"\U0001F6C8"  # pragma: no mutate
WARN_UNICODE = u"\U000026a0"  # pragma: no mutate
BULLET = u"\U000025cb"  # pragma: no mutate


class Color(Enum):
    """
    Contains foreground colors for the command line
    """

    BLACK = "\033[30m"  # pragma: no mutate
    RED = "\033[31m"  # pragma: no mutate
    PURPLE = "\033[35m"  # pragma: no mutate
    CYAN = "\033[36m"  # pragma: no mutate
    ERROR = "\033[91m"  # pragma: no mutate
    GREEN = "\033[92m"  # pragma: no mutate
    YELLOW = "\033[93m"  # pragma: no mutate
    BLUE = "\033[94m"  # pragma: no mutate
    MAGENTA = "\033[95m"  # pragma: no mutate
    WHITE = "\033[95m"  # pragma: no mutate


class Background(Enum):
    """
    Contains background colors for the command line
    """

    BLACK = "\033[40m"  # pragma: no mutate
    RED = "\033[41m"  # pragma: no mutate
    GREEN = "\033[42m"  # pragma: no mutate
    YELLOW = "\033[43m"  # pragma: no mutate
    BLUE = "\033[44m"  # pragma: no mutate
    PURPLE = "\033[45m"  # pragma: no mutate
    CYAN = "\033[46m"  # pragma: no mutate
    WHITE = "\033[47m"  # pragma: no mutate


class Format(Enum):
    """
    Contains text formatting options
    """

    END = "\033[0m"  # pragma: no mutate
    BOLD = "\033[1m"  # pragma: no mutate
    DIM = "\033[2m"  # pragma: no mutate
    UNDERLINE = "\033[4m"  # pragma: no mutate
    HIDDEN = "\033[8m"  # pragma: no mutate


def get_success_prefix(succeeded: bool = None) -> str:
    """
    Returns a padded string indicating success

    Check for True, Cross for False, spaces for None
    """
    if succeeded is None:
        string = "  "  # pragma: no mutate
    elif succeeded:
        # The check has a smaller width than the cross, so pad it
        string = CHECK_UNICODE + " "  # pragma: no mutate
    else:
        string = CROSS_UNICODE

    return string


def print_error(message: str) -> None:
    """
    Prints an error message
    """
    PrettyStatusPrinter(message).with_specific_color(Color.ERROR).print_message()


# pylint: disable=too-many-instance-attributes
class PrettyStatusPrinter:
    """
    Prints status messages, prettily
    """

    def __init__(self, message: str):
        """
        .
        """
        self.__with_ellipsis = True  # pragma: no mutate
        self.__specific_color = None  # pragma: no mutate
        self.__result_colors = {
            True: Color.GREEN,  # pragma: no mutate
            False: Color.ERROR,  # pragma: no mutate
        }
        self.__message_postfix = {
            True: "Completed",  # pragma: no mutate
            False: "Failed",  # pragma: no mutate
        }
        self.__results = {None: None, True: True, False: False}  # pragma: no mutate
        self.__background_color = None  # pragma: no mutate
        self.__styles = []  # pragma: no mutate
        self.__message = str(message)  # pragma: no mutate
        self.__line_ending = "\n"  # pragma: no mutate
        self.__started = False  # pragma: no mutate

    def __get_styled_message(self, result=None) -> str:
        """
        Returns the styled message
        Needs to know success status to resolve color correctly
        """
        styled_message = ""  # pragma: no mutate
        if self.__specific_color:
            styled_message = self.__specific_color.value
        elif result is not None:
            styled_message = (
                self.__result_colors[result].value
                if result in self.__result_colors
                else self.__result_colors[self.__results[result]].value
            )

        if self.__background_color:
            styled_message += self.__background_color.value

        if self.__styles:
            for style in self.__styles:
                styled_message += style.value

        styled_message += get_success_prefix(result)
        styled_message += self.__message

        if self.__started and self.__with_ellipsis:
            styled_message += "..."

        styled_message += self.__message_postfix.get(
            result, self.__message_postfix.get(self.__results[result], "")
        )

        styled_message += Format.END.value

        return styled_message

    def with_custom_result(self, result, is_success: bool) -> PrettyStatusPrinter:
        """
        Allow custom result responses
        Requires definition of whether it is a "success" or not
        DO NOT USE "0" or "1" AS VALUES - THEY WILL COLLIDE WITH TRUE/FALSE
        """
        self.__results[result] = is_success
        return self

    def with_ellipsis(self, include: bool = True) -> PrettyStatusPrinter:
        """
        Include ellipsis on start, or not
        """
        self.__with_ellipsis = include
        return self

    def with_specific_color(self, color: Color) -> PrettyStatusPrinter:
        """
        Always print in this color
        """
        self.__specific_color = color
        return self

    # pylint: disable=bad-continuation
    def with_color_for_result(self, result, color: Color) -> PrettyStatusPrinter:
        """
        Sets the output color for a given response
        """

        self.__result_colors[result] = color
        return self

    def with_message_postfix_for_result(
        self, result, postfix: str
    ) -> PrettyStatusPrinter:
        """
        Adds message postfix for for given result, e.g. "failed to do X" or "Y happened"
        """
        self.__message_postfix[result] = str(postfix)
        return self

    def with_background_color(self, background: Background) -> PrettyStatusPrinter:
        """
        Sets the background color
        """
        self.__background_color = background
        return self

    def with_line_ending(self, line_ending: str) -> PrettyStatusPrinter:
        """
        Sets the line ending to print
        """
        self.__line_ending = line_ending
        return self

    def with_styles(self, styles: list) -> PrettyStatusPrinter:
        """
        Sets styles to print the message with
        """
        self.__styles += styles
        return self

    def print_message(
        self, to_overwrite: bool = False, result=None, clear_line_first: bool = False
    ) -> None:
        """
        Prints the message
        If to overwrite, will use a carriage return instead of newline
        Succeeded can also be specified, to pass through for formatting
        Clear line will reset the line prior to printing - useful if you need multiple
        states for a single primary message (e.g. exiting...phase1, exiting...phase2)
        """
        line_ending = "\r" if to_overwrite else self.__line_ending
        print(
            (CLEAR_LINE if clear_line_first else "")
            + self.__get_styled_message(result),
            end=line_ending,
            flush=True,  # pragma: no mutate
        )

    def get_styled_message(self, result=None) -> str:
        """
        Returns styled message
        Used mainly for testing
        """
        if result is not None:
            self.__started = True
        return self.__get_styled_message(result) + self.__line_ending

    def print_start(self) -> PrettyStatusPrinter:
        """
        Prints the starting message
        """
        self.__started = True
        self.print_message(True)
        return self

    def print_complete(self, succeeded: bool = True):
        """
        Print the completed message, for a given success status
        """
        self.print_message(result=succeeded)


def readable_bytes(size: int, suffix: str = "B") -> str:
    """
    Prints size of file

    Parameters
    ----------
    size : int
        Bytes to format
    suffix='B' : str
        What to print after the SI prefix
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:  # pragma: no mutate
        if abs(size) < 1024.0:
            return "%3.1f%s%s" % (size, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s" % (size, "Yi", suffix)


def readable_duration(seconds: int) -> str:
    """
    Converts elapsed seconds to a readable time string
    """
    days = int(seconds / 86400)
    seconds -= days * 86400
    hours = int(seconds / 3600)
    seconds -= hours * 3600
    minutes = int(seconds / 60)
    seconds -= minutes * 60
    seconds = round(seconds, 1)

    time_string = ""
    if days:
        time_string += "{0} day{1}, ".format(days, "s" if days != 1 else "")
    if hours or days:
        time_string += "{0} hour{1}, ".format(hours, "s" if hours != 1 else "")
    if minutes or hours or days:
        time_string += "{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "")

    return time_string + "{0} second{1}".format(seconds, "s" if seconds != 1 else "")
