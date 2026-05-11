# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
import uuid
from datetime import datetime
import time



class UserAccountInfo(TypedDict):
    _id: str
    phone_number: str
    display_name: str
    profile_picture: str
    status_message: str
    account_setting: dict

class ContactInfo(TypedDict):
    _id: str
    contact_user_id: str
    contact_display_name: str
    is_blocked: bool

class ChatInfo(TypedDict):
    chat_id: str
    participant_user_ids: List[str]
    is_group: bool
    created_at: str
    last_message_id: Optional[str]

class MessageInfo(TypedDict):
    message_id: str
    chat_id: str
    sender_user_id: str
    timestamp: str
    content: str
    media_id: Optional[str]
    message_type: str
    status: str

class MediaFileInfo(TypedDict):
    media_id: str
    file_type: str
    url_or_path: str
    uploaded_by_user_id: str
    upload_timestamp: str

class GroupInfo(TypedDict):
    group_id: str
    group_name: str
    member_user_ids: List[str]
    admin_user_ids: List[str]
    group_description: str
    group_icon: str

class _GeneratedEnvImpl:
    def __init__(self):
        # --- UserAccount entity: see UserAccountInfo
        self.account: UserAccountInfo = {}

        # --- Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}

        # --- Chats: {chat_id: ChatInfo}
        self.chats: Dict[str, ChatInfo] = {}

        # --- Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # --- MediaFiles: {media_id: MediaFileInfo}
        self.media_files: Dict[str, MediaFileInfo] = {}

        # --- Groups: {group_id: GroupInfo}
        self.groups: Dict[str, GroupInfo] = {}

        # Constraints:
        # - Only contacts that are verified WhatsApp users can be added to a user’s contact list.
        # - A user cannot send messages to or receive messages from contacts who are blocked.
        # - Group chats must have at least one admin at any time.
        # - Media files referenced in messages must exist in the MediaFile entity and be accessible by participants.

    def _sync_group_chat_participants(self, group_id: str, previous_member_user_ids: Optional[List[str]] = None) -> None:
        group_key = self._resolve_group_key(group_id)
        if group_key is None:
            return
        group = self.groups.get(group_key)
        if not group:
            return

        target_chat_ids = []
        group_public_id = group.get("group_id") or group_key
        for candidate in (group_key, group_public_id):
            if candidate is None:
                continue
            candidate = str(candidate)
            derived_chat_ids = [candidate]
            if candidate.startswith("chat_"):
                derived_chat_ids.append(candidate[5:])
            else:
                derived_chat_ids.append(f"chat_{candidate}")
            for chat_id in derived_chat_ids:
                chat = self.chats.get(chat_id)
                if chat and chat.get("is_group"):
                    target_chat_ids.append(chat_id)

        if not target_chat_ids and previous_member_user_ids is not None:
            previous_members = set(previous_member_user_ids)
            for chat_id, chat in self.chats.items():
                if chat.get("is_group") and set(chat.get("participant_user_ids", [])) == previous_members:
                    target_chat_ids.append(chat_id)

        for chat_id in dict.fromkeys(target_chat_ids):
            chat = self.chats.get(chat_id)
            if not chat:
                continue
            chat["participant_user_ids"] = list(group.get("member_user_ids", []))
            self.chats[chat_id] = chat

    def _resolve_group_key(self, group_id: str) -> Optional[str]:
        if group_id in self.groups:
            return group_id
        for key, group in self.groups.items():
            if group.get("group_id") == group_id:
                return key
        return None

    def _get_group(self, group_id: str) -> tuple[Optional[str], Optional[GroupInfo]]:
        group_key = self._resolve_group_key(group_id)
        if group_key is None:
            return None, None
        return group_key, self.groups.get(group_key)

    def _find_group_for_chat(self, chat_id: str) -> tuple[Optional[str], Optional[GroupInfo]]:
        group_key = self._resolve_group_key(chat_id)
        if group_key is not None:
            return group_key, self.groups.get(group_key)
        chat = self.chats.get(chat_id)
        for key, group in self.groups.items():
            group_public_id = group.get("group_id")
            candidates = {str(key)}
            if group_public_id is not None:
                candidates.add(str(group_public_id))
            for candidate in list(candidates):
                if candidate.startswith("chat_"):
                    candidates.add(candidate[5:])
                else:
                    candidates.add(f"chat_{candidate}")
            if chat_id in candidates:
                return key, group
            if chat and chat.get("is_group") and set(chat.get("participant_user_ids", [])) == set(group.get("member_user_ids", [])):
                return key, group
        return None, None

    def get_account_info(self) -> dict:
        """
        Retrieve the WhatsApp user's account profile information.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo  # Dictionary of account fields
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., account not found)
            }
        Constraints:
            - None (read-only operation).
            - Returns error if account not initialized.
        """
        if not self.account or "_id" not in self.account:
            return {"success": False, "error": "Account information is not available."}
        return {"success": True, "data": self.account}

    def list_contacts(self) -> dict:
        """
        Retrieve all contacts in the user's WhatsApp contact list, including their metadata
        such as display name and block status.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List of all contacts (could be empty if none)
            }
        Constraints:
            - None; only the current user's own contact list is returned.
        """
        contacts_list = list(self.contacts.values())
        return { "success": True, "data": contacts_list }

    def get_contact_info(self, contact_id: str) -> dict:
        """
        Retrieve detailed information for a specific contact by contact_id.

        Args:
            contact_id (str): Unique identifier for the contact in the user's contact list.

        Returns:
            dict: {
                "success": True,
                "data": ContactInfo,    # Full info for the contact.
            }
            or
            {
                "success": False,
                "error": str            # Reason (e.g. contact not found).
            }

        Constraints:
            - Only contacts in the user's contact list are accessible.
        """
        contact_info = self.contacts.get(contact_id)
        if not contact_info:
            return {"success": False, "error": "Contact not found"}
        return {"success": True, "data": contact_info}

    def list_chats(self) -> dict:
        """
        Retrieve all chat threads (both individual and group) that the current user participates in.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ChatInfo],  # may be empty if user is not in any chat
                }
            or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g., user id not set
                }
        Constraints:
            - Only chats where the current user's _id is listed in participant_user_ids will be returned.
        """
        user_id = self.account.get("_id")
        if not user_id:
            return {
                "success": False,
                "error": "User account not initialized or missing _id"
            }
        result = [
            chat_info
            for chat_info in self.chats.values()
            if user_id in chat_info["participant_user_ids"]
        ]
        return { "success": True, "data": result }

    def get_chat_info(self, chat_id: str) -> dict:
        """
        Retrieve detailed information for a specific chat by its chat_id.

        Args:
            chat_id (str): Unique identifier of the chat to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ChatInfo  # Dictionary of chat metadata
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g. "Chat not found"
                    }
        Constraints:
            - The given chat_id must exist.
        """
        chat_info = self.chats.get(chat_id)
        if chat_info is None:
            return {"success": False, "error": "Chat not found"}

        return {"success": True, "data": chat_info}

    def list_messages_in_chat(self, chat_id: str) -> dict:
        """
        Retrieve the sequence of messages for a given chat thread.

        Args:
            chat_id (str): The chat thread identifier.

        Returns:
            dict:
                - If chat exists: { "success": True, "data": List[MessageInfo] }
                - If chat does not exist: { "success": False, "error": "Chat does not exist" }

        Constraints:
            - chat_id must be found in the user's chats.
            - Messages are returned in ascending order by timestamp.
        """
        if chat_id not in self.chats:
            return { "success": False, "error": "Chat does not exist" }

        messages = [msg for msg in self.messages.values() if msg["chat_id"] == chat_id]
        # Sort by timestamp ascending (assume ISO string or similar lex order is correct)
        messages_sorted = sorted(messages, key=lambda x: x["timestamp"])
        return { "success": True, "data": messages_sorted }

    def get_message_info(self, message_id: str) -> dict:
        """
        Retrieve the full details of a specific message by message_id.

        Args:
            message_id (str): Unique identifier of the message to retrieve.

        Returns:
            dict:
              - If found: {"success": True, "data": MessageInfo}
              - If not found: {"success": False, "error": "Message not found"}

        Constraints:
            - message_id must exist in the environment's messages.
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message not found"}
        return {"success": True, "data": self.messages[message_id]}

    def list_media_files(self) -> dict:
        """
        Retrieve a summary of all media files associated with the user's WhatsApp account.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MediaFileInfo],  # List of all media file metadata (may be empty)
            }
        """
        if not isinstance(self.media_files, dict):
            return { "success": True, "data": [] }
        media_list = list(self.media_files.values())
        return { "success": True, "data": media_list }

    def get_media_file_info(self, media_id: str) -> dict:
        """
        Retrieve the metadata details for a specific media file using its media_id.

        Args:
            media_id (str): The unique identifier for the media file.

        Returns:
            dict:
                - If exists:
                    {
                        "success": True,
                        "data": MediaFileInfo
                    }
                - If not found:
                    {
                        "success": False,
                        "error": "Media file not found"
                    }

        Constraints:
            - The media file must exist in the environment's media_files dictionary.
        """
        media_info = self.media_files.get(media_id)
        if media_info is None:
            return { "success": False, "error": "Media file not found" }
        return { "success": True, "data": media_info }

    def list_groups(self) -> dict:
        """
        Retrieve all group chats (GroupInfo) where the user is a member.

        Returns:
            dict: {
                "success": True,
                "data": List[GroupInfo],  # list of groups the user is in (empty if none)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Requires the account to be initialized.
            - Returns only groups where the user's _id is in member_user_ids.
        """
        user_id = self.account.get("_id")
        if not user_id:
            return { "success": False, "error": "User account not initialized" }

        result = [
            group_info for group_info in self.groups.values()
            if user_id in group_info["member_user_ids"]
        ]

        return { "success": True, "data": result }

    def get_group_info(self, group_id: str) -> dict:
        """
        Retrieve detailed information and membership/admin info for a specific group.

        Args:
            group_id (str): The unique group identifier.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": GroupInfo  # group_id, group_name, member_user_ids, admin_user_ids, group_description, group_icon
                }
                On failure: {
                    "success": False,
                    "error": "Group not found"
                }

        Constraints:
            - Returns info only if group_id exists in groups.
        """
        _, group = self._get_group(group_id)
        if not group:
            return { "success": False, "error": "Group not found" }
        return { "success": True, "data": group }

    def list_group_members(self, group_id: str) -> dict:
        """
        Retrieve the list of member user IDs for the specified group.

        Args:
            group_id (str): The identifier of the group.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of user IDs of members (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. group not found
            }

        Constraints:
            - The specified group must exist.
        """
        _, group = self._get_group(group_id)
        if not group:
            return { "success": False, "error": "Group not found" }
        return { "success": True, "data": group.get('member_user_ids', []) }

    def get_blocked_contacts(self) -> dict:
        """
        Retrieve all currently blocked contacts.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # All contacts where is_blocked is True
            }
        Constraints:
            - Only accesses current user's contacts.
            - Returns empty list if no blocked contacts.
        """
        blocked = [
            contact for contact in self.contacts.values()
            if contact.get("is_blocked", False)
        ]
        return { "success": True, "data": blocked }

    def add_contact(self, contact_user_id: str, contact_display_name: str) -> dict:
        """
        Add a new verified WhatsApp user to the contact list.

        Args:
            contact_user_id (str): The WhatsApp user ID to add as a contact.
            contact_display_name (str): The display name to show in this user's contact list.

        Returns:
            dict: {
                "success": True,
                "message": "Contact added successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only verified WhatsApp users can be added.
            - A contact with the same contact_user_id cannot already exist.
            - A user cannot add themselves as a contact.
        """
        # Must not add self as contact
        if contact_user_id == self.account.get('_id'):
            return {"success": False, "error": "Cannot add yourself as a contact."}

        # Check if contact already exists
        for contact in self.contacts.values():
            if contact["contact_user_id"] == contact_user_id:
                return {"success": False, "error": "Contact already exists in your contact list."}

        # Check if the contact_user_id exists in known WhatsApp users
        # Since we only have self.account (single user), let's simulate a verification mechanism.
        # In a real environment, there should be a global registry. Here, only allow if contact_user_id is not None:
        if not contact_user_id or not isinstance(contact_user_id, str):
            return {"success": False, "error": "Invalid contact user id."}

        # Simulate presence in registry:
        # For this environment, assume there is a "verified_user_ids" list in self. If not, always fail.
        verified_ids = getattr(self, "verified_user_ids", None)
        if verified_ids is None or contact_user_id not in verified_ids:
            return {"success": False, "error": "The contact user is not a verified WhatsApp user."}

        # Create a unique contact _id (e.g., "contact_<user_id>_<number>"). For uniqueness, use len(contacts).
        new_contact_id = f"contact_{contact_user_id}_{len(self.contacts) + 1}"

        new_contact = {
            "_id": new_contact_id,
            "contact_user_id": contact_user_id,
            "contact_display_name": contact_display_name,
            "is_blocked": False
        }

        self.contacts[new_contact_id] = new_contact
        return {
            "success": True,
            "message": "Contact added successfully."
        }

    def remove_contact(self, contact_id: str) -> dict:
        """
        Remove a contact from the user's contact list.

        Args:
            contact_id (str): The ID of the contact to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Contact removed successfully."
            }
            or
            {
                "success": False,
                "error": "Contact does not exist."
            }

        Constraints:
            - contact_id must exist in self.contacts.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist." }
        del self.contacts[contact_id]
        return { "success": True, "message": "Contact removed successfully." }

    def block_contact(self, contact_id: str) -> dict:
        """
        Mark a contact as blocked in the user's contact list, preventing message exchanges.

        Args:
            contact_id (str): The unique identifier of the contact entry to block.
    
        Returns:
            dict:
                - On success: { "success": True, "message": "Contact blocked successfully." }
                - On error:   { "success": False, "error": "Contact not found." }
    
        Constraints:
            - The contact must exist in the current user's contact list.
            - Idempotent: If the contact is already blocked, returns success.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return { "success": False, "error": "Contact not found." }
    
        if contact["is_blocked"]:
            return { "success": True, "message": "Contact blocked successfully." }
    
        contact["is_blocked"] = True
        self.contacts[contact_id] = contact  # Update the dictionary (not strictly necessary for mutable dicts)
        return { "success": True, "message": "Contact blocked successfully." }

    def unblock_contact(self, contact_id: str) -> dict:
        """
        Remove the blocked status from a contact in the user's contact list.

        Args:
            contact_id (str): The unique contact ID within self.contacts.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Contact unblocked." }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - The contact must exist in the contact list.
            - Only unblock if currently blocked (is_blocked == True).
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return { "success": False, "error": "Contact does not exist." }
        if not contact.get("is_blocked", False):
            return { "success": False, "error": "Contact is not currently blocked." }
        contact["is_blocked"] = False
        self.contacts[contact_id] = contact  # Update the contact entry
        return { "success": True, "message": "Contact unblocked." }

    def update_profile_info(
        self,
        display_name: str = None,
        profile_picture: str = None,
        status_message: str = None,
        account_setting: dict = None
    ) -> dict:
        """
        Update profile information for the current user account. Only provided parameters will be updated.

        Args:
            display_name (str, optional): New display name.
            profile_picture (str, optional): URL/path for new profile picture.
            status_message (str, optional): New status message.
            account_setting (dict, optional): New account settings as a dictionary.

        Returns:
            dict: {
                "success": True,
                "message": "Profile updated successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only the provided fields will be updated.
            - If account_setting is provided, it must be a dictionary.
        """
        if display_name is not None:
            self.account["display_name"] = display_name
        if profile_picture is not None:
            self.account["profile_picture"] = profile_picture
        if status_message is not None:
            self.account["status_message"] = status_message
        if account_setting is not None:
            if not isinstance(account_setting, dict):
                return {"success": False, "error": "account_setting must be a dictionary"}
            self.account["account_setting"] = account_setting
        return {"success": True, "message": "Profile updated successfully"}

    def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: str,
        media_id: Optional[str] = None
    ) -> dict:
        """
        Send a message (text or media) to a contact or group.

        Args:
            chat_id (str): The target chat's unique identifier.
            content (str): The text content of the message. Can be empty if media is present.
            message_type (str): The type of the message ('text', 'image', 'video', etc.).
            media_id (Optional[str]): The ID of the media file, if any.

        Returns:
            dict: {
                "success": True,
                "message": "Message sent",
                "message_id": <str, newly created message ID>
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - For direct chat, the recipient must not be blocked.
            - For group chat, sender must be a group member.
            - media_id must exist (if provided) and be accessible by participants.
            - chat_id must be valid, and the sender must be a participant.
            - At least one of content or media must be present.
        """

        # 1. Check chat_id validity
        chat = self.chats.get(chat_id)
        if not chat:
            return {"success": False, "error": "Chat does not exist"}

        sender_user_id = self.account.get("_id")
        if not sender_user_id:
            return {"success": False, "error": "User account is not initialized"}

        # 2. Check sender is a participant
        if sender_user_id not in chat["participant_user_ids"]:
            return {"success": False, "error": "Sender is not a participant in this chat"}

        # 3. Minimum message content check
        if not content and not media_id:
            return {"success": False, "error": "Message must have text content or attached media"}

        # 4. Media checks
        if media_id:
            media = self.media_files.get(media_id)
            if not media:
                return {"success": False, "error": "Media file does not exist"}
            # Accessible? Must be uploaded by sender or accessible by chat members
            # Assuming for now that upload by sender or member = accessible
            # Can strengthen if needed
            if not (media["uploaded_by_user_id"] == sender_user_id or
                    media["uploaded_by_user_id"] in chat["participant_user_ids"]):
                return {"success": False, "error": "Media file not accessible by chat participants"}

        if not chat["is_group"]:
            # One-to-one chat: check if other is blocked or sender is blocked by other
            # Find the other participant
            others = [uid for uid in chat["participant_user_ids"] if uid != sender_user_id]
            if not others:
                return {"success": False, "error": "No recipient found in direct chat"}
            recipient_id = others[0]
            # Is recipient blocked by sender?
            blocked_contacts = [
                c for c in self.contacts.values()
                if c["contact_user_id"] == recipient_id and c["is_blocked"]
            ]
            if blocked_contacts:
                return {"success": False, "error": "Cannot send message: recipient is blocked"}
            # Optionally: check if sender is blocked by recipient (would need their contacts, which we may not have)

        else:
            # Group chat: sender must be member
            if sender_user_id not in chat["participant_user_ids"]:
                return {"success": False, "error": "Sender is not a member of the group"}

        # 5. Create message
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        msg_info = {
            "message_id": message_id,
            "chat_id": chat_id,
            "sender_user_id": sender_user_id,
            "timestamp": timestamp,
            "content": content,
            "media_id": media_id,
            "message_type": message_type,
            "status": "sent"
        }
        self.messages[message_id] = msg_info

        # 6. Update chat's last_message_id
        chat["last_message_id"] = message_id
        self.chats[chat_id] = chat

        return {
            "success": True,
            "message": "Message sent",
            "message_id": message_id
        }

    def delete_message(self, message_id: str, for_all: bool = False) -> dict:
        """
        Remove a message from chat history.

        Args:
            message_id (str): The message's unique identifier to delete.
            for_all (bool): If True, attempt to delete for all participants (not just for self view).

        Returns:
            dict: {
                "success": True,
                "message": str  # Success description
            }
            or
            {
                "success": False,
                "error": str  # Failure reason
            }

        Constraints:
            - Only the sender can delete for all participants (in groups, possibly admin as well).
            - Deleting for self (for_all=False) removes from user's view (here, removes it globally for this user).
            - If deleting last message in chat, update chat's last_message_id.
            - Silently succeeds if already deleted.
            - Message must exist.
        """
        user_id = self.account.get("_id")
        if not user_id:
            return {"success": False, "error": "User not authenticated."}

        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message does not exist."}

        sender_id = msg["sender_user_id"]
        chat_id = msg["chat_id"]
        chat = self.chats.get(chat_id)

        if not chat:
            return {"success": False, "error": "Associated chat does not exist."}

        # Case 1: Delete for all
        if for_all:
            allowed_for_all = user_id == sender_id
            if not allowed_for_all and chat.get("is_group"):
                _, group = self._find_group_for_chat(chat_id)
                if group and user_id in group.get("admin_user_ids", []):
                    allowed_for_all = True
            if not allowed_for_all:
                return {"success": False, "error": "Only the sender can delete a message for all participants."}
            # Remove the message globally
            self.messages.pop(message_id)
            # Update chat's last_message_id if needed
            if chat.get("last_message_id") == message_id:
                # Find previous message in this chat by timestamp
                prev_msg_id = None
                prev_ts = None
                for mid, m in self.messages.items():
                    if m["chat_id"] == chat_id:
                        if prev_ts is None or m["timestamp"] > prev_ts:
                            prev_msg_id = mid
                            prev_ts = m["timestamp"]
                self.chats[chat_id]["last_message_id"] = prev_msg_id
            return {"success": True, "message": "Message deleted for all participants."}

        # Case 2: Delete for self (default)
        # Since environment does not model per-user message hiding,
        # we physically remove the message only if sender is user (or the only participant)
        # OR we could ignore for_all flag (but as per WhatsApp: "delete for me" = remove from my view)
        # For simplicity: allow any participant to "delete for self" (i.e., this single-user account environment)

        # Remove the message (no per-user hiding)
        self.messages.pop(message_id)
        if chat.get("last_message_id") == message_id:
            # Find previous message in this chat by timestamp
            prev_msg_id = None
            prev_ts = None
            for mid, m in self.messages.items():
                if m["chat_id"] == chat_id:
                    if prev_ts is None or m["timestamp"] > prev_ts:
                        prev_msg_id = mid
                        prev_ts = m["timestamp"]
            self.chats[chat_id]["last_message_id"] = prev_msg_id

        return {"success": True, "message": "Message deleted for self." if not for_all else "Message deleted for all participants."}

    def create_group(
        self,
        group_name: str,
        member_user_ids: list,
        admin_user_ids: list,
        group_description: str = "",
        group_icon: str = ""
    ) -> dict:
        """
        Create a new group chat.

        Args:
            group_name (str): Name for the group chat (must not be empty).
            member_user_ids (List[str]): List of user IDs to be added as members (must include only verified WhatsApp users).
            admin_user_ids (List[str]): List of user IDs to be added as admins (must be subset of member_user_ids, non-empty).
            group_description (str, optional): Group description.
            group_icon (str, optional): URL or string representing group icon.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "message": "Group created",
                      "group_id": str
                    }
                On failure:
                    {
                      "success": False,
                      "error": str
                    }

        Constraints:
            - All user IDs must correspond to verified WhatsApp users (must exist as contacts or be self).
            - admin_user_ids must not be empty and must be a subset of member_user_ids.
            - group_name must not be empty.
            - Group must have at least one admin.
        """
        # Validate non-empty group name
        if not group_name or not group_name.strip():
            return {"success": False, "error": "Group name must not be empty."}

        # Validate member_user_ids and admin_user_ids as lists with at least the required members
        if not isinstance(member_user_ids, list) or len(member_user_ids) == 0:
            return {"success": False, "error": "You must specify at least one group member."}
        if not isinstance(admin_user_ids, list) or len(admin_user_ids) == 0:
            return {"success": False, "error": "You must specify at least one group admin."}

        # Admins must all be members
        if not set(admin_user_ids).issubset(set(member_user_ids)):
            return {"success": False, "error": "All admins must also be group members."}

        # A list of all verified WhatsApp user IDs: contacts' contact_user_id + self
        verified_user_ids = set([self.account.get('_id', None)])
        for contact in self.contacts.values():
            verified_user_ids.add(contact['contact_user_id'])

        # Validate that every group member is a verified WhatsApp user
        for uid in member_user_ids:
            if uid not in verified_user_ids:
                return {"success": False, "error": f"User '{uid}' is not a verified WhatsApp user."}

        # Validate that every admin is a verified WhatsApp user (should be covered by above but explicit)
        for uid in admin_user_ids:
            if uid not in verified_user_ids:
                return {"success": False, "error": f"Admin '{uid}' is not a verified WhatsApp user."}

        # Generate unique group_id (e.g., "group_<next_id>")
        group_id = f"group_{uuid.uuid4().hex}"

        # Generate GroupInfo
        group_info = {
            "group_id": group_id,
            "group_name": group_name,
            "member_user_ids": list(set(member_user_ids)),
            "admin_user_ids": list(set(admin_user_ids)),
            "group_description": group_description,
            "group_icon": group_icon,
        }
        self.groups[group_id] = group_info

        # Optionally, create a ChatInfo as well to represent this group chat
        chat_id = group_id  # Use group_id as chat_id for clarity
        self.chats[chat_id] = {
            "chat_id": chat_id,
            "participant_user_ids": list(set(member_user_ids)),
            "is_group": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_message_id": None,
        }

        return {"success": True, "message": "Group created", "group_id": group_id}

    def update_group_info(
        self,
        group_id: str,
        group_name: str = None,
        group_description: str = None,
        group_icon: str = None,
        member_user_ids: list = None,
        admin_user_ids: list = None,
    ) -> dict:
        """
        Update group settings for a WhatsApp group.

        Args:
            group_id (str): Target group to update.
            group_name (Optional[str]): New group name (if updating).
            group_description (Optional[str]): New group description (if updating).
            group_icon (Optional[str]): New group icon (if updating).
            member_user_ids (Optional[List[str]]): New list of group members (if updating).
            admin_user_ids (Optional[List[str]]): New list of group admins (if updating).

        Returns:
            dict: {
              "success": True, "message": "Group info updated successfully."
            } or {
              "success": False, "error": <str>
            }

        Constraints:
            - group_id must exist in self.groups.
            - At least one admin must remain in the group.
            - admin_user_ids must be a subset of member_user_ids.
            - All given user IDs must be valid (not checked here due to missing user registry but can be added if available).
        """
        group_key, group = self._get_group(group_id)
        if not group:
            return {"success": False, "error": "Group does not exist."}

        # Default to present state if not updating
        previous_members = list(group.get("member_user_ids", []))
        new_members = member_user_ids if member_user_ids is not None else group["member_user_ids"]
        new_admins = admin_user_ids if admin_user_ids is not None else group["admin_user_ids"]

        # Check all admins are in members
        if set(new_admins) - set(new_members):
            return {"success": False, "error": "All admins must be group members."}

        if not new_admins:
            return {"success": False, "error": "Group must have at least one admin."}

        # Update fields
        if group_name is not None:
            group["group_name"] = group_name
        if group_description is not None:
            group["group_description"] = group_description
        if group_icon is not None:
            group["group_icon"] = group_icon
        if member_user_ids is not None:
            group["member_user_ids"] = new_members
        if admin_user_ids is not None:
            group["admin_user_ids"] = new_admins

        # Save back
        self.groups[group_key] = group
        self._sync_group_chat_participants(group_id, previous_members)

        return {"success": True, "message": "Group info updated successfully."}

    def add_group_member(self, group_id: str, user_id: str) -> dict:
        """
        Add a user to a group chat.

        Args:
            group_id (str): ID of the target group chat.
            user_id (str): ID of the user to be added as a member.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> added to group <group_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Group must exist.
            - User must not already be a member.
            - User must exist (i.e., is a verified WhatsApp user, modeled as being present in account or in at least one UserAccount/contacts list).
            - Group must always have at least one admin (not compromised by this operation).
        """
        # Check if group exists
        group_key, group = self._get_group(group_id)
        if not group:
            return { "success": False, "error": f"Group '{group_id}' does not exist." }

        # Check if user is already a member
        if user_id in group["member_user_ids"]:
            return { "success": False, "error": f"User '{user_id}' is already a group member." }

        # Determine if user exists: check in contacts or account (admin may only access visible users).
        user_exists = False
        if user_id == self.account.get("_id"):
            user_exists = True
        else:
            # Check in contacts (contacts represents only this account's known users)
            for contact in self.contacts.values():
                if contact["contact_user_id"] == user_id:
                    user_exists = True
                    break
        # In a larger environment, we'd look for user in a UserAccount DB
        if not user_exists:
            return { "success": False, "error": f"User '{user_id}' does not exist or is not a verified WhatsApp user." }

        # Mutate: add user to group member list
        previous_members = list(group.get("member_user_ids", []))
        group["member_user_ids"].append(user_id)
        self.groups[group_key] = group
        self._sync_group_chat_participants(group_id, previous_members)

        return {
            "success": True,
            "message": f"User '{user_id}' added to group '{group_id}'."
        }

    def remove_group_member(self, group_id: str, user_id: str) -> dict:
        """
        Remove a member from a group chat.

        Args:
            group_id (str): The ID of the group chat.
            user_id (str): The user ID of the member to remove.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> removed from group <group_id>"
            }
            or
            {
                "success": False,
                "error": str  # Description of any failure
            }

        Constraints:
            - The group must exist.
            - The user must be a member of the group.
            - If the user is an admin, after removal there must remain at least one admin in the group.
        """
        group_key, group = self._get_group(group_id)
        if not group:
            return { "success": False, "error": "Group does not exist" }

        if user_id not in group["member_user_ids"]:
            return { "success": False, "error": "User is not a member of this group" }
    
        # If the user is an admin, make sure there is at least one admin after removal
        previous_members = list(group.get("member_user_ids", []))
        if user_id in group["admin_user_ids"]:
            # Count admins after removal
            admins_left = [uid for uid in group["admin_user_ids"] if uid != user_id]
            if len(admins_left) == 0:
                return { "success": False, "error": "Cannot remove the only admin from the group" }
            group["admin_user_ids"] = admins_left
    
        # Remove from member list
        group["member_user_ids"] = [uid for uid in group["member_user_ids"] if uid != user_id]
        self.groups[group_key] = group
        self._sync_group_chat_participants(group_id, previous_members)

        return { "success": True, "message": f"User {user_id} removed from group {group_id}" }

    def assign_group_admin(self, group_id: str, user_id: str) -> dict:
        """
        Grant admin rights to a group member.

        Args:
            group_id (str): The target group identifier.
            user_id (str): The user ID to be given admin rights.

        Returns:
            dict: On success,
              {
                "success": True,
                "message": "User <user_id> is now an admin of group <group_id>."
              }
              On failure,
              {
                "success": False,
                "error": <reason>
              }

        Constraints:
            - Only a current admin (self.account["_id"]) can assign admin status.
            - The group must exist.
            - user_id must be in member_user_ids of the group.
            - user_id must not already be in admin_user_ids.
        """
        # Check group exists
        group_key, group = self._get_group(group_id)
        if not group:
            return {"success": False, "error": "Group does not exist"}
    
        # Check that acting user is admin
        acting_user_id = self.account.get("_id")
        if acting_user_id not in group["admin_user_ids"]:
            return {"success": False, "error": "Permission denied: Only an admin can assign a new admin."}
    
        # Check user is a member
        if user_id not in group["member_user_ids"]:
            return {"success": False, "error": "User is not a member of the group."}
    
        # Check user not already admin
        if user_id in group["admin_user_ids"]:
            return {"success": False, "error": "User is already an admin of this group."}
    
        # Add to admin list
        group["admin_user_ids"].append(user_id)
        self.groups[group_key] = group  # Not strictly necessary if dicts are mutable, but explicit
    
        return {
            "success": True,
            "message": f"User {user_id} is now an admin of group {group_id}."
        }

    def revoke_group_admin(self, group_id: str, user_id: str) -> dict:
        """
        Remove admin rights from a user in a group, but ensure at least one admin always remains.

        Args:
            group_id (str): The group's unique identifier.
            user_id (str): The unique identifier of the user whose admin rights should be revoked.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Admin rights revoked for user <user_id> in group <group_id>"
                }
                On failure: {
                    "success": False,
                    "error": "<description of the error>"
                }
            
        Constraints:
            - At least one admin must remain in the group after this operation.
            - Group must exist and user must be in admin_user_ids.
        """
        group_key, group = self._get_group(group_id)
        if group is None:
            return { "success": False, "error": "Group does not exist" }

        admin_user_ids = group.get("admin_user_ids", [])
        if user_id not in admin_user_ids:
            return { "success": False, "error": f"User {user_id} is not an admin in group {group_id}" }

        if len(admin_user_ids) <= 1:
            return {
                "success": False,
                "error": "Cannot revoke admin rights: group must have at least one admin"
            }

        # Remove user_id from admin list
        group["admin_user_ids"] = [uid for uid in admin_user_ids if uid != user_id]
        self.groups[group_key] = group  # Save update

        return {
            "success": True,
            "message": f"Admin rights revoked for user {user_id} in group {group_id}"
        }

    def upload_media_file(
        self,
        file_type: str,
        url_or_path: str,
        media_id: str = None,
        upload_timestamp: str = None
    ) -> dict:
        """
        Upload and add a new media file to the account.

        Args:
            file_type (str): The type of the media file (e.g., 'image', 'video').
            url_or_path (str): The URL or path where the media file is stored.
            media_id (str, optional): Unique ID for the media file. If not provided, one will be generated.
            upload_timestamp (str, optional): Upload timestamp. If not provided, will use current time (ISO8601).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Media file uploaded",
                    "media_id": <media_id>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - media_id must be unique
            - file_type and url_or_path are required
            - uploaded_by_user_id is set to current user's id
        """

        # Pre-checks: user must be initialized
        user_id = self.account.get("_id")
        if not user_id:
            return {"success": False, "error": "User not initialized"}

        # Validate inputs
        if not file_type or not url_or_path:
            return {"success": False, "error": "file_type and url_or_path are required"}

        # Generate or validate media_id
        if media_id is None:
            media_id = str(uuid.uuid4())
        elif media_id in self.media_files:
            return {"success": False, "error": "media_id already exists"}

        # Upload timestamp: use current if not provided
        if upload_timestamp is None:
            upload_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Create MediaFile entry
        media_info = {
            "media_id": media_id,
            "file_type": file_type,
            "url_or_path": url_or_path,
            "uploaded_by_user_id": user_id,
            "upload_timestamp": upload_timestamp
        }

        # Save in media_files
        self.media_files[media_id] = media_info

        return {
            "success": True,
            "message": "Media file uploaded",
            "media_id": media_id
        }

    def delete_media_file(self, media_id: str) -> dict:
        """
        Remove an existing media file from the uploaded files, if it is not referenced by any message.

        Args:
            media_id (str): Unique identifier of the media file to remove.

        Returns:
            dict: 
                On success: { "success": True, "message": "Media file deleted" }
                On failure:
                    { "success": False, "error": "Media file does not exist" }
                    { "success": False, "error": "Media file is referenced by existing messages" }
        Constraints:
            - The media file cannot be deleted if it is still referenced by any message.
        """
        # Does the media file exist?
        if media_id not in self.media_files:
            return { "success": False, "error": "Media file does not exist" }

        # Is it referenced by any message?
        for msg in self.messages.values():
            if msg.get("media_id") == media_id:
                return {
                    "success": False,
                    "error": "Media file is referenced by existing messages"
                }

        # Delete the media file
        del self.media_files[media_id]
        return { "success": True, "message": "Media file deleted" }

    def mark_message_as_read(self, message_id: str = None, chat_id: str = None) -> dict:
        """
        Mark a message (by message_id) or all messages in a chat (by chat_id) as read.
        At least one of message_id or chat_id must be provided. If both provided, message_id is prioritized.

        Args:
            message_id (str, optional): The ID of the message to mark as read.
            chat_id (str, optional): The ID of the chat to mark all messages as read.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Description of how many messages were marked as read
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Can only mark messages as read in chats the user participates in.
        """
        user_id = self.account.get("_id")
        if message_id:
            msg = self.messages.get(message_id)
            if not msg:
                return {"success": False, "error": "Message not found"}
            chat = self.chats.get(msg["chat_id"])
            if not chat or user_id not in chat["participant_user_ids"]:
                return {"success": False, "error": "Not a participant of the chat"}
            if msg["status"] == "read":
                return {"success": True, "message": "Message already marked as read"}
            msg["status"] = "read"
            return {"success": True, "message": "1 message marked as read"}
        elif chat_id:
            chat = self.chats.get(chat_id)
            if not chat:
                return {"success": False, "error": "Chat not found"}
            if user_id not in chat["participant_user_ids"]:
                return {"success": False, "error": "Not a participant of the chat"}
            count = 0
            for msg in self.messages.values():
                if msg["chat_id"] == chat_id and msg["status"] != "read":
                    msg["status"] = "read"
                    count += 1
            return {"success": True, "message": f"{count} message(s) marked as read"}
        else:
            return {"success": False, "error": "Specify message_id or chat_id to mark as read"}

    def clear_chat_history(self, chat_id: str) -> dict:
        """
        Delete all messages in a chat thread (for the current user only).

        Args:
            chat_id (str): The unique identifier of the chat to clear.

        Returns:
            dict:
                - On success: { "success": True, "message": "Cleared chat history for user <user_id> in chat <chat_id>" }
                - On failure: { "success": False, "error": <reason> }
        Constraints:
            - The chat must exist.
            - The user must be a participant in the chat.
            - Removes all messages for this chat from the local account state (`self.messages`).
        """
        user_id = self.account.get("_id")
        if not user_id:
            return { "success": False, "error": "User account not initialized" }

        chat_info = self.chats.get(chat_id)
        if chat_info is None:
            return { "success": False, "error": "Chat does not exist" }

        if user_id not in chat_info.get("participant_user_ids", []):
            return { "success": False, "error": "User is not a participant in the chat" }

        # Gather message ids in self.messages for this chat
        message_ids_to_delete = [mid for mid, msg in self.messages.items() if msg["chat_id"] == chat_id]

        # Remove these messages from self.messages
        for mid in message_ids_to_delete:
            del self.messages[mid]

        return {
            "success": True,
            "message": f"Cleared chat history for user {user_id} in chat {chat_id}"
        }

    def leave_group(self, group_id: str) -> dict:
        """
        Allows the current user to leave the specified group chat.
        If the user is an admin, ensures at least one admin remains unless the user was the last member.
    
        Args:
            group_id (str): The ID of the group to leave.

        Returns:
            dict: On success: {
                    "success": True,
                    "message": "User <user_id> left group <group_id>"
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Group must exist.
            - User must be a member.
            - If the user is an admin, at least one admin must remain unless group becomes empty.
        """
        user_id = self.account.get("_id")
        group_key, group = self._get_group(group_id)
        if group is None:
            return { "success": False, "error": "Group does not exist" }
    
        members = group.get("member_user_ids", [])
        admins = group.get("admin_user_ids", [])

        if user_id not in members:
            return { "success": False, "error": "User is not a member of this group" }
    
        # If user is admin, check admin constraint
        is_admin = user_id in admins
        leaving_admins = [uid for uid in admins if uid != user_id]

        # If user is sole admin and other members remain,
        # must not allow leaving (would leave group with no admins)
        if is_admin and len(admins) == 1 and len(members) > 1:
            return {
                "success": False,
                "error": "Cannot leave group as the only admin. Assign another admin first."
            }

        # Remove user from members and, if present, admins
        new_members = [uid for uid in members if uid != user_id]
        new_admins = [uid for uid in admins if uid != user_id]
        group["member_user_ids"] = new_members
        group["admin_user_ids"] = new_admins

        self.groups[group_key] = group  # Update group
        self._sync_group_chat_participants(group_id, members)

        return {
            "success": True,
            "message": f"User {user_id} left group {group_id}"
        }


class WhatsAppUserAccount(BaseEnv):
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

    def get_account_info(self, **kwargs):
        return self._call_inner_tool('get_account_info', kwargs)

    def list_contacts(self, **kwargs):
        return self._call_inner_tool('list_contacts', kwargs)

    def get_contact_info(self, **kwargs):
        return self._call_inner_tool('get_contact_info', kwargs)

    def list_chats(self, **kwargs):
        return self._call_inner_tool('list_chats', kwargs)

    def get_chat_info(self, **kwargs):
        return self._call_inner_tool('get_chat_info', kwargs)

    def list_messages_in_chat(self, **kwargs):
        return self._call_inner_tool('list_messages_in_chat', kwargs)

    def get_message_info(self, **kwargs):
        return self._call_inner_tool('get_message_info', kwargs)

    def list_media_files(self, **kwargs):
        return self._call_inner_tool('list_media_files', kwargs)

    def get_media_file_info(self, **kwargs):
        return self._call_inner_tool('get_media_file_info', kwargs)

    def list_groups(self, **kwargs):
        return self._call_inner_tool('list_groups', kwargs)

    def get_group_info(self, **kwargs):
        return self._call_inner_tool('get_group_info', kwargs)

    def list_group_members(self, **kwargs):
        return self._call_inner_tool('list_group_members', kwargs)

    def get_blocked_contacts(self, **kwargs):
        return self._call_inner_tool('get_blocked_contacts', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def remove_contact(self, **kwargs):
        return self._call_inner_tool('remove_contact', kwargs)

    def block_contact(self, **kwargs):
        return self._call_inner_tool('block_contact', kwargs)

    def unblock_contact(self, **kwargs):
        return self._call_inner_tool('unblock_contact', kwargs)

    def update_profile_info(self, **kwargs):
        return self._call_inner_tool('update_profile_info', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def create_group(self, **kwargs):
        return self._call_inner_tool('create_group', kwargs)

    def update_group_info(self, **kwargs):
        return self._call_inner_tool('update_group_info', kwargs)

    def add_group_member(self, **kwargs):
        return self._call_inner_tool('add_group_member', kwargs)

    def remove_group_member(self, **kwargs):
        return self._call_inner_tool('remove_group_member', kwargs)

    def assign_group_admin(self, **kwargs):
        return self._call_inner_tool('assign_group_admin', kwargs)

    def revoke_group_admin(self, **kwargs):
        return self._call_inner_tool('revoke_group_admin', kwargs)

    def upload_media_file(self, **kwargs):
        return self._call_inner_tool('upload_media_file', kwargs)

    def delete_media_file(self, **kwargs):
        return self._call_inner_tool('delete_media_file', kwargs)

    def mark_message_as_read(self, **kwargs):
        return self._call_inner_tool('mark_message_as_read', kwargs)

    def clear_chat_history(self, **kwargs):
        return self._call_inner_tool('clear_chat_history', kwargs)

    def leave_group(self, **kwargs):
        return self._call_inner_tool('leave_group', kwargs)
