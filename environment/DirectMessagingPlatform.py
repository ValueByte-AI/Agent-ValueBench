# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
from typing import Optional, List, Dict, Any
import time
import uuid
import json



class UserInfo(TypedDict):
    _id: str
    username: str
    profile_info: Dict[str, Any]
    account_status: str  # (inferred from 'account_sta')

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    recipient_ids: List[str]  # (from 'recipient_id(s)')
    content: str
    timestamp: float  # can also be str if needed
    thread_id: str
    topic_tags: List[str]
    # delivery_status: Maps recipient_id -> status
    delivery_status: Dict[str, str]
    # read_status: Maps recipient_id -> read/unread
    read_status: Dict[str, str]

class MessageThreadInfo(TypedDict):
    thread_id: str
    participant_ids: List[str]
    last_updated: float  # can also be str if needed
    topic_tag: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Social media direct messaging platform stateful environment.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # MessageThreads: {thread_id: MessageThreadInfo}
        self.message_threads: Dict[str, MessageThreadInfo] = {}

        # Constraints (for further implementation):
        # - Only users involved in a direct message can access its content.
        # - Message content is immutable after being sent (editing creates a new version or message).
        # - Topic filters (tags) can be assigned by senders or via automatic detection for searchability.
        # - Messages are timestamped to establish recency.
        # - Notification state (delivery_status, read_status) must be tracked for each recipient.
        # - Deleting a message or user may affect visibility for other participants depending on privacy settings.
        self._deleted_msgs_for_user: Dict[str, set[str]] = {}

    def _message_deleted_for_user(self, message_id: str, user_id: str) -> bool:
        deleted_users = self._deleted_msgs_for_user.get(message_id, set())
        return user_id in deleted_users

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user details given a username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": UserInfo}
                On failure:
                    {"success": False, "error": "User not found"}
        Constraints:
            - Usernames are expected to be unique.
        """
        for user in self.users.values():
            if user.get("username") == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details using a user ID.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": UserInfo  # User metadata dictionary
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - User ID must exist in the platform.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def search_messages_by_recipient_and_topic(
        self,
        recipient_id: str,
        topic_tags: 'List[str]' = None
    ) -> dict:
        """
        Find all messages received by a user, optionally filtering by topic tags.

        Args:
            recipient_id (str): User ID of the recipient (must exist).
            topic_tags (Optional[List[str]]): List of topic tags, match messages containing ANY tag.
                If None or empty, all messages for recipient are returned.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[MessageInfo] }
                - On error: { "success": False, "error": error_str }

        Constraints:
            - Only messages where recipient_id is present in MessageInfo.recipient_ids are considered.
            - User (recipient) must exist.
        """
        if recipient_id not in self.users:
            return { "success": False, "error": "Recipient user does not exist" }

        if isinstance(topic_tags, str):
            topic_tags = [topic_tags]
        elif topic_tags is not None and not isinstance(topic_tags, list):
            return { "success": False, "error": "topic_tags must be a list of strings" }

        results = []
        topic_tags_set = set(topic_tags) if topic_tags else None
        for msg in self.messages.values():
            if recipient_id in msg.get("recipient_ids", []):
                if self._message_deleted_for_user(msg["message_id"], recipient_id):
                    continue
                if not topic_tags_set:
                    results.append(msg)
                else:
                    if set(msg.get("topic_tags", [])) & topic_tags_set:
                        results.append(msg)
        return {
            "success": True,
            "data": results
        }


    def get_recent_messages_for_user(self, user_id: str, since_timestamp: Optional[float] = None) -> dict:
        """
        Retrieve the most recent direct messages for a specific user, optionally filtered by a minimum timestamp.

        Args:
            user_id (str): The ID of the user.
            since_timestamp (float, optional): Only include messages sent at or after this timestamp. If None, include all.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # Most recent messages first
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - Only users involved in a message as sender or recipient can access the message.
            - User must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Filter relevant messages
        relevant_messages: List[MessageInfo] = []
        for msg in self.messages.values():
            if user_id == msg["sender_id"] or user_id in msg["recipient_ids"]:
                if self._message_deleted_for_user(msg["message_id"], user_id):
                    continue
                if since_timestamp is None or msg["timestamp"] >= since_timestamp:
                    relevant_messages.append(msg)

        # Sort by timestamp descending (most recent first)
        relevant_messages.sort(key=lambda m: m["timestamp"], reverse=True)

        return { "success": True, "data": relevant_messages }

    def get_unread_messages_for_user(self, user_id: str) -> dict:
        """
        List all unread messages for a user.

        Args:
            user_id (str): The unique identifier of the user to fetch unread messages for.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[MessageInfo]  # All messages for which user_id is in recipient_ids and read_status[user_id] == "unread"
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g. user does not exist
                    }

        Constraints:
            - Only users involved in a direct message can access its content (user must be a recipient).
            - User must exist in the platform.
            - Message content is returned as-is; read_status must be tracked per recipient.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = []
        for msg in self.messages.values():
            if user_id in msg['recipient_ids']:
                if self._message_deleted_for_user(msg["message_id"], user_id):
                    continue
                # Defensive: only process if read_status contains user_id
                status = msg['read_status'].get(user_id)
                if status == "unread":
                    result.append(msg)

        return { "success": True, "data": result }

    def get_message_by_id(self, message_id: str, requesting_user_id: str) -> dict:
        """
        Retrieve a message's full details by its message_id.
    
        Args:
            message_id (str): Unique identifier of the message.
            requesting_user_id (str): The ID of the user requesting the message (must be sender or recipient).

        Returns:
            dict: {
                "success": True,
                "data": MessageInfo
            }
            or
            {
                "success": False,
                "error": str  # Error message (not found / access denied)
            }
    
        Constraints:
            - Only sender or recipient(s) of the message may view its content.
        """
        message = self.messages.get(message_id)
        if message is None:
            return {"success": False, "error": "Message not found"}

        # Enforce access constraint
        if (requesting_user_id != message["sender_id"] and
                requesting_user_id not in message["recipient_ids"]):
            return {
                "success": False,
                "error": "Access denied: user not authorized to view this message"
            }
        if self._message_deleted_for_user(message_id, requesting_user_id):
            return {"success": False, "error": "Message not found"}
    
        return {"success": True, "data": message}

    def get_message_thread_by_id(self, thread_id: str) -> dict:
        """
        Retrieve full details of a message thread (participants, last updated, topic) by thread_id.

        Args:
            thread_id (str): The unique thread identifier.

        Returns:
            dict: {
                "success": True,
                "data": MessageThreadInfo,  # Thread info dictionary
            }
            or
            {
                "success": False,
                "error": str  # "Thread does not exist"
            }

        Constraints:
            - The thread_id must exist in the system.
        """
        thread_info = self.message_threads.get(thread_id)
        if thread_info is None:
            return { "success": False, "error": "Thread does not exist" }
        return { "success": True, "data": thread_info }

    def list_threads_for_user(self, user_id: str) -> dict:
        """
        Retrieve all message threads in which a specific user participates.

        Args:
            user_id (str): The ID of the user whose threads are to be listed.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[MessageThreadInfo],  # List of threads (can be empty)
                }
            On failure (if user does not exist):
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - Only threads where the user_id appears in the thread's participant_ids are listed.
            - The user must exist in self.users.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        threads = [
            thread_info
            for thread_info in self.message_threads.values()
            if user_id in thread_info.get("participant_ids", [])
        ]

        return { "success": True, "data": threads }

    def search_threads_by_topic(self, topic_tag: str) -> dict:
        """
        Find all message threads whose topic_tag exactly matches the provided topic string.

        Args:
            topic_tag (str): The topic string to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageThreadInfo]  # list of thread infos with matching topic_tag (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # error description for invalid search
            }

        Constraints:
            - topic_tag must be a non-empty string.
            - No thread access constraints are enforced (all threads are included).
        """
        if not isinstance(topic_tag, str) or not topic_tag.strip():
            return {"success": False, "error": "Invalid or empty topic_tag"}

        result = [
            thread_info for thread_info in self.message_threads.values()
            if thread_info.get("topic_tag") == topic_tag
        ]
        return {"success": True, "data": result}

    def get_message_delivery_status(self, message_id: str) -> dict:
        """
        Get the delivery status (e.g., delivered, failed, etc.) of a message for each recipient.

        Args:
            message_id (str): The unique identifier of the message to query.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": Dict[str, str],  # Mapping recipient_id -> delivery status
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason the operation failed (e.g., message not found)
                    }

        Constraints:
            - If the message does not exist, return an error.
            - (Strictly speaking, only participants can access this, but in the absence of user_id context, return the status if found.)
        """
        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message not found"}

        delivery_status = msg.get("delivery_status", {})
        return {"success": True, "data": delivery_status}

    def get_message_read_status(self, message_id: str) -> dict:
        """
        Get the read/unread status of a message for each recipient.

        Args:
            message_id (str): Unique identifier of the target message.

        Returns:
            dict:
                - success: True and data key with read_status dictionary {recipient_id: "read"/"unread"} if message exists.
                - success: False and error key if the message is not found.

        Constraints:
            - Message must exist (message_id present in self.messages).
            - No access control/user permission checks performed here.
        """
        message = self.messages.get(message_id)
        if message is None:
            return {"success": False, "error": "Message not found"}

        # Return the mapping from recipient_id to read/unread status
        return {"success": True, "data": dict(message.get("read_status", {}))}

    def get_messages_in_thread(self, thread_id: str) -> dict:
        """
        List all messages contained in a specific thread.

        Args:
            thread_id (str): Unique identifier of the message thread.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # List of messages sorted by timestamp
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. thread does not exist
            }

        Constraints:
            - The specified thread_id must exist.
            - If no messages are in the thread, returns empty list.
        """
        if thread_id not in self.message_threads:
            return { "success": False, "error": "Thread does not exist" }

        messages_in_thread = [
            msg for msg in self.messages.values()
            if msg["thread_id"] == thread_id
        ]

        # Sort messages by timestamp ascending (chronological order)
        messages_in_thread.sort(key=lambda x: x["timestamp"])

        return { "success": True, "data": messages_in_thread }

    def send_direct_message(
        self,
        sender_id: str,
        recipient_ids: list,
        content: str,
        topic_tags: list = None,
        thread_id: str = None
    ) -> dict:
        """
        Send a new direct message from a sender to one or more recipients.

        Args:
            sender_id (str): User ID of sender. Must exist.
            recipient_ids (List[str]): List of user IDs to receive the message. All must exist.
            content (str): The message content. Must be nonempty.
            topic_tags (List[str], optional): List of topic tags, if any.
            thread_id (str, optional): Assign message to existing thread (must exist and include all participants), otherwise a new thread is created.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Direct message sent", "message_id": <new_id>}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - Sender and all recipient users MUST exist in self.users.
            - If a thread_id is specified, it MUST exist and include all participants.
            - Content must be nonempty (not blank/whitespace).
            - Message gets unique message_id and current timestamp.
            - Read/delivery status for each recipient is initialized to 'unread', 'undelivered'.
            - Topic tags may be assigned by sender.
        """

        # Validate sender
        if sender_id not in self.users:
            return { "success": False, "error": "Sender does not exist." }
        # Validate recipients
        if not isinstance(recipient_ids, list) or len(recipient_ids) == 0:
            return { "success": False, "error": "At least one recipient is required." }
        for rid in recipient_ids:
            if rid not in self.users:
                return { "success": False, "error": f"Recipient {rid} does not exist." }

        # Validate content
        if not isinstance(content, str) or not content.strip():
            return { "success": False, "error": "Message content cannot be empty." }
        # Normalize topic tags
        if topic_tags is None:
            topic_tags = []

        # Participants: sender+recipients
        participants_set = set([sender_id] + recipient_ids)

        # Handle thread (existing or new)
        if thread_id:
            thread = self.message_threads.get(thread_id)
            if not thread:
                return { "success": False, "error": "Specified thread does not exist." }
            # Thread must include all participants
            if not participants_set.issubset(set(thread["participant_ids"])):
                return {
                    "success": False,
                    "error": "All sender and recipients must be participants in the thread."
                }
        else:
            # Create new thread
            thread_id = str(uuid.uuid4())
            thread_info = {
                "thread_id": thread_id,
                "participant_ids": list(participants_set),
                "last_updated": time.time(),
                "topic_tag": topic_tags[0] if topic_tags else ""
            }
            self.message_threads[thread_id] = thread_info

        # Generate unique message_id
        message_id = str(uuid.uuid4())
        while message_id in self.messages:
            message_id = str(uuid.uuid4())

        # Set up status dictionaries
        delivery_status = {rid: "undelivered" for rid in recipient_ids}
        read_status = {rid: "unread" for rid in recipient_ids}

        # Build message info
        timestamp = time.time()
        message_info = {
            "message_id": message_id,
            "sender_id": sender_id,
            "recipient_ids": recipient_ids,
            "content": content,
            "timestamp": timestamp,
            "thread_id": thread_id,
            "topic_tags": topic_tags,
            "delivery_status": delivery_status,
            "read_status": read_status,
        }
        self.messages[message_id] = message_info

        # Update thread's last_updated field
        self.message_threads[thread_id]["last_updated"] = timestamp

        return {
            "success": True,
            "message": "Direct message sent",
            "message_id": message_id
        }

    def update_message_read_status(self, message_id: str, recipient_id: str, read_status: str) -> dict:
        """
        Set a message as read (or unread) for a specific recipient.

        Args:
            message_id (str): ID of the message to update
            recipient_id (str): User ID of the recipient
            read_status (str): New read status value ("read" or "unread")

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Read status updated for user on message."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Message must exist.
            - Recipient must be one of the message's recipient_ids.
            - Only "read" or "unread" are valid read statuses.
        """
        if message_id not in self.messages:
            return { "success": False, "error": "Message does not exist." }

        message = self.messages[message_id]
        if recipient_id not in message["recipient_ids"]:
            return { "success": False, "error": "User is not a recipient of the message." }

        if read_status not in ["read", "unread"]:
            return { "success": False, "error": "Invalid read status. Must be 'read' or 'unread'." }

        # Update read status
        message["read_status"][recipient_id] = read_status

        return { "success": True, "message": f"Read status updated to '{read_status}' for user {recipient_id} on message {message_id}." }

    def update_message_delivery_status(self, message_id: str, recipient_id: str, status: str) -> dict:
        """
        Update the delivery status of a given message for a specific recipient.

        Args:
            message_id (str): The unique identifier of the message.
            recipient_id (str): The user ID of the recipient whose delivery status is to be updated.
            status (str): The new delivery status (e.g. 'delivered', 'failed', 'pending').

        Returns:
            dict: {
                "success": True,
                "message": "Delivery status updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The message must exist.
            - recipient_id must be one of the message's recipient_ids.
            - Only the delivery_status for the specified recipient is updated.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message not found."}

        if recipient_id not in msg["recipient_ids"]:
            return {"success": False, "error": "Recipient is not in the message's recipients."}

        # Update delivery status
        msg["delivery_status"][recipient_id] = status

        return {"success": True, "message": "Delivery status updated successfully."}

    def assign_topic_tag_to_thread(self, thread_id: str, topic_tag: str) -> dict:
        """
        Assign or change a topic tag for a given message thread.

        Args:
            thread_id (str): Identifier of the message thread.
            topic_tag (str): The topic tag to assign to the thread.

        Returns:
            dict: {
                "success": True,
                "message": "Topic tag updated for thread <thread_id>"
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., thread not found or invalid topic tag)
            }

        Constraints:
            - Thread must exist.
            - Topic tag must not be empty.
        """
        if thread_id not in self.message_threads:
            return { "success": False, "error": "Thread does not exist" }
        if not topic_tag or not isinstance(topic_tag, str) or topic_tag.strip() == "":
            return { "success": False, "error": "Invalid topic tag" }

        self.message_threads[thread_id]["topic_tag"] = topic_tag.strip()

        return { "success": True, "message": f"Topic tag updated for thread {thread_id}" }

    def delete_message_for_user(self, message_id: str, user_id: str) -> dict:
        """
        Remove a message from visibility for a specific user, subject to privacy constraints.
        The message remains in the system for other participants, but after this operation
        the specified user will not see the message in their queries.

        Args:
            message_id (str): The message to hide/remove for the user.
            user_id (str): The user for whom the message should be deleted from view.

        Returns:
            dict: Success or error structure:
                {
                    "success": True,
                    "message": "Message <id> has been deleted from visibility for user <id>."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }
    
        Constraints:
            - The message and user must exist.
            - The user must be the sender or a recipient (a participant) of the message.
            - Deletion only affects user's view, not global state.
        """

        # Check if message exists
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist."}

        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        msg = self.messages[message_id]
        participants = set(msg["recipient_ids"]) | {msg["sender_id"]}
        if user_id not in participants:
            return {"success": False, "error": "User is not a participant in the message."}

        # Check if already deleted for this user
        if message_id in self._deleted_msgs_for_user and user_id in self._deleted_msgs_for_user[message_id]:
            return {"success": False, "error": "Message is already deleted from visibility for this user."}

        # Add deletion mark
        if message_id not in self._deleted_msgs_for_user:
            self._deleted_msgs_for_user[message_id] = set()
        self._deleted_msgs_for_user[message_id].add(user_id)

        return {
            "success": True,
            "message": f"Message {message_id} has been deleted from visibility for user {user_id}."
        }

    def delete_user_account(self, user_id: str) -> dict:
        """
        Remove a user’s account from the platform.
        Effects:
            - Removes user from all message threads' participant lists. Deletes threads with no remaining participants.
            - Removes user from all messages (as sender and/or recipient).
                - If user is the sender, mark sender as '<deleted>'.
                - If user is a recipient, removes user from recipient_ids, delivery_status, and read_status for that message.
                - Deletes messages with no sender and no recipients.
            - Removes user from the users list.
        Args:
            user_id (str): The unique ID of the user to delete.
        Returns:
            dict: {
                "success": True,
                "message": "User account deleted and related records updated."
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - If user does not exist, returns an error.
            - Implements platform privacy rules in the absence of detailed settings.
        """

        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Remove user from all message threads
        threads_to_delete = []
        for thread_id, thread_info in list(self.message_threads.items()):
            if user_id in thread_info["participant_ids"]:
                thread_info["participant_ids"] = [
                    uid for uid in thread_info["participant_ids"] if uid != user_id
                ]
                if not thread_info["participant_ids"]:
                    # No participants left: delete thread
                    threads_to_delete.append(thread_id)

        for thread_id in threads_to_delete:
            del self.message_threads[thread_id]

        # Update messages: remove user as sender/recipient
        messages_to_delete = []
        for msg_id, msg in list(self.messages.items()):
            changed = False
            # If user is the sender, mark sender as '<deleted>'
            if msg["sender_id"] == user_id:
                msg["sender_id"] = "<deleted>"
                changed = True

            # Remove user from recipients
            if user_id in msg["recipient_ids"]:
                msg["recipient_ids"] = [uid for uid in msg["recipient_ids"] if uid != user_id]
                changed = True
                # Remove delivery_status and read_status entries
                if user_id in msg["delivery_status"]:
                    del msg["delivery_status"][user_id]
                if user_id in msg["read_status"]:
                    del msg["read_status"][user_id]

            # If after all updates, message has no sender (or sender is '<deleted>') and no recipients, delete message
            if (msg["sender_id"] == "<deleted>" or not msg["sender_id"]) and not msg["recipient_ids"]:
                messages_to_delete.append(msg_id)

        for msg_id in messages_to_delete:
            del self.messages[msg_id]

        # Remove user from users
        del self.users[user_id]

        return {
            "success": True,
            "message": "User account deleted and related records updated."
        }


class DirectMessagingPlatform(BaseEnv):
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
            if key == "_deleted_msgs_for_user":
                normalized = {}
                raw_value = copy.deepcopy(value)
                if isinstance(raw_value, str):
                    try:
                        raw_value = json.loads(raw_value)
                    except Exception:
                        raw_value = {}
                if isinstance(raw_value, dict):
                    for message_id, users in raw_value.items():
                        if isinstance(users, str):
                            normalized[message_id] = {users}
                        elif isinstance(users, (list, set, tuple)):
                            normalized[message_id] = set(users)
                setattr(env, key, normalized)
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

    def search_messages_by_recipient_and_topic(self, **kwargs):
        return self._call_inner_tool('search_messages_by_recipient_and_topic', kwargs)

    def get_recent_messages_for_user(self, **kwargs):
        return self._call_inner_tool('get_recent_messages_for_user', kwargs)

    def get_unread_messages_for_user(self, **kwargs):
        return self._call_inner_tool('get_unread_messages_for_user', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def get_message_thread_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_thread_by_id', kwargs)

    def list_threads_for_user(self, **kwargs):
        return self._call_inner_tool('list_threads_for_user', kwargs)

    def search_threads_by_topic(self, **kwargs):
        return self._call_inner_tool('search_threads_by_topic', kwargs)

    def get_message_delivery_status(self, **kwargs):
        return self._call_inner_tool('get_message_delivery_status', kwargs)

    def get_message_read_status(self, **kwargs):
        return self._call_inner_tool('get_message_read_status', kwargs)

    def get_messages_in_thread(self, **kwargs):
        return self._call_inner_tool('get_messages_in_thread', kwargs)

    def send_direct_message(self, **kwargs):
        return self._call_inner_tool('send_direct_message', kwargs)

    def update_message_read_status(self, **kwargs):
        return self._call_inner_tool('update_message_read_status', kwargs)

    def update_message_delivery_status(self, **kwargs):
        return self._call_inner_tool('update_message_delivery_status', kwargs)

    def assign_topic_tag_to_thread(self, **kwargs):
        return self._call_inner_tool('assign_topic_tag_to_thread', kwargs)

    def delete_message_for_user(self, **kwargs):
        return self._call_inner_tool('delete_message_for_user', kwargs)

    def delete_user_account(self, **kwargs):
        return self._call_inner_tool('delete_user_account', kwargs)
