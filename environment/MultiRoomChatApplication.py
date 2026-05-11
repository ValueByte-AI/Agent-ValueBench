# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import time
import uuid
from typing import Optional, Dict



# User state: maps to User entity/attributes
class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    account_status: str        # e.g., 'active', 'suspended', 'banned'
    joined_room: List[str]     # List of room_ids

# ChatRoom state: maps to ChatRoom entity/attributes
class ChatRoomInfo(TypedDict):
    room_id: str
    room_name: str
    topic: str
    room_members: List[str]    # List of user _ids
    access_level: str          # e.g., 'public', 'private', 'invite-only'

# RoomMembership state: maps to RoomMembership entity/attributes
class RoomMembershipInfo(TypedDict):
    _id: str                   # user id
    room_id: str
    membership_status: str     # e.g., 'active', 'left', 'banned'
    join_timestamp: Union[str, float]
    role_in_room: str          # e.g., 'member', 'moderator'

# Message state: maps to Message entity/attributes
class MessageInfo(TypedDict):
    message_id: str
    room_id: str
    sender_id: str
    content: str
    timestamp: Union[str, float]
    message_type: str          # e.g., 'text', 'system'
    sta: str                   # status ('delivered', 'edited', 'deleted', etc.)

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Multi-room chat application state.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Chat rooms: {room_id: ChatRoomInfo}
        self.chat_rooms: Dict[str, ChatRoomInfo] = {}

        # Room memberships: {(_id, room_id): RoomMembershipInfo}
        # Alternate structure: room_memberships_by_user: {_id: List[RoomMembershipInfo]}
        self.room_memberships: Dict[str, Dict[str, RoomMembershipInfo]] = {}
        # Maps _id -> {room_id: RoomMembershipInfo}

        # Message histories: {room_id: List[MessageInfo]}
        self.messages: Dict[str, List[MessageInfo]] = {}

        # Constraints:
        # - Only users who are members of a room may send/read messages from that room.
        # - Message history for each room is persistent and retrievable based on access controls.
        # - Room access (public/private/invite-only) may restrict membership and message visibility.
        # - User account must be 'active' to send messages.

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user information given a user ID.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # The user's info if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - No access control; all fields are returned if user exists.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information given a username.

        Args:
            username (str): The username to query.

        Returns:
            dict: 
                { "success": True, "data": UserInfo } if username exists,
                { "success": False, "error": "User not found" } otherwise.

        Constraints:
            - None specific for this query (does not involve permissions or state modification).
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_user_account_status(self, _id: str) -> dict:
        """
        Query the account status (e.g., active, suspended, banned) for a user.

        Args:
            _id (str): The user's unique identifier.

        Returns:
            dict: 
                On success: { "success": True, "data": str }  # account_status
                On failure: { "success": False, "error": str }  # e.g., user not found

        Constraints:
            - The user must exist in the application state.
            - No special permission is required to query status.
        """
        user = self.users.get(_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user["account_status"] }

    def list_joined_rooms(self, user_id: str) -> dict:
        """
        Retrieve the list of chat room IDs a user has joined.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[str]   # List of joined room_ids, empty if none
            }
            or
            {
                "success": False,
                "error": str  # Error reason, e.g., user not found
            }

        Constraints:
            - user_id must correspond to an existing user in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        joined_rooms = user.get("joined_room", [])
        return { "success": True, "data": joined_rooms }

    def get_room_by_id(self, room_id: str) -> dict:
        """
        Fetch metadata for a chat room by room_id.

        Args:
            room_id (str): The unique identifier of the chat room.

        Returns:
            dict: 
              On success:
                {
                    "success": True,
                    "data": {
                        "room_id": str,
                        "room_name": str,
                        "topic": str,
                        "access_level": str,
                        "room_members": List[str]
                    }
                }
              On failure:
                {
                    "success": False,
                    "error": "Room not found"
                }

        Constraints:
            - The room must exist in self.chat_rooms.
            - No permissions are required for this metadata query.
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Room not found" }
    
        data = {
            "room_id": room["room_id"],
            "room_name": room["room_name"],
            "topic": room["topic"],
            "access_level": room["access_level"],
            "room_members": room["room_members"]
        }
        return { "success": True, "data": data }

    def get_room_by_name(self, room_name: str) -> dict:
        """
        Fetch chat room metadata (ChatRoomInfo) by room name.

        Args:
            room_name (str): The name of the chat room to fetch.

        Returns:
            dict:
                {
                    "success": True,
                    "data": ChatRoomInfo,   # Metadata for the room
                }
                or
                {
                    "success": False,
                    "error": str  # "Room not found" if not found
                }

        Notes:
            - Room names are assumed to be unique.
            - No access or membership checks are performed.

        Edge Cases:
            - If room name does not exist, return error.
        """
        for room_info in self.chat_rooms.values():
            if room_info["room_name"] == room_name:
                return { "success": True, "data": room_info }
        return { "success": False, "error": "Room not found" }

    def get_room_access_level(self, room_id: str) -> dict:
        """
        Retrieve the access control level (public/private/invite-only) for a given room.

        Args:
            room_id (str): The unique identifier for the chat room.

        Returns:
            dict: 
                If successful:
                    { "success": True, "data": access_level (str) }
                If room does not exist:
                    { "success": False, "error": "Room not found" }
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Room not found" }
        return { "success": True, "data": room["access_level"] }

    def list_room_members(self, room_id: str) -> dict:
        """
        Retrieve the list of user IDs who are current members of the specified chat room.

        Args:
            room_id (str): The unique identifier of the chat room.

        Returns:
            dict:
                success: True and data is a List[str] of user IDs if the room exists.
                success: False and error is a string if the room does not exist.

        Constraints:
            - The room must exist.
            - The output list may be empty if the room has no members.
        """
        room_info = self.chat_rooms.get(room_id)
        if not room_info:
            return {"success": False, "error": "Room does not exist"}

        return {"success": True, "data": list(room_info["room_members"])}

    def get_room_membership_status(self, _id: str, room_id: str) -> dict:
        """
        Retrieve the room membership status and role for a specific user in a specific room.

        Args:
            _id (str): The user id.
            room_id (str): The chat room id.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "membership_status": str,
                            "role_in_room": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of the error (user/room/membership not found)
                    }

        Constraints:
            - Both user and room must exist.
            - Membership info must exist for the given user and room.
        """
        # Check if user exists
        if _id not in self.users:
            return {"success": False, "error": "User not found"}
        # Check if room exists
        if room_id not in self.chat_rooms:
            return {"success": False, "error": "Room not found"}
        # Check if membership exists
        user_memberships = self.room_memberships.get(_id)
        if not user_memberships or room_id not in user_memberships:
            return {"success": False, "error": "Membership not found for this user in the specified room"}
        membership_info = user_memberships[room_id]

        return {
            "success": True,
            "data": {
                "membership_status": membership_info["membership_status"],
                "role_in_room": membership_info["role_in_room"]
            }
        }

    def fetch_room_message_history(self, room_id: str, user_id: str) -> dict:
        """
        Retrieve the message history for a given chat room if the requesting user is allowed by membership and access control.
    
        Args:
            room_id (str): The id of the chat room.
            user_id (str): The id of the requesting user.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only users who are members (with 'active' status) of a room may read messages from that room,
              subject to access control.
            - Returns all delivered/visible messages in the room.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        # Check room exists
        if room_id not in self.chat_rooms:
            return { "success": False, "error": "Room does not exist" }

        # Check user membership in the room
        user_room_memberships = self.room_memberships.get(user_id, {})
        membership = user_room_memberships.get(room_id)
        if not membership or membership["membership_status"] != "active":
            return { "success": False, "error": "Access denied: user is not an active member of the room" }

        # Fetch and return messages (visible only)
        messages = self.messages.get(room_id, [])
        # Optionally filter for delivered/visible messages
        visible_messages = [
            m for m in messages if m.get("sta", "") != "deleted"
        ]
        return { "success": True, "data": visible_messages }

    def get_message_by_id(self, message_id: str) -> dict:
        """
        Fetch the content and metadata of a specific message using message_id.

        Args:
            message_id (str): The unique identifier of the message.

        Returns:
            dict:
                - If found: { "success": True, "data": MessageInfo }
                - If not found: { "success": False, "error": "Message not found" }

        Constraints:
            - Assumes message_id is unique across all rooms.
            - No access/membership control enforced in this operation.
        """
        for room_msgs in self.messages.values():
            for msg in room_msgs:
                if msg["message_id"] == message_id:
                    return { "success": True, "data": msg }
        return { "success": False, "error": "Message not found" }

    def list_user_room_memberships(self, user_id: str) -> dict:
        """
        List all RoomMembershipInfo objects for the user (including current and historical).

        Args:
            user_id (str): The user id (_id) whose memberships to list.

        Returns:
            dict: {
                "success": True,
                "data": List[RoomMembershipInfo],  # May be empty if no memberships
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., user not found
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        memberships = []
        if user_id in self.room_memberships:
            memberships = list(self.room_memberships[user_id].values())

        return {"success": True, "data": memberships}


    def send_message(
        self,
        sender_id: str,
        room_id: str,
        content: str,
        message_type: Optional[str] = "text"
    ) -> dict:
        """
        Post a new message from a user to the specified chat room if constraints allow.

        Args:
            sender_id (str): The unique user ID of the sender.
            room_id (str): The unique room ID for the chat room.
            content (str): The content/text of the message.
            message_type (str, optional): The type of message (default: "text").

        Returns:
            dict: {
                "success": True,
                "message": "Message sent",
                "message_id": str  # The unique ID for the created message
            }
            or
            {
                "success": False,
                "error": str  # Explanation of why the message could not be sent
            }

        Constraints:
            - Only users with 'active' account status can send messages.
            - Only users who are active members of the destination room may post.
            - The room and user must exist.
        """
        # Check if sender exists
        user = self.users.get(sender_id)
        if not user:
            return { "success": False, "error": "Sender does not exist" }

        # Check user account status
        if user["account_status"] != "active":
            return { "success": False, "error": "User account is not active" }

        # Check room exists
        room = self.chat_rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Room does not exist" }

        # Check sender has membership in the room
        membership = (
            self.room_memberships.get(sender_id, {}).get(room_id)
            if sender_id in self.room_memberships else None
        )
        if not membership or membership["membership_status"] != "active":
            return { "success": False, "error": "User is not an active member of this room" }

        # All checks passed - create message
        new_message_id = str(uuid.uuid4())
        timestamp = time.time()

        message_info = {
            "message_id": new_message_id,
            "room_id": room_id,
            "sender_id": sender_id,
            "content": content,
            "timestamp": timestamp,
            "message_type": message_type or "text",
            "sta": "delivered"
        }

        if room_id not in self.messages:
            self.messages[room_id] = []
        self.messages[room_id].append(message_info)

        return {
            "success": True,
            "message": "Message sent",
            "message_id": new_message_id
        }

    def join_room(self, user_id: str, room_id: str) -> dict:
        """
        Add a user to a room. Creates or updates an active RoomMembershipInfo for the user-room pair,
        adds user to room's member list, and records membership in the user's joined_room list.

        Args:
            user_id (str): The user's unique identifier.
            room_id (str): The chat room's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> joined room <room_id>."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist and be 'active'.
            - Room must exist.
            - Cannot join invite-only rooms without invite (not handled here).
            - User must not already be an active member.
        """

        # 1. User and Room existence checks
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        room = self.chat_rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Room does not exist." }

        # 2. User account must be active
        if user["account_status"] != "active":
            return { "success": False, "error": "User account is not active." }

        # 3. Room access policy
        if room.get("access_level") == "invite-only":
            return { "success": False, "error": "Cannot join invite-only room without invite." }

        # 4. User must not already be an active member
        # Check in room_memberships structure
        membership = self.room_memberships.get(user_id, {}).get(room_id)
        if membership and membership.get("membership_status") == "active":
            return { "success": False, "error": "User is already an active member of this room." }

        # 5. Perform membership addition
        # 5.1 - Add to room_members list if not present
        if user_id not in room["room_members"]:
            room["room_members"].append(user_id)
            self.chat_rooms[room_id] = room

        # 5.2 - Add to user's joined_room list if not present
        if room_id not in user["joined_room"]:
            user["joined_room"].append(room_id)
            self.users[user_id] = user

        # 5.3 - Add/update RoomMembershipInfo
        join_timestamp = time.time()
        room_membership_info = {
            "_id": user_id,
            "room_id": room_id,
            "membership_status": "active",
            "join_timestamp": join_timestamp,
            "role_in_room": "member"
        }
        if user_id not in self.room_memberships:
            self.room_memberships[user_id] = {}
        self.room_memberships[user_id][room_id] = room_membership_info

        return {
            "success": True,
            "message": f"User {user_id} joined room {room_id}."
        }

    def leave_room(self, user_id: str, room_id: str) -> dict:
        """
        Remove a user from a chat room.
        Updates RoomMembershipInfo (membership_status -> 'left'), removes user from room_members (ChatRoomInfo),
        and removes the room from the user's joined_room list (UserInfo).

        Args:
            user_id (str): The ID of the user leaving the room.
            room_id (str): The ID of the room to leave.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "User <user_id> has left room <room_id>"
                }
                On failure:
                {
                    "success": False,
                    "error": "<error_message>"
                }

        Constraints:
            - The user and room must exist.
            - The user must currently be a member of the room.
            - RoomMembershipInfo for (user_id, room_id) must exist.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": f"User not found: {user_id}"}
        # Check room existence
        if room_id not in self.chat_rooms:
            return {"success": False, "error": f"Room not found: {room_id}"}
        # Check membership info
        if user_id not in self.room_memberships or room_id not in self.room_memberships[user_id]:
            return {"success": False, "error": f"User is not a member of the room."}
        room_membership = self.room_memberships[user_id][room_id]
        if room_membership.get("membership_status") != "active":
            return {"success": False, "error": f"User is not an active member of the room."}
        # Remove user from chat room's member list
        if user_id in self.chat_rooms[room_id]['room_members']:
            self.chat_rooms[room_id]['room_members'].remove(user_id)
        # Remove room from user's joined_room list
        if room_id in self.users[user_id]['joined_room']:
            self.users[user_id]['joined_room'].remove(room_id)
        # Update membership status
        room_membership['membership_status'] = "left"
        return {"success": True, "message": f"User {user_id} has left room {room_id}"}

    def edit_message(self, message_id: str, editor_id: str, new_content: str) -> dict:
        """
        Modify the content of an existing message (if allowed).

        Args:
            message_id (str): Identifier of the message to edit.
            editor_id (str): User ID attempting the edit.
            new_content (str): The new content for the message.

        Returns:
            dict: {
                "success": True,
                "message": "Message edited successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only the sender (editor_id == sender_id) may edit a message.
            - Editor's account_status must be 'active'.
            - Editor must be an 'active' member of the room (membership_status == 'active').
            - Message must exist and be editable ('sta' not 'deleted').
        """
        # Find message
        target_msg = None
        found_room_id = None
        for room_id, msg_list in self.messages.items():
            for idx, msg in enumerate(msg_list):
                if msg["message_id"] == message_id:
                    target_msg = msg
                    found_room_id = room_id
                    msg_index = idx
                    break
            if target_msg:
                break

        if not target_msg:
            return {"success": False, "error": "Message not found."}

        # Check if user exists
        if editor_id not in self.users:
            return {"success": False, "error": "Editor user does not exist."}
        editor = self.users[editor_id]

        # Check editor's account status
        if editor["account_status"] != "active":
            return {"success": False, "error": "Editor account is not active."}

        # Editor must be sender
        if editor_id != target_msg["sender_id"]:
            return {"success": False, "error": "Only the sender can edit the message."}

        room_id = target_msg["room_id"]
        # Check editor's room membership and status
        if (editor_id not in self.room_memberships or
            room_id not in self.room_memberships[editor_id]):
            return {"success": False, "error": "Editor is not a member of the room."}
        membership = self.room_memberships[editor_id][room_id]
        if membership["membership_status"] != "active":
            return {"success": False, "error": "Editor is not an active member of the room."}

        # Disallow edits to deleted messages (or possibly other sta values)
        if target_msg["sta"] == "deleted":
            return {"success": False, "error": "Cannot edit a deleted message."}

        # Update content and status
        self.messages[room_id][msg_index]["content"] = new_content
        self.messages[room_id][msg_index]["sta"] = "edited"
        # Optionally, update timestamp (not required, but common for edit audit trail)
        self.messages[room_id][msg_index]["timestamp"] = time.time()

        return {"success": True, "message": "Message edited successfully."}

    def delete_message(self, user_id: str, message_id: str) -> dict:
        """
        Logically delete a message by setting its 'sta' attribute to 'deleted'.

        Args:
            user_id (str): The ID of the user attempting the delete operation.
            message_id (str): The ID of the message to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Message deleted"
            }
            or
            {
                "success": False,
                "error": str  # error details
            }
    
        Constraints:
            - The message with message_id must exist.
            - Only the sender of the message can delete it.
            - User must have 'active' account_status.
            - Mark the message's 'sta' as 'deleted'. If already 'deleted', still return success.
        """
        # Check user exists and is active
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        if user["account_status"] != "active":
            return { "success": False, "error": "User account not active" }

        # Search for message across all rooms
        found = False
        for room_id, msgs in self.messages.items():
            for msg in msgs:
                if msg["message_id"] == message_id:
                    found = True
                    if msg["sender_id"] != user_id:
                        membership = self.room_memberships.get(user_id, {}).get(room_id)
                        if not membership or membership.get("membership_status") != "active":
                            return {"success": False, "error": "User not authorized to delete this message"}
                        if membership.get("role_in_room") not in ("moderator", "admin"):
                            return {"success": False, "error": "User not authorized to delete this message"}
                    # Logical delete
                    if msg["sta"] == "deleted":
                        return { "success": True, "message": "Message deleted" }
                    msg["sta"] = "deleted"
                    return { "success": True, "message": "Message deleted" }
        if not found:
            return { "success": False, "error": "Message does not exist" }

    def update_room_membership_status(
        self, 
        _id: str, 
        room_id: str, 
        membership_status: str = None, 
        role_in_room: str = None
    ) -> dict:
        """
        Change a user's membership status or role in a chat room.

        Args:
            _id (str): User identifier whose membership is to be updated.
            room_id (str): The room's identifier.
            membership_status (str, optional): The new membership status (e.g., 'active', 'banned', 'left'). If None, not updated.
            role_in_room (str, optional): The new role in the room (e.g., 'member', 'moderator'). If None, not updated.

        Returns:
            dict: {
                "success": True,
                "message": "Membership status updated"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User and room must exist.
            - There must be an existing membership entry; otherwise error.
        """
        # Check if user exists
        if _id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check if room exists
        if room_id not in self.chat_rooms:
            return { "success": False, "error": "Room does not exist" }

        # Check if membership exists
        if _id not in self.room_memberships or room_id not in self.room_memberships[_id]:
            return { "success": False, "error": "Membership record does not exist for this user in this room" }

        membership = self.room_memberships[_id][room_id]

        # Update only the values provided
        if membership_status is not None:
            membership['membership_status'] = membership_status
        if role_in_room is not None:
            membership['role_in_room'] = role_in_room

        # Save back
        self.room_memberships[_id][room_id] = membership

        return {
            "success": True,
            "message": "Membership status updated"
        }

    def create_room(
        self,
        room_id: str,
        room_name: str,
        topic: str,
        access_level: str,
        creator_id: str,
    ) -> dict:
        """
        Create a new chat room with the specified metadata, and assign the creator as an initial member and moderator.

        Args:
            room_id (str): Unique identifier for the room.
            room_name (str): Human-readable name, must be unique.
            topic (str): (Optional) Room topic or description.
            access_level (str): Room policy: 'public', 'private', 'invite-only'.
            creator_id (str): User ID of the creator; must exist and be active.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Room created",
                    "room_id": <room_id>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - room_id and room_name must be unique among all chat rooms.
            - creator_id must be a valid, 'active' user.
            - On creation, creator is added to room_members and made active moderator.
        """
        # Check uniqueness for room_id
        if room_id in self.chat_rooms:
            return {"success": False, "error": "Room ID already exists"}

        # Check uniqueness for room_name
        if any(
            room_info["room_name"] == room_name
            for room_info in self.chat_rooms.values()
        ):
            return {"success": False, "error": "Room name already exists"}

        # Validate creator
        creator = self.users.get(creator_id)
        if creator is None:
            return {"success": False, "error": "Creator user does not exist"}
        if creator["account_status"] != "active":
            return {"success": False, "error": "Creator account is not active"}

        # Create chat room info structure
        new_room: ChatRoomInfo = {
            "room_id": room_id,
            "room_name": room_name,
            "topic": topic,
            "room_members": [creator_id],
            "access_level": access_level,
        }
        self.chat_rooms[room_id] = new_room

        # Add to creator's room list
        if room_id not in creator["joined_room"]:
            creator["joined_room"].append(room_id)

        # Create room membership as moderator
        now = time.time()
        membership_info: RoomMembershipInfo = {
            "_id": creator_id,
            "room_id": room_id,
            "membership_status": "active",
            "join_timestamp": now,
            "role_in_room": "moderator",
        }
        if creator_id not in self.room_memberships:
            self.room_memberships[creator_id] = {}
        self.room_memberships[creator_id][room_id] = membership_info

        # Initialize messages history for room
        self.messages[room_id] = []

        return {
            "success": True,
            "message": "Room created",
            "room_id": room_id,
        }

    def update_room_details(
        self, 
        room_id: str, 
        room_name: str = None, 
        topic: str = None, 
        access_level: str = None
    ) -> dict:
        """
        Update a chat room's name, topic, and/or access level.

        Args:
            room_id (str): The unique ID of the chat room to update.
            room_name (str, optional): New name for the chat room.
            topic (str, optional): New topic for the chat room.
            access_level (str, optional): New access level ('public', 'private', 'invite-only').

        Returns:
            dict: On success:
                {'success': True, 'message': 'Room details updated'}
            On error:
                {'success': False, 'error': <reason>}

        Constraints:
            - room_id must exist.
            - At least one of room_name, topic, access_level must be provided.
            - If access_level provided, must be one of allowed values.
        """
        allowed_access_levels = {'public', 'private', 'invite-only'}
        if room_id not in self.chat_rooms:
            return {"success": False, "error": "Room not found"}
        if room_name is None and topic is None and access_level is None:
            return {"success": False, "error": "No update fields provided"}
        if access_level is not None and access_level not in allowed_access_levels:
            return {
                "success": False, 
                "error": f"Invalid access_level: must be one of {allowed_access_levels}"
            }

        room = self.chat_rooms[room_id]
        changes = []
        if room_name is not None and room_name != room["room_name"]:
            room["room_name"] = room_name
            changes.append("name")
        if topic is not None and topic != room["topic"]:
            room["topic"] = topic
            changes.append("topic")
        if access_level is not None and access_level != room["access_level"]:
            room["access_level"] = access_level
            changes.append("access_level")

        if not changes:
            return {"success": True, "message": "No changes made: all provided values match current room info"}
        return {"success": True, "message": "Room details updated"}


    def add_user_to_room(self, admin_id: str, target_user_id: str, room_id: str) -> dict:
        """
        Admin/mod operation to add a user to a room, typically for invite-only/private rooms.

        Args:
            admin_id (str): ID of the admin/moderator invoking the addition.
            target_user_id (str): ID of the user to add to the room.
            room_id (str): ID of the room.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
        - All users and room must exist.
        - Only admins/moderators for the room can invoke this operation.
        - User must not already be an active member.
        - Target user's account_status must not be 'banned' or 'suspended'.
        - Room membership and user room lists updated atomically.
        """
        # Existence checks
        if room_id not in self.chat_rooms:
            return { "success": False, "error": "Room does not exist." }
        if admin_id not in self.users:
            return { "success": False, "error": "Admin user does not exist." }
        if target_user_id not in self.users:
            return { "success": False, "error": "Target user does not exist." }

        chat_room = self.chat_rooms[room_id]
        admin_user = self.users[admin_id]
        target_user = self.users[target_user_id]

        # Permission: Is admin_id a moderator for this room?
        admin_room_memberships = self.room_memberships.get(admin_id, {})
        admin_room_info = admin_room_memberships.get(room_id)
        if not admin_room_info or admin_room_info.get("membership_status") != "active":
            return { "success": False, "error": "Admin is not a member of the room." }
        if admin_room_info.get("role_in_room") not in ("moderator", "admin"):
            return { "success": False, "error": "Admin privileges required to add users." }

        # Check if target_user is already an active member
        target_room_memberships = self.room_memberships.get(target_user_id, {})
        target_room_info = target_room_memberships.get(room_id)
        if target_room_info and target_room_info.get("membership_status") == "active":
            return { "success": False, "error": "User is already an active member of the room." }

        # Check if account status is acceptable
        if target_user["account_status"] in ("banned", "suspended"):
            return { "success": False, "error": "Target user's account is not eligible for room membership." }

        # Update membership
        join_ts = time.time()
        # Add to chat_room's member list if not already present
        if target_user_id not in chat_room["room_members"]:
            chat_room["room_members"].append(target_user_id)

        # Add room to user's joined_room if not already present
        if room_id not in target_user["joined_room"]:
            target_user["joined_room"].append(room_id)

        # Add or update RoomMembershipInfo
        if target_user_id not in self.room_memberships:
            self.room_memberships[target_user_id] = {}
        self.room_memberships[target_user_id][room_id] = {
            "_id": target_user_id,
            "room_id": room_id,
            "membership_status": "active",
            "join_timestamp": join_ts,
            "role_in_room": "member"
        }

        return {
            "success": True,
            "message": f"User {target_user['username']} added to room {chat_room['room_name']}."
        }

    def remove_user_from_room(self, admin_id: str, target_user_id: str, room_id: str, ban: bool = False) -> dict:
        """
        Forcibly remove (kick or ban) a user from a room. Requires admin/mod privileges.

        Args:
            admin_id (str): _id of user performing the action (must be moderator in room).
            target_user_id (str): _id of user to remove from the room.
            room_id (str): The chat room's id.
            ban (bool): If True, set membership_status to 'banned'; else to 'left'.

        Returns:
            dict: {
                "success": True,
                "message": "User <id> has been removed from room <room_id>."
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only moderators/admins may remove users.
            - Target must be a current active member to remove.
            - Target and room must exist.
        """
        # Check all entities exist
        if admin_id not in self.users:
            return { "success": False, "error": "Admin user does not exist." }
        if target_user_id not in self.users:
            return { "success": False, "error": "Target user does not exist." }
        if room_id not in self.chat_rooms:
            return { "success": False, "error": "Chat room does not exist." }

        # Check admin's membership and role
        admin_membership = self.room_memberships.get(admin_id, {}).get(room_id)
        if not admin_membership or admin_membership["membership_status"] != "active":
            return { "success": False, "error": "Admin is not an active member of the room." }
        if admin_membership["role_in_room"] not in ["moderator", "admin"]:
            return { "success": False, "error": "Insufficient privileges (must be moderator or admin)." }

        # Check target's membership
        target_membership = self.room_memberships.get(target_user_id, {}).get(room_id)
        if not target_membership or target_membership["membership_status"] != "active":
            return { "success": False, "error": "Target user is not an active member of the room." }

        # Do not allow removing oneself (optional, can be adjusted)
        if admin_id == target_user_id:
            return { "success": False, "error": "Admin/moderator cannot remove themselves." }

        # Remove user from room's member list, if present
        if target_user_id in self.chat_rooms[room_id]["room_members"]:
            self.chat_rooms[room_id]["room_members"].remove(target_user_id)
        # Remove room from user's joined_room list
        if room_id in self.users[target_user_id]["joined_room"]:
            self.users[target_user_id]["joined_room"].remove(room_id)

        # Update membership status
        if ban:
            target_membership["membership_status"] = "banned"
        else:
            target_membership["membership_status"] = "left"
        # Optionally: Clear role_in_room, but may want to retain history

        return {
            "success": True,
            "message": f"User {target_user_id} has been {'banned from' if ban else 'removed from'} room {room_id}."
        }

    def restore_message(self, message_id: str) -> dict:
        """
        Restore a previously deleted message, setting its status from 'deleted' (or equivalent)
        back to 'delivered', if possible.

        Args:
            message_id (str): The unique ID of the message to restore.

        Returns:
            dict: {
                "success": True,
                "message": "Message restored successfully."
            }
            or
            {
                "success": False,
                "error": "reason"  # explanation if restoration isn't possible
            }

        Constraints:
            - Message must exist in message history.
            - Message must have status 'deleted'.
            - On success, set status to 'delivered'.
        """
        # Find message by traversing all message histories
        for room_id, message_list in self.messages.items():
            for msg in message_list:
                if msg["message_id"] == message_id:
                    if msg["sta"] != "deleted":
                        return {"success": False, "error": "Message is not deleted and cannot be restored."}
                    msg["sta"] = "delivered"
                    return {"success": True, "message": "Message restored successfully."}
        return {"success": False, "error": "Message not found."}


class MultiRoomChatApplication(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def list_joined_rooms(self, **kwargs):
        return self._call_inner_tool('list_joined_rooms', kwargs)

    def get_room_by_id(self, **kwargs):
        return self._call_inner_tool('get_room_by_id', kwargs)

    def get_room_by_name(self, **kwargs):
        return self._call_inner_tool('get_room_by_name', kwargs)

    def get_room_access_level(self, **kwargs):
        return self._call_inner_tool('get_room_access_level', kwargs)

    def list_room_members(self, **kwargs):
        return self._call_inner_tool('list_room_members', kwargs)

    def get_room_membership_status(self, **kwargs):
        return self._call_inner_tool('get_room_membership_status', kwargs)

    def fetch_room_message_history(self, **kwargs):
        return self._call_inner_tool('fetch_room_message_history', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def list_user_room_memberships(self, **kwargs):
        return self._call_inner_tool('list_user_room_memberships', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def join_room(self, **kwargs):
        return self._call_inner_tool('join_room', kwargs)

    def leave_room(self, **kwargs):
        return self._call_inner_tool('leave_room', kwargs)

    def edit_message(self, **kwargs):
        return self._call_inner_tool('edit_message', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def update_room_membership_status(self, **kwargs):
        return self._call_inner_tool('update_room_membership_status', kwargs)

    def create_room(self, **kwargs):
        return self._call_inner_tool('create_room', kwargs)

    def update_room_details(self, **kwargs):
        return self._call_inner_tool('update_room_details', kwargs)

    def add_user_to_room(self, **kwargs):
        return self._call_inner_tool('add_user_to_room', kwargs)

    def remove_user_from_room(self, **kwargs):
        return self._call_inner_tool('remove_user_from_room', kwargs)

    def restore_message(self, **kwargs):
        return self._call_inner_tool('restore_message', kwargs)
