# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict
from typing import List, Dict, Any



class GameInfo(TypedDict):
    app_id: str
    title: str
    metadata: Dict[str, Any]
    original_price: float
    discounted_price: float
    discount_percent: float
    is_on_discount: bool
    purchase_url: str
    genre: str
    developer: str
    publisher: str
    release_date: str
    description: str
    tag: str

class DiscountInfo(TypedDict):
    discount_id: str
    app_id: str
    discount_percent: float
    discounted_price: float
    start_date: str
    end_date: str
    active: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a digital game store platform.
        """

        # Games: {app_id: GameInfo}
        self.games: Dict[str, GameInfo] = {}

        # Discounts: {discount_id: DiscountInfo}
        self.discounts: Dict[str, DiscountInfo] = {}
        
        # Constraints:
        # - Discounted price must be <= original price.
        # - Only games with active discounts (is_on_discount = True or active = True
        #   and current date within start_date and end_date) are shown as on offer.
        # - Each game must have a unique app_id.
        # - Purchase URLs are unique to each game and must be valid.

    @staticmethod
    def _discount_dates_valid(discount: DiscountInfo) -> bool:
        try:
            start = discount["start_date"]
            end = discount["end_date"]
        except Exception:
            return False
        if not isinstance(start, str) or not isinstance(end, str):
            return False
        return start <= end

    def _discount_is_effectively_active(self, discount: DiscountInfo) -> bool:
        return bool(discount.get("active", False)) and self._discount_dates_valid(discount)

    def _active_discounts_for_app(self, app_id: str) -> List[DiscountInfo]:
        return [
            discount
            for discount in self.discounts.values()
            if discount.get("app_id") == app_id and self._discount_is_effectively_active(discount)
        ]

    def _sync_game_discount_state(self, app_id: str, preferred_discount_id: str | None = None) -> None:
        game = self.games.get(app_id)
        if not game:
            return

        active_discounts = self._active_discounts_for_app(app_id)
        chosen_discount = None

        if preferred_discount_id is not None:
            for discount in active_discounts:
                if discount.get("discount_id") == preferred_discount_id:
                    chosen_discount = discount
                    break

        if chosen_discount is None and active_discounts:
            chosen_discount = active_discounts[-1]

        if chosen_discount is None:
            game["is_on_discount"] = False
            game["discounted_price"] = game["original_price"]
            game["discount_percent"] = 0.0
            return

        game["is_on_discount"] = True
        game["discounted_price"] = chosen_discount["discounted_price"]
        game["discount_percent"] = chosen_discount["discount_percent"]

    def _sync_all_games_from_discounts(self) -> None:
        for app_id in list(self.games.keys()):
            self._sync_game_discount_state(app_id)


    def list_discounted_games(self) -> dict:
        """
        Retrieve all games currently on active discount on the platform.

        Returns:
            dict:
                success (bool): Operation status.
                data (List[Dict]): List of games on discount, each including
                    title, original_price, discount_percent, discounted_price.

        Constraints:
            - A game is on discount if:
                * game['is_on_discount'] == True
                OR
                * there is a DiscountInfo with active == True, app_id matches,
                  and current date is within [start_date, end_date] (inclusive).
            - Discounted price must be <= original price.
        """
        result: List[Dict[str, Any]] = []

        # Construct a mapping from app_id to all (potentially active) discounts
        discounts_by_app: Dict[str, List[DiscountInfo]] = {}
        for discount in self.discounts.values():
            discounts_by_app.setdefault(discount["app_id"], []).append(discount)

        for game in self.games.values():
            is_discounted = False

            # Check game is_on_discount field
            if game.get("is_on_discount", False):
                is_discounted = True
            else:
                # Check for any active, valid discount in the discounts store
                for discount in discounts_by_app.get(game["app_id"], []):
                    if self._discount_is_effectively_active(discount):
                        is_discounted = True
                        break
            if is_discounted:
                # Pricing check: discounted_price <= original_price
                original_price = game.get("original_price", 0.0)
                discounted_price = game.get("discounted_price", 0.0)
                discount_percent = game.get("discount_percent", 0.0)
                if discounted_price > original_price:
                    # Constraint violation: skip
                    continue
                result.append({
                    "title": game["title"],
                    "original_price": original_price,
                    "discount_percent": discount_percent,
                    "discounted_price": discounted_price,
                })
        return {"success": True, "data": result}

    def get_game_by_app_id(self, app_id: str) -> dict:
        """
        Retrieve detailed metadata and information for a specific game identified by its app_id.

        Args:
            app_id (str): Unique identifier of the game.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": GameInfo}
                - If not found:
                    {"success": False, "error": "Game with specified app_id not found"}
        Constraints:
            - app_id must match a game present in the platform.
        """
        if app_id in self.games:
            return {"success": True, "data": self.games[app_id]}
        else:
            return {"success": False, "error": "Game with specified app_id not found"}

    def get_discount_by_app_id(self, app_id: str) -> dict:
        """
        Retrieve discount details, validity, and pricing for any discount associated with a specific game.

        Args:
            app_id (str): The app_id of the game.

        Returns:
            dict: {
              "success": True,
              "data": DiscountInfo
            }
            or
            {
              "success": False,
              "error": "No discount found for this app_id"
            }
        Constraints:
            - Returns the active discount if present, otherwise any discount for the app_id.
            - If no discount exists at all for the app_id, returns error.
        """
        # Gather all discounts for the given app_id
        candidate_discounts = [
            discount for discount in self.discounts.values()
            if discount["app_id"] == app_id
        ]
        if not candidate_discounts:
            return {"success": False, "error": "No discount found for this app_id"}
    
        # Prefer active discounts
        active_discounts = [d for d in candidate_discounts if d["active"]]
        if active_discounts:
            # If multiple active, pick the one with the closest end_date
            # (Optional: for now just pick the first)
            return {"success": True, "data": active_discounts[0]}
    
        # Otherwise, return first available discount (inactive)
        return {"success": True, "data": candidate_discounts[0]}

    def get_game_purchase_url(self, app_id: str) -> dict:
        """
        Retrieve the purchase URL for a game by its unique app_id.

        Args:
            app_id (str): The unique identifier for the game.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": {
                        "app_id": str,
                        "purchase_url": str
                    }
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g., game not found.
                  }
        Constraints:
            - The app_id must exist in the platform's games.
            - Purchase URL is assumed valid if present in the game info.
        """
        game = self.games.get(app_id)
        if not game:
            return {"success": False, "error": "Game not found"}
        return {
            "success": True,
            "data": {
                "app_id": app_id,
                "purchase_url": game["purchase_url"]
            }
        }

    def list_games_by_genre(self, genre: str) -> dict:
        """
        List all games filtered by a specific genre.

        Args:
            genre (str): The genre to filter games by.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo]  # List of games for the given genre (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid
            }

        Constraints:
            - genre must be a non-empty string.
        """
        if not isinstance(genre, str) or not genre.strip():
            return { "success": False, "error": "Invalid genre parameter" }
    
        result = [
            game_info for game_info in self.games.values()
            if game_info["genre"] == genre
        ]
        return { "success": True, "data": result }

    def search_games_by_title(self, title_query: str) -> dict:
        """
        Return a list of games that match or partially match a given title string (case-insensitive substring match).

        Args:
            title_query (str): The string to search for within game titles.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # List of matching games (empty if none matched)
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., invalid input type)
            }
    
        Constraints:
            - No extra domain constraints for this query.
            - Matching is case-insensitive.
        """
        if not isinstance(title_query, str):
            return {"success": False, "error": "title_query must be a string"}

        query_lower = title_query.lower()
        matching_games = [
            game_info for game_info in self.games.values()
            if query_lower in game_info["title"].lower()
        ]
        return {"success": True, "data": matching_games}

    def list_all_games(self) -> dict:
        """
        Retrieve metadata for all games in the digital game store catalog.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo]  # List of all games' metadata (may be empty if no games)
            }
        """
        result = list(self.games.values())
        return { "success": True, "data": result }

    def get_active_discounts(self) -> dict:
        """
        Retrieve all currently active discount offers with their details.

        Returns:
            dict: {
                "success": True,
                "data": List[DiscountInfo]  # List of active discount information dicts.
            }

        Constraints:
            - Only discounts with 'active' == True and current date between 'start_date' and 'end_date' (inclusive) are considered active.
            - If no active discounts, data is an empty list.
            - Discounts with invalid date fields are ignored.
        """

        active_discounts = []
        for discount in self.discounts.values():
            if self._discount_is_effectively_active(discount):
                active_discounts.append(discount)
        return {"success": True, "data": active_discounts}

    def add_or_update_game(self, game_info: dict) -> dict:
        """
        Add a new game or update an existing game's metadata and pricing.
        Enforces:
            - Unique app_id for each game.
            - Unique purchase_url for each game.
            - discounted_price <= original_price
    
        Args:
            game_info (dict): Dictionary containing all GameInfo fields.
        
        Returns:
            dict: On success:
                { "success": True, "message": "Game added" } or
                { "success": True, "message": "Game updated" }
            On error:
                { "success": False, "error": "reason" }
        """
        # Required fields
        required_fields = [
            "app_id", "title", "metadata", "original_price", "discounted_price", 
            "discount_percent", "is_on_discount", "purchase_url", "genre", 
            "developer", "publisher", "release_date", "description", "tag"
        ]
        for field in required_fields:
            if field not in game_info:
                return {"success": False, "error": f"Missing required field: {field}"}

        app_id = game_info["app_id"]
        purchase_url = game_info["purchase_url"]
        original_price = game_info["original_price"]
        discounted_price = game_info["discounted_price"]
    
        # Discounted price constraint
        if not isinstance(original_price, (float, int)) or not isinstance(discounted_price, (float, int)):
            return {"success": False, "error": "Prices must be numeric values"}
        if discounted_price > original_price:
            return {"success": False, "error": "Discounted price must be less than or equal to original price"}
    
        # Purchase URL uniqueness constraint
        for existing_app_id, existing_game in self.games.items():
            if existing_game.get("purchase_url") == purchase_url:
                if app_id != existing_app_id:
                    return {
                        "success": False,
                        "error": "Purchase URL must be unique across all games"
                    }

        # New game or update?
        if app_id in self.games:
            # Update existing game
            self.games[app_id].update(game_info)
            return {"success": True, "message": "Game updated"}
        else:
            # Add new game, enforce uniqueness of app_id handled by dict key
            self.games[app_id] = game_info
            return {"success": True, "message": "Game added"}

    def add_or_update_discount(
        self,
        discount_id: str,
        app_id: str,
        discount_percent: float,
        discounted_price: float,
        start_date: str,
        end_date: str,
        active: bool
    ) -> dict:
        """
        Create or update a discount offer for a game, enforcing that:
          - discounted_price ≤ original_price for the game
          - app_id exists in games
          - discount_percent is 0-100
          - discount_id is unique (or will be updated)
        Args:
            discount_id (str): Unique identifier for the discount
            app_id (str): Game to receive discount
            discount_percent (float): Numeric percent off (0-100)
            discounted_price (float): New price
            start_date (str): Discount valid start date (YYYY-MM-DD)
            end_date (str): Discount valid end date (YYYY-MM-DD)
            active (bool): If the discount is currently active

        Returns:
            dict: {
                "success": True,
                "message": "Discount created/updated for game <app_id>"
            }
            or
            {
                "success": False,
                "error": "Error message"
            }
        Constraints:
            - discounted_price must be less than or equal to original_price.
            - app_id must exist.
            - 0 ≤ discount_percent ≤ 100
        """
        # Game existence
        if app_id not in self.games:
            return {"success": False, "error": f"Game with app_id {app_id} does not exist"}

        game = self.games[app_id]
        if discounted_price > game["original_price"]:
            return {"success": False, "error": "Discounted price cannot exceed original price"}

        if not (0 <= discount_percent <= 100):
            return {"success": False, "error": "Discount percent must be between 0 and 100"}

        if not isinstance(start_date, str) or not isinstance(end_date, str) or start_date > end_date:
            return {"success": False, "error": "Invalid discount date range"}

        discount_info = {
            "discount_id": discount_id,
            "app_id": app_id,
            "discount_percent": discount_percent,
            "discounted_price": discounted_price,
            "start_date": start_date,
            "end_date": end_date,
            "active": active
        }

        self.discounts[discount_id] = discount_info
        self._sync_game_discount_state(app_id, preferred_discount_id=discount_id)

        return {
            "success": True,
            "message": f"Discount created/updated for game {app_id}"
        }

    def remove_discount(self, discount_id: str) -> dict:
        """
        Remove a discount offer given by its discount_id, deactivating and disassociating it
        from its corresponding game. Updates the associated game's discount status and price.

        Args:
            discount_id (str): The unique ID of the discount to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Discount <discount_id> removed and associated game updated."
            }
            or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - If discount does not exist, operation fails.
            - Associated game is updated: is_on_discount=False, discounted_price=original_price, discount_percent=0.
        """
        if discount_id not in self.discounts:
            return { "success": False, "error": "Discount does not exist." }

        discount = self.discounts[discount_id]
        app_id = discount["app_id"]

        # Remove the discount from discounts dict
        del self.discounts[discount_id]

        game_updated = app_id in self.games
        self._sync_game_discount_state(app_id)

        msg = f"Discount {discount_id} removed."
        if game_updated:
            msg += " Associated game updated."
        else:
            msg += " Associated game not found, so no game updated."

        return { "success": True, "message": msg }

    def update_purchase_url(self, app_id: str, new_url: str) -> dict:
        """
        Change the purchase URL for a game, ensuring the URL is unique across all games
        and has a valid format.

        Args:
            app_id (str): The app_id of the game to update.
            new_url (str): The new purchase URL.

        Returns:
            dict: {
                "success": True,
                "message": "Purchase URL for game <app_id> updated."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - The game with app_id must exist.
            - The new purchase_url must not be already used by a different game.
            - The purchase_url must be a valid URL (starts with "http://" or "https://").
        """

        # Check if game exists
        if app_id not in self.games:
            return { "success": False, "error": "Game not found." }
    
        # Check URL validity
        if not (isinstance(new_url, str) and (new_url.startswith("http://") or new_url.startswith("https://")) and len(new_url) > len("http://")):
            return { "success": False, "error": "Invalid purchase URL." }
    
        # Check uniqueness (except for this game itself)
        for other_app_id, game in self.games.items():
            if other_app_id != app_id and game["purchase_url"] == new_url:
                return { "success": False, "error": "Purchase URL already in use." }

        # Update purchase URL
        self.games[app_id]["purchase_url"] = new_url

        return { "success": True, "message": f"Purchase URL for game {app_id} updated." }

    def update_game_price(self, app_id: str, new_price: float) -> dict:
        """
        Change the original price of a game identified by app_id, ensuring that
        the discounted price does not exceed the new original price as per constraints.
    
        Args:
            app_id (str): The application's unique identifier.
            new_price (float): The new original price to set. Must be > 0.
        
        Returns:
            dict:
                On success:
                    { "success": True, "message": "Game price updated." }
                On failure:
                    { "success": False, "error": "reason" }
        Constraints:
            - The game must exist.
            - new_price > 0.
            - After update, discounted_price ≤ original_price.
        """
        # Check if game exists
        game = self.games.get(app_id)
        if not game:
            return { "success": False, "error": "Game not found." }
        if not isinstance(new_price, (int, float)) or new_price <= 0:
            return { "success": False, "error": "Invalid new price. Must be a positive number." }

        # Update the original price
        game["original_price"] = new_price

        # Enforce constraint: discounted_price <= original_price
        if game["discounted_price"] > new_price:
            # Adjust discounted_price and discount_percent
            game["discounted_price"] = new_price
            game["discount_percent"] = 0.0
            # Optionally, you might want to set is_on_discount=False
            if game["is_on_discount"]:
                game["is_on_discount"] = False

        # If there is also an active discount record, ensure discount integrity
        for discount in self.discounts.values():
            if discount["app_id"] == app_id:
                if discount["discounted_price"] > new_price:
                    discount["discounted_price"] = new_price
                    discount["discount_percent"] = 0.0
                    discount["active"] = False

        self._sync_game_discount_state(app_id)

        return { "success": True, "message": "Game price updated." }

    def change_discount_status(
        self,
        discount_id: str,
        active: bool = None,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        Activate or deactivate a discount, and/or update its validity period.

        Args:
            discount_id (str): The unique ID of the discount to modify.
            active (bool, optional): Set to True to activate, False to deactivate; if None, not changed.
            start_date (str, optional): New start date for validity period (ISO8601), or None for no change.
            end_date (str, optional): New end date for validity period (ISO8601), or None for no change.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the operations performed,
            }
            or
            {
                "success": False,
                "error": str     # Error message
            }

        Constraints:
            - discount_id must exist in self.discounts.
            - If both start_date and end_date are provided, start_date must be <= end_date.
            - At least one of active, start_date, or end_date must be provided.
        """
        if discount_id not in self.discounts:
            return {"success": False, "error": "Discount ID not found"}

        discount = self.discounts[discount_id]

        if active is None and start_date is None and end_date is None:
            return {"success": False, "error": "No update parameters provided"}

        # If both start_date and end_date given, check order
        if start_date is not None and end_date is not None:
            if start_date > end_date:
                return {"success": False, "error": "start_date cannot be after end_date"}

        messages = []
        if active is not None:
            discount["active"] = active
            messages.append(f"Active status set to {active}")

        if start_date is not None:
            discount["start_date"] = start_date
            messages.append(f"Start date set to {start_date}")

        if end_date is not None:
            discount["end_date"] = end_date
            messages.append(f"End date set to {end_date}")

        self.discounts[discount_id] = discount  # Update to ensure write-through
        self._sync_game_discount_state(discount["app_id"], preferred_discount_id=discount_id)

        return {"success": True, "message": "; ".join(messages)}


class DigitalGameStorePlatform(BaseEnv):
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
        if hasattr(env, "_sync_all_games_from_discounts"):
            env._sync_all_games_from_discounts()

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

    def list_discounted_games(self, **kwargs):
        return self._call_inner_tool('list_discounted_games', kwargs)

    def get_game_by_app_id(self, **kwargs):
        return self._call_inner_tool('get_game_by_app_id', kwargs)

    def get_discount_by_app_id(self, **kwargs):
        return self._call_inner_tool('get_discount_by_app_id', kwargs)

    def get_game_purchase_url(self, **kwargs):
        return self._call_inner_tool('get_game_purchase_url', kwargs)

    def list_games_by_genre(self, **kwargs):
        return self._call_inner_tool('list_games_by_genre', kwargs)

    def search_games_by_title(self, **kwargs):
        return self._call_inner_tool('search_games_by_title', kwargs)

    def list_all_games(self, **kwargs):
        return self._call_inner_tool('list_all_games', kwargs)

    def get_active_discounts(self, **kwargs):
        return self._call_inner_tool('get_active_discounts', kwargs)

    def add_or_update_game(self, **kwargs):
        return self._call_inner_tool('add_or_update_game', kwargs)

    def add_or_update_discount(self, **kwargs):
        return self._call_inner_tool('add_or_update_discount', kwargs)

    def remove_discount(self, **kwargs):
        return self._call_inner_tool('remove_discount', kwargs)

    def update_purchase_url(self, **kwargs):
        return self._call_inner_tool('update_purchase_url', kwargs)

    def update_game_price(self, **kwargs):
        return self._call_inner_tool('update_game_price', kwargs)

    def change_discount_status(self, **kwargs):
        return self._call_inner_tool('change_discount_status', kwargs)
