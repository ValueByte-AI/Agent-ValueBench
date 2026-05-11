# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import csv
import io



class UserInfo(TypedDict):
    _id: str
    full_name: str
    email_address: str
    job_title: str
    department: str
    phone_number: str
    sta: str  # Status

class ContactInfo(TypedDict):
    contact_id: str
    full_name: str
    email_address: str
    organization: str
    phone_number: str
    typ: str  # Type

class GroupInfo(TypedDict):
    group_id: str
    group_name: str
    members: List[str]  # List of _id (users) or contact_id (contacts)
    description: str

class AccessControlInfo(TypedDict):
    principal_id: str
    role: str
    permission: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for an enterprise email directory service.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}

        # Groups: {group_id: GroupInfo}
        self.groups: Dict[str, GroupInfo] = {}

        # Access controls: {principal_id: AccessControlInfo}
        self.access_controls: Dict[str, AccessControlInfo] = {}

        # Constraints:
        # - Only authorized users (with correct permissions) can export directory/contact data.
        # - Group membership must reference existing users or contacts.
        # - Each email address in the directory must be unique.

    @staticmethod
    def _parse_permissions(permission_value: str) -> List[str]:
        if not isinstance(permission_value, str):
            return []
        return [p.strip().lower() for p in permission_value.replace(",", " ").split() if p.strip()]

    @staticmethod
    def _match_filter_value(actual, expected) -> bool:
        if isinstance(expected, dict):
            if "$in" in expected and isinstance(expected["$in"], (list, tuple, set)):
                return actual in expected["$in"]
            return actual == expected
        if isinstance(expected, (list, tuple, set)):
            return actual in expected
        return actual == expected

    def _get_access_control_entry(self, principal_id: str):
        entry = self.access_controls.get(principal_id)
        if entry is not None:
            return entry
        for value in self.access_controls.values():
            if isinstance(value, dict) and value.get("principal_id") == principal_id:
                return value
        return None

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details by user ID.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict: {
                'success': True,
                'data': UserInfo
            }
            or
            {
                'success': False,
                'error': 'User not found'
            }

        Constraints:
            - The user must exist in the directory (self.users).
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": self.users[user_id] }

    def get_user_by_email(self, email_address: str) -> dict:
        """
        Retrieve user details by email address.

        Args:
            email_address (str): The user's email address to look up.

        Returns:
            dict:
                {
                    "success": True,
                    "data": UserInfo  # User information if found
                }
                or
                {
                    "success": False,
                    "error": str  # Reason (e.g., 'User not found')
                }

        Constraints:
            - Email addresses are unique across the directory.
        """
        for user in self.users.values():
            if user["email_address"] == email_address:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def list_all_users(self) -> dict:
        """
        List all users present in the email directory.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List may be empty if no users are present.
            }
            or
            {
                "success": False,
                "error": str  # Description of error, though not expected in normal cases.
            }
        Constraints:
            - No input required.
            - No access control enforced for querying all users.
        """
        try:
            user_list = list(self.users.values())
            return {"success": True, "data": user_list}
        except Exception as e:
            return {"success": False, "error": f"Failed to list users: {str(e)}"}

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Retrieve contact details by contact ID.

        Args:
            contact_id (str): The unique ID of the contact.

        Returns:
            dict: {
                "success": True,
                "data": ContactInfo  # The contact's info if found.
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g., not found)
            }

        Constraints:
            - No permissions required for this operation.
            - Returns error if contact_id does not exist.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return {"success": False, "error": "Contact not found"}
        return {"success": True, "data": contact}

    def get_contact_by_email(self, email_address: str) -> dict:
        """
        Retrieve contact details using the provided email address.

        Args:
            email_address (str): The email address of the contact to look up.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ContactInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Contact with this email address does not exist."
                    }
        Constraints:
            - Only contacts are checked (not users).
            - Email address must be unique, so at most one result.
        """
        for contact in self.contacts.values():
            if contact['email_address'] == email_address:
                return {"success": True, "data": contact}
        return {"success": False, "error": "Contact with this email address does not exist."}

    def list_all_contacts(self) -> dict:
        """
        List all contacts (user and external) in the directory.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List of all contacts (may be empty)
            }
        """
        contact_list = list(self.contacts.values())
        return { "success": True, "data": contact_list }

    def get_group_by_id(self, group_id: str) -> dict:
        """
        Retrieve group details and membership by group ID.

        Args:
            group_id (str): The ID of the group to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": GroupInfo,  # Group information and membership
            }
            or
            {
                "success": False,
                "error": str  # Description of error if group not found
            }

        Constraints:
            - The group_id must exist in the directory service.
        """
        if group_id not in self.groups:
            return { "success": False, "error": "Group not found" }

        group_info = self.groups[group_id]
        return { "success": True, "data": group_info }

    def list_all_groups(self) -> dict:
        """
        List all groups in the directory.

        Returns:
            dict: {
                "success": True,
                "data": List[GroupInfo]  # List of all group information (may be empty).
            }
        """
        groups_list = list(self.groups.values())
        return {
            "success": True,
            "data": groups_list
        }

    def get_group_members(self, group_id: str) -> dict:
        """
        Given a group ID, list all member IDs (users/contacts).

        Args:
            group_id (str): The ID of the group.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of member IDs (users' _id or contacts' contact_id, as recorded)
            }
            or
            {
                "success": False,
                "error": str  # If group_id not found
            }

        Constraints:
            - The specified group must exist.
        """
        group = self.groups.get(group_id)
        if group is None:
            return { "success": False, "error": "Group not found" }
        members = group.get('members', [])
        return { "success": True, "data": list(members) }

    def check_email_uniqueness(self, email_address: str) -> dict:
        """
        Checks if the given email address is unique across both users and contacts.

        Args:
            email_address (str): The email address to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "is_unique": bool  # True if email address does not exist anywhere; False otherwise.
                }
            }
            or
            {
                "success": False,
                "error": str  # description of the error
            }

        Constraints:
            - An email address is considered unique if it does not appear in any user or contact.
            - Empty or non-string email addresses are invalid input.
        """
        if not isinstance(email_address, str) or not email_address.strip():
            return {"success": False, "error": "Invalid email address parameter."}

        email_lower = email_address.strip().lower()
        user_emails = (user["email_address"].lower() for user in self.users.values())
        contact_emails = (contact["email_address"].lower() for contact in self.contacts.values())

        is_unique = email_lower not in user_emails and email_lower not in contact_emails

        return {"success": True, "data": {"is_unique": is_unique}}

    def get_access_control(self, principal_id: str) -> dict:
        """
        Retrieve the access control entry for the specified principal_id.

        Args:
            principal_id (str): The unique identifier for the principal.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AccessControlInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Access control entry not found"
                    }
        Constraints:
            - If the principal_id is not found, return an appropriate error.
        """
        ac_entry = self._get_access_control_entry(principal_id)
        if ac_entry is None:
            return {
                "success": False,
                "error": "Access control entry not found"
            }
        return {
            "success": True,
            "data": ac_entry
        }

    def check_permission_for_export(self, principal_id: str) -> dict:
        """
        Check if the specified principal/user has permission to export directory/contact data.

        Args:
            principal_id (str): The identifier of the principal/user to check.

        Returns:
            dict: On success,
                    {"success": True, "has_permission": bool}
                  On error (principal_id not in access_controls),
                    {"success": False, "error": str}

        Constraints:
            - Only authorized users (with correct permissions) can export directory/contact data.
        """
        access = self._get_access_control_entry(principal_id)
        if not access:
            return {"success": False, "error": "Principal ID not found in access control list"}

        # Consider permission string contains "export" (could be "export", "admin,export", etc.)
        permissions = self._parse_permissions(access.get("permission", ""))
        has_permission = any(p in {"export", "export_contacts"} for p in permissions)

        return {"success": True, "has_permission": has_permission}

    def export_contacts_to_csv(self, caller_id: str, filter_criteria: dict = None) -> dict:
        """
        Export all contacts, or a subset filtered by criteria, to CSV format if caller has the right permission.

        Args:
            caller_id (str): The principal_id invoking the export (for permission check).
            filter_criteria (dict, optional): Filtering conditions for contacts (e.g., keys: 'typ', 'organization', etc.).

        Returns:
            dict: {
                "success": True,
                "csv": str   # CSV-formatted string for the selected contacts (header always included)
            }
            OR
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Only authorized users (with correct 'export_contacts' permission) may perform this operation.
        """
        # Check permissions
        ac = self._get_access_control_entry(caller_id)
        if not ac:
            return { "success": False, "error": "Caller does not exist in access control system" }
        permissions = self._parse_permissions(ac.get("permission", ""))
        if not any(p in {"export", "export_contacts"} for p in permissions):
            return { "success": False, "error": "Permission denied for export_contacts operation" }
    
        # Determine which contacts to export
        contacts = list(self.contacts.values())
        if filter_criteria:
            def match(contact):
                for k, v in filter_criteria.items():
                    if k not in contact or not self._match_filter_value(contact[k], v):
                        return False
                return True
            contacts = [c for c in contacts if match(c)]

        # Prepare CSV header based on ContactInfo fields
        if contacts:
            header_fields = list(contacts[0].keys())
        else:
            # Default/known header fields in case of no contact
            header_fields = ["contact_id", "full_name", "email_address", "organization", "phone_number", "typ"]

        # Build CSV rows
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header_fields)
        writer.writeheader()
        for contact in contacts:
            writer.writerow({k: contact.get(k, "") for k in header_fields})
    
        csv_str = output.getvalue()
        output.close()
        return { "success": True, "csv": csv_str }

    def add_user(self, _id: str, full_name: str, email_address: str,
                 job_title: str, department: str, phone_number: str,
                 sta: str) -> dict:
        """
        Add a new user to the directory (enforces unique ID and unique email address).

        Args:
            _id (str): Unique user ID.
            full_name (str): The user's full name.
            email_address (str): Must be unique across users & contacts.
            job_title (str): User's job title.
            department (str): User's department.
            phone_number (str): User's phone number.
            sta (str): Status.

        Returns:
            dict: {
                "success": True,
                "message": "User added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of constraint violation
            }

        Constraints:
            - _id must be unique among users.
            - email_address must be unique across users and contacts.
        """
        if _id in self.users:
            return { "success": False, "error": "User ID already exists" }

        # Check email uniqueness in users
        for user in self.users.values():
            if user['email_address'].lower() == email_address.lower():
                return { "success": False, "error": "Email address already exists in users" }
        # Check email uniqueness in contacts
        for contact in self.contacts.values():
            if contact['email_address'].lower() == email_address.lower():
                return { "success": False, "error": "Email address already exists in contacts" }

        self.users[_id] = {
            "_id": _id,
            "full_name": full_name,
            "email_address": email_address,
            "job_title": job_title,
            "department": department,
            "phone_number": phone_number,
            "sta": sta
        }
        return { "success": True, "message": "User added successfully" }

    def update_user_info(self, user_id: str, updates: dict) -> dict:
        """
        Update the information for a specific user identified by user_id.
    
        Args:
            user_id (str): The _id of the user to update.
            updates (dict): Dictionary of fields to update. Possible keys includ:
                'full_name', 'email_address', 'job_title', 'department', 'phone_number', 'sta'.

        Returns:
            dict: 
              Success: { "success": True, "message": "User info updated successfully." }
              Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - User must exist.
            - If updating email_address, the new value must be unique across all users and contacts.
            - Only valid attributes may be updated.
            - Cannot update '_id'.
        """
        # Ensure user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }
    
        user = self.users[user_id]
        allowed_fields = {"full_name", "email_address", "job_title", "department", "phone_number", "sta"}
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
    
        if not update_fields:
            return { "success": False, "error": "No valid user attribute to update." }
    
        # If updating email_address, must check for uniqueness
        if "email_address" in update_fields:
            new_email = update_fields["email_address"]
            # Check users for duplicate (excluding the current user)
            for uid, u in self.users.items():
                if uid != user_id and u["email_address"].lower() == new_email.lower():
                    return { "success": False, "error": "Email address already in use." }
            # Check contacts for duplicate
            for c in self.contacts.values():
                if c["email_address"].lower() == new_email.lower():
                    return { "success": False, "error": "Email address already in use." }

        # Apply updates
        for k, v in update_fields.items():
            user[k] = v

        return { "success": True, "message": "User info updated successfully." }

    def delete_user(self, _id: str) -> dict:
        """
        Remove a user from the directory.
    
        Args:
            _id (str): The unique user ID to remove.

        Returns:
            dict: 
                On success: { "success": True, "message": "User <_id> deleted" }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - The user must exist.
            - Remove the user from all group memberships to maintain referential integrity.
        """

        if _id not in self.users:
            return { "success": False, "error": f"User '{_id}' does not exist" }

        # Remove user from all group memberships
        for group in self.groups.values():
            if _id in group["members"]:
                group["members"] = [m for m in group["members"] if m != _id]

        # Delete the user object
        del self.users[_id]

        return { "success": True, "message": f"User '{_id}' deleted" }

    def add_contact(
        self,
        contact_id: str,
        full_name: str,
        email_address: str,
        organization: str,
        phone_number: str,
        typ: str
    ) -> dict:
        """
        Add a new contact to the directory.

        Args:
            contact_id (str): Unique identifier for the contact.
            full_name (str): Full name of the contact.
            email_address (str): Email address (must be unique across users and contacts).
            organization (str): Organization of the contact.
            phone_number (str): Contact phone number.
            typ (str): Type of contact (e.g., external, internal, etc.).

        Returns:
            dict: 
                { "success": True, "message": "Contact added successfully." }
                or
                { "success": False, "error": <reason> }
    
        Constraints:
            - Email address must be unique across users and contacts.
            - contact_id must be unique among contacts.
        """
        # Validate required fields
        if not all([contact_id, full_name, email_address, organization, phone_number, typ]):
            return { "success": False, "error": "Missing required contact attributes" }

        # Check email uniqueness
        for user in self.users.values():
            if user["email_address"].lower() == email_address.lower():
                return { "success": False, "error": "Email address already exists in the directory." }
        for contact in self.contacts.values():
            if contact["email_address"].lower() == email_address.lower():
                return { "success": False, "error": "Email address already exists in the directory." }

        # Check contact_id uniqueness
        if contact_id in self.contacts:
            return { "success": False, "error": "Contact ID already exists." }

        # Add the contact
        contact_info: ContactInfo = {
            "contact_id": contact_id,
            "full_name": full_name,
            "email_address": email_address,
            "organization": organization,
            "phone_number": phone_number,
            "typ": typ
        }
        self.contacts[contact_id] = contact_info

        return { "success": True, "message": "Contact added successfully." }

    def update_contact_info(self, contact_id: str, updates: dict) -> dict:
        """
        Update attributes for a specific contact.

        Args:
            contact_id (str): Contact to update.
            updates (dict): Keys are ContactInfo fields to update (excluding contact_id).

        Returns:
            dict: {
                "success": True,
                "message": "Contact updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - contact_id must exist.
            - If 'email_address' is updated, the new address must be unique across all users and contacts.
            - contact_id itself cannot be changed.
        """
        if contact_id not in self.contacts:
            return {"success": False, "error": "Contact not found"}

        contact = self.contacts[contact_id]

        # If updating email_address, ensure uniqueness across users and contacts
        if "email_address" in updates:
            new_email = updates["email_address"]
            if new_email != contact["email_address"]:
                # search contacts (excluding current)
                for cid, c in self.contacts.items():
                    if cid != contact_id and c["email_address"].lower() == new_email.lower():
                        return {"success": False, "error": "Email address already in use by another contact"}
                # search users
                for u in self.users.values():
                    if u["email_address"].lower() == new_email.lower():
                        return {"success": False, "error": "Email address already in use by a user"}

        # Disallow changing contact_id
        if "contact_id" in updates and updates["contact_id"] != contact_id:
            return {"success": False, "error": "Cannot change contact_id"}

        # Update the fields
        for k, v in updates.items():
            if k == "contact_id":
                continue  # skip; don't mutate the key
            if k in contact:
                contact[k] = v

        self.contacts[contact_id] = contact

        return {"success": True, "message": "Contact updated successfully"}

    def delete_contact(self, contact_id: str) -> dict:
        """
        Remove a contact from the directory and from any group membership.

        Args:
            contact_id (str): The ID of the contact to remove.

        Returns:
            dict: 
              On success: { "success": True, "message": "Contact <contact_id> deleted" }
              On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Removes contact from directory and any group memberships referencing the contact.
            - If contact does not exist, operation fails.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found" }
    
        # Remove the contact itself
        del self.contacts[contact_id]

        # Remove the contact from all group memberships
        for group in self.groups.values():
            if contact_id in group["members"]:
                group["members"] = [m for m in group["members"] if m != contact_id]

        return { "success": True, "message": f"Contact {contact_id} deleted" }

    def create_group(
        self,
        group_id: str,
        group_name: str,
        members: list,
        description: str
    ) -> dict:
        """
        Create a new group with the specified members.

        Args:
            group_id (str): Unique identifier for the group.
            group_name (str): Group's display name.
            members (list of str): List of user _id and/or contact_id to include as members.
            description (str): Group description.

        Returns:
            dict: {
                "success": True,
                "message": f"Group '{group_name}' created with id '{group_id}'."
            }
            or
            {
                "success": False,
                "error": str (reason for failure)
            }

        Constraints:
            - group_id must be unique.
            - All member IDs must reference existing users or contacts.
        """
        if group_id in self.groups:
            return {
                "success": False,
                "error": f"Group ID '{group_id}' already exists."
            }

        invalid_members = [
            m for m in members if m not in self.users and m not in self.contacts
        ]
        if invalid_members:
            return {
                "success": False,
                "error": f"Invalid member IDs: {invalid_members}"
            }

        self.groups[group_id] = {
            "group_id": group_id,
            "group_name": group_name,
            "members": members.copy(),
            "description": description
        }

        return {
            "success": True,
            "message": f"Group '{group_name}' created with id '{group_id}'."
        }

    def update_group_info(
        self, 
        group_id: str, 
        group_name: str = None, 
        description: str = None, 
        members: list = None
    ) -> dict:
        """
        Update a group's name, description, and/or members.

        Args:
            group_id (str): The group identifier to update.
            group_name (str, optional): New group name.
            description (str, optional): New group description.
            members (list, optional): Entire new list of member ids (users' _id or contacts' contact_id).

        Returns:
            dict: 
                { "success": True, "message": "Group info updated." }
                or
                { "success": False, "error": error_description }

        Constraints:
            - group_id must exist.
            - If members is provided, every member must exist in users or contacts.
        """
        group = self.groups.get(group_id)
        if not group:
            return { "success": False, "error": "Group does not exist." }

        changed = False

        if group_name is not None:
            group["group_name"] = group_name
            changed = True
        if description is not None:
            group["description"] = description
            changed = True
        if members is not None:
            # Validate all member ids
            invalid_ids = []
            for mid in members:
                if (mid not in self.users) and (mid not in self.contacts):
                    invalid_ids.append(mid)
            if invalid_ids:
                return {
                    "success": False,
                    "error": f"These member IDs do not exist: {', '.join(invalid_ids)}"
                }
            group["members"] = members
            changed = True

        if not changed:
            return { "success": True, "message": "No changes were provided." }

        self.groups[group_id] = group  # Explicit assignment to indicate update
        return { "success": True, "message": "Group info updated." }

    def add_group_members(self, group_id: str, member_ids: list) -> dict:
        """
        Add members (users or contacts) to the specified group.

        Args:
            group_id (str): The unique identifier of the target group.
            member_ids (List[str]): List of user _id or contact_id strings to add to the group.

        Returns:
            dict:
                - On success: {"success": True, "message": "Added X new member(s) to group <group_id>"}
                - On error: {"success": False, "error": "..."}
    
        Constraints:
            - Each member ID must exist as a user (_id) or contact (contact_id).
            - Will not add duplicate entries to a group.
            - Group must exist.
        """
        if group_id not in self.groups:
            return {"success": False, "error": "Group not found"}

        if not isinstance(member_ids, list):
            return {"success": False, "error": "member_ids should be a list"}

        group = self.groups[group_id]
        existing_members = set(group["members"])

        # Partition member_ids by validity
        invalid_ids = []
        valid_new_members = []

        for mid in member_ids:
            # Check if ID exists and is not already a member
            if (mid in self.users or mid in self.contacts):
                if mid not in existing_members:
                    valid_new_members.append(mid)
            else:
                invalid_ids.append(mid)

        if invalid_ids:
            return {
                "success": False,
                "error": f"Some member IDs are invalid: {invalid_ids}"
            }

        # Add valid new members to the group
        if valid_new_members:
            group["members"].extend(valid_new_members)

        return {
            "success": True,
            "message": f"Added {len(valid_new_members)} new member(s) to group {group_id}"
        }

    def remove_group_member(self, group_id: str, member_id: str) -> dict:
        """
        Remove a member (user _id or contact_id) from the specified group.

        Args:
            group_id (str): The unique identifier of the group.
            member_id (str): The unique identifier (user _id or contact_id) of the member to remove.

        Returns:
            dict:
              - On success:
                {
                    "success": True,
                    "message": "Member removed from group."
                }
              - On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - The specified group must exist.
            - The member must be present in the group for it to be removed.
        """
        group = self.groups.get(group_id)
        if group is None:
            return {
                "success": False,
                "error": "Group does not exist."
            }
        if member_id not in group["members"]:
            return {
                "success": False,
                "error": "Member not in group."
            }

        group["members"].remove(member_id)
        return {
            "success": True,
            "message": "Member removed from group."
        }

    def set_access_control(self, principal_id: str, role: str, permission: str) -> dict:
        """
        Set or modify the access control entry for a user/principal.

        Args:
            principal_id (str): The identifier of the principal (user or contact).
            role (str): The role to assign (e.g., 'admin', 'user', etc.).
            permission (str): Permission string or code to assign (e.g., 'read', 'write', etc.)

        Returns:
            dict: {
                "success": True,
                "message": "Access control entry set for principal_id <principal_id>."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - If principal_id is not a valid user or contact, behavior is permissive as per specification.
        """
        self.access_controls[principal_id] = {
            "principal_id": principal_id,
            "role": role,
            "permission": permission
        }
        return {
            "success": True,
            "message": f"Access control entry set for principal_id {principal_id}."
        }

    def revoke_access_control(self, principal_id: str) -> dict:
        """
        Remove (revoke) access control entry for a user/principal.

        Args:
            principal_id (str): The unique identifier for the user/principal whose access control is to be revoked.

        Returns:
            dict: {
                "success": True,
                "message": "Access control revoked for principal <principal_id>"
            }
            or
            {
                "success": False,
                "error": "Principal <principal_id> does not have access control to revoke."
            }
        Constraints:
            - Only principals with existing access control entries can be revoked.
        """
        if principal_id not in self.access_controls:
            return {
                "success": False,
                "error": f"Principal {principal_id} does not have access control to revoke."
            }

        del self.access_controls[principal_id]

        return {
            "success": True,
            "message": f"Access control revoked for principal {principal_id}"
        }


class EnterpriseEmailDirectoryService(BaseEnv):
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
        init_config = copy.deepcopy(init_config)
        for state_key, id_field in (
            ("users", "_id"),
            ("contacts", "contact_id"),
            ("groups", "group_id"),
            ("access_controls", "principal_id"),
        ):
            records = init_config.get(state_key)
            if isinstance(records, dict):
                init_config[state_key] = {
                    (record.get(id_field) if isinstance(record, dict) and record.get(id_field) else key): record
                    for key, record in records.items()
                }
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_contact_by_id(self, **kwargs):
        return self._call_inner_tool('get_contact_by_id', kwargs)

    def get_contact_by_email(self, **kwargs):
        return self._call_inner_tool('get_contact_by_email', kwargs)

    def list_all_contacts(self, **kwargs):
        return self._call_inner_tool('list_all_contacts', kwargs)

    def get_group_by_id(self, **kwargs):
        return self._call_inner_tool('get_group_by_id', kwargs)

    def list_all_groups(self, **kwargs):
        return self._call_inner_tool('list_all_groups', kwargs)

    def get_group_members(self, **kwargs):
        return self._call_inner_tool('get_group_members', kwargs)

    def check_email_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_email_uniqueness', kwargs)

    def get_access_control(self, **kwargs):
        return self._call_inner_tool('get_access_control', kwargs)

    def check_permission_for_export(self, **kwargs):
        return self._call_inner_tool('check_permission_for_export', kwargs)

    def export_contacts_to_csv(self, **kwargs):
        return self._call_inner_tool('export_contacts_to_csv', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def update_contact_info(self, **kwargs):
        return self._call_inner_tool('update_contact_info', kwargs)

    def delete_contact(self, **kwargs):
        return self._call_inner_tool('delete_contact', kwargs)

    def create_group(self, **kwargs):
        return self._call_inner_tool('create_group', kwargs)

    def update_group_info(self, **kwargs):
        return self._call_inner_tool('update_group_info', kwargs)

    def add_group_members(self, **kwargs):
        return self._call_inner_tool('add_group_members', kwargs)

    def remove_group_member(self, **kwargs):
        return self._call_inner_tool('remove_group_member', kwargs)

    def set_access_control(self, **kwargs):
        return self._call_inner_tool('set_access_control', kwargs)

    def revoke_access_control(self, **kwargs):
        return self._call_inner_tool('revoke_access_control', kwargs)
