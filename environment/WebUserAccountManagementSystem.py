# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import TypedDict, Dict
import hashlib
import uuid
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    full_name: str
    email: str
    status: str  # 'active', 'inactive', or 'deactivated'
    rol: str

class CredentialInfo(TypedDict):
    _id: str
    password_hash: str
    last_password_change: str

class SessionInfo(TypedDict):
    session_id: str
    user_id: str
    login_timestamp: str
    last_activity_timestamp: str
    is_active: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a web-based user account management system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Credentials: {_id: CredentialInfo}
        self.credentials: Dict[str, CredentialInfo] = {}

        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}

        # --- Constraints ---
        # - Only users with 'active' status can establish or maintain sessions.
        # - Passwords must be stored securely as hashes (never in plaintext).
        # - Each session must be associated with a valid user account.
        # - Administrators can terminate any active session at any time.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information using the given username.

        Args:
            username (str): The username to query.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str  # e.g. "User not found"
            }

        Constraints:
            - Searches for the user with matching username.
            - Returns user details if found, otherwise an error.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return {"success": True, "data": user_info}

        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user information using the unique user ID (_id).

        Args:
            _id (str): Unique identifier of the user.

        Returns:
            dict:
                - If user exists: 
                    { "success": True, "data": UserInfo }
                - If user does not exist:
                    { "success": False, "error": "User not found" }

        Constraints:
            - The user with the given _id must exist in the system.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        Retrieve all user accounts in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of all user info dicts, may be empty if no users exist
            }
        Constraints:
            - None for this operation.
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def get_user_status(self, user_id: str) -> dict:
        """
        Check the current status (active/inactive/deactivated) of a user.

        Args:
            user_id (str): The unique user identifier (_id) whose status is to be queried.

        Returns:
            dict:
                - On success: { "success": True, "data": <status_value> }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user["status"] }

    def get_credential_by_user_id(self, user_id: str) -> dict:
        """
        Retrieve the credential entry for a given user ID.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": CredentialInfo,
            }
            or
            {
                "success": False,
                "error": str,  # Reason for error (user or credential not found)
            }
        Constraints:
            - The user ID must correspond to an existing user.
            - The credentials mapping must have an entry for the given user ID.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if user_id not in self.credentials:
            return {"success": False, "error": "Credential entry does not exist for user"}

        return {
            "success": True,
            "data": self.credentials[user_id]
        }


    def verify_password_for_user(self, user_id: str, plaintext_password: str) -> dict:
        """
        Check if a provided plaintext password, when hashed, matches the stored password hash for a given user.

        Args:
            user_id (str): The unique ID of the user whose password is being verified.
            plaintext_password (str): The plaintext password to check.

        Returns:
            dict: On success,
                { "success": True, "data": bool }  # True if matched, False otherwise
                On failure,
                { "success": False, "error": str }

        Constraints:
            - Passwords must be securely compared: hash(plaintext_password) == stored password_hash.
            - User and credential must exist.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Check credentials exist for user
        if user_id not in self.credentials:
            return { "success": False, "error": "Credentials for user not found" }

        cred = self.credentials[user_id]
        stored_hash = cred.get("password_hash", "")
        if not stored_hash:
            return { "success": False, "error": "No stored password hash for user" }

        # Emulate secure hash verification (using SHA256 for demo)
        # In production: use Argon2/bcrypt/etc.
        password_bytes = (plaintext_password or "").encode("utf-8")
        candidate_hash = hashlib.sha256(password_bytes).hexdigest()

        match = candidate_hash == stored_hash

        return { "success": True, "data": match }

    def get_sessions_by_user_id(self, user_id: str) -> dict:
        """
        List all sessions associated with a given user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[SessionInfo],  # All sessions (possibly empty list)
            }
            OR
            {
                "success": False,
                "error": str  # e.g., "User not found"
            }

        Constraints:
            - user_id must exist in the system.
            - Returns all session records linked to the given user, regardless of status.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        sessions = [
            session_info for session_info in self.sessions.values()
            if session_info["user_id"] == user_id
        ]
        return {"success": True, "data": sessions}

    def get_active_sessions_by_user_id(self, user_id: str) -> dict:
        """
        List all currently active sessions for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[SessionInfo],  # Active sessions for this user (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., "User does not exist"
            }

        Constraints:
            - The user must exist (user_id must be present in self.users).
            - Only sessions where is_active == True and user_id matches are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        active_sessions = [
            session_info
            for session_info in self.sessions.values()
            if session_info["user_id"] == user_id and session_info["is_active"]
        ]

        return { "success": True, "data": active_sessions }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve detailed information for a session using its session ID.

        Args:
            session_id (str): The unique identifier of the session.

        Returns:
            dict:
                On success:
                    {"success": True, "data": SessionInfo}  # SessionInfo for the session.
                On failure:
                    {"success": False, "error": "Session not found"}
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session not found"}
        return {"success": True, "data": session}

    def list_all_active_sessions(self) -> dict:
        """
        List all active sessions across all users.

        Returns:
            dict:
                - success: True if operation succeeds.
                - data: List[SessionInfo] where is_active is True. May be an empty list if no active sessions exist.

        Constraints:
            - Only sessions where is_active is True will be returned.
        """
        active_sessions = [
            session_info
            for session_info in self.sessions.values()
            if session_info["is_active"] is True
        ]
        return { "success": True, "data": active_sessions }

    def get_session_user_id(self, session_id: str) -> dict:
        """
        For a given session ID, return the associated user ID.

        Args:
            session_id (str): The session's unique identifier.

        Returns:
            dict:
                On success:
                    {"success": True, "data": str}  # user_id associated with session
                On failure:
                    {"success": False, "error": str}  # "Session not found"
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session not found"}
        return {"success": True, "data": session["user_id"]}

    def terminate_session_by_id(self, session_id: str) -> dict:
        """
        Terminates (logouts) a specific session by setting its is_active attribute to False.

        Args:
            session_id (str): The identifier of the session to terminate.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Session <session_id> terminated (set as inactive)."
                }
                On failure: {
                    "success": False,
                    "error": "Session not found."
                }

        Constraints:
            - Any session can be terminated regardless of its current is_active state.
            - No permissions are checked for this operation (administrators can terminate any session).
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session not found." }

        session["is_active"] = False
        return {
            "success": True,
            "message": f"Session {session_id} terminated (set as inactive)."
        }

    def terminate_all_sessions_for_user(self, user_id: str) -> dict:
        """
        End (invalidate) all active sessions for the specified user.

        Args:
            user_id (str): The user _id whose sessions should be ended.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Terminated X active session(s) for user <user_id>."
                }
                If user does not exist:
                {
                    "success": False,
                    "error": "User not found."
                }

        Constraints:
            - user_id must exist in the system.
            - All sessions associated with this user are set to is_active=False if active.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        count_terminated = 0
        for session in self.sessions.values():
            if session["user_id"] == user_id and session["is_active"]:
                session["is_active"] = False
                count_terminated += 1

        return {
            "success": True,
            "message": f"Terminated {count_terminated} active session(s) for user {user_id}."
        }

    def terminate_multiple_sessions(self, session_ids: list[str]) -> dict:
        """
        Bulk terminate a provided list of session IDs.
    
        Args:
            session_ids (list[str]): List of session IDs to be terminated.

        Returns:
            dict: {
                "success": True,
                "message": "Terminated N sessions."
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Only sessions that exist and are currently active will be terminated.
            - Skips session IDs that do not exist or are already inactive.
        """
        if not session_ids or not isinstance(session_ids, list):
            return { "success": False, "error": "No session IDs provided." }
    
        terminated_count = 0
        for sid in session_ids:
            session = self.sessions.get(sid)
            if session and session.get("is_active", False):
                session["is_active"] = False
                terminated_count += 1
                # Optionally, could update timestamp or add audit log here

        return {
            "success": True,
            "message": f"Terminated {terminated_count} session(s)."
        }

    def update_user_status(self, user_id: str, new_status: str) -> dict:
        """
        Change the user status to 'active', 'inactive', or 'deactivated'.

        Args:
            user_id (str): The _id of the user to update.
            new_status (str): The desired status ('active', 'inactive', 'deactivated').

        Returns:
            dict: {
                "success": True,
                "message": "User status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "User not found" | "Invalid status value"
            }

        Constraints:
            - Only 'active', 'inactive', or 'deactivated' are valid values for status.
            - The user must exist in the system.
        """
        allowed_statuses = {"active", "inactive", "deactivated"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status value" }
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        self.users[user_id]["status"] = new_status
        return { "success": True, "message": f"User status updated to {new_status}." }

    def update_user_password(self, user_id: str, new_password_hash: str, change_time: str) -> dict:
        """
        Change a user's password hash and update last_password_change.

        Args:
            user_id (str): The unique user identifier.
            new_password_hash (str): The new (securely computed) password hash; must not be None or empty.
            change_time (str): The timestamp (as string) when the change occurs.

        Returns:
            dict: {
                "success": True,
                "message": "Password updated for user <user_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Password hash must not be empty.
            - Credential record for user_id must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if user_id not in self.credentials:
            return {"success": False, "error": "Credential record not found for user"}
        if not new_password_hash or new_password_hash.strip() == "":
            return {"success": False, "error": "Password hash cannot be empty"}
    
        # Update password hash and last_password_change
        self.credentials[user_id]["password_hash"] = new_password_hash
        self.credentials[user_id]["last_password_change"] = change_time

        return {"success": True, "message": f"Password updated for user {user_id}"}


    def create_new_session(self, user_id: str) -> dict:
        """
        Establish a new session for an 'active' user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Session created",
                        "session": SessionInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error reason>
                    }
    
        Constraints:
            - The user must exist and have status 'active'.
            - Each session must have a unique session_id.
            - The session is associated with the user_id.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        if user.get("status") != "active":
            return {"success": False, "error": "User is not active. Session cannot be created."}

        # Create unique session_id
        for _ in range(5):  # Limit retries for safety
            session_id = str(uuid.uuid4())
            if session_id not in self.sessions:
                break
        else:
            return {"success": False, "error": "Failed to generate a unique session id"}

        now = datetime.utcnow().isoformat() + 'Z'

        session_info: SessionInfo = {
            "session_id": session_id,
            "user_id": user_id,
            "login_timestamp": now,
            "last_activity_timestamp": now,
            "is_active": True
        }
        self.sessions[session_id] = session_info

        return {
            "success": True,
            "message": "Session created",
            "session": session_info
        }

    def invalidate_all_sessions(self) -> dict:
        """
        End (invalidate) all sessions in the system as an emergency administrative action.

        This operation forcibly marks all sessions as inactive, regardless of current state or user.
        Does not delete session records, only sets is_active = False for each session.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "message": "All sessions have been invalidated."
            }

        Constraints:
            - No input parameters required.
            - All sessions (if any) set to is_active = False.
        """
        for session in self.sessions.values():
            session["is_active"] = False
        return {
            "success": True,
            "message": "All sessions have been invalidated."
        }

    def reset_user_credentials(self, user_id: str, new_password_hash: str, reset_time: str) -> dict:
        """
        Reset a user's password and related credential data.

        Args:
            user_id (str): The user's unique ID whose credentials are to be reset.
            new_password_hash (str): The new password hash (should NOT be plaintext).
            reset_time (str): The timestamp of the reset (e.g., ISO format).

        Returns:
            dict:
                - On success: { "success": True, "message": "User credentials reset." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - User must exist in the system.
            - Corresponding Credential entry must exist.
            - Password must be set as a hash, not as plaintext.
            - Empty hashes are invalid.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User ID does not exist." }

        # Check credentials exist for user
        if user_id not in self.credentials:
            return { "success": False, "error": "Credential record not found for user." }

        # Validate new_password_hash is not empty or obviously insecure
        if not new_password_hash or not isinstance(new_password_hash, str):
            return { "success": False, "error": "Password hash must be a non-empty string." }
        if len(new_password_hash) < 10:  # Simple check, not a guarantee
            return { "success": False, "error": "Password hash appears too short for security." }

        # Reset the credentials
        cred = self.credentials[user_id]
        cred["password_hash"] = new_password_hash
        cred["last_password_change"] = reset_time

        return { "success": True, "message": "User credentials reset." }

    def create_new_user(
        self,
        _id: str,
        username: str,
        full_name: str,
        email: str,
        status: str,
        rol: str
    ) -> dict:
        """
        Add a new user to the system.

        Args:
            _id (str): Unique user identifier
            username (str): Unique username
            full_name (str): Full name of the user
            email (str): User's email address
            status (str): One of 'active', 'inactive', or 'deactivated'
            rol (str): User's role

        Returns:
            dict: {
                "success": True,
                "message": "User created successfully"
            }
            On failure:
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - _id must be unique (not already in self.users)
            - username must be unique (not used by any user)
            - status must be 'active', 'inactive', or 'deactivated'
            - All fields must be provided and non-empty
        """
        valid_statuses = {"active", "inactive", "deactivated"}
    
        # Check required fields
        if not all([_id, username, full_name, email, status, rol]):
            return {"success": False, "error": "All fields must be provided and non-empty"}
    
        # Check _id uniqueness
        if _id in self.users:
            return {"success": False, "error": "User ID already exists"}
    
        # Check username uniqueness
        for user in self.users.values():
            if user["username"] == username:
                return {"success": False, "error": "Username already exists"}
    
        # Check valid status
        if status not in valid_statuses:
            return {"success": False, "error": "Invalid status value"}
    
        # Create user
        user_info: UserInfo = {
            "_id": _id,
            "username": username,
            "full_name": full_name,
            "email": email,
            "status": status,
            "rol": rol
        }
    
        self.users[_id] = user_info

        return {"success": True, "message": "User created successfully"}

    def delete_user(self, user_id: str) -> dict:
        """
        Completely remove a user account and all associated data (credentials, sessions).

        Args:
            user_id (str): The unique ID of the user to delete.

        Returns:
            dict: 
                {"success": True, "message": "User and all associated data deleted."}
                or
                {"success": False, "error": "User does not exist"}

        Constraints:
            - Removes the user record from the system.
            - Removes any credentials record for that user.
            - Removes all session records for that user (active or inactive).
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Remove user
        del self.users[user_id]

        # Remove credentials (if present—no error if missing)
        if user_id in self.credentials:
            del self.credentials[user_id]

        # Remove all sessions for user
        sessions_to_delete = [sid for sid, sinfo in self.sessions.items() if sinfo["user_id"] == user_id]
        for sid in sessions_to_delete:
            del self.sessions[sid]

        return {"success": True, "message": "User and all associated data deleted."}


class WebUserAccountManagementSystem(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_user_status(self, **kwargs):
        return self._call_inner_tool('get_user_status', kwargs)

    def get_credential_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_credential_by_user_id', kwargs)

    def verify_password_for_user(self, **kwargs):
        return self._call_inner_tool('verify_password_for_user', kwargs)

    def get_sessions_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_user_id', kwargs)

    def get_active_sessions_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_active_sessions_by_user_id', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def list_all_active_sessions(self, **kwargs):
        return self._call_inner_tool('list_all_active_sessions', kwargs)

    def get_session_user_id(self, **kwargs):
        return self._call_inner_tool('get_session_user_id', kwargs)

    def terminate_session_by_id(self, **kwargs):
        return self._call_inner_tool('terminate_session_by_id', kwargs)

    def terminate_all_sessions_for_user(self, **kwargs):
        return self._call_inner_tool('terminate_all_sessions_for_user', kwargs)

    def terminate_multiple_sessions(self, **kwargs):
        return self._call_inner_tool('terminate_multiple_sessions', kwargs)

    def update_user_status(self, **kwargs):
        return self._call_inner_tool('update_user_status', kwargs)

    def update_user_password(self, **kwargs):
        return self._call_inner_tool('update_user_password', kwargs)

    def create_new_session(self, **kwargs):
        return self._call_inner_tool('create_new_session', kwargs)

    def invalidate_all_sessions(self, **kwargs):
        return self._call_inner_tool('invalidate_all_sessions', kwargs)

    def reset_user_credentials(self, **kwargs):
        return self._call_inner_tool('reset_user_credentials', kwargs)

    def create_new_user(self, **kwargs):
        return self._call_inner_tool('create_new_user', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

