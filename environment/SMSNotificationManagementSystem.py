# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import re
import uuid
from typing import List, Dict, Any
import datetime
from datetime import datetime
from typing import Optional, Dict



class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    phone_number: str
    status: str  # e.g. 'active', 'inactive'

class SMSMessageInfo(TypedDict):
    message_id: str
    request_id: str
    content: str
    created_at: str  # ISO timestamp
    sender_id: str

class SMSDeliveryInfo(TypedDict):
    delivery_id: str
    message_id: str
    customer_id: str
    phone_number: str
    delivery_status: str  # e.g. 'pending', 'sent', 'delivered', 'failed'
    sent_at: Optional[str]  # ISO timestamp or None
    delivered_at: Optional[str]  # ISO timestamp or None
    gateway_response: Optional[str]

class SMSGatewayInfo(TypedDict):
    gateway_id: str
    provider_name: str
    api_endpoint: str
    status: str  # e.g. 'active', 'inactive'

class _GeneratedEnvImpl:
    def __init__(self):
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # SMS Messages: {message_id: SMSMessageInfo}
        self.sms_messages: Dict[str, SMSMessageInfo] = {}

        # SMS Deliveries: {delivery_id: SMSDeliveryInfo}
        self.sms_deliveries: Dict[str, SMSDeliveryInfo] = {}

        # SMS Gateways: {gateway_id: SMSGatewayInfo}
        self.sms_gateways: Dict[str, SMSGatewayInfo] = {}

        # Constraints:
        # - Each SMSMessage can be sent to multiple customers (linked via SMSDelivery)
        # - Each SMSDelivery must have a delivery_status (e.g., pending, sent, delivered, failed)
        # - request_id must uniquely identify a batch of messages for tracking/qeurying
        # - phone_number must be valid (format and uniqueness constraints may apply)
        # - Only customers with active status can receive messages
        # - External gateways may have rate-limits and operational constraints

    def list_all_customers(self) -> dict:
        """
        Retrieve all registered customers.

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo],  # List of all customers (can be empty if none registered)
            }
        """
        customers_list = list(self.customers.values())
        return { "success": True, "data": customers_list }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Get details of a customer using their customer_id.

        Args:
            customer_id (str): Unique identifier of the customer.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": CustomerInfo
                }
                On failure: {
                    "success": False,
                    "error": "Customer not found"
                }
        Constraints:
            - The customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def get_active_customers(self) -> dict:
        """
        Retrieve all customers whose status is exactly 'active'.

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo],  # List of active customers. Empty if none.
            }
        """
        active_customers = [
            customer_info for customer_info in self.customers.values()
            if customer_info.get('status') == 'active'
        ]
        return { "success": True, "data": active_customers }

    def validate_phone_number(self, phone_number: str) -> dict:
        """
        Check if a given phone number is valid in format and unique among all customers.

        Args:
            phone_number (str): Phone number to check.

        Returns:
            dict:
              - success: True/False
              - data: {"is_valid": bool, "is_unique": bool} (on success)
              - error: str (on failure)

        Constraints:
            - Format is considered valid if phone number follows pattern: optional "+" at start, then 8-15 digits.
            - Uniqueness means no existing customer has this phone number.
        """
        if not isinstance(phone_number, str) or not phone_number:
            return { "success": False, "error": "Phone number is required." }
    
        # Regex: optional + at start, then 8 to 15 digits
        pattern = r"^\+?\d{8,15}$"
        is_valid = re.fullmatch(pattern, phone_number) is not None

        is_unique = all(
            cust["phone_number"] != phone_number
            for cust in self.customers.values()
        ) if is_valid else False  # If invalid, don't bother with uniqueness

        return {
            "success": True,
            "data": {
                "is_valid": is_valid,
                "is_unique": is_unique
            }
        }

    def list_all_sms_messages(self) -> dict:
        """
        Retrieves all SMSMessage records in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SMSMessageInfo],  # List of all SMSMessage records (could be empty)
            }

        Constraints:
            - None specific for this operation (read-only, no filtering).
        """
        all_messages = list(self.sms_messages.values())
        return { "success": True, "data": all_messages }

    def get_sms_message_by_id(self, message_id: str) -> dict:
        """
        Retrieve the details of an SMSMessage given its unique message_id.

        Args:
            message_id (str): The unique identifier of the SMSMessage.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": SMSMessageInfo
                }
                On failure: {
                    "success": False,
                    "error": "SMS message not found"
                }
        Constraints:
            - The message_id must exist in the sms_messages mapping.
        """
        if message_id in self.sms_messages:
            return {
                "success": True,
                "data": self.sms_messages[message_id]
            }
        else:
            return {
                "success": False,
                "error": "SMS message not found"
            }

    def get_sms_messages_by_request_id(self, request_id: str) -> dict:
        """
        List all SMSMessage records associated with the specified request_id.
    
        Args:
            request_id (str): The batch request identifier for filtering SMSMessage records.
    
        Returns:
            dict: {
                "success": True,
                "data": List[SMSMessageInfo]  # List of SMSMessage records with given request_id (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Only in case of invalid input type
            }
        
        Constraints:
            - All messages with matching request_id are included in the result.
            - If none found, returns an empty list (success).
        """
        if not isinstance(request_id, str) or not request_id:
            return {"success": False, "error": "Invalid request_id: must be non-empty string"}

        result = [
            msg_info
            for msg_info in self.sms_messages.values()
            if msg_info["request_id"] == request_id
        ]
        return {"success": True, "data": result}

    def list_sms_deliveries_by_message_id(self, message_id: str) -> dict:
        """
        Retrieve all SMSDelivery records associated with the given message_id.

        Args:
            message_id (str): The unique ID of the SMSMessage for which delivery records are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[SMSDeliveryInfo],  # List of delivery records, empty list if none found
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g. message_id does not exist)
            }

        Constraints:
            - message_id must correspond to a valid SMSMessage.
            - If no deliveries exist for a valid message_id, returns empty list with success=True.
        """
        if message_id not in self.sms_messages:
            return { "success": False, "error": "Specified message_id does not exist." }

        deliveries = [
            delivery for delivery in self.sms_deliveries.values()
            if delivery['message_id'] == message_id
        ]
        return {
            "success": True,
            "data": deliveries
        }

    def list_sms_deliveries_by_request_id(self, request_id: str) -> dict:
        """
        Retrieves all SMSDelivery records that are linked to all SMSMessage instances with the specified request_id.

        Args:
            request_id (str): The batch/request identifier to search for.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[SMSDeliveryInfo]}
                On failure (e.g., no messages matched):
                    {"success": False, "error": str}
        Constraints:
            - The request_id must exist on at least one SMSMessage.
            - Will return all SMSDeliveryInfo with their message_id matching any such message.
            - Returns an empty list if no deliveries found for valid request_id.
        """
        # Step 1: Find all message_ids for the request_id
        message_ids = [mid for mid, msg in self.sms_messages.items() if msg["request_id"] == request_id]

        if not message_ids:
            return {"success": False, "error": "No messages found for the given request_id"}

        # Step 2: Find all deliveries linked to those message_ids
        deliveries = [
            delivery for delivery in self.sms_deliveries.values()
            if delivery["message_id"] in message_ids
        ]

        return {"success": True, "data": deliveries}

    def get_delivery_status_by_delivery_id(self, delivery_id: str) -> dict:
        """
        Retrieve the delivery_status and gateway_response for a specific SMSDelivery.

        Args:
            delivery_id (str): The unique identifier for the SMS delivery instance.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "delivery_status": str,         # e.g. 'pending', 'delivered', etc.
                    "gateway_response": Optional[str], # Gateway feedback, if any
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g. 'Delivery ID does not exist'
            }

        Constraints:
            - The given delivery_id must exist in the system.
        """
        delivery = self.sms_deliveries.get(delivery_id)
        if not delivery:
            return {
                "success": False,
                "error": "Delivery ID does not exist"
            }
        return {
            "success": True,
            "data": {
                "delivery_status": delivery["delivery_status"],
                "gateway_response": delivery.get("gateway_response")
            }
        }

    def get_overall_delivery_status_by_request_id(self, request_id: str) -> dict:
        """
        Summarize delivery statuses for all SMSDeliveries associated with the given request_id.

        Args:
            request_id (str): The unique batch/request identifier.

        Returns:
            dict: {
                "success": True,
                "data": {<delivery_status>: <count>, ...},
                "total": int  # total number of delivery records found for this request_id
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. request_id not found
            }

        Constraints:
            - request_id must correspond to at least one SMSMessage.
            - Reports zeroes if there are no deliveries, still a success.
        """
        # Find all message_ids for this request_id
        relevant_message_ids = [
            msg["message_id"]
            for msg in self.sms_messages.values()
            if msg["request_id"] == request_id
        ]
        if not relevant_message_ids:
            return {"success": False, "error": "No messages found for this request_id"}

        # Gather and count delivery statuses
        status_summary = {}
        total = 0
        for delivery in self.sms_deliveries.values():
            if delivery["message_id"] in relevant_message_ids:
                status = delivery.get("delivery_status", "unknown")
                status_summary[status] = status_summary.get(status, 0) + 1
                total += 1

        return {"success": True, "data": status_summary, "total": total}

    def list_active_gateways(self) -> dict:
        """
        Retrieve all SMS gateway services that are marked as 'active'.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SMSGatewayInfo],  # List of active gateway info dicts (empty if none found)
            }
        """
        active_gateways = [
            gateway_info
            for gateway_info in self.sms_gateways.values()
            if gateway_info.get("status") == "active"
        ]
        return { "success": True, "data": active_gateways }

    def get_gateway_by_id(self, gateway_id: str) -> dict:
        """
        Retrieve SMS gateway details by gateway_id.

        Args:
            gateway_id (str): The unique identifier of the SMS gateway.

        Returns:
            dict: {
                "success": True,
                "data": SMSGatewayInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - gateway_id must exist in the sms_gateways mapping.
        """
        gateway = self.sms_gateways.get(gateway_id)
        if not gateway:
            return {"success": False, "error": "Gateway not found"}
        return {"success": True, "data": gateway}

    def check_gateway_status(self, gateway_id: str) -> dict:
        """
        Query the operational status ('active', 'inactive', etc.) of a specific SMS gateway.

        Args:
            gateway_id (str): Unique identifier of the SMS gateway.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "gateway_id": str,
                    "status": str  # e.g., 'active', 'inactive', or other status
                }
            }
            or
            {
                "success": False,
                "error": str  # explanation, e.g., gateway not found
            }

        Constraints:
            - The gateway_id must exist in the system to retrieve its status.
        """
        gateway = self.sms_gateways.get(gateway_id)
        if not gateway:
            return { "success": False, "error": "Gateway not found" }
        return {
            "success": True,
            "data": {
                "gateway_id": gateway_id,
                "status": gateway.get("status", "")
            }
        }


    def create_sms_message(
        self,
        request_id: str,
        content: str,
        created_at: str,
        sender_id: str
    ) -> dict:
        """
        Create a new SMSMessage record for a batch of SMS sends.

        Args:
            request_id (str): Batch identifier for tracking.
            content (str): Message content text.
            created_at (str): ISO timestamp when this message is created.
            sender_id (str): Identifier of the sender.

        Returns:
            dict:
             - On success:
                 {
                    "success": True,
                    "message": "SMSMessage created",
                    "data": SMSMessageInfo
                 }
             - On failure:
                 {
                    "success": False,
                    "error": str
                 }

        Constraints:
            - message_id must be unique within sms_messages.
            - All arguments required and must be non-empty.
        """
        # Validate input
        if not (request_id and content and created_at and sender_id):
            return { "success": False, "error": "All arguments (request_id, content, created_at, sender_id) are required and must be non-empty." }

        # Generate unique message_id
        for _ in range(5):
            message_id = str(uuid.uuid4())
            if message_id not in self.sms_messages:
                break
        else:
            return { "success": False, "error": "Could not generate unique message_id, try again." }

        sms_message: SMSMessageInfo = {
            "message_id": message_id,
            "request_id": request_id,
            "content": content,
            "created_at": created_at,
            "sender_id": sender_id
        }
        self.sms_messages[message_id] = sms_message

        return {
            "success": True,
            "message": "SMSMessage created",
            "data": sms_message
        }


    def create_batch_sms_deliveries(self, message_id: str, customer_ids: List[str]) -> dict:
        """
        Create SMSDelivery records for batch sending of a message to multiple customers.

        Args:
            message_id (str): The ID of the SMSMessage to send.
            customer_ids (List[str]): The list of customer IDs to receive the message.

        Returns:
            dict: {
                "success": True,
                "data": List[SMSDeliveryInfo],  # List of newly created delivery records
                "invalid_customers": List[str], # List of customer_ids not processed (inactive or not found)
            }
            OR
            {
                "success": False,
                "error": str  # Error message
            }
    
        Constraints:
            - Only customers with "active" status will receive deliveries.
            - The message_id must exist.
            - Each delivery_id must be unique.
        """
        if message_id not in self.sms_messages:
            return {"success": False, "error": "SMSMessage not found"}

        created_deliveries: List[SMSDeliveryInfo] = []
        invalid_customers: List[str] = []
        for cust_id in customer_ids:
            cust = self.customers.get(cust_id)
            if not cust or cust.get("status") != "active":
                invalid_customers.append(cust_id)
                continue
            delivery_id = str(uuid.uuid4())
            new_delivery: SMSDeliveryInfo = {
                "delivery_id": delivery_id,
                "message_id": message_id,
                "customer_id": cust_id,
                "phone_number": cust["phone_number"],
                "delivery_status": "pending",
                "sent_at": None,
                "delivered_at": None,
                "gateway_response": None
            }
            self.sms_deliveries[delivery_id] = new_delivery
            created_deliveries.append(new_delivery)

        return {
            "success": True,
            "data": created_deliveries,
            "invalid_customers": invalid_customers
        }

    def trigger_sms_send(self, delivery_ids: list[str]) -> dict:
        """
        Initiate the sending of specified SMSDeliveries: updates their status from 'pending' to 'sent'
        (if possible), sets the sent_at field (to current UTC ISO timestamp), and records gateway_response.

        Args:
            delivery_ids (list[str]): List of SMSDelivery delivery_ids to trigger sending for.

        Returns:
            dict: {
                "success": True,
                "message": f"Triggered sending for N deliveries.",
                "details": {
                    "sent": [<delivery_id>, ...],
                    "skipped": {
                        <delivery_id>: <reason string>,  # Ineligible or failed reasons
                        ...
                    }
                }
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        
        Constraints:
            - Only deliveries with status 'pending' can be triggered.
            - Delivery's customer must be 'active'.
            - There must be at least one gateway in 'active' status.
            - Updates: set sent_at timestamp and set delivery_status to 'sent'. Optionally, add sample gateway_response.
        """

        if not delivery_ids or not isinstance(delivery_ids, list):
            return { "success": False, "error": "Parameter 'delivery_ids' must be a non-empty list." }

        # Gather all active gateways
        active_gateways = [gw for gw in self.sms_gateways.values() if gw['status'] == 'active']
        if not active_gateways:
            return { "success": False, "error": "No active SMS gateways are available." }

        details = {"sent": [], "skipped": {}}
        now_iso = datetime.utcnow().isoformat() + "Z"
    
        for did in delivery_ids:
            delivery = self.sms_deliveries.get(did)
            if not delivery:
                details["skipped"][did] = "Delivery does not exist"
                continue
        
            if delivery["delivery_status"] != "pending":
                details["skipped"][did] = f"Delivery status is '{delivery['delivery_status']}', not pending"
                continue

            customer_id = delivery.get("customer_id")
            customer = self.customers.get(customer_id)
            if not customer:
                details["skipped"][did] = f"Customer {customer_id} not found"
                continue
            if customer["status"] != "active":
                details["skipped"][did] = "Customer is not active"
                continue

            # Pick the first active gateway
            gateway = active_gateways[0]
            # Simulate sending: update fields
            delivery["delivery_status"] = "sent"
            delivery["sent_at"] = now_iso
            delivery["gateway_response"] = f"Queued via gateway {gateway['provider_name']}"
            details["sent"].append(did)
    
        if not details["sent"]:
            return {
                "success": False,
                "error": "No deliveries were eligible for sending.",
                "details": details
            }

        return {
            "success": True,
            "message": f"Triggered sending for {len(details['sent'])} deliveries.",
            "details": details
        }


    def update_delivery_status(
        self, 
        delivery_id: str, 
        new_status: str, 
        gateway_response: Optional[str] = None
    ) -> dict:
        """
        Update the delivery_status of a SMSDelivery.

        Args:
            delivery_id (str): The ID of the delivery record to update.
            new_status (str): The new delivery status ('pending', 'sent', 'delivered', 'failed').
            gateway_response (Optional[str]): Optional gateway system feedback to log.

        Returns:
            dict: {
                "success": True,
                "message": "Delivery status updated for delivery_id=..."
            }
            or
            {
                "success": False,
                "error":  "reason"
            }

        Constraints:
            - delivery_id must exist in the system.
            - new_status must be one of: 'pending', 'sent', 'delivered', 'failed'.
            - Timestamps: if new_status is 'sent', update sent_at; if 'delivered', update delivered_at.
        """
        allowed_statuses = {'pending', 'sent', 'delivered', 'failed'}
        delivery: Optional[Dict] = self.sms_deliveries.get(delivery_id)
        if not delivery:
            return {"success": False, "error": f"Delivery ID {delivery_id} does not exist"}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid delivery_status '{new_status}'"}

        # Update status
        delivery['delivery_status'] = new_status

        now_iso = datetime.utcnow().isoformat()

        if new_status == 'sent':
            delivery['sent_at'] = now_iso
            # Optionally clear delivered_at if status moves back
            if delivery.get('delivered_at') is not None:
                delivery['delivered_at'] = None
        elif new_status == 'delivered':
            # Set sent_at if not previously set
            if not delivery.get('sent_at'):
                delivery['sent_at'] = now_iso
            delivery['delivered_at'] = now_iso
        elif new_status in ['pending', 'failed']:
            # Clear delivered_at if not delivered
            if delivery.get('delivered_at') is not None:
                delivery['delivered_at'] = None
        # Optionally update gateway response
        if gateway_response is not None:
            delivery['gateway_response'] = gateway_response

        self.sms_deliveries[delivery_id] = delivery

        return {
            "success": True,
            "message": f"Delivery status updated for delivery_id={delivery_id}"
        }

    def add_new_customer(self, customer_id: str, name: str, phone_number: str) -> dict:
        """
        Register a new customer with validated phone number.

        Args:
            customer_id (str): Unique ID for the customer.
            name (str): Name of the customer.
            phone_number (str): Customer's phone number to validate.

        Returns:
            dict: Success or error message.
                - On success: { "success": True, "message": "Customer added successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - customer_id must be unique.
            - phone_number must pass validation and not already be assigned to another customer.
            - status is set to 'active' by default upon creation.
        """
        # Check if customer_id is unique
        if customer_id in self.customers:
            return { "success": False, "error": "Customer ID already exists" }

        # Validate phone number (format/logic using provided utility)
        validation_result = self.validate_phone_number(phone_number)
        if not validation_result.get("success") or not validation_result.get("data", {}).get("is_valid", False):
            return { "success": False, "error": "Invalid phone number format" }

        # Check if phone_number is already used by another customer
        for cust in self.customers.values():
            if cust["phone_number"] == phone_number:
                return { "success": False, "error": "Phone number already registered to another customer" }

        # Create new customer entry
        new_customer = {
            "customer_id": customer_id,
            "name": name,
            "phone_number": phone_number,
            "status": "active"
        }
        self.customers[customer_id] = new_customer

        return { "success": True, "message": "Customer added successfully" }

    def update_customer_status(self, customer_id: str, new_status: str) -> dict:
        """
        Change the status of a customer to 'active' or 'inactive'.

        Args:
            customer_id (str): The unique identifier for the customer.
            new_status (str): The new status to set ('active' or 'inactive').

        Returns:
            dict:
                - On success: { "success": True, "message": "Customer status updated" }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - Only updates existing customers.
            - Only allows status values 'active' or 'inactive'.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        if new_status not in {"active", "inactive"}:
            return {"success": False, "error": "Invalid status value"}

        self.customers[customer_id]["status"] = new_status
        return {"success": True, "message": "Customer status updated"}

    def add_sms_gateway(
        self, 
        gateway_id: str, 
        provider_name: str, 
        api_endpoint: str, 
        status: str
    ) -> dict:
        """
        Add/register a new SMS gateway into the system.
    
        Args:
            gateway_id (str): Unique identifier for the gateway.
            provider_name (str): Name of the gateway provider.
            api_endpoint (str): The API endpoint of the gateway.
            status (str): Status of the gateway ('active' or 'inactive' expected).
    
        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Gateway <gateway_id> added."}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - gateway_id must be unique.
            - status should be 'active' or 'inactive'.
            - All parameters must be non-empty strings.
        """
        if not (gateway_id and provider_name and api_endpoint and status):
            return {"success": False, "error": "All fields are required and must be non-empty."}
    
        if gateway_id in self.sms_gateways:
            return {"success": False, "error": f"Gateway ID '{gateway_id}' already exists."}
    
        if status not in {"active", "inactive"}:
            return {"success": False, "error": "Invalid status. Must be 'active' or 'inactive'."}
    
        gateway_info = {
            "gateway_id": gateway_id,
            "provider_name": provider_name,
            "api_endpoint": api_endpoint,
            "status": status
        }
        self.sms_gateways[gateway_id] = gateway_info
    
        return {"success": True, "message": f"Gateway '{gateway_id}' added."}

    def update_gateway_status(self, gateway_id: str, new_status: str) -> dict:
        """
        Change the operational status of a given SMS gateway.

        Args:
            gateway_id (str): Identifier of the SMS gateway to update.
            new_status (str): The new status to set ('active' or 'inactive').

        Returns:
            dict: {
                "success": True,
                "message": "Gateway status updated from <old> to <new>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The SMS gateway must exist.
            - Status should typically be 'active' or 'inactive'.
        """
        if gateway_id not in self.sms_gateways:
            return { "success": False, "error": "Gateway with the provided ID does not exist." }

        if new_status not in ("active", "inactive"):
            return { "success": False, "error": "Invalid status value. Must be 'active' or 'inactive'." }

        old_status = self.sms_gateways[gateway_id]["status"]
        self.sms_gateways[gateway_id]["status"] = new_status

        if old_status == new_status:
            return { "success": True, "message": f"Gateway status was already '{new_status}'." }
        else:
            return { "success": True, "message": f"Gateway status updated from '{old_status}' to '{new_status}'." }

    def retry_failed_deliveries(self) -> dict:
        """
        Attempt re-sending of all SMSDelivery records with 'failed' delivery_status,
        possibly using alternate gateways.

        Returns:
            dict: {
                'success': True,
                'message': str,
                'retried_delivery_ids': List[str],    # IDs of deliveries retried
                'skipped_delivery_ids': List[str],    # IDs of failed deliveries not retried (with reasons)
                'details': Dict[str, str]             # delivery_id → reason for skipped (or 'retried')
            }
            or
            {
                'success': False,
                'error': str
            }
        Constraints:
            - Only retry deliveries where customer is still active.
            - Only retry if there is at least one SMS gateway active.
            - Simulates resending: delivery_status set to 'pending', gateway_response cleared.
            - If possible, assign a different (random) active gateway (simulate this by adding gateway_response note).
        """

        # Prepare gateway selection
        active_gateways = [
            gw for gw in self.sms_gateways.values()
            if gw['status'] == 'active'
        ]
        if not active_gateways:
            return {
                'success': False,
                'error': "No active SMS gateways available for retry."
            }

        retried_ids = []
        skipped_ids = []
        details = {}

        for delivery_id, delivery in self.sms_deliveries.items():
            if delivery['delivery_status'] != 'failed':
                continue

            cust_id = delivery['customer_id']
            customer = self.customers.get(cust_id)
            if not customer:
                skipped_ids.append(delivery_id)
                details[delivery_id] = "Customer not found"
                continue
            if customer['status'].lower() != 'active':
                skipped_ids.append(delivery_id)
                details[delivery_id] = "Customer not active"
                continue

            # Pick a different (or the same if only one) active gateway
            # (Assume we store previous gateway_used in gateway_response, just note it)
            assigned_gateway = active_gateways[0]  # For simplicity; can randomize if desired.

            # Simulate retry: set as pending, clear gateway_response, update sent_at
            self.sms_deliveries[delivery_id]['delivery_status'] = 'pending'
            self.sms_deliveries[delivery_id]['sent_at'] = datetime.utcnow().isoformat()
            self.sms_deliveries[delivery_id]['delivered_at'] = None
            self.sms_deliveries[delivery_id]['gateway_response'] = (
                f"Retry initiated via gateway {assigned_gateway['provider_name']} (gateway_id: {assigned_gateway['gateway_id']})"
            )
            retried_ids.append(delivery_id)
            details[delivery_id] = "Retried"

        msg = f"{len(retried_ids)} failed deliveries resent. {len(skipped_ids)} deliveries not retried."
        return {
            'success': True,
            'message': msg,
            'retried_delivery_ids': retried_ids,
            'skipped_delivery_ids': skipped_ids,
            'details': details
        }

    def invalidate_phone_number(self, phone_number: str) -> dict:
        """
        Invalidate a phone number in the system: for any customer associated with this phone number,
        mark them as 'inactive'. If no customer has this phone number, report accordingly.
        Does not affect SMSDelivery history entries.
    
        Args:
            phone_number (str): The phone number to be invalidated.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number <X> invalidated"
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Only affects customers with matching phone_number.
            - Sets their 'status' attribute to 'inactive'.
            - If no such customer exists, returns an error.
            - Delivery records are left untouched for traceability.
        """
        found = False
        for customer in self.customers.values():
            if customer["phone_number"] == phone_number:
                found = True
                customer["status"] = "inactive"
        if not found:
            return {"success": False, "error": f"No customer with phone number {phone_number} found"}
        return {"success": True, "message": f"Phone number {phone_number} invalidated"}


class SMSNotificationManagementSystem(BaseEnv):
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

    def list_all_customers(self, **kwargs):
        return self._call_inner_tool('list_all_customers', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def get_active_customers(self, **kwargs):
        return self._call_inner_tool('get_active_customers', kwargs)

    def validate_phone_number(self, **kwargs):
        return self._call_inner_tool('validate_phone_number', kwargs)

    def list_all_sms_messages(self, **kwargs):
        return self._call_inner_tool('list_all_sms_messages', kwargs)

    def get_sms_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_sms_message_by_id', kwargs)

    def get_sms_messages_by_request_id(self, **kwargs):
        return self._call_inner_tool('get_sms_messages_by_request_id', kwargs)

    def list_sms_deliveries_by_message_id(self, **kwargs):
        return self._call_inner_tool('list_sms_deliveries_by_message_id', kwargs)

    def list_sms_deliveries_by_request_id(self, **kwargs):
        return self._call_inner_tool('list_sms_deliveries_by_request_id', kwargs)

    def get_delivery_status_by_delivery_id(self, **kwargs):
        return self._call_inner_tool('get_delivery_status_by_delivery_id', kwargs)

    def get_overall_delivery_status_by_request_id(self, **kwargs):
        return self._call_inner_tool('get_overall_delivery_status_by_request_id', kwargs)

    def list_active_gateways(self, **kwargs):
        return self._call_inner_tool('list_active_gateways', kwargs)

    def get_gateway_by_id(self, **kwargs):
        return self._call_inner_tool('get_gateway_by_id', kwargs)

    def check_gateway_status(self, **kwargs):
        return self._call_inner_tool('check_gateway_status', kwargs)

    def create_sms_message(self, **kwargs):
        return self._call_inner_tool('create_sms_message', kwargs)

    def create_batch_sms_deliveries(self, **kwargs):
        return self._call_inner_tool('create_batch_sms_deliveries', kwargs)

    def trigger_sms_send(self, **kwargs):
        return self._call_inner_tool('trigger_sms_send', kwargs)

    def update_delivery_status(self, **kwargs):
        return self._call_inner_tool('update_delivery_status', kwargs)

    def add_new_customer(self, **kwargs):
        return self._call_inner_tool('add_new_customer', kwargs)

    def update_customer_status(self, **kwargs):
        return self._call_inner_tool('update_customer_status', kwargs)

    def add_sms_gateway(self, **kwargs):
        return self._call_inner_tool('add_sms_gateway', kwargs)

    def update_gateway_status(self, **kwargs):
        return self._call_inner_tool('update_gateway_status', kwargs)

    def retry_failed_deliveries(self, **kwargs):
        return self._call_inner_tool('retry_failed_deliveries', kwargs)

    def invalidate_phone_number(self, **kwargs):
        return self._call_inner_tool('invalidate_phone_number', kwargs)
