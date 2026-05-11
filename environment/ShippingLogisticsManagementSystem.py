# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class LocationInfo(TypedDict):
    location_id: str
    address: str
    postcode: str
    country: str
    customer_id: str

class PackageInfo(TypedDict):
    package_id: str
    weight: float
    volume: float
    dimensions: str
    shipment_id: str

class ShipmentInfo(TypedDict):
    shipment_id: str
    origin_location_id: str
    destination_location_id: str
    status: str
    scheduled_pickup: str
    scheduled_delivery: str
    carrier_id: str

class ShippingRateRuleInfo(TypedDict):
    rule_id: str
    origin_postcode: str
    destination_postcode: str
    min_weight: float
    max_weight: float
    min_volume: float
    max_volume: float
    price: float
    carrier_id: str

class TransactionInfo(TypedDict):
    transaction_id: str
    shipment_id: str
    package_id: str
    date: str
    amount: float
    payment_method: str
    status: str

class CustomerInfo(TypedDict):
    customer_id: str
    company_name: str
    contact_info: str
    billing_address: str

class CarrierInfo(TypedDict):
    carrier_id: str
    name: str
    contact_info: str
    integration_setting: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Locations: {location_id: LocationInfo}
        self.locations: Dict[str, LocationInfo] = {}
        # Packages: {package_id: PackageInfo}
        self.packages: Dict[str, PackageInfo] = {}
        # Shipments: {shipment_id: ShipmentInfo}
        self.shipments: Dict[str, ShipmentInfo] = {}
        # Shipping Rate Rules: {rule_id: ShippingRateRuleInfo}
        self.shipping_rate_rules: Dict[str, ShippingRateRuleInfo] = {}
        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}
        # Carriers: {carrier_id: CarrierInfo}
        self.carriers: Dict[str, CarrierInfo] = {}

        # Constraints (to be enforced by environment methods):
        # - Shipping quotes must be computed based on package characteristics and defined rate rules.
        # - A package must have weight and volume specified for accurate quoting.
        # - Transactions must be linked to valid shipments or packages.
        # - Shipments must have defined origin and destination locations.
        # - Only valid, supported postcode routes may be quoted.
        # - Shipment and transaction statuses must be updated according to logistics workflow steps.

    @staticmethod
    def _is_effectively_unassigned(shipment_id: Any) -> bool:
        """
        Treat placeholder shipment markers as unassigned inventory.

        Several formal cases encode packages awaiting booking with values such as
        "", "UNASSIGNED", "PENDING", or "NONE" in package.shipment_id. These
        placeholders are not backed by real shipment records and should not block
        create_new_shipment from taking ownership of the package.
        """
        if shipment_id is None:
            return True
        if not isinstance(shipment_id, str):
            return False
        normalized = shipment_id.strip().upper()
        return normalized in {"", "UNASSIGNED", "PENDING", "NONE"}

    def get_location_by_postcode(self, postcode: str) -> dict:
        """
        Retrieve detailed location information for all locations matching a given postcode.

        Args:
            postcode (str): The postcode to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # All locations where postcode matches
            }
            OR
            {
                "success": False,
                "error": str  # if postcode input is invalid
            }

        Constraints:
            - Postcode must be a non-empty string.
            - Query matches are case sensitive (unless normalizing is required; not specified here).
            - No error if no locations match; return empty list.
        """
        if not isinstance(postcode, str) or not postcode.strip():
            return {"success": False, "error": "Postcode must be a non-empty string."}

        result = [
            loc_info
            for loc_info in self.locations.values()
            if loc_info.get("postcode") == postcode
        ]

        return {"success": True, "data": result}

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve location information for the provided location_id.

        Args:
            location_id (str): Unique identifier for the location.
    
        Returns:
            dict:
                - If found: {
                      "success": True,
                      "data": LocationInfo  # All details for the requested location.
                  }
                - If not found: {
                      "success": False,
                      "error": "Location not found"
                  }

        Constraints:
            - location_id must exist in the system.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }
        return { "success": True, "data": self.locations[location_id] }

    def list_locations_for_customer(self, customer_id: str) -> dict:
        """
        List all location records registered for a specific customer.

        Args:
            customer_id (str): The ID of the customer whose locations are requested.

        Returns:
            dict: {
               "success": True,
               "data": List[LocationInfo]  # Locations belonging to the customer; empty if none.
            }
            or
            {
               "success": False,
               "error": str  # Description (e.g. customer not found)
            }

        Constraints:
            - customer_id must exist in the customers dict.
            - Returns all associated locations if customer exists.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist."}

        locations = [
            location for location in self.locations.values()
            if location['customer_id'] == customer_id
        ]
        return {"success": True, "data": locations}

    def get_package_info(self, package_id: str) -> dict:
        """
        Retrieve the details of a package, including weight, volume, and dimensions.

        Args:
            package_id (str): The unique identifier of the package.

        Returns:
            dict: {
                "success": True,
                "data": PackageInfo  # All info for the package
            }
            OR
            {
                "success": False,
                "error": "Package not found"
            }

        Constraints:
            - The package_id must exist in the system.
        """
        package = self.packages.get(package_id)
        if not package:
            return { "success": False, "error": "Package not found" }
        return { "success": True, "data": package }

    def find_applicable_shipping_rate_rules(
        self, 
        origin_postcode: str, 
        destination_postcode: str, 
        weight: float, 
        volume: float
    ) -> dict:
        """
        Find all shipping rate rules that apply to a route (origin & destination postcodes) 
        and given package characteristics (weight, volume).

        Args:
            origin_postcode (str): Origin postcode.
            destination_postcode (str): Destination postcode.
            weight (float): Weight of the package (must be positive, required).
            volume (float): Volume of the package (must be positive, required).

        Returns:
            dict: {
                "success": True,
                "data": List[ShippingRateRuleInfo],  # all matching rate rules, may be empty
            }
            or 
            {
                "success": False,
                "error": str  # error message for invalid input
            }

        Constraints:
            - Only rules matching origin/destination postcodes and where
              min_weight <= weight <= max_weight and min_volume <= volume <= max_volume
              are included.
            - weight and volume must be specified as positive numbers.
        """
        if (not isinstance(weight, (int, float)) or weight <= 0 or
            not isinstance(volume, (int, float)) or volume <= 0):
            return {"success": False, "error": "Invalid package weight or volume (must be positive numbers)"}
        if not isinstance(origin_postcode, str) or not isinstance(destination_postcode, str):
            return {"success": False, "error": "Origin and destination postcodes must be strings"}

        result = []
        for rule in self.shipping_rate_rules.values():
            if (
                rule["origin_postcode"] == origin_postcode
                and rule["destination_postcode"] == destination_postcode
                and rule["min_weight"] <= weight <= rule["max_weight"]
                and rule["min_volume"] <= volume <= rule["max_volume"]
            ):
                result.append(rule)
        return {"success": True, "data": result}

    def compute_shipping_quote(
        self,
        origin_postcode: str,
        destination_postcode: str,
        weight: float,
        volume: float
    ) -> dict:
        """
        Calculate shipping cost using matched shipping rate rule, package weight, and volume
        for given origin and destination postcodes.

        Args:
            origin_postcode (str): Postcode of the shipment origin.
            destination_postcode (str): Postcode of the shipment destination.
            weight (float): The weight of the package (must be > 0).
            volume (float): The volume of the package (must be > 0).

        Returns:
            dict:
                - success: True, and data (dict) containing keys price, carrier_id, rule_id, and optionally carrier_name.
                - success: False, and error (str) explaining why quoting failed.

        Constraints:
            - Shipping quotes must use defined shipping rate rules.
            - Weight and volume must be provided and > 0.
            - Only supported postcode routes may be quoted.

        """
        # Validate inputs
        if not origin_postcode or not destination_postcode:
            return { "success": False, "error": "Both origin and destination postcodes are required." }
        if weight is None or volume is None:
            return { "success": False, "error": "Both weight and volume are required." }
        if weight <= 0 or volume <= 0:
            return { "success": False, "error": "Weight and volume must be positive values." }

        # Find all applicable rate rules
        applicable_rules = []
        for rule in self.shipping_rate_rules.values():
            if (rule['origin_postcode'] == origin_postcode and
                rule['destination_postcode'] == destination_postcode and
                rule['min_weight'] <= weight <= rule['max_weight'] and
                rule['min_volume'] <= volume <= rule['max_volume']):
                applicable_rules.append(rule)

        if not applicable_rules:
            return { "success": False, "error": "No applicable shipping rate rule found for the given route and package characteristics." }

        # Choose the rule with the lowest price (if multiples exist)
        matched_rule = min(applicable_rules, key=lambda r: r["price"])

        # Optionally, provide carrier_name in response
        carrier_id = matched_rule["carrier_id"]
        carrier_name = self.carriers[carrier_id]["name"] if carrier_id in self.carriers else None

        result = {
            "price": matched_rule["price"],
            "carrier_id": carrier_id,
            "rule_id": matched_rule["rule_id"],
        }
        if carrier_name:
            result["carrier_name"] = carrier_name

        return { "success": True, "data": result }

    def get_shipment_info(self, shipment_id: str) -> dict:
        """
        Retrieve detailed information about a specific shipment.

        Args:
            shipment_id (str): The unique identifier of the shipment.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": ShipmentInfo}
                - If not found:
                    {"success": False, "error": "Shipment does not exist"}
        Constraints:
            - The shipment_id must exist in the system.
        """
        shipment = self.shipments.get(shipment_id)
        if shipment is None:
            return {"success": False, "error": "Shipment does not exist"}
        return {"success": True, "data": shipment}

    def get_shipments_by_location(self, location_id: str) -> dict:
        """
        Retrieve all shipments where the origin or destination location matches the given location_id.

        Args:
            location_id (str): Unique identifier for the location.

        Returns:
            dict: {
                "success": True,
                "data": List[ShipmentInfo]
            }
            or
            {
                "success": False,
                "error": str  # if location does not exist
            }
    
        Constraints:
            - The location_id must exist in the locations registry.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }

        matched_shipments = [
            shipment_info for shipment_info in self.shipments.values()
            if shipment_info["origin_location_id"] == location_id or shipment_info["destination_location_id"] == location_id
        ]

        return { "success": True, "data": matched_shipments }

    def get_transaction_info(self, transaction_id: str) -> dict:
        """
        Retrieve all information about a transaction by its transaction_id.

        Args:
            transaction_id (str): The ID of the transaction to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo  # Transaction details, if found
            }
            OR
            {
                "success": False,
                "error": "Transaction not found"
            }

        Constraints:
            - The transaction must exist in the system.
            - Only information retrieval; no workflow or linkage checks performed.
        """
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Transaction not found"}

        return {"success": True, "data": self.transactions[transaction_id]}

    def list_transactions_for_shipment(self, shipment_id: str) -> dict:
        """
        List all transactions associated with the specified shipment.

        Args:
            shipment_id (str): The unique identifier for the shipment.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List can be empty if no transactions found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., shipment does not exist)
            }

        Constraints:
            - The specified shipment_id must exist in the system.
            - Only transactions linked (via shipment_id) to the given shipment are returned.
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "Shipment does not exist"}

        transaction_list = [
            t_info for t_info in self.transactions.values()
            if t_info["shipment_id"] == shipment_id
        ]

        return {"success": True, "data": transaction_list}

    def get_customer_info(self, customer_id: str) -> dict:
        """
        Retrieve the details (CustomerInfo) for a specific customer.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: 
                { "success": True, "data": CustomerInfo } on success,
                or
                { "success": False, "error": "Customer does not exist" } on failure.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer does not exist" }
        return { "success": True, "data": customer }

    def get_carrier_info(self, carrier_id: str) -> dict:
        """
        Retrieve information about a shipping carrier.

        Args:
            carrier_id (str): The unique identifier for the carrier.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": CarrierInfo}
                - If not found:
                    {"success": False, "error": "Carrier not found"}
        """
        carrier = self.carriers.get(carrier_id)
        if carrier is None:
            return {"success": False, "error": "Carrier not found"}
        return {"success": True, "data": carrier}

    def list_supported_routes(self) -> dict:
        """
        List all unique valid (origin_postcode, destination_postcode) pairs for which
        at least one shipping rate rule exists.

        Returns:
            dict: {
                "success": True,
                "data": List[Tuple[str, str]],  # List of (origin_postcode, destination_postcode) pairs
            }

        Notes:
            - The list contains unique pairs; duplicate postcode pairs (from multiple rules) are not repeated.
            - Returns an empty list if there are no shipping rate rules defined.
        """
        pairs_set = set()
        for rule in self.shipping_rate_rules.values():
            pair = (rule['origin_postcode'], rule['destination_postcode'])
            pairs_set.add(pair)
        result = [list(pair) for pair in sorted(pairs_set)]
        return {"success": True, "data": result}

    def add_new_package(
        self, 
        package_id: str, 
        weight: float, 
        volume: float, 
        dimensions: str, 
        shipment_id: str
    ) -> dict:
        """
        Add a new package to the system.

        Args:
            package_id (str): Unique package ID.
            weight (float): Weight of the package (must be positive).
            volume (float): Volume of the package (must be positive).
            dimensions (str): Dimensions of the package (non-empty).
            shipment_id (str): Shipment ID this package is associated with (must exist).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Package <package_id> added successfully."}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - package_id must be unique.
            - weight and volume must be specified and positive.
            - dimensions must be non-empty.
            - shipment_id must exist in shipments.
        """
        # Check for unique package ID
        if package_id in self.packages:
            return {"success": False, "error": f"Package ID '{package_id}' already exists."}

        # Validate shipment existence
        if shipment_id not in self.shipments:
            return {"success": False, "error": f"Shipment ID '{shipment_id}' does not exist."}

        # Validate weight and volume
        if not isinstance(weight, (int, float)) or weight <= 0:
            return {"success": False, "error": "Weight must be a positive number."}
        if not isinstance(volume, (int, float)) or volume <= 0:
            return {"success": False, "error": "Volume must be a positive number."}

        # Validate dimensions
        if not isinstance(dimensions, str) or not dimensions.strip():
            return {"success": False, "error": "Dimensions must be a non-empty string."}

        # Create and add the new package
        new_package = {
            "package_id": package_id,
            "weight": weight,
            "volume": volume,
            "dimensions": dimensions,
            "shipment_id": shipment_id
        }
        self.packages[package_id] = new_package

        return {
            "success": True,
            "message": f"Package {package_id} added successfully."
        }

    def create_new_shipment(
        self,
        shipment_id: str,
        origin_location_id: str,
        destination_location_id: str,
        package_ids: list,
        carrier_id: str,
        scheduled_pickup: str,
        scheduled_delivery: str,
        status: str = "Scheduled"
    ) -> dict:
        """
        Create a new shipment linking packages, locations, and carrier.

        Args:
            shipment_id (str): Unique ID for the new shipment.
            origin_location_id (str): Location ID for the origin.
            destination_location_id (str): Location ID for the destination.
            package_ids (list of str): List of package IDs to be associated with this shipment.
            carrier_id (str): Carrier ID to use for shipment.
            scheduled_pickup (str): Scheduled pickup datetime.
            scheduled_delivery (str): Scheduled delivery datetime.
            status (str, optional): Initial status (default "Scheduled").

        Returns:
            dict: { "success": True, "message": "Shipment <id> created successfully." }
                  or
                  { "success": False, "error": "<reason>" }

        Constraints:
            - shipment_id must be unique.
            - origin/destination_location_id and carrier_id must exist.
            - All package_ids must exist and not be already assigned to a different shipment.
            - package_ids list must not be empty.
        """
        # Validate uniqueness of shipment_id
        if shipment_id in self.shipments:
            return {"success": False, "error": "Shipment ID already exists."}
    
        # Validate locations
        if origin_location_id not in self.locations:
            return {"success": False, "error": "Origin location does not exist."}
        if destination_location_id not in self.locations:
            return {"success": False, "error": "Destination location does not exist."}
    
        # Validate carrier
        if carrier_id not in self.carriers:
            return {"success": False, "error": "Carrier does not exist."}
    
        # Validate package list
        if not isinstance(package_ids, list) or len(package_ids) == 0:
            return {"success": False, "error": "package_ids must be a non-empty list."}
    
        validated_packages = []
        for pid in package_ids:
            if pid not in self.packages:
                return {"success": False, "error": f"Package {pid} does not exist."}
            pkg_info = self.packages[pid]
            # Placeholder values such as UNASSIGNED/PENDING/NONE are not real
            # bookings and should not block shipment creation.
            if not self._is_effectively_unassigned(pkg_info.get("shipment_id")):
                return {"success": False, "error": f"Package {pid} is already assigned to shipment {pkg_info['shipment_id']}."}
            validated_packages.append(pkg_info)
    
        # Add the shipment
        shipment_info = {
            "shipment_id": shipment_id,
            "origin_location_id": origin_location_id,
            "destination_location_id": destination_location_id,
            "status": status,
            "scheduled_pickup": scheduled_pickup,
            "scheduled_delivery": scheduled_delivery,
            "carrier_id": carrier_id,
        }
        self.shipments[shipment_id] = shipment_info

        # Link packages to this shipment
        for pid in package_ids:
            self.packages[pid]["shipment_id"] = shipment_id

        return {
            "success": True,
            "message": f"Shipment {shipment_id} created successfully."
        }

    def update_shipment_status(self, shipment_id: str, new_status: str) -> dict:
        """
        Update the tracking status of an existing shipment.

        Args:
            shipment_id (str): The identifier of the shipment to update.
            new_status (str): The new status value to set.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Shipment status updated to <new_status> for shipment <shipment_id>."}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - The shipment must exist in the system.
            - Status changes should conform to workflow steps, but if not specified, update as requested.
        """
        shipment = self.shipments.get(shipment_id)
        if shipment is None:
            return {"success": False, "error": f"Shipment {shipment_id} does not exist."}

        # If there were allowed statuses or transitions, check here.
        # For now, we proceed to update.

        shipment["status"] = new_status
        self.shipments[shipment_id] = shipment  # Redundant, but explicit.

        return {
            "success": True,
            "message": f"Shipment status updated to {new_status} for shipment {shipment_id}."
        }

    def add_new_transaction(
        self,
        transaction_id: str,
        shipment_id: str,
        package_id: str,
        date: str,
        amount: float,
        payment_method: str,
        status: str
    ) -> dict:
        """
        Register a new transaction linked to a valid shipment or package.

        Args:
            transaction_id (str): Unique transaction identifier.
            shipment_id (str): Associated shipment ID (may be empty if package_id given).
            package_id (str): Associated package ID (may be empty if shipment_id given).
            date (str): Transaction date (ISO format).
            amount (float): Transaction amount.
            payment_method (str): Payment method (description/code).
            status (str): Initial status of the transaction.

        Returns:
            dict: 
                On success: { "success": True, "message": "Transaction <id> added." }
                On error: { "success": False, "error": "<Reason>" }

        Constraints:
            - Must provide at least one of shipment_id or package_id.
            - At least one of shipment_id or package_id must exist in the system.
            - transaction_id must be unique.
        """
        # Check for uniqueness of transaction_id
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists." }

        # Must have at least one valid reference
        shipment_exists = shipment_id and shipment_id in self.shipments
        package_exists = package_id and package_id in self.packages

        if not (shipment_exists or package_exists):
            return { "success": False, "error": "A valid shipment_id or package_id must be provided." }

        # Fill in all fields, with empty string if one of shipment_id/package_id is not supplied
        transaction_info = {
            "transaction_id": transaction_id,
            "shipment_id": shipment_id if shipment_exists else "",
            "package_id": package_id if package_exists else "",
            "date": date,
            "amount": amount,
            "payment_method": payment_method,
            "status": status
        }

        self.transactions[transaction_id] = transaction_info

        return { "success": True, "message": f"Transaction {transaction_id} added." }

    def update_transaction_status(self, transaction_id: str, new_status: str) -> dict:
        """
        Update the processing or payment status of a transaction.

        Args:
            transaction_id (str): The unique ID of the transaction to update.
            new_status (str): The new status string for this transaction.

        Returns:
            dict: {
                "success": True, "message": "Transaction status updated."
            } on success.
            dict: {
                "success": False, "error": str
            } on failure.

        Constraints:
            - Transaction must exist.
            - The new status is accepted as provided (no explicit validation).
        """
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction not found." }
        if not isinstance(new_status, str) or new_status.strip() == "":
            return { "success": False, "error": "New status must be a non-empty string." }

        self.transactions[transaction_id]['status'] = new_status
        return { "success": True, "message": "Transaction status updated." }

    def add_shipping_rate_rule(
        self,
        rule_id: str,
        origin_postcode: str,
        destination_postcode: str,
        min_weight: float,
        max_weight: float,
        min_volume: float,
        max_volume: float,
        price: float,
        carrier_id: str
    ) -> dict:
        """
        Add a new shipping rate rule for new postcode routes or price changes.

        Args:
            rule_id (str): Unique identifier for the new rule.
            origin_postcode (str): Origin postcode for the rule.
            destination_postcode (str): Destination postcode for the rule.
            min_weight (float): Minimum allowed weight (kg).
            max_weight (float): Maximum allowed weight (kg).
            min_volume (float): Minimum allowed volume (cubic meters).
            max_volume (float): Maximum allowed volume (cubic meters).
            price (float): Quoted shipping price.
            carrier_id (str): Identifier for the shipping provider (must exist).

        Returns:
            dict: {"success": True, "message": "..."} on success,
                  {"success": False, "error": "..."} on failure.

        Constraints:
            - rule_id must be unique.
            - carrier_id must exist.
            - min_weight <= max_weight, min_volume <= max_volume.
            - All numeric values must be non-negative.
        """
        # Uniqueness check for rule_id
        if rule_id in self.shipping_rate_rules:
            return {"success": False, "error": f"Rule ID '{rule_id}' already exists."}

        # Existence check for carrier
        if carrier_id not in self.carriers:
            return {"success": False, "error": f"Carrier ID '{carrier_id}' does not exist."}

        # Numeric value checks
        if min_weight < 0 or max_weight < 0 or min_volume < 0 or max_volume < 0 or price < 0:
            return {"success": False, "error": "Negative values for weight, volume, or price are not allowed."}

        # Range logic checks
        if min_weight > max_weight:
            return {"success": False, "error": "min_weight cannot be greater than max_weight."}
        if min_volume > max_volume:
            return {"success": False, "error": "min_volume cannot be greater than max_volume."}

        # (Optionally, could check for duplicate rules with same keys,
        # but spec does not explicitly require this.)

        self.shipping_rate_rules[rule_id] = {
            "rule_id": rule_id,
            "origin_postcode": origin_postcode,
            "destination_postcode": destination_postcode,
            "min_weight": min_weight,
            "max_weight": max_weight,
            "min_volume": min_volume,
            "max_volume": max_volume,
            "price": price,
            "carrier_id": carrier_id
        }

        return {"success": True, "message": f"Shipping rate rule '{rule_id}' added successfully."}

    def remove_package(self, package_id: str) -> dict:
        """
        Delete a package record from the system.
    
        Args:
            package_id (str): The unique identifier of the package to remove.

        Returns:
            dict:
                - On success: {"success": True, "message": "Package <package_id> removed."}
                - If package not found: {"success": False, "error": "Package not found"}
                - If package is linked to any transaction: {"success": False, "error": "Cannot remove package; it is referenced by existing transactions."}
    
        Constraints:
            - Do not remove a package if any transaction is linked to it.
            - Transaction integrity must be preserved.
        """
        # Check if package exists
        if package_id not in self.packages:
            return {"success": False, "error": "Package not found"}

        # Check for transactions referencing this package
        for txn in self.transactions.values():
            if txn.get("package_id") == package_id:
                return {"success": False, "error": "Cannot remove package; it is referenced by existing transactions."}

        # Remove the package
        del self.packages[package_id]
        return {"success": True, "message": f"Package {package_id} removed."}

    def remove_shipment(self, shipment_id: str) -> dict:
        """
        Delete a shipment record from the system if and only if it has no linked packages or transactions.

        Args:
            shipment_id (str): The unique identifier for the shipment to remove.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Shipment <shipment_id> removed." }
                On failure (any reason):
                    { "success": False, "error": <reason> }

        Constraints:
            - A shipment cannot be removed if there are packages or transactions linked to it.
            - The shipment must exist in the system.
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": f"Shipment '{shipment_id}' does not exist."}

        # Check for linked packages
        linked_packages = [
            p for p in self.packages.values() if p.get('shipment_id') == shipment_id
        ]
        if linked_packages:
            return {
                "success": False,
                "error": f"Cannot remove shipment '{shipment_id}': linked packages exist."
            }

        # Check for linked transactions
        linked_transactions = [
            t for t in self.transactions.values() if t.get('shipment_id') == shipment_id
        ]
        if linked_transactions:
            return {
                "success": False,
                "error": f"Cannot remove shipment '{shipment_id}': linked transactions exist."
            }

        # Proceed to remove the shipment
        del self.shipments[shipment_id]
        return {
            "success": True,
            "message": f"Shipment '{shipment_id}' removed."
        }


class ShippingLogisticsManagementSystem(BaseEnv):
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

    def get_location_by_postcode(self, **kwargs):
        return self._call_inner_tool('get_location_by_postcode', kwargs)

    def get_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_location_by_id', kwargs)

    def list_locations_for_customer(self, **kwargs):
        return self._call_inner_tool('list_locations_for_customer', kwargs)

    def get_package_info(self, **kwargs):
        return self._call_inner_tool('get_package_info', kwargs)

    def find_applicable_shipping_rate_rules(self, **kwargs):
        return self._call_inner_tool('find_applicable_shipping_rate_rules', kwargs)

    def compute_shipping_quote(self, **kwargs):
        return self._call_inner_tool('compute_shipping_quote', kwargs)

    def get_shipment_info(self, **kwargs):
        return self._call_inner_tool('get_shipment_info', kwargs)

    def get_shipments_by_location(self, **kwargs):
        return self._call_inner_tool('get_shipments_by_location', kwargs)

    def get_transaction_info(self, **kwargs):
        return self._call_inner_tool('get_transaction_info', kwargs)

    def list_transactions_for_shipment(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_shipment', kwargs)

    def get_customer_info(self, **kwargs):
        return self._call_inner_tool('get_customer_info', kwargs)

    def get_carrier_info(self, **kwargs):
        return self._call_inner_tool('get_carrier_info', kwargs)

    def list_supported_routes(self, **kwargs):
        return self._call_inner_tool('list_supported_routes', kwargs)

    def add_new_package(self, **kwargs):
        return self._call_inner_tool('add_new_package', kwargs)

    def create_new_shipment(self, **kwargs):
        return self._call_inner_tool('create_new_shipment', kwargs)

    def update_shipment_status(self, **kwargs):
        return self._call_inner_tool('update_shipment_status', kwargs)

    def add_new_transaction(self, **kwargs):
        return self._call_inner_tool('add_new_transaction', kwargs)

    def update_transaction_status(self, **kwargs):
        return self._call_inner_tool('update_transaction_status', kwargs)

    def add_shipping_rate_rule(self, **kwargs):
        return self._call_inner_tool('add_shipping_rate_rule', kwargs)

    def remove_package(self, **kwargs):
        return self._call_inner_tool('remove_package', kwargs)

    def remove_shipment(self, **kwargs):
        return self._call_inner_tool('remove_shipment', kwargs)
