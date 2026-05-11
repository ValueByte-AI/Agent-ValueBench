# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict, Any



class PhoneNumberInfo(TypedDict):
    number: str
    country_code: str
    status: str  # e.g., 'available', 'allocated'
    metadata: Dict[str, Any]
    allocated_to_organization_id: Optional[str]  # None if not allocated

class CountryInfo(TypedDict):
    country_code: str
    country_name: str

class OrganizationInfo(TypedDict):
    organization_id: str
    organization_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Represents the virtual phone number management system state.
        """

        # Phone numbers: {number: PhoneNumberInfo}
        # Maps a phone number string to its metadata, country linkage, allocation, etc.
        self.phone_numbers: Dict[str, PhoneNumberInfo] = {}

        # Countries: {country_code: CountryInfo}
        # Maps a unique country code to its country data.
        self.countries: Dict[str, CountryInfo] = {}

        # Organizations: {organization_id: OrganizationInfo}
        # Maps an organization ID to its descriptive data.
        self.organizations: Dict[str, OrganizationInfo] = {}

        # Constraints:
        # - Only phone numbers with status="available" may be provisioned or displayed as available.
        # - Each phone number must be associated with a valid country_code.
        # - Allocating a number to an organization updates its status and allocated_to_organization_id.
        # - Country codes must be unique per country.

    def _resolve_phone_number_key(self, number: str) -> Optional[str]:
        """
        Resolve a user-facing phone number string to the backing inventory key.

        Most cases use the phone number string itself as the inventory key, but a
        few store records under an internal ID while exposing the real phone
        number via the `number` field in tool outputs. Number-oriented tools
        should accept either form.
        """
        if number in self.phone_numbers:
            return number

        for key, phone_info in self.phone_numbers.items():
            if phone_info.get("number") == number:
                return key

        return None

    def list_countries(self) -> dict:
        """
        Retrieve the list of all countries with their unique country codes and names.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CountryInfo],  # Each with 'country_code' and 'country_name'.
            }

        Constraints:
            - No constraints directly relevant; if no countries exist, data=[].
        """
        countries_list = list(self.countries.values())
        return { "success": True, "data": countries_list }

    def get_country_by_code(self, country_code: str) -> dict:
        """
        Retrieve the country name and metadata (country_code and country_name)
        for a given country code.

        Args:
            country_code (str): The country code to query.

        Returns:
            dict: {
                "success": True,
                "data": CountryInfo,  # Includes country_code and country_name
            }
            or
            {
                "success": False,
                "error": str  # Description of why lookup failed
            }

        Constraints:
            - country_code must exist in the system.
        """
        country = self.countries.get(country_code)
        if not country:
            return { "success": False, "error": "Country code not found" }
        return { "success": True, "data": country }

    def list_available_phone_numbers(self) -> dict:
        """
        Retrieve a list of all available phone numbers (with metadata) across all countries.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PhoneNumberInfo]  # may be an empty list if none available
            }

        Constraints:
            - Only phone numbers with status == "available" are included in the output.
        """
        available_numbers = [
            pn for pn in self.phone_numbers.values()
            if pn["status"] == "available"
        ]
        return {"success": True, "data": available_numbers}

    def list_available_numbers_by_country(self, country_code: str) -> dict:
        """
        Retrieve all available phone numbers for a specific country code.

        Args:
            country_code (str): The country code to filter phone numbers by.

        Returns:
            dict: {
                "success": True,
                "data": List[PhoneNumberInfo]  # List of available numbers for the country (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., country code does not exist
            }

        Constraints:
            - Only phone numbers with status="available" are included.
            - The country_code must exist in the countries registry.
        """
        if country_code not in self.countries:
            return { "success": False, "error": "Country code does not exist" }
    
        result = [
            pn_info for pn_info in self.phone_numbers.values()
            if pn_info["country_code"] == country_code and pn_info["status"] == "available"
        ]
        return { "success": True, "data": result }

    def get_phone_number_info(self, number: str) -> dict:
        """
        Get detailed information for a specific phone number, including:
        - Full phone number metadata.
        - Associated country info (country_code, country_name).
        - If allocated, organization info (organization_id, organization_name).

        Args:
            number (str): The phone number identifier to query. The platform accepts
                either the inventory key or the displayed phone number string.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "phone_number": PhoneNumberInfo,
                    "country": CountryInfo or None,
                    "organization": OrganizationInfo or None
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The phone number must exist in the inventory.
            - Country/organization enrichment info returned as None if not found.
        """
        phone_key = self._resolve_phone_number_key(number)
        if not phone_key:
            return {"success": False, "error": "Phone number does not exist"}

        phone_info = self.phone_numbers[phone_key]

        # Get country info (may be None if data inconsistent)
        country_info = self.countries.get(phone_info["country_code"])

        # Get organization info if allocated
        org_info = None
        org_id = phone_info.get("allocated_to_organization_id")
        if org_id is not None:
            org_info = self.organizations.get(org_id)

        return {
            "success": True,
            "data": {
                "phone_number": phone_info,
                "country": country_info,
                "organization": org_info
            }
        }

    def list_organizations(self) -> dict:
        """
        Retrieve all organizations registered in the platform.

        Args:
            None

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[OrganizationInfo]  # May be empty if no organizations
                    }
        """
        organizations_list = list(self.organizations.values())
        return { "success": True, "data": organizations_list }

    def get_organization_info(self, organization_id: str) -> dict:
        """
        Retrieve profile and identifying information for a specific organization.

        Args:
            organization_id (str): The unique identifier of the organization.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": OrganizationInfo plus an "allocated_phone_numbers"
                        list containing the currently assigned phone number strings
                        for that organization.
                }
                On failure: {
                    "success": False,
                    "error": str  # Error message if the organization is not found
                }
        Constraints:
            - The organization_id must exist in the platform.
        """
        org_info = self.organizations.get(organization_id)
        if org_info is None:
            return {
                "success": False,
                "error": "Organization does not exist"
            }

        allocated_phone_numbers = sorted(
            phone_info["number"]
            for phone_info in self.phone_numbers.values()
            if phone_info.get("allocated_to_organization_id") == organization_id
        )
        enriched_info = copy.deepcopy(org_info)
        enriched_info["allocated_phone_numbers"] = allocated_phone_numbers

        return {
            "success": True,
            "data": enriched_info
        }

    def allocate_phone_number_to_organization(self, number: str, organization_id: str) -> dict:
        """
        Assign an available phone number to a specified organization, updating its status and allocation field.

        Args:
            number (str): The phone number to allocate. The platform accepts either
                the inventory key or the displayed phone number string.
            organization_id (str): The target organization's ID.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Phone number <number> allocated to organization <organization_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Explanation of failure
                    }

        Constraints:
            - The phone number must exist and have status="available".
            - The organization must exist.
            - On allocation, update status to "allocated" and set allocated_to_organization_id.
        """
        phone_key = self._resolve_phone_number_key(number)
        if not phone_key:
            return { "success": False, "error": "Phone number does not exist." }
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
    
        phone_info = self.phone_numbers[phone_key]
        if phone_info["status"] != "available":
            return { "success": False, "error": "Phone number is not available for allocation." }
    
        phone_info["status"] = "allocated"
        phone_info["allocated_to_organization_id"] = organization_id
        self.phone_numbers[phone_key] = phone_info  # Store back in case a copy was taken

        return {
            "success": True,
            "message": f"Phone number {phone_info['number']} allocated to organization {organization_id}."
        }

    def release_phone_number(self, number: str) -> dict:
        """
        Release an allocated phone number back to 'available' status.

        Args:
            number (str): The phone number to be released. The platform accepts
                either the inventory key or the displayed phone number string.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "<number> released and made available." }
                On failure:
                    { "success": False, "error": "<Reason>" }

        Constraints:
            - Only phone numbers that exist and are currently allocated may be released.
            - Status is set to 'available', and allocated_to_organization_id is cleared.
        """
        phone_key = self._resolve_phone_number_key(number)
        if phone_key is None:
            return { "success": False, "error": f"Phone number {number} does not exist." }

        phone_info = self.phone_numbers[phone_key]

        if phone_info['status'] != 'allocated':
            return { "success": False, "error": f"Phone number {phone_info['number']} is not currently allocated." }

        phone_info['status'] = 'available'
        phone_info['allocated_to_organization_id'] = None
        self.phone_numbers[phone_key] = phone_info

        return { "success": True, "message": f"Phone number {phone_info['number']} released and made available." }

    def add_phone_number(
        self, 
        number: str, 
        country_code: str, 
        metadata: dict
    ) -> dict:
        """
        Add a new phone number to the platform's inventory.

        Args:
            number (str): The phone number to add (must not already exist).
            country_code (str): Country code to associate the phone number to (must exist).
            metadata (dict): Metadata dictionary (can be empty).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Phone number added to inventory." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Phone number must be unique in system (number must not already exist).
            - country_code must refer to an existing country.
            - New phone number is added with status='available' and allocated_to_organization_id=None.
        """
        # Check not empty
        if not number or not isinstance(number, str):
            return { "success": False, "error": "Phone number must be a non-empty string." }

        if number in self.phone_numbers:
            return { "success": False, "error": "Phone number already exists in inventory." }

        if country_code not in self.countries:
            return { "success": False, "error": "Nonexistent country_code. Cannot add phone number." }

        phone_info: PhoneNumberInfo = {
            "number": number,
            "country_code": country_code,
            "status": "available",
            "metadata": metadata if isinstance(metadata, dict) else {},
            "allocated_to_organization_id": None
        }
        self.phone_numbers[number] = phone_info
        return { "success": True, "message": "Phone number added to inventory." }

    def remove_phone_number(self, number: str) -> dict:
        """
        Permanently delete a phone number from the system.

        Args:
            number (str): The phone number to remove. The platform accepts either
                the inventory key or the displayed phone number string.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number <number> has been removed from the system."
            }
            or
            {
                "success": False,
                "error": "Phone number does not exist"
            }

        Constraints:
            - The phone number must exist in the system for removal.
            - Upon success, the phone number is deleted from the platform.
        """
        phone_key = self._resolve_phone_number_key(number)
        if phone_key is None:
            return { "success": False, "error": "Phone number does not exist" }

        removed_number = self.phone_numbers[phone_key]["number"]
        del self.phone_numbers[phone_key]
        return {
            "success": True,
            "message": f"Phone number {removed_number} has been removed from the system."
        }

    def add_country(self, country_code: str, country_name: str) -> dict:
        """
        Register a new country with a unique country_code.

        Args:
            country_code (str): Unique country code to register.
            country_name  (str): Name of the country.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Country 'country_name' (code: country_code) added."
                }
                OR
                {
                    "success": False,
                    "error": "Country code already exists" | "country_code or country_name missing/invalid"
                }

        Constraints:
            - country_code must be unique (not present in self.countries).
        """
        if not country_code or not country_name:
            return { "success": False, "error": "country_code or country_name missing/invalid" }
        if country_code in self.countries:
            return { "success": False, "error": "Country code already exists" }

        self.countries[country_code] = {
            "country_code": country_code,
            "country_name": country_name
        }

        return {
            "success": True,
            "message": f"Country '{country_name}' (code: {country_code}) added."
        }

    def remove_country(self, country_code: str) -> dict:
        """
        Remove a country entry from the system, but only if no phone numbers in the system reference this country_code.

        Args:
            country_code (str): The country code to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Country removed: <country_code>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The country_code must exist.
            - No phone number in the system can reference this country_code.
        """
        # Check if the country exists
        if country_code not in self.countries:
            return { "success": False, "error": f"Country code not found: {country_code}" }

        # Check if any phone number references this country code
        for pn in self.phone_numbers.values():
            if pn["country_code"] == country_code:
                return {
                    "success": False,
                    "error": (
                        f"Cannot remove country {country_code}: one or more phone numbers reference it."
                    )
                }

        # It is safe to remove the country
        del self.countries[country_code]
        return {
            "success": True,
            "message": f"Country removed: {country_code}"
        }

    def add_organization(self, organization_id: str, organization_name: str) -> dict:
        """
        Register a new organization in the platform.

        Args:
            organization_id (str): Unique identifier for the organization.
            organization_name (str): Descriptive display name for the organization.

        Returns:
            dict:
                - On success: { "success": True, "message": "Organization added successfully." }
                - On failure: { "success": False, "error": "reason for failure" }
    
        Constraints:
            - organization_id must be unique (not already in self.organizations).
            - organization_id and organization_name must be non-empty.
        """
        if not organization_id or not isinstance(organization_id, str):
            return { "success": False, "error": "organization_id must be a non-empty string." }
        if not organization_name or not isinstance(organization_name, str):
            return { "success": False, "error": "organization_name must be a non-empty string." }
        if organization_id in self.organizations:
            return { "success": False, "error": "Organization ID already exists." }
    
        self.organizations[organization_id] = {
            "organization_id": organization_id,
            "organization_name": organization_name
        }
        return { "success": True, "message": "Organization added successfully." }

    def remove_organization(self, organization_id: str) -> dict:
        """
        Remove an organization from the platform, ensuring it has no allocated phone numbers.

        Args:
            organization_id (str): The unique identifier of the organization to remove.

        Returns:
            dict: 
                { "success": True, "message": "Organization <org_id> removed." }
                or
                { "success": False, "error": <error description> }

        Constraints:
            - The organization must exist.
            - The organization cannot be removed if any phone number is still allocated to it.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist."}
    
        # Check if any phone number is still allocated to this organization
        for pn_info in self.phone_numbers.values():
            if pn_info.get("allocated_to_organization_id") == organization_id:
                return {
                    "success": False,
                    "error": "Organization has allocated phone numbers and cannot be removed."
                }
    
        del self.organizations[organization_id]
        return {"success": True, "message": f"Organization {organization_id} removed."}


class VirtualPhoneNumberManagementPlatform(BaseEnv):
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

    def list_countries(self, **kwargs):
        return self._call_inner_tool('list_countries', kwargs)

    def get_country_by_code(self, **kwargs):
        return self._call_inner_tool('get_country_by_code', kwargs)

    def list_available_phone_numbers(self, **kwargs):
        return self._call_inner_tool('list_available_phone_numbers', kwargs)

    def list_available_numbers_by_country(self, **kwargs):
        return self._call_inner_tool('list_available_numbers_by_country', kwargs)

    def get_phone_number_info(self, **kwargs):
        return self._call_inner_tool('get_phone_number_info', kwargs)

    def list_organizations(self, **kwargs):
        return self._call_inner_tool('list_organizations', kwargs)

    def get_organization_info(self, **kwargs):
        return self._call_inner_tool('get_organization_info', kwargs)

    def allocate_phone_number_to_organization(self, **kwargs):
        return self._call_inner_tool('allocate_phone_number_to_organization', kwargs)

    def release_phone_number(self, **kwargs):
        return self._call_inner_tool('release_phone_number', kwargs)

    def add_phone_number(self, **kwargs):
        return self._call_inner_tool('add_phone_number', kwargs)

    def remove_phone_number(self, **kwargs):
        return self._call_inner_tool('remove_phone_number', kwargs)

    def add_country(self, **kwargs):
        return self._call_inner_tool('add_country', kwargs)

    def remove_country(self, **kwargs):
        return self._call_inner_tool('remove_country', kwargs)

    def add_organization(self, **kwargs):
        return self._call_inner_tool('add_organization', kwargs)

    def remove_organization(self, **kwargs):
        return self._call_inner_tool('remove_organization', kwargs)
