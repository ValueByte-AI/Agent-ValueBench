# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid



class JobPostingInfo(TypedDict):
    job_id: str
    team_id: str
    title: str
    description: str
    creation_date: str
    status: str
    location: str
    position_type: str  # corrected from 'position_typ'

class TeamInfo(TypedDict):
    team_id: str  # corrected from 'am_id'
    team_name: str
    buyer_reference_id: str
    department: str  # corrected from 'departmen'

class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    team_id: str
    role: str  # corrected from 'rol'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for recruitment platform job management.
        """

        # JobPostings: {job_id: JobPostingInfo}
        self.job_postings: Dict[str, JobPostingInfo] = {}

        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each JobPosting must be associated with exactly one Team (team_id or buyer_reference_id).
        # - Only job postings within a given time window are included in time-based queries.
        # - Only active (non-deleted) job postings are included in standard review/search.
        # - Access control to job postings is restricted by user role/team association.

    def get_team_by_buyer_reference_id(self, buyer_reference_id: str) -> dict:
        """
        Retrieve a team entity using its `buyer_reference_id`.

        Args:
            buyer_reference_id (str): The buyer_reference_id for which the team is to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo
            }
            or
            {
                "success": False,
                "error": str  # If no matching team is found
            }

        Constraints:
            - Each team in the system should have a unique buyer_reference_id.
        """
        for team in self.teams.values():
            if team.get("buyer_reference_id") == buyer_reference_id:
                return { "success": True, "data": team }

        return {
            "success": False,
            "error": "Team with given buyer_reference_id not found"
        }

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve detailed information about a team using the team's team_id.

        Args:
            team_id (str): The unique identifier for the team.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": TeamInfo}
                - On failure (team_id not found):
                    {"success": False, "error": "Team not found"}

        Constraints:
            - The team_id must exist in the system.
        """
        team_info = self.teams.get(team_id)
        if team_info is None:
            return {"success": False, "error": "Team not found"}
        else:
            return {"success": True, "data": team_info}

    def list_all_teams(self) -> dict:
        """
        List all teams/organizational units in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TeamInfo],  # All teams (can be empty if none exist)
            }
        Constraints:
            - No input parameters.
            - No access control; returns all teams present in the system.
        """
        teams_list = list(self.teams.values())
        return { "success": True, "data": teams_list }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user details given the user's unique _id.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict: 
              - On success: {"success": True, "data": UserInfo}
              - On failure: {"success": False, "error": "User not found"}

        Constraints:
            - The user _id must exist in the system.
        """
        user = self.users.get(_id)
        if user is not None:
            return { "success": True, "data": user }
        else:
            return { "success": False, "error": "User not found" }

    def list_users_by_team_id(self, team_id: str) -> dict:
        """
        List all users associated with a particular team.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # list of user metadata (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # reason for failure (e.g. "Team does not exist")
            }

        Constraints:
            - Team with team_id must exist.
            - Lists all users whose 'team_id' == team_id.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        result = [
            user_info for user_info in self.users.values()
            if user_info["team_id"] == team_id
        ]

        return { "success": True, "data": result }

    def get_user_role(self, user_id: str) -> dict:
        """
        Retrieve the role of a specific user by their user_id.

        Args:
            user_id (str): The unique identifier (_id) of the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # The user's role
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., user not found
            }

        Constraints:
            - The user must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info["role"] }

    def list_job_postings_by_team_id(self, team_id: str) -> dict:
        """
        Retrieve all job postings associated with a specific team by team_id.

        Args:
            team_id (str): The unique identifier for the team.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[JobPostingInfo]  # may be an empty list if no job postings for team
                    }
                On error:
                    {
                        "success": False,
                        "error": "Team does not exist"
                    }

        Constraints:
            - Team must exist.
            - Returns all job postings for the given team (no status or access filtering).
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        results = [
            job_info for job_info in self.job_postings.values()
            if job_info["team_id"] == team_id
        ]

        return { "success": True, "data": results }

    def list_active_job_postings_by_team_id(self, team_id: str) -> dict:
        """
        Retrieve all active (non-deleted) job postings for the specified team.

        Args:
            team_id (str): The ID of the team whose active job postings are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostingInfo]  # List may be empty if no active postings for the team
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. team does not exist
            }

        Constraints:
            - The team must exist.
            - Only job postings whose status indicates they are active (status == "active") are returned.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        # Assuming "active" job postings have status == "active" (case-insensitive match).
        active_postings = [
            posting for posting in self.job_postings.values()
            if posting["team_id"] == team_id and posting["status"].lower() == "active"
        ]

        return { "success": True, "data": active_postings }

    def list_job_postings_by_team_and_time_window(self, team_id: str, start_date: str, end_date: str) -> dict:
        """
        Retrieve all active job postings for the given team, whose creation_date falls within [start_date, end_date] (inclusive).

        Args:
            team_id (str): The unique id of the team to filter job postings by.
            start_date (str): The start of the creation_date window (ISO 8601 string, inclusive).
            end_date (str): The end of the creation_date window (ISO 8601 string, inclusive).

        Returns:
            dict: 
                - On success: {"success": True, "data": [JobPostingInfo, ...]}
                - On error: {"success": False, "error": error message}

        Constraints:
            - Team must exist.
            - Only job postings associated to the team_id are returned.
            - Only job postings with 'status' different from 'deleted' are included.
            - Only postings whose 'creation_date' between start_date and end_date (inclusive) are included.
            - start_date should not be greater than end_date (lexicographically).

        Notes:
            - creation_date, start_date, and end_date should be ISO 8601 format strings, which are lexicographically comparable.
        """
        # Check if the team exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        # Check date input validity
        if start_date > end_date:
            return {"success": False, "error": "Invalid date range: start_date > end_date"}

        result = []
        for jp in self.job_postings.values():
            # Only include active postings (status != 'deleted')
            if jp["team_id"] != team_id:
                continue
            if jp.get("status", "").lower() == "deleted":
                continue
            # Date-window filtering (inclusive)
            if start_date <= jp.get("creation_date", "") <= end_date:
                result.append(jp)
        return {"success": True, "data": result}

    def get_job_posting_by_id(self, job_id: str) -> dict:
        """
        Retrieve detailed information for a specific job posting given its job_id.

        Args:
            job_id (str): The unique identifier for the job posting.

        Returns:
            dict: {
                "success": True,
                "data": JobPostingInfo,   # if found
            }
            or
            {
                "success": False,
                "error": str              # if not found
            }

        Constraints:
            - The job_id must exist in the system.
            - No access/role filter is applied.
        """
        job = self.job_postings.get(job_id)
        if job is None:
            return {"success": False, "error": "Job posting not found"}
        return {"success": True, "data": job}


    def list_active_job_postings_by_time_window(
        self,
        start_date: str,
        end_date: str,
        team_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        List all active job postings created within the specified time window.
        Optionally filter by one or more team IDs.

        Args:
            start_date (str): Inclusive lower bound of creation_date (ISO format 'YYYY-MM-DD')
            end_date (str): Inclusive upper bound of creation_date (ISO format 'YYYY-MM-DD')
            team_ids (Optional[List[str]]): If provided, only include job postings from these teams.

        Returns:
            dict:
                Success: { "success": True, "data": [JobPostingInfo, ...] }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Only include job postings where 'status' indicates active (e.g., status == "active").
            - Only include postings where start_date <= creation_date <= end_date.
            - If team_ids is given, only include postings from those teams.
        """
        # Parse the date strings to datetime for comparison
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except Exception:
            return { "success": False, "error": "Invalid date format. Use YYYY-MM-DD." }

        if end_dt < start_dt:
            return { "success": False, "error": "end_date must not be before start_date." }

        result = []
        for jp in self.job_postings.values():
            # Filter: status
            if jp.get("status", "").lower() != "active":
                continue

            # Filter: team (if given)
            if team_ids is not None and jp.get("team_id") not in team_ids:
                continue

            # Filter: creation date
            try:
                job_dt = datetime.strptime(jp.get("creation_date", ""), "%Y-%m-%d")
            except Exception:
                # Ignore badly formatted or missing creation_date
                continue

            if start_dt <= job_dt <= end_dt:
                result.append(jp)

        return { "success": True, "data": result }

    def check_access_to_job_posting(self, user_id: str, job_id: str) -> dict:
        """
        Determine if a user has the required role or team association to access a given job posting.

        Args:
            user_id (str): ID of the user to check.
            job_id (str): ID of the job posting being accessed.

        Returns:
            dict:
                success (bool): If the function ran successfully.
                has_access (bool, optional): Whether the user can access the posting. Only present if success.
                reason (str): Explanation for access granted or denied, or error details.
                error (str, optional): Error message if failed.

        Constraints:
            - User and JobPosting must exist in the system.
            - Admin role has access to all.
            - Otherwise, user.team_id must match job_posting.team_id.
        """
        # Fetch User
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Fetch JobPosting
        job_posting = self.job_postings.get(job_id)
        if not job_posting:
            return {"success": False, "error": "JobPosting not found"}

        user_role = user.get('role', '').lower()
        user_team_id = user.get('team_id')
        job_team_id = job_posting.get('team_id')

        # Admins can access all job postings
        if user_role == 'admin':
            return {
                "success": True,
                "has_access": True,
                "reason": "User is admin and has access to all job postings."
            }

        # Non-admins can access postings only within their own team
        if user_team_id == job_team_id:
            return {
                "success": True,
                "has_access": True,
                "reason": "User's team matches the job posting's team."
            }
        else:
            return {
                "success": True,
                "has_access": False,
                "reason": "User's team does not match the job posting's team, and user is not admin."
            }

    def add_job_posting(
        self,
        team_id: str,
        title: str,
        description: str,
        creation_date: str,
        status: str = "active",
        location: str = "",
        position_type: str = "",
        job_id: str = None
    ) -> dict:
        """
        Create a new job posting under the specified team.

        Args:
            team_id (str): The ID of the team to associate with this job posting.
            title (str): Title of the job posting.
            description (str): Description of the job.
            creation_date (str): Date the job was created (format: ISO 8601 recommended).
            status (str, optional): Status of the job posting ('active', 'inactive', etc.). Defaults to 'active'.
            location (str, optional): Job location. Defaults to "".
            position_type (str, optional): Type of the position. Defaults to "".
            job_id (str, optional): Unique job ID. If not provided, will be auto-generated.

        Returns:
            dict: {
                "success": True,
                "message": "Job posting created successfully",
                "job_id": <job_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The specified team_id must exist.
            - The job_id must be unique if provided.
            - All required fields (team_id, title, description, creation_date) must be supplied.
        """
        # Validate required fields
        if not team_id or not title or not description or not creation_date:
            return {"success": False, "error": "Missing required fields"}

        # Validate team
        if team_id not in self.teams:
            return {"success": False, "error": "Specified team_id does not exist"}

        # Generate a job_id if not supplied
        if not job_id:
            job_id = str(uuid.uuid4())
        else:
            # Ensure uniqueness of job_id
            if job_id in self.job_postings:
                return {"success": False, "error": "job_id already exists"}

        # Construct the new job posting
        job_posting = {
            "job_id": job_id,
            "team_id": team_id,
            "title": title,
            "description": description,
            "creation_date": creation_date,
            "status": status,
            "location": location,
            "position_type": position_type,
        }

        # Insert into job postings
        self.job_postings[job_id] = job_posting

        return {
            "success": True,
            "message": "Job posting created successfully",
            "job_id": job_id
        }

    def update_job_posting(self, job_id: str, **updates) -> dict:
        """
        Edit the details of an existing job posting.

        Args:
            job_id (str): The unique ID of the job posting to update.
            **updates: Arbitrary keyword arguments for updatable job posting fields (e.g., title, description, status, location, position_type).

        Returns:
            dict: {
                "success": True,
                "message": "Job posting <job_id> updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The job posting must exist.
            - Only specified, allowed fields are modifiable.
            - Attempting to update job_id will be rejected.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist" }

        allowed_fields = {"title", "description", "status", "location", "position_type"}
        invalid_fields = set(updates.keys()) - allowed_fields

        if "job_id" in updates:
            return { "success": False, "error": "Cannot update job_id" }
        if not updates:
            return { "success": False, "error": "No fields provided for update" }
        if invalid_fields:
            return { "success": False, "error": f"Invalid or uneditable fields: {', '.join(sorted(invalid_fields))}" }

        # Update the job posting
        for key, value in updates.items():
            self.job_postings[job_id][key] = value

        return { "success": True, "message": f"Job posting {job_id} updated successfully" }

    def deactivate_job_posting(self, job_id: str) -> dict:
        """
        Soft-delete (deactivate) a job posting by setting its status to 'inactive'.
    
        Args:
            job_id (str): The unique identifier of the job posting to deactivate.
        
        Returns:
            dict: {
                "success": True,
                "message": "Job posting <job_id> deactivated."
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., not found, already inactive)
            }
        
        Constraints:
            - The job posting must exist.
            - A job posting already inactive should not be deactivated again.
            - The status value 'inactive' is used to represent soft-delete.
        """
        job = self.job_postings.get(job_id)
        if not job:
            return { "success": False, "error": "Job posting not found" }
        if job.get("status", "").lower() == "inactive":
            return { "success": False, "error": "Job posting is already inactive." }

        job["status"] = "inactive"
        self.job_postings[job_id] = job
        return { "success": True, "message": f"Job posting {job_id} deactivated." }

    def activate_job_posting(self, job_id: str) -> dict:
        """
        Restore (activate) a deactivated/inactive job posting.

        Args:
            job_id (str): The identifier for the job posting to activate.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success confirmation
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: not found, already active, etc.
            }

        Constraints:
            - Only non-active job postings can be activated.
            - Job posting must exist.
        """
        job_posting = self.job_postings.get(job_id)
        if job_posting is None:
            return {"success": False, "error": "Job posting not found."}

        if job_posting["status"].lower() == "active":
            return {"success": False, "error": "Job posting is already active."}

        job_posting["status"] = "active"
        self.job_postings[job_id] = job_posting  # (Probably not needed, but ensures dict is updated.)

        return {"success": True, "message": f"Job posting {job_id} activated."}

    def assign_job_posting_to_team(self, job_id: str, new_team_id: str) -> dict:
        """
        Change the team association of a job posting, if allowed.

        Args:
            job_id (str): The unique ID of the job posting to modify.
            new_team_id (str): The team_id of the new team to associate with this job posting.

        Returns:
            dict:
                { "success": True, "message": "Job posting <job_id> reassigned to team <new_team_id>." }
            or
                { "success": False, "error": <reason> }

        Constraints:
            - job_id must exist in job_postings.
            - new_team_id must exist in teams.
            - The job posting must be reassigned to exactly one team after the operation.
            - (Typically, permission checks would apply, but not described for this op.)
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist" }
        if new_team_id not in self.teams:
            return { "success": False, "error": "Target team does not exist" }
    
        # Optionally, check if job posting is active (if required)
        # status = self.job_postings[job_id].get("status", "").lower()
        # if status != "active":
        #     return { "success": False, "error": "Job posting is not active and cannot be reassigned" }

        self.job_postings[job_id]["team_id"] = new_team_id
        return { "success": True, "message": f"Job posting {job_id} reassigned to team {new_team_id}." }

    def add_team(
        self,
        team_id: str,
        team_name: str,
        buyer_reference_id: str,
        department: str
    ) -> dict:
        """
        Create a new team/organizational unit.

        Args:
            team_id (str): Unique identifier for the team.
            team_name (str): Name of the team.
            buyer_reference_id (str): Reference ID associated with buyer/account.
            department (str): Department for the team.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Team <team_name> (ID: <team_id>) added."
                }
                On failure,
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - `team_id` must not already exist within the system.
            - All fields must be non-empty strings.
        """

        # Validate input fields (simple non-empty string check)
        if not all(isinstance(x, str) and x.strip() for x in [team_id, team_name, buyer_reference_id, department]):
            return {"success": False, "error": "All team fields must be non-empty strings."}

        if team_id in self.teams:
            return {"success": False, "error": f"Team with ID '{team_id}' already exists."}

        team_info: TeamInfo = {
            "team_id": team_id,
            "team_name": team_name,
            "buyer_reference_id": buyer_reference_id,
            "department": department
        }

        self.teams[team_id] = team_info

        return {
            "success": True,
            "message": f"Team {team_name} (ID: {team_id}) added."
        }

    def update_team(
        self,
        team_id: str,
        team_name: str = None,
        buyer_reference_id: str = None,
        department: str = None
    ) -> dict:
        """
        Edit the metadata/details about a team.

        Args:
            team_id (str): Unique identifier for the team to update.
            team_name (str, optional): New team name.
            buyer_reference_id (str, optional): New buyer reference id.
            department (str, optional): New department name.

        Returns:
            dict:
              - On success: {"success": True, "message": "Team details updated."}
              - On failure: {"success": False, "error": <str error reason>}

        Constraints:
            - team_id must exist.
            - Only team_name, buyer_reference_id, and department can be modified.
            - At least one update field must be provided.
        """
        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": "Team not found."}
    
        updated = False
        if team_name is not None:
            team["team_name"] = team_name
            updated = True
        if buyer_reference_id is not None:
            team["buyer_reference_id"] = buyer_reference_id
            updated = True
        if department is not None:
            team["department"] = department
            updated = True
    
        if not updated:
            return {"success": False, "error": "No update fields provided."}

        # Save back to state (not strictly needed as dict is mutable, but for clarity)
        self.teams[team_id] = team
        return {"success": True, "message": "Team details updated."}

    def add_user(self, _id: str, name: str, email: str, team_id: str, role: str) -> dict:
        """
        Register a new user/stakeholder in the system.

        Args:
            _id (str): Unique identifier for the user.
            name (str): Full name of the user.
            email (str): Email address of the user.
            team_id (str): Team identifier (must exist).
            role (str): User's role in the system.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "User <name> added successfully."}
                - On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - User _id must be unique across all users.
            - User must be assigned to an existing team.
            - All fields must be non-empty.
        """
        # Check required fields
        if not all([_id, name, email, team_id, role]):
            return {"success": False, "error": "All user fields must be provided and non-empty."}

        if _id in self.users:
            return {"success": False, "error": f"User ID '{_id}' already exists."}

        if team_id not in self.teams:
            return {"success": False, "error": f"Team ID '{team_id}' does not exist."}

        self.users[_id] = {
            "_id": _id,
            "name": name,
            "email": email,
            "team_id": team_id,
            "role": role
        }

        return {"success": True, "message": f"User '{name}' added successfully."}

    def update_user_role(self, user_id: str, new_role: str = None, new_team_id: str = None) -> dict:
        """
        Change the role and/or team association of a user.

        Args:
            user_id (str): The user to update.
            new_role (str, optional): The new role. Leave as None if not changing.
            new_team_id (str, optional): The new team ID to associate. Leave as None if not changing.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> role/team updated."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The user must exist.
            - If new_team_id is given, it must correspond to a valid team.
            - At least one of new_role or new_team_id must be provided.
        """
        if user_id not in self.users:
            return {"success": False, "error": f"User {user_id} does not exist."}
        if new_role is None and new_team_id is None:
            return {"success": False, "error": "No new_role or new_team_id provided; nothing to update."}
        if new_team_id is not None and new_team_id not in self.teams:
            return {"success": False, "error": f"Team {new_team_id} does not exist."}

        user_info = self.users[user_id]
        changes = []
        if new_role is not None:
            user_info["role"] = new_role
            changes.append("role")
        if new_team_id is not None:
            user_info["team_id"] = new_team_id
            changes.append("team")
        self.users[user_id] = user_info
        msg = f"User {user_id} updated ({', '.join(changes)})."
        return {"success": True, "message": msg}


class RecruitmentJobManagementSystem(BaseEnv):
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

    def get_team_by_buyer_reference_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_buyer_reference_id', kwargs)

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def list_all_teams(self, **kwargs):
        return self._call_inner_tool('list_all_teams', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_users_by_team_id(self, **kwargs):
        return self._call_inner_tool('list_users_by_team_id', kwargs)

    def get_user_role(self, **kwargs):
        return self._call_inner_tool('get_user_role', kwargs)

    def list_job_postings_by_team_id(self, **kwargs):
        return self._call_inner_tool('list_job_postings_by_team_id', kwargs)

    def list_active_job_postings_by_team_id(self, **kwargs):
        return self._call_inner_tool('list_active_job_postings_by_team_id', kwargs)

    def list_job_postings_by_team_and_time_window(self, **kwargs):
        return self._call_inner_tool('list_job_postings_by_team_and_time_window', kwargs)

    def get_job_posting_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_posting_by_id', kwargs)

    def list_active_job_postings_by_time_window(self, **kwargs):
        return self._call_inner_tool('list_active_job_postings_by_time_window', kwargs)

    def check_access_to_job_posting(self, **kwargs):
        return self._call_inner_tool('check_access_to_job_posting', kwargs)

    def add_job_posting(self, **kwargs):
        return self._call_inner_tool('add_job_posting', kwargs)

    def update_job_posting(self, **kwargs):
        return self._call_inner_tool('update_job_posting', kwargs)

    def deactivate_job_posting(self, **kwargs):
        return self._call_inner_tool('deactivate_job_posting', kwargs)

    def activate_job_posting(self, **kwargs):
        return self._call_inner_tool('activate_job_posting', kwargs)

    def assign_job_posting_to_team(self, **kwargs):
        return self._call_inner_tool('assign_job_posting_to_team', kwargs)

    def add_team(self, **kwargs):
        return self._call_inner_tool('add_team', kwargs)

    def update_team(self, **kwargs):
        return self._call_inner_tool('update_team', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_role(self, **kwargs):
        return self._call_inner_tool('update_user_role', kwargs)

