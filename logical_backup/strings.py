"""
Contains printed messages, errors, etc
"""
from os import path as os_path
import tempfile

from logical_backup.utilities import PrintableEnum

# pylint: disable=unnecessary-lambda


class Configurations(PrintableEnum):
    """
    Program configurations
    """

    MAX_CONNECTIONS = 20  # pragma: no mutate
    CONNECTION_TIMEOUT = 0.1  # pragma: no mutate
    MESSAGE_TIMEOUT = 0.1  # pragma: no mutate
    # close a connection this many seconds of inactivigy
    CLOSE_CONNECTION_AFTER = 5  # pragma: no mutate
    MAX_MESSAGE_SIZE = 1024  # pragma: no mutate

    MESSAGE_DELIMITER = ","  # pragma: no mutate


class Errors(PrintableEnum):
    """
    Printed error messages
    """

    COMMAND_VALIDATE_NOT_IMPLEMENTED = (
        "Validate must be overridden"  # pragma: no mutate
    )
    COMMAND_CREATE_ACTIONS_NOT_IMPLEMENTED = (
        "Create actions must be overridden"  # pragma: no mutate
    )

    ACTION_RUN_NOT_IMPLEMENTED = (
        "Action must override run function"  # pragma: no mutate
    )
    ACTION_NAME_NOT_IMPLEMENTED = (
        "Action must override name function"  # pragma: no mutate
    )

    NONEXISTENT_FILE = "File path does not exist!"  # pragma: no mutate
    FILE_ALREADY_BACKED_UP = "File is already backed up!"  # pragma: no mutate
    FILE_ALREADY_BACKED_UP_AT = lambda path: (
        "File is already backed up at {0}!".format(path)  # pragma: no mutate
    )
    FILE_NOT_BACKED_UP = "File path not backed up!"  # pragma: no mutate
    NEW_FILE_ALREADY_BACKED_UP = (
        "File already backed up at new location!"  # pragma: no mutate
    )
    CANNOT_FIND_BACKUP = "Cannot find back up of file!"  # pragma: no mutate
    FILE_DEVICE_INVALID = "Unable to find device for file"  # pragma: no mutate
    CANNOT_READ_FILE_AT = lambda path: (
        "Unable to read source file: {0}".format(path)  # pragma: no mutate
    )
    FAILED_ADD_FILE_DB = lambda path: (
        "Failed to record file in database: {0}".format(path)  # pragma: no mutate
    )

    NONEXISTENT_FOLDER = "Folder path does not exist!"  # pragma: no mutate
    FOLDER_ALREADY_ADDED = "Folder already added!"  # pragma: no mutate
    FOLDER_ALREADY_ADDED_AT = lambda path: (
        "Folder {0} already added!".format(path)  # pragma: no mutate
    )
    FOLDER_BACKED_UP_AT = lambda path: (  # pragma: no mutate
        "Folder already backed up at path '{0}'!".format(path)  # pragma: no mutate
    )
    FOLDER_NOT_BACKED_UP = "Folder not backed up!"  # pragma: no mutate
    FOLDER_NOT_BACKED_UP_AT = lambda path: (  # pragma: no mutate
        "Specified folder not backed up: '{0}'!".format(path)  # pragma: no mutate
    )
    FOLDER_NOT_CREATED = lambda path: (
        "Failed to create folder: {0}".format(path)  # pragma: no mutate
    )
    CANNOT_OVERWRITE_EXISTING_FOLDER = (
        "Cannot move folder over existing file!"  # pragma: no mutate
    )
    FAILED_FOLDER_REMOVE = lambda folder: (
        "Failed to remove folder '{0}' "  # pragma: no mutate
        "from database!".format(folder)  # pragma: no mutate
    )
    FAILED_FOLDER_ADD = lambda folder: (
        "Failed to add folder '{0}' "  # pragma: no mutate
        "back to the database!".format(folder)  # pragma: no mutate
    )
    FAILED_FOLDER_SECURITY = lambda folder_path: (
        "Failed to set folder "
        "security options for {0}".format(folder_path)  # pragma: no mutate
    )

    DEVICE_PATH_NOT_MOUNTED = lambda path: (
        "No device is mounted at {0}".format(path)  # pragma: no mutate
    )
    DEVICE_NOT_WRITEABLE_AT = lambda path: (
        "Cannot write to device at {0}".format(path)  # pragma: no mutate
    )
    DEVICE_MUST_BE_ADDED = (
        "A device must be added before "  # pragma: no mutate
        "any other actions can occur!"  # pragma: no mutate
    )
    DEVICE_ALREADY_ADDED_AT = lambda path: ()
    NO_DEVICES_FOUND = "None!"  # pragma: no mutate
    SOME_DEVICES_FOUND = "Found some devices:"  # pragma: no mutate
    UNRECOGNIZED_DEVICE_IDENTIFIER = (
        "Failed. Unrecognized device identifier!"  # pragma: no mutate
    )
    DEVICE_NAME_TAKEN = "Failed. Name already taken!"  # pragma: no mutate
    DEVICE_MOUNT_POINT_USED = (
        "Failed. Device already registered at mount point!"  # pragma: no mutate
    )
    DEVICE_SERIAL_USED = (
        "Failed. Serial already registered for another device!"  # pragma: no mutate
    )
    DEVICE_UNKNOWN_ERROR = "Failed. Unknown error occurred!"  # pragma: no mutate
    DEVICE_SUPER_UNKNOWN_ERROR = (
        "Failed. Super-unknown error occurred!"  # pragma: no mutate
    )

    NO_SAVED_DEVICES = "No devices saved!"  # pragma: no mutate
    SELECTED_DEVICE_FULL = (
        "Exiting since unable to fit all files on selected device"  # pragma: no mutate
    )
    DEVICE_HAS_INSUFFICIENT_SPACE = (
        "Selected device will not fit all files!"  # pragma: no mutate
    )
    NO_DEVICE_WITH_SPACE_AVAILABLE = (
        "No device with space available!"  # pragma: no mutate
    )
    INSUFFICIENT_SPACE_FOR_DIRECTORY = lambda bytes_needed: (  # pragma: no mutate
        "Sum of available devices' space is insufficient, "  # pragma: no mutate
        "need {0} additional space! Exiting".format(bytes_needed)  # pragma: no mutate
    )
    FILE_DEVICE_NOT_MOUNTED = (
        "Device for backed-up file is not mounted!"  # pragma: no mutate
    )

    FAILED_GET_CHECKSUM = "Failed to get checksum"  # pragma: no mutate
    FAILED_GET_CHECKSUM_FOR = lambda path: (
        "Failed to get checksum: " + path  # pragma: no mutate
    )
    CHECKSUM_MISMATCH = "File checksum does not match"  # pragma: no mutate
    CHECKSUM_MISMATCH_AFTER_COPY = "Checksum mismatch after copy!"  # pragma: no mutate
    CHECKSUM_MISMATCH_AFTER_COPY_FOR = lambda path: (
        "Checksum mismatch after copy: " + path  # pragma: no mutate
    )
    NONE_FOUND = "None found!"  # pragma: no mutate

    FAILED_FILE_DEVICE_DB_UPDATE = (
        "Failed to update device for file in database!"  # pragma: no mutate
    )
    RESTORE_PATH_EXISTS = "Path to restore already exists!"  # pragma: no mutate
    FAIL_SET_PERMISSIONS_REMOVED = (
        "Failed to set file permissions/owner, "  # pragma: no mutate
        "but able to remove file"  # pragma: no mutate  # pragma: no mutate
    )
    FAIL_SET_PERMISSIONS_MANUAL = (
        "Failed to set file permissions/owner, "  # pragma: no mutate
        "manual removal required!"  # pragma: no mutate  # pragma: no mutate
    )

    FAILED_REMOVE_FILE_UPDATE = (
        "Failed to remove file, so cannot update!"  # pragma: no mutate
    )
    FAILED_ADD_FILE_UPDATE = "Failed to add file during update!"  # pragma: no mutate

    FAILED_REMOVE_FILE = "Failed to remove file from the database!"  # pragma: no mutate

    NO_NETWORK_RESPONSE = (
        "Failed to get a response for device availability"  # pragma: no mutate
    )

    INVALID_COMMAND = lambda command: (
        "Command is not valid: '{0}'".format(command)  # pragma: no mutate
    )

    FAILED_TO_CREATE_ACTIONS = "Command failed to create actions"  # pragma: no mutate

    THREAD_COUNT_NUMERIC = (
        "Thread count must be present and numeric"  # pragma: no mutate
    )
    INSUFFICIENT_REORDER_POSITIONS = (
        "A source and destination position must be provided"  # pragma: no mutate
    )
    INVALID_SOURCE_POSITION = (
        "Source position must a number or range"  # pragma: no mutate
    )
    INVALID_DESTINATION_POSITION = (
        "Destination must a number or 'top'/'bottom'"  # pragma: no mutate
    )
    UNABLE_TO_ACQUIRE = (
        "Queue in use. Verify queue state and re-run command"  # pragma: no mutate
    )
    INSUFFICIENT_STATUS_OPTIONS = (
        "To identify a message, [c]omplete or [q]ueued "  # pragma: no mutate
        "plus an index must be specified"  # pragma: no mutate
    )

    STOP_MANAGER_BEFORE_CLOSE = (
        "Can only close the server connection "  # pragma: no mutate
        "if the manager is stopped!"  # pragma: no mutate
    )


class InputPrompts(PrintableEnum):
    """
    Input prompt messages
    """

    ALLOW_DEVICE_CHANGE = (
        "Continue with any available device? (y/N, 'n' will exit) "  # pragma: no mutate
    )

    RECURSIVE_REMOVE_DIRECTORY = (  # pragma: no mutate
        "Found one or more backed-up folders "  # pragma: no mutate
        "that no longer exist! "  # pragma: no mutate
        "Remove ALL missing directories recursively? "  # pragma: no mutate
        "Type REMOVE uppdercase to do so "  # pragma: no mutate
    )
    RECURSIVE_REMOVE_FILE = (  # pragma: no mutate
        "Found one or more backed-up files that no longer exist! "  # pragma: no mutate
        "Remove all missing files? Type YES uppercase to do so "  # pragma: no mutate
    )  # pragma: no mutate

    DEVICE_NAME = "Device name: "  # pragma: no mutate
    DEVICE_IDENTIFIER = (
        "Unable to find systemic identifier. "  # pragma: no mutate
        "Please provide a unique identifier for the device: "  # pragma: no mutate
    )

    CLI_STATUS = lambda completed_count, action_count, thread_count: (  # pragma: no mutate
        "[{0}/{1}:{2}]# ".format(  # pragma: no mutate
            completed_count, action_count, thread_count  # pragma: no mutate
        )  # pragma: no mutate
    )


class Info(PrintableEnum):
    """
    Informational messages
    """

    ACTION = "The action to take"  # pragma: no mutate
    CHECKING_DEVICES = "Checking for devices"  # pragma: no mutate
    ALL_DEVICES_FOUND = "All devices found"  # pragma: no mutate
    NO_DEVICES_FOUND = "None found, but command can continue"
    CONTINUING_WITHOUT_DEVICE = "Continuing without all devices"  # pragma: no mutate

    CHECKING_DEVICE = "Checking availability on device"  # pragma: no mutate
    AUTO_SELECT_DEVICE = "Auto-selecting device"  # pragma: no mutate
    DEVICE_SUBSTITUTED = lambda original, replacement: (  # pragma: no mutate
        "Device {0} was substituted for {1}".format(  # pragma: no mutate
            original, replacement  # pragma: no mutate
        )  # pragma: no mutate
    )  # pragma: no mutate
    SUBSTITUTION_REJECTED = "User rejected device substitution"  # pragma: no mutate
    GET_FILE_SIZE = "Getting file size"  # pragma: no mutate
    FILE_SIZE_OUTPUT = lambda size: "Read. File size is " + size  # pragma: no mutate
    FILE_SIZE_OUTPUT_AT = lambda path, size: (
        "Read file {0}. File size is {1}".format(path, size)  # pragma: no mutate
    )

    SAVING_DEVICE = "Saving device"  # pragma: no mutate
    COPYING_FILE = lambda path: "Copying file {0}" + path  # pragma: no mutate
    SAVING_FILE_TO_DB = "Saving file record to DB"  # pragma: no mutate
    FILE_SAVED = lambda path: "File backed up: " + path  # pragma: no mutate

    COPYING_FILE_DEVICE = "Copying file to new device"  # pragma: no mutate

    VALIDATE_FILE_REMOVAL = "Validating file removal"  # pragma: no mutate
    FILE_REMOVED = "File removed"  # pragma: no mutate

    PROGRAM_DESCRIPTION = (
        "Back up and restore files across multiple hard drives\n\n"  # pragma: no mutate
        "Actions:\n"  # pragma: no mutate
        "         add: add a file or folder "  # pragma: no mutate
        "to the backup selection\n"  # pragma: no mutate
        "      remove: remove a file or folder "  # pragma: no mutate
        "from the backup selection\n"  # pragma: no mutate
        "        move: move a file or folder "  # pragma: no mutate
        "in the backup selection, "  # pragma: no mutate
        "OR files/folders between devices\n"  # pragma: no mutate
        "     restore: restore a file/folder/all files "  # pragma: no mutate
        "to their original location\n"  # pragma: no mutate
        "      verify: check a backed-up file/folder/all "  # pragma: no mutate
        "files for integrity "  # pragma: no mutate
        "(this will NOT check the local filesystem copy, "  # pragma: no mutate
        "as that is assumed to be correct)\n"  # pragma: no mutate
        " interactive: run in interactive mode, "  # pragma: no mutate
        "allowing threads for faster throughput\n"  # pragma: no mutate
        "list-devices: list all the registered backup devices\n"  # pragma: no mutate
        "Example uses:\n"  # pragma: no mutate
        "  # Will add a new device\n"  # pragma: no mutate
        "  add --device /mnt/dev1\n"  # pragma: no mutate
        "  # Will add this file to the backup set\n"  # pragma: no mutate
        "  add --file /home/user/foo.txt\n"  # pragma: no mutate
        "  # Will remove the /etc folder recursively from backup\n"  # pragma: no mutate
        "  remove --folder /etc\n"  # pragma: no mutate
        "  # Will check all backed up files for integrity\n"  # pragma: no mutate
        "  verify --all\n"  # pragma: no mutate
        "  # Will restore the documents folder from backup\n"  # pragma: no mutate
        "  restore /home/user/documents\n"  # pragma: no mutate
        "  # Will rehome the file, "  # pragma: no mutate
        "updating the backup archive with the new location\n"  # pragma: no mutate
        "  move --file /backups/large.bak "  # pragma: no mutate
        "--move-path /backups/archive/\n"  # pragma: no mutate
        "  # Will move the backed up folder from "  # pragma: no mutate
        "its current drive to another, "  # pragma: no mutate
        "if one particular drive is too full to "  # pragma: no mutate
        "take a needed operation\n"  # pragma: no mutate
        "  move --file /backups --device dev2\n"  # pragma: no mutate
    )

    CLI_HELP = (
        "This mode allows parallel operations and interactivity.\n"  # pragma: no mutate
        "Reference program help for normal operations, "  # pragma: no mutate
        "such as adding or removing files\n\n"  # pragma: no mutate
        "Additional actions include:\n"  # pragma: no mutate
        "           reorder:\n"
        "    Reprioritize items in the queue. Ranges and comma-separated values are "
        "allowed for the source, e.g. 1-3,5,6-8,10. Destination is a single number or "
        "the designation 'top' or 'bottom'.\n"
        "             clear:\n"
        "    Remove one or more items from the list. If no arguments provided, will "
        "clear all the completed actions. Otherwise, this will remove the specified "
        "pending actions. If an item is mid-processing, it cannot be cleared.\n"
        "            status:\n"
        "    View the status of the processing. If [c]omplete or [queue] are provided "
        "along with an item's index, will report on that item only."
        "          messages:\n"
        "    Similar to status, this will report messages and errors from an action. "
        "[c]omplete or [q]ueue should be specified with an index to indicate the "
        "desired action to display messages for.\n"
        "  set_thread_count: Change parallelism to given number\n"  # pragma: no mutate
        "              help: Display this text\n"  # pragma: no mutate
        "              exit:\n"
        "    Exit the shell - will remove all unprocessed "
        "queue items and allow exiting after the "  # pragma: no mutate
        "current actions finish\n"  # pragma: no mutate
    )

    TARGET_FILE_HELP = "The file to take action on"  # pragma: no mutate
    TARGET_FOLDER_HELP = "The folder to take action on"  # pragma: no mutate
    TARGET_DEVICE_HELP = "Mount path for a device"  # pragma: no mutate
    TARGET_FROM_DEVICE_HELP = (
        "Use to restrict operation to a specific device"  # pragma: no mutate
    )
    TARGET_ALL_HELP = "Perform operation on all files"  # pragma: no mutate
    TARGET_MOVE_PATH_HELP = "Target for move operaetion"  # pragma: no mutate
    ARGUMENT_THREADS_HELP = "Number of threads to run commands in"  # pragma: no mutate

    ADD_FILE_NAME = lambda file_path: (  # pragma: no mutate
        "Adding file: " + os_path.basename(file_path)  # pragma: no mutate
    )

    COMMAND_CREATED_ACTIONS = lambda action_count: int(  # pragma: no mutate
        "Command created {0} actions".format(action_count)  # pragma: no mutate
    )

    EXITING = lambda exit_action: f"Exiting...{exit_action}"  # pragma: no mutate


class Commands(PrintableEnum):
    """
    Possible commands
    """

    ADD = "add"  # pragma: no mutate
    MOVE = "move"  # pragma: no mutate
    REMOVE = "remove"  # pragma: no mutate
    UPDATE = "update"  # pragma: no mutate
    VERIFY = "verify"  # pragma: no mutate
    RESTORE = "restore"  # pragma: no mutate
    LIST_DEVICES = "list-devices"  # pragma: no mutate
    SEARCH = "search"  # pragma: no mutate
    INTERACTIVE = "interactive"  # pragma: no mutate

    # CLI-only commands
    # Reorder queue
    REORDER = "reorder"  # pragma: no mutate
    # Remove completed item/s from the queue
    CLEAR = "clear"  # pragma: no mutate
    # Get messages/errors
    MESSAGES = "messages"  # pragma: no mutate
    # Check current and pending jobs, success/fail stats
    STATUS = "status"
    # Change number of running threads
    SET_THREADS = "set_thread_count"
    # Show commands
    HELP = "help"
    # Exit shell
    EXIT = "exit"


class Targets(PrintableEnum):
    """
    Possible target of a command
    """

    ALL = "--all"  # pragma: no mutate
    FILE = "--file"  # pragma: no mutate
    FOLDER = "--folder"  # pragma: no mutate
    DEVICE = "--device"  # pragma: no mutate
    FROM_DEVICE = "--from-device"  # pragma: no mutate
    MOVE_PATH = "--move-path"  # pragma: no mutate
    THREADS = "--threads"  # pragma: no mutate


class Arguments(PrintableEnum):
    """
    Argument options
    """

    ALL = "all"  # pragma: no mutate
    FILE = "file"  # pragma: no mutate
    FOLDER = "folder"  # pragma: no mutate
    DEVICE = "device"  # pragma: no mutate
    FROM_DEVICE = "from_device"  # pragma: no mutate
    MOVE_PATH = "move_path"  # pragma: no mutate
    THREADS = "threads"  # pragma: no mutate


class DeviceArguments(PrintableEnum):
    """
    Commands and responses in the device manager
    """

    SOCKET_PATH = os_path.join(  # pragma: no mutate
        tempfile.gettempdir(), "logical-backup-device-manager.sock"  # pragma: no mutate
    )

    COMMAND_DELIMITER = ","  # pragma: no mutate
    COMMAND_HELLO = "hello"  # pragma: no mutate
    COMMAND_GET_DEVICE = "get-device"  # pragma: no mutate
    COMMAND_CHECK_DEVICE = "check-device"  # pragma: no mutate
    COMMAND_STOP = "stop"  # pragma: no mutate

    RESPONSE_OK = "ok"  # pragma: no mutate
    RESPONSE_SUBSTITUTE = "substitute"  # pragma: no mutate
    RESPONSE_PARTIAL = "partial"  # pragma: no mutate
    RESPONSE_UNRESOLVABLE = "unresolvable"  # pragma: no mutate
    RESPONSE_INVALID = "invalid"  # pragma: no mutate

    ERROR_INSUFFICIENT_PARAMETERS = lambda command: (
        "Insufficient parameters for command {0}".format(command)  # pragma: no mutate
    )
    ERROR_UNKNOWN_DEVICE = lambda device_path: (
        "Unknown device path provided: {0}".format(device_path)  # pragma: no mutate
    )
    ERROR_SIZE_IS_NOT_NUMBER = lambda size: (
        "Provided size is not an integer: {0}".format(size)  # pragma: no mutate
    )
    ERROR_SIZE_IS_ZERO = "Requested size is zero"  # pragma: no mutate
    ERROR_UNKNOWN_EXCEPTION = lambda error: (
        "An unknown exception occurred: {0}!".format(error)  # pragma: no mutate
    )
    ERROR_UNKNOWN_COMMAND = lambda command: (
        "Unrecognized command: {0}".format(command)
    )  # pragma: no mutate
    ERROR_BAD_HELLO = lambda command: (
        "Invalid hello command: {0}".format(command)  # pragma: no mutate
    )

    KEY_ACCEPT = "accept"  # pragma: no mutate
    KEY_INITIALIZE = "initialize"  # pragma: no mutate

    MESSAGE_CLOSING_CONNECTION = lambda txid: (
        "Closing connection: {0}".format(txid)  # pragma: no mutate
    )
