# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime, timezone



# Package/Shipment entity
class PackageInfo(TypedDict):
    tracking_number: str
    status: str
    sender_id: str
    recipient_id: str
    shipping_address: str
    destination_address: str
    current_location: str

# TrackingEvent entity
class TrackingEventInfo(TypedDict):
    event_id: str
    tracking_number: str
    event_type: str
    event_time: str
    location: str

# User entity
class UserInfo(TypedDict):
    _id: str
    name: str
    contact_info: str
    role: str  # 'sender' or 'recipient'

class _GeneratedEnvImpl:
    def __init__(self):
        # Packages/Shipments mapping: {tracking_number: PackageInfo}
        self.packages: Dict[str, PackageInfo] = {}

        # Tracking events per package: {tracking_number: List[TrackingEventInfo]}
        self.tracking_events: Dict[str, List[TrackingEventInfo]] = {}

        # Users mapping: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # --- Constraints ---
        # - Each package/shipment must have a unique tracking number.
        # - Tracking events for a package must be stored in chronological order.
        # - Package status must reflect the most recent tracking event (e.g., "In Transit", "Delivered").
        # - Only authorized users can access or modify the tracking information.

    @staticmethod
    def _is_internal_user(user: dict) -> bool:
        role = str(user.get("role", "")).lower()
        return role not in ("sender", "recipient")

    @staticmethod
    def _event_sort_key(event_time: str):
        if isinstance(event_time, str):
            normalized = event_time[:-1] + "+00:00" if event_time.endswith("Z") else event_time
            try:
                parsed = datetime.fromisoformat(normalized)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return (1, parsed)
            except Exception:
                pass
            clock_text = event_time
            if clock_text.startswith("00:") and clock_text.endswith(" AM"):
                clock_text = "12:" + clock_text[3:]
            try:
                return (0, datetime.strptime(clock_text, "%I:%M %p"))
            except Exception:
                pass
        return (2, str(event_time))

    @staticmethod
    def _normalize_status_after_event(current_status: str, event_type: str) -> str:
        if event_type == "Exception" and current_status == "Exception - Critical":
            return current_status
        return event_type


    def get_package_by_tracking_number(self, tracking_number: str, requesting_user_id: str) -> dict:
        """
        Retrieve full package information (status, participants, locations) for a given tracking number.

        Args:
            tracking_number (str): Unique tracking number identifying the package.
            requesting_user_id (str): The user requesting the information. Must be sender or recipient.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": PackageInfo}
                - On error (package not found):
                    {"success": False, "error": "Tracking number not found"}
                - On error (not authorized):
                    {"success": False, "error": "Not authorized to access this package"}

        Constraints:
            - The tracking number must exist.
            - Only sender or recipient (authorized users) can access info for privacy/security reasons.
        """
        # Find package
        package = self.packages.get(tracking_number)
        if not package:
            return {"success": False, "error": "Tracking number not found"}

        requesting_user = self.users.get(requesting_user_id)
        if not requesting_user:
            return {"success": False, "error": "Requesting user not found"}

        # Authorization: sender, recipient, or internal operational user
        if (
            requesting_user_id not in (package["sender_id"], package["recipient_id"])
            and not self._is_internal_user(requesting_user)
        ):
            return {"success": False, "error": "Not authorized to access this package"}

        # If authorized, return full info
        return {"success": True, "data": package}

    def get_current_status(self, tracking_number: str, user_id: str) -> dict:
        """
        Obtain the current status (e.g., "In Transit," "Delivered") for a given package.

        Args:
            tracking_number (str): Unique identifier for the package.
            user_id (str): User ID requesting the status (must be sender or recipient).

        Returns:
            dict: {
                "success": True,
                "data": str  # current status string,
            }
            or
            {
                "success": False,
                "error": str  # error description
            }

        Constraints:
        - Only sender or recipient of the package may access status info (authorization).
        - Returns error if package or user does not exist, or access is not permitted.
        """
        # Check package exists
        package = self.packages.get(tracking_number)
        if not package:
            return { "success": False, "error": "Package with tracking number not found" }
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        # Authorization: Only sender or recipient can access
        if user_id != package["sender_id"] and user_id != package["recipient_id"]:
            return { "success": False, "error": "User not authorized to access this package's status" }
        # Return current status
        return { "success": True, "data": package["status"] }

    def get_current_location(self, tracking_number: str, user_id: str) -> dict:
        """
        Obtain the current known location of a package by tracking number.

        Args:
            tracking_number (str): Unique ID for the shipment/package.
            user_id (str): ID of the user requesting the information.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": str  # The current location
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - The package must exist.
            - The user must be authorized to access this package's information
              (e.g., sender, recipient, or verified authorized user).
        """
        package = self.packages.get(tracking_number)
        if not package:
            return {"success": False, "error": "Package not found"}

        # Authorization check (assuming the system provides 'verify_user_authorization')
        if hasattr(self, "verify_user_authorization"):
            auth_check = self.verify_user_authorization(user_id, tracking_number)
            if not (isinstance(auth_check, dict) and auth_check.get("success") and auth_check.get("authorized") is True):
                return {"success": False, "error": "User not authorized to access tracking information"}

        return {"success": True, "data": package["current_location"]}

    def get_tracking_history(self, tracking_number: str) -> dict:
        """
        Retrieve the complete chronological list of tracking events for a package.

        Args:
            tracking_number (str): The unique package tracking number.

        Returns:
            dict:
                success: True, and data: List[TrackingEventInfo] (may be empty if no events)
                OR
                success: False, and error: Reason string (e.g., package does not exist)

        Constraints:
            - The tracking number must refer to an existing package.
            - Tracking events are returned in chronological order.
        """
        if tracking_number not in self.packages:
            return {"success": False, "error": "Package with tracking number does not exist."}

        # Events may be empty, but always present as a list if package exists
        history = self.tracking_events.get(tracking_number, [])
        return {"success": True, "data": history}

    def list_packages_by_user(self, user_id: str) -> dict:
        """
        List all packages (shipments) where the user is either the sender or recipient.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict:
                - On success: {"success": True, "data": List[PackageInfo]}
                  (list may be empty if user is not a sender or recipient on any package)
                - On failure: {"success": False, "error": str}
                  (e.g., "User does not exist")
        Constraints:
            - Only an existing user may use this operation.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_packages = [
            package for package in self.packages.values()
            if package["sender_id"] == user_id or package["recipient_id"] == user_id
        ]

        return {"success": True, "data": user_packages}

    def get_user_info_by_id(self, user_id: str) -> dict:
        """
        Fetch full user profile/details by user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Full profile/details of the user
            }
            or
            {
                "success": False,
                "error": "User ID not found"
            }

        Constraints:
            - The user must exist in the system for the provided user_id.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User ID not found"}
        return {"success": True, "data": user_info}

    def verify_user_authorization(self, user_id: str, tracking_number: str) -> dict:
        """
        Check if the specified user is authorized to view or modify information about the specified package.
    
        Args:
            user_id (str): The user's unique identifier.
            tracking_number (str): The package's tracking number.
    
        Returns:
            dict:
                If authorized:
                    {'success': True, 'authorized': True}
                If not authorized:
                    {'success': True, 'authorized': False}
                If error (user or package not found):
                    {'success': False, 'error': str}
    
        Constraints:
            - Only sender or recipient of the package are authorized.
            - User and package must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
        if tracking_number not in self.packages:
            return {"success": False, "error": "Package not found"}
        pkg = self.packages[tracking_number]
        user = self.users[user_id]
        if user_id == pkg["sender_id"] or user_id == pkg["recipient_id"] or self._is_internal_user(user):
            return {"success": True, "authorized": True}
        else:
            return {"success": True, "authorized": False}

    def add_tracking_event(
        self,
        tracking_number: str,
        event_id: str,
        event_type: str,
        event_time: str,
        location: str,
        user_id: str
    ) -> dict:
        """
        Add a new event to a package's tracking history and update the package's status/location.

        Args:
            tracking_number (str): The unique tracking number of the package.
            event_id (str): Unique identifier for the tracking event.
            event_type (str): Type of the event (e.g., 'Picked Up', 'In Transit', 'Delivered').
            event_time (str): Timestamp of the event (ISO string or similar format).
            location (str): Location where the event occurred.
            user_id (str): ID of the user attempting to perform this operation.

        Returns:
            dict: {
                "success": True,
                "message": "Tracking event added and package updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The tracking_number must exist.
            - Only authorized users (sender, recipient, or privileged) may add events.
            - Historical correction events may be inserted and the event chain remains stored in chronological order.
            - Package status/location are updated if the new event becomes the latest operational event.
        """
        # Check package exists
        if tracking_number not in self.packages:
            return {"success": False, "error": "Tracking number does not exist"}

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        package = self.packages[tracking_number]
        # Authorization: allow sender, recipient, or any user with role not limited to 'sender'/'recipient'
        if (
            user["_id"] != package["sender_id"]
            and user["_id"] != package["recipient_id"]
            and user.get("role") in ("sender", "recipient")
        ):
            return {"success": False, "error": "User not authorized to modify this package"}

        # Prepare tracking event
        new_event = {
            "event_id": event_id,
            "tracking_number": tracking_number,
            "event_type": event_type,
            "event_time": event_time,
            "location": location,
        }

        tracking_history = list(self.tracking_events.get(tracking_number, []))

        if tracking_history:
            if any(ev["event_id"] == event_id for ev in tracking_history):
                return {"success": False, "error": "Event ID already exists for this package"}

        # Stage the sorted history first so a bad insert does not partially mutate state.
        prior_status = self.packages[tracking_number]["status"]
        candidate_history = tracking_history + [new_event]
        candidate_history.sort(key=lambda ev: self._event_sort_key(ev["event_time"]))
        self.tracking_events[tracking_number] = candidate_history

        # Update package status/location only if this event is now the latest event.
        latest_event = candidate_history[-1]
        if latest_event["event_id"] == event_id:
            self.packages[tracking_number]["status"] = self._normalize_status_after_event(prior_status, event_type)
            self.packages[tracking_number]["current_location"] = location

        return {
            "success": True,
            "message": "Tracking event added and package updated"
        }

    def update_package_status(self, tracking_number: str, new_status: str, requester_id: str) -> dict:
        """
        Manually update a package's status (for exception handling and only by authorized staff).

        Args:
            tracking_number (str): The package's unique tracking number.
            new_status (str): The status to set for the package (e.g., "Exception", "Delayed").
            requester_id (str): The user ID requesting the status update.

        Returns:
            dict: {
                "success": True,
                "message": "Package status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - Package with tracking_number must exist.
            - requester_id must exist and must be an authorized staff user (role NOT 'sender' or 'recipient').
        """

        # Check package existence
        if tracking_number not in self.packages:
            return { "success": False, "error": "Package not found" }

        # Check user existence
        user = self.users.get(requester_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Check user authorization -- assuming roles other than 'sender' and 'recipient' are allowed
        if user.get('role') in ('sender', 'recipient'):
            return { "success": False, "error": "Permission denied: not authorized to update package status" }

        # All checks passed - update status
        self.packages[tracking_number]['status'] = new_status

        return {
            "success": True,
            "message": f"Package status updated to {new_status}."
        }

    def create_package_shipment(
        self,
        tracking_number: str,
        sender_id: str,
        recipient_id: str,
        shipping_address: str,
        destination_address: str
    ) -> dict:
        """
        Register a new package with required shipment details and a unique tracking number.

        Args:
            tracking_number (str): Unique identifier for the shipment.
            sender_id (str): User ID of the sender (must exist and have role 'sender').
            recipient_id (str): User ID of the recipient (must exist and have role 'recipient').
            shipping_address (str): Origin address.
            destination_address (str): Delivery address.

        Returns:
            dict:
                { "success": True, "message": "Package created with tracking number X." }
                OR
                { "success": False, "error": "Reason" }

        Constraints:
            - tracking_number must be globally unique
            - sender_id and recipient_id must reference existing users (with correct roles)
        """
        # Check unique tracking_number
        if tracking_number in self.packages:
            return { "success": False, "error": "Tracking number already exists." }

        # Validate sender
        sender_info = self.users.get(sender_id)
        if not sender_info or sender_info.get("role") != "sender":
            return { "success": False, "error": "Sender ID invalid or not a sender." }

        # Validate recipient
        recipient_info = self.users.get(recipient_id)
        if not recipient_info or recipient_info.get("role") != "recipient":
            return { "success": False, "error": "Recipient ID invalid or not a recipient." }

        # Set initial status and location
        status = "Created"
        current_location = shipping_address

        # Create the package record
        self.packages[tracking_number] = {
            "tracking_number": tracking_number,
            "status": status,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "shipping_address": shipping_address,
            "destination_address": destination_address,
            "current_location": current_location,
        }

        # Initialize empty tracking events list for this package
        self.tracking_events[tracking_number] = []

        return { "success": True, "message": f"Package created with tracking number {tracking_number}." }

    def delete_package(self, tracking_number: str, user_id: str) -> dict:
        """
        Remove a package and all its related tracking events (admin only).

        Args:
            tracking_number (str): The unique tracking number of the package to remove.
            user_id (str): The user ID performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": "Package and all tracking events deleted"
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only users with 'admin' role may perform this action.
            - Both the package and all associated tracking events are deleted.
        """

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Check admin privileges
        if user.get("role") != "admin":
            return { "success": False, "error": "Permission denied: Admin privileges required" }

        # Check package exists
        if tracking_number not in self.packages:
            return { "success": False, "error": "Package not found" }

        # Delete package
        del self.packages[tracking_number]

        # Delete associated tracking events (if present)
        if tracking_number in self.tracking_events:
            del self.tracking_events[tracking_number]

        return { "success": True, "message": "Package and all tracking events deleted" }

    def update_user_info(self, user_id: str, update_data: dict, requester_id: str) -> dict:
        """
        Modify sender or recipient details, subject to privacy/security constraints.

        Args:
            user_id (str): The unique identifier of the user to update.
            update_data (dict): Keys/values to update (only name, contact_info, or role allowed).
            requester_id (str): The user id requesting the update (for authorization).

        Returns:
            dict: {
                "success": True,
                "message": "User info updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only authorized users may update user information.
            - Only updatable fields are allowed (name, contact_info, role).
            - Cannot update user _id.
        """

        if user_id not in self.users:
            return { "success": False, "error": "User to update does not exist." }
        if requester_id not in self.users:
            return { "success": False, "error": "Requester does not exist." }

        # Only allow update of name, contact_info, or role
        allowed_fields = {"name", "contact_info", "role"}
        for key in update_data:
            if key not in allowed_fields:
                return { "success": False, "error": f"Cannot update field '{key}'." }
            if key == "_id":
                return { "success": False, "error": "Cannot update user ID (_id)." }

        requester = self.users[requester_id]
        # Authorization: users may update themselves; internal operational users may update others.
        if requester_id != user_id and not self._is_internal_user(requester):
            return { "success": False, "error": "Unauthorized: only the user or admin can update user info." }

        # Update allowed fields
        for k, v in update_data.items():
            self.users[user_id][k] = v

        return { "success": True, "message": "User info updated." }

    def remove_tracking_event(self, tracking_number: str, event_id: str) -> dict:
        """
        Remove a specific tracking event from a package's event chain. Recalculate package status and
        current location as per the latest remaining event.

        Args:
            tracking_number (str): The tracking number of the package.
            event_id (str): The unique ID of the tracking event to remove.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success description
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Package must exist.
            - Tracking event must exist for the package.
            - After removal, package status and current_location must reflect the new latest event.
            - Tracking events must remain in chronological order.
        """
        # Check package existence
        if tracking_number not in self.packages:
            return {"success": False, "error": "Package does not exist."}
        if tracking_number not in self.tracking_events or not self.tracking_events[tracking_number]:
            return {"success": False, "error": "No tracking events found for this package."}

        # Find event index
        events = self.tracking_events[tracking_number]
        idx_to_remove = next((i for i, ev in enumerate(events) if ev["event_id"] == event_id), None)
        if idx_to_remove is None:
            return {"success": False, "error": "Tracking event not found for this package."}

        prior_status = self.packages[tracking_number]["status"]

        # Remove event
        removed_event = events.pop(idx_to_remove)

        # After removal, ensure chronological order is maintained (it is, since we're just removing)
        # Update package status/current_location to most recent event, or reset if none left
        if events:
            latest_event = events[-1]
            self.packages[tracking_number]["status"] = self._normalize_status_after_event(prior_status, latest_event["event_type"])
            self.packages[tracking_number]["current_location"] = latest_event["location"]
        else:
            self.packages[tracking_number]["status"] = "Unknown"
            self.packages[tracking_number]["current_location"] = ""

        return {
            "success": True,
            "message": "Tracking event removed. Package status updated as needed."
        }


class CourierPackageTrackingSystem(BaseEnv):
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
            if key == "verify_user_authorization" and callable(getattr(env, key, None)):
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

    def get_package_by_tracking_number(self, **kwargs):
        return self._call_inner_tool('get_package_by_tracking_number', kwargs)

    def get_current_status(self, **kwargs):
        return self._call_inner_tool('get_current_status', kwargs)

    def get_current_location(self, **kwargs):
        return self._call_inner_tool('get_current_location', kwargs)

    def get_tracking_history(self, **kwargs):
        return self._call_inner_tool('get_tracking_history', kwargs)

    def list_packages_by_user(self, **kwargs):
        return self._call_inner_tool('list_packages_by_user', kwargs)

    def get_user_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_id', kwargs)

    def verify_user_authorization(self, **kwargs):
        return self._call_inner_tool('verify_user_authorization', kwargs)

    def add_tracking_event(self, **kwargs):
        return self._call_inner_tool('add_tracking_event', kwargs)

    def update_package_status(self, **kwargs):
        return self._call_inner_tool('update_package_status', kwargs)

    def create_package_shipment(self, **kwargs):
        return self._call_inner_tool('create_package_shipment', kwargs)

    def delete_package(self, **kwargs):
        return self._call_inner_tool('delete_package', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def remove_tracking_event(self, **kwargs):
        return self._call_inner_tool('remove_tracking_event', kwargs)
