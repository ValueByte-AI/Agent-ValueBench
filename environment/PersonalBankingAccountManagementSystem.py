# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict
import uuid



class UserInfo(TypedDict):
    _id: str
    name: str
    contact_info: str
    account_id: str

class AccountInfo(TypedDict):
    account_id: str
    user_id: str
    account_type: str
    balance: float
    status: str

class RecurringPaymentInfo(TypedDict):
    recurring_payment_id: str
    account_id: str
    payee: str
    amount: float
    start_date: str
    frequency: str
    end_date: str
    status: str

class TransactionInfo(TypedDict):
    transaction_id: str
    account_id: str
    date: str
    amount: float
    type: str
    status: str
    recurring_payment_id: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a stateful personal banking account management system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Accounts: {account_id: AccountInfo}
        self.accounts: Dict[str, AccountInfo] = {}

        # Recurring Payments: {recurring_payment_id: RecurringPaymentInfo}
        self.recurring_payments: Dict[str, RecurringPaymentInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Constraints (to be implemented in methods):
        # - Only active recurring payments are processed and generate transactions.
        # - Transactions for recurring payments must fall within the payment schedule period.
        # - Transaction status should accurately reflect payment completion (e.g., cleared, pending, failed).
        # - Users can only access their own accounts and payment information.
        # - Account balance cannot go below allowed overdraft limit (if any) during payment execution.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user profile information (including internal user ID) by name.

        Args:
            name (str): The user's name to search for.

        Returns:
            dict: 
                - If user(s) found: {
                    "success": True,
                    "data": List[UserInfo]  # list of user info dict(s) with that name
                  }
                - If not found: {
                    "success": False,
                    "error": "User not found"
                  }

        Notes:
            - Name does not have to be unique; returns all matching users.
            - Returns an empty list if no user found.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "User not found"}

        matched_users = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]

        if matched_users:
            return {"success": True, "data": matched_users}
        else:
            return {"success": False, "error": "User not found"}

    def get_user_accounts(self, user_id: str) -> dict:
        """
        Retrieve all accounts associated with a specific user.

        Args:
            user_id (str): The unique user identifier whose accounts are to be retrieved.

        Returns:
            dict:
              - On success: {"success": True, "data": List[AccountInfo]} (may be empty if no accounts)
              - On error: {"success": False, "error": str} (if user does not exist)

        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        accounts = [
            account_info
            for account_info in self.accounts.values()
            if account_info["user_id"] == user_id
        ]
        return {"success": True, "data": accounts}

    def get_account_by_id(self, account_id: str) -> dict:
        """
        Retrieve details for a specific account by account_id.

        Args:
            account_id (str): Unique identifier for the account.

        Returns:
            dict:
                - If found: { "success": True, "data": AccountInfo }
                - If not found: { "success": False, "error": "Account not found" }

        Constraints:
            - account_id must exist in the system.
        """
        account = self.accounts.get(account_id)
        if account is None:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": account }

    def list_recurring_payments_for_account(self, account_id: str) -> dict:
        """
        List all recurring payments (active/inactive) for a particular account.

        Args:
            account_id (str): The identifier of the account.

        Returns:
            dict: {
                "success": True,
                "data": List[RecurringPaymentInfo], # may be empty if none
            }
            or
            {
                "success": False,
                "error": str # describes why, e.g., "Account does not exist"
            }

        Constraints:
            - The account must exist in the system.
            - No status filtering is performed (all recurring payments for this account are included).
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}

        result = [
            rp for rp in self.recurring_payments.values()
            if rp["account_id"] == account_id
        ]
        return {"success": True, "data": result}

    def list_recurring_payments_for_period(
        self,
        user_id: str,
        account_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        List all recurring payments linked to a particular account of a user that overlap with a given date range.

        Args:
            user_id (str): The requesting user's ID (for access control).
            account_id (str): The account to filter recurring payments by.
            start_date (str): The (inclusive) start of the period in ISO 8601 format (e.g., '2024-01-01').
            end_date (str): The (inclusive) end of the period in ISO 8601 format.

        Returns:
            dict:
                - On success: {"success": True, "data": List[RecurringPaymentInfo]}
                - On failure: {"success": False, "error": str}

        Constraints:
            - Only allow if user_id owns the account_id.
            - Return only those recurring payments whose schedule period overlaps with [start_date, end_date].
        """
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}

        if account['user_id'] != user_id:
            return {"success": False, "error": "Permission denied: user does not own the account"}

        # To ensure date comparisons, dates must be in ISO 8601 string format (YYYY-MM-DD or similar)
        results = []
        for rp in self.recurring_payments.values():
            if rp['account_id'] != account_id:
                continue
            # Overlap: (rp.end_date >= start_date) and (rp.start_date <= end_date)
            if rp['end_date'] >= start_date and rp['start_date'] <= end_date:
                results.append(rp)

        return {"success": True, "data": results}

    def get_recurring_payment_by_id(self, recurring_payment_id: str) -> dict:
        """
        Retrieve details about a particular recurring payment by its unique identifier.

        Args:
            recurring_payment_id (str): The ID of the recurring payment to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": RecurringPaymentInfo
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Recurring payment not found"
            }

        Notes:
            - Does not check user authorization. Access control should be handled at a higher layer if needed.
        """
        payment = self.recurring_payments.get(recurring_payment_id)
        if payment is None:
            return {
                "success": False,
                "error": "Recurring payment not found"
            }
        return {
            "success": True,
            "data": payment
        }

    def list_transactions_for_recurring_payment(self, recurring_payment_id: str) -> dict:
        """
        List all transactions generated by a specified recurring payment.

        Args:
            recurring_payment_id (str): The identifier of the recurring payment.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of all transactions for this recurring payment
            }
            or
            {
                "success": False,
                "error": str  # If recurring_payment_id not found
            }

        Constraints:
            - recurring_payment_id must exist in the system.
            - Returns all transactions with that recurring_payment_id.
        """
        if recurring_payment_id not in self.recurring_payments:
            return {"success": False, "error": "Recurring payment not found"}

        transaction_list = [
            tx for tx in self.transactions.values()
            if tx["recurring_payment_id"] == recurring_payment_id
        ]

        return {
            "success": True,
            "data": transaction_list
        }

    def list_transactions_for_account_in_period(
        self, account_id: str, start_date: str, end_date: str
    ) -> dict:
        """
        List all transactions for a given account within the specified date range (inclusive).

        Args:
            account_id (str): The target account's ID.
            start_date (str): Start of date period, in 'YYYY-MM-DD' format (inclusive).
            end_date (str): End of date period, in 'YYYY-MM-DD' format (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of matching transactions
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The account must exist.
            - Dates are string-compared (assume ISO 8601 format 'YYYY-MM-DD').
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        # Collect transactions matching account and date range (inclusive)
        results = [
            tx for tx in self.transactions.values()
            if (
                tx["account_id"] == account_id and
                start_date <= tx["date"] <= end_date
            )
        ]
        return { "success": True, "data": results }

    def get_transaction_status(self, transaction_id: str) -> dict:
        """
        Retrieve the status (such as cleared, pending, failed, etc.) of a transaction, by its unique ID.

        Args:
            transaction_id (str): The identifier of the transaction.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": {
                        "transaction_id": str,
                        "status": str
                    }
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - The transaction must exist in the system.
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Transaction not found" }

        return { 
            "success": True,
            "data": {
                "transaction_id": transaction_id,
                "status": transaction["status"]
            }
        }

    def get_account_balance(self, account_id: str) -> dict:
        """
        Retrieve the current balance for a specific account.

        Args:
            account_id (str): The unique identifier of the account.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": float,  # current account balance
                }
                On failure: {
                    "success": False,
                    "error": str  # description of the problem
                }

        Constraints:
            - The account_id must exist in the banking system.
        """
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": account["balance"] }

    def get_account_status(self, account_id: str) -> dict:
        """
        Get the status (active/suspended/closed/etc.) of a specific account.

        Args:
            account_id (str): The unique identifier of the account.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": {
                        "account_id": str,
                        "status": str
                    }
                }
                OR
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - The account must exist in the system.
        """
        account = self.accounts.get(account_id)
        if account is None:
            return { "success": False, "error": "Account not found" }
        return {
            "success": True,
            "data": {
                "account_id": account_id,
                "status": account["status"]
            }
        }

    def list_user_recurring_payments(self, user_id: str) -> dict:
        """
        List all recurring payments configured by the user across all user accounts.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict: {
                "success": True,
                "data": List[RecurringPaymentInfo],  # All recurring payments for user's accounts.
            }
            or
            {
                "success": False,
                "error": str  # User not found.
            }

        Constraints:
            - Users can only view recurring payments for their own accounts.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_account_ids = [
            acct["account_id"] for acct in self.accounts.values()
            if acct["user_id"] == user_id
        ]

        # Collect recurring payments for all accounts owned by the user
        recurring_payments = [
            rp for rp in self.recurring_payments.values()
            if rp["account_id"] in user_account_ids
        ]

        return {"success": True, "data": recurring_payments}

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Get the details of a single transaction using its transaction ID.

        Args:
            transaction_id (str): The unique transaction identifier.

        Returns:
            dict:
                - success: True, and 'data' with TransactionInfo if found.
                - success: False, and 'error' if not found.

        Constraints:
            - No user/account permission checks are applied in this method.
            - Returns only if the transaction exists.
        """
        tx = self.transactions.get(transaction_id)
        if tx is None:
            return {"success": False, "error": "Transaction not found"}

        return {"success": True, "data": tx}

    def pause_recurring_payment(self, recurring_payment_id: str) -> dict:
        """
        Freeze or pause an active recurring payment schedule.

        Args:
            recurring_payment_id (str): The ID of the recurring payment to pause.

        Returns:
            dict: {
                "success": True,
                "message": "Recurring payment paused successfully."
            }
            or
            {
                "success": False,
                "error": "Recurring payment not found." | "Recurring payment is not active and cannot be paused."
            }

        Constraints:
            - Only recurring payments with status 'active' may be paused.
            - Paused recurring payments will not generate new transactions.
        """
        payment = self.recurring_payments.get(recurring_payment_id)
        if payment is None:
            return { "success": False, "error": "Recurring payment not found." }

        if payment["status"].lower() != "active":
            return { "success": False, "error": "Recurring payment is not active and cannot be paused." }

        payment["status"] = "paused"
        self.recurring_payments[recurring_payment_id] = payment

        return { "success": True, "message": "Recurring payment paused successfully." }

    def resume_recurring_payment(self, recurring_payment_id: str) -> dict:
        """
        Resume a previously paused recurring payment schedule.

        Args:
            recurring_payment_id (str): The ID of the recurring payment to resume.

        Returns:
            dict:
                - On success: {"success": True, "message": "Recurring payment <id> resumed."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - Recurring payment must exist.
            - Recurring payment must be in 'paused' status to be resumed.
            - Cannot resume if already active or if cancelled/terminated.

        Notes:
            - Does not check user ownership; assumes operation is invoked with appropriate permissions/context.
        """
        payment = self.recurring_payments.get(recurring_payment_id)
        if payment is None:
            return {"success": False, "error": "Recurring payment not found."}

        status = payment.get("status", "").lower()
        if status == "active":
            return {"success": False, "error": "Recurring payment is already active."}
        if status == "cancelled":
            return {"success": False, "error": "Recurring payment has been cancelled and cannot be resumed."}
        if status != "paused":
            return {"success": False, "error": f"Recurring payment cannot be resumed from status '{status}'."}

        payment["status"] = "active"
        self.recurring_payments[recurring_payment_id] = payment
        return {"success": True, "message": f"Recurring payment {recurring_payment_id} resumed."}

    def cancel_recurring_payment(self, user_id: str, recurring_payment_id: str) -> dict:
        """
        Permanently cancel an active recurring payment, if owned by the user.

        Args:
            user_id (str): The ID of the user requesting cancellation.
            recurring_payment_id (str): The ID of the recurring payment to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Recurring payment canceled successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - User can only cancel their own recurring payments (matching their account).
            - Only "active" recurring payments can be cancelled.
        """
        rp = self.recurring_payments.get(recurring_payment_id)
        if not rp:
            return {"success": False, "error": "Recurring payment not found."}
        account_id = rp["account_id"]
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Associated account not found."}
        if account["user_id"] != user_id:
            return {"success": False, "error": "Permission denied. User does not own this recurring payment."}
        if rp["status"].lower() != "active":
            return {"success": False, "error": f"Recurring payment is not active (current status: {rp['status']})."}
        # Cancel the payment (implementation: set status)
        rp["status"] = "canceled"
        self.recurring_payments[recurring_payment_id] = rp
        return {"success": True, "message": "Recurring payment canceled successfully."}

    def update_account_balance(
        self, 
        account_id: str, 
        amount_delta: float, 
        initiator_user_id: str
    ) -> dict:
        """
        Adjust the balance for a specific account by a specified amount (can be positive or negative).
    
        Args:
            account_id (str): The account to update.
            amount_delta (float): The amount to change the balance by (positive = credit, negative = debit).
            initiator_user_id (str): ID of the user attempting the operation (must be the account owner).
    
        Returns:
            dict: 
                { "success": True, "message": "Balance updated. New balance: X.XX" }
                or
                { "success": False, "error": "reason" }
    
        Constraints:
            - Only the account's owner may adjust this account's balance.
            - Balance cannot go below zero (unless an overdraft limit is implemented).
            - Account must exist.
        """
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}
    
        if account["user_id"] != initiator_user_id:
            return {"success": False, "error": "Permission denied: user cannot update this account"}
    
        new_balance = account["balance"] + amount_delta
        # Assuming no overdraft allowed
        if new_balance < 0:
            return {
                "success": False,
                "error": "Insufficient funds: operation would overdraw account"
            }
    
        account["balance"] = new_balance
        # Optionally: log or update timestamp, not specified.

        return {
            "success": True,
            "message": f"Balance updated. New balance: {new_balance:.2f}"
        }

    def add_transaction(
        self,
        transaction_id: str,
        account_id: str,
        date: str,
        amount: float,
        type: str,
        status: str,
        recurring_payment_id: Optional[str] = None,
    ) -> dict:
        """
        Manually add a new transaction (admin or system-initiated).

        Args:
            transaction_id (str): Unique ID for the transaction.
            account_id (str): The account to which the transaction applies.
            date (str): Transaction date in ISO format.
            amount (float): Transaction amount (positive value).
            type (str): "debit" or "credit".
            status (str): Status of transaction ("cleared", "pending", etc.).
            recurring_payment_id (Optional[str]): Link to a recurring payment if applicable.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction <id> added."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - Transaction ID must be unique.
            - Account must exist.
            - If recurring_payment_id is provided, it must exist.
            - For debits, account balance cannot go below zero (no overdraft allowed).
            - Amount must be positive.
        """
        # Check transaction id uniqueness
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists." }

        # Check if account exists
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account does not exist." }

        # Check if recurring_payment exists (if provided)
        if recurring_payment_id is not None:
            if recurring_payment_id not in self.recurring_payments:
                return { "success": False, "error": "Recurring payment does not exist." }

        # Amount must be positive
        if amount <= 0:
            return { "success": False, "error": "Transaction amount must be positive." }

        # For debits, check sufficient balance
        if type == "debit":
            if account["balance"] < amount:
                return { "success": False, "error": "Insufficient balance (no overdraft allowed)." }

        # Add transaction
        self.transactions[transaction_id] = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "date": date,
            "amount": amount,
            "type": type,
            "status": status,
            "recurring_payment_id": recurring_payment_id
        }

        # Optionally update balance (commonly done by banking systems)
        if status == "cleared":
            if type == "debit":
                account["balance"] -= amount
            elif type == "credit":
                account["balance"] += amount

        return { "success": True, "message": f"Transaction {transaction_id} added." }

    def update_transaction_status(self, transaction_id: str, new_status: str) -> dict:
        """
        Update the status of a transaction (e.g., from pending to cleared or failed).

        Args:
            transaction_id (str): The unique identifier for the transaction to update.
            new_status (str): The new desired status ("pending", "cleared", "failed", etc.)

        Returns:
            dict: {
                "success": True,
                "message": "Transaction status updated"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Transaction must exist in self.transactions.
            - The new status should be within the allowed status set ["pending", "cleared", "failed"].
            - If status is already the desired new_status, still report success but state so.
        """
        allowed_statuses = {"pending", "cleared", "failed"}
        txn = self.transactions.get(transaction_id)
        if txn is None:
            return { "success": False, "error": "Transaction does not exist" }

        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status value" }

        current_status = txn["status"]
        if current_status == new_status:
            return { "success": True, "message": f"Transaction status is already '{new_status}'" }

        txn["status"] = new_status
        self.transactions[transaction_id] = txn  # Save change

        return { "success": True, "message": f"Transaction status updated to '{new_status}'" }

    def create_recurring_payment(
        self, 
        acting_user_id: str, 
        account_id: str, 
        payee: str, 
        amount: float, 
        start_date: str, 
        frequency: str, 
        end_date: str
    ) -> dict:
        """
        Add a new recurring payment schedule to an account.

        Args:
            acting_user_id (str): The _id of the user attempting to create the recurring payment.
            account_id (str): The ID of the account from which the payment will be made.
            payee (str): The recipient of the recurring payment.
            amount (float): The recurring payment amount (must be positive).
            start_date (str): The starting date for the schedule (format: 'YYYY-MM-DD').
            frequency (str): The payment recurrence frequency (e.g., 'monthly', 'weekly').
            end_date (str): The end date for the recurrence (format: 'YYYY-MM-DD').

        Returns:
            dict: 
                On success: 
                    {
                        "success": True,
                        "message": "Recurring payment created successfully",
                        "recurring_payment_id": <generated_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error_reason>
                    }

        Constraints:
            - The user may only create recurring payments on their own accounts.
            - Account must be active.
            - Amount must be positive.
            - start_date must not be after end_date.
        """
        # Check if account exists
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}

        # Permission: Only allow if acting_user_id matches account's user_id
        if account["user_id"] != acting_user_id:
            return {"success": False, "error": "User not authorized to add payments to this account"}

        # Account status must be active
        if account["status"].lower() != "active":
            return {"success": False, "error": "Account is not active"}

        # Basic amount check
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {"success": False, "error": "Amount must be positive"}

        # Basic date check (formatting assumed correct for simplicity)
        if start_date > end_date:
            return {"success": False, "error": "Start date must not be after end date"}

        # Frequency check - restrict to basic allowed types for example
        allowed_frequencies = {"daily", "weekly", "monthly", "yearly"}
        if frequency.lower() not in allowed_frequencies:
            return {"success": False, "error": f"Frequency '{frequency}' is not allowed"}

        # Generate unique recurring_payment_id
        recurring_payment_id = str(uuid.uuid4())

        # Compose and insert new RecurringPaymentInfo
        new_payment: RecurringPaymentInfo = {
            "recurring_payment_id": recurring_payment_id,
            "account_id": account_id,
            "payee": payee,
            "amount": amount,
            "start_date": start_date,
            "frequency": frequency,
            "end_date": end_date,
            "status": "active"
        }
        self.recurring_payments[recurring_payment_id] = new_payment

        return {
            "success": True,
            "message": "Recurring payment created successfully",
            "recurring_payment_id": recurring_payment_id
        }

    def edit_recurring_payment(
        self,
        recurring_payment_id: str,
        user_id: str,
        amount: float = None,
        payee: str = None,
        start_date: str = None,
        frequency: str = None,
        end_date: str = None,
        status: str = None
    ) -> dict:
        """
        Modify details of an existing recurring payment (amount, payee, schedule, etc.).
        Only the user that owns the account may edit their associated recurring payments.

        Args:
            recurring_payment_id (str): The unique ID of the recurring payment to be edited.
            user_id (str): User ID requesting the edit (for permission check).
            amount (float, optional): New payment amount (must be positive if provided).
            payee (str, optional): New payee name/identifier.
            start_date (str, optional): New start date (ISO format).
            frequency (str, optional): New frequency (e.g., 'monthly', 'weekly').
            end_date (str, optional): New end date (ISO format).
            status (str, optional): New status (e.g., 'active', 'paused', 'cancelled').

        Returns:
            dict:
                - success: True/False
                - message: (on success)
                - error: Reason for failure (on error)

        Constraints:
            - Only the user who owns the associated account may edit this recurring payment.
            - amount, if given, must be positive.
            - start_date, if both given, should not be after end_date.
            - recurring payment must exist.

        """
        rp = self.recurring_payments.get(recurring_payment_id)
        if rp is None:
            return {"success": False, "error": "Recurring payment does not exist"}

        account_id = rp["account_id"]
        account = self.accounts.get(account_id)
        if account is None:
            return {"success": False, "error": "Associated account not found"}

        if account["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: User does not own this recurring payment"}

        # Sanity checks on fields
        if amount is not None:
            if not isinstance(amount, (int, float)) or amount <= 0:
                return {"success": False, "error": "Amount must be a positive number"}
            rp["amount"] = amount

        if payee is not None:
            if not isinstance(payee, str) or not payee.strip():
                return {"success": False, "error": "Payee must be a non-empty string"}
            rp["payee"] = payee.strip()

        if start_date is not None:
            if not isinstance(start_date, str) or not start_date.strip():
                return {"success": False, "error": "Start date must be a valid non-empty string"}
            rp["start_date"] = start_date.strip()

        if end_date is not None:
            if not isinstance(end_date, str) or not end_date.strip():
                return {"success": False, "error": "End date must be a valid non-empty string"}
            rp["end_date"] = end_date.strip()

        # If both start_date and end_date now exist, check order (simple string compare, since dates should be in ISO format)
        new_start = rp.get("start_date")
        new_end = rp.get("end_date")
        if new_start and new_end and new_start > new_end:
            return {"success": False, "error": "Start date cannot be after end date"}

        if frequency is not None:
            if not isinstance(frequency, str) or not frequency.strip():
                return {"success": False, "error": "Frequency must be a valid non-empty string"}
            rp["frequency"] = frequency.strip()

        if status is not None:
            allowed_statuses = {"active", "paused", "cancelled"}
            if status not in allowed_statuses:
                return {"success": False, "error": f"Status must be one of {allowed_statuses}"}
            rp["status"] = status

        # Save changes
        self.recurring_payments[recurring_payment_id] = rp

        return {"success": True, "message": "Recurring payment updated successfully."}

    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Remove a transaction record, identified by its transaction_id.

        Args:
            transaction_id (str): The unique identifier for the transaction to be deleted.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Transaction <id> deleted."}
                On failure:
                    {"success": False, "error": "Transaction does not exist."}

        Constraints:
            - Only an admin may invoke this operation (permission check not performed here).
            - If the transaction does not exist, no deletion is performed.
        """
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            return {"success": False, "error": "Transaction does not exist."}
        if transaction.get("status") == "deleted":
            return {"success": True, "message": f"Transaction {transaction_id} deleted."}
        transaction["status"] = "deleted"
        self.transactions[transaction_id] = transaction
        return {"success": True, "message": f"Transaction {transaction_id} deleted."}

    def restore_transaction(self, transaction_id: str) -> dict:
        """
        Restore a deleted (soft-deleted) transaction if recovery is allowed.

        Args:
            transaction_id (str): Unique ID of the transaction to restore.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction <id> restored."
            }
            or
            {
                "success": False,
                "error": str  # Error message describing the failure reason.
            }

        Constraints:
            - Transaction must exist with a status indicating it was deleted (e.g., "deleted").
            - Should not restore if transaction status is not "deleted".
            - Associated account must still exist.
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Transaction does not exist." }

        # Assumption: "deleted" status indicates soft-deletion
        if transaction["status"] != "deleted":
            return { "success": False, "error": "Transaction is not deleted or already active." }

        account_id = transaction["account_id"]
        if account_id not in self.accounts:
            return { "success": False, "error": "Associated account does not exist." }

        # Restore transaction (status change)
        transaction["status"] = "pending"   # Or "cleared"? Assuming "pending" is the default.

        # Update the transactions dictionary (assignment not strictly needed, but for clarity)
        self.transactions[transaction_id] = transaction

        return { "success": True, "message": f"Transaction {transaction_id} restored." }


class PersonalBankingAccountManagementSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_accounts(self, **kwargs):
        return self._call_inner_tool('get_user_accounts', kwargs)

    def get_account_by_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_id', kwargs)

    def list_recurring_payments_for_account(self, **kwargs):
        return self._call_inner_tool('list_recurring_payments_for_account', kwargs)

    def list_recurring_payments_for_period(self, **kwargs):
        return self._call_inner_tool('list_recurring_payments_for_period', kwargs)

    def get_recurring_payment_by_id(self, **kwargs):
        return self._call_inner_tool('get_recurring_payment_by_id', kwargs)

    def list_transactions_for_recurring_payment(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_recurring_payment', kwargs)

    def list_transactions_for_account_in_period(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_account_in_period', kwargs)

    def get_transaction_status(self, **kwargs):
        return self._call_inner_tool('get_transaction_status', kwargs)

    def get_account_balance(self, **kwargs):
        return self._call_inner_tool('get_account_balance', kwargs)

    def get_account_status(self, **kwargs):
        return self._call_inner_tool('get_account_status', kwargs)

    def list_user_recurring_payments(self, **kwargs):
        return self._call_inner_tool('list_user_recurring_payments', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def pause_recurring_payment(self, **kwargs):
        return self._call_inner_tool('pause_recurring_payment', kwargs)

    def resume_recurring_payment(self, **kwargs):
        return self._call_inner_tool('resume_recurring_payment', kwargs)

    def cancel_recurring_payment(self, **kwargs):
        return self._call_inner_tool('cancel_recurring_payment', kwargs)

    def update_account_balance(self, **kwargs):
        return self._call_inner_tool('update_account_balance', kwargs)

    def add_transaction(self, **kwargs):
        return self._call_inner_tool('add_transaction', kwargs)

    def update_transaction_status(self, **kwargs):
        return self._call_inner_tool('update_transaction_status', kwargs)

    def create_recurring_payment(self, **kwargs):
        return self._call_inner_tool('create_recurring_payment', kwargs)

    def edit_recurring_payment(self, **kwargs):
        return self._call_inner_tool('edit_recurring_payment', kwargs)

    def delete_transaction(self, **kwargs):
        return self._call_inner_tool('delete_transaction', kwargs)

    def restore_transaction(self, **kwargs):
        return self._call_inner_tool('restore_transaction', kwargs)
