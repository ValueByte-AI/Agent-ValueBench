# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class VirtualCardInfo(TypedDict):
    card_id: str
    user_id: str
    merchant: Optional[str]  # None means no restriction
    spending_limit: float
    status: str
    creation_date: str
    expiration_date: str

class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    account_status: str

class TransactionInfo(TypedDict):
    transaction_id: str
    card_id: str
    amount: float
    merchant: str
    transaction_date: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Persistent virtual card management environment.
        """

        # VirtualCards: {card_id: VirtualCardInfo}
        self.virtual_cards: Dict[str, VirtualCardInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Constraints:
        # - Each VirtualCard must be associated with a single user (user_id).
        # - Spending_limit must be enforced across transactions for each card.
        # - Merchant restriction: if set, only transactions with that merchant are allowed.
        # - Card status (only active cards may be used/retrieved for spending).
        # - card_id must be unique.
        # - New cards cannot be created with a spending limit less than zero.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info object(s) whose name matches the provided name.

        Args:
            name (str): Name of the user(s) to search for.

        Returns:
            dict: 
              - If found: {"success": True, "data": List[UserInfo]} (possibly empty list)
              - If no user found: {"success": False, "error": "No user found with the given name"}

        Notes:
            - Multiple users may share the same name; all matches are returned in a list.
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        if not matches:
            return {"success": False, "error": "No user found with the given name"}
        return {"success": True, "data": matches}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the full user information for a specified user_id.

        Args:
            user_id (str): The unique identifier for the user (_id in UserInfo).

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The corresponding user's info dict.
            }
            or
            {
                "success": False,
                "error": str  # If user_id not found.
            }

        Constraints:
            - user_id must exist in the users dictionary.
        """
        user = self.users.get(user_id)
        if user is not None:
            return {"success": True, "data": user}
        else:
            return {"success": False, "error": "User not found"}

    def list_virtual_cards_by_user(self, user_id: str) -> dict:
        """
        Retrieve all virtual cards belonging to a specified user.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            dict:
                - success: True, with 'data' a list of VirtualCardInfo dicts for cards where card['user_id'] == user_id.
                - success: False, with 'error' if the user_id does not exist.

        Constraints:
            - User with user_id must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        result = [
            card_info for card_info in self.virtual_cards.values()
            if card_info['user_id'] == user_id
        ]
        return { "success": True, "data": result }

    def get_virtual_card_by_merchant(self, user_id: str, merchant: str) -> dict:
        """
        Retrieve a user's virtual card that is restricted to the specified merchant.

        Args:
            user_id (str): The user's unique identifier.
            merchant (str): The merchant name that the virtual card is restricted to.

        Returns:
            dict: 
                { "success": True, "data": VirtualCardInfo }
                OR
                { "success": False, "error": str } if user or matching card not found.

        Constraints:
            - The user must exist.
            - The card must belong to the user and have merchant restriction equal to merchant.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        for card in self.virtual_cards.values():
            # Match owner and specific merchant restriction
            if card["user_id"] == user_id and card["merchant"] == merchant:
                return { "success": True, "data": card }
    
        return { "success": False, "error": "No card found for user with specified merchant" }

    def get_virtual_card_by_id(self, card_id: str) -> dict:
        """
        Retrieve detailed information about a virtual card by its card_id.

        Args:
            card_id (str): The unique identifier of the virtual card.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": VirtualCardInfo
                    }
                On failure (card_id not found):
                    {
                        "success": False,
                        "error": "Virtual card not found"
                    }

        Constraints:
            - card_id must exist in the system.
            - No restriction on card status (all statuses may be retrieved).
        """
        card = self.virtual_cards.get(card_id)
        if card is None:
            return {"success": False, "error": "Virtual card not found"}
        return {"success": True, "data": card}

    def list_active_virtual_cards_by_user(self, user_id: str) -> dict:
        """
        List all virtual cards with 'active' status for a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - If user exists:
                    {
                        "success": True,
                        "data": List[VirtualCardInfo]  # May be empty if the user has no active cards
                    }
                - If user does not exist:
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - User must exist in the system.
            - Only cards with status == 'active' and belonging to user_id are included.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        active_cards = [
            card for card in self.virtual_cards.values()
            if card["user_id"] == user_id and card["status"] == "active"
        ]
        return {"success": True, "data": active_cards}

    def get_transaction_history_for_card(self, card_id: str) -> dict:
        """
        Retrieve all transactions associated with a given card.

        Args:
            card_id (str): The unique ID of the virtual card.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of transactions for this card, possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Error (e.g. card does not exist)
            }

        Constraints:
            - The provided card_id must exist in the virtual_cards storage.
        """
        if card_id not in self.virtual_cards:
            return { "success": False, "error": "Card does not exist" }

        transactions = [
            tx for tx in self.transactions.values()
            if tx["card_id"] == card_id
        ]

        return { "success": True, "data": transactions }

    def create_virtual_card(
        self,
        card_id: str,
        user_id: str,
        merchant: Optional[str],
        spending_limit: float,
        status: str,
        creation_date: str,
        expiration_date: str
    ) -> dict:
        """
        Create a new virtual card for a user with specified attributes, enforcing:
          - spending_limit >= 0,
          - unique card_id,
          - user_id must exist.

        Args:
            card_id (str): Unique identifier for the virtual card.
            user_id (str): The user's unique identifier (owner of the card).
            merchant (Optional[str]): Merchant restriction (None for no restriction).
            spending_limit (float): Spending cap for the card (must be >=0).
            status (str): Initial card status (typically 'active').
            creation_date (str): ISO datetime when the card is created.
            expiration_date (str): ISO datetime when the card expires.

        Returns:
            dict: {
                "success": True,
                "message": "Virtual card created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        """
        # Card ID must be unique
        if card_id in self.virtual_cards:
            return { "success": False, "error": "Card ID already exists." }

        # User must exist
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Spending limit must be >= 0
        if not isinstance(spending_limit, (int, float)) or spending_limit < 0:
            return { "success": False, "error": "Spending limit must be greater than or equal to zero." }

        # Create card info object
        card_info: VirtualCardInfo = {
            "card_id": card_id,
            "user_id": user_id,
            "merchant": merchant,
            "spending_limit": spending_limit,
            "status": status,
            "creation_date": creation_date,
            "expiration_date": expiration_date
        }

        # Add to system
        self.virtual_cards[card_id] = card_info

        return { "success": True, "message": "Virtual card created successfully." }

    def set_virtual_card_status(self, card_id: str, new_status: str) -> dict:
        """
        Change the status of a virtual card (e.g., activate, block, expire).
    
        Args:
            card_id (str): Unique identifier for the virtual card.
            new_status (str): New status value for the card ("active", "blocked", "expired", etc.).
        
        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Status of virtual card <card_id> changed to <new_status>." }
                On failure:
                    { "success": False, "error": "reason" }
        
        Constraints:
            - The card must exist.
            - No restrictions on allowed statuses beyond presence (for robustness).
        """
        if not card_id or not isinstance(card_id, str):
            return { "success": False, "error": "Invalid or missing card_id." }
        if not new_status or not isinstance(new_status, str):
            return { "success": False, "error": "Invalid or missing new_status." }
        card = self.virtual_cards.get(card_id)
        if card is None:
            return { "success": False, "error": "Virtual card not found." }
        card["status"] = new_status
        return { "success": True, "message": f"Status of virtual card {card_id} changed to {new_status}." }

    def update_virtual_card_spending_limit(self, card_id: str, new_spending_limit: float) -> dict:
        """
        Adjust the spending limit of an existing virtual card.

        Args:
            card_id (str): The unique identifier of the target virtual card.
            new_spending_limit (float): The new spending limit value (must be non-negative).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Spending limit updated." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Card must exist.
            - new_spending_limit must be >= 0.
        """
        if card_id not in self.virtual_cards:
            return { "success": False, "error": "Card not found." }

        if new_spending_limit < 0:
            return { "success": False, "error": "Spending limit must be non-negative." }

        self.virtual_cards[card_id]["spending_limit"] = new_spending_limit
        return { "success": True, "message": "Spending limit updated." }

    def delete_virtual_card(self, card_id: str) -> dict:
        """
        Delete (remove) a virtual card specified by its card_id.

        Args:
            card_id (str): Unique identifier of the virtual card to delete.

        Returns:
            dict: 
             - If successful: {"success": True, "message": "Virtual card <card_id> deleted."}
             - If not found: {"success": False, "error": "Card not found."}

        Constraints:
            - Only existing cards can be deleted.
            - Deletion does not remove transaction history (transactions referencing this card_id are retained).
        """
        if card_id not in self.virtual_cards:
            return { "success": False, "error": "Card not found." }

        del self.virtual_cards[card_id]
        return { "success": True, "message": f"Virtual card {card_id} deleted." }

    def update_virtual_card_merchant_restriction(self, card_id: str, merchant: str) -> dict:
        """
        Change the merchant restriction for the specified virtual card.

        Args:
            card_id (str): Unique identifier for the virtual card.
            merchant (str): New merchant restriction. If '', None, or string 'None', removes restriction.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Merchant restriction updated for card <card_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <description of the problem>
                    }

        Constraints:
            - card_id must exist.
            - Allow change regardless of card status (following provided rules).
            - merchant can be None, empty string, or any string. None means no restriction.
        """
        if card_id not in self.virtual_cards:
            return {"success": False, "error": "Card not found."}

        normalized_merchant = merchant
        if merchant is None or (isinstance(merchant, str) and merchant.strip().lower() == "none") or merchant == "":
            normalized_merchant = None

        self.virtual_cards[card_id]["merchant"] = normalized_merchant

        return {"success": True, "message": f"Merchant restriction updated for card {card_id}."}

    def update_virtual_card_expiration_date(self, card_id: str, new_expiration_date: str) -> dict:
        """
        Change the expiration date of a specified virtual card.

        Args:
            card_id (str): ID of the virtual card to update.
            new_expiration_date (str): New expiration date to be set (string format, validated elsewhere).

        Returns:
            dict: 
                - { "success": True, "message": "Expiration date for card <card_id> updated to <new_expiration_date>" }
                - or { "success": False, "error": "Virtual card not found" }

        Constraints:
            - card_id must exist in the system.
            - No validation on date format is enforced here.
        """
        if card_id not in self.virtual_cards:
            return { "success": False, "error": "Virtual card not found" }

        self.virtual_cards[card_id]["expiration_date"] = new_expiration_date
        return {
            "success": True,
            "message": f"Expiration date for card {card_id} updated to {new_expiration_date}"
        }


class VirtualCardManagementSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_virtual_cards_by_user(self, **kwargs):
        return self._call_inner_tool('list_virtual_cards_by_user', kwargs)

    def get_virtual_card_by_merchant(self, **kwargs):
        return self._call_inner_tool('get_virtual_card_by_merchant', kwargs)

    def get_virtual_card_by_id(self, **kwargs):
        return self._call_inner_tool('get_virtual_card_by_id', kwargs)

    def list_active_virtual_cards_by_user(self, **kwargs):
        return self._call_inner_tool('list_active_virtual_cards_by_user', kwargs)

    def get_transaction_history_for_card(self, **kwargs):
        return self._call_inner_tool('get_transaction_history_for_card', kwargs)

    def create_virtual_card(self, **kwargs):
        return self._call_inner_tool('create_virtual_card', kwargs)

    def set_virtual_card_status(self, **kwargs):
        return self._call_inner_tool('set_virtual_card_status', kwargs)

    def update_virtual_card_spending_limit(self, **kwargs):
        return self._call_inner_tool('update_virtual_card_spending_limit', kwargs)

    def delete_virtual_card(self, **kwargs):
        return self._call_inner_tool('delete_virtual_card', kwargs)

    def update_virtual_card_merchant_restriction(self, **kwargs):
        return self._call_inner_tool('update_virtual_card_merchant_restriction', kwargs)

    def update_virtual_card_expiration_date(self, **kwargs):
        return self._call_inner_tool('update_virtual_card_expiration_date', kwargs)

