# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class AccountInfo(TypedDict):
    account_id: str
    account_name: str
    account_type: str
    owner_id: str
    balance: float

class TransactionInfo(TypedDict):
    transaction_id: str
    account_id: str
    date: str
    amount: float
    category: str
    memo: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Accounts: maps account_id to AccountInfo
        # Entity: Account (account_id, account_name, account_type, owner_id, balance)
        self.accounts: Dict[str, AccountInfo] = {}

        # Transactions: maps transaction_id to TransactionInfo
        # Entity: Transaction (transaction_id, account_id, date, amount, category, memo)
        self.transactions: Dict[str, TransactionInfo] = {}

        # Users: maps user_id to UserInfo
        # Entity: User (_id as user_id, name, email)
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Every transaction must belong to exactly one account (account_id).
        # - Account balances may be computed as the sum of transaction amounts.
        # - No two transactions within the same account may share both the same date and the same memo.
        # - Amounts are numeric and can be positive (income) or negative (expense).

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of user information dicts with matching name (may be empty if no users found)
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., invalid input)
            }

        Constraints:
            - The name parameter must be a non-empty string.
            - Multiple users can share the same name; all matches are returned.
        """
        if not isinstance(name, str) or name.strip() == "":
            return { "success": False, "error": "Name must be a non-empty string" }

        result = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]

        return { "success": True, "data": result }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - If user exists: {"success": True, "data": UserInfo}
                - If user does not exist: {"success": False, "error": "User not found"}

        Constraints:
            - user_id must correspond to an existing user in the system.
        """
        user = self.users.get(user_id)
        if user is not None:
            return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_account_by_name(self, account_name: str, owner_id: str = None) -> dict:
        """
        Retrieve account details using account name, and optionally owner_id.

        Args:
            account_name (str): Name of the account to search for.
            owner_id (str, optional): ID of the owner. If specified, only accounts belonging to this owner are returned.

        Returns:
            dict: {
                "success": True,
                "data": AccountInfo or List[AccountInfo],
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If multiple accounts match (same name, different owners), returns list of matches.
            - If owner_id specified, only accounts under that owner are considered.
            - If no matching account, returns error.
        """
        # Collect matches according to parameters
        matches = []
        for acct in self.accounts.values():
            if acct["account_name"] == account_name:
                if owner_id is None or acct["owner_id"] == owner_id:
                    matches.append(acct)

        if not matches:
            return { "success": False, "error": "Account not found." }
        if len(matches) == 1:
            # return as singular object if only one match
            return { "success": True, "data": matches[0] }
        else:
            # return list of matches (can be >1 if searching globally)
            return { "success": True, "data": matches }

    def get_accounts_by_user(self, user_id: str) -> dict:
        """
        List all accounts belonging to a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[AccountInfo]  # Empty list if the user owns no accounts
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The user with the given user_id must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        accounts = [acc for acc in self.accounts.values() if acc["owner_id"] == user_id]
        return { "success": True, "data": accounts }

    def get_account_by_id(self, account_id: str) -> dict:
        """
        Retrieve account information given the unique account_id.

        Args:
            account_id (str): Unique identifier of the account.

        Returns:
            dict:
                - If found: { "success": True, "data": AccountInfo }
                - If not found: { "success": False, "error": "Account not found" }
        """
        account = self.accounts.get(account_id)
        if account is None:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": account }

    def list_transactions_by_account(self, account_id: str) -> dict:
        """
        Retrieve all transactions for the given account.

        Args:
            account_id (str): ID of the account whose transactions are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo]  # possibly empty if account has no transactions
            }
            or
            {
                "success": False,
                "error": str  # error reason (e.g., account not found)
            }
    
        Constraints:
            - account_id must exist in the system.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found"}
    
        transactions = [
            tx for tx in self.transactions.values()
            if tx["account_id"] == account_id
        ]
        return {"success": True, "data": transactions}

    def find_transaction_by_date_and_memo(self, account_id: str, date: str, memo: str) -> dict:
        """
        Retrieve a transaction in the specified account that matches both a specific date and memo.

        Args:
            account_id (str): The account's unique identifier.
            date (str): Transaction date (in the same format as stored in TransactionInfo).
            memo (str): Transaction memo for identification.

        Returns:
            dict:
              - If found: { "success": True, "data": TransactionInfo }
              - If no such transaction: { "success": False, "error": "Transaction not found" }
              - If account doesn't exist: { "success": False, "error": "Account does not exist" }

        Constraints:
            - Only search within the specified account.
            - No two transactions per account can have both the same date and the same memo.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        for transaction in self.transactions.values():
            if (
                transaction['account_id'] == account_id and
                transaction['date'] == date and
                transaction['memo'] == memo
            ):
                return { "success": True, "data": transaction }
    
        return { "success": False, "error": "Transaction not found" }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve full information about a transaction given its unique transaction_id.

        Args:
            transaction_id (str): The ID of the transaction to retrieve.

        Returns:
            dict:
                - If the transaction exists:
                    {
                        "success": True,
                        "data": TransactionInfo
                    }
                - If the transaction does not exist:
                    {
                        "success": False,
                        "error": "Transaction not found"
                    }
        Constraints:
            - The transaction_id must exist in the system.
        """
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            return { "success": False, "error": "Transaction not found" }
        return { "success": True, "data": transaction }

    def list_transactions_by_date(self, account_id: str, date: str) -> dict:
        """
        Get all transactions in a specific account for a given date.

        Args:
            account_id (str): ID of the account to query.
            date (str): Date string to filter transactions (format assumed as stored in TransactionInfo).

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo]  # All transactions for the account on the given date
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The account_id must exist.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        result = [
            tx for tx in self.transactions.values()
            if tx["account_id"] == account_id and tx["date"] == date
        ]
        return { "success": True, "data": result }

    def check_duplicate_transaction_in_account(self, account_id: str, date: str, memo: str) -> dict:
        """
        Check if a transaction with the given date and memo already exists in the account.

        Args:
            account_id (str): The account in which to check for duplicate.
            date (str): Date of the transaction (format assumed string).
            memo (str): Memo of the transaction.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if duplicate exists, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # error message if account does not exist
            }

        Constraints:
            - Account must exist.
            - Duplicate is defined as another transaction in the same account having the same date and memo.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        for tx in self.transactions.values():
            if (
                tx['account_id'] == account_id and
                tx['date'] == date and
                tx['memo'] == memo
            ):
                return { "success": True, "data": True }

        return { "success": True, "data": False }

    def calculate_account_balance(self, account_id: str) -> dict:
        """
        Compute (and update) the balance of the account as the sum of its transactions' amounts.

        Args:
            account_id (str): The ID of the account for which to calculate the balance.

        Returns:
            dict:
                - On success: { "success": True, "balance": float }
                - On failure: { "success": False, "error": str }
        Constraints:
            - The account_id must exist in the system.
            - The balance is computed as the sum of all amounts of transactions with the given account_id.
            - If there are no transactions, the balance is 0.0.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        total = 0.0
        for tx in self.transactions.values():
            if tx["account_id"] == account_id:
                total += tx["amount"]

        # Update balance in account info for internal consistency
        self.accounts[account_id]["balance"] = total

        return { "success": True, "balance": total }

    def update_transaction(
        self,
        transaction_id: str,
        amount: float = None,
        date: str = None,
        memo: str = None,
        category: str = None
    ) -> dict:
        """
        Modify amount, memo, category, or date of an existing transaction, enforcing uniqueness constraint within the account.

        Args:
            transaction_id (str): The ID of the transaction to update.
            amount (float, optional): New amount; must be numeric if provided.
            date (str, optional): New date.
            memo (str, optional): New memo.
            category (str, optional): New category.

        Returns:
            dict: 
                On success: { "success": True, "message": "Transaction updated successfully" }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - The transaction must exist.
            - The updated (date, memo) pair must be unique in the account (no duplicate with another transaction).
            - Amount must be numeric if provided.
        """

        # Check transaction exists
        tx = self.transactions.get(transaction_id)
        if not tx:
            return { "success": False, "error": "Transaction not found" }

        # Nothing to update?
        if amount is None and date is None and memo is None and category is None:
            return { "success": False, "error": "No fields to update" }

        # Prepare new values (defaults to existing)
        new_amount = tx["amount"] if amount is None else amount
        new_date = tx["date"] if date is None else date
        new_memo = tx["memo"] if memo is None else memo
        new_category = tx["category"] if category is None else category
        account_id = tx["account_id"]

        # Validate amount if provided
        if amount is not None:
            if not isinstance(amount, (float, int)):
                return { "success": False, "error": "Invalid amount" }

        # Enforce: uniqueness of (date, memo) in the account (excluding self)
        for other_tx in self.transactions.values():
            if (
                other_tx["transaction_id"] != transaction_id
                and other_tx["account_id"] == account_id
                and other_tx["date"] == new_date
                and other_tx["memo"] == new_memo
            ):
                return {
                    "success": False,
                    "error": "Duplicate transaction (date and memo) exists in account"
                }

        # All good, perform update
        tx["amount"] = float(new_amount)
        tx["date"] = new_date
        tx["memo"] = new_memo
        tx["category"] = new_category

        # Optionally, recalculate account balance (if system keeps it eager)
        if account_id in self.accounts:
            account = self.accounts[account_id]
            account["balance"] = sum(
                t["amount"]
                for t in self.transactions.values()
                if t["account_id"] == account_id
            )

        return { "success": True, "message": "Transaction updated successfully" }

    def add_transaction(
        self,
        transaction_id: str,
        account_id: str,
        date: str,
        amount: float,
        category: str,
        memo: str
    ) -> dict:
        """
        Create a new transaction under a specific account with linkage and uniqueness constraints.

        Args:
            transaction_id (str): A unique identifier for the transaction.
            account_id (str): The account to associate with this transaction.
            date (str): The transaction date (ISO or YYYY-MM-DD recommended).
            amount (float): Transaction amount (negative for expense, positive for income).
            category (str): Transaction category.
            memo (str): Description/memo.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction added successfully"
            } on success,
            or
            {
                "success": False,
                "error": "<description>"
            }

        Constraints:
            - The referenced account must exist.
            - The transaction_id must be unique.
            - No other transaction within the same account can share the same date and memo.
            - The amount must be numeric (float or int).
        """
        # Check for missing parameters
        if not all([transaction_id, account_id, date, category, memo]):
            return {"success": False, "error": "Missing required transaction fields"}

        # Check amount is numeric
        try:
            float_amount = float(amount)
        except (TypeError, ValueError):
            return {"success": False, "error": "Amount must be numeric"}

        # Check account exists
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}

        # Check transaction_id uniqueness
        if transaction_id in self.transactions:
            return {"success": False, "error": "Transaction ID already exists"}

        # Check uniqueness of (date, memo) within this account
        for t in self.transactions.values():
            if t["account_id"] == account_id and t["date"] == date and t["memo"] == memo:
                return {"success": False, "error": "Duplicate transaction: this account already has a transaction with the same date and memo"}

        new_transaction: TransactionInfo = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "date": date,
            "amount": float_amount,
            "category": category,
            "memo": memo
        }
        self.transactions[transaction_id] = new_transaction

        # Update account balance immediately (sum of all transaction amounts)
        self.accounts[account_id]["balance"] += float_amount

        return {"success": True, "message": "Transaction added successfully"}

    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Removes a transaction from its associated account and from the system.
        Updates the account's balance accordingly.

        Args:
            transaction_id (str): The unique identifier of the transaction to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction deleted and account balance updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The transaction must exist.
            - The associated account must exist.
            - After removal, account balance reflects the removal of this transaction's amount.
        """
        # Check transaction exists
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return { "success": False, "error": "Transaction does not exist." }

        account_id = transaction["account_id"]
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Associated account does not exist." }

        # Update account's balance
        account["balance"] -= transaction["amount"]

        # Remove the transaction
        del self.transactions[transaction_id]

        return {
            "success": True,
            "message": "Transaction deleted and account balance updated."
        }

    def update_account_info(self, account_id: str, account_name: str = None, account_type: str = None) -> dict:
        """
        Edit account-level fields for a given account.

        Args:
            account_id (str): Unique identifier of the account to edit.
            account_name (Optional[str]): New name for the account (if updating).
            account_type (Optional[str]): New type for the account (if updating).

        Returns:
            dict: 
                On success:  { "success": True, "message": "Account info updated" }
                On failure:  { "success": False, "error": reason_str }
    
        Constraints:
            - The account_id must correspond to an existing account.
            - At least one updatable field must be provided.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account not found" }

        updated = False
        account = self.accounts[account_id]

        if account_name is not None:
            account["account_name"] = account_name
            updated = True

        if account_type is not None:
            account["account_type"] = account_type
            updated = True

        if not updated:
            return { "success": False, "error": "No updatable fields provided" }

        self.accounts[account_id] = account  # Re-assign for completeness (dict is mutable)
        return { "success": True, "message": "Account info updated" }

    def add_account(
        self, 
        account_id: str, 
        account_name: str, 
        account_type: str, 
        owner_id: str, 
        balance: float = 0.0
    ) -> dict:
        """
        Add a new financial account for a user.

        Args:
            account_id (str): Unique identifier for the account.
            account_name (str): The display name of the account.
            account_type (str): The type/category of the account (e.g., 'Checking', 'Savings').
            owner_id (str): The user_id of the account's owner.
            balance (float, optional): Opening balance for the account. Defaults to 0.0.

        Returns:
            dict: 
                On success:
                    {
                        "success": True, 
                        "message": "Account <account_id> added for user <owner_id>"
                    }
                On failure:
                    {
                        "success": False, 
                        "error": <error reason>
                    }

        Constraints:
            - account_id must be unique (not already in accounts).
            - owner_id must refer to an existing user.
            - balance must be numeric.
        """
        if account_id in self.accounts:
            return {"success": False, "error": f"Account with ID '{account_id}' already exists"}
        if owner_id not in self.users:
            return {"success": False, "error": f"User with ID '{owner_id}' does not exist"}
        try:
            balance = float(balance)
        except (TypeError, ValueError):
            return {"success": False, "error": "Balance must be a numeric value"}
        account_info: AccountInfo = {
            "account_id": account_id,
            "account_name": account_name,
            "account_type": account_type,
            "owner_id": owner_id,
            "balance": balance,
        }
        self.accounts[account_id] = account_info
        return {"success": True, "message": f"Account '{account_id}' added for user '{owner_id}'"}

    def delete_account(self, account_id: str) -> dict:
        """
        Remove the specified account and all transactions associated with it.

        Args:
            account_id (str): The unique identifier of the account to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Account and its transactions deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Account not found."
            }

        Constraints:
            - The account must exist.
            - All transactions belonging to this account will also be removed.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found."}

        # Remove transactions associated with this account
        to_delete = [tid for tid, tinfo in self.transactions.items() if tinfo["account_id"] == account_id]
        for tid in to_delete:
            del self.transactions[tid]

        # Remove the account itself
        del self.accounts[account_id]

        return {
            "success": True,
            "message": "Account and its transactions deleted successfully."
        }

    def recalculate_account_balance(self, account_id: str) -> dict:
        """
        Recompute and update the balance for the specified account by summing the
        amounts of all its transactions.

        Args:
            account_id (str): The unique identifier of the account to update.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Account balance recalculated to <new_balance>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Account does not exist"
                    }

        Constraints:
            - The specified account must exist.
            - The balance is computed as the sum of all transaction amounts for this account.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        balance = sum(
            t["amount"]
            for t in self.transactions.values()
            if t["account_id"] == account_id
        )
        self.accounts[account_id]["balance"] = balance

        return {
            "success": True,
            "message": f"Account balance recalculated to {balance}"
        }


class PersonalFinanceManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_account_by_name(self, **kwargs):
        return self._call_inner_tool('get_account_by_name', kwargs)

    def get_accounts_by_user(self, **kwargs):
        return self._call_inner_tool('get_accounts_by_user', kwargs)

    def get_account_by_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_id', kwargs)

    def list_transactions_by_account(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_account', kwargs)

    def find_transaction_by_date_and_memo(self, **kwargs):
        return self._call_inner_tool('find_transaction_by_date_and_memo', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def list_transactions_by_date(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_date', kwargs)

    def check_duplicate_transaction_in_account(self, **kwargs):
        return self._call_inner_tool('check_duplicate_transaction_in_account', kwargs)

    def calculate_account_balance(self, **kwargs):
        return self._call_inner_tool('calculate_account_balance', kwargs)

    def update_transaction(self, **kwargs):
        return self._call_inner_tool('update_transaction', kwargs)

    def add_transaction(self, **kwargs):
        return self._call_inner_tool('add_transaction', kwargs)

    def delete_transaction(self, **kwargs):
        return self._call_inner_tool('delete_transaction', kwargs)

    def update_account_info(self, **kwargs):
        return self._call_inner_tool('update_account_info', kwargs)

    def add_account(self, **kwargs):
        return self._call_inner_tool('add_account', kwargs)

    def delete_account(self, **kwargs):
        return self._call_inner_tool('delete_account', kwargs)

    def recalculate_account_balance(self, **kwargs):
        return self._call_inner_tool('recalculate_account_balance', kwargs)

