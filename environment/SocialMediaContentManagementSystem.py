# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict



class PostInfo(TypedDict):
    post_id: str
    content: str
    author_id: str
    creation_time: str
    language_id: str
    metadata: Dict[str, Any]

class ScoreInfo(TypedDict):
    score_id: str
    post_id: str
    user_id: str
    value: float
    scale: float
    language_id: str
    creation_time: str
    metadata: Dict[str, Any]

class LanguageInfo(TypedDict):
    language_id: str
    name: str
    language_voice: str

class UserInfo(TypedDict):
    user_id: str
    display_name: str
    profile_info: Dict[str, Any]
    account_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for social media content management.
        """

        # Posts: {post_id: PostInfo}
        self.posts: Dict[str, PostInfo] = {}
        # Maps to state entity "Pos": post_id, content, author_id, creation_time, language_id, metadata

        # Scores: {score_id: ScoreInfo}
        self.scores: Dict[str, ScoreInfo] = {}
        # Maps to state entity "Score": score_id, post_id, user_id, value, scale, language_id, creation_time, metadata

        # Languages: {language_id: LanguageInfo}
        self.languages: Dict[str, LanguageInfo] = {}
        # Maps to state entity "Language": language_id, name, language_voice

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Maps to state entity "User": user_id, display_name, profile_info, account_status

        # Constraints:
        # - Each post must reference an existing language.
        # - Each score must reference an existing post, user, and language, and have a valid scale.
        # - The score value must be within the valid range for the given scale.
        # - Posts and scores cannot exist without their referenced entities.

    def get_post_by_id(self, post_id: str) -> dict:
        """
        Retrieve the complete details of a post using its post_id.

        Args:
            post_id (str): The unique identifier of the post to retrieve.

        Returns:
            dict:
                - If found:
                    {
                        "success": True,
                        "data": PostInfo  # All post fields
                    }
                - If not found:
                    {
                        "success": False,
                        "error": "Post not found"
                    }

        Constraints:
            - This function does not check the validity of referenced entities (e.g., language) for retrieval.
            - Only returns information if the post exists.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post not found"}
        return {"success": True, "data": self.posts[post_id]}

    def get_score_by_id(self, score_id: str) -> dict:
        """
        Retrieve the complete details of a score using its score_id.

        Args:
            score_id (str): The unique identifier of the score.

        Returns:
            dict: 
              On success: {"success": True, "data": ScoreInfo}
              On failure: {"success": False, "error": "Score not found"}
        Constraints:
            - The score with the given score_id must exist.
        """
        score = self.scores.get(score_id)
        if score is None:
            return {"success": False, "error": "Score not found"}
        return {"success": True, "data": score}

    def list_all_posts(self) -> dict:
        """
        Retrieve a list with metadata of all existing posts in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[PostInfo],  # A list (possibly empty) of all PostInfo dicts in the system
            }
        """
        all_posts = list(self.posts.values())
        return { "success": True, "data": all_posts }

    def list_all_scores(self) -> dict:
        """
        Retrieve a list of all scores in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ScoreInfo]  # May be empty if there are no scores
            }
        """
        # Return all ScoreInfo dicts as a list
        all_scores = list(self.scores.values())
        return { "success": True, "data": all_scores }

    def get_language_by_id(self, language_id: str) -> dict:
        """
        Fetch language details including language_id, name, and language_voice using the given language_id.

        Args:
            language_id (str): Identifier of the language to fetch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": LanguageInfo  # The language details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Language not found"
                    }

        Constraints:
            - language_id must exist in self.languages.
        """
        language = self.languages.get(language_id)
        if language is None:
            return {"success": False, "error": "Language not found"}
        return {"success": True, "data": language}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details using the provided user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Dictionary containing the user's details
            }
            or
            {
                "success": False,
                "error": str  # If the user does not exist
            }

        Constraints:
            - The user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_post_language(self, post_id: str) -> dict:
        """
        For a given post_id, return its associated language's details.

        Args:
            post_id (str): Identifier of the post.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": LanguageInfo  # The associated language info.
                    }
                On failure (missing post or language):
                    {
                        "success": False,
                        "error": str  # Reason for failure.
                    }

        Constraints:
            - The post must exist.
            - The language referenced by the post must exist.
        """
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": "Post does not exist"}

        language_id = post.get("language_id")
        language = self.languages.get(language_id)
        if not language:
            return {"success": False, "error": "Associated language does not exist"}

        return {"success": True, "data": language}

    def get_score_language(self, score_id: str) -> dict:
        """
        Retrieve the language details (LanguageInfo) associated with the given score_id.

        Args:
            score_id (str): The ID of the score to query.

        Returns:
            dict: {
                "success": True,
                "data": LanguageInfo      # Language info referenced by the score
            }
            or
            {
                "success": False,
                "error": str              # Reason why query failed
            }

        Constraints:
            - The score_id must exist.
            - The score must reference a valid language_id (exist in languages).
        """
        score = self.scores.get(score_id)
        if not score:
            return { "success": False, "error": "Score not found" }

        language_id = score.get("language_id")
        language_info = self.languages.get(language_id)
        if not language_info:
            return { "success": False, "error": "Referenced language not found" }

        return { "success": True, "data": language_info }

    def list_post_scores(self, post_id: str) -> dict:
        """
        List all scores associated with the given post_id.

        Args:
            post_id (str): The ID of the post for which scores are to be listed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ScoreInfo]  # List of all scores for this post_id (can be empty)
                    }
                - On failure (e.g., post does not exist):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The post_id must exist in self.posts.
            - Returns all ScoreInfo where score['post_id'] == post_id.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist"}

        scores = [
            score for score in self.scores.values()
            if score["post_id"] == post_id
        ]

        return {"success": True, "data": scores}

    def list_user_posts(self, user_id: str) -> dict:
        """
        List all posts authored by the given user_id.

        Args:
            user_id (str): The ID of the user whose posts should be listed.

        Returns:
            dict:
                - If user exists:
                    {
                        "success": True,
                        "data": List[PostInfo]  # List of posts authored by the user (can be empty)
                    }
                - If user does not exist:
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - The specified user_id must reference an existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            post_info for post_info in self.posts.values()
            if post_info["author_id"] == user_id
        ]

        return { "success": True, "data": result }

    def list_user_scores(self, user_id: str) -> dict:
        """
        List all scores given by a specific user.

        Args:
            user_id (str): The identifier of the user whose scores are to be listed.

        Returns:
            dict: {
                 "success": True,
                 "data": List[ScoreInfo]   # All scores where score['user_id'] == user_id (can be empty)
            }
            or
            {
                 "success": False,
                 "error": str  # Reason for failure (e.g., user does not exist)
            }

        Constraints:
            - The user referenced by user_id must exist prior to making this query.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        scores = [
            score_info for score_info in self.scores.values()
            if score_info["user_id"] == user_id
        ]
        return {"success": True, "data": scores}

    def create_post(
        self,
        post_id: str,
        content: str,
        author_id: str,
        creation_time: str,
        language_id: str,
        metadata: dict
    ) -> dict:
        """
        Create a new post with the given attributes.

        Args:
            post_id (str): Unique identifier for the post.
            content (str): The body/content of the post.
            author_id (str): The user_id of the post's author (must refer to an existing user).
            creation_time (str): The UTC/ISO string for the post creation timestamp.
            language_id (str): The language identifier (must refer to an existing language).
            metadata (dict): Additional metadata about the post.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Post created successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - post_id must be unique (not already present).
            - author_id must reference an existing user.
            - language_id must reference an existing language.
        """
        if post_id in self.posts:
            return {"success": False, "error": "Post ID already exists."}

        if author_id not in self.users:
            return {"success": False, "error": "Author (user_id) does not exist."}

        if language_id not in self.languages:
            return {"success": False, "error": "Language (language_id) does not exist."}

        self.posts[post_id] = {
            "post_id": post_id,
            "content": content,
            "author_id": author_id,
            "creation_time": creation_time,
            "language_id": language_id,
            "metadata": metadata
        }

        return {"success": True, "message": "Post created successfully."}

    def update_post_content(self, post_id: str, content: str = None, metadata: dict = None) -> dict:
        """
        Update the content and/or metadata of an existing post.

        Args:
            post_id (str): The unique identifier of the post.
            content (Optional[str]): The new content for the post (if updating).
            metadata (Optional[dict]): Keys and values to update in the metadata (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Post content and/or metadata updated."
            }
            or
            {
                "success": False,
                "error": "Post does not exist." | "Nothing to update." | "Metadata must be a dictionary."
            }

        Constraints:
            - Post must exist.
            - If metadata is provided, it must be a dict.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist."}

        if content is None and metadata is None:
            return {"success": False, "error": "Nothing to update."}

        post = self.posts[post_id]

        if content is not None:
            post["content"] = content

        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "Metadata must be a dictionary."}
            # Merge/overwrite the specified keys in the existing metadata
            post["metadata"].update(metadata)

        self.posts[post_id] = post  # Update post in storage (not strictly necessary if mutable dict)

        return {"success": True, "message": "Post content and/or metadata updated."}

    def delete_post(self, post_id: str) -> dict:
        """
        Remove a post by its post_id if no score entity references it.

        Args:
            post_id (str): The unique identifier of the post to delete.
        
        Returns:
            dict: 
                {"success": True, "message": "Post deleted" }
                OR
                {"success": False, "error": "<reason>"}

        Constraints:
            - The post must exist.
            - No Score must reference this post_id.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist"}

        # Check for referencing scores
        for score in self.scores.values():
            if score["post_id"] == post_id:
                return {
                    "success": False,
                    "error": "Cannot delete post: it is referenced by at least one score."
                }

        # No reference found, safe to delete
        del self.posts[post_id]
        return {"success": True, "message": "Post deleted"}

    def create_score(
        self,
        score_id: str,
        post_id: str,
        user_id: str,
        value: float,
        scale: float,
        language_id: str,
        creation_time: str,
        metadata: dict = None
    ) -> dict:
        """
        Create a new score for a post by a user.

        Args:
            score_id (str): Unique identifier for the score.
            post_id (str): ID of the post being scored.
            user_id (str): ID of the user who gives the score.
            value (float): The score value (must be in [0, scale]).
            scale (float): The maximum possible value for the score (must be > 0).
            language_id (str): The language context of the score.
            creation_time (str): ISO 8601 or other formatted creation timestamp.
            metadata (dict): Additional info (optional).

        Returns:
            dict:
                On success: { "success": True, "message": "Score <score_id> created." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - score_id must be unique.
            - post_id, user_id, and language_id must reference valid, existing entities.
            - scale must be > 0.
            - value must be in the inclusive range [0, scale].
        """

        # Check for duplicate score_id
        if score_id in self.scores:
            return { "success": False, "error": f"Score ID '{score_id}' already exists." }
        # Check if referenced post exists
        if post_id not in self.posts:
            return { "success": False, "error": f"Referenced post_id '{post_id}' does not exist." }
        # Check if referenced user exists
        if user_id not in self.users:
            return { "success": False, "error": f"Referenced user_id '{user_id}' does not exist." }
        # Check if referenced language exists
        if language_id not in self.languages:
            return { "success": False, "error": f"Referenced language_id '{language_id}' does not exist." }
        # Scale must be positive
        if not isinstance(scale, (float, int)) or scale <= 0:
            return { "success": False, "error": "Scale must be a positive number." }
        # Value must be in [0, scale]
        if not isinstance(value, (float, int)) or value < 0 or value > scale:
            return { "success": False, "error": f"Value {value} must be between 0 and scale {scale}." }

        if metadata is None:
            metadata = {}

        score_info = {
            "score_id": score_id,
            "post_id": post_id,
            "user_id": user_id,
            "value": value,
            "scale": scale,
            "language_id": language_id,
            "creation_time": creation_time,
            "metadata": metadata
        }

        self.scores[score_id] = score_info
        return { "success": True, "message": f"Score '{score_id}' created." }

    def update_score_value(
        self,
        score_id: str,
        value: float = None,
        scale: float = None,
        metadata: dict = None
    ) -> dict:
        """
        Update the value, scale, and/or metadata of a score, ensuring value is valid for scale.

        Args:
            score_id (str): The ID of the score to update.
            value (float, optional): The new score value. Will be set if provided.
            scale (float, optional): The new valid scale. Will be set if provided.
            metadata (dict, optional): The new metadata. Will be set if provided.

        Returns:
            dict: {
                "success": True,
                "message": "Score value/scale/metadata updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. not found, invalid value)
            }

        Constraints:
            - The referenced score_id must exist.
            - If value or scale change, the value must be within [0, scale] after the update.
        """
        if score_id not in self.scores:
            return { "success": False, "error": "Score not found" }

        score = self.scores[score_id]

        # Determine new value and scale for validation
        new_value = value if value is not None else score["value"]
        new_scale = scale if scale is not None else score["scale"]

        # Validate value range (can only be checked if both are not None)
        if new_value < 0 or new_value > new_scale:
            return {
                "success": False,
                "error": f"Score value {new_value} out of range for scale {new_scale}"
            }

        # Perform updates
        if value is not None:
            score["value"] = value
        if scale is not None:
            score["scale"] = scale
        if metadata is not None:
            score["metadata"] = metadata

        self.scores[score_id] = score

        return {
            "success": True,
            "message": "Score value/scale/metadata updated successfully."
        }

    def delete_score(self, score_id: str) -> dict:
        """
        Remove a score from the system by its score_id.

        Args:
            score_id (str): The identifier of the score to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Score <score_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Score does not exist."
            }

        Constraints:
            - The given score_id must exist in the system.
            - If not found, return a descriptive error.
        """
        if score_id not in self.scores:
            return { "success": False, "error": "Score does not exist." }
        del self.scores[score_id]
        return { "success": True, "message": f"Score {score_id} deleted." }

    def create_language(self, language_id: str, name: str, language_voice: str) -> dict:
        """
        Add a new language to the system.

        Args:
            language_id (str): Unique identifier for the language.
            name (str): Human-readable name of the language.
            language_voice (str): Attribute representing the language's voice or dialect/engine.

        Returns:
            dict: 
                { "success": True, "message": "Language <language_id> created" }
                OR
                { "success": False, "error": "Language id already exists" }

        Constraints:
            - language_id must be unique and not already present in the system.
        """
        if not language_id or not name or not language_voice:
            return {"success": False, "error": "Missing required language attributes"}
        if language_id in self.languages:
            return {"success": False, "error": "Language id already exists"}

        self.languages[language_id] = {
            "language_id": language_id,
            "name": name,
            "language_voice": language_voice
        }
        return {"success": True, "message": f"Language {language_id} created"}

    def update_language(self, language_id: str, name: str = None, language_voice: str = None) -> dict:
        """
        Update the 'name' and/or 'language_voice' of an existing language.

        Args:
            language_id (str): ID of the language to update.
            name (str, optional): New display name for the language.
            language_voice (str, optional): New voice/variant attribute.

        Returns:
            dict: {
                "success": True,
                "message": "Language <language_id> updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - language_id must exist in the system.
            - At least one of 'name' or 'language_voice' must be provided.
        """
        # Check existence
        if language_id not in self.languages:
            return {"success": False, "error": f"Language {language_id} does not exist."}

        if name is None and language_voice is None:
            return {"success": False, "error": "No update fields provided; specify at least one field (name or language_voice)."}

        # Update fields if given
        updated = False
        lang = self.languages[language_id]
        if name is not None:
            lang["name"] = name
            updated = True
        if language_voice is not None:
            lang["language_voice"] = language_voice
            updated = True

        return {"success": True, "message": f"Language {language_id} updated."}

    def delete_language(self, language_id: str) -> dict:
        """
        Remove a language, if no posts or scores reference it.

        Args:
            language_id (str): The language's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Language <language_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Language not found." | "Language is still referenced by posts or scores."
            }

        Constraints:
            - The specified language cannot be deleted if it is referenced by any post or score.
        """
        # Check if language exists
        if language_id not in self.languages:
            return { "success": False, "error": "Language not found." }

        # Check for references in posts
        for post in self.posts.values():
            if post["language_id"] == language_id:
                return { "success": False, "error": "Language is still referenced by posts or scores." }

        # Check for references in scores
        for score in self.scores.values():
            if score["language_id"] == language_id:
                return { "success": False, "error": "Language is still referenced by posts or scores." }

        # Passed constraints, can delete
        del self.languages[language_id]
        return { "success": True, "message": f"Language {language_id} deleted." }

    def create_user(
        self,
        user_id: str,
        display_name: str,
        profile_info: dict,
        account_status: str
    ) -> dict:
        """
        Register a new user in the system.

        Args:
            user_id (str): Unique identifier for the user.
            display_name (str): User's display name.
            profile_info (dict): Profile-related details (may be empty).
            account_status (str): Status of the account ("active", "inactive", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "User created successfully"
            }
            or
            {
                "success": False,
                "error": <reason for failure>
            }

        Constraints:
            - `user_id` must be unique (not already in the system).
            - All fields required (minimal validation).
        """
        if not user_id or not isinstance(user_id, str):
            return {"success": False, "error": "user_id is required and must be a non-empty string"}
        if user_id in self.users:
            return {"success": False, "error": "User ID already exists"}
        if not display_name or not isinstance(display_name, str):
            return {"success": False, "error": "display_name is required and must be a non-empty string"}
        if profile_info is None or not isinstance(profile_info, dict):
            return {"success": False, "error": "profile_info must be a dictionary"}
        if not account_status or not isinstance(account_status, str):
            return {"success": False, "error": "account_status is required and must be a non-empty string"}

        user_info: UserInfo = {
            "user_id": user_id,
            "display_name": display_name,
            "profile_info": profile_info,
            "account_status": account_status
        }
        self.users[user_id] = user_info

        return {"success": True, "message": "User created successfully"}

    def update_user_profile(
        self,
        user_id: str,
        profile_info: dict = None,
        account_status: str = None
    ) -> dict:
        """
        Update the profile information and/or account status of an existing user.

        Args:
            user_id (str): The ID of the user to update.
            profile_info (dict, optional): The new profile information to merge or update.
            account_status (str, optional): The new account status to set (e.g., "active", "banned").

        Returns:
            dict: {
                "success": True,
                "message": "User profile updated."
            }
            or
            {
                "success": False,
                "error": str,  # Description of the error.
            }
        Constraints:
            - The user must exist.
            - At least one of profile_info or account_status must be provided.
            - For profile_info, performs a merge/update rather than an overwrite.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist." }

        if profile_info is None and account_status is None:
            return { "success": False, "error": "No update content provided." }

        if profile_info is not None:
            # Merge/update the profile_info dict (not overwrite)
            user["profile_info"].update(profile_info)

        if account_status is not None:
            user["account_status"] = account_status

        # Update in users dict (already in-place modification)
        self.users[user_id] = user
        return { "success": True, "message": "User profile updated." }

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user from the system, if no posts or scores reference them.

        Args:
            user_id (str): The unique identifier of the user to be deleted.

        Returns:
            dict:
                On success: { "success": True, "message": "User <user_id> deleted." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Cannot delete user if any post references them as author_id.
            - Cannot delete user if any score references them as user_id.
            - User must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check posts for author_id reference
        referenced_by_posts = any(post["author_id"] == user_id for post in self.posts.values())
        if referenced_by_posts:
            return { "success": False, "error": "Cannot delete user: referenced by at least one post." }

        # Check scores for user_id reference
        referenced_by_scores = any(score["user_id"] == user_id for score in self.scores.values())
        if referenced_by_scores:
            return { "success": False, "error": "Cannot delete user: referenced by at least one score." }

        # Safe to delete
        del self.users[user_id]
        return { "success": True, "message": f"User {user_id} deleted." }


class SocialMediaContentManagementSystem(BaseEnv):
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

    def get_post_by_id(self, **kwargs):
        return self._call_inner_tool('get_post_by_id', kwargs)

    def get_score_by_id(self, **kwargs):
        return self._call_inner_tool('get_score_by_id', kwargs)

    def list_all_posts(self, **kwargs):
        return self._call_inner_tool('list_all_posts', kwargs)

    def list_all_scores(self, **kwargs):
        return self._call_inner_tool('list_all_scores', kwargs)

    def get_language_by_id(self, **kwargs):
        return self._call_inner_tool('get_language_by_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_post_language(self, **kwargs):
        return self._call_inner_tool('get_post_language', kwargs)

    def get_score_language(self, **kwargs):
        return self._call_inner_tool('get_score_language', kwargs)

    def list_post_scores(self, **kwargs):
        return self._call_inner_tool('list_post_scores', kwargs)

    def list_user_posts(self, **kwargs):
        return self._call_inner_tool('list_user_posts', kwargs)

    def list_user_scores(self, **kwargs):
        return self._call_inner_tool('list_user_scores', kwargs)

    def create_post(self, **kwargs):
        return self._call_inner_tool('create_post', kwargs)

    def update_post_content(self, **kwargs):
        return self._call_inner_tool('update_post_content', kwargs)

    def delete_post(self, **kwargs):
        return self._call_inner_tool('delete_post', kwargs)

    def create_score(self, **kwargs):
        return self._call_inner_tool('create_score', kwargs)

    def update_score_value(self, **kwargs):
        return self._call_inner_tool('update_score_value', kwargs)

    def delete_score(self, **kwargs):
        return self._call_inner_tool('delete_score', kwargs)

    def create_language(self, **kwargs):
        return self._call_inner_tool('create_language', kwargs)

    def update_language(self, **kwargs):
        return self._call_inner_tool('update_language', kwargs)

    def delete_language(self, **kwargs):
        return self._call_inner_tool('delete_language', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

