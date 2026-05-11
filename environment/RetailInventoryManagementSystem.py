# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import time
from typing import List, Dict, Union



# Represents each distinct item in the store
class ProductInfo(TypedDict):
    product_id: str
    product_name: str
    current_stock_count: int
    last_updated_timestamp: Union[str, float]  # timestamp as ISO string or Unix epoch

# Records each modification to a product’s stock count
class InventoryChangeLogInfo(TypedDict):
    product_id: str
    previous_stock_count: int
    new_stock_count: int
    change_timestamp: Union[str, float]

class _GeneratedEnvImpl:
    def __init__(self):
        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # InventoryChangeLog: List of InventoryChangeLogInfo
        self.inventory_change_log: List[InventoryChangeLogInfo] = []

        # Constraints:
        # - product_id must be unique for each product.
        # - current_stock_count should be non-negative.
        # - Each update to a product’s stock count must be recorded in InventoryChangeLog with a valid timestamp.
        # - last_updated_timestamp must reflect the most recent update for each product.
        # - Only recognized products (existing product_id) can have their inventory updated.

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve full product information given a product_id.

        Args:
            product_id (str): Identifier of the product to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - product_id must exist in the current product records.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}

        return {"success": True, "data": product}

    def list_all_products(self) -> dict:
        """
        Retrieve a list of all products currently tracked by the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # All products, possibly empty if none exist
            }

        Constraints:
            - No input constraints; returns all products as currently tracked.
        """
        result = list(self.products.values())
        return { "success": True, "data": result }

    def get_current_stock_count(self, product_id: str) -> dict:
        """
        Retrieve the current stock count for the product with the specified product_id.

        Args:
            product_id (str): Unique identifier of the product.

        Returns:
            dict: 
            - On success: { "success": True, "data": current_stock_count }
            - On failure: { "success": False, "error": "Product not found" }

        Constraints:
            - Only recognized products (existing product_id) can be queried.
        """
        product = self.products.get(product_id)
        if product is None:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product["current_stock_count"] }

    def get_last_updated_timestamp(self, product_id: str) -> dict:
        """
        Retrieve the last_updated_timestamp for a given product.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": str | float   # last_updated_timestamp as ISO string or Unix epoch
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. product not found
            }

        Constraints:
            - Only recognized products (existing product_id) can be queried.
        """
        product = self.products.get(product_id)
        if product is None:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": product["last_updated_timestamp"]}

    def get_inventory_change_log(self) -> dict:
        """
        Retrieve the complete inventory change log for auditing and review.
    
        Args:
            None
    
        Returns:
            dict: {
                "success": True,
                "data": List[InventoryChangeLogInfo]  # all inventory change records; may be empty list
            }
        """
        return {
            "success": True,
            "data": self.inventory_change_log.copy()  # Defensive copy to avoid external mutation
        }

    def get_product_change_log(self, product_id: str) -> dict:
        """
        Retrieve all inventory change log entries for the specified product.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryChangeLogInfo]  # All change log entries for product,
            }
            OR
            {
                "success": False,
                "error": "Product not found"
            }

        Constraints:
            - product_id must exist in the products.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        logs = [
            entry for entry in self.inventory_change_log
            if entry["product_id"] == product_id
        ]

        return {"success": True, "data": logs}


    def update_product_stock(self, product_id: str, new_stock_count: int) -> dict:
        """
        Update the stock count and last_updated_timestamp for a product.
        Also records the change in the InventoryChangeLog.

        Args:
            product_id (str): Unique identifier for the product to update.
            new_stock_count (int): The new stock count (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Stock updated for product <product_id>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - product_id must exist.
            - new_stock_count should be non-negative.
            - Each update is logged in inventory_change_log.
            - last_updated_timestamp is set to current time (Unix epoch).
        """
        if product_id not in self.products:
            return {"success": False, "error": f"Product with ID '{product_id}' does not exist."}

        if not isinstance(new_stock_count, int) or new_stock_count < 0:
            return {"success": False, "error": "new_stock_count must be a non-negative integer."}

        prev_stock = self.products[product_id]['current_stock_count']
        now = time.time()

        # Update product info
        self.products[product_id]['current_stock_count'] = new_stock_count
        self.products[product_id]['last_updated_timestamp'] = now

        # Record the change log
        log_entry = {
            'product_id': product_id,
            'previous_stock_count': prev_stock,
            'new_stock_count': new_stock_count,
            'change_timestamp': now
        }
        self.inventory_change_log.append(log_entry)

        return {
            "success": True,
            "message": f"Stock updated for product {product_id}."
        }

    def record_inventory_change(
        self,
        product_id: str,
        previous_stock_count: int,
        new_stock_count: int,
        change_timestamp: 'str|float'
    ) -> dict:
        """
        Append a new entry to InventoryChangeLog for a given product's stock update.

        Args:
            product_id (str): The ID of the product whose inventory has changed.
            previous_stock_count (int): The stock count before the change.
            new_stock_count (int): The stock count after the change.
            change_timestamp (str|float): The timestamp of the change (ISO8601 or Unix epoch).

        Returns:
            dict: 
                - On success: {"success": True, "message": "Inventory change recorded for product <product_id>."}
                - On failure: {"success": False, "error": str}

        Constraints:
            - The product_id must exist in self.products.
            - Both stock counts must be non-negative integers.
            - change_timestamp must be provided (as str or float).
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product ID does not exist." }
        if not isinstance(previous_stock_count, int) or previous_stock_count < 0:
            return { "success": False, "error": "previous_stock_count must be a non-negative integer." }
        if not isinstance(new_stock_count, int) or new_stock_count < 0:
            return { "success": False, "error": "new_stock_count must be a non-negative integer." }
        if change_timestamp is None or (not isinstance(change_timestamp, (str, float, int))):
            return { "success": False, "error": "Invalid or missing change_timestamp." }

        entry: InventoryChangeLogInfo = {
            "product_id": product_id,
            "previous_stock_count": previous_stock_count,
            "new_stock_count": new_stock_count,
            "change_timestamp": change_timestamp
        }
        self.inventory_change_log.append(entry)
        return {
            "success": True,
            "message": f"Inventory change recorded for product {product_id}."
        }


    def batch_update_product_stock(self, updates: List[Dict[str, Union[str, int]]]) -> Dict:
        """
        Perform batch updates to multiple products' stock counts atomically.
    
        Args:
            updates (List[dict]): Each dict must contain:
                - 'product_id' (str): The ID of the product to update.
                - 'new_stock_count' (int): The new stock count (must be non-negative).
    
        Returns:
            dict: {
                "success": True,
                "message": "Batch update of X products completed successfully"
            }
            or
            {
                "success": False,
                "error": str,
                "failed_ids": List[str]  # List of product_ids that triggered the error
            }
    
        Constraints:
            - All product_ids must exist.
            - All new_stock_count must be >= 0.
            - The update must be atomic: if any update fails constraint, no changes or logs are made.
            - After each update, log the change with a valid timestamp and update the product's last_updated_timestamp.
        """
        # Collect validation errors first
        failed_ids = []
        for upd in updates:
            product_id = upd.get('product_id')
            new_stock = upd.get('new_stock_count')
            # Check product existence
            if product_id not in self.products:
                failed_ids.append(product_id)
            # Check valid stock count
            elif new_stock is None or not isinstance(new_stock, int) or new_stock < 0:
                failed_ids.append(product_id)
    
        if failed_ids:
            return {
                "success": False,
                "error": "Some product_ids missing or invalid new_stock_count values.",
                "failed_ids": failed_ids
            }

        # Passed all checks; perform update atomically
        timestamp = time.time()
        for upd in updates:
            product_id = upd['product_id']
            new_stock = upd['new_stock_count']
            product_info = self.products[product_id]
            prev_stock = product_info['current_stock_count']
            # Update product info
            product_info['current_stock_count'] = new_stock
            product_info['last_updated_timestamp'] = timestamp
            self.products[product_id] = product_info
            # Record inventory change log
            log_entry: InventoryChangeLogInfo = {
                "product_id": product_id,
                "previous_stock_count": prev_stock,
                "new_stock_count": new_stock,
                "change_timestamp": timestamp
            }
            self.inventory_change_log.append(log_entry)

        return {
            "success": True,
            "message": f"Batch update of {len(updates)} products completed successfully"
        }

    def set_product_last_updated_timestamp(self, product_id: str, last_updated_timestamp: 'Union[str, float]') -> dict:
        """
        Directly modify a product's last_updated_timestamp for correction or administrative purposes.

        Args:
            product_id (str): The ID of the product to update.
            last_updated_timestamp (Union[str, float]): The new timestamp to assign (ISO string or Unix epoch).

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message.
            }
            or
            {
                "success": False,
                "error": str    # Description of the failure.
            }

        Constraints:
            - The product_id must exist in the system.
            - Only affects the last_updated_timestamp field, not stock count nor logs.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product not found" }

        self.products[product_id]['last_updated_timestamp'] = last_updated_timestamp

        return { "success": True, "message": f"last_updated_timestamp updated for product_id '{product_id}'" }


class RetailInventoryManagementSystem(BaseEnv):
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

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_current_stock_count(self, **kwargs):
        return self._call_inner_tool('get_current_stock_count', kwargs)

    def get_last_updated_timestamp(self, **kwargs):
        return self._call_inner_tool('get_last_updated_timestamp', kwargs)

    def get_inventory_change_log(self, **kwargs):
        return self._call_inner_tool('get_inventory_change_log', kwargs)

    def get_product_change_log(self, **kwargs):
        return self._call_inner_tool('get_product_change_log', kwargs)

    def update_product_stock(self, **kwargs):
        return self._call_inner_tool('update_product_stock', kwargs)

    def record_inventory_change(self, **kwargs):
        return self._call_inner_tool('record_inventory_change', kwargs)

    def batch_update_product_stock(self, **kwargs):
        return self._call_inner_tool('batch_update_product_stock', kwargs)

    def set_product_last_updated_timestamp(self, **kwargs):
        return self._call_inner_tool('set_product_last_updated_timestamp', kwargs)

