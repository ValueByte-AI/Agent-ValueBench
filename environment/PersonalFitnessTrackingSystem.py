# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime
from typing import Optional, List, Dict



# User: _id (str), name (str), profile_info (str), contact_info (str)
class UserInfo(TypedDict):
    _id: str
    name: str
    profile_info: str
    contact_info: str

# ActivitySession: session_id (str), user_id (str), activity_type (str), start_time (str), end_time (str), location (str)
class ActivitySessionInfo(TypedDict):
    session_id: str
    user_id: str
    activity_type: str
    start_time: str
    end_time: str
    location: str

# HealthMetrics: session_id (str), hydration_level (float), heart_rate (float), calories_burned (float), steps (int), additional_metric (float)
class HealthMetricsInfo(TypedDict):
    session_id: str
    hydration_level: float
    heart_rate: float
    calories_burned: float
    steps: int
    additional_metric: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Activity Sessions: {session_id: ActivitySessionInfo}
        self.activity_sessions: Dict[str, ActivitySessionInfo] = {}

        # Health Metrics: {session_id: HealthMetricsInfo}
        self.health_metrics: Dict[str, HealthMetricsInfo] = {}

        # Constraints:
        # - Each ActivitySession is associated with exactly one User (via user_id in ActivitySessionInfo).
        # - HealthMetrics are linked and valid only in context of a specific ActivitySession (via session_id).
        # - Updates to health metrics should ideally preserve audit/history (optional, for more advanced systems).
        # - Hydration level and other health metrics must be within physiologically realistic ranges
        #   (e.g., non-negative, not exceeding maximum safe values).

    def _normalize_health_metrics_audit(self):
        if not hasattr(self, "health_metrics_audit"):
            return None

        raw = self.health_metrics_audit
        if isinstance(raw, dict):
            normalized = {}
            for session_id, entries in raw.items():
                if isinstance(entries, list):
                    normalized[str(session_id)] = copy.deepcopy(entries)
                elif isinstance(entries, dict):
                    normalized[str(session_id)] = [copy.deepcopy(entries)]
                elif entries is None:
                    normalized[str(session_id)] = []
            self.health_metrics_audit = normalized
            return normalized

        if isinstance(raw, list):
            normalized = {}
            for entry in raw:
                if not isinstance(entry, dict):
                    continue
                session_id = entry.get("session_id")
                if session_id is None:
                    continue
                normalized.setdefault(str(session_id), []).append(copy.deepcopy(entry))
            self.health_metrics_audit = normalized
            return normalized

        if isinstance(raw, str):
            stripped = raw.strip()
            if not stripped:
                self.health_metrics_audit = {}
                return self.health_metrics_audit
            try:
                parsed = json.loads(stripped)
            except Exception:
                self.health_metrics_audit = {}
                return self.health_metrics_audit
            self.health_metrics_audit = parsed
            return self._normalize_health_metrics_audit()

        self.health_metrics_audit = {}
        return self.health_metrics_audit


    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user information by their unique user identifier.

        Args:
            _id (str): The system-wide unique identifier for the user.

        Returns:
            dict: 
            - If found: { "success": True, "data": UserInfo }
            - If not found: { "success": False, "error": "User not found" }

        Constraints:
            - User _id must exist in the system.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve all user records that match the given name (case-insensitive).

        Args:
            name (str): The user's name to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo],  # All matching User records
                }
                or
                {
                    "success": False,
                    "error": str  # "User not found"
                }

        Notes/Constraints:
            - Name match is case-insensitive.
            - Returns all user records matching the given name.
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"].lower() == name.lower()
        ]

        if not matches:
            return { "success": False, "error": "User not found" }
        else:
            return { "success": True, "data": matches }

    def list_user_activity_sessions(self, user_id: str) -> dict:
        """
        Retrieve all activity sessions associated with the given user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivitySessionInfo],  # List (possibly empty) of activity session information
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        result = [
            session_info
            for session_info in self.activity_sessions.values()
            if session_info["user_id"] == user_id
        ]

        return {"success": True, "data": result}


    def get_activity_sessions_by_type_and_time(
        self,
        user_id: str,
        activity_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> dict:
        """
        Retrieve a user's activity sessions filtered by activity_type and/or a specific time window.

        Args:
            user_id (str): User's unique ID whose sessions to retrieve.
            activity_type (str, optional): Only include sessions of this activity type (if given).
            start_time (str, optional): ISO-format string; lower bound (inclusive) for session start time.
            end_time (str, optional): ISO-format string; upper bound (inclusive) for session end time.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivitySessionInfo],  # possibly empty if no sessions match
            }
            or
            {
                "success": False,
                "error": str,  # error message
            }

        Constraints:
            - user_id must exist in the users table.
            - Time bounds are compared as ISO strings.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        def is_within_time_window(session: Dict) -> bool:
            # Convert string times to datetime for robust comparison;
            # if missing, fallback to simple string comparison (ISO format).
            st = session.get("start_time")
            et = session.get("end_time")
            # No window provided
            if not start_time and not end_time:
                return True
            try:
                # Compare times as datetime objects
                session_start = datetime.fromisoformat(st) if st else None
                session_end = datetime.fromisoformat(et) if et else None
                window_start = datetime.fromisoformat(start_time) if start_time else None
                window_end = datetime.fromisoformat(end_time) if end_time else None
                # Session must at least partly overlap requested window
                if window_start and session_end and session_end < window_start:
                    return False
                if window_end and session_start and session_start > window_end:
                    return False
                return True
            except Exception:
                # If time format invalid, fail all matching
                return False

        # Filter sessions
        result = []
        for session in self.activity_sessions.values():
            if session["user_id"] != user_id:
                continue
            if activity_type and session["activity_type"] != activity_type:
                continue
            if (start_time or end_time) and not is_within_time_window(session):
                continue
            result.append(session)

        return { "success": True, "data": result }

    def get_activity_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve details for a specific activity session using its session_id.

        Args:
            session_id (str): Unique identifier of the activity session.

        Returns:
            dict: 
              - {"success": True, "data": ActivitySessionInfo} on success
              - {"success": False, "error": str} if the session is not found

        Constraints:
            - The activity session must exist in the system.
        """
        if session_id not in self.activity_sessions:
            return {"success": False, "error": "Activity session not found"}
        return {"success": True, "data": self.activity_sessions[session_id]}

    def get_health_metrics_by_session_id(self, session_id: str) -> dict:
        """
        Retrieve health metrics for a specified ActivitySession.

        Args:
            session_id (str): The ID of the activity session whose health metrics are to be retrieved.

        Returns:
            dict:
                {
                    "success": True,
                    "data": HealthMetricsInfo  # Health metrics for the given session
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., session_id not found)
                }

        Constraints:
            - Returns health metrics only if they exist for the session_id.
        """
        if session_id not in self.health_metrics:
            return {
                "success": False,
                "error": "No health metrics found for the given session ID"
            }
    
        return {
            "success": True,
            "data": self.health_metrics[session_id]
        }

    def get_health_metrics_audit_history(self, session_id: str) -> dict:
        """
        Retrieve the audit/modification history for a health metrics record.

        Args:
            session_id (str): The unique identifier for the activity session/health metric record.

        Returns:
            dict: 
                - If audit/history is enabled and present:
                    {
                        "success": True,
                        "data": List[dict]  # List of audit/history records for the given session_id
                    }
                - If audit/history is not enabled in the system:
                    {
                        "success": False,
                        "error": "Audit/history not enabled"
                    }
                - If the session_id is invalid:
                    {
                        "success": False,
                        "error": "Invalid session_id"
                    }
        Constraints:
            - Audit/history is optional. Only return data if available.
            - session_id must exist in health_metrics.
        """
        # Validate if session_id is in health_metrics
        if session_id not in self.health_metrics:
            return { "success": False, "error": "Invalid session_id" }
    
        # Audit/history infrastructure check (not required by base class)
        # Assume: if self.health_metrics_audit exists
        audit_history = self._normalize_health_metrics_audit()
        if audit_history is None:
            return { "success": False, "error": "Audit/history not enabled" }
        if session_id not in audit_history:
            return { "success": True, "data": [] }
    
        return {
            "success": True,
            "data": audit_history[session_id]
        }

    def update_health_metric(
        self,
        session_id: str,
        hydration_level: float = None,
        heart_rate: float = None,
        calories_burned: float = None,
        steps: int = None,
        additional_metric: float = None
    ) -> dict:
        """
        Update one or more quantitative health metric values for a specific session's HealthMetrics entry,
        enforcing physiological validity constraints.

        Args:
            session_id (str): Unique ID of the ActivitySession whose HealthMetrics to update.
            hydration_level (float, optional): New hydration value in liters (must be >= 0).
            heart_rate (float, optional): New heart rate in bpm (must be >= 0).
            calories_burned (float, optional): New calories value (must be >= 0).
            steps (int, optional): New step count (must be >= 0).
            additional_metric (float, optional): New value for additional metric (must be >= 0).

        Returns:
            dict:
                - {"success": True, "message": "Health metrics updated for session <session_id>"} on success
                - {"success": False, "error": "<reason>"} on error (session not found, invalid values, etc.)
    
        Constraints:
            - session_id must exist in the health_metrics dictionary.
            - Any updated fields must be within physiologically realistic ranges (non-negative).
        """
        if session_id not in self.health_metrics:
            return {"success": False, "error": "Session health metrics not found"}

        # Collect updates and validate
        updates = {}
        if hydration_level is not None:
            if not isinstance(hydration_level, (int, float)) or hydration_level < 0:
                return {"success": False, "error": "Invalid hydration_level (must be non-negative number)"}
            updates["hydration_level"] = float(hydration_level)
        if heart_rate is not None:
            if not isinstance(heart_rate, (int, float)) or heart_rate < 0:
                return {"success": False, "error": "Invalid heart_rate (must be non-negative number)"}
            updates["heart_rate"] = float(heart_rate)
        if calories_burned is not None:
            if not isinstance(calories_burned, (int, float)) or calories_burned < 0:
                return {"success": False, "error": "Invalid calories_burned (must be non-negative number)"}
            updates["calories_burned"] = float(calories_burned)
        if steps is not None:
            if not isinstance(steps, int) or steps < 0:
                return {"success": False, "error": "Invalid steps (must be non-negative integer)"}
            updates["steps"] = steps
        if additional_metric is not None:
            if not isinstance(additional_metric, (int, float)) or additional_metric < 0:
                return {"success": False, "error": "Invalid additional_metric (must be non-negative number)"}
            updates["additional_metric"] = float(additional_metric)

        if not updates:
            return {"success": False, "error": "No valid metrics provided to update"}

        # Apply updates
        for key, value in updates.items():
            self.health_metrics[session_id][key] = value

        return {
            "success": True,
            "message": f"Health metrics updated for session {session_id}"
        }

    def log_activity_session(
        self,
        session_id: str,
        user_id: str,
        activity_type: str,
        start_time: str,
        end_time: str,
        location: str
    ) -> dict:
        """
        Create and store a new ActivitySession for the specified user.

        Args:
            session_id (str): Unique identifier for this activity session.
            user_id (str): The user performing the activity (must exist in the system).
            activity_type (str): Type of the activity (e.g., 'running').
            start_time (str): Timestamp for activity start.
            end_time (str): Timestamp for activity end.
            location (str): Location where the activity was performed.

        Returns:
            dict: {
                "success": True,
                "message": "ActivitySession created for user <user_id> with session_id <session_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - session_id must be unique.
            - user_id must exist in the system.
            - Each ActivitySession must belong to exactly one User.
        """
        # Check for unique session_id
        if session_id in self.activity_sessions:
            return {"success": False, "error": f"session_id '{session_id}' already exists"}

        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": f"user_id '{user_id}' does not exist"}

        # Create the ActivitySession entry
        self.activity_sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "activity_type": activity_type,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
        }

        return {"success": True, "message": f"ActivitySession created for user {user_id} with session_id {session_id}."}

    def create_health_metrics_for_session(
        self,
        session_id: str,
        hydration_level: float,
        heart_rate: float,
        calories_burned: float,
        steps: int,
        additional_metric: float
    ) -> dict:
        """
        Initialize HealthMetrics data for a newly logged session.
    
        Args:
            session_id (str): The ActivitySession ID to associate with these metrics. Must exist.
            hydration_level (float): Hydration in liters or relevant units. Must be non-negative and realistic.
            heart_rate (float): Heart rate in BPM. Must be within physiological limits (30 < hr < 250).
            calories_burned (float): Calories burned. Must be non-negative, usually < 10000.
            steps (int): Number of steps. Must be non-negative.
            additional_metric (float): Additional metric (non-negative).
    
        Returns:
            dict: 
              - On success: {"success": True, "message": "..."}
              - On failure: {"success": False, "error": "..."}
    
        Constraints:
            - session_id must exist as an ActivitySession.
            - No HealthMetrics may already exist for this session.
            - All inputs must be within physiologically realistic non-negative ranges.
        """
        # 1. Check session existence
        if session_id not in self.activity_sessions:
            return {"success": False, "error": f"ActivitySession {session_id} does not exist"}
    
        # 2. Check for existing HealthMetrics
        if session_id in self.health_metrics:
            return {"success": False, "error": "HealthMetrics for this session already exist"}
    
        # 3. Physiological range checks
        if not (0.0 <= hydration_level <= 10.0):
            return {"success": False, "error": "Hydration level out of realistic range (0~10L)"}
        if not (30.0 < heart_rate < 250.0):
            return {"success": False, "error": "Heart rate must be in (30, 250) BPM"}
        if not (0.0 <= calories_burned < 10000.0):
            return {"success": False, "error": "Calories burned out of plausible range (0~10000)"}
        if not (isinstance(steps, int) and steps >= 0):
            return {"success": False, "error": "Steps must be a non-negative integer"}
        if not (additional_metric >= 0.0):
            return {"success": False, "error": "Additional metric must be non-negative"}

        # 4. Create HealthMetrics record
        metrics = {
            "session_id": session_id,
            "hydration_level": hydration_level,
            "heart_rate": heart_rate,
            "calories_burned": calories_burned,
            "steps": steps,
            "additional_metric": additional_metric
        }
        self.health_metrics[session_id] = metrics

        return {"success": True, "message": f"HealthMetrics created for session {session_id}"}

    def append_health_metrics_audit_entry(self, session_id: str, audit_entry: dict) -> dict:
        """
        Appends an audit/history entry to the HealthMetrics audit log for the given session.

        Args:
            session_id (str): The session identifier whose HealthMetrics' audit entry is to be recorded.
            audit_entry (dict): The audit entry to log.
                It should include at least 'timestamp' (float/int/str) and any other relevant info
                (e.g., what was changed, old/new value, who did it).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Audit entry appended to HealthMetrics session <session_id>"
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - Only append if the HealthMetrics record for session_id exists.
            - The audit_entry must be a dict and should contain at least a 'timestamp' key.

        """
        if session_id not in self.health_metrics:
            return { "success": False, "error": "No HealthMetrics exists for this session" }
    
        if not isinstance(audit_entry, dict):
            return { "success": False, "error": "Audit entry must be a dictionary" }
        if 'timestamp' not in audit_entry:
            return { "success": False, "error": "Audit entry missing required 'timestamp' field" }

        # Lazy creation of audit trail structure if not present
        if not hasattr(self, "health_metrics_audit"):
            self.health_metrics_audit = {}

        audit_history = self._normalize_health_metrics_audit()
        if session_id not in audit_history:
            audit_history[session_id] = []

        audit_history[session_id].append(audit_entry)

        return {
            "success": True,
            "message": f"Audit entry appended to HealthMetrics session {session_id}"
        }

    def delete_activity_session(self, session_id: str) -> dict:
        """
        Remove an activity session and its associated health metrics records for a given session_id.

        Args:
            session_id (str): The activity session identifier to delete.

        Returns:
            dict:
                { "success": True, "message": "Activity session and associated health metrics deleted." }
                or
                { "success": False, "error": "Activity session not found." }

        Constraints:
            - Only delete if session exists.
            - Remove all associated HealthMetrics for this session.
        """
        if session_id not in self.activity_sessions:
            return { "success": False, "error": "Activity session not found." }

        # Remove the activity session
        del self.activity_sessions[session_id]

        # Remove health metrics if any for this session (if present)
        if session_id in self.health_metrics:
            del self.health_metrics[session_id]

        return {
            "success": True,
            "message": "Activity session and associated health metrics deleted."
        }

    def delete_health_metrics_record(self, session_id: str) -> dict:
        """
        Remove HealthMetrics data for a given session (admin/cleanup action).

        Args:
            session_id (str): The session ID for which the associated HealthMetrics record should be deleted.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Health metrics record for session <session_id> deleted." }
                - On failure: { "success": False, "error": "Health metrics record for session not found." }

        Constraints:
            - Only deletes HealthMetrics for an existing session_id.
            - Does not remove any ActivitySession or User data.
        """
        if session_id not in self.health_metrics:
            return { "success": False, "error": "Health metrics record for session not found." }
    
        del self.health_metrics[session_id]
        return { "success": True, "message": f"Health metrics record for session {session_id} deleted." }


class PersonalFitnessTrackingSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_user_activity_sessions(self, **kwargs):
        return self._call_inner_tool('list_user_activity_sessions', kwargs)

    def get_activity_sessions_by_type_and_time(self, **kwargs):
        return self._call_inner_tool('get_activity_sessions_by_type_and_time', kwargs)

    def get_activity_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_activity_session_by_id', kwargs)

    def get_health_metrics_by_session_id(self, **kwargs):
        return self._call_inner_tool('get_health_metrics_by_session_id', kwargs)

    def get_health_metrics_audit_history(self, **kwargs):
        return self._call_inner_tool('get_health_metrics_audit_history', kwargs)

    def update_health_metric(self, **kwargs):
        return self._call_inner_tool('update_health_metric', kwargs)

    def log_activity_session(self, **kwargs):
        return self._call_inner_tool('log_activity_session', kwargs)

    def create_health_metrics_for_session(self, **kwargs):
        return self._call_inner_tool('create_health_metrics_for_session', kwargs)

    def append_health_metrics_audit_entry(self, **kwargs):
        return self._call_inner_tool('append_health_metrics_audit_entry', kwargs)

    def delete_activity_session(self, **kwargs):
        return self._call_inner_tool('delete_activity_session', kwargs)

    def delete_health_metrics_record(self, **kwargs):
        return self._call_inner_tool('delete_health_metrics_record', kwargs)
