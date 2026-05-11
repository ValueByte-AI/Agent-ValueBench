# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Tuple, TypedDict



# Feed mapping: feed_id → FeedInfo
class FeedInfo(TypedDict):
    feed_id: str
    title: str
    description: str
    url: str
    last_updated: str  # ISO timestamp, e.g. '2023-04-13T18:02:51Z'

# Article mapping: article_id → ArticleInfo
class ArticleInfo(TypedDict):
    article_id: str
    feed_id: str
    title: str
    content: str
    publication_date: str  # ISO timestamp
    url: str
    author: str  # (Corrected from 'autho')

# User mapping: _id (user_id) → UserInfo
class UserInfo(TypedDict):
    _id: str
    display_name: str
    preferences: dict  # (Corrected from 'preferenc')

# ArticleUserState: (user_id, article_id) → ArticleUserStateInfo
class ArticleUserStateInfo(TypedDict):
    _id: str  # user_id
    article_id: str
    read_status: str
    bookmarked: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for RSS feed reader system.
        """

        # Feeds: {feed_id: FeedInfo}
        self.feeds: Dict[str, FeedInfo] = {}
        # Articles: {article_id: ArticleInfo}
        self.articles: Dict[str, ArticleInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # ArticleUserStates: {(user_id, article_id): ArticleUserStateInfo}
        self.article_user_states: Dict[Tuple[str, str], ArticleUserStateInfo] = {}

        # Constraints (see environment spec):
        # - Each article must be linked to an existing feed.
        # - ArticleUserState exists only if a user has interacted with an article.
        # - Feed keyword search is on the feed's 'title' attribute.
        # - Articles in a feed are ordered by publication_date descending for latest queries.
        # - Only active (non-deleted) feeds/articles are considered in search and retrieval.

    def _normalize_article_user_state_keys(self) -> None:
        normalized = {}
        for key, value in self.article_user_states.items():
            if isinstance(key, tuple) and len(key) == 2:
                normalized[key] = value
                continue
            if not isinstance(value, dict):
                normalized[key] = value
                continue
            user_id = value.get("user_id")
            if not user_id:
                candidate = value.get("_id")
                if candidate in self.users:
                    user_id = candidate
            if not user_id and len(self.users) == 1:
                user_id = next(iter(self.users))
            article_id = value.get("article_id")
            if user_id and article_id:
                value.setdefault("user_id", user_id)
                normalized[(user_id, article_id)] = value
            else:
                normalized[key] = value
        self.article_user_states = normalized

    def _find_article_user_state_key(self, user_id: str, article_id: str):
        direct_key = (user_id, article_id)
        if direct_key in self.article_user_states:
            return direct_key

        for key, value in self.article_user_states.items():
            if not isinstance(value, dict):
                continue
            state_user_id = value.get("user_id")
            if not state_user_id:
                candidate = value.get("_id")
                if candidate in self.users:
                    state_user_id = candidate
            if not state_user_id and len(self.users) == 1:
                state_user_id = next(iter(self.users))
            if state_user_id == user_id and value.get("article_id") == article_id:
                return key
        return None

    def search_feeds_by_title_keyword(self, keyword: str) -> dict:
        """
        Find all active feeds whose `title` contains a given keyword (case-insensitive).

        Args:
            keyword (str): Keyword to search for in feed titles.

        Returns:
            dict:
                { "success": True, "data": List[FeedInfo] }
                If no match, data is empty list.

        Constraints:
            - Search only considers active feeds (if 'active' status is tracked; otherwise, all feeds).
            - The match is performed on the 'title' attribute of Feed, case-insensitive containment.
        """
        if not keyword or not isinstance(keyword, str):
            # An empty or non-string keyword will act as no match.
            return {"success": True, "data": []}
    
        keyword_lower = keyword.lower()
        matching_feeds = []
        for feed in self.feeds.values():
            # Check active status if present; assume all active if not present.
            is_active = feed.get("active", True)
            if not is_active:
                continue
            if keyword_lower in feed["title"].lower():
                matching_feeds.append(feed)
        return {"success": True, "data": matching_feeds}

    def get_feed_by_id(self, feed_id: str) -> dict:
        """
        Retrieve full metadata of a feed by its feed_id, but only if the feed is active.

        Args:
            feed_id (str): Unique identifier of the feed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": FeedInfo  # Full metadata for the requested feed.
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Feed not found or inactive"
                    }

        Constraints:
            - Only active feeds are returned.
            - If the feed does not exist or is inactive, failure is returned.

        Notes:
            - The FeedInfo dict is expected to contain an "active" boolean key.
        """
        feed = self.feeds.get(feed_id)
        if feed is None:
            return {"success": False, "error": "Feed not found or inactive"}
        # Assume FeedInfo has "active" key
        if not feed.get("active", True):
            return {"success": False, "error": "Feed not found or inactive"}
        return {"success": True, "data": feed}

    def list_all_active_feeds(self) -> dict:
        """
        Return the list of all active (non-deleted) feeds in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[FeedInfo],  # May be empty if no feeds/none are active
            }

        Constraints:
            - Only feeds considered 'active' (not deleted) are included.
            - If 'active' attribute is present in FeedInfo, use it to filter.
            - Otherwise, assume all feeds in self.feeds are active.
        """
        feeds_list = []
        for feed in self.feeds.values():
            # Check for 'active' attribute. If present, require it be True.
            if "active" in feed:
                if feed["active"]:
                    feeds_list.append(feed)
            else:
                feeds_list.append(feed)
        return {
            "success": True,
            "data": feeds_list
        }

    def list_articles_by_feed(self, feed_id: str) -> dict:
        """
        List all active articles for a given feed_id, ordered by 'publication_date' descending.

        Args:
            feed_id (str): The ID of the feed whose articles to list.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo]  # list may be empty if no articles for feed,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (feed does not exist/inactive)
            }

        Constraints:
            - Only active (non-deleted) feeds and articles are listed. If 'active' fields are not present,
              all entries in self.feeds/self.articles are considered active.
            - Articles must be ordered by publication_date descending (ISO timestamp).
        """
        # Check that the feed exists
        feed = self.feeds.get(feed_id)
        if not feed or ("active" in feed and not feed["active"]):
            return {"success": False, "error": "Feed does not exist or is inactive"}

        # Get all articles with this feed_id
        articles = [
            article for article in self.articles.values()
            if article["feed_id"] == feed_id and article.get("active", True)
        ]
        # Order by publication_date descending (string order is valid for ISO)
        articles_sorted = sorted(
            articles,
            key=lambda x: x["publication_date"],
            reverse=True
        )
        return {"success": True, "data": articles_sorted}

    def get_latest_articles_by_feed(self, feed_id: str, count: int) -> dict:
        """
        Retrieve the N most recent active articles for a specified feed, sorted by publication_date descending.

        Args:
            feed_id (str): ID of the feed to retrieve articles from.
            count (int): Number of latest articles to retrieve (N ≥ 0).

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": List[ArticleInfo],  # length ≤ count, ordered newest (descending publication_date)
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Feed must exist (present in self.feeds).
            - Only articles with matching feed_id are returned.
            - If active status is ever tracked, only active articles/feeds are returned.
            - Articles sorted by publication_date descending (ISO timestamp string comparison is safe for this).
        """
        feed = self.feeds.get(feed_id)
        if not feed:
            return {"success": False, "error": "Feed does not exist"}
        if "active" in feed and not feed["active"]:
            return {"success": False, "error": "Feed does not exist or is inactive"}

        if count <= 0:
            return {"success": True, "data": []}

        # Get articles belonging to the feed
        articles_for_feed = [
            article for article in self.articles.values()
            if article["feed_id"] == feed_id and article.get("active", True)
        ]

        # If 'is_active' or similar were tracked: filter for it here.
        # e.g.: if article.get('is_active', True): ...

        # Sort articles by publication_date descending (string ISO format is lexicographically sortable)
        articles_sorted = sorted(
            articles_for_feed,
            key=lambda a: a["publication_date"],
            reverse=True
        )

        # Take at most N
        latest_articles = articles_sorted[:count]

        return {"success": True, "data": latest_articles}

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Fetch full data for a single article, only if it is active.

        Args:
            article_id (str): The article's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": ArticleInfo  # Full info for the article
            }
            or
            {
                "success": False,
                "error": str  # 'Article not found or inactive'
            }

        Constraints:
            - Only active (non-deleted) articles may be returned.
        """
        article = self.articles.get(article_id)
        if not article:
            return {"success": False, "error": "Article not found or inactive"}

        # By convention, missing "active" means True (for backward compatibility)
        if "active" in article and not article["active"]:
            return {"success": False, "error": "Article not found or inactive"}

        return {"success": True, "data": article}

    def get_feed_articles_count(self, feed_id: str) -> dict:
        """
        Return the number of active articles for a given feed.

        Args:
            feed_id (str): The ID of the feed.

        Returns:
            dict: On success:
                { "success": True, "data": int }  # The count of active articles
                On error:
                { "success": False, "error": str }  # Reason for error (feed not found, not active)
    
        Constraints:
            - Feed must exist and be active (if 'active' field is present, active==True).
            - Only count articles that are active (if 'active' in ArticleInfo, active==True),
              and whose feed_id == provided feed_id.
        """
        # Check feed existence
        feed = self.feeds.get(feed_id)
        if not feed:
            return { "success": False, "error": "Feed does not exist" }
        # Check feed active status if such a field exists
        if 'active' in feed and not feed['active']:
            return { "success": False, "error": "Feed is not active" }
        # Count active articles
        count = 0
        for article in self.articles.values():
            # Must be for the target feed
            if article.get('feed_id') != feed_id:
                continue
            # If articles have 'active' key, only count if active
            if 'active' in article:
                if article['active']:
                    count += 1
            else:
                # If no 'active' tracking, assume article is active
                count += 1
        return { "success": True, "data": count }

    def get_article_user_state(self, user_id: str, article_id: str) -> dict:
        """
        Check if a user has a read/bookmarked state for a particular article.

        Args:
            user_id (str): The user identifier.
            article_id (str): The article identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ArticleUserStateInfo  # The state object for this user/article.
                    }
                On failure (no state found):
                    {
                        "success": False,
                        "error": "No ArticleUserState for this user-article pair"
                    }

        Constraints:
            - ArticleUserState exists only if a user has previously interacted with an article.
        """
        self._normalize_article_user_state_keys()
        key = self._find_article_user_state_key(user_id, article_id)
        state = self.article_user_states.get(key) if key is not None else None
        if state is not None:
            return { "success": True, "data": state }
        else:
            return { "success": False, "error": "No ArticleUserState for this user-article pair" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Fetch user information (profile, preferences) by user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User profile dictionary if found
            }
            or
            {
                "success": False,
                "error": str  # "User not found"
            }
        Constraints:
            - The user_id must exist in the environment state.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def mark_article_as_read(self, user_id: str, article_id: str) -> dict:
        """
        Sets or updates the read_status of the specified article for the specified user.

        Args:
            user_id (str): The user's unique identifier.
            article_id (str): The article's unique identifier.

        Returns:
            dict: 
                - { "success": True, "message": "Article marked as read for user <user_id>" }
                - { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - Article must exist and be active (if "active" flag exists, must be True).
            - Article must link to an existing and active feed.
            - Creates ArticleUserState if it doesn't exist. Updates otherwise.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Check article exists
        article = self.articles.get(article_id)
        if not article:
            return {"success": False, "error": "Article not found"}
        # Check if article is active (if "active" field present)
        if "active" in article and not article["active"]:
            return {"success": False, "error": "Article is not active"}

        # Check feed exists
        feed_id = article.get("feed_id")
        feed = self.feeds.get(feed_id)
        if not feed:
            return {"success": False, "error": "Article's feed does not exist"}

        # Check feed is active
        if "active" in feed and not feed["active"]:
            return {"success": False, "error": "Article's feed is not active"}

        # Mark as read in article_user_states
        self._normalize_article_user_state_keys()
        key = self._find_article_user_state_key(user_id, article_id)
        current_state = self.article_user_states.get(key) if key is not None else None

        if current_state:
            # Update read_status to 'read' (keep bookmarked state)
            current_state["read_status"] = "read"
        else:
            # Create a new record (default bookmarked = False)
            self.article_user_states[(user_id, article_id)] = {
                "_id": user_id,
                "user_id": user_id,
                "article_id": article_id,
                "read_status": "read",
                "bookmarked": False
            }

        return {"success": True, "message": f"Article marked as read for user {user_id}"}

    def bookmark_article(self, user_id: str, article_id: str, bookmarked: bool) -> dict:
        """
        Mark or unmark an article as bookmarked by a user.

        Args:
            user_id (str): The _id of the user performing the operation.
            article_id (str): The article to modify the bookmark state for.
            bookmarked (bool): True to mark as bookmarked, False to unmark.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Bookmark state updated"
                }
            or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - User and Article must exist.
            - Operates only on active articles (if an 'active' attribute exists for articles and it's False, treat as not found/inactive).
            - ArticleUserState is created if not present.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check article exists
        article_info = self.articles.get(article_id)
        if not article_info:
            return {"success": False, "error": "Article does not exist"}

        # Check active status for article, if the attribute exists
        if "active" in article_info and not article_info["active"]:
            return {"success": False, "error": "Article is not active"}
    
        self._normalize_article_user_state_keys()
        key = self._find_article_user_state_key(user_id, article_id)
        if key is not None:
            # Update existing state
            self.article_user_states[key]["bookmarked"] = bookmarked
        else:
            # Create new state -- initialize read_status to "unread"
            self.article_user_states[(user_id, article_id)] = {
                "_id": user_id,
                "user_id": user_id,
                "article_id": article_id,
                "read_status": "unread",
                "bookmarked": bookmarked
            }
        return {"success": True, "message": "Bookmark state updated"}

    def update_feed_active_status(self, feed_id: str, active: bool) -> dict:
        """
        Change a feed's active status (activate, deactivate, or "delete" feed).

        Args:
            feed_id (str): The unique identifier of the feed to modify.
            active (bool): True to activate, False to deactivate/delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Feed <feed_id> set to active/inactive." }
                On failure: { "success": False, "error": "Feed not found" }

        Constraints:
            - Only existing feeds can have their status changed.
            - If 'active' field does not exist in FeedInfo, it will be created/added.
        """
        feed = self.feeds.get(feed_id)
        if feed is None:
            return { "success": False, "error": "Feed not found" }

        feed["active"] = active  # Add or update the 'active' flag

        status_text = "active" if active else "inactive"
        return {
            "success": True,
            "message": f"Feed {feed_id} set to {status_text}."
        }

    def update_article_active_status(self, article_id: str, active: bool) -> dict:
        """
        Change (set) an article's active status (activate or deactivate/delete).

        Args:
            article_id (str): The unique identifier of the article to update.
            active (bool): Desired active status (True = active/present, False = deactivated/deleted).

        Returns:
            dict: {
                "success": True,
                "message": "Article active status updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Article must exist.
            - Status change is idempotent (setting to current value is still a success).
        """
        article = self.articles.get(article_id)
        if not article:
            return { "success": False, "error": "Article does not exist." }

        # Handle legacy data: if 'active' is missing, default to True.
        current_active = article.get("active", True)
        if current_active == active:
            return { "success": True, "message": "Article active status is already set as requested." }

        article["active"] = active
        self.articles[article_id] = article

        return { "success": True, "message": f"Article active status updated to {active}." }

    def add_new_feed(
        self,
        feed_id: str,
        title: str,
        description: str,
        url: str,
        last_updated: str
    ) -> dict:
        """
        Add a newly discovered feed to the active feeds list.

        Args:
            feed_id (str): Unique identifier for the feed.
            title (str): Feed title.
            description (str): Feed description.
            url (str): Feed url.
            last_updated (str): ISO timestamp string representing last update time.

        Returns:
            dict: 
             - On success: { "success": True, "message": "Feed added." }
             - On failure: { "success": False, "error": <reason> }

        Constraints:
            - feed_id must be unique (no duplicate feeds).
            - All fields must be present (non-empty).
            - All feeds are considered active by being present in self.feeds.
        """
        if not all([feed_id, title, description, url, last_updated]):
            return { "success": False, "error": "All required fields must be provided and non-empty." }

        if feed_id in self.feeds:
            return { "success": False, "error": f"Feed with id '{feed_id}' already exists." }

        self.feeds[feed_id] = {
            "feed_id": feed_id,
            "title": title,
            "description": description,
            "url": url,
            "last_updated": last_updated
        }

        return { "success": True, "message": "Feed added." }

    def add_new_article(
        self,
        article_id: str,
        feed_id: str,
        title: str,
        content: str,
        publication_date: str,
        url: str,
        author: str
    ) -> dict:
        """
        Add a new article under an existing, active feed.

        Args:
            article_id (str): Unique article ID (must not already exist).
            feed_id (str): Existing feed ID (must exist and be active).
            title (str): Article title.
            content (str): Article content/body.
            publication_date (str): Publication timestamp, ISO format.
            url (str): Article URL.
            author (str): Article author.

        Returns:
            dict: On success:
                { "success": True, "message": "Article added under feed_id <feed_id>." }
            On failure (feed does not exist, inactive, or article_id already exists):
                { "success": False, "error": <reason> }

        Constraints:
            - Article must have unique article_id.
            - Article must be linked to an existing, active feed.
        """
        # Check unique article_id
        if article_id in self.articles:
            return { "success": False, "error": f"Article ID '{article_id}' already exists." }
    
        # Check feed exists
        feed_info = self.feeds.get(feed_id)
        if feed_info is None:
            return { "success": False, "error": f"Feed ID '{feed_id}' does not exist." }
    
        # Check if feed is active (if 'active' is present)
        if "active" in feed_info and not feed_info["active"]:
            return { "success": False, "error": f"Feed ID '{feed_id}' is not active." }

        # Create ArticleInfo TypedDict
        article_info = {
            "article_id": article_id,
            "feed_id": feed_id,
            "title": title,
            "content": content,
            "publication_date": publication_date,
            "url": url,
            "author": author
        }

        self.articles[article_id] = article_info

        return { "success": True, "message": f"Article added under feed_id {feed_id}." }

    def update_user_preferences(self, user_id: str, preferences: dict) -> dict:
        """
        Update the preference configuration for a given user.

        Args:
            user_id (str): ID of the user whose preferences to update
            preferences (dict): New preferences configuration to assign (replaces old preferences)

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User preferences updated" }
                On failure:
                    { "success": False, "error": str }
    
        Constraints:
            - User must exist
            - Preferences must be a dict
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not isinstance(preferences, dict):
            return { "success": False, "error": "Preferences must be a dictionary" }

        self.users[user_id]['preferences'] = preferences
        return { "success": True, "message": "User preferences updated" }

    def delete_article_user_state(self, user_id: str, article_id: str) -> dict:
        """
        Remove a user's ArticleUserState entry for a given article (removes read/bookmarked state).
    
        Args:
            user_id (str): The user identifier.
            article_id (str): The article identifier.
        
        Returns:
            dict:
                - On success: { "success": True, "message": "Article user state deleted." }
                - On failure:
                    - If user or article not found: { "success": False, "error": "User or article does not exist." }
                    - If no ArticleUserState entry for the (user, article) pair: 
                        { "success": False, "error": "No article user state found for the specified user and article." }
        Constraints:
            - ArticleUserState exists only if a user has interacted with an article.
            - No effect if trying to delete a nonexistent entry, except error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if article_id not in self.articles:
            return { "success": False, "error": "Article does not exist." }
        self._normalize_article_user_state_keys()
        key = self._find_article_user_state_key(user_id, article_id)
        if key is None:
            return { "success": False, "error": "No article user state found for the specified user and article." }
        del self.article_user_states[key]
        return { "success": True, "message": "Article user state deleted." }


class RSSFeedReaderSystem(BaseEnv):
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
        if hasattr(env, "_normalize_article_user_state_keys"):
            env._normalize_article_user_state_keys()

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

    def search_feeds_by_title_keyword(self, **kwargs):
        return self._call_inner_tool('search_feeds_by_title_keyword', kwargs)

    def get_feed_by_id(self, **kwargs):
        return self._call_inner_tool('get_feed_by_id', kwargs)

    def list_all_active_feeds(self, **kwargs):
        return self._call_inner_tool('list_all_active_feeds', kwargs)

    def list_articles_by_feed(self, **kwargs):
        return self._call_inner_tool('list_articles_by_feed', kwargs)

    def get_latest_articles_by_feed(self, **kwargs):
        return self._call_inner_tool('get_latest_articles_by_feed', kwargs)

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def get_feed_articles_count(self, **kwargs):
        return self._call_inner_tool('get_feed_articles_count', kwargs)

    def get_article_user_state(self, **kwargs):
        return self._call_inner_tool('get_article_user_state', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def mark_article_as_read(self, **kwargs):
        return self._call_inner_tool('mark_article_as_read', kwargs)

    def bookmark_article(self, **kwargs):
        return self._call_inner_tool('bookmark_article', kwargs)

    def update_feed_active_status(self, **kwargs):
        return self._call_inner_tool('update_feed_active_status', kwargs)

    def update_article_active_status(self, **kwargs):
        return self._call_inner_tool('update_article_active_status', kwargs)

    def add_new_feed(self, **kwargs):
        return self._call_inner_tool('add_new_feed', kwargs)

    def add_new_article(self, **kwargs):
        return self._call_inner_tool('add_new_article', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def delete_article_user_state(self, **kwargs):
        return self._call_inner_tool('delete_article_user_state', kwargs)
