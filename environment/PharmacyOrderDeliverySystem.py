# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
import uuid
from typing import List, Dict



# Patient: patient_id, name, contact_info, prescription_info
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    contact_info: str
    prescription_info: str

# Medication: medication_id, name, dosage, form, instruction
class MedicationInfo(TypedDict):
    medication_id: str
    name: str
    dosage: str
    form: str
    instruction: str

# OrderMedication: order_id, medication_id, quantity
class OrderMedicationInfo(TypedDict):
    order_id: str
    medication_id: str
    quantity: int

# MedicationOrder: order_id, patient_id, medication_list, order_date, order_status, prescription_required
class MedicationOrderInfo(TypedDict):
    order_id: str
    patient_id: str
    medication_list: List[OrderMedicationInfo]
    order_date: str
    order_status: str
    prescription_required: bool

# Shipment: shipment_id, order_id, carrier, tracking_number, delivery_status, shipped_date, expected_delivery_date, delivered_date
class ShipmentInfo(TypedDict):
    shipment_id: str
    order_id: str
    carrier: str
    tracking_number: str
    delivery_status: str
    shipped_date: str
    expected_delivery_date: str
    delivered_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Pharmacy medication order and delivery tracking system state.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Medications: {medication_id: MedicationInfo}
        self.medications: Dict[str, MedicationInfo] = {}

        # MedicationOrders: {order_id: MedicationOrderInfo}
        self.medication_orders: Dict[str, MedicationOrderInfo] = {}

        # Shipments: {shipment_id: ShipmentInfo}
        self.shipments: Dict[str, ShipmentInfo] = {}

        # Constraints:
        # - Only valid (active) medication orders can be tracked for delivery.
        # - A patient can only access the status of their own medication orders.
        # - Delivery status options follow defined workflow (e.g., "pending", "shipped", "in transit", "out for delivery", "delivered").
        # - Prescription medications require valid prescriptions attached to the order before shipment.

    def _patient_has_valid_prescription(self, patient: PatientInfo) -> bool:
        prescription_info = patient.get("prescription_info")
        return bool(prescription_info and str(prescription_info).strip())

    def _medication_requires_prescription(self, patient_id: str, medication: MedicationInfo) -> bool:
        medication_id = medication["medication_id"]

        # Reuse this patient's historical order requirements when the medication
        # has already been prescribed through the system.
        for existing_order in self.medication_orders.values():
            if existing_order.get("patient_id") != patient_id:
                continue
            if not existing_order.get("prescription_required"):
                continue
            for item in existing_order.get("medication_list", []):
                if item.get("medication_id") == medication_id:
                    return True

        prescription_text = str(
            self.patients.get(patient_id, {}).get("prescription_info") or ""
        ).lower()
        medication_name = str(medication.get("name") or "").lower()
        if medication_id.lower() in prescription_text:
            return True
        if medication_name and medication_name in prescription_text:
            return True

        return "prescription" in str(medication.get("instruction") or "").lower()

    def _find_shipment_by_order_id(self, order_id: str):
        for shipment_id, shipment in self.shipments.items():
            if shipment["order_id"] == order_id:
                return shipment_id, shipment
        return None, None

    def _calculate_expected_delivery_date(self, order_date: str) -> str:
        try:
            parsed_date = datetime.date.fromisoformat(order_date)
        except Exception:
            return ""
        return (parsed_date + datetime.timedelta(days=1)).isoformat()

    def _create_pending_shipment(self, order_id: str, order_date: str) -> ShipmentInfo:
        shipment_id = f"SHIP-{uuid.uuid4().hex[:8].upper()}"
        while shipment_id in self.shipments:
            shipment_id = f"SHIP-{uuid.uuid4().hex[:8].upper()}"

        existing_tracking_numbers = {
            shipment.get("tracking_number") for shipment in self.shipments.values()
        }
        tracking_number = f"AUTO-{uuid.uuid4().hex[:10].upper()}"
        while tracking_number in existing_tracking_numbers:
            tracking_number = f"AUTO-{uuid.uuid4().hex[:10].upper()}"

        shipment: ShipmentInfo = {
            "shipment_id": shipment_id,
            "order_id": order_id,
            "carrier": "AutoAssigned",
            "tracking_number": tracking_number,
            "delivery_status": "pending",
            "shipped_date": "",
            "expected_delivery_date": self._calculate_expected_delivery_date(order_date),
            "delivered_date": "",
        }
        self.shipments[shipment_id] = shipment
        return shipment

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient details by patient_id, including prescription information.

        Args:
            patient_id (str): Unique patient identifier.

        Returns:
            dict:
                On success: { "success": True, "data": PatientInfo }
                On failure: { "success": False, "error": "Patient not found" }

        Constraints:
            - patient_id must exist in the system.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve patient information using the patient's name.

        Args:
            name (str): The name of the patient to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo],  # List of patients with this name (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Patient not found"
            }

        Notes:
            - If multiple patients have the same name, all will be returned.
            - Names are case-sensitive unless normalization is desired.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid patient name parameter"}

        matches = [patient for patient in self.patients.values() if patient["name"] == name]

        if not matches:
            return {"success": False, "error": "Patient not found"}

        return {"success": True, "data": matches}

    def list_medication_orders_for_patient(self, patient_id: str) -> dict:
        """
        List all medication orders belonging to a given patient.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict:
                - If patient exists:
                    {
                        "success": True,
                        "data": List[MedicationOrderInfo]  # All orders for this patient (may be empty)
                    }
                - If patient does not exist:
                    {
                        "success": False,
                        "error": "Patient not found"
                    }

        Constraints:
            - The given patient_id must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        orders = [
            order for order in self.medication_orders.values()
            if order["patient_id"] == patient_id
        ]
        return { "success": True, "data": orders }

    def get_active_medication_orders_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve all valid (active) medication orders for the specified patient.

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[MedicationOrderInfo],  # Possibly empty if no active orders
                    }
                - On failure (invalid patient):
                    {
                        "success": False,
                        "error": "Patient not found"
                    }

        Constraints:
            - Only returns orders for the provided patient_id.
            - Only includes "active" orders.
              "Active" excludes statuses: 'cancelled', 'completed', 'delivered', 'fulfilled'.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        # Define terminal/inactive order statuses
        inactive_statuses = {"cancelled", "canceled", "completed", "delivered", "fulfilled"}

        active_orders = [
            order for order in self.medication_orders.values()
            if order["patient_id"] == patient_id and
               order["order_status"].lower() not in inactive_statuses
        ]

        return {"success": True, "data": active_orders}

    def get_medication_order_by_id(self, order_id: str) -> dict:
        """
        Retrieve all details for a specific medication order using order_id.

        Args:
            order_id (str): The unique ID of the medication order.

        Returns:
            dict: 
                - If found: {"success": True, "data": MedicationOrderInfo}
                - If not found: {"success": False, "error": "Medication order not found"}
        """
        order = self.medication_orders.get(order_id)
        if not order:
            return {"success": False, "error": "Medication order not found"}
        return {"success": True, "data": order}

    def get_medications_in_order(self, order_id: str) -> dict:
        """
        Retrieve the list of medications, with full details and ordered quantities,
        for the medication order specified by order_id.

        Args:
            order_id (str): The ID of the medication order.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each item: medication details and 'quantity'
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., order not found
            }

        Constraints:
            - If the referenced medication order does not exist, return error.
            - If a medication reference is missing in self.medications, skip it (or add with 'medication_id': ..., 'missing': True).
        """
        order = self.medication_orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}

        medications_info = []
        for om in order.get("medication_list", []):
            medication_id = om.get("medication_id")
            medication = self.medications.get(medication_id)
            entry = {}
            if medication:
                entry = {
                    "medication_id": medication["medication_id"],
                    "name": medication["name"],
                    "dosage": medication["dosage"],
                    "form": medication["form"],
                    "instruction": medication["instruction"],
                    "quantity": om.get("quantity", 0)
                }
            else:
                # Gracefully signal missing medication data
                entry = {
                    "medication_id": medication_id,
                    "missing": True,
                    "quantity": om.get("quantity", 0)
                }
            medications_info.append(entry)

        return {"success": True, "data": medications_info}

    def get_shipment_by_order_id(self, order_id: str) -> dict:
        """
        Retrieve all shipment details (ShipmentInfo) associated with the specified order_id.

        Args:
            order_id (str): The medication order ID whose shipment(s) is/are to be looked up.

        Returns:
            dict: {
                "success": True,
                "data": List[ShipmentInfo],  # May be an empty list if no shipments for this order_id
            }
            or
            {
                "success": False,
                "error": str  # Error reason (e.g., order_id not found)
            }

        Constraints:
            - If order_id does not exist in the system, returns failure.
            - Returns all shipments that reference the given order_id by shipment.order_id.
        """
        if order_id not in self.medication_orders:
            return { "success": False, "error": "Order ID does not exist." }

        result = [
            shipment_info for shipment_info in self.shipments.values()
            if shipment_info["order_id"] == order_id
        ]

        return { "success": True, "data": result }

    def get_shipment_status(self, shipment_id: str = None, order_id: str = None) -> dict:
        """
        Retrieve the current delivery status for a shipment by shipment_id or order_id.

        Args:
            shipment_id (str, optional): The unique ID of the shipment.
            order_id (str, optional): The unique ID of the order whose shipment's status to query.

        Returns:
            dict:
              On success:
                { "success": True, "data": { "delivery_status": <str> } }
              On error:
                { "success": False, "error": <reason> }

        Constraints:
            - At least one of shipment_id or order_id must be provided.
            - If both are provided and point to different shipments, shipment_id takes precedence.
            - Returns the delivery_status of the first matching shipment if multiple shipments exist for an order.
        """
        # Case 1: shipment_id provided and found
        if shipment_id:
            shipment = self.shipments.get(shipment_id)
            if shipment:
                return { "success": True, "data": { "delivery_status": shipment["delivery_status"] } }
            else:
                return { "success": False, "error": f"No shipment found for shipment_id '{shipment_id}'." }

        # Case 2: order_id provided, no shipment_id or not found by shipment_id
        if order_id:
            for s in self.shipments.values():
                if s["order_id"] == order_id:
                    return { "success": True, "data": { "delivery_status": s["delivery_status"] } }
            return { "success": False, "error": f"No shipment found for order_id '{order_id}'." }

        # Neither provided
        return { "success": False, "error": "At least one of shipment_id or order_id must be provided." }

    def list_shipment_status_options(self) -> dict:
        """
        Return the defined valid workflow/status options for delivery shipments.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # The valid shipment delivery status workflow options
            }

        Constraints:
            - Options follow the defined workflow for delivery. 
            - Always succeeds (unless critical internal error).
        """
        # Defined workflow for delivery status (from the constraint example)
        status_options = [
            "pending",
            "shipped",
            "in transit",
            "out for delivery",
            "delivered"
        ]
        return { "success": True, "data": status_options }

    def check_prescription_validity(self, order_id: str) -> dict:
        """
        Confirm whether the prescription attached to a medication order is valid.

        Args:
            order_id (str): The unique ID of the medication order to check prescription validity for.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "order_id": str,
                            "prescription_required": bool,
                            "valid": bool,
                            "message": str
                        }
                    }
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - If the order does not exist, return an error.
            - If prescription is required, prescription_info must be present (non-empty) on the patient.
            - If prescription is not required, always valid.
        """
        # Check order exists
        order = self.medication_orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order does not exist"}
    
        prescription_required = order["prescription_required"]
        patient_id = order["patient_id"]
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient associated with order does not exist"}
    
        # If prescription is not required, always valid
        if not prescription_required:
            return {
                "success": True,
                "data": {
                    "order_id": order_id,
                    "prescription_required": False,
                    "valid": True,
                    "message": "Prescription not required for this order."
                }
            }
    
        # For this environment, assume "valid" = prescription_info is a non-empty string
        prescription_info = patient.get("prescription_info")
        if prescription_info and str(prescription_info).strip():
            return {
                "success": True,
                "data": {
                    "order_id": order_id,
                    "prescription_required": True,
                    "valid": True,
                    "message": "Valid prescription is attached to the order."
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "order_id": order_id,
                    "prescription_required": True,
                    "valid": False,
                    "message": "No valid prescription attached to the order."
                }
            }

    def update_shipment_status(self, shipment_id: str, new_status: str) -> dict:
        """
        Updates the delivery status of a shipment following allowed workflow transitions.

        Args:
            shipment_id (str): Unique identifier of the shipment to update.
            new_status (str): The desired delivery status. Must follow defined workflow.

        Returns:
            dict: {
                "success": True,
                "message": "Shipment status updated from X to Y."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Shipment must exist.
            - Only valid (active) medication orders can be tracked for delivery.
            - Only allow workflow-valid status transitions.
            - Delivery status options are: "pending", "shipped", "in transit", "out for delivery", "delivered".
        """
        # Allowed statuses in defined order
        allowed_statuses = [
            "pending",
            "shipped",
            "in transit",
            "out for delivery",
            "delivered"
        ]

        # Workflow: only allow next-in-sequence or same status if already at final
        next_status = {
            "pending": "shipped",
            "shipped": "in transit",
            "in transit": "out for delivery",
            "out for delivery": "delivered",
            "delivered": None  # Final state
        }

        # Check shipment exists
        if shipment_id not in self.shipments:
            return { "success": False, "error": "Shipment does not exist." }

        shipment = self.shipments[shipment_id]
        current_status = shipment["delivery_status"]

        # Check new_status is valid
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid delivery status '{new_status}'." }

        # Check workflow transition: must be the defined next_status from current, or stay at "delivered"
        if current_status == new_status:
            # No change, permitted (idempotent)
            return { "success": True, "message": f"Shipment status already '{new_status}'." }

        if next_status.get(current_status) != new_status:
            return {
                "success": False,
                "error": f"Invalid status transition from '{current_status}' to '{new_status}'."
            }

        # Check associated order is active
        order_id = shipment["order_id"]
        if order_id not in self.medication_orders:
            return { "success": False, "error": "Associated medication order not found." }
        order = self.medication_orders[order_id]
        if order["order_status"].lower() not in ["active", "processing", "pending", "shipped"]:
            # Define active order statuses as needed
            return { "success": False, "error": "Medication order is not active; cannot update shipment." }

        # Update the shipment status
        old_status = shipment["delivery_status"]
        shipment["delivery_status"] = new_status
        self.shipments[shipment_id] = shipment

        return {
            "success": True,
            "message": f"Shipment status updated from '{old_status}' to '{new_status}'."
        }

    def mark_order_as_shipped(self, order_id: str) -> dict:
        """
        Update the medication order and the associated shipment to indicate that the order has shipped.

        Args:
            order_id (str): The ID of the medication order to mark as shipped.

        Returns:
            dict: {
                "success": True,
                "message": "Order marked as shipped."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Order must exist and be in a valid (active) status.
            - If prescription is required, a valid prescription must be attached.
            - A shipment corresponding to the order must exist.
            - Shipment status must allow transition to "shipped".
            - Shipment and order states are updated accordingly.
        """

        # Check if order exists
        order = self.medication_orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order does not exist." }

        # Check order_status: Only active orders can be shipped (let's consider 'pending' or 'processing' as active)
        active_statuses = {"pending", "processing", "active"}
        if order["order_status"] not in active_statuses:
            return { "success": False, "error": f"Order is not in a state that can be shipped (current status: {order['order_status']})." }

        # If prescription is required, check for valid prescription
        if order["prescription_required"]:
            patient_id = order["patient_id"]
            patient = self.patients.get(patient_id)
            if (not patient) or (not patient.get("prescription_info")) or patient["prescription_info"].strip() == "":
                return { "success": False, "error": "A valid prescription is required before the order can be shipped." }

        # Find the shipment associated with this order_id
        _, shipment = self._find_shipment_by_order_id(order_id)

        if not shipment:
            return { "success": False, "error": "No shipment record found for this order." }

        # Allowed status transitions
        allowed_from_statuses = {"pending", "in transit"}  # Assuming these can move to "shipped"
        if shipment["delivery_status"] not in {"pending"}:
            return { "success": False, "error": f"Shipment already marked as '{shipment['delivery_status']}', cannot mark as shipped." }

        now = datetime.datetime.now().isoformat()

        # Update order and shipment states
        order["order_status"] = "shipped"
        shipment["delivery_status"] = "shipped"
        shipment["shipped_date"] = now

        # Commit changes (since dicts are mutable, this happens in place)
        self.medication_orders[order_id] = order
        self.shipments[shipment["shipment_id"]] = shipment

        return { "success": True, "message": "Order marked as shipped." }

    def attach_prescription_to_order(self, order_id: str, prescription_info: str) -> dict:
        """
        Add or update the valid prescription for a medication order.
    
        Args:
            order_id (str): The order to which to attach the prescription.
            prescription_info (str): The prescription data/details to attach.

        Returns:
            dict:
                - On success: { "success": True, "message": "Prescription attached to order <order_id>." }
                - On error: { "success": False, "error": <error_message> }
    
        Constraints:
            - The order must exist.
            - The associated patient must exist.
            - Updates the PatientInfo's prescription_info with the provided value.
        """

        # Check order exists
        order = self.medication_orders.get(order_id)
        if not order:
            return { "success": False, "error": "Medication order not found." }

        patient_id = order.get("patient_id")
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Associated patient not found." }

        # Attach/update the prescription to the patient (or to the order if model changes)
        patient["prescription_info"] = prescription_info
        # Optionally: mark that prescription is now attached (if needed)

        return {
            "success": True,
            "message": f"Prescription attached to order {order_id}."
        }


    def create_medication_order(self, patient_id: str, medication_items: List[Dict], order_date: str) -> dict:
        """
        Place a new medication order for a patient.

        Args:
            patient_id (str): The patient's unique identifier.
            medication_items (List[dict]): List of items, each has:
                - medication_id (str)
                - quantity (int)
            order_date (str): Date of the order (ISO format or suitable string).

        Returns:
            dict:
                On success: { "success": True, "message": "Order created", "order_id": str }
                On failure: { "success": False, "error": str }

        Constraints:
            - Patient must exist.
            - All medications must exist.
            - Quantity for each medication must be positive.
            - If any medication requires prescription, patient must have valid prescription_info.
            - Order ID uniquely generated.
            - medication_items should not be empty.
        """
        # 1. Patient validity
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found"}

        # 2. medication_items not empty
        if not medication_items or not isinstance(medication_items, list):
            return {"success": False, "error": "No medications specified for the order"}

        # 3. Validate medications and build medication_list
        medication_list = []
        prescription_required = False
        for item in medication_items:
            med_id = item.get("medication_id")
            qty = item.get("quantity")
            medication = self.medications.get(med_id)
            if not medication:
                return {"success": False, "error": f"Medication {med_id} does not exist"}
            if not isinstance(qty, int) or qty <= 0:
                return {"success": False, "error": f"Invalid quantity for medication {med_id}"}
            if self._medication_requires_prescription(patient_id, medication):
                prescription_required = True
            medication_list.append({
                "order_id": "",  # Will be filled after order_id is determined
                "medication_id": med_id,
                "quantity": qty
            })

        # 4. If prescription required, validate
        if prescription_required:
            if not self._patient_has_valid_prescription(patient):
                return {"success": False, "error": "Prescription required but not found for this patient"}

        # 5. Generate unique order_id
        order_id = str(uuid.uuid4())
        for med in medication_list:
            med["order_id"] = order_id

        # 6. Create order
        new_order: MedicationOrderInfo = {
            "order_id": order_id,
            "patient_id": patient_id,
            "medication_list": medication_list,
            "order_date": order_date,
            "order_status": "pending",
            "prescription_required": prescription_required
        }
        self.medication_orders[order_id] = new_order
        self._create_pending_shipment(order_id, order_date)

        # 7. Return success
        return {"success": True, "message": "Order created", "order_id": order_id}

    def cancel_medication_order(self, order_id: str) -> dict:
        """
        Invalidate or remove a medication order if allowed.

        Args:
            order_id (str): The ID of the medication order to cancel.

        Returns:
            dict: 
                success (bool), 
                message (str) if successful, 
                error (str) if failed (e.g., order does not exist or cannot be canceled).

        Constraints:
            - Only orders that are not "shipped", "delivered", or already "canceled" may be canceled.
            - All associated shipments must also be in a cancelable state (not shipped or delivered).
        """
        # Check for existence
        order = self.medication_orders.get(order_id)
        if order is None:
            return { "success": False, "error": f"Order {order_id} does not exist." }

        # Disallowed final states
        non_cancelable_statuses = {"shipped", "delivered", "canceled"}
        status = order.get("order_status", "").lower()
        if status in non_cancelable_statuses:
            return { "success": False, "error": f"Order {order_id} cannot be canceled (status: {status})." }

        # Check if there is an associated shipment that is shipped or delivered
        for shipment in self.shipments.values():
            if shipment["order_id"] == order_id:
                delivery_status = shipment.get("delivery_status", "").lower()
                if delivery_status in {"shipped", "in transit", "out for delivery", "delivered"}:
                    return {
                        "success": False,
                        "error": f"Order {order_id} cannot be canceled; shipment already {delivery_status}."
                    }
                # Optionally, remove/cancel the shipment
                shipment["delivery_status"] = "canceled"

        # Mark the order as canceled
        order["order_status"] = "canceled"

        return {
            "success": True,
            "message": f"Order {order_id} canceled successfully."
        }

    def update_medication_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Manually change the status of a medication order (e.g., from draft to active).
    
        Args:
            order_id (str): The ID of the medication order to update.
            new_status (str): The new status to set for the order.
    
        Returns:
            dict: {
                "success": True,
                "message": str  # Success message.
            }
            or
            {
                "success": False,
                "error": str  # Error message.
            }
    
        Constraints:
            - order_id must refer to an existing medication order
            - new_status must be in the set of valid statuses
            - Order status transitions should follow valid workflow if specified (not enforced unless workflow specified)
        """
        # Define allowed statuses; extend as required by workflow
        allowed_statuses = {
            "draft",
            "active",
            "pending",
            "processing",
            "halted",
            "on_hold",
            "shipped",
            "delivered",
            "fulfilled",
            "cancelled",
            "canceled",
            "completed",
        }

        # Check order existence
        if order_id not in self.medication_orders:
            return {"success": False, "error": "Medication order does not exist."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed statuses: {sorted(allowed_statuses)}"}

        normalized_status = "on_hold" if new_status in {"on_hold", "halted"} else new_status
        self.medication_orders[order_id]["order_status"] = normalized_status

        return {
            "success": True,
            "message": f"Medication order {order_id} status updated to '{normalized_status}'."
        }


class PharmacyOrderDeliverySystem(BaseEnv):
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

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def get_patient_by_name(self, **kwargs):
        return self._call_inner_tool('get_patient_by_name', kwargs)

    def list_medication_orders_for_patient(self, **kwargs):
        return self._call_inner_tool('list_medication_orders_for_patient', kwargs)

    def get_active_medication_orders_for_patient(self, **kwargs):
        return self._call_inner_tool('get_active_medication_orders_for_patient', kwargs)

    def get_medication_order_by_id(self, **kwargs):
        return self._call_inner_tool('get_medication_order_by_id', kwargs)

    def get_medications_in_order(self, **kwargs):
        return self._call_inner_tool('get_medications_in_order', kwargs)

    def get_shipment_by_order_id(self, **kwargs):
        return self._call_inner_tool('get_shipment_by_order_id', kwargs)

    def get_shipment_status(self, **kwargs):
        return self._call_inner_tool('get_shipment_status', kwargs)

    def list_shipment_status_options(self, **kwargs):
        return self._call_inner_tool('list_shipment_status_options', kwargs)

    def check_prescription_validity(self, **kwargs):
        return self._call_inner_tool('check_prescription_validity', kwargs)

    def update_shipment_status(self, **kwargs):
        return self._call_inner_tool('update_shipment_status', kwargs)

    def mark_order_as_shipped(self, **kwargs):
        return self._call_inner_tool('mark_order_as_shipped', kwargs)

    def attach_prescription_to_order(self, **kwargs):
        return self._call_inner_tool('attach_prescription_to_order', kwargs)

    def create_medication_order(self, **kwargs):
        return self._call_inner_tool('create_medication_order', kwargs)

    def cancel_medication_order(self, **kwargs):
        return self._call_inner_tool('cancel_medication_order', kwargs)

    def update_medication_order_status(self, **kwargs):
        return self._call_inner_tool('update_medication_order_status', kwargs)
