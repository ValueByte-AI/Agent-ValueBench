# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import time



# UserAccount: _id, phone_number, registration_status, verification_status, registration_timestamp, associated_devices
class UserAccountInfo(TypedDict):
    _id: str
    phone_number: str
    registration_status: str
    verification_status: str
    registration_timestamp: Union[str, float]
    associated_devices: List[str]

# Device: device_id, user_id, device_type, device_status, last_active_timestamp
class DeviceInfo(TypedDict):
    device_id: str
    user_id: str
    device_type: str
    device_status: str
    last_active_timestamp: Union[str, float]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Messaging platform user account management system.
        """

        # User accounts: {user_id (_id): UserAccountInfo}
        # Each phone number must be unique across accounts.
        self.user_accounts: Dict[str, UserAccountInfo] = {}

        # Devices: {device_id: DeviceInfo}
        self.devices: Dict[str, DeviceInfo] = {}

        # Constraints:
        # - Each phone number must be unique (one account per phone number)
        # - An account can only be used after successful verification
        # - A device must be associated with a verified and registered account
        # - Verification and registration statuses must be queryable per account

    def get_account_by_phone_number(self, phone_number: str) -> dict:
        """
        Retrieve full account info for a unique phone number.

        Args:
            phone_number (str): The phone number to look up.

        Returns:
            dict: 
              On success: { "success": True, "data": UserAccountInfo }
              On failure: { "success": False, "error": "Account with this phone number does not exist" }

        Constraints:
            - Each phone number is unique in the system.
        """
        # Linear search since user_accounts is keyed by user_id, not phone_number.
        for account in self.user_accounts.values():
            if account["phone_number"] == phone_number:
                return { "success": True, "data": account }
        return { "success": False, "error": "Account with this phone number does not exist" }

    def is_phone_number_registered(self, phone_number: str) -> dict:
        """
        Check if a phone number is registered in the system.

        Args:
            phone_number (str): The phone number to check (must be non-empty string).

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if phone number is registered, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., invalid input)
            }

        Constraints:
            - Phone number must be a non-empty string.
        """
        if not isinstance(phone_number, str) or not phone_number.strip():
            return {"success": False, "error": "Invalid phone number input"}

        for account_info in self.user_accounts.values():
            if account_info["phone_number"] == phone_number:
                return {"success": True, "data": True}
        return {"success": True, "data": False}

    def get_account_verification_status(
        self, 
        phone_number: str = None, 
        user_id: str = None
    ) -> dict:
        """
        Query the verification status of an account by phone number or user ID.
    
        Args:
            phone_number (str, optional): The phone number linked to the account.
            user_id (str, optional): The user account's unique ID (_id).
    
        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": {
                        "user_id": str,
                        "phone_number": str,
                        "verification_status": str
                    }
                }
              - On error: {
                    "success": False,
                    "error": str
                }
    
        Constraints:
            - At least one of phone_number or user_id must be provided.
            - Each phone number is unique (one account per phone number).
        """
        account = None

        if user_id:
            account = self.user_accounts.get(user_id)
            if not account:
                return {"success": False, "error": "Account not found for given user_id"}
        elif phone_number:
            for ua in self.user_accounts.values():
                if ua["phone_number"] == phone_number:
                    account = ua
                    break
            if not account:
                return {"success": False, "error": "Account not found for given phone number"}
        else:
            return {"success": False, "error": "Must provide phone_number or user_id"}

        return {
            "success": True,
            "data": {
                "user_id": account["_id"],
                "phone_number": account["phone_number"],
                "verification_status": account["verification_status"]
            }
        }

    def get_account_registration_status(self, phone_number: str = None, user_id: str = None) -> dict:
        """
        Query the registration status of an account by phone number or user_id.

        Args:
            phone_number (str, optional): The phone number of the user account.
            user_id (str, optional): The unique user_id (_id) of the user account.

        Returns:
            dict: 
              - On success: {"success": True, "registration_status": str}
              - On failure: {"success": False, "error": str}

        Constraints:
            - At least one identifier (phone_number or user_id) must be provided.
            - If both are provided and do not correspond to the same account, the first that resolves is used.
        """

        # Must provide at least one identifier
        if phone_number is None and user_id is None:
            return {"success": False, "error": "Must provide phone_number or user_id"}

        account = None

        if user_id:
            account = self.user_accounts.get(user_id)
        if account is None and phone_number:
            for acc in self.user_accounts.values():
                if acc["phone_number"] == phone_number:
                    account = acc
                    break

        if not account:
            return {"success": False, "error": "Account not found"}

        return {"success": True, "registration_status": account["registration_status"]}

    def list_all_accounts(self) -> dict:
        """
        Retrieve all user accounts currently in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserAccountInfo],  # List of all user accounts (may be empty if none exist)
            }

        Constraints:
            - No parameters or constraints. Returns all accounts.
        """
        accounts = list(self.user_accounts.values())
        return {"success": True, "data": accounts}

    def get_devices_for_account(self, user_id: str) -> dict:
        """
        List all device IDs associated with the given user account.

        Args:
            user_id (str): Account unique identifier (_id).

        Returns:
            dict:
              - success: True and data: List of device IDs if account exists (possibly empty).
              - success: False and error: error string if account does not exist.

        Constraints:
            - The specified account (_id) must exist in the system.
        """
        account = self.user_accounts.get(user_id)
        if not account:
            return {"success": False, "error": "User account not found"}

        # Will be a list (can be empty) of device_id strings
        return {"success": True, "data": list(account.get("associated_devices", []))}

    def get_device_info_by_device_id(self, device_id: str) -> dict:
        """
        Retrieve device information given a device ID.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            dict:
                - success: True and device info (DeviceInfo) if device exists.
                - success: False and error message if device does not exist.

        Constraints:
            - device_id must exist in the system.
        """
        device_info = self.devices.get(device_id)
        if not device_info:
            return { "success": False, "error": "Device not found" }
        return { "success": True, "data": device_info }

    def list_devices_for_phone_number(self, phone_number: str) -> dict:
        """
        Fetch all device info associated with a given phone number’s account.

        Args:
            phone_number (str): The phone number to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo]  # May be empty
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. account not found)
            }

        Constraints:
            - Each phone number must be unique (one account per phone number).
        """
        # Find user account by phone number
        user_account = None
        for account in self.user_accounts.values():
            if account["phone_number"] == phone_number:
                user_account = account
                break
        if not user_account:
            return { "success": False, "error": "Account with the provided phone number does not exist" }

        device_infos = []
        for device_id in user_account.get("associated_devices", []):
            device = self.devices.get(device_id)
            if device:
                device_infos.append(device)
        return { "success": True, "data": device_infos }

    def get_device_status(self, device_id: str) -> dict:
        """
        Query the current status (e.g., active/inactive) of a device by device_id.

        Args:
            device_id (str): The unique identifier for a device.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "device_id": str,
                            "device_status": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Device not found"
                    }

        Constraints:
            - The device_id must exist in the system's devices.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "device_status": device["device_status"]
            }
        }


    def register_account(self, phone_number: str) -> dict:
        """
        Register a new user account with the provided phone number, ensuring uniqueness.

        Args:
            phone_number (str): The phone number for the new account.

        Returns:
            dict:
                On Success:
                    { "success": True, "message": "Account registered", "account_id": <account_id> }
                On Failure (e.g., phone number already exists):
                    { "success": False, "error": "Phone number already registered" }

        Constraints:
            - Each phone number must be unique (one account per phone number).
        """
        # Enforce uniqueness of phone_number
        for account in self.user_accounts.values():
            if account["phone_number"] == phone_number:
                return { "success": False, "error": "Phone number already registered" }

        # Create a unique account ID (can use phone number or combination with timestamp for uniqueness)
        account_id = f"user_{phone_number}"

        # Prepare new user account info
        account_info: UserAccountInfo = {
            "_id": account_id,
            "phone_number": phone_number,
            "registration_status": "registered",
            "verification_status": "unverified",
            "registration_timestamp": time.time(),
            "associated_devices": [],
        }

        self.user_accounts[account_id] = account_info

        return { "success": True, "message": "Account registered", "account_id": account_id }

    def set_account_registration_status(self, phone_number: str, registration_status: str) -> dict:
        """
        Change the registration status of an existing account identified by phone number.

        Args:
            phone_number (str): The unique phone number of the user account.
            registration_status (str): The new registration status to be set (e.g., "pending", "registered", "suspended").

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Registration status updated for account with phone number X."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Account with the specified phone number does not exist."
                    }

        Constraints:
            - The account must exist (phone number is unique across accounts).
        """
        # Locate the account by phone number
        user_account_id = None
        for _id, acc in self.user_accounts.items():
            if acc["phone_number"] == phone_number:
                user_account_id = _id
                break

        if user_account_id is None:
            return {
                "success": False,
                "error": "Account with the specified phone number does not exist."
            }

        self.user_accounts[user_account_id]["registration_status"] = registration_status

        return {
            "success": True,
            "message": f"Registration status updated for account with phone number {phone_number}."
        }

    def set_account_verification_status(self, phone_number: str, verification_status: str) -> dict:
        """
        Change (set) the verification status of a user account identified by phone number.

        Args:
            phone_number (str): The unique phone number identifying the account.
            verification_status (str): New verification status to apply (e.g., 'unverified', 'verified', 'rejected').

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Account verification status updated." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Each phone number must correspond to a unique user account.
            - The account must exist.
            - No validation is performed on status value (for custom statuses).
        """
        found = None
        for user in self.user_accounts.values():
            if user["phone_number"] == phone_number:
                found = user
                break

        if not found:
            return { "success": False, "error": "Account with specified phone number does not exist." }

        found["verification_status"] = verification_status
        return { "success": True, "message": "Account verification status updated." }

    def associate_device_with_account(self, user_id: str, device_info: DeviceInfo) -> dict:
        """
        Add a new device to a user's account.

        Args:
            user_id (str): The user account's unique identifier (_id).
            device_info (DeviceInfo): The new device information to be associated with this account.

        Returns:
            dict: Success or error message:
                {
                    "success": True,
                    "message": "Device associated with account."
                }
                OR
                {
                    "success": False,
                    "error": "Reason for failure..."
                }

        Constraints:
            - user_id must exist in user_accounts.
            - The user account must be both registered and verified.
            - device_id must not already exist in self.devices.
        """
        # Validate user existence
        user = self.user_accounts.get(user_id)
        if user is None:
            return { "success": False, "error": "User account does not exist." }

        # Check account registration and verification
        if user.get("registration_status") != "registered":
            return { "success": False, "error": "Account is not registered." }
        if user.get("verification_status") != "verified":
            return { "success": False, "error": "Account is not verified." }

        # Extract device_id and ensure it's unique
        device_id = device_info.get("device_id")
        if device_id is None or not isinstance(device_id, str) or device_id == "":
            return { "success": False, "error": "Invalid device_id." }
        if device_id in self.devices:
            return { "success": False, "error": "A device with this device_id already exists." }

        # Double-check device is not already associated
        if device_id in user["associated_devices"]:
            return { "success": False, "error": "Device already associated with this account." }

        # Force user_id in the device info to match the target user
        device_info = dict(device_info)  # Make a shallow copy
        device_info["user_id"] = user_id

        # Register device
        self.devices[device_id] = device_info
        user["associated_devices"].append(device_id)

        return { "success": True, "message": "Device associated with account." }

    def dissociate_device_from_account(self, device_id: str) -> dict:
        """
        Remove (dissociate) a device from its associated user account in the messaging platform system.

        Args:
            device_id (str): The unique identifier of the device to be dissociated.

        Returns:
            dict: 
                On success: { "success": True, "message": "Device <device_id> dissociated from account <user_id>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Device must exist.
            - Device must be associated with a user account (device's user_id is non-empty and account exists).
            - Updates both device and user account records.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }

        user_id = device.get("user_id")
        if not user_id:
            return { "success": False, "error": "Device is not associated with any account" }

        account = self.user_accounts.get(user_id)
        if not account:
            # Inconsistent state: device refers to non-existent account
            return { "success": False, "error": f"Associated user account {user_id} not found" }

        # Remove device from the user's associated_devices, if present
        if device_id in account["associated_devices"]:
            account["associated_devices"].remove(device_id)
        # else: falls through if device_id was not in associated_devices -- possible data inconsistency

        # Dissociate device. Once a flagged device is detached from an account,
        # it should no longer remain active in the platform state.
        device["user_id"] = ""
        device["device_status"] = "inactive"
    
        return {
            "success": True,
            "message": f"Device {device_id} dissociated from account {user_id}"
        }

    def update_device_status(self, device_id: str, new_status: str) -> dict:
        """
        Change the status of a device (e.g., lost/active/inactive) by device_id.

        Args:
            device_id (str): The ID of the device to update.
            new_status (str): The new status to set for the device.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Device <device_id> status updated to <new_status>." }
                - On failure: { "success": False, "error": <description> }
    
        Constraints:
            - The device must exist.
            - The device must be associated with a registered and verified account.
        """
        device = self.devices.get(device_id)
        if device is None:
            return { "success": False, "error": "Device not found." }

        user_id = device.get("user_id")
        user = self.user_accounts.get(user_id)
        if (
            user is None or
            user.get("registration_status") != "registered" or
            user.get("verification_status") != "verified"
        ):
            # Allow the cleanup path where a device has already been
            # dissociated and is being explicitly marked inactive.
            if user_id == "" and new_status == "inactive":
                device["device_status"] = new_status
                return {
                    "success": True,
                    "message": f"Device {device_id} status updated to {new_status}."
                }
            return { "success": False, "error": "Device association invalid." }

        # Update the status
        device["device_status"] = new_status

        # Optionally update last_active_timestamp if status is set to 'active'
        # Not mandated by spec; omitted for now.

        return {
            "success": True,
            "message": f"Device {device_id} status updated to {new_status}."
        }

    def delete_account_by_phone_number(self, phone_number: str) -> dict:
        """
        Permanently removes a user account given its phone number, including
        cascading delete on all devices associated with that account.

        Args:
            phone_number (str): The phone number of the account to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Account (and associated devices if any) deleted for phone number ..."
            }
            or
            {
                "success": False,
                "error": "Account with this phone number does not exist"
            }

        Constraints:
            - Each phone number is unique; only one account should match.
            - All devices associated with the deleted account are also deleted (cascade).
        """
        # Find the user account by phone number
        user_id_to_delete = None
        for user_id, account in self.user_accounts.items():
            if account["phone_number"] == phone_number:
                user_id_to_delete = user_id
                break

        if not user_id_to_delete:
            return {
                "success": False,
                "error": "Account with this phone number does not exist"
            }
    
        # Identify devices to delete (cascade)
        device_ids_to_delete = [
            device_id
            for device_id, device in self.devices.items()
            if device["user_id"] == user_id_to_delete
        ]
        for device_id in device_ids_to_delete:
            del self.devices[device_id]
    
        # Delete the user account
        del self.user_accounts[user_id_to_delete]

        return {
            "success": True,
            "message": f"Account and {len(device_ids_to_delete)} associated device(s) deleted for phone number {phone_number}."
        }


class MessagingPlatformAccountSystem(BaseEnv):
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

    def get_account_by_phone_number(self, **kwargs):
        return self._call_inner_tool('get_account_by_phone_number', kwargs)

    def is_phone_number_registered(self, **kwargs):
        return self._call_inner_tool('is_phone_number_registered', kwargs)

    def get_account_verification_status(self, **kwargs):
        return self._call_inner_tool('get_account_verification_status', kwargs)

    def get_account_registration_status(self, **kwargs):
        return self._call_inner_tool('get_account_registration_status', kwargs)

    def list_all_accounts(self, **kwargs):
        return self._call_inner_tool('list_all_accounts', kwargs)

    def get_devices_for_account(self, **kwargs):
        return self._call_inner_tool('get_devices_for_account', kwargs)

    def get_device_info_by_device_id(self, **kwargs):
        return self._call_inner_tool('get_device_info_by_device_id', kwargs)

    def list_devices_for_phone_number(self, **kwargs):
        return self._call_inner_tool('list_devices_for_phone_number', kwargs)

    def get_device_status(self, **kwargs):
        return self._call_inner_tool('get_device_status', kwargs)

    def register_account(self, **kwargs):
        return self._call_inner_tool('register_account', kwargs)

    def set_account_registration_status(self, **kwargs):
        return self._call_inner_tool('set_account_registration_status', kwargs)

    def set_account_verification_status(self, **kwargs):
        return self._call_inner_tool('set_account_verification_status', kwargs)

    def associate_device_with_account(self, **kwargs):
        return self._call_inner_tool('associate_device_with_account', kwargs)

    def dissociate_device_from_account(self, **kwargs):
        return self._call_inner_tool('dissociate_device_from_account', kwargs)

    def update_device_status(self, **kwargs):
        return self._call_inner_tool('update_device_status', kwargs)

    def delete_account_by_phone_number(self, **kwargs):
        return self._call_inner_tool('delete_account_by_phone_number', kwargs)
