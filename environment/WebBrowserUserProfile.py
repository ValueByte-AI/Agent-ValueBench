# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional, List, Dict
import uuid
from typing import Dict, Any



class UserProfileInfo(TypedDict):
    profile_id: str
    user_id: str
    active_session: bool

class BrowsingHistoryEntry(TypedDict):
    entry_id: str
    profile_id: str
    url: str
    visit_time: str  # ISO timestamp as string
    visit_count: int
    title: str

class CacheEntry(TypedDict):
    cache_id: str
    profile_id: str
    resource_url: str
    resource_type: str
    cached_data: bytes  # Assuming binary data for cached resources
    expiration_time: str  # ISO timestamp as string

class CookieInfo(TypedDict):
    cookie_id: str
    profile_id: str
    domain: str
    value: str
    expiration_time: str  # ISO timestamp as string
    scope: str

class SavedPasswordInfo(TypedDict):
    password_id: str
    profile_id: str
    site: str
    username: str
    encrypted_password: str

class SiteSettingInfo(TypedDict):
    setting_id: str
    profile_id: str
    site: str
    setting_key: str
    setting_value: str

class _GeneratedEnvImpl:
    def __init__(self):
        # User Profiles: {profile_id: UserProfileInfo}
        self.user_profiles: Dict[str, UserProfileInfo] = {}

        # Browsing History: {entry_id: BrowsingHistoryEntry}
        self.browsing_history: Dict[str, BrowsingHistoryEntry] = {}

        # Cache: {cache_id: CacheEntry}
        self.cache: Dict[str, CacheEntry] = {}

        # Cookies: {cookie_id: CookieInfo}
        self.cookies: Dict[str, CookieInfo] = {}

        # Saved Passwords: {password_id: SavedPasswordInfo}
        self.saved_passwords: Dict[str, SavedPasswordInfo] = {}

        # Site Settings: {setting_id: SiteSettingInfo}
        self.site_settings: Dict[str, SiteSettingInfo] = {}

        # Constraints:
        # - Browsing data (history, cache, cookies, etc.) must be scoped and isolated per user profile.
        # - Clearing history or cache must only affect the selected user profile.
        # - Some data types may have optional retention periods or user-configurable deletion policies.
        # - Secure handling is required for sensitive data (e.g., passwords).
        # - Operations like querying, modifying, exporting must comply with user privacy preferences.

    def _resolve_profile(self, profile_id: str):
        if profile_id in self.user_profiles:
            profile = self.user_profiles[profile_id]
            return profile_id, profile.get("profile_id", profile_id)

        for key, profile in self.user_profiles.items():
            if profile.get("profile_id") == profile_id:
                return key, profile_id

        return None, None

    def get_active_user_profile(self) -> dict:
        """
        Retrieve the currently active user profile(s).

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[UserProfileInfo]  # All active profiles (usually one, but may be multiple)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "No active user profile."
                    }

        Notes:
            - Returns all profiles with 'active_session' == True.
            - If no active user profile in the environment, returns failure.
        """
        active_profiles = [
            profile
            for profile in self.user_profiles.values()
            if profile.get("active_session", False)
        ]

        if not active_profiles:
            return {"success": False, "error": "No active user profile."}

        return {"success": True, "data": active_profiles}

    def list_user_profiles(self) -> dict:
        """
        List all user profiles available in the browser.

        Returns:
            dict: {
                "success": True,
                "data": List[UserProfileInfo]  # List of all user profiles (could be empty)
            }
        """
        profiles = list(self.user_profiles.values())
        return { "success": True, "data": profiles }

    def get_browsing_history(
        self, 
        profile_id: str, 
        url_substring: str = None, 
        title_substring: str = None, 
        start_time: str = None, 
        end_time: str = None,
    ) -> dict:
        """
        Retrieve browsing history entries for a given user profile, optionally filtered by URL substring,
        title substring, and/or time range.

        Args:
            profile_id (str): The user profile whose browsing history to retrieve.
            url_substring (str, optional): If provided, only include entries whose URL contains this substring.
            title_substring (str, optional): If provided, only include entries whose title contains this substring.
            start_time (str, optional): ISO timestamp; only include entries visited at or after this time.
            end_time (str, optional): ISO timestamp; only include entries visited at or before this time.

        Returns:
            dict: 
                On success: {"success": True, "data": [BrowsingHistoryEntry, ...]}
                On failure: {"success": False, "error": str}
        Constraints:
            - Only entries belonging to the specified user profile may be returned.
            - If the profile does not exist, return an error.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return {"success": False, "error": "Profile not found."}

        result = []
        for entry in self.browsing_history.values():
            if entry["profile_id"] != canonical_profile_id:
                continue
            if url_substring and url_substring not in entry["url"]:
                continue
            if title_substring and title_substring not in entry.get("title", ""):
                continue
            # ISO time filtering
            if start_time and entry["visit_time"] < start_time:
                continue
            if end_time and entry["visit_time"] > end_time:
                continue
            result.append(entry)

        return {"success": True, "data": result}

    def get_cache_entries(self, profile_id: str) -> dict:
        """
        Retrieve all cache entries associated with a specified user profile.

        Args:
            profile_id (str): The user profile ID for which cache entries are to be retrieved.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[CacheEntry],  # may be empty
                  }
                - On failure: {
                      "success": False,
                      "error": str  # explanation, e.g., profile does not exist
                  }

        Constraints:
            - Browsing data is isolated per user profile; only entries for the given profile are returned.
            - The specified profile must exist.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        entries = [
            cache_entry for cache_entry in self.cache.values()
            if cache_entry["profile_id"] == canonical_profile_id
        ]
        return { "success": True, "data": entries }

    def get_cookies(self, profile_id: str) -> dict:
        """
        Retrieve all browser cookies for the specified user profile.

        Args:
            profile_id (str): The ID of the user profile.

        Returns:
            dict: {
                "success": True,
                "data": List[CookieInfo],  # List of cookies belonging to that profile (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Profile does not exist"
            }

        Constraints:
            - Only return cookies associated with the given profile_id.
            - The profile_id must exist in user_profiles.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        cookies = [
            cookie for cookie in self.cookies.values()
            if cookie["profile_id"] == canonical_profile_id
        ]

        return { "success": True, "data": cookies }

    def get_saved_passwords(self, profile_id: str) -> dict:
        """
        Retrieve all saved password entries (encrypted) belonging to the specified user profile.

        Args:
            profile_id (str): The identifier of the user profile.

        Returns:
            dict:
                - { "success": True, "data": List[SavedPasswordInfo] }
                    (possibly empty list if no passwords)
                - { "success": False, "error": "Profile does not exist" }

        Constraints:
            - profile_id must exist in self.user_profiles.
            - Only passwords belonging to that profile_id are returned.
            - Passwords remain encrypted; secure handling is expected externally.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        result = [
            pwd for pwd in self.saved_passwords.values()
            if pwd['profile_id'] == canonical_profile_id
        ]
        return { "success": True, "data": result }

    def get_site_settings(self, profile_id: str) -> dict:
        """
        Retrieve site-specific settings (SiteSettingInfo) for a user profile.

        Args:
            profile_id (str): The ID of the user profile whose site settings are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[SiteSettingInfo],  # List may be empty if none.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., unknown profile_id)
            }

        Constraints:
            - Site settings must be isolated per user profile.
            - The provided profile_id must exist.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return {"success": False, "error": "Profile not found"}
        result = [
            setting for setting in self.site_settings.values()
            if setting["profile_id"] == canonical_profile_id
        ]
        return {"success": True, "data": result}

    def preview_clearable_data(self, profile_id: str) -> dict:
        """
        Preview the browsing history, cache, and cookie entries that would be removed for the specified user profile.

        Args:
            profile_id (str): The user profile ID for which to preview clearable data.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "history": List[BrowsingHistoryEntry],
                    "cache": List[CacheEntry],
                    "cookies": List[CookieInfo]
                }
            }
            OR
            {
                "success": False,
                "error": str  # e.g., "Profile not found"
            }

        Constraints:
            - Only entries scoped to the given profile_id will be included.
            - No data is actually deleted or modified.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile not found" }

        history = [
            entry for entry in self.browsing_history.values()
            if entry["profile_id"] == canonical_profile_id
        ]
        cache = [
            entry for entry in self.cache.values()
            if entry["profile_id"] == canonical_profile_id
        ]
        cookies = [
            entry for entry in self.cookies.values()
            if entry["profile_id"] == canonical_profile_id
        ]

        return {
            "success": True,
            "data": {
                "history": history,
                "cache": cache,
                "cookies": cookies
            }
        }

    def clear_browsing_history(self, profile_id: str, entry_ids: list = None) -> dict:
        """
        Remove all or selected browsing history entries for a given user profile.

        Args:
            profile_id (str): The target user profile whose browsing history is to be cleared.
            entry_ids (list, optional): List of specific entry IDs to remove. If None, all entries for the profile will be cleared.

        Returns:
            dict: 
                On success: { "success": True, "message": "<N> entries deleted for profile <profile_id>" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Only history entries belonging to the specified profile will be affected.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "User profile does not exist." }
    
        entries_to_delete = []

        if entry_ids is not None:
            # Only delete entries that (a) exist and (b) belong to this profile
            for eid in entry_ids:
                entry = self.browsing_history.get(eid)
                if entry and entry['profile_id'] == canonical_profile_id:
                    entries_to_delete.append(eid)
            for eid in entries_to_delete:
                del self.browsing_history[eid]
            count = len(entries_to_delete)
            return { "success": True, "message": f"{count} selected browsing history entries deleted for profile {canonical_profile_id}." }
        else:
            # Delete all entries belonging to this profile
            entry_ids_all = [eid for eid, entry in self.browsing_history.items() if entry["profile_id"] == canonical_profile_id]
            for eid in entry_ids_all:
                del self.browsing_history[eid]
            count = len(entry_ids_all)
            return { "success": True, "message": f"{count} browsing history entries deleted for profile {canonical_profile_id}." }


    def clear_cache(self, profile_id: str, cache_ids: Optional[List[str]] = None) -> dict:
        """
        Remove all or selected cache entries for a user profile.

        Args:
            profile_id (str): The profile whose cache entries should be cleared.
            cache_ids (Optional[List[str]]): If provided, only these cache entries will be removed
                                             (must also belong to the profile). If omitted or None,
                                             all cache entries for the profile will be removed.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Cleared N cache entries for profile <profile_id>."
                }
                On failure (e.g. profile not found): {
                    "success": False,
                    "error": "Profile does not exist."
                }

        Constraints:
            - Cache entries are isolated per user profile.
            - If cache_ids are given, only entries belonging to the profile are removed.
            - If no matching entries, still return success with 0 entries cleared.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return {"success": False, "error": "Profile does not exist."}

        cleared_count = 0
        # Build a set for quick lookup if filtering by cache_ids
        cache_ids_set = set(cache_ids) if cache_ids else None

        # Collect cache_ids to delete (prevent changing dict size during iteration)
        to_delete = []
        for cache_id, cache_entry in self.cache.items():
            if cache_entry["profile_id"] == canonical_profile_id:
                if cache_ids_set is None or cache_id in cache_ids_set:
                    to_delete.append(cache_id)

        for cache_id in to_delete:
            del self.cache[cache_id]
            cleared_count += 1

        return {
            "success": True,
            "message": f"Cleared {cleared_count} cache entr{'y' if cleared_count == 1 else 'ies'} for profile {canonical_profile_id}."
        }

    def clear_cookies(self, profile_id: str) -> dict:
        """
        Remove all cookies for the specified user profile.

        Args:
            profile_id (str): The user profile ID whose cookies should be cleared.

        Returns:
            dict: {
                "success": True,
                "message": "All cookies for profile <profile_id> cleared."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., profile does not exist.
            }
        Constraints:
            - Only affects cookies belonging to the given user profile.
            - Fails if the profile does not exist.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return {"success": False, "error": "User profile does not exist."}
    
        # Get cookie_ids to delete to avoid modifying dict during iteration
        cookie_ids_to_delete = [
            cookie_id for cookie_id, cookie in self.cookies.items()
            if cookie["profile_id"] == canonical_profile_id
        ]
        for cookie_id in cookie_ids_to_delete:
            del self.cookies[cookie_id]

        return {
            "success": True,
            "message": f"All cookies for profile {canonical_profile_id} cleared."
        }

    def clear_saved_passwords(self, profile_id: str) -> dict:
        """
        Remove all saved passwords for the given user profile, securely.

        Args:
            profile_id (str): The profile ID from which all saved passwords will be cleared.

        Returns:
            dict: {
                "success": True,
                "message": "All saved passwords cleared for profile <profile_id>."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only affects the specified user profile.
            - Secure deletion (removal from memory).
            - Fails if profile does not exist.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        # Collect password IDs to delete
        to_delete = [pw_id for pw_id, pw in self.saved_passwords.items() if pw["profile_id"] == canonical_profile_id]

        for pw_id in to_delete:
            # For secure deletion, actually remove from self.saved_passwords
            del self.saved_passwords[pw_id]
    
        return {
            "success": True,
            "message": f"All saved passwords cleared for profile {canonical_profile_id}."
        }

    def clear_site_settings(self, profile_id: str) -> dict:
        """
        Remove all site-specific settings for a given user profile.

        Args:
            profile_id (str): The identifier of the user profile whose site settings will be removed.

        Returns:
            dict: 
                {"success": True, "message": "Cleared all site settings for profile <profile_id>."}
                or
                {"success": False, "error": "<error message>"}

        Constraints:
            - Only site settings belonging to the specified profile are removed.
            - The profile must exist.
            - It is a no-op (but still success) if there are no site settings for the profile.
        """
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return {"success": False, "error": "Profile does not exist"}

        # Collect setting_ids belonging to the profile
        to_remove = [setting_id for setting_id, setting_info in self.site_settings.items()
                     if setting_info["profile_id"] == canonical_profile_id]

        for setting_id in to_remove:
            del self.site_settings[setting_id]

        return {
            "success": True,
            "message": f"Cleared all site settings for profile {canonical_profile_id}."
        }

    def export_browsing_data(self, profile_id: str, categories: list[str]) -> dict:
        """
        Export selected categories (history, cache, cookies, saved passwords, site settings) 
        for a given user profile for portability or backup.

        Args:
            profile_id (str): The user profile identifier whose data is to be exported.
            categories (list of str): Data categories to export. Valid: "history", "cache",
                                      "cookies", "saved_passwords", "site_settings".

        Returns:
            dict: 
              "success": True and "data": {category: [entries]} if successful.
              "success": False and "error": str if not.

        Constraints:
            - Only export data belonging to the given profile_id.
            - Categories must be from the allowed list.
            - Browsing data must remain isolated per profile.
            - Sensitive data ("saved_passwords") is included as-is for export.
        """

        allowed_categories = {
            "history": self.browsing_history,
            "cache": self.cache,
            "cookies": self.cookies,
            "saved_passwords": self.saved_passwords,
            "site_settings": self.site_settings,
        }

        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        # Validate categories
        invalid = [cat for cat in categories if cat not in allowed_categories]
        if invalid:
            return {
                "success": False,
                "error": f"Invalid categories requested: {', '.join(invalid)}"
            }

        # Gather data
        export_data = {}

        for cat in categories:
            store = allowed_categories[cat]
            # Filter entries by profile_id
            filtered = [
                entry for entry in store.values()
                if entry.get("profile_id") == canonical_profile_id
            ]
            export_data[cat] = filtered

        return { "success": True, "data": export_data }


    def import_browsing_data(self, profile_id: str, browsing_data: Dict[str, Any]) -> dict:
        """
        Import browsing data into a specified user profile.

        Args:
            profile_id (str): The ID of the user profile to import data into. Must exist.
            browsing_data (dict): A dictionary which may contain any combination of these keys:
                - 'browsing_history': list of dicts to be deserialized to BrowsingHistoryEntry
                - 'cache': list of dicts to be deserialized to CacheEntry
                - 'cookies': list of dicts to be deserialized to CookieInfo
                - 'saved_passwords': list of dicts to be deserialized to SavedPasswordInfo
                - 'site_settings': list of dicts to be deserialized to SiteSettingInfo

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - Data must be assigned to the target profile regardless of imported profile_id values.
            - Entry IDs (entry_id, cache_id, etc.) must not conflict with existing IDs; on conflict, new unique IDs must be assigned.
            - Data must not overwrite existing entities.
            - Secure handling of sensitive data is maintained (no transformations).
            - If input browsing_data is empty or contains only unknown keys, operation is still considered successful.
        """
        # Check if profile exists
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist." }

        added_counts = {
            "browsing_history": 0,
            "cache": 0,
            "cookies": 0,
            "saved_passwords": 0,
            "site_settings": 0
        }

        # Helper: For each entity type, process import
        entity_specs = [
            ("browsing_history", self.browsing_history, "entry_id"),
            ("cache", self.cache, "cache_id"),
            ("cookies", self.cookies, "cookie_id"),
            ("saved_passwords", self.saved_passwords, "password_id"),
            ("site_settings", self.site_settings, "setting_id"),
        ]

        for key, storage, id_field in entity_specs:
            entries = browsing_data.get(key, [])
            for raw_entry in entries:
                if not isinstance(raw_entry, dict):
                    continue  # Skip malformed

                # Overwrite/insert required fields
                entry = raw_entry.copy()
                # Ensure correct profile
                entry["profile_id"] = canonical_profile_id
                # Ensure unique ID
                current_id = entry.get(id_field)
                needs_new_id = current_id is None or current_id in storage
                if needs_new_id:
                    # Generate new unique ID
                    while True:
                        new_id = str(uuid.uuid4())
                        if new_id not in storage:
                            entry[id_field] = new_id
                            break
                else:
                    entry[id_field] = current_id

                # Final sanity checks for basic required fields
                if entry.get(id_field) in storage:
                    # Rare race (shouldn't occur), generate unique
                    while True:
                        new_id = str(uuid.uuid4())
                        if new_id not in storage:
                            entry[id_field] = new_id
                            break

                # Insert into environment
                storage[entry[id_field]] = entry
                added_counts[key] += 1

        message = f"Browsing data imported successfully into profile '{canonical_profile_id}'. Counts: {added_counts}"
        return { "success": True, "message": message }

    def set_data_retention_policy(self, profile_id: str, policies: dict) -> dict:
        """
        Configure automatic deletion/retention policies for browsing data per user profile.

        Args:
            profile_id (str): The profile ID to set policies for.
            policies (dict): Dictionary mapping data type to retention policy,
                e.g., {
                        "history": {"retention_days": 30},
                        "cache": {"retention_days": 7},
                        "cookies": {"retention_days": 10}
                      }
                Supported types: "history", "cache", "cookies", "passwords", "site_settings"
                Value must be a dict (e.g., contain "retention_days": int)

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Retention policy set for profile <profile_id>"}
                On failure:
                    {"success": False, "error": "Reason for failure"}

        Constraints:
            - Profile must exist.
            - Policy types must be valid.
            - Policy values must be dict with at least "retention_days" (int >= 0).
            - Retention policies are stored per profile.
        """
        # Supported data types
        allowed_types = {"history", "cache", "cookies", "passwords", "site_settings"}

        # Check profile exists
        _, canonical_profile_id = self._resolve_profile(profile_id)
        if canonical_profile_id is None:
            return { "success": False, "error": "Profile does not exist" }

        # Validate and normalize policies dict
        for key, value in policies.items():
            if key not in allowed_types:
                return { "success": False, "error": f"Invalid data category '{key}' in policies" }
            if not isinstance(value, dict):
                return { "success": False, "error": f"Policy for '{key}' must be a dictionary" }
            # Allow 0-day retention to represent immediate/continuous purging.
            if "retention_days" not in value or not isinstance(value["retention_days"], int) or value["retention_days"] < 0:
                return { "success": False, "error": f"Policy for '{key}' must include non-negative integer 'retention_days'" }

        # Create structure if it doesn't exist yet
        if not hasattr(self, "data_retention_policies") or not isinstance(self.data_retention_policies, dict):
            self.data_retention_policies = {}

        # Store/overwrite the policy
        self.data_retention_policies[canonical_profile_id] = policies.copy()

        return {
            "success": True,
            "message": f"Retention policy set for profile {canonical_profile_id}"
        }


class WebBrowserUserProfile(BaseEnv):
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
            if key == "data_retention_policies":
                normalized = value
                if isinstance(normalized, str):
                    try:
                        normalized = json.loads(normalized)
                    except Exception:
                        normalized = {}
                if not isinstance(normalized, dict):
                    normalized = {}
                setattr(env, key, copy.deepcopy(normalized))
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

    def get_active_user_profile(self, **kwargs):
        return self._call_inner_tool('get_active_user_profile', kwargs)

    def list_user_profiles(self, **kwargs):
        return self._call_inner_tool('list_user_profiles', kwargs)

    def get_browsing_history(self, **kwargs):
        return self._call_inner_tool('get_browsing_history', kwargs)

    def get_cache_entries(self, **kwargs):
        return self._call_inner_tool('get_cache_entries', kwargs)

    def get_cookies(self, **kwargs):
        return self._call_inner_tool('get_cookies', kwargs)

    def get_saved_passwords(self, **kwargs):
        return self._call_inner_tool('get_saved_passwords', kwargs)

    def get_site_settings(self, **kwargs):
        return self._call_inner_tool('get_site_settings', kwargs)

    def preview_clearable_data(self, **kwargs):
        return self._call_inner_tool('preview_clearable_data', kwargs)

    def clear_browsing_history(self, **kwargs):
        return self._call_inner_tool('clear_browsing_history', kwargs)

    def clear_cache(self, **kwargs):
        return self._call_inner_tool('clear_cache', kwargs)

    def clear_cookies(self, **kwargs):
        return self._call_inner_tool('clear_cookies', kwargs)

    def clear_saved_passwords(self, **kwargs):
        return self._call_inner_tool('clear_saved_passwords', kwargs)

    def clear_site_settings(self, **kwargs):
        return self._call_inner_tool('clear_site_settings', kwargs)

    def export_browsing_data(self, **kwargs):
        return self._call_inner_tool('export_browsing_data', kwargs)

    def import_browsing_data(self, **kwargs):
        return self._call_inner_tool('import_browsing_data', kwargs)

    def set_data_retention_policy(self, **kwargs):
        return self._call_inner_tool('set_data_retention_policy', kwargs)
