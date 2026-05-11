# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime
from typing import List, Dict



# Represents an item in the catalog
class ProductInfo(TypedDict):
    product_id: str
    name: str
    description: str
    category: str
    price: float
    availability_status: str

# Represents a customer/request
class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str

# Represents a generated quotation
class QuotationInfo(TypedDict):
    quote_id: str
    customer_id: str
    product_list: List[str]  # List of product_ids
    quoted_prices: Dict[str, float]  # Maps product_id to quoted price
    validity_period: str
    status: str
    created_at: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Product catalog and quotation management environment.
        State attributes correspond to environment entities.
        """
        # Products: {product_id: ProductInfo} (maps product ID to product metadata)
        self.products: Dict[str, ProductInfo] = {}

        # Customers/Requests: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Quotations: {quote_id: QuotationInfo}
        self.quotations: Dict[str, QuotationInfo] = {}
        
        # Constraints:
        # - Only available products (availability_status = "available") can be included in quotations.
        # - Prices quoted are valid only within the quotation's specified validity period.
        # - Quotations must reference valid existing products from the product catalog.
        # - Each quotation can be generated only upon explicit customer/request.

    def list_available_products(self) -> dict:
        """
        Return all products in the catalog where availability_status is "available".

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProductInfo]  # list may be empty if no products available
                }
        Constraints:
            Only products with availability_status == "available" will be included in the output.
        """
        available_products = [
            product_info for product_info in self.products.values()
            if product_info.get("availability_status") == "available"
        ]
        return { "success": True, "data": available_products }

    def search_products_by_name(self, search_term: str) -> dict:
        """
        Retrieve a list of products whose name matches the provided search term,
        using case-insensitive substring matching.

        Args:
            search_term (str): The search term to look for in the product names.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]
            }
            - The list may be empty if no products match.

        Notes:
            - Matching is case-insensitive and based on substring search.
            - No filtering by availability or other fields.
        """
        term = search_term.lower()
        matches = [
            product_info
            for product_info in self.products.values()
            if term in product_info["name"].lower()
        ]
        return { "success": True, "data": matches }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve detailed information for a specific product by its product_id.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo  # Detailed information about the product
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., product not found
            }

        Constraints:
            - Product must exist in the product catalog.
        """
        product = self.products.get(product_id)
        if product is not None:
            return {"success": True, "data": product}
        else:
            return {"success": False, "error": "Product not found"}

    def filter_products_by_category(self, category: str) -> dict:
        """
        Return all products belonging to the specified category.

        Args:
            category (str): The product category to filter by (exact match).

        Returns:
            dict:
                - "success": True if operation succeeds.
                - "data": List[ProductInfo] for matching products (empty if none found).
        """
        result = [
            product_info for product_info in self.products.values()
            if product_info["category"] == category
        ]
        return { "success": True, "data": result }

    def get_product_price(self, product_id: str) -> dict:
        """
        Return the current price for a product given its product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": float  # Current price of the product
            }
            or
            {
                "success": False,
                "error": str  # Description of why the lookup failed
            }

        Constraints:
            - The product_id must exist in the product catalog; otherwise, the lookup fails.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}

        return {"success": True, "data": product["price"]}

    def get_customer_by_name(self, name: str) -> dict:
        """
        Retrieve customer details (may be multiple) by customer name (case-insensitive).

        Args:
            name (str): The name of the customer to search for.

        Returns:
            dict:
              - On success:
                  {
                      "success": True,
                      "data": List[CustomerInfo]  # one or more matched customers
                  }
              - On failure (no matching customer):
                  {
                      "success": False,
                      "error": "No customer found with the given name"
                  }

        Constraints:
            - Name matching is case-insensitive.
            - All customers with the given name are returned.
        """
        matches = [
            customer
            for customer in self.customers.values()
            if customer["name"].lower() == name.lower()
        ]
        if not matches:
            return { "success": False, "error": "No customer found with the given name" }
        return { "success": True, "data": matches }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer details by their customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: 
                On success: { "success": True, "data": CustomerInfo }
                On failure: { "success": False, "error": "Customer not found" }

        Constraints:
            - The customer_id must exist in the self.customers dictionary.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def list_customer_quotations(self, customer_id: str) -> dict:
        """
        Return all quotations associated with a particular customer_id.

        Args:
            customer_id (str): The unique ID of the customer to look up quotations for.

        Returns:
            dict: {
                "success": True,
                "data": List[QuotationInfo],  # list may be empty if no quotations
            }
            or
            {
                "success": False,
                "error": str  # explanation if customer_id is invalid
            }

        Constraints:
            - The customer_id must exist in the system.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer ID does not exist" }

        quotations = [
            q for q in self.quotations.values()
            if q["customer_id"] == customer_id
        ]
        return { "success": True, "data": quotations }

    def get_quotation_by_id(self, quote_id: str) -> dict:
        """
        Retrieve full details of a specific quotation by quote_id.

        Args:
            quote_id (str): The unique identifier for the quotation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": QuotationInfo
                    }
                On failure (quotation not found):
                    {
                        "success": False,
                        "error": "Quotation does not exist"
                    }
        """
        if quote_id not in self.quotations:
            return { "success": False, "error": "Quotation does not exist" }

        return { "success": True, "data": self.quotations[quote_id] }


    def create_quotation(
        self,
        customer_id: str,
        product_list: List[str],
        quoted_prices: Dict[str, float],
        validity_period: str,
        status: str
    ) -> dict:
        """
        Generate a new quotation for specified available products and a customer, assigning prices and validity.

        Args:
            customer_id (str): The customer/request for whom the quotation is generated.
            product_list (List[str]): List of product_ids to include in the quotation.
            quoted_prices (Dict[str, float]): Mapping of product_id to quoted price.
            validity_period (str): Quotation's validity period.
            status (str): Status string for the quotation (e.g., 'draft', 'sent').

        Returns:
            dict:
                On success: { "success": True, "message": "Quotation <quote_id> created" }
                On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Each product in product_list must exist and be available.
            - quoted_prices must be provided for all products in product_list.
            - customer_id must exist.
            - Each quotation can only be generated upon explicit customer/request.
        """
        # Validate customer_id
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}
    
        # Validate product_list non-empty
        if not product_list:
            return {"success": False, "error": "Quotation must include at least one product"}
    
        # Validate each product
        for pid in product_list:
            if pid not in self.products:
                return {"success": False, "error": f"Product {pid} does not exist"}
            if self.products[pid]['availability_status'] != 'available':
                return {"success": False, "error": f"Product {pid} is not available for quotation"}

        # Validate quoted_prices: must cover each product and only those
        if set(quoted_prices.keys()) != set(product_list):
            return {"success": False, "error": "Quoted prices must be specified for every product in product_list and only those."}

        # Generate unique quote_id
        quote_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        new_quote = {
            "quote_id": quote_id,
            "customer_id": customer_id,
            "product_list": product_list.copy(),
            "quoted_prices": quoted_prices.copy(),
            "validity_period": validity_period,
            "status": status,
            "created_at": created_at
        }

        self.quotations[quote_id] = new_quote

        return {"success": True, "message": f"Quotation {quote_id} created"}

    def update_quotation_status(self, quote_id: str, new_status: str) -> dict:
        """
        Change the status field of a quotation (e.g., mark as sent, accepted, expired, etc.).

        Args:
            quote_id (str): The identifier for the quotation whose status is to be updated.
            new_status (str): The new status value to set.

        Returns:
            dict: {
                "success": True,
                "message": "Quotation status updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The specified quotation must exist in the system.
            - The status field is updated as per input.
        """
        if not quote_id or not isinstance(quote_id, str):
            return { "success": False, "error": "Invalid or missing quote_id." }
        if not new_status or not isinstance(new_status, str):
            return { "success": False, "error": "Invalid or missing new_status." }
        if quote_id not in self.quotations:
            return { "success": False, "error": f"Quotation with id '{quote_id}' does not exist." }

        self.quotations[quote_id]['status'] = new_status
        return { "success": True, "message": "Quotation status updated successfully." }

    def revise_quotation(
        self,
        quote_id: str,
        new_product_list: list = None,
        new_quoted_prices: dict = None,
        new_validity_period: str = None,
        new_status: str = None
    ) -> dict:
        """
        Edit an existing quotation (edit product list, quoted prices, validity period, or status).

        Args:
            quote_id (str): The quotation to edit.
            new_product_list (list[str], optional): New list of product IDs.
            new_quoted_prices (dict[str, float], optional): New mapping from product_id to quoted price.
            new_validity_period (str, optional): New validity period string.
            new_status (str, optional): New status string for the quotation.

        Returns:
            dict: {
                "success": True,
                "message": "Quotation revised successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The quotation must exist.
            - Only available products can be included in the quotation.
            - Quoted prices, if supplied, must correspond to product list.
            - Quotation must reference valid, existing products.
        """
        # Check the quotation exists
        if quote_id not in self.quotations:
            return {"success": False, "error": "Quotation does not exist."}
        quote = self.quotations[quote_id]

        # If no fields to update, return error
        if all(x is None for x in (new_product_list, new_quoted_prices, new_validity_period, new_status)):
            return {"success": False, "error": "No updates specified for revision."}

        # Determine final product list after possible revision
        product_list = new_product_list if new_product_list is not None else quote["product_list"]

        # Validate product list: must refer to valid & available products
        for pid in product_list:
            if pid not in self.products:
                return {"success": False, "error": f"Product '{pid}' does not exist in catalog."}
            if self.products[pid]["availability_status"] != "available":
                return {"success": False, "error": f"Product '{pid}' is not available and cannot be quoted."}

        # Validate quoted prices: all product_ids must be in product_list
        quoted_prices = new_quoted_prices if new_quoted_prices is not None else quote["quoted_prices"]
        for pid in quoted_prices:
            if pid not in product_list:
                return {"success": False, "error": f"Quoted price for product '{pid}' not in quoted product list."}

        if new_status is not None and (not isinstance(new_status, str) or not new_status):
            return {"success": False, "error": "Invalid new_status value."}

        # Optional: ensure all products in product_list have quoted prices (not required unless specification says so)
        # for pid in product_list:
        #     if pid not in quoted_prices:
        #         return {"success": False, "error": f"Missing quoted price for product '{pid}'."}

        # Apply updates
        if new_product_list is not None:
            quote["product_list"] = new_product_list
        if new_quoted_prices is not None:
            quote["quoted_prices"] = new_quoted_prices
        if new_validity_period is not None:
            quote["validity_period"] = new_validity_period
        if new_status is not None:
            quote["status"] = new_status

        return {"success": True, "message": "Quotation revised successfully."}

    def delete_quotation(self, quote_id: str) -> dict:
        """
        Remove a quotation completely from the system.

        Args:
            quote_id (str): The unique identifier of the quotation to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Quotation <id> deleted."
            }
            or
            {
                "success": False,
                "error": "Quotation not found"
            }

        Constraints:
            - quote_id must exist in the quotations database.
            - No restrictions on the status or referencing entities.
        """
        if quote_id not in self.quotations:
            return { "success": False, "error": "Quotation not found" }
    
        del self.quotations[quote_id]
        return { "success": True, "message": f"Quotation {quote_id} deleted." }

    def update_product_availability(self, product_id: str, new_status: str) -> dict:
        """
        Change the availability_status of a product to make it available or unavailable for quoting/sale.

        Args:
            product_id (str): The unique identifier of the product to update.
            new_status (str): The new availability status ("available" or "unavailable").

        Returns:
            dict: Success message or error info:
                { "success": True, "message": "<updated>" }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - product_id must exist in the catalog.
            - new_status should be "available" or "unavailable".
        """
        valid_statuses = {"available", "unavailable"}
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}
        if new_status not in valid_statuses:
            return {"success": False, "error": "Invalid availability_status"}
    
        self.products[product_id]["availability_status"] = new_status
        return {
            "success": True,
            "message": f"Product {product_id} availability_status updated to '{new_status}'"
        }

    def update_product_price(self, product_id: str, new_price: float) -> dict:
        """
        Update the price associated with a given product.

        Args:
            product_id (str): The ID of the product to update.
            new_price (float): The new price to set for the product. Must be non-negative.

        Returns:
            dict:
                On success: { "success": True, "message": "Product price updated successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Product must exist in the catalog.
            - Price must be a non-negative float.
        """
        # Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product not found" }
        # Validate price
        try:
            price_value = float(new_price)
            if price_value < 0:
                return { "success": False, "error": "Invalid price value" }
        except (ValueError, TypeError):
            return { "success": False, "error": "Invalid price value" }
        # Update
        self.products[product_id]['price'] = price_value
        return { "success": True, "message": "Product price updated successfully." }


class ProductCatalogQuotationSystem(BaseEnv):
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

    def list_available_products(self, **kwargs):
        return self._call_inner_tool('list_available_products', kwargs)

    def search_products_by_name(self, **kwargs):
        return self._call_inner_tool('search_products_by_name', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def filter_products_by_category(self, **kwargs):
        return self._call_inner_tool('filter_products_by_category', kwargs)

    def get_product_price(self, **kwargs):
        return self._call_inner_tool('get_product_price', kwargs)

    def get_customer_by_name(self, **kwargs):
        return self._call_inner_tool('get_customer_by_name', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_customer_quotations(self, **kwargs):
        return self._call_inner_tool('list_customer_quotations', kwargs)

    def get_quotation_by_id(self, **kwargs):
        return self._call_inner_tool('get_quotation_by_id', kwargs)

    def create_quotation(self, **kwargs):
        return self._call_inner_tool('create_quotation', kwargs)

    def update_quotation_status(self, **kwargs):
        return self._call_inner_tool('update_quotation_status', kwargs)

    def revise_quotation(self, **kwargs):
        return self._call_inner_tool('revise_quotation', kwargs)

    def delete_quotation(self, **kwargs):
        return self._call_inner_tool('delete_quotation', kwargs)

    def update_product_availability(self, **kwargs):
        return self._call_inner_tool('update_product_availability', kwargs)

    def update_product_price(self, **kwargs):
        return self._call_inner_tool('update_product_price', kwargs)
