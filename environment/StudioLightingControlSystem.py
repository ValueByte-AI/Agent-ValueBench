# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict, List
import time



class LightingFixtureInfo(TypedDict):
    fixture_id: str
    name: str
    type: str
    assigned_role: str
    intensity: float  # or int; float preferred for lighting precision
    color: str
    status: str  # Note: "sta" is assumed to be a typo for "status"

class PresetInfo(TypedDict):
    preset_id: str
    name: str
    configuration: Dict[str, Any]  # mapping fixture_id to fixture settings

class LightingLogInfo(TypedDict):
    log_id: str
    fixture_id: str
    timestamp: float  # could be datetime, but using float for simplicity
    action: str
    old_value: Any
    new_value: Any  # "new_val" is assumed a typo for "new_value"

class _GeneratedEnvImpl:
    def __init__(self):
        # Fixtures: {fixture_id: LightingFixtureInfo}
        self.fixtures: Dict[str, LightingFixtureInfo] = {}

        # Presets: {preset_id: PresetInfo}
        self.presets: Dict[str, PresetInfo] = {}

        # Lighting logs: {log_id: LightingLogInfo}
        self.lighting_logs: Dict[str, LightingLogInfo] = {}

        # Constraints:
        # - Intensity values must be within allowed fixture range (e.g., 0-100).
        # - Color values must be valid for the fixture type.
        # - Only fixtures with status == "active" can be controlled or adjusted.
        # - Preset recall may override individual fixture settings.

    @staticmethod
    def _is_valid_color_for_fixture_type(fixture_type: str, color: str) -> bool:
        if not isinstance(color, str) or not color.strip():
            return False

        normalized_type = (fixture_type or "").strip().lower()
        normalized_color = color.strip()
        basic_named_colors = {
            "red", "green", "blue", "white", "yellow", "cyan", "magenta",
            "orange", "purple", "pink", "amber", "warm white", "cool white",
        }

        is_hex = re.fullmatch(r"#[0-9a-fA-F]{6}", normalized_color) is not None
        is_kelvin = re.fullmatch(r"\d{4,5}K", normalized_color, flags=re.IGNORECASE) is not None

        if "rgb" in normalized_type:
            return is_hex or normalized_color.lower() in basic_named_colors

        if any(token in normalized_type for token in ("panel", "spot", "white", "mono", "fresnel", "light")):
            return is_kelvin or normalized_color.lower() in {"white", "warm white", "cool white"}

        return is_hex or is_kelvin or normalized_color.lower() in basic_named_colors

    def get_fixture_by_name(self, name: str) -> dict:
        """
        Retrieve a lighting fixture's details by its human-readable name.

        Args:
            name (str): The fixture's human-readable label (e.g., "Key Light").

        Returns:
            dict:
                - success: True and data: LightingFixtureInfo if found.
                - success: False and error message if not found.

        Constraints:
            - Returns the first matching fixture if multiple exist with same name.
            - Name comparison is case-sensitive.
        """
        if not isinstance(name, str) or not name:
            return { "success": False, "error": "Invalid fixture name provided." }

        for fixture in self.fixtures.values():
            if fixture["name"] == name:
                return { "success": True, "data": fixture }

        return { "success": False, "error": "No fixture found with the given name." }

    def get_fixture_by_id(self, fixture_id: str) -> dict:
        """
        Retrieve a lighting fixture's full details by its unique fixture_id.

        Args:
            fixture_id (str): The ID of the fixture to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": LightingFixtureInfo
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - fixture_id must exist within self.fixtures.
        """
        fixture = self.fixtures.get(fixture_id)
        if not fixture:
            return { "success": False, "error": "Fixture not found" }
        return { "success": True, "data": fixture }

    def list_fixtures(self) -> dict:
        """
        Fetch all registered fixtures in the studio lighting system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LightingFixtureInfo]  # List of all fixture info dicts (may be empty)
            }

        Constraints:
            - No constraints: all fixtures are listed regardless of status or other properties.
        """
        fixtures_list = list(self.fixtures.values())
        return {
            "success": True,
            "data": fixtures_list
        }

    def list_fixtures_by_status(self, status: str) -> dict:
        """
        Get all fixtures (with metadata) filtered by their status.

        Args:
            status (str): The status to filter fixtures by (e.g., "active", "inactive").

        Returns:
            dict: {
                "success": True,
                "data": List[LightingFixtureInfo]  # All fixtures with matching status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., invalid argument type)
            }

        Constraints:
            - Status is compared as a string.
        """
        if not isinstance(status, str):
            return { "success": False, "error": "Provided status must be a string" }
        result = [
            fixture for fixture in self.fixtures.values()
            if fixture["status"] == status
        ]
        return { "success": True, "data": result }

    def get_fixture_intensity(self, fixture_id: str) -> dict:
        """
        Query the current intensity setting of a given lighting fixture.

        Args:
            fixture_id (str): Unique identifier for the lighting fixture.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "fixture_id": str,
                            "intensity": float
                        }
                    }
                - On failure (fixture not found):
                    {
                        "success": False,
                        "error": "Fixture not found"
                    }

        Constraints:
            - fixture_id must exist in the system.
            - No status check for querying (even inactive fixtures can be queried).
        """
        fixture = self.fixtures.get(fixture_id)
        if not fixture:
            return {"success": False, "error": "Fixture not found"}
        return {
            "success": True,
            "data": {
                "fixture_id": fixture_id,
                "intensity": fixture["intensity"]
            }
        }

    def get_fixture_color(self, fixture_id: str) -> dict:
        """
        Query the current color setting of a given lighting fixture.

        Args:
            fixture_id (str): Unique identifier of the fixture.

        Returns:
            dict: {
                "success": True,
                "data": str  # Color value (e.g., "3200K", "#FFFFFF", etc.)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., fixture not found
            }

        Constraints:
            - Fixture must exist in the system.
        """
        fixture = self.fixtures.get(fixture_id)
        if fixture is None:
            return { "success": False, "error": "Fixture not found" }
        return { "success": True, "data": fixture["color"] }

    def get_fixture_status(self, fixture_id: str) -> dict:
        """
        Retrieve the current status (e.g., "active", "inactive") of a given lighting fixture.

        Args:
            fixture_id (str): The unique identifier of the fixture to query.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status value of the fixture ("active", "inactive", etc.)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., "Fixture not found"
            }

        Constraints:
            - The fixture must exist in the system (looked up by fixture_id).
            - No restrictions on status for querying; always allowed if fixture is present.
        """
        fixture = self.fixtures.get(fixture_id)
        if fixture is None:
            return { "success": False, "error": "Fixture not found" }

        return { "success": True, "data": fixture["status"] }

    def list_presets(self) -> dict:
        """
        Retrieve all available lighting presets.

        Returns:
            dict: {
                "success": True,
                "data": List[PresetInfo],  # List of all preset info (may be empty if none)
            }
        Constraints:
            - None; all presets are listed regardless of other system state.
        """
        presets_list = list(self.presets.values())
        return { "success": True, "data": presets_list }

    def get_preset_by_name(self, name: str) -> dict:
        """
        Retrieve a preset's configuration by its name.

        Args:
            name (str): The preset name (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": PresetInfo,  # Matching preset info
            }
            OR
            {
                "success": False,
                "error": str  # Reason (e.g., "Preset not found")
            }

        Constraints:
            - Preset name must match exactly (case-sensitive).
            - Returns only the first found if multiple presets by the same name.
        """
        for preset in self.presets.values():
            if preset["name"] == name:
                return { "success": True, "data": preset }
        return { "success": False, "error": "Preset not found" }

    def get_preset_by_id(self, preset_id: str) -> dict:
        """
        Retrieve a preset's complete configuration and info by its preset_id.

        Args:
            preset_id (str): Identifier of the preset to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": PresetInfo  # The matching preset's dictionary
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., not found)
            }
    
        Constraints:
            - The preset must exist (preset_id must be in self.presets).
        """
        preset = self.presets.get(preset_id)
        if preset is None:
            return { "success": False, "error": "Preset not found" }
        return { "success": True, "data": preset }

    def get_lighting_log_by_fixture(self, fixture_id: str) -> dict:
        """
        Fetch all lighting log entries associated with the specified fixture.

        Args:
            fixture_id (str): Unique identifier of the lighting fixture.

        Returns:
            dict: {
                "success": True,
                "data": List[LightingLogInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The fixture with fixture_id must exist.
            - Returns all log entries where log.fixture_id == fixture_id (empty list if none).
        """
        if fixture_id not in self.fixtures:
            return { "success": False, "error": "Fixture does not exist" }
    
        logs = [
            log for log in self.lighting_logs.values()
            if log["fixture_id"] == fixture_id
        ]
        return { "success": True, "data": logs }

    def get_last_fixture_log(self, fixture_id: str) -> dict:
        """
        Retrieve the most recent log entry for a specific fixture.

        Args:
            fixture_id (str): The unique identifier of the lighting fixture.

        Returns:
            dict:
                On success: { "success": True, "data": LightingLogInfo }
                If no logs: { "success": False, "error": "No logs found for this fixture" }
                If fixture does not exist: { "success": False, "error": "Fixture not found" }
        """
        if fixture_id not in self.fixtures:
            return { "success": False, "error": "Fixture not found" }

        logs = [
            log for log in self.lighting_logs.values()
            if log["fixture_id"] == fixture_id
        ]

        if not logs:
            return { "success": False, "error": "No logs found for this fixture" }

        # Get the log with the latest timestamp
        latest_log = max(logs, key=lambda l: l["timestamp"])

        return { "success": True, "data": latest_log }

    def set_fixture_intensity(self, fixture_id: str, intensity: float) -> dict:
        """
        Adjust the intensity of a specified fixture, enforcing allowed range (0-100) and only if status is 'active'.

        Args:
            fixture_id (str): The unique identifier of the lighting fixture.
            intensity (float): Desired intensity value (should be between 0 and 100 inclusive).

        Returns:
            dict: 
                - On success:
                    {"success": True, "message": "Intensity updated for fixture <id> to <intensity>"}
                - On failure:
                    {"success": False, "error": "..."}
    
        Constraints:
            - Intensity must be in [0, 100].
            - Fixture must exist and have status == 'active'.
        """
        # Check if fixture exists
        fixture = self.fixtures.get(fixture_id)
        if not fixture:
            return {"success": False, "error": "Fixture not found"}

        # Check status
        if fixture["status"] != "active":
            return {"success": False, "error": "Fixture is not active"}

        # Coerce intensity to float if possible
        try:
            intensity_value = float(intensity)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid intensity value type"}

        # Range check
        if not (0 <= intensity_value <= 100):
            return {"success": False, "error": "Intensity out of allowed range (0-100)"}

        # Save old value (if logging implemented)
        old_intensity = fixture["intensity"]

        # Update intensity
        fixture["intensity"] = intensity_value

        # Optional: Update self.fixtures - but since dict is mutable, not necessary
        # self.fixtures[fixture_id] = fixture

        # Optionally, log the change here (not required in base operation)

        return {
            "success": True,
            "message": f"Intensity updated for fixture {fixture_id} to {intensity_value}"
        }

    def set_fixture_color(self, fixture_id: str, color: str) -> dict:
        """
        Change the color value of a specified fixture, validating for fixture type and only if the fixture is 'active'.
    
        Args:
            fixture_id (str): The unique identifier of the lighting fixture to adjust.
            color (str): The new color value to set.
        
        Returns:
            dict: Success or error information.
                On success: {
                    "success": True,
                    "message": "Color set to <color> for fixture <fixture_id>"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The fixture must exist.
            - The fixture must be 'active'.
            - The color value must be valid for the fixture type.
        """
        # Check if fixture exists
        fixture = self.fixtures.get(fixture_id)
        if not fixture:
            return {"success": False, "error": f"Fixture '{fixture_id}' does not exist"}

        # Check if fixture is active
        if fixture.get("status") != "active":
            return {"success": False, "error": f"Fixture '{fixture_id}' is not active"}
    
        fixture_type = fixture.get("type")
        if not self._is_valid_color_for_fixture_type(fixture_type, color):
            return {"success": False, "error": f"Color '{color}' is not valid for fixture type '{fixture_type}'"}

        # Change the color
        old_color = fixture["color"]
        fixture["color"] = color

        # Optional: Log this change (if the system supports logging here)
        # (not needed for correctness per operation description)

        return {
            "success": True,
            "message": f"Color set to {color} for fixture {fixture_id}"
        }

    def set_fixture_status(self, fixture_id: str, new_status: str) -> dict:
        """
        Change the operational status of a lighting fixture (e.g., activate or deactivate it).

        Args:
            fixture_id (str): The unique identifier of the fixture.
            new_status (str): The new status to assign (e.g., "active", "inactive").

        Returns:
            dict: 
                Success: { "success": True, "message": "Status of fixture <id> set to <status>" }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The fixture must exist.
            - Allowed statuses are assumed to be "active" and "inactive".
            - No effect if status is already set to new_status (idempotent).
        """
        fixture = self.fixtures.get(fixture_id)
        if fixture is None:
            return { "success": False, "error": f"Fixture with id '{fixture_id}' does not exist." }
    
        allowed_statuses = {"active", "inactive"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Status '{new_status}' is not a supported fixture status." }
    
        old_status = fixture.get("status", None)
        fixture["status"] = new_status

        # (Optional: If logging is desired, a log entry can be made here.)

        return { "success": True, "message": f"Status of fixture '{fixture_id}' set to '{new_status}'." }

    def recall_preset(self, preset_id: str) -> dict:
        """
        Apply all settings from a preset, overriding current individual fixture states as specified.

        Args:
            preset_id (str): The ID of the preset to recall.

        Returns:
            dict: 
              - On full or partial success: {"success": True, "message": "Preset applied (with details)", "skipped": [...], "updated": [...]}
              - On error: {"success": False, "error": str}

        Constraints:
            - Only fixtures with status == "active" can be updated.
            - Intensity must be within 0-100.
            - Color must be valid for that fixture type (if validation implemented).
            - Nonexistent fixtures or invalid setting fixtures are skipped (not treated as hard failure).
            - Each update is logged.
        """
        if preset_id not in self.presets:
            return {"success": False, "error": "Preset does not exist"}

        preset = self.presets[preset_id]
        config = preset["configuration"]

        updated = []
        skipped = []  # List of fixture_ids (or tuple with reason) which were skipped

        for fixture_id, settings in config.items():
            fixture = self.fixtures.get(fixture_id)
            if not fixture:
                skipped.append({"fixture_id": fixture_id, "reason": "Fixture does not exist"})
                continue
            if fixture.get("status") != "active":
                skipped.append({"fixture_id": fixture_id, "reason": "Fixture not active"})
                continue
            fixture_updates = {}
            for attr, value in settings.items():
                # Only known, adjustable attributes should be updated (intensity, color, etc.)
                if attr == "intensity":
                    if not (0 <= value <= 100):
                        skipped.append({
                            "fixture_id": fixture_id,
                            "attribute": "intensity",
                            "reason": "Invalid intensity (must be 0-100)"
                        })
                        continue
                    old_value = fixture["intensity"]
                    fixture["intensity"] = value
                    fixture_updates["intensity"] = (old_value, value)

                    # Log change
                    log_id = f"log_{fixture_id}_{int(time.time()*1000)}_intensity"
                    self.lighting_logs[log_id] = {
                        "log_id": log_id,
                        "fixture_id": fixture_id,
                        "timestamp": time.time(),
                        "action": "recall_preset_update_intensity",
                        "old_value": old_value,
                        "new_value": value
                    }
                elif attr == "color":
                    if not self._is_valid_color_for_fixture_type(fixture.get("type"), value):
                        skipped.append({
                            "fixture_id": fixture_id,
                            "attribute": "color",
                            "reason": f"Invalid color '{value}' for fixture type '{fixture.get('type')}'"
                        })
                        continue
                    old_value = fixture["color"]
                    fixture["color"] = value
                    fixture_updates["color"] = (old_value, value)

                    log_id = f"log_{fixture_id}_{int(time.time()*1000)}_color"
                    self.lighting_logs[log_id] = {
                        "log_id": log_id,
                        "fixture_id": fixture_id,
                        "timestamp": time.time(),
                        "action": "recall_preset_update_color",
                        "old_value": old_value,
                        "new_value": value
                    }
                # Optionally handle other updatable attributes here (e.g. assigned_role, etc.)
            if fixture_updates:
                updated.append({"fixture_id": fixture_id, "updates": fixture_updates})
            elif not any(s["fixture_id"] == fixture_id for s in skipped):
                skipped.append({"fixture_id": fixture_id, "reason": "No valid attributes to update"})

        msg_details = f"{len(updated)} fixtures updated"
        if skipped:
            msg_details += f", {len(skipped)} fixtures skipped"
        return {
            "success": True,
            "message": f"Preset '{preset['name']}' applied: {msg_details}",
            "updated": updated,
            "skipped": skipped
        }

    def log_fixture_change(
        self,
        fixture_id: str,
        action: str,
        old_value: Any,
        new_value: Any,
        timestamp: float
    ) -> dict:
        """
        Record a manual change to a fixture's setting in the lighting log for audit/reproducibility.

        Args:
            fixture_id (str): Unique identifier of the lighting fixture being changed.
            action (str): Description of the change/action (e.g., "set_intensity").
            old_value (Any): Value before change.
            new_value (Any): Value after change.
            timestamp (float): Unix timestamp of the change.

        Returns:
            dict:
                On success: { "success": True, "message": "Logged fixture change for fixture fixture_id." }
                On failure: { "success": False, "error": "Fixture not found." }

        Constraints:
            - The fixture_id must correspond to an existing fixture.
            - Logging changes is allowed regardless of fixture status.
        """
        if fixture_id not in self.fixtures:
            return { "success": False, "error": "Fixture not found." }
    
        # Generate unique log_id; use fixture_id + timestamp for uniqueness
        log_id = f"{fixture_id}_{timestamp}"
        log_entry: LightingLogInfo = {
            "log_id": log_id,
            "fixture_id": fixture_id,
            "timestamp": timestamp,
            "action": action,
            "old_value": old_value,
            "new_value": new_value
        }
        self.lighting_logs[log_id] = log_entry

        return {
            "success": True,
            "message": f"Logged fixture change for fixture {fixture_id}."
        }

    def batch_update_fixtures(
        self, 
        fixture_ids: List[str], 
        updates: Dict[str, Any]
    ) -> dict:
        """
        Apply updates (e.g., intensity, color) to multiple fixtures at once, enforcing all relevant constraints.

        Args:
            fixture_ids (List[str]): List of fixture IDs to update.
            updates (Dict[str, Any]): Dict of properties to update (e.g., {"intensity": 80, "color": "blue"}).

        Returns:
            dict: {
                "success": True,
                "message": "Batch update applied to fixtures: [...]"
            } on success,
            or
            {
                "success": False,
                "error": str  # explanation of failures
            } on error.

        Constraints enforced:
            - Only fixtures with status == "active" are updated.
            - Intensity must be in [0, 100].
            - Color must be valid for fixture type (here, checks nonempty/non-None).
            - If any fixture fails constraints or is not found, abort batch (atomic).
        """
        failed_fixtures = []
        allowed_intensity_min, allowed_intensity_max = 0, 100

        # Pre-validation
        for fid in fixture_ids:
            fixture = self.fixtures.get(fid)
            if fixture is None:
                failed_fixtures.append(f"{fid}: not found")
                continue
            if fixture["status"] != "active":
                failed_fixtures.append(f"{fid}: inactive")
                continue
            if "intensity" in updates:
                intensity = updates["intensity"]
                if not (isinstance(intensity, (int, float)) and allowed_intensity_min <= intensity <= allowed_intensity_max):
                    failed_fixtures.append(f"{fid}: intensity out of range (0-100)")
            if "color" in updates:
                color = updates["color"]
                if not self._is_valid_color_for_fixture_type(fixture["type"], color):
                    failed_fixtures.append(f"{fid}: invalid color '{color}' for type '{fixture['type']}'")

        if failed_fixtures:
            return {
                "success": False,
                "error": f"Batch update failed for fixtures: {', '.join(failed_fixtures)}"
            }

        # If all OK, proceed with updates
        for fid in fixture_ids:
            fixture = self.fixtures[fid]
            if "intensity" in updates:
                fixture["intensity"] = updates["intensity"]
            if "color" in updates:
                fixture["color"] = updates["color"]
            # More fields could be added; handles only 'intensity' and 'color' as typical

        return {
            "success": True,
            "message": f"Batch update applied to fixtures: {fixture_ids}"
        }


class StudioLightingControlSystem(BaseEnv):
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

    def get_fixture_by_name(self, **kwargs):
        return self._call_inner_tool('get_fixture_by_name', kwargs)

    def get_fixture_by_id(self, **kwargs):
        return self._call_inner_tool('get_fixture_by_id', kwargs)

    def list_fixtures(self, **kwargs):
        return self._call_inner_tool('list_fixtures', kwargs)

    def list_fixtures_by_status(self, **kwargs):
        return self._call_inner_tool('list_fixtures_by_status', kwargs)

    def get_fixture_intensity(self, **kwargs):
        return self._call_inner_tool('get_fixture_intensity', kwargs)

    def get_fixture_color(self, **kwargs):
        return self._call_inner_tool('get_fixture_color', kwargs)

    def get_fixture_status(self, **kwargs):
        return self._call_inner_tool('get_fixture_status', kwargs)

    def list_presets(self, **kwargs):
        return self._call_inner_tool('list_presets', kwargs)

    def get_preset_by_name(self, **kwargs):
        return self._call_inner_tool('get_preset_by_name', kwargs)

    def get_preset_by_id(self, **kwargs):
        return self._call_inner_tool('get_preset_by_id', kwargs)

    def get_lighting_log_by_fixture(self, **kwargs):
        return self._call_inner_tool('get_lighting_log_by_fixture', kwargs)

    def get_last_fixture_log(self, **kwargs):
        return self._call_inner_tool('get_last_fixture_log', kwargs)

    def set_fixture_intensity(self, **kwargs):
        return self._call_inner_tool('set_fixture_intensity', kwargs)

    def set_fixture_color(self, **kwargs):
        return self._call_inner_tool('set_fixture_color', kwargs)

    def set_fixture_status(self, **kwargs):
        return self._call_inner_tool('set_fixture_status', kwargs)

    def recall_preset(self, **kwargs):
        return self._call_inner_tool('recall_preset', kwargs)

    def log_fixture_change(self, **kwargs):
        return self._call_inner_tool('log_fixture_change', kwargs)

    def batch_update_fixtures(self, **kwargs):
        return self._call_inner_tool('batch_update_fixtures', kwargs)
