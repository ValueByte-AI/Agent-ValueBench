# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str  # Should match an existing category_id
    price: float
    volume_ml: int
    alcohol_percent: float
    description: str
    available_quantity: int

class CategoryInfo(TypedDict):
    category_id: str
    name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for alcoholic beverage inventory management.
        """

        # Products: {product_id: ProductInfo}
        # ProductInfo attributes: product_id, name, category, price, volume_ml, alcohol_percent, description, available_quantity
        self.products: Dict[str, ProductInfo] = {}

        # Categories: {category_id: CategoryInfo}
        # CategoryInfo attributes: category_id, name, description
        self.categories: Dict[str, CategoryInfo] = {}

        # Constraints:
        # - Product names should be unique or uniquely identifiable.
        # - Product attributes (price, volume_ml, alcohol_percent, etc.) must be within reasonable ranges.
        #   (e.g., alcohol_percent between 0 and 100)
        # - Each product must be assigned to a valid category (category_id must exist in self.categories).
        # - available_quantity must be a non-negative integer.

    def search_products_by_name(self, name_query: str) -> dict:
        """
        Search for beverage products by (partial) name, supporting unique or closest match identification.

        Args:
            name_query (str): The (partial) name to search for; case-insensitive.

        Returns:
            dict: 
              - On success: { "success": True, "data": List[ProductInfo] }
                If no matches, returns empty list in data.
              - On error: { "success": False, "error": str }

        Constraints:
            - Product names are assumed to be unique, but partial matches may return multiple products.
            - name_query should be a non-empty string.
        """
        if not isinstance(name_query, str):
            return {"success": False, "error": "name_query must be a string"}
        if name_query.strip() == "":
            return {"success": False, "error": "name_query must be a non-empty string"}

        name_query_lower = name_query.lower()
        matches = [
            product_info
            for product_info in self.products.values()
            if name_query_lower in product_info["name"].lower()
        ]
        return {"success": True, "data": matches}

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve full information of a product using its product_id.

        Args:
            product_id (str): Unique identifier of the product to retrieve.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": ProductInfo
                  }
                - On error: {
                      "success": False,
                      "error": "Product not found"
                  }
        Constraints:
            - product_id must exist in the product records.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product not found" }

        return { "success": True, "data": self.products[product_id] }

    def get_product_by_name(self, name: str) -> dict:
        """
        Retrieve full information for a product using its unique name.

        Args:
            name (str): The name of the product to retrieve.

        Returns:
            dict:
                - On success: { "success": True, "data": ProductInfo }
                - On failure: { "success": False, "error": error_message }

        Constraints:
            - Product names should be unique or uniquely identifiable.
        """
        matches = [prod for prod in self.products.values() if prod["name"] == name]

        if len(matches) == 1:
            return { "success": True, "data": matches[0] }
        elif len(matches) == 0:
            return { "success": False, "error": "Product with the given name not found" }
        else:
            # Data integrity violated: multiple products with same name
            return { "success": False, "error": "Multiple products found with this name; data inconsistency" }

    def list_all_products(self) -> dict:
        """
        List all beverage products in the inventory.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # List of all products, possibly empty
            }

        Constraints:
            - None. Returns all records from the current state.
        """
        all_products = list(self.products.values())
        return { "success": True, "data": all_products }

    def filter_products_by_category(self, category_id: str) -> dict:
        """
        Retrieve all products assigned to a specific category.

        Args:
            category_id (str): The category's unique identifier.

        Returns:
            dict: 
              - {
                    "success": True,
                    "data": List[ProductInfo],   # List of matching products, empty if none found
                }
              - {
                    "success": False,
                    "error": str  # "Category not found"
                }

        Constraints:
            - category_id must exist in the system.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category not found" }

        products_in_category = [
            product_info
            for product_info in self.products.values()
            if product_info["category"] == category_id
        ]

        return { "success": True, "data": products_in_category }

    def filter_products_by_alcohol_percent(
        self,
        min_alcohol_percent: float,
        max_alcohol_percent: float
    ) -> dict:
        """
        Find products whose alcohol_percent is within the specified, inclusive range.

        Args:
            min_alcohol_percent (float): The minimum alcohol percentage (inclusive), must be between 0 and 100.
            max_alcohol_percent (float): The maximum alcohol percentage (inclusive), must be between 0 and 100.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of matching product info dicts. May be empty.
            }
            or
            {
                "success": False,
                "error": str  # Reason for input failure
            }

        Constraints:
            - Both min and max must be in [0, 100], and min <= max.
        """
        if (
            not (0 <= min_alcohol_percent <= 100)
            or not (0 <= max_alcohol_percent <= 100)
        ):
            return {
                "success": False,
                "error": "Alcohol percent range must be between 0 and 100."
            }
        if min_alcohol_percent > max_alcohol_percent:
            return {
                "success": False,
                "error": "Minimum alcohol percent cannot be greater than maximum."
            }

        matches = [
            product for product in self.products.values()
            if min_alcohol_percent <= product["alcohol_percent"] <= max_alcohol_percent
        ]
        return {
            "success": True,
            "data": matches
        }

    def filter_products_by_price_range(self, min_price: float, max_price: float) -> dict:
        """
        Find and return all products with a price in the inclusive range [min_price, max_price].

        Args:
            min_price (float): Minimum price (inclusive).
            max_price (float): Maximum price (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": list of ProductInfo for matching products (may be empty)
            }
            OR
            {
                "success": False,
                "error": str (reason for failure, e.g., invalid input)
            }

        Constraints:
            - min_price and max_price must be numbers and min_price <= max_price.
            - Only products whose price falls within the range are returned.
        """
        if not isinstance(min_price, (int, float)) or not isinstance(max_price, (int, float)):
            return {"success": False, "error": "min_price and max_price must be numbers"}
        if min_price > max_price:
            return {"success": False, "error": "min_price cannot be greater than max_price"}
        result = [
            product for product in self.products.values()
            if min_price <= product["price"] <= max_price
        ]
        return {"success": True, "data": result}

    def get_product_attributes(self, product_id: str) -> dict:
        """
        Retrieve selected attributes (name, price, volume_ml, alcohol_percent, category)
        for a specified product identified by its product_id.

        Args:
            product_id (str): The unique ID of the product.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": {
                        "name": str,
                        "price": float,
                        "volume_ml": int,
                        "alcohol_percent": float,
                        "category": str
                    }
                }
                On failure: {
                    "success": False,
                    "error": str  # Error message if product not found
                }
        Constraints:
            - product_id must exist in the system.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        product = self.products[product_id]
        data = {
            "name": product["name"],
            "price": product["price"],
            "volume_ml": product["volume_ml"],
            "alcohol_percent": product["alcohol_percent"],
            "category": product["category"],
        }
        return {"success": True, "data": data}

    def list_all_categories(self) -> dict:
        """
        Retrieve all beverage categories with IDs and descriptions.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # List of all categories (can be empty)
            }

        Notes:
            - No constraints or validation required; simply returns all categories.
            - If there are no categories, returns an empty list.
        """
        categories_list = list(self.categories.values())
        return {"success": True, "data": categories_list}

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve information about a category using its category_id.

        Args:
            category_id (str): The unique identifier for the category.

        Returns:
            dict: {
                "success": True,
                "data": CategoryInfo
            }
            or
            {
                "success": False,
                "error": "Category not found"
            }

        Constraints:
            - The specified category_id must exist in the system.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def get_category_by_name(self, name: str) -> dict:
        """
        Retrieve information about a category using its name.

        Args:
            name (str): The name of the category to search for.

        Returns:
            dict:
                - If found: { "success": True, "data": CategoryInfo }
                - If not found: { "success": False, "error": "Category with the specified name does not exist." }

        Constraints:
            - Category names may not be unique, but this returns the first match found.
            - Name comparison is case-sensitive.
        """
        for category in self.categories.values():
            if category["name"] == name:
                return { "success": True, "data": category }
        return { "success": False, "error": "Category with the specified name does not exist." }

    def add_product(
        self,
        product_id: str,
        name: str,
        category: str,
        price: float,
        volume_ml: int,
        alcohol_percent: float,
        description: str,
        available_quantity: int,
    ) -> dict:
        """
        Add a new beverage product to the inventory after verifying all value and uniqueness constraints.

        Args:
            product_id (str): Unique identifier for the product.
            name (str): Unique product name.
            category (str): category_id that the product belongs to.
            price (float): Price of the product (must be >= 0).
            volume_ml (int): Volume in milliliters (must be > 0).
            alcohol_percent (float): Alcohol percentage (must be between 0 and 100, inclusive).
            description (str): Description of the product.
            available_quantity (int): Stock (must be >= 0).

        Returns:
            dict: { "success": True, "message": str }
                  or
                  { "success": False, "error": str }

        Constraints enforced:
            - product_id must be unique.
            - name must be unique (case-insensitive).
            - category must exist.
            - price >= 0, volume_ml > 0, 0 <= alcohol_percent <= 100, available_quantity >= 0.
        """
        # Check if product_id is unique
        if product_id in self.products:
            return { "success": False, "error": "Product ID already exists." }

        # Product Name uniqueness (case-insensitive)
        for prod in self.products.values():
            if prod["name"].lower() == name.lower():
                return { "success": False, "error": "Product name already exists." }

        # Validate category existence
        if category not in self.categories:
            return { "success": False, "error": "Category does not exist." }

        # Validate numeric attributes
        if not isinstance(price, (int, float)) or price < 0:
            return { "success": False, "error": "Price must be a non-negative number." }

        if not isinstance(volume_ml, int) or volume_ml <= 0:
            return { "success": False, "error": "Volume must be a positive integer." }

        if (
            not isinstance(alcohol_percent, (int, float)) or 
            alcohol_percent < 0 or 
            alcohol_percent > 100
        ):
            return { "success": False, "error": "Alcohol percent must be between 0 and 100." }

        if not isinstance(available_quantity, int) or available_quantity < 0:
            return { "success": False, "error": "Available quantity must be a non-negative integer." }

        # All constraints satisfied, create product
        self.products[product_id] = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "price": float(price),
            "volume_ml": int(volume_ml),
            "alcohol_percent": float(alcohol_percent),
            "description": description,
            "available_quantity": int(available_quantity),
        }

        return { "success": True, "message": "Product added successfully." }

    def update_product_attributes(self, product_id: str, updates: dict) -> dict:
        """
        Update attributes (price, volume_ml, alcohol_percent, name, category, description,
        available_quantity) for an existing product, with full validation.

        Args:
            product_id (str): Unique identifier for the product.
            updates (dict): Key-value pairs of attributes to update.

        Returns:
            dict: {
                "success": True,
                "message": "Product attributes updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Updated name (if provided) must be unique among all products except the current one.
            - category (if provided) must point to an existing category_id.
            - price, volume_ml must be non-negative.
            - alcohol_percent must be between 0 and 100.
            - available_quantity must be a non-negative integer.
            - Ignores unrecognized attributes.
        """
        # Product existence check
        if product_id not in self.products:
            return { "success": False, "error": "Product not found" }
        product = self.products[product_id]

        # Allowed updates
        allowed_fields = {"name", "category", "price", "volume_ml", "alcohol_percent", "description", "available_quantity"}

        for key in updates:
            if key not in allowed_fields:
                continue  # Ignore unrecognized field

            value = updates[key]

            if key == "name":
                # Name uniqueness
                for pid, p in self.products.items():
                    if pid != product_id and p["name"].strip().lower() == str(value).strip().lower():
                        return { "success": False, "error": "Product name must be unique" }
            elif key == "category":
                if value not in self.categories:
                    return { "success": False, "error": "Category does not exist" }
            elif key == "price":
                try:
                    v = float(value)
                    if v < 0:
                        return { "success": False, "error": "Price must be non-negative" }
                except (ValueError, TypeError):
                    return { "success": False, "error": "Price must be a valid number" }
            elif key == "volume_ml":
                try:
                    v = int(value)
                    if v < 0:
                        return { "success": False, "error": "Volume must be non-negative integer" }
                except (ValueError, TypeError):
                    return { "success": False, "error": "Volume must be a valid integer" }
            elif key == "alcohol_percent":
                try:
                    v = float(value)
                    if not (0 <= v <= 100):
                        return { "success": False, "error": "Alcohol percent must be between 0 and 100" }
                except (ValueError, TypeError):
                    return { "success": False, "error": "Alcohol percent must be a valid number" }
            elif key == "available_quantity":
                try:
                    v = int(value)
                    if v < 0:
                        return { "success": False, "error": "Available quantity must be non-negative integer" }
                except (ValueError, TypeError):
                    return { "success": False, "error": "Available quantity must be a valid integer" }

        # If all validation passes, apply updates
        for key in allowed_fields:
            if key in updates:
                product[key] = updates[key]

        return { "success": True, "message": "Product attributes updated successfully" }

    def adjust_product_quantity(self, product_id: str, adjustment: int) -> dict:
        """
        Increase or decrease the available_quantity for a product, ensuring it does not become negative.

        Args:
            product_id (str): The ID of the product whose stock quantity will be adjusted.
            adjustment (int): The integer amount to adjust by (can be positive or negative).

        Returns:
            dict: 
                - On success: {
                    "success": True, 
                    "message": "Product quantity adjusted to X."  # X is the new quantity
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Description of the error
                  }

        Constraints:
            - Product must exist.
            - Resulting available_quantity must be a non-negative integer.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found."}

        # Ensure adjustment is integer
        if not isinstance(adjustment, int):
            return {"success": False, "error": "Adjustment value must be an integer."}

        current_qty = self.products[product_id]["available_quantity"]
        new_qty = current_qty + adjustment

        if new_qty < 0:
            return {"success": False, "error": "Adjustment would result in negative product quantity."}

        self.products[product_id]["available_quantity"] = new_qty
        return {
            "success": True,
            "message": f"Product quantity for '{product_id}' adjusted to {new_qty}."
        }

    def remove_product(self, product_id: str) -> dict:
        """
        Delete a beverage product from the inventory.

        Args:
            product_id (str): Unique identifier of the product to remove.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Product <product_id> removed from inventory."}
                - On failure: {"success": False, "error": "Product not found."}

        Constraints:
            - The product must exist in the inventory (self.products).
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found."}
    
        del self.products[product_id]
        return {
            "success": True,
            "message": f"Product {product_id} removed from inventory."
        }

    def add_category(self, category_id: str, name: str, description: str) -> dict:
        """
        Insert a new beverage category into the inventory system.

        Args:
            category_id (str): Unique identifier for the new category.
            name (str): Human-readable category name.
            description (str): Category description.

        Returns:
            dict: {
                "success": True, "message": "Category '<name>' added successfully."
            }
            or
            {
                "success": False, "error": <error reason>
            }

        Constraints:
            - category_id must be unique (not in self.categories).
            - category name should not duplicate an existing category's name.
            - All fields are required and must be non-empty strings.
        """
        # Check for non-empty input
        if not category_id or not name or not description:
            return { "success": False, "error": "All fields (category_id, name, description) must be non-empty." }

        # Check for unique category_id
        if category_id in self.categories:
            return { "success": False, "error": f"Category ID '{category_id}' already exists." }

        # Check for unique name among categories
        if any(c["name"].lower() == name.lower() for c in self.categories.values()):
            return { "success": False, "error": f"Category name '{name}' already exists." }

        # Add the new category
        new_category = {
            "category_id": category_id,
            "name": name,
            "description": description
        }
        self.categories[category_id] = new_category
        return { "success": True, "message": f"Category '{name}' added successfully." }

    def update_category(self, category_id: str, name: str = None, description: str = None) -> dict:
        """
        Edit the name and/or description of an existing category.

        Args:
            category_id (str): The ID of the category to update.
            name (str, optional): New name for the category (if changing).
            description (str, optional): New description for the category (if changing).

        Returns:
            dict: {
                "success": True,
                "message": "Category updated"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - category_id must exist.
            - At least one of 'name' or 'description' must be provided.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category ID does not exist" }

        if name is None and description is None:
            return { "success": False, "error": "No updates provided (name or description required)" }

        if name is not None:
            self.categories[category_id]["name"] = name
        if description is not None:
            self.categories[category_id]["description"] = description

        return { "success": True, "message": "Category updated" }

    def remove_category(self, category_id: str) -> dict:
        """
        Remove the specified category from the inventory, only if no product uses this category.

        Args:
            category_id (str): The unique identifier of the category to be removed.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Category <category_id> removed successfully."
                }
                OR
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Category must exist.
            - No product may reference this category (category_id) at time of removal.
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist."}

        # Check if any product references this category
        for product in self.products.values():
            if product['category'] == category_id:
                return {
                    "success": False,
                    "error": f"Cannot remove category; product '{product['name']}' (ID: {product['product_id']}) uses this category."
                }

        del self.categories[category_id]
        return {
            "success": True,
            "message": f"Category {category_id} removed successfully."
        }

    def validate_product_constraints(self, product_id: str = None, name: str = None) -> dict:
        """
        Validate that a product's attributes and relations satisfy all inventory constraints.

        Args:
            product_id (str, optional): ID of the product to validate.
            name (str, optional): Name of the product to validate (case-insensitive).
    
        Returns:
            dict:
                {
                    "success": True,
                    "message": "Product constraints valid."
                }
                Or on failure:
                {
                    "success": False,
                    "error": <reason>
                }
    
        Constraints Checked:
            - Product must exist (by ID or unique name).
            - Must have unique name (no others with same case-insensitive name).
            - price >= 0.0
            - volume_ml >= 0
            - 0 <= alcohol_percent <= 100
            - available_quantity >= 0 and integer
            - category refers to a valid category
        """
        # Find the product
        product = None
        if product_id is not None:
            product = self.products.get(product_id)
            if not product:
                return {"success": False, "error": f"Product with id '{product_id}' does not exist."}
        elif name is not None:
            # Search by name (case-insensitive)
            matching = [
                p for p in self.products.values()
                if p["name"].lower() == name.lower()
            ]
            if not matching:
                return {"success": False, "error": f"Product with name '{name}' does not exist."}
            if len(matching) > 1:
                return {"success": False, "error": f"Multiple products found with name '{name}'. Name must be unique."}
            product = matching[0]
            product_id = product['product_id']
        else:
            return {"success": False, "error": "Must provide either product_id or name."}

        # Unique name check (except this product itself)
        for pid, p in self.products.items():
            if pid != product_id and p['name'].lower() == product['name'].lower():
                return {"success": False, "error": "Duplicate product name found. Names must be unique."}
    
        # Attribute validation
        if not isinstance(product["price"], (int, float)) or product["price"] < 0.0:
            return {"success": False, "error": "Product price must be a non-negative number."}
        if not isinstance(product["volume_ml"], int) or product["volume_ml"] < 0:
            return {"success": False, "error": "Product volume_ml must be a non-negative integer."}
        if (not isinstance(product["alcohol_percent"], (int, float)) or
            product["alcohol_percent"] < 0 or product["alcohol_percent"] > 100):
            return {"success": False, "error": "alcohol_percent must be between 0 and 100 (inclusive)."}
        if (not isinstance(product["available_quantity"], int) or
            product["available_quantity"] < 0):
            return {"success": False, "error": "available_quantity must be a non-negative integer."}
        # Category validation
        if product["category"] not in self.categories:
            return {"success": False, "error": "Product category is invalid (category_id does not exist)."}

        return {"success": True, "message": "Product constraints valid."}


class AlcoholicBeverageInventoryManagementSystem(BaseEnv):
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

    def search_products_by_name(self, **kwargs):
        return self._call_inner_tool('search_products_by_name', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def get_product_by_name(self, **kwargs):
        return self._call_inner_tool('get_product_by_name', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def filter_products_by_category(self, **kwargs):
        return self._call_inner_tool('filter_products_by_category', kwargs)

    def filter_products_by_alcohol_percent(self, **kwargs):
        return self._call_inner_tool('filter_products_by_alcohol_percent', kwargs)

    def filter_products_by_price_range(self, **kwargs):
        return self._call_inner_tool('filter_products_by_price_range', kwargs)

    def get_product_attributes(self, **kwargs):
        return self._call_inner_tool('get_product_attributes', kwargs)

    def list_all_categories(self, **kwargs):
        return self._call_inner_tool('list_all_categories', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_attributes(self, **kwargs):
        return self._call_inner_tool('update_product_attributes', kwargs)

    def adjust_product_quantity(self, **kwargs):
        return self._call_inner_tool('adjust_product_quantity', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def remove_category(self, **kwargs):
        return self._call_inner_tool('remove_category', kwargs)

    def validate_product_constraints(self, **kwargs):
        return self._call_inner_tool('validate_product_constraints', kwargs)
