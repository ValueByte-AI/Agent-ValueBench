# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import time
from datetime import datetime



class JobInfo(TypedDict):
    job_id: str
    name: str
    creator_id: str
    created_at: str
    status: str
    priority: int
    scheduled_time: str
    parameters: Dict[str, Any]
    execution_history: List[Dict[str, Any]]

class UserInfo(TypedDict):
    _id: str
    username: str
    permission: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Job Scheduling and Management System environment.
        """

        # Jobs: {job_id: JobInfo}
        # Maps job_id to job details and execution history.
        self.jobs: Dict[str, JobInfo] = {}

        # Users: {_id: UserInfo}
        # Maps user _id to user details and permissions.
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each job_id must be unique.
        # - Only authorized users may query or manipulate specific jobs.
        # - Status values are from a controlled set (e.g., pending, running, completed, failed, canceled).
        # - Execution history must accurately log all status or parameter changes for each job.

    def get_job_by_id(self, job_id: str) -> dict:
        """
        Retrieve detailed metadata and historical records for a job given its job_id.

        Args:
            job_id (str): The unique job identifier to query.

        Returns:
            dict: {
                "success": True,
                "data": JobInfo  # Complete job info, including metadata and execution history
            }
            or
            {
                "success": False,
                "error": str  # E.g., "Job not found"
            }

        Constraints:
            - job_id must exist in the system.
            - (Authorization is not enforced unless a user context is provided.)
        """
        job_info = self.jobs.get(job_id)
        if not job_info:
            return { "success": False, "error": "Job not found" }
        return { "success": True, "data": job_info }

    def list_all_jobs(self) -> dict:
        """
        Retrieve a list of all jobs managed by the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[JobInfo]  # List may be empty if no jobs are present
            }

        Constraints:
            - Returns all jobs regardless of creator or status, with full JobInfo.
        """
        job_list = list(self.jobs.values())
        return {"success": True, "data": job_list}

    def list_jobs_by_creator(self, creator_id: str = None, username: str = None) -> dict:
        """
        List all jobs created by a specific user, referenced by either creator_id or username.

        Args:
            creator_id (str, optional): The user's unique ID to filter jobs by. Default None.
            username (str, optional): The user's username to filter jobs by. Default None.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[JobInfo]}  # May be empty if none found.
                On error:
                    {"success": False, "error": str}

        Constraints:
            - At least one of creator_id or username must be provided.
            - If username is given, must resolve to a valid user.
        """
        if not creator_id and not username:
            return {"success": False, "error": "Must provide either creator_id or username."}

        resolved_creator_id = creator_id
        if not resolved_creator_id and username:
            # Find user with this username
            user = next((u for u in self.users.values() if u["username"] == username), None)
            if not user:
                return {"success": False, "error": f"User with username '{username}' not found."}
            resolved_creator_id = user["_id"]

        result = [
            job_info for job_info in self.jobs.values()
            if job_info["creator_id"] == resolved_creator_id
        ]

        return {"success": True, "data": result}

    def get_job_status(self, job_id: str, user_id: str) -> dict:
        """
        Retrieve the current status of a specific job, only if the user is authorized.

        Args:
            job_id (str): Unique identifier of the job.
            user_id (str): Unique identifier of the user requesting the status.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "data": {
                            "job_id": str,
                            "status": str
                        }
                    }
                Failure (job not found, user not found, or not authorized):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Each job_id must be unique.
            - Only authorized users (e.g., creator of the job or admins) may query the status.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Check if job exists
        if job_id not in self.jobs:
            return { "success": False, "error": "Job not found" }

        job = self.jobs[job_id]
        user = self.users[user_id]

        # Authorization: allow if user is creator or has admin permission
        if user["permission"] != "admin" and user["_id"] != job["creator_id"]:
            return { "success": False, "error": "Permission denied" }

        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": job["status"]
            }
        }

    def get_job_execution_history(self, job_id: str, requester_id: str) -> dict:
        """
        Fetch the execution history (status and parameter change log) of a specified job.

        Args:
            job_id (str): The identifier of the job whose execution history is requested.
            requester_id (str): User ID of requester, for access control.

        Returns:
            dict: 
                {"success": True, "data": execution_history} on success,
                or {"success": False, "error": error_message} on failure.

        Constraints:
            - Only authorized users may access job information.
            - job_id must exist.
        """
        job = self.jobs.get(job_id)
        if job is None:
            return {"success": False, "error": "Job not found"}
    
        user = self.users.get(requester_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        # Permission check: allow if admin or creator
        if user["permission"] != "admin" and requester_id != job["creator_id"]:
            return {"success": False, "error": "Permission denied"}

        # Return execution history
        return {"success": True, "data": job.get("execution_history", [])}

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user details (including _id and permissions) by username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": UserInfo  # The full user information dict
                }
            or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g., "User not found"
                }
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details, including permissions, by internal user _id.

        Args:
            user_id (str): The unique internal user identifier (_id).

        Returns:
            dict:
                - {"success": True, "data": UserInfo} if user exists
                - {"success": False, "error": "User not found"} if user does not exist

        Constraints:
            - Each user_id must be unique in the system.
            - No authorization check needed for this query.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user}

    def check_user_permission_for_job(self, user_id: str, job_id: str) -> dict:
        """
        Determine whether a user is authorized to query or manipulate a given job.

        Args:
            user_id (str): The user's unique identifier (_id).
            job_id (str): The job's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": bool   # True if permitted, False if not.
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g., user or job does not exist
            }

        Constraints:
            - User must exist.
            - Job must exist.
            - Permissions: 'admin' can access any job. Others may only access jobs they created.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        job = self.jobs.get(job_id)
        if not job:
            return {"success": False, "error": "Job does not exist"}

        # Example permission logic
        if user["permission"] == "admin":
            return {"success": True, "data": True}

        if job["creator_id"] == user_id:
            return {"success": True, "data": True}

        # Default: no permission
        return {"success": True, "data": False}

    def create_job(
        self,
        job_id: str,
        name: str,
        creator_id: str,
        priority: int,
        scheduled_time: str,
        parameters: Dict[str, Any],
        created_at: str = None,
        status: str = None
    ) -> dict:
        """
        Add a new job to the system, ensuring job_id uniqueness, creator validity, controlled initial status, and initial execution history record.

        Args:
            job_id (str): Unique identifier for the job.
            name (str): Descriptive job name.
            creator_id (str): User ID of the job creator (must exist).
            priority (int): Job priority.
            scheduled_time (str): Scheduled execution time.
            parameters (Dict[str, Any]): Job parameters/config.
            created_at (str, optional): Job creation datetime (default: now as ISO string).
            status (str, optional): Initial status (default: "pending" and must be valid).

        Returns:
            dict: {
                "success": True,
                "message": f"Job {job_id} created successfully."
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - job_id must be unique.
            - Only existing users can create jobs.
            - Status must be in allowed set: {"pending", "running", "completed", "failed", "canceled"}.
            - Execution history must start with creation event.
        """

        allowed_statuses = {"pending", "running", "completed", "failed", "canceled"}

        # Check for uniqueness
        if job_id in self.jobs:
            return {"success": False, "error": "Job ID already exists."}

        # Check creator validity
        user = self.users.get(creator_id)
        if not user:
            return {"success": False, "error": "Creator user does not exist."}

        # Minimal permissions check (user must exist; configurable for more)
        # Could check if user["permission"] in {"submit", "admin"}, etc.

        # Default status is 'pending'
        job_status = status if status is not None else "pending"
        if job_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid job status. Allowed: {allowed_statuses}"}

        # Set created_at
        created_time = created_at if created_at else datetime.utcnow().isoformat()

        # Initial execution history
        execution_history = [{
            "timestamp": created_time,
            "event": "created",
            "creator_id": creator_id,
            "new_status": job_status
        }]

        job_info: JobInfo = {
            "job_id": job_id,
            "name": name,
            "creator_id": creator_id,
            "created_at": created_time,
            "status": job_status,
            "priority": priority,
            "scheduled_time": scheduled_time,
            "parameters": parameters,
            "execution_history": execution_history
        }

        self.jobs[job_id] = job_info

        return {
            "success": True,
            "message": f"Job {job_id} created successfully."
        }

    def update_job_status(self, job_id: str, new_status: str, user_id: str) -> dict:
        """
        Change a job's status (pending, running, completed, failed, canceled),
        logging the change in execution history.

        Args:
            job_id (str): The job identifier.
            new_status (str): The status to set ("pending", "running", "completed", "failed", "canceled").
            user_id (str): The user requesting the change.

        Returns:
            dict: {
                "success": True,
                "message": "Job <job_id> status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Only authorized users may manipulate the job.
            - Status must be one of the controlled set.
            - Execution history is appended with status change info (timestamp, user, from/to).
        """

        # Allowed statuses
        allowed_statuses = {"pending", "running", "completed", "failed", "canceled"}

        # Check job exists
        job = self.jobs.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Authorization: Only allow if user is creator or has 'admin' permission
        if user_id != job["creator_id"] and user.get("permission") != "admin":
            return {"success": False, "error": "User not authorized to update this job"}

        # Validate new status
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status: {new_status}"}

        old_status = job["status"]
        # Update status
        job["status"] = new_status

        # Log into execution history
        entry = {
            "timestamp": time.time(),
            "action": "status_update",
            "user_id": user_id,
            "from": old_status,
            "to": new_status,
        }
        job["execution_history"].append(entry)

        return {
            "success": True,
            "message": f"Job {job_id} status updated to {new_status}."
        }


    def update_job_parameters(self, job_id: str, new_parameters: dict, user_id: str) -> dict:
        """
        Modify job parameters and record the change in job execution history.

        Args:
            job_id (str): ID of job to update.
            new_parameters (dict): The new parameters to set for the job.
            user_id (str): The user performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": "Job parameters updated and change recorded in execution history."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Job must exist.
            - User must exist and must be authorized ("admin" or job creator).
            - Execution history is updated with the change.
            - Parameters must be a dict.
        """

        # Check job exists
        if job_id not in self.jobs:
            return { "success": False, "error": "Job not found" }

        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        job = self.jobs[job_id]
        user = self.users[user_id]

        # Permission check: user must be admin or creator of job
        if user["permission"] != "admin" and user["_id"] != job["creator_id"]:
            return { "success": False, "error": "Permission denied" }

        if not isinstance(new_parameters, dict):
            return { "success": False, "error": "Parameters must be a dictionary" }

        old_parameters = job.get("parameters", {}).copy()

        # Update parameters
        job["parameters"] = new_parameters.copy()  # Use copy to avoid reference issues

        # Record in execution_history
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "update_parameters",
            "user_id": user_id,
            "old_parameters": old_parameters,
            "new_parameters": new_parameters
        }
        job.setdefault("execution_history", []).append(history_entry)

        return {
            "success": True,
            "message": "Job parameters updated and change recorded in execution history."
        }

    def add_execution_history_entry(self, job_id: str, event: Dict[str, Any]) -> dict:
        """
        Append a new event (status/parameter/user action) to a job’s execution history for auditing.

        Args:
            job_id (str): Identifier of the job to modify.
            event (Dict[str, Any]): The event/audit record to append (should include relevant info such as timestamp, user, action, etc.).

        Returns:
            dict:
                - {"success": True, "message": "Execution history entry added to job <job_id>."}
                - {"success": False, "error": "Job not found."}

        Constraints:
            - The job must exist (job_id valid).
            - Appends atomically to the job's execution_history.
        """
        job = self.jobs.get(job_id)
        if job is None:
            return {"success": False, "error": "Job not found."}

        if not isinstance(event, dict):
            return {"success": False, "error": "Event must be a dict."}

        job["execution_history"].append(event)
        return {"success": True, "message": f"Execution history entry added to job {job_id}."}

    def delete_job(self, job_id: str, requester_id: str) -> dict:
        """
        Remove a job from the system. Only an authorized user (admin) can perform this operation.

        Args:
            job_id (str): The ID of the job to delete.
            requester_id (str): The ID of the user making the delete request.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Job <job_id> deleted." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Each job_id must exist.
            - Only users with permission == 'admin' can delete jobs.
        """
        # Check whether requester exists
        if requester_id not in self.users:
            return {"success": False, "error": "Requester user does not exist."}

        requester_info = self.users[requester_id]
        if requester_info["permission"] != "admin":
            return {"success": False, "error": "Permission denied. Only admin can delete jobs."}

        # Check whether job exists
        if job_id not in self.jobs:
            return {"success": False, "error": "Job does not exist."}

        # Optionally, could log deletion info to some audit log here.

        del self.jobs[job_id]
        return {"success": True, "message": f"Job {job_id} deleted."}

    def reschedule_job(self, job_id: str, new_scheduled_time: str, user_id: str) -> dict:
        """
        Change the scheduled_time of a job and record the update in the execution history.

        Args:
            job_id (str): The ID of the job to be rescheduled.
            new_scheduled_time (str): The new scheduled time (expected ISO 8601 string).
            user_id (str): The ID of the user attempting the operation.

        Returns:
            dict:
                success: True and a message on success,
                or
                success: False and error describing the issue.

        Constraints:
            - Only authorized users may reschedule a job.
            - The job must exist.
            - The user must exist.
            - Execution history is appended with a rescheduling entry.
        """
        # Verify job exists
        job = self.jobs.get(job_id)
        if job is None:
            return {"success": False, "error": "Job does not exist"}

        # Verify user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}

        # Permission check (for demo: creator or user.permission == 'admin')
        if not (job["creator_id"] == user_id or user.get("permission") == "admin"):
            return {"success": False, "error": "User not authorized to reschedule this job"}

        old_scheduled_time = job["scheduled_time"]
        job["scheduled_time"] = new_scheduled_time

        # Record in execution history
        entry = {
            "event": "rescheduled",
            "by_user_id": user_id,
            "timestamp": "now",  # In real code, use current time
            "old_scheduled_time": old_scheduled_time,
            "new_scheduled_time": new_scheduled_time,
        }
        job["execution_history"].append(entry)

        return {
            "success": True,
            "message": (
                f"Job {job_id} rescheduled from {old_scheduled_time} to {new_scheduled_time} by user {user_id}."
            )
        }


class JobSchedulingManagementSystem(BaseEnv):
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

    def get_job_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_by_id', kwargs)

    def list_all_jobs(self, **kwargs):
        return self._call_inner_tool('list_all_jobs', kwargs)

    def list_jobs_by_creator(self, **kwargs):
        return self._call_inner_tool('list_jobs_by_creator', kwargs)

    def get_job_status(self, **kwargs):
        return self._call_inner_tool('get_job_status', kwargs)

    def get_job_execution_history(self, **kwargs):
        return self._call_inner_tool('get_job_execution_history', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_permission_for_job(self, **kwargs):
        return self._call_inner_tool('check_user_permission_for_job', kwargs)

    def create_job(self, **kwargs):
        return self._call_inner_tool('create_job', kwargs)

    def update_job_status(self, **kwargs):
        return self._call_inner_tool('update_job_status', kwargs)

    def update_job_parameters(self, **kwargs):
        return self._call_inner_tool('update_job_parameters', kwargs)

    def add_execution_history_entry(self, **kwargs):
        return self._call_inner_tool('add_execution_history_entry', kwargs)

    def delete_job(self, **kwargs):
        return self._call_inner_tool('delete_job', kwargs)

    def reschedule_job(self, **kwargs):
        return self._call_inner_tool('reschedule_job', kwargs)

