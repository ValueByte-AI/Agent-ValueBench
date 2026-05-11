# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
from datetime import datetime



class VenueInfo(TypedDict):
    venue_id: str
    name: str
    location: str
    capacity: int
    amenities: List[str]
    availability_status: str  # e.g., 'active', 'inactive', 'booked'
    booking_schedule: List[Dict[str, Any]]  # Details of individual bookings

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Event venue management system state.
        """

        # Venues: {venue_id: VenueInfo}
        # Each venue represents an event venue, capturing its identification, location, characteristics,
        # amenities, availability, and booking schedule.
        self.venues: Dict[str, VenueInfo] = {}

        # Constraints:
        # - Each venue_id must be unique.
        # - A venue’s availability_status and booking_schedule must be consistent.
        # - Venue capacity and amenities must be accurate and up to date.
        # - Only venues with active status can be booked or displayed for selection.

    @staticmethod
    def _coerce_time(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def get_venue_by_id(self, venue_id: str) -> dict:
        """
        Retrieve full VenueInfo for the venue with the given unique venue_id.

        Args:
            venue_id (str): The unique identifier of the venue.

        Returns:
            dict: {
                "success": True,
                "data": VenueInfo
            }
            or
            {
                "success": False,
                "error": "Venue not found"
            }
        Constraints:
            - venue_id must be unique.
        """
        venue = self.venues.get(venue_id)
        if venue is None:
            return {"success": False, "error": "Venue not found"}
        return {"success": True, "data": venue}

    def get_venues_by_ids(self, venue_ids: List[str]) -> dict:
        """
        Retrieve venue details for multiple venues given a list of venue_ids.

        Args:
            venue_ids (List[str]): List of venue_id strings to look up.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[VenueInfo],         # Venue details for found ids (order as input minus not_found)
                    "not_found": List[str],          # Venue_ids that do not exist
                }
        Constraints:
            - Only venues present in the system are returned.
            - Nonexistent ids are reported in "not_found".
            - If no ids are found, data is empty and not_found includes all input ids.
        """
        # To preserve order and remove duplicates
        unique_ids = []
        seen = set()
        for vid in venue_ids:
            if vid not in seen:
                unique_ids.append(vid)
                seen.add(vid)

        found = []
        not_found = []
        for vid in unique_ids:
            venue = self.venues.get(vid)
            if venue is not None:
                found.append(venue)
            else:
                not_found.append(vid)
        return {
            "success": True,
            "data": found,
            "not_found": not_found
        }

    def list_all_venues(self) -> dict:
        """
        List all venues registered in the system.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[VenueInfo],  # List of all venues (can be empty)
                }
        """
        all_venues = list(self.venues.values())
        return { "success": True, "data": all_venues }

    def search_venues_by_location(self, location: str) -> dict:
        """
        Retrieve all venues in the specified location with active status.

        Args:
            location (str): The target location to search venues for.

        Returns:
            dict: {
                "success": True,
                "data": List[VenueInfo]  # List of matching venues (may be empty)
            }
        Constraints:
            - Only venues with 'active' availability_status are included in the results.
        """
        result = [
            venue_info for venue_info in self.venues.values()
            if venue_info['location'] == location and venue_info['availability_status'] == 'active'
        ]
        return { "success": True, "data": result }

    def filter_venues_by_status(self, status: str) -> dict:
        """
        List all venues by a given availability_status.

        Args:
            status (str): The required availability status (e.g., 'active', 'inactive', 'booked').

        Returns:
            dict: {
                "success": True,
                "data": List[VenueInfo],    # list of venues with this status
            }
            or
            {
                "success": False,
                "error": str
            }

        Notes:
            - Returns empty list if no venues match the given status.
            - Accepts any string as status; no strict validation.
        """
        result = [
            venue for venue in self.venues.values()
            if venue["availability_status"] == status
        ]

        return { "success": True, "data": result }

    def filter_venues_by_capacity(self, min_capacity: int) -> dict:
        """
        List venues whose capacity matches or exceeds a minimum required capacity.
        Only venues with 'active' availability_status are included.

        Args:
            min_capacity (int): The minimum required capacity (must be non-negative integer).

        Returns:
            dict:
                - success (bool): True if operation performed successfully.
                - data (List[VenueInfo]): List of venue information dicts matching criteria.
                - error (str): If invalid input, error message.
        Constraints:
            - Only venues with 'active' status can be listed.
            - min_capacity must be a non-negative integer.
        """
        if not isinstance(min_capacity, int) or min_capacity < 0:
            return {"success": False, "error": "Invalid capacity value"}
    
        result = [
            venue for venue in self.venues.values()
            if venue["availability_status"] == "active" and venue["capacity"] >= min_capacity
        ]
        return {"success": True, "data": result}

    def filter_venues_by_amenities(self, required_amenities: list[str]) -> dict:
        """
        List venues (VenueInfo) whose amenities contain all amenities in required_amenities
        and that have 'active' availability_status.

        Args:
            required_amenities (list[str]): List of amenities that must be present for a venue to match.

        Returns:
            dict: {
                "success": True,
                "data": List[VenueInfo],  # venues that match (may be empty if no matches)
            }

        Constraints:
            - Only venues with 'active' status are included.
            - Each venue's amenities must include all of required_amenities (set inclusion).
        """
        results = []
        for venue in self.venues.values():
            # Only consider active venues for filtering
            if venue["availability_status"] != "active":
                continue
            if all(amenity in venue["amenities"] for amenity in required_amenities):
                results.append(venue)
        return {"success": True, "data": results}

    def get_venue_booking_schedule(self, venue_id: str) -> dict:
        """
        Retrieve the complete booking schedule for a specified venue.

        Args:
            venue_id (str): The unique identifier for the venue.

        Returns:
            dict:
                - success (bool): True if retrieval is successful.
                - data (List[Dict]): The venue's booking schedule if found.
                - error (str): Explanation if retrieval fails.

        Constraints:
            - The specified venue_id must exist in the system.
        """
        venue = self.venues.get(venue_id)
        if not venue:
            return {"success": False, "error": "Venue not found"}
        return {"success": True, "data": venue["booking_schedule"]}


    def check_venue_availability(self, venue_id: str, start_time: datetime, end_time: datetime) -> dict:
        """
        Check if a venue is available (i.e., not booked) during the given date/time range.

        Args:
            venue_id (str): The unique identifier of the venue.
            start_time (datetime): Start of the requested availability window.
            end_time (datetime): End of the requested availability window.

        Returns:
            dict:
                - On success:
                    { "success": True, "available": bool }
                - On failure:
                    { "success": False, "error": str }

        Constraints:
            - Venue must exist in the system.
            - Venue must have 'active' status.
            - Booking ranges must not overlap with the requested range.
            - start_time must precede end_time.
        """

        # 1. Venue existence check
        venue = self.venues.get(venue_id)
        if not venue:
            return { "success": False, "error": "Venue does not exist" }

        # 2. Status check
        if venue["availability_status"] != "active":
            return { "success": False, "error": "Venue is not active" }

        # 3. Time validity check
        start_dt = self._coerce_time(start_time)
        end_dt = self._coerce_time(end_time)
        if start_dt is None or end_dt is None:
            return { "success": False, "error": "Invalid start or end time" }
        if start_dt >= end_dt:
            return { "success": False, "error": "Start time must precede end time" }

        # 4. Overlap check with booking_schedule
        for booking in venue.get("booking_schedule", []):
            # Assume booking has "start_time" and "end_time" stored as datetime objects
            b_start = self._coerce_time(booking.get("start_time"))
            b_end = self._coerce_time(booking.get("end_time"))
            if b_start is None or b_end is None:
                continue
            # Check overlap: (existing_start < req_end) and (existing_end > req_start)
            if (b_start < end_dt) and (b_end > start_dt):
                # Overlap detected
                return { "success": True, "available": False }

        # No overlap found
        return { "success": True, "available": True }

    def get_venue_status(self, venue_id: str) -> dict:
        """
        Return the current availability_status of a venue.

        Args:
            venue_id (str): The unique identifier of the venue.

        Returns:
            dict: {
                "success": True,
                "data": str  # The venue's current availability_status (e.g., 'active', 'inactive', 'booked')
            }
            or
            {
                "success": False,
                "error": str  # "Venue not found" if venue_id doesn't exist
            }

        Constraints:
            - The venue_id must exist in the system.
        """
        venue = self.venues.get(venue_id)
        if not venue:
            return {"success": False, "error": "Venue not found"}

        return {"success": True, "data": venue["availability_status"]}

    def update_venue_info(
        self,
        venue_id: str,
        capacity: int = None,
        location: str = None,
        amenities: list = None
    ) -> dict:
        """
        Update the capacity, location, and/or amenities for an existing venue.

        Args:
            venue_id (str): The ID of the venue to update.
            capacity (int, optional): New capacity value. Must be a positive integer if provided.
            location (str, optional): New location string.
            amenities (list, optional): New amenities list. Must be a list of strings if provided.

        Returns:
            dict: {
                "success": True,
                "message": str  # Update message
            }
            OR
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - venue_id must exist.
            - capacity and amenities must have correct types/values if provided.
        """
        if venue_id not in self.venues:
            return {"success": False, "error": "Venue not found"}

        venue = self.venues[venue_id]

        # Validate and set capacity
        if capacity is not None:
            if not isinstance(capacity, int) or capacity <= 0:
                return {"success": False, "error": "Capacity must be a positive integer"}
            venue["capacity"] = capacity

        # Validate and set location
        if location is not None:
            if not isinstance(location, str) or location.strip() == '':
                return {"success": False, "error": "Location must be a non-empty string"}
            venue["location"] = location

        # Validate and set amenities
        if amenities is not None:
            if not isinstance(amenities, list) or not all(isinstance(a, str) for a in amenities):
                return {"success": False, "error": "Amenities must be a list of strings"}
            venue["amenities"] = amenities

        self.venues[venue_id] = venue

        return {"success": True, "message": f"Venue '{venue_id}' information updated successfully."}

    def set_venue_status(self, venue_id: str, new_status: str) -> dict:
        """
        Change the availability_status for a venue to 'active', 'inactive', or 'booked'.

        Args:
            venue_id (str): The unique ID of the venue to update.
            new_status (str): The new status string ('active', 'inactive', 'booked').

        Returns:
            dict: {
                "success": True,
                "message": "Venue status updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The venue must exist.
            - Only valid statuses are accepted ('active', 'inactive', 'booked').
            - Booking consistency checks are NOT enforced (as not specified for this operation).
        """
        valid_statuses = {"active", "inactive", "booked"}
        if venue_id not in self.venues:
            return { "success": False, "error": f"Venue with id '{venue_id}' does not exist." }

        if new_status not in valid_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Valid statuses are: {', '.join(valid_statuses)}." }

        self.venues[venue_id]["availability_status"] = new_status
        return { "success": True, "message": "Venue status updated successfully." }

    def update_venue_amenities(
        self, 
        venue_id: str,
        add_amenities: list = None,
        remove_amenities: list = None
    ) -> dict:
        """
        Add or remove amenities for a specific venue.

        Args:
            venue_id (str): The ID of the venue to update.
            add_amenities (list, optional): Amenities to add to the venue. Default: None.
            remove_amenities (list, optional): Amenities to remove from the venue. Default: None.

        Returns:
            dict:
                On success: {"success": True, "message": str}
                On failure: {"success": False, "error": str}

        Constraints:
            - Only updates amenities for an existing venue.
            - Amenities list must not contain duplicates.
            - Removing amenity not present is ignored.
        """
        if venue_id not in self.venues:
            return {"success": False, "error": f"Venue {venue_id} does not exist"}

        venue = self.venues[venue_id]
        current_amenities = set(venue.get("amenities", []))

        changed = False

        if add_amenities:
            for amenity in add_amenities:
                if amenity not in current_amenities:
                    current_amenities.add(amenity)
                    changed = True

        if remove_amenities:
            for amenity in remove_amenities:
                if amenity in current_amenities:
                    current_amenities.remove(amenity)
                    changed = True

        # Update amenities
        venue["amenities"] = list(current_amenities)

        if changed:
            return {"success": True, "message": f"Amenities updated for venue_id {venue_id}"}
        else:
            return {"success": True, "message": f"No amenities updated for venue_id {venue_id}"}

    def update_venue_capacity(self, venue_id: str, new_capacity: int) -> dict:
        """
        Modify the capacity value for a venue.

        Args:
            venue_id (str): The unique identifier for the venue.
            new_capacity (int): The new capacity value to be set. Must be a positive integer.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Capacity for venue <venue_id> updated to <new_capacity>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Description of error"
                    }

        Constraints:
            - Venue (venue_id) must exist.
            - new_capacity must be a positive integer (> 0).
            - Venue capacity must always be accurate and up to date.
        """
        if venue_id not in self.venues:
            return { "success": False, "error": f"Venue with ID '{venue_id}' does not exist." }

        if not isinstance(new_capacity, int) or new_capacity <= 0:
            return { "success": False, "error": "Capacity must be a positive integer." }

        self.venues[venue_id]['capacity'] = new_capacity

        return {
            "success": True,
            "message": f"Capacity for venue {venue_id} updated to {new_capacity}."
        }

    def add_venue_booking(self, venue_id: str, booking_details: Dict[str, Any]) -> dict:
        """
        Add a new booking to a venue’s booking_schedule, ensuring no double-booking and status consistency.

        Args:
            venue_id (str): The unique ID of the venue to be booked.
            booking_details (dict): A dictionary containing booking information. Must include
                'start_time' and 'end_time' as comparable values (ideally ISO format strings or timestamps).

        Returns:
            dict:
                - On success: { "success": True, "message": "Booking added to venue <venue_id>." }
                - On failure: { "success": False, "error": <reason str> }

        Constraints:
            - Venue must exist and status be 'active'.
            - No overlap with existing bookings (double-booking not allowed).
            - booking_details must include 'start_time' and 'end_time', and they must be valid & non-overlapping.
        """
        if venue_id not in self.venues:
            return { "success": False, "error": "Venue does not exist." }

        venue = self.venues[venue_id]
        if venue["availability_status"] != "active":
            return { "success": False, "error": "Venue is not active. Only active venues can be booked." }

        # Check booking_details format
        required_fields = ["start_time", "end_time"]
        for field in required_fields:
            if field not in booking_details:
                return { "success": False, "error": f"Missing required booking detail: {field}" }

        new_start = self._coerce_time(booking_details["start_time"])
        new_end = self._coerce_time(booking_details["end_time"])
        if new_start is None or new_end is None:
            return { "success": False, "error": "Invalid booking times." }
        if new_start >= new_end:
            return { "success": False, "error": "Invalid booking times: end_time must be after start_time." }

        # Check for overlap with existing bookings
        for existing_booking in venue.get("booking_schedule", []):
            ex_start = self._coerce_time(existing_booking.get("start_time"))
            ex_end = self._coerce_time(existing_booking.get("end_time"))
            if ex_start is None or ex_end is None:
                continue
            if not (new_end <= ex_start or new_start >= ex_end):
                return {
                    "success": False,
                    "error": "Time conflict: booking overlaps with existing booking."
                }
        # If all checks passed, add booking
        venue["booking_schedule"].append(booking_details)

        # (Optionally) Update availability_status if needed, but constraint is mainly status consistency (left as is).
        # Could check here if the venue should be marked as 'booked', depending on business logic.

        return { "success": True, "message": f"Booking added to venue {venue_id}." }

    def remove_venue_booking(self, venue_id: str, booking_id: str) -> dict:
        """
        Remove a booking entry from a venue’s schedule and update status if necessary.

        Args:
            venue_id (str): Unique identifier of the venue.
            booking_id (str): Unique identifier of the booking entry to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Booking removed from venue schedule." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Venue must exist.
            - Booking must exist in venue's booking_schedule.
            - After removal, ensure availability_status is consistent with the booking_schedule.
        """
        venue = self.venues.get(venue_id)
        if not venue:
            return { "success": False, "error": "Venue not found" }

        # Look for the booking by booking_id
        booking_schedule = venue.get("booking_schedule", [])
        booking_index = None
        for idx, booking in enumerate(booking_schedule):
            if booking.get("booking_id") == booking_id:
                booking_index = idx
                break

        if booking_index is None:
            return { "success": False, "error": "Booking not found in venue schedule" }

        # Remove the booking
        del booking_schedule[booking_index]
        venue["booking_schedule"] = booking_schedule

        # Update status: If no bookings, set to 'active', otherwise if bookings remain and venue was 'active', do nothing.
        if len(booking_schedule) == 0:
            venue["availability_status"] = "active"
        # Optionally: if bookings remain, set to 'booked'
        elif len(booking_schedule) > 0:
            venue["availability_status"] = "booked"

        return { "success": True, "message": "Booking removed from venue schedule." }

    def add_new_venue(self, venue_info: dict) -> dict:
        """
        Add a new venue to the management system, ensuring that the venue_id is unique.

        Args:
            venue_info (dict): A dictionary with all required fields to define VenueInfo:
                - venue_id (str)
                - name (str)
                - location (str)
                - capacity (int)
                - amenities (List[str])
                - availability_status (str)  # Should be a valid status, e.g. 'active', 'inactive'
                - booking_schedule (List[Dict[str, Any]])  # Usually an empty list for new venues

        Returns:
            dict:
                - On success: { "success": True, "message": "Venue <venue_id> added." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - venue_id must be unique (must not already exist)
            - capacity must be a positive integer
            - amenities must be a list
            - availability_status should be a valid status (accept 'active', 'inactive', 'booked')
            - booking_schedule should be a list (usually empty when registering)
        """
        if not isinstance(venue_info, dict):
            return { "success": False, "error": "venue_info must be a dictionary." }
        required_fields = ["venue_id", "name", "location", "capacity", "amenities", "availability_status", "booking_schedule"]
        for field in required_fields:
            if field not in venue_info:
                return { "success": False, "error": f"Missing required field: {field}" }
    
        venue_id = venue_info["venue_id"]
        if venue_id in self.venues:
            return { "success": False, "error": "Venue ID already exists." }
        if not isinstance(venue_info["capacity"], int) or venue_info["capacity"] <= 0:
            return { "success": False, "error": "Venue capacity must be a positive integer." }
        if not isinstance(venue_info["amenities"], list):
            return { "success": False, "error": "Amenities must be a list." }
        if venue_info["availability_status"] not in ["active", "inactive", "booked"]:
            return { "success": False, "error": "Invalid availability_status; must be 'active', 'inactive', or 'booked'." }
        if not isinstance(venue_info["booking_schedule"], list):
            return { "success": False, "error": "booking_schedule must be a list." }

        self.venues[venue_id] = {
            "venue_id": venue_info["venue_id"],
            "name": venue_info["name"],
            "location": venue_info["location"],
            "capacity": venue_info["capacity"],
            "amenities": venue_info["amenities"],
            "availability_status": venue_info["availability_status"],
            "booking_schedule": venue_info["booking_schedule"]
        }
        return { "success": True, "message": f"Venue {venue_id} added." }

    def delete_venue(self, venue_id: str) -> dict:
        """
        Remove a venue from the system by its unique venue_id.

        Args:
            venue_id (str): The unique identifier of the venue to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Venue <venue_id> has been deleted"
            }
            or
            {
                "success": False,
                "error": "Venue not found"
            }

        Constraints:
            - venue_id must exist in the system.
            - Any admin-only restriction is presumed enforced elsewhere.
        """
        if venue_id not in self.venues:
            return { "success": False, "error": "Venue not found" }

        del self.venues[venue_id]
        return { "success": True, "message": f"Venue {venue_id} has been deleted" }

    def correct_booking_schedule(self, venue_id: str) -> dict:
        """
        Update or fix inconsistencies in a venue's booking_schedule to match its availability_status.

        Args:
            venue_id (str): The unique identifier of the venue to process.

        Returns:
            dict:
                - On success: { "success": True, "message": "Booking schedule for venue <venue_id> corrected to match availability_status." }
                - On failure: { "success": False, "error": "Venue not found." }

        Constraints:
            - If availability_status is 'active' or 'inactive', booking_schedule should be empty.
            - If status is 'booked', booking_schedule must have at least one booking.
            - If status is not recognized, leave as is and succeed.
        """
        venue = self.venues.get(venue_id)
        if venue is None:
            return {"success": False, "error": "Venue not found."}

        status = venue["availability_status"]
        fixed = False

        if status in ("active", "inactive"):
            if venue["booking_schedule"]:
                venue["booking_schedule"] = []
                fixed = True
        elif status == "booked":
            if not venue["booking_schedule"]:
                # Add a placeholder booking to satisfy constraint
                venue["booking_schedule"] = [{
                    "booking_id": "auto_placeholder",
                    "details": "Auto-added booking to match 'booked' status",
                }]
                fixed = True
        # For other statuses, we do not define corrections.

        if fixed:
            message = f"Booking schedule for venue {venue_id} corrected to match availability_status."
        else:
            message = f"No correction needed for venue {venue_id}; booking_schedule already matches availability_status."

        return { "success": True, "message": message }


class EventVenueManagementSystem(BaseEnv):
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

    def get_venue_by_id(self, **kwargs):
        return self._call_inner_tool('get_venue_by_id', kwargs)

    def get_venues_by_ids(self, **kwargs):
        return self._call_inner_tool('get_venues_by_ids', kwargs)

    def list_all_venues(self, **kwargs):
        return self._call_inner_tool('list_all_venues', kwargs)

    def search_venues_by_location(self, **kwargs):
        return self._call_inner_tool('search_venues_by_location', kwargs)

    def filter_venues_by_status(self, **kwargs):
        return self._call_inner_tool('filter_venues_by_status', kwargs)

    def filter_venues_by_capacity(self, **kwargs):
        return self._call_inner_tool('filter_venues_by_capacity', kwargs)

    def filter_venues_by_amenities(self, **kwargs):
        return self._call_inner_tool('filter_venues_by_amenities', kwargs)

    def get_venue_booking_schedule(self, **kwargs):
        return self._call_inner_tool('get_venue_booking_schedule', kwargs)

    def check_venue_availability(self, **kwargs):
        return self._call_inner_tool('check_venue_availability', kwargs)

    def get_venue_status(self, **kwargs):
        return self._call_inner_tool('get_venue_status', kwargs)

    def update_venue_info(self, **kwargs):
        return self._call_inner_tool('update_venue_info', kwargs)

    def set_venue_status(self, **kwargs):
        return self._call_inner_tool('set_venue_status', kwargs)

    def update_venue_amenities(self, **kwargs):
        return self._call_inner_tool('update_venue_amenities', kwargs)

    def update_venue_capacity(self, **kwargs):
        return self._call_inner_tool('update_venue_capacity', kwargs)

    def add_venue_booking(self, **kwargs):
        return self._call_inner_tool('add_venue_booking', kwargs)

    def remove_venue_booking(self, **kwargs):
        return self._call_inner_tool('remove_venue_booking', kwargs)

    def add_new_venue(self, **kwargs):
        return self._call_inner_tool('add_new_venue', kwargs)

    def delete_venue(self, **kwargs):
        return self._call_inner_tool('delete_venue', kwargs)

    def correct_booking_schedule(self, **kwargs):
        return self._call_inner_tool('correct_booking_schedule', kwargs)
