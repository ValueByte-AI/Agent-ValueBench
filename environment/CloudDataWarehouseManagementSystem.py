# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



# Represents resource allocation and operational parameters
class ConfigurationInfo(TypedDict):
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    region: str
    scaling_policy: str

# Tracks per-warehouse usage stats
class UsageStatisticsInfo(TypedDict):
    warehouse_id: str
    cpu_usage_hours: float
    storage_used_gb: float
    queries_executed: int
    last_accessed_timestamp: str

# Maps users to warehouses and permissions
class AccessControlInfo(TypedDict):
    warehouse_id: str
    user_id: str
    permission_level: str  # e.g., read, write, admin

# Data warehouse instance metadata
class DataWarehouseInfo(TypedDict):
    warehouse_id: str
    name: str
    creation_timestamp: str
    status: str  # e.g., active, deleted, deleting
    configuration: ConfigurationInfo
    usage_statistics: UsageStatisticsInfo
    owner_id: str

# User info
class UserInfo(TypedDict):
    user_id: str
    username: str
    role: str
    account_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # DataWarehouses: {warehouse_id: DataWarehouseInfo}
        self.data_warehouses: Dict[str, DataWarehouseInfo] = {}

        # UsageStatistics: {warehouse_id: UsageStatisticsInfo}
        self.usage_statistics: Dict[str, UsageStatisticsInfo] = {}

        # AccessControl: List of permissions (warehouse_id, user_id, permission_level)
        self.access_controls: List[AccessControlInfo] = []

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraint annotations:
        # - Only users with appropriate permission_level (admin) in AccessControl can delete DataWarehouse instances.
        # - Cannot delete a warehouse with status already "deleted" or "deleting".
        # - Configuration and UsageStatistics are linked to existing DataWarehouse instances only.
        # - Deleting a DataWarehouse also marks associated AccessControl and UsageStatistics as inactive or archived.

    def get_warehouse_by_id(self, warehouse_id: str) -> dict:
        """
        Retrieve the full metadata and status of a given data warehouse by warehouse_id.

        Args:
            warehouse_id (str): Unique identifier of the data warehouse.

        Returns:
            dict:
              On success:
                {
                    "success": True,
                    "data": DataWarehouseInfo
                }
              On failure (warehouse_id does not exist):
                {
                    "success": False,
                    "error": "Warehouse not found"
                }
        Constraints:
            - Warehouse must exist in the system.
            - No special permissions or status constraints for reading.
        """
        if warehouse_id not in self.data_warehouses:
            return {"success": False, "error": "Warehouse not found"}
        return {"success": True, "data": self.data_warehouses[warehouse_id]}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info based on user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User's information if found
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if there is no such user
            }

        Constraints:
            - No special constraints; simply checks for user existence.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user info based on username.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Behavior:
            - If a user with the specified username exists, returns their info.
            - If not found, returns an appropriate error.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return { "success": True, "data": user_info }
        return { "success": False, "error": "User not found" }

    def get_access_control_for_warehouse_and_user(self, warehouse_id: str, user_id: str) -> dict:
        """
        Retrieve the permission_level (and full AccessControlInfo) for a given user and warehouse.

        Args:
            warehouse_id (str): The warehouse ID.
            user_id (str): The user ID.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": AccessControlInfo  # The entry with warehouse_id, user_id, and permission_level
                }
                or
                {
                    "success": False,
                    "error": "Access control entry not found for user and warehouse"
                }

        Constraints:
            - Only checks access_control table; does not verify user or warehouse existence in their own tables.
        """
        for ace in self.access_controls:
            if ace["warehouse_id"] == warehouse_id and ace["user_id"] == user_id:
                return {"success": True, "data": ace}
        return {"success": False, "error": "Access control entry not found for user and warehouse"}

    def list_warehouses_by_status(self, status: str) -> dict:
        """
        List all data warehouses with the specified status.

        Args:
            status (str): The status to filter warehouses by (e.g., "active", "deleting", "deleted").

        Returns:
            dict: {
                "success": True,
                "data": List[DataWarehouseInfo],  # List of warehouse metadata matching status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., missing or invalid status)
            }

        Constraints:
            - Status must be a non-empty string.
            - If no warehouses match the status, return an empty list with success.
        """
        if not isinstance(status, str) or not status.strip():
            return { "success": False, "error": "Status must be a non-empty string." }

        result = [
            warehouse_info for warehouse_info in self.data_warehouses.values()
            if warehouse_info["status"] == status
        ]
        return { "success": True, "data": result }

    def get_usage_statistics_for_warehouse(self, warehouse_id: str) -> dict:
        """
        Retrieve usage statistics for a given warehouse.

        Args:
            warehouse_id (str): The unique identifier of the warehouse.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UsageStatisticsInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - warehouse_id must correspond to an existing DataWarehouse.
            - If no usage statistics exist for the warehouse, returns failure.
        """
        if warehouse_id not in self.data_warehouses:
            return { "success": False, "error": "Warehouse does not exist" }
    
        usage_stats = self.usage_statistics.get(warehouse_id)
        if not usage_stats:
            return { "success": False, "error": "No usage statistics found for this warehouse" }
    
        return { "success": True, "data": usage_stats }

    def get_configuration_for_warehouse(self, warehouse_id: str) -> dict:
        """
        Retrieve the configuration (resource allocation and operational settings) for a given data warehouse.

        Args:
            warehouse_id (str): The unique identifier of the warehouse.

        Returns:
            dict: {
                "success": True,
                "data": ConfigurationInfo
            }
            or {
                "success": False,
                "error": str  # Error message if warehouse does not exist
            }

        Constraints:
            - The warehouse must exist.
            - No access control checks required for this query.
        """
        warehouse = self.data_warehouses.get(warehouse_id)
        if warehouse is None:
            return {"success": False, "error": "Warehouse does not exist"}

        config = warehouse.get("configuration")
        return {"success": True, "data": config}

    def list_access_control_entries_for_warehouse(self, warehouse_id: str) -> dict:
        """
        List all access control entries (user_id and permission_level) for a specified data warehouse.

        Args:
            warehouse_id (str): ID of the warehouse.

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "user_id": str,
                    "permission_level": str
                }]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Warehouse must exist.
        """
        if warehouse_id not in self.data_warehouses:
            return {"success": False, "error": "Warehouse does not exist"}

        entries = [
            {
                "user_id": ac["user_id"],
                "permission_level": ac["permission_level"]
            }
            for ac in self.access_controls
            if ac["warehouse_id"] == warehouse_id
        ]

        return { "success": True, "data": entries }

    def delete_data_warehouse(self, warehouse_id: str, user_id: str) -> dict:
        """
        Mark a data warehouse and all its associated AccessControl and UsageStatistics as deleted/inactive,
        after performing necessary permission and status checks.

        Args:
            warehouse_id (str): The identifier of the warehouse to delete.
            user_id (str): The user attempting the delete operation.

        Returns:
            dict: 
                On success: { "success": True, "message": "Warehouse deleted successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only users with admin permission on the warehouse can perform deletion.
            - Warehouse must not be already deleted or deleting.
            - Associated UsageStatistics and AccessControl entries are archived/inactivated.
        """

        # Check warehouse existence
        warehouse = self.data_warehouses.get(warehouse_id)
        if warehouse is None:
            return {"success": False, "error": "Warehouse not found"}

        # Check user existence
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        # Check warehouse status
        if warehouse["status"] in ("deleted", "deleting"):
            return {"success": False, "error": f"Warehouse already {warehouse['status']}"}

        # Check admin access control
        has_admin = any(
            ac["warehouse_id"] == warehouse_id and
            ac["user_id"] == user_id and
            ac["permission_level"].lower() == "admin"
            for ac in self.access_controls
        )
        if not has_admin:
            return {"success": False, "error": "Permission denied: User is not an admin for this warehouse"}

        # Mark the warehouse as deleted
        warehouse["status"] = "deleted"

        # Archive UsageStatistics if present
        usage_stats = self.usage_statistics.get(warehouse_id)
        if usage_stats:
            usage_stats["archived"] = True  # Add 'archived' flag if not present
            # Optionally add a timestamp or remove from active usage statistics

        # Archive all AccessControl entries for this warehouse
        for ac in self.access_controls:
            if ac["warehouse_id"] == warehouse_id:
                ac["inactive"] = True

        # Ensure the reference in the warehouse metadata
        warehouse["usage_statistics"]["archived"] = True

        return {"success": True, "message": "Warehouse deleted successfully"}


    def create_data_warehouse(
        self,
        warehouse_id: str,
        name: str,
        owner_id: str,
        configuration: dict
    ) -> dict:
        """
        Create a new data warehouse instance with supplied configuration and owner.

        Args:
            warehouse_id (str): Unique identifier for the warehouse.
            name (str): Human-readable warehouse name.
            owner_id (str): User ID of the warehouse owner (must exist and be active).
            configuration (dict): Warehouse configuration (cpu_cores, memory_gb, storage_gb, region, scaling_policy).

        Returns:
            dict: {
                "success": True,
                "message": "Data warehouse created successfully."
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
        - warehouse_id must be unique.
        - owner_id must be a valid, active user.
        - All required config fields must be provided.
        - Sets initial status to "active" and creates basic usage statistics and access control.
        """

        REQUIRED_CONFIG_FIELDS = {'cpu_cores', 'memory_gb', 'storage_gb', 'region', 'scaling_policy'}

        # Check warehouse_id uniqueness
        if warehouse_id in self.data_warehouses:
            return {"success": False, "error": "Warehouse ID already exists."}

        # Check owner validity
        user = self.users.get(owner_id)
        if not user or user["account_status"] != "active":
            return {"success": False, "error": "Owner user does not exist or is not active."}

        # Validate configuration
        missing = [field for field in REQUIRED_CONFIG_FIELDS if field not in configuration]
        if missing:
            return {"success": False, "error": f"Missing configuration fields: {', '.join(missing)}"}

        now_ts = datetime.utcnow().isoformat()

        # Compose ConfigurationInfo to ensure all fields are present
        conf: ConfigurationInfo = {
            "cpu_cores": int(configuration["cpu_cores"]),
            "memory_gb": int(configuration["memory_gb"]),
            "storage_gb": int(configuration["storage_gb"]),
            "region": configuration["region"],
            "scaling_policy": configuration["scaling_policy"]
        }

        usage_stats: UsageStatisticsInfo = {
            "warehouse_id": warehouse_id,
            "cpu_usage_hours": 0.0,
            "storage_used_gb": 0.0,
            "queries_executed": 0,
            "last_accessed_timestamp": now_ts
        }

        warehouse_info: DataWarehouseInfo = {
            "warehouse_id": warehouse_id,
            "name": name,
            "creation_timestamp": now_ts,
            "status": "active",
            "configuration": conf,
            "usage_statistics": usage_stats,
            "owner_id": owner_id
        }

        # Store the new warehouse record
        self.data_warehouses[warehouse_id] = warehouse_info

        # Store usage statistics
        self.usage_statistics[warehouse_id] = usage_stats

        # Grant admin permission to owner
        self.access_controls.append({
            "warehouse_id": warehouse_id,
            "user_id": owner_id,
            "permission_level": "admin"
        })

        return {"success": True, "message": "Data warehouse created successfully."}

    def update_warehouse_configuration(self, warehouse_id: str, user_id: str, new_configuration: dict) -> dict:
        """
        Modify the configuration parameters of an existing warehouse.
    
        Args:
            warehouse_id (str): ID of the data warehouse to update.
            user_id (str): ID of the user requesting the update.
            new_configuration (dict): New configuration parameters (should conform to ConfigurationInfo schema).
    
        Returns:
            dict: 
                {"success": True, "message": "Warehouse configuration updated."}
                or
                {"success": False, "error": "<reason>"}
    
        Constraints:
            - User must exist and have 'admin' permission_level for the warehouse.
            - Warehouse must exist and not be in 'deleted' or 'deleting' status.
            - Configuration must match expected parameters.
        """
        # Check warehouse existence
        wh = self.data_warehouses.get(warehouse_id)
        if not wh:
            return {"success": False, "error": "Warehouse does not exist."}

        # Check warehouse status
        if wh["status"] in ("deleted", "deleting"):
            return {"success": False, "error": f"Cannot update configuration for warehouse in status '{wh['status']}'."}

        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check user permissions
        authorized = False
        for ac in self.access_controls:
            if ac["warehouse_id"] == warehouse_id and ac["user_id"] == user_id and ac["permission_level"] == "admin":
                authorized = True
                break
        if not authorized:
            return {"success": False, "error": "Permission denied: user lacks admin privileges for this warehouse."}

        # Basic schema check (more detailed validation can be added as needed)
        required_keys = {"cpu_cores", "memory_gb", "storage_gb", "region", "scaling_policy"}
        if not all(key in new_configuration for key in required_keys):
            return {"success": False, "error": "New configuration is missing one or more required fields."}

        # Update configuration
        wh["configuration"] = dict(new_configuration)  # Replace with new settings

        # Optionally, updating status or modified timestamp could be done here

        return {"success": True, "message": "Warehouse configuration updated."}

    def archive_usage_statistics_for_warehouse(self, warehouse_id: str) -> dict:
        """
        Archives (marks as inactive) the usage statistics for a warehouse. 

        Args:
            warehouse_id (str): The unique identifier of the warehouse.

        Returns:
            dict: {
                "success": True,
                "message": "Usage statistics for warehouse <warehouse_id> archived."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        
        Constraints:
            - Warehouse must exist.
            - Warehouse status must be "deleted" or "deleting".
            - Usage statistics must exist for the warehouse.
            - The 'archived' key will be added/set to True in statistics.
        """
        warehouse_info = self.data_warehouses.get(warehouse_id)
        if not warehouse_info:
            return { "success": False, "error": "Warehouse not found." }
        if warehouse_info["status"] not in ("deleted", "deleting"):
            return { 
                "success": False, 
                "error": "Cannot archive usage statistics for a warehouse that is not deleted or deleting."
            }
        usage_stat = self.usage_statistics.get(warehouse_id)
        if not usage_stat:
            return { "success": False, "error": "Usage statistics not found for this warehouse." }
        usage_stat["archived"] = True  # Add or update archived flag
        return { 
            "success": True, 
            "message": f"Usage statistics for warehouse {warehouse_id} archived." 
        }

    def archive_access_control_for_warehouse(self, warehouse_id: str) -> dict:
        """
        Mark all access control entries for the given warehouse as archived (inactive).
    
        Args:
            warehouse_id (str): The warehouse to archive access control for.
        
        Returns:
            dict: 
              - On success:
                  { "success": True, "message": "All access control entries for warehouse archived." }
              - On error (warehouse does not exist):
                  { "success": False, "error": "Warehouse does not exist." }
              
        Constraints:
          - Only warehouses that exist can be archived.
          - Archiving sets 'archived' key in AccessControlInfo to True for all matching entries.
          - If no entries found, return success with message.
        """
        if warehouse_id not in self.data_warehouses:
            return { "success": False, "error": "Warehouse does not exist." }
    
        any_updated = False
        for entry in self.access_controls:
            if entry.get("warehouse_id") == warehouse_id:
                entry["archived"] = True
                any_updated = True

        return { "success": True, "message": "All access control entries for warehouse archived." }

    def restore_data_warehouse(self, warehouse_id: str, requesting_user_id: str) -> dict:
        """
        Restore a previously deleted data warehouse (status must be 'deleted') to 'active' status,
        if requester has admin permissions. Also unarchives associated access controls and usage statistics.

        Args:
            warehouse_id (str): ID of the warehouse to restore.
            requesting_user_id (str): User ID of actor requesting the restore.

        Returns:
            dict: {
                "success": True,
                "message": "Warehouse restored to active status."
            }
            or
            {
                "success": False,
                "error": "Error reason"
            }

        Constraints:
            - Only users with admin permission can restore the warehouse.
            - Only warehouses with status 'deleted' can be restored.
            - Associated AccessControl and UsageStatistics are unarchived/marked active again.
        """
        # Check warehouse exists
        warehouse = self.data_warehouses.get(warehouse_id)
        if not warehouse:
            return { "success": False, "error": "Warehouse does not exist." }

        # Check warehouse status is 'deleted'
        if warehouse["status"] != "deleted":
            return { "success": False, "error": f"Warehouse status must be 'deleted' to restore, current status: {warehouse['status']}" }

        # Check requesting user is admin for this warehouse
        has_admin = False
        for ac in self.access_controls:
            if ac["warehouse_id"] == warehouse_id and ac["user_id"] == requesting_user_id and ac.get("permission_level", "").lower() == "admin":
                has_admin = True
                break
        if not has_admin:
            return { "success": False, "error": "Requesting user lacks admin permission for this warehouse." }

        # Restore warehouse status
        warehouse["status"] = "active"
        self.data_warehouses[warehouse_id] = warehouse

        # Unarchive usage statistics (add archived flag if missing)
        if warehouse_id in self.usage_statistics:
            usage_stats = self.usage_statistics[warehouse_id]
            usage_stats["archived"] = False  # Mark as not archived (add field if not present)
            self.usage_statistics[warehouse_id] = usage_stats

        # Unarchive access control entries (add archived flag if missing)
        for ac in self.access_controls:
            if ac["warehouse_id"] == warehouse_id:
                ac["archived"] = False  # Mark as not archived (add field if not present)

        return { "success": True, "message": "Warehouse restored to active status." }

    def add_or_update_access_control_entry(
        self,
        warehouse_id: str,
        user_id: str,
        permission_level: str
    ) -> dict:
        """
        Grant or modify a user's permissions for a specific warehouse.

        Args:
            warehouse_id (str): The ID of the warehouse.
            user_id (str): The ID of the user.
            permission_level (str): Permission to be granted (e.g., 'read', 'write', 'admin').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Permission updated/granted for user <user_id> on warehouse <warehouse_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure."
                    }

        Constraints:
            - Both warehouse and user must exist.
            - Updates if entry exists, creates otherwise.
        """
        if not warehouse_id or warehouse_id not in self.data_warehouses:
            return { "success": False, "error": "Warehouse does not exist." }

        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        updated = False
        for entry in self.access_controls:
            if entry["warehouse_id"] == warehouse_id and entry["user_id"] == user_id:
                entry["permission_level"] = permission_level
                updated = True
                break

        if not updated:
            new_entry: AccessControlInfo = {
                "warehouse_id": warehouse_id,
                "user_id": user_id,
                "permission_level": permission_level
            }
            self.access_controls.append(new_entry)

        return {
            "success": True,
            "message": f"Permission {'updated' if updated else 'granted'} for user {user_id} on warehouse {warehouse_id}."
        }


class CloudDataWarehouseManagementSystem(BaseEnv):
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

    def get_warehouse_by_id(self, **kwargs):
        return self._call_inner_tool('get_warehouse_by_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_access_control_for_warehouse_and_user(self, **kwargs):
        return self._call_inner_tool('get_access_control_for_warehouse_and_user', kwargs)

    def list_warehouses_by_status(self, **kwargs):
        return self._call_inner_tool('list_warehouses_by_status', kwargs)

    def get_usage_statistics_for_warehouse(self, **kwargs):
        return self._call_inner_tool('get_usage_statistics_for_warehouse', kwargs)

    def get_configuration_for_warehouse(self, **kwargs):
        return self._call_inner_tool('get_configuration_for_warehouse', kwargs)

    def list_access_control_entries_for_warehouse(self, **kwargs):
        return self._call_inner_tool('list_access_control_entries_for_warehouse', kwargs)

    def delete_data_warehouse(self, **kwargs):
        return self._call_inner_tool('delete_data_warehouse', kwargs)

    def create_data_warehouse(self, **kwargs):
        return self._call_inner_tool('create_data_warehouse', kwargs)

    def update_warehouse_configuration(self, **kwargs):
        return self._call_inner_tool('update_warehouse_configuration', kwargs)

    def archive_usage_statistics_for_warehouse(self, **kwargs):
        return self._call_inner_tool('archive_usage_statistics_for_warehouse', kwargs)

    def archive_access_control_for_warehouse(self, **kwargs):
        return self._call_inner_tool('archive_access_control_for_warehouse', kwargs)

    def restore_data_warehouse(self, **kwargs):
        return self._call_inner_tool('restore_data_warehouse', kwargs)

    def add_or_update_access_control_entry(self, **kwargs):
        return self._call_inner_tool('add_or_update_access_control_entry', kwargs)

