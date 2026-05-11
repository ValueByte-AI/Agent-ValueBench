# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
from typing import List, Optional



class AccountInfo(TypedDict):
    account_id: str
    account_name: str
    user_id: str

class BreachInfo(TypedDict):
    breach_id: str
    source: str
    description: str
    breach_timestamp: str

class AccountBreachInfo(TypedDict):
    account_id: str
    breach_id: str
    detected_timestamp: str
    notification_status: str

class UserInfo(TypedDict):
    user_id: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Accounts: {account_id: AccountInfo}
        self.accounts: Dict[str, AccountInfo] = {}
        # Breaches: {breach_id: BreachInfo}
        self.breaches: Dict[str, BreachInfo] = {}
        # AccountBreaches: {account_id: List[AccountBreachInfo]}
        self.account_breaches: Dict[str, List[AccountBreachInfo]] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Only breaches with breach_timestamp within a defined "recent" period are considered in alerting.
        # - notification_status in AccountBreach controls whether alerts must be sent again for an account-breach pair.
        # - An account can be associated with multiple breaches, and each breach can impact multiple accounts.
        # - Accounts must be uniquely identifiable.

    @staticmethod
    def _parse_iso_timestamp(raw_timestamp: str) -> datetime.datetime:
        if not isinstance(raw_timestamp, str) or not raw_timestamp.strip():
            raise ValueError("timestamp must be a non-empty string")
        normalized = raw_timestamp.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(datetime.timezone.utc)

    def get_account_by_name(self, account_name: str) -> dict:
        """
        Retrieve account information using an account_name.

        Args:
            account_name (str): The name of the account to search for.

        Returns:
            dict:
                - If found: {"success": True, "data": AccountInfo}
                - If not found: {"success": False, "error": "Account not found"}

        Constraints:
            - Accounts are uniquely identifiable (typically via account_id).
            - Returns the first match for the given account_name.
        """
        for account in self.accounts.values():
            if account["account_name"] == account_name:
                return {"success": True, "data": account}
        return {"success": False, "error": "Account not found"}

    def get_account_by_id(self, account_id: str) -> dict:
        """
        Retrieve detailed account information using account_id.

        Args:
            account_id (str): The unique identifier for the account.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": AccountInfo  # Account details dictionary
                }
                or
                {
                    "success": False,
                    "error": str  # Explanation if the account does not exist
                }
        Constraints:
            - The account with the given account_id must exist.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found"}
        return {"success": True, "data": self.accounts[account_id]}

    def list_accounts_by_user(self, user_id: str) -> dict:
        """
        Get all accounts belonging to a specific user.

        Args:
            user_id (str): The user identifier for which to retrieve accounts.

        Returns:
            dict: {
                "success": True,
                "data": List[AccountInfo]  # List of accounts for the user, may be empty
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "User does not exist"
            }

        Constraints:
            - user_id must exist in the system (self.users).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        accounts_for_user = [
            account_info for account_info in self.accounts.values()
            if account_info["user_id"] == user_id
        ]

        return {"success": True, "data": accounts_for_user}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information (user_id and contact_info) by user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: 
                - {"success": True, "data": UserInfo} if user exists.
                - {"success": False, "error": "User not found"} if user_id not present.

        Constraints:
            - User must exist in self.users.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def get_user_contact_info(self, user_id: str) -> dict:
        """
        Retrieve the contact information for a user given their user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # Contact info for the user
            }
            or
            {
                "success": False,
                "error": str  # Error message if user is not found
            }

        Constraints:
            - The user must exist (identified uniquely by user_id).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user["contact_info"] }

    def list_account_breaches(self, account_id: str) -> dict:
        """
        Retrieve all breach records (AccountBreachInfo) for the specified account_id.

        Args:
            account_id (str): The unique identifier of the account.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[AccountBreachInfo]  # May be empty if no breaches
                }
                or
                {
                    "success": False,
                    "error": str  # Reason, e.g. "Account does not exist"
                }

        Constraints:
            - account_id must exist in the system.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        breach_list = self.account_breaches.get(account_id, [])

        return { "success": True, "data": breach_list }

    def get_breach_by_id(self, breach_id: str) -> dict:
        """
        Retrieve details (metadata) of a breach by its unique breach_id.

        Args:
            breach_id (str): The breach identifier to look up.

        Returns:
            dict:
                - If found:
                    {
                        "success": True,
                        "data": BreachInfo  # The breach metadata
                    }
                - If not found:
                    {
                        "success": False,
                        "error": "Breach not found"
                    }

        Constraints:
            - breach_id must exist in the breaches database.
        """
        if breach_id not in self.breaches:
            return { "success": False, "error": "Breach not found" }
        return { "success": True, "data": self.breaches[breach_id] }

    def list_breaches_for_account(self, account_id: str) -> dict:
        """
        Get all BreachInfo objects impacting the given account_id.

        Args:
            account_id (str): The ID of the account whose impacting breaches are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[BreachInfo],  # List of BreachInfo dicts impacting this account
            }
            or
            {
                "success": False,
                "error": str  # If account does not exist
            }

        Constraints:
            - The account_id must exist in the system.
            - Only returns breaches actually recorded by AccountBreach relation.
            - If a breach referenced by AccountBreachInfo is missing, it is skipped.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}

        breaches_info = []
        for ab in self.account_breaches.get(account_id, []):
            breach_id = ab.get("breach_id")
            if breach_id in self.breaches:
                breaches_info.append(self.breaches[breach_id])

        return {"success": True, "data": breaches_info}


    def filter_recent_breaches(self, breach_ids: List[str], cutoff_timestamp: Optional[str] = None) -> dict:
        """
        Filter a list of breaches to only those considered "recent" per system policy.

        Args:
            breach_ids (List[str]): List of breach IDs to check.
            cutoff_timestamp (str, optional): ISO format timestamp representing minimum "recent" time.
                If None, defaults to 30 days ago from now.

        Returns:
            dict: {
                "success": True,
                "data": List[BreachInfo],  # List of recent breaches' info
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Only include breaches whose breach_timestamp >= cutoff_timestamp.
            - Timestamps should be compared in ISO format.
            - If breach_ids not found, skip them.
        """
        if not isinstance(breach_ids, list):
            return { "success": False, "error": "breach_ids must be a list" }

        candidate_breaches = []
        for breach_id in breach_ids:
            breach = self.breaches.get(breach_id)
            if breach is None:
                continue
            breach_ts_raw = breach.get("breach_timestamp")
            if not breach_ts_raw:
                continue
            try:
                breach_ts = self._parse_iso_timestamp(breach_ts_raw)
            except Exception:
                continue
            candidate_breaches.append((breach, breach_ts))

        # Determine cutoff timestamp without consulting host time.
        if cutoff_timestamp is None:
            if not candidate_breaches:
                return {"success": True, "data": []}
            cutoff_dt = max(ts for _, ts in candidate_breaches) - datetime.timedelta(days=30)
        else:
            try:
                cutoff_dt = self._parse_iso_timestamp(cutoff_timestamp)
            except Exception:
                return { "success": False, "error": "cutoff_timestamp must be ISO format" }

        recent_breaches: List[BreachInfo] = []
        for breach, breach_ts in candidate_breaches:
            if breach_ts >= cutoff_dt:
                recent_breaches.append(breach)

        return { "success": True, "data": recent_breaches }

    def get_notification_status(self, account_id: str, breach_id: str) -> dict:
        """
        Retrieve the notification_status for a specific account_id and breach_id.

        Args:
            account_id (str): The monitored account's unique ID.
            breach_id (str): The unique ID of the breach event.

        Returns:
            dict: {
                "success": True,
                "data": str  # notification_status, e.g. "notified", "pending"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Account with account_id must exist.
            - There must be a mapping for (account_id, breach_id) in account_breaches.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}

        breaches = self.account_breaches.get(account_id, [])
        for ab in breaches:
            if ab["breach_id"] == breach_id:
                return {"success": True, "data": ab["notification_status"]}
        return {"success": False, "error": "No breach mapping found for given account and breach"}

    def list_accounts(self) -> dict:
        """
        List all accounts being monitored by the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AccountInfo]  # A list of all accounts (can be empty)
            }

        Constraints:
            - None specific to listing; always succeeds.
        """
        all_accounts = list(self.accounts.values())
        return {"success": True, "data": all_accounts}

    def update_notification_status(self, account_id: str, breach_id: str, notification_status: str) -> dict:
        """
        Update the notification_status value for a given account-breach pair.

        Args:
            account_id (str): The ID of the account.
            breach_id (str): The ID of the breach.
            notification_status (str): The new notification status value.

        Returns:
            dict: {
                "success": True,
                "message": "Notification status updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The account and breach must both exist.
            - The account must be associated with the given breach.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist." }
        if breach_id not in self.breaches:
            return { "success": False, "error": "Breach does not exist." }
        if account_id not in self.account_breaches:
            return { "success": False, "error": "No breaches recorded for this account." }

        for abinfo in self.account_breaches[account_id]:
            if abinfo["breach_id"] == breach_id:
                abinfo["notification_status"] = notification_status
                return { "success": True, "message": "Notification status updated successfully." }

        return { "success": False, "error": "No such breach associated with the provided account." }

    def add_account_breach(
        self,
        account_id: str,
        breach_id: str,
        detected_timestamp: str,
        notification_status: str
    ) -> dict:
        """
        Add a new breach association for an account.

        Args:
            account_id (str): The id of the account to associate.
            breach_id (str): The id of the breach to associate.
            detected_timestamp (str): When the impact was detected (string/timestamp).
            notification_status (str): Notification status for this account-breach pair.

        Returns:
            dict: {
                "success": True,
                "message": "... successfully added ..."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - account_id must exist in the system.
            - breach_id must exist in the system.
            - Should not create duplicate AccountBreach for the same (account_id, breach_id).
        """
        if account_id not in self.accounts:
            return {"success": False, "error": f"Account {account_id} does not exist"}
        if breach_id not in self.breaches:
            return {"success": False, "error": f"Breach {breach_id} does not exist"}

        breaches = self.account_breaches.get(account_id, [])
        for ab in breaches:
            if ab["breach_id"] == breach_id:
                return {
                    "success": False,
                    "error": f"Association between account {account_id} and breach {breach_id} already exists"
                }
        new_entry = {
            "account_id": account_id,
            "breach_id": breach_id,
            "detected_timestamp": detected_timestamp,
            "notification_status": notification_status
        }
        if account_id not in self.account_breaches:
            self.account_breaches[account_id] = []
        self.account_breaches[account_id].append(new_entry)
        return {
            "success": True,
            "message": f"AccountBreach association added for account {account_id} and breach {breach_id}"
        }

    def add_account(self, account_id: str, account_name: str, user_id: str) -> dict:
        """
        Add a new account to the system.

        Args:
            account_id (str): Unique identifier for the account.
            account_name (str): The account name (e.g., email address).
            user_id (str): The user to whom this account belongs; must exist in the system.

        Returns:
            dict: {
                "success": True,
                "message": "Account added successfully."
            }
            OR
            {
                "success": False,
                "error": reason string
            }

        Constraints:
            - account_id must be unique.
            - user_id must exist in the system.
            - All arguments must be non-empty strings.
        """
        # Validate input presence
        if not account_id or not isinstance(account_id, str):
            return { "success": False, "error": "account_id must be a non-empty string." }
        if not account_name or not isinstance(account_name, str):
            return { "success": False, "error": "account_name must be a non-empty string." }
        if not user_id or not isinstance(user_id, str):
            return { "success": False, "error": "user_id must be a non-empty string." }

        # Check account ID uniqueness
        if account_id in self.accounts:
            return { "success": False, "error": "Account with this account_id already exists." }

        # Check that user_id exists
        if user_id not in self.users:
            return { "success": False, "error": "user_id does not exist in the system." }

        # Add the account
        self.accounts[account_id] = {
            "account_id": account_id,
            "account_name": account_name,
            "user_id": user_id
        }

        # Initialize account_breaches for this account
        if account_id not in self.account_breaches:
            self.account_breaches[account_id] = []

        return { "success": True, "message": "Account added successfully." }

    def add_breach(
        self,
        breach_id: str,
        source: str,
        description: str,
        breach_timestamp: str
    ) -> dict:
        """
        Add a new security breach record.

        Args:
            breach_id (str): Unique identifier for the breach.
            source (str): Source/system from which the breach originated.
            description (str): Description of what the breach involves.
            breach_timestamp (str): ISO or string-encoded time when the breach occurred.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Breach record added successfully."}
                On failure:
                    {"success": False, "error": "..."}
    
        Constraints:
            - breach_id must be unique; if it exists, must not overwrite existing breach.
            - All fields are required and must not be empty.
        """
        if not breach_id or not source or not description or not breach_timestamp:
            return {"success": False, "error": "All fields are required and must not be empty."}
        if breach_id in self.breaches:
            return {"success": False, "error": "Breach ID already exists."}
    
        self.breaches[breach_id] = {
            "breach_id": breach_id,
            "source": source,
            "description": description,
            "breach_timestamp": breach_timestamp
        }
        return {"success": True, "message": "Breach record added successfully."}

    def add_user(self, user_id: str, contact_info: str) -> dict:
        """
        Register a new user in the account breach monitoring system.

        Args:
            user_id (str): Unique identifier for the user.
            contact_info (str): User's contact information (email, phone, etc.).

        Returns:
            dict: 
                - On success: {"success": True, "message": "User added successfully."}
                - On failure: {"success": False, "error": "User ID already exists."} or other error description.

        Constraints:
            - user_id must be unique within the system.
            - contact_info must not be empty.
        """
        if not user_id or not contact_info:
            return { "success": False, "error": "user_id and contact_info must be provided." }
    
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists." }

        self.users[user_id] = {
            "user_id": user_id,
            "contact_info": contact_info
        }
        return { "success": True, "message": "User added successfully." }

    def remove_account_breach(self, account_id: str, breach_id: str) -> dict:
        """
        Remove an existing breach association from an account.
    
        Args:
            account_id (str): The ID of the account.
            breach_id (str): The ID of the breach to remove for this account.

        Returns:
            dict: {
                "success": True,
                "message": "Breach removed from account."
            }
            or
            {
                "success": False,
                "error": "No such breach association for account."  # Or account not found
            }

        Constraints:
            - The account must exist.
            - The breach association (account_id + breach_id) must exist.
            - Removing the mapping does not affect other data.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist." }
        if account_id not in self.account_breaches:
            return { "success": False, "error": "No breach associations for this account." }
    
        breach_list = self.account_breaches[account_id]
        initial_len = len(breach_list)
        # Keep only those that do NOT match the breach_id to remove
        new_breach_list = [ab for ab in breach_list if ab["breach_id"] != breach_id]
    
        if len(new_breach_list) == initial_len:
            return { "success": False, "error": "No such breach association for account." }
    
        self.account_breaches[account_id] = new_breach_list
        return { "success": True, "message": "Breach removed from account." }


class AccountBreachMonitoringSystem(BaseEnv):
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

    def get_account_by_name(self, **kwargs):
        return self._call_inner_tool('get_account_by_name', kwargs)

    def get_account_by_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_id', kwargs)

    def list_accounts_by_user(self, **kwargs):
        return self._call_inner_tool('list_accounts_by_user', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_contact_info(self, **kwargs):
        return self._call_inner_tool('get_user_contact_info', kwargs)

    def list_account_breaches(self, **kwargs):
        return self._call_inner_tool('list_account_breaches', kwargs)

    def get_breach_by_id(self, **kwargs):
        return self._call_inner_tool('get_breach_by_id', kwargs)

    def list_breaches_for_account(self, **kwargs):
        return self._call_inner_tool('list_breaches_for_account', kwargs)

    def filter_recent_breaches(self, **kwargs):
        return self._call_inner_tool('filter_recent_breaches', kwargs)

    def get_notification_status(self, **kwargs):
        return self._call_inner_tool('get_notification_status', kwargs)

    def list_accounts(self, **kwargs):
        return self._call_inner_tool('list_accounts', kwargs)

    def update_notification_status(self, **kwargs):
        return self._call_inner_tool('update_notification_status', kwargs)

    def add_account_breach(self, **kwargs):
        return self._call_inner_tool('add_account_breach', kwargs)

    def add_account(self, **kwargs):
        return self._call_inner_tool('add_account', kwargs)

    def add_breach(self, **kwargs):
        return self._call_inner_tool('add_breach', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def remove_account_breach(self, **kwargs):
        return self._call_inner_tool('remove_account_breach', kwargs)
