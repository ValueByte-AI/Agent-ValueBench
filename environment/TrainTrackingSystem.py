# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class TrainInfo(TypedDict):
    train_id: str
    route_id: str
    status: str
    current_location_id: str

class LocationInfo(TypedDict):
    location_id: str
    latitude: float
    longitude: float
    timestamp: float  # UNIX timestamp

class RouteInfo(TypedDict):
    route_id: str
    name: str
    schedule_id: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    stops: List[str]
    planned_time: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Trains: {train_id: TrainInfo}
        self.trains: Dict[str, TrainInfo] = {}

        # Locations: {location_id: LocationInfo}
        self.locations: Dict[str, LocationInfo] = {}

        # Routes: {route_id: RouteInfo}
        self.routes: Dict[str, RouteInfo] = {}

        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}

        # Constraints:
        # - Each train must be associated with a valid route.
        # - Location data must have a valid timestamp and coordinates.
        # - The current location of a train is updated in real time and references the most recent location record.
        # - Trains and routes must exist in the system prior to location or schedule assignment.

    def get_trains_by_route(self, route_id: str) -> dict:
        """
        Retrieve all trains currently assigned to a specific route by route_id.

        Args:
            route_id (str): The route identifier for which to list all assigned trains.

        Returns:
            dict: {
                "success": True,
                "data": List[TrainInfo]  # All TrainInfo dicts where route_id matches
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - The given route_id must exist in the system.
            - If no trains are assigned to this route, result will be an empty list.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        trains_on_route = [
            train_info for train_info in self.trains.values()
            if train_info["route_id"] == route_id
        ]

        return {"success": True, "data": trains_on_route}

    def get_train_by_id(self, train_id: str) -> dict:
        """
        Retrieve details of a specific train using its train_id.

        Args:
            train_id (str): The unique identifier for the train.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": TrainInfo  # Details of the train
                }
            On failure,
                {
                    "success": False,
                    "error": str  # Error message, e.g., train not found
                }
        Constraints:
            - The train with the given train_id must exist in the system.
        """
        train = self.trains.get(train_id)
        if train is None:
            return {"success": False, "error": "Train with given train_id does not exist"}
        return {"success": True, "data": train}

    def get_route_by_id(self, route_id: str) -> dict:
        """
        Retrieve details for a specific route by route_id.

        Args:
            route_id (str): The unique identifier for the route.

        Returns:
            dict: {
                "success": True,
                "data": RouteInfo  # Details of the requested route
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., route not found
            }
        Constraints:
            - Route must exist in the system.
        """
        if route_id not in self.routes:
            return {"success": False, "error": "Route not found"}

        return {"success": True, "data": self.routes[route_id]}

    def get_current_location_of_train(self, train_id: str) -> dict:
        """
        Retrieve the current location_id associated with the specified train.

        Args:
            train_id (str): The ID of the train whose location is to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": { "current_location_id": str }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - train_id must exist in the system.
        """
        train = self.trains.get(train_id)
        if not train:
            return { "success": False, "error": f"Train ID '{train_id}' does not exist" }

        current_location_id = train.get("current_location_id")
        return {
            "success": True,
            "data": { "current_location_id": current_location_id }
        }

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Given a location_id, retrieve the location details (latitude, longitude, timestamp).

        Args:
            location_id (str): The unique identifier for the location record.

        Returns:
            dict: 
              - On success: {"success": True, "data": LocationInfo}
              - On failure: {"success": False, "error": str} (e.g., location_id does not exist)

        Constraints:
            - The location_id must exist in the system.
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location ID does not exist"}
        return {"success": True, "data": self.locations[location_id]}

    def get_route_schedule(self, route_id: str) -> dict:
        """
        Retrieve the schedule (planned stops and times) assigned to a specific route.

        Args:
            route_id (str): The unique ID of the route.

        Returns:
            dict: {
                "success": True,
                "data": ScheduleInfo,  # If schedule found
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure
            }

        Constraints:
            - route_id must exist in the system.
            - schedule_id referenced by route must exist in self.schedules.
        """
        route = self.routes.get(route_id)
        if not route:
            return {"success": False, "error": "Route ID does not exist"}

        schedule_id = route.get("schedule_id")
        if not schedule_id:
            return {"success": False, "error": "No schedule assigned to this route"}

        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found for the route"}

        return {"success": True, "data": schedule}

    def get_train_status(self, train_id: str) -> dict:
        """
        Retrieve the operational status (on time, delayed, out of service, etc.) of a train.

        Args:
            train_id (str): The unique identifier for the train.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "train_id": str,
                    "status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Train not found"
            }

        Constraints:
            - The specified train_id must exist in the system.
        """
        train = self.trains.get(train_id)
        if not train:
            return {"success": False, "error": "Train not found"}

        return {"success": True, "data": {
            "train_id": train_id,
            "status": train["status"]
        }}

    def get_location_history_for_train(self, train_id: str) -> dict:
        """
        Retrieve the history/log of all known location records for a given train, ordered from oldest to newest.

        Args:
            train_id (str): ID of the train whose location history is to be retrieved.

        Returns:
            dict:
                - Success: {
                    "success": True,
                    "data": List[LocationInfo]  # May be empty if no history available.
                }
                - Failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g., train not found.
                }

        Constraints:
            - The train must exist in the system.
            - Only location records that exist in self.locations are returned.
        """
        if train_id not in self.trains:
            return {"success": False, "error": "Train does not exist"}

        # See if location history mapping exists; if not, assume no history
        if not hasattr(self, "train_location_history"):
            self.train_location_history = {}

        loc_id_list = self.train_location_history.get(train_id, [])
        history = []
        for loc_id in loc_id_list:
            loc = self.locations.get(loc_id)
            if loc:
                history.append(loc)

        return {"success": True, "data": history}

    def list_all_routes(self) -> dict:
        """
        Return the complete list of all routes operated in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo], # all RouteInfo entries, possibly empty if no routes are defined
            }
        """
        all_routes = list(self.routes.values())
        return {
            "success": True,
            "data": all_routes
        }

    def list_all_trains(self) -> dict:
        """
        Returns the complete list of all trains in the system with their route assignments.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TrainInfo],  # List of all trains (may be empty if none exist)
            }
        """
        result = list(self.trains.values())
        return { "success": True, "data": result }

    def update_train_location(
        self,
        train_id: str,
        latitude: float,
        longitude: float,
        timestamp: float
    ) -> dict:
        """
        Update a train's current location by recording a new real-time location and referencing it.

        Args:
            train_id (str): Train to update.
            latitude (float): New location latitude (-90 to 90).
            longitude (float): New location longitude (-180 to 180).
            timestamp (float): Unix timestamp of location record (must be non-negative and newest for this train).

        Returns:
            dict:
                success (bool): Whether the operation succeeded.
                message (str): If successful, description and new location_id.
                error (str): If failed, explanation of error.

        Constraints:
            - Train must exist.
            - Latitude must be between -90 and 90; longitude between -180 and 180.
            - Timestamp must be non-negative and not older than previous location.
            - A new LocationInfo is inserted and referenced by the train.
        """
        # Check that the train exists
        train = self.trains.get(train_id)
        if not train:
            return { "success": False, "error": "Train does not exist" }

        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0):
            return { "success": False, "error": "Invalid latitude; must be between -90 and 90" }
        if not (-180.0 <= longitude <= 180.0):
            return { "success": False, "error": "Invalid longitude; must be between -180 and 180" }
        if not (isinstance(timestamp, (float, int)) and timestamp >= 0):
            return { "success": False, "error": "Invalid timestamp; must be non-negative" }

        # Enforce that the timestamp is newer than previous location
        prev_location_id = train.get("current_location_id")
        if prev_location_id:
            prev_location = self.locations.get(prev_location_id)
            if prev_location and timestamp < prev_location["timestamp"]:
                return { "success": False, "error": "Timestamp must not be older than current location timestamp" }

        # Generate a new unique location_id
        # Use train_id + timestamp string for uniqueness
        location_id = f"{train_id}-{str(uuid.uuid4())}"

        # Construct new location entry
        location_info = {
            "location_id": location_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": float(timestamp),
        }
        self.locations[location_id] = location_info

        # Update train to reference new location
        self.trains[train_id]["current_location_id"] = location_id

        return {
            "success": True,
            "message": f"Train location updated. New location_id: {location_id}"
        }

    def add_location_record(self, train_id: str, latitude: float, longitude: float, timestamp: float) -> dict:
        """
        Record a new location entry for a train, specifying latitude, longitude, and timestamp.
        Updates the train's current_location_id to point to this new location.

        Args:
            train_id (str): ID of the train to update
            latitude (float): Latitude of the location (should be in [-90, 90])
            longitude (float): Longitude of the location (should be in [-180, 180])
            timestamp (float): UNIX timestamp of the location reading

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Location record added for train {train_id} (location_id: {location_id})",
                    "location_id": str
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - train_id must exist in the system
            - latitude/longitude/timestamp must be valid types
            - Updates train's current_location_id to new location
        """
        # Validate train_id
        if train_id not in self.trains:
            return {"success": False, "error": f"Train with ID '{train_id}' does not exist."}

        # Basic coordinate and timestamp sanity checks
        if not (isinstance(latitude, float) or isinstance(latitude, int)):
            return {"success": False, "error": "Latitude must be a float."}
        if not (isinstance(longitude, float) or isinstance(longitude, int)):
            return {"success": False, "error": "Longitude must be a float."}
        if not (isinstance(timestamp, float) or isinstance(timestamp, int)):
            return {"success": False, "error": "Timestamp must be a float (UNIX time)."}

        # Optional: check lat/lon ranges; skip for generality unless strict validation needed

        # Generate new, unique location_id
        location_id = str(uuid.uuid4())

        # Create the location record
        location_info = {
            "location_id": location_id,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "timestamp": float(timestamp)
        }
        self.locations[location_id] = location_info

        # Update train's current location
        self.trains[train_id]["current_location_id"] = location_id

        return {
            "success": True,
            "message": f"Location record added for train {train_id} (location_id: {location_id})",
            "location_id": location_id
        }

    def assign_train_to_route(self, train_id: str, route_id: str) -> dict:
        """
        Assign a train to a valid route, updating the train's route_id.

        Args:
            train_id (str): The ID of the train to assign.
            route_id (str): The ID of the route to assign the train to.

        Returns:
            dict: {
                "success": True,
                "message": "Train <train_id> assigned to route <route_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The train and the route must both already exist in the system.
            - Updates the train's route_id.
        """
        if train_id not in self.trains:
            return { "success": False, "error": "Train does not exist" }
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist" }

        self.trains[train_id]["route_id"] = route_id
        return {
            "success": True,
            "message": f"Train {train_id} assigned to route {route_id}."
        }

    def add_route(self, route_id: str, name: str, schedule_id: str) -> dict:
        """
        Add a new route to the system.

        Args:
            route_id (str): Unique identifier for the new route.
            name (str): Human-readable/official name for the route.
            schedule_id (str): The ID of the existing schedule to associate.

        Returns:
            dict: {
                "success": True,
                "message": "Route <route_id> added successfully."
            }
            OR
            dict: {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - route_id must not already exist.
            - schedule_id must exist.
        """
        if route_id in self.routes:
            return { "success": False, "error": "Route ID already exists." }
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule ID does not exist." }

        route_info: RouteInfo = {
            "route_id": route_id,
            "name": name,
            "schedule_id": schedule_id
        }
        self.routes[route_id] = route_info

        return {"success": True, "message": f"Route {route_id} added successfully."}

    def add_schedule(self, schedule_id: str, stops: list, planned_time: list) -> dict:
        """
        Create a new schedule in the system with a unique schedule_id, a list of stops, and corresponding planned times.

        Args:
            schedule_id (str): Unique identifier for the schedule.
            stops (list[str]): List of stop identifiers.
            planned_time (list[str]): List of planned times for each stop.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule <schedule_id> created."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - schedule_id must not already exist.
            - stops and planned_time must be lists of equal non-zero length.
        """
        # Validate unique schedule id
        if schedule_id in self.schedules:
            return {"success": False, "error": f"Schedule {schedule_id} already exists."}

        # Basic validation
        if not isinstance(stops, list) or not isinstance(planned_time, list):
            return {"success": False, "error": "stops and planned_time must be lists."}
        if len(stops) == 0 or len(planned_time) == 0:
            return {"success": False, "error": "stops and planned_time cannot be empty."}
        if len(stops) != len(planned_time):
            return {"success": False, "error": "stops and planned_time lists must have the same length."}

        self.schedules[schedule_id] = {
            "schedule_id": schedule_id,
            "stops": stops,
            "planned_time": planned_time
        }
        return {"success": True, "message": f"Schedule {schedule_id} created."}

    def update_train_status(self, train_id: str, new_status: str) -> dict:
        """
        Change a train's operational status (e.g., from "on time" to "delayed").

        Args:
            train_id (str): ID of the train to update status for.
            new_status (str): The new operational status for the train.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message if status update is successful
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., train not found)
            }

        Constraints:
            - train_id must exist in self.trains.
            - Status string can be any value. No restriction enforced here.
        """
        train = self.trains.get(train_id)
        if train is None:
            return { "success": False, "error": "Train ID not found" }
        train["status"] = new_status
        return { "success": True, "message": f"Status of train {train_id} updated to '{new_status}'" }

    def update_schedule_for_route(self, route_id: str, schedule_id: str) -> dict:
        """
        Update the schedule assignment for a route.

        Args:
            route_id (str): The ID of the route to update.
            schedule_id (str): The ID of the new schedule to assign to the route.

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "Schedule updated for route <route_id>."
                }
                On failure: {
                    "success": False, 
                    "error": <error description>
                }

        Constraints:
            - The given route_id must exist in the system.
            - The given schedule_id must exist in the system.
        """
        if route_id not in self.routes:
            return { "success": False, "error": f"Route '{route_id}' does not exist." }
        if schedule_id not in self.schedules:
            return { "success": False, "error": f"Schedule '{schedule_id}' does not exist." }

        self.routes[route_id]['schedule_id'] = schedule_id

        return { "success": True, "message": f"Schedule updated for route {route_id}." }

    def remove_train(self, train_id: str) -> dict:
        """
        Remove a train from service and from the system registry.

        Args:
            train_id (str): Unique ID of the train to be removed.

        Returns:
            dict:
                { "success": True, "message": "Train <train_id> removed from system registry." }
                or
                { "success": False, "error": "Train does not exist." }

        Constraints:
            - The train must exist in the system registry.
            - This operation does not affect location history or schedules;
              it only removes the train from the train registry.
        """
        if train_id not in self.trains:
            return { "success": False, "error": "Train does not exist." }

        del self.trains[train_id]
        return { "success": True, "message": f"Train {train_id} removed from system registry." }

    def remove_route(self, route_id: str) -> dict:
        """
        Remove a route from the system if no trains are assigned to it.
    
        Args:
            route_id (str): The route ID to remove.
    
        Returns:
            dict:
                - success=True and message on success.
                - success=False and error on failure (nonexistent route or route has dependent trains).
    
        Constraints:
            - Cannot remove route if any train is assigned to it.
            - Route must exist.
        """
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist" }

        # Check for dependent trains
        dependent_trains = [
            train_id for train_id, train_info in self.trains.items()
            if train_info["route_id"] == route_id
        ]
        if dependent_trains:
            return {
                "success": False,
                "error": (
                    f"Route cannot be removed: trains assigned to this route: {dependent_trains}"
                )
            }

        del self.routes[route_id]
        return { "success": True, "message": f"Route {route_id} removed successfully" }

    def remove_location_record(self, location_id: str) -> dict:
        """
        Remove a location record from the system, ensuring no train currently references it.

        Args:
            location_id (str): The identifier of the location record to remove.

        Returns:
            dict:
                - {"success": True, "message": "Location record <location_id> removed."}
                - {"success": False, "error": "<error message>"}

        Constraints:
            - The provided location_id must exist in the system.
            - The location record can only be removed if it is not referenced by any train's current_location_id.
        """
        if location_id not in self.locations:
            return { "success": False, "error": f"Location record '{location_id}' does not exist." }

        # Check for referential integrity: is this location in use?
        for train in self.trains.values():
            if train.get("current_location_id") == location_id:
                return {
                    "success": False,
                    "error": f"Cannot remove location record '{location_id}' because it is currently referenced by train '{train['train_id']}'."
                }

        # Safe to remove
        del self.locations[location_id]
        return {
            "success": True,
            "message": f"Location record '{location_id}' removed."
        }


class TrainTrackingSystem(BaseEnv):
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
        history = getattr(env, "train_location_history", {})
        if isinstance(history, str):
            normalized_history = {}
            location_ids = list(getattr(env, "locations", {}).keys())
            for train_id in getattr(env, "trains", {}).keys():
                match = re.search(rf"{re.escape(train_id)}\s*:\s*(.*?)(?=(?:[A-Za-z0-9_-]+\s*:)|$)", history)
                if not match:
                    continue
                segment = match.group(1)
                found = []
                for location_id in location_ids:
                    pos = segment.find(location_id)
                    if pos != -1:
                        found.append((pos, location_id))
                if found:
                    normalized_history[train_id] = [location_id for _, location_id in sorted(found)]
            env.train_location_history = normalized_history

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

    def get_trains_by_route(self, **kwargs):
        return self._call_inner_tool('get_trains_by_route', kwargs)

    def get_train_by_id(self, **kwargs):
        return self._call_inner_tool('get_train_by_id', kwargs)

    def get_route_by_id(self, **kwargs):
        return self._call_inner_tool('get_route_by_id', kwargs)

    def get_current_location_of_train(self, **kwargs):
        return self._call_inner_tool('get_current_location_of_train', kwargs)

    def get_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_location_by_id', kwargs)

    def get_route_schedule(self, **kwargs):
        return self._call_inner_tool('get_route_schedule', kwargs)

    def get_train_status(self, **kwargs):
        return self._call_inner_tool('get_train_status', kwargs)

    def get_location_history_for_train(self, **kwargs):
        return self._call_inner_tool('get_location_history_for_train', kwargs)

    def list_all_routes(self, **kwargs):
        return self._call_inner_tool('list_all_routes', kwargs)

    def list_all_trains(self, **kwargs):
        return self._call_inner_tool('list_all_trains', kwargs)

    def update_train_location(self, **kwargs):
        return self._call_inner_tool('update_train_location', kwargs)

    def add_location_record(self, **kwargs):
        return self._call_inner_tool('add_location_record', kwargs)

    def assign_train_to_route(self, **kwargs):
        return self._call_inner_tool('assign_train_to_route', kwargs)

    def add_route(self, **kwargs):
        return self._call_inner_tool('add_route', kwargs)

    def add_schedule(self, **kwargs):
        return self._call_inner_tool('add_schedule', kwargs)

    def update_train_status(self, **kwargs):
        return self._call_inner_tool('update_train_status', kwargs)

    def update_schedule_for_route(self, **kwargs):
        return self._call_inner_tool('update_schedule_for_route', kwargs)

    def remove_train(self, **kwargs):
        return self._call_inner_tool('remove_train', kwargs)

    def remove_route(self, **kwargs):
        return self._call_inner_tool('remove_route', kwargs)

    def remove_location_record(self, **kwargs):
        return self._call_inner_tool('remove_location_record', kwargs)
