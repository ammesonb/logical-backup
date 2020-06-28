"""
Tests printing of status messages
"""

from logical_backup.pretty_print import (
    PrettyStatusPrinter,
    CHECK_UNICODE,
    CROSS_UNICODE,
    Color,
    Background,
    Format,
)


def test_basic_print(capsys):
    """
    .
    """
    psp = PrettyStatusPrinter("test message")
    psp.print_message()

    out = capsys.readouterr()
    assert "test message" + Format.END.value + "\n" in out.out, "Message is printed"
    assert "..." not in out.out, "Message has no dots"


def test_formatted_print(capsys):
    """
    .
    """
    psp = (
        PrettyStatusPrinter("a message")
        .with_specific_color(Color.MAGENTA)
        .with_background_color(Background.BLUE)
        .with_styles([Format.BOLD])
        .with_styles([Format.UNDERLINE])
        .with_line_ending("\r\n")
    )
    psp.print_message()

    out = capsys.readouterr()
    for part in [
        "a message" + Format.END.value + "\r\n",
        Color.MAGENTA.value,
        Background.BLUE.value,
        Format.BOLD.value,
        Format.UNDERLINE.value,
    ]:
        assert part in out.out, "Expected component is printed"


def test_basic_start_complete(capsys):
    """
    .
    """
    psp = PrettyStatusPrinter("testing thing")
    psp.print_start()
    psp.print_complete(True)

    out = capsys.readouterr()
    assert (
        "testing thing..." + Format.END.value + "\r" in out.out
    ), "First line to be overwritten is printed"
    assert "testing thing...Complete" in out.out, "Complete message prints"
    assert CHECK_UNICODE in out.out, "Complete check prints"
    assert Color.GREEN.value in out.out, "Complete color is printed"

    psp.print_start()
    psp.print_complete(False)

    out = capsys.readouterr()
    assert (
        "testing thing..." + Format.END.value + "\r" in out.out
    ), "First line to be overwritten is printed"
    assert "testing thing...Failed" in out.out, "Failure message prints"
    assert CROSS_UNICODE in out.out, "Failure cross prints"
    assert Color.ERROR.value in out.out, "Error color is printed"


def test_start_complete_no_ellipsis(capsys):
    """
    .
    """
    psp = PrettyStatusPrinter("ellipsis - ").with_ellipsis(False)
    psp.print_start()
    psp.print_complete(True)

    out = capsys.readouterr()
    assert "ellipsis - Complete" in out.out, "No ellipsis in success message"
    assert "..." not in out.out, "No ellipsis printed"

    psp = PrettyStatusPrinter("ellipsis - ").with_ellipsis(False)
    psp.print_start()
    psp.print_complete(False)

    out = capsys.readouterr()
    assert "ellipsis - Failed" in out.out, "No ellipsis in fail message"
    assert "..." not in out.out, "No ellipsis printed"


def test_formatted_start_complete(capsys):
    """
    .
    """
    psp = (
        PrettyStatusPrinter("formatted")
        .with_color_for_result(True, Color.CYAN)
        .with_color_for_result(False, Color.RED)
        .with_message_postfix_for_result(True, "Done")
        .with_message_postfix_for_result(False, "Error")
    )
    psp.print_start()
    psp.print_complete(True)

    out = capsys.readouterr()
    assert (
        "formatted..." + Format.END.value + "\r" in out.out
    ), "First line to be overwritten is printed"
    assert "formatted...Done" in out.out, "Custom complete message prints"
    assert CHECK_UNICODE in out.out, "Complete check prints"
    assert Color.CYAN.value in out.out, "Custom complete color is printed"

    psp.print_start()
    psp.print_complete(False)

    out = capsys.readouterr()
    assert (
        "formatted..." + Format.END.value + "\r" in out.out
    ), "First line to be overwritten is printed"
    assert "formatted...Error" in out.out, "Custom failure message prints"
    assert CROSS_UNICODE in out.out, "Failure cross prints"
    assert Color.RED.value in out.out, "Custom failure color is printed"


def test_specific_color_overrides_success(capsys):
    """
    .
    """
    psp = PrettyStatusPrinter("specific").with_specific_color(Color.CYAN)
    psp.print_start()
    psp.print_complete(True)

    out = capsys.readouterr()
    assert Color.CYAN.value in out.out, "Completion color should be cyan not default"

    psp.print_start()
    psp.print_complete(False)

    out = capsys.readouterr()
    assert Color.CYAN.value in out.out, "Failure color should be cyan not default"
