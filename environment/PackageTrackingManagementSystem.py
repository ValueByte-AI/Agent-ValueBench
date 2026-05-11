# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ShipmentInfo(TypedDict):
    shipment_id: str
    carrier_name: str
    tracking_number: str
    current_status: str
    current_location: str
    destination_address: str
    sender_info: str
    recipient_info: str

class StatusHistoryInfo(TypedDict):
    shipment_id: str
    status_timestamp: str
    status_detail: str
    location: str
    language: str

class CarrierInfo(TypedDict):
    carrier_name: str
    contact_details: str
    tracking_endpoint: str

class UserInfo(TypedDict):
    _id: str
    language_preference: str
    contact_info: str
    managed_shipments: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for the package tracking management system.
        """

        # Shipments: {shipment_id: ShipmentInfo}
        self.shipments: Dict[str, ShipmentInfo] = {}

        # StatusHistory: {shipment_id: List[StatusHistoryInfo]}
        self.status_histories: Dict[str, List[StatusHistoryInfo]] = {}

        # Carriers: {carrier_name: CarrierInfo}
        self.carriers: Dict[str, CarrierInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each shipment must have a valid tracking number and associated carrier.
        # - Status updates must be associated with both a timestamp and a location.
        # - Multilingual support requires that status updates can be presented in the user’s preferred language.
        # - Only authorized users can view or request status updates on their managed shipments.
        # - Shipment status must accurately reflect the most recent carrier-provided status.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user profile and preferences by user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user_id must exist in the users dictionary.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_language_preference(self, user_id: str) -> dict:
        """
        Get the preferred language of the user for formatting multilingual updates.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                - On success: { "success": True, "data": <language_preference:str> }
                - On failure: { "success": False, "error": "<reason>" }
        Constraints:
            - The user with the given ID must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        # Handle the unlikely case that language_preference is missing
        lang = user.get("language_preference")
        if lang is None:
            return { "success": False, "error": "Language preference not set for user" }
        return { "success": True, "data": lang }

    def get_user_managed_shipments(self, user_id: str) -> dict:
        """
        List all shipment IDs managed/monitored by a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[str]  # shipment IDs managed by the user (can be empty)
                }
                On failure: {
                    "success": False,
                    "error": str  # description of the error (e.g., user not found)
                }

        Constraints:
            - Only existing users are supported; if the user does not exist, return an error.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        managed_shipments = user.get("managed_shipments", [])
        return { "success": True, "data": managed_shipments }

    def is_user_authorized_for_shipment(self, user_id: str, shipment_id: str) -> dict:
        """
        Check whether a user is authorized to view or update the given shipment.

        Args:
            user_id (str): The unique identifier for the user.
            shipment_id (str): The unique shipment ID.

        Returns:
            dict: {
                "success": True,
                "authorized": True/False  # Indicates if the user is authorized for this shipment
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (user or shipment not found)
            }

        Constraints:
            - Only users whose managed_shipments include shipment_id are authorized.
            - If the user or shipment does not exist, operation fails.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment not found"}

        authorized = shipment_id in user.get("managed_shipments", [])
        return { "success": True, "authorized": authorized }

    def get_shipment_by_id(self, shipment_id: str) -> dict:
        """
        Retrieve details of a shipment by its shipment_id.

        Args:
            shipment_id (str): The unique identifier of the shipment.

        Returns:
            dict: {
                "success": True,
                "data": ShipmentInfo  # Dictionary with all shipment details
            }
            or
            {
                "success": False,
                "error": "Shipment not found"
            }

        Constraints:
            - The given shipment_id must exist in the system.
            - No user authorization enforced in this operation.
        """
        if shipment_id not in self.shipments:
            return { "success": False, "error": "Shipment not found" }

        return { "success": True, "data": self.shipments[shipment_id] }

    def get_shipment_by_tracking_number_and_carrier(self, carrier_name: str, tracking_number: str) -> dict:
        """
        Retrieve shipment details by matching both the given carrier_name and tracking_number.

        Args:
            carrier_name (str): The shipping carrier to query.
            tracking_number (str): The shipment's tracking number.
    
        Returns:
            dict:
                On success: { "success": True, "data": ShipmentInfo }
                On failure: { "success": False, "error": str }
    
        Constraints:
            - Returns the first (and should be only) shipment matching both carrier and tracking number.
            - Does not perform authorization checks.
        """
        for shipment in self.shipments.values():
            if shipment["carrier_name"] == carrier_name and shipment["tracking_number"] == tracking_number:
                return {"success": True, "data": shipment}

        return {
            "success": False,
            "error": "No shipment found with the given carrier and tracking number."
        }

    def get_shipments_by_ids(self, shipment_ids: list) -> dict:
        """
        Retrieve details (ShipmentInfo) for multiple shipment IDs (batch query).

        Args:
            shipment_ids (list of str): List of shipment_id strings to query.

        Returns:
            dict: {
                "success": True,
                "data": List[ShipmentInfo],  # List of found shipment info entries
                "not_found": List[str],      # List of shipment_ids that do not exist (optional, for transparency)
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - If shipment_ids is not a list or is empty, returns an error.
            - Shipments not found are reported in 'not_found' key.
        """
        if not isinstance(shipment_ids, list) or len(shipment_ids) == 0:
            return {"success": False, "error": "shipment_ids must be a non-empty list."}

        found_shipments = []
        not_found = []

        for sid in shipment_ids:
            if sid in self.shipments:
                found_shipments.append(self.shipments[sid])
            else:
                not_found.append(sid)

        return {
            "success": True,
            "data": found_shipments,
            "not_found": not_found
        }

    def get_current_shipment_status(self, shipment_id: str) -> dict:
        """
        Retrieve the current status, location, destination, and other relevant details for a shipment.

        Args:
            shipment_id (str): The unique identifier for the shipment.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ShipmentInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Shipment not found"
                    }

        Constraints:
            - The shipment with the given ID must exist in the system.
        """
        shipment_info = self.shipments.get(shipment_id)
        if not shipment_info:
            return { "success": False, "error": "Shipment not found" }
        return { "success": True, "data": shipment_info }

    def get_status_history_for_shipment(
        self,
        shipment_id: str,
        language: str = None,
        limit: int = None
    ) -> dict:
        """
        Retrieve status updates for a shipment, optionally filtered by language and limited to the most recent entries.

        Args:
            shipment_id (str): The ID of the shipment whose status history to retrieve.
            language (str, optional): If specified, only status updates in this language are returned.
            limit (int, optional): If specified, return only up to 'limit' most recent status updates.

        Returns:
            dict: {
                "success": True,
                "data": List[StatusHistoryInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Shipment must exist in the system.
            - If 'language' is specified, only include updates matching that language.
            - If 'limit' is specified, return at most the N most recent updates (by status_timestamp).
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment does not exist"}

        status_list = self.status_histories.get(shipment_id, [])

        # Apply language filter if specified
        if language:
            status_list = [
                status for status in status_list
                if status.get("language") == language
            ]

        # Sort by status_timestamp descending (most recent first)
        status_list_sorted = sorted(
            status_list,
            key=lambda x: x.get("status_timestamp", ""),
            reverse=True
        )

        # Apply limit if specified
        if limit is not None:
            status_list_sorted = status_list_sorted[:limit]

        return {"success": True, "data": status_list_sorted}

    def get_latest_status_update_in_language(self, shipment_id: str, language: str) -> dict:
        """
        Retrieve the most recent status entry (StatusHistoryInfo) for a shipment in the specified language.

        Args:
            shipment_id (str): Unique identifier for the shipment.
            language (str): Language code (e.g., 'en', 'fr') in which to retrieve the status detail.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": StatusHistoryInfo  # The latest status entry in the given language.
                }
                OR
                {
                    "success": False,
                    "error": str  # Error description.
                }

        Constraints:
            - shipment_id must exist.
            - There must be at least one status entry in the specified language.
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment does not exist."}

        if shipment_id not in self.status_histories or not self.status_histories[shipment_id]:
            return {"success": False, "error": "No status history for this shipment."}
    
        status_list = [
            status for status in self.status_histories[shipment_id]
            if status["language"] == language
        ]

        if not status_list:
            return {"success": False, "error": "No status updates found in the specified language."}

        # Assume status_timestamp is ISO8601 and sortable lexicographically
        latest_status = max(status_list, key=lambda s: s["status_timestamp"])
        return {"success": True, "data": latest_status}

    def get_carrier_info(self, carrier_name: str) -> dict:
        """
        Retrieve contact details and tracking endpoint information for the specified carrier.

        Args:
            carrier_name (str): The name of the carrier.

        Returns:
            dict: {
                "success": True,
                "data": CarrierInfo  # CarrierInfo dictionary if found
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Carrier not found"
            }

        Constraints:
            - The carrier must exist in the system.
        """
        if carrier_name not in self.carriers:
            return { "success": False, "error": "Carrier not found" }
        return { "success": True, "data": self.carriers[carrier_name] }

    def add_status_update(
        self,
        shipment_id: str,
        status_detail: str,
        status_timestamp: str,
        location: str,
        language: str = "en"
    ) -> dict:
        """
        Append a new status update to a shipment's history.

        Args:
            shipment_id (str): ID of the shipment to update.
            status_detail (str): Status description.
            status_timestamp (str): Timestamp of the update (ISO8601 or similar).
            location (str): Where the status update occurred.
            language (str, optional): Language code for the status text (default "en").

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Status update added to shipment <shipment_id>"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Shipment must exist.
            - Status update must include timestamp and location.
            - System must keep status_histories[shipment_id] updated.
            - Shipment's current_status and current_location must reflect the most recent status update for the shipment.
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment does not exist"}
        if not status_timestamp or not location:
            return {"success": False, "error": "Status update must include timestamp and location"}
        if not status_detail:
            return {"success": False, "error": "Status detail must not be empty"}
        if not language:
            language = "en"

        status_update: StatusHistoryInfo = {
            "shipment_id": shipment_id,
            "status_timestamp": status_timestamp,
            "status_detail": status_detail,
            "location": location,
            "language": language
        }
        if shipment_id not in self.status_histories:
            self.status_histories[shipment_id] = []
        self.status_histories[shipment_id].append(status_update)

        # Constraint: Shipment's current_status and current_location must reflect the most recent status update
        # We assume the 'most recent' is the one with the latest status_timestamp
        history = self.status_histories[shipment_id]
        latest = max(history, key=lambda x: x["status_timestamp"])
        self.shipments[shipment_id]["current_status"] = latest["status_detail"]
        self.shipments[shipment_id]["current_location"] = latest["location"]

        return {
            "success": True,
            "message": f"Status update added to shipment {shipment_id}"
        }

    def update_shipment_current_status(self, shipment_id: str) -> dict:
        """
        Update a shipment's current_status and current_location according to the latest status history entry.

        Args:
            shipment_id (str): The ID of the shipment to update.

        Returns:
            dict:
                - On success: { "success": True, "message": "Shipment status updated to the latest status history." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Shipment must exist.
            - Shipment must have at least one status history entry.
            - The latest status history is determined by the highest status_timestamp (lexicographical comparison if ISO8601).
            - Updates the current_status and current_location to match the latest status history entry.
        """
        # Check that the shipment exists
        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment not found."}

        # Check for status history presence
        history_list = self.status_histories.get(shipment_id, [])
        if not history_list:
            return {"success": False, "error": "No status history available for shipment."}

        # Find the latest status history entry by status_timestamp
        try:
            # Assuming status_timestamp is in ISO8601 format so lexicographical comparison works
            latest_entry = max(history_list, key=lambda x: x["status_timestamp"])
        except Exception:
            return {"success": False, "error": "Malformed status history data."}

        # Perform the update
        self.shipments[shipment_id]["current_status"] = latest_entry["status_detail"]
        self.shipments[shipment_id]["current_location"] = latest_entry["location"]

        return {"success": True, "message": "Shipment status updated to the latest status history."}

    def associate_shipment_with_user(self, user_id: str, shipment_id: str) -> dict:
        """
        Add an existing shipment to a user's managed shipments list.

        Args:
            user_id (str): The ID of the user.
            shipment_id (str): The ID of the shipment to associate.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Shipment <shipment_id> associated with user <user_id>."
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Both user and shipment must exist.
            - If shipment already present in user's managed shipments, operation is idempotent and returns success.
            - Only modifies user's managed_shipments, not shipment data itself.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        if shipment_id not in self.shipments:
            return { "success": False, "error": "Shipment does not exist" }

        if shipment_id in user["managed_shipments"]:
            return {
                "success": True,
                "message": f"Shipment {shipment_id} is already associated with user {user_id}."
            }

        user["managed_shipments"].append(shipment_id)
        return {
            "success": True,
            "message": f"Shipment {shipment_id} associated with user {user_id}."
        }

    def create_new_shipment(
        self,
        shipment_id: str,
        carrier_name: str,
        tracking_number: str,
        current_status: str,
        current_location: str,
        destination_address: str,
        sender_info: str,
        recipient_info: str,
        status_detail: str,
        status_timestamp: str,
        status_location: str,
        language: str,
    ) -> dict:
        """
        Register a new shipment with valid tracking number, carrier, and initial status.

        Args:
            shipment_id (str): Unique identifier for the shipment.
            carrier_name (str): Name of the shipping carrier.
            tracking_number (str): Tracking number for the shipment.
            current_status (str): The current status for the shipment (initial status).
            current_location (str): Current location of the shipment.
            destination_address (str): Final destination address.
            sender_info (str): Information about the sender.
            recipient_info (str): Information about the recipient.
            status_detail (str): Status description for the status history.
            status_timestamp (str): Timestamp of the initial status update.
            status_location (str): Location for the initial status update.
            language (str): Language code for the status update.

        Returns:
            dict: Success or failure result with appropriate message.

        Constraints:
            - Shipment ID must be unique.
            - Carrier must exist.
            - Tracking number must be provided.
            - Status history requires timestamp and location (non-empty).
            - All fields must be provided (non-empty).
        """
        # Field validation
        required_fields = [
            ("shipment_id", shipment_id),
            ("carrier_name", carrier_name),
            ("tracking_number", tracking_number),
            ("current_status", current_status),
            ("current_location", current_location),
            ("destination_address", destination_address),
            ("sender_info", sender_info),
            ("recipient_info", recipient_info),
            ("status_detail", status_detail),
            ("status_timestamp", status_timestamp),
            ("status_location", status_location),
            ("language", language),
        ]
        for field, value in required_fields:
            if not value or str(value).strip() == "":
                return {"success": False, "error": f"Field '{field}' must be provided and non-empty."}

        if shipment_id in self.shipments:
            return {"success": False, "error": "Shipment ID already exists."}
        if carrier_name not in self.carriers:
            return {"success": False, "error": f"Carrier '{carrier_name}' does not exist."}

        # Register the shipment
        shipment_info: ShipmentInfo = {
            "shipment_id": shipment_id,
            "carrier_name": carrier_name,
            "tracking_number": tracking_number,
            "current_status": current_status,
            "current_location": current_location,
            "destination_address": destination_address,
            "sender_info": sender_info,
            "recipient_info": recipient_info,
        }
        self.shipments[shipment_id] = shipment_info

        # Add the initial status history entry
        status_history_entry: StatusHistoryInfo = {
            "shipment_id": shipment_id,
            "status_timestamp": status_timestamp,
            "status_detail": status_detail,
            "location": status_location,
            "language": language,
        }
        self.status_histories[shipment_id] = [status_history_entry]

        return {"success": True, "message": f"Shipment {shipment_id} created successfully."}

    def bulk_add_status_updates(self, status_updates: list) -> dict:
        """
        Insert status updates for multiple shipments at once.

        Args:
            status_updates (List[dict]): Each dict must include:
                - shipment_id (str)
                - status_timestamp (str)
                - status_detail (str)
                - location (str)
                - language (str)

        Returns:
            dict: {
                "success": True,
                "message": "<count> status updates added. <count> failed.",
                "errors": List[str]  # optional, if any failed
            }

        Constraints:
            - Each status update must include all required fields.
            - shipment_id must exist in the system.
            - Skips invalid updates, returns per-update error messages.
            - Does not abort the entire batch due to partial errors.
        """
        required_fields = {"shipment_id", "status_timestamp", "status_detail", "location", "language"}
        added = 0
        errors = []

        for idx, upd in enumerate(status_updates):
            # Check required fields
            missing = [field for field in required_fields if field not in upd]
            if missing:
                errors.append(f"Update #{idx+1}: missing fields {missing}")
                continue
            shipment_id = upd["shipment_id"]
            if shipment_id not in self.shipments:
                errors.append(f"Update #{idx+1}: shipment_id '{shipment_id}' does not exist")
                continue
        
            # Add status update
            status_entry = {
                "shipment_id": shipment_id,
                "status_timestamp": upd["status_timestamp"],
                "status_detail": upd["status_detail"],
                "location": upd["location"],
                "language": upd["language"]
            }
            if shipment_id not in self.status_histories:
                self.status_histories[shipment_id] = []
            self.status_histories[shipment_id].append(status_entry)
            latest = max(self.status_histories[shipment_id], key=lambda x: x["status_timestamp"])
            self.shipments[shipment_id]["current_status"] = latest["status_detail"]
            self.shipments[shipment_id]["current_location"] = latest["location"]
            added += 1

        result = {"success": True,
                  "message": f"{added} status updates added. {len(errors)} failed."}
        if errors:
            result["errors"] = errors
        return result

    def import_shipments_for_user(self, user_id: str, shipment_ids: list) -> dict:
        """
        Bulk-associate a set of existing shipments with a user's managed shipments list.

        Args:
            user_id (str): The ID of the user who will manage/monitor the shipments.
            shipment_ids (List[str]): List of shipment IDs to be associated.

        Returns:
            dict: {
                "success": True,
                "message": "Shipments successfully associated with user"
            }
            or
            {
                "success": False,
                "error": <error string>
            }

        Constraints:
            - The user must exist.
            - All provided shipment_ids must correspond to existing shipments.
            - No duplicate associations should occur—association is idempotent.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": f"User with id '{user_id}' does not exist."}

        missing_shipments = [sid for sid in shipment_ids if sid not in self.shipments]
        if missing_shipments:
            return {
                "success": False,
                "error": f"The following shipment(s) do not exist: {', '.join(missing_shipments)}"
            }

        user_info = self.users[user_id]
        managed = set(user_info.get("managed_shipments", []))
        added = 0
        for sid in shipment_ids:
            if sid not in managed:
                managed.add(sid)
                added += 1

        # Update user's managed_shipments with no duplicates
        user_info["managed_shipments"] = list(managed)
        self.users[user_id] = user_info

        return {
            "success": True,
            "message": (
                f"{added} shipment(s) successfully associated with user '{user_id}'."
                if added > 0 else
                "All specified shipments were already associated with this user."
            )
        }


class PackageTrackingManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_language_preference(self, **kwargs):
        return self._call_inner_tool('get_user_language_preference', kwargs)

    def get_user_managed_shipments(self, **kwargs):
        return self._call_inner_tool('get_user_managed_shipments', kwargs)

    def is_user_authorized_for_shipment(self, **kwargs):
        return self._call_inner_tool('is_user_authorized_for_shipment', kwargs)

    def get_shipment_by_id(self, **kwargs):
        return self._call_inner_tool('get_shipment_by_id', kwargs)

    def get_shipment_by_tracking_number_and_carrier(self, **kwargs):
        return self._call_inner_tool('get_shipment_by_tracking_number_and_carrier', kwargs)

    def get_shipments_by_ids(self, **kwargs):
        return self._call_inner_tool('get_shipments_by_ids', kwargs)

    def get_current_shipment_status(self, **kwargs):
        return self._call_inner_tool('get_current_shipment_status', kwargs)

    def get_status_history_for_shipment(self, **kwargs):
        return self._call_inner_tool('get_status_history_for_shipment', kwargs)

    def get_latest_status_update_in_language(self, **kwargs):
        return self._call_inner_tool('get_latest_status_update_in_language', kwargs)

    def get_carrier_info(self, **kwargs):
        return self._call_inner_tool('get_carrier_info', kwargs)

    def add_status_update(self, **kwargs):
        return self._call_inner_tool('add_status_update', kwargs)

    def update_shipment_current_status(self, **kwargs):
        return self._call_inner_tool('update_shipment_current_status', kwargs)

    def associate_shipment_with_user(self, **kwargs):
        return self._call_inner_tool('associate_shipment_with_user', kwargs)

    def create_new_shipment(self, **kwargs):
        return self._call_inner_tool('create_new_shipment', kwargs)

    def bulk_add_status_updates(self, **kwargs):
        return self._call_inner_tool('bulk_add_status_updates', kwargs)

    def import_shipments_for_user(self, **kwargs):
        return self._call_inner_tool('import_shipments_for_user', kwargs)
