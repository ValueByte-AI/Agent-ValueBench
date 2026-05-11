# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class APIInfo(TypedDict):
    api_id: str
    name: str
    endpoint: str
    status: str
    version: str
    metadata: Dict[str, Any]
    health_status: str  # Assumed correction from 'health_sta'

class APIResourceInfo(TypedDict):
    api_id: str
    resource_type: str
    resource_id: str
    resource_a: Any  # Using Any due to unspecified type

class AccessPolicyInfo(TypedDict):
    policy_id: str
    api_id: str
    allowed_users: List[str]
    roles: List[str]
    rate_lim: int  # Assumed integer for rate limit

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for API management and orchestration.
        """

        # APIs: {api_id: APIInfo}
        self.apis: Dict[str, APIInfo] = {}

        # APIResources: {api_id: {resource_id: APIResourceInfo}}
        self.api_resources: Dict[str, Dict[str, APIResourceInfo]] = {}

        # Access Policies: {policy_id: AccessPolicyInfo}
        self.access_policies: Dict[str, AccessPolicyInfo] = {}

        # Constraints/reminders:
        # - API version and status must be up to date and queryable at all times.
        # - APIResource existence depends on the corresponding API's current state and resource catalog.
        # - Access to API or APIResource queries may depend on the access policy associated with the user/role.
        # - APIs must be healthy (health_status = "healthy") for certain operations to succeed.

    def get_api_by_name(self, name: str) -> dict:
        """
        Retrieve information about an API given its human-readable name.

        Args:
            name (str): The name of the API to search for.

        Returns:
            dict: {
                "success": True,
                "data": APIInfo
            }
            or
            {
                "success": False,
                "error": "API not found"
            }
        Constraints:
            - API version and status must be up to date and queryable at all times.
            - If no API with the given name exists, operation fails.
        """
        for api in self.apis.values():
            if api["name"] == name:
                return {"success": True, "data": api}
        return {"success": False, "error": "API not found"}

    def get_api_by_id(self, api_id: str) -> dict:
        """
        Retrieve information about an API given its api_id.

        Args:
            api_id (str): The unique identifier of the API.

        Returns:
            dict: {
                "success": True,
                "data": APIInfo,  # full API metadata
            }
            or
            {
                "success": False,
                "error": str,  # e.g., "API not found"
            }

        Constraints:
            - The API info must always be queryable if api_id exists.
            - No access policy or health requirements for this query.
        """
        api_info = self.apis.get(api_id)
        if api_info is None:
            return { "success": False, "error": "API not found" }
        return { "success": True, "data": api_info }

    def get_api_status(self, api_id: str) -> dict:
        """
        Retrieve the current operational status of an API.

        Args:
            api_id (str): The unique identifier of the API.

        Returns:
            dict:
                - On success: { "success": True, "data": <status_str> }
                - On failure: { "success": False, "error": "API not found" }

        Constraints:
            - The API must exist in the platform.
            - API status is always up-to-date and queryable.
        """
        api = self.apis.get(api_id)
        if not api:
            return {"success": False, "error": "API not found"}
        return {"success": True, "data": api["status"]}

    def get_api_version(self, api_id: str) -> dict:
        """
        Retrieve the current version string for an API.

        Args:
            api_id (str): The unique identifier of the API.

        Returns:
            dict: 
              On success: { "success": True, "data": <API version string> }
              On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - The API identified by api_id must exist.
            - API version must always be up to date and queryable.
        """
        api = self.apis.get(api_id)
        if not api:
            return { "success": False, "error": "API not found" }
        return { "success": True, "data": api['version'] }

    def get_api_health_status(self, api_id: str) -> dict:
        """
        Retrieve the health status (e.g., 'healthy', 'unhealthy') of the API with the specified api_id.

        Args:
            api_id (str): Unique identifier of the API.

        Returns:
            dict: {
                "success": True,
                "data": { "api_id": str, "health_status": str }
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., API not found).
            }

        Constraints:
            - The API must exist in the platform.
            - No permission check is enforced for this operation.
        """
        api = self.apis.get(api_id)
        if not api:
            return {
                "success": False,
                "error": "API not found"
            }
        return {
            "success": True,
            "data": {
                "api_id": api_id,
                "health_status": api["health_status"]
            }
        }

    def list_apis(self) -> dict:
        """
        List all APIs currently registered in the platform.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[APIInfo],  # List of all APIs' info (may be empty if none)
            }

        Constraints:
            - API version and status must be up to date and queryable at all times.
            - No access check required for this operation.
        """
        api_list = list(self.apis.values())
        return { "success": True, "data": api_list }

    def list_api_versions(self, api_name: str) -> dict:
        """
        List all available versions for a given API, if version history is supported.

        Args:
            api_name (str): The name of the API for which to list all versions.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Sorted list of unique version strings
            }
            or
            {
                "success": False,
                "error": str  # e.g. API name not found
            }

        Constraints:
            - If no API with the given name exists, return failure.
            - Version history is inferred by multiple APIs with the same name but different version fields.
            - Output is deduplicated and sorted (lexicographically).
        """
        # Find all APIs with the given name
        versions = set()
        for api in self.apis.values():
            if api.get("name") == api_name and "version" in api:
                versions.add(api["version"])
        if not versions:
            return {"success": False, "error": "API name not found or has no versions"}
        return {"success": True, "data": sorted(list(versions))}

    def get_api_metadata(self, api_id: str) -> dict:
        """
        Retrieve metadata associated with a specific API.

        Args:
            api_id (str): The ID of the API to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": <metadata_dict>
                    }
                On failure (API not found):
                    {
                        "success": False,
                        "error": "API not found"
                    }

        Constraints:
            - API must exist by api_id in the platform.
        """
        api_info = self.apis.get(api_id)
        if api_info is None:
            return { "success": False, "error": "API not found" }
        return { "success": True, "data": api_info.get("metadata", {}) }

    def list_api_resources(self, api_id: str) -> dict:
        """
        List all resources associated with a specific API.

        Args:
            api_id (str): The ID of the API whose resources should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[APIResourceInfo] # may be empty if API has no resources
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., API does not exist
            }

        Constraints:
            - The API must exist in the platform.
            - Returns empty list if API exists but has no resources.
        """
        if api_id not in self.apis:
            return {"success": False, "error": "API does not exist"}
    
        resources = []
        if api_id in self.api_resources:
            resources = list(self.api_resources[api_id].values())

        return {"success": True, "data": resources}

    def get_api_resource_by_id(self, api_id: str, resource_id: str) -> dict:
        """
        Retrieve a specific APIResource by API ID and resource_id.

        Args:
            api_id (str): The ID of the API to search under.
            resource_id (str): The resource ID within the specified API.

        Returns:
            dict: {
                "success": True,
                "data": APIResourceInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (API not found, resource not found, etc.)
            }

        Constraints:
            - The API must exist in the registry.
            - The resource must exist within the API's resource catalog.
            - APIResource existence depends on the API's state and resource catalog.
        """
        if api_id not in self.apis:
            return {"success": False, "error": f"API with id '{api_id}' does not exist."}

        api_resource_dict = self.api_resources.get(api_id)
        if not api_resource_dict or resource_id not in api_resource_dict:
            return {"success": False, "error": f"Resource with id '{resource_id}' not found for API '{api_id}'."}

        resource_info = api_resource_dict[resource_id]
        return {"success": True, "data": resource_info}

    def api_resource_exists(
        self,
        api_id: str,
        resource_type: str = None,
        resource_id: str = None
    ) -> dict:
        """
        Check for the existence of a specific APIResource by API (`api_id`), optionally filtered
        by resource_type and/or resource_id.

        Args:
            api_id (str): The API's unique identifier.
            resource_type (str, optional): The type of the resource to check for.
            resource_id (str, optional): The resource's unique identifier to look for.

        Returns:
            dict:
                - On success: { "success": True, "exists": <bool> }
                - On error (e.g., API does not exist): { "success": False, "error": <str> }

        Constraints:
            - api_id must exist in the APIs registry.
            - If resource_type/resource_id are provided, apply as filters.
        """
        if api_id not in self.apis:
            return {"success": False, "error": "API ID does not exist"}

        resources = self.api_resources.get(api_id, {})

        for res in resources.values():
            if resource_type is not None and res["resource_type"] != resource_type:
                continue
            if resource_id is not None and res["resource_id"] != resource_id:
                continue
            # Found a matching resource
            return {"success": True, "exists": True}

        # No matching resource found
        return {"success": True, "exists": False}

    def get_access_policy_by_api(self, api_id: str) -> dict:
        """
        Retrieve all access policies governing the specified API.

        Args:
            api_id (str): Identifier of the API whose access policies are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[AccessPolicyInfo],  # List of policies for the api_id (may be empty).
            }
            or
            {
                "success": False,
                "error": str  # e.g., "API not found"
            }

        Constraints:
            - If the API exists but has no policies, returns success with an empty list.
        """
        if api_id not in self.apis:
            return {
                "success": False,
                "error": "API not found"
            }
        policies = [
            policy for policy in self.access_policies.values()
            if policy.get("api_id") == api_id
        ]
        return {
            "success": True,
            "data": policies
        }

    def get_access_policy_by_user(self, user_id: str) -> dict:
        """
        Retrieve all access policies associated with the given user.

        Args:
            user_id (str): The user identifier to match in the allowed_users field of access policies.

        Returns:
            dict: {
                "success": True,
                "data": List[AccessPolicyInfo],  # All policies where user_id is in allowed_users
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must be non-empty string.
            - Operation always succeeds with an empty list if no policies match.
        """
        if not isinstance(user_id, str) or not user_id.strip():
            return { "success": False, "error": "Invalid or missing user_id" }
    
        result = [
            policy for policy in self.access_policies.values()
            if user_id in policy.get("allowed_users", [])
        ]
        return { "success": True, "data": result }

    def get_access_policy_by_role(self, role: str) -> dict:
        """
        Retrieve all access policies associated with a given role.

        Args:
            role (str): The role to search for among all access policies.

        Returns:
            dict:
                - success (bool): Always True if input is valid.
                - data (List[AccessPolicyInfo]): A list of policies where 'role' is present in the policy's 'roles'.

        Constraints:
            - If no policies are found for the provided role, an empty list is returned.
        """
        result = [
            policy for policy in self.access_policies.values()
            if role in policy.get("roles", [])
        ]
        return {"success": True, "data": result}

    def check_user_access_to_api(self, api_id: str, user_id: str) -> dict:
        """
        Determines if a specified user has access to a given API.

        Args:
            api_id (str): The identifier of the API to query.
            user_id (str): The user whose access is being checked.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if user has access, False if not
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., API does not exist)
            }

        Constraints:
            - If API does not exist, return error.
            - Only direct user access (allowed_users) is checked.
            - If no policy gives access, data=False.
        """
        if api_id not in self.apis:
            return {"success": False, "error": "API does not exist"}

        has_access = False
        for policy in self.access_policies.values():
            if policy["api_id"] == api_id and user_id in policy.get("allowed_users", []):
                has_access = True
                break

        return {"success": True, "data": has_access}

    def check_user_access_to_resource(self, user_id: str, api_id: str, resource_id: str) -> dict:
        """
        Determines if a specified user can access a given APIResource.

        Args:
            user_id (str): The user identifier to check access for.
            api_id (str): The API ID to which the resource belongs.
            resource_id (str): The resource ID of the APIResource.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "access_granted": bool,
                            "reason": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - The API and the resource must both exist.
            - There must be an access policy for the API.
            - API must be healthy (health_status == "healthy") for access.
            - User must be in allowed_users (role checks not implemented unless role-user association present).
        """
        # Check API exists
        api_info = self.apis.get(api_id)
        if not api_info:
            return { "success": False, "error": "API not found" }

        # APIResource exists and belongs to the API
        api_resources = self.api_resources.get(api_id, {})
        if resource_id not in api_resources:
            return { "success": False, "error": "Resource not found for API" }

        # API must be healthy for access
        if api_info.get("health_status") != "healthy":
            return {
                "success": True,
                "data": {
                    "access_granted": False,
                    "reason": "API is not healthy"
                }
            }

        # Find all access policies for API.
        # Access should be granted if any policy attached to the API explicitly allows the user.
        access_policies = [
            ap for ap in self.access_policies.values()
            if ap["api_id"] == api_id
        ]

        if not access_policies:
            return {
                "success": False,
                "error": "No access policy found for API"
            }

        for access_policy in access_policies:
            allowed_users = access_policy.get("allowed_users", [])
            if user_id in allowed_users:
                return {
                    "success": True,
                    "data": {
                        "access_granted": True,
                        "reason": "User is directly permitted by access policy"
                    }
                }

        # (Role-based access could be added here if user<->role mapping existed.)

        # If not in allowed_users
        return {
            "success": True,
            "data": {
                "access_granted": False,
                "reason": "User not permitted by access policy"
            }
        }

    def update_api_status(self, api_id: str, new_status: str) -> dict:
        """
        Change the status of a specified API (e.g., enable/disable/maintenance).

        Args:
            api_id (str): The unique identifier for the API to update.
            new_status (str): The new status to set ('enabled', 'disabled', 'maintenance', etc.).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "API status updated to '<new_status>' for API <api_id>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The API must exist.
            - Status is updated immediately to ensure queryability.
            - (Optional) Only certain status values allowed.
        """
        if api_id not in self.apis:
            return { "success": False, "error": "API not found" }

        # Optional: enforce only allowed statuses
        allowed_statuses = {"enabled", "disabled", "maintenance"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'" }

        self.apis[api_id]["status"] = new_status

        return {
            "success": True,
            "message": f"API status updated to '{new_status}' for API {api_id}"
        }

    def update_api_version(self, api_id: str, new_version: str) -> dict:
        """
        Update the version field of a specified API.

        Args:
            api_id (str): The identifier for the API whose version should be updated.
            new_version (str): The new version string to assign.

        Returns:
            dict: 
                On success: { "success": True, "message": "API version updated successfully." }
                On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - API with the given api_id must exist.
            - API version becomes immediately queryable after update.
        """
        api_info = self.apis.get(api_id)
        if api_info is None:
            return { "success": False, "error": "API not found." }
    
        current_version = api_info.get('version', None)
        if current_version == new_version:
            return { "success": True, "message": "API version is already set to the given value." }
    
        api_info['version'] = new_version
        return { "success": True, "message": "API version updated successfully." }

    def update_api_health_status(self, api_id: str, health_status: str) -> dict:
        """
        Set or update the `health_status` of a specified API.

        Args:
            api_id (str): The API identifier to update.
            health_status (str): The new health status value ("healthy", "unhealthy", etc.).

        Returns:
            dict: 
                On success: { "success": True, "message": "API health_status updated" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - `api_id` must exist in the platform.
            - Health status should be updated to reflect the immediate new state.
        """
        api = self.apis.get(api_id)
        if not api:
            return { "success": False, "error": "API with specified api_id does not exist" }

        # Optionally: Validate health_status if desired, e.g., against allowed strings

        api["health_status"] = health_status

        return { "success": True, "message": "API health_status updated" }

    def update_api_metadata(self, api_id: str, metadata_update: dict) -> dict:
        """
        Modify (merge) the metadata dictionary associated with a specific API.

        Args:
            api_id (str): The unique identifier of the API to update.
            metadata_update (dict): New/updated metadata fields to merge into the API's existing metadata.

        Returns:
            dict: {
                "success": True,
                "message": "API metadata updated"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., API not found, bad metadata_update type)
            }

        Constraints:
            - API must exist.
            - Only modifies/merges specified metadata fields; does not replace the whole metadata dict.
        """
        if api_id not in self.apis:
            return { "success": False, "error": "API not found" }
        if not isinstance(metadata_update, dict):
            return { "success": False, "error": "Provided metadata_update is not a dictionary" }

        self.apis[api_id]['metadata'].update(metadata_update)
        return { "success": True, "message": "API metadata updated" }

    def add_new_api(
        self, 
        api_id: str, 
        name: str, 
        endpoint: str, 
        status: str, 
        version: str, 
        metadata: dict, 
        health_status: str
    ) -> dict:
        """
        Registers a new API in the platform.

        Args:
            api_id (str): Unique identifier for the API to register.
            name (str): Name of the API.
            endpoint (str): Endpoint URL or path for the API.
            status (str): Initial status of the API.
            version (str): API version string.
            metadata (dict): Arbitrary metadata to associate with the API.
            health_status (str): Initial health status of the API.

        Returns:
            dict:
                On success: { "success": True, "message": "API registered successfully" }
                On error:   { "success": False, "error": "API with this ID already exists" }

        Constraints:
            - The api_id must not already exist.
            - All supplied fields are required.
        """
        if api_id in self.apis:
            return { "success": False, "error": "API with this ID already exists" }

        api_info: APIInfo = {
            "api_id": api_id,
            "name": name,
            "endpoint": endpoint,
            "status": status,
            "version": version,
            "metadata": metadata,
            "health_status": health_status
        }
        self.apis[api_id] = api_info
        # Optionally initialize resource mapping for this API
        if api_id not in self.api_resources:
            self.api_resources[api_id] = {}

        return { "success": True, "message": "API registered successfully" }

    def remove_api(self, api_id: str) -> dict:
        """
        Deregister an API from the platform. This operation will:
        - Remove the API entry from self.apis
        - Remove all APIResources associated with the api_id
        - Remove all AccessPolicy entries referencing this api_id

        Args:
            api_id (str): The unique identifier of the API to remove.

        Returns:
            dict: {
                "success": True,
                "message": "API <api_id> deregistered successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - API must exist to be removed.
            - All associated APIResources and AccessPolicies must be cleaned up.
        """
        if api_id not in self.apis:
            return { "success": False, "error": f"API with id '{api_id}' does not exist" }

        # Remove the API
        del self.apis[api_id]

        # Remove any resources associated with the API
        if api_id in self.api_resources:
            del self.api_resources[api_id]

        # Remove any access policies referencing this API
        policies_to_remove = [policy_id for policy_id, policy in self.access_policies.items() if policy["api_id"] == api_id]
        for policy_id in policies_to_remove:
            del self.access_policies[policy_id]

        return { "success": True, "message": f"API '{api_id}' deregistered successfully" }

    def add_api_resource(
        self,
        api_id: str,
        resource_type: str,
        resource_id: str,
        resource_a: Any
    ) -> dict:
        """
        Add/register a new resource under a specified API.

        Args:
            api_id (str): The API under which the resource should be registered.
            resource_type (str): The type/kind of the resource (e.g., "person").
            resource_id (str): The unique identifier of this resource under the API.
            resource_a (Any): Resource-specific content/data.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <resource_id> registered under API <api_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Corresponding API must exist and be healthy (health_status == "healthy").
            - resource_id must be unique under the given API.
        """
        # Check API existence
        api = self.apis.get(api_id)
        if api is None:
            return { "success": False, "error": f"API '{api_id}' does not exist." }
    
        # Check API health
        if api.get("health_status") != "healthy":
            return { "success": False, "error": "API is not healthy. Cannot add resource." }

        # Ensure api_resources collection for this API exists
        if api_id not in self.api_resources:
            self.api_resources[api_id] = {}

        # Check for resource_id uniqueness under this API
        if resource_id in self.api_resources[api_id]:
            return { "success": False, "error": f"Resource '{resource_id}' already exists under API '{api_id}'." }

        # Add the resource
        resource_info: APIResourceInfo = {
            "api_id": api_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_a": resource_a
        }
        self.api_resources[api_id][resource_id] = resource_info

        return {
            "success": True,
            "message": f"Resource '{resource_id}' registered under API '{api_id}'."
        }

    def remove_api_resource(self, api_id: str, resource_id: str) -> dict:
        """
        Remove or deregister an existing APIResource.

        Args:
            api_id (str): The ID of the API to which the resource belongs.
            resource_id (str): The ID of the resource to remove.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "APIResource <resource_id> removed from API <api_id>."
                }
                - On failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - The provided API must exist.
            - The specified resource must exist for the API.
            - APIResource existence depends on corresponding API's current state and catalog.
        """
        if api_id not in self.apis:
            return { "success": False, "error": f"API with id '{api_id}' does not exist." }

        if api_id not in self.api_resources or not self.api_resources[api_id]:
            return { "success": False, "error": f"No resources found for API with id '{api_id}'." }

        if resource_id not in self.api_resources[api_id]:
            return { "success": False, "error": f"Resource with id '{resource_id}' does not exist for API '{api_id}'." }

        del self.api_resources[api_id][resource_id]

        # Optionally clean up api_id entry if no more resources remain
        if not self.api_resources[api_id]:
            del self.api_resources[api_id]

        return { "success": True, "message": f"APIResource '{resource_id}' removed from API '{api_id}'." }

    def update_access_policy(
        self,
        policy_id: str,
        allowed_users: list = None,
        roles: list = None,
        rate_lim: int = None,
    ) -> dict:
        """
        Modify the access policy of a specific API by policy_id.
        Any of the allowed_users, roles, or rate_lim fields can be updated, if provided (others are left unchanged).

        Args:
            policy_id (str): The unique policy identifier to update.
            allowed_users (List[str], optional): New list of allowed users. If None, leave unchanged.
            roles (List[str], optional): New list of allowed roles. If None, leave unchanged.
            rate_lim (int, optional): New rate limit integer. If None, leave unchanged.

        Returns:
            dict
                On success: { "success": True, "message": "Access policy updated." }
                On failure: { "success": False, "error": "reason" }
        Constraints:
            - policy_id must exist in self.access_policies.
            - Only updates provided fields.
        """
        if policy_id not in self.access_policies:
            return { "success": False, "error": "Access policy does not exist" }

        # Optional: Type checks for parameters
        if allowed_users is not None and not isinstance(allowed_users, list):
            return { "success": False, "error": "allowed_users must be a list" }
        if roles is not None and not isinstance(roles, list):
            return { "success": False, "error": "roles must be a list" }
        if rate_lim is not None and not isinstance(rate_lim, int):
            return { "success": False, "error": "rate_lim must be int" }

        policy = self.access_policies[policy_id]

        if allowed_users is not None:
            policy['allowed_users'] = allowed_users
        if roles is not None:
            policy['roles'] = roles
        if rate_lim is not None:
            policy['rate_lim'] = rate_lim

        return { "success": True, "message": "Access policy updated." }

    def add_access_policy(
        self, 
        policy_id: str, 
        api_id: str, 
        allowed_users: list, 
        roles: list, 
        rate_lim: int
    ) -> dict:
        """
        Create a new access policy for an API.

        Args:
            policy_id (str): Unique identifier for the access policy.
            api_id (str): The API to which this policy applies (must exist).
            allowed_users (list[str]): List of user identifiers allowed by this policy.
            roles (list[str]): Roles granted by this policy.
            rate_lim (int): Rate limit for API access (must be positive int).

        Returns:
            dict: 
                On success: { "success": True, "message": "Access policy <policy_id> added for API <api_id>" }
                On failure: { "success": False, "error": <reason_string> }

        Constraints:
            - policy_id must be unique (not already present).
            - api_id must refer to an existing API.
            - allowed_users and roles must be lists.
            - rate_lim must be a positive integer.
        """
        # Check uniqueness of policy_id
        if policy_id in self.access_policies:
            return { "success": False, "error": "Policy ID already exists" }
        # Check that api_id exists
        if api_id not in self.apis:
            return { "success": False, "error": "API with the given api_id does not exist" }
        # Validate allowed_users
        if not isinstance(allowed_users, list):
            return { "success": False, "error": "allowed_users must be a list" }
        # Validate roles
        if not isinstance(roles, list):
            return { "success": False, "error": "roles must be a list" }
        # Validate rate_lim
        if not isinstance(rate_lim, int) or rate_lim <= 0:
            return { "success": False, "error": "rate_lim must be a positive integer" }

        policy: AccessPolicyInfo = {
            "policy_id": policy_id,
            "api_id": api_id,
            "allowed_users": allowed_users,
            "roles": roles,
            "rate_lim": rate_lim
        }

        self.access_policies[policy_id] = policy
        return {
            "success": True,
            "message": f"Access policy {policy_id} added for API {api_id}"
        }

    def remove_access_policy(self, policy_id: str) -> dict:
        """
        Delete an access policy from the system.

        Args:
            policy_id (str): The unique identifier of the access policy to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Access policy <policy_id> removed successfully."
            }
            or
            {
                "success": False,
                "error": "Access policy <policy_id> does not exist."
            }

        Constraints:
            - The specified access policy must exist in the system.
        """
        if policy_id not in self.access_policies:
            return {
                "success": False,
                "error": f"Access policy {policy_id} does not exist."
            }

        del self.access_policies[policy_id]
        return {
            "success": True,
            "message": f"Access policy {policy_id} removed successfully."
        }


class APIManagementOrchestrationPlatform(BaseEnv):
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

    def get_api_by_name(self, **kwargs):
        return self._call_inner_tool('get_api_by_name', kwargs)

    def get_api_by_id(self, **kwargs):
        return self._call_inner_tool('get_api_by_id', kwargs)

    def get_api_status(self, **kwargs):
        return self._call_inner_tool('get_api_status', kwargs)

    def get_api_version(self, **kwargs):
        return self._call_inner_tool('get_api_version', kwargs)

    def get_api_health_status(self, **kwargs):
        return self._call_inner_tool('get_api_health_status', kwargs)

    def list_apis(self, **kwargs):
        return self._call_inner_tool('list_apis', kwargs)

    def list_api_versions(self, **kwargs):
        return self._call_inner_tool('list_api_versions', kwargs)

    def get_api_metadata(self, **kwargs):
        return self._call_inner_tool('get_api_metadata', kwargs)

    def list_api_resources(self, **kwargs):
        return self._call_inner_tool('list_api_resources', kwargs)

    def get_api_resource_by_id(self, **kwargs):
        return self._call_inner_tool('get_api_resource_by_id', kwargs)

    def api_resource_exists(self, **kwargs):
        return self._call_inner_tool('api_resource_exists', kwargs)

    def get_access_policy_by_api(self, **kwargs):
        return self._call_inner_tool('get_access_policy_by_api', kwargs)

    def get_access_policy_by_user(self, **kwargs):
        return self._call_inner_tool('get_access_policy_by_user', kwargs)

    def get_access_policy_by_role(self, **kwargs):
        return self._call_inner_tool('get_access_policy_by_role', kwargs)

    def check_user_access_to_api(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_api', kwargs)

    def check_user_access_to_resource(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_resource', kwargs)

    def update_api_status(self, **kwargs):
        return self._call_inner_tool('update_api_status', kwargs)

    def update_api_version(self, **kwargs):
        return self._call_inner_tool('update_api_version', kwargs)

    def update_api_health_status(self, **kwargs):
        return self._call_inner_tool('update_api_health_status', kwargs)

    def update_api_metadata(self, **kwargs):
        return self._call_inner_tool('update_api_metadata', kwargs)

    def add_new_api(self, **kwargs):
        return self._call_inner_tool('add_new_api', kwargs)

    def remove_api(self, **kwargs):
        return self._call_inner_tool('remove_api', kwargs)

    def add_api_resource(self, **kwargs):
        return self._call_inner_tool('add_api_resource', kwargs)

    def remove_api_resource(self, **kwargs):
        return self._call_inner_tool('remove_api_resource', kwargs)

    def update_access_policy(self, **kwargs):
        return self._call_inner_tool('update_access_policy', kwargs)

    def add_access_policy(self, **kwargs):
        return self._call_inner_tool('add_access_policy', kwargs)

    def remove_access_policy(self, **kwargs):
        return self._call_inner_tool('remove_access_policy', kwargs)
