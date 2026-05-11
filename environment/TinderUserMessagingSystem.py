# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
from datetime import datetime
import time
import uuid
from typing import Dict



class UserProfileInfo(TypedDict):
    _id: str
    name: str
    nationality: str
    photos: List[str]
    interests: List[str]
    profile_status: str
    privacy_setting: str

class MatchInfo(TypedDict):
    match_id: str
    user_id_1: str
    user_id_2: str
    match_timestamp: str
    match_sta: str

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    receiver_id: str
    match_id: str
    timestamp: str
    content: str
    read_sta: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Tinder user and messaging simulation.
        """

        # UserProfiles: {_id: UserProfileInfo}
        self.user_profiles: Dict[str, UserProfileInfo] = {}
        # Maps to:
        # entity: UserProfile
        # attributes: _id, name, nationality, photos, interests, profile_status, privacy_setting

        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}
        # Maps to:
        # entity: Match
        # attributes: match_id, user_id_1, user_id_2, match_timestamp, match_sta

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}
        # Maps to:
        # entity: Message
        # attributes: message_id, sender_id, receiver_id, match_id, timestamp, content, read_sta

        # Store currently authenticated user's ID (operations performed as this user)
        self.current_user_id: Optional[str] = None

        # Constraints:
        # - Only users who have mutually matched can send direct messages to each other.
        # - Users can search or filter other profiles by nationality and other attributes unless restricted by privacy settings.
        # - Privacy settings for each profile may limit visibility or messaging accessibility.
        # - Users can only operate via their authenticated UserProfile.

    @staticmethod
    def _timestamp_sort_key(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return float("-inf")
            try:
                return float(text)
            except ValueError:
                pass
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return float("-inf")
        return float("-inf")

    def get_user_profile_by_name(self, name: str) -> dict:
        """
        Retrieve a user's profile details using their display name.

        Args:
            name (str): The display name (case sensitive) to search for.

        Returns:
            dict:
                On success:
                    { "success": True, "data": UserProfileInfo }
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - Only authenticated users (self.current_user_id) may perform this operation.
            - Privacy settings of the found profile may restrict visibility.
            - If multiple profiles match the name, the first one found is returned.
        """
        # Check authentication
        if self.current_user_id is None:
            return { "success": False, "error": "No user is currently authenticated" }
    
        # Scan for user(s) with the matching display name
        for user in self.user_profiles.values():
            if user["name"] == name:
                # Privacy check: for simplicity, we assume 'private' privacy_setting means invisible
                if user.get("privacy_setting", "").lower() == "private" and user["_id"] != self.current_user_id:
                    return { "success": False, "error": "User profile not visible due to privacy settings" }
                # Profile found and visible
                return { "success": True, "data": user }

        # No such user by that name found
        return { "success": False, "error": "User profile with that name does not exist" }

    def get_current_user_profile(self) -> dict:
        """
        Retrieve the user profile info of the currently authenticated user.

        Returns:
            dict: {
                "success": True,
                "data": UserProfileInfo  # User's own profile info
            }
            or
            {
                "success": False,
                "error": str  # e.g., if not authenticated
            }

        Constraints:
            - Only permitted if a user is authenticated via their UserProfile.
        """
        if self.current_user_id is None:
            return {"success": False, "error": "No user is currently authenticated"}

        user_profile = self.user_profiles.get(self.current_user_id)
        if user_profile is None:
            return {"success": False, "error": "Authenticated user profile not found"}

        return {"success": True, "data": user_profile}

    def list_visible_user_profiles(self) -> dict:
        """
        List all user profiles visible to the currently authenticated user,
        taking into account each profile's privacy_setting.

        Returns:
            dict: Success -- {
                "success": True,
                "data": List[UserProfileInfo]  # Profiles visible to the current user (excluding self)
            }
            Or error -- {
                "success": False,
                "error": str  # Error message (e.g., not authenticated)
            }

        Constraints:
            - Must be called by an authenticated user.
            - Privacy settings govern profile visibility.
            - User's own profile is not included in the returned list.
        """
        if not self.current_user_id or self.current_user_id not in self.user_profiles:
            return {"success": False, "error": "Not authenticated"}

        result = []
        for user_id, profile in self.user_profiles.items():
            if user_id == self.current_user_id:
                continue  # Do not show self in visible users

            # Assume privacy_setting: 'public' means visible; anything else means hidden
            if profile.get("privacy_setting", "public") == "public":
                result.append(profile)

        return {"success": True, "data": result}

    def search_user_profiles_by_nationality(self, nationality: str) -> dict:
        """
        Return user profiles whose nationality matches the specified value, 
        subject to privacy restrictions (excluding profiles with 'private' privacy_setting).
        The currently authenticated user must be set and is excluded from results.

        Args:
            nationality (str): Nationality string to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserProfileInfo],   # May be empty if no results.
            }
            or 
            {
                "success": False,
                "error": str,   # error reason
            }

        Constraints:
            - User must be authenticated (`current_user_id` set).
            - Profiles with 'private' privacy_setting are excluded from results.
            - Own profile (current user) is excluded from results.
        """
        if not self.current_user_id or self.current_user_id not in self.user_profiles:
            return { "success": False, "error": "No authenticated user." }

        result = []
        for profile in self.user_profiles.values():
            if (
                profile["_id"] != self.current_user_id and
                profile["nationality"] == nationality and
                profile.get("privacy_setting", "public") != "private"
            ):
                result.append(profile)

        return { "success": True, "data": result }

    def get_user_privacy_setting(self, user_id: str) -> dict:
        """
        Query the privacy setting of a specific user profile.

        Args:
            user_id (str): The user ID whose privacy setting will be fetched.

        Returns:
            dict:
                - On success: {"success": True, "data": privacy_setting}
                - On failure: {"success": False, "error": reason}

        Constraints:
            - The user_id must exist in the user_profiles.
        """
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return {"success": False, "error": "User profile does not exist"}
        return {"success": True, "data": user_profile["privacy_setting"]}

    def get_user_profile_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user profile given its user_id.

        Args:
            user_id (str): The unique user ID whose profile is to be fetched.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserProfileInfo }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - If user profile does not exist, return failure.
            - If profile privacy_setting is "private", only allow access if current_user_id matches user_id.
        """
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return { "success": False, "error": "User does not exist" }

        if user_profile.get("privacy_setting", "") == "private":
            if self.current_user_id != user_id:
                return { "success": False, "error": "Profile is private" }

        return { "success": True, "data": user_profile }

    def list_matches_of_current_user(self) -> dict:
        """
        List all match connections (MatchInfo) that include the currently authenticated user.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]   # List of the user's match connections, may be empty
            }
            or
            {
                "success": False,
                "error": str  # Description of failure (e.g., not authenticated)
            }

        Constraints:
            - Operation may only be performed as an authenticated user.
        """
        if not self.current_user_id:
            return {"success": False, "error": "No user is currently authenticated."}

        results = [
            match_info for match_info in self.matches.values()
            if match_info["user_id_1"] == self.current_user_id or match_info["user_id_2"] == self.current_user_id
        ]
        return {"success": True, "data": results}

    def find_match_between_users(self, other_user_id: str) -> dict:
        """
        Retrieve the match record (MatchInfo) between the currently authenticated user and the specified other user.
    
        Args:
            other_user_id (str): The _id of the other user to check for a match with.
    
        Returns:
            dict: 
            - If a match is found: { "success": True, "data": MatchInfo }
            - If no match: { "success": True, "data": None }
            - If authentication or user error: { "success": False, "error": str }
    
        Constraints:
            - Must be performed as an authenticated user.
            - Both user profiles must exist.
        """
        if self.current_user_id is None:
            return {"success": False, "error": "No user is currently authenticated."}
        if other_user_id not in self.user_profiles:
            return {"success": False, "error": "Other user does not exist."}
        if self.current_user_id not in self.user_profiles:
            return {"success": False, "error": "Authenticated user profile does not exist."}

        # Find any match where {user_id_1, user_id_2} == {current_user_id, other_user_id}
        uid1 = self.current_user_id
        uid2 = other_user_id
        for match_info in self.matches.values():
            pair = {match_info["user_id_1"], match_info["user_id_2"]}
            if set([uid1, uid2]) == pair:
                return {"success": True, "data": match_info}

        return {"success": True, "data": None}

    def get_match_info_by_id(self, match_id: str) -> dict:
        """
        Retrieve the details of a match using the provided match_id.

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict: 
                - { "success": True, "data": MatchInfo } if the match is found.
                - { "success": False, "error": "Match not found" } if not.

        Constraints:
            - No authentication or privacy check is needed; this is a direct query by match_id.
        """
        match_info = self.matches.get(match_id)
        if match_info is None:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match_info }

    def list_messages_for_match(self, match_id: str) -> dict:
        """
        Retrieve all messages sent and received in a specific match, for the currently authenticated user.

        Args:
            match_id (str): The match ID to retrieve the message history.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": List[MessageInfo],   # All messages for this match, possibly empty if none exist
                }
                On failure:
                {
                    "success": False,
                    "error": str   # Error description
                }

        Constraints:
            - User must be authenticated (self.current_user_id is not None).
            - The match must exist.
            - The current user must be either user_id_1 or user_id_2 in the match (a participant).
        """
        # Authentication check
        if not self.current_user_id:
            return {"success": False, "error": "User not authenticated."}

        # Match existence check
        match_info = self.matches.get(match_id)
        if match_info is None:
            return {"success": False, "error": "Match does not exist."}

        # User participation check
        if self.current_user_id not in [match_info['user_id_1'], match_info['user_id_2']]:
            return {"success": False, "error": "Current user is not a participant in this match."}

        # Retrieve all messages for this match, sorted chronologically.
        messages_for_match = [
            msg for msg in self.messages.values()
            if msg['match_id'] == match_id
        ]
        messages_for_match.sort(key=lambda m: self._timestamp_sort_key(m.get("timestamp")))

        return {"success": True, "data": messages_for_match}

    def get_latest_message_in_match(self, match_id: str) -> dict:
        """
        Retrieve the most recent message (MessageInfo) in a conversation (match).
    
        Args:
            match_id (str): The identifier of the match/conversation.

        Returns:
            dict: 
                - On success, if messages exist: 
                    { "success": True, "data": <MessageInfo> }
                - On success, if no messages exist:
                    { "success": True, "data": None }
                - On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The match must exist.
            - The current user must be authenticated and be a participant in the match.
        """
        # Check if user is authenticated
        if not self.current_user_id:
            return { "success": False, "error": "User not authenticated" }

        # Check if match exists
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match does not exist" }

        # Check if current user is participant of match
        if self.current_user_id not in [match['user_id_1'], match['user_id_2']]:
            return { "success": False, "error": "Access denied: not a participant in the match" }

        # Retrieve all messages linked to this match
        messages_in_match = [
            msg for msg in self.messages.values() if msg["match_id"] == match_id
        ]

        if not messages_in_match:
            return { "success": True, "data": None }

        # Find message with latest timestamp
        latest_msg = max(messages_in_match, key=lambda m: self._timestamp_sort_key(m.get("timestamp")))

        return { "success": True, "data": latest_msg }

    def get_message_info_by_id(self, message_id: str) -> dict:
        """
        Retrieve a specific message's details using its message_id. Only the sender or receiver may view the message.
    
        Args:
            message_id (str): Unique identifier for the message.

        Returns:
            dict:
                Success: { "success": True, "data": MessageInfo }
                Failure: { "success": False, "error": str }
        
        Constraints:
            - The requester must be authenticated (self.current_user_id not None).
            - Only sender or receiver of the message can retrieve info.
            - Fails if the message does not exist.
        """
        # Check authentication
        if not self.current_user_id:
            return { "success": False, "error": "Not authenticated" }

        # Check if message exists
        if message_id not in self.messages:
            return { "success": False, "error": "Message does not exist" }

        msg_info = self.messages[message_id]

        # Check if current user is sender or receiver
        if self.current_user_id != msg_info["sender_id"] and self.current_user_id != msg_info["receiver_id"]:
            return { "success": False, "error": "Permission denied: not sender or receiver" }

        return { "success": True, "data": msg_info }

    def authenticate_as_user(self, name: str) -> dict:
        """
        Set the currently authenticated user by user name.

        Args:
            name (str): The name of the user to authenticate as. Matching is case-sensitive and must be unique.

        Returns:
            dict: {
                "success": True,
                "message": "Authenticated as <user name> (<user id>)"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The name must exactly match an existing user profile.
            - If multiple users exist with the same name, authentication fails due to ambiguity.
        """
        matches = [profile for profile in self.user_profiles.values() if profile["name"] == name]
        if len(matches) == 0:
            return {"success": False, "error": "User not found"}
        if len(matches) > 1:
            return {"success": False, "error": "Multiple users found with the given name; authentication is ambiguous"}
        user = matches[0]
        self.current_user_id = user["_id"]
        return {"success": True, "message": f"Authenticated as {user['name']} ({user['_id']})"}

    def send_match_request(self, target_user_id: str) -> dict:
        """
        Initiate a match request from the currently authenticated user to another user (target_user_id).
        Returns:
            dict: Success or failure message.
            - On success: {"success": True, "message": "..."}
            - On failure: {"success": False, "error": "..."}
        Constraints:
            - Must be authenticated.
            - Target user must exist and not be same as self.
            - Cannot request if match or pending match already exists between users.
            - Target's privacy_setting may restrict requests (e.g., "private" blocks).
        """
        # Check authentication
        if not self.current_user_id or self.current_user_id not in self.user_profiles:
            return {"success": False, "error": "Authentication required."}
        if target_user_id not in self.user_profiles:
            return {"success": False, "error": "Target user does not exist."}
        if self.current_user_id == target_user_id:
            return {"success": False, "error": "Cannot send match request to yourself."}

        # Disallow match request if privacy_setting is 'private'
        target_privacy = self.user_profiles[target_user_id].get("privacy_setting", "public")
        if target_privacy == "private":
            return {"success": False, "error": "Target user does not accept match requests due to privacy settings."}

        # Check for existing match (pending or accepted) between these users
        for match in self.matches.values():
            u1, u2 = match["user_id_1"], match["user_id_2"]
            if {u1, u2} == {self.current_user_id, target_user_id}:
                if match.get("match_sta", "").lower() in ("pending", "accepted", "active", "matched"):
                    return {"success": False, "error": "Match or match request already exists between users."}

        # Generate match_id (could use uuid, but here just use count for determinism)
        match_id = f"match_{len(self.matches) + 1}"
        match_info = {
            "match_id": match_id,
            "user_id_1": self.current_user_id,
            "user_id_2": target_user_id,
            "match_timestamp": datetime.utcnow().isoformat(),
            "match_sta": "pending"
        }
        self.matches[match_id] = match_info

        return {
            "success": True,
            "message": f"Match request sent from {self.current_user_id} to {target_user_id}."
        }

    def accept_match_request(self, match_id: str) -> dict:
        """
        Accept/reply to a pending match request, establishing a mutual match.

        Args:
            match_id (str): The unique identifier of the pending match request.

        Returns:
            dict:
              On success: {"success": True, "message": "Match request accepted; mutual match established."}
              On failure: {"success": False, "error": <reason>}

        Constraints:
            - The user must be authenticated.
            - Match must exist and involve the authenticated user.
            - Match must not already be established (i.e., must be pending).
        """

        if self.current_user_id is None:
            return { "success": False, "error": "No user is currently authenticated." }

        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match ID does not exist." }

        # Check if current user is involved in this match
        if self.current_user_id not in (match["user_id_1"], match["user_id_2"]):
            return { "success": False, "error": "Authenticated user is not part of this match." }

        match_state = match["match_sta"].lower()
        if match_state in ("matched", "active"):
            return { "success": False, "error": "Match request already accepted/mutual." }

        if match_state != "pending":
            return { "success": False, "error": f"Cannot accept match in current state: {match['match_sta']}" }

        # Establish a usable mutual match state for downstream messaging tools.
        match["match_sta"] = "active"
        # Optionally: update match["match_timestamp"] to current time if desired

        return { "success": True, "message": "Match request accepted; mutual match established." }


    def send_message_to_match(self, match_id: str, content: str) -> dict:
        """
        Send a direct message from the authenticated user to their matched user, if permitted.

        Args:
            match_id (str): The ID of the match context (must be active, must include current user).
            content (str): The textual message to send.

        Returns:
            dict: {
                "success": True,
                "message": "Message sent successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
        - User must be authenticated (self.current_user_id not None).
        - Match must exist, be active, and include current user.
        - Messaging must not be blocked by privacy settings.
        """
        # 1. Authentication check
        if not self.current_user_id:
            return { "success": False, "error": "User not authenticated" }

        # 2. Match exists
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match does not exist" }

        # 3. Match is active
        if match.get("match_sta", "").lower() not in {"active", "matched"}:
            return { "success": False, "error": "Match is not active" }

        # 4. Current user is in match
        user1 = match["user_id_1"]
        user2 = match["user_id_2"]
        if self.current_user_id == user1:
            receiver_id = user2
        elif self.current_user_id == user2:
            receiver_id = user1
        else:
            return { "success": False, "error": "User not member of this match" }

        # 5. Receiver profile exists
        receiver_profile = self.user_profiles.get(receiver_id)
        if not receiver_profile:
            return { "success": False, "error": "Receiver profile does not exist" }

        # 6. Privacy check for receiver -- only basic check
        privacy_setting = receiver_profile.get("privacy_setting", "public").lower()
        if privacy_setting in ["private", "messages_blocked"]:
            return { "success": False, "error": "Receiver has disabled receiving messages" }

        # 7. Optional: check empty message content
        if not content or not content.strip():
            return { "success": False, "error": "Message content cannot be empty" }

        # 8. Store the new message
        new_message_id = str(uuid.uuid4())
        timestamp = str(time.time())
        message_info = {
            "message_id": new_message_id,
            "sender_id": self.current_user_id,
            "receiver_id": receiver_id,
            "match_id": match_id,
            "timestamp": timestamp,
            "content": content,
            "read_sta": "unread"
        }
        self.messages[new_message_id] = message_info

        return { "success": True, "message": "Message sent successfully" }

    def mark_message_as_read(self, message_id: str) -> dict:
        """
        Mark the specified message as read by updating its read_sta attribute.
    
        Args:
            message_id (str): The ID of the message to mark as read.
    
        Returns:
            dict:
                - success: True/False
                - message (if success): Success message.
                - error (if failure): Error description.
    
        Constraints:
            - Must be performed by the authenticated user.
            - Only the receiver of the message can mark it as read.
            - The message must exist.
        """
        if self.current_user_id is None:
            return { "success": False, "error": "No user is currently authenticated." }
    
        msg = self.messages.get(message_id)
        if msg is None:
            return { "success": False, "error": "Message does not exist." }
    
        if msg["receiver_id"] != self.current_user_id:
            return { "success": False, "error": "Only the receiver of the message can mark it as read." }
    
        # Update the read status (assume "read" is the value for read_sta)
        msg["read_sta"] = "read"
    
        # Optional: update the object in self.messages too (not strictly necessary with dict ref)
        self.messages[message_id] = msg
    
        return { "success": True, "message": "Message marked as read." }

    def update_profile_privacy_setting(self, new_privacy_setting: str) -> dict:
        """
        Change the privacy_setting of the currently authenticated user's profile.

        Args:
            new_privacy_setting (str): The new privacy setting to apply for the profile.

        Returns:
            dict: {
                "success": True,
                "message": "Privacy setting updated for user <id>"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. not authenticated, user not found)
            }

        Constraints:
            - Users can only operate via their authenticated UserProfile.
            - Only the authenticated user's own profile can be updated.
        """
        if self.current_user_id is None:
            return {"success": False, "error": "No authenticated user."}

        user_id = self.current_user_id
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return {"success": False, "error": "Authenticated user profile not found."}

        user_profile["privacy_setting"] = new_privacy_setting

        return {
            "success": True,
            "message": f"Privacy setting updated for user {user_id}"
        }

    def update_profile_attributes(self, updates: Dict[str, object]) -> dict:
        """
        Modify attributes (name, interests, nationality, etc.) of the currently authenticated user's profile.

        Args:
            updates (Dict[str, object]): Dictionary of profile attributes to update with their new values.

        Returns:
            dict: 
                - Success: { "success": True, "message": "User profile updated successfully" }
                - Failure: { "success": False, "error": "reason" }

        Constraints:
            - Only the currently authenticated user can update their profile.
            - Cannot update profile '_id'.
            - Fields not in UserProfileInfo or not allowed to be changed are ignored.
            - Fails if there are no valid update fields.
        """
        if self.current_user_id is None:
            return { "success": False, "error": "User not authenticated" }

        user_id = self.current_user_id
        if user_id not in self.user_profiles:
            return { "success": False, "error": "Current user profile not found" }

        profile = self.user_profiles[user_id]
        updatable_fields = set(profile.keys()) - {"_id"}
        updated_any = False
        for key, value in updates.items():
            if key in updatable_fields:
                profile[key] = value
                updated_any = True
        if not updated_any:
            return { "success": False, "error": "No valid fields provided for update" }

        self.user_profiles[user_id] = profile
        return { "success": True, "message": "User profile updated successfully" }

    def unmatch_user(self, other_user_id: str) -> dict:
        """
        Remove or deactivate an existing match between the current user and another user.

        Args:
            other_user_id (str): The user ID of the other user with whom to unmatch.

        Returns:
            dict: {
                "success": True,
                "message": "Unmatched user successfully."
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - User must be authenticated (self.current_user_id is set).
            - Only the two users in an active match can unmatch.
            - If match does not exist, or is already inactive, operation fails.
        """
        # Check authentication
        if not self.current_user_id:
            return {"success": False, "error": "Not authenticated as any user."}
        if other_user_id == self.current_user_id:
            return {"success": False, "error": "Cannot unmatch with oneself."}
        # Check both users exist
        if self.current_user_id not in self.user_profiles or other_user_id not in self.user_profiles:
            return {"success": False, "error": "One or both users do not exist."}
        # Find active match
        match = None
        for match_info in self.matches.values():
            users = {match_info["user_id_1"], match_info["user_id_2"]}
            if {self.current_user_id, other_user_id} == users:
                if match_info.get("match_sta", "active").lower() in {"active", "matched"}:
                    match = match_info
                    break
        if not match:
            return {"success": False, "error": "No active match exists between users."}
        # Deactivate the match
        match["match_sta"] = "inactive"
        return {"success": True, "message": "Unmatched user successfully."}


class TinderUserMessagingSystem(BaseEnv):
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

    def get_user_profile_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_profile_by_name', kwargs)

    def get_current_user_profile(self, **kwargs):
        return self._call_inner_tool('get_current_user_profile', kwargs)

    def list_visible_user_profiles(self, **kwargs):
        return self._call_inner_tool('list_visible_user_profiles', kwargs)

    def search_user_profiles_by_nationality(self, **kwargs):
        return self._call_inner_tool('search_user_profiles_by_nationality', kwargs)

    def get_user_privacy_setting(self, **kwargs):
        return self._call_inner_tool('get_user_privacy_setting', kwargs)

    def get_user_profile_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_profile_by_id', kwargs)

    def list_matches_of_current_user(self, **kwargs):
        return self._call_inner_tool('list_matches_of_current_user', kwargs)

    def find_match_between_users(self, **kwargs):
        return self._call_inner_tool('find_match_between_users', kwargs)

    def get_match_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_info_by_id', kwargs)

    def list_messages_for_match(self, **kwargs):
        return self._call_inner_tool('list_messages_for_match', kwargs)

    def get_latest_message_in_match(self, **kwargs):
        return self._call_inner_tool('get_latest_message_in_match', kwargs)

    def get_message_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_info_by_id', kwargs)

    def authenticate_as_user(self, **kwargs):
        return self._call_inner_tool('authenticate_as_user', kwargs)

    def send_match_request(self, **kwargs):
        return self._call_inner_tool('send_match_request', kwargs)

    def accept_match_request(self, **kwargs):
        return self._call_inner_tool('accept_match_request', kwargs)

    def send_message_to_match(self, **kwargs):
        return self._call_inner_tool('send_message_to_match', kwargs)

    def mark_message_as_read(self, **kwargs):
        return self._call_inner_tool('mark_message_as_read', kwargs)

    def update_profile_privacy_setting(self, **kwargs):
        return self._call_inner_tool('update_profile_privacy_setting', kwargs)

    def update_profile_attributes(self, **kwargs):
        return self._call_inner_tool('update_profile_attributes', kwargs)

    def unmatch_user(self, **kwargs):
        return self._call_inner_tool('unmatch_user', kwargs)
