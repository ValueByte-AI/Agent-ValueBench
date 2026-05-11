# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class UserInfo(TypedDict):
    _id: str
    name: str
    account_sta: str

class LogEntryInfo(TypedDict):
    entry_id: str
    user_id: str
    content: str
    created_timestamp: float  # or str if using ISO format
    tags: List[str]
    category: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for a personal log management system.
        """
        # Users: {user_id: UserInfo}
        # Entity: User → attributes: _id, name, account_sta
        self.users: Dict[str, UserInfo] = {}

        # Log Entries: {entry_id: LogEntryInfo}
        # Entity: LogEntry → attributes: entry_id, user_id, content, created_timestamp, tags, category
        self.log_entries: Dict[str, LogEntryInfo] = {}

        # Constraints:
        # - Each LogEntry must be associated with exactly one User (linked by user_id).
        # - created_timestamp must be immutable once set.
        # - Log entries must be retrievable in time order (ascending/descending) for a given user.
        # - Users can only access, search, or aggregate their own log entries unless permissions allow otherwise.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info(s) by name.

        Args:
            name (str): The name to use for user lookup.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # All matching users (empty if no match)
            }

        Constraints:
            - None specific; simply matches by 'name'.
            - Multiple users with the same name may exist; all matches are returned.
        """
        matches = [user for user in self.users.values() if user.get('name') == name]
        return {"success": True, "data": matches}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info using user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # If user is found
            }
            or
            {
                "success": False,
                "error": str  # If user is not found
            }
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_user_log_entries(self, user_id: str) -> dict:
        """
        Retrieve all log/journal entries for a specific user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[LogEntryInfo],  # List of log entries for the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. user not found
            }

        Constraints:
            - The specified user must exist.
            - Only log entries associated with the user are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        user_logs = [
            log_entry for log_entry in self.log_entries.values()
            if log_entry["user_id"] == user_id
        ]

        return { "success": True, "data": user_logs }

    def search_user_logs_by_time_range(
        self, 
        user_id: str, 
        start_timestamp: float, 
        end_timestamp: float
    ) -> dict:
        """
        Retrieve all log entries for a user where created_timestamp is within a specified time window (inclusive).

        Args:
            user_id (str): The unique identifier of the user whose logs to retrieve.
            start_timestamp (float): The start time (Unix timestamp, inclusive).
            end_timestamp (float): The end time (Unix timestamp, inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[LogEntryInfo],  # List of matching log entries ordered by created_timestamp ascending.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. user does not exist or invalid range
            }

        Constraints:
            - user_id must exist.
            - Only logs belonging to the user are returned.
            - If start_timestamp > end_timestamp, returns error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if start_timestamp > end_timestamp:
            return { "success": False, "error": "Invalid time range" }

        results = [
            entry for entry in self.log_entries.values()
            if entry["user_id"] == user_id and
               start_timestamp <= entry["created_timestamp"] <= end_timestamp
        ]
        results.sort(key=lambda x: x["created_timestamp"])
        return { "success": True, "data": results }

    def get_log_entry_by_id(self, entry_id: str) -> dict:
        """
        Retrieve the full details of a single log entry by its unique entry_id.

        Args:
            entry_id (str): The unique identifier of the log entry to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": LogEntryInfo  # All attributes of the found log entry
            }
            or
            {
                "success": False,
                "error": "Log entry not found"
            }

        Constraints:
            - The entry_id must exist in self.log_entries.
            - No mutation; no permission check unless user context is specified.
        """
        entry = self.log_entries.get(entry_id)
        if entry is None:
            return {"success": False, "error": "Log entry not found"}
        return {"success": True, "data": entry}

    def list_user_logs_ordered(self, user_id: str, order: str = "asc") -> dict:
        """
        Retrieve all log entries for a specific user, ordered by created_timestamp.

        Args:
            user_id (str): The ID of the user whose logs are to be listed.
            order (str): "asc" for ascending, "desc" for descending order. Defaults to "asc".

        Returns:
            dict:
              - If successful:
                    {
                        "success": True,
                        "data": List[LogEntryInfo]  # Ordered list of user's logs
                    }
              - If error, for example if user does not exist or order is invalid:
                    {
                        "success": False,
                        "error": str  # Error description
                    }

        Constraints:
            - user_id must exist.
            - Only accepts "asc" or "desc" as order argument.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if order not in ("asc", "desc"):
            return { "success": False, "error": "Invalid order argument; must be 'asc' or 'desc'" }

        user_logs = [entry for entry in self.log_entries.values() if entry["user_id"] == user_id]
        reverse_sort = (order == "desc")
        user_logs_sorted = sorted(user_logs, key=lambda x: x["created_timestamp"], reverse=reverse_sort)

        return {
            "success": True,
            "data": user_logs_sorted
        }

    def filter_user_logs_by_tag(self, user_id: str, tag: str) -> dict:
        """
        Return all logs for the specified user that contain the specified tag.

        Args:
            user_id (str): The unique identifier of the user.
            tag (str): The tag to filter log entries by.

        Returns:
            dict:
                success: True if operation completed,
                data: list of LogEntryInfo dicts matching the tag (possibly empty).
            or
                success: False if user does not exist,
                error: reason as str.

        Constraints:
            - Each LogEntry must be associated with exactly one User.
            - Only log entries for the specified user are considered.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        filtered_logs = [
            entry for entry in self.log_entries.values()
            if entry["user_id"] == user_id and tag in entry["tags"]
        ]

        return { "success": True, "data": filtered_logs }

    def filter_user_logs_by_category(self, user_id: str, category: str) -> dict:
        """
        Return all log entries for a specific user within the given category.

        Args:
            user_id (str): The user's unique identifier.
            category (str): The category to filter log entries by.

        Returns:
            dict: {
                "success": True,
                "data": List[LogEntryInfo],  # All matching logs (may be empty)
            }
            OR
            {
                "success": False,
                "error": str,  # Reason for failure
            }

        Constraints:
            - Only logs belonging to the specified user are returned.
            - User must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        filtered_logs = [
            entry for entry in self.log_entries.values()
            if entry["user_id"] == user_id and entry["category"] == category
        ]
        return {"success": True, "data": filtered_logs}

    def count_user_logs_in_time_range(self, user_id: str, start_timestamp: float, end_timestamp: float) -> dict:
        """
        Counts the number of log entries for a specific user that were created within the given (inclusive) time range.

        Args:
            user_id (str): ID of the user whose logs to count.
            start_timestamp (float): Lower inclusive bound of the timestamp (Unix time).
            end_timestamp (float): Upper inclusive bound of the timestamp (Unix time).

        Returns:
            dict: {
                "success": True,
                "data": int  # The count of log entries
            } 
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - user_id must exist in the system.
            - Only logs for the given user are counted.
            - If start_timestamp > end_timestamp the count is 0.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if start_timestamp > end_timestamp:
            # Inverted range returns count 0; not an error
            return {"success": True, "data": 0}

        count = sum(
            1
            for entry in self.log_entries.values()
            if entry["user_id"] == user_id and 
               start_timestamp <= entry["created_timestamp"] <= end_timestamp
        )
        return {"success": True, "data": count}

    def add_log_entry(
        self,
        entry_id: str,
        user_id: str,
        content: str,
        created_timestamp: float,
        tags: list,
        category: str
    ) -> dict:
        """
        Create a new log entry associated with a user. The created_timestamp is set during creation and is immutable.

        Args:
            entry_id (str): Unique identifier for the log entry.
            user_id (str): Identifier of the user who owns the log entry.
            content (str): The main text content of the log entry.
            created_timestamp (float): The creation timestamp (immutable thereafter).
            tags (List[str]): Tags associated with the entry.
            category (str): The category of the log entry.

        Returns:
            dict:
                On success: { "success": True, "message": "Log entry created." }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - entry_id must be unique.
            - user_id must refer to an existing user.
            - created_timestamp is set on creation and never modified.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check if entry_id is unique
        if entry_id in self.log_entries:
            return { "success": False, "error": "Entry ID already exists" }

        # (Optional) Basic checks for content, tags, category
        if not content:
            return { "success": False, "error": "Content must not be empty" }
        if not isinstance(tags, list):
            return { "success": False, "error": "Tags must be a list" }
        if not isinstance(created_timestamp, (int, float)):
            return { "success": False, "error": "created_timestamp must be numeric" }

        self.log_entries[entry_id] = {
            "entry_id": entry_id,
            "user_id": user_id,
            "content": content,
            "created_timestamp": float(created_timestamp),
            "tags": tags,
            "category": category
        }

        return { "success": True, "message": "Log entry created." }

    def delete_log_entry(self, entry_id: str, user_id: str) -> dict:
        """
        Remove an existing log entry by entry_id if and only if the user (user_id) is the entry’s owner.

        Args:
            entry_id (str): The identifier of the log entry to delete.
            user_id (str): The ID of the user attempting the deletion.

        Returns:
            dict: 
                - {"success": True, "message": "Log entry deleted."} on success
                - {"success": False, "error": <reason>} on failure

        Constraints:
            - The entry_id and user_id must both exist.
            - The log entry must belong to user_id.
            - Only the owner may delete (unless future permissions are added).
        """
        if entry_id not in self.log_entries:
            return {"success": False, "error": "Log entry does not exist."}
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        log_entry = self.log_entries[entry_id]
        if log_entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: user is not the owner of this entry."}
        del self.log_entries[entry_id]
        return {"success": True, "message": "Log entry deleted."}

    def update_log_entry_content(
        self,
        entry_id: str,
        user_id: str,
        new_content: str = None,
        new_tags: list = None,
        new_category: str = None
    ) -> dict:
        """
        Edit the content, tags, or category of a log entry.
        Only the owner of the log entry is permitted to modify it.
        The created_timestamp field cannot be changed.

        Args:
            entry_id (str): The entry to update.
            user_id (str): The user performing the operation.
            new_content (str, optional): New content for the log entry.
            new_tags (list, optional): New list of tags.
            new_category (str, optional): New category.

        Returns:
            dict: {
                "success": True,
                "message": "Log entry updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Only owner can edit their entry.
            - created_timestamp is immutable.
            - At least one of new_content, new_tags, new_category must be provided.
        """
        log_entry = self.log_entries.get(entry_id)
        if log_entry is None:
            return {"success": False, "error": "Log entry does not exist."}

        if log_entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: not owner of the log entry."}

        if new_content is None and new_tags is None and new_category is None:
            return {"success": False, "error": "No updates provided."}

        # Only modify allowed fields
        if new_content is not None:
            log_entry["content"] = new_content
        if new_tags is not None:
            log_entry["tags"] = list(new_tags)
        if new_category is not None:
            log_entry["category"] = new_category

        # State updated in place because log_entry is a reference to dict value
        return {"success": True, "message": "Log entry updated successfully."}

    def bulk_delete_user_logs_by_time_range(
        self,
        user_id: str,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Delete all logs associated with a user within [start_time, end_time).

        Args:
            user_id (str): The user whose logs to delete.
            start_time (float): Start (inclusive) of the time window (Unix timestamp).
            end_time (float): End (exclusive) of the time window (Unix timestamp).

        Returns:
            dict: {
                "success": True,
                "message": str,  # Summary of deletion, e.g. 'Deleted N logs for user ...'
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only logs belonging to the given user will be deleted.
            - Timestamps are not modified.
            - It is not an error to delete zero logs.
            - User must exist.
        """
        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        # Collect relevant log entry ids
        to_delete = []
        for entry_id, log_info in self.log_entries.items():
            if (
                log_info["user_id"] == user_id
                and start_time <= log_info["created_timestamp"] < end_time
            ):
                to_delete.append(entry_id)

        # Delete entries
        for entry_id in to_delete:
            del self.log_entries[entry_id]
    
        return {
            "success": True,
            "message": f"Deleted {len(to_delete)} log(s) for user '{user_id}' in the specified time window."
        }


class PersonalLogManagementSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_log_entries(self, **kwargs):
        return self._call_inner_tool('list_user_log_entries', kwargs)

    def search_user_logs_by_time_range(self, **kwargs):
        return self._call_inner_tool('search_user_logs_by_time_range', kwargs)

    def get_log_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_log_entry_by_id', kwargs)

    def list_user_logs_ordered(self, **kwargs):
        return self._call_inner_tool('list_user_logs_ordered', kwargs)

    def filter_user_logs_by_tag(self, **kwargs):
        return self._call_inner_tool('filter_user_logs_by_tag', kwargs)

    def filter_user_logs_by_category(self, **kwargs):
        return self._call_inner_tool('filter_user_logs_by_category', kwargs)

    def count_user_logs_in_time_range(self, **kwargs):
        return self._call_inner_tool('count_user_logs_in_time_range', kwargs)

    def add_log_entry(self, **kwargs):
        return self._call_inner_tool('add_log_entry', kwargs)

    def delete_log_entry(self, **kwargs):
        return self._call_inner_tool('delete_log_entry', kwargs)

    def update_log_entry_content(self, **kwargs):
        return self._call_inner_tool('update_log_entry_content', kwargs)

    def bulk_delete_user_logs_by_time_range(self, **kwargs):
        return self._call_inner_tool('bulk_delete_user_logs_by_time_range', kwargs)
