"""
Device helper functions
"""
import psutil

from logical_backup.utilities import process
from logical_backup.pretty_print import PrettyStatusPrinter


def __get_device_path(mount_point: str) -> str:
    """
    Resolve the /dev/ path for a given mounted device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    partitions = psutil.disk_partitions()
    partition = [part for part in partitions if part.mountpoint == mount_point]
    return partition[0].device if partition else None


def get_device_serial(mount_point: str) -> str:
    """
    Get the serial ID for a device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    message = (
        PrettyStatusPrinter("Checking device serial")
        .with_message_postfix_for_result(False, "No serial found!")
        .print_start()
    )

    serial = None  # pragma: no mutate
    partition = __get_device_path(mount_point)
    if partition:
        commands = [  # pragma: no mutate
            [
                "udevadm",
                "info",
                "--query=all",
                "--name=" + partition,
            ],  # pragma: no mutate
            ["grep", " disk/by-uuid/"],  # pragma: no mutate
            # pylint: disable=anomalous-backslash-in-string
            # This is a bash escape, not regex
            ["sed", "s/.*by-uuid\///"],  # pragma: no mutate
        ]  # pragma: no mutate
        output = process.run_piped_command(commands)

        if output["stdout"].strip():
            serial = output["stdout"].strip().decode("utf-8")

    if serial:
        message.with_message_postfix_for_result(
            True, "Found " + serial
        ).print_complete()
    else:
        message.print_complete(False)

    return serial


def get_device_uuid(mount_point: str) -> str:
    """
    Get the system UUID for a device

    Parameters
    ----------
    mount_point : str
        The mount point for the drive
    """
    message = (
        PrettyStatusPrinter("Checking device UUID")
        .with_message_postfix_for_result(False, "No UUID found!")
        .print_start()
    )

    uuid = None  # pragma: no mutate
    partition = __get_device_path(mount_point)
    if partition:
        commands = [  # pragma: no mutate
            ["blkid", partition, "-o", "value"],
            ["head", "-1"],  # pragma: no mutate
        ]  # pragma: no mutate
        output = process.run_piped_command(commands)

        if output["stdout"].strip():
            uuid = output["stdout"].strip().decode("utf-8")

    if uuid:
        message.with_message_postfix_for_result(True, "Found " + uuid).print_complete()
    else:
        message.print_complete(False)

    return uuid


def get_device_space(mount_point: str) -> int:
    """
    Return available drive space, in bytes

    Parameters
    ----------
    mount_point : str
        The mount point

    Returns
    -------
    float
        Bytes of available space
    """
    available = psutil.disk_usage(mount_point)
    return available.free
