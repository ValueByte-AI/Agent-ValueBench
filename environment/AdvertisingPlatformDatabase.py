# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
from typing import List, Dict, Optional
from datetime import date



class UserInfo(TypedDict):
    _id: str
    username: str
    contact_info: str
    account_status: str  # e.g., "active", "suspended"
    join_date: str       # ISO format date string
    last_login: str      # ISO format date string

class ProductInfo(TypedDict):
    product_id: str
    name: str
    description: str
    category: str

class ProductPriceInfo(TypedDict):
    product_id: str
    price: float
    effective_date: str  # ISO format date string

class CampaignInfo(TypedDict):
    campaign_id: str
    name: str
    product_id: str
    user_id: str
    start_date: str      # ISO format date string
    end_date: str        # ISO format date string
    status: str
    budget: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        # State space mapping: User [_id, username, contact_info, account_status, join_date, last_login]
        self.users: Dict[str, UserInfo] = {}

        # Products: {product_id: ProductInfo}
        # State space mapping: Product [product_id, name, description, category]
        self.products: Dict[str, ProductInfo] = {}

        # Product prices: {product_id: [ProductPriceInfo, ...]}
        # State space mapping: ProductPrice [product_id, price, effective_date]
        self.product_prices: Dict[str, List[ProductPriceInfo]] = {}

        # Campaigns: {campaign_id: CampaignInfo}
        # State space mapping: Campaign [campaign_id, name, product_id, user_id, start_date, end_date, status, budget]
        self.campaigns: Dict[str, CampaignInfo] = {}

        # Constraints:
        # - ProductPrice entries for a given product should not have overlapping effective_date ranges.
        # - Only active users (account_status = "active") can launch new campaigns.
        # - Product references in Campaign and ProductPrice must exist in the Product entity.
        # - The most recent price (by effective_date ≤ today) is used as today's price.
        self._benchmark_today: Optional[date] = None

    @staticmethod
    def _parse_iso_date(raw: object) -> Optional[date]:
        if not isinstance(raw, str) or not raw.strip():
            return None
        text = raw.strip()
        if "T" in text:
            text = text.split("T", 1)[0]
        if text.endswith("Z"):
            text = text[:-1]
        try:
            return date.fromisoformat(text)
        except Exception:
            return None

    def _get_benchmark_today(self) -> date:
        if self._benchmark_today is not None:
            return self._benchmark_today

        last_login_dates: List[date] = []
        for user in self.users.values():
            if isinstance(user, dict):
                parsed = self._parse_iso_date(user.get("last_login"))
                if parsed is not None:
                    last_login_dates.append(parsed)
        if last_login_dates:
            self._benchmark_today = max(last_login_dates)
            return self._benchmark_today

        fallback_dates: List[date] = []
        for user in self.users.values():
            if isinstance(user, dict):
                parsed = self._parse_iso_date(user.get("join_date"))
                if parsed is not None:
                    fallback_dates.append(parsed)
        for price_history in self.product_prices.values():
            if isinstance(price_history, list):
                for price_info in price_history:
                    if isinstance(price_info, dict):
                        parsed = self._parse_iso_date(price_info.get("effective_date"))
                        if parsed is not None:
                            fallback_dates.append(parsed)
        for campaign in self.campaigns.values():
            if isinstance(campaign, dict):
                for key in ("start_date", "end_date"):
                    parsed = self._parse_iso_date(campaign.get(key))
                    if parsed is not None:
                        fallback_dates.append(parsed)

        self._benchmark_today = max(fallback_dates) if fallback_dates else date(2023, 1, 1)
        return self._benchmark_today

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve all information for a user by their username.

        Args:
            username (str): The username of the user to find.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            } if found,
            {
                "success": False,
                "error": "User not found"
            } otherwise.

        Constraints:
            - Username is assumed to be unique, but returns the first match if not.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, _id: str) -> dict:
        """
        Fetch user details by the user’s unique _id.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict:
                On success: {"success": True, "data": UserInfo}
                On failure: {"success": False, "error": "User not found"}

        Constraints:
            - The user with the specified _id must exist.
        """
        user = self.users.get(_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def list_all_users(self) -> dict:
        """
        Return a list of all users registered on the platform.

        Args:
            None

        Returns:
            dict:
                - success: True if operation was successful
                - data: List[UserInfo] (possibly empty if no users exist)
        """
        user_list = list(self.users.values())
        return { "success": True, "data": user_list }

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Retrieve the current account status (e.g., active, suspended) of a user.

        Args:
            user_id (str): Unique identifier (_id) of the user.

        Returns:
            dict: 
                On success: 
                    {"success": True, "data": {"_id": <user_id>, "account_status": <str>}}
                On failure: 
                    {"success": False, "error": "User not found"}

        Constraints:
            - The user_id must refer to an existing user in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        return {
            "success": True,
            "data": {
                "_id": user["_id"],
                "account_status": user["account_status"]
            }
        }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Fetch product information for a given product_id.

        Args:
            product_id (str): Unique identifier of the product to fetch.

        Returns:
            dict:
                Success: { "success": True, "data": ProductInfo }
                Failure: { "success": False, "error": "Product not found" }

        Constraints:
            - product_id must exist in the product database.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def list_all_products(self) -> dict:
        """
        List all products in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of all products (may be empty if no products exist)
            }
        """
        all_products = list(self.products.values())
        return { "success": True, "data": all_products }


    def get_product_price_by_date(self, product_id: str, query_date: str) -> dict:
        """
        Retrieve the most recent price for the given product effective on or before the specified date.

        Args:
            product_id (str): The product ID to query.
            query_date (str): The date (ISO format string, YYYY-MM-DD) for which to get the price.

        Returns:
            dict:
                {
                    "success": True,
                    "data": ProductPriceInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Product reference must exist in the product catalog.
            - Price must be effective on or before the query date.
        """
        # Check if product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        # Get price history for product
        price_history = self.product_prices.get(product_id, [])
        if not price_history:
            return {"success": False, "error": "No price history found for this product"}

        try:
            query_dt = datetime.fromisoformat(query_date)
        except Exception:
            return {"success": False, "error": "Invalid query_date format"}

        # Find all prices with effective_date <= query_date
        eligible_prices = []
        for price_info in price_history:
            try:
                eff_dt = datetime.fromisoformat(price_info["effective_date"])
            except Exception:
                continue  # Skip invalid dates
            if eff_dt <= query_dt:
                eligible_prices.append((eff_dt, price_info))

        if not eligible_prices:
            return {"success": False, "error": "No price set for this product before or on the given date"}

        # Get the price with the most recent effective_date
        eligible_prices.sort(key=lambda tup: tup[0], reverse=True)
        latest_price_info = eligible_prices[0][1]
        return {"success": True, "data": latest_price_info}


    def get_products_today_prices(self, product_ids: List[str]) -> dict:
        """
        Retrieve benchmark-today's price for one or more specified product_ids, determined by the
        most recent ProductPriceInfo record with effective_date ≤ the environment's controlled benchmark date.
    
        Args:
            product_ids (List[str]): List of product_id strings whose prices are to be queried.

        Returns:
            dict:
              {
                "success": True,
                "data": {
                    product_id1: ProductPriceInfo or None,  # ProductPriceInfo if found, else None
                    product_id2: ...
                }
              }
              or
              {
                "success": False,
                "error": str  # Description of the error
              }

        Constraints:
            - Ignore products that do not exist; return None for such keys in result.
            - If a product has no effective price up to the benchmark date, its value is also None.
            - ProductPriceInfo returned should be the one with max effective_date ≤ the benchmark date.
        """
        if not isinstance(product_ids, list):
            return { "success": False, "error": "Input must be a list of product_ids" }
        benchmark_today = self._get_benchmark_today()
        result: Dict[str, Optional[dict]] = {}
        for pid in product_ids:
            # Validate product existence
            if pid not in self.products:
                result[pid] = None
                continue
            # Get price history for this product
            price_history = self.product_prices.get(pid, [])
            # Find price entries with effective_date <= benchmark_today
            valid_prices = []
            for price_entry in price_history:
                try:
                    eff_date = datetime.strptime(price_entry['effective_date'], "%Y-%m-%d").date()
                except Exception:
                    continue  # ignore malformed date records
                if eff_date <= benchmark_today:
                    valid_prices.append((eff_date, price_entry))
            if not valid_prices:
                result[pid] = None
            else:
                # Pick entry with max effective_date (most recent)
                most_recent = max(valid_prices, key=lambda x: x[0])[1]
                result[pid] = most_recent
        return { "success": True, "data": result }

    def get_product_price_history(self, product_id: str) -> dict:
        """
        Retrieve the full chronological price history for a specific product.

        Args:
            product_id (str): Unique identifier for the product.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ProductPriceInfo]  # Sorted chronologically by effective_date
                    }
                - On product not found:
                    {
                        "success": False,
                        "error": "Product does not exist"
                    }

        Constraints:
            - Product with the provided product_id must exist.
            - Returns empty list if no price records are found for the product.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        price_history = self.product_prices.get(product_id, [])

        # Sort by effective_date ascending (oldest first)
        sorted_history = sorted(
            price_history, 
            key=lambda x: x["effective_date"]
        )
        return {"success": True, "data": sorted_history}

    def get_campaign_by_id(self, campaign_id: str) -> dict:
        """
        Retrieve campaign details by campaign_id.

        Args:
            campaign_id (str): The unique identifier of the campaign.

        Returns:
            dict: 
                - On success:
                    { "success": True, "data": CampaignInfo }
                - On failure (if campaign_id not found):
                    { "success": False, "error": "Campaign not found" }
        Constraints:
            - None. This is a simple lookup operation.
        """
        campaign = self.campaigns.get(campaign_id)
        if campaign is None:
            return { "success": False, "error": "Campaign not found" }
        return { "success": True, "data": campaign }

    def list_user_campaigns(self, user_id: str) -> dict:
        """
        List all campaigns launched by the specified user.

        Args:
            user_id (str): The ID of the user whose campaigns to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # List of campaigns belonging to user
            }
            or
            {
                "success": False,
                "error": str  # If user does not exist
            }

        Constraints:
            - The user with user_id must exist in the platform.
            - Returns all campaigns where campaign.user_id == user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        campaigns = [
            campaign_info
            for campaign_info in self.campaigns.values()
            if campaign_info["user_id"] == user_id
        ]

        return { "success": True, "data": campaigns }

    def list_product_campaigns(self, product_id: str) -> dict:
        """
        List all campaigns advertising a specified product.

        Args:
            product_id (str): The ID of the product whose campaigns are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo], # List of campaigns linked to the product (may be empty)
            }
            or
            {
                "success": False,
                "error": str # Reason for failure, e.g., "Product not found"
            }

        Constraints:
            - Only return campaigns where campaign['product_id'] == product_id
            - The product_id must exist in self.products.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product not found" }

        result = [
            campaign for campaign in self.campaigns.values()
            if campaign["product_id"] == product_id
        ]

        return { "success": True, "data": result }


    def list_active_campaigns(self) -> dict:
        """
        Retrieve all currently active campaigns using the environment's controlled benchmark date.
        A campaign is considered active if:
            - status == "active"
            - start_date <= benchmark_today <= end_date

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # List of active campaigns' info (may be empty if none)
            }
        """
        benchmark_today_iso = self._get_benchmark_today().isoformat()
        result = []
        for campaign in self.campaigns.values():
            status = campaign.get("status", "")
            start_date_str = campaign.get("start_date", "")
            end_date_str = campaign.get("end_date", "")
            if status != "active":
                continue
            # Date format is assumed to be YYYY-MM-DD; do simple string comparison.
            if start_date_str <= benchmark_today_iso <= end_date_str:
                result.append(campaign)
        return {"success": True, "data": result}

    def add_user(
        self,
        _id: str,
        username: str,
        contact_info: str,
        account_status: str,
        join_date: str,
        last_login: str
    ) -> dict:
        """
        Add a new user to the database.

        Args:
            _id (str): Unique user identifier.
            username (str): Username for the user (must not duplicate existing usernames).
            contact_info (str): Contact information for the user.
            account_status (str): Account status, e.g. 'active', 'suspended'.
            join_date (str): User join date in ISO format.
            last_login (str): Last login date/time in ISO format.

        Returns:
            dict: {
                "success": True,
                "message": "User successfully added"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - _id must be unique.
            - username must be unique.
            - All attributes must be provided and non-empty.
            - No validation is done for account_status or dates beyond non-empty fields.
        """
        # Check if all required fields are provided
        required_fields = {
            "_id": _id,
            "username": username,
            "contact_info": contact_info,
            "account_status": account_status,
            "join_date": join_date,
            "last_login": last_login
        }
        for key, value in required_fields.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return { "success": False, "error": f"Missing required user attribute: {key}" }

        # Check for duplicate ID
        if _id in self.users:
            return { "success": False, "error": "User ID already exists" }
    
        # (Optional strictness) Check for duplicate username
        for user in self.users.values():
            if user["username"] == username:
                return { "success": False, "error": "Username already exists" }
    
        # Compose UserInfo and add to users
        self.users[_id] = {
            "_id": _id,
            "username": username,
            "contact_info": contact_info,
            "account_status": account_status,
            "join_date": join_date,
            "last_login": last_login
        }

        return { "success": True, "message": "User successfully added" }

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Set or update a user's account status.

        Args:
            user_id (str): The unique ID of the user whose status is being updated.
            new_status (str): The new status to assign (e.g., "active", "suspended").

        Returns:
            dict: 
                - On success: { "success": True, "message": "User account status updated to <new_status>." }
                - On error:   { "success": False, "error": "reason" }
    
        Constraints:
            - The user with the given user_id must exist.
            - No explicit check for valid statuses in constraints; any string accepted.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        if not new_status or not isinstance(new_status, str):
            return { "success": False, "error": "Invalid new status" }
        user["account_status"] = new_status
        return { "success": True, "message": f"User account status updated to {new_status}." }

    def add_product(self, product_id: str, name: str, description: str, category: str) -> dict:
        """
        Add a new product to the platform.

        Args:
            product_id (str): Unique identifier for the product.
            name (str): Name of the product.
            description (str): Description of the product.
            category (str): Category this product belongs to.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Product added successfully."}
                On failure (duplicate product_id, missing required info):
                    {"success": False, "error": str}
        Constraints:
            - product_id must be unique within the products table.
            - All parameters are required and must be non-empty.
        """
        if not all([product_id, name, description, category]):
            return {"success": False, "error": "All product fields must be provided and non-empty."}

        if product_id in self.products:
            return {"success": False, "error": f"Product with id '{product_id}' already exists."}

        self.products[product_id] = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "category": category
        }
        return {"success": True, "message": "Product added successfully."}

    def update_product_info(
        self,
        product_id: str,
        name: str = None,
        description: str = None,
        category: str = None
    ) -> dict:
        """
        Update information for an existing product.

        Args:
            product_id (str): The unique identifier of the product to update.
            name (str, optional): New product name.
            description (str, optional): New product description.
            category (str, optional): New product category.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Product information updated." }
                - On failure:
                    { "success": False, "error": <string error message> }

        Constraints:
            - Product with product_id must exist.
            - At least one field to update (name, description, category) must be provided.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found."}

        if name is None and description is None and category is None:
            return {"success": False, "error": "No update fields specified."}

        product = self.products[product_id]
        if name is not None:
            product["name"] = name
        if description is not None:
            product["description"] = description
        if category is not None:
            product["category"] = category

        # Changes are applied in-place.
        return {"success": True, "message": "Product information updated."}

    def add_product_price(self, product_id: str, price: float, effective_date: str) -> dict:
        """
        Adds a new ProductPriceInfo record for a product.
        Ensures:
            - The product exists.
            - No ProductPriceInfo for the same product has the same effective_date (no overlapping price entries).

        Args:
            product_id (str): The ID of the product.
            price (float): The price to record for the product.
            effective_date (str): The ISO-format date when the price becomes effective.

        Returns:
            dict: 
                On success: 
                  { "success": True, "message": "Product price added for product_id {product_id} on {effective_date}" }
                On failure: 
                  { "success": False, "error": "reason" }
        """
        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        # Fetch existing price history (or create list)
        price_list = self.product_prices.get(product_id, [])

        # Enforce: no same effective_date for this product
        for price_entry in price_list:
            if price_entry["effective_date"] == effective_date:
                return { "success": False, "error": "A price for this product and date already exists" }

        # Add new price entry
        new_entry = {
            "product_id": product_id,
            "price": price,
            "effective_date": effective_date
        }
        price_list.append(new_entry)
        # Sort price entries by date ascending, for cleanliness
        price_list.sort(key=lambda d: d["effective_date"])
        self.product_prices[product_id] = price_list

        return {
            "success": True,
            "message": f"Product price added for product_id {product_id} on {effective_date}"
        }

    def update_product_price(self, product_id: str, effective_date: str, price: float) -> dict:
        """
        Update the price for a product's price record that matches the given effective_date.

        Args:
            product_id (str): The ID of the product.
            effective_date (str): The ISO date string for the record to update.
            price (float): The new price to set.

        Returns:
            dict: {
                "success": True,
                "message": "Product price updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - product_id must exist in the products database.
            - There must exist a ProductPrice record for (product_id, effective_date).
            - No overlapping effective_date ranges are allowed (not relevant for price edits only, but checked if date were changeable).
        """
        # Check if product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}
    
        # Check that there is a price series for the product
        if product_id not in self.product_prices or not self.product_prices[product_id]:
            return {"success": False, "error": "No price records exist for product."}
    
        # Find the record to update
        found = False
        for price_info in self.product_prices[product_id]:
            if price_info["effective_date"] == effective_date:
                price_info["price"] = price
                found = True
                break

        if not found:
            return {"success": False, "error": "No price record found for this product and effective_date."}

        return {"success": True, "message": "Product price updated successfully."}

    def delete_product_price(self, product_id: str, effective_date: str) -> dict:
        """
        Remove a price record for a product by product_id and effective_date.

        Args:
            product_id (str): The product to remove the price record from.
            effective_date (str): The ISO date string representing the price's effective date.

        Returns:
            dict: {
                "success": True,
                "message": "Price record for product {product_id} at {effective_date} deleted."
            }
            or
            {
                "success": False,
                "error": str  # description: product/price does not exist
            }

        Constraints:
            - Product must exist.
            - ProductPrice entry must exist for product_id and effective_date.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }

        price_list = self.product_prices.get(product_id, [])
        new_price_list = [p for p in price_list if p["effective_date"] != effective_date]
        if len(new_price_list) == len(price_list):
            return { "success": False, "error": "Price record not found." }

        self.product_prices[product_id] = new_price_list
        return {
            "success": True,
            "message": f"Price record for product {product_id} at {effective_date} deleted."
        }

    def add_campaign(
        self,
        campaign_id: str,
        name: str,
        product_id: str,
        user_id: str,
        start_date: str,
        end_date: str,
        status: str,
        budget: float
    ) -> dict:
        """
        Create a new campaign, validating that:
          - The user exists and account_status is 'active'.
          - The product exists.
          - The campaign_id is unique.

        Args:
            campaign_id (str): Unique campaign identifier.
            name (str): Campaign name.
            product_id (str): ID of the product advertised.
            user_id (str): ID of the user launching the campaign.
            start_date (str): Campaign start date (ISO format).
            end_date (str): Campaign end date (ISO format).
            status (str): Campaign status.
            budget (float): Budget of the campaign.

        Returns:
            dict: {
                "success": True,
                "message": "Campaign added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        """
        # Check campaign_id unique
        if campaign_id in self.campaigns:
            return { "success": False, "error": "Campaign ID already exists." }
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }
        # Check user is active
        if user["account_status"] != "active":
            return { "success": False, "error": "User is not active." }
        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }

        # All constraints passed: create the campaign
        campaign_info = {
            "campaign_id": campaign_id,
            "name": name,
            "product_id": product_id,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "budget": budget,
        }
        self.campaigns[campaign_id] = campaign_info

        return { "success": True, "message": "Campaign added successfully." }

    def update_campaign_status(self, campaign_id: str, new_status: str) -> dict:
        """
        Change a campaign’s status to the specified value.

        Args:
            campaign_id (str): The unique identifier of the campaign to update.
            new_status (str): The new status for the campaign (e.g., "active", "paused", "ended").

        Returns:
            dict: {
                "success": True,
                "message": "Campaign {campaign_id} status updated to {new_status}."
            }
            or
            {
                "success": False,
                "error": "Campaign not found."
            }

        Constraints:
            - Campaign with given campaign_id must exist.
            - No explicit validation for allowed statuses.
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found."}

        self.campaigns[campaign_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Campaign {campaign_id} status updated to {new_status}."
        }

    def delete_campaign(self, campaign_id: str) -> dict:
        """
        Delete a campaign from the system.

        Args:
            campaign_id (str): The unique ID of the campaign to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Campaign <campaign_id> deleted successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Campaign not found."
                    }

        Constraints:
            - The campaign identified by campaign_id must exist in the system.
            - No cascade deletion or related cleanup is specified.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign not found." }
    
        del self.campaigns[campaign_id]
        return { "success": True, "message": f"Campaign {campaign_id} deleted successfully." }


class AdvertisingPlatformDatabase(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_product_price_by_date(self, **kwargs):
        return self._call_inner_tool('get_product_price_by_date', kwargs)

    def get_products_today_prices(self, **kwargs):
        return self._call_inner_tool('get_products_today_prices', kwargs)

    def get_product_price_history(self, **kwargs):
        return self._call_inner_tool('get_product_price_history', kwargs)

    def get_campaign_by_id(self, **kwargs):
        return self._call_inner_tool('get_campaign_by_id', kwargs)

    def list_user_campaigns(self, **kwargs):
        return self._call_inner_tool('list_user_campaigns', kwargs)

    def list_product_campaigns(self, **kwargs):
        return self._call_inner_tool('list_product_campaigns', kwargs)

    def list_active_campaigns(self, **kwargs):
        return self._call_inner_tool('list_active_campaigns', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_account_status(self, **kwargs):
        return self._call_inner_tool('update_user_account_status', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_info(self, **kwargs):
        return self._call_inner_tool('update_product_info', kwargs)

    def add_product_price(self, **kwargs):
        return self._call_inner_tool('add_product_price', kwargs)

    def update_product_price(self, **kwargs):
        return self._call_inner_tool('update_product_price', kwargs)

    def delete_product_price(self, **kwargs):
        return self._call_inner_tool('delete_product_price', kwargs)

    def add_campaign(self, **kwargs):
        return self._call_inner_tool('add_campaign', kwargs)

    def update_campaign_status(self, **kwargs):
        return self._call_inner_tool('update_campaign_status', kwargs)

    def delete_campaign(self, **kwargs):
        return self._call_inner_tool('delete_campaign', kwargs)
