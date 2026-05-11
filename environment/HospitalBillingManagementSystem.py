# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    contact_info: str

class BillInfo(TypedDict):
    bill_id: str
    patient_id: str
    total_amount: float
    outstanding_balance: float
    bill_date: str
    status: str

class PaymentInfo(TypedDict):
    payment_id: str
    bill_id: str
    payment_date: str
    amount: float
    payment_method: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for hospital billing management.
        """

        # Patients: {patient_id: PatientInfo}
        # Entity: Patient (patient_id, name, contact_info)
        self.patients: Dict[str, PatientInfo] = {}

        # Bills: {bill_id: BillInfo}
        # Entity: Bill (bill_id, patient_id, total_amount, outstanding_balance, bill_date, status)
        self.bills: Dict[str, BillInfo] = {}

        # Payments: {payment_id: PaymentInfo}
        # Entity: Payment (payment_id, bill_id, payment_date, amount, payment_method)
        self.payments: Dict[str, PaymentInfo] = {}

        # Constraints:
        # - Payments cannot exceed the outstanding balance on a bill.
        # - Bills must exist before payments can be made to them.
        # - Payments should update the outstanding balance of the bill accordingly.
        # - The status of a bill should change to "paid" when the outstanding balance reaches zero.

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient information given a patient_id.

        Args:
            patient_id (str): The identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # All patient fields
            }
            or
            {
                "success": False,
                "error": str  # "Patient not found"
            }

        Constraints:
            - The patient_id must exist in the system for a successful query.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def list_all_patients(self) -> dict:
        """
        Retrieve information for all registered patients in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # May be empty if no patients exist
            }

        Constraints:
            - No special constraints; all patients present in the self.patients dictionary are returned.
        """
        all_patients = list(self.patients.values())
        return {
            "success": True,
            "data": all_patients
        }

    def get_bill_by_id(self, bill_id: str) -> dict:
        """
        Retrieve bill details (BillInfo) based on the provided bill_id.

        Args:
            bill_id (str): The bill identifier.

        Returns:
            dict: {
                "success": True,
                "data": BillInfo,  # on success
            }
            or
            {
                "success": False,
                "error": str  # if the bill_id does not exist
            }

        Constraints:
            - The provided bill_id must exist in the system.
        """
        bill = self.bills.get(bill_id)
        if bill is None:
            return { "success": False, "error": "Bill does not exist" }
        return { "success": True, "data": bill }

    def list_bills_by_patient(self, patient_id: str) -> dict:
        """
        List all bills (with metadata) associated with the specified patient.

        Args:
            patient_id (str): The ID of the patient whose bills are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[BillInfo]  # List of BillInfo dicts; may be empty if the patient has no bills.
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g., patient not found
            }

        Constraints:
            - The patient_id must exist in the system.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
    
        bills = [
            bill_info for bill_info in self.bills.values()
            if bill_info["patient_id"] == patient_id
        ]
        return {"success": True, "data": bills}

    def get_bill_status(self, bill_id: str) -> dict:
        """
        Retrieve the current status ("unpaid", "partially paid", "paid") of the bill with the given bill_id.

        Args:
            bill_id (str): The unique identifier for the bill.

        Returns:
            dict:
                - On success: { "success": True, "data": <str: status> }
                - On failure: { "success": False, "error": "Bill not found" }

        Constraints:
            - The bill with bill_id must exist in the system.
        """
        bill = self.bills.get(bill_id)
        if not bill:
            return {"success": False, "error": "Bill not found"}

        return {"success": True, "data": bill["status"]}

    def get_bill_outstanding_balance(self, bill_id: str) -> dict:
        """
        Retrieve the outstanding balance amount for a given bill.

        Args:
            bill_id (str): The ID of the bill whose outstanding balance is being queried.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": float  # The outstanding balance amount
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., bill not found
                    }

        Constraints:
            - The bill must exist.
        """
        bill = self.bills.get(bill_id)
        if not bill:
            return {"success": False, "error": "Bill does not exist"}
        return {"success": True, "data": bill["outstanding_balance"]}

    def list_payments_by_bill(self, bill_id: str) -> dict:
        """
        Retrieve all payment records for a specific bill_id.

        Args:
            bill_id (str): The ID of the bill whose payments are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[PaymentInfo],  # list of payments for the bill (may be empty if no payments)
            }
            or
            {
                "success": False,
                "error": str,  # explanation, e.g. "Bill does not exist"
            }

        Constraints:
            - The bill with bill_id must exist.
        """
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill does not exist" }

        payments = [
            payment_info
            for payment_info in self.payments.values()
            if payment_info["bill_id"] == bill_id
        ]

        return { "success": True, "data": payments }

    def get_payment_by_id(self, payment_id: str) -> dict:
        """
        Retrieve payment details for a given payment_id.

        Args:
            payment_id (str): The unique identifier for the payment record.

        Returns:
            dict: {
                "success": True,
                "data": PaymentInfo  # The payment detail, if found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., payment not found)
            }

        Constraints:
            - No additional constraints; simply a read lookup for payment_id.
        """
        payment = self.payments.get(payment_id)
        if payment is not None:
            return {"success": True, "data": payment}

        return {"success": False, "error": "Payment not found"}

    def apply_payment_to_bill(
        self,
        bill_id: str,
        payment_id: str,
        payment_date: str,
        amount: float,
        payment_method: str
    ) -> dict:
        """
        Processes a new payment for a bill. Updates the bill's outstanding balance, adds the payment,
        and changes the bill's status to 'paid' if the outstanding balance reaches zero.

        Args:
            bill_id (str): Bill to which payment applies.
            payment_id (str): Unique identifier for the new payment.
            payment_date (str): Date of payment.
            amount (float): Amount paid (must be > 0 and <= outstanding balance).
            payment_method (str): Payment method (cash, card, etc.).

        Returns:
            dict: Success or error message.

        Constraints:
            - Bill must exist.
            - Payments cannot exceed the outstanding balance.
            - Each payment_id must be unique.
            - After payment, bill's outstanding_balance is reduced by amount.
            - When outstanding_balance is zero, status becomes 'paid'.
        """

        # Check if bill exists
        bill = self.bills.get(bill_id)
        if bill is None:
            return { "success": False, "error": "Bill does not exist." }

        # Validate payment_id uniqueness
        if payment_id in self.payments:
            return { "success": False, "error": "Payment ID already exists." }

        # Validate amount
        if amount <= 0:
            return { "success": False, "error": "Payment amount must be greater than zero." }

        if amount > bill["outstanding_balance"]:
            return { "success": False, "error": "Payment amount exceeds outstanding balance." }

        old_balance = bill["outstanding_balance"]
        new_balance = round(old_balance - amount, 2)

        # Create payment record
        payment_info = {
            "payment_id": payment_id,
            "bill_id": bill_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_method": payment_method
        }
        self.payments[payment_id] = payment_info

        # Update bill
        bill["outstanding_balance"] = new_balance

        # Update bill status
        if new_balance == 0:
            bill["status"] = "paid"
            msg = "Payment applied to bill. Outstanding balance is now zero. Bill marked as paid."
        else:
            # Optionally handle if partial payment transitions bill from "unpaid" to "partially paid"
            bill["status"] = "partially paid" if new_balance < bill["total_amount"] else bill["status"]
            msg = f"Payment applied to bill. Outstanding balance updated to {new_balance}."

        return { "success": True, "message": msg }

    def update_bill_status(self, bill_id: str, new_status: str) -> dict:
        """
        Explicitly set the status of a bill, overriding internal status management.

        Args:
            bill_id (str): The unique identifier of the bill to modify.
            new_status (str): The new status to assign (e.g., 'unpaid', 'partially paid', 'paid').

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Bill status updated to <new_status>." }
                On error (e.g., bill missing):
                    { "success": False, "error": "Bill does not exist." }

        Constraints:
            - Bill must exist to be updated.
            - Explicit status overrides must remain consistent with the bill's current total_amount and outstanding_balance.
            - Expected status is:
                "paid" if outstanding_balance == 0
                "unpaid" if outstanding_balance == total_amount
                "partially paid" otherwise
        """
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill does not exist." }

        bill = self.bills[bill_id]
        if bill["outstanding_balance"] == 0:
            expected_status = "paid"
        elif bill["outstanding_balance"] == bill["total_amount"]:
            expected_status = "unpaid"
        else:
            expected_status = "partially paid"

        if new_status != expected_status:
            return {
                "success": False,
                "error": (
                    f"Status '{new_status}' is inconsistent with bill balances; "
                    f"expected '{expected_status}'."
                ),
            }

        self.bills[bill_id]['status'] = new_status
        return { "success": True, "message": f"Bill status updated to {new_status}." }

    def update_bill_outstanding_balance(self, bill_id: str, new_outstanding_balance: float) -> dict:
        """
        Adjust the outstanding balance of a bill. If the outstanding balance
        becomes zero, also update the bill status to 'paid'.

        Args:
            bill_id (str): ID of the target bill.
            new_outstanding_balance (float): New outstanding balance value.

        Returns:
            dict: {
                "success": True,
                "message": "Outstanding balance updated for Bill <bill_id>."
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Bill must exist.
            - Outstanding balance cannot be negative.
            - Bill status changes to 'paid' if outstanding balance is zero.
        """
        bill = self.bills.get(bill_id)
        if not bill:
            return {"success": False, "error": "Bill does not exist."}
        if new_outstanding_balance < 0:
            return {"success": False, "error": "Outstanding balance cannot be negative."}

        bill["outstanding_balance"] = new_outstanding_balance

        if new_outstanding_balance == 0:
            bill["status"] = "paid"
        else:
            # Optionally update to "unpaid" or "partially paid", here we set to "unpaid"
            bill["status"] = "unpaid"

        return { "success": True, "message": f"Outstanding balance updated for Bill {bill_id}." }

    def create_bill(self, bill_id: str, patient_id: str, total_amount: float, bill_date: str) -> dict:
        """
        Create a new bill entry for a patient.

        Args:
            bill_id (str): Unique identifier for the new bill.
            patient_id (str): Existing patient's ID this bill is for.
            total_amount (float): Total amount billed (>0).
            bill_date (str): Date the bill is issued (format e.g. 'YYYY-MM-DD').

        Returns:
            dict: {
                "success": True,
                "message": "Bill created for patient {patient_id}"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Patient must exist.
            - bill_id must be unique.
            - total_amount must be positive.
            - outstanding_balance initialized to total_amount.
            - status initialized to 'unpaid'.
        """
        # Check bill ID uniqueness
        if bill_id in self.bills:
            return {"success": False, "error": "Bill ID already exists"}

        # Check existence of patient
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        # Validate total_amount
        if not isinstance(total_amount, (int, float)) or total_amount <= 0:
            return {"success": False, "error": "Total amount must be a positive number"}

        # Create bill entry
        new_bill = {
            "bill_id": bill_id,
            "patient_id": patient_id,
            "total_amount": float(total_amount),
            "outstanding_balance": float(total_amount),
            "bill_date": bill_date,
            "status": "unpaid"
        }

        self.bills[bill_id] = new_bill

        return {
            "success": True,
            "message": f"Bill created for patient {patient_id}"
        }

    def delete_payment(self, payment_id: str) -> dict:
        """
        Remove a payment record from the system and update related bill's outstanding balance and status.

        Args:
            payment_id (str): The unique ID of the payment to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Payment <payment_id> deleted and bill adjusted."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Payment to be deleted must exist.
            - Associated bill must exist.
            - Removing the payment increases the bill's outstanding_balance.
            - If the bill status is "paid" and outstanding_balance is increased > 0, set status appropriately.
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return { "success": False, "error": "Payment does not exist" }
    
        bill_id = payment["bill_id"]
        bill = self.bills.get(bill_id)
        if not bill:
            return { "success": False, "error": "Associated bill does not exist" }
    
        amount = payment["amount"]

        # Remove payment
        del self.payments[payment_id]

        # Update bill's outstanding_balance
        bill["outstanding_balance"] += amount

        # Update bill status as needed
        if bill["outstanding_balance"] == 0:
            bill["status"] = "paid"
        elif bill["outstanding_balance"] < bill["total_amount"]:
            bill["status"] = "partially paid"
        else:
            bill["status"] = "unpaid"

        return {
            "success": True,
            "message": f"Payment {payment_id} deleted and bill adjusted."
        }

    def revert_payment(self, payment_id: str) -> dict:
        """
        Revert a specific payment and adjust the associated bill’s outstanding balance and status.

        Args:
            payment_id (str): The payment to revert.

        Returns:
            dict: {
                "success": True,
                "message": "Payment reverted, bill updated"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Payment must exist.
            - Bill associated with payment must exist.
            - After reversion, outstanding_balance should not exceed total_amount.
            - Bill status must be updated: 
                "paid" if outstanding_balance == 0,
                "unpaid" if outstanding_balance == total_amount,
                "partially paid" otherwise.
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return { "success": False, "error": "Payment does not exist" }

        bill_id = payment["bill_id"]
        bill = self.bills.get(bill_id)
        if not bill:
            return { "success": False, "error": "Associated bill does not exist" }

        amount = payment["amount"]

        # Remove the payment
        del self.payments[payment_id]

        # Update the bill's outstanding balance
        new_outstanding = bill["outstanding_balance"] + amount
        # Ensure outstanding_balance does not exceed total_amount
        if new_outstanding > bill["total_amount"]:
            bill["outstanding_balance"] = bill["total_amount"]
        else:
            bill["outstanding_balance"] = new_outstanding

        # Update status
        if bill["outstanding_balance"] == 0:
            bill["status"] = "paid"
        elif bill["outstanding_balance"] == bill["total_amount"]:
            bill["status"] = "unpaid"
        else:
            bill["status"] = "partially paid"

        return { "success": True, "message": "Payment reverted, bill updated" }

    def edit_bill_amount(
        self,
        bill_id: str,
        total_amount: float = None,
        outstanding_balance: float = None
    ) -> dict:
        """
        Modify the total amount and/or outstanding balance of a bill.
        This is an admin-level operation.

        Args:
            bill_id (str): The ID of the bill to modify.
            total_amount (float, optional): The new total amount. Must be non-negative, if provided.
            outstanding_balance (float, optional): The new outstanding balance. Must be non-negative and <= total_amount.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Bill amount and/or outstanding balance updated successfully."}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Bill must exist.
            - Outstanding balance must not exceed total amount or be negative.
            - Total amount must not be negative.
            - Status auto-updates: paid if outstanding_balance==0, unpaid/partially paid otherwise.
        """
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill does not exist." }

        bill = self.bills[bill_id]

        # Only update fields if provided
        new_total_amount = total_amount if total_amount is not None else bill["total_amount"]
        new_outstanding_balance = outstanding_balance if outstanding_balance is not None else bill["outstanding_balance"]

        # Validation
        if new_total_amount < 0:
            return { "success": False, "error": "Total amount cannot be negative." }
        if new_outstanding_balance < 0:
            return { "success": False, "error": "Outstanding balance cannot be negative." }
        if new_outstanding_balance > new_total_amount:
            return { "success": False, "error": "Outstanding balance cannot exceed the total amount." }

        # Apply update
        bill["total_amount"] = new_total_amount
        bill["outstanding_balance"] = new_outstanding_balance

        # Auto-update status
        if new_outstanding_balance == 0:
            bill["status"] = "paid"
        elif new_outstanding_balance < new_total_amount:
            bill["status"] = "partially paid"
        else:
            bill["status"] = "unpaid"

        self.bills[bill_id] = bill

        return { "success": True, "message": "Bill amount and/or outstanding balance updated successfully." }


class HospitalBillingManagementSystem(BaseEnv):
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

    def list_all_patients(self, **kwargs):
        return self._call_inner_tool('list_all_patients', kwargs)

    def get_bill_by_id(self, **kwargs):
        return self._call_inner_tool('get_bill_by_id', kwargs)

    def list_bills_by_patient(self, **kwargs):
        return self._call_inner_tool('list_bills_by_patient', kwargs)

    def get_bill_status(self, **kwargs):
        return self._call_inner_tool('get_bill_status', kwargs)

    def get_bill_outstanding_balance(self, **kwargs):
        return self._call_inner_tool('get_bill_outstanding_balance', kwargs)

    def list_payments_by_bill(self, **kwargs):
        return self._call_inner_tool('list_payments_by_bill', kwargs)

    def get_payment_by_id(self, **kwargs):
        return self._call_inner_tool('get_payment_by_id', kwargs)

    def apply_payment_to_bill(self, **kwargs):
        return self._call_inner_tool('apply_payment_to_bill', kwargs)

    def update_bill_status(self, **kwargs):
        return self._call_inner_tool('update_bill_status', kwargs)

    def update_bill_outstanding_balance(self, **kwargs):
        return self._call_inner_tool('update_bill_outstanding_balance', kwargs)

    def create_bill(self, **kwargs):
        return self._call_inner_tool('create_bill', kwargs)

    def delete_payment(self, **kwargs):
        return self._call_inner_tool('delete_payment', kwargs)

    def revert_payment(self, **kwargs):
        return self._call_inner_tool('revert_payment', kwargs)

    def edit_bill_amount(self, **kwargs):
        return self._call_inner_tool('edit_bill_amount', kwargs)
