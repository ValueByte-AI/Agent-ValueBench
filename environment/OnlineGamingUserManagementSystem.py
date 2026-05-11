# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class UserInfo(TypedDict):
    _id: str  # unique user identifier
    username: str
    password_hash: str  # securely stored hash, never plaintext
    registration_date: str
    email: str
    account_status: str  # e.g., suspended, banned, active
    preferences: Dict[str, Any]  # preference settings (key-value pairs)

class UserProfileInfo(TypedDict):
    _id: str  # user id this profile belongs to
    display_name: str
    avatar_url: str
    bio: str
    contact_info: str

class AchievementInfo(TypedDict):
    achievement_id: str
    user_id: str  # user who earned the achievement
    achievement_type: str
    date_earned: str
    metadata: Dict[str, Any]

class GameProgressInfo(TypedDict):
    _id: str  # unique progress id, maybe composite of user and game
    game_id: str
    level: int
    score: int
    progress_data: Dict[str, Any]
    last_played: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for online gaming platform user management.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # UserProfiles: {_id: UserProfileInfo}
        self.user_profiles: Dict[str, UserProfileInfo] = {}

        # Achievements: {achievement_id: AchievementInfo}
        self.achievements: Dict[str, AchievementInfo] = {}

        # GameProgress records: {_id: GameProgressInfo}
        self.game_progress: Dict[str, GameProgressInfo] = {}

        # Constraints:
        # - Each user_id (_id) must be unique.
        # - User credentials (password_hash) must be securely stored and never revealed in plain text.
        # - Achievements and game progress must be correctly associated with the relevant user_id.
        # - Users can only access or modify their own data unless granted platform administrative permissions.
        # - Account status may restrict access or operations (e.g., suspended, banned, active).

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve non-sensitive user information by user ID, excluding the password hash.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
              - {
                    "success": True, 
                    "data": {UserInfo (without 'password_hash')}
                }
              - OR
                {
                    "success": False, 
                    "error": "User not found"
                }

        Constraints:
            - password_hash must never be included in the output.
            - Returns only information if the user exists.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Return all fields except 'password_hash'
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        return {"success": True, "data": user_info}

    def get_user_profile(self, user_id: str) -> dict:
        """
        Retrieve the extended profile (display name, avatar, bio, contact info) for the given user ID.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": UserProfileInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "User profile not found"
            }

        Constraints:
            - The user ID must exist in the user_profiles mapping.
        """
        if not isinstance(user_id, str) or not user_id:
            return {"success": False, "error": "Invalid user ID"}
        if user_id not in self.user_profiles:
            return {"success": False, "error": "User profile not found"}
        return {"success": True, "data": self.user_profiles[user_id]}

    def get_user_achievements(self, user_id: str) -> dict:
        """
        List all achievements earned by a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[AchievementInfo]  # All achievements for this user (may be empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., user does not exist)
                    }

        Constraints:
            - User with user_id must exist in the system.
            - Only achievements for the specified user_id are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User with given user_id does not exist" }

        result = [
            ach for ach in self.achievements.values()
            if ach["user_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_user_game_progress(self, user_id: str) -> dict:
        """
        List all game progress records for a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[GameProgressInfo],  # may be empty if user has no progress
            }
            or
            {
                "success": False,
                "error": str  # error message, e.g., if user does not exist
            }

        Constraints:
            - The user (user_id) must exist in the system.
            - Only game progress records associated with the user are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Collect all game progress where progress_id starts with user_id (common composite id pattern)
        results = [
            progress for progress in self.game_progress.values()
            if progress["_id"].startswith(user_id + ":") or progress.get("user_id", None) == user_id
        ]

        return {"success": True, "data": results}

    def list_users_by_status(self, account_status: str) -> dict:
        """
        Retrieve a list of users filtered by their account_status.
    
        Args:
            account_status (str): Status value to filter users by (e.g., 'active', 'banned', etc.).
    
        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # List of users' public info (never includes password_hash)
            }
            or
            {
                "success": False,
                "error": str  # Only if an input is invalid or an internal error occurs
            }
    
        Constraints:
            - Never return password_hash in any user entry.
            - If no users match, return an empty list with success=True.
        """
        users_filtered = []
        for user in self.users.values():
            if user["account_status"] == account_status:
                # Exclude password_hash; prepare public info
                user_info = {
                    "_id": user["_id"],
                    "username": user["username"],
                    "registration_date": user["registration_date"],
                    "email": user["email"],
                    "account_status": user["account_status"],
                    "preferences": user["preferences"]
                }
                users_filtered.append(user_info)

        return { "success": True, "data": users_filtered }

    def get_account_status(self, user_id: str) -> dict:
        """
        Query the account status (e.g., active, suspended, banned) for a given user.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "user_id": str,
                    "account_status": str
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user ID must exist in the system.
            - No sensitive information (e.g., password) is ever revealed.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "account_status": user["account_status"]
            }
        }

    def search_users_by_username(self, username_query: str) -> dict:
        """
        Retrieve a list of users whose usernames partially or fully match the provided query string.
    
        Args:
            username_query (str): The substring (case-insensitive) to search for in usernames.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "data": List[UserInfo (without password_hash)],
                    }
                - If input is invalid:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - password_hash field is never returned or revealed.
            - Empty username_query returns error {"success": False, "error": "..."}.
        """
        if not username_query or not isinstance(username_query, str):
            return {"success": False, "error": "Missing or invalid username query."}

        normalized_query = username_query.lower()
        results = []
        for user in self.users.values():
            if normalized_query in user["username"].lower():
                # Exclude password_hash
                user_info = {k: v for k, v in user.items() if k != "password_hash"}
                results.append(user_info)

        return {"success": True, "data": results}

    def check_user_permission(
        self,
        caller_id: str,
        target_user_id: str,
        required_permission: str
    ) -> dict:
        """
        Checks if the caller has the required permission level (admin or owner)
        to operate on the target user account.

        Args:
            caller_id (str): The user_id of the requesting user.
            target_user_id (str): The user_id of the user whose data is being operated on.
            required_permission (str): Permission type to check, e.g., "admin" or "owner".

        Returns:
            dict:
                { "success": True, "has_permission": bool }
                or
                { "success": False, "error": str } on input or logic errors.

        Constraints:
            - Both user IDs must exist.
            - Owner means caller == target and account_status is "active".
            - Admin means account_status is "admin".
            - Suspended/banned/etc. users cannot be granted any permissions.
        """
        # Validate users exist
        caller = self.users.get(caller_id)
        if not caller:
            return { "success": False, "error": f"Caller user_id {caller_id} not found" }
        target = self.users.get(target_user_id)
        if not target:
            return { "success": False, "error": f"Target user_id {target_user_id} not found" }

        # Validate permission type
        if required_permission not in ("admin", "owner"):
            return { "success": False, "error": "Invalid required_permission type" }

        # Account status check
        if caller["account_status"] not in ("active", "admin"):
            return { "success": True, "has_permission": False }

        if required_permission == "admin":
            # Only admin users have admin rights
            if caller["account_status"] == "admin":
                return { "success": True, "has_permission": True }
            else:
                return { "success": True, "has_permission": False }

        if required_permission == "owner":
            # User must be acting on own account and be active
            if caller_id == target_user_id and caller["account_status"] == "active":
                return { "success": True, "has_permission": True }
            else:
                return { "success": True, "has_permission": False }

        # Fallback (shouldn't be reached)
        return { "success": False, "error": "Unhandled permission logic" }

    def register_new_user(
        self,
        _id: str,
        username: str,
        password_hash: str,
        email: str,
        registration_date: str,
        preferences: dict = None
    ) -> dict:
        """
        Register a new user account with a unique user ID and a securely stored password hash.

        Args:
            _id (str): Unique user identifier.
            username (str): Desired username (must be unique).
            password_hash (str): Secure hash of user's password (never plaintext).
            email (str): User's email address.
            registration_date (str): ISO or platform-consistent registration date.
            preferences (dict, optional): User preference settings. Defaults to {}.

        Returns:
            dict: {
                "success": True,
                "message": "User registered successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Each user_id (_id) must be unique.
            - Each username must be unique.
            - Password_hash must be supplied, never stored/received as plaintext.
        """
        # Validate _id uniqueness
        if _id in self.users:
            return { "success": False, "error": "User ID already exists" }

        # Validate username uniqueness
        for user in self.users.values():
            if user['username'] == username:
                return { "success": False, "error": "Username already exists" }

        # Basic password hash validation (must not be empty and not plaintext-like)
        if not password_hash or len(password_hash) < 20:
            # 20 chars: rudimentary check for hash (not exhaustive)
            return { "success": False, "error": "Password hash is invalid or insecure" }

        # Basic email validation (rudimentary)
        if ('@' not in email) or ('.' not in email):
            return { "success": False, "error": "Email format is invalid" }

        # Set defaults
        user_info = {
            "_id": _id,
            "username": username,
            "password_hash": password_hash,
            "registration_date": registration_date,
            "email": email,
            "account_status": "active",
            "preferences": preferences if preferences is not None else {}
        }

        self.users[_id] = user_info
        return { "success": True, "message": "User registered successfully" }

    def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any], 
        requester_id: str, 
        is_admin: bool = False
    ) -> dict:
        """
        Update fields in a user's extended profile (display_name, avatar_url, bio, contact_info).

        Args:
            user_id (str): The unique identifier of the user whose profile to update.
            updates (dict): Dictionary of fields to update (keys: display_name, avatar_url, bio, contact_info).
            requester_id (str): The unique identifier of the user making the request.
            is_admin (bool): Whether the requester has administrative privileges (default: False).

        Returns:
            dict: {
                "success": True,
                "message": "User profile updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only the owner or an admin may modify the profile.
            - Updates are restricted to display_name, avatar_url, bio, and contact_info.
            - If the account is banned or suspended, updates are allowed only for admins.
        """
        # Validate requester exists
        if requester_id not in self.users:
            return { "success": False, "error": "Requester user does not exist." }
    
        # Validate target user and profile exists
        if user_id not in self.users:
            return { "success": False, "error": "Target user does not exist." }
        if user_id not in self.user_profiles:
            return { "success": False, "error": "User profile does not exist." }

        # Permission check: must be self or admin
        if requester_id != user_id and not is_admin:
            return { "success": False, "error": "Permission denied. Only the user or an admin may update the profile." }

        # Account status restriction for normal users
        status = self.users[user_id].get("account_status", "").lower()
        if status in ("banned", "suspended") and not is_admin:
            return { "success": False, "error": f"Profile update not allowed: account status is '{status}'." }

        # Only allow whitelisted updatable fields
        allowed_fields = {"display_name", "avatar_url", "bio", "contact_info"}
        updates_to_apply = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates_to_apply:
            return { "success": False, "error": "No valid updatable fields in request." }

        # Apply updates
        for k, v in updates_to_apply.items():
            self.user_profiles[user_id][k] = v

        return { "success": True, "message": "User profile updated." }

    def update_user_preferences(
        self, 
        user_id: str, 
        new_preferences: dict, 
        requester_id: str, 
        is_admin: bool = False
    ) -> dict:
        """
        Modify a user's preference settings if permitted.

        Args:
            user_id (str): The unique identifier of the user whose preferences should be modified.
            new_preferences (dict): Key-value pairs to update/add in the user's preferences.
            requester_id (str): ID of the user making the request (must be user themselves or admin).
            is_admin (bool): If True, the requester is an admin and can override most restrictions.

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "User preferences updated successfully." }
                On failure: 
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only the account holder or an admin can modify preferences.
            - If the account is not active, update is not allowed, unless requester is admin.
            - Preferences must be a dictionary.
        """
        # User existence check
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Permission check
        if requester_id != user_id and not is_admin:
            return { "success": False, "error": "Permission denied. Can only update own preferences unless admin." }

        user_info = self.users[user_id]

        # Account status check
        if user_info.get("account_status", "active") != "active" and not is_admin:
            return { "success": False, "error": f"Cannot update preferences; account status is '{user_info.get('account_status', 'unknown')}'." }

        # Preferences type check
        if not isinstance(new_preferences, dict):
            return { "success": False, "error": "New preferences must be provided as a dictionary." }

        # Merge/update the preferences dict
        # Only update the specified keys, keep existing ones
        user_info["preferences"].update(new_preferences)

        # Reflect changes in the global dict
        self.users[user_id] = user_info

        return { "success": True, "message": "User preferences updated successfully." }

    def update_account_status(self, requester_id: str, target_user_id: str, new_status: str) -> dict:
        """
        Change a user's account status (e.g., activate, suspend, ban).
        Constraints:
          - Only users with proper administrative privilege can perform this operation.
          - Both requester_id and target_user_id must exist.
          - new_status must be a valid status string (e.g., 'active', 'suspended', 'banned').
          - User cannot change their own status unless permitted by platform policy.

        Args:
            requester_id (str): The user attempting to perform the status change.
            target_user_id (str): The user account whose status is to be changed.
            new_status (str): The new status string.

        Returns:
            dict: {
                "success": True,
                "message": "Account status updated to <new_status> for user <target_user_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        """
        # Check existence of both users
        if requester_id not in self.users:
            return {"success": False, "error": "Requester user not found."}
        if target_user_id not in self.users:
            return {"success": False, "error": "Target user not found."}

        # Enforce status value (typical statuses)
        valid_statuses = {"active", "suspended", "banned"}
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid account status '{new_status}'."}

        # Check permissions: Use internal permission system if exists, here we just check for 'admin'
        requester_info = self.users[requester_id]
        if requester_info.get("account_status") != "admin":
            return {"success": False, "error": "Permission denied. Only admins can modify account status."}
    
        # Don't do anything if no actual change
        current_status = self.users[target_user_id]["account_status"]
        if current_status == new_status:
            return {"success": True, "message": f"Account status for user {target_user_id} is already '{new_status}'."}

        # All checks pass, update status
        self.users[target_user_id]["account_status"] = new_status

        return {
            "success": True,
            "message": f"Account status updated to '{new_status}' for user {target_user_id}."
        }

    def add_user_achievement(
        self,
        achievement_id: str,
        user_id: str,
        achievement_type: str,
        date_earned: str,
        metadata: Dict[str, Any]
    ) -> dict:
        """
        Add a new achievement for a given user.

        Args:
            achievement_id (str): Unique identifier for the achievement.
            user_id (str): User's unique identifier to associate the achievement with.
            achievement_type (str): Type or category of the achievement.
            date_earned (str): Date the achievement was earned.
            metadata (dict): Additional metadata related to the achievement.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Achievement added for user <user_id>"}
                On failure:
                    {"success": False, "error": "reason"}

        Constraints:
            - achievement_id must be unique.
            - user_id must exist in self.users.
            - Achievement must be associated with a valid user.
            - User's account status must allow adding achievements (must be 'active').
        """
        # Check if achievement_id already exists
        if achievement_id in self.achievements:
            return {"success": False, "error": "Achievement ID already exists"}

        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check if user account is in a status that allows achievement add
        user_account_status = self.users[user_id].get("account_status", "active")
        if user_account_status not in ["active"]:
            return {"success": False, "error": f"User account status '{user_account_status}' does not allow adding achievements"}

        # Add achievement
        achievement_info: AchievementInfo = {
            "achievement_id": achievement_id,
            "user_id": user_id,
            "achievement_type": achievement_type,
            "date_earned": date_earned,
            "metadata": metadata
        }
        self.achievements[achievement_id] = achievement_info

        return {"success": True, "message": f"Achievement added for user {user_id}"}

    def update_game_progress(
        self, user_id: str, game_id: str, level: int, score: int, 
        progress_data: dict, last_played: str
    ) -> dict:
        """
        Modify or add a user's game progress record.

        Args:
            user_id (str): The ID of the user whose progress to modify/add.
            game_id (str): The ID of the game.
            level (int): The user level in the game.
            score (int): The user score in the game.
            progress_data (dict): Additional progress information.
            last_played (str): ISO date/time string of last played.

        Returns:
            dict: On success: {
                "success": True, 
                "message": "Game progress for user {user_id} & game {game_id} updated/added."
            }
            On failure: {
                "success": False, 
                "error": "<reason>"
            }

        Constraints:
            - user_id must exist and be active (account status must not be suspended/banned).
            - game_progress record key is composite of user_id and game_id.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        if user["account_status"] not in ("active",):
            return {"success": False, "error": f"User account is {user['account_status']}."}

        progress_key = f"{user_id}:{game_id}"
        progress_record = self.game_progress.get(progress_key)

        if progress_record:
            # Update existing
            progress_record["level"] = level
            progress_record["score"] = score
            progress_record["progress_data"] = progress_data
            progress_record["last_played"] = last_played
            action = "updated"
        else:
            # Add new
            self.game_progress[progress_key] = {
                "_id": progress_key,
                "game_id": game_id,
                "level": level,
                "score": score,
                "progress_data": progress_data,
                "last_played": last_played
            }
            action = "added"

        return {
            "success": True,
            "message": f"Game progress for user {user_id} & game {game_id} {action}."
        }

    def delete_user_account(self, user_id: str, requester_id: str) -> dict:
        """
        Permanently remove a user and all associated data (admin only).

        Args:
            user_id (str): The ID of the user to delete.
            requester_id (str): The ID of the user performing the operation (for admin check).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User and associated data permanently removed." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only an administrator can perform this operation.
            - All associated data (profile, achievements, game progress) is also removed.
            - Operation must not leak any credentials or sensitive values.
            - If user does not exist, return error.
        """
        # Verify requester exists and is admin
        admin_status = False
        requester_info = self.users.get(requester_id)
        if requester_info and requester_info.get("account_status", "").lower() == "admin":
            admin_status = True

        if not admin_status:
            return { "success": False, "error": "Permission denied: administrator rights required." }

        # Check if target user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }

        # Delete user record
        del self.users[user_id]

        # Delete user profile
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]

        # Delete all achievements for this user
        achievements_to_delete = [aid for aid, ach in self.achievements.items() if ach["user_id"] == user_id]
        for aid in achievements_to_delete:
            del self.achievements[aid]

        # Delete all game progress for this user
        game_progress_to_delete = [gpid for gpid, gp in self.game_progress.items() if gp["_id"].startswith(user_id)]
        for gpid in game_progress_to_delete:
            del self.game_progress[gpid]

        return { "success": True, "message": "User and associated data permanently removed." }

    def change_user_password(
        self,
        requesting_user_id: str,
        target_user_id: str,
        new_password_hash: str,
        admin_override: bool = False
    ) -> dict:
        """
        Update a user's password (as hash). Only the user themselves or an admin may attempt this.
        Restrictions:
          - Only self-service or admin may change a user's password.
          - Account must exist.
          - For non-admin, account_status must not be suspended/banned.
          - The new password_hash must not be empty.
          - Password is stored as a hash (never plaintext).

        Args:
            requesting_user_id (str): The user performing the operation.
            target_user_id (str): The account whose password is to be changed.
            new_password_hash (str): The new password hash value (must not be blank).
            admin_override (bool): If True, requesting user acts as admin.

        Returns:
            dict: {
              "success": True,
              "message": "Password updated successfully"
            }
            OR
            dict: {
              "success": False,
              "error": "<reason>"
            }
        """
        # Check user existence
        if target_user_id not in self.users:
            return { "success": False, "error": "Target user does not exist" }
        target_user = self.users[target_user_id]
        # Check requesting user
        if requesting_user_id not in self.users:
            return { "success": False, "error": "Requesting user does not exist" }

        # Permissions: must be self or admin
        is_self = requesting_user_id == target_user_id
        if not is_self and not admin_override:
            return { "success": False, "error": "Permission denied: not self or no admin rights" }

        # Target account status checks
        account_status = target_user["account_status"].lower()
        if account_status in ["banned", "suspended"]:
            # For admin, optionally allow for 'suspended', but likely not for 'banned'
            if not admin_override or account_status == "banned":
                return { "success": False, "error": f"Account status '{account_status}' prohibits password change" }

        # Password hash validation (never plaintext, not empty)
        if not isinstance(new_password_hash, str) or not new_password_hash.strip():
            return { "success": False, "error": "New password hash must be a non-empty string" }

        # If all checks pass, perform update
        target_user["password_hash"] = new_password_hash
        # (Optionally update password change metadata here...)

        return { "success": True, "message": "Password updated successfully" }

    def remove_user_achievement(self, achievement_id: str, requester_id: str) -> dict:
        """
        Delete an achievement from the user's record.

        Args:
            achievement_id (str): The ID of the achievement to delete.
            requester_id (str): The ID of the user making the delete request.

        Returns:
            dict: {
                "success": True,
                "message": "Achievement removed from user record."
            }
            OR
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Achievement must exist.
            - Only the owner (achievement.user_id) or a platform admin can remove the achievement.
            - Account status may restrict access (e.g., banned/suspended users may not perform actions).
        """

        # Helper: check if requester is admin
        def is_admin(user_id: str) -> bool:
            # Example implementation: (in practice, we'd check specific fields/roles; here just stub)
            user = self.users.get(user_id)
            if not user:
                return False
            return user.get("account_status") == "admin"

        if achievement_id not in self.achievements:
            return {"success": False, "error": "Achievement does not exist."}

        achievement = self.achievements[achievement_id]
        achievement_owner = achievement["user_id"]
        requester = self.users.get(requester_id)

        if requester is None:
            return {"success": False, "error": "Requester user does not exist."}

        # Only achievement owner or admin may remove
        if requester_id != achievement_owner and not is_admin(requester_id):
            return {"success": False, "error": "Permission denied. Only achievement owner or admin may remove achievements."}

        # Optional: Check account status (e.g., only 'active' accounts may self-remove achievements)
        if requester_id == achievement_owner and requester.get("account_status") != "active":
            return {"success": False, "error": "User account is not active."}

        # Remove the achievement
        del self.achievements[achievement_id]
        return {"success": True, "message": "Achievement removed from user record."}

    def reset_user_preferences(self, user_id: str) -> dict:
        """
        Restore a user's preferences to platform defaults.

        Args:
            user_id (str): Unique identifier of the user whose preferences will be reset.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Preferences reset to platform defaults."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - The user must exist.
            - The user's account_status must be 'active'.
            - Platform default preferences should be applied.
        """
        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # Check account status
        if user.get("account_status") != "active":
            return {"success": False, "error": f"Account status is '{user.get('account_status')}', operation not permitted."}

        # Get platform defaults
        default_preferences = getattr(self, "default_preferences", {})
        if not isinstance(default_preferences, dict):
            return {"success": False, "error": "Platform default preferences are not configured."}

        # Reset preferences
        user["preferences"] = default_preferences.copy()
        self.users[user_id] = user  # Update record explicitly (depends on implementation, but safe)

        return {"success": True, "message": "Preferences reset to platform defaults."}


class OnlineGamingUserManagementSystem(BaseEnv):
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
            if key == "check_user_permission":
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_profile(self, **kwargs):
        return self._call_inner_tool('get_user_profile', kwargs)

    def get_user_achievements(self, **kwargs):
        return self._call_inner_tool('get_user_achievements', kwargs)

    def get_user_game_progress(self, **kwargs):
        return self._call_inner_tool('get_user_game_progress', kwargs)

    def list_users_by_status(self, **kwargs):
        return self._call_inner_tool('list_users_by_status', kwargs)

    def get_account_status(self, **kwargs):
        return self._call_inner_tool('get_account_status', kwargs)

    def search_users_by_username(self, **kwargs):
        return self._call_inner_tool('search_users_by_username', kwargs)

    def check_user_permission(self, **kwargs):
        return self._call_inner_tool('check_user_permission', kwargs)

    def register_new_user(self, **kwargs):
        return self._call_inner_tool('register_new_user', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def update_account_status(self, **kwargs):
        return self._call_inner_tool('update_account_status', kwargs)

    def add_user_achievement(self, **kwargs):
        return self._call_inner_tool('add_user_achievement', kwargs)

    def update_game_progress(self, **kwargs):
        return self._call_inner_tool('update_game_progress', kwargs)

    def delete_user_account(self, **kwargs):
        return self._call_inner_tool('delete_user_account', kwargs)

    def change_user_password(self, **kwargs):
        return self._call_inner_tool('change_user_password', kwargs)

    def remove_user_achievement(self, **kwargs):
        return self._call_inner_tool('remove_user_achievement', kwargs)

    def reset_user_preferences(self, **kwargs):
        return self._call_inner_tool('reset_user_preferences', kwargs)
