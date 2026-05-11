# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional, List
import datetime
import json
import csv
import io



class OrganizationInfo(TypedDict):
    organization_id: str
    organization_type: str
    name: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str
    organization_id: str
    role: str

class ProjectInfo(TypedDict):
    project_id: str
    name: str
    organization_id: str

class TimeEntryInfo(TypedDict):
    time_entry_id: str
    user_id: str
    project_id: str
    organization_id: str
    start_time: str
    end_time: str
    duration: float
    description: str
    day: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Time Entries: {time_entry_id: TimeEntryInfo}
        self.time_entries: Dict[str, TimeEntryInfo] = {}

        # Constraints and rules:
        # - Each time entry must be associated with a valid user, project, and organization.
        # - Projects must belong to a single organization.
        # - Users belong to a single organization but may contribute to multiple projects within that organization.
        # - Reports can be filtered by organization, company, agency, user, and project.
        # - Supported export formats for reporting: CSV and JSON.

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve organization details given its organization_id.

        Args:
            organization_id (str): The unique ID of the organization to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": OrganizationInfo  # Organization info for the ID
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. organization not found
            }

        Constraints:
            - The organization_id must exist in the system.
        """
        organization = self.organizations.get(organization_id)
        if organization is None:
            return { "success": False, "error": "Organization not found" }
    
        return { "success": True, "data": organization }

    def list_organizations_by_type(self, organization_type: str) -> dict:
        """
        Retrieve all organizations filtered by organization_type (e.g., "agency", "company").

        Args:
            organization_type (str): The type of organization to filter for.

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo], # The organizations matching the given type (may be empty)
            }

        Notes:
            - If no organizations match the type, returns an empty list.
            - organization_type is case-sensitive for filtering (as per stored).
        """
        if not isinstance(organization_type, str) or not organization_type:
            return {
                "success": False,
                "error": "organization_type must be a non-empty string"
            }

        result = [
            organization
            for organization in self.organizations.values()
            if organization.get("organization_type") == organization_type
        ]
        return {
            "success": True,
            "data": result
        }

    def get_projects_by_organization(self, organization_id: str) -> dict:
        """
        List all projects that belong to the given organization.

        Args:
            organization_id (str): The ID of the organization to search for.

        Returns:
            dict:
                - success: True and data (list of ProjectInfo) on success.
                - success: False and error message if organization does not exist.

        Constraints:
            - The specified organization_id must exist in the system.
            - Each project belongs to a single organization.

        Edge Cases:
            - If organization exists but has no projects, returns success with empty data list.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }
    
        projects = [
            project_info for project_info in self.projects.values()
            if project_info["organization_id"] == organization_id
        ]
        return { "success": True, "data": projects }

    def get_users_by_organization(self, organization_id: str) -> dict:
        """
        List all users that belong to a given organization.

        Args:
            organization_id (str): The ID of the target organization.

        Returns:
            dict:
                - On success: { "success": True, "data": List[UserInfo] }
                  (Returns all users matching the given organization_id; empty list if none.)
                - On failure: { "success": False, "error": str }
                  (Error if the organization does not exist.)

        Constraints:
            - Organization must exist in the system.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        result = [
            user_info for user_info in self.users.values()
            if user_info["organization_id"] == organization_id
        ]
        return { "success": True, "data": result }

    def get_time_entries_by_organization(self, organization_id: str) -> dict:
        """
        Retrieve all time entries associated with a given organization.

        Args:
            organization_id (str): The unique identifier for the organization.

        Returns:
            dict: {
                "success": True,
                "data": List[TimeEntryInfo]  # List of time entries for the organization (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g., organization does not exist
            }

        Constraints:
            - The organization must exist in the system.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        result = [
            te for te in self.time_entries.values()
            if te["organization_id"] == organization_id
        ]

        return {"success": True, "data": result}

    def get_time_entries_by_project(self, project_id: str) -> dict:
        """
        Retrieve all time entries associated with the specified project.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict: {
                "success": True,
                "data": List[TimeEntryInfo],  # List of time entries, possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. "Project does not exist"
            }

        Constraints:
            - The project must exist in the system.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        result = [
            time_entry for time_entry in self.time_entries.values()
            if time_entry["project_id"] == project_id
        ]

        return {"success": True, "data": result}

    def get_time_entries_by_user(self, user_id: str) -> dict:
        """
        Retrieve all time entries recorded by a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[TimeEntryInfo]  # List of all time entries for the user
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., user not found
            }

        Constraints:
            - user_id must exist in the users dictionary.
            - Returns all matching entries; result may be empty.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        entries = [
            entry for entry in self.time_entries.values()
            if entry["user_id"] == user_id
        ]
        return {"success": True, "data": entries}


    def filter_time_entries(
        self,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Retrieve time entries filtered by arbitrary combinations of organization, project, user, and/or date range.

        Args:
            organization_id (str, optional): Only include entries with this organization_id.
            project_id (str, optional): Only include entries with this project_id.
            user_id (str, optional): Only include entries with this user_id.
            start_date (str, optional): ‘YYYY-MM-DD’ - only include entries with day >= this date.
            end_date (str, optional): ‘YYYY-MM-DD’ - only include entries with day <= this date.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": [TimeEntryInfo, ...] }
                On failure:
                    { "success": False, "error": <reason> }

        Notes/Constraints:
            - If no filters are provided, returns all time entries.
            - If start_date or end_date are present, must be parseable as YYYY-MM-DD.
            - Does not error on non-existent org/project/user IDs; just filters by value.
        """
        # Parse dates if provided
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        except Exception:
            return { "success": False, "error": "Invalid date format for start_date or end_date (expected YYYY-MM-DD)" }
    
        result = []
        for entry in self.time_entries.values():
            if organization_id is not None and entry["organization_id"] != organization_id:
                continue
            if project_id is not None and entry["project_id"] != project_id:
                continue
            if user_id is not None and entry["user_id"] != user_id:
                continue
            # Date range matches on 'day' field (assumed YYYY-MM-DD)
            if (start_dt or end_dt):
                try:
                    entry_day = datetime.datetime.strptime(entry["day"], "%Y-%m-%d").date()
                except Exception:
                    continue  # skip entry with invalid date
                if start_dt and entry_day < start_dt:
                    continue
                if end_dt and entry_day > end_dt:
                    continue
            result.append(entry)

        return { "success": True, "data": result }

    def aggregate_time_by_user(
        self, 
        organization_id: str = None, 
        project_id: str = None, 
        user_id: str = None
    ) -> dict:
        """
        Aggregate and summarize total recorded time per user, filtered by organization, project, or user.

        Args:
            organization_id (str, optional): The organization to filter by.
            project_id (str, optional): The project to filter by.
            user_id (str, optional): The user to filter by.

        Returns:
            dict: {
                "success": True,
                "data": [
                    {
                        "user_id": str,
                        "user_name": str,
                        "total_duration": float
                    }
                    ...
                ]
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - If a filter ID is provided, it must exist in the system.
            - If no entries match, returns an empty list.
        """
        # Validate filters
        if organization_id is not None and organization_id not in self.organizations:
            return {"success": False, "error": "Organization ID does not exist"}
        if project_id is not None and project_id not in self.projects:
            return {"success": False, "error": "Project ID does not exist"}
        if user_id is not None and user_id not in self.users:
            return {"success": False, "error": "User ID does not exist"}

        # Aggregate durations
        user_durations = {}  # user_id: float

        for entry in self.time_entries.values():
            if organization_id is not None and entry["organization_id"] != organization_id:
                continue
            if project_id is not None and entry["project_id"] != project_id:
                continue
            if user_id is not None and entry["user_id"] != user_id:
                continue

            uid = entry["user_id"]
            duration = entry.get("duration", 0.0)
            if uid in user_durations:
                user_durations[uid] += duration
            else:
                user_durations[uid] = duration

        # Prepare result
        results = []
        for uid, total_duration in user_durations.items():
            user_info = self.users.get(uid)
            user_name = user_info["name"] if user_info else ""
            results.append({
                "user_id": uid,
                "user_name": user_name,
                "total_duration": total_duration
            })

        return { "success": True, "data": results }

    def aggregate_time_by_project(self, organization_id: str) -> dict:
        """
        Aggregate and summarize total recorded time per project within a given organization.

        Args:
            organization_id (str): The ID of the organization by which to aggregate projects and time entries.

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "project_id": str,
                    "project_name": str,
                    "total_duration": float
                }]
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only includes projects belonging to the organization.
            - Only sums durations of time entries belonging to each project (and the organization).
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist."}

        # Gather all projects for this organization
        projects_in_org = {
            pid: proj
            for pid, proj in self.projects.items()
            if proj["organization_id"] == organization_id
        }

        # Initialize aggregation map
        project_totals = {pid: 0.0 for pid in projects_in_org}

        # Aggregate durations
        for entry in self.time_entries.values():
            pid = entry["project_id"]
            if entry["organization_id"] == organization_id and pid in project_totals:
                duration = entry.get("duration", 0.0)
                if isinstance(duration, (int, float)):
                    project_totals[pid] += duration

        # Build result
        data = [
            {
                "project_id": pid,
                "project_name": projects_in_org[pid]["name"],
                "total_duration": project_totals[pid]
            }
            for pid in projects_in_org
        ]

        return {"success": True, "data": data}

    def export_report(self, filters: dict, format: str) -> dict:
        """
        Export a filtered time report to the specified format (CSV or JSON).
        Filter keys can include: organization_id, organization_type, user_id, project_id.
    
        Args:
            filters (dict): Filtering criteria for time entries (e.g., organization_id, user_id, project_id).
            format (str): Export format, must be 'CSV' or 'JSON' (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": <str: export content>,
                "format": <"CSV"|"JSON">
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Only supports CSV and JSON.
            - Returns empty export if no entries found.
            - Filters with unknown values (e.g., org/project/user IDs not present) yield empty results.
        """

        # Validate format
        fmt = format.upper()
        if fmt not in ("CSV", "JSON"):
            return {"success": False, "error": f"Unsupported format '{format}'. Only 'CSV' and 'JSON' allowed."}

        # Build filtered list
        filtered_entries = list(self.time_entries.values())

        # Supported filter keys
        allowed_filter_keys = {
            "organization_id", 
            "organization_type", 
            "user_id", 
            "project_id"
        }
        # Handle organization_type filter
        org_type_filter = filters.get("organization_type")
        if org_type_filter:
            allowed_orgs = [
                oid for oid, org in self.organizations.items()
                if org.get("organization_type") == org_type_filter
            ]
            filtered_entries = [
                entry for entry in filtered_entries 
                if entry.get("organization_id") in allowed_orgs
            ]
        # Other basic filters
        for key in ["organization_id", "user_id", "project_id"]:
            value = filters.get(key)
            if value:
                filtered_entries = [
                    entry for entry in filtered_entries if entry.get(key) == value
                ]

        # If user/org/project filter specified but entity does not exist: return empty
        if filters.get("organization_id") and filters["organization_id"] not in self.organizations:
            filtered_entries = []
        if filters.get("project_id") and filters["project_id"] not in self.projects:
            filtered_entries = []
        if filters.get("user_id") and filters["user_id"] not in self.users:
            filtered_entries = []

        # Export
        if fmt == "JSON":
            export_content = json.dumps(filtered_entries, indent=2)
        elif fmt == "CSV":
            output = io.StringIO()
            # Determine CSV headers
            headers = [
                "time_entry_id", "user_id", "project_id", "organization_id",
                "start_time", "end_time", "duration", "description", "day"
            ]
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for entry in filtered_entries:
                # Only write known headers
                row = {h: entry.get(h, "") for h in headers}
                writer.writerow(row)
            export_content = output.getvalue()
            output.close()
        else:
            return {"success": False, "error": "Unexpected export format."}

        return {
            "success": True,
            "data": export_content,
            "format": fmt
        }

    def add_time_entry(self,
                       time_entry_id: str,
                       user_id: str,
                       project_id: str,
                       organization_id: str,
                       start_time: str,
                       end_time: str,
                       duration: float,
                       description: str,
                       day: str) -> dict:
        """
        Add a new time entry to the system, ensuring all associations and integrity constraints.

        Args:
            time_entry_id (str): Unique ID for the new time entry.
            user_id (str): ID of the user recording this time.
            project_id (str): Associated project ID.
            organization_id (str): Associated organization ID.
            start_time (str): Start time (ISO string or platform standard).
            end_time (str): End time (ISO string or platform standard).
            duration (float): Duration in hours (or platform standard).
            description (str): Description of work/time.
            day (str): Date for the time entry.

        Returns:
            dict: Success or failure message.

        Constraints:
            - time_entry_id must be unique (not already in self.time_entries).
            - user_id, project_id, organization_id must exist in their respective stores.
            - The user and project must both belong to the given organization.

        """
        # Uniqueness check
        if time_entry_id in self.time_entries:
            return { "success": False, "error": "Time entry ID already exists." }
        # Existence checks
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
        # Integrity constraints
        user_info = self.users[user_id]
        project_info = self.projects[project_id]
        if user_info['organization_id'] != organization_id:
            return { "success": False, "error": "User does not belong to the given organization." }
        if project_info['organization_id'] != organization_id:
            return { "success": False, "error": "Project does not belong to the given organization." }
    
        # All validations passed - create the entry
        time_entry: TimeEntryInfo = {
            "time_entry_id": time_entry_id,
            "user_id": user_id,
            "project_id": project_id,
            "organization_id": organization_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "description": description,
            "day": day
        }
        self.time_entries[time_entry_id] = time_entry
        return { "success": True, "message": "Time entry added successfully." }

    def update_time_entry(
        self,
        time_entry_id: str,
        user_id: str = None,
        project_id: str = None,
        organization_id: str = None,
        start_time: str = None,
        end_time: str = None,
        duration: float = None,
        description: str = None,
        day: str = None
    ) -> dict:
        """
        Update properties of an existing time entry. Only provided arguments will be updated.

        Args:
            time_entry_id (str): The ID of the time entry to update.
            user_id (str, optional): New user ID.
            project_id (str, optional): New project ID.
            organization_id (str, optional): New organization ID.
            start_time (str, optional): New start time.
            end_time (str, optional): New end time.
            duration (float, optional): New duration in hours.
            description (str, optional): New description.
            day (str, optional): New date.

        Returns:
            dict: {
                "success": True,
                "message": "Time entry updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - time_entry_id must exist.
            - If user_id/project_id/organization_id are provided, they must exist.
            - The user and project must both belong to the (possibly updated) organization.
            - All associations must remain valid according to the constraints.
            - At least one updatable field must be provided.
        """
        # Check if time entry exists
        if time_entry_id not in self.time_entries:
            return {"success": False, "error": "Time entry not found"}

        entry = self.time_entries[time_entry_id]

        # Make a local copy to check new associations
        new_user_id = user_id if user_id is not None else entry["user_id"]
        new_project_id = project_id if project_id is not None else entry["project_id"]
        new_organization_id = organization_id if organization_id is not None else entry["organization_id"]

        # Validate entities
        if new_user_id not in self.users:
            return {"success": False, "error": "Specified user_id does not exist"}
        if new_project_id not in self.projects:
            return {"success": False, "error": "Specified project_id does not exist"}
        if new_organization_id not in self.organizations:
            return {"success": False, "error": "Specified organization_id does not exist"}

        # Validate relationships
        user_info = self.users[new_user_id]
        project_info = self.projects[new_project_id]

        if user_info["organization_id"] != new_organization_id:
            return {"success": False, "error": "User does not belong to the specified organization"}
        if project_info["organization_id"] != new_organization_id:
            return {"success": False, "error": "Project does not belong to the specified organization"}

        # Check at least one field to update
        updatable = [user_id, project_id, organization_id, start_time, end_time, duration, description, day]
        if not any(field is not None for field in updatable):
            return {"success": False, "error": "No fields provided to update"}

        # Update fields
        if user_id is not None:
            entry["user_id"] = user_id
        if project_id is not None:
            entry["project_id"] = project_id
        if organization_id is not None:
            entry["organization_id"] = organization_id
        if start_time is not None:
            entry["start_time"] = start_time
        if end_time is not None:
            entry["end_time"] = end_time
        if duration is not None:
            entry["duration"] = duration
        if description is not None:
            entry["description"] = description
        if day is not None:
            entry["day"] = day

        self.time_entries[time_entry_id] = entry

        return {"success": True, "message": "Time entry updated successfully."}

    def add_user(self, user_id: str, name: str, email: str, organization_id: str, role: str) -> dict:
        """
        Add a new user to an organization.

        Args:
            user_id (str): Unique user identifier.
            name (str): User's name.
            email (str): User's email (must be unique).
            organization_id (str): The organization to which the user will belong.
            role (str): The user's role.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User added", "user_id": <user_id> }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - organization_id must exist in the system.
            - user_id must be unique.
            - email must be unique.
            - Users belong to a single organization.
        """
        # Check organization exists
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        # Check user_id uniqueness
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists" }

        # Check email uniqueness
        for u in self.users.values():
            if u['email'] == email:
                return { "success": False, "error": "Email already exists" }

        # Add user
        self.users[user_id] = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "organization_id": organization_id,
            "role": role
        }

        return { "success": True, "message": "User added", "user_id": user_id }

    def add_project(self, project_id: str, name: str, organization_id: str) -> dict:
        """
        Add a new project to an organization.

        Args:
            project_id (str): Unique identifier for the new project.
            name (str): Name of the project.
            organization_id (str): Identifier of the organization to which this project belongs.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Project added successfully."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason (e.g. organization does not exist, project_id exists)
                    }

        Constraints:
            - organization_id must exist in the system.
            - project_id must be unique.
            - Projects must belong to a single organization.
        """
        # Check if organization_id exists
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
    
        # Check if project_id already exists
        if project_id in self.projects:
            return { "success": False, "error": "Project ID already exists." }
    
        # Optional: check for duplicate project name within the organization
        for p in self.projects.values():
            if p['organization_id'] == organization_id and p['name'] == name:
                return { "success": False, "error": "Project name already exists for this organization." }

        # Add project
        project_info: ProjectInfo = {
            "project_id": project_id,
            "name": name,
            "organization_id": organization_id
        }
        self.projects[project_id] = project_info
        return { "success": True, "message": "Project added successfully." }

    def remove_time_entry(self, time_entry_id: str) -> dict:
        """
        Delete a time entry from the system.

        Args:
            time_entry_id (str): Unique identifier of the time entry to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Time entry <id> removed."
            }
            or
            {
                "success": False,
                "error": "Time entry not found."
            }

        Constraints:
            - The time entry must exist in the system.
        """
        if time_entry_id not in self.time_entries:
            return { "success": False, "error": "Time entry not found." }
    
        del self.time_entries[time_entry_id]
        return { "success": True, "message": f"Time entry {time_entry_id} removed." }

    def remove_project(self, project_id: str) -> dict:
        """
        Delete a project (by project_id) from the system.

        Args:
            project_id (str): The unique identifier of the project to delete.

        Returns:
            dict: On success:
                { "success": True, "message": "Project <project_id> deleted." }
            On failure:
                { "success": False, "error": "<reason>" }

        Constraints:
            - Project must exist in the system.
            - All time entries associated with this project must be deleted or reassigned first;
              otherwise, deletion is blocked to prevent orphaned time entries.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}

        # Check for linked time entries
        has_linked_entries = any(
            te_info["project_id"] == project_id for te_info in self.time_entries.values()
        )
        if has_linked_entries:
            return {
                "success": False,
                "error": "Cannot delete project; time entries are associated with this project."
            }

        # Delete the project
        del self.projects[project_id]

        return {
            "success": True,
            "message": f"Project {project_id} deleted."
        }

    def remove_user(self, user_id: str) -> dict:
        """
        Remove a user from the system by user_id.

        Args:
            user_id (str): The unique identifier of the user to remove.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "User <user_id> removed."}
                - On failure (user not found / has associated time entries):
                    {"success": False, "error": "..."}
    
        Constraints:
            - User must exist.
            - User cannot be removed if there are time entries associated with them,
              to preserve referential integrity (as each time entry must be associated with a valid user).
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        # Check for associated time entries
        for te in self.time_entries.values():
            if te["user_id"] == user_id:
                return {
                    "success": False,
                    "error": f"Cannot remove user; time entries are associated with user_id {user_id}."
                }
    
        # Safe to remove
        del self.users[user_id]
        return {"success": True, "message": f"User {user_id} removed."}


class ProfessionalTimeTrackingReportingSystem(BaseEnv):
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
            id_fields = {
                "organizations": "organization_id",
                "projects": "project_id",
                "users": "user_id",
                "time_entries": "time_entry_id",
            }
            if key in id_fields and isinstance(copied, dict):
                id_field = id_fields[key]
                copied = {
                    item.get(id_field, item_key): item
                    for item_key, item in copied.items()
                    if isinstance(item, dict)
                }
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

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_organizations_by_type(self, **kwargs):
        return self._call_inner_tool('list_organizations_by_type', kwargs)

    def get_projects_by_organization(self, **kwargs):
        return self._call_inner_tool('get_projects_by_organization', kwargs)

    def get_users_by_organization(self, **kwargs):
        return self._call_inner_tool('get_users_by_organization', kwargs)

    def get_time_entries_by_organization(self, **kwargs):
        return self._call_inner_tool('get_time_entries_by_organization', kwargs)

    def get_time_entries_by_project(self, **kwargs):
        return self._call_inner_tool('get_time_entries_by_project', kwargs)

    def get_time_entries_by_user(self, **kwargs):
        return self._call_inner_tool('get_time_entries_by_user', kwargs)

    def filter_time_entries(self, **kwargs):
        return self._call_inner_tool('filter_time_entries', kwargs)

    def aggregate_time_by_user(self, **kwargs):
        return self._call_inner_tool('aggregate_time_by_user', kwargs)

    def aggregate_time_by_project(self, **kwargs):
        return self._call_inner_tool('aggregate_time_by_project', kwargs)

    def export_report(self, **kwargs):
        return self._call_inner_tool('export_report', kwargs)

    def add_time_entry(self, **kwargs):
        return self._call_inner_tool('add_time_entry', kwargs)

    def update_time_entry(self, **kwargs):
        return self._call_inner_tool('update_time_entry', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def add_project(self, **kwargs):
        return self._call_inner_tool('add_project', kwargs)

    def remove_time_entry(self, **kwargs):
        return self._call_inner_tool('remove_time_entry', kwargs)

    def remove_project(self, **kwargs):
        return self._call_inner_tool('remove_project', kwargs)

    def remove_user(self, **kwargs):
        return self._call_inner_tool('remove_user', kwargs)
