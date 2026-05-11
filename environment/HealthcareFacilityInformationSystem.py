# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class LocationInfo(TypedDict):
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    latitude: float
    longitude: float

class HealthcareFacilityInfo(TypedDict):
    facility_id: str
    name: str
    facility_type: str
    ownership_type: str
    location: LocationInfo
    operational_status: str
    contact_information: str
    accreditation_status: str
    affiliated_network: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Healthcare Facility Information System state structure.
        """

        # Facilities: {facility_id: HealthcareFacilityInfo}
        # - Each facility has unique facility_id
        # - Location is a nested structure (LocationInfo)
        self.facilities: Dict[str, HealthcareFacilityInfo] = {}

        # Constraints:
        # - Each facility must have a unique facility_id.
        # - Each facility must have a valid and complete location.
        # - Facility operational_status is constrained to accepted values (e.g., active, inactive, under_construction, closed).
        # - Ownership type must be from a predefined set (e.g., private, public, government, non-profit).
        # - Facility data must support both retrieval (queries) and update operations.

    def get_facility_by_id(self, facility_id: str) -> dict:
        """
        Retrieve all information for a single healthcare facility by its unique facility_id.

        Args:
            facility_id (str): The unique identifier for the healthcare facility.

        Returns:
            dict: 
                If found: { "success": True, "data": HealthcareFacilityInfo }
                If not found: { "success": False, "error": "Facility not found" }

        Constraints:
            - The facility_id must exist in the system.
        """
        if not facility_id or facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found" }
        return { "success": True, "data": self.facilities[facility_id] }

    def get_facility_location_by_id(self, facility_id: str) -> dict:
        """
        Retrieve the location details for the healthcare facility with the specified facility_id.

        Args:
            facility_id (str): The unique identifier for the healthcare facility.

        Returns:
            dict: {
                "success": True,
                "data": LocationInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., facility not found)
            }

        Constraints:
            - The facility must exist and have a location.
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return { "success": False, "error": "Facility with given facility_id does not exist." }

        return { "success": True, "data": facility["location"] }

    def list_all_facilities(self) -> dict:
        """
        Retrieve a list of all healthcare facilities currently in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareFacilityInfo],  # List of all facilities (may be empty)
            }

        Constraints:
            - No constraints apply for query; always succeeds.
        """
        all_facilities = list(self.facilities.values())
        return { "success": True, "data": all_facilities }

    def filter_facilities_by_status(self, operational_status: str) -> dict:
        """
        List facilities filtered by their operational_status.

        Args:
            operational_status (str): Status to filter facilities by. Must be one of:
              "active", "inactive", "under_construction", "closed".

        Returns:
            dict: 
              {"success": True, "data": List[HealthcareFacilityInfo]}
              OR
              {"success": False, "error": "reason"}

        Constraints:
          - operational_status must be one of the accepted values.
        """
        allowed_statuses = {"active", "inactive", "under_construction", "closed"}
        if operational_status not in allowed_statuses:
            return {"success": False, "error": "Invalid operational status"}

        result = [
            facility
            for facility in self.facilities.values()
            if facility["operational_status"] == operational_status
        ]
        return {"success": True, "data": result}

    def filter_facilities_by_ownership(self, ownership_type: str) -> dict:
        """
        List all facilities matching the specified ownership_type.

        Args:
            ownership_type (str): The ownership type to filter facilities by.
                Accepted values: 'private', 'public', 'government', 'non-profit'.

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareFacilityInfo]  # All facilities with the ownership_type (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason why operation failed (e.g. invalid ownership_type)
            }

        Constraints:
            - ownership_type must be one of the allowed ownership types.
        """
        allowed_types = {"private", "public", "government", "non-profit"}
        if ownership_type not in allowed_types:
            return { "success": False, "error": "Invalid ownership_type. Must be one of: private, public, government, non-profit." }

        facilities = [
            facility for facility in self.facilities.values()
            if facility["ownership_type"] == ownership_type
        ]
        return { "success": True, "data": facilities }

    def filter_facilities_by_type(self, facility_type: str) -> dict:
        """
        List all healthcare facilities that match the specified facility_type.

        Args:
            facility_type (str): The type of facility to filter for (e.g., 'hospital', 'clinic', 'lab').

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareFacilityInfo]  # All facilities with matching facility_type
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., missing facility_type
            }

        Constraints:
            - facility_type must be a non-empty string.
            - Comparison is case-insensitive.
        """
        if not isinstance(facility_type, str) or not facility_type.strip():
            return {"success": False, "error": "facility_type must be a non-empty string"}

        facility_type_lower = facility_type.strip().lower()

        filtered = [
            facility
            for facility in self.facilities.values()
            if facility.get("facility_type", "").strip().lower() == facility_type_lower
        ]

        return {"success": True, "data": filtered}

    def filter_facilities_by_network(self, affiliated_network: str) -> dict:
        """
        List all healthcare facilities that belong to the specified affiliated_network.

        Args:
            affiliated_network (str): The network name or identifier to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[HealthcareFacilityInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - affiliated_network must be a non-empty string.
            - Exact string match on the 'affiliated_network' attribute.
            - If no matches, returns an empty list in data.
        """
        if not isinstance(affiliated_network, str) or affiliated_network.strip() == "":
            return {"success": False, "error": "affiliated_network must be a non-empty string"}

        result = [
            facility for facility in self.facilities.values()
            if facility.get("affiliated_network", "") == affiliated_network
        ]
        return {"success": True, "data": result}

    def get_facility_accreditation_status(self, facility_id: str) -> dict:
        """
        Retrieve the accreditation_status for a facility by its facility_id.

        Args:
            facility_id (str): The unique identifier of the healthcare facility.

        Returns:
            dict: {
                "success": True,
                "data": str,  # The accreditation status of the facility
            }
            or
            {
                "success": False,
                "error": str  # Description of the error if not found
            }

        Constraints:
            - Facility with the provided facility_id must exist.
            - Each facility is guaranteed to have an accreditation_status field.
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return { "success": False, "error": "Facility not found" }
        # Robustness: check that accreditation_status exists and is a string
        accreditation_status = facility.get("accreditation_status")
        if accreditation_status is None or not isinstance(accreditation_status, str):
            return { "success": False, "error": "Accreditation status not available" }
        return { "success": True, "data": accreditation_status }

    def validate_facility_location(self, facility_id: str) -> dict:
        """
        Check whether location information for the specified facility is complete and valid.

        Args:
            facility_id (str): Unique identifier for the healthcare facility.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "valid": bool,           # True if valid and complete, else False
                    "issues": List[str]      # List of validation problem descriptions (empty if valid)
                }
            }
            or
            {
                "success": False,
                "error": str               # Description of error (facility not found)
            }

        Constraints:
            - Facility must exist.
            - All required location fields must be present and have reasonable values.
            - address_line1, city, state, postal_code, country: non-empty string
            - latitude: float, -90 <= latitude <= 90
            - longitude: float, -180 <= longitude <= 180
            - address_line2 is optional
        """
        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found" }

        facility = self.facilities[facility_id]
        location = facility.get("location")
        required_str_fields = ["address_line1", "city", "state", "postal_code", "country"]
        issues = []

        # Check presence and non-empty string for required string fields
        for field in required_str_fields:
            value = location.get(field) if location else None
            if not isinstance(value, str) or not value.strip():
                issues.append(f"Missing or invalid field: {field}")

        # Check latitude
        lat = location.get("latitude") if location else None
        if lat is None or not isinstance(lat, (float, int)) or not (-90.0 <= float(lat) <= 90.0):
            issues.append("Latitude missing or out of range (-90 to 90)")

        # Check longitude
        lon = location.get("longitude") if location else None
        if lon is None or not isinstance(lon, (float, int)) or not (-180.0 <= float(lon) <= 180.0):
            issues.append("Longitude missing or out of range (-180 to 180)")

        result = {
            "valid": len(issues) == 0,
            "issues": issues
        }
        return { "success": True, "data": result }

    def create_facility(self, new_facility: dict) -> dict:
        """
        Create a new healthcare facility record with all required details.

        Args:
            new_facility (dict): Expected to conform to HealthcareFacilityInfo structure,
                                 including a nested 'location' dict.
                - facility_id (str): Unique facility identifier.
                - name (str)
                - facility_type (str)
                - ownership_type (str): Must be one of ['private','public','government','non-profit']
                - location (dict): Must satisfy LocationInfo (all fields except address_line2 required/nonempty)
                - operational_status (str): Must be one of ['active','inactive','under_construction','closed']
                - contact_information (str)
                - accreditation_status (str)
                - affiliated_network (str)
        
        Returns:
            dict: 
                On success: {"success": True, "message": "Facility created successfully."}
                On failure: {"success": False, "error": "<reason>"}
    
        Constraints:
            - facility_id must be unique
            - All facility/location fields must be present (except location.address_line2 which is optional)
            - operational_status must be ['active','inactive','under_construction','closed']
            - ownership_type must be ['private','public','government','non-profit']
        """

        required_fields = [
            'facility_id', 'name', 'facility_type',
            'ownership_type', 'location', 'operational_status',
            'contact_information', 'accreditation_status',
            'affiliated_network'
        ]
        allowed_status = ['active', 'inactive', 'under_construction', 'closed']
        allowed_ownership = ['private', 'public', 'government', 'non-profit']
        location_required_fields = [
            'address_line1', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude'
        ]

        # 1. Check all required facility fields present
        for field in required_fields:
            if field not in new_facility:
                return { "success": False, "error": f"Missing required field: {field}" }

        # 2. Check facility_id uniqueness
        facility_id = new_facility['facility_id']
        if facility_id in self.facilities:
            return { "success": False, "error": "facility_id already exists." }

        # 3. Validate ownership_type
        if new_facility['ownership_type'] not in allowed_ownership:
            return { "success": False, "error": "Invalid ownership_type. Must be one of: " + ", ".join(allowed_ownership) }

        # 4. Validate operational_status
        if new_facility['operational_status'] not in allowed_status:
            return { "success": False, "error": "Invalid operational_status. Must be one of: " + ", ".join(allowed_status) }

        # 5. Validate location completeness and types
        location = new_facility['location']
        for f in location_required_fields:
            if f not in location or location[f] in [None, '']:
                return { "success": False, "error": f"Missing or empty location field: {f}" }
        # Attempt to convert latitude/longitude to float if not already, fail if not possible
        try:
            location['latitude'] = float(location['latitude'])
            location['longitude'] = float(location['longitude'])
        except Exception:
            return { "success": False, "error": "Invalid latitude/longitude. Must be numbers." }

        # 6. Store (deepcopy to be safe, or just assign)
        self.facilities[facility_id] = {
            "facility_id": facility_id,
            "name": new_facility["name"],
            "facility_type": new_facility["facility_type"],
            "ownership_type": new_facility["ownership_type"],
            "location": {
                "address_line1": location["address_line1"],
                "address_line2": location.get("address_line2", ""),
                "city": location["city"],
                "state": location["state"],
                "postal_code": location["postal_code"],
                "country": location["country"],
                "latitude": location["latitude"],
                "longitude": location["longitude"]
            },
            "operational_status": new_facility["operational_status"],
            "contact_information": new_facility["contact_information"],
            "accreditation_status": new_facility["accreditation_status"],
            "affiliated_network": new_facility["affiliated_network"]
        }

        return { "success": True, "message": "Facility created successfully." }

    def update_facility_location(self, facility_id: str, new_location: dict) -> dict:
        """
        Update the location information for an existing healthcare facility.

        Args:
            facility_id (str): Unique ID for the healthcare facility.
            new_location (dict): Dictionary with location fields; must include:
                - address_line1 (str)
                - city (str)
                - state (str)
                - postal_code (str)
                - country (str)
                - latitude (float)
                - longitude (float)
                - Optional: address_line2 (str)

        Returns:
            dict: 
             - On success: { "success": True, "message": "Location updated for facility <facility_id>" }
             - On error: { "success": False, "error": <error reason> }

        Constraints:
            - Facility with given ID must exist.
            - Location must be valid and complete (no missing required fields).
        """
        # 1. Check existence of facility
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        # 2. Validate location completeness
        required_fields = [
            "address_line1", "city", "state", "postal_code", "country", "latitude", "longitude"
        ]
        for field in required_fields:
            if field not in new_location or new_location[field] in [None, ""]:
                return {"success": False, "error": f"Location is incomplete or missing field '{field}'"}

        # 3. Validate types (latitude/longitude must be float)
        try:
            lat = float(new_location["latitude"])
            lon = float(new_location["longitude"])
        except (ValueError, TypeError):
            return {"success": False, "error": "Latitude and longitude must be numeric"}
    
        # Prepare LocationInfo; address_line2 is optional
        location_info = {
            "address_line1": new_location["address_line1"],
            "address_line2": new_location.get("address_line2"),
            "city": new_location["city"],
            "state": new_location["state"],
            "postal_code": new_location["postal_code"],
            "country": new_location["country"],
            "latitude": lat,
            "longitude": lon,
        }
        # 4. Update facility location
        self.facilities[facility_id]["location"] = location_info

        return {"success": True, "message": f"Location updated for facility {facility_id}"}

    def update_facility_status(self, facility_id: str, new_status: str) -> dict:
        """
        Change the operational_status of a healthcare facility, enforcing allowed status values.

        Args:
            facility_id (str): Unique identifier of the facility to update.
            new_status (str): The new operational status to set. Must be one of:
                ["active", "inactive", "under_construction", "closed"]

        Returns:
            dict: 
            - On success: { "success": True, "message": "Facility status updated successfully" }
            - On failure: { "success": False, "error": <reason> }

        Constraints:
            - facility_id must exist in the system.
            - new_status must be a valid operational status.
        """
        allowed_statuses = {"active", "inactive", "under_construction", "closed"}

        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility ID not found" }
    
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status: {new_status}. Allowed statuses: {sorted(allowed_statuses)}" }

        self.facilities[facility_id]["operational_status"] = new_status
        return { "success": True, "message": "Facility status updated successfully" }

    def update_facility_ownership_type(self, facility_id: str, new_ownership_type: str) -> dict:
        """
        Update the ownership_type of the healthcare facility with the provided facility_id.

        Args:
            facility_id (str): The unique identifier of the facility to update.
            new_ownership_type (str): The new ownership type. Must be one of: 'private', 'public', 'government', 'non-profit'.

        Returns:
            dict: {
                "success": True,
                "message": "Ownership type updated."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - Facility must exist.
            - new_ownership_type must be one of: 'private', 'public', 'government', 'non-profit'.
        """
        allowed_ownership_types = {"private", "public", "government", "non-profit"}

        # Check if facility exists
        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found." }

        # Ownership type validation
        if new_ownership_type not in allowed_ownership_types:
            return {
                "success": False,
                "error": f"Ownership type '{new_ownership_type}' is invalid. Allowed values: {', '.join(allowed_ownership_types)}."
            }

        self.facilities[facility_id]["ownership_type"] = new_ownership_type

        return { "success": True, "message": "Ownership type updated." }

    def update_facility_contact_information(self, facility_id: str, new_contact_information: str) -> dict:
        """
        Updates the contact_information attribute for the specified facility.

        Args:
            facility_id (str): The unique identifier of the facility to update.
            new_contact_information (str): The new contact information to set.

        Returns:
            dict: {
                "success": True,
                "message": "Contact information updated for facility <facility_id>."
            }
            or
            {
                "success": False,
                "error": "Facility with facility_id <facility_id> does not exist."
            }

        Constraints:
            - Facility must exist (checked by facility_id).
            - No format/structure validation is performed on the contact_information.
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return {"success": False, "error": f"Facility with facility_id {facility_id} does not exist."}
    
        facility["contact_information"] = new_contact_information
        return {"success": True, "message": f"Contact information updated for facility {facility_id}."}

    def update_facility_accreditation_status(self, facility_id: str, new_accreditation_status: str) -> dict:
        """
        Update the accreditation_status for a healthcare facility.

        Args:
            facility_id (str): The unique identifier for the facility.
            new_accreditation_status (str): The new accreditation status to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Accreditation status updated for facility <facility_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Facility with the given ID does not exist."
                    }

        Constraints:
            - Facility must exist (facility_id in facilities).
        """
        if facility_id not in self.facilities:
            return {
                "success": False,
                "error": "Facility with the given ID does not exist."
            }
        self.facilities[facility_id]["accreditation_status"] = new_accreditation_status
        return {
            "success": True,
            "message": f"Accreditation status updated for facility {facility_id}."
        }

    def update_facility_affiliated_network(self, facility_id: str, affiliated_network: str) -> dict:
        """
        Update the affiliated_network attribute for a healthcare facility.

        Args:
            facility_id (str): The unique identifier of the healthcare facility.
            affiliated_network (str): The new value for affiliated_network.

        Returns:
            dict: {
                "success": True,
                "message": "Affiliated network updated for facility <facility_id>."
            }
            or
            {
                "success": False,
                "error": "Facility not found."
            }

        Constraints:
            - Facility with facility_id must exist.
            - No restriction on value of affiliated_network.
        """
        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found." }

        self.facilities[facility_id]["affiliated_network"] = affiliated_network

        return {
            "success": True,
            "message": f"Affiliated network updated for facility {facility_id}."
        }

    def update_facility_name_type(
        self,
        facility_id: str,
        name: str = None,
        facility_type: str = None
    ) -> dict:
        """
        Update the name and/or facility_type for the specified healthcare facility.

        Args:
            facility_id (str): Unique identifier of the facility to be updated.
            name (Optional[str]): New name for the facility (if updating).
            facility_type (Optional[str]): New facility type (if updating).

        Returns:
            dict:
                On success: { "success": True, "message": "Facility name and/or type updated." }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - facility_id must exist.
            - At least one of name or facility_type must be provided (not both None).
            - Other fields remain unchanged.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility with given facility_id does not exist."}

        if name is None and facility_type is None:
            return {"success": False, "error": "No update values provided (name and facility_type are both None)."}

        updated = False

        if name is not None:
            self.facilities[facility_id]["name"] = name
            updated = True

        if facility_type is not None:
            self.facilities[facility_id]["facility_type"] = facility_type
            updated = True

        if updated:
            return {"success": True, "message": "Facility name and/or type updated."}
        else:
            return {"success": False, "error": "No valid update performed."}

    def delete_facility(self, facility_id: str) -> dict:
        """
        Remove a healthcare facility from the system, if it exists.

        Args:
            facility_id (str): The unique identifier of the facility to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Facility <facility_id> deleted successfully" }
                On failure:
                    { "success": False, "error": "Facility with id <facility_id> does not exist" }

        Constraints:
            - Facility must exist in the system to be deleted.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": f"Facility with id {facility_id} does not exist"}

        del self.facilities[facility_id]
        return {"success": True, "message": f"Facility {facility_id} deleted successfully"}


class HealthcareFacilityInformationSystem(BaseEnv):
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

    def get_facility_by_id(self, **kwargs):
        return self._call_inner_tool('get_facility_by_id', kwargs)

    def get_facility_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_facility_location_by_id', kwargs)

    def list_all_facilities(self, **kwargs):
        return self._call_inner_tool('list_all_facilities', kwargs)

    def filter_facilities_by_status(self, **kwargs):
        return self._call_inner_tool('filter_facilities_by_status', kwargs)

    def filter_facilities_by_ownership(self, **kwargs):
        return self._call_inner_tool('filter_facilities_by_ownership', kwargs)

    def filter_facilities_by_type(self, **kwargs):
        return self._call_inner_tool('filter_facilities_by_type', kwargs)

    def filter_facilities_by_network(self, **kwargs):
        return self._call_inner_tool('filter_facilities_by_network', kwargs)

    def get_facility_accreditation_status(self, **kwargs):
        return self._call_inner_tool('get_facility_accreditation_status', kwargs)

    def validate_facility_location(self, **kwargs):
        return self._call_inner_tool('validate_facility_location', kwargs)

    def create_facility(self, **kwargs):
        return self._call_inner_tool('create_facility', kwargs)

    def update_facility_location(self, **kwargs):
        return self._call_inner_tool('update_facility_location', kwargs)

    def update_facility_status(self, **kwargs):
        return self._call_inner_tool('update_facility_status', kwargs)

    def update_facility_ownership_type(self, **kwargs):
        return self._call_inner_tool('update_facility_ownership_type', kwargs)

    def update_facility_contact_information(self, **kwargs):
        return self._call_inner_tool('update_facility_contact_information', kwargs)

    def update_facility_accreditation_status(self, **kwargs):
        return self._call_inner_tool('update_facility_accreditation_status', kwargs)

    def update_facility_affiliated_network(self, **kwargs):
        return self._call_inner_tool('update_facility_affiliated_network', kwargs)

    def update_facility_name_type(self, **kwargs):
        return self._call_inner_tool('update_facility_name_type', kwargs)

    def delete_facility(self, **kwargs):
        return self._call_inner_tool('delete_facility', kwargs)

