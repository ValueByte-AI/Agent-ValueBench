# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# --- Entity TypedDicts ---

class TrainInfo(TypedDict):
    train_id: str
    train_type: str
    capacity: int
    assigned_route_id: str

class RouteInfo(TypedDict):
    route_id: str
    origin_station_id: str
    destination_station_id: str
    station_sequence: List[str]  # Ordered list of station_ids

class StationInfo(TypedDict):
    station_id: str
    name: str
    location: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    train_id: str
    date: str  # Could be more strict, e.g., datetime
    departure_times: List[str]
    arrival_times: List[str]
    active: bool

class RouteAssignmentInfo(TypedDict):
    train_id: str
    route_id: str
    schedule_id: str

# --- Environment Class ---

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for managing trains, routes, stations, schedules, and assignments.
        """

        # Trains: {train_id: TrainInfo}
        self.trains: Dict[str, TrainInfo] = {}

        # Routes: {route_id: RouteInfo}
        self.routes: Dict[str, RouteInfo] = {}

        # Stations: {station_id: StationInfo}
        self.stations: Dict[str, StationInfo] = {}

        # Schedules (Timetables): {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}

        # Route Assignments: {schedule_id: RouteAssignmentInfo}
        self.route_assignments: Dict[str, RouteAssignmentInfo] = {}

        # Constraints:
        # - Only trains with schedules marked as "active" for the requested date are considered available.
        # - Each route must have valid origin and destination stations.
        # - Trains cannot be assigned to multiple routes at the same time and date.
        # - Departure and arrival times in schedules must match route station sequence.

    def _find_route_assignment_entry(self, schedule_id: str):
        """
        Return the underlying route assignment storage key plus the assignment payload
        for a given schedule_id.

        Historical case data sometimes stores route_assignments keyed by an arbitrary
        identifier (for example "RA-1") instead of the schedule_id itself. All tools
        should therefore resolve assignments by the embedded schedule_id field rather
        than assuming the dict key matches the schedule_id.
        """
        if schedule_id in self.route_assignments:
            return schedule_id, self.route_assignments[schedule_id]

        for assignment_key, assignment in self.route_assignments.items():
            if assignment.get("schedule_id") == schedule_id:
                return assignment_key, assignment

        return None, None

    def _refresh_train_assigned_route(self, train_id: str):
        if train_id not in self.trains:
            return

        for assignment in self.route_assignments.values():
            if assignment["train_id"] == train_id:
                self.trains[train_id]["assigned_route_id"] = assignment["route_id"]
                return

        self.trains[train_id]["assigned_route_id"] = ""

    def get_station_by_name(self, station_name: str) -> dict:
        """
        Retrieve station_id and details given a station name.

        Args:
            station_name (str): The name of the station to look up (case-sensitive, exact match).

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": StationInfo,  # Full info of the first station matching the name
                }
                On failure,
                {
                    "success": False,
                    "error": str,  # If not found, "No station found with the given name"
                }

        Notes:
            - If multiple stations share the same name, only the first match found is returned.
            - Match is case-sensitive.
        """
        for station in self.stations.values():
            if station["name"] == station_name:
                return {"success": True, "data": station}
        return {"success": False, "error": "No station found with the given name"}

    def get_route_by_origin_and_destination(self, origin_station_id: str, destination_station_id: str) -> dict:
        """
        Find all route_ids where the origin and destination station IDs match the inputs.

        Args:
            origin_station_id (str): The station_id representing the origin station.
            destination_station_id (str): The station_id representing the destination station.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[str]  # list of route_ids where both origin and destination match
                }

        Notes:
            - If no route matches, returns an empty list in the "data" field.
            - Does not check if station_id values are valid stations; only matches routes.
        """
        route_ids = [
            route_id
            for route_id, route_info in self.routes.items()
            if route_info["origin_station_id"] == origin_station_id
            and route_info["destination_station_id"] == destination_station_id
        ]
        return { "success": True, "data": route_ids }

    def list_routes(self) -> dict:
        """
        Retrieve the list of all defined routes in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo]
            }
            If there are no routes, 'data' will be an empty list.

        Constraints:
            - None (all routes are returned; their validity is not checked in this method).
        """
        route_list = list(self.routes.values())
        return { "success": True, "data": route_list }

    def get_trains_assigned_to_route(self, route_id: str) -> dict:
        """
        Get all train_ids that are assigned to a given route via route assignments.

        Args:
            route_id (str): The route ID for which to retrieve assigned trains.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of train_ids assigned to the given route (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. route does not exist
            }

        Constraints:
            - The given route_id must exist in the system.
        """
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist." }

        train_ids = [
            assignment["train_id"]
            for assignment in self.route_assignments.values()
            if assignment["route_id"] == route_id
        ]

        return { "success": True, "data": train_ids }

    def get_active_schedules_for_train_by_date(self, train_id: str, date: str) -> dict:
        """
        List all active schedules (schedule_ids and full details) for the given train on the specified date.

        Args:
            train_id (str): The unique identifier of the train.
            date (str): The date string for which to list schedules.

        Returns:
            dict:
                {
                  "success": True,
                  "data": List[ScheduleInfo],  # List of all matching active schedules (may be empty)
                }
            or
                {
                  "success": False,
                  "error": str  # Reason train not found or other failure
                }

        Constraints:
            - Only schedules for this train, on this date, with 'active' == True are returned.
            - If train_id does not exist, operation fails.
        """
        if train_id not in self.trains:
            return {"success": False, "error": "Train not found"}

        matching_schedules = [
            schedule for schedule in self.schedules.values()
            if (schedule["train_id"] == train_id
                and schedule["date"] == date
                and schedule["active"])
        ]
        return {"success": True, "data": matching_schedules}

    def get_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Return the schedule details for a given schedule_id.

        Args:
            schedule_id (str): The unique identifier for the desired schedule.

        Returns:
            dict: {
                "success": True,
                "data": ScheduleInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Error cases:
            - If the schedule_id does not exist, returns success: False with an error message.
        """
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            return { "success": False, "error": "Schedule ID does not exist" }
        return { "success": True, "data": schedule }

    def get_route_assignment_by_schedule(self, schedule_id: str) -> dict:
        """
        Retrieve the RouteAssignmentInfo for a given schedule_id.

        Args:
            schedule_id (str): The unique identifier for the schedule.

        Returns:
            dict: {
                "success": True,
                "data": RouteAssignmentInfo  # The train-route-schedule assignment
            }
            or
            {
                "success": False,
                "error": "Route assignment for the given schedule_id does not exist"
            }

        Constraints:
            - The route assignment for the given schedule_id must exist in the system.
        """
        _, assignment = self._find_route_assignment_entry(schedule_id)
        if assignment is None:
            return {
                "success": False,
                "error": "Route assignment for the given schedule_id does not exist"
            }
        return {
            "success": True,
            "data": assignment
        }

    def get_train_info(self, train_id: str) -> dict:
        """
        Retrieve the operational details of a train by train_id.

        Args:
            train_id (str): Unique train identifier.

        Returns:
            dict: {
                "success": True,
                "data": TrainInfo  # If train is found
            }
            or
            {
                "success": False,
                "error": str  # If not found
            }

        Constraints:
            - train_id must exist in the system.
            - No modification to system state.
        """
        train_info = self.trains.get(train_id)
        if train_info is None:
            return {"success": False, "error": "Train not found"}
        return {"success": True, "data": train_info}

    def list_trains(self) -> dict:
        """
        Get all trains registered in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[TrainInfo],  # List of all trains (may be empty if none registered)
            }

        Constraints:
            - No constraints. This operation lists all existing trains.
        """
        trains_list = list(self.trains.values())
        return { "success": True, "data": trains_list }

    def list_stations(self) -> dict:
        """
        Retrieve the full list of all available stations.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[StationInfo]  # List may be empty if no stations exist
            }
        """
        return {
            "success": True,
            "data": list(self.stations.values())
        }

    def check_route_station_sequence_consistency(self, route_id: str, schedule_id: str) -> dict:
        """
        Verify that the given route's station sequence matches the number of 
        departure/arrival times in the specified schedule.

        Args:
            route_id (str): The route to check.
            schedule_id (str): The schedule to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "consistent": bool,
                    "reason": str
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints checked:
        - Route must exist.
        - Schedule must exist.
        - Schedule must be assigned to the given route.
        - The station_sequence length must match both departure_times and arrival_times length.
        """

        if route_id not in self.routes:
            return { "success": False, "error": "Route not found." }
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule not found." }
    
        # Check assignment: schedule_id must map to route_id in self.route_assignments
        _, assign_info = self._find_route_assignment_entry(schedule_id)
        if not assign_info or assign_info["route_id"] != route_id:
            return {
                "success": False,
                "error": "Schedule is not assigned to the given route."
            }

        route = self.routes[route_id]
        sched = self.schedules[schedule_id]

        station_count = len(route["station_sequence"])
        departure_count = len(sched["departure_times"])
        arrival_count = len(sched["arrival_times"])

        if station_count == departure_count == arrival_count:
            return {
                "success": True,
                "data": {
                    "consistent": True,
                    "reason": "Station sequence count matches both departure and arrival times."
                }
            }
        # If not equal, explain what mismatches.
        mismatches = []
        if station_count != departure_count:
            mismatches.append(
                f"station_sequence count ({station_count}) != departure_times count ({departure_count})"
            )
        if station_count != arrival_count:
            mismatches.append(
                f"station_sequence count ({station_count}) != arrival_times count ({arrival_count})"
            )
        if departure_count != arrival_count:
            mismatches.append(
                f"departure_times count ({departure_count}) != arrival_times count ({arrival_count})"
            )

        return {
            "success": True,
            "data": {
                "consistent": False,
                "reason": "; ".join(mismatches)
            }
        }

    def get_schedules_by_route_and_date(self, route_id: str, date: str) -> dict:
        """
        Return all active schedules assigned to a specific route for a specific date.

        Args:
            route_id (str): ID of the route.
            date (str): Date string to match schedules.

        Returns:
            dict:
                - On success: {"success": True, "data": List[ScheduleInfo]}
                - On error: {"success": False, "error": str}
    
        Constraints:
            - Only schedules that are 'active' and assigned to route_id (via route_assignments)
              are returned.
            - The schedule date must match.
            - The route must exist.
        """

        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist" }

        matching_schedule_ids = [
            assignment["schedule_id"]
            for assignment in self.route_assignments.values()
            if assignment["route_id"] == route_id
        ]

        # Filter schedules for given date and active status
        result = []
        for schedule_id in matching_schedule_ids:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                continue
            if schedule["active"] and schedule["date"] == date:
                result.append(schedule)

        return { "success": True, "data": result }

    def add_station(self, station_id: str, name: str, location: str) -> dict:
        """
        Add a new station to the system.

        Args:
            station_id (str): Unique identifier for the station.
            name (str): Name of the station.
            location (str): Location description or code for the station.

        Returns:
            dict:
                On success: { "success": True, "message": "Station <station_id> added." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - station_id must be unique (not already present in self.stations).
            - station_id, name, and location should not be empty.
        """
        if not station_id or not isinstance(station_id, str):
            return { "success": False, "error": "station_id must be a non-empty string." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Station name must be a non-empty string." }
        if not location or not isinstance(location, str):
            return { "success": False, "error": "Station location must be a non-empty string." }
        if station_id in self.stations:
            return { "success": False, "error": f"Station with ID '{station_id}' already exists." }

        new_station: StationInfo = {
            "station_id": station_id,
            "name": name,
            "location": location
        }
        self.stations[station_id] = new_station

        return { "success": True, "message": f"Station {station_id} added." }

    def update_station(self, station_id: str, name: str = None, location: str = None) -> dict:
        """
        Modify the details (name/location) of an existing station.

        Args:
            station_id (str): The unique ID of the station to update.
            name (str, optional): The new name for the station.
            location (str, optional): The new location for the station.

        Returns:
            dict: 
                { "success": True, "message": "Station updated successfully." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - The station must exist.
            - At least one of (name, location) must be provided.
            - Name/location, if provided, must be non-empty strings.
        """
        if station_id not in self.stations:
            return { "success": False, "error": "Station does not exist." }

        if name is None and location is None:
            return { "success": False, "error": "No update fields provided. Specify at least one of name or location." }
    
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return { "success": False, "error": "Station name must be a non-empty string." }
            self.stations[station_id]["name"] = name.strip()

        if location is not None:
            if not isinstance(location, str) or not location.strip():
                return { "success": False, "error": "Station location must be a non-empty string." }
            self.stations[station_id]["location"] = location.strip()

        return { "success": True, "message": "Station updated successfully." }

    def add_route(
        self,
        route_id: str,
        origin_station_id: str,
        destination_station_id: str,
        station_sequence: list
    ) -> dict:
        """
        Add a new route with origin, destination, and station sequence.

        Args:
            route_id (str): Unique route identifier.
            origin_station_id (str): Station ID of the origin station.
            destination_station_id (str): Station ID of the destination station.
            station_sequence (List[str]): Ordered list of station IDs from origin to destination.

        Returns:
            dict: Success or failure with error description.
            Success: { "success": True, "message": "Route <route_id> added." }
            Failure: { "success": False, "error": <reason> }

        Constraints:
            - route_id must be unique.
            - origin_station_id and destination_station_id must exist.
            - All items in station_sequence must be valid station IDs.
            - station_sequence must start with origin_station_id and end with destination_station_id.
            - Stations in station_sequence must not be repeated.
        """
        # Check route_id uniqueness
        if route_id in self.routes:
            return { "success": False, "error": f"Route ID '{route_id}' already exists." }
    
        # Check origin and destination station IDs existence
        if origin_station_id not in self.stations:
            return { "success": False, "error": f"Origin station ID '{origin_station_id}' does not exist." }
        if destination_station_id not in self.stations:
            return { "success": False, "error": f"Destination station ID '{destination_station_id}' does not exist." }

        # Check station_sequence is a non-empty list
        if not isinstance(station_sequence, list) or len(station_sequence) < 2:
            return { "success": False, "error": "Station sequence must be a list with at least origin and destination." }

        # Check that station_sequence starts with origin and ends with destination
        if station_sequence[0] != origin_station_id:
            return { "success": False, "error": "Station sequence must start with the origin station ID." }
        if station_sequence[-1] != destination_station_id:
            return { "success": False, "error": "Station sequence must end with the destination station ID." }

        # Check all stations exist and no duplicates
        station_ids_set = set()
        for station_id in station_sequence:
            if station_id not in self.stations:
                return { "success": False, "error": f"Station ID '{station_id}' in sequence does not exist." }
            if station_id in station_ids_set:
                return { "success": False, "error": f"Station ID '{station_id}' is repeated in the sequence." }
            station_ids_set.add(station_id)

        # Add the route
        route_info = {
            "route_id": route_id,
            "origin_station_id": origin_station_id,
            "destination_station_id": destination_station_id,
            "station_sequence": station_sequence
        }
        self.routes[route_id] = route_info

        return { "success": True, "message": f"Route '{route_id}' added." }

    def update_route(
        self,
        route_id: str,
        origin_station_id: str = None,
        destination_station_id: str = None,
        station_sequence: List[str] = None
    ) -> dict:
        """
        Edit an existing route's endpoints or station sequence.

        Args:
            route_id (str): The ID of the route to update.
            origin_station_id (str, optional): New origin station ID.
            destination_station_id (str, optional): New destination station ID.
            station_sequence (List[str], optional): New ordered list of station IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Route <route_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Route must exist.
            - Any provided station IDs must exist.
            - If station_sequence is provided, all IDs must be valid stations,
              must start with origin_station_id (if provided, else current origin), 
              and end with destination_station_id (if provided, else current destination).
            - At least one field must be provided to update.
        """
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist." }

        route = self.routes[route_id]
        updates = {}

        # Check if any update is requested
        if origin_station_id is None and destination_station_id is None and station_sequence is None:
            return { "success": False, "error": "No updates specified." }

        # Validate new origin/destination stations if provided
        if origin_station_id is not None:
            if origin_station_id not in self.stations:
                return { "success": False, "error": "Origin station ID does not exist." }
            updates["origin_station_id"] = origin_station_id
        else:
            origin_station_id = route["origin_station_id"]

        if destination_station_id is not None:
            if destination_station_id not in self.stations:
                return { "success": False, "error": "Destination station ID does not exist." }
            updates["destination_station_id"] = destination_station_id
        else:
            destination_station_id = route["destination_station_id"]

        # Validate station sequence, if provided
        if station_sequence is not None:
            # All must exist
            for sid in station_sequence:
                if sid not in self.stations:
                    return { "success": False, "error": f"Station ID '{sid}' in sequence does not exist." }
            # Must start with origin_station_id and end with destination_station_id
            if station_sequence[0] != origin_station_id:
                return { "success": False,
                         "error": "Station sequence must start with the origin station." }
            if station_sequence[-1] != destination_station_id:
                return { "success": False,
                         "error": "Station sequence must end with the destination station." }
            updates["station_sequence"] = station_sequence

        # Apply updates
        self.routes[route_id].update(updates)

        return { "success": True, "message": f"Route {route_id} updated successfully." }

    def assign_train_to_route_and_schedule(
        self,
        train_id: str,
        route_id: str,
        schedule_id: str
    ) -> dict:
        """
        Create a new RouteAssignment linking a train, route, and schedule.

        Args:
            train_id (str): The train to assign.
            route_id (str): The route to assign to.
            schedule_id (str): The schedule for the assignment.

        Returns:
            dict: 
                Success: { "success": True, "message": "Train successfully assigned to route and schedule." }
                Failure: { "success": False, "error": <error message> }

        Constraints:
            - All IDs must exist (train, route, schedule).
            - The schedule must be 'active'.
            - The schedule's train_id must match the provided train_id.
            - The train must NOT already be assigned to another route on the SAME DATE.
            - The schedule_id must not already have an assignment.
        """
        # Existence checks
        if train_id not in self.trains:
            return { "success": False, "error": "Train does not exist." }
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist." }
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule does not exist." }
    
        schedule = self.schedules[schedule_id]

        # Schedule must be active
        if not schedule.get("active", False):
            return { "success": False, "error": "Schedule is not active." }

        # Schedule's train_id must match the specified train_id
        if schedule["train_id"] != train_id:
            return { "success": False, "error": "Schedule train_id does not match the specified train_id." }

        # Check if this schedule_id already has an assignment
        existing_assignment_key, _ = self._find_route_assignment_entry(schedule_id)
        if existing_assignment_key is not None:
            return { "success": False, "error": "Schedule is already assigned to a train/route." }

        # The train cannot be assigned to another route at the same date
        # Find all assignments for this train at schedule.date
        target_date = schedule["date"]
        for ra in self.route_assignments.values():
            # Get the schedule of this assignment
            ra_train_id = ra["train_id"]
            ra_schedule_id = ra["schedule_id"]
            # Defensive: verify referenced schedule exists
            ra_schedule = self.schedules.get(ra_schedule_id)
            if ra_train_id == train_id and ra_schedule and ra_schedule["date"] == target_date:
                return { "success": False, "error": "Train is already assigned to another route on the same date." }

        # Additional constraint: route_id must be real (already checked), but we could ensure route station sequence
        # matches schedule times here if needed (out of scope for assignment only).

        # All checks pass: create RouteAssignment
        self.route_assignments[schedule_id] = {
            "train_id": train_id,
            "route_id": route_id,
            "schedule_id": schedule_id,
        }

        # Also update the train's assigned_route_id mirror field.
        self._refresh_train_assigned_route(train_id)

        return { "success": True, "message": "Train successfully assigned to route and schedule." }

    def unassign_train_from_route(self, schedule_id: str) -> dict:
        """
        Remove a route assignment for a train given the schedule_id.

        Args:
            schedule_id (str): The ID of the schedule (and thus the assignment) to remove.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Train unassigned from route for schedule <schedule_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - schedule_id must exist in route_assignments.
            - No operation if assignment does not exist.
        """
        assignment_key, _ = self._find_route_assignment_entry(schedule_id)
        if assignment_key is None:
            return { "success": False, "error": f"No route assignment found for schedule_id: {schedule_id}" }

        removed_assignment = self.route_assignments.pop(assignment_key)
        train_id = removed_assignment["train_id"]

        self._refresh_train_assigned_route(train_id)
        return {
            "success": True,
            "message": f"Train unassigned from route for schedule {schedule_id}."
        }

    def add_train(
        self,
        train_id: str,
        train_type: str,
        capacity: int,
        assigned_route_id: str = ""
    ) -> dict:
        """
        Register a new train with operational details.

        Args:
            train_id (str): Unique identifier for the train.
            train_type (str): Type of the train (e.g., 'express', 'local').
            capacity (int): Seating/passenger capacity. Must be positive integer.
            assigned_route_id (str, optional): The route to assign this train to (may be empty or blank for unassigned).

        Returns:
            dict: {
                "success": True,
                "message": "Train registered successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - train_id must be unique.
            - capacity must be positive.
            - If assigned_route_id is provided (non-empty), it must exist in self.routes.
        """
        if not train_id or not isinstance(train_id, str):
            return {"success": False, "error": "train_id must be a non-empty string."}
        if train_id in self.trains:
            return {"success": False, "error": "A train with this train_id already exists."}
        if not isinstance(capacity, int) or capacity <= 0:
            return {"success": False, "error": "Capacity must be a positive integer."}
        if assigned_route_id and assigned_route_id not in self.routes:
            return {"success": False, "error": "Assigned route does not exist."}

        train_info = {
            "train_id": train_id,
            "train_type": train_type,
            "capacity": capacity,
            "assigned_route_id": assigned_route_id
        }
        self.trains[train_id] = train_info
        return {"success": True, "message": "Train registered successfully."}

    def update_train(
        self,
        train_id: str,
        train_type: str = None,
        capacity: int = None,
        assigned_route_id: str = None
    ) -> dict:
        """
        Change properties of a train: train_type, capacity, assigned_route_id.

        Args:
            train_id (str): The ID of the train to update. Must exist.
            train_type (str, optional): New train type.
            capacity (int, optional): New capacity. Must be positive.
            assigned_route_id (str, optional): New route to assign. Must exist as a route.

        Returns:
            dict: {
                "success": True,
                "message": "Train updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Train must exist.
            - If assigned_route_id is provided, it must exist as a route.
            - If capacity is provided, must be positive integer.
            - At least one of the updatable fields must be provided.
        """
        # Check train exists
        if train_id not in self.trains:
            return {"success": False, "error": "Train does not exist."}

        if train_type is None and capacity is None and assigned_route_id is None:
            return {"success": False, "error": "No fields provided to update."}

        # Validate assigned_route_id if being updated
        if assigned_route_id is not None:
            if assigned_route_id not in self.routes:
                return {"success": False, "error": "Assigned route does not exist."}

        # Validate capacity if being updated
        if capacity is not None:
            if not isinstance(capacity, int) or capacity <= 0:
                return {"success": False, "error": "Capacity must be a positive integer."}

        # Perform update
        train = self.trains[train_id]
        if train_type is not None:
            train["train_type"] = train_type
        if capacity is not None:
            train["capacity"] = capacity
        if assigned_route_id is not None:
            train["assigned_route_id"] = assigned_route_id

        self.trains[train_id] = train
        return {"success": True, "message": "Train updated successfully."}

    def add_schedule(
        self,
        schedule_id: str,
        train_id: str,
        date: str,
        departure_times: list,
        arrival_times: list,
        active: bool,
    ) -> dict:
        """
        Create a new schedule (timetable) entry for the given train.

        Args:
            schedule_id (str): Unique identifier for this schedule.
            train_id (str): ID of the train to which this schedule applies.
            date (str): Date for this schedule (format: e.g., 'YYYY-MM-DD').
            departure_times (List[str]): List of departure times per station (order matches route station sequence).
            arrival_times (List[str]): List of arrival times per station (order matches route station sequence).
            active (bool): Whether this schedule is active.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule added successfully."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - schedule_id must be unique.
            - train_id must exist.
            - The lengths of departure_times and arrival_times should be equal.
            - If the train has an assigned_route_id, the number of times should match the route station sequence length.
        """
        # Check for unique schedule_id
        if schedule_id in self.schedules:
            return {"success": False, "error": "Schedule ID already exists."}
        # Check if train exists
        if train_id not in self.trains:
            return {"success": False, "error": "Train ID does not exist."}
        # Check departure/arrival times lists are non-empty and of same length
        if not departure_times or not arrival_times:
            return {"success": False, "error": "Departure and arrival times cannot be empty."}
        if len(departure_times) != len(arrival_times):
            return {"success": False, "error": "Departure and arrival times must be of the same length."}
        # If possible, check alignment with route station sequence
        assigned_route_id = self.trains[train_id].get("assigned_route_id")
        if assigned_route_id and assigned_route_id in self.routes:
            station_seq = self.routes[assigned_route_id]["station_sequence"]
            if len(departure_times) != len(station_seq):
                return {
                    "success": False,
                    "error": "Number of departure/arrival times does not match the station sequence for the assigned route.",
                }

        # If all validations pass, create schedule
        self.schedules[schedule_id] = {
            "schedule_id": schedule_id,
            "train_id": train_id,
            "date": date,
            "departure_times": departure_times,
            "arrival_times": arrival_times,
            "active": active
        }

        return {"success": True, "message": "Schedule added successfully."}

    def update_schedule(
        self,
        schedule_id: str,
        departure_times: List[str] = None,
        arrival_times: List[str] = None,
        active: bool = None,
        date: str = None,
        train_id: str = None
    ) -> dict:
        """
        Edit an existing schedule (timetable).

        Args:
            schedule_id (str): The identifier of the schedule to update.
            departure_times (List[str], optional): Updated departure times per station (must match station sequence length).
            arrival_times (List[str], optional): Updated arrival times per station (must match station sequence length).
            active (bool, optional): Updated active status.
            date (str, optional): Updated date for the schedule.
            train_id (str, optional): Updated train assignment (should only be valid if train is eligible).

        Returns:
            dict:
                - success (bool): True if update was made, False otherwise.
                - message (str): Success description, if success True.
                - error (str): Error message, if success False.

        Constraints:
            - Schedule with schedule_id must exist.
            - If updating times, lengths must match station sequence for associated route.
            - If the schedule is temporarily unassigned from any route, only non-route-dependent
              fields (train_id, date, active) may be updated.
            - Train cannot be assigned to multiple routes at the same time and date (on changes).
        """
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            return { "success": False, "error": "Schedule does not exist." }

        previous_train_id = schedule["train_id"]

        # Get assigned route for this schedule
        _, assignment = self._find_route_assignment_entry(schedule_id)
        route_id = assignment["route_id"] if assignment is not None else None
        route = self.routes.get(route_id) if route_id is not None else None
        station_count = len(route["station_sequence"]) if route is not None else None

        # Validate times if provided
        if departure_times is not None:
            if station_count is None:
                return { "success": False, "error": "Schedule is not assigned to any route." }
            if len(departure_times) != station_count:
                return {
                    "success": False,
                    "error": "departure_times length does not match station sequence."
                }
            schedule["departure_times"] = departure_times
        if arrival_times is not None:
            if station_count is None:
                return { "success": False, "error": "Schedule is not assigned to any route." }
            if len(arrival_times) != station_count:
                return {
                    "success": False,
                    "error": "arrival_times length does not match station sequence."
                }
            schedule["arrival_times"] = arrival_times

        # Update other attributes
        if active is not None:
            schedule["active"] = active
        if date is not None:
            schedule["date"] = date
        if train_id is not None:
            schedule["train_id"] = train_id
            if assignment is not None:
                assignment["train_id"] = train_id

        # Check that train is not assigned to multiple routes for same date
        # Only if date or train_id updated
        updated_train_id = schedule["train_id"]
        updated_date = schedule["date"]
        for sched in self.schedules.values():
            if sched["schedule_id"] != schedule_id and sched["train_id"] == updated_train_id and sched["date"] == updated_date and sched["active"]:
                # Find their assignment route
                _, other_assign = self._find_route_assignment_entry(sched["schedule_id"])
                if other_assign and route_id is not None and other_assign["route_id"] != route_id:
                    return {
                        "success": False,
                        "error": "Train is already assigned to a different route at the same time and date."
                    }

        if train_id is not None and train_id != previous_train_id:
            self._refresh_train_assigned_route(previous_train_id)
            self._refresh_train_assigned_route(train_id)
        else:
            self._refresh_train_assigned_route(schedule["train_id"])

        return { "success": True, "message": "Schedule updated successfully." }

    def activate_schedule(self, schedule_id: str) -> dict:
        """
        Set a schedule as active for operational use.

        Args:
            schedule_id (str): Identifier of the schedule to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule <schedule_id> activated"
            }
            or
            {
                "success": False,
                "error": "Schedule not found"
            }

        Constraints:
            - The schedule must exist in the system.
            - Operation is idempotent: activating an already-active schedule is considered successful.
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return { "success": False, "error": "Schedule not found" }

        schedule["active"] = True
        return { "success": True, "message": f"Schedule {schedule_id} activated" }

    def deactivate_schedule(self, schedule_id: str) -> dict:
        """
        Mark a schedule as inactive, so it will not be considered in active queries.

        Args:
            schedule_id (str): Unique identifier of the schedule to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. schedule does not exist)
            }

        Constraints:
            - The schedule must exist in the system.
            - Operation is idempotent: already inactive schedules will result in success.
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return { "success": False, "error": "Schedule does not exist." }

        if not schedule["active"]:
            return { "success": True, "message": f"Schedule {schedule_id} was already inactive." }

        schedule["active"] = False
        # (If necessary, could update state or references further here.)
        return { "success": True, "message": f"Schedule {schedule_id} deactivated." }

    def validate_route_and_schedule_assignment(
        self,
        train_id: str,
        route_id: str,
        schedule_id: str
    ) -> dict:
        """
        Validates if assigning train `train_id` to route `route_id` with schedule `schedule_id`
        is conflict-free and adheres to all system constraints.

        Args:
            train_id (str): ID of the train to assign.
            route_id (str): ID of the route to assign to.
            schedule_id (str): ID of the schedule (timetable) for assignment.

        Returns:
            dict: {
                "success": True,
                "message": "Assignment is valid."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (constraint violation)
            }

        Constraints:
            - All IDs must exist.
            - The schedule must be for the provided train and active.
            - The route's origin and destination stations must exist.
            - No other assignment exists for this train and date.
            - Departure/arrival times in schedule must match the route's station_sequence.
        """

        # Check train existence
        if train_id not in self.trains:
            return { "success": False, "error": "Train does not exist." }

        # Check route existence
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist." }

        # Check schedule existence
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule does not exist." }

        route = self.routes[route_id]
        train = self.trains[train_id]
        schedule = self.schedules[schedule_id]

        # Check schedule's assigned train
        if schedule["train_id"] != train_id:
            return { "success": False, "error": "Schedule does not belong to this train." }

        # Check schedule is active
        if not schedule["active"]:
            return { "success": False, "error": "Schedule is not active." }

        # Route station validity
        origin = route["origin_station_id"]
        dest = route["destination_station_id"]
        # Check if stations exist
        if origin not in self.stations or dest not in self.stations:
            return { "success": False, "error": "Origin or destination station does not exist." }

        # Departure/arrival times vs. station_sequence
        num_stations = len(route["station_sequence"])
        if (
            len(schedule["departure_times"]) != num_stations or
            len(schedule["arrival_times"]) != num_stations
        ):
            return {
                "success": False,
                "error": "Departure/arrival times do not match station sequence in schedule."
            }

        # No multiple assignments for same train & date
        check_date = schedule["date"]
        for other_assignment in self.route_assignments.values():
            other_sched_id = other_assignment["schedule_id"]
            other_sched = self.schedules.get(other_sched_id)
            if not other_sched:
                continue
            # Only other assignments for the same train *with overlapping date*
            if other_assignment["train_id"] == train_id and other_sched["date"] == check_date:
                # If this is an 'update' of the same assignment, allow.
                if other_sched_id == schedule_id and other_assignment["route_id"] == route_id:
                    continue
                return {
                    "success": False,
                    "error": f"Train already assigned to a route (ID: {other_assignment['route_id']}) on {check_date}."
                }

        return { "success": True, "message": "Assignment is valid." }

    def remove_schedule(self, schedule_id: str) -> dict:
        """
        Delete a schedule from the system, and remove any associated route assignment.

        Args:
            schedule_id (str): The unique ID of the schedule to remove.

        Returns:
            dict: {
                "success": True, "message": "Schedule <schedule_id> deleted."
            }
            or
            {
                "success": False, "error": str
            }

        Constraints:
            - If the schedule does not exist, return failure.
            - Any RouteAssignment with this schedule_id should also be removed.
            - Do not raise exceptions; return structured result.
        """
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule not found." }

        assignment_key, removed_assignment = self._find_route_assignment_entry(schedule_id)

        # Remove schedule
        del self.schedules[schedule_id]

        # Remove associated route assignment if exists
        if assignment_key is not None:
            del self.route_assignments[assignment_key]

        if removed_assignment:
            train_id = removed_assignment["train_id"]
            self._refresh_train_assigned_route(train_id)

        return { "success": True, "message": f"Schedule {schedule_id} deleted." }


class TrainScheduleManagementSystem(BaseEnv):
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

    def get_station_by_name(self, **kwargs):
        return self._call_inner_tool('get_station_by_name', kwargs)

    def get_route_by_origin_and_destination(self, **kwargs):
        return self._call_inner_tool('get_route_by_origin_and_destination', kwargs)

    def list_routes(self, **kwargs):
        return self._call_inner_tool('list_routes', kwargs)

    def get_trains_assigned_to_route(self, **kwargs):
        return self._call_inner_tool('get_trains_assigned_to_route', kwargs)

    def get_active_schedules_for_train_by_date(self, **kwargs):
        return self._call_inner_tool('get_active_schedules_for_train_by_date', kwargs)

    def get_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_id', kwargs)

    def get_route_assignment_by_schedule(self, **kwargs):
        return self._call_inner_tool('get_route_assignment_by_schedule', kwargs)

    def get_train_info(self, **kwargs):
        return self._call_inner_tool('get_train_info', kwargs)

    def list_trains(self, **kwargs):
        return self._call_inner_tool('list_trains', kwargs)

    def list_stations(self, **kwargs):
        return self._call_inner_tool('list_stations', kwargs)

    def check_route_station_sequence_consistency(self, **kwargs):
        return self._call_inner_tool('check_route_station_sequence_consistency', kwargs)

    def get_schedules_by_route_and_date(self, **kwargs):
        return self._call_inner_tool('get_schedules_by_route_and_date', kwargs)

    def add_station(self, **kwargs):
        return self._call_inner_tool('add_station', kwargs)

    def update_station(self, **kwargs):
        return self._call_inner_tool('update_station', kwargs)

    def add_route(self, **kwargs):
        return self._call_inner_tool('add_route', kwargs)

    def update_route(self, **kwargs):
        return self._call_inner_tool('update_route', kwargs)

    def assign_train_to_route_and_schedule(self, **kwargs):
        return self._call_inner_tool('assign_train_to_route_and_schedule', kwargs)

    def unassign_train_from_route(self, **kwargs):
        return self._call_inner_tool('unassign_train_from_route', kwargs)

    def add_train(self, **kwargs):
        return self._call_inner_tool('add_train', kwargs)

    def update_train(self, **kwargs):
        return self._call_inner_tool('update_train', kwargs)

    def add_schedule(self, **kwargs):
        return self._call_inner_tool('add_schedule', kwargs)

    def update_schedule(self, **kwargs):
        return self._call_inner_tool('update_schedule', kwargs)

    def activate_schedule(self, **kwargs):
        return self._call_inner_tool('activate_schedule', kwargs)

    def deactivate_schedule(self, **kwargs):
        return self._call_inner_tool('deactivate_schedule', kwargs)

    def validate_route_and_schedule_assignment(self, **kwargs):
        return self._call_inner_tool('validate_route_and_schedule_assignment', kwargs)

    def remove_schedule(self, **kwargs):
        return self._call_inner_tool('remove_schedule', kwargs)
