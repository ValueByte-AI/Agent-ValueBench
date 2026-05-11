# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import datetime



class StoryInfo(TypedDict):
    story_id: str
    title: str
    author_id: str
    content: str
    branches: Any  # Could be list or dict depending on platform format
    media_elements: List[str]
    average_rating: float
    num_ratings: int
    publish_status: str

class UserInfo(TypedDict):
    user_id: str
    username: str
    email: str
    account_status: str
    registration_date: str

class ReviewInfo(TypedDict):
    review_id: str
    story_id: str
    user_id: str
    comment_text: str
    rating: int
    timestamp: str
    moderation_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Interactive Story Platform environment state.
        """

        # Stories: {story_id: StoryInfo}
        self.stories: Dict[str, StoryInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Reviews: {review_id: ReviewInfo}
        self.reviews: Dict[str, ReviewInfo] = {}

        # Constraints:
        # - Each review must be associated with a valid user and a valid story.
        # - Only one review per user per story (latest version kept).
        # - Ratings must be within valid scale (e.g., 1–5).
        # - Submitted reviews may require moderation before display.
        # - Average rating and number of ratings per story must update when reviews are added/updated.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve all user information given a user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo  # Full user information
                    }
                On failure (user_id does not exist):
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user:
            return { "success": True, "data": user }
        else:
            return { "success": False, "error": "User not found" }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information using their username.

        Args:
            username (str): The username to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - Only one user per username should exist (usernames must be unique).
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_user_exists(self, user_id: str = None, username: str = None) -> dict:
        """
        Checks whether a user exists, given user_id or username.

        Args:
            user_id (str, optional): The user's unique ID.
            username (str, optional): The user's username.

        Returns:
            dict: {
                "success": True,
                "exists": bool
            }
            or
            {
                "success": False,
                "error": str  # If no parameters are given or input is invalid
            }

        Constraints:
            - At least one of user_id or username must be provided (not empty).
            - If both are provided and either matches a user, returns True.
        """
        if (user_id is None or user_id == "") and (username is None or username == ""):
            return { "success": False, "error": "Must provide either user_id or username." }

        exists = False

        if user_id and user_id in self.users:
            exists = True
        elif username:
            for user in self.users.values():
                if user["username"] == username:
                    exists = True
                    break

        return { "success": True, "exists": exists }

    def get_story_by_id(self, story_id: str) -> dict:
        """
        Retrieve detailed information for a story given its story_id.

        Args:
            story_id (str): Unique identifier of the story.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": StoryInfo  # All information about the story.
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Story not found"
                    }

        Constraints:
            - story_id must exist in the system.
        """
        story = self.stories.get(story_id)
        if not story:
            return {"success": False, "error": "Story not found"}
        return {"success": True, "data": story}

    def check_story_exists(self, story_id: str) -> dict:
        """
        Check whether a story with the given story_id exists in the platform.

        Args:
            story_id (str): Unique identifier of the story to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if story exists, False otherwise
            }

        Constraints:
            - No permission checks, just dictionary lookup.
        """
        exists = story_id in self.stories
        return { "success": True, "data": exists }

    def check_story_published(self, story_id: str) -> dict:
        """
        Confirm whether a story is currently published and accessible.

        Args:
            story_id (str): The unique identifier of the story to check.

        Returns:
            dict: {
                "success": True,
                "published": bool  # True if story is published, otherwise False
            }
            or
            {
                "success": False,
                "error": str  # If story does not exist
            }

        Constraints:
            - The story must exist in the platform.
        """
        story = self.stories.get(story_id)
        if not story:
            return { "success": False, "error": "Story does not exist" }

        published = story.get("publish_status", "").lower() == "published"
        return { "success": True, "published": published }

    def get_review_by_user_and_story(self, user_id: str, story_id: str) -> dict:
        """
        Retrieve a review for a specific (user_id, story_id) pair if it exists.

        Args:
            user_id (str): ID of the user.
            story_id (str): ID of the story.

        Returns:
            dict: 
                {"success": True, "data": ReviewInfo} if found,
                {"success": False, "error": "..."} otherwise.

        Constraints:
            - User and story must exist.
            - At most one review per (user_id, story_id) pair.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
        if story_id not in self.stories:
            return {"success": False, "error": "Story not found"}
    
        for review in self.reviews.values():
            if review["user_id"] == user_id and review["story_id"] == story_id:
                return {"success": True, "data": review}
    
        return {"success": False, "error": "Review not found"}

    def list_reviews_by_story(self, story_id: str) -> dict:
        """
        Retrieve all reviews (ReviewInfo) associated with a specified story.

        Args:
            story_id (str): The ID of the story whose reviews are to be listed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ReviewInfo]  # Could be empty if no reviews present
                    }
                On error (e.g., story_id does not exist):
                    {
                        "success": False,
                        "error": str  # e.g., "Story not found"
                    }

        Constraints:
            - story_id must refer to an existing story.
            - All reviews associated with the story are returned, regardless of moderation status.
        """
        if story_id not in self.stories:
            return {"success": False, "error": "Story not found"}

        review_list = [
            review for review in self.reviews.values()
            if review["story_id"] == story_id
        ]

        return {"success": True, "data": review_list}

    def list_reviews_by_user(self, user_id: str) -> dict:
        """
        Retrieve all reviews submitted by the specified user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]  # All reviews by this user (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user does not exist)
            }

        Constraints:
            - The user must exist in the platform.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            review_info for review_info in self.reviews.values()
            if review_info["user_id"] == user_id
        ]
        return { "success": True, "data": result }

    def get_review_moderation_status(self, review_id: str) -> dict:
        """
        Get the current moderation status (e.g., pending, approved, rejected) of the specified review.

        Args:
            review_id (str): The unique identifier for the review.

        Returns:
            dict: {
                "success": True,
                "data": str  # Moderation status of the review (e.g., "pending", "approved", "rejected")
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. if review does not exist
            }

        Constraints:
            - The review_id must exist in the platform.
        """
        if review_id not in self.reviews:
            return { "success": False, "error": "Review not found" }

        moderation_status = self.reviews[review_id]["moderation_status"]
        return { "success": True, "data": moderation_status }

    def get_story_rating_info(self, story_id: str) -> dict:
        """
        Retrieve the average rating and the number of ratings for a specific story.

        Args:
            story_id (str): The unique identifier of the story.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "average_rating": float,
                            "num_ratings": int
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Story does not exist"
                    }

        Constraints:
            - The specified story_id must exist in self.stories.
            - The average_rating and num_ratings reflect current data for the story.
        """
        story = self.stories.get(story_id)
        if not story:
            return { "success": False, "error": "Story does not exist" }
        data = {
            "average_rating": story["average_rating"],
            "num_ratings": story["num_ratings"]
        }
        return { "success": True, "data": data }

    def add_or_update_review(self, user_id: str, story_id: str, comment_text: str, rating: int) -> dict:
        """
        Add or update a review for a story by a user.
        Enforces one review per user/story, validates rating, updates aggregation.

        Args:
            user_id (str): The ID of the user submitting the review.
            story_id (str): The ID of the story being reviewed.
            comment_text (str): The review comment.
            rating (int): The rating (must be between 1 and 5 inclusive).

        Returns:
            dict: {
                "success": True,
                "message": str,
                "review_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User and story must exist.
            - Rating in [1, 5].
            - At most one review per user per story (replace if exists).
            - Story aggregate ratings updated.

        """
        # Validate user and story
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if story_id not in self.stories:
            return {"success": False, "error": "Story does not exist"}

        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {"success": False, "error": "Rating must be an integer between 1 and 5"}

        # Check for existing review by this user for this story
        existing_review_id = None
        for rid, review in self.reviews.items():
            if review["user_id"] == user_id and review["story_id"] == story_id:
                existing_review_id = rid
                break

        now_ts = datetime.datetime.now().isoformat()
        moderation_status = "pending"

        if existing_review_id:
            # Update existing review
            self.reviews[existing_review_id].update({
                "comment_text": comment_text,
                "rating": rating,
                "timestamp": now_ts,
                "moderation_status": moderation_status
            })
            review_id = existing_review_id
            message = "Review updated successfully."
        else:
            # Add new review
            review_id = f"rev_{len(self.reviews)+1:06d}"
            self.reviews[review_id] = {
                "review_id": review_id,
                "story_id": story_id,
                "user_id": user_id,
                "comment_text": comment_text,
                "rating": rating,
                "timestamp": now_ts,
                "moderation_status": moderation_status
            }
            message = "Review added successfully."

        approved_ratings = [
            rev["rating"]
            for rev in self.reviews.values()
            if rev["story_id"] == story_id and rev.get("moderation_status") == "approved"
        ]
        if approved_ratings:
            avg_rating = sum(approved_ratings) / len(approved_ratings)
            num_ratings = len(approved_ratings)
        else:
            avg_rating = 0.0
            num_ratings = 0

        self.stories[story_id]["average_rating"] = float(round(avg_rating, 2))
        self.stories[story_id]["num_ratings"] = num_ratings

        return {
            "success": True,
            "message": message,
            "review_id": review_id
        }

    def moderate_review(self, review_id: str, new_status: str) -> dict:
        """
        Change the moderation status of a review.

        Args:
            review_id (str): The unique identifier of the review to moderate.
            new_status (str): The moderation status to set (e.g., 'approved', 'rejected').

        Returns:
            dict:
                - On success: {"success": True, "message": "Moderation status updated for review <review_id>."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The review must exist.
            - No explicit check on allowed moderation statuses (accept any string as status).
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review does not exist."}
    
        self.reviews[review_id]["moderation_status"] = new_status
        return {"success": True, "message": f"Moderation status updated for review {review_id}."}

    def update_story_aggregate_rating(self, story_id: str) -> dict:
        """
        Recalculate and update the average rating and number of ratings for a story.

        Args:
            story_id (str): The ID of the story whose ratings should be updated.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "message": "Aggregate rating updated for story <story_id>."
                }
              - On failure: {
                    "success": False,
                    "error": "Story does not exist."
                }

        Constraints:
            - Only consider reviews for this story that have a moderation_status of 'approved'.
            - If there are no approved reviews, set average_rating to 0.0 and num_ratings to 0.
        """
        if story_id not in self.stories:
            return { "success": False, "error": "Story does not exist." }

        # Collect ratings from approved reviews for this story
        approved_ratings = [
            review['rating']
            for review in self.reviews.values()
            if review['story_id'] == story_id and review['moderation_status'] == "approved"
        ]

        num_ratings = len(approved_ratings)
        average_rating = float(sum(approved_ratings)) / num_ratings if num_ratings > 0 else 0.0

        self.stories[story_id]['average_rating'] = average_rating
        self.stories[story_id]['num_ratings'] = num_ratings

        return {
            "success": True,
            "message": f"Aggregate rating updated for story {story_id}."
        }

    def delete_review(self, review_id: str) -> dict:
        """
        Remove a review from the system and update story aggregate rating accordingly.

        Args:
            review_id (str): The unique identifier for the review to delete.

        Returns:
            dict: {
                "success": True,
                "message": str  # On successful deletion and update
            }
            or
            {
                "success": False,
                "error": str  # If review_id does not exist
            }

        Constraints:
            - Review must exist.
            - Aggregate rating and rating count for the associated story must be updated after deletion.
            - If story has no remaining ratings, set average_rating=0.0 and num_ratings=0.
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review does not exist"}

        review = self.reviews[review_id]
        story_id = review["story_id"]

        # Remove the review
        del self.reviews[review_id]

        # Recompute aggregate ratings for the story
        ratings = [
            r["rating"]
            for r in self.reviews.values()
            if (
                r["story_id"] == story_id
                and isinstance(r.get("rating", None), int)
                and r.get("moderation_status") == "approved"
            )
        ]

        if story_id in self.stories:
            if ratings:
                avg = sum(ratings) / len(ratings)
                self.stories[story_id]["average_rating"] = avg
                self.stories[story_id]["num_ratings"] = len(ratings)
            else:
                self.stories[story_id]["average_rating"] = 0.0
                self.stories[story_id]["num_ratings"] = 0

        return {
            "success": True,
            "message": f"Review {review_id} deleted and aggregate ratings updated for story {story_id}."
        }

    def create_user(self, user_id: str, username: str, email: str, account_status: str, registration_date: str) -> dict:
        """
        Add a new user to the system.

        Args:
            user_id (str): Unique identifier for the user (must not already exist).
            username (str): The user's display or login name.
            email (str): The user's email address.
            account_status (str): The account status (e.g., 'active', 'pending', 'banned').
            registration_date (str): Registration date in string/ISO format.

        Returns:
            dict: 
                On success: { "success": True, "message": "User <user_id> created successfully" }
                On failure: { "success": False, "error": "User ID already exists" }

        Constraints:
            - User IDs must be unique in the system.
        """
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists" }
    
        self.users[user_id] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "account_status": account_status,
            "registration_date": registration_date
        }
        return { "success": True, "message": f"User {user_id} created successfully" }

    def create_story(
        self,
        story_id: str,
        title: str,
        author_id: str,
        content: str,
        branches: Any,
        media_elements: List[str],
        publish_status: str
    ) -> dict:
        """
        Add a new story to the platform.
        Args:
            story_id (str): Unique identifier for the story.
            title (str): Story title.
            author_id (str): User ID of the author (must exist).
            content (str): Story content.
            branches (Any): Branch data structure for story navigation.
            media_elements (List[str]): Media asset identifiers (URLs, paths, etc).
            publish_status (str): Current story publishing status.

        Returns:
            dict: {
                "success": True,
                "message": "Story created",
                "story_id": str
            }
            OR
            {
                "success": False,
                "error": str (reason)
            }

        Constraints:
            - story_id must be unique.
            - author_id must point to an existing user.
            - Initializes average_rating=0.0 and num_ratings=0
        """
        # Validate story_id
        if story_id in self.stories:
            return { "success": False, "error": "Story ID already exists" }
        # Validate author
        if author_id not in self.users:
            return { "success": False, "error": "Author user does not exist" }
        # Validate mandatory fields
        if not all([story_id, title, author_id, content, branches is not None, media_elements is not None, publish_status]):
            return { "success": False, "error": "Missing one or more required fields" }

        story: StoryInfo = {
            "story_id": story_id,
            "title": title,
            "author_id": author_id,
            "content": content,
            "branches": branches,
            "media_elements": media_elements,
            "average_rating": 0.0,
            "num_ratings": 0,
            "publish_status": publish_status
        }
        self.stories[story_id] = story
        return { "success": True, "message": "Story created", "story_id": story_id }

    def change_story_publish_status(self, story_id: str, new_status: str) -> dict:
        """
        Change the publication status of a story (publish or unpublish it).

        Args:
            story_id (str): Unique identifier of the story.
            new_status (str): New publish status to set (e.g., 'published', 'unpublished').

        Returns:
            dict: {
                "success": True,
                "message": "Story <story_id> publish status changed to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<Reason for failure>"
            }

        Constraints:
            - story_id must exist in self.stories.
            - new_status should be a valid non-empty string (suggested: 'published', 'unpublished').
        """
        if story_id not in self.stories:
            return { "success": False, "error": f"Story '{story_id}' does not exist." }

        # Acceptable statuses (might want to extend with more statuses based on platform)
        valid_statuses = {'published', 'unpublished', 'draft'}
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "New status must be a non-empty string." }
        if new_status not in valid_statuses:
            return { "success": False, "error": f"Invalid publish status '{new_status}'." }

        current_status = self.stories[story_id]['publish_status']
        self.stories[story_id]['publish_status'] = new_status

        if current_status == new_status:
            msg = f"Story '{story_id}' publish status was already '{new_status}'."
        else:
            msg = f"Story '{story_id}' publish status changed to '{new_status}'."

        return { "success": True, "message": msg }


class InteractiveStoryPlatform(BaseEnv):
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

    def check_user_exists(self, **kwargs):
        return self._call_inner_tool('check_user_exists', kwargs)

    def get_story_by_id(self, **kwargs):
        return self._call_inner_tool('get_story_by_id', kwargs)

    def check_story_exists(self, **kwargs):
        return self._call_inner_tool('check_story_exists', kwargs)

    def check_story_published(self, **kwargs):
        return self._call_inner_tool('check_story_published', kwargs)

    def get_review_by_user_and_story(self, **kwargs):
        return self._call_inner_tool('get_review_by_user_and_story', kwargs)

    def list_reviews_by_story(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_story', kwargs)

    def list_reviews_by_user(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_user', kwargs)

    def get_review_moderation_status(self, **kwargs):
        return self._call_inner_tool('get_review_moderation_status', kwargs)

    def get_story_rating_info(self, **kwargs):
        return self._call_inner_tool('get_story_rating_info', kwargs)

    def add_or_update_review(self, **kwargs):
        return self._call_inner_tool('add_or_update_review', kwargs)

    def moderate_review(self, **kwargs):
        return self._call_inner_tool('moderate_review', kwargs)

    def update_story_aggregate_rating(self, **kwargs):
        return self._call_inner_tool('update_story_aggregate_rating', kwargs)

    def delete_review(self, **kwargs):
        return self._call_inner_tool('delete_review', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def create_story(self, **kwargs):
        return self._call_inner_tool('create_story', kwargs)

    def change_story_publish_status(self, **kwargs):
        return self._call_inner_tool('change_story_publish_status', kwargs)
