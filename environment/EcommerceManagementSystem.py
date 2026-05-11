# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time



class EmployeeInfo(TypedDict):
    employee_id: str
    name: str
    role: str
    contact_info: str
    status: str

class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    price: float
    stock_quantity: int
    description: str
    status: str

class UserAccountInfo(TypedDict):
    user_id: str
    username: str
    contact_info: str
    account_status: str
    created_at: str

class TransactionInfo(TypedDict):
    transaction_id: str
    user_id: str
    products: List[str]
    date: str
    total_amount: float
    status: str

class GSTVerificationInfo(TypedDict):
    gst_number: str
    verification_status: str
    verified_at: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        E-commerce Management System Environment

        # Constraints:
        - Employee and product IDs are unique identifiers.
        - Product catalog supports filtering (by category, etc.) and pagination (page/limit).
        - GST numbers must be verified according to external (governmental) systems.
        - Only products marked with status “active/available” are shown in listings.
        - Transactions must link to valid user accounts and product references.
        """

        # Employees: {employee_id: EmployeeInfo}
        self.employees: Dict[str, EmployeeInfo] = {}

        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # User Accounts: {user_id: UserAccountInfo}
        self.user_accounts: Dict[str, UserAccountInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # GST Verifications: {gst_number: GSTVerificationInfo}
        self.gst_verifications: Dict[str, GSTVerificationInfo] = {}

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve detailed information for an employee using their unique employee_id.

        Args:
            employee_id (str): The unique identifier of the employee.

        Returns:
            dict: 
                - On success: { "success": True, "data": EmployeeInfo }
                - On failure: { "success": False, "error": "Employee not found" }

        Constraints:
            - Employee IDs are unique.
        """
        emp = self.employees.get(employee_id)
        if emp is None:
            return { "success": False, "error": "Employee not found" }
        return { "success": True, "data": emp }

    def get_gst_verification_status(self, gst_number: str) -> dict:
        """
        Query the verification status and details of a GST number from stored records.

        Args:
            gst_number (str): The GST number to look up.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": GSTVerificationInfo  # GST verification details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "GST number not found"
                    }
        """
        gst_info = self.gst_verifications.get(gst_number)
        if gst_info is None:
            return {"success": False, "error": "GST number not found"}
        return {"success": True, "data": gst_info}

    def list_products_by_category(self, category: str) -> dict:
        """
        List all products in a specified category that are currently marked as "active" or "available".

        Args:
            category (str): The product category to filter by (case-sensitive, e.g., "shoes").

        Returns:
            dict:
                On success:
                  {
                    "success": True,
                    "data": List[ProductInfo]  # Only products in category with status "active" or "available"
                  }
                On error:
                  {
                    "success": False,
                    "error": str
                  }

        Constraints:
            - Only "active"/"available" products are returned.
            - Category must be a non-empty string.
        """
        if not isinstance(category, str) or len(category.strip()) == 0:
            return { "success": False, "error": "Category must be a non-empty string" }

        allowed_status = {"active", "available"}
        filtered_products = [
            product for product in self.products.values()
            if product["category"] == category and product["status"].lower() in allowed_status
        ]

        return { "success": True, "data": filtered_products }

    def list_products_paginated(self, page: int, limit: int) -> dict:
        """
        Retrieve a paginated list of products from the catalog, only including those
        with status "active" or "available".

        Args:
            page (int): The 1-based page number to retrieve.
            limit (int): The number of products per page.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],   # The page of products
                "total": int                 # Total count of active/available products
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only products with status "active" or "available" are included.
            - Proper pagination is enforced based on input page/limit.
        """
        if not isinstance(page, int) or not isinstance(limit, int) or page < 1 or limit < 1:
            return {"success": False, "error": "page and limit must be positive integers"}

        # Filter products: only those that are active/available
        allowed_status = {"active", "available"}
        filtered_products = [
            p for p in self.products.values()
            if p.get("status", "").lower() in allowed_status
        ]
        total = len(filtered_products)

        # Pagination: index from (page-1)*limit to page*limit (non-inclusive)
        start = (page - 1) * limit
        end = start + limit

        paginated = filtered_products[start:end] if start < total else []

        return {
            "success": True,
            "data": paginated,
            "total": total
        }

    def list_first_n_products(self, n: int) -> dict:
        """
        Retrieve the first N products from the catalog that have status "active" or "available".
        Products are returned in the default catalog order (insertion order).

        Args:
            n (int): Number of products to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only products with status exactly "active" or "available" (case-insensitive) are considered.
            - n must be a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            return {"success": False, "error": "Parameter 'n' must be a positive integer."}
    
        filtered = [
            product for product in self.products.values()
            if str(product['status']).lower() in ("active", "available")
        ]
    
        result = filtered[:n]
        return {"success": True, "data": result}

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve detailed information for a product using its unique product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": ProductInfo  # Product metadata with all fields.
                }
                - On error: {
                    "success": False,
                    "error": "Product not found"
                }
        Notes:
            - Returns product data regardless of status.
            - Product IDs are unique, so at most one record is returned.
        """
        product = self.products.get(product_id)
        if product is None:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def get_all_products(self) -> dict:
        """
        Retrieve the entire list of all products in the store with status "active" or "available".

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only products where status is "active" or "available" (case-insensitive) are included.
        """
        active_statuses = {"active", "available"}
        result = [
            product_info
            for product_info in self.products.values()
            if product_info["status"].lower() in active_statuses
        ]
        return {"success": True, "data": result}

    def get_user_account_by_id(self, user_id: str) -> dict:
        """
        Retrieve user account info for the specified user ID.

        Args:
            user_id (str): Unique identifier of the user account.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo,
            }
            or
            {
                "success": False,
                "error": str  # "User account not found"
            }

        Constraints:
            - user_id must exist in the system.
        """
        user = self.user_accounts.get(user_id)
        if not user:
            return { "success": False, "error": "User account not found" }
        return { "success": True, "data": user }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve details of a transaction using transaction_id.

        Args:
            transaction_id (str): The unique identifier of the transaction.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo  # Transaction metadata/details
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. transaction not found)
            }

        Constraints:
            - Transaction ID must exist in the system.
            - No verification of related user/product links in this query.
        """
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction not found" }

        transaction_info = self.transactions[transaction_id]
        return { "success": True, "data": transaction_info }

    def verify_gst_number(self, gst_number: str) -> dict:
        """
        Perform GST number verification (simulated) via external system,
        and update/store the verification status and details in the environment.

        Args:
            gst_number (str): The GST number to verify.

        Returns:
            dict: {
                "success": True,
                "message": "GST number verified and info stored."
            }
            or
            {
                "success": False,
                "error": "Invalid GST number."
            }

        Constraints:
            - GST numbers must be verified according to external systems (simulated).
            - Creates or updates GSTVerificationInfo in the environment.
            - Minimal format check for GST number.
        """

        # Minimal check: non-empty and length, you may improve with regex as needed.
        if not isinstance(gst_number, str) or not gst_number.strip() or len(gst_number.strip()) < 6:
            return { "success": False, "error": "Invalid GST number." }

        # Simulate "external" verification: let's say even GST numbers are "VERIFIED", odds are "UNVERIFIED"
        normalized = gst_number.strip()
        # For simplicity, hash or digit-based mock check
        try:
            key_digit = int(''.join([c for c in normalized if c.isdigit()])[:1]) if any(c.isdigit() for c in normalized) else 0
        except ValueError:
            key_digit = 0
        verification_status = "VERIFIED" if key_digit % 2 == 0 else "UNVERIFIED"

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        self.gst_verifications[normalized] = {
            "gst_number": normalized,
            "verification_status": verification_status,
            "verified_at": timestamp
        }

        return {
            "success": True,
            "message": "GST number verified and info stored."
        }


class EcommerceManagementSystem(BaseEnv):
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

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def get_gst_verification_status(self, **kwargs):
        return self._call_inner_tool('get_gst_verification_status', kwargs)

    def list_products_by_category(self, **kwargs):
        return self._call_inner_tool('list_products_by_category', kwargs)

    def list_products_paginated(self, **kwargs):
        return self._call_inner_tool('list_products_paginated', kwargs)

    def list_first_n_products(self, **kwargs):
        return self._call_inner_tool('list_first_n_products', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def get_all_products(self, **kwargs):
        return self._call_inner_tool('get_all_products', kwargs)

    def get_user_account_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_account_by_id', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def verify_gst_number(self, **kwargs):
        return self._call_inner_tool('verify_gst_number', kwargs)

