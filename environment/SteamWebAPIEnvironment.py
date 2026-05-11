# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any
import time



class AppInfo(TypedDict):
    app_id: str
    name: str
    developer: str
    publisher: str
    release_date: str
    genre: str
    description: str
    additional_metadata: Dict[str, Any]

class AchievementInfo(TypedDict):
    achievement_id: str
    app_id: str
    name: str
    description: str
    icon: str
    global_percentage: float

class NewsArticleInfo(TypedDict):
    article_id: str
    app_id: str
    title: str
    content: str
    url: str
    date_published: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Steam Web API data retrieval and management.
        """

        # Apps: {app_id: AppInfo}
        # State space: App (app_id, name, developer, publisher, release_date, genre, description, additional_metadata)
        self.apps: Dict[str, AppInfo] = {}

        # Achievements: {achievement_id: AchievementInfo}
        # State space: Achievement (achievement_id, app_id, name, description, icon, global_percentage)
        self.achievements: Dict[str, AchievementInfo] = {}

        # NewsArticles: {article_id: NewsArticleInfo}
        # State space: NewsArticle (article_id, app_id, title, content, url, date_published)
        self.news_articles: Dict[str, NewsArticleInfo] = {}

        # Constraints:
        # - Each Achievement and NewsArticle must reference a valid app_id present in self.apps.
        # - The global_percentage for Achievements must be between 0 and 100.
        # - Only the most recent news(s) should be returned for a "latest news" query.
        # - App metadata should be kept up-to-date with Steam.

    def get_app_by_id(self, app_id: str) -> dict:
        """
        Retrieve complete metadata for a game/application using its app_id.

        Args:
            app_id (str): The unique identifier of the game or application.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": AppInfo  # All available metadata for the app
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., app_id not found
                    }

        Constraints:
            - The app_id must exist in the environment.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App with the specified app_id does not exist."}
        return {"success": True, "data": self.apps[app_id]}

    def list_achievements_by_app(self, app_id: str) -> dict:
        """
        Retrieve all achievements (including global percentages and metadata) for a specific app_id.

        Args:
            app_id (str): The unique identifier of the app whose achievements to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[AchievementInfo],  # All achievements for the app (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # E.g., "App ID does not exist"
            }

        Constraints:
            - Only achievements linked to valid app_id are stored, but existence will be checked.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App ID does not exist"}

        achievements = [
            achievement for achievement in self.achievements.values()
            if achievement["app_id"] == app_id
        ]
        return {"success": True, "data": achievements}

    def get_global_achievement_percentages(self, app_id: str) -> dict:
        """
        Retrieve a mapping of achievement_id to global_percentage for all achievements of a given app.

        Args:
            app_id (str): The App ID to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {achievement_id: global_percentage, ...}
                    }
                On failure:
                    {
                        "success": False,
                        "error": "App ID does not exist"
                    }

        Constraints:
            - The given app_id must exist in the apps database.
            - Only achievements where achievement.app_id == app_id are considered.
            - The result may be an empty dictionary if no achievements for this app.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App ID does not exist" }

        result = {
            achievement["achievement_id"]: achievement["global_percentage"]
            for achievement in self.achievements.values()
            if achievement["app_id"] == app_id
        }

        return { "success": True, "data": result }

    def get_latest_news_by_app(self, app_id: str) -> dict:
        """
        Retrieve the most recent news article(s) for a specific app_id, sorted by date_published.

        Args:
            app_id (str): The Steam App ID for which to fetch the latest news.

        Returns:
            dict: {
                "success": True,
                "data": List[NewsArticleInfo]  # Most recent news article(s), latest first
            }
            or
            {
                "success": False,
                "error": str  # If the app_id does not exist
            }

        Constraints:
            - app_id must exist in self.apps.
            - Only news articles whose app_id matches are considered.
            - If multiple articles have the same latest date (date_published), return all of them.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App ID does not exist"}

        # Gather all news articles for this app
        candidates = [
            article for article in self.news_articles.values()
            if article["app_id"] == app_id
        ]

        if not candidates:
            return {"success": True, "data": []}

        # Find the maximum date_published string (assume ISO format for lexical comparison)
        latest_date = max(article["date_published"] for article in candidates)
        latest_articles = [
            article for article in candidates
            if article["date_published"] == latest_date
        ]

        # Sort (though they should have the same date, maintain a consistent order by article_id)
        latest_articles.sort(key=lambda x: x.get("article_id", ""))

        return {"success": True, "data": latest_articles}

    def get_news_by_app(self, app_id: str) -> dict:
        """
        Retrieve all news articles (not just the latest) for a given app_id.

        Args:
            app_id (str): The unique identifier of the app/game for which news is retrieved.
    
        Returns:
            dict: {
                "success": True,
                "data": List[NewsArticleInfo],  # List of news article dicts or empty if none
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., app_id does not exist
            }
    
        Constraints:
            - The app_id must exist in self.apps.
            - All news articles returned must have NewsArticleInfo["app_id"] == app_id.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App ID does not exist"}

        articles = [
            article for article in self.news_articles.values()
            if article["app_id"] == app_id
        ]
        return {"success": True, "data": articles}

    def verify_app_exists(self, app_id: str) -> dict:
        """
        Check if an app with the specified app_id exists in the Steam database.

        Args:
            app_id (str): The unique application ID to check.

        Returns:
            dict: {
                "success": True,
                "exists": bool   # True if app_id exists, False otherwise
            }

        Notes:
            - If app_id is not present or is invalid, returns exists=False.
            - This operation does not raise errors; always returns a success result.
        """
        exists = bool(app_id) and app_id in self.apps
        return {
            "success": True,
            "exists": exists
        }

    def list_all_apps(self) -> dict:
        """
        List all apps currently tracked by the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AppInfo],  # List of all AppInfo dictionaries (may be empty if no apps tracked)
            }
        """
        all_apps = list(self.apps.values())
        return { "success": True, "data": all_apps }

    def validate_achievement_links(self) -> dict:
        """
        Ensure all Achievement objects reference valid (existing) app_ids.

        Returns:
            dict: {
                "success": True,
                "data": List[AchievementInfo],  # List of AchievementInfo with invalid app_ids (may be empty)
            }
        """
        invalid_achievements = [
            achievement for achievement in self.achievements.values()
            if achievement["app_id"] not in self.apps
        ]
        return {"success": True, "data": invalid_achievements}

    def validate_news_links(self) -> dict:
        """
        Checks all NewsArticles to ensure their app_id references a valid App in the environment.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]
                    # Each dict: {"article_id": str, "invalid_app_id": str}
                    # If all are valid, list is empty.
            }

        Constraints:
            - Each NewsArticle must reference an app_id that exists in self.apps.
            - Handles NewsArticles with missing or empty app_id as invalid.
        """
        invalid_articles = []
        for article in self.news_articles.values():
            app_id = article.get("app_id")
            if (not app_id) or (app_id not in self.apps):
                invalid_articles.append({
                    "article_id": article.get("article_id", "UNKNOWN"),
                    "invalid_app_id": app_id if app_id else "MISSING"
                })
        return { "success": True, "data": invalid_articles }

    def update_app_metadata(self, app_id: str, new_metadata: dict) -> dict:
        """
        Update the stored metadata of a given app (by app_id) to keep it up-to-date with Steam.

        Args:
            app_id (str): The unique identifier of the app to update.
            new_metadata (dict): Dictionary of fields and values to update within the app's metadata.
                Only the fields recognized in AppInfo will be updated. 'app_id' itself cannot be changed.

        Returns:
            dict: {
                "success": True,
                "message": "App metadata updated successfully."
            }
            or
            {
                "success": False,
                "error": "App with the given app_id does not exist." or "Invalid metadata fields provided."
            }

        Constraints:
            - app_id must exist in self.apps.
            - Only updatable fields present in AppInfo schema will be overwritten (except app_id).
            - Fields with invalid types will be ignored, and if no valid fields provided, will return an error.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App with the given app_id does not exist."}

        valid_fields = set(AppInfo.__annotations__.keys()) - {"app_id"}
        updated = False

        for key, value in new_metadata.items():
            if key in valid_fields:
                # Optionally: If type checking desired, ensure value type matches schema
                self.apps[app_id][key] = value
                updated = True

        if not updated:
            return {"success": False, "error": "Invalid metadata fields provided."}

        return {"success": True, "message": "App metadata updated successfully."}

    def add_or_update_achievement(
        self,
        achievement_id: str,
        app_id: str,
        name: str,
        description: str,
        icon: str,
        global_percentage: float
    ) -> dict:
        """
        Add a new achievement or update an existing achievement. Ensures:
        - The provided app_id exists in the App registry.
        - 'global_percentage' is between 0 and 100 (inclusive).
        - If 'achievement_id' exists, updates all fields.
        - If it does not exist, creates a new Achievement entry.

        Args:
            achievement_id (str): The achievement's unique ID.
            app_id (str): The Steam app this achievement is associated with; must exist.
            name (str): Name of the achievement.
            description (str): Description of the achievement.
            icon (str): Icon URL or identifier.
            global_percentage (float): Global unlock percentage (0 <= x <= 100).

        Returns:
            dict: 
                { "success": True, "message": "Achievement added." } or
                { "success": True, "message": "Achievement updated." }
                or
                { "success": False, "error": "reason" }
        """
        # Check that app_id exists
        if app_id not in self.apps:
            return {"success": False, "error": "app_id does not exist"}

        # Check global_percentage validity
        if not (0.0 <= global_percentage <= 100.0):
            return {"success": False, "error": "global_percentage must be between 0 and 100"}

        # Prepare achievement dict
        achievement_data = {
            "achievement_id": achievement_id,
            "app_id": app_id,
            "name": name,
            "description": description,
            "icon": icon,
            "global_percentage": float(global_percentage)
        }

        if achievement_id in self.achievements:
            # Update existing
            self.achievements[achievement_id].update(achievement_data)
            return {"success": True, "message": "Achievement updated."}
        else:
            # Add new
            self.achievements[achievement_id] = achievement_data
            return {"success": True, "message": "Achievement added."}

    def add_or_update_news_article(self, article_id: str, app_id: str, title: str, content: str, url: str, date_published: str) -> dict:
        """
        Add a new news article or update an existing one for a given app.
    
        Args:
            article_id (str): Unique identifier for the news article.
            app_id (str): The app_id the article is related to (must exist).
            title (str): The news article title.
            content (str): The main body/content of the news article.
            url (str): The URL to the news article.
            date_published (str): Publication date of the article.
    
        Returns:
            dict: 
                If success:
                    {
                        "success": True,
                        "message": "Added (or updated) news article for app <app_id>."
                    }
                If error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - Provided app_id must exist in self.apps.
            - article_id uniquely identifies a news article and may be updated.
        """
        # Check that app_id exists
        if app_id not in self.apps:
            return {"success": False, "error": f"app_id '{app_id}' does not exist"}

        news_data: NewsArticleInfo = {
            "article_id": article_id,
            "app_id": app_id,
            "title": title,
            "content": content,
            "url": url,
            "date_published": date_published
        }
        updated = False
        if article_id in self.news_articles:
            # Update existing article
            self.news_articles[article_id].update(news_data)
            updated = True
        else:
            # Add new article
            self.news_articles[article_id] = news_data

        action = "Updated" if updated else "Added"
        return {"success": True, "message": f"{action} news article '{article_id}' for app '{app_id}'."}

    def remove_achievement(self, achievement_id: str) -> dict:
        """
        Remove an achievement from the system for a given achievement_id.

        Args:
            achievement_id (str): The unique identifier of the achievement to remove.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Achievement <achievement_id> removed successfully."}
                On failure:
                    {"success": False, "error": "Achievement not found"}

        Constraints:
            - The achievement_id must exist in the system.
            - Only the achievement is removed; related App/News are unaffected.
        """
        if achievement_id not in self.achievements:
            return { "success": False, "error": "Achievement not found" }

        del self.achievements[achievement_id]
        return { "success": True, "message": f"Achievement {achievement_id} removed successfully." }

    def remove_news_article(self, article_id: str) -> dict:
        """
        Remove a news article from the system by its unique article_id.

        Args:
            article_id (str): The unique identifier for the news article to remove.

        Returns:
            dict: {
                "success": True,
                "message": "News article <article_id> removed successfully."
            }
            OR
            {
                "success": False,
                "error": "News article not found."
            }

        Constraints:
            - The specified article_id must exist within the news_articles collection.
            - This operation does not check app linkage or permissions.
        """
        if article_id not in self.news_articles:
            return {"success": False, "error": "News article not found."}

        del self.news_articles[article_id]
        return {"success": True, "message": f"News article {article_id} removed successfully."}

    def bulk_refresh_all_app_metadata(self) -> dict:
        """
        Refresh (simulate update of) metadata for all apps to ensure information remains current.
    
        This function simulates pulling the latest metadata from Steam for each app,
        and updates the 'additional_metadata' field, adding or updating a key 'last_refreshed'
        with the current timestamp. This helps indicate the refresh has taken place.
    
        Args:
            None

        Returns:
            dict: {
                "success": True,
                "message": "All app metadata refreshed successfully."
            }
            or
            {
                "success": False,
                "error": str
            }
        """

        for app_id, app_info in self.apps.items():
            # In a real scenario, here you would pull from Steam's API.
            # For simulation, we mark a timestamp of refresh.
            app_info["additional_metadata"]["last_refreshed"] = time.time()
            # Optionally, you could simulate more info updates here.

        return {
            "success": True,
            "message": "All app metadata refreshed successfully."
        }


class SteamWebAPIEnvironment(BaseEnv):
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

    def get_app_by_id(self, **kwargs):
        return self._call_inner_tool('get_app_by_id', kwargs)

    def list_achievements_by_app(self, **kwargs):
        return self._call_inner_tool('list_achievements_by_app', kwargs)

    def get_global_achievement_percentages(self, **kwargs):
        return self._call_inner_tool('get_global_achievement_percentages', kwargs)

    def get_latest_news_by_app(self, **kwargs):
        return self._call_inner_tool('get_latest_news_by_app', kwargs)

    def get_news_by_app(self, **kwargs):
        return self._call_inner_tool('get_news_by_app', kwargs)

    def verify_app_exists(self, **kwargs):
        return self._call_inner_tool('verify_app_exists', kwargs)

    def list_all_apps(self, **kwargs):
        return self._call_inner_tool('list_all_apps', kwargs)

    def validate_achievement_links(self, **kwargs):
        return self._call_inner_tool('validate_achievement_links', kwargs)

    def validate_news_links(self, **kwargs):
        return self._call_inner_tool('validate_news_links', kwargs)

    def update_app_metadata(self, **kwargs):
        return self._call_inner_tool('update_app_metadata', kwargs)

    def add_or_update_achievement(self, **kwargs):
        return self._call_inner_tool('add_or_update_achievement', kwargs)

    def add_or_update_news_article(self, **kwargs):
        return self._call_inner_tool('add_or_update_news_article', kwargs)

    def remove_achievement(self, **kwargs):
        return self._call_inner_tool('remove_achievement', kwargs)

    def remove_news_article(self, **kwargs):
        return self._call_inner_tool('remove_news_article', kwargs)

    def bulk_refresh_all_app_metadata(self, **kwargs):
        return self._call_inner_tool('bulk_refresh_all_app_metadata', kwargs)

