# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class LanguageInfo(TypedDict):
    language_id: str
    name: str
    region: str
    script: str
    family: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Languages: {language_id: LanguageInfo}
        self.languages: Dict[str, LanguageInfo] = {}

        # Constraints:
        # - language_id must be unique (enforced by dict keys)
        # - name, region, script, family should be well-formed and non-empty for each language
        # - Retrieval by language_id is efficient via dictionary

    def get_language_by_id(self, language_id: str) -> dict:
        """
        Retrieve all metadata for a language specified by its language_id.

        Args:
            language_id (str): Unique identifier of the language.

        Returns:
            dict: {
                "success": True,
                "data": LanguageInfo  # Metadata dictionary of the language
            }
            or
            {
                "success": False,
                "error": str  # Error message if language not found
            }

        Constraints:
            - The language_id must exist in the database.
        """
        if language_id not in self.languages:
            return {"success": False, "error": "Language not found"}

        return {"success": True, "data": self.languages[language_id]}

    def get_languages_by_ids(self, language_ids: list[str]) -> dict:
        """
        Retrieve LanguageInfo objects for each specified language_id.

        Args:
            language_ids (list[str]): List of language_id strings to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": Dict[str, LanguageInfo] }
                    - Each key is a found language_id, and value is the full LanguageInfo.
                    - If input list is empty, "data" will be {}.
                    - If a language_id is not found, it is simply omitted.
                - On error: { "success": False, "error": str } (e.g., input not a list)

        Constraints:
            - Efficient dictionary-based lookup.
        """
        if not isinstance(language_ids, list):
            return { "success": False, "error": "Input must be a list of language_id strings." }

        result = {}
        for lang_id in language_ids:
            if lang_id in self.languages:
                result[lang_id] = self.languages[lang_id]

        return { "success": True, "data": result }

    def list_all_languages(self) -> dict:
        """
        Retrieve the complete list of language entries in the database.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "data": List[LanguageInfo]  # list of all language records (may be empty)
                    }
        Constraints:
            - Returns all registered languages.
            - No parameters or filters.
        """
        all_languages = list(self.languages.values())
        return { "success": True, "data": all_languages }

    def search_languages_by_name(self, name: str, fuzzy: bool = True) -> dict:
        """
        Find languages that match a given name (exact or fuzzy).

        Args:
            name (str): The language name to search for. Must be non-empty.
            fuzzy (bool): If True (default), perform case-insensitive substring match.
                          If False, require exact case-sensitive match.

        Returns:
            dict:
                - On success: {'success': True, 'data': List[LanguageInfo]}
                - On error:   {'success': False, 'error': str}

        Constraints:
            - `name` must be a non-empty string.
            - If fuzzy is True, match if `name` is a substring (case-insensitive) of language name.
            - If fuzzy is False, match if `name` == language name (case-sensitive).
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Search name must be a non-empty string"}
        name = name.strip()
        results = []
        if fuzzy:
            name_lower = name.lower()
            for lang in self.languages.values():
                if name_lower in lang["name"].lower():
                    results.append(lang)
        else:
            for lang in self.languages.values():
                if lang["name"] == name:
                    results.append(lang)
        return {"success": True, "data": results}

    def filter_languages_by_region(self, region: str) -> dict:
        """
        Retrieve all languages whose 'region' attribute matches the specified region.

        Args:
            region (str): Region value to filter languages by (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[LanguageInfo],  # may be empty if no match
            }
            or
            {
                "success": False,
                "error": str  # error message for invalid region input
            }

        Constraints:
            - region must be a non-empty string.
            - Only returns languages where region matches exactly.
        """
        if not isinstance(region, str) or not region.strip():
            return { "success": False, "error": "Region must be a non-empty string." }

        result = [
            lang_info for lang_info in self.languages.values()
            if lang_info["region"] == region
        ]
        return { "success": True, "data": result }

    def filter_languages_by_script(self, script: str) -> dict:
        """
        Retrieve all languages that use a specific script.

        Args:
            script (str): The script to filter by (case-sensitive match).

        Returns:
            dict: {
                "success": True,
                "data": List[LanguageInfo],  # List may be empty if no matches
            }

        Notes:
            - If `script` is empty, returns an empty list.
            - Script comparison is case-sensitive.
        """
        if not script:
            return {"success": True, "data": []}
        result = [
            lang_info for lang_info in self.languages.values()
            if lang_info["script"] == script
        ]
        return {"success": True, "data": result}

    def filter_languages_by_family(self, family: str) -> dict:
        """
        Retrieve all languages belonging to the specified language family.

        Args:
            family (str): The language family name to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[LanguageInfo]  # List (possibly empty) of matching languages
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., invalid family parameter
            }

        Constraints:
            - Only exact matches on the 'family' attribute (case-sensitive).
            - 'family' must be provided and non-empty string.
        """
        if not isinstance(family, str) or not family.strip():
            return {"success": False, "error": "Invalid or missing 'family' parameter"}

        result = [
            lang_info for lang_info in self.languages.values()
            if lang_info["family"] == family
        ]
        return {"success": True, "data": result}

    def check_language_exists(self, language_id: str) -> dict:
        """
        Verifies whether the given language_id exists in the database.

        Args:
            language_id (str): Unique identifier of the language to check.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if language_id exists, False otherwise
            }
        Constraints:
            - language_id should be a non-empty string for a valid check. If invalid, returns exists=False.
        """
        if not isinstance(language_id, str) or not language_id:
            return {"success": True, "exists": False}

        exists = language_id in self.languages
        return {"success": True, "exists": exists}

    def add_language(
        self, 
        language_id: str, 
        name: str, 
        region: str, 
        script: str, 
        family: str
    ) -> dict:
        """
        Add a new language entry, ensuring unique language_id and complete (non-empty) metadata.

        Args:
            language_id (str): Unique identifier for the language.
            name (str): Name of the language.
            region (str): Primary region where the language is used.
            script (str): Script used for the language.
            family (str): Language family.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Language added successfully." }
                On error:
                    { "success": False, "error": str }
                
        Constraints:
            - language_id must not already exist in the catalog.
            - All attributes must be non-empty (name, region, script, family).
        """
        if language_id in self.languages:
            return { "success": False, "error": "Language ID already exists." }
    
        # Check all required fields
        if not all([
            isinstance(language_id, str) and language_id.strip(),
            isinstance(name, str) and name.strip(),
            isinstance(region, str) and region.strip(),
            isinstance(script, str) and script.strip(),
            isinstance(family, str) and family.strip()
        ]):
            return { "success": False, "error": "All language fields must be non-empty." }
    
        new_language: LanguageInfo = {
            "language_id": language_id.strip(),
            "name": name.strip(),
            "region": region.strip(),
            "script": script.strip(),
            "family": family.strip()
        }
        self.languages[language_id.strip()] = new_language
        return { "success": True, "message": "Language added successfully." }

    def update_language(
        self,
        language_id: str,
        name: str = None,
        region: str = None,
        script: str = None,
        family: str = None
    ) -> dict:
        """
        Modify the information of an existing language entry.

        Args:
            language_id (str): The unique identifier for the language to modify.
            name (str, optional): New value for name.
            region (str, optional): New value for region.
            script (str, optional): New value for script.
            family (str, optional): New value for family.

        Returns:
            dict: 
                On success: { "success": True, "message": "Language updated successfully" }
                On error: { "success": False, "error": str }

        Constraints:
            - language_id must exist.
            - Any provided fields must be non-empty strings.
            - At least one updatable field must be provided.
        """
        if language_id not in self.languages:
            return { "success": False, "error": "Language ID does not exist" }

        updatable_fields = ["name", "region", "script", "family"]
        updates = {}
        for field, value in zip(updatable_fields, [name, region, script, family]):
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    return {"success": False, "error": f"Invalid value for {field}"}
                updates[field] = value.strip()

        if not updates:
            return {"success": False, "error": "No valid fields provided for update" }

        # Apply updates
        for field, value in updates.items():
            self.languages[language_id][field] = value

        return {"success": True, "message": "Language updated successfully"}

    def delete_language(self, language_id: str) -> dict:
        """
        Remove a language entry from the catalog by language_id.

        Args:
            language_id (str): The unique identifier of the language to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Language <language_id> deleted"
            }
            or
            {
                "success": False,
                "error": "Language ID not found"
            }

        Constraints:
            - language_id must exist in the catalog to be deleted.
        """
        if language_id not in self.languages:
            return {"success": False, "error": "Language ID not found"}
        del self.languages[language_id]
        return {"success": True, "message": f"Language {language_id} deleted"}

    def bulk_add_languages(self, languages: list[dict]) -> dict:
        """
        Add multiple language entries at once, ensuring each is unique and complete.

        Args:
            languages (list of dict): Each dict should contain keys:
                - language_id (str)
                - name (str)
                - region (str)
                - script (str)
                - family (str)

        Returns:
            dict: On success,
                {"success": True, "message": "N languages added successfully."}
                On failure,
                {"success": False, "error": "Error description."}

        Constraints:
            - language_id must be unique (not present in database or duplicated in input).
            - All fields (language_id, name, region, script, family) must be present and non-empty in each entry.
            - If any error occurs, no languages are added.
        """
        required_fields = ["language_id", "name", "region", "script", "family"]

        # Check for duplicate language_ids in input
        input_ids = [lang.get("language_id", "") for lang in languages]
        seen = set()
        for lid in input_ids:
            if not lid:
                return {"success": False, "error": "Missing or empty language_id in input list."}
            if lid in seen:
                return {"success": False, "error": f"Duplicate language_id in input list: {lid}"}
            seen.add(lid)

        # Check for completeness & current-DB-uniqueness
        for lang in languages:
            for field in required_fields:
                if field not in lang or not str(lang[field]).strip():
                    return {"success": False, "error": f"Missing or empty attribute '{field}' for language_id '{lang.get('language_id', '<unknown>')}'."}
            # Uniqueness in database
            if lang["language_id"] in self.languages:
                return {"success": False, "error": f"Duplicate language_id in database: {lang['language_id']}"}

        # All checks passed, add entries
        for lang in languages:
            # All are complete; we assume input dicts fit the LanguageInfo structure
            self.languages[lang["language_id"]] = {
                "language_id": lang["language_id"],
                "name": lang["name"],
                "region": lang["region"],
                "script": lang["script"],
                "family": lang["family"],
            }

        return {"success": True, "message": f"{len(languages)} languages added successfully."}


class LanguageCatalogDatabase(BaseEnv):
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

    def get_language_by_id(self, **kwargs):
        return self._call_inner_tool('get_language_by_id', kwargs)

    def get_languages_by_ids(self, **kwargs):
        return self._call_inner_tool('get_languages_by_ids', kwargs)

    def list_all_languages(self, **kwargs):
        return self._call_inner_tool('list_all_languages', kwargs)

    def search_languages_by_name(self, **kwargs):
        return self._call_inner_tool('search_languages_by_name', kwargs)

    def filter_languages_by_region(self, **kwargs):
        return self._call_inner_tool('filter_languages_by_region', kwargs)

    def filter_languages_by_script(self, **kwargs):
        return self._call_inner_tool('filter_languages_by_script', kwargs)

    def filter_languages_by_family(self, **kwargs):
        return self._call_inner_tool('filter_languages_by_family', kwargs)

    def check_language_exists(self, **kwargs):
        return self._call_inner_tool('check_language_exists', kwargs)

    def add_language(self, **kwargs):
        return self._call_inner_tool('add_language', kwargs)

    def update_language(self, **kwargs):
        return self._call_inner_tool('update_language', kwargs)

    def delete_language(self, **kwargs):
        return self._call_inner_tool('delete_language', kwargs)

    def bulk_add_languages(self, **kwargs):
        return self._call_inner_tool('bulk_add_languages', kwargs)

