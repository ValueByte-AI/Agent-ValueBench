# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import time
from typing import List, Dict, Any
from datetime import datetime
import uuid
from typing import Any



class TransactionInfo(TypedDict):
    transaction_id: str
    timestamp: str
    amount: float
    customer_id: str
    merchant_id: str
    payment_method: str
    risk_score: float
    flag_status: str
    resolution_status: str
    assessment_reason: str

class FlagInfo(TypedDict):
    flag_id: str
    transaction_id: str
    flag_type: str
    created_at: str
    description: str

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    risk_profile: str

class ResolutionInfo(TypedDict):
    transaction_id: str
    reviewed_by: str
    status: str
    reviewed_at: str
    comments_audit_trail: str  # fieldname fixed from 'comments/audit_trail'

class _GeneratedEnvImpl:
    def __init__(self):
        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}
        # Flags: {flag_id: FlagInfo}
        self.flags: Dict[str, FlagInfo] = {}
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}
        # Resolutions: {transaction_id: ResolutionInfo}
        self.resolutions: Dict[str, ResolutionInfo] = {}
        
        # Constraints:
        # - Only transactions with flag_status = "flagged" may be batch approved or reviewed for fraud.
        # - Resolution status transitions must be auditable (logged actions).
        # - Each flag must reference a valid transaction.
        # - Approval of a transaction updates both its resolution_status and possibly its flag_status.
        # - Any change to a transaction’s status must be timestamped and linked to a user or agent.

    def get_flagged_transactions(self) -> dict:
        """
        Retrieve all transactions that currently have flag_status set to 'flagged'.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TransactionInfo],  # May be empty if no flagged transactions
                }
        """
        flagged = [
            tx for tx in self.transactions.values()
            if tx.get("flag_status") == "flagged"
        ]
        return { "success": True, "data": flagged }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve the full details of a transaction given its transaction_id.

        Args:
            transaction_id (str): The unique identifier for the transaction.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo,  # Full transaction info dict
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. transaction not found
            }

        Constraints:
            - None (simple retrieval, no permission or audit logging needed).
        """
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            return { "success": False, "error": "Transaction not found" }

        return { "success": True, "data": transaction }

    def get_flags_for_transaction(self, transaction_id: str) -> dict:
        """
        Retrieve all flags associated with a given transaction.

        Args:
            transaction_id (str): The ID of the transaction to lookup flags for.

        Returns:
            dict: 
                - If successful: { "success": True, "data": List[FlagInfo] }
                - If failure:    { "success": False, "error": "Transaction not found" }

        Constraints:
            - Transaction must exist in the system.
            - All returned flags reference the specified transaction.
        """
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction not found" }
        flags_for_transaction = [
            flag_info for flag_info in self.flags.values()
            if flag_info["transaction_id"] == transaction_id
        ]
        return { "success": True, "data": flags_for_transaction }

    def get_flag_by_id(self, flag_id: str) -> dict:
        """
        Retrieve flag information given a flag_id.

        Args:
            flag_id (str): The identifier of the flag.

        Returns:
            dict: 
                - If found:
                    {"success": True, "data": FlagInfo}
                - If not found:
                    {"success": False, "error": "Flag not found"}

        Constraints:
            - The flag_id must exist in the system.
        """
        if flag_id not in self.flags:
            return {"success": False, "error": "Flag not found"}
        return {"success": True, "data": self.flags[flag_id]}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer information given a customer_id.

        Args:
            customer_id (str): The unique customer identifier to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CustomerInfo
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Customer not found"
                    }
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": self.customers[customer_id] }

    def get_resolution_by_transaction(self, transaction_id: str) -> dict:
        """
        Retrieve the resolution/audit trail for a given transaction.

        Args:
            transaction_id (str): The unique transaction identifier for which to fetch resolution info.

        Returns:
            dict:
                - If resolution exists:
                    {"success": True, "data": ResolutionInfo}
                - If resolution does not exist:
                    {"success": False, "error": "No resolution found for transaction"}
                
        Constraints:
            - Resolution info must reference a valid transaction_id.
        """
        resolution = self.resolutions.get(transaction_id)
        if resolution is None:
            return {
                "success": False,
                "error": "No resolution found for transaction"
            }
        return {
            "success": True,
            "data": resolution
        }

    def list_transactions_by_status(self, status: str) -> dict:
        """
        List all transactions filtered by their resolution_status.

        Args:
            status (str): The resolution_status value to filter transactions by.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo], # List of matching transactions (may be empty)
            }
        """
        result = [
            txn for txn in self.transactions.values()
            if txn["resolution_status"] == status
        ]
        return { "success": True, "data": result }

    def get_transactions_for_customer(self, customer_id: str) -> dict:
        """
        Retrieve all transactions associated with the specified customer_id.

        Args:
            customer_id (str): The customer identifier.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TransactionInfo],  # May be empty if no transactions found
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (invalid input)
                }

        Constraints:
            - No check for existence of customer in self.customers. Returns all matching transactions.
            - No modifications/auditing required for queries.
        """
        if not isinstance(customer_id, str) or not customer_id:
            return { "success": False, "error": "customer_id must be a non-empty string" }
    
        txns = [
            txn for txn in self.transactions.values()
            if txn.get("customer_id") == customer_id
        ]
        return { "success": True, "data": txns }


    def approve_transaction(self, transaction_id: str, agent: str, comments: str = "") -> dict:
        """
        Approve a single flagged transaction. Updates resolution_status, flag_status, and creates/updates an audit log entry.

        Args:
            transaction_id (str): ID of the transaction to approve.
            agent (str): Username or identifier of the agent approving the transaction (required for audit).
            comments (str, optional): Additional comments for audit/compliance log.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction <id> approved and audit log updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Transaction must exist.
            - Transaction must have flag_status == "flagged".
            - All status changes must be timestamped and include agent and audit comments.
            - Updates both transaction['resolution_status'] and transaction['flag_status'].
            - Updates or creates an entry in self.resolutions.
        """
        txn = self.transactions.get(transaction_id)
        if txn is None:
            return {"success": False, "error": "Transaction does not exist."}
    
        if txn.get("flag_status") != "flagged":
            return {"success": False, "error": "Transaction is not flagged and cannot be approved."}
    
        # Update status
        txn["resolution_status"] = "approved"
        txn["flag_status"] = "approved"
        self.transactions[transaction_id] = txn

        # Audit log in resolutions
        ts = str(int(time.time()))
        audit_comment = f"Approved by {agent} at {ts}."
        if comments:
            audit_comment += f" Comments: {comments}"
        res_info = {
            "transaction_id": transaction_id,
            "reviewed_by": agent,
            "status": "approved",
            "reviewed_at": ts,
            "comments_audit_trail": audit_comment
        }
        self.resolutions[transaction_id] = res_info

        return {"success": True, "message": f"Transaction {transaction_id} approved and audit log updated."}


    def batch_approve_flagged_transactions(
        self,
        reviewed_by: str,
        comments: str = "",
        reviewed_at: str = None
    ) -> dict:
        """
        Approve all transactions currently flagged (flag_status == 'flagged'):
        - Updates transaction's resolution_status to 'approved' and flag_status to 'approved'
        - Makes/updates ResolutionInfo with audit log (reviewed_by, reviewed_at, status, comments)
        - All audits are timestamped with current time

        Args:
            reviewed_by (str): The agent/user who approves the flagged transactions (must not be empty).
            comments (str, optional): Additional comments for all approvals (default blank).
            reviewed_at (str, optional): Explicit review timestamp to store in the audit record.
                If omitted, the current UTC time is used.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success message
                "approved_transactions": List[str]  # List of transaction IDs processed
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only transactions with flag_status == "flagged" are processed
            - Audit trails must be logged/resolution audit entry created/updated for each
            - All status changes must be timestamped and linked to reviewed_by
        """
        if not reviewed_by or not isinstance(reviewed_by, str):
            return {"success": False, "error": "Parameter 'reviewed_by' is required and must be a string."}

        to_approve = [
            t_id for t_id, t_info in self.transactions.items()
            if t_info.get("flag_status") == "flagged"
        ]

        now = reviewed_at if reviewed_at else time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        approved_list = []

        for t_id in to_approve:
            trx = self.transactions[t_id]
            # Update status
            trx["resolution_status"] = "approved"
            trx["flag_status"] = "approved"  # Could also be "cleared", as per business rules

            # Audit log (ResolutionInfo)
            res_info = {
                "transaction_id": t_id,
                "reviewed_by": reviewed_by,
                "status": "approved",
                "reviewed_at": now,
                "comments_audit_trail": comments or "Batch auto-approved."
            }
            self.resolutions[t_id] = res_info
            approved_list.append(t_id)

        return {
            "success": True,
            "message": f"{len(approved_list)} flagged transactions approved.",
            "approved_transactions": approved_list
        }


    def update_flag_status(
        self,
        transaction_id: str,
        new_flag_status: str,
        user: str,
        comment: str = ""
    ) -> dict:
        """
        Change the flag_status of a given transaction (e.g., from 'reviewed' to 'flagged' or 'approved')
        and log the change in the ResolutionInfo audit trail.

        Args:
            transaction_id (str): Transaction to update.
            new_flag_status (str): New flag_status value.
            user (str): Username/agent performing action (must not be empty).
            comment (str, optional): Additional comment or reason.

        Returns:
            dict: {"success": True, "message": "..."} on success;
                  {"success": False, "error": "..."} on error.

        Constraints:
            - Updates must be logged for audit/compliance; log includes user, timestamp, old/new status, optional comment.
            - Transaction must exist.
            - user must not be empty.
        """
        if not user or not isinstance(user, str):
            return {"success": False, "error": "User/agent must be provided and non-empty."}
        txn = self.transactions.get(transaction_id)
        if not txn:
            return {"success": False, "error": "Transaction not found."}

        old_flag_status = txn["flag_status"]
        # Do the update
        txn["flag_status"] = new_flag_status
        self.transactions[transaction_id] = txn  # For completeness

        # Build audit entry
        now_iso = datetime.utcnow().isoformat()
        audit_entry = (
            f"[{now_iso}] User '{user}' changed flag_status: '{old_flag_status}' -> '{new_flag_status}'."
        )
        if comment:
            audit_entry += f" Comment: {comment}"

        # Update or create resolution audit trail
        if transaction_id in self.resolutions:
            res = self.resolutions[transaction_id]
            # Append to audit trail (newline separated)
            if res["comments_audit_trail"]:
                res["comments_audit_trail"] += "\n" + audit_entry
            else:
                res["comments_audit_trail"] = audit_entry
            # Set status to reflect latest operation
            res["status"] = f"flag_status:{new_flag_status}"
            res["reviewed_by"] = user
            res["reviewed_at"] = now_iso
            self.resolutions[transaction_id] = res
        else:
            # Create fresh resolution entry
            self.resolutions[transaction_id] = {
                "transaction_id": transaction_id,
                "reviewed_by": user,
                "status": f"flag_status:{new_flag_status}",
                "reviewed_at": now_iso,
                "comments_audit_trail": audit_entry,
            }

        return {"success": True, "message": f"Flag status updated to '{new_flag_status}' for transaction '{transaction_id}' and audit logged."}

    def resolve_transaction(
        self,
        transaction_id: str,
        reviewed_by: str,
        status: str,
        reviewed_at: str,
        comments: str
    ) -> dict:
        """
        Set the resolution status (e.g., verified, approved, rejected) of a transaction and record the review (who, when, comments).

        Args:
            transaction_id (str): The ID of the transaction to resolve.
            reviewed_by (str): The user/agent reviewing the transaction.
            status (str): New resolution status ("verified", "approved", "rejected", etc.).
            reviewed_at (str): Timestamp of review (ISO8601 or standard string format).
            comments (str): Review comments or audit trail for compliance.

        Returns:
            dict: {
                "success": True,
                "message": f"Transaction <transaction_id> resolved as <status> by <reviewed_by>."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Transaction must exist.
            - ResolutionInfo must be created/updated for auditing.
            - Transaction's resolution_status must be updated.
            - Transaction's flag_status is updated to the supplied final status so the item leaves the flagged queue.
            - All status changes must be timestamped and linked to a reviewer.
        """
        # Check for required fields and existence
        if not transaction_id or transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction does not exist" }
        if not reviewed_by:
            return { "success": False, "error": "Reviewer (reviewed_by) must be specified" }
        if not status:
            return { "success": False, "error": "Resolution status must be specified" }
        if not reviewed_at:
            return { "success": False, "error": "Review timestamp (reviewed_at) must be specified" }

        # Update transaction resolution_status and clear it from the flagged queue.
        self.transactions[transaction_id]["resolution_status"] = status
        self.transactions[transaction_id]["flag_status"] = status

        # Audit log/update
        resolution_record = ResolutionInfo(
            transaction_id=transaction_id,
            reviewed_by=reviewed_by,
            status=status,
            reviewed_at=reviewed_at,
            comments_audit_trail=comments
        )
        self.resolutions[transaction_id] = resolution_record

        return {
            "success": True,
            "message": f"Transaction {transaction_id} resolved as {status} by {reviewed_by}."
        }

    def add_flag_to_transaction(self, transaction_id: str, flag_type: str, description: str, created_at: str, flag_id: str = None) -> dict:
        """
        Create and attach a new fraud flag to an existing transaction.

        Args:
            transaction_id (str): ID of the transaction to flag.
            flag_type (str): The type/category of fraud suspicion.
            description (str): Detail or reason for the flag.
            created_at (str): ISO-format timestamp when the flag is created.
            flag_id (str, optional): If provided, used as the flag's ID; if not, a unique one is generated.

        Returns:
            dict:
              - On success: { "success": True, "message": "Flag added to transaction XYZ with flag_id ..."}
              - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The referenced transaction must exist.
            - The flag_id must be unique.
            - Each flag must reference a valid transaction.
        """
        # Check transaction exists
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Referenced transaction does not exist"}

        # Generate unique flag_id if not provided
        if flag_id is None:
            flag_id = str(uuid.uuid4())
        else:
            # Validate unique flag_id
            if flag_id in self.flags:
                return {"success": False, "error": "Flag ID already exists"}

        # Attach the flag
        self.flags[flag_id] = {
            "flag_id": flag_id,
            "transaction_id": transaction_id,
            "flag_type": flag_type,
            "created_at": created_at,
            "description": description
        }

        return {
            "success": True,
            "message": f"Flag added to transaction {transaction_id} with flag_id {flag_id}"
        }


    def remove_flag_from_transaction(
        self,
        flag_id: str,
        removed_by: str,
        removal_comment: str
    ) -> dict:
        """
        Remove or deactivate a specific flag from a transaction, and log/audit this action.

        Args:
            flag_id (str): The unique ID of the flag to remove.
            removed_by (str): The username/agent performing the removal (for auditing).
            removal_comment (str): Reason or context for the removal (for audit trail).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Flag {flag_id} removed from transaction {transaction_id} and action audited." }
                On failure:
                    { "success": False, "error": str }
    
        Constraints:
            - The flag_id must exist.
            - The flag's associated transaction_id must exist.
            - The action must be auditable: log entry with timestamp, agent, reason.
        """
        if flag_id not in self.flags:
            return { "success": False, "error": f"Flag {flag_id} does not exist." }

        flag_info = self.flags[flag_id]
        transaction_id = flag_info["transaction_id"]
        if transaction_id not in self.transactions:
            return { "success": False, "error": f"Transaction {transaction_id} referenced by flag does not exist." }
    
        # Remove the flag
        del self.flags[flag_id]

        # Audit the action (log in resolutions)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        audit_note = f"Flag {flag_id} removed by {removed_by} at {timestamp}. Comment: {removal_comment}"
        # Append to audit trail if resolution exists, else create it
        if transaction_id in self.resolutions:
            prev = self.resolutions[transaction_id]["comments_audit_trail"]
            new_audit = prev + "\n" + audit_note if prev else audit_note
            self.resolutions[transaction_id]["comments_audit_trail"] = new_audit
        else:
            self.resolutions[transaction_id] = {
                "transaction_id": transaction_id,
                "reviewed_by": removed_by,
                "status": "flag_removed",
                "reviewed_at": timestamp,
                "comments_audit_trail": audit_note,
            }
        return {
            "success": True,
            "message": f"Flag {flag_id} removed from transaction {transaction_id} and action audited."
        }

    def log_audit_entry(self, transaction_id: str, reviewed_by: str, action: str, timestamp: str, comments: str) -> dict:
        """
        Explicitly record an audit trail event for a transaction, including user/agent, action, timestamp, and comments.

        Args:
            transaction_id (str): ID of the transaction audited.
            reviewed_by (str): User or agent performing the action.
            action (str): What was done (action to record).
            timestamp (str): When the action was performed (e.g., ISO string).
            comments (str): Additional notes or explanation.

        Returns:
            dict: {
                "success": True,
                "message": "Audit entry recorded for transaction"
            }
            or
            dict: {
                "success": False,
                "error": str  # Reason, e.g., transaction does not exist
            }

        Constraints:
            - transaction_id must exist in the system.
            - Audit entry must be appended to comments_audit_trail in ResolutionInfo.
            - Audit entries must always include user, action, timestamp.
        """
        # Check transaction exists
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction does not exist" }

        # Compose audit entry
        entry = f"[{timestamp}] {reviewed_by} {action}: {comments}"

        # Ensure a resolution record exists for this transaction
        if transaction_id not in self.resolutions:
            self.resolutions[transaction_id] = {
                "transaction_id": transaction_id,
                "reviewed_by": reviewed_by,
                "status": "",  # No status update for audit record
                "reviewed_at": timestamp,
                "comments_audit_trail": entry
            }
        else:
            # Append audit entry to existing audit trail
            current_trail = self.resolutions[transaction_id]["comments_audit_trail"]
            if current_trail:
                new_trail = current_trail + "\n" + entry
            else:
                new_trail = entry
            self.resolutions[transaction_id]["comments_audit_trail"] = new_trail
            # Optionally update reviewed_by and reviewed_at for this audit
            self.resolutions[transaction_id]["reviewed_by"] = reviewed_by
            self.resolutions[transaction_id]["reviewed_at"] = timestamp

        return { "success": True, "message": "Audit entry recorded for transaction" }


    def update_transaction_field(
        self,
        transaction_id: str,
        field: str,
        value: Any,
        user_id: str,
        comment: str = ""
    ) -> dict:
        """
        Update an arbitrary transaction field and record the change in the audit log (ResolutionInfo).

        Args:
            transaction_id (str): The transaction identifier.
            field (str): The TransactionInfo field to update.
            value (Any): The new value for the field.
            user_id (str): The user/agent performing the update (for auditing).
            comment (str): Optional comment/justification for the change.

        Returns:
            dict: {
                "success": True,
                "message": "Field updated and audit logged."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Transaction must exist.
            - Field must exist in TransactionInfo and be updatable (not 'transaction_id').
            - All updates must be auditable (append to comments_audit_trail, update reviewed_at and reviewed_by in resolutions).
        """
        # Validate the transaction
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction does not exist." }

        # Prevent transaction_id modification and invalid fields
        valid_fields = set(self.transactions[transaction_id].keys()) - {"transaction_id"}
        if field not in valid_fields:
            return { "success": False, "error": f"Field '{field}' is not updatable or does not exist." }

        # Save old value
        old_value = self.transactions[transaction_id][field]
        # Update transaction field
        self.transactions[transaction_id][field] = value

        # Prepare audit log entry
        timestamp = datetime.utcnow().isoformat() + "Z"
        audit_entry = (
            f"[{timestamp}] user '{user_id}' updated '{field}': '{old_value}' -> '{value}'"
        )
        if comment:
            audit_entry += f" | Comment: {comment}"

        # Audit in ResolutionInfo
        res = self.resolutions.get(transaction_id)
        if res:
            # Append to existing audit trail
            prev_trail = res.get("comments_audit_trail", "")
            new_trail = (prev_trail + "\n" + audit_entry) if prev_trail else audit_entry
            res["comments_audit_trail"] = new_trail
            res["reviewed_by"] = user_id
            res["reviewed_at"] = timestamp
        else:
            # Create a resolution/audit record
            self.resolutions[transaction_id] = {
                "transaction_id": transaction_id,
                "reviewed_by": user_id,
                "status": self.transactions[transaction_id].get("resolution_status", ""),
                "reviewed_at": timestamp,
                "comments_audit_trail": audit_entry,
            }

        return { "success": True, "message": f"Field '{field}' updated for transaction '{transaction_id}' and audit logged." }


class RetailFraudDetectionSystem(BaseEnv):
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

    def get_flagged_transactions(self, **kwargs):
        return self._call_inner_tool('get_flagged_transactions', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def get_flags_for_transaction(self, **kwargs):
        return self._call_inner_tool('get_flags_for_transaction', kwargs)

    def get_flag_by_id(self, **kwargs):
        return self._call_inner_tool('get_flag_by_id', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def get_resolution_by_transaction(self, **kwargs):
        return self._call_inner_tool('get_resolution_by_transaction', kwargs)

    def list_transactions_by_status(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_status', kwargs)

    def get_transactions_for_customer(self, **kwargs):
        return self._call_inner_tool('get_transactions_for_customer', kwargs)

    def approve_transaction(self, **kwargs):
        return self._call_inner_tool('approve_transaction', kwargs)

    def batch_approve_flagged_transactions(self, **kwargs):
        return self._call_inner_tool('batch_approve_flagged_transactions', kwargs)

    def update_flag_status(self, **kwargs):
        return self._call_inner_tool('update_flag_status', kwargs)

    def resolve_transaction(self, **kwargs):
        return self._call_inner_tool('resolve_transaction', kwargs)

    def add_flag_to_transaction(self, **kwargs):
        return self._call_inner_tool('add_flag_to_transaction', kwargs)

    def remove_flag_from_transaction(self, **kwargs):
        return self._call_inner_tool('remove_flag_from_transaction', kwargs)

    def log_audit_entry(self, **kwargs):
        return self._call_inner_tool('log_audit_entry', kwargs)

    def update_transaction_field(self, **kwargs):
        return self._call_inner_tool('update_transaction_field', kwargs)
