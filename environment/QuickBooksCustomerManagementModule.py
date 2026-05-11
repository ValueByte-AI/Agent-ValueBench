# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import csv
import io
import re
import uuid




class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_information: str
    address: str
    email: str
    phone: str
    account_status: str
    date_added: str


class TransactionInfo(TypedDict):
    transaction_id: str
    customer_id: str
    date: str
    amount: float
    transaction_type: str
    reference_document: str


class CommunicationLogInfo(TypedDict):
    log_id: str
    customer_id: str
    date: str
    communication_type: str
    details: str
    agent_id: str


class _GeneratedEnvImpl:
    def __init__(self):
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Communication Logs: {log_id: CommunicationLogInfo}
        self.communication_logs: Dict[str, CommunicationLogInfo] = {}

        # Constraints:
        # - Each customer must have a unique customer_id.
        # - Customer contact information must be valid and up-to-date.
        # - Customer records must be accessible for querying and export.
        # - Deletion or merging of customer records must handle associated transactions and logs appropriately.
        # - Access to customer data may be subject to user permissions or privacy policy compliance.

    def get_all_customers(self) -> dict:
        """
        Retrieve a list of all customers with their relevant information.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo]  # List of all customer records (empty list if none)
            }
        Constraints:
            - Returns all customers currently in the system.
            - No input and no explicit permission checks are implemented here.
        """
        customers_list = list(self.customers.values())
        return {
            "success": True,
            "data": customers_list
        }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve detailed information for a specific customer by their unique customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: 
                Success: { "success": True, "data": CustomerInfo }
                Failure: { "success": False, "error": "Customer not found" }

        Constraints:
            - customer_id must exist in the self.customers dictionary.
            - Each customer_id is unique.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer not found" }

        return { "success": True, "data": self.customers[customer_id] }

    def search_customers_by_name(self, query: str) -> dict:
        """
        Search for customers by a partial or full match of their name (case-insensitive).
    
        Args:
            query (str): Partial or full customer name to search for.
    
        Returns:
            dict: 
                { "success": True, "data": List[CustomerInfo] }
                or
                { "success": False, "error": str }
    
        Constraints:
            - Query string must not be empty or whitespace.
            - Returns all customers with a case-insensitive substring match in their name.
            - Does not apply any permission or privacy filtering.
        """
        if not isinstance(query, str) or query.strip() == "":
            return { "success": False, "error": "Invalid search query" }
    
        query_lower = query.strip().lower()
        result = [
            customer 
            for customer in self.customers.values()
            if query_lower in customer["name"].lower()
        ]
        return { "success": True, "data": result }

    def get_customer_contact_info(self, customer_id: str) -> dict:
        """
        Retrieve the contact information (email, phone, address) for a specified customer.

        Args:
            customer_id (str): The unique identifier for the customer.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": {
                        "email": str,
                        "phone": str,
                        "address": str
                    }
                }
                On failure (customer does not exist),
                {
                    "success": False,
                    "error": "Customer does not exist"
                }

        Constraints:
            - customer_id must exist in the system.
            - No permission checking performed in this operation.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer does not exist"}
    
        data = {
            "email": customer["email"],
            "phone": customer["phone"],
            "address": customer["address"]
        }
        return {"success": True, "data": data}

    def export_customer_list(self, format: str) -> dict:
        """
        Export the list of customers in the specified format.

        Args:
            format (str): Desired export format. Supported: 'csv', 'excel'.

        Returns:
            dict: {
                "success": True,
                "data": <exported_customer_list>  # CSV string, or list-of-dicts for 'excel'
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., unsupported format)
            }

        Constraints:
            - All customer records must be exported.
            - Format must be supported ('csv', 'excel').
        """
        supported_formats = {'csv', 'excel'}
        if format.lower() not in supported_formats:
            return {"success": False, "error": f"Unsupported export format: {format}"}
    
        customers = list(self.customers.values())
        headers = [
            "customer_id", "name", "contact_information", "address", "email",
            "phone", "account_status", "date_added"
        ]

        if format.lower() == "csv":
            # Generate CSV string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for cust in customers:
                writer.writerow({h: cust.get(h, "") for h in headers})
            csv_str = output.getvalue()
            output.close()
            return {"success": True, "data": csv_str}
    
        elif format.lower() == "excel":
            # Here, 'excel' means returning a list of dicts (to be consumed by Excel utilities).
            return {"success": True, "data": [dict(cust) for cust in customers]}

    def get_customer_transactions(self, customer_id: str) -> dict:
        """
        Retrieve the transaction history for a specific customer.

        Args:
            customer_id (str): The unique customer ID whose transactions are needed.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionInfo],  # May be an empty list if no transactions
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., customer does not exist)
            }

        Constraints:
            - The customer_id must exist.
            - Returns all transactions associated with the specified customer.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}

        transactions = [
            tx for tx in self.transactions.values()
            if tx["customer_id"] == customer_id
        ]

        return {"success": True, "data": transactions}

    def get_customer_communication_logs(self, customer_id: str) -> dict:
        """
        Retrieve all communication logs associated with a customer.

        Args:
            customer_id (str): The ID of the customer to fetch communication logs for.

        Returns:
            dict: 
                - {"success": True, "data": List[CommunicationLogInfo]}: list may be empty
                - {"success": False, "error": str}: with error reason if customer does not exist

        Constraints:
            - Customer must exist (customer_id must be present in self.customers).
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        logs = [
            log_info for log_info in self.communication_logs.values()
            if log_info["customer_id"] == customer_id
        ]

        return {"success": True, "data": logs}

    def check_customer_exists(
        self, 
        customer_id: str = None, 
        name: str = None, 
        email: str = None, 
        phone: str = None
    ) -> dict:
        """
        Checks whether a customer exists, identified by customer_id or by combination of provided details.

        Args:
            customer_id (str, optional): Unique identifier for customer.
            name (str, optional): Customer name.
            email (str, optional): Customer email.
            phone (str, optional): Customer phone number.

        Returns:
            dict: 
                - If a matching customer is found:
                    { "success": True, "exists": True, "customer_id": <matched_customer_id> }
                - If not found:
                    { "success": True, "exists": False }
                - On input error:
                    { "success": False, "error": <error_message> }

        Constraints:
            - At least one parameter must be provided (customer_id or any identifying detail).
            - If several details are given, all must match one customer (AND match).
        """
        if not (customer_id or name or email or phone):
            return { "success": False, "error": "Must provide customer_id or at least one identifying detail." }

        if customer_id:
            if customer_id in self.customers:
                return { "success": True, "exists": True, "customer_id": customer_id }
            else:
                return { "success": True, "exists": False }

        # All customers must match all provided details (AND logic)
        for cid, info in self.customers.items():
            match = True
            if name is not None and info.get("name") != name:
                match = False
            if email is not None and info.get("email") != email:
                match = False
            if phone is not None and info.get("phone") != phone:
                match = False
            if match:
                return { "success": True, "exists": True, "customer_id": cid }
        return { "success": True, "exists": False }

    def check_access_permission(self, user_id: str, customer_ids: list) -> dict:
        """
        Verify if the specified user/session has permission to access/export the specified customer data.

        Args:
            user_id (str): Identifier for the user/session requesting access.
            customer_ids (list of str): List of customer_ids the user wishes to access.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            customer_id: True/False,  # For each requested customer_id
                            ...
                        }
                    }
                On error:
                    {
                        "success": False,
                        "error": "Error message"
                    }

        Constraints:
            - If user_id is "admin", grant access to all customers.
            - If user_id is "suspended", deny access to all customers.
            - For other user_ids, grant access if customer exists.
            - If customer does not exist, return False for that customer.
            - user_id must be provided.
        """
        if not user_id:
            return { "success": False, "error": "User/session ID must be provided." }
        if not isinstance(customer_ids, list):
            return { "success": False, "error": "customer_ids must be a list of customer IDs." }

        permission_result = {}
        if user_id == "admin":
            for cust_id in customer_ids:
                permission_result[cust_id] = True
        elif user_id == "suspended":
            for cust_id in customer_ids:
                permission_result[cust_id] = False
        else:
            for cust_id in customer_ids:
                if cust_id in self.customers:
                    permission_result[cust_id] = True
                else:
                    permission_result[cust_id] = False

        return { "success": True, "data": permission_result }

    def add_new_customer(
        self,
        customer_id: str,
        name: str,
        contact_information: str,
        address: str,
        email: str,
        phone: str,
        account_status: str,
        date_added: str
    ) -> dict:
        """
        Create a new customer record with unique customer_id and validated contact info.

        Args:
            customer_id (str): Unique identifier for the customer.
            name (str): Customer name.
            contact_information (str): Additional contact info.
            address (str): Customer address.
            email (str): Email address (should contain '@').
            phone (str): Phone number.
            account_status (str): e.g., 'active', 'inactive', etc.
            date_added (str): The date the customer is added (ISO format recommended).

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - customer_id must be unique.
            - contact info (email, phone) must be valid and nonempty.
        """

        # Enforce uniqueness of customer_id
        if customer_id in self.customers:
            return {"success": False, "error": f"Customer ID '{customer_id}' already exists."}

        # Basic field completeness check
        fields = {
            "customer_id": customer_id,
            "name": name,
            "contact_information": contact_information,
            "address": address,
            "email": email,
            "phone": phone,
            "account_status": account_status,
            "date_added": date_added,
        }
        for key, value in fields.items():
            if not value or not str(value).strip():
                return {"success": False, "error": f"Field '{key}' is required and cannot be empty."}

        # Basic email validation
        if "@" not in email or "." not in email:
            return {"success": False, "error": "Invalid email address."}

        # Phone validation: simple check (non-empty, could do more advanced check as needed)
        if not any(c.isdigit() for c in phone):
            return {"success": False, "error": "Invalid phone number."}

        # Add the customer
        self.customers[customer_id] = {
            "customer_id": customer_id,
            "name": name,
            "contact_information": contact_information,
            "address": address,
            "email": email,
            "phone": phone,
            "account_status": account_status,
            "date_added": date_added
        }

        return {"success": True, "message": f"Customer '{customer_id}' added successfully."}

    def update_customer_details(
        self,
        customer_id: str,
        name: str = None,
        contact_information: str = None,
        address: str = None,
        email: str = None,
        phone: str = None,
        account_status: str = None
    ) -> dict:
        """
        Update an existing customer's metadata. Fields that are not provided will remain unchanged.

        Args:
            customer_id (str): The unique ID of the customer to update.
            name (str, optional): New name for the customer.
            contact_information (str, optional): New contact info.
            address (str, optional): New address.
            email (str, optional): New email (must contain '@').
            phone (str, optional): New phone (must be non-empty and digits).
            account_status (str, optional): New status.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Customer details updated." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The customer must exist.
            - Updated contact info (email, phone) must be valid if provided.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer ID not found." }
    
        # Track if there is at least one field to update
        updates = 0

        if name is not None:
            customer['name'] = name
            updates += 1

        if contact_information is not None:
            customer['contact_information'] = contact_information
            updates += 1

        if address is not None:
            customer['address'] = address
            updates += 1

        if email is not None:
            if '@' not in email or not email.strip():
                return { "success": False, "error": "Invalid email address." }
            customer['email'] = email
            updates += 1

        if phone is not None:
            if not phone.strip() or not any(c.isdigit() for c in phone):
                return { "success": False, "error": "Invalid phone number." }
            customer['phone'] = phone
            updates += 1

        if account_status is not None:
            customer['account_status'] = account_status
            updates += 1

        if updates == 0:
            return { "success": False, "error": "No data provided to update." }
    
        self.customers[customer_id] = customer  # Save back to mapping

        return { "success": True, "message": "Customer details updated." }

    def delete_customer(self, customer_id: str) -> dict:
        """
        Remove a customer from the system and handle all associated transactions and communication logs.
        Associated transactions and logs are deleted along with the customer.

        Args:
            customer_id (str): The ID of the customer to delete.

        Returns:
            dict:
                - On success: {"success": True, "message": "Customer <customer_id> deleted and associated data handled."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Customer must exist.
            - All related transactions and communication logs are to be deleted as well.
        """
        if not customer_id:
            return {"success": False, "error": "No customer_id provided."}

        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist."}

        # Delete all associated transactions
        transactions_to_delete = [tid for tid, tinfo in self.transactions.items() if tinfo["customer_id"] == customer_id]
        for tid in transactions_to_delete:
            del self.transactions[tid]

        # Delete all associated communication logs
        logs_to_delete = [lid for lid, linfo in self.communication_logs.items() if linfo["customer_id"] == customer_id]
        for lid in logs_to_delete:
            del self.communication_logs[lid]

        # Delete the customer itself
        del self.customers[customer_id]

        return {"success": True, "message": f"Customer {customer_id} deleted and associated data handled."}

    def merge_customers(self, primary_customer_id: str, duplicate_customer_ids: list) -> dict:
        """
        Merge duplicate customer records into a single customer, consolidating their transactions
        and communication logs. All associated transactions and logs are moved to the primary.

        Args:
            primary_customer_id (str): The customer_id to retain as the merged record.
            duplicate_customer_ids (list of str): A list of customer IDs to merge into the primary (these records will be deleted).

        Returns:
            dict: {
                "success": True,
                "message": "Merged X customer(s) into primary customer_id."
            } or {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - All customer IDs must exist.
            - The primary_customer_id must not be in duplicate_customer_ids.
            - All transactions and communication logs of duplicates must have their customer_id reassigned to the primary.
            - Duplicates must be removed from customer records.
            - If any of the duplicate_customer_ids do not exist, return an error.
        """
        # Validate primary_customer_id exists
        if primary_customer_id not in self.customers:
            return { "success": False, "error": f"Primary customer_id '{primary_customer_id}' does not exist." }

        if not duplicate_customer_ids:
            return { "success": False, "error": "No duplicate_customer_ids provided for merging." }

        # Remove self-merge if accidentally included
        if primary_customer_id in duplicate_customer_ids:
            return { "success": False, "error": "Primary customer_id cannot be listed as a duplicate." }

        # Validate all duplicate_customer_ids exist
        non_existent = [cid for cid in duplicate_customer_ids if cid not in self.customers]
        if non_existent:
            return { "success": False, "error": f"Duplicate customer IDs not found: {', '.join(non_existent)}" }

        # Move all transactions and logs from each duplicate to primary
        for dup_id in duplicate_customer_ids:
            # Transactions
            for transaction in self.transactions.values():
                if transaction["customer_id"] == dup_id:
                    transaction["customer_id"] = primary_customer_id
            # Communication Logs
            for log in self.communication_logs.values():
                if log["customer_id"] == dup_id:
                    log["customer_id"] = primary_customer_id
            # Remove duplicate customer record
            del self.customers[dup_id]

        return {
            "success": True,
            "message": f"Merged {len(duplicate_customer_ids)} customer(s) into '{primary_customer_id}'."
        }

    def update_customer_contact_info(
        self, 
        customer_id: str, 
        contact_information: str = None, 
        address: str = None, 
        email: str = None, 
        phone: str = None
    ) -> dict:
        """
        Update only the contact fields (contact_information, address, email, phone)
        of the specified customer. Validates the new values where possible.

        Args:
            customer_id (str): The unique identifier of the customer to update.
            contact_information (str, optional): New contact information.
            address (str, optional): New address.
            email (str, optional): New email address (must be valid format).
            phone (str, optional): New phone number.

        Returns:
            dict: 
                { "success": True, "message": "Customer contact information updated." }
                or
                { "success": False, "error": "<error_reason>" }

        Constraints:
            - Customer must exist.
            - Email, if provided, must be syntactically valid.
            - At least one contact field must be provided.
            - Fields not provided are unchanged.
        """

        # Check if customer exists
        cust = self.customers.get(customer_id)
        if not cust:
            return {"success": False, "error": "Customer does not exist."}

        any_update = False

        # Validate and update email if provided
        if email is not None:
            email_regex = r"^[^@]+@[^@]+\.[^@]+$"
            if not re.match(email_regex, email):
                return {"success": False, "error": "Invalid email format."}
            cust["email"] = email
            any_update = True

        # Validate and update phone if provided (basic)
        if phone is not None:
            phone_str = str(phone)
            phone_regex = r"^[\d\+\-\(\) ]{7,}$"  # Basic: at least 7 chars, only relevant chars
            if not re.match(phone_regex, phone_str):
                return {"success": False, "error": "Invalid phone number format."}
            cust["phone"] = phone_str
            any_update = True

        # Update contact_information if provided
        if contact_information is not None:
            cust["contact_information"] = contact_information
            any_update = True

        # Update address if provided
        if address is not None:
            cust["address"] = address
            any_update = True

        if not any_update:
            return {"success": False, "error": "No contact fields provided for update."}

        self.customers[customer_id] = cust  # Save back to mapping (dict object, for clarity)
        return {"success": True, "message": "Customer contact information updated."}

    def add_transaction_for_customer(
        self,
        transaction_id: str,
        customer_id: str,
        date: str,
        amount: float,
        transaction_type: str,
        reference_document: str
    ) -> dict:
        """
        Add a new transaction linked to a specific customer.

        Args:
            transaction_id (str): Unique identifier for the transaction.
            customer_id (str): ID of the customer to link the transaction to.
            date (str): Date of the transaction (format: string).
            amount (float): Amount of the transaction.
            transaction_type (str): Transaction type/category.
            reference_document (str): Reference document ID or path.

        Returns:
            dict:
                - {"success": True, "message": "Transaction <transaction_id> added for customer <customer_id>."}
                - {"success": False, "error": "<reason>"}

        Constraints:
            - The customer_id must exist in the system.
            - Each transaction_id must be unique (not already used).
        """
        if transaction_id in self.transactions:
            return {"success": False, "error": "Transaction ID already exists."}

        if customer_id not in self.customers:
            return {"success": False, "error": "Customer ID does not exist."}

        # (Optional) Could check for negative amounts or validate other fields

        transaction_info: TransactionInfo = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "date": date,
            "amount": amount,
            "transaction_type": transaction_type,
            "reference_document": reference_document
        }

        self.transactions[transaction_id] = transaction_info

        return {
            "success": True,
            "message": f"Transaction {transaction_id} added for customer {customer_id}."
        }


    def add_communication_log_for_customer(
        self, 
        customer_id: str,
        date: str,
        communication_type: str,
        details: str,
        agent_id: str
    ) -> dict:
        """
        Record a new communication interaction (log) for a specified customer.
    
        Args:
            customer_id (str): ID of the customer to log communication for.
            date (str): Date/time of the communication (format as used in environment).
            communication_type (str): Type of communication (e.g., phone, email, meeting).
            details (str): Details/content of the communication.
            agent_id (str): Identifier of the agent who communicated.

        Returns:
            dict: 
              On success: {
                "success": True, 
                "message": "Communication log added for customer <customer_id>"
              }
              On error: {
                "success": False,
                "error": <error string>
              }

        Constraints:
            - The customer_id must refer to an existing customer.
            - Each communication log must have a unique log_id.
            - All fields are required and should be non-empty strings.
        """
        # Check required fields
        if not all([customer_id, date, communication_type, details, agent_id]):
            return {"success": False, "error": "All fields must be provided and non-empty"}

        # Ensure the customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}

        # Generate a unique log_id
        while True:
            log_id = str(uuid.uuid4())
            if log_id not in self.communication_logs:
                break

        new_log = {
            "log_id": log_id,
            "customer_id": customer_id,
            "date": date,
            "communication_type": communication_type,
            "details": details,
            "agent_id": agent_id
        }

        self.communication_logs[log_id] = new_log

        return {
            "success": True,
            "message": f"Communication log added for customer {customer_id}"
        }


class QuickBooksCustomerManagementModule(BaseEnv):
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

    def get_all_customers(self, **kwargs):
        return self._call_inner_tool('get_all_customers', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def search_customers_by_name(self, **kwargs):
        return self._call_inner_tool('search_customers_by_name', kwargs)

    def get_customer_contact_info(self, **kwargs):
        return self._call_inner_tool('get_customer_contact_info', kwargs)

    def export_customer_list(self, **kwargs):
        return self._call_inner_tool('export_customer_list', kwargs)

    def get_customer_transactions(self, **kwargs):
        return self._call_inner_tool('get_customer_transactions', kwargs)

    def get_customer_communication_logs(self, **kwargs):
        return self._call_inner_tool('get_customer_communication_logs', kwargs)

    def check_customer_exists(self, **kwargs):
        return self._call_inner_tool('check_customer_exists', kwargs)

    def check_access_permission(self, **kwargs):
        return self._call_inner_tool('check_access_permission', kwargs)

    def add_new_customer(self, **kwargs):
        return self._call_inner_tool('add_new_customer', kwargs)

    def update_customer_details(self, **kwargs):
        return self._call_inner_tool('update_customer_details', kwargs)

    def delete_customer(self, **kwargs):
        return self._call_inner_tool('delete_customer', kwargs)

    def merge_customers(self, **kwargs):
        return self._call_inner_tool('merge_customers', kwargs)

    def update_customer_contact_info(self, **kwargs):
        return self._call_inner_tool('update_customer_contact_info', kwargs)

    def add_transaction_for_customer(self, **kwargs):
        return self._call_inner_tool('add_transaction_for_customer', kwargs)

    def add_communication_log_for_customer(self, **kwargs):
        return self._call_inner_tool('add_communication_log_for_customer', kwargs)

