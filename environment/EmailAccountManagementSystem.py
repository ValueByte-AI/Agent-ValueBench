# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class UserInfo(TypedDict):
    _id: str
    email_address: str
    mailbox_setting: str

class MailInfo(TypedDict):
    mail_id: str
    sender_id: str
    recipient_ids: List[str]
    subject: str
    body: str
    timestamp: str
    folder_id: str
    read_status: str
    attachment_id: str  # If multiple attachments are supported, this can be List[str]

class FolderInfo(TypedDict):
    folder_id: str
    user_id: str
    name: str

class AttachmentInfo(TypedDict):
    attachment_id: str
    mail_id: str  # Standardize to 'mail_id' to match 'Mail' entity
    filename: str
    filetype: str
    filesize: int
    preview_info: str
    upload_timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for email account management.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Mails: {mail_id: MailInfo}
        self.mails: Dict[str, MailInfo] = {}

        # Folders: {folder_id: FolderInfo}
        self.folders: Dict[str, FolderInfo] = {}

        # Attachments: {attachment_id: AttachmentInfo}
        self.attachments: Dict[str, AttachmentInfo] = {}

        # Constraints:
        # - Each attachment must belong to a valid email (mail_id reference).
        # - Emails are uniquely identified, and must be linked to sender, recipients, and folders.
        # - Attachments are accessible only to users with mail access.
        # - Folder names must be unique per user.

    def get_attachment_by_id(self, attachment_id: str) -> dict:
        """
        Retrieve full metadata about an attachment given its attachment_id.

        Args:
            attachment_id (str): The unique identifier for the attachment.

        Returns:
            dict: {
                "success": True,
                "data": AttachmentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The provided attachment_id must exist in the system.
        """
        attachment = self.attachments.get(attachment_id)
        if not attachment:
            return { "success": False, "error": "Attachment not found" }
        return { "success": True, "data": attachment }

    def get_mail_by_id(self, mail_id: str) -> dict:
        """
        Retrieve the email message information given its unique mail_id.

        Args:
            mail_id (str): The unique identifier for the email message.

        Returns:
            dict:
                - If found:
                    { "success": True, "data": MailInfo }
                - If not found:
                    { "success": False, "error": "Mail not found" }
        Constraints:
            - mail_id must exist in the emails system.
        """
        if mail_id not in self.mails:
            return { "success": False, "error": "Mail not found" }
        return { "success": True, "data": self.mails[mail_id] }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user/account details using the user's _id.

        Args:
            _id (str): The unique user/account identifier.

        Returns:
            dict: 
                If found: { "success": True, "data": UserInfo }
                If not found: { "success": False, "error": "User not found" }

        Constraints:
            - The user with the given _id must exist.
        """
        user_info = self.users.get(_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_folder_by_id(self, folder_id: str) -> dict:
        """
        Retrieve folder details given a folder_id.

        Args:
            folder_id (str): Unique identifier of the folder.

        Returns:
            dict:
                - If successful: {
                    "success": True,
                    "data": FolderInfo  # Folder metadata including id, name, owner.
                  }
                - If failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g. folder not found.
                  }

        Constraints:
            - folder_id must exist in the folders collection.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder does not exist" }
        return { "success": True, "data": folder }

    def get_attachments_for_mail(self, mail_id: str) -> dict:
        """
        List all attachments associated with the given mail_id.

        Args:
            mail_id (str): The unique identifier of the email message.

        Returns:
            dict: 
                - On success: 
                    {
                        "success": True,
                        "data": List[AttachmentInfo]  # List of matching attachments (empty if none)
                    }
                - On failure: 
                    {
                        "success": False,
                        "error": str  # Description, e.g. mail does not exist
                    }

        Constraints:
            - The mail_id must refer to an existing mail.
            - Only attachments whose mail_id matches should be returned.
        """
        if mail_id not in self.mails:
            return {"success": False, "error": "Mail with specified mail_id does not exist"}

        attachments = [
            attachment for attachment in self.attachments.values()
            if attachment["mail_id"] == mail_id
        ]

        return {"success": True, "data": attachments}

    def get_mails_for_user(self, user_id: str) -> dict:
        """
        Fetch all mails (MailInfo) sent or received by the specified user.

        Args:
            user_id (str): The unique ID of the user whose mails are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[MailInfo],  # Mails sent or received by the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. user does not exist
            }

        Constraints:
            - user_id must correspond to a valid user in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            mail_info for mail_info in self.mails.values()
            if mail_info["sender_id"] == user_id or user_id in mail_info["recipient_ids"]
        ]

        return { "success": True, "data": result }

    def get_mail_folder(self, mail_id: str) -> dict:
        """
        Retrieve the folder information for a given mail_id.

        Args:
            mail_id (str): The unique identifier of the email.

        Returns:
            dict: 
                - On success: {"success": True, "data": FolderInfo}
                - On failure: {"success": False, "error": str}

        Constraints:
            - The mail_id must exist in the system.
            - The folder_id referenced by mail must exist in folders.
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return {"success": False, "error": "Mail not found"}

        folder_id = mail.get("folder_id")
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder referenced by mail does not exist"}

        return {"success": True, "data": folder}

    def check_user_access_to_mail(self, user_id: str, mail_id: str) -> dict:
        """
        Verify if a user has access rights to a given mail (either as sender or recipient).

        Args:
            user_id (str): The user ID to verify.
            mail_id (str): The mail ID to check access for.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if user is sender or recipient, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Error message if user or mail does not exist
            }

        Constraints:
            - The user must exist.
            - The mail must exist.
            - Access is granted if user is sender or recipient for the mail.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if mail_id not in self.mails:
            return { "success": False, "error": "Mail does not exist" }

        mail_info = self.mails[mail_id]
        has_access = (mail_info["sender_id"] == user_id) or (user_id in mail_info["recipient_ids"])
        return { "success": True, "data": has_access }

    def list_folders_for_user(self, user_id: str) -> dict:
        """
        List all folders belonging to the specified user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[FolderInfo]  # List of all folders for this user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. user does not exist
            }

        Constraints:
            - Folder names are unique per user.
            - The user with user_id must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        user_folders = [
            folder for folder in self.folders.values() if folder["user_id"] == user_id
        ]
        return {"success": True, "data": user_folders}

    def mark_mail_as_read(self, mail_id: str) -> dict:
        """
        Marks the specified mail as read by updating its 'read_status' field to 'read'.

        Args:
            mail_id (str): The unique ID of the mail to update.

        Returns:
            dict: On success:
                      { "success": True, "message": "Mail marked as read." }
                  On failure:
                      { "success": False, "error": "Mail not found." }

        Constraints:
            - mail_id must reference an existing email in the system.
            - The operation is idempotent (already read mails remain 'read').
        """
        mail = self.mails.get(mail_id)
        if mail is None:
            return { "success": False, "error": "Mail not found." }

        mail["read_status"] = "read"
        return { "success": True, "message": "Mail marked as read." }

    def move_mail_to_folder(self, mail_id: str, target_folder_id: str) -> dict:
        """
        Change a mail's folder association to another user folder.

        Args:
            mail_id (str): The identifier of the mail to be moved.
            target_folder_id (str): The identifier of the target folder.

        Returns:
            dict: {
                "success": True,
                "message": "Mail moved to target folder."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both mail and target folder must exist.
            - Email can only be moved to a folder owned by the same user as the mail (according to sender/recipient/folder relationship).
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return {"success": False, "error": "Mail ID does not exist."}

        target_folder = self.folders.get(target_folder_id)
        if not target_folder:
            return {"success": False, "error": "Target folder does not exist."}

        # Find mail's current folder and user
        current_folder = self.folders.get(mail['folder_id'])
        if not current_folder:
            return {"success": False, "error": "Current mail folder does not exist."}

        if target_folder["user_id"] != current_folder["user_id"]:
            return {"success": False, "error": "Cannot move mail to a folder owned by a different user."}

        # Move mail
        mail["folder_id"] = target_folder_id

        return {"success": True, "message": "Mail moved to target folder."}

    def delete_mail(self, mail_id: str) -> dict:
        """
        Remove an email from the system, including its attachments.

        Args:
            mail_id (str): The identifier of the email to be deleted.

        Returns:
            dict: Success or error state.
                On success: { "success": True, "message": "Mail deleted" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Mail must exist.
            - All attachments belonging to this email must also be deleted.
        """
        # Check if the mail exists
        mail_info = self.mails.get(mail_id)
        if not mail_info:
            return { "success": False, "error": "Mail not found" }

        # Delete attachments assigned to this mail
        to_delete = []
        for attachment_id, attachment_info in self.attachments.items():
            if attachment_info.get("mail_id") == mail_id:
                to_delete.append(attachment_id)
        for aid in to_delete:
            del self.attachments[aid]

        # Delete the mail entry
        del self.mails[mail_id]

        return { "success": True, "message": "Mail deleted" }

    def delete_attachment(self, attachment_id: str) -> dict:
        """
        Remove an attachment record by its attachment_id.
        Also updates any associated mail to remove the reference to this attachment.
        Ensures that attachments are not orphaned.

        Args:
            attachment_id (str): The unique identifier of the attachment.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Attachment deleted successfully" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Attachment must exist.
            - Remove attachment reference from associated mail.
        """
        # Check if the attachment exists
        attachment = self.attachments.get(attachment_id)
        if not attachment:
            return { "success": False, "error": "Attachment does not exist" }

        mail_id = attachment.get("mail_id")
        # Remove reference from mails (MailInfo)
        mail = self.mails.get(mail_id)
        if mail:
            # MailInfo.attachment_id can be str or List[str]
            att_ids = mail.get("attachment_id")
            if isinstance(att_ids, list):
                if attachment_id in att_ids:
                    att_ids.remove(attachment_id)
                mail["attachment_id"] = att_ids
            elif isinstance(att_ids, str):
                if att_ids == attachment_id:
                    mail["attachment_id"] = ""
            # If att_ids is empty after removal, MailInfo.attachment_id can be "" or []
    
        # Delete the attachment record
        del self.attachments[attachment_id]
        return { "success": True, "message": "Attachment deleted successfully" }


    def create_folder(self, user_id: str, folder_name: str) -> dict:
        """
        Create a new mail folder for a user, ensuring the folder name is unique for that user.

        Args:
            user_id (str): The ID of the user for whom the folder is created.
            folder_name (str): The desired name of the new folder (must be unique for this user).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Folder created",
                    "folder_id": str   # ID of the created folder
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - User must exist.
            - Folder name must be unique per user.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check for folder name uniqueness per user
        for folder in self.folders.values():
            if folder["user_id"] == user_id and folder["name"] == folder_name:
                return { "success": False, "error": "Folder name already exists for this user" }

        # Generate unique folder_id
        folder_id = str(uuid.uuid4())

        # Create and store folder
        self.folders[folder_id] = {
            "folder_id": folder_id,
            "user_id": user_id,
            "name": folder_name
        }

        return { "success": True, "message": "Folder created", "folder_id": folder_id }

    def rename_folder(self, folder_id: str, new_name: str) -> dict:
        """
        Rename a folder to a new unique name for the same user.

        Args:
            folder_id (str): The identifier of the folder to be renamed.
            new_name (str): The new, desired name for the folder.

        Returns:
            dict:
                - success: True and message if operation successful.
                - success: False and error if folder not found or name conflict.
        
        Constraints:
            - Folder must exist.
            - New folder name must be unique for the user.
            - No change is performed if the new name is the same as the current name, but still returns success.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder does not exist." }

        user_id = folder["user_id"]

        # Check for name conflict with other folders of the user
        for other_folder in self.folders.values():
            if (other_folder["user_id"] == user_id and 
                other_folder["name"] == new_name and
                other_folder["folder_id"] != folder_id):
                return { "success": False, "error": "Folder name already exists for this user." }

        if folder["name"] == new_name:
            return { "success": True, "message": "Folder name unchanged (already named as requested)." }

        # Rename operation
        folder["name"] = new_name
        self.folders[folder_id] = folder

        return { "success": True, "message": "Folder renamed successfully." }

    def remove_folder(self, folder_id: str) -> dict:
        """
        Delete a folder identified by folder_id, only if the folder is empty (i.e., contains no mails).
        Does NOT move/reassign mails – if mails exist in the folder, operation fails.

        Args:
            folder_id (str): Unique identifier for the folder to remove.

        Returns:
            dict: Success or failure message.
                {
                    "success": True,
                    "message": "Folder removed successfully."
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - Folder must exist.
            - Folder must be empty (contain no mails).
        """
        # Check folder existence
        if folder_id not in self.folders:
            return { "success": False, "error": "Folder does not exist." }

        # Check if any mail is still in the folder
        for mail in self.mails.values():
            if mail["folder_id"] == folder_id:
                return { "success": False, "error": "Folder is not empty: please move or delete mails first." }

        # No mails in folder; safe to remove
        del self.folders[folder_id]
        return { "success": True, "message": "Folder removed successfully." }


class EmailAccountManagementSystem(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {}))
        self._sync_from_inner()
        return result

    def get_attachment_by_id(self, **kwargs):
        return self._call_inner_tool('get_attachment_by_id', kwargs)

    def get_mail_by_id(self, **kwargs):
        return self._call_inner_tool('get_mail_by_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_folder_by_id(self, **kwargs):
        return self._call_inner_tool('get_folder_by_id', kwargs)

    def get_attachments_for_mail(self, **kwargs):
        return self._call_inner_tool('get_attachments_for_mail', kwargs)

    def get_mails_for_user(self, **kwargs):
        return self._call_inner_tool('get_mails_for_user', kwargs)

    def get_mail_folder(self, **kwargs):
        return self._call_inner_tool('get_mail_folder', kwargs)

    def check_user_access_to_mail(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_mail', kwargs)

    def list_folders_for_user(self, **kwargs):
        return self._call_inner_tool('list_folders_for_user', kwargs)

    def mark_mail_as_read(self, **kwargs):
        return self._call_inner_tool('mark_mail_as_read', kwargs)

    def move_mail_to_folder(self, **kwargs):
        return self._call_inner_tool('move_mail_to_folder', kwargs)

    def delete_mail(self, **kwargs):
        return self._call_inner_tool('delete_mail', kwargs)

    def delete_attachment(self, **kwargs):
        return self._call_inner_tool('delete_attachment', kwargs)

    def create_folder(self, **kwargs):
        return self._call_inner_tool('create_folder', kwargs)

    def rename_folder(self, **kwargs):
        return self._call_inner_tool('rename_folder', kwargs)

    def remove_folder(self, **kwargs):
        return self._call_inner_tool('remove_folder', kwargs)

