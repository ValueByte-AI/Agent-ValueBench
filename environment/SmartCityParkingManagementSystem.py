# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import math
import uuid
from typing import Optional, Union



class ParkingLotInfo(TypedDict):
    lot_id: str
    name: str
    latitude: float
    longitude: float
    capacity: int
    available_spaces: int
    operational_status: str

class ReservationInfo(TypedDict):
    reservation_id: str
    lot_id: str
    user_id: str
    reserved_spaces: int
    reservation_start_time: str  # or float (timestamp)
    reservation_end_time: str    # or float (timestamp)
    reservation_status: str

class HistoricalUsageInfo(TypedDict):
    lot_id: str
    timestamp: str  # or float (timestamp)
    spaces_occupied: int
    spaces_available: int

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Smart city parking management environment.
        """

        # ParkingLots: {lot_id: ParkingLotInfo}
        # Attributes: lot_id, name, latitude, longitude, capacity, available_spaces, operational_status
        self.parking_lots: Dict[str, ParkingLotInfo] = {}

        # Reservations: {reservation_id: ReservationInfo}
        # Attributes: reservation_id, lot_id, user_id, reserved_spaces, reservation_start_time, reservation_end_time, reservation_status
        self.reservations: Dict[str, ReservationInfo] = {}

        # HistoricalUsage: [HistoricalUsageInfo, ...]
        # Attributes: lot_id, timestamp, spaces_occupied, spaces_available
        self.historical_usage: List[HistoricalUsageInfo] = []

        # Hidden bookkeeping:
        # Preserve non-reservation occupancy implied by the initial state (or by
        # explicit update_available_spaces calls). This lets us keep
        # available_spaces consistent with both background occupancy and active
        # reservations.
        self._non_reservation_occupancy_by_lot: Dict[str, int] = {}

        # Constraints:
        # - available_spaces ≤ capacity for each ParkingLot
        # - Reservations cannot be made for more spaces than currently available.
        # - Only parking lots with operational_status = "open" are available for reservations and queries.
        # - User location is input for queries but not persisted unless tied to events/reservations.

    def _get_active_reserved_spaces(self, lot_id: str) -> int:
        return sum(
            reservation.get("reserved_spaces", 0)
            for reservation in self.reservations.values()
            if reservation.get("lot_id") == lot_id and reservation.get("reservation_status") == "active"
        )

    def _initialize_non_reservation_occupancy(self) -> None:
        occupancy_by_lot: Dict[str, int] = {}
        for lot_id, lot in self.parking_lots.items():
            active_reserved_spaces = self._get_active_reserved_spaces(lot_id)
            available_spaces = int(lot.get("available_spaces", 0) or 0)
            capacity = int(lot.get("capacity", 0) or 0)
            occupancy_by_lot[lot_id] = max(capacity - active_reserved_spaces - available_spaces, 0)
        self._non_reservation_occupancy_by_lot = occupancy_by_lot

    def _set_non_reservation_occupancy_from_available(self, lot_id: str) -> None:
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return
        active_reserved_spaces = self._get_active_reserved_spaces(lot_id)
        available_spaces = int(lot.get("available_spaces", 0) or 0)
        capacity = int(lot.get("capacity", 0) or 0)
        self._non_reservation_occupancy_by_lot[lot_id] = max(
            capacity - active_reserved_spaces - available_spaces,
            0,
        )

    def _recompute_available_spaces(self, lot_id: str) -> None:
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return
        if lot_id not in self._non_reservation_occupancy_by_lot:
            self._initialize_non_reservation_occupancy()
        active_reserved_spaces = self._get_active_reserved_spaces(lot_id)
        non_reservation_occupancy = self._non_reservation_occupancy_by_lot.get(lot_id, 0)
        lot["available_spaces"] = max(
            lot.get("capacity", 0) - non_reservation_occupancy - active_reserved_spaces,
            0,
        )

    def list_open_parking_lots(self) -> dict:
        """
        Retrieve all parking lots currently operational (operational_status == "open").

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ParkingLotInfo],  # List of open parking lots (may be empty)
                }
                OR
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Only parking lots with operational_status == "open" are included in the result.
        """
        open_lots = [
            lot_info
            for lot_info in self.parking_lots.values()
            if lot_info.get("operational_status", "").lower() == "open"
        ]
        return {"success": True, "data": open_lots}

    def filter_parking_lots_by_distance(
        self,
        latitude: float,
        longitude: float,
        radius: float
    ) -> dict:
        """
        Given a geographic location and radius (in kilometers), return all 'open'
        parking lots within that range.

        Args:
            latitude (float): Reference latitude, must be between -90 and 90.
            longitude (float): Reference longitude, must be between -180 and 180.
            radius (float): Search radius in kilometers, must be > 0.

        Returns:
            dict: {
                "success": True,
                "data": List[ParkingLotInfo],  # May be empty if no lots within range.
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only parking lots with operational_status == "open" are considered.
            - Invalid location/radius parameters return failure.
        """

        # Validate input
        if not (-90.0 <= latitude <= 90.0):
            return { "success": False, "error": "Invalid latitude value" }
        if not (-180.0 <= longitude <= 180.0):
            return { "success": False, "error": "Invalid longitude value" }
        if not (radius > 0):
            return { "success": False, "error": "Radius must be greater than 0" }

        def haversine(lat1, lon1, lat2, lon2):
            # Earth radius in kilometers
            R = 6371.0
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = (math.sin(dphi/2.0)**2 +
                 math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        results = []
        for lot in self.parking_lots.values():
            if lot.get("operational_status") != "open":
                continue
            lot_lat = lot.get("latitude")
            lot_lon = lot.get("longitude")
            if lot_lat is None or lot_lon is None:
                continue
            distance = haversine(latitude, longitude, lot_lat, lot_lon)
            if distance <= radius:
                results.append(lot)

        return { "success": True, "data": results }

    def get_available_spaces(self, lot_id: str) -> dict:
        """
        Query the number of currently available spaces for a specific, open parking lot.

        Args:
            lot_id (str): Identifier of the parking lot.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": {
                          "lot_id": str,
                          "available_spaces": int
                      }
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Reason, e.g., lot not found or not open
                    }
        Constraints:
            - Only lots with operational_status == "open" can be queried.
        """
        lot = self.parking_lots.get(lot_id)
        if lot is None:
            return {"success": False, "error": "Parking lot does not exist"}
        if lot["operational_status"] != "open":
            return {"success": False, "error": "Parking lot is not open for queries"}
        return {
            "success": True,
            "data": {
                "lot_id": lot_id,
                "available_spaces": lot["available_spaces"]
            }
        }

    def get_lot_with_max_available_spaces(self, candidate_lot_ids: list) -> dict:
        """
        Given a candidate list of parking lot IDs, select the open parking lot with the highest available_spaces.

        Args:
            candidate_lot_ids (list of str): List of parking lot IDs to consider.

        Returns:
            dict: 
               { "success": True, "data": <ParkingLotInfo> }
               or
               { "success": False, "error": str }

        Constraints:
            - Only parking lots with operational_status == "open" are considered.
            - If none are open or exist, returns an error.
        """
        if not candidate_lot_ids or not isinstance(candidate_lot_ids, list):
            return {"success": False, "error": "No candidate lot IDs provided."}

        open_lots = [
            self.parking_lots[lot_id]
            for lot_id in candidate_lot_ids
            if lot_id in self.parking_lots and self.parking_lots[lot_id]["operational_status"] == "open"
        ]

        if not open_lots:
            return {"success": False, "error": "No open lots found in candidate list"}

        lot_with_max = max(open_lots, key=lambda lot: lot["available_spaces"])
        return {"success": True, "data": lot_with_max}

    def get_parking_lot_info(self, lot_id: str = None, name: str = None) -> dict:
        """
        Retrieve details (ParkingLotInfo) for a parking lot by lot_id or name.
    
        Args:
            lot_id (str, optional): Unique identifier of the parking lot.
            name (str, optional): Name of the parking lot.

        Returns:
            dict: 
                {"success": True, "data": ParkingLotInfo} if found;
                {"success": False, "error": str} otherwise.

        Constraints:
            - At least one of lot_id or name must be provided.
            - Closed lots remain queryable so coordinators can inspect and plan around them.
        """
        if lot_id is None and name is None:
            return {"success": False, "error": "Must provide either lot_id or name."}
    
        lot = None

        if lot_id is not None:
            lot = self.parking_lots.get(lot_id)
            if lot is None:
                return {"success": False, "error": f"No parking lot found with lot_id: {lot_id}."}
            return {"success": True, "data": lot}

        # If only name is provided, find by exact name regardless of status
        for info in self.parking_lots.values():
            if info["name"] == name:
                return {"success": True, "data": info}
    
        return {"success": False, "error": f"No parking lot found with name: {name}."}

    def get_reservations_by_user(self, user_id: str) -> dict:
        """
        List all reservations made by a specific user.

        Args:
            user_id (str): The identifier of the user for whom to fetch reservations.

        Returns:
            dict: {
                "success": True,
                "data": List[ReservationInfo]  # List may be empty if user has no reservations
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. invalid input)
            }

        Constraints:
            - user_id should not be None or empty.
        """
        if not user_id or not isinstance(user_id, str):
            return {"success": False, "error": "Invalid user_id"}
    
        user_reservations = [
            reservation for reservation in self.reservations.values()
            if reservation["user_id"] == user_id
        ]
        return {
            "success": True,
            "data": user_reservations
        }

    def get_reservations_by_lot(self, lot_id: str) -> dict:
        """
        List all current reservations for a specific parking lot.

        Args:
            lot_id (str): The unique identifier of the parking lot.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ReservationInfo]  # Reservations for this lot (possibly empty)
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - The specified lot_id must exist.
            - The parking lot must have operational_status == "open".
        """
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return { "success": False, "error": "Parking lot does not exist" }
        if lot["operational_status"] != "open":
            return { "success": False, "error": "Parking lot is not open for queries" }

        reservations = [
            r
            for r in self.reservations.values()
            if r["lot_id"] == lot_id
        ]

        return { "success": True, "data": reservations }

    def check_lot_operational_status(self, lot_id: str) -> dict:
        """
        Query the operational status of the specified parking lot.

        Args:
            lot_id (str): Identifier of the parking lot.

        Returns:
            dict: {
                "success": True,
                "data": str  # The operational_status (e.g., "open", "closed", etc.)
            }
            or
            {
                "success": False,
                "error": "Parking lot not found"
            }
        Constraints:
            - lot_id must exist in self.parking_lots.
        """
        lot = self.parking_lots.get(lot_id)
        if lot is None:
            return { "success": False, "error": "Parking lot not found" }
        return { "success": True, "data": lot["operational_status"] }

    def get_historical_usage_by_lot(self, lot_id: str) -> dict:
        """
        Retrieve historical occupancy and availability data for the specified parking lot.

        Args:
            lot_id (str): Unique identifier of the parking lot.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[HistoricalUsageInfo]  # List may be empty if no data.
                    }
                On failure (e.g., invalid lot_id):
                    {
                        "success": False,
                        "error": str  # Description of the error, e.g. Parking lot does not exist
                    }

        Constraints:
            - The provided lot_id must correspond to an existing parking lot.
        """
        if lot_id not in self.parking_lots:
            return { "success": False, "error": "Parking lot does not exist" }

        usage_records = [
            usage for usage in self.historical_usage
            if usage["lot_id"] == lot_id
        ]

        return { "success": True, "data": usage_records }

    def get_lot_capacity(self, lot_id: str) -> dict:
        """
        Query the maximum capacity for a specific parking lot.

        Args:
            lot_id (str): The unique identifier for the parking lot.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "lot_id": str,
                        "capacity": int
                    }
                }
                On failure (e.g., invalid lot_id):
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The specified lot_id must exist in the system.
        """
        lot_info = self.parking_lots.get(lot_id)
        if not lot_info:
            return {"success": False, "error": "Parking lot not found"}

        return {
            "success": True,
            "data": {
                "lot_id": lot_id,
                "capacity": lot_info["capacity"]
            }
        }


    def create_reservation(
        self,
        lot_id: str,
        user_id: str,
        reserved_spaces: int,
        reservation_start_time: Union[str, float],
        reservation_end_time: Union[str, float]
    ) -> dict:
        """
        Reserve one or more spaces in a parking lot if availability and operational status allow.

        Args:
            lot_id (str): The ID of the parking lot.
            user_id (str): ID of the user making the reservation.
            reserved_spaces (int): Number of spaces to reserve (must be > 0).
            reservation_start_time (str/float): Reservation start time.
            reservation_end_time (str/float): Reservation end time.

        Returns:
            dict: On success:
                    {
                      "success": True,
                      "message": "Reservation created successfully.",
                      "reservation_id": <new_reservation_id>
                    }
                  On failure:
                    {
                      "success": False,
                      "error": <description of reason>
                    }

        Constraints:
            - Lot must exist and be open.
            - reserved_spaces must be positive and ≤ lot's available_spaces.
            - Lot's available_spaces is decremented upon successful reservation.
        """
        # Check if lot exists
        if lot_id not in self.parking_lots:
            return { "success": False, "error": "Parking lot does not exist." }

        lot_info = self.parking_lots[lot_id]
        if lot_info["operational_status"] != "open":
            return { "success": False, "error": "Parking lot is not open for reservations." }

        # Validate reserved_spaces
        if not isinstance(reserved_spaces, int) or reserved_spaces <= 0:
            return { "success": False, "error": "Invalid reserved_spaces (must be positive integer)." }

        if reserved_spaces > lot_info["available_spaces"]:
            return { "success": False, "error": "Not enough available spaces in the parking lot." }

        # (Optional basic time sanity check)
        if (reservation_end_time is not None and reservation_start_time is not None and
                reservation_end_time < reservation_start_time):
            return { "success": False, "error": "reservation_end_time must be after reservation_start_time." }

        # Generate unique reservation_id
        reservation_id = str(uuid.uuid4())

        # Create reservation entry
        reservation: ReservationInfo = {
            "reservation_id": reservation_id,
            "lot_id": lot_id,
            "user_id": user_id,
            "reserved_spaces": reserved_spaces,
            "reservation_start_time": reservation_start_time,
            "reservation_end_time": reservation_end_time,
            "reservation_status": "active",
        }

        # Store reservation
        self.reservations[reservation_id] = reservation

        # Keep the lot state consistent with active reservations.
        self._recompute_available_spaces(lot_id)

        return {
            "success": True,
            "message": "Reservation created successfully.",
            "reservation_id": reservation_id
        }

    def cancel_reservation(self, reservation_id: str) -> dict:
        """
        Cancel an existing reservation and update the available_spaces for the associated lot.

        Args:
            reservation_id (str): The unique identifier for the reservation to cancel.

        Returns:
            dict:
                {"success": True, "message": "Reservation cancelled and availability updated."}
                or
                {"success": False, "error": <reason>}

        Constraints:
            - Only reservations that exist and are currently active can be cancelled.
            - When cancelling, reserved spaces are released back into the lot's available_spaces.
            - After release, available_spaces for the lot should not exceed its capacity.
            - If the reservation or lot does not exist, or reservation is already cancelled, operation fails.
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return {"success": False, "error": "Reservation does not exist."}

        if reservation.get("reservation_status") != "active":
            return {"success": False, "error": "Reservation is not active or already cancelled."}

        lot_id = reservation.get("lot_id")
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return {"success": False, "error": "Associated parking lot does not exist."}

        reserved_spaces = reservation.get("reserved_spaces", 0)
        # Cancel the reservation
        reservation["reservation_status"] = "cancelled"

        # Keep the lot state consistent with the remaining active reservations.
        self._recompute_available_spaces(lot_id)

        return {"success": True, "message": "Reservation cancelled and availability updated."}

    def update_available_spaces(self, lot_id: str, new_available_spaces: int) -> dict:
        """
        Adjust the available_spaces for a parking lot.

        Args:
            lot_id (str): The unique ID of the parking lot to update.
            new_available_spaces (int): The new integer value for available spaces.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of the update
            }
            OR
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Lot must exist in the system.
            - Lot's operational_status must be "open".
            - new_available_spaces must be >= 0 and <= lot's capacity.
        """
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return { "success": False, "error": f"Parking lot with id '{lot_id}' does not exist." }

        if lot["operational_status"] != "open":
            return { "success": False, "error": "Cannot update: parking lot is not open." }

        capacity = lot["capacity"]
        if not (0 <= new_available_spaces <= capacity):
            return {
                "success": False,
                "error": f"new_available_spaces must be between 0 and {capacity}."
            }

        lot["available_spaces"] = new_available_spaces
        self._set_non_reservation_occupancy_from_available(lot_id)
        return { "success": True, "message": f"Available spaces updated for lot {lot_id}." }

    def change_lot_operational_status(self, lot_id: str, operational_status: str) -> dict:
        """
        Set a parking lot's operational_status to "open" or "closed".

        Args:
            lot_id (str): The unique identifier for the parking lot.
            operational_status (str): The new operational status ("open" or "closed").

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Operational status of parking lot <lot_id> set to <operational_status>" }
                On failure:
                    { "success": False, "error": "reason for failure" }

        Constraints:
            - Only "open" or "closed" are valid operational status values.
            - lot_id must exist in the system.
        """
        if lot_id not in self.parking_lots:
            return { "success": False, "error": "Parking lot does not exist" }
        if operational_status not in ("open", "closed"):
            return { "success": False, "error": "Invalid operational_status: must be 'open' or 'closed'" }

        self.parking_lots[lot_id]["operational_status"] = operational_status
        return {
            "success": True,
            "message": f"Operational status of parking lot {lot_id} set to {operational_status}"
        }

    def update_lot_capacity(self, lot_id: str, new_capacity: int) -> dict:
        """
        Change the capacity attribute of a parking lot (e.g., after remodeling).

        Args:
            lot_id (str): The identifier for the parking lot to update.
            new_capacity (int): The new capacity value to set (must be non-negative).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Capacity for lot <lot_id> updated to <new_capacity>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure."
                    }

        Constraints:
            - available_spaces must not exceed new_capacity after the update. If it does, adjust available_spaces down to match new_capacity.
            - new_capacity must be a non-negative integer.
            - lot_id must exist.
        """
        if lot_id not in self.parking_lots:
            return { "success": False, "error": f"Parking lot '{lot_id}' does not exist." }

        if not isinstance(new_capacity, int) or new_capacity < 0:
            return { "success": False, "error": "New capacity must be a non-negative integer." }

        lot = self.parking_lots[lot_id]
        previous_capacity = lot["capacity"]
        lot["capacity"] = new_capacity

        # Keep the lot state consistent with the remaining active reservations.
        self._recompute_available_spaces(lot_id)

        self.parking_lots[lot_id] = lot  # Update in state

        return {
            "success": True,
            "message": f"Capacity for lot {lot_id} updated to {new_capacity}."
        }

    def record_historical_usage(
        self,
        lot_id: str,
        timestamp: str,
        spaces_occupied: int,
        spaces_available: int
    ) -> dict:
        """
        Record a new historical usage entry for a parking lot.

        Args:
            lot_id (str): The parking lot's unique identifier.
            timestamp (str): The time when the record is captured (may be ISO8601 or float, per convention).
            spaces_occupied (int): Number of spaces occupied at the timestamp.
            spaces_available (int): Number of spaces available at the timestamp.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Historical usage recorded successfully." }
              - On failure: { "success": False, "error": "reason" }

        Constraints:
            - lot_id must exist in self.parking_lots.
            - spaces_occupied and spaces_available must be >= 0.
            - spaces_occupied + spaces_available should not exceed the lot's capacity.
        """
        lot = self.parking_lots.get(lot_id)
        if not lot:
            return { "success": False, "error": "Parking lot does not exist." }
        if not (isinstance(spaces_occupied, int) and spaces_occupied >= 0):
            return { "success": False, "error": "spaces_occupied must be a non-negative integer." }
        if not (isinstance(spaces_available, int) and spaces_available >= 0):
            return { "success": False, "error": "spaces_available must be a non-negative integer." }

        capacity = lot["capacity"]
        if spaces_occupied + spaces_available > capacity:
            return { "success": False, "error": "Sum of occupied and available spaces exceeds lot capacity." }

        record = {
            "lot_id": lot_id,
            "timestamp": timestamp,
            "spaces_occupied": spaces_occupied,
            "spaces_available": spaces_available
        }
        self.historical_usage.append(record)
        return { "success": True, "message": "Historical usage recorded successfully." }


class SmartCityParkingManagementSystem(BaseEnv):
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
        if hasattr(env, "_initialize_non_reservation_occupancy"):
            env._initialize_non_reservation_occupancy()

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "_non_reservation_occupancy_by_lot",
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

    def list_open_parking_lots(self, **kwargs):
        return self._call_inner_tool('list_open_parking_lots', kwargs)

    def filter_parking_lots_by_distance(self, **kwargs):
        return self._call_inner_tool('filter_parking_lots_by_distance', kwargs)

    def get_available_spaces(self, **kwargs):
        return self._call_inner_tool('get_available_spaces', kwargs)

    def get_lot_with_max_available_spaces(self, **kwargs):
        return self._call_inner_tool('get_lot_with_max_available_spaces', kwargs)

    def get_parking_lot_info(self, **kwargs):
        return self._call_inner_tool('get_parking_lot_info', kwargs)

    def get_reservations_by_user(self, **kwargs):
        return self._call_inner_tool('get_reservations_by_user', kwargs)

    def get_reservations_by_lot(self, **kwargs):
        return self._call_inner_tool('get_reservations_by_lot', kwargs)

    def check_lot_operational_status(self, **kwargs):
        return self._call_inner_tool('check_lot_operational_status', kwargs)

    def get_historical_usage_by_lot(self, **kwargs):
        return self._call_inner_tool('get_historical_usage_by_lot', kwargs)

    def get_lot_capacity(self, **kwargs):
        return self._call_inner_tool('get_lot_capacity', kwargs)

    def create_reservation(self, **kwargs):
        return self._call_inner_tool('create_reservation', kwargs)

    def cancel_reservation(self, **kwargs):
        return self._call_inner_tool('cancel_reservation', kwargs)

    def update_available_spaces(self, **kwargs):
        return self._call_inner_tool('update_available_spaces', kwargs)

    def change_lot_operational_status(self, **kwargs):
        return self._call_inner_tool('change_lot_operational_status', kwargs)

    def update_lot_capacity(self, **kwargs):
        return self._call_inner_tool('update_lot_capacity', kwargs)

    def record_historical_usage(self, **kwargs):
        return self._call_inner_tool('record_historical_usage', kwargs)
