# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from typing import Dict, Any



class ResourceInfo(TypedDict):
    resource_id: str
    resource_type: str
    region: str
    instance_type: str
    status: str
    configuration: Dict[str, Any]
    assigned_security_group: str

class SecurityGroupInfo(TypedDict):
    security_group_id: str
    name: str
    rules: List[Dict[str, Any]]
    associated_resources: List[str]

class DeploymentInfo(TypedDict):
    deployment_id: str
    resources: List[str]
    deployment_time: str
    status: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    permissions: List[str]
    associated_deployments: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a cloud resource management platform.
        """

        # Resources: {resource_id: ResourceInfo}
        # Attributes: resource_id, resource_type, region, instance_type, status, configuration, assigned_security_group
        self.resources: Dict[str, ResourceInfo] = {}

        # Security Groups: {security_group_id: SecurityGroupInfo}
        # Attributes: security_group_id, name, rules, associated_resources
        self.security_groups: Dict[str, SecurityGroupInfo] = {}

        # Deployments: {deployment_id: DeploymentInfo}
        # Attributes: deployment_id, resources, deployment_time, status
        self.deployments: Dict[str, DeploymentInfo] = {}

        # Users: {user_id: UserInfo}
        # Attributes: user_id, name, permissions, associated_deployments
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Resources must be provisioned in supported regions.
        # - Only allowed instance types (e.g., "small", "medium", "large") can be used per resource type.
        # - Security group rules must comply with organizational/network policies.
        # - A resource cannot be assigned to a non-existent or deleted security group.
        # - Resource status must reflect real-world provisioning state (e.g., running, terminated, pending).

    @staticmethod
    def _split_csv_string(value: str) -> List[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    def _normalized_supported_regions(self) -> List[str]:
        raw_value = getattr(self, "supported_regions", [])

        if isinstance(raw_value, str):
            try:
                parsed_value = json.loads(raw_value)
                if isinstance(parsed_value, list):
                    raw_value = parsed_value
            except Exception:
                raw_value = self._split_csv_string(raw_value)

        if isinstance(raw_value, list):
            normalized = [str(item).strip() for item in raw_value if str(item).strip()]
            self.supported_regions = normalized
            return normalized

        return []

    def _normalized_allowed_instance_types(self) -> Any:
        default_mapping = {
            "database": ["small", "medium", "large"],
            "web_server": ["small", "medium", "large", "xlarge"],
            "cache": ["micro", "small", "medium"],
        }
        raw_value = getattr(self, "allowed_instance_types", None)

        if raw_value is None:
            self.allowed_instance_types = copy.deepcopy(default_mapping)
            return copy.deepcopy(default_mapping)

        if isinstance(raw_value, str):
            try:
                parsed_value = json.loads(raw_value)
                if isinstance(parsed_value, (dict, list)):
                    raw_value = parsed_value
                else:
                    raw_value = self._split_csv_string(raw_value)
            except Exception:
                raw_value = self._split_csv_string(raw_value)

        if isinstance(raw_value, list):
            normalized = [str(item).strip() for item in raw_value if str(item).strip()]
            self.allowed_instance_types = normalized
            return normalized

        if isinstance(raw_value, dict):
            normalized = {}
            for resource_type, instance_types in raw_value.items():
                if isinstance(instance_types, str):
                    normalized_types = self._split_csv_string(instance_types)
                elif isinstance(instance_types, list):
                    normalized_types = [
                        str(item).strip() for item in instance_types if str(item).strip()
                    ]
                else:
                    continue
                normalized[str(resource_type)] = normalized_types

            if normalized:
                self.allowed_instance_types = normalized
                return normalized

        self.allowed_instance_types = copy.deepcopy(default_mapping)
        return copy.deepcopy(default_mapping)

    def _recognized_resource_types(self) -> set:
        recognized = {"database", "web_server", "cache", "media_server", "data_processor"}
        for resource in self.resources.values():
            resource_type = resource.get("resource_type")
            if isinstance(resource_type, str) and resource_type.strip():
                recognized.add(resource_type.strip())
        allowed_instance_types = self._normalized_allowed_instance_types()
        if isinstance(allowed_instance_types, dict):
            recognized.update(allowed_instance_types.keys())
        return recognized

    def list_supported_regions(self) -> dict:
        """
        Retrieve the set of regions where resources may be provisioned.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of supported region strings (may be empty if not configured)
            }

        Constraints:
            - Only defined/canonical regions should be returned (not computed from resources).
            - This method does not error but returns an empty list if not configured.
        """
        # Example: supported regions can be specified during initialization or as a static attribute.
        return {"success": True, "data": self._normalized_supported_regions()}

    def list_allowed_instance_types(self, resource_type: str) -> dict:
        """
        Retrieve the list of allowed instance types for a specified resource type
        (e.g., database, web server).

        Args:
            resource_type (str): The type of resource to query.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Valid instance types for the resource_type
            }
            OR
            {
                "success": False,
                "error": str  # If resource_type is invalid
            }
        Constraints:
            - Only allowed/defined resource_types are accepted.
        """
        allowed_instance_types = self._normalized_allowed_instance_types()

        if isinstance(allowed_instance_types, list):
            if (
                not resource_type
                or not isinstance(resource_type, str)
                or resource_type not in self._recognized_resource_types()
            ):
                return {"success": False, "error": "Unknown resource type"}
            return {"success": True, "data": allowed_instance_types}

        if resource_type not in allowed_instance_types:
            return {"success": False, "error": "Unknown resource type"}

        return {"success": True, "data": allowed_instance_types[resource_type]}

    def get_security_group_by_name(self, name: str) -> dict:
        """
        Find and return a security group's information by its name.

        Args:
            name (str): The name of the security group to look up.

        Returns:
            dict:
                - success (bool): Whether the lookup succeeded.
                - data (SecurityGroupInfo): The security group's information, if found.
                - error (str): Error message if not found.

        Constraints:
            - If multiple security groups have the same name, returns the first one found.
            - Returns failure if no security group with the given name exists.
        """
        if not name or not isinstance(name, str):
            return {
                "success": False,
                "error": "Invalid security group name."
            }

        for sg in self.security_groups.values():
            if sg.get("name") == name:
                return {
                    "success": True,
                    "data": sg
                }
        return {
            "success": False,
            "error": f"Security group with name '{name}' not found."
        }

    def list_security_groups(self) -> dict:
        """
        List all security groups defined in the environment.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SecurityGroupInfo]  # All security group info objects, may be empty if none exist.
            }
        """
        return {
            "success": True,
            "data": list(self.security_groups.values())
        }

    def get_security_group_rules(self, security_group_id: str) -> dict:
        """
        Retrieve the network/access policy rules for a given security group.

        Args:
            security_group_id (str): The unique ID of the security group to query.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, Any]],  # List of rule dictionaries; may be empty if no rules
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., security group does not exist)
            }

        Constraints:
            - The specified security group must exist.
        """
        sg = self.security_groups.get(security_group_id)
        if sg is None:
            return {"success": False, "error": "Security group does not exist"}
        rules = sg.get("rules", [])
        return {"success": True, "data": rules}

    def get_resource_info(self, resource_id: str) -> dict:
        """
        Retrieve all details of a resource with the specified resource_id.

        Args:
            resource_id (str): The unique identifier for the resource.

        Returns:
            dict: 
                If resource exists:
                    { "success": True, "data": ResourceInfo }
                If resource does not exist:
                    { "success": False, "error": "Resource not found" }
        Constraints:
            - The resource must exist in the platform for retrieval.
        """
        resource_info = self.resources.get(resource_id)
        if resource_info is None:
            return { "success": False, "error": "Resource not found" }
        return { "success": True, "data": resource_info }

    def list_resources_by_type_and_region(self, resource_type: str, region: str) -> dict:
        """
        List all resources of a specific type within a given region.

        Args:
            resource_type (str): The type of resource to filter by.
            region (str): The region in which to filter resources.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[ResourceInfo],  # List (possibly empty) of matching resources' info,
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error.
                }

        Constraints:
            - No failure if zero matches found. Returns an empty list in that case.
            - No permissions checks are performed.
        """
        if not resource_type or not region:
            return {"success": False, "error": "Both resource_type and region are required parameters"}
    
        result = [
            resource_info for resource_info in self.resources.values()
            if resource_info["resource_type"] == resource_type and resource_info["region"] == region
        ]
        return {"success": True, "data": result}

    def get_resource_status(self, resource_id: str) -> dict:
        """
        Retrieve the operational status (e.g., running, terminated, pending) of the specified resource.

        Args:
            resource_id (str): The unique identifier of the resource.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str  # Status string such as "running", "terminated", or "pending"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message indicating reason for failure.
                    }

        Constraints:
            - The resource must exist in the system.
        """
        resource = self.resources.get(resource_id)
        if not resource:
            return { "success": False, "error": "Resource not found" }
        return { "success": True, "data": resource["status"] }

    def list_deployments(self) -> dict:
        """
        List all deployment objects in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DeploymentInfo],  # list of all deployments, may be empty
            }
        """
        deployments_list = list(self.deployments.values())
        return { "success": True, "data": deployments_list }

    def get_deployment_info(self, deployment_id: str) -> dict:
        """
        Retrieve details and the associated resource information for a specific deployment.

        Args:
            deployment_id (str): The unique identifier for the deployment.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "deployment_id": str,
                    "deployment_time": str,
                    "status": str,
                    "resources": List[ResourceInfo],  # List of resource info dicts
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The deployment_id must exist in the platform.
            - Missing resources in deployment's list are not included in result.
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return {"success": False, "error": "Deployment not found"}

        # Gather resource info for all resource ids in deployment
        resource_infos = [
            self.resources[res_id]
            for res_id in deployment['resources']
            if res_id in self.resources
        ]

        result = {
            "deployment_id": deployment["deployment_id"],
            "deployment_time": deployment["deployment_time"],
            "status": deployment["status"],
            "resources": resource_infos
        }

        return {"success": True, "data": result}

    def get_user_permissions(self, user_id: str) -> dict:
        """
        Retrieve the list of permissions associated with a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of the user's permissions
            }
            or
            {
                "success": False,
                "error": str,  # Error message if the user does not exist
            }

        Constraints:
            - user_id must exist in the platform's records.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User does not exist" }

        # permissions is always a list (possibly empty)
        return { "success": True, "data": user_info.get("permissions", []) }

    def create_security_group(self, name: str, rules: list) -> dict:
        """
        Create a new security group with the specified name and rules if one does not already exist.

        Args:
            name (str): The human-readable name for the security group (must be unique).
            rules (List[Dict[str, Any]]): The list of network/access policy rules to associate with this group.

        Returns:
            dict: {
                "success": True,
                "message": "Security group '<name>' created with ID <security_group_id>."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Security group name must be unique.
            - Rules must comply with organizational/network policies (basic compliance check here).
        """
        # Name must not be empty
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Security group name must be a non-empty string."}

        # Check if a security group with the same name already exists
        for sg in self.security_groups.values():
            if sg['name'] == name:
                return {"success": False, "error": "Security group with the given name already exists."}

        # Rule set must be a list and at least one rule (can adjust this policy as needed)
        if not isinstance(rules, list):
            return {"success": False, "error": "Rules must be provided as a list."}
    
        # Placeholder for rule compliance check (always True here)
        def rules_compliant(rule_list):
            # Implement real checks as needed
            return True

        if not rules_compliant(rules):
            return {"success": False, "error": "Security group rules do not comply with network policy."}
    
        # Generate a unique security_group_id
        security_group_id = str(uuid.uuid4())

        sg_info = {
            "security_group_id": security_group_id,
            "name": name,
            "rules": rules,
            "associated_resources": []
        }
        self.security_groups[security_group_id] = sg_info

        return {
            "success": True,
            "message": f"Security group '{name}' created with ID {security_group_id}."
        }

    def update_security_group_rules(self, security_group_id: str, new_rules: list) -> dict:
        """
        Modify or extend rules for an existing security group.

        Args:
            security_group_id (str): ID of the security group whose rules should be updated.
            new_rules (List[Dict[str, Any]]): The new list of rules to set (will replace current rules).

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Security group rules updated for <security_group_id>" }
                On failure:
                    { "success": False, "error": "Security group does not exist" }
                    { "success": False, "error": "One or more rules violate organizational policies" }

        Constraints:
            - Security group must exist.
            - All new rules must comply with organizational/network policies (mocked check).
        """

        # Check if the security group exists
        if security_group_id not in self.security_groups:
            return { "success": False, "error": "Security group does not exist" }

        # Placeholder/mock compliance check for policies
        # For the demo, any rule with a forbidden field or value is rejected
        # (e.g., disallow port 22 ingress from "0.0.0.0/0" for SSH openness)
        forbidden_ports = [22]  # Example policy
        for rule in new_rules:
            if (
                ("port" in rule and rule.get("port") in forbidden_ports) and
                ("cidr" in rule and rule.get("cidr") == "0.0.0.0/0") and
                (rule.get("protocol", "").lower() in ["tcp", "all"])
            ):
                return {
                    "success": False,
                    "error": "One or more rules violate organizational policies"
                }

        # If compliance check passes, update the rules (replace)
        self.security_groups[security_group_id]["rules"] = new_rules

        return {
            "success": True,
            "message": f"Security group rules updated for {security_group_id}"
        }


    def provision_resource(
        self,
        resource_type: str,
        region: str,
        instance_type: str,
        configuration: Dict[str, Any],
        assigned_security_group: str,
    ) -> dict:
        """
        Instantiate (create) a new resource (e.g., database, web server) in the platform.

        Args:
            resource_type (str): Type of resource to provision (e.g., "web_server").
            region (str): Cloud region for provisioning.
            instance_type (str): Sizing of resource (e.g. "small", "medium", "large").
            configuration (dict): Resource-specific configuration settings.
            assigned_security_group (str): Security group ID to assign to the new resource.

        Returns:
            dict:
              - If successful: {"success": True, "message": "Resource <resource_id> provisioned."}
              - If failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Region must be in supported regions.
            - Instance type must be allowed for the given resource type.
            - Security group must exist.
            - Resource ID is generated and must be unique.
            - Resource status is set to "pending" on creation.
        """
        # Check for platform configuration
        if not hasattr(self, 'supported_regions') or not hasattr(self, 'allowed_instance_types'):
            return {"success": False, "error": "Supported regions/instance types configuration not found."}

        supported_regions = self._normalized_supported_regions()
        allowed_instance_types = self._normalized_allowed_instance_types()

        if region not in supported_regions:
            return {"success": False, "error": f"Region '{region}' is not supported."}

        if isinstance(allowed_instance_types, list):
            if resource_type not in self._recognized_resource_types():
                return {"success": False, "error": f"Resource type '{resource_type}' is not recognized."}
            if instance_type not in allowed_instance_types:
                return {
                    "success": False,
                    "error": f"Instance type '{instance_type}' is not allowed for resource type '{resource_type}'."
                }
        else:
            if resource_type not in allowed_instance_types:
                return {"success": False, "error": f"Resource type '{resource_type}' is not recognized."}

            if instance_type not in allowed_instance_types[resource_type]:
                return {
                    "success": False,
                    "error": f"Instance type '{instance_type}' is not allowed for resource type '{resource_type}'."
                }

        if assigned_security_group not in self.security_groups:
            return {
                "success": False,
                "error": f"Assigned security group '{assigned_security_group}' does not exist."
            }

        if not isinstance(configuration, dict):
            return {
                "success": False,
                "error": "Configuration must be a dictionary."
            }

        # Generate resource_id
        resource_id = str(uuid.uuid4())
        if resource_id in self.resources:
            return {"success": False, "error": "Resource ID generation conflict, please try again."}

        # Create resource structure
        new_resource = {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "region": region,
            "instance_type": instance_type,
            "status": "pending",
            "configuration": configuration,
            "assigned_security_group": assigned_security_group
        }

        # Add to resource pool
        self.resources[resource_id] = new_resource

        # Attach resource to security group
        # Ensure no duplicates in the associated_resources list
        sg = self.security_groups[assigned_security_group]
        if resource_id not in sg["associated_resources"]:
            sg["associated_resources"].append(resource_id)

        return {
            "success": True,
            "message": f"Resource '{resource_id}' provisioned."
        }

    def assign_security_group_to_resource(self, resource_id: str, security_group_id: str) -> dict:
        """
        Attach a valid existing security group to a resource.
    
        Args:
            resource_id (str): The ID of the target resource.
            security_group_id (str): The ID of the security group to assign.
    
        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Security group <security_group_id> assigned to resource <resource_id>"
                  }
                - On failure: {
                    "success": False,
                    "error": "<description>"
                  }
    
        Constraints:
            - The resource must exist.
            - The security group must exist (cannot be non-existent or deleted).
            - Updates both the resource and security group objects for consistent linkage.
        """
        # Check if resource exists
        if resource_id not in self.resources:
            return { "success": False, "error": f"Resource {resource_id} does not exist" }
    
        # Check if security group exists
        if security_group_id not in self.security_groups:
            return { "success": False, "error": f"Security group {security_group_id} does not exist" }

        resource = self.resources[resource_id]
        new_group = self.security_groups[security_group_id]
        old_group_id = resource.get("assigned_security_group")

        # Remove from old security group's resource list if necessary
        if old_group_id and old_group_id != security_group_id:
            old_group = self.security_groups.get(old_group_id)
            if old_group and resource_id in old_group.get("associated_resources", []):
                old_group["associated_resources"].remove(resource_id)

        # Assign new group to resource
        resource["assigned_security_group"] = security_group_id

        # Add resource to new group's associated_resources, if not present
        if resource_id not in new_group.get("associated_resources", []):
            new_group["associated_resources"].append(resource_id)

        return { "success": True, "message": f"Security group {security_group_id} assigned to resource {resource_id}" }

    def create_deployment(self, deployment_id: str, resource_ids: list, deployment_time: str, status: str) -> dict:
        """
        Creates a new deployment object linking a set of resources for lifecycle tracking.
        Args:
            deployment_id (str): Unique identifier for the deployment.
            resource_ids (List[str]): List of existing resource IDs to include in the deployment.
            deployment_time (str): Timestamp for deployment creation (ISO string or similar).
            status (str): Initial status for the deployment.
        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Deployment <deployment_id> created with resources: <ids>"
                }
            On error:
                {
                    "success": False,
                    "error": "<reason>"
                }
        Constraints:
            - All resource_ids must exist in self.resources.
            - deployment_id must be unique.
        """
        if not deployment_id or not isinstance(deployment_id, str):
            return {"success": False, "error": "deployment_id must be a non-empty string."}

        if deployment_id in self.deployments:
            return {"success": False, "error": "Deployment ID already exists."}

        if not isinstance(resource_ids, list) or not all(isinstance(rid, str) for rid in resource_ids):
            return {"success": False, "error": "resource_ids must be a list of strings."}

        missing_resources = [rid for rid in resource_ids if rid not in self.resources]
        if missing_resources:
            return {"success": False, "error": f"Resource(s) do not exist: {', '.join(missing_resources)}"}

        # Compose deployment info:
        deployment_info = {
            "deployment_id": deployment_id,
            "resources": resource_ids,
            "deployment_time": deployment_time,
            "status": status
        }
        self.deployments[deployment_id] = deployment_info

        return {
            "success": True,
            "message": f"Deployment {deployment_id} created with resources: {', '.join(resource_ids)}"
        }

    def update_resource_status(self, resource_id: str, new_status: str) -> dict:
        """
        Change the operational status of a resource (e.g., move to running, terminated).

        Args:
            resource_id (str): The unique identifier of the resource.
            new_status (str): The new status for the resource. Allowed values: 'running', 'terminated', 'pending'.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <resource_id> status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - Resource must exist.
            - new_status must be one of ['running', 'terminated', 'pending'].
            - Resource status must always reflect real provisioning state.
        """
        allowed_statuses = {"running", "terminated", "pending"}
        if resource_id not in self.resources:
            return {"success": False, "error": f"Resource {resource_id} does not exist"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed: running, terminated, pending"}
        # Update status
        self.resources[resource_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Resource {resource_id} status updated to {new_status}"
        }

    def update_resource_configuration(self, resource_id: str, new_configuration: Dict[str, Any]) -> dict:
        """
        Change or set configuration parameters for an existing resource.

        Args:
            resource_id (str): The ID of the resource to update.
            new_configuration (Dict[str, Any]): Configuration values to set/merge onto existing config.

        Returns:
            dict: {
                "success": True,
                "message": "Configuration updated for resource <resource_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Resource must exist.
            - Resource must not be in 'terminated' status.
            - new_configuration must be a dict.
            - Performs an update/merge onto existing configuration dictionary.
        """
        # Check for existence
        resource = self.resources.get(resource_id)
        if not resource:
            return {"success": False, "error": f"Resource {resource_id} does not exist"}

        # Configuration must be a dict
        if not isinstance(new_configuration, dict):
            return {"success": False, "error": "Configuration must be a dictionary"}

        # Do not allow update if resource is terminated
        if resource["status"].lower() == "terminated":
            return {
                "success": False,
                "error": f"Cannot update configuration of terminated resource {resource_id}"
            }

        # Update (merge/replace) configuration
        resource["configuration"].update(new_configuration)

        # (optional: update the resource in self.resources, though 'resource' is a reference)
        self.resources[resource_id] = resource

        return {"success": True, "message": f"Configuration updated for resource {resource_id}"}

    def decommission_resource(self, resource_id: str) -> dict:
        """
        Mark the specified resource as terminated and remove all associations,
        reflecting de-provisioning from the system.

        Args:
            resource_id (str): Unique identifier of the resource to decommission.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <id> successfully decommissioned"
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Resource must exist.
            - Status will be set to 'terminated' (if not already).
            - Resource will be removed from all SecurityGroup.associated_resources lists.
            - No deletion from deployments to preserve history.
        """
        # Check resource existence
        resource = self.resources.get(resource_id)
        if not resource:
            return { "success": False, "error": "Resource does not exist" }

        # Idempotent: If already terminated, just ensure associations are also cleaned up
        resource["status"] = "terminated"

        # Remove from associated security group's resource list
        assigned_sg_id = resource.get("assigned_security_group")
        if assigned_sg_id and assigned_sg_id in self.security_groups:
            sg = self.security_groups[assigned_sg_id]
            if resource_id in sg["associated_resources"]:
                sg["associated_resources"].remove(resource_id)
            # Optional: unset assigned_security_group on the resource?
            resource["assigned_security_group"] = ""

        # Clean up from any other security groups (robustness, in case of data issues)
        for sg in self.security_groups.values():
            if resource_id in sg["associated_resources"]:
                sg["associated_resources"].remove(resource_id)

        # (Optional) Could also remove resource from self.resources, but usually "terminated" means marked, not deleted.

        return {
            "success": True,
            "message": f"Resource {resource_id} successfully decommissioned"
        }


class CloudResourceManagementPlatform(BaseEnv):
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
            if key == "supported_regions" and isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        value = parsed
                except Exception:
                    value = [item.strip() for item in value.split(",") if item.strip()]
            elif key == "allowed_instance_types" and isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (dict, list)):
                        value = parsed
                except Exception:
                    value = [item.strip() for item in value.split(",") if item.strip()]
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

    def list_supported_regions(self, **kwargs):
        return self._call_inner_tool('list_supported_regions', kwargs)

    def list_allowed_instance_types(self, **kwargs):
        return self._call_inner_tool('list_allowed_instance_types', kwargs)

    def get_security_group_by_name(self, **kwargs):
        return self._call_inner_tool('get_security_group_by_name', kwargs)

    def list_security_groups(self, **kwargs):
        return self._call_inner_tool('list_security_groups', kwargs)

    def get_security_group_rules(self, **kwargs):
        return self._call_inner_tool('get_security_group_rules', kwargs)

    def get_resource_info(self, **kwargs):
        return self._call_inner_tool('get_resource_info', kwargs)

    def list_resources_by_type_and_region(self, **kwargs):
        return self._call_inner_tool('list_resources_by_type_and_region', kwargs)

    def get_resource_status(self, **kwargs):
        return self._call_inner_tool('get_resource_status', kwargs)

    def list_deployments(self, **kwargs):
        return self._call_inner_tool('list_deployments', kwargs)

    def get_deployment_info(self, **kwargs):
        return self._call_inner_tool('get_deployment_info', kwargs)

    def get_user_permissions(self, **kwargs):
        return self._call_inner_tool('get_user_permissions', kwargs)

    def create_security_group(self, **kwargs):
        return self._call_inner_tool('create_security_group', kwargs)

    def update_security_group_rules(self, **kwargs):
        return self._call_inner_tool('update_security_group_rules', kwargs)

    def provision_resource(self, **kwargs):
        return self._call_inner_tool('provision_resource', kwargs)

    def assign_security_group_to_resource(self, **kwargs):
        return self._call_inner_tool('assign_security_group_to_resource', kwargs)

    def create_deployment(self, **kwargs):
        return self._call_inner_tool('create_deployment', kwargs)

    def update_resource_status(self, **kwargs):
        return self._call_inner_tool('update_resource_status', kwargs)

    def update_resource_configuration(self, **kwargs):
        return self._call_inner_tool('update_resource_configuration', kwargs)

    def decommission_resource(self, **kwargs):
        return self._call_inner_tool('decommission_resource', kwargs)
