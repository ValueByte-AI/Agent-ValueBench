# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
from typing import Optional, Dict, Any



class WarehouseInfo(TypedDict):
    warehouse_id: str
    location: str  # e.g., city/state
    name: str

class ZoneInfo(TypedDict):
    zone_id: str
    warehouse_id: str  # must refer to a valid warehouse
    name: str

class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    description: str

class InventoryRecordInfo(TypedDict):
    product_id: str
    warehouse_id: str
    zone_id: str
    quantity: int
    timestamp: float  # Unix timestamp (seconds since epoch)

class _GeneratedEnvImpl:
    def __init__(self):
        # Warehouses: {warehouse_id: WarehouseInfo}
        self.warehouses: Dict[str, WarehouseInfo] = {}

        # Zones: {zone_id: ZoneInfo}
        self.zones: Dict[str, ZoneInfo] = {}

        # Products: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # Inventory Records: list of inventory transactions and states
        # Each record is unique by (product_id, warehouse_id, zone_id, timestamp)
        self.inventory_records: List[InventoryRecordInfo] = []

        # Constraints:
        # - Each zone must belong to a warehouse (zone.warehouse_id must refer to a valid warehouse).
        # - Product quantities must be non-negative.
        # - Inventory changes are tracked with accurate timestamps for audit and reporting.
        # - Each InventoryRecord is unique by (product_id, warehouse_id, zone_id, timestamp).

    def get_warehouse_by_location(self, location: str) -> dict:
        """
        Retrieve all warehouse info(s) matching the specified city/state location.

        Args:
            location (str): The city/state string to use for warehouse lookup.

        Returns:
            dict: {
                "success": True,
                "data": List[WarehouseInfo],  # List of WarehouseInfo matching location
            }
            or
            {
                "success": False,
                "error": str  # "No warehouse found in given location"
            }
        Constraints:
            - Returns all warehouses whose location field matches the input string exactly.
            - If none found, returns error.
        """
        matches = [
            warehouse_info
            for warehouse_info in self.warehouses.values()
            if warehouse_info["location"] == location
        ]

        if not matches:
            return {
                "success": False,
                "error": "No warehouse found in given location"
            }
        return {
            "success": True,
            "data": matches
        }

    def get_warehouse_by_id(self, warehouse_id: str) -> dict:
        """
        Retrieve warehouse info using the warehouse ID.

        Args:
            warehouse_id (str): The unique warehouse identifier.

        Returns:
            dict:
                - {"success": True, "data": WarehouseInfo} if warehouse found
                - {"success": False, "error": "Warehouse not found"} otherwise

        Constraints:
            - warehouse_id must exist in the system.
        """
        warehouse_info = self.warehouses.get(warehouse_id)
        if warehouse_info is None:
            return { "success": False, "error": "Warehouse not found" }
        return { "success": True, "data": warehouse_info }

    def list_all_warehouses(self) -> dict:
        """
        Retrieve a list of all warehouses in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[WarehouseInfo], # May be empty
            }
        """
        warehouses_list = list(self.warehouses.values())
        return {"success": True, "data": warehouses_list}

    def list_zones_in_warehouse(self, warehouse_id: str) -> dict:
        """
        Retrieve all zones belonging to the specified warehouse.

        Args:
            warehouse_id (str): Unique identifier for the target warehouse.

        Returns:
            dict: {
                "success": True,
                "data": List[ZoneInfo]  # List of zones in the warehouse; empty list if none.
            }
            OR
            {
                "success": False,
                "error": str  # If warehouse does not exist.
            }

        Constraints:
            - warehouse_id must refer to an existing warehouse.
            - Returns all zones linked to this warehouse.
        """
        if warehouse_id not in self.warehouses:
            return {"success": False, "error": "Warehouse does not exist"}

        zones_in_warehouse = [
            zone_info for zone_info in self.zones.values()
            if zone_info["warehouse_id"] == warehouse_id
        ]

        return {"success": True, "data": zones_in_warehouse}

    def get_zone_by_name(self, name: str, warehouse_id: str = None) -> dict:
        """
        Retrieve zone info(s) by name, optionally within a given warehouse.

        Args:
            name (str): The name of the zone to search for.
            warehouse_id (str, optional): If provided, restrict search to this warehouse context.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ZoneInfo]  # may be empty if no matches
                    }
                On error (invalid warehouse):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - If warehouse_id is supplied, it must exist in the system.
        """
        if warehouse_id is not None and warehouse_id not in self.warehouses:
            return { "success": False, "error": "Warehouse not found" }

        results = [
            zone for zone in self.zones.values()
            if zone["name"] == name and (warehouse_id is None or zone["warehouse_id"] == warehouse_id)
        ]

        return { "success": True, "data": results }

    def list_all_zones(self) -> dict:
        """
        List all zones across all warehouses.

        Returns:
            dict: {
                "success": True,
                "data": List[ZoneInfo]  # List of all zones (may be empty)
            }
        Constraints:
            - Simply returns all ZoneInfo objects present in the system.
        """
        return {
            "success": True,
            "data": list(self.zones.values())
        }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve product details by product ID.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo
            }
            or
            {
                "success": False,
                "error": "Product not found"
            }

        Constraints:
            - Returns failure if the product_id does not exist in the system.
        """
        product = self.products.get(product_id)
        if product is None:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def list_products_by_criteria(self, name: str = None, category: str = None, description: str = None) -> dict:
        """
        List products whose name, category, or description matches the provided criteria.
        All criteria parameters are optional. Matching is case-insensitive and will do substring search.
        If no criteria are provided, all products will be returned.

        Args:
            name (str, optional): Substring to match against product 'name'.
            category (str, optional): Substring to match against product 'category'.
            description (str, optional): Substring to match against product 'description'.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # All products matching any criteria, or all products if no criteria
            }
        """
        result = []
        for product in self.products.values():
            matches = True
            if name is not None:
                if name.lower() not in product["name"].lower():
                    matches = False
            if category is not None:
                if category.lower() not in product["category"].lower():
                    matches = False
            if description is not None:
                if description.lower() not in product["description"].lower():
                    matches = False
            if matches:
                result.append(product)
        return {"success": True, "data": result}

    def get_inventory_records(
        self, 
        product_ids: list, 
        warehouse_ids: list, 
        zone_ids: list, 
        start_timestamp: float = None, 
        end_timestamp: float = None
    ) -> dict:
        """
        Retrieve all inventory records filtered by product_ids, warehouse_ids, zone_ids, 
        and optional date range.

        Args:
            product_ids (list[str]): List of product IDs to filter (must exist).
            warehouse_ids (list[str]): List of warehouse IDs to filter (must exist).
            zone_ids (list[str]): List of zone IDs to filter (must exist).
            start_timestamp (float, optional): Only records with timestamp >= this value.
            end_timestamp (float, optional): Only records with timestamp <= this value.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryRecordInfo]  # May be empty
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - All IDs supplied must correspond to existing products, warehouses, or zones.
            - If timestamps are provided, start_timestamp <= end_timestamp.
        """
        # Validate input types
        if not isinstance(product_ids, list) or not isinstance(warehouse_ids, list) or not isinstance(zone_ids, list):
            return {"success": False, "error": "All IDs must be provided as lists."}

        # Validate that all IDs exist
        invalid_products = [pid for pid in product_ids if pid not in self.products]
        if invalid_products:
            return {"success": False, "error": f"Invalid product_ids: {invalid_products}"}

        invalid_warehouses = [wid for wid in warehouse_ids if wid not in self.warehouses]
        if invalid_warehouses:
            return {"success": False, "error": f"Invalid warehouse_ids: {invalid_warehouses}"}

        invalid_zones = [zid for zid in zone_ids if zid not in self.zones]
        if invalid_zones:
            return {"success": False, "error": f"Invalid zone_ids: {invalid_zones}"}

        # Validate timestamps
        if start_timestamp is not None and end_timestamp is not None:
            if start_timestamp > end_timestamp:
                return {"success": False, "error": "start_timestamp cannot be greater than end_timestamp."}

        # Filter records
        records = []
        for rec in self.inventory_records:
            if (
                rec["product_id"] in product_ids and
                rec["warehouse_id"] in warehouse_ids and
                rec["zone_id"] in zone_ids and
                (start_timestamp is None or rec["timestamp"] >= start_timestamp) and
                (end_timestamp is None or rec["timestamp"] <= end_timestamp)
            ):
                records.append(rec)

        return {"success": True, "data": records}

    def get_current_inventory_status(
        self,
        product_ids: list,
        warehouse_ids: list = None,
        zone_ids: list = None
    ) -> dict:
        """
        Get the latest inventory quantity (by most recent timestamp)
        for given product IDs in specified warehouse(s) and zone(s).

        Args:
            product_ids (List[str]): Product IDs to query (required).
            warehouse_ids (List[str], optional): Filter for only these warehouses. If None, include all.
            zone_ids (List[str], optional): Filter for only these zones. If None, include all.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryRecordInfo]  # latest records per (product_id, warehouse_id, zone_id)
            }
            or
            {
                "success": False,
                "error": str  # error message
            }
        Constraints:
            - Product quantities must be non-negative.
            - Only most recent (latest timestamp) record per combo.
        """

        # Validate input
        if not isinstance(product_ids, list) or not product_ids or not all(isinstance(pid, str) for pid in product_ids):
            return {"success": False, "error": "product_ids must be a non-empty list of strings"}
        if warehouse_ids is not None:
            if not isinstance(warehouse_ids, list) or not all(isinstance(wid, str) for wid in warehouse_ids):
                return {"success": False, "error": "warehouse_ids must be a list of strings or None"}
        if zone_ids is not None:
            if not isinstance(zone_ids, list) or not all(isinstance(zid, str) for zid in zone_ids):
                return {"success": False, "error": "zone_ids must be a list of strings or None"}

        # Build filter set for fast lookup
        product_id_set = set(product_ids)
        warehouse_id_set = set(warehouse_ids) if warehouse_ids is not None else None
        zone_id_set = set(zone_ids) if zone_ids is not None else None

        # {(product_id, warehouse_id, zone_id): InventoryRecordInfo (latest timestamp)}
        latest_records = {}

        for record in self.inventory_records:
            pid = record["product_id"]
            wid = record["warehouse_id"]
            zid = record["zone_id"]

            if pid not in product_id_set:
                continue
            if warehouse_id_set is not None and wid not in warehouse_id_set:
                continue
            if zone_id_set is not None and zid not in zone_id_set:
                continue

            key = (pid, wid, zid)
            if key not in latest_records or record["timestamp"] > latest_records[key]["timestamp"]:
                latest_records[key] = record

        return {
            "success": True,
            "data": list(latest_records.values())
        }

    def get_inventory_history(
        self,
        product_ids: List[str] = None,
        warehouse_ids: List[str] = None,
        zone_ids: List[str] = None,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Retrieve historical inventory changes filtered by products, warehouses/zones, and date range.

        Args:
            product_ids (List[str], optional): Only include these product_ids.
            warehouse_ids (List[str], optional): Only include these warehouse_ids.
            zone_ids (List[str], optional): Only include these zone_ids.
            start_time (float, optional): Only include records with timestamp >= start_time.
            end_time (float, optional): Only include records with timestamp <= end_time.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryRecordInfo]  # filtered records
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Filters are all optional and combinable.
            - If no records match, data is an empty list.
        """
        # Input validation
        if start_time is not None and not isinstance(start_time, (float, int)):
            return { "success": False, "error": "start_time must be a float (Unix timestamp)" }
        if end_time is not None and not isinstance(end_time, (float, int)):
            return { "success": False, "error": "end_time must be a float (Unix timestamp)" }

        filtered = []
        for record in self.inventory_records:
            if product_ids is not None and record["product_id"] not in product_ids:
                continue
            if warehouse_ids is not None and record["warehouse_id"] not in warehouse_ids:
                continue
            if zone_ids is not None and record["zone_id"] not in zone_ids:
                continue
            if start_time is not None and record["timestamp"] < start_time:
                continue
            if end_time is not None and record["timestamp"] > end_time:
                continue
            filtered.append(record)

        return { "success": True, "data": filtered }

    def get_inventory_record_by_key(
        self,
        product_id: str,
        warehouse_id: str,
        zone_id: str,
        timestamp: float
    ) -> dict:
        """
        Retrieve a specific inventory record by composite key (product_id, warehouse_id, zone_id, timestamp).

        Args:
            product_id (str): Product identifier.
            warehouse_id (str): Warehouse identifier.
            zone_id (str): Zone identifier.
            timestamp (float): Unix timestamp of the record.

        Returns:
            dict: 
                {"success": True, "data": InventoryRecordInfo} if found.
                {"success": False, "error": "Inventory record not found."} otherwise.

        Constraints:
            - InventoryRecord is unique on (product_id, warehouse_id, zone_id, timestamp).
            - Inventory quantity must be non-negative.
        """
        for rec in self.inventory_records:
            if (
                rec["product_id"] == product_id and
                rec["warehouse_id"] == warehouse_id and
                rec["zone_id"] == zone_id and
                rec["timestamp"] == timestamp
            ):
                return {"success": True, "data": rec}

        return {"success": False, "error": "Inventory record not found."}

    def get_zone_warehouse_relationship(self, zone_id: str) -> dict:
        """
        Validate and retrieve the warehouse that a given zone belongs to.

        Args:
            zone_id (str): The ID of the zone.

        Returns:
            dict: {
              "success": True,
              "data": WarehouseInfo  # Info of the warehouse the zone belongs to
            }
            or
            {
              "success": False,
              "error": str  # Reason (zone not found, warehouse not found)
            }

        Constraints:
            - The specified zone must exist.
            - The zone must reference a warehouse that exists in the system.
        """
        if zone_id not in self.zones:
            return { "success": False, "error": "Zone does not exist" }
        warehouse_id = self.zones[zone_id]["warehouse_id"]
        if warehouse_id not in self.warehouses:
            return { "success": False, "error": "Zone refers to a non-existent warehouse" }
        return { "success": True, "data": self.warehouses[warehouse_id] }

    def check_zone_belongs_to_warehouse(self, zone_id: str, warehouse_id: str) -> dict:
        """
        Verify if a specified zone is within a specific warehouse.

        Args:
            zone_id (str): The unique ID of the zone to check.
            warehouse_id (str): The unique ID of the warehouse.

        Returns:
            dict:
                - If the zone exists:
                    {"success": True, "data": True}   # If zone belongs to warehouse
                    {"success": True, "data": False}  # If zone does not belong to warehouse
                - If the zone does not exist:
                    {"success": False, "error": "Zone does not exist"}

        Constraints:
            - The zone must exist in the system to check membership.
            - Each zone can only belong to one warehouse.
        """
        zone_info = self.zones.get(zone_id)
        if not zone_info:
            return {"success": False, "error": "Zone does not exist"}

        belongs = zone_info["warehouse_id"] == warehouse_id
        return {"success": True, "data": belongs}

    def add_inventory_record(
        self,
        product_id: str,
        warehouse_id: str,
        zone_id: str,
        quantity: int,
        timestamp: float
    ) -> dict:
        """
        Add a new inventory record (transaction), ensuring:
          - Uniqueness by (product_id, warehouse_id, zone_id, timestamp)
          - Product, warehouse, and zone exist
          - Zone belongs to warehouse
          - Quantity is non-negative

        Args:
            product_id (str): The product identifier.
            warehouse_id (str): The warehouse identifier.
            zone_id (str): The zone identifier.
            quantity (int): The quantity of the product (must be non-negative).
            timestamp (float): The timestamp for the record (Unix seconds).

        Returns:
            dict: {
                "success": True,
                "message": "Inventory record added for (product_id, warehouse_id, zone_id, timestamp)"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        """
        # Existence checks
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }
        if warehouse_id not in self.warehouses:
            return { "success": False, "error": "Warehouse does not exist" }
        if zone_id not in self.zones:
            return { "success": False, "error": "Zone does not exist" }

        # Zone/warehouse relationship
        if self.zones[zone_id]["warehouse_id"] != warehouse_id:
            return { "success": False, "error": "Zone does not belong to specified warehouse" }

        # Quantity non-negative
        if quantity < 0:
            return { "success": False, "error": "Quantity must be non-negative" }

        # Uniqueness
        for rec in self.inventory_records:
            if (
                rec["product_id"] == product_id and
                rec["warehouse_id"] == warehouse_id and
                rec["zone_id"] == zone_id and
                rec["timestamp"] == timestamp
            ):
                return { "success": False, "error": "Inventory record already exists for these keys" }

        # Insert the new record
        new_record = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "zone_id": zone_id,
            "quantity": quantity,
            "timestamp": timestamp
        }
        self.inventory_records.append(new_record)

        msg = (
            f"Inventory record added for "
            f"({product_id}, {warehouse_id}, {zone_id}, {timestamp})"
        )
        return { "success": True, "message": msg }


    def update_inventory_quantity(
        self,
        product_id: str,
        warehouse_id: str,
        zone_id: str,
        quantity: int
    ) -> dict:
        """
        Update the inventory quantity for a specific product in a zone of a warehouse.
        Appends a new InventoryRecordInfo with the given quantity and current timestamp.

        Args:
            product_id (str): ID of the product.
            warehouse_id (str): ID of the warehouse.
            zone_id (str): ID of the zone (must belong to warehouse_id).
            quantity (int): The updated (non-negative) inventory quantity to record.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Inventory quantity updated for product <product_id> in warehouse <warehouse_id>, zone <zone_id>."
                }
                Failure: {
                    "success": False,
                    "error": <description of the error>
                }

        Constraints:
            - product_id, warehouse_id, zone_id must exist
            - zone must belong to warehouse
            - quantity must be non-negative
            - new record gets accurate current timestamp
        """

        # Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }

        # Check warehouse existence
        if warehouse_id not in self.warehouses:
            return { "success": False, "error": "Warehouse does not exist." }

        # Check zone existence
        if zone_id not in self.zones:
            return { "success": False, "error": "Zone does not exist." }

        # Check zone is in warehouse
        zone_info = self.zones[zone_id]
        if zone_info["warehouse_id"] != warehouse_id:
            return { "success": False, "error": "Zone does not belong to specified warehouse." }

        # Check non-negative quantity
        if not isinstance(quantity, int) or quantity < 0:
            return { "success": False, "error": "Quantity must be a non-negative integer." }

        # Current timestamp
        current_time = time.time()

        # Create new inventory record
        new_record = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "zone_id": zone_id,
            "quantity": quantity,
            "timestamp": current_time
        }

        # Ensure record uniqueness per constraints (should be safe, but add check)
        keys = {(record["product_id"], record["warehouse_id"], record["zone_id"], record["timestamp"])
                for record in self.inventory_records}
        record_key = (product_id, warehouse_id, zone_id, current_time)
        if record_key in keys:
            return { "success": False, "error": "Unable to create a unique inventory record (timestamp conflict)." }

        self.inventory_records.append(new_record)
        return {
            "success": True,
            "message": (
                f"Inventory quantity updated for product {product_id} in warehouse {warehouse_id}, zone {zone_id}."
            )
        }


    def transfer_inventory_between_zones(
        self, 
        product_id: str,
        from_warehouse_id: str, from_zone_id: str,
        to_warehouse_id: str, to_zone_id: str,
        quantity: int
    ) -> dict:
        """
        Move a quantity of product from one zone to another (possibly across warehouses), updating inventory records.
        Args:
            product_id (str): The product to move.
            from_warehouse_id (str): Warehouse ID of the source zone.
            from_zone_id (str): Source zone ID.
            to_warehouse_id (str): Warehouse ID of the destination zone.
            to_zone_id (str): Destination zone ID.
            quantity (int): Number of product units to move (must be > 0).
        Returns:
            dict: 
                On success:
                  { "success": True, "message": "Transferred X units of product_id from ... to ..." }
                On failure:
                  { "success": False, "error": <reason> }
        Constraints:
            - Zones and warehouses must exist.
            - Product must exist.
            - Source zone must have sufficient quantity (quantity must not go negative).
            - Product quantities must never be negative.
            - All changes must be timestamped with current time.
        """

        # 1. Validate positive quantity
        if quantity <= 0:
            return { "success": False, "error": "Transfer quantity must be greater than zero." }
    
        # 2. Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }
    
        # 3. Check zones and warehouse existence/integrity
        # Source zone
        if from_zone_id not in self.zones:
            return { "success": False, "error": "Source zone does not exist." }
        if self.zones[from_zone_id]["warehouse_id"] != from_warehouse_id:
            return { "success": False, "error": "Source zone does not belong to specified source warehouse." }
        if from_warehouse_id not in self.warehouses:
            return { "success": False, "error": "Source warehouse does not exist." }
        # Destination zone
        if to_zone_id not in self.zones:
            return { "success": False, "error": "Destination zone does not exist." }
        if self.zones[to_zone_id]["warehouse_id"] != to_warehouse_id:
            return { "success": False, "error": "Destination zone does not belong to specified destination warehouse." }
        if to_warehouse_id not in self.warehouses:
            return { "success": False, "error": "Destination warehouse does not exist." }
    
        # 4. Get current (latest) inventory quantity at source
        from_records = [
            rec for rec in self.inventory_records
            if rec["product_id"] == product_id and
               rec["warehouse_id"] == from_warehouse_id and
               rec["zone_id"] == from_zone_id
        ]
        current_from_quantity = 0
        if from_records:
            latest_from_record = max(from_records, key=lambda r: r["timestamp"])
            current_from_quantity = latest_from_record["quantity"]

        if current_from_quantity < quantity:
            return { "success": False, "error": "Insufficient quantity in source zone for transfer." }

        # 5. Get current (latest) inventory quantity at destination
        to_records = [
            rec for rec in self.inventory_records
            if rec["product_id"] == product_id and
               rec["warehouse_id"] == to_warehouse_id and
               rec["zone_id"] == to_zone_id
        ]
        current_to_quantity = 0
        if to_records:
            latest_to_record = max(to_records, key=lambda r: r["timestamp"])
            current_to_quantity = latest_to_record["quantity"]

        # 6. Update (append) new inventory records for both zones with timestamp
        now = time.time()
        # New source record
        src_new_qty = current_from_quantity - quantity
        self.inventory_records.append({
            "product_id": product_id,
            "warehouse_id": from_warehouse_id,
            "zone_id": from_zone_id,
            "quantity": src_new_qty,
            "timestamp": now
        })
        # New destination record
        dest_new_qty = current_to_quantity + quantity
        self.inventory_records.append({
            "product_id": product_id,
            "warehouse_id": to_warehouse_id,
            "zone_id": to_zone_id,
            "quantity": dest_new_qty,
            "timestamp": now
        })

        return {
            "success": True,
            "message": (
                f"Transferred {quantity} units of product '{product_id}' "
                f"from warehouse '{from_warehouse_id}' zone '{from_zone_id}' "
                f"to warehouse '{to_warehouse_id}' zone '{to_zone_id}'."
            )
        }


    def reconcile_inventory(self, product_id: str, warehouse_id: str, zone_id: str, new_quantity: int, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Adjust inventory to match a physical count and record the adjustment for audit.

        Args:
            product_id (str): The product's unique identifier.
            warehouse_id (str): The warehouse's unique identifier.
            zone_id (str): The zone's unique identifier within the warehouse.
            new_quantity (int): The new physically counted product quantity (must be >= 0).
            timestamp (float, optional): The time of reconciliation as Unix epoch seconds. If None, uses current time.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Inventory for product <product_id> in warehouse <warehouse_id>, zone <zone_id> reconciled to <new_quantity> at <timestamp>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error message>
                    }

        Constraints:
            - Product, warehouse, and zone must all exist.
            - Zone must belong to the warehouse.
            - Quantity must be non-negative.
            - An inventory record is always added (never overwritten).
        """
        # Validate product
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}
        # Validate warehouse
        if warehouse_id not in self.warehouses:
            return {"success": False, "error": "Warehouse does not exist"}
        # Validate zone
        if zone_id not in self.zones:
            return {"success": False, "error": "Zone does not exist"}
        # Zone-warehouse relationship
        zone_info = self.zones[zone_id]
        if zone_info["warehouse_id"] != warehouse_id:
            return {"success": False, "error": "Zone does not belong to the specified warehouse"}
        # Validate new_quantity
        if not isinstance(new_quantity, int) or new_quantity < 0:
            return {"success": False, "error": "New quantity must be a non-negative integer"}
        # Determine timestamp
        actual_timestamp = float(timestamp) if timestamp is not None else time.time()
        # Create inventory record (audit trail)
        inventory_record = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "zone_id": zone_id,
            "quantity": new_quantity,
            "timestamp": actual_timestamp
        }
        self.inventory_records.append(inventory_record)
        msg = (
            f"Inventory for product {product_id} in warehouse {warehouse_id}, zone {zone_id} "
            f"reconciled to {new_quantity} at {actual_timestamp}."
        )
        return {"success": True, "message": msg}

    def delete_inventory_record(
        self,
        product_id: str,
        warehouse_id: str,
        zone_id: str,
        timestamp: float,
        approved: bool = False
    ) -> dict:
        """
        Remove an erroneous inventory record.
    
        Args:
            product_id (str): Product identifier.
            warehouse_id (str): Warehouse identifier.
            zone_id (str): Zone identifier.
            timestamp (float): The timestamp (unique record key).
            approved (bool): Admin/audit approval flag (must be True).
    
        Returns:
            dict: {
                "success": True,
                "message": "Inventory record deleted"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - The record must exist (match all keys).
            - Deletion requires explicit admin/audit approval (approved=True).
        """
        if not approved:
            return { "success": False, "error": "Admin/audit approval required" }
    
        found_idx = -1
        for idx, rec in enumerate(self.inventory_records):
            if (
                rec["product_id"] == product_id and
                rec["warehouse_id"] == warehouse_id and
                rec["zone_id"] == zone_id and
                rec["timestamp"] == timestamp
            ):
                found_idx = idx
                break

        if found_idx == -1:
            return { "success": False, "error": "Inventory record not found" }
    
        del self.inventory_records[found_idx]
        return { "success": True, "message": "Inventory record deleted" }

    def add_zone_to_warehouse(self, zone_id: str, warehouse_id: str, name: str) -> dict:
        """
        Create a new zone assigned to a specified warehouse.

        Args:
            zone_id (str): Unique identifier for the zone.
            warehouse_id (str): Identifier of the warehouse to assign the zone to.
            name (str): Name of the zone.

        Returns:
            dict:
                On Success:
                    {
                        "success": True,
                        "message": "Zone <zone_id> added to warehouse <warehouse_id>."
                    }
                On Failure:
                    {
                        "success": False,
                        "error": "<description>"
                    }

        Constraints:
            - warehouse_id must exist in the system.
            - zone_id must be unique.
        """
        if warehouse_id not in self.warehouses:
            return {"success": False, "error": "warehouse_id does not exist"}

        if zone_id in self.zones:
            return {"success": False, "error": "zone_id already exists"}

        self.zones[zone_id] = {
            "zone_id": zone_id,
            "warehouse_id": warehouse_id,
            "name": name
        }

        return {
            "success": True,
            "message": f"Zone {zone_id} added to warehouse {warehouse_id}."
        }

    def add_warehouse(self, warehouse_id: str, location: str, name: str) -> dict:
        """
        Add a new warehouse to the system.

        Args:
            warehouse_id (str): Unique identifier for the warehouse.
            location (str): Text description of the warehouse location (e.g., city/state).
            name (str): Human-readable name for the warehouse.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Warehouse added successfully"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - warehouse_id must be unique.
            - All input fields must be non-empty strings.
        """
        # Check for valid, non-empty fields
        if not warehouse_id or not isinstance(warehouse_id, str):
            return {"success": False, "error": "warehouse_id must be a non-empty string"}
        if not location or not isinstance(location, str):
            return {"success": False, "error": "location must be a non-empty string"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "name must be a non-empty string"}

        # Check uniqueness
        if warehouse_id in self.warehouses:
            return {"success": False, "error": "warehouse_id already exists"}

        # Add warehouse
        self.warehouses[warehouse_id] = {
            "warehouse_id": warehouse_id,
            "location": location,
            "name": name,
        }

        return {"success": True, "message": "Warehouse added successfully"}

    def add_product(
        self,
        product_id: str,
        name: str,
        category: str,
        description: str
    ) -> dict:
        """
        Register a new product in the system.

        Args:
            product_id (str): Unique identifier of the product.
            name (str): Name of the product.
            category (str): Category of the product.
            description (str): Product description.

        Returns:
            dict: {
                "success": True,
                "message": "Product <product_id> successfully added."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., duplicate product_id)
            }

        Constraints:
            - product_id must be unique (not already registered).
            - All fields should be non-empty strings.
        """
        # Check for existing product_id
        if product_id in self.products:
            return {
                "success": False,
                "error": f"Product with product_id '{product_id}' already exists."
            }
        # Optional additional validation
        if not all(isinstance(x, str) and x.strip() for x in [product_id, name, category, description]):
            return {
                "success": False,
                "error": "All product fields must be non-empty strings."
            }
        # Construct and add new product
        product_info: ProductInfo = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "description": description
        }
        self.products[product_id] = product_info
        return {
            "success": True,
            "message": f"Product '{product_id}' successfully added."
        }

    def update_product_info(
        self,
        product_id: str,
        name: str = None,
        category: str = None,
        description: str = None
    ) -> dict:
        """
        Edit the details of an existing product.

        Args:
            product_id (str): The ID of the product to update.
            name (str, optional): The new name of the product.
            category (str, optional): The new category of the product.
            description (str, optional): The new description of the product.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Product info updated for product_id <id>"
                }
                On error:
                {
                    "success": False,
                    "error": <error message>
                }

        Constraints:
            - product_id must exist in self.products.
            - Only name, category, and description can be updated.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}
    
        updatable_fields = ["name", "category", "description"]
        product = self.products[product_id]
        updated = False

        if name is not None:
            product["name"] = name
            updated = True
        if category is not None:
            product["category"] = category
            updated = True
        if description is not None:
            product["description"] = description
            updated = True

        if not updated:
            return {"success": False, "error": "No valid fields to update"}

        self.products[product_id] = product
        return {
            "success": True,
            "message": f"Product info updated for product_id {product_id}"
        }

    def update_zone_info(self, zone_id: str, name: str = None, warehouse_id: str = None) -> dict:
        """
        Update the name and/or warehouse assignment of a zone.

        Args:
            zone_id (str): The unique identifier of the zone to be updated.
            name (str, optional): The new name for the zone.
            warehouse_id (str, optional): The new warehouse ID for the zone (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Zone info updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - The specified zone must exist.
            - If warehouse_id is provided, it must correspond to an existing warehouse.
            - At least one of 'name' or 'warehouse_id' must be provided.
        """
        # Check presence of the zone
        if zone_id not in self.zones:
            return {"success": False, "error": "Zone does not exist."}
    
        # Check that there's something to update
        if name is None and warehouse_id is None:
            return {"success": False, "error": "No update fields provided."}

        # If warehouse assignment change is requested, validate warehouse_id
        if warehouse_id is not None:
            if warehouse_id not in self.warehouses:
                return {"success": False, "error": f"Warehouse '{warehouse_id}' does not exist."}
            self.zones[zone_id]["warehouse_id"] = warehouse_id

        # If renaming, update the name
        if name is not None:
            self.zones[zone_id]["name"] = name

        return {"success": True, "message": "Zone info updated successfully."}


class WarehouseManagementSystem(BaseEnv):
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

    def get_warehouse_by_location(self, **kwargs):
        return self._call_inner_tool('get_warehouse_by_location', kwargs)

    def get_warehouse_by_id(self, **kwargs):
        return self._call_inner_tool('get_warehouse_by_id', kwargs)

    def list_all_warehouses(self, **kwargs):
        return self._call_inner_tool('list_all_warehouses', kwargs)

    def list_zones_in_warehouse(self, **kwargs):
        return self._call_inner_tool('list_zones_in_warehouse', kwargs)

    def get_zone_by_name(self, **kwargs):
        return self._call_inner_tool('get_zone_by_name', kwargs)

    def list_all_zones(self, **kwargs):
        return self._call_inner_tool('list_all_zones', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_products_by_criteria(self, **kwargs):
        return self._call_inner_tool('list_products_by_criteria', kwargs)

    def get_inventory_records(self, **kwargs):
        return self._call_inner_tool('get_inventory_records', kwargs)

    def get_current_inventory_status(self, **kwargs):
        return self._call_inner_tool('get_current_inventory_status', kwargs)

    def get_inventory_history(self, **kwargs):
        return self._call_inner_tool('get_inventory_history', kwargs)

    def get_inventory_record_by_key(self, **kwargs):
        return self._call_inner_tool('get_inventory_record_by_key', kwargs)

    def get_zone_warehouse_relationship(self, **kwargs):
        return self._call_inner_tool('get_zone_warehouse_relationship', kwargs)

    def check_zone_belongs_to_warehouse(self, **kwargs):
        return self._call_inner_tool('check_zone_belongs_to_warehouse', kwargs)

    def add_inventory_record(self, **kwargs):
        return self._call_inner_tool('add_inventory_record', kwargs)

    def update_inventory_quantity(self, **kwargs):
        return self._call_inner_tool('update_inventory_quantity', kwargs)

    def transfer_inventory_between_zones(self, **kwargs):
        return self._call_inner_tool('transfer_inventory_between_zones', kwargs)

    def reconcile_inventory(self, **kwargs):
        return self._call_inner_tool('reconcile_inventory', kwargs)

    def delete_inventory_record(self, **kwargs):
        return self._call_inner_tool('delete_inventory_record', kwargs)

    def add_zone_to_warehouse(self, **kwargs):
        return self._call_inner_tool('add_zone_to_warehouse', kwargs)

    def add_warehouse(self, **kwargs):
        return self._call_inner_tool('add_warehouse', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_info(self, **kwargs):
        return self._call_inner_tool('update_product_info', kwargs)

    def update_zone_info(self, **kwargs):
        return self._call_inner_tool('update_zone_info', kwargs)

