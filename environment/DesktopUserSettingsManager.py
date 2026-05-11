# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from typing import Optional, Dict, Any



class UserInfo(TypedDict):
    _id: str
    username: str
    associated_profile: List[str]  # List of profile_ids

class ProfileInfo(TypedDict):
    profile_id: str
    user_id: str  # Must reference an existing User
    profile_name: str
    active_status: bool
    color_scheme: str
    color_temperature: float  # System-supported range
    text_size: float         # System-supported range
    other_display_settings: Any  # Could be dict or encoded str
    accessibility_option: str

class ReminderInfo(TypedDict):
    reminder_id: str
    profile_id: str   # Must reference an existing Profile
    message: str
    recurrence_interval_minutes: int  # Must be positive
    enabled: bool
    next_trigger_time: str  # Could use str (ISO) or float (timestamp)

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing desktop user settings and profiles.

        Constraints:
        - Each user can have multiple profiles but only one active profile at a time.
        - Profiles must reference an existing user.
        - Reminder recurrence intervals must be positive integers.
        - Text size and color temperature values must be within system-supported ranges.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Profiles: {profile_id: ProfileInfo}
        self.profiles: Dict[str, ProfileInfo] = {}

        # Reminders: {reminder_id: ReminderInfo}
        self.reminders: Dict[str, ReminderInfo] = {}
        # Some cases inject validator sentinel values using the same keys as
        # tool methods. Preserve them here instead of overwriting callables.
        self._validation_tool_state: Dict[str, Any] = {}

    def _parse_next_trigger_time(self, value: Any) -> Optional[datetime]:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if not isinstance(value, str):
            return None
        value = value.strip()
        if not value:
            return None
        if value.endswith("Z"):
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _format_next_trigger_time(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _default_next_trigger_time(self, profile_id: str, recurrence_interval_minutes: int) -> str:
        latest_existing: Optional[datetime] = None
        for reminder in self.reminders.values():
            if reminder.get("profile_id") != profile_id:
                continue
            parsed = self._parse_next_trigger_time(reminder.get("next_trigger_time"))
            if parsed is None:
                continue
            if latest_existing is None or parsed > latest_existing:
                latest_existing = parsed
        if latest_existing is None:
            base = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
            return self._format_next_trigger_time(base)
        return self._format_next_trigger_time(
            latest_existing + timedelta(minutes=recurrence_interval_minutes)
        )

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information for the specified username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user information dictionary
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g., "User not found"
            }

        Constraints:
            - Username must match exactly (case-sensitive).
            - If no such user exists, return success=False.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information given a user's unique id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": self.users[user_id] }

    def list_profiles_for_user(self, user_id: str) -> dict:
        """
        List all profiles (with metadata) associated with a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProfileInfo],  # List of associated ProfileInfo (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of error (e.g., user not found)
                }

        Constraints:
            - User with user_id must exist.
            - Only profiles that actually exist in the system will be returned (ignoring any dangling ids).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_info = self.users[user_id]
        profile_ids = user_info.get("associated_profile", [])
        result = [
            self.profiles[pid]
            for pid in profile_ids
            if pid in self.profiles
        ]
        return {"success": True, "data": result}

    def get_active_profile_for_user(self, user_id: str) -> dict:
        """
        Retrieve the currently active profile for a user by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": ProfileInfo }  # The active profile's info.
                On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - User must exist.
            - Per system constraints, there must be at most one active profile for any user.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found" }
    
        profile_ids = user_info.get("associated_profile", [])
        for pid in profile_ids:
            profile = self.profiles.get(pid)
            if profile and profile["user_id"] == user_id and profile.get("active_status", False):
                return { "success": True, "data": profile }
    
        return { "success": False, "error": "No active profile for user" }

    def get_profile_by_id(self, profile_id: str) -> dict:
        """
        Retrieve detailed information for a profile by its id.

        Args:
            profile_id (str): The ID of the profile to retrieve.

        Returns:
            dict: 
                - On success: { "success": True, "data": ProfileInfo }
                - On failure (profile does not exist): { "success": False, "error": str }

        Constraints:
            - Profile must exist in the manager.
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return { "success": False, "error": "Profile not found" }
        return { "success": True, "data": profile }

    def list_reminders_for_profile(self, profile_id: str) -> dict:
        """
        List all reminders associated with the specified profile.

        Args:
            profile_id (str): The identifier of the profile whose reminders should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo],  # May be empty if no reminders are found.
            }
            or
            {
                "success": False,
                "error": str  # If the profile does not exist.
            }

        Constraints:
            - The profile_id must correspond to an existing profile.
        """
        if profile_id not in self.profiles:
            return { "success": False, "error": "Profile does not exist" }

        result = [
            reminder for reminder in self.reminders.values()
            if reminder["profile_id"] == profile_id
        ]
        return { "success": True, "data": result }

    def get_reminder_by_id(self, reminder_id: str) -> dict:
        """
        Retrieve information for a reminder using its unique reminder_id.

        Args:
            reminder_id (str): The ID of the reminder to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ReminderInfo,  # Reminder metadata
            }
            or
            {
                "success": False,
                "error": str  # Reason the reminder could not be found
            }

        Constraints:
            - The reminder_id must exist in the managed reminders.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder not found" }
        return { "success": True, "data": reminder }

    def validate_color_temperature_in_range(self, color_temperature: float) -> dict:
        """
        Check whether the provided color_temperature is within the system-supported range.

        Args:
            color_temperature (float): The color temperature (in Kelvin) to check.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True if in range, else False
            }
            If input is not a number, result is False.
    
        Constraints:
            - Accepts only numeric input (float/int).
            - System-supported range is 1000.0 to 10000.0 inclusive.
        """
        MIN_CT = 1000.0
        MAX_CT = 10000.0

        # Ensure input is numeric
        if not isinstance(color_temperature, (float, int)):
            return {"success": True, "data": False}
    
        if MIN_CT <= color_temperature <= MAX_CT:
            return {"success": True, "data": True}
        else:
            return {"success": True, "data": False}

    def validate_text_size_in_range(self, text_size: float) -> dict:
        """
        Check if a given text size value falls within the system-supported range.

        Args:
            text_size (float): The text size to validate.

        Returns:
            dict:
                {
                    "success": True,
                    "data": True/False   # True if within range, False otherwise
                }
            or
                {
                    "success": False,
                    "error": str         # Explanation of error
                }

        Constraints:
            - System-supported text size is assumed to be between 8.0 and 72.0 (inclusive).
            - If text_size is not a float/int, operation fails.
        """
        try:
            val = float(text_size)
        except (TypeError, ValueError):
            return { "success": False, "error": "Invalid text_size value" }

        MIN_SIZE = 8.0
        MAX_SIZE = 72.0

        in_range = MIN_SIZE <= val <= MAX_SIZE
        return { "success": True, "data": in_range }

    def validate_reminder_recurrence_positive(self, reminder_id: str) -> dict:
        """
        Confirm that a specified recurrence interval for a reminder is a positive integer.

        Args:
            reminder_id (str): The ID of the reminder to validate.

        Returns:
            dict: 
                - { "success": True, "data": True } if recurrence interval is a positive integer
                - { "success": True, "data": False } if not (zero, negative, non-integer)
                - { "success": False, "error": "Reminder does not exist" } if reminder is missing

        Constraints:
            - Reminder must exist.
            - Recurrence interval must be an integer greater than 0.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder does not exist" }
        interval = reminder.get("recurrence_interval_minutes")
        is_positive_integer = isinstance(interval, int) and interval > 0
        return { "success": True, "data": is_positive_integer }

    def create_profile(
        self,
        user_id: str,
        profile_name: str,
        color_scheme: str,
        color_temperature: float,
        text_size: float,
        other_display_settings: Any,
        accessibility_option: str
    ) -> dict:
        """
        Create a new profile for a user with specified settings.

        Args:
            user_id (str): User to whom the profile will belong (must exist).
            profile_name (str): Name of the profile.
            color_scheme (str): Color scheme preference.
            color_temperature (float): Must be within supported system range.
            text_size (float): Must be within supported system range.
            other_display_settings (Any): Additional display preferences/settings.
            accessibility_option (str): Accessibility preference.

        Returns:
            dict: 
              On success:
                {"success": True, "message": "Profile created", "profile": <ProfileInfo>}
              On error:
                {"success": False, "error": <reason>}

        Constraints:
            - user_id must exist.
            - color_temperature in system-supported range.
            - text_size in system-supported range.
            - Profile will be inactive by default (active_status=False).
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Validate color temperature
        temp_ok = self.validate_color_temperature_in_range(color_temperature)
        if (not temp_ok.get("success", False)) or (not temp_ok.get("data", False)):
            return {"success": False, "error": f"Color temperature out of supported range. {temp_ok.get('error','')}".strip()}
        # Validate text size
        size_ok = self.validate_text_size_in_range(text_size)
        if (not size_ok.get("success", False)) or (not size_ok.get("data", False)):
            return {"success": False, "error": f"Text size out of supported range. {size_ok.get('error','')}".strip()}

        # Create unique profile_id (simple approach: "profile_{N}")
        profile_id = f"profile_{len(self.profiles) + 1}"
        while profile_id in self.profiles:
            profile_id = f"profile_{len(self.profiles) + 1 + len(profile_id)}"

        profile_info: ProfileInfo = {
            "profile_id": profile_id,
            "user_id": user_id,
            "profile_name": profile_name,
            "active_status": False,  # Only set to True by set_profile_active_status
            "color_scheme": color_scheme,
            "color_temperature": color_temperature,
            "text_size": text_size,
            "other_display_settings": other_display_settings,
            "accessibility_option": accessibility_option
        }

        self.profiles[profile_id] = profile_info
        # Link profile to user
        self.users[user_id]["associated_profile"].append(profile_id)

        return {"success": True, "message": "Profile created", "profile": profile_info}

    def set_profile_active_status(self, profile_id: str) -> dict:
        """
        Set a profile as active and deactivate all other profiles for the same user.

        Args:
            profile_id (str): The ID of the profile to activate.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Profile <profile_id> is now active for user <user_id>" }
                - On error:   { "success": False, "error": "reason" }

        Constraints:
          - The profile must exist.
          - The associated user must exist.
          - Only one profile per user is active at a time (enforced by deactivating others).
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return { "success": False, "error": "Profile does not exist" }
    
        user_id = profile.get("user_id")
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "Profile references a non-existent user" }
    
        # Deactivate all other profiles for this user
        for p in self.profiles.values():
            if p["user_id"] == user_id:
                p["active_status"] = (p["profile_id"] == profile_id)
        return {
            "success": True,
            "message": f"Profile {profile_id} is now active for user {user_id}"
        }

    def update_profile_settings(
        self,
        profile_id: str,
        color_temperature: float = None,
        text_size: float = None,
        color_scheme: str = None,
        accessibility_option: str = None,
        other_display_settings: Any = None,
    ) -> dict:
        """
        Modify color temperature, text size, color scheme, or accessibility options of a profile.

        Args:
            profile_id (str): The unique id of the profile to update.
            color_temperature (float, optional): Desired color temperature. Must be within supported range.
            text_size (float, optional): Desired text size. Must be within supported range.
            color_scheme (str, optional): Desired color scheme.
            accessibility_option (str, optional): Accessibility option string.
            other_display_settings (Any, optional): Arbitrary other display-related settings.

        Returns:
            dict: {
                "success": True,
                "message": "Profile settings updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        Constraints:
            - Profile must exist.
            - color_temperature/text_size, if provided, must be within supported range.
            - No update is performed if no updatable fields are provided.
        """
        # Ensure the profile exists
        if profile_id not in self.profiles:
            return {"success": False, "error": "Profile does not exist"}

        profile = self.profiles[profile_id]
        changed = False

        # Validate and update color_temperature
        if color_temperature is not None:
            valid_temp = self.validate_color_temperature_in_range(color_temperature)
            if (not valid_temp.get("success", False)) or (not valid_temp.get("data", False)):
                return {"success": False, "error": f"Invalid color temperature: {valid_temp.get('error', '')}".strip()}
            profile["color_temperature"] = color_temperature
            changed = True

        # Validate and update text_size
        if text_size is not None:
            valid_size = self.validate_text_size_in_range(text_size)
            if (not valid_size.get("success", False)) or (not valid_size.get("data", False)):
                return {"success": False, "error": f"Invalid text size: {valid_size.get('error', '')}".strip()}
            profile["text_size"] = text_size
            changed = True

        # Update color_scheme if provided
        if color_scheme is not None:
            profile["color_scheme"] = color_scheme
            changed = True

        # Update accessibility_option if provided
        if accessibility_option is not None:
            profile["accessibility_option"] = accessibility_option
            changed = True

        # Update other_display_settings if provided
        if other_display_settings is not None:
            profile["other_display_settings"] = other_display_settings
            changed = True

        if not changed:
            return {"success": False, "error": "No updatable fields were provided"}

        self.profiles[profile_id] = profile
        return {"success": True, "message": "Profile settings updated successfully"}


    def create_reminder(
        self, 
        profile_id: str, 
        message: str, 
        recurrence_interval_minutes: int, 
        enabled: bool = True, 
        next_trigger_time: Optional[str] = None
    ) -> dict:
        """
        Add a new reminder associated with a profile.

        Args:
            profile_id (str): Profile to which the reminder will be attached.
            message (str): The reminder message.
            recurrence_interval_minutes (int): Frequency (positive integer, in minutes).
            enabled (bool): Whether the reminder is enabled upon creation.
            next_trigger_time (str, optional): The next trigger time (ISO string or timestamp).
                If omitted, the environment assigns a deterministic default slot. When a task
                does not specify a required trigger time, callers should omit this field rather
                than invent one.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder created.",
                "reminder_id": str
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Profile must exist.
            - Recurrence interval must be positive.
        """
        # Check profile exists
        if profile_id not in self.profiles:
            return {"success": False, "error": "Profile does not exist"}

        # Check recurrence interval
        if not isinstance(recurrence_interval_minutes, int) or recurrence_interval_minutes <= 0:
            return {"success": False, "error": "Recurrence interval must be a positive integer"}

        # next_trigger_time (basic validation / deterministic default)
        if next_trigger_time is None:
            next_trigger_time = self._default_next_trigger_time(profile_id, recurrence_interval_minutes)
        elif not isinstance(next_trigger_time, (str, float, int)):
            return {"success": False, "error": "next_trigger_time must be an ISO string or timestamp if provided"}

        # Generate a unique reminder_id
        reminder_id = str(uuid.uuid4())

        # Create ReminderInfo dict
        reminder_info = {
            "reminder_id": reminder_id,
            "profile_id": profile_id,
            "message": message,
            "recurrence_interval_minutes": recurrence_interval_minutes,
            "enabled": enabled,
            "next_trigger_time": next_trigger_time,
        }

        self.reminders[reminder_id] = reminder_info

        return {
            "success": True,
            "message": "Reminder created.",
            "reminder_id": reminder_id
        }

    def update_reminder(
        self,
        reminder_id: str,
        message: str = None,
        recurrence_interval_minutes: int = None,
        enabled: bool = None
    ) -> dict:
        """
        Modify the message, recurrence interval, and/or enabled status of an existing reminder.

        Args:
            reminder_id (str): The ID of the reminder to update.
            message (str, optional): The new reminder message (if updating).
            recurrence_interval_minutes (int, optional): New recurrence interval in minutes (must be positive).
            enabled (bool, optional): Enabled status of the reminder.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Reminder must exist.
            - If updating recurrence_interval_minutes, it must be a positive integer.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return { "success": False, "error": "Reminder does not exist" }

        updated = False

        if message is not None:
            if not isinstance(message, str):
                return { "success": False, "error": "Message must be a string" }
            reminder["message"] = message
            updated = True

        if recurrence_interval_minutes is not None:
            if not isinstance(recurrence_interval_minutes, int) or recurrence_interval_minutes <= 0:
                return { "success": False, "error": "recurrence_interval_minutes must be a positive integer" }
            reminder["recurrence_interval_minutes"] = recurrence_interval_minutes
            updated = True

        if enabled is not None:
            if not isinstance(enabled, bool):
                return { "success": False, "error": "enabled must be a boolean value" }
            reminder["enabled"] = enabled
            updated = True

        if not updated:
            return { "success": False, "error": "No valid fields provided to update" }

        self.reminders[reminder_id] = reminder
        return { "success": True, "message": "Reminder updated successfully" }

    def delete_reminder(self, reminder_id: str) -> dict:
        """
        Remove a specific reminder from the system.

        Args:
            reminder_id (str): The ID of the reminder to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder <reminder_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Reminder does not exist."
            }

        Constraints:
            - The reminder_id must exist in the reminders dictionary.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder does not exist." }
        del self.reminders[reminder_id]
        return { "success": True, "message": f"Reminder {reminder_id} deleted successfully." }

    def deactivate_profile(self, profile_id: str) -> dict:
        """
        Deactivate a profile by setting its active_status to False.

        Args:
            profile_id (str): The ID of the profile to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "Profile '<profile_id>' deactivated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The profile_id must exist in self.profiles.
            - Operation is idempotent (if already deactivated, it is still treated as success).
            - Deactivating a profile does not activate another profile.
        """
        if profile_id not in self.profiles:
            return {"success": False, "error": f"Profile '{profile_id}' does not exist."}
    
        self.profiles[profile_id]["active_status"] = False
        return {"success": True, "message": f"Profile '{profile_id}' deactivated."}

    def delete_profile(self, profile_id: str) -> dict:
        """
        Remove a profile and all its associated reminders from the system.
        Also removes the profile from the associated user's profile list.

        Args:
            profile_id (str): The ID of the profile to delete.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Profile and associated reminders deleted."
                }
                OR
                {
                    "success": False,
                    "error": "Profile not found."
                }

        Constraints enforced:
            - Profile must exist.
            - All reminders associated with the profile are deleted.
            - Profile is removed from the user's profile list.
        """
        # Check profile existence
        if profile_id not in self.profiles:
            return { "success": False, "error": "Profile not found." }

        # Get profile info and user_id
        profile = self.profiles[profile_id]
        user_id = profile["user_id"]

        # Remove profile from user's associated_profile
        user = self.users.get(user_id)
        if user and profile_id in user.get("associated_profile", []):
            user["associated_profile"].remove(profile_id)

        # Delete associated reminders
        reminder_ids_to_delete = [
            r_id for r_id, r_info in self.reminders.items()
            if r_info["profile_id"] == profile_id
        ]
        for r_id in reminder_ids_to_delete:
            del self.reminders[r_id]

        # Delete the profile
        del self.profiles[profile_id]

        return { "success": True, "message": "Profile and associated reminders deleted." }

    def associate_profile_with_user(self, user_id: str, profile_id: str) -> dict:
        """
        Link an existing profile_id to a user's associated_profile list.

        Args:
            user_id (str): The ID of the user to associate the profile with.
            profile_id (str): The ID of the profile to link.

        Returns:
            dict: {
                "success": True,
                "message": "Profile <profile_id> associated with user <user_id>."
            }
            or
            {
                "success": False,
                "error": str  # Error message describing the failure reason.
            }

        Constraints:
            - The user must exist.
            - The profile must exist.
            - The profile must reference (belong to) the user.
            - Do not add duplicates if already associated.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": f"User '{user_id}' does not exist."}
        # Check if profile exists
        if profile_id not in self.profiles:
            return {"success": False, "error": f"Profile '{profile_id}' does not exist."}
        # Check if profile belongs to user
        if self.profiles[profile_id]["user_id"] != user_id:
            return {"success": False, "error": "Profile does not belong to this user."}
        # Check for duplicate
        user_info = self.users[user_id]
        if profile_id in user_info["associated_profile"]:
            # Idempotent: already associated
            return {"success": True, "message": f"Profile '{profile_id}' already associated with user '{user_id}'."}
        # Associate
        user_info["associated_profile"].append(profile_id)
        return {"success": True, "message": f"Profile '{profile_id}' associated with user '{user_id}'."}


class DesktopUserSettingsManager(BaseEnv):
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
            if key in {"validate_color_temperature_in_range", "validate_text_size_in_range"}:
                env._validation_tool_state[key] = copy.deepcopy(value)
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

    def list_profiles_for_user(self, **kwargs):
        return self._call_inner_tool('list_profiles_for_user', kwargs)

    def get_active_profile_for_user(self, **kwargs):
        return self._call_inner_tool('get_active_profile_for_user', kwargs)

    def get_profile_by_id(self, **kwargs):
        return self._call_inner_tool('get_profile_by_id', kwargs)

    def list_reminders_for_profile(self, **kwargs):
        return self._call_inner_tool('list_reminders_for_profile', kwargs)

    def get_reminder_by_id(self, **kwargs):
        return self._call_inner_tool('get_reminder_by_id', kwargs)

    def validate_color_temperature_in_range(self, **kwargs):
        return self._call_inner_tool('validate_color_temperature_in_range', kwargs)

    def validate_text_size_in_range(self, **kwargs):
        return self._call_inner_tool('validate_text_size_in_range', kwargs)

    def validate_reminder_recurrence_positive(self, **kwargs):
        return self._call_inner_tool('validate_reminder_recurrence_positive', kwargs)

    def create_profile(self, **kwargs):
        return self._call_inner_tool('create_profile', kwargs)

    def set_profile_active_status(self, **kwargs):
        return self._call_inner_tool('set_profile_active_status', kwargs)

    def update_profile_settings(self, **kwargs):
        return self._call_inner_tool('update_profile_settings', kwargs)

    def create_reminder(self, **kwargs):
        return self._call_inner_tool('create_reminder', kwargs)

    def update_reminder(self, **kwargs):
        return self._call_inner_tool('update_reminder', kwargs)

    def delete_reminder(self, **kwargs):
        return self._call_inner_tool('delete_reminder', kwargs)

    def deactivate_profile(self, **kwargs):
        return self._call_inner_tool('deactivate_profile', kwargs)

    def delete_profile(self, **kwargs):
        return self._call_inner_tool('delete_profile', kwargs)

    def associate_profile_with_user(self, **kwargs):
        return self._call_inner_tool('associate_profile_with_user', kwargs)
