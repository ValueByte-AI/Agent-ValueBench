# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime
import datetime
import uuid



class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    address: str
    contact_info: str
    payment_info: str
    medical_history: str

class PrescriptionInfo(TypedDict):
    prescription_id: str
    customer_id: str
    medication_id: str
    prescriber_id: str
    valid_from: str
    valid_until: str
    refills_remaining: int
    is_valid: bool

class MedicationInfo(TypedDict):
    medication_id: str
    name: str
    dosage: str
    form: str
    stock_quantity: int
    requires_prescription: bool

class OrderInfo(TypedDict):
    order_id: str
    customer_id: str
    prescription_id: str
    order_date: str
    status: str
    payment_status: str
    delivery_id: str

class DeliveryInfo(TypedDict):
    delivery_id: str
    order_id: str
    shipping_provider: str
    tracking_number: str
    delivery_address: str
    delivery_status: str
    estimated_delivery_time: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Prescriptions: {prescription_id: PrescriptionInfo}
        self.prescriptions: Dict[str, PrescriptionInfo] = {}

        # Medications: {medication_id: MedicationInfo}
        self.medications: Dict[str, MedicationInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Deliveries: {delivery_id: DeliveryInfo}
        self.deliveries: Dict[str, DeliveryInfo] = {}

        # Virtual current time for the case. Case parameters may override this.
        self.current_time: str = "2023-10-26T12:00:00"

        # Constraints:
        # - Only valid prescriptions with available refills can be ordered.
        # - Medication stock_quantity must be sufficient to fulfill the order.
        # - Payment must be processed and confirmed before order fulfillment.
        # - Orders for prescription medications require prescription validation before processing.
        # - Delivery address must match or be verified for the customer.
        # - A prescription cannot be reused once refills are exhausted or it has expired.

    def _get_current_datetime(self) -> datetime.datetime:
        raw = getattr(self, "current_time", "2023-10-26T12:00:00")

        if isinstance(raw, datetime.datetime):
            return raw
        if isinstance(raw, datetime.date):
            return datetime.datetime.combine(raw, datetime.time.min)
        if isinstance(raw, (int, float)):
            return datetime.datetime.fromtimestamp(raw)
        if isinstance(raw, str):
            try:
                return datetime.datetime.fromisoformat(raw)
            except ValueError:
                try:
                    return datetime.datetime.strptime(raw, "%Y-%m-%d")
                except ValueError:
                    pass
        return datetime.datetime(2023, 10, 26, 12, 0, 0)

    def _get_current_date(self) -> datetime.date:
        return self._get_current_datetime().date()

    @staticmethod
    def _parse_case_date(raw_value: str) -> datetime.date:
        if not isinstance(raw_value, str):
            raise ValueError("Expected date string")

        try:
            return datetime.datetime.strptime(raw_value, "%Y-%m-%d").date()
        except ValueError:
            return datetime.datetime.fromisoformat(raw_value).date()

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer profile information using the given customer_id.

        Args:
            customer_id (str): Unique identifier for the customer.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": CustomerInfo  # Customer's profile info
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Customer not found"
                    }
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def search_customer_by_name(self, name: str) -> dict:
        """
        Retrieve customer(s) by name for identity resolution or support.

        Args:
            name (str): The customer's name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo],  # All matching customers (may be empty if none).
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid name).
            }

        Notes:
            - The name search is case-insensitive.
            - Returns all customers whose name exactly matches the provided value, ignoring case.
            - If no customers match, returns empty list (success).
            - If name is empty, returns error.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "A valid customer name must be provided."}

        name_lower = name.strip().lower()
        results = [
            customer for customer in self.customers.values()
            if customer.get("name", "").strip().lower() == name_lower
        ]
        return {"success": True, "data": results}

    def get_prescriptions_for_customer(self, customer_id: str) -> dict:
        """
        List all prescriptions associated with a given customer.

        Args:
            customer_id (str): Unique identifier for the customer.

        Returns:
            dict:
                Success: { "success": True, "data": List[PrescriptionInfo] }
                    - The list may be empty if the customer has no prescriptions.
                Failure: { "success": False, "error": str }
                    - If customer_id not found.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer not found" }

        prescriptions_list = [
            prescription for prescription in self.prescriptions.values()
            if prescription["customer_id"] == customer_id
        ]
        return { "success": True, "data": prescriptions_list }

    def get_prescription_by_id(self, prescription_id: str) -> dict:
        """
        Retrieve all details of a particular prescription by its ID.

        Args:
            prescription_id (str): The unique identifier for the prescription.

        Returns:
            dict: 
                - On success: { "success": True, "data": PrescriptionInfo }
                - On failure: { "success": False, "error": "Prescription not found" }

        Constraints:
            - The prescription must exist in the system.
        """
        prescription = self.prescriptions.get(prescription_id)
        if prescription is None:
            return { "success": False, "error": "Prescription not found" }

        return { "success": True, "data": prescription }


    def check_prescription_validity(self, prescription_id: str) -> dict:
        """
        Check if a prescription is valid: 
        (1) it exists, 
        (2) is marked as valid, 
        (3) the current date is within its effective dates, 
        (4) has remaining refills.

        Args:
            prescription_id (str): The unique identifier for the prescription.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "is_valid": bool,
                            "within_effective_dates": bool,
                            "has_refills": bool,
                            "eligible": bool   # Only True if all the above are True
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message (e.g. "Prescription not found")
                    }

        Constraints:
            - Prescription must exist.
            - Date strings in 'valid_from' and 'valid_until' must be properly formatted (YYYY-MM-DD). 
              If not, treat as not within dates.
        """
        prescription = self.prescriptions.get(prescription_id)
        if not prescription:
            return { "success": False, "error": "Prescription not found" }

        # Extract and check fields
        is_valid = bool(prescription.get("is_valid", False))
        has_refills = prescription.get("refills_remaining", 0) > 0

        # Check dates
        today = self._get_current_date()
        within_effective_dates = False
        try:
            valid_from = self._parse_case_date(prescription["valid_from"])
            valid_until = self._parse_case_date(prescription["valid_until"])
            within_effective_dates = valid_from <= today <= valid_until
        except Exception:
            # If date parsing fails, treat as not within valid dates
            within_effective_dates = False

        eligible = is_valid and within_effective_dates and has_refills

        return {
            "success": True,
            "data": {
                "is_valid": is_valid,
                "within_effective_dates": within_effective_dates,
                "has_refills": has_refills,
                "eligible": eligible
            }
        }

    def get_medication_by_id(self, medication_id: str) -> dict:
        """
        Retrieve medication details by medication_id.

        Args:
            medication_id (str): The unique identifier for the medication.

        Returns:
            dict: {
                "success": True,
                "data": MedicationInfo,  # Details of the medication if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - medication_id must exist in the system.
        """
        medication = self.medications.get(medication_id)
        if medication is None:
            return {"success": False, "error": "Medication not found"}
        return {"success": True, "data": medication}

    def get_medication_inventory(self, medication_id: str) -> dict:
        """
        Query the current stock quantity for a specific medication.

        Args:
            medication_id (str): The unique identifier for the medication.

        Returns:
            dict: 
                - If medication exists: { "success": True, "data": { "medication_id": str, "stock_quantity": int } }
                - If medication does not exist: { "success": False, "error": "Medication not found" }

        Constraints:
            - The medication_id must exist in the medications dictionary.
        """
        medication = self.medications.get(medication_id)
        if medication is None:
            return { "success": False, "error": "Medication not found" }
        return {
            "success": True,
            "data": {
                "medication_id": medication_id,
                "stock_quantity": medication["stock_quantity"]
            }
        }

    def check_medication_requires_prescription(self, medication_id: str) -> dict:
        """
        Check whether a medication requires a valid prescription.

        Args:
            medication_id (str): The medication's unique identifier.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": {
                        "medication_id": <str>,
                        "requires_prescription": <bool>
                    }
                  }
                - On failure: {
                    "success": False,
                    "error": "Medication not found"
                  }
        Constraints:
            - medication_id must exist in the system.
        """
        medication = self.medications.get(medication_id)
        if not medication:
            return {"success": False, "error": "Medication not found"}
        return {
            "success": True,
            "data": {
                "medication_id": medication_id,
                "requires_prescription": medication["requires_prescription"]
            }
        }

    def get_orders_for_customer(self, customer_id: str) -> dict:
        """
        List all orders placed by a given customer.

        Args:
            customer_id (str): The ID of the customer.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[OrderInfo]  # May be empty if no orders
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Customer not found"
                    }

        Constraints:
            - The customer_id must exist in the system.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        orders = [
            order_info for order_info in self.orders.values()
            if order_info["customer_id"] == customer_id
        ]
        return {"success": True, "data": orders}

    def get_order_status(self, order_id: str) -> dict:
        """
        Fetch the status and payment_status fields for an order, given its order_id.

        Args:
            order_id (str): Unique identifier for the order.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "status": str,
                    "payment_status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. 'Order not found'
            }

        Constraints:
            - The order with order_id must exist.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}

        return {
            "success": True,
            "data": {
                "status": order["status"],
                "payment_status": order["payment_status"]
            }
        }

    def get_delivery_details_by_order_id(self, order_id: str) -> dict:
        """
        Retrieve the delivery information (DeliveryInfo) for a given order_id.

        Args:
            order_id (str): The unique identifier of the order for which delivery details are requested.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": DeliveryInfo  # Delivery details for the order
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Error description ('Order not found', etc.)
                    }

        Constraints:
            - The order must exist.
            - The order must have a valid delivery_id, and that delivery_id must exist in the system.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}

        delivery_id = order.get("delivery_id", "")
        if not delivery_id or delivery_id not in self.deliveries:
            return {"success": False, "error": "No delivery assigned or delivery not found for this order"}

        delivery_info = self.deliveries[delivery_id]
        return {"success": True, "data": delivery_info}

    def verify_customer_delivery_address(self, customer_id: str, delivery_address: str) -> dict:
        """
        Checks whether the given delivery address is valid/approved for the specified customer.
    
        Args:
            customer_id (str): The unique identifier for the customer.
            delivery_address (str): The delivery address to check.

        Returns:
            dict: {
                "success": True, 
                "data": { "is_valid": True, "message": "Address is valid/approved for customer." }
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Customer must exist in the system.
            - Address is only validated via direct equality to the stored customer address.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer ID not found"}
    
        if customer["address"] == delivery_address:
            return {
                "success": True,
                "data": {
                    "is_valid": True,
                    "message": "Address is valid/approved for customer."
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "is_valid": False,
                    "message": "Address does not match the approved address on record."
                }
            }

    def place_order(self, customer_id: str, prescription_id: str) -> dict:
        """
        Create a new order for a valid prescription and medication, associated with a customer.

        Args:
            customer_id (str): The ID of the customer placing the order.
            prescription_id (str): The ID of the prescription to be used for the order.

        Returns:
            dict: {
                "success": True,
                "message": "Order <order_id> successfully placed."
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints enforced:
            - Customer, prescription, and medication existence.
            - Only valid (not expired, not invalidated, not exhausted) prescriptions with available refills can be ordered.
            - Medication stock_quantity must be sufficient.
            - Delivery address must be present for the customer.
            - Orders for prescription medications require prescription validation before processing.
        """

        # 1. Check for existence of entities
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found."}
        if prescription_id not in self.prescriptions:
            return {"success": False, "error": "Prescription not found."}

        customer = self.customers[customer_id]
        prescription = self.prescriptions[prescription_id]
        medication_id = prescription["medication_id"]

        if medication_id not in self.medications:
            return {"success": False, "error": "Medication not found."}

        medication = self.medications[medication_id]

        # 2. Check that prescription belongs to this customer
        if prescription["customer_id"] != customer_id:
            return {"success": False, "error": "Prescription does not belong to this customer."}

        # 3. Check prescription validity
        if not prescription["is_valid"]:
            return {"success": False, "error": "Prescription is not valid."}
        if prescription["refills_remaining"] <= 0:
            return {"success": False, "error": "No refills remaining on prescription."}
        # Check date validity
        try:
            current_date = self._get_current_date()
            valid_from_date = self._parse_case_date(prescription["valid_from"])
            valid_until_date = self._parse_case_date(prescription["valid_until"])
            if current_date < valid_from_date or current_date > valid_until_date:
                return {"success": False, "error": "Prescription is not within its valid date range."}
        except Exception:
            return {"success": False, "error": "Invalid date format in prescription."}

        # 4. Check medication stock
        if medication["stock_quantity"] < 1:
            return {"success": False, "error": "Medication is out of stock."}

        # 5. If medication requires prescription, double-check prescription requirements (already done above)

        # 6. Delivery address present
        if not customer.get("address"):
            return {"success": False, "error": "Customer does not have a delivery address on file."}

        # 7. Generate order_id and set order fields
        order_id = str(uuid.uuid4())
        order_date = self._get_current_datetime().isoformat()
        order_info = {
            "order_id": order_id,
            "customer_id": customer_id,
            "prescription_id": prescription_id,
            "order_date": order_date,
            "status": "Pending",
            "payment_status": "Pending",
            "delivery_id": ""
        }

        self.orders[order_id] = order_info

        return {"success": True, "message": f"Order {order_id} successfully placed."}

    def decrement_prescription_refills(self, prescription_id: str) -> dict:
        """
        Reduce the 'refills_remaining' count on a prescription after a successful order.

        Args:
            prescription_id (str): The unique identifier of the prescription.

        Returns:
            dict: {
                "success": True,
                "message": "Refills decremented"
            }
            or
            {
                "success": False,
                "error": "Describes the validation or update error"
            }

        Constraints:
            - Only valid prescriptions with available refills can be decremented.
            - If refills_remaining reaches 0, prescription is marked as invalid.
        """
        # Check if prescription exists
        prescription = self.prescriptions.get(prescription_id)
        if prescription is None:
            return { "success": False, "error": "Prescription not found" }

        # Check if prescription is currently valid
        if not prescription.get("is_valid", False):
            return { "success": False, "error": "Prescription is already invalid" }

        # Check if there are refills remaining
        refills_remaining = prescription.get("refills_remaining", 0)
        if refills_remaining <= 0:
            return { "success": False, "error": "No refills remaining for this prescription" }

        # Decrement the refills
        prescription["refills_remaining"] = refills_remaining - 1

        # Invalidate the prescription if refills run out
        if prescription["refills_remaining"] == 0:
            prescription["is_valid"] = False

        # Update back into state (dict is mutable, but for clarity)
        self.prescriptions[prescription_id] = prescription

        return { "success": True, "message": "Refills decremented" }

    def decrement_medication_stock(self, medication_id: str, amount: int) -> dict:
        """
        Decrease the inventory count for a specified medication after order placement.

        Args:
            medication_id (str): The identifier of the medication whose stock is to be decremented.
            amount (int): The amount to decrement from the medication's inventory (must be > 0).

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "Decremented stock by <amount>. New stock_quantity: <value>."
                    }
                Failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Medication must exist in the system.
            - Amount must be a positive integer.
            - Stock quantity must be sufficient to cover the decrement (cannot go below zero).
        """
        if medication_id not in self.medications:
            return {"success": False, "error": "Medication does not exist."}
        if not isinstance(amount, int) or amount <= 0:
            return {"success": False, "error": "Decrement amount must be a positive integer."}
        if self.medications[medication_id]["stock_quantity"] < amount:
            return {
                "success": False,
                "error": f"Insufficient stock. Available: {self.medications[medication_id]['stock_quantity']}, requested: {amount}."
            }
        self.medications[medication_id]["stock_quantity"] -= amount
        return {
            "success": True,
            "message": f"Decremented stock by {amount}. New stock_quantity: {self.medications[medication_id]['stock_quantity']}."
        }

    def process_payment_for_order(self, order_id: str) -> dict:
        """
        Charge customer for a given order and update that order's payment_status to 'paid'.

        Args:
            order_id (str): The unique identifier of the order to process payment for.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Payment processed for order <order_id>."
                }
                Failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Order must exist.
            - Customer must exist for the order.
            - Customer must have valid payment_info.
            - Payment cannot be reprocessed for an already paid order.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found." }
        if order["payment_status"] == "paid":
            return { "success": False, "error": "Order is already paid." }

        customer_id = order.get("customer_id")
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer not found for this order." }
        payment_info = customer.get("payment_info", "").strip()
        if not payment_info:
            return { "success": False, "error": "Customer payment information is missing or invalid." }

        # Simulate payment processing (success assumed)
        order["payment_status"] = "paid"
        self.orders[order_id] = order  # ensure updated in store

        return {
            "success": True,
            "message": f"Payment processed for order {order_id}."
        }

    def assign_delivery_to_order(
        self,
        order_id: str,
        shipping_provider: str,
        delivery_address: str,
        tracking_number: str = "",
        delivery_status: str = "pending",
        estimated_delivery_time: str = ""
    ) -> dict:
        """
        Create or update delivery details for an order, specifying shipping provider, delivery address, etc.

        Args:
            order_id (str): The order to assign delivery for.
            shipping_provider (str): Name of the shipping or logistics provider.
            delivery_address (str): The address where medication should be delivered (must match customer's address).
            tracking_number (str, optional): Tracking number for the shipment.
            delivery_status (str, optional): Current status of the delivery.
            estimated_delivery_time (str, optional): ETA for delivery.

        Returns:
            dict: {
                "success": True,
                "message": "Delivery assigned/updated for order <order_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - order_id must exist.
            - delivery_address must exactly match the corresponding customer's address.
            - Updates delivery if exists; creates delivery otherwise.
            - Only one delivery per order.
        """
        # Check if order exists
        if order_id not in self.orders:
            return {"success": False, "error": "Order does not exist."}
        order = self.orders[order_id]
        customer_id = order["customer_id"]

        # Check if customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Associated customer not found."}
        customer = self.customers[customer_id]

        # Validate delivery address constraint
        if delivery_address != customer["address"]:
            return {"success": False, "error": "Delivery address does not match customer's registered address."}

        delivery_id = order.get("delivery_id", "")

        # Update existing delivery
        if delivery_id and delivery_id in self.deliveries:
            delivery = self.deliveries[delivery_id]
            delivery.update({
                "shipping_provider": shipping_provider,
                "tracking_number": tracking_number,
                "delivery_address": delivery_address,
                "delivery_status": delivery_status,
                "estimated_delivery_time": estimated_delivery_time
            })
            self.deliveries[delivery_id] = delivery  # not strictly necessary, but for consistency
            return {"success": True, "message": f"Delivery updated for order {order_id}"}

        # Create new delivery
        new_delivery_id = f"DELIVERY_{order_id}"
        # Ensure no duplicate delivery_id
        if new_delivery_id in self.deliveries:
            return {"success": False, "error": f"Internal error: delivery_id {new_delivery_id} already exists."}

        delivery_info = {
            "delivery_id": new_delivery_id,
            "order_id": order_id,
            "shipping_provider": shipping_provider,
            "tracking_number": tracking_number,
            "delivery_address": delivery_address,
            "delivery_status": delivery_status,
            "estimated_delivery_time": estimated_delivery_time
        }
        self.deliveries[new_delivery_id] = delivery_info
        # Link delivery_id to order
        order["delivery_id"] = new_delivery_id
        self.orders[order_id] = order
        return {"success": True, "message": f"Delivery assigned to order {order_id}"}

    def update_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Change the status of an order (e.g., to 'processing', 'fulfilled', or 'cancelled').

        Args:
            order_id (str): The order's unique identifier.
            new_status (str): The new status string to assign to the order.

        Returns:
            dict: {
                "success": True,
                "message": "Order status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - order_id must exist.
            - new_status must be a non-empty string.
            - No restriction on status value or transition in current spec.
        """
        if order_id not in self.orders:
            return { "success": False, "error": "Order ID does not exist" }

        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "New status must be a non-empty string" }

        self.orders[order_id]['status'] = new_status.strip()
        return { "success": True, "message": f"Order status updated to '{new_status.strip()}'" }

    def update_delivery_status(self, delivery_id: str, new_status: str) -> dict:
        """
        Change the delivery_status of a delivery.

        Args:
            delivery_id (str): The unique identifier for the delivery to update.
            new_status (str): The new status value to set (e.g., 'in transit', 'delivered').

        Returns:
            dict: {
                "success": True,
                "message": "Delivery status updated to '<new_status>' for delivery <delivery_id>."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - delivery_id must exist in self.deliveries.
            - new_status should be a non-empty string.
        """
        if delivery_id not in self.deliveries:
            return {"success": False, "error": f"Delivery with id '{delivery_id}' does not exist."}

        if not isinstance(new_status, str) or not new_status.strip():
            return {"success": False, "error": "New delivery status must be a non-empty string."}

        self.deliveries[delivery_id]['delivery_status'] = new_status.strip()
        return {
            "success": True,
            "message": f"Delivery status updated to '{new_status.strip()}' for delivery {delivery_id}."
        }

    def add_or_update_customer_address(self, customer_id: str, address: str) -> dict:
        """
        Add a new or update the existing delivery address for a customer, with address verification.

        Args:
            customer_id (str): Unique identifier for the customer.
            address (str): The new or updated delivery address.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Customer address added/updated and verified."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - customer_id must exist in the system.
            - address must be non-empty (after stripping whitespace).
            - Address verification must succeed (simulated here as always successful).
        """
        # Check if the customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer ID does not exist."}

        # Validate new address
        if not isinstance(address, str) or not address.strip():
            return {"success": False, "error": "Address is blank or invalid."}

        # Simulate address verification (assume all addresses are valid)
        address_verified = True  # This could be replaced with real verification

        if not address_verified:
            return {"success": False, "error": "Address verification failed."}

        # Update the customer's address
        self.customers[customer_id]["address"] = address.strip()

        return {"success": True, "message": "Customer address added/updated and verified."}

    def invalidate_prescription(self, prescription_id: str) -> dict:
        """
        Mark a prescription as no longer valid, e.g., due to expiration or depletion of refills.

        Args:
            prescription_id (str): The unique ID of the prescription to invalidate.

        Returns:
            dict: {
                "success": True,
                "message": "Prescription {prescription_id} invalidated successfully."
            }
            or
            {
                "success": False,
                "error": "Prescription not found."
            }

        Constraints:
            - Only marks the prescription as invalid if it exists.
            - Idempotent: If the prescription is already invalid, operation is treated as success.
        """
        pres = self.prescriptions.get(prescription_id)
        if not pres:
            return { "success": False, "error": "Prescription not found." }

        pres["is_valid"] = False
        return { "success": True, "message": f"Prescription {prescription_id} invalidated successfully." }

    def restock_medication(self, medication_id: str, quantity: int) -> dict:
        """
        Increase the stock_quantity for a medication in the inventory.

        Args:
            medication_id (str): The identifier for the medication to restock.
            quantity (int): The amount to add to the current stock. Must be positive.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "<quantity> units added to <medication_id> (now <new_stock> in stock)"
                }
                On error: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - medication_id must exist in the system.
            - quantity must be a positive integer (> 0).
        """
        if medication_id not in self.medications:
            return { "success": False, "error": "Invalid medication_id" }
        if not isinstance(quantity, int) or quantity <= 0:
            return { "success": False, "error": "Quantity must be a positive integer" }

        current_stock = self.medications[medication_id]["stock_quantity"]
        new_stock = current_stock + quantity
        self.medications[medication_id]["stock_quantity"] = new_stock

        return {
            "success": True,
            "message": f"{quantity} units added to {medication_id} (now {new_stock} in stock)"
        }


class OnlinePharmacyOrderManagementSystem(BaseEnv):
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

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def search_customer_by_name(self, **kwargs):
        return self._call_inner_tool('search_customer_by_name', kwargs)

    def get_prescriptions_for_customer(self, **kwargs):
        return self._call_inner_tool('get_prescriptions_for_customer', kwargs)

    def get_prescription_by_id(self, **kwargs):
        return self._call_inner_tool('get_prescription_by_id', kwargs)

    def check_prescription_validity(self, **kwargs):
        return self._call_inner_tool('check_prescription_validity', kwargs)

    def get_medication_by_id(self, **kwargs):
        return self._call_inner_tool('get_medication_by_id', kwargs)

    def get_medication_inventory(self, **kwargs):
        return self._call_inner_tool('get_medication_inventory', kwargs)

    def check_medication_requires_prescription(self, **kwargs):
        return self._call_inner_tool('check_medication_requires_prescription', kwargs)

    def get_orders_for_customer(self, **kwargs):
        return self._call_inner_tool('get_orders_for_customer', kwargs)

    def get_order_status(self, **kwargs):
        return self._call_inner_tool('get_order_status', kwargs)

    def get_delivery_details_by_order_id(self, **kwargs):
        return self._call_inner_tool('get_delivery_details_by_order_id', kwargs)

    def verify_customer_delivery_address(self, **kwargs):
        return self._call_inner_tool('verify_customer_delivery_address', kwargs)

    def place_order(self, **kwargs):
        return self._call_inner_tool('place_order', kwargs)

    def decrement_prescription_refills(self, **kwargs):
        return self._call_inner_tool('decrement_prescription_refills', kwargs)

    def decrement_medication_stock(self, **kwargs):
        return self._call_inner_tool('decrement_medication_stock', kwargs)

    def process_payment_for_order(self, **kwargs):
        return self._call_inner_tool('process_payment_for_order', kwargs)

    def assign_delivery_to_order(self, **kwargs):
        return self._call_inner_tool('assign_delivery_to_order', kwargs)

    def update_order_status(self, **kwargs):
        return self._call_inner_tool('update_order_status', kwargs)

    def update_delivery_status(self, **kwargs):
        return self._call_inner_tool('update_delivery_status', kwargs)

    def add_or_update_customer_address(self, **kwargs):
        return self._call_inner_tool('add_or_update_customer_address', kwargs)

    def invalidate_prescription(self, **kwargs):
        return self._call_inner_tool('invalidate_prescription', kwargs)

    def restock_medication(self, **kwargs):
        return self._call_inner_tool('restock_medication', kwargs)
