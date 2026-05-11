# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
from datetime import date, datetime, timedelta



# Equipment entity (original: "quipme")
class EquipmentInfo(TypedDict):
    equipment_id: str
    name: str
    type: str
    condition: str
    status: str  # "available" | "rented" | "maintenance"

# Customer entity
class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    account_status: str

# RentalTransaction entity (original: "RentalTransactio")
class RentalTransactionInfo(TypedDict):
    transaction_id: str
    customer_id: str
    equipment_id: str
    rental_date: str        # Can use datetime in real implementation
    due_date: str           # Can use datetime in real implementation
    return_date: Optional[str]  # Can be None if not returned
    payment_status: str     # "completed" | "pending" etc.
    transaction_status: str # "active" | "returned" etc.

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Equipment Rental Management System state representation.

        Constraints:
        - Equipment can only be rented if status is "available".
        - Upon return, equipment status is updated from "rented" to "available".
        - A rental transaction's status must be updated to "returned" upon completion of the return.
        - Payment must be completed or pending; late returns may incur additional fees.
        - Due date must be calculated based on rental policy and start date.
        """
        # Equipment inventory: {equipment_id: EquipmentInfo}
        self.equipment: Dict[str, EquipmentInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Rental transactions: {transaction_id: RentalTransactionInfo}
        self.rental_transactions: Dict[str, RentalTransactionInfo] = {}

        # Scenario-local current date in YYYY-MM-DD format.
        self.current_date: Optional[str] = None

    @staticmethod
    def _parse_date_only(value: Optional[str]) -> Optional[date]:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            pass
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    def _get_scenario_current_date(self) -> date:
        explicit_current_date = self._parse_date_only(self.current_date)
        if explicit_current_date is not None:
            return explicit_current_date

        known_dates = []
        for transaction in self.rental_transactions.values():
            if not isinstance(transaction, dict):
                continue
            for field in ("rental_date", "due_date", "return_date"):
                parsed = self._parse_date_only(transaction.get(field))
                if parsed is not None:
                    known_dates.append(parsed)

        if known_dates:
            return max(known_dates)
        return date(1970, 1, 1)

    def get_customer_by_name(self, name: str) -> dict:
        """
        Retrieve all customer profiles with the given customer name.
    
        Args:
            name (str): The customer's name to look up.
    
        Returns:
            dict: 
                - If successful, 
                    {"success": True, "data": List[CustomerInfo]}
                - If customer name is empty,
                    {"success": False, "error": "<reason>"}
            The returned list is empty if no customers with that name are found.

        Constraints:
            - Customer name must not be empty.
            - Multiple customers with the same name may exist; all are returned.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Customer name must not be empty."}

        result = [
            customer_info
            for customer_info in self.customers.values()
            if customer_info["name"] == name
        ]

        return {"success": True, "data": result}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer details using their unique customer_id.

        Args:
            customer_id (str): Unique identifier of the customer.

        Returns:
            dict: 
                - On success: { "success": True, "data": CustomerInfo }
                - On failure: { "success": False, "error": "Customer not found" }

        Constraints:
            - The customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def list_customer_active_rentals(self, customer_id: str) -> dict:
        """
        List all active rental transactions for a given customer.

        Args:
            customer_id (str): ID of the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[RentalTransactionInfo],  # List of active rentals
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The given customer must exist in the system.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}

        active_rentals = [
            transaction
            for transaction in self.rental_transactions.values()
            if transaction["customer_id"] == customer_id and transaction["transaction_status"] == "active"
        ]

        return {"success": True, "data": active_rentals}

    def get_rental_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve detailed information about a rental transaction given its transaction_id.

        Args:
            transaction_id (str): Unique identifier for the rental transaction.

        Returns:
            dict: {
                "success": True,
                "data": RentalTransactionInfo
            }
            OR
            {
                "success": False,
                "error": "Rental transaction not found"
            }

        Constraints:
            - transaction_id must exist in the rental transaction store.
        """
        txn = self.rental_transactions.get(transaction_id)
        if txn is None:
            return { "success": False, "error": "Rental transaction not found" }
        return { "success": True, "data": txn }

    def list_equipment_by_customer(self, customer_id: str) -> dict:
        """
        List all equipment items currently rented by a specific customer, with associated transaction info.

        Args:
            customer_id (str): The ID of the customer to query.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each: {"equipment_info": EquipmentInfo, "transaction_info": RentalTransactionInfo}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only includes rentals with transaction_status == "active".
            - Only includes existing equipment.
            - If customer_id does not exist, returns error.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        result = []
        for transaction in self.rental_transactions.values():
            if transaction["customer_id"] == customer_id and transaction["transaction_status"] == "active":
                equipment_id = transaction["equipment_id"]
                equipment_info = self.equipment.get(equipment_id)
                if equipment_info is not None:
                    result.append({
                        "equipment_info": equipment_info,
                        "transaction_info": transaction
                    })
                else:
                    # Equipment missing from inventory; omit or could include with None
                    continue

        return {"success": True, "data": result}

    def get_equipment_by_id(self, equipment_id: str) -> dict:
        """
        Retrieve information about a specific equipment item by its equipment_id.

        Args:
            equipment_id (str): Unique identifier of the equipment.

        Returns:
            dict: {
                "success": True,
                "data": EquipmentInfo
            }
            or
            {
                "success": False,
                "error": str  # "Equipment not found"
            }

        Constraints:
            - The equipment_id must exist in the system.
        """
        equipment = self.equipment.get(equipment_id)
        if equipment is None:
            return { "success": False, "error": "Equipment not found" }
        return { "success": True, "data": equipment }

    def get_equipment_status(self, equipment_id: str) -> dict:
        """
        Retrieve the current status and condition of an equipment item.

        Args:
            equipment_id (str): Unique identifier for the equipment.

        Returns:
            dict:
                success: True and data containing 'status' and 'condition' if found.
                success: False and 'error' if equipment not found.

        Constraints:
            - The equipment_id must exist in the equipment inventory.
        """
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return { "success": False, "error": "Equipment not found" }
        return {
            "success": True,
            "data": {
                "status": equipment["status"],
                "condition": equipment["condition"]
            }
        }

    def get_rental_transactions_by_equipment(self, equipment_id: str) -> dict:
        """
        Retrieve all rental transactions (history) for a specific equipment item.

        Args:
            equipment_id (str): The unique identifier of the equipment.

        Returns:
            dict: {
                "success": True,
                "data": List[RentalTransactionInfo],  # May be empty if no transactions
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g. equipment not found
            }

        Constraints:
            - The equipment must exist in the system.
        """
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment not found" }

        transactions = [
            tx for tx in self.rental_transactions.values()
            if tx["equipment_id"] == equipment_id
        ]
        return { "success": True, "data": transactions }

    def get_payment_status(self, transaction_id: str) -> dict:
        """
        Retrieve the current payment status for a given rental transaction.

        Args:
            transaction_id (str): The ID of the rental transaction to look up.

        Returns:
            dict: 
              - On success: { "success": True, "data": <payment_status (str)> }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The transaction_id must exist in the system.
        """
        transaction = self.rental_transactions.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Rental transaction not found"}
    
        return {"success": True, "data": transaction["payment_status"]}


    def is_rental_overdue(self, transaction_id: str) -> dict:
        """
        Check if the rental transaction is overdue based on its due date and the current date.

        Args:
            transaction_id (str): ID of the rental transaction to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if overdue, False otherwise
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - The rental transaction must exist.
            - Returned rentals are overdue if and only if return_date > due_date.
            - Active rentals are compared against the scenario-local current date.
            - Date strings must be in ISO format (YYYY-MM-DD).
        """
        rt = self.rental_transactions.get(transaction_id)
        if rt is None:
            return { "success": False, "error": "Rental transaction does not exist" }
    
        due_date = self._parse_date_only(rt.get("due_date"))
        if due_date is None:
            return { "success": False, "error": "Invalid or missing due_date format" }

        return_date = self._parse_date_only(rt.get("return_date"))
        if return_date is not None:
            return { "success": True, "data": return_date > due_date }

        scenario_today = self._get_scenario_current_date()
        is_overdue = scenario_today > due_date

        return { "success": True, "data": is_overdue }


    def return_equipment(self, transaction_id: str, return_date: Optional[str] = None) -> dict:
        """
        Process the return of an equipment:
        - Sets equipment status to "available"
        - Updates corresponding rental transaction's status to "returned"
        - Sets the return_date to specified value or scenario-local current date in ISO format

        Args:
            transaction_id (str): The rental transaction being returned.
            return_date (Optional[str]): Return date as ISO string; if None, use the scenario-local current date.

        Returns:
            dict: 
                On success: { "success": True, "message": "Equipment returned successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
         - Equipment must be currently rented.
         - Transaction must be active and not previously returned.
        """
        # 1. Check transaction exists
        transaction = self.rental_transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Rental transaction not found." }

        # 2. Check transaction status
        if transaction["transaction_status"] != "active":
            return { "success": False, "error": "Rental transaction is not active or already returned." }

        equipment_id = transaction["equipment_id"]
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return { "success": False, "error": "Associated equipment not found." }

        # 3. Check equipment status
        if equipment["status"] != "rented":
            return { "success": False, "error": "Equipment is not currently rented." }

        # 4. Set return date
        if return_date is not None:
            try:
                # Optionally validate the date is ISO format
                datetime.fromisoformat(return_date)
            except Exception:
                return { "success": False, "error": "Invalid return_date format; must be ISO string." }
            set_return_date = return_date
        else:
            set_return_date = self._get_scenario_current_date().isoformat()

        # 5. Update equipment status
        equipment["status"] = "available"

        # 6. Update transaction status and return date
        transaction["transaction_status"] = "returned"
        transaction["return_date"] = set_return_date

        # 7. Save changes (not needed if referencing original dicts)
        self.equipment[equipment_id] = equipment
        self.rental_transactions[transaction_id] = transaction

        return { "success": True, "message": "Equipment returned successfully." }

    def update_equipment_status(self, equipment_id: str, new_status: str) -> dict:
        """
        Change the status of a specific equipment item.

        Args:
            equipment_id (str): The unique identifier for the equipment.
            new_status (str): Status to set ("available", "rented", or "maintenance").

        Returns:
            dict: {
                "success": True,
                "message": "Equipment status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Equipment with the given equipment_id must exist.
            - new_status must be one of "available", "rented", "maintenance".
        """
        allowed_statuses = {"available", "rented", "maintenance"}
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment ID not found." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed: available, rented, maintenance." }
        self.equipment[equipment_id]["status"] = new_status
        return { "success": True, "message": f"Equipment status updated to {new_status}." }

    def update_rental_transaction_status(self, transaction_id: str, new_status: str) -> dict:
        """
        Update the status of a rental transaction (e.g., to 'returned', 'active').

        Args:
            transaction_id (str): The ID of the rental transaction to update.
            new_status (str): The new status to set ('returned', 'active', etc.).

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Rental transaction status updated to <new_status>." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Rental transaction must exist.
            - If new_status is 'returned', the corresponding equipment's status must also be updated to 'available'.
        """
        tx = self.rental_transactions.get(transaction_id)
        if tx is None:
            return { "success": False, "error": "Rental transaction not found." }

        current_status = tx["transaction_status"]
        tx["transaction_status"] = new_status

        # If returned, update equipment status to available
        if new_status == "returned":
            equipment_id = tx["equipment_id"]
            equipment = self.equipment.get(equipment_id)
            if equipment is not None:
                equipment["status"] = "available"
            # If equipment is not found, still allow transaction status change per minimal contract

        return { 
            "success": True, 
            "message": f"Rental transaction status updated to '{new_status}'." 
        }

    def set_rental_return_date(self, transaction_id: str, return_date: str) -> dict:
        """
        Set the return_date for a rental transaction.

        Args:
            transaction_id (str): The rental transaction ID.
            return_date (str): The date the equipment was returned (recommended ISO format).

        Returns:
            dict: {
                "success": True,
                "message": "Return date set successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Transaction must exist.
            - return_date can only be set if not already set for this transaction.
        """
        txn = self.rental_transactions.get(transaction_id)
        if txn is None:
            return { "success": False, "error": "Transaction does not exist." }
        if txn.get("return_date") not in (None, ""):
            return { "success": False, "error": "Return date has already been set for this transaction." }

        txn["return_date"] = return_date
        return { "success": True, "message": "Return date set successfully." }

    def update_payment_status(self, transaction_id: str, payment_status: str) -> dict:
        """
        Change the payment status for a given rental transaction.

        Args:
            transaction_id (str): The ID of the rental transaction to update.
            payment_status (str): The new payment status (e.g., 'completed', 'pending', 'late_fee_applied').

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation description
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Transaction must exist.
            - Payment status is changed to the provided value; valid statuses include 'completed', 'pending', or values reflecting late fees.
        """
        transaction = self.rental_transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Transaction not found" }

        transaction['payment_status'] = payment_status
        self.rental_transactions[transaction_id] = transaction
        return {
            "success": True,
            "message": f"Payment status updated for transaction {transaction_id}"
        }

    def charge_late_fee(self, transaction_id: str, late_fee_description: str = "late_fee_due") -> dict:
        """
        Apply an additional late fee to a rental transaction if the equipment was returned after its due date.
        This updates the payment_status to reflect the outstanding late fee.

        Args:
            transaction_id (str): ID of the rental transaction to update.
            late_fee_description (str): Description or flag to indicate late fee in payment_status. Defaults to "late_fee_due".

        Returns:
            dict: {
                "success": True,
                "message": "Late fee charged to transaction"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
        - Transaction must exist.
        - Transaction must have return_date set.
        - Only apply late fee if return_date > due_date.
        - Updates payment_status to indicate late fee due ("late_fee_due").
        """
        transaction = self.rental_transactions.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction does not exist."}

        return_date = transaction.get("return_date")
        due_date = transaction.get("due_date")
        if not return_date:
            return {"success": False, "error": "Equipment has not been returned yet; cannot charge late fee."}

        # Assume date strings in comparable format (e.g., "YYYY-MM-DD" or ISO).
        if return_date <= due_date:
            return {"success": False, "error": "Return was not overdue; late fee not applicable."}

        # Optionally check if already charged; update or overwrite payment_status.
        transaction["payment_status"] = late_fee_description

        self.rental_transactions[transaction_id] = transaction

        return {"success": True, "message": "Late fee charged to transaction."}

    def create_rental_transaction(
        self,
        transaction_id: str,
        customer_id: str,
        equipment_id: str,
        rental_date: str,
        due_date: str,
        payment_status: str = "pending"
    ) -> dict:
        """
        Create a new rental transaction linking a customer with equipment.
        Updates both equipment and transaction status accordingly.

        Args:
            transaction_id (str): Unique identifier for the transaction.
            customer_id (str): ID of the customer.
            equipment_id (str): ID of the equipment to rent.
            rental_date (str): Rental start date/time.
            due_date (str): Due date/time for the rental.
            payment_status (str): Optional, defaults to "pending".

        Returns:
            dict: {
                "success": True,
                "message": "Rental transaction created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
        - Equipment must exist and be "available".
        - Customer must exist.
        - Transaction ID must not already exist.
        - Upon success, equipment status set to "rented", transaction status set to "active".
        """
        # Check if transaction_id is unique
        if transaction_id in self.rental_transactions:
            return {"success": False, "error": "Transaction ID already exists."}

        # Lookup equipment
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return {"success": False, "error": "Equipment not found."}
        if equipment["status"] != "available":
            return {"success": False, "error": "Equipment not available for rental."}

        # Lookup customer
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer not found."}

        # Create rental transaction
        rental_transaction: RentalTransactionInfo = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "equipment_id": equipment_id,
            "rental_date": rental_date,
            "due_date": due_date,
            "return_date": None,
            "payment_status": payment_status,
            "transaction_status": "active"
        }
        self.rental_transactions[transaction_id] = rental_transaction

        # Update equipment status to "rented"
        equipment["status"] = "rented"
        self.equipment[equipment_id] = equipment

        return {"success": True, "message": "Rental transaction created successfully."}

    def delete_rental_transaction(self, transaction_id: str) -> dict:
        """
        Remove a rental transaction from the system (admin action).
    
        Args:
            transaction_id (str): The ID of the rental transaction to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Rental transaction deleted successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., transaction not found)
            }
    
        Constraints:
            - Only valid transaction IDs may be deleted.
            - This is an admin operation; business logic constraints (equipment status, payments) are not applied here.
        """
        if transaction_id not in self.rental_transactions:
            return { "success": False, "error": "Rental transaction not found." }
    
        del self.rental_transactions[transaction_id]
        return { "success": True, "message": "Rental transaction deleted successfully." }


    def set_due_date(self, transaction_id: str, rental_period_days: int = 7) -> dict:
        """
        Calculate and set the due_date for a rental transaction, based on rental policy and
        the rental_date.

        Args:
            transaction_id (str): The ID of the rental transaction.
            rental_period_days (int, optional): The number of days for the rental period
                (default is 7).

        Returns:
            dict: {
                "success": True,
                "message": "Due date set to <due_date>"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Transaction must exist.
            - rental_date must be present and in YYYY-MM-DD format.
            - Due date must be calculated as rental_date + rental_period_days.
        """
        if transaction_id not in self.rental_transactions:
            return { "success": False, "error": "Rental transaction does not exist" }

        transaction = self.rental_transactions[transaction_id]
        rental_date_str = transaction.get("rental_date")
        if not rental_date_str:
            return { "success": False, "error": "Rental date not set for this transaction" }

        try:
            rental_date = datetime.strptime(rental_date_str, "%Y-%m-%d")
        except ValueError:
            return { "success": False, "error": "Invalid rental date format; expected YYYY-MM-DD" }

        due_date = rental_date + timedelta(days=rental_period_days)
        due_date_str = due_date.strftime("%Y-%m-%d")

        transaction["due_date"] = due_date_str
        self.rental_transactions[transaction_id] = transaction

        return { "success": True, "message": f"Due date set to {due_date_str}" }


class EquipmentRentalManagementSystem(BaseEnv):
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

    def get_customer_by_name(self, **kwargs):
        return self._call_inner_tool('get_customer_by_name', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_customer_active_rentals(self, **kwargs):
        return self._call_inner_tool('list_customer_active_rentals', kwargs)

    def get_rental_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_rental_transaction_by_id', kwargs)

    def list_equipment_by_customer(self, **kwargs):
        return self._call_inner_tool('list_equipment_by_customer', kwargs)

    def get_equipment_by_id(self, **kwargs):
        return self._call_inner_tool('get_equipment_by_id', kwargs)

    def get_equipment_status(self, **kwargs):
        return self._call_inner_tool('get_equipment_status', kwargs)

    def get_rental_transactions_by_equipment(self, **kwargs):
        return self._call_inner_tool('get_rental_transactions_by_equipment', kwargs)

    def get_payment_status(self, **kwargs):
        return self._call_inner_tool('get_payment_status', kwargs)

    def is_rental_overdue(self, **kwargs):
        return self._call_inner_tool('is_rental_overdue', kwargs)

    def return_equipment(self, **kwargs):
        return self._call_inner_tool('return_equipment', kwargs)

    def update_equipment_status(self, **kwargs):
        return self._call_inner_tool('update_equipment_status', kwargs)

    def update_rental_transaction_status(self, **kwargs):
        return self._call_inner_tool('update_rental_transaction_status', kwargs)

    def set_rental_return_date(self, **kwargs):
        return self._call_inner_tool('set_rental_return_date', kwargs)

    def update_payment_status(self, **kwargs):
        return self._call_inner_tool('update_payment_status', kwargs)

    def charge_late_fee(self, **kwargs):
        return self._call_inner_tool('charge_late_fee', kwargs)

    def create_rental_transaction(self, **kwargs):
        return self._call_inner_tool('create_rental_transaction', kwargs)

    def delete_rental_transaction(self, **kwargs):
        return self._call_inner_tool('delete_rental_transaction', kwargs)

    def set_due_date(self, **kwargs):
        return self._call_inner_tool('set_due_date', kwargs)
