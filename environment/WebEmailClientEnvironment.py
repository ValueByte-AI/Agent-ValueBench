# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class UserInfo(TypedDict):
    _id: str
    username: str
    email_address: str
    preference: str

class MailMessageInfo(TypedDict):
    message_id: str
    sender: str
    recipients: List[str]
    subject: str
    body: str
    timestamp: str
    read_status: Dict[str, bool]   # user_id → read/unread
    flags: Dict[str, List[str]]    # user_id → [flags]
    folder_id: str
    thread_id: str

class FolderInfo(TypedDict):
    folder_id: str
    user_id: str
    name: str           # e.g., Inbox, Sent, Archive, Trash
    parent_folder_id: str

class MailThreadInfo(TypedDict):
    thread_id: str
    subject: str
    list_of_message_id: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Web-based email client environment state.

        Constraints:
        - Only emails/folders belonging to the user can be accessed or manipulated.
        - Each email is assigned to exactly one folder at a time.
        - The read/unread status, and flags (e.g., starred, important) are user-specific.
        - Folders like Inbox, Sent, and Trash are reserved and cannot be deleted or renamed.
        - Real-time sync: all changes update client UI for the user immediately.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Messages: {message_id: MailMessageInfo}
        self.messages: Dict[str, MailMessageInfo] = {}

        # Folders: {folder_id: FolderInfo}
        self.folders: Dict[str, FolderInfo] = {}

        # Threads: {thread_id: MailThreadInfo}
        self.threads: Dict[str, MailThreadInfo] = {}

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve the account details for the specified user.

        Args:
            user_id (str): The identifier of the user whose details are requested.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - Only existing users can be queried.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def list_folders(self, user_id: str) -> dict:
        """
        List all folders belonging to the specified user, including reserved and user-defined folders.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[FolderInfo],  # List of folders owned by user_id (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # "User does not exist"
            }

        Constraints:
            - Only folders belonging to user_id are listed.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            folder_info
            for folder_info in self.folders.values()
            if folder_info["user_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_folder_by_name(self, user_id: str, folder_name: str) -> dict:
        """
        Retrieve the metadata for a folder with the specified name belonging to the given user.

        Args:
            user_id (str): The user's unique identifier.
            folder_name (str): The display name of the folder (e.g., 'Inbox', 'Sent').

        Returns:
            dict: {
                "success": True,
                "data": FolderInfo  # Metadata for the folder
            }
            OR
            {
                "success": False,
                "error": str  # Reason (e.g., folder not found)
            }

        Constraints:
            - Only folders owned by the user should be searched.
            - Folders are unique per (user_id, folder_name).
        """
        for folder in self.folders.values():
            if folder["user_id"] == user_id and folder["name"] == folder_name:
                return { "success": True, "data": folder }
        return { "success": False, "error": "Folder not found for user" }

    def list_messages_in_folder(self, user_id: str, folder_id: str) -> dict:
        """
        List all messages contained in the specified folder belonging to the user.

        Args:
            user_id (str): The ID of the user making the query.
            folder_id (str): The ID of the folder whose messages to list.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MailMessageInfo]  # List of messages (can be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., folder does not exist, access denied)
                    }
        Constraints:
            - Only show messages in folders belonging to this user.
        """
        folder = self.folders.get(folder_id)
        if folder is None:
            return {"success": False, "error": "Folder does not exist"}
        if folder["user_id"] != user_id:
            return {"success": False, "error": "Access denied: folder does not belong to user"}
        messages = [
            msg for msg in self.messages.values()
            if msg["folder_id"] == folder_id
        ]
        return {"success": True, "data": messages}

    def list_unread_messages_in_folder(self, user_id: str, folder_id: str) -> dict:
        """
        Retrieve all unread messages (MailMessageInfo) for a user in a specified folder.

        Args:
            user_id (str): ID of the user requesting the unread messages.
            folder_id (str): ID of the folder to search.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[MailMessageInfo]  # May be empty if no unread messages.
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason for failure.
                }

        Constraints:
            - Only messages in folders owned by the user are accessible.
            - Unread status is determined by 'read_status' for the given user_id.
            - folder_id must exist and belong to user_id.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check folder existence and ownership
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder does not exist"}
        if folder['user_id'] != user_id:
            return {"success": False, "error": "Folder does not belong to user"}

        # Filter messages in the folder that are unread by user
        unread_messages = []
        for m in self.messages.values():
            if m['folder_id'] == folder_id:
                # Ensure user_id exists in read_status mapping
                if m.get('read_status', {}).get(user_id) is False:
                    unread_messages.append(m)

        return {"success": True, "data": unread_messages}

    def get_message_info(self, user_id: str, message_id: str) -> dict:
        """
        Fetch details (sender, subject, body, status, flags, etc.) for a specified message.
    
        Args:
            user_id (str): ID of the user requesting the message info.
            message_id (str): ID of the message/email to retrieve.
    
        Returns:
            dict: {
                "success": True,
                "data": MailMessageInfo
            }
            OR
            {
                "success": False,
                "error": str  # Reason (e.g., not found, access denied)
            }
        
        Constraints:
            - Only emails belonging to the user can be accessed.
            - Message must exist.
        """
        # Message existence check
        message = self.messages.get(message_id)
        if message is None:
            return { "success": False, "error": "Message not found" }
    
        folder_id = message.get("folder_id")
        folder = self.folders.get(folder_id)
        if folder is None:
            # Folder missing: inconsistent state, treat as not found/accessible
            return { "success": False, "error": "Message folder not found" }
    
        if folder["user_id"] != user_id:
            return { "success": False, "error": "Access denied: email does not belong to user" }
    
        return { "success": True, "data": message }

    def list_threads_in_folder(self, user_id: str, folder_id: str) -> dict:
        """
        List all conversation threads present in a given folder for the specified user.

        Args:
            user_id (str): The user whose threads are to be listed.
            folder_id (str): The folder in which to look for threads.

        Returns:
            dict:
                success: True and 'data': List[MailThreadInfo] if successful (may be empty).
                success: False and 'error': error message if folder not found or unauthorized.

        Constraints:
            - The folder must exist and belong to the user.
            - Only threads with at least one message in the given folder are listed.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder does not exist" }
        if folder["user_id"] != user_id:
            return { "success": False, "error": "Folder does not belong to user" }

        # Find all messages assigned to this folder belonging to this user
        thread_ids = set()
        for msg in self.messages.values():
            if msg["folder_id"] == folder_id:
                # All messages in this folder must belong to the user by design
                thread_ids.add(msg["thread_id"])

        # Collect all MailThreadInfo for these threads
        threads_in_folder = [
            self.threads[tid]
            for tid in thread_ids
            if tid in self.threads
        ]

        return { "success": True, "data": threads_in_folder }

    def get_thread_messages(self, thread_id: str, user_id: str) -> dict:
        """
        List all messages in a given thread that are accessible to the specified user.

        Args:
            thread_id (str): The thread ID to look up.
            user_id (str): The ID of the requesting user.

        Returns:
            dict: {
                "success": True,
                "data": List[MailMessageInfo],  # Only messages accessible to user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., thread does not exist)
            }

        Constraints:
            - Only emails belonging to the user are returned.
        """
        thread = self.threads.get(thread_id)
        if not thread:
            return {"success": False, "error": "Thread not found"}

        accessible_messages = []
        for message_id in thread.get("list_of_message_id", []):
            msg = self.messages.get(message_id)
            if not msg:
                continue  # message missing; just skip
            folder_id = msg.get("folder_id")
            folder = self.folders.get(folder_id)
            if (folder is not None) and (folder["user_id"] == user_id):
                accessible_messages.append(msg)

        return {"success": True, "data": accessible_messages}

    def get_message_read_status(self, user_id: str, message_id: str) -> dict:
        """
        Check whether a specific message is marked read or unread for the user.

        Args:
            user_id (str): The ID of the user.
            message_id (str): The message to check.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "message_id": str,
                            "user_id": str,
                            "is_read": bool
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Only a user can query read status for messages in folders they own.
        """
        if message_id not in self.messages:
            return {
                "success": False,
                "error": "Message does not exist"
            }

        message = self.messages[message_id]
        folder_id = message["folder_id"]
        folder = self.folders.get(folder_id)

        if not folder or folder["user_id"] != user_id:
            return {
                "success": False,
                "error": "User does not have access to this message"
            }

        # If user's read status is missing, treat as unread (convention)
        is_read = message.get("read_status", {}).get(user_id, False)

        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "user_id": user_id,
                "is_read": is_read
            }
        }

    def get_message_flags(self, user_id: str, message_id: str) -> dict:
        """
        Retrieve all flags (starred, important, etc.) for a given message for the specified user.

        Args:
            user_id (str): The user's id requesting the flags.
            message_id (str): The message id whose flags are to be retrieved.

        Returns:
            dict:
              - On success: { "success": True, "data": List[str] }
              - On error:   { "success": False, "error": str }

        Constraints:
            - Only emails/messages belonging to the user (i.e., in a folder owned by the user) can be accessed.
            - If user or message do not exist, return an error.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        # Check message existence
        message = self.messages.get(message_id)
        if not message:
            return { "success": False, "error": "Message not found" }
    
        # Get the folder info for the message
        folder_id = message.get("folder_id")
        folder = self.folders.get(folder_id)
        if not folder or folder["user_id"] != user_id:
            return { "success": False, "error": "Access denied" }
    
        # Fetch the flags for this user (may be an empty list)
        user_flags = message.get("flags", {}).get(user_id, [])
        return { "success": True, "data": user_flags }

    def mark_message_as_read(self, user_id: str, message_id: str) -> dict:
        """
        Set a message’s read_status to “read” for the specified user.

        Args:
            user_id (str): The ID of the user.
            message_id (str): The ID of the email message to be marked as read.

        Returns:
            dict: {
                "success": True,
                "message": "Message marked as read for user"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only emails belonging to the user can be accessed and manipulated.
            - Updates should only affect the target user.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        # Check if message exists
        if message_id not in self.messages:
            return { "success": False, "error": "Message does not exist" }
        message = self.messages[message_id]

        # Check if message belongs to the user (folder ownership)
        folder_id = message.get("folder_id")
        if folder_id not in self.folders:
            return { "success": False, "error": "Message's folder does not exist" }
        folder = self.folders[folder_id]
        if folder["user_id"] != user_id:
            return { "success": False, "error": "Message does not belong to this user" }

        # Set the read_status for this user (idempotent)
        message["read_status"][user_id] = True

        return { "success": True, "message": "Message marked as read for user" }

    def mark_message_as_unread(self, user_id: str, message_id: str) -> dict:
        """
        Set the specified message's read_status to 'unread' (False) for the given user.

        Args:
            user_id (str): The user's ID.
            message_id (str): The message's ID.

        Returns:
            dict: {
              "success": True,
              "message": "Message marked as unread for user."
            }
            OR
            dict: {
              "success": False,
              "error": "Reason for failure."
            }

        Constraints:
            - Only emails belonging to the user can be manipulated.
            - The user and message must exist.
            - The message must be in a folder belonging to the user.
            - Idempotent: If already unread for user, still returns success.
        """
        # Validate user
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Validate message
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist."}
        message = self.messages[message_id]

        # Validate that the message is in a folder owned by the user
        folder_id = message["folder_id"]
        folder_info = self.folders.get(folder_id)
        if not folder_info or folder_info["user_id"] != user_id:
            return {"success": False, "error": "Message does not belong to this user."}

        # Mark as unread (False)
        message.setdefault("read_status", {})
        message["read_status"][user_id] = False

        return {"success": True, "message": "Message marked as unread for user."}

    def mark_all_messages_as_read_in_folder(self, user_id: str, folder_id: str) -> dict:
        """
        Set all unread messages in a folder as “read” for the user.

        Args:
            user_id (str): The user's unique identifier.
            folder_id (str): The folder's unique identifier (must belong to user).

        Returns:
            dict:
                On success:
                  { "success": True, "message": "All unread messages have been marked as read in folder <folder_name> for user <username>." }
                On failure:
                  { "success": False, "error": "<description>" }

        Constraints:
            - Only emails and folders belonging to the user can be affected.
            - Read/unread status is set only for this user.
            - Action is idempotent (already read messages are not changed).
        """
        # Check that user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # Check folder exists and belongs to user
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder does not exist."}
        if folder["user_id"] != user_id:
            return {"success": False, "error": "Folder does not belong to this user."}

        # Track if anything was updated (for info, even if not required)
        affected_count = 0

        for msg in self.messages.values():
            if msg["folder_id"] == folder_id:
                # Only update if unread for this user
                if not msg["read_status"].get(user_id, False):
                    msg["read_status"][user_id] = True
                    affected_count += 1

        return {
            "success": True,
            "message": (
                f"All unread messages have been marked as read "
                f"in folder '{folder['name']}' for user '{user['username']}'."
            )
        }

    def move_message_to_folder(self, user_id: str, message_id: str, target_folder_id: str) -> dict:
        """
        Move a specific email message to another folder for the user.

        Args:
            user_id (str): The ID of the user performing the operation.
            message_id (str): The ID of the message to be moved.
            target_folder_id (str): The ID of the destination folder.

        Returns:
            dict: {
                "success": True,
                "message": "Message moved to folder <folder_name>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only emails belonging to the user can be accessed/manipulated.
            - The target folder must belong to the user.
            - Each email is assigned to exactly one folder at a time.
        """
        # Check message exists
        if message_id not in self.messages:
            return { "success": False, "error": "Message not found" }

        message = self.messages[message_id]
        current_folder_id = message["folder_id"]

        # Check current folder exists and belongs to user
        if current_folder_id not in self.folders:
            return { "success": False, "error": "Current folder does not exist" }
        if self.folders[current_folder_id]["user_id"] != user_id:
            return { "success": False, "error": "Access denied: Message does not belong to user" }

        # Check target folder exists and belongs to user
        if target_folder_id not in self.folders:
            return { "success": False, "error": "Target folder does not exist" }
        if self.folders[target_folder_id]["user_id"] != user_id:
            return { "success": False, "error": "Access denied: Target folder does not belong to user" }

        # Already in target folder?
        if current_folder_id == target_folder_id:
            return { "success": False, "error": "Message already in the target folder" }

        # All checks passed, move the message
        self.messages[message_id]["folder_id"] = target_folder_id
        folder_name = self.folders[target_folder_id]["name"]
        return { "success": True, "message": f"Message moved to folder {folder_name}" }

    def flag_message(self, user_id: str, message_id: str, flag: str) -> dict:
        """
        Add a flag (e.g., "starred", "important") to a message for the user.

        Args:
            user_id (str): The user ID for whom the flag applies.
            message_id (str): The ID of the message to be flagged.
            flag (str): The string flag to add.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only emails belonging to the user (i.e., message is in a folder owned by user) can be flagged.
            - The flags list for this user on the message is created if not present.
            - If the flag is already present, the operation is idempotent and still returns success.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": f"User {user_id} does not exist" }

        # Check message exists
        message = self.messages.get(message_id)
        if message is None:
            return { "success": False, "error": f"Message {message_id} does not exist" }

        # Check folder exists and belongs to user
        folder_id = message.get("folder_id")
        folder = self.folders.get(folder_id)
        if folder is None:
            return { "success": False, "error": "Message's folder does not exist" }
        if folder["user_id"] != user_id:
            return { "success": False, "error": "User does not have permission to flag this message" }

        # Add the flag if not present
        user_flags = message["flags"].get(user_id, [])
        if flag not in user_flags:
            user_flags.append(flag)
            message["flags"][user_id] = user_flags  # Save back (since .get() returns a copy for TypedDict/regular dicts)

        return {
            "success": True,
            "message": f"Flag '{flag}' added to message {message_id} for user {user_id}."
        }

    def unflag_message(self, user_id: str, message_id: str, flag: str) -> dict:
        """
        Remove a specific flag from a message for a user.

        Args:
            user_id (str): ID of the user performing the operation.
            message_id (str): ID of the message whose flag is to be removed.
            flag (str): The flag to remove (e.g., 'starred').

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Flag '<flag>' removed from message '<message_id>' for user '<user_id>'."
                }
                Failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Only emails belonging to the user can be accessed/manipulated.
            - If the flag does not exist for the user on this message, return an error.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check message existence
        message = self.messages.get(message_id)
        if not message:
            return { "success": False, "error": "Message does not exist." }

        folder_id = message.get("folder_id")
        folder = self.folders.get(folder_id)
        if not folder or folder["user_id"] != user_id:
            return { "success": False, "error": "User does not have access to this message." }

        # Check if flag is present for this user
        flags_dict = message.get("flags", {})
        flags_list = flags_dict.get(user_id, [])

        if flag not in flags_list:
            return { "success": False, "error": f"Flag '{flag}' not set for user on this message." }

        # Remove the flag
        flags_list.remove(flag)
        # Update: If flags_list is now empty, remove user's entry for cleanliness
        if flags_list:
            flags_dict[user_id] = flags_list
        else:
            flags_dict.pop(user_id)
        # Save changes
        message["flags"] = flags_dict

        return {
            "success": True,
            "message": f"Flag '{flag}' removed from message '{message_id}' for user '{user_id}'."
        }

    def delete_message(self, user_id: str, message_id: str) -> dict:
        """
        Moves the given message to the user's "Trash" folder.
        Only user's own messages can be manipulated.
        Cannot permanently delete from reserved folders;
        this just moves to Trash.

        Args:
            user_id (str): The id of the requesting user.
            message_id (str): The id of the message to move to Trash.

        Returns:
            dict: { "success": True, "message": <description> } on success,
                  { "success": False, "error": <reason> } on failure.

        Constraints:
            - Only user’s own messages can be manipulated.
            - Each email is assigned to exactly one folder at a time.
            - Cannot permanently delete from non-Trash reserved folders.
        """
        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check that message exists
        msg = self.messages.get(message_id)
        if msg is None:
            return {"success": False, "error": "Message does not exist"}

        # Check that the message's folder belongs to this user
        folder_id = msg.get("folder_id")
        folder = self.folders.get(folder_id)
        if folder is None or folder["user_id"] != user_id:
            return {"success": False, "error": "User does not have permission to delete this message"}

        # Find the user's Trash folder
        trash_folder_id = None
        for f in self.folders.values():
            if f["user_id"] == user_id and f["name"].lower() == "trash":
                trash_folder_id = f["folder_id"]
                break
        if trash_folder_id is None:
            return {"success": False, "error": "Trash folder does not exist for user"}

        # If already in Trash, just succeed (idempotent)
        if folder_id == trash_folder_id:
            return {"success": True, "message": "Message already in Trash folder"}

        # Move the message to Trash folder
        msg["folder_id"] = trash_folder_id
        # Optionally, could update timestamp, etc. (if implemented)

        return {"success": True, "message": f"Message {message_id} moved to Trash folder"}

    def permanently_delete_message_from_trash(self, user_id: str, message_id: str) -> dict:
        """
        Permanently remove a message from the Trash folder for a specific user.

        Args:
            user_id (str): The user's unique identifier.
            message_id (str): The message's unique identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Message permanently deleted from trash."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
        - Only messages belonging to the user (i.e., in a folder owned by the user) can be deleted.
        - Message must be currently in the Trash folder for the user.
        - Removing a message is permanent (irreversible).
        """
        # Validate user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Validate message existence
        msg = self.messages.get(message_id)
        if not msg:
            return { "success": False, "error": "Message does not exist." }

        # Find user's Trash folder
        trash_folder_id = None
        for folder in self.folders.values():
            if folder['user_id'] == user_id and folder['name'].lower() == "trash":
                trash_folder_id = folder['folder_id']
                break

        if not trash_folder_id:
            return { "success": False, "error": "Trash folder not found for the user." }

        # Check ownership: does the message belong to the user (in their folder)?
        msg_folder = self.folders.get(msg['folder_id'])
        if not msg_folder or msg_folder['user_id'] != user_id:
            return { "success": False, "error": "Message does not belong to the user." }

        # Is it in Trash?
        if msg['folder_id'] != trash_folder_id:
            return { "success": False, "error": "Message is not in the user's Trash folder." }

        # Remove from thread, if present there
        thread_id = msg.get('thread_id')
        if thread_id and thread_id in self.threads:
            thread = self.threads[thread_id]
            if message_id in thread['list_of_message_id']:
                thread['list_of_message_id'].remove(message_id)
                # Optionally: if thread now empty, remove thread (not specified by rules)
                if not thread['list_of_message_id']:
                    del self.threads[thread_id]

        # Permanently delete the message
        del self.messages[message_id]

        return {
            "success": True,
            "message": "Message permanently deleted from trash."
        }

    def create_folder(self, user_id: str, name: str, parent_folder_id: str = "") -> dict:
        """
        Create a new user-defined folder for the specified user.

        Args:
            user_id (str): The ID of the user creating the folder.
            name (str): The name of the folder to create.
            parent_folder_id (str, optional): ID of parent folder for nesting. Can be empty for root-level.

        Returns:
            dict: {"success": True, "message": "Folder '<name>' created with id <folder_id>"}
                  or {"success": False, "error": <error_reason>}

        Constraints:
            - Only allows user-specific folder creation.
            - Reserved folder names (Inbox, Sent, Trash, Archive) cannot be used.
            - Folder names must be unique for each user (case-insensitive).
            - If parent_folder_id is not empty, it must exist and belong to the user.
        """
        reserved_names = {"inbox", "sent", "trash", "archive"}

        # Check the user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Reserved name rule (case-insensitive)
        if name.strip().lower() in reserved_names:
            return {"success": False, "error": f"'{name}' is a reserved folder name."}

        # Check for unique name under the user
        for folder in self.folders.values():
            if folder["user_id"] == user_id and folder["name"].strip().lower() == name.strip().lower():
                return {"success": False, "error": f"Folder '{name}' already exists for this user."}

        # If parent_folder_id specified, it must exist and belong to the user
        if parent_folder_id:
            if parent_folder_id not in self.folders:
                return {"success": False, "error": "Parent folder does not exist."}
            if self.folders[parent_folder_id]["user_id"] != user_id:
                return {"success": False, "error": "Parent folder does not belong to the user."}

        # Generate a unique folder_id
        folder_id = str(uuid.uuid4())

        # Build folder info
        folder_info: FolderInfo = {
            "folder_id": folder_id,
            "user_id": user_id,
            "name": name.strip(),
            "parent_folder_id": parent_folder_id or "",
        }
        self.folders[folder_id] = folder_info

        return {"success": True, "message": f"Folder '{name.strip()}' created with id {folder_id}."}

    def rename_folder(self, user_id: str, folder_id: str, new_name: str) -> dict:
        """
        Rename a user-created folder. Reserved folders (Inbox, Sent, Archive, Trash) cannot be renamed.

        Args:
            user_id (str): The user requesting the rename.
            folder_id (str): The id of the folder to rename.
            new_name (str): The new name for the folder.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Folder renamed successfully." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Only folders owned by the user may be renamed.
            - Reserved folders cannot be renamed.
            - The new name must not duplicate another folder in the same parent folder for the user.
            - The new name must be non-empty and not only whitespace.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder not found." }
        if folder["user_id"] != user_id:
            return { "success": False, "error": "Permission denied to rename this folder." }
        if folder["name"] in {"Inbox", "Sent", "Archive", "Trash"}:
            return { "success": False, "error": "Cannot rename reserved folder." }
        if not isinstance(new_name, str) or not new_name.strip():
            return { "success": False, "error": "Folder name cannot be empty." }
        # Check for duplicate in the same parent folder
        for f in self.folders.values():
            if (
                f["user_id"] == user_id and 
                f["parent_folder_id"] == folder["parent_folder_id"] and
                f["name"].strip().lower() == new_name.strip().lower() and
                f["folder_id"] != folder_id
            ):
                return { "success": False, "error": "A folder with the same name already exists." }
        folder["name"] = new_name.strip()
        return { "success": True, "message": "Folder renamed successfully." }

    def remove_folder(self, user_id: str, folder_id: str) -> dict:
        """
        Delete a user-created folder for the given user.
        Reserved folders ("Inbox", "Sent", "Trash", "Archive") cannot be deleted.
        The folder must be empty (contain no messages) before deletion.

        Args:
            user_id (str): The user performing the operation.
            folder_id (str): The identifier of the folder to delete.

        Returns:
            dict:
                - success (bool)
                - message (str) on success or error (str) on failure.

        Constraints:
            - Only folders owned by the user can be removed.
            - Reserved folders ("Inbox", "Sent", "Trash", "Archive") cannot be removed.
            - Folder must be empty (no messages assigned to it).
        """
        # Check if folder exists
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder does not exist."}
        # Check folder ownership
        if folder["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: folder does not belong to user."}
        # Check reserved folders
        reserved = {"Inbox", "Sent", "Trash", "Archive"}
        if folder["name"] in reserved:
            return {"success": False, "error": f"Cannot delete reserved folder '{folder['name']}'."}
        # Check if folder is empty
        for message in self.messages.values():
            if message["folder_id"] == folder_id:
                return {"success": False, "error": "Folder is not empty: move all messages out before deletion."}
        # Remove folder
        del self.folders[folder_id]
        return {"success": True, "message": f"Folder '{folder['name']}' deleted successfully."}


class WebEmailClientEnvironment(BaseEnv):
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

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def list_folders(self, **kwargs):
        return self._call_inner_tool('list_folders', kwargs)

    def get_folder_by_name(self, **kwargs):
        return self._call_inner_tool('get_folder_by_name', kwargs)

    def list_messages_in_folder(self, **kwargs):
        return self._call_inner_tool('list_messages_in_folder', kwargs)

    def list_unread_messages_in_folder(self, **kwargs):
        return self._call_inner_tool('list_unread_messages_in_folder', kwargs)

    def get_message_info(self, **kwargs):
        return self._call_inner_tool('get_message_info', kwargs)

    def list_threads_in_folder(self, **kwargs):
        return self._call_inner_tool('list_threads_in_folder', kwargs)

    def get_thread_messages(self, **kwargs):
        return self._call_inner_tool('get_thread_messages', kwargs)

    def get_message_read_status(self, **kwargs):
        return self._call_inner_tool('get_message_read_status', kwargs)

    def get_message_flags(self, **kwargs):
        return self._call_inner_tool('get_message_flags', kwargs)

    def mark_message_as_read(self, **kwargs):
        return self._call_inner_tool('mark_message_as_read', kwargs)

    def mark_message_as_unread(self, **kwargs):
        return self._call_inner_tool('mark_message_as_unread', kwargs)

    def mark_all_messages_as_read_in_folder(self, **kwargs):
        return self._call_inner_tool('mark_all_messages_as_read_in_folder', kwargs)

    def move_message_to_folder(self, **kwargs):
        return self._call_inner_tool('move_message_to_folder', kwargs)

    def flag_message(self, **kwargs):
        return self._call_inner_tool('flag_message', kwargs)

    def unflag_message(self, **kwargs):
        return self._call_inner_tool('unflag_message', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def permanently_delete_message_from_trash(self, **kwargs):
        return self._call_inner_tool('permanently_delete_message_from_trash', kwargs)

    def create_folder(self, **kwargs):
        return self._call_inner_tool('create_folder', kwargs)

    def rename_folder(self, **kwargs):
        return self._call_inner_tool('rename_folder', kwargs)

    def remove_folder(self, **kwargs):
        return self._call_inner_tool('remove_folder', kwargs)

