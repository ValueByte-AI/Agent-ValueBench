# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
import json



class UserAccountInfo(TypedDict):
    _id: str
    name: str
    contact_info: str
    account_status: str

class CardControlInfo(TypedDict):
    card_id: str
    control_type: str
    value: str

class PaymentCardInfo(TypedDict):
    card_id: str
    user_id: str
    card_number: str
    card_type: str
    expiration_date: str
    spending_limit: float
    status: str  # active/inactive
    controls: List[CardControlInfo]  # List of current controls

class TransactionInfo(TypedDict):
    transaction_id: str
    card_id: str
    timestamp: str
    amount: float
    merchant: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserAccountInfo}
        self.users: Dict[str, UserAccountInfo] = {}

        # Cards: {card_id: PaymentCardInfo}
        self.cards: Dict[str, PaymentCardInfo] = {}

        # Controls: {card_id: List[CardControlInfo]}
        self.controls: Dict[str, List[CardControlInfo]] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}
        self._system_spending_limit_bounds_state: Any = None

        # --- Constraints ---
        # - A card’s spending limit can only be changed if the card is active.
        # - The new spending limit must be a non-negative value and within system-configured maximum/minimum thresholds.
        # - Only the user who owns the card can modify its controls or limits.
        # - Card status, expiration, and other constraints may restrict operations (e.g., cannot transact if inactive or expired).

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by user name.

        Args:
            name (str): The user's name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserAccountInfo]  # List of matching user info dicts
            }
            or
            {
                "success": False,
                "error": str  # 'User not found' if name does not match any user
            }

        Notes:
            - If multiple users share the same name, all are returned.
            - Name comparison is case sensitive.
        """
        matches = [user_info for user_info in self.users.values() if user_info["name"] == name]
        if not matches:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": matches}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user account details by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo,  # On success, the user account information
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if user_id does not exist
            }

        Constraints:
            - No special permission required.
            - Returns error if user_id is not present in the system.
        """
        if user_id in self.users:
            return {"success": True, "data": self.users[user_id]}
        else:
            return {"success": False, "error": "User not found"}

    def list_user_cards(self, user_id: str) -> dict:
        """
        List all payment cards associated with the given user.

        Args:
            user_id (str): The unique ID of the user whose cards are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[PaymentCardInfo],  # possibly empty if no cards
            }
            or
            {
                "success": False,
                "error": str  # if user does not exist
            }

        Constraints:
            - The provided user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_cards = [
            card for card in self.cards.values()
            if card["user_id"] == user_id
        ]
        return {"success": True, "data": user_cards}

    def get_card_by_id(self, card_id: str) -> dict:
        """
        Retrieve the full details (PaymentCardInfo) of a card using its card_id.

        Args:
            card_id (str): The unique identifier for the card.

        Returns:
            dict: {
                "success": True,
                "data": PaymentCardInfo  # All fields describing the payment card
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g., card not found
            }

        Constraints:
            - Card must exist in the system.
        """
        card_info = self.cards.get(card_id)
        if not card_info:
            return { "success": False, "error": "Card not found" }
        return { "success": True, "data": card_info }

    def get_card_by_name_for_user(self, user_id: str, friendly_name: str) -> dict:
        """
        Retrieve a user's card by a friendly name or tag (e.g., "Uber Eats card"), if supported.

        Args:
            user_id (str): The unique ID of the user.
            friendly_name (str): The friendly name or tag to search for.

        Returns:
            dict: 
              - On success: { "success": True, "data": PaymentCardInfo }
              - On failure: { "success": False, "error": str }
    
        Notes:
            - The system does not support an explicit "card name" field. The implementation tries to match:
                1. The card's `card_type` (case-insensitive).
                2. Any CardControl with control_type "name" and value matching the friendly_name.
            - Returns the first match found.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
    
        # Collect all the user's cards
        user_cards = [
            card for card in self.cards.values()
            if card["user_id"] == user_id
        ]
        if not user_cards:
            return { "success": False, "error": "User has no cards." }

        friendly_name_lower = friendly_name.strip().lower()
        for card in user_cards:
            # 1. Check card_type as friendly name (case-insensitive)
            if card.get("card_type", "").strip().lower() == friendly_name_lower:
                return { "success": True, "data": card }
        
            # 2. Check if controls contain a "name" type control with matching value
            for control in card.get("controls", []):
                if control.get("control_type", "").strip().lower() == "name" and \
                   control.get("value", "").strip().lower() == friendly_name_lower:
                    return { "success": True, "data": card }

        return { "success": False, "error": "Card with friendly name not found for user." }

    def get_card_status(self, card_id: str) -> dict:
        """
        Retrieve the status (active/inactive), expiration date, and main attributes of a card.

        Args:
            card_id (str): The unique identifier of the card to query.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": {
                        "card_id": ...,
                        "status": ...,
                        "expiration_date": ...,
                        "card_type": ...,
                        "card_number": ...,
                        "user_id": ...,
                        "spending_limit": ...,
                    }
                  }
                - On failure: {
                    "success": False,
                    "error": <error message>
                  }
        """
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card not found" }

        # Collect the main attributes for status reporting
        card_status_info = {
            "card_id": card["card_id"],
            "status": card["status"],
            "expiration_date": card["expiration_date"],
            "card_type": card["card_type"],
            "card_number": card["card_number"],
            "user_id": card["user_id"],
            "spending_limit": card["spending_limit"]
        }
        return { "success": True, "data": card_status_info }

    def get_card_spending_limit(self, card_id: str) -> dict:
        """
        Retrieve the current spending limit of a card.

        Args:
            card_id (str): The unique identifier of the payment card.

        Returns:
            dict: 
                - On success: { "success": True, "data": { "card_id": str, "spending_limit": float } }
                - On failure: { "success": False, "error": str }
        Constraints:
            - The specified card_id must exist in the system.
        """
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card does not exist" }
        return {
            "success": True,
            "data": {
                "card_id": card_id,
                "spending_limit": card["spending_limit"]
            }
        }

    def get_card_controls(self, card_id: str) -> dict:
        """
        List all control settings (CardControlInfo) for a specific card.

        Args:
            card_id (str): The unique identifier for the card.

        Returns:
            dict: {
                "success": True,
                "data": List[CardControlInfo]  # List of controls for the card; empty if no controls
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., card not found
            }

        Constraints:
            - The card_id must exist in the system.
        """
        if card_id not in self.cards:
            return { "success": False, "error": "Card not found" }
    
        # Prefer the up-to-date controls dictionary, but fallback to card info if needed
        controls = self.controls.get(card_id)
        if controls is None:
            # controls may also live in the PaymentCardInfo for backward compatibility
            card_info = self.cards[card_id]
            controls = card_info.get("controls", [])
        return { "success": True, "data": controls }

    def check_user_owns_card(self, user_id: str, card_id: str) -> dict:
        """
        Verify if a certain card belongs to (is owned by) a given user.

        Args:
            user_id (str): The unique identifier for the user.
            card_id (str): The unique identifier for the card.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if card belongs to user, else False
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure
                }
        Constraints:
            - User and card must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if card_id not in self.cards:
            return { "success": False, "error": "Card does not exist" }
        card_info = self.cards[card_id]
        is_owned = card_info["user_id"] == user_id
        return { "success": True, "data": is_owned }

    def get_system_spending_limit_bounds(self) -> dict:
        """
        Retrieve the system-configured minimum and maximum allowable spending limits.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "min_limit": float,
                    "max_limit": float
                }
            }
            or
            {
                "success": False,
                "error": str
            }
        
        Constraints:
            - Must return the system-wide spending limit bounds if set.
            - If not set, returns sensible defaults (min: 0.0, max: 10000.0).
        """
        configured_state = getattr(self, "_system_spending_limit_bounds_state", None)
        if isinstance(configured_state, str):
            try:
                configured_state = json.loads(configured_state)
            except Exception:
                configured_state = None

        if isinstance(configured_state, dict):
            min_limit = configured_state.get("min_limit", configured_state.get("min"))
            max_limit = configured_state.get("max_limit", configured_state.get("max"))
        else:
            min_limit = getattr(self, "spending_limit_min", 0.0)
            max_limit = getattr(self, "spending_limit_max", 10000.0)

        if (min_limit is None) or (max_limit is None):
            return {
                "success": False,
                "error": "System spending limit bounds are not configured."
            }

        return {
            "success": True,
            "data": {
                "min_limit": float(min_limit),
                "max_limit": float(max_limit)
            }
        }

    def list_card_transactions(self, card_id: str) -> dict:
        """
        List all transaction records for a given card.

        Args:
            card_id (str): The unique identifier of the card whose transactions should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of transaction log entries for the card (can be empty if no transactions)
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g. card does not exist)
            }

        Constraints:
            - The card must exist in the system.
        """
        if card_id not in self.cards:
            return { "success": False, "error": "Card does not exist" }

        transactions = [
            info for info in self.transactions.values()
            if info["card_id"] == card_id
        ]

        return { "success": True, "data": transactions }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve details about a specific transaction by its unique ID.

        Args:
            transaction_id (str): The unique identifier for the transaction.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo   # Transaction details as a dictionary
            }
            or
            {
                "success": False,
                "error": str              # Error message if not found
            }

        Constraints:
            - The transaction must exist in the system.
            - No permission/auth check required to query.
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction does not exist"}
        return {"success": True, "data": transaction}

    def set_card_spending_limit(self, card_id: str, new_limit: float, user_id: str) -> dict:
        """
        Update the spending limit of a card, after validating all business constraints.

        Args:
            card_id (str): The ID of the card to update.
            new_limit (float): The new spending limit to set.
            user_id (str): The ID of the user attempting to set the limit.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Spending limit updated successfully."
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Card must exist.
            - User must exist.
            - Only the user who owns the card may modify its spending limit.
            - Card must be active.
            - New limit must be a non-negative number and within system-configured bounds.
        """
        # Validate card exists
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card does not exist."}

        # Validate user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # Validate ownership
        if card["user_id"] != user_id:
            return {"success": False, "error": "User does not own this card."}

        # Only active cards can have their limit changed
        if card["status"] != "active":
            return {"success": False, "error": "Card is not active."}

        # New limit must be a non-negative number
        try:
            limit_val = float(new_limit)
        except (TypeError, ValueError):
            return {"success": False, "error": "Provided spending limit is not a valid number."}

        if limit_val < 0:
            return {"success": False, "error": "Spending limit must be non-negative."}

        # Get system bounds
        bounds_result = self.get_system_spending_limit_bounds()
        if not bounds_result.get("success"):
            return {"success": False, "error": "Could not retrieve system spending limit bounds."}

        min_limit = bounds_result["data"].get("min_limit", bounds_result["data"].get("min", 0))
        max_limit = bounds_result["data"].get("max_limit", bounds_result["data"].get("max", float("inf")))

        if limit_val < min_limit:
            return {"success": False, "error": f"Spending limit below minimum allowed: {min_limit}"}
        if limit_val > max_limit:
            return {"success": False, "error": f"Spending limit exceeds maximum allowed: {max_limit}"}

        # Passed all checks; update the card
        card["spending_limit"] = limit_val
        self.cards[card_id] = card

        return {"success": True, "message": "Spending limit updated successfully."}

    def activate_card(self, card_id: str, user_id: str) -> dict:
        """
        Set the status of a specific card to "active".
    
        Args:
            card_id (str): The unique identifier of the card to activate.
            user_id (str): The user attempting the activation (for permission checking).
        
        Returns:
            dict: {
                "success": True,
                "message": "Card activated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }
    
        Constraints:
          - Card must exist.
          - Only the owning user can activate the card.
          - Card should not already be active.
          - Card should not be expired (expiration_date in the past).
        """

        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card does not exist." }

        if card["user_id"] != user_id:
            return { "success": False, "error": "Permission denied. User does not own this card." }
    
        if card["status"] == "active":
            return { "success": False, "error": "Card is already active." }
    
        # Check if expired (assume expiration_date format: 'YYYY-MM' or 'YYYY-MM-DD')
        try:
            exp_date_str = card["expiration_date"]
            if len(exp_date_str) == 7:
                exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m")
                # Assume cards expire at end of the expiration month
                next_month = exp_date.replace(day=28) + datetime.timedelta(days=4)
                exp_date = next_month - datetime.timedelta(days=next_month.day)
            else:
                exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d")
            now = datetime.datetime.now()
            if now > exp_date:
                return { "success": False, "error": "Card is expired and cannot be activated." }
        except Exception:
            return { "success": False, "error": "Invalid expiration date format." }

        card["status"] = "active"
        self.cards[card_id] = card
        return { "success": True, "message": "Card activated successfully." }

    def deactivate_card(self, card_id: str, user_id: str) -> dict:
        """
        Deactivate the specified card by setting its status to 'inactive'.
    
        Args:
            card_id (str): The card identifier to deactivate.
            user_id (str): The currently authenticated user attempting the operation.
    
        Returns:
            dict: {
                "success": True,
                "message": "Card <card_id> deactivated."
            }
            or
            {
                "success": False,
                "error": <error description>
            }
    
        Constraints:
            - Only the user who owns the card can deactivate it.
            - If the card is already inactive, the operation is idempotent (still returns success).
            - Card must exist.
        """
        card = self.cards.get(card_id)
        if card is None:
            return { "success": False, "error": "Card does not exist." }
        if card["user_id"] != user_id:
            return { "success": False, "error": "Permission denied. User does not own the card." }
        if card["status"] == "inactive":
            return { "success": True, "message": f"Card {card_id} is already inactive." }
        card["status"] = "inactive"
        return { "success": True, "message": f"Card {card_id} deactivated." }

    def modify_card_control(
        self, user_id: str, card_id: str, control_type: str, new_value: str
    ) -> dict:
        """
        Adjust a specific control setting (e.g., merchant restriction or online payment permission)
        for a payment card.

        Args:
            user_id (str): The ID of the user requesting the modification.
            card_id (str): The payment card's ID.
            control_type (str): The specific type of control to change.
            new_value (str): The new value to set for this control.

        Returns:
            dict: {
                "success": True,
                "message": "Control updated."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Only the user who owns the card may modify its controls.
            - Card and user must exist.
            - The specified control_type must already exist for the card.
        """
        # Check card existence
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card not found." }

        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found." }

        # Check ownership
        if card["user_id"] != user_id:
            return { "success": False, "error": "User does not own this card." }

        # Check controls existence for the card
        card_controls = self.controls.get(card_id, [])
        found = False
        for ctrl in card_controls:
            if ctrl["control_type"] == control_type:
                ctrl["value"] = new_value
                found = True

        if found:
            # Also update the copy in card["controls"] list for consistency
            for ctrl in card["controls"]:
                if ctrl["control_type"] == control_type:
                    ctrl["value"] = new_value
            return { "success": True, "message": "Control updated." }
        else:
            return { "success": False, "error": "Specified control does not exist for this card." }

    def add_card_control(
        self, user_id: str, card_id: str, control_type: str, value: str
    ) -> dict:
        """
        Add a new control type/value to a card.

        Args:
            user_id (str): The user attempting to add the control.
            card_id (str): The card to which the control is being added.
            control_type (str): Type of the control (e.g., "merchant_block_list").
            value (str): Value for the control (e.g., "block_merchant_foo").

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Control added to card."
                  }
                - On failure: {
                    "success": False,
                    "error": "<reason>"
                  }

        Constraints:
            - User must exist and own the card.
            - Card must exist.
            - Control (type/value) must not already exist for card.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check card exists
        if card_id not in self.cards:
            return {"success": False, "error": "Card does not exist."}

        card_info = self.cards[card_id]

        # Only owner can modify controls
        if card_info["user_id"] != user_id:
            return {"success": False, "error": "User does not own the card."}

        # Initialize controls list if not present
        if card_id not in self.controls:
            self.controls[card_id] = []

        # Check for duplicate
        for c in self.controls[card_id]:
            if c["control_type"] == control_type and c["value"] == value:
                return {"success": False, "error": "This control already exists for the card."}

        # Create and add the new control
        new_control = {
            "card_id": card_id,
            "control_type": control_type,
            "value": value
        }
        self.controls[card_id].append(new_control)

        # Also update the card's embedded controls list
        if "controls" in card_info:
            card_info["controls"].append(new_control)
        else:
            card_info["controls"] = [new_control]

        return {"success": True, "message": "Control added to card."}

    def remove_card_control(self, user_id: str, card_id: str, control_type: str) -> dict:
        """
        Remove a specific control (by type) from a card.

        Args:
            user_id (str): The user requesting the operation. Must own the card.
            card_id (str): The card from which to remove the control.
            control_type (str): The control_type to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Control removed from card."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Only the card owner may modify card controls.
            - Fails if card does not exist, or not owned by user, or control not present.
        """
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card does not exist."}
        if card["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: User does not own the card."}

        controls = self.controls.get(card_id, [])
        # Find the index(es) of controls matching the type
        filtered_controls = [c for c in controls if c["control_type"] != control_type]
        if len(filtered_controls) == len(controls):
            return {"success": False, "error": "Specified control type not found on this card."}

        # Update controls storage
        self.controls[card_id] = filtered_controls
        # Also update the PaymentCardInfo's .controls list
        card_controls_updated = [c for c in card["controls"] if c["control_type"] != control_type]
        card["controls"] = card_controls_updated

        return {"success": True, "message": "Control removed from card."}

    def update_card_expiration(self, card_id: str, new_expiration_date: str) -> dict:
        """
        Change the expiration date of a card (typically an admin/issuer operation).

        Args:
            card_id (str): The ID of the card to update.
            new_expiration_date (str): The new expiration date to set (expected format: 'YYYY-MM' or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Expiration date updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        Constraints:
            - The card with the given card_id must exist in the system.
            - This operation may be administrator/issuer-restricted; access control should be handled externally.
            - No exceptions are raised; errors are indicated in the returned dict.
        """
        if card_id not in self.cards:
            return { "success": False, "error": "Card not found." }

        if not new_expiration_date or not isinstance(new_expiration_date, str):
            return { "success": False, "error": "Invalid expiration date." }

        # Optionally: add a basic format check (YYYY-MM)
        parts = new_expiration_date.split('-')
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            return { "success": False, "error": "Expiration date format should be YYYY-MM." }
        year, month = parts
        if not (1 <= int(month) <= 12):
            return { "success": False, "error": "Month must be between 01 and 12." }

        # Update expiration date
        self.cards[card_id]["expiration_date"] = new_expiration_date
        return { "success": True, "message": "Expiration date updated." }


class DigitalWalletCardManagementSystem(BaseEnv):
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
            if key == "get_system_spending_limit_bounds":
                setattr(env, "_system_spending_limit_bounds_state", copy.deepcopy(value))
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_cards(self, **kwargs):
        return self._call_inner_tool('list_user_cards', kwargs)

    def get_card_by_id(self, **kwargs):
        return self._call_inner_tool('get_card_by_id', kwargs)

    def get_card_by_name_for_user(self, **kwargs):
        return self._call_inner_tool('get_card_by_name_for_user', kwargs)

    def get_card_status(self, **kwargs):
        return self._call_inner_tool('get_card_status', kwargs)

    def get_card_spending_limit(self, **kwargs):
        return self._call_inner_tool('get_card_spending_limit', kwargs)

    def get_card_controls(self, **kwargs):
        return self._call_inner_tool('get_card_controls', kwargs)

    def check_user_owns_card(self, **kwargs):
        return self._call_inner_tool('check_user_owns_card', kwargs)

    def get_system_spending_limit_bounds(self, **kwargs):
        return self._call_inner_tool('get_system_spending_limit_bounds', kwargs)

    def list_card_transactions(self, **kwargs):
        return self._call_inner_tool('list_card_transactions', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def set_card_spending_limit(self, **kwargs):
        return self._call_inner_tool('set_card_spending_limit', kwargs)

    def activate_card(self, **kwargs):
        return self._call_inner_tool('activate_card', kwargs)

    def deactivate_card(self, **kwargs):
        return self._call_inner_tool('deactivate_card', kwargs)

    def modify_card_control(self, **kwargs):
        return self._call_inner_tool('modify_card_control', kwargs)

    def add_card_control(self, **kwargs):
        return self._call_inner_tool('add_card_control', kwargs)

    def remove_card_control(self, **kwargs):
        return self._call_inner_tool('remove_card_control', kwargs)

    def update_card_expiration(self, **kwargs):
        return self._call_inner_tool('update_card_expiration', kwargs)
