# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
import uuid
import time
from typing import Optional, Dict



class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    price: float
    stock_quantity: int
    is_available: bool

class UserInfo(TypedDict):
    user_id: str
    name: str
    preferred_payment_method: str
    contact_info: str

class ShoppingListInfo(TypedDict):
    user_id: str
    list_id: str
    item_ids: List[str]
    created_at: str
    note: str

class ShoppingCartInfo(TypedDict):
    user_id: str
    cart_id: str
    item_ids: List[str]
    quantities: Dict[str, int]  # product_id → quantity

class OrderInfo(TypedDict):
    order_id: str
    user_id: str
    item_ids: List[str]
    quantities: Dict[str, int]  # product_id → quantity
    status: str
    placed_at: str
    delivery_slot: str

class PaymentInfo(TypedDict):
    payment_id: str
    order_id: str
    user_id: str
    amount: float
    status: str
    payment_method: str
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Shopping Lists: {user_id: {list_id: ShoppingListInfo}}
        self.shopping_lists: Dict[str, Dict[str, ShoppingListInfo]] = {}

        # Shopping Carts: {user_id: ShoppingCartInfo}
        self.shopping_carts: Dict[str, ShoppingCartInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Payments: {payment_id: PaymentInfo}
        self.payments: Dict[str, PaymentInfo] = {}

        # Constraints:
        # - Orders can only be placed for items with sufficient stock_quantity.
        # - Shopping carts are user-specific and may differ from saved shopping lists.
        # - Payment must be successful for order status to progress from "pending" to "processing" or "confirmed".
        # - Product availability must be updated in real-time as orders are placed.
        # - Users can only manage and view their own shopping lists, carts, and order history.

    def get_product_by_name(self, name: str) -> dict:
        """
        Retrieve product info by product name.
    
        Args:
            name (str): The product name to search for (case-sensitive).
    
        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of matching products; empty list if none found
            }
            or
            {
                "success": False,
                "error": str  # If name is invalid or not provided
            }

        Notes:
            - Name match is case-sensitive and may return multiple products if names are not unique.
            - Always includes stock and availability in the result.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing product name"}

        matches = [
            prod for prod in self.products.values()
            if prod["name"] == name
        ]

        return {"success": True, "data": matches}

    def list_products_by_category(self, category: str) -> dict:
        """
        List all available products for a given category.

        Args:
            category (str): The category name (case sensitive).

        Returns:
            dict:
                success (bool): True on success.
                data (List[ProductInfo]): List of available products in the specified category (may be empty).

            If no products match the category or none are available, data will be an empty list.
            If input category is an empty string, data will be an empty list.
        """
        if not category or not isinstance(category, str):
            # Treat as valid but no results, do not return an error
            return {"success": True, "data": []}

        result = [
            info for info in self.products.values()
            if info["category"] == category and info.get("is_available", False)
        ]
        return {"success": True, "data": result}

    def check_product_stock(self, product_id: str) -> dict:
        """
        Query the current stock quantity of a specified product.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "product_id": str,
                            "stock_quantity": int
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g. "Product not found"
                    }

        Constraints:
            - The product must exist in the system.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        return {
            "success": True,
            "data": {
                "product_id": product_id,
                "stock_quantity": product["stock_quantity"]
            }
        }

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve account/profile information for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # The user's profile/account information
            }
            or
            {
                "success": False,
                "error": str  # Error message if user does not exist
            }

        Constraints:
            - The user_id must exist in the system's users.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        return {"success": True, "data": self.users[user_id]}

    def get_user_shopping_lists(self, user_id: str) -> dict:
        """
        Retrieve all shopping lists for the specified user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ShoppingListInfo]  # list may be empty if user has no shopping lists
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., user does not exist)
                    }

        Constraints:
            - The user must exist within the system.
            - Only returns lists belonging to this user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        lists = []
        if user_id in self.shopping_lists:
            lists = list(self.shopping_lists[user_id].values())

        return {"success": True, "data": lists}

    def get_shopping_list_by_id(self, user_id: str, list_id: str) -> dict:
        """
        Retrieve details of a specific shopping list by list_id and user_id.

        Args:
            user_id (str): ID for the owner of the shopping list.
            list_id (str): ID of the shopping list to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ShoppingListInfo,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Users can only access their own shopping lists.
            - Returns error if user does not exist or list_id does not exist for user.
        """
        if user_id not in self.shopping_lists:
            return {"success": False, "error": "User has no shopping lists."}

        user_lists = self.shopping_lists[user_id]
        if list_id not in user_lists:
            return {"success": False, "error": "Shopping list not found for user."}

        return {"success": True, "data": user_lists[list_id]}

    def get_user_shopping_cart(self, user_id: str) -> dict:
        """
        Retrieve the active shopping cart for a given user.

        Args:
            user_id (str): The ID of the user whose shopping cart is requested.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": ShoppingCartInfo
                }
                On failure:
                {
                    "success": False,
                    "error": str  # "User not found" or "No active shopping cart for user"
                }

        Constraints:
            - User must exist in the system.
            - User must have an active shopping cart.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        if user_id not in self.shopping_carts:
            return { "success": False, "error": "No active shopping cart for user" }

        cart = self.shopping_carts[user_id]
        return { "success": True, "data": cart }

    def get_cart_items_and_quantities(self, user_id: str) -> dict:
        """
        List product IDs and their quantities currently in the user's shopping cart.

        Args:
            user_id (str): The ID of the user whose cart is to be queried.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "item_ids": List[str],
                            "quantities": Dict[str, int]
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - Only the specified user's cart is accessed.
            - If the user does not have an active cart, the result is failure.
        """
        cart = self.shopping_carts.get(user_id)
        if cart is None:
            return { "success": False, "error": "No shopping cart found for the user." }

        item_ids = cart.get("item_ids", [])
        quantities = cart.get("quantities", {})

        return {
            "success": True,
            "data": {
                "item_ids": item_ids,
                "quantities": quantities
            }
        }

    def get_user_orders(self, user_id: str) -> dict:
        """
        List all orders for the given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[OrderInfo]  # List of orders for the user (may be empty)
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # "User not found"
                    }
        Constraints:
            - User must exist.
            - Returns all orders belonging to the specified user (may be empty).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_orders = [
            order_info for order_info in self.orders.values()
            if order_info["user_id"] == user_id
        ]

        return {"success": True, "data": user_orders}

    def get_order_details(self, order_id: str, user_id: str) -> dict:
        """
        Retrieve the full details of a specific order for a user.

        Args:
            order_id (str): ID of the order to look up.
            user_id (str): The user requesting the details. Only allowed to view their own orders.

        Returns:
            dict:
              - On success:
                  {
                      "success": True,
                      "data": OrderInfo  # Order's full detail.
                  }
              - On failure (order not found or user mismatch):
                  {
                      "success": False,
                      "error": str  # "Order not found" or "Permission denied"
                  }

        Constraints:
          - Users can only view their own orders (order.user_id must equal user_id).
        """
        order = self.orders.get(order_id)
        if order is None:
            return {"success": False, "error": "Order not found"}

        if order["user_id"] != user_id:
            return {"success": False, "error": "Permission denied"}

        return {"success": True, "data": order}

    def get_order_status(self, user_id: str, order_id: str) -> dict:
        """
        Query the current status of a user's order.

        Args:
            user_id (str): The ID of the user requesting the order status.
            order_id (str): The ID of the order.

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        "order_id": str,
                        "status": str
                    }
                }
            or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Users can only view the status of their own orders.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order does not exist"}
        if order["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: User does not own this order"}
        return {"success": True, "data": {"order_id": order_id, "status": order["status"]}}

    def get_user_payments(self, user_id: str) -> dict:
        """
        List all payment records for a given user.

        Args:
            user_id (str): The ID of the user whose payment records are to be returned.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[PaymentInfo],  # List of payments for the user (may be empty)
                  }
                - On failure: {
                    "success": False,
                    "error": str  # "User does not exist."
                  }

        Constraints:
            - Users can only view their own payment records.
            - user_id must exist in self.users.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        user_payments = [
            payment for payment in self.payments.values()
            if payment["user_id"] == user_id
        ]

        return {"success": True, "data": user_payments}

    def get_payment_details(self, payment_id: str) -> dict:
        """
        Retrieve details for a specific payment using payment_id.

        Args:
            payment_id (str): Unique identifier for the payment.

        Returns:
            dict:
                Success:
                    { "success": True, "data": PaymentInfo }
                Failure (not found):
                    { "success": False, "error": "Payment not found" }

        Constraints:
            - Payment must exist in the system.
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return { "success": False, "error": "Payment not found" }

        return { "success": True, "data": payment }

    def add_item_to_shopping_cart(self, user_id: str, product_id: str, quantity: int) -> dict:
        """
        Add a product with the specified quantity to the user's shopping cart.

        Args:
            user_id (str): The ID of the user performing the operation.
            product_id (str): The ID of the product to be added.
            quantity (int): The number of units to add (must be > 0).

        Returns:
            dict: {
                "success": True,
                "message": "Added X units of product Y to user's cart."
            }
            OR
            dict: {
                "success": False,
                "error": "Description of the failure reason."
            }

        Constraints:
            - User must exist.
            - Product must exist and be available.
            - Quantity must be positive.
            - Stock must be sufficient (requested cart quantity ≤ stock_quantity).
            - If no shopping cart exists for user, create one.
            - Product will only appear once per cart (increase quantity if already in cart).
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check product existence
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product does not exist."}

        # Check product availability
        if not product['is_available']:
            return {"success": False, "error": "Product is not available."}

        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            return {"success": False, "error": "Quantity must be a positive integer."}

        # Create user cart if not present
        if user_id not in self.shopping_carts:
            self.shopping_carts[user_id] = ShoppingCartInfo(
                user_id=user_id,
                cart_id=f"cart_{user_id}",      # simple scheme
                item_ids=[],
                quantities={}
            )
        cart = self.shopping_carts[user_id]

        # Determine new desired quantity for the product in the cart
        already_in_cart = cart['quantities'].get(product_id, 0)
        new_cart_quantity = already_in_cart + quantity

        # Check the stock constraint
        if new_cart_quantity > product["stock_quantity"]:
            return {"success": False, "error": "Requested quantity exceeds current stock."}

        # Add or update product in cart
        if product_id not in cart['quantities']:
            cart['item_ids'].append(product_id)
        cart['quantities'][product_id] = new_cart_quantity

        return {
            "success": True,
            "message": f"Added {quantity} units of product {product_id} to user's cart."
        }

    def remove_item_from_shopping_cart(self, user_id: str, product_id: str) -> dict:
        """
        Remove a specific product from the specified user's shopping cart.

        Args:
            user_id (str): The ID of the user whose cart is being modified.
            product_id (str): The ID of the product to remove from the cart.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Product removed from shopping cart."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The user must exist and have a shopping cart.
            - The product must be present in the user's cart.
            - Only affects the specified user's cart, not inventory or shopping lists.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        cart = self.shopping_carts.get(user_id)
        if not cart:
            return {"success": False, "error": "User does not have a shopping cart."}

        if product_id not in cart["item_ids"]:
            return {"success": False, "error": "Product not in shopping cart."}

        # Remove the product from the cart's item_ids and quantities
        cart["item_ids"] = [pid for pid in cart["item_ids"] if pid != product_id]
        if product_id in cart["quantities"]:
            del cart["quantities"][product_id]

        # State is already modified in self.shopping_carts[user_id] (dictionary is by reference)
        return {"success": True, "message": "Product removed from shopping cart."}

    def update_cart_item_quantity(self, user_id: str, product_id: str, quantity: int) -> dict:
        """
        Change the quantity of an item already in the user's shopping cart.

        Args:
            user_id (str): The ID of the user whose cart is being modified.
            product_id (str): The ID of the product to update in the cart.
            quantity (int): The new quantity for the item (must be >= 0).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Cart quantity updated." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - User can only modify their own cart.
            - Cart must exist for the user.
            - Product must already be in the user's cart.
            - Quantity must not be negative.
            - Setting quantity to 0 removes the product from the cart.
        """
        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
    
        # Check that cart exists for the user
        cart = self.shopping_carts.get(user_id)
        if not cart:
            return {"success": False, "error": "Shopping cart does not exist for user."}
    
        # Check that the product is in the cart
        if product_id not in cart["item_ids"] or product_id not in cart["quantities"]:
            return {"success": False, "error": "Product is not in the shopping cart."}
    
        # Validate quantity
        if quantity < 0:
            return {"success": False, "error": "Quantity cannot be negative."}
    
        if quantity == 0:
            # Remove item from cart
            cart["item_ids"] = [pid for pid in cart["item_ids"] if pid != product_id]
            if product_id in cart["quantities"]:
                del cart["quantities"][product_id]
            return {"success": True, "message": "Product removed from cart."}
        else:
            # Update quantity
            cart["quantities"][product_id] = quantity
            return {"success": True, "message": "Cart quantity updated."}

    def clear_shopping_cart(self, user_id: str) -> dict:
        """
        Remove all items from the specified user's shopping cart.

        Args:
            user_id (str): The ID of the user whose cart is to be cleared.

        Returns:
            dict: {
                "success": True,
                "message": "Shopping cart cleared for user <user_id>."
            }
            OR
            {
                "success": False,
                "error": "Shopping cart not found for user."
            }

        Constraints:
            - Only carts existing in self.shopping_carts can be cleared.
            - Cart becomes empty: item_ids is emptied, quantities is an empty dict.
            - Users can only clear their own carts (assumed enforced externally).
        """
        cart = self.shopping_carts.get(user_id)
        if not cart:
            return {"success": False, "error": "Shopping cart not found for user."}

        cart["item_ids"] = []
        cart["quantities"] = {}

        return {
            "success": True,
            "message": f"Shopping cart cleared for user {user_id}."
        }

    def create_shopping_list(
        self,
        user_id: str,
        list_id: str,
        item_ids: list,
        created_at: str,
        note: str
    ) -> dict:
        """
        Create and save a new shopping list for the specified user.
    
        Args:
            user_id (str): User creating the shopping list (must exist).
            list_id (str): Unique list ID for this user (must not already exist for this user).
            item_ids (list of str): Product IDs to include.
            created_at (str): Creation timestamp.
            note (str): Description or note for the shopping list.

        Returns:
            dict: 
                On success: { "success": True, "message": "Shopping list created." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - user_id must exist
            - list_id must be unique for this user
            - All item_ids must exist in products
            - Users can only create lists for themselves
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if user_id not in self.shopping_lists:
            self.shopping_lists[user_id] = {}

        if list_id in self.shopping_lists[user_id]:
            return { "success": False, "error": "Shopping list ID already exists for this user" }

        invalid_items = [item_id for item_id in item_ids if item_id not in self.products]
        if invalid_items:
            return { "success": False, "error": f"Invalid product IDs: {', '.join(invalid_items)}" }

        new_list = {
            "user_id": user_id,
            "list_id": list_id,
            "item_ids": item_ids,
            "created_at": created_at,
            "note": note
        }
        self.shopping_lists[user_id][list_id] = new_list

        return { "success": True, "message": "Shopping list created." }

    def add_item_to_shopping_list(self, user_id: str, list_id: str, product_id: str) -> dict:
        """
        Add a product to a user's specific shopping list.

        Args:
            user_id (str): The ID of the user making the change.
            list_id (str): The shopping list ID (must belong to user_id).
            product_id (str): The ID of the product to add.

        Returns:
            dict: 
                - If successful: { "success": True, "message": "Product added to shopping list." }
                - If error: { "success": False, "error": "Reason for failure" }

        Constraints:
            - User can only add items to their own lists.
            - Product must exist in the system.
            - Product will not be added if already present in the list.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Check shopping list exists for user
        if user_id not in self.shopping_lists or list_id not in self.shopping_lists[user_id]:
            return { "success": False, "error": "Shopping list does not exist for this user." }

        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }

        shopping_list = self.shopping_lists[user_id][list_id]

        # Check for duplicate
        if product_id in shopping_list["item_ids"]:
            return { "success": False, "error": "Product is already in the shopping list." }

        # Add product
        shopping_list["item_ids"].append(product_id)

        return { "success": True, "message": "Product added to shopping list." }

    def remove_item_from_shopping_list(self, user_id: str, list_id: str, product_id: str) -> dict:
        """
        Remove a product from a specific shopping list.

        Args:
            user_id (str): The ID of the user who owns the shopping list.
            list_id (str): The ID of the shopping list to modify.
            product_id (str): The product ID to remove from the shopping list.

        Returns:
            dict: {
                "success": True,
                "message": "Product removed from shopping list."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Users can only manage and view their own shopping lists.
            - Shopping list must belong to the specified user.
        """
        # Check that the user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check that the user has any shopping lists
        if user_id not in self.shopping_lists or list_id not in self.shopping_lists[user_id]:
            return {"success": False, "error": "Shopping list does not exist for this user."}

        shopping_list = self.shopping_lists[user_id][list_id]

        if product_id not in shopping_list["item_ids"]:
            return {"success": False, "error": "Product not found in shopping list."}

        # Remove product_id from item_ids
        shopping_list["item_ids"].remove(product_id)

        return {"success": True, "message": "Product removed from shopping list."}

    def place_order(self, user_id: str) -> dict:
        """
        Create a new order from the user's shopping cart, checking and updating product stock.

        Args:
            user_id (str): The ID of the user placing the order.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "order_id": <new_order_id>,
                        "message": "Order placed successfully."
                    }
                - On error:
                    {
                        "success": False,
                        "error": <error_message>
                    }
        Constraints:
            - Cannot place order if user/cart does not exist, cart is empty, or stock is insufficient for any item.
            - If successful, product stock is decremented, cart is cleared, and order is recorded.
        """

        # User existence check
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Shopping cart existence and non-empty check
        cart = self.shopping_carts.get(user_id)
        if not cart or not cart["item_ids"] or not cart.get("quantities"):
            return {"success": False, "error": "Shopping cart is empty."}

        # Check product availability and collect error info
        insufficient = []
        for product_id in cart["item_ids"]:
            product = self.products.get(product_id)
            quantity = cart["quantities"].get(product_id, 0)
            if not product:
                insufficient.append({"product_id": product_id, "reason": "Product does not exist"})
            elif not product["is_available"]:
                insufficient.append({"product_id": product_id, "reason": "Product not available"})
            elif quantity > product["stock_quantity"]:
                insufficient.append({"product_id": product_id, "reason": "Insufficient stock"})

        if insufficient:
            return {
                "success": False,
                "error": f"Order not placed due to issues with products: {insufficient}"
            }

        # All checks passed; place order.
        # Update product inventory
        for product_id in cart["item_ids"]:
            quantity = cart["quantities"][product_id]
            self.products[product_id]["stock_quantity"] -= quantity
            # If stock reaches zero, mark unavailable
            if self.products[product_id]["stock_quantity"] == 0:
                self.products[product_id]["is_available"] = False

        # Create order_id
        order_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        order_info = {
            "order_id": order_id,
            "user_id": user_id,
            "item_ids": list(cart["item_ids"]),
            "quantities": dict(cart["quantities"]),
            "status": "pending",  # Order just placed
            "placed_at": now,
            "delivery_slot": ""   # Empty, must be set later
        }
        self.orders[order_id] = order_info

        # Clear cart
        self.shopping_carts[user_id]["item_ids"] = []
        self.shopping_carts[user_id]["quantities"] = {}

        return {
            "success": True,
            "order_id": order_id,
            "message": "Order placed successfully."
        }

    def update_product_inventory(self, product_id: str, new_stock_quantity: int) -> dict:
        """
        Adjust the stock_quantity and is_available status of a product.

        Args:
            product_id (str): The product to update.
            new_stock_quantity (int): The value to set stock_quantity to. Must be >= 0.

        Returns:
            dict:
                { "success": True, "message": "Inventory updated" }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - product_id must exist.
            - new_stock_quantity must be >= 0.
            - If new_stock_quantity == 0, set is_available to False. If > 0, True.
        """
        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }
        # Check stock_quantity validity
        if not isinstance(new_stock_quantity, int) or new_stock_quantity < 0:
            return { "success": False, "error": "Stock quantity must be a non-negative integer" }

        product = self.products[product_id]
        product["stock_quantity"] = new_stock_quantity
        product["is_available"] = new_stock_quantity > 0

        return { "success": True, "message": "Inventory updated" }


    def create_payment(self, order_id: str, payment_method: Optional[str] = None, amount: Optional[float] = None) -> dict:
        """
        Create a payment record for an order (initiates transaction for user).

        Args:
            order_id (str): The ID of the order to be paid.
            payment_method (Optional[str]): Payment method to use (defaults to user's preferred method if not provided).
            amount (Optional[float]): Amount to be paid (defaults to computed amount from order if not provided).

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Payment record created",
                        "payment_id": <str>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Order must exist.
            - The order's user must exist.
            - No existing payment record for this order (only one payment per order).
            - Payment method must be specified or deduced.
            - Amount must be computable or given.
            - Only the user who owns the order can initiate payment.
        """
        # Order must exist
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist" }
    
        order = self.orders[order_id]
        user_id = order["user_id"]

        # User must exist
        if user_id not in self.users:
            return { "success": False, "error": "User associated with order does not exist" }

        # Ensure there isn't already a payment for this order
        for payment in self.payments.values():
            if payment["order_id"] == order_id:
                return { "success": False, "error": "Payment already exists for this order" }
    
        # Payment method
        user_info = self.users[user_id]
        actual_payment_method = payment_method if payment_method is not None else user_info.get("preferred_payment_method")
        if not actual_payment_method:
            return { "success": False, "error": "No payment method provided or configured for user" }
    
        # Amount
        if amount is None:
            # Calculate amount using order's items and product prices
            total = 0.0
            quantities = order.get("quantities", {})
            for pid, qty in quantities.items():
                product = self.products.get(pid)
                if (product is None) or (not product.get("is_available", True)):
                    return { "success": False, "error": f"Product '{pid}' unavailable for pricing" }
                product_price = product.get("price", 0.0)
                total += product_price * qty
            actual_amount = round(total, 2)
        else:
            actual_amount = amount

        # Create unique payment_id
        payment_id = "pay_" + str(uuid.uuid4())

        # Timestamp (ISO format)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        # Create PaymentInfo
        payment_record = {
            "payment_id": payment_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": actual_amount,
            "status": "pending",
            "payment_method": actual_payment_method,
            "timestamp": timestamp
        }
        self.payments[payment_id] = payment_record

        return {
            "success": True,
            "message": "Payment record created",
            "payment_id": payment_id
        }

    def update_payment_status(self, payment_id: str, new_status: str) -> dict:
        """
        Update the status of a payment.

        Args:
            payment_id (str): The unique identifier of the payment to update.
            new_status (str): The desired new status value (e.g., "successful", "failed", "pending").

        Returns:
            dict: {
                "success": True,
                "message": "Payment status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "Payment not found."
            }

        Constraints:
            - Payment with the given payment_id must exist.
            - Status will be set as provided (no enum validation enforced here).
        """
        payment = self.payments.get(payment_id)
        if payment is None:
            return {"success": False, "error": "Payment not found."}

        payment["status"] = new_status
        self.payments[payment_id] = payment  # Explicit update for clarity
        return {"success": True, "message": f"Payment status updated to {new_status}."}

    def advance_order_status(self, order_id: str) -> dict:
        """
        Progress the order's status from 'pending' to 'processing' after confirming successful payment.

        Args:
            order_id (str): The unique identifier of the order to be advanced.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Order status advanced to processing."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The order must exist.
            - The order status must be "pending".
            - There must be at least one successful payment for this order (payment.status == "successful").
            - If order is already not "pending", don't advance.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order does not exist."}

        if order["status"] != "pending":
            return {"success": False, "error": f"Order status is '{order['status']}', not eligible for advancement."}

        # Find any successful payment for this order
        successful_payment_found = False
        for payment in self.payments.values():
            if payment["order_id"] == order_id and payment["status"] == "successful":
                successful_payment_found = True
                break

        if not successful_payment_found:
            return {"success": False, "error": "No successful payment found for this order."}

        # Advance order status to 'processing'
        order["status"] = "processing"
        self.orders[order_id] = order  # Not strictly necessary with mutable dicts, but kept for clarity

        return {"success": True, "message": "Order status advanced to processing."}

    def cancel_order(self, user_id: str, order_id: str) -> dict:
        """
        Cancels an order (if allowed) and returns reserved stock to inventory.
    
        Args:
            user_id (str): The ID of the user attempting to cancel the order.
            order_id (str): The ID of the order to cancel.
    
        Returns:
            dict: {
                "success": True,
                "message": "Order <order_id> canceled successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Only the user who owns the order may cancel it.
            - If products still exist, their stock will be incremented by the reserved quantity.
            - Orders already canceled or completed/delivered cannot be canceled again.
        """
        # Find order
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found."}
    
        # Permission check
        if order["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: not order owner."}
    
        # Check status
        if order["status"] in ("canceled", "delivered", "completed"):
            return {"success": False, "error": f"Order already {order['status']} and cannot be canceled."}

        # Restore product inventory where possible
        for product_id, qty in order["quantities"].items():
            if product_id in self.products:
                self.products[product_id]["stock_quantity"] += qty
                self.products[product_id]["is_available"] = self.products[product_id]["stock_quantity"] > 0
            # If product was deleted after order, do nothing for that product

        # Update order status
        order["status"] = "canceled"

        return {
            "success": True,
            "message": f"Order {order_id} canceled successfully."
        }

    def edit_delivery_slot(self, user_id: str, order_id: str, new_delivery_slot: str) -> dict:
        """
        Update the delivery slot/time for a placed order.

        Args:
            user_id (str): The user's unique identifier requesting the change.
            order_id (str): The order's unique identifier.
            new_delivery_slot (str): The new delivery slot/time string.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Delivery slot updated successfully." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The order must exist.
            - Only the user who owns the order can update its delivery slot.
            - Order status may optionally prevent updates if delivered or cancelled.
        """
        # Check if order exists
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order does not exist." }

        # Enforce that only the order owner can modify
        if order["user_id"] != user_id:
            return { "success": False, "error": "Permission denied: users can only edit their own orders." }

        # Optional: Prevent updates on certain statuses
        if order["status"].lower() in ("delivered", "cancelled", "canceled"):
            return { "success": False, "error": f"Cannot edit delivery slot for orders that are {order['status']}." }

        # Update delivery slot
        order["delivery_slot"] = new_delivery_slot
        self.orders[order_id] = order

        return { "success": True, "message": "Delivery slot updated successfully." }


class OnlineGroceryOrderingSystem(BaseEnv):
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

    def get_product_by_name(self, **kwargs):
        return self._call_inner_tool('get_product_by_name', kwargs)

    def list_products_by_category(self, **kwargs):
        return self._call_inner_tool('list_products_by_category', kwargs)

    def check_product_stock(self, **kwargs):
        return self._call_inner_tool('check_product_stock', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_user_shopping_lists(self, **kwargs):
        return self._call_inner_tool('get_user_shopping_lists', kwargs)

    def get_shopping_list_by_id(self, **kwargs):
        return self._call_inner_tool('get_shopping_list_by_id', kwargs)

    def get_user_shopping_cart(self, **kwargs):
        return self._call_inner_tool('get_user_shopping_cart', kwargs)

    def get_cart_items_and_quantities(self, **kwargs):
        return self._call_inner_tool('get_cart_items_and_quantities', kwargs)

    def get_user_orders(self, **kwargs):
        return self._call_inner_tool('get_user_orders', kwargs)

    def get_order_details(self, **kwargs):
        return self._call_inner_tool('get_order_details', kwargs)

    def get_order_status(self, **kwargs):
        return self._call_inner_tool('get_order_status', kwargs)

    def get_user_payments(self, **kwargs):
        return self._call_inner_tool('get_user_payments', kwargs)

    def get_payment_details(self, **kwargs):
        return self._call_inner_tool('get_payment_details', kwargs)

    def add_item_to_shopping_cart(self, **kwargs):
        return self._call_inner_tool('add_item_to_shopping_cart', kwargs)

    def remove_item_from_shopping_cart(self, **kwargs):
        return self._call_inner_tool('remove_item_from_shopping_cart', kwargs)

    def update_cart_item_quantity(self, **kwargs):
        return self._call_inner_tool('update_cart_item_quantity', kwargs)

    def clear_shopping_cart(self, **kwargs):
        return self._call_inner_tool('clear_shopping_cart', kwargs)

    def create_shopping_list(self, **kwargs):
        return self._call_inner_tool('create_shopping_list', kwargs)

    def add_item_to_shopping_list(self, **kwargs):
        return self._call_inner_tool('add_item_to_shopping_list', kwargs)

    def remove_item_from_shopping_list(self, **kwargs):
        return self._call_inner_tool('remove_item_from_shopping_list', kwargs)

    def place_order(self, **kwargs):
        return self._call_inner_tool('place_order', kwargs)

    def update_product_inventory(self, **kwargs):
        return self._call_inner_tool('update_product_inventory', kwargs)

    def create_payment(self, **kwargs):
        return self._call_inner_tool('create_payment', kwargs)

    def update_payment_status(self, **kwargs):
        return self._call_inner_tool('update_payment_status', kwargs)

    def advance_order_status(self, **kwargs):
        return self._call_inner_tool('advance_order_status', kwargs)

    def cancel_order(self, **kwargs):
        return self._call_inner_tool('cancel_order', kwargs)

    def edit_delivery_slot(self, **kwargs):
        return self._call_inner_tool('edit_delivery_slot', kwargs)
