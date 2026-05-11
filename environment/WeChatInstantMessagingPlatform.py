# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import uuid
from datetime import datetime, timezone



class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    profile_info: Union[dict, str]
    account_sta: str  # e.g. 'active' or 'inactive'

class ContactListInfo(TypedDict):
    _id: str  # user_id
    contacts: List[str]  # list of user_ids
    blocked_contacts: List[str]  # list of user_ids

class ConversationInfo(TypedDict):
    conversation_id: str
    type: str  # 'individual' or 'group'
    participant_ids: List[str]
    conversation_setting: Union[dict, str]

class MessageInfo(TypedDict):
    message_id: str
    conversation_id: str
    sender_id: str
    recipient_ids: List[str]
    timestamp: Union[str, float]
    content_type: str
    content: str
    status: str  # 'sent', 'delivered', 'read', etc.

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: mapping from user_id to UserInfo
        self.users: Dict[str, UserInfo] = {}

        # Contact lists: mapping from user_id to ContactListInfo
        self.contact_lists: Dict[str, ContactListInfo] = {}

        # Conversations: mapping from conversation_id to ConversationInfo
        self.conversations: Dict[str, ConversationInfo] = {}

        # Messages: mapping from message_id to MessageInfo
        self.messages: Dict[str, MessageInfo] = {}

        # Constraints:
        # - Only users in a contact list can be messaged directly (unless restricted by privacy settings).
        # - Messages are delivered only if both sender and recipient accounts are active.
        # - Message sending and receipt are tracked for each participant in a conversation.
        self._virtual_message_epoch: float | None = None
        self._virtual_message_format: str = "iso"

    @staticmethod
    def _parse_timestamp_value(value):
        if isinstance(value, (int, float)):
            return float(value), "numeric"
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None, None
            try:
                return float(text), "numeric"
            except ValueError:
                normalized = text.replace("Z", "+00:00")
                try:
                    dt = datetime.fromisoformat(normalized)
                except ValueError:
                    return None, None
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt.timestamp(), "iso"
        return None, None

    def _initialize_virtual_message_clock(self):
        if self._virtual_message_epoch is not None:
            return

        candidates = []
        explicit_current_time = getattr(self, "current_time", None)
        if explicit_current_time is not None:
            parsed_epoch, parsed_format = self._parse_timestamp_value(explicit_current_time)
            if parsed_epoch is not None:
                candidates.append((parsed_epoch, parsed_format))

        for message in self.messages.values():
            parsed_epoch, parsed_format = self._parse_timestamp_value(message.get("timestamp"))
            if parsed_epoch is not None:
                candidates.append((parsed_epoch, parsed_format))

        if candidates:
            latest_epoch, latest_format = max(candidates, key=lambda item: item[0])
            self._virtual_message_epoch = latest_epoch
            self._virtual_message_format = latest_format or "iso"
        else:
            self._virtual_message_epoch = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp()
            self._virtual_message_format = "iso"

    def _next_virtual_message_metadata(self):
        self._initialize_virtual_message_clock()
        assert self._virtual_message_epoch is not None
        self._virtual_message_epoch += 60.0
        epoch = self._virtual_message_epoch
        if self._virtual_message_format == "numeric":
            timestamp = epoch
        else:
            timestamp = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        message_id = f"m_{int(epoch * 1000)}_{len(self.messages)}"
        return message_id, timestamp

    def _get_contact_list_entry(self, user_id: str):
        contact_info = self.contact_lists.get(user_id)
        if contact_info is not None:
            return user_id, contact_info

        for contact_key, candidate in self.contact_lists.items():
            if isinstance(candidate, dict) and candidate.get("_id") == user_id:
                return contact_key, candidate

        return None, None

    def _get_contact_list_info(self, user_id: str):
        _, contact_info = self._get_contact_list_entry(user_id)
        return contact_info

    def _ensure_contact_list_info(self, user_id: str):
        contact_key, contact_info = self._get_contact_list_entry(user_id)
        if contact_info is not None:
            return contact_key, contact_info

        self.contact_lists[user_id] = {
            "_id": user_id,
            "contacts": [],
            "blocked_contacts": [],
        }
        return user_id, self.contact_lists[user_id]

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve the UserInfo for a user given their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str  # if the user does not exist
            }

        Constraints:
            - If the user does not exist, return success=False with appropriate error message.
            - If there are multiple users with the same username, returns the first match found.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User with this username does not exist" }

    def get_user_by_display_name(self, display_name: str) -> dict:
        """
        Retrieve all users whose display_name matches the input string.

        Args:
            display_name (str): The display name to match (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo], # List of user info dicts (may be empty if no match)
            }
            OR
            {
                "success": False,
                "error": str,  # Error message (e.g., blank input)
            }

        Constraints:
            - display_name must be provided (non-empty string).
            - Multiple users can share a display_name; all matching UserInfos are returned.
        """
        if not isinstance(display_name, str) or not display_name.strip():
            return {"success": False, "error": "display_name must be a non-empty string"}
    
        matching_users = [
            user_info for user_info in self.users.values()
            if user_info.get("display_name") == display_name
        ]
        return {"success": True, "data": matching_users}

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve the full profile and account status for a user given user_id.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user's complete profile and status info.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user not found)
            }

        Constraints:
            - The user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_contact_list(self, user_id: str) -> dict:
        """
        Retrieve all contacts and blocked contacts for a specific user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "contacts": List[str],  # List of user_ids in the contact list (may be empty)
                            "blocked_contacts": List[str]  # List of user_ids in blocked contacts (may be empty)
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g., 'User or contact list not found'
                    }
    
        Constraints:
            - The user must exist and have a contact list entry in the system.
        """
        contact_info = self._get_contact_list_info(user_id)
        if not contact_info:
            return { "success": False, "error": "User or contact list not found" }

        return {
            "success": True,
            "data": {
                "contacts": list(contact_info.get("contacts", [])),
                "blocked_contacts": list(contact_info.get("blocked_contacts", []))
            }
        }

    def is_contact(self, user_id: str, target_user_id: str) -> dict:
        """
        Check whether 'target_user_id' is present in the contact list of 'user_id'.

        Args:
            user_id (str): The user whose contact list will be checked.
            target_user_id (str): The user to look for in the contact list.

        Returns:
            dict:
                On success:  { "success": True, "data": bool }
                    - True if target_user_id is in user_id's contact list, False otherwise.
                On error:    { "success": False, "error": str }

        Constraints:
            - Both users must exist.
            - user_id must have a contact list.
        """
        if user_id not in self.users:
            return { "success": False, "error": f"user_id '{user_id}' does not exist" }
        if target_user_id not in self.users:
            return { "success": False, "error": f"target_user_id '{target_user_id}' does not exist" }
        contact_list_info = self._get_contact_list_info(user_id)
        if contact_list_info is None:
            return { "success": False, "error": f"No contact list found for user_id '{user_id}'" }
        is_in_contacts = target_user_id in contact_list_info.get("contacts", [])
        return { "success": True, "data": is_in_contacts }

    def is_blocked(self, user_id: str, blocked_user_id: str) -> dict:
        """
        Check if 'blocked_user_id' is in 'user_id's blocked_contacts list.

        Args:
            user_id (str): The user whose blocked_contacts to check.
            blocked_user_id (str): The user to check for presence in blocked_contacts.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if blocked_user_id is in user_id's blocked_contacts, else False
            }
            or
            {
                "success": False,
                "error": str  # Error description (user does not exist, etc)
            }

        Constraints:
            - Both user_id and blocked_user_id must exist.
            - user_id must have an entry in contact_lists.
        """
        if user_id not in self.users:
            return {"success": False, "error": f"User '{user_id}' does not exist"}
        if blocked_user_id not in self.users:
            return {"success": False, "error": f"User '{blocked_user_id}' does not exist"}
        contact_list = self._get_contact_list_info(user_id)
        if contact_list is None:
            return {"success": False, "error": f"User '{user_id}' has no contact list"}
        is_blocked = blocked_user_id in contact_list.get("blocked_contacts", [])
        return {"success": True, "data": is_blocked}

    def check_account_active(self, user_id: str) -> dict:
        """
        Verify whether a user account is active.

        Args:
            user_id (str): The unique ID of the user to check.

        Returns:
            dict:
              - If user exists:
                  {"success": True, "data": {"active": bool}}
              - If user does not exist:
                  {"success": False, "error": "User not found"}

        Constraints:
            - user_id must exist within the platform's user registry.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        is_active = user.get('account_sta') == 'active'
        return {"success": True, "data": {"active": is_active}}

    def find_conversation_with_participant(self, user_id_1: str, user_id_2: str) -> dict:
        """
        Find an individual (non-group) conversation between two user_ids.

        Args:
            user_id_1 (str): First user ID.
            user_id_2 (str): Second user ID.

        Returns:
            dict: {
                "success": True,
                "data": ConversationInfo  # Conversation info if found
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. if users don't exist or conversation not found
            }

        Constraint:
            - Must be an 'individual' conversation involving exactly these two user IDs.
        """
        # Validate users exist
        if user_id_1 not in self.users or user_id_2 not in self.users:
            missing = []
            if user_id_1 not in self.users:
                missing.append(user_id_1)
            if user_id_2 not in self.users:
                missing.append(user_id_2)
            return {"success": False, "error": f"User(s) not found: {', '.join(missing)}"}

        # Search for the individual conversation
        participants_set = {user_id_1, user_id_2}
        for conv in self.conversations.values():
            if (conv["type"] == "individual" and 
                set(conv["participant_ids"]) == participants_set and
                len(conv["participant_ids"]) == 2):
                return {"success": True, "data": conv}

        return {"success": False, "error": "No individual conversation found between specified users."}

    def get_conversation_info(self, conversation_id: str) -> dict:
        """
        Fetch ConversationInfo by conversation_id.

        Args:
            conversation_id (str): The unique ID of the conversation to fetch.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": ConversationInfo
                    }
                - If conversation_id not found:
                    {
                        "success": False,
                        "error": "Conversation not found"
                    }
        """
        convo = self.conversations.get(conversation_id)
        if convo is None:
            return { "success": False, "error": "Conversation not found" }
        return { "success": True, "data": convo }

    def list_conversations_for_user(self, user_id: str) -> dict:
        """
        List all conversations (conversation IDs and types) that a user is participating in.

        Args:
            user_id (str): The user ID whose conversations are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[{"conversation_id": str, "type": str}]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user must exist in the platform.
            - No filtering for active/account state, all participations are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        conversations = []
        for conv in self.conversations.values():
            if "participant_ids" in conv and user_id in conv["participant_ids"]:
                conversations.append({
                    "conversation_id": conv["conversation_id"],
                    "type": conv["type"]
                })

        return {"success": True, "data": conversations}

    def list_messages_in_conversation(self, conversation_id: str) -> dict:
        """
        Retrieve all message records for a particular conversation.

        Args:
            conversation_id (str): The ID of the conversation whose messages are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # List of MessageInfo dicts in this conversation (can be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Conversation does not exist"
            }

        Constraints:
            - The conversation must exist in the platform.
        """
        if conversation_id not in self.conversations:
            return { "success": False, "error": "Conversation does not exist" }

        messages = [
            msg for msg in self.messages.values()
            if msg["conversation_id"] == conversation_id
        ]
        return { "success": True, "data": messages }

    def get_message_status(self, message_id: str, recipient_id: str) -> dict:
        """
        Return the delivery/read status for a given message and recipient.

        Args:
            message_id (str): Unique ID of the message.
            recipient_id (str): User ID of the recipient.

        Returns:
            dict: {
                "success": True,
                "data": {"message_id": str, "recipient_id": str, "status": str}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - message_id must exist.
            - recipient_id must be in the message's recipient_ids.
        Note:
            Current implementation assumes status is a single field; if per-recipient, update logic accordingly.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message not found"}

        if recipient_id not in msg["recipient_ids"]:
            return {"success": False, "error": "Recipient not part of the message"}

        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "status": msg["status"],
            },
        }

    def create_conversation(
        self,
        participant_ids: list,
        conv_type: str,
        conversation_setting=None,
    ) -> dict:
        """
        Create a new conversation (individual or group) if one does not already exist for the given participants and type.

        Args:
            participant_ids (list of str): User IDs participating in the conversation.
            conv_type (str): Either 'individual' or 'group'.
            conversation_setting (optional): Dict or str with settings for the conversation.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Conversation created" or "Conversation already exists",
                        "conversation_id": <id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - For individual, participant_ids must be length 2, not the same user.
            - For individual, both users must be in each other's contact lists.
            - All users must exist and have account_sta == 'active'.
            - Group: at least 2 participants, all must be active.
            - Only one conversation with the same set of participants and type exists.
        """

        # Clean and check participants
        participant_ids = list(set(participant_ids))  # Deduplicate
        if conv_type not in ("individual", "group"):
            return {"success": False, "error": "Invalid conversation type."}
        if not participant_ids or (conv_type == "individual" and len(participant_ids) != 2):
            return {"success": False, "error": "Individual conversations must have exactly 2 participants."}
        if conv_type == "group" and len(participant_ids) < 2:
            return {"success": False, "error": "Group conversations must have at least 2 participants."}
        # Check all users exist and are active
        for uid in participant_ids:
            if uid not in self.users:
                return {"success": False, "error": f"User {uid} does not exist."}
            if self.users[uid].get("account_sta", "") != "active":
                return {"success": False, "error": f"User {uid} is not active."}
        if conv_type == "individual":
            u1, u2 = participant_ids[0], participant_ids[1]
            contacts1 = self._get_contact_list_info(u1)
            contacts2 = self._get_contact_list_info(u2)
            contacts1 = contacts1.get("contacts", []) if contacts1 else []
            contacts2 = contacts2.get("contacts", []) if contacts2 else []
            if u2 not in contacts1 or u1 not in contacts2:
                return {"success": False, "error": "Users are not mutual contacts."}
        # Check if exact conversation exists (for individual: sorted tuple, for group: sorted set)
        part_set = sorted(participant_ids)
        for conv in self.conversations.values():
            if conv["type"] == conv_type and sorted(conv["participant_ids"]) == part_set:
                return {
                    "success": True,
                    "message": "Conversation already exists",
                    "conversation_id": conv["conversation_id"]
                }
        # Create new conversation
        new_id = "conv_" + str(uuid.uuid4())
        self.conversations[new_id] = {
            "conversation_id": new_id,
            "type": conv_type,
            "participant_ids": part_set,
            "conversation_setting": conversation_setting if conversation_setting is not None else {},
        }
        return {
            "success": True,
            "message": "Conversation created",
            "conversation_id": new_id
        }

    def send_message(
        self,
        conversation_id: str,
        sender_id: str,
        content_type: str,
        content: str
    ) -> dict:
        """
        Compose and transmit a new message in a conversation.

        Args:
            conversation_id (str): The conversation where the message is being sent.
            sender_id (str): The user sending the message.
            content_type (str): The kind of content (e.g., text, image).
            content (str): The actual message content.

        Returns:
            dict: {
                "success": True,
                "message": "Message sent successfully.",
                "message_id": str,
                "message_info": MessageInfo
            }
            OR
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - For 'individual' chats, recipient must be in sender's contact list and both users must be active.
            - For group, sender must be in group, and all recipients must be active.
            - Messages are only delivered if both sender and recipients are active.
            - Cannot send to blocked recipient.
        """
        # Validate conversation
        conv = self.conversations.get(conversation_id)
        if not conv:
            return {"success": False, "error": "Conversation does not exist."}

        # Validate sender
        sender = self.users.get(sender_id)
        if not sender:
            return {"success": False, "error": "Sender does not exist."}
        if sender["account_sta"] != "active":
            return {"success": False, "error": "Sender account is not active."}

        # Check sender is in the conversation's participants
        if sender_id not in conv["participant_ids"]:
            return {"success": False, "error": "Sender is not in conversation participants."}

        # Figure out recipients
        recipient_ids = [uid for uid in conv["participant_ids"] if uid != sender_id]
        if not recipient_ids:
            return {"success": False, "error": "No message recipients found."}

        # For individual conversations, must check contacts and blocks
        if conv["type"] == "individual":
            if len(conv["participant_ids"]) != 2:
                return {"success": False, "error": "Invalid participant count for individual conversation."}
            recipient_id = recipient_ids[0]
            recipient = self.users.get(recipient_id)
            if not recipient:
                return {"success": False, "error": "Recipient does not exist."}
            if recipient["account_sta"] != "active":
                return {"success": False, "error": "Recipient account is not active."}

            # Check contact list
            sender_contacts = self._get_contact_list_info(sender_id) or {"contacts": []}
            if recipient_id not in sender_contacts.get("contacts", []):
                return {"success": False, "error": "Recipient is not in sender's contact list."}

            # Check block
            recipient_blocked = self._get_contact_list_info(recipient_id) or {"blocked_contacts": []}
            if sender_id in recipient_blocked.get("blocked_contacts", []):
                return {"success": False, "error": "Sender is blocked by recipient."}
            # For individual, only one recipient
            active_recipient_ids = [recipient_id]
        else:  # group conversation
            # For group, remove blocked/inactive participants
            active_recipient_ids = []
            for uid in recipient_ids:
                u = self.users.get(uid)
                if not u or u["account_sta"] != "active":
                    continue
                # If sender is blocked by recipient
                recipient_blocked = self._get_contact_list_info(uid) or {"blocked_contacts": []}
                if sender_id in recipient_blocked.get("blocked_contacts", []):
                    continue
                active_recipient_ids.append(uid)
            if not active_recipient_ids:
                return {"success": False, "error": "No active, unblocked recipients in group."}

        # Create Message
        new_message_id, timestamp = self._next_virtual_message_metadata()
        message_info: MessageInfo = {
            "message_id": new_message_id,
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "recipient_ids": active_recipient_ids,
            "timestamp": timestamp,
            "content_type": content_type,
            "content": content,
            "status": "sent"
        }
        self.messages[new_message_id] = message_info

        return {
            "success": True,
            "message": "Message sent successfully.",
            "message_id": new_message_id,
            "message_info": message_info
        }

    def update_message_status(
        self, 
        message_id: str, 
        recipient_id: str, 
        new_status: str
    ) -> dict:
        """
        Change the delivery status ('sent', 'delivered', 'read') for a specific message/recipient.

        Args:
            message_id (str): The ID of the message to update.
            recipient_id (str): The recipient user ID for whom to update the status.
            new_status (str): New status to set ('sent', 'delivered', or 'read').

        Returns:
            dict: 
                Success: { "success": True, "message": "Updated message status." }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - Message must exist.
            - Recipient must be among the message's recipient_ids.
            - If status is currently a string, it will be converted to dict on first per-recipient update.
            - Valid status values: 'sent', 'delivered', 'read'.
        """
        VALID_STATUSES = {'sent', 'delivered', 'read'}
        msg = self.messages.get(message_id)
        if not msg:
            return { "success": False, "error": "Message does not exist." }
        if recipient_id not in msg.get('recipient_ids', []):
            return { "success": False, "error": "Recipient not in this message's recipient list." }
        if new_status not in VALID_STATUSES:
            return { "success": False, "error": f"Invalid status: {new_status}." }

        # Status tracking: string or per-recipient dict.
        status = msg.get('status', None)
        # Per-recipient status
        if isinstance(status, dict):
            msg['status'][recipient_id] = new_status
        elif isinstance(status, str):
            # If single recipient, just update; else migrate to dict
            if len(msg['recipient_ids']) == 1:
                msg['status'] = new_status
            else:
                # Convert to per-recipient dict
                status_dict = {uid: status for uid in msg['recipient_ids']}
                status_dict[recipient_id] = new_status
                msg['status'] = status_dict
        else:
            # Uninitialized or wrong format, default to dict
            status_dict = {uid: 'sent' for uid in msg['recipient_ids']}
            status_dict[recipient_id] = new_status
            msg['status'] = status_dict

        self.messages[message_id] = msg
        return { "success": True, "message": "Updated message status." }

    def add_contact(self, user_id: str, new_contact_id: str) -> dict:
        """
        Add a user (new_contact_id) to another user's (user_id) contacts list.

        Args:
            user_id (str): The ID of the user making the addition.
            new_contact_id (str): The ID of the user to add as a contact.

        Returns:
            dict: 
                {'success': True, 'message': 'Contact added successfully.'}
                or
                {'success': False, 'error': <error message>}

        Constraints:
            - Both users must exist.
            - A user cannot add themselves as a contact.
            - Cannot add if already a contact.
        """
        # Check both users exist
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if new_contact_id not in self.users:
            return {"success": False, "error": "User to add does not exist."}
        if user_id == new_contact_id:
            return {"success": False, "error": "Cannot add yourself as a contact."}

        # Ensure the user's contact list exists
        _, contact_info = self._ensure_contact_list_info(user_id)
        if new_contact_id in contact_info["contacts"]:
            return {"success": False, "error": "User is already a contact."}
        if new_contact_id in contact_info.get("blocked_contacts", []):
            # You technically can add someone to contacts and keep them blocked, 
            # but most UIs prevent this
            # Let's allow, but a system may want a warning

            pass

        contact_info["contacts"].append(new_contact_id)

        return {"success": True, "message": "Contact added successfully."}

    def block_contact(self, user_id: str, blocked_user_id: str) -> dict:
        """
        Add a user to the blocked_contacts for the given user.

        Args:
            user_id (str): The ID of the user who wishes to block someone.
            blocked_user_id (str): The ID of the user to block.

        Returns:
            dict: {
                "success": True,
                "message": "User <blocked_user_id> blocked for user <user_id>."
            }
            or
            {
                "success": False,
                "error": <reason>,
            }

        Constraints:
            - Both user_id and blocked_user_id must exist.
            - user_id cannot block themselves.
            - The block entry is only added if not already present.
        """
        # Check that both users exist
        if user_id not in self.users:
            return {"success": False, "error": f"User with id '{user_id}' does not exist."}
        if blocked_user_id not in self.users:
            return {"success": False, "error": f"User to block with id '{blocked_user_id}' does not exist."}
        if user_id == blocked_user_id:
            return {"success": False, "error": "User cannot block themselves."}

        # Get contact list
        _, contact_list = self._ensure_contact_list_info(user_id)
        if not contact_list:
            return {"success": False, "error": f"Contact list for user '{user_id}' not found."}

        # Check if already blocked
        if blocked_user_id in contact_list["blocked_contacts"]:
            return {"success": False, "error": f"User '{blocked_user_id}' is already blocked by '{user_id}'."}

        # Add to blocked_contacts
        contact_list["blocked_contacts"].append(blocked_user_id)

        return {
            "success": True,
            "message": f"User '{blocked_user_id}' blocked for user '{user_id}'."
        }

    def unblock_contact(self, user_id: str, blocked_user_id: str) -> dict:
        """
        Remove a user from blocked_contacts for a given user.

        Args:
            user_id (str): The user's id performing the unblock action.
            blocked_user_id (str): The id of the user to be unblocked.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "User unblocked successfully."
                }
                On failure:
                {
                    "success": False,
                    "error": "<error reason>"
                }

        Constraints:
            - Both user_id and blocked_user_id must exist as users.
            - user_id must have a contact list.
            - blocked_user_id must be in user_id's blocked_contacts.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if blocked_user_id not in self.users:
            return {"success": False, "error": "User to unblock does not exist."}
        contact_list = self._get_contact_list_info(user_id)
        if contact_list is None:
            return {"success": False, "error": "User has no contact list entry."}
        blocked_contacts = contact_list["blocked_contacts"]
        if blocked_user_id not in blocked_contacts:
            return {"success": False, "error": "User is not in the blocked contacts."}
        # Remove the user from blocked_contacts
        blocked_contacts.remove(blocked_user_id)
        return {"success": True, "message": "User unblocked successfully."}

    def remove_contact(self, user_id: str, contact_id: str) -> dict:
        """
        Remove a contact from the user's contact list.

        Args:
            user_id (str): The ID of the user removing the contact.
            contact_id (str): The ID of the user to remove from contacts.

        Returns:
            dict: {
                "success": True,
                "message": "Contact removed successfully."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - Both user_id and contact_id must exist in the platform.
            - user_id must have a contact list.
            - contact_id must exist in user_id's contacts for removal to proceed.
            - Removal is unidirectional.
        """
        # Check both users exist
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if contact_id not in self.users:
            return { "success": False, "error": "Contact user does not exist." }

        # Check contact list exists for user_id
        contact_list = self._get_contact_list_info(user_id)
        if contact_list is None:
            return { "success": False, "error": "User does not have a contact list." }
        clist = contact_list

        if contact_id not in clist["contacts"]:
            return { "success": False, "error": "Contact is not in user's contacts." }

        clist["contacts"].remove(contact_id)

        return { "success": True, "message": "Contact removed successfully." }


class WeChatInstantMessagingPlatform(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_display_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_display_name', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_contact_list(self, **kwargs):
        return self._call_inner_tool('get_contact_list', kwargs)

    def is_contact(self, **kwargs):
        return self._call_inner_tool('is_contact', kwargs)

    def is_blocked(self, **kwargs):
        return self._call_inner_tool('is_blocked', kwargs)

    def check_account_active(self, **kwargs):
        return self._call_inner_tool('check_account_active', kwargs)

    def find_conversation_with_participant(self, **kwargs):
        return self._call_inner_tool('find_conversation_with_participant', kwargs)

    def get_conversation_info(self, **kwargs):
        return self._call_inner_tool('get_conversation_info', kwargs)

    def list_conversations_for_user(self, **kwargs):
        return self._call_inner_tool('list_conversations_for_user', kwargs)

    def list_messages_in_conversation(self, **kwargs):
        return self._call_inner_tool('list_messages_in_conversation', kwargs)

    def get_message_status(self, **kwargs):
        return self._call_inner_tool('get_message_status', kwargs)

    def create_conversation(self, **kwargs):
        return self._call_inner_tool('create_conversation', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def update_message_status(self, **kwargs):
        return self._call_inner_tool('update_message_status', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def block_contact(self, **kwargs):
        return self._call_inner_tool('block_contact', kwargs)

    def unblock_contact(self, **kwargs):
        return self._call_inner_tool('unblock_contact', kwargs)

    def remove_contact(self, **kwargs):
        return self._call_inner_tool('remove_contact', kwargs)
