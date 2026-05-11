# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime, timedelta, timezone



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    interests: List[str]
    preferences: Dict[str, str]

class HealthcareResourceInfo(TypedDict):
    resource_id: str
    title: str
    description: str
    category: str
    tags: List[str]
    content_type: str

class BookmarkInfo(TypedDict):
    _id: str
    user_id: str  # Added for many-to-many mapping
    resource_id: str
    date_bookmarked: str  # ISO timestamp as string

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a healthcare information portal.
        """
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Healthcare Resources: {resource_id: HealthcareResourceInfo}
        self.resources: Dict[str, HealthcareResourceInfo] = {}

        # Bookmarks: {user_id: List[BookmarkInfo]}
        # Each BookmarkInfo contains the user_id, resource_id, and bookmarking metadata
        self.bookmarks: Dict[str, List[BookmarkInfo]] = {}

        # Constraints:
        # - Only existing resources in the HealthcareResource catalog can be bookmarked.
        # - Each bookmark must tie a valid user to a valid resource.
        # - Duplicate bookmarks (same user and resource) should not be created.
        # - Users can only access and manage their own bookmarks.

    @staticmethod
    def _parse_controlled_datetime(value):
        if not value or not isinstance(value, str):
            return None
        text = value.strip()
        if not text or text.lower() in {"none", "null"}:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except Exception:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _next_bookmark_timestamp(self) -> str:
        explicit = self._parse_controlled_datetime(getattr(self, "current_time", None))
        if explicit is not None:
            return explicit.isoformat().replace("+00:00", "Z")

        seen = []
        for bookmark_list in self.bookmarks.values():
            for bookmark in bookmark_list:
                dt = self._parse_controlled_datetime(bookmark.get("date_bookmarked"))
                if dt is not None:
                    seen.append(dt)
        if not seen:
            base = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            base = max(seen) + timedelta(seconds=1)
        return base.isoformat().replace("+00:00", "Z")

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve detailed user profile information by user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user_id must exist in the users database.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_email(self, email: str) -> dict:
        """
        Retrieve user profile information by email address.

        Args:
            email (str): The email address to search for.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - Email matching is case-sensitive.
            - If no user with the given email exists, returns an error.
        """
        for user in self.users.values():
            if user["email"] == email:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def search_resources_by_title(self, title_query: str) -> dict:
        """
        Search healthcare resources by their title or partial title.

        Args:
            title_query (str): Search string (case-insensitive, partial match allowed).

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareResourceInfo],  # All resources whose title matches
            }

        Constraints:
            - No access or permission restrictions for searching.
            - Empty string returns all resources.
        """
        # Prepare for case-insensitive search
        query = title_query.strip().lower()
        results = [
            resource for resource in self.resources.values()
            if query in resource['title'].lower()
        ]
        return {
            "success": True,
            "data": results
        }

    def get_resource_by_id(self, resource_id: str) -> dict:
        """
        Retrieve the details of a healthcare resource given its resource_id.

        Args:
            resource_id (str): The unique identifier of the resource.

        Returns:
            dict:
                - If found: { "success": True, "data": HealthcareResourceInfo }
                - If not found: { "success": False, "error": "Resource not found" }

        Constraints:
            - The resource must exist in the resource catalog.
        """
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource not found" }
        return { "success": True, "data": self.resources[resource_id] }

    def search_resources_by_category(self, category: str) -> dict:
        """
        Find healthcare resources matching the specified category.

        Args:
            category (str): The category to filter resources by
                            (case-insensitive exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareResourceInfo] (possibly empty if no matches)
            }
            If `category` is not a string or is empty, returns:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The search is case-insensitive.
        """
        if not isinstance(category, str) or not category.strip():
            return { "success": False, "error": "Invalid or empty category" }

        category_lower = category.strip().lower()
        matches = [
            resource
            for resource in self.resources.values()
            if resource.get("category", "").strip().lower() == category_lower
        ]
        return { "success": True, "data": matches }

    def search_resources_by_tag(self, tag: str) -> dict:
        """
        Find all healthcare resources that contain the provided tag.

        Args:
            tag (str): The tag to filter the healthcare resources by.

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareResourceInfo],  # List of resources with the tag (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for error (e.g. missing tag parameter)
            }

        Notes:
            - The tag match is case-sensitive.
            - If tag is empty or None, will return an error.
        """
        if not tag or not isinstance(tag, str):
            return {"success": False, "error": "Tag parameter is required and must be a non-empty string"}

        matched = [
            res for res in self.resources.values()
            if tag in res.get('tags', [])
        ]
        return {"success": True, "data": matched}

    def list_user_bookmarks(self, user_id: str) -> dict:
        """
        List all bookmarks for a specific user.

        Args:
            user_id (str): The ID of the user whose bookmarks to retrieve.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[BookmarkInfo] }
                - On failure: { "success": False, "error": str }
    
        Constraints:
            - Only existing users' bookmarks can be listed.
            - Users can only access their own bookmarks (assumed enforced by caller).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        bookmarks = self.bookmarks.get(user_id, [])
        return { "success": True, "data": bookmarks }

    def check_bookmark_exists(self, user_id: str, resource_id: str) -> dict:
        """
        Check whether a particular healthcare resource is already bookmarked by a user.

        Args:
            user_id (str): The ID of the user.
            resource_id (str): The ID of the healthcare resource.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if bookmark exists, False otherwise
            } or {
                "success": False,
                "error": str  # If the user or resource does not exist
            }

        Constraints:
            - User must exist in the system.
            - Resource must exist in the catalog.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if resource_id not in self.resources:
            return {"success": False, "error": "Resource does not exist"}

        user_bookmarks = self.bookmarks.get(user_id, [])
        exists = any(bm["resource_id"] == resource_id for bm in user_bookmarks)

        return {"success": True, "data": exists}


    def add_bookmark(self, user_id: str, resource_id: str) -> dict:
        """
        Create a bookmark linking a user to a healthcare resource if all constraints are satisfied.

        Args:
            user_id (str): ID of the user creating the bookmark.
            resource_id (str): ID of the healthcare resource to bookmark.

        Returns:
            dict: {
                "success": True,
                "message": "Bookmark added successfully."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Both user and resource must exist.
            - Duplicate bookmarks (same user and resource) should not be created.
            - Bookmark will have a unique _id and record date_bookmarked in ISO8601 format.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check resource exists
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource does not exist." }

        # Prepare or obtain user's bookmark list
        user_bookmarks = self.bookmarks.setdefault(user_id, [])

        # Check for duplicate bookmark
        for bm in user_bookmarks:
            if bm["resource_id"] == resource_id:
                return { "success": False, "error": "Bookmark already exists." }

        # Generate unique bookmark id
        bookmark_id = str(uuid.uuid4())
        date_bookmarked = self._next_bookmark_timestamp()

        new_bookmark = {
            "_id": bookmark_id,
            "user_id": user_id,
            "resource_id": resource_id,
            "date_bookmarked": date_bookmarked
        }

        user_bookmarks.append(new_bookmark)

        return { "success": True, "message": "Bookmark added successfully." }

    def remove_bookmark(self, user_id: str, resource_id: str) -> dict:
        """
        Delete an existing bookmark for a user-resource pair.

        Args:
            user_id (str): The ID of the user whose bookmark is to be removed.
            resource_id (str): The ID of the healthcare resource to unbookmark.

        Returns:
            dict: {
                "success": True,
                "message": "Bookmark removed successfully."
            }
            or
            {
                "success": False,
                "error": "User does not exist" | "Bookmark does not exist"
            }

        Constraints:
            - Only existing resources already bookmarked by the user can be unbookmarked.
            - Users can only remove their own bookmarks.
            - Removing a non-existent bookmark is an error.
        """
        # Check for user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        bookmarks = self.bookmarks.get(user_id, [])

        # Find index of the bookmark for resource_id
        bookmark_index = next((i for i, b in enumerate(bookmarks) if b["resource_id"] == resource_id), None)

        if bookmark_index is None:
            return { "success": False, "error": "Bookmark does not exist" }

        # Remove the bookmark
        del bookmarks[bookmark_index]
        # If user has no remaining bookmarks, optionally clean up (not required)

        self.bookmarks[user_id] = bookmarks
        return { "success": True, "message": "Bookmark removed successfully." }

    def update_user_preferences(
        self,
        user_id: str,
        interests: 'Optional[List[str]]' = None,
        preferences: 'Optional[Dict[str, str]]' = None
    ) -> dict:
        """
        Update and personalize a user's preferences and/or interests.

        Args:
            user_id (str): The ID of the user to update.
            interests (Optional[List[str]]): New list of interests; replaces existing if provided.
            preferences (Optional[Dict[str, str]]): Dictionary of new/updated preferences. Only provided keys are updated.

        Returns:
            dict: {
                "success": True,
                "message": "User preferences updated."
            }
            or if user not found:
            {
                "success": False,
                "error": "User not found."
            }

        Constraints:
            - Only existing users can be updated.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}
    
        user = self.users[user_id]
        updated = False

        if interests is not None:
            user['interests'] = interests
            updated = True

        if preferences is not None:
            if 'preferences' not in user or not isinstance(user['preferences'], dict):
                user['preferences'] = {}
            user['preferences'].update(preferences)
            updated = True

        self.users[user_id] = user  # Store the updated user info

        if updated:
            return {"success": True, "message": "User preferences updated."}
        else:
            return {"success": True, "message": "No changes made to user preferences."}

    def clear_all_user_bookmarks(self, user_id: str) -> dict:
        """
        Remove all bookmarks for a specific user.

        Args:
            user_id (str): The unique ID of the user whose bookmarks are to be cleared.

        Returns:
            dict: {
                "success": True,
                "message": "All bookmarks cleared for user <user_id>."
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User does not exist"
            }

        Constraints:
            - Only existing users can have their bookmarks cleared.
            - Operation only affects the bookmarks of the specified user.
            - If the user has no bookmarks, the operation is still considered successful (idempotent).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Clear all bookmarks for this user
        self.bookmarks[user_id] = []

        return { "success": True, "message": f"All bookmarks cleared for user {user_id}." }


class HealthcareInformationPortal(BaseEnv):
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

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def search_resources_by_title(self, **kwargs):
        return self._call_inner_tool('search_resources_by_title', kwargs)

    def get_resource_by_id(self, **kwargs):
        return self._call_inner_tool('get_resource_by_id', kwargs)

    def search_resources_by_category(self, **kwargs):
        return self._call_inner_tool('search_resources_by_category', kwargs)

    def search_resources_by_tag(self, **kwargs):
        return self._call_inner_tool('search_resources_by_tag', kwargs)

    def list_user_bookmarks(self, **kwargs):
        return self._call_inner_tool('list_user_bookmarks', kwargs)

    def check_bookmark_exists(self, **kwargs):
        return self._call_inner_tool('check_bookmark_exists', kwargs)

    def add_bookmark(self, **kwargs):
        return self._call_inner_tool('add_bookmark', kwargs)

    def remove_bookmark(self, **kwargs):
        return self._call_inner_tool('remove_bookmark', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def clear_all_user_bookmarks(self, **kwargs):
        return self._call_inner_tool('clear_all_user_bookmarks', kwargs)
