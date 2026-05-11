# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class LanguageInfo(TypedDict):
    language_code: str
    language_name: str
    is_active: bool

class TranslationToolInfo(TypedDict):
    tool_id: str
    tool_name: str
    supported_languages: List[str]

class UserInfo(TypedDict):
    user_id: str
    company_name: str
    usage_statistics: Dict[str, Any]  # Stats per user, could be expanded as needed

class TranslationRequestInfo(TypedDict):
    request_id: str
    user_id: str
    source_language: str
    target_language: str
    content_length: int
    timestamp: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a machine translation platform.
        """

        # Languages: {language_code: LanguageInfo}
        self.languages: Dict[str, LanguageInfo] = {}
        # Maps each language_code to LanguageInfo

        # Translation Tools: {tool_id: TranslationToolInfo}
        self.translation_tools: Dict[str, TranslationToolInfo] = {}
        # Maps each tool_id to TranslationToolInfo

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Maps each user_id to UserInfo

        # Translation Requests: {request_id: TranslationRequestInfo}
        self.translation_requests: Dict[str, TranslationRequestInfo] = {}
        # Maps each request_id to TranslationRequestInfo

        # Constraints:
        # - Only languages with is_active = True are available for translation.
        # - Each TranslationTool can only offer translation for languages in its supported_languages list.
        # - Usage statistics are tracked per user and can be aggregated by company.

    def _find_language_storage_key(self, language_code: str):
        if not isinstance(language_code, str) or not language_code.strip():
            return None
        normalized_code = language_code.strip()
        if normalized_code in self.languages:
            return normalized_code
        for key, language_info in self.languages.items():
            if language_info.get("language_code") == normalized_code:
                return key
        return None

    def _get_language_record(self, language_code: str):
        storage_key = self._find_language_storage_key(language_code)
        if storage_key is None:
            return None, None
        return storage_key, self.languages.get(storage_key)

    def get_translation_tool_by_name(self, tool_name: str) -> dict:
        """
        Retrieve information about a translation tool given its name.

        Args:
            tool_name (str): Name of the translation tool.

        Returns:
            dict:
                - { "success": True, "data": TranslationToolInfo } if found.
                - { "success": False, "error": "Translation tool not found" } if not found.

        Constraints:
            - tool_name matching is case sensitive.
        """
        for tool_info in self.translation_tools.values():
            if tool_info["tool_name"] == tool_name:
                return { "success": True, "data": tool_info }
        return { "success": False, "error": "Translation tool not found" }

    def get_supported_languages_by_tool(self, tool_id: str) -> dict:
        """
        Get the list of language codes supported by a specific translation tool.

        Args:
            tool_id (str): The unique ID of the translation tool.

        Returns:
            dict:
                - On success: {"success": True, "data": List[str]} (language codes supported)
                - On failure: {"success": False, "error": str}
        Constraints:
            - tool_id must exist in self.translation_tools.
        """
        tool = self.translation_tools.get(tool_id)
        if tool is None:
            return { "success": False, "error": "Tool not found" }
        supported_languages = tool.get("supported_languages", [])
        return { "success": True, "data": supported_languages }

    def get_language_info_by_code(self, language_code: str) -> dict:
        """
        Retrieve LanguageInfo for a given language code, including language name and is_active status.

        Args:
            language_code (str): Language code to look up.

        Returns:
            dict: {
                "success": True,
                "data": LanguageInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Returns info regardless of is_active status.
            - Returns error if language code does not exist.
        """
        _, language = self._get_language_record(language_code)
        if language is None:
            return {"success": False, "error": "Language code not found"}

        return {"success": True, "data": language}

    def list_active_languages(self) -> dict:
        """
        Retrieve all languages with is_active = True.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LanguageInfo],  # List (possibly empty) of LanguageInfo for active languages
            }

        Constraints:
            - Lists only languages with is_active = True.
            - No error: returns empty data if no active languages.
        """
        result = [
            lang_info for lang_info in self.languages.values()
            if lang_info["is_active"] is True
        ]
        return { "success": True, "data": result }

    def list_active_languages_supported_by_tool(self, tool_id: str) -> dict:
        """
        Retrieve all languages (names and codes) that are both currently active and supported by the given translation tool.

        Args:
            tool_id (str): The unique identifier of the translation tool.

        Returns:
            dict: {
                "success": True,
                "data": [
                    {"language_code": str, "language_name": str}, ...
                ]
            }
            OR
            {
                "success": False,
                "error": str  # e.g., "Translation tool not found"
            }

        Constraints:
            - Only languages that are in both the tool's supported_languages list and are active (is_active = True) are included.
        """
        tool = self.translation_tools.get(tool_id)
        if tool is None:
            return {
                "success": False,
                "error": "Translation tool not found"
            }

        result = []
        for lang_code in tool.get("supported_languages", []):
            _, lang_info = self._get_language_record(lang_code)
            if lang_info and lang_info.get("is_active"):
                result.append({
                    "language_code": lang_info["language_code"],
                    "language_name": lang_info["language_name"]
                })

        return {
            "success": True,
            "data": result
        }

    def get_user_by_company(self, company_name: str) -> dict:
        """
        List users associated with a specific company name.

        Args:
            company_name (str): The company name to query users for.

        Returns:
            dict
                - On success: { "success": True, "data": List[UserInfo] }.
                  The list may be empty if no users are found for the company.
                - On error: { "success": False, "error": str } if input is invalid.

        Constraints:
            - company_name must be a non-empty string.
        """
        if not isinstance(company_name, str) or not company_name.strip():
            return { "success": False, "error": "Invalid company_name" }

        result = [
            user_info
            for user_info in self.users.values()
            if user_info.get("company_name") == company_name
        ]

        return { "success": True, "data": result }

    def get_usage_statistics_by_user(self, user_id: str) -> dict:
        """
        Retrieve usage statistics for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - { "success": True, "data": usage_statistics } if user exists
                - { "success": False, "error": "User not found" } if invalid user_id

        Constraints:
            - The user must exist in the platform.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User not found"}

        usage_stats = user_info.get("usage_statistics", {})
        return {"success": True, "data": usage_stats}

    def aggregate_usage_statistics_by_company(self, company_name: str) -> dict:
        """
        Aggregate usage statistics for all users belonging to the specified company.

        Args:
            company_name (str): The company for which to aggregate usage statistics.

        Returns:
            dict with:
              - success: True and data: aggregated usage statistics dictionary if users found
              - success: False and error message if no users found for the company

        Details:
            - Aggregation by summing numeric values per usage_statistics key across all users in the company.
            - If statistics contain non-numeric values, those keys are ignored in aggregation.
        """
        # Collect all users for the company
        users_in_company = [
            user for user in self.users.values()
            if user.get("company_name") == company_name
        ]

        if not users_in_company:
            return { "success": False, "error": "No users found for the company" }

        aggregated_stats = {}

        for user in users_in_company:
            usage_stats = user.get("usage_statistics", {})
            for key, val in usage_stats.items():
                if isinstance(val, (int, float)):
                    aggregated_stats[key] = aggregated_stats.get(key, 0) + val
                # Non-numeric stats are ignored for summation

        return { "success": True, "data": aggregated_stats }

    def list_translation_requests_by_user(self, user_id: str) -> dict:
        """
        Retrieve all translation requests submitted by a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[TranslationRequestInfo]  # List of requests for the user (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found
            }

        Constraints:
            - The user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        requests = [
            req_info for req_info in self.translation_requests.values()
            if req_info["user_id"] == user_id
        ]
        return { "success": True, "data": requests }

    def activate_language(self, language_code: str) -> dict:
        """
        Set a language's `is_active` status to True, making it available for translation.

        Args:
            language_code (str): The language code to activate.

        Returns:
            dict: 
                { "success": True, "message": "Language <language_code> activated" }
                OR
                { "success": False, "error": <reason> }
        Constraints:
            - Language must exist in self.languages.
            - Language must not already be active.
        """
        language_key, language = self._get_language_record(language_code)
        if language is None:
            return { "success": False, "error": "Language does not exist" }
        if language.get("is_active", False):
            return { "success": False, "error": "Language already active" }
        language["is_active"] = True
        self.languages[language_key] = language
        return { "success": True, "message": f"Language {language_code} activated" }

    def deactivate_language(self, language_code: str) -> dict:
        """
        Set a language's is_active status to False (remove it from available languages).

        Args:
            language_code (str): The code of the language to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "Language <code> deactivated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Language must exist in the system.
            - Language is set to inactive if it is currently active.
            - No effect if already inactive (return error).
        """
        language_key, lang = self._get_language_record(language_code)
        if not lang:
            return {"success": False, "error": "Language code not found"}
        if lang["is_active"] is False:
            return {"success": False, "error": "Language is already inactive"}
        lang["is_active"] = False
        self.languages[language_key] = lang  # Explicit re-assign for completeness
        return {"success": True, "message": f"Language {language_code} deactivated."}

    def update_translation_tool_supported_languages(self, tool_id: str, supported_languages: list) -> dict:
        """
        Modify the list of supported language codes for a specified translation tool.

        Args:
            tool_id (str): The unique identifier for the translation tool.
            supported_languages (List[str]): The new list of language codes to support.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "message": "Supported languages updated for tool <tool_id>"
                  }
                - On failure: {
                      "success": False,
                      "error": "<description of error>"
                  }

        Constraints:
            - tool_id must exist in self.translation_tools.
            - Each language code in supported_languages must be present in self.languages.
            - This operation does not check if the languages are active.
        """
        if tool_id not in self.translation_tools:
            return {"success": False, "error": f"Translation tool with id '{tool_id}' does not exist."}

        invalid_codes = [
            code for code in supported_languages
            if self._find_language_storage_key(code) is None
        ]
        if invalid_codes:
            return {
                "success": False,
                "error": f"The following language codes do not exist: {', '.join(invalid_codes)}"
            }

        self.translation_tools[tool_id]['supported_languages'] = supported_languages
        return {
            "success": True,
            "message": f"Supported languages updated for tool {tool_id}"
        }

    def update_usage_statistics(self, user_id: str, stats_update: dict) -> dict:
        """
        Add to or modify the usage statistics record for a given user.

        Args:
            user_id (str): The ID of the user whose stats should be updated.
            stats_update (dict): Key-value pairs describing stat updates.
                - If the value is numeric and exists, increment; else set/overwrite.
                - If non-numeric, simply set/overwrite.
    
        Returns:
            dict: {
                "success": True,
                "message": str  # on success, describes user updated,
            }
            or
            {
                "success": False,
                "error": str  # error reason, e.g. user not found
            }
    
        Constraints:
            - User must exist.
            - No checks on stats_update shape; all valid Python keys/values handled.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        usage_stats = user.get('usage_statistics', {})
        for key, update_val in stats_update.items():
            current_val = usage_stats.get(key)
            # Increment if both are numeric, else overwrite.
            if isinstance(update_val, (int, float)) and isinstance(current_val, (int, float)):
                usage_stats[key] = current_val + update_val
            else:
                usage_stats[key] = update_val
        user['usage_statistics'] = usage_stats
        self.users[user_id] = user
        return { "success": True, "message": f"Usage statistics updated for user {user_id}" }

    def add_translation_request(
        self,
        request_id: str,
        user_id: str,
        source_language: str,
        target_language: str,
        content_length: int,
        timestamp: str,
        status: str
    ) -> dict:
        """
        Record a new translation request event in the platform.

        Args:
            request_id (str): Unique id for the translation request.
            user_id (str): The user's id making the request.
            source_language (str): Source language code.
            target_language (str): Target language code.
            content_length (int): Length of the content to be translated.
            timestamp (str): Request timestamp.
            status (str): Status of the translation.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Translation request recorded"
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - request_id must be unique (not already present)
            - user_id must exist
            - source_language and target_language must exist and be active
            - content_length must be a non-negative integer
        """
        # Check for unique request_id
        if request_id in self.translation_requests:
            return {"success": False, "error": "Request ID already exists"}

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check source_language and target_language exist and are active
        _, source_language_info = self._get_language_record(source_language)
        if source_language_info is None or not source_language_info["is_active"]:
            return {"success": False, "error": "Source language is invalid or inactive"}

        _, target_language_info = self._get_language_record(target_language)
        if target_language_info is None or not target_language_info["is_active"]:
            return {"success": False, "error": "Target language is invalid or inactive"}

        # content_length must be a non-negative integer
        if not isinstance(content_length, int) or content_length < 0:
            return {"success": False, "error": "content_length must be a non-negative integer"}

        # status should be a non-empty string
        if not isinstance(status, str) or len(status.strip()) == 0:
            return {"success": False, "error": "Status must be a non-empty string"}

        new_request = {
            "request_id": request_id,
            "user_id": user_id,
            "source_language": source_language,
            "target_language": target_language,
            "content_length": content_length,
            "timestamp": timestamp,
            "status": status
        }

        self.translation_requests[request_id] = new_request

        return {"success": True, "message": "Translation request recorded"}

    def update_translation_request_status(self, request_id: str, new_status: str) -> dict:
        """
        Update the status field of a translation request.

        Args:
            request_id (str): The identifier of the translation request to update.
            new_status (str): The new status value (e.g., "completed", "failed", "pending").

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "message": "Translation request <request_id> status updated to <new_status>."
                }
              - On failure: {
                    "success": False,
                    "error": "<reason>"
                }
        Constraints:
            - The translation request must exist.
            - new_status must be a non-empty string.
        """
        if not isinstance(new_status, str) or not new_status.strip():
            return {"success": False, "error": "Invalid new_status value."}

        if request_id not in self.translation_requests:
            return {"success": False, "error": "Translation request not found."}

        self.translation_requests[request_id]["status"] = new_status.strip()

        return {
            "success": True,
            "message": f"Translation request {request_id} status updated to {new_status.strip()}."
        }


class MachineTranslationPlatform(BaseEnv):
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

    def get_translation_tool_by_name(self, **kwargs):
        return self._call_inner_tool('get_translation_tool_by_name', kwargs)

    def get_supported_languages_by_tool(self, **kwargs):
        return self._call_inner_tool('get_supported_languages_by_tool', kwargs)

    def get_language_info_by_code(self, **kwargs):
        return self._call_inner_tool('get_language_info_by_code', kwargs)

    def list_active_languages(self, **kwargs):
        return self._call_inner_tool('list_active_languages', kwargs)

    def list_active_languages_supported_by_tool(self, **kwargs):
        return self._call_inner_tool('list_active_languages_supported_by_tool', kwargs)

    def get_user_by_company(self, **kwargs):
        return self._call_inner_tool('get_user_by_company', kwargs)

    def get_usage_statistics_by_user(self, **kwargs):
        return self._call_inner_tool('get_usage_statistics_by_user', kwargs)

    def aggregate_usage_statistics_by_company(self, **kwargs):
        return self._call_inner_tool('aggregate_usage_statistics_by_company', kwargs)

    def list_translation_requests_by_user(self, **kwargs):
        return self._call_inner_tool('list_translation_requests_by_user', kwargs)

    def activate_language(self, **kwargs):
        return self._call_inner_tool('activate_language', kwargs)

    def deactivate_language(self, **kwargs):
        return self._call_inner_tool('deactivate_language', kwargs)

    def update_translation_tool_supported_languages(self, **kwargs):
        return self._call_inner_tool('update_translation_tool_supported_languages', kwargs)

    def update_usage_statistics(self, **kwargs):
        return self._call_inner_tool('update_usage_statistics', kwargs)

    def add_translation_request(self, **kwargs):
        return self._call_inner_tool('add_translation_request', kwargs)

    def update_translation_request_status(self, **kwargs):
        return self._call_inner_tool('update_translation_request_status', kwargs)
