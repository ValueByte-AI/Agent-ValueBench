# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class LogEntryInfo(TypedDict):
    log_id: str
    timestamp: str  # or float, depending on implementation
    event_type: str
    event_description: str
    updated_at: str  # or float
    updated_by: str

class UpdateHistoryInfo(TypedDict):
    log_id: str
    previous_timestamp: str  # or float
    previous_event_type: str
    previous_event_description: str
    updated_at: str  # or float
    updated_by: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Application Log Management System environment state.
        """

        # Log entries: {log_id: LogEntryInfo}
        # Each log entry must have a unique log_id.
        self.log_entries: Dict[str, LogEntryInfo] = {}

        # Update history: {log_id: List[UpdateHistoryInfo]}
        # Maintains a historical record of changes to log entries.
        self.update_history: Dict[str, List[UpdateHistoryInfo]] = {}

        # Authorized users for update operations.
        self.authorized_users = set()

        # Constraints reminder:
        # - Each log entry must have a unique log_id.
        # - Only authorized users can update log entries.
        # - Updates to a log entry must be timestamped and preferably recorded in update history for audit trails.
        # - Log entries should not be deleted if data integrity and audit are priorities; changes are tracked via updates.
        # - The system must provide confirmation of successful updates.

    def get_log_entry_by_id(self, log_id: str) -> dict:
        """
        Retrieve the full log entry information for a given log_id.

        Args:
            log_id (str): Unique identifier of the log entry.

        Returns:
            dict: 
              If found:
                  {
                    "success": True,
                    "data": LogEntryInfo
                  }
              If not found:
                  {
                    "success": False,
                    "error": "Log entry does not exist"
                  }

        Constraints:
            - log_id must exist in the system.
        """
        log_entry = self.log_entries.get(log_id)
        if log_entry is None:
            return { "success": False, "error": "Log entry does not exist" }
        return { "success": True, "data": log_entry }

    def list_log_entries(
        self,
        event_type: str = None,
        start_timestamp: str = None,
        end_timestamp: str = None
    ) -> dict:
        """
        Retrieve a list of all log entries, optionally filtered by event_type and/or timestamp range.

        Args:
            event_type (str, optional): Filter results to only those with this event_type.
            start_timestamp (str, optional): Include only entries with timestamp >= this value.
            end_timestamp (str, optional): Include only entries with timestamp <= this value.

        Returns:
            dict: {
                "success": True,
                "data": List[LogEntryInfo]  # All matching log entries
            }
            or
            {
                "success": False,
                "error": str  # Description of input or filtering error
            }

        Constraints:
            - Does not require user authorization.
            - Does not mutate state.
            - If start_timestamp/end_timestamp are specified, must be valid and comparable to entry timestamps.
        """

        # Helper for timestamp comparison
        def is_within_range(ts: str, start: str, end: str) -> bool:
            if start and ts < start:
                return False
            if end and ts > end:
                return False
            return True

        if start_timestamp and end_timestamp:
            if start_timestamp > end_timestamp:
                return {
                    "success": False,
                    "error": "start_timestamp must be less than or equal to end_timestamp"
                }

        # Apply filters
        result = []
        for entry in self.log_entries.values():
            # filter by event_type
            if event_type and entry["event_type"] != event_type:
                continue
            # filter by timestamp range (assume str comparison is sufficient for now)
            ts = entry["timestamp"]
            if start_timestamp and ts < start_timestamp:
                continue
            if end_timestamp and ts > end_timestamp:
                continue
            result.append(entry)

        return { "success": True, "data": result }

    def get_update_history(self, log_id: str) -> dict:
        """
        Retrieve the audit trail (update history) for a given log entry by log_id.

        Args:
            log_id (str): The unique identifier for the log entry.

        Returns:
            dict:
                - If log entry does not exist:
                    { "success": False, "error": "Log entry not found" }
                - If log entry exists:
                    { "success": True, "data": List[UpdateHistoryInfo] }
                    (data may be empty if no history exists)
    
        Constraints:
            - The log_id must correspond to an existing log entry.
            - No permission required for query.
            - If update history does not exist, return empty list in "data".
        """
        if log_id not in self.log_entries:
            return { "success": False, "error": "Log entry not found" }

        history = self.update_history.get(log_id, [])
        return { "success": True, "data": history }

    def is_user_authorized(self, username: str) -> dict:
        """
        Verify whether a given user is authorized to update log entries.

        Args:
            username (str): The username or user ID to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "authorized": bool  # True if the user is authorized, else False
                }
            }
            or
            {
                "success": False,
                "error": str  # Error message for missing input
            }

        Constraints:
            - If the username is not provided, returns an error.
            - Uses self.authorized_users if defined; else, no users are authorized by default.
        """
        if not username or not isinstance(username, str):
            return { "success": False, "error": "Username must be provided" }

        # Assume there is a set or list of authorized users; if not, default to empty set
        authorized_users = getattr(self, "authorized_users", set())
        if not isinstance(authorized_users, (set, list)):
            authorized_users = set()

        is_authorized = username in authorized_users
        return {
            "success": True,
            "data": {
                "authorized": is_authorized
            }
        }

    def confirm_log_update(self, log_id: str) -> dict:
        """
        Confirm whether the update to a specific log entry was successful and reflect the latest state.

        Args:
            log_id (str): The unique identifier for the log entry.

        Returns:
            dict: {
                "success": True,
                "data": LogEntryInfo  # The latest info/state for the given log_id
            }
            or
            {
                "success": False,
                "error": str  # Error description if log_id is not found
            }

        Constraints:
            - log_id must exist in the system.
        """
        if log_id not in self.log_entries:
            return { "success": False, "error": "Log entry does not exist" }

        return { "success": True, "data": self.log_entries[log_id] }

    def update_log_entry(
        self,
        log_id: str,
        updated_by: str,
        updated_at: str,
        timestamp: str = None,
        event_type: str = None,
        event_description: str = None
    ) -> dict:
        """
        Update fields (timestamp, event_type, event_description) for a specified log entry,
        record the prior state for audit history, and enforce user authorization.

        Args:
            log_id (str): ID of the log entry to update.
            updated_by (str): Username of updater (must be authorized).
            updated_at (str): Timestamp for when the update occurred.
            timestamp (str, optional): New value for 'timestamp' field.
            event_type (str, optional): New value for 'event_type'.
            event_description (str, optional): New value for 'event_description'.

        Returns:
            dict: {
                "success": True,
                "message": "Log entry updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only authorized users can update.
            - log_id must exist.
            - Must record update history (with old values) for audit.
        """
        # Check log entry exists
        if log_id not in self.log_entries:
            return { "success": False, "error": "Log entry does not exist." }

        # Ensure at least one field is to be updated
        if timestamp is None and event_type is None and event_description is None:
            return { "success": False, "error": "No fields specified for update." }

        # Check user authorization
        auth_result = self.is_user_authorized(updated_by)
        if not auth_result.get("success"):
            return { "success": False, "error": auth_result.get("error", "Authorization check failed.") }
        if not auth_result.get("data", {}).get("authorized", False):
            return { "success": False, "error": "User not authorized for update." }

        # Get current log entry
        log_entry = self.log_entries[log_id]

        # Record prior state for update history unless the same snapshot
        # was already manually appended for this exact update event.
        prior_history = {
            "log_id": log_id,
            "previous_timestamp": log_entry["timestamp"],
            "previous_event_type": log_entry["event_type"],
            "previous_event_description": log_entry["event_description"],
            "updated_at": updated_at,
            "updated_by": updated_by
        }
        history_list = self.update_history.setdefault(log_id, [])
        if not history_list or history_list[-1] != prior_history:
            history_list.append(prior_history)

        # Update the fields in the log entry
        if timestamp is not None:
            log_entry["timestamp"] = timestamp
        if event_type is not None:
            log_entry["event_type"] = event_type
        if event_description is not None:
            log_entry["event_description"] = event_description
        log_entry["updated_at"] = updated_at
        log_entry["updated_by"] = updated_by

        self.log_entries[log_id] = log_entry

        return { "success": True, "message": "Log entry updated successfully." }

    def record_update_history(
        self,
        log_id: str,
        previous_timestamp: str,
        previous_event_type: str,
        previous_event_description: str,
        updated_at: str,
        updated_by: str
    ) -> dict:
        """
        Manually add an entry to the log's update history for auditing/rollback scenarios.

        Args:
            log_id (str): The ID of the log entry to which this history relates.
            previous_timestamp (str): The timestamp value before update.
            previous_event_type (str): The event type value before update.
            previous_event_description (str): The event description before update.
            updated_at (str): When this update record is added.
            updated_by (str): Who performed/triggers the update (username or system).

        Returns:
            dict
                On success: { "success": True, "message": "Update history recorded for log <log_id>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - log_id must exist in self.log_entries (cannot audit non-existent log).
            - This operation only appends to the update history.
        """

        if log_id not in self.log_entries:
            return { "success": False, "error": "Log entry not found" }

        history_entry: UpdateHistoryInfo = {
            "log_id": log_id,
            "previous_timestamp": previous_timestamp,
            "previous_event_type": previous_event_type,
            "previous_event_description": previous_event_description,
            "updated_at": updated_at,
            "updated_by": updated_by
        }

        if log_id not in self.update_history:
            self.update_history[log_id] = []

        self.update_history[log_id].append(history_entry)

        return { "success": True, "message": f"Update history recorded for log {log_id}" }


class ApplicationLogManagementSystem(BaseEnv):
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
            if key == "is_user_authorized":
                if isinstance(value, str):
                    env.authorized_users = {item.strip() for item in value.split(",") if item.strip()}
                elif isinstance(value, (list, tuple, set)):
                    env.authorized_users = {str(item).strip() for item in value if str(item).strip()}
                else:
                    env.authorized_users = set()
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

    def get_log_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_log_entry_by_id', kwargs)

    def list_log_entries(self, **kwargs):
        return self._call_inner_tool('list_log_entries', kwargs)

    def get_update_history(self, **kwargs):
        return self._call_inner_tool('get_update_history', kwargs)

    def is_user_authorized(self, **kwargs):
        return self._call_inner_tool('is_user_authorized', kwargs)

    def confirm_log_update(self, **kwargs):
        return self._call_inner_tool('confirm_log_update', kwargs)

    def update_log_entry(self, **kwargs):
        return self._call_inner_tool('update_log_entry', kwargs)

    def record_update_history(self, **kwargs):
        return self._call_inner_tool('record_update_history', kwargs)
