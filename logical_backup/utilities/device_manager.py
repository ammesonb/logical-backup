"""
Manages devices
"""
import multiprocessing
import socket

from logical_backup.objects import Device
from logical_backup import db
from logical_backup import utility
from logical_backup.strings import Configurations, DeviceArguments


def __device_has_space(device: Device, needed_space: int) -> bool:
    """
    Checks if a device has enough space
    """
    return device.available_space - device.allocated_space >= needed_space


class DeviceManager:
    """
    Manages devices to maintain available space, etc.
    shared across processes

    Requests:
    check-device,<device_path>,<requested_size>
        Check a given device path for a requested amount of space

    Responses:
    ok
        Response as submitted is valid
    substitute,<other_device_path>
        The submitted device is not available, use this one instead
    partial
        Response is satisfiable but not as submitted
        E.g., this folder must be split across multiple devices
    unresolvable
        No set of devices will work
    invalid
        Provided parameteres are not valid
    """

    # pylint: disable=bad-continuation
    def __init__(
        self, sock: socket.socket, max_connections: int = Configurations.MAX_CONNECTIONS
    ):
        """
        Set up socket for listening
        """
        sock.settimeout(Configurations.CONNECTION_TIMEOUT)
        self.__socket = sock
        self.__socket.listen(max_connections)
        self.__connections = []

        self.__devices = {}
        self.__messages = []
        self.__errors = []

        devices = db.get_devices()
        for device in devices:
            device.available_space = utility.get_device_space(device.device_path)
            device.allocated_space = 0
            self.__devices[device.device_path] = device

    def __accept_connection(self) -> None:
        """
        See if there are any pending connections
        """
        while True:
            try:
                conn = self.__socket.accept()[0]
                conn.settimeout(Configurations.MESSAGE_TIMEOUT)
                self.__connections.append(conn)
            except socket.timeout:
                break
            # Want to catch any possible failure, to add to errors
            # pylint: disable=broad-except
            except Exception as exc:
                self.__errors.append(str(exc))
                break

    def __receive_messages(self) -> None:
        """
        Check for sent messages
        """
        while True:
            for connection in self.__connections:
                try:
                    message = connection.recv(Configurations.MAX_MESSAGE_SIZE)
                    self.__process_message(message, connection)
                except socket.timeout:
                    continue
                # Want to catch any possible failure, to add to errors
                # pylint: disable=broad-except
                except Exception as exc:
                    self.__errors.append(str(exc))
                    continue

    def __process_message(self, message: str, connection) -> None:
        """
        Process a received message
        """
        parts = message.split(",")
        if parts[0] == DeviceArguments.COMMAND_CHECK_DEVICE:
            self.__check_device_space(parts, connection)
        elif parts[0] == DeviceArguments.COMMAND_GET_DEVICE:
            pass

    # pylint: disable=bad-continuation
    def __check_message_length(
        self, message_parts: list, length: int, connection: socket.socket
    ) -> bool:
        """
        Checks message is at least N parts long
        """
        if len(message_parts) < length:
            self.__errors.append(
                DeviceArguments.ERROR_INSUFFICIENT_PARAMETERS(message_parts[0])
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID))

        return len(message_parts) < length

    # pylint: disable=bad-continuation
    def __check_device_space(
        self, message_parts: list, connection: socket.socket
    ) -> None:
        """
        Checks that a given device has enough space
        """
        if not self.__check_message_length(message_parts, 3, connection):
            return

        # Check if device path exists, size is valid
        device_path, requested_size = message_parts[1], message_parts[2]
        if device_path not in self.__devices:
            self.__errors.append(DeviceArguments.ERROR_UNKNOWN_DEVICE(device_path))
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID))
            return

        if not requested_size.isnumeric():
            self.__errors.append(
                DeviceArguments.ERROR_SIZE_IS_NOT_NUMBER(requested_size)
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID))
            return

        # Will this device fit the request
        if __device_has_space(self.__devices[device_path], int(requested_size)):
            # If yes, add the requested space to the portion this one has allocated already
            self.__devices[device_path].allocated_space += requested_size
            connection.send(format_message(DeviceArguments.RESPONSE_OK))
            return

        # Otherwise, check all devices
        for device in self.__devices:
            # If one has sufficient space, substitute it for the one provided
            # NOTE: will NOT reserve space yet - another call MUST be made
            # This allows a user to reject the substitute first
            if device.available_space - device.allocated_space >= requested_size:
                connection.send(
                    format_message(
                        DeviceArguments.RESPONSE_SUBSTITUTE, [device.device_path]
                    )
                )
                return

        # Otherwise, exit as unresolvable
        connection.send(DeviceArguments.RESPONSE_UNRESOLVABLE)

    def __pick_device(self, message_parts: list, connection: socket.socket) -> None:
        """
        Finds a device with sufficient space
        """
        if not self.__check_message_length(message_parts, 2, connection):
            return

        requested_size = message_parts[1]
        if not requested_size.isnumeric():
            self.__errors.append(
                DeviceArguments.ERROR_SIZE_IS_NOT_NUMBER(requested_size)
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID))

        for device in self.__devices:
            if __device_has_space(device, int(message_parts[2])):
                connection.send(
                    format_message(
                        DeviceArguments.RESPONSE_SUBSTITUTE, [device.device_path]
                    )
                )
                break

    @property
    def errors(self) -> list:
        """
        Get errors
        """
        return self.__errors

    @property
    def messages(self) -> list:
        """
        Get messages
        """
        return self.__messages


def format_message(command: DeviceArguments, parameters: list = None) -> str:
    """
    Formats command and parameters into a coherent string
    """
    return DeviceArguments.COMMAND_DELIMITER.join(
        [str(command), parameters if parameters else []]
    )


# pylint: disable=bad-continuation
def send_message(
    message: list, sock: socket.socket, lock: multiprocessing.synchronize.Lock
):
    """
    Sends a message through the socket
    Message should be a list of pieces, to join
    """
    with lock:
        sock.send(format_message(message[0], message[1:]))
