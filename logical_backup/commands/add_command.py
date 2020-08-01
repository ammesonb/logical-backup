"""
The "add" class of commands
"""
from logical_backup.commands.base_command import BaseCommand
from logical_backup.commands.actions import AddFileAction
from logical_backup import db
from logical_backup.utilities import files
from logical_backup.pretty_print import readable_bytes
from logical_backup.objects import File
from logical_backup.utilities.device_manager import send_message, format_message
from logical_backup.strings import Errors, Info, DeviceArguments, Configurations


class AddCommand(BaseCommand):
    """
    Command for adding files, folders, and devices
    """

    __adding_file = None
    __adding_folder = None
    __adding_device = None
    __to_specific_device = None

    def __validate_file(self) -> None:
        """
        Validate file parameters
        """
        self.__adding_file = False
        if self._validator.has_file():
            if not self._validator.file_exists():
                self._add_error(Errors.NONEXISTENT_FILE)
            else:
                self.__adding_file = True
                if db.file_exists(self._validator.get_file()):
                    self._add_error(
                        Errors.FILE_ALREADY_BACKED_UP_AT(self._validator.get_file())
                    )

    def __validate_folder(self) -> None:
        """
        Validate folder parameters
        """
        self.__adding_folder = False
        if self._validator.has_folder():
            if not self._validator.folder_exists():
                self._add_error(Errors.NONEXISTENT_FOLDER)
            else:
                self.__adding_folder = True
                if db.get_folders(self._validator.get_folder()):
                    self._add_error(
                        Errors.FOLDER_ALREADY_ADDED_AT(self._validator.get_folder())
                    )

    def __validate_device(self) -> None:
        """
        Validate device to add, or device to add file _to_ - MUST BE CALLED LAST
        """
        self.__adding_device = False
        # Default to success case, since may not be applicable
        self.__to_specific_device = True

        if self._validator.has_device():
            # Add device if not adding either of the other things
            if not self.__adding_file and not self.__adding_folder:
                if self._validator.device_exists():
                    self.__adding_device = True
                    # Adding device makes this check irrelevant
                    self.__to_specific_device = False

            # Regardless, device path must exist
            if not self._validator.device_exists():
                # Should set this here since device may not exist for files/folders
                self.__to_specific_device = False
                self._add_error(Errors.DEVICE_PATH_NOT_MOUNTED)
            elif not self._validator.device_writeable():
                self.__to_specific_device = False
                self._add_error(
                    Errors.DEVICE_NOT_WRITEABLE_AT(self._validator.get_device())
                )

        # No device specified
        else:
            self.__to_specific_device = False

    def _validate(self) -> None:
        """
        Validates the arguments provided
        """
        self.__validate_file()
        self.__validate_folder()
        self.__validate_device()

    def _create_actions(self):
        """
        Figures out what needs to happen
        """
        if self.__adding_file:
            file_obj = self.__make_file_object(self._validator.get_file())
            return None if not file_obj else AddFileAction(file_obj)

        if self.__adding_folder:
            pass

        if self.__adding_device:
            pass

        return None

    def __make_file_object(self, file_path: str) -> File:
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

        file_obj = File()
        file_obj.set_properties(files.create_backup_name(file_path), file_path, "")
        file_obj.set_security(**security_details)

        file_size = files.get_file_size(file_path)
        self._add_message(
            Info.FILE_SIZE_OUTPUT_AT(file_path, readable_bytes(file_size))
        )

        selected_device_path = None
        if self.__to_specific_device:
            device_path = self._validator.get_device()
            file_size = files.get_file_size(file_path)

            selected_device_path = self.__check_device(device_path, file_size)
            if not selected_device_path:
                return None

        else:
            file_size = files.get_file_size(file_path)
            self._add_message(Info.AUTO_SELECT_DEVICE)
            send_message(
                [DeviceArguments.COMMAND_GET_DEVICE, file_size],
                self.device_manager_socket,
                self.device_manager_lock,
            )
            result = self.device_manager_socket.recv(Configurations.MAX_MESSAGE_SIZE)
            if result != str(DeviceArguments.RESPONSE_SUBSTITUTE):
                self._add_error(
                    Errors.INVALID_COMMAND(
                        format_message(DeviceArguments.COMMAND_GET_DEVICE, [file_size])
                    )
                )
                return None

            selected_device_path = result.strip().replace(
                DeviceArguments.RESPONSE_SUBSTITUTE + DeviceArguments.COMMAND_DELIMITER,
                "",
            )

        devices = db.get_devices()
        # Should always have a result, if we get to this point
        # It will be in the database since the manager reads from it too
        selected_device = [
            device for device in devices if device.device_path == selected_device_path
        ][0]
        file_obj.device = selected_device
        file_obj.device_name = selected_device.device_name

        return file_obj

    def __check_device(self, device_path: str, file_size: int) -> str:
        """
        Checks if a given device has space for a file
        Returns device path if one is accepted, None otherwise
        """
        self._add_message(Info.CHECKING_DEVICE)
        send_message(
            [DeviceArguments.COMMAND_CHECK_DEVICE, device_path, file_size],
            self.device_manager_socket,
            self.device_manager_lock,
        )
        result = self.device_manager_socket.recv(Configurations.MAX_MESSAGE_SIZE)
        # pylint: disable=bad-continuation
        if result in [
            DeviceArguments.RESPONSE_INVALID,
            DeviceArguments.RESPONSE_UNRESOLVABLE,
        ]:
            self._add_error(
                Errors.INVALID_COMMAND(
                    format_message(
                        DeviceArguments.COMMAND_CHECK_DEVICE, [device_path, file_size]
                    )
                )
            )
            return None

        if str(DeviceArguments.RESPONSE_SUBSTITUTE) in result:
            new_device_path = result.strip().replace(
                str(DeviceArguments.RESPONSE_SUBSTITUTE)
                + DeviceArguments.COMMAND_DELIMITER,
                "",
            )
            confirm = (
                input(
                    "Allow device substitution to {0}? (Y/n) ".format(new_device_path)
                )
                == "n"
            )
            return (
                None if not confirm else self.__check_device(new_device_path, file_size)
            )

        return device_path if result == str(DeviceArguments.RESPONSE_OK) else None
