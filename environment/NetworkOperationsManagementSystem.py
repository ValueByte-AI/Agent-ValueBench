# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any



class DeviceInfo(TypedDict):
    device_id: str
    name: str
    type: str    # Should correspond to an entry in DeviceTypeInfo.type_id
    status: str  # e.g., "online", "offline", "unknown"
    location: str
    performance_metrics: Dict[str, float]  # Mapping of metric name to value
    last_checked_tim: float  # Timestamp (e.g., UNIX time)

class DeviceTypeInfo(TypedDict):
    type_id: str
    type_name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Network Operations Management System stateful environment.
        """

        # Devices: {device_id: DeviceInfo}
        # Represents managed systems or network devices and their status/metrics.
        self.devices: Dict[str, DeviceInfo] = {}

        # Device Types: {type_id: DeviceTypeInfo}
        # Standardized categories/types for devices.
        self.device_types: Dict[str, DeviceTypeInfo] = {}

        # Constraints:
        # - Each device must have a unique device_id.
        # - Device status must be regularly updated for accurate reporting.
        # - Each device must be associated with a valid DeviceType (type_id).
        # - Performance metrics may have freshness/expiration requirements.
        self._logical_time = None

    def _infer_controlled_now(self) -> float:
        timestamps = []
        for device in self.devices.values():
            last_checked = device.get("last_checked_tim")
            if isinstance(last_checked, (int, float)):
                timestamps.append(float(last_checked))
        return max(timestamps) if timestamps else 0.0

    def _set_logical_time(self, explicit_time: float) -> float:
        self._logical_time = float(explicit_time)
        return self._logical_time

    def _remember_timestamp(self, observed_time: float) -> None:
        observed = float(observed_time)
        if self._logical_time is None or observed > self._logical_time:
            self._logical_time = observed

    def _get_controlled_now(self, explicit_time: float = None) -> float:
        if explicit_time is not None:
            return self._set_logical_time(explicit_time)
        if self._logical_time is not None:
            return float(self._logical_time)
        return self._infer_controlled_now()

    def get_device_by_id(self, device_id: str) -> dict:
        """
        Retrieve detailed information about a specific device using its device_id.

        Args:
            device_id (str): The unique identifier of the device to query.

        Returns:
            dict:
                - If found:
                    { "success": True, "data": DeviceInfo }
                - If not found:
                    { "success": False, "error": "Device not found" }

        Constraints:
            - device_id must exist in self.devices.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device not found" }
        return { "success": True, "data": self.devices[device_id] }

    def get_device_status(self, device_id: str) -> dict:
        """
        Retrieve the current operational status of a device (online/offline/unknown/etc).
    
        Args:
            device_id (str): The unique identifier of the device.
    
        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": { "device_id": str, "status": str }
                }
              - On error: {
                    "success": False,
                    "error": "Device not found"
                }
        Constraints:
            - The device_id must exist in the system devices registry.
        """
        device = self.devices.get(device_id)
        if device is None:
            return { "success": False, "error": "Device not found" }
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "status": device["status"]
            }
        }

    def list_devices_by_type(self, type_id: str) -> dict:
        """
        Retrieve a list of all devices matching a specific type ID.

        Args:
            type_id (str): The unique identifier for the device type (should match DeviceTypeInfo.type_id).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[DeviceInfo]   # All devices with device['type'] == type_id.
                }
            or
                {
                    "success": False,
                    "error": str  # Description of error; e.g. type_id does not exist.
                }

        Constraints:
            - type_id must exist in self.device_types.
            - Returns all devices whose 'type' field matches given type_id.
        """
        if type_id not in self.device_types:
            return {"success": False, "error": "Device type not found"}

        result = [device for device in self.devices.values() if device["type"] == type_id]
        return {"success": True, "data": result}

    def list_all_devices(self) -> dict:
        """
        Retrieve a full list of all managed devices.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo]  # List of all devices (may be empty if none managed)
            }

        Constraints:
            - No constraints; this operation returns all registered devices.
        """
        return { "success": True, "data": list(self.devices.values()) }

    def get_device_performance_metrics(self, device_id: str, max_age_seconds: float = None, current_time: float = None) -> dict:
        """
        Retrieve the performance metrics of a given device, optionally checking for freshness.

        Args:
            device_id (str): Unique ID of the device whose metrics to retrieve.
            max_age_seconds (float, optional): If set, require that the metrics are at most this many seconds old.
            current_time (float, optional): Current UNIX timestamp (used for age calculation; if not given, no age check will be performed).

        Returns:
            dict:  
                - On success: { "success": True, "data": <performance_metrics dict> }
                - On device not found: { "success": False, "error": "Device not found" }
                - On stale data (if max_age_seconds specified): { "success": False, "error": "Metrics data is too old" }
        Constraints:
            - Device must exist.
            - If max_age_seconds is given, last_checked_tim must not be older than max_age_seconds.
        """
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}

        if current_time is not None:
            self._set_logical_time(current_time)

        if max_age_seconds is not None:
            if current_time is None:
                return {"success": False, "error": "Current time required for freshness check"}
            age = current_time - device["last_checked_tim"]
            if age > max_age_seconds:
                return {"success": False, "error": "Metrics data is too old"}

        return {"success": True, "data": device["performance_metrics"]}

    def list_all_device_types(self) -> dict:
        """
        Retrieve all standardized device categories/types (DeviceTypeInfo) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceTypeInfo],  # May be empty if no types present
            }
        """
        device_type_list = list(self.device_types.values())
        return {
            "success": True,
            "data": device_type_list
        }

    def get_device_type_details(self, type_id: str) -> dict:
        """
        Retrieve the details/description of a specific device type.

        Args:
            type_id (str): Identifier for the device type.

        Returns:
            dict: {
                "success": True,
                "data": DeviceTypeInfo,  # On success, the matching DeviceType information.
            }
            or
            {
                "success": False,
                "error": str  # If device type not found.
            }

        Constraints:
            - type_id must exist in self.device_types.
        """
        if type_id not in self.device_types:
            return { "success": False, "error": "Device type not found" }
        return { "success": True, "data": self.device_types[type_id] }


    def check_performance_metrics_freshness(self, device_id: str, freshness_threshold_sec: float) -> dict:
        """
        Check whether a device’s performance metrics are up to date (within a freshness threshold).

        Args:
            device_id (str): Unique identifier of the device to check.
            freshness_threshold_sec (float): Maximum allowable staleness (in seconds) for metrics to be considered fresh.

        Returns:
            dict:
                {
                  "success": True,
                  "data": {
                      "fresh": bool,  # True if metrics are fresh, else False
                      "last_checked_tim": float,  # Timestamp of the last metrics check
                      "current_time": float,  # Controlled current time used in calculation
                      "age_seconds": float,  # How old the metrics are (seconds)
                  }
                }
                OR
                { "success": False, "error": "<reason>" }

        Constraints:
            - Device must exist (device_id present in self.devices).
            - freshness_threshold_sec should be non-negative (else, always reports as not fresh).
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device not found" }

        device_info = self.devices[device_id]
        last_checked = device_info.get("last_checked_tim", 0.0)
        now = self._get_controlled_now()
        age = now - last_checked

        if freshness_threshold_sec < 0:
            return { "success": False, "error": "Invalid freshness threshold (must be non-negative)" }

        fresh = age <= freshness_threshold_sec

        return {
            "success": True,
            "data": {
                "fresh": fresh,
                "last_checked_tim": last_checked,
                "current_time": now,
                "age_seconds": age
            }
        }

    def validate_device_type_association(self, device_id: str) -> dict:
        """
        Verify that the specified device's 'type' references a valid DeviceType.

        Args:
            device_id (str): The ID of the device to validate.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "device_id": str,
                    "type": str,
                    "type_valid": bool,
                    "type_name": Optional[str],  # Name of type if valid
                }
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Device must exist in self.devices.
            - Device's 'type' must match an entry in self.device_types[type_id].
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": f"Device with device_id '{device_id}' does not exist" }

        device_type_id = device.get("type")
        if not device_type_id:
            return { "success": False, "error": f"Device with device_id '{device_id}' does not have a 'type' set" }

        device_type = self.device_types.get(device_type_id)
        if not device_type:
            return {
                "success": True,
                "data": {
                    "device_id": device_id,
                    "type": device_type_id,
                    "type_valid": False,
                    "type_name": None,
                }
            }

        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "type": device_type_id,
                "type_valid": True,
                "type_name": device_type.get("type_name"),
            }
        }

    def add_device(
        self, 
        device_id: str, 
        name: str, 
        type: str, 
        status: str, 
        location: str, 
        performance_metrics: Dict[str, float], 
        last_checked_tim: float
    ) -> dict:
        """
        Add a new device into the environment inventory.

        Args:
            device_id (str): Unique identifier for the device.
            name (str): Device name.
            type (str): type_id corresponding to a valid DeviceType.
            status (str): Device operational status (e.g., online, offline).
            location (str): Device location descriptor.
            performance_metrics (Dict[str, float]): Metrics such as CPU, memory, etc.
            last_checked_tim (float): Timestamp of last health/status check.

        Returns:
            dict: 
                { "success": True, "message": "Device added successfully." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - device_id must be unique.
            - type must be a valid type_id in self.device_types.
        """
        if device_id in self.devices:
            return { "success": False, "error": "Device with this device_id already exists." }
        if type not in self.device_types:
            return { "success": False, "error": "Invalid device type (type_id does not exist)." }

        device_info: DeviceInfo = {
            "device_id": device_id,
            "name": name,
            "type": type,
            "status": status,
            "location": location,
            "performance_metrics": performance_metrics,
            "last_checked_tim": last_checked_tim
        }
        self.devices[device_id] = device_info

        return { "success": True, "message": "Device added successfully." }


    def update_device_status(self, device_id: str, status: str) -> dict:
        """
        Update the operational status of a specified device and refresh its last_checked_tim.

        Args:
            device_id (str): Unique identifier of the device to update.
            status (str): New operational status (e.g., "online", "offline", "unknown").

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Device status updated for <device_id>."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Device must exist in self.devices.
            - Updates the 'status' and 'last_checked_tim' fields.
        """
        if device_id not in self.devices:
            return {"success": False, "error": "Device not found"}

        self.devices[device_id]["status"] = status
        self.devices[device_id]["last_checked_tim"] = self._get_controlled_now()
        return {"success": True, "message": f"Device status updated for {device_id}."}

    def update_device_performance_metrics(
        self, 
        device_id: str, 
        performance_metrics: Dict[str, float], 
        last_checked_tim: float
    ) -> dict:
        """
        Update the performance metrics and last_checked_tim for the specified device.

        Args:
            device_id (str): Unique identifier for the device to update.
            performance_metrics (Dict[str, float]): Dictionary of metric name to value.
            last_checked_tim (float): UNIX timestamp indicating when metrics were last checked.

        Returns:
            dict: 
                If successful:
                    {"success": True, "message": "Performance metrics updated for device <device_id>."}
                If error:
                    {"success": False, "error": "Device not found"} 

        Constraints:
            - The device with device_id must exist in the system.
            - Updates both 'performance_metrics' and 'last_checked_tim'.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device not found" }
    
        self.devices[device_id]["performance_metrics"] = performance_metrics
        self.devices[device_id]["last_checked_tim"] = last_checked_tim
        self._remember_timestamp(last_checked_tim)

        return {
            "success": True,
            "message": f"Performance metrics updated for device {device_id}."
        }

    def remove_device(self, device_id: str) -> dict:
        """
        Remove a device from the system by device_id.

        Args:
            device_id (str): Unique identifier of the device to be removed.

        Returns:
            dict:
                Success: { "success": True, "message": "Device <id> removed from the system." }
                Failure: { "success": False, "error": "Device not found." }

        Constraints:
            - The device must already exist in the system (self.devices).
            - The device will be deleted from the state if found.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device not found." }

        del self.devices[device_id]
        return { "success": True, "message": f"Device {device_id} removed from the system." }

    def add_device_type(self, type_id: str, type_name: str, description: str) -> dict:
        """
        Add a new DeviceType to the system.

        Args:
            type_id (str): Unique identifier for the device type/category.
            type_name (str): Readable name of the device type.
            description (str): Description of the device type.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Device type '<type_id>' added."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - type_id must be unique in the system.
        """
        if type_id in self.device_types:
            return {"success": False, "error": f"Device type '{type_id}' already exists."}

        self.device_types[type_id] = {
            "type_id": type_id,
            "type_name": type_name,
            "description": description
        }
        return {"success": True, "message": f"Device type '{type_id}' added."}

    def update_device_type(self, device_id: str, new_type_id: str) -> dict:
        """
        Change the type of an existing device, after validation.

        Args:
            device_id (str): Unique identifier of the device to modify.
            new_type_id (str): DeviceType (type_id) to assign to the device.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Device type updated successfully"
                }
                or
                {
                    "success": False,
                    "error": "Reason for failure"
                }

        Constraints:
            - device_id must exist.
            - new_type_id must refer to an existing DeviceType.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device ID does not exist" }
        if new_type_id not in self.device_types:
            return { "success": False, "error": "Device type does not exist" }

        self.devices[device_id]['type'] = new_type_id

        return { "success": True, "message": "Device type updated successfully" }

    def reconcile_device_types(self) -> dict:
        """
        Scan all devices and fix or flag devices that do not have a valid type association.

        Returns:
            dict: {
                "success": True,
                "flagged_devices": List[str],  # device_ids with invalid type association (not auto-fixed)
                "fixed_devices": List[dict],   # Each dict: {"device_id": str, "old_type": str, "new_type": str} for fixed devices
                "message": str                 # Human-readable summary
            }

        Constraints:
            - Each device's 'type' must match a type_id in self.device_types.
            - Devices with invalid type associations are flagged.
            - Devices whose type can be fixed (e.g., set to a fallback type) are fixed and recorded.
            - No exception is raised.
        """

        flagged_devices = []
        fixed_devices = []

        # Use a fallback type if one exists ("unknown" by convention) when fixing devices.
        fallback_type_id = None
        for tid, tinfo in self.device_types.items():
            if tinfo["type_name"].lower() == "unknown":
                fallback_type_id = tid
                break

        for device_id, device in self.devices.items():
            if device["type"] not in self.device_types:
                if fallback_type_id:
                    # Auto-fix: set to fallback, track fix
                    old_type = device["type"]
                    self.devices[device_id]["type"] = fallback_type_id
                    fixed_devices.append({
                        "device_id": device_id,
                        "old_type": old_type,
                        "new_type": fallback_type_id
                    })
                else:
                    flagged_devices.append(device_id)

        message = (
            f"Reconciliation complete. "
            f"Flagged {len(flagged_devices)} devices with invalid type associations. "
            f"Fixed {len(fixed_devices)} devices to fallback type." if fallback_type_id else
            f"Reconciliation complete. Flagged {len(flagged_devices)} devices with invalid type associations and no fallback available."
        )
        return {
            "success": True,
            "flagged_devices": flagged_devices,
            "fixed_devices": fixed_devices,
            "message": message
        }


class NetworkOperationsManagementSystem(BaseEnv):
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

    def get_device_by_id(self, **kwargs):
        return self._call_inner_tool('get_device_by_id', kwargs)

    def get_device_status(self, **kwargs):
        return self._call_inner_tool('get_device_status', kwargs)

    def list_devices_by_type(self, **kwargs):
        return self._call_inner_tool('list_devices_by_type', kwargs)

    def list_all_devices(self, **kwargs):
        return self._call_inner_tool('list_all_devices', kwargs)

    def get_device_performance_metrics(self, **kwargs):
        return self._call_inner_tool('get_device_performance_metrics', kwargs)

    def list_all_device_types(self, **kwargs):
        return self._call_inner_tool('list_all_device_types', kwargs)

    def get_device_type_details(self, **kwargs):
        return self._call_inner_tool('get_device_type_details', kwargs)

    def check_performance_metrics_freshness(self, **kwargs):
        return self._call_inner_tool('check_performance_metrics_freshness', kwargs)

    def validate_device_type_association(self, **kwargs):
        return self._call_inner_tool('validate_device_type_association', kwargs)

    def add_device(self, **kwargs):
        return self._call_inner_tool('add_device', kwargs)

    def update_device_status(self, **kwargs):
        return self._call_inner_tool('update_device_status', kwargs)

    def update_device_performance_metrics(self, **kwargs):
        return self._call_inner_tool('update_device_performance_metrics', kwargs)

    def remove_device(self, **kwargs):
        return self._call_inner_tool('remove_device', kwargs)

    def add_device_type(self, **kwargs):
        return self._call_inner_tool('add_device_type', kwargs)

    def update_device_type(self, **kwargs):
        return self._call_inner_tool('update_device_type', kwargs)

    def reconcile_device_types(self, **kwargs):
        return self._call_inner_tool('reconcile_device_types', kwargs)
