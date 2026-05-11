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
    display_name: str
    account_status: str
    profile_info: dict  # Additional profile fields

class ContactListInfo(TypedDict):
    _id: str  # user_id for whom this contact list belongs
    contacts: List[str]  # List of user_ids

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: str  # Could use ISO 8601 string, or float for epoch
    delivery_status: str
    is_archived: bool

class ConversationInfo(TypedDict):
    conversation_id: str
    participant_ids: List[str]
    message_ids: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for Messaging application user account system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Contact lists: {user_id: ContactListInfo}
        self.contact_lists: Dict[str, ContactListInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # Conversations: {conversation_id: ConversationInfo}
        self.conversations: Dict[str, ConversationInfo] = {}

        # Constraints:
        # - Messages can only be sent between users with valid, active account_status.
        # - A user may send messages only to users in their ContactList.
        # - Each Message must have a valid sender_id and recipient_id corresponding to existing users.
        # - Message delivery_status must be updated according to delivery and read events.
        # - Message content must comply with platform policies (e.g., no prohibited content).

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information by their username.

        Args:
            username (str): The username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User information for the matching username
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. user not found
            }

        Constraints:
            - Username lookup is case sensitive.
            - Fails if no user with the given username exists.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve full user information by their unique _id.

        Args:
            _id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,    # If user exists
            }
            or
            {
                "success": False,
                "error": str         # If user does not exist
            }

        Constraints:
            - Only checks for existence of the user _id.
        """
        user_info = self.users.get(_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Query the account status (e.g., active, inactive, suspended) for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success: { "success": True, "data": <account_status: str> }
                On failure: { "success": False, "error": "User not found" }

        Constraints:
            - user_id must correspond to an existing user in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user["account_status"]}

    def list_user_contacts(self, user_id: str) -> dict:
        """
        List all contact user_ids for a given user.

        Args:
            user_id (str): The unique identifier of the user whose contacts are to be listed.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[str],  # User IDs of contacts (may be an empty list)
                }
                OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - user_id must exist in the users registry.
            - User must have a contact list entry.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if user_id not in self.contact_lists:
            return { "success": False, "error": "User has no contact list" }

        contacts = self.contact_lists[user_id].get("contacts", [])
        return { "success": True, "data": contacts }

    def is_contact(self, user_id: str, contact_user_id: str) -> dict:
        """
        Check if contact_user_id is present in the contact list of user_id.

        Args:
            user_id (str): The user whose contact list is being checked.
            contact_user_id (str): The user to check for within the contact list.

        Returns:
            dict: 
                - { "success": True, "is_contact": bool }
                  (True if contact_user_id is a contact of user_id, False otherwise)
                - { "success": False, "error": str } on invalid input

        Constraints:
            - Both user_id and contact_user_id must correspond to existing users.
            - The contact list for user_id must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "user_id does not exist" }
        if contact_user_id not in self.users:
            return { "success": False, "error": "contact_user_id does not exist" }
        contact_list_info = self.contact_lists.get(user_id)
        if not contact_list_info:
            return { "success": False, "error": "Contact list for user does not exist" }
        is_contact = contact_user_id in contact_list_info["contacts"]
        return { "success": True, "is_contact": is_contact }

    def list_user_messages(self, user_id: str) -> dict:
        """
        Retrieve all messages (sent or received) by a user, identified by their _id.

        Args:
            user_id (str): The user ID to fetch messages for.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo]  # May be empty if no messages found.
            }
            or
            {
                "success": False,
                "error": str  # E.g., "User does not exist"
            }

        Constraints:
            - user_id must be a valid registered user (must exist in self.users).
            - Returns all messages where sender_id == user_id or recipient_id == user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        user_messages = [
            msg for msg in self.messages.values()
            if msg["sender_id"] == user_id or msg["recipient_id"] == user_id
        ]
    
        return { "success": True, "data": user_messages }

    def get_message_by_id(self, message_id: str) -> dict:
        """
        Retrieve message details by its unique message_id.

        Args:
            message_id (str): Unique identifier for the message.

        Returns:
            dict: {
                "success": True,
                "data": MessageInfo
            }
            OR
            {
                "success": False,
                "error": "Message not found"
            }

        Constraints:
            - message_id must exist in the system.
        """
        message = self.messages.get(message_id)
        if not message:
            return { "success": False, "error": "Message not found" }
        return { "success": True, "data": message }

    def get_user_conversations(self, user_id: str) -> dict:
        """
        Retrieve all conversation threads in which the given user is a participant.

        Args:
            user_id (str): ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ConversationInfo]  # List of conversations the user participates in (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "User does not exist"
            }

        Constraints:
            - The user_id must correspond to an existing user in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        user_conversations = [
            conv for conv in self.conversations.values()
            if user_id in conv.get("participant_ids", [])
        ]
        return { "success": True, "data": user_conversations }

    def get_conversation_by_id(self, conversation_id: str) -> dict:
        """
        Retrieve full information about a conversation given its conversation_id.

        Args:
            conversation_id (str): The unique identifier of the conversation.

        Returns:
            dict:
                If successful:
                    {
                        "success": True,
                        "data": ConversationInfo  # Conversation record (may have empty fields)
                    }
                If conversation not found:
                    {
                        "success": False,
                        "error": "Conversation does not exist"
                    }
        Constraints:
            - conversation_id must exist in the environment.
        """
        if conversation_id not in self.conversations:
            return { "success": False, "error": "Conversation does not exist" }
        return { "success": True, "data": self.conversations[conversation_id] }

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        content: str,
        timestamp: str,
        delivery_status: str = "sent"
    ) -> dict:
        """
        Create and send a new message from sender_id to recipient_id with given content and timestamp.

        Args:
            sender_id (str): User ID of the sender.
            recipient_id (str): User ID of the recipient.
            content (str): Message content.
            timestamp (str): Timestamp for the message (ISO 8601 or epoch string).
            delivery_status (str): Initial delivery status (default "sent").

        Returns:
            dict:
                - success: True and the created message_id on success.
                - success: False and error message on failure.

        Constraints:
            - Both sender and recipient must exist and be 'active'.
            - Recipient must be in sender's contact list.
            - Content must not be empty or prohibited (placeholder policy).
        """

        # Existence and active account checks
        sender = self.users.get(sender_id)
        recipient = self.users.get(recipient_id)
        if not sender:
            return {"success": False, "error": "Sender does not exist"}
        if not recipient:
            return {"success": False, "error": "Recipient does not exist"}
        if sender.get("account_status") != "active":
            return {"success": False, "error": "Sender account is not active"}
        if recipient.get("account_status") != "active":
            return {"success": False, "error": "Recipient account is not active"}

        # Contact check
        contact_list = self.contact_lists.get(sender_id)
        if not contact_list or recipient_id not in contact_list["contacts"]:
            return {"success": False, "error": "Recipient is not in sender's contacts"}

        # Basic content compliance (example: non-empty, no obvious banned word)
        if not content or not content.strip():
            return {"success": False, "error": "Message content cannot be empty"}
        banned_words = ["banned", "prohibited"]  # Example list
        lowered = content.lower()
        if any(banned_word in lowered for banned_word in banned_words):
            return {"success": False, "error": "Message content contains prohibited content"}

        # Create a unique message_id
        msg_id = str(uuid.uuid4())
        while msg_id in self.messages:
            msg_id = str(uuid.uuid4())

        # Construct MessageInfo
        msg: MessageInfo = {
            "message_id": msg_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "content": content,
            "timestamp": timestamp,
            "delivery_status": delivery_status,
            "is_archived": False
        }

        # Store the message
        self.messages[msg_id] = msg

        return {"success": True, "message": "Message sent successfully", "message_id": msg_id}

    def update_message_delivery_status(self, message_id: str, new_status: str) -> dict:
        """
        Change the delivery_status of a message (e.g., from sent→delivered→read).

        Args:
            message_id (str): The unique message identifier.
            new_status (str): The new delivery status value to assign.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Delivery status updated." }
                On error:
                    { "success": False, "error": "reason" }
    
        Constraints:
            - message_id must exist in self.messages.
            - Status transition must not regress: can't go from a later status to an earlier one (e.g., "read"→"sent").
            - Allowed progression: "sent" → "delivered" → "read".
            - Idempotent: same status is allowed.
        """
        # Allowed delivery status values, in order of progression
        allowed_statuses = ["sent", "delivered", "read"]
        if message_id not in self.messages:
            return { "success": False, "error": "Message does not exist." }

        message = self.messages[message_id]
        current_status = message["delivery_status"]

        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid delivery status '{new_status}'." }

        try:
            current_index = allowed_statuses.index(current_status)
            new_index = allowed_statuses.index(new_status)
        except ValueError:
            return { "success": False, "error": "Current or new status invalid." }

        # Only allow progression or idempotent updates, not regression in status
        if new_index < current_index:
            return { "success": False, "error": f"Cannot change delivery_status from '{current_status}' to '{new_status}'." }

        # Update only if changed
        if new_status != current_status:
            message["delivery_status"] = new_status
            self.messages[message_id] = message  # Refresh for strict mutability (dict ref)
    
        return { "success": True, "message": "Delivery status updated." }

    def archive_message(self, message_id: str) -> dict:
        """
        Mark a message as archived.

        Args:
            message_id (str): The unique identifier for the message to archive.

        Returns:
            dict: {
                "success": True,
                "message": "Message archived"
            }
            or
            {
                "success": False,
                "error": "Message does not exist"
            }

        Constraints:
            - The message_id must exist in the system.
            - This operation sets is_archived=True for the given message.
            - If already archived, this is a no-op and still succeeds.
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist"}

        self.messages[message_id]["is_archived"] = True

        return {"success": True, "message": "Message archived"}

    def add_contact(self, owner_user_id: str, contact_user_id: str) -> dict:
        """
        Add a user (contact_user_id) to the contact list of another user (owner_user_id).

        Args:
            owner_user_id (str): The user whose contact list will be updated
            contact_user_id (str): The user to add as a contact

        Returns:
            dict:
                - On success: { "success": True, "message": "Contact added." }
                - On error: { "success": False, "error": "<reason>" }
    
        Constraints:
            - Both owner and contact must exist as users
            - Cannot add oneself as a contact
            - Contact user must not already be in the owner's contact list
            - If owner has no contact list, create a new one
        """
        if owner_user_id not in self.users:
            return { "success": False, "error": "Owner user does not exist" }
        if contact_user_id not in self.users:
            return { "success": False, "error": "Contact user does not exist" }
        if owner_user_id == contact_user_id:
            return { "success": False, "error": "Cannot add oneself as a contact" }

        # Initialize or use the contact list
        if owner_user_id not in self.contact_lists:
            self.contact_lists[owner_user_id] = {
                "_id": owner_user_id,
                "contacts": []
            }

        contact_list = self.contact_lists[owner_user_id]

        if contact_user_id in contact_list["contacts"]:
            return { "success": False, "error": "Contact already exists in contact list" }

        contact_list["contacts"].append(contact_user_id)
        return { "success": True, "message": "Contact added." }

    def remove_contact(self, user_id: str, contact_user_id: str) -> dict:
        """
        Remove an existing contact from a user’s contact list.

        Args:
            user_id (str): The user whose contact list to modify.
            contact_user_id (str): The user to remove from the contact list.

        Returns:
            dict: {
                "success": True,
                "message": "Contact removed from user contact list."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Both users must exist.
            - The user's contact list must exist.
            - The contact must be present in the user's contact list.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if contact_user_id not in self.users:
            return {"success": False, "error": "Contact user does not exist."}
        if user_id not in self.contact_lists:
            return {"success": False, "error": "User's contact list does not exist."}
        contact_list = self.contact_lists[user_id]
        if contact_user_id not in contact_list["contacts"]:
            return {"success": False, "error": "Contact user is not in the contact list."}
        contact_list["contacts"].remove(contact_user_id)
        return {"success": True, "message": "Contact removed from user contact list."}

    def create_conversation(self, participant_ids: list) -> dict:
        """
        Initiate a new conversation with a set of participant user_ids.

        Args:
            participant_ids (list of str): List of user_ids to include in the conversation.

        Returns:
            dict:
                On success:
                    {'success': True, 'message': 'Conversation created', 'conversation_id': <new_id>}
                On failure:
                    {'success': False, 'error': <reason>}

        Constraints:
            - Each participant_id must correspond to an existing user in self.users.
            - There must be at least 2 distinct participants in the conversation.
            - Duplicates in participant_ids are ignored.
            - conversation_id must be globally unique.
        """
        if not isinstance(participant_ids, list) or not participant_ids:
            return {"success": False, "error": "participant_ids must be a non-empty list"}

        # Remove duplicates while preserving order
        seen = set()
        unique_participants = []
        for uid in participant_ids:
            if uid not in seen:
                unique_participants.append(uid)
                seen.add(uid)
        participant_ids = unique_participants

        if len(participant_ids) < 2:
            return {"success": False, "error": "At least two participants required to start a conversation"}

        for uid in participant_ids:
            if uid not in self.users:
                return {"success": False, "error": f"User '{uid}' does not exist"}

        # Generate a unique conversation_id (simple increment or UUID)
        conversation_id = str(uuid.uuid4())
        while conversation_id in self.conversations:
            conversation_id = str(uuid.uuid4())

        # Create the conversation object
        conversation_info = {
            "conversation_id": conversation_id,
            "participant_ids": participant_ids,
            "message_ids": [],
        }
        self.conversations[conversation_id] = conversation_info

        return {
            "success": True,
            "message": "Conversation created",
            "conversation_id": conversation_id
        }

    def add_message_to_conversation(self, conversation_id: str, message_id: str) -> dict:
        """
        Append a message_id to the message_ids list of an existing conversation.

        Args:
            conversation_id (str): The ID of the conversation to which to add the message.
            message_id (str): The ID of the message to add.

        Returns:
            dict: {
                "success": True,
                "message": "Message added to conversation."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both conversation_id and message_id must exist.
            - The message_id cannot already be in the conversation's message_ids.
            - (Recommended) The message's sender and recipient should be among the conversation's participant_ids.
        """
        # Check conversation exists
        if conversation_id not in self.conversations:
            return {"success": False, "error": "Conversation does not exist."}
    
        # Check message exists
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist."}
    
        conversation = self.conversations[conversation_id]
        msg_ids = conversation["message_ids"]
    
        # Prevent duplicate
        if message_id in msg_ids:
            return {"success": False, "error": "Message already in conversation."}
    
        # Ensure message parties are conversation participants
        message = self.messages[message_id]
        sender = message["sender_id"]
        recipient = message["recipient_id"]
        participants = conversation["participant_ids"]
        if sender not in participants or recipient not in participants:
            return {
                "success": False,
                "error": "Message sender and recipient must be participants in the conversation."
            }
    
        msg_ids.append(message_id)
        # Update conversation state
        self.conversations[conversation_id]["message_ids"] = msg_ids
        return {"success": True, "message": "Message added to conversation."}

    def delete_message(self, message_id: str, requester_id: str) -> dict:
        """
        Remove a message from the system.
        Can be performed by the sender, recipient, or (if policy allows) an admin user.

        Args:
            message_id (str): The unique identifier of the message to be deleted.
            requester_id (str): The user_id of the account requesting the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Message <id> deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The message must exist.
            - Only the sender, recipient, or admin may delete a message (admin not implemented here).
            - Must also remove the message_id from any ConversationInfo that contains it.
        """
        # Check message exists
        if message_id not in self.messages:
            return {"success": False, "error": "Message not found."}

        msg = self.messages[message_id]
        sender_id = msg['sender_id']
        recipient_id = msg['recipient_id']

        # Check requester is sender or recipient
        if requester_id != sender_id and requester_id != recipient_id:
            return {"success": False, "error": "Permission denied: only sender or recipient can delete the message."}

        # Remove from all conversations
        for conv in self.conversations.values():
            if message_id in conv["message_ids"]:
                conv["message_ids"] = [mid for mid in conv["message_ids"] if mid != message_id]

        # Delete message
        del self.messages[message_id]

        return {"success": True, "message": f"Message {message_id} deleted."}

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Change the account_status of a user (e.g., activate, suspend, deactivate).

        Args:
            user_id (str): The user ID whose status should be updated.
            new_status (str): The new status value to assign (e.g., "active", "suspended", "deactivated").
                NOTE: This function does not enforce a specific set of allowed status values.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "message": "User account status updated to <new_status>"
                    }
                If user not found:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - user_id must exist in the system.
            - No check on validity of new_status value unless otherwise specified.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        self.users[user_id]["account_status"] = new_status
        return {
            "success": True,
            "message": f"User account status updated to {new_status}"
        }


class MessagingUserAccountSystem(BaseEnv):
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
            if key == "contact_lists" and isinstance(value, dict):
                normalized_contact_lists = {}
                for raw_key, raw_value in value.items():
                    contact_list = copy.deepcopy(raw_value)
                    owner_user_id = None
                    if isinstance(raw_key, str) and raw_key in env.users:
                        owner_user_id = raw_key
                    elif isinstance(contact_list, dict):
                        raw_list_id = contact_list.get("_id")
                        if isinstance(raw_list_id, str):
                            if raw_list_id in env.users:
                                owner_user_id = raw_list_id
                            elif raw_list_id.startswith("cl_") and raw_list_id[3:] in env.users:
                                owner_user_id = raw_list_id[3:]
                    if owner_user_id is None and isinstance(raw_key, str) and raw_key.startswith("cl_") and raw_key[3:] in env.users:
                        owner_user_id = raw_key[3:]
                    if owner_user_id is None:
                        owner_user_id = raw_key
                    if isinstance(contact_list, dict):
                        contact_list["_id"] = owner_user_id
                    normalized_contact_lists[owner_user_id] = contact_list
                setattr(env, key, normalized_contact_lists)
                continue
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def list_user_contacts(self, **kwargs):
        return self._call_inner_tool('list_user_contacts', kwargs)

    def is_contact(self, **kwargs):
        return self._call_inner_tool('is_contact', kwargs)

    def list_user_messages(self, **kwargs):
        return self._call_inner_tool('list_user_messages', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def get_user_conversations(self, **kwargs):
        return self._call_inner_tool('get_user_conversations', kwargs)

    def get_conversation_by_id(self, **kwargs):
        return self._call_inner_tool('get_conversation_by_id', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def update_message_delivery_status(self, **kwargs):
        return self._call_inner_tool('update_message_delivery_status', kwargs)

    def archive_message(self, **kwargs):
        return self._call_inner_tool('archive_message', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def remove_contact(self, **kwargs):
        return self._call_inner_tool('remove_contact', kwargs)

    def create_conversation(self, **kwargs):
        return self._call_inner_tool('create_conversation', kwargs)

    def add_message_to_conversation(self, **kwargs):
        return self._call_inner_tool('add_message_to_conversation', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def update_user_account_status(self, **kwargs):
        return self._call_inner_tool('update_user_account_status', kwargs)
