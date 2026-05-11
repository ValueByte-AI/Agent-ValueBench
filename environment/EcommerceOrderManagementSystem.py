# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ProductInfo(TypedDict):
    product_id: str
    name: str
    price: float
    stock_quantity: int

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    email: str
    account_sta: str  # possibly meant to be 'account_status'

class OrderItemInfo(TypedDict):
    order_id: str
    product_id: str
    quantity: int

class OrderInfo(TypedDict):
    order_id: str
    customer_id: str
    status: str
    order_date: str
    order_item: List[OrderItemInfo]

class _GeneratedEnvImpl:
    def __init__(self):
        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Mapping from order_id to list of its order item(s)
        # OrderItems: {order_id: List[OrderItemInfo]}
        self.order_items: Dict[str, List[OrderItemInfo]] = {}

        # Constraints:
        # - Each order is associated with exactly one customer.
        # - Only customers can view the status of their own orders.
        # - Each order must have at least one associated product (via OrderItem).
        # - Order status values must be from a defined set (e.g., pending, shipped, delivered, cancelled).

    def _get_effective_order_items(self, order_id: str) -> List[OrderItemInfo]:
        """
        Resolve order items for an order.

        Formal cases sometimes only populate the canonical `orders[order_id]["order_item"]`
        field and omit the mirrored `order_items[order_id]` mapping. Read tools should still
        return the order's actual items in that situation.
        """
        if order_id in self.order_items:
            return self.order_items[order_id]
        order = self.orders.get(order_id)
        if not order:
            return []
        raw_items = order.get("order_item", [])
        if isinstance(raw_items, list):
            return raw_items
        return []

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer information using the customer's unique identifier.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict:
              On success: {
                  "success": True,
                  "data": CustomerInfo  # Dictionary of customer info
              }
              On failure: {
                  "success": False,
                  "error": "Customer not found"
              }
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def get_customer_by_email(self, email: str) -> dict:
        """
        Retrieve customer information using the provided email address.

        Args:
            email (str): The customer's email address.

        Returns:
            dict:
                {
                    "success": True,
                    "data": CustomerInfo  # The found customer's information
                }
                or
                {
                    "success": False,
                    "error": "Customer with the given email does not exist"
                }

        Constraints:
            - Email is expected to be unique among customers.
            - If no customer has the given email, the operation fails.
        """
        for customer in self.customers.values():
            if customer["email"] == email:
                return {"success": True, "data": customer}
        return {"success": False, "error": "Customer with the given email does not exist"}

    def get_orders_by_customer(self, customer_id: str) -> dict:
        """
        Retrieve a list of all orders belonging to a specific customer.

        Args:
            customer_id (str): The customer's unique ID.

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo]  # list of orders for the customer (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # error message, e.g. customer does not exist
            }
    
        Constraints:
            - Customer must exist.
            - Each order is associated with exactly one customer.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist" }
    
        customer_orders = [
            order for order in self.orders.values()
            if order["customer_id"] == customer_id
        ]
        return { "success": True, "data": customer_orders }

    def get_order_by_id(self, order_id: str) -> dict:
        """
        Retrieve order details (OrderInfo) including customer_id, status, order_date, and order_item list,
        given an order_id.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": OrderInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Order not found"
                    }

        Constraints:
            - order_id must refer to a valid existing order.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }
        return { "success": True, "data": order }

    def verify_order_ownership(self, order_id: str, customer_id: str) -> dict:
        """
        Check if a given order_id is owned by a specific customer_id.

        Args:
            order_id (str): The order's unique identifier.
            customer_id (str): The supposed owner's customer_id.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "owned": bool  # True if the order belongs to the customer, else False
                    }
                On failure (order not found):
                    {
                        "success": False,
                        "error": "Order does not exist"
                    }

        Constraints:
            - Each order is associated with exactly one customer.
        """
        order = self.orders.get(order_id)
        if order is None:
            return { "success": False, "error": "Order does not exist" }
        owned = (order["customer_id"] == customer_id)
        return { "success": True, "owned": owned }

    def get_order_status(self, order_id: str, customer_id: str) -> dict:
        """
        Return the current status of an order, if and only if the requesting customer owns this order.

        Args:
            order_id (str): The ID of the order to query.
            customer_id (str): The ID of the customer making the request.

        Returns:
            dict: 
                { "success": True, "data": { "order_id": str, "status": str } }
                OR
                { "success": False, "error": str } if order not found or not owned by the customer.

        Constraints:
            - Only the customer who owns the order may query its status.
            - The order must exist.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order does not exist" }
        if order["customer_id"] != customer_id:
            return { "success": False, "error": "Permission denied: This order does not belong to the requesting customer." }
        return { 
            "success": True, 
            "data": {
                "order_id": order_id,
                "status": order["status"]
            }
        }

    def get_order_item_list(self, order_id: str) -> dict:
        """
        Retrieve the list of OrderItemInfo objects associated with a particular order.

        Args:
            order_id (str): The unique ID of the order.

        Returns:
            dict: {
                "success": True,
                "data": List[OrderItemInfo]  # May be empty (but constraints suggest at least 1)
            }
            or
            {
                "success": False,
                "error": str  # Reason the operation failed (e.g., order does not exist)
            }

        Constraints:
            - The provided order_id must correspond to an existing order.
            - Each order should have at least one associated OrderItemInfo.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order does not exist"}

        items = self._get_effective_order_items(order_id)
        return {"success": True, "data": items}

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve product details for the given product_id.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict: If found, returns {
                      "success": True,
                      "data": ProductInfo
                  }
                  If not found, returns {
                      "success": False,
                      "error": "Product not found"
                  }

        Constraints:
            - The given product_id must exist in the products dictionary.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": self.products[product_id]}

    def get_products_for_order(self, order_id: str) -> dict:
        """
        Retrieve product details for all products (with quantities) in a specific order.

        Args:
            order_id (str): ID of the order.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[dict]  # Each dict includes: product info, and quantity ordered
                }
                OR
                {
                    "success": False,
                    "error": str  # error message describing the failure
                }

        Constraints:
            - order_id must exist and be associated with at least one OrderItem.
            - Product must exist in the system.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order does not exist"}

        order_items = self._get_effective_order_items(order_id)
        if not order_items:
            return {"success": False, "error": "No items associated with this order"}

        result = []
        for item in order_items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            product_info = self.products.get(product_id)
            if not product_info:
                # Skip missing product, but log the error in a special way
                result.append({
                    "product_id": product_id,
                    "error": "Product not found in system",
                    "quantity": quantity
                })
                continue

            # Combine product info with ordered quantity
            prod_and_qty = dict(product_info)
            prod_and_qty["quantity_ordered"] = quantity
            result.append(prod_and_qty)

        return {"success": True, "data": result}

    def list_allowed_order_statuses(self) -> dict:
        """
        Return the list of valid order status values that orders can have.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": list of str,  # e.g. ["pending", "shipped", "delivered", "cancelled"]
            }
        Constraints:
            - Status list is defined by system convention and does not change per-request.
            - No input required.
        """
        allowed_statuses = ["pending", "shipped", "delivered", "cancelled"]
        return {
            "success": True,
            "data": allowed_statuses
        }

    def update_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Change the status of an order, enforcing allowed transitions and validation.
    
        Args:
            order_id (str): The ID of the order to update.
            new_status (str): One of the allowed status values ('pending', 'shipped', 'delivered', 'cancelled').
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Order status updated to <new_status>" }
                On failure: { "success": False, "error": "reason" }
    
        Constraints:
            - Order must exist.
            - new_status must be one of allowed values.
            - Status transition must obey allowed rules:
                * Allowed: 
                    - pending → shipped, pending → cancelled
                    - shipped → delivered, shipped → cancelled
                * Not allowed:
                    - Any transition from delivered or cancelled (final states)
                    - Any transition not listed above
        """
        allowed_statuses = {'pending', 'shipped', 'delivered', 'cancelled'}
        allowed_transitions = {
            'pending': {'shipped', 'cancelled'},
            'shipped': {'delivered', 'cancelled'},
            'delivered': set(),  # Final state
            'cancelled': set(),  # Final state
        }

        # Order existence
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist" }

        # Status value
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed values: {sorted(allowed_statuses)}" }

        order = self.orders[order_id]
        current_status = order["status"]

        if current_status == new_status:
            return { "success": False, "error": f"Order already has status '{new_status}'" }

        if new_status not in allowed_transitions.get(current_status, set()):
            return { 
                "success": False, 
                "error": f"Cannot change status from '{current_status}' to '{new_status}'"
            }

        # Perform update
        order["status"] = new_status
        self.orders[order_id] = order

        return { "success": True, "message": f"Order status updated to '{new_status}'" }

    def create_order(
        self, 
        order_id: str, 
        customer_id: str, 
        order_items: list,  # List[dict] with keys: product_id, quantity
        status: str, 
        order_date: str
    ) -> dict:
        """
        Add a new order for a customer, with initial status and products.

        Args:
            order_id (str): Unique order identifier.
            customer_id (str): Customer placing the order.
            order_items (List[dict]): [{ "product_id": str, "quantity": int }...] List of order items.
            status (str): Initial status for the order (must be allowed).
            order_date (str): Date/time when the order is placed.

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
            - order_id must be unique.
            - customer_id must exist.
            - status must be one of allowed values.
            - order_items must be non-empty, all product IDs must exist, quantities > 0.
        """
        # Allowed statuses
        allowed_statuses = {"pending", "shipped", "delivered", "cancelled"}

        if order_id in self.orders:
            return { "success": False, "error": "Order ID already exists." }

        if customer_id not in self.customers:
            return { "success": False, "error": "Customer not found." }

        if status not in allowed_statuses:
            return { "success": False, "error": f"Order status '{status}' is not allowed." }

        if not order_items or not isinstance(order_items, list):
            return { "success": False, "error": "Order must contain at least one product." }

        created_items = []
        for item in order_items:
            if (
                "product_id" not in item or
                "quantity" not in item or
                not isinstance(item["quantity"], int)
            ):
                return { "success": False, "error": "Invalid order item data." }
            product_id = item["product_id"]
            quantity = item["quantity"]
            if product_id not in self.products:
                return { "success": False, "error": f"Product '{product_id}' does not exist." }
            if quantity <= 0:
                return { "success": False, "error": f"Quantity for product '{product_id}' must be positive." }
            created_items.append({
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity
            })
    
        # Build and store the order & its items
        order_info = {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": status,
            "order_date": order_date,
            "order_item": created_items  # full list of OrderItemInfo
        }
        self.orders[order_id] = order_info
        self.order_items[order_id] = created_items

        return {
            "success": True,
            "message": f"Order '{order_id}' created for customer '{customer_id}'."
        }

    def update_order_items(self, order_id: str, new_items: list) -> dict:
        """
        Change the list or quantities of items in an order.

        Args:
            order_id (str): The order whose items are to be updated.
            new_items (list of dict): Each dict contains:
                product_id (str): Product identifier.
                quantity (int): Quantity for that product (> 0).

        Returns:
            dict: {
                "success": True,
                "message": "Order items updated for order_id=<...>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The order must exist.
            - Each new item product_id must exist in products.
            - Each quantity must be positive integer.
            - new_items must not be empty (order must have at least one product).
            - No duplicate product_ids within new_items.
        """
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist" }
    
        if not isinstance(new_items, list) or len(new_items) == 0:
            return { "success": False, "error": "Order must contain at least one product" }
    
        seen_product_ids = set()
        for item in new_items:
            if not isinstance(item, dict):
                return { "success": False, "error": "Each item must be a dict with 'product_id' and 'quantity'" }
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            if not product_id or product_id not in self.products:
                return { "success": False, "error": f"Product ID '{product_id}' does not exist" }
            if not isinstance(quantity, int) or quantity <= 0:
                return { "success": False, "error": f"Invalid quantity '{quantity}' for product '{product_id}'" }
            if product_id in seen_product_ids:
                return { "success": False, "error": f"Duplicate product_id '{product_id}' in items" }
            seen_product_ids.add(product_id)
    
        # Build new OrderItemInfo list
        updated_order_items = []
        for item in new_items:
            updated_order_items.append({
                "order_id": order_id,
                "product_id": item["product_id"],
                "quantity": item["quantity"]
            })

        # Update in-memory structures
        self.order_items[order_id] = updated_order_items
        self.orders[order_id]["order_item"] = updated_order_items

        return { "success": True, "message": f"Order items updated for order_id={order_id}" }

    def delete_order(self, order_id: str) -> dict:
        """
        Permanently remove an order and its order items from the system.

        Args:
            order_id (str): The unique identifier of the order to be deleted.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Order <order_id> and its items have been deleted." }
                - On failure: { "success": False, "error": "Order not found" }

        Constraints:
            - Order must exist for deletion.
            - All order items associated with that order are also removed.
            - After deletion, the order and its items are not recoverable.
        """
        if order_id not in self.orders:
            return { "success": False, "error": "Order not found" }
    
        # Delete the order itself
        del self.orders[order_id]
    
        # Delete the order items associated with this order, if any
        if order_id in self.order_items:
            del self.order_items[order_id]
    
        return {
            "success": True,
            "message": f"Order {order_id} and its items have been deleted."
        }

    def update_product_stock(self, product_id: str, delta_quantity: int) -> dict:
        """
        Modify the available stock quantity for the specified product.

        Args:
            product_id (str): The unique identifier for the product.
            delta_quantity (int): The amount to change the stock by.
                                  Positive to increase, negative to decrease.

        Returns:
            dict: 
                If success:
                    { "success": True, "message": "Product <id> stock updated from <old> to <new>." }
                If failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Product must exist.
            - Stock quantity after update must not be negative.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        current_stock = product['stock_quantity']
        new_stock = current_stock + delta_quantity
        if new_stock < 0:
            return { "success": False, "error": "Insufficient stock: cannot set stock below zero" }
        product['stock_quantity'] = new_stock
        self.products[product_id] = product
        return {
            "success": True,
            "message": f"Product {product_id} stock updated from {current_stock} to {new_stock}."
        }

    def create_customer_account(
        self, 
        customer_id: str, 
        name: str, 
        email: str, 
        account_sta: str
    ) -> dict:
        """
        Add a new customer record to the system.

        Args:
            customer_id (str): The unique ID for the new customer.
            name (str): The customer's name.
            email (str): The customer's email address (must be unique).
            account_sta (str): Account status string.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "message": "Customer account created."
                    }
                On failure (duplicate email or customer_id, or missing arguments):
                    {
                      "success": False,
                      "error": str
                    }

        Constraints:
            - customer_id must be unique.
            - email must be unique among customers.
            - Required fields must not be empty.
        """
        # Check for required fields
        if not all([customer_id, name, email, account_sta]):
            return {"success": False, "error": "All customer fields are required."}
    
        # Enforce unique customer_id
        if customer_id in self.customers:
            return {"success": False, "error": "Customer ID already exists."}
    
        # Enforce unique email
        for customer in self.customers.values():
            if customer["email"] == email:
                return {"success": False, "error": "Email already in use."}
    
        # Add the customer
        customer_info = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "account_sta": account_sta
        }
        self.customers[customer_id] = customer_info
        return {"success": True, "message": "Customer account created."}

    def update_customer_info(
        self,
        customer_id: str,
        name: str = None,
        email: str = None,
        account_sta: str = None
    ) -> dict:
        """
        Update customer account information for the specified customer.

        Args:
            customer_id (str): Unique identifier of the customer to update.
            name (str, optional): New name for the customer.
            email (str, optional): New email address (must not duplicate another customer's email).
            account_sta (str, optional): New account status value.

        Returns:
            dict: {
                "success": True,
                "message": "Customer info updated successfully."
            } on success,
            or
            {
                "success": False,
                "error": <description>
            } on failure.

        Constraints:
            - customer_id must exist.
            - If email is provided, it must not be taken by another customer.
            - At least one updatable field must be given.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist." }

        if name is None and email is None and account_sta is None:
            return { "success": False, "error": "No update fields provided." }

        # Check for duplicate email (if changed)
        if email is not None:
            for cid, customer in self.customers.items():
                if cid != customer_id and customer["email"].lower() == email.lower():
                    return { "success": False, "error": "Email already in use by another customer." }

        customer = self.customers[customer_id]

        if name is not None:
            customer["name"] = name
        if email is not None:
            customer["email"] = email
        if account_sta is not None:
            customer["account_sta"] = account_sta

        self.customers[customer_id] = customer
        return { "success": True, "message": "Customer info updated successfully." }


class EcommerceOrderManagementSystem(BaseEnv):
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

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def get_customer_by_email(self, **kwargs):
        return self._call_inner_tool('get_customer_by_email', kwargs)

    def get_orders_by_customer(self, **kwargs):
        return self._call_inner_tool('get_orders_by_customer', kwargs)

    def get_order_by_id(self, **kwargs):
        return self._call_inner_tool('get_order_by_id', kwargs)

    def verify_order_ownership(self, **kwargs):
        return self._call_inner_tool('verify_order_ownership', kwargs)

    def get_order_status(self, **kwargs):
        return self._call_inner_tool('get_order_status', kwargs)

    def get_order_item_list(self, **kwargs):
        return self._call_inner_tool('get_order_item_list', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def get_products_for_order(self, **kwargs):
        return self._call_inner_tool('get_products_for_order', kwargs)

    def list_allowed_order_statuses(self, **kwargs):
        return self._call_inner_tool('list_allowed_order_statuses', kwargs)

    def update_order_status(self, **kwargs):
        return self._call_inner_tool('update_order_status', kwargs)

    def create_order(self, **kwargs):
        return self._call_inner_tool('create_order', kwargs)

    def update_order_items(self, **kwargs):
        return self._call_inner_tool('update_order_items', kwargs)

    def delete_order(self, **kwargs):
        return self._call_inner_tool('delete_order', kwargs)

    def update_product_stock(self, **kwargs):
        return self._call_inner_tool('update_product_stock', kwargs)

    def create_customer_account(self, **kwargs):
        return self._call_inner_tool('create_customer_account', kwargs)

    def update_customer_info(self, **kwargs):
        return self._call_inner_tool('update_customer_info', kwargs)
