"""
Action to add a file
"""
import os
from os import path as os_path
import shutil

from logical_backup import db
from logical_backup import utility
from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.objects import File
from logical_backup.strings import Errors, Info


class AddFileAction(BaseAction):
    """
    Action to add a new file
    """

    def __init__(self, file_obj: File):
        """
        .
        """
        super().__init__(self)
        self.file_obj = file_obj

    def run(self) -> None:
        """
        Run the action
        """
        file_path = self.file_obj.file_path
        checksum = utility.checksum_file(file_path)
        if not checksum:
            self._fail(Errors.FAILED_GET_CHECKSUM_FOR(file_path))
            return

        self.file_obj.checksum = checksum

        backup_path = os_path.join(
            self.file_obj.device.device_path, self.file_obj.file_name
        )
        shutil.copyfile(file_path, backup_path)

        self._add_message(Info.COPYING_FILE(file_path))
        checksum2 = utility.checksum_file(backup_path)

        if checksum != checksum2:
            self._fail(Errors.CHECKSUM_MISMATCH_AFTER_COPY_FOR(file_path))
            os.remove(backup_path)
            return

        self._add_message(str(Info.SAVING_FILE_TO_DB))

        succeeded = db.add_file(self.file_obj)
        if succeeded == db.DatabaseError.SUCCESS:
            self._add_message(Info.FILE_SAVED(file_path))
            self._succeed()
        else:
            self._fail(Errors.FAILED_ADD_FILE_DB(file_path))
            os.remove(backup_path)
