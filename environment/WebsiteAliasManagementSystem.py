# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import re
import uuid
import datetime



class AliasInfo(TypedDict):
    alias_id: str
    alias_string: str
    associated_entity_type: str
    associated_entity_id: str
    date_created: str
    sta: str  # Likely means 'status'

class EntityInfo(TypedDict):
    entity_id: str
    entity_type: str  # Could be 'resource', 'profile', or 'url'
    owner_id: str
    target_url: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing website aliases and their assignments.
        """
        # Aliases: alias_id -> AliasInfo
        # Maps each alias to its info. Each alias_string must be globally unique.
        self.aliases: Dict[str, AliasInfo] = {}

        # Entities: entity_id -> EntityInfo
        # Resources, profiles, or URLs that may have an alias assigned.
        self.entities: Dict[str, EntityInfo] = {}
        self._validate_alias_string_format_state = None

        # -- Constraint notes (for implementation in methods) --
        # - Each alias_string must be unique across the system (no duplicate aliases).
        # - An alias must be associated with exactly one entity (resource, profile, or URL).
        # - Only available (unassigned) aliases can be assigned to a new resource.
        # - Alias strings may be subject to format/character restrictions per platform policy.

    def check_alias_availability(self, alias_string: str) -> dict:
        """
        Determines whether a specific alias string is available for assignment.
        Checks:
          - That alias_string meets platform's format/character policy (calls validate_alias_string_format).
          - That alias_string is not already in use (globally unique among aliases).

        Args:
            alias_string (str): The string to check for availability.

        Returns:
            dict:
                {
                    "success": True,
                    "available": True
                }
                if available
                or
                {
                    "success": True,
                    "available": False,
                    "reason": <reason>
                }
                if not available or format-invalid
                or
                {
                    "success": False,
                    "error": <error message>
                }
                for unexpected conditions.
        """
        # Validate alias string format (assume separate method or simple logic)
        if hasattr(self, "validate_alias_string_format"):
            fmt_result = self.validate_alias_string_format(alias_string)
            format_data = fmt_result.get("data", {}) if isinstance(fmt_result, dict) else {}
            if not format_data.get("valid", False):
                return {
                    "success": True,
                    "available": False,
                    "reason": format_data.get("reason", "Alias string format invalid")
                }
        # Check uniqueness in self.aliases (alias_string must be unique)
        for alias_info in self.aliases.values():
            if alias_info["alias_string"] == alias_string:
                return {
                    "success": True,
                    "available": False,
                    "reason": "Alias is already in use"
                }
        return {"success": True, "available": True}

    def get_alias_by_string(self, alias_string: str) -> dict:
        """
        Retrieve all information about a given alias using its alias_string.

        Args:
            alias_string (str): The alias string to look up.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AliasInfo  # Information about the alias
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Alias not found"
                    }
    
        Constraints:
            - alias_string must exist in the system.
        """
        for alias_info in self.aliases.values():
            if alias_info["alias_string"] == alias_string:
                return {"success": True, "data": alias_info}
        return {"success": False, "error": "Alias not found"}

    def get_alias_by_id(self, alias_id: str) -> dict:
        """
        Retrieve all information about a given alias using its alias_id.

        Args:
            alias_id (str): The unique identifier for the alias.

        Returns:
            dict: 
                {"success": True, "data": AliasInfo} if found,
                {"success": False, "error": "Alias ID not found"} otherwise.

        Constraints:
            - Alias ID must exist in the system.
        """
        alias_info = self.aliases.get(alias_id)
        if alias_info is None:
            return {"success": False, "error": "Alias ID not found"}
        return {"success": True, "data": alias_info}

    def list_all_aliases(self) -> dict:
        """
        List all aliases currently registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AliasInfo]  # All AliasInfo records (may be empty)
            }
        """
        alias_list = list(self.aliases.values())
        return { "success": True, "data": alias_list }

    def get_entity_alias(self, entity_id: str) -> dict:
        """
        Fetch the alias (if any) currently assigned to the specified entity.

        Args:
            entity_id (str): The ID of the resource, profile, or URL.

        Returns:
            dict: 
                { "success": True, "data": AliasInfo }  # If an alias is assigned
                { "success": True, "data": None }       # If no alias assigned
                { "success": False, "error": str }      # If entity_id is not found

        Constraints:
            - The entity must exist.
            - There should be at most one alias assigned to a given entity.
        """
        if entity_id not in self.entities:
            return {"success": False, "error": "Entity does not exist"}
    
        # Search for alias assigned to this entity_id
        for alias in self.aliases.values():
            if alias["associated_entity_id"] == entity_id:
                return {"success": True, "data": alias}
    
        # No alias found for this entity
        return {"success": True, "data": None}

    def get_entity_by_id(self, entity_id: str) -> dict:
        """
        Retrieve details (EntityInfo) about a resource, profile, or URL given its entity_id.

        Args:
            entity_id (str): The unique identifier of the target entity.

        Returns:
            dict: {
                "success": True,
                "data": EntityInfo  # Entity information dict
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., entity not found)
            }

        Constraints:
            - The entity_id must exist in the entities registry.
        """
        entity = self.entities.get(entity_id)
        if entity is None:
            return { "success": False, "error": "Entity not found" }
        return { "success": True, "data": entity }

    def list_aliases_by_entity_type(self, entity_type: str) -> dict:
        """
        List every alias assigned to a specific entity type (resource, profile, url).

        Args:
            entity_type (str): The target entity type. Must be one of 'resource', 'profile', or 'url'.

        Returns:
            dict: {
                "success": True,
                "data": List[AliasInfo],  # May be empty if no matches
            }
            OR
            {
                "success": False,
                "error": str  # Description of error reason
            }

        Constraints:
            - entity_type must be exactly 'resource', 'profile', or 'url' (case-sensitive).
        """
        valid_types = {'resource', 'profile', 'url'}
        if entity_type not in valid_types:
            return {"success": False, "error": "Invalid entity_type. Must be one of 'resource', 'profile', or 'url'."}

        result = [
            alias_info for alias_info in self.aliases.values()
            if alias_info['associated_entity_type'] == entity_type
        ]
        return {"success": True, "data": result}

    def validate_alias_string_format(self, alias_string: str) -> dict:
        """
        Check if the given alias string meets platform format/character restrictions.

        Args:
            alias_string (str): The alias string to validate.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "valid": bool,    # True if the string is valid, else False
                    "reason": str     # If not valid, a brief description of why
                }
            }

        Constraints (assumed, typical):
            - Length between 3 and 32 characters inclusive
            - Allowed characters: a-z, A-Z, 0-9, underscore (_), hyphen (-)
            - Must start with a letter
            - No spaces or special characters
            - No consecutive hyphens/underscores, not start/end with hyphen/underscore
        """

        if not isinstance(alias_string, str) or len(alias_string) == 0:
            return {
                "success": True,
                "data": { "valid": False, "reason": "Alias string cannot be empty." }
            }
        pattern = getattr(self, "_validate_alias_string_format_state", None)
        if isinstance(pattern, str) and pattern:
            named_policy_patterns = {
                "standard_alphanumeric_no_spaces": r"^[A-Za-z][A-Za-z0-9]{2,31}$",
                "standard_policy": r"^[a-z][a-z0-9_-]{2,31}$",
                "standard_policy_regex_v1": r"^[a-z][a-z0-9_-]{2,31}$",
            }
            pattern = named_policy_patterns.get(pattern, pattern)
            try:
                if re.fullmatch(pattern, alias_string):
                    return {
                        "success": True,
                        "data": {"valid": True, "reason": ""}
                    }
                return {
                    "success": True,
                    "data": {"valid": False, "reason": "Alias string does not match platform policy."}
                }
            except re.error:
                pass
        if len(alias_string) < 3 or len(alias_string) > 32:
            return {
                "success": True,
                "data": { "valid": False, "reason": "Alias length must be 3-32 characters." }
            }
        if not re.match(r'^[a-zA-Z]', alias_string):
            return {
                "success": True,
                "data": { "valid": False, "reason": "Alias must start with a letter." }
            }
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', alias_string):
            return {
                "success": True,
                "data": { "valid": False, "reason": "Alias contains invalid characters." }
            }
        if (
            alias_string[0] in "-_" or
            alias_string[-1] in "-_" or
            "--" in alias_string or
            "__" in alias_string or
            "-_" in alias_string or
            "_-" in alias_string
        ):
            return {
                "success": True,
                "data": { "valid": False, "reason": "Alias cannot start/end with hyphen/underscore or have consecutive hyphens/underscores." }
            }
        return {
            "success": True,
            "data": { "valid": True, "reason": "" }
        }


    def assign_alias_to_entity(self, alias_string: str, associated_entity_id: str) -> dict:
        """
        Assign an available and valid alias to a specific entity.

        Args:
            alias_string (str): The desired alias to assign (must be unique and conform to platform policy).
            associated_entity_id (str): The ID of the entity (resource/profile/URL) to link to this alias.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Alias '<alias>' assigned to entity '<entity_id>'"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Alias string must be globally unique (not already assigned to any entity).
            - Alias string must pass any format/character restrictions.
            - The associated entity must exist in the system.
            - An alias may only be assigned to one entity (no shared assignments).
            - Only available/unassigned aliases can be assigned.

        Notes:
            - If a platform-specific format validator exists (as a method), it will be called.
            - Timestamps (date_created) are in ISO 8601 format (UTC).
        """

        # 1. Look for an existing alias record with this alias string.
        existing_alias = None
        for alias_info in self.aliases.values():
            if alias_info["alias_string"].lower() == alias_string.lower():
                existing_alias = alias_info
                break

        # 2. Validate alias string format if validator method exists
        if hasattr(self, "validate_alias_string_format"):
            validate_result = self.validate_alias_string_format(alias_string)
            if not isinstance(validate_result, dict) or not validate_result.get("success", False):
                return {"success": False, "error": "Alias string format invalid"}
            if not validate_result.get("data", {}).get("valid", False):
                return {
                    "success": False,
                    "error": validate_result.get("data", {}).get("reason", "Alias string format invalid")
                }

        # 3. Check entity existence
        entity_info = self.entities.get(associated_entity_id)
        if entity_info is None:
            return {"success": False, "error": "Associated entity does not exist"}

        # 4. If the alias already exists but is currently unassigned, reuse it in place.
        if existing_alias is not None:
            if existing_alias.get("associated_entity_id"):
                return {"success": False, "error": "Alias string is already assigned"}

            existing_alias["associated_entity_type"] = entity_info["entity_type"]
            existing_alias["associated_entity_id"] = associated_entity_id
            existing_alias["sta"] = "assigned"
            return {
                "success": True,
                "message": f"Alias '{alias_string}' assigned to entity '{associated_entity_id}'"
            }

        # 5. Assign new alias
        alias_id = str(uuid.uuid4())
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        new_alias: AliasInfo = {
            "alias_id": alias_id,
            "alias_string": alias_string,
            "associated_entity_type": entity_info["entity_type"],
            "associated_entity_id": associated_entity_id,
            "date_created": now_iso,
            "sta": "active"
        }
        self.aliases[alias_id] = new_alias

        return {
            "success": True,
            "message": f"Alias '{alias_string}' assigned to entity '{associated_entity_id}'"
        }

    def unassign_alias(self, alias_id: str) -> dict:
        """
        Remove the assignment of an alias from its associated entity.

        Args:
            alias_id (str): The unique identifier of the alias to unassign.

        Returns:
            dict: {
                "success": True,
                "message": "Alias unassigned from entity"
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Alias must exist in the system.
            - Alias must currently be assigned to an entity (associated_entity_id and associated_entity_type must be non-empty).
            - After unassignment, associated_entity_id and associated_entity_type will be set to empty strings, and 'sta' (status) set to 'unassigned'.
        """
        alias_info = self.aliases.get(alias_id)
        if alias_info is None:
            return {"success": False, "error": f"Alias with alias_id {alias_id} does not exist"}

        # Check if alias is already unassigned
        if not alias_info.get("associated_entity_type") or not alias_info.get("associated_entity_id"):
            return {"success": False, "error": "Alias is not currently assigned to any entity"}

        # Perform unassignment
        alias_info["associated_entity_type"] = ""
        alias_info["associated_entity_id"] = ""
        alias_info["sta"] = "unassigned"
        # Optionally, update the date_created or add a modified timestamp if the data model supported

        # Update the record
        self.aliases[alias_id] = alias_info

        return {"success": True, "message": "Alias unassigned from entity"}

    def update_alias_string(self, alias_id: str, new_alias_string: str) -> dict:
        """
        Modify the alias_string of an existing alias, enforcing global uniqueness 
        and format/character policy rules.

        Args:
            alias_id (str): The ID of the alias to modify.
            new_alias_string (str): The new alias string to assign.

        Returns:
            dict: 
                On success: { "success": True, "message": "Alias string updated successfully." }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - alias_id must already exist.
            - new_alias_string must be globally unique (not used by any other alias).
            - new_alias_string must pass the platform's format/character validity checks.
        """
        # Check if alias exists
        if alias_id not in self.aliases:
            return { "success": False, "error": "Alias ID does not exist." }

        # Check for alias string uniqueness among ALL aliases (ignoring the one being updated)
        for other_id, info in self.aliases.items():
            if other_id != alias_id and info["alias_string"] == new_alias_string:
                return { "success": False, "error": "Alias string already in use." }

        # Check format/character validity, assuming such a function exists
        if hasattr(self, 'validate_alias_string_format'):
            format_check = self.validate_alias_string_format(new_alias_string)
            if not (isinstance(format_check, dict) and format_check.get("success", False) and format_check.get("data", {}).get("valid", False)):
                error_message = (
                    format_check.get("data", {}).get("reason", "Alias string does not meet format requirements.")
                    if isinstance(format_check, dict) else "Alias string does not meet format requirements."
                )
                return { "success": False, "error": error_message }
    
        # All checks passed – update the alias_string and refresh status to reflect
        # the now-valid alias state.
        self.aliases[alias_id]["alias_string"] = new_alias_string
        if self.aliases[alias_id].get("associated_entity_id") and self.aliases[alias_id].get("associated_entity_type"):
            self.aliases[alias_id]["sta"] = "assigned"
        else:
            self.aliases[alias_id]["sta"] = "unassigned"
        return { "success": True, "message": "Alias string updated successfully." }

    def delete_alias(self, alias_id: str) -> dict:
        """
        Permanently remove an alias from the system.

        Args:
            alias_id (str): The unique identifier of the alias to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Alias <alias_id> deleted permanently." }
                - On failure: { "success": False, "error": "Alias not found" }

        Constraints:
            - Alias must exist in the system.
            - Only admin-level operations may invoke this (assumed by system, not checked here).
        """
        if alias_id not in self.aliases:
            return { "success": False, "error": "Alias not found" }

        del self.aliases[alias_id]
        return { "success": True, "message": f"Alias {alias_id} deleted permanently." }

    def reassign_alias_to_entity(self, alias_id: str, new_entity_id: str) -> dict:
        """
        Change an alias’s association from one entity to another, enforcing all uniqueness and assignment constraints.

        Args:
            alias_id (str): The ID of the alias to be reassigned.
            new_entity_id (str): The target entity ID to associate with the alias.

        Returns:
            dict: {
                "success": True,
                "message": "Alias reassigned from entity {old} to entity {new}"
            } on success,
            or
            {
                "success": False,
                "error": str
            } on error.

        Constraints:
            - Alias must exist.
            - New entity must exist.
            - The alias is updated to reference the new entity.
            - Alias string remains unique as there is no renaming here.
            - Each alias is always tied to exactly one entity.
        """
        alias_info = self.aliases.get(alias_id)
        if not alias_info:
            return {"success": False, "error": "Alias ID does not exist"}

        new_entity = self.entities.get(new_entity_id)
        if not new_entity:
            return {"success": False, "error": "Target entity does not exist"}

        old_entity_id = alias_info["associated_entity_id"]
        old_entity_type = alias_info["associated_entity_type"]

        # Edge: No change needed
        if old_entity_id == new_entity_id:
            return {"success": True, "message": "Alias is already associated with the target entity."}

        # Update association
        alias_info["associated_entity_id"] = new_entity_id
        alias_info["associated_entity_type"] = new_entity["entity_type"]

        # Save change
        self.aliases[alias_id] = alias_info

        return {
            "success": True,
            "message": f"Alias reassigned from entity {old_entity_id} to entity {new_entity_id}"
        }


class WebsiteAliasManagementSystem(BaseEnv):
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
            if key == "validate_alias_string_format":
                setattr(env, "_validate_alias_string_format_state", copy.deepcopy(value))
            else:
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

    def check_alias_availability(self, **kwargs):
        return self._call_inner_tool('check_alias_availability', kwargs)

    def get_alias_by_string(self, **kwargs):
        return self._call_inner_tool('get_alias_by_string', kwargs)

    def get_alias_by_id(self, **kwargs):
        return self._call_inner_tool('get_alias_by_id', kwargs)

    def list_all_aliases(self, **kwargs):
        return self._call_inner_tool('list_all_aliases', kwargs)

    def get_entity_alias(self, **kwargs):
        return self._call_inner_tool('get_entity_alias', kwargs)

    def get_entity_by_id(self, **kwargs):
        return self._call_inner_tool('get_entity_by_id', kwargs)

    def list_aliases_by_entity_type(self, **kwargs):
        return self._call_inner_tool('list_aliases_by_entity_type', kwargs)

    def validate_alias_string_format(self, **kwargs):
        return self._call_inner_tool('validate_alias_string_format', kwargs)

    def assign_alias_to_entity(self, **kwargs):
        return self._call_inner_tool('assign_alias_to_entity', kwargs)

    def unassign_alias(self, **kwargs):
        return self._call_inner_tool('unassign_alias', kwargs)

    def update_alias_string(self, **kwargs):
        return self._call_inner_tool('update_alias_string', kwargs)

    def delete_alias(self, **kwargs):
        return self._call_inner_tool('delete_alias', kwargs)

    def reassign_alias_to_entity(self, **kwargs):
        return self._call_inner_tool('reassign_alias_to_entity', kwargs)
