# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Any, Dict, List, TypedDict

from .BaseEnv import BaseEnv



class ProjectInfo(TypedDict):
    project_id: str
    title: str
    start_date: str
    end_date: str
    status: str
    description: str

class TeamMemberInfo(TypedDict):
    member_id: str
    name: str
    roles: List[str]        # Qualified roles
    contact_info: str
    availability: str       # Could be schedule string or range

class ProjectRoleAssignmentInfo(TypedDict):
    assignment_id: str
    project_id: str
    member_id: str
    role: str
    assignment_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Team members: {member_id: TeamMemberInfo}
        self.team_members: Dict[str, TeamMemberInfo] = {}

        # ProjectRoleAssignments: {assignment_id: ProjectRoleAssignmentInfo}
        self.role_assignments: Dict[str, ProjectRoleAssignmentInfo] = {}

        # Constraints:
        # - Each team member can only be assigned to roles for which they are qualified.
        # - A project must have at least one team member assigned to begin.
        # - No duplicate role assignments for the same team member within a single project.
        # - Project start dates cannot overlap for the same team member if their availability is limited.

    @staticmethod
    def _has_full_availability(availability: str) -> bool:
        return isinstance(availability, str) and availability.strip().lower() == "full"

    def get_project_by_title(self, title: str) -> dict:
        """
        Retrieve details about a project using its title.

        Args:
            title (str): The exact title of the project to look up.

        Returns:
            dict: If found, {
                "success": True,
                "data": ProjectInfo
            }
            else,
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Titles are assumed to be unique, but if duplicates exist, the first match is returned.
        """
        for project in self.projects.values():
            if project['title'] == title:
                return {"success": True, "data": project}
        return {"success": False, "error": "Project not found for given title"}

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve details of a project using its unique project_id.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict: 
                - On success: { "success": True, "data": ProjectInfo }
                - On failure: { "success": False, "error": "Project with given project_id does not exist" }

        Constraints:
            - The project with the specified ID must exist in the system.
        """
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Project with given project_id does not exist" }
        return { "success": True, "data": project }

    def list_all_projects(self) -> dict:
        """
        List all animation projects currently tracked in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]  # List of all stored animation projects (can be empty)
            }
        """
        projects_list = list(self.projects.values())
        return { "success": True, "data": projects_list }

    def get_projects_for_member(self, member_id: str) -> dict:
        """
        Fetch all projects (limited to project_id, title, start_date, end_date) in which the specified team member participates.

        Args:
            member_id (str): The ID of the team member.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict: {project_id, title, start_date, end_date}
            }
            or
            {
                "success": False,
                "error": "Team member does not exist"
            }
        Constraints:
            - The member_id must exist in the system.
        """
        if member_id not in self.team_members:
            return {"success": False, "error": "Team member does not exist"}

        # Find all assignment records for this member
        project_ids = set()
        for assignment in self.role_assignments.values():
            if assignment["member_id"] == member_id:
                project_ids.add(assignment["project_id"])

        # Compile project info for each found project
        result = []
        for pid in project_ids:
            project = self.projects.get(pid)
            if project:
                result.append({
                    "project_id": project["project_id"],
                    "title": project["title"],
                    "start_date": project["start_date"],
                    "end_date": project["end_date"]
                })

        return {"success": True, "data": result}

    def get_assignments_for_project(self, project_id: str) -> dict:
        """
        Retrieve all role assignments (member, role) for a specified project.

        Args:
            project_id (str): ID of the project whose role assignments are to be retrieved.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProjectRoleAssignmentInfo]  # (May be empty if no assignments)
                }
                or
                {
                    "success": False,
                    "error": str  # e.g., "Project does not exist"
                }

        Constraints:
            - The specified project_id must exist in the system.
        """

        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        results = [
            assignment_info
            for assignment_info in self.role_assignments.values()
            if assignment_info["project_id"] == project_id
        ]

        return { "success": True, "data": results }

    def get_assignments_for_member(self, member_id: str) -> dict:
        """
        Retrieve all role assignments (ProjectRoleAssignmentInfo) associated with the given team member.

        Args:
            member_id (str): The unique ID of the team member.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[ProjectRoleAssignmentInfo]  # List may be empty if member has no assignments.
                  }
                - On error: {
                      "success": False,
                      "error": str  # Reason, e.g., member does not exist.
                  }

        Constraints:
            - Team member must exist in the system.
        """
        if member_id not in self.team_members:
            return { "success": False, "error": "Team member does not exist" }

        assignments = [
            assignment for assignment in self.role_assignments.values()
            if assignment["member_id"] == member_id
        ]
        return { "success": True, "data": assignments }

    def get_team_member_by_name(self, name: str) -> dict:
        """
        Retrieve all team members' information and their qualified roles by a given name.

        Args:
            name (str): The name to search for (case-insensitive).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TeamMemberInfo]  # All matches, may be empty if none found
                }
                OR
                {
                    "success": False,
                    "error": str  # No member found with the given name
                }

        Constraints:
            - No constraints, only searches by name.
        """
        # Find all team members with matching (case-insensitive) name
        matches = [
            member_info
            for member_info in self.team_members.values()
            if member_info["name"].lower() == name.lower()
        ]
        if matches:
            return { "success": True, "data": matches }
        else:
            return { "success": False, "error": "No team member found with the specified name." }

    def get_team_member_by_id(self, member_id: str) -> dict:
        """
        Retrieve a team member's information and their qualified roles by their member_id.

        Args:
            member_id (str): The unique identifier of the team member.

        Returns:
            dict: {
                "success": True,
                "data": TeamMemberInfo  # Info of the member including qualified roles
            }
            or
            {
                "success": False,
                "error": str  # Description if member_id does not exist
            }
        """
        member = self.team_members.get(member_id)
        if not member:
            return {"success": False, "error": f"Team member with id '{member_id}' does not exist"}
        return {"success": True, "data": member}

    def list_all_team_members(self) -> dict:
        """
        List all team members currently available in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TeamMemberInfo]  # List of all team members (may be empty)
            }
        """
        all_members = list(self.team_members.values())
        return {
            "success": True,
            "data": all_members
        }

    def check_member_role_qualification(self, member_id: str, role: str) -> dict:
        """
        Check if the given team member is qualified for the specified project role.

        Args:
            member_id (str): The team member's unique identifier.
            role (str): The role to check qualification for.

        Returns:
            dict:
                Success: { "success": True, "qualified": bool }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - The team member must exist in the system.
            - Role should be a non-empty string.
        """
        member = self.team_members.get(member_id)
        if not member:
            return { "success": False, "error": "Team member not found" }
        if not isinstance(role, str) or not role.strip():
            return { "success": False, "error": "Role must be a non-empty string" }
    
        qualified = role in member.get("roles", [])
        return { "success": True, "qualified": qualified }


    def check_member_availability(self, member_id: str) -> dict:
        """
        Determine if a team member is available to take on new project work,
        based on current role assignments and their availability constraints.

        Args:
            member_id (str): ID of the team member to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "available": bool,
                    "details": str or list  # If unavailable, list of conflicting assignments.
                }
            }
            or
            {
                "success": False,
                "error": str  # Team member not found or ambiguity in data.
            }

        Constraints:
            - If member has availability 'full', always available.
            - If 'limited', check that no project assignments overlap in time.
            - If availability is unrecognized, treat as 'limited'.
        """
        member = self.team_members.get(member_id)
        if not member:
            return { "success": False, "error": "Team member not found" }

        availability = member.get("availability", "limited")
        if self._has_full_availability(availability):
            return { "success": True, "data": { "available": True, "details": "Member is fully available." } }

        # Get all project assignments for this member
        member_assignments = [
            ra for ra in self.role_assignments.values()
            if ra["member_id"] == member_id
        ]

        # Gather scheduled project date ranges
        ranges = []
        for ra in member_assignments:
            proj = self.projects.get(ra["project_id"])
            if not proj:
                continue
            try:
                start = datetime.strptime(proj["start_date"], "%Y-%m-%d")
                end = datetime.strptime(proj["end_date"], "%Y-%m-%d")
            except Exception:
                continue  # Bad date format, skip this project

            ranges.append({
                "project_id": proj["project_id"],
                "title": proj["title"],
                "start": start,
                "end": end,
            })

        # For 'limited': check for any date overlaps among assigned projects
        conflicts = []
        ranges_sorted = sorted(ranges, key=lambda x: x["start"])
        for i in range(len(ranges_sorted)):
            for j in range(i+1, len(ranges_sorted)):
                a = ranges_sorted[i]
                b = ranges_sorted[j]
                # Overlap if a's end ≥ b's start and b's end ≥ a's start
                if a["end"] >= b["start"] and b["end"] >= a["start"]:
                    conflicts.append({
                        "project_1": {"id": a["project_id"], "title": a["title"], "start": a["start"].strftime("%Y-%m-%d"), "end": a["end"].strftime("%Y-%m-%d")},
                        "project_2": {"id": b["project_id"], "title": b["title"], "start": b["start"].strftime("%Y-%m-%d"), "end": b["end"].strftime("%Y-%m-%d")},
                    })

        if conflicts:
            return {
                "success": True,
                "data": {
                    "available": False,
                    "details": conflicts
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "available": True,
                    "details": "No overlapping project assignments detected."
                }
            }

    def check_duplicate_assignment(self, project_id: str, member_id: str) -> dict:
        """
        Check whether a team member already has any role assignment in a given project.

        Args:
            project_id (str): The ID of the project to check.
            member_id (str): The ID of the team member to check for.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if assignment exists, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. project/member does not exist
            }

        Constraints:
            - Project and member IDs must exist.
            - No duplicate assignments for a member within the same project.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}
        if member_id not in self.team_members:
            return {"success": False, "error": "Team member does not exist"}

        has_assignment = any(
            ra["project_id"] == project_id and ra["member_id"] == member_id
            for ra in self.role_assignments.values()
        )

        return {"success": True, "data": has_assignment}


    def create_project(
        self,
        title: str,
        start_date: str,
        end_date: str,
        status: str,
        description: str
    ) -> dict:
        """
        Create a new animation project.

        Args:
            title (str): Project title (must be unique)
            start_date (str): Project start date (format not enforced)
            end_date (str): Project end date (format not enforced)
            status (str): Current status of the project
            description (str): Project description

        Returns:
            dict: {
                "success": True,
                "message": "Project created",
                "project_id": str
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Project titles must be unique.
        """
        # Check for required arguments
        if not title or not start_date or not end_date or not status:
            return { "success": False, "error": "Missing required project information" }

        # Enforce unique title
        for proj in self.projects.values():
            if proj['title'] == title:
                return { "success": False, "error": "Project title already exists" }

        # Generate unique project ID
        new_project_id = str(uuid.uuid4())

        new_project_info = {
            "project_id": new_project_id,
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "description": description
        }

        self.projects[new_project_id] = new_project_info

        return {
            "success": True,
            "message": "Project created",
            "project_id": new_project_id
        }

    def assign_role_to_member(
        self,
        project_id: str,
        member_id: str,
        role: str,
        assignment_date: str
    ) -> dict:
        """
        Assign a role to a team member in a project, creating a ProjectRoleAssignment entry.
        Checks qualification, duplicate assignments, and scheduling conflicts.

        Args:
            project_id (str): The ID of the project.
            member_id (str): The team member's ID.
            role (str): The role to assign.
            assignment_date (str): The date/time of assignment (string).

        Returns:
            dict:
                - On success: { "success": True, "message": "<success>" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Member must exist and be qualified for the role.
            - Project must exist.
            - No duplicate (same project, member, role) assignment.
            - No overlapping projects if member's availability is limited.

        """
        # Check for project existence
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }

        # Check for member existence
        if member_id not in self.team_members:
            return { "success": False, "error": "Team member does not exist." }

        tm_info = self.team_members[member_id]

        # Check if member is qualified for the role
        if role not in tm_info.get("roles", []):
            return { "success": False, "error": "Team member is not qualified for this role." }

        # Check for duplicate assignment (same project, member, role)
        for assg in self.role_assignments.values():
            if (
                assg["project_id"] == project_id and
                assg["member_id"] == member_id and
                assg["role"] == role
            ):
                return { "success": False, "error": "Duplicate role assignment for this member in the project." }

        # Availability & scheduling conflict: 
        # We'll enforce no project date overlaps if availability != "unlimited"
        # Assume "availability" string: "unlimited" if no scheduling restriction; otherwise, restrict
        # For all assignments of this member, check for overlap with this project's dates
        project_info = self.projects[project_id]
        target_start = project_info["start_date"]
        target_end = project_info["end_date"]
        member_availability = tm_info.get("availability", "limited")
        if not self._has_full_availability(member_availability):
            # search for other assignments
            for assg in self.role_assignments.values():
                if assg["member_id"] == member_id and assg["project_id"] != project_id:
                    other_proj = self.projects.get(assg["project_id"])
                    if other_proj:
                        # Check overlap (assume date strings in ISO "YYYY-MM-DD")
                        other_start = other_proj["start_date"]
                        other_end = other_proj["end_date"]
                        if (
                            other_start <= target_end and
                            target_start <= other_end
                        ):
                            return {
                                "success": False,
                                "error": "Member has another project overlapping these dates and availability is limited."
                            }
        # Generate new assignment_id
        assignment_id = f"assg_{len(self.role_assignments) + 1}"

        new_assg: ProjectRoleAssignmentInfo = {
            "assignment_id": assignment_id,
            "project_id": project_id,
            "member_id": member_id,
            "role": role,
            "assignment_date": assignment_date
        }
        self.role_assignments[assignment_id] = new_assg

        return {
            "success": True,
            "message": f"Assigned role '{role}' to team member '{member_id}' in project '{project_id}'."
        }

    def bulk_assign_roles_to_members(self, project_id: str, assignments: list) -> dict:
        """
        Assign multiple team members to specific roles for a given project in a single transaction.

        Args:
            project_id (str): The ID of the project.
            assignments (List[dict]): Each dict must have {"member_id": str, "role": str}

        Returns:
            dict: {
                "success": True,
                "message": "Bulk assignments completed for project <project_id>."
            }
            or
            {
                "success": False,
                "error": "Error reason describing the failed constraint."
            }
    
        Constraints:
            - Project must exist.
            - Each team member must exist.
            - Member must be qualified for the role.
            - No duplicate assignment (same member/role for the project).
            - Member's project start dates must not overlap if availability is limited.
            - Transaction is all-or-nothing: if any error, no assignments are created.
        """
        # Check project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}
    
        # Gather project start/end for overlap checking
        project_info = self.projects[project_id]
        project_start = project_info['start_date']
        project_end = project_info['end_date']

        # To check for duplicates in this batch or existing assignments
        batch_assignment_keys = set()
        existing_assignment_keys = set(
            (a['member_id'], a['role'])
            for a in self.role_assignments.values()
            if a['project_id'] == project_id
        )

        # Pre-validation loop BEFORE any state change
        for entry in assignments:
            member_id = entry.get('member_id')
            role = entry.get('role')
            if not member_id or not role:
                return {"success": False, "error": "Missing member_id or role in an assignment entry."}

            # Check team member exists
            if member_id not in self.team_members:
                return {"success": False, "error": f"Team member '{member_id}' does not exist."}

            member_info = self.team_members[member_id]

            # Check member qualified for role
            if role not in member_info['roles']:
                return {"success": False, "error": f"Member {member_id} not qualified for role '{role}'."}

            # Check for batch duplicate assignments
            assignment_key = (member_id, role)
            if assignment_key in batch_assignment_keys:
                return {"success": False, "error": f"Duplicate role '{role}' for member '{member_id}' in input batch."}
            batch_assignment_keys.add(assignment_key)

            # Check for already existing assignment
            if assignment_key in existing_assignment_keys:
                return {
                    "success": False,
                    "error": f"Member '{member_id}' already assigned role '{role}' for project '{project_id}'."
                }

            # Check member's project start dates for overlap if availability is not 'unlimited'
            member_availability = member_info.get('availability', 'limited')
            if not self._has_full_availability(member_availability):
                for a in self.role_assignments.values():
                    if a['member_id'] == member_id:
                        other_proj = self.projects[a['project_id']]
                        other_start, other_end = other_proj['start_date'], other_proj['end_date']
                        overlap = not (project_end < other_start or project_start > other_end)
                        if overlap:
                            return {
                                "success": False,
                                "error": (
                                    f"Schedule conflict for member '{member_id}': "
                                    f"project '{a['project_id']}' ({other_start} to {other_end}) "
                                    f"overlaps with this project ({project_start} to {project_end})."
                                )
                            }

        # All checks passed: do the batch assignment
        now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for entry in assignments:
            member_id = entry['member_id']
            role = entry['role']
            assignment_id = f"{project_id}:{member_id}:{role}"

            self.role_assignments[assignment_id] = {
                "assignment_id": assignment_id,
                "project_id": project_id,
                "member_id": member_id,
                "role": role,
                "assignment_date": now_str
            }

        return {
            "success": True,
            "message": f"Bulk assignments completed for project {project_id}."
        }

    def update_project_details(
        self,
        project_id: str,
        title: str = None,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        description: str = None
    ) -> dict:
        """
        Edit or update project attributes (title, start_date, end_date, status, description).

        Args:
            project_id (str): The unique identifier of the project to update.
            title (str, optional): New title for the project.
            start_date (str, optional): New start date.
            end_date (str, optional): New end date.
            status (str, optional): Updated status value.
            description (str, optional): Updated description.

        Returns:
            dict: {
                "success": True,
                "message": "Project details updated successfully"
            }
            or
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - Project must exist.
            - If title is provided, it must not be empty.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        project = self.projects[project_id]

        # Validate title if updating it.
        if title is not None:
            if not title.strip():
                return {"success": False, "error": "Title cannot be empty"}
            project["title"] = title

        if start_date is not None:
            project["start_date"] = start_date

        if end_date is not None:
            project["end_date"] = end_date

        if status is not None:
            project["status"] = status

        if description is not None:
            project["description"] = description

        # Persist changes
        self.projects[project_id] = project

        return {"success": True, "message": "Project details updated successfully"}

    def remove_assignment(self, assignment_id: str) -> dict:
        """
        Remove a team member’s role assignment from a project.

        Args:
            assignment_id (str): The unique ID of the assignment to be removed.

        Returns:
            dict:
                On success: { "success": True, "message": "Assignment removed from project." }
                On failure: { "success": False, "error": "Assignment not found" }
    
        Constraints:
            - The assignment with the given ID must exist to be removed.
            - Removing the last assignment from a project is allowed; project
              constraint applies at project start, not at assignment removal.
        """
        if assignment_id not in self.role_assignments:
            return { "success": False, "error": "Assignment not found" }

        del self.role_assignments[assignment_id]
        return { "success": True, "message": "Assignment removed from project." }

    def change_member_role_in_project(self, project_id: str, member_id: str, new_role: str) -> dict:
        """
        Modify a team member’s role for an existing assignment in a specific project.

        Args:
            project_id (str): Unique project identifier.
            member_id (str): Unique team member identifier.
            new_role (str): The new role to assign for this member in this project.

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
            - Team member must exist and be qualified for the new role.
            - Project must exist.
            - Existing assignment between member/project must exist.
            - No duplicate role assignment for the member/project with the new role.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }
        if member_id not in self.team_members:
            return { "success": False, "error": "Team member does not exist." }

        member_info = self.team_members[member_id]
        if new_role not in member_info["roles"]:
            return { "success": False, "error": f"Member is not qualified for the role '{new_role}'." }

        # Find assignment(s) for this member on this project
        assignment_id = None
        for aid, assignment in self.role_assignments.items():
            if assignment["project_id"] == project_id and assignment["member_id"] == member_id:
                assignment_id = aid
                break

        if assignment_id is None:
            return { "success": False, "error": "No assignment found for this member in this project." }

        # Check for duplicate: does this member already have an assignment 
        # with this same role in this same project (possibly there is more than one assignment per member)?
        for aid, assignment in self.role_assignments.items():
            if (assignment["project_id"] == project_id 
                and assignment["member_id"] == member_id
                and assignment["role"] == new_role):
                # If it is the same assignment as we're modifying, that's fine
                if aid != assignment_id:
                    return { "success": False, "error": "Duplicate role assignment for this member in this project." }

        # All checks pass; modify the role
        self.role_assignments[assignment_id]["role"] = new_role

        return { "success": True, "message": "Role updated for member in project." }

    def delete_project(self, project_id: str) -> dict:
        """
        Remove a project and all associated role assignments from the system.

        Args:
            project_id (str): The unique identifier for the project to be deleted.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Project <project_id> and all associated assignments have been deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Project <project_id> does not exist."
                    }

        Constraints:
            - The project must exist in the system.
            - All role assignments associated with the project are also deleted.
        """
        if project_id not in self.projects:
            return { "success": False, "error": f"Project {project_id} does not exist." }

        # Remove the project itself
        del self.projects[project_id]

        # Collect assignment_ids of all assignments associated with the project
        to_remove = [aid for aid, ra in self.role_assignments.items() if ra["project_id"] == project_id]

        for aid in to_remove:
            del self.role_assignments[aid]

        return {
            "success": True,
            "message": f"Project {project_id} and all associated assignments have been deleted."
        }


class AnimationStudioProjectManagementSystem(BaseEnv):
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

    def get_project_by_title(self, **kwargs):
        return self._call_inner_tool('get_project_by_title', kwargs)

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def list_all_projects(self, **kwargs):
        return self._call_inner_tool('list_all_projects', kwargs)

    def get_projects_for_member(self, **kwargs):
        return self._call_inner_tool('get_projects_for_member', kwargs)

    def get_assignments_for_project(self, **kwargs):
        return self._call_inner_tool('get_assignments_for_project', kwargs)

    def get_assignments_for_member(self, **kwargs):
        return self._call_inner_tool('get_assignments_for_member', kwargs)

    def get_team_member_by_name(self, **kwargs):
        return self._call_inner_tool('get_team_member_by_name', kwargs)

    def get_team_member_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_member_by_id', kwargs)

    def list_all_team_members(self, **kwargs):
        return self._call_inner_tool('list_all_team_members', kwargs)

    def check_member_role_qualification(self, **kwargs):
        return self._call_inner_tool('check_member_role_qualification', kwargs)

    def check_member_availability(self, **kwargs):
        return self._call_inner_tool('check_member_availability', kwargs)

    def check_duplicate_assignment(self, **kwargs):
        return self._call_inner_tool('check_duplicate_assignment', kwargs)

    def create_project(self, **kwargs):
        return self._call_inner_tool('create_project', kwargs)

    def assign_role_to_member(self, **kwargs):
        return self._call_inner_tool('assign_role_to_member', kwargs)

    def bulk_assign_roles_to_members(self, **kwargs):
        return self._call_inner_tool('bulk_assign_roles_to_members', kwargs)

    def update_project_details(self, **kwargs):
        return self._call_inner_tool('update_project_details', kwargs)

    def remove_assignment(self, **kwargs):
        return self._call_inner_tool('remove_assignment', kwargs)

    def change_member_role_in_project(self, **kwargs):
        return self._call_inner_tool('change_member_role_in_project', kwargs)

    def delete_project(self, **kwargs):
        return self._call_inner_tool('delete_project', kwargs)
