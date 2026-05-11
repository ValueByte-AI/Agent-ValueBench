# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
from typing import Optional
import time



class UserInfo(TypedDict):
    _id: str  # Globally unique user ID
    username: str  # Unique username
    display_name: str
    email: str
    bio: str
    avatar_url: str
    location: str
    account_created_at: str
    account_updated_at: str
    is_active: bool

class UserStatisticsInfo(TypedDict):
    _id: str  # User ID (foreign key to User)
    followers_count: int
    following_count: int
    public_repos_count: int
    contributions_count: int

class FollowerRelationshipInfo(TypedDict):
    follower_user_id: str  # User ID of the follower
    followed_user_id: str  # User ID of the followed
    followed_since: str    # Timestamp

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id (user_id): UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # User statistics: {_id (user_id): UserStatisticsInfo}
        self.user_statistics: Dict[str, UserStatisticsInfo] = {}

        # Follower relationships: List of FollowerRelationshipInfo
        # (Each tuple: follower_user_id follows followed_user_id)
        self.follower_relationships: List[FollowerRelationshipInfo] = []

        # Constraints:
        # - Username must be unique for each user.
        # - user_id (_id) is a globally unique identifier for each user.
        # - Users can follow or unfollow other users; cycles are allowed.
        # - Only active users (is_active=True) are returned in queries by default.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve a user's complete profile by their unique username.
        Only returns user profile if user is active.

        Args:
            username (str): The user's unique username.

        Returns:
            dict: 
              - On success: { "success": True, "data": UserInfo }
              - On failure: { "success": False, "error": "User not found or inactive" }

        Constraints:
            - Only active users (is_active=True) are returned.
            - Username must be matched exactly (case-sensitive, as typical in GitHub).
        """
        for user in self.users.values():
            if user["username"] == username:
                if user.get("is_active", False):
                    return {"success": True, "data": user}
                else:
                    return {"success": False, "error": "User not found or inactive"}
        return {"success": False, "error": "User not found or inactive"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's complete profile by their unique user ID.
        Only active users are returned by default.

        Args:
            user_id (str): The globally unique user ID.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo  # Full user profile dictionary
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (not found or not active)
                    }

        Constraints:
            - Returns only if the user exists and is active.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        if not user_info.get("is_active", False):
            return { "success": False, "error": "User is not active" }
        return { "success": True, "data": user_info }

    def list_active_users(self) -> dict:
        """
        List all active user profiles on the platform.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo]
                    # List of UserInfo dicts representing all active users.
                    # An empty list is returned if no active users exist.
                }

        Constraints:
            - Only users with is_active == True are returned.
        """
        active_users = [
            user_info for user_info in self.users.values()
            if user_info.get("is_active", False) is True
        ]
        return { "success": True, "data": active_users }

    def list_all_users(self) -> dict:
        """
        List all user profiles in the system, regardless of active/inactive status.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all user info dictionaries (may be empty if no users)
            }

        Constraints:
            - All users are returned, regardless of the `is_active` field.
        """
        all_users = list(self.users.values())
        return { "success": True, "data": all_users }

    def check_username_exists(self, username: str) -> dict:
        """
        Determine if a given username is already taken by any user (active or inactive).

        Args:
            username (str): The username to check.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": bool  # True if username exists, False otherwise
                }
                or
                {
                    "success": False,
                    "error": str  # error message if input is invalid
                }

        Constraints:
            - Username must be unique for each user.
            - Returns True if any user (active or not) has the provided username.
        """
        if not isinstance(username, str) or username.strip() == "":
            return { "success": False, "error": "Invalid username input" }

        exists = any(user["username"] == username for user in self.users.values())
        return { "success": True, "data": exists }

    def get_user_statistics(self, user_id: str) -> dict:
        """
        Retrieve the statistics (followers, following, public repos, contributions) for a specific user by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserStatisticsInfo  # If successful
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - User (user_id) must exist.
            - User must be active (is_active == True).
            - Statistics must exist for user.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }
        if not user.get("is_active", False):
            return { "success": False, "error": "User is not active" }
        stats = self.user_statistics.get(user_id)
        if stats is None:
            return { "success": False, "error": "Statistics not found for user" }
        return { "success": True, "data": stats }

    def get_followers(self, user_id: str) -> dict:
        """
        Retrieve a list of user profiles of users who actively follow the specified user.

        Args:
            user_id (str): The ID of the user whose followers should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of active followers' full profiles (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Why the query could not complete.
            }

        Constraints:
            - Only active users are returned in queries by default (both the target and their followers).
        """
        # Check that the target user exists and is active
        user_info = self.users.get(user_id)
        if not user_info or not user_info.get("is_active", False):
            return { "success": False, "error": "User not found or not active" }
    
        follower_user_ids = [
            rel["follower_user_id"]
            for rel in self.follower_relationships
            if rel["followed_user_id"] == user_id
        ]

        active_follower_profiles = [
            self.users[fid]
            for fid in follower_user_ids
            if fid in self.users and self.users[fid].get("is_active", False)
        ]

        return { "success": True, "data": active_follower_profiles }

    def get_following(self, user_id: str) -> dict:
        """
        Retrieve a list of user profiles (UserInfo) of users whom the specified user is following.
        Only active users are returned in the results.

        Args:
            user_id (str): The ID of the user whose following list to query.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[UserInfo],  # List of profiles followed by user_id (and active)
                }
                or
                {
                    "success": False,
                    "error": str  # Error message, e.g., user not found
                }

        Constraints:
            - user_id must exist in self.users.
            - Only active users are returned in results.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        following_ids = [
            rel["followed_user_id"]
            for rel in self.follower_relationships
            if rel["follower_user_id"] == user_id
        ]
        # Only return those followed users whose profiles are active and exist
        result = [
            self.users[fid]
            for fid in following_ids
            if fid in self.users and self.users[fid]["is_active"]
        ]

        return { "success": True, "data": result }

    def get_follower_relationship(self, follower_user_id: str, followed_user_id: str) -> dict:
        """
        Check if a follower relationship exists between two users and retrieve its details.

        Args:
            follower_user_id (str): User ID of the follower.
            followed_user_id (str): User ID of the followed.

        Returns:
            dict: {
                "success": True, 
                "data": FollowerRelationshipInfo  # If the relationship exists.
            }
            or
            {
                "success": False,
                "error": str  # If one/both users do not exist or no such relationship.
            }

        Constraints:
            - Both user IDs must exist in the user database.
            - Returns only the first matching relationship if any (should be unique by system design).
        """
        if follower_user_id not in self.users or followed_user_id not in self.users:
            return { "success": False, "error": "One or both user IDs do not exist" }

        for rel in self.follower_relationships:
            if (
                rel["follower_user_id"] == follower_user_id and
                rel["followed_user_id"] == followed_user_id
            ):
                return { "success": True, "data": rel }

        return { "success": False, "error": "Follower relationship does not exist" }


    def update_user_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        location: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """
        Update a user's profile information.

        Args:
            user_id (str): Globally unique user ID.
            display_name (Optional[str]): New display name.
            bio (Optional[str]): New bio.
            avatar_url (Optional[str]): New avatar URL.
            location (Optional[str]): New location.
            email (Optional[str]): New email address.

        Returns:
            dict: {
                "success": True,
                "message": "User profile updated"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Only updatable fields: display_name, bio, avatar_url, location, email.
            - Updates account_updated_at timestamp to now.
            - User must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        user = self.users[user_id]
        updatable_fields = ["display_name", "bio", "avatar_url", "location", "email"]
        updated = False

        # Only update the fields that are not None and are permitted
        if display_name is not None:
            user["display_name"] = display_name
            updated = True
        if bio is not None:
            user["bio"] = bio
            updated = True
        if avatar_url is not None:
            user["avatar_url"] = avatar_url
            updated = True
        if location is not None:
            user["location"] = location
            updated = True
        if email is not None:
            user["email"] = email
            updated = True

        if not updated:
            return { "success": False, "error": "No profile fields to update" }

        # Update account_updated_at timestamp to now
        user["account_updated_at"] = datetime.utcnow().isoformat() + "Z"

        self.users[user_id] = user
        return { "success": True, "message": "User profile updated" }

    def set_user_active_status(self, user_id: str, is_active: bool) -> dict:
        """
        Activate or deactivate a user account (toggle is_active).

        Args:
            user_id (str): The unique ID of the user to update.
            is_active (bool): The desired activity status (True=activate, False=deactivate).

        Returns:
            dict: {
                "success": True,
                "message": "User active status updated."
            }
            or
            {
                "success": False,
                "error": "User not found."
            }

        Constraints:
            - Only existing users' statuses can be changed.
            - Returns success even if updating to the same value.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }
        self.users[user_id]['is_active'] = is_active
        return { "success": True, "message": "User active status updated." }

    def change_username(self, user_id: str, new_username: str) -> dict:
        """
        Change a user's username to a new, unique value.

        Args:
            user_id (str): Unique ID of the user to rename.
            new_username (str): Desired new username. Must be unique.

        Returns:
            dict:
                - On success: {"success": True, "message": "Username changed successfully"}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The user must exist.
            - The new username must not already be taken by another user.
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User ID does not exist" }

        # If new_username is current username of this user, treat as success (no change)
        if user["username"] == new_username:
            return { "success": True, "message": "Username is already set to the new value" }

        # Check for uniqueness of new_username across all users
        for info in self.users.values():
            if info["username"] == new_username:
                return { "success": False, "error": "Username already in use" }

        # Passed constraints, proceed with update
        user["username"] = new_username
        # If needed, update account_updated_at (not specified, but could be done)

        return { "success": True, "message": "Username changed successfully" }


    def follow_user(self, follower_user_id: str, followed_user_id: str) -> dict:
        """
        Create a new follower relationship: user with follower_user_id follows user with followed_user_id.

        Args:
            follower_user_id (str): User ID of the follower.
            followed_user_id (str): User ID of the followed.

        Returns:
            dict:
                Success: { "success": True, "message": "User <follower_user_id> now follows user <followed_user_id>." }
                Failure: { "success": False, "error": <error_message> }
        Constraints:
            - Both users must exist and be active.
            - A user cannot follow themselves.
            - The follower relationship must not already exist.
            - On success, statistics are updated accordingly.
        """

        # Check existence and active status
        follower = self.users.get(follower_user_id)
        followed = self.users.get(followed_user_id)
        if not follower:
            return { "success": False, "error": "Follower user does not exist." }
        if not followed:
            return { "success": False, "error": "Followed user does not exist." }
        if not follower["is_active"]:
            return { "success": False, "error": "Follower user is not active." }
        if not followed["is_active"]:
            return { "success": False, "error": "Followed user is not active." }
        if follower_user_id == followed_user_id:
            return { "success": False, "error": "A user cannot follow themselves." }

        # Check if relationship already exists
        for rel in self.follower_relationships:
            if rel["follower_user_id"] == follower_user_id and rel["followed_user_id"] == followed_user_id:
                return { "success": False, "error": "Follower relationship already exists." }

        # Establish timestamp (ISO 8601 string)
        now = datetime.utcnow().isoformat() + "Z"

        # Add the new follower relationship
        new_relationship = {
            "follower_user_id": follower_user_id,
            "followed_user_id": followed_user_id,
            "followed_since": now
        }
        self.follower_relationships.append(new_relationship)

        # Update UserStatistics
        if follower_user_id in self.user_statistics:
            self.user_statistics[follower_user_id]["following_count"] += 1
        if followed_user_id in self.user_statistics:
            self.user_statistics[followed_user_id]["followers_count"] += 1

        return {
            "success": True,
            "message": f"User {follower_user_id} now follows user {followed_user_id}."
        }

    def unfollow_user(self, follower_user_id: str, followed_user_id: str) -> dict:
        """
        Remove an existing follower relationship: user A ('follower_user_id') unfollows user B ('followed_user_id').

        Args:
            follower_user_id (str): ID of the user performing the unfollow.
            followed_user_id (str): ID of the user to be unfollowed.

        Returns:
            dict: {
                "success": True,
                "message": "User <follower_user_id> has unfollowed user <followed_user_id>"
            }
            OR
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - Both users must exist and be active.
            - A follower relationship must exist.
            - Updates follower/following counts consistently.
        """

        # Check users exist
        user_a = self.users.get(follower_user_id)
        user_b = self.users.get(followed_user_id)
        if not user_a:
            return {"success": False, "error": "Follower user does not exist"}
        if not user_b:
            return {"success": False, "error": "Followed user does not exist"}

        # Check both users are active
        if not user_a["is_active"]:
            return {"success": False, "error": "Follower user is not active"}
        if not user_b["is_active"]:
            return {"success": False, "error": "Followed user is not active"}

        # Cannot unfollow self?
        if follower_user_id == followed_user_id:
            return {"success": False, "error": "User cannot unfollow themselves"}

        # Find and remove the follower relationship
        found = False
        # Remove all matches just in case (should be only one according to constraints)
        new_relationships = []
        for rel in self.follower_relationships:
            if rel["follower_user_id"] == follower_user_id and rel["followed_user_id"] == followed_user_id:
                found = True
                continue  # do not add to new_relationships: this "deletes" the rel
            new_relationships.append(rel)
        if not found:
            return {"success": False, "error": "Follower relationship does not exist"}
        self.follower_relationships = new_relationships

        # Update follower/following counts if stats exist
        follower_stats = self.user_statistics.get(follower_user_id)
        followed_stats = self.user_statistics.get(followed_user_id)
        if follower_stats:
            follower_stats["following_count"] = max(0, follower_stats["following_count"] - 1)
        if followed_stats:
            followed_stats["followers_count"] = max(0, followed_stats["followers_count"] - 1)

        return {
            "success": True,
            "message": f"User {follower_user_id} has unfollowed user {followed_user_id}"
        }

    def increment_user_statistics(self, user_id: str, stat_field: str, amount: int = 1) -> dict:
        """
        Increment a specific statistics field (followers_count, following_count, 
        public_repos_count, or contributions_count) for a given user.

        Args:
            user_id (str): The target user's unique ID.
            stat_field (str): The stats field to increment. Must be one of:
                'followers_count', 'following_count', 'public_repos_count', 'contributions_count'.
            amount (int, optional): Amount to increment by. Must be positive. Default is 1.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Statistic '<stat_field>' for user <user_id> incremented by <amount>."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - user_id must be present in user_statistics.
            - stat_field must be a valid statistics field.
            - amount must be a positive integer.
        """
        allowed_fields = {'followers_count', 'following_count', 'public_repos_count', 'contributions_count'}
        if user_id not in self.user_statistics:
            return {"success": False, "error": "User statistics not found"}
        if stat_field not in allowed_fields:
            return {"success": False, "error": f"Invalid statistics field: {stat_field}"}
        if not isinstance(amount, int) or amount <= 0:
            return {"success": False, "error": "Amount must be a positive integer"}

        stats = self.user_statistics[user_id]
        stats[stat_field] += amount
        # If needed, ensure no negative values (shouldn't be possible with only increments).
        return {
            "success": True,
            "message": f"Statistic '{stat_field}' for user {user_id} incremented by {amount}."
        }

    def decrement_user_statistics(self, user_id: str, stat_field: str) -> dict:
        """
        Decrement a specific statistic counter for a user.

        Args:
            user_id (str): User's unique ID whose statistic is to be decremented.
            stat_field (str): The statistic field to decrement 
                              ('followers_count', 'following_count', 'public_repos_count', 'contributions_count').

        Returns:
            dict: {
                "success": True,
                "message": "Decremented <stat_field> for user <user_id>."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - stat_field must be a valid statistics counter.
            - Counter must not be decremented below zero.
            - user_id must exist in user_statistics.
        """
        valid_fields = {"followers_count", "following_count", "public_repos_count", "contributions_count"}
    
        if user_id not in self.user_statistics:
            return { "success": False, "error": f"User statistics for user_id '{user_id}' not found." }
        if stat_field not in valid_fields:
            return { "success": False, "error": f"Invalid stat_field '{stat_field}'." }
    
        current_val = self.user_statistics[user_id][stat_field]
        if current_val <= 0:
            return { "success": False, "error": f"Statistic '{stat_field}' for user '{user_id}' is already zero." }
    
        self.user_statistics[user_id][stat_field] = current_val - 1
        return { "success": True, "message": f"Decremented {stat_field} for user {user_id}." }

    def create_user(
        self,
        _id: str,
        username: str,
        display_name: str,
        email: str,
        bio: str = "",
        avatar_url: str = "",
        location: str = "",
        is_active: bool = True,
        account_created_at: str = None,
        account_updated_at: str = None
    ) -> dict:
        """
        Add a new user with unique username and user_id, and initializes user statistics.

        Args:
            _id (str): Globally unique user ID.
            username (str): Unique username.
            display_name (str): Display name for the user.
            email (str): User's email.
            bio (str, optional): User bio.
            avatar_url (str, optional): URL to user's avatar.
            location (str, optional): User location.
            is_active (bool, optional): If user is active. Defaults to True.
            account_created_at (str, optional): Creation time (ISO8601). If None, uses current time.
            account_updated_at (str, optional): Last updated time (ISO8601). If None, uses current time.

        Returns:
            dict: {
                "success": True, "message": "User created successfully."
            }
            or
            {
                "success": False, "error": "reason"
            }

        Constraints:
            - Username must be unique.
            - _id (user ID) must be unique.
        """

        # Check for unique username
        for user in self.users.values():
            if user["username"] == username:
                return {"success": False, "error": "Username already exists."}

        # Check for unique user ID
        if _id in self.users:
            return {"success": False, "error": "User ID already exists."}

        # Set current time if not provided
        now_iso = datetime.utcfromtimestamp(time.time()).isoformat() + 'Z'
        if account_created_at is None:
            account_created_at = now_iso
        if account_updated_at is None:
            account_updated_at = now_iso

        # Create UserInfo
        self.users[_id] = {
            "_id": _id,
            "username": username,
            "display_name": display_name,
            "email": email,
            "bio": bio,
            "avatar_url": avatar_url,
            "location": location,
            "account_created_at": account_created_at,
            "account_updated_at": account_updated_at,
            "is_active": is_active
        }

        # Initialize user statistics
        self.user_statistics[_id] = {
            "_id": _id,
            "followers_count": 0,
            "following_count": 0,
            "public_repos_count": 0,
            "contributions_count": 0
        }

        return {"success": True, "message": "User created successfully."}


class GitHubUserManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_active_users(self, **kwargs):
        return self._call_inner_tool('list_active_users', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def check_username_exists(self, **kwargs):
        return self._call_inner_tool('check_username_exists', kwargs)

    def get_user_statistics(self, **kwargs):
        return self._call_inner_tool('get_user_statistics', kwargs)

    def get_followers(self, **kwargs):
        return self._call_inner_tool('get_followers', kwargs)

    def get_following(self, **kwargs):
        return self._call_inner_tool('get_following', kwargs)

    def get_follower_relationship(self, **kwargs):
        return self._call_inner_tool('get_follower_relationship', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def set_user_active_status(self, **kwargs):
        return self._call_inner_tool('set_user_active_status', kwargs)

    def change_username(self, **kwargs):
        return self._call_inner_tool('change_username', kwargs)

    def follow_user(self, **kwargs):
        return self._call_inner_tool('follow_user', kwargs)

    def unfollow_user(self, **kwargs):
        return self._call_inner_tool('unfollow_user', kwargs)

    def increment_user_statistics(self, **kwargs):
        return self._call_inner_tool('increment_user_statistics', kwargs)

    def decrement_user_statistics(self, **kwargs):
        return self._call_inner_tool('decrement_user_statistics', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

