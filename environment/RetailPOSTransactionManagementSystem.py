# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



# TypedDicts for structured entity data

class ProductInfo(TypedDict):
    # From Product: product_id, name, category, current_price
    product_id: str
    name: str
    category: str
    current_price: float

class StoreLocationInfo(TypedDict):
    # From StoreLocation: location_id, name, address
    location_id: str
    name: str
    address: str

class TransactionItemInfo(TypedDict):
    # From TransactionItem: transaction_id, product_id, quantity, unit_price
    transaction_id: str
    product_id: str
    quantity: int
    unit_price: float

class TransactionInfo(TypedDict):
    # From Transaction: transaction_id, timestamp, location_id, payment_method, transaction_items, total_amount
    transaction_id: str
    timestamp: str
    location_id: str
    payment_method: str
    transaction_items: List[TransactionItemInfo]
    total_amount: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing the state of a Retail POS Transaction Management System

        Constraints:
        - Each transaction is linked to exactly one location via location_id.
        - Transaction timestamps are immutable once recorded.
        - Each TransactionItem references exactly one Transaction and one Product.
        - Product pricing and details are referenced as current at the time of the transaction.
        - Transaction data must be accessible by date range and location for reporting and auditing.
        """

        # Products sold through the POS system
        # Keyed by product_id
        self.products: Dict[str, ProductInfo] = {}

        # Store locations involved in transactions
        # Keyed by location_id
        self.store_locations: Dict[str, StoreLocationInfo] = {}

        # All sales transactions (records include reference to items, payment, total)
        # Keyed by transaction_id
        self.transactions: Dict[str, TransactionInfo] = {}

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve details of a specific transaction, including all items and metadata.

        Args:
            transaction_id (str): The unique ID of the transaction to query.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo               # All transaction metadata and items
            }
            or
            {
                "success": False,
                "error": str                          # Reason for failure (e.g., transaction not found)
            }

        Constraints:
            - The given transaction_id must exist in the system.
        """
        tx = self.transactions.get(transaction_id)
        if tx is None:
            return { "success": False, "error": "Transaction not found" }
        return { "success": True, "data": tx }

    def list_transactions_by_location(self, location_id: str) -> dict:
        """
        Retrieve all transactions for a specific store location.

        Args:
            location_id (str): The ID of the store location.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo]  # List may be empty if no transactions for location
            }
            or
            {
                "success": False,
                "error": str  # error message if location does not exist
            }

        Constraints:
            - The location_id must correspond to an existing store location.
            - All transactions where 'location_id' matches are included.
        """
        if location_id not in self.store_locations:
            return { "success": False, "error": "Store location does not exist." }
    
        result = [
            transaction for transaction in self.transactions.values()
            if transaction['location_id'] == location_id
        ]
        return { "success": True, "data": result }


    def list_transactions_by_date_range(self, start_date: str, end_date: str) -> dict:
        """
        Retrieve all transactions within the specified start and end date (inclusive).

        Args:
            start_date (str): Range start (inclusive), ISO 8601 string (e.g. '2024-06-01T00:00:00')
            end_date (str): Range end (inclusive), ISO 8601 string (e.g. '2024-06-30T23:59:59')

        Returns:
            dict:
            - { "success": True, "data": List[TransactionInfo] }
            - { "success": False, "error": <reason str> }

        Constraints:
            - Both dates must be parseable ISO8601 date/time strings.
            - start_date must be <= end_date (inclusive).
        """
        # Validate date formats
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except Exception:
            return { "success": False, "error": "Invalid date format. Use ISO 8601 date/time strings." }
        if start_dt > end_dt:
            return { "success": False, "error": "Start date must be before or equal to end date." }

        results = []
        for tx in self.transactions.values():
            try:
                tx_dt = datetime.fromisoformat(tx["timestamp"])
            except Exception:
                continue  # skip malformed transaction (shouldn't occur, but defensive)
            if start_dt <= tx_dt <= end_dt:
                results.append(tx)

        return { "success": True, "data": results }


    def list_transactions_by_location_and_date_range(
        self,
        location_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Retrieve all transactions for a given location within a specified (inclusive) date range.

        Args:
            location_id (str): The location/store to filter by.
            start_date (str): ISO date string ("YYYY-MM-DD"), inclusive.
            end_date (str): ISO date string ("YYYY-MM-DD"), inclusive.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo]  # Possibly empty
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - location_id must exist in the system.
            - start_date and end_date must be valid ISO dates and start_date <= end_date.
            - Only transactions with matching location and whose
              timestamp's date part is between start_date and end_date (inclusive) are included.
        """
        # Check location
        if location_id not in self.store_locations:
            return {"success": False, "error": "Location does not exist"}

        # Validate dates and correct range
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
        if start_dt > end_dt:
            return {"success": False, "error": "Start date cannot be after end date."}

        result = []
        for txn in self.transactions.values():
            if txn["location_id"] != location_id:
                continue
            try:
                txn_date = datetime.fromisoformat(txn["timestamp"]).date()
            except Exception:
                # skip transactions with malformed timestamp
                continue
            if start_dt <= txn_date <= end_dt:
                result.append(txn)

        return {"success": True, "data": result}

    def get_transaction_items(self, transaction_id: str) -> dict:
        """
        List all items (products, quantities, unit prices) in a given transaction.

        Args:
            transaction_id (str): The identifier of the transaction to query.

        Returns:
            dict:
                - If transaction found:
                    { "success": True, "data": List[TransactionItemInfo] }
                - If not found:
                    { "success": False, "error": "Transaction not found" }

        Constraints:
            - Transaction must exist in the system.
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Transaction not found" }

        transaction_items = transaction.get("transaction_items", [])
        return { "success": True, "data": transaction_items }

    def get_store_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve the details for a specific store location.

        Args:
            location_id (str): The unique identifier of the store location.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": StoreLocationInfo
                }
                On failure,
                {
                    "success": False,
                    "error": str  # "Store location not found"
                }

        Constraints:
            - The store location must exist in the system.
        """
        store = self.store_locations.get(location_id)
        if store is None:
            return { "success": False, "error": "Store location not found" }
        return { "success": True, "data": store }

    def list_all_store_locations(self) -> dict:
        """
        List all retail store locations managed by the system.

        Returns:
            dict: {
                "success": True,
                "data": List[StoreLocationInfo]  # List of all store locations, possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Error message, if internal failure occurs
            }
        """
        if not hasattr(self, "store_locations") or self.store_locations is None:
            return { "success": False, "error": "Store locations data unavailable." }

        locations = list(self.store_locations.values())
        return { "success": True, "data": locations }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve product details by product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo,   # Product details if product_id is found
            }
            OR
            {
                "success": False,
                "error": str           # Reason for failure, e.g., 'Product not found'
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
        List all products in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # List of all products (can be empty if no products exist)
            }

        Constraints:
            - None (simply returns all available products).
            - If no products are registered, returns an empty list.
        """
        # Retrieve all ProductInfo entries as a list
        products_list = list(self.products.values())
        return {
            "success": True,
            "data": products_list
        }

    def get_transactions_by_product_id(self, product_id: str) -> dict:
        """
        List all transactions that include at least one TransactionItem for the specified product.

        Args:
            product_id (str): The ID of the product to search for in transactions.

        Returns:
            dict:
                - If successful, {
                      "success": True,
                      "data": List[TransactionInfo]  # May be empty if no transactions contain this product
                  }
                - If product does not exist, {
                      "success": False,
                      "error": "Product not found"
                  }

        Constraints:
            - Product must exist in the system.
            - Only transactions containing this product will be returned.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        result = []
        for transaction in self.transactions.values():
            for item in transaction.get("transaction_items", []):
                if item["product_id"] == product_id:
                    result.append(transaction)
                    break  # Avoid duplicates; one match per transaction is sufficient

        return {"success": True, "data": result}

    def summarize_transactions(
        self,
        location_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Returns aggregate transaction data for a given store location and date range.

        Args:
            location_id (str): ID of the store location.
            start_date (str): Start date (inclusive), format 'YYYY-MM-DD' or ISO date string.
            end_date (str): End date (inclusive), format 'YYYY-MM-DD' or ISO date string.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "location_id": str,
                    "transaction_count": int,
                    "total_sales_amount": float
                }
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - Only considers transactions for this location.
            - Only considers transactions where start_date <= timestamp <= end_date.
            - If no transactions found, returns counts/sums of 0.
            - Returns error if location_id doesn't exist.
            - Date strings compared lexicographically (expecting ISO format).
        """
        if location_id not in self.store_locations:
            return { "success": False, "error": "Location not found" }
        # Validate date string format (assume at least length and ordering)
        if (
            not isinstance(start_date, str) or not isinstance(end_date, str) or
            len(start_date) < 10 or len(end_date) < 10
        ):
            return { "success": False, "error": "Invalid date format" }

        if start_date > end_date:
            return { "success": False, "error": "Start date is after end date" }

        transaction_count = 0
        total_sales_amount = 0.0

        for t in self.transactions.values():
            if t["location_id"] != location_id:
                continue
            # Acceptable timestamp string assumed to start with 'YYYY-MM-DD'
            tx_date = t["timestamp"][:10]
            if start_date <= tx_date <= end_date:
                transaction_count += 1
                total_sales_amount += t.get("total_amount", 0.0)

        return {
            "success": True,
            "data": {
                "location_id": location_id,
                "transaction_count": transaction_count,
                "total_sales_amount": total_sales_amount
            }
        }

    def add_transaction(
        self,
        transaction_id: str,
        timestamp: str,
        location_id: str,
        payment_method: str,
        transaction_items: list,
        total_amount: float
    ) -> dict:
        """
        Records a new transaction and its items in the system.

        Args:
            transaction_id (str): Unique ID for the transaction.
            timestamp (str): Transaction datetime (immutable after recording).
            location_id (str): Store location where transaction occurred (must exist).
            payment_method (str): Payment method (e.g. "Cash", "Card").
            transaction_items (list of dict): Each item should be {
                'product_id': str,
                'quantity': int,
                'unit_price': float
            }
            total_amount (float): Total amount of the transaction.

        Returns:
            dict: On success,
                { "success": True, "message": "Transaction added successfully" }
            On error,
                { "success": False, "error": <reason> }

        Constraints:
        - transaction_id must be unique.
        - location_id must exist.
        - Each product_id must reference an existing product.
        - Quantity must be >0.
        - Transaction timestamps are immutable after recording.
        """
        # Check transaction uniqueness
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists" }

        # Check location exists
        if location_id not in self.store_locations:
            return { "success": False, "error": "Location does not exist" }

        # Validate items
        items_list = []
        for idx, item in enumerate(transaction_items):
            # product_id, quantity, unit_price required:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            unit_price = item.get('unit_price')
            # Check product exists
            if not product_id or (product_id not in self.products):
                return {"success": False, "error": f"Product with ID {product_id} does not exist (item #{idx+1})"}
            # Check quantity
            if not isinstance(quantity, int) or quantity <= 0:
                return {"success": False, "error": f"Invalid quantity for product {product_id} (item #{idx+1})"}
            # Check unit_price
            if not isinstance(unit_price, (int, float)) or unit_price < 0:
                return {"success": False, "error": f"Invalid unit_price for product {product_id} (item #{idx+1})"}
            items_list.append({
                "transaction_id": transaction_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": float(unit_price)
            })

        # All checks passed – record transaction
        new_transaction = {
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "location_id": location_id,
            "payment_method": payment_method,
            "transaction_items": items_list,
            "total_amount": float(total_amount)
        }
        self.transactions[transaction_id] = new_transaction
        return { "success": True, "message": "Transaction added successfully" }

    def void_transaction(self, transaction_id: str) -> dict:
        """
        Mark a transaction as voided/cancelled.
        - Maintains audit trail: does NOT alter timestamp or original transaction items/details.
        - If already voided, operation is idempotent (returns error).
    
        Args:
            transaction_id (str): The ID of the transaction to be voided.
    
        Returns:
            dict:
                - On success: { "success": True, "message": "Transaction <id> marked as voided." }
                - On failure: { "success": False, "error": <reason> }
        Constraints:
            - Transaction must exist.
            - Transaction must not already be voided.
            - Does not modify timestamp, transaction_items, or total_amount.
            - Retains all original details for audit trail.
        """
        txn = self.transactions.get(transaction_id)
        if txn is None:
            return { "success": False, "error": "Transaction not found." }

        # We dynamically add a 'voided' attribute if it doesn't exist.
        if txn.get("voided", False):
            return { "success": False, "error": "Transaction is already voided." }

        txn["voided"] = True
        # Optionally, record audit info such as 'voided_timestamp' or 'voided_reason' in real systems
        # Here, just mark as voided per requirements

        return { "success": True, "message": f"Transaction {transaction_id} marked as voided." }

    def add_product(
        self, 
        product_id: str, 
        name: str, 
        category: str, 
        current_price: float
    ) -> dict:
        """
        Add a new product to the product catalog.

        Args:
            product_id (str): Unique product identifier.
            name (str): Product's name.
            category (str): Product's category.
            current_price (float): Product's current price. Must be >= 0.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Product <product_id> added successfully."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - product_id must be unique (not already in catalog).
            - current_price must be non-negative.
            - name and category must be non-empty.
        """
        if not product_id or not product_id.strip():
            return {"success": False, "error": "Product ID must not be empty."}
        if product_id in self.products:
            return {"success": False, "error": "Product ID already exists."}
        if not name or not name.strip():
            return {"success": False, "error": "Product name must not be empty."}
        if not category or not category.strip():
            return {"success": False, "error": "Product category must not be empty."}
        if not isinstance(current_price, (int, float)) or current_price < 0:
            return {"success": False, "error": "Current price must be a non-negative number."}

        product_info: ProductInfo = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "current_price": float(current_price)
        }
        self.products[product_id] = product_info

        return {"success": True, "message": f"Product {product_id} added successfully."}

    def update_product_price(self, product_id: str, new_price: float) -> dict:
        """
        Update the current price for a given product.
        Does NOT affect past transactions.

        Args:
            product_id (str): The unique identifier for the product to update.
            new_price (float): The new price to set. Must be non-negative.

        Returns:
            dict: {
                "success": True,
                "message": "Product price updated successfully."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Product must already exist in the system.
            - new_price must be non-negative.
            - Only the 'current_price' on product is changed; past transactions are immutable.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found."}
        if not isinstance(new_price, (int, float)) or new_price < 0:
            return {"success": False, "error": "New price must be non-negative."}

        product["current_price"] = float(new_price)
        return {"success": True, "message": "Product price updated successfully."}

    def add_store_location(self, location_id: str, name: str, address: str) -> dict:
        """
        Add a new store location to the system.

        Args:
            location_id (str): Unique identifier for the store location (must not already exist).
            name (str): Name of the store location.
            address (str): Address of the store location.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Store location <location_id> added." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - location_id must be unique.
            - All fields must be non-empty.
        """
        if not location_id or not name or not address:
            return { "success": False, "error": "All fields (location_id, name, address) are required and must be non-empty." }
        if location_id in self.store_locations:
            return { "success": False, "error": "Location ID already exists." }
        self.store_locations[location_id] = {
            "location_id": location_id,
            "name": name,
            "address": address
        }
        return { "success": True, "message": f"Store location {location_id} added." }

    def update_store_location(
        self,
        location_id: str,
        name: str = None,
        address: str = None
    ) -> dict:
        """
        Edit metadata (name, address) for an existing store location.

        Args:
            location_id (str): ID of the store location to update.
            name (str, optional): New store name (if provided).
            address (str, optional): New store address (if provided).

        Returns:
            dict: {
                "success": True,
                "message": "Store location updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - location_id must exist.
            - At least one of name or address must be provided.
            - Only provided fields are updated.
        """
        if location_id not in self.store_locations:
            return {"success": False, "error": "Store location does not exist."}
        if name is None and address is None:
            return {"success": False, "error": "No update fields provided. Specify at least one of name or address."}

        if name is not None:
            self.store_locations[location_id]["name"] = name
        if address is not None:
            self.store_locations[location_id]["address"] = address

        return {"success": True, "message": "Store location updated."}


class RetailPOSTransactionManagementSystem(BaseEnv):
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

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def list_transactions_by_location(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_location', kwargs)

    def list_transactions_by_date_range(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_date_range', kwargs)

    def list_transactions_by_location_and_date_range(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_location_and_date_range', kwargs)

    def get_transaction_items(self, **kwargs):
        return self._call_inner_tool('get_transaction_items', kwargs)

    def get_store_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_store_location_by_id', kwargs)

    def list_all_store_locations(self, **kwargs):
        return self._call_inner_tool('list_all_store_locations', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_transactions_by_product_id(self, **kwargs):
        return self._call_inner_tool('get_transactions_by_product_id', kwargs)

    def summarize_transactions(self, **kwargs):
        return self._call_inner_tool('summarize_transactions', kwargs)

    def add_transaction(self, **kwargs):
        return self._call_inner_tool('add_transaction', kwargs)

    def void_transaction(self, **kwargs):
        return self._call_inner_tool('void_transaction', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_price(self, **kwargs):
        return self._call_inner_tool('update_product_price', kwargs)

    def add_store_location(self, **kwargs):
        return self._call_inner_tool('add_store_location', kwargs)

    def update_store_location(self, **kwargs):
        return self._call_inner_tool('update_store_location', kwargs)

