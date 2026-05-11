# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
import time
from datetime import datetime



class SecuritySystemInfo(TypedDict):
    system_id: str
    mode: str  # e.g., 'armed'/'disarmed'
    alert_settings: dict  # Detailed alert settings, type unknown
    last_updated: str
    location: str

class DeviceInfo(TypedDict):
    device_id: str
    type: str  # e.g., 'alarm', 'sensor', 'camera'
    status: str  # e.g., 'active', 'inactive'
    operational_state: str
    location: str

class UserInfo(TypedDict):
    user_id: str
    privileges: List[str]
    preferences: dict
    last_login: str

class EventInfo(TypedDict):
    event_id: str
    timestamp: str
    event_type: str
    affected_device_id: str
    resolved_state: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Smart Home Security System stateful environment.
        """

        # SecuritySystems: {system_id: SecuritySystemInfo}
        self.security_systems: Dict[str, SecuritySystemInfo] = {}

        # Devices: {device_id: DeviceInfo}
        self.devices: Dict[str, DeviceInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Events: list of security events, for log/history
        self.events: List[EventInfo] = []

        # Constraints:
        # - Only authorized users may change system mode (arm/disarm).
        # - Devices must be operable to affect system state changes.
        # - System maintains log/history of all state changes and events.
        # - Alert settings determine thresholds for device/event triggers.

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve user information (privileges, preferences, last login) by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
              - If successful: {
                    "success": True,
                    "data": UserInfo
                }
              - If user not found: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def check_user_privileges(self, user_id: str) -> dict:
        """
        Determine the specific system control privileges of a user.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # The list of privilege strings (empty list possible)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., user not found
            }

        Constraints:
            - No authorization required (query only).
            - Returns all privileges associated with the user_id.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user_info.get("privileges", [])}

    def get_security_system_status(self, system_id: str) -> dict:
        """
        Fetch the current mode (armed/disarmed) and alert settings of the given home security system.

        Args:
            system_id (str): The unique identifier for the security system.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "mode": str,            # 'armed' or 'disarmed'
                            "alert_settings": dict  # Alert settings data
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., system not found)
                    }
        Constraints:
            - The specified system_id must exist.
        """
        system = self.security_systems.get(system_id)
        if not system:
            return {"success": False, "error": "Security system does not exist"}

        result = {
            "mode": system["mode"],
            "alert_settings": system["alert_settings"]
        }
        return {"success": True, "data": result}

    def get_devices_by_type(self, device_type: str) -> dict:
        """
        List all devices of a specified type (e.g., all alarms or all sensors) including their
        status and operational state.

        Args:
            device_type (str): The type of device to filter by ('alarm', 'sensor', 'camera', etc.)

        Returns:
            dict:
                - success (bool): Operation was successful.
                - data (List[DeviceInfo]): List of devices matching the given type (may be empty).
                - error (str, optional): Reason for failure if unsuccessful.

        Constraints:
            - device_type must be a non-empty string.
        """
        if not device_type or not isinstance(device_type, str):
            return {"success": False, "error": "Invalid or missing device_type parameter"}

        devices = [
            device_info
            for device_info in self.devices.values()
            if device_info["type"] == device_type
        ]

        return {"success": True, "data": devices}

    def get_device_status(self, device_id: str) -> dict:
        """
        Obtain detailed status and operational state for a specific device.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            dict: {
                "success": True,
                "data": DeviceInfo,   # Device metadata including status and operational state
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Device not found"
            }

        Constraints:
            - The device must exist in the system.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }

        return { "success": True, "data": device }

    def get_event_log(self) -> dict:
        """
        Retrieve the complete log/history of security events and state changes.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],  # List of all event log entries (possibly empty)
            }

        Constraints:
            - No filters, all events in system are returned.
            - Event log must be maintained for all state changes.
            - No permissions required to view event log.
        """
        return {
            "success": True,
            "data": list(self.events)  # Return a copy of the event log list.
        }

    def get_alert_settings(self, system_id: str) -> dict:
        """
        Query the current alert settings/thresholds configured in the specified security system.

        Args:
            system_id (str): The identifier for the security system to query.

        Returns:
            dict: {
                "success": True,
                "data": dict  # The alert_settings dictionary for this system
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., 'Security system not found')
            }

        Constraints:
            - The specified security system must exist.
        """
        system_info = self.security_systems.get(system_id)
        if not system_info:
            return {"success": False, "error": "Security system not found"}
        alert_settings = system_info.get("alert_settings")
        if alert_settings is None:
            return {"success": False, "error": "Alert settings not configured for this system"}
        return {"success": True, "data": alert_settings}

    @staticmethod
    def _alarm_is_ready_for_arming(device: dict) -> bool:
        if device.get("status") != "active":
            return False

        state = str(device.get("operational_state", "")).strip().lower()
        blocked_states = {
            "",
            "disabled",
            "error",
            "fault",
            "inactive",
            "maintenance",
            "malfunction",
            "network_degraded",
            "offline",
            "pending_maintenance",
            "testing",
            "triggered",
        }
        return state not in blocked_states

    def set_security_system_mode(self, system_id: str, user_id: str, new_mode: str) -> dict:
        """
        Change the mode (armed/disarmed) of the security system if the user is authorized and devices are operable.
    
        Args:
            system_id (str): Identifier of the target security system.
            user_id (str): Identifier of the requesting user.
            new_mode (str): Desired mode, either 'armed' or 'disarmed'.
    
        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Only authorized users (requiring 'set_mode' privilege) may change the mode.
            - To arm, all devices of type 'alarm' must be active and operable.
            - System logs all mode changes as events.
            - Valid modes: 'armed', 'disarmed'.
        """
        # Validate inputs
        if system_id not in self.security_systems:
            return {"success": False, "error": "Security system not found."}
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}
        if new_mode not in ["armed", "disarmed"]:
            return {"success": False, "error": "Invalid mode specified."}

        system = self.security_systems[system_id]
        user = self.users[user_id]

        # Privilege check
        if "set_mode" not in user.get("privileges", []):
            return {"success": False, "error": "User lacks privilege to set system mode."}

        current_mode = system["mode"]
        if current_mode == new_mode:
            return {"success": True, "message": f"System already in mode '{new_mode}'."}

        # If arming, ensure all alarms are active and operable
        if new_mode == "armed":
            for device in self.devices.values():
                if device["type"] == "alarm":
                    if not self._alarm_is_ready_for_arming(device):
                        return {"success": False, "error": f"Alarm device '{device['device_id']}' is not operable."}

        # Set new mode and update last_updated timestamp
        system["mode"] = new_mode
        system["last_updated"] = datetime.utcnow().isoformat()
        self.security_systems[system_id] = system  # Not strictly necessary, but consistent

        # Log the event
        event = {
            "event_id": f"{system_id}_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": f"set_mode_{new_mode}",
            "affected_device_id": "",  # Not device-specific
            "resolved_state": new_mode,
        }
        self.events.append(event)

        return {"success": True, "message": f"System mode updated to '{new_mode}'."}

    def update_alert_settings(self, system_id: str, new_settings: dict, user_id: str) -> dict:
        """
        Update the alert threshold/configuration for the security system (e.g., motion sensitivity, alarm delay).

        Args:
            system_id (str): ID of the target security system to update.
            new_settings (dict): New alert settings to apply.
            user_id (str): User performing the update (must have proper privileges).

        Returns:
            dict: {
                "success": True,
                "message": "Alert settings updated for system X."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Only authorized users ('admin' or 'configure_alerts') may update alert settings.
            - System's 'last_updated' must be set to current time.
            - Action is logged in self.events.
            - Security system and user must exist.
        """

        # Check if system exists
        if system_id not in self.security_systems:
            return { "success": False, "error": "Security system not found" }
    
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        user = self.users[user_id]
    
        # Check privilege
        allowed = 'admin' in user['privileges'] or 'configure_alerts' in user['privileges']
        if not allowed:
            return { "success": False, "error": "Insufficient privileges" }

        # Validate settings
        if not isinstance(new_settings, dict) or not new_settings:
            return { "success": False, "error": "New settings must be a non-empty dictionary" }
    
        # Update settings in place (replace, or could merge if required)
        self.security_systems[system_id]['alert_settings'] = new_settings
        self.security_systems[system_id]['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        # Log the action as an event
        event_info = {
            "event_id": f"evt_{int(time.time()*1000)}",
            "timestamp": self.security_systems[system_id]['last_updated'],
            "event_type": "alert_settings_updated",
            "affected_device_id": system_id,
            "resolved_state": "settings_updated"
        }
        self.events.append(event_info)

        return {
            "success": True,
            "message": f"Alert settings updated for system {system_id}."
        }

    def log_event(
        self,
        event_id: str,
        timestamp: str,
        event_type: str,
        affected_device_id: str,
        resolved_state: str
    ) -> dict:
        """
        Record an event/state change (e.g., mode changes, device triggers, config changes) in the event history.

        Args:
            event_id (str): Unique identifier for the event. Must not duplicate existing events.
            timestamp (str): Time of the event (e.g., ISO8601).
            event_type (str): Nature/type of event (e.g., 'armed', 'device_triggered', etc.).
            affected_device_id (str): Device affected; if not relevant, pass an empty string.
            resolved_state (str): The resolution or resulting state (e.g., 'resolved', 'pending', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Event logged successfully."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - event_id must be unique in the event log.
            - If affected_device_id is given (non-empty), the device must exist.
            - All fields are required (except affected_device_id, which can be empty if N/A).
        """
        # Check non-empty fields (except affected_device_id, which can be empty string)
        for field_value, field_name in [
            (event_id, "event_id"),
            (timestamp, "timestamp"),
            (event_type, "event_type"),
            (resolved_state, "resolved_state")
        ]:
            if not field_value:
                return {"success": False, "error": f"Missing required field: {field_name}"}

        # Check for duplicate event_id
        if any(event["event_id"] == event_id for event in self.events):
            return {"success": False, "error": "Duplicate event_id"}

        # If affected_device_id is specified, confirm it exists
        if affected_device_id and affected_device_id not in self.devices:
            return {"success": False, "error": "Specified affected_device_id does not exist"}

        event_info: EventInfo = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "affected_device_id": affected_device_id,
            "resolved_state": resolved_state
        }
        self.events.append(event_info)
        return {"success": True, "message": "Event logged successfully."}

    def update_device_status(
        self, 
        device_id: str, 
        status: str = None, 
        operational_state: str = None
    ) -> dict:
        """
        Change the operational status (active/inactive) and/or state of a specified device.

        Args:
            device_id (str): The unique identifier of the device to update.
            status (str, optional): The new device status ("active"/"inactive"). If None, status is not changed.
            operational_state (str, optional): New operational state value. If None, state is not changed.

        Returns:
            dict:
                On success: { "success": True, "message": "Device status/state updated." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Device must exist.
            - At least one of 'status' or 'operational_state' must be provided.
            - Status must be 'active' or 'inactive' if provided.
            - All changes are logged in the event history (self.events).
        """

        # Validate device exists
        if device_id not in self.devices:
            return { "success": False, "error": "Device does not exist." }

        # Validate at least one update value provided
        if status is None and operational_state is None:
            return { "success": False, "error": "No status or operational_state value specified." }

        device = self.devices[device_id]
        changes = []
        event_types = []
        old_status = device["status"]
        old_operational_state = device["operational_state"]

        # Update status if specified
        if status is not None:
            if status not in ("active", "inactive"):
                return { "success": False, "error": "Invalid status value. Must be 'active' or 'inactive'." }
            if status != old_status:
                device["status"] = status
                changes.append(f"status: {old_status} -> {status}")
                event_types.append("device_status_changed")
            # else: no status change

        # Update operational_state if specified
        if operational_state is not None:
            if operational_state != old_operational_state:
                device["operational_state"] = operational_state
                changes.append(f"operational_state: {old_operational_state} -> {operational_state}")
                event_types.append("device_operational_state_changed")
            # else: no operational_state change

        if not changes:
            return { "success": True, "message": "No changes made. Device already had requested status/state." }

        # Log one event per type of change
        timestamp = datetime.utcnow().isoformat() + "Z"
        for evt_type in set(event_types):
            self.events.append({
                "event_id": f"ev-{int(time.time()*1e6)}-{evt_type}",  # Unique event ID
                "timestamp": timestamp,
                "event_type": evt_type,
                "affected_device_id": device_id,
                "resolved_state": device["status"]
            })

        return { "success": True, "message": f"Device status/state updated. {'; '.join(changes)}" }


class SmartHomeSecuritySystem(BaseEnv):
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

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def check_user_privileges(self, **kwargs):
        return self._call_inner_tool('check_user_privileges', kwargs)

    def get_security_system_status(self, **kwargs):
        return self._call_inner_tool('get_security_system_status', kwargs)

    def get_devices_by_type(self, **kwargs):
        return self._call_inner_tool('get_devices_by_type', kwargs)

    def get_device_status(self, **kwargs):
        return self._call_inner_tool('get_device_status', kwargs)

    def get_event_log(self, **kwargs):
        return self._call_inner_tool('get_event_log', kwargs)

    def get_alert_settings(self, **kwargs):
        return self._call_inner_tool('get_alert_settings', kwargs)

    def set_security_system_mode(self, **kwargs):
        return self._call_inner_tool('set_security_system_mode', kwargs)

    def update_alert_settings(self, **kwargs):
        return self._call_inner_tool('update_alert_settings', kwargs)

    def log_event(self, **kwargs):
        return self._call_inner_tool('log_event', kwargs)

    def update_device_status(self, **kwargs):
        return self._call_inner_tool('update_device_status', kwargs)
