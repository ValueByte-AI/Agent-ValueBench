# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import datetime
import time



class AppConfigurationInfo(TypedDict):
    app_id: str
    current_version: str
    release_channel: str
    last_updated: str  # Timestamp, could be ISO string or epoch

class ResourceVersionInfo(TypedDict):
    resource_type: str
    version: str
    last_updated: str  # Timestamp

class PlatformCompatibilityInfo(TypedDict):
    platform_name: str
    platform_version: str
    min_supported_version: str
    max_supported_version: str

class UISettingInfo(TypedDict):
    setting_name: str
    value: str
    last_updated: str  # Timestamp

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Mobile Application Configuration Management System stateful environment.
        """
        # AppConfigurations: {app_id: AppConfigurationInfo}
        self.app_configurations: Dict[str, AppConfigurationInfo] = {}

        # ResourceVersions: {resource_type: ResourceVersionInfo}
        self.resource_versions: Dict[str, ResourceVersionInfo] = {}

        # PlatformCompatibility: {"platform_name:platform_version": PlatformCompatibilityInfo}
        self.platform_compatibility: Dict[str, PlatformCompatibilityInfo] = {}

        # UISettings: {setting_name: UISettingInfo}
        self.ui_settings: Dict[str, UISettingInfo] = {}

        # --- State Space entity/attribute mapping:
        # - app_configurations → AppConfiguratio: app_id, current_version, release_channel, last_updated
        # - resource_versions → ResourceVersio: resource_type, version, last_updated
        # - platform_compatibility → PlatformCompatibil: platform_name, platform_version, min_supported_version, max_supported_version
        # - ui_settings → UISettings: setting_name, value, last_updated

        # --- Constraints (to be implemented in operations):
        # - Each resource type must have a unique version tracked.
        # - App version and platform compatibility must be updated prior to deployment.
        # - UI settings must be applied atomically to prevent inconsistent user experiences.
        # - All configuration changes should be timestamped (last_updated) for auditability.

    def get_app_configuration(self, app_id: str) -> dict:
        """
        Retrieve app configuration details including current_version, release_channel, and last_updated for the specified app_id.

        Args:
            app_id (str): The unique identifier for the app.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AppConfigurationInfo
                    }
                On failure (if app_id not found):
                    {
                        "success": False,
                        "error": "App ID not found"
                    }

        Constraints:
            - The app_id must exist in the system.
        """
        info = self.app_configurations.get(app_id)
        if info is None:
            return { "success": False, "error": "App ID not found" }
        return { "success": True, "data": info }

    def get_resource_version(self, resource_type: str) -> dict:
        """
        Retrieve the version and last_updated timestamp for a specific resource type.

        Args:
            resource_type (str): The type of the resource to look up (e.g., 'menu', 'translations').

        Returns:
            dict: 
              {
                  "success": True,
                  "data": ResourceVersionInfo
              }
              or
              {
                  "success": False,
                  "error": str
              }
            - On success, returns version info for the resource type.
            - If resource_type not found, returns error.
    
        Constraints:
            - Each resource type must have a unique version tracked.
            - Read-only operation; no timestamp update.
        """
        if resource_type not in self.resource_versions:
            return {"success": False, "error": "Resource type not found"}

        data = self.resource_versions[resource_type]
        return {"success": True, "data": data}

    def list_resource_versions(self) -> dict:
        """
        Retrieve all registered resource types and their current versions.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceVersionInfo]  # May be empty if no resource types are registered.
            }

        Constraints:
            - Each resource type is unique (enforced by resource_versions dictionary key).
            - Read-only operation; does not modify state.
        """
        resource_versions_list = list(self.resource_versions.values())
        return {
            "success": True,
            "data": resource_versions_list
        }

    def get_platform_compatibility(self, platform_name: str, platform_version: str) -> dict:
        """
        Retrieve platform compatibility information (min/max supported version) for a given platform name and version.

        Args:
            platform_name (str): The name of the platform (e.g., 'Android', 'iOS').
            platform_version (str): The specific version of the platform.

        Returns:
            dict: {
                "success": True,
                "data": PlatformCompatibilityInfo  # Information about min/max supported version, etc.
            }
            or
            {
                "success": False,
                "error": str  # Description if not found
            }

        Constraints:
            - The pair (platform_name, platform_version) is used as a unique key for lookup.
        """
        key = f"{platform_name}:{platform_version}"
        info = self.platform_compatibility.get(key)
        if info is None:
            return {
                "success": False,
                "error": "Platform compatibility entry not found"
            }
        return {
            "success": True,
            "data": info
        }

    def list_platform_compatibility(self) -> dict:
        """
        Lists compatibility info for all supported platforms and versions.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PlatformCompatibilityInfo]  # All platform compatibility entries
            }
        """
        result = list(self.platform_compatibility.values())
        return { "success": True, "data": result }

    def get_ui_setting(self, setting_name: str) -> dict:
        """
        Retrieve the current value and last_updated timestamp of a specific UI setting.

        Args:
            setting_name (str): The key/name of the UI setting to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "setting_name": str,
                    "value": str,
                    "last_updated": str
                }
            }
            OR
            {
                "success": False,
                "error": "UI setting not found"
            }

        Constraints:
            - The requested setting must exist in the system.
        """
        setting = self.ui_settings.get(setting_name)
        if not setting:
            return { "success": False, "error": "UI setting not found" }

        return {
            "success": True,
            "data": {
                "setting_name": setting["setting_name"],
                "value": setting["value"],
                "last_updated": setting["last_updated"]
            }
        }

    def list_ui_settings(self) -> dict:
        """
        Retrieve all UI setting names and values.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict has "setting_name" and "value"
            }

        Constraints:
            - Returns all UI settings; success even if no settings exist (empty list).
        """
        result = [
            {"setting_name": s["setting_name"], "value": s["value"]}
            for s in self.ui_settings.values()
        ]
        return {"success": True, "data": result}

    def update_app_configuration(
        self,
        app_id: str,
        current_version: str,
        release_channel: str,
        last_updated: str
    ) -> dict:
        """
        Update the app configuration for the specified app.

        Args:
            app_id (str): App identifier to update.
            current_version (str): New version label/string to set.
            release_channel (str): New release channel (e.g., 'beta', 'stable') to set.
            last_updated (str): Timestamp string (ISO or epoch) of this update.

        Returns:
            dict: {
              "success": True,
              "message": "App configuration updated for app_id=..."
            }
            or
            {
              "success": False,
              "error": "App ID ... does not exist"
            }

        Constraints:
          - The given app_id must already exist in the system.
          - The last_updated field is mandatory and will be set.
          - Only current_version, release_channel, and last_updated are affected.
          - All configuration changes must have the last_updated timestamp for auditability.
        """
        if app_id not in self.app_configurations:
            return {
                "success": False,
                "error": f"App ID '{app_id}' does not exist"
            }
        # Update the fields
        self.app_configurations[app_id]['current_version'] = current_version
        self.app_configurations[app_id]['release_channel'] = release_channel
        self.app_configurations[app_id]['last_updated'] = last_updated

        return {
            "success": True,
            "message": f"App configuration updated for app_id={app_id}"
        }

    def update_resource_version(self, resource_type: str, version: str) -> dict:
        """
        Set a new version for a given resource type (creating or updating as needed).
        Ensures each resource_type remains unique and updates the last_updated timestamp.

        Args:
            resource_type (str): The type identifier for the resource (e.g., 'menu', 'translations').
            version (str): The new version string to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Resource version updated."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure."
                    }

        Constraints:
            - Each resource_type must have a unique version tracked.
            - Must update last_updated timestamp to now.
        """

        # Validation
        if not isinstance(resource_type, str) or not resource_type.strip():
            return {"success": False, "error": "Invalid resource_type."}
        if not isinstance(version, str) or not version.strip():
            return {"success": False, "error": "Invalid version."}

        now = datetime.datetime.utcnow().isoformat()

        self.resource_versions[resource_type] = {
            "resource_type": resource_type,
            "version": version,
            "last_updated": now
        }

        return {
            "success": True,
            "message": f"Resource version for '{resource_type}' set to '{version}' and timestamp updated."
        }

    def update_platform_compatibility(
        self,
        platform_name: str,
        platform_version: str,
        min_supported_version: str,
        max_supported_version: str,
        last_updated: str
    ) -> dict:
        """
        Modify the platform compatibility info for a platform/version.

        Args:
            platform_name (str): The name of the platform (e.g., "Android", "iOS").
            platform_version (str): The major (or major.minor) platform version to update.
            min_supported_version (str): New minimum supported version.
            max_supported_version (str): New maximum supported version.
            last_updated (str): Timestamp of this configuration change (ISO or epoch).

        Returns:
            dict: 
                On success: { "success": True, "message": "Platform compatibility for ... updated." }
                On failure: { "success": False, "error": "...reason..." }

        Constraints:
            - The record to update must exist. (No create-on-missing.)
            - The min_supported_version must not be greater than max_supported_version (numeric version compare when possible).
            - All configuration changes should be timestamped (last_updated).
        """
        key = f"{platform_name}:{platform_version}"
        if not all([platform_name, platform_version, min_supported_version, max_supported_version, last_updated]):
            return { "success": False, "error": "All input fields must be provided." }

        if key not in self.platform_compatibility:
            return { "success": False, "error": "Platform compatibility info not found for the specified platform and version." }

        min_version_parts = tuple(int(part) for part in re.findall(r"\d+", min_supported_version))
        max_version_parts = tuple(int(part) for part in re.findall(r"\d+", max_supported_version))
        if min_version_parts and max_version_parts:
            invalid_range = min_version_parts > max_version_parts
        else:
            invalid_range = min_supported_version > max_supported_version

        if invalid_range:
            return { "success": False, "error": "min_supported_version cannot be greater than max_supported_version." }

        info = self.platform_compatibility[key]
        info['min_supported_version'] = min_supported_version
        info['max_supported_version'] = max_supported_version
        info['last_updated'] = last_updated

        self.platform_compatibility[key] = info

        return {
            "success": True,
            "message": f"Platform compatibility for {platform_name} {platform_version} updated."
        }

    def apply_ui_settings_atomically(self, updates: list) -> dict:
        """
        Atomically apply a batch of UI setting updates.

        Args:
            updates (list): List of dicts, each with:
                - 'setting_name' (str): the UI setting name to update.
                - 'value' (str): the new value to assign.

        Returns:
            dict:
                On Success:
                    { "success": True, "message": "All UI settings updated atomically" }
                On Failure:
                    {
                        "success": False,
                        "error": <reason string>
                    }
        Constraints:
            - If any setting_name does not exist or input is malformed, no updates are applied.
            - All last_updated fields must be set to the current timestamp.
            - If updates is empty, do nothing and succeed.
            - Duplicate setting_names in input are treated as an error (no updates performed).
        """

        if not isinstance(updates, list):
            return { "success": False, "error": "Input must be a list of updates" }
        if not updates:
            return { "success": True, "message": "No updates to apply" }

        # Gather all setting_names to update
        setting_names = [u.get('setting_name') for u in updates]

        # Check for missing parameters in updates
        for u in updates:
            if 'setting_name' not in u or 'value' not in u:
                return { "success": False, "error": "Each update must include 'setting_name' and 'value'" }
            if not isinstance(u['setting_name'], str):
                return { "success": False, "error": "setting_name must be a string" }

        # Check for duplicate setting_names in the batch
        if len(setting_names) != len(set(setting_names)):
            return { "success": False, "error": "Duplicate setting_names in input batch are not allowed" }

        # Check all setting_names exist
        for name in setting_names:
            if name not in self.ui_settings:
                return { "success": False, "error": f"Setting '{name}' does not exist" }

        current_timestamp = str(time.time())

        # Apply all updates atomically
        for u in updates:
            name = u['setting_name']
            value = u['value']
            # Update value and last_updated
            self.ui_settings[name]['value'] = value
            self.ui_settings[name]['last_updated'] = current_timestamp

        return { "success": True, "message": "All UI settings updated atomically" }

    def batch_update_resource_versions(self, updates: list) -> dict:
        """
        Atomically update multiple resource types and their versions,
        enforcing per-resource-type uniqueness and timestamping 'last_updated' for auditability.

        Args:
            updates (list): List of dicts, each with 'resource_type' (str) and 'version' (str).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Successfully updated N resource versions atomically."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Each resource type can appear at most once in the updates list.
            - All updates are atomic: either all are applied, or none.
            - All updates are timestamped with the same new 'last_updated'.
        """
        # --- Input validation ---
        if not isinstance(updates, list):
            return {"success": False, "error": "Input 'updates' must be a list"}

        seen_resource_types = set()
        for idx, upd in enumerate(updates):
            if not isinstance(upd, dict):
                return {"success": False, "error": f"Update at index {idx} is not a dict"}
            if "resource_type" not in upd or "version" not in upd:
                return {"success": False, "error": f"Update at index {idx} missing 'resource_type' or 'version'"}
            rt = upd["resource_type"]
            if rt in seen_resource_types:
                return {"success": False, "error": f"Duplicate resource_type '{rt}' in updates input"}
            seen_resource_types.add(rt)

        # --- All checks passed: prepare atomic update ---
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Prepare new resource_versions mapping so we can apply atomically
        new_resource_versions = self.resource_versions.copy()
        for upd in updates:
            rt = upd["resource_type"]
            ver = upd["version"]
            new_resource_versions[rt] = {
                "resource_type": rt,
                "version": ver,
                "last_updated": timestamp
            }

        # --- Atomicity: all updates successful, so now commit ---
        self.resource_versions = new_resource_versions

        return {
            "success": True,
            "message": f"Successfully updated {len(updates)} resource versions atomically."
        }

    def timestamp_configuration_change(self, entity_type: str, identifier, timestamp: str) -> dict:
        """
        Apply an updated last_updated timestamp to any configuration entity for auditability.

        Args:
            entity_type (str): The kind of entity to update.
                Must be one of: 'app_configuration', 'resource_version', 'ui_setting'
            identifier: The unique identifying key for the entity:
                - For 'app_configuration': app_id (str)
                - For 'resource_version': resource_type (str)
                - For 'ui_setting': setting_name (str)
            timestamp (str): The timestamp (ISO or epoch as used by the config DB) to set.

        Returns:
            dict: {
                "success": True,
                "message": "...",
            }
            or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The identified entity must exist and support 'last_updated'.
            - Only updates the last_updated field.
        """
        if entity_type == "app_configuration":
            app_id = identifier
            if app_id not in self.app_configurations:
                return { "success": False, "error": f"App configuration '{app_id}' not found" }
            self.app_configurations[app_id]["last_updated"] = timestamp
            return {
                "success": True,
                "message": f"Timestamp updated for app_configuration:{app_id}"
            }

        elif entity_type == "resource_version":
            resource_type = identifier
            if resource_type not in self.resource_versions:
                return { "success": False, "error": f"Resource version '{resource_type}' not found" }
            self.resource_versions[resource_type]["last_updated"] = timestamp
            return {
                "success": True,
                "message": f"Timestamp updated for resource_version:{resource_type}"
            }

        elif entity_type == "ui_setting":
            setting_name = identifier
            if setting_name not in self.ui_settings:
                return { "success": False, "error": f"UI setting '{setting_name}' not found" }
            self.ui_settings[setting_name]["last_updated"] = timestamp
            return {
                "success": True,
                "message": f"Timestamp updated for ui_setting:{setting_name}"
            }

        else:
            return {
                "success": False,
                "error": f"Unsupported entity_type '{entity_type}'. Supported types: app_configuration, resource_version, ui_setting"
            }

    def delete_resource_version(self, resource_type: str) -> dict:
        """
        Remove a resource version entry by resource_type.

        Args:
            resource_type (str): The resource type to delete from resource_versions.

        Returns:
            dict:
                - {"success": True, "message": "Resource version '<resource_type>' deleted."}
                - {"success": False, "error": "Resource version for '<resource_type>' does not exist."}

        Constraints:
            - Each resource type must have a unique version tracked.
            - Only delete if resource_type exists.
            - No exception should be raised; always return a result dict.
        """
        if resource_type not in self.resource_versions:
            return {
                "success": False,
                "error": f"Resource version for '{resource_type}' does not exist."
            }
        del self.resource_versions[resource_type]
        return {
            "success": True,
            "message": f"Resource version '{resource_type}' deleted."
        }

    def remove_platform_compatibility(self, platform_name: str, platform_version: str) -> dict:
        """
        Remove platform compatibility setting for a specific platform/version.

        Args:
            platform_name (str): The name of the platform (e.g., 'Android').
            platform_version (str): The version string (e.g., '12.0').

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Platform compatibility for <platform_name> <platform_version> removed."
                }
            OR
                {
                    "success": False,
                    "error": "Platform compatibility for <platform_name> <platform_version> not found."
                }

        Constraints:
            - Must only remove the specified platform/version.
            - No exceptions raised. Result indicated via return dict.
        """
        key = f"{platform_name}:{platform_version}"
        if key not in self.platform_compatibility:
            return {
                "success": False,
                "error": f"Platform compatibility for {platform_name} {platform_version} not found."
            }
        del self.platform_compatibility[key]
        return {
            "success": True,
            "message": f"Platform compatibility for {platform_name} {platform_version} removed."
        }


class MobileAppConfigManagementSystem(BaseEnv):
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
            if key == "platform_compatibility" and isinstance(value, dict):
                normalized_platform_compatibility = {}
                for raw_key, raw_value in value.items():
                    entry = copy.deepcopy(raw_value)
                    platform_name = None
                    platform_version = None
                    if isinstance(entry, dict):
                        platform_name = entry.get("platform_name")
                        platform_version = entry.get("platform_version")
                    if isinstance(platform_name, str) and isinstance(platform_version, str):
                        normalized_key = f"{platform_name}:{platform_version}"
                    elif isinstance(raw_key, str) and "_" in raw_key:
                        head, tail = raw_key.split("_", 1)
                        normalized_key = f"{head}:{tail}"
                    else:
                        normalized_key = raw_key
                    normalized_platform_compatibility[normalized_key] = entry
                setattr(env, key, normalized_platform_compatibility)
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

    def get_app_configuration(self, **kwargs):
        return self._call_inner_tool('get_app_configuration', kwargs)

    def get_resource_version(self, **kwargs):
        return self._call_inner_tool('get_resource_version', kwargs)

    def list_resource_versions(self, **kwargs):
        return self._call_inner_tool('list_resource_versions', kwargs)

    def get_platform_compatibility(self, **kwargs):
        return self._call_inner_tool('get_platform_compatibility', kwargs)

    def list_platform_compatibility(self, **kwargs):
        return self._call_inner_tool('list_platform_compatibility', kwargs)

    def get_ui_setting(self, **kwargs):
        return self._call_inner_tool('get_ui_setting', kwargs)

    def list_ui_settings(self, **kwargs):
        return self._call_inner_tool('list_ui_settings', kwargs)

    def update_app_configuration(self, **kwargs):
        return self._call_inner_tool('update_app_configuration', kwargs)

    def update_resource_version(self, **kwargs):
        return self._call_inner_tool('update_resource_version', kwargs)

    def update_platform_compatibility(self, **kwargs):
        return self._call_inner_tool('update_platform_compatibility', kwargs)

    def apply_ui_settings_atomically(self, **kwargs):
        return self._call_inner_tool('apply_ui_settings_atomically', kwargs)

    def batch_update_resource_versions(self, **kwargs):
        return self._call_inner_tool('batch_update_resource_versions', kwargs)

    def timestamp_configuration_change(self, **kwargs):
        return self._call_inner_tool('timestamp_configuration_change', kwargs)

    def delete_resource_version(self, **kwargs):
        return self._call_inner_tool('delete_resource_version', kwargs)

    def remove_platform_compatibility(self, **kwargs):
        return self._call_inner_tool('remove_platform_compatibility', kwargs)
