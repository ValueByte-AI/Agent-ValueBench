# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    current_job_id: str  # must reference a valid JobRole
    job_history: List[str]  # list of past job_ids
    skills: List[str]
    preferences: Dict[str, Any]  # assuming preferences is a flexible key-value store

class JobRoleInfo(TypedDict):
    job_id: str
    title: str
    description: str
    required_skills: List[str]
    industry: str
    typical_career_path: List[str]  # list of job_id

class JobRelationshipInfo(TypedDict):
    from_job_id: str  # must reference existing JobRole
    to_job_id: str    # must reference existing JobRole
    relationship_type: str  # 'promotion', 'lateral move', etc.

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # JobRoles: {job_id: JobRoleInfo}
        self.job_roles: Dict[str, JobRoleInfo] = {}

        # JobRelationships: list of relationships
        self.job_relationships: List[JobRelationshipInfo] = []

        # Constraints:
        # - Each user must have a valid current_job_id that references an existing JobRole.
        # - Career recommendations should only include valid, active job roles.
        # - Job relationships must be between defined job_ids and may be directional or bidirectional, depending on relationship_type.
        # - Data consistency between user profiles and job definitions must be maintained.

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve the full user profile using the user's unique identifier.

        Args:
            _id (str): Unique user identifier.

        Returns:
            dict:
                success: True and data with UserInfo if found,
                otherwise success: False and an error message.

        Constraints:
            - The _id must exist in the users dictionary.
        """
        user = self.users.get(_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user profile(s) by exact or partial (case-insensitive) name match.
        If 'name' is an empty string, returns all users.

        Args:
            name (str): Username or partial name string to match (case-insensitive, substring match).

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - data (List[UserInfo]): List of matching user profiles. Empty if no matches.
                - error (str, optional): Error message on failure.
        """
        if not isinstance(name, str):
            return {"success": False, "error": "Invalid name parameter type"}

        name_lower = name.strip().lower()
        results = []

        for user in self.users.values():
            if name_lower == "" or name_lower in user["name"].lower():
                results.append(user)

        return {"success": True, "data": results}

    def get_user_current_job_id(self, user_id: str) -> dict:
        """
        Fetch the current_job_id for a given user.

        Args:
            user_id (str): The unique identifier (_id) of the user.

        Returns:
            dict:
                - { "success": True, "data": current_job_id } if found and valid.
                - { "success": False, "error": reason } if not found or invalid.

        Constraints:
            - The user must exist.
            - The user's current_job_id must reference an existing job role.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        job_id = user.get("current_job_id")
        if not job_id or job_id not in self.job_roles:
            return { "success": False, "error": "Invalid or missing current_job_id for user" }
        return { "success": True, "data": job_id }

    def get_jobrole_by_id(self, job_id: str) -> dict:
        """
        Retrieve job role details by job_id.

        Args:
            job_id (str): The unique identifier of the job role.

        Returns:
            dict: {
                "success": True,
                "data": JobRoleInfo  # The job role details if found,
            }
            or
            {
                "success": False,
                "error": str  # Error explanation if the job role does not exist.
            }

        Constraints:
            - job_id must correspond to a valid JobRole in the system.
        """
        job_role = self.job_roles.get(job_id)
        if job_role is None:
            return { "success": False, "error": "JobRole not found" }
        return { "success": True, "data": job_role }

    def get_jobrole_by_title(self, title: str) -> dict:
        """
        Lookup a job role by its title.

        Args:
            title (str): The exact title of the job role to find.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": JobRoleInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "JobRole not found with the specified title"
                    }

        Constraints:
            - Title matching is case-sensitive.
            - Returns the first match if duplicates (should not occur in a properly managed system).
        """
        for jobrole in self.job_roles.values():
            if jobrole["title"] == title:
                return { "success": True, "data": jobrole }
        return { "success": False, "error": "JobRole not found with the specified title" }

    def list_all_jobroles(self) -> dict:
        """
        Return a list of all job roles in the system.

        Returns:
            dict:
                - success (bool): True if the operation succeeded.
                - data (List[JobRoleInfo]): List of job role info dicts (may be empty if no job roles are present).
        """
        all_jobroles = list(self.job_roles.values())
        return { "success": True, "data": all_jobroles }

    def get_jobrelationships_from_job(self, job_id: str, relationship_type: str = None) -> dict:
        """
        List all job relationships where the given job_id is the source (from_job_id),
        optionally filtering by relationship_type.

        Args:
            job_id (str): The job_role ID to be used as the source for relationships.
            relationship_type (str, optional): If provided, filter relationships by this type.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": List[JobRelationshipInfo]
                }
                Failure: {
                    "success": False,
                    "error": str
                }
        Constraints:
            - job_id must reference an existing JobRole.
        """
        if job_id not in self.job_roles:
            return { "success": False, "error": "JobRole does not exist" }

        results = [
            rel for rel in self.job_relationships
            if rel["from_job_id"] == job_id and (relationship_type is None or rel["relationship_type"] == relationship_type)
        ]

        return { "success": True, "data": results }

    def get_jobrelationships_to_job(self, job_id: str, relationship_type: str = None) -> dict:
        """
        Retrieve all job relationships where the given job_id is the destination (to_job_id).
        Optionally filter results by relationship_type.

        Args:
            job_id (str): The destination job role's unique identifier.
            relationship_type (str, optional): Filter for relationship type (e.g., 'promotion').

        Returns:
            dict: {
                "success": True,
                "data": List[JobRelationshipInfo]  # may be empty if no matches
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - job_id must exist in self.job_roles.
        """
        if job_id not in self.job_roles:
            return {"success": False, "error": "Job role does not exist"}

        relationships = [
            jr for jr in self.job_relationships
            if jr["to_job_id"] == job_id and (relationship_type is None or jr["relationship_type"] == relationship_type)
        ]

        return {"success": True, "data": relationships}

    def get_related_jobroles(self, job_id: str) -> dict:
        """
        Get all job roles related to a specified job_id by any JobRelationship
        (e.g., 'promotion', 'lateral move', 'related to'). Includes both outgoing
        and incoming relationships.

        Args:
            job_id (str): The job_id for which to find related job roles.

        Returns:
            dict: {
                "success": True,
                "data": List[JobRoleInfo]  # List of unique, active related job roles
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - job_id must exist in self.job_roles.
            - Only include valid, active job roles in result.
            - No duplicates in output.
        """
        if job_id not in self.job_roles:
            return {"success": False, "error": "JobRole does not exist"}

        related_job_ids = set()
        for rel in self.job_relationships:
            if rel["from_job_id"] == job_id:
                related_job_ids.add(rel["to_job_id"])
            elif rel["to_job_id"] == job_id:
                related_job_ids.add(rel["from_job_id"])

        # Remove the original job_id if present (shouldn't, but for safety)
        related_job_ids.discard(job_id)

        # Filter for only existing and active JobRoles, no duplicates
        related_jobroles = []
        for rjid in related_job_ids:
            # Check job exists
            jobrole_info = self.job_roles.get(rjid)
            if not jobrole_info:
                continue
            # Check active status
            # If is_jobrole_active is a method, call it; otherwise assume all are active
            is_active_result = (
                self.is_jobrole_active(rjid)
                if hasattr(self, "is_jobrole_active")
                else {"success": True, "active": True}
            )
            if is_active_result.get("success") and is_active_result.get("data", True):
                related_jobroles.append(jobrole_info)

        return {"success": True, "data": related_jobroles}

    def get_typical_career_path_for_job(self, job_id: str, return_titles: bool = False) -> dict:
        """
        List the typical career path for a given job_role.

        Args:
            job_id (str): The job_id of the starting job_role.
            return_titles (bool): If True, returns job_titles instead of job_ids.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # Ordered list of job_ids or job_titles found in typical_career_path.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. job not found)
            }

        Constraints:
            - The job_role must exist.
            - Only valid job_ids (present in job_roles) are returned.
        """
        if job_id not in self.job_roles:
            return {"success": False, "error": "JobRole not found"}

        path_ids = self.job_roles[job_id].get("typical_career_path", [])
        # Only include job_ids actually present in the system (valid, active job roles)
        valid_path_ids = [jid for jid in path_ids if jid in self.job_roles]

        if return_titles:
            result = [self.job_roles[jid]["title"] for jid in valid_path_ids]
        else:
            result = valid_path_ids

        return {"success": True, "data": result}

    def is_jobrole_active(self, job_id: str) -> dict:
        """
        Check if the specified job_id corresponds to a valid, active JobRole in the system.

        Args:
            job_id (str): The job role identifier to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if job_id is valid and active, False otherwise
            }

        Constraints:
            - The job_id must be present in self.job_roles to be considered active.
        """
        is_active = job_id in self.job_roles
        return { "success": True, "data": is_active }

    def add_jobrole(
        self,
        job_id: str,
        title: str,
        description: str,
        required_skills: list,
        industry: str,
        typical_career_path: list
    ) -> dict:
        """
        Add a new job role to the system.

        Args:
            job_id (str): Unique job role identifier.
            title (str): Title of the job role.
            description (str): Description of the job role.
            required_skills (List[str]): List of required skill keywords.
            industry (str): Name of the industry this job is in.
            typical_career_path (List[str]): List of job_ids representing typical career paths from this job.

        Returns:
            dict:
                - On success: {"success": True, "message": "Job role <job_id> added."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - job_id must be unique (not already in use).
            - Each id in typical_career_path (if not empty) must reference an existing job_role.
            - All fields must be present and valid.
        """
        # Check for job_id uniqueness
        if job_id in self.job_roles:
            return {"success": False, "error": f"Job role with id '{job_id}' already exists."}

        # Validate types
        if not isinstance(required_skills, list) or not all(isinstance(skill, str) for skill in required_skills):
            return {"success": False, "error": "required_skills must be a list of strings."}
        if not isinstance(typical_career_path, list) or not all(isinstance(jid, str) for jid in typical_career_path):
            return {"success": False, "error": "typical_career_path must be a list of strings."}

        # typical_career_path validation: all entries must reference valid job_roles
        invalid_refs = [jid for jid in typical_career_path if jid not in self.job_roles]
        if invalid_refs:
            return {"success": False, "error": f"typical_career_path references non-existent job_role(s): {invalid_refs}"}

        # Build the new job role
        jobrole_info = {
            "job_id": job_id,
            "title": title,
            "description": description,
            "required_skills": required_skills,
            "industry": industry,
            "typical_career_path": typical_career_path,
        }

        self.job_roles[job_id] = jobrole_info

        return {"success": True, "message": f"Job role {job_id} added."}

    def update_jobrole(
        self,
        job_id: str,
        title: str = None,
        description: str = None,
        required_skills: list = None,
        industry: str = None,
        typical_career_path: list = None
    ) -> dict:
        """
        Modify the attributes of an existing job role.

        Args:
            job_id (str): The identifier of the job role to update.
            title (str, optional): New title to set.
            description (str, optional): New description to set.
            required_skills (list, optional): List of new required skills.
            industry (str, optional): New industry string.
            typical_career_path (list, optional): List of new job_ids for career path.

        Returns:
            dict: {
                "success": True, "message": "JobRole <job_id> updated"
            } on success,
            or {
                "success": False, "error": "reason"
            } on failure.

        Constraints:
            - job_id must exist.
            - Any job_ids in typical_career_path (if provided) must exist in job_roles (data consistency).
        """
        # Check that the job_id exists
        if job_id not in self.job_roles:
            return { "success": False, "error": "JobRole does not exist" }
    
        jobrole = self.job_roles[job_id]

        # Validate typical_career_path if provided
        if typical_career_path is not None:
            for ref_id in typical_career_path:
                if ref_id not in self.job_roles:
                    return {
                        "success": False,
                        "error": f"typical_career_path contains non-existent job_id '{ref_id}'"
                    }

        # Only update fields that are provided
        if title is not None:
            jobrole["title"] = title
        if description is not None:
            jobrole["description"] = description
        if required_skills is not None:
            jobrole["required_skills"] = list(required_skills)
        if industry is not None:
            jobrole["industry"] = industry
        if typical_career_path is not None:
            jobrole["typical_career_path"] = list(typical_career_path)

        return { "success": True, "message": f"JobRole {job_id} updated" }

    def delete_jobrole(self, job_id: str) -> dict:
        """
        Remove a job role from the system.

        Args:
            job_id (str): The job role's unique identifier to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Job role '<job_id>' deleted successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Cannot delete a JobRole if any user's current_job_id references it.
            - Remove job_relationships where from_job_id or to_job_id is job_id.
            - Remove job_id from job_history of all users and from all job_roles' typical_career_path.
            - If job_id does not exist, return error.
        """
        # Check existence
        if job_id not in self.job_roles:
            return {"success": False, "error": f"Job role '{job_id}' does not exist."}

        # Check user current_job_id constraint
        for user in self.users.values():
            if user['current_job_id'] == job_id:
                return {
                    "success": False,
                    "error": f"Cannot delete job role '{job_id}': it is referenced as a current job by user '{user['_id']}'."
                }

        # Remove job_relationships involving this job_id
        self.job_relationships = [
            rel for rel in self.job_relationships
            if rel['from_job_id'] != job_id and rel['to_job_id'] != job_id
        ]

        # Remove from job_roles' typical_career_path lists
        for jr in self.job_roles.values():
            if 'typical_career_path' in jr and isinstance(jr['typical_career_path'], list):
                if job_id in jr['typical_career_path']:
                    jr['typical_career_path'] = [jid for jid in jr['typical_career_path'] if jid != job_id]

        # Remove from all users' job_history
        for user in self.users.values():
            if 'job_history' in user and isinstance(user['job_history'], list):
                if job_id in user['job_history']:
                    user['job_history'] = [jid for jid in user['job_history'] if jid != job_id]

        # Delete the job_role
        del self.job_roles[job_id]

        return {"success": True, "message": f"Job role '{job_id}' deleted successfully."}

    def add_jobrelationship(self, from_job_id: str, to_job_id: str, relationship_type: str) -> dict:
        """
        Add a new job relationship between two existing job roles.

        Args:
            from_job_id (str): JobRole ID for the source job.
            to_job_id (str): JobRole ID for the target job.
            relationship_type (str): The type of relationship (e.g., 'promotion', 'lateral move').

        Returns:
            dict: 
                On success: { "success": True, "message": "Job relationship added successfully." }
                On failure: 
                    { "success": False, "error": <error message> }

        Constraints:
            - Both job IDs must exist in the job_roles dictionary.
            - An identical relationship (from_job_id, to_job_id, relationship_type) should not already exist.
            - Relationship type is assumed arbitrary unless a schema is provided elsewhere.
        """
        # Validate job IDs
        if from_job_id not in self.job_roles:
            return {"success": False, "error": "from_job_id does not exist."}
        if to_job_id not in self.job_roles:
            return {"success": False, "error": "to_job_id does not exist."}

        # Check for duplicate relationship
        for rel in self.job_relationships:
            if (
                rel["from_job_id"] == from_job_id and
                rel["to_job_id"] == to_job_id and
                rel["relationship_type"] == relationship_type
            ):
                return {"success": False, "error": "This job relationship already exists."}

        # Add new relationship
        new_relationship: JobRelationshipInfo = {
            "from_job_id": from_job_id,
            "to_job_id": to_job_id,
            "relationship_type": relationship_type,
        }
        self.job_relationships.append(new_relationship)
        return {"success": True, "message": "Job relationship added successfully."}

    def update_jobrelationship(
        self,
        old_from_job_id: str,
        old_to_job_id: str,
        old_relationship_type: str,
        new_from_job_id: str,
        new_to_job_id: str,
        new_relationship_type: str
    ) -> dict:
        """
        Edit an existing job relationship's endpoints or type.

        Args:
            old_from_job_id (str): Source job_id of the original relationship.
            old_to_job_id (str): Target job_id of the original relationship.
            old_relationship_type (str): Type of the original relationship.
            new_from_job_id (str): New source job_id to update to.
            new_to_job_id (str): New target job_id to update to.
            new_relationship_type (str): New relationship type to update to.

        Returns:
            dict: {
                "success": True, "message": "Job relationship updated successfully"
            } or {
                "success": False, "error": "<error message>"
            }

        Constraints:
            - Original relationship must exist.
            - New job_ids (from and to) must exist in job_roles.
            - Must not duplicate an existing relationship of (from, to, type).
        """
        # Find the existing relationship index
        idx = None
        for i, jr in enumerate(self.job_relationships):
            if (jr["from_job_id"] == old_from_job_id and
                jr["to_job_id"] == old_to_job_id and
                jr["relationship_type"] == old_relationship_type):
                idx = i
                break
        if idx is None:
            return {"success": False, "error": "Original job relationship not found"}

        # Check new from/to job_ids exist
        if new_from_job_id not in self.job_roles:
            return {"success": False, "error": f"from_job_id '{new_from_job_id}' does not exist"}
        if new_to_job_id not in self.job_roles:
            return {"success": False, "error": f"to_job_id '{new_to_job_id}' does not exist"}

        # Check for duplicate relationship (excluding the one being edited)
        for i, jr in enumerate(self.job_relationships):
            if i == idx:
                continue
            if (jr["from_job_id"] == new_from_job_id and
                jr["to_job_id"] == new_to_job_id and
                jr["relationship_type"] == new_relationship_type):
                return {"success": False, "error": "A job relationship with the new attributes already exists"}

        # Apply update
        self.job_relationships[idx] = {
            "from_job_id": new_from_job_id,
            "to_job_id": new_to_job_id,
            "relationship_type": new_relationship_type
        }

        return {"success": True, "message": "Job relationship updated successfully"}

    def delete_jobrelationship(self, from_job_id: str, to_job_id: str, relationship_type: str) -> dict:
        """
        Remove a specific job relationship.

        Args:
            from_job_id (str): JobRole ID where the relationship starts.
            to_job_id (str): JobRole ID where the relationship ends.
            relationship_type (str): The type of relationship (e.g. 'promotion', 'lateral move').

        Returns:
            dict: {
                "success": True,
                "message": "Job relationship deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Job relationship not found." | "Invalid job_id(s)."
            }

        Constraints:
            - Both job IDs must reference existing JobRoles.
            - The relationship must exist before it can be deleted.
        """
        if from_job_id not in self.job_roles or to_job_id not in self.job_roles:
            return {"success": False, "error": "Invalid job_id(s)."}

        initial_count = len(self.job_relationships)
        self.job_relationships = [
            jr for jr in self.job_relationships
            if not (
                jr['from_job_id'] == from_job_id and
                jr['to_job_id'] == to_job_id and
                jr['relationship_type'] == relationship_type
            )
        ]
        if len(self.job_relationships) == initial_count:
            return {"success": False, "error": "Job relationship not found."}
        else:
            return {"success": True, "message": "Job relationship deleted successfully."}

    def update_user_current_job(self, user_id: str, new_job_id: str) -> dict:
        """
        Update the current job for a given user to a new valid JobRole.

        Args:
            user_id (str): The unique user identifier.
            new_job_id (str): The job ID to set as the user's current job.

        Returns:
            dict: {
                "success": True,
                "message": "User's current job updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The user must exist.
            - The new_job_id must reference a valid JobRole.
            - Data consistency must be maintained.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        if new_job_id not in self.job_roles:
            return {"success": False, "error": "JobRole does not exist"}
        user["current_job_id"] = new_job_id
        return {"success": True, "message": "User's current job updated"}

    def update_user_profile(
        self,
        user_id: str,
        name: str = None,
        skills: list = None,
        preferences: dict = None
    ) -> dict:
        """
        Modify user attributes such as name, skills, or preferences.

        Args:
            user_id (str): Unique ID of the user to update.
            name (str, optional): New name for the user.
            skills (List[str], optional): New list of skills.
            preferences (Dict[str, Any], optional): Updated preferences dict.

        Returns:
            dict:
              - On success:
                  { "success": True, "message": "User profile updated successfully." }
              - On failure:
                  { "success": False, "error": "<reason>" }

        Constraints:
            - User ID must exist.
            - Attribute types must be correct.
            - Only name, skills, and preferences can be updated.
            - At least one modifiable attribute must be provided.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        # No updates provided
        if name is None and skills is None and preferences is None:
            return {"success": False, "error": "No attributes provided for update."}

        user = self.users[user_id]

        # Validate and update name
        if name is not None:
            if not isinstance(name, str):
                return {"success": False, "error": "Name must be a string."}
            user["name"] = name

        # Validate and update skills
        if skills is not None:
            if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
                return {"success": False, "error": "Skills must be a list of strings."}
            user["skills"] = skills

        # Validate and update preferences
        if preferences is not None:
            if not isinstance(preferences, dict):
                return {"success": False, "error": "Preferences must be a dictionary."}
            user["preferences"] = preferences

        self.users[user_id] = user

        return {"success": True, "message": "User profile updated successfully."}


class CareerManagementPlatform(BaseEnv):
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
            if key == "is_jobrole_active":
                setattr(env, "_is_jobrole_active_state", copy.deepcopy(value))
                continue
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_current_job_id(self, **kwargs):
        return self._call_inner_tool('get_user_current_job_id', kwargs)

    def get_jobrole_by_id(self, **kwargs):
        return self._call_inner_tool('get_jobrole_by_id', kwargs)

    def get_jobrole_by_title(self, **kwargs):
        return self._call_inner_tool('get_jobrole_by_title', kwargs)

    def list_all_jobroles(self, **kwargs):
        return self._call_inner_tool('list_all_jobroles', kwargs)

    def get_jobrelationships_from_job(self, **kwargs):
        return self._call_inner_tool('get_jobrelationships_from_job', kwargs)

    def get_jobrelationships_to_job(self, **kwargs):
        return self._call_inner_tool('get_jobrelationships_to_job', kwargs)

    def get_related_jobroles(self, **kwargs):
        return self._call_inner_tool('get_related_jobroles', kwargs)

    def get_typical_career_path_for_job(self, **kwargs):
        return self._call_inner_tool('get_typical_career_path_for_job', kwargs)

    def is_jobrole_active(self, **kwargs):
        return self._call_inner_tool('is_jobrole_active', kwargs)

    def add_jobrole(self, **kwargs):
        return self._call_inner_tool('add_jobrole', kwargs)

    def update_jobrole(self, **kwargs):
        return self._call_inner_tool('update_jobrole', kwargs)

    def delete_jobrole(self, **kwargs):
        return self._call_inner_tool('delete_jobrole', kwargs)

    def add_jobrelationship(self, **kwargs):
        return self._call_inner_tool('add_jobrelationship', kwargs)

    def update_jobrelationship(self, **kwargs):
        return self._call_inner_tool('update_jobrelationship', kwargs)

    def delete_jobrelationship(self, **kwargs):
        return self._call_inner_tool('delete_jobrelationship', kwargs)

    def update_user_current_job(self, **kwargs):
        return self._call_inner_tool('update_user_current_job', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)
