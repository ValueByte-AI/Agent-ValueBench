# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime



class FundInfo(TypedDict):
    fund_id: str
    name: str
    characteristics: str
    assigned_manager_id: str  # Fund manager assigned to this fund
    status: str

class FundManagerInfo(TypedDict):
    manager_id: str
    name: str
    license_status: str
    assigned_fund: str  # Fund currently managed (can be empty if unassigned)

class ClientInfo(TypedDict):
    client_id: str
    name: str
    account_status: str
    associated_fund: str  # Fund client is associated with

class TransactionInfo(TypedDict):
    transaction_id: str
    fund_id: str
    client_id: str
    date: str
    amount: float
    transaction_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for investment management.
        """
        # Funds: {fund_id: FundInfo}
        self.funds: Dict[str, FundInfo] = {}

        # Fund Managers: {manager_id: FundManagerInfo}
        self.fund_managers: Dict[str, FundManagerInfo] = {}

        # Clients: {client_id: ClientInfo}
        self.clients: Dict[str, ClientInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Constraints:
        # - Each fund must have zero or one assigned fund manager at a given time.
        # - Only active/authorized fund managers can be assigned to manage funds.
        # - A fund’s assignment to a manager must be valid as of the current (or any queried) date.
        # - Each transaction must reference existing clients and funds.
        # - Compliance checks may restrict which funds a manager can be assigned to, based on regulatory requirements.

    def get_fund_manager_by_id(self, manager_id: str) -> dict:
        """
        Retrieve details (name, status, assignments) of a fund manager by manager_id.

        Args:
            manager_id (str): The unique ID of the target fund manager.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": FundManagerInfo}
                - If not found:
                    {"success": False, "error": "Fund manager not found"}

        Constraints:
            - manager_id must exist in self.fund_managers.
        """
        fund_manager = self.fund_managers.get(manager_id)
        if fund_manager is None:
            return { "success": False, "error": "Fund manager not found" }
        return { "success": True, "data": fund_manager }

    def list_all_fund_managers(self) -> dict:
        """
        Retrieve all fund managers in the system with their details.

        Returns:
            dict: {
                "success": True,
                "data": List[FundManagerInfo]  # List of all fund managers (can be empty)
            }

        Constraints:
            - No input parameters required.
            - No constraints enforced; returns current state.
        """
        data = list(self.fund_managers.values())
        return { "success": True, "data": data }

    def get_fund_by_id(self, fund_id: str) -> dict:
        """
        Retrieve details about a single fund using its unique fund_id.

        Args:
            fund_id (str): Unique identifier of the fund to query.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": FundInfo
                }
                On failure: {
                    "success": False,
                    "error": "Fund not found"
                }

        Constraints:
            - The fund_id must exist in the system.
        """
        fund = self.funds.get(fund_id)
        if fund is not None:
            return { "success": True, "data": fund }
        else:
            return { "success": False, "error": "Fund not found" }

    def list_funds_by_manager_id(self, manager_id: str) -> dict:
        """
        List all funds that are assigned to a given fund manager.

        Args:
            manager_id (str): The ID of the fund manager.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[FundInfo]  # List of funds with assigned_manager_id == manager_id (may be empty)
                }
                - On error: {
                    "success": False,
                    "error": str  # Reason for failure, e.g., "Manager not found"
                }

        Constraints:
            - Provided manager_id must exist in the fund manager records.
        """
        if manager_id not in self.fund_managers:
            return { "success": False, "error": "Manager not found" }

        result = [
            fund_info for fund_info in self.funds.values()
            if fund_info.get('assigned_manager_id') == manager_id
        ]

        return {
            "success": True,
            "data": result
        }

    def list_all_funds(self) -> dict:
        """
        Retrieve all investment funds in the system, with their details.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[FundInfo]  # List of all funds and their details (possible empty)
                }

        Constraints:
            - None. No user parameters and no constraints beyond returning full fund info table.
        """
        all_funds = list(self.funds.values())
        return { "success": True, "data": all_funds }

    def get_fund_characteristics(self, fund_id: str) -> dict:
        """
        Query the characteristics and status of a fund.

        Args:
            fund_id (str): The unique identifier of the fund.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "characteristics": str,
                    "status": str
                }
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - The fund must exist in the system.
        """
        fund = self.funds.get(fund_id)
        if not fund:
            return { "success": False, "error": "Fund not found" }
        return {
            "success": True,
            "data": {
                "characteristics": fund["characteristics"],
                "status": fund["status"]
            }
        }

    def get_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve client details using client_id.

        Args:
            client_id (str): Unique identifier for the client.

        Returns:
            dict:
                - If found: { "success": True, "data": ClientInfo }
                - If not found: { "success": False, "error": "Client not found" }

        Constraints:
            - The client_id must exist in the current client records.
        """
        client = self.clients.get(client_id)
        if client is None:
            return { "success": False, "error": "Client not found" }
        return { "success": True, "data": client }

    def list_clients_by_fund_id(self, fund_id: str) -> dict:
        """
        List all clients associated with a specific fund.

        Args:
            fund_id (str): The unique identifier of the fund.

        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo],  # List of clients associated with the fund (empty list allowed)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Fund does not exist"
            }

        Constraints:
            - The provided fund_id must exist in the system.
        """
        if fund_id not in self.funds:
            return { "success": False, "error": "Fund does not exist" }

        result = [
            client_info for client_info in self.clients.values()
            if client_info.get('associated_fund') == fund_id
        ]
        return { "success": True, "data": result }

    def list_all_clients(self) -> dict:
        """
        Retrieve all registered clients in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo]  # List of all registered clients (possibly empty)
            }

        Notes:
            - No parameters required.
            - Always succeeds, returning an (possibly empty) list of ClientInfo dicts.
        """
        all_clients = list(self.clients.values())
        return {
            "success": True,
            "data": all_clients
        }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve details for a specific transaction using its transaction_id.

        Args:
            transaction_id (str): The unique identifier for the target transaction.

        Returns:
            dict: If found,
                {
                    "success": True,
                    "data": TransactionInfo,  # Details of the transaction
                }
                If not found,
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

    def list_transactions_by_fund_id(self, fund_id: str) -> dict:
        """
        List all transactions related to a particular fund.

        Args:
            fund_id (str): The unique identifier of the fund.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # List of transactions for the fund (may be empty)
            }
            or
            {
                "success": False,
                "error": str,  # Error message, e.g. "Fund does not exist"
            }

        Constraints:
            - The fund_id must exist in the system.
        """
        if fund_id not in self.funds:
            return { "success": False, "error": "Fund does not exist" }

        result = [
            tx for tx in self.transactions.values()
            if tx["fund_id"] == fund_id
        ]

        return { "success": True, "data": result }

    def list_transactions_by_client_id(self, client_id: str) -> dict:
        """
        List all transactions made by a particular client.

        Args:
            client_id (str): The unique identifier of the client.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": List[TransactionInfo]  # List of TransactionInfo for that client (may be empty)
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Description of the error, e.g., client does not exist.
                }

        Constraints:
            - client_id must exist in the system (self.clients).
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }
    
        result = [
            tx for tx in self.transactions.values()
            if tx["client_id"] == client_id
        ]
        return { "success": True, "data": result }

    def compliance_check_manager_assignment(self, manager_id: str, fund_id: str) -> dict:
        """
        Check if the assignment of a manager to a fund is compliant according to system and regulatory rules.

        Args:
            manager_id (str): The ID of the fund manager.
            fund_id (str): The ID of the fund to which assignment is considered.

        Returns:
            dict:
                - On compliance check success (regardless of compliance): 
                    {
                        "success": True,
                        "data": { 
                            "compliant": True/False,
                            "reason": str (if not compliant)
                         }
                    }
                - On failure due to not found entities: 
                    { "success": False, "error": str }

        Constraints checked:
            - Fund manager and fund must exist.
            - Fund manager must be 'active' or 'authorized' in license_status.
            - Additional system-specific compliance logic can be inserted as necessary.
        """
        # Check that manager exists
        if manager_id not in self.fund_managers:
            return { "success": False, "error": "Fund manager not found" }
        # Check that fund exists
        if fund_id not in self.funds:
            return { "success": False, "error": "Fund not found" }

        manager = self.fund_managers[manager_id]
        fund = self.funds[fund_id]

        # Check license status
        if manager["license_status"].lower() not in ["active", "authorized"]:
            return {
                "success": True,
                "data": {
                    "compliant": False,
                    "reason": "Manager license is not active/authorized"
                }
            }

        # (Place for additional compliance rules)
        # For now, assume additional compliance (e.g., certifications, fund traits) are not encoded

        return {
            "success": True,
            "data": { 
                "compliant": True
            }
        }

    def check_manager_license_status(self, manager_id: str) -> dict:
        """
        Query the license_status of a specified fund manager.

        Args:
            manager_id (str): The identifier of the fund manager to query.

        Returns:
            dict:
                - If found: { "success": True, "data": <license_status: str> }
                - If not found: { "success": False, "error": "Fund manager not found" }

        Constraints:
            - manager_id must exist in the fund_managers registry.
        """
        manager = self.fund_managers.get(manager_id)
        if not manager:
            return { "success": False, "error": "Fund manager not found" }
        return { "success": True, "data": manager["license_status"] }

    def check_fund_assignment_valid_on_date(self, fund_id: str, date: str = None) -> dict:
        """
        Verify if a fund’s assignment to a manager is valid as of a specific date (or current date).
        Due to data model limitations, only current assignment can be checked.

        Args:
            fund_id (str): Fund ID to verify assignment for.
            date (str, optional): Date as 'YYYY-MM-DD'. If provided and not today, only current can be checked.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "is_valid": bool,           # Whether the fund is validly assigned to a manager
                    "reason": str               # Explanation for the assessment
                }
            }
            or
            {
                "success": False,
                "error": str                   # Error explanation (e.g. fund not found)
            }

        Constraints:
            - Fund must exist.
            - Only current assignments can be inspected (no history as of arbitrary dates).
            - Manager must exist and have active/authorized license.
        """

        # Check if fund exists
        fund = self.funds.get(fund_id)
        if fund is None:
            return {"success": False, "error": "Fund does not exist"}

        # Check assignment
        manager_id = fund.get("assigned_manager_id")
        if not manager_id:
            return {
                "success": True,
                "data": {
                    "is_valid": False,
                    "reason": "Invalid: No manager assigned to fund."
                }
            }

        manager = self.fund_managers.get(manager_id)
        if manager is None:
            return {
                "success": True,
                "data": {
                    "is_valid": False,
                    "reason": "Invalid: Assigned manager does not exist."
                }
            }

        # Check active/authorized manager (license_status)
        if manager.get("license_status", "").lower() not in ["active", "authorized"]:
            return {
                "success": True,
                "data": {
                    "is_valid": False,
                    "reason": f"Invalid: Manager's license status is '{manager.get('license_status', '')}', not active/authorized."
                }
            }

        # Date logic: if date is provided but not 'today'
        if date:
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            if date != today_str:
                return {
                    "success": True,
                    "data": {
                        "is_valid": False,
                        "reason": (
                            "Historical assignment queries are not supported: "
                            "system only tracks current assignment."
                        )
                    }
                }

        # All checks passed
        return {
            "success": True,
            "data": {
                "is_valid": True,
                "reason": "Valid: Manager is assigned and license is active/authorized."
            }
        }

    def list_funds_without_manager(self) -> dict:
        """
        List all funds that currently have no assigned manager.

        Returns:
            dict:
                success (bool): True if the operation was successful.
                data (List[FundInfo]): A list of FundInfo dicts for all funds where assigned_manager_id
                                       is missing, empty string, or None.

        Constraints:
            - N/A for this query operation.

        Edge Cases:
            - If there are no funds, returns an empty data list with success True.
            - If all funds have managers, same behavior (empty list).
        """
        result = [
            fund_info for fund_info in self.funds.values()
            if not fund_info.get("assigned_manager_id")
        ]
        return {"success": True, "data": result}

    def assign_manager_to_fund(self, fund_id: str, manager_id: str) -> dict:
        """
        Assign or reassign a fund manager to a fund (updates assigned_manager_id and FundManager.assigned_fund),
        subject to compliance and status rules.

        Args:
            fund_id (str): The unique identifier of the fund.
            manager_id (str): The unique identifier of the manager.

        Returns:
            dict:
                On success: { "success": True, "message": "Manager <manager_id> assigned to fund <fund_id>." }
                On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Fund and manager must exist.
            - Manager's license_status must be 'active' or 'authorized'.
            - Compliance check must succeed.
            - Manager can only be assigned to one fund; fund can only have one manager.
            - Existing assignments will be replaced (if any).
        """
        # Check fund existence
        if fund_id not in self.funds:
            return { "success": False, "error": f"Fund '{fund_id}' does not exist." }
        # Check manager existence
        if manager_id not in self.fund_managers:
            return { "success": False, "error": f"Manager '{manager_id}' does not exist." }

        manager_info = self.fund_managers[manager_id]
        fund_info = self.funds[fund_id]

        # Check manager license status
        if manager_info["license_status"].lower() not in ("active", "authorized"):
            return { "success": False, "error": "Manager is not active/authorized." }

        # Simulate compliance check (assume presence of compliance_check_manager_assignment)
        if hasattr(self, "compliance_check_manager_assignment"):
            cc_result = self.compliance_check_manager_assignment(manager_id, fund_id)
            if not (isinstance(cc_result, dict) and cc_result.get("success", False)):
                error_msg = cc_result.get("error", "Compliance check failed.") if isinstance(cc_result, dict) else "Compliance check failed."
                return { "success": False, "error": error_msg }

        # Remove this manager from previous fund assignment (if any)
        previous_fund_id = manager_info.get("assigned_fund")
        if previous_fund_id and previous_fund_id != fund_id:
            if previous_fund_id in self.funds:
                self.funds[previous_fund_id]["assigned_manager_id"] = ""
            # Remove assignment
            manager_info["assigned_fund"] = ""

        # Remove previous manager from this fund (if any)
        prev_manager_id = fund_info.get("assigned_manager_id")
        if prev_manager_id and prev_manager_id != manager_id and prev_manager_id in self.fund_managers:
            self.fund_managers[prev_manager_id]["assigned_fund"] = ""

        # Assign manager to fund
        fund_info["assigned_manager_id"] = manager_id
        manager_info["assigned_fund"] = fund_id

        return { "success": True, "message": f"Manager '{manager_id}' assigned to fund '{fund_id}'." }

    def remove_manager_from_fund(self, fund_id: str) -> dict:
        """
        Unassign a manager from a fund, leaving the fund with no manager.

        Args:
            fund_id (str): The unique identifier of the fund whose manager should be removed.

        Returns:
            dict: 
                { "success": True, "message": "Manager unassigned from fund <fund_id>" }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - The fund must exist.
            - The fund must have an assigned manager.
            - The manager's `assigned_fund` will also be cleared if they exist in the system.
        """
        fund = self.funds.get(fund_id)
        if not fund:
            return { "success": False, "error": f"Fund with id '{fund_id}' does not exist." }
    
        manager_id = fund.get("assigned_manager_id", "")
        if not manager_id:
            return { "success": False, "error": f"Fund '{fund_id}' has no assigned manager." }

        # Clear the assignment in the fund
        self.funds[fund_id]["assigned_manager_id"] = ""
    
        # Also clear in FundManager if present and pointing to this fund
        manager = self.fund_managers.get(manager_id)
        if manager and manager.get("assigned_fund") == fund_id:
            self.fund_managers[manager_id]["assigned_fund"] = ""

        return { "success": True, "message": f"Manager unassigned from fund {fund_id}" }

    def update_fund_status(self, fund_id: str, new_status: str) -> dict:
        """
        Change the status of a fund to a new value (e.g., activate, close, suspend etc).

        Args:
            fund_id (str): The ID of the fund whose status should be updated.
            new_status (str): The new status value for the fund.

        Returns:
            dict: {
                "success": True,
                "message": "Status of fund <fund_id> updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "Fund not found"
            }

        Constraints:
            - Fund with given fund_id must exist in the system.
            - No restriction on the allowed status values.
        """
        if fund_id not in self.funds:
            return { "success": False, "error": "Fund not found" }

        self.funds[fund_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Status of fund {fund_id} updated to {new_status}"
        }

    def update_manager_license_status(self, manager_id: str, license_status: str) -> dict:
        """
        Update the license_status (e.g., active, suspended, expired) of a fund manager.

        Args:
            manager_id (str): The unique identifier of the fund manager.
            license_status (str): The new license status for the manager.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message on successful update
            } or {
                "success": False,
                "error": str  # Error message on failure (e.g., manager not found)
            }

        Constraints:
            - Fund manager must exist in the system.
        """
        if manager_id not in self.fund_managers:
            return {
                "success": False,
                "error": f"Fund manager with ID '{manager_id}' does not exist"
            }
        # Optional: Enforce non-empty string for license_status
        if not isinstance(license_status, str) or not license_status.strip():
            return {
                "success": False,
                "error": "license_status must be a non-empty string"
            }
        self.fund_managers[manager_id]["license_status"] = license_status.strip()
        return {
            "success": True,
            "message": f"Updated license_status for manager {manager_id} to '{license_status.strip()}'"
        }

    def add_fund(
        self,
        fund_id: str,
        name: str,
        characteristics: str,
        assigned_manager_id: str,
        status: str
    ) -> dict:
        """
        Create a new investment fund with the given attributes.

        Args:
            fund_id (str): Unique ID for the fund (must not already exist)
            name (str): Name of the fund
            characteristics (str): Description of fund properties
            assigned_manager_id (str): Manager assigned to this fund (may be empty for unassigned)
            status (str): Fund status (e.g., 'active', 'inactive', etc.)

        Returns:
            dict: {
                "success": True, "message": "Fund <fund_id> added successfully."
            }
            or
            dict: {
                "success": False, "error": "reason for failure"
            }

        Constraints:
            - fund_id must be unique.
            - If assigned_manager_id is not empty, it must exist and the manager's license_status must be active/authorized.
            - Each fund can have zero or one assigned manager.
        """
        # Check for unique fund_id
        if fund_id in self.funds:
            return {"success": False, "error": f"Fund ID '{fund_id}' already exists."}

        # Basic input validation
        if not name.strip():
            return {"success": False, "error": "Fund name cannot be empty."}
        if not characteristics.strip():
            return {"success": False, "error": "Fund characteristics cannot be empty."}

        # Manager assignment validation
        assigned_id = assigned_manager_id.strip()
        if assigned_id:
            manager = self.fund_managers.get(assigned_id)
            if not manager:
                return {"success": False, "error": f"Assigned fund manager '{assigned_id}' does not exist."}
            # Only active/authorized managers allowed (assuming 'active' or 'authorized' are acceptable statuses)
            # We'll consider both 'active' and 'authorized' as permitted values for compatibility.
            if manager["license_status"].lower() not in {"active", "authorized"}:
                return {"success": False, "error": f"Assigned manager '{assigned_id}' is not authorized (license status: {manager['license_status']})."}

        # All validation passed, add to funds
        self.funds[fund_id] = {
            "fund_id": fund_id,
            "name": name,
            "characteristics": characteristics,
            "assigned_manager_id": assigned_id,
            "status": status
        }
        return {"success": True, "message": f"Fund '{fund_id}' added successfully."}

    def add_fund_manager(self, manager_id: str, name: str, license_status: str, assigned_fund: str = "") -> dict:
        """
        Create a new fund manager entry.

        Args:
            manager_id (str): Unique identifier for the fund manager.
            name (str): Name of the fund manager.
            license_status (str): License status of the manager.
            assigned_fund (str, optional): Fund ID assigned to this manager (default: "").

        Returns:
            dict: {
                "success": True,
                "message": "Fund manager added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - manager_id must be unique.
            - assigned_fund, if provided and not empty, must refer to an existing fund.
        """
        if not manager_id or not name or not license_status:
            return {"success": False, "error": "manager_id, name, and license_status are required."}

        if manager_id in self.fund_managers:
            return {"success": False, "error": "Manager with this ID already exists."}

        if assigned_fund:
            if assigned_fund not in self.funds:
                return {"success": False, "error": "Assigned fund does not exist."}
            # Additional check: ensure the fund does not already have a manager
            if self.funds[assigned_fund].get("assigned_manager_id"):
                return {"success": False, "error": "Fund already has an assigned manager."}

        self.fund_managers[manager_id] = {
            "manager_id": manager_id,
            "name": name,
            "license_status": license_status,
            "assigned_fund": assigned_fund
        }

        # If assigned_fund, update the fund as well to set assigned_manager_id
        if assigned_fund:
            self.funds[assigned_fund]["assigned_manager_id"] = manager_id

        return {"success": True, "message": "Fund manager added successfully."}

    def add_client(
        self,
        client_id: str,
        name: str,
        account_status: str,
        associated_fund: str = ""
    ) -> dict:
        """
        Register a new client into the system.

        Args:
            client_id (str): Unique identifier for the new client.
            name (str): Name of the client.
            account_status (str): Status of the client's account (e.g., 'active', 'inactive').
            associated_fund (str, optional): Fund ID the client is associated with. If not associated, pass empty string.

        Returns:
            dict: {
                "success": True,
                "message": "Client <client_id> added."
            } or {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - client_id must be unique (not already in the system).
            - If associated_fund is specified (not empty), it must exist in the system.
        """
        # Check mandatory fields
        if not client_id or not name or not account_status:
            return {"success": False, "error": "Missing required client information."}

        # Client ID uniqueness
        if client_id in self.clients:
            return {"success": False, "error": f"Client ID '{client_id}' already exists."}

        # Associated fund validity (if not empty)
        if associated_fund and associated_fund not in self.funds:
            return {"success": False, "error": f"Associated fund '{associated_fund}' does not exist."}

        # Add the new client
        client_info: ClientInfo = {
            "client_id": client_id,
            "name": name,
            "account_status": account_status,
            "associated_fund": associated_fund
        }
        self.clients[client_id] = client_info

        return {"success": True, "message": f"Client '{client_id}' added."}

    def add_transaction(
        self,
        transaction_id: str,
        fund_id: str,
        client_id: str,
        date: str,
        amount: float,
        transaction_type: str
    ) -> dict:
        """
        Record a new transaction involving a client and a fund.

        Args:
            transaction_id (str): Unique identifier for the transaction.
            fund_id (str): The fund involved in the transaction (must exist).
            client_id (str): The client involved in the transaction (must exist).
            date (str): Date of transaction (ISO 8601 or similar).
            amount (float): Value of the transaction (should be positive).
            transaction_type (str): Nature of the transaction (buy/sell/transfer, etc).

        Returns:
            dict: {
                "success": True,
                "message": "Transaction <transaction_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - transaction_id must be unique.
            - fund_id and client_id must reference existing fund and client.
        """
        if transaction_id in self.transactions:
            return { "success": False, "error": f"Transaction ID '{transaction_id}' already exists." }

        if fund_id not in self.funds:
            return { "success": False, "error": f"Fund ID '{fund_id}' does not exist." }

        if client_id not in self.clients:
            return { "success": False, "error": f"Client ID '{client_id}' does not exist." }

        if not isinstance(amount, (int, float)) or amount <= 0:
            return { "success": False, "error": "Amount must be a positive number." }

        if not transaction_type or not isinstance(transaction_type, str):
            return { "success": False, "error": "A valid transaction_type must be provided." }

        self.transactions[transaction_id] = {
            "transaction_id": transaction_id,
            "fund_id": fund_id,
            "client_id": client_id,
            "date": date,
            "amount": amount,
            "transaction_type": transaction_type
        }

        return {
            "success": True,
            "message": f"Transaction {transaction_id} added successfully."
        }

    def update_fund_characteristics(self, fund_id: str, new_characteristics: str) -> dict:
        """
        Modify the characteristics/attributes of a fund.

        Args:
            fund_id (str): The ID of the fund whose characteristics will be updated.
            new_characteristics (str): The new characteristics for the fund.
    
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Fund characteristics updated successfully."
                    }
                On failure (e.g., fund not found):
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - The fund specified by fund_id must exist.
        """
        fund = self.funds.get(fund_id)
        if not fund:
            return {"success": False, "error": "Fund not found."}
    
        fund["characteristics"] = new_characteristics
        return {"success": True, "message": "Fund characteristics updated successfully."}

    def update_client_account_status(self, client_id: str, new_status: str) -> dict:
        """
        Change the account_status of a client.

        Args:
            client_id (str): The unique identifier of the client whose account status is to be updated.
            new_status (str): The new account status value to set.

        Returns:
            dict: {
                "success": True,
                "message": "Client account_status updated."
            }
            or
            {
                "success": False,
                "error": "Client not found."
            }
    
        Constraints:
            - The client_id must exist in the system.
            - No restrictions are specified on status value.
        """
        client = self.clients.get(client_id)
        if client is None:
            return { "success": False, "error": "Client not found." }

        client["account_status"] = new_status
        return { "success": True, "message": "Client account_status updated." }

    def remove_fund(self, fund_id: str) -> dict:
        """
        Delete an investment fund from the system, if no transactions or clients reference it.

        Args:
            fund_id (str): The ID of the fund to remove.

        Returns:
            dict: 
                - { "success": True, "message": "Fund <fund_id> removed from the system." }
                - { "success": False, "error": <reason> }

        Constraints:
            - Cannot remove if there are transactions referencing the fund.
            - Cannot remove if there are clients associated with the fund.
            - Updates assigned manager if needed.
        """
        # Check fund exists
        if fund_id not in self.funds:
            return { "success": False, "error": f"Fund {fund_id} does not exist." }

        # Check for transactions referencing the fund
        for txn in self.transactions.values():
            if txn["fund_id"] == fund_id:
                return { 
                    "success": False, 
                    "error": f"Cannot remove fund {fund_id}: transactions exist referencing this fund."
                }
    
        # Check for clients associated to the fund
        for client in self.clients.values():
            if client.get("associated_fund") == fund_id:
                return {
                    "success": False,
                    "error": f"Cannot remove fund {fund_id}: clients are still associated with this fund."
                }

        # Update fund manager if necessary
        assigned_manager_id = self.funds[fund_id].get("assigned_manager_id")
        if assigned_manager_id and assigned_manager_id in self.fund_managers:
            manager = self.fund_managers[assigned_manager_id]
            if manager.get("assigned_fund") == fund_id:
                manager["assigned_fund"] = ""

        # Remove the fund
        del self.funds[fund_id]

        return {
            "success": True,
            "message": f"Fund {fund_id} removed from the system."
        }

    def remove_fund_manager(self, manager_id: str) -> dict:
        """
        Delete a fund manager's record from the system.
        If the manager is currently assigned to any fund, their assignment will be removed (fund.assigned_manager_id set to empty).

        Args:
            manager_id (str): The unique identifier for the fund manager to remove.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Fund manager <manager_id> removed successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Any funds currently assigned to this manager will have their assigned_manager_id cleared.
            - If the manager_id does not exist, operation fails.
        """
        # Check if the manager exists
        if manager_id not in self.fund_managers:
            return { "success": False, "error": f"Fund manager {manager_id} does not exist." }

        # Remove the manager assignment from any funds
        for fund in self.funds.values():
            if fund.get('assigned_manager_id') == manager_id:
                fund['assigned_manager_id'] = ""  # Clear assignment

        # Remove fund manager record
        del self.fund_managers[manager_id]

        return {
            "success": True,
            "message": f"Fund manager {manager_id} removed successfully."
        }

    def remove_client(self, client_id: str) -> dict:
        """
        Delete a client's record from the system.

        Args:
            client_id (str): The unique identifier of the client to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Client <client_id> removed."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Client must exist in the system.
            - Cannot remove the client if there are transactions referencing this client.
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist." }

        # Check for transactions that reference this client
        for txn in self.transactions.values():
            if txn["client_id"] == client_id:
                return {
                    "success": False,
                    "error": "Cannot remove client: existing transactions reference this client."
                }

        del self.clients[client_id]
        return { "success": True, "message": f"Client {client_id} removed." }

    def remove_transaction(self, transaction_id: str) -> dict:
        """
        Delete a transaction record from the system.

        Args:
            transaction_id (str): Unique identifier of the transaction to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction <transaction_id> removed successfully."
            }
            OR
            {
                "success": False,
                "error": "Transaction does not exist."
            }

        Constraints:
            - The transaction must exist in the system.
        """
        if transaction_id not in self.transactions:
            return {
                "success": False,
                "error": "Transaction does not exist."
            }
        del self.transactions[transaction_id]
        return {
            "success": True,
            "message": f"Transaction {transaction_id} removed successfully."
        }


class InvestmentManagementSystem(BaseEnv):
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
            current = getattr(env, key, None)
            if callable(current):
                setattr(env, f"_{key}_state", copy.deepcopy(value))
            else:
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

    def get_fund_manager_by_id(self, **kwargs):
        return self._call_inner_tool('get_fund_manager_by_id', kwargs)

    def list_all_fund_managers(self, **kwargs):
        return self._call_inner_tool('list_all_fund_managers', kwargs)

    def get_fund_by_id(self, **kwargs):
        return self._call_inner_tool('get_fund_by_id', kwargs)

    def list_funds_by_manager_id(self, **kwargs):
        return self._call_inner_tool('list_funds_by_manager_id', kwargs)

    def list_all_funds(self, **kwargs):
        return self._call_inner_tool('list_all_funds', kwargs)

    def get_fund_characteristics(self, **kwargs):
        return self._call_inner_tool('get_fund_characteristics', kwargs)

    def get_client_by_id(self, **kwargs):
        return self._call_inner_tool('get_client_by_id', kwargs)

    def list_clients_by_fund_id(self, **kwargs):
        return self._call_inner_tool('list_clients_by_fund_id', kwargs)

    def list_all_clients(self, **kwargs):
        return self._call_inner_tool('list_all_clients', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def list_transactions_by_fund_id(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_fund_id', kwargs)

    def list_transactions_by_client_id(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_client_id', kwargs)

    def compliance_check_manager_assignment(self, **kwargs):
        return self._call_inner_tool('compliance_check_manager_assignment', kwargs)

    def check_manager_license_status(self, **kwargs):
        return self._call_inner_tool('check_manager_license_status', kwargs)

    def check_fund_assignment_valid_on_date(self, **kwargs):
        return self._call_inner_tool('check_fund_assignment_valid_on_date', kwargs)

    def list_funds_without_manager(self, **kwargs):
        return self._call_inner_tool('list_funds_without_manager', kwargs)

    def assign_manager_to_fund(self, **kwargs):
        return self._call_inner_tool('assign_manager_to_fund', kwargs)

    def remove_manager_from_fund(self, **kwargs):
        return self._call_inner_tool('remove_manager_from_fund', kwargs)

    def update_fund_status(self, **kwargs):
        return self._call_inner_tool('update_fund_status', kwargs)

    def update_manager_license_status(self, **kwargs):
        return self._call_inner_tool('update_manager_license_status', kwargs)

    def add_fund(self, **kwargs):
        return self._call_inner_tool('add_fund', kwargs)

    def add_fund_manager(self, **kwargs):
        return self._call_inner_tool('add_fund_manager', kwargs)

    def add_client(self, **kwargs):
        return self._call_inner_tool('add_client', kwargs)

    def add_transaction(self, **kwargs):
        return self._call_inner_tool('add_transaction', kwargs)

    def update_fund_characteristics(self, **kwargs):
        return self._call_inner_tool('update_fund_characteristics', kwargs)

    def update_client_account_status(self, **kwargs):
        return self._call_inner_tool('update_client_account_status', kwargs)

    def remove_fund(self, **kwargs):
        return self._call_inner_tool('remove_fund', kwargs)

    def remove_fund_manager(self, **kwargs):
        return self._call_inner_tool('remove_fund_manager', kwargs)

    def remove_client(self, **kwargs):
        return self._call_inner_tool('remove_client', kwargs)

    def remove_transaction(self, **kwargs):
        return self._call_inner_tool('remove_transaction', kwargs)
