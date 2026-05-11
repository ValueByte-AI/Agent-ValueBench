# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class UserInfo(TypedDict):
    _id: str
    name: str
    subscription_type: str
    monthly_allowance: int
    usage_this_month: int
    account_sta: str

class SupportedLanguageInfo(TypedDict):
    language_code: str
    language_name: str
    is_active: bool

class TranslationRequestInfo(TypedDict, total=False):
    quest_id: str
    user_id: str
    source_language: str
    target_language: str
    word_count: int
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Online Translation Service Account Management System stateful environment.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # SupportedLanguages: {language_code: SupportedLanguageInfo}
        self.supported_languages: Dict[str, SupportedLanguageInfo] = {}
        # TranslationRequests: {quest_id: TranslationRequestInfo}
        self.translation_requests: Dict[str, TranslationRequestInfo] = {}

        # Constraints:
        # - A user's usage_this_month must not exceed monthly_allowance
        # - Only languages with is_active=True are available for translation
        # - Allowances and usage are reset at the beginning of each billing period (e.g., monthly)

    def list_active_languages(self) -> dict:
        """
        List all currently supported (active) languages, including their language codes and display names.

        Returns:
            dict: {
                "success": True,
                "data": List[SupportedLanguageInfo]  # All is_active==True languages
            }

        Constraints:
            - Only languages with is_active == True are included.
        """
        active_languages = [
            lang_info
            for lang_info in self.supported_languages.values()
            if lang_info.get("is_active", False) is True
        ]
        return {"success": True, "data": active_languages}

    def get_language_info(self, language_code: str) -> dict:
        """
        Retrieve the full information for a given language by its language code.

        Args:
            language_code (str): The unique code of the language to look up.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": SupportedLanguageInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Language not found"
                    }

        Constraints:
            - The language_code must exist in supported_languages.
        """
        lang_info = self.supported_languages.get(language_code)
        if not lang_info:
            return { "success": False, "error": "Language not found" }
        return { "success": True, "data": lang_info }

    def list_all_languages(self) -> dict:
        """
        Lists all supported languages (both active and inactive) registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SupportedLanguageInfo]  # List may be empty if no languages registered
            }
        """
        all_languages = list(self.supported_languages.values())
        return { "success": True, "data": all_languages }

    def get_user_info_by_name(self, name: str) -> dict:
        """
        Retrieve a user's profile details by their name (subscription type, allowance, usage, status, etc).

        Args:
            name (str): The name of the user to search for.
    
        Returns:
            dict: 
                - If found: {
                    "success": True,
                    "data": UserInfo
                  }
                - If not found: {
                    "success": False,
                    "error": "User not found"
                  }

        Constraints:
            - User names may not be unique. This returns the first match found, or an error if not found.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "User not found"}

        for user in self.users.values():
            if user["name"] == name:
                return {"success": True, "data": user}
    
        return {"success": False, "error": "User not found"}

    def get_user_info_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's profile (subscription type, monthly allowance, usage, status)
        by their unique _id.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,   # The complete UserInfo dictionary.
            }
            or
            {
                "success": False,
                "error": str        # Error message if user is not found.
            }

        Constraints:
            - Returns profile only if the user exists.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_monthly_left_allowance(self, user_id: str) -> dict:
        """
        Query the remaining translation allowance for a user in the current billing cycle.

        Args:
            user_id (str): The unique user identifier (_id).

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "monthly_left_allowance": int
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - User must exist.
            - Returns 'monthly_allowance - usage_this_month' (may be negative if data error elsewhere).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        left = user["monthly_allowance"] - user["usage_this_month"]
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "monthly_left_allowance": left
            }
        }

    def get_user_usage_this_month(self, user_id: str) -> dict:
        """
        Query the number of translation units (e.g., words) the user has used so far in the current month.

        Args:
            user_id (str): The unique identifier of the user whose usage is to be queried.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "usage_this_month": int
                        }
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - User must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "usage_this_month": user["usage_this_month"]
            }
        }

    def get_user_subscription_type(self, user_id: str) -> dict:
        """
        Return the subscription type (e.g., free, premium) for the user specified by user_id.

        Args:
            user_id (str): The unique ID (_id) of the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # subscription_type, e.g., 'free', 'premium'
            }
            OR
            {
                "success": False,
                "error": str  # Error description (e.g., user not found)
            }

        Constraints:
            - User must exist in the system.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user_info["subscription_type"]}

    def list_user_translation_requests(self, user_id: str) -> dict:
        """
        Retrieve all translation requests associated with the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[TranslationRequestInfo],  # May be empty if user has no requests
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - The user_id must reference an existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            req for req in self.translation_requests.values()
            if req.get("user_id") == user_id
        ]
        return { "success": True, "data": result }

    def get_translation_request_details(self, quest_id: str) -> dict:
        """
        Retrieve details for a specific translation request.

        Args:
            quest_id (str): The unique identifier of the translation request.

        Returns:
            dict: {
                "success": True,
                "data": TranslationRequestInfo,  # Details of the translation request
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure (e.g., request not found)
            }

        Constraints:
            - The translation request with the given quest_id must exist.
        """
        if quest_id not in self.translation_requests:
            return { "success": False, "error": "Translation request not found" }
        return {
            "success": True,
            "data": self.translation_requests[quest_id].copy()
        }

    def increment_user_usage(self, user_id: str, increment: int) -> dict:
        """
        Increase a user's usage_this_month by a specified translation unit count.

        Args:
            user_id (str): The unique ID of the user whose usage is to be incremented.
            increment (int): The number of translation units to add.
    
        Returns:
            dict:
                - On success: { "success": True, "message": ... }
                - On failure: { "success": False, "error": ... }
    
        Constraints:
            - User must exist.
            - Increment must be a non-negative integer.
            - usage_this_month + increment must not exceed monthly_allowance.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist." }

        if not isinstance(increment, int) or increment < 0:
            return { "success": False, "error": "Increment must be a non-negative integer." }

        new_usage = user["usage_this_month"] + increment
        if new_usage > user["monthly_allowance"]:
            return { "success": False, "error": "User's usage would exceed monthly allowance." }

        user["usage_this_month"] = new_usage
        return {
            "success": True,
            "message": f"usage_this_month incremented by {increment} for user {user_id}."
        }

    def reset_all_users_monthly_usage(self) -> dict:
        """
        Reset every user's usage_this_month value to 0 at the start of a new billing period.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "message": "All users' monthly usage has been reset."
            }

        Constraints:
            - All users' usage_this_month must be reset to 0.
            - Safe if there are no users.
        """
        for user in self.users.values():
            user["usage_this_month"] = 0
        return {
            "success": True,
            "message": "All users' monthly usage has been reset."
        }

    def activate_language(self, language_code: str) -> dict:
        """
        Marks the specified language as active in the supported languages list.

        Args:
            language_code (str): The language code to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Language <language_code> activated."
            }
            or
            {
                "success": False,
                "error": "Language not found"
            }
        Constraints:
            - The language must already exist in supported_languages.
            - Operation is idempotent: activating an already active language still returns success.
        """
        language = self.supported_languages.get(language_code)
        if not language:
            return { "success": False, "error": "Language not found" }
        if language["is_active"]:
            return { "success": True, "message": f"Language {language_code} activated." }
        language["is_active"] = True
        return { "success": True, "message": f"Language {language_code} activated." }

    def deactivate_language(self, language_code: str) -> dict:
        """
        Mark a specified language as inactive (not available for new translations).

        Args:
            language_code (str): The code of the language to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "Language <language_code> deactivated"
            }
            or
            {
                "success": False,
                "error": str  # e.g., language does not exist or already inactive
            }

        Constraints:
            - The language must exist in supported_languages.
            - Only active languages can be deactivated.
        """
        lang = self.supported_languages.get(language_code)
        if lang is None:
            return {"success": False, "error": "Language code does not exist"}
        if not lang["is_active"]:
            return {"success": False, "error": "Language is already inactive"}
        lang["is_active"] = False
        self.supported_languages[language_code] = lang  # Ensure update (dict is mutable so usually not needed)
        return {"success": True, "message": f"Language {language_code} deactivated"}

    def adjust_user_allowance(self, user_id: str, new_allowance: int) -> dict:
        """
        Modify a user's monthly_allowance (for administrative adjustment or plan upgrade/downgrade).
    
        Args:
            user_id (str): The user's unique identifier (_id).
            new_allowance (int): The new monthly allowance to set for the user.
    
        Returns:
            dict: 
            {
                "success": True,
                "message": "User's monthly allowance updated to <value>."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist.
            - new_allowance must be a positive integer.
            - User's usage_this_month must not exceed new_allowance.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist."}

        if not isinstance(new_allowance, int) or new_allowance <= 0:
            return {"success": False, "error": "New allowance must be a positive integer."}

        if user["usage_this_month"] > new_allowance:
            return {"success": False, "error": "Cannot set allowance below current monthly usage."}

        user["monthly_allowance"] = new_allowance
        return {
            "success": True,
            "message": f"User's monthly allowance updated to {new_allowance}."
        }


class TranslationServiceAccountManagementSystem(BaseEnv):
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
            if key == "users" and isinstance(value, dict):
                normalized = {}
                for original_key, user in value.items():
                    if isinstance(user, dict):
                        normalized[user.get("_id") or original_key] = copy.deepcopy(user)
                    else:
                        normalized[original_key] = copy.deepcopy(user)
                setattr(env, key, normalized)
                continue
            if key == "supported_languages" and isinstance(value, dict):
                normalized = {}
                for original_key, language in value.items():
                    if isinstance(language, dict):
                        normalized[language.get("language_code") or original_key] = copy.deepcopy(language)
                    else:
                        normalized[original_key] = copy.deepcopy(language)
                setattr(env, key, normalized)
                continue
            if key == "translation_requests" and isinstance(value, dict):
                normalized = {}
                for original_key, request in value.items():
                    if isinstance(request, dict):
                        normalized[request.get("quest_id") or original_key] = copy.deepcopy(request)
                    else:
                        normalized[original_key] = copy.deepcopy(request)
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

    def list_active_languages(self, **kwargs):
        return self._call_inner_tool('list_active_languages', kwargs)

    def get_language_info(self, **kwargs):
        return self._call_inner_tool('get_language_info', kwargs)

    def list_all_languages(self, **kwargs):
        return self._call_inner_tool('list_all_languages', kwargs)

    def get_user_info_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_name', kwargs)

    def get_user_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_id', kwargs)

    def get_user_monthly_left_allowance(self, **kwargs):
        return self._call_inner_tool('get_user_monthly_left_allowance', kwargs)

    def get_user_usage_this_month(self, **kwargs):
        return self._call_inner_tool('get_user_usage_this_month', kwargs)

    def get_user_subscription_type(self, **kwargs):
        return self._call_inner_tool('get_user_subscription_type', kwargs)

    def list_user_translation_requests(self, **kwargs):
        return self._call_inner_tool('list_user_translation_requests', kwargs)

    def get_translation_request_details(self, **kwargs):
        return self._call_inner_tool('get_translation_request_details', kwargs)

    def increment_user_usage(self, **kwargs):
        return self._call_inner_tool('increment_user_usage', kwargs)

    def reset_all_users_monthly_usage(self, **kwargs):
        return self._call_inner_tool('reset_all_users_monthly_usage', kwargs)

    def activate_language(self, **kwargs):
        return self._call_inner_tool('activate_language', kwargs)

    def deactivate_language(self, **kwargs):
        return self._call_inner_tool('deactivate_language', kwargs)

    def adjust_user_allowance(self, **kwargs):
        return self._call_inner_tool('adjust_user_allowance', kwargs)
