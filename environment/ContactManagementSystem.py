# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ContactInfo(TypedDict):
    contact_id: str
    name: str
    phone_numbers: List[str]
    emails: List[str]
    addresses: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for a contact management system.
        """

        # Contacts: {contact_id: ContactInfo}
        # Maps each contact_id to a contact's information.
        self.contacts: Dict[str, ContactInfo] = {}

        # Constraints:
        # - Each contact must have a unique contact_id.
        # - Phone numbers, emails, and addresses can be multiple per contact.
        # - Contacts can be created, updated, deleted, and searched by various attributes (methods not yet implemented).

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Retrieve the complete contact information for a given contact_id.

        Args:
            contact_id (str): The unique identifier for the contact.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": ContactInfo
                }
                or
                {
                    "success": False,
                    "error": "Contact not found"
                }

        Constraints:
            - contact_id must exist in the system.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return { "success": False, "error": "Contact not found" }
        return { "success": True, "data": contact }

    def get_contacts_by_ids(self, contact_ids: list[str]) -> dict:
        """
        Retrieve contact information for a list of contact_ids in a single batch.

        Args:
            contact_ids (list[str]): List of unique contact identifiers to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # Only the contacts found are returned. List may be empty.
            }

        Constraints:
            - If contact_ids is empty, returns an empty list.
            - If a contact_id does not exist, it is skipped (no error).
        """
        result = [
            self.contacts[cid]
            for cid in contact_ids
            if cid in self.contacts
        ]
        return { "success": True, "data": result }

    def search_contacts_by_name(self, name_query: str) -> dict:
        """
        Find contacts whose name matches or partially matches the provided string (case-insensitive).

        Args:
            name_query (str): The substring or full string to search for in contact names.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List of matching contacts (may be empty)
            }

        Constraints:
            - The match is case-insensitive and partial (substring search).
            - No error if there are no matches; an empty list is returned.
        """
        lowered_query = name_query.lower()
        results = [
            contact for contact in self.contacts.values()
            if lowered_query in contact["name"].lower()
        ]
        return {"success": True, "data": results}

    def search_contacts_by_phone(self, phone_number: str) -> dict:
        """
        Finds and returns all contacts containing a specific phone number.

        Args:
            phone_number (str): The phone number to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # Contacts whose phone_numbers contain the given number
            }

        Constraints:
            - Exact match in contact's phone_numbers list.
            - No error is raised if no contacts are found; returns an empty list in that case.
        """
        matched_contacts = [
            contact for contact in self.contacts.values()
            if phone_number in contact.get("phone_numbers", [])
        ]
        return {"success": True, "data": matched_contacts}

    def search_contacts_by_email(self, email: str) -> dict:
        """
        Find all contacts containing the specified email address.

        Args:
            email (str): The email address to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List of contacts with the given email, may be empty
            }

        Constraints:
            - Email can appear in multiple contacts.
            - No error is returned if no contact matches (returns empty list).
        """
        result = [
            contact for contact in self.contacts.values()
            if email in contact["emails"]
        ]

        return {"success": True, "data": result}

    def search_contacts_by_address(self, address_query: str) -> dict:
        """
        Find contacts associated with a specific address substring.

        Args:
            address_query (str): Substring to search for within all addresses on each contact.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # All contacts where at least one address contains the substring.
            }
            or
            {
                "success": False,
                "error": str  # Error description if invalid input.
            }

        Constraints:
            - Searches are case-insensitive.
            - Address_query must be a non-empty string.
        """
        if not isinstance(address_query, str) or not address_query.strip():
            return { "success": False, "error": "address_query must be a non-empty string" }

        q = address_query.strip().lower()
        matching_contacts = [
            contact for contact in self.contacts.values()
            if any(q in address.lower() for address in contact.get("addresses", []))
        ]
        return { "success": True, "data": matching_contacts }

    def list_all_contacts(self) -> dict:
        """
        Retrieve the information of all contacts currently stored in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # List of all contacts; empty if none exist
            }

        Constraints:
            - No parameters required.
            - Always succeeds; returns [] if no contacts are present.
        """
        all_contacts = list(self.contacts.values())
        return { "success": True, "data": all_contacts }

    def add_contact(
        self,
        contact_id: str,
        name: str,
        phone_numbers: list,
        emails: list,
        addresses: list
    ) -> dict:
        """
        Create a new contact with a unique contact_id and associated information.

        Args:
            contact_id (str): Unique identifier for the contact.
            name (str): Contact person's name.
            phone_numbers (List[str]): List of phone numbers for the contact.
            emails (List[str]): List of email addresses for the contact.
            addresses (List[str]): List of street/postal addresses.

        Returns:
            dict: { "success": True, "message": "Contact <contact_id> added" }
                  OR
                  { "success": False, "error": "Contact ID already exists" }

        Constraints:
            - contact_id must be unique in the system.
            - phone_numbers, emails, addresses must be lists (empty lists allowed).
        """
        if contact_id in self.contacts:
            return { "success": False, "error": "Contact ID already exists" }

        # Defensive: ensure lists
        phone_numbers = phone_numbers if isinstance(phone_numbers, list) else []
        emails = emails if isinstance(emails, list) else []
        addresses = addresses if isinstance(addresses, list) else []

        new_contact: ContactInfo = {
            "contact_id": contact_id,
            "name": name,
            "phone_numbers": phone_numbers,
            "emails": emails,
            "addresses": addresses
        }
        self.contacts[contact_id] = new_contact

        return { "success": True, "message": f"Contact {contact_id} added" }

    def update_contact(
        self, 
        contact_id: str, 
        name: str, 
        phone_numbers: list, 
        emails: list, 
        addresses: list
    ) -> dict:
        """
        Update all information of the contact with the given contact_id.

        Args:
            contact_id (str): Unique identifier of the contact to update.
            name (str): New name.
            phone_numbers (List[str]): Full list of new phone numbers.
            emails (List[str]): Full list of new email addresses.
            addresses (List[str]): Full list of new addresses.

        Returns:
            dict: {
                "success": True,
                "message": "Contact (<contact_id>) updated successfully."
            }
            or
            {
                "success": False,
                "error": "Contact does not exist."
            }

        Constraints:
            - The contact must already exist (contact_id present in the system).
            - Entire contact information is replaced with the provided data.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist." }
    
        self.contacts[contact_id] = {
            "contact_id": contact_id,
            "name": name,
            "phone_numbers": list(phone_numbers),
            "emails": list(emails),
            "addresses": list(addresses)
        }
        return { "success": True, "message": f"Contact ({contact_id}) updated successfully." }

    def update_contact_partial(
        self,
        contact_id: str,
        name: str = None,
        phone_numbers: list = None,
        emails: list = None,
        addresses: list = None
    ) -> dict:
        """
        Partially update specific fields for an existing contact.

        Args:
            contact_id (str): The unique identifier for the contact.
            name (Optional[str]): New name (overwrites previous).
            phone_numbers (Optional[List[str]]): New list of phone numbers (overwrites previous).
            emails (Optional[List[str]]): New list of emails (overwrites previous).
            addresses (Optional[List[str]]): New list of addresses (overwrites previous).

        Returns:
            dict: {
                "success": True,
                "message": "Updated contact fields: ..."  # which fields were updated
            }
            OR
            {
                "success": False,
                "error": str  # error description
            }
        Constraints:
            - contact_id must exist.
            - Input types for each field must be correct if provided.
            - Each contact remains unique by contact_id.
        """
        if contact_id not in self.contacts:
            return {"success": False, "error": "Contact not found."}

        contact = self.contacts[contact_id]
        updated_fields = []

        if name is not None:
            if not isinstance(name, str):
                return {"success": False, "error": "Name must be a string."}
            contact["name"] = name
            updated_fields.append("name")

        if phone_numbers is not None:
            if not isinstance(phone_numbers, list) or not all(isinstance(p, str) for p in phone_numbers):
                return {"success": False, "error": "phone_numbers must be a list of strings."}
            contact["phone_numbers"] = phone_numbers
            updated_fields.append("phone_numbers")

        if emails is not None:
            if not isinstance(emails, list) or not all(isinstance(e, str) for e in emails):
                return {"success": False, "error": "emails must be a list of strings."}
            contact["emails"] = emails
            updated_fields.append("emails")

        if addresses is not None:
            if not isinstance(addresses, list) or not all(isinstance(a, str) for a in addresses):
                return {"success": False, "error": "addresses must be a list of strings."}
            contact["addresses"] = addresses
            updated_fields.append("addresses")

        if not updated_fields:
            return {"success": False, "error": "No fields provided to update."}

        self.contacts[contact_id] = contact
        return {
            "success": True,
            "message": f"Updated contact fields: {', '.join(updated_fields)}"
        }

    def add_phone_to_contact(self, contact_id: str, phone_number: str) -> dict:
        """
        Add a new phone number to the specified contact.

        Args:
            contact_id (str): The unique identifier of the contact record.
            phone_number (str): The phone number to add.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number added to contact."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The contact with `contact_id` must exist.
            - The `phone_number` must not already be present for the contact.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return {"success": False, "error": "Contact not found."}
        if phone_number in contact["phone_numbers"]:
            return {"success": False, "error": "Phone number already exists for this contact."}
        contact["phone_numbers"].append(phone_number)
        return {"success": True, "message": "Phone number added to contact."}

    def add_email_to_contact(self, contact_id: str, email: str) -> dict:
        """
        Add a new email address to an existing contact.

        Args:
            contact_id (str): The unique identifier of the contact to update.
            email (str): The email address to add.

        Returns:
            dict: 
                { "success": True, "message": "Email added to contact." }
                or
                { "success": False, "error": "Reason for failure." }

        Constraints:
            - The contact identified by contact_id must exist.
            - Do not add duplicate emails to a contact.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return { "success": False, "error": "Contact not found." }
        if email in contact['emails']:
            return { "success": False, "error": "Email already exists for this contact." }
        contact['emails'].append(email)
        return { "success": True, "message": "Email added to contact." }

    def add_address_to_contact(self, contact_id: str, address: str) -> dict:
        """
        Add a new address to an existing contact.

        Args:
            contact_id (str): Unique identifier for the contact.
            address (str): New address to be added.

        Returns:
            dict:
                {"success": True, "message": "Address added to contact <contact_id>"}
                or
                {"success": False, "error": "Contact not found"}
                or
                {"success": False, "error": "Address already exists for contact"}
    
        Constraints:
            - Contact must exist.
            - Address will not be added if it already exists in the contact's address list.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return { "success": False, "error": "Contact not found" }
        if address in contact["addresses"]:
            return { "success": False, "error": "Address already exists for contact" }
        contact["addresses"].append(address)
        return { "success": True, "message": f"Address added to contact {contact_id}" }

    def remove_phone_from_contact(self, contact_id: str, phone_number: str) -> dict:
        """
        Remove a phone number from the specified contact's record.

        Args:
            contact_id (str): Unique identifier of the contact.
            phone_number (str): The phone number to remove.

        Returns:
            dict: {"success": True, "message": "..."} on success,
                  {"success": False, "error": "..."} on failure.

        Constraints:
            - The contact must exist (contact_id must be present in the system).
            - The phone number must already be associated with the contact.
        """
        if contact_id not in self.contacts:
            return {"success": False, "error": f"Contact with id {contact_id} does not exist."}

        contact = self.contacts[contact_id]
        if phone_number not in contact["phone_numbers"]:
            return {"success": False, "error": f"Phone number {phone_number} not found in contact {contact_id}."}

        contact["phone_numbers"].remove(phone_number)
        return {
            "success": True,
            "message": f"Phone number {phone_number} removed from contact {contact_id}."
        }

    def remove_email_from_contact(self, contact_id: str, email: str) -> dict:
        """
        Remove an email address from a contact's record.

        Args:
            contact_id (str): The unique identifier of the contact.
            email (str): The email address to remove.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Email removed from contact."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The contact must exist.
            - The specified email must exist in the contact's emails list.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return {"success": False, "error": "Contact not found."}

        if email not in contact["emails"]:
            return {"success": False, "error": "Email address not found for contact."}

        contact["emails"].remove(email)
        return {"success": True, "message": "Email removed from contact."}

    def remove_address_from_contact(self, contact_id: str, address: str) -> dict:
        """
        Remove an address from a contact's record.

        Args:
            contact_id (str): Unique identifier of the contact.
            address (str): The address to remove from contact's addresses.

        Returns:
            dict: 
                On success: { "success": True, "message": "Address removed from contact." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The contact must exist.
            - The address must be present in the contact's addresses list.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return { "success": False, "error": "Contact does not exist." }
        if address not in contact["addresses"]:
            return { "success": False, "error": "Address not associated with this contact." }

        contact["addresses"].remove(address)
        return { "success": True, "message": "Address removed from contact." }

    def delete_contact(self, contact_id: str) -> dict:
        """
        Permanently delete a contact from the system by contact_id.

        Args:
            contact_id (str): The unique identifier of the contact to delete.

        Returns:
            dict: 
                - { "success": True, "message": "Contact deleted" } on success
                - { "success": False, "error": "Contact not found" } if contact_id does not exist

        Constraints:
            - Ensures only existing contacts can be deleted.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found" }
    
        del self.contacts[contact_id]
        return { "success": True, "message": "Contact deleted" }


class ContactManagementSystem(BaseEnv):
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

    def get_contact_by_id(self, **kwargs):
        return self._call_inner_tool('get_contact_by_id', kwargs)

    def get_contacts_by_ids(self, **kwargs):
        return self._call_inner_tool('get_contacts_by_ids', kwargs)

    def search_contacts_by_name(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_name', kwargs)

    def search_contacts_by_phone(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_phone', kwargs)

    def search_contacts_by_email(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_email', kwargs)

    def search_contacts_by_address(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_address', kwargs)

    def list_all_contacts(self, **kwargs):
        return self._call_inner_tool('list_all_contacts', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def update_contact(self, **kwargs):
        return self._call_inner_tool('update_contact', kwargs)

    def update_contact_partial(self, **kwargs):
        return self._call_inner_tool('update_contact_partial', kwargs)

    def add_phone_to_contact(self, **kwargs):
        return self._call_inner_tool('add_phone_to_contact', kwargs)

    def add_email_to_contact(self, **kwargs):
        return self._call_inner_tool('add_email_to_contact', kwargs)

    def add_address_to_contact(self, **kwargs):
        return self._call_inner_tool('add_address_to_contact', kwargs)

    def remove_phone_from_contact(self, **kwargs):
        return self._call_inner_tool('remove_phone_from_contact', kwargs)

    def remove_email_from_contact(self, **kwargs):
        return self._call_inner_tool('remove_email_from_contact', kwargs)

    def remove_address_from_contact(self, **kwargs):
        return self._call_inner_tool('remove_address_from_contact', kwargs)

    def delete_contact(self, **kwargs):
        return self._call_inner_tool('delete_contact', kwargs)

