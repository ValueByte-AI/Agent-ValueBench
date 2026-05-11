# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class MemberProfileInfo(TypedDict):
    profile_id: str
    name: str
    gender: str
    date_of_birth: str
    religion: str
    caste: str
    marital_status: str
    education: str
    age: int
    height: int
    address: str
    contact_information: str
    profile_creation_date: str
    profile_status: str
    profile_picture: str
    occupation: str
    income: str
    family_details: str
    interests: str
    languages_spoken: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing an online matrimonial portal database.
        """

        # Member profiles: {profile_id: MemberProfileInfo}
        self.member_profiles: Dict[str, MemberProfileInfo] = {}
        
        # Constraints:
        # - profile_id must be unique for each member.
        # - Only active (profile_status = 'active') profiles included in search/filter results unless otherwise specified.
        # - Data used in search filters (religion, caste, marital_status, education, age, height) must be present in each profile for inclusion in results.
        # - Sensitive information (contact_information, address) may be access-controlled based on user privileges.

    def filter_profiles(
        self,
        religion: str = None,
        caste: str = None,
        marital_status: str = None,
        education: str = None,
        age: int = None,
        height: int = None
    ) -> dict:
        """
        Retrieve member profiles matching provided filters. Only includes profiles with
        profile_status == "active" and all required filter data present.

        Args:
            religion (str, optional): Religion filter.
            caste (str, optional): Caste filter.
            marital_status (str, optional): Marital status filter.
            education (str, optional): Education filter.
            age (int, optional): Age filter (exact match).
            height (int, optional): Height filter (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[MemberProfileInfo]  # List of matching profiles
            }

        Constraints:
            - Only profiles with profile_status == "active" are included.
            - All fields used in filters (religion, caste, marital_status, education, age, height)
              must be present (non-None) in the profile for a match.

        Notes:
            - Ignore profiles missing any required filter data for active search.
            - If no filter is supplied, will return all active profiles with all required fields present.
        """
        filters = {
            "religion": religion,
            "caste": caste,
            "marital_status": marital_status,
            "education": education,
            "age": age,
            "height": height
        }

        result = []
        for profile in self.member_profiles.values():
            # Must be active
            if profile.get("profile_status") != "active":
                continue

            # Profile must have all required search fields present (not None/not missing)
            if any(
                profile.get(field) is None for field in
                ["religion", "caste", "marital_status", "education", "age", "height"]
            ):
                continue

            # For each provided filter, must match exactly
            match = True
            for field, value in filters.items():
                if value is not None:
                    if profile.get(field) != value:
                        match = False
                        break
            if match:
                result.append(profile)

        return { "success": True, "data": result }

    def get_profile_by_id(self, profile_id: str) -> dict:
        """
        Retrieve the detailed information for a single profile specified by profile_id.

        Args:
            profile_id (str): The unique identifier for the member profile.

        Returns:
            dict:
                - On success: { "success": True, "data": MemberProfileInfo }
                - On failure: { "success": False, "error": "Profile not found" }

        Constraints:
            - Returns all fields for the given profile_id if found (including sensitive fields).
            - Returns error if profile_id does not exist in the database.
        """
        profile_info = self.member_profiles.get(profile_id)
        if profile_info is None:
            return { "success": False, "error": "Profile not found" }
        return { "success": True, "data": profile_info }

    def get_profile_public_details(self, profile_id: str) -> dict:
        """
        Retrieve only public (non-sensitive) fields for a specified profile_id.

        Args:
            profile_id (str): Unique profile ID to fetch.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": {public_fields}}
                - On failure:
                    {"success": False, "error": "Profile not found"}

        Constraints:
            - Only public (non-sensitive) fields are included in the result.
              Sensitive fields: 'address', 'contact_information'.
            - profile_id must exist in the database.
        """
        if profile_id not in self.member_profiles:
            return {"success": False, "error": "Profile not found"}
        profile = self.member_profiles[profile_id]
        sensitive_fields = {'address', 'contact_information'}
        public_data = {k: v for k, v in profile.items() if k not in sensitive_fields}
        return {"success": True, "data": public_data}

    def get_profile_sensitive_details(self, profile_id: str, has_sensitive_access: bool) -> dict:
        """
        Retrieve sensitive fields (address and contact_information) for the specified profile,
        subject to access control.

        Args:
            profile_id (str): The unique ID of the member profile to query.
            has_sensitive_access (bool): Whether the requester has privilege to access
                                         sensitive information (address/contact_info).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "address": str,
                            "contact_information": str
                        }
                    }
                - On failure (profile not found, insufficient privilege):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The profile must exist.
            - The requester must have access privileges (has_sensitive_access).
            - If privileges are insufficient, sensitive data must not be returned.
        """
        profile = self.member_profiles.get(profile_id)
        if not profile:
            return { "success": False, "error": "Profile does not exist" }

        if not has_sensitive_access:
            return { "success": False, "error": "Insufficient privilege to view sensitive details" }

        result = {
            "address": profile.get("address", ""),
            "contact_information": profile.get("contact_information", "")
        }
        return { "success": True, "data": result }

    def check_profile_status(self, profile_id: str) -> dict:
        """
        Query the current status ('active', 'inactive', etc.) of a member profile by profile_id.

        Args:
            profile_id (str): The unique identifier for the member profile.

        Returns:
            dict: 
                If success: {
                    "success": True,
                    "data": {
                        "profile_id": <profile_id>,
                        "profile_status": <str>
                    }
                }
                If not found: {
                    "success": False,
                    "error": "Profile not found"
                }

        Constraints:
            - profile_id must exist in the database.
            - No privilege checks required for status (non-sensitive).
        """
        profile = self.member_profiles.get(profile_id)
        if profile is None:
            return { "success": False, "error": "Profile not found" }

        return {
            "success": True,
            "data": {
                "profile_id": profile_id,
                "profile_status": profile["profile_status"]
            }
        }

    def list_all_active_profiles(self) -> dict:
        """
        Retrieve all active member profiles (where profile_status == 'active').

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[MemberProfileInfo],  # List of all active profiles (may be empty)
                }

        Constraints:
            - Only profiles with profile_status == 'active' are included.
            - Profiles missing 'profile_status' or with a different status are ignored.

        Notes:
            - No filter on privileges or data completeness.
            - Returns all fields, including potentially sensitive ones.
        """
        active_profiles = [
            profile for profile in self.member_profiles.values()
            if profile.get("profile_status", "") == "active"
        ]
        return {
            "success": True,
            "data": active_profiles
        }

    def list_profiles_by_status(self, status: str) -> dict:
        """
        Lists all profiles with the specified status.

        Args:
            status (str): The profile_status to filter by (e.g., 'active', 'inactive', 'suspended').

        Returns:
            dict: {
                "success": True,
                "data": List[MemberProfileInfo]  # List of profiles with the given status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If input status is missing or empty
            }

        Constraints:
            - Returns all profiles matching the specified status.
            - If no such profiles exist, returns empty list with success.
            - If status is not provided or is blank, returns error.
        """
        if not status or not isinstance(status, str):
            return { "success": False, "error": "Profile status to filter by must be a non-empty string." }

        result = [
            profile for profile in self.member_profiles.values()
            if profile.get("profile_status") == status
        ]

        return { "success": True, "data": result }

    def check_profile_data_completeness(self, profile_id: str) -> dict:
        """
        Verify if a given member profile contains all attribute fields required for search filtering.

        Args:
            profile_id (str): Unique identifier of the member profile.

        Returns:
            dict:
                - If profile exists:
                    {
                        "success": True,
                        "complete": bool,  # True if all required fields present and populated, else False
                        "missing_fields": List[str]  # List of missing or empty/None required fields (only if incomplete)
                    }
                - If profile does not exist:
                    {
                        "success": False,
                        "error": "Profile not found"
                    }
        Constraints:
            - Required fields: religion, caste, marital_status, education, age, height
            - Fields must be present in profile and have valid (non-empty/non-None) values.
        """
        # Required fields
        required_fields = ["religion", "caste", "marital_status", "education", "age", "height"]
    
        profile = self.member_profiles.get(profile_id)
        if profile is None:
            return {"success": False, "error": "Profile not found"}
    
        missing_fields = []
        for field in required_fields:
            value = profile.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing_fields.append(field)
    
        if missing_fields:
            return {
                "success": True,
                "complete": False,
                "missing_fields": missing_fields
            }
        else:
            return {
                "success": True,
                "complete": True,
                "missing_fields": []
            }

    def check_user_privileges(self, user_context: dict) -> dict:
        """
        Determine whether the current user/requestor has sufficient access rights to view 
        sensitive profile information.

        Args:
            user_context (dict): Context object with user privilege info, must include at least a 'role' key.

        Returns:
            dict:
                If input valid: {
                    "success": True,
                    "data": { "has_privilege": bool }
                }
                On bad input: {
                    "success": False,
                    "error": str
                }
            
        Constraints:
            - If user_context missing, or 'role' not present/unknown, privilege is denied (False).
            - Only users with roles in ['admin', 'privileged'] are allowed to view sensitive info.
        """
        if not isinstance(user_context, dict):
            return { "success": False, "error": "Invalid or missing user context." }
        role = user_context.get('role')
        if role is None:
            return { "success": False, "error": "No role information provided in user context." }

        privileged_roles = ['admin', 'privileged']
        has_privilege = role in privileged_roles

        return { "success": True, "data": { "has_privilege": has_privilege } }

    def create_profile(self, profile_data: dict) -> dict:
        """
        Add a new member profile to the database, ensuring the profile_id is unique
        and that all required fields are present for inclusion in search/filter results.

        Args:
            profile_data (dict): Dictionary with keys matching MemberProfileInfo fields.

        Returns:
            dict: {
                "success": True,
                "message": "Profile <profile_id> successfully created."
            }
            or
            {
                "success": False,
                "error": <reason>,
            }

        Constraints:
            - profile_id must be unique.
            - All filter-related fields (religion, caste, marital_status, education, age, height) must be present.
            - All fields in MemberProfileInfo should be present (required for correct profile creation).
        """
        required_fields = [
            "profile_id", "name", "gender", "date_of_birth", "religion", "caste",
            "marital_status", "education", "age", "height", "address", 
            "contact_information", "profile_creation_date", "profile_status",
            "profile_picture", "occupation", "income", "family_details",
            "interests", "languages_spoken"
        ]

        # Check all required fields are present
        missing = [k for k in required_fields if k not in profile_data]
        if missing:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing)}"
            }

        profile_id = profile_data["profile_id"]

        # Check for uniqueness
        if profile_id in self.member_profiles:
            return {
                "success": False,
                "error": f"profile_id '{profile_id}' already exists"
            }
    
        # Check data types for filter fields
        filter_fields = ["religion", "caste", "marital_status", "education", "age", "height"]
        filter_types = {
            "religion": str, "caste": str, "marital_status": str,
            "education": str, "age": int, "height": int,
        }
        for field in filter_fields:
            if field not in profile_data:
                return {
                    "success": False,
                    "error": f"Filter field '{field}' is missing"
                }
            expected_type = filter_types[field]
            if not isinstance(profile_data[field], expected_type):
                return {
                    "success": False,
                    "error": f"Field '{field}' must be of type {expected_type.__name__}"
                }

        # Store the new profile (copying only the expected fields)
        new_profile = {k: profile_data[k] for k in required_fields}
        self.member_profiles[profile_id] = new_profile

        return {
            "success": True,
            "message": f"Profile '{profile_id}' successfully created."
        }

    def update_profile_details(self, profile_id: str, updated_fields: dict) -> dict:
        """
        Modify one or more permissible fields of an existing profile.

        Args:
            profile_id (str): The unique profile identifier to update.
            updated_fields (dict): Dictionary with field names and new values to be set.

        Returns:
            dict: {
                "success": True,
                "message": "Profile <profile_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - profile_id cannot be changed.
            - Only valid fields (in MemberProfileInfo, except profile_id) may be updated.
            - profile_id must exist.
        """
        if profile_id not in self.member_profiles:
            return { "success": False, "error": f"Profile ID '{profile_id}' does not exist." }

        if not updated_fields or not isinstance(updated_fields, dict):
            return { "success": False, "error": "No update fields provided or invalid input." }

        allowed_fields = set(self.member_profiles[profile_id].keys()) - {'profile_id'}
        invalid_fields = [k for k in updated_fields if k not in allowed_fields]

        if invalid_fields:
            return { "success": False, "error": f"Invalid or unmodifiable field(s): {', '.join(invalid_fields)}" }

        for k, v in updated_fields.items():
            self.member_profiles[profile_id][k] = v

        return { "success": True, "message": f"Profile {profile_id} updated successfully." }

    def set_profile_status(self, profile_id: str, new_status: str) -> dict:
        """
        Change the status of a profile (activate, deactivate, suspend, etc.).

        Args:
            profile_id (str): Unique identifier of the member profile.
            new_status (str): The new profile status (e.g., 'active', 'inactive', 'suspended').

        Returns:
            dict:
                On success: { "success": True, "message": "Profile status updated to <new_status>." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The specified profile_id must exist in the system.
            - 'new_status' can be any string.
        """
        profile = self.member_profiles.get(profile_id)
        if profile is None:
            return { "success": False, "error": "Profile ID does not exist." }
    
        if profile['profile_status'] == new_status:
            return { "success": False, "error": f"Profile status is already '{new_status}'." }
    
        profile['profile_status'] = new_status
        return { "success": True, "message": f"Profile status updated to '{new_status}'." }

    def delete_profile(self, profile_id: str) -> dict:
        """
        Remove a member profile from the database by profile_id.

        Args:
            profile_id (str): The unique profile ID to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Profile <profile_id> deleted."
                    }
                On failure (e.g. not found):
                    {
                        "success": False,
                        "error": "Profile not found."
                    }

        Constraints:
            - profile_id must exist in the database.
            - (Privilege check not implemented here.)
        """
        if profile_id not in self.member_profiles:
            return {
                "success": False,
                "error": "Profile not found."
            }
        del self.member_profiles[profile_id]
        return {
            "success": True,
            "message": f"Profile {profile_id} deleted."
        }

    def update_profile_picture(self, profile_id: str, profile_picture: str) -> dict:
        """
        Change or set the profile picture for a member.

        Args:
            profile_id (str): Unique identifier of the member profile.
            profile_picture (str): New value for the profile picture (path/URL/ID).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Profile picture updated for profile_id <id>" }
                - On failure: { "success": False, "error": "reason for failure" }

        Constraints:
            - profile_id must exist in the database.
            - No status or privilege constraint applies for this operation.
        """
        if profile_id not in self.member_profiles:
            return { "success": False, "error": "Profile ID does not exist" }

        self.member_profiles[profile_id]["profile_picture"] = profile_picture
        return { "success": True, "message": f"Profile picture updated for profile_id {profile_id}" }

    def update_sensitive_information(
        self,
        profile_id: str,
        requester: dict,
        address: str = None,
        contact_information: str = None
    ) -> dict:
        """
        Update sensitive information ('address', 'contact_information') of a member profile.

        Args:
            profile_id (str): Unique identifier for the profile to be updated.
            requester (dict): Information about the requester, must include a boolean field 'can_edit_sensitive_info'.
            address (str, optional): New address to set (if updating).
            contact_information (str, optional): New contact information to set (if updating).

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "Sensitive information updated for profile_id XYZ."
                    }
                Failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Profile must exist.
            - At least one of (address, contact_information) must be provided.
            - Requester must have 'can_edit_sensitive_info' == True.
        """
        if profile_id not in self.member_profiles:
            return {"success": False, "error": "Profile does not exist."}

        if not (address is not None or contact_information is not None):
            return {"success": False, "error": "No sensitive information provided for update."}

        if not (isinstance(requester, dict) and requester.get("can_edit_sensitive_info", False)):
            return {"success": False, "error": "Insufficient privileges to update sensitive information."}

        updated = False
        if address is not None:
            self.member_profiles[profile_id]["address"] = address
            updated = True
        if contact_information is not None:
            self.member_profiles[profile_id]["contact_information"] = contact_information
            updated = True

        if not updated:
            # Redundant but defensive
            return {"success": False, "error": "No update performed on sensitive fields."}

        return {
            "success": True,
            "message": f"Sensitive information updated for profile_id {profile_id}."
        }

    def add_profile_interest(self, profile_id: str, interest: str) -> dict:
        """
        Add an interest or hobby to the specified member profile’s interests list.

        Args:
            profile_id (str): The unique identifier of the member profile.
            interest (str): The interest/hobby to add.

        Returns:
            dict: {
                "success": True,
                "message": "Interest added to profile."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - profile_id must exist in the system.
            - interest must not be empty/blank and must not already be present in the interests list.
            - The interests attribute is a comma-separated string with no duplicate interests.
        """
        if profile_id not in self.member_profiles:
            return {"success": False, "error": "Profile does not exist."}

        # Normalize and validate the interest string
        new_interest = interest.strip()
        if not new_interest:
            return {"success": False, "error": "Interest cannot be empty."}

        profile = self.member_profiles[profile_id]
        current_interests = profile.get("interests", "")

        # Parse the interests into a list, removing empty entries and normalizing whitespace
        interests_list = [s.strip() for s in current_interests.split(",") if s.strip()]
    
        # Check if the interest already exists (case-insensitive)
        if any(new_interest.lower() == i.lower() for i in interests_list):
            return {"success": False, "error": "Interest already present in profile."}

        # Add the new interest
        interests_list.append(new_interest)
        profile["interests"] = ", ".join(interests_list)

        return {"success": True, "message": "Interest added to profile."}

    def remove_profile_interest(self, profile_id: str, interest: str) -> dict:
        """
        Remove a specified interest or hobby from a member profile.

        Args:
            profile_id (str): The unique identifier for the member profile.
            interest (str): The interest or hobby to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Interest removed from profile." }
                On failure:
                    { "success": False, "error": "Profile not found." }
                    OR
                    { "success": False, "error": "Interest not present in profile." }

        Constraints:
            - Profile must exist.
            - Interest must be present in the profile's interests.
            - Interests are comma-separated in the 'interests' attribute (may contain whitespace).
        """
        profile = self.member_profiles.get(profile_id)
        if not profile:
            return { "success": False, "error": "Profile not found." }

        interests_str = profile.get("interests", "")
        # Split/strip
        raw_interests = [i.strip() for i in interests_str.split(",") if i.strip()]
        if interest not in raw_interests:
            return { "success": False, "error": "Interest not present in profile." }

        # Remove interest
        new_interests = [i for i in raw_interests if i != interest]
        profile["interests"] = ", ".join(new_interests)

        # Save back
        self.member_profiles[profile_id] = profile

        return { "success": True, "message": "Interest removed from profile." }

    def update_family_details(self, profile_id: str, family_details: str) -> dict:
        """
        Edit (update) the family_details attribute of a member profile.

        Args:
            profile_id (str): Unique identifier of the member profile to update.
            family_details (str): The new family details information.

        Returns:
            dict: {
                "success": True,
                "message": "Family details updated for profile <profile_id>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - profile_id must exist in the database.
            - family_details should be a non-empty string.
        """
        if profile_id not in self.member_profiles:
            return {"success": False, "error": "Profile ID does not exist."}
        if not isinstance(family_details, str) or family_details.strip() == "":
            return {"success": False, "error": "family_details value must be a non-empty string."}
    
        self.member_profiles[profile_id]["family_details"] = family_details.strip()
        return {
            "success": True,
            "message": f"Family details updated for profile {profile_id}."
        }


class MatrimonialPortalDatabase(BaseEnv):
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

    def filter_profiles(self, **kwargs):
        return self._call_inner_tool('filter_profiles', kwargs)

    def get_profile_by_id(self, **kwargs):
        return self._call_inner_tool('get_profile_by_id', kwargs)

    def get_profile_public_details(self, **kwargs):
        return self._call_inner_tool('get_profile_public_details', kwargs)

    def get_profile_sensitive_details(self, **kwargs):
        return self._call_inner_tool('get_profile_sensitive_details', kwargs)

    def check_profile_status(self, **kwargs):
        return self._call_inner_tool('check_profile_status', kwargs)

    def list_all_active_profiles(self, **kwargs):
        return self._call_inner_tool('list_all_active_profiles', kwargs)

    def list_profiles_by_status(self, **kwargs):
        return self._call_inner_tool('list_profiles_by_status', kwargs)

    def check_profile_data_completeness(self, **kwargs):
        return self._call_inner_tool('check_profile_data_completeness', kwargs)

    def check_user_privileges(self, **kwargs):
        return self._call_inner_tool('check_user_privileges', kwargs)

    def create_profile(self, **kwargs):
        return self._call_inner_tool('create_profile', kwargs)

    def update_profile_details(self, **kwargs):
        return self._call_inner_tool('update_profile_details', kwargs)

    def set_profile_status(self, **kwargs):
        return self._call_inner_tool('set_profile_status', kwargs)

    def delete_profile(self, **kwargs):
        return self._call_inner_tool('delete_profile', kwargs)

    def update_profile_picture(self, **kwargs):
        return self._call_inner_tool('update_profile_picture', kwargs)

    def update_sensitive_information(self, **kwargs):
        return self._call_inner_tool('update_sensitive_information', kwargs)

    def add_profile_interest(self, **kwargs):
        return self._call_inner_tool('add_profile_interest', kwargs)

    def remove_profile_interest(self, **kwargs):
        return self._call_inner_tool('remove_profile_interest', kwargs)

    def update_family_details(self, **kwargs):
        return self._call_inner_tool('update_family_details', kwargs)

