# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict



class UserInfo(TypedDict):
    _id: str
    username: str
    profile_info: str
    account_sta: str  # Likely 'account_status'

class ContentInfo(TypedDict):
    content_id: str
    user_id: str
    content_type: str
    data: str
    created_at: str
    visibility_sta: str  # Likely 'visibility_status'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment to manage users and their associated content.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Contents: {content_id: ContentInfo}
        self.contents: Dict[str, ContentInfo] = {}

        # Constraints (to enforce in future methods):
        # - Each content item must be associated with a valid, existing user_id.
        # - Content visibility and retrieval must respect the content's visibility_sta (status).
        # - content_type must be defined and valid (e.g., "highlight", "post", "media").

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for a given user ID.

        Args:
            user_id (str): The unique identifier (_id) of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,    # User information for the provided user ID
            }
            or
            {
                "success": False,
                "error": str         # Error message if user not found
            }

        Constraints:
            - user_id must exist in the user records.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information for a specific username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User's info if username exists
            }
            or
            {
                "success": False,
                "error": str  # If username not found
            }

        Constraints:
            - Username must exist in the system.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "Username not found" }

    def list_all_users(self) -> dict:
        """
        Retrieve information on all users in the system.

        Returns:
            dict:
                - success (bool): True if retrieval is successful.
                - data (List[UserInfo]): List of user records (may be empty if no users present).
        """
        all_users = list(self.users.values())
        return {
            "success": True,
            "data": all_users
        }

    def get_content_by_id(self, content_id: str) -> dict:
        """
        Retrieve a specific content item by its content_id.

        Args:
            content_id (str): The unique identifier for the content item.

        Returns:
            dict: {
                "success": True,
                "data": ContentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - content_id must exist in the system (self.contents).
        """
        content = self.contents.get(content_id)
        if content is None:
            return {"success": False, "error": "Content item does not exist."}
        return {"success": True, "data": content}

    def get_user_content(self, user_id: str) -> dict:
        """
        Retrieve all content items (with their metadata) associated with a specific user ID.

        Args:
            user_id (str): The unique ID of the user whose content should be retrieved.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ContentInfo],  # May be empty if user has no content
                    }
                On failure (e.g., user does not exist):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The user_id must correspond to an existing user in the system.
            - All content for the user is returned (regardless of visibility).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_content = [
            content_info for content_info in self.contents.values()
            if content_info["user_id"] == user_id
        ]

        return {"success": True, "data": user_content}

    def get_user_content_by_type(self, user_id: str, content_type: str) -> dict:
        """
        Retrieve all content items of a specific type for a given user.

        Args:
            user_id (str): The unique identifier of the user.
            content_type (str): Type of content to retrieve (e.g., 'highlight', 'post', 'media').

        Returns:
            dict: {
                "success": True,
                "data": List[ContentInfo],  # List of ContentInfo dicts (empty list if no match)
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - The given user_id must exist in the system.
            - Returns only exact matches for content_type.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            content for content in self.contents.values()
            if content['user_id'] == user_id and content['content_type'] == content_type
        ]

        return { "success": True, "data": result }


    def filter_content_by_visibility(self, content_ids: List[str], visibility_status: str) -> dict:
        """
        Filter a given list of content items by the specified visibility status.

        Args:
            content_ids (List[str]): A list of content IDs to filter.
            visibility_status (str): The required visibility status ('public', 'private', etc.).

        Returns:
            dict: {
                "success": True,
                "data": List[ContentInfo]  # All matching content,
            }

        Notes:
            - Ignores any content_ids that do not exist in the system.
            - Returns only contents that match the visibility_status.
            - Returns an empty list if no items match.
        """
        filtered = [
            self.contents[cid]
            for cid in content_ids
            if cid in self.contents and self.contents[cid]["visibility_sta"] == visibility_status
        ]
        return {"success": True, "data": filtered}

    def validate_content_type(self, content_type: str) -> dict:
        """
        Check if a given content_type is valid per environment rules.

        Args:
            content_type (str): The content_type to validate ("highlight", "post", "media").

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if content_type is valid, False otherwise
            }

        Constraints:
            - Valid content_types are "highlight", "post", "media".
        """
        valid_types = {"highlight", "post", "media"}

        # If content_type is not a string, treat as invalid
        if not isinstance(content_type, str):
            return { "success": True, "data": False }

        return { "success": True, "data": content_type in valid_types }

    def check_content_user_exists(self, content_id: str) -> dict:
        """
        Validate whether the content item's user_id refers to an existing user.

        Args:
            content_id (str): The identifier of the content item.

        Returns:
            dict: 
                Success and user existence: { "success": True, "data": { "user_exists": bool } }
                If content does not exist: { "success": False, "error": str }

        Constraints:
            - The content_id must exist in the contents.
            - Checks if the referenced user_id exists among users.
        """
        content_info = self.contents.get(content_id)
        if not content_info:
            return { "success": False, "error": "Content with the given content_id does not exist" }
        user_id = content_info["user_id"]
        user_exists = user_id in self.users
        return { "success": True, "data": { "user_exists": user_exists } }

    def create_content(
        self,
        content_id: str,
        user_id: str,
        content_type: str,
        data: str,
        created_at: str,
        visibility_sta: str
    ) -> dict:
        """
        Add a new content item to the system.

        Args:
            content_id (str): Unique identifier for the new content.
            user_id (str): ID of the user to associate the content with (must exist).
            content_type (str): One of "highlight", "post", "media".
            data (str): The content data.
            created_at (str): Creation timestamp (string format).
            visibility_sta (str): Content visibility setting, e.g., "public" or "private".
        
        Returns:
            dict:
                On success: { "success": True, "message": "Content created successfully" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - content_id must be unique.
            - user_id must exist.
            - content_type must be valid ("highlight", "post", "media").
        """
        # Enforce unique content_id
        if content_id in self.contents:
            return { "success": False, "error": "Content ID already exists" }

        # Enforce user_id exists
        if user_id not in self.users:
            return { "success": False, "error": "Associated user_id does not exist" }

        # Enforce valid content_type
        allowed_types = {"highlight", "post", "media"}
        if content_type not in allowed_types:
            return { "success": False, "error": "Invalid content_type" }

        # Passed all checks, create the content item
        self.contents[content_id] = {
            "content_id": content_id,
            "user_id": user_id,
            "content_type": content_type,
            "data": data,
            "created_at": created_at,
            "visibility_sta": visibility_sta,
        }

        return { "success": True, "message": "Content created successfully" }

    def update_content_visibility(self, content_id: str, visibility_sta: str) -> dict:
        """
        Change the `visibility_sta` attribute of a content item.

        Args:
            content_id (str): The identifier of the content item to update.
            visibility_sta (str): The new visibility status (e.g., "public", "private").

        Returns:
            dict: {
                "success": True,
                "message": "Visibility status updated for content <content_id>"
            }
            or
            {
                "success": False,
                "error": "Content not found"
            }

        Constraints:
            - The content item must exist.
            - visibility_sta should be a non-empty string (no further validation imposed here).
        """
        content = self.contents.get(content_id)
        if not content:
            return { "success": False, "error": "Content not found" }
        if not isinstance(visibility_sta, str) or not visibility_sta.strip():
            return { "success": False, "error": "Invalid visibility status" }

        content["visibility_sta"] = visibility_sta
        return {
            "success": True,
            "message": f"Visibility status updated for content {content_id}"
        }

    def delete_content(self, content_id: str) -> dict:
        """
        Remove an existing content item from the system.

        Args:
            content_id (str): The unique ID of the content to delete.

        Returns:
            dict: 
                { "success": True, "message": "Content <content_id> deleted." }
                OR
                { "success": False, "error": "Content not found." }

        Constraints:
            - The content_id must exist in the current contents.
        """
        if content_id not in self.contents:
            return { "success": False, "error": "Content not found." }
    
        del self.contents[content_id]
        return { "success": True, "message": f"Content {content_id} deleted." }

    def update_content_data(self, content_id: str, new_data: str) -> dict:
        """
        Modify the data payload of a specific content item.

        Args:
            content_id (str): The unique identifier of the content to update.
            new_data (str): The new data payload to store in the content.

        Returns:
            dict:
                On success: { "success": True, "message": "Content data updated successfully." }
                On failure: { "success": False, "error": "Content not found." }

        Constraints:
            - The specified content_id must exist in the system.
        """
        if content_id not in self.contents:
            return { "success": False, "error": "Content not found." }

        self.contents[content_id]["data"] = new_data
        return { "success": True, "message": "Content data updated successfully." }

    def create_user(self, _id: str, username: str, profile_info: str, account_sta: str) -> dict:
        """
        Add a new user account to the system.

        Args:
            _id (str): Unique identifier for the user.
            username (str): Username of the user.
            profile_info (str): Profile information for the user.
            account_sta (str): Account status (e.g., "active", "inactive").

        Returns:
            dict: {
                "success": True,
                "message": "User created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - _id must be unique within the users.
        """
        if _id in self.users:
            return {"success": False, "error": "User with the given _id already exists."}

        new_user = {
            "_id": _id,
            "username": username,
            "profile_info": profile_info,
            "account_sta": account_sta
        }
        self.users[_id] = new_user

        return {"success": True, "message": "User created successfully."}

    def update_user_profile(self, user_id: str, profile_info: str = None, account_sta: str = None) -> dict:
        """
        Update the profile information and/or account status for a user.

        Args:
            user_id (str): The ID of the user to update.
            profile_info (str, optional): New profile info to set (if given).
            account_sta (str, optional): New account status to set (if given).

        Returns:
            dict:
                On success: { "success": True, "message": "User profile updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - At least one of profile_info or account_sta must be provided.
            - Unspecified fields are not changed.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        if profile_info is None and account_sta is None:
            return { "success": False, "error": "No update data provided" }
    
        user = self.users[user_id]
        if profile_info is not None:
            user["profile_info"] = profile_info
        if account_sta is not None:
            user["account_sta"] = account_sta
    
        self.users[user_id] = user  # Save back, not strictly necessary for dicts but explicit.
        return { "success": True, "message": "User profile updated" }

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user by their user_id and delete all content associated with their account.

        Args:
            user_id (str): The _id of the user to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "User and associated content deleted"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The user must exist in the system.
            - All content associated with this user must also be removed.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Remove all content with this user_id
        to_delete = [cid for cid, info in self.contents.items() if info["user_id"] == user_id]
        for cid in to_delete:
            del self.contents[cid]

        # Remove the user
        del self.users[user_id]

        return { "success": True, "message": "User and associated content deleted" }


class UserContentManagementSystem(BaseEnv):
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

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_content_by_id(self, **kwargs):
        return self._call_inner_tool('get_content_by_id', kwargs)

    def get_user_content(self, **kwargs):
        return self._call_inner_tool('get_user_content', kwargs)

    def get_user_content_by_type(self, **kwargs):
        return self._call_inner_tool('get_user_content_by_type', kwargs)

    def filter_content_by_visibility(self, **kwargs):
        return self._call_inner_tool('filter_content_by_visibility', kwargs)

    def validate_content_type(self, **kwargs):
        return self._call_inner_tool('validate_content_type', kwargs)

    def check_content_user_exists(self, **kwargs):
        return self._call_inner_tool('check_content_user_exists', kwargs)

    def create_content(self, **kwargs):
        return self._call_inner_tool('create_content', kwargs)

    def update_content_visibility(self, **kwargs):
        return self._call_inner_tool('update_content_visibility', kwargs)

    def delete_content(self, **kwargs):
        return self._call_inner_tool('delete_content', kwargs)

    def update_content_data(self, **kwargs):
        return self._call_inner_tool('update_content_data', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

