# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# Represents a financial security
class SecurityInfo(TypedDict):
    security_id: str
    security_type: str
    legal_structure: str
    name: str
    status: str
    performance_data: str
    compliance_info: str

# Represents a person involved in the management or administration of a security
class PersonnelInfo(TypedDict):
    personnel_id: str
    name: str
    title: str
    contact_info: str
    status: str  # 'sta' assumed to be 'status'

# Represents a team responsible for managing securities
class ManagementTeamInfo(TypedDict):
    team_id: str    # 'am_id' corrected to 'team_id'
    name: str
    description: str

# Represents personnel assignments to securities
class SecurityPersonnelAssignmentInfo(TypedDict):
    security_id: str
    personnel_id: str
    role: str
    start_date: str
    end_date: str   # 'end_da' corrected to 'end_date'

# Represents an administrative entity associated with certain securities (especially funds)
class FundAdministratorInfo(TypedDict):
    admin_id: str
    name: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Securities: {security_id: SecurityInfo}
        self.securities: Dict[str, SecurityInfo] = {}

        # Personnel: {personnel_id: PersonnelInfo}
        self.personnel: Dict[str, PersonnelInfo] = {}

        # Management Teams: {team_id: ManagementTeamInfo}
        self.management_teams: Dict[str, ManagementTeamInfo] = {}

        # Security-Personnel assignments (association list)
        self.security_personnel_assignments: List[SecurityPersonnelAssignmentInfo] = []

        # Fund Administrators: {admin_id: FundAdministratorInfo}
        self.fund_administrators: Dict[str, FundAdministratorInfo] = {}

        # --- Constraints (to be enforced in business logic later) ---
        # - Each security must have a unique security_id and a defined security_type.
        # - Every SecurityPersonnelAssignment must reference valid security_id and personnel_id.
        # - Personnel assignments to securities may have required or allowable roles depending on the security_type.
        # - Orphaned personnel or security records (with no associations) should be cleaned up or flagged.
        # - Legal and compliance information must be kept up to date for all securities.

    def get_security_by_id(self, security_id: str) -> dict:
        """
        Retrieve full information for a given security_id.

        Args:
            security_id (str): Unique identifier for the security.

        Returns:
            dict: 
                On success: { "success": True, "data": SecurityInfo }
                On error: { "success": False, "error": <reason str> }
    
        Constraints:
            - The security_id must exist in the system.
        """
        if security_id not in self.securities:
            return { "success": False, "error": f"Security with security_id '{security_id}' does not exist." }
        return { "success": True, "data": self.securities[security_id] }

    def list_securities_by_type(self, security_type: str) -> dict:
        """
        List all securities filtered by the specified security_type.

        Args:
            security_type (str): Security type to filter results (e.g., 'ETF', 'fund', etc.).

        Returns:
            dict: {
                "success": True,
                "data": List[SecurityInfo]  # May be empty if no matches
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - security_type must be a non-empty string.
        """
        if not isinstance(security_type, str) or not security_type.strip():
            return { "success": False, "error": "Invalid or missing security_type parameter" }
    
        filtered = [
            security for security in self.securities.values()
            if security.get("security_type") == security_type
        ]
        return { "success": True, "data": filtered }

    def get_security_personnel_assignments(self, security_id: str) -> dict:
        """
        Retrieve all personnel assignment records for the specified security_id.

        Args:
            security_id (str): The ID of the security for which to retrieve personnel assignments.

        Returns:
            dict:
              - On success:
                  { "success": True, "data": List[SecurityPersonnelAssignmentInfo] }
                  (list may be empty if no assignments)
              - On failure:
                  { "success": False, "error": str }
                  (if the security_id does not exist)

        Constraints:
            - security_id must exist in self.securities.
        """
        if security_id not in self.securities:
            return {"success": False, "error": "Security does not exist"}

        result = [
            assignment
            for assignment in self.security_personnel_assignments
            if assignment["security_id"] == security_id
        ]
        return {"success": True, "data": result}

    def get_personnel_by_id(self, personnel_id: str) -> dict:
        """
        Retrieve the complete personnel information for the given personnel_id.

        Args:
            personnel_id (str): The unique identifier of the personnel to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": PersonnelInfo
            }
            or
            {
                "success": False,
                "error": "Personnel not found"
            }

        Constraints:
            - personnel_id must exist in the personnel registry (self.personnel)
        """
        if personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel not found"}

        return {"success": True, "data": self.personnel[personnel_id]}

    def list_all_personnel(self) -> dict:
        """
        List all personnel in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PersonnelInfo]   # List of all personnel entries (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.personnel.values())
        }

    def get_personnel_for_security(self, security_id: str) -> dict:
        """
        Given a security_id, return the details of all associated personnel, enriched with their
        role and assignment period.

        Args:
            security_id (str): The ID of the security to query.

        Returns:
            dict:
                success: True if the security exists (always returns, even if no personnel associated).
                data: List of dicts - each has:
                    - personnel_info: PersonnelInfo
                    - role: str
                    - start_date: str
                    - end_date: str
                OR
                success: False, error: <reason> if the security does not exist.

        Constraints:
            - Security must exist in the system.
            - Only returns assignments where the personnel reference is valid.
        """
        if security_id not in self.securities:
            return { "success": False, "error": "Security not found" }

        results = []
        for assignment in self.security_personnel_assignments:
            if assignment["security_id"] == security_id:
                personnel_id = assignment["personnel_id"]
                personnel_info = self.personnel.get(personnel_id)
                if personnel_info:
                    results.append({
                        "personnel_info": personnel_info,
                        "role": assignment["role"],
                        "start_date": assignment["start_date"],
                        "end_date": assignment["end_date"]
                    })

        return { "success": True, "data": results }

    def get_management_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve management team info by its team_id.

        Args:
            team_id (str): The unique identifier for the management team.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": ManagementTeamInfo  # the info dictionary for the team
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Management team not found"
                    }
        Constraints:
            - The team_id must exist in the system to return a successful result.
            - No side effect; read-only query.
        """
        if team_id in self.management_teams:
            return {"success": True, "data": self.management_teams[team_id]}
        else:
            return {"success": False, "error": "Management team not found"}

    def get_fund_administrator_by_id(self, admin_id: str) -> dict:
        """
        Retrieve fund administrator info by admin_id.

        Args:
            admin_id (str): Unique identifier for the fund administrator.

        Returns:
            dict:
                On success: { "success": True, "data": FundAdministratorInfo }
                On failure: { "success": False, "error": "Fund administrator not found" }

        Constraints:
            - The supplied admin_id must be present in the fund administrators registry.
        """
        if admin_id not in self.fund_administrators:
            return { "success": False, "error": "Fund administrator not found" }
        return { "success": True, "data": self.fund_administrators[admin_id] }

    def get_orphaned_personnel(self) -> dict:
        """
        List all personnel not currently assigned to any active securities.

        Returns:
            dict: {
                "success": True,
                "data": List[PersonnelInfo],  # List of orphaned personnel
            }

        Constraints:
            - Only assignments to securities whose status is 'active' count as 'assigned'.
            - If a personnel is not assigned to any 'active' security, they are considered orphaned.
        """
        # Build set of personnel_ids assigned to at least one active security
        assigned_personnel_ids = set()
        for assignment in self.security_personnel_assignments:
            sec_id = assignment["security_id"]
            if sec_id in self.securities and self.securities[sec_id]["status"] == "active":
                assigned_personnel_ids.add(assignment["personnel_id"])

        orphaned_personnel = [
            personnel_info
            for pid, personnel_info in self.personnel.items()
            if pid not in assigned_personnel_ids
        ]

        return { "success": True, "data": orphaned_personnel }

    def get_orphaned_securities(self) -> dict:
        """
        List all securities (SecurityInfo) that do not have any personnel assigned (i.e., no assignments exist in security_personnel_assignments).

        Returns:
            dict: {
                "success": True,
                "data": List[SecurityInfo],  # All securities with no assignments
            }
        Notes:
            - If there are no securities, data will be an empty list.
            - If there are no assignments at all, all securities are orphaned.
        """
        # Get all security_ids with any assignment
        assigned_security_ids = set(
            assignment["security_id"] for assignment in self.security_personnel_assignments
        )

        # Orphaned = those security_ids not in assignments at all
        orphaned_securities = [
            security_info
            for security_id, security_info in self.securities.items()
            if security_id not in assigned_security_ids
        ]

        return {
            "success": True,
            "data": orphaned_securities
        }

    def get_compliance_info_for_security(self, security_id: str) -> dict:
        """
        Query the legal and compliance information for a specific security.

        Args:
            security_id (str): The unique identifier of the security.

        Returns:
            dict: 
              - If found: {
                    "success": True,
                    "data": {
                        "security_id": str,
                        "compliance_info": str,
                        "legal_structure": str
                    }
                }
              - If not found: {
                    "success": False,
                    "error": "Security not found"
                }

        Constraints:
            - The security_id must exist in the system.
        """
        security = self.securities.get(security_id)
        if not security:
            return {"success": False, "error": "Security not found"}

        return {
            "success": True,
            "data": {
                "security_id": security_id,
                "compliance_info": security.get("compliance_info", ""),
                "legal_structure": security.get("legal_structure", "")
            }
        }

    def add_security(
        self,
        security_id: str,
        security_type: str,
        legal_structure: str,
        name: str,
        status: str,
        performance_data: str,
        compliance_info: str
    ) -> dict:
        """
        Add a new security with required metadata to the system.

        Args:
            security_id (str): Unique identifier for the security.
            security_type (str): Type of the security (e.g., stock, fund, ETF, etc.).
            legal_structure (str): Legal structure of the security.
            name (str): Name of the security.
            status (str): Status (e.g., active, inactive).
            performance_data (str): Performance metrics or description.
            compliance_info (str): Compliance or legal notes.

        Returns:
            dict: {
                "success": True,
                "message": "Security <security_id> added."
            }
            or
            {
                "success": False,
                "error": str  # Description of the failure (e.g., duplicate ID, missing fields)
            }

        Constraints:
            - security_id must be unique in the system.
            - security_type must be provided (not empty).
        """

        # Check that security_id is unique
        if not security_id:
            return { "success": False, "error": "security_id must be provided" }
        if security_id in self.securities:
            return { "success": False, "error": f"Security with id {security_id} already exists" }

        # Check that security_type is provided and non-empty
        if not security_type:
            return { "success": False, "error": "security_type must be provided" }

        # Ensure mandatory fields are provided
        required_fields = [legal_structure, name, status]
        if any(f is None or f == "" for f in required_fields):
            return { "success": False, "error": "Missing required fields for security creation" }

        # Add the security
        self.securities[security_id] = {
            "security_id": security_id,
            "security_type": security_type,
            "legal_structure": legal_structure,
            "name": name,
            "status": status,
            "performance_data": performance_data,
            "compliance_info": compliance_info
        }

        return { "success": True, "message": f"Security {security_id} added." }

    def update_security_info(self, security_id: str, update_fields: dict) -> dict:
        """
        Modify data for an existing security.

        Args:
            security_id (str): The unique identifier for the security to update.
            update_fields (dict): Which fields to update and their new values. 
                Allowed fields: security_type, legal_structure, name, status, performance_data, compliance_info.

        Returns:
            dict: {
                "success": True,
                "message": "Security [security_id] info updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only permitted fields may be updated.
            - Security must exist.
            - Compliance/legal info must stay up to date (enforced by acceptance of valid updates).
        """
        # Allowed updatable fields
        allowed_fields = set([
            "security_type",
            "legal_structure",
            "name",
            "status",
            "performance_data",
            "compliance_info"
        ])
        if security_id not in self.securities:
            return {"success": False, "error": "Security does not exist"}
        if not update_fields:
            return {"success": False, "error": "No fields provided for update"}
        for field in update_fields:
            if field not in allowed_fields:
                return {"success": False, "error": f"Invalid field for update: {field}"}
        # Update the security's attributes
        for field, value in update_fields.items():
            self.securities[security_id][field] = value
        return {"success": True, "message": f"Security {security_id} info updated successfully"}

    def delete_security(self, security_id: str) -> dict:
        """
        Remove a security identified by security_id from the system.

        This deletes the security and all SecurityPersonnelAssignment associations with this security.
        Personnel or management teams left without any assignments are NOT deleted here.

        Args:
            security_id (str): The ID of the security to be deleted.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Security <security_id> deleted and associations cleaned up."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Security not found."
                    }

        Constraints:
            - Security must exist.
            - All SecurityPersonnelAssignments referencing this security are also removed.
            - Does NOT automatically delete orphaned personnel or management teams (handled separately).
        """
        if security_id not in self.securities:
            return { "success": False, "error": "Security not found." }

        # Remove the security
        del self.securities[security_id]

        # Remove associated personnel assignments
        original_assignment_count = len(self.security_personnel_assignments)
        self.security_personnel_assignments = [
            a for a in self.security_personnel_assignments if a["security_id"] != security_id
        ]
        removed_count = original_assignment_count - len(self.security_personnel_assignments)

        return {
            "success": True,
            "message": f"Security {security_id} deleted and {removed_count} assignment(s) cleaned up."
        }

    def add_personnel(
        self,
        personnel_id: str,
        name: str,
        title: str,
        contact_info: str,
        status: str
    ) -> dict:
        """
        Adds a new personnel record to the system.

        Args:
            personnel_id (str): Unique identifier for the personnel.
            name (str): Name of the personnel.
            title (str): Job title.
            contact_info (str): Contact information.
            status (str): Status string (e.g., 'Active', 'Inactive').

        Returns:
            dict:
                - On success: { "success": True, "message": "Personnel record added." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - personnel_id must be unique (not already present in personnel dict).
        """
        if personnel_id in self.personnel:
            return { "success": False, "error": "Personnel with this ID already exists." }

        self.personnel[personnel_id] = {
            "personnel_id": personnel_id,
            "name": name,
            "title": title,
            "contact_info": contact_info,
            "status": status
        }
        return { "success": True, "message": "Personnel record added." }

    def update_personnel_info(self, personnel_id: str, name: str = None, title: str = None, contact_info: str = None, status: str = None) -> dict:
        """
        Update the information for a personnel entry.

        Args:
            personnel_id (str): The ID of the personnel whose info to update.
            name (str, optional): New name for the personnel.
            title (str, optional): New title for the personnel.
            contact_info (str, optional): New contact info.
            status (str, optional): New status for the personnel.

        Returns:
            dict:
                Success: { "success": True, "message": "Personnel information updated." }
                Failure: { "success": False, "error": "Personnel not found." }

        Constraints:
            - personnel_id must exist in the personnel dictionary.
            - Only defined fields ('name', 'title', 'contact_info', 'status') may be updated.
            - The 'personnel_id' itself cannot be changed.
        """
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel not found." }

        update_fields = {
            "name": name,
            "title": title,
            "contact_info": contact_info,
            "status": status
        }

        personnel_info = self.personnel[personnel_id]
        for key, value in update_fields.items():
            if value is not None:
                personnel_info[key] = value

        return { "success": True, "message": "Personnel information updated." }

    def delete_personnel(self, personnel_id: str) -> dict:
        """
        Remove a personnel record and all of their associations with securities.

        Args:
            personnel_id (str): The unique identifier of the personnel to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Personnel record deleted and associations removed."
            }
            or
            {
                "success": False,
                "error": "Personnel record does not exist."
            }

        Constraints:
            - The personnel must exist.
            - All SecurityPersonnelAssignment records referencing this personnel must be removed.
        """
        if personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel record does not exist."}

        # Remove all SecurityPersonnelAssignmentInfo referencing this personnel_id
        before_count = len(self.security_personnel_assignments)
        self.security_personnel_assignments = [
            assignment for assignment in self.security_personnel_assignments
            if assignment["personnel_id"] != personnel_id
        ]
        after_count = len(self.security_personnel_assignments)
        # (Removal of associations is always a success, regardless of whether any existed.)

        # Remove from personnel
        del self.personnel[personnel_id]

        return {
            "success": True,
            "message": "Personnel record deleted and associations removed."
        }

    def add_management_team(self, team_id: str, name: str, description: str) -> dict:
        """
        Add a new management team to the system.

        Args:
            team_id (str): Unique identifier for the management team.
            name (str): Name of the management team.
            description (str): Description of the management team.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Management team <team_id> added." }
                - On failure: { "success": False, "error": "<error_reason>" }

        Constraints:
            - The team_id must be unique within the system.
            - team_id, name, and description should be non-empty strings.
        """
        if not team_id or not name or not description:
            return { "success": False, "error": "team_id, name, and description are required and must be non-empty." }
        if team_id in self.management_teams:
            return { "success": False, "error": f"Management team with id '{team_id}' already exists." }
    
        new_team: ManagementTeamInfo = {
            "team_id": team_id,
            "name": name,
            "description": description
        }
        self.management_teams[team_id] = new_team
        return { "success": True, "message": f"Management team '{team_id}' added." }

    def assign_personnel_to_security(
        self,
        security_id: str,
        personnel_id: str,
        role: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Create or update a SecurityPersonnelAssignment for a given security and personnel.

        Args:
            security_id (str): Unique identifier of the security.
            personnel_id (str): Unique identifier of the personnel.
            role (str): The role of personnel in relation to the security.
            start_date (str): Start date of assignment (format assumed ISO date string).
            end_date (str): End date of assignment (format assumed ISO date string).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Personnel assigned to security successfully." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - security_id must exist in self.securities.
            - personnel_id must exist in self.personnel.
            - If an assignment with this (security_id, personnel_id) exists, it is updated; otherwise, created.

        Notes:
            - If role validity per security_type is to be enforced, it is not done here due to lack of mapping/business logic.
            - Date value/ordering are not validated (could be added if desired).
        """
        if security_id not in self.securities:
            return { "success": False, "error": "Security ID does not exist." }
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel ID does not exist." }

        found = False
        for assignment in self.security_personnel_assignments:
            if assignment["security_id"] == security_id and assignment["personnel_id"] == personnel_id:
                # Update existing assignment
                assignment["role"] = role
                assignment["start_date"] = start_date
                assignment["end_date"] = end_date
                found = True
                break

        if not found:
            # Create new assignment
            self.security_personnel_assignments.append({
                "security_id": security_id,
                "personnel_id": personnel_id,
                "role": role,
                "start_date": start_date,
                "end_date": end_date
            })

        return { "success": True, "message": "Personnel assigned to security successfully." }

    def unassign_personnel_from_security(
        self,
        security_id: str,
        personnel_id: str,
        end_date: str = "",
        set_end_date: bool = True
    ) -> dict:
        """
        Unassign (remove or logically deactivate) a SecurityPersonnelAssignment for the given security_id and personnel_id.

        Args:
            security_id (str): The ID of the security from which personnel should be unassigned.
            personnel_id (str): The ID of the personnel to unassign.
            end_date (str, optional): The end date string to set when logically ending assignment (if set_end_date=True).
                                      Default "" (means use today's date, or leave blank depending on policy).
            set_end_date (bool, optional): Whether to set the end_date (logical unassign) or to remove the assignment (physical removal).
                                           Default True (set end_date).

        Returns:
            dict:
                - On success: { "success": True, "message": str }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Assignment must exist with given security_id and personnel_id.
            - Assignment must reference valid security_id and personnel_id.
            - If set_end_date=True, sets the end_date (if not already set).
            - If set_end_date=False, completely removes the assignment.

        Edge Cases:
            - If no matching assignment exists, returns success: False.
            - If multiple assignments exist, all are processed.
        """
        # Validate if security and personnel exist
        if security_id not in self.securities:
            return {"success": False, "error": f"Security with id '{security_id}' does not exist."}
        if personnel_id not in self.personnel:
            return {"success": False, "error": f"Personnel with id '{personnel_id}' does not exist."}

        found = False
        updated_count = 0

        if set_end_date:
            for assignment in self.security_personnel_assignments:
                if assignment["security_id"] == security_id and assignment["personnel_id"] == personnel_id:
                    found = True
                    if assignment.get("end_date"):
                        continue  # Already ended
                    assignment["end_date"] = end_date if end_date else "TODAY"  # Or use a real date util if available
                    updated_count += 1
            if not found:
                return {"success": False, "error": "No active assignment found for the given security and personnel."}
            if updated_count == 0:
                return {"success": False, "error": "Assignment(s) already ended previously."}
            return {
                "success": True,
                "message": f"Set end_date for {updated_count} assignment(s) between security '{security_id}' and personnel '{personnel_id}'."
            }
        else:
            # Remove all assignments (active or not) for this pair
            new_assignments = []
            removed_count = 0
            for assignment in self.security_personnel_assignments:
                if assignment["security_id"] == security_id and assignment["personnel_id"] == personnel_id:
                    found = True
                    removed_count += 1
                    continue  # Skip, i.e. remove
                new_assignments.append(assignment)
            if not found:
                return {"success": False, "error": "No assignment(s) found for the given security and personnel."}
            self.security_personnel_assignments = new_assignments
            return {
                "success": True,
                "message": f"Removed {removed_count} assignment(s) between security '{security_id}' and personnel '{personnel_id}'."
            }

    def clean_orphaned_records(self) -> dict:
        """
        Detect and remove orphaned securities or personnel (i.e., those with no associations).
        An orphaned Personnel is one whose personnel_id does not appear in any SecurityPersonnelAssignment.
        An orphaned Security is one whose security_id does not appear in any SecurityPersonnelAssignment.
        This operation removes such records from the system.

        Returns:
            dict: {
                "success": True,
                "message": "Number of orphaned records removed/flagged: ...",
                "details": {
                    "orphaned_personnel_removed": List[str],  # list of personnel_ids removed
                    "orphaned_securities_removed": List[str],  # list of security_ids removed
                }
            }
            or
            {
                "success": False,
                "error": <str>
            }
        """
        try:
            # Collect all referenced personnel and securities from assignments
            assigned_personnel = set(assignment['personnel_id'] for assignment in self.security_personnel_assignments)
            assigned_securities = set(assignment['security_id'] for assignment in self.security_personnel_assignments)

            orphaned_personnel = [pid for pid in self.personnel if pid not in assigned_personnel]
            orphaned_securities = [sid for sid in self.securities if sid not in assigned_securities]

            # Remove orphaned personnel
            for pid in orphaned_personnel:
                del self.personnel[pid]

            # Remove orphaned securities
            for sid in orphaned_securities:
                del self.securities[sid]

            message = (
                f"Orphaned records removed: {len(orphaned_personnel)} personnel, "
                f"{len(orphaned_securities)} securities."
            )
            return {
                "success": True,
                "message": message,
                "details": {
                    "orphaned_personnel_removed": orphaned_personnel,
                    "orphaned_securities_removed": orphaned_securities
                }
            }
        except Exception as e:
            # Should not happen, but in case of unexpected error
            return {
                "success": False,
                "error": f"Internal error during orphaned record cleanup: {str(e)}"
            }

    def update_compliance_info(self, security_id: str, new_compliance_info: str) -> dict:
        """
        Update or refresh compliance/legal data for a specific security.

        Args:
            security_id (str): The identifier of the security to update.
            new_compliance_info (str): The new compliance or legal information to store.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Compliance information updated for security <security_id>." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Security with security_id must exist.
            - new_compliance_info must be a non-empty string.
        """
        if security_id not in self.securities:
            return { "success": False, "error": "Security ID not found." }
        if not isinstance(new_compliance_info, str) or new_compliance_info.strip() == "":
            return { "success": False, "error": "Invalid compliance information." }
    
        self.securities[security_id]["compliance_info"] = new_compliance_info
        return { 
            "success": True, 
            "message": f"Compliance information updated for security {security_id}."
        }

    def add_fund_administrator(self, admin_id: str, name: str, contact_info: str) -> dict:
        """
        Insert a new fund administrator record.

        Args:
            admin_id (str): Unique identifier for the fund administrator.
            name (str): Name of the fund administrator.
            contact_info (str): Contact details for the administrator.

        Returns:
            dict: {
                "success": True,
                "message": "Fund administrator added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - admin_id must be unique.
            - No field may be empty.
        """
        if not admin_id or not name or not contact_info:
            return { "success": False, "error": "All fields (admin_id, name, contact_info) must be provided and non-empty." }

        if admin_id in self.fund_administrators:
            return { "success": False, "error": "Fund administrator with this ID already exists." }

        self.fund_administrators[admin_id] = {
            "admin_id": admin_id,
            "name": name,
            "contact_info": contact_info
        }

        return { "success": True, "message": "Fund administrator added successfully." }

    def update_fund_administrator_info(
        self,
        admin_id: str,
        name: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Update attributes for a fund administrator.

        Args:
            admin_id (str): The ID of the fund administrator to update.
            name (str, optional): The new name for the fund administrator.
            contact_info (str, optional): The new contact information.

        Returns:
            dict: 
                On success: { "success": True, "message": "Fund administrator info updated successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The admin_id must already exist.
            - At least one of 'name' or 'contact_info' must be provided for update.
        """
        if admin_id not in self.fund_administrators:
            return { "success": False, "error": "Fund administrator not found" }

        if name is None and contact_info is None:
            return { "success": False, "error": "No update fields provided" }

        admin = self.fund_administrators[admin_id]
        updated = False

        if name is not None:
            admin["name"] = name
            updated = True
        if contact_info is not None:
            admin["contact_info"] = contact_info
            updated = True

        if updated:
            self.fund_administrators[admin_id] = admin
            return { "success": True, "message": "Fund administrator info updated successfully" }
        else:
            return { "success": False, "error": "No valid fields to update" }

    def delete_fund_administrator(self, admin_id: str) -> dict:
        """
        Remove a fund administrator record from the system.

        Args:
            admin_id (str): Unique identifier of the fund administrator to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Fund administrator <admin_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Fund administrator not found."
            }

        Constraints:
            - The provided admin_id must exist in the system.
            - No explicit check for associations is required per the provided structure.
        """
        if admin_id not in self.fund_administrators:
            return { "success": False, "error": "Fund administrator not found." }
    
        del self.fund_administrators[admin_id]
        return { "success": True, "message": f"Fund administrator {admin_id} deleted." }


class FinancialSecuritiesInformationManagementSystem(BaseEnv):
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

    def get_security_by_id(self, **kwargs):
        return self._call_inner_tool('get_security_by_id', kwargs)

    def list_securities_by_type(self, **kwargs):
        return self._call_inner_tool('list_securities_by_type', kwargs)

    def get_security_personnel_assignments(self, **kwargs):
        return self._call_inner_tool('get_security_personnel_assignments', kwargs)

    def get_personnel_by_id(self, **kwargs):
        return self._call_inner_tool('get_personnel_by_id', kwargs)

    def list_all_personnel(self, **kwargs):
        return self._call_inner_tool('list_all_personnel', kwargs)

    def get_personnel_for_security(self, **kwargs):
        return self._call_inner_tool('get_personnel_for_security', kwargs)

    def get_management_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_management_team_by_id', kwargs)

    def get_fund_administrator_by_id(self, **kwargs):
        return self._call_inner_tool('get_fund_administrator_by_id', kwargs)

    def get_orphaned_personnel(self, **kwargs):
        return self._call_inner_tool('get_orphaned_personnel', kwargs)

    def get_orphaned_securities(self, **kwargs):
        return self._call_inner_tool('get_orphaned_securities', kwargs)

    def get_compliance_info_for_security(self, **kwargs):
        return self._call_inner_tool('get_compliance_info_for_security', kwargs)

    def add_security(self, **kwargs):
        return self._call_inner_tool('add_security', kwargs)

    def update_security_info(self, **kwargs):
        return self._call_inner_tool('update_security_info', kwargs)

    def delete_security(self, **kwargs):
        return self._call_inner_tool('delete_security', kwargs)

    def add_personnel(self, **kwargs):
        return self._call_inner_tool('add_personnel', kwargs)

    def update_personnel_info(self, **kwargs):
        return self._call_inner_tool('update_personnel_info', kwargs)

    def delete_personnel(self, **kwargs):
        return self._call_inner_tool('delete_personnel', kwargs)

    def add_management_team(self, **kwargs):
        return self._call_inner_tool('add_management_team', kwargs)

    def assign_personnel_to_security(self, **kwargs):
        return self._call_inner_tool('assign_personnel_to_security', kwargs)

    def unassign_personnel_from_security(self, **kwargs):
        return self._call_inner_tool('unassign_personnel_from_security', kwargs)

    def clean_orphaned_records(self, **kwargs):
        return self._call_inner_tool('clean_orphaned_records', kwargs)

    def update_compliance_info(self, **kwargs):
        return self._call_inner_tool('update_compliance_info', kwargs)

    def add_fund_administrator(self, **kwargs):
        return self._call_inner_tool('add_fund_administrator', kwargs)

    def update_fund_administrator_info(self, **kwargs):
        return self._call_inner_tool('update_fund_administrator_info', kwargs)

    def delete_fund_administrator(self, **kwargs):
        return self._call_inner_tool('delete_fund_administrator', kwargs)

