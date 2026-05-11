# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Tuple, TypedDict



class ReportInfo(TypedDict):
    report_id: str
    title: str
    authors: List[str]
    issue_date: str
    version: int
    content: str
    status: str  # e.g., 'active', 'archived'

class ReportVersionInfo(TypedDict):
    report_id: str
    version_number: int
    created_date: str
    content: str
    change_description: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    role: str
    access_level: str
    account_status: str

class AccessControlInfo(TypedDict):
    report_id: str
    user_id: str
    permissions: List[str]  # e.g., ['read', 'write', 'download']

class _GeneratedEnvImpl:
    def __init__(self):
        # Reports: {report_id: ReportInfo}
        # Corresponds to entity: Report (report_id, title, authors, issue_date, version, content, status)
        self.reports: Dict[str, ReportInfo] = {}

        # Report Versions: {(report_id, version_number): ReportVersionInfo}
        # Corresponds to entity: ReportVersion (report_id, version_number, created_date, content, change_description)
        self.report_versions: Dict[Tuple[str, int], ReportVersionInfo] = {}

        # Users: {user_id: UserInfo}
        # Corresponds to entity: User (user_id, name, role, access_level, account_status)
        self.users: Dict[str, UserInfo] = {}

        # Access Control: {(report_id, user_id): AccessControlInfo}
        # Corresponds to entity: AccessControl (report_id, user_id, permissions)
        self.access_controls: Dict[Tuple[str, str], AccessControlInfo] = {}

        # Constraints:
        # - Only authorized users may access or retrieve reports.
        # - Each report_id must be unique, and report versions are tracked and retrievable.
        # - Access permissions are checked before permitting viewing or downloading of report content.
        # - Report metadata (title, author, issue date) must be maintained and searchable.

    def get_report_by_id(self, report_id: str, user_id: str) -> dict:
        """
        Retrieve the metadata and content of a report by its unique report_id for an authorized user.

        Args:
            report_id (str): The unique identifier for the report.
            user_id (str): The unique identifier of the user requesting the report.

        Returns:
            dict: 
                - If successful: { "success": True, "data": ReportInfo }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only authorized users (with 'read' permission and active account) may access reports.
            - Returns error if report or user does not exist or access is denied.
        """
        # Check if report exists
        if report_id not in self.reports:
            return { "success": False, "error": "Report does not exist" }
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        user_info = self.users[user_id]
        # Check user account status
        if user_info.get("account_status") != "active":
            return { "success": False, "error": "User account is not active" }
        # Check access control
        access_key = (report_id, user_id)
        ac = self.access_controls.get(access_key)
        if not ac or "read" not in ac.get("permissions", []):
            return { "success": False, "error": "Access denied: insufficient permissions for this report" }
        # All checks passed; return report
        return { "success": True, "data": self.reports[report_id] }

    def check_user_access_to_report(
        self, user_id: str, report_id: str, required_permission: str
    ) -> dict:
        """
        Determine if a user has the required permission (read, write, download) for a given report.

        Args:
            user_id (str): The ID of the user requesting access.
            report_id (str): The ID of the report to check.
            required_permission (str): The type of permission to check ('read', 'write', 'download').

        Returns:
            dict: {
                "success": True,
                "has_permission": bool
            }
            or on error:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Returns success with has_permission True/False if inputs valid.
            - Returns error if user or report does not exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if report_id not in self.reports:
            return { "success": False, "error": "Report does not exist" }
        ac_key = (report_id, user_id)
        permissions = []
        if ac_key in self.access_controls:
            permissions = self.access_controls[ac_key]["permissions"]
        has_permission = required_permission in permissions
        return {
            "success": True,
            "has_permission": has_permission
        }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve details (role, access_level, account_status, name, etc.) for the given user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # if user is found
            }
            or
            {
                "success": False,
                "error": str  # if user_id is not found
            }

        Constraints:
            - user_id must exist in the system. If not, return an error.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_reports_by_attribute(self, **attributes) -> dict:
        """
        Retrieve all reports matching specified attributes.
    
        Args:
            attributes: Keyword arguments for any subset of the following
                (title, authors, issue_date, version, status, etc).
                - 'authors' can be a string or a list (at least one must match).
                - All other attributes checked with equality.

        Returns:
            dict:
                - success: True/False
                - data: List[ReportInfo] (if successful)
                - error: str (if not successful)
    
        Constraints:
            - Attributes must be valid fields of ReportInfo.
            - If no valid attributes specified, returns error.
        """
        valid_fields = {"report_id", "title", "authors", "issue_date", "version", "content", "status"}
        used_attrs = {k: v for k, v in attributes.items() if k in valid_fields and v is not None}

        if not used_attrs:
            return {"success": False, "error": "No valid attributes specified for filtering"}
    
        result = []
        for report in self.reports.values():
            match = True
            for attr, value in used_attrs.items():
                if attr == "authors":
                    # support single string or list, and match if any author is present
                    report_authors = [a.lower() for a in report.get("authors", [])]
                    if isinstance(value, str):
                        if value.lower() not in report_authors:
                            match = False
                            break
                    elif isinstance(value, list):
                        if not any(v.lower() in report_authors for v in value if isinstance(v, str)):
                            match = False
                            break
                    else:
                        match = False
                        break
                else:
                    # direct equality
                    if report.get(attr) != value:
                        match = False
                        break
            if match:
                result.append(report)
    
        return {"success": True, "data": result}

    def get_report_versions(self, report_id: str) -> dict:
        """
        List all available versions for a specific report_id.

        Args:
            report_id (str): The unique identifier of the report whose versions are to be listed.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": List[ReportVersionInfo]  # Sorted by version_number ascending
                }
              - On failure: {
                    "success": False,
                    "error": str  # Reason, e.g. "Report ID does not exist"
                }

        Constraints:
            - The report_id must exist in the system.
        """
        if report_id not in self.reports:
            return {"success": False, "error": "Report ID does not exist"}

        versions = [
            rv for (rid, _), rv in self.report_versions.items()
            if rid == report_id
        ]
        # Optionally, sort by version_number ascending
        versions.sort(key=lambda rv: rv["version_number"])
        return {"success": True, "data": versions}

    def get_report_version_content(self, report_id: str, version_number: int) -> dict:
        """
        Fetch the content and metadata of a specific version of a report.

        Args:
            report_id (str): The report's unique identifier.
            version_number (int): The version number of the report to fetch.

        Returns:
            dict: {
                "success": True,
                "data": ReportVersionInfo  # Content and metadata of the specified report version.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., report/version not found.
            }

        Constraints:
            - The (report_id, version_number) combination must exist in the system.
            - No access or permission check is required for this operation.
        """
        key = (report_id, version_number)
        if key not in self.report_versions:
            return {"success": False, "error": "Specified report version does not exist."}

        return {"success": True, "data": self.report_versions[key]}

    def search_reports(self, **criteria) -> dict:
        """
        Search the report database using combinations of metadata attributes.

        Supported criteria keys:
            - report_id (str; substring match, case-insensitive)
            - title (str; substring match, case-insensitive)
            - authors (str or List[str]; report matches if any supplied author matches any of its authors, case-insensitive)
            - issue_date (str; exact match)
            - version (int)
            - status (str; e.g., 'active', 'archived')

        Args:
            **criteria: Arbitrary report metadata fields and values to filter on.
    
        Returns:
            dict:
                On success: {"success": True, "data": List[ReportInfo]}
                On failure: {"success": False, "error": reason}

        Constraints:
            - Unknown fields are ignored.
            - All supplied criteria must be AND'ed (i.e., report must satisfy ALL provided filters).
        """
        # No criteria: return all reports
        if not criteria:
            return {"success": True, "data": list(self.reports.values())}

        matched_reports = []
        # Supported fields
        allowed_fields = {"report_id", "title", "authors", "issue_date", "version", "status"}

        for report in self.reports.values():
            is_match = True
            for key, value in criteria.items():
                if key not in allowed_fields:
                    continue  # Ignore unsupported criteria fields
                if key == "title":
                    # Substring, case-insensitive matching
                    if not isinstance(value, str) or value.lower() not in report["title"].lower():
                        is_match = False
                        break
                elif key == "authors":
                    report_authors = [a.lower() for a in report.get("authors", [])]
                    if isinstance(value, str):
                        # Match if any author matches (case-insensitive)
                        if value.lower() not in report_authors:
                            is_match = False
                            break
                    elif isinstance(value, list):
                        # Match if any supplied author is in report_authors
                        value_lower = [v.lower() for v in value if isinstance(v, str)]
                        if not any(v in report_authors for v in value_lower):
                            is_match = False
                            break
                    else:
                        # Invalid type
                        is_match = False
                        break
                elif key == "version":
                    if report.get("version") != value:
                        is_match = False
                        break
                elif key == "report_id":
                    if not isinstance(value, str) or value.lower() not in report.get("report_id", "").lower():
                        is_match = False
                        break
                elif key == "issue_date":
                    if report.get("issue_date") != value:
                        is_match = False
                        break
                elif key == "status":
                    if report.get("status") != value:
                        is_match = False
                        break
            if is_match:
                matched_reports.append(report)

        return {"success": True, "data": matched_reports}

    def list_user_permissions(self, user_id: str) -> dict:
        """
        List all permissions a user has across all reports.

        Args:
            user_id (str): User identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[{"report_id": str, "permissions": List[str]}]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist in the system.
            - Only reports the user's explicit permissions across all reports.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        result = []
        for (report_id, uid), acl in self.access_controls.items():
            if uid == user_id:
                result.append({
                    "report_id": report_id,
                    "permissions": acl["permissions"]
                })
    
        return { "success": True, "data": result }

    def create_report(
        self,
        report_id: str,
        title: str,
        authors: list,
        issue_date: str,
        content: str,
        created_by_user_id: str,
        status: str = "active"
    ) -> dict:
        """
        Add a new report to the system with metadata and initial content.

        Args:
            report_id (str): Unique ID for the report.
            title (str): Title of the report.
            authors (List[str]): List of author names or user IDs.
            issue_date (str): The date the report is issued.
            content (str): The body/content of the report.
            created_by_user_id (str): The user ID of the creator.
            status (str, optional): Initial report status. Defaults to 'active'.

        Returns:
            dict: {
                "success": True,
                "message": "Report created successfully."
            }
            or
            dict: {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - report_id must be unique.
            - The user creating the report must exist and be 'active'.
            - Initial version (1) must be created in version history.
        """
        # Check user exists and is active
        userinfo = self.users.get(created_by_user_id)
        if not userinfo or userinfo['account_status'] != 'active':
            return {"success": False, "error": "Creator user does not exist or is not active."}

        # Check uniqueness of report_id
        if report_id in self.reports:
            return {"success": False, "error": "Report ID already exists."}

        # Basic input validation
        if not (report_id and title and authors and issue_date and content):
            return {"success": False, "error": "All mandatory fields must be provided."}

        # Create the report info
        report_info: ReportInfo = {
            "report_id": report_id,
            "title": title,
            "authors": authors,
            "issue_date": issue_date,
            "version": 1,
            "content": content,
            "status": status
        }
        self.reports[report_id] = report_info

        # Add initial version to report_versions
        report_version_info: ReportVersionInfo = {
            "report_id": report_id,
            "version_number": 1,
            "created_date": issue_date,
            "content": content,
            "change_description": "Initial version created"
        }
        self.report_versions[(report_id, 1)] = report_version_info

        # Assign access rights: Creator gets all rights on this report
        self.access_controls[(report_id, created_by_user_id)] = {
            "report_id": report_id,
            "user_id": created_by_user_id,
            "permissions": ["read", "write", "download"]
        }

        return {"success": True, "message": "Report created successfully."}

    def update_report_metadata(
        self, 
        report_id: str, 
        title: str = None, 
        authors: list = None, 
        issue_date: str = None
    ) -> dict:
        """
        Modify a report's metadata (title, authors, or issue_date).
    
        Args:
            report_id (str): The unique ID of the report to modify.
            title (Optional[str]): New title for the report.
            authors (Optional[List[str]]): New list of authors.
            issue_date (Optional[str]): New issue date (string).
    
        Returns:
            dict: {
                "success": True,
                "message": "Report metadata updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - Report must exist.
            - At least one metadata field (title, authors, issue_date) must be provided.
            - authors (if provided) must be a list of strings.
        """
        if report_id not in self.reports:
            return { "success": False, "error": "Report does not exist." }

        if title is None and authors is None and issue_date is None:
            return { "success": False, "error": "No metadata fields to update provided." }

        report = self.reports[report_id]
        updated = False

        if title is not None:
            if not isinstance(title, str):
                return { "success": False, "error": "Title must be a string." }
            report["title"] = title
            updated = True

        if authors is not None:
            if not isinstance(authors, list) or not all(isinstance(a, str) for a in authors):
                return { "success": False, "error": "Authors must be a list of strings." }
            report["authors"] = authors
            updated = True

        if issue_date is not None:
            if not isinstance(issue_date, str):
                return { "success": False, "error": "Issue date must be a string." }
            report["issue_date"] = issue_date
            updated = True

        if not updated:
            return { "success": False, "error": "No valid metadata fields to update." }

        self.reports[report_id] = report
        return { "success": True, "message": "Report metadata updated." }

    def add_report_version(
        self,
        report_id: str,
        content: str,
        change_description: str,
        created_date: str,
    ) -> dict:
        """
        Add a new version to an existing report, storing content and change description.

        Args:
            report_id (str): The unique report identifier for the report to version.
            content (str): The new version's content.
            change_description (str): Description of changes in this version.
            created_date (str): ISO8601 or similar date string for when version is created.

        Returns:
            dict: {
                "success": True,
                "message": "Report version X for report <report_id> added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - report_id must exist in the system.
            - Cannot add a version to an archived report.
            - Active and draft reports may receive new versions.
            - Version numbers are strictly incremented.
            - Report metadata is updated accordingly.
        """
        # Validate report existence
        report = self.reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report ID not found."}

        # Archived reports are immutable, but draft and active reports may continue versioning.
        if report.get("status", "active") == "archived":
            return {"success": False, "error": "Cannot add version to archived report."}

        # Get current version, default to 1 if missing
        current_version = report.get("version", 1)
        new_version_number = current_version + 1

        # Check that the version doesn't already exist
        if (report_id, new_version_number) in self.report_versions:
            return {"success": False, "error": f"Version {new_version_number} for report {report_id} already exists."}

        # Create and add the new version
        version_info: ReportVersionInfo = {
            "report_id": report_id,
            "version_number": new_version_number,
            "created_date": created_date,
            "content": content,
            "change_description": change_description
        }
        self.report_versions[(report_id, new_version_number)] = version_info

        # Update master Report
        report["version"] = new_version_number
        report["content"] = content
        # (Optional: update a modified/updated timestamp if present)

        self.reports[report_id] = report

        return {
            "success": True,
            "message": f"Report version {new_version_number} for report {report_id} added successfully."
        }

    def archive_report(self, report_id: str) -> dict:
        """
        Change the status of the specified report to "archived".

        Args:
            report_id (str): The unique identifier of the report to be archived.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Report <report_id> has been archived."
                  }
                - On failure: {
                    "success": False,
                    "error": "Report not found."
                  }

        Constraints:
            - The specified report must exist.
            - Status is set to "archived" regardless of current state (idempotent).
            - No user/permission check is performed in this operation.
        """
        report = self.reports.get(report_id)
        if not report:
            return { "success": False, "error": "Report not found." }

        report["status"] = "archived"
        return { "success": True, "message": f"Report {report_id} has been archived." }

    def modify_access_control(
        self,
        report_id: str,
        user_id: str,
        permissions: list,
        action: str  # 'grant' or 'revoke'
    ) -> dict:
        """
        Update access permissions for a user on a specific report (grant or revoke permissions).

        Args:
            report_id (str): The report whose access control is to be updated.
            user_id (str): The user whose permissions are being changed.
            permissions (list of str): List of permissions to grant or revoke. Supported: 'read', 'write', 'download'.
            action (str): Either 'grant' (add/set permissions) or 'revoke' (remove specified permissions).
    
        Returns:
            dict:
                On success: { "success": True, "message": <description> }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - report_id and user_id must exist.
            - permissions must not be empty, and all permissions must be valid.
            - Grant: adds (without duplicating) or sets permissions. If entry does not exist, creates.
            - Revoke: removes listed permissions; deletes the entry if no permissions remain.
        """
        # Validate report existence
        if report_id not in self.reports:
            return { "success": False, "error": "Report not found" }
        # ACL changes are admin-side operations, so suspended/inactive users
        # can still have their permissions updated or revoked.
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        valid_permissions = {"read", "write", "download"}
        # Filter out invalid permissions
        filtered_permissions = [p for p in permissions if p in valid_permissions]
        if not filtered_permissions:
            return { "success": False, "error": "No valid permissions specified" }

        key = (report_id, user_id)
        current_entry = self.access_controls.get(key)

        # Grant permissions
        if action == 'grant':
            if current_entry:
                # Add any new permissions (no duplicates)
                new_perms = set(current_entry['permissions'])
                before = new_perms.copy()
                new_perms.update(filtered_permissions)
                self.access_controls[key]['permissions'] = sorted(list(new_perms))
                added = new_perms - before
                msg = f"Granted permissions {list(added)} to user {user_id} for report {report_id}." if added else "No new permissions were granted."
            else:
                self.access_controls[key] = {
                    "report_id": report_id,
                    "user_id": user_id,
                    "permissions": sorted(list(set(filtered_permissions)))
                }
                msg = f"Granted permissions {filtered_permissions} to user {user_id} for report {report_id}."
            return { "success": True, "message": msg }

        # Revoke permissions
        elif action == 'revoke':
            if not current_entry:
                return { "success": False, "error": "No permissions found to revoke for user on this report." }
            else:
                existing = set(current_entry["permissions"])
                before = existing.copy()
                to_remove = set(filtered_permissions)
                remaining = existing - to_remove
                revoked = existing & to_remove
                if not revoked:
                    return { "success": False, "error": "Specified permissions were not present." }
                if remaining:
                    self.access_controls[key]["permissions"] = sorted(list(remaining))
                    msg = f"Revoked permissions {list(revoked)} from user {user_id} for report {report_id}."
                else:
                    # All permissions revoked, remove entry
                    del self.access_controls[key]
                    msg = f"All permissions revoked for user {user_id} on report {report_id}; access entry deleted."
                return { "success": True, "message": msg }
        else:
            return { "success": False, "error": "Invalid action. Use 'grant' or 'revoke'." }

    def register_user(
        self,
        user_id: str,
        name: str,
        role: str,
        access_level: str,
        account_status: str
    ) -> dict:
        """
        Create a new user account in the system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): Display name of the user.
            role (str): Role of the user (e.g., 'analyst', 'manager').
            access_level (str): Access privilege level (e.g., 'basic', 'admin').
            account_status (str): Account status, such as 'active', 'inactive'.

        Returns:
            dict: {
                "success": True, "message": "User registered successfully."
            }
            or
            {
                "success": False, "error": <reason>
            }

        Constraints:
            - user_id must be unique.
            - All fields must be provided and non-empty.
        """
        # Basic input check
        if not all([user_id, name, role, access_level, account_status]):
            return { "success": False, "error": "All user fields must be provided and non-empty." }

        if user_id in self.users:
            return { "success": False, "error": f"User with user_id '{user_id}' already exists." }

        user_info: UserInfo = {
            "user_id": user_id,
            "name": name,
            "role": role,
            "access_level": access_level,
            "account_status": account_status
        }

        self.users[user_id] = user_info

        return { "success": True, "message": "User registered successfully." }

    def update_user_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's account_status (e.g., set to active/inactive/suspended).

        Args:
            user_id (str): ID of the user whose status is to be updated.
            new_status (str): New status string to set ('active', 'inactive', 'suspended', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "User account_status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - user_id must refer to an existing user in the system.
            - Only updates the 'account_status' field of the user record.
            - No restriction on new_status value is specified, but typical values are 'active', 'inactive', 'suspended'.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User ID does not exist."}

        self.users[user_id]['account_status'] = new_status
        return {"success": True, "message": f"User account_status updated to {new_status}."}

    def delete_report(self, report_id: str, user_id: str) -> dict:
        """
        Remove a report and all associated versions and access control entries from the system.
        Only admin users may perform this operation.

        Args:
            report_id (str): The ID of the report to delete.
            user_id (str): The user requesting the operation.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation if successful
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - Only users with role 'admin' can delete reports.
            - Deletion removes all associated report versions and access controls.
            - The report must exist.
            - The requesting user must exist.
        """

        # Check that user exists and is admin
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}
        if user_info.get("role") != "admin":
            return {"success": False, "error": "Permission denied: only admins can delete reports"}

        # Check report existence
        if report_id not in self.reports:
            return {"success": False, "error": "Report does not exist"}

        # Remove the report
        del self.reports[report_id]

        # Remove all versions
        versions_to_remove = [key for key in self.report_versions if key[0] == report_id]
        for vkey in versions_to_remove:
            del self.report_versions[vkey]

        # Remove all access control entries for this report
        ac_to_remove = [key for key in self.access_controls if key[0] == report_id]
        for ackey in ac_to_remove:
            del self.access_controls[ackey]

        return {
            "success": True,
            "message": f"Report {report_id} and all associated versions removed"
        }


class EnterpriseReportManagementSystem(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "report_versions" and isinstance(copied, dict):
                normalized = {}
                for original_key, info in copied.items():
                    if isinstance(info, dict):
                        report_id = info.get("report_id")
                        version_number = info.get("version_number")
                        if report_id is not None and version_number is not None:
                            normalized[(report_id, version_number)] = info
                            continue
                    normalized[original_key] = info
                setattr(env, key, normalized)
                continue
            if key == "access_controls" and isinstance(copied, dict):
                normalized = {}
                for original_key, info in copied.items():
                    if isinstance(info, dict):
                        report_id = info.get("report_id")
                        user_id = info.get("user_id")
                        if report_id is not None and user_id is not None:
                            normalized[(report_id, user_id)] = info
                            continue
                    normalized[original_key] = info
                setattr(env, key, normalized)
                continue
            setattr(env, key, copied)

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

    def get_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_report_by_id', kwargs)

    def check_user_access_to_report(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_report', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_reports_by_attribute(self, **kwargs):
        return self._call_inner_tool('list_reports_by_attribute', kwargs)

    def get_report_versions(self, **kwargs):
        return self._call_inner_tool('get_report_versions', kwargs)

    def get_report_version_content(self, **kwargs):
        return self._call_inner_tool('get_report_version_content', kwargs)

    def search_reports(self, **kwargs):
        return self._call_inner_tool('search_reports', kwargs)

    def list_user_permissions(self, **kwargs):
        return self._call_inner_tool('list_user_permissions', kwargs)

    def create_report(self, **kwargs):
        return self._call_inner_tool('create_report', kwargs)

    def update_report_metadata(self, **kwargs):
        return self._call_inner_tool('update_report_metadata', kwargs)

    def add_report_version(self, **kwargs):
        return self._call_inner_tool('add_report_version', kwargs)

    def archive_report(self, **kwargs):
        return self._call_inner_tool('archive_report', kwargs)

    def modify_access_control(self, **kwargs):
        return self._call_inner_tool('modify_access_control', kwargs)

    def register_user(self, **kwargs):
        return self._call_inner_tool('register_user', kwargs)

    def update_user_status(self, **kwargs):
        return self._call_inner_tool('update_user_status', kwargs)

    def delete_report(self, **kwargs):
        return self._call_inner_tool('delete_report', kwargs)
