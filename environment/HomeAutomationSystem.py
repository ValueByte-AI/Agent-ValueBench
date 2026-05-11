# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict
import datetime
import json



class DeviceInfo(TypedDict):
    device_id: str
    type: str  # (e.g., light, HVAC, entertainment)
    state: Dict[str, Any]  # e.g., {'on': True, 'brightness': 70}
    location: str  # room_id or zone_id
    last_updated: str  # timestamp as ISO string
    supported_setting: List[str]  # e.g., ['on/off', 'brightness']
    allowed_ranges: Dict[str, Any]

class RoomInfo(TypedDict):
    room_id: str
    name: str
    list_of_device_id: List[str]

class SceneInfo(TypedDict):
    scene_id: str
    name: str
    trigger_conditions: Any  # e.g., could be dict or list, for time/event triggers
    device_settings: List[Dict[str, Any]]  # intended device states/values
    enabled: bool

class UserInfo(TypedDict):
    user_id: str
    name: str
    preferences: Dict[str, Any]  # e.g., preferred sleep temperature, wake time

class _GeneratedEnvImpl:
    def __init__(self):
        # Devices: {device_id: DeviceInfo}
        self.devices: Dict[str, DeviceInfo] = {}
        # Rooms/Zones: {room_id: RoomInfo}
        self.rooms: Dict[str, RoomInfo] = {}
        # Scenes/Automations: {scene_id: SceneInfo}
        self.scenes: Dict[str, SceneInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Optional per-device range overrides injected from initial state.
        self._device_allowed_ranges_state: Dict[str, Dict[str, Any]] = {}

        # Constraints:
        # - Device state changes must fall within allowed ranges (e.g., setpoint min/max, dimming).
        # - Some device types only accept specific commands (e.g., lights can't set temperature).
        # - Scenes/automations can be enabled/disabled by users or agents.
        # - Device states must synchronize with hardware if manual override occurs.
        # - Room assignments for devices must remain consistent for location-based actions.

    @staticmethod
    def _parse_benchmark_timestamp(timestamp: str):
        if not isinstance(timestamp, str) or not timestamp:
            return None
        normalized = timestamp.replace("Z", "+00:00")
        try:
            dt = datetime.datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt

    def _next_benchmark_timestamp(self) -> str:
        latest = None
        for device in self.devices.values():
            dt = self._parse_benchmark_timestamp(device.get("last_updated"))
            if dt is not None and (latest is None or dt > latest):
                latest = dt
        if latest is None:
            latest = datetime.datetime(1970, 1, 1, 0, 0, 0)
        else:
            latest = latest + datetime.timedelta(seconds=1)
        return latest.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _device_info_with_allowed_ranges(self, device: DeviceInfo) -> DeviceInfo:
        device_info = copy.deepcopy(device)
        allowed_ranges_resp = self.get_device_allowed_ranges(device_info["device_id"])
        device_info["allowed_ranges"] = (
            copy.deepcopy(allowed_ranges_resp["data"])
            if allowed_ranges_resp.get("success")
            else {}
        )
        return device_info

    def _validate_device_state_change(self, device_id: str, new_state: Dict[str, Any]) -> dict:
        if device_id not in self.devices:
            return {"success": False, "error": "Device does not exist"}
        if not isinstance(new_state, dict) or not new_state:
            return {"success": False, "error": "No state changes specified"}

        device = self.devices[device_id]
        supported_settings = device.get("supported_setting", [])
        allowed_ranges_resp = self.get_device_allowed_ranges(device_id)
        allowed_ranges = allowed_ranges_resp["data"] if allowed_ranges_resp.get("success") else {}

        for key, value in new_state.items():
            if key not in supported_settings:
                return {
                    "success": False,
                    "error": f"Setting '{key}' not supported for device type '{device['type']}'"
                }

            if key not in allowed_ranges:
                continue
            limits = allowed_ranges[key]
            if isinstance(limits, dict):
                if "min" in limits and value < limits["min"]:
                    return {"success": False, "error": f"Value for '{key}' below minimum ({limits['min']})"}
                if "max" in limits and value > limits["max"]:
                    return {"success": False, "error": f"Value for '{key}' above maximum ({limits['max']})"}
                if "allowed" in limits and value not in limits["allowed"]:
                    return {"success": False, "error": f"Value for '{key}' not allowed: {value}"}
            elif isinstance(limits, list):
                if value not in limits:
                    return {"success": False, "error": f"Value for '{key}' not allowed: {value}"}

        return {"success": True}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve the user info and preferences for a user given their exact name.

        Args:
            name (str): The exact name of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo        # User record found
            }
            or
            {
                "success": False,
                "error": str            # "User not found"
            }

        Constraints:
            - User name must be an exact match.
        """
        for user in self.users.values():
            if user["name"] == name:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Retrieve the automation and environment preferences for a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Any],  # User's preferences (may be empty if none set)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., user not found)
            }

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user.get("preferences", {}) }

    def get_room_by_name(self, room_name: str) -> dict:
        """
        Retrieve room/zone information (room_id, name, list_of_device_id) by its name.

        Args:
            room_name (str): The name of the room/zone to query (e.g., "bedroom").

        Returns:
            dict: {
                "success": True,
                "data": RoomInfo,  # The matching room's info
            }
            or
            {
                "success": False,
                "error": str  # Description of the error if the room is not found
            }

        Constraints:
            - Names are matched exactly (case-sensitive).
            - If multiple rooms share the same name, the first found is returned.
        """
        for room in self.rooms.values():
            if room["name"] == room_name:
                return { "success": True, "data": room }
        return { "success": False, "error": f"Room with name '{room_name}' not found" }

    def list_devices_in_room(self, room_id: str) -> dict:
        """
        List all devices assigned to a particular room or zone.

        Args:
            room_id (str): The ID of the room or zone.

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo],  # List of device information assigned to the room
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - room_id must exist in the system.
            - Only devices currently present in self.devices and listed in the room are returned.
        """
        if room_id not in self.rooms:
            return {"success": False, "error": f"Room or zone '{room_id}' does not exist."}

        device_infos = []
        for device_id in self.rooms[room_id]["list_of_device_id"]:
            if device_id in self.devices:
                device_infos.append(self._device_info_with_allowed_ranges(self.devices[device_id]))

        return {"success": True, "data": device_infos}

    def get_device_info(self, device_id: str) -> dict:
        """
        Retrieve detailed information and the current state for the device with the specified device_id.

        Args:
            device_id (str): The unique identifier for the device.

        Returns:
            dict: {
                "success": True,
                "data": DeviceInfo  # Dictionary with all device metadata and state.
            }
            or
            {
                "success": False,
                "error": str  # If device not found.
            }

        Constraints:
            - The device_id must exist in the system.
            - No hardware query is performed; this is an in-memory state fetch.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }

        return { "success": True, "data": self._device_info_with_allowed_ranges(device) }

    def filter_devices_by_type(self, device_ids: list, device_type: str) -> dict:
        """
        Filter a device list by type.

        Args:
            device_ids (List[str]): List of device IDs to filter.
            device_type (str): The device type to filter by (e.g., 'HVAC', 'light').

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo],  # All matching devices' info
            }

        Notes:
            - If a device_id in device_ids does not exist, it is skipped.
            - If no devices match, returns empty list (success).
        """
        if not isinstance(device_ids, list) or not isinstance(device_type, str):
            return { "success": False, "error": "Invalid input types" }

        result = [
            self.devices[dev_id]
            for dev_id in device_ids
            if dev_id in self.devices and self.devices[dev_id]["type"] == device_type
        ]

        return { "success": True, "data": result }

    def get_device_supported_settings(self, device_id: str) -> dict:
        """
        Query which settings or commands are supported for a given device.

        Args:
            device_id (str): The unique identifier for the target device.

        Returns:
            dict:
                - On success: {"success": True, "data": List[str]}  # list of supported settings
                - On failure: {"success": False, "error": str}      # error message, e.g., device not found

        Constraints:
            - The device_id must exist in the system.
        """
        device = self.devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        return {"success": True, "data": device.get("supported_setting", [])}

    def get_device_state(self, device_id: str) -> dict:
        """
        Retrieve the current state (on/off, brightness, setpoint, etc.) for a device.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Any]  # The device's current state,
            }
            or
            {
                "success": False,
                "error": str  # If the device does not exist
            }

        Constraints:
            - device_id must exist within the system.
        """
        device = self.devices.get(device_id)
        if device is None:
            return { "success": False, "error": "Device ID not found" }
        return { "success": True, "data": device.get("state", {}) }

    def get_scene_by_name(self, scene_name: str) -> dict:
        """
        Retrieve a scene/automation by its name.

        Args:
            scene_name (str): The name of the scene or automation to retrieve.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": SceneInfo  # Scene metadata and settings
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Scene not found"
                    }

        Constraints:
            - Scene names are considered unique.
        """
        for scene in self.scenes.values():
            if scene['name'] == scene_name:
                return { "success": True, "data": scene }
        return { "success": False, "error": "Scene not found" }

    def list_scenes_for_room(self, room_id: str) -> dict:
        """
        List all automations/scenes that affect devices within a given room.

        Args:
            room_id (str): The ID of the room to check.

        Returns:
            dict: {
                "success": True,
                "data": List[SceneInfo],  # List of matching scenes (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If room does not exist
            }

        Constraints:
            - Only scenes that directly affect devices associated with this room are included.
            - Considers the list_of_device_id for the room and matches with each scene's device_settings.
        """
        if room_id not in self.rooms:
            return { "success": False, "error": "Room does not exist" }
        device_ids = set(self.rooms[room_id]['list_of_device_id'])
        affected_scenes = []
        for scene in self.scenes.values():
            for device_setting in scene.get('device_settings', []):
                device_id = device_setting.get('device_id')
                if device_id in device_ids:
                    affected_scenes.append(scene)
                    break  # Only add scene once
        return { "success": True, "data": affected_scenes }

    def get_device_allowed_ranges(self, device_id: str) -> dict:
        """
        Get configuration constraints/ranges for supported settings for a specific device.

        Args:
            device_id (str): The identifier for the device.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Dict[str, Any]]  # e.g. { 'brightness': {'min':0, 'max':100}, ... }
            }
            or
            {
                "success": False,
                "error": str  # e.g. 'Device not found'
            }

        Constraints:
            - device_id must exist in the system.
            - Only settings from supported_setting (and that have defined ranges) are returned.
        """
        # Allowed ranges mapping by device type and setting.
        ALLOWED_RANGES = {
            'light': {
                'brightness': {'min': 0, 'max': 100},
                'on': {'allowed': [True, False]},
                'color': {'allowed': ['white', 'warm', 'warm white', 'warm_white', 'dynamic', 'high-contrast']},
            },
            'HVAC': {
                'temperature': {'min': 60, 'max': 85},
                'mode': {'allowed': ['cool', 'heat', 'fan', 'auto', 'off']},
            },
            'vacuum': {
                'status': {'allowed': ['cleaning', 'docked', 'error_stuck', 'idle']},
                'alarm': {'allowed': [True, False]},
                'volume': {'min': 0, 'max': 10},
            },
            'door': {
                'locked': {'allowed': [True, False]},
            },
            'laser_strobe': {
                'on': {'allowed': [True, False]},
                'mode': {'allowed': ['off', 'steady', 'dynamic', 'strobe']},
                'intensity': {'min': 0, 'max': 100},
            },
            'surround_sound': {
                'on': {'allowed': [True, False]},
                'volume': {'min': 0, 'max': 100},
                'bass_boost': {'allowed': [True, False]},
            },
        }

        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }
    
        device_type = device["type"]
        supported_settings = device.get("supported_setting", [])

        allowed_ranges: dict = {}
        state_overrides = self._device_allowed_ranges_state.get(device_id, {})
        for setting in supported_settings:
            if setting in state_overrides:
                allowed_ranges[setting] = copy.deepcopy(state_overrides[setting])
                continue
            type_ranges = ALLOWED_RANGES.get(device_type, {})
            if setting in type_ranges:
                allowed_ranges[setting] = type_ranges[setting]
        return { "success": True, "data": allowed_ranges }

    def set_device_state(self, device_id: str, new_state: Dict[str, Any]) -> dict:
        """
        Change one or more state properties of a device, ensuring that new values
        comply with device constraints (supported settings and value ranges).

        Args:
            device_id (str): The ID of the device to modify.
            new_state (Dict[str, Any]): State keys and values to set; e.g., {'on': True, 'brightness': 60}

        Returns:
            dict: {
                "success": True,
                "message": "Device state updated"
            }
            or
            {
                "success": False,
                "error": Reason for failure
            }

        Constraints:
          - Device must exist.
          - State keys must be supported by device type.
          - Values must be within allowed ranges for each setting.
        """
        validation = self._validate_device_state_change(device_id, new_state)
        if not validation.get("success"):
            return validation

        device = self.devices[device_id]
        device['state'].update(new_state)
        device['last_updated'] = self._next_benchmark_timestamp()

        return { "success": True, "message": "Device state updated" }

    def enable_scene(self, scene_id: str) -> dict:
        """
        Enable a particular scene/automation so its automatic actions become active.

        Args:
            scene_id (str): The identifier of the scene to enable.

        Returns:
            dict: 
                { "success": True, "message": "Scene <scene_id> enabled" }
                OR
                { "success": False, "error": "<reason>" }

        Constraints:
            - The scene must exist in the system.
            - Sets scene's 'enabled' field to True.
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            return { "success": False, "error": "Scene not found" }
        if scene["enabled"]:
            return { "success": True, "message": f"Scene {scene_id} already enabled" }

        scene["enabled"] = True
        # Optionally update self.scenes[scene_id], but as dict this mutates in place
        return { "success": True, "message": f"Scene {scene_id} enabled" }

    def disable_scene(self, scene_id: str) -> dict:
        """
        Disable a particular scene/automation so it cannot be triggered.

        Args:
            scene_id (str): The unique identifier of the scene to disable.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Scene <scene_id> disabled" }
                - On failure: { "success": False, "error": "Scene not found" }

        Constraints:
            - The scene must exist in the system.
            - No effect if scene is already disabled (idempotent).
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            return { "success": False, "error": "Scene not found" }

        # Idempotency: disabling an already-disabled scene is still success
        scene["enabled"] = False
        return { "success": True, "message": f"Scene {scene_id} disabled" }

    def update_scene_device_settings(self, scene_id: str, device_settings: list) -> dict:
        """
        Update the device_settings list for a given scene, altering which device states will
        be set when the scene is activated.

        Args:
            scene_id (str): The identifier of the scene to update.
            device_settings (list of dict): The new list of device setting dicts for the scene.

        Returns:
            dict: {
                "success": True,
                "message": "Device settings updated for scene <scene_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - The scene must exist.
            - device_settings must be a list of dicts.
        """
        if scene_id not in self.scenes:
            return { "success": False, "error": "Scene does not exist" }

        if not isinstance(device_settings, list):
            return { "success": False, "error": "device_settings must be a list" }

        for ds in device_settings:
            if not isinstance(ds, dict):
                return { "success": False, "error": "Each device setting must be a dictionary" }
            if "device_id" not in ds:
                return { "success": False, "error": "Each device setting must include device_id" }

            state_payload = None
            if "state" in ds:
                state_payload = ds.get("state")
            elif "settings" in ds:
                state_payload = ds.get("settings")
            else:
                state_payload = {k: v for k, v in ds.items() if k != "device_id"}

            if not isinstance(state_payload, dict) or not state_payload:
                return { "success": False, "error": "Each device setting must include a non-empty state/settings payload" }

            validation = self._validate_device_state_change(ds["device_id"], state_payload)
            if not validation.get("success"):
                return validation

        self.scenes[scene_id]["device_settings"] = device_settings

        return { "success": True, "message": f"Device settings updated for scene {scene_id}" }


    def synchronize_manual_device_state(self, device_id: str, updated_state: dict) -> dict:
        """
        Synchronize a device's logical state to match a physical (manual/agent) change.

        Args:
            device_id (str): The device to synchronize.
            updated_state (dict): The intended new state, as reported by hardware or agent override.

        Returns:
            dict:
                On success: {"success": True, "message": "Device state synchronized."}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - Device must exist.
            - State keys must be allowed for this device (see supported_setting).
            - State values must fall within allowed ranges (assume a get_device_allowed_ranges method exists).
            - Updates device's logical state and last_updated timestamp.
        """

        validation = self._validate_device_state_change(device_id, updated_state)
        if not validation.get("success"):
            return validation

        device = self.devices[device_id]
        device["state"].update(updated_state)
        device["last_updated"] = self._next_benchmark_timestamp()

        # In real system, here is where hardware sync would be performed

        return {"success": True, "message": "Device state synchronized."}

    def update_user_preferences(self, user_id: str, preferences: dict) -> dict:
        """
        Update the stored preferences for a given user. Only the provided keys will be updated/added.

        Args:
            user_id (str): The unique identifier for the user.
            preferences (dict): Dictionary of preference key/values to update.

        Returns:
            dict: {
                "success": True,
                "message": "User preferences updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The user must exist (user_id in self.users).
            - The preferences argument must be a dict.
            - Preferences are arbitrary key-value pairs (freeform).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if not isinstance(preferences, dict):
            return { "success": False, "error": "Preferences must be a dictionary." }

        # Update/merge preferences; add or overwrite keys.
        self.users[user_id]["preferences"].update(preferences)

        return { "success": True, "message": "User preferences updated." }


class HomeAutomationSystem(BaseEnv):
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
            if key == "get_device_allowed_ranges":
                parsed = copy.deepcopy(value)
                if isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except Exception:
                        parsed = {}
                env._device_allowed_ranges_state = parsed if isinstance(parsed, dict) else {}
                continue
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

    def get_user_preferences(self, **kwargs):
        return self._call_inner_tool('get_user_preferences', kwargs)

    def get_room_by_name(self, **kwargs):
        return self._call_inner_tool('get_room_by_name', kwargs)

    def list_devices_in_room(self, **kwargs):
        return self._call_inner_tool('list_devices_in_room', kwargs)

    def get_device_info(self, **kwargs):
        return self._call_inner_tool('get_device_info', kwargs)

    def filter_devices_by_type(self, **kwargs):
        return self._call_inner_tool('filter_devices_by_type', kwargs)

    def get_device_supported_settings(self, **kwargs):
        return self._call_inner_tool('get_device_supported_settings', kwargs)

    def get_device_state(self, **kwargs):
        return self._call_inner_tool('get_device_state', kwargs)

    def get_scene_by_name(self, **kwargs):
        return self._call_inner_tool('get_scene_by_name', kwargs)

    def list_scenes_for_room(self, **kwargs):
        return self._call_inner_tool('list_scenes_for_room', kwargs)

    def get_device_allowed_ranges(self, **kwargs):
        return self._call_inner_tool('get_device_allowed_ranges', kwargs)

    def set_device_state(self, **kwargs):
        return self._call_inner_tool('set_device_state', kwargs)

    def enable_scene(self, **kwargs):
        return self._call_inner_tool('enable_scene', kwargs)

    def disable_scene(self, **kwargs):
        return self._call_inner_tool('disable_scene', kwargs)

    def update_scene_device_settings(self, **kwargs):
        return self._call_inner_tool('update_scene_device_settings', kwargs)

    def synchronize_manual_device_state(self, **kwargs):
        return self._call_inner_tool('synchronize_manual_device_state', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)
