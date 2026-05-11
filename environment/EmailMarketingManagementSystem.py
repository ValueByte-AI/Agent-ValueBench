# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import re
from typing import Any, Optional, Dict



class ContactInfo(TypedDict):
    contact_id: str
    name: str
    email: str
    status: str
    segment_tags: List[str]
    subscription_status: str
    custom_field: Dict[str, Any]

class ListInfo(TypedDict):
    list_id: str
    name: str
    description: str
    created_at: str
    contact_ids: List[str]  # Each list contains multiple contacts

class MessageInfo(TypedDict):
    message_id: str
    subject: str
    body: str
    sent_at: str
    status: str
    campaign_id: str
    recipient_ids: List[str]
    open_rate: float
    click_rate: float
    delivery_status: str  # Correcting 'delivery_sta'

class CampaignInfo(TypedDict):
    campaign_id: str
    name: str
    start_date: str
    end_date: str
    message_ids: List[str]
    list_ids: List[str]
    performance_metric: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        # Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}
        # Lists: {list_id: ListInfo}
        self.lists: Dict[str, ListInfo] = {}
        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}
        # Campaigns: {campaign_id: CampaignInfo}
        self.campaigns: Dict[str, CampaignInfo] = {}

        # Constraints:
        # - A contact may belong to multiple lists.
        # - A message can be sent to multiple contacts (directly or via lists).
        # - Message delivery and engagement metrics must be tracked per message and per campaign.
        # - Contacts must have a valid email and active subscription status to be sent messages.
        # - Deleting a contact removes them from all associated lists, but not from message history.

    def list_all_contacts(self) -> dict:
        """
        Retrieve all contacts in the system with their profiles, segmentation, and subscription status.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]
            }
            - List will be empty if no contacts exist.
        """
        all_contacts = list(self.contacts.values())
        return {
            "success": True,
            "data": all_contacts
        }

    def list_all_lists(self) -> dict:
        """
        Retrieve all recipient lists, including their metadata and the IDs of contacts in each list.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ListInfo],  # May be empty if no lists exist
            }
        """
        result = list(self.lists.values())
        return { "success": True, "data": result }

    def list_all_messages(self) -> dict:
        """
        Retrieve all message records in the system, including their subject, body, delivery status, and engagement metrics.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # All messages in the system (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error if retrieval fails
            }

        Constraints:
            - No access restrictions; all messages are returned.
        """
        if not isinstance(self.messages, dict):
            return {"success": False, "error": "Message records unavailable."}

        # Get all MessageInfo as a list
        messages_list = list(self.messages.values())
        return {"success": True, "data": messages_list}

    def list_all_campaigns(self) -> dict:
        """
        Retrieve all campaigns with their details, including associated lists and messages.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # List of all campaign info dicts (possibly empty)
            }
        """
        campaigns_list = list(self.campaigns.values())
        return { "success": True, "data": campaigns_list }

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Retrieve the full details for a specific contact with the given contact_id.

        Args:
            contact_id (str): Unique identifier of the contact to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ContactInfo dict with all values,
            }
            or
            {
                "success": False,
                "error": "Contact not found"
            }

        Constraints:
            - Returns error if contact_id does not exist in the system.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return {"success": False, "error": "Contact not found"}
        return {"success": True, "data": contact}

    def get_list_by_id(self, list_id: str) -> dict:
        """
        Retrieve the details and membership of a specific list by list_id.

        Args:
            list_id (str): Unique identifier for the list to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ListInfo  # full structure containing metadata and membership (contact_ids)
                    }
                On failure (if list_id does not exist):
                    {
                        "success": False,
                        "error": "List not found"
                    }

        Constraints:
            - List with given list_id must exist in the system.
        """
        list_info = self.lists.get(list_id)
        if list_info is None:
            return {"success": False, "error": "List not found"}
        return {"success": True, "data": list_info}

    def get_contacts_in_list(self, list_id: str) -> dict:
        """
        Retrieve all contact profiles belonging to a specific list.

        Args:
            list_id (str): The unique identifier for the list.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[ContactInfo] }
                - On failure: { "success": False, "error": str }

        Constraints:
            - The specified list must exist in the system.
            - Only includes contacts for which contact_id exists (skips missing/integrity-violated contacts).
        """
        if list_id not in self.lists:
            return { "success": False, "error": "List not found" }
    
        contact_ids = self.lists[list_id].get("contact_ids", [])
        contacts = [
            self.contacts[contact_id]
            for contact_id in contact_ids
            if contact_id in self.contacts
        ]
        return { "success": True, "data": contacts }

    def get_messages_in_campaign(self, campaign_id: str) -> dict:
        """
        Retrieve all messages (MessageInfo) associated with a given campaign.

        Args:
            campaign_id (str): The unique ID of the campaign.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo]  # May be empty if no messages are associated
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. campaign not found
            }
        Constraints:
            - None (query operation only, campaign must exist)
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        messages = [
            self.messages[mid]
            for mid in campaign.get("message_ids", [])
            if mid in self.messages
        ]

        return {"success": True, "data": messages}

    def get_campaign_performance(self, campaign_id: str) -> dict:
        """
        Retrieve summary performance metrics and reporting data for a given campaign.

        Args:
            campaign_id (str): Unique identifier of the campaign.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Any]  # campaign performance data and reporting summary
            }
            or
            {
                "success": False,
                "error": str  # reason for failure (e.g. campaign not found)
            }

        Constraints:
            - The campaign with campaign_id must exist in the system.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return { "success": False, "error": "Campaign not found" }

        # Return summary info, not just performance_metric for reporting clarity
        data = {
            "campaign_id": campaign["campaign_id"],
            "name": campaign["name"],
            "start_date": campaign["start_date"],
            "end_date": campaign["end_date"],
            "performance_metric": campaign.get("performance_metric", {}),
        }
        return {"success": True, "data": data}

    def get_message_metrics(self, message_id: str) -> dict:
        """
        Retrieve engagement metrics (open rate, click rate, delivery status) for a specified message.

        Args:
            message_id (str): The unique identifier for the message.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "open_rate": float,
                            "click_rate": float,
                            "delivery_status": str
                        }
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The message_id must exist in the system.
        """
        message = self.messages.get(message_id)
        if not message:
            return { "success": False, "error": "Message not found" }

        metrics = {
            "open_rate": message["open_rate"],
            "click_rate": message["click_rate"],
            "delivery_status": message["delivery_status"]
        }
        return {"success": True, "data": metrics}

    def filter_contacts_by_segment(self, segment_tags: list) -> dict:
        """
        List all contacts which have all specified segment_tags.

        Args:
            segment_tags (list of str): Tags to filter contacts by; must exist in contact's segment_tags.

        Returns:
            dict: {
                'success': True,
                'data': List[ContactInfo]   # May be empty if no contacts match.
            }
            or
            {
                'success': False,
                'error': str  # Reason for failure (e.g., invalid input)
            }

        Constraints:
            - If segment_tags is empty, all contacts should be returned.
        """
        if not isinstance(segment_tags, list) or any(not isinstance(tag, str) for tag in segment_tags):
            return {"success": False, "error": "segment_tags must be a list of strings"}

        # Empty filter means return all contacts
        if not segment_tags:
            result = list(self.contacts.values())
            return {"success": True, "data": result}

        result = [
            contact for contact in self.contacts.values()
            if all(tag in contact["segment_tags"] for tag in segment_tags)
        ]
        return {"success": True, "data": result}

    def add_contact(
        self,
        contact_id: str,
        name: str,
        email: str,
        status: str,
        segment_tags: list,
        subscription_status: str,
        custom_field: dict
    ) -> dict:
        """
        Add a new contact to the system.

        Args:
            contact_id (str): Unique identifier for the contact.
            name (str): Contact's name.
            email (str): Email address (must be valid).
            status (str): Status (e.g., 'active', 'inactive').
            segment_tags (list): Segmentation tags (list of strings).
            subscription_status (str): Contact's subscription status (e.g., 'active', 'unsubscribed').
            custom_field (dict): Any additional info.

        Returns:
            dict:
                On success: { "success": True, "message": "Contact added successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - contact_id must be unique.
            - email must be valid (roughly: contains '@' and '.').
        """
        if not contact_id or contact_id in self.contacts:
            return { "success": False, "error": "Contact ID already exists or is invalid" }

        if not isinstance(email, str) or '@' not in email or '.' not in email:
            return { "success": False, "error": "Invalid email address" }

        if not isinstance(segment_tags, list):
            return { "success": False, "error": "segment_tags must be a list" }

        # No explicit limits on subscription_status, so just record as given

        self.contacts[contact_id] = {
            "contact_id": contact_id,
            "name": name,
            "email": email,
            "status": status,
            "segment_tags": segment_tags,
            "subscription_status": subscription_status,
            "custom_field": custom_field
        }

        return { "success": True, "message": "Contact added successfully" }


    def update_contact(
        self,
        contact_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
        segment_tags: Optional[list] = None,
        subscription_status: Optional[str] = None,
        custom_field: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Modify the details, segmentation, or status of an existing contact.

        Args:
            contact_id (str): The ID of the contact to update.
            name (str, optional): New name for the contact.
            email (str, optional): New email address for the contact (must be valid).
            status (str, optional): New status.
            segment_tags (list, optional): New list of segment tags.
            subscription_status (str, optional): New subscription status.
            custom_field (dict, optional): New custom field values.

        Returns:
            dict: {
                'success': True,
                'message': 'Contact updated.'
            }
            or
            {
                'success': False,
                'error': <reason>
            }

        Constraints:
            - Contact must exist.
            - Email must be a valid format if changed.
            - Optionally, subscription_status should be to a known set (not enforced if not specified).
        """
        if contact_id not in self.contacts:
            return {"success": False, "error": "Contact does not exist"}

        contact = self.contacts[contact_id]

        # Validate email format if updating email
        if email is not None:
            email_pattern = r"(^[^@\s]+@[^@\s]+\.[^@\s]+$)"
            if not re.match(email_pattern, email):
                return {"success": False, "error": "Invalid email format"}
            contact["email"] = email

        if name is not None:
            contact["name"] = name

        if status is not None:
            contact["status"] = status

        if segment_tags is not None:
            if not isinstance(segment_tags, list):
                return {"success": False, "error": "segment_tags must be a list"}
            contact["segment_tags"] = segment_tags

        if subscription_status is not None:
            contact["subscription_status"] = subscription_status

        if custom_field is not None:
            if not isinstance(custom_field, dict):
                return {"success": False, "error": "custom_field must be a dictionary"}
            contact["custom_field"] = custom_field

        self.contacts[contact_id] = contact
        return {"success": True, "message": "Contact updated."}

    def delete_contact(self, contact_id: str) -> dict:
        """
        Remove a contact from the system and ensure they are removed from all associated lists,
        while preserving their history in past messages.

        Args:
            contact_id (str): Unique identifier of the contact to delete.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Contact <contact_id> deleted and removed from all lists." }
                - On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - Remove from all lists (contact_ids list in each ListInfo).
            - Do NOT remove from any message recipient/history.
            - If contact_id does not exist, return an error.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": f"Contact {contact_id} does not exist." }

        # Remove contact from all lists
        for list_info in self.lists.values():
            if contact_id in list_info["contact_ids"]:
                list_info["contact_ids"].remove(contact_id)

        # Remove contact from contacts
        del self.contacts[contact_id]

        return { "success": True, "message": f"Contact {contact_id} deleted and removed from all lists." }

    def add_list(
        self,
        list_id: str,
        name: str,
        description: str,
        created_at: str,
        contact_ids: list
    ) -> dict:
        """
        Create a new recipient list with a specified set of contacts.

        Args:
            list_id (str): Unique ID for the new list.
            name (str): Name for the new list.
            description (str): Description of the list.
            created_at (str): Creation timestamp (ISO8601 or suitable string).
            contact_ids (list[str]): List of contact IDs to include in this new list.

        Returns:
            dict -- Success or error message:
                {
                    "success": True,
                    "message": "List <name> created with N contacts."
                }
                or
                {
                    "success": False,
                    "error": "Reason for failure"
                }

        Constraints:
            - list_id must be unique.
            - contact_ids must all exist in the system.
        """
        # Validate input types
        if not isinstance(list_id, str) or not list_id.strip():
            return {"success": False, "error": "List ID must be a non-empty string."}
        if list_id in self.lists:
            return {"success": False, "error": f"List ID '{list_id}' already exists."}
        if not isinstance(contact_ids, list):
            return {"success": False, "error": "contact_ids must be a list."}
    
        # Validate contacts
        missing_contacts = [cid for cid in contact_ids if cid not in self.contacts]
        if missing_contacts:
            return {
                "success": False,
                "error": f"Contact IDs do not exist: {missing_contacts}"
            }

        # Create the new list info
        new_list: ListInfo = {
            "list_id": list_id,
            "name": name,
            "description": description,
            "created_at": created_at,
            "contact_ids": contact_ids.copy(),  # prevent accidental aliasing of the input
        }
        self.lists[list_id] = new_list

        return {
            "success": True,
            "message": f"List '{name}' created with {len(contact_ids)} contacts."
        }

    def update_list(
        self,
        list_id: str,
        name: str = None,
        description: str = None,
        contact_ids: list = None
    ) -> dict:
        """
        Modify metadata or contact membership of an existing list.

        Args:
            list_id (str): Identifier of the list to modify.
            name (str, optional): New name for the list.
            description (str, optional): New description for the list.
            contact_ids (list of str, optional): New list of contact IDs for list membership.

        Returns:
            dict: 
                - On success: { "success": True, "message": "List updated successfully" }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - list_id must exist
            - If updating contact_ids, all contact_ids must exist in self.contacts
            - At least one field must be provided for update (name, description, contact_ids)
        """
        if list_id not in self.lists:
            return { "success": False, "error": "List does not exist" }

        if name is None and description is None and contact_ids is None:
            return { "success": False, "error": "No fields provided to update" }

        list_info = self.lists[list_id]

        if name is not None:
            list_info["name"] = name

        if description is not None:
            list_info["description"] = description

        if contact_ids is not None:
            # Check that all contacts exist
            invalid_contacts = [cid for cid in contact_ids if cid not in self.contacts]
            if invalid_contacts:
                return {
                    "success": False,
                    "error": f"Contact IDs not found: {', '.join(invalid_contacts)}"
                }
            list_info["contact_ids"] = contact_ids

        self.lists[list_id] = list_info

        return { "success": True, "message": "List updated successfully" }

    def delete_list(self, list_id: str) -> dict:
        """
        Remove a recipient list from the system.

        Args:
            list_id (str): The unique identifier of the list to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "List <list_id> deleted."
            }
            or
            {
                "success": False,
                "error": "List not found."
            }

        Constraints:
            - Deleting a list removes it from the system.
            - For consistency, any campaigns referencing this list in their list_ids will have it removed from their list_ids.
            - Contacts referenced in the list are unaffected.
        """
        if list_id not in self.lists:
            return {"success": False, "error": "List not found."}

        # Remove the list
        del self.lists[list_id]

        # Remove references from campaigns
        for campaign in self.campaigns.values():
            if list_id in campaign.get("list_ids", []):
                campaign["list_ids"] = [lid for lid in campaign["list_ids"] if lid != list_id]

        return {"success": True, "message": f"List {list_id} deleted."}

    def add_contact_to_list(self, contact_id: str, list_id: str) -> dict:
        """
        Add an existing contact to a specified recipient list.

        Args:
            contact_id (str): The ID of the contact to add.
            list_id (str): The ID of the list to add the contact to.

        Returns:
            dict: {
                "success": True,
                "message": "Contact added to list."
            }
            or
            {
                "success": False,
                "error": str  # Error message if contact/list does not exist or already in list
            }

        Constraints:
            - The contact must exist.
            - The list must exist.
            - Do not add the same contact to the list more than once.
        """
        if contact_id not in self.contacts:
            return {"success": False, "error": "Contact does not exist."}
        if list_id not in self.lists:
            return {"success": False, "error": "List does not exist."}
    
        list_info = self.lists[list_id]
    
        if contact_id in list_info["contact_ids"]:
            return {"success": False, "error": "Contact already in the list."}
    
        list_info["contact_ids"].append(contact_id)
        return {"success": True, "message": "Contact added to list."}

    def remove_contact_from_list(self, contact_id: str, list_id: str) -> dict:
        """
        Remove a contact from a specified list.

        Args:
            contact_id (str): The ID of the contact to remove.
            list_id (str): The ID of the list from which to remove the contact.

        Returns:
            dict: 
                {"success": True, "message": "Contact <contact_id> removed from list <list_id>."}
            or 
                {"success": False, "error": "<reason>"}

        Constraints:
            - The list with list_id must exist.
            - The contact with contact_id must exist.
            - The contact must be present in the list; if not, inform the user.
        """
        if list_id not in self.lists:
            return { "success": False, "error": f"List with id '{list_id}' does not exist." }

        if contact_id not in self.contacts:
            return { "success": False, "error": f"Contact with id '{contact_id}' does not exist." }

        contact_ids = self.lists[list_id]["contact_ids"]
        if contact_id not in contact_ids:
            return { "success": False, "error": f"Contact '{contact_id}' is not in list '{list_id}'." }

        # Remove contact from list's contact_ids
        self.lists[list_id]["contact_ids"] = [cid for cid in contact_ids if cid != contact_id]

        return { "success": True, "message": f"Contact '{contact_id}' removed from list '{list_id}'." }

    def add_message(
        self,
        message_id: str,
        subject: str,
        body: str,
        sent_at: str,
        status: str,
        campaign_id: str,
        recipient_ids: list,
        open_rate: float = 0.0,
        click_rate: float = 0.0,
        delivery_status: str = "pending"
    ) -> dict:
        """
        Create and store a new message for campaign use.

        Args:
            message_id (str): Unique identifier for the message.
            subject (str): Email subject.
            body (str): Email body/content.
            sent_at (str): Scheduled or actual sent time as string.
            status (str): 'draft', 'scheduled', 'sent', etc.
            campaign_id (str): The campaign this message is part of.
            recipient_ids (List[str]): List of contact IDs to receive the message.
            open_rate (float, optional): Initial open rate. Defaults to 0.0.
            click_rate (float, optional): Initial click rate. Defaults to 0.0.
            delivery_status (str, optional): Delivery status. Defaults to 'pending'.

        Returns:
            dict: Success or error message.
        Constraints:
            - message_id must be unique.
            - campaign_id must exist.
            - recipient_ids must refer to existing contacts.
        """
        # Check uniqueness of message_id
        if message_id in self.messages:
            return {"success": False, "error": "Message ID already exists."}

        # Check campaign existence
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Associated campaign does not exist."}

        # Ensure all recipient_ids are valid contacts
        invalid_contacts = [cid for cid in recipient_ids if cid not in self.contacts]
        if invalid_contacts:
            return {
                "success": False,
                "error": f"Invalid recipient contact IDs: {invalid_contacts}"
            }

        # Create the message info
        self.messages[message_id] = {
            "message_id": message_id,
            "subject": subject,
            "body": body,
            "sent_at": sent_at,
            "status": status,
            "campaign_id": campaign_id,
            "recipient_ids": recipient_ids,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "delivery_status": delivery_status
        }

        # Optionally, update the campaign's message list
        if "message_ids" in self.campaigns[campaign_id]:
            self.campaigns[campaign_id]["message_ids"].append(message_id)
        else:
            self.campaigns[campaign_id]["message_ids"] = [message_id]

        return {"success": True, "message": f"Message {message_id} created successfully."}

    def update_message(self, message_id: str, updates: dict) -> dict:
        """
        Edit the contents or status of an existing message.

        Args:
            message_id (str): The ID of the message to update.
            updates (dict): Dictionary of fields and their new values to update in the message.
                            Allowed keys: any in MessageInfo except message_id.
                            Example: { "subject": "New Subject", "status": "sent", "body": "Updated content" }

        Returns:
            dict: {
                "success": True,
                "message": "Message <message_id> updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The message must exist.
            - Only update allowed fields (ignore 'message_id').
            - If no valid fields provided, operation fails.
        """
        if message_id not in self.messages:
            return { "success": False, "error": "Message not found" }

        allowed_fields = set([
            "subject", "body", "sent_at", "status", "campaign_id", "recipient_ids",
            "open_rate", "click_rate", "delivery_status"
        ])
        msg_info = self.messages[message_id]
        updated = False

        for key, value in updates.items():
            if key not in allowed_fields:
                continue
            # Simple type guard for open_rate/click_rate:
            if key in ("open_rate", "click_rate"):
                if not (isinstance(value, (float, int)) and 0.0 <= value <= 1.0):
                    return { "success": False, "error": f"{key} must be a float between 0 and 1" }
                value = float(value)
            if key == "recipient_ids":
                if not (isinstance(value, list) and all(isinstance(cid, str) for cid in value)):
                    return { "success": False, "error": "recipient_ids must be a list of contact_id strings" }
            msg_info[key] = value
            updated = True

        if not updated:
            return { "success": False, "error": "No valid fields provided to update" }

        self.messages[message_id] = msg_info
        return { "success": True, "message": f"Message {message_id} updated successfully" }

    def delete_message(self, message_id: str) -> dict:
        """
        Remove a message from the system.
        Also removes the message ID from any associated campaigns' 'message_ids' lists.

        Args:
            message_id (str): The unique identifier of the message to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Message <message_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Message not found."
            }

        Constraints:
            - If the message_id does not exist, this operation fails.
            - Removes message_id from any CampaignInfo.message_ids fields where present.
        """
        if message_id not in self.messages:
            return { "success": False, "error": "Message not found." }

        # Remove message from messages dict
        del self.messages[message_id]

        # Remove the message_id from any campaigns it is linked to
        for campaign in self.campaigns.values():
            if message_id in campaign['message_ids']:
                campaign['message_ids'] = [
                    mid for mid in campaign['message_ids'] if mid != message_id
                ]

        return { "success": True, "message": f"Message {message_id} deleted successfully." }

    def record_message_delivery(self, message_id: str, delivery_status: str, sent_at: str) -> dict:
        """
        Update the delivery_status and sent_at of a message when it is sent.

        Args:
            message_id (str): The unique identifier of the message to update.
            delivery_status (str): The new delivery status (e.g., "sent", "queued", "failed").
            sent_at (str): The timestamp (ISO string) indicating when the message was sent.

        Returns:
            dict: Success message or error.

        Constraints:
            - The message_id must exist within self.messages.
            - Fields 'delivery_status' and 'sent_at' will be updated accordingly.
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message with given ID does not exist."}

        msg = self.messages[message_id]
        msg["delivery_status"] = delivery_status
        msg["sent_at"] = sent_at
        # Optionally update status field if that's semantically needed
        if delivery_status.lower() == "sent":
            msg["status"] = "sent"

        return {"success": True, "message": "Message delivery recorded."}

    def record_engagement_metric(
        self,
        object_type: str,
        object_id: str,
        open_rate: float = None,
        click_rate: float = None
    ) -> dict:
        """
        Update engagement metrics (open_rate and/or click_rate) for a given message or campaign.

        Args:
            object_type (str): Either 'message' or 'campaign'.
            object_id (str): ID of the target message or campaign.
            open_rate (float, optional): New open rate value (0.0–1.0).
            click_rate (float, optional): New click rate value (0.0–1.0).

        Returns:
            dict: {
                "success": True, "message": "Engagement metric updated for <object_type> <object_id>."
            }
            or
            {
                "success": False, "error": <error description>
            }

        Constraints:
            - object_type must be 'message' or 'campaign'.
            - object_id must exist in the relevant dictionary.
            - open_rate and click_rate (if provided) must be between 0 and 1.
            - At least one metric value must be provided.
        """
        object_type = object_type.lower()
        if object_type not in {"message", "campaign"}:
            return {"success": False, "error": "object_type must be 'message' or 'campaign'."}
        if open_rate is None and click_rate is None:
            return {"success": False, "error": "No engagement metric (open_rate or click_rate) provided."}
        if open_rate is not None:
            if not (0.0 <= open_rate <= 1.0):
                return {"success": False, "error": "open_rate must be between 0 and 1."}
        if click_rate is not None:
            if not (0.0 <= click_rate <= 1.0):
                return {"success": False, "error": "click_rate must be between 0 and 1."}

        if object_type == "message":
            if object_id not in self.messages:
                return {"success": False, "error": f"Message {object_id} does not exist."}
            msg = self.messages[object_id]
            if open_rate is not None:
                msg["open_rate"] = open_rate
            if click_rate is not None:
                msg["click_rate"] = click_rate
        elif object_type == "campaign":
            if object_id not in self.campaigns:
                return {"success": False, "error": f"Campaign {object_id} does not exist."}
            camp = self.campaigns[object_id]
            if "performance_metric" not in camp or not isinstance(camp["performance_metric"], dict):
                camp["performance_metric"] = {}
            if open_rate is not None:
                camp["performance_metric"]["open_rate"] = open_rate
            if click_rate is not None:
                camp["performance_metric"]["click_rate"] = click_rate

        return {
            "success": True,
            "message": f"Engagement metric updated for {object_type} {object_id}."
        }

    def add_campaign(
        self,
        campaign_id: str,
        name: str,
        start_date: str,
        end_date: str,
        message_ids: list,
        list_ids: list,
        performance_metric: dict
    ) -> dict:
        """
        Create a new campaign, associating lists and messages.

        Args:
            campaign_id (str): Unique identifier for the campaign.
            name (str): Name of the campaign.
            start_date (str): Starting date of the campaign.
            end_date (str): End date of the campaign.
            message_ids (List[str]): List of message IDs to associate.
            list_ids (List[str]): List of list IDs to associate.
            performance_metric (Dict[str, Any]): Performance metrics for the campaign.

        Returns:
            dict: Success or error message indicating result of the operation.

        Constraints:
            - campaign_id must be unique.
            - All message_ids must exist in self.messages.
            - All list_ids must exist in self.lists.
        """

        if campaign_id in self.campaigns:
            return {"success": False, "error": f"Campaign with id '{campaign_id}' already exists."}

        invalid_messages = [mid for mid in message_ids if mid not in self.messages]
        if invalid_messages:
            return {
                "success": False,
                "error": f"Message IDs not found: {invalid_messages}"
            }

        invalid_lists = [lid for lid in list_ids if lid not in self.lists]
        if invalid_lists:
            return {
                "success": False,
                "error": f"List IDs not found: {invalid_lists}"
            }

        campaign_info: CampaignInfo = {
            "campaign_id": campaign_id,
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "message_ids": list(message_ids),
            "list_ids": list(list_ids),
            "performance_metric": dict(performance_metric) if performance_metric is not None else {}
        }
        self.campaigns[campaign_id] = campaign_info
        return {
            "success": True,
            "message": f"Campaign '{campaign_id}' successfully created and associated with specified lists and messages."
        }

    def update_campaign(
        self,
        campaign_id: str,
        name: str = None,
        start_date: str = None,
        end_date: str = None,
        message_ids: list = None,
        list_ids: list = None,
        performance_metric: dict = None
    ) -> dict:
        """
        Edit details, message roster, or associated lists for a campaign.

        Args:
            campaign_id (str): The campaign to update (required).
            name (str, optional): New campaign name.
            start_date (str, optional): New start date.
            end_date (str, optional): New end date.
            message_ids (list, optional): New list of associated message_ids.
            list_ids (list, optional): New list of associated list_ids.
            performance_metric (dict, optional): Updated performance metrics.

        Returns:
            dict: {
                "success": True,
                "message": "Campaign updated successfully"
            }
            or error:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - campaign_id must exist.
            - Any new message_ids/list_ids (if given) must exist in the system.
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign does not exist"}

        campaign = self.campaigns[campaign_id]

        if name is not None:
            campaign["name"] = name

        if start_date is not None:
            campaign["start_date"] = start_date

        if end_date is not None:
            campaign["end_date"] = end_date

        if message_ids is not None:
            # Validate all message_ids exist
            for mid in message_ids:
                if mid not in self.messages:
                    return {"success": False, "error": f"Message ID '{mid}' does not exist"}
            campaign["message_ids"] = message_ids

        if list_ids is not None:
            # Validate all list_ids exist
            for lid in list_ids:
                if lid not in self.lists:
                    return {"success": False, "error": f"List ID '{lid}' does not exist"}
            campaign["list_ids"] = list_ids

        if performance_metric is not None:
            campaign["performance_metric"] = performance_metric

        # Save changes
        self.campaigns[campaign_id] = campaign

        return {"success": True, "message": "Campaign updated successfully"}

    def delete_campaign(self, campaign_id: str) -> dict:
        """
        Remove a campaign and its report (performance metrics) from the system.
    
        Args:
            campaign_id (str): Unique identifier of the campaign to delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Campaign <campaign_id> deleted." }
                On failure: { "success": False, "error": "Campaign not found." }

        Constraints:
            - Deletion only removes the campaign object and its performance data.
            - Associated messages, lists, and contacts are NOT deleted.
            - If the campaign_id does not exist, operation fails.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign not found." }
        del self.campaigns[campaign_id]
        return { "success": True, "message": f"Campaign {campaign_id} deleted." }


class EmailMarketingManagementSystem(BaseEnv):
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

    def list_all_contacts(self, **kwargs):
        return self._call_inner_tool('list_all_contacts', kwargs)

    def list_all_lists(self, **kwargs):
        return self._call_inner_tool('list_all_lists', kwargs)

    def list_all_messages(self, **kwargs):
        return self._call_inner_tool('list_all_messages', kwargs)

    def list_all_campaigns(self, **kwargs):
        return self._call_inner_tool('list_all_campaigns', kwargs)

    def get_contact_by_id(self, **kwargs):
        return self._call_inner_tool('get_contact_by_id', kwargs)

    def get_list_by_id(self, **kwargs):
        return self._call_inner_tool('get_list_by_id', kwargs)

    def get_contacts_in_list(self, **kwargs):
        return self._call_inner_tool('get_contacts_in_list', kwargs)

    def get_messages_in_campaign(self, **kwargs):
        return self._call_inner_tool('get_messages_in_campaign', kwargs)

    def get_campaign_performance(self, **kwargs):
        return self._call_inner_tool('get_campaign_performance', kwargs)

    def get_message_metrics(self, **kwargs):
        return self._call_inner_tool('get_message_metrics', kwargs)

    def filter_contacts_by_segment(self, **kwargs):
        return self._call_inner_tool('filter_contacts_by_segment', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def update_contact(self, **kwargs):
        return self._call_inner_tool('update_contact', kwargs)

    def delete_contact(self, **kwargs):
        return self._call_inner_tool('delete_contact', kwargs)

    def add_list(self, **kwargs):
        return self._call_inner_tool('add_list', kwargs)

    def update_list(self, **kwargs):
        return self._call_inner_tool('update_list', kwargs)

    def delete_list(self, **kwargs):
        return self._call_inner_tool('delete_list', kwargs)

    def add_contact_to_list(self, **kwargs):
        return self._call_inner_tool('add_contact_to_list', kwargs)

    def remove_contact_from_list(self, **kwargs):
        return self._call_inner_tool('remove_contact_from_list', kwargs)

    def add_message(self, **kwargs):
        return self._call_inner_tool('add_message', kwargs)

    def update_message(self, **kwargs):
        return self._call_inner_tool('update_message', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

    def record_message_delivery(self, **kwargs):
        return self._call_inner_tool('record_message_delivery', kwargs)

    def record_engagement_metric(self, **kwargs):
        return self._call_inner_tool('record_engagement_metric', kwargs)

    def add_campaign(self, **kwargs):
        return self._call_inner_tool('add_campaign', kwargs)

    def update_campaign(self, **kwargs):
        return self._call_inner_tool('update_campaign', kwargs)

    def delete_campaign(self, **kwargs):
        return self._call_inner_tool('delete_campaign', kwargs)

