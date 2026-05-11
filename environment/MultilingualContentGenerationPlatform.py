# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class LanguageInfo(TypedDict):
    language_code: str
    language_name: str

class LocaleInfo(TypedDict):
    locale_code: str
    description: str
    associated_language_code: str
    region: str

class ContentGeneratorToolInfo(TypedDict):
    tool_id: str
    tool_name: str
    supported_locale_codes: List[str]

class TranslationResourceInfo(TypedDict):
    resource_id: str
    source_language_code: str
    target_language_code: str
    resource_type: str

class UserInfo(TypedDict):
    user_id: str
    organization: str
    permissions: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Languages: {language_code: LanguageInfo}
        self.languages: Dict[str, LanguageInfo] = {}

        # Locales: {locale_code: LocaleInfo}
        self.locales: Dict[str, LocaleInfo] = {}

        # Content Generator Tools: {tool_id: ContentGeneratorToolInfo}
        self.tools: Dict[str, ContentGeneratorToolInfo] = {}

        # Translation Resources: {resource_id: TranslationResourceInfo}
        self.translation_resources: Dict[str, TranslationResourceInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each ContentGeneratorTool can support multiple locales, and each locale must reference a valid language.
        # - The set of available languages/locales for a tool cannot be empty.
        # - Translation resources, if referenced, must map between supported languages.
        # - Users can only access features/locales permitted by their permissions/organization access.

    def get_tool_by_name(self, tool_name: str) -> dict:
        """
        Retrieve the ContentGeneratorToolInfo by the tool's name.

        Args:
            tool_name (str): Name of the content generator tool to search for.

        Returns:
            dict: {
                "success": True,
                "data": ContentGeneratorToolInfo,  # Tool information for the matched tool name
            }
            or
            {
                "success": False,
                "error": str  # If not found or ambiguous
            }

        Constraints:
            - Tool name must match exactly (case-sensitive).
            - If multiple tools have the same name (should not happen), the first match is returned.
        """
        for tool in self.tools.values():
            if tool["tool_name"] == tool_name:
                return {"success": True, "data": tool}
        return {"success": False, "error": f"No tool found with name '{tool_name}'."}

    def get_tool_by_id(self, tool_id: str) -> dict:
        """
        Retrieve information about a Content Generator Tool by its tool_id.

        Args:
            tool_id (str): The unique identifier of the tool.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ContentGeneratorToolInfo  # The tool's info
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., tool does not exist
                    }

        Constraints:
            - No permission check is performed for this operation.
            - Returns ContentGeneratorToolInfo if found.
        """
        tool_info = self.tools.get(tool_id)
        if tool_info is None:
            return {"success": False, "error": "Tool does not exist"}
        return {"success": True, "data": tool_info}

    def list_all_tools(self) -> dict:
        """
        Retrieve a list of all content generator tools available on the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[ContentGeneratorToolInfo]  # May be empty if no tools exist
            }

        Constraints:
            - No filters, returns all tools in the platform.
            - Does not enforce any tool has supported locales (assumes platform integrity).
        """
        tools_list = list(self.tools.values())
        return { "success": True, "data": tools_list }

    def get_supported_locales_for_tool(self, tool_id: str) -> dict:
        """
        Retrieve the list of supported locale codes for the specified content generator tool.

        Args:
            tool_id (str): The unique identifier of the content generator tool.

        Returns:
            dict: 
              - On success: {"success": True, "data": List[str]}  # List of supported locale codes
              - On failure: {"success": False, "error": str}      # If tool is not found or has empty supported locales

        Constraints:
            - The tool must exist in the system.
            - The tool should always have at least one supported locale, but method will check for misconfiguration.
        """
        tool = self.tools.get(tool_id)
        if not tool:
            return {"success": False, "error": "Tool not found"}
    
        locales = tool.get("supported_locale_codes", [])
        if not locales:
            return {"success": False, "error": "No supported locales configured for this tool"}

        return {"success": True, "data": locales}

    def get_locale_by_code(self, locale_code: str) -> dict:
        """
        Retrieve locale details by its code.

        Args:
            locale_code (str): The unique code of the locale to query, e.g. "en-US".

        Returns:
            dict:
                On success:
                    { "success": True, "data": LocaleInfo }
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - The locale_code must exist in the platform.
        """
        locale = self.locales.get(locale_code)
        if locale is None:
            return { "success": False, "error": "Locale not found" }

        return { "success": True, "data": locale }

    def list_locales(self) -> dict:
        """
        Retrieve the complete list of available locales on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LocaleInfo]  # List of all locale records (may be empty)
            }
        Constraints:
            - No user input required.
            - No permission or other constraints for this query.
        """
        locales_list = list(self.locales.values())
        return { "success": True, "data": locales_list }

    def get_language_by_code(self, language_code: str) -> dict:
        """
        Retrieve language details given a language_code.

        Args:
            language_code (str): The code of the language to retrieve (e.g., "en", "fr").

        Returns:
            dict: {
                "success": True,
                "data": LanguageInfo
            }
            or
            {
                "success": False,
                "error": "Language code not found"
            }

        Constraints:
            - language_code must exist in the languages dictionary.
        """
        lang = self.languages.get(language_code)
        if not lang:
            return {"success": False, "error": "Language code not found"}
        return {"success": True, "data": lang}

    def list_languages(self) -> dict:
        """
        Retrieve the complete list of supported languages on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LanguageInfo]  # List of all language entries (may be empty)
            }
        Constraints:
            - None.
        """
        languages_list = list(self.languages.values())
        return {
            "success": True,
            "data": languages_list
        }

    def get_locales_for_language(self, language_code: str) -> dict:
        """
        Retrieve all locale entries associated with a given language_code.

        Args:
            language_code (str): The language code to query (e.g., 'en', 'fr').

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[LocaleInfo]
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Language code not found"
                    }

        Constraints:
            - language_code must exist in self.languages.
            - Returns all locales with associated_language_code == language_code.
        """
        if language_code not in self.languages:
            return {"success": False, "error": "Language code not found"}

        result = [
            locale_info for locale_info in self.locales.values()
            if locale_info["associated_language_code"] == language_code
        ]
        return {"success": True, "data": result}

    def get_translation_resources(
        self,
        source_language_code: str = None,
        target_language_code: str = None
    ) -> dict:
        """
        Retrieve translation resources, optionally filtered by source and/or target language code.

        Args:
            source_language_code (str, optional): If specified, only resources with this source language code are returned.
            target_language_code (str, optional): If specified, only resources with this target language code are returned.

        Returns:
            dict: {
                "success": True,
                "data": List[TranslationResourceInfo],  # resources matching the criteria, empty list if none
            }
        """
        result = []
        for resource in self.translation_resources.values():
            if source_language_code and resource["source_language_code"] != source_language_code:
                continue
            if target_language_code and resource["target_language_code"] != target_language_code:
                continue
            result.append(resource)
        return {"success": True, "data": result}

    def get_user_permissions(self, user_id: str) -> dict:
        """
        Retrieve a user's permissions and accessible features.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                success: True if user found, False otherwise.
                data: {
                    "user_id": str,
                    "organization": str,
                    "permissions": List[str],
                } if success.
                error: str, if user not found.
        Constraints:
            - User must exist in the platform.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { 
            "success": True, 
            "data": {
                "user_id": user["user_id"],
                "organization": user["organization"],
                "permissions": user.get("permissions", []),
            }
        }

    @staticmethod
    def _normalize_permission_token(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")

    def _tool_permission_candidates(self, tool_id: str) -> set:
        candidates = {f"tool:{tool_id}"}
        tool = self.tools.get(tool_id, {})
        raw_values = [tool_id]
        if isinstance(tool, dict):
            raw_values.append(tool.get("tool_name", ""))

        for raw_value in raw_values:
            normalized = self._normalize_permission_token(raw_value)
            if not normalized:
                continue
            candidates.add(f"access_{normalized}")
            candidates.add(f"{normalized}_access")

            tokens = [
                token
                for token in normalized.split("_")
                if token and token not in {"tool", "content", "generator", "gen"} and not token.isdigit()
            ]
            if tokens:
                compact = "_".join(tokens)
                candidates.add(f"access_{compact}")
                candidates.add(f"{compact}_access")
                candidates.add(f"{compact}_tool_access")
        return candidates

    def _locale_permission_candidates(self, locale_code: str) -> set:
        normalized = self._normalize_permission_token(locale_code)
        candidates = {f"locale:{locale_code}"}
        if normalized:
            candidates.add(f"access_{normalized}")
            candidates.add(f"{normalized}_access")
            candidates.add(f"access_locale_{normalized}")
            candidates.add(f"locale_{normalized}_access")
        return candidates

    def check_tool_access_for_user(
        self, user_id: str, tool_id: str = None, locale_code: str = None
    ) -> dict:
        """
        Check whether the user has access to a given tool and/or locale.

        Args:
            user_id (str): The ID of the user to check.
            tool_id (str, optional): The tool ID to check access for.
            locale_code (str, optional): The locale code to check access for.

        Returns:
            dict: 
                - If valid check & processed:
                    { "success": True, "data": {"access": bool, "reason": str} }
                - On error/bad input:
                    { "success": False, "error": str }

        Constraints:
            - The user must exist.
            - If tool_id is provided, the tool_id must exist.
            - If locale_code is provided, the locale must exist.
            - At least one of tool_id or locale_code must be specified.
            - User access is granted if they have corresponding permission string(s).
        """

        # Input validation
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not tool_id and not locale_code:
            return { "success": False, "error": "Must specify at least tool_id or locale_code" }
        if tool_id and tool_id not in self.tools:
            return { "success": False, "error": "Tool does not exist" }
        if locale_code and locale_code not in self.locales:
            return { "success": False, "error": "Locale does not exist" }

        user_perms = self.users[user_id]["permissions"]

        tool_access = True
        locale_access = True
        missing = []

        if tool_id:
            required_candidates = self._tool_permission_candidates(tool_id)
            if not required_candidates.intersection(user_perms):
                tool_access = False
                missing.append(f"tool access ({tool_id})")

        if locale_code:
            locale_supported_by_tool = False
            if tool_id:
                locale_supported_by_tool = locale_code in self.tools[tool_id].get("supported_locale_codes", [])

            if locale_supported_by_tool and tool_access:
                locale_access = True
            else:
                required_candidates = self._locale_permission_candidates(locale_code)
                if not required_candidates.intersection(user_perms):
                    locale_access = False
                    missing.append(f"locale access ({locale_code})")

        overall_access = tool_access and locale_access
        if overall_access:
            return {
                "success": True,
                "data": {
                    "access": True,
                    "reason": "User has required access."
                }
            }
        else:
            missing_reasons = ', '.join(missing)
            return {
                "success": True,
                "data": {
                    "access": False,
                    "reason": f"User lacks permission for {missing_reasons}."
                }
            }

    def add_supported_locale_to_tool(self, tool_id: str, locale_code: str) -> dict:
        """
        Add a locale code to a content generator tool’s supported locales.

        Args:
            tool_id (str): The unique identifier of the content generator tool.
            locale_code (str): The locale code to add (must reference a valid Locale).

        Returns:
            dict: {
                "success": True,
                "message": "Locale added to tool"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Tool must exist.
            - Locale must exist.
            - Locale's associated language must be valid.
            - Locale must not already be in tool's supported_locale_codes.
        """
        # Check if tool exists
        if tool_id not in self.tools:
            return { "success": False, "error": "Tool does not exist" }

        # Check if locale exists
        if locale_code not in self.locales:
            return { "success": False, "error": "Locale does not exist" }

        tool = self.tools[tool_id]
        locale = self.locales[locale_code]

        # Check if locale already supported
        if locale_code in tool["supported_locale_codes"]:
            return { "success": False, "error": "Locale already supported by tool" }

        # Check if locale's associated language exists
        lang_code = locale["associated_language_code"]
        if lang_code not in self.languages:
            return { "success": False, "error": "Locale references invalid language" }

        # Add the locale to the tool
        tool["supported_locale_codes"].append(locale_code)
        return { "success": True, "message": f"Locale '{locale_code}' added to tool '{tool_id}'" }

    def remove_supported_locale_from_tool(self, tool_id: str, locale_code: str) -> dict:
        """
        Remove a locale code from a content generator tool's supported locales.

        Args:
            tool_id (str): The ID of the content generator tool.
            locale_code (str): The locale code to remove.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Locale <locale_code> removed from tool <tool_id>."
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - After removal, supported_locale_codes must not be empty.
            - The tool and locale must exist.
            - The locale_code must actually be supported by the tool.
        """
        tool = self.tools.get(tool_id)
        if not tool:
            return { "success": False, "error": "Tool does not exist" }
    
        if locale_code not in tool["supported_locale_codes"]:
            return { "success": False, "error": "Locale code not supported by the tool" }

        if len(tool["supported_locale_codes"]) == 1:
            # Would result in empty set if we remove the last one
            return {
                "success": False,
                "error": "Cannot remove the last supported locale from the tool"
            }
    
        # Remove the locale code
        tool["supported_locale_codes"].remove(locale_code)
        return {
            "success": True,
            "message": f"Locale {locale_code} removed from tool {tool_id}."
        }

    def add_translation_resource(
        self,
        resource_id: str,
        source_language_code: str,
        target_language_code: str,
        resource_type: str
    ) -> dict:
        """
        Adds a new translation resource mapping between supported languages.

        Args:
            resource_id (str): Unique identifier for the translation resource.
            source_language_code (str): Source language code (must exist).
            target_language_code (str): Target language code (must exist).
            resource_type (str): Type of the translation resource (e.g., 'machine', 'human').

        Returns:
            dict: {
                "success": True,
                "message": "Translation resource added."
            }
            or
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - resource_id must be unique.
            - Both source_language_code and target_language_code must exist in the platform languages.
        """
        if resource_id in self.translation_resources:
            return { "success": False, "error": "Resource ID already exists." }

        if source_language_code not in self.languages:
            return { "success": False, "error": "Invalid source language code." }

        if target_language_code not in self.languages:
            return { "success": False, "error": "Invalid target language code." }

        if not isinstance(resource_type, str) or not resource_type.strip():
            return { "success": False, "error": "Resource type must be a non-empty string." }

        self.translation_resources[resource_id] = {
            "resource_id": resource_id,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "resource_type": resource_type
        }

        return { "success": True, "message": "Translation resource added." }

    def remove_translation_resource(self, resource_id: str) -> dict:
        """
        Remove a translation resource by its unique resource_id.

        Args:
            resource_id (str): The ID of the translation resource to remove.

        Returns:
            dict: 
                On success: 
                    {
                        "success": True,
                        "message": "Translation resource <resource_id> removed."
                    }
                On failure: 
                    {
                        "success": False,
                        "error": "Translation resource does not exist."
                    }

        Constraints:
            - Only resources currently present can be removed.
            - No deletion occurs if the specified resource_id does not exist.
        """
        if resource_id not in self.translation_resources:
            return { "success": False, "error": "Translation resource does not exist." }
    
        del self.translation_resources[resource_id]
        return { "success": True, "message": f"Translation resource {resource_id} removed." }

    def create_locale(
        self,
        locale_code: str,
        description: str,
        associated_language_code: str,
        region: str
    ) -> dict:
        """
        Add a new locale to the system.

        Args:
            locale_code (str): Unique locale identifier (e.g., 'en-US').
            description (str): Description of the locale.
            associated_language_code (str): Language code that the locale is based on; must exist.
            region (str): Region/string representing the locale's regional variant.

        Returns:
            dict: Success:
                {
                    "success": True,
                    "message": "Locale <locale_code> created successfully."
                }
            dict: Failure (language missing, duplicate locale, or invalid input):
                {
                    "success": False,
                    "error": "Associated language does not exist." | "Locale already exists." | other reason.
                }

        Constraints:
            - Locale code must be unique.
            - Associated language must already exist in the platform.
        """
        # Check for valid input
        if not all([locale_code, description, associated_language_code, region]):
            return {"success": False, "error": "All fields (locale_code, description, associated_language_code, region) are required."}

        if locale_code in self.locales:
            return {"success": False, "error": "Locale already exists."}

        if associated_language_code not in self.languages:
            return {"success": False, "error": "Associated language does not exist."}

        # Construct LocaleInfo and add to platform
        new_locale: LocaleInfo = {
            'locale_code': locale_code,
            'description': description,
            'associated_language_code': associated_language_code,
            'region': region
        }
        self.locales[locale_code] = new_locale

        return {
            "success": True,
            "message": f"Locale {locale_code} created successfully."
        }

    def delete_locale(self, locale_code: str) -> dict:
        """
        Delete an existing locale from the platform.

        Args:
            locale_code (str): The locale code to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Locale <locale_code> deleted." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Cannot delete a locale if it is in active use (referenced by any ContentGeneratorTool).
            - Locale must exist.
        """
        # Check existence
        if locale_code not in self.locales:
            return { "success": False, "error": "Locale does not exist." }

        # Check if in use by any tool
        for tool in self.tools.values():
            if locale_code in tool.get('supported_locale_codes', []):
                return {
                    "success": False,
                    "error": "Locale is in active use and cannot be deleted."
                }
    
        # Safe to delete
        del self.locales[locale_code]
        return {
            "success": True,
            "message": f"Locale {locale_code} deleted."
        }

    def add_language(self, language_code: str, language_name: str) -> dict:
        """
        Add a new supported language to the platform.

        Args:
            language_code (str): Unique code for the language, e.g., 'en', 'fr'.
            language_name (str): Human-readable name for the language, e.g., 'English'.

        Returns:
            dict: {
                "success": True,
                "message": "Language <code> (<name>) added"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - language_code must be unique (not already present in self.languages).
            - language_code and language_name must be non-empty.
        """
        code = (language_code or "").strip()
        name = (language_name or "").strip()

        if not code:
            return { "success": False, "error": "Language code cannot be empty" }
        if not name:
            return { "success": False, "error": "Language name cannot be empty" }
        if code in self.languages:
            return { "success": False, "error": "Language code already exists" }

        self.languages[code] = {
            "language_code": code,
            "language_name": name
        }

        return {
            "success": True,
            "message": f"Language {code} ({name}) added"
        }

    def delete_language(self, language_code: str) -> dict:
        """
        Remove a supported language if and only if it is not in active use by any locale or translation resource.

        Args:
            language_code (str): The code of the language to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Language deleted"
            }
            or
            {
                "success": False,
                "error": str  # error message describing the failure reason
            }

        Constraints:
            - Language must exist.
            - Language must NOT be referenced by any Locale's associated_language_code.
            - Language must NOT be referenced by any TranslationResource's source or target language.
        """
        # Check existence
        if language_code not in self.languages:
            return { "success": False, "error": "Language does not exist" }

        # Check Locales (active use)
        for locale in self.locales.values():
            if locale["associated_language_code"] == language_code:
                return {
                    "success": False,
                    "error": f"Language {language_code} is actively used by locale '{locale['locale_code']}'."
                }

        # Check Translation Resources (active use)
        for resource in self.translation_resources.values():
            if (resource["source_language_code"] == language_code or
                resource["target_language_code"] == language_code):
                return {
                    "success": False,
                    "error": f"Language {language_code} is used in translation resource '{resource['resource_id']}'."
                }

        # Passed all checks; delete the language
        del self.languages[language_code]
        return { "success": True, "message": f"Language {language_code} deleted" }

    def update_user_permissions(self, user_id: str, new_permissions: list) -> dict:
        """
        Update the permissions list for the user with the specified user_id.

        Args:
            user_id (str): The user or organization's ID.
            new_permissions (list[str]): The new list of permissions to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Permissions updated for user <user_id>"
            }
            or
            {
                "success": False,
                "error": "User not found" | "Invalid permissions format"
            }

        Constraints:
            - user_id must exist in the platform.
            - new_permissions must be a list of strings.
            - This operation does not validate permission values themselves beyond type.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        if not isinstance(new_permissions, list) or not all(isinstance(p, str) for p in new_permissions):
            return { "success": False, "error": "Invalid permissions format" }

        self.users[user_id]["permissions"] = new_permissions
        return { "success": True, "message": f"Permissions updated for user {user_id}" }

    def create_content_generator_tool(
        self, 
        tool_id: str, 
        tool_name: str, 
        supported_locale_codes: list
    ) -> dict:
        """
        Create a new content generator tool with the specified supported locales.

        Args:
            tool_id (str): Unique identifier for the tool.
            tool_name (str): Name of the tool.
            supported_locale_codes (list of str): List of locale_code values (must exist in platform).

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Content generator tool <tool_name> (ID: <tool_id>) created with supported locales."
                }
                Failure: {
                    "success": False,
                    "error": <description>
                }

        Constraints:
            - tool_id must be unique (not already exist).
            - supported_locale_codes must not be empty.
            - Each locale_code in supported_locale_codes must exist in self.locales.
        """
        if tool_id in self.tools:
            return {"success": False, "error": f"Tool ID '{tool_id}' already exists."}

        if not supported_locale_codes or not isinstance(supported_locale_codes, list):
            return {"success": False, "error": "Supported locale codes must be a non-empty list."}

        missing_locales = [
            code for code in supported_locale_codes
            if code not in self.locales
        ]
        if missing_locales:
            return {
                "success": False, 
                "error": f"Locale codes do not exist: {', '.join(missing_locales)}"
            }

        # Create and store the new tool
        self.tools[tool_id] = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "supported_locale_codes": supported_locale_codes
        }

        return {
            "success": True,
            "message": (
                f"Content generator tool '{tool_name}' (ID: {tool_id}) created with supported locales."
            )
        }

    def delete_content_generator_tool(self, tool_id: str) -> dict:
        """
        Remove a content generator tool from the platform.

        Args:
            tool_id (str): The unique ID of the tool to remove.

        Returns:
            dict: 
              - {"success": True, "message": "Tool <tool_id> deleted successfully."}
              - {"success": False, "error": "<reason>"} on error

        Constraints:
            - The tool must exist.
            - Deletion must NOT result in any locale being unsupported by any tool 
              (no locale can be left "orphaned" with zero tools after this operation).
        """
        if tool_id not in self.tools:
            return {"success": False, "error": f"Tool '{tool_id}' does not exist."}

        # Locales supported by the tool being removed
        tool_info = self.tools[tool_id]
        affected_locales = set(tool_info.get("supported_locale_codes", []))

        # For each affected locale, check if there are other tools supporting it
        orphaned_locales = []
        for locale in affected_locales:
            supported_elsewhere = any(
                locale in tool.get("supported_locale_codes", []) and tid != tool_id
                for tid, tool in self.tools.items()
            )
            if not supported_elsewhere:
                orphaned_locales.append(locale)

        if orphaned_locales:
            return {
                "success": False,
                "error": (
                    "Cannot delete tool because the following locales would be orphaned: " +
                    ", ".join(orphaned_locales)
                )
            }

        # Safe to delete: remove the tool
        del self.tools[tool_id]

        return {
            "success": True,
            "message": f"Tool '{tool_id}' deleted successfully."
        }


class MultilingualContentGenerationPlatform(BaseEnv):
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
            if key in {
                "languages",
                "locales",
                "tools",
                "translation_resources",
                "users",
            } and isinstance(value, dict):
                id_field = {
                    "languages": "language_code",
                    "locales": "locale_code",
                    "tools": "tool_id",
                    "translation_resources": "resource_id",
                    "users": "user_id",
                }[key]
                normalized = {}
                for outer_key, item in value.items():
                    item_copy = copy.deepcopy(item)
                    if isinstance(item_copy, dict):
                        normalized[item_copy.get(id_field, outer_key)] = item_copy
                    else:
                        normalized[outer_key] = item_copy
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

    def get_tool_by_name(self, **kwargs):
        return self._call_inner_tool('get_tool_by_name', kwargs)

    def get_tool_by_id(self, **kwargs):
        return self._call_inner_tool('get_tool_by_id', kwargs)

    def list_all_tools(self, **kwargs):
        return self._call_inner_tool('list_all_tools', kwargs)

    def get_supported_locales_for_tool(self, **kwargs):
        return self._call_inner_tool('get_supported_locales_for_tool', kwargs)

    def get_locale_by_code(self, **kwargs):
        return self._call_inner_tool('get_locale_by_code', kwargs)

    def list_locales(self, **kwargs):
        return self._call_inner_tool('list_locales', kwargs)

    def get_language_by_code(self, **kwargs):
        return self._call_inner_tool('get_language_by_code', kwargs)

    def list_languages(self, **kwargs):
        return self._call_inner_tool('list_languages', kwargs)

    def get_locales_for_language(self, **kwargs):
        return self._call_inner_tool('get_locales_for_language', kwargs)

    def get_translation_resources(self, **kwargs):
        return self._call_inner_tool('get_translation_resources', kwargs)

    def get_user_permissions(self, **kwargs):
        return self._call_inner_tool('get_user_permissions', kwargs)

    def check_tool_access_for_user(self, **kwargs):
        return self._call_inner_tool('check_tool_access_for_user', kwargs)

    def add_supported_locale_to_tool(self, **kwargs):
        return self._call_inner_tool('add_supported_locale_to_tool', kwargs)

    def remove_supported_locale_from_tool(self, **kwargs):
        return self._call_inner_tool('remove_supported_locale_from_tool', kwargs)

    def add_translation_resource(self, **kwargs):
        return self._call_inner_tool('add_translation_resource', kwargs)

    def remove_translation_resource(self, **kwargs):
        return self._call_inner_tool('remove_translation_resource', kwargs)

    def create_locale(self, **kwargs):
        return self._call_inner_tool('create_locale', kwargs)

    def delete_locale(self, **kwargs):
        return self._call_inner_tool('delete_locale', kwargs)

    def add_language(self, **kwargs):
        return self._call_inner_tool('add_language', kwargs)

    def delete_language(self, **kwargs):
        return self._call_inner_tool('delete_language', kwargs)

    def update_user_permissions(self, **kwargs):
        return self._call_inner_tool('update_user_permissions', kwargs)

    def create_content_generator_tool(self, **kwargs):
        return self._call_inner_tool('create_content_generator_tool', kwargs)

    def delete_content_generator_tool(self, **kwargs):
        return self._call_inner_tool('delete_content_generator_tool', kwargs)
