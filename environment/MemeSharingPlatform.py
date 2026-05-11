# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import random
from typing import Optional, Dict
import uuid
from typing import List, Dict
import time



class MemeInfo(TypedDict):
    meme_id: str
    title: str
    image_url: str
    genre: str
    upload_date: str
    uploader_id: str
    views: int
    upvotes: int
    downvotes: int
    tag: str

class UserInfo(TypedDict):
    _id: str
    username: str
    uploaded_memes: List[str]
    favorite_memes: List[str]
    created_l: str  # assuming this is a creation timestamp

class UserListInfo(TypedDict):
    list_id: str
    user_id: str
    name: str
    meme_ids: List[str]
    creation_da: str  # assuming this is a creation date

class TrendingListInfo(TypedDict):
    period: str  # e.g., 'day', 'week', 'month'
    genre: str
    ranked_meme_ids: List[str]
    generation_timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a meme-sharing platform.

        State attributes:
        - memes: meme entities and metadata
        - users: user accounts and their meme relationships
        - user_lists: user-created meme collections
        - trending_lists: genre- and period-specific trending meme data
        """

        # Memes: {meme_id: MemeInfo}
        self.memes: Dict[str, MemeInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # User-generated lists: {list_id: UserListInfo}
        self.user_lists: Dict[str, UserListInfo] = {}

        # Trending lists: {(period, genre): TrendingListInfo}
        # We'll use a string key f"{period}:{genre}" for simplicity
        self.trending_lists: Dict[str, TrendingListInfo] = {}

        # Constraints:
        # - Each meme must belong to at least one genre.
        # - Memes are ranked by a combination of upvotes, downvotes, and/or views to determine "top" status.
        # - Random meme selection by genre uses all memes with that genre.
        # - Only existing memes can be listed or retrieved.
        # - User-generated lists reference existing memes and are linked to the owner user.

    def list_memes_by_genre(self, genre: str) -> dict:
        """
        Return all memes (with metadata) that have the specified genre.

        Args:
            genre (str): The genre to filter memes by.

        Returns:
            dict: {
                "success": True,
                "data": List[MemeInfo]  # list of meme dictionaries with matching genre (may be empty)
            }

        Constraints:
            - Each meme must belong to at least one genre.
            - Only existing memes can be listed.
            - If no memes have the specified genre, data is an empty list.
        """
        result = [
            meme for meme in self.memes.values()
            if meme['genre'] == genre
        ]
        return {"success": True, "data": result}

    def get_top_memes_by_genre(self, genre: str) -> dict:
        """
        Return memes of a specific genre, sorted by (upvotes - downvotes), then by views descending.

        Args:
            genre (str): The genre to filter and rank memes by.

        Returns:
            dict:
                success (bool): True if operation is successful.
                data (List[MemeInfo]): Ranked list of memes matching the genre.
                OR
                success (bool): False if genre is missing.
                error (str): Error description.
        Constraints:
            - Only existing memes with the specified genre are considered.
        """
        if not genre or not isinstance(genre, str):
            return { "success": False, "error": "Genre must be specified as a non-empty string." }

        # Select memes by genre
        matching_memes = [
            meme for meme in self.memes.values()
            if meme.get("genre") == genre
        ]

        # Rank: primary key (upvotes - downvotes), secondary key views, both descending
        matching_memes_sorted = sorted(
            matching_memes,
            key=lambda m: (m.get("upvotes", 0) - m.get("downvotes", 0), m.get("views", 0)),
            reverse=True
        )

        return {
            "success": True,
            "data": matching_memes_sorted
        }

    def get_trending_list(self, period: str, genre: str) -> dict:
        """
        Retrieve the precomputed trending list for the given period and genre.

        Args:
            period (str): Time period, e.g., 'day', 'week', 'month'.
            genre (str): Genre/category for which trending memes are requested.

        Returns:
            dict: 
                {"success": True, "data": TrendingListInfo}
                OR
                {"success": False, "error": str}

        Constraints:
            - Trending list must exist for the specified period and genre.
            - Only existing memes are referenced in trending lists (assumed constructed correctly).
        """
        key = f"{period}:{genre}"
        if key not in self.trending_lists:
            return {
                "success": False,
                "error": "No trending list found for that period and genre"
            }
        return {
            "success": True,
            "data": self.trending_lists[key]
        }


    def get_random_meme_by_genre(self, genre: str) -> Dict[str, object]:
        """
        Return a random meme (full MemeInfo) from all memes of a specified genre.

        Args:
            genre (str): The genre to filter memes by.

        Returns:
            dict:
                On success:
                    {"success": True, "data": MemeInfo}
                On failure (no memes for genre):
                    {"success": False, "error": "No memes found for specified genre"}

        Constraints:
            - Only memes whose 'genre' matches the input are considered.
            - If no such memes exist, returns failure.
        """
        matching_memes = [
            meme for meme in self.memes.values()
            if meme.get("genre") == genre
        ]
        if not matching_memes:
            return {"success": False, "error": "No memes found for specified genre"}

        chosen = random.choice(matching_memes)
        return {"success": True, "data": chosen}

    def get_meme_details(self, meme_id: str) -> dict:
        """
        Retrieve all metadata for a specific meme by its meme_id.

        Args:
            meme_id (str): The unique ID of the meme to retrieve.

        Returns:
            dict: 
                - On success: {"success": True, "data": MemeInfo}
                - On failure: {"success": False, "error": "Meme does not exist"}

        Constraints:
            - Only existing memes can be retrieved.
        """
        meme = self.memes.get(meme_id)
        if meme is None:
            return { "success": False, "error": "Meme does not exist" }
        return { "success": True, "data": meme }

    def list_all_genres(self) -> dict:
        """
        Return a list of all distinct genres currently represented among memes.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[str],  # List of unique genres
                }
                On error, returns:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only genres of existing memes are included.
            - Duplicates are removed; each genre appears once.
        """
        genres = set()
        for meme in self.memes.values():
            if meme["genre"]:
                genres.add(meme["genre"])
        # Return as sorted for consistency
        return { "success": True, "data": sorted(genres) }

    def get_user_info_by_username(self, username: str) -> dict:
        """
        Retrieve a user profile (UserInfo) given their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user's information, if found.
            }
            or
            {
                "success": False,
                "error": str  # Error description if user not found.
            }

        Constraints:
            - Returns the user's info if a unique username match is found.
            - If no match, returns not found.
            - Username lookup is case-sensitive.
        """
        if not username or not isinstance(username, str):
            return {"success": False, "error": "Invalid or empty username"}

        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_uploaded_memes(self, user_id: str) -> dict:
        """
        List all existing MemeInfo records for memes uploaded by a particular user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[MemeInfo],    # List of meme info (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g. user does not exist)
            }

        Constraints:
            - Only existing memes can be listed/retrieved.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }

        uploaded_memes = user.get("uploaded_memes", [])
        result = [
            self.memes[meme_id]
            for meme_id in uploaded_memes
            if meme_id in self.memes
        ]
        return { "success": True, "data": result }

    def get_user_favorite_memes(self, username: str) -> dict:
        """
        List all memes a user has favorited.

        Args:
            username (str): The username of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[MemeInfo],  # All favorited memes by this user (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # e.g., 'User not found'
            }

        Constraints:
            - Only memes that exist in the platform will be returned.
            - If user does not exist, returns error.
        """
        # Find user by username
        user = None
        for u in self.users.values():
            if u["username"] == username:
                user = u
                break
        if not user:
            return { "success": False, "error": "User not found" }

        favorite_memes = user.get("favorite_memes", [])
        result = [self.memes[meme_id] for meme_id in favorite_memes if meme_id in self.memes]

        return { "success": True, "data": result }

    def list_user_generated_lists(self, user_id: str) -> dict:
        """
        Retrieve all user-generated meme lists for the specified user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[UserListInfo]
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - User must exist in the system.
            - Lists returned are only those where user_id matches.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_lists = [
            list_info
            for list_info in self.user_lists.values()
            if list_info.get("user_id") == user_id
        ]
        return {"success": True, "data": user_lists}

    def get_user_meme_list_by_name(self, user_id: str, list_name: str) -> dict:
        """
        Retrieve a specific meme list (collection) created by a user with the specified name.

        Args:
            user_id (str): The unique identifier of the user.
            list_name (str): The name of the user-generated list to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": UserListInfo  # The user list info if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - Only lists linked to user_id can be retrieved.
            - Only existing lists can be retrieved.
        """
        for user_list in self.user_lists.values():
            if user_list["user_id"] == user_id and user_list["name"] == list_name:
                return {"success": True, "data": user_list}

        return {"success": False, "error": "List not found for user"}

    def increment_meme_views(self, meme_id: str) -> dict:
        """
        Increments the view count of a meme by 1.

        Args:
            meme_id (str): The unique ID of the meme to increment the view count for.

        Returns:
            dict: 
                - If success: { "success": True, "message": "Meme view count incremented." }
                - If meme does not exist: { "success": False, "error": "Meme does not exist" }
        Constraints:
            - Only existing memes can be updated.
        """
        if meme_id not in self.memes:
            return { "success": False, "error": "Meme does not exist" }
    
        self.memes[meme_id]["views"] += 1
        return { "success": True, "message": "Meme view count incremented." }

    def upvote_meme(self, meme_id: str) -> dict:
        """
        Increase the upvote count of a specified meme by 1.

        Args:
            meme_id (str): The unique identifier of the meme to upvote.

        Returns:
            dict: 
                If successful: { "success": True, "message": "Upvote incremented for meme <meme_id>" }
                If meme does not exist: { "success": False, "error": "Meme does not exist" }

        Constraints:
            - Meme must exist in the platform to be upvoted.
        """
        meme = self.memes.get(meme_id)
        if meme is None:
            return { "success": False, "error": "Meme does not exist" }
        meme["upvotes"] += 1
        return { "success": True, "message": f"Upvote incremented for meme {meme_id}" }

    def downvote_meme(self, meme_id: str) -> dict:
        """
        Increments the downvote count of a meme by 1.

        Args:
            meme_id (str): Unique identifier of the meme to downvote.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Downvoted meme '<title>' (id: <meme_id>)."
                  }
                - On failure: {
                    "success": False,
                    "error": "Meme does not exist."
                  }
        Constraints:
            - Only existing memes can be downvoted.
        """
        meme = self.memes.get(meme_id)
        if meme is None:
            return { "success": False, "error": "Meme does not exist." }

        # Increment the downvotes count
        meme['downvotes'] = int(meme.get('downvotes', 0)) + 1
        return {
            "success": True,
            "message": f"Downvoted meme '{meme['title']}' (id: {meme_id})."
        }

    def add_meme_to_user_list(self, list_id: str, meme_id: str) -> dict:
        """
        Add a specified meme to a user-generated list.

        Args:
            list_id (str): The identifier of the user-generated meme list.
            meme_id (str): The identifier of the meme to add.

        Returns:
            dict: {
                "success": True,
                "message": "Meme added to user list."
            }
            or
            {
                "success": False,
                "error": str  # error description.
            }

        Constraints:
            - Both list and meme must exist.
            - Meme must not already be present in the list.
            - Only existing memes may be referenced by user lists.
        """
        # Check if the user-generated list exists
        if list_id not in self.user_lists:
            return { "success": False, "error": "User list does not exist." }

        # Check if the meme exists
        if meme_id not in self.memes:
            return { "success": False, "error": "Meme does not exist." }

        user_list = self.user_lists[list_id]
        if meme_id in user_list['meme_ids']:
            return { "success": False, "error": "Meme already in this user list." }

        user_list['meme_ids'].append(meme_id)
        return { "success": True, "message": "Meme added to user list." }

    def remove_meme_from_user_list(self, list_id: str, meme_id: str) -> dict:
        """
        Remove a specified meme from a user-generated list.

        Args:
            list_id (str): The unique identifier of the user-generated list.
            meme_id (str): The unique identifier of the meme to remove.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Meme removed from user list." }
                On failure:
                    { "success": False, "error": str }
        Constraints:
            - The user-generated list must exist.
            - The meme must exist in the system.
            - The meme must currently be in the list.
            - Updates list state by removing meme from meme_ids.
        """
        # Check the list exists
        if list_id not in self.user_lists:
            return { "success": False, "error": "User-generated list does not exist." }

        # Check the meme exists
        if meme_id not in self.memes:
            return { "success": False, "error": "Meme does not exist." }

        # Check the meme is actually in the list
        user_list = self.user_lists[list_id]
        if meme_id not in user_list["meme_ids"]:
            return { "success": False, "error": "Meme not found in user list." }

        # Remove meme from the list
        user_list["meme_ids"].remove(meme_id)
        return { "success": True, "message": "Meme removed from user list." }

    def add_meme_to_user_favorites(self, user_id: str, meme_id: str) -> dict:
        """
        Add a meme to the user's list of favorite memes.

        Args:
            user_id (str): The user's unique ID.
            meme_id (str): The meme's unique ID to be added.

        Returns:
            dict:
                - success (bool): True if the operation succeeds, else False.
                - message (str): Description for success.
                - error (str): Description for failure if not successful.

        Constraints:
            - The user must exist.
            - The meme must exist.
            - Memes are not duplicated in a user's favorites.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        # Check meme existence
        if meme_id not in self.memes:
            return { "success": False, "error": "Meme does not exist" }
        user_info = self.users[user_id]
        if meme_id in user_info["favorite_memes"]:
            return {
                "success": False,
                "error": "Meme already in user's favorites"
            }
        user_info["favorite_memes"].append(meme_id)
        return {
            "success": True,
            "message": "Meme added to user's favorites"
        }

    def remove_meme_from_user_favorites(self, user_id: str, meme_id: str) -> dict:
        """
        Remove a meme from a user's favorites.

        Args:
            user_id (str): The user's unique identifier (_id).
            meme_id (str): The meme's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Meme removed from favorites."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - The user must exist.
            - The meme must exist.
            - Operation is idempotent (removing a meme not present: still success).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }
        if meme_id not in self.memes:
            return { "success": False, "error": "Meme does not exist." }
    
        # Remove meme_id from user's favorite_memes if present
        if meme_id in user["favorite_memes"]:
            user["favorite_memes"].remove(meme_id)
            # Actually update the user info in state (dict is mutable, but be explicit)
            self.users[user_id] = user  # Not strictly necessary, but for clarity

        return { "success": True, "message": "Meme removed from favorites." }


    def create_user_meme_list(self, user_id: str, name: str, meme_ids: List[str]) -> dict:
        """
        Create a new user-generated meme list for the specified user.

        Args:
            user_id (str): ID of the user creating the list.
            name (str): Name/title for the new meme list. Must not duplicate an existing list name for this user.
            meme_ids (List[str]): List of meme IDs to include. Each must exist in the memes registry.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "List created",
                        "list_id": <new_list_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <description>
                    }

        Constraints:
            - The user must exist.
            - All meme_ids must be valid (i.e., exist in self.memes).
            - The list name must not already exist for this user.
            - The new list will be added to self.user_lists with a unique list_id.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check for duplicate list name for this user
        for user_list in self.user_lists.values():
            if user_list['user_id'] == user_id and user_list['name'] == name:
                return { "success": False, "error": "List name already exists for this user." }

        # Validate all meme_ids
        for meme_id in meme_ids:
            if meme_id not in self.memes:
                return { "success": False, "error": f"Meme ID '{meme_id}' does not exist." }

        # Generate unique list_id
        list_id = str(uuid.uuid4())

        # Use current timestamp as creation date
        creation_da = str(int(time.time()))

        # Create and insert the UserListInfo
        new_list = {
            "list_id": list_id,
            "user_id": user_id,
            "name": name,
            "meme_ids": meme_ids.copy(),
            "creation_da": creation_da
        }

        self.user_lists[list_id] = new_list

        return {
            "success": True,
            "message": "List created",
            "list_id": list_id
        }

    def delete_user_meme_list(self, list_id: str) -> dict:
        """
        Delete an existing user-generated meme list.

        Args:
            list_id (str): The unique identifier of the user list to delete.

        Returns:
            dict: {
                "success": True,
                "message": "User meme list deleted successfully"
            }
            or
            {
                "success": False,
                "error": "List does not exist"
            }

        Constraints:
            - List must exist in self.user_lists.
            - No deletion of non-existent list.
        """
        if list_id not in self.user_lists:
            return { "success": False, "error": "List does not exist" }

        del self.user_lists[list_id]
        return { "success": True, "message": "User meme list deleted successfully" }


class MemeSharingPlatform(BaseEnv):
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
            if key == "trending_lists" and isinstance(value, dict):
                normalized = copy.deepcopy(value)
                for original_key, item in value.items():
                    if not isinstance(item, dict):
                        continue
                    period = item.get("period")
                    genre = item.get("genre")
                    if isinstance(period, str) and isinstance(genre, str):
                        normalized[f"{period}:{genre}"] = copy.deepcopy(item)
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

    def list_memes_by_genre(self, **kwargs):
        return self._call_inner_tool('list_memes_by_genre', kwargs)

    def get_top_memes_by_genre(self, **kwargs):
        return self._call_inner_tool('get_top_memes_by_genre', kwargs)

    def get_trending_list(self, **kwargs):
        return self._call_inner_tool('get_trending_list', kwargs)

    def get_random_meme_by_genre(self, **kwargs):
        return self._call_inner_tool('get_random_meme_by_genre', kwargs)

    def get_meme_details(self, **kwargs):
        return self._call_inner_tool('get_meme_details', kwargs)

    def list_all_genres(self, **kwargs):
        return self._call_inner_tool('list_all_genres', kwargs)

    def get_user_info_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_username', kwargs)

    def get_user_uploaded_memes(self, **kwargs):
        return self._call_inner_tool('get_user_uploaded_memes', kwargs)

    def get_user_favorite_memes(self, **kwargs):
        return self._call_inner_tool('get_user_favorite_memes', kwargs)

    def list_user_generated_lists(self, **kwargs):
        return self._call_inner_tool('list_user_generated_lists', kwargs)

    def get_user_meme_list_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_meme_list_by_name', kwargs)

    def increment_meme_views(self, **kwargs):
        return self._call_inner_tool('increment_meme_views', kwargs)

    def upvote_meme(self, **kwargs):
        return self._call_inner_tool('upvote_meme', kwargs)

    def downvote_meme(self, **kwargs):
        return self._call_inner_tool('downvote_meme', kwargs)

    def add_meme_to_user_list(self, **kwargs):
        return self._call_inner_tool('add_meme_to_user_list', kwargs)

    def remove_meme_from_user_list(self, **kwargs):
        return self._call_inner_tool('remove_meme_from_user_list', kwargs)

    def add_meme_to_user_favorites(self, **kwargs):
        return self._call_inner_tool('add_meme_to_user_favorites', kwargs)

    def remove_meme_from_user_favorites(self, **kwargs):
        return self._call_inner_tool('remove_meme_from_user_favorites', kwargs)

    def create_user_meme_list(self, **kwargs):
        return self._call_inner_tool('create_user_meme_list', kwargs)

    def delete_user_meme_list(self, **kwargs):
        return self._call_inner_tool('delete_user_meme_list', kwargs)
