# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from math import radians, cos, sin, sqrt, atan2



# BusStop entity (stop_id = op_id) with associated attributes
class BusStopInfo(TypedDict):
    stop_id: str         # corresponds to op_id
    name: str
    latitude: float
    longitude: float
    associated_route_id: List[str]  # list of route_ids

# Route entity with associated attributes
class RouteInfo(TypedDict):
    route_id: str        # corresponds to oute_id
    name: str
    list_of_stop_ids: List[str]
    schedule_info: str   # could be expanded to a structured dict

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for city bus route and stop management.
        """

        # Bus stops: {stop_id: BusStopInfo}
        # Maps unique stop_id to bus stop metadata and associated routes
        self.bus_stops: Dict[str, BusStopInfo] = {}

        # Routes: {route_id: RouteInfo}
        # Maps route_id to route metadata, stops and schedules
        self.routes: Dict[str, RouteInfo] = {}

        # Constraints:
        # - Every stop must have a unique stop_id.
        # - Every stop is associated with at least one route (unless temporarily out of service).
        # - Each stop must have valid, non-null geographic coordinates (latitude and longitude).

    def search_bus_stops_by_keyword(self, keyword: str) -> dict:
        """
        Search bus stops where the name or related fields (name or stop_id) match the given keyword, case-insensitive.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[BusStopInfo]  # List of bus stops whose name or stop_id matches the keyword (case-insensitive).
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error (e.g. missing or invalid input).
                }
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return { "success": False, "error": "Invalid or empty keyword." }

        keyword_lower = keyword.strip().lower()
        matches = []
        for stop in self.bus_stops.values():
            # Check name and stop_id fields, case-insensitive
            if (keyword_lower in stop["name"].lower()) or (keyword_lower in stop["stop_id"].lower()):
                matches.append(stop)

        return { "success": True, "data": matches }

    def get_bus_stop_info(self, stop_id: str) -> dict:
        """
        Retrieve the complete metadata for a specified bus stop.

        Args:
            stop_id (str): The unique identifier of the bus stop.

        Returns:
            dict: 
                - If found: {"success": True, "data": BusStopInfo}
                - If not found: {"success": False, "error": "Bus stop not found"}

        Constraints:
            - Bus stop with stop_id must exist.
        """
        bus_stop = self.bus_stops.get(stop_id)
        if bus_stop is None:
            return {"success": False, "error": "Bus stop not found"}

        return {"success": True, "data": bus_stop}

    def list_all_bus_stops(self) -> dict:
        """
        Retrieve all bus stops in the system with their metadata.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BusStopInfo],   # List may be empty if there are no bus stops.
            }

        Notes:
            - This function never fails unless there is a programmatic/system error,
              in which case a failure message will be returned.
        """
        try:
            stops = list(self.bus_stops.values())
            return { "success": True, "data": stops }
        except Exception as e:
            return { "success": False, "error": f"Unexpected error: {str(e)}" }

    def get_bus_stops_by_location(self, latitude: float, longitude: float, distance: float) -> dict:
        """
        Retrieve all bus stops within a certain distance (in kilometers) of a given latitude/longitude.
    
        Args:
            latitude (float): Reference latitude (degrees, -90 to 90).
            longitude (float): Reference longitude (degrees, -180 to 180).
            distance (float): Search radius in kilometers (must be > 0).
        
        Returns:
            dict: {
                "success": True,
                "data": List[BusStopInfo]  # List (possibly empty) of stops within given radius
            }
            OR
            {
                "success": False,
                "error": str
            }
        Constraints:
            - All arguments must be provided and valid.
            - Uses Haversine formula for distance.
        """
        # Validate input ranges
        if not (-90 <= latitude <= 90):
            return {"success": False, "error": "Invalid latitude value"}
        if not (-180 <= longitude <= 180):
            return {"success": False, "error": "Invalid longitude value"}
        if not (distance > 0):
            return {"success": False, "error": "Distance must be positive"}


        def haversine(lat1, lon1, lat2, lon2):
            # Earth radius in kilometers
            R = 6371.0
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        matches = []
        for stop_info in self.bus_stops.values():
            stop_lat = stop_info.get("latitude")
            stop_lon = stop_info.get("longitude")
            # Defensive: coordinates should already be valid, but check for nulls
            if stop_lat is None or stop_lon is None:
                continue
            dist = haversine(latitude, longitude, stop_lat, stop_lon)
            if dist <= distance:
                matches.append(stop_info)

        return {"success": True, "data": matches}

    def get_bus_stops_by_route_id(self, route_id: str) -> dict:
        """
        List all stops served by the specified route.

        Args:
            route_id (str): The ID of the route whose stops are to be listed.

        Returns:
            dict:
                - If route exists:
                    {
                        "success": True,
                        "data": List[BusStopInfo]  # All stops for the route (may be empty)
                    }
                - If route does not exist:
                    {
                        "success": False,
                        "error": "Route does not exist"
                    }
        Constraints:
            - Route with route_id must exist.
            - If the route's stop list contains invalid stop ids, those stops are ignored in the output.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        route_info = self.routes[route_id]
        stop_list = []
        for stop_id in route_info["list_of_stop_ids"]:
            stop_info = self.bus_stops.get(stop_id)
            if stop_info:
                stop_list.append(stop_info)
            # else: skip missing stop_id silently

        return {"success": True, "data": stop_list}

    def get_route_info(self, route_id: str) -> dict:
        """
        Retrieve details for a route including name, stop sequence, and schedule info.

        Args:
            route_id (str): The unique route identifier.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": RouteInfo  # Route metadata (name, list_of_stop_ids, schedule_info)
                }
                Failure: {
                    "success": False,
                    "error": str  # Reason (e.g., route does not exist)
                }
        Constraints:
            - The route must exist in the system (route_id in self.routes).
        """
        route_info = self.routes.get(route_id)
        if not route_info:
            return {"success": False, "error": "Route does not exist"}
        return {"success": True, "data": route_info}

    def list_all_routes(self) -> dict:
        """
        Retrieve a full list of all bus routes in the system with their metadata.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo]  # List of all route metadata (could be empty if no routes)
            }

        Constraints:
            - None. Returns all stored routes. If none exist, returns empty list.
        """
        routes_list = list(self.routes.values())
        return { "success": True, "data": routes_list }

    def get_routes_for_stop(self, stop_id: str) -> dict:
        """
        For a given bus stop (by stop_id), returns a list of all route IDs and names that serve the stop.

        Args:
            stop_id (str): The unique identifier for the bus stop.

        Returns:
            dict: {
                "success": True,
                "data": List[ { "route_id": str, "name": str } ]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The bus stop must exist in the system.
            - Only return route info for routes existing in the system.
        """
        # Check bus stop exists
        if stop_id not in self.bus_stops:
            return {"success": False, "error": "Bus stop does not exist"}

        bus_stop = self.bus_stops[stop_id]
        route_infos = []
        for route_id in bus_stop.get("associated_route_id", []):
            route = self.routes.get(route_id)
            if route:
                route_infos.append({
                    "route_id": route["route_id"],
                    "name": route["name"]
                })
            # If route does not exist, skip it (could be a data inconsistency)

        return {"success": True, "data": route_infos}

    def add_bus_stop(
        self,
        stop_id: str,
        name: str,
        latitude: float,
        longitude: float,
        associated_route_id: list
    ) -> dict:
        """
        Add a new bus stop with metadata.
    
        Args:
            stop_id (str): Unique identifier for the bus stop.
            name (str): Name of the bus stop.
            latitude (float): Geographic latitude (-90 <= latitude <= 90).
            longitude (float): Geographic longitude (-180 <= longitude <= 180).
            associated_route_id (List[str]): List of associated route_ids.
        
        Returns:
            dict: {
                "success": True,
                "message": "Bus stop <stop_id> added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - stop_id must be unique.
            - latitude/longitude must be non-null and within valid ranges.
            - associated_route_id should not be empty.
        """
        if stop_id in self.bus_stops:
            return {"success": False, "error": "stop_id already exists."}

        if latitude is None or longitude is None:
            return {"success": False, "error": "Invalid coordinates."}

        if not (isinstance(latitude, (float, int)) and -90 <= latitude <= 90):
            return {"success": False, "error": "Invalid latitude value."}

        if not (isinstance(longitude, (float, int)) and -180 <= longitude <= 180):
            return {"success": False, "error": "Invalid longitude value."}

        if not associated_route_id or not isinstance(associated_route_id, list):
            return {"success": False, "error": "Bus stop must be associated with at least one route."}

        new_stop = {
            "stop_id": stop_id,
            "name": name,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "associated_route_id": list(associated_route_id)
        }
        self.bus_stops[stop_id] = new_stop

        # Keep route metadata consistent for any already-existing associated routes.
        for route_id in associated_route_id:
            route = self.routes.get(route_id)
            if route is not None and stop_id not in route["list_of_stop_ids"]:
                route["list_of_stop_ids"].append(stop_id)

        return {"success": True, "message": f"Bus stop {stop_id} added."}

    def update_bus_stop_info(
        self, 
        stop_id: str,
        name: str = None,
        latitude: float = None,
        longitude: float = None,
        associated_route_id: list = None
    ) -> dict:
        """
        Modify a stop’s name, coordinates, or associated routes.
        At least one of the updatable fields must be provided.
        Constraints:
          - Bus stop must exist (stop_id).
          - If latitude/longitude are provided, they must not be None.
          - If associated_route_id is provided, it must be a non-empty list of valid route_id strings.
          - After the update, associated_route_id must remain non-empty (unless 'out of service' logic is separately specified).

        Args:
            stop_id (str): The unique stop id to update.
            name (str, optional): New name for the stop.
            latitude (float, optional): New latitude (must not be None if provided).
            longitude (float, optional): New longitude (must not be None if provided).
            associated_route_id (List[str], optional): New list of route_ids for this stop.

        Returns:
            dict: {
                "success": True,
                "message": "Bus stop info updated for stop_id <stop_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        """
        # Check existence
        if stop_id not in self.bus_stops:
            return {"success": False, "error": "Stop ID does not exist"}

        if not any([name is not None, latitude is not None, longitude is not None, associated_route_id is not None]):
            return {"success": False, "error": "No update fields provided"}

        stop = self.bus_stops[stop_id]
        # Update name
        if name is not None:
            stop["name"] = name

        # Update latitude
        if latitude is not None:
            if not isinstance(latitude, (int, float)) or latitude is None:
                return {"success": False, "error": "Invalid latitude value"}
            stop["latitude"] = float(latitude)

        # Update longitude
        if longitude is not None:
            if not isinstance(longitude, (int, float)) or longitude is None:
                return {"success": False, "error": "Invalid longitude value"}
            stop["longitude"] = float(longitude)

        # Update associated_route_id
        if associated_route_id is not None:
            if not isinstance(associated_route_id, list) or len(associated_route_id) == 0:
                return {"success": False, "error": "associated_route_id must be a non-empty list"}
            # Check all routes exist
            for rid in associated_route_id:
                if rid not in self.routes:
                    return {"success": False, "error": f"Route ID {rid} does not exist"}

            old_route_ids = set(stop["associated_route_id"])
            new_route_ids = set(associated_route_id)

            for rid in old_route_ids - new_route_ids:
                route = self.routes.get(rid)
                if route and stop_id in route["list_of_stop_ids"]:
                    route["list_of_stop_ids"].remove(stop_id)

            for rid in new_route_ids:
                route = self.routes.get(rid)
                if route and stop_id not in route["list_of_stop_ids"]:
                    route["list_of_stop_ids"].append(stop_id)

            stop["associated_route_id"] = associated_route_id

        # After update, enforce bus stop has at least one route
        if not stop["associated_route_id"]:
            return {"success": False, "error": "Bus stop must be associated with at least one route"}

        self.bus_stops[stop_id] = stop
        return {"success": True, "message": f"Bus stop info updated for stop_id {stop_id}"}

    def remove_bus_stop(self, stop_id: str) -> dict:
        """
        Remove a bus stop from the system, provided it does not violate
        uniqueness or association constraints.

        Args:
            stop_id (str): Unique identifier for the bus stop.

        Returns:
            dict:
                On success: 
                    {
                        "success": True,
                        "message": "Bus stop removed successfully."
                    }
                On failure: 
                    {
                        "success": False,
                        "error": <str: reason>
                    }

        Constraints:
            - Stop must exist.
            - Stop cannot be removed if still associated with any route (i.e., appears in any RouteInfo['list_of_stop_ids']).
        """
        # Check if stop exists
        if stop_id not in self.bus_stops:
            return { "success": False, "error": "Bus stop does not exist." }

        # Check for associations in any route
        for route in self.routes.values():
            if stop_id in route.get("list_of_stop_ids", []):
                return {
                    "success": False,
                    "error": "Cannot remove bus stop: still referenced in route(s)."
                }

        # Safe to remove
        del self.bus_stops[stop_id]

        return {
            "success": True,
            "message": "Bus stop removed successfully."
        }

    def add_route(
        self,
        route_id: str,
        name: str,
        list_of_stop_ids: list,
        schedule_info: str
    ) -> dict:
        """
        Add a new route to the system.

        Args:
            route_id (str): Unique identifier for the route.
            name (str): Official name of the route.
            list_of_stop_ids (list of str): Ordered list of stop_ids to be included in the route.
            schedule_info (str): String containing route schedule information.

        Returns:
            dict:
                - On success: {"success": True, "message": "Route <route_id> added."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - route_id must be unique (not present in self.routes).
            - Every stop_id in list_of_stop_ids must exist in self.bus_stops.
            - Each stop will be updated to associate with this route if not already associated.
        """
        if route_id in self.routes:
            return {"success": False, "error": "Route ID already exists."}

        # Validate all stop IDs
        missing_stops = [stop_id for stop_id in list_of_stop_ids if stop_id not in self.bus_stops]
        if missing_stops:
            return {"success": False, "error": f"Stop(s) not found: {', '.join(missing_stops)}"}

        # Construct new RouteInfo
        new_route: RouteInfo = {
            'route_id': route_id,
            'name': name,
            'list_of_stop_ids': list(list_of_stop_ids),
            'schedule_info': schedule_info
        }
        self.routes[route_id] = new_route

        # Update each BusStop with this route association
        for stop_id in list_of_stop_ids:
            stop = self.bus_stops[stop_id]
            if route_id not in stop['associated_route_id']:
                stop['associated_route_id'].append(route_id)

        return {"success": True, "message": f"Route {route_id} added."}

    def update_route_info(
        self,
        route_id: str,
        name: str = None,
        list_of_stop_ids: list = None,
        schedule_info: str = None
    ) -> dict:
        """
        Modify a route’s name, stop sequence, or schedule info.

        Args:
            route_id (str): The ID of the route to update.
            name (Optional[str]): New name for the route (if provided).
            list_of_stop_ids (Optional[List[str]]): New ordered list of stop IDs (if provided).
            schedule_info (Optional[str]): New schedule info (if provided).

        Returns:
            dict: {
                "success": True,
                "message": "Route info updated successfully"
            }
            or {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - route_id must exist.
            - If list_of_stop_ids is provided, all stop IDs must exist.
            - Maintain consistency: bus stops must have route in their associated_route_id if present in list_of_stop_ids, and remove if no longer present.
        """
        if route_id not in self.routes:
            return { "success": False, "error": "Route not found" }

        route = self.routes[route_id]
        changes_made = False

        # Update name if provided
        if name is not None:
            route['name'] = name
            changes_made = True

        # Update schedule_info if provided
        if schedule_info is not None:
            route['schedule_info'] = schedule_info
            changes_made = True

        # Update list_of_stop_ids if provided
        if list_of_stop_ids is not None:
            # Check all stop_ids exist
            invalid_stops = [sid for sid in list_of_stop_ids if sid not in self.bus_stops]
            if invalid_stops:
                return { "success": False, "error": f"Invalid stop_id(s): {invalid_stops} in list_of_stop_ids" }

            # Remember the old stop set
            old_stops = set(route['list_of_stop_ids'])
            new_stops = set(list_of_stop_ids)
            # 1. Remove route_id from any stops no longer part of the route
            for sid in old_stops - new_stops:
                if route_id in self.bus_stops[sid]['associated_route_id']:
                    self.bus_stops[sid]['associated_route_id'].remove(route_id)
            # 2. Add route_id to any new stops
            for sid in new_stops:
                if route_id not in self.bus_stops[sid]['associated_route_id']:
                    self.bus_stops[sid]['associated_route_id'].append(route_id)
            # 3. Update route's stop list
            route['list_of_stop_ids'] = list_of_stop_ids
            changes_made = True

        if changes_made:
            return { "success": True, "message": "Route info updated successfully" }
        else:
            return { "success": True, "message": "No changes made to route info" }

    def remove_route(self, route_id: str) -> dict:
        """
        Remove a route from the system, ensuring no stops are left with zero associated routes,
        unless such stops are designated 'out of service' (not handled in this schema).

        Args:
            route_id (str): The unique identifier for the route to remove.

        Returns:
            dict: {
                "success": True,
                "message": f"Route {route_id} removed."
            }
            or
            {
                "success": False,
                "error": str  # Description of error.
            }

        Constraints:
            - Cannot leave any bus stop with zero associated routes if this is the only route.
            - Route must exist.
        """
        # Check if the route exists
        if route_id not in self.routes:
            return {"success": False, "error": f"Route '{route_id}' does not exist."}

        # Collect bus stops that would be left with zero associated routes
        orphaned_stops = []
        for stop_id, stop_info in self.bus_stops.items():
            if route_id in stop_info.get('associated_route_id', []):
                if len(stop_info['associated_route_id']) == 1:
                    orphaned_stops.append({"stop_id": stop_id, "name": stop_info.get("name", "")})

        if orphaned_stops:
            stop_list = ', '.join([f"{s['stop_id']} ({s['name']})" for s in orphaned_stops])
            return {
                "success": False,
                "error": f"Cannot remove route '{route_id}' as it would leave stops without any associated route: {stop_list}"
            }

        # Proceed with removal
        # 1. Remove the route from each stop's associated_route_id list
        for stop_info in self.bus_stops.values():
            if route_id in stop_info.get("associated_route_id", []):
                stop_info["associated_route_id"] = [rid for rid in stop_info["associated_route_id"] if rid != route_id]

        # 2. Remove the route from the routes dict
        del self.routes[route_id]

        return {
            "success": True,
            "message": f"Route '{route_id}' removed."
        }

    def associate_stop_with_route(self, stop_id: str, route_id: str) -> dict:
        """
        Add a route ID to the set of associated routes for a bus stop.

        Args:
            stop_id (str): The ID of the bus stop.
            route_id (str): The ID of the route to associate with the stop.

        Returns:
            dict: {
                "success": True,
                "message": "Route <route_id> associated with stop <stop_id>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The stop and route must exist.
            - No duplicate associations are added.
        """
        if stop_id not in self.bus_stops:
            return {"success": False, "error": f"Stop ID '{stop_id}' does not exist"}
        if route_id not in self.routes:
            return {"success": False, "error": f"Route ID '{route_id}' does not exist"}

        stop_info = self.bus_stops[stop_id]
        if route_id in stop_info["associated_route_id"]:
            return {
                "success": True,
                "message": f"Route {route_id} already associated with stop {stop_id}"
            }

        stop_info["associated_route_id"].append(route_id)
        if stop_id not in self.routes[route_id]["list_of_stop_ids"]:
            self.routes[route_id]["list_of_stop_ids"].append(stop_id)
        return {
            "success": True,
            "message": f"Route {route_id} associated with stop {stop_id}"
        }

    def disassociate_stop_from_route(self, stop_id: str, route_id: str) -> dict:
        """
        Remove a route from a stop’s associated_route_id. This operation is prohibited
        if it would leave the stop without any associated routes (and there is no 'out of service' flag).

        Args:
            stop_id (str): The unique identifier for the bus stop.
            route_id (str): The route to remove from this stop's associations.

        Returns:
            dict: {
                "success": True,
                "message": "Route disassociated from stop."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Both stop_id and route_id must exist.
            - route_id must be in the stop's associated_route_id list.
            - At least one route must remain associated, otherwise, disassociation is prohibited.
        """
        # Validate bus stop existence
        stop = self.bus_stops.get(stop_id)
        if not stop:
            return { "success": False, "error": "Bus stop does not exist." }

        # Validate route existence
        route = self.routes.get(route_id)
        if not route:
            return { "success": False, "error": "Route does not exist." }

        # Validate route association
        if route_id not in stop["associated_route_id"]:
            return { "success": False, "error": "Route is not associated with the stop." }

        # Constraint: cannot remove last route
        if len(stop["associated_route_id"]) == 1:
            return { "success": False, "error": "Cannot disassociate the last route; stop must be associated with at least one route." }

        # Remove association from stop
        stop["associated_route_id"].remove(route_id)

        # Optionally, also remove stop_id from route's list_of_stop_ids if present
        if stop_id in route["list_of_stop_ids"]:
            route["list_of_stop_ids"].remove(stop_id)

        return { "success": True, "message": f"Route '{route_id}' disassociated from stop '{stop_id}'." }


class CityBusRouteManagementSystem(BaseEnv):
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

    def search_bus_stops_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_bus_stops_by_keyword', kwargs)

    def get_bus_stop_info(self, **kwargs):
        return self._call_inner_tool('get_bus_stop_info', kwargs)

    def list_all_bus_stops(self, **kwargs):
        return self._call_inner_tool('list_all_bus_stops', kwargs)

    def get_bus_stops_by_location(self, **kwargs):
        return self._call_inner_tool('get_bus_stops_by_location', kwargs)

    def get_bus_stops_by_route_id(self, **kwargs):
        return self._call_inner_tool('get_bus_stops_by_route_id', kwargs)

    def get_route_info(self, **kwargs):
        return self._call_inner_tool('get_route_info', kwargs)

    def list_all_routes(self, **kwargs):
        return self._call_inner_tool('list_all_routes', kwargs)

    def get_routes_for_stop(self, **kwargs):
        return self._call_inner_tool('get_routes_for_stop', kwargs)

    def add_bus_stop(self, **kwargs):
        return self._call_inner_tool('add_bus_stop', kwargs)

    def update_bus_stop_info(self, **kwargs):
        return self._call_inner_tool('update_bus_stop_info', kwargs)

    def remove_bus_stop(self, **kwargs):
        return self._call_inner_tool('remove_bus_stop', kwargs)

    def add_route(self, **kwargs):
        return self._call_inner_tool('add_route', kwargs)

    def update_route_info(self, **kwargs):
        return self._call_inner_tool('update_route_info', kwargs)

    def remove_route(self, **kwargs):
        return self._call_inner_tool('remove_route', kwargs)

    def associate_stop_with_route(self, **kwargs):
        return self._call_inner_tool('associate_stop_with_route', kwargs)

    def disassociate_stop_from_route(self, **kwargs):
        return self._call_inner_tool('disassociate_stop_from_route', kwargs)
