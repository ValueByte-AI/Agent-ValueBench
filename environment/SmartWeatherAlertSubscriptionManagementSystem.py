# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class UserInfo(TypedDict):
    _id: str
    name: str
    contact_info: str

class DeviceInfo(TypedDict):
    device_id: str
    device_type: str
    user_id: str
    device_sta: str  # device status

class WeatherAlertSubscriptionInfo(TypedDict):
    subscription_id: str
    user_id: str
    device_id: str
    alert_types: List[str]
    parameters: Dict[str, str]  # customizable alert parameters
    sta: str  # subscription status

class WeatherAlertTypeInfo(TypedDict):
    alert_type_id: str
    name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Devices: {device_id: DeviceInfo}
        self.devices: Dict[str, DeviceInfo] = {}

        # Subscriptions: {subscription_id: WeatherAlertSubscriptionInfo}
        self.subscriptions: Dict[str, WeatherAlertSubscriptionInfo] = {}

        # Alert types: {alert_type_id: WeatherAlertTypeInfo}
        self.alert_types: Dict[str, WeatherAlertTypeInfo] = {}

        # Constraints:
        # - Each subscription must be associated with a valid user and device.
        # - A user may have multiple active subscriptions, but not duplicate subscriptions for the same alert type and device.
        # - Only devices with active status receive weather alert deliveries.
        # - Subscription parameters must match supported alert types and devices.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user(s) information by their name.

        Args:
            name (str): The user's name to search for (case-sensitive exact match).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo],  # List of user info dicts matching the name.
                }
                or
                {
                    "success": False,
                    "error": str,  # Reason for failure (e.g., not found, invalid name)
                }

        Constraints:
            - Name must be a non-empty string.
            - May return multiple users if names are duplicated; empty list is not a success.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Invalid name"}

        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        if not matches:
            return {"success": False, "error": "No user found with the specified name"}

        return {"success": True, "data": matches}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information using the user's unique ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": UserInfo,  # user information dictionary
                  }
                - On failure: {
                      "success": False,
                      "error": "User not found"
                  }
        Constraints:
            - The user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_user_devices(self, user_id: str) -> dict:
        """
        List all devices associated with a specific user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo]  # List of devices associated with the user (can be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user not found
            }
    
        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_devices = [
            device_info for device_info in self.devices.values()
            if device_info["user_id"] == user_id
        ]

        return {"success": True, "data": user_devices}

    def get_device_by_id(self, device_id: str) -> dict:
        """
        Retrieve all information about a specific device by device_id.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            dict:
                - If device exists:
                    { "success": True, "data": DeviceInfo }
                - If not:
                    { "success": False, "error": "Device not found" }
        """
        device = self.devices.get(device_id)
        if device is None:
            return { "success": False, "error": "Device not found" }
        return { "success": True, "data": device }

    def check_device_status(self, device_id: str) -> dict:
        """
        Check whether the given device is active and eligible for alert delivery.

        Args:
            device_id (str): The unique identifier for the device to be checked.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "device_id": str,
                            "device_sta": str,
                            "eligible": bool  # True if device_sta == "active"
                        }
                    }
                - On error:
                    {
                        "success": False,
                        "error": "Device not found"
                    }

        Constraints:
            - Only devices with device_sta == 'active' are eligible for alert delivery.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }

        eligible = device["device_sta"] == "active"
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "device_sta": device["device_sta"],
                "eligible": eligible
            }
        }

    def get_alert_types(self) -> dict:
        """
        Return all available weather alert types in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[WeatherAlertTypeInfo]  # May be empty if no types configured
            }

        Constraints:
            - No constraints are enforced (information query).
            - If no alert types are present, data will be an empty list.
        """
        data = list(self.alert_types.values())
        return { "success": True, "data": data }

    def get_alert_type_info(self, alert_type_id: str) -> dict:
        """
        Retrieve details of a specific weather alert type given its ID.

        Args:
            alert_type_id (str): The unique identifier of the weather alert type.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": WeatherAlertTypeInfo
                }
                On error,
                {
                    "success": False,
                    "error": "Alert type not found"
                }

        Constraints:
            - The alert_type_id must exist in the alert_types mapping.
        """
        alert_type_info = self.alert_types.get(alert_type_id)
        if not alert_type_info:
            return {"success": False, "error": "Alert type not found"}
        return {"success": True, "data": alert_type_info}

    def list_user_subscriptions(self, user_id: str) -> dict:
        """
        List all weather alert subscriptions for a specific user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                - success: True and data (list of WeatherAlertSubscriptionInfo) if user is found
                - success: False and error message if user does not exist

        Constraints:
            - User must exist in self.users.
            - Returns all subscriptions associated with the user (regardless of status).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        subs = [
            sub for sub in self.subscriptions.values()
            if sub["user_id"] == user_id
        ]

        return {"success": True, "data": subs}

    def get_subscription_by_id(self, subscription_id: str) -> dict:
        """
        Retrieve the full details for a specific weather alert subscription.

        Args:
            subscription_id (str): The unique identifier for the subscription.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": WeatherAlertSubscriptionInfo  # complete subscription details
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g. "Subscription not found"
                    }

        Constraints:
            - The subscription_id must exist in the system.
        """
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            return { "success": False, "error": "Subscription not found" }
        return { "success": True, "data": subscription }

    def check_duplicate_subscription(self, user_id: str, device_id: str, alert_types: List[str]) -> dict:
        """
        Determines whether a duplicate weather alert subscription exists for the given user,
        device, and alert type(s). Returns True if a duplicate is found, False otherwise.

        Args:
            user_id (str): The user's unique identifier.
            device_id (str): The device's unique identifier.
            alert_types (List[str]): List of weather alert type IDs (strings) to check for duplication.

        Returns:
            dict:
                Success: { "success": True, "data": bool }
                    True if a duplicate exists, False otherwise.
                Failure: { "success": False, "error": str }
                    Describes why the check could not be completed (e.g., unknown user/device/alert_type).
        Constraints:
            - The user and device must both exist.
            - At least one valid alert type must be provided.
            - Duplicate means: user, device, and any alert_type in alert_types already exist as a subscription.
        """

        if user_id not in self.users:
            return { "success": False, "error": f"User '{user_id}' does not exist." }
        if device_id not in self.devices:
            return { "success": False, "error": f"Device '{device_id}' does not exist." }
        if not alert_types or not isinstance(alert_types, list):
            return { "success": False, "error": "No alert_types provided." }
        for at in alert_types:
            if at not in self.alert_types:
                return { "success": False, "error": f"Alert type '{at}' does not exist." }

        # Check for duplicate subscriptions
        for sub in self.subscriptions.values():
            if sub["user_id"] == user_id and sub["device_id"] == device_id:
                if any(at in sub["alert_types"] for at in alert_types):
                    return { "success": True, "data": True }

        return { "success": True, "data": False }

    def create_weather_alert_subscription(
        self,
        user_id: str,
        device_id: str,
        alert_types: list,
        parameters: dict
    ) -> dict:
        """
        Create a new weather alert subscription for a user on a specified device for given alert types.

        Args:
            user_id (str): The user's unique id.
            device_id (str): Device id to deliver alerts.
            alert_types (List[str]): List of alert type ids to subscribe to.
            parameters (Dict[str, str]): Custom parameters for this subscription.

        Returns:
            dict: 
                - On success:
                    { "success": True, "message": "Subscription created successfully", "subscription_id": <id> }
                - On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - User and device must exist, and device must belong to the user.
            - Device must be "active".
            - All given alert types must exist.
            - No duplicate active subscriptions for the same user, device, and alert type.
            - Subscription parameters must be compatible (not enforced unless system has parameter schema).
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Check device existence
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }
        if device['user_id'] != user_id:
            return { "success": False, "error": "Device is not associated with the user" }
        if device['device_sta'] != 'active':
            return { "success": False, "error": "Device is not active" }

        # Alert types existence
        missing_types = [tid for tid in alert_types if tid not in self.alert_types]
        if missing_types:
            return {
                "success": False,
                "error": f"Alert type(s) not found: {', '.join(missing_types)}"
            }

        if not alert_types:
            return { "success": False, "error": "At least one alert type must be specified" }

        # Check for duplicate subscriptions (user, device, alert_type ALL matching)
        for sub in self.subscriptions.values():
            if sub["user_id"] == user_id and sub["device_id"] == device_id and sub["sta"] == "active":
                # Does any alert_type overlap?
                if set(sub["alert_types"]) & set(alert_types):
                    return {
                        "success": False,
                        "error": "Duplicate active subscription exists for at least one requested alert type on this device"
                    }

        # Generate new unique subscription_id (simple increment for demo, in prod use uuid)
        idx = 1
        while True:
            new_id = f"sub_{idx}"
            if new_id not in self.subscriptions:
                break
            idx += 1

        # Create subscription record
        subscription_data = {
            "subscription_id": new_id,
            "user_id": user_id,
            "device_id": device_id,
            "alert_types": list(alert_types),
            "parameters": dict(parameters),
            "sta": "active"
        }
        self.subscriptions[new_id] = subscription_data

        return {
            "success": True,
            "message": "Subscription created successfully",
            "subscription_id": new_id
        }

    def update_subscription_parameters(self, subscription_id: str, parameters: Dict[str, str]) -> dict:
        """
        Modify customization parameters of an existing weather alert subscription.

        Args:
            subscription_id (str): The ID of the subscription to update.
            parameters (Dict[str, str]): The new parameters to set (must comply with alert types for this subscription).

        Returns:
            dict:
                On success: {"success": True, "message": "Subscription parameters updated."}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - The subscription must exist and be active.
            - The parameters must match supported alert types and devices.
        """
        if subscription_id not in self.subscriptions:
            return {"success": False, "error": "Subscription does not exist."}

        subscription = self.subscriptions[subscription_id]
        if subscription.get("sta", "").lower() != "active":
            return {"success": False, "error": "Only active subscriptions can be updated."}

        # Simple validation: parameters must be dict, and not empty (or you may want to allow empty).
        if not isinstance(parameters, dict):
            return {"success": False, "error": "Parameters must be a dictionary."}
    
        # Check parameters are appropriate for this subscription's alert types. We lack schema, so just check keys are strings.
        # If there was an alert type to parameter-name mapping, would check here.

        for k, v in parameters.items():
            if not isinstance(k, str) or not isinstance(v, str):
                return {"success": False, "error": "Parameter keys and values must be strings."}

        # Optional: Check for unsupported parameters (if a list for the alert_type existed; skip if not specified)

        # Update parameters
        subscription['parameters'] = parameters
        # Consider updating a timestamp here if one existed.

        return {"success": True, "message": "Subscription parameters updated."}

    def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Mark an existing weather alert subscription as cancelled/inactive.

        Args:
            subscription_id (str): The unique identifier of the subscription to cancel.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation or info if already cancelled
            }
            or
            {
                "success": False,
                "error": str  # If subscription_id does not exist
            }

        Constraints:
            - The subscription must exist in the system.
            - Marks 'sta' field of the subscription as "cancelled".
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found."}

        if subscription.get("sta") == "cancelled":
            return {"success": True, "message": "Subscription already cancelled."}

        subscription["sta"] = "cancelled"
        return {"success": True, "message": "Subscription cancelled."}

    def activate_device(self, device_id: str) -> dict:
        """
        Change the status of a device to 'active' (e.g., after repair/reactivation).

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            dict: {
                "success": True,
                "message": "Device activated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason the update could not be performed
            }

        Constraints:
            - Device must exist in the system.
            - Setting device_sta to 'active' is idempotent; operation always succeeds if device exists.
        """
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}

        device["device_sta"] = "active"
        return {"success": True, "message": "Device activated successfully"}

    def deactivate_device(self, device_id: str) -> dict:
        """
        Change the status of a device to inactive (e.g., lost or broken).

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            dict: {
                "success": True,
                "message": "Device <device_id> deactivated."
            }
            or
            {
                "success": False,
                "error": "Device does not exist."
            }

        Constraints:
            - The device must exist in the system.
            - If already inactive, operation still succeeds.
        """
        device = self.devices.get(device_id)
        if device is None:
            return { "success": False, "error": "Device does not exist." }

        if device["device_sta"] == "inactive":
            return {
                "success": True,
                "message": f"Device {device_id} is already inactive."
            }

        device["device_sta"] = "inactive"
        self.devices[device_id] = device
        return {
            "success": True,
            "message": f"Device {device_id} deactivated."
        }

    def delete_weather_alert_subscription(self, subscription_id: str) -> dict:
        """
        Permanently remove a weather alert subscription from the system.
        (Admin-level operation)

        Args:
            subscription_id (str): The unique identifier of the subscription to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Subscription deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Subscription not found."
            }
    
        Constraints:
            - The subscription must exist in the system.
            - This is an admin-level operation; no user validation is performed.
        """
        if subscription_id not in self.subscriptions:
            return {"success": False, "error": "Subscription not found."}

        del self.subscriptions[subscription_id]
        return {"success": True, "message": "Subscription deleted successfully."}


class SmartWeatherAlertSubscriptionManagementSystem(BaseEnv):
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

    def list_user_devices(self, **kwargs):
        return self._call_inner_tool('list_user_devices', kwargs)

    def get_device_by_id(self, **kwargs):
        return self._call_inner_tool('get_device_by_id', kwargs)

    def check_device_status(self, **kwargs):
        return self._call_inner_tool('check_device_status', kwargs)

    def get_alert_types(self, **kwargs):
        return self._call_inner_tool('get_alert_types', kwargs)

    def get_alert_type_info(self, **kwargs):
        return self._call_inner_tool('get_alert_type_info', kwargs)

    def list_user_subscriptions(self, **kwargs):
        return self._call_inner_tool('list_user_subscriptions', kwargs)

    def get_subscription_by_id(self, **kwargs):
        return self._call_inner_tool('get_subscription_by_id', kwargs)

    def check_duplicate_subscription(self, **kwargs):
        return self._call_inner_tool('check_duplicate_subscription', kwargs)

    def create_weather_alert_subscription(self, **kwargs):
        return self._call_inner_tool('create_weather_alert_subscription', kwargs)

    def update_subscription_parameters(self, **kwargs):
        return self._call_inner_tool('update_subscription_parameters', kwargs)

    def cancel_subscription(self, **kwargs):
        return self._call_inner_tool('cancel_subscription', kwargs)

    def activate_device(self, **kwargs):
        return self._call_inner_tool('activate_device', kwargs)

    def deactivate_device(self, **kwargs):
        return self._call_inner_tool('deactivate_device', kwargs)

    def delete_weather_alert_subscription(self, **kwargs):
        return self._call_inner_tool('delete_weather_alert_subscription', kwargs)

