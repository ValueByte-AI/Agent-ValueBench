# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    name: str
    role: str  # tenant, landlord, property_manager
    contact_info: str

class PropertyInfo(TypedDict):
    property_id: str
    address: str
    landlord_id: str

class PaymentInfo(TypedDict):
    payment_id: str
    tenant_id: str
    property_id: str
    amount: float
    date: str
    status: str  # pending, confirmed, refunded
    method: str

class RecurringChargeInfo(TypedDict):
    charge_id: str
    tenant_id: str
    property_id: str
    amount: float
    frequency: str
    next_due_date: str
    active_sta: bool  # active status; assumed boolean

class DisputeInfo(TypedDict):
    dispute_id: str
    payment_id: str
    tenant_id: str
    status: str  # open, resolved, rejected
    reason: str
    created_da: str

class RefundInfo(TypedDict):
    fund_id: str
    payment_id: str
    amount: float
    status: str  # requested, approved, processed, rejected
    request_date: str
    process_da: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Properties: {property_id: PropertyInfo}
        self.properties: Dict[str, PropertyInfo] = {}

        # Payments: {payment_id: PaymentInfo}
        self.payments: Dict[str, PaymentInfo] = {}

        # Recurring Charges: {charge_id: RecurringChargeInfo}
        self.recurring_charges: Dict[str, RecurringChargeInfo] = {}

        # Disputes: {dispute_id: DisputeInfo}
        self.disputes: Dict[str, DisputeInfo] = {}

        # Refunds: {fund_id: RefundInfo}
        self.refunds: Dict[str, RefundInfo] = {}

        # Constraint rules:
        # - Each payment is associated with exactly one tenant and one property.
        # - Refunds can only be processed for confirmed payments.
        # - Each refund must reference the original payment.
        # - Disputes must reference a specific payment and can be raised only by the tenant who made the payment.
        # - Only active recurring charges are scheduled for future payments.
        # - Payment status must update when a refund is processed.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Fetch user info by user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            } if the user exists,
            or
            {
                "success": False,
                "error": "User not found"
            } if the user does not exist.

        Constraints:
            - The user ID must be present in the system's users.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_role(self, role: str) -> dict:
        """
        List all users with the specified role.

        Args:
            role (str): The role to filter by. Must be 'tenant', 'landlord', or 'property_manager'.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[UserInfo]  # May be empty if no users with that role
                    }
                On failure (invalid role):
                    {
                        "success": False,
                        "error": str  # Explanation of the error
                    }

        Constraints:
            - role must be one of 'tenant', 'landlord', 'property_manager'
        """
        allowed_roles = {"tenant", "landlord", "property_manager"}
        if role not in allowed_roles:
            return {"success": False, "error": "Invalid role. Must be 'tenant', 'landlord', or 'property_manager'."}
        result = [user for user in self.users.values() if user["role"] == role]
        return {"success": True, "data": result}

    def get_property_by_id(self, property_id: str) -> dict:
        """
        Retrieve property details by its unique property_id.

        Args:
            property_id (str): The unique identifier of the property.

        Returns:
            dict: {
                "success": True,
                "data": PropertyInfo,  # Property details if found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error if property_id not found
            }

        Constraints:
            - property_id must exist in the system.
        """
        property_info = self.properties.get(property_id)
        if not property_info:
            return {"success": False, "error": "Property not found"}

        return {"success": True, "data": property_info}

    def list_properties_by_landlord(self, landlord_id: str) -> dict:
        """
        List all properties for the specified landlord.

        Args:
            landlord_id (str): The unique identifier of the landlord.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PropertyInfo]  # May be empty if landlord has no properties
                }
                or
                {
                    "success": False,
                    "error": str  # Reason, e.g. landlord not found or not a landlord
                }
        Constraints:
            - Landlord_id must belong to an existing user whose role is 'landlord'.
        """
        user = self.users.get(landlord_id)
        if not user or user.get("role") != "landlord":
            return {"success": False, "error": "Landlord not found or user is not a landlord"}

        result = [
            prop for prop in self.properties.values()
            if prop.get("landlord_id") == landlord_id
        ]
        return {"success": True, "data": result}

    def get_payment_by_id(self, payment_id: str) -> dict:
        """
        Retrieve payment details by payment_id.

        Args:
            payment_id (str): The unique identifier of the payment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PaymentInfo  # payment details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Payment not found"
                    }

        Constraints:
            - No permission or association check is performed; purely retrieval based on ID.
        """
        payment = self.payments.get(payment_id)
        if payment is None:
            return { "success": False, "error": "Payment not found" }
        return { "success": True, "data": payment }

    def list_payments_by_tenant(self, tenant_id: str) -> dict:
        """
        List all payments associated with the specified tenant.

        Args:
            tenant_id (str): The unique identifier of the tenant.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[PaymentInfo]  # List of payments for this tenant. May be empty if none found.
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., tenant not found, not a tenant)
                    }
        Constraints:
            - tenant_id must exist in self.users and have role 'tenant'.
            - Only payments where PaymentInfo['tenant_id'] == tenant_id are returned.
        """
        user = self.users.get(tenant_id)
        if not user:
            return {"success": False, "error": "Tenant ID does not exist"}
        if user.get("role") != "tenant":
            return {"success": False, "error": "User is not a tenant"}

        payments = [
            payment for payment in self.payments.values()
            if payment["tenant_id"] == tenant_id
        ]
        return {"success": True, "data": payments}

    def get_payment_status(self, payment_id: str) -> dict:
        """
        Retrieve the current status of a payment (pending, confirmed, refunded).

        Args:
            payment_id (str): The unique identifier of the payment.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "payment_id": str,
                    "status": str
                }
            }
            or {
                "success": False,
                "error": str
            }
        Constraints:
            - The payment_id must exist in the system.
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}

        return {
            "success": True,
            "data": {
                "payment_id": payment_id,
                "status": payment["status"]
            }
        }

    def list_refunds_by_payment(self, payment_id: str) -> dict:
        """
        List all refund records (RefundInfo) linked to a given payment_id.

        Args:
            payment_id (str): The payment identifier for which refunds are queried.

        Returns:
            dict: {
                "success": True,
                "data": List[RefundInfo]  # All refunds referencing this payment (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. payment does not exist
            }

        Constraints:
            - payment_id must reference an existing payment.
            - Only refunds referencing the payment_id are returned.
        """
        if payment_id not in self.payments:
            return {"success": False, "error": "Payment not found"}

        refunds = [
            refund_info for refund_info in self.refunds.values()
            if refund_info["payment_id"] == payment_id
        ]

        return {"success": True, "data": refunds}

    def get_refund_by_id(self, fund_id: str) -> dict:
        """
        Retrieve the details and status of a refund by fund_id.

        Args:
            fund_id (str): The unique identifier of the refund.

        Returns:
            dict: {
                "success": True,
                "data": RefundInfo
            }
            or
            {
                "success": False,
                "error": str  # "Refund not found"
            }

        Constraints:
            - Refund must exist with the provided fund_id.
        """
        refund = self.refunds.get(fund_id)
        if refund is None:
            return {"success": False, "error": "Refund not found"}
        return {"success": True, "data": refund}

    def get_recurring_charge_by_id(self, charge_id: str) -> dict:
        """
        Retrieve the details of a specific recurring charge arrangement by its ID.

        Args:
            charge_id (str): Unique identifier of the recurring charge.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": RecurringChargeInfo}
                On failure (not found):
                    {"success": False, "error": "Recurring charge not found"}
        Constraints:
            - The recurring charge must exist in the system.
        """
        if charge_id not in self.recurring_charges:
            return {"success": False, "error": "Recurring charge not found"}
        return {"success": True, "data": self.recurring_charges[charge_id]}

    def list_active_recurring_charges_by_tenant(self, tenant_id: str) -> dict:
        """
        List all active recurring charges for a tenant.

        Args:
            tenant_id (str): The unique ID of the tenant.

        Returns:
            dict: {
                "success": True,
                "data": List[RecurringChargeInfo],  # May be empty if none found
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the error (e.g., tenant not found)
            }

        Constraints:
            - Only recurring charges with active_sta == True are returned.
            - tenant_id must correspond to a user of role 'tenant'.
        """
        user = self.users.get(tenant_id)
        if not user:
            return {"success": False, "error": "Tenant not found"}
        if user.get("role") != "tenant":
            return {"success": False, "error": "User is not a tenant"}

        active_charges = [
            charge for charge in self.recurring_charges.values()
            if charge["tenant_id"] == tenant_id and charge.get("active_sta", False)
        ]
        return {"success": True, "data": active_charges}

    def list_disputes_by_payment(self, payment_id: str) -> dict:
        """
        List all disputes related to a specific payment.

        Args:
            payment_id (str): The ID of the payment whose disputes should be listed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[DisputeInfo]  # All disputes referencing this payment
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., payment not found
                    }
        Constraints:
            - payment_id must exist in the system.
        """
        if payment_id not in self.payments:
            return { "success": False, "error": "Payment ID does not exist." }

        result = [
            dispute for dispute in self.disputes.values()
            if dispute['payment_id'] == payment_id
        ]
        return { "success": True, "data": result }

    def get_dispute_by_id(self, dispute_id: str) -> dict:
        """
        Retrieve details for a specific dispute by its dispute_id.

        Args:
            dispute_id (str): The unique identifier of the dispute to retrieve.

        Returns:
            dict:
                On success: {"success": True, "data": DisputeInfo}
                On failure: {"success": False, "error": "Dispute not found"}

        Constraints:
            - Dispute must exist in the system.
            - No permission checks are performed; this is a direct lookup.
        """
        dispute_info = self.disputes.get(dispute_id)
        if not dispute_info:
            return {"success": False, "error": "Dispute not found"}
        return {"success": True, "data": dispute_info}

    def create_refund_request(self, fund_id: str, payment_id: str, amount: float, request_date: str) -> dict:
        """
        Create a new refund record for a confirmed payment (status set to 'requested').

        Args:
            fund_id (str): Unique refund record identifier.
            payment_id (str): The payment to refund.
            amount (float): The refund amount (should be <= original payment).
            request_date (str): Date of refund request.

        Returns:
            dict:
                { "success": True, "message": "Refund request created." }
                or
                { "success": False, "error": <reason> }

        Constraints:
        - Refunds can only be processed for confirmed payments.
        - Each refund must reference an original payment.
        - Amount must be positive and less than or equal to original payment amount.
        - Refund fund_id must be unique.
        """

        # Check: unique refund id
        if fund_id in self.refunds:
            return { "success": False, "error": "Refund ID already exists." }

        # Check: payment exists
        payment = self.payments.get(payment_id)
        if payment is None:
            return { "success": False, "error": "Referenced payment does not exist." }

        # Check: payment must be confirmed
        if payment["status"] != "confirmed":
            return { "success": False, "error": "Refund can be requested only for confirmed payments." }

        # Amount must be positive and <= payment amount
        if not (0 < amount <= payment["amount"]):
            return { "success": False, "error": "Invalid refund amount." }

        # If multiple refunds per payment are not allowed, uncomment next:
        # if any(refund["payment_id"] == payment_id and refund["status"] in ("requested", "approved", "processed") for refund in self.refunds.values()):
        #     return { "success": False, "error": "A refund is already requested or in process for this payment." }

        # Create the refund info
        refund_info = {
            "fund_id": fund_id,
            "payment_id": payment_id,
            "amount": amount,
            "status": "requested",
            "request_date": request_date,
            "process_da": ""   # Not yet processed
        }
        self.refunds[fund_id] = refund_info

        return { "success": True, "message": "Refund request created." }

    def update_refund_status(self, fund_id: str, new_status: str) -> dict:
        """
        Change the status of a refund (e.g., to approved, processed, or rejected).
        If new_status is "processed", the associated payment's status will also be updated to "refunded".

        Args:
            fund_id (str): The ID of the refund to update.
            new_status (str): The new status to set for the refund ("requested", "approved", "processed", "rejected").

        Returns:
            dict: {
                "success": True,
                "message": "Refund status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Refund must exist.
            - new_status must be one of: "requested", "approved", "processed", "rejected".
            - If new_status is "processed", update the related payment's status to "refunded" (if payment present).
        """
        allowed_statuses = {"requested", "approved", "processed", "rejected"}
        refund = self.refunds.get(fund_id)
        if not refund:
            return { "success": False, "error": "Refund not found." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid refund status: {new_status}." }

        refund["status"] = new_status

        if new_status == "processed":
            payment_id = refund.get("payment_id")
            payment = self.payments.get(payment_id)
            if payment:
                payment["status"] = "refunded"

        return { "success": True, "message": f"Refund status updated to {new_status}." }

    def update_payment_status(self, payment_id: str, new_status: str) -> dict:
        """
        Change the status of a payment (e.g., to refunded after a refund is processed).

        Args:
            payment_id (str): The unique identifier of the payment to update.
            new_status (str): The new status for the payment. Must be one of 'pending', 'confirmed', 'refunded'.

        Returns:
            dict: 
                { "success": True, "message": "Payment status updated to <new_status>" }
                or
                { "success": False, "error": "Payment not found" }
                or
                { "success": False, "error": "Invalid status value: <new_status>" }

        Constraints:
            - Only accepts 'pending', 'confirmed', or 'refunded' as valid new statuses.
            - Payment must exist.
        """
        allowed_statuses = {'pending', 'confirmed', 'refunded'}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status value: {new_status}" }
        if payment_id not in self.payments:
            return { "success": False, "error": "Payment not found" }

        self.payments[payment_id]['status'] = new_status
        return { "success": True, "message": f"Payment status updated to {new_status}" }

    def create_dispute(self, payment_id: str, tenant_id: str, reason: str) -> dict:
        """
        File a new dispute for a specific payment. Only the tenant who made the payment can create the dispute.

        Args:
            payment_id (str): The ID of the payment to dispute.
            tenant_id (str): The ID of the tenant creating the dispute.
            reason (str): The textual reason for the dispute.

        Returns:
            dict: {
                "success": True,
                "message": "Dispute created successfully",
                "dispute_id": <dispute_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Payment must exist.
            - Tenant must exist and be of 'tenant' role.
            - Only the tenant who made the payment can create the dispute.
            - Reason must be provided.
        """
        # Check payment existence
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment does not exist"}

        # Check tenant existence and role
        tenant = self.users.get(tenant_id)
        if not tenant or tenant.get("role") != "tenant":
            return {"success": False, "error": "Tenant not found or invalid role"}

        # Ensure the tenant is the one who made the payment
        if payment["tenant_id"] != tenant_id:
            return {"success": False, "error": "Dispute can only be raised by the tenant who made the payment"}

        # Check that a reason is given
        if not reason or not reason.strip():
            return {"success": False, "error": "Dispute reason cannot be empty"}

        # Create unique dispute ID (simple auto-increment)
        dispute_id = f"disp_{len(self.disputes) + 1}"

        # Creation date (placeholder, ideally current date string)
        created_da = datetime.utcnow().isoformat()

        dispute_info = {
            "dispute_id": dispute_id,
            "payment_id": payment_id,
            "tenant_id": tenant_id,
            "status": "open",
            "reason": reason,
            "created_da": created_da
        }

        self.disputes[dispute_id] = dispute_info

        return {
            "success": True,
            "message": "Dispute created successfully",
            "dispute_id": dispute_id
        }

    def resolve_dispute(self, dispute_id: str, status: str) -> dict:
        """
        Change the status of a specified dispute to 'resolved' or 'rejected'.

        Args:
            dispute_id (str): Unique identifier of the dispute.
            status (str): Must be 'resolved' or 'rejected'.

        Returns:
            dict: 
                On success: { "success": True, "message": "Dispute <id> status updated to <status>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Dispute must exist.
            - status must be either 'resolved' or 'rejected'.
        """
        if dispute_id not in self.disputes:
            return { "success": False, "error": f"Dispute with id {dispute_id} does not exist" }
        if status not in ("resolved", "rejected"):
            return { "success": False, "error": "Status must be either 'resolved' or 'rejected'" }
        self.disputes[dispute_id]["status"] = status
        return { "success": True, "message": f"Dispute {dispute_id} status updated to {status}" }

    def activate_recurring_charge(self, charge_id: str) -> dict:
        """
        Set the status of a recurring charge to active (True) by charge_id.

        Args:
            charge_id (str): Unique identifier of the recurring charge.

        Returns:
            dict: {
                "success": True,
                "message": "Recurring charge <charge_id> activated."
            }
            or
            {
                "success": False,
                "error": "Recurring charge with ID <charge_id> does not exist."
            }
        
        Constraints:
            - The recurring charge must exist.
            - The operation is idempotent: mark as active regardless of current state.
        """
        if charge_id not in self.recurring_charges:
            return {
                "success": False,
                "error": f"Recurring charge with ID {charge_id} does not exist."
            }
        self.recurring_charges[charge_id]["active_sta"] = True
        return {
            "success": True,
            "message": f"Recurring charge {charge_id} activated."
        }

    def deactivate_recurring_charge(self, charge_id: str) -> dict:
        """
        Deactivate (set inactive) the recurring charge identified by charge_id.

        Args:
            charge_id (str): The unique identifier of the recurring charge.

        Returns:
            dict: 
              - {"success": True, "message": "Recurring charge deactivated successfully."}
                if deactivation (or was already inactive)
              - {"success": False, "error": "Recurring charge not found."}
                if the charge does not exist

        Constraints:
            - charge_id must exist in recurring_charges.
            - Operation is idempotent: already inactive counts as successful deactivation.
        """
        rc = self.recurring_charges.get(charge_id)
        if not rc:
            return {"success": False, "error": "Recurring charge not found."}

        if not rc["active_sta"]:
            # Already inactive
            return {"success": True, "message": "Recurring charge deactivated successfully."}
    
        rc["active_sta"] = False
        return {"success": True, "message": "Recurring charge deactivated successfully."}

    def process_refund(self, fund_id: str) -> dict:
        """
        Complete a refund for a payment:
        - Moves the refund status to 'processed'.
        - Updates the related payment status to 'refunded'.
    
        Args:
            fund_id (str): The ID of the refund to process.
    
        Returns:
            dict: {
                "success": True,
                "message": "Refund processed, payment marked as refunded."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Refund must exist and be in 'approved' status.
            - Refund must reference an existing payment.
            - Payment must be in 'confirmed' status.
            - When a refund is processed, the payment status must also be updated to 'refunded'.
        """
        refund = self.refunds.get(fund_id)
        if not refund:
            return {"success": False, "error": "Refund not found."}

        if refund["status"] != "approved":
            return {"success": False, "error": "Refund is not in 'approved' status and cannot be processed."}

        payment_id = refund["payment_id"]
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Original payment referenced by refund does not exist."}
    
        if payment["status"] != "confirmed":
            return {
                "success": False,
                "error": "Refunds can only be processed for payments with status 'confirmed'."
            }

        # Update refund status to 'processed'
        refund["status"] = "processed"
        # Optionally, update process_da to current date/time (not implemented here)

        # Update payment status to 'refunded'
        payment["status"] = "refunded"
    
        # Persist the changes
        self.refunds[fund_id] = refund
        self.payments[payment_id] = payment

        return {
            "success": True,
            "message": "Refund processed, payment marked as refunded."
        }

    def update_recurring_charge_due_date(self, charge_id: str, new_due_date: str) -> dict:
        """
        Update the next due date for a recurring charge.

        Args:
            charge_id (str): The unique identifier for the recurring charge to be updated.
            new_due_date (str): The new due date string to set (date format as used in the environment).

        Returns:
            dict:
                - On success: {"success": True, "message": "Next due date updated for charge <charge_id>."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - The specified recurring charge must exist in the system.
            - new_due_date should be a non-empty string.
        """
        if not charge_id or charge_id not in self.recurring_charges:
            return {"success": False, "error": "Recurring charge does not exist."}
        if not new_due_date or not isinstance(new_due_date, str) or not new_due_date.strip():
            return {"success": False, "error": "Invalid or missing new due date."}
        self.recurring_charges[charge_id]["next_due_date"] = new_due_date.strip()
        return {
            "success": True,
            "message": f"Next due date updated for charge {charge_id}."
        }


class OnlineRentPaymentManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_role(self, **kwargs):
        return self._call_inner_tool('get_user_by_role', kwargs)

    def get_property_by_id(self, **kwargs):
        return self._call_inner_tool('get_property_by_id', kwargs)

    def list_properties_by_landlord(self, **kwargs):
        return self._call_inner_tool('list_properties_by_landlord', kwargs)

    def get_payment_by_id(self, **kwargs):
        return self._call_inner_tool('get_payment_by_id', kwargs)

    def list_payments_by_tenant(self, **kwargs):
        return self._call_inner_tool('list_payments_by_tenant', kwargs)

    def get_payment_status(self, **kwargs):
        return self._call_inner_tool('get_payment_status', kwargs)

    def list_refunds_by_payment(self, **kwargs):
        return self._call_inner_tool('list_refunds_by_payment', kwargs)

    def get_refund_by_id(self, **kwargs):
        return self._call_inner_tool('get_refund_by_id', kwargs)

    def get_recurring_charge_by_id(self, **kwargs):
        return self._call_inner_tool('get_recurring_charge_by_id', kwargs)

    def list_active_recurring_charges_by_tenant(self, **kwargs):
        return self._call_inner_tool('list_active_recurring_charges_by_tenant', kwargs)

    def list_disputes_by_payment(self, **kwargs):
        return self._call_inner_tool('list_disputes_by_payment', kwargs)

    def get_dispute_by_id(self, **kwargs):
        return self._call_inner_tool('get_dispute_by_id', kwargs)

    def create_refund_request(self, **kwargs):
        return self._call_inner_tool('create_refund_request', kwargs)

    def update_refund_status(self, **kwargs):
        return self._call_inner_tool('update_refund_status', kwargs)

    def update_payment_status(self, **kwargs):
        return self._call_inner_tool('update_payment_status', kwargs)

    def create_dispute(self, **kwargs):
        return self._call_inner_tool('create_dispute', kwargs)

    def resolve_dispute(self, **kwargs):
        return self._call_inner_tool('resolve_dispute', kwargs)

    def activate_recurring_charge(self, **kwargs):
        return self._call_inner_tool('activate_recurring_charge', kwargs)

    def deactivate_recurring_charge(self, **kwargs):
        return self._call_inner_tool('deactivate_recurring_charge', kwargs)

    def process_refund(self, **kwargs):
        return self._call_inner_tool('process_refund', kwargs)

    def update_recurring_charge_due_date(self, **kwargs):
        return self._call_inner_tool('update_recurring_charge_due_date', kwargs)

