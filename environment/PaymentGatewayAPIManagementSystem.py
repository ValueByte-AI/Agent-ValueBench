# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict, Any
import time
from datetime import datetime



# TypedDict for API entity
class APIInfo(TypedDict):
    api_name: str
    status: str
    last_checked_time: str  # ISO8601 timestamp string
    response_times: List[float]  # list of response durations (seconds)
    availability_history: List[str]  # list of timestamps when available/unavailable

# TypedDict for Channel entity
class ChannelInfo(TypedDict):
    channel_id: str
    name: str
    api_name: str  # reference to API
    status: str
    configuration: Dict[str, Any]  # configuration details
    supported_currency: List[str]  # list of ISO currency codes

# TypedDict for Product entity
class ProductInfo(TypedDict):
    product_id: str
    name: str
    price: float
    currency: str
    availability_status: str
    metadata: Dict[str, Any]  # miscellaneous product metadata

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Stateful management system for payment gateway APIs, channels, and products.
        """

        # APIs: {api_name: APIInfo}
        self.apis: Dict[str, APIInfo] = {}
        # Channels: {channel_id: ChannelInfo}
        self.channels: Dict[str, ChannelInfo] = {}
        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}
        self.valid_user_ids: set[str] = set()

        # Constraints (for implementation in logic methods):
        # - Valid product/channel IDs must correspond to existing entities.
        # - API status must be consistently monitored and reflect near real-time state.
        # - Channel status must update in response to API status changes and configuration updates.
        # - Only authorized users/merchants can access or manage specific products, channels, or APIs.

    @staticmethod
    def _normalize_authorizations(authorizations: Any, apis: Dict[str, APIInfo], channels: Dict[str, ChannelInfo], products: Dict[str, ProductInfo]) -> Dict[str, Dict[str, set]]:
        normalized: Dict[str, Dict[str, set]] = {
            "product": {},
            "channel": {},
            "api": {},
        }

        def add(entity_type: str, entity_id: str, user_id: str) -> None:
            if entity_type not in normalized or not entity_id or not user_id:
                return
            normalized[entity_type].setdefault(entity_id, set()).add(user_id)

        def resolve_entity_type(entity_key: str) -> Optional[str]:
            if entity_key in channels:
                return "channel"
            if entity_key in products:
                return "product"
            if entity_key in apis:
                return "api"
            return None

        if authorizations is None:
            return normalized

        if isinstance(authorizations, str):
            stripped = authorizations.strip()
            if not stripped:
                return normalized
            try:
                authorizations = json.loads(stripped)
            except Exception:
                return normalized

        if not isinstance(authorizations, dict):
            return normalized

        # Internal form: {"channel": {"chan_1": ["user_a"]}, ...}
        if set(authorizations.keys()) & {"product", "channel", "api"}:
            for entity_type in ("product", "channel", "api"):
                entity_map = authorizations.get(entity_type, {})
                if not isinstance(entity_map, dict):
                    continue
                for entity_id, users in entity_map.items():
                    if isinstance(users, str):
                        users = [users]
                    if isinstance(users, (list, tuple, set)):
                        for user_id in users:
                            if isinstance(user_id, str) and user_id:
                                add(entity_type, entity_id, user_id)
            return normalized

        # Merchant-centric form: {"merch_001": {"channels": ["chan_1"]}}
        merchant_centric = all(isinstance(v, dict) for v in authorizations.values())
        if merchant_centric:
            for user_id, grants in authorizations.items():
                if not isinstance(user_id, str) or not isinstance(grants, dict):
                    continue
                for plural_type, entity_ids in grants.items():
                    entity_type = {"products": "product", "channels": "channel", "apis": "api"}.get(plural_type)
                    if entity_type is None:
                        continue
                    if isinstance(entity_ids, str):
                        entity_ids = [entity_ids]
                    if isinstance(entity_ids, (list, tuple, set)):
                        for entity_id in entity_ids:
                            if isinstance(entity_id, str):
                                add(entity_type, entity_id, user_id)
            return normalized

        # Entity-centric form: {"chan_1": ["user_a", "user_b"]}
        for entity_id, users in authorizations.items():
            entity_type = resolve_entity_type(entity_id)
            if entity_type is None:
                continue
            if isinstance(users, str):
                users = [users]
            if isinstance(users, (list, tuple, set)):
                for user_id in users:
                    if isinstance(user_id, str) and user_id:
                        add(entity_type, entity_id, user_id)

        return normalized

    def _is_user_authorized_for_entity(self, entity_type: str, entity_id: str, user_id: Optional[str]) -> bool:
        if not isinstance(user_id, str) or not user_id:
            return False

        raw_policy = getattr(self, "_authorize_user_for_entity_state", None)
        if isinstance(raw_policy, str) and raw_policy and user_id == raw_policy:
            return True

        entity_map = getattr(self, "authorizations", {}).get(entity_type, {})
        authorized_users = entity_map.get(entity_id, set())
        return user_id in authorized_users

    def _is_known_user_id(self, user_id: str) -> bool:
        if not isinstance(user_id, str) or not user_id:
            return False
        valid_user_ids = getattr(self, "valid_user_ids", set())
        if not valid_user_ids:
            return True
        return user_id in valid_user_ids

    def get_api_info(self, api_name: str) -> dict:
        """
        Retrieve all current operational and health metrics for a specified API by name.

        Args:
            api_name (str): The name of the API to query.

        Returns:
            dict: {
                "success": True,
                "data": APIInfo,  # Complete dictionary describing the API's status and metrics
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., API not found)
            }

        Constraints:
            - The given api_name must correspond to an existing API entity in the system.
        """
        if api_name not in self.apis:
            return { "success": False, "error": "API not found" }

        return { "success": True, "data": self.apis[api_name] }

    def get_api_status(self, api_name: str) -> dict:
        """
        Retrieve the current operational status (e.g., active, degraded, offline) of the specified API.

        Args:
            api_name (str): The unique name/identifier of the API.

        Returns:
            dict:
                {"success": True, "data": str}  # status string on success
                or
                {"success": False, "error": str}  # reason for failure (e.g., API not found)

        Constraints:
            - The api_name must correspond to an existing API entity.
        """
        api_info = self.apis.get(api_name)
        if not api_info:
            return { "success": False, "error": "API not found" }
        return { "success": True, "data": api_info["status"] }

    def get_channel_info_by_id(self, channel_id: str) -> dict:
        """
        Retrieve the complete configuration and metadata for a channel by its channel_id.

        Args:
            channel_id (str): Unique identifier for the channel.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": ChannelInfo
                }
                or
                {
                    "success": False,
                    "error": "Channel not found"
                }

        Constraints:
            - The channel_id must correspond to an existing channel entity.
        """
        channel_info = self.channels.get(channel_id)
        if not channel_info:
            return {"success": False, "error": "Channel not found"}
        return {"success": True, "data": channel_info}

    def get_channel_status(self, channel_id: str) -> dict:
        """
        Get the current operational status of a specified channel by channel_id.

        Args:
            channel_id (str): The unique identifier of the payment channel.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "channel_id": str,
                    "status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., channel not found)
            }

        Constraints:
            - channel_id must exist in the channels dictionary.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return {"success": False, "error": "Channel not found"}

        return {
            "success": True,
            "data": {
                "channel_id": channel_id,
                "status": channel["status"]
            }
        }

    def get_product_info_by_id(self, product_id: str) -> dict:
        """
        Retrieve all the details (pricing, metadata, etc.) for a product by its product_id.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo
            }
            or
            {
                "success": False,
                "error": "Product does not exist"
            }

        Constraints:
            - Valid product_id must correspond to an existing product entity.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        return { "success": True, "data": self.products[product_id] }

    def check_product_exists(self, product_id: str) -> dict:
        """
        Verify if a product with the specified product_id exists.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict:
              - If product exists: { "success": True, "exists": True }
              - If not exists:     { "success": True, "exists": False }
              - If input is invalid (e.g., None or empty): treat as not exists

        Constraints:
            - Checks presence of product_id in self.products.
            - No exceptions are raised; always returns a dict.
        """
        if not product_id or not isinstance(product_id, str):
            return { "success": True, "exists": False }

        exists = product_id in self.products
        return { "success": True, "exists": exists }

    def check_channel_exists(self, channel_id: str) -> dict:
        """
        Verify if a channel with the specified channel_id exists.

        Args:
            channel_id (str): The unique identifier of the channel.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if channel exists, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Error message if invalid input
            }

        Constraints:
            - channel_id should be a non-empty string.
        """
        if not isinstance(channel_id, str) or not channel_id.strip():
            return { "success": False, "error": "Invalid channel_id: must be a non-empty string." }

        exists = channel_id in self.channels
        return { "success": True, "data": exists }

    def list_all_apis(self) -> dict:
        """
        Retrieve a list of all registered APIs and their top-level summaries.

        Returns:
            dict: {
                "success": True,
                "data": List[APIInfo],  # All API entities' information (may be empty if none exist)
            }
        """
        api_summaries = list(self.apis.values())
        return { "success": True, "data": api_summaries }

    def list_all_channels(self) -> dict:
        """
        Retrieve a summary list of all channels managed by the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ChannelInfo],  # All channels currently managed, possibly empty
            }

        Constraints:
            - Returns all channels; does not perform authorization check as no user/session info is provided.
        """
        channel_list = list(self.channels.values())
        return {
            "success": True,
            "data": channel_list
        }

    def list_all_products(self) -> dict:
        """
        List all products registered on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of product info dicts (may be empty if no products registered)
            }

        Constraints:
            - No authorization, filtering, or input parameters are required for this operation.
        """
        products_list = list(self.products.values())
        return { "success": True, "data": products_list }


    def update_api_status(self, api_name: str, new_status: str) -> dict:
        """
        Change the status and health information for a specific API.

        Args:
            api_name (str): Name of the API whose status is to be updated.
            new_status (str): The new operational status (e.g. 'online', 'offline', 'degraded').

        Returns:
            dict: {
              "success": True,
              "message": "API status updated from <old_status> to <new_status>"
            }
            or
            {
              "success": False,
              "error": "API not found"
            }

        Constraints:
            - API name must already exist.
            - Updates the status and last_checked_time; logs the change in availability_history.
        """
        api = self.apis.get(api_name)
        if not api:
            return { "success": False, "error": "API not found" }

        old_status = api["status"]
        api["status"] = new_status
        # Update last checked time to current UTC ISO timestamp
        now_iso = datetime.utcnow().isoformat() + 'Z'
        api["last_checked_time"] = now_iso
        # Optionally record every status change in the availability history with timestamp string
        api["availability_history"].append(f"{now_iso}: {new_status}")

        return {
            "success": True,
            "message": f"API status updated from {old_status} to {new_status}"
        }

    def log_api_check_time(self, api_name: str, timestamp: str, result: str) -> dict:
        """
        Record a monitoring check on an API with timestamp and availability result.

        Args:
            api_name (str): Name/identifier of the API to log check for.
            timestamp (str): ISO8601 timestamp string for the check event.
            result (str): The result of the check ("available", "unavailable", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "API check logged successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - API must exist in self.apis.
            - Will update the API's last_checked_time and append to availability_history.
        """
        api = self.apis.get(api_name)
        if not api:
            return { "success": False, "error": "API does not exist." }
    
        # Update last checked time to the provided timestamp
        api["last_checked_time"] = timestamp

        # Record event in availability_history with explicit result
        # Format: "<result>|<timestamp>" for clarity
        entry = f"{result}|{timestamp}"
        if "availability_history" not in api or not isinstance(api["availability_history"], list):
            api["availability_history"] = []
        api["availability_history"].append(entry)

        # Persist back (not strictly needed since dict is mutable)
        self.apis[api_name] = api

        return { "success": True, "message": "API check logged successfully." }

    def update_channel_status(self, channel_id: str, new_status: str) -> dict:
        """
        Update the status field of a channel.

        Args:
            channel_id (str): The unique identifier for the channel to update.
            new_status (str): The new status to be set for the channel
                (e.g., "active", "inactive", "maintenance").

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Channel status updated"
                    }
                On error (channel not found):
                    {
                        "success": False,
                        "error": "Channel does not exist"
                    }

        Constraints:
            - channel_id must exist in the system.
            - Status is updated unconditionally (caller ensures logic).
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }

        self.channels[channel_id]['status'] = new_status
        return { "success": True, "message": "Channel status updated" }

    def modify_channel_configuration(
        self, 
        channel_id: str, 
        new_configuration: Dict[str, Any], 
        user_id: str
    ) -> dict:
        """
        Change (replace) the configuration settings of a specified payment channel.

        Args:
            channel_id (str): Unique identifier of the channel to modify.
            new_configuration (Dict[str, Any]): New configuration settings for the channel.
            user_id (str): The ID of the user requesting the change, for authorization.

        Returns:
            dict: {
                "success": True,
                "message": "Channel configuration updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - channel_id must refer to an existing channel.
            - Only an authorized user/merchant can change a channel's configuration.
            - Status must update in response to configuration updates (set to "updated").
        """
        # Check whether channel exists
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist." }
    
        # Authorization check (assume this helper exists and returns {"success": True/False, ...})
        if not self._is_user_authorized_for_entity("channel", channel_id, user_id):
            return { "success": False, "error": "Permission denied." }
    
        # Validate new configuration type
        if not isinstance(new_configuration, dict):
            return { "success": False, "error": "Invalid configuration format. Must be a dictionary." }
    
        # Perform configuration update
        self.channels[channel_id]["configuration"] = new_configuration

        # Update channel status in response to configuration change (simple policy: set to "updated")
        self.channels[channel_id]["status"] = "updated"

        return { "success": True, "message": "Channel configuration updated." }

    def add_product(
        self,
        product_id: str,
        name: str,
        price: float,
        currency: str,
        availability_status: str,
        metadata: dict
    ) -> dict:
        """
        Add a new product to the platform.

        Args:
            product_id (str): Unique product identifier.
            name (str): Product name.
            price (float): Product price.
            currency (str): ISO currency code.
            availability_status (str): Whether the product is available.
            metadata (dict): Miscellaneous additional product fields.

        Returns:
            dict: {
                "success": True,
                "message": "Product <id> successfully added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The product_id must be unique (must not already exist).
            - The provided data types should be correct.
            - (Optionally) Authorization should be checked before adding a product.
        """

        # Check if product_id already exists
        if product_id in self.products:
            return { "success": False, "error": "Product ID already exists" }

        # (Basic) type validation
        if not isinstance(product_id, str) or not product_id:
            return { "success": False, "error": "Product ID must be a non-empty string" }
        if not isinstance(name, str) or not name:
            return { "success": False, "error": "Product name must be a non-empty string" }
        if not isinstance(price, (float, int)) or price < 0:
            return { "success": False, "error": "Product price must be a non-negative number" }
        if not isinstance(currency, str) or not currency:
            return { "success": False, "error": "Currency must be a non-empty string" }
        if not isinstance(availability_status, str) or not availability_status:
            return { "success": False, "error": "Availability status required" }
        if not isinstance(metadata, dict):
            return { "success": False, "error": "Metadata must be a dictionary" }

        # Add the product
        self.products[product_id] = {
            "product_id": product_id,
            "name": name,
            "price": float(price),
            "currency": currency,
            "availability_status": availability_status,
            "metadata": metadata
        }

        return {
            "success": True,
            "message": f"Product '{product_id}' successfully added."
        }

    def update_product_details(
        self,
        product_id: str,
        name: str = None,
        price: float = None,
        currency: str = None,
        availability_status: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Update details (fields) of a product by product_id.

        Args:
            product_id (str): The unique identifier of the product to update.
            name (str, optional): New product name.
            price (float, optional): New product price.
            currency (str, optional): New currency code.
            availability_status (str, optional): New availability status.
            metadata (dict, optional): New metadata dictionary to replace existing.

        Returns:
            dict: {
                "success": True,
                "message": "Product details updated successfully."
            } on success,
            or
            {
                "success": False,
                "error": "reason"
            } on failure.

        Constraints:
            - product_id must exist.
            - Only allowed fields may be updated.
            - Field types must match definition.
            - At least one field must be provided for update.
        """
        allowed_fields = ["name", "price", "currency", "availability_status", "metadata"]
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        # Gather fields to change
        updates = {}
        if name is not None:
            if not isinstance(name, str):
                return { "success": False, "error": "Field 'name' must be a string." }
            updates["name"] = name

        if price is not None:
            if not isinstance(price, (int, float)):
                return { "success": False, "error": "Field 'price' must be a number." }
            updates["price"] = float(price)

        if currency is not None:
            if not isinstance(currency, str):
                return { "success": False, "error": "Field 'currency' must be a string." }
            updates["currency"] = currency

        if availability_status is not None:
            if not isinstance(availability_status, str):
                return { "success": False, "error": "Field 'availability_status' must be a string." }
            updates["availability_status"] = availability_status

        if metadata is not None:
            if not isinstance(metadata, dict):
                return { "success": False, "error": "Field 'metadata' must be a dictionary." }
            updates["metadata"] = metadata

        if not updates:
            return { "success": False, "error": "No update fields provided." }

        # Apply updates
        for k, v in updates.items():
            self.products[product_id][k] = v

        return { "success": True, "message": "Product details updated successfully." }

    def delete_product(
        self, 
        product_id: str, 
        user_id: Optional[str] = None, 
        hard_delete: bool = False
    ) -> dict:
        """
        Remove a product from active offerings (soft-delete or hard-delete).
    
        Args:
            product_id (str): The unique product identifier to remove.
            user_id (Optional[str]): ID of the user requesting the operation (for authorization).
            hard_delete (bool): If True, the product will be permanently deleted (removed from records);
                                If False, it will only be deactivated (soft-delete).
                            
        Returns:
            dict:
                On success:
                    { "success": True, "message": "Product <id> deleted." }
                On failure:
                    { "success": False, "error": "..."}
    
        Constraints:
            - The product ID must correspond to an existing product.
            - Only authorized users/merchants can delete products.
            - Soft-delete sets availability_status to "deleted".
            - Hard-delete removes product from platform.
        """
        # Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }
    
        # Authorization check (assume presence of authorize_user_for_entity)
        if user_id is not None:
            if not self._is_user_authorized_for_entity("product", product_id, user_id):
                return { "success": False, "error": "Not authorized to delete this product." }
    
        if hard_delete:
            del self.products[product_id]
            return { "success": True, "message": f"Product {product_id} hard-deleted." }
        else:
            self.products[product_id]["availability_status"] = "deleted"
            return { "success": True, "message": f"Product {product_id} soft-deleted (status set to 'deleted')." }

    def add_channel(
        self,
        channel_id: str,
        name: str,
        api_name: str,
        status: str,
        configuration: Dict[str, Any],
        supported_currency: List[str]
    ) -> dict:
        """
        Registers a new payment channel in the system.
    
        Args:
            channel_id (str): Unique identifier for the channel.
            name (str): Channel's display name.
            api_name (str): Name of the API this channel operates over (must exist).
            status (str): Initial status of the channel.
            configuration (dict): Channel configuration details.
            supported_currency (List[str]): List of ISO currency codes supported by this channel.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Channel <channel_id> added successfully."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Channel ID must not already exist in the system.
            - The referenced api_name must already exist in the system.
            - Channel info must contain all required fields.
            - (Authorization checks could be enforced if user context is provided.)
        """
        # Check if channel_id already exists
        if channel_id in self.channels:
            return {"success": False, "error": f"Channel ID '{channel_id}' already exists."}

        # Check if the referenced API exists
        if api_name not in self.apis:
            return {"success": False, "error": f"Referenced API '{api_name}' does not exist."}

        # Minimal validation for essential fields (already required by signature)
        if not channel_id or not name or not api_name or not isinstance(supported_currency, list):
            return {"success": False, "error": "Invalid or missing required channel information."}

        # Build channel info
        channel_info: ChannelInfo = {
            "channel_id": channel_id,
            "name": name,
            "api_name": api_name,
            "status": status,
            "configuration": configuration,
            "supported_currency": supported_currency
        }

        # Add to internal records
        self.channels[channel_id] = channel_info

        return {"success": True, "message": f"Channel '{channel_id}' added successfully."}

    def delete_channel(self, channel_id: str, user_id: str) -> dict:
        """
        Remove a channel from the system.

        Args:
            channel_id (str): The unique identifier of the channel to be removed.
            user_id (str): The ID of the user/merchant requesting the deletion.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Channel <channel_id> deleted successfully"
                }
                On failure:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The channel_id must exist.
            - Only authorized users/merchants can delete the channel.
        """
        # Check if channel exists
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }

        # Authorization check
        if not self._is_user_authorized_for_entity("channel", channel_id, user_id):
            return { "success": False, "error": "Permission denied" }

        # Remove channel
        del self.channels[channel_id]
        return { "success": True, "message": f"Channel {channel_id} deleted successfully" }

    def add_api_integration(
        self,
        api_name: str,
        status: str = "inactive",
        last_checked_time: str = "",
        response_times: Optional[list] = None,
        availability_history: Optional[list] = None
    ) -> dict:
        """
        Register a new third-party payment API for the system to monitor and use.

        Args:
            api_name (str): Unique name/identifier for the API.
            status (str, optional): Initial API status, default is "inactive".
            last_checked_time (str, optional): ISO8601 string for last checked time, default empty.
            response_times (List[float], optional): List of response time measurements. Defaults to empty.
            availability_history (List[str], optional): List of availability timestamps. Defaults to empty.

        Returns:
            dict: {
                "success": True,
                "message": "API integration added successfully"
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - api_name must be unique.
            - api_name must not be empty.
        """
        if not api_name or not isinstance(api_name, str):
            return {"success": False, "error": "API name must be a non-empty string"}
        if api_name in self.apis:
            return {"success": False, "error": f"API '{api_name}' already exists"}
        if status not in {"inactive", "active", "error", "unknown", "online", "offline", "degraded"}:
            return {"success": False, "error": f"Invalid status '{status}'"}

        self.apis[api_name] = {
            "api_name": api_name,
            "status": status,
            "last_checked_time": last_checked_time,
            "response_times": response_times if response_times is not None else [],
            "availability_history": availability_history if availability_history is not None else []
        }
        return {"success": True, "message": "API integration added successfully"}

    def delete_api_integration(self, api_name: str, user_id: str) -> dict:
        """
        Remove an API integration from the management system.

        Args:
            api_name (str): Name (unique identifier) of the API integration to be deleted.
            user_id (str): ID of the user/merchant requesting deletion.
    
        Returns:
            dict: 
              - On success: { "success": True, "message": "API integration '<api_name>' deleted successfully." }
              - On failure: { "success": False, "error": "reason" }

        Constraints:
            - api_name must exist in the system.
            - Only authorized users/merchants may delete the API.
            - An API integration cannot be deleted if there are Channels referencing it.
        """
        # Check existence
        if api_name not in self.apis:
            return {"success": False, "error": f"API integration '{api_name}' does not exist."}

        # Authorization check (assuming a method exists)
        if hasattr(self, "authorize_user_for_entity"):
            if not self._is_user_authorized_for_entity("api", api_name, user_id):
                return {"success": False, "error": "Not authorized to delete this API integration."}
        # Else, if no mechanism, skip authorization (can be tuned during integration)

        # Check for associated Channels
        associated_channels = [
            c for c in self.channels.values() if c['api_name'] == api_name
        ]
        if associated_channels:
            return {
                "success": False,
                "error": f"Cannot delete API '{api_name}': channels are still using this API."
            }

        # All constraints passed, proceed to delete
        del self.apis[api_name]
        return {
            "success": True,
            "message": f"API integration '{api_name}' deleted successfully."
        }

    def update_api_availability_history(self, api_name: str, event_timestamp: str, availability_state: Optional[str] = None) -> dict:
        """
        Add an event to an API’s availability history for status tracking.

        Args:
            api_name (str): The name of the API integration to update.
            event_timestamp (str): The ISO8601 timestamp marking the availability event.
            availability_state (Optional[str]): Optional; e.g., "available" or "unavailable".

        Returns:
            dict: {
                "success": True,
                "message": "API availability history updated"
            }
            on failure:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The api_name must correspond to an existing API integration.
            - The event will be appended to the API's availability_history.
        """
        if not api_name or api_name not in self.apis:
            return { "success": False, "error": "API does not exist" }

        if not event_timestamp:
            return { "success": False, "error": "Event timestamp required" }

        entry = event_timestamp
        if availability_state:
            entry = f"{event_timestamp} {availability_state}"

        # Defensive: ensure availability_history is a list
        if "availability_history" not in self.apis[api_name] or not isinstance(self.apis[api_name]["availability_history"], list):
            self.apis[api_name]["availability_history"] = []

        self.apis[api_name]["availability_history"].append(entry)

        return { "success": True, "message": "API availability history updated" }

    def authorize_user_for_entity(self, entity_type: str, entity_id: str, user_id: str) -> dict:
        """
        Grant access permission to a product, channel, or API entity for a particular authorized user or merchant.

        Args:
            entity_type (str): One of "product", "channel", or "api".
            entity_id (str): For 'product' = product_id, for 'channel' = channel_id, for 'api' = api_name.
            user_id (str): The user or merchant identifier to authorize.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> is now authorized for <entity_type> <entity_id>"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The entity_type must be "product", "channel", or "api".
            - The entity_id must exist for the given entity_type.
            - Authorizations are tracked and idempotent (no duplicate grants).

        State change: Adds user_id to the set of authorized users for the specified entity.
        """

        valid_types = ("product", "channel", "api")
        if entity_type not in valid_types:
            return {"success": False, "error": "Invalid entity type"}

        # Check entity exists
        if entity_type == "product":
            if entity_id not in self.products:
                return {"success": False, "error": "Product does not exist"}
        elif entity_type == "channel":
            if entity_id not in self.channels:
                return {"success": False, "error": "Channel does not exist"}
        elif entity_type == "api":
            if entity_id not in self.apis:
                return {"success": False, "error": "API does not exist"}

        if not self._is_known_user_id(user_id):
            return {"success": False, "error": "Unknown user or merchant identifier"}

        # Initialize authorization mapping if not present
        if not hasattr(self, "authorizations"):
            # Structure: { entity_type: { entity_id: set([user_id, ...]) } }
            self.authorizations = {
                "product": {},
                "channel": {},
                "api": {}
            }

        if entity_id not in self.authorizations[entity_type]:
            self.authorizations[entity_type][entity_id] = set()

        already_authorized = user_id in self.authorizations[entity_type][entity_id]
        self.authorizations[entity_type][entity_id].add(user_id)
        if already_authorized:
            return {
                "success": True,
                "message": f"User {user_id} is already authorized for {entity_type} {entity_id}"
            }
        else:
            return {
                "success": True,
                "message": f"User {user_id} is now authorized for {entity_type} {entity_id}"
            }


class PaymentGatewayAPIManagementSystem(BaseEnv):
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
        normalized_authorizations = {
            "product": {},
            "channel": {},
            "api": {},
        }
        for key, value in init_config.items():
            if key == "authorize_user_for_entity":
                setattr(env, "_authorize_user_for_entity_state", copy.deepcopy(value))
                structured_policy = _GeneratedEnvImpl._normalize_authorizations(
                    value,
                    getattr(env, "apis", {}),
                    getattr(env, "channels", {}),
                    getattr(env, "products", {}),
                )
                for entity_type, entity_map in structured_policy.items():
                    for entity_id, users in entity_map.items():
                        normalized_authorizations[entity_type].setdefault(entity_id, set()).update(users)
                continue
            if key == "authorizations":
                normalized = _GeneratedEnvImpl._normalize_authorizations(
                    value,
                    getattr(env, "apis", {}),
                    getattr(env, "channels", {}),
                    getattr(env, "products", {}),
                )
                for entity_type, entity_map in normalized.items():
                    for entity_id, users in entity_map.items():
                        normalized_authorizations[entity_type].setdefault(entity_id, set()).update(users)
                continue
            if key == "valid_user_ids":
                parsed_value = value
                if isinstance(value, str):
                    stripped = value.strip()
                    if not stripped:
                        setattr(env, "valid_user_ids", set())
                        continue
                    try:
                        parsed_value = json.loads(stripped)
                    except Exception:
                        parsed_value = [value]
                if isinstance(parsed_value, str):
                    parsed_value = [parsed_value]
                if isinstance(parsed_value, (list, tuple, set)):
                    setattr(
                        env,
                        "valid_user_ids",
                        {item for item in parsed_value if isinstance(item, str) and item},
                    )
                continue
            setattr(env, key, copy.deepcopy(value))
        if any(normalized_authorizations.values()):
            setattr(env, "authorizations", normalized_authorizations)

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

    def get_api_info(self, **kwargs):
        return self._call_inner_tool('get_api_info', kwargs)

    def get_api_status(self, **kwargs):
        return self._call_inner_tool('get_api_status', kwargs)

    def get_channel_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_channel_info_by_id', kwargs)

    def get_channel_status(self, **kwargs):
        return self._call_inner_tool('get_channel_status', kwargs)

    def get_product_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_info_by_id', kwargs)

    def check_product_exists(self, **kwargs):
        return self._call_inner_tool('check_product_exists', kwargs)

    def check_channel_exists(self, **kwargs):
        return self._call_inner_tool('check_channel_exists', kwargs)

    def list_all_apis(self, **kwargs):
        return self._call_inner_tool('list_all_apis', kwargs)

    def list_all_channels(self, **kwargs):
        return self._call_inner_tool('list_all_channels', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def update_api_status(self, **kwargs):
        return self._call_inner_tool('update_api_status', kwargs)

    def log_api_check_time(self, **kwargs):
        return self._call_inner_tool('log_api_check_time', kwargs)

    def update_channel_status(self, **kwargs):
        return self._call_inner_tool('update_channel_status', kwargs)

    def modify_channel_configuration(self, **kwargs):
        return self._call_inner_tool('modify_channel_configuration', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_details(self, **kwargs):
        return self._call_inner_tool('update_product_details', kwargs)

    def delete_product(self, **kwargs):
        return self._call_inner_tool('delete_product', kwargs)

    def add_channel(self, **kwargs):
        return self._call_inner_tool('add_channel', kwargs)

    def delete_channel(self, **kwargs):
        return self._call_inner_tool('delete_channel', kwargs)

    def add_api_integration(self, **kwargs):
        return self._call_inner_tool('add_api_integration', kwargs)

    def delete_api_integration(self, **kwargs):
        return self._call_inner_tool('delete_api_integration', kwargs)

    def update_api_availability_history(self, **kwargs):
        return self._call_inner_tool('update_api_availability_history', kwargs)

    def authorize_user_for_entity(self, **kwargs):
        return self._call_inner_tool('authorize_user_for_entity', kwargs)
