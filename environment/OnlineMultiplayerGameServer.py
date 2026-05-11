# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict
import time



class PlayerInfo(TypedDict):
    player_id: str
    username: str
    profile_data: Any
    currency_balance: float
    inventory: List[str]  # list of item ids (m_id)
    progress: Any
    login_status: str
    last_sync_tim: str  # or float, depending on implementation

class ItemInfo(TypedDict):
    m_id: str
    item_type: str
    item_prop: Any

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for online multiplayer game server managing players and items.
        """

        # Players: {player_id: PlayerInfo}
        #   - Attributes: player_id, username, profile_data, currency_balance,
        #     inventory, progress, login_status, last_sync_tim
        self.players: Dict[str, PlayerInfo] = {}

        # Items: {m_id: ItemInfo}
        #   - Attributes: m_id, item_type, item_prop
        self.items: Dict[str, ItemInfo] = {}

        # Constraints:
        # - Each player must have a unique player_id.
        # - Virtual currency balances cannot be negative.
        # - Player inventory can only contain items that exist in the item catalog.
        # - Player progress must only increment or change by valid in-game actions.
        # - All player state-affecting actions must be validated/synchronized to prevent cheating or state corruption.

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve the complete profile and game-related information for a given player by their unique player_id.

        Args:
            player_id (str): The unique ID of the player.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": PlayerInfo  # The full info for the player
                  }
                - On failure: {
                      "success": False,
                      "error": "Player not found"
                  }

        Constraints:
            - The player_id must exist in the server.
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player}

    def get_player_by_username(self, username: str) -> dict:
        """
        Retrieve a player's information given their username.

        Args:
            username (str): The username of the player to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo
            }
            or
            {
                "success": False,
                "error": str  # e.g. player not found
            }

        Constraints:
            - The username should match exactly.
            - If no such player exists, return success=False.
        """
        for player in self.players.values():
            if player["username"] == username:
                return { "success": True, "data": player }
        return { "success": False, "error": "Player with this username does not exist" }

    def get_all_players(self) -> dict:
        """
        List all registered players on the server.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo],  # List of all players' info (empty list if no players)
            }

        Constraints:
            - No parameters are required.
            - Returns all players currently registered in the server.
        """
        players_list = list(self.players.values())
        return { "success": True, "data": players_list }

    def get_player_currency_balance(self, player_id: str) -> dict:
        """
        Fetch the virtual currency balance for a specific player.

        Args:
            player_id (str): Unique identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": float  # player's virtual currency balance
            }
            or
            {
                "success": False,
                "error": str  # "Player not found"
            }

        Constraints:
            - player_id must exist in the system.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player not found" }
        return { "success": True, "data": player["currency_balance"] }

    def get_player_inventory(self, player_id: str) -> dict:
        """
        List all item IDs currently owned by a specific player.

        Args:
            player_id (str): The unique identifier of the player to query.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": List[str]  # List of item IDs (may be empty).
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Error message (e.g., player does not exist).
                    }

        Constraints:
            - The player with the given ID must exist.
        """
        player = self.players.get(player_id)
        if not player:
            return { "success": False, "error": "Player does not exist" }

        inventory = player.get("inventory", [])
        return { "success": True, "data": list(inventory) }

    def get_player_progress(self, player_id: str) -> dict:
        """
        Retrieve the progress or achievements of a player.

        Args:
            player_id (str): Unique identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": Any              # The progress information of the player.
            }
            or
            {
                "success": False,
                "error": str            # Reason for error, e.g., player not found.
            }

        Constraints:
            - player_id must exist in the server.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player not found" }
        return { "success": True, "data": player["progress"] }

    def get_player_login_status(self, player_id: str) -> dict:
        """
        Check whether the player is currently logged in.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str    # Login status (e.g., "online", "offline", etc.)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Player not found"
                    }
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player not found"}

        return {"success": True, "data": player["login_status"]}

    def get_player_last_sync_time(self, player_id: str) -> dict:
        """
        Get the last synchronization timestamp for a player.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                - {"success": True, "data": last_sync_tim}
                    If the player exists; last_sync_tim is typically a string or float timestamp.
                - {"success": False, "error": "Player does not exist"}
                    If the player_id is not found in the server.

        Constraints:
            - player_id must exist within self.players.
        """
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player does not exist"}

        return {"success": True, "data": player["last_sync_tim"]}

    def get_item_by_id(self, m_id: str) -> dict:
        """
        Retrieve full information about a specific item (type and properties) in the item catalog.

        Args:
            m_id (str): The unique identifier of the item.

        Returns:
            dict: {
                "success": True,
                "data": ItemInfo
            }
            or
            {
                "success": False,
                "error": str  # If item does not exist
            }

        Constraints:
            - m_id must exist in the item catalog (self.items).
        """
        if m_id not in self.items:
            return { "success": False, "error": "Item does not exist" }
        return { "success": True, "data": self.items[m_id] }

    def get_all_items(self) -> dict:
        """
        Retrieve the full item catalog currently available in the game.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ItemInfo]  # All items in the catalog (empty if none)
            }

        Constraints:
            - No constraints directly affect this query operation.
        """
        result = list(self.items.values())
        return {"success": True, "data": result}

    def check_item_exists(self, m_id: str) -> dict:
        """
        Verify if a given item id exists in the system’s item catalog.

        Args:
            m_id (str): The item id to check.

        Returns:
            dict: {
                "success": True,
                "data": { "exists": bool }  # True if item exists, False otherwise
            }
            If m_id is invalid (not string or empty), exists will be False.

        Constraints:
            - No state change; just check existence.
        """
        if not isinstance(m_id, str) or not m_id:
            # Invalid id treated as not existing
            return { "success": True, "data": { "exists": False } }
        exists = m_id in self.items
        return { "success": True, "data": { "exists": exists } }

    def update_player_currency_balance(self, player_id: str, amount: float) -> dict:
        """
        Add to or subtract from a player’s virtual currency, ensuring the result is non-negative.

        Args:
            player_id (str): Unique player identifier.
            amount (float): Amount to add (positive) or subtract (negative) from the player's currency.

        Returns:
            dict: {
                "success": True,
                "message": "Player currency updated. New balance: <balance>"
            }
            or
            {
                "success": False,
                "error": <string describing error>
            }

        Constraints:
            - The player must exist.
            - The resulting currency balance cannot be negative.
        """
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player does not exist."}

        new_balance = player["currency_balance"] + amount
        if new_balance < 0:
            return {"success": False, "error": "Operation would result in negative currency balance."}

        player["currency_balance"] = new_balance
        return {
            "success": True,
            "message": f"Player currency updated. New balance: {new_balance}"
        }

    def add_item_to_inventory(self, player_id: str, item_id: str) -> dict:
        """
        Add a specific item (item_id) to a player's (player_id) inventory if the item exists in the catalog.

        Args:
            player_id (str): The unique identifier of the player.
            item_id (str): The unique identifier of the item to add (m_id).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Item added to inventory"}
                On failure:
                    {"success": False, "error": reason}

        Constraints:
            - The player_id must exist in the system.
            - The item_id must exist in the item catalog.
            - Inventory can only contain items that exist in the catalog.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }
        if item_id not in self.items:
            return { "success": False, "error": "Item not found in catalog" }
    
        # Add to player's inventory (assume duplicates are allowed)
        self.players[player_id]["inventory"].append(item_id)
    
        # Validate postcondition: Inventory items are all in catalog (should always be True here)
        for iid in self.players[player_id]["inventory"]:
            if iid not in self.items:
                return {
                    "success": False,
                    "error": "Inventory contains invalid item(s) after addition (state corruption)"
                }

        return { "success": True, "message": "Item added to inventory" }

    def remove_item_from_inventory(self, player_id: str, m_id: str) -> dict:
        """
        Remove a specified item (by m_id) from a player's inventory.

        Args:
            player_id (str): Unique identifier of the player.
            m_id (str): Unique identifier of the item to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Item <m_id> removed from player <player_id> inventory."
            }
            or
            {
                "success": False,
                "error": "<error description>"
            }

        Constraints:
            - Player must exist.
            - Item must exist in the player's current inventory.
            - After removal, the player's inventory must only contain item ids present in the item catalog.
        """
        # Check whether player exists
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}

        player = self.players[player_id]

        # Check item existence in player inventory
        if m_id not in player["inventory"]:
            return {"success": False, "error": "Item not found in player's inventory."}

        # Remove the item (remove only the first occurrence)
        player["inventory"].remove(m_id)

        # Optional: Validate remaining inventory items are all still valid
        catalog_ids = set(self.items.keys())
        for inv_item in player["inventory"]:
            if inv_item not in catalog_ids:
                return {
                    "success": False,
                    "error": "Player inventory has invalid item(s) after removal. State possibly corrupted."
                }

        # Update in players dict (in case further logic is attached)
        self.players[player_id] = player

        return {
            "success": True,
            "message": f"Item {m_id} removed from player {player_id} inventory."
        }

    def update_player_progress(self, player_id: str, progress_update: Any) -> dict:
        """
        Update or increment a player’s progress according to valid in-game actions.

        Args:
            player_id (str): The unique identifier of the player.
            progress_update (Any): The update or increment to apply. Expected type/logic
                depends on the game's progress model (e.g., numeric, dict of levels, etc.).

        Returns:
            dict: { "success": True, "message": str }
                  or
                  { "success": False, "error": str }

        Constraints:
            - Progress must only increment or change by valid in-game actions.
            - No progress regression allowed.
            - Player must exist.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player does not exist." }

        # Accept stringified JSON for compatibility with models that wrap
        # object/number updates in a JSON string, but normalize to native types.
        if isinstance(progress_update, str):
            stripped = progress_update.strip()
            if stripped:
                try:
                    parsed_update = json.loads(stripped)
                except Exception:
                    parsed_update = None
                else:
                    if isinstance(parsed_update, (dict, int, float)) and not isinstance(parsed_update, bool):
                        progress_update = parsed_update

        current_progress = player.get("progress")
        # Numeric progress (e.g. level, integer/float): Only allow increment
        if isinstance(current_progress, (int, float)) and isinstance(progress_update, (int, float)):
            if progress_update < current_progress:
                return { "success": False, "error": "Progress regression is not allowed." }
            player["progress"] = progress_update
            return { "success": True, "message": "Player progress updated." }

        # Dictionary progress (e.g., levels: {"level": 5, "xp": 230})
        if isinstance(current_progress, dict) and isinstance(progress_update, dict):
            # Only allow updates that increment each key or add new keys
            updated = current_progress.copy()
            for k, v in progress_update.items():
                old_v = current_progress.get(k)
                if old_v is not None and isinstance(old_v, (int, float)) and isinstance(v, (int, float)):
                    if v < old_v:
                        return { "success": False, "error": f"Progress key '{k}' regression is not allowed." }
                updated[k] = v
            player["progress"] = updated
            return { "success": True, "message": "Player progress updated." }

        # If custom structure: only allow replacing if not regressing (generic fallback)
        if current_progress == progress_update:
            return { "success": True, "message": "Player progress unchanged." }
        else:
            # Last-resort: allow updating if not decreasing (or avoid if not comparable)
            # To be safe, refuse unknown types/invalid structures
            return { "success": False, "error": "Invalid or unsupported progress update structure." }


    def player_login(self, player_id: str) -> dict:
        """
        Sets the player's login status to 'logged in' and updates their last_sync_tim to the current time.

        Args:
            player_id (str): The unique identifier of the player to log in.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> is now logged in"
            }
            or
            {
                "success": False,
                "error": str  # Error message if player not found
            }

        Constraints:
            - The player must exist in the server.
            - Updates login_status to "logged in" and last_sync_tim to the current time.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }

        self.players[player_id]["login_status"] = "logged in"
        self.players[player_id]["last_sync_tim"] = time.time()
        return { "success": True, "message": f"Player {player_id} is now logged in" }


    def player_logout(self, player_id: str) -> dict:
        """
        Set a player's login status to 'logged out' and update last_sync_tim.

        Args:
            player_id (str): The unique ID of the player to log out.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> logged out and sync time updated"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Player must exist.
            - Updates player['login_status'] to 'logged out' (idempotent).
            - Updates player['last_sync_tim'] to the current timestamp (float).
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player does not exist"}

        player["login_status"] = "logged out"
        player["last_sync_tim"] = time.time()

        return {
            "success": True,
            "message": f"Player {player_id} logged out and sync time updated"
        }

    def synchronize_player_state(self, player_id: str) -> dict:
        """
        Commit and validate all recent changes to a player's state atomically.

        Args:
            player_id (str): The unique ID of the player to synchronize.

        Returns:
            dict: {
                "success": True,
                "message": "Player state synchronized successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for synchronization failure.
            }

        Constraints:
            - The player must exist.
            - The currency balance must not be negative.
            - All items in inventory must exist in the item catalog.
            - Synchronization is atomic; if validation fails, no partial update occurs.
            - Updates last_sync_tim to current time.
        """

        player = self.players.get(player_id)
        if not player:
            return { "success": False, "error": "Player does not exist." }

        # Validate currency balance
        if player.get("currency_balance", 0) < 0:
            return { "success": False, "error": "Currency balance cannot be negative." }

        # Validate inventory
        inventory = player.get("inventory", [])
        invalid_items = [iid for iid in inventory if iid not in self.items]
        if invalid_items:
            return {
                "success": False,
                "error": f"Inventory contains items not in catalog: {invalid_items}"
            }

        # Progress validation is intentionally left to the stored specification when provided.

        # Simulate atomic commit by updating last_sync_tim as final step
        player["last_sync_tim"] = time.time()

        # Save committed state (no intermediate updates needed for atomicity in this model)
        self.players[player_id] = player

        return {
            "success": True,
            "message": "Player state synchronized successfully."
        }

    def create_player(
        self,
        player_id: str,
        username: str,
        profile_data: Any,
        initial_currency: float = 0.0,
        initial_inventory: list = None,
        initial_progress: Any = None,
        login_status: str = "offline",
        last_sync_tim: str = "",
    ) -> dict:
        """
        Add a new player with a unique player_id to the system.

        Args:
            player_id (str): Unique player identifier.
            username (str): Player's username.
            profile_data (Any): Miscellaneous profile data.
            initial_currency (float, optional): Initial virtual currency balance (defaults to 0.0). Must not be negative.
            initial_inventory (list, optional): Initial inventory as list of item IDs (defaults to empty list).
            initial_progress (Any, optional): Initial player progress (defaults to None/empty).
            login_status (str, optional): Player's initial login status (defaults to "offline").
            last_sync_tim (str, optional): Initial last sync time (defaults to empty string).

        Returns:
            dict:
                - success (bool): Whether the player was created.
                - message (str): On success, success message.
                - error (str): On failure, reason for failure.

        Constraints:
            - player_id must be unique.
            - Virtual currency balance cannot be negative.
            - Inventory must only contain items in the item catalog (for initial inventory).
        """
        # Check for unique player_id
        if player_id in self.players:
            return {"success": False, "error": "Player with this player_id already exists."}
        # Currency cannot be negative
        if initial_currency < 0:
            return {"success": False, "error": "Currency balance cannot be negative."}
        # Inventory validation
        if initial_inventory is None:
            initial_inventory = []
        else:
            # Check if every item in initial_inventory exists in the item catalog
            missing_items = [iid for iid in initial_inventory if iid not in self.items]
            if missing_items:
                return {"success": False, "error": f"Inventory contains invalid item IDs: {missing_items}"}

        # Populate the player's info
        player_info: PlayerInfo = {
            "player_id": player_id,
            "username": username,
            "profile_data": profile_data,
            "currency_balance": initial_currency,
            "inventory": initial_inventory,
            "progress": initial_progress if initial_progress is not None else {},
            "login_status": login_status,
            "last_sync_tim": last_sync_tim,
        }
        self.players[player_id] = player_info
        return {"success": True, "message": f"Player {player_id} created successfully."}

    def delete_player(self, player_id: str) -> dict:
        """
        Remove a player (and all persistent data) from the game system.

        Args:
            player_id (str): The unique ID of the player to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Player not found."
            }

        Constraints:
            - player_id must exist in the system.
            - This is an admin operation; no permission checks required here.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found." }

        del self.players[player_id]
        return { "success": True, "message": f"Player {player_id} deleted." }

    def update_item_in_catalog(self, m_id: str, item_type: str = None, item_prop: Any = None) -> dict:
        """
        Edit properties of an item in the item catalog (admin/developer operation).

        Args:
            m_id (str): The unique item id to update (must already exist).
            item_type (str, optional): New item type (if updating).
            item_prop (Any, optional): New item properties (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Item updated"
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The item must exist in the catalog.
            - At least one of item_type or item_prop must be provided.
            - It is not allowed to update m_id itself.
        """
        # Existence check
        if m_id not in self.items:
            return {"success": False, "error": "Item does not exist in the catalog."}

        # Nothing to update
        if item_type is None and item_prop is None:
            return {"success": False, "error": "No update data provided (item_type or item_prop required)."}

        # Perform update
        item = self.items[m_id]
        updated_fields = []
        if item_type is not None:
            item["item_type"] = item_type
            updated_fields.append("item_type")
        if item_prop is not None:
            item["item_prop"] = item_prop
            updated_fields.append("item_prop")
        self.items[m_id] = item
        return {
            "success": True,
            "message": f"Item {m_id} updated ({', '.join(updated_fields)})"
        }

    def add_item_to_catalog(self, m_id: str, item_type: str, item_prop: Any) -> dict:
        """
        Add a new item to the canonical item catalog.

        Args:
            m_id (str): The unique item id.
            item_type (str): The type/category of the item.
            item_prop (Any): Additional properties of the item.

        Returns:
            dict: {
                "success": True,
                "message": "Item added to catalog"
            }
            or
            {
                "success": False,
                "error": "Item with this m_id already exists"
            }

        Constraints:
            - m_id must be unique in the item catalog.
        """
        if not m_id or m_id in self.items:
            return {
                "success": False,
                "error": "Item with this m_id already exists"
            }

        self.items[m_id] = {
            "m_id": m_id,
            "item_type": item_type,
            "item_prop": item_prop
        }

        return {
            "success": True,
            "message": "Item added to catalog"
        }

    def remove_item_from_catalog(self, m_id: str) -> dict:
        """
        Remove an item from the item catalog. This prevents future acquisition of this item,
        but does not affect any existing instances of the item in player inventories.

        Args:
            m_id (str): Unique ID of the item to remove.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Item <m_id> removed from catalog" }
                - On failure: { "success": False, "error": "Item does not exist in catalog" }

        Constraints:
            - Only existing catalog items may be removed.
            - Does not remove item from any player inventory.
        """
        if m_id not in self.items:
            return { "success": False, "error": "Item does not exist in catalog" }
    
        del self.items[m_id]
        return { "success": True, "message": f"Item {m_id} removed from catalog" }


class OnlineMultiplayerGameServer(BaseEnv):
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

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_player_by_username(self, **kwargs):
        return self._call_inner_tool('get_player_by_username', kwargs)

    def get_all_players(self, **kwargs):
        return self._call_inner_tool('get_all_players', kwargs)

    def get_player_currency_balance(self, **kwargs):
        return self._call_inner_tool('get_player_currency_balance', kwargs)

    def get_player_inventory(self, **kwargs):
        return self._call_inner_tool('get_player_inventory', kwargs)

    def get_player_progress(self, **kwargs):
        return self._call_inner_tool('get_player_progress', kwargs)

    def get_player_login_status(self, **kwargs):
        return self._call_inner_tool('get_player_login_status', kwargs)

    def get_player_last_sync_time(self, **kwargs):
        return self._call_inner_tool('get_player_last_sync_time', kwargs)

    def get_item_by_id(self, **kwargs):
        return self._call_inner_tool('get_item_by_id', kwargs)

    def get_all_items(self, **kwargs):
        return self._call_inner_tool('get_all_items', kwargs)

    def check_item_exists(self, **kwargs):
        return self._call_inner_tool('check_item_exists', kwargs)

    def update_player_currency_balance(self, **kwargs):
        return self._call_inner_tool('update_player_currency_balance', kwargs)

    def add_item_to_inventory(self, **kwargs):
        return self._call_inner_tool('add_item_to_inventory', kwargs)

    def remove_item_from_inventory(self, **kwargs):
        return self._call_inner_tool('remove_item_from_inventory', kwargs)

    def update_player_progress(self, **kwargs):
        return self._call_inner_tool('update_player_progress', kwargs)

    def player_login(self, **kwargs):
        return self._call_inner_tool('player_login', kwargs)

    def player_logout(self, **kwargs):
        return self._call_inner_tool('player_logout', kwargs)

    def synchronize_player_state(self, **kwargs):
        return self._call_inner_tool('synchronize_player_state', kwargs)

    def create_player(self, **kwargs):
        return self._call_inner_tool('create_player', kwargs)

    def delete_player(self, **kwargs):
        return self._call_inner_tool('delete_player', kwargs)

    def update_item_in_catalog(self, **kwargs):
        return self._call_inner_tool('update_item_in_catalog', kwargs)

    def add_item_to_catalog(self, **kwargs):
        return self._call_inner_tool('add_item_to_catalog', kwargs)

    def remove_item_from_catalog(self, **kwargs):
        return self._call_inner_tool('remove_item_from_catalog', kwargs)
