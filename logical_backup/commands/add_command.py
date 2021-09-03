"""
The "add" class of commands
"""
from multiprocessing import synchronize
import socket
from typing import Optional

from logical_backup.commands.base_command import BaseCommand, Config
from logical_backup.commands.actions import AddFileAction
from logical_backup import db
from logical_backup.db import DatabaseError

from logical_backup.utilities import files, device as device_util
from logical_backup.pretty_print import readable_bytes
from logical_backup.objects import File
from logical_backup.utilities import device_manager
from logical_backup.strings import Errors, Info, DeviceArguments, Configurations


# pylint: disable=too-few-public-methods
class AddConfig(Config):
    """
    Add command config
    """

    adding_file = None
    adding_folder = None
    adding_device = None
    to_specific_device = None

    # pylint: disable=bad-continuation
    def __init__(
        self,
        adding_file: bool = None,
        adding_folder: bool = None,
        adding_device: bool = None,
        to_specific_device: bool = None,
    ):
        self.adding_file = adding_file
        self.adding_folder = adding_folder
        self.adding_device = adding_device
        self.to_specific_device = to_specific_device


class AddCommand(BaseCommand):
    """
    Command for adding files, folders, and devices
    """

    # pylint: disable=bad-continuation,too-many-arguments
    def __init__(
        self,
        arguments: dict,
        manager: device_manager.DeviceManager,
        device_manager_socket: socket.socket,
        device_manager_lock: synchronize.Lock,
        txid: str = None,
    ):
        if device_manager_socket and txid:
            connection, self.txid = device_manager_socket, txid
        else:
            connection, self.txid = device_manager.get_connection()
        super().__init__(arguments, manager, connection, device_manager_lock)

    def _validate_file(self) -> AddConfig:
        """
        Validate file parameters
        """
        config = AddConfig()
        config.adding_file = False
        if self._validator.has_file():
            config.adding_file = True

            if not self._validator.file_exists():
                self._add_error(Errors.NONEXISTENT_FILE)
            elif db.file_exists(self._validator.get_file()):
                self._add_error(
                    Errors.FILE_ALREADY_BACKED_UP_AT(self._validator.get_file())
                )

        return config

    def _validate_folder(self, config: AddConfig) -> AddConfig:
        """
        Validate folder parameters
        """
        config.adding_folder = False
        if self._validator.has_folder():
            config.adding_folder = True

            if not self._validator.folder_exists():
                self._add_error(Errors.NONEXISTENT_FOLDER)
            elif db.get_folders(self._validator.get_folder()):
                self._add_error(
                    Errors.FOLDER_ALREADY_ADDED_AT(self._validator.get_folder())
                )

        return config

    def _validate_device(self, config: AddConfig) -> AddConfig:
        """
        Validate device to add, or device to add file _to_ - MUST BE CALLED LAST
        """
        config.adding_device = False
        # Default to success case, since may not be applicable
        config.to_specific_device = True

        if self._validator.has_device():
            # Add device if not adding either of the other things
            if not config.adding_file and not config.adding_folder:
                if self._validator.device_exists():
                    config.adding_device = True
                    # Adding device makes this check irrelevant
                    config.to_specific_device = False

            # Regardless, device path must exist
            if not self._validator.device_exists():
                # Should set this here since device may not exist for files/folders
                config.to_specific_device = False
                self._add_error(
                    Errors.DEVICE_PATH_NOT_MOUNTED(self._validator.get_device())
                )
            elif not self._validator.device_writeable():
                config.to_specific_device = False
                self._add_error(
                    Errors.DEVICE_NOT_WRITEABLE_AT(self._validator.get_device())
                )

        # No device specified
        else:
            config.to_specific_device = False

        return config

    def _validate(self) -> AddConfig:
        """
        Validates the arguments provided
        """
        config = self._validate_file()
        config = self._validate_folder(config)
        return self._validate_device(config)

    def _create_actions(self, config: AddConfig) -> None:
        """
        Figures out what needs to happen
        """
        if config.adding_file:
            file_obj = self._make_file_object(self._validator.get_file(), config)
            if file_obj:
                self._actions.append(AddFileAction(file_obj))

        if config.adding_folder:
            pass

        if config.adding_device:
            self._add_device(self._validator.get_device())

    def _make_file_object(self, file_path: str, config: AddConfig) -> Optional[File]:
        """
        Creates a file object based on a path
        """
        if db.file_exists(file_path):
            self._add_error(Errors.FILE_ALREADY_BACKED_UP_AT(file_path))
            return None

        try:
            security_details = files.get_file_security(file_path)
        except PermissionError:
            self._add_error(Errors.CANNOT_READ_FILE_AT(file_path))
            return None

        file_size = files.get_file_size(file_path)
        self._add_message(
            Info.FILE_SIZE_OUTPUT_AT(file_path, readable_bytes(file_size))
        )

        selected_device_path = self._get_device_path(
            file_size,
            self._validator.get_device() if config.to_specific_device else None,
        )
        if not selected_device_path:
            return None

        file_obj = File()
        file_obj.set_properties(files.create_backup_name(file_path), file_path, "")
        file_obj.set_security(**security_details)

        devices = db.get_devices()
        # Should always have a result, if we get to this point
        # It will be in the database since the manager reads from it too
        selected_device = [
            device for device in devices if device.device_path == selected_device_path
        ][0]
        file_obj.device = selected_device
        file_obj.device_name = selected_device.device_name

        return file_obj

    def _get_device_path(
        self, needed_size: int, specific_path: Optional[str]
    ) -> Optional[str]:
        """
        Get the device path for the file/folders
        """
        if specific_path:
            selected_device_path = self._check_device(specific_path, needed_size)
            if not selected_device_path:
                return None

        else:
            self._add_message(str(Info.AUTO_SELECT_DEVICE))
            device_manager.send_message(
                [DeviceArguments.COMMAND_GET_DEVICE, needed_size],
                self._device_manager_socket,
                self._device_manager_lock,
            )
            result = self._device_manager_socket.recv(
                Configurations.MAX_MESSAGE_SIZE
            ).decode()
            if str(DeviceArguments.RESPONSE_SUBSTITUTE) not in result:
                self._add_error(
                    Errors.INVALID_COMMAND(
                        device_manager.format_message(
                            DeviceArguments.COMMAND_GET_DEVICE, [str(needed_size)]
                        )
                    )
                )
                # pylint: disable=expression-not-assigned
                [
                    self._add_error(error)
                    for error in self._device_manager.errors(self.txid)
                ]
                return None

            selected_device_path = result.strip().replace(
                DeviceArguments.RESPONSE_SUBSTITUTE + DeviceArguments.COMMAND_DELIMITER,
                "",
            )

        return selected_device_path

    def _check_device(
        self, device_path: str, file_size: int, lock_acquired: bool = False
    ) -> Optional[str]:
        """
        Checks if a given device has space for a file
        Returns device path if one is accepted, None otherwise
        """
        if not lock_acquired:
            self._device_manager_lock.acquire()

        self._add_message(str(Info.CHECKING_DEVICE))
        device_manager.send_message(
            [DeviceArguments.COMMAND_CHECK_DEVICE, device_path, str(file_size)],
            self._device_manager_socket,
            self._device_manager_lock,
            False,
        )

        result = self._device_manager_socket.recv(
            Configurations.MAX_MESSAGE_SIZE
        ).decode()
        response = None
        # pylint: disable=bad-continuation
        if result in [
            str(DeviceArguments.RESPONSE_INVALID),
            str(DeviceArguments.RESPONSE_UNRESOLVABLE),
        ]:
            self._add_error(
                Errors.INVALID_COMMAND(
                    device_manager.format_message(
                        DeviceArguments.COMMAND_CHECK_DEVICE,
                        [device_path, str(file_size)],
                    )
                )
            )
            # pylint: disable=expression-not-assigned
            [self._add_error(error) for error in self._device_manager.errors(self.txid)]

        elif str(DeviceArguments.RESPONSE_SUBSTITUTE) in result:
            new_device_path = result.strip().replace(
                str(DeviceArguments.RESPONSE_SUBSTITUTE)
                + DeviceArguments.COMMAND_DELIMITER,
                "",
            )
            self._add_message(Info.DEVICE_SUBSTITUTED(device_path, new_device_path))
            # Allow confirm to default to "yes"
            confirm = not (
                input(
                    "Allow device substitution to {0}? (Y/n) ".format(new_device_path)
                ).lower()
                == "n"
            )
            if not confirm:
                response = None
                self._add_message(str(Info.SUBSTITUTION_REJECTED))
            else:
                response = self._check_device(new_device_path, file_size, True)
        elif result == str(DeviceArguments.RESPONSE_OK):
            response = device_path

        if not lock_acquired:
            self._device_manager_lock.release()

        return response

    def _add_device(self, mount_point: str):
        """
        Add a device to the database
        """
        device_name = input(InputPrompts.DEVICE_NAME)
        identifier = device_util.get_device_serial(mount_point)
        identifier_type = DEVICE_SERIAL
        if not identifier:
            identifier = device_util.get_device_uuid(mount_point)
            identifier_type = SYSTEM_UUID

        if not identifier:
            identifier = input(InputPrompts.DEVICE_IDENTIFIER)
            identifier_type = USER_SPECIFIED

        save_message = (
            PrettyStatusPrinter(Info.SAVING_DEVICE)
            .with_custom_result(2, False)
            .with_message_postfix_for_result(2, Errors.UNRECOGNIZED_DEVICE_IDENTIFIER)
            .with_custom_result(3, False)
            .with_message_postfix_for_result(3, Errors.DEVICE_NAME_TAKEN)
            .with_custom_result(4, False)
            .with_message_postfix_for_result(4, Errors.DEVICE_MOUNT_POINT_USED)
            .with_custom_result(5, False)
            .with_message_postfix_for_result(5, Errors.DEVICE_SERIAL_USED)
            .with_custom_result(6, False)
            .with_message_postfix_for_result(6, Errors.DEVICE_UNKNOWN_ERROR)
            .with_custom_result(7, False)
            .with_message_postfix_for_result(7, Errors.DEVICE_SUPER_UNKNOWN_ERROR)
            .with_custom_result(DeviceArguments.RESPONSE_INVALID, False)
            # TODO: what is the command here?
            .with_message_postfix_for_result(
                DeviceArguments.RESPONSE_INVALID, Errors.INVALID_COMMAND()
            )
        )

        device_manager.send_message(
            [
                DeviceArguments.COMMAND_ADD_DEVICE,
                device_name,
                mount_point,
                identifier_type,
                identifier,
            ],
            self._device_manager_socket,
            self._device_manager_lock,
        )
        result = self._device_manager_socket.recv(
            Configurations.MAX_MESSAGE_SIZE
        ).decode()

        if result == DatabaseError.SUCCESS:
            self._add_message(save_message.get_styled_message(True))
        else:
            self._add_error(save_message.get_styled_message(result))
