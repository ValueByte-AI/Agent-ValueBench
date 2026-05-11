# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime



class ArticleInfo(TypedDict):
    article_id: str
    title: str
    authors: List[str]
    publication_date: str
    content: str
    keywords: List[str]
    source: str

class UserInfo(TypedDict):
    _id: str
    username: str
    preference: Dict[str, str]  # Assuming preference is a dict; adjust type as needed

class UserReadHistoryInfo(TypedDict):
    _id: str       # user ID
    article_id: str
    read_timestamp: str

class UserStarredArticleInfo(TypedDict):
    _id: str       # user ID
    article_id: str
    starred_timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for personal article aggregation and management.
        """

        # Articles: {article_id: ArticleInfo}
        # Entity: Article [article_id, title, authors, publication_date, content, keywords, source]
        self.articles: Dict[str, ArticleInfo] = {}

        # Users: {_id: UserInfo}
        # Entity: User [_id, username, preference]
        self.users: Dict[str, UserInfo] = {}

        # User read history: {_id: List[UserReadHistoryInfo]}
        # Entity: UserReadHistory [_id, article_id, read_timestamp]
        self.user_read_history: Dict[str, List[UserReadHistoryInfo]] = {}

        # User starred/bookmarked articles: {_id: List[UserStarredArticleInfo]}
        # Entity: UserStarredArticle [_id, article_id, starred_timestamp]
        self.user_starred_articles: Dict[str, List[UserStarredArticleInfo]] = {}

        # Constraints:
        # - An article can be starred by multiple users independently.
        # - Each (user_id, article_id) pair is unique in UserReadHistory and UserStarredArticle.
        # - Search/filter operations depend on article attributes and user read history.
        # - Bookmarking/starred status only affects the specific user performing the action.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information by username.

        Args:
            username (str): The username to look up.

        Returns:
            dict: 
                - { "success": True, "data": UserInfo } if user is found
                - { "success": False, "error": "User not found" } if no such user

        Constraints:
            - Username is assumed to be unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_articles_by_keywords_and_date(
        self,
        keywords: list,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Search for articles filtered by provided keyword list (at least one match), and a publication date range (inclusive).

        Args:
            keywords (List[str]): List of keywords to match (OR).
            start_date (str): Start date in ISO format 'YYYY-MM-DD' (inclusive).
            end_date (str): End date in ISO format 'YYYY-MM-DD' (inclusive).

        Returns:
            dict:
                - success: True, data: List[ArticleInfo] for matching articles
                - success: False, error: description of error

        Notes:
            - If keywords is empty, search only by date.
            - If dates are invalid or start_date > end_date, returns error.
            - If no matches, returns an empty data list.
        """

        # Validate date strings
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            return { "success": False, "error": "Invalid date format. Use YYYY-MM-DD." }

        if start_dt > end_dt:
            return { "success": False, "error": "start_date cannot be later than end_date." }

        matches = []
        for article in self.articles.values():
            # Publication date filter
            try:
                pub_dt = datetime.datetime.strptime(article['publication_date'], "%Y-%m-%d").date()
            except Exception:
                continue  # Skip articles with invalid dates

            if not (start_dt <= pub_dt <= end_dt):
                continue

            # Keyword filter
            if keywords:
                if not any(kw.lower() in [k.lower() for k in article.get('keywords', [])] for kw in keywords):
                    continue  # No keyword matches
            # else: no keyword filter

            matches.append(article)

        return { "success": True, "data": matches }

    def get_user_read_history(self, user_id: str) -> dict:
        """
        Retrieve the list of articles a user has read, with timestamps.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict: {
                "success": True,
                "data": List[UserReadHistoryInfo]  # List of read articles (may be empty)
            }
            or {
                "success": False,
                "error": str  # e.g., user does not exist
            }

        Constraints:
            - The user must exist in the platform.
            - Always returns a list (may be empty if user has not read any articles).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        read_history = self.user_read_history.get(user_id, [])
        return { "success": True, "data": read_history }

    def has_user_read_article(self, user_id: str, article_id: str) -> dict:
        """
        Check whether a specific user has read a specific article.

        Args:
            user_id (str): The user's unique identifier.
            article_id (str): The article's unique identifier.

        Returns:
            dict: On success:
                    { "success": True, "data": True/False }
                  On error:
                    { "success": False, "error": "reason" }

        Constraints:
            - User must exist.
            - Article must exist.
            - (user_id, article_id) is unique in user read history.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist" }

        user_history = self.user_read_history.get(user_id, [])
        for record in user_history:
            if record["article_id"] == article_id:
                return { "success": True, "data": True }
        return { "success": True, "data": False }

    def get_user_starred_articles(self, user_id: str) -> dict:
        """
        Retrieve the list of articles a user has starred/bookmarked.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                success: True if operation is successful.
                data: List of dicts, each with:
                    - "article": ArticleInfo (the article's information)
                    - "starred_timestamp": str (when it was starred)
                OR
                success: False, error: str (if user does not exist)

        Constraints:
            - User must exist.
            - If user has no starred articles, data is an empty list.
            - Article metadata is matched via article_id; missing articles are skipped.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        starred_entries = self.user_starred_articles.get(user_id, [])
        result = []
        for entry in starred_entries:
            article_id = entry.get("article_id")
            article_info = self.articles.get(article_id)
            if article_info:
                result.append({
                    "article": article_info,
                    "starred_timestamp": entry["starred_timestamp"]
                })
            # If article_id missing from self.articles (inconsistent data), skip.

        return {"success": True, "data": result}

    def has_user_starred_article(self, user_id: str, article_id: str) -> dict:
        """
        Check if a specific user has already starred/bookmarked a specific article.

        Args:
            user_id (str): The user's unique ID.
            article_id (str): The article's unique ID.

        Returns:
            dict: {
                "success": True,
                "data": bool    # True if user has starred this article, False otherwise
            }
            or
            {
                "success": False,
                "error": str    # Reason for failure (e.g. invalid user or article)
            }

        Constraints:
            - Both user and article must exist.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check article existence
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist"}

        # Check if the article is starred by the user
        starred_list = self.user_starred_articles.get(user_id, [])
        found = any(item["article_id"] == article_id for item in starred_list)
        return {"success": True, "data": found}

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Retrieve all metadata for an article, using its article_id.

        Args:
            article_id (str): The unique identifier of the article.

        Returns:
            dict: {
                "success": True,
                "data": ArticleInfo  # All metadata for the article
            }
            or
            {
                "success": False,
                "error": str  # "Article not found" if the ID is invalid
            }
    
        Constraints:
            - The specified article_id must exist in the articles collection.
        """
        article = self.articles.get(article_id)
        if article is None:
            return {"success": False, "error": "Article not found"}

        return {"success": True, "data": article}

    def star_article_for_user(self, user_id: str, article_id: str, starred_timestamp: str) -> dict:
        """
        Add an article to a user's starred/bookmarked list, if not already present.

        Args:
            user_id (str): The unique user ID.
            article_id (str): The article's unique ID.
            starred_timestamp (str): The timestamp for when the article was starred/bookmarked.

        Returns:
            dict: 
            On success:
                {"success": True, "message": "Article starred for user."}
            On failure:
                {"success": False, "error": <reason>}

        Constraints:
            - The user must exist.
            - The article must exist.
            - Each (user_id, article_id) pair is unique (cannot be starred twice).
            - Operation affects only the given user's starred list.
        """

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check article exists
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist."}

        user_starred = self.user_starred_articles.setdefault(user_id, [])
        # Check for duplicate
        for starred in user_starred:
            if starred["article_id"] == article_id:
                return {"success": False, "error": "Article already starred by user."}

        # Add to starred list
        self.user_starred_articles[user_id].append({
            "_id": user_id,
            "article_id": article_id,
            "starred_timestamp": starred_timestamp
        })
        return {"success": True, "message": "Article starred for user."}

    def unstar_article_for_user(self, user_id: str, article_id: str) -> dict:
        """
        Remove an article from a user's starred/bookmarked list.

        Args:
            user_id (str): The user's unique ID.
            article_id (str): The article's unique ID.

        Returns:
            dict: On success:
                      { "success": True, "message": "Article unstarred for user." }
                  On failure:
                      { "success": False, "error": <reason> }

        Constraints:
            - User and article must exist.
            - The (user_id, article_id) pair must be present in the starred list.
            - Bookmarking/starred status only affects the given user.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check if article exists
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist." }

        # Check if the user has any starred articles
        starred_list = self.user_starred_articles.get(user_id, [])
        idx_to_remove = None
        for idx, record in enumerate(starred_list):
            if record["article_id"] == article_id:
                idx_to_remove = idx
                break

        if idx_to_remove is None:
            return { "success": False, "error": "Article is not starred by this user." }

        # Remove the article from the user's starred list
        del self.user_starred_articles[user_id][idx_to_remove]
        return { "success": True, "message": "Article unstarred for user." }

    def add_article_to_user_read_history(self, user_id: str, article_id: str, read_timestamp: str) -> dict:
        """
        Records that a user has read a specified article, adding a read history entry if not already present.

        Args:
            user_id (str): The user's unique identifier.
            article_id (str): The article's unique identifier.
            read_timestamp (str): Timestamp when the article was read.

        Returns:
            dict:
                - On success: { "success": True, "message": "Article added to user read history." }
                - On failure: { "success": False, "error": "..." }

        Constraints:
            - user_id must exist.
            - article_id must exist.
            - Each (user_id, article_id) pair is unique in the read history.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist." }

        # Initialize user read history if not present
        history = self.user_read_history.setdefault(user_id, [])

        # Check uniqueness
        for record in history:
            if record["article_id"] == article_id:
                return { "success": False, "error": "Article already present in user read history." }

        # Add new record
        new_record = {
            "_id": user_id,
            "article_id": article_id,
            "read_timestamp": read_timestamp
        }
        history.append(new_record)
        return { "success": True, "message": "Article added to user read history." }

    def remove_article_from_user_read_history(self, user_id: str, article_id: str) -> dict:
        """
        Remove a specific read-history entry for a user.

        Args:
            user_id (str): The user's unique identifier.
            article_id (str): The article's unique identifier whose read history to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Read history entry removed for user and article."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (user not found, entry not found, etc.)
            }

        Constraints:
            - The user must exist.
            - There must be a read history entry for the (user_id, article_id) pair.
            - Each (user_id, article_id) pair should be unique (at most one entry).
        """

        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if user_id not in self.user_read_history or not self.user_read_history[user_id]:
            return { "success": False, "error": "No read history for user" }

        user_history = self.user_read_history[user_id]
        entry_found = False
        for idx, entry in enumerate(user_history):
            if entry["article_id"] == article_id:
                entry_found = True
                del user_history[idx]
                # If no more read history entries, optionally remove key entirely
                if not user_history:
                    self.user_read_history[user_id] = []
                return { 
                    "success": True, 
                    "message": "Read history entry removed for user and article." 
                }
        return { 
            "success": False, 
            "error": "Read history entry for this article does not exist for the user" 
        }

    def update_user_preferences(self, user_id: str, new_preferences: dict) -> dict:
        """
        Modify the preference attributes for a specific user.

        Args:
            user_id (str): The ID of the user whose preferences should be updated.
            new_preferences (dict): The new/updated preferences to apply (merged into existing preferences).

        Returns:
            dict: { "success": True, "message": "User preferences updated." }
                  or { "success": False, "error": "User does not exist." }

        Constraints:
            - The user must exist in the platform.
            - Only the specified user's preferences are updated.
            - The preferences are merged: fields present in new_preferences overwrite existing ones.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if not isinstance(new_preferences, dict):
            return { "success": False, "error": "new_preferences must be a dictionary." }

        user_pref = self.users[user_id].get("preference", {})
        user_pref.update(new_preferences)
        self.users[user_id]["preference"] = user_pref

        return { "success": True, "message": "User preferences updated." }

    def bulk_star_articles_for_user(self, user_id: str, article_ids: list, starred_timestamp: str) -> dict:
        """
        Star multiple articles for a user in a single operation, ensuring each (user_id, article_id)
        pair is unique in UserStarredArticle.

        Args:
            user_id (str): The ID of the user who is starring the articles.
            article_ids (List[str]): List of article IDs to star.
            starred_timestamp (str): Timestamp to record for the starring action.

        Returns:
            dict: {
                "success": True,
                "message": "Starred X new articles for user {user_id}."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Each article_id must exist; nonexistent articles are skipped.
            - Each (user_id, article_id) pair appears only once in the starred list.
            - If no article was newly starred, reflects in message.
        """

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Initialize starred list if not exists
        user_starred = self.user_starred_articles.setdefault(user_id, [])

        # Create lookup for fast (user, article_id) existence check
        already_starred_ids = set(item["article_id"] for item in user_starred)

        newly_starred_count = 0

        for article_id in article_ids:
            if article_id not in self.articles:
                continue  # Skip non-existent articles
            if article_id in already_starred_ids:
                continue  # Skip already starred
            # Add new star
            new_star = {
                "_id": user_id,
                "article_id": article_id,
                "starred_timestamp": starred_timestamp
            }
            user_starred.append(new_star)
            already_starred_ids.add(article_id)
            newly_starred_count += 1

        return {
            "success": True,
            "message": f"Starred {newly_starred_count} new articles for user {user_id}."
        }


class PersonalArticleManagementPlatform(BaseEnv):
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

    def get_articles_by_keywords_and_date(self, **kwargs):
        return self._call_inner_tool('get_articles_by_keywords_and_date', kwargs)

    def get_user_read_history(self, **kwargs):
        return self._call_inner_tool('get_user_read_history', kwargs)

    def has_user_read_article(self, **kwargs):
        return self._call_inner_tool('has_user_read_article', kwargs)

    def get_user_starred_articles(self, **kwargs):
        return self._call_inner_tool('get_user_starred_articles', kwargs)

    def has_user_starred_article(self, **kwargs):
        return self._call_inner_tool('has_user_starred_article', kwargs)

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def star_article_for_user(self, **kwargs):
        return self._call_inner_tool('star_article_for_user', kwargs)

    def unstar_article_for_user(self, **kwargs):
        return self._call_inner_tool('unstar_article_for_user', kwargs)

    def add_article_to_user_read_history(self, **kwargs):
        return self._call_inner_tool('add_article_to_user_read_history', kwargs)

    def remove_article_from_user_read_history(self, **kwargs):
        return self._call_inner_tool('remove_article_from_user_read_history', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def bulk_star_articles_for_user(self, **kwargs):
        return self._call_inner_tool('bulk_star_articles_for_user', kwargs)

