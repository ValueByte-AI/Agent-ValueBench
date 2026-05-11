# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class ProductInfo(TypedDict):
    product_code: str
    product_name: str
    stock_quantity: int
    location: str
    supplier: str
    category: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment class for inventory management.
        """

        # Products: {product_code: ProductInfo}
        #   - product_code: Unique product identifier (str)
        #   - product_name: Name of the product (str)
        #   - stock_quantity: Units in stock (int, must be >= 0)
        #   - location: Storage location (str)
        #   - supplier: Supplier name or code (str)
        #   - category: Product category (str)
        self.products: Dict[str, ProductInfo] = {}

        # Constraints:
        # - Each product_code must be unique.
        # - stock_quantity must be an integer >= 0.
        # - Product records can be updated to reflect sales/deliveries/restocking.
        # - Queries should reflect the latest stock_quantity for each product.

    def get_product_by_code(self, product_code: str) -> dict:
        """
        Retrieve full product information for a specific product_code.

        Args:
            product_code (str): The unique identifier of the product.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ProductInfo  # All fields for the matching product
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Product not found"
                    }

        Constraints:
            - product_code must exist in the inventory.
        """
        if product_code not in self.products:
            return {"success": False, "error": "Product not found"}

        return {"success": True, "data": self.products[product_code]}

    def get_stock_quantity(self, product_code: str) -> dict:
        """
        Query the current stock quantity for the given product_code.

        Args:
            product_code (str): Unique identifier for the product.

        Returns:
            dict:
                {
                    "success": True,
                    "data": int  # Stock quantity (>= 0)
                }
                or
                {
                    "success": False,
                    "error": str  # Error description (e.g., product does not exist)
                }
        Constraints:
            - product_code must exist in the system.
            - stock_quantity is always integer >= 0.
        """
        if product_code not in self.products:
            return { "success": False, "error": "Product code does not exist" }

        stock_quantity = self.products[product_code]["stock_quantity"]
        return { "success": True, "data": stock_quantity }

    def list_all_products(self) -> dict:
        """
        Retrieve a list of all products and their details in the inventory.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # All products in inventory (may be empty if inventory is empty)
            }

        There are no inputs and no errors for this operation; always succeeds.
        """
        return {
            "success": True,
            "data": list(self.products.values())
        }

    def find_products_by_category(self, category: str) -> dict:
        """
        List all products within the specified category.

        Args:
            category (str): The category to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],   # All products in the given category (empty if none found)
            }

        Notes:
            - Matches category values exactly (case-sensitive).
            - Returns success even if no products match.
        """
        result = [
            product_info for product_info in self.products.values()
            if product_info["category"] == category
        ]
        return {"success": True, "data": result}

    def find_low_stock_products(self, threshold: int) -> dict:
        """
        Retrieve all products whose stock_quantity is below the specified threshold.

        Args:
            threshold (int): Numeric stock threshold. Products with stock_quantity < threshold are returned.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[ProductInfo] }
                - On illegal input: { "success": False, "error": str }
        Constraints:
            - threshold must be a non-negative integer.
            - The returned list may be empty if no products match.
        """
        if not isinstance(threshold, int) or threshold < 0:
            return { "success": False, "error": "Threshold must be a non-negative integer" }

        low_stock_products = [
            product for product in self.products.values()
            if product["stock_quantity"] < threshold
        ]
        return { "success": True, "data": low_stock_products }

    def get_products_by_supplier(self, supplier: str) -> dict:
        """
        List all products supplied by the specified supplier.

        Args:
            supplier (str): The name or code of the supplier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ProductInfo]  # List of matching products (may be empty if none found)
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Description of error (e.g., supplier not specified)
                    }
        Constraints:
            - Returns an empty list if no products from the given supplier.
            - Query is case-sensitive (exact match on supplier field).
        """
        if not isinstance(supplier, str) or supplier == "":
            return {"success": False, "error": "Supplier must be a non-empty string"}

        results = [
            product_info for product_info in self.products.values()
            if product_info["supplier"] == supplier
        ]

        return {"success": True, "data": results}

    def check_product_exists(self, product_code: str) -> dict:
        """
        Check if a product with the given product_code exists in the inventory.

        Args:
            product_code (str): The unique product identifier to check.

        Returns:
            dict:
                - If the product exists:
                    { "success": True, "data": True }
                - If the product does not exist:
                    { "success": True, "data": False }

        Constraints:
            - product_code must be a string.
            - product_code uniqueness is guaranteed by the system.
        """
        exists = product_code in self.products
        return { "success": True, "data": exists }

    def update_stock_quantity(self, product_code: str, new_quantity: int) -> dict:
        """
        Directly modify the stock_quantity for the given product_code.

        Args:
            product_code (str): Unique identifier for the product whose stock is to be updated.
            new_quantity (int): The new stock quantity (must be >= 0).

        Returns:
            dict: {
                "success": True,
                "message": "Stock quantity updated for product <product_code>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure (product not found, invalid quantity, etc.)"
            }

        Constraints:
            - product_code must exist in the system.
            - new_quantity must be an integer >= 0.
        """
        if product_code not in self.products:
            return {"success": False, "error": "Product code does not exist"}
        if not isinstance(new_quantity, int) or new_quantity < 0:
            return {"success": False, "error": "Stock quantity must be an integer >= 0"}
    
        self.products[product_code]['stock_quantity'] = new_quantity
        return {
            "success": True,
            "message": f"Stock quantity updated for product {product_code}."
        }

    def increment_stock(self, product_code: str, amount: int) -> dict:
        """
        Increase the stock_quantity for a product, for restocking operations.

        Args:
            product_code (str): Unique identifier for the product.
            amount (int): Number of units to add (must be > 0).

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Stock incremented by <amount> for product <product_code>." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - product_code must exist in the inventory.
            - amount must be a positive integer (>0).
            - stock_quantity must remain an integer >= 0 (enforced automatically by increment).
        """
        if product_code not in self.products:
            return { "success": False, "error": "Product code does not exist." }
        if not isinstance(amount, int) or amount <= 0:
            return { "success": False, "error": "Increment amount must be a positive integer." }

        product = self.products[product_code]
        product["stock_quantity"] += amount
        # Enforce integer type and >=0 for robustness
        if product["stock_quantity"] < 0:
            product["stock_quantity"] = 0

        return { 
            "success": True,
            "message": f"Stock incremented by {amount} for product {product_code}."
        }

    def decrement_stock(self, product_code: str, amount: int) -> dict:
        """
        Decrease the stock_quantity for a product after a sale.

        Args:
            product_code (str): Unique product identifier to decrement the stock of.
            amount (int): Amount to decrement (must be ≥ 1).

        Returns:
            dict: 
                On success:
                    {
                        "success": True, 
                        "message": "Decremented stock of product <product_code> by <amount>, new stock: <new_quantity>"
                    }
                On failure:
                    { "success": False, "error": "<reason>" }
        Constraints:
            - Product must exist.
            - Amount must be a positive integer.
            - Resulting stock_quantity cannot go below zero.
        """
        if product_code not in self.products:
            return { "success": False, "error": "Product does not exist" }
        if not isinstance(amount, int) or amount < 1:
            return { "success": False, "error": "Amount must be a positive integer" }
        current_stock = self.products[product_code]["stock_quantity"]
        if current_stock < amount:
            return { "success": False, "error": "Insufficient stock to decrement by requested amount" }
        self.products[product_code]["stock_quantity"] = current_stock - amount
        return {
            "success": True,
            "message": f"Decremented stock of product {product_code} by {amount}, new stock: {self.products[product_code]['stock_quantity']}"
        }

    def add_new_product(
        self,
        product_code: str,
        product_name: str,
        stock_quantity: int,
        location: str,
        supplier: str,
        category: str
    ) -> dict:
        """
        Add a new product to the inventory. Ensures product_code is unique and stock_quantity >= 0.

        Args:
            product_code (str): Unique identifier for the product.
            product_name (str): Name of the product.
            stock_quantity (int): Stock count (must be integer >= 0).
            location (str): Storage location.
            supplier (str): Supplier name or code.
            category (str): Product category.

        Returns:
            dict: {
                "success": True,
                "message": "Product added successfully."
            }
            or
            {
                "success": False,
                "error": <error description>
            }
        Constraints:
            - product_code must be unique.
            - stock_quantity must be integer >= 0.
        """

        # Validate uniqueness
        if product_code in self.products:
            return { "success": False, "error": "Product code already exists." }
    
        # Validate stock_quantity
        if not isinstance(stock_quantity, int) or stock_quantity < 0:
            return { "success": False, "error": "Stock quantity must be an integer >= 0." }

        self.products[product_code] = {
            "product_code": product_code,
            "product_name": product_name,
            "stock_quantity": stock_quantity,
            "location": location,
            "supplier": supplier,
            "category": category,
        }

        return {
            "success": True,
            "message": f"Product '{product_name}' (code: {product_code}) added successfully."
        }

    def update_product_info(
        self,
        product_code: str,
        product_name: str = None,
        location: str = None,
        supplier: str = None,
        category: str = None
    ) -> dict:
        """
        Modify non-stock details of a product (name, location, supplier, category).

        Args:
            product_code (str): Unique code identifying the product to update.
            product_name (str, optional): New name for the product.
            location (str, optional): New storage location.
            supplier (str, optional): New supplier information.
            category (str, optional): New product category.

        Returns:
            dict:
                - On success: { "success": True, "message": "Product info updated successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Product must exist.
            - Only non-stock, non-key attributes are updatable.
            - At least one updatable field must be provided.
        """
        if product_code not in self.products:
            return { "success": False, "error": "Product with that code does not exist" }

        fields_to_update = {}
        if product_name is not None:
            fields_to_update["product_name"] = product_name
        if location is not None:
            fields_to_update["location"] = location
        if supplier is not None:
            fields_to_update["supplier"] = supplier
        if category is not None:
            fields_to_update["category"] = category

        if not fields_to_update:
            return { "success": False, "error": "No updatable fields provided" }

        # Only update allowed fields
        for key, value in fields_to_update.items():
            self.products[product_code][key] = value

        return { "success": True, "message": "Product info updated successfully" }

    def remove_product(self, product_code: str) -> dict:
        """
        Remove a product from the inventory, given its unique product_code.

        Args:
            product_code (str): The unique product identifier to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Product <product_code> removed from inventory"
            }
            or
            {
                "success": False,
                "error": "Product not found"
            }

        Constraints:
            - The product_code must exist in the inventory.
            - (No other constraints are specified for removal.)
        """
        if product_code not in self.products:
            return {"success": False, "error": "Product not found"}

        del self.products[product_code]
        return {"success": True, "message": f"Product {product_code} removed from inventory"}


class InventoryManagementSystem(BaseEnv):
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

    def get_product_by_code(self, **kwargs):
        return self._call_inner_tool('get_product_by_code', kwargs)

    def get_stock_quantity(self, **kwargs):
        return self._call_inner_tool('get_stock_quantity', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def find_products_by_category(self, **kwargs):
        return self._call_inner_tool('find_products_by_category', kwargs)

    def find_low_stock_products(self, **kwargs):
        return self._call_inner_tool('find_low_stock_products', kwargs)

    def get_products_by_supplier(self, **kwargs):
        return self._call_inner_tool('get_products_by_supplier', kwargs)

    def check_product_exists(self, **kwargs):
        return self._call_inner_tool('check_product_exists', kwargs)

    def update_stock_quantity(self, **kwargs):
        return self._call_inner_tool('update_stock_quantity', kwargs)

    def increment_stock(self, **kwargs):
        return self._call_inner_tool('increment_stock', kwargs)

    def decrement_stock(self, **kwargs):
        return self._call_inner_tool('decrement_stock', kwargs)

    def add_new_product(self, **kwargs):
        return self._call_inner_tool('add_new_product', kwargs)

    def update_product_info(self, **kwargs):
        return self._call_inner_tool('update_product_info', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)

