# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
import re
import uuid
from typing import List, Optional, Dict, Any
from typing import Dict
from typing import Optional, Dict



class ContactInfo(TypedDict):
    contact_id: str
    name: str
    location: str
    organization_id: Optional[str]
    communication_method: List[str]  # List of method_ids

class CommunicationMethodInfo(TypedDict):
    method_id: str
    contact_id: str
    type: str  # e.g., 'email', 'phone'
    value: str

class OrganizationInfo(TypedDict):
    organization_id: str
    name: str
    address: str

class InteractionInfo(TypedDict):
    interaction_id: str
    contact_id: str
    date: str
    type: str
    note: str

_UNSET = object()

class _GeneratedEnvImpl:
    def __init__(self):
        # Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}
        # Communication Methods: {method_id: CommunicationMethodInfo}
        self.communication_methods: Dict[str, CommunicationMethodInfo] = {}
        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}
        # Interactions: {interaction_id: InteractionInfo}
        self.interactions: Dict[str, InteractionInfo] = {}

        # Constraints:
        # - Each contact must have at least one communication method on record (see contacts, communication_methods).
        # - Contact names and locations are searchable.
        # - Each contact may (but does not have to) be affiliated with an organization (organization_id optional in ContactInfo).
        # - Communication methods must be valid for their specified type (e.g., email format).

    @staticmethod
    def _is_valid_email(value: str) -> bool:
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", value))

    @staticmethod
    def _is_valid_phone(value: str) -> bool:
        if not isinstance(value, str):
            return False
        digits = re.sub(r"\D", "", value)
        return bool(re.match(r"^[0-9\-\+ ]{7,}$", value)) and 7 <= len(digits) <= 15

    def search_contacts_by_name(self, name_query: str) -> dict:
        """
        Search for contacts whose name matches (partially or fully, case-insensitive) the provided query string.

        Args:
            name_query (str): The (partial or full) name to search for (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List may be empty if no matches.
            }
            or
            {
                "success": False,
                "error": str  # On invalid input (e.g., empty query)
            }
        """
        if not isinstance(name_query, str) or name_query.strip() == "":
            return {"success": False, "error": "Query string cannot be empty."}

        lower_query = name_query.strip().lower()
        results = [
            contact for contact in self.contacts.values()
            if lower_query in contact["name"].lower()
        ]
        return {"success": True, "data": results}

    def search_contacts_by_location(self, location: str) -> dict:
        """
        Search for contacts whose location matches the provided geographic location.

        Args:
            location (str): The location string to match (case-insensitive, exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List of matching contacts (may be empty)
            }

        Constraints:
            - Match is case-insensitive and must be exact on the 'location' field.
            - No error returned for zero matches.
        """
        if not isinstance(location, str) or not location.strip():
            # Empty search location is considered invalid (can also be treated as returning all contacts, but specs suggest matching needed)
            return {"success": True, "data": []}

        matches = [
            contact
            for contact in self.contacts.values()
            if contact["location"].strip().lower() == location.strip().lower()
        ]
        return {"success": True, "data": matches}

    def search_contacts_by_name_and_location(self, name: str, location: str) -> dict:
        """
        Search for contacts matching both a given name and location.

        Args:
            name (str): The name to search for (exact match).
            location (str): The location to search for (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # All matching contacts (empty if none found)
            }
        """
        result = [
            contact
            for contact in self.contacts.values()
            if contact["name"] == name and contact["location"] == location
        ]
        return { "success": True, "data": result }

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Retrieve the full profile data for a contact using their contact_id.

        Args:
            contact_id (str): The unique identifier of the contact.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": ContactInfo
                  }
                - On failure: {
                      "success": False,
                      "error": str
                  }

        Constraints:
            - contact_id must exist in the CRM system.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return {"success": False, "error": "Contact not found"}
        return {"success": True, "data": contact}

    def get_communication_methods_for_contact(self, contact_id: str) -> dict:
        """
        List all communication methods associated with a specific contact.

        Args:
            contact_id (str): The ID of the contact whose communication methods are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[CommunicationMethodInfo],  # List of communication methods for the contact
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. "Contact not found"
            }
        Constraints:
            - Contact must exist in the CRM system.
            - Only actual, existing communication methods will be returned (dangling/invalid method_ids are ignored).
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found" }
        contact = self.contacts[contact_id]
        method_ids = contact.get('communication_method', [])
        methods = [
            self.communication_methods[method_id]
            for method_id in method_ids
            if method_id in self.communication_methods
        ]
        return { "success": True, "data": methods }

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve detailed information about an organization given its organization_id.

        Args:
            organization_id (str): Unique identifier for the organization.

        Returns:
            dict: {
                "success": True,
                "data": OrganizationInfo
            }
            or
            {
                "success": False,
                "error": "Organization not found"
            }

        Constraints:
            - Organization ID must exist in the system.
        """
        org = self.organizations.get(organization_id)
        if org is not None:
            return {"success": True, "data": org}
        else:
            return {"success": False, "error": "Organization not found"}

    def get_contact_organization(self, contact_id: str) -> dict:
        """
        Retrieve the organization affiliation details for a contact, if any.

        Args:
            contact_id (str): The ID of the contact.

        Returns:
            dict:
                - If the contact exists and is affiliated:
                    {"success": True, "data": OrganizationInfo}
                - If the contact exists but is unaffiliated:
                    {"success": True, "data": None}
                - If the contact not found:
                    {"success": False, "error": "Contact not found"}
                - If the organization reference is broken:
                    {"success": False, "error": "Organization not found for this contact"}

        Constraints:
            - Organization affiliation is optional (organization_id may be None).
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return {"success": False, "error": "Contact not found"}

        organization_id = contact.get("organization_id")
        if not organization_id:
            return {"success": True, "data": None}

        organization = self.organizations.get(organization_id)
        if not organization:
            return {"success": False, "error": "Organization not found for this contact"}

        return {"success": True, "data": organization}

    def get_interactions_for_contact(self, contact_id: str) -> dict:
        """
        Retrieve all recorded interactions associated with the specified contact.

        Args:
            contact_id (str): The unique identifier for the contact.

        Returns:
            dict: {
                "success": True,
                "data": List[InteractionInfo]  # List of the contact's interactions (can be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., contact does not exist
            }

        Constraints:
            - The contact must exist in the CRM.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist" }

        interactions = [
            interaction for interaction in self.interactions.values()
            if interaction["contact_id"] == contact_id
        ]

        return { "success": True, "data": interactions }


    def communication_method_validity_check(self, type: str, value: str) -> dict:
        """
        Verify that a given communication method value conforms to its type specification.

        Args:
            type (str): Type of communication method (e.g., 'email', 'phone').
            value (str): The value to validate (e.g., email address, phone number).

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if valid, False if invalid
            }
            OR
            {
                "success": False,
                "error": str  # Description of error (e.g. unsupported type)
            }

        Supported types:
            - 'email': Must be a valid email format.
            - 'phone': Must be a plausible international or local phone number.

        Constraints:
            - Only simple format validation is performed.
        """
        if type == "email":
            # Simple regex for email validation
            pattern = r"^[A-Za-z0-9\._%+-]+@[A-Za-z0-9\.-]+\.[A-Za-z]{2,}$"
            is_valid = bool(re.fullmatch(pattern, value))
            return {"success": True, "data": is_valid}
        elif type == "phone":
            # Allow international or local, but just check for digits and some symbols, minimum 7 digits
            pattern = r"^[\d\+\-\s\(\)]{7,}$"
            digits = re.sub(r"\D", "", value)
            is_valid = bool(re.fullmatch(pattern, value)) and len(digits) >= 7
            return {"success": True, "data": is_valid}
        else:
            return {"success": False, "error": "Unsupported communication method type"}

    def list_all_contacts(self) -> dict:
        """
        Retrieve a list of all contacts in the CRM system.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ContactInfo]  # List of all contacts (may be empty if none)
                    }
        """
        contacts_list = list(self.contacts.values())
        return {"success": True, "data": contacts_list}

    def get_contacts_in_organization(self, organization_id: str) -> dict:
        """
        List all contacts affiliated with a given organization.

        Args:
            organization_id (str): The unique ID of the target organization.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # List of contacts with matching organization_id, possibly empty.
            }
            or
            {
                "success": False,
                "error": str  # Indicates if the organization does not exist.
            }

        Constraints:
            - organization_id must exist in the CRM system.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        result = [
            contact for contact in self.contacts.values()
            if contact.get("organization_id") == organization_id
        ]
        return { "success": True, "data": result }


    def add_new_contact(
        self, 
        contact_id: str, 
        name: str, 
        location: str, 
        communication_methods: List[Dict[str, str]], 
        organization_id: Optional[str] = None
    ) -> dict:
        """
        Add a new contact to the CRM, ensuring at least one valid communication method exists.

        Args:
            contact_id (str): Unique identifier for the contact.
            name (str): Name of the contact.
            location (str): Location of the contact.
            communication_methods (List[Dict[str, str]]): Each dict contains:
                - 'type': str (e.g., 'email', 'phone')
                - 'value': str (value for that type)
            organization_id (Optional[str]): ID of affiliated organization (or None).

        Returns:
            dict: {
                'success': True,
                'message': str,  # description of successful addition
                'contact_id': str
            }
            or
            {
                'success': False,
                'error': str
            }

        Constraints:
            - Must provide at least one valid communication method.
            - contact_id must be unique.
            - organization_id must exist (if provided).
            - Communication methods validated for type.
            - Communication method ids generated to be unique.
        """
        # Check unique contact_id
        if contact_id in self.contacts:
            return {"success": False, "error": "Contact ID already exists"}

        # At least one communication method required
        if not communication_methods or len(communication_methods) == 0:
            return {"success": False, "error": "At least one communication method is required"}

        # Organization exists (if provided)
        if organization_id is not None and organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        # Validate communication methods and prepare method entries
        created_method_ids = []
        for i, method in enumerate(communication_methods):
            mtype = method.get("type")
            value = method.get("value")
            if not mtype or not value:
                return {"success": False, "error": f"Communication method missing type or value"}
            # Validate type/value
            if mtype == "email":
                if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
                    return {"success": False, "error": f"Invalid email format: {value}"}
            elif mtype == "phone":
                if not re.match(r"^[\d\s\-\+\(\)]+$", value):
                    return {"success": False, "error": f"Invalid phone number format: {value}"}
            # Extend with other types as needed

            # Generate a unique method_id
            while True:
                method_id = str(uuid.uuid4())
                if method_id not in self.communication_methods:
                    break
            created_method_ids.append(method_id)
            comm_method_info = {
                "method_id": method_id,
                "contact_id": contact_id,
                "type": mtype,
                "value": value
            }
            self.communication_methods[method_id] = comm_method_info

        # Create and add the contact
        contact_info = {
            "contact_id": contact_id,
            "name": name,
            "location": location,
            "organization_id": organization_id,
            "communication_method": created_method_ids
        }
        self.contacts[contact_id] = contact_info

        return {
            "success": True,
            "message": f"Contact {name} added successfully.",
            "contact_id": contact_id
        }

    def update_contact_info(
        self, 
        contact_id: str, 
        name: Optional[str] = None, 
        location: Optional[str] = None, 
        organization_id: Any = _UNSET
    ) -> dict:
        """
        Edit the profile information for an existing contact.
        Only the provided fields will be updated.

        Args:
            contact_id (str): The ID of the contact to update.
            name (Optional[str]): New name (if any).
            location (Optional[str]): New location (if any).
            organization_id (Optional[str]): New organization_id (if any). If None, will disaffiliate the contact.

        Returns:
            dict: {
                "success": True,
                "message": "Contact info updated"
            } or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - contact_id must exist.
            - If organization_id is provided and not None, must exist in self.organizations.
        """
        # Check that contact exists
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found" }
    
        contact = self.contacts[contact_id]
        updated = False

        # Update name
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return { "success": False, "error": "Invalid name" }
            contact["name"] = name.strip()
            updated = True
    
        # Update location
        if location is not None:
            if not isinstance(location, str) or not location.strip():
                return { "success": False, "error": "Invalid location" }
            contact["location"] = location.strip()
            updated = True

        # Update organization_id
        if organization_id is not _UNSET:
            if organization_id is None or organization_id == "":
                # Explicitly disassociate
                contact["organization_id"] = None
            else:
                if organization_id not in self.organizations:
                    return { "success": False, "error": "Organization does not exist" }
                contact["organization_id"] = organization_id
            updated = True

        # If nothing to update, just return success
        if not updated:
            return { "success": True, "message": "No fields updated" }
    
        self.contacts[contact_id] = contact
        return { "success": True, "message": "Contact info updated" }


    def add_communication_method_to_contact(self, contact_id: str, type: str, value: str) -> dict:
        """
        Add a new communication method to an existing contact with value validation for the specified type.

        Args:
            contact_id (str): The ID of the target contact.
            type (str): Type of communication method (e.g., 'email', 'phone').
            value (str): The contact detail for the communication method.

        Returns:
            dict: {
                'success': True,
                'message': 'Communication method added to contact'
            }
            or
            {
                'success': False,
                'error': 'reason for failure'
            }

        Constraints:
            - Contact must exist.
            - Value must be valid for the given type ('email' must be a valid email, 'phone' must be a valid phone).
            - Automatically generate unique method_id.
        """
        # 1. Check contact exists
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist" }

        # 2. Validate value for type
        if type.lower() == 'email':
            if not self._is_valid_email(value):
                return { "success": False, "error": "Invalid email format" }
        elif type.lower() == 'phone':
            if not self._is_valid_phone(value):
                return { "success": False, "error": "Invalid phone format" }
        # Optionally, expand for more types
    
        # 3. Generate unique method_id
        method_id = str(uuid.uuid4())
        while method_id in self.communication_methods:
            method_id = str(uuid.uuid4())

        # 4. Construct the method info
        comm_method = {
            "method_id": method_id,
            "contact_id": contact_id,
            "type": type,
            "value": value
        }

        # 5. Update state
        self.communication_methods[method_id] = comm_method
        # Append to contact's list of method_ids
        self.contacts[contact_id]["communication_method"].append(method_id)

        return { "success": True, "message": "Communication method added to contact" }


    def update_communication_method(
        self,
        method_id: str,
        type: Optional[str] = None,
        value: Optional[str] = None
    ) -> Dict:
        """
        Update the 'type' and/or 'value' of a communication method given its method_id.

        Args:
            method_id (str): The unique identifier of the communication method.
            type (Optional[str]): The new type ('email', 'phone', etc.), if to be changed.
            value (Optional[str]): The new value (email address, phone number, etc.), if to be changed.

        Returns:
            dict: On success:
                { "success": True, "message": "Communication method updated." }
                  On failure:
                { "success": False, "error": "reason" }

        Constraints:
            - method_id must exist.
            - At least one of type or value must be provided.
            - The resulting (type, value) must be valid (e.g., email format, phone format).
        """
        if method_id not in self.communication_methods:
            return { "success": False, "error": "Communication method does not exist." }

        if type is None and value is None:
            return { "success": False, "error": "No update parameters provided (type and value both missing)." }

        method_info = self.communication_methods[method_id].copy()
        new_type = type if type is not None else method_info["type"]
        new_value = value if value is not None else method_info["value"]

        # Validation for communication method types
        def valid_for_type(_type: str, _val: str) -> bool:
            if _type == "email":
                return self._is_valid_email(_val)
            elif _type == "phone":
                # Match the same permissive phone format accepted when adding a method.
                return self._is_valid_phone(_val)
            else:
                # Accept all for unknown types
                return True

        if not valid_for_type(new_type, new_value):
            return { "success": False, "error": f"Value '{new_value}' is not valid for communication type '{new_type}'." }

        # Update
        if type is not None:
            self.communication_methods[method_id]["type"] = type
        if value is not None:
            self.communication_methods[method_id]["value"] = value

        return { "success": True, "message": "Communication method updated." }

    def remove_communication_method(self, method_id: str) -> dict:
        """
        Remove a communication method from a contact, but only if at least one remains.

        Args:
            method_id (str): The identifier for the communication method to remove.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Communication method <method_id> removed from contact <contact_id>." }
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - Each contact must always have at least one communication method on record.
            - The communication method must exist.
        """
        # Step 1: Check if communication method exists
        if method_id not in self.communication_methods:
            return { "success": False, "error": "Communication method does not exist." }

        comm_method_info = self.communication_methods[method_id]
        contact_id = comm_method_info["contact_id"]

        # Step 2: Check if contact exists
        if contact_id not in self.contacts:
            return { "success": False, "error": "Associated contact does not exist." }

        contact_info = self.contacts[contact_id]
        current_methods = contact_info["communication_method"]

        # Step 3: Check if method_id is actually listed for this contact (integrity)
        if method_id not in current_methods:
            return { "success": False, "error": f"Communication method {method_id} is not associated with contact {contact_id}." }

        # Step 4: Enforce constraint (must leave at least one method)
        if len(current_methods) <= 1:
            return { "success": False, "error": "Cannot remove the last communication method from contact." }

        # Step 5: Remove method from contact's list and from communication_methods dict
        contact_info["communication_method"] = [mid for mid in current_methods if mid != method_id]
        self.communication_methods.pop(method_id)

        return {
            "success": True,
            "message": f"Communication method {method_id} removed from contact {contact_id}."
        }

    def affiliate_contact_with_organization(self, contact_id: str, organization_id: str) -> dict:
        """
        Assign or update an organization_id for a specific contact.

        Args:
            contact_id (str): ID of the contact to affiliate.
            organization_id (str): ID of the organization to affiliate with.

        Returns:
            dict: {
               "success": True,
               "message": "Contact {contact_id} affiliated with organization {organization_id}"
            }
            or
            {
               "success": False,
               "error": "reason"
            }

        Constraints:
            - Both contact_id and organization_id must exist.
            - Updates contact's organization_id field.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist" }
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }
    
        self.contacts[contact_id]["organization_id"] = organization_id
        return {
            "success": True,
            "message": f"Contact {contact_id} affiliated with organization {organization_id}"
        }

    def disaffiliate_contact_from_organization(self, contact_id: str) -> dict:
        """
        Remove organization affiliation from the contact specified by contact_id.

        Args:
            contact_id (str): The unique identifier of the contact.

        Returns:
            dict:
                - On success:
                  { "success": True, "message": "Organization affiliation removed from contact." }
                - On error:
                  { "success": False, "error": "Contact not found."}

        Constraints:
            - The contact must exist in the CRM.
            - After this operation, the contact has no organization affiliation.
            - Operation is idempotent if the contact is already unaffiliated.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return {"success": False, "error": "Contact not found."}

        contact["organization_id"] = None
        return {"success": True, "message": "Organization affiliation removed from contact."}


    def add_interaction_for_contact(
        self,
        contact_id: str,
        date: str,
        interaction_type: str,
        note: str
    ) -> dict:
        """
        Record a new interaction (meeting, call, email, etc.) tied to a contact.

        Args:
            contact_id (str): The contact id the interaction is associated with. Contact must exist.
            date (str): When the interaction occurred (string format, e.g., 'YYYY-MM-DD').
            interaction_type (str): Type of the interaction (e.g., 'call', 'meeting').
            note (str): Description or summary of the interaction.

        Returns:
            dict: 
                On success: { "success": True, "message": "Interaction recorded successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The provided contact_id must exist.
            - Required fields must not be empty.
            - The interaction_id will be automatically generated and will be unique.
        """
        # Check if contact exists
        if contact_id not in self.contacts:
            return {"success": False, "error": "Contact does not exist."}
        # Basic required field checks
        if not date or not interaction_type or not note:
            return {"success": False, "error": "Date, interaction type, and note are required."}

        # Generate unique interaction_id
        interaction_id = str(uuid.uuid4())

        interaction_info = {
            "interaction_id": interaction_id,
            "contact_id": contact_id,
            "date": date,
            "type": interaction_type,
            "note": note
        }

        self.interactions[interaction_id] = interaction_info

        return {"success": True, "message": "Interaction recorded successfully."}

    def update_interaction(
        self,
        interaction_id: str,
        contact_id: str = None,
        date: str = None,
        type: str = None,
        note: str = None
    ) -> dict:
        """
        Edit the details of a previously recorded interaction.

        Args:
            interaction_id (str): The unique ID of the interaction to update.
            contact_id (str, optional): New contact_id to associate with, if changing.
            date (str, optional): New date value.
            type (str, optional): New type value.
            note (str, optional): New note value.

        Returns:
            dict: {
                "success": True,
                "message": "Interaction updated successfully"
            }
            or
            {
                "success": False,
                "error": <str: reason>
            }

        Constraints:
            - interaction_id must exist.
            - If contact_id is updated, the new contact_id must exist in the system.
            - At least one update field should be provided (optional: ignore if all None).
        """
        if interaction_id not in self.interactions:
            return {"success": False, "error": "Interaction does not exist"}

        interaction = self.interactions[interaction_id]
        updated = False

        if contact_id is not None:
            if contact_id not in self.contacts:
                return {"success": False, "error": "Provided contact_id does not exist"}
            interaction["contact_id"] = contact_id
            updated = True

        if date is not None:
            interaction["date"] = date
            updated = True

        if type is not None:
            interaction["type"] = type
            updated = True

        if note is not None:
            interaction["note"] = note
            updated = True

        if not updated:
            return {"success": True, "message": "No updates applied; nothing changed"}

        self.interactions[interaction_id] = interaction  # Save is technically redundant for dict
        return {"success": True, "message": "Interaction updated successfully"}

    def delete_contact(self, contact_id: str) -> dict:
        """
        Permanently remove a contact and all associated communication methods and interactions,
        but only if the contact_id exists. Cleans up references in other tables as necessary.

        Args:
            contact_id (str): The unique identifier of the contact to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Contact and associated data deleted." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Contact must exist.
            - Upon deletion, all associated communication methods and interactions are also deleted.
            - No constraint is violated since non-existent contacts do not factor into the rule about each contact having at least one communication method.
        """

        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist." }

        # Delete all associated communication methods
        method_ids_to_delete = [
            method_id for method_id, method in self.communication_methods.items()
            if method["contact_id"] == contact_id
        ]
        for method_id in method_ids_to_delete:
            del self.communication_methods[method_id]

        # Delete all associated interactions
        interaction_ids_to_delete = [
            interaction_id for interaction_id, interaction in self.interactions.items()
            if interaction["contact_id"] == contact_id
        ]
        for interaction_id in interaction_ids_to_delete:
            del self.interactions[interaction_id]

        # Remove the contact itself
        del self.contacts[contact_id]

        return { "success": True, "message": "Contact and all related data deleted." }

    def delete_interaction(self, interaction_id: str) -> dict:
        """
        Remove an interaction history entry for a contact.

        Args:
            interaction_id (str): The unique identifier of the interaction to be deleted.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Interaction deleted successfully." }
                - On failure: { "success": False, "error": "Interaction not found." }

        Constraints:
            - The interaction with the specified interaction_id must exist in the system.
            - Deleting an interaction does not affect other entities or violate system constraints.
        """
        if interaction_id not in self.interactions:
            return { "success": False, "error": "Interaction not found." }
        del self.interactions[interaction_id]
        return { "success": True, "message": "Interaction deleted successfully." }


class CrmSystem(BaseEnv):
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

    def search_contacts_by_name(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_name', kwargs)

    def search_contacts_by_location(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_location', kwargs)

    def search_contacts_by_name_and_location(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_name_and_location', kwargs)

    def get_contact_by_id(self, **kwargs):
        return self._call_inner_tool('get_contact_by_id', kwargs)

    def get_communication_methods_for_contact(self, **kwargs):
        return self._call_inner_tool('get_communication_methods_for_contact', kwargs)

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def get_contact_organization(self, **kwargs):
        return self._call_inner_tool('get_contact_organization', kwargs)

    def get_interactions_for_contact(self, **kwargs):
        return self._call_inner_tool('get_interactions_for_contact', kwargs)

    def communication_method_validity_check(self, **kwargs):
        return self._call_inner_tool('communication_method_validity_check', kwargs)

    def list_all_contacts(self, **kwargs):
        return self._call_inner_tool('list_all_contacts', kwargs)

    def get_contacts_in_organization(self, **kwargs):
        return self._call_inner_tool('get_contacts_in_organization', kwargs)

    def add_new_contact(self, **kwargs):
        return self._call_inner_tool('add_new_contact', kwargs)

    def update_contact_info(self, **kwargs):
        return self._call_inner_tool('update_contact_info', kwargs)

    def add_communication_method_to_contact(self, **kwargs):
        return self._call_inner_tool('add_communication_method_to_contact', kwargs)

    def update_communication_method(self, **kwargs):
        return self._call_inner_tool('update_communication_method', kwargs)

    def remove_communication_method(self, **kwargs):
        return self._call_inner_tool('remove_communication_method', kwargs)

    def affiliate_contact_with_organization(self, **kwargs):
        return self._call_inner_tool('affiliate_contact_with_organization', kwargs)

    def disaffiliate_contact_from_organization(self, **kwargs):
        return self._call_inner_tool('disaffiliate_contact_from_organization', kwargs)

    def add_interaction_for_contact(self, **kwargs):
        return self._call_inner_tool('add_interaction_for_contact', kwargs)

    def update_interaction(self, **kwargs):
        return self._call_inner_tool('update_interaction', kwargs)

    def delete_contact(self, **kwargs):
        return self._call_inner_tool('delete_contact', kwargs)

    def delete_interaction(self, **kwargs):
        return self._call_inner_tool('delete_interaction', kwargs)
