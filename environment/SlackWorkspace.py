# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import time
import uuid
from typing import List, Dict, Any
from typing import Optional, Dict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    display_name: str
    email: str
    status: str
    rol: str

class ChannelInfo(TypedDict):
    channel_id: str
    name: str
    topic: str
    is_private: bool
    member_user_id: List[str]  # List of user IDs

class MessageInfo(TypedDict):
    message_id: str
    channel_id: str
    sender_user_id: str
    timestamp: str
    content: str
    attachments: List[str]  # List of attachment IDs
    edited_timestamp: str
    deleted: bool

class AttachmentInfo(TypedDict):
    attachment_id: str
    message_id: str
    file_type: str
    file_url: str
    metadata: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Channels: {channel_id: ChannelInfo}
        self.channels: Dict[str, ChannelInfo] = {}
        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}
        # Attachments: {attachment_id: AttachmentInfo}
        self.attachments: Dict[str, AttachmentInfo] = {}

        # Constraints:
        # - Only channel members may send messages in a channel.
        # - Messages can be edited or deleted only by their sender or users with appropriate roles (e.g., admins).
        # - Channel privacy (is_private) restricts visibility and membership.
        # - Message IDs and timestamps are unique and ordered for retrieval and display.

    def get_channel_by_name(self, name: str) -> dict:
        """
        Retrieve full channel details by channel name.

        Args:
            name (str): The name of the channel to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ChannelInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., not found)
            }

        Constraints:
            - Channel names are assumed to be unique.
            - No privacy or membership check is performed.
        """
        for channel in self.channels.values():
            if channel["name"] == name:
                return { "success": True, "data": channel }
        return { "success": False, "error": f"Channel with name '{name}' does not exist." }

    def get_channel_info(self, channel_id: str) -> dict:
        """
        Retrieve the full information for a channel by its channel_id.

        Args:
            channel_id (str): Unique identifier of the channel.

        Returns:
            dict:
              - If channel exists:
                {
                    "success": True,
                    "data": ChannelInfo  # Complete info about the channel
                }
              - If not found:
                {
                    "success": False,
                    "error": "Channel not found"
                }

        Constraints:
            - Checks only for existence of the channel with given channel_id.
        """
        channel = self.channels.get(channel_id)
        if not channel:
            return {"success": False, "error": "Channel not found"}
        return {"success": True, "data": channel}

    def is_user_channel_member(self, user_id: str, channel_id: str) -> dict:
        """
        Check if a user is a member of a specific Slack channel.

        Args:
            user_id (str): The user ID to check.
            channel_id (str): The channel ID to check.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": bool }  # True if member, False if not
                On failure (user or channel does not exist):
                    { "success": False, "error": "<error message>" }

        Constraints:
            - Both user and channel must exist.
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        channel_info = self.channels[channel_id]
        is_member = user_id in channel_info["member_user_id"]
        return { "success": True, "data": is_member }

    def get_channel_members(self, channel_id: str) -> dict:
        """
        List all user IDs of members in the specified channel.

        Args:
            channel_id (str): The unique identifier for the Slack channel.

        Returns:
            dict: {
                "success": True,
                "data": List[str],      # List of member user IDs (may be empty)
            } 
            or 
            {
                "success": False,
                "error": str            # Error message if channel does not exist
            }

        Constraints:
            - The specified channel must exist in the workspace.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return { "success": False, "error": "Channel not found" }
        return { "success": True, "data": list(channel.get("member_user_id", [])) }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve details for the specified user given their user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                If user exists:
                    { "success": True, "data": UserInfo }
                If not found:
                    { "success": False, "error": "User not found" }

        Constraints:
            - user_id must exist in the workspace.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user details via exact username (not display_name).

        Args:
            name (str): The username (not display name) to search for.

        Returns:
            dict:
                On success:
                    { "success": True, "data": UserInfo }
                On failure:
                    { "success": False, "error": "User not found" }
        Constraints:
            - Performs an exact match on the 'name' field.
            - If more than one user has the same name (unexpected), returns the first found.
        """
        for user_info in self.users.values():
            if user_info["name"] == name:
                return { "success": True, "data": user_info }
        return { "success": False, "error": "User not found" }

    def get_channel_messages(self, channel_id: str, order: str = "asc") -> dict:
        """
        List all (non-deleted) messages in a specific channel, ordered by timestamp.

        Args:
            channel_id (str): The unique identifier of the channel.
            order (str, optional): 'asc' (default) for ascending timestamp order, 
                                   'desc' for descending.

        Returns:
            dict: 
                On success:
                { "success": True, "data": List[MessageInfo] }
                On error:
                { "success": False, "error": "Channel does not exist" }
    
        Constraints:
            - The channel must exist.
            - Only non-deleted messages are listed.
            - Messages are ordered by their timestamp.
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }

        filtered_messages = [
            msg for msg in self.messages.values()
            if msg["channel_id"] == channel_id and not msg.get("deleted", False)
        ]

        # Sort by timestamp (assuming timestamp is a string-comparable value)
        try:
            sorted_messages = sorted(
                filtered_messages,
                key=lambda msg: msg["timestamp"],
                reverse=(order == "desc")
            )
        except Exception as e:
            # Fallback to unsorted if there is an error in sorting (rare)
            sorted_messages = filtered_messages

        return { "success": True, "data": sorted_messages }

    def get_message_by_id(self, message_id: str) -> dict:
        """
        Retrieve the full details of a specific message by its message_id.

        Args:
            message_id (str): The unique identifier for the message.

        Returns:
            dict: {
                "success": True,
                "data": MessageInfo   # If message is found
            }
            or
            {
                "success": False,
                "error": "Message not found"  # If no such message exists
            }

        Constraints:
            - No permissions are checked; any message may be queried by ID.
        """
        message = self.messages.get(message_id)
        if not message:
            return {"success": False, "error": "Message not found"}
        return {"success": True, "data": message}

    def get_attachment_by_id(self, attachment_id: str) -> dict:
        """
        Retrieve information for a given attachment by its attachment_id.

        Args:
            attachment_id (str): The unique ID of the attachment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AttachmentInfo  # The attachment metadata.
                    }
                On failure (attachment not found):
                    {
                        "success": False,
                        "error": "Attachment not found"
                    }
        """
        if attachment_id not in self.attachments:
            return {"success": False, "error": "Attachment not found"}
        return {"success": True, "data": self.attachments[attachment_id]}

    def list_channel_names(self) -> dict:
        """
        Retrieve the names of all channels in the workspace.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of channel names. May be empty if no channels exist.
            }

        Constraints:
            - No input required.
            - No special permissions required.
        """
        channel_names = [channel_info["name"] for channel_info in self.channels.values()]
        return {"success": True, "data": channel_names}

    def send_message(
        self,
        channel_id: str,
        sender_user_id: str,
        content: str,
        attachments: List[str] = None
    ) -> dict:
        """
        Post a new message to a channel as a user.

        Args:
            channel_id (str): ID of the target channel.
            sender_user_id (str): ID of the user posting.
            content (str): Message text.
            attachments (List[str], optional): List of valid attachment IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Message posted",
                "message_id": str,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Channel and user must exist.
            - User must be a member of the channel.
            - Attachments must exist if provided.
            - At least one of content or attachments must be non-empty.
        """

        if channel_id not in self.channels:
            return {"success": False, "error": "Channel does not exist"}
        if sender_user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        channel = self.channels[channel_id]
        if sender_user_id not in channel['member_user_id']:
            return {"success": False, "error": "User is not a member of the channel"}

        # Default to empty list if attachments is None
        if attachments is None:
            attachments = []

        # Validate attachments
        for att_id in attachments:
            if att_id not in self.attachments:
                return {"success": False, "error": f"Attachment {att_id} does not exist"}

        # At least one of content or attachments must not be empty
        if not content and not attachments:
            return {"success": False, "error": "Cannot send empty message without attachments"}

        # Generate unique message id and timestamp
        message_id = str(uuid.uuid4())
        timestamp = str(time.time())
    
        # MessageInfo
        message_info = {
            "message_id": message_id,
            "channel_id": channel_id,
            "sender_user_id": sender_user_id,
            "timestamp": timestamp,
            "content": content,
            "attachments": attachments,
            "edited_timestamp": "",
            "deleted": False
        }

        self.messages[message_id] = message_info

        # Associate attachments with this message
        for att_id in attachments:
            self.attachments[att_id]['message_id'] = message_id

        return {
            "success": True,
            "message": "Message posted",
            "message_id": message_id
        }

    def edit_message(self, message_id: str, editor_user_id: str, new_content: str, edited_timestamp: str) -> dict:
        """
        Edit an existing message's content and edited_timestamp.

        Args:
            message_id (str): The message to edit.
            editor_user_id (str): The user attempting the edit.
            new_content (str): New text content for the message.
            edited_timestamp (str): Timestamp for the edit operation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Message edited successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Only the sender of the message or admin users may edit the message.
            - Editing a deleted message is not allowed.
        """
        # Check that message exists
        message = self.messages.get(message_id)
        if not message:
            return { "success": False, "error": "Message does not exist." }

        # Check that user exists
        user = self.users.get(editor_user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        # Check if deleted
        if message.get("deleted", False):
            return { "success": False, "error": "Cannot edit a deleted message." }

        # Permission check: sender or admin
        is_sender = (editor_user_id == message["sender_user_id"])
        is_admin = (user.get("rol") == "admin")
        if not (is_sender or is_admin):
            return { "success": False, "error": "Permission denied to edit this message." }

        # Perform the edit
        message["content"] = new_content
        message["edited_timestamp"] = edited_timestamp

        return { "success": True, "message": "Message edited successfully." }

    def delete_message(self, message_id: str, user_id: str) -> dict:
        """
        Mark a message as deleted (soft delete) if requested by its sender or by an admin.

        Args:
            message_id (str): The ID of the message to delete.
            user_id (str): The ID of the user requesting the delete.

        Returns:
            dict: {
                "success": True,
                "message": "Message marked as deleted."
            }
            or
            {
                "success": False,
                "error": "Error description"
            }

        Constraints:
            - Only the sender of the message or users with 'admin' role may delete the message.
            - If the message does not exist or is already deleted, return an appropriate error.
        """
        # Check message exists
        message = self.messages.get(message_id)
        if not message:
            return {"success": False, "error": "Message not found"}

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Check already deleted
        if message.get("deleted", False):
            return {"success": False, "error": "Message already deleted"}

        # Authorization check (sender or admin)
        if user["_id"] != message["sender_user_id"] and user.get("rol", "").lower() != "admin":
            return {"success": False, "error": "Permission denied: only sender or admin may delete message"}

        # Perform soft delete
        message["deleted"] = True

        return {"success": True, "message": "Message marked as deleted."}

    def add_user_to_channel(self, user_id: str, channel_id: str) -> dict:
        """
        Adds the specified user to the member list of the specified channel,
        following channel membership and privacy constraints.

        Args:
            user_id (str): The user ID of the user to add.
            channel_id (str): The channel ID to which the user is to be added.

        Returns:
            dict:
                If successful:
                    { "success": True, "message": "User <user_id> added to channel <channel_id>" }
                If failed:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Both user and channel must exist.
            - User must not already be a member of the channel.
            - Channel privacy may restrict admission, but without a requesting user/role,
              only membership and existence checks are enforced.
        """
        # Check if channel exists
        channel = self.channels.get(channel_id)
        if channel is None:
            return { "success": False, "error": "Channel does not exist" }
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        # Check if user is already a member
        if user_id in channel["member_user_id"]:
            return { "success": False, "error": "User is already a member of the channel" }

        # Add the user to the channel member list
        channel["member_user_id"].append(user_id)
        # Normally you may want to update self.channels[channel_id]; in-place modification suffices here

        return {
            "success": True,
            "message": f"User {user_id} added to channel {channel_id}"
        }

    def remove_user_from_channel(self, channel_id: str, user_id: str) -> dict:
        """
        Remove a user from a channel's membership list.

        Args:
            channel_id (str): The ID of the channel.
            user_id (str): The ID of the user to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "User <user_id> removed from channel <channel_id>." }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - The channel must exist.
            - The user must exist.
            - The user must currently be a member of the channel.
        """
        # Check if channel exists
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist." }
    
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        channel = self.channels[channel_id]
        members = channel["member_user_id"]

        if user_id not in members:
            return { "success": False, "error": "User is not a member of the channel." }

        # Remove user
        channel["member_user_id"] = [uid for uid in members if uid != user_id]
        self.channels[channel_id] = channel

        return {
            "success": True,
            "message": f"User {user_id} removed from channel {channel_id}."
        }


    def create_channel(self, name: str, topic: str, is_private: bool, member_user_ids: List[str]) -> dict:
        """
        Create a new channel in the workspace with the given name, topic, privacy setting, and members.

        Args:
            name (str): The channel's display name (must be unique).
            topic (str): Description or topic for the channel.
            is_private (bool): If True, channel is private.
            member_user_ids (List[str]): List of user IDs to be added as members.

        Returns:
            dict:
                On success: { "success": True, "message": "Channel created with channel_id <id>" }
                On failure: { "success": False, "error": "<description>" }

        Constraints:
            - Channel name must be unique.
            - All user IDs in member_user_ids must exist in workspace.
        """
        # Check for uniqueness of channel name
        for ch in self.channels.values():
            if ch["name"].lower() == name.lower():
                return {"success": False, "error": "Channel name already exists."}

        # Validate all user IDs
        invalid_users = [uid for uid in member_user_ids if uid not in self.users]
        if invalid_users:
            return {"success": False, "error": f"Invalid user IDs: {', '.join(invalid_users)}"}

        # Generate unique channel_id
        channel_id = str(uuid.uuid4())

        channel_info: ChannelInfo = {
            "channel_id": channel_id,
            "name": name,
            "topic": topic,
            "is_private": is_private,
            "member_user_id": list(member_user_ids),  # copy to avoid external mutations
        }

        self.channels[channel_id] = channel_info

        return {"success": True, "message": f"Channel created with channel_id {channel_id}"}


    def upload_attachment(
        self, 
        file_type: str, 
        file_url: str, 
        metadata: Dict[str, Any], 
        message_id: Optional[str] = None
    ) -> dict:
        """
        Add an attachment (file or rich media) to the workspace for later association with a message.

        Args:
            file_type (str): The type of the file (e.g., 'image', 'pdf', 'video').
            file_url (str): The URL or path to the file.
            metadata (dict): Additional metadata about the attachment.
            message_id (str, optional): The ID of the message to associate with, or None.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Attachment uploaded",
                    "attachment_id": <new_attachment_id>
                }
                On failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - file_type and file_url must be non-empty strings.
            - metadata must be a dict.
            - If message_id is provided, it must reference an existing message.

        """
        # Validate input
        if not isinstance(file_type, str) or not file_type.strip():
            return {"success": False, "error": "Invalid file_type"}
        if not isinstance(file_url, str) or not file_url.strip():
            return {"success": False, "error": "Invalid file_url"}
        if not isinstance(metadata, dict):
            return {"success": False, "error": "metadata must be a dict"}
        if message_id is not None and message_id not in self.messages:
            return {"success": False, "error": "message_id does not exist"}

        # Generate unique attachment_id
        attachment_id = str(uuid.uuid4())
        while attachment_id in self.attachments:
            attachment_id = str(uuid.uuid4())

        # Construct new AttachmentInfo
        attachment_record = {
            "attachment_id": attachment_id,
            "message_id": message_id if message_id else "",
            "file_type": file_type,
            "file_url": file_url,
            "metadata": metadata
        }

        self.attachments[attachment_id] = attachment_record

        # Optionally, if message_id is provided, append to that message's attachments
        if message_id:
            if "attachments" in self.messages[message_id]:
                attachments_list = self.messages[message_id]["attachments"]
                if attachment_id not in attachments_list:
                    attachments_list.append(attachment_id)
            else:
                self.messages[message_id]["attachments"] = [attachment_id]

        return {
            "success": True,
            "message": "Attachment uploaded",
            "attachment_id": attachment_id
        }

    def associate_attachment_to_message(self, attachment_id: str, message_id: str) -> dict:
        """
        Link an existing attachment to a designated message.

        Args:
            attachment_id (str): The ID of the attachment to link.
            message_id (str): The ID of the message to link the attachment to.

        Returns:
            dict: {
                "success": True,
                "message": "Attachment associated with message."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (attachment/message not found, already associated, etc.)
            }

        Constraints:
            - Both message and attachment must exist.
            - Attachment can only be associated with one message at a time.
            - No duplicate attachment IDs in a message's attachments list.
        """
        # Check existence of message
        if message_id not in self.messages:
            return { "success": False, "error": "Message does not exist." }

        # Check existence of attachment
        if attachment_id not in self.attachments:
            return { "success": False, "error": "Attachment does not exist." }

        message = self.messages[message_id]
        attachment = self.attachments[attachment_id]

        # Check if attachment is already associated with a different message
        if attachment['message_id'] and attachment['message_id'] != message_id:
            return {
                "success": False,
                "error": f"Attachment already associated with another message (message_id: {attachment['message_id']})."
            }

        # Link attachment to message if not already present
        if attachment_id not in message['attachments']:
            message['attachments'].append(attachment_id)
        # Update the attachment's message_id field
        attachment['message_id'] = message_id

        return { "success": True, "message": "Attachment associated with message." }

    def change_channel_privacy(self, channel_id: str, is_private: bool) -> dict:
        """
        Set the privacy flag (public/private) for a specific channel.

        Args:
            channel_id (str): The ID of the channel to update.
            is_private (bool): The desired privacy setting (True for private, False for public).

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Channel privacy set to <public/private> for channel <channel_id>"
                }
                On failure,
                {
                    "success": False,
                    "error": "Channel does not exist"
                }

        Constraints:
            - Channel must exist in the workspace.
            - This operation does not check user permissions (admin/owner) as per operation description.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return {"success": False, "error": "Channel does not exist"}

        channel["is_private"] = is_private
        privacy_str = "private" if is_private else "public"
        return {
            "success": True,
            "message": f"Channel privacy set to {privacy_str} for channel {channel_id}"
        }

    def rename_channel(self, channel_id: str, new_name: str) -> dict:
        """
        Change the name of a channel.

        Args:
            channel_id (str): The identifier of the channel to be renamed.
            new_name (str): The intended new unique channel name.

        Returns:
            dict: {
                "success": True,
                "message": str  # e.g., "Channel renamed to <new_name>"
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., channel does not exist, name taken)
            }

        Constraints:
            - Channel must exist.
            - New name must be non-empty and unique among all channels.
        """
        if not new_name or not new_name.strip():
            return {"success": False, "error": "New channel name cannot be empty"}

        if channel_id not in self.channels:
            return {"success": False, "error": "Channel does not exist"}

        new_name = new_name.strip()
        # Check for uniqueness (case insensitive, for robustness)
        for cid, info in self.channels.items():
            if info["name"].lower() == new_name.lower() and cid != channel_id:
                return {"success": False, "error": "Channel name already in use"}

        # All checks passed, perform rename
        self.channels[channel_id]["name"] = new_name
        return {"success": True, "message": f"Channel renamed to {new_name}"}


class SlackWorkspace(BaseEnv):
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

    def get_channel_by_name(self, **kwargs):
        return self._call_inner_tool('get_channel_by_name', kwargs)

    def get_channel_info(self, **kwargs):
        return self._call_inner_tool('get_channel_info', kwargs)

    def is_user_channel_member(self, **kwargs):
        return self._call_inner_tool('is_user_channel_member', kwargs)

    def get_channel_members(self, **kwargs):
        return self._call_inner_tool('get_channel_members', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_channel_messages(self, **kwargs):
        return self._call_inner_tool('get_channel_messages', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def get_attachment_by_id(self, **kwargs):
        return self._call_inner_tool('get_attachment_by_id', kwargs)

    def list_channel_names(self, **kwargs):
        return self._call_inner_tool('list_channel_names', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def edit_message(self, **kwargs):
        return self._call_inner_tool('edit_message', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def add_user_to_channel(self, **kwargs):
        return self._call_inner_tool('add_user_to_channel', kwargs)

    def remove_user_from_channel(self, **kwargs):
        return self._call_inner_tool('remove_user_from_channel', kwargs)

    def create_channel(self, **kwargs):
        return self._call_inner_tool('create_channel', kwargs)

    def upload_attachment(self, **kwargs):
        return self._call_inner_tool('upload_attachment', kwargs)

    def associate_attachment_to_message(self, **kwargs):
        return self._call_inner_tool('associate_attachment_to_message', kwargs)

    def change_channel_privacy(self, **kwargs):
        return self._call_inner_tool('change_channel_privacy', kwargs)

    def rename_channel(self, **kwargs):
        return self._call_inner_tool('rename_channel', kwargs)

