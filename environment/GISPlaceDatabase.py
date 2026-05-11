# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
from math import radians, cos, sin, asin, sqrt



class PlaceInfo(TypedDict):
    place_id: str
    name: str
    latitude: float
    longitude: float
    type: str
    address: str
    tags: List[str]
    a: str

class SpatialIndexInfo(TypedDict, total=False):
    index_type: str
    index_data: Any  # Internal structure, could be an R-tree or similar

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for a GIS place database.
        """

        # Place storage: {place_id: PlaceInfo}
        # (Represents unique locations, coordinates, and metadata)
        self.places: Dict[str, PlaceInfo] = {}

        # Internal spatial index (for accelerating spatial queries)
        # (Optional, abstract; may wrap spatial indexing structures)
        self.spatial_index: SpatialIndexInfo = {}

        # Constraints:
        # - Each place must have unique geographic coordinates (latitude, longitude).
        # - All spatial queries must respect Earth geometry (e.g., haversine for distance).
        # - Place attributes must be consistent and up to date.
        # - Spatial indexes must be updated if a place is added, modified, or removed.

    def get_place_by_id(self, place_id: str) -> dict:
        """
        Retrieve the complete information of a place given its unique place_id.

        Args:
            place_id (str): The unique identifier of the place to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": PlaceInfo  # Full information of the requested place
            }
            or
            {
                "success": False,
                "error": str  # Reason why the place could not be retrieved (e.g. not found)
            }

        Constraints:
            - The place_id must exist in the system.
            - Place attributes are assumed to be consistent and up to date.
        """
        if place_id not in self.places:
            return {
                "success": False,
                "error": "Place not found"
            }
        return {
            "success": True,
            "data": self.places[place_id]
        }

    def list_all_places(self) -> dict:
        """
        Return a list of all places stored in the GIS database.

        Returns:
            dict: {
                "success": True,
                "data": List[PlaceInfo]
            }
            - List may be empty if no places exist.

        Constraints:
            - Returns current data in the system.
            - No input parameters.
        """
        # Simply collect all PlaceInfo as a list
        all_places = list(self.places.values())
        return { "success": True, "data": all_places }

    def find_places_within_radius(
        self, 
        center_latitude: float, 
        center_longitude: float, 
        radius_km: float
    ) -> dict:
        """
        Find all places within a given radius (in kilometers) from the specified latitude and longitude,
        using the haversine formula for spherical Earth geometry.

        Args:
            center_latitude (float): Latitude of the center point (-90 <= latitude <= 90)
            center_longitude (float): Longitude of the center point (-180 <= longitude <= 180)
            radius_km (float): Radius in kilometers (must be >= 0)

        Returns:
            dict:
                - If input is valid: {
                      "success": True,
                      "data": List[PlaceInfo]  # All places within or exactly at the given radius (may be empty)
                  }
                - If input invalid: {
                      "success": False,
                      "error": "<error reason>"
                  }

        Constraints:
            - Use the haversine formula.
            - Only valid latitude, longitude and non-negative radius.
        """
        # Validate inputs
        if not (-90.0 <= center_latitude <= 90.0):
            return { "success": False, "error": "Latitude out of range (-90 to 90)" }
        if not (-180.0 <= center_longitude <= 180.0):
            return { "success": False, "error": "Longitude out of range (-180 to 180)" }
        if radius_km < 0:
            return { "success": False, "error": "Radius must be non-negative" }


        def haversine(lat1, lon1, lat2, lon2):
            # Earth radius (mean) in kilometers
            R = 6371.0
            # Convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            # Haversine calculation
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2.0)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2.0)**2
            c = 2 * asin(sqrt(a))
            return R * c

        result = []
        for place in self.places.values():
            distance = haversine(
                center_latitude, center_longitude,
                place["latitude"], place["longitude"]
            )
            if distance <= radius_km:
                result.append(place)

        return { "success": True, "data": result }

    def search_places_by_attribute(self, filters: dict) -> dict:
        """
        Query places filtered by specified attributes.

        Args:
            filters (dict): Keys can include:
                - "type" (str): Place type to match exactly.
                - "tags" (List[str]): At least one tag must match.
                - "name" (str): Substring (case-insensitive) match within place name.

        Returns:
            dict: On success,
                { "success": True, "data": List[PlaceInfo] }
                On error,
                { "success": False, "error": "description" }

        Constraints:
            - Only supported filter keys are applied ("type", "tags", "name").
            - Tag matching: place's tags must have at least one element in common with provided "tags" list.
            - Name matching: case-insensitive substring.
        """
        supported_keys = {"type", "tags", "name"}
        for k in filters.keys():
            if k not in supported_keys:
                return { "success": False, "error": f"Unsupported filter key: {k}" }
    
        results = []
        for place in self.places.values():
            match = True
            # Exact type match
            if "type" in filters:
                if place["type"] != filters["type"]:
                    match = False
            # Tags intersection (at least one match)
            if match and "tags" in filters:
                search_tags = set(filters["tags"])
                place_tags = set(place.get("tags", []))
                if not search_tags & place_tags:
                    match = False
            # Case-insensitive name substring
            if match and "name" in filters:
                if filters["name"].lower() not in place["name"].lower():
                    match = False
            if match:
                results.append(place)
        return { "success": True, "data": results }

    def get_place_by_coordinates(self, latitude: float, longitude: float) -> dict:
        """
        Retrieve a place's details using its exact latitude and longitude.

        Args:
            latitude (float): The latitude of the place to retrieve.
            longitude (float): The longitude of the place to retrieve.

        Returns:
            dict:
                {
                    "success": True,
                    "data": PlaceInfo
                }
                OR
                {
                    "success": False,
                    "error": "Place not found at the specified coordinates"
                }

        Constraints:
            - There can be at most one place at a given (latitude, longitude) due to uniqueness.
            - Coordinates must match exactly (no tolerance).
        """
        for place in self.places.values():
            if place["latitude"] == latitude and place["longitude"] == longitude:
                return { "success": True, "data": place }
        return { "success": False, "error": "Place not found at the specified coordinates" }

    def add_place(
        self,
        place_id: str,
        name: str,
        latitude: float,
        longitude: float,
        type: str,
        address: str,
        tags: list,
        a: str
    ) -> dict:
        """
        Add a new place to the database, enforcing coordinate uniqueness and updating the spatial index.

        Args:
            place_id (str): Unique place identifier.
            name (str): Name of the place.
            latitude (float): Latitude of the place (must be unique when paired with longitude).
            longitude (float): Longitude of the place (must be unique when paired with latitude).
            type (str): Type/category of the place.
            address (str): Postal or textual address.
            tags (List[str]): List of descriptive tags.
            a (str): Additional attribute.

        Returns:
            dict: {
                "success": True,
                "message": "Place added and spatial index updated"
            }
            or
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - Coordinates (latitude, longitude) must be unique across all places.
            - Place attributes must be up to date.
            - Spatial index must be updated after addition.
        """
        # Check coordinate uniqueness
        for existing_place in self.places.values():
            if existing_place["latitude"] == latitude and existing_place["longitude"] == longitude:
                return {"success": False, "error": "Coordinates already in use"}

        # Optional: check unique place_id (not strictly required but good integrity)
        if place_id in self.places:
            return {"success": False, "error": "Place ID already exists"}

        # (Basic coordinate sanity check)
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            return {"success": False, "error": "Invalid coordinates"}

        new_place: PlaceInfo = {
            "place_id": place_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "type": type,
            "address": address,
            "tags": tags,
            "a": a
        }

        self.places[place_id] = new_place

        # Keep the write atomic: if the spatial-index hook is misconfigured,
        # do not leave a partially inserted place behind.
        try:
            updater = self._update_spatial_index_with_new_place
            if not callable(updater):
                raise TypeError("_update_spatial_index_with_new_place is not callable")
            updater(place_id, new_place)
        except Exception as exc:
            self.places.pop(place_id, None)
            return {"success": False, "error": f"Spatial index update failed: {exc}"}

        return {"success": True, "message": "Place added and spatial index updated"}

    def _update_spatial_index_with_new_place(self, place_id: str, new_place: PlaceInfo):
        """
        Internal helper to update the spatial index with new place (abstract/stub implementation).
        """
        # This is a no-op/stub, but ensures compliance with constraint for updating spatial index.
        if "index_data" in self.spatial_index:
            # Example: Suppose it is a list
            if isinstance(self.spatial_index["index_data"], list):
                self.spatial_index["index_data"].append(new_place)
        # else: do nothing or set up index structure as needed
        return {"success": True, "message": "Spatial index updated for new place."}

    def update_place(self, place_id: str, updates: Dict[str, Any]) -> dict:
        """
        Modify attributes of an existing place, enforcing data consistency and spatial index update.

        Args:
            place_id (str): The ID of the place to update.
            updates (Dict[str, Any]): Dictionary mapping attribute names to new values.

        Returns:
            dict: On success: {"success": True, "message": "Place <place_id> updated successfully"}
                  On failure: {"success": False, "error": str}

        Constraints:
            - Target place must exist.
            - Only valid attributes may be updated.
            - If latitude/longitude are updated, resulting coordinates must remain unique.
            - Place attributes must remain consistent/valid.
            - Spatial index must be updated to reflect changes.
        """
        if place_id not in self.places:
            return {"success": False, "error": "Place ID does not exist"}

        # Allowed attributes for update
        allowed_attrs = {
            "name", "latitude", "longitude", "type", "address", "tags", "a"
        }
        if not updates:
            return {"success": False, "error": "No updates provided"}

        # Attribute validation
        for attr in updates:
            if attr not in allowed_attrs:
                return {"success": False, "error": f"Invalid attribute: {attr}"}

        current_info = self.places[place_id].copy()
        new_lat = updates.get("latitude", current_info["latitude"])
        new_lon = updates.get("longitude", current_info["longitude"])

        # If coordinates are being changed, enforce uniqueness
        if ("latitude" in updates) or ("longitude" in updates):
            # Check against other places
            for pid, info in self.places.items():
                if pid == place_id:
                    continue
                if float(info["latitude"]) == float(new_lat) and float(info["longitude"]) == float(new_lon):
                    return {"success": False, "error": "Coordinates conflict with an existing place (coordinates must be unique)"}

        # Update place attributes
        for attr, val in updates.items():
            current_info[attr] = val

        # Additional consistency checks could go here

        self.places[place_id] = current_info

        # Update spatial index if present (abstract, just simulate update)
        if hasattr(self, "spatial_index") and self.spatial_index:
            # In real code, this would update the R-tree or similar structure.
            self.rebuild_spatial_index()

        return {"success": True, "message": f"Place {place_id} updated successfully"}

    def remove_place(
        self, 
        place_id: str = None, 
        latitude: float = None, 
        longitude: float = None
    ) -> dict:
        """
        Remove a place from the database by place_id or by coordinates,
        and trigger a spatial index update.

        Args:
            place_id (str, optional): Unique identifier of the place.
            latitude (float, optional): Latitude coordinate.
            longitude (float, optional): Longitude coordinate.

        Returns:
            dict: {
                "success": True,
                "message": "Place removed and spatial index updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only one place can exist at any unique coordinate.
            - If both place_id and coordinates are provided, they must refer to the same place or an error is returned.
            - After successful removal, the spatial index must be updated accordingly.
        """
        # Step 1: Identify the place to remove
        target_place_id = None

        # Allow removal by place_id or coordinates
        if place_id is not None:
            if place_id not in self.places:
                return {"success": False, "error": "Place not found by place_id"}
            target_place = self.places[place_id]
            # If coordinates are also provided, verify they match
            if latitude is not None and longitude is not None:
                if not (
                    abs(target_place["latitude"] - latitude) < 1e-8
                    and abs(target_place["longitude"] - longitude) < 1e-8
                ):
                    return {
                        "success": False,
                        "error": "Provided place_id and coordinates do not refer to the same place"
                    }
            target_place_id = place_id
        elif latitude is not None and longitude is not None:
            # Find by coordinates
            for pid, place in self.places.items():
                if abs(place["latitude"] - latitude) < 1e-8 and abs(place["longitude"] - longitude) < 1e-8:
                    target_place_id = pid
                    break
            if target_place_id is None:
                return {"success": False, "error": "Place not found at given coordinates"}
        else:
            return {"success": False, "error": "Must provide either place_id or latitude and longitude"}

        # Step 2: Remove the place
        del self.places[target_place_id]

        # Step 3: Rebuild or update the spatial index
        if hasattr(self, "rebuild_spatial_index") and callable(self.rebuild_spatial_index):
            self.rebuild_spatial_index()
        # else: No-op if the method doesn't exist (as allowed by environment)

        return {
            "success": True,
            "message": "Place removed and spatial index updated"
        }

    def rebuild_spatial_index(self) -> dict:
        """
        Explicitly rebuild the internal spatial index from the current set of places.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "message": "Spatial index rebuilt from current places."
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure (should almost never occur)
            }

        Constraints:
            - The new spatial index must accurately reflect all places in self.places.
            - If there are no places, the index should be empty but the operation is successful.
        """
        try:
            # For demonstration, we'll use a simple list of (lat, lon, place_id)
            # In a real system, this would be an R-tree or more efficient structure
            index_data = [
                (place['latitude'], place['longitude'], place_id)
                for place_id, place in self.places.items()
            ]
            self.spatial_index['index_type'] = 'simple_list'
            self.spatial_index['index_data'] = index_data

            return {
                "success": True,
                "message": "Spatial index rebuilt from current places."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to rebuild spatial index: {str(e)}"
            }

    def validate_coordinates_uniqueness(self, latitude: float, longitude: float, exclude_place_id: str = None) -> dict:
        """
        Check if the provided latitude/longitude pair is already used by any existing place
        (excluding optionally a specific place by place_id during updates).

        Args:
            latitude (float): Latitude to check.
            longitude (float): Longitude to check.
            exclude_place_id (str, optional): If provided, this place_id is ignored (for updates).

        Returns:
            dict:
                On success (coordinates unique): {"success": True, "message": "Coordinates are unique."}
                On error (coordinates in use): {"success": False, "error": "Coordinates already in use by place_id <id>"}

        Constraints:
            - No two places may have identical (latitude, longitude) pairs.
            - Optional exclusion for update operations.
        """
        for pid, info in self.places.items():
            if exclude_place_id is not None and pid == exclude_place_id:
                continue
            if info["latitude"] == latitude and info["longitude"] == longitude:
                return {
                    "success": False,
                    "error": f"Coordinates already in use by place_id {pid}"
                }
        return {
            "success": True,
            "message": "Coordinates are unique."
        }

    def validate_place_attributes_consistency(self, place_info: dict) -> dict:
        """
        Check if a place's attributes are consistent and up-to-date with system rules before making changes.

        Args:
            place_info (dict): Dictionary containing the proposed PlaceInfo attributes.

        Returns:
            dict: {
                "success": True,
                "message": "Place attributes are consistent"
            } if valid,
            {
                "success": False,
                "error": str
            } if any attribute is inconsistent/invalid.

        Constraints:
            - All required fields (*place_id, name, latitude, longitude, type, address, tags, a*) must be present and not empty.
            - Latitude must be in [-90, 90]; longitude in [-180, 180].
            - tags must be a list of strings.
        """
        required_fields = ["place_id", "name", "latitude", "longitude", "type", "address", "tags", "a"]
        # Check all required fields present and not empty (basic checks)
        for field in required_fields:
            if field not in place_info:
                return {"success": False, "error": f"Missing required field: {field}"}
            if (place_info[field] is None) or (isinstance(place_info[field], str) and not place_info[field].strip()):
                return {"success": False, "error": f"Field '{field}' is empty"}
    
        # Latitude/longitude validity
        try:
            lat = float(place_info["latitude"])
            lon = float(place_info["longitude"])
        except (ValueError, TypeError):
            return {"success": False, "error": "Latitude and longitude must be numbers"}
        if not (-90.0 <= lat <= 90.0):
            return {"success": False, "error": "Latitude must be between -90 and 90"}
        if not (-180.0 <= lon <= 180.0):
            return {"success": False, "error": "Longitude must be between -180 and 180"}
    
        # tags must be a list of strings
        tags = place_info["tags"]
        if not isinstance(tags, list):
            return {"success": False, "error": "Tags must be a list"}
        for tag in tags:
            if not isinstance(tag, str):
                return {"success": False, "error": "All tags must be strings"}
            if not tag.strip():
                return {"success": False, "error": "Tags cannot contain empty strings"}

        # If more advanced "up-to-date" rules exist, add here.

        return {"success": True, "message": "Place attributes are consistent"}


class GISPlaceDatabase(BaseEnv):
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
            if key == "rebuild_spatial_index":
                setattr(env, "_rebuild_spatial_index_state", copy.deepcopy(value))
                continue
            if key == "_update_spatial_index_with_new_place":
                setattr(env, "_update_spatial_index_with_new_place_state", copy.deepcopy(value))
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

    def get_place_by_id(self, **kwargs):
        return self._call_inner_tool('get_place_by_id', kwargs)

    def list_all_places(self, **kwargs):
        return self._call_inner_tool('list_all_places', kwargs)

    def find_places_within_radius(self, **kwargs):
        return self._call_inner_tool('find_places_within_radius', kwargs)

    def search_places_by_attribute(self, **kwargs):
        return self._call_inner_tool('search_places_by_attribute', kwargs)

    def get_place_by_coordinates(self, **kwargs):
        return self._call_inner_tool('get_place_by_coordinates', kwargs)

    def add_place(self, **kwargs):
        return self._call_inner_tool('add_place', kwargs)

    def _update_spatial_index_with_new_place(self, **kwargs):
        return self._call_inner_tool('_update_spatial_index_with_new_place', kwargs)

    def update_place(self, **kwargs):
        return self._call_inner_tool('update_place', kwargs)

    def remove_place(self, **kwargs):
        return self._call_inner_tool('remove_place', kwargs)

    def rebuild_spatial_index(self, **kwargs):
        return self._call_inner_tool('rebuild_spatial_index', kwargs)

    def validate_coordinates_uniqueness(self, **kwargs):
        return self._call_inner_tool('validate_coordinates_uniqueness', kwargs)

    def validate_place_attributes_consistency(self, **kwargs):
        return self._call_inner_tool('validate_place_attributes_consistency', kwargs)
