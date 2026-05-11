# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
import uuid



# Represents each wine available for browsing, recommendation, and purchase.
class WineProductInfo(TypedDict):
    wine_id: str
    name: str
    varietal: str
    origin: str
    vintage: str
    price: float
    description: str
    stock_quantity: int

# Represents platform users.
class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    user_type: str  # "individual" or "business"
    preferences: str  # Could be List[str], but spec says "preferences"

# Represents an item in a cart.
class CartItemInfo(TypedDict):
    cart_id: str
    wine_id: str
    quantity: int

# Represents a shopping cart for a user.
class ShoppingCartInfo(TypedDict):
    cart_id: str
    user_id: str
    last_updated: str
    cart_items: List[CartItemInfo]

class _GeneratedEnvImpl:
    def __init__(self):
        # Wines: {wine_id: WineProductInfo}
        self.wines: Dict[str, WineProductInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Shopping carts: {cart_id: ShoppingCartInfo}
        self.shopping_carts: Dict[str, ShoppingCartInfo] = {}

        # Constraints:
        # - Wine stock_quantity cannot be negative; users cannot add more to cart than is available.
        # - Each shopping cart is associated with a single user and contains zero or more items.
        # - Only available (in-stock) wines are eligible for recommendation.
        # - Cart contents should be updated in real time if item quantities or stock change.

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.datetime.utcnow().isoformat() + "Z"

    def list_available_wines(self) -> dict:
        """
        Retrieve the full list of wines currently in stock (stock_quantity > 0).

        Returns:
            dict:
                - success (bool): True if the operation completes normally.
                - data (List[WineProductInfo]): List of WineProductInfo for all wines with stock_quantity > 0.

        Constraints:
            - Only wines with stock_quantity > 0 are returned.
            - If no such wines, returns success with empty list.
        """
        available_wines = [
            wine for wine in self.wines.values()
            if wine['stock_quantity'] > 0
        ]
        return { "success": True, "data": available_wines }

    def get_wine_by_id(self, wine_id: str) -> dict:
        """
        Retrieve the details of a wine product given its wine_id.

        Args:
            wine_id (str): The unique identifier for the wine product.

        Returns:
            dict:
                success (bool): Operation result.
                data (WineProductInfo): Wine details if found.
                error (str): Error message if wine is not found.

        Constraints:
            - The wine product with wine_id must exist in the catalogue.
        """
        wine = self.wines.get(wine_id)
        if wine is None:
            return {"success": False, "error": "Wine product not found"}
        return {"success": True, "data": wine}

    def search_wines(
        self, 
        varietal: str = None, 
        origin: str = None, 
        vintage: str = None, 
        min_price: float = None, 
        max_price: float = None
    ) -> dict:
        """
        Search for wines using optional filters (varietal, origin, vintage, price range).

        Args:
            varietal (str, optional): Wine varietal to match.
            origin (str, optional): Wine origin (e.g. country/region) to match.
            vintage (str, optional): Wine vintage (as string or int) to match.
            min_price (float, optional): Minimum price (inclusive).
            max_price (float, optional): Maximum price (inclusive).

        Returns:
            dict: {
                'success': True,
                'data': List[WineProductInfo]    # List of matching wines (empty if none match)
            }
        """
        if isinstance(varietal, str) and varietal.strip() == "":
            varietal = None
        if isinstance(origin, str) and origin.strip() == "":
            origin = None
        if isinstance(vintage, str) and vintage.strip() == "":
            vintage = None

        matches = []
        for wine in self.wines.values():
            # Filter by varietal
            if varietal is not None and wine.get('varietal') != varietal:
                continue
            # Filter by origin
            if origin is not None and wine.get('origin') != origin:
                continue
            # Filter by vintage
            if vintage is not None and str(wine.get('vintage')) != str(vintage):
                continue
            # Filter by min_price
            if min_price is not None and wine.get('price', 0) < min_price:
                continue
            # Filter by max_price
            if max_price is not None and wine.get('price', 0) > max_price:
                continue
            matches.append(wine)
        return { "success": True, "data": matches }

    def recommend_wines(self, user_id: str, limit: int = 10) -> dict:
        """
        Provide a list of wine recommendations for a user, based on wine availability
        and (optionally) user preferences.

        Args:
            user_id (str): ID of the user to recommend wines for.
            limit (int): Maximum number of recommendations to return (default: 10).

        Returns:
            dict: {
                "success": True,
                "data": List[WineProductInfo],  # List of recommended wines (could be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - User must exist.
            - Only wines with stock_quantity > 0 are considered.
            - Optionally use user preferences for more relevant recommendations.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Filter in-stock wines
        available_wines = [
            wine for wine in self.wines.values()
            if wine["stock_quantity"] > 0
        ]

        # Try to use preferences, if any
        preferences = user.get("preferences")
        recommended = []

        if preferences:
            preferences_str = preferences.lower()
            # Recommend wines matching preferences in varietal or origin
            for wine in available_wines:
                if (preferences_str in wine["varietal"].lower()
                    or preferences_str in wine["origin"].lower()
                    or preferences_str in wine["name"].lower()):
                    recommended.append(wine)
            # If not enough, fill up with random/other available wines
            if len(recommended) < limit:
                others = [w for w in available_wines if w not in recommended]
                recommended.extend(others[:limit - len(recommended)])
            # Limit to 'limit'
            recommended = recommended[:limit]
        else:
            # No preferences: recommend any available wines, limit to 'limit'
            recommended = available_wines[:limit]

        return { "success": True, "data": recommended }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user profile info given a user's unique _id.

        Args:
            user_id (str): User's unique _id.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo    # On success
            }
            or
            {
                "success": False,
                "error": str        # "User not found"
            }
        Constraints:
            - The _id must correspond to an existing user.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_cart(self, user_id: str) -> dict:
        """
        Retrieve the current shopping cart and list all its items for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": ShoppingCartInfo,  # Cart and items (cart_items may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. user does not exist or cart not found
            }

        Constraints:
            - The user must exist.
            - Each shopping cart is associated with a single user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        for cart in self.shopping_carts.values():
            if cart["user_id"] == user_id:
                return { "success": True, "data": cart }

        return { "success": False, "error": "Shopping cart not found for user" }

    def get_cart_items(self, cart_id: str) -> dict:
        """
        Retrieve all items (wine_id, quantity) in a specified shopping cart.

        Args:
            cart_id (str): The unique identifier for the shopping cart.

        Returns:
            dict: {
                "success": True,
                "data": List[{'wine_id': str, 'quantity': int}],  # List of cart items from that cart (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., "Cart does not exist"
            }

        Constraints:
            - The cart_id must correspond to an existing shopping cart.
        """
        cart = self.shopping_carts.get(cart_id)
        if not cart:
            return { "success": False, "error": "Cart does not exist" }
        items_info = [
            {"wine_id": item["wine_id"], "quantity": item["quantity"]}
            for item in cart.get("cart_items", [])
        ]
        return { "success": True, "data": items_info }

    def get_cart_item_detail(self, cart_id: str) -> dict:
        """
        For each item in the given shopping cart, provide full wine details along with quantity.

        Args:
            cart_id (str): The ID of the shopping cart to query.

        Returns:
            dict: 
                {
                    "success": True, 
                    "data": List[{"wine": WineProductInfo, "quantity": int}]
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Fails if cart does not exist.
            - Skips any cart items referencing wines that no longer exist in catalog.
        """
        if cart_id not in self.shopping_carts:
            return { "success": False, "error": "Cart does not exist" }
    
        cart = self.shopping_carts[cart_id]
        details = []
        for item in cart.get("cart_items", []):
            wine_id = item["wine_id"]
            if wine_id not in self.wines:
                continue  # Skip missing wines (they were removed from catalog)
            wine_info = self.wines[wine_id]
            details.append({
                "wine": wine_info,
                "quantity": item["quantity"]
            })
        return { "success": True, "data": details }

    def check_wine_stock(self, wine_id: str) -> dict:
        """
        Check available stock quantity for a specified wine.

        Args:
            wine_id (str): The unique identifier for the wine to check.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "wine_id": str,
                            "stock_quantity": int
                        }
                    }
                On failure (wine not found):
                    {
                        "success": False,
                        "error": "Wine not found"
                    }
        Constraints:
            - WineProduct must exist in the system.
            - Stock quantity must reflect the current inventory (may be zero or more).
        """
        wine = self.wines.get(wine_id)
        if wine is None:
            return { "success": False, "error": "Wine not found" }
        return {
            "success": True,
            "data": {
                "wine_id": wine_id,
                "stock_quantity": wine["stock_quantity"]
            }
        }

    def add_cart_item(self, cart_id: str, wine_id: str, quantity: int) -> dict:
        """
        Add a specified quantity of a wine product to the user's shopping cart,
        only if sufficient stock is available and the cart/wine exists.

        Args:
            cart_id (str): The shopping cart's identifier.
            wine_id (str): The wine product's identifier.
            quantity (int): Number of units/bottles to add.

        Returns:
            dict: {
                "success": True,
                "message": "Wine added to cart"
            }
            or
            {
                "success": False,
                "error": "Reason for failure (cart/wine not found, insufficient stock, invalid quantity)"
            }

        Constraints:
            - Cart must exist.
            - Wine must exist.
            - Quantity must be positive.
            - Total quantity in cart plus requested quantity must not exceed stock_quantity.
            - Wine stock_quantity cannot be negative.
        """
        if cart_id not in self.shopping_carts:
            return { "success": False, "error": "Shopping cart does not exist" }
        if wine_id not in self.wines:
            return { "success": False, "error": "Wine product does not exist" }
        if quantity < 1:
            return { "success": False, "error": "Quantity must be at least 1" }

        wine = self.wines[wine_id]
        available_stock = wine["stock_quantity"]

        cart = self.shopping_carts[cart_id]
        cart_items = cart["cart_items"]

        # Find if this wine is already in the cart
        existing_item = None
        for item in cart_items:
            if item["wine_id"] == wine_id:
                existing_item = item
                break

        total_in_cart = existing_item["quantity"] if existing_item else 0
        if (quantity + total_in_cart) > available_stock:
            return {
                "success": False,
                "error": f"Insufficient stock: available {available_stock}, requested {quantity + total_in_cart}"
            }

        if existing_item:
            # Update existing item's quantity
            existing_item["quantity"] += quantity
        else:
            # Add new item to cart
            new_item = {
                "cart_id": cart_id,
                "wine_id": wine_id,
                "quantity": quantity
            }
            cart_items.append(new_item)

        cart["last_updated"] = self._current_timestamp()

        return { "success": True, "message": "Wine added to cart" }

    def update_cart_item_quantity(self, cart_id: str, wine_id: str, new_quantity: int) -> dict:
        """
        Modify the quantity of a specific wine in a cart, enforcing stock constraints.

        Args:
            cart_id (str): The shopping cart's ID.
            wine_id (str): The wine's ID to update quantity for.
            new_quantity (int): The new desired quantity.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of update
            }
            or
            dict: {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Cart must exist.
            - Cart item for wine must exist in cart.
            - Wine must exist.
            - new_quantity >= 0 and <= available stock.
            - Setting quantity to zero removes the item.
        """
        if cart_id not in self.shopping_carts:
            return { "success": False, "error": "Cart does not exist" }

        cart = self.shopping_carts[cart_id]

        # Find the cart item by wine_id
        cart_item = None
        for item in cart["cart_items"]:
            if item["wine_id"] == wine_id:
                cart_item = item
                break

        if cart_item is None:
            return { "success": False, "error": "Wine item not found in cart" }

        if wine_id not in self.wines:
            return { "success": False, "error": "Wine not found" }

        wine = self.wines[wine_id]

        if new_quantity < 0:
            return { "success": False, "error": "Quantity cannot be negative" }

        if new_quantity > wine["stock_quantity"]:
            return { "success": False, "error": "Requested quantity exceeds available stock" }

        # Update or remove cart item
        if new_quantity == 0:
            cart["cart_items"].remove(cart_item)
            cart["last_updated"] = self._current_timestamp()
            return { "success": True, "message": "Cart item removed (quantity set to zero)" }
        else:
            cart_item["quantity"] = new_quantity
            cart["last_updated"] = self._current_timestamp()
            return { "success": True, "message": f"Cart item quantity updated to {new_quantity}" }

    def remove_cart_item(self, cart_id: str, wine_id: str) -> dict:
        """
        Remove a specific wine product from the user’s shopping cart.

        Args:
            cart_id (str): The ID of the shopping cart.
            wine_id (str): The ID of the wine product to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Wine removed from cart."
            }
            or
            {
                "success": False,
                "error": "Reason for the failure."
            }

        Constraints:
            - The cart must exist.
            - If cart does not contain the specified wine, return error.
            - Cart's 'last_updated' should be updated to reflect the change.
        """
        if cart_id not in self.shopping_carts:
            return {"success": False, "error": "Cart does not exist."}

        cart = self.shopping_carts[cart_id]
        original_count = len(cart["cart_items"])
        new_cart_items = [item for item in cart["cart_items"] if item["wine_id"] != wine_id]

        if len(new_cart_items) == original_count:
            return {"success": False, "error": "Wine not found in cart."}

        cart["cart_items"] = new_cart_items

        # Update last_updated (use current timestamp as string, for simplicity use ISO format)
        cart["last_updated"] = self._current_timestamp()

        self.shopping_carts[cart_id] = cart

        return {"success": True, "message": "Wine removed from cart."}

    def clear_cart(self, cart_id: str) -> dict:
        """
        Remove all items from a user’s shopping cart.

        Args:
            cart_id (str): The ID of the shopping cart to clear.

        Returns:
            dict: {
                "success": True,
                "message": "Cart cleared successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The cart must exist.
            - All items are removed and last_updated is set to current time.
            - This operation does not affect wine inventory.
        """
        if cart_id not in self.shopping_carts:
            return { "success": False, "error": "Cart does not exist." }

        self.shopping_carts[cart_id]["cart_items"] = []
        self.shopping_carts[cart_id]["last_updated"] = self._current_timestamp()
        return { "success": True, "message": "Cart cleared successfully." }

    def synchronize_cart_with_stock(self) -> dict:
        """
        Synchronize all shopping carts with the current wine stock.
        - For each cart item:
            - If the wine is no longer in catalog, remove the item from cart.
            - If the wine stock_quantity is zero, remove the item from cart.
            - If the quantity in the cart exceeds available stock, reduce it to the available stock.
        Updates shopping carts in place.
        Returns:
            dict: {
                "success": True,
                "message": "All shopping carts synchronized with current wine stock."
            }
        Constraints:
            - Cart contents should be updated in real time if item quantities or stock change.
            - Users cannot have more in their cart than is available for purchase.
        """
        for cart in self.shopping_carts.values():
            updated_cart_items = []
            changed = False
            for item in cart["cart_items"]:
                wine_id = item["wine_id"]
                quantity = item["quantity"]
                wine = self.wines.get(wine_id)
                if not wine:
                    # Wine deleted from catalog; skip this item (remove)
                    changed = True
                    continue
                stock_quantity = wine.get("stock_quantity", 0)
                if stock_quantity <= 0:
                    # No stock, remove from cart
                    changed = True
                    continue
                if quantity > stock_quantity:
                    # Reduce cart quantity to match available stock
                    updated_cart_items.append({
                        "cart_id": item["cart_id"],
                        "wine_id": wine_id,
                        "quantity": stock_quantity
                    })
                    changed = True
                else:
                    # No problem, keep as is
                    updated_cart_items.append(item)
            cart["cart_items"] = updated_cart_items
            if changed:
                cart["last_updated"] = self._current_timestamp()

        return {
            "success": True,
            "message": "All shopping carts synchronized with current wine stock."
        }

    def update_wine_stock_quantity(self, wine_id: str, new_stock_quantity: int) -> dict:
        """
        Admin-level operation to directly adjust the stock quantity of a wine product.

        Args:
            wine_id (str): The ID of the wine product to update.
            new_stock_quantity (int): The new stock quantity to set. Must be zero or positive.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Wine stock quantity updated." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Cannot set stock quantity negative.
            - wine_id must exist.
            - Shopping cart items referencing this wine must be synchronized if their quantities exceed the new stock.
        """
        # Existence check
        if wine_id not in self.wines:
            return { "success": False, "error": "Wine product not found." }

        # Stock quantity check
        if not isinstance(new_stock_quantity, int) or new_stock_quantity < 0:
            return { "success": False, "error": "Stock quantity cannot be negative." }

        # Update
        self.wines[wine_id]["stock_quantity"] = new_stock_quantity

        # Synchronize carts (if implemented)
        # We'll check carts and adjust any cart_items referencing this wine if necessary
        for cart in self.shopping_carts.values():
            updated = False
            updated_items = []
            for item in cart["cart_items"]:
                if item["wine_id"] != wine_id:
                    updated_items.append(item)
                    continue
                if item["quantity"] <= new_stock_quantity:
                    updated_items.append(item)
                    continue
                updated = True
                if new_stock_quantity > 0:
                    updated_items.append({
                        "cart_id": item["cart_id"],
                        "wine_id": item["wine_id"],
                        "quantity": new_stock_quantity,
                    })
            if updated:
                cart["cart_items"] = updated_items
                cart["last_updated"] = self._current_timestamp()

        return { "success": True, "message": "Wine stock quantity updated." }


    def create_new_cart(self, user_id: str) -> dict:
        """
        Create a new (empty) shopping cart associated with the given user.

        Args:
            user_id (str): The _id of the user for whom to create the cart.

        Returns:
            dict:
              - Success: {
                  "success": True,
                  "message": "Cart created.",
                  "cart_id": <new_cart_id>
                }
              - Failure: {
                  "success": False,
                  "error": "reason"
                }

        Constraints:
            - The user must exist.
            - Each user may only have one active cart.
            - The cart will be empty and have the current timestamp as 'last_updated'.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check for existing cart for this user
        for cart in self.shopping_carts.values():
            if cart["user_id"] == user_id:
                return {"success": False, "error": "User already has a shopping cart."}

        # Generate unique cart_id
        new_cart_id = str(uuid.uuid4())
        if new_cart_id in self.shopping_carts:
            # Super-rare edge case, try again once
            new_cart_id = str(uuid.uuid4())
            if new_cart_id in self.shopping_carts:
                return {"success": False, "error": "Could not generate unique cart ID."}

        # Timestamp: ISO string
        now_str = self._current_timestamp()

        # Create new cart
        new_cart = {
            "cart_id": new_cart_id,
            "user_id": user_id,
            "last_updated": now_str,
            "cart_items": [],
        }
        self.shopping_carts[new_cart_id] = new_cart

        return {
            "success": True,
            "message": "Cart created.",
            "cart_id": new_cart_id,
        }

    def delete_cart(self, cart_id: str) -> dict:
        """
        Remove a shopping cart entirely from the system.

        Args:
            cart_id (str): The unique identifier of the cart to remove.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Cart deleted successfully."}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - The cart must exist in the system to be deleted.
            - Cart items are contained within the cart; no separate cleanup required.
        """
        if cart_id not in self.shopping_carts:
            return {"success": False, "error": "Cart does not exist."}

        del self.shopping_carts[cart_id]
        return {"success": True, "message": "Cart deleted successfully."}


class WineEcommercePlatform(BaseEnv):
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

    def list_available_wines(self, **kwargs):
        return self._call_inner_tool('list_available_wines', kwargs)

    def get_wine_by_id(self, **kwargs):
        return self._call_inner_tool('get_wine_by_id', kwargs)

    def search_wines(self, **kwargs):
        return self._call_inner_tool('search_wines', kwargs)

    def recommend_wines(self, **kwargs):
        return self._call_inner_tool('recommend_wines', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_cart(self, **kwargs):
        return self._call_inner_tool('get_user_cart', kwargs)

    def get_cart_items(self, **kwargs):
        return self._call_inner_tool('get_cart_items', kwargs)

    def get_cart_item_detail(self, **kwargs):
        return self._call_inner_tool('get_cart_item_detail', kwargs)

    def check_wine_stock(self, **kwargs):
        return self._call_inner_tool('check_wine_stock', kwargs)

    def add_cart_item(self, **kwargs):
        return self._call_inner_tool('add_cart_item', kwargs)

    def update_cart_item_quantity(self, **kwargs):
        return self._call_inner_tool('update_cart_item_quantity', kwargs)

    def remove_cart_item(self, **kwargs):
        return self._call_inner_tool('remove_cart_item', kwargs)

    def clear_cart(self, **kwargs):
        return self._call_inner_tool('clear_cart', kwargs)

    def synchronize_cart_with_stock(self, **kwargs):
        return self._call_inner_tool('synchronize_cart_with_stock', kwargs)

    def update_wine_stock_quantity(self, **kwargs):
        return self._call_inner_tool('update_wine_stock_quantity', kwargs)

    def create_new_cart(self, **kwargs):
        return self._call_inner_tool('create_new_cart', kwargs)

    def delete_cart(self, **kwargs):
        return self._call_inner_tool('delete_cart', kwargs)
