# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any
import uuid
from datetime import datetime
import time
from typing import Any, Optional



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    phone_number: str
    registration_date: str
    account_status: str
    authentication_credential: str

class DigitalWalletAccountInfo(TypedDict):
    account_id: str
    user_id: str
    brocoins_balance: float
    last_updated: str
    account_metadata: Any  # Can be dict or str depending on system specifics

class TransactionInfo(TypedDict):
    transaction_id: str
    account_id: str
    amount: float
    currency_type: str
    timestamp: str
    transaction_type: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Digital Wallet Accounts: {account_id: DigitalWalletAccountInfo}
        self.wallet_accounts: Dict[str, DigitalWalletAccountInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Constraints:
        # - Each DigitalWalletAccount is uniquely linked to a User.
        # - brocoins_balance must be non-negative unless overdrafts are allowed.
        # - Authentication is required to access account details and balances.
        # - Only existing, active accounts can be queried for balance or details.

    @staticmethod
    def _normalize_status(value: Any) -> Optional[str]:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered:
                return lowered
        return None

    def _get_wallet_status(self, account: Dict[str, Any]) -> Optional[str]:
        direct_status = self._normalize_status(account.get("account_status"))
        if direct_status:
            return direct_status
        metadata = account.get("account_metadata")
        if isinstance(metadata, dict):
            metadata_status = self._normalize_status(metadata.get("status"))
            if metadata_status:
                return metadata_status
        return None

    def _set_wallet_status(self, account: Dict[str, Any], new_status: str) -> None:
        normalized_status = new_status.lower()
        account["account_status"] = normalized_status
        metadata = account.get("account_metadata")
        if isinstance(metadata, dict):
            metadata["status"] = normalized_status

    def _has_active_user(self, user: Optional[Dict[str, Any]]) -> bool:
        return bool(user) and self._normalize_status(user.get("account_status")) == "active"

    def _is_active_wallet_account(self, account: Dict[str, Any], user: Optional[Dict[str, Any]]) -> bool:
        if not self._has_active_user(user):
            return False
        wallet_status = self._get_wallet_status(account)
        return wallet_status in (None, "active")

    def authenticate_user(self, username: str, authentication_credential: str) -> dict:
        """
        Authenticate a user based on username and credential.

        Args:
            username (str): The username of the user trying to authenticate.
            authentication_credential (str): The credential (e.g., password/hash) to verify.

        Returns:
            dict: 
              On success:
                {
                    "success": True,
                    "auth_token": str,   # A mock/session token for the user
                    "user_id": str       # The user's unique ID
                }
              On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only users with 'account_status' == 'active' can authenticate.
            - User is looked up by username.
            - Credential must exactly match that stored for the user.
        """
        for user in self.users.values():
            if user["username"] == username:
                if user["account_status"] != "active":
                    return { "success": False, "error": "Account is not active" }
                if user["authentication_credential"] != authentication_credential:
                    return { "success": False, "error": "Invalid credentials" }
                # Token can be a placeholder string
                return {
                    "success": True,
                    "auth_token": f"token:{user['_id']}",
                    "user_id": user["_id"]
                }
        return { "success": False, "error": "User not found" }

    def get_user_profile(self, user_id: str = None, username: str = None) -> dict:
        """
        Retrieve profile details for a specific user by user ID or username.

        Args:
            user_id (str, optional): The unique identifier of the user.
            username (str, optional): The username of the user.

        Returns:
            dict:
                On success: { "success": True, "data": UserInfo }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - At least one of user_id or username must be provided.
            - Returns user info even if the user's account_status is not active.
        """
        if not user_id and not username:
            return { "success": False, "error": "Either user_id or username must be provided" }

        user = None
        if user_id:
            user = self.users.get(user_id)
            if user:
                return { "success": True, "data": user }

        if username:
            for info in self.users.values():
                if info.get("username") == username:
                    return { "success": True, "data": info }

        return { "success": False, "error": "User not found" }

    def get_account_by_user_id(self, user_id: str) -> dict:
        """
        Retrieve the digital wallet account information linked to a given user ID.
    
        Args:
            user_id (str): The unique ID of the user whose account info is requested.
        
        Returns:
            dict: 
              - On success: {"success": True, "data": DigitalWalletAccountInfo}
              - On error: {"success": False, "error": str}
    
        Constraints:
            - Only existing, active user accounts can be queried.
            - Account must exist and be uniquely linked to the given user.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}
        if user_info.get("account_status") != "active":
            return {"success": False, "error": "User account is not active"}

        # Find the wallet account with the matching user_id
        for account in self.wallet_accounts.values():
            if account.get("user_id") == user_id:
                return {"success": True, "data": account}
        return {"success": False, "error": "Wallet account not found for user"}

    def get_account_by_account_id(self, account_id: str) -> dict:
        """
        Retrieve wallet account details given an account ID.

        Args:
            account_id (str): The wallet account identifier.

        Returns:
            dict: {
                "success": True,
                "data": DigitalWalletAccountInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: non-existent account or inactive/non-existent user
            }

        Constraints:
            - Only existing, active accounts can be queried for details.
            - Account must exist.
            - The associated user must exist and have 'active' account_status.
        """
        account = self.wallet_accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Wallet account does not exist"}

        user_id = account.get("user_id")
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Associated user does not exist"}

        if not self._has_active_user(user):
            return {"success": False, "error": "Account is not active"}

        if self._get_wallet_status(account) not in (None, "active"):
            return {"success": False, "error": "Account is not active"}

        return {"success": True, "data": account}

    def check_account_status(self, account_id: str) -> dict:
        """
        Query whether a given wallet account is active and valid.

        Args:
            account_id (str): Unique identifier for the wallet account.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "account_id": str,
                    "status": str  # "active", "inactive", "not_found", "invalid_user_status"
                }
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - Only existing accounts linked to an active user are considered active and valid.
        """
        account = self.wallet_accounts.get(account_id)
        if account is None:
            status = "not_found"
        else:
            user_id = account.get("user_id")
            user = self.users.get(user_id)
            if not self._has_active_user(user):
                status = "invalid_user_status"
            else:
                status = self._get_wallet_status(account) or "active"
        return {
            "success": True,
            "data": {
                "account_id": account_id,
                "status": status
            }
        }

    def get_brocoins_balance(self, account_id: str, authentication_credential: str) -> dict:
        """
        Fetch the current BroCoins balance for a specific wallet account.

        Args:
            account_id (str): The ID of the digital wallet account.
            authentication_credential (str): The user's credential for authentication.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "account_id": str,
                    "brocoins_balance": float
                }
            } on success,
            or
            {
                "success": False,
                "error": str
            } on failure.

        Constraints:
            - The account must exist.
            - The linked user must exist and be active.
            - Valid authentication_credential is required.
        """
        account = self.wallet_accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account does not exist" }

        user = self.users.get(account["user_id"])
        if not user:
            return { "success": False, "error": "Linked user does not exist" }

        if user["account_status"].lower() != "active":
            return { "success": False, "error": "Account/user is not active" }

        if user["authentication_credential"] != authentication_credential:
            return { "success": False, "error": "Authentication failed" }

        return {
            "success": True,
            "data": {
                "account_id": account_id,
                "brocoins_balance": account["brocoins_balance"]
            }
        }

    def list_user_accounts(self, user_id: str) -> dict:
        """
        List all wallet accounts belonging to a specific user.

        Args:
            user_id (str): The unique ID of the user whose accounts are to be listed.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[DigitalWalletAccountInfo]  # All accounts for the user (empty if none)
                }
                On error:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The user must exist in the system.
            - Returns all wallet accounts where wallet_account['user_id'] == user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_accounts = [
            account for account in self.wallet_accounts.values()
            if account["user_id"] == user_id
        ]
        return {"success": True, "data": user_accounts}

    def list_transactions_for_account(self, account_id: str) -> dict:
        """
        Retrieve the transaction log (debits, credits) for a specific wallet account.

        Args:
            account_id (str): The ID of the wallet account.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of transactions for the account, may be empty
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure ("Account does not exist", "Account is not active")
            }

        Constraints:
            - Only existing, active accounts can be queried for their transactions.
            - An active account is defined as one linked to an active user (account_status == "active").
        """
        account = self.wallet_accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}

        user_id = account.get("user_id")
        user = self.users.get(user_id)
        if not user or user.get("account_status") != "active":
            return {"success": False, "error": "Account is not active"}

        transactions = [
            tx_info for tx_info in self.transactions.values()
            if tx_info["account_id"] == account_id
        ]
        return {"success": True, "data": transactions}

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Fetch details of a transaction using its transaction_id.

        Args:
            transaction_id (str): The unique ID of the transaction.

        Returns:
            dict: If transaction exists:
                {
                    "success": True,
                    "data": TransactionInfo  # Transaction details
                }
                If transaction does not exist:
                {
                    "success": False,
                    "error": "Transaction not found"
                }

        Constraints:
            - The transaction with the provided ID must exist.
        """
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found"}
        return {"success": True, "data": transaction}

    def get_all_active_accounts(self) -> dict:
        """
        List all wallet accounts whose owners are active users.

        Returns:
            dict: {
                "success": True,
                "data": List[DigitalWalletAccountInfo],  # list may be empty
            }

        Constraints:
            - Only include accounts where the linked user's account_status is "active".
            - If a wallet account references a missing user (user_id not in self.users), that account is omitted.
        """
        result = []
        for account in self.wallet_accounts.values():
            user_id = account.get("user_id")
            user = self.users.get(user_id)
            if self._has_active_user(user):
                result.append(account)
        return {"success": True, "data": result}

    def credit_brocoins(self, account_id: str, amount: float, currency_type: str = "BroCoins") -> dict:
        """
        Adds the specified amount of BroCoins to an account's balance and records a credit transaction.

        Args:
            account_id (str): The ID of the wallet account to credit.
            amount (float): Amount of BroCoins to add (must be > 0).
            currency_type (str, optional): The currency type; defaults to 'BroCoins'.

        Returns:
            dict:
                - success (bool)
                - message (str): on success, describes operation and transaction ID
                - error (str): on failure, describes the error

        Constraints:
            - Only existing, active accounts can be credited.
            - Amount must be positive.
            - The balance cannot be negative (credit never breaks this).
            - Transaction id must be unique.
            - last_updated is set to current time.
        """

        # Validate account
        account = self.wallet_accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account ID does not exist"}

        # Account is tied to a User; check user's account_status
        user_id = account["user_id"]
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Linked user does not exist for this account"}
        if not self._is_active_wallet_account(account, user):
            return {"success": False, "error": "Account is not active"}

        # Validate amount
        if not (isinstance(amount, (int, float)) and amount > 0):
            return {"success": False, "error": "Credit amount must be a positive number"}

        # Update balance and last_updated
        new_balance = account["brocoins_balance"] + amount
        now_str = datetime.now().isoformat(timespec='seconds')
        account["brocoins_balance"] = new_balance
        account["last_updated"] = now_str
        self.wallet_accounts[account_id] = account

        # Create new transaction
        transaction_id = str(uuid.uuid4())
        transaction = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount,
            "currency_type": currency_type,
            "timestamp": now_str,
            "transaction_type": "credit",
            "status": "success"
        }
        self.transactions[transaction_id] = transaction

        return {
            "success": True,
            "message": f"Credited {amount} {currency_type} to account {account_id}, transaction ID {transaction_id}."
        }


    def debit_brocoins(self, account_id: str, amount: float) -> dict:
        """
        Subtract a specified amount from an account’s BroCoins balance.
        Also creates a debit transaction log.
    
        Args:
            account_id (str): The ID of the wallet account to be debited.
            amount (float): Amount of BroCoins to subtract (must be positive).
    
        Returns:
            dict: {
                "success": True,
                "message": "Debited X BroCoins from account ..."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - Only existing, active accounts can be debited.
            - brocoins_balance must be >= amount and remain non-negative.
            - amount must be positive.
        """

        # Check account existence
        account = self.wallet_accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}
    
        # Check status
        user_id = account["user_id"]
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Associated user does not exist"}
        if not self._is_active_wallet_account(account, user):
            return {"success": False, "error": "Account not active"}

        # Input validation
        if not isinstance(amount, (float, int)) or amount <= 0:
            return {"success": False, "error": "Debit amount must be a positive number"}
    
        # Check sufficient funds
        if account["brocoins_balance"] < amount:
            return {"success": False, "error": "Insufficient BroCoins balance"}
    
        # Perform debit
        account["brocoins_balance"] -= amount
        account["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.wallet_accounts[account_id] = account  # Save back (if necessary)

        # Record transaction
        transaction_id = str(uuid.uuid4())
        transaction: TransactionInfo = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount,
            "currency_type": "BroCoins",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "transaction_type": "debit",
            "status": "completed"
        }
        self.transactions[transaction_id] = transaction

        return {
            "success": True,
            "message": f"Debited {amount} BroCoins from account {account_id} (new balance: {account['brocoins_balance']})."
        }


    def create_wallet_account(
        self, 
        user_id: str, 
        brocoins_balance: float = 0.0, 
        account_metadata: Optional[Any] = None,
        account_id: Optional[str] = None
    ) -> dict:
        """
        Initialize a new digital wallet account for a user.

        Args:
            user_id (str): The ID of the user for whom the account is created.
            brocoins_balance (float): Initial brocoins balance (must be >= 0). Default: 0.0.
            account_metadata (Any, optional): Metadata for the account. Default: empty dict.
            account_id (str, optional): Explicitly specify account_id. If None, the system generates it.

        Returns:
            dict: {
                "success": True,
                "message": "Wallet account created",
                "account_id": <account_id>
            }
            or
            {
                "success": False,
                "error": reason
            }

        Constraints:
            - Only existing users can be assigned a wallet account.
            - Each DigitalWalletAccount is uniquely linked to a User.
            - brocoins_balance must be non-negative.
            - Only one wallet account per user.
        """
        # Validate user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
    
        # Ensure unique link (user doesn't already have account)
        for acc in self.wallet_accounts.values():
            if acc["user_id"] == user_id:
                return { "success": False, "error": "User already has a wallet account" }
    
        # brocoins_balance must be non-negative
        if brocoins_balance < 0:
            return { "success": False, "error": "brocoins_balance cannot be negative" }
    
        # Generate account_id if not provided
        if not account_id:
            account_id = str(uuid.uuid4())

        # Use provided metadata or default
        if account_metadata is None:
            account_metadata = {}

        # Set last_updated to now in ISO8601
        now = datetime.utcnow().isoformat()

        account_info = {
            "account_id": account_id,
            "user_id": user_id,
            "brocoins_balance": brocoins_balance,
            "last_updated": now,
            "account_metadata": account_metadata
        }
        self.wallet_accounts[account_id] = account_info

        return {
            "success": True,
            "message": "Wallet account created",
            "account_id": account_id
        }

    def update_user_profile(self, user_id: str, updates: dict) -> dict:
        """
        Update profile details (such as email, phone, etc.) for an existing user.

        Args:
            user_id (str): The unique ID of the user whose profile is being updated.
            updates (dict): Key-value pairs of user info fields to update. 
                Allowed updatable fields: 'email', 'phone_number', 'account_status'

        Returns:
            dict: {
                "success": True,
                "message": "Profile updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Only fields 'email', 'phone_number', 'account_status' are allowed to be updated.
            - No updates if all provided fields are invalid.
        """
        allowed_fields = {'email', 'phone_number', 'account_status'}
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        user = self.users[user_id]
        updated = False

        for field, value in updates.items():
            if field not in allowed_fields:
                return { "success": False, "error": f"Cannot update field: {field}" }
            user[field] = value
            updated = True

        if not updated:
            return { "success": False, "error": "No valid fields provided to update" }

        self.users[user_id] = user
        return { "success": True, "message": "Profile updated successfully" }

    def change_account_status(self, account_id: str, new_status: str) -> dict:
        """
        Update the status of a wallet account to 'active', 'suspended', or 'closed'.

        Args:
            account_id (str): The ID of the digital wallet account to update.
            new_status (str): The target status ('active', 'suspended', 'closed').

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Account status updated to <new_status>"
                }
                On failure:
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - The account must exist.
            - Only 'active', 'suspended', or 'closed' are allowed as status values.
            - If the account is already in the target status, report success.
        """
        allowed_statuses = {'active', 'suspended', 'closed'}

        # Check account existence
        account = self.wallet_accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account does not exist" }

        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'" }

        # The DigitalWalletAccountInfo does not have 'account_status',
        # but from the state space definition, account_status may be part of User.
        # We'll check/add at the account level for robustness.
        old_status = self._get_wallet_status(account)
        if old_status == new_status:
            return { "success": True, "message": f"Account already in status '{new_status}'" }

        # Update the status
        self._set_wallet_status(account, new_status)
        self.wallet_accounts[account_id] = account

        return {
            "success": True,
            "message": f"Account status updated to '{new_status}'"
        }

    def record_transaction(
        self,
        transaction_id: str,
        account_id: str,
        amount: float,
        currency_type: str,
        timestamp: str,
        transaction_type: str,
        status: str
    ) -> dict:
        """
        Log a new transaction in the system for auditing or balance update.

        Args:
            transaction_id (str): Unique transaction identifier.
            account_id (str): The wallet account ID related to this transaction.
            amount (float): The amount of the transaction.
            currency_type (str): The currency type ("brocoins" expected).
            timestamp (str): Timestamp of the transaction (ISO 8601 recommended).
            transaction_type (str): Type of transaction ("credit" or "debit").
            status (str): Transaction status ("pending", "completed", etc.)

        Returns:
            dict: On success,
                { "success": True, "message": "Transaction recorded successfully." }
                  On failure,
                { "success": False, "error": "<reason>" }
        Constraints:
            - transaction_id must be unique (not already used).
            - account_id must exist in the system.
        """
        # Check transaction_id uniqueness
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists." }
        # Check associated account existence
        if account_id not in self.wallet_accounts:
            return { "success": False, "error": "Account does not exist." }

        # Create transaction entry
        transaction_info = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount,
            "currency_type": currency_type,
            "timestamp": timestamp,
            "transaction_type": transaction_type,
            "status": status
        }
        self.transactions[transaction_id] = transaction_info
        return { "success": True, "message": "Transaction recorded successfully." }

    def update_account_metadata(self, account_id: str, metadata: Any) -> dict:
        """
        Modify the metadata associated with a wallet account (e.g., set limits, preferences).

        Args:
            account_id (str): The identifier of the wallet account to modify.
            metadata (Any): The new metadata to associate with the account.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Account metadata updated for account_id <id>" }
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - The account must exist in the system.
            - The account must be in active status.
            - No restrictions on metadata content unless specified elsewhere.
        """
        account = self.wallet_accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}
    
        user_id = account["user_id"]
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "Account's associated user does not exist"}
        if not self._is_active_wallet_account(account, user_info):
            return {"success": False, "error": "Account is not active"}
    
        account["account_metadata"] = metadata
        # Optionally update last_updated timestamp (if logic requires)
        # from datetime import datetime
        # account["last_updated"] = datetime.utcnow().isoformat()
        return {
            "success": True,
            "message": f"Account metadata updated for account_id {account_id}"
        }


class DigitalWalletAccountManagementSystem(BaseEnv):
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

    def authenticate_user(self, **kwargs):
        return self._call_inner_tool('authenticate_user', kwargs)

    def get_user_profile(self, **kwargs):
        return self._call_inner_tool('get_user_profile', kwargs)

    def get_account_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_user_id', kwargs)

    def get_account_by_account_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_account_id', kwargs)

    def check_account_status(self, **kwargs):
        return self._call_inner_tool('check_account_status', kwargs)

    def get_brocoins_balance(self, **kwargs):
        return self._call_inner_tool('get_brocoins_balance', kwargs)

    def list_user_accounts(self, **kwargs):
        return self._call_inner_tool('list_user_accounts', kwargs)

    def list_transactions_for_account(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_account', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def get_all_active_accounts(self, **kwargs):
        return self._call_inner_tool('get_all_active_accounts', kwargs)

    def credit_brocoins(self, **kwargs):
        return self._call_inner_tool('credit_brocoins', kwargs)

    def debit_brocoins(self, **kwargs):
        return self._call_inner_tool('debit_brocoins', kwargs)

    def create_wallet_account(self, **kwargs):
        return self._call_inner_tool('create_wallet_account', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def change_account_status(self, **kwargs):
        return self._call_inner_tool('change_account_status', kwargs)

    def record_transaction(self, **kwargs):
        return self._call_inner_tool('record_transaction', kwargs)

    def update_account_metadata(self, **kwargs):
        return self._call_inner_tool('update_account_metadata', kwargs)
