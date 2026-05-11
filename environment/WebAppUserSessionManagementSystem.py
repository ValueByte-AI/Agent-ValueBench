# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from datetime import datetime, timezone
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    account_sta: str  # e.g., 'active', 'locked', etc.

class SessionInfo(TypedDict):
    session_id: str
    user_id: str
    start_time: str  # ISO format timestamp
    end_time: str    # ISO format timestamp or "" if ongoing
    session_status: str  # e.g., 'active', 'ended'
    ip_add: str          # IP address

class ActivityLogInfo(TypedDict):
    activity_id: str
    session_id: str
    timestamp: str       # ISO format timestamp
    action_type: str
    detail: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Web Application User Session Management System
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}

        # ActivityLogs: {activity_id: ActivityLogInfo}
        self.activity_logs: Dict[str, ActivityLogInfo] = {}

        # State space entities:
        #   User: _id, username, email, account_sta
        #   Session: session_id, user_id, start_time, end_time, session_status, ip_addr
        #   ActivityLog: activity_id, session_id, timestamp, action_type, detail

        # Constraints:
        # - Sessions are linked to one and only one user.
        # - Activity logs are associated with a single session.
        # - Only valid (active or properly ended) sessions can record activities.
        # - Users cannot initiate multiple concurrent sessions if policy disallows (single session per user constraint, if enabled).
        # - Activity logs must be timestamped and immutable once recorded.

    @staticmethod
    def _normalize_policy_flag(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "enabled"}
        return bool(value)

    def get_user_by_username(self, username: str) -> dict:
        """
        Given a username, find and return the corresponding user information.

        Args:
            username (str): The username to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User info for the given username
            }
            or
            {
                "success": False,
                "error": str  # Error message if the username is not found
            }

        Constraints:
            - Username is assumed to be unique.
            - Only returns information, no state changes.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {
                    "success": True,
                    "data": user
                }
        return {
            "success": False,
            "error": "User not found"
        }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's information by their unique user id.

        Args:
            user_id (str): The unique user _id to search for.

        Returns:
            dict: 
                - If found: {'success': True, 'data': UserInfo}
                - If not found: {'success': False, 'error': 'User not found'}

        Constraints:
            - The user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def list_all_users(self) -> dict:
        """
        Return details of all users in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],    # List of all users, possibly empty.
            }

        Notes:
            - If there are no users, the list will be empty.
            - No filtering, returns all known UserInfo.
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def get_user_sessions(self, user_id: str) -> dict:
        """
        Fetch all sessions initiated by a given user.

        Args:
            user_id (str): The unique user id.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[SessionInfo]  # List of SessionInfo dicts for this user (may be empty if none)
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason, e.g. user does not exist
                }

        Constraints:
            - User must exist in the system.
            - Sessions are always linked to users by user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_sessions = [
            session for session in self.sessions.values() if session["user_id"] == user_id
        ]
        return { "success": True, "data": user_sessions }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve detailed information of a session with the specified session id.

        Args:
            session_id (str): Unique identifier of the session.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": SessionInfo,  # Complete session info if found
                }
                OR
                {
                    "success": False,
                    "error": "Session not found"
                }

        Constraints:
            - session_id must refer to an existing session.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session not found"}
        return {"success": True, "data": session}

    def list_user_active_sessions(self, user_id: str) -> dict:
        """
        List all currently active sessions for a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[SessionInfo],  # All active sessions for this user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user does not exist)
            }

        Constraints:
            - The specified user_id must exist.
            - Only sessions with session_status == 'active' are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        active_sessions = [
            sess for sess in self.sessions.values()
            if sess["user_id"] == user_id and sess["session_status"] == "active"
        ]

        return { "success": True, "data": active_sessions }

    def get_session_activity_logs(self, session_id: str) -> dict:
        """
        Retrieve all activity logs (ActivityLogInfo) associated with the specified session.

        Args:
            session_id (str): Unique session identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivityLogInfo],  # list of logs for the session (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason (e.g., session does not exist)
            }

        Constraints:
            - The provided session_id must exist in the system.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }

        logs = [
            log for log in self.activity_logs.values()
            if log["session_id"] == session_id
        ]

        return { "success": True, "data": logs }

    def list_user_activity_logs(self, user_id: str) -> dict:
        """
        Retrieve all activity logs performed by a user across all their sessions.

        Args:
            user_id (str): The unique ID of the user whose logs are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivityLogInfo],  # May be empty if no logs
            }
            or
            {
                "success": False,
                "error": str  # e.g. "User does not exist"
            }

        Constraints:
            - The user must exist in the system.
            - Only logs for sessions linked to this user will be returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Collect all session_ids for this user
        user_session_ids = {
            session_id for session_id, session in self.sessions.items()
            if session["user_id"] == user_id
        }

        # Find and collect all activity logs with those session_ids
        user_activity_logs = [
            log for log in self.activity_logs.values()
            if log["session_id"] in user_session_ids
        ]

        return {"success": True, "data": user_activity_logs}

    def get_activity_log_by_id(self, activity_id: str) -> dict:
        """
        Retrieve details for a specific activity log item.

        Args:
            activity_id (str): Unique identifier for the activity log.

        Returns:
            dict: {
                "success": True,
                "data": ActivityLogInfo  # The activity log details
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Activity log not found"
            }

        Constraints:
            - The activity log must exist in the system.
        """
        activity_log = self.activity_logs.get(activity_id)
        if activity_log is None:
            return { "success": False, "error": "Activity log not found" }
        return { "success": True, "data": activity_log }

    def get_session_status(self, session_id: str) -> dict:
        """
        Check the current status (e.g., 'active', 'ended') of a given session.

        Args:
            session_id (str): The unique identifier for the session.

        Returns:
            dict: {
                "success": True,
                "data": str  # The session's current status
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., session does not exist
            }

        Constraints:
            - The session_id must exist in the system.
        """
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session does not exist" }
        return { "success": True, "data": session["session_status"] }

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Retrieve the account status (e.g., 'active', 'locked', etc.) for a user.

        Args:
            user_id (str): The unique user ID.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": str  # The user's account status, e.g. 'active'
                }
                On failure (user does not exist):
                {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - User must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        account_status = user.get("account_sta", None)
        if account_status is None:
            return { "success": False, "error": "Account status unavailable" }
        return { "success": True, "data": account_status }

    def session_policy_info(self) -> dict:
        """
        Retrieve the current session policy information, specifically whether the
        'single session per user' constraint is enforced.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "single_session_per_user_enforced": bool
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Returns policy in effect. If policy flag is undefined in the system, returns error.
        """
        if hasattr(self, "single_session_per_user_enabled"):
            policy_flag = self._normalize_policy_flag(getattr(self, "single_session_per_user_enabled"))
        elif hasattr(self, "single_session_per_user"):
            policy_flag = self._normalize_policy_flag(getattr(self, "single_session_per_user"))
        else:
            return {
                "success": False,
                "error": "Session policy flag 'single_session_per_user' is not configured in the system."
            }
        return {
            "success": True,
            "data": {
                "single_session_per_user_enforced": policy_flag
            }
        }


    def start_new_session(self, user_id: str, ip_add: str) -> dict:
        """
        Initiate a new session for a specified user.

        Args:
            user_id (str): The User's unique identifier for which to start the session.
            ip_add (str): The IP address from which the session is being initiated.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Session started",
                        "session_info": {SessionInfo}
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - User must exist and have 'active' account_sta.
            - If single session per user is enforced, user must not have any 'active' (unfinished) sessions.
            - Sessions are associated with exactly one user.
            - Automatically generates session_id and ISO timestamp.
        """

        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check account status
        if user["account_sta"] != "active":
            return { "success": False, "error": f"User account status is '{user['account_sta']}'" }

        # Single session per user policy handling
        # Default is disabled unless a field self.single_session_policy is set to True
        policy_enabled = False
        if hasattr(self, "single_session_per_user_enabled"):
            policy_enabled = self._normalize_policy_flag(getattr(self, "single_session_per_user_enabled"))
        elif hasattr(self, "single_session_per_user"):
            policy_enabled = self._normalize_policy_flag(getattr(self, "single_session_per_user"))
        if policy_enabled:
            # Check for an active session
            active_sessions = [
                sess for sess in self.sessions.values()
                if sess["user_id"] == user_id and sess["session_status"] == "active"
            ]
            if active_sessions:
                return { "success": False, "error": "Single session policy enforced: user already has an active session." }

        # Generate unique session_id & timestamps
        session_id = uuid.uuid4().hex
        now_iso = datetime.now(timezone.utc).isoformat()

        # Create SessionInfo
        session_info = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": now_iso,
            "end_time": "",
            "session_status": "active",
            "ip_add": ip_add
        }

        self.sessions[session_id] = session_info

        return {
            "success": True,
            "message": "Session started",
            "session_info": session_info
        }


    def end_session(self, session_id: str) -> dict:
        """
        Mark an existing session as ended by setting its 'end_time' to the current timestamp
        and its 'session_status' to 'ended'.

        Args:
            session_id (str): The ID of the session to end.

        Returns:
            dict: {
                "success": True,
                "message": "Session <session_id> ended successfully."
            }
            or
            {
                "success": False,
                "error": "Session does not exist." or "Session is already ended."
            }

        Constraints:
            - The session must exist.
            - If the session is already ended, no changes are made and error message returned.
            - Sets end_time to current UTC time (ISO string) and session_status to 'ended'.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session does not exist." }
        if session["session_status"] == "ended":
            return { "success": False, "error": "Session is already ended." }
    
        now_iso = datetime.utcnow().isoformat() + "Z"
        session["end_time"] = now_iso
        session["session_status"] = "ended"

        # Save back (dict is mutable, but for clarity)
        self.sessions[session_id] = session

        return { "success": True, "message": f"Session {session_id} ended successfully." }

    def append_activity_log(
        self,
        session_id: str,
        action_type: str,
        detail: str,
        timestamp: str
    ) -> dict:
        """
        Record a new immutable activity log under a valid session.

        Args:
            session_id (str): The session to associate with the activity log.
            action_type (str): The type of action (e.g., 'login', 'file_upload', etc.).
            detail (str): Additional detail about the action.
            timestamp (str): ISO timestamp when the action occurred.

        Returns:
            dict: {
                "success": True,
                "message": "Activity log recorded successfully.",
                "activity_id": <activity_id: str>
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The session_id must refer to an existing session.
            - Only sessions with 'active' or 'ended' status can have logs recorded.
            - Activity logs are immutable once created.
            - Each activity log id is unique.
        """
        # Check if session exists
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session does not exist." }

        # Check session validity
        if session['session_status'] not in ('active', 'ended'):
            return { "success": False, "error": "Only active or ended sessions can record activities." }

        # Simple parameter validation
        if not action_type.strip():
            return { "success": False, "error": "action_type cannot be empty." }
        if not detail.strip():
            return { "success": False, "error": "detail cannot be empty." }
        if not timestamp.strip():
            return { "success": False, "error": "timestamp cannot be empty." }

        # Generate unique activity_id (use a counter or uuid4)
        activity_id = str(uuid.uuid4())
        while activity_id in self.activity_logs:
            activity_id = str(uuid.uuid4())

        log = {
            "activity_id": activity_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "action_type": action_type,
            "detail": detail
        }
        self.activity_logs[activity_id] = log

        return {
            "success": True,
            "message": "Activity log recorded successfully.",
            "activity_id": activity_id
        }

    def lock_user_account(self, _id: str) -> dict:
        """
        Lock a user's account by changing their 'account_sta' field to 'locked'.

        Args:
            _id (str): The unique identifier of the user to lock.

        Returns:
            dict: {
                "success": True,
                "message": "User account locked"
            }
            or
            {
                "success": False,
                "error": "User not found" | "Account already locked"
            }

        Constraints:
            - User must exist in self.users.
            - If already locked, no change and return appropriate error.
        """
        user = self.users.get(_id)
        if not user:
            return {"success": False, "error": "User not found"}

        if user.get('account_sta') == 'locked':
            return {"success": False, "error": "Account already locked"}

        user['account_sta'] = 'locked'
        self.users[_id] = user
        return {"success": True, "message": "User account locked"}

    def unlock_user_account(self, user_id: str) -> dict:
        """
        Change a user's account status to 'active'.

        Args:
            user_id (str): The unique user identifier (_id).

        Returns:
            dict: {
                "success": True,
                "message": "User account unlocked and set to active."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Setting status to 'active' is always permitted.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found." }

        user["account_sta"] = "active"
        return { "success": True, "message": "User account unlocked and set to active." }

    def enforce_single_session_policy(self, enabled: bool) -> dict:
        """
        Toggle or apply the "single session per user" constraint policy for security.

        Args:
            enabled (bool): True to enable the policy (only one active session per user),
                            False to disable the policy (multiple active sessions allowed).

        Returns:
            dict: {
                "success": True,
                "message": "Policy enabled/disabled. [Optional: users with multiple active sessions: N]",
            }
            or
            {
                "success": False,
                "error": "Reason for failure",
            }

        Notes/Constraints:
            - The actual enforcement on session start/end is handled elsewhere.
            - Report users with >1 active session when enabling (for admin info).
            - No sessions are forcibly ended or modified here.
        """
        if not isinstance(enabled, bool):
            return { "success": False, "error": "Parameter 'enabled' must be a boolean." }

        # Initialize the policy attribute if not already present
        self.single_session_per_user_enabled = enabled
        self.single_session_per_user = enabled

        # Count users with multiple active sessions (for info if enabling)
        if enabled:
            user_active_sessions = {}
            for sess in self.sessions.values():
                if sess["session_status"] == "active":
                    user_active_sessions.setdefault(sess["user_id"], 0)
                    user_active_sessions[sess["user_id"]] += 1
            users_with_multiple = [uid for uid, count in user_active_sessions.items() if count > 1]
            message = "Single session per user policy enabled."
            if users_with_multiple:
                message += f" Warning: {len(users_with_multiple)} users currently have multiple active sessions."
            return { "success": True, "message": message }
        else:
            return { "success": True, "message": "Single session per user policy disabled." }


class WebAppUserSessionManagementSystem(BaseEnv):
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
            if key in {"single_session_per_user", "single_session_per_user_enabled"}:
                normalized = _GeneratedEnvImpl._normalize_policy_flag(value)
                setattr(env, "single_session_per_user_enabled", normalized)
                setattr(env, "single_session_per_user", normalized)
            else:
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_user_sessions(self, **kwargs):
        return self._call_inner_tool('get_user_sessions', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def list_user_active_sessions(self, **kwargs):
        return self._call_inner_tool('list_user_active_sessions', kwargs)

    def get_session_activity_logs(self, **kwargs):
        return self._call_inner_tool('get_session_activity_logs', kwargs)

    def list_user_activity_logs(self, **kwargs):
        return self._call_inner_tool('list_user_activity_logs', kwargs)

    def get_activity_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_activity_log_by_id', kwargs)

    def get_session_status(self, **kwargs):
        return self._call_inner_tool('get_session_status', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def session_policy_info(self, **kwargs):
        return self._call_inner_tool('session_policy_info', kwargs)

    def start_new_session(self, **kwargs):
        return self._call_inner_tool('start_new_session', kwargs)

    def end_session(self, **kwargs):
        return self._call_inner_tool('end_session', kwargs)

    def append_activity_log(self, **kwargs):
        return self._call_inner_tool('append_activity_log', kwargs)

    def lock_user_account(self, **kwargs):
        return self._call_inner_tool('lock_user_account', kwargs)

    def unlock_user_account(self, **kwargs):
        return self._call_inner_tool('unlock_user_account', kwargs)

    def enforce_single_session_policy(self, **kwargs):
        return self._call_inner_tool('enforce_single_session_policy', kwargs)
