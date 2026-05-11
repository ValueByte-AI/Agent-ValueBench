# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    profile_pic: str

class EngagementMetricsInfo(TypedDict):
    media_id: str
    like_count: int
    comment_count: int
    view_count: int
    share_count: int

class MediaInfo(TypedDict):
    media_id: str
    author_id: str
    media_type: str
    created_at: str
    caption: str
    url: str
    engagement_metric: str  # Reference to media_id in EngagementMetricsInfo

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing Instagram media management API.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Media: {media_id: MediaInfo}
        # Each media_id must be unique.
        # author_id must reference an existing user (see constraints).
        self.media: Dict[str, MediaInfo] = {}

        # Engagement metrics: {media_id: EngagementMetricsInfo}
        # Engagement statistics are non-negative integers.
        self.engagement_metrics: Dict[str, EngagementMetricsInfo] = {}

        # Only authorized users/applications may access media details via the API.
        # (Authorization/enforcement not modeled here; see constraints.)


    def get_media_by_id(self, media_id: str) -> dict:
        """
        Retrieve detailed metadata (MediaInfo) for a media item given its media_id.

        Args:
            media_id (str): The unique media identifier.

        Returns:
            dict: {
                "success": True,
                "data": MediaInfo
            }
            OR
            {
                "success": False,
                "error": "Media not found"
            }

        Constraints:
            - media_id must exist in self.media (each is unique).
            - No authorization logic enforced in this environment.
        """
        if media_id not in self.media:
            return { "success": False, "error": "Media not found" }
        return { "success": True, "data": self.media[media_id] }

    def get_media_list_by_author(self, author_id: str) -> dict:
        """
        Retrieve all media items posted by the specified author (user ID).

        Args:
            author_id (str): The user ID of the author.

        Returns:
            dict: 
                - {
                      "success": True,
                      "data": List[MediaInfo],  # All media posted by the author (may be empty list)
                  }
                - {
                      "success": False,
                      "error": str  # If author does not exist
                  }

        Constraints:
            - The author_id must reference an existing user.
        """
        if author_id not in self.users:
            return {"success": False, "error": "Author does not exist"}

        result = [
            media_info for media_info in self.media.values()
            if media_info["author_id"] == author_id
        ]
        return {"success": True, "data": result}

    def get_engagement_metrics_by_media_id(self, media_id: str) -> dict:
        """
        Retrieve the engagement metrics (like, comment, view, share counts)
        for a given media_id.

        Args:
            media_id (str): The media item's unique identifier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": EngagementMetricsInfo
                    }
                - On failure (media_id not found):
                    {
                        "success": False,
                        "error": "Engagement metrics for media_id not found"
                    }

        Constraints:
            - media_id must exist in self.engagement_metrics.
            - Engagement statistics must be non-negative integers (guaranteed elsewhere).
            - No modification of state; pure query.
        """
        metrics = self.engagement_metrics.get(media_id)
        if metrics is None:
            return {
                "success": False,
                "error": "Engagement metrics for media_id not found"
            }
        return {
            "success": True,
            "data": metrics
        }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user (author) information by user_id.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # user profile information
            }
            or
            {
                "success": False,
                "error": str  # reason for failure, e.g., user_id not found
            }

        Constraints:
            - user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_user_by_username(self, username: str) -> dict:
        """
        Fetch a user's details using their Instagram username.

        Args:
            username (str): The Instagram username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,   # The user's info dictionary
            }
            or
            {
                "success": False,
                "error": "User not found",
            }

        Constraints:
            - The username must exist in the system.
            - Matching is case-insensitive and accepts usernames with or without a leading '@'.
        """
        if not isinstance(username, str):
            return { "success": False, "error": "User not found" }

        normalized_query = username.strip()
        if normalized_query.startswith("@"):
            normalized_query = normalized_query[1:]
        normalized_query = normalized_query.lower()

        for user in self.users.values():
            stored_username = user["username"]
            normalized_stored = stored_username[1:] if stored_username.startswith("@") else stored_username
            if normalized_stored.lower() == normalized_query:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def media_exists(self, media_id: str) -> dict:
        """
        Check whether a specific media_id exists in the system.

        Args:
            media_id (str): The media ID to look up.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if media_id exists, else False
            }

        Constraints:
            - Returns False if input is None or empty string.
            - Each media_id must be unique.
        """
        if not media_id or not isinstance(media_id, str):
            return { "success": True, "data": False }

        exists = media_id in self.media
        return { "success": True, "data": exists }

    def list_all_media(self) -> dict:
        """
        Retrieve a list of all media items on the platform.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[MediaInfo],  # List of all media metadata (may be empty).
            }

        Constraints:
            - No inputs.
            - Returns all media info currently present in the environment.
        """
        all_media = list(self.media.values())
        return { "success": True, "data": all_media }

    def list_recent_media_for_user(self, user_id: str) -> dict:
        """
        Retrieve a list of media posted by a specific user, ordered by created_at descending (most recent first).

        Args:
            user_id (str): The _id of the user whose media to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MediaInfo]  # may be empty
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user (user_id) must exist in the system.
            - Items are ordered by created_at (descending).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        user_media = [
            media_info for media_info in self.media.values()
            if media_info["author_id"] == user_id
        ]

        # Assume created_at is ISO8601 or comparable string, sort descending (most recent first)
        sorted_media = sorted(user_media, key=lambda x: x["created_at"], reverse=True)

        return { "success": True, "data": sorted_media }

    def update_media_caption(self, media_id: str, new_caption: str) -> dict:
        """
        Update the caption text for a specific media item.

        Args:
            media_id (str): The unique identifier of the media to update.
            new_caption (str): The new caption text to set.

        Returns:
            dict:
                On success: { "success": True, "message": "Caption updated for media <media_id>" }
                On failure: { "success": False, "error": "Media not found" }

        Constraints:
            - media_id must reference an existing entry in self.media.
            - No restrictions on caption content/format.
        """
        if media_id not in self.media:
            return { "success": False, "error": "Media not found" }
    
        self.media[media_id]['caption'] = new_caption

        return { "success": True, "message": f"Caption updated for media {media_id}" }

    def update_engagement_metrics(
        self,
        media_id: str,
        like_count: int = None,
        comment_count: int = None,
        view_count: int = None,
        share_count: int = None
    ) -> dict:
        """
        Update one or more engagement metrics for a specific media item.

        Args:
            media_id (str): The media ID whose engagement metrics are to be updated.
            like_count (int, optional): New like count (must be non-negative integer).
            comment_count (int, optional): New comment count (must be non-negative integer).
            view_count (int, optional): New view count (must be non-negative integer).
            share_count (int, optional): New share count (must be non-negative integer).

        Returns:
            dict:
                "success": True, "message": "Engagement metrics updated for media_id <media_id>"
                OR
                "success": False, "error": <reason>

        Constraints:
            - media_id must exist in self.engagement_metrics.
            - Supplied new values must be non-negative integers.
            - At least one value must be supplied to update.
        """
        if media_id not in self.engagement_metrics:
            return { "success": False, "error": "Media ID does not exist in engagement metrics." }

        # Build list of updates
        updates = {}
        for k, v in [("like_count", like_count), ("comment_count", comment_count),
                     ("view_count", view_count), ("share_count", share_count)]:
            if v is not None:
                if not isinstance(v, int) or v < 0:
                    return { "success": False, "error": f"{k} must be a non-negative integer." }
                updates[k] = v

        if not updates:
            return {"success": False, "error": "No engagement metric provided to update."}

        # Apply updates
        for k, v in updates.items():
            self.engagement_metrics[media_id][k] = v

        return { "success": True, "message": f"Engagement metrics updated for media_id {media_id}" }

    def create_media(
        self,
        media_id: str,
        author_id: str,
        media_type: str,
        created_at: str,
        caption: str,
        url: str
    ) -> dict:
        """
        Add a new media entry to the system.

        Args:
            media_id (str): Unique identifier for the media.
            author_id (str): ID of the author (must exist in users).
            media_type (str): Type of media ('photo', 'video', etc).
            created_at (str): Creation timestamp.
            caption (str): Media caption.
            url (str): URL to the media file.

        Returns:
            dict: 
                {"success": True, "message": "Media created successfully."}
                or
                {"success": False, "error": str}
        Constraints:
            - media_id must be unique.
            - author_id must reference an existing user.
            - Engagement metrics initialized to zero.
        """
        if not media_id or media_id in self.media:
            return {"success": False, "error": "media_id must be unique and non-empty."}
    
        if author_id not in self.users:
            return {"success": False, "error": "author_id does not exist."}
    
        # Create the engagement metrics entry (all zero)
        metrics = {
            "media_id": media_id,
            "like_count": 0,
            "comment_count": 0,
            "view_count": 0,
            "share_count": 0
        }
        self.engagement_metrics[media_id] = metrics
    
        new_media = {
            "media_id": media_id,
            "author_id": author_id,
            "media_type": media_type,
            "created_at": created_at,
            "caption": caption,
            "url": url,
            "engagement_metric": media_id
        }
        self.media[media_id] = new_media
    
        return {"success": True, "message": "Media created successfully."}

    def delete_media(self, media_id: str) -> dict:
        """
        Remove a media item and its associated engagement metrics from the platform.

        Args:
            media_id (str): The unique identifier of the media item to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Media <media_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Media not found."
            }

        Constraints:
            - media_id must exist in the media dictionary.
            - All related engagement metrics should also be removed if present.
        """
        if media_id not in self.media:
            return {"success": False, "error": "Media not found."}

        # Remove the media item
        del self.media[media_id]

        # Remove engagement metrics if present
        if media_id in self.engagement_metrics:
            del self.engagement_metrics[media_id]

        return {"success": True, "message": f"Media {media_id} deleted."}

    def increment_engagement_metric(self, media_id: str, metric_type: str) -> dict:
        """
        Atomically increment a specific type of engagement metric (like, comment, view, share)
        for a given media item.

        Args:
            media_id (str): The ID of the media whose engagement to increment.
            metric_type (str): The engagement metric type ("like", "comment", "view", "share").

        Returns:
            dict: {
                "success": True,
                "message": f"Engagement metric {metric_type} incremented for media {media_id}"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - media_id must exist.
            - metric_type must be one of: "like", "comment", "view", "share".
            - Engagement counts remain non-negative.
        """
        metric_map = {
            "like": "like_count",
            "comment": "comment_count",
            "view": "view_count",
            "share": "share_count"
        }

        if media_id not in self.engagement_metrics:
            return {"success": False, "error": "Media engagement metrics not found for given media_id"}

        if metric_type not in metric_map:
            return {"success": False, "error": "Invalid metric_type. Must be one of: like, comment, view, share"}

        metric_field = metric_map[metric_type]
        curr_value = self.engagement_metrics[media_id][metric_field]
        if not isinstance(curr_value, int) or curr_value < 0:
            # Defensive: Should not occur
            return {"success": False, "error": "Invalid engagement metric data"}

        self.engagement_metrics[media_id][metric_field] += 1

        return {
            "success": True,
            "message": f"Engagement metric {metric_type} incremented for media {media_id}"
        }


class InstagramMediaManagementAPI(BaseEnv):
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

    def get_media_by_id(self, **kwargs):
        return self._call_inner_tool('get_media_by_id', kwargs)

    def get_media_list_by_author(self, **kwargs):
        return self._call_inner_tool('get_media_list_by_author', kwargs)

    def get_engagement_metrics_by_media_id(self, **kwargs):
        return self._call_inner_tool('get_engagement_metrics_by_media_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def media_exists(self, **kwargs):
        return self._call_inner_tool('media_exists', kwargs)

    def list_all_media(self, **kwargs):
        return self._call_inner_tool('list_all_media', kwargs)

    def list_recent_media_for_user(self, **kwargs):
        return self._call_inner_tool('list_recent_media_for_user', kwargs)

    def update_media_caption(self, **kwargs):
        return self._call_inner_tool('update_media_caption', kwargs)

    def update_engagement_metrics(self, **kwargs):
        return self._call_inner_tool('update_engagement_metrics', kwargs)

    def create_media(self, **kwargs):
        return self._call_inner_tool('create_media', kwargs)

    def delete_media(self, **kwargs):
        return self._call_inner_tool('delete_media', kwargs)

    def increment_engagement_metric(self, **kwargs):
        return self._call_inner_tool('increment_engagement_metric', kwargs)
