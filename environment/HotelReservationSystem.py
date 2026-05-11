# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import uuid



class RoomInfo(TypedDict):
    room_id: str
    type: str
    amenities: List[str]
    occupancy_status: str

class ReservationInfo(TypedDict):
    reservation_id: str
    room_id: str
    guest_id: str
    start_date: str
    end_date: str
    status: str

class GuestInfo(TypedDict):
    guest_id: str
    name: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Rooms: {room_id: RoomInfo}
        self.rooms: Dict[str, RoomInfo] = {}

        # Reservations: {reservation_id: ReservationInfo}
        self.reservations: Dict[str, ReservationInfo] = {}

        # Guests: {guest_id: GuestInfo}
        self.guests: Dict[str, GuestInfo] = {}

        # Constraints:
        # - A room cannot be reserved by more than one guest during overlapping date ranges.
        # - Only available (not currently reserved/occupied) rooms can be booked for a given date range.
        # - Room type must match the requested type when searching or booking.
        # - Reservation status may affect availability (e.g., only active bookings block availability).

    def _parse_date(self, date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def _reservation_blocks_booking(self, reservation: ReservationInfo) -> bool:
        return reservation.get("status", "").lower() in {"booked", "checked-in"}

    def _ranges_overlap(self, start_a, end_a, start_b, end_b) -> bool:
        # Standard overnight stays use checkout-style [start, end) ranges, so
        # same-day turnover remains allowed. Single-day bookings (start == end)
        # are treated as occupying that calendar day by extending the end
        # boundary by one day for overlap checks.
        normalized_end_a = end_a if end_a > start_a else start_a + timedelta(days=1)
        normalized_end_b = end_b if end_b > start_b else start_b + timedelta(days=1)
        return start_a < normalized_end_b and normalized_end_a > start_b

    def list_rooms_by_type(self, room_type: str) -> dict:
        """
        Retrieve all room records matching a specified type.

        Args:
            room_type (str): The room type to filter by (e.g., "single", "double").

        Returns:
            dict: {
                "success": True,
                "data": List[RoomInfo],  # List of matching rooms, possibly empty
            }

        Notes:
            - Returns an empty list if no rooms match the specified type.
            - No error if the type does not exist among rooms in the system.
            - No permission or status checking is involved.
        """
        matching_rooms = [
            room_info
            for room_info in self.rooms.values()
            if room_info['type'] == room_type
        ]
        return {"success": True, "data": matching_rooms}

    def get_room_info(self, room_id: str) -> dict:
        """
        Retrieve full information about a specific room, given its room_id.

        Args:
            room_id (str): Identifier of the room to fetch.

        Returns:
            dict: {
                "success": True,
                "data": RoomInfo  # Room details if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if room not found
            }

        Constraints:
            - The room_id must exist in the hotel room records.
        """
        room_info = self.rooms.get(room_id)
        if room_info is None:
            return { "success": False, "error": "Room not found" }
        return { "success": True, "data": room_info }

    def list_all_rooms(self) -> dict:
        """
        List all rooms in the hotel with their attributes.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[RoomInfo]  # All rooms, possibly empty if none present
                }
        Notes:
            - No input arguments are required.
            - Returns an empty list if there are no rooms in the hotel.
        """
        all_rooms = list(self.rooms.values())
        return {
            "success": True,
            "data": all_rooms
        }

    def get_room_reservations(self, room_id: str) -> dict:
        """
        Retrieve all reservations associated with a given room_id.

        Args:
            room_id (str): The ID of the room.

        Returns:
            dict: {
                "success": True,
                "data": List[ReservationInfo]  # All reservations for this room (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if room does not exist.
            }

        Constraints:
            - The room must exist in the system.
        """
        if room_id not in self.rooms:
            return { "success": False, "error": "Room does not exist" }

        result = [
            reservation
            for reservation in self.reservations.values()
            if reservation["room_id"] == room_id
        ]
        return { "success": True, "data": result }


    def get_reservations_in_date_range(self, start_date: str, end_date: str, status: Optional[str] = None) -> dict:
        """
        Retrieve all reservations that overlap with the given date range, optionally filtering by reservation status.

        Args:
            start_date (str): Start of the date range (format "YYYY-MM-DD").
            end_date (str): End of the date range (format "YYYY-MM-DD").
            status (Optional[str]): Reservation status to filter by (if provided).

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[ReservationInfo] }
                - On error:
                    { "success": False, "error": str }

        Constraints:
            - start_date and end_date must be valid dates, and start_date <= end_date.
            - Reservations overlap if their date ranges share any day.
        """
        # Date validation and conversion
        try:
            query_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
        if query_start > query_end:
            return {"success": False, "error": "start_date cannot be after end_date."}

        result = []
        for reservation in self.reservations.values():
            try:
                res_start = datetime.strptime(reservation["start_date"], "%Y-%m-%d").date()
                res_end = datetime.strptime(reservation["end_date"], "%Y-%m-%d").date()
            except Exception:
                continue  # Skip reservations with bad dates

            # Overlaps if not (res_end < query_start or res_start > query_end)
            if res_end < query_start or res_start > query_end:
                continue  # No overlap

            if status is not None and reservation["status"] != status:
                continue

            result.append(reservation)

        return {"success": True, "data": result}

    def check_room_availability(self, room_id: str, start_date: str, end_date: str) -> dict:
        """
        Check whether a specific room is available for a given date range.

        Args:
            room_id (str): The room's unique identifier.
            start_date (str): The requested start date (YYYY-MM-DD).
            end_date (str): The requested end date (YYYY-MM-DD), must be on or after start_date.

        Returns:
            dict:
                If success:
                    {
                        "success": True,
                        "available": bool  # True if available, False if not
                    }
                If error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Room must exist.
            - Date range must be valid.
            - Availability is blocked by any overlapping "booked" or "checked-in" reservations.
            - Rooms in "maintenance" or "cleaning" status are treated as unavailable regardless of dates.
            - Date format must be 'YYYY-MM-DD'.
        """

        # Validate room existence
        if room_id not in self.rooms:
            return { "success": False, "error": "Room does not exist" }

        # Validate date format and range
        try:
            req_start = self._parse_date(start_date)
            req_end = self._parse_date(end_date)
        except ValueError:
            return { "success": False, "error": "Invalid date format; use YYYY-MM-DD" }

        if req_start > req_end:
            return { "success": False, "error": "end_date must be on or after start_date" }

        # Out-of-service rooms are unavailable regardless of reservation dates.
        occupancy_status = self.rooms[room_id].get("occupancy_status", "").lower()
        if occupancy_status in {"maintenance", "cleaning"}:
            return { "success": True, "available": False }

        # Check for overlapping reservations
        blocking_statuses = {"booked", "checked-in"}
        for reservation in self.reservations.values():
            if reservation["room_id"] != room_id:
                continue
            if reservation["status"].lower() not in blocking_statuses:
                continue
            # Reservation date interval
            try:
                res_start = self._parse_date(reservation["start_date"])
                res_end = self._parse_date(reservation["end_date"])
            except Exception:
                # Skip reservations with bad data
                continue
            if self._ranges_overlap(req_start, req_end, res_start, res_end):
                return { "success": True, "available": False }

        return { "success": True, "available": True }

    def get_room_occupancy_status(self, room_id: str) -> dict:
        """
        Query the current occupancy status of a specified room.

        Args:
            room_id (str): The unique identifier for the room.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "room_id": <room_id>,
                            "occupancy_status": <occupancy_status>
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Room does not exist"
                    }

        Constraints:
            - The room_id must exist in the system.
        """
        room = self.rooms.get(room_id)
        if not room:
            return {"success": False, "error": "Room does not exist"}
        return {
            "success": True,
            "data": {
                "room_id": room_id,
                "occupancy_status": room["occupancy_status"]
            }
        }

    def get_reservation_status(self, reservation_id: str) -> dict:
        """
        Retrieve the status of a reservation by its reservation_id.

        Args:
            reservation_id (str): The unique identifier of the reservation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str  # Reservation status (e.g., 'booked', 'checked-in', 'canceled')
                    }
                On error:
                    {
                        "success": False,
                        "error": "Reservation not found"
                    }

        Constraints:
            - The reservation_id must exist in the system.
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return { "success": False, "error": "Reservation not found" }
        return { "success": True, "data": reservation["status"] }

    def list_guest_reservations(self, guest_id: str) -> dict:
        """
        List all reservations made by a specific guest.

        Args:
            guest_id (str): The unique identifier for the guest.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - data (List[ReservationInfo]): Reservations made by the guest (empty list if none), if success.
                - error (str): If failure, error message.

        Constraints:
            - The guest_id must exist in the system.
        """
        if guest_id not in self.guests:
            return { "success": False, "error": "Guest does not exist" }

        guest_reservations = [
            reservation for reservation in self.reservations.values()
            if reservation["guest_id"] == guest_id
        ]

        return { "success": True, "data": guest_reservations }

    def find_available_rooms(self, start_date: str, end_date: str, room_type: str = None) -> dict:
        """
        For a given date range and (optional) room type, return a list of all rooms available for booking.

        Args:
            start_date (str): Desired booking start date (YYYY-MM-DD).
            end_date (str): Desired booking end date (YYYY-MM-DD).
            room_type (str, optional): Room type filter (e.g., 'single', 'double').

        Returns:
            dict: {
                "success": True,
                "data": List[RoomInfo],  # List of available rooms matching criteria (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of invalid input or error
            }

        Constraints:
            - Only rooms not reserved (active reservations) or occupied in overlapping date ranges are returned.
            - If room_type is provided, only rooms of that type are included.
        """

        try:
            req_start = self._parse_date(start_date)
            req_end = self._parse_date(end_date)
        except Exception:
            return { "success": False, "error": "Invalid date format. Use YYYY-MM-DD." }

        if req_start > req_end:
            return { "success": False, "error": "Start date cannot be after end date." }

        normalized_room_type = room_type
        if isinstance(normalized_room_type, str) and normalized_room_type.strip() == "":
            normalized_room_type = None

        # Reservation statuses that block availability (active)
        available_rooms = []
        for room_id, room in self.rooms.items():
            # Room type filter
            if normalized_room_type is not None and room["type"] != normalized_room_type:
                continue

            # Out-of-service rooms are never returned as available.
            if room.get("occupancy_status", "").lower() in {"maintenance", "cleaning"}:
                continue

            # Check for any active reservation for this room overlapping the requested period
            is_available = True
            for res in self.reservations.values():
                if res["room_id"] != room_id:
                    continue
                if not self._reservation_blocks_booking(res):
                    continue
                try:
                    res_start = self._parse_date(res["start_date"])
                    res_end = self._parse_date(res["end_date"])
                except Exception:
                    continue
                if self._ranges_overlap(req_start, req_end, res_start, res_end):
                    is_available = False
                    break

            if is_available:
                available_rooms.append(room)

        return { "success": True, "data": available_rooms }


    def create_reservation(
        self,
        room_id: str,
        guest_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Book a room for a guest for a specific date range, enforcing constraints:
        - Room exists and type is as required.
        - Guest exists.
        - Date range is valid (YYYY-MM-DD, start <= end).
        - Room is not already reserved/occupied for any overlapping date by an active reservation.
        - Only active reservations block new bookings (status not 'canceled').
    
        Args:
            room_id (str): ID of room to book.
            guest_id (str): ID of guest making reservation.
            start_date (str): Reservation start date (YYYY-MM-DD).
            end_date (str): Reservation end date (YYYY-MM-DD).
    
        Returns:
            dict: {
                "success": True,
                "message": "Reservation created",
                "reservation_id": <reservation_id>
            } on success; or
            {
                "success": False,
                "error": <reason>
            } on failure.
        """
        # Basic existence checks
        if room_id not in self.rooms:
            return {"success": False, "error": "Room does not exist"}
        if guest_id not in self.guests:
            return {"success": False, "error": "Guest does not exist"}
        if not start_date or not end_date:
            return {"success": False, "error": "Start and end date are required"}
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            return {"success": False, "error": "Invalid date format; use YYYY-MM-DD"}
        if start_dt > end_dt:
            return {"success": False, "error": "Start date must be on or before end date"}

        room_status = self.rooms[room_id].get("occupancy_status", "").lower()
        if room_status in {"maintenance", "cleaning"}:
            return {"success": False, "error": f"Room is currently unavailable due to status '{room_status}'"}

        # Check for overlapping reservations on the same room (excluding inactive reservations)
        for r in self.reservations.values():
            if r["room_id"] != room_id or not self._reservation_blocks_booking(r):
                continue
            try:
                r_start = self._parse_date(r["start_date"])
                r_end = self._parse_date(r["end_date"])
            except Exception:
                continue  # skip corrupted reservation

            if self._ranges_overlap(start_dt, end_dt, r_start, r_end):
                return {"success": False, "error": "Room is already reserved for overlapping date range"}

        # Create unique reservation_id
        reservation_id = str(uuid.uuid4())
        reservation_info = {
            "reservation_id": reservation_id,
            "room_id": room_id,
            "guest_id": guest_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "booked"
        }
        self.reservations[reservation_id] = reservation_info

        return {
            "success": True,
            "message": "Reservation created",
            "reservation_id": reservation_id
        }

    def cancel_reservation(self, reservation_id: str) -> dict:
        """
        Cancel a reservation by setting its status to 'canceled', if allowed.

        Args:
            reservation_id (str): The unique ID of the reservation to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Reservation <id> cancelled."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - Only reservations that exist and are not already 'canceled' or 'checked-out' can be canceled.
            - Updates the status in-place.
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return { "success": False, "error": "Reservation does not exist." }

        if reservation["status"] == "canceled":
            return { "success": False, "error": "Reservation is already canceled." }

        if reservation["status"] == "checked-out":
            return { "success": False, "error": "Cannot cancel a reservation that has been checked out." }

        reservation["status"] = "canceled"
        self.reservations[reservation_id] = reservation

        return {
            "success": True,
            "message": f"Reservation {reservation_id} cancelled."
        }

    def check_in_guest(self, reservation_id: str) -> dict:
        """
        Mark a reservation as 'checked-in' and update the associated room's occupancy_status to 'occupied'.

        Args:
            reservation_id (str): The reservation to check in.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Guest checked in, reservation and room updated"
                  }
                - On failure: {
                    "success": False,
                    "error": <reason>
                  }

        Constraints:
            - Reservation must exist and its status must be 'booked'.
            - The associated room must exist and must not already be 'occupied'.
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return { "success": False, "error": "Reservation does not exist" }

        if reservation["status"] != "booked":
            return { "success": False, "error": f"Cannot check in: reservation status is '{reservation['status']}'" }

        room_id = reservation["room_id"]
        room = self.rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Associated room does not exist" }

        if room["occupancy_status"] == "occupied":
            return { "success": False, "error": "Room is already occupied" }

        # Update reservation and room status
        reservation["status"] = "checked-in"
        room["occupancy_status"] = "occupied"

        # Save updates
        self.reservations[reservation_id] = reservation
        self.rooms[room_id] = room

        return { "success": True, "message": "Guest checked in, reservation and room updated" }

    def check_out_guest(self, reservation_id: str) -> dict:
        """
        Update reservation and associated room state to reflect guest check-out.

        Args:
            reservation_id (str): The ID of the reservation for which to check out the guest.

        Returns:
            dict:
                - On success: { "success": True, "message": "Guest checked out successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Reservation must exist and be in 'checked-in' status.
            - Room associated with reservation must exist.
            - After checkout, reservation status set to 'checked-out', room's occupancy_status set to 'available'.
        """
        # Retrieve reservation
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return { "success": False, "error": "Reservation does not exist." }

        # Check that reservation is in 'checked-in' status
        if reservation['status'] != 'checked-in':
            return { "success": False, "error": "Reservation is not in a checked-in state." }

        room_id = reservation['room_id']
        room = self.rooms.get(room_id)
        if not room:
            return { "success": False, "error": "Associated room does not exist." }

        # Update reservation status
        reservation['status'] = 'checked-out'
        self.reservations[reservation_id] = reservation

        # Update room occupancy status
        room['occupancy_status'] = 'available'
        self.rooms[room_id] = room

        return { "success": True, "message": "Guest checked out successfully." }

    def update_room_occupancy_status(self, room_id: str, occupancy_status: str) -> dict:
        """
        Change or set a room's occupancy status (e.g., vacant, occupied, cleaning).

        Args:
            room_id (str): The unique ID of the room to update.
            occupancy_status (str): The new occupancy status to assign to the room.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Room occupancy status updated to <occupancy_status> for room <room_id>" }
                On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - The room with the given room_id must exist.
            - (Optionally) If valid statuses are limited, only allow those values; otherwise accept any.
        """
        allowed_statuses = {"available", "vacant", "occupied", "cleaning", "maintenance"}
        if room_id not in self.rooms:
            return { "success": False, "error": f"Room ID '{room_id}' does not exist" }
        if occupancy_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid occupancy status '{occupancy_status}'. Allowed: {sorted(allowed_statuses)}" }
    
        self.rooms[room_id]["occupancy_status"] = occupancy_status
        return { 
            "success": True, 
            "message": f"Room occupancy status updated to '{occupancy_status}' for room '{room_id}'" 
        }

    def modify_reservation_dates(
        self, 
        reservation_id: str, 
        new_start_date: str = None, 
        new_end_date: str = None
    ) -> dict:
        """
        Change the start or end date of an existing reservation, enforcing constraints.

        Args:
            reservation_id (str): The ID of the reservation to modify.
            new_start_date (str, optional): New start date in 'YYYY-MM-DD' format. If None, retains old value.
            new_end_date (str, optional): New end date in 'YYYY-MM-DD' format. If None, retains old value.
    
        Returns:
            dict: 
             - On success: { "success": True, "message": "Reservation dates updated" }
             - On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - Reservation must exist and be modifiable (e.g. not 'cancelled' or 'checked-out').
            - new_start_date <= new_end_date (if both provided).
            - No overlap with other ACTIVE reservations for the same room (status 'booked' or 'checked-in').
        """

        # Lookup reservation
        res = self.reservations.get(reservation_id)
        if res is None:
            return {"success": False, "error": "Reservation does not exist"}

        # Only disallow clearly finalized/inactive reservations.
        if res["status"] in ("canceled", "checked-out"):
            return {"success": False, "error": "Reservation cannot be modified in its current status"}

        # Current dates
        cur_start = res["start_date"]
        cur_end = res["end_date"]

        start_date = new_start_date if new_start_date is not None else cur_start
        end_date = new_end_date if new_end_date is not None else cur_end

        # Validate date order
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            if end_dt < start_dt:
                return {"success": False, "error": "End date cannot be before start date"}
        except Exception:
            return {"success": False, "error": "Invalid date format"}

        room_id = res["room_id"]

        # Check for overlap with other active reservations for the room
        for other in self.reservations.values():
            if (
                other["reservation_id"] != reservation_id and
                other["room_id"] == room_id and
                other["status"] in ("booked", "checked-in")  # only active block
            ):
                # Check overlap: [a, b] and [c, d] overlap if (a <= d) and (c <= b)
                other_start = other["start_date"]
                other_end = other["end_date"]
                try:
                    other_start_dt = datetime.strptime(other_start, '%Y-%m-%d')
                    other_end_dt = datetime.strptime(other_end, '%Y-%m-%d')
                except Exception:
                    continue  # skip invalid
                if self._ranges_overlap(start_dt.date(), end_dt.date(), other_start_dt.date(), other_end_dt.date()):
                    return {"success": False, "error": "Date range overlaps with another reservation for this room"}

        # Passed checks; update
        res["start_date"] = start_date
        res["end_date"] = end_date
        self.reservations[reservation_id] = res

        return {"success": True, "message": "Reservation dates updated"}

    def update_reservation_status(self, reservation_id: str, new_status: str) -> dict:
        """
        Update the status (e.g., 'booked', 'checked-in', 'canceled') of a reservation.

        Args:
            reservation_id (str): The unique identifier of the reservation to update.
            new_status (str): The new status string. Must be one of: 'booked', 'checked-in', 'canceled'.

        Returns:
            dict: {
                "success": True,
                "message": "Reservation status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Reservation with reservation_id must exist.
            - new_status must be a valid status value.
        """
        valid_statuses = {"booked", "checked-in", "canceled"}
        if reservation_id not in self.reservations:
            return {"success": False, "error": "Reservation does not exist"}
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Valid statuses are: {', '.join(valid_statuses)}."}

        self.reservations[reservation_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Reservation status updated to '{new_status}'."
        }

    def register_guest(self, name: str, contact_info: str) -> dict:
        """
        Register a new guest in the hotel reservation system.

        Args:
            name (str): Full name of the guest.
            contact_info (str): The guest's contact details.

        Returns:
            dict: {
                "success": True,
                "message": "Guest registered with guest_id <guest_id>"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - guest_id is auto-generated and unique.
            - Name and contact_info must not be empty.
        """
        if not name or not contact_info:
            return { "success": False, "error": "Name and contact information must be provided." }

        # Generate unique guest_id
        num = 1
        while True:
            guest_id = f"GUEST{num:04d}"
            if guest_id not in self.guests:
                break
            num += 1

        self.guests[guest_id] = {
            "guest_id": guest_id,
            "name": name,
            "contact_info": contact_info
        }

        return {
            "success": True,
            "message": f"Guest registered with guest_id {guest_id}"
        }


class HotelReservationSystem(BaseEnv):
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

    def list_rooms_by_type(self, **kwargs):
        return self._call_inner_tool('list_rooms_by_type', kwargs)

    def get_room_info(self, **kwargs):
        return self._call_inner_tool('get_room_info', kwargs)

    def list_all_rooms(self, **kwargs):
        return self._call_inner_tool('list_all_rooms', kwargs)

    def get_room_reservations(self, **kwargs):
        return self._call_inner_tool('get_room_reservations', kwargs)

    def get_reservations_in_date_range(self, **kwargs):
        return self._call_inner_tool('get_reservations_in_date_range', kwargs)

    def check_room_availability(self, **kwargs):
        return self._call_inner_tool('check_room_availability', kwargs)

    def get_room_occupancy_status(self, **kwargs):
        return self._call_inner_tool('get_room_occupancy_status', kwargs)

    def get_reservation_status(self, **kwargs):
        return self._call_inner_tool('get_reservation_status', kwargs)

    def list_guest_reservations(self, **kwargs):
        return self._call_inner_tool('list_guest_reservations', kwargs)

    def find_available_rooms(self, **kwargs):
        return self._call_inner_tool('find_available_rooms', kwargs)

    def create_reservation(self, **kwargs):
        return self._call_inner_tool('create_reservation', kwargs)

    def cancel_reservation(self, **kwargs):
        return self._call_inner_tool('cancel_reservation', kwargs)

    def check_in_guest(self, **kwargs):
        return self._call_inner_tool('check_in_guest', kwargs)

    def check_out_guest(self, **kwargs):
        return self._call_inner_tool('check_out_guest', kwargs)

    def update_room_occupancy_status(self, **kwargs):
        return self._call_inner_tool('update_room_occupancy_status', kwargs)

    def modify_reservation_dates(self, **kwargs):
        return self._call_inner_tool('modify_reservation_dates', kwargs)

    def update_reservation_status(self, **kwargs):
        return self._call_inner_tool('update_reservation_status', kwargs)

    def register_guest(self, **kwargs):
        return self._call_inner_tool('register_guest', kwargs)
