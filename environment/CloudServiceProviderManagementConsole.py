# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class RegionInfo(TypedDict):
    # Represents a geographic area managing provisionable cloud resources
    region_id: str
    region_name: str
    status: str  # enabled, disabled, or available
    supported_services: List[str]  # List of service_id
    resource_quota: int  # Assumed as int

class ServiceInfo(TypedDict):
    # Represents a cloud service and its available regions
    service_id: str
    service_name: str
    regions_available: List[str]  # List of region_id

class _GeneratedEnvImpl:
    def __init__(self):
        # Regions: {region_id: RegionInfo}
        self.regions: Dict[str, RegionInfo] = {}
        # Services: {service_id: ServiceInfo}
        self.services: Dict[str, ServiceInfo] = {}

        # Constraints:
        # - Only regions with status "enabled" or "available" can be used for deploying resources.
        # - Each region must have a unique region_id and region_name.
        # - Services can only be provisioned in regions where they are listed as available.

    def list_all_regions(self) -> dict:
        """
        Return complete information about all defined regions.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RegionInfo],  # All regions (empty list if none defined)
            }

        Constraints:
            - No constraints enforced—this is a pure query.
        """
        all_regions = list(self.regions.values())
        return { "success": True, "data": all_regions }

    def get_region_by_id(self, region_id: str) -> dict:
        """
        Retrieve metadata for a region by unique region_id.

        Args:
            region_id (str): The unique identifier for the region to query.

        Returns:
            dict: {
                "success": True,
                "data": RegionInfo,   # Region details for the given region_id
            }
            or
            {
                "success": False,
                "error": str  # Description if region not found
            }

        Constraints:
            - region_id must exist in the regions dictionary.
        """
        region_info = self.regions.get(region_id)
        if region_info is None:
            return { "success": False, "error": "Region with given region_id not found" }
        return { "success": True, "data": region_info }

    def get_region_by_name(self, region_name: str) -> dict:
        """
        Retrieve region metadata by region_name.

        Args:
            region_name (str): The human-friendly name of the region.

        Returns:
            dict: 
              - On success: { "success": True, "data": RegionInfo }
              - On failure: { "success": False, "error": "Region not found" }

        Constraints:
            - region_name must be unique among all regions.
        """
        for region in self.regions.values():
            if region["region_name"] == region_name:
                return { "success": True, "data": region }
        return { "success": False, "error": "Region not found" }

    def list_regions_by_status(self, status: str) -> dict:
        """
        Retrieve all regions filtered by their status ('enabled', 'available', or 'disabled').

        Args:
            status (str): The region status to filter by. Valid values: 'enabled', 'available', 'disabled'.

        Returns:
            dict: {
                "success": True,
                "data": List[RegionInfo],  # List of regions with the specified status
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, such as invalid status value
            }

        Constraints:
            - Only status values 'enabled', 'available', or 'disabled' are valid.
        """
        valid_statuses = {"enabled", "available", "disabled"}
        if status not in valid_statuses:
            return {"success": False, "error": "Invalid status value"}

        matching_regions = [
            region_info for region_info in self.regions.values()
            if region_info["status"] == status
        ]

        return {"success": True, "data": matching_regions}

    def list_available_regions(self) -> dict:
        """
        List all regions with status "enabled" or "available" (deployable).
        Returns region_id and region_name for each such region.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict: {"region_id": str, "region_name": str}
            }

        Constraints:
            - Only regions with status "enabled" or "available" are included.
            - Returns empty list if no matching regions.
        """
        result = [
            {"region_id": region["region_id"], "region_name": region["region_name"]}
            for region in self.regions.values()
            if region["status"] in ("enabled", "available")
        ]
        return {"success": True, "data": result}

    def get_region_supported_services(self, region_id: str) -> dict:
        """
        For a given region, list all the supported service_ids and service_names.

        Args:
            region_id (str): The unique identifier of the region.

        Returns:
            dict: {
                "success": True,
                "data": [  # List of supported services
                    {
                        "service_id": str,
                        "service_name": Optional[str]  # None or missing if not defined
                    },
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g., "Region not found"
            }

        Constraints:
            - The region must exist.
            - If a supported service is missing from the global list, it is included with service_name as None.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region not found" }
    
        region_info = self.regions[region_id]
        result = []
        for service_id in region_info.get("supported_services", []):
            service_info = self.services.get(service_id)
            service_name = service_info["service_name"] if service_info else None
            result.append({
                "service_id": service_id,
                "service_name": service_name
            })
    
        return { "success": True, "data": result }

    def list_all_services(self) -> dict:
        """
        Return metadata for all defined services.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ServiceInfo],  # List of all service metadata (may be empty)
            }
        """
        services_list = list(self.services.values())
        return { "success": True, "data": services_list }

    def get_service_by_id(self, service_id: str) -> dict:
        """
        Retrieve detailed information about a service given its unique service_id.

        Args:
            service_id (str): Unique identifier for the service.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": ServiceInfo  # Service metadata dictionary
                    }
                - On failure:
                    {
                      "success": False,
                      "error": str  # Error message, e.g., "Service not found"
                    }

        Constraints:
            - service_id must be present in self.services.
        """
        service = self.services.get(service_id)
        if not service:
            return {"success": False, "error": "Service not found"}

        return {"success": True, "data": service}

    def get_service_by_name(self, service_name: str) -> dict:
        """
        Retrieve cloud service info by its human-friendly service_name.

        Args:
            service_name (str): The name of the service to look up.

        Returns:
            dict: {
                "success": True,
                "data": ServiceInfo  # Service information structure
            }
            or
            {
                "success": False,
                "error": str  # Reason why retrieval failed (e.g. not found)
            }

        Constraints:
            - Service names are unique in the environment.
        """
        for service_info in self.services.values():
            if service_info["service_name"] == service_name:
                return {"success": True, "data": service_info}
        return {"success": False, "error": "Service with specified name does not exist"}

    def get_service_supported_regions(self, service_id: str) -> dict:
        """
        For a given service, list all regions (region_ids and region_names) in which it is available.

        Args:
            service_id (str): The unique identifier of the service.

        Returns:
            dict: {
                "success": True,
                "data": [ { "region_id": str, "region_name": str }, ... ]
            }
            or
            {
                "success": False,
                "error": "Service not found"
            }

        Constraints:
            - If the service_id does not exist, returns an error.
            - Only returns regions that actually exist in the system (skips missing regions if any).
        """
        service = self.services.get(service_id)
        if service is None:
            return { "success": False, "error": "Service not found" }

        regions_info = []
        for region_id in service.get("regions_available", []):
            region = self.regions.get(region_id)
            if region:
                regions_info.append({
                    "region_id": region["region_id"],
                    "region_name": region["region_name"]
                })

        return { "success": True, "data": regions_info }

    def get_region_resource_quota(self, region_id: str) -> dict:
        """
        Retrieve the current resource quota for the specified region.

        Args:
            region_id (str): Unique identifier of the region.

        Returns:
            dict: {
                "success": True,
                "data": int  # resource_quota value for the region,
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., region does not exist)
            }

        Constraints:
            - The region_id must exist in the regions dictionary.
        """
        region = self.regions.get(region_id)
        if region is None:
            return { "success": False, "error": "Region does not exist" }

        return { "success": True, "data": region["resource_quota"] }

    def check_region_id_uniqueness(self, region_id: str) -> dict:
        """
        Verify if the provided region_id is unique (i.e., not already present in the environment).

        Args:
            region_id (str): The region ID to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if region_id is unique (does not exist in current regions), False otherwise.
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid (e.g., empty)
            }
        Constraints:
            - region_id must not be empty
            - Each region must have a unique region_id
        """
        if not region_id or not isinstance(region_id, str):
            return { "success": False, "error": "Invalid input: region_id must be a non-empty string." }

        is_unique = region_id not in self.regions
        return { "success": True, "data": is_unique }

    def check_region_name_uniqueness(self, region_name: str) -> dict:
        """
        Verify if a given region_name is unique among all regions.

        Args:
            region_name (str): The region name to be checked.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if region_name is unique (not in use), False otherwise
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - region_name must be non-empty string.
            - Uniqueness is case-sensitive.
        """
        if not isinstance(region_name, str) or not region_name:
            return { "success": False, "error": "region_name must be a non-empty string" }

        for region in self.regions.values():
            if region["region_name"] == region_name:
                return { "success": True, "data": False }

        return { "success": True, "data": True }

    def enable_region(self, region_id: str) -> dict:
        """
        Change the status of a region to "enabled".

        Args:
            region_id (str): Unique region identifier.

        Returns:
            dict: {
                "success": True,
                "message": str  # The region status has been set to enabled (or already enabled)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., region not found
            }

        Constraints:
            - The region with the specified region_id must exist.
            - Status changed only if region is not already enabled.
        """
        region = self.regions.get(region_id)
        if not region:
            return { "success": False, "error": f"Region '{region_id}' not found" }

        if region["status"] == "enabled":
            return { "success": True, "message": f"Region '{region_id}' is already enabled" }

        region["status"] = "enabled"
        self.regions[region_id] = region  # Explicitly update in case of dict
        return { "success": True, "message": f"Region '{region_id}' status set to enabled" }

    def disable_region(self, region_id: str) -> dict:
        """
        Sets the status of the specified region to 'disabled'.

        Args:
            region_id (str): The unique identifier of the region to disable.

        Returns:
            dict: {
                "success": True,
                "message": "Region {region_id} status set to disabled."
            }
            or
            {
                "success": False,
                "error": "Region not found."
            }

        Constraints:
            - Region must exist.
            - Idempotent: If region is already disabled, still return success.

        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region not found." }

        self.regions[region_id]["status"] = "disabled"
        return { "success": True, "message": f"Region {region_id} status set to disabled." }

    def set_region_status(self, region_id: str, status: str) -> dict:
        """
        Set the status of a region to one of the valid values ("enabled", "available", "disabled").

        Args:
            region_id (str): The unique identifier for the region whose status is to be changed.
            status (str): The target status. Must be "enabled", "available", or "disabled".

        Returns:
            dict: {
                "success": True,
                "message": "Region status set to <status> for region <region_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The region must exist (region_id must be present).
            - The status must be one of: "enabled", "available", "disabled".
        """
        if region_id not in self.regions:
            return { "success": False, "error": f"Region with id '{region_id}' does not exist." }

        valid_statuses = {"enabled", "available", "disabled"}
        if status not in valid_statuses:
            return { "success": False, "error": f"Invalid status '{status}'. Must be one of {sorted(valid_statuses)}." }

        self.regions[region_id]['status'] = status
        return { "success": True, "message": f"Region status set to {status} for region {region_id}." }

    def add_region(
        self,
        region_id: str,
        region_name: str,
        status: str,
        supported_services: list,
        resource_quota: int
    ) -> dict:
        """
        Add a new region to the cloud environment.

        Args:
            region_id (str): Unique region identifier.
            region_name (str): Unique, human-friendly region name.
            status (str): Must be one of "enabled", "disabled", or "available".
            supported_services (List[str]): List of service_ids for initial support.
            resource_quota (int): Initial resource quota (non-negative integer).
    
        Returns:
            dict: 
                { "success": True, "message": "Region '<region_id>' added successfully." }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - region_id and region_name must be unique.
            - status must be "enabled", "disabled", or "available".
            - resource_quota must be >= 0.
            - No restrictions enforced here for supported_services.
        """
        # Check for region_id uniqueness
        if region_id in self.regions:
            return { "success": False, "error": "region_id already exists" }

        # Check for region_name uniqueness
        for r in self.regions.values():
            if r['region_name'] == region_name:
                return { "success": False, "error": "region_name already exists" }

        # Validate status
        if status not in ['enabled', 'disabled', 'available']:
            return { "success": False, "error": "Invalid status value" }

        # Validate resource_quota
        if not isinstance(resource_quota, int) or resource_quota < 0:
            return { "success": False, "error": "resource_quota must be a non-negative integer" }

        # Validate supported_services to be a list (light validation)
        if not isinstance(supported_services, list):
            return { "success": False, "error": "supported_services must be a list of service_id strings" }

        # Compose RegionInfo
        region_info = {
            "region_id": region_id,
            "region_name": region_name,
            "status": status,
            "supported_services": list(supported_services),
            "resource_quota": resource_quota
        }
        self.regions[region_id] = region_info

        return { "success": True, "message": f"Region '{region_id}' added successfully." }

    def remove_region(self, region_id: str) -> dict:
        """
        Remove a region and all associated resource info from the system.

        Args:
            region_id (str): The unique identifier of the region to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Region <region_id> removed successfully."
            }
            or
            {
                "success": False,
                "error": "Region does not exist."
            }

        Constraints:
            - Only an existing region can be removed.
            - All references to the region in services (regions_available) must be purged.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist." }

        # Remove region from regions dict
        del self.regions[region_id]

        # Remove region from all services' regions_available lists
        for service in self.services.values():
            if region_id in service["regions_available"]:
                service["regions_available"] = [
                    r for r in service["regions_available"] if r != region_id
                ]

        return { "success": True, "message": f"Region {region_id} removed successfully." }

    def set_region_resource_quota(self, region_id: str, new_quota: int) -> dict:
        """
        Update the resource quota for the given region.

        Args:
            region_id (str): The unique identifier of the region to update.
            new_quota (int): The new resource quota value (must be a non-negative integer).

        Returns:
            dict:
                - On success: { "success": True, "message": "Resource quota updated for region <region_id>." }
                - On failure: { "success": False, "error": str }

        Constraints:
            - The region must exist (region_id present in self.regions).
            - The new quota must be a non-negative integer.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist." }

        if not isinstance(new_quota, int) or new_quota < 0:
            return { "success": False, "error": "Invalid quota value. Must be a non-negative integer." }

        self.regions[region_id]["resource_quota"] = new_quota

        return { "success": True, "message": f"Resource quota updated for region {region_id}." }

    def add_service(self, service_id: str, service_name: str, regions_available: List[str]) -> dict:
        """
        Add a new service definition and specify its supported regions.

        Args:
            service_id (str): Unique identifier for the new service.
            service_name (str): Human-friendly service name.
            regions_available (List[str]): List of region_ids where this service is available.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Service <service_id> added."}
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - service_id must be unique (no existing Service with that id).
            - regions_available must only contain region_ids that exist in self.regions.
            - (Optional) service_name uniqueness not enforced unless specified by constraints.
        """
        if service_id in self.services:
            return {"success": False, "error": "Service ID already exists."}

        # Check all region IDs exist
        invalid_regions = [rid for rid in regions_available if rid not in self.regions]
        if invalid_regions:
            return {"success": False, "error": f"Region IDs do not exist: {', '.join(invalid_regions)}"}

        self.services[service_id] = {
            "service_id": service_id,
            "service_name": service_name,
            "regions_available": list(regions_available)
        }

        return {"success": True, "message": f"Service {service_id} added."}

    def remove_service(self, service_id: str) -> dict:
        """
        Remove a service from the management console system.

        Args:
            service_id (str): The ID of the service to remove.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Service <service_id> removed successfully."}
                - On failure: {"success": False, "error": "Service <service_id> does not exist."}
    
        Constraints:
            - service_id must exist in the system.
            - After removal, service_id must be removed from all regions' supported_services lists for consistency.
        """
        if service_id not in self.services:
            return {"success": False, "error": f"Service {service_id} does not exist."}

        # Remove from services dict
        del self.services[service_id]

        # Remove from all regions' supported_services lists
        for region_info in self.regions.values():
            if service_id in region_info.get("supported_services", []):
                region_info["supported_services"] = [
                    sid for sid in region_info["supported_services"] if sid != service_id
                ]

        return {"success": True, "message": f"Service {service_id} removed successfully."}

    def update_region_supported_services(self, region_id: str, new_supported_services: list) -> dict:
        """
        Edit the list of services supported in a region.

        Args:
            region_id (str): The unique identifier of the region.
            new_supported_services (list of str): List of service_id to set as supported in this region.

        Returns:
            dict: {
                "success": True,
                "message": "Supported services updated for region <region_id>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - region_id must exist.
            - All service_id in new_supported_services must exist.
            - Duplicate service_ids in the list will be reduced to unique set.
        """
        if region_id not in self.regions:
            return { "success": False, "error": f"Region {region_id} does not exist" }
    
        # Remove duplicates from new_supported_services and convert to list of strings
        unique_services = list({str(sid) for sid in new_supported_services})
    
        # Validate that all service_ids exist
        missing_services = [sid for sid in unique_services if sid not in self.services]
        if missing_services:
            return { 
                "success": False,
                "error": f"Invalid service_id(s): {', '.join(missing_services)}"
            }
    
        # Update supported_services for region
        self.regions[region_id]['supported_services'] = unique_services

        return {
            "success": True,
            "message": f"Supported services updated for region {region_id}"
        }

    def update_service_available_regions(self, service_id: str, new_region_ids: List[str]) -> dict:
        """
        Edit the regions where a given service is available.

        Args:
            service_id (str): The identifier for the service to update availability.
            new_region_ids (List[str]): New list of region_ids where this service should be available.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Regions for service updated." }
                - On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - service_id must exist in self.services.
            - Each region_id in new_region_ids must exist in self.regions.
            - No exceptions raised; errors are reported via result dict.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service ID does not exist" }

        invalid_regions = [rid for rid in new_region_ids if rid not in self.regions]
        if invalid_regions:
            return { "success": False, "error": f"Invalid region ID(s): {', '.join(invalid_regions)}" }

        self.services[service_id]["regions_available"] = new_region_ids

        return { "success": True, "message": "Regions for service updated." }

    def rename_region(self, region_id: str, new_region_name: str) -> dict:
        """
        Change the region_name for a given region_id, ensuring uniqueness.

        Args:
            region_id (str): ID of the region to rename.
            new_region_name (str): The desired new, unique human-friendly name for the region.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "<old_name> renamed to <new_region_name>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - region_id must exist.
            - new_region_name must be unique among all regions.
        """
        # Check if region_id exists
        region_info = self.regions.get(region_id)
        if not region_info:
            return { "success": False, "error": "Region ID does not exist" }

        # Check uniqueness of new_region_name
        for rid, info in self.regions.items():
            if info["region_name"] == new_region_name and rid != region_id:
                return { "success": False, "error": "Region name already in use" }

        old_name = region_info["region_name"]
        # Update the region name
        self.regions[region_id]["region_name"] = new_region_name

        return {
            "success": True,
            "message": f"Region '{old_name}' (ID: {region_id}) renamed to '{new_region_name}'"
        }


class CloudServiceProviderManagementConsole(BaseEnv):
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

    def list_all_regions(self, **kwargs):
        return self._call_inner_tool('list_all_regions', kwargs)

    def get_region_by_id(self, **kwargs):
        return self._call_inner_tool('get_region_by_id', kwargs)

    def get_region_by_name(self, **kwargs):
        return self._call_inner_tool('get_region_by_name', kwargs)

    def list_regions_by_status(self, **kwargs):
        return self._call_inner_tool('list_regions_by_status', kwargs)

    def list_available_regions(self, **kwargs):
        return self._call_inner_tool('list_available_regions', kwargs)

    def get_region_supported_services(self, **kwargs):
        return self._call_inner_tool('get_region_supported_services', kwargs)

    def list_all_services(self, **kwargs):
        return self._call_inner_tool('list_all_services', kwargs)

    def get_service_by_id(self, **kwargs):
        return self._call_inner_tool('get_service_by_id', kwargs)

    def get_service_by_name(self, **kwargs):
        return self._call_inner_tool('get_service_by_name', kwargs)

    def get_service_supported_regions(self, **kwargs):
        return self._call_inner_tool('get_service_supported_regions', kwargs)

    def get_region_resource_quota(self, **kwargs):
        return self._call_inner_tool('get_region_resource_quota', kwargs)

    def check_region_id_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_region_id_uniqueness', kwargs)

    def check_region_name_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_region_name_uniqueness', kwargs)

    def enable_region(self, **kwargs):
        return self._call_inner_tool('enable_region', kwargs)

    def disable_region(self, **kwargs):
        return self._call_inner_tool('disable_region', kwargs)

    def set_region_status(self, **kwargs):
        return self._call_inner_tool('set_region_status', kwargs)

    def add_region(self, **kwargs):
        return self._call_inner_tool('add_region', kwargs)

    def remove_region(self, **kwargs):
        return self._call_inner_tool('remove_region', kwargs)

    def set_region_resource_quota(self, **kwargs):
        return self._call_inner_tool('set_region_resource_quota', kwargs)

    def add_service(self, **kwargs):
        return self._call_inner_tool('add_service', kwargs)

    def remove_service(self, **kwargs):
        return self._call_inner_tool('remove_service', kwargs)

    def update_region_supported_services(self, **kwargs):
        return self._call_inner_tool('update_region_supported_services', kwargs)

    def update_service_available_regions(self, **kwargs):
        return self._call_inner_tool('update_service_available_regions', kwargs)

    def rename_region(self, **kwargs):
        return self._call_inner_tool('rename_region', kwargs)
