# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import math



class ProductInfo(TypedDict):
    asin: str
    title: str
    url: str
    image_url: str
    category: str

class PriceRecordInfo(TypedDict):
    asin: str
    price: float
    currency: str
    timestamp: float  # Using float for epoch seconds

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Amazon product price tracker system environment.
        """

        # Products entity: {asin: ProductInfo}
        # entity: Product, attributes: asin, title, url, image_url, category
        self.products: Dict[str, ProductInfo] = {}

        # Price history per product: {asin: List[PriceRecordInfo]}
        # entity: PriceRecord, attributes: asin, price, currency, timestamp
        self.price_history: Dict[str, List[PriceRecordInfo]] = {}

        # --- Constraints (for future enforcement) ---
        # - Each PriceRecord must be associated with a valid Product (asin must exist in Product entity).
        # - Price values should be non-negative.
        # - Timestamps in PriceRecord should be immutable and strictly increasing with new records per ASIN.
        # - Duplicate (asin, timestamp) pairs should not exist.
        # - Only the most recent available price per product is considered for "latest price" queries.
        # - Historical price statistics and charts operate on data from PriceRecord within the requested time window.

    def get_product_by_asin(self, asin: str) -> dict:
        """
        Retrieve full product information for a specified ASIN.

        Args:
            asin (str): Amazon Standard Identification Number (unique product ID).

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo  # Complete product information for given ASIN
            }
            or
            {
                "success": False,
                "error": str  # Error message if ASIN not found
            }

        Constraints:
            - ASIN must exist in the product list (self.products).
        """
        product = self.products.get(asin)
        if product is None:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def list_all_products(self) -> dict:
        """
        Retrieve a summary list of all tracked products.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]   # list may be empty if no products exist
            }
        """
        all_products = list(self.products.values())
        return {
            "success": True,
            "data": all_products
        }

    def get_latest_price(self, asin: str) -> dict:
        """
        Fetch the most recent price record (price, currency, timestamp, asin) for a specified product ASIN.

        Args:
            asin (str): Amazon Standard Identification Number of the product.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": Latest PriceRecordInfo (dict: asin, price, currency, timestamp)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str (reason: ASIN not found or no price history)
                    }

        Constraints:
            - ASIN must exist in the product list.
            - There must be at least one PriceRecordInfo for the product.
            - Returns only the record with the highest timestamp for the ASIN.
        """
        if asin not in self.products:
            return {"success": False, "error": "ASIN does not exist"}

        price_records = self.price_history.get(asin, None)
        if not price_records or len(price_records) == 0:
            return {"success": False, "error": "No price history available for ASIN"}

        # Since timestamps are strictly increasing, the latest is the one with the max timestamp
        latest_record = max(price_records, key=lambda rec: rec["timestamp"])
        return {"success": True, "data": latest_record}

    def get_highest_price(self, asin: str, start_time: float = None, end_time: float = None) -> dict:
        """
        Retrieve the highest observed price (with currency and timestamp) for the specified ASIN,
        optionally within the given time window.

        Args:
            asin (str): ASIN (Amazon product ID) of the product.
            start_time (float, optional): Include only records from this epoch timestamp onwards.
            end_time (float, optional): Include only records up to this epoch timestamp.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "price": float,
                    "currency": str,
                    "timestamp": float
                }
            }
            If no price records are found for the condition (asin, time window), then:
            {
                "success": True,
                "data": None
            }
            On error (e.g. asin does not exist, time window invalid):
            {
                "success": False,
                "error": str
            }
        Constraints:
            - ASIN must exist in products.
            - Only returns highest among available PriceRecords for that ASIN in the specified time window (if any).
            - start_time and end_time, if specified, must form a valid window (start_time <= end_time).
        """
        if asin not in self.products:
            return {"success": False, "error": "ASIN does not exist"}

        if asin not in self.price_history or not self.price_history[asin]:
            return {"success": True, "data": None}

        # Validate time window
        if start_time is not None and end_time is not None:
            if start_time > end_time:
                return {"success": False, "error": "Invalid time window: start_time is after end_time"}

        # Filter records
        records = self.price_history[asin]
        filtered = []
        for rec in records:
            ts = rec["timestamp"]
            if start_time is not None and ts < start_time:
                continue
            if end_time is not None and ts > end_time:
                continue
            filtered.append(rec)

        if not filtered:
            return {"success": True, "data": None}

        # Find record with highest price (if tie, pick the most recent one)
        max_price = max(r["price"] for r in filtered)
        candidates = [r for r in filtered if r["price"] == max_price]
        # Pick the one with latest timestamp if multiple
        highest = max(candidates, key=lambda r: r["timestamp"])

        return {
            "success": True,
            "data": {
                "price": highest["price"],
                "currency": highest["currency"],
                "timestamp": highest["timestamp"]
            }
        }

    def get_lowest_price(
        self,
        asin: str,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Retrieve the lowest observed price (and timestamp/currency) for the given ASIN,
        optionally restricted to a [start_time, end_time] window.

        Args:
            asin (str): The target ASIN.
            start_time (float, optional): Epoch seconds for start of the time window (inclusive).
            end_time (float, optional): Epoch seconds for end of the time window (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": {
                    "price": float,
                    "currency": str,
                    "timestamp": float
                } | None  # None if no price record found in window
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - ASIN must exist in the tracked products.
            - If no price records exist in the time window, data is None.
            - Time window [start_time, end_time] is inclusive. If either not provided, treated as unbounded.
        """
        if asin not in self.products:
            return {"success": False, "error": "Product/ASIN does not exist"}

        price_records = self.price_history.get(asin, [])
        # Filter by time window if provided
        filtered_records = []
        for rec in price_records:
            if start_time is not None and rec["timestamp"] < start_time:
                continue
            if end_time is not None and rec["timestamp"] > end_time:
                continue
            filtered_records.append(rec)

        if not filtered_records:
            return {"success": True, "data": None}

        # Find record(s) with min price
        min_price = min(rec["price"] for rec in filtered_records)
        min_price_records = [rec for rec in filtered_records if rec["price"] == min_price]

        # If multiple, return the earliest timestamp
        best_record = min(min_price_records, key=lambda x: x["timestamp"])

        return {
            "success": True,
            "data": {
                "price": best_record["price"],
                "currency": best_record["currency"],
                "timestamp": best_record["timestamp"]
            }
        }

    def get_price_history(
        self, 
        asin: str, 
        start_time: float = None, 
        end_time: float = None
    ) -> dict:
        """
        Retrieve all price records for a given ASIN, optionally within a provided time window.

        Args:
            asin (str): The ASIN (unique product identifier) to query price history for.
            start_time (float, optional): Minimum timestamp (inclusive) for filtering. Epoch seconds.
            end_time (float, optional): Maximum timestamp (inclusive) for filtering. Epoch seconds.

        Returns:
            dict: On success:
                {"success": True, "data": List[PriceRecordInfo]}
                (list may be empty if no records match.)
            On failure:
                {"success": False, "error": str}

        Constraints:
            - ASIN must exist in the system.
            - If provided, start_time must be <= end_time.
        """
        if asin not in self.products:
            return {"success": False, "error": "Product not found"}
    
        records = self.price_history.get(asin, [])

        # Time window filter
        if start_time is not None and end_time is not None and start_time > end_time:
            return {"success": False, "error": "Invalid time window: start_time > end_time"}

        filtered_records = []
        for rec in records:
            ts = rec["timestamp"]
            if (start_time is not None and ts < start_time):
                continue
            if (end_time is not None and ts > end_time):
                continue
            filtered_records.append(rec)

        return {"success": True, "data": filtered_records}

    def generate_price_history_chart(self, asin: str, start_time: float, end_time: float) -> dict:
        """
        Generate chart data representing the price history for a specified product (ASIN)
        over a given time range.

        Args:
            asin (str): Product ASIN to query.
            start_time (float): Start of the time window (epoch seconds, inclusive).
            end_time (float): End of the time window (epoch seconds, inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict: {"timestamp": float, "price": float, "currency": str}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - ASIN must exist.
            - start_time <= end_time.
            - Only include PriceRecord in the [start_time, end_time] interval.
        """
        # Check: ASIN exists
        if asin not in self.products:
            return {"success": False, "error": "Product with given ASIN does not exist"}

        # Check: valid time window
        if start_time > end_time:
            return {"success": False, "error": "Invalid time range: start_time is after end_time"}

        # Get price history for ASIN
        records = self.price_history.get(asin, [])
        # Only include records within time window
        chart_data = [
            {"timestamp": rec["timestamp"], "price": rec["price"], "currency": rec["currency"]}
            for rec in records
            if start_time <= rec["timestamp"] <= end_time
        ]

        return {"success": True, "data": chart_data}

    def get_price_statistics(self, asin: str, start_time: float, end_time: float) -> dict:
        """
        Aggregate price statistics for a product (by ASIN) over a [start_time, end_time] window.

        Args:
            asin (str): Product ASIN.
            start_time (float): Start of time window (epoch seconds, inclusive).
            end_time (float): End of time window (epoch seconds, inclusive).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "average": float,
                        "stddev": float,
                        "min": float,
                        "max": float,
                        "first": float,
                        "last": float,
                        "currency": str
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - ASIN must be tracked.
            - Time window must be valid.
            - Statistics computed are over records strictly within [start_time, end_time].
        """

        if asin not in self.products:
            return { "success": False, "error": "ASIN not found" }

        if start_time > end_time:
            return { "success": False, "error": "Invalid time window" }

        records = self.price_history.get(asin, [])
        records_in_window = [r for r in records if (start_time <= r["timestamp"] <= end_time)]

        if not records_in_window:
            return { "success": False, "error": "No price records in time window" }

        prices = [r["price"] for r in records_in_window if r["price"] >= 0]
        if not prices:
            return { "success": False, "error": "No valid price records in window" }

        # Assume all price records for an ASIN use the same currency (enforced elsewhere)
        currency = records_in_window[0]["currency"]

        n = len(prices)
        average = sum(prices) / n
        if n == 1:
            stddev = 0.0
        else:
            mean = average
            variance = sum((p - mean) ** 2 for p in prices) / n
            stddev = math.sqrt(variance)

        min_price = min(prices)
        max_price = max(prices)

        # Sort by timestamp to get first and last
        records_in_window_sorted = sorted(records_in_window, key=lambda r: r["timestamp"])
        first = records_in_window_sorted[0]["price"]
        last = records_in_window_sorted[-1]["price"]

        result = {
            "average": average,
            "stddev": stddev,
            "min": min_price,
            "max": max_price,
            "first": first,
            "last": last,
            "currency": currency
        }
        return { "success": True, "data": result }

    def validate_asin_exists(self, asin: str) -> dict:
        """
        Check if a given ASIN is present in the Product entity.

        Args:
            asin (str): The ASIN to validate.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if the ASIN exists, False otherwise.
            }
        Constraints:
            - None. Returns True/False based on presence of asin in products.
        """
        exists = asin in self.products
        return {"success": True, "exists": exists}

    def add_product(
        self,
        asin: str,
        title: str,
        url: str,
        image_url: str,
        category: str
    ) -> dict:
        """
        Add a new product to the system.

        Args:
            asin (str): The unique Amazon product identifier.
            title (str): Product title.
            url (str): Amazon product URL.
            image_url (str): URL to the product image.
            category (str): Product category.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Product with ASIN <asin> successfully added."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Description of the reason (e.g., ASIN exists, missing field)"
                    }

        Constraints:
            - ASIN must be unique/not already present.
            - All fields are required and must be non-empty.
        """
        # Validate required fields are all present and non-empty
        if not all([asin, title, url, image_url, category]):
            return {
                "success": False,
                "error": "All fields (asin, title, url, image_url, category) are required and must be non-empty."
            }

        # ASIN must be unique
        if asin in self.products:
            return {
                "success": False,
                "error": f"Product with ASIN {asin} already exists."
            }

        # Add the new product
        product_info: ProductInfo = {
            "asin": asin,
            "title": title,
            "url": url,
            "image_url": image_url,
            "category": category
        }
        self.products[asin] = product_info

        return {
            "success": True,
            "message": f"Product with ASIN {asin} successfully added."
        }

    def update_product_info(
        self,
        asin: str,
        title: str = None,
        url: str = None,
        image_url: str = None,
        category: str = None
    ) -> dict:
        """
        Update metadata information of an existing product.

        Args:
            asin (str): The ASIN of the product to update.
            title (str, optional): New title for the product.
            url (str, optional): New URL for the product.
            image_url (str, optional): New image URL for the product.
            category (str, optional): New category for the product.

        Returns:
            dict:
                - On success: {"success": True, "message": "..."}
                - On failure: {"success": False, "error": "..."}

        Constraints:
            - Product with the given ASIN must exist.
            - At least one metadata field must be provided for update.
            - ASIN may not be changed.
        """
        if asin not in self.products:
            return {
                "success": False,
                "error": f"Product with ASIN {asin} not found."
            }

        # Collect the fields to update
        updates = {}
        if title is not None:
            updates['title'] = title
        if url is not None:
            updates['url'] = url
        if image_url is not None:
            updates['image_url'] = image_url
        if category is not None:
            updates['category'] = category

        if not updates:
            return {
                "success": False,
                "error": "No update fields provided."
            }

        # Perform updates
        for key, value in updates.items():
            self.products[asin][key] = value

        return {
            "success": True,
            "message": f"Product info for ASIN {asin} updated successfully."
        }

    def remove_product(self, asin: str) -> dict:
        """
        Delete a product specified by its ASIN from the system, including all associated PriceRecords.

        Args:
            asin (str): The ASIN of the product to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Product and associated price records deleted."
            }
            or
            {
                "success": False,
                "error": "Product does not exist"
            }

        Constraints:
            - Only removes if the product exists.
            - Removes all associated price records (if any).
        """
        if asin not in self.products:
            return {"success": False, "error": "Product does not exist"}

        # Remove the product entry
        del self.products[asin]

        # Remove associated price records, if present
        if asin in self.price_history:
            del self.price_history[asin]

        return {"success": True, "message": "Product and associated price records deleted."}

    def add_price_record(
        self, 
        asin: str, 
        price: float, 
        currency: str, 
        timestamp: float
    ) -> dict:
        """
        Insert a new price record for an ASIN.

        Args:
            asin (str): The product's ASIN (must exist).
            price (float): The observed price (must be non-negative).
            currency (str): Currency code for the price.
            timestamp (float): Epoch time of the observation (must be strictly increasing for this ASIN).

        Returns:
            dict: Success: { "success": True, "message": ... }
                  Failure: { "success": False, "error": ... }

        Constraints:
            - ASIN must exist in Product entity.
            - Price must be non-negative.
            - Timestamp must be strictly greater than previous records for this ASIN.
            - Duplicate (asin, timestamp) records are forbidden.
        """
        # 1. ASIN existence check
        if asin not in self.products:
            return { "success": False, "error": "ASIN does not exist" }
        # 2. Price non-negative
        if price < 0:
            return { "success": False, "error": "Price must be non-negative" }
        # 3. Retrieve price history for this ASIN (if any)
        records = self.price_history.get(asin, [])
        # 4. Check for duplicate (asin, timestamp)
        if any(r["timestamp"] == timestamp for r in records):
            return { "success": False, "error": "Duplicate (asin, timestamp) price record" }
        # 5. Timestamp strictly increasing
        if records and timestamp <= records[-1]["timestamp"]:
            return { "success": False, "error": "Timestamp must be strictly increasing for the ASIN" }
        # 6. Add record
        record = {
            "asin": asin,
            "price": price,
            "currency": currency,
            "timestamp": timestamp,
        }
        self.price_history.setdefault(asin, []).append(record)
        return { 
            "success": True,
            "message": f"Price record added for ASIN {asin} at {timestamp}." 
        }

    def delete_price_record(self, asin: str, timestamp: float) -> dict:
        """
        Remove a specific price record identified by ASIN and timestamp.

        Args:
            asin (str): The ASIN (Amazon product identifier) of the product.
            timestamp (float): The timestamp (epoch seconds) of the price record to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Price record deleted."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - The (asin, timestamp) pair must exist uniquely in price_history.
            - Associated product (ASIN) must exist.
            - On success, the price record is removed and no data corruption occurs.
        """
        if asin not in self.products:
            return {"success": False, "error": "ASIN does not exist."}

        if asin not in self.price_history or not self.price_history[asin]:
            return {"success": False, "error": "No price records found for this ASIN."}

        # Find the record index in the list for the given timestamp
        price_records = self.price_history[asin]
        idx_to_remove = None
        for i, rec in enumerate(price_records):
            if rec["timestamp"] == timestamp:
                idx_to_remove = i
                break

        if idx_to_remove is None:
            return {"success": False, "error": "No matching price record found for the given timestamp."}

        # Remove the record
        del self.price_history[asin][idx_to_remove]
        # Optionally, remove asin key from price_history if now empty, or leave as empty list (either is OK)
        # if not self.price_history[asin]:
        #     del self.price_history[asin]

        return {"success": True, "message": "Price record deleted."}

    def purge_price_records_by_time(
        self, 
        asin: str, 
        start_time: float, 
        end_time: float
    ) -> dict:
        """
        Delete all price records for a given ASIN that have a timestamp between start_time and end_time (inclusive).

        Args:
            asin (str): The ASIN of the product whose price records should be purged.
            start_time (float): Epoch time (inclusive) for start of purge window.
            end_time (float): Epoch time (inclusive) for end of purge window.

        Returns:
            dict: 
                - On success: { "success": True, "message": "<N> price records deleted for ASIN <asin> within time window." }
                - On error: { "success": False, "error": "error message" }

        Constraints:
            - ASIN must exist in the Product entity.
            - start_time must be <= end_time.
        """
        if asin not in self.products:
            return { "success": False, "error": "ASIN does not exist." }
        if start_time > end_time:
            return { "success": False, "error": "Invalid time window: start_time > end_time." }

        orig_records = self.price_history.get(asin, [])
        remaining_records = [
            rec for rec in orig_records
            if not (start_time <= rec["timestamp"] <= end_time)
        ]
        deleted_count = len(orig_records) - len(remaining_records)
        self.price_history[asin] = remaining_records

        return {
            "success": True,
            "message": f"{deleted_count} price records deleted for ASIN {asin} within time window."
        }

    def correct_price_record(self, asin: str, timestamp: float, new_price: float) -> dict:
        """
        Modify the price value of the price record for a given product (ASIN) at a specific timestamp.

        Args:
            asin (str): The ASIN of the product whose price record is to be corrected.
            timestamp (float): The timestamp (epoch seconds) of the target price record.
            new_price (float): The corrected, non-negative price value.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Price record updated successfully" }
                - On failure: { "success": False, "error": <reason str> }

        Constraints:
            - ASIN must correspond to a valid product.
            - Price value must be non-negative.
            - The (asin, timestamp) record must exist.
        """
        # Validate asin exists
        if asin not in self.products:
            return { "success": False, "error": "ASIN does not exist" }
        # Validate non-negative price
        if not isinstance(new_price, (int, float)) or new_price < 0:
            return { "success": False, "error": "Price must be a non-negative number" }

        # Validate we have price record list for asin
        if asin not in self.price_history or not self.price_history[asin]:
            return { "success": False, "error": "No price records found for this ASIN" }

        # Locate the price record
        for record in self.price_history[asin]:
            if record["timestamp"] == timestamp:
                # Perform correction
                record["price"] = new_price
                return { "success": True, "message": "Price record updated successfully" }

        # No matching timestamp found
        return { "success": False, "error": "No price record found for given ASIN and timestamp" }


class AmazonPriceTrackerSystem(BaseEnv):
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

    def get_product_by_asin(self, **kwargs):
        return self._call_inner_tool('get_product_by_asin', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_latest_price(self, **kwargs):
        return self._call_inner_tool('get_latest_price', kwargs)

    def get_highest_price(self, **kwargs):
        return self._call_inner_tool('get_highest_price', kwargs)

    def get_lowest_price(self, **kwargs):
        return self._call_inner_tool('get_lowest_price', kwargs)

    def get_price_history(self, **kwargs):
        return self._call_inner_tool('get_price_history', kwargs)

    def generate_price_history_chart(self, **kwargs):
        return self._call_inner_tool('generate_price_history_chart', kwargs)

    def get_price_statistics(self, **kwargs):
        return self._call_inner_tool('get_price_statistics', kwargs)

    def validate_asin_exists(self, **kwargs):
        return self._call_inner_tool('validate_asin_exists', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_info(self, **kwargs):
        return self._call_inner_tool('update_product_info', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)

    def add_price_record(self, **kwargs):
        return self._call_inner_tool('add_price_record', kwargs)

    def delete_price_record(self, **kwargs):
        return self._call_inner_tool('delete_price_record', kwargs)

    def purge_price_records_by_time(self, **kwargs):
        return self._call_inner_tool('purge_price_records_by_time', kwargs)

    def correct_price_record(self, **kwargs):
        return self._call_inner_tool('correct_price_record', kwargs)

