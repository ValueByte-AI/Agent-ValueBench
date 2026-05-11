# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import uuid



class UserAccountInfo(TypedDict):
    account_id: str
    user_name: str
    tokens: List[str]
    status: str

class BookableItemInfo(TypedDict):
    item_id: str
    item_name: str
    item_type: str
    location: str
    availability_schedule: Dict[str, bool]  # e.g., {"2024-06-15T09:00": True}
    access: List[str]  # List of account_ids allowed to view/book, or other access control mechanism

class ReservationInfo(TypedDict):
    reservation_id: str
    account_id: str
    item_id: str
    reservation_time: str  # ISO time string
    status: str            # e.g., "active", "cancelled", "completed"
    detail: str            # Arbitrary details

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for online booking and reservation management:
        Tracks users, bookable items, and reservations.
        """

        # Users: {account_id: UserAccountInfo}
        self.users: Dict[str, UserAccountInfo] = {}

        # Bookable Items: {item_id: BookableItemInfo}
        self.items: Dict[str, BookableItemInfo] = {}

        # Reservations: {reservation_id: ReservationInfo}
        self.reservations: Dict[str, ReservationInfo] = {}

        # Constraints:
        # - A bookable item can only be reserved if it is available in the specified time slot.
        # - User accounts must be authenticated with valid tokens.
        # - A reservation links one account to one bookable item at a time (per reservation record).
        # - Bookable items may have different visibility or access rules tied to accounts (access).
        # - Reservations may be cancelled or modified only by the owning account and subject to availability rules.

    def get_account_by_token(self, token: str) -> dict:
        """
        Retrieve the user account information associated with the provided authentication token.

        Args:
            token (str): The authentication token.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo  # The matched user account info
            }
            or
            {
                "success": False,
                "error": str  # If the token does not correspond to any user account
            }

        Constraints:
            - The token must exist in at least one user's 'tokens' list.
        """
        for user_info in self.users.values():
            if token in user_info.get("tokens", []):
                return { "success": True, "data": user_info }
        return { "success": False, "error": "Token not associated with any user account" }

    def list_accounts_by_tokens(self, tokens: list) -> dict:
        """
        Given a list of tokens, retrieve details for all corresponding user accounts.

        Args:
            tokens (list of str): List of authentication tokens.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[UserAccountInfo]  # zero or more accounts
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # error reason
                    }
        Constraints:
            - tokens must be a list of strings.
        """

        if not isinstance(tokens, list):
            return {"success": False, "error": "Input must be a list of tokens."}
        if not all(isinstance(tok, str) for tok in tokens):
            return {"success": False, "error": "All tokens must be strings."}

        result = []
        tokens_set = set(tokens)
        for user_info in self.users.values():
            if any(tok in tokens_set for tok in user_info.get("tokens", [])):
                result.append(user_info)

        return {"success": True, "data": result}

    def list_bookable_items_for_account(self, account_id: str) -> dict:
        """
        Retrieve the list of bookable items accessible/visible to the specified account.

        Args:
            account_id (str): The identifier of the user account.

        Returns:
            dict:
                - If success: {"success": True, "data": List[BookableItemInfo]}
                - If error: {"success": False, "error": str}

        Constraints:
            - The account_id must exist in the system.
            - Only return items where the account_id is present in the item's access list.
        """
        if account_id not in self.users:
            return {"success": False, "error": "Account does not exist"}

        result = [
            item_info
            for item_info in self.items.values()
            if account_id in item_info.get("access", [])
        ]

        return {"success": True, "data": result}

    def get_bookable_item_details(self, item_id: str) -> dict:
        """
        Return full metadata/details for a specific bookable item by item_id.

        Args:
            item_id (str): Identifier of the bookable item.

        Returns:
            dict:
                - If item exists:
                    {"success": True, "data": BookableItemInfo}
                - If not found:
                    {"success": False, "error": "Bookable item not found"}

        Constraints:
            - Only retrieves details if the item exists in the system.
        """
        if item_id not in self.items:
            return {"success": False, "error": "Bookable item not found"}

        return {"success": True, "data": self.items[item_id]}

    def check_item_availability_for_time(self, item_id: str, reservation_time: str) -> dict:
        """
        Query whether a specific bookable item is available for a given time slot.

        Args:
            item_id (str): The ID of the bookable item.
            reservation_time (str): ISO-formatted time slot to check (e.g., "2024-06-15T09:00").

        Returns:
            dict: {
                "success": True,
                "data": {
                    "item_id": str,
                    "reservation_time": str,
                    "available": bool
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If the item does not exist, returns an error.
            - If the time slot is not listed in availability_schedule, treat as unavailable.
        """
        item = self.items.get(item_id)
        if not item:
            return { "success": False, "error": "Item not found" }

        available = item["availability_schedule"].get(reservation_time, False)

        return {
            "success": True,
            "data": {
                "item_id": item_id,
                "reservation_time": reservation_time,
                "available": available
            }
        }

    def list_available_items_for_account_and_time(self, account_id: str, reservation_time: str) -> dict:
        """
        For a specific account and time, list all bookable items accessible to the account
        and available at the given time.

        Args:
            account_id (str): The user account's ID making the inquiry.
            reservation_time (str): The ISO timestamp (e.g., "2024-06-15T09:00") to check item availability.

        Returns:
            dict: {
                'success': True,
                'data': List[BookableItemInfo]  # List of items account can access and are available at that time
            }
            OR
            {
                'success': False,
                'error': str  # Reason for failure (e.g. account not found)
            }

        Constraints:
            - account_id must exist
            - Only return items where account_id is in 'access' list and 'availability_schedule'[reservation_time] == True
        """
        # Check if the account exists
        if account_id not in self.users:
            return { "success": False, "error": "Account not found" }

        available_items = []
        for item in self.items.values():
            # Account must have access
            if account_id not in item.get("access", []):
                continue
            # The specified time must be in the availability schedule and available
            if item.get("availability_schedule", {}).get(reservation_time, False):
                available_items.append(item)

        return { "success": True, "data": available_items }

    def get_reservations_for_account(self, account_id: str) -> dict:
        """
        Retrieve all reservations (active, cancelled, etc.) for the given account.

        Args:
            account_id (str): The account id for which to list all reservations.

        Returns:
            dict: 
                { "success": True, "data": List[ReservationInfo] }
                    - list is empty if the account has no reservations
                { "success": False, "error": str }
                    - if the account does not exist

        Constraints:
            - account_id must exist in the system.
        """
        if account_id not in self.users:
            return { "success": False, "error": "Account does not exist" }
    
        reservations = [
            reservation
            for reservation in self.reservations.values()
            if reservation["account_id"] == account_id
        ]
        return { "success": True, "data": reservations }

    def get_reservations_for_item(
        self, 
        item_id: str, 
        status: str = None, 
        reservation_time: str = None
    ) -> dict:
        """
        List all reservations (or filtered) for a specific bookable item.

        Args:
            item_id (str): The ID of the bookable item.
            status (str, optional): Reservation status to filter (e.g. "active", "cancelled", etc.).
            reservation_time (str, optional): Filter for a specific reservation time (ISO string).

        Returns:
            dict: {
                "success": True,
                "data": List[ReservationInfo],  # List of reservations for the item (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g. "Item does not exist")
            }

        Constraints:
            - item_id must refer to a valid BookableItem.
            - If no reservations are found, return an empty list with success.
        """
        if item_id not in self.items:
            return {"success": False, "error": "Item does not exist"}

        reservations = [
            res for res in self.reservations.values()
            if res["item_id"] == item_id
               and (status is None or res["status"] == status)
               and (reservation_time is None or res["reservation_time"] == reservation_time)
        ]
        return {"success": True, "data": reservations}

    def compare_items_across_accounts(self, account_ids: list) -> dict:
        """
        Aggregate and organize accessible bookable item lists from multiple accounts for side-by-side comparison.

        Args:
            account_ids (List[str]): List of account IDs to compare accessible items for.

        Returns:
            dict: {
                "success": True,
                "data": {
                    account_id1: List[BookableItemInfo],
                    account_id2: List[BookableItemInfo],
                    ...
                }
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g. invalid input or no valid accounts
            }

        Constraints:
            - Only items with the account_id in their 'access' list are included for each account.
            - Account_ids not present in the system will have an empty list in the result.
            - If no valid account_ids, an error is returned.
        """
        if not isinstance(account_ids, list) or not account_ids:
            return {"success": False, "error": "No account IDs provided."}

        result = {}
        valid_account_found = False

        for acc_id in account_ids:
            if acc_id in self.users:
                valid_account_found = True
                accessible_items = [
                    item for item in self.items.values()
                    if acc_id in item.get("access", [])
                ]
                result[acc_id] = accessible_items
            else:
                # Could also omit, but better to show intent that account doesn't exist
                result[acc_id] = []

        if not valid_account_found:
            return {"success": False, "error": "No valid account IDs provided."}

        return {"success": True, "data": result}

    def create_reservation(
        self,
        token: str,
        item_id: str,
        reservation_time: str,
        detail: str
    ) -> dict:
        """
        Attempt to create a reservation for a user authenticated by token
        for the specified item at the given time slot, if permitted and available.

        Args:
            token (str): The authentication token of the user.
            item_id (str): ID of the bookable item.
            reservation_time (str): The desired booking time (ISO string).
            detail (str): Details/notes about the reservation.

        Returns:
            dict: {
                "success": True,
                "message": "Reservation created",
                "reservation_id": <new_id>
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must be authenticated (token for active account).
            - Item must exist, be accessible, and be available at reservation_time.
            - The reservation links one account, one bookable item, one slot.
            - The item slot is marked unavailable upon booking.
        """
        # Find authenticated user by token
        account_id = None
        for user in self.users.values():
            if token in user.get('tokens', []):
                if user.get('status', '').lower() == 'active':
                    account_id = user['account_id']
                    break
        if not account_id:
            return { "success": False, "error": "Authentication failed or inactive user" }

        # Check item
        item = self.items.get(item_id)
        if not item:
            return { "success": False, "error": "Item does not exist" }
        if account_id not in item.get('access', []):
            return { "success": False, "error": "User does not have access to this item" }

        # Check slot availability
        schedule = item.get('availability_schedule', {})
        if reservation_time not in schedule:
            return { "success": False, "error": "Time slot not defined for item" }
        if not schedule[reservation_time]:
            return { "success": False, "error": "Time slot unavailable" }

        # All checks passed, create reservation
        # Generate reservation_id (simple incremental or UUID mechanism)
        reservation_id = str(uuid.uuid4())

        reservation: ReservationInfo = {
            "reservation_id": reservation_id,
            "account_id": account_id,
            "item_id": item_id,
            "reservation_time": reservation_time,
            "status": "active",
            "detail": detail,
        }

        self.reservations[reservation_id] = reservation
        # Mark slot as unavailable
        self.items[item_id]["availability_schedule"][reservation_time] = False

        return {
            "success": True,
            "message": "Reservation created",
            "reservation_id": reservation_id,
        }

    def cancel_reservation(self, reservation_id: str, token: str) -> dict:
        """
        Cancels an active reservation. Only the owning account may cancel their reservation,
        subject to appropriate status.

        Args:
            reservation_id (str): The ID of the reservation to cancel.
            token (str): The authentication token of the user trying to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Reservation <reservation_id> cancelled successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
          - Only the owning account may cancel their reservation (using token for authentication).
          - Reservation must be active to be cancelled.
        """
        # 1. Find account by token
        account_id = None
        for user in self.users.values():
            if token in user["tokens"]:
                account_id = user["account_id"]
                break
        if not account_id:
            return { "success": False, "error": "Invalid or unauthorized token" }

        # 2. Ensure reservation exists
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return { "success": False, "error": "Reservation does not exist" }

        # 3. Ensure reservation is owned by account
        if reservation["account_id"] != account_id:
            return { "success": False, "error": "You do not own this reservation" }

        # 4. Reservation must be active
        if reservation["status"] != "active":
            return { "success": False, "error": f"Reservation is not active (current status is '{reservation['status']}')" }

        # 5. Perform cancellation
        reservation["status"] = "cancelled"
        item = self.items.get(reservation["item_id"])
        if item:
            item.setdefault("availability_schedule", {})[reservation["reservation_time"]] = True

        return {
            "success": True,
            "message": f"Reservation {reservation_id} cancelled successfully."
        }

    def modify_reservation_time(self, reservation_id: str, account_id: str, new_time: str) -> dict:
        """
        Change the time slot for an existing reservation, with checks on availability and ownership.

        Args:
            reservation_id (str): The unique identifier for the reservation.
            account_id (str): The account requesting the modification (auth/ownership).
            new_time (str): The desired new reservation time (ISO string).

        Returns:
            dict: {
                "success": True,
                "message": "Reservation time updated to <new_time>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Reservation must exist and belong to given account_id.
            - Reservation must be active (not cancelled or completed).
            - Bookable item must exist and be accessible to account_id.
            - Bookable item must be available at new_time.
            - There must be no conflicting reservation for the item at new_time.
        """
        # Check reservation exists
        if reservation_id not in self.reservations:
            return { "success": False, "error": "Reservation does not exist" }
        reservation = self.reservations[reservation_id]

        # Ownership check
        if reservation["account_id"] != account_id:
            return { "success": False, "error": "Permission denied: only the owning account can modify the reservation" }

        # Status check
        if reservation["status"] not in ["active"]:
            return { "success": False, "error": f"Reservation cannot be modified in its current status: {reservation['status']}" }

        item_id = reservation["item_id"]
        # Check item existence
        if item_id not in self.items:
            return { "success": False, "error": "Bookable item for reservation no longer exists" }
        item = self.items[item_id]

        # Access control check
        if account_id not in item.get("access", []):
            return { "success": False, "error": "Account does not have access to this item" }

        # Check item availability for the new_time
        if item["availability_schedule"].get(new_time) is not True:
            return { "success": False, "error": f"Item is not available at {new_time}" }

        # Check for conflicting reservation for the item at the new_time
        for other_res in self.reservations.values():
            if (
                other_res["item_id"] == item_id
                and other_res["reservation_time"] == new_time
                and other_res["status"] == "active"
                and other_res["reservation_id"] != reservation_id
            ):
                return { "success": False, "error": f"Item already reserved at {new_time}" }

        # All checks passed, perform the update:
        old_time = reservation["reservation_time"]

        # Mark old slot as available
        if old_time in item["availability_schedule"]:
            item["availability_schedule"][old_time] = True
        # Mark new slot as unavailable
        item["availability_schedule"][new_time] = False

        # Update reservation time
        reservation["reservation_time"] = new_time

        return {
            "success": True,
            "message": f"Reservation time updated to {new_time}"
        }

    def batch_cancel_reservations(self, acting_account_id: str, reservation_ids: list) -> dict:
        """
        Cancel multiple reservations for a user (or group of users), 
        ensuring ownership and correct status. Only 'active' reservations
        owned by acting_account_id can be cancelled. 

        Args:
            acting_account_id (str): The account_id of the user initiating the cancellation.
            reservation_ids (list): List of reservation_id values to be cancelled.

        Returns:
            dict: {
                "success": True,
                "message": <summary string detailing which reservations were cancelled, which failed and why>
            }
            or
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - Only the owning account (the one matching reservation.account_id) may cancel a reservation.
            - Only reservations in 'active' status can be cancelled.
        """
        if not isinstance(reservation_ids, list) or not reservation_ids:
            return {"success": False, "error": "No reservation IDs provided"}

        if acting_account_id not in self.users:
            return {"success": False, "error": "Acting account does not exist"}

        cancelled = []
        failed = []

        for rid in reservation_ids:
            rinfo = self.reservations.get(rid)
            if not rinfo:
                failed.append({"reservation_id": rid, "reason": "Reservation does not exist"})
                continue
            if rinfo["account_id"] != acting_account_id:
                failed.append({"reservation_id": rid, "reason": "Does not belong to acting account"})
                continue
            if rinfo["status"] != "active":
                failed.append({"reservation_id": rid, "reason": f"Cannot cancel reservation with status '{rinfo['status']}'"})
                continue

            # Perform cancellation
            rinfo["status"] = "cancelled"
            item = self.items.get(rinfo["item_id"])
            if item:
                item.setdefault("availability_schedule", {})[rinfo["reservation_time"]] = True
            cancelled.append(rid)

        msg = []
        if cancelled:
            msg.append(f"Cancelled reservations: {', '.join(cancelled)}.")
        if failed:
            msg.append(
                "Failures: " +
                "; ".join([f"{f['reservation_id']}: {f['reason']}" for f in failed])
            )
        if not cancelled:
            # All failed
            return {"success": False, "error": "No reservations cancelled. " + " ".join(msg)}
        return {"success": True, "message": " ".join(msg)}

    def update_bookable_item_availability(self, item_id: str, new_availability: Dict[str, bool]) -> dict:
        """
        Modify the availability schedule of a bookable item.

        Args:
            item_id (str): Identifier of the bookable item to update.
            new_availability (Dict[str, bool]): Mapping of ISO time strings to their availability (True/False).

        Returns:
            dict: {
                "success": True,
                "message": "Availability schedule updated for item <item_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Item must exist in self.items.
            - new_availability must be a dict mapping ISO strings to bools.
            - Edge case: If new_availability is empty, it will still overwrite the schedule.
        """
        # Check if item exists
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        # Validate new_availability format
        if not isinstance(new_availability, dict):
            return {"success": False, "error": "Invalid new availability format"}
        for t, v in new_availability.items():
            if not isinstance(t, str) or not isinstance(v, bool):
                return {"success": False, "error": "Availability keys must be string times and values must be boolean"}

        self.items[item_id]["availability_schedule"] = new_availability.copy()

        return {
            "success": True,
            "message": f"Availability schedule updated for item {item_id}"
        }

    def add_bookable_item(
        self,
        item_id: str,
        item_name: str,
        item_type: str,
        location: str,
        availability_schedule: Dict[str, bool],
        access: list
    ) -> dict:
        """
        Add a new bookable item to the system (admin-level action).

        Args:
            item_id (str): Unique identifier for the new item.
            item_name (str): Descriptive name of the item.
            item_type (str): Category/type designation.
            location (str): Physical or logical location.
            availability_schedule (Dict[str, bool]): Schedule of time-slot availability.
            access (List[str]): List of account_ids allowed to view/book the item.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - item_id must be unique; if an item with this ID already exists, fail.
            - All fields are required and should match type.
        """
        # Unique item_id check
        if item_id in self.items:
            return { "success": False, "error": "Item with given item_id already exists" }
        # Basic input validation
        if not all([
            isinstance(item_id, str) and item_id,
            isinstance(item_name, str) and item_name,
            isinstance(item_type, str) and item_type,
            isinstance(location, str) and location,
            isinstance(availability_schedule, dict),
            isinstance(access, list)
        ]):
            return { "success": False, "error": "Invalid or missing required fields" }
        # Optionally, could check for time-string format in availability_schedule

        item_info = {
            "item_id": item_id,
            "item_name": item_name,
            "item_type": item_type,
            "location": location,
            "availability_schedule": availability_schedule,
            "access": access,
        }
        self.items[item_id] = item_info
        return { "success": True, "message": f"Bookable item added: {item_id}" }

    def remove_bookable_item(self, item_id: str) -> dict:
        """
        Remove a bookable item from the system (admin-level action), along with
        all associated reservations.

        Args:
            item_id (str): Unique identifier of the bookable item to remove.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Bookable item <item_id> removed."
                  }
                - On failure: {
                    "success": False,
                    "error": "Bookable item not found"
                  }

        Constraints:
            - If the bookable item does not exist, operation fails.
            - All reservations for this item are also removed from the system.
            - No authentication required (admin-level).
        """
        if item_id not in self.items:
            return { "success": False, "error": "Bookable item not found" }

        # Remove the bookable item itself
        del self.items[item_id]

        # Remove all reservations related to this item
        reservations_to_remove = [
            res_id for res_id, res in self.reservations.items()
            if res["item_id"] == item_id
        ]
        for res_id in reservations_to_remove:
            del self.reservations[res_id]

        return { "success": True, "message": f"Bookable item {item_id} removed." }


class OnlineBookingReservationSystem(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "users" and isinstance(copied, dict):
                normalized = {}
                for entry_key, entry in copied.items():
                    if isinstance(entry, dict) and entry.get("account_id"):
                        normalized[entry["account_id"]] = entry
                    else:
                        normalized[entry_key] = entry
                copied = normalized
            elif key == "items" and isinstance(copied, dict):
                normalized = {}
                for entry_key, entry in copied.items():
                    if isinstance(entry, dict) and entry.get("item_id"):
                        normalized[entry["item_id"]] = entry
                    else:
                        normalized[entry_key] = entry
                copied = normalized
            elif key == "reservations" and isinstance(copied, dict):
                normalized = {}
                for entry_key, entry in copied.items():
                    if isinstance(entry, dict) and entry.get("reservation_id"):
                        normalized[entry["reservation_id"]] = entry
                    else:
                        normalized[entry_key] = entry
                copied = normalized
            setattr(env, key, copied)

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

    def get_account_by_token(self, **kwargs):
        return self._call_inner_tool('get_account_by_token', kwargs)

    def list_accounts_by_tokens(self, **kwargs):
        return self._call_inner_tool('list_accounts_by_tokens', kwargs)

    def list_bookable_items_for_account(self, **kwargs):
        return self._call_inner_tool('list_bookable_items_for_account', kwargs)

    def get_bookable_item_details(self, **kwargs):
        return self._call_inner_tool('get_bookable_item_details', kwargs)

    def check_item_availability_for_time(self, **kwargs):
        return self._call_inner_tool('check_item_availability_for_time', kwargs)

    def list_available_items_for_account_and_time(self, **kwargs):
        return self._call_inner_tool('list_available_items_for_account_and_time', kwargs)

    def get_reservations_for_account(self, **kwargs):
        return self._call_inner_tool('get_reservations_for_account', kwargs)

    def get_reservations_for_item(self, **kwargs):
        return self._call_inner_tool('get_reservations_for_item', kwargs)

    def compare_items_across_accounts(self, **kwargs):
        return self._call_inner_tool('compare_items_across_accounts', kwargs)

    def create_reservation(self, **kwargs):
        return self._call_inner_tool('create_reservation', kwargs)

    def cancel_reservation(self, **kwargs):
        return self._call_inner_tool('cancel_reservation', kwargs)

    def modify_reservation_time(self, **kwargs):
        return self._call_inner_tool('modify_reservation_time', kwargs)

    def batch_cancel_reservations(self, **kwargs):
        return self._call_inner_tool('batch_cancel_reservations', kwargs)

    def update_bookable_item_availability(self, **kwargs):
        return self._call_inner_tool('update_bookable_item_availability', kwargs)

    def add_bookable_item(self, **kwargs):
        return self._call_inner_tool('add_bookable_item', kwargs)

    def remove_bookable_item(self, **kwargs):
        return self._call_inner_tool('remove_bookable_item', kwargs)
