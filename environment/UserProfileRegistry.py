# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class UserProfileInfo(TypedDict):
    _id: str
    name: str
    gender: str
    age: int
    contact_details: str
    demographic_a: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        User profile registry environment state.
        """

        # UserProfiles: {_id: UserProfileInfo}
        self.user_profiles: Dict[str, UserProfileInfo] = {}

        # Constraints:
        # - Each user_id (_id) must be unique in user_profiles dict
        # - All profiles must have non-null _id and required fields
        # - 'age' must be a non-negative integer

    def get_user_profile_by_id(self, _id: str) -> dict:
        """
        Retrieve the entire user profile dictionary for a given _id.

        Args:
            _id (str): The unique user ID to look up.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": UserProfileInfo
                  }
                - On failure: {
                    "success": False,
                    "error": "User profile not found"
                  }

        Constraints:
            - _id must exist in the registry.
        """
        profile = self.user_profiles.get(_id)
        if not profile:
            return {"success": False, "error": "User profile not found"}
        return {"success": True, "data": profile}

    def get_user_attributes(self, user_ids: list[str], attributes: list[str]) -> dict:
        """
        Retrieve specific attributes for one or more user profiles given their IDs.

        Args:
            user_ids (list[str]): List of user profile IDs to look up.
            attributes (list[str]): List of attribute names to retrieve (e.g., ['name', 'gender']).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            user_id1: {attr1: value, attr2: value, ...},
                            user_id2: {...},
                            ...
                        }
                    }
                - On error (missing users or invalid attributes):
                    {
                        "success": False,
                        "error": "Reason"
                    }

        Constraints:
            - All user IDs must exist in the registry.
            - All requested attributes must be valid UserProfile attributes.
        """
        allowed_attrs = set(UserProfileInfo.__annotations__.keys())

        # Validate attributes requested
        invalid_attrs = [attr for attr in attributes if attr not in allowed_attrs]
        if invalid_attrs:
            return {"success": False, "error": f"Invalid attribute(s): {', '.join(invalid_attrs)}"}

        # Validate user IDs
        missing_ids = [uid for uid in user_ids if uid not in self.user_profiles]
        if missing_ids:
            return {"success": False, "error": f"User(s) not found: {', '.join(missing_ids)}"}

        # Gather results
        result = {}
        for uid in user_ids:
            profile = self.user_profiles[uid]
            result[uid] = {attr: profile[attr] for attr in attributes}

        return {"success": True, "data": result}

    def list_all_user_profiles(self) -> dict:
        """
        Retrieve a list of all user profile records.

        Returns:
            dict: {
                "success": True,
                "data": List[UserProfileInfo],  # All user profile dictionaries (may be empty if none exist)
            }
        """
        profiles = list(self.user_profiles.values())
        return { "success": True, "data": profiles }

    def search_user_profiles_by_attribute(self, attribute: str, value) -> dict:
        """
        Find user profiles where a given attribute matches a supplied value.

        Args:
            attribute (str): The profile field to filter on (e.g., 'gender', 'age').
            value: The value to match for the given attribute (type depends on attribute).

        Returns:
            dict: {
                "success": True,
                "data": List[UserProfileInfo]  # May be empty if no matches
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Attribute gender does not exist"
            }

        Constraints:
            - Only existing fields in UserProfileInfo are valid for filtering.
        """

        valid_attributes = {"_id", "name", "gender", "age", "contact_details", "demographic_a"}
        if attribute not in valid_attributes:
            return {
                "success": False,
                "error": f"Attribute '{attribute}' is not valid"
            }

        result = [
            profile for profile in self.user_profiles.values()
            if attribute in profile and profile[attribute] == value
        ]

        return {
            "success": True,
            "data": result
        }

    def add_user_profile(
        self,
        _id: str,
        name: str,
        gender: str,
        age: int,
        contact_details: str,
        demographic_a: str
    ) -> dict:
        """
        Create and add a new user profile with required non-null fields, enforcing uniqueness of _id.

        Args:
            _id (str): Unique user identifier (must not already exist and must be non-null).
            name (str): User's name (must be non-null).
            gender (str): User's gender (must be non-null).
            age (int): User's age (must be a non-negative integer).
            contact_details (str): Contact information (must be non-null).
            demographic_a (str): Demographic attribute (must be non-null).

        Returns:
            dict: {
                "success": True,
                "message": "User profile added successfully."
            }
            or
            {
                "success": False,
                "error": "<error description>"
            }

        Constraints:
            - _id must be unique (cannot already exist).
            - All fields must be non-null (i.e. not None).
            - age must be a non-negative integer.
        """
        # Check all required fields are provided and non-null/non-empty
        required_fields = {
            "_id": _id,
            "name": name,
            "gender": gender,
            "age": age,
            "contact_details": contact_details,
            "demographic_a": demographic_a,
        }
        for field, value in required_fields.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return {"success": False, "error": f"Field '{field}' is required and cannot be null or empty."}

        # Check age validity
        if not isinstance(age, int) or age < 0:
            return {"success": False, "error": "Age must be a non-negative integer."}

        # Check uniqueness of _id
        if _id in self.user_profiles:
            return {"success": False, "error": "A user profile with this _id already exists."}

        # Add profile
        profile: UserProfileInfo = {
            "_id": _id,
            "name": name,
            "gender": gender,
            "age": age,
            "contact_details": contact_details,
            "demographic_a": demographic_a
        }
        self.user_profiles[_id] = profile
        return {"success": True, "message": "User profile added successfully."}

    def update_user_profile(self, _id: str, update_fields: dict) -> dict:
        """
        Update one or more attributes of a user profile identified by _id.
        Only valid fields ("name", "gender", "age", "contact_details", "demographic_a")
        can be updated. If "age" is supplied, it must be a non-negative integer.
        "_id" cannot be updated by this operation.

        Args:
            _id (str): The user ID of the profile to update.
            update_fields (dict): Mapping of attributes to update and their new values.

        Returns:
            dict: 
                On success: { "success": True, "message": "User profile updated successfully" }
                On failure: { "success": False, "error": <reason> }
        """
        if _id not in self.user_profiles:
            return { "success": False, "error": "User ID does not exist" }
        if not isinstance(update_fields, dict) or not update_fields:
            return { "success": True, "message": "No attributes updated" }

        profile = self.user_profiles[_id]
        valid_fields = {"name", "gender", "age", "contact_details", "demographic_a"}

        for key, value in update_fields.items():
            if key == "_id":
                return { "success": False, "error": "Cannot update user ID (_id) via this operation" }
            if key not in valid_fields:
                return { "success": False, "error": f"Invalid attribute: {key}" }
            if key == "age":
                if not isinstance(value, int) or value < 0:
                    return { "success": False, "error": "Invalid value for age: must be non-negative integer" }

        # Passed validation, perform update
        for key, value in update_fields.items():
            profile[key] = value

        self.user_profiles[_id] = profile
        return { "success": True, "message": "User profile updated successfully" }

    def delete_user_profile(self, _id: str) -> dict:
        """
        Remove a user profile record identified by _id from the registry.

        Args:
            _id (str): The unique identifier for the user profile to be removed.

        Returns:
            dict: 
                - If _id exists: { "success": True, "message": "User profile with _id '<_id>' deleted." }
                - If _id does not exist: { "success": False, "error": "User profile with _id '<_id>' does not exist." }

        Constraints:
            - Will only delete an existing user profile.
            - No deletion occurs if the user profile does not exist.
        """
        if _id not in self.user_profiles:
            return { "success": False, "error": f"User profile with _id '{_id}' does not exist." }
        del self.user_profiles[_id]
        return { "success": True, "message": f"User profile with _id '{_id}' deleted." }

    def validate_user_profile(self, profile: dict) -> dict:
        """
        Validates the provided user profile data for required fields and value constraints.

        Args:
            profile (dict): User profile data (should contain _id, name, gender, age, contact_details, demographic_a).

        Returns:
            dict:
                - {"success": True, "message": "Profile is valid"} if all constraints are satisfied
                - {"success": False, "error": <description>} otherwise

        Constraints:
            - All required fields must be present and not None or empty (str).
            - _id must be a non-empty string.
            - age must be a non-negative integer.
        """
        required_fields = ['_id', 'name', 'gender', 'age', 'contact_details', 'demographic_a']
        for field in required_fields:
            if field not in profile:
                return {"success": False, "error": f"Missing required field: {field}"}
            if profile[field] is None:
                return {"success": False, "error": f"Field '{field}' cannot be None"}
            if isinstance(profile[field], str) and not profile[field].strip():
                return {"success": False, "error": f"Field '{field}' cannot be empty string"}
        # _id check
        if not isinstance(profile['_id'], str):
            return {"success": False, "error": "Field '_id' must be a string"}
        if not profile['_id'].strip():
            return {"success": False, "error": "Field '_id' cannot be empty string"}
        # Age check
        if not isinstance(profile['age'], int):
            return {"success": False, "error": "Field 'age' must be an integer"}
        if profile['age'] < 0:
            return {"success": False, "error": "Field 'age' must be a non-negative integer"}
        return {"success": True, "message": "Profile is valid"}

    def change_user_id(self, old_id: str, new_id: str) -> dict:
        """
        Change a user's _id, ensuring the new ID is unique and not null.

        Args:
            old_id (str): The current user ID to change from.
            new_id (str): The new user ID to assign.

        Returns:
            dict: 
                On success: { "success": True, "message": "User ID changed from <old_id> to <new_id>" }
                On failure: { "success": False, "error": "<error message>" }
    
        Constraints:
            - old_id must exist in user_profiles.
            - new_id must not exist in user_profiles and must not be null or empty.
        """
        if old_id not in self.user_profiles:
            return { "success": False, "error": "Old user ID does not exist" }
        if not new_id or not isinstance(new_id, str) or new_id.strip() == "":
            return { "success": False, "error": "New user ID must be a non-empty string" }
        if new_id in self.user_profiles:
            return { "success": False, "error": "New user ID already exists" }

        profile = self.user_profiles.pop(old_id)
        profile["_id"] = new_id
        self.user_profiles[new_id] = profile

        return { "success": True, "message": f"User ID changed from {old_id} to {new_id}" }


class UserProfileRegistry(BaseEnv):
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

    def get_user_profile_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_profile_by_id', kwargs)

    def get_user_attributes(self, **kwargs):
        return self._call_inner_tool('get_user_attributes', kwargs)

    def list_all_user_profiles(self, **kwargs):
        return self._call_inner_tool('list_all_user_profiles', kwargs)

    def search_user_profiles_by_attribute(self, **kwargs):
        return self._call_inner_tool('search_user_profiles_by_attribute', kwargs)

    def add_user_profile(self, **kwargs):
        return self._call_inner_tool('add_user_profile', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def delete_user_profile(self, **kwargs):
        return self._call_inner_tool('delete_user_profile', kwargs)

    def validate_user_profile(self, **kwargs):
        return self._call_inner_tool('validate_user_profile', kwargs)

    def change_user_id(self, **kwargs):
        return self._call_inner_tool('change_user_id', kwargs)

