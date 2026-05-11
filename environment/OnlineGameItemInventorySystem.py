# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
import uuid
from typing import Optional, Dict, Any



class PlayerInfo(TypedDict):
    player_id: str
    profile_details: dict  # Or str, depending on actual implementation
    currency_balance: Dict[str, float]  # currency_name → amount

class ItemInfo(TypedDict):
    item_id: str
    name: str
    supported_game_ids: List[str]
    price_per_currency: Dict[str, float]  # currency_name → price
    item_type: str

class PurchaseRecordInfo(TypedDict):
    purchase_id: str
    player_id: str
    item_id: str
    quantity: int
    currency_used: str
    timestamp: str  # ISO 8601, or float (UNIX time)

class GameInfo(TypedDict):
    game_id: str
    game_name: str

class CurrencyInfo(TypedDict):
    currency_name: str
    conversion_rate_to_base: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Online Game Item Store and Inventory System

        Constraints:
        - Players cannot purchase an item if they already own it, when the item type is unique or otherwise restricted from duplicate ownership.
        - A player cannot purchase an item unless their balance in the chosen currency is sufficient to cover the item’s cost.
        - Item must be valid for the specified game.
        - All purchase transactions must be recorded with a timestamp.
        - Item quantities and currency balances must be updated atomically per transaction to prevent race conditions.
        """

        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Items: {item_id: ItemInfo}
        self.items: Dict[str, ItemInfo] = {}

        # Inventory: {player_id: {item_id: quantity}}
        self.inventory: Dict[str, Dict[str, int]] = {}

        # Purchase Records: {purchase_id: PurchaseRecordInfo}
        self.purchase_records: Dict[str, PurchaseRecordInfo] = {}

        # Games: {game_id: GameInfo}
        self.games: Dict[str, GameInfo] = {}

        # Currencies: {currency_name: CurrencyInfo}
        self.currencies: Dict[str, CurrencyInfo] = {}

    def get_player_info(self, player_id: str) -> dict:
        """
        Retrieve detailed information for a given player_id.

        Args:
            player_id (str): The unique player identifier to look up.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": PlayerInfo (dictionary with profile_details and currency_balance)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Player not found"
                    }
        Constraints:
            - player_id must exist in the system.
        """
        player = self.players.get(player_id)
        if not player:
            return { "success": False, "error": "Player not found" }
        return { "success": True, "data": player }

    def get_item_by_name(self, item_name: str) -> dict:
        """
        Find and return item information by the given item name.

        Args:
            item_name (str): The human-readable name of the item to search for.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": <ItemInfo dict>}
                - On failure:
                    {"success": False, "error": "Item not found"}
        Constraints:
            - Name matching is case-sensitive.
            - Returns the first match if multiple items share the same name.
        """
        for item in self.items.values():
            if item["name"] == item_name:
                return {
                    "success": True,
                    "data": item
                }
        return {
            "success": False,
            "error": "Item not found"
        }

    def get_item_info(self, item_id: str) -> dict:
        """
        Retrieve item information (including price and supported games) by item_id.

        Args:
            item_id (str): The unique identifier for the item.

        Returns:
            dict: 
                - { "success": True, "data": ItemInfo } if item exists
                - { "success": False, "error": str } if item does not exist

        Constraints:
            - item_id must correspond to an item in the catalog.
        """
        if item_id not in self.items:
            return { "success": False, "error": "Item not found" }

        return { "success": True, "data": self.items[item_id] }

    def get_player_inventory(self, player_id: str) -> dict:
        """
        List all items and their quantities owned by the specified player.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": [ { "item_id": str, "quantity": int }, ... ]
                          # List may be empty if no items are owned
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason (e.g. "Player does not exist")
                    }
        Constraints:
            - Fails if player does not exist in the system.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        # Get the inventory dictionary for this player, could be missing
        player_inventory = self.inventory.get(player_id, {})
        inventory_list = [
            { "item_id": item_id, "quantity": quantity }
            for item_id, quantity in player_inventory.items()
        ]

        return { "success": True, "data": inventory_list }

    def check_item_ownership(self, player_id: str, item_id: str) -> dict:
        """
        Determine whether a player owns (and how many units of) a given item.

        Args:
            player_id (str): The unique identifier of the player.
            item_id (str): The unique identifier of the item.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "owns": bool,   # True if quantity > 0, else False
                            "quantity": int # Number of this item owned by the player
                        }
                    }
                On error:
                    {
                        "success": False,
                        "error": str     # Human-readable error message.
                    }

        Constraints:
            - Returns quantity 0 and owns: False if player does not own this item.
            - Returns error if player or item does not exist in system.
        """
        # Check for player existence
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        # Check for item existence
        if item_id not in self.items:
            return { "success": False, "error": "Item does not exist" }

        # Default to 0 if inventory not present
        quantity = 0
        if player_id in self.inventory:
            quantity = self.inventory[player_id].get(item_id, 0)
        owns = quantity > 0

        return {
            "success": True,
            "data": {
                "owns": owns,
                "quantity": quantity
            }
        }

    def get_game_info(self, game_id: str) -> dict:
        """
        Retrieve details of a game by its game_id.

        Args:
            game_id (str): The unique identifier for the game.

        Returns:
            dict:
                - Success: { "success": True, "data": GameInfo }
                - Failure: { "success": False, "error": str }

        Constraints:
            - The game_id must exist in self.games.
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game ID does not exist." }
        return { "success": True, "data": self.games[game_id] }

    def check_item_game_compatibility(self, item_id: str, game_id: str) -> dict:
        """
        Check if a given item is compatible with the specified game.

        Args:
            item_id (str): The unique identifier for the item.
            game_id (str): The unique identifier for the game.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool,  # True if compatible, False otherwise
                }
                or
                {
                    "success": False,
                    "error": str,  # Description of error if item_id or game_id does not exist
                }
        Constraints:
            - item_id must reference a valid Item.
            - game_id must reference a valid Game.
            - Compatibility is determined by presence of game_id in ItemInfo['supported_game_ids'].
        """
        if item_id not in self.items:
            return {"success": False, "error": "Item does not exist"}

        if game_id not in self.games:
            return {"success": False, "error": "Game does not exist"}

        item = self.items[item_id]
        compatible = game_id in item.get("supported_game_ids", [])

        return {"success": True, "data": compatible}

    def get_currency_balance(self, player_id: str, currency_name: str) -> dict:
        """
        Query a player's current balance for a specific currency.

        Args:
            player_id (str): Unique identifier for the player.
            currency_name (str): Name of the currency to query.

        Returns:
            dict: 
              On success: {
                  "success": True,
                  "data": {
                      "player_id": str,
                      "currency_name": str,
                      "balance": float
                  }
              }
              On failure: {
                  "success": False,
                  "error": str
              }

        Constraints:
            - The player must exist.
            - Returns 0 if the player has no balance entry for the specified currency.
            - No permission constraints for this readonly operation.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player does not exist" }
    
        # Optionally validate currency; but if the player's balance dict uses arbitrary names, can skip.
        # Uncomment the next two lines if you wish to validate the currency exists in the system.
        # if currency_name not in self.currencies:
        #     return { "success": False, "error": "Currency does not exist" }

        balance = player["currency_balance"].get(currency_name, 0.0)
        return {
            "success": True,
            "data": {
                "player_id": player_id,
                "currency_name": currency_name,
                "balance": balance
            }
        }

    def get_item_price(self, item_id: str, currency_name: str) -> dict:
        """
        Look up the price of a specific item in a given currency.

        Args:
            item_id (str): ID of the item whose price is sought.
            currency_name (str): The currency in which to display price.

        Returns:
            dict:
              - success: True and data = price (float or int) if found
              - success: False and error = explanation if failure
        """
        item = self.items.get(item_id)
        if not item:
            return {"success": False, "error": "Item does not exist"}

        price_map = item.get("price_per_currency", {})
        if currency_name not in price_map:
            return {"success": False, "error": "Item not available in specified currency"}

        price = price_map[currency_name]
        return {"success": True, "data": price}

    def get_currency_info(self, currency_name: str) -> dict:
        """
        Retrieve definition and conversion info for a given currency.

        Args:
            currency_name (str): The name of the currency.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": CurrencyInfo  # Details including name and its conversion rate to base currency
                    }
                On failure (e.g., not found):
                    {
                        "success": False,
                        "error": str  # Reason, e.g., currency does not exist
                    }
        """
        currency = self.currencies.get(currency_name)
        if currency is None:
            return { "success": False, "error": "Currency does not exist" }
        return { "success": True, "data": currency }

    def get_purchase_history(
        self, 
        player_id: str, 
        item_id: str = None, 
        game_id: str = None
    ) -> dict:
        """
        List all purchase records for a player, optionally filtered by item or game.

        Args:
            player_id (str): ID of the player whose purchase history is requested.
            item_id (str, optional): Restrict to a specific item.
            game_id (str, optional): Restrict to purchases of items compatible with this game.

        Returns:
            dict: {
                "success": True,
                "data": List[PurchaseRecordInfo]  # All matched purchase records.
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - player_id must exist.
            - If provided, item_id and game_id should filter results.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        filtered_records = []
        for record in self.purchase_records.values():
            if record["player_id"] != player_id:
                continue
            if item_id is not None and record["item_id"] != item_id:
                continue
            if game_id is not None:
                # Check if this item supports the specified game
                item_info = self.items.get(record["item_id"])
                if not item_info or game_id not in item_info.get("supported_game_ids", []):
                    continue
            filtered_records.append(record)

        return { "success": True, "data": filtered_records }


    def purchase_item(
        self,
        player_id: str,
        item_id: str,
        currency_name: str,
        quantity: int = 1,
        game_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Atomically purchase a specified item for a player:
          - Checks item existence and compatibility with game (if given)
          - Checks player existence and sufficient currency balance
          - Prevents duplicate ownership for unique or restricted items
          - Deducts currency, adds to inventory, and records transaction with timestamp
    
        Args:
            player_id (str): Player making the purchase.
            item_id (str): Item to purchase.
            currency_name (str): Currency to use for purchase.
            quantity (int): Number of items to purchase (default 1).
            game_id (Optional[str]): Game for which item compatibility is checked (if provided).
    
        Returns:
            dict: 
                On success:
                  {
                    "success": True,
                    "message": "...",
                    "purchase_id": str,
                    "remaining_balance": float,
                    "new_inventory_quantity": int
                  }
                On failure:
                  {
                    "success": False,
                    "error": str
                  }
    
        Constraints:
            - Player, item, currency must exist.
            - Quantity must be positive.
            - Sufficient funds in player currency.
            - No duplicate unique/restricted items.
            - Item must be compatible with specified game (if game_id given).
            - Transaction must be atomic.
        """
        # Existence checks
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        if item_id not in self.items:
            return { "success": False, "error": "Item does not exist" }
        item = self.items[item_id]
        if currency_name not in self.currencies:
            return { "success": False, "error": "Currency does not exist" }
        if currency_name not in item["price_per_currency"]:
            return { "success": False, "error": "Item not purchasable in this currency" }
        if quantity <= 0:
            return { "success": False, "error": "Quantity must be positive" }
        player = self.players[player_id]
        price_per_unit = item["price_per_currency"][currency_name]
        total_price = price_per_unit * quantity

        # Game compatibility check
        if game_id is not None:
            if game_id not in self.games:
                return { "success": False, "error": "Game does not exist" }
            if game_id not in item["supported_game_ids"]:
                return { "success": False, "error": "Item not compatible with the specified game" }

        # Ownership restriction for "unique" or similar item types
        item_type = item.get("item_type", "")
        player_inventory = self.inventory.get(player_id, {})
        already_owned_qty = player_inventory.get(item_id, 0)
        if item_type.lower() in ["unique", "singleton", "non-duplicable"]:  # Extend as needed
            if already_owned_qty > 0:
                return { "success": False, "error": "Player already owns this unique item" }
            if quantity > 1:
                return { "success": False, "error": "Cannot purchase multiple of a unique item" }

        # Sufficient funds check
        current_balance = player["currency_balance"].get(currency_name, 0.0)
        if current_balance < total_price:
            return { "success": False, "error": "Insufficient balance" }

        # --- Begin Atomic Transaction ---
        # Deduct currency
        new_balance = current_balance - total_price
        # Update balance (copy to avoid partial update issues)
        player_currency_balance = dict(player["currency_balance"])
        player_currency_balance[currency_name] = new_balance
        self.players[player_id]["currency_balance"] = player_currency_balance

        # Update inventory
        new_inventory = dict(player_inventory)
        new_quantity = already_owned_qty + quantity
        new_inventory[item_id] = new_quantity
        self.inventory[player_id] = new_inventory

        # Record purchase
        purchase_id = uuid.uuid4().hex
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        purchase_record = {
            "purchase_id": purchase_id,
            "player_id": player_id,
            "item_id": item_id,
            "quantity": quantity,
            "currency_used": currency_name,
            "timestamp": ts
        }
        self.purchase_records[purchase_id] = purchase_record

        return {
            "success": True,
            "message": f"Purchased {quantity} of item {item_id} for player {player_id}",
            "purchase_id": purchase_id,
            "remaining_balance": new_balance,
            "new_inventory_quantity": new_quantity
        }

    def update_player_inventory(self, player_id: str, item_id: str, quantity_change: int) -> dict:
        """
        Add or adjust the quantity of an item owned by a player in their inventory.

        Args:
            player_id (str): The player's unique identifier.
            item_id (str): The item's unique identifier.
            quantity_change (int): The amount to change the quantity by (positive to add, negative to remove).

        Returns:
            dict: 
                On success: { "success": True, "message": "Player inventory updated successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Player and item must exist.
            - Cannot reduce item quantity below zero.
            - If adding a new item: initialize in inventory if not present.
            - If removal reduces quantity to zero: remove from inventory (optional, but not below zero).
            - No duplicate entries per (player_id, item_id).
        """
        # Validate player
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist." }

        # Validate item
        if item_id not in self.items:
            return { "success": False, "error": "Item does not exist." }

        # Get or create player's inventory
        player_inventory = self.inventory.setdefault(player_id, {})

        current_qty = player_inventory.get(item_id, 0)
        new_qty = current_qty + quantity_change

        if quantity_change == 0:
            # No adjustment: treat as success (no-op)
            return { "success": True, "message": "No change to inventory." }

        if new_qty < 0:
            return { "success": False, "error": "Cannot reduce item quantity below zero." }
        elif new_qty == 0:
            # Remove item from inventory if exists and quantity drops to zero
            if item_id in player_inventory:
                del player_inventory[item_id]
            # else, nothing to remove but resulting state is valid (as if item not present)
            return { "success": True, "message": "Item removed from inventory (quantity is zero)." }
        else:
            # Set or update quantity
            player_inventory[item_id] = new_qty
            return { "success": True, "message": "Player inventory updated successfully." }

    def update_currency_balance(self, player_id: str, currency_name: str, amount: float) -> dict:
        """
        Add or deduct an amount from a player's currency balance.

        Args:
            player_id (str): The player's unique identifier.
            currency_name (str): The name of the currency.
            amount (float): Amount to add (positive) or deduct (negative).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Player <player_id> currency <currency_name> balance updated to <new_balance>" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Player and currency must exist.
            - Player's balance in the currency cannot go negative.
            - Zero-amount results in no-effect but returns success.
        """
        # Check if player exists
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        # Check if currency exists in the system
        if currency_name not in self.currencies:
            return {"success": False, "error": "Currency does not exist"}

        # Get player's balance info
        currency_balance = self.players[player_id]["currency_balance"]
        current_balance = currency_balance.get(currency_name, 0.0)

        # Calculate new balance
        new_balance = current_balance + amount

        if new_balance < 0:
            return {"success": False, "error": "Insufficient balance; balance cannot go negative"}

        # Zero-amount: No operation but still "success"
        if amount == 0:
            return {
                "success": True,
                "message": f"No change: Player {player_id} currency {currency_name} balance is {current_balance}"
            }

        # Update balance
        self.players[player_id]["currency_balance"][currency_name] = new_balance

        return {
            "success": True,
            "message": f"Player {player_id} currency {currency_name} balance updated to {new_balance}"
        }

    def record_purchase(
        self,
        purchase_id: str,
        player_id: str,
        item_id: str,
        quantity: int,
        currency_used: str,
        timestamp: str
    ) -> dict:
        """
        Create and store a new Purchase Record.

        Args:
            purchase_id (str): Unique identifier for the purchase record.
            player_id (str): Player who made the purchase.
            item_id (str): Item being purchased.
            quantity (int): Number of items purchased (must be > 0).
            currency_used (str): The in-game currency used in the purchase.
            timestamp (str): ISO8601 or UNIX float time.

        Returns:
            dict: 
             - On success: {"success": True, "message": "Purchase record created and stored."}
             - On failure: {"success": False, "error": "reason"}

        Constraints:
            - purchase_id must be unique.
            - player_id, item_id, and currency_used must exist.
            - quantity must be positive.
            - timestamp must be provided.
            - Actual balance and inventory updates are handled elsewhere.
        """
        # Uniqueness & existence checks
        if not purchase_id or purchase_id in self.purchase_records:
            return {"success": False, "error": "purchase_id is missing or already exists."}
        if player_id not in self.players:
            return {"success": False, "error": "player_id does not exist."}
        if item_id not in self.items:
            return {"success": False, "error": "item_id does not exist."}
        if currency_used not in self.currencies:
            return {"success": False, "error": "currency_used does not exist."}
        if not isinstance(quantity, int) or quantity <= 0:
            return {"success": False, "error": "quantity must be a positive integer."}
        if not timestamp:
            return {"success": False, "error": "timestamp must be provided."}

        record: PurchaseRecordInfo = {
            "purchase_id": purchase_id,
            "player_id": player_id,
            "item_id": item_id,
            "quantity": quantity,
            "currency_used": currency_used,
            "timestamp": timestamp,
        }
        self.purchase_records[purchase_id] = record

        return {"success": True, "message": "Purchase record created and stored."}

    def rollback_transaction(self, purchase_id: str) -> dict:
        """
        Undo a purchase (e.g., in case of error or insufficient atomicity—restores balances and inventory).

        Args:
            purchase_id (str): The unique ID of the purchase to rollback.

        Returns:
            dict: {
                "success": True,
                "message": "Purchase rollback successful."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - All changes (currency refund, inventory removal, and record deletion) must be applied atomically.
            - If purchase record does not exist, failure.
            - Cannot roll back if player doesn't have enough of the item to remove.
        """
        record = self.purchase_records.get(purchase_id)
        if not record:
            return { "success": False, "error": "Purchase record does not exist." }
        player_id = record["player_id"]
        item_id = record["item_id"]
        quantity = record["quantity"]
        currency = record["currency_used"]
        amount_spent = None
        if item_id not in self.items:
            return { "success": False, "error": "Item info missing, cannot rollback safely." }
        item_info = self.items[item_id]
        if currency not in item_info["price_per_currency"]:
            return { "success": False, "error": "Currency information for item is missing." }
        amount_spent = item_info["price_per_currency"][currency] * quantity

        # Rollback currency
        player_info = self.players.get(player_id)
        if not player_info:
            return { "success": False, "error": "Player does not exist." }
        # Add the amount back to balance
        if currency not in player_info["currency_balance"]:
            return { "success": False, "error": "Player's currency information is missing." }
        # Rollback inventory
        if player_id not in self.inventory or item_id not in self.inventory[player_id]:
            return { "success": False, "error": "Inventory inconsistent: player does not own this item." }
        if self.inventory[player_id][item_id] < quantity:
            return { "success": False, "error": "Inventory inconsistent: player holds less items than being rolled back." }

        # --- Atomic block starts ---
        # Refund currency
        self.players[player_id]["currency_balance"][currency] += amount_spent
        # Remove items from inventory
        self.inventory[player_id][item_id] -= quantity
        if self.inventory[player_id][item_id] == 0:
            del self.inventory[player_id][item_id]
            # If player's inventory is empty, optionally clean up (not required)
        # Remove purchase record
        del self.purchase_records[purchase_id]
        # --- Atomic block ends ---

        return { "success": True, "message": "Purchase rollback successful." }

    def remove_item_from_inventory(self, player_id: str, item_id: str, quantity: int = 1) -> dict:
        """
        Delete or decrement an item in a player's inventory.

        Args:
            player_id (str): The player's ID to update inventory for.
            item_id (str): The item ID to be removed or decremented.
            quantity (int, optional): How many to remove (default: 1).

        Returns:
            dict: {
                "success": True,
                "message": "Item removed from inventory"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - player_id must exist and have the item in their inventory.
            - Item's current quantity must be >= quantity to remove, and quantity must be positive.
            - If quantity becomes zero after removal, remove the item entry for that player.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        if item_id not in self.items:
            return { "success": False, "error": "Item does not exist" }
        if player_id not in self.inventory or item_id not in self.inventory[player_id]:
            return { "success": False, "error": "Player does not own this item" }
        if not isinstance(quantity, int) or quantity <= 0:
            return { "success": False, "error": "Quantity must be a positive integer" }

        current_quantity = self.inventory[player_id][item_id]
        if quantity > current_quantity:
            return { "success": False, "error": "Quantity to remove exceeds owned amount" }

        if quantity == current_quantity:
            del self.inventory[player_id][item_id]
            # Clean up if no more items for this player
            if not self.inventory[player_id]:
                del self.inventory[player_id]
            return { "success": True, "message": f"All of item '{item_id}' removed from player '{player_id}' inventory" }
        else:
            self.inventory[player_id][item_id] -= quantity
            return { "success": True, "message": f"Decremented item '{item_id}' by {quantity} for player '{player_id}'" }


class OnlineGameItemInventorySystem(BaseEnv):
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

    def get_player_info(self, **kwargs):
        return self._call_inner_tool('get_player_info', kwargs)

    def get_item_by_name(self, **kwargs):
        return self._call_inner_tool('get_item_by_name', kwargs)

    def get_item_info(self, **kwargs):
        return self._call_inner_tool('get_item_info', kwargs)

    def get_player_inventory(self, **kwargs):
        return self._call_inner_tool('get_player_inventory', kwargs)

    def check_item_ownership(self, **kwargs):
        return self._call_inner_tool('check_item_ownership', kwargs)

    def get_game_info(self, **kwargs):
        return self._call_inner_tool('get_game_info', kwargs)

    def check_item_game_compatibility(self, **kwargs):
        return self._call_inner_tool('check_item_game_compatibility', kwargs)

    def get_currency_balance(self, **kwargs):
        return self._call_inner_tool('get_currency_balance', kwargs)

    def get_item_price(self, **kwargs):
        return self._call_inner_tool('get_item_price', kwargs)

    def get_currency_info(self, **kwargs):
        return self._call_inner_tool('get_currency_info', kwargs)

    def get_purchase_history(self, **kwargs):
        return self._call_inner_tool('get_purchase_history', kwargs)

    def purchase_item(self, **kwargs):
        return self._call_inner_tool('purchase_item', kwargs)

    def update_player_inventory(self, **kwargs):
        return self._call_inner_tool('update_player_inventory', kwargs)

    def update_currency_balance(self, **kwargs):
        return self._call_inner_tool('update_currency_balance', kwargs)

    def record_purchase(self, **kwargs):
        return self._call_inner_tool('record_purchase', kwargs)

    def rollback_transaction(self, **kwargs):
        return self._call_inner_tool('rollback_transaction', kwargs)

    def remove_item_from_inventory(self, **kwargs):
        return self._call_inner_tool('remove_item_from_inventory', kwargs)

