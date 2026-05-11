# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict



class ProductInfo(TypedDict, total=False):
    # product_id: unique product identifier (str)
    product_id: str
    name: str
    price: float
    quantity: int
    # additional_attributes: Arbitrary extra product data
    additional_attributes: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # Constraints:
        # - Each product_id is unique within the system.
        # - Product price and quantity must be non-negative values.
        # - All product queries and updates must be performed using valid product_ids.

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve all information for a product given its product_id.

        Args:
            product_id (str): The unique identifier for the product to retrieve.

        Returns:
            dict: If successful:
                        {
                            "success": True,
                            "data": ProductInfo  # Product info dict (all fields)
                        }
                  If product_id is not found:
                        {
                            "success": False,
                            "error": "Product does not exist"
                        }

        Constraints:
            - product_id must exist in the inventory.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        return { "success": True, "data": self.products[product_id] }

    def get_product_price_by_id(self, product_id: str) -> dict:
        """
        Retrieve the price of a product based on its unique product_id.

        Args:
            product_id (str): Unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": float,  # price of the product
            }
            or
            {
                "success": False,
                "error": str,  # reason the price could not be retrieved
            }

        Constraints:
            - product_id must exist in the inventory.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product ID does not exist" }
        if "price" not in product:
            return { "success": False, "error": "Price information is missing for this product" }
        return { "success": True, "data": product["price"] }

    def get_product_quantity_by_id(self, product_id: str) -> dict:
        """
        Retrieve the current stock quantity for a product given its product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: 
                On success: { "success": True, "data": <quantity: int> }
                On error: { "success": False, "error": "Product not found" }

        Constraints:
            - product_id must exist in the system.
            - Product quantity must be a non-negative integer.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        quantity = product.get("quantity")
        # Defensive: If for some reason quantity is missing or invalid, treat as error
        if quantity is None or not isinstance(quantity, int) or quantity < 0:
            return { "success": False, "error": "Invalid product quantity" }
        return { "success": True, "data": quantity }

    def list_all_products(self) -> dict:
        """
        Retrieve the full list of products and their details from the inventory.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of all products' info (possibly empty)
            }

        Constraints:
            - None specific for this query.
        """
        all_products = list(self.products.values())
        return { "success": True, "data": all_products }

    def find_product_by_name(self, name_query: str) -> dict:
        """
        Look up product(s) whose name matches (or contains) a given string.
        Returns a list of matching product_ids.

        Args:
            name_query (str): Substring or phrase to match (case-insensitive) in product names.
                              If empty, returns all product_ids.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of matching product_ids (empty if no match found)
            }
        """
        # Prepare case-insensitive matching
        query = name_query.lower()
        result = []

        for product_id, product in self.products.items():
            product_name = product.get("name", "")
            if query == "" or query in product_name.lower():
                result.append(product_id)

        return {"success": True, "data": result}

    def get_product_attribute_by_id(self, product_id: str, attribute_name: str) -> dict:
        """
        Retrieve a specific attribute (such as manufacturer, category, etc.) of a product by its product_id and the attribute name.
    
        Args:
            product_id (str): The unique product identifier.
            attribute_name (str): Name of the attribute to retrieve (may be standard or in additional_attributes).

        Returns:
            dict: 
                On success: { "success": True, "data": <attribute_value> }
                On failure: { "success": False, "error": "reason" }
    
        Constraints:
            - Query must be performed with a valid product_id.
            - Returns attribute from top-level ProductInfo or its additional_attributes.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }

        if attribute_name in product:
            return { "success": True, "data": product[attribute_name] }

        # Try to fetch from additional_attributes if present
        additional = product.get("additional_attributes", {})
        if attribute_name in additional:
            return { "success": True, "data": additional[attribute_name] }

        return { "success": False, "error": f"Attribute '{attribute_name}' not found for product '{product_id}'" }

    def update_product_price(self, product_id: str, new_price: float) -> dict:
        """
        Change the price of a given product by product_id.

        Args:
            product_id (str): Unique identifier for the product.
            new_price (float): New price to set. Must be non-negative.

        Returns:
            dict: {
                "success": True,
                "message": "Price updated for product <product_id>."
            }
            or
            {
                "success": False,
                "error": "reason message"
            }

        Constraints:
            - product_id must be present in the system.
            - new_price must be non-negative.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }
        if not isinstance(new_price, (int, float)):
            return { "success": False, "error": "New price must be a number." }
        if new_price < 0:
            return { "success": False, "error": "New price must be non-negative." }

        self.products[product_id]["price"] = new_price
        return { "success": True, "message": f"Price updated for product {product_id}." }

    def update_product_quantity(self, product_id: str, new_quantity: int) -> dict:
        """
        Change the stock quantity for a product, ensuring the new quantity is non-negative.

        Args:
            product_id (str): Unique identifier of the product to update.
            new_quantity (int): The new quantity value (must be >= 0).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Quantity for product <product_id> updated to <new_quantity>." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - product_id must exist in the product inventory.
            - new_quantity must be non-negative (>= 0).
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product ID does not exist." }
        if not isinstance(new_quantity, int) or new_quantity < 0:
            return { "success": False, "error": "Quantity must be a non-negative integer." }
        self.products[product_id]["quantity"] = new_quantity
        return {
            "success": True,
            "message": f"Quantity for product {product_id} updated to {new_quantity}."
        }

    def add_product(self, product_id: str, name: str, price: float, quantity: int, additional_attributes: dict = None) -> dict:
        """
        Add a new product to the inventory.

        Args:
            product_id (str): Unique product identifier.
            name (str): Name of the product.
            price (float): Non-negative price of the product.
            quantity (int): Non-negative available quantity.
            additional_attributes (dict, optional): Additional product attributes.

        Returns:
            dict: {
                "success": True,
                "message": "Product <product_id> added successfully"
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - product_id is unique (must not already exist)
            - price and quantity must be non-negative
            - product_id, name must be provided (not empty)
        """

        if not product_id or not name:
            return { "success": False, "error": "product_id and name are required" }
        if product_id in self.products:
            return { "success": False, "error": "Product ID already exists" }
        if not isinstance(price, (int, float)) or price < 0:
            return { "success": False, "error": "Invalid or negative price" }
        if not isinstance(quantity, int) or quantity < 0:
            return { "success": False, "error": "Invalid or negative quantity" }
        info = {
            "product_id": product_id,
            "name": name,
            "price": float(price),
            "quantity": int(quantity)
        }
        if additional_attributes and isinstance(additional_attributes, dict):
            info["additional_attributes"] = additional_attributes
        self.products[product_id] = info
        return { "success": True, "message": f"Product {product_id} added successfully" }

    def remove_product(self, product_id: str) -> dict:
        """
        Delete a product from inventory by its product_id.

        Args:
            product_id (str): The unique identifier of the product to be deleted.

        Returns:
            dict:
                - If success: { "success": True, "message": "Product <product_id> removed successfully." }
                - If failure: { "success": False, "error": "Product with id <product_id> does not exist." }

        Constraints:
            - product_id must exist in the inventory.
        """
        if product_id not in self.products:
            return { "success": False, "error": f"Product with id {product_id} does not exist." }
        del self.products[product_id]
        return { "success": True, "message": f"Product {product_id} removed successfully." }

    def update_product_attribute(
        self,
        product_id: str,
        attribute_key: str,
        attribute_value: any
    ) -> dict:
        """
        Update or set the value of a specific additional attribute for a product,
        identified by product_id.

        Args:
            product_id (str): The unique identifier of the product.
            attribute_key (str): The key/name of the additional attribute to update/set.
            attribute_value (any): The value to set for the additional attribute.

        Returns:
            dict: {
                "success": True,
                "message": "Updated attribute '<attribute_key>' for product '<product_id>'."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - product_id must exist in the system.
            - attribute_key must be a non-empty string.
        """

        if product_id not in self.products:
            return {"success": False, "error": "Invalid product_id: product does not exist."}

        if not isinstance(attribute_key, str) or not attribute_key.strip():
            return {"success": False, "error": "attribute_key must be a non-empty string."}

        product = self.products[product_id]
        # Ensure 'additional_attributes' exists
        if "additional_attributes" not in product or product["additional_attributes"] is None:
            product["additional_attributes"] = {}

        product["additional_attributes"][attribute_key] = attribute_value

        return {
            "success": True,
            "message": f"Updated attribute '{attribute_key}' for product '{product_id}'."
        }


class ProductInventoryManagementSystem(BaseEnv):
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

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def get_product_price_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_price_by_id', kwargs)

    def get_product_quantity_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_quantity_by_id', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def find_product_by_name(self, **kwargs):
        return self._call_inner_tool('find_product_by_name', kwargs)

    def get_product_attribute_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_attribute_by_id', kwargs)

    def update_product_price(self, **kwargs):
        return self._call_inner_tool('update_product_price', kwargs)

    def update_product_quantity(self, **kwargs):
        return self._call_inner_tool('update_product_quantity', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)

    def update_product_attribute(self, **kwargs):
        return self._call_inner_tool('update_product_attribute', kwargs)

