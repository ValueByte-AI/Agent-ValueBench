# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict



class ProductInfo(TypedDict):
    product_id: str
    name: str
    description: str
    category_id: str
    metadata: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str

class CategoryInfo(TypedDict):
    category_id: str
    category_name: str
    parent_category_id: str

class ProductLogInfo(TypedDict):
    log_id: str
    product_id: str
    event_type: str
    event_timestamp: str
    user_id: str
    detail: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    role: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Product Information Management System (PIM) stateful environment structure.
        """

        # Products: {product_id: ProductInfo}
        # From entity Produc: product_id, name, description, category_id, metadata, status, created_at, updated_at
        self.products: Dict[str, ProductInfo] = {}

        # Categories: {category_id: CategoryInfo}
        # From entity Categor: category_id, category_name, parent_category_id
        self.categories: Dict[str, CategoryInfo] = {}

        # Product logs: {log_id: ProductLogInfo}
        # From entity ProductLog: log_id, product_id, event_type, event_timestamp, user_id, detail
        self.logs: Dict[str, ProductLogInfo] = {}

        # Users: {user_id: UserInfo}
        # From entity User: user_id, name, role
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each product must belong to an existing category (or a root category).
        # - No two products can have the same product_id.
        # - Logs must reference a valid product.
        # - Only authorized users can access or modify product data.
        # - Metadata for each product must meet required validation schemas (if defined).

    @staticmethod
    def _parse_iso_datetime(value: Any):
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except Exception:
            return None

    @staticmethod
    def _format_iso_datetime(value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _next_product_updated_at(self, product_id: str, product: dict) -> str:
        candidates = []
        for key in ("updated_at", "created_at"):
            parsed = self._parse_iso_datetime(product.get(key))
            if parsed is not None:
                candidates.append(parsed)
        for log in self.logs.values():
            if log.get("product_id") != product_id:
                continue
            parsed = self._parse_iso_datetime(log.get("event_timestamp"))
            if parsed is not None:
                candidates.append(parsed)
        if not candidates:
            existing = product.get("updated_at")
            if isinstance(existing, str) and existing:
                return existing
            return "1970-01-01T00:00:01Z"
        return self._format_iso_datetime(max(candidates) + timedelta(seconds=1))

    def _normalize_metadata_schema_store(self):
        if not hasattr(self, "metadata_schemas"):
            self.metadata_schemas = {}

        schema_store = self.metadata_schemas
        if schema_store in (None, ""):
            schema_store = {}
        elif isinstance(schema_store, str):
            try:
                schema_store = json.loads(schema_store)
            except Exception:
                schema_store = {}
        if not isinstance(schema_store, dict):
            schema_store = {}
        self.metadata_schemas = schema_store
        return schema_store

    def _validate_metadata_for_category(self, category_id: str, metadata: dict) -> dict:
        schema_store = self._normalize_metadata_schema_store()

        schema = schema_store.get(category_id)
        if schema is None:
            return {"success": False, "error": "Validation schema not found for category"}

        if not isinstance(metadata, dict):
            return {"success": False, "error": "Invalid metadata format"}

        if isinstance(schema, str):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "errors": [
                        f"Schema definition '{schema}' is unavailable for category '{category_id}'."
                    ],
                },
            }

        if not isinstance(schema, dict):
            return {"success": False, "error": "Validation schema not found for category"}

        required_keys = schema.get("required")
        if required_keys is None:
            required_keys = schema.get("required_keys", [])
        errors = []
        for key in required_keys:
            if key not in metadata:
                errors.append(f"Missing key in metadata: '{key}'")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, expected_type in properties.items():
                if key not in metadata:
                    continue
                value = metadata.get(key)
                if expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Metadata key '{key}' must be an integer")
                elif expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Metadata key '{key}' must be a string")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Metadata key '{key}' must be a boolean")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"Metadata key '{key}' must be an object")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Metadata key '{key}' must be an array")

        return {
            "success": True,
            "data": {
                "valid": len(errors) == 0,
                "errors": errors,
            },
        }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve detailed information for a product given its unique product_id.

        Args:
            product_id (str): The unique product identifier.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": ProductInfo  # Complete product info
                }
              - On failure: {
                    "success": False,
                    "error": "Product not found"
                }

        Constraints:
            - product_id must exist in the system.
        """
        product = self.products.get(product_id)
        if product is None:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": product}

    def list_all_products(self) -> dict:
        """
        Retrieve a list of all products managed within the PIM system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # List of all product info (may be empty if no products)
            }
        Edge Cases:
            - If there are no products, 'data' is an empty list.
        """
        product_list = list(self.products.values())
        return { "success": True, "data": product_list }

    def get_product_by_category(self, category_id: str) -> dict:
        """
        Retrieve all products assigned to a given category by category_id.

        Args:
            category_id (str): The ID of the category for which products are requested.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProductInfo],  # Product dicts assigned to the category (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # e.g., "Category does not exist"
                }

        Constraints:
            - The given category_id must exist in the system.
            - Only includes products directly assigned to category_id (does NOT include subcategories).
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        products = [
            product_info for product_info in self.products.values()
            if product_info["category_id"] == category_id
        ]

        return {"success": True, "data": products}

    def get_product_metadata(self, product_id: str) -> dict:
        """
        Retrieve the metadata dictionary associated with the specified product.

        Args:
            product_id (str): The unique ID of the product.

        Returns:
            dict: 
                - On success: {"success": True, "data": <metadata dict>}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - The product_id must exist in the products store.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }

        metadata = product.get("metadata")
        if not isinstance(metadata, dict):
            return { "success": False, "error": "Invalid metadata format" }

        return { "success": True, "data": metadata }

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve category information (such as name and hierarchy) by its category_id.

        Args:
            category_id (str): The unique identifier of the category to retrieve.

        Returns:
            dict: 
                { "success": True, "data": CategoryInfo } if category is found,
                { "success": False, "error": "Category not found" } if not.

        Constraints:
            - The category_id must exist in the system.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def list_all_categories(self) -> dict:
        """
        Retrieve a list of all product categories.

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of all category info objects (may be empty)
            }
        """
        categories_list = list(self.categories.values())
        return {
            "success": True,
            "data": categories_list
        }

    def get_logs_by_product_id(self, product_id: str) -> dict:
        """
        Retrieve all log records associated with the specified product_id.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductLogInfo]  # All logs referencing this product (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Error description if product_id does not exist
            }

        Constraints:
            - product_id must exist in the system (self.products).
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        logs = [
            log_info for log_info in self.logs.values()
            if log_info["product_id"] == product_id
        ]

        return {"success": True, "data": logs}

    def get_log_by_id(self, log_id: str) -> dict:
        """
        Retrieve a specific product log record by its log_id.

        Args:
            log_id (str): The unique identifier of the log entry.

        Returns:
            dict: {
                "success": True,
                "data": ProductLogInfo,  # The log entry with the specified id
            }
            or
            {
                "success": False,
                "error": "Log entry not found"
            }

        Constraints:
        - The log_id must exist in the environment.
        """
        if log_id not in self.logs:
            return {"success": False, "error": "Log entry not found"}
        return {"success": True, "data": self.logs[log_id]}

    def get_logs_by_event_type(self, product_id: str, event_type: str) -> dict:
        """
        Retrieve all product log entries for a specific product filtered by event_type.

        Args:
            product_id (str): The ID of the product whose logs to retrieve.
            event_type (str): The event type to filter by (e.g., 'update', 'delete').

        Returns:
            dict: {
                "success": True,
                "data": List[ProductLogInfo],  # List of log entries (possibly empty)
            }
            OR
            {
                "success": False,
                "error": str  # Description of error (e.g. product does not exist)
            }

        Constraints:
            - product_id must exist in the system.
            - Only logs for the given product and matching event_type are returned.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        matching_logs = [
            log for log in self.logs.values()
            if log["product_id"] == product_id and log["event_type"] == event_type
        ]

        return {"success": True, "data": matching_logs}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information based on user_id.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict:
                On success: { "success": True, "data": UserInfo }
                On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user_id must exist in the users collection.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def check_user_permission_for_product_access(self, user_id: str, product_id: str) -> dict:
        """
        Determine if a user is authorized to access or modify a specific product.

        Args:
            user_id (str): The unique ID of the user trying to access/modify product data.
            product_id (str): The unique ID of the product the user wants to access/modify.

        Returns:
            dict: {
                "success": True,
                "permission_granted": bool,  # True if user is authorized, otherwise False
                "role": str,                 # User's role
                "reason": str                # Explanation for the result
            }
            or
            {
                "success": False,
                "error": str  # Error description (unknown user/product, etc)
            }

        Constraints:
            - Only authorized users (based on their roles) can access/modify product data.
            - User and product must exist.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product does not exist" }

        role = user.get("role")
        if role == "admin":
            return {
                "success": True,
                "permission_granted": True,
                "role": role,
                "reason": "Admin users have full access to all products."
            }
        elif role == "editor":
            return {
                "success": True,
                "permission_granted": True,
                "role": role,
                "reason": "Editors are authorized to access and modify product data."
            }
        elif role == "manager":
            return {
                "success": True,
                "permission_granted": True,
                "role": role,
                "reason": "Managers are authorized to access and modify product data."
            }
        elif role == "viewer":
            return {
                "success": True,
                "permission_granted": False,
                "role": role,
                "reason": "Viewers are not authorized to modify product data."
            }
        else:
            return {
                "success": True,
                "permission_granted": False,
                "role": role if role else "",
                "reason": "User's role does not grant access to modify product data."
            }

    def validate_product_metadata_schema(self, product_id: str) -> dict:
        """
        Validate that a product's metadata field meets the required schema for its category.

        Args:
            product_id (str): The product's identifier.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "valid": bool,
                    "errors": list[str]  # List of error messages if invalid, empty if valid
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. missing product or schema
            }

        Constraints:
            - Product must exist.
            - Validation schema must exist (stubbed here as self.metadata_schemas[category_id]).
            - Metadata format should be checked.
        """
        product = self.products.get(product_id)
        if product is None:
            return {"success": False, "error": "Product not found"}

        return self._validate_metadata_for_category(
            product.get("category_id"),
            product.get("metadata", {}),
        )

    def create_product(
        self,
        product_id: str,
        name: str,
        description: str,
        category_id: str,
        metadata: dict,
        status: str,
        created_at: str,
        updated_at: str,
        user_id: str,
    ) -> dict:
        """
        Add a new product to the system, ensuring uniqueness of product_id, existence of category, 
        proper metadata (if schema is defined), and that the creator has appropriate permission.

        Args:
            product_id (str): Unique product identifier.
            name (str): Product name.
            description (str): Product description.
            category_id (str): Category for product, must exist.
            metadata (dict): Arbitrary data, may be schema-validated.
            status (str): Product status.
            created_at (str): Product creation timestamp.
            updated_at (str): Product last update timestamp.
            user_id (str): The ID of the user attempting creation.

        Returns:
            dict: {
                "success": True, "message": "Product created successfully"
            } 
            or 
            {
                "success": False, "error": str
            }

        Constraints:
            - product_id must be unique.
            - category_id must exist.
            - Only authorized users can create products (role: "admin" or "manager").
            - metadata must pass validation if a schema is defined (calls validate_product_metadata_schema).
        """
        # Check unique product_id
        if product_id in self.products:
            return {"success": False, "error": "Product with this product_id already exists"}
    
        # Check category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}
    
        # Check user & permission
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        if user.get("role") not in ("admin", "manager"):
            return {"success": False, "error": "User not authorized to create products"}

        validation_result = self._validate_metadata_for_category(category_id, metadata)
        if validation_result.get("success", False):
            if not validation_result["data"]["valid"]:
                return {"success": False, "error": "; ".join(validation_result["data"]["errors"])}
        elif validation_result.get("error") != "Validation schema not found for category":
            return {"success": False, "error": f"Metadata validation failed: {validation_result.get('error', 'Unknown error')}"}

        # All checks passed, create product
        self.products[product_id] = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "category_id": category_id,
            "metadata": metadata,
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        return {"success": True, "message": "Product created successfully"}

    def update_product(
        self,
        user_id: str,
        product_id: str,
        name: str = None,
        description: str = None,
        category_id: str = None,
        metadata: dict = None,
        status: str = None
    ) -> dict:
        """
        Modify one or more fields of a product, including metadata or status.

        Args:
            user_id (str): The ID of the user performing the update.
            product_id (str): ID of the product to update.
            name (str, optional): New product name.
            description (str, optional): New product description.
            category_id (str, optional): New category ID.
            metadata (dict, optional): New product metadata (must satisfy schema).
            status (str, optional): New status for the product.

        Returns:
            dict: {
                "success": True,
                "message": "Product updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only authorized users can update product data (must check user role).
            - The product must exist.
            - If changing category, new category_id must exist.
            - If updating metadata, must validate schema.
            - updated_at is set to current time.
        """

        # 1. User validation
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        user_info = self.users[user_id]
        # Check role, assume 'admin', 'editor', and 'manager' can update
        if user_info.get("role") not in ("admin", "editor", "manager"):
            return {"success": False, "error": "User is not authorized to update products."}

        # 2. Product existence
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}

        product = self.products[product_id]
        updates = {}

        # 3. Category validation
        if category_id is not None:
            if category_id not in self.categories:
                return {"success": False, "error": "Specified category does not exist."}
            updates["category_id"] = category_id

        # 4. Metadata validation
        if metadata is not None:
            validation_result = self._validate_metadata_for_category(
                category_id if category_id is not None else product["category_id"],
                metadata,
            )
            if validation_result.get("success", False):
                if not validation_result["data"]["valid"]:
                    return {"success": False, "error": f"Invalid metadata: {'; '.join(validation_result['data']['errors'])}"}
            elif validation_result.get("error") != "Validation schema not found for category":
                return {"success": False, "error": f"Invalid metadata: {validation_result.get('error', 'Unknown error')}"}
            updates["metadata"] = metadata

        # 5. Other fields
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status

        if not updates:
            return {"success": False, "error": "No update fields provided."}

        # 6. Apply updates, update updated_at timestamp
        for k, v in updates.items():
            product[k] = v
        product["updated_at"] = self._next_product_updated_at(product_id, product)

        # Save the updated product back (not always needed because dict is mutable)
        self.products[product_id] = product

        return {"success": True, "message": "Product updated."}

    def delete_product(self, product_id: str, user_id: str) -> dict:
        """
        Permanently remove a product from the system, along with all related logs.

        Args:
            product_id (str): ID of the product to be deleted.
            user_id (str): ID of the user attempting the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Product <product_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Product must exist.
            - User must exist and be authorized (typically "admin" role) to delete product.
            - All product logs referencing this product will also be deleted for referential integrity.
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check user role (assuming only "admin" can delete)
        if user.get("role") != "admin":
            return { "success": False, "error": "Permission denied: user is not authorized to delete products" }

        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        # Delete product
        del self.products[product_id]

        # Delete logs referencing this product (referential integrity)
        to_delete = [log_id for log_id, log in self.logs.items() if log["product_id"] == product_id]
        for log_id in to_delete:
            del self.logs[log_id]

        return { "success": True, "message": f"Product {product_id} deleted successfully." }

    def create_category(
        self,
        category_id: str,
        category_name: str,
        parent_category_id: str = ""
    ) -> dict:
        """
        Add a new category to the PIM system.

        Args:
            category_id (str): Unique identifier for the new category.
            category_name (str): Name of the category (must not be empty).
            parent_category_id (str, optional): ID of the parent category ("" or None for root/top-level).

        Returns:
            dict:
                - On success: {"success": True, "message": "Category <category_id> created successfully"}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Category ID must be unique.
            - If parent_category_id is not "" or None, it must exist in system.
            - Category name must be non-empty.
        """
        if not category_id or not category_name:
            return {"success": False, "error": "category_id and category_name are required and must be non-empty"}

        if category_id in self.categories:
            return {"success": False, "error": f"Category ID '{category_id}' already exists"}

        if parent_category_id and parent_category_id not in self.categories:
            return {"success": False, "error": f"Parent category '{parent_category_id}' does not exist"}

        new_category: CategoryInfo = {
            "category_id": category_id,
            "category_name": category_name,
            "parent_category_id": parent_category_id or ""
        }
        self.categories[category_id] = new_category

        return {"success": True, "message": f"Category '{category_id}' created successfully"}

    def update_category(self, category_id: str, update_fields: Dict[str, str]) -> dict:
        """
        Modify details (such as name and/or parent) of an existing category.

        Args:
            category_id (str): ID of the category to update.
            update_fields (Dict[str, str]): Fields to update, e.g.,
                {
                    "category_name": "<new_name>",           # optional
                    "parent_category_id": "<new_parent_id>"  # optional
                }

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Category updated successfully"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - category_id must exist.
            - If updating parent_category_id, the new parent must exist (unless it's a root marker such as None or '').
            - Must not set parent_category_id to itself or any of its descendants (tree/cycle check).
        """
        # Check if category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        cat = self.categories[category_id]

        # Handle category_name update (if provided)
        if "category_name" in update_fields:
            new_name = update_fields["category_name"].strip()
            if not new_name:
                return {"success": False, "error": "Category name cannot be empty"}
            cat["category_name"] = new_name

        # Handle parent_category_id update (if provided)
        if "parent_category_id" in update_fields:
            new_parent = update_fields["parent_category_id"]

            is_root = new_parent in ("", None)  # Allow root category marker
            if not is_root:
                # Parent must exist and not be the category itself
                if new_parent not in self.categories:
                    return {"success": False, "error": "New parent category does not exist"}
                if new_parent == category_id:
                    return {"success": False, "error": "Category cannot be its own parent"}

                # Check tree structure: new parent cannot be a descendant of this category (no cycles)
                ancestor = new_parent
                while ancestor not in ("", None):
                    if ancestor == category_id:
                        return {"success": False, "error": "Setting this parent would create a cycle in the category tree"}
                    ancestor = self.categories[ancestor]["parent_category_id"]

            cat["parent_category_id"] = new_parent if not is_root else ""

        # Save updated category
        self.categories[category_id] = cat
        return {"success": True, "message": "Category updated successfully"}

    def delete_category(self, category_id: str) -> dict:
        """
        Delete a category, ensuring no products are orphaned and no subcategories remain.

        Args:
            category_id (str): The ID of the category to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Category <category_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Cannot delete a category if any product is assigned to it.
            - Cannot delete a category if it has subcategories (other categories with this as parent).
            - Category must exist.
        """
        # Check if the category exists
        if category_id not in self.categories:
            return { "success": False, "error": f"Category '{category_id}' does not exist." }

        # Check for products assigned to this category
        has_products = any(
            product["category_id"] == category_id
            for product in self.products.values()
        )
        if has_products:
            return { "success": False, "error": f"Cannot delete category '{category_id}': products are assigned to this category." }

        # Check for subcategories
        has_subcategories = any(
            cat["parent_category_id"] == category_id
            for cat in self.categories.values()
            if cat["category_id"] != category_id  # Exclude self
        )
        if has_subcategories:
            return { "success": False, "error": f"Cannot delete category '{category_id}': subcategories exist." }

        # If all checks pass, delete category
        del self.categories[category_id]
        return { "success": True, "message": f"Category '{category_id}' deleted successfully." }

    def add_product_log_entry(
        self,
        product_id: str,
        event_type: str,
        event_timestamp: str,
        user_id: str,
        detail: str
    ) -> dict:
        """
        Create a new log entry for a product event (e.g., update, delete).

        Args:
            product_id (str): The ID of the product the log pertains to.
            event_type (str): The type of event (e.g., "update", "delete").
            event_timestamp (str): The timestamp when the event occurred (ISO8601 or other string).
            user_id (str): The user who performed the event.
            detail (str): Additional details about the event.

        Returns:
            dict: {
                "success": True,
                "message": "Product log entry created",
                "log_id": str
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - `product_id` must exist in the system.
            - `user_id` must exist in the system.
            - The log entry's log_id must be unique.
        """
        # Validate product_id
        if product_id not in self.products:
            return {"success": False, "error": "Invalid product_id: product does not exist."}

        # Validate user_id
        if user_id not in self.users:
            return {"success": False, "error": "Invalid user_id: user does not exist."}

        # Basic event_type and event_timestamp checks
        if not event_type or not isinstance(event_type, str):
            return {"success": False, "error": "Invalid event_type."}

        if not event_timestamp or not isinstance(event_timestamp, str):
            return {"success": False, "error": "Invalid event_timestamp."}

        # Generate a new unique log_id
        # We'll use a simple logic: "log_<number>", where number = len(self.logs) + 1, ensuring uniqueness
        log_id_base = "log_"
        i = len(self.logs) + 1
        while True:
            proposed_log_id = f"{log_id_base}{i}"
            if proposed_log_id not in self.logs:
                break
            i += 1

        log_entry = {
            "log_id": proposed_log_id,
            "product_id": product_id,
            "event_type": event_type,
            "event_timestamp": event_timestamp,
            "user_id": user_id,
            "detail": detail
        }

        self.logs[proposed_log_id] = log_entry

        return {
            "success": True,
            "message": "Product log entry created",
            "log_id": proposed_log_id
        }

    def update_product_log_entry(
        self,
        log_id: str,
        event_type: str = None,
        event_timestamp: str = None,
        user_id: str = None,
        detail: str = None,
    ) -> dict:
        """
        Modify the details of an existing product log entry.

        Args:
            log_id (str): The unique identifier of the log entry to be updated.
            event_type (str, optional): New event type.
            event_timestamp (str, optional): New event timestamp.
            user_id (str, optional): New user ID responsible for the event.
            detail (str, optional): New detail string.

        Returns:
            dict:
                Success: { "success": True, "message": "Product log entry updated successfully." }
                Failure: { "success": False, "error": "Log entry not found." } or
                         { "success": False, "error": "No fields provided to update." }

        Constraints:
            - The log_id must exist in logs.
            - Only event_type, event_timestamp, user_id, and detail fields are updatable.
        """
        if log_id not in self.logs:
            return { "success": False, "error": "Log entry not found." }

        update_fields = {}
        if event_type is not None:
            update_fields['event_type'] = event_type
        if event_timestamp is not None:
            update_fields['event_timestamp'] = event_timestamp
        if user_id is not None:
            update_fields['user_id'] = user_id
        if detail is not None:
            update_fields['detail'] = detail

        if not update_fields:
            return { "success": False, "error": "No fields provided to update." }

        self.logs[log_id].update(update_fields)
        return { "success": True, "message": "Product log entry updated successfully." }

    def delete_product_log_entry(self, log_id: str, user_id: str) -> dict:
        """
        Remove a product log entry by its log_id if the log exists and user is authorized.

        Args:
            log_id (str): Unique identifier of the product log entry to delete.
            user_id (str): Unique identifier of the user requesting deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Product log entry deleted."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Only authorized users (e.g., role == 'admin') can delete log entries.
            - log_id must exist in the logs dictionary.
        """
        # Check that the user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}

        # Only admin can delete logs
        if user.get("role") != "admin":
            return {"success": False, "error": "Permission denied: only admin can delete log entries"}

        # Check that the log entry exists
        if log_id not in self.logs:
            return {"success": False, "error": "Log entry does not exist"}

        # Perform deletion
        del self.logs[log_id]

        return {"success": True, "message": "Product log entry deleted."}

    def create_user(self, user_id: str, name: str, role: str) -> dict:
        """
        Add a new user to the system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): Name of the user.
            role (str): Role designation for the user.

        Returns:
            dict:
                - On success: { "success": True, "message": "User created successfully." }
                - On failure: { "success": False, "error": "Error message" }

        Constraints:
            - user_id must not already exist.
            - All fields (user_id, name, role) must be provided (nonempty).
        """
        # Field presence checks
        if not user_id or not name or not role:
            return { "success": False, "error": "user_id, name, and role are required." }
        # Uniqueness check
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists." }

        # Construct and add user
        new_user = {
            "user_id": user_id,
            "name": name,
            "role": role,
        }
        self.users[user_id] = new_user

        return { "success": True, "message": "User created successfully." }

    def update_user_role(self, user_id: str, new_role: str) -> dict:
        """
        Update the role/permissions of a user.

        Args:
            user_id (str): The unique identifier of the user whose role is to be changed.
            new_role (str): The new role to assign.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User role updated successfully" }
                On failure:
                    { "success": False, "error": <error_message> }

        Constraints:
            - User with user_id must exist in the system.
            - (Assumed) new_role must be a non-empty string.
            - (Constraint about authorization is skipped since no actor context is provided.)
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if not isinstance(new_role, str) or not new_role.strip():
            return {"success": False, "error": "New role must be a non-empty string"}

        self.users[user_id]["role"] = new_role.strip()
        return {"success": True, "message": "User role updated successfully"}

    def revoke_user_access(
        self,
        user_id: str,
        product_ids: list = None,
        category_ids: list = None
    ) -> dict:
        """
        Remove a user's access to certain products and/or product categories.
        Records the revoked product_ids and/or category_ids under the user's information.

        Args:
            user_id (str): User whose access is to be revoked.
            product_ids (list[str], optional): List of product IDs to revoke access to.
            category_ids (list[str], optional): List of category IDs to revoke access to.

        Returns:
            dict:
                - { "success": True, "message": "User access revoked for specified products/categories." }
                - { "success": False, "error": "reason" }

        Constraints:
            - User must exist.
            - Each product_id and category_id (if provided) must exist.
            - If neither product_ids nor category_ids are provided or both are empty, action is a no-op.
        """
        # Input validation
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        product_ids = product_ids or []
        category_ids = category_ids or []

        # Must specify at least one thing to revoke
        if not product_ids and not category_ids:
            return {"success": False, "error": "No products or categories specified to revoke."}

        invalid_products = [pid for pid in product_ids if pid not in self.products]
        invalid_categories = [cid for cid in category_ids if cid not in self.categories]

        if invalid_products or invalid_categories:
            errors = []
            if invalid_products:
                errors.append(f"Invalid product_ids: {invalid_products}")
            if invalid_categories:
                errors.append(f"Invalid category_ids: {invalid_categories}")
            return {"success": False, "error": "; ".join(errors)}

        # Add per-user revoked lists if not present
        user_info = self.users[user_id]
        if 'revoked_products' not in user_info:
            user_info['revoked_products'] = set()
        if 'revoked_categories' not in user_info:
            user_info['revoked_categories'] = set()
        # Update the revoked products/categories
        user_info['revoked_products'].update(product_ids)
        user_info['revoked_categories'].update(category_ids)

        return {"success": True, "message": "User access revoked for specified products/categories."}


class ProductInformationManagementSystem(BaseEnv):
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
            if key == "validate_product_metadata_schema":
                setattr(env, "_validate_product_metadata_schema_state", copy.deepcopy(value))
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

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_product_by_category(self, **kwargs):
        return self._call_inner_tool('get_product_by_category', kwargs)

    def get_product_metadata(self, **kwargs):
        return self._call_inner_tool('get_product_metadata', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_all_categories(self, **kwargs):
        return self._call_inner_tool('list_all_categories', kwargs)

    def get_logs_by_product_id(self, **kwargs):
        return self._call_inner_tool('get_logs_by_product_id', kwargs)

    def get_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_log_by_id', kwargs)

    def get_logs_by_event_type(self, **kwargs):
        return self._call_inner_tool('get_logs_by_event_type', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_permission_for_product_access(self, **kwargs):
        return self._call_inner_tool('check_user_permission_for_product_access', kwargs)

    def validate_product_metadata_schema(self, **kwargs):
        return self._call_inner_tool('validate_product_metadata_schema', kwargs)

    def create_product(self, **kwargs):
        return self._call_inner_tool('create_product', kwargs)

    def update_product(self, **kwargs):
        return self._call_inner_tool('update_product', kwargs)

    def delete_product(self, **kwargs):
        return self._call_inner_tool('delete_product', kwargs)

    def create_category(self, **kwargs):
        return self._call_inner_tool('create_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)

    def add_product_log_entry(self, **kwargs):
        return self._call_inner_tool('add_product_log_entry', kwargs)

    def update_product_log_entry(self, **kwargs):
        return self._call_inner_tool('update_product_log_entry', kwargs)

    def delete_product_log_entry(self, **kwargs):
        return self._call_inner_tool('delete_product_log_entry', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_role(self, **kwargs):
        return self._call_inner_tool('update_user_role', kwargs)

    def revoke_user_access(self, **kwargs):
        return self._call_inner_tool('revoke_user_access', kwargs)
