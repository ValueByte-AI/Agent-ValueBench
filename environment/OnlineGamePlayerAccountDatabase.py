# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class PlayerInfo(TypedDict):
    player_id: str
    username: str
    email: str
    profile_info: str
    account_status: str  # inferred from account_sta

class CurrencyBalanceInfo(TypedDict):
    player_id: str
    coins: int
    gem: int

class InventoryInfo(TypedDict):
    player_id: str
    item_id: str
    quantity: int

class AchievementInfo(TypedDict):
    player_id: str
    achievement_id: str
    achieved_at: str  # inferred from achieved_a

class ProgressionInfo(TypedDict):
    player_id: str
    level: int
    experience_points: int
    last_login: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Online game player account database environment initializer.
        """

        # Maps player_id → PlayerInfo (core profile)
        self.players: Dict[str, PlayerInfo] = {}
        # Maps player_id → CurrencyBalanceInfo (coins/gems)
        self.currency_balances: Dict[str, CurrencyBalanceInfo] = {}
        # Maps player_id → List of InventoryInfo (items/quantities)
        self.inventories: Dict[str, List[InventoryInfo]] = {}
        # Maps player_id → List of AchievementInfo (achievements unlocked)
        self.achievements: Dict[str, List[AchievementInfo]] = {}
        # Maps player_id → ProgressionInfo (progression metrics)
        self.progressions: Dict[str, ProgressionInfo] = {}

        # Constraints:
        # - Currency balances (coins, gem) cannot be negative.
        # - Each player_id is unique across all entities.
        # - Only existing, valid items may be added to a player's inventory.
        # - Achievements can only be recorded once per player.
        # - Progression must update according to game-defined rules (e.g., XP thresholds for leveling up).
        self.current_time = "2023-10-26T12:00:00Z"
        self.item_validation_flag = None

    @staticmethod
    def _parse_bool_like(value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "active", "enabled"}:
                return True
            if lowered in {"0", "false", "no", "off", "inactive", "disabled"}:
                return False
        return None

    def _get_master_items(self) -> Any:
        raw = getattr(self, "master_items", None)
        if raw is None:
            return None
        if isinstance(raw, str):
            return {
                item.strip()
                for item in raw.split(",")
                if item and item.strip()
            }
        if isinstance(raw, dict):
            return {str(item_id).strip() for item_id in raw.keys() if str(item_id).strip()}
        if isinstance(raw, (list, tuple, set)):
            return {str(item_id).strip() for item_id in raw if str(item_id).strip()}
        return None

    def _validate_item_id(self, item_id: str) -> dict:
        master_items = self._get_master_items()
        if master_items is not None:
            return {"success": True, "data": item_id in master_items}

        flag = self._parse_bool_like(getattr(self, "item_validation_flag", None))
        if flag is not None:
            return {"success": True, "data": flag}

        return {"success": False, "error": "Master item list not available"}

    def _get_current_time_iso(self) -> str:
        raw = getattr(self, "current_time", None)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return "2023-10-26T12:00:00Z"

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve the player profile and core identification info by player_id.

        Args:
            player_id (str): The unique identifier of a player.

        Returns:
            dict:
                success: True and data key with PlayerInfo if found,
                         False and error key if not found.

        Constraints:
            - player_id must exist in self.players.
        """
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player}

    def get_player_by_username(self, username: str) -> dict:
        """
        Retrieve a player's profile information using their username.

        Args:
            username (str): The username of the player to look up.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo   # Player profile as a dictionary
            }
            or
            {
                "success": False,
                "error": str   # Reason for failure, e.g., player not found
            }

        Constraints:
            - Usernames are assumed to be unique in the player database.
            - If not found, return an error.
        """
        if not username:
            return { "success": False, "error": "Username cannot be empty" }
        for player in self.players.values():
            if player["username"] == username:
                return { "success": True, "data": player }
        return { "success": False, "error": "Player not found" }

    def list_all_players(self) -> dict:
        """
        Get a list of all registered players.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo],  # List of all player information (may be empty)
            }

        Constraints:
            - None (no parameter, read-only listing).
        """
        all_players = list(self.players.values())
        return { "success": True, "data": all_players }

    def check_player_account_status(self, player_id: str) -> dict:
        """
        Check the current account status of a player.

        Args:
            player_id (str): The unique ID of the player.

        Returns:
            dict: {
                "success": True,
                "data": str  # The player's account status
            }
            or
            {
                "success": False,
                "error": str  # Error message if player not found or status missing
            }

        Constraints:
            - The player_id must exist in the system.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player not found" }
        status = player.get("account_status")
        if status is None:
            return { "success": False, "error": "Account status not available" }
        return { "success": True, "data": status }

    def get_currency_balance(self, player_id: str) -> dict:
        """
        Query the current coin and gem balances for a given player_id.

        Args:
            player_id (str): Unique identifier for the player.

        Returns:
            dict:
                - success: True, and data with the player's coin and gem amounts, if found.
                - success: False, and error message if player or currency balance not found.

        Constraints:
            - Only existing players with an active currency balance record can be queried.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }

        currency_info = self.currency_balances.get(player_id)
        if not currency_info:
            return { "success": False, "error": "Currency balance record not found for the player" }

        return { "success": True, "data": {
            "player_id": currency_info["player_id"],
            "coins": currency_info["coins"],
            "gem": currency_info["gem"],
        }}

    def get_inventory(self, player_id: str) -> dict:
        """
        Retrieve the entire inventory for a given player by player_id.

        Args:
            player_id (str): The unique player identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryInfo],  # list of inventory items with quantities (may be empty if no inventory)
            }
            or
            {
                "success": False,
                "error": str  # e.g., player does not exist
            }

        Constraints:
            - player_id must exist in the database.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        # Retrieve inventory or default to an empty list if none exist
        inventory_list = self.inventories.get(player_id, [])

        return {"success": True, "data": inventory_list}

    def get_achievements(self, player_id: str) -> dict:
        """
        List all achievements unlocked by the player with corresponding timestamps.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[AchievementInfo]
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - The player must exist (player_id in self.players).
        """

        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}

        achievements = self.achievements.get(player_id, [])
        return {"success": True, "data": achievements}

    def get_progression(self, player_id: str) -> dict:
        """
        Retrieve progression info for a player, including level, experience points, and last login timestamp.

        Args:
            player_id (str): The unique player identifier.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": ProgressionInfo  # Progression details for the player
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason, e.g. "Player not found"
                }

        Constraints:
            - player_id must exist in the database.
        """
        progression = self.progressions.get(player_id)
        if not progression:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": progression}

    def is_item_valid(self, item_id: str) -> dict:
        """
        Check if an item_id exists in the master item list (used for validation before inventory operations).

        Args:
            item_id (str): The identifier of the item to validate.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True if item_id is valid (exists in master list), False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure, e.g., master item list unavailable
            }

        Constraints:
            - Only existing, valid items may be added to player's inventory.
            - If master item list is unavailable, operation should fail gracefully.
        """
        return self._validate_item_id(item_id)

    def has_achievement(self, player_id: str, achievement_id: str) -> dict:
        """
        Check if a player has already unlocked a particular achievement.

        Args:
            player_id (str): Unique player identifier.
            achievement_id (str): The achievement's unique identifier.

        Returns:
            dict: {
                "success": True,
                "has_achievement": bool  # True if unlocked, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., player not found
            }

        Constraints:
            - The player must exist in the database.
            - Achievements are unique per player and can be checked by scanning the player's achievement list.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        player_achievements = self.achievements.get(player_id, [])
        for ach in player_achievements:
            if ach["achievement_id"] == achievement_id:
                return { "success": True, "has_achievement": True }
        return { "success": True, "has_achievement": False }

    def get_players_by_level_range(self, min_level: int, max_level: int, return_profiles: bool = False) -> dict:
        """
        Retrieve list of player_ids (or full profiles if return_profiles is True) for players whose level
        is in the inclusive range [min_level, max_level].

        Args:
            min_level (int): lower bound (inclusive) of the level range (must be >=0)
            max_level (int): upper bound (inclusive) of the level range (must be >=0)
            return_profiles (bool, optional): if True, return player profiles; else, just player_ids

        Returns:
            dict: {
                "success": True,
                "data": List[str] or List[PlayerInfo],  # player_ids or PlayerInfo list
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - min_level and max_level must be integers >= 0, and min_level <= max_level
        """
        if not (isinstance(min_level, int) and isinstance(max_level, int)):
            return {"success": False, "error": "Levels must be integers."}
        if min_level < 0 or max_level < 0:
            return {"success": False, "error": "Levels cannot be negative."}
        if min_level > max_level:
            return {"success": False, "error": "Invalid level range: min_level is greater than max_level."}

        matching_ids = [
            pid for pid, prog in self.progressions.items()
            if prog["level"] >= min_level and prog["level"] <= max_level
        ]
        if return_profiles:
            data = [self.players[pid] for pid in matching_ids if pid in self.players]
        else:
            data = matching_ids

        return {"success": True, "data": data}

    def list_inventory_items_for_player(self, player_id: str) -> dict:
        """
        List all item_ids present in the player's inventory.

        Args:
            player_id (str): The player to query.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # list of item_ids owned by the player, may be empty
            }
            OR
            {
                "success": False,
                "error": str  # Player does not exist
            }

        Constraints:
            - player_id must refer to an existing player.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        inventory = self.inventories.get(player_id, [])
        item_ids = [entry["item_id"] for entry in inventory]
        # The same item_id may appear more than once (should it be unique?). We'll deduplicate to give unique items.
        item_ids_unique = list(set(item_ids))

        return { "success": True, "data": item_ids_unique }

    def update_currency_balance(self, player_id: str, coins_delta: int, gem_delta: int) -> dict:
        """
        Update the currency balances (coins/gems) for a player by adding or subtracting amounts.

        Args:
            player_id (str): The target player's unique ID.
            coins_delta (int): Signed amount to add/subtract from the player's coins.
            gem_delta (int): Signed amount to add/subtract from the player's gems.

        Returns:
            dict: { "success": True, "message": "Currency balances updated." }
                  OR
                  { "success": False, "error": "<reason>" }

        Constraints:
            - Player must exist.
            - Resulting coins and gems must not be negative.
            - Each player's balances are stored in self.currency_balances[player_id].
        """
        if player_id not in self.currency_balances:
            return { "success": False, "error": "Player not found." }

        cb = self.currency_balances[player_id]
        new_coins = cb["coins"] + coins_delta
        new_gem = cb["gem"] + gem_delta

        if new_coins < 0 or new_gem < 0:
            return {
                "success": False,
                "error": "Insufficient balance: currency balances cannot be negative."
            }

        cb["coins"] = new_coins
        cb["gem"] = new_gem
        self.currency_balances[player_id] = cb
        return { "success": True, "message": "Currency balances updated." }

    def add_inventory_item(self, player_id: str, item_id: str, quantity: int) -> dict:
        """
        Add a valid item to a player's inventory or update its quantity.
    
        Args:
            player_id (str): ID of the player
            item_id (str): ID of the item to add/update
            quantity (int): Amount of the item to add (can be >0 or <0, but final quantity cannot be negative).
    
        Returns:
            dict: On success:
                { "success": True, "message": "Item <item_id> added/updated in inventory for player <player_id>." }
            On failure:
                { "success": False, "error": "<reason>" }
    
        Constraints:
            - Player must exist.
            - Item must be valid.
            - Resulting item quantity in inventory must not be negative.
        """
        # Check player exists
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist." }

        # Check item validity
        valid_item_result = self._validate_item_id(item_id)
        if not valid_item_result.get("success") or not valid_item_result.get("data", False):
            return { "success": False, "error": "Item does not exist or is invalid." }
    
        # Get or create inventory list for player
        inventory = self.inventories.setdefault(player_id, [])
        # Search for item in inventory
        for entry in inventory:
            if entry["item_id"] == item_id:
                new_quantity = entry["quantity"] + quantity
                if new_quantity < 0:
                    return { "success": False, "error": "Cannot set item quantity below zero." }
                entry["quantity"] = new_quantity
                return { "success": True, "message": f"Item {item_id} updated in inventory for player {player_id}." }
    
        # Item not in inventory yet
        if quantity < 0:
            return { "success": False, "error": "Cannot add item with negative quantity." }
        if quantity == 0:
            return { "success": True, "message": f"Item {item_id} not added (quantity zero) for player {player_id}." }
        new_entry = {
            "player_id": player_id,
            "item_id": item_id,
            "quantity": quantity
        }
        inventory.append(new_entry)
        return { "success": True, "message": f"Item {item_id} added to inventory for player {player_id}." }

    def remove_inventory_item(self, player_id: str, item_id: str, quantity: int) -> dict:
        """
        Remove or decrease the quantity of a specific item from the player's inventory.

        Args:
            player_id (str): The unique player whose inventory is to be updated.
            item_id (str): The ID of the item to remove or decrease.
            quantity (int): How many units to remove (must be > 0).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "..."}
                On failure:
                    {"success": False, "error": "..."}
        Constraints:
            - player_id must exist.
            - item_id must exist in the player's inventory.
            - quantity must be positive.
            - If resulting quantity <= 0, item is removed from inventory.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}
        if quantity <= 0:
            return {"success": False, "error": "Quantity to remove must be positive."}
        # Ensure player has an inventory
        inventory = self.inventories.get(player_id, [])
        for idx, inv in enumerate(inventory):
            if inv["item_id"] == item_id:
                if inv["quantity"] < quantity:
                    return {"success": False, "error": "Player does not have enough quantity of the item to remove."}
                elif inv["quantity"] == quantity:
                    # Remove entire item
                    del inventory[idx]
                    self.inventories[player_id] = inventory  # update explicitly
                    return {"success": True, "message": f"Item {item_id} removed from player {player_id}'s inventory."}
                else:
                    inv["quantity"] -= quantity
                    self.inventories[player_id] = inventory  # update explicitly
                    return {"success": True, "message": f"Item {item_id} quantity reduced by {quantity} for player {player_id}."}
        # Item not found
        return {"success": False, "error": "Item not found in player's inventory."}

    def add_achievement(self, player_id: str, achievement_id: str, achieved_at: str) -> dict:
        """
        Add an achievement record for a player, ensuring uniqueness.

        Args:
            player_id (str): The unique identifier of the player.
            achievement_id (str): The identifier for the achievement.
            achieved_at (str): Timestamp when the achievement is unlocked (ISO format string).

        Returns:
            dict: 
              - If successful:
                  {
                    "success": True,
                    "message": "Achievement added for player."
                  }
              - On failure (player missing or achievement exists):
                  {
                    "success": False,
                    "error": "<reason>"
                  }
        Constraints:
            - Only existing players can have achievements added.
            - Each (player_id, achievement_id) pair must be unique.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        if player_id not in self.achievements:
            self.achievements[player_id] = []

        for ach in self.achievements[player_id]:
            if ach["achievement_id"] == achievement_id:
                return { "success": False, "error": "Player already has this achievement" }

        new_achievement = {
            "player_id": player_id,
            "achievement_id": achievement_id,
            "achieved_at": achieved_at
        }
        self.achievements[player_id].append(new_achievement)

        return { "success": True, "message": "Achievement added for player." }

    def update_progression(self, player_id: str, additional_experience: int) -> dict:
        """
        Update a player's progression by adding experience_points (XP), and update
        player's level according to XP thresholds and game rules.

        Args:
            player_id (str): The unique ID of the player to update.
            additional_experience (int): Amount of XP to add (must be >= 0).

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of new level/Xp,
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Player must exist.
            - Only positive additional_experience may be added.
            - Level is recalculated according to XP thresholds after addition.
            - XP thresholds for next level: XP needed for level N = (N-1)*N*50
        """
        # Check player exists
        if player_id not in self.progressions:
            return { "success": False, "error": "Player does not exist" }
        if additional_experience < 0:
            return { "success": False, "error": "Cannot add negative experience points" }

        progression = self.progressions[player_id]
        old_xp = progression["experience_points"]
        old_level = progression["level"]

        # Update XP
        new_xp = old_xp + additional_experience

        # LEVEL UP RULE: XP thresholds:
        # Level 1: 0
        # Level 2: 100
        # Level 3: 300
        # Level 4: 600
        # Level N+1: Threshold = N*(N+1)/2 * 100 = sum_{k=1}^N (k*100)
        # But for simplicity, let's use:
        # XP needed for next level = (level^2) * 100
        # We'll loop to find the highest level <= new_xp
        def xp_for_level(level: int) -> int:
            # Level 1: 0 XP
            # Level 2: 100 XP
            # Level 3: 300 XP
            return ((level - 1) * level * 50)

        # Always at least level 1
        new_level = 1
        while True:
            next_level = new_level + 1
            if new_xp >= xp_for_level(next_level):
                new_level += 1
            else:
                break

        # Positive XP updates should never reduce an existing level even if the
        # stored historical XP/level pair is internally inconsistent.
        progression["experience_points"] = new_xp
        progression["level"] = max(old_level, new_level)
        self.progressions[player_id] = progression

        return {
            "success": True,
            "message": f"Player {player_id}: XP updated to {new_xp}, level is now {progression['level']}."
        }


    def record_last_login(self, player_id: str) -> dict:
        """
        Sets the 'last_login' timestamp for the given player's progression to the current time.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict: 
                On success: {'success': True, 'message': 'Player last_login updated'}
                On failure: {'success': False, 'error': <reason>}
        Constraints:
            - player_id must exist in players and progressions.
            - Timestamp is set to the current UTC ISO 8601 time string.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}
        if player_id not in self.progressions:
            return {"success": False, "error": "Player progression does not exist"}
    
        now_iso = self._get_current_time_iso()
        self.progressions[player_id]["last_login"] = now_iso
        return {"success": True, "message": "Player last_login updated"}

    def set_player_account_status(self, player_id: str, new_status: str) -> dict:
        """
        Change a player's account status (e.g., activate, suspend, ban).

        Args:
            player_id (str): The unique identifier of the player.
            new_status (str): The intended account status ("active", "suspended", "banned", etc.).

        Returns:
            dict: 
                - { "success": True, "message": "Player account status updated to <new_status>" }
                - { "success": False, "error": "<reason>" }

        Constraints:
            - The player must exist.
            - No restrictions on allowed status values as per current environment specification.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        self.players[player_id]["account_status"] = new_status
        return { 
            "success": True, 
            "message": f"Player account status updated to {new_status}"
        }


class OnlineGamePlayerAccountDatabase(BaseEnv):
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
            if key == "is_item_valid":
                setattr(env, "item_validation_flag", copy.deepcopy(value))
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

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_player_by_username(self, **kwargs):
        return self._call_inner_tool('get_player_by_username', kwargs)

    def list_all_players(self, **kwargs):
        return self._call_inner_tool('list_all_players', kwargs)

    def check_player_account_status(self, **kwargs):
        return self._call_inner_tool('check_player_account_status', kwargs)

    def get_currency_balance(self, **kwargs):
        return self._call_inner_tool('get_currency_balance', kwargs)

    def get_inventory(self, **kwargs):
        return self._call_inner_tool('get_inventory', kwargs)

    def get_achievements(self, **kwargs):
        return self._call_inner_tool('get_achievements', kwargs)

    def get_progression(self, **kwargs):
        return self._call_inner_tool('get_progression', kwargs)

    def is_item_valid(self, **kwargs):
        return self._call_inner_tool('is_item_valid', kwargs)

    def has_achievement(self, **kwargs):
        return self._call_inner_tool('has_achievement', kwargs)

    def get_players_by_level_range(self, **kwargs):
        return self._call_inner_tool('get_players_by_level_range', kwargs)

    def list_inventory_items_for_player(self, **kwargs):
        return self._call_inner_tool('list_inventory_items_for_player', kwargs)

    def update_currency_balance(self, **kwargs):
        return self._call_inner_tool('update_currency_balance', kwargs)

    def add_inventory_item(self, **kwargs):
        return self._call_inner_tool('add_inventory_item', kwargs)

    def remove_inventory_item(self, **kwargs):
        return self._call_inner_tool('remove_inventory_item', kwargs)

    def add_achievement(self, **kwargs):
        return self._call_inner_tool('add_achievement', kwargs)

    def update_progression(self, **kwargs):
        return self._call_inner_tool('update_progression', kwargs)

    def record_last_login(self, **kwargs):
        return self._call_inner_tool('record_last_login', kwargs)

    def set_player_account_status(self, **kwargs):
        return self._call_inner_tool('set_player_account_status', kwargs)
