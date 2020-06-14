"""
Some pretty-printing stuff
"""
from enum import Enum

CHECK_UNICODE = "\u2714"
CROSS_UNICODE = "\u274c"


class Color(Enum):
    """
    Contains foreground colors for the command line
    """

    BLACK = "\033[30m"
    RED = "\033[31m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"
    ERROR = "\033[91m"  # Salmon-ish
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE = "\033[95m"


class Background(Enum):
    """
    Contains background colors for the command line
    """

    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    PURPLE = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"


class Format(Enum):
    """
    Contains text formatting options
    """

    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    HIDDEN = "\033[8m"


# pylint: disable=bad-continuation
def pprint(
    message: str,
    color: Color = None,
    background: Background = None,
    formats: list = None,
    line_ending: str = "\n",
) -> None:
    """
    Prints a message

    Parameters
    ----------
    message : str
        The message to print
    color : Color
        Foreground color of the text
    background : Background
        Background color of the text
    formats : list
        One or more formats to apply, e.g. bold or underlined
    line_ending : str
        The line ending to print
    """
    print_string = ""
    if color:
        print_string += color.value
    if background:
        print_string += background.value
    if formats:
        print_string += "".join([style.value for style in formats])
    print_string += message + Format.END.value

    print(print_string, end=line_ending, flush=True)


# pylint: disable=bad-continuation
def pprint_start(
    message: str,
    color: Color = None,
    background: Background = None,
    formats: list = None,
):
    """
    Prints a message

    Parameters
    ----------
    message : str
        The message to print
    color : Color
        Foreground color of the text
    background : Background
        Background color of the text
    formats : list
        One or more formats to apply, e.g. bold or underlined
    """
    pprint("  " + message, color, background, formats, "\r")


# pylint: disable=bad-continuation
def pprint_complete(
    message: str,
    succeeded: bool,
    color: Color = None,
    background: Background = None,
    formats: list = None,
) -> None:
    """
    Prints a message about a completed operation

    Parameters
    ----------
    message : str
        The message to print
    succeeded : bool
        Whether the operation succeeded
    color : Color
        Foreground color of the text
    background : Background
        Background color of the text
    formats : list
        One or more formats to apply, e.g. bold or underlined
    """
    pprint(
        "{0}{1}".format((CHECK_UNICODE + " ") if succeeded else CROSS_UNICODE, message),
        color,
        background,
        formats,
    )


def readable_bytes(bytes, suffix="B") -> str:
    """
    Prints size of file

    Parameters
    ----------
    bytes
        Bytes to format
    suffix='B'
        What to print after the SI prefix
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(bytes) < 1024.0:
            return "%3.1f%s%s" % (bytes, unit, suffix)
        bytes /= 1024.0
    return "%.1f%s%s" % (bytes, "Yi", suffix)
