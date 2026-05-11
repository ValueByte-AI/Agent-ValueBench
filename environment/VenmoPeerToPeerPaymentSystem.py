# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    profile_info: str
    authentication_status: str
    account_status: str

class AccountInfo(TypedDict):
    _id: str
    balance: float
    currency: str

class TransactionInfo(TypedDict):
    transaction_id: str
    sender_id: str
    recipient_id: str
    amount: float
    currency: str
    status: str
    timestamp: str
    note: str
    transaction_type: str

class ContactInfo(TypedDict):
    _id: str
    contact_user_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment class for a Venmo-like peer-to-peer payment system.
        """
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Accounts: {_id: AccountInfo}
        self.accounts: Dict[str, AccountInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Contacts: {_id: List[ContactInfo]}
        # By convention, each user's contacts can be looked up via self.contacts[user_id]
        self.contacts: Dict[str, List[ContactInfo]] = {}

        # Constraint rules (annotated, not enforced here):
        # - Sender must be authenticated and authorized for the operation.
        # - Sender’s account balance must be >= the payment amount.
        # - Transfers only allowed between valid, active accounts.
        # - Each transaction must have a unique identifier and be recorded in transaction history.
        # - User identification (e.g., by username or display name) must resolve to a unique, valid account.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve the full UserInfo record for a user specified by username.
    
        Args:
            username (str): The username of the user to lookup.
        
        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": UserInfo
                }
                On failure: {
                    "success": False,
                    "error": "User with specified username does not exist"
                }
                If multiple users are found (violation of uniqueness constraint): {
                    "success": False,
                    "error": "Multiple users found with the same username"
                }
        Constraints:
            - Each username should identify one unique, valid account.
        """
        # Collect users matching the given username.
        matching_users = [user for user in self.users.values() if user["username"] == username]

        if len(matching_users) == 0:
            return { "success": False, "error": "User with specified username does not exist" }
        if len(matching_users) > 1:
            # Uniqueness constraint violated.
            return { "success": False, "error": "Multiple users found with the same username" }

        # Success.
        return { "success": True, "data": matching_users[0] }

    def get_user_by_display_name(self, display_name: str) -> dict:
        """
        Retrieve all users matching the given display name.

        Args:
            display_name (str): Display name to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo]  # List of all users with that display name (possibly empty)
                }

        Notes:
            - Multiple users can share the same display name.
            - If no users are found, returns an empty list (not an error).
        """
        matching_users = [
            user_info for user_info in self.users.values()
            if user_info.get("display_name") == display_name
        ]
        return { "success": True, "data": matching_users }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Fetches and returns user information for the given unique user ID.

        Args:
            user_id (str): The unique user identifier (_id).

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - User _id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all registered users.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo]  # possibly empty
                }
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def check_user_authentication_status(self, user_id: str) -> dict:
        """
        Query the current authentication status of a user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # The authentication status of the user (e.g., "authenticated", "not authenticated", etc.)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found.
            }

        Constraints:
            - user_id must correspond to a valid user in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user.get("authentication_status") }

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Retrieve the current account status for a user.

        Args:
            user_id (str): The unique identifier for the user (_id field).

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "account_status": str  # e.g., 'active', 'suspended', 'closed'
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # "User not found"
                    }

        Constraints:
            - user_id must map to an existing user.
        """

        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User not found" }

        account_status = self.users[user_id].get("account_status", None)
        if not account_status:
            return { "success": False, "error": "Account status unavailable" }

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "account_status": account_status
            }
        }

    def get_account_by_user_id(self, user_id: str) -> dict:
        """
        Retrieve account details (including balance and currency) for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - success: True, and 'data' contains the AccountInfo if lookup is successful.
                - success: False, and 'error' describes reason (user/account not found).

        Constraints:
            - user_id must exist in the system.
            - The user must have a linked account.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if user_id not in self.accounts:
            return {"success": False, "error": "No account found for user"}
        account_info = self.accounts[user_id]
        return {"success": True, "data": account_info}

    def get_account_balance(self, user_id: str) -> dict:
        """
        Return the balance and currency of the account associated with a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": {"balance": float, "currency": str},
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - The user must exist.
            - The account associated with the user must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if user_id not in self.accounts:
            return {"success": False, "error": "Account does not exist for the user."}

        account_info = self.accounts[user_id]
        return {
            "success": True,
            "data": {
                "balance": account_info["balance"],
                "currency": account_info["currency"]
            }
        }

    def get_contacts_for_user(self, user_id: str) -> dict:
        """
        Retrieve the list of contact users (friends) for a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # List of contact relationships (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        contacts_list = self.contacts.get(user_id, [])
        return { "success": True, "data": contacts_list }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Fetch a specific transaction record by its transaction_id.

        Args:
            transaction_id (str): The unique identifier for the transaction.

        Returns:
            dict:
                - On success: { "success": True, "data": TransactionInfo }
                - On failure: { "success": False, "error": "Transaction not found" }

        Constraints:
            - The given transaction_id must exist in the transaction records.
        """
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction not found" }
        return { "success": True, "data": self.transactions[transaction_id] }

    def list_transactions_for_user(self, user_id: str) -> dict:
        """
        Retrieve the history of all transactions (sent/received/requests) for a given user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[TransactionInfo],  # all transactions involving the user (may be empty)
                }
                On failure: {
                    "success": False,
                    "error": str  # error message
                }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_transactions = [
            tx for tx in self.transactions.values()
            if tx["sender_id"] == user_id or tx["recipient_id"] == user_id
        ]

        return {"success": True, "data": user_transactions}

    def check_transaction_id_unique(self, transaction_id: str) -> dict:
        """
        Check if a proposed transaction ID is unique (not already used).

        Args:
            transaction_id (str): The transaction ID to check for uniqueness.

        Returns:
            dict:
                - If input is valid:
                    {"success": True, "data": bool}
                    # True if unique, False if already exists
                - If input is invalid:
                    {"success": False, "error": str}

        Constraints:
            - Transaction ID must be a non-empty string.
            - Transactions must have unique identifiers.
        """
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            return { "success": False, "error": "Invalid transaction ID: must be a non-empty string." }

        is_unique = transaction_id not in self.transactions
        return { "success": True, "data": is_unique }


    def send_payment(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        currency: str,
        note: str = "",
    ) -> dict:
        """
        Send money from sender to recipient, performing validation and recording the transaction.

        Args:
            sender_id (str): User ID of sender.
            recipient_id (str): User ID of recipient.
            amount (float): Amount to send (must be > 0).
            currency (str): Currency code (e.g., "USD").
            note (str, optional): Transaction note.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": str,  # Description of payment.
                        "transaction_id": str  # The new transaction ID
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of why payment failed
                    }

        Constraints enforced:
            - Sender must be authenticated.
            - Sender and recipient accounts must be valid and active.
            - Sender balance >= amount.
            - Currency must match both accounts.
            - Cannot send payment to oneself.
        """
        # Check sender and recipient exist
        sender = self.users.get(sender_id)
        recipient = self.users.get(recipient_id)
        if not sender:
            return { "success": False, "error": "Sender does not exist" }
        if not recipient:
            return { "success": False, "error": "Recipient does not exist" }
        if sender_id == recipient_id:
            return { "success": False, "error": "Cannot send payment to yourself" }
        # Check authentication
        if sender.get('authentication_status', '').lower() != "authenticated":
            return { "success": False, "error": "Sender is not authenticated" }
        # Check sender and recipient account status
        if sender.get('account_status', '').lower() != "active":
            return { "success": False, "error": "Sender's account is not active" }
        if recipient.get('account_status', '').lower() != "active":
            return { "success": False, "error": "Recipient's account is not active" }
        # Get sender/recipient accounts
        sender_acct = self.accounts.get(sender_id)
        recipient_acct = self.accounts.get(recipient_id)
        if not sender_acct or not recipient_acct:
            return { "success": False, "error": "Sender or recipient account does not exist" }
        # Check currency matches
        if sender_acct['currency'] != currency:
            return { "success": False, "error": "Sender account currency mismatch" }
        if recipient_acct['currency'] != currency:
            return { "success": False, "error": "Recipient account currency mismatch" }
        # Check amount validity
        if not (isinstance(amount, (int, float)) and amount > 0):
            return { "success": False, "error": "Amount must be positive" }
        # Check sufficient balance
        if sender_acct["balance"] < amount:
            return { "success": False, "error": "Insufficient balance" }
        # All good, perform transaction
        new_transaction_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        transaction_info = {
            "transaction_id": new_transaction_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "amount": amount,
            "currency": currency,
            "status": "completed",
            "timestamp": now,
            "note": note,
            "transaction_type": "payment"
        }
        # Deduct and credit
        self.accounts[sender_id]["balance"] -= amount
        self.accounts[recipient_id]["balance"] += amount
        # Record in transaction history
        self.transactions[new_transaction_id] = transaction_info
        return {
            "success": True,
            "message": f"Payment of {amount:.2f} {currency} sent from {sender.get('username','')} to {recipient.get('username','')}.",
            "transaction_id": new_transaction_id
        }


    def request_payment(self,
                       requester_id: str,
                       target_id: str,
                       amount: float,
                       currency: str,
                       note: str = "",
                       timestamp: str = None) -> dict:
        """
        Create a payment request transaction (pending status) from requester to target.

        Args:
            requester_id (str): ID of the user making the request.
            target_id (str): ID of the user to be requested from.
            amount (float): Amount to be requested. Must be > 0.
            currency (str): Currency code (e.g., 'USD').
            note (str, optional): Description or note for the request.
            timestamp (str, optional): Timestamp; if not provided, will use current time.

        Returns:
            dict: {
                "success": True,
                "message": "Payment request created",
                "transaction_id": str,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Requester must be authenticated and have active account.
            - Target user must exist and have active account.
            - Amount must be positive.
            - All IDs must resolve to existing users.
            - Transaction ID must be unique.
        """
        # Verify requester exists and is authenticated/active
        requester = self.users.get(requester_id)
        if not requester:
            return {"success": False, "error": "Requester does not exist"}
        if requester["authentication_status"] != "authenticated":
            return {"success": False, "error": "Requester is not authenticated"}
        if requester["account_status"] != "active":
            return {"success": False, "error": "Requester account is not active"}
    
        # Verify target exists and is active
        target = self.users.get(target_id)
        if not target:
            return {"success": False, "error": "Target user does not exist"}
        if target["account_status"] != "active":
            return {"success": False, "error": "Target account is not active"}

        # Amount sanity check
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {"success": False, "error": "Invalid amount (must be positive number)"}

        # Currency check (minimal)
        if not isinstance(currency, str) or not currency:
            return {"success": False, "error": "Invalid currency"}

        # Timestamp
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()

        # Generate unique transaction id
        for _ in range(5):
            transaction_id = str(uuid.uuid4())
            if transaction_id not in self.transactions:
                break
        else:
            return {"success": False, "error": "Could not generate unique transaction ID"}

        # Record transaction
        transaction = {
            'transaction_id': transaction_id,
            'sender_id': requester_id,
            'recipient_id': target_id,
            'amount': float(amount),
            'currency': currency,
            'status': "pending",
            'timestamp': timestamp,
            'note': note,
            'transaction_type': "request"
        }
        self.transactions[transaction_id] = transaction

        return {
            "success": True,
            "message": "Payment request created",
            "transaction_id": transaction_id
        }

    def record_transaction(self, transaction_info: TransactionInfo) -> dict:
        """
        Create a new transaction record in the transaction history, enforcing idempotency.

        Args:
            transaction_info (TransactionInfo): The full transaction data to be recorded. Must contain:
                transaction_id, sender_id, recipient_id, amount, currency, status, timestamp, note, transaction_type

        Returns:
            dict: 
                On success: { "success": True, "message": "Transaction recorded successfully" }
                On idempotency: { "success": True, "message": "Transaction already recorded (idempotent)" }
                On error: { "success": False, "error": "reason" }

        Constraints:
            - transaction_id must be unique unless the same transaction_info is supplied (idempotency).
            - transaction_info should follow the TransactionInfo schema.
        """
        tid = transaction_info.get("transaction_id")
        # Check missing transaction_id or required fields
        required_fields = [
            "transaction_id", "sender_id", "recipient_id", "amount", "currency",
            "status", "timestamp", "note", "transaction_type"
        ]
        missing = [field for field in required_fields if field not in transaction_info]
        if missing:
            return { "success": False, "error": f"Missing required fields: {missing}" }
    
        if tid in self.transactions:
            existing = self.transactions[tid]
            # Check for idempotency
            if dict(existing) == dict(transaction_info):
                return { "success": True, "message": "Transaction already recorded (idempotent)" }
            else:
                return { "success": False, "error": "Transaction ID already exists with different data" }
    
        # Record the transaction
        self.transactions[tid] = dict(transaction_info)
        return { "success": True, "message": "Transaction recorded successfully" }

    def update_transaction_status(self, transaction_id: str, new_status: str) -> dict:
        """
        Update the status of a transaction (to completed, failed, pending, etc.).

        Args:
            transaction_id (str): Unique identifier for the transaction to update.
            new_status (str): The new status value for the transaction.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction status updated."
            }
            or
            {
                "success": False,
                "error": "Transaction not found."
            }

        Constraints:
            - The given transaction_id must exist in the system.
            - Any string is accepted for the new_status.
        """
        txn = self.transactions.get(transaction_id)
        if not txn:
            return { "success": False, "error": "Transaction not found." }

        txn['status'] = new_status
        return { "success": True, "message": "Transaction status updated." }

    def add_contact(self, user_id: str, contact_user_id: str) -> dict:
        """
        Add a new contact to the user's contact list.

        Args:
            user_id (str): The ID of the user adding the contact.
            contact_user_id (str): The ID of the user to be added as a contact.

        Returns:
            dict: 
                - { "success": True, "message": "Contact added successfully" }
                - { "success": False, "error": "reason" }

        Constraints:
            - Both user_id and contact_user_id must exist.
            - Users cannot add themselves as a contact.
            - Cannot add a contact that is already present.
        """
        # Check that both users exist
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if contact_user_id not in self.users:
            return { "success": False, "error": "Contact user does not exist" }
        if user_id == contact_user_id:
            return { "success": False, "error": "Cannot add self as a contact" }
        # Initialize contact list if needed
        if user_id not in self.contacts:
            self.contacts[user_id] = []
        # Check whether the contact already exists
        for contact in self.contacts[user_id]:
            if contact["contact_user_id"] == contact_user_id:
                return { "success": False, "error": "Contact already exists" }
        # Add the new contact
        contact_entry = {"_id": user_id, "contact_user_id": contact_user_id}
        self.contacts[user_id].append(contact_entry)
        return { "success": True, "message": "Contact added successfully" }

    def update_account_balance(self, account_id: str, amount_delta: float, currency: str) -> dict:
        """
        Adjust a user’s account balance by `amount_delta`. Used internally for send_payment/request_payment.

        Args:
            account_id (str): The account's unique identifier.
            amount_delta (float): The value to add (or subtract) from the current balance.
            currency (str): The currency of the adjustment, must match the account currency.

        Returns:
            dict:
                - success (bool): Whether the update succeeded.
                - message (str): On success, confirmation message.
                - error (str): On failure, reason for failure.

        Constraints:
            - Account must exist.
            - Account's currency must match the provided currency.
            - Account must be active (via lookup from users/account_status if enforced).
            - Balance cannot go negative after adjustment.
        """
        # Confirm account exists
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist."}

        # Currency match
        if account["currency"] != currency:
            return {"success": False, "error": "Currency mismatch."}

        # Optionally check account status (if implemented, e.g., 'active')
        # Find user for this account
        user_id = None
        for uid, user in self.users.items():
            if user.get("_id") == account_id:
                user_id = uid
                break
        if user_id is None:
            # There may not be a 1:1 ID match. Try to find the user whose account is this ID
            for uid, user in self.users.items():
                acc_id = user.get("_id", None)
                if acc_id == account_id:
                    user_id = uid
                    break
        # If we can determine account status from the account info itself, use that.
        # Assuming we need to look up in self.users
        for user in self.users.values():
            if user.get("_id") == account_id:
                account_status = user.get("account_status", "active")
                if account_status != "active":
                    return {"success": False, "error": "Account is not active."}

        # Check that balance after update is not negative
        new_balance = account["balance"] + amount_delta
        if new_balance < 0:
            return {"success": False, "error": "Insufficient funds: balance cannot go negative."}

        # Perform update
        account["balance"] = new_balance
        self.accounts[account_id] = account

        return {"success": True, "message": "Account balance updated."}

    def mark_authentication_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's authentication status (e.g., login or logout).

        Args:
            user_id (str): The unique identifier of the user.
            new_status (str): New authentication status (e.g., 'authenticated', 'unauthenticated').

        Returns:
            dict: 
                - On success: {"success": True, "message": "User authentication status updated"}
                - On failure: {"success": False, "error": "reason"}
    
        Constraints:
            - The user_id must exist in the system.
            - new_status must be a non-empty string.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid authentication status" }

        self.users[user_id]["authentication_status"] = new_status.strip()
        return { "success": True, "message": "User authentication status updated" }

    def set_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Activate, suspend, deactivate, or close a user account by updating the 'account_status' field.

        Args:
            user_id (str): The unique identifier of the user whose account is to be updated.
            new_status (str): The new status for the account (e.g., "active", "suspended", "deactivated", "closed").

        Returns:
            dict:
              On success:
                {"success": True, "message": "Account status updated to <new_status> for user <user_id>."}
              On failure:
                {"success": False, "error": "<reason>"}

        Constraints:
            - user_id must correspond to an existing user.
            - new_status should generally be "active", "suspended", "deactivated", or "closed".
        """
        allowed_statuses = ["active", "suspended", "deactivated", "closed"]
        if user_id not in self.users:
            return {"success": False, "error": "User ID does not exist."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed: {', '.join(allowed_statuses)}"}

        self.users[user_id]["account_status"] = new_status
        return {
            "success": True,
            "message": f"Account status updated to {new_status} for user {user_id}."
        }


class VenmoPeerToPeerPaymentSystem(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_display_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_display_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def check_user_authentication_status(self, **kwargs):
        return self._call_inner_tool('check_user_authentication_status', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def get_account_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_user_id', kwargs)

    def get_account_balance(self, **kwargs):
        return self._call_inner_tool('get_account_balance', kwargs)

    def get_contacts_for_user(self, **kwargs):
        return self._call_inner_tool('get_contacts_for_user', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def list_transactions_for_user(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_user', kwargs)

    def check_transaction_id_unique(self, **kwargs):
        return self._call_inner_tool('check_transaction_id_unique', kwargs)

    def send_payment(self, **kwargs):
        return self._call_inner_tool('send_payment', kwargs)

    def request_payment(self, **kwargs):
        return self._call_inner_tool('request_payment', kwargs)

    def record_transaction(self, **kwargs):
        return self._call_inner_tool('record_transaction', kwargs)

    def update_transaction_status(self, **kwargs):
        return self._call_inner_tool('update_transaction_status', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def update_account_balance(self, **kwargs):
        return self._call_inner_tool('update_account_balance', kwargs)

    def mark_authentication_status(self, **kwargs):
        return self._call_inner_tool('mark_authentication_status', kwargs)

    def set_account_status(self, **kwargs):
        return self._call_inner_tool('set_account_status', kwargs)
