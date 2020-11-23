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
    readable_bytes,
    readable_duration,
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
        .with_line_ending("\r")
    )
    psp.print_message()
    out = capsys.readouterr()
    assert out.out == psp.get_styled_message(), "Expected message prints"


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

    psp = PrettyStatusPrinter("ellipsis").with_ellipsis()
    psp.print_start()
    psp.print_complete(False)

    out = capsys.readouterr()
    assert "ellipsis...Failed" in out.out, "Ellipsis in fail message"


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


def test_custom_result(capsys):
    """
    .
    """
    # Negative two, because why not
    psp = (
        PrettyStatusPrinter("testing thing")
        .with_custom_result(-2, True)
        .with_color_for_result(-2, Color.WHITE)
        .with_message_postfix_for_result(-2, "Random number")
    )
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

    psp.print_start()
    psp.print_complete(-2)

    out = capsys.readouterr()
    assert (
        "testing thing..." + Format.END.value + "\r" in out.out
    ), "First line to be overwritten is printed"
    assert "testing thing...Random number" in out.out, "Custom result message prints"
    assert CHECK_UNICODE in out.out, "Success check prints"
    assert Color.WHITE.value in out.out, "Custom result color is printed"


def test_byte_printing():
    """
    Check printing library output
    """
    assert readable_bytes(100) == "100.0B", "Bytes output"
    assert readable_bytes(2 * 1024) == "2.0KiB", "KiloBytes output"
    assert readable_bytes(3 * 1024 * 1024) == "3.0MiB", "MegaBytes output"
    assert readable_bytes(4.056 * 1024 * 1024) == "4.1MiB", "MegaBytes output"
    assert readable_bytes(4.056 * 1024 * 1024) == "4.1MiB", "MegaBytes output"
    assert readable_bytes(1 * 1024 ** 8) == "1.0YiB", "Super huge output"
    assert readable_bytes(1 * 1024 ** 9) == "1024.0YiB", "Super super huge output"


def test_readable_time():
    """
    .
    """
    assert readable_duration(0) == "0 seconds", "No seconds"
    assert readable_duration(1) == "1 second", "One second"
    assert readable_duration(60) == "1 minute, 0 seconds", "One minute"
    assert readable_duration(61) == "1 minute, 1 second", "One minute, one second"
    assert readable_duration(3600) == "1 hour, 0 minutes, 0 seconds", "One hour"
    assert (
        readable_duration(3601) == "1 hour, 0 minutes, 1 second"
    ), "One hour, one second"
    assert readable_duration(86400) == "1 day, 0 hours, 0 minutes, 0 seconds", "One day"
    assert (
        readable_duration(86401) == "1 day, 0 hours, 0 minutes, 1 second"
    ), "One day, one second"
    assert (
        readable_duration(90061) == "1 day, 1 hour, 1 minute, 1 second"
    ), "One of everything"
    assert (
        readable_duration(180122) == "2 days, 2 hours, 2 minutes, 2 seconds"
    ), "Two of everything"
