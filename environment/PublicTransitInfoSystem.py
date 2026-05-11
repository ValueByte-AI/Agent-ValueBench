# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
import math
import re



class RouteInfo(TypedDict):
    route_id: str
    route_number: str
    mode: str  # 'bus' or 'rail'
    name: str
    directions: List[str]
    path_geometry: str

class DetourInfo(TypedDict):
    detour_id: str
    route_id: str
    direction: str
    start_location: str
    end_location: str
    start_datetime: str
    end_datetime: str
    current_message: str

class StopInfo(TypedDict):
    stop_id: str
    name: str
    latitude: float
    longitude: float
    served_routes: List[str]

class StationInfo(TypedDict):
    station_id: str
    name: str
    latitude: float
    longitude: float
    served_routes: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Route records: {route_id: RouteInfo}
        self.routes: Dict[str, RouteInfo] = {}  # Maps each route_id to route metadata

        # Detour records: {detour_id: DetourInfo}
        self.detours: Dict[str, DetourInfo] = {}  # Maps each detour_id to detour info

        # Virtual clock for evaluating detour activity. This must be supplied by case
        # data when time-sensitive behavior matters; it must not use host time.
        self.current_datetime: str = "2024-01-01T00:00:00+00:00"

        # Stop records: {stop_id: StopInfo}
        self.stops: Dict[str, StopInfo] = {}  # Maps each stop_id to stop metadata

        # Station records: {station_id: StationInfo}
        self.stations: Dict[str, StationInfo] = {}  # Maps each station_id to station metadata

        # Constraints:
        # - Detours must reference valid route(s) and relevant directions.
        # - Validity of detours is determined by current datetime between start_datetime and end_datetime.
        # - Stops and stations must have valid geographic coordinates for spatial queries.
        # - Each stop or station may be served by multiple routes (and vice versa).
        # - Real-time service alerts, detours, and messages must be kept up-to-date and consistent with transit ops.

    def _default_current_datetime(self) -> datetime:
        return datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    def _parse_datetime_string(self, value: str, reference_dt: datetime | None = None) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid datetime string")
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"

        if re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", text):
            ref = reference_dt or self._default_current_datetime()
            parts = [int(part) for part in text.split(":")]
            hour, minute = parts[0], parts[1]
            second = parts[2] if len(parts) == 3 else 0
            return ref.replace(hour=hour, minute=minute, second=second, microsecond=0)

        return datetime.fromisoformat(text)

    def _get_current_datetime(self) -> datetime:
        raw = getattr(self, "current_datetime", None)
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str) and raw.strip():
            try:
                return self._parse_datetime_string(raw, self._default_current_datetime())
            except Exception:
                pass
        return self._default_current_datetime()

    def _align_current_datetime(self, reference_dt: datetime) -> datetime:
        current_dt = self._get_current_datetime()
        if reference_dt.tzinfo is None:
            return current_dt.replace(tzinfo=None)
        if current_dt.tzinfo is None:
            return current_dt.replace(tzinfo=reference_dt.tzinfo)
        return current_dt.astimezone(reference_dt.tzinfo)

    def get_route_by_number(self, route_number: str) -> dict:
        """
        Retrieve route metadata (route_id, mode, name, directions, path_geometry) by route_number.

        Args:
            route_number (str): The public-facing route number to search for.

        Returns:
            dict: {
                "success": True,
                "data": RouteInfo
            }
            OR
            {
                "success": False,
                "error": "Route with given number not found"
            }

        Constraint:
            - Returns the first route with the exact route_number match; if none exist, returns error.
        """
        for route in self.routes.values():
            if route["route_number"] == route_number:
                return {"success": True, "data": route}
        return {"success": False, "error": "Route with given number not found"}

    def get_route_by_id(self, route_id: str) -> dict:
        """
        Retrieve full route information using the unique route_id.

        Args:
            route_id (str): The unique identifier for the route.

        Returns:
            dict: {
                "success": True,
                "data": RouteInfo  # RouteInfo dictionary for the requested route.
            }
            or
            {
                "success": False,
                "error": str  # If the route_id is not found.
            }

        Constraints:
            - route_id must exist in the system.

        Edge Cases:
            - If route_id is missing from the routes, returns error message.
        """
        route = self.routes.get(route_id)
        if route is not None:
            return { "success": True, "data": route }
        else:
            return { "success": False, "error": f"Route with route_id {route_id} does not exist" }

    def list_routes_by_mode(self, mode: str) -> dict:
        """
        List all transit routes filtered by transit mode.

        Args:
            mode (str): Transit mode to filter ("bus" or "rail").

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo],  # All RouteInfo for matching routes (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., unsupported mode
            }

        Constraints:
            - Only 'bus' or 'rail' are valid modes.
        """
        allowed_modes = {"bus", "rail"}
        mode_lower = mode.lower().strip()

        if mode_lower not in allowed_modes:
            return { "success": False, "error": "Invalid transit mode" }

        routes = [
            route for route in self.routes.values()
            if route["mode"].lower() == mode_lower
        ]
        return { "success": True, "data": routes }

    def get_detours_by_route_id(self, route_id: str) -> dict:
        """
        Retrieve all detour records (active or inactive) associated with a given route_id.

        Args:
            route_id (str): Unique identifier for the route.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[DetourInfo],  # may be empty if no detours for this route
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # "Route does not exist"
                    }

        Constraints:
            - The provided route_id must exist in the system.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        detours = [
            detour_info for detour_info in self.detours.values()
            if detour_info["route_id"] == route_id
        ]

        return {"success": True, "data": detours}

    def get_active_detours_by_route_id(self, route_id: str) -> dict:
        """
        Retrieve all currently active detours for the specified route_id, where 'active' means the
        current datetime is within the detour's start_datetime and end_datetime (inclusive).

        Args:
            route_id (str): The unique identifier for a transit route.

        Returns:
            dict:
                - On success: {"success": True, "data": List[DetourInfo]} (possibly empty list)
                - On error:   {"success": False, "error": str}
        Constraints:
            - Route must exist.
            - Detour datetime strings must be valid ISO 8601. Detours with invalid datetime formats are skipped.
        """

        # Check route exists
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        current_dt = self._get_current_datetime()
        active_detours = []
        for detour in self.detours.values():
            if detour.get("route_id") != route_id:
                continue
            # Attempt to parse dates, skip detours with invalid date format
            try:
                start_dt = self._parse_datetime_string(detour["start_datetime"], current_dt)
                end_dt = self._parse_datetime_string(detour["end_datetime"], current_dt)
            except Exception:
                continue  # Ignore detours with invalid datetime formats

            if (start_dt.tzinfo is None) != (end_dt.tzinfo is None):
                continue
            now_dt = self._align_current_datetime(start_dt)

            if start_dt <= now_dt <= end_dt:
                active_detours.append(detour)

        return {"success": True, "data": active_detours}

    def get_detour_details(self, detour_id: str) -> dict:
        """
        Retrieve full details for a specific detour by detour_id.

        Args:
            detour_id (str): Unique ID of the detour to query.

        Returns:
            dict:
                - On success: { "success": True, "data": DetourInfo }
                - If not found: { "success": False, "error": "Detour not found" }

        Constraints:
            - detour_id must exist in self.detours.
        """
        detour = self.detours.get(detour_id)
        if not detour:
            return { "success": False, "error": "Detour not found" }
        return { "success": True, "data": detour }

    def get_detours_by_route_number_and_mode(self, route_number: str, mode: str) -> dict:
        """
        Retrieve all detours for a transit route, identified by route_number and mode.

        Args:
            route_number (str): The designated route number (e.g., "4").
            mode (str): The transit mode (e.g., "bus" or "rail").

        Returns:
            dict:
              On success:
                {
                    "success": True,
                    "data": List[DetourInfo],  # All detours linked to the route (may be empty)
                }
              On failure:
                {
                    "success": False,
                    "error": str,  # Reason, e.g. "Route not found"
                }

        Constraints:
            - Only detours for matched route (by route_number and mode) are returned.
            - Does not check for time activity; all detours are returned.
            - Returns an empty list if route exists but has no detours.
        """
        # Find route by number & mode
        route_id = None
        for route in self.routes.values():
            if route["route_number"] == route_number and route["mode"] == mode:
                route_id = route["route_id"]
                break

        if route_id is None:
            return {"success": False, "error": "Route not found for the specified number and mode"}

        # Collect all detours for this route
        detours = [
            detour
            for detour in self.detours.values()
            if detour["route_id"] == route_id
        ]

        return {"success": True, "data": detours}

    def list_stops_within_radius(self, latitude: float, longitude: float, radius_meters: float) -> dict:
        """
        List all bus stops within a specified radius (meters) of a geographic point.

        Args:
            latitude (float): Central latitude in decimal degrees (-90 to 90).
            longitude (float): Central longitude in decimal degrees (-180 to 180).
            radius_meters (float): Search radius in meters (must be > 0).

        Returns:
            dict: {
                "success": True,
                "data": List[StopInfo],  # List (possibly empty) of matching stops
            }
            or
            {
                "success": False,
                "error": str  # e.g., invalid input parameters
            }

        Constraints:
            - All stop coordinates must be valid geocoordinates.
            - Stops with invalid/missing coordinates are ignored.
        """
        # Validate latitude and longitude
        if not (isinstance(latitude, (int, float)) and -90 <= latitude <= 90):
            return { "success": False, "error": "Invalid latitude" }
        if not (isinstance(longitude, (int, float)) and -180 <= longitude <= 180):
            return { "success": False, "error": "Invalid longitude" }
        if not (isinstance(radius_meters, (int, float)) and radius_meters > 0):
            return { "success": False, "error": "Radius must be positive" }


        def haversine(lat1, lon1, lat2, lon2):
            # Earth radius in meters
            R = 6371000
            phi1 = radians(lat1)
            phi2 = radians(lat2)
            delta_phi = radians(lat2 - lat1)
            delta_lambda = radians(lon2 - lon1)
            a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        result = []
        for stop in self.stops.values():
            stop_lat = stop.get("latitude")
            stop_lon = stop.get("longitude")
            if (
                isinstance(stop_lat, (int, float))
                and isinstance(stop_lon, (int, float))
                and -90 <= stop_lat <= 90
                and -180 <= stop_lon <= 180
            ):
                distance = haversine(latitude, longitude, stop_lat, stop_lon)
                if distance <= radius_meters:
                    result.append(stop)

        return { "success": True, "data": result }


    def list_stations_within_radius(self, latitude: float, longitude: float, radius: float) -> dict:
        """
        List all rail stations within a specified radius (in kilometers) of a provided geographic point.

        Args:
            latitude (float): Latitude of center point (-90 to 90).
            longitude (float): Longitude of center point (-180 to 180).
            radius (float): Search radius in kilometers (must be > 0).

        Returns:
            dict: {
                "success": True,
                "data": List[StationInfo],  # List of station infos within radius (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # reason for error (invalid input)
            }

        Constraints:
            - Latitude must be in [-90, 90], longitude in [-180, 180].
            - Radius must be > 0.
        """

        # Validate input parameters
        if not (-90.0 <= latitude <= 90.0):
            return { "success": False, "error": "Invalid latitude" }
        if not (-180.0 <= longitude <= 180.0):
            return { "success": False, "error": "Invalid longitude" }
        if radius <= 0:
            return { "success": False, "error": "Radius must be greater than 0" }

        def haversine_distance(lat1, lon1, lat2, lon2):
            """
            Compute the Haversine distance between two points on Earth (km).
            """
            R = 6371.0  # Earth radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            d_phi = math.radians(lat2 - lat1)
            d_lambda = math.radians(lon2 - lon1)
            a = math.sin(d_phi / 2.0) ** 2 + \
                math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        results = []
        for station in self.stations.values():
            dist = haversine_distance(latitude, longitude, station["latitude"], station["longitude"])
            if dist <= radius:
                results.append(station)

        return { "success": True, "data": results }

    def get_stop_by_id(self, stop_id: str) -> dict:
        """
        Retrieve full stop information given a stop_id.

        Args:
            stop_id (str): The unique identifier for the desired stop.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": StopInfo  # Dictionary of all stop attributes
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Stop not found"
                    }

        Constraints:
            - The provided stop_id must exist in the system.
        """
        if stop_id not in self.stops:
            return { "success": False, "error": "Stop not found" }
        return { "success": True, "data": self.stops[stop_id] }

    def get_station_by_id(self, station_id: str) -> dict:
        """
        Retrieve full station information by station_id.

        Args:
            station_id (str): The unique identifier for the station.

        Returns:
            dict: {
                "success": True,
                "data": StationInfo
            } if found,
            {
                "success": False,
                "error": "Station not found"
            } otherwise.

        Constraints:
            - station_id must exist in the system.
        """
        station = self.stations.get(station_id)
        if station is not None:
            return { "success": True, "data": station }
        else:
            return { "success": False, "error": "Station not found" }

    def get_stops_served_by_route(self, route_id: str) -> dict:
        """
        Retrieve the list of all stops (with metadata) served by the specified route.

        Args:
            route_id (str): The unique identifier of the route.

        Returns:
            dict: {
                "success": True,
                "data": List[StopInfo]  # List of matching stop metadata (may be empty if route serves no stops)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Route does not exist"
            }

        Constraints:
            - Fails if the given route_id does not exist.
            - Returns an empty list if a valid route serves no stops.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        stops_served = [
            stop_info for stop_info in self.stops.values()
            if route_id in stop_info["served_routes"]
        ]

        return {"success": True, "data": stops_served}

    def get_stations_served_by_route(self, route_id: str) -> dict:
        """
        Retrieve the list of all stations served by a specific route (by route_id).

        Args:
            route_id (str): The unique identifier for the route.

        Returns:
            dict: {
                "success": True,
                "data": List[StationInfo],  # List of stations served by the route (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # If route_id is invalid
            }

        Constraints:
            - The route_id must exist in the system.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route not found"}

        stations = [
            station
            for station in self.stations.values()
            if route_id in station.get("served_routes", [])
        ]

        return {"success": True, "data": stations}

    def get_routes_by_stop_or_station(self, entity_id: str) -> dict:
        """
        Retrieve all routes that serve a given stop or station by their id.

        Args:
            entity_id (str): The unique id of the stop or station.

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo],  # List of routes that serve the given stop or station
            }
            or
            {
                "success": False,
                "error": str  # If no stop or station matches the given id
            }

        Constraints:
            - If entity_id is not found in stops or stations, operation fails.
            - Only route_ids that exist in the system are returned (skip missing).
        """
        served_routes = None

        if entity_id in self.stops:
            served_routes = self.stops[entity_id]["served_routes"]
        elif entity_id in self.stations:
            served_routes = self.stations[entity_id]["served_routes"]
        else:
            return { "success": False, "error": "No stop or station found with the given id" }
    
        # Filter for real routes that still exist (avoid missing keys)
        routes = [
            self.routes[route_id]
            for route_id in served_routes
            if route_id in self.routes
        ]

        return { "success": True, "data": routes }

    def add_detour(
        self, 
        detour_id: str, 
        route_id: str, 
        direction: str, 
        start_location: str, 
        end_location: str, 
        start_datetime: str, 
        end_datetime: str, 
        current_message: str
    ) -> dict:
        """
        Create and add a new detour linked to a specified route and direction.

        Args:
            detour_id (str): Unique identifier for the detour. Must not already exist.
            route_id (str): Route affected by the detour. Must already exist.
            direction (str): Direction of the detour (must be listed in route's `directions`).
            start_location (str): Start location description of detour.
            end_location (str): End location description of detour.
            start_datetime (str): Start datetime of detour (ISO8601 or system convention).
            end_datetime (str): End datetime of detour.
            current_message (str): Active status/message of the detour.

        Returns:
            dict: 
              On success:
                {"success": True, "message": "Detour added for route <route_id> (<direction>)"}
              On failure:
                {"success": False, "error": <description>}
    
        Constraints:
          - Detour ID must be unique.
          - Route ID must exist.
          - Direction must be valid for the route.
        """
        if detour_id in self.detours:
            return {"success": False, "error": "Detour ID already exists"}

        route = self.routes.get(route_id)
        if route is None:
            return {"success": False, "error": "Invalid route_id"}

        if direction not in route.get("directions", []):
            return {"success": False, "error": "Invalid direction for the specified route"}

        try:
            start_obj = self._parse_datetime_string(start_datetime, self._get_current_datetime())
            end_obj = self._parse_datetime_string(end_datetime, self._get_current_datetime())
            if start_obj > end_obj:
                return {"success": False, "error": "start_datetime must not be after end_datetime."}
        except Exception:
            return {
                "success": False,
                "error": "Invalid date format for start_datetime or end_datetime (must be ISO 8601, optionally with 'Z', or HH:MM/HH:MM:SS in the virtual service day).",
            }

        detour_info: DetourInfo = {
            "detour_id": detour_id,
            "route_id": route_id,
            "direction": direction,
            "start_location": start_location,
            "end_location": end_location,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "current_message": current_message
        }

        self.detours[detour_id] = detour_info
        return {
            "success": True,
            "message": f"Detour added for route {route_id} ({direction})"
        }

    def update_detour(self, detour_id: str, updates: dict) -> dict:
        """
        Update details of an existing detour.

        Args:
            detour_id (str): The unique ID of the detour to update.
            updates (dict): Dictionary of fields to update (any DetourInfo field).

        Returns:
            dict: 
                On success: {"success": True, "message": "Detour updated successfully."}
                On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - detour_id must exist.
            - If updating route_id, the new route_id must exist.
            - If updating direction, the direction must exist in the directions for the associated route.
            - If updating start_datetime/end_datetime, they must be valid ISO strings and start <= end.
            - Only DetourInfo fields may be updated.
        """
        allowed_fields = {
            "route_id", "direction", "start_location", 
            "end_location", "start_datetime", 
            "end_datetime", "current_message"
        }
        if detour_id not in self.detours:
            return { "success": False, "error": "Detour not found." }

        detour = self.detours[detour_id].copy()  # to build updated values

        # Validate and apply updates
        for key, value in updates.items():
            if key not in allowed_fields:
                continue  # skip irrelevant keys

            if key == "route_id":
                # Check route exists
                if value not in self.routes:
                    return { "success": False, "error": "Given route_id does not exist." }
                detour["route_id"] = value

            elif key == "direction":
                # Look up proper route's directions
                route_id = updates.get("route_id", detour["route_id"])
                route = self.routes.get(route_id)
                if not route:
                    return { "success": False, "error": "Associated route for direction not found." }
                if value not in route["directions"]:
                    return { "success": False, "error": "Direction not valid for given route." }
                detour["direction"] = value

            elif key in ("start_datetime", "end_datetime"):
                # Optional: Check valid ISO string and date order
                detour[key] = value

            else:
                detour[key] = value

        # Datetime chronological check (if both provided or changed)
        start_dt = updates.get("start_datetime", detour["start_datetime"])
        end_dt = updates.get("end_datetime", detour["end_datetime"])
        # try to parse and compare if both present
        try:
            if start_dt and end_dt:
                reference_dt = self._get_current_datetime()
                start_obj = self._parse_datetime_string(start_dt, reference_dt)
                end_obj = self._parse_datetime_string(end_dt, reference_dt)
                if start_obj > end_obj:
                    return { "success": False, "error": "start_datetime must not be after end_datetime." }
        except Exception:
            return {
                "success": False,
                "error": "Invalid date format for start_datetime or end_datetime (must be ISO 8601, optionally with 'Z', or HH:MM/HH:MM:SS in the virtual service day).",
            }

        # Save back the updated detour
        self.detours[detour_id] = detour
        return { "success": True, "message": "Detour updated successfully." }

    def remove_detour(self, detour_id: str) -> dict:
        """
        Remove an existing detour from the system.

        Args:
            detour_id (str): The identifier of the detour to remove.

        Returns:
            dict: {
                'success': True,
                'message': 'Detour <detour_id> removed'
            }
            or
            {
                'success': False,
                'error': '<reason>'
            }

        Constraints:
            - The detour_id must exist in the system.
        """
        if detour_id not in self.detours:
            return {"success": False, "error": f"Detour '{detour_id}' does not exist"}
        del self.detours[detour_id]
        return {"success": True, "message": f"Detour '{detour_id}' removed"}

    def add_stop(
        self,
        stop_id: str,
        name: str,
        latitude: float,
        longitude: float,
        served_routes: list
    ) -> dict:
        """
        Add a new transit stop to the system.

        Args:
            stop_id (str): Unique identifier for the stop.
            name (str): Name of the stop. Should be non-empty.
            latitude (float): Latitude in degrees (-90 to 90).
            longitude (float): Longitude in degrees (-180 to 180).
            served_routes (List[str]): List of route_id that serve this stop.

        Returns:
            dict: {
                "success": True,
                "message": "Stop <stop_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - stop_id must be unique (not already present).
            - latitude and longitude must be valid coordinates.
            - All served_routes must reference valid route IDs.
            - Name should be non-empty.
        """

        # Check stop_id uniqueness
        if stop_id in self.stops:
            return {"success": False, "error": f"Stop ID '{stop_id}' already exists."}

        # Check name non-empty
        if not isinstance(name, str) or name.strip() == "":
            return {"success": False, "error": "Stop name cannot be empty."}

        # Check latitude and longitude validity
        if not (isinstance(latitude, (float, int)) and -90 <= latitude <= 90):
            return {"success": False, "error": "Invalid latitude. Must be between -90 and 90."}
        if not (isinstance(longitude, (float, int)) and -180 <= longitude <= 180):
            return {"success": False, "error": "Invalid longitude. Must be between -180 and 180."}

        # served_routes must be a list of valid route IDs
        if not isinstance(served_routes, list):
            return {"success": False, "error": "served_routes must be a list of route IDs."}

        invalid_routes = [rid for rid in served_routes if rid not in self.routes]
        if invalid_routes:
            return {
                "success": False,
                "error": f"Invalid route_id(s) in served_routes: {', '.join(invalid_routes)}."
            }

        # Compose and add the new stop
        stop_info = {
            "stop_id": stop_id,
            "name": name,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "served_routes": list(served_routes),
        }

        self.stops[stop_id] = stop_info

        return {
            "success": True,
            "message": f"Stop {stop_id} added successfully."
        }

    def update_stop(
        self,
        stop_id: str,
        name: str = None,
        latitude: float = None,
        longitude: float = None,
        served_routes: list = None
    ) -> dict:
        """
        Update stop information, location, or served routes.

        Args:
            stop_id (str): The id of the stop to update.
            name (str, optional): New stop name.
            latitude (float, optional): New latitude (must be -90 <= latitude <= 90).
            longitude (float, optional): New longitude (must be -180 <= longitude <= 180).
            served_routes (list of str, optional): New list of route_id's the stop serves (each must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Stop updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - stop_id must exist.
            - If latitude/longitude provided, they must be within valid ranges.
            - If served_routes provided, all routes must exist in self.routes.
        """
        # Check existence
        if stop_id not in self.stops:
            return {"success": False, "error": "Stop not found."}

        stop = self.stops[stop_id]

        # Validate coordinate updates if given
        if latitude is not None:
            if not (-90.0 <= latitude <= 90.0):
                return {"success": False, "error": "Invalid latitude, must be between -90 and 90."}
        if longitude is not None:
            if not (-180.0 <= longitude <= 180.0):
                return {"success": False, "error": "Invalid longitude, must be between -180 and 180."}

        # Validate served_routes if given
        if served_routes is not None:
            if not isinstance(served_routes, list):
                return {"success": False, "error": "served_routes must be a list of route_id strings."}
            invalid_routes = [r for r in served_routes if r not in self.routes]
            if invalid_routes:
                return {"success": False, "error": f"Invalid route(s) in served_routes: {invalid_routes}"}

        # Apply updates
        if name is not None:
            stop["name"] = name
        if latitude is not None:
            stop["latitude"] = latitude
        if longitude is not None:
            stop["longitude"] = longitude
        if served_routes is not None:
            stop["served_routes"] = served_routes

        self.stops[stop_id] = stop  # Not strictly necessary but for clarity

        return {"success": True, "message": "Stop updated successfully."}

    def remove_stop(self, stop_id: str) -> dict:
        """
        Remove a stop from the transit information system.

        Args:
            stop_id (str): The ID of the stop to remove.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Stop <stop_id> removed successfully"}
                On failure:
                    {"success": False, "error": "Stop not found"}

        Constraints:
            - The stop must exist in the system.
            - No referential updates are needed elsewhere according to current model.
        """
        if stop_id not in self.stops:
            return {"success": False, "error": "Stop not found"}

        del self.stops[stop_id]
        return {"success": True, "message": f"Stop {stop_id} removed successfully"}

    def add_station(
        self, 
        station_id: str, 
        name: str, 
        latitude: float, 
        longitude: float, 
        served_routes: list
    ) -> dict:
        """
        Add a new station to the system with valid coordinates and served routes.

        Args:
            station_id (str): Unique identifier for the station.
            name (str): Name of the station.
            latitude (float): Latitude (-90 to 90).
            longitude (float): Longitude (-180 to 180).
            served_routes (List[str]): List of route_ids the station serves.

        Returns:
            dict: {
                "success": True,
                "message": "Station <station_id> added."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - station_id must not already exist.
            - latitude in [-90, 90], longitude in [-180, 180].
            - Each route_id in served_routes must exist in self.routes.
        """
        # Check station_id uniqueness
        if station_id in self.stations:
            return {"success": False, "error": "Station ID already exists"}

        # Validate latitude/longitude
        if not (-90.0 <= latitude <= 90.0):
            return {"success": False, "error": "Latitude must be between -90 and 90"}
        if not (-180.0 <= longitude <= 180.0):
            return {"success": False, "error": "Longitude must be between -180 and 180"}

        # Validate name
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Station name must be a non-empty string"}

        # Validate served_routes entries
        for rid in served_routes:
            if rid not in self.routes:
                return {"success": False, "error": f"Route ID '{rid}' in served_routes does not exist"}

        # Construct and add the station
        station_info = {
            "station_id": station_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "served_routes": list(served_routes)
        }
        self.stations[station_id] = station_info

        return {"success": True, "message": f"Station {station_id} added."}

    def update_station(
        self, 
        station_id: str,
        name: str = None,
        latitude: float = None,
        longitude: float = None,
        served_routes: list = None
    ) -> dict:
        """
        Update station information such as name, location (latitude/longitude), and served routes.

        Args:
            station_id (str): Identifier of the station to update.
            name (str, optional): New station name.
            latitude (float, optional): New latitude value (must be between -90 and 90).
            longitude (float, optional): New longitude value (must be between -180 and 180).
            served_routes (list, optional): New list of route IDs the station serves (all routes must exist).

        Returns:
            dict: 
                Success - { "success": True, "message": "Station updated successfully" }
                Failure - { "success": False, "error": <reason> }

        Constraints:
            - station_id must exist.
            - Latitude and longitude, if provided, must be within valid geographic ranges.
            - If served_routes is provided, every route_id must exist in self.routes.
        """
        if station_id not in self.stations:
            return { "success": False, "error": "Station does not exist" }
        # Copy station info for update
        station = self.stations[station_id]

        # Validate and apply updates
        updates = 0

        if name is not None:
            station['name'] = name
            updates += 1

        if latitude is not None:
            try:
                lat = float(latitude)
                if lat < -90 or lat > 90:
                    return { "success": False, "error": "Latitude must be between -90 and 90" }
                station['latitude'] = lat
                updates += 1
            except (ValueError, TypeError):
                return { "success": False, "error": "Invalid latitude value" }

        if longitude is not None:
            try:
                lng = float(longitude)
                if lng < -180 or lng > 180:
                    return { "success": False, "error": "Longitude must be between -180 and 180" }
                station['longitude'] = lng
                updates += 1
            except (ValueError, TypeError):
                return { "success": False, "error": "Invalid longitude value" }

        if served_routes is not None:
            if not isinstance(served_routes, list):
                return { "success": False, "error": "served_routes must be a list of route IDs" }
            invalid_routes = [rid for rid in served_routes if rid not in self.routes]
            if invalid_routes:
                return { "success": False, "error": f"Invalid route IDs: {invalid_routes}" }
            station['served_routes'] = list(served_routes)
            updates += 1

        if updates == 0:
            return { "success": False, "error": "No valid update fields provided" }

        self.stations[station_id] = station
        return { "success": True, "message": "Station updated successfully" }

    def remove_station(self, station_id: str) -> dict:
        """
        Remove a station from the system by its station_id.

        Args:
            station_id (str): Unique identifier for the station.

        Returns:
            dict:
                - On success: { "success": True, "message": "Station <station_id> removed." }
                - On failure: { "success": False, "error": "Station not found." }

        Constraints:
            - The specified station must exist in self.stations.
            - Removal only affects the stations dict; associations on routes or other entities are not updated unless specified elsewhere.
        """
        if station_id not in self.stations:
            return { "success": False, "error": "Station not found." }

        del self.stations[station_id]
        return { "success": True, "message": f"Station {station_id} removed." }


class PublicTransitInfoSystem(BaseEnv):
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

    def get_route_by_number(self, **kwargs):
        return self._call_inner_tool('get_route_by_number', kwargs)

    def get_route_by_id(self, **kwargs):
        return self._call_inner_tool('get_route_by_id', kwargs)

    def list_routes_by_mode(self, **kwargs):
        return self._call_inner_tool('list_routes_by_mode', kwargs)

    def get_detours_by_route_id(self, **kwargs):
        return self._call_inner_tool('get_detours_by_route_id', kwargs)

    def get_active_detours_by_route_id(self, **kwargs):
        return self._call_inner_tool('get_active_detours_by_route_id', kwargs)

    def get_detour_details(self, **kwargs):
        return self._call_inner_tool('get_detour_details', kwargs)

    def get_detours_by_route_number_and_mode(self, **kwargs):
        return self._call_inner_tool('get_detours_by_route_number_and_mode', kwargs)

    def list_stops_within_radius(self, **kwargs):
        return self._call_inner_tool('list_stops_within_radius', kwargs)

    def list_stations_within_radius(self, **kwargs):
        return self._call_inner_tool('list_stations_within_radius', kwargs)

    def get_stop_by_id(self, **kwargs):
        return self._call_inner_tool('get_stop_by_id', kwargs)

    def get_station_by_id(self, **kwargs):
        return self._call_inner_tool('get_station_by_id', kwargs)

    def get_stops_served_by_route(self, **kwargs):
        return self._call_inner_tool('get_stops_served_by_route', kwargs)

    def get_stations_served_by_route(self, **kwargs):
        return self._call_inner_tool('get_stations_served_by_route', kwargs)

    def get_routes_by_stop_or_station(self, **kwargs):
        return self._call_inner_tool('get_routes_by_stop_or_station', kwargs)

    def add_detour(self, **kwargs):
        return self._call_inner_tool('add_detour', kwargs)

    def update_detour(self, **kwargs):
        return self._call_inner_tool('update_detour', kwargs)

    def remove_detour(self, **kwargs):
        return self._call_inner_tool('remove_detour', kwargs)

    def add_stop(self, **kwargs):
        return self._call_inner_tool('add_stop', kwargs)

    def update_stop(self, **kwargs):
        return self._call_inner_tool('update_stop', kwargs)

    def remove_stop(self, **kwargs):
        return self._call_inner_tool('remove_stop', kwargs)

    def add_station(self, **kwargs):
        return self._call_inner_tool('add_station', kwargs)

    def update_station(self, **kwargs):
        return self._call_inner_tool('update_station', kwargs)

    def remove_station(self, **kwargs):
        return self._call_inner_tool('remove_station', kwargs)
