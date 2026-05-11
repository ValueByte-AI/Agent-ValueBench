# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from typing import Optional, Dict, Any



class OrganizationInfo(TypedDict):
    organization_id: str
    name: str
    number_of_seats: int
    status: str  # e.g., "active", "inactive", "suspended"
    admin_user_id: str

class APIInfo(TypedDict):
    api_id: str
    name: str
    category: str
    status: str  # e.g., "active", "inactive", "suspended"
    owner_organization_id: str
    metadata: Dict[str, Any]  # Arbitrary metadata per API

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str
    organization_id: str  # Assumes single org per user for now; if many, can be List[str]
    role: str  # e.g., "admin", "member", etc.
    status: str  # e.g., "active", "inactive", etc.

class IntegrationInfo(TypedDict):
    integration_id: str
    type: str
    configuration: Dict[str, Any]
    linked_api_ids: List[str]
    organization_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a SaaS platform administrator dashboard.
        """
        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}

        # APIs: {api_id: APIInfo}
        self.apis: Dict[str, APIInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Integrations: {integration_id: IntegrationInfo}
        self.integrations: Dict[str, IntegrationInfo] = {}

        # Constraints/reminders:
        # - api_id must be unique, and each API associated with exactly one owner_organization_id.
        # - number_of_seats for each organization cannot be negative.
        # - Only users with appropriate roles (e.g., admin) can access/modify sensitive organization or API data.
        # - Status fields must be chosen from defined values ("active", "inactive", "suspended", etc.).
        # - Each user belongs to one (or more, if allowed) organizations and may have different roles/permissions.

    def get_api_by_id(self, api_id: str) -> dict:
        """
        Retrieve the full information dictionary of an API given its api_id.

        Args:
            api_id (str): Unique identifier for the API.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": APIInfo
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "API not found"
                    }

        Constraints:
            - The api_id must exist in the system.
        """
        api_info = self.apis.get(api_id)
        if api_info is None:
            return {"success": False, "error": "API not found"}
        return {"success": True, "data": api_info}

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve full information about an organization given its organization_id.

        Args:
            organization_id (str): The unique ID of the organization.

        Returns:
            dict: {
                "success": True,
                "data": OrganizationInfo  # Full info for the organization
            }
            OR
            {
                "success": False,
                "error": str  # Reason (e.g. "Organization not found")
            }
        Constraints:
            - organization_id must exist in the system.
            - Returns fields: name, number_of_seats, status, admin_user_id (+ organization_id).
        """
        org = self.organizations.get(organization_id)
        if org is None:
            return {"success": False, "error": "Organization not found"}
        return {"success": True, "data": org}

    def list_apis_by_organization(self, organization_id: str) -> dict:
        """
        List all APIs owned by a specific organization.

        Args:
            organization_id (str): The unique identifier of the target organization.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[APIInfo] }
                    # List may be empty if the organization owns no APIs.
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Organization must exist.
            - Only APIs with owner_organization_id == organization_id are returned.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        result = [
            api_info for api_info in self.apis.values()
            if api_info["owner_organization_id"] == organization_id
        ]
        return { "success": True, "data": result }

    def get_api_metadata(self, api_id: str) -> dict:
        """
        Retrieve the metadata dictionary for the specified API.

        Args:
            api_id (str): The unique identifier of the API.

        Returns:
            dict: 
                - On success: {"success": True, "data": metadata dict for the API}
                - On failure: {"success": False, "error": "API not found"}

        Constraints:
            - The api_id must exist in the system.
        """
        api = self.apis.get(api_id)
        if not api:
            return {"success": False, "error": "API not found"}
        return {"success": True, "data": api["metadata"]}

    def get_organization_admin(self, organization_id: str) -> dict:
        """
        Retrieve the admin user's details for a given organization.

        Args:
            organization_id (str): The identifier of the organization.

        Returns:
            dict:
                - On success: { "success": True, "data": <UserInfo dict> }
                - On failure: { "success": False, "error": <reason str> }

        Constraints:
            - The organization with given ID must exist.
            - The organization's admin_user_id must refer to an actual user.
            - The user must have role="admin" and belong to the organization.
        """
        org = self.organizations.get(organization_id)
        if not org:
            return { "success": False, "error": "Organization does not exist" }
    
        admin_user_id = org.get("admin_user_id")
        if not admin_user_id:
            return { "success": False, "error": "Organization has no admin_user_id set" }

        admin_user = self.users.get(admin_user_id)
        if not admin_user:
            return { "success": False, "error": "Admin user does not exist" }
    
        # Consistency checks
        if admin_user.get("role") != "admin":
            return { "success": False, "error": "User is not an admin" }
        if admin_user.get("organization_id") != organization_id:
            return { "success": False, "error": "Admin user does not belong to this organization" }
    
        return { "success": True, "data": admin_user }

    def list_all_organizations(self) -> dict:
        """
        Lists all organizations registered in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo]  # All organization info objects (may be empty)
            }
        """
        org_list = list(self.organizations.values())
        return {"success": True, "data": org_list}

    def list_all_apis(self) -> dict:
        """
        List all API records currently registered in the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[APIInfo],  # List of all APIs' information (could be empty)
            }

        Constraints:
            - No input parameters are needed.
            - Returns all APIs present. No filtering or access control applied.
        """
        all_apis = list(self.apis.values())
        return { "success": True, "data": all_apis }

    def list_organization_users(self, organization_id: str) -> dict:
        """
        List all users belonging to a specific organization.

        Args:
            organization_id (str): The ID of the organization whose users to list.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[UserInfo]  # List of users in the organization (may be empty).
                }
                On error: {
                    "success": False,
                    "error": str  # Description of the error, e.g. organization does not exist.
                }

        Constraints:
            - The organization_id must exist.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        users_in_org = [
            user_info for user_info in self.users.values()
            if user_info["organization_id"] == organization_id
        ]
        return {"success": True, "data": users_in_org}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve information for a user given their user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - user_id must exist within the system's user records.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def list_integration_by_organization(self, organization_id: str) -> dict:
        """
        List all integrations associated with the given organization.

        Args:
            organization_id (str): Unique identifier of the organization.

        Returns:
            dict: 
                If organization exists:
                    { "success": True, "data": List[IntegrationInfo] }
                If organization does not exist:
                    { "success": False, "error": "Organization does not exist" }

        Constraints:
            - The given organization_id must be present in self.organizations.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }
    
        integrations = [
            integration for integration in self.integrations.values()
            if integration["organization_id"] == organization_id
        ]
        return { "success": True, "data": integrations }

    def get_integration_by_id(self, integration_id: str) -> dict:
        """
        Retrieve the detailed information for a specific integration by its integration_id.

        Args:
            integration_id (str): The unique identifier of the integration to retrieve.

        Returns:
            dict:
                - If found:
                    {
                        "success": True,
                        "data": IntegrationInfo
                    }
                - If not found:
                    {
                        "success": False,
                        "error": "Integration not found"
                    }
        """
        integration = self.integrations.get(integration_id)
        if integration is None:
            return {"success": False, "error": "Integration not found"}
        return {"success": True, "data": integration}

    def list_apis_by_status(self, status: str) -> dict:
        """
        List all APIs matching a specific status.

        Args:
            status (str): The status to filter APIs by. Must be one of:
                          "active", "inactive", "suspended".

        Returns:
            dict: On success, {
                      "success": True,
                      "data": List[APIInfo]  # List of API dicts with matching status
                  }
                  On error (invalid status), {
                      "success": False,
                      "error": "Invalid status value"
                  }

        Constraints:
            - Only APIs with status in the allowed set will be listed.
            - Allowed status values: "active", "inactive", "suspended".
        """
        allowed_statuses = {"active", "inactive", "suspended"}
        if status not in allowed_statuses:
            return {"success": False, "error": "Invalid status value"}

        result = [api for api in self.apis.values() if api["status"] == status]

        return {"success": True, "data": result}

    def list_organizations_by_status(self, status: str) -> dict:
        """
        List all organizations with the specified status.

        Args:
            status (str): The status to filter organizations by ("active", "inactive", "suspended" etc.)

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo]
            }
            or
            {
                "success": False,
                "error": str  # If the status is invalid
            }

        Constraints:
            - Status must be one of the allowed values: "active", "inactive", "suspended".
        """

        allowed_statuses = {"active", "inactive", "suspended"}
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid status" }

        results = [
            org_info
            for org_info in self.organizations.values()
            if org_info["status"] == status
        ]
        return { "success": True, "data": results }

    def add_api(
        self,
        api_id: str,
        name: str,
        category: str,
        status: str,
        owner_organization_id: str,
        metadata: dict
    ) -> dict:
        """
        Register a new API, ensuring unique api_id and associating it with an organization.

        Args:
            api_id (str): Unique identifier for the API.
            name (str): Name of the API.
            category (str): Category of the API.
            status (str): Status ("active", "inactive", "suspended").
            owner_organization_id (str): Must be an existing organization.
            metadata (dict): Metadata for the API.

        Returns:
            dict:
                success (bool): True if operation succeeded.
                message (str): Success message (if succeeded).
                error (str): Error message (if failed).

        Constraints:
            - api_id must be unique.
            - owner_organization_id must exist in organizations.
            - status must be one of defined values: "active", "inactive", "suspended".
        """
        allowed_statuses = {"active", "inactive", "suspended"}

        if api_id in self.apis:
            return { "success": False, "error": "API ID already exists" }
        if owner_organization_id not in self.organizations:
            return { "success": False, "error": "Owner organization does not exist" }
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid status value" }

        self.apis[api_id] = {
            "api_id": api_id,
            "name": name,
            "category": category,
            "status": status,
            "owner_organization_id": owner_organization_id,
            "metadata": metadata or {},
        }

        return { "success": True, "message": f"API registered with id {api_id}" }

    def update_api_info(
        self,
        api_id: str,
        name: str = None,
        category: str = None,
        metadata: dict = None,
        status: str = None
    ) -> dict:
        """
        Modify selected fields (name, category, metadata, status) of an existing API.

        Args:
            api_id (str): The unique identifier of the API to update.
            name (str, optional): New name for the API.
            category (str, optional): New category for the API.
            metadata (dict, optional): New metadata dictionary for the API.
            status (str, optional): New status for the API ("active", "inactive", "suspended").

        Returns:
            dict: {
                "success": True,
                "message": "API information updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - api_id must exist.
            - status must be one of "active", "inactive", "suspended" if provided.
            - At least one field to update must be provided.
        """
        if api_id not in self.apis:
            return {"success": False, "error": "API with the given api_id does not exist."}

        allowed_statuses = {"active", "inactive", "suspended"}

        # Check at least one field is provided
        if all(arg is None for arg in [name, category, metadata, status]):
            return {"success": False, "error": "No fields provided for update."}

        api = self.apis[api_id]
        updated = False

        if name is not None:
            api["name"] = name
            updated = True

        if category is not None:
            api["category"] = category
            updated = True

        if metadata is not None:
            # Expect full replacement
            api["metadata"] = metadata
            updated = True

        if status is not None:
            if status not in allowed_statuses:
                return {"success": False, "error": "Invalid status value. Must be one of: active, inactive, suspended."}
            api["status"] = status
            updated = True

        if updated:
            self.apis[api_id] = api
            return {"success": True, "message": "API information updated."}
        else:
            return {"success": False, "error": "No fields were updated."}

    def change_api_status(self, api_id: str, new_status: str) -> dict:
        """
        Change the status of an API, enforcing allowed status values.

        Args:
            api_id (str): The identifier of the API to change.
            new_status (str): The desired new status ("active", "inactive", "suspended").

        Returns:
            dict: {
                "success": True,
                "message": "API status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - api_id must correspond to an existing API.
            - new_status must be one of the allowed values: "active", "inactive", "suspended".
            - (Role/permission enforcement not handled here.)
        """
        allowed_statuses = {"active", "inactive", "suspended"}
        if api_id not in self.apis:
            return { "success": False, "error": "API not found" }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status: {new_status}" }
        self.apis[api_id]["status"] = new_status
        return { "success": True, "message": f"API status updated to {new_status}" }

    def delete_api(self, api_id: str) -> dict:
        """
        Remove an API from the platform. If associated, this will also
        remove references to the API from any integrations' linked_api_ids.

        Args:
            api_id (str): The unique identifier for the API to delete.

        Returns:
            dict: {
                "success": True,
                "message": "API <api_id> deleted from platform"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - The API must exist on the platform.
            - API is removed from the self.apis dictionary.
            - Remove this API's id from all integration 'linked_api_ids' lists.
        """

        if api_id not in self.apis:
            return {"success": False, "error": "API not found"}

        # Remove API from all integrations' linked_api_ids where present
        for integration in self.integrations.values():
            if api_id in integration.get("linked_api_ids", []):
                integration["linked_api_ids"] = [
                    aid for aid in integration["linked_api_ids"] if aid != api_id
                ]

        # Remove the API from the platform
        del self.apis[api_id]
        return {"success": True, "message": f"API {api_id} deleted from platform"}

    def add_organization(
        self,
        organization_id: str,
        name: str,
        number_of_seats: int,
        status: str,
        admin_user_id: str
    ) -> dict:
        """
        Register a new organization.

        Args:
            organization_id (str): Unique identifier for the organization.
            name (str): Name of the organization.
            number_of_seats (int): Number of seats (must be >= 0).
            status (str): Organizational status ("active", "inactive", or "suspended").
            admin_user_id (str): User ID of the admin user for this organization.

        Returns:
            dict: {
                "success": True,
                "message": "Organization registered successfully."
            } on success,
            or {
                "success": False,
                "error": <error description>
            } on failure (duplicate ID, invalid parameters, missing admin user).

        Constraints:
            - organization_id must be unique.
            - number_of_seats must not be negative.
            - status must be one of: "active", "inactive", "suspended".
            - admin_user_id must exist in users.
        """
        allowed_status = {"active", "inactive", "suspended"}
        if organization_id in self.organizations:
            return { "success": False, "error": "Organization ID already exists." }
        if number_of_seats < 0:
            return { "success": False, "error": "Number of seats cannot be negative." }
        if status not in allowed_status:
            return { "success": False, "error": "Invalid status value." }
        if admin_user_id not in self.users:
            return { "success": False, "error": "Admin user does not exist." }

        org_info: OrganizationInfo = {
            "organization_id": organization_id,
            "name": name,
            "number_of_seats": number_of_seats,
            "status": status,
            "admin_user_id": admin_user_id
        }

        self.organizations[organization_id] = org_info
        return { "success": True, "message": "Organization registered successfully." }

    def update_organization_info(
        self,
        organization_id: str,
        requester_user_id: str,
        name: str = None,
        number_of_seats: int = None,
        admin_user_id: str = None,
        status: str = None
    ) -> dict:
        """
        Modify attributes of an organization (name, number_of_seats, admin_user_id, status).

        Args:
            organization_id (str): ID of the organization to modify.
            requester_user_id (str): ID of the user requesting the change (must be admin).
            name (str, optional): New name.
            number_of_seats (int, optional): New seat count (must be non-negative).
            admin_user_id (str, optional): New admin user's user_id; must exist in this org.
            status (str, optional): New status ("active", "inactive", "suspended").

        Returns:
            dict: { "success": True, "message": ... }
                  or { "success": False, "error": ... }

        Constraints:
            - Only admins may change organization info.
            - number_of_seats cannot be negative.
            - status must be valid.
            - admin_user_id (if set) must exist in users and belong to the organization.
        """
        # Check organization exists
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }

        org = self.organizations[organization_id]

        # Check requester is admin of this org
        requester = self.users.get(requester_user_id)
        if not requester or requester["organization_id"] != organization_id or requester["role"] != "admin":
            return { "success": False, "error": "Permission denied. Only org admins may modify organization info." }

        # Validate and update provided fields
        allowed_status = {"active", "inactive", "suspended"}

        if name is not None:
            org["name"] = name

        if number_of_seats is not None:
            if number_of_seats < 0:
                return { "success": False, "error": "Number of seats cannot be negative." }
            org["number_of_seats"] = number_of_seats

        if admin_user_id is not None:
            new_admin = self.users.get(admin_user_id)
            if not new_admin or new_admin["organization_id"] != organization_id:
                return { "success": False, "error": "admin_user_id does not correspond to a user in this organization." }
            org["admin_user_id"] = admin_user_id

        if status is not None:
            if status not in allowed_status:
                return { "success": False, "error": f"Invalid status '{status}'. Allowed: {allowed_status}" }
            org["status"] = status

        self.organizations[organization_id] = org  # Persist (dict is mutable, but for clarity)

        return { "success": True, "message": "Organization info updated." }

    def change_organization_status(self, organization_id: str, new_status: str) -> dict:
        """
        Change the status of an organization, enforcing allowed status values.

        Args:
            organization_id (str): ID of the organization to update.
            new_status (str): New status string. Must be one of "active", "inactive", or "suspended".

        Returns:
            dict: {
                "success": True,
                "message": "Organization status updated."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Organization must exist.
            - new_status must be one of allowed values: "active", "inactive", "suspended".
        """
        allowed_statuses = {"active", "inactive", "suspended"}
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Status must be one of {sorted(allowed_statuses)}." }

        self.organizations[organization_id]["status"] = new_status
        return { "success": True, "message": "Organization status updated." }

    def adjust_organization_seats(self, organization_id: str, new_number_of_seats: int) -> dict:
        """
        Update the number_of_seats for an organization.

        Args:
            organization_id (str): The ID of the organization to adjust.
            new_number_of_seats (int): The desired number of seats (must be 0 or greater).

        Returns:
            dict: On success:
                    { "success": True, "message": "Organization <id> seat count updated to <n>." }
                  On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The organization must exist.
            - The number of seats must be non-negative.
        """
        # Existence check
        org = self.organizations.get(organization_id)
        if org is None:
            return { "success": False, "error": f"Organization '{organization_id}' does not exist." }

        # Non-negative seats check
        if not isinstance(new_number_of_seats, int) or new_number_of_seats < 0:
            return { "success": False, "error": "New number_of_seats must be a non-negative integer." }

        org["number_of_seats"] = new_number_of_seats

        return {
            "success": True,
            "message": f"Organization '{organization_id}' seat count updated to {new_number_of_seats}."
        }


    def add_user(
        self,
        name: str,
        email: str,
        organization_id: str,
        role: str,
        status: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user and associate them with an organization.

        Args:
            name (str): Name of the new user.
            email (str): Email address of the user.
            organization_id (str): The organization to associate the user with.
            role (str): Role of the user ("admin", "member", etc.).
            status (str): Status of the user ("active", "inactive", etc.).
            user_id (Optional[str]): Optionally provide a specific user_id; otherwise generated.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "User successfully added with user_id <id>"
                    }
                Failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - organization_id must exist.
            - user_id must be unique.
            - No hard enforcement on role/status strings beyond presence.
        """
        if not all([name, email, organization_id, role, status]):
            return {"success": False, "error": "All fields (name, email, organization_id, role, status) are required."}

        if organization_id not in self.organizations:
            return {"success": False, "error": f"Organization ID '{organization_id}' does not exist."}

        # Generate a unique user_id if not provided
        new_user_id = user_id or str(uuid.uuid4())
        if new_user_id in self.users:
            return {"success": False, "error": f"user_id '{new_user_id}' already exists."}

        # Optionally check for duplicate email (not a requirement)
        for user in self.users.values():
            if user["email"] == email:
                return {"success": False, "error": f"Email '{email}' is already used by another user."}

        user_info: UserInfo = {
            "user_id": new_user_id,
            "name": name,
            "email": email,
            "organization_id": organization_id,
            "role": role,
            "status": status
        }

        self.users[new_user_id] = user_info

        return {"success": True, "message": f"User successfully added with user_id {new_user_id}"}

    def update_user_info(
        self,
        user_id: str,
        name: str = None,
        email: str = None,
        organization_id: str = None,
        role: str = None,
        status: str = None
    ) -> dict:
        """
        Update an existing user's attributes.

        Args:
            user_id (str): The unique identifier of the user to update.
            name (str, optional): New name for the user.
            email (str, optional): New email address.
            organization_id (str, optional): New organization assignment (must exist).
            role (str, optional): New role designation.
            status (str, optional): New status (must be valid, e.g., 'active', 'inactive', 'suspended').

        Returns:
            dict: Result of the operation.
                {"success": True, "message": "User info updated."}
                or
                {"success": False, "error": "<reason>"}

        Constraints:
            - user_id must exist.
            - If organization_id is given, it must exist.
            - If status, must be a valid value.
            - At least one update field (besides user_id) must be provided.
        """
        allowed_statuses = {"active", "inactive", "suspended"}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # No update parameters provided
        if all(param is None for param in [name, email, organization_id, role, status]):
            return {"success": False, "error": "No attributes provided to update."}

        user = self.users[user_id]

        if organization_id is not None:
            if organization_id not in self.organizations:
                return {"success": False, "error": "Target organization does not exist."}
            user["organization_id"] = organization_id

        if status is not None:
            if status not in allowed_statuses:
                return {"success": False, "error": f"Invalid status. Allowed: {', '.join(allowed_statuses)}."}
            user["status"] = status

        if name is not None:
            user["name"] = name

        if email is not None:
            user["email"] = email

        if role is not None:
            user["role"] = role

        self.users[user_id] = user  # Not strictly necessary, as 'user' is ref, but for clarity

        return {"success": True, "message": "User info updated."}

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user from the system.

        Args:
            user_id (str): The unique identifier of the user to remove.

        Returns:
            dict: {
                "success": True,
                "message": "User deleted"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        del self.users[user_id]
        return {"success": True, "message": "User deleted"}

    def add_integration(
        self,
        user_id: str,
        integration_id: str,
        type: str,
        configuration: Dict[str, Any],
        linked_api_ids: List[str],
        organization_id: str
    ) -> dict:
        """
        Register (add) a new integration for an organization.

        Args:
            user_id (str): The user performing the operation (must be admin of organization).
            integration_id (str): Unique identifier for the integration.
            type (str): Type/category of the integration.
            configuration (Dict[str, Any]): Configuration/settings for the integration.
            linked_api_ids (List[str]): List of API IDs to link to this integration.
            organization_id (str): The organization to which this integration is attached.

        Returns:
            dict: {
                "success": True,
                "message": "Integration <integration_id> added to organization <organization_id>."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - integration_id must be unique.
            - organization_id must exist.
            - Each linked_api_id must exist and be associated with this organization.
            - Only 'admin' users for the organization can perform this operation.
        """
        # Check user exists and is admin for this organization
        user = self.users.get(user_id)
        if not user or user["organization_id"] != organization_id or user["role"] != "admin":
            return {"success": False, "error": "Permission denied: Only admins of this organization can add integrations."}

        # Check organization exists
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization not found."}

        # Check integration_id uniqueness
        if integration_id in self.integrations:
            return {"success": False, "error": "Integration ID already exists."}

        # Validate all linked_api_ids
        for aid in linked_api_ids:
            api = self.apis.get(aid)
            if not api:
                return {"success": False, "error": f"API ID '{aid}' does not exist."}
            if api["owner_organization_id"] != organization_id:
                return {"success": False, "error": f"API '{aid}' does not belong to organization '{organization_id}'."}

        # Add integration
        new_integration: IntegrationInfo = {
            "integration_id": integration_id,
            "type": type,
            "configuration": configuration,
            "linked_api_ids": linked_api_ids,
            "organization_id": organization_id
        }
        self.integrations[integration_id] = new_integration
        return {
            "success": True,
            "message": f"Integration '{integration_id}' added to organization '{organization_id}'."
        }

    def update_integration_info(
        self, 
        integration_id: str, 
        configuration: dict = None, 
        linked_api_ids: list = None
    ) -> dict:
        """
        Update integration configuration and/or linked API IDs for a given integration.

        Args:
            integration_id (str): The ID of the integration to update.
            configuration (dict, optional): New configuration dictionary. If None, retains existing.
            linked_api_ids (List[str], optional): List of API IDs to associate with this integration.
                                                 If None, retains existing.

        Returns:
            dict:
                - { "success": True, "message": "Integration info updated." }
                - { "success": False, "error": <reason> }

        Constraints:
            - integration_id must exist in self.integrations.
            - Any new linked_api_ids must all exist in self.apis.
            - At least one of configuration or linked_api_ids must be provided.
        """
        # Check existence of the integration
        if integration_id not in self.integrations:
            return { "success": False, "error": "Integration not found." }
    
        if configuration is None and linked_api_ids is None:
            return { "success": False, "error": "No update data provided." }

        # Check that all linked_api_ids exist (if supplied)
        if linked_api_ids is not None:
            missing_apis = [api_id for api_id in linked_api_ids if api_id not in self.apis]
            if missing_apis:
                return {
                    "success": False,
                    "error": f"One or more API IDs do not exist: {', '.join(missing_apis)}"
                }

        # Perform the updates as requested
        integration = self.integrations[integration_id]
        updated = False

        if configuration is not None:
            integration["configuration"] = configuration
            updated = True
        if linked_api_ids is not None:
            integration["linked_api_ids"] = linked_api_ids
            updated = True

        if updated:
            self.integrations[integration_id] = integration
            return { "success": True, "message": "Integration info updated." }
        else:
            return { "success": False, "error": "No update performed." }

    def delete_integration(self, integration_id: str) -> dict:
        """
        Removes an integration from the system.

        Args:
            integration_id (str): The unique identifier for the integration to delete.

        Returns:
            dict: 
                On success: 
                    {
                        "success": True,
                        "message": "Integration <integration_id> deleted successfully."
                    }
                On failure (e.g., not found): 
                    {
                        "success": False,
                        "error": "Integration not found."
                    }

        Constraints:
            - The specified integration_id must exist in the system.
        """
        if integration_id not in self.integrations:
            return { "success": False, "error": "Integration not found." }
    
        del self.integrations[integration_id]
        return { "success": True, "message": f"Integration {integration_id} deleted successfully." }

    def set_user_role(self, requesting_user_id: str, target_user_id: str, new_role: str) -> dict:
        """
        Assign or update a user's role within their organization.

        Args:
            requesting_user_id (str): The user making the request (must be an admin in the same org).
            target_user_id (str): The user whose role will be updated.
            new_role (str): The role to assign to the user (e.g., "admin", "member").

        Returns:
            dict: {
                "success": True, "message": "User role updated to <new_role>"
            }
            or
            {
                "success": False, "error": "<reason>"
            }

        Constraints:
            - Only users with the "admin" role can set user roles.
            - Both users must exist and belong to the same organization.
            - The new_role should be valid (here, any role string is allowed as rule not specified).
        """
        # Check both users exist
        requesting_user = self.users.get(requesting_user_id)
        if not requesting_user:
            return { "success": False, "error": "Requesting user does not exist" }
        target_user = self.users.get(target_user_id)
        if not target_user:
            return { "success": False, "error": "Target user does not exist" }
        # Check organizations match
        if requesting_user["organization_id"] != target_user["organization_id"]:
            return { "success": False, "error": "Permission denied: different organization" }
        # Check permissions
        if requesting_user["role"] != "admin":
            return { "success": False, "error": "Permission denied: only admins can change user roles" }
        # Idempotent: role already set
        if target_user["role"] == new_role:
            return { "success": True, "message": f"User role already set to {new_role}" }
        # Set role
        self.users[target_user_id]["role"] = new_role
        return { "success": True, "message": f"User role updated to {new_role}" }

    def assign_api_to_organization(self, api_id: str, organization_id: str) -> dict:
        """
        Change or set the owner_organization_id for the specified API.

        Args:
            api_id (str): The identifier of the API to reassign.
            organization_id (str): The target organization's ID.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "API <api_id> assigned to organization <organization_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # description of the failure reason
                    }

        Constraints:
            - api_id must exist in the system.
            - organization_id must exist in the system.
            - Each API must always be associated with one owner organization.
        """
        if api_id not in self.apis:
            return { "success": False, "error": f"API with id '{api_id}' does not exist." }
        if organization_id not in self.organizations:
            return { "success": False, "error": f"Organization with id '{organization_id}' does not exist." }

        # Set the API's owner_organization_id to the new value
        self.apis[api_id]["owner_organization_id"] = organization_id

        return {
            "success": True,
            "message": f"API {api_id} assigned to organization {organization_id}."
        }


class SaaSAdminDashboard(BaseEnv):
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

    def get_api_by_id(self, **kwargs):
        return self._call_inner_tool('get_api_by_id', kwargs)

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_apis_by_organization(self, **kwargs):
        return self._call_inner_tool('list_apis_by_organization', kwargs)

    def get_api_metadata(self, **kwargs):
        return self._call_inner_tool('get_api_metadata', kwargs)

    def get_organization_admin(self, **kwargs):
        return self._call_inner_tool('get_organization_admin', kwargs)

    def list_all_organizations(self, **kwargs):
        return self._call_inner_tool('list_all_organizations', kwargs)

    def list_all_apis(self, **kwargs):
        return self._call_inner_tool('list_all_apis', kwargs)

    def list_organization_users(self, **kwargs):
        return self._call_inner_tool('list_organization_users', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_integration_by_organization(self, **kwargs):
        return self._call_inner_tool('list_integration_by_organization', kwargs)

    def get_integration_by_id(self, **kwargs):
        return self._call_inner_tool('get_integration_by_id', kwargs)

    def list_apis_by_status(self, **kwargs):
        return self._call_inner_tool('list_apis_by_status', kwargs)

    def list_organizations_by_status(self, **kwargs):
        return self._call_inner_tool('list_organizations_by_status', kwargs)

    def add_api(self, **kwargs):
        return self._call_inner_tool('add_api', kwargs)

    def update_api_info(self, **kwargs):
        return self._call_inner_tool('update_api_info', kwargs)

    def change_api_status(self, **kwargs):
        return self._call_inner_tool('change_api_status', kwargs)

    def delete_api(self, **kwargs):
        return self._call_inner_tool('delete_api', kwargs)

    def add_organization(self, **kwargs):
        return self._call_inner_tool('add_organization', kwargs)

    def update_organization_info(self, **kwargs):
        return self._call_inner_tool('update_organization_info', kwargs)

    def change_organization_status(self, **kwargs):
        return self._call_inner_tool('change_organization_status', kwargs)

    def adjust_organization_seats(self, **kwargs):
        return self._call_inner_tool('adjust_organization_seats', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

    def add_integration(self, **kwargs):
        return self._call_inner_tool('add_integration', kwargs)

    def update_integration_info(self, **kwargs):
        return self._call_inner_tool('update_integration_info', kwargs)

    def delete_integration(self, **kwargs):
        return self._call_inner_tool('delete_integration', kwargs)

    def set_user_role(self, **kwargs):
        return self._call_inner_tool('set_user_role', kwargs)

    def assign_api_to_organization(self, **kwargs):
        return self._call_inner_tool('assign_api_to_organization', kwargs)

