# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict
from typing import List



class ProjectInfo(TypedDict):
    project_id: str
    title: str
    description: str
    owner_id: str
    upload_date: str
    metadata: dict
    conten: str  # content

class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    organization: str
    account_sta: str  # account status

class InteractionLogInfo(TypedDict):
    vent_id: str  # event id
    project_id: str
    user_id: Optional[str]
    event_type: str  # 'view' or 'download'
    timestamp: str
    metadata: dict

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Project repository platform with analytics stateful environment.
        """

        # Projects: {project_id: ProjectInfo}
        # entity: Projec, attributes: project_id, title, description, owner_id, upload_date, metadata, conten
        self.projects: Dict[str, ProjectInfo] = {}

        # Users: {_id: UserInfo}
        # entity: User, attributes: _id, name, email, organization, account_sta
        self.users: Dict[str, UserInfo] = {}

        # Interaction Logs: {vent_id: InteractionLogInfo}
        # entity: vent (InteractionLog), attributes: vent_id, project_id, user_id, event_type, timestamp, metadata
        self.interactions: Dict[str, InteractionLogInfo] = {}

        # Constraints:
        # - Projects must have a unique project_id and owner_id.
        # - Interaction logs must include a valid timestamp and reference an existing project.
        # - Only certain event types (e.g., view, download) are valid for analytic queries.
        # - Analytics data must be filterable by timeframe and project.

    def get_project_by_title(self, title: str) -> dict:
        """
        Retrieve project information using the project's title.

        Args:
            title (str): The title of the project to search for.

        Returns:
            dict: 
                - { "success": True, "data": ProjectInfo } if project found
                - { "success": False, "error": str } if not found

        Constraints:
            - No requirement for unique titles; returns first match found.
        """
        for project in self.projects.values():
            if project["title"] == title:
                return { "success": True, "data": project }
        return { "success": False, "error": "Project with given title not found" }

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve project details by unique project_id.

        Args:
            project_id (str): Unique identifier of the project.

        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo,  # Project details including metadata and content
            }
            or
            {
                "success": False,
                "error": str  # If the project does not exist
            }
        Constraints:
            - The project_id must exist in the system.
        """
        if not project_id or project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
        return {"success": True, "data": self.projects[project_id]}

    def list_all_projects(self) -> dict:
        """
        List all projects in the repository.

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]  # List of all project records (may be empty if no projects)
            }
        """
        projects_list = list(self.projects.values())
        return { "success": True, "data": projects_list }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by unique user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User information dictionary
            }
            or
            {
                "success": False,
                "error": str  # Error message if user not found
            }
        Constraints:
            - The user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": self.users[user_id]}

    def get_user_projects(self, user_id: str) -> dict:
        """
        List all projects owned by a given user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user_id must exist in the users database.
            - Returns all projects with owner_id equal to user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_projects = [
            project for project in self.projects.values() if project["owner_id"] == user_id
        ]
        return {"success": True, "data": user_projects}

    def get_project_owner_info(self, project_id: str) -> dict:
        """
        Retrieve the owner (user) information for a given project.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": UserInfo  # The project owner's full user info
                    }
                - On failure (project or owner not found):
                    {
                        "success": False,
                        "error": <error message>
                    }

        Constraints:
            - The project_id must exist in the system.
            - The project must have a valid owner_id that exists in the user records.
        """
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Project not found" }
        owner_id = project.get("owner_id")
        owner = self.users.get(owner_id)
        if not owner:
            return { "success": False, "error": "Owner not found" }
        return { "success": True, "data": owner }

    def list_interaction_logs_by_project(self, project_id: str) -> dict:
        """
        Retrieve all interaction logs (events) associated with the specified project.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict: {
                "success": True,
                "data": List[InteractionLogInfo],  # List of logs (can be empty if no events)
            }
            or
            {
                "success": False,
                "error": str  # "Project not found" if project_id invalid
            }

        Constraints:
            - The project_id must exist in the projects repository.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        logs = [
            log for log in self.interactions.values()
            if log["project_id"] == project_id
        ]

        return {"success": True, "data": logs}


    def list_interaction_logs_by_filter(
        self, 
        project_id: str, 
        event_type: str, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """
        Retrieve interaction logs filtered by project_id, event_type ('view' or 'download'), and timeframe.

        Args:
            project_id (str): The ID of the project whose logs are to be retrieved.
            event_type (str): The type of event to filter for ('view' or 'download').
            start_time (str): The inclusive start of the queried timeframe (ISO8601 format).
            end_time (str): The inclusive end of the queried timeframe (ISO8601 format).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[InteractionLogInfo]  # All matching logs, possibly empty
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - project_id must exist
            - event_type must be 'view' or 'download'
            - start_time <= end_time
            - Logs must reference the project and be within time and type filters.
        """
        # Check that the project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        # Validate event_type
        if event_type not in ("view", "download"):
            return {"success": False, "error": "Invalid event_type"}

        # Time validation (assume ISO8601 or sortable string for timestamps)
        if start_time > end_time:
            return {"success": False, "error": "Invalid timeframe"}

        result: List[InteractionLogInfo] = []
        for log in self.interactions.values():
            if (
                log["project_id"] == project_id and
                log["event_type"] == event_type and
                (start_time <= log["timestamp"] <= end_time)
            ):
                result.append(log)

        return {"success": True, "data": result}

    def count_project_events_by_type_and_timeframe(
        self, project_id: str, start_time: str, end_time: str
    ) -> dict:
        """
        Count the number of 'view' and 'download' events for a given project_id
        within the inclusive timeframe [start_time, end_time].

        Args:
            project_id (str): The project to analyze.
            start_time (str): Start of the timeframe (ISO8601 or similar, inclusive).
            end_time (str): End of the timeframe (ISO8601 or similar, inclusive).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": { "view": int, "download": int }
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Project must exist.
            - Only 'view' and 'download' event_types are counted.
            - start_time and end_time must be ordered (start <= end).
            - Time comparison is string-based (assumes ISO format).
        """
        # Check project exists
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }
    
        if start_time > end_time:
            return { "success": False, "error": "Invalid timeframe: start_time after end_time" }
    
        counts = { "view": 0, "download": 0 }
        valid_types = ("view", "download")

        for log in self.interactions.values():
            if log["project_id"] != project_id:
                continue
            if log["event_type"] not in valid_types:
                continue
            # Timed window inclusive
            ts = log["timestamp"]
            # Defensive: skip if timestamp field missing or malformed (not comparable as string)
            if not isinstance(ts, str):
                continue
            if start_time <= ts <= end_time:
                counts[log["event_type"]] += 1

        return { "success": True, "data": counts }

    def get_project_analytics_summary(self, project_id: str, start_time: str, end_time: str) -> dict:
        """
        Aggregate all analytics data (views, downloads) for a project over a specified period.

        Args:
            project_id (str): The unique identifier of the project.
            start_time (str): Start of the time window (inclusive), in ISO8601 or comparable string format.
            end_time (str): End of the time window (inclusive), in ISO8601 or comparable string format.

        Returns:
            dict: {
                "success": True,
                "data": {"view": int, "download": int}  # counts of each event type in window
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only events of type 'view' or 'download' are counted.
            - Project must exist.
            - Timeframe is inclusive (>= start_time and <= end_time).
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        valid_event_types = {"view", "download"}
        counts = {"view": 0, "download": 0}

        for log in self.interactions.values():
            if log["project_id"] != project_id:
                continue
            if log["event_type"] not in valid_event_types:
                continue
            timestamp = log["timestamp"]
            if start_time <= timestamp <= end_time:
                counts[log["event_type"]] += 1

        return {"success": True, "data": counts}

    def list_valid_event_types(self) -> dict:
        """
        Return all valid event types for analytic queries.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[str]  # List of valid event types, e.g. ["view", "download"]
                }
        Constraints:
            - The valid event types are statically set per platform policy.
        """
        valid_event_types = ["view", "download"]
        return {
            "success": True,
            "data": valid_event_types
        }

    def get_project_metadata(self, project_id: str) -> dict:
        """
        Retrieve the metadata dictionary associated with a specified project.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "data": <metadata dict>
                    }
                If project does not exist:
                    {
                        "success": False,
                        "error": "Project not found"
                    }

        Constraints:
            - The specified project_id must exist in the platform's projects.
        """
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        return {"success": True, "data": project.get("metadata", {})}

    def add_project(
        self,
        project_id: str,
        title: str,
        description: str,
        owner_id: str,
        upload_date: str,
        metadata: dict,
        conten: str
    ) -> dict:
        """
        Add a new project to the repository, enforcing unique project_id and valid owner_id.

        Args:
            project_id (str): Unique project identifier.
            title (str): Project title.
            description (str): Project description.
            owner_id (str): Must match an existing user _id.
            upload_date (str): Date of project upload (string format).
            metadata (dict): Project metadata.
            conten (str): Project content.

        Returns:
            dict: {
                "success": True,
                "message": "Project <project_id> added successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - project_id must be unique.
            - owner_id must exist in users.
        """
        if project_id in self.projects:
            return {"success": False, "error": "Project ID already exists"}

        if owner_id not in self.users:
            return {"success": False, "error": "Owner ID does not exist"}

        self.projects[project_id] = {
            "project_id": project_id,
            "title": title,
            "description": description,
            "owner_id": owner_id,
            "upload_date": upload_date,
            "metadata": metadata,
            "conten": conten
        }
        return {"success": True, "message": f"Project {project_id} added successfully"}

    def update_project_metadata(
        self,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Update a project's metadata, title, or description.

        Args:
            project_id (str): The identifier of the project to update.
            title (str, optional): New title for the project.
            description (str, optional): New description for the project.
            metadata (dict, optional): New metadata dictionary for the project.

        Returns:
            dict: {
                "success": True,
                "message": "Project metadata/title/description updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The project identified by `project_id` must exist.
            - At least one of `title`, `description`, or `metadata` must be provided.
            - Only provided fields are updated; others remain unchanged.
        """
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Project does not exist." }

        if title is None and description is None and metadata is None:
            return { "success": False, "error": "No update fields provided." }

        updated_fields = []
        if title is not None:
            project["title"] = title
            updated_fields.append("title")
        if description is not None:
            project["description"] = description
            updated_fields.append("description")
        if metadata is not None:
            project["metadata"] = metadata
            updated_fields.append("metadata")
        # Project dict in self.projects is already updated by reference

        if updated_fields:
            msg = f"Project {project_id} updated fields: {', '.join(updated_fields)}."
            return { "success": True, "message": msg }
        else:
            # Shouldn't be possible, but for safety
            return { "success": False, "error": "No valid update fields provided." }

    def update_project_content(self, project_id: str, new_content: str) -> dict:
        """
        Update the content ('conten') of a project.

        Args:
            project_id (str): The ID of the project to update.
            new_content (str): The new content to set for the project.

        Returns:
            dict: {
                "success": True,
                "message": "Project content updated."
            }
            or
            {
                "success": False,
                "error": "Project not found."
            }

        Constraints:
            - The 'project_id' must exist in self.projects.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project not found." }
        self.projects[project_id]['conten'] = new_content
        return { "success": True, "message": "Project content updated." }

    def delete_project(self, project_id: str) -> dict:
        """
        Remove a project and its associated interaction logs from the system.

        Args:
            project_id (str): The unique identifier of the project to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Project <project_id> deleted"
            }
            or
            {
                "success": False,
                "error": "Project does not exist"
            }

        Constraints:
            - The project must exist.
            - All interaction logs related to the project must be deleted for consistency.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        # Remove the project
        del self.projects[project_id]

        # Remove all interaction logs referencing this project
        logs_to_delete = [vent_id for vent_id, log in self.interactions.items() if log["project_id"] == project_id]
        for vent_id in logs_to_delete:
            del self.interactions[vent_id]

        return { "success": True, "message": f"Project {project_id} deleted" }

    def add_user(self, _id: str, name: str, email: str, organization: str, account_sta: str) -> dict:
        """
        Add a new user to the platform, ensuring the user ID is unique.

        Args:
            _id (str): Unique user identifier.
            name (str): User's name.
            email (str): User's email.
            organization (str): User's organization.
            account_sta (str): User's account status.

        Returns:
            dict:
                - On success: { "success": True, "message": "User added successfully" }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - User ID (_id) must be unique.
            - All fields required (no empty values).
        """
        # Validate input presence
        if not all([_id, name, email, organization, account_sta]):
            return {"success": False, "error": "All fields are required"}

        # Check for uniqueness of user ID
        if _id in self.users:
            return {"success": False, "error": "User with this ID already exists"}

        user_info = {
            "_id": _id,
            "name": name,
            "email": email,
            "organization": organization,
            "account_sta": account_sta
        }
        self.users[_id] = user_info
        return {"success": True, "message": "User added successfully"}

    def update_user_info(self, _id: str, name: str = None, email: str = None, organization: str = None, account_sta: str = None) -> dict:
        """
        Modify a user’s information or account status.

        Args:
            _id (str): The unique user ID to update.
            name (str, optional): New name for the user.
            email (str, optional): New email address.
            organization (str, optional): New organization.
            account_sta (str, optional): New account status.

        Returns:
            dict: {
                "success": True,
                "message": str  # Human-readable summary
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User _id must exist.
            - Only updates fields present in UserInfo.
            - Ignores invalid or unspecified fields.
            - If no fields are provided, it's treated as a successful no-op if user exists.
        """
        if _id not in self.users:
            return {"success": False, "error": "User not found."}

        # Update user fields if new values are provided
        update_fields = {'name': name, 'email': email, 'organization': organization, 'account_sta': account_sta}
        user_info = self.users[_id]

        updated = []
        for field, value in update_fields.items():
            if value is not None and field in user_info:
                user_info[field] = value
                updated.append(field)

        self.users[_id] = user_info

        if updated:
            return {"success": True, "message": f"User info for {_id} updated: {', '.join(updated)}."}
        else:
            return {"success": True, "message": f"No changes made to user {_id}."}

    def add_interaction_log(
        self,
        vent_id: str,
        project_id: str,
        event_type: str,
        timestamp: str,
        metadata: dict,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Log a new interaction event (view or download) for a project.

        Args:
            vent_id (str): Unique event ID for the log.
            project_id (str): The project ID the event references (must exist).
            event_type (str): The event type, only 'view' or 'download' allowed.
            timestamp (str): When the event occurred (must be non-empty).
            metadata (dict): Additional metadata for the event.
            user_id (Optional[str]): The user performing the event (can be None or omitted).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Interaction log added successfully"}
                On failure:
                    {"success": False, "error": "...reason..."}
        Constraints:
            - project_id must refer to an existing project.
            - event_type must be 'view' or 'download'.
            - vent_id must be unique within the interactions log.
            - timestamp must be provided (non-empty).
            - user_id is optional and need not exist in users.
        """
        # Check unique event id
        if vent_id in self.interactions:
            return { "success": False, "error": "Duplicate event id (vent_id) detected." }

        # Validate project
        if project_id not in self.projects:
            return { "success": False, "error": "Referenced project_id does not exist." }

        # Validate event_type
        if event_type not in ("view", "download"):
            return { "success": False, "error": "Invalid event_type. Only 'view' or 'download' are allowed." }

        # Validate timestamp
        if not isinstance(timestamp, str) or not timestamp.strip():
            return { "success": False, "error": "Missing or invalid timestamp." }

        # Create log entry
        log_entry: InteractionLogInfo = {
            "vent_id": vent_id,
            "project_id": project_id,
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "metadata": metadata or {},
        }
        self.interactions[vent_id] = log_entry
        return { "success": True, "message": "Interaction log added successfully" }

    def delete_interaction_log(self, vent_id: str) -> dict:
        """
        Remove a specific interaction/event log by its event (vent) id.

        Args:
            vent_id (str): Unique identifier of the interaction log to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Interaction log deleted."
            }
            or
            {
                "success": False,
                "error": "Interaction log not found."
            }

        Constraints:
            - The interaction log must exist.
            - No exceptions are raised; errors are reported in the return dictionary.
        """
        if vent_id not in self.interactions:
            return { "success": False, "error": "Interaction log not found." }
        del self.interactions[vent_id]
        return { "success": True, "message": "Interaction log deleted." }

    def update_interaction_log_metadata(self, vent_id: str, metadata: dict) -> dict:
        """
        Modify the metadata/details of an existing interaction log.

        Args:
            vent_id (str): The unique event ID of the interaction log to update.
            metadata (dict): The new metadata to assign to the interaction log.

        Returns:
            dict:
                - On success: { "success": True, "message": "Interaction log metadata updated successfully." }
                - On failure:
                    { "success": False, "error": "Interaction log does not exist." }
                    { "success": False, "error": "Invalid metadata: must be a dictionary." }
        Constraints:
            - The provided vent_id must exist in the environment.
            - The provided metadata must be a valid dictionary.
        """
        if vent_id not in self.interactions:
            return { "success": False, "error": "Interaction log does not exist." }

        if not isinstance(metadata, dict):
            return { "success": False, "error": "Invalid metadata: must be a dictionary." }

        self.interactions[vent_id]["metadata"] = metadata
        return { "success": True, "message": "Interaction log metadata updated successfully." }

    def bulk_delete_logs_for_project(self, project_id: str) -> dict:
        """
        Delete all interaction logs associated with the specified project.

        Args:
            project_id (str): Unique identifier of the project whose logs will be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Deleted X interaction logs for project <project_id>."
            }
            or
            {
                "success": False,
                "error": "<reason/error>"
            }

        Constraints:
            - Project must exist in the platform (self.projects).
            - Only interaction logs for this project will be affected.
        """
        if project_id not in self.projects:
            return {
                "success": False,
                "error": f"Project with id '{project_id}' does not exist."
            }

        # Find logs to delete
        logs_to_delete = [
            vent_id for vent_id, log in self.interactions.items()
            if log['project_id'] == project_id
        ]
        deleted_count = len(logs_to_delete)

        for vent_id in logs_to_delete:
            del self.interactions[vent_id]

        return {
            "success": True,
            "message": f"Deleted {deleted_count} interaction logs for project '{project_id}'."
        }


class ProjectRepositoryAnalyticsPlatform(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_projects(self, **kwargs):
        return self._call_inner_tool('get_user_projects', kwargs)

    def get_project_owner_info(self, **kwargs):
        return self._call_inner_tool('get_project_owner_info', kwargs)

    def list_interaction_logs_by_project(self, **kwargs):
        return self._call_inner_tool('list_interaction_logs_by_project', kwargs)

    def list_interaction_logs_by_filter(self, **kwargs):
        return self._call_inner_tool('list_interaction_logs_by_filter', kwargs)

    def count_project_events_by_type_and_timeframe(self, **kwargs):
        return self._call_inner_tool('count_project_events_by_type_and_timeframe', kwargs)

    def get_project_analytics_summary(self, **kwargs):
        return self._call_inner_tool('get_project_analytics_summary', kwargs)

    def list_valid_event_types(self, **kwargs):
        return self._call_inner_tool('list_valid_event_types', kwargs)

    def get_project_metadata(self, **kwargs):
        return self._call_inner_tool('get_project_metadata', kwargs)

    def add_project(self, **kwargs):
        return self._call_inner_tool('add_project', kwargs)

    def update_project_metadata(self, **kwargs):
        return self._call_inner_tool('update_project_metadata', kwargs)

    def update_project_content(self, **kwargs):
        return self._call_inner_tool('update_project_content', kwargs)

    def delete_project(self, **kwargs):
        return self._call_inner_tool('delete_project', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def add_interaction_log(self, **kwargs):
        return self._call_inner_tool('add_interaction_log', kwargs)

    def delete_interaction_log(self, **kwargs):
        return self._call_inner_tool('delete_interaction_log', kwargs)

    def update_interaction_log_metadata(self, **kwargs):
        return self._call_inner_tool('update_interaction_log_metadata', kwargs)

    def bulk_delete_logs_for_project(self, **kwargs):
        return self._call_inner_tool('bulk_delete_logs_for_project', kwargs)

