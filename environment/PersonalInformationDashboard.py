# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime as dt
from uuid import uuid4
import uuid
import time



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    connected_profile: List[str]  # List of profile_ids

class MessageInfo(TypedDict):
    message_id: str
    source: str
    sender: str
    receiver: str
    content: str
    timestamp: str
    is_important: bool
    folder: str  # (corrected from 'fold')

class NoteInfo(TypedDict):
    note_id: str
    user_id: str
    content: str
    created_at: str
    last_modified: str

class ReminderInfo(TypedDict):
    reminder_id: str  # (corrected from 'minder_id')
    user_id: str
    content: str
    due_date: str
    status: str  # (corrected from 'sta')

class ExternalProfileInfo(TypedDict):
    profile_id: str
    service_name: str
    username: str
    linked_user_id: str
    access_token: str
    last_sync: str

class ExternalResourceInfo(TypedDict):
    resource_id: str  # (corrected from 'ource_id')
    external_profile_id: str
    type: str
    content: str
    last_fetched: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # Notes: {note_id: NoteInfo}
        self.notes: Dict[str, NoteInfo] = {}

        # Reminders: {reminder_id: ReminderInfo}
        self.reminders: Dict[str, ReminderInfo] = {}

        # External Profiles: {profile_id: ExternalProfileInfo}
        self.external_profiles: Dict[str, ExternalProfileInfo] = {}

        # External Public Resources: {resource_id: ExternalResourceInfo}
        self.external_resources: Dict[str, ExternalResourceInfo] = {}

        # Constraints and rules:
        # - Each message belongs to a specific source and user (via sender/receiver/source)
        # - Connected external profiles must have valid authentication credentials (access_token) to retrieve/update data
        # - Public resources (external_resources) are typically read-only and may be cached
        # - User permissions restrict access to private vs. public data
        # - Data synchronization with external accounts may be subject to API rate limits and refresh intervals

    @staticmethod
    def _parse_timestamp(value):
        if isinstance(value, (int, float)):
            return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("empty timestamp")
            try:
                return dt.datetime.fromtimestamp(float(raw), tz=dt.timezone.utc)
            except ValueError:
                pass
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            parsed = dt.datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        raise ValueError("unsupported timestamp type")

    def get_message_by_id(self, message_id: str) -> dict:
        """
        Retrieve message details by message_id, including importance and folder.

        Args:
            message_id (str): Unique identifier for the message.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": MessageInfo
                  }
                - On failure: {
                    "success": False,
                    "error": "Message not found"
                  }

        Constraints:
            - Message with the provided message_id must exist in system.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message not found"}
        return {"success": True, "data": msg}

    def list_important_messages(self, user_id: str) -> dict:
        """
        List all important messages (is_important=True) where the specified user is the receiver.

        Args:
            user_id (str): The user's unique identifier.

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
            - User must exist in the system.
            - Only messages where receiver == user_id and is_important==True are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        result = [
            msg for msg in self.messages.values()
            if msg.get('receiver') == user_id and msg.get('is_important', False) is True
        ]

        return {"success": True, "data": result}

    def list_messages_by_folder(self, user_id: str, folder: str) -> dict:
        """
        Retrieve all messages for the given user that are in the specified folder.

        Args:
            user_id (str): The _id of the user whose messages to query.
            folder (str): The folder name (e.g., 'inbox', 'sent').

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # All matching messages (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description (user not found)
            }

        Constraints:
            - The user_id must refer to an existing user.
            - Message's 'folder' field must match the given folder exactly.
            - Only messages where the user is the receiver will be returned (typical for personal inbox/folder).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        messages = [
            msg for msg in self.messages.values()
            if msg["receiver"] == user_id and msg["folder"] == folder
        ]
        return {"success": True, "data": messages}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info by exact name, including all their connected external profile info.

        Args:
            name (str): The name of the user to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "user": UserInfo,
                    "external_profiles": List[ExternalProfileInfo]
                }
            }
            or
            {
                "success": False,
                "error": str  # 'User not found'
            }

        Constraints:
            - User name must exactly match.
            - Returns all existing external profiles referenced.
        """
        # Find user by name (exact match)
        user = None
        for user_info in self.users.values():
            if user_info["name"] == name:
                user = user_info
                break

        if not user:
            return {"success": False, "error": "User not found"}

        # Resolve external profile details
        connected_profiles = []
        for profile_id in user.get("connected_profile", []):
            profile = self.external_profiles.get(profile_id)
            if profile is not None:
                connected_profiles.append(profile)

        return {
            "success": True,
            "data": {
                "user": user,
                "external_profiles": connected_profiles
            }
        }

    def get_external_profile_by_username_and_service(self, username: str, service_name: str) -> dict:
        """
        Find an external profile by username and service name.

        Args:
            username (str): The username of the external profile.
            service_name (str): The service name (e.g., GitHub, Twitter, etc.) of the external profile.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ExternalProfileInfo  # The matched external profile
                    }
                On failure:
                    {
                        "success": False,
                        "error": "No such external profile"
                    }
        """
        for profile in self.external_profiles.values():
            if profile["username"] == username and profile["service_name"] == service_name:
                return {"success": True, "data": profile}
        return {"success": False, "error": "No such external profile"}

    def get_external_profile_by_id(self, profile_id: str) -> dict:
        """
        Retrieve details of an external profile (including access token, last_sync, etc.) by its profile_id.

        Args:
            profile_id (str): The unique identifier of the external profile to retrieve.

        Returns:
            dict: 
            - On success: {"success": True, "data": ExternalProfileInfo}
            - On failure: {"success": False, "error": "External profile not found"}

        Constraints:
            - The profile_id must exist in the external_profiles dictionary.
        """
        profile = self.external_profiles.get(profile_id)
        if profile is None:
            return { "success": False, "error": "External profile not found" }
        return { "success": True, "data": profile }

    def list_external_profiles_for_user(self, user_id: str) -> dict:
        """
        List all connected external profiles for a given user.

        Args:
            user_id (str): The _id of the user whose external profiles are to be listed.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[ExternalProfileInfo],  # May be empty if the user has no connected profiles.
                }
                On failure: {
                    "success": False,
                    "error": str,  # Error message, e.g., user not found.
                }
        Constraints:
            - The user must exist (user_id must be present in self.users).
            - Only returns profiles that currently exist in self.external_profiles.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User not found"}

        profile_ids = user_info.get("connected_profile", [])
        ext_profiles = [
            self.external_profiles[pid]
            for pid in profile_ids
            if pid in self.external_profiles
        ]
        return {"success": True, "data": ext_profiles}

    def list_external_public_resources_by_profile(self, profile_id: str) -> dict:
        """
        Retrieve all external public resources associated with a given external profile.

        Args:
            profile_id (str): The unique identifier of the external profile.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ExternalResourceInfo]  # may be empty
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason (e.g., profile does not exist)
                    }

        Constraints:
            - The profile with the specified profile_id must exist.
            - No permissions are checked for public resource listing.
        """
        if profile_id not in self.external_profiles:
            return {"success": False, "error": "External profile does not exist"}

        resources = [
            resource_info
            for resource_info in self.external_resources.values()
            if resource_info["external_profile_id"] == profile_id
        ]

        return {"success": True, "data": resources}

    def find_external_public_resource_by_type_and_profile(
        self,
        external_profile_id: str,
        resource_type: str,
    ) -> dict:
        """
        Find all external public resources of a given type that are linked to a specific external profile.

        Args:
            external_profile_id (str): The profile_id of the external profile (e.g., a GitHub or Twitter linked account).
            resource_type (str): The type of public resource to search for (e.g., 'repository').

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ExternalResourceInfo],
                }
                OR
                {
                    "success": False,
                    "error": str,
                }

        Constraints:
            - The external profile must exist within the dashboard.
        """
        if external_profile_id not in self.external_profiles:
            return { "success": False, "error": "External profile does not exist" }

        results = [
            resource for resource in self.external_resources.values()
            if resource["external_profile_id"] == external_profile_id and resource["type"] == resource_type
        ]

        return { "success": True, "data": results }

    def check_external_profile_token_validity(self, profile_id: str) -> dict:
        """
        Verify whether the access token of an external profile is present and non-empty for API operations.

        Args:
            profile_id (str): The unique identifier of the external profile.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "profile_id": str,
                    "is_valid": bool,
                    "reason": str
                }
            }
            or
            {
                "success": False,
                "error": str  # "Profile not found"
            }

        Constraints:
            - The profile must exist in the system.
            - Token is considered valid if it is present and non-empty.
        """
        profile = self.external_profiles.get(profile_id)
        if not profile:
            return {
                "success": False,
                "error": "Profile not found"
            }

        token = profile.get("access_token", "")
        if token and isinstance(token, str) and token.strip():
            return {
                "success": True,
                "data": {
                    "profile_id": profile_id,
                    "is_valid": True,
                    "reason": "Token is present"
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "profile_id": profile_id,
                    "is_valid": False,
                    "reason": "Token is missing or empty"
                }
            }

    def get_note_by_id(self, note_id: str) -> dict:
        """
        Retrieve a specific note by its unique note_id.

        Args:
            note_id (str): Unique identifier for the note.

        Returns:
            dict: {
                "success": True,
                "data": NoteInfo  # The note information if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - The given note_id must exist in the system.
        """
        note = self.notes.get(note_id)
        if note is None:
            return { "success": False, "error": "Note not found" }
        return { "success": True, "data": note }

    def list_notes_for_user(self, user_id: str) -> dict:
        """
        List all notes belonging to a given user.

        Args:
            user_id (str): The unique identifier of the user to query notes for.

        Returns:
            dict:
                - On success: {"success": True, "data": List[NoteInfo]}
                - On failure: {"success": False, "error": "reason"}

        Constraints:
            - user_id must exist in the system (self.users).
            - Returns all notes with NoteInfo["user_id"] == user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        notes = [
            note_info for note_info in self.notes.values()
            if note_info["user_id"] == user_id
        ]

        return { "success": True, "data": notes }

    def get_reminder_by_id(self, reminder_id: str) -> dict:
        """
        Retrieve a specific reminder by its reminder_id.

        Args:
            reminder_id (str): The unique identifier for the reminder.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ReminderInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reminder not found"
                    }

        Constraints:
            - Reminder must exist in the system with the given reminder_id.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return { "success": False, "error": "Reminder not found" }
        return { "success": True, "data": reminder }

    def list_reminders_for_user(self, user_id: str) -> dict:
        """
        List all reminders set by a user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo]
            }
            Or:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User with given user_id must exist.
            - Returns an empty list if the user has no reminders.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        reminders = [
            reminder for reminder in self.reminders.values()
            if reminder["user_id"] == user_id
        ]

        return { "success": True, "data": reminders }

    def check_public_resource_cache_freshness(self, resource_id: str, threshold_seconds: int = 3600) -> dict:
        """
        Determine if a cached external public resource is fresh based on its last_fetched timestamp.

        Args:
            resource_id (str): The unique ID of the external public resource to check.
            threshold_seconds (int, optional): Age limit in seconds for cache freshness (default: 3600).

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": {
                        "fresh": bool,  # True if cache is within freshness threshold
                        "last_fetched": str,  # The last_fetched timestamp from record
                        "age_seconds": float,  # How old the cache is
                        "threshold_seconds": int  # The threshold used
                    }
                }
                On error:
                {
                    "success": False,
                    "error": str  # Explanation, e.g., resource not found or timestamp parsing failed
                }

        Constraints:
            - The resource must exist in external_resources.
            - last_fetched must be a valid ISO format datetime string.

        """

        resource = self.external_resources.get(resource_id)
        if not resource:
            return {"success": False, "error": "Resource does not exist"}

        last_fetched_str = resource.get("last_fetched")
        if not last_fetched_str:
            return {"success": False, "error": "Missing last_fetched timestamp"}

        try:
            # Try to parse as ISO 8601
            last_fetched_dt = self._parse_timestamp(last_fetched_str)
            now = dt.datetime.now(dt.timezone.utc)
            age_seconds = (now - last_fetched_dt).total_seconds()
        except Exception as e:
            return {"success": False, "error": f"Invalid last_fetched timestamp format: {last_fetched_str}"}

        fresh = age_seconds < threshold_seconds

        return {
            "success": True,
            "data": {
                "fresh": fresh,
                "last_fetched": last_fetched_str,
                "age_seconds": age_seconds,
                "threshold_seconds": threshold_seconds
            }
        }

    def mark_message_as_important(self, message_id: str, is_important: bool) -> dict:
        """
        Set or unset the 'is_important' status of a message.

        Args:
            message_id (str): The unique identifier of the message.
            is_important (bool): The desired importance status (True=important, False=not important).

        Returns:
            dict:
                - On success: {"success": True, "message": "Message <id> marked as important."} or not important.
                - On error: {"success": False, "error": "reason"}

        Constraints:
            - The message must exist in the system.
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist"}

        # Check type strictly for safety
        if not isinstance(is_important, bool):
            return {"success": False, "error": "'is_important' must be a boolean value"}

        self.messages[message_id]["is_important"] = is_important

        status_str = "marked as important" if is_important else "marked as not important"
        return {"success": True, "message": f"Message {message_id} {status_str}."}

    def move_message_to_folder(self, message_id: str, target_folder: str) -> dict:
        """
        Move a message to a different folder (e.g., inbox, archive, trash).

        Args:
            message_id (str): The unique ID of the message to move.
            target_folder (str): The name of the destination folder.

        Returns:
            dict: {
                "success": True,
                "message": "Message moved to folder '<target_folder>'."
            }
            or
            {
                "success": False,
                "error": "Message not found." | "Target folder must be a non-empty string."
            }

        Constraints:
            - Message must exist.
            - Target folder must be a non-empty string.
        """
        if not target_folder or not isinstance(target_folder, str):
            return { "success": False, "error": "Target folder must be a non-empty string." }

        msg = self.messages.get(message_id)
        if not msg:
            return { "success": False, "error": "Message not found." }

        # Perform the move
        msg["folder"] = target_folder
        return { "success": True, "message": f"Message moved to folder '{target_folder}'." }

    def add_note(self, user_id: str, content: str) -> dict:
        """
        Create a new user note.

        Args:
            user_id (str): The ID of the user owning the note.
            content (str): Text content of the note.

        Returns:
            dict: {
                "success": True,
                "message": "Note created successfully",
                "note_id": <new_note_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist in self.users
            - content must not be empty
            - note_id must be unique (auto-generated)
            - created_at and last_modified are set to the creation timestamp (UTC ISO)
        """

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if not isinstance(content, str) or not content.strip():
            return {"success": False, "error": "Note content cannot be empty"}

        note_id = str(uuid4())
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()

        # Defensive uniqueness check, unlikely to collide
        while note_id in self.notes:
            note_id = str(uuid4())

        new_note = {
            "note_id": note_id,
            "user_id": user_id,
            "content": content,
            "created_at": timestamp,
            "last_modified": timestamp
        }

        self.notes[note_id] = new_note

        return {
            "success": True,
            "message": "Note created successfully",
            "note_id": note_id
        }

    def update_note(self, note_id: str, content: str = None) -> dict:
        """
        Modify content of an existing note.

        Args:
            note_id (str): The unique identifier of the note to update.
            content (str, optional): The new content of the note.

        Returns:
            dict: {
                "success": True,
                "message": "Note updated"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only updates the content (and last_modified).
            - note_id must exist.
            - last_modified is always updated to current time if any update is made.
            - No other fields (user_id, created_at, note_id) can be changed.
            - At least one updatable field must be provided.
        """

        if note_id not in self.notes:
            return { "success": False, "error": "Note does not exist" }

        if content is None:
            return { "success": False, "error": "No new content specified for update" }

        note = self.notes[note_id]
        note["content"] = content
        note["last_modified"] = dt.datetime.now(dt.timezone.utc).isoformat()
        self.notes[note_id] = note

        return { "success": True, "message": "Note updated" }

    def delete_note(self, note_id: str) -> dict:
        """
        Remove a note from the system.

        Args:
            note_id (str): The unique identifier of the note to delete.

        Returns:
            dict: 
                On success: {"success": True, "message": "Note deleted successfully."}
                On failure: {"success": False, "error": "Note not found."}

        Constraints:
            - The note with the given note_id must exist.
        """
        if note_id not in self.notes:
            return {"success": False, "error": "Note not found."}

        del self.notes[note_id]
        return {"success": True, "message": "Note deleted successfully."}


    def add_reminder(self, user_id: str, content: str, due_date: str, status: str = "pending") -> dict:
        """
        Create and add a new reminder for the specified user.

        Args:
            user_id (str): The user's unique identifier.
            content (str): The content/text of the reminder.
            due_date (str): The due date/time for the reminder (ISO string recommended).
            status (str, optional): The status of the reminder ("pending", "done", etc.). Defaults to "pending".

        Returns:
            dict:
                On success: {"success": True, "message": "Reminder added", "reminder_id": <reminder_id>}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - user_id must exist in the dashboard.
            - reminder_id is autogenerated and unique.
            - content and due_date must be nonempty.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if not content or not due_date:
            return {"success": False, "error": "Content and due_date must be provided"}

        # Generate a unique reminder_id
        reminder_id = str(uuid.uuid4())
        while reminder_id in self.reminders:  # safeguard against rare uuid collision
            reminder_id = str(uuid.uuid4())

        reminder_info = {
            "reminder_id": reminder_id,
            "user_id": user_id,
            "content": content,
            "due_date": due_date,
            "status": status
        }

        self.reminders[reminder_id] = reminder_info

        return {
            "success": True,
            "message": "Reminder added",
            "reminder_id": reminder_id
        }

    def update_reminder(
        self,
        reminder_id: str,
        content: str = None,
        due_date: str = None,
        status: str = None
    ) -> dict:
        """
        Modify the content, due_date, or status of a reminder.

        Args:
            reminder_id (str): The ID of the reminder to update.
            content (Optional[str]): New content string for the reminder.
            due_date (Optional[str]): New due date string.
            status (Optional[str]): Updated status.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of error (reminder not found, nothing to update, etc.)
            }

        Constraints:
            - At least one of content, due_date, or status must be provided.
            - reminder_id must exist in the system.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found" }
    
        if content is None and due_date is None and status is None:
            return { "success": False, "error": "No fields specified to update" }

        reminder = self.reminders[reminder_id]
        updated = False

        if content is not None and reminder["content"] != content:
            reminder["content"] = content
            updated = True
        if due_date is not None and reminder["due_date"] != due_date:
            reminder["due_date"] = due_date
            updated = True
        if status is not None and reminder["status"] != status:
            reminder["status"] = status
            updated = True

        if not updated:
            # All fields match current, nothing actually changed, but it's not an error
            return { "success": True, "message": "Reminder already up to date" }
    
        self.reminders[reminder_id] = reminder
        return { "success": True, "message": "Reminder updated successfully" }

    def delete_reminder(self, reminder_id: str) -> dict:
        """
        Remove a reminder from the system.
    
        Args:
            reminder_id (str): The unique identifier of the reminder to delete.
    
        Returns:
            dict: 
                - { "success": True, "message": "Reminder deleted successfully." }
                - { "success": False, "error": "Reminder not found." }

        Constraints:
            - The reminder must exist in the system.
            - No user permission checks are enforced here.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found." }
    
        del self.reminders[reminder_id]
        return { "success": True, "message": "Reminder deleted successfully." }


    def add_external_profile(
        self,
        user_id: str,
        service_name: str,
        username: str,
        access_token: str,
        profile_id: str = None
    ) -> dict:
        """
        Link a new external service profile (e.g., GitHub) to the user's dashboard.

        Args:
            user_id (str): ID of the user to link the profile to.
            service_name (str): Name of the external service (e.g., 'GitHub').
            username (str): Username on the external service.
            access_token (str): Valid authentication token for the external service.
            profile_id (str, optional): Unique ID for the external profile (auto-generated if None).

        Returns:
            dict: {
                "success": True,
                "message": "External profile added and linked to user"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Provided user_id must exist.
            - access_token must be provided (non-empty).
            - Only one profile per (user, service_name, username).
            - profile_id must be unique system-wide.
            - After creation, update the user's connected_profile list.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        if not access_token or not access_token.strip():
            return {"success": False, "error": "A valid access_token must be provided"}

        # Check for duplicate (user, service_name, username)
        for profile in self.external_profiles.values():
            if (profile["linked_user_id"] == user_id and
                profile["service_name"].lower() == service_name.lower() and
                profile["username"].lower() == username.lower()):
                return {"success": False, "error": "Profile for this service and username already linked to this user"}

        # Generate unique profile_id if not provided or is duplicate
        if profile_id is None or profile_id in self.external_profiles:
            profile_id = str(uuid.uuid4())

        # Build ExternalProfileInfo
        new_profile = {
            "profile_id": profile_id,
            "service_name": service_name,
            "username": username,
            "linked_user_id": user_id,
            "access_token": access_token,
            "last_sync": ""  # Sync timestamp empty, not performed yet
        }

        # Add to external_profiles
        self.external_profiles[profile_id] = new_profile

        # Update the user's connected_profile list if not already present
        if "connected_profile" not in self.users[user_id]:
            self.users[user_id]["connected_profile"] = []

        if profile_id not in self.users[user_id]["connected_profile"]:
            self.users[user_id]["connected_profile"].append(profile_id)

        return {"success": True, "message": "External profile added and linked to user"}

    def update_external_profile_token(self, profile_id: str, new_access_token: str) -> dict:
        """
        Refresh or update access credentials (access_token) for an external profile.

        Args:
            profile_id (str): The unique identifier of the external profile to update.
            new_access_token (str): The new access token (credential) to be stored.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Access token updated for profile <profile_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Explanation: profile not found, token invalid, etc.
                    }

        Constraints:
            - profile_id must refer to an existing external profile.
            - new_access_token must be non-empty.
        """
        profile = self.external_profiles.get(profile_id)
        if profile is None:
            return { "success": False, "error": "External profile not found" }

        if not isinstance(new_access_token, str) or not new_access_token.strip():
            return { "success": False, "error": "Provided access token is invalid" }

        profile["access_token"] = new_access_token.strip()
        # Optionally update last_sync or additional metadata if used

        return {
            "success": True,
            "message": f"Access token updated for profile {profile_id}"
        }


    def sync_external_profile_data(self, profile_id: str) -> dict:
        """
        Fetch the latest data from an external profile, refreshing cached resources.

        Args:
            profile_id (str): The unique identifier of the external profile to sync.

        Returns:
            dict: Success or error message.
                - On success: { "success": True, "message": "External profile data synchronized and cache refreshed." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The external profile must exist.
            - Must have a valid (non-empty) access token.
            - Rate limiting: Sync operation may be disallowed if last_sync is too recent (e.g., less than 60 seconds ago).
            - Refresh all relevant cached resources (simulate by updating last_fetched field).
        """
        # 1. Check profile existence
        profile = self.external_profiles.get(profile_id)
        if not profile:
            return { "success": False, "error": "External profile does not exist." }
    
        # 2. Check if the access token is valid (non-empty, simplistic check)
        access_token = profile.get("access_token", "")
        if not access_token:
            return { "success": False, "error": "No valid access token for external profile." }
    
        # 3. Rate limiting: assume a minimum of 60 seconds between syncs
        try:
            last_sync_dt = self._parse_timestamp(profile.get("last_sync", "0"))
            last_sync_ts = last_sync_dt.timestamp()
        except Exception:
            last_sync_ts = 0.0

        now = time.time()
        now_iso = dt.datetime.fromtimestamp(now, tz=dt.timezone.utc).isoformat()
        MIN_INTERVAL = 60  # seconds

        if last_sync_ts > 0 and (now - last_sync_ts < MIN_INTERVAL):
            return {
                "success": False,
                "error": f"Sync rate limited. Please wait {int(MIN_INTERVAL - (now - last_sync_ts))} seconds before synching again."
            }
    
        # 4. "Fetch latest data" - simulate by updating all relevant cached resources' last_fetched timestamp
        resources_updated = 0
        for resource in self.external_resources.values():
            if resource["external_profile_id"] == profile_id:
                resource["last_fetched"] = now_iso
                if resource.get("type") == "client_presentation_data":
                    resource["content"] = "Latest synced client metrics for the upcoming presentation."
                resources_updated += 1
    
        # (In a real system, new resources/data could be created/fetched here.)

        # 5. Update profile's last_sync
        profile["last_sync"] = now_iso

        return {
            "success": True,
            "message": f"External profile data synchronized and cache refreshed ({resources_updated} resources updated)."
        }

    def cache_external_public_resource(
        self,
        resource_id: str,
        external_profile_id: str,
        type: str,
        content: str,
        last_fetched: str
    ) -> dict:
        """
        Cache or update a public resource (fetched from external API) for local use.
    
        Args:
            resource_id (str): Unique ID of the external resource.
            external_profile_id (str): The profile through which this resource was fetched (must exist).
            type (str): The type of resource (e.g., "repo", "tweet").
            content (str): The content/data returned from the external API.
            last_fetched (str): Time when this resource was last fetched (timestamp or ISO string).
    
        Returns:
            dict:
                {
                    "success": True,
                    "message": "External public resource cached successfully."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Associated external profile must exist in self.external_profiles.
            - access_token for that profile must not be empty.
            - If resource already exists, it is updated/overwritten.
        """
        profile = self.external_profiles.get(external_profile_id)
        if profile is None:
            return {"success": False, "error": "Associated external profile does not exist."}
        if not profile.get("access_token"):
            return {"success": False, "error": "External profile has no valid access token."}

        resource_info: ExternalResourceInfo = {
            "resource_id": resource_id,
            "external_profile_id": external_profile_id,
            "type": type,
            "content": content,
            "last_fetched": last_fetched
        }
        self.external_resources[resource_id] = resource_info
        return {"success": True, "message": "External public resource cached successfully."}

    def remove_external_profile(self, user_id: str, profile_id: str) -> dict:
        """
        Unlink an external profile from the user's dashboard.

        Args:
            user_id (str): The ID of the user from whose dashboard to remove the profile.
            profile_id (str): The ID of the external profile to unlink.

        Returns:
            dict:
              - {"success": True, "message": "External profile removed from user dashboard."}
              - {"success": False, "error": str} if profile/user does not exist or not linked
        Constraints:
            - User must exist.
            - External profile must exist.
            - User must have profile_id in their connected_profile list.
            - Only remove the link from the user's connected_profile; do not delete from global registry.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check profile exists
        if profile_id not in self.external_profiles:
            return {"success": False, "error": "Profile does not exist"}

        user_info = self.users[user_id]
        if profile_id not in user_info["connected_profile"]:
            return {"success": False, "error": "Profile is not linked to this user"}

        # Remove the profile id from the user's connected_profile list
        user_info["connected_profile"].remove(profile_id)

        # Optionally: Ensure no other user is linked, remove from registry if desired (not required here)

        return {"success": True, "message": "External profile removed from user dashboard."}


class PersonalInformationDashboard(BaseEnv):
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

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def list_important_messages(self, **kwargs):
        return self._call_inner_tool('list_important_messages', kwargs)

    def list_messages_by_folder(self, **kwargs):
        return self._call_inner_tool('list_messages_by_folder', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_external_profile_by_username_and_service(self, **kwargs):
        return self._call_inner_tool('get_external_profile_by_username_and_service', kwargs)

    def get_external_profile_by_id(self, **kwargs):
        return self._call_inner_tool('get_external_profile_by_id', kwargs)

    def list_external_profiles_for_user(self, **kwargs):
        return self._call_inner_tool('list_external_profiles_for_user', kwargs)

    def list_external_public_resources_by_profile(self, **kwargs):
        return self._call_inner_tool('list_external_public_resources_by_profile', kwargs)

    def find_external_public_resource_by_type_and_profile(self, **kwargs):
        return self._call_inner_tool('find_external_public_resource_by_type_and_profile', kwargs)

    def check_external_profile_token_validity(self, **kwargs):
        return self._call_inner_tool('check_external_profile_token_validity', kwargs)

    def get_note_by_id(self, **kwargs):
        return self._call_inner_tool('get_note_by_id', kwargs)

    def list_notes_for_user(self, **kwargs):
        return self._call_inner_tool('list_notes_for_user', kwargs)

    def get_reminder_by_id(self, **kwargs):
        return self._call_inner_tool('get_reminder_by_id', kwargs)

    def list_reminders_for_user(self, **kwargs):
        return self._call_inner_tool('list_reminders_for_user', kwargs)

    def check_public_resource_cache_freshness(self, **kwargs):
        return self._call_inner_tool('check_public_resource_cache_freshness', kwargs)

    def mark_message_as_important(self, **kwargs):
        return self._call_inner_tool('mark_message_as_important', kwargs)

    def move_message_to_folder(self, **kwargs):
        return self._call_inner_tool('move_message_to_folder', kwargs)

    def add_note(self, **kwargs):
        return self._call_inner_tool('add_note', kwargs)

    def update_note(self, **kwargs):
        return self._call_inner_tool('update_note', kwargs)

    def delete_note(self, **kwargs):
        return self._call_inner_tool('delete_note', kwargs)

    def add_reminder(self, **kwargs):
        return self._call_inner_tool('add_reminder', kwargs)

    def update_reminder(self, **kwargs):
        return self._call_inner_tool('update_reminder', kwargs)

    def delete_reminder(self, **kwargs):
        return self._call_inner_tool('delete_reminder', kwargs)

    def add_external_profile(self, **kwargs):
        return self._call_inner_tool('add_external_profile', kwargs)

    def update_external_profile_token(self, **kwargs):
        return self._call_inner_tool('update_external_profile_token', kwargs)

    def sync_external_profile_data(self, **kwargs):
        return self._call_inner_tool('sync_external_profile_data', kwargs)

    def cache_external_public_resource(self, **kwargs):
        return self._call_inner_tool('cache_external_public_resource', kwargs)

    def remove_external_profile(self, **kwargs):
        return self._call_inner_tool('remove_external_profile', kwargs)
