"""
Manages devices
"""
import contextlib
import multiprocessing
import os
import socket
import time
import uuid

from logical_backup.objects import Device
from logical_backup import db
from logical_backup.db import DatabaseError
from logical_backup.utilities import device, testing
from logical_backup.strings import Configurations, DeviceArguments, Errors


@contextlib.contextmanager
def fake_lock():
    yield None


def _device_has_space(dev: Device, needed_space: int) -> bool:
    """
    Checks if a device has enough space
    """
    return dev.available_space - dev.allocated_space >= needed_space


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
        self,
        sock: socket.socket,
        max_connection_count=Configurations.MAX_CONNECTIONS.value,
    ):
        """
        Set up socket for listening
        """
        sock.settimeout(Configurations.CONNECTION_TIMEOUT.value)
        self.__stop = False  # pragma: no mutate
        self.__socket = sock
        self.__socket.listen(max_connection_count)
        self.__connections = {}
        self.__last_heard = {}

        self.__devices = {}
        self.__messages = {
            str(DeviceArguments.KEY_ACCEPT): [],
            str(DeviceArguments.KEY_INITIALIZE): [],
        }
        self.__errors = {
            str(DeviceArguments.KEY_ACCEPT): [],
            str(DeviceArguments.KEY_INITIALIZE): [],
        }

        devices = db.get_devices()
        for dev in devices:
            self._add_device(dev)

    def _accept_connection(self) -> None:
        """
        See if there are any pending connections
        """
        while True:
            try:
                conn = self.__socket.accept()[0]
                conn.settimeout(float(Configurations.MESSAGE_TIMEOUT.value))
                self._initialize_connection(conn)
            except socket.timeout:
                break
            # Want to catch any possible failure, to add to errors
            # pylint: disable=broad-except
            except Exception as exc:
                self._add_error(str(DeviceArguments.KEY_ACCEPT), str(exc))
                break

    def _initialize_connection(self, connection: socket.socket):
        """
        Set up a connection
        """
        message = connection.recv(Configurations.MAX_MESSAGE_SIZE.value).decode()
        if (
            not message.startswith(str(DeviceArguments.COMMAND_HELLO))
            or not str(DeviceArguments.COMMAND_DELIMITER) in message
        ):
            self._add_error(
                str(DeviceArguments.KEY_INITIALIZE),
                DeviceArguments.ERROR_BAD_HELLO(message),
            )
            connection.send(str(DeviceArguments.RESPONSE_INVALID).encode())
            connection.close()
            return

        txid = message.split(str(DeviceArguments.COMMAND_DELIMITER))[1]
        self.__connections[txid] = connection
        self.__last_heard[txid] = time.time()
        self.__errors[txid] = []
        self.__messages[txid] = []

    def _auto_close_connection(self, txid: str):
        """
        Auto close connection, if expired
        """
        if (
            time.time() - self.__last_heard[txid]
        ) > Configurations.CLOSE_CONNECTION_AFTER.value:
            self.close(txid)
            self._add_message(
                str(DeviceArguments.KEY_INITIALIZE),
                DeviceArguments.MESSAGE_CLOSING_CONNECTION(txid),
            )

    def _receive_messages(self) -> None:
        """
        Check for sent messages
        """
        transactions_to_close = []
        for txid, connection in self.__connections.items():
            try:
                message = connection.recv(
                    Configurations.MAX_MESSAGE_SIZE.value
                ).decode()
                self.__last_heard[txid] = time.time()

                if message == str(DeviceArguments.COMMAND_STOP):
                    self.__stop = True
                    break

                self._process_message(txid, message, connection)
            except socket.timeout:
                self._auto_close_connection(txid)
            except BrokenPipeError:
                transactions_to_close.append(txid)
            # Want to catch any possible failure, to add to errors
            # pylint: disable=broad-except
            except Exception as exc:
                self._add_error(txid, str(exc))
                connection.send(
                    DeviceArguments.ERROR_UNKNOWN_EXCEPTION(str(exc)).encode()
                )
                continue

        for txid in transactions_to_close:
            self.close(txid)

    def loop(self) -> None:
        """
        Accept connections and receive/process messages
        """
        while not self.stopped:
            self._accept_connection()
            self._receive_messages()

    def _process_message(
        self, txid: str, message: str, connection: socket.socket
    ) -> None:
        """
        Process a received message
        """
        parts = message.split(str(DeviceArguments.COMMAND_DELIMITER))
        if parts[0] == str(DeviceArguments.COMMAND_CHECK_DEVICE):
            self._check_device_space(txid, parts, connection)
        elif parts[0] == str(DeviceArguments.COMMAND_GET_DEVICE):
            self._pick_device(txid, parts, connection)
        elif parts[0] == str(DeviceArguments.COMMAND_ADD_DEVICE):
            self._add_device(txid, parts[1:], connection)
        else:
            connection.send(str(DeviceArguments.RESPONSE_INVALID).encode())
            self._add_error(txid, DeviceArguments.ERROR_UNKNOWN_COMMAND(message))

    # pylint: disable=bad-continuation
    def _check_message_length(
        self, txid: str, message_parts: list, length: int, connection: socket.socket
    ) -> bool:
        """
        Checks message is at least N parts long
        """
        if len(message_parts) < length:
            self._add_error(
                txid, DeviceArguments.ERROR_INSUFFICIENT_PARAMETERS(message_parts[0])
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID).encode())

        return len(message_parts) >= length

    # pylint: disable=bad-continuation
    def _check_device_space(
        self, txid: str, message_parts: list, connection: socket.socket
    ) -> None:
        """
        Checks that a given device has enough space
        """
        if not self._check_message_length(txid, message_parts, 3, connection):
            return

        # Check if device path exists, size is valid
        device_path, requested_size = message_parts[1], message_parts[2]
        if not requested_size.isnumeric():
            self._add_error(
                txid, DeviceArguments.ERROR_SIZE_IS_NOT_NUMBER(requested_size)
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID).encode())
            return

        requested_size = int(requested_size)
        if int(requested_size) == 0:
            self._add_error(txid, str(DeviceArguments.ERROR_SIZE_IS_ZERO))
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID).encode())
            return

        if device_path not in self.__devices:
            self._add_error(txid, DeviceArguments.ERROR_UNKNOWN_DEVICE(device_path))
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID).encode())
            return

        # Will this device fit the request
        if (
            _device_has_space(self.__devices[device_path], int(requested_size))
            and requested_size > 0
        ):
            # If yes, add the requested space to the portion
            # this one has allocated already
            self.__devices[device_path].allocated_space += requested_size
            connection.send(format_message(DeviceArguments.RESPONSE_OK).encode())
            return

        # Otherwise, check all devices
        for dev in self.__devices.values():
            # If one has sufficient space, substitute it for the one provided
            # NOTE: will NOT reserve space yet - another call MUST be made
            # This allows a user to reject the substitute first
            if 0 < requested_size <= dev.available_space - dev.allocated_space:
                connection.send(
                    format_message(
                        DeviceArguments.RESPONSE_SUBSTITUTE, [dev.device_path]
                    ).encode()
                )
                return

        # Otherwise, exit as unresolvable
        connection.send(str(DeviceArguments.RESPONSE_UNRESOLVABLE).encode())

    def _pick_device(
        self, txid: str, message_parts: list, connection: socket.socket
    ) -> None:
        """
        Finds a device with sufficient space
        """
        if not self._check_message_length(txid, message_parts, 2, connection):
            return

        requested_size = message_parts[1]
        if not requested_size.isnumeric():
            self._add_error(
                txid, DeviceArguments.ERROR_SIZE_IS_NOT_NUMBER(requested_size)
            )
            connection.send(format_message(DeviceArguments.RESPONSE_INVALID).encode())
            return

        found_device = False
        for dev in self.__devices.values():
            if _device_has_space(dev, int(requested_size)):
                found_device = True
                dev.allocated_space += int(requested_size)
                connection.send(
                    format_message(
                        DeviceArguments.RESPONSE_SUBSTITUTE, [dev.device_path]
                    ).encode()
                )
                break

        if not found_device:
            connection.send(str(DeviceArguments.RESPONSE_UNRESOLVABLE).encode())

    def _add_new_device(
        self, txid: str, message_parts: list, connection: socket.socket
    ) -> None:
        """
        Add a new device to the manager
        """
        if len(message_parts) != 4:
            connection.send(str(DeviceArguments.RESPONSE_INVALID).encode())
        else:
            device = Device()
            device.set(*message_parts)
            result = db.add_device(device)

            if result == DatabaseError.SUCCESS:
                self._add_device(device)

            connection.send(str(result.value).encode())

    def _add_device(self, device_to_add: Device):
        """
        Add an existing device to the manager tracking system
        """
        device_to_add.available_space = device.get_device_space(
            device_to_add.device_path
        )
        device_to_add.allocated_space = 0
        self.__devices[device_to_add.device_path] = device_to_add

    def errors(self, txid: str) -> list:
        """
        Get errors
        """
        return self.__errors[txid] if txid in self.__errors else None

    def messages(self, txid: str) -> list:
        """
        Get messages
        """
        return self.__messages[txid] if txid in self.__messages else None

    def close(self, txid: str):
        """
        Close a given connection
        """
        if txid not in self.__connections:
            return

        self.__connections[txid].close()
        del self.__connections[txid]
        del self.__last_heard[txid]
        del self.__errors[txid]
        del self.__messages[txid]

    def stop(self):
        """
        Set stopped
        """
        self.__stop = True

    @property
    def stopped(self) -> bool:
        """
        Returns if this was stopped
        """
        return self.__stop

    @property
    def connections(self) -> list:
        """
        Returns connections, for testing only
        """
        return self.__connections if testing.is_test() else []

    def _add_error(self, txid: str, error: str):
        """
        Adds an error for a transaction
        """
        self.__errors[txid].append(error)

    def _add_message(self, txid: str, message: str):
        """
        Adds a message for a transaction
        """
        self.__messages[txid].append(message)

    def exit(self):
        """
        Close the socket
        """
        self.__socket.close()


def format_message(command: DeviceArguments, parameters: list = None) -> str:
    """
    Formats command and parameters into a coherent string
    """
    return str(DeviceArguments.COMMAND_DELIMITER).join(
        [str(command)] + (parameters if parameters else [])
    )


# pylint: disable=bad-continuation
def send_message(
    message: list,
    sock: socket.socket,
    lock: multiprocessing.synchronize.Lock,
    should_lock: bool = True,
):
    """
    Sends a message through the socket
    Message should be a list of pieces, to join
    """
    with lock if should_lock else fake_lock():
        sock.send(format_message(message[0], message[1:]).encode())


def get_connection() -> tuple:
    """
    Creates a connection to the device manager
    Returns connection, txid
    """
    txid = str(uuid.uuid4())

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(DeviceArguments.SOCKET_PATH))
    client_sock.send(format_message(DeviceArguments.COMMAND_HELLO, [txid]).encode())

    return (client_sock, txid)


def get_server_connection() -> socket.socket:
    """
    Creates a new bound connection to the server socket
    """
    if os.path.exists(str(DeviceArguments.SOCKET_PATH)):  # pragma: no cover
        os.unlink(str(DeviceArguments.SOCKET_PATH))

    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.bind(str(DeviceArguments.SOCKET_PATH))

    return server_sock


def close_server(device_manager: DeviceManager):
    """
    Cleans up the server socket
    CAN ONLY USE IF STOPPED
    """
    if not device_manager.stopped:
        raise AttributeError(Errors.STOP_MANAGER_BEFORE_CLOSE)

    device_manager.exit()
    os.unlink(str(DeviceArguments.SOCKET_PATH))
