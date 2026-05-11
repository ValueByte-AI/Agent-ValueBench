# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



class LocationInfo(TypedDict):
    location_id: str
    name: str
    alternate_names: List[str]
    latitude: float
    longitude: float
    type: str
    bounding_box: Optional[List[float]]  # e.g., [min_lat, min_lon, max_lat, max_lon] or None

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Geospatial location database.
        Manages geo-entities indexed by unique location_id.
        """

        # Locations: {location_id: LocationInfo}
        self.locations: Dict[str, LocationInfo] = {}

        # Constraints:
        # - Each location must have a unique location_id.
        # - Each location must have at least one set of coordinates (latitude and longitude).
        # - Names (including alternate_names) may not be unique; searches may return multiple locations.
        # - Coordinates should fall within valid geographical bounds (latitude: -90 to 90, longitude: -180 to 180).

    def search_locations_by_name(self, search_string: str) -> dict:
        """
        Retrieve all locations whose 'name' or an element of 'alternate_names' matches the provided search string.

        Args:
            search_string (str): Name to search. Case-insensitive. Must fully match either the main name or any alternate.

        Returns:
            dict:
                - success (bool): True if query was performed.
                - data (List[LocationInfo]): List of matching LocationInfo objects (empty if none match).
        Notes:
            - Matching is case-insensitive.
            - No partial/fuzzy/substring matching; only full equality.
        """
        search_string_lower = search_string.lower()
        result = []
        for location in self.locations.values():
            # Check main name
            if location["name"].lower() == search_string_lower:
                result.append(location)
                continue
            # Check alternate names
            if any(alt_name.lower() == search_string_lower for alt_name in location.get("alternate_names", [])):
                result.append(location)
        return {"success": True, "data": result}

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve a specific location's complete info using its unique location_id.

        Args:
            location_id (str): The unique identifier for the requested location.

        Returns:
            dict: {
                "success": True,
                "data": LocationInfo,  # The full info dict for the found location
            }
            or
            {
                "success": False,
                "error": str  # "Location not found"
            }

        Constraints:
            - location_id must exist in the locations dictionary.
        """
        location = self.locations.get(location_id)
        if location is None:
            return {"success": False, "error": "Location not found"}
        return {"success": True, "data": location}

    def get_coordinates_by_location_id(self, location_id: str) -> dict:
        """
        Obtain the latitude and longitude for the specified location_id.

        Args:
            location_id (str): The unique ID of the location.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "latitude": float,
                    "longitude": float
                }
            }
            or
            {
                "success": False,
                "error": str  # Location not found or missing coordinates
            }

        Constraints:
            - The specified location_id must exist in the database.
            - All locations are guaranteed to have valid coordinates per database constraints.
        """
        loc = self.locations.get(location_id)
        if loc is None:
            return { "success": False, "error": "Location not found" }

        # Defensive: But per constraints, these should always exist
        latitude = loc.get("latitude")
        longitude = loc.get("longitude")
        if latitude is None or longitude is None:
            return { "success": False, "error": "Coordinates missing for location." }
    
        return {
            "success": True,
            "data": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

    def filter_locations_by_type(self, location_type: str) -> dict:
        """
        Retrieve all locations of a given type (e.g., city, park, building).

        Args:
            location_type (str): The location type to filter by (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # All matching locations (may be empty)
            }

        Notes:
            - This operation is case-insensitive on the location type.
            - If no locations match, returns success with an empty list.
        """
        location_type_lc = location_type.strip().lower()
        matches = [
            loc for loc in self.locations.values()
            if loc.get("type", "").strip().lower() == location_type_lc
        ]
        return { "success": True, "data": matches }

    def search_locations_in_bounding_box(self, bounding_box: list) -> dict:
        """
        Retrieve all locations whose coordinates (or bounding box, if defined) intersect or are contained within 
        the specified bounding box.

        Args:
            bounding_box (list of float): [min_lat, min_lon, max_lat, max_lon], 
                where lat ∈ [-90, 90], lon ∈ [-180, 180].

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo],  # Matching locations (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. invalid bounding box
            }

        Constraints:
            - bounding_box must be valid (length=4, correct order, within latitude/longitude bounds).
        """

        # Validate bounding_box argument
        if (
            not isinstance(bounding_box, (list, tuple))
            or len(bounding_box) != 4
        ):
            return { "success": False, "error": "Invalid bounding box: must be a list of four numbers [min_lat, min_lon, max_lat, max_lon]" }

        min_lat, min_lon, max_lat, max_lon = bounding_box

        # Validate range and order
        if not (
            isinstance(min_lat, (int, float)) and
            isinstance(min_lon, (int, float)) and
            isinstance(max_lat, (int, float)) and
            isinstance(max_lon, (int, float))
        ):
            return { "success": False, "error": "Invalid bounding box: elements must be numbers" }
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90 and -180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            return { "success": False, "error": "Invalid bounding box: coordinates out of range" }
        if min_lat > max_lat or min_lon > max_lon:
            return { "success": False, "error": "Invalid bounding box: min values must be <= max values" }
    
        def bbox_intersects(bb1, bb2):
            # Returns True if two bounding boxes intersect
            min_lat1, min_lon1, max_lat1, max_lon1 = bb1
            min_lat2, min_lon2, max_lat2, max_lon2 = bb2
            return not (max_lat1 < min_lat2 or min_lat1 > max_lat2 or max_lon1 < min_lon2 or min_lon1 > max_lon2)

        matches = []
        for loc in self.locations.values():
            loc_bbox = loc.get("bounding_box")
            if loc_bbox:
                # Intersection test for bounding boxes
                if bbox_intersects(bounding_box, loc_bbox):
                    matches.append(loc)
            else:
                # Point-in-bounding-box test
                lat = loc["latitude"]
                lon = loc["longitude"]
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    matches.append(loc)

        return { "success": True, "data": matches }

    def list_all_locations(self) -> dict:
        """
        List all registered location entities in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # May be empty if no locations registered
            }
        Constraints:
            - No constraints are checked; all locations currently present are returned.
        """
        all_locations = list(self.locations.values())
        return { "success": True, "data": all_locations }

    def validate_location_coordinates(self, location_id: str) -> dict:
        """
        Check if the specified location's coordinates fall within valid geographical bounds.
    
        Args:
            location_id (str): The unique identifier of the location to validate.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": {
                        "valid": bool,    # True if coordinates are within valid bounds, else False
                        "latitude": float,
                        "longitude": float
                    }
                }
                or
                {
                    "success": False,
                    "error": str  # Error message, e.g., location not found
                }

        Constraints:
            - Latitude must be between -90 and 90.
            - Longitude must be between -180 and 180.
            - location_id must exist.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }

        loc = self.locations[location_id]
        latitude = loc.get("latitude")
        longitude = loc.get("longitude")

        # Defensive: check if values are not None and are float/int
        if latitude is None or longitude is None:
            return {
                "success": False,
                "error": "Location does not have valid latitude and longitude"
            }

        valid = (-90 <= latitude <= 90) and (-180 <= longitude <= 180)

        return {
            "success": True,
            "data": {
                "valid": valid,
                "latitude": latitude,
                "longitude": longitude
            }
        }

    def add_location(
        self,
        location_id: str,
        name: str,
        alternate_names: List[str],
        latitude: float,
        longitude: float,
        type: str,
        bounding_box: Optional[List[float]] = None,
    ) -> dict:
        """
        Add a new location entity to the geospatial location database.

        Args:
            location_id (str): Unique identifier for the location.
            name (str): Main name for the location.
            alternate_names (List[str]): Alternate/variant names.
            latitude (float): Latitude of the location (-90 <= latitude <= 90).
            longitude (float): Longitude of the location (-180 <= longitude <= 180).
            type (str): Type/category (e.g., city, park, building).
            bounding_box (Optional[List[float]]): Optional bounding box [min_lat, min_lon, max_lat, max_lon].

        Returns:
            dict:
                On success: { "success": True, "message": "Location added successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - location_id must be unique.
            - latitude in [-90, 90], longitude in [-180, 180].
            - bounding_box, if provided, must have 4 floats (min_lat, min_lon, max_lat, max_lon)
              in valid ranges and min < max for lat and lon.
        """
        # Check for unique location_id
        if location_id in self.locations:
            return { "success": False, "error": "Location ID already exists" }
    
        # Check that latitude and longitude are within bounds
        if not (-90.0 <= latitude <= 90.0):
            return { "success": False, "error": "Latitude must be between -90 and 90" }
        if not (-180.0 <= longitude <= 180.0):
            return { "success": False, "error": "Longitude must be between -180 and 180" }
    
        # Check required fields
        if not name or not type:
            return { "success": False, "error": "Missing required fields: name and type are required" }
        if alternate_names is None:
            alternate_names = []

        # Validate bounding_box if provided
        if bounding_box is not None:
            if (
                not isinstance(bounding_box, list)
                or len(bounding_box) != 4
                or not all(isinstance(x, (int, float)) for x in bounding_box)
            ):
                return { "success": False, "error": "Invalid bounding_box: must be a list of 4 numbers" }
            min_lat, min_lon, max_lat, max_lon = bounding_box
            if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
                return { "success": False, "error": "Bounding box latitude values must be between -90 and 90" }
            if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
                return { "success": False, "error": "Bounding box longitude values must be between -180 and 180" }
            if min_lat > max_lat or min_lon > max_lon:
                return { "success": False, "error": "Bounding box min values must be <= max values" }

        new_location: LocationInfo = {
            "location_id": location_id,
            "name": name,
            "alternate_names": list(alternate_names),
            "latitude": latitude,
            "longitude": longitude,
            "type": type,
            "bounding_box": bounding_box,
        }
        self.locations[location_id] = new_location

        return { "success": True, "message": "Location added successfully" }

    def update_location_info(self, location_id: str, updates: dict) -> dict:
        """
        Update any attribute(s) for a given location while enforcing coordinate and uniqueness constraints.

        Args:
            location_id (str): The ID of the location to update.
            updates (dict): Dictionary of attribute names and their new values.
                Allowed keys: name (str), alternate_names (List[str]), latitude (float),
                             longitude (float), type (str), bounding_box (Optional[List[float]])
                Changing location_id is NOT supported (use a new add/remove operation).

        Returns:
            dict: {
                "success": True,
                "message": "Location updated successfully."
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - location_id must exist.
            - latitude (if present) must be in [-90, 90].
            - longitude (if present) must be in [-180, 180].
            - location_id is unique and cannot be changed by this operation.
        """
        # Check if location_id exists
        if location_id not in self.locations:
            return {"success": False, "error": "Location ID does not exist"}

        allowed_fields = {"name", "alternate_names", "latitude", "longitude", "type", "bounding_box"}
        for key in updates.keys():
            if key not in allowed_fields:
                return {"success": False, "error": f"Field '{key}' cannot be updated or is invalid."}

        # Validate coordinates if included
        if "latitude" in updates:
            lat = updates["latitude"]
            if not isinstance(lat, (float, int)) or not (-90 <= lat <= 90):
                return {"success": False, "error": "Latitude must be between -90 and 90."}
        if "longitude" in updates:
            lon = updates["longitude"]
            if not isinstance(lon, (float, int)) or not (-180 <= lon <= 180):
                return {"success": False, "error": "Longitude must be between -180 and 180."}

        # Validate alternate_names if present
        if "alternate_names" in updates:
            if not isinstance(updates["alternate_names"], list) or not all(isinstance(n, str) for n in updates["alternate_names"]):
                return {"success": False, "error": "alternate_names must be a list of strings."}

        # Validate bounding_box if present
        if "bounding_box" in updates:
            bb = updates["bounding_box"]
            if bb is not None:
                if (not isinstance(bb, list)) or (len(bb) != 4) or \
                   (not all(isinstance(f, (float, int)) for f in bb)):
                    return {"success": False, "error": "bounding_box must be None or a list of four floats [min_lat, min_lon, max_lat, max_lon]."}

                # Optionally, validate bounding coordinates (optional, but sensible)
                min_lat, min_lon, max_lat, max_lon = bb
                if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90 and -180 <= min_lon <= 180 and -180 <= max_lon <= 180):
                    return {"success": False, "error": "Bounding box coordinates out of bounds."}

        # All checks passed, perform updates atomically
        for key, value in updates.items():
            self.locations[location_id][key] = value

        return {"success": True, "message": "Location updated successfully."}

    def add_alternate_name_to_location(self, location_id: str, alternate_name: str) -> dict:
        """
        Add a new alternate name to a location's alternate_names list.

        Args:
            location_id (str): The unique ID of the location.
            alternate_name (str): The alternate name to add.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Alternate name added to location."
                    }
                On failure (location not found, name already exists, or invalid input):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The location must exist.
            - The alternate name must not already exist in the location's alternate_names list.
            - The alternate name must not be empty.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found." }

        if not isinstance(alternate_name, str) or not alternate_name.strip():
            return { "success": False, "error": "Invalid alternate name." }

        location = self.locations[location_id]
        if alternate_name in location["alternate_names"]:
            return { "success": False, "error": "Alternate name already exists for this location." }

        location["alternate_names"].append(alternate_name)
        return { "success": True, "message": "Alternate name added to location." }

    def set_location_bounding_box(self, location_id: str, bounding_box: list) -> dict:
        """
        Define or update the bounding box for a specified location.

        Args:
            location_id (str): Unique identifier of the location.
            bounding_box (list of float): List [min_lat, min_lon, max_lat, max_lon] representing the bounding area.

        Returns:
            dict: 
              - Success: { "success": True, "message": "Bounding box set for location <location_id>" }
              - Failure: { "success": False, "error": "reason" }
    
        Constraints:
            - location_id must exist in the location database.
            - bounding_box must be a list of four floats: [min_lat, min_lon, max_lat, max_lon]
            - Each coordinate must be within valid bounds:
                min_lat and max_lat: -90 <= value <= 90
                min_lon and max_lon: -180 <= value <= 180
            - min_lat <= max_lat, min_lon <= max_lon
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location ID does not exist" }

        if (not isinstance(bounding_box, list)) or (len(bounding_box) != 4):
            return { "success": False, "error": "bounding_box must be a list of four numeric values [min_lat, min_lon, max_lat, max_lon]" }

        try:
            min_lat, min_lon, max_lat, max_lon = [float(x) for x in bounding_box]
        except Exception:
            return { "success": False, "error": "bounding_box must contain only numbers" }

        # Validate latitude and longitude ranges
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            return { "success": False, "error": "Latitude values must be between -90 and 90" }
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            return { "success": False, "error": "Longitude values must be between -180 and 180" }
    
        if min_lat > max_lat:
            return { "success": False, "error": "min_lat cannot be greater than max_lat" }
        if min_lon > max_lon:
            return { "success": False, "error": "min_lon cannot be greater than max_lon" }

        self.locations[location_id]['bounding_box'] = [min_lat, min_lon, max_lat, max_lon]

        return { "success": True, "message": f"Bounding box set for location {location_id}" }

    def remove_alternate_name_from_location(self, location_id: str, alternate_name: str) -> dict:
        """
        Remove an alternate name from a location's alternate_names list.

        Args:
            location_id (str): The unique identifier for the location.
            alternate_name (str): The alternate name to remove from the list.

        Returns:
            dict:
                - On success: {"success": True, "message": "Alternate name removed from location." }
                - On failure: {"success": False, "error": <error message> }

        Constraints:
            - location_id must exist in the locations database.
            - alternate_name must exist in the location's alternate_names list (comparison is case-sensitive).
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location ID does not exist."}

        location = self.locations[location_id]

        if not location["alternate_names"]:
            return {"success": False, "error": "No alternate names to remove for this location."}

        if alternate_name not in location["alternate_names"]:
            return {"success": False, "error": "Alternate name not found in this location's alternate_names."}

        # Remove the alternate name (remove only one instance if duplicates exist)
        location["alternate_names"].remove(alternate_name)
        return {"success": True, "message": "Alternate name removed from location."}


class GeospatialLocationDatabase(BaseEnv):
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

    def search_locations_by_name(self, **kwargs):
        return self._call_inner_tool('search_locations_by_name', kwargs)

    def get_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_location_by_id', kwargs)

    def get_coordinates_by_location_id(self, **kwargs):
        return self._call_inner_tool('get_coordinates_by_location_id', kwargs)

    def filter_locations_by_type(self, **kwargs):
        return self._call_inner_tool('filter_locations_by_type', kwargs)

    def search_locations_in_bounding_box(self, **kwargs):
        return self._call_inner_tool('search_locations_in_bounding_box', kwargs)

    def list_all_locations(self, **kwargs):
        return self._call_inner_tool('list_all_locations', kwargs)

    def validate_location_coordinates(self, **kwargs):
        return self._call_inner_tool('validate_location_coordinates', kwargs)

    def add_location(self, **kwargs):
        return self._call_inner_tool('add_location', kwargs)

    def update_location_info(self, **kwargs):
        return self._call_inner_tool('update_location_info', kwargs)

    def add_alternate_name_to_location(self, **kwargs):
        return self._call_inner_tool('add_alternate_name_to_location', kwargs)

    def set_location_bounding_box(self, **kwargs):
        return self._call_inner_tool('set_location_bounding_box', kwargs)

    def remove_alternate_name_from_location(self, **kwargs):
        return self._call_inner_tool('remove_alternate_name_from_location', kwargs)

