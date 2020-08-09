"""
Tests the device manager
"""
import os
from os import path as os_path
import socket
import multiprocessing
from multiprocessing import synchronize
import threading
from time import sleep

from pytest import fixture, raises

from logical_backup import db
from logical_backup.objects import Device
from logical_backup.utilities import device
from logical_backup.utilities.device_manager import (
    DeviceManager,
    _device_has_space,
    send_message,
    format_message,
)

# pylint: disable=unused-import
from logical_backup.utilities.testing import counter_wrapper, auto_set_testing
from logical_backup.strings import DeviceArguments


@fixture(autouse=True)
def __unbind_socket():
    """
    Removes socket path, if exists
    """
    if os_path.exists(str(DeviceArguments.SOCKET_PATH)):
        os.unlink(str(DeviceArguments.SOCKET_PATH))

    yield

    if os_path.exists(str(DeviceArguments.SOCKET_PATH)):
        os.unlink(str(DeviceArguments.SOCKET_PATH))


def __run_server(lock):
    with lock:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock.bind(str(DeviceArguments.SOCKET_PATH))
        sock.listen(1)

    # pylint: disable=unused-variable
    conn, client = sock.accept()
    message = conn.recv(10)
    conn.send(message)
    sock.close()


def test_device_has_space():
    """
    .
    """
    dev = Device()
    dev.available_space = 100
    dev.allocated_space = 100

    assert not _device_has_space(dev, 10), "Full device does not have space"

    dev.allocated_space = 95
    assert not _device_has_space(dev, 10), "Semi-full device does not have space"

    dev.allocated_space = 90
    assert _device_has_space(dev, 10), "File that fills device has space"

    dev.allocated_space = 0
    assert _device_has_space(dev, 10), "Empty device has space"


def test_format_message():
    """
    .
    """
    formatted = format_message(DeviceArguments.COMMAND_GET_DEVICE)
    assert formatted == str(DeviceArguments.COMMAND_GET_DEVICE), "Only command returned"

    formatted = format_message(DeviceArguments.COMMAND_GET_DEVICE, ["foo", "bar"])
    expected = str(DeviceArguments.COMMAND_DELIMITER).join(
        [str(DeviceArguments.COMMAND_GET_DEVICE), "foo", "bar"]
    )
    assert formatted == expected, "Command and parameters"


def test_send_message(monkeypatch):
    """
    .
    """

    lock = multiprocessing.Lock()

    # Lock extends SemLock, so need to override the enter method
    # on the semlock class itself to check it is acquired
    enter_func = synchronize.SemLock.__enter__

    @counter_wrapper
    def mock_enter(self):
        return enter_func(self)

    monkeypatch.setattr(synchronize.SemLock, "__enter__", mock_enter)

    server_thread = threading.Thread(target=__run_server, args=[lock])
    server_thread.start()
    # Give server time to bind, to avoid lock race condition
    sleep(0.2)

    with lock:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(str(DeviceArguments.SOCKET_PATH))
    send_message(["foo"], client_sock, lock)
    message = client_sock.recv(10)
    assert message.decode() == "foo", "Message received"
    assert mock_enter.counter == 3, "Acquire called by server, client, and send"
    server_thread.join()


def test_errors_messages_empty(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))
    manager = DeviceManager(sock)
    assert manager.errors == [], "No errors"
    assert manager.messages == [], "No messages"


def test_accept_connection(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    with raises(ConnectionRefusedError):
        client_sock.connect(str(DeviceArguments.SOCKET_PATH))

    manager = DeviceManager(sock)
    accept_thread = threading.Thread(target=manager._accept_connection)
    accept_thread.start()

    client_sock.connect(str(DeviceArguments.SOCKET_PATH))
    assert manager.errors == [], "No errors in accepting connection"
    client_sock.sendall(b"garbage data")

    assert True, "No exception thrown"


def test_stop_message_immediately_stops(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_process_message(message, conn):
        return None

    manager = DeviceManager(sock)
    monkeypatch.setattr(manager, "_process_message", mock_process_message)
    accept_thread = threading.Thread(target=manager._accept_connection)
    accept_thread.start()

    # Wait for thread to start before connecting
    sleep(0.2)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(DeviceArguments.SOCKET_PATH))

    # Wait for connection to be accepted before message is sent
    sleep(0.2)

    assert manager.errors == [], "No errors in accepting connection"
    assert not manager.stopped, "Device manager not stopped"
    client_sock.sendall(str(DeviceArguments.COMMAND_STOP).encode())

    manager._receive_messages()

    assert mock_process_message.counter == 0, "Process message not called"
    assert manager.stopped, "Device manager stopped"


def test_receive_message_stops_with_no_message(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_process_message(message, connection):
        return None

    manager = DeviceManager(sock)
    monkeypatch.setattr(manager, "_process_message", mock_process_message)
    accept_thread = threading.Thread(target=manager._accept_connection)
    accept_thread.start()

    sleep(0.1)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(DeviceArguments.SOCKET_PATH))
    assert manager.errors == [], "No errors in accepting connection"

    sleep(0.1)

    manager._receive_messages()

    assert mock_process_message.counter == 0, "Process message not called"
    assert not manager.stopped, "Device manager not stopped"


def test_receive_messages(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_process_message(message, connection):
        return None

    manager = DeviceManager(sock)
    monkeypatch.setattr(manager, "_process_message", mock_process_message)
    accept_thread = threading.Thread(target=manager._accept_connection)
    accept_thread.start()

    sleep(0.1)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(DeviceArguments.SOCKET_PATH))

    sleep(0.1)

    client_sock.sendall("random".encode())
    manager._receive_messages()

    assert mock_process_message.counter == 1, "Process message called"
    assert not manager.stopped, "Device manager not stopped"


def test_loop(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    @counter_wrapper
    def mock_accept_connection():
        return None

    @counter_wrapper
    def mock_receive_messages():
        manager.stop()

    manager = DeviceManager(sock)
    monkeypatch.setattr(manager, "_accept_connection", mock_accept_connection)
    monkeypatch.setattr(manager, "_receive_messages", mock_receive_messages)

    manager.loop()

    assert mock_accept_connection.counter == 1, "Accept connection called"
    assert mock_receive_messages.counter == 1, "Receive messages called"


def test_accept_exceptions(monkeypatch):
    """
    .
    """

    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_socket_accept(timeout):
        raise socket.timeout("No response")

    manager = DeviceManager(sock)
    monkeypatch.setattr(socket.socket, "accept", mock_socket_accept)

    manager._accept_connection()

    assert manager.errors == [], "Timeout doesn't add error"
    assert mock_socket_accept.counter == 1, "Accept only called once"

    @counter_wrapper
    # pylint: disable=unused-argument
    def fail_socket_accept(timeout):
        raise ConnectionRefusedError("Client hung up")

    monkeypatch.setattr(socket.socket, "accept", fail_socket_accept)

    manager._accept_connection()

    assert manager.errors == ["Client hung up"], "Error added"
    assert fail_socket_accept.counter == 1, "Accept only called once"


def test_process_message(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))
    manager = DeviceManager(sock)

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_device_space(parts, connection):
        return None

    @counter_wrapper
    # pylint: disable=unused-argument
    def mock_pick_device(parts, connection):
        return None

    monkeypatch.setattr(manager, "_check_device_space", mock_device_space)
    monkeypatch.setattr(manager, "_pick_device", mock_pick_device)

    message = str(DeviceArguments.COMMAND_DELIMITER).join(
        [str(DeviceArguments.COMMAND_CHECK_DEVICE), "123", "foo"]
    )
    manager._process_message(message, None)
    assert mock_device_space.counter == 1, "Device space called once"
    assert mock_pick_device.counter == 0, "Pick device not called"

    message = str(DeviceArguments.COMMAND_DELIMITER).join(
        [str(DeviceArguments.COMMAND_GET_DEVICE), "123"]
    )
    manager._process_message(message, None)
    assert mock_device_space.counter == 1, "Device space not called again"
    assert mock_pick_device.counter == 1, "Pick device called"


def test_check_message_length(monkeypatch):
    """
    .
    """
    monkeypatch.setattr(db, "get_devices", lambda device=None: [])
    monkeypatch.setattr(device, "get_device_space", lambda device=None: None)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(DeviceArguments.SOCKET_PATH))
    manager = DeviceManager(sock)
    accept_thread = threading.Thread(target=manager._accept_connection)
    accept_thread.start()

    # Give server time to bind, to avoid lock race condition
    sleep(0.2)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(DeviceArguments.SOCKET_PATH))

    # Give server time to accept
    sleep(0.1)

    server_client_sock = manager.connections[0]

    assert manager._check_message_length(
        [1, 2, 3], 3, server_client_sock
    ), "Three-part message works"

    assert not manager._check_message_length(
        ["test-command", "12345"], 3, server_client_sock
    ), "Missing message part fails"

    assert manager.errors == [
        DeviceArguments.ERROR_INSUFFICIENT_PARAMETERS("test-command")
    ]
    received = client_sock.recv(100).decode()
    assert received == str(
        DeviceArguments.RESPONSE_INVALID
    ), "Insufficient param count message sent"
