# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import time
import uuid
from typing import Optional, Dict
from typing import Optional
from datetime import datetime



class TenantInfo(TypedDict):
    tenant_id: str
    tenant_name: str
    status: str

class UserInfo(TypedDict):
    _id: str
    tenant_id: str
    email: str
    username: str
    account_status: str
    registration_date: str  # or float, depending on expected format
    last_login: Optional[str]  # or Optional[float], depending on design

class AuthTokenInfo(TypedDict):
    token_value: str
    user_id: str
    tenant_id: str
    token_type: str
    creation_time: str  # or float
    expiry_time: str  # or float
    token_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Tenants: {tenant_id: TenantInfo}
        self.tenants: Dict[str, TenantInfo] = {}

        # Users: {user_id (_id): UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # AuthTokens: {token_value: AuthTokenInfo}
        self.auth_tokens: Dict[str, AuthTokenInfo] = {}

        # Constraints:
        # - Each User belongs to exactly one Tenant.
        # - AuthTokens must reference a valid User and Tenant, and be valid (not expired or already used).
        # - Confirmation tokens are only valid for users with account_status = "pending_confirmation".
        # - User data and AuthTokens are isolated by tenant—no cross-tenant access.
        # - Upon successful confirmation, user account_status is set to "active", and the token is marked as used or invalid.
        self.current_time: Optional[str] = None

    @staticmethod
    def _parse_time_like(value):
        if value is None:
            raise ValueError("Timestamp is missing")
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            raise ValueError("Timestamp is empty")
        try:
            return float(text)
        except Exception:
            pass
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return datetime.fromisoformat(text).timestamp()
        except Exception as exc:
            raise ValueError("Timestamp format unsupported") from exc

    def _infer_current_time(self) -> float:
        candidates = []

        def add_candidate(value):
            try:
                candidates.append(self._parse_time_like(value))
            except Exception:
                pass

        for user in self.users.values():
            add_candidate(user.get("registration_date"))
            add_candidate(user.get("last_login"))

        for token in self.auth_tokens.values():
            add_candidate(token.get("creation_time"))
            if token.get("token_status") in {"expired", "invalid", "used"}:
                add_candidate(token.get("expiry_time"))

        if candidates:
            return max(candidates)
        return 0.0

    def _now_ts(self) -> float:
        if self.current_time is not None:
            return self._parse_time_like(self.current_time)
        return self._infer_current_time()

    def _default_current_time_text(self) -> str:
        if self.current_time is not None:
            return str(self.current_time)
        return datetime.utcfromtimestamp(self._now_ts()).isoformat() + "Z"

    def get_tenant_by_id(self, tenant_id: str) -> dict:
        """
        Retrieve information for a specific tenant by tenant_id.

        Args:
            tenant_id (str): The unique identifier of the tenant.

        Returns:
            dict: 
              Success: {
                "success": True,
                "data": TenantInfo
              }
              Failure: {
                "success": False,
                "error": "Tenant not found"
              }

        Constraints:
            - tenant_id must exist in the system.
        """
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            return { "success": False, "error": "Tenant not found" }
        return { "success": True, "data": tenant }

    def get_tenant_by_name(self, tenant_name: str) -> dict:
        """
        Retrieve tenant information for a given tenant_name.

        Args:
            tenant_name (str): The name of the tenant.

        Returns:
            dict: 
              - If found: { "success": True, "data": TenantInfo }
              - If not found: { "success": False, "error": "Tenant not found" }

        Constraints:
            - Searches for exact tenant_name match.
            - Returns only one result, if found.
        """
        for tenant in self.tenants.values():
            if tenant["tenant_name"] == tenant_name:
                return { "success": True, "data": tenant }
        return { "success": False, "error": "Tenant not found" }

    def list_all_tenants(self) -> dict:
        """
        List all registered tenants in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[TenantInfo]  # a list (possibly empty) of all tenant records
            }
        """
        tenants_list = list(self.tenants.values())
        return { "success": True, "data": tenants_list }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info by user _id (includes account status and tenant association).

        Args:
            user_id (str): The unique _id of the user.

        Returns:
            dict: 
              - On success:
                   { "success": True, "data": UserInfo }
              - If user not found:
                   { "success": False, "error": "User not found" }

        Constraints:
            - user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_username(self, tenant_id: str, username: str) -> dict:
        """
        Retrieve user info by username in the given tenant.

        Args:
            tenant_id (str): The tenant's unique identifier (scope for the search).
            username (str): The username to look for.

        Returns:
            dict:
                If found: {"success": True, "data": UserInfo}
                If tenant not found: {"success": False, "error": "Tenant not found"}
                If user not found for username+tenant: {"success": False, "error": "User not found for specified username and tenant"}
        Constraints:
            - The provided tenant_id must exist.
            - Only users belonging to the given tenant_id are searched.
            - Does not leak info about users in other tenants.
        """
        if tenant_id not in self.tenants:
            return {"success": False, "error": "Tenant not found"}

        for user in self.users.values():
            if user["tenant_id"] == tenant_id and user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found for specified username and tenant"}

    def get_users_by_tenant(self, tenant_id: str) -> dict:
        """
        List all users belonging to the specified tenant.

        Args:
            tenant_id (str): The unique identifier of the tenant.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[UserInfo]  # List of user info dicts for the tenant, could be empty.
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., "Tenant does not exist"
                    }

        Constraints:
            - tenant_id must refer to an existing tenant.
            - Returned users must only belong to the provided tenant (isolation).
        """
        if tenant_id not in self.tenants:
            return {"success": False, "error": "Tenant does not exist"}

        users_list = [
            user_info for user_info in self.users.values()
            if user_info["tenant_id"] == tenant_id
        ]

        return {"success": True, "data": users_list}

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Query the account_status of a specific user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "user_id": str,
                    "account_status": str
                }
            } if user exists
            or
            {
                "success": False,
                "error": str
            } if user is not found

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "account_status": user["account_status"]
            }
        }

    def get_token_by_value(self, token_value: str) -> dict:
        """
        Retrieve AuthTokenInfo for a given token_value.

        Args:
            token_value (str): The authentication token's unique value.

        Returns:
            dict: {
                "success": True,
                "data": AuthTokenInfo
            }
            or
            {
                "success": False,
                "error": "Token not found"
            }

        Constraints:
            - Token value must exist in the system.
        """
        token_info = self.auth_tokens.get(token_value)
        if not token_info:
            return { "success": False, "error": "Token not found" }
        return { "success": True, "data": token_info }

    def list_tokens_for_user(self, user_id: str, tenant_id: str) -> dict:
        """
        List all AuthTokens associated with a specific user and tenant.

        Args:
            user_id (str): The ID of the user whose tokens are to be listed.
            tenant_id (str): The ID of the tenant to which the user and tokens must belong.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[AuthTokenInfo]  # List of AuthTokenInfo dicts (possibly empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of the error
                    }

        Constraints:
            - The user must exist and belong to the provided tenant.
            - All returned tokens must be associated with both the user and tenant.
            - If user or tenant invalid, return error message.
        """
        # Check tenant exists
        if tenant_id not in self.tenants:
            return {"success": False, "error": "Tenant does not exist"}

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        if user["tenant_id"] != tenant_id:
            return {"success": False, "error": "User does not belong to specified tenant"}

        # Find all tokens matching user and tenant
        tokens = [
            token_info for token_info in self.auth_tokens.values()
            if token_info["user_id"] == user_id and token_info["tenant_id"] == tenant_id
        ]
        return {"success": True, "data": tokens}

    def check_token_validity(self, token_value: str, user_id: str, tenant_id: str) -> dict:
        """
        Verify if a given AuthToken is valid for the specified user and tenant.

        Args:
            token_value (str): The authentication/confirmation token value to be checked.
            user_id (str): The user ID that should own the token.
            tenant_id (str): The tenant ID under which the token and user should exist.

        Returns:
            dict:
                On query success:
                    {
                        "success": True,
                        "data": {
                            "is_valid": bool,
                            "reason": str
                        }
                    }
                If inputs are invalid or entities not found:
                    {
                        "success": False,
                        "error": str
                    }

        Validation logic:
            - AuthToken exists, references provided user and tenant.
            - Token status is "active" (not used/invalid/expired).
            - Token is not expired (expiry_time > current time).
            - User exists and belongs to provided tenant.
            - Tenant exists.
            - For token_type=="confirmation": user's account_status must be "pending_confirmation".
        """

        # Check if tenant exists
        if tenant_id not in self.tenants:
            return {"success": False, "error": "Tenant not found"}

        # Check if user exists and belongs to tenant
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        if user["tenant_id"] != tenant_id:
            return {"success": False, "error": "User does not belong to tenant"}

        # Check if token exists
        token = self.auth_tokens.get(token_value)
        if not token:
            return {"success": False, "error": "Token not found"}

        # Check if token is associated to the specified user and tenant
        if token["user_id"] != user_id or token["tenant_id"] != tenant_id:
            return {"success": True, "data": {"is_valid": False, "reason": "Token does not belong to provided user and tenant"}}

        # Check token_status (assuming "active" is valid)
        if token["token_status"] != "active":
            return {"success": True, "data": {"is_valid": False, "reason": f"Token status is not active: {token['token_status']}"}}

        # Check token expiry (convert to float, assume string or float as permitted)
        try:
            expiry_time = self._parse_time_like(token["expiry_time"])
            now = self._now_ts()
        except Exception:
            return {"success": False, "error": "Invalid expiry_time format in token"}

        if expiry_time <= now:
            return {"success": True, "data": {"is_valid": False, "reason": "Token has expired"}}

        # If confirmation token, check user's account status
        if token.get("token_type") in {"confirmation", "confirmation_token"}:
            if user.get("account_status") != "pending_confirmation":
                return {"success": True, "data": {"is_valid": False, "reason": "Confirmation token can only be used if user is pending confirmation"}}

        # All checks passed
        return {"success": True, "data": {"is_valid": True, "reason": "Token is valid"}}

    def check_user_token_association(
        self,
        token_value: str,
        user_id: str,
        tenant_id: str
    ) -> dict:
        """
        Check if a specified token is correctly associated with the given user and tenant.

        Args:
            token_value (str): The token value to validate.
            user_id (str): The user ID supposed to be associated with the token.
            tenant_id (str): The tenant ID supposed to be associated with both the token and user.

        Returns:
            dict: 
                - { "success": True, "data": True } if association is correct.
                - { "success": True, "data": False } if association is incorrect.
                - { "success": False, "error": <reason> } if token, user, or tenant do not exist.

        Constraints:
            - Token, user, and tenant must all exist.
            - Token.user_id must match user_id and token.tenant_id must match tenant_id.
            - User.tenant_id must match tenant_id as well.
        """
        # Check tenant existence
        if tenant_id not in self.tenants:
            return { "success": False, "error": "Tenant does not exist." }
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        # Check token existence
        if token_value not in self.auth_tokens:
            return { "success": False, "error": "Token does not exist." }
    
        token = self.auth_tokens[token_value]
        user = self.users[user_id]

        # Does token reference correct user and tenant, and does user belong to this tenant?
        is_associated = (
            token["user_id"] == user_id and
            token["tenant_id"] == tenant_id and
            user["tenant_id"] == tenant_id
        )

        return { "success": True, "data": is_associated }

    def set_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Update a user's account_status field.

        Args:
            user_id (str): The unique identifier of the user to update.
            new_status (str): The new account status to be set (e.g., 'active', 'pending_confirmation', etc.).

        Returns:
            dict:
                Success: { "success": True, "message": "User account_status updated." }
                Failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user with user_id must exist.
            - No additional constraints on account_status transitions are specified.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        user['account_status'] = new_status
        return { "success": True, "message": "User account_status updated." }

    def mark_token_as_used(self, token_value: str) -> dict:
        """
        Mark the specified authentication token as used (invalidating it).

        Args:
            token_value (str): The identifier of the token to be marked as used.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Token marked as used."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason for failure>"
                    }

        Constraints:
            - The token must exist in the system.
            - If the token is already used or invalid, the operation is idempotent (returns success with appropriate message).
        """
        token_info = self.auth_tokens.get(token_value)
        if not token_info:
            return { "success": False, "error": "Token not found." }
    
        if token_info["token_status"] in ("used", "invalid"):
            # Already used or invalidated, idempotent
            return { "success": True, "message": "Token was already marked as used or invalid." }
    
        # Mark the token as used
        token_info["token_status"] = "used"
        self.auth_tokens[token_value] = token_info
        return { "success": True, "message": "Token marked as used." }


    def create_user(self, tenant_id: str, email: str, username: str, account_status: Optional[str] = None) -> dict:
        """
        Add a new user to the system under the specified tenant.

        Args:
            tenant_id (str): The ID of the tenant to which the user is to be added.
            email (str): The user's email address (unique within tenant).
            username (str): The user's username (unique within tenant).
            account_status (Optional[str]): Optional initial account status 
                                            (default is "pending_confirmation").

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "User created with _id <id>",
                    "user_id": <id>
                }
                On failure:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - tenant_id must exist.
            - email and username must be unique within the tenant.
            - Each user is associated with exactly one tenant.
        """

        # Check if tenant exists
        if tenant_id not in self.tenants:
            return { "success": False, "error": "Tenant not found" }

        # Email and username must be unique within tenant
        for user in self.users.values():
            if user["tenant_id"] == tenant_id:
                if user["email"].lower() == email.lower():
                    return { "success": False, "error": "Email already exists for this tenant" }
                if user["username"].lower() == username.lower():
                    return { "success": False, "error": "Username already exists for this tenant" }

        # Assign new unique user ID
        new_user_id = str(uuid.uuid4())

        # Default account status
        if account_status is None:
            account_status = "pending_confirmation"

        registration_date = self._default_current_time_text()
        # Optional: last_login is None at creation
        user_info: Dict[str, Optional[str]] = {
            "_id": new_user_id,
            "tenant_id": tenant_id,
            "email": email,
            "username": username,
            "account_status": account_status,
            "registration_date": registration_date,
            "last_login": None,
        }
        self.users[new_user_id] = user_info

        return {
            "success": True,
            "message": f"User created with _id {new_user_id}",
            "user_id": new_user_id
        }


    def create_auth_token(
        self,
        user_id: str,
        tenant_id: str,
        token_type: str,
        expiry_time: str,
        creation_time: Optional[str] = None,
        token_value: Optional[str] = None,
        token_status: Optional[str] = "active"
    ) -> dict:
        """
        Generate a new AuthToken for a user within a specific tenant.

        Args:
            user_id (str): ID of the user receiving the token.
            tenant_id (str): Tenant context; must match the user's tenant.
            token_type (str): Purpose of the token (e.g., "confirmation").
            expiry_time (str): When the token expires (as string or float).
            creation_time (Optional[str]): Creation timestamp (default: now).
            token_value (Optional[str]): Force set a token value. If None, auto-generate.
            token_status (Optional[str]): Initial status, default is "active".

        Returns:
            dict: {
                "success": True,
                "message": "AuthToken created",
                "token_value": str,
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - user_id and tenant_id must exist and match.
            - token_value must be unique.
            - expiry_time must be after creation_time.
            - tenant isolation enforced.
        """
        # --- Check tenant existence ---
        if tenant_id not in self.tenants:
            return {"success": False, "error": "Tenant does not exist"}

        # --- Check user existence and tenant association ---
        user = self.users.get(user_id)
        if not user or user["tenant_id"] != tenant_id:
            return {"success": False, "error": "User does not exist or does not belong to tenant"}

        # --- Generate unique token_value if needed ---
        if token_value is None:
            while True:
                generated = str(uuid.uuid4())
                if generated not in self.auth_tokens:
                    token_value = generated
                    break
        else:
            if token_value in self.auth_tokens:
                return {"success": False, "error": "Token value already exists"}

        # --- Use current time if creation_time not specified ---
        if creation_time is None:
            creation_time = self._default_current_time_text()

        # --- Check expiry_time > creation_time ---
        try:
            ct = self._parse_time_like(creation_time)
            et = self._parse_time_like(expiry_time)
            if et <= ct:
                return {"success": False, "error": "Expiry time must be after creation time"}
        except Exception:
            return {"success": False, "error": "Invalid creation_time or expiry_time format"}

        # --- Build AuthTokenInfo ---
        token_info = {
            "token_value": token_value,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_type": token_type,
            "creation_time": creation_time,
            "expiry_time": expiry_time,
            "token_status": token_status or "active"
        }

        self.auth_tokens[token_value] = token_info

        return {
            "success": True,
            "message": "AuthToken created",
            "token_value": token_value
        }

    def invalidate_token(self, token_value: str) -> dict:
        """
        Mark an AuthToken as invalid before its expiry.

        Args:
            token_value (str): The value (identifier) of the token to invalidate.

        Returns:
            dict: 
                On success: { "success": True, "message": "Token <token_value> is now invalid." }
                On failure: { "success": False, "error": "Token does not exist." }

        Constraints:
            - The token must exist in the system.
            - If the token is already 'invalid' or 'used', operation is idempotent (no error, just indicate token is already invalid).
            - Sets 'token_status' to 'invalid'.
        """
        token = self.auth_tokens.get(token_value)
        if token is None:
            return { "success": False, "error": "Token does not exist." }

        if token["token_status"] in ("invalid", "used"):
            return { 
                "success": True, 
                "message": f"Token {token_value} was already {token['token_status']}."
            }

        token["token_status"] = "invalid"
        self.auth_tokens[token_value] = token
        return { "success": True, "message": f"Token {token_value} is now invalid." }

    def update_token_expiry(self, token_value: str, new_expiry_time: str) -> dict:
        """
        Change the expiry_time of an AuthToken.

        Args:
            token_value (str): The value of the token whose expiry time is to be updated.
            new_expiry_time (str): The new expiry time to set (can be string/float per environment).

        Returns:
            dict: {
                "success": True,
                "message": "Token expiry updated."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - The auth token with the provided value must exist.
            - (Optional: If token is already used or invalid, updating should not be allowed.)
        """
        if token_value not in self.auth_tokens:
            return {"success": False, "error": "Token not found."}

        token_info = self.auth_tokens[token_value]

        if token_info.get("token_status") in ("used", "invalid"):
            return {"success": False, "error": "Cannot update expiry of a used or invalid token."}

        token_info["expiry_time"] = new_expiry_time
        self.auth_tokens[token_value] = token_info

        return {"success": True, "message": "Token expiry updated."}

    def confirm_account_with_token(self, token_value: str) -> dict:
        """
        Atomically confirms a user account with the provided confirmation token:
          - Validates token and referenced user/tenant.
          - Ensures token is of type 'confirmation_token'
          - Ensures token is valid (not expired, not already used/invalid).
          - Ensures user status is 'pending_confirmation'.
          - Ensures user and token belong to the same tenant.
          - Sets user account_status to 'active'.
          - Sets token_status to 'used'.
      
        Args:
            token_value (str): The confirmation token value.
        
        Returns:
            dict: {
                "success": True,
                "message": "User account confirmed and token marked as used."
            }
            or {
                "success": False,
                "error": str
            }
        Constraints:
            - No cross-tenant operation; user and token must be in the same tenant.
            - Account status and token type/status validations enforced.
        """
        # Check token existence
        token = self.auth_tokens.get(token_value)
        if not token:
            return {"success": False, "error": "Token does not exist."}

        # Token must reference a valid user/tenant
        user_id = token.get("user_id")
        tenant_id = token.get("tenant_id")
        if not user_id or not tenant_id:
            return {"success": False, "error": "Invalid token: missing user or tenant reference."}

        user = self.users.get(user_id)
        tenant = self.tenants.get(tenant_id)

        if not user:
            return {"success": False, "error": "User does not exist."}
        if not tenant:
            return {"success": False, "error": "Tenant does not exist."}

        # Data isolation: user must belong to the tenant
        if user["tenant_id"] != tenant_id:
            return {"success": False, "error": "User does not belong to the referenced tenant."}

        # Token constraints
        # Confirmation tokens are only valid for users with account_status=pending_confirmation
        if token.get("token_type") not in {"confirmation", "confirmation_token"}:
            return {"success": False, "error": "Token is not a confirmation token."}

        # Check token_status is valid (not used/invalid)
        if token.get("token_status") not in {"active", "valid", "unused"}:
            return {"success": False, "error": f"Token is not valid (status: {token.get('token_status')})."}

        # Check expiry
        now = self._now_ts()
        try:
            expiry = self._parse_time_like(token.get("expiry_time"))
        except Exception:
            return {"success": False, "error": "Token expiry time invalid."}
        if now > expiry:
            return {"success": False, "error": "Token has expired."}

        # User must be pending confirmation
        if user.get("account_status") != "pending_confirmation":
            return {"success": False, "error": "User is not pending confirmation."}

        # All good: set user to active, token to used
        user["account_status"] = "active"
        token["token_status"] = "used"

        return {
            "success": True,
            "message": "User account confirmed and token marked as used."
        }

    def reset_user_password(self, token_value: str, new_password: str) -> dict:
        """
        Reset a user's password using a valid password reset token.

        Args:
            token_value (str): Password reset token.
            new_password (str): New plain password to set (in practice should be properly hashed/stored).

        Returns:
            dict: {
                "success": True,
                "message": "Password reset successful."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Token must exist and be of type "password_reset".
            - Token must not be expired or already used/invalid.
            - Token must reference a valid user and tenant.
            - After success, token is marked as used/inactive and password is updated.
        """

        token = self.auth_tokens.get(token_value)
        if not token:
            return {"success": False, "error": "Token not found"}

        # Validate token type
        if token.get("token_type") != "password_reset":
            return {"success": False, "error": "Invalid token type for password reset"}

        # Check token is active/valid status
        if token.get("token_status") not in ("active", "valid"):  # "active"/"valid" is assumed, adjust as needed
            return {"success": False, "error": "Token is already used or invalid"}

        # Check expiry
        try:
            expiry_time = self._parse_time_like(token["expiry_time"])
        except Exception:
            return {"success": False, "error": "Invalid token expiry time format"}
        current_time = self._now_ts()
        if current_time > expiry_time:
            return {"success": False, "error": "Token has expired"}

        # Validate user
        user_id = token.get("user_id")
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}

        # Tenant isolation
        if token.get("tenant_id") != user_info.get("tenant_id"):
            return {"success": False, "error": "Tenant mismatch"}

        # Optionally: check if user is allowed to reset password (e.g., not deactivated)
        # Here we assume any status except e.g. 'deactivated' is allowed
        if user_info.get("account_status") == "deactivated":
            return {"success": False, "error": "User account is deactivated and cannot reset password"}

        # --- Perform reset ---
        # For demonstration; in real world, passwords are hashed and salted!
        user_info["password"] = new_password
        # Mark token as used/invalid
        token["token_status"] = "used"
        self.auth_tokens[token_value] = token
        self.users[user_id] = user_info

        return {"success": True, "message": "Password reset successful."}

    def deactivate_user_account(self, user_id: str, new_status: str) -> dict:
        """
        Deactivate a user's account by setting their account_status to 'deactivated' or 'suspended'.

        Args:
            user_id (str): The unique user identifier.
            new_status (str): Either 'deactivated' or 'suspended'.

        Returns:
            dict: {
                "success": True,
                "message": "User {user_id} account_status set to {new_status}."
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must refer to an existing user.
            - new_status must be either 'deactivated' or 'suspended'.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if new_status not in ("deactivated", "suspended"):
            return {"success": False, "error": "Invalid status; must be 'deactivated' or 'suspended'"}

        self.users[user_id]["account_status"] = new_status
        return {
            "success": True,
            "message": f"User {user_id} account_status set to {new_status}."
        }

    def delete_user(self, user_id: str, invalidate_tokens: bool = True) -> dict:
        """
        Remove a user account identified by user_id.
        Optionally invalidates all tokens associated with this user.

        Args:
            user_id (str): The unique user ID to delete.
            invalidate_tokens (bool): If True, all tokens for this user will be invalidated (default: True).

        Returns:
            dict: {
                "success": True,
                "message": "User deleted (and tokens invalidated if specified)"
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., user does not exist)
            }

        Constraints:
            - User must exist.
            - If invalidate_tokens is True, all tokens for the user (by user_id) will have token_status set to "invalid".
            - All user data and affected tokens are scoped to the same tenant.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_info = self.users[user_id]
        tenant_id = user_info["tenant_id"]

        # Remove the user
        del self.users[user_id]

        # Optionally invalidate all tokens associated with this user
        if invalidate_tokens:
            for token in self.auth_tokens.values():
                if token["user_id"] == user_id and token["tenant_id"] == tenant_id:
                    if token["token_status"] not in ["invalid", "used"]:
                        token["token_status"] = "invalid"

        return {
            "success": True,
            "message": f"User '{user_id}' deleted{' and their tokens invalidated' if invalidate_tokens else ''}."
        }


class MultiTenantUserAuthenticationSystem(BaseEnv):
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

    def get_tenant_by_id(self, **kwargs):
        return self._call_inner_tool('get_tenant_by_id', kwargs)

    def get_tenant_by_name(self, **kwargs):
        return self._call_inner_tool('get_tenant_by_name', kwargs)

    def list_all_tenants(self, **kwargs):
        return self._call_inner_tool('list_all_tenants', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_users_by_tenant(self, **kwargs):
        return self._call_inner_tool('get_users_by_tenant', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def get_token_by_value(self, **kwargs):
        return self._call_inner_tool('get_token_by_value', kwargs)

    def list_tokens_for_user(self, **kwargs):
        return self._call_inner_tool('list_tokens_for_user', kwargs)

    def check_token_validity(self, **kwargs):
        return self._call_inner_tool('check_token_validity', kwargs)

    def check_user_token_association(self, **kwargs):
        return self._call_inner_tool('check_user_token_association', kwargs)

    def set_user_account_status(self, **kwargs):
        return self._call_inner_tool('set_user_account_status', kwargs)

    def mark_token_as_used(self, **kwargs):
        return self._call_inner_tool('mark_token_as_used', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def create_auth_token(self, **kwargs):
        return self._call_inner_tool('create_auth_token', kwargs)

    def invalidate_token(self, **kwargs):
        return self._call_inner_tool('invalidate_token', kwargs)

    def update_token_expiry(self, **kwargs):
        return self._call_inner_tool('update_token_expiry', kwargs)

    def confirm_account_with_token(self, **kwargs):
        return self._call_inner_tool('confirm_account_with_token', kwargs)

    def reset_user_password(self, **kwargs):
        return self._call_inner_tool('reset_user_password', kwargs)

    def deactivate_user_account(self, **kwargs):
        return self._call_inner_tool('deactivate_user_account', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)
