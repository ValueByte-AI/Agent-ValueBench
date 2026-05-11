# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class PositionInfo(TypedDict):
    latitude: float
    longitude: float
    altitude: float

class AircraftInfo(TypedDict):
    aircraft_id: str
    position: PositionInfo
    speed: float
    heading: float
    status: str
    last_update_time: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for tracking aircraft telemetry and state in real-time.
        """

        # Aircraft registry: {aircraft_id: AircraftInfo}
        # Maps each unique aircraft_id to telemetry/status for tracked aircraft.
        self.aircraft: Dict[str, AircraftInfo] = {}

        # Constraints, reminders:
        # - Each aircraft must have a unique aircraft_id.
        # - Telemetry data (position, speed, heading) must be regularly updated.
        # - Aircraft with outdated/missing updates may need to be flagged/removed.
        # - Only aircraft within the defined airspace/area of interest are tracked.

    def get_aircraft_by_id(self, aircraft_id: str) -> dict:
        """
        Retrieve full telemetry and status information for a specific aircraft.

        Args:
            aircraft_id (str): The unique identifier of the aircraft to retrieve.

        Returns:
            dict:
                {
                    "success": True,
                    "data": AircraftInfo
                }
                or
                {
                    "success": False,
                    "error": "Aircraft not found"
                }

        Constraints:
            - The given aircraft_id must exist in the tracking registry.
        """
        if not aircraft_id or aircraft_id not in self.aircraft:
            return { "success": False, "error": "Aircraft not found" }

        return { "success": True, "data": self.aircraft[aircraft_id] }

    def get_aircraft_speed(self, aircraft_id: str) -> dict:
        """
        Retrieve the current speed of the specified aircraft.

        Args:
            aircraft_id (str): The unique identifier for the aircraft.

        Returns:
            dict:
                - On success: { "success": True, "data": float }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Aircraft with the given aircraft_id must exist in the registry.
        """
        aircraft = self.aircraft.get(aircraft_id)
        if not aircraft:
            return { "success": False, "error": "Aircraft not found" }

        return { "success": True, "data": aircraft["speed"] }

    def get_aircraft_heading(self, aircraft_id: str) -> dict:
        """
        Get the current heading (direction, in degrees) of the specified aircraft.

        Args:
            aircraft_id (str): The unique identifier of the aircraft.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": float  # heading value
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Explanation, e.g. "Aircraft not found"
                    }

        Constraints:
            - Aircraft must exist in the tracking system (by aircraft_id).
        """
        if aircraft_id not in self.aircraft:
            return { "success": False, "error": "Aircraft not found" }

        heading = self.aircraft[aircraft_id]['heading']
        return { "success": True, "data": heading }

    def get_aircraft_position(self, aircraft_id: str) -> dict:
        """
        Retrieve the current position (latitude, longitude, altitude) for a specified aircraft.

        Args:
            aircraft_id (str): Unique identifier of the aircraft.

        Returns:
            dict: {
                "success": True,
                "data": PositionInfo,  # Current position info for the aircraft
            }
            or
            {
                "success": False,
                "error": str  # Error reason, e.g. "Aircraft does not exist"
            }

        Constraints:
            - Aircraft with the given aircraft_id must exist in the tracking registry.
        """
        aircraft = self.aircraft.get(aircraft_id)
        if not aircraft:
            return {"success": False, "error": "Aircraft does not exist"}
        return {"success": True, "data": aircraft["position"]}

    def get_aircraft_status(self, aircraft_id: str) -> dict:
        """
        Query the current status (e.g., active, inactive, flagged) of the specified aircraft.

        Args:
            aircraft_id (str): The unique identifier for the aircraft.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status of the aircraft (e.g. "active")
            }
            or
            {
                "success": False,
                "error": str  # Error message if aircraft is not found
            }

        Constraints:
            - aircraft_id must exist in the tracked aircraft registry.
        """
        aircraft = self.aircraft.get(aircraft_id)
        if not aircraft:
            return { "success": False, "error": "Aircraft not found" }
        return { "success": True, "data": aircraft["status"] }

    def list_all_tracked_aircraft(self) -> dict:
        """
        List all aircraft currently tracked in the system.

        Returns:
            dict
                success: True if operation succeeded, False if not applicable (should not occur).
                data: List[AircraftInfo] -- a list of all tracked aircraft (may be empty if none).

        Constraints:
            - No parameters required.
            - Does not filter by staleness or status; just reports all current registry entries.
        """
        aircraft_list = list(self.aircraft.values())
        return { "success": True, "data": aircraft_list }

    def check_aircraft_last_update(self, aircraft_id: str) -> dict:
        """
        Get the timestamp of the last telemetry update for a specified aircraft.

        Args:
            aircraft_id (str): Unique identifier for the aircraft.

        Returns:
            dict:
                - On success: { "success": True, "data": last_update_time (float) }
                - On error: { "success": False, "error": "Aircraft not found" }

        Constraints:
            - The specified aircraft_id must exist in the registry.
        """
        aircraft = self.aircraft.get(aircraft_id)
        if not aircraft:
            return { "success": False, "error": "Aircraft not found" }
        return { "success": True, "data": aircraft["last_update_time"] }

    def find_stale_aircraft(self, current_time: float, stale_threshold: float) -> dict:
        """
        Identify all aircraft whose last telemetry update is older than the provided threshold.

        Args:
            current_time (float): The reference/current time as a UNIX timestamp.
            stale_threshold (float): The staleness threshold in seconds.

        Returns:
            dict: {
                "success": True,
                "data": List[AircraftInfo]  # All aircraft with last_update_time < (current_time - stale_threshold)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - stale_threshold must be > 0.
        """
        if stale_threshold <= 0:
            return {
                "success": False,
                "error": "Stale threshold must be greater than zero."
            }
        if not isinstance(current_time, (float, int)):
            return {
                "success": False,
                "error": "Invalid current_time parameter."
            }

        cutoff_time = current_time - stale_threshold
        stale_aircraft = [
            aircraft_info for aircraft_info in self.aircraft.values()
            if aircraft_info["last_update_time"] < cutoff_time
        ]
        return {
            "success": True,
            "data": stale_aircraft
        }

    def verify_airspace_compliance(self, aircraft_id: str) -> dict:
        """
        Check if a specified aircraft's position is within the defined airspace or area of interest.

        Args:
            aircraft_id (str): Unique identifier for the aircraft to check.

        Returns:
            dict: 
                - If success:
                    {
                        "success": True,
                        "data": {
                            "in_airspace": bool,           # True if within boundaries
                            "position": PositionInfo       # Position of the aircraft
                        }
                    }
                - If failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Aircraft must exist in the registry.
            - Airspace boundaries (lat/lon/alt min/max) must be defined as class attributes.

        """
        if aircraft_id not in self.aircraft:
            return {"success": False, "error": "Aircraft not found"}

        # Ensure airspace boundaries are set in the class
        boundary_attrs = [
            "airspace_lat_min", "airspace_lat_max",
            "airspace_lon_min", "airspace_lon_max",
            "airspace_alt_min", "airspace_alt_max",
        ]
        for attr in boundary_attrs:
            if not hasattr(self, attr):
                return {"success": False, "error": f"Airspace boundary '{attr}' not defined"}

        info = self.aircraft[aircraft_id]
        pos = info.get("position", {})
        lat = pos.get("latitude")
        lon = pos.get("longitude")
        alt = pos.get("altitude")

        if lat is None or lon is None or alt is None:
            return {"success": False, "error": "Incomplete position information for aircraft"}

        try:
            lat_min = float(self.airspace_lat_min)
            lat_max = float(self.airspace_lat_max)
            lon_min = float(self.airspace_lon_min)
            lon_max = float(self.airspace_lon_max)
            alt_min = float(self.airspace_alt_min)
            alt_max = float(self.airspace_alt_max)
        except (TypeError, ValueError):
            return {"success": False, "error": "Invalid airspace boundary values"}

        in_lat = lat_min <= lat <= lat_max
        in_lon = lon_min <= lon <= lon_max
        in_alt = alt_min <= alt <= alt_max

        return {
            "success": True,
            "data": {
                "in_airspace": in_lat and in_lon and in_alt,
                "position": pos
            }
        }

    def update_aircraft_telemetry(
        self, 
        aircraft_id: str, 
        position: dict, 
        speed: float, 
        heading: float, 
        last_update_time: float
    ) -> dict:
        """
        Update the position, speed, heading, and last_update_time of a tracked aircraft.

        Args:
            aircraft_id (str): Unique identifier of the aircraft.
            position (dict): Position info with keys 'latitude', 'longitude', 'altitude' (all floats).
            speed (float): Aircraft speed.
            heading (float): Aircraft heading (degrees).
            last_update_time (float): Timestamp of telemetry update (UNIX time).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Telemetry updated for aircraft <aircraft_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason string>
                    }

        Constraints:
            - The aircraft must be actively tracked.
            - All position fields must be provided and valid.
            - Negative values for altitude/speed are not accepted.
        """
        # Check aircraft is tracked
        if aircraft_id not in self.aircraft:
            return { "success": False, "error": "Aircraft ID not tracked" }
    
        # Validate position
        required_keys = {"latitude", "longitude", "altitude"}
        if not isinstance(position, dict) or not required_keys.issubset(position.keys()):
            return { "success": False, "error": "Missing position fields (latitude, longitude, altitude)" }
        try:
            lat = float(position["latitude"])
            lon = float(position["longitude"])
            alt = float(position["altitude"])
            if alt < 0:
                return { "success": False, "error": "Altitude cannot be negative" }
        except (TypeError, ValueError):
            return { "success": False, "error": "Invalid position field types" }

        # Validate speed and heading
        try:
            speed = float(speed)
            heading = float(heading)
            if speed < 0:
                return { "success": False, "error": "Speed cannot be negative" }
        except (TypeError, ValueError):
            return { "success": False, "error": "Invalid speed or heading type" }

        try:
            last_update_time = float(last_update_time)
        except (TypeError, ValueError):
            return { "success": False, "error": "Invalid last_update_time type" }

        # Perform the update
        info = self.aircraft[aircraft_id]
        info["position"] = {
            "latitude": lat,
            "longitude": lon,
            "altitude": alt
        }
        info["speed"] = speed
        info["heading"] = heading
        info["last_update_time"] = last_update_time

        return { "success": True, "message": f"Telemetry updated for aircraft {aircraft_id}" }

    def add_aircraft(
        self,
        aircraft_id: str,
        position: dict,
        speed: float,
        heading: float,
        status: str,
        last_update_time: float
    ) -> dict:
        """
        Register a new aircraft into the tracking system with a unique aircraft_id.

        Args:
            aircraft_id (str): Unique identifier for the aircraft.
            position (dict): Dictionary with keys 'latitude', 'longitude', 'altitude' (floats).
            speed (float): Aircraft speed.
            heading (float): Aircraft heading.
            status (str): Status string.
            last_update_time (float): Unix timestamp of last update.

        Returns:
            dict: {
                "success": True,
                "message": "Aircraft <id> added."
            } or {
                "success": False,
                "error": "<error_message>"
            }

        Constraints:
            - aircraft_id must be unique in the system.
            - position dict must contain valid latitude, longitude, altitude.
        """
        # Check aircraft_id uniqueness
        if aircraft_id in self.aircraft:
            return {"success": False, "error": "Aircraft ID already exists."}

        # Validate position
        required_pos_keys = {"latitude", "longitude", "altitude"}
        if not isinstance(position, dict) or not required_pos_keys.issubset(position.keys()):
            return {"success": False, "error": "Position must include latitude, longitude, and altitude."}
        try:
            lat = float(position["latitude"])
            lon = float(position["longitude"])
            alt = float(position["altitude"])
        except (ValueError, TypeError):
            return {"success": False, "error": "Position values must be floats."}

        # Assemble AircraftInfo
        aircraft_info: AircraftInfo = {
            "aircraft_id": aircraft_id,
            "position": {
                "latitude": lat,
                "longitude": lon,
                "altitude": alt
            },
            "speed": float(speed),
            "heading": float(heading),
            "status": str(status),
            "last_update_time": float(last_update_time)
        }
        self.aircraft[aircraft_id] = aircraft_info
        return {"success": True, "message": f"Aircraft {aircraft_id} added."}


    def flag_stale_aircraft(self, stale_threshold: float = 300.0, current_time: float = None) -> dict:
        """
        Mark aircraft with outdated telemetry as 'flagged' in their status field.

        Args:
            stale_threshold (float): Number of seconds since last update after which an aircraft is considered stale.
                                    Default is 300 seconds (5 minutes).
            current_time (float, optional): Reference/current time as a UNIX timestamp. If omitted, the
                                    tool uses the latest last_update_time currently present in the registry
                                    as a deterministic virtual reference time.

        Returns:
            dict: 
                - { "success": True, "message": "<N> aircraft flagged as stale." }
                  On success, N is the number of aircraft whose status was updated to 'flagged'.
        Constraints:
            - Only aircraft with (current_time - last_update_time) > stale_threshold are flagged.
            - Updates the 'status' key to the string "flagged".
            - No error is thrown if no aircraft are found or all are non-stale.
        """
        if stale_threshold <= 0:
            return {
                "success": False,
                "error": "Stale threshold must be greater than zero."
            }
        if current_time is None:
            if not self.aircraft:
                return {"success": True, "message": "0 aircraft flagged as stale."}
            current_time = max(ac["last_update_time"] for ac in self.aircraft.values())
        try:
            current_time = float(current_time)
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "Invalid current_time parameter."
            }
        num_flagged = 0

        for ac in self.aircraft.values():
            if (current_time - ac["last_update_time"]) > stale_threshold:
                if ac["status"] != "flagged":
                    ac["status"] = "flagged"
                    num_flagged += 1

        return {
            "success": True,
            "message": f"{num_flagged} aircraft flagged as stale."
        }

    def remove_aircraft(self, aircraft_id: str) -> dict:
        """
        Remove a specified aircraft from tracking by its aircraft_id.

        Args:
            aircraft_id (str): Unique identifier of the aircraft to remove.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "message": "Aircraft <aircraft_id> removed from tracking"
                  }
                - On failure: {
                      "success": False,
                      "error": "Aircraft not found"
                  }

        Constraints:
            - The aircraft to be removed must exist in the system.
        """
        if aircraft_id not in self.aircraft:
            return { "success": False, "error": "Aircraft not found" }
        del self.aircraft[aircraft_id]
        return { "success": True, "message": f"Aircraft {aircraft_id} removed from tracking" }


    def update_aircraft_status(self, aircraft_id: str, new_status: str) -> dict:
        """
        Update the status of a specific aircraft in the tracking system.

        Args:
            aircraft_id (str): Unique identifier of the aircraft whose status will be updated.
            new_status (str): New status string (e.g., 'active', 'inactive', 'flagged', 'removed').

        Returns:
            dict:
                - {"success": True, "message": "Aircraft status updated"} on success
                - {"success": False, "error": <reason>} if aircraft not found or invalid input

        Constraints:
            - Aircraft must exist in the tracking registry.
            - Status can be set to any string (unless restricted further in system).
        """

        if not aircraft_id or aircraft_id not in self.aircraft:
            return { "success": False, "error": "Aircraft not found" }
    
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid new status" }

        self.aircraft[aircraft_id]["status"] = new_status
        return { "success": True, "message": f"Aircraft {aircraft_id} status updated to '{new_status}'" }


class AircraftTrackingSystem(BaseEnv):
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

    def get_aircraft_by_id(self, **kwargs):
        return self._call_inner_tool('get_aircraft_by_id', kwargs)

    def get_aircraft_speed(self, **kwargs):
        return self._call_inner_tool('get_aircraft_speed', kwargs)

    def get_aircraft_heading(self, **kwargs):
        return self._call_inner_tool('get_aircraft_heading', kwargs)

    def get_aircraft_position(self, **kwargs):
        return self._call_inner_tool('get_aircraft_position', kwargs)

    def get_aircraft_status(self, **kwargs):
        return self._call_inner_tool('get_aircraft_status', kwargs)

    def list_all_tracked_aircraft(self, **kwargs):
        return self._call_inner_tool('list_all_tracked_aircraft', kwargs)

    def check_aircraft_last_update(self, **kwargs):
        return self._call_inner_tool('check_aircraft_last_update', kwargs)

    def find_stale_aircraft(self, **kwargs):
        return self._call_inner_tool('find_stale_aircraft', kwargs)

    def verify_airspace_compliance(self, **kwargs):
        return self._call_inner_tool('verify_airspace_compliance', kwargs)

    def update_aircraft_telemetry(self, **kwargs):
        return self._call_inner_tool('update_aircraft_telemetry', kwargs)

    def add_aircraft(self, **kwargs):
        return self._call_inner_tool('add_aircraft', kwargs)

    def flag_stale_aircraft(self, **kwargs):
        return self._call_inner_tool('flag_stale_aircraft', kwargs)

    def remove_aircraft(self, **kwargs):
        return self._call_inner_tool('remove_aircraft', kwargs)

    def update_aircraft_status(self, **kwargs):
        return self._call_inner_tool('update_aircraft_status', kwargs)
