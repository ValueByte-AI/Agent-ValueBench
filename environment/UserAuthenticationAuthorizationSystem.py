# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict, Any
import uuid
from typing import Optional, Dict



class UserInfo(TypedDict):
    _id: str
    username: str
    hashed_password: str
    phone_number: str
    email: str
    account_status: str
    mfa_enabled: bool

class OTPInfo(TypedDict):
    otp_id: str
    user_id: str
    code: str
    template_name: str
    contact_method: str
    expiration_time: float
    is_used: bool

class SecurityTemplateInfo(TypedDict):
    template_name: str
    template_content: str
    expiry_duration: float
    delivery_method: str

class LoginEventInfo(TypedDict):
    event_id: str
    user_id: str
    timestamp: float
    event_type: str
    successful: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        User Authentication and Authorization System environment.

        Constraints:
        - OTPs must be unique per user and expire after a set duration.
        - OTPs should not be reused; is_used flag is set after verification.
        - Only verified contact methods (e.g., phone_number) may be used for OTP delivery.
        - Users may only request a certain number of OTPs within a set timeframe (rate limiting).
        - The SecurityTemplate used must exist and be active.
        """
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # OTPs: {otp_id: OTPInfo}
        self.otps: Dict[str, OTPInfo] = {}

        # SecurityTemplates: {template_name: SecurityTemplateInfo}
        self.security_templates: Dict[str, SecurityTemplateInfo] = {}

        # LoginEvents: {event_id: LoginEventInfo}
        self.login_events: Dict[str, LoginEventInfo] = {}

        self.current_time: float = 1700000000.0

    def _now(self) -> float:
        try:
            return float(self.current_time)
        except Exception:
            return 1700000000.0

    def get_user_by_phone(self, phone_number: str) -> dict:
        """
        Retrieve user information by phone number.

        Args:
            phone_number (str): The phone number associated with the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Details of the found user
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found
            }

        Constraints:
            - Only returns one user (if multiple found, returns the first match).
        """
        for user in self.users.values():
            if user.get("phone_number") == phone_number:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information given a username.

        Args:
            username (str): Username to search for.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": UserInfo  # All user info for found user
                }
                On failure: {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - Returns info for the first user with exact username match.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details by unique user ID.

        Args:
            user_id (str): The unique identifier (_id) of the user.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": UserInfo}
                - If not found:
                    {"success": False, "error": "User not found"}
        Constraints:
            - The user ID must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def list_verified_contact_methods(self, user_id: str) -> dict:
        """
        List all verified contact methods (phone_number, email) for a given user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                { "success": True, "data": { "phone_number": str|None, "email": str|None } }
                or
                { "success": False, "error": "User not found" }
        Constraints:
            - Only returns contact methods set (non-empty). No verification flags in schema;
              so treats non-empty entries as 'verified'.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
    
        contact_methods = {}
        if user.get("phone_number"):
            contact_methods["phone_number"] = user["phone_number"]
        if user.get("email"):
            contact_methods["email"] = user["email"]

        return { "success": True, "data": contact_methods }

    def get_security_template(self, template_name: str) -> dict:
        """
        Retrieve information for a specific SecurityTemplate by its template name.
    
        Args:
            template_name (str): The name of the SecurityTemplate to retrieve.
    
        Returns:
            dict:
                Success: { "success": True, "data": SecurityTemplateInfo }
                Failure: { "success": False, "error": "Security template not found" }
    
        Constraints:
            - The template_name must exist in the system's security_templates.
        """
        template = self.security_templates.get(template_name)
        if template is None:
            return { "success": False, "error": "Security template not found" }
        return { "success": True, "data": template }

    def list_active_security_templates(self) -> dict:
        """
        List all active SecurityTemplates available in the system.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[SecurityTemplateInfo]  # All security templates (may be empty list)
                }

        Notes:
            - "Active" status is not stored; all templates in self.security_templates are considered active by design.
            - Returns an empty list if no templates exist.
        """
        data = list(self.security_templates.values())
        return {"success": True, "data": data}

    def list_user_otps(self, user_id: str) -> dict:
        """
        Retrieve all OTPs associated with the given user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[OTPInfo],   # All OTPs for this user (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # "User not found"
            }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        otps = [
            otp_info for otp_info in self.otps.values()
            if otp_info["user_id"] == user_id
        ]
        return { "success": True, "data": otps }

    def get_otp_by_id(self, otp_id: str) -> dict:
        """
        Retrieve the details of a specific OTP by its ID.

        Args:
            otp_id (str): The unique identifier of the OTP to fetch.

        Returns:
            dict: {
                "success": True,
                "data": OTPInfo  # OTP details if found,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "OTP not found"
            }

        Constraints:
            - The otp_id must exist in the OTP records.
        """
        otp = self.otps.get(otp_id)
        if not otp:
            return {"success": False, "error": "OTP not found"}

        return {"success": True, "data": otp}


    def list_user_active_otps(self, user_id: str) -> dict:
        """
        Retrieve all unexpired and unused OTPs for the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[OTPInfo]  # Active OTPs for the user (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., user does not exist
                    }

        Constraints:
            - Only OTPs where (expiration_time > now and is_used == False) should be listed.
            - user_id must refer to a valid user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        now = self._now()
        active_otps = [
            otp for otp in self.otps.values()
            if otp["user_id"] == user_id and not otp["is_used"] and otp["expiration_time"] > now
        ]
        return { "success": True, "data": active_otps }

    def count_user_otp_requests_in_timeframe(self, user_id: str, start_time: float, end_time: float) -> dict:
        """
        Count the number of OTPs generated by a user within a specified time window.
        The count is used for rate limiting OTP requests.

        Args:
            user_id (str): The target user's ID.
            start_time (float): The start of the time window (inclusive), as a Unix timestamp.
            end_time (float): The end of the time window (inclusive), as a Unix timestamp.

        Returns:
            dict: {
                "success": True,
                "data": int  # Number of OTPs matching the criteria
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - user_id must exist
            - Only OTPs with computed creation_time in [start_time, end_time] are counted.
        """
        # Validate user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if start_time > end_time:
            return { "success": False, "error": "Invalid time window: start_time > end_time" }

        count = 0
        for otp in self.otps.values():
            if otp["user_id"] != user_id:
                continue
            # Lookup expiry_duration from its SecurityTemplate
            template_name = otp.get("template_name")
            template = self.security_templates.get(template_name)
            if not template:
                continue  # Ignore OTPs with missing templates (should not happen per constraints)
            expiry_duration = template.get("expiry_duration", 0.0)
            # Deduce creation_time
            creation_time = otp.get("expiration_time", 0.0) - expiry_duration
            if start_time <= creation_time <= end_time:
                count += 1

        return { "success": True, "data": count }

    def list_login_events_for_user(self, user_id: str) -> dict:
        """
        Retrieve all login and OTP usage events for the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[LoginEventInfo]  # all event dicts for the user; empty if none found
                }
                or
                {
                    "success": False,
                    "error": str  # e.g. "User does not exist"
                }

        Constraints:
            - user_id must exist in the users dictionary.
            - No filtering for event type; returns all LoginEvent types for the user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        result = [
            event_info
            for event_info in self.login_events.values()
            if event_info["user_id"] == user_id
        ]
        return {"success": True, "data": result}

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Query the account status (e.g., 'active', 'suspended') for the user with the provided user_id.

        Args:
            user_id (str): The unique identifier of the user (_id field).

        Returns:
            dict:
                - If user exists:
                    {"success": True, "data": {"user_id": str, "account_status": str}}
                - If user not found:
                    {"success": False, "error": "User not found"}

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "account_status": user["account_status"]
            }
        }


    def generate_otp(self, user_id: str, template_name: str, contact_method: str) -> dict:
        """
        Create and store a new OTP for a user with a provided SecurityTemplate and contact method.

        Args:
            user_id (str): The ID of the user for whom to generate the OTP.
            template_name (str): The name of the SecurityTemplate to use.
            contact_method (str): Either the verified contact field name
                ('phone_number' or 'email') or the concrete verified phone/email
                value to use for OTP delivery.

        Returns:
            dict: {
                "success": True,
                "message": "OTP generated",
                "otp_id": str,   # The generated OTP's unique identifier
                "code": str      # The actual OTP code
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist;
            - contact_method must resolve to one of the user's verified contact methods;
            - template_name must exist;
            - OTP must be unique per user;
            - is_used is set to False and expiration_time is enforced per template.
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        matched_field = None
        resolved_contact_method = contact_method
        if contact_method in ("phone_number", "email"):
            resolved_contact_method = user.get(contact_method)
            matched_field = contact_method if resolved_contact_method else None
        elif user.get("phone_number") == contact_method:
            matched_field = "phone_number"
        elif user.get("email") == contact_method:
            matched_field = "email"
        if matched_field is None:
            return {"success": False, "error": "Contact method is not verified for user"}

        verified_flag = f"{matched_field}_verified"
        if verified_flag in user and not user.get(verified_flag, False):
            return {"success": False, "error": "Contact method is not verified for user"}

        # Check provided SecurityTemplate exists
        template = self.security_templates.get(template_name)
        if not template:
            return {"success": False, "error": "SecurityTemplate does not exist"}

        # Generate a code (6-digit number as example; in reality, could follow template formatting)
        code = f"{uuid.uuid4().int % 1000000:06d}"

        # Generate unique OTP id
        otp_id = str(uuid.uuid4())

        # Set expiration based on template expiry_duration (seconds from now)
        current_now = self._now()
        expiration_time = current_now + float(template.get("expiry_duration", 300))  # default 5m if missing

        # Enforce uniqueness: no duplicate OTP code for this user currently unexpired (not strictly necessary for code, but could check)
        for otp in self.otps.values():
            if (
                otp["user_id"] == user_id and
                otp["code"] == code and
                not otp["is_used"] and
                otp["expiration_time"] > current_now
            ):
                # Regenerate code, once (in practice, repeat until unique); keep simple for MVP
                code = f"{uuid.uuid4().int % 1000000:06d}"

        # Store the OTP
        otp_info = {
            "otp_id": otp_id,
            "user_id": user_id,
            "code": code,
            "template_name": template_name,
            "contact_method": resolved_contact_method,
            "expiration_time": expiration_time,
            "is_used": False
        }
        self.otps[otp_id] = otp_info

        return {
            "success": True,
            "message": "OTP generated",
            "otp_id": otp_id,
            "code": code
        }

    def mark_otp_as_used(self, otp_id: str) -> dict:
        """
        Mark the OTP specified by otp_id as used (sets is_used = True).

        Args:
            otp_id (str): The unique identifier for the OTP.

        Returns:
            dict: {
                "success": True,
                "message": "OTP marked as used."
            }
            or
            {
                "success": False,
                "error": "OTP not found." or "OTP is already marked as used."
            }

        Constraints:
            - OTP must exist in the system.
            - OTP must not already be marked as used.
        """
        otp = self.otps.get(otp_id)
        if otp is None:
            return { "success": False, "error": "OTP not found." }
        if otp.get("is_used", False):
            return { "success": False, "error": "OTP is already marked as used." }
    
        otp["is_used"] = True
        # No return or update for database/persistence layer needed, as dicts are mutable.
        return { "success": True, "message": "OTP marked as used." }

    def expire_otp(self, otp_id: str) -> dict:
        """
        Force-expire an OTP by setting its expiration_time to the past, regardless of current value.

        Args:
            otp_id (str): The unique identifier of the OTP to expire.

        Returns:
            dict: 
                { "success": True, "message": "OTP <otp_id> has been force-expired." }
                or
                { "success": False, "error": "OTP not found." }

        Constraints/Notes:
            - If the OTP is already expired or is_used is True, the operation is still treated as success ("idempotent").
            - Does not delete the OTP, just force-expires it.
        """

        otp = self.otps.get(otp_id)
        if otp is None:
            return { "success": False, "error": "OTP not found." }

        # Set the expiration_time to now minus a small epsilon (force in the past)
        otp["expiration_time"] = self._now() - 1

        # Optionally set is_used to True for maximum revocation (commented; can be enabled if desired)
        # otp["is_used"] = True

        return { "success": True, "message": f"OTP {otp_id} has been force-expired." }

    def log_login_event(
        self,
        event_id: str,
        user_id: str,
        timestamp: float,
        event_type: str,
        successful: bool
    ) -> dict:
        """
        Add a new LoginEvent (login or OTP use) to the system.

        Args:
            event_id (str): Unique identifier for the login event.
            user_id (str): User ID associated with this event (must exist).
            timestamp (float): Unix epoch timestamp for event.
            event_type (str): Nature of event (e.g., 'login', 'otp_use').
            successful (bool): Whether the event was successful.

        Returns:
            dict: {
                "success": True,
                "message": "Login event logged"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - event_id must be unique.
            - user_id must exist in users.
        """
        # Validate event_id uniqueness
        if event_id in self.login_events:
            return {"success": False, "error": "Event ID already exists."}

        # Validate user existence
        if user_id not in self.users:
            return {"success": False, "error": "User ID does not exist."}

        # Basic validation for required fields
        if event_type is None or timestamp is None:
            return {"success": False, "error": "Missing required login event parameters."}

        # Assemble the login event
        login_event: LoginEventInfo = {
            "event_id": event_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "successful": successful,
        }
        self.login_events[event_id] = login_event

        return {"success": True, "message": "Login event logged"}

    def enable_user_mfa(self, user_id: str) -> dict:
        """
        Enable multi-factor authentication (MFA) for a given user.

        Args:
            user_id (str): The unique identifier (_id) for the user.

        Returns:
            dict: 
                { "success": True, "message": "MFA enabled for user <user_id>" }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - User must exist.
            - Should not enable MFA for users with non-active status.
            - If MFA is already enabled, returns success message (idempotent).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        if user["account_status"].lower() != "active":
            return { "success": False, "error": f"User account status is not active: {user['account_status']}" }

        if user.get("mfa_enabled") is True:
            return { "success": True, "message": f"MFA already enabled for user {user_id}" }

        user["mfa_enabled"] = True
        # Optionally, persist this change if writable to self.users

        return { "success": True, "message": f"MFA enabled for user {user_id}" }

    def disable_user_mfa(self, user_id: str) -> dict:
        """
        Disable multi-factor authentication (MFA) for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "message": "MFA disabled for user <user_id or username>"
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. user not found
            }

        Constraints:
            - The user must exist in the system.
            - Operation is idempotent (no error if already disabled).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        if user["mfa_enabled"]:
            user["mfa_enabled"] = False
            self.users[user_id] = user  # update to reflect change if necessary
            return {
                "success": True, 
                "message": f'MFA disabled for user {user.get("username", user_id)}'
            }
        else:
            return {
                "success": True, 
                "message": f'MFA was already disabled for user {user.get("username", user_id)}'
            }

    def update_user_contact_method(
        self,
        user_id: str,
        contact_method: str,
        value: str = None,
        verified: bool = None
    ) -> dict:
        """
        Update or verify a user's contact method (phone_number or email).

        Args:
            user_id (str): ID of the user to be updated.
            contact_method (str): Which contact method ('phone_number' or 'email').
            value (str, optional): New value for the contact method.
            verified (bool, optional): If provided, will set the "<contact_method>_verified" flag.

        Returns:
            dict: {
                "success": True,
                "message": "Contact method updated/verifed successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist.
            - Contact method must be one of: 'phone_number', 'email'.
            - If setting verified status, contact method value must be present.
        """
        # Check for user existence
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        if contact_method not in ["phone_number", "email"]:
            return {"success": False, "error": "Invalid contact method."}

        user = self.users[user_id]

        # Update value if provided
        if value is not None:
            user[contact_method] = value

        # Add verified flag if not present
        verified_flag = f"{contact_method}_verified"
        if verified_flag not in user:
            user[verified_flag] = False

        # Set verified status if specified
        if verified is not None:
            if not user.get(contact_method):
                return {
                    "success": False,
                    "error": f"Cannot set verified status: {contact_method} value is not set."
                }
            user[verified_flag] = verified

        self.users[user_id] = user
        msg = f"{contact_method} updated"
        if verified is not None:
            msg += f" and {'verified' if verified else 'unverified'}"
        msg += " successfully."
        return {"success": True, "message": msg}

    def revoke_otp(self, otp_id: str, current_time: float) -> dict:
        """
        Invalidate (revoke) an unexpired, unused OTP before its normal expiration.

        Args:
            otp_id (str): The OTP's unique identifier to revoke.
            current_time (float): The current Unix timestamp (used for expiration check).

        Returns:
            dict: {
                "success": True,
                "message": "OTP revoked."
            }
            OR
            {
                "success": False,
                "error": reason
            }

        Constraints:
            - OTP must exist.
            - OTP must not be expired (expiration_time > current_time).
            - OTP must not be already used.
        """
        otp = self.otps.get(otp_id)
        if not otp:
            return { "success": False, "error": "OTP does not exist." }

        if otp["is_used"]:
            return { "success": False, "error": "OTP has already been used." }

        if otp["expiration_time"] <= current_time:
            return { "success": False, "error": "OTP has already expired." }

        # Revoke: mark as used (so audit/history is preserved)
        otp["is_used"] = True
        self.otps[otp_id] = otp
        return { "success": True, "message": "OTP revoked." }


class UserAuthenticationAuthorizationSystem(BaseEnv):
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

    def get_user_by_phone(self, **kwargs):
        return self._call_inner_tool('get_user_by_phone', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_verified_contact_methods(self, **kwargs):
        return self._call_inner_tool('list_verified_contact_methods', kwargs)

    def get_security_template(self, **kwargs):
        return self._call_inner_tool('get_security_template', kwargs)

    def list_active_security_templates(self, **kwargs):
        return self._call_inner_tool('list_active_security_templates', kwargs)

    def list_user_otps(self, **kwargs):
        return self._call_inner_tool('list_user_otps', kwargs)

    def get_otp_by_id(self, **kwargs):
        return self._call_inner_tool('get_otp_by_id', kwargs)

    def list_user_active_otps(self, **kwargs):
        return self._call_inner_tool('list_user_active_otps', kwargs)

    def count_user_otp_requests_in_timeframe(self, **kwargs):
        return self._call_inner_tool('count_user_otp_requests_in_timeframe', kwargs)

    def list_login_events_for_user(self, **kwargs):
        return self._call_inner_tool('list_login_events_for_user', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def generate_otp(self, **kwargs):
        return self._call_inner_tool('generate_otp', kwargs)

    def mark_otp_as_used(self, **kwargs):
        return self._call_inner_tool('mark_otp_as_used', kwargs)

    def expire_otp(self, **kwargs):
        return self._call_inner_tool('expire_otp', kwargs)

    def log_login_event(self, **kwargs):
        return self._call_inner_tool('log_login_event', kwargs)

    def enable_user_mfa(self, **kwargs):
        return self._call_inner_tool('enable_user_mfa', kwargs)

    def disable_user_mfa(self, **kwargs):
        return self._call_inner_tool('disable_user_mfa', kwargs)

    def update_user_contact_method(self, **kwargs):
        return self._call_inner_tool('update_user_contact_method', kwargs)

    def revoke_otp(self, **kwargs):
        return self._call_inner_tool('revoke_otp', kwargs)
