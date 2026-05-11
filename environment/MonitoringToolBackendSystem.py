# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    account_status: str
    contact_info: str  # could be adapted to Dict or more detailed type

class EndpointInfo(TypedDict):
    endpoint_id: str
    hostname: str
    ip_address: str
    status: str
    registered_timestamp: str
    last_activity_timestamp: str
    user_id: str

class EndpointDataInfo(TypedDict):
    endpoint_id: str
    user_id: str
    data_type: str
    value: Any
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for monitoring tool backend system state.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Endpoints: {endpoint_id: EndpointInfo}
        self.endpoints: Dict[str, EndpointInfo] = {}

        # Endpoint data: list of EndpointDataInfo entries
        self.endpoint_data: List[EndpointDataInfo] = []

        # Constraints:
        # - Each endpoint must be associated with a valid user (user_id exists).
        # - Endpoint data can only be retrieved or removed if the user has sufficient permissions (ownership or admin).
        # - Deleting endpoint data for a user removes all data for that user’s endpoints; endpoints of other users are unaffected.
        # - Endpoint status and historic data must be consistent; removing endpoint data may require cleanup in aggregates.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details (UserInfo) using a user ID.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                - If user exists:
                    {
                        "success": True,
                        "data": UserInfo
                    }
                - If user not found:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - User ID must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Check the account status (active, inactive, suspended, etc.) for a given user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": { "_id": user_id, "account_status": <status> }
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - User with user_id must exist.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": { "_id": user_id, "account_status": user["account_status"] } }

    def list_endpoints_by_user(self, user_id: str) -> dict:
        """
        Retrieve all endpoints associated with a given user ID.

        Args:
            user_id (str): The user ID whose endpoints are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[EndpointInfo],  # endpoints for user (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # error reason, e.g. user does not exist
            }

        Constraints:
            - user_id must correspond to an existing user
            - Only endpoints belonging to the given user are listed
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        endpoints_list = [
            endpoint_info for endpoint_info in self.endpoints.values()
            if endpoint_info["user_id"] == user_id
        ]

        return { "success": True, "data": endpoints_list }

    def get_endpoint_by_id(self, endpoint_id: str) -> dict:
        """
        Retrieve details for the specified endpoint using its unique ID.

        Args:
            endpoint_id (str): The unique identifier of the endpoint.

        Returns:
            dict: {
                "success": True,
                "data": EndpointInfo  # All metadata for the endpoint
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., not found)
            }

        Constraints:
            - The provided endpoint_id must exist in the system.
            - No additional permissions are required for this read operation.
        """
        endpoint = self.endpoints.get(endpoint_id)
        if endpoint is None:
            return { "success": False, "error": "Endpoint not found" }
        return { "success": True, "data": endpoint }

    def check_endpoint_ownership(self, endpoint_id: str, user_id: str) -> dict:
        """
        Confirm whether a given endpoint is owned by a specific user.

        Args:
            endpoint_id (str): The ID of the endpoint to check.
            user_id (str): The user ID to check ownership against.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "is_owner": bool  # True if endpoint is owned by user, else False
                    }
                On failure (endpoint does not exist):
                    {
                        "success": False,
                        "error": str  # Error message
                    }
        Constraints:
            - Endpoint must exist in the system.
            - Ownership is determined by comparing endpoint's 'user_id' to the provided 'user_id'.
        """
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return { "success": False, "error": "Endpoint does not exist" }
        is_owner = endpoint["user_id"] == user_id
        return { "success": True, "is_owner": is_owner }

    def list_endpoint_data_by_user(self, user_id: str) -> dict:
        """
        Retrieve all endpoint data records associated with the specified user ID.

        Args:
            user_id (str): User ID for which endpoint data should be listed.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[EndpointDataInfo]  # All records where user_id matches
                  }
                - On failure: {
                    "success": False,
                    "error": str
                  }

        Constraints:
            - User with user_id must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_data = [
            record for record in self.endpoint_data
            if record["user_id"] == user_id
        ]
        return {"success": True, "data": user_data}

    def list_endpoint_data_by_endpoint(self, endpoint_id: str) -> dict:
        """
        Retrieve all endpoint data records for a specific endpoint ID.

        Args:
            endpoint_id (str): The ID of the endpoint whose monitoring data is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[EndpointDataInfo]  # List of data records for the endpoint (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error message if the endpoint does not exist
            }

        Constraints:
            - The specified endpoint must exist (endpoint_id in self.endpoints).
            - No permission check is enforced in this operation.
        """
        if endpoint_id not in self.endpoints:
            return {"success": False, "error": "Endpoint not found"}

        data_records = [
            entry for entry in self.endpoint_data
            if entry["endpoint_id"] == endpoint_id
        ]

        return {"success": True, "data": data_records}

    def get_endpoint_data(
        self,
        user_id: str,
        endpoint_id: str,
        data_type: str = None,
        start_time: str = None,
        end_time: str = None
    ) -> dict:
        """
        Retrieve endpoint data filtered by user ID, endpoint ID, and optional criteria (data_type, start_time, end_time).
    
        Args:
            user_id (str): The user ID requesting data (must be endpoint owner).
            endpoint_id (str): The target endpoint ID.
            data_type (str, optional): Filter by data type.
            start_time (str, optional): ISO/lexically comparable timestamp (inclusive lower bound).
            end_time (str, optional): ISO/lexically comparable timestamp (inclusive upper bound).
    
        Returns:
            dict: {
                "success": True,
                "data": [EndpointDataInfo, ...]
            }
            OR
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - The user must exist.
            - The endpoint must exist and belong to the user.
            - Data is filtered as specified.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User ID not found" }

        # Check endpoint exists
        endpoint_info = self.endpoints.get(endpoint_id)
        if not endpoint_info:
            return { "success": False, "error": "Endpoint ID not found" }

        # Check endpoint ownership
        if endpoint_info["user_id"] != user_id:
            return { "success": False, "error": "Permission denied (user does not own endpoint)" }

        # Collect and filter endpoint data
        result = []
        for data in self.endpoint_data:
            if data["endpoint_id"] != endpoint_id:
                continue
            if data["user_id"] != user_id:
                continue
            if data_type is not None and data["data_type"] != data_type:
                continue
            # Timestamps are ISO/lexical order
            if start_time is not None and data["timestamp"] < start_time:
                continue
            if end_time is not None and data["timestamp"] > end_time:
                continue
            result.append(data)

        return { "success": True, "data": result }

    def list_data_types_for_endpoint(self, endpoint_id: str) -> dict:
        """
        List distinct data types collected for a given endpoint 
        (e.g., 'metrics', 'logs', 'events', etc.).

        Args:
            endpoint_id (str): The endpoint's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # Unique data_type values for the endpoint
            }
            or
            {
                "success": False,
                "error": str,       # "Endpoint not found"
            }

        Constraints:
            - The endpoint must exist in self.endpoints.
            - All matching data_type values are listed uniquely.
        """
        if endpoint_id not in self.endpoints:
            return {"success": False, "error": "Endpoint not found"}

        data_types = set()
        for entry in self.endpoint_data:
            if entry["endpoint_id"] == endpoint_id:
                data_types.add(entry["data_type"])

        return {"success": True, "data": sorted(data_types)}

    def get_endpoint_status(self, endpoint_id: str) -> dict:
        """
        Query the current status of an endpoint (active, offline, etc.).

        Args:
            endpoint_id (str): The unique identifier for the endpoint.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "endpoint_id": str,
                    "status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Endpoint not found"
            }

        Constraints:
            - The endpoint with the specified ID must exist.
            - No permission checks required for this operation.
        """
        endpoint = self.endpoints.get(endpoint_id)
        if endpoint is None:
            return { "success": False, "error": "Endpoint not found" }

        return {
            "success": True,
            "data": {
                "endpoint_id": endpoint_id,
                "status": endpoint["status"]
            }
        }

    def get_endpoint_activity_history(self, endpoint_id: str) -> dict:
        """
        Retrieve a time-ordered (by timestamp ascending) list of activity or status logs for a given endpoint.
    
        Args:
            endpoint_id (str): The unique identifier of the endpoint.

        Returns:
            dict: 
            - If successful:
                {
                    "success": True,
                    "data": List[EndpointDataInfo],  # List may be empty
                }
            - If error (e.g. endpoint does not exist):
                {
                    "success": False,
                    "error": str,
                }
    
        Constraints:
            - The specified endpoint_id must exist.
        """
        if endpoint_id not in self.endpoints:
            return { "success": False, "error": "Endpoint does not exist." }

        # Select endpoint data entries associated with this endpoint
        data_entries = [d for d in self.endpoint_data if d["endpoint_id"] == endpoint_id]

        # Sort by timestamp ascending (assuming ISO8601 or sortable string, otherwise convert)
        sorted_entries = sorted(data_entries, key=lambda x: x["timestamp"])

        return { "success": True, "data": sorted_entries }

    def remove_endpoint_data_by_user(self, user_id: str) -> dict:
        """
        Delete all endpoint data for all endpoints owned by the specified user.

        Args:
            user_id (str): The user ID whose endpoint data is to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "<N> endpoint data entries removed for user <user_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only remove data associated with endpoints owned by the specified user.
            - Operation is successful even if there is no data to remove.
            - User must exist.
        """
        # Check if the user exists
        if user_id not in self.users:
            return { "success": False, "error": f"User '{user_id}' does not exist." }

        # Find all endpoint IDs owned by the user
        user_endpoint_ids = set(
            ep_id for ep_id, ep in self.endpoints.items() if ep["user_id"] == user_id
        )

        if not user_endpoint_ids:
            # Success: User exists but has no endpoints.
            return {
                "success": True,
                "message": f"No endpoint data to remove; user '{user_id}' owns no endpoints."
            }

        # Filter and count entries that would be removed
        before_count = len(self.endpoint_data)
        self.endpoint_data = [
            data for data in self.endpoint_data
            if data["endpoint_id"] not in user_endpoint_ids
        ]
        after_count = len(self.endpoint_data)
        removed = before_count - after_count

        return {
            "success": True,
            "message": f"{removed} endpoint data entries removed for user '{user_id}'."
        }

    def remove_endpoint_data_by_endpoint(self, endpoint_id: str, user_id: str) -> dict:
        """
        Delete all data for a specific endpoint, if the requesting user owns the endpoint.

        Args:
            endpoint_id (str): The unique identifier of the endpoint.
            user_id (str): The unique identifier of the requesting user.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the deletion (count, endpoint, etc.)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (not found, permission denied)
            }

        Constraints:
            - Endpoint must exist.
            - User must exist.
            - Only users who own the endpoint (endpoint.user_id == user_id) can delete its data.
            - Data deletion only affects records for the given endpoint.
        """
        # Verify user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        # Verify endpoint exists
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return {"success": False, "error": "Endpoint does not exist"}
    
        # Check ownership/permission
        if endpoint["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: user does not own endpoint"}
    
        # Find and delete data
        before_count = len(self.endpoint_data)
        self.endpoint_data = [
            data for data in self.endpoint_data
            if data["endpoint_id"] != endpoint_id
        ]
        deleted_count = before_count - len(self.endpoint_data)

        # Optional: cleanup aggregates
        if hasattr(self, "cleanup_aggregate_tables_after_deletion"):
            self.cleanup_aggregate_tables_after_deletion(endpoint_id=endpoint_id)
    
        return {
            "success": True,
            "message": f"Deleted {deleted_count} endpoint data record(s) for endpoint '{endpoint_id}'."
        }

    def remove_specific_endpoint_data(
        self,
        user_id: str,
        endpoint_id: str,
        data_type: str,
        start_time: str = None,
        end_time: str = None
    ) -> dict:
        """
        Delete endpoint data matching criteria: user, endpoint, data_type, and an optional time range.

        Args:
            user_id (str): The user requesting data removal.
            endpoint_id (str): The endpoint whose data to remove.
            data_type (str): The data type to remove (e.g., 'metrics', 'logs').
            start_time (str, optional): Only remove data after or at this timestamp (inclusive).
            end_time (str, optional): Only remove data before or at this timestamp (inclusive).

        Returns:
            dict:
                - On success: { "success": True, "message": "Deleted X matching endpoint data records." }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - Endpoint must exist and belong to the user.
            - Only data for this endpoint/user/data_type is removed.
            - If start_time/end_time are supplied, only data inside this time range is removed.
            - User must be owner of the endpoint to remove endpoint's data (no admin/backdoor logic).
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Check endpoint exists
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return { "success": False, "error": "Endpoint does not exist" }

        # Check ownership
        if endpoint["user_id"] != user_id:
            return { "success": False, "error": "Permission denied: user does not own this endpoint" }

        # Filter and delete matching data entries
        to_delete_indices = []
        for idx, record in enumerate(self.endpoint_data):
            if (
                record["endpoint_id"] == endpoint_id and
                record["user_id"] == user_id and
                record["data_type"] == data_type
            ):
                timestamp = record["timestamp"]
                if start_time and timestamp < start_time:
                    continue
                if end_time and timestamp > end_time:
                    continue
                to_delete_indices.append(idx)

        if not to_delete_indices:
            return { "success": True, "message": "No matching endpoint data records found to delete." }

        # Delete from the end to preserve indices
        for idx in reversed(to_delete_indices):
            del self.endpoint_data[idx]

        return {
            "success": True,
            "message": f"Deleted {len(to_delete_indices)} matching endpoint data records."
        }

    def cleanup_aggregate_tables_after_deletion(
        self, user_id: str = None, endpoint_id: str = None
    ) -> dict:
        """
        Cleans up/updates aggregate or summary records after deletion of endpoint data.

        Args:
            user_id (str, optional): If provided, cleanup for all aggregates/summaries associated with this user.
            endpoint_id (str, optional): If provided, cleanup for all aggregates/summaries associated with this endpoint.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - At least one of user_id or endpoint_id must be provided.
            - Aggregates for unrelated users/endpoints must not be changed.
            - If the key does not exist, operation is a no-op but returns success.
        """
        # Simulate aggregates by assuming self.aggregates exists: 
        if not hasattr(self, "aggregates"):
            # Simulated structure: {"user:<user_id>": {...}, "endpoint:<endpoint_id>": {...}}
            self.aggregates = {}

        if user_id is None and endpoint_id is None:
            return {"success": False, "error": "Must provide user_id or endpoint_id for cleanup."}

        # Track what we clean
        cleaned_keys = []
        if user_id is not None:
            for agg_key in (f"user:{user_id}", user_id):
                if agg_key in self.aggregates:
                    del self.aggregates[agg_key]
                    cleaned_keys.append(agg_key)
        if endpoint_id is not None:
            for agg_key in (f"endpoint:{endpoint_id}", endpoint_id):
                if agg_key in self.aggregates:
                    del self.aggregates[agg_key]
                    cleaned_keys.append(agg_key)

        if cleaned_keys:
            return {
                "success": True,
                "message": f"Aggregates cleaned: {', '.join(cleaned_keys)}"
            }
        else:
            return {
                "success": True,
                "message": "No matching aggregates to clean. Operation successful."
            }

    def update_endpoint_status(self, endpoint_id: str, new_status: str) -> dict:
        """
        Change the status of an endpoint (e.g., set to 'inactive' after deleted data).

        Args:
            endpoint_id (str): The ID of the endpoint whose status should be updated.
            new_status (str): The new status value to set for the endpoint.

        Returns:
            dict: {
                "success": True,
                "message": "Endpoint status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - endpoint_id must exist in the system.
            - Only the status of the specified endpoint is changed.
        """
        if endpoint_id not in self.endpoints:
            return { "success": False, "error": "Endpoint not found" }

        self.endpoints[endpoint_id]["status"] = new_status

        # Optionally update last_activity_timestamp to current time (as a string)
        # import time
        # self.endpoints[endpoint_id]["last_activity_timestamp"] = str(time.time())

        return {
            "success": True,
            "message": f"Endpoint status updated to {new_status}"
        }

    def add_endpoint_data(self, endpoint_id: str, user_id: str, data_type: str, value: Any, timestamp: str) -> dict:
        """
        Insert new endpoint data for a specific endpoint and user.

        Args:
            endpoint_id (str): The unique identifier of the endpoint.
            user_id (str): The unique identifier of the user.
            data_type (str): The type of metric/log/event being inserted.
            value (Any): The value of the data (could be numeric, string, dict, etc).
            timestamp (str): Timestamp string (format should be consistent with system).

        Returns:
            dict: {
                "success": True,
                "message": "Endpoint data added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist in self.users.
            - endpoint_id must exist in self.endpoints and be associated with user_id.
            - All fields are required.
        """
        # Check existence of user
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if endpoint_id not in self.endpoints:
            return { "success": False, "error": "Endpoint does not exist." }
        endpoint_info = self.endpoints[endpoint_id]
        if endpoint_info["user_id"] != user_id:
            return { "success": False, "error": "Endpoint is not associated with the specified user." }
        if not data_type or timestamp is None:
            return { "success": False, "error": "Missing required field data_type or timestamp." }

        data_entry = {
            "endpoint_id": endpoint_id,
            "user_id": user_id,
            "data_type": data_type,
            "value": value,
            "timestamp": timestamp
        }
        self.endpoint_data.append(data_entry)
        return { "success": True, "message": "Endpoint data added successfully." }

    def update_endpoint_last_activity(self, endpoint_id: str, new_timestamp: str) -> dict:
        """
        Update the last_activity_timestamp for an endpoint.

        Args:
            endpoint_id (str): The ID of the endpoint whose activity timestamp is to be updated.
            new_timestamp (str): The new timestamp to record (ISO8601, RFC3339, etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Last activity timestamp updated for endpoint <endpoint_id>."
            }
            or
            {
                "success": False,
                "error": "Endpoint does not exist."
            }

        Constraints:
            - The specified endpoint_id must exist in self.endpoints.
        """
        if endpoint_id not in self.endpoints:
            return {"success": False, "error": "Endpoint does not exist."}
        self.endpoints[endpoint_id]["last_activity_timestamp"] = new_timestamp
        return {
            "success": True, 
            "message": f"Last activity timestamp updated for endpoint {endpoint_id}."
        }


class MonitoringToolBackendSystem(BaseEnv):
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
            if key == "cleanup_aggregate_tables_after_deletion":
                setattr(env, "_cleanup_aggregate_tables_after_deletion_state", copy.deepcopy(value))
                continue
            if key == "aggregates" and isinstance(value, str):
                try:
                    setattr(env, key, copy.deepcopy(json.loads(value)))
                except Exception:
                    setattr(env, key, {})
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def list_endpoints_by_user(self, **kwargs):
        return self._call_inner_tool('list_endpoints_by_user', kwargs)

    def get_endpoint_by_id(self, **kwargs):
        return self._call_inner_tool('get_endpoint_by_id', kwargs)

    def check_endpoint_ownership(self, **kwargs):
        return self._call_inner_tool('check_endpoint_ownership', kwargs)

    def list_endpoint_data_by_user(self, **kwargs):
        return self._call_inner_tool('list_endpoint_data_by_user', kwargs)

    def list_endpoint_data_by_endpoint(self, **kwargs):
        return self._call_inner_tool('list_endpoint_data_by_endpoint', kwargs)

    def get_endpoint_data(self, **kwargs):
        return self._call_inner_tool('get_endpoint_data', kwargs)

    def list_data_types_for_endpoint(self, **kwargs):
        return self._call_inner_tool('list_data_types_for_endpoint', kwargs)

    def get_endpoint_status(self, **kwargs):
        return self._call_inner_tool('get_endpoint_status', kwargs)

    def get_endpoint_activity_history(self, **kwargs):
        return self._call_inner_tool('get_endpoint_activity_history', kwargs)

    def remove_endpoint_data_by_user(self, **kwargs):
        return self._call_inner_tool('remove_endpoint_data_by_user', kwargs)

    def remove_endpoint_data_by_endpoint(self, **kwargs):
        return self._call_inner_tool('remove_endpoint_data_by_endpoint', kwargs)

    def remove_specific_endpoint_data(self, **kwargs):
        return self._call_inner_tool('remove_specific_endpoint_data', kwargs)

    def cleanup_aggregate_tables_after_deletion(self, **kwargs):
        return self._call_inner_tool('cleanup_aggregate_tables_after_deletion', kwargs)

    def update_endpoint_status(self, **kwargs):
        return self._call_inner_tool('update_endpoint_status', kwargs)

    def add_endpoint_data(self, **kwargs):
        return self._call_inner_tool('add_endpoint_data', kwargs)

    def update_endpoint_last_activity(self, **kwargs):
        return self._call_inner_tool('update_endpoint_last_activity', kwargs)
