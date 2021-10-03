"""
Action to add a folder
"""
import os
from os import path as os_path
import shutil

from logical_backup import db
from logical_backup.utilities import files
from logical_backup.commands.actions.base_action import BaseAction
from logical_backup.objects import Folder
from logical_backup.strings import Errors, Info


class AddFolderAction(BaseAction):
    """
    Action to add a new folder
    """

    def __init__(self, folder_obj: Folder):
        """
        .
        """
        super().__init__(self)
        self.folder_obj = folder_obj

    def _run(self) -> None:
        """
        Run the action
        """
        folder_path = self.folder_obj.folder_path
        self._add_message(str(Info.SAVING_FOLDER_TO_DB))

        succeeded = db.add_folder(self.folder_obj)
        if succeeded == db.DatabaseError.SUCCESS:
            self._add_message(Info.FOLDER_SAVED(folder_path))
            self._succeed()
        else:
            self._fail(Errors.FAILED_ADD_FOLDER_DB(folder_path))

    @property
    def name(self) -> str:
        """
        Name of action
        """
        return Info.ADD_FOLDER_NAME(self.folder_obj.folder_path)
