# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import datetime



# Represents a construction project
class ProjectInfo(TypedDict):
    project_id: str
    name: str
    status: str
    description: str
    start_date: str
    end_date: str

# Represents milestones in a project's timeline
class MilestoneInfo(TypedDict):
    milestone_id: str
    project_id: str
    name: str
    target_date: str
    completion_date: Optional[str]
    status: str

# Represents a chronological project plan
class TimelineInfo(TypedDict):
    project_id: str
    phases: List[str]                 # list of phase names
    milestones: List[str]             # list of milestone_ids
    deadlines: Dict[str, str]         # {phase_name: deadline_date}
    schedule: Dict[str, str]          # {phase_name: scheduled_date}

# Represents a resource allocated to a project
class ResourceInfo(TypedDict):
    resource_id: str
    type: str
    details: str
    assigned_project_id: str

# Represents staff assigned to a project
class PersonnelInfo(TypedDict):
    person_id: str
    name: str
    role: str
    assigned_project_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Timelines: {project_id: TimelineInfo}
        self.timelines: Dict[str, TimelineInfo] = {}

        # Milestones: {milestone_id: MilestoneInfo}
        self.milestones: Dict[str, MilestoneInfo] = {}

        # Resources: {resource_id: ResourceInfo}
        self.resources: Dict[str, ResourceInfo] = {}

        # Personnel: {person_id: PersonnelInfo}
        self.personnel: Dict[str, PersonnelInfo] = {}

        # Constraints:
        # - Each project can have multiple milestones and resources/personnel assigned.
        # - Timeline phases and deadlines must be consistent with milestones.
        # - Only active projects can have their schedule updated.
        # - Milestone dates must fall within the project’s overall start_date and end_date.

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve the project details given its project_id.

        Args:
            project_id (str): Unique identifier for the project.
    
        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo,  # Project details
            }
            or
            {
                "success": False,
                "error": str  # Error description if project_id not found
            }

        Constraints:
            - project_id must exist in the system.
        """
        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": f"Project with project_id '{project_id}' does not exist."}
        return {"success": True, "data": project}

    def list_all_projects(self) -> dict:
        """
        Retrieve information for all construction projects (active and archived).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]  # List of projects, may be empty if no projects exist
            }

        Edge Cases:
            - If there are no projects, 'data' will be an empty list.
        """
        projects_list = list(self.projects.values())
        return {"success": True, "data": projects_list}

    def get_project_status(self, project_id: str) -> dict:
        """
        Retrieve the current status of a given project.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict: {
                "success": True,
                "data": str  # status value of the project
            }
            OR
            {
                "success": False,
                "error": str  # error description if project does not exist
            }

        Constraints:
            - The project with the given project_id must exist in the system.
        """
        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": "Project not found"}
        return {"success": True, "data": project["status"]}

    def get_timeline_by_project_id(self, project_id: str) -> dict:
        """
        Retrieve the entire timeline information (phases, milestones, deadlines, schedule) for the given project.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict: {
                "success": True,
                "data": TimelineInfo  # Timeline details for the project.
            }
            or
            {
                "success": False,
                "error": str  # e.g., if the timeline or project does not exist.
            }
    
        Constraints:
            - No status constraint (project does not need to be 'active').
            - Timeline data must exist for the provided project_id.
        """
        timeline = self.timelines.get(project_id)
        if timeline is None:
            return {
                "success": False,
                "error": "Timeline for project not found"
            }
        return {
            "success": True,
            "data": timeline
        }

    def get_milestones_by_project_id(self, project_id: str) -> dict:
        """
        List all milestone details associated with a specific project.

        Args:
            project_id (str): Unique identifier of the project.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": List[MilestoneInfo],  # List may be empty if no milestones for project
                }
              - On failure: {
                    "success": False,
                    "error": str  # Reason for error, e.g., project does not exist
                }

        Constraints:
            - The project_id must refer to an existing project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        milestones = [
            milestone_info for milestone_info in self.milestones.values()
            if milestone_info["project_id"] == project_id
        ]

        return { "success": True, "data": milestones }

    def get_milestone_by_id(self, milestone_id: str) -> dict:
        """
        Retrieve full details of a specific milestone by its milestone_id.

        Args:
            milestone_id (str): The unique identifier of the milestone.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": MilestoneInfo
                }
                On failure (milestone does not exist):
                {
                    "success": False,
                    "error": "Milestone not found"
                }
        Constraints:
            - The milestone_id must exist in the project management system.
        """
        milestone = self.milestones.get(milestone_id)
        if milestone is None:
            return { "success": False, "error": "Milestone not found" }
        return { "success": True, "data": milestone }

    def get_resources_by_project_id(self, project_id: str) -> dict:
        """
        Retrieve all resources assigned to a given project.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[ResourceInfo],  # List of resources assigned to the project (may be empty)
                }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g., project not found
                }

        Constraints:
            - project_id must correspond to an existing project
            - Returns all ResourceInfo where assigned_project_id == project_id
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project ID does not exist"}

        result = [
            resource_info for resource_info in self.resources.values()
            if resource_info["assigned_project_id"] == project_id
        ]

        return {"success": True, "data": result}

    def get_personnel_by_project_id(self, project_id: str) -> dict:
        """
        List all personnel assigned to the specified project.

        Args:
            project_id (str): ID of the project to query.

        Returns:
            dict:
                - success=True, data=List[PersonnelInfo]: all personnel assigned to the project (may be empty)
                - success=False, error=str: reason (e.g., project not found)

        Constraints:
            - The project_id must exist in the system.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        personnel_list = [
            info for info in self.personnel.values()
            if info['assigned_project_id'] == project_id
        ]

        return {"success": True, "data": personnel_list}

    def check_milestone_dates_within_project(self, project_id: str) -> dict:
        """
        Verify that all milestone target and completion dates for the given project
        fall within the project's start_date and end_date.

        Args:
            project_id (str): The ID of the project to check.

        Returns:
            dict: 
            If successful and no milestone violation:
                {
                    "success": True,
                    "data": {
                        "valid": True,
                        "checked_milestones": List[milestone_id],
                        "violations": []
                    }
                }
            If violations found:
                {
                    "success": True,
                    "data": {
                        "valid": False,
                        "checked_milestones": List[milestone_id],
                        "violations": List[{
                            "milestone_id": str,
                            "violation": str
                        }]
                    }
                }
            If error (e.g. project does not exist):
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Milestone target_date and completion_date must fall within project start_date and end_date.
            - completion_date may be None (ignore check if absent).
        """
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Project does not exist" }

        start = project['start_date']
        end = project['end_date']

        checked_milestones = []
        violations = []
        for ms in self.milestones.values():
            if ms['project_id'] != project_id:
                continue
            checked_milestones.append(ms['milestone_id'])
            # Assumes the date format is comparable with string (ISO or YYYY-MM-DD)
            # If needed, could import datetime but per state definition, assume string ISO.
            target = ms['target_date']
            if not (start <= target <= end):
                violations.append({
                    "milestone_id": ms["milestone_id"],
                    "violation": f"Target date {target} outside project date range [{start}, {end}]"
                })
            if ms['completion_date']:
                compl = ms['completion_date']
                if not (start <= compl <= end):
                    violations.append({
                        "milestone_id": ms["milestone_id"],
                        "violation": f"Completion date {compl} outside project date range [{start}, {end}]"
                    })
        return {
            "success": True,
            "data": {
                "valid": len(violations) == 0,
                "checked_milestones": checked_milestones,
                "violations": violations
            }
        }

    def get_project_schedule(self, project_id: str) -> dict:
        """
        Retrieve the phase-wise schedule for a given project.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, str]  # schedule: {phase_name: scheduled_date}, may be empty if no schedule
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (project/timeline not found)
            }

        Constraints:
            - The project must exist.
            - The project's timeline must exist.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        timeline = self.timelines.get(project_id)
        if timeline is None:
            return {"success": False, "error": "Timeline for project not found"}

        # Always return the schedule dict (may be empty)
        return {"success": True, "data": timeline.get("schedule", {})}

    def update_project_status(self, project_id: str, new_status: str) -> dict:
        """
        Change the status of a project (e.g., active, archived, completed).

        Args:
            project_id (str): The unique project identifier whose status is to be changed.
            new_status (str): The new status to apply (e.g., "active", "archived", "completed").

        Returns:
            dict:
                - success (bool): True if the update succeeded, False otherwise.
                - message (str): Success description.
                - error (str): Description of error (if any).

        Constraints:
            - Project with project_id must exist.
            - No explicit restriction on status values unless validated here.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }
    
        # Optionally, implement allowed status validation:
        # allowed_statuses = {"active", "archived", "completed"}
        # if new_status not in allowed_statuses:
        #     return { "success": False, "error": f"Invalid status '{new_status}'." }

        self.projects[project_id]["status"] = new_status
        return { 
            "success": True, 
            "message": f"Project status updated to '{new_status}' for project '{project_id}'." 
        }

    def create_project(
        self,
        project_id: str,
        name: str,
        status: str,
        description: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Create a new construction project record.

        Args:
            project_id (str): Unique identifier for the project.
            name (str): Name of the project.
            status (str): Status (e.g., 'active', 'planned', 'archived').
            description (str): Project description.
            start_date (str): Project start date (string format).
            end_date (str): Project end date (string format).

        Returns:
            dict: {
                "success": True,
                "message": "Project created successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - project_id must be unique.
            - Required fields must be non-empty.
        """
        # Check all required fields are provided and non-empty
        if not all([project_id, name, status, description, start_date, end_date]):
            return {"success": False, "error": "All project fields are required and must be non-empty."}

        if project_id in self.projects:
            return {"success": False, "error": "Project ID already exists."}

        project_info = {
            "project_id": project_id,
            "name": name,
            "status": status,
            "description": description,
            "start_date": start_date,
            "end_date": end_date
        }

        self.projects[project_id] = project_info

        return {"success": True, "message": "Project created successfully."}

    def update_timeline_schedule(self, project_id: str, new_schedule: Dict[str, str]) -> dict:
        """
        Update the scheduled dates for phases within a project's timeline.
    
        Args:
            project_id (str): The ID of the project whose schedule is to be updated.
            new_schedule (Dict[str, str]): A mapping {phase_name: new_scheduled_date}.
                All phase names in new_schedule must exist in the project's timeline phases.
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Schedule updated for project <project_id>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Project must exist.
            - Timeline for the project must exist.
            - Project status must be 'active'.
            - Phase names in new_schedule must all be defined in the project's timeline phases.
        """
        # Check if project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
    
        # Check if timeline exists
        if project_id not in self.timelines:
            return {"success": False, "error": "Timeline not found for the project"}
    
        # Check project status
        status = self.projects[project_id]["status"]
        if status.lower() not in {"active", "paused"}:
            return {"success": False, "error": "Only active or paused projects can have their schedule updated"}
    
        # Check for valid phases (all phases in new_schedule must be valid)
        timeline = self.timelines[project_id]
        valid_phases = set(timeline["phases"])
        for phase in new_schedule:
            if phase not in valid_phases:
                return {"success": False, "error": f"Invalid phase: '{phase}' not found in project timeline phases"}
    
        # Update timeline schedule
        timeline_schedule = timeline.get("schedule", {})
        timeline_schedule.update(new_schedule)
        # Save back in the state
        timeline["schedule"] = timeline_schedule
        self.timelines[project_id] = timeline
    
        return {"success": True, "message": f"Schedule updated for project {project_id}"}

    def add_milestone_to_project(
        self,
        project_id: str,
        milestone_id: str,
        name: str,
        target_date: str,
        status: str,
        completion_date: Optional[str] = None,
    ) -> dict:
        """
        Add a new milestone to a project, ensuring the milestone's date(s) fall within the project's start and end dates.

        Args:
            project_id (str): Project to which the milestone is to be added.
            milestone_id (str): Unique milestone identifier.
            name (str): Milestone name.
            target_date (str): Planned date for milestone (YYYY-MM-DD).
            completion_date (Optional[str]): Actual completion date, or None.
            status (str): Status for the milestone.

        Returns:
            dict:
                On success: { "success": True, "message": "Milestone added to project." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Milestone dates (target and completion, if set) must be within the project's start_date and end_date.
            - Milestone ID must be unique.
            - Project must exist.
        """
        # Check project existence
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }

        # Check milestone uniqueness
        if milestone_id in self.milestones:
            return { "success": False, "error": "Milestone ID already exists." }

        project = self.projects[project_id]
        project_start = project.get("start_date")
        project_end = project.get("end_date")
    
        # Helper for date string comparison (assuming YYYY-MM-DD)
        def _date_in_range(date: str, start: str, end: str) -> bool:
            return (start <= date <= end)

        if not _date_in_range(target_date, project_start, project_end):
            return { "success": False, "error": "Target date is outside the project's date bounds." }

        if completion_date in ("", "None"):
            completion_date = None

        if completion_date is not None:
            if not _date_in_range(completion_date, project_start, project_end):
                return { "success": False, "error": "Completion date is outside the project's date bounds." }

        # Add milestone entry
        milestone_info: MilestoneInfo = {
            "milestone_id": milestone_id,
            "project_id": project_id,
            "name": name,
            "target_date": target_date,
            "completion_date": completion_date,
            "status": status
        }
        self.milestones[milestone_id] = milestone_info

        # Update timeline's milestone list if timeline exists for project
        if project_id in self.timelines:
            self.timelines[project_id]["milestones"].append(milestone_id)

        return { "success": True, "message": "Milestone added to project." }

    def update_milestone_details(
        self,
        milestone_id: str,
        target_date: Optional[str] = None,
        completion_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> dict:
        """
        Update target_date, completion_date, or status of a milestone, with date consistency checks.

        Args:
            milestone_id (str): Unique milestone ID to update.
            target_date (Optional[str]): New planned date ("YYYY-MM-DD"), optional.
            completion_date (Optional[str]): New completion date ("YYYY-MM-DD"), optional.
            status (Optional[str]): New status value, optional.

        Returns:
            dict: 
              - Success: {"success": True, "message": "Milestone updated successfully."}
              - Failure: {"success": False, "error": "reason"}
    
        Constraints:
            - Milestone must exist.
            - Any provided date (target_date/completion_date) must be between project's start_date and end_date (inclusive).
            - Dates should be in ISO "YYYY-MM-DD" format.
        """

        # Lookup milestone
        milestone = self.milestones.get(milestone_id)
        if milestone is None:
            return {"success": False, "error": "Milestone not found."}

        project_id = milestone.get("project_id")
        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": "Associated project not found."}

        # Project date boundaries
        start_date = project.get("start_date")
        end_date = project.get("end_date")
        try:
            project_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            project_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            return {"success": False, "error": "Project start/end date format invalid."}

        # Validate and update target_date if provided
        if target_date is not None:
            try:
                td = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            except Exception:
                return {"success": False, "error": "target_date format invalid."}
            if not (project_start <= td <= project_end):
                return {"success": False, "error": "target_date not within project's start/end dates."}
            milestone["target_date"] = target_date

        # Validate and update completion_date if provided
        if completion_date is not None:
            try:
                cd = datetime.datetime.strptime(completion_date, "%Y-%m-%d").date()
            except Exception:
                return {"success": False, "error": "completion_date format invalid."}
            if not (project_start <= cd <= project_end):
                return {"success": False, "error": "completion_date not within project's start/end dates."}
            milestone["completion_date"] = completion_date

        if status is not None:
            milestone["status"] = status

        # Save changes (dict is by-reference so saved)
        self.milestones[milestone_id] = milestone

        return {"success": True, "message": "Milestone updated successfully."}

    def assign_resource_to_project(
        self,
        resource_id: str,
        project_id: str,
        type: Optional[str] = None,
        details: Optional[str] = None,
    ) -> dict:
        """
        Allocate a resource to a project (creating a new resource assignment).
    
        Args:
            resource_id (str): Unique ID of the resource to assign.
            type (str): Type of the resource (e.g., equipment, material).
            details (str): Description or specifics of the resource.
            project_id (str): The ID of the project to assign the resource to.

        Returns:
            dict: {
                "success": True,
                "message": "Resource assigned to project <project_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The project must exist.
            - If resource_id already exists and is assigned to another project, return error.
            - If resource_id already assigned to the same project, return error.
        """
        # Check project existence
        if project_id not in self.projects:
            return { "success": False, "error": f"Project {project_id} does not exist." }

        # Does the resource exist?
        if resource_id in self.resources:
            existing_resource = self.resources[resource_id]
            existing_project_id = existing_resource.get("assigned_project_id", "")
            if existing_project_id == project_id:
                return { "success": False, "error": f"Resource {resource_id} is already assigned to this project." }
            if existing_project_id:
                return { "success": False, "error": f"Resource {resource_id} is already assigned to another project ({existing_resource['assigned_project_id']})." }
            if type is not None:
                existing_resource["type"] = type
            if details is not None:
                existing_resource["details"] = details
            existing_resource["assigned_project_id"] = project_id
            self.resources[resource_id] = existing_resource
            return {
                "success": True,
                "message": f"Resource {resource_id} assigned to project {project_id}."
            }

        if type is None or details is None:
            return { "success": False, "error": "type and details are required when assigning a new resource." }
    
        # Assign the new resource
        resource_info: ResourceInfo = {
            "resource_id": resource_id,
            "type": type,
            "details": details,
            "assigned_project_id": project_id
        }
        self.resources[resource_id] = resource_info

        return {
            "success": True,
            "message": f"Resource {resource_id} assigned to project {project_id}."
        }

    def assign_personnel_to_project(self, person_id: str, project_id: str) -> dict:
        """
        Assign a personnel/staff member to a specified project.

        Args:
            person_id (str): The unique identifier of the personnel to be assigned.
            project_id (str): The unique identifier of the target project.

        Returns:
            dict:
                { "success": True, "message": "Personnel assigned to project successfully." }
                OR
                { "success": False, "error": <error_message> }

        Constraints:
            - Personnel (person_id) must exist.
            - Project (project_id) must exist.
            - Updates 'assigned_project_id' for the specified personnel.
            - If personnel is already assigned to the project, operation is idempotent and returns success.
        """
        if person_id not in self.personnel:
            return { "success": False, "error": "Personnel does not exist." }

        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }

        current_project_id = self.personnel[person_id].get("assigned_project_id")
        if current_project_id == project_id:
            return { "success": True, "message": "Personnel assigned to project successfully." }

        self.personnel[person_id]["assigned_project_id"] = project_id
        return { "success": True, "message": "Personnel assigned to project successfully." }

    def remove_resource_from_project(self, resource_id: str, project_id: str) -> dict:
        """
        De-allocate a resource from a given project.
    
        Args:
            resource_id (str): ID of the resource to be removed.
            project_id (str): ID of the project from which the resource is to be removed.

        Returns:
            dict: On success, { "success": True, "message": "Resource <resource_id> removed from project <project_id>" }
                  On failure, { "success": False, "error": <reason> }
              
        Constraints:
            - The resource must exist.
            - The project must exist.
            - The resource must be assigned to the given project.
            - The resource's assigned_project_id is set to an empty string upon removal.
        """
        if resource_id not in self.resources:
            return { "success": False, "error": f"Resource {resource_id} does not exist." }
        if project_id not in self.projects:
            return { "success": False, "error": f"Project {project_id} does not exist." }
        resource = self.resources[resource_id]
        if resource.get("assigned_project_id", "") != project_id:
            return { "success": False, "error": f"Resource {resource_id} is not assigned to project {project_id}." }

        # De-allocate the resource
        resource["assigned_project_id"] = ""
        return { "success": True, "message": f"Resource {resource_id} removed from project {project_id}" }

    def remove_personnel_from_project(self, person_id: str, project_id: str) -> dict:
        """
        Remove personnel assignment from a project.

        Args:
            person_id (str): The ID of the personnel to remove.
            project_id (str): The ID of the project from which to remove the personnel.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Personnel <person_id> removed from project <project_id>."
                }
            or
                {
                    "success": False,
                    "error": "<reason>"
                }
    
        Constraints:
            - Personnel must exist.
            - Project must exist.
            - Personnel must actually be assigned to the given project.
        """
        if person_id not in self.personnel:
            return { "success": False, "error": f"Personnel {person_id} does not exist." }
        if project_id not in self.projects:
            return { "success": False, "error": f"Project {project_id} does not exist." }
        personnel_entry = self.personnel[person_id]
        if personnel_entry["assigned_project_id"] != project_id:
            return { "success": False, "error": f"Personnel {person_id} is not assigned to project {project_id}." }
    
        personnel_entry["assigned_project_id"] = ""
        self.personnel[person_id] = personnel_entry
        return {
            "success": True,
            "message": f"Personnel {person_id} removed from project {project_id}."
        }


class ConstructionProjectManagementSystem(BaseEnv):
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

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def list_all_projects(self, **kwargs):
        return self._call_inner_tool('list_all_projects', kwargs)

    def get_project_status(self, **kwargs):
        return self._call_inner_tool('get_project_status', kwargs)

    def get_timeline_by_project_id(self, **kwargs):
        return self._call_inner_tool('get_timeline_by_project_id', kwargs)

    def get_milestones_by_project_id(self, **kwargs):
        return self._call_inner_tool('get_milestones_by_project_id', kwargs)

    def get_milestone_by_id(self, **kwargs):
        return self._call_inner_tool('get_milestone_by_id', kwargs)

    def get_resources_by_project_id(self, **kwargs):
        return self._call_inner_tool('get_resources_by_project_id', kwargs)

    def get_personnel_by_project_id(self, **kwargs):
        return self._call_inner_tool('get_personnel_by_project_id', kwargs)

    def check_milestone_dates_within_project(self, **kwargs):
        return self._call_inner_tool('check_milestone_dates_within_project', kwargs)

    def get_project_schedule(self, **kwargs):
        return self._call_inner_tool('get_project_schedule', kwargs)

    def update_project_status(self, **kwargs):
        return self._call_inner_tool('update_project_status', kwargs)

    def create_project(self, **kwargs):
        return self._call_inner_tool('create_project', kwargs)

    def update_timeline_schedule(self, **kwargs):
        return self._call_inner_tool('update_timeline_schedule', kwargs)

    def add_milestone_to_project(self, **kwargs):
        return self._call_inner_tool('add_milestone_to_project', kwargs)

    def update_milestone_details(self, **kwargs):
        return self._call_inner_tool('update_milestone_details', kwargs)

    def assign_resource_to_project(self, **kwargs):
        return self._call_inner_tool('assign_resource_to_project', kwargs)

    def assign_personnel_to_project(self, **kwargs):
        return self._call_inner_tool('assign_personnel_to_project', kwargs)

    def remove_resource_from_project(self, **kwargs):
        return self._call_inner_tool('remove_resource_from_project', kwargs)

    def remove_personnel_from_project(self, **kwargs):
        return self._call_inner_tool('remove_personnel_from_project', kwargs)
