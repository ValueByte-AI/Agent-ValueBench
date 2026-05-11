# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import uuid



# User: _id, username, join_date, reputation
class UserInfo(TypedDict):
    _id: str
    username: str
    join_date: str
    reputation: int

# Thread: thread_id, title, content, user_id, timestamp, tags, rating_score
class ThreadInfo(TypedDict):
    thread_id: str
    title: str
    content: str
    user_id: str  # creator's user id
    timestamp: str
    tags: List[str]  # List of tag_ids
    rating_score: Union[int, float]

# Tag: tag_id, tag_name
class TagInfo(TypedDict):
    tag_id: str
    tag_name: str

# Rating: rating_id, thread_id, user_id, value, timestamp
class RatingInfo(TypedDict):
    rating_id: str
    thread_id: str
    user_id: str
    value: int
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Persistent state for online forum discussion platform.

        Constraints:
        - Each thread must have at least one associated tag.
        - A user can rate a given thread only once.
        - Aggregated thread ratings (rating_score) are computed by combining individual ratings.
        - Users can only edit or delete their own threads.
        - Tags must be pre-defined or created by users according to platform policy.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Threads: {thread_id: ThreadInfo}
        self.threads: Dict[str, ThreadInfo] = {}

        # Tags: {tag_id: TagInfo}
        self.tags: Dict[str, TagInfo] = {}

        # Ratings: {rating_id: RatingInfo}
        self.ratings: Dict[str, RatingInfo] = {}

    def get_tag_by_name(self, tag_name: str) -> dict:
        """
        Retrieve tag information by tag name.

        Args:
            tag_name (str): The name of the tag to look up.

        Returns:
            dict: {
                "success": True,
                "data": TagInfo  # Tag information if found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. not found
            }
    
        Constraints:
            - Tag names are expected to be unique. Only exact match is returned.
        """
        for tag in self.tags.values():
            if tag["tag_name"] == tag_name:
                return { "success": True, "data": tag }
        return { "success": False, "error": "Tag not found" }

    def list_threads_by_tag(self, tag_id: str) -> dict:
        """
        List all threads that are associated with a given tag_id.

        Args:
            tag_id (str): The tag's unique identifier.

        Returns:
            dict: 
                {
                    "success": True, 
                    "data": List[ThreadInfo]  # All threads with this tag (can be empty)
                }
                OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - tag_id must exist in the system.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist." }
    
        threads_with_tag = [
            thread_info for thread_info in self.threads.values()
            if tag_id in thread_info.get("tags", [])
        ]
        return { "success": True, "data": threads_with_tag }

    def get_thread_by_id(self, thread_id: str) -> dict:
        """
        Retrieve all details (ThreadInfo) for a thread given its thread_id.

        Args:
            thread_id (str): The unique identifier for the thread.

        Returns:
            dict:
                - success: True and data (ThreadInfo) if found.
                - success: False and error message if thread_id does not exist.

        Constraints:
            - The thread_id must exist in the forum.
        """
        thread_info = self.threads.get(thread_id)
        if not thread_info:
            return {"success": False, "error": "Thread not found"}
        return {"success": True, "data": thread_info}

    def get_thread_rating_score(self, thread_id: str) -> dict:
        """
        Retrieve the current aggregated rating score for a given thread.

        Args:
            thread_id (str): The identifier of the thread.

        Returns:
            dict:
                - If successful:
                    {"success": True, "data": int or float}  # Current aggregated rating score
                - If thread not found:
                    {"success": False, "error": "Thread not found"}

        Constraints:
            - The thread must exist in the platform.
        """
        thread = self.threads.get(thread_id)
        if thread is None:
            return { "success": False, "error": "Thread not found" }
        return { "success": True, "data": thread["rating_score"] }

    def list_top_rated_threads_by_tag(self, tag_id: str, limit: int = None) -> dict:
        """
        List threads that have the specified tag, sorted by their rating_score (descending).
        Optionally, limit the number of returned results.

        Args:
            tag_id (str): The id of the tag to filter threads by.
            limit (int, optional): Maximum number of results to return (must be positive if given).

        Returns:
            dict: {
                "success": True,
                "data": List[ThreadInfo]  # Sorted list (may be empty)
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - tag_id must exist in the tag database.
            - limit must be positive integer if provided.
        """
        if tag_id not in self.tags:
            return {"success": False, "error": "Tag not found"}

        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                return {"success": False, "error": "Limit must be a positive integer if provided"}

        # Collect threads with this tag
        threads_with_tag = [
            thread for thread in self.threads.values()
            if tag_id in thread.get("tags", [])
        ]

        # Sort descending by rating_score
        threads_sorted = sorted(
            threads_with_tag,
            key=lambda t: t.get("rating_score", 0),
            reverse=True
        )

        # Apply optional limit
        if limit is not None:
            threads_sorted = threads_sorted[:limit]

        return {"success": True, "data": threads_sorted}

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve a user's full profile information given their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": UserInfo  # The user's profile
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason (e.g., "User not found")
                }
        Constraints:
            - Usernames are case-sensitive and assumed unique. If multiple users have the same username, the first match is returned.
            - No permissions required for this read operation.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "User not found"}

    def get_ratings_for_thread(self, thread_id: str) -> dict:
        """
        List all individual ratings (votes) received by a specific thread.

        Args:
            thread_id (str): The unique identifier of the thread.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[RatingInfo]   # List of ratings for this thread (could be empty)
                }
                If thread does not exist: {
                    "success": False,
                    "error": "Thread does not exist"
                }
        Constraints:
            - The thread must exist.
        """
        if thread_id not in self.threads:
            return { "success": False, "error": "Thread does not exist" }

        ratings = [
            rating for rating in self.ratings.values()
            if rating["thread_id"] == thread_id
        ]
        return { "success": True, "data": ratings }

    def get_tags_for_thread(self, thread_id: str) -> dict:
        """
        Given a thread_id, list all tags (TagInfo) associated with the thread.

        Args:
            thread_id (str): The unique identifier of the thread.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo]  # If thread exists, all tag info for its tags (possibly empty if tags missing by data corruption)
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The thread must exist.
            - Handles missing tags gracefully (skipped in data).
        """
        thread = self.threads.get(thread_id)
        if thread is None:
            return { "success": False, "error": "Thread does not exist" }
    
        # Retrieve tag infos; skip tags that are missing in the self.tags table
        tag_infos = [
            self.tags[tag_id] for tag_id in thread.get("tags", [])
            if tag_id in self.tags
        ]

        return { "success": True, "data": tag_infos }

    def has_user_rated_thread(self, user_id: str, thread_id: str) -> dict:
        """
        Check if a given user has already rated a specified thread.

        Args:
            user_id (str): The unique ID of the user to check.
            thread_id (str): The unique ID of the thread to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if the user has rated the thread, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Description of the error; e.g., user or thread not found
            }

        Constraints:
            - user_id must exist.
            - thread_id must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if thread_id not in self.threads:
            return {"success": False, "error": "Thread does not exist"}

        for rating in self.ratings.values():
            if rating["user_id"] == user_id and rating["thread_id"] == thread_id:
                return {"success": True, "data": True}

        return {"success": True, "data": False}

    def list_all_tags(self) -> dict:
        """
        List all available or pre-defined tags in the forum.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],  # List of all tags (possibly empty if none exist)
            }

        Constraints:
            - None specific; shows all tags in the platform state.
        """
        tag_list = list(self.tags.values())
        return { "success": True, "data": tag_list }

    def add_thread(
        self, 
        title: str, 
        content: str, 
        user_id: str, 
        tag_ids: list, 
        timestamp: str
    ) -> dict:
        """
        Create a new thread with at least one associated tag.

        Args:
            title (str): Title of the thread.
            content (str): Content/body of the thread.
            user_id (str): The ID of the user creating this thread.
            tag_ids (List[str]): List of tag IDs to associate with this thread (must be non-empty, all tags must exist).
            timestamp (str): Thread creation timestamp.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Thread created",
                        "thread_id": <new_thread_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
    
        Constraints:
            - Each thread must have at least one existing tag.
            - Tags must be pre-defined (already exist in self.tags).
            - user_id must exist.
        """
        # Basic parameter checks
        if not title or not isinstance(title, str):
            return {"success": False, "error": "Thread title is required and must be a string"}
        if not content or not isinstance(content, str):
            return {"success": False, "error": "Thread content is required and must be a string"}
        if not user_id or not isinstance(user_id, str):
            return {"success": False, "error": "user_id is required and must be a string"}
        if not isinstance(tag_ids, list) or not tag_ids:
            return {"success": False, "error": "At least one tag_id must be provided"}
        if not timestamp or not isinstance(timestamp, str):
            return {"success": False, "error": "timestamp is required and must be a string"}
        # User existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        # All tags must exist
        missing_tags = [tid for tid in tag_ids if tid not in self.tags]
        if missing_tags:
            return {
                "success": False,
                "error": f"Tag(s) do not exist: {', '.join(missing_tags)}"
            }
        # Generate unique thread_id
        new_thread_id = str(uuid.uuid4())
        if new_thread_id in self.threads:
            # Incredibly unlikely, but re-generate if collision (paranoia)
            while new_thread_id in self.threads:
                new_thread_id = str(uuid.uuid4())
        # Build thread info
        thread_info = {
            "thread_id": new_thread_id,
            "title": title,
            "content": content,
            "user_id": user_id,
            "timestamp": timestamp,
            "tags": list(tag_ids),
            "rating_score": 0
        }
        self.threads[new_thread_id] = thread_info
        return {
            "success": True,
            "message": "Thread created",
            "thread_id": new_thread_id
        }

    def edit_thread(
        self,
        thread_id: str,
        user_id: str,
        title: str = None,
        content: str = None,
        tags: list = None
    ) -> dict:
        """
        Edit (update) the content, title, and/or tags of a thread.
        Only the original author (creator) of the thread can perform this operation.

        Args:
            thread_id (str): ID of thread to edit.
            user_id (str): User performing the edit; must match thread creator.
            title (Optional[str]): New title (if provided).
            content (Optional[str]): New content (if provided).
            tags (Optional[List[str]]): New list of tag_ids (if provided).

        Returns:
            dict: {
                "success": True,
                "message": "Thread updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only the thread creator can edit.
            - After edit, thread must have at least one associated tag.
            - All provided tags must exist.
            - At least one field (title, content, tags) must be provided.
        """
        # Check thread exists
        thread = self.threads.get(thread_id)
        if not thread:
            return {"success": False, "error": "Thread does not exist."}

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check user is author
        if thread["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: Only the thread author can edit."}

        # Validate at least one field to update
        if title is None and content is None and tags is None:
            return {"success": False, "error": "No fields to update provided."}

        # If tags are provided, validate non-empty and all tags exist
        if tags is not None:
            if not tags or not isinstance(tags, list):
                return {"success": False, "error": "Tags list must be a non-empty list."}
            for tag_id in tags:
                if tag_id not in self.tags:
                    return {"success": False, "error": f"Tag '{tag_id}' does not exist."}
            thread["tags"] = tags

        # After tags update (or if not updating, check current tags), ensure at least one tag
        tag_check = thread["tags"]
        if not tag_check or not isinstance(tag_check, list) or len(tag_check) == 0:
            return {
                "success": False,
                "error": "Each thread must have at least one associated tag."
            }

        # Update title/content if provided
        if title is not None:
            thread["title"] = title
        if content is not None:
            thread["content"] = content

        # Optionally (not required by spec), one could update 'timestamp' to "last updated", but
        # since only 'timestamp' is given in ThreadInfo, we'll leave it unchanged.

        self.threads[thread_id] = thread
        return {"success": True, "message": "Thread updated successfully."}

    def delete_thread(self, thread_id: str, request_user_id: str) -> dict:
        """
        Delete a thread identified by thread_id. Only the thread's author (request_user_id) may perform deletion.
        All associated ratings with this thread are also removed.

        Args:
            thread_id (str): The ID of the thread to delete.
            request_user_id (str): The user ID of the user attempting the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Thread deleted successfully."
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - Thread must exist.
            - Only the author can delete their thread.
            - All ratings for the thread are removed.
        """

        thread = self.threads.get(thread_id)
        if thread is None:
            return {"success": False, "error": "Thread does not exist."}
    
        if request_user_id != thread["user_id"]:
            return {"success": False, "error": "Permission denied: only the author can delete this thread."}
    
        # Delete associated ratings
        ratings_to_delete = [
            rating_id for rating_id, rating in self.ratings.items()
            if rating["thread_id"] == thread_id
        ]
        for rating_id in ratings_to_delete:
            del self.ratings[rating_id]
    
        # Delete thread
        del self.threads[thread_id]
        return {"success": True, "message": "Thread deleted successfully."}

    def add_rating(
        self, 
        user_id: str, 
        thread_id: str, 
        value: int, 
        timestamp: str
    ) -> dict:
        """
        Add a user's rating for a thread, enforcing only one rating per user per thread.
    
        Args:
            user_id (str): The user's identifier.
            thread_id (str): The thread to be rated.
            value (int): The rating value (e.g., upvote, downvote, score).
            timestamp (str): The ISO timestamp for when the rating is cast.
        
        Returns:
            dict: 
                On success: { "success": True, "message": "Rating added successfully." }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - User and thread must exist.
            - User can rate a given thread only once.
            - After addition, the thread's rating_score is recalculated by combining (sum) all ratings for this thread.
        """
        # Check User
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        # Check Thread
        if thread_id not in self.threads:
            return {"success": False, "error": "Thread does not exist."}
        # Check if user has already rated this thread
        for rating in self.ratings.values():
            if rating["thread_id"] == thread_id and rating["user_id"] == user_id:
                return {"success": False, "error": "User has already rated this thread."}
        # Create a new unique rating_id (could use a counter or a composite key)
        rating_id = f"{user_id}_{thread_id}_{len(self.ratings) + 1}"
        # Add to ratings
        new_rating = {
            "rating_id": rating_id,
            "thread_id": thread_id,
            "user_id": user_id,
            "value": value,
            "timestamp": timestamp
        }
        self.ratings[rating_id] = new_rating
        # Recalculate thread's rating_score (sum of all rating values for this thread)
        rating_score = sum(
            r["value"] for r in self.ratings.values() if r["thread_id"] == thread_id
        )
        self.threads[thread_id]["rating_score"] = rating_score
        return {"success": True, "message": "Rating added successfully."}

    def edit_rating(
        self,
        user_id: str,
        thread_id: str,
        new_value: int,
        new_timestamp: str,
    ) -> dict:
        """
        Edit/change a user’s previous rating on a thread.

        Args:
            user_id (str): The user ID of the rater.
            thread_id (str): The thread being rated.
            new_value (int): The new value for the rating.
            new_timestamp (str): Timestamp of the modification.

        Returns:
            dict: {
                "success": True,
                "message": "Rating updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - User must have already rated the thread.
            - Updates the thread's aggregated rating_score after modification.
            - Only the user who authored the rating can edit it (implied).
        """
        # Check if user and thread exist
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if thread_id not in self.threads:
            return {"success": False, "error": "Thread does not exist"}

        # Find the rating for this user/thread
        rating_id = None
        for rid, rating in self.ratings.items():
            if rating["user_id"] == user_id and rating["thread_id"] == thread_id:
                rating_id = rid
                break

        if rating_id is None:
            return {
                "success": False,
                "error": "Rating does not exist for this user/thread"
            }
    
        # Edit the rating's value and timestamp
        self.ratings[rating_id]["value"] = new_value
        self.ratings[rating_id]["timestamp"] = new_timestamp

        # Update thread's aggregated rating_score
        ratings_for_thread = [
            r["value"] for r in self.ratings.values() if r["thread_id"] == thread_id
        ]
        # By default, use sum of rating values as the aggregate (platform rule can override)
        if ratings_for_thread:
            agg_score = sum(ratings_for_thread)
        else:
            agg_score = 0
        self.threads[thread_id]["rating_score"] = agg_score

        return {
            "success": True,
            "message": "Rating updated successfully"
        }

    def remove_rating(self, user_id: str, thread_id: str) -> dict:
        """
        Remove a user's rating from a thread.

        Args:
            user_id (str): ID of the user removing their rating.
            thread_id (str): ID of the thread for which the rating is removed.

        Returns:
            dict: {
                "success": True,
                "message": "Rating removed successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must have previously rated the thread.
            - Thread must exist.
            - Aggregated rating_score of the thread is updated after removal.
        """
        if thread_id not in self.threads:
            return {"success": False, "error": "Thread does not exist."}
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Find the rating_id for this user/thread pair
        rating_id_to_remove = None
        for rating_id, rating in self.ratings.items():
            if rating["user_id"] == user_id and rating["thread_id"] == thread_id:
                rating_id_to_remove = rating_id
                break

        if rating_id_to_remove is None:
            return {"success": False, "error": "Rating does not exist for this user and thread."}

        # Remove the rating
        del self.ratings[rating_id_to_remove]

        # Recalculate the thread's rating_score
        ratings_for_thread = [
            rating["value"]
            for rating in self.ratings.values()
            if rating["thread_id"] == thread_id
        ]
        rating_score = sum(ratings_for_thread) if ratings_for_thread else 0

        self.threads[thread_id]["rating_score"] = rating_score

        return {"success": True, "message": "Rating removed successfully."}


    def add_tag(self, tag_name: str) -> dict:
        """
        Create a new tag for discussion topics, if permitted by platform policy.
        Ensures tag_name is unique (case-insensitive).
    
        Args:
            tag_name (str): The proposed name for the tag.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Tag created with id <tag_id>" }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Tag name must be unique (case-insensitive) among all tags.
            - Tag name must not be empty or whitespace-only.
            - If platform policy forbids tag creation, operation fails.
        """
        # Platform policy toggle (assume allowed if attribute not present)
        if hasattr(self, "allow_tag_creation") and not getattr(self, "allow_tag_creation"):
            return { "success": False, "error": "Tag creation not permitted by platform policy" }

        clean_name = tag_name.strip()
        if not clean_name:
            return { "success": False, "error": "Tag name must not be empty" }
    
        # Check for name uniqueness (case-insensitive)
        for tag in self.tags.values():
            if tag['tag_name'].strip().lower() == clean_name.lower():
                return { "success": False, "error": "Tag name already exists" }
    
        tag_id = str(uuid.uuid4())
        self.tags[tag_id] = {
            "tag_id": tag_id,
            "tag_name": clean_name
        }
        return { "success": True, "message": f"Tag created with id {tag_id}" }

    def edit_tag(self, tag_id: str, new_tag_name: str) -> dict:
        """
        Edit the name of an existing tag if permitted.

        Args:
            tag_id (str): The identifier of the tag to edit.
            new_tag_name (str): The new name for the tag.

        Returns:
            dict: {
                "success": True,
                "message": "Tag updated successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - tag_id must correspond to an existing tag.
            - new_tag_name must be non-empty and not already in use by another tag.
        """
        # Check tag existence
        if tag_id not in self.tags:
            return {"success": False, "error": "Tag does not exist"}

        new_tag_name = new_tag_name.strip()
        if not new_tag_name:
            return {"success": False, "error": "Tag name cannot be empty"}

        # Check for name conflict with other tags
        for t_id, tag_info in self.tags.items():
            if t_id != tag_id and tag_info['tag_name'].lower() == new_tag_name.lower():
                return {"success": False, "error": "A tag with that name already exists"}

        # Edit the tag
        self.tags[tag_id]['tag_name'] = new_tag_name
        return {"success": True, "message": "Tag updated successfully"}

    def assign_tag_to_thread(self, thread_id: str, tag_id: str) -> dict:
        """
        Assign an existing tag to a thread.

        Args:
            thread_id (str): The ID of the thread.
            tag_id (str): The ID of the tag to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Tag assigned to thread successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Thread must exist.
            - Tag must exist.
            - Tag must not already be assigned to the thread.
            - Each thread must have at least one tag at all times (invariant maintained).
        """
        if thread_id not in self.threads:
            return { "success": False, "error": "Thread does not exist" }
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist" }
        thread = self.threads[thread_id]
        if tag_id in thread["tags"]:
            return { "success": False, "error": "Tag already assigned to thread" }
        thread["tags"].append(tag_id)
        self.threads[thread_id] = thread
        return { "success": True, "message": "Tag assigned to thread successfully" }

    def remove_tag_from_thread(self, thread_id: str, tag_id: str) -> dict:
        """
        Remove a tag from a thread, ensuring the thread retains at least one tag.

        Args:
            thread_id (str): The ID of the thread to modify.
            tag_id (str): The ID of the tag to remove from the thread.

        Returns:
            dict: {
                "success": True,
                "message": "Tag <tag_id> removed from thread <thread_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The thread must exist.
            - The tag must exist.
            - The tag must currently be assigned to the thread.
            - After removal, the thread must have at least one tag assigned.
        """
        # Check that the thread exists
        if thread_id not in self.threads:
            return {"success": False, "error": "Thread does not exist."}

        # Check that the tag exists
        if tag_id not in self.tags:
            return {"success": False, "error": "Tag does not exist."}

        thread_info = self.threads[thread_id]
        tags = thread_info.get("tags", [])

        # Check if tag is associated with this thread
        if tag_id not in tags:
            return {"success": False, "error": "Tag is not assigned to this thread."}

        # Ensure at least one tag will remain after removal
        if len(tags) == 1:
            return {"success": False, "error": "Cannot remove the last tag from a thread. Each thread must have at least one tag."}

        # Remove the tag
        new_tags = [tid for tid in tags if tid != tag_id]
        thread_info["tags"] = new_tags

        # Update the thread in the main dictionary
        self.threads[thread_id] = thread_info

        return {
            "success": True,
            "message": f"Tag {tag_id} removed from thread {thread_id}."
        }


class OnlineForumDiscussionPlatform(BaseEnv):
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

    def get_tag_by_name(self, **kwargs):
        return self._call_inner_tool('get_tag_by_name', kwargs)

    def list_threads_by_tag(self, **kwargs):
        return self._call_inner_tool('list_threads_by_tag', kwargs)

    def get_thread_by_id(self, **kwargs):
        return self._call_inner_tool('get_thread_by_id', kwargs)

    def get_thread_rating_score(self, **kwargs):
        return self._call_inner_tool('get_thread_rating_score', kwargs)

    def list_top_rated_threads_by_tag(self, **kwargs):
        return self._call_inner_tool('list_top_rated_threads_by_tag', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_ratings_for_thread(self, **kwargs):
        return self._call_inner_tool('get_ratings_for_thread', kwargs)

    def get_tags_for_thread(self, **kwargs):
        return self._call_inner_tool('get_tags_for_thread', kwargs)

    def has_user_rated_thread(self, **kwargs):
        return self._call_inner_tool('has_user_rated_thread', kwargs)

    def list_all_tags(self, **kwargs):
        return self._call_inner_tool('list_all_tags', kwargs)

    def add_thread(self, **kwargs):
        return self._call_inner_tool('add_thread', kwargs)

    def edit_thread(self, **kwargs):
        return self._call_inner_tool('edit_thread', kwargs)

    def delete_thread(self, **kwargs):
        return self._call_inner_tool('delete_thread', kwargs)

    def add_rating(self, **kwargs):
        return self._call_inner_tool('add_rating', kwargs)

    def edit_rating(self, **kwargs):
        return self._call_inner_tool('edit_rating', kwargs)

    def remove_rating(self, **kwargs):
        return self._call_inner_tool('remove_rating', kwargs)

    def add_tag(self, **kwargs):
        return self._call_inner_tool('add_tag', kwargs)

    def edit_tag(self, **kwargs):
        return self._call_inner_tool('edit_tag', kwargs)

    def assign_tag_to_thread(self, **kwargs):
        return self._call_inner_tool('assign_tag_to_thread', kwargs)

    def remove_tag_from_thread(self, **kwargs):
        return self._call_inner_tool('remove_tag_from_thread', kwargs)

