# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ParcelInfo(TypedDict):
    tracking_number: str
    sender_id: str
    recipient_id: str
    current_status: str
    current_location: str
    delivery_estimate: str
    shipment_date: str
    delivery_date: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    address: str
    contact_info: str

class ParcelStatusHistoryInfo(TypedDict):
    tracking_number: str
    timestamp: str
    status: str
    location: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Represents the state of the parcel tracking system.
        """

        # Parcels: {tracking_number: ParcelInfo}
        # Maps each unique parcel by its tracking number and stores its current state and delivery info
        self.parcels: Dict[str, ParcelInfo] = {}

        # Users: {user_id: UserInfo}
        # Contains sender/recipient data for reference
        self.users: Dict[str, UserInfo] = {}

        # Parcel Status History: {tracking_number: List[ParcelStatusHistoryInfo]}
        # Stores full chronological history of status/location updates for each parcel
        self.parcel_status_history: Dict[str, List[ParcelStatusHistoryInfo]] = {}

        # Constraints:
        # - Each tracking number is unique system-wide.
        # - Status updates must be timestamped in chronological order.
        # - Delivery estimate and actual delivery date must be managed and, when actual delivery occurs, stored appropriately.
        # - Only authorized personnel can modify status or location data.

    def _is_authorized_staff(self, staff_id: str) -> bool:
        """
        Check whether a staff ID is authorized according to the configured authorized_staff state.

        Supports:
        - single staff id string
        - list / set / tuple of ids
        - dict keyed by staff id, or dict values with boolean-ish flags
        """
        authorized = getattr(self, "authorized_staff", None)
        if staff_id is None:
            return False
        if isinstance(authorized, str):
            return staff_id == authorized
        if isinstance(authorized, (list, tuple, set)):
            return staff_id in authorized
        if isinstance(authorized, dict):
            if staff_id in authorized:
                value = authorized[staff_id]
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.strip().lower() not in {"false", "0", "no", "inactive", ""}
                return bool(value)
            return False
        return False

    def get_parcel_by_tracking_number(self, tracking_number: str) -> dict:
        """
        Retrieve all current information about a parcel using its tracking number.

        Args:
            tracking_number (str): Unique parcel identifier.

        Returns:
            dict: {
                "success": True,
                "data": ParcelInfo,
            }
            or
            {
                "success": False,
                "error": str  # Reason why the query failed (e.g., parcel not found)
            }

        Constraints:
            - Each tracking number is unique system-wide.
        """
        parcel = self.parcels.get(tracking_number)
        if parcel is None:
            return { "success": False, "error": "Parcel not found" }
        return { "success": True, "data": parcel }

    def get_parcel_delivery_estimate(self, tracking_number: str) -> dict:
        """
        Query the estimated delivery date for a specific parcel.

        Args:
            tracking_number (str): The unique identifier for the parcel.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str  # The estimated delivery date string, may be empty if not set
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Parcel tracking number not found"
                    }

        Constraints:
            - Parcel with the provided tracking number must exist.
        """
        parcel = self.parcels.get(tracking_number)
        if not parcel:
            return {"success": False, "error": "Parcel tracking number not found"}
    
        return {"success": True, "data": parcel.get("delivery_estimate", "")}

    def get_parcel_actual_delivery_date(self, tracking_number: str) -> dict:
        """
        Query the actual delivery date for a parcel, if already delivered.

        Args:
            tracking_number (str): The tracking number of the parcel.

        Returns:
            dict: 
                - {"success": True, "data": <delivery_date (str)>} if delivered.
                - {"success": True, "data": None} if not yet delivered.
                - {"success": False, "error": <error_message>} if parcel does not exist.

        Constraints:
            - tracking_number must exist.
            - delivery_date must reflect delivery occurrence or be empty/None if not yet delivered.
        """
        parcel = self.parcels.get(tracking_number)
        if not parcel:
            return {"success": False, "error": "Parcel with this tracking number does not exist."}

        delivery_date = parcel.get("delivery_date")
        if delivery_date and delivery_date.strip():
            return {"success": True, "data": delivery_date}
        else:
            # delivery_date not set, not delivered yet
            return {"success": True, "data": None}

    def get_parcel_current_status(self, tracking_number: str) -> dict:
        """
        Retrieve the current status and location of a parcel.

        Args:
            tracking_number (str): The unique tracking number of the parcel.

        Returns:
            dict:
                success: True and data: {"current_status": str, "current_location": str} if found,
                success: False and error message if not found.

        Constraints:
            - The tracking number must exist in the system.
        """
        parcel = self.parcels.get(tracking_number)
        if not parcel:
            return {"success": False, "error": "Parcel not found"}

        return {
            "success": True,
            "data": {
                "current_status": parcel["current_status"],
                "current_location": parcel["current_location"]
            }
        }

    def get_parcel_status_history(self, tracking_number: str) -> dict:
        """
        Fetch the full chronological status/location update history for a given parcel.

        Args:
            tracking_number (str): The unique tracking number for the parcel.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[ParcelStatusHistoryInfo]  # Chronological history, possibly empty
                    }
                - If the parcel is not found:
                    {
                        "success": False,
                        "error": "Parcel not found"
                    }

        Constraints:
            - tracking_number must exist in the system (parcel must exist).
            - Returned list is expected to be in chronological order.
        """
        if tracking_number not in self.parcels:
            return {"success": False, "error": "Parcel not found"}

        history = self.parcel_status_history.get(tracking_number, [])
        return {"success": True, "data": history}

    def list_parcels_by_user(self, user_id: str) -> dict:
        """
        Retrieve all parcels for which the specified user is either the sender or recipient.

        Args:
            user_id (str): User identifier (must exist in the system).

        Returns:
            dict: {
                "success": True,
                "data": List[ParcelInfo]  # Zero or more parcels associated with the user
            }
            OR
            {
                "success": False,
                "error": str  # "User does not exist"
            }

        Constraints:
            - user_id must exist in self.users.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            parcel_info for parcel_info in self.parcels.values()
            if parcel_info["sender_id"] == user_id or parcel_info["recipient_id"] == user_id
        ]
        return { "success": True, "data": result }

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve user info (name, address, contact, etc.) for a given user_id.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": self.users[user_id] }

    def find_parcels_by_status(self, status: str) -> dict:
        """
        Query all parcels whose current status matches the specified status.

        Args:
            status (str): The target parcel status (e.g., "in transit", "delivered") to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[ParcelInfo]  # List of parcels currently at the given status,
                                          # empty if no match.
            }

        Constraints:
            - Query operation, no side effects.
            - Status match is case-sensitive (exact match).

        Edge Cases:
            - If no parcels match, returns "success": True and an empty list in "data".
        """
        result = [
            parcel_info for parcel_info in self.parcels.values()
            if parcel_info["current_status"] == status
        ]
        return { "success": True, "data": result }

    def update_parcel_status(
        self, 
        tracking_number: str, 
        new_status: str, 
        timestamp: str, 
        staff_id: str
    ) -> dict:
        """
        Updates the status of a parcel, only if called by authorized staff and the provided
        timestamp is not earlier than the last known status update.

        Args:
            tracking_number (str): Unique identifier for the parcel.
            new_status (str): The status to assign to the parcel.
            timestamp (str): Timestamp of the new status update (ISO8601 or similar, lexicographically comparable).
            staff_id (str): ID of the staff attempting this update.

        Returns:
            dict: On success: { "success": True, "message": "Parcel status updated" }
                  On error: { "success": False, "error": <reason> }

        Constraints:
            - Only authorized personnel may update statuses.
            - Status updates must be timestamped in monotonic (chronological) order.
        """

        if not self._is_authorized_staff(staff_id):
            return {"success": False, "error": "Permission denied: not authorized staff"}

        # Check parcel exists
        if tracking_number not in self.parcels:
            return {"success": False, "error": "Parcel not found"}

        # Get previous status history for ordering check
        history = self.parcel_status_history.get(tracking_number, [])
        if history:
            last_ts = history[-1]['timestamp']
            if timestamp < last_ts:
                return {"success": False, "error": "Timestamp is earlier than last update"}

        # Update current status in Parcels
        self.parcels[tracking_number]['current_status'] = new_status

        # Append to parcel status history
        status_entry = {
            "tracking_number": tracking_number,
            "timestamp": timestamp,
            "status": new_status,
            "location": self.parcels[tracking_number].get('current_location', '')
        }
        if tracking_number not in self.parcel_status_history:
            self.parcel_status_history[tracking_number] = []
        self.parcel_status_history[tracking_number].append(status_entry)

        return {"success": True, "message": "Parcel status updated"}

    def update_parcel_location(self, tracking_number: str, new_location: str, staff_user_id: str, timestamp: str) -> dict:
        """
        Update the current location of a parcel and append this event to its status history.
        Only authorized staff may perform this operation.

        Args:
            tracking_number (str): The unique parcel identifier.
            new_location (str): The location string to set as current.
            staff_user_id (str): The user attempting the update (must be staff).
            timestamp (str): The ISO8601-formatted time of this update.

        Returns:
            dict: {
                "success": True,
                "message": "Parcel location updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only staff may modify parcel location.
            - Must append update (timestamp, status, location) to parcel's status history.
            - Tracking number must exist.
        """
        if not self._is_authorized_staff(staff_user_id):
            return {"success": False, "error": "Permission denied: Only authorized staff can update parcel location."}

        if tracking_number not in self.parcels:
            return {"success": False, "error": "Parcel with given tracking number does not exist."}

        parcel = self.parcels[tracking_number]
        # Update the current_location field
        parcel["current_location"] = new_location

        # Append to status history
        history_entry = {
            "tracking_number": tracking_number,
            "timestamp": timestamp,
            "status": parcel["current_status"],
            "location": new_location
        }
        if tracking_number not in self.parcel_status_history:
            self.parcel_status_history[tracking_number] = []
        self.parcel_status_history[tracking_number].append(history_entry)

        return {"success": True, "message": "Parcel location updated."}

    def set_parcel_delivery_estimate(self, tracking_number: str, delivery_estimate: str, is_staff: bool) -> dict:
        """
        Modify the projected delivery date for a parcel.
        Only permitted for staff/authorized personnel.

        Args:
            tracking_number (str): The parcel tracking number whose estimate is to be updated.
            delivery_estimate (str): The new delivery estimate (date string, format not enforced here).
            is_staff (bool): True if calling user has staff privilege (authorization).

        Returns:
            dict: {"success": True, "message": "..."} on success,
                  {"success": False, "error": "..."} on error.

        Constraints:
            - Only staff can modify.
            - Parcel must exist.
        """
        if not is_staff:
            return {"success": False, "error": "Permission denied: only authorized staff can modify delivery estimates."}

        if tracking_number not in self.parcels:
            return {"success": False, "error": f"Parcel with tracking number {tracking_number} does not exist."}

        self.parcels[tracking_number]['delivery_estimate'] = delivery_estimate
        return {
            "success": True,
            "message": f"Delivery estimate updated for parcel {tracking_number}."
        }

    def record_parcel_delivery(self, tracking_number: str, delivery_date: str, staff_id: str) -> dict:
        """
        Mark a parcel as delivered: 
          - set 'Delivered' status,
          - set the actual delivery date,
          - append a corresponding record in the parcel's status history.
        (Staff-only operation.)

        Args:
            tracking_number (str): The parcel's unique tracking number.
            delivery_date (str): Actual delivery date-time (string, e.g., ISO8601).
            staff_id (str): Acting user ID (must be authorized staff).

        Returns:
            dict: 
                { "success": True, "message": "Parcel marked as delivered." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - The tracking number must exist.
            - Only staff can perform this operation.
            - Delivery date and status must be updated and recorded only if not already marked delivered.
            - Status history must be updated.
        """
        if not self._is_authorized_staff(staff_id):
            return {"success": False, "error": "Permission denied: only staff may mark delivery."}
    
        parcel = self.parcels.get(tracking_number)
        if not parcel:
            return {"success": False, "error": "Parcel not found."}
    
        if parcel.get("current_status") == "Delivered" or parcel.get("delivery_date"):
            return {"success": False, "error": "Parcel already marked as delivered."}

        # Update parcel current status and delivery date
        parcel["current_status"] = "Delivered"
        parcel["delivery_date"] = delivery_date
        self.parcels[tracking_number] = parcel

        # Record in history
        location = parcel.get("current_location", "")
        history_entry = {
            "tracking_number": tracking_number,
            "timestamp": delivery_date,
            "status": "Delivered",
            "location": location,
        }
        if tracking_number not in self.parcel_status_history:
            self.parcel_status_history[tracking_number] = []
        self.parcel_status_history[tracking_number].append(history_entry)

        return {"success": True, "message": "Parcel marked as delivered."}

    def add_new_parcel(
        self,
        tracking_number: str,
        sender_id: str,
        recipient_id: str,
        current_status: str,
        current_location: str,
        delivery_estimate: str,
        shipment_date: str,
        delivery_date: str
    ) -> dict:
        """
        Add a new parcel to the system.

        Args:
            tracking_number (str): Unique parcel tracking number.
            sender_id (str): User ID of the sender. Must exist.
            recipient_id (str): User ID of the recipient. Must exist.
            current_status (str): Initial status for the parcel.
            current_location (str): Initial location for the parcel.
            delivery_estimate (str): Estimated delivery date (string).
            shipment_date (str): Shipment date (string).
            delivery_date (str): Initial delivery date (string, may be empty if not delivered).

        Returns:
            dict: {
                "success": True,
                "message": "Parcel {tracking_number} added successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Each tracking number must be unique.
            - Sender and recipient must exist as valid user IDs.
        """
        # Check uniqueness of tracking number
        if tracking_number in self.parcels:
            return {"success": False, "error": "Tracking number already exists."}

        # Check sender and recipient exist
        if sender_id not in self.users or recipient_id not in self.users:
            return {"success": False, "error": "Sender or recipient does not exist."}

        # Construct parcel info
        parcel_info = {
            "tracking_number": tracking_number,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "current_status": current_status,
            "current_location": current_location,
            "delivery_estimate": delivery_estimate,
            "shipment_date": shipment_date,
            "delivery_date": delivery_date,
        }

        self.parcels[tracking_number] = parcel_info

        # Optionally initialize empty status history for the parcel
        if tracking_number not in self.parcel_status_history:
            self.parcel_status_history[tracking_number] = []

        return {
            "success": True,
            "message": f"Parcel {tracking_number} added successfully."
        }

    def add_new_user(self, user_id: str, name: str, address: str, contact_info: str) -> dict:
        """
        Register a new user in the tracking system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): Name of the user.
            address (str): Address of the user.
            contact_info (str): Contact information for the user.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> added successfully"
            }
            or
            {
                "success": False,
                "error": "User ID already exists"
            }

        Constraints:
            - user_id must be unique system-wide.
        """
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists" }

        self.users[user_id] = {
            "user_id": user_id,
            "name": name,
            "address": address,
            "contact_info": contact_info
        }

        return { "success": True, "message": f"User {user_id} added successfully" }

    def append_parcel_status_history(
        self,
        tracking_number: str,
        timestamp: str,
        status: str,
        location: str
    ) -> dict:
        """
        Add a new status/location/timestamp entry to a parcel's history,
        ensuring it is strictly chronological.

        Args:
            tracking_number (str): The parcel to update.
            timestamp (str): The timestamp of this update (should be ISO 8601 string).
            status (str): The new status for the parcel.
            location (str): The new location for the parcel.

        Returns:
            dict: {
                "success": True,
                "message": "Status history appended."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Parcel must exist.
            - Status updates must be in strict chronological order by timestamp.
        """
        # Check parcel existence
        if tracking_number not in self.parcels:
            return { "success": False, "error": "Parcel does not exist." }

        history = self.parcel_status_history.setdefault(tracking_number, [])
        if history:
            last_timestamp = history[-1]["timestamp"]
            if timestamp <= last_timestamp:
                return {
                    "success": False,
                    "error": (
                        "Timestamps must be strictly increasing. "
                        f"Last timestamp: {last_timestamp}, provided: {timestamp}"
                    )
                }

        new_entry = {
            "tracking_number": tracking_number,
            "timestamp": timestamp,
            "status": status,
            "location": location
        }
        history.append(new_entry)
        return { "success": True, "message": "Status history appended." }

    def delete_parcel(self, tracking_number: str, requester_role: str) -> dict:
        """
        Remove a parcel record entirely from the system (admin/staff only; rarely used, with integrity checks).

        Args:
            tracking_number (str): The unique identifier for the parcel.
            requester_role (str): The role of the requester (must be 'admin' or 'staff').

        Returns:
            dict: {
                "success": True,
                "message": "Parcel <tracking_number> deleted successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }
    
        Constraints:
            - Only admin or staff are allowed to delete parcel records.
            - The tracking number must exist in the system.
            - Both the parcel record and its status history should be removed.
        """
        # Permission check
        if requester_role.lower() not in ["admin", "staff"]:
            return {"success": False, "error": "Permission denied: only admin or staff can delete parcels."}

        # Existence check
        if tracking_number not in self.parcels:
            return {"success": False, "error": f"Parcel with tracking_number '{tracking_number}' does not exist."}

        # Remove parcel record
        del self.parcels[tracking_number]

        # Remove status history if it exists
        if tracking_number in self.parcel_status_history:
            del self.parcel_status_history[tracking_number]

        return {
            "success": True,
            "message": f"Parcel {tracking_number} deleted successfully."
        }


class ParcelTrackingSystem(BaseEnv):
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

    def get_parcel_by_tracking_number(self, **kwargs):
        return self._call_inner_tool('get_parcel_by_tracking_number', kwargs)

    def get_parcel_delivery_estimate(self, **kwargs):
        return self._call_inner_tool('get_parcel_delivery_estimate', kwargs)

    def get_parcel_actual_delivery_date(self, **kwargs):
        return self._call_inner_tool('get_parcel_actual_delivery_date', kwargs)

    def get_parcel_current_status(self, **kwargs):
        return self._call_inner_tool('get_parcel_current_status', kwargs)

    def get_parcel_status_history(self, **kwargs):
        return self._call_inner_tool('get_parcel_status_history', kwargs)

    def list_parcels_by_user(self, **kwargs):
        return self._call_inner_tool('list_parcels_by_user', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def find_parcels_by_status(self, **kwargs):
        return self._call_inner_tool('find_parcels_by_status', kwargs)

    def update_parcel_status(self, **kwargs):
        return self._call_inner_tool('update_parcel_status', kwargs)

    def update_parcel_location(self, **kwargs):
        return self._call_inner_tool('update_parcel_location', kwargs)

    def set_parcel_delivery_estimate(self, **kwargs):
        return self._call_inner_tool('set_parcel_delivery_estimate', kwargs)

    def record_parcel_delivery(self, **kwargs):
        return self._call_inner_tool('record_parcel_delivery', kwargs)

    def add_new_parcel(self, **kwargs):
        return self._call_inner_tool('add_new_parcel', kwargs)

    def add_new_user(self, **kwargs):
        return self._call_inner_tool('add_new_user', kwargs)

    def append_parcel_status_history(self, **kwargs):
        return self._call_inner_tool('append_parcel_status_history', kwargs)

    def delete_parcel(self, **kwargs):
        return self._call_inner_tool('delete_parcel', kwargs)
