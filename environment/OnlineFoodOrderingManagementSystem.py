# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import time
import uuid
from typing import List, Dict, Any



# --- TypedDicts ---

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    address: str  # From "add" (assumed typo)

class MenuItemInfo(TypedDict):
    menu_item_id: str
    name: str
    description: str
    price: float
    availability_status: str  # From "availability_sta" (assumed typo)

class OrderItemInfo(TypedDict):
    order_id: str
    menu_item_id: str
    quantity: int
    item_price: float  # From "item_pric" (assumed typo)

class DeliveryInfo(TypedDict):
    order_id: str
    delivery_address: str
    delivery_time: str
    delivery_status: str
    delivery_person_id: str

class OrderInfo(TypedDict):
    order_id: str
    customer_id: str
    status: str
    order_time: str
    delivery_info: DeliveryInfo
    order_items: List[OrderItemInfo]

# --- Environment Class ---

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing online food ordering, orders, menu items, customers, order items and delivery info.
        """

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}
        # MenuItems: {menu_item_id: MenuItemInfo}
        self.menu_items: Dict[str, MenuItemInfo] = {}
        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}
        # OrderItems: {order_id: List[OrderItemInfo]}
        self.order_items: Dict[str, List[OrderItemInfo]] = {}
        # DeliveryInfo: {order_id: DeliveryInfo}
        self.delivery_info: Dict[str, DeliveryInfo] = {}

        # --- Constraints/Notes ---
        # - Each order is associated with precisely one customer (OrderInfo.customer_id).
        # - Each order consists of one or more order items, each linked to a valid menu item (OrderItemInfo, MenuItemInfo).
        # - Order status must reflect valid states (e.g., "pending", "preparing", "out for delivery", "delivered", "cancelled").
        # - Only available menu items (MenuItemInfo.availability_status) can be ordered.
        # - Retrieval operations should support pagination (page size, page number parameters).
        # - Customer private details must be securely stored and accessed according to privacy policies.


    def list_orders_paginated(self, page_number: int, page_size: int) -> dict:
        """
        Retrieve a paginated list of orders.
        Each order entry contains: order_id, customer details (id and name only), and order status.

        Args:
            page_number (int): 1-based page index (must be >=1)
            page_size (int): Number of orders per page (must be >=1)

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "order_id": str,
                    "customer": { "customer_id": str, "name": str },
                    "status": str
                }]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only permissible fields from customer info are returned (customer_id and name).
            - Pagination is supported.
            - If page_number is out of range (no orders on that page), returns an empty list with success.
        """
        # Validate input
        if not (isinstance(page_number, int) and page_number >= 1):
            return { "success": False, "error": "Invalid page_number (must be >=1)" }
        if not (isinstance(page_size, int) and page_size >= 1):
            return { "success": False, "error": "Invalid page_size (must be >=1)" }

        order_list = list(self.orders.values())
        total_orders = len(order_list)
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size

        # If start_idx >= total_orders, page is out of range; return empty list, success.
        if start_idx >= total_orders:
            return { "success": True, "data": [] }

        paged_orders = order_list[start_idx:end_idx]
        result = []
        for order in paged_orders:
            customer_id = order.get("customer_id")
            customer = self.customers.get(customer_id, {"customer_id": customer_id, "name": ""})
            customer_out = {"customer_id": customer.get("customer_id", ""), "name": customer.get("name", "")}
            result.append({
                "order_id": order.get("order_id", ""),
                "customer": customer_out,
                "status": order.get("status", "")
            })

        return { "success": True, "data": result }

    def get_order_details(self, order_id: str) -> dict:
        """
        Retrieve all details for a specific order, given its order ID, including customer details, order items, and delivery info.

        Args:
            order_id (str): The order ID to look up.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": {
                        "order": OrderInfo,
                        "customer": CustomerInfo,
                        "order_items": List[OrderItemInfo],
                        "delivery_info": DeliveryInfo
                    }
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Fails if order_id does not exist.
            - May omit sub-objects if not present, but only order_id absence triggers an error.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order not found"}

        order = self.orders[order_id]
        customer_id = order["customer_id"]
        customer = self.customers.get(customer_id)
        order_items = self.order_items.get(order_id, [])
        delivery_info = self.delivery_info.get(order_id)

        # Bundle all details, None if any component missing (except order itself)
        details = {
            "order": order,
            "customer": customer,
            "order_items": order_items,
            "delivery_info": delivery_info
        }
        return {"success": True, "data": details}

    def list_customer_orders_paginated(
        self, 
        customer_id: str, 
        page_number: int, 
        page_size: int
    ) -> dict:
        """
        Retrieve a paginated list of all orders for a specific customer.

        Args:
            customer_id (str): The unique ID of the customer.
            page_number (int): The current page number (1-based, must be >=1).
            page_size (int): How many orders per page (must be >=1).

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo],  # List of orders for the customer (size=min(page_size, rest))
            }
            or
            {
                "success": False,
                "error": str,  # Error reason.
            }
        Constraints:
            - The customer must exist in the system.
            - page_number and page_size must be positive integers.
            - Retrieval is paginated.
        """
        # Check customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}
    
        if not isinstance(page_number, int) or page_number < 1 or not isinstance(page_size, int) or page_size < 1:
            return {"success": False, "error": "Invalid pagination parameters"}
    
        # Filter orders for this customer
        customer_orders = [
            order_info 
            for order_info in self.orders.values()
            if order_info["customer_id"] == customer_id
        ]

        # Sort orders by order_time, newest first (optional, but usually desired)
        customer_orders.sort(key=lambda x: x["order_time"], reverse=True)

        # Pagination calculation
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size
        paginated_orders = customer_orders[start_idx:end_idx]

        return {"success": True, "data": paginated_orders}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve detailed information about a customer by customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": CustomerInfo  # name, contact_info, address, customer_id
                }
                On failure:
                {
                    "success": False,
                    "error": "Customer not found"
                }
    
        Constraints:
            - If customer_id does not exist, returns error.
            - Customer information should be accessed in compliance with privacy policies; this function assumes appropriate access rights.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer not found" }
        # (Optionally: If privacy fields need redacting, apply here. Assuming all info is permissible.)
        return { "success": True, "data": customer }

    def get_customer_by_name(self, name: str) -> dict:
        """
        Retrieve customer details using customer name, observing privacy rules.

        Args:
            name (str): Customer name (case-insensitive; leading/trailing whitespace ignored).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[CustomerInfo]  # list may be empty if no such customer found
                    }
                - On error:
                    {
                        "success": False,
                        "error": str
                    }
        Privacy:
            - Customer private details are only returned as stored in CustomerInfo.
        """
        name_query = name.strip().lower()
        results = [
            customer
            for customer in self.customers.values()
            if customer["name"].strip().lower() == name_query
        ]
        return {
            "success": True,
            "data": results
        }

    def list_menu_items(self) -> dict:
        """
        Returns a list of all menu items with their status (including availability).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MenuItemInfo],  # List of all menu items (can be empty)
            }
        """
        items = list(self.menu_items.values())
        return { "success": True, "data": items }

    def get_menu_item_by_id(self, menu_item_id: str) -> dict:
        """
        Retrieve details for a specified menu item by menu_item_id.

        Args:
            menu_item_id (str): Unique ID of the menu item to query.

        Returns:
            dict: 
              - On success: {"success": True, "data": MenuItemInfo}
              - On failure: {"success": False, "error": "Menu item not found"}

        Constraints:
            - menu_item_id must exist in the menu_items collection.
        """
        if menu_item_id not in self.menu_items:
            return { "success": False, "error": "Menu item not found" }
    
        return { "success": True, "data": self.menu_items[menu_item_id] }

    def list_order_items(self, order_id: str) -> dict:
        """
        List all items and their quantities for a specific order.

        Args:
            order_id (str): The unique identifier of the order.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "data": List[OrderItemInfo],  # The itemization for the order (can be an empty list)
                    }
                - If order does not exist:
                    {
                        "success": False,
                        "error": "Order does not exist"
                    }

        Constraints:
            - order_id must correspond to an Order in the system.
            - OrderItems may be empty due to data error, but should be listed if present.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order does not exist"}

        items = self.order_items.get(order_id, [])
        return {"success": True, "data": items}

    def get_delivery_info(self, order_id: str) -> dict:
        """
        Retrieve delivery information for a given order.

        Args:
            order_id (str): ID of the order whose delivery information is required.

        Returns:
            dict: {
                "success": True,
                "data": DeliveryInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The specified order_id must exist in the system.
            - DeliveryInfo for the order must exist.

        Edge Cases:
            - If order_id does not exist, return error.
            - If delivery information for the order does not exist, return error.
        """
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist" }
        if order_id not in self.delivery_info:
            return { "success": False, "error": "Delivery info does not exist for given order" }
        return {
            "success": True,
            "data": self.delivery_info[order_id]
        }

    def list_orders_by_status_paginated(
        self,
        status: str,
        page_size: int,
        page_number: int
    ) -> dict:
        """
        Paginated listing of orders with the specified status.

        Args:
            status (str): Target order status (e.g., "pending", "delivered").
            page_size (int): Number of results per page (must be positive).
            page_number (int): Page number (1-based, must be positive).

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo],           # Page of matching orders
                "total_count": int,                # Total number of orders with this status
                "page_number": int,                # The current page number
                "page_size": int                   # The requested page size
            }
            OR
            {
                "success": False,
                "error": str                       # Reason for failure
            }

        Constraints:
            - Only valid status types are allowed.
            - Pagination: positive page_size and page_number.
        """
        valid_statuses = {"pending", "preparing", "out for delivery", "delivered", "cancelled"}

        if status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{status}'."}
        if not isinstance(page_size, int) or not isinstance(page_number, int) or page_size <= 0 or page_number <= 0:
            return {"success": False, "error": "page_size and page_number must be positive integers."}

        # Filter orders by status
        filtered_orders = [order for order in self.orders.values() if order["status"] == status]
        total_count = len(filtered_orders)

        # Pagination
        start = (page_number - 1) * page_size
        end = start + page_size

        # Return empty list if start is beyond range, but still success
        page_slice = filtered_orders[start:end] if start < total_count else []

        return {
            "success": True,
            "data": page_slice,
            "total_count": total_count,
            "page_number": page_number,
            "page_size": page_size
        }

    def update_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Change the status of an order to one of the allowed states.

        Args:
            order_id (str): The ID of the order whose status needs updating.
            new_status (str): The new status value. Allowed values: 
                "pending", "preparing", "out for delivery", "delivered", "cancelled".

        Returns:
            dict:
                - On success: { "success": True, "message": "Order status updated to <new_status>." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The order_id must exist.
            - The new_status must be one of the allowed states.
        """
        allowed_statuses = {"pending", "preparing", "out for delivery", "delivered", "cancelled"}

        if order_id not in self.orders:
            return { "success": False, "error": "Order ID does not exist." }

        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid order status value." }

        self.orders[order_id]["status"] = new_status
        return { "success": True, "message": f"Order status updated to {new_status}." }


    def create_order(self, customer_id: str, order_items: List[Dict[str, Any]]) -> dict:
        """
        Place a new order for a customer with specified order items (only available menu items).

        Args:
            customer_id (str): The ID of the customer placing the order.
            order_items (List[Dict]): Each dict must include:
                - menu_item_id (str)
                - quantity (int > 0)

        Returns:
            dict:
                - On success: {"success": True, "message": "Order created", "order_id": <order_id>}
                - On failure: {"success": False, "error": <reason string>}

        Constraints:
            - Only available menu items can be ordered.
            - Menu items must exist.
            - Quantities must be positive integers.
            - Each order is associated with one customer and has at least one order item.
        """

        # Validate customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Invalid customer_id"}

        if not order_items or not isinstance(order_items, list):
            return {"success": False, "error": "Order must include at least one order item"}

        parsed_order_items = []
        seen_menu_items = set()

        for idx, item in enumerate(order_items):
            menu_item_id = item.get("menu_item_id")
            quantity = item.get("quantity")
            if not menu_item_id or type(quantity) is not int or quantity <= 0:
                return {"success": False, "error": f"Invalid order item at position {idx+1}: missing or invalid menu_item_id/quantity"}
            if menu_item_id in seen_menu_items:
                return {"success": False, "error": f"Duplicate menu_item_id '{menu_item_id}' in order items"}
            seen_menu_items.add(menu_item_id)
            # Check menu item exists and is available
            menu_item = self.menu_items.get(menu_item_id)
            if not menu_item:
                return {"success": False, "error": f"Menu item '{menu_item_id}' not found"}
            if menu_item["availability_status"] != "available":
                return {"success": False, "error": f"Menu item '{menu_item_id}' is not available"}
            parsed_order_items.append({
                'order_id': '',  # To be filled after order_id assigned
                'menu_item_id': menu_item_id,
                'quantity': quantity,
                'item_price': menu_item['price']
            })

        # Generate unique order_id
        order_id = str(uuid.uuid4())

        # Assign order_id to each order_item
        for oi in parsed_order_items:
            oi['order_id'] = order_id

        # Prepare delivery info (unfilled or placeholder as appropriate)
        delivery_info = {
            'order_id': order_id,
            'delivery_address': self.customers[customer_id]['address'],
            'delivery_time': "",  # unknown at order creation
            'delivery_status': "pending",
            'delivery_person_id': ""
        }

        # Compose order info
        now_timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        order_info = {
            'order_id': order_id,
            'customer_id': customer_id,
            'status': "pending",
            'order_time': now_timestr,
            'delivery_info': delivery_info,
            'order_items': parsed_order_items
        }

        # Update environment state
        self.orders[order_id] = order_info
        self.order_items[order_id] = parsed_order_items
        self.delivery_info[order_id] = delivery_info

        return {
            "success": True,
            "message": "Order created",
            "order_id": order_id
        }

    def update_order_items(self, order_id: str, new_items: list) -> dict:
        """
        Modify the order items or quantities for an existing order.

        Args:
            order_id (str): ID of the order to update.
            new_items (list): List of dicts, each: { 'menu_item_id': str, 'quantity': int }.
                - Must not be empty (order must have ≥1 item).
                - Each menu_item_id must exist and be available.
                - Each quantity must be > 0.
                - No duplicate menu_item_id allowed in new_items.

        Returns:
            dict:
                { "success": True, "message": "Order items updated for order <order_id>." }
                or
                { "success": False, "error": "<error description>" }
        """

        if order_id not in self.orders:
            return { "success": False, "error": "Order not found" }

        if not isinstance(new_items, list) or len(new_items) == 0:
            return { "success": False, "error": "At least one order item is required" }

        seen_ids = set()
        processed_items = []

        for item in new_items:
            menu_item_id = item.get("menu_item_id")
            quantity = item.get("quantity")

            if not menu_item_id or not isinstance(menu_item_id, str):
                return { "success": False, "error": "Invalid or missing menu_item_id in order items" }

            if menu_item_id in seen_ids:
                return { "success": False, "error": f"Duplicate menu_item_id '{menu_item_id}' in order items" }
            seen_ids.add(menu_item_id)

            if menu_item_id not in self.menu_items:
                return { "success": False, "error": f"Menu item '{menu_item_id}' does not exist" }

            menu_item = self.menu_items[menu_item_id]
            if menu_item["availability_status"] != "available":
                return { "success": False, "error": f"Menu item '{menu_item_id}' is not available" }
            if not isinstance(quantity, int) or quantity <= 0:
                return { "success": False, "error": f"Invalid quantity for menu item '{menu_item_id}'" }

            processed_items.append({
                "order_id": order_id,
                "menu_item_id": menu_item_id,
                "quantity": quantity,
                "item_price": menu_item["price"]
            })

        # Replace order items for this order
        self.order_items[order_id] = processed_items

        # If present, update in the order info as well (for consistency)
        if "order_items" in self.orders[order_id]:
            self.orders[order_id]["order_items"] = processed_items

        return { "success": True, "message": f"Order items updated for order {order_id}." }

    def cancel_order(self, order_id: str) -> dict:
        """
        Set an order's status to "cancelled", if allowed by business logic.

        Args:
            order_id (str): The unique identifier of the order to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Order <order_id> status set to cancelled"
            }
            or
            {
                "success": False,
                "error": str  # Reason why operation failed (non-existent order, non-cancellable status, etc.)
            }

        Constraints:
            - Only orders not already in a terminal status (e.g., "delivered", "cancelled") can be cancelled.
            - Order must exist.
        """

        # Check order existence
        if order_id not in self.orders:
            return {"success": False, "error": f"Order {order_id} does not exist."}

        order = self.orders[order_id]
        current_status = order["status"]

        # Define non-cancellable (terminal) statuses
        terminal_statuses = {"delivered", "cancelled"}

        if current_status in terminal_statuses:
            return {
                "success": False,
                "error": f"Cannot cancel order in status '{current_status}'."
            }

        # Set order status to 'cancelled'
        order["status"] = "cancelled"
        self.orders[order_id] = order

        return {
            "success": True,
            "message": f"Order {order_id} status set to cancelled"
        }

    def update_menu_item_availability(self, menu_item_id: str, new_status: str) -> dict:
        """
        Change the availability status of a menu item (affecting whether it can be ordered).
    
        Args:
            menu_item_id (str): The ID of the menu item to be updated.
            new_status (str): The new availability status ('available' or 'unavailable').
    
        Returns:
            dict: {
                "success": True,
                "message": "Availability status updated for menu item <menu_item_id>."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }
    
        Constraints:
            - menu_item_id must exist.
            - new_status must be "available" or "unavailable".
        """
        # Check if menu item exists
        if menu_item_id not in self.menu_items:
            return {
                "success": False,
                "error": f"Menu item with id '{menu_item_id}' does not exist."
            }

        # Only allow these statuses
        valid_statuses = {"available", "unavailable"}
        if new_status not in valid_statuses:
            return {
                "success": False,
                "error": "Invalid status. Only 'available' or 'unavailable' are allowed."
            }

        # Update the menu item's availability status
        self.menu_items[menu_item_id]["availability_status"] = new_status

        return {
            "success": True,
            "message": f"Availability status updated for menu item {menu_item_id}."
        }

    def update_customer_info(
        self,
        customer_id: str,
        name: Optional[str] = None,
        contact_info: Optional[str] = None,
        address: Optional[str] = None
    ) -> dict:
        """
        Update the details of a customer.

        Args:
            customer_id (str): Unique identifier of the customer.
            name (Optional[str]): New name for the customer. If None, do not update.
            contact_info (Optional[str]): New contact info. If None, do not update.
            address (Optional[str]): New address. If None, do not update.

        Returns:
            dict: {
                "success": True,
                "message": "Customer information updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The customer_id must exist.
            - At least one updatable field must be provided.
            - Privacy and authorization are assumed managed elsewhere.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist."}

        if all(val is None for val in [name, contact_info, address]):
            return {"success": False, "error": "No fields to update provided."}

        customer = self.customers[customer_id]

        if name is not None:
            customer["name"] = name
        if contact_info is not None:
            customer["contact_info"] = contact_info
        if address is not None:
            customer["address"] = address

        self.customers[customer_id] = customer

        return {"success": True, "message": "Customer information updated."}

    def update_delivery_info(
        self, 
        order_id: str,
        delivery_address: str = None,
        delivery_time: str = None,
        delivery_status: str = None,
        delivery_person_id: str = None
    ) -> dict:
        """
        Update delivery details for a given order.

        Args:
            order_id (str): The ID of the order whose delivery info is to be updated.
            delivery_address (str, optional): New delivery address.
            delivery_time (str, optional): New scheduled delivery time.
            delivery_status (str, optional): Updated delivery status.
            delivery_person_id (str, optional): New assigned delivery person ID.

        Returns:
            dict: {
                "success": True,
                "message": "Updated delivery info fields: <comma-separated list>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - order_id must exist and have delivery info.
            - At least one delivery field must be provided to update.
        """
        if order_id not in self.orders:
            return { "success": False, "error": "Order not found." }

        if order_id not in self.delivery_info:
            return { "success": False, "error": "Delivery info for this order does not exist." }

        fields_to_update = {}
        if delivery_address is not None:
            fields_to_update["delivery_address"] = delivery_address
        if delivery_time is not None:
            fields_to_update["delivery_time"] = delivery_time
        if delivery_status is not None:
            fields_to_update["delivery_status"] = delivery_status
        if delivery_person_id is not None:
            fields_to_update["delivery_person_id"] = delivery_person_id

        if not fields_to_update:
            return { "success": False, "error": "No delivery info fields to update were specified." }

        for k, v in fields_to_update.items():
            self.delivery_info[order_id][k] = v

        # Also ensure that OrderInfo's nested `delivery_info` is synchronized
        self.orders[order_id]["delivery_info"] = self.delivery_info[order_id]

        return {
            "success": True,
            "message": f"Updated delivery info fields: {', '.join(fields_to_update.keys())}"
        }


class OnlineFoodOrderingManagementSystem(BaseEnv):
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

    def list_orders_paginated(self, **kwargs):
        return self._call_inner_tool('list_orders_paginated', kwargs)

    def get_order_details(self, **kwargs):
        return self._call_inner_tool('get_order_details', kwargs)

    def list_customer_orders_paginated(self, **kwargs):
        return self._call_inner_tool('list_customer_orders_paginated', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def get_customer_by_name(self, **kwargs):
        return self._call_inner_tool('get_customer_by_name', kwargs)

    def list_menu_items(self, **kwargs):
        return self._call_inner_tool('list_menu_items', kwargs)

    def get_menu_item_by_id(self, **kwargs):
        return self._call_inner_tool('get_menu_item_by_id', kwargs)

    def list_order_items(self, **kwargs):
        return self._call_inner_tool('list_order_items', kwargs)

    def get_delivery_info(self, **kwargs):
        return self._call_inner_tool('get_delivery_info', kwargs)

    def list_orders_by_status_paginated(self, **kwargs):
        return self._call_inner_tool('list_orders_by_status_paginated', kwargs)

    def update_order_status(self, **kwargs):
        return self._call_inner_tool('update_order_status', kwargs)

    def create_order(self, **kwargs):
        return self._call_inner_tool('create_order', kwargs)

    def update_order_items(self, **kwargs):
        return self._call_inner_tool('update_order_items', kwargs)

    def cancel_order(self, **kwargs):
        return self._call_inner_tool('cancel_order', kwargs)

    def update_menu_item_availability(self, **kwargs):
        return self._call_inner_tool('update_menu_item_availability', kwargs)

    def update_customer_info(self, **kwargs):
        return self._call_inner_tool('update_customer_info', kwargs)

    def update_delivery_info(self, **kwargs):
        return self._call_inner_tool('update_delivery_info', kwargs)

