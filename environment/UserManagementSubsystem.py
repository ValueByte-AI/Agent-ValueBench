# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
from typing import Optional
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    email: str
    status: str
    date_created: str
    last_login: str

class RoleInfo(TypedDict):
    role_id: str
    role_name: str
    permission: str

class UserCredentialInfo(TypedDict):
    _id: str           # user id
    password_hash: str
    password_last_changed: str
    two_factor_enabled: bool

class UserAccessRightInfo(TypedDict):
    _id: str           # user id
    resource_id: str
    access_level: str

class UserActivityLogInfo(TypedDict):
    activity_id: str
    user_id: str
    action: str
    timestamp: str
    result: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        # status is constrained to: active, inactive, suspended, deactivated, etc.
        self.users: Dict[str, UserInfo] = {}

        # Roles: {role_id: RoleInfo}
        self.roles: Dict[str, RoleInfo] = {}

        # User Credentials: {_id (user id): UserCredentialInfo}
        self.credentials: Dict[str, UserCredentialInfo] = {}

        # User Access Rights: {_id (user id): List[UserAccessRightInfo]}
        # Each user may have multiple resource access rights.
        self.access_rights: Dict[str, List[UserAccessRightInfo]] = {}

        # User Activity Logs: List[UserActivityLogInfo]; immutable, must be retained for audit.
        self.activity_logs: List[UserActivityLogInfo] = []

        # Constraints:
        # - User status values must be one of: active, inactive, suspended, deactivated, etc.
        # - Only users with 'active' status can access protected resources.
        # - Users may have one or more roles assigned (not shown explicitly in state, but could be a mapping).
        # - Activity logs must be append-only and immutable for audit/compliance.

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve the full information of a user by their unique user ID.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict:
                If the user exists:
                    { "success": True, "data": UserInfo }
                If not:
                    { "success": False, "error": "User not found" }
        Constraints:
            - No modification to state. No status check performed.
        """
        user_info = self.users.get(_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve the full user information for a given username.

        Args:
            username (str): The username of the user to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - Username lookup is case-sensitive.
            - Usernames are assumed to be unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def list_all_users(self) -> dict:
        """
        Returns a list of all users registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # All user info dicts (empty list if no users)
            }
        """
        user_list = list(self.users.values())
        return { "success": True, "data": user_list }

    def list_users_by_status(self, status: str) -> dict:
        """
        Return a list of users whose status matches the provided status.

        Args:
            status (str): The user status to filter by (e.g., "active", "inactive", "suspended", "deactivated", etc.)

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[UserInfo],  # May be empty if no users match
                }
              OR
                {
                    "success": False,
                    "error": str  # Explanation, e.g. invalid status
                }

        Constraints:
            - The status argument must be one of the allowed values: active, inactive, suspended, deactivated, etc.
        """
        allowed_statuses = {"active", "inactive", "suspended", "deactivated"}
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid status" }

        filtered_users = [
            user_info for user_info in self.users.values()
            if user_info["status"] == status
        ]

        return { "success": True, "data": filtered_users }

    def get_user_status(self, _id: str) -> dict:
        """
        Fetch the status (active, inactive, etc.) of a specific user.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict: 
                { "success": True, "data": str }                   # The user's status
                or
                { "success": False, "error": "User not found" }    # If user does not exist

        Constraints:
            - Only checks if user exists. Does not enforce any access permission.
            - User status values are managed elsewhere via constraints.
        """
        user = self.users.get(_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user["status"] }

    def list_user_roles(self, user_id: str) -> dict:
        """
        List all roles assigned to a user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[RoleInfo]   # List of role infos assigned to this user (empty if none)
            }
            OR
            {
                "success": False,
                "error": str  # e.g., user does not exist
            }

        Constraints:
            - Returns empty list if user exists but has no roles.
            - Returns error if user does not exist.
            - Only returns roles present in the roles dictionary.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Ensure user_roles mapping exists (as it is implied by the environment logic)
        if not hasattr(self, 'user_roles'):
            # If not present, treat as no roles assigned for any user
            user_roles = []
        else:
            user_roles = self.user_roles.get(user_id, [])

        # Collect RoleInfo for assigned role ids
        result = []
        for role_id in user_roles:
            role_info = self.roles.get(role_id)
            if role_info:
                result.append(role_info)

        return {"success": True, "data": result}

    def get_role_by_id(self, role_id: str) -> dict:
        """
        Retrieve full details of a role by role_id.

        Args:
            role_id (str): The unique identifier for the role.

        Returns:
            dict: 
                {"success": True, "data": RoleInfo} if found,
                {"success": False, "error": str} if not found.
        """
        role = self.roles.get(role_id)
        if role is None:
            return {"success": False, "error": "Role not found"}
        return {"success": True, "data": role}

    def list_all_roles(self) -> dict:
        """
        Return details of all defined roles in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RoleInfo],  # may be empty if no roles are defined
            }
        """
        all_roles = list(self.roles.values())
        return {"success": True, "data": all_roles}

    def list_user_access_rights(self, _id: str) -> dict:
        """
        Retrieve all resource access rights for a specified user.

        Args:
            _id (str): The unique user ID.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserAccessRightInfo],  # List may be empty if user has no access rights
                }
                or
                {
                    "success": False,
                    "error": str  # e.g., "User not found"
                }

        Constraints:
            - The user must exist in the system.
        """
        if _id not in self.users:
            return { "success": False, "error": "User not found" }

        rights = self.access_rights.get(_id, [])
        return { "success": True, "data": rights }

    def get_user_credential_info(self, _id: str = "", user_id: str = "") -> dict:
        """
        Retrieve credential information (password hash, password last changed, 2FA enabled)
        for the given user id.

        Args:
            _id (str): The user id.

        Returns:
            dict: {
                "success": True,
                "data": UserCredentialInfo,
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure (e.g., user credential info not found)
            }
        Constraints:
            - Returns only what's in the credentials store, irrespective of the user's status.
        """
        lookup_id = _id or user_id
        credential = self.credentials.get(lookup_id)
        if credential is None:
            return { "success": False, "error": "User credential info not found" }
        return { "success": True, "data": credential }

    def list_user_activity_logs(self, user_id: str) -> dict:
        """
        Retrieve all activity log entries for a specific user.

        Args:
            user_id (str): The unique identifier of the user whose logs are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[UserActivityLogInfo]  # May be empty if no logs exist for user
            }
            or
            {
                "success": False,
                "error": str  # Error message if user not found, etc.
            }

        Constraints:
            - User must exist in the subsystem.
            - Log data is append-only and immutable (no modification here).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        logs = [log for log in self.activity_logs if log["user_id"] == user_id]
        return { "success": True, "data": logs }

    def get_activity_log_by_id(self, activity_id: str) -> dict:
        """
        Retrieve details of a specific activity log entry by activity_id.

        Args:
            activity_id (str): Unique identifier of the activity log entry.

        Returns:
            dict:
                - If found: {"success": True, "data": <UserActivityLogInfo>}
                - If not found: {"success": False, "error": "Activity log entry not found"}
        """
        for log in self.activity_logs:
            if log["activity_id"] == activity_id:
                return {"success": True, "data": log}
        return {"success": False, "error": "Activity log entry not found"}

    def check_user_access_to_resource(self, user_id: str, resource_id: str) -> dict:
        """
        Determine if a user has access rights to the specified resource, and if so, return the access level.

        Args:
            user_id (str): The user to check.
            resource_id (str): The resource identifier.

        Returns:
            dict: On success, if access is granted:
                  {
                    "success": True,
                    "data": {
                        "user_id": <user_id>,
                        "resource_id": <resource_id>,
                        "access_level": <str>
                    }
                  }
                  If access not granted, or on error:
                  {
                    "success": False,
                    "error": <error string>
                  }

        Constraints:
            - User must exist and must have 'active' status.
            - Access rights must explicitly grant access to the specified resource.
        """
        # Check user existence
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}

        # Check user status
        if user_info["status"] != "active":
            return {"success": False, "error": "User is not active; access denied"}

        # Check access rights for this resource
        user_access_list = self.access_rights.get(user_id, [])
        for access_info in user_access_list:
            if access_info["resource_id"] == resource_id:
                return {
                    "success": True,
                    "data": {
                        "user_id": user_id,
                        "resource_id": resource_id,
                        "access_level": access_info["access_level"]
                    }
                }

        return {"success": False, "error": "User has no access rights for the specified resource"}

    def add_user(
        self,
        _id: str,
        username: str,
        display_name: str,
        email: str,
        status: str = "active",
        date_created: str = "",
        last_login: str = ""
    ) -> dict:
        """
        Add a new user to the system with required attributes.

        Args:
            _id (str): Unique user ID.
            username (str): Unique username.
            display_name (str): Display name for the user.
            email (str): Email address.
            status (str, optional): Initial user status. Defaults to "active".
            date_created (str, optional): Date created (ISO8601 or similar); will be set to now if empty.
            last_login (str, optional): Last login time (initially can be empty).

        Returns:
            dict: {
                "success": True,
                "message": "User <username> (<_id>) added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Status must be in the permitted set ("active", "inactive", "suspended", "deactivated", etc.).
            - _id and username must be unique.
        """

        # Check if user ID is unique
        if _id in self.users:
            return {"success": False, "error": "User ID already exists."}

        # Check if username is unique
        if any(u["username"] == username for u in self.users.values()):
            return {"success": False, "error": "Username already exists."}

        # Acceptable status values (extend as needed)
        allowed_status = {"active", "inactive", "suspended", "deactivated"}
        if status not in allowed_status:
            return {"success": False, "error": f"Invalid status '{status}'."}

        if not all([_id, username, display_name, email]):
            return {"success": False, "error": "Missing required user attributes."}

        if not date_created:
            date_created = datetime.utcnow().isoformat()
        if not last_login:
            last_login = ""

        user_info: UserInfo = {
            "_id": _id,
            "username": username,
            "display_name": display_name,
            "email": email,
            "status": status,
            "date_created": date_created,
            "last_login": last_login
        }

        self.users[_id] = user_info
        return {"success": True, "message": f"User {username} ({_id}) added."}

    def update_user_status(self, user_id: str, new_status: str) -> dict:
        """
        Change the status of a user (must set to one of the allowed values).

        Args:
            user_id (str): The unique ID of the user whose status is to be changed.
            new_status (str): The new status value; must be one of the allowed values:
                'active', 'inactive', 'suspended', 'deactivated', etc.

        Returns:
            dict: {
                "success": True,
                "message": "User status updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The user must exist in the system.
            - The new status must be in the set of allowed statuses.
        """
        allowed_statuses = {"active", "inactive", "suspended", "deactivated"}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status value. Allowed values are: {', '.join(allowed_statuses)}."}

        user["status"] = new_status
        return {"success": True, "message": "User status updated successfully."}

    def update_user_info(self, _id: str, fields: Optional[dict] = None, **kwargs) -> dict:
        """
        Update modifiable user profile details (such as display_name, email) for the specified user.

        Args:
            _id (str): The user ID to update.
            **fields: Arbitrary profile fields to update, e.g., display_name="New Name", email="email@domain.com".

        Returns:
            dict: {
                "success": True,
                "message": "User info updated."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Only 'display_name' and 'email' are allowed to be updated.
            - User must exist.
            - Attempts to update other fields will be ignored.
            - At least one updatable field must be specified.
        """
        if _id not in self.users:
            return {"success": False, "error": "User not found."}

        allowed_fields = {"display_name", "email"}
        raw_fields: Dict[str, Any] = {}
        if isinstance(fields, dict):
            raw_fields.update(fields)
        raw_fields.update(kwargs)
        update_fields = {k: v for k, v in raw_fields.items() if k in allowed_fields}
    
        if not update_fields:
            return {"success": False, "error": "No updatable fields provided (allowed: display_name, email)."}

        # Update the user's info
        for key, value in update_fields.items():
            self.users[_id][key] = value

        return {"success": True, "message": "User info updated."}

    def set_user_roles(self, user_id: str, role_ids: List[str]) -> dict:
        """
        Assign one or multiple roles (by role ID) to a user.
    
        Args:
            user_id (str): The unique ID of the user.
            role_ids (List[str]): List of role IDs to assign to the user.
        
        Returns:
            dict: 
                - If success: {"success": True, "message": "Roles assigned to user <user_id>"}
                - If error: {"success": False, "error": <reason>}
    
        Constraints:
            - User must exist.
            - Each role_id in role_ids must be a valid role in the system.
            - Duplicated role_ids will be ignored (each role assigned at most once).
            - If role_ids is empty, user will have no roles.
        """
        # Ensure role mapping storage exists
        if not hasattr(self, "user_roles"):
            self.user_roles: Dict[str, List[str]] = {}

        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        
        # Validate all role_ids exist
        invalid_roles = [r for r in role_ids if r not in self.roles]
        if invalid_roles:
            return { 
                "success": False, 
                "error": f"Invalid role IDs: {', '.join(invalid_roles)}" 
            }
    
        # Remove duplicates
        unique_role_ids = list(set(role_ids))
        self.user_roles[user_id] = unique_role_ids

        return { 
            "success": True, 
            "message": f"Roles assigned to user {user_id}" 
        }

    def remove_user_role(self, user_id: str, role_id: str) -> dict:
        """
        Remove a role from a user.

        Args:
            user_id (str): The user's unique id.
            role_id (str): The role id to be removed from the user.

        Returns:
            dict: {
                "success": True,
                "message": "Role <role_id> removed from user <user_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Both user and role must exist.
            - The role must be currently assigned to the user.
            - User-role mapping must be maintained (assumed as self.user_roles).
        """
        # Assure user-role mapping exists
        if not hasattr(self, 'user_roles'):
            self.user_roles: Dict[str, List[str]] = {}

        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if role_id not in self.roles:
            return { "success": False, "error": "Role does not exist." }
        if user_id not in self.user_roles or role_id not in self.user_roles[user_id]:
            return { "success": False, "error": "User does not have this role assigned." }

        self.user_roles[user_id].remove(role_id)

        # Clean up if user now has no roles (optional)
        if len(self.user_roles[user_id]) == 0:
            del self.user_roles[user_id]

        return { "success": True, "message": f"Role {role_id} removed from user {user_id}." }


    def update_user_credential(
        self, 
        _id: str, 
        password_hash: Optional[str] = None, 
        two_factor_enabled: Optional[bool] = None
    ) -> dict:
        """
        Change a user's password and/or 2FA settings.

        Args:
            _id (str): The user id whose credentials are to be updated.
            password_hash (Optional[str]): New password hash to set (optional).
            two_factor_enabled (Optional[bool]): Enable/disable 2FA (optional).

        Returns:
            dict: {
                "success": True,
                "message": "User credential updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - User and their credentials must exist.
            - password_last_changed should be updated to current time if password_hash is changed.
            - Must not change any value if neither parameter is given.
        """
        if _id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if _id not in self.credentials:
            return {"success": False, "error": "User credentials do not exist."}
        if password_hash is None and two_factor_enabled is None:
            return {"success": False, "error": "No changes specified (nothing to update)."}

        cred = self.credentials[_id]
        changed = False

        if password_hash is not None:
            # Assuming non-empty string is required for password hash
            if not isinstance(password_hash, str) or not password_hash:
                return {"success": False, "error": "Invalid password_hash provided."}
            cred["password_hash"] = password_hash
            # Update password_last_changed timestamp (ISO 8601 string)
            cred["password_last_changed"] = datetime.utcnow().isoformat()
            changed = True

        if two_factor_enabled is not None:
            if not isinstance(two_factor_enabled, bool):
                return {"success": False, "error": "two_factor_enabled must be a boolean."}
            cred["two_factor_enabled"] = two_factor_enabled
            changed = True

        if changed:
            self.credentials[_id] = cred
            return {"success": True, "message": "User credential updated successfully."}
        else:
            return {"success": False, "error": "No valid changes to make."}

    def add_access_right_to_user(self, user_id: str, resource_id: str, access_level: str) -> dict:
        """
        Assign access to a specific resource at a given access level to a user.

        Args:
            user_id (str): The unique user ID.
            resource_id (str): The resource identifier.
            access_level (str): The level of access to be granted.

        Returns:
            dict: {
               "success": True,
               "message": "Access right assigned to user."
            }
            OR
            {
               "success": False,
               "error": <reason>
            }

        Constraints:
            - The user must exist.
            - Only users with 'active' status can receive new access rights.
            - Do not add a duplicate (resource_id, access_level) for the same user.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        # Check user status
        if user.get("status") != "active":
            return { "success": False, "error": "Only users with 'active' status can be assigned access rights." }

        # Get current access rights or initialize
        user_rights = self.access_rights.get(user_id, [])

        # Check for duplicate assignment
        for ar in user_rights:
            if ar["resource_id"] == resource_id and ar["access_level"] == access_level:
                return { "success": False, "error": "User already has this access right for the resource." }

        # Prepare new access right record
        new_access_right = {
            "_id": user_id,
            "resource_id": resource_id,
            "access_level": access_level
        }

        # Add access right
        user_rights.append(new_access_right)
        self.access_rights[user_id] = user_rights

        return { "success": True, "message": "Access right assigned to user." }

    def remove_access_right_from_user(self, user_id: str, resource_id: str) -> dict:
        """
        Remove a specific resource access right from a user.

        Args:
            user_id (str): The ID of the user for whom resource access is to be removed.
            resource_id (str): The ID of the resource whose access right should be removed.

        Returns:
            dict:
                On success: {"success": True, "message": "Access right removed from user <user_id> for resource <resource_id>."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - User must exist in the system.
            - The user must have at least one access right for the specified resource_id.
            - All UserAccessRightInfo entries for this (user, resource_id) will be removed.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        if user_id not in self.access_rights or not self.access_rights[user_id]:
            return {"success": False, "error": "User has no access rights"}

        original_len = len(self.access_rights[user_id])
        new_access_list = [
            ar for ar in self.access_rights[user_id]
            if ar["resource_id"] != resource_id
        ]
        if len(new_access_list) == original_len:
            return {"success": False, "error": "User has no access rights for this resource"}

        self.access_rights[user_id] = new_access_list

        return {"success": True, "message": f"Access right removed from user {user_id} for resource {resource_id}."}

    def append_activity_log(
        self,
        activity_id: str,
        user_id: str,
        action: str,
        timestamp: str,
        result: str
    ) -> dict:
        """
        Append a new audit activity log entry to the immutable activity log list.

        Args:
            activity_id (str): Unique identifier for the activity log entry.
            user_id (str): The user associated with the activity.
            action (str): The action performed.
            timestamp (str): When the action occurred (string/ISO time).
            result (str): Outcome or result of the action.

        Returns:
            dict: {
                "success": True,
                "message": "Activity log appended."
            } on success, or
            {
                "success": False,
                "error": "Activity ID already exists" | "Missing required field"
            }
    
        Constraints:
            - Log list is append-only and immutable.
            - activity_id should be unique.
            - All fields must be provided (not None).
        """
        # Check fields are all present
        if not all([activity_id, user_id, action, timestamp, result]):
            return {"success": False, "error": "Missing required field"}

        # Check for duplicate activity_id for immutability/integrity
        if any(log["activity_id"] == activity_id for log in self.activity_logs):
            return {"success": False, "error": "Activity ID already exists"}

        log_entry = {
            "activity_id": activity_id,
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp,
            "result": result
        }
        self.activity_logs.append(log_entry)
        return {"success": True, "message": "Activity log appended."}

    def deactivate_user(self, user_id: str) -> dict:
        """
        Transition a user's status to 'deactivated'.

        Args:
            user_id (str): The unique user identifier (_id) to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> deactivated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The user must exist in the system.
            - If already deactivated, operation is considered a no-op and returns an error.
            - Status must be set to 'deactivated' (allowed value).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }
        if user["status"] == "deactivated":
            return { "success": False, "error": "User is already deactivated." }

        user["status"] = "deactivated"
        self.users[user_id] = user  # Explicitly re-store for clarity, though dict is by reference.
        return { "success": True, "message": f"User {user_id} deactivated." }

    def suspend_user(self, user_id: str) -> dict:
        """
        Transition a user's status specifically to 'suspended'.

        Args:
            user_id (str): Unique identifier of the user whose status is to be set.

        Returns:
            dict: {
                "success": True,
                "message": "User <id> suspended."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Fails if the user does not exist.
            - Fails if the user is already suspended.
            - Only updates the 'status' field to 'suspended'.
            - Must conform to allowed status values.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found." }

        if user["status"] == "suspended":
            return { "success": False, "error": "User is already suspended." }

        # (Optional: Enforce allowed status values, but status should always accept 'suspended' as per environment)
        user["status"] = "suspended"
        return { "success": True, "message": f"User {user_id} suspended." }

    def activate_user(self, _id: str) -> dict:
        """
        Transition the specified user's status to 'active'.

        Args:
            _id (str): The unique identifier of the user to activate.

        Returns:
            dict: {
                "success": True,
                "message": "User status set to active"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist in the system.
            - If the user is already 'active', the operation fails gracefully.
        """
        user = self.users.get(_id)
        if not user:
            return { "success": False, "error": "User not found" }

        if user["status"] == "active":
            return { "success": False, "error": "User is already active" }

        user["status"] = "active"
        self.users[_id] = user  # Ensure change is persisted

        return { "success": True, "message": "User status set to active" }

    def delete_user(self, user_id: str) -> dict:
        """
        Permanently remove a user (and associated credentials and access rights) from the system.
    
        Args:
            user_id (str): The _id of the user to delete.
        
        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "User '<username>' permanently deleted."
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }
    
        Constraints:
            - All user records must be deleted from users, credentials, and access_rights.
            - User activity logs MUST NOT be deleted or edited (must be retained for audit/compliance).
            - Returns error if user does not exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
    
        username = self.users[user_id]["username"]

        # Remove user from all relevant stores
        self.users.pop(user_id, None)
        self.credentials.pop(user_id, None)
        self.access_rights.pop(user_id, None)
        if hasattr(self, "user_roles") and isinstance(self.user_roles, dict):
            self.user_roles.pop(user_id, None)
        # Do NOT touch self.activity_logs

        return {
            "success": True,
            "message": f"User '{username}' permanently deleted."
        }


class UserManagementSubsystem(BaseEnv):
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
            normalized = copy.deepcopy(value)
            if key == "user_roles":
                if isinstance(normalized, str):
                    try:
                        normalized = json.loads(normalized)
                    except Exception:
                        normalized = {}
                if not isinstance(normalized, dict):
                    normalized = {}
                cleaned_roles = {}
                for user_id, role_ids in normalized.items():
                    if isinstance(role_ids, list):
                        cleaned_roles[str(user_id)] = [str(role_id) for role_id in role_ids]
                normalized = cleaned_roles
            setattr(env, key, normalized)

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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def list_users_by_status(self, **kwargs):
        return self._call_inner_tool('list_users_by_status', kwargs)

    def get_user_status(self, **kwargs):
        return self._call_inner_tool('get_user_status', kwargs)

    def list_user_roles(self, **kwargs):
        return self._call_inner_tool('list_user_roles', kwargs)

    def get_role_by_id(self, **kwargs):
        return self._call_inner_tool('get_role_by_id', kwargs)

    def list_all_roles(self, **kwargs):
        return self._call_inner_tool('list_all_roles', kwargs)

    def list_user_access_rights(self, **kwargs):
        return self._call_inner_tool('list_user_access_rights', kwargs)

    def get_user_credential_info(self, **kwargs):
        return self._call_inner_tool('get_user_credential_info', kwargs)

    def list_user_activity_logs(self, **kwargs):
        return self._call_inner_tool('list_user_activity_logs', kwargs)

    def get_activity_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_activity_log_by_id', kwargs)

    def check_user_access_to_resource(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_resource', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_status(self, **kwargs):
        return self._call_inner_tool('update_user_status', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def set_user_roles(self, **kwargs):
        return self._call_inner_tool('set_user_roles', kwargs)

    def remove_user_role(self, **kwargs):
        return self._call_inner_tool('remove_user_role', kwargs)

    def update_user_credential(self, **kwargs):
        return self._call_inner_tool('update_user_credential', kwargs)

    def add_access_right_to_user(self, **kwargs):
        return self._call_inner_tool('add_access_right_to_user', kwargs)

    def remove_access_right_from_user(self, **kwargs):
        return self._call_inner_tool('remove_access_right_from_user', kwargs)

    def append_activity_log(self, **kwargs):
        return self._call_inner_tool('append_activity_log', kwargs)

    def deactivate_user(self, **kwargs):
        return self._call_inner_tool('deactivate_user', kwargs)

    def suspend_user(self, **kwargs):
        return self._call_inner_tool('suspend_user', kwargs)

    def activate_user(self, **kwargs):
        return self._call_inner_tool('activate_user', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)
