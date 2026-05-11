# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
from typing import Dict



class TaskInfo(TypedDict):
    task_id: str
    title: str
    description: str
    assigned_user_id: str
    status: str
    deadline: str
    dependency_ids: List[str]
    project_id: str

class JobInfo(TypedDict):
    job_id: str
    title: str
    description: str
    assigned_user_id: str
    status: str
    deadline: str
    dependency_ids: List[str]
    project_id: str

class UserInfo(TypedDict):
    user_id: str  # "_id" from original, renamed for clarity
    name: str
    email: str
    role: str
    account_status: str  # corrected from "account_sta"

class ProjectInfo(TypedDict):
    project_id: str
    name: str
    description: str
    status: str
    owner_user_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Tasks: {task_id: TaskInfo}
        self.tasks: Dict[str, TaskInfo] = {}

        # Jobs: {job_id: JobInfo}
        self.jobs: Dict[str, JobInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Constraints:
        # - Task and job status can only take approved values (e.g., "open," "in progress," "completed").
        # - Deadlines must be valid time values and can only be assigned to existing tasks/jobs.
        # - Dependencies can only reference existing tasks or jobs.
        # - Each task or job should belong to a valid project.
        # - Only users with valid accounts can be assigned to tasks/jobs.

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Retrieve all information for a specific task by its ID.

        Args:
            task_id (str): The unique identifier for the task.

        Returns:
            dict: {
                "success": True,
                "data": TaskInfo,  # Information about the task
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., task not found
            }

        Constraints:
            - Task must exist in the system.
        """
        task_info = self.tasks.get(task_id)
        if task_info is None:
            return { "success": False, "error": "Task not found" }
        return { "success": True, "data": task_info }

    def get_job_by_id(self, job_id: str) -> dict:
        """
        Retrieve all information for a specific job by its ID.

        Args:
            job_id (str): The unique identifier of the job.

        Returns:
            dict:
                success: True and data containing JobInfo if found,
                else success: False and an error message.
                Example:
                    {"success": True, "data": JobInfo}
                    {"success": False, "error": "Job not found"}

        Constraints:
            - job_id must exist in the jobs dictionary.
        """
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        return {"success": True, "data": self.jobs[job_id]}

    def list_tasks_for_project(self, project_id: str) -> dict:
        """
        Retrieve all tasks belonging to the specified project.

        Args:
            project_id (str): The ID of the project for which to retrieve tasks.

        Returns:
            dict: 
                - On success: {"success": True, "data": List[TaskInfo]}
                - On failure: {"success": False, "error": str}
    
        Constraints:
            - The project must exist in the system (project_id in self.projects).
            - No permissions are checked in this query.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        tasks = [
            task_info for task_info in self.tasks.values()
            if task_info["project_id"] == project_id
        ]
    
        return {"success": True, "data": tasks}

    def list_jobs_for_project(self, project_id: str) -> dict:
        """
        Retrieve all jobs assigned to the specified project.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict:
                success: True and data: list of JobInfo (may be empty if no jobs)
                or
                success: False and error: description (e.g., project does not exist)

        Constraints:
            - The given project_id must correspond to an existing project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        jobs = [
            job_info for job_info in self.jobs.values()
            if job_info["project_id"] == project_id
        ]
        return { "success": True, "data": jobs }

    def list_tasks_assigned_to_user(self, user_id: str) -> dict:
        """
        Retrieve all tasks currently assigned to a specific user.

        Args:
            user_id (str): ID of the user whose assigned tasks are to be listed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TaskInfo],  # may be empty if user has no assigned tasks
                    }
                On error:
                    {
                        "success": False,
                        "error": str,  # e.g., "User does not exist"
                    }

        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        assigned_tasks = [task for task in self.tasks.values() if task["assigned_user_id"] == user_id]
        return {"success": True, "data": assigned_tasks}

    def list_jobs_assigned_to_user(self, user_id: str) -> dict:
        """
        Retrieve all jobs assigned to a specific user.

        Args:
            user_id (str): The ID of the user whose jobs are to be retrieved.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[JobInfo],  # List of jobs assigned to the user (possibly empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of the error (e.g., user does not exist)
                    }

        Constraints:
            - The given user_id must refer to an existing user.
            - No filtering on account status; returns jobs for the user regardless.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        assigned_jobs = [
            job_info for job_info in self.jobs.values()
            if job_info["assigned_user_id"] == user_id
        ]
        return {
            "success": True,
            "data": assigned_jobs
        }

    def get_task_status(self, task_id: str) -> dict:
        """
        Retrieve the current status string of a given task.

        Args:
            task_id (str): The unique identifier for the task.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status of the task (e.g., "open", "in progress", "completed", etc.)
            }
            or
            {
                "success": False,
                "error": str  # Reason the operation failed (e.g., task not found)
            }
        Constraints:
            - The task_id must reference an existing task.
        """
        task = self.tasks.get(task_id)
        if task is None:
            return { "success": False, "error": "Task not found" }
        return { "success": True, "data": task["status"] }

    def get_job_status(self, job_id: str) -> dict:
        """
        Retrieve the current status of the specified job.

        Args:
            job_id (str): The unique identifier for the job.

        Returns:
            dict: {
                "success": True,
                "data": str  # The current status of the job
            }
            or
            {
                "success": False,
                "error": str  # Error message if job not found
            }

        Constraints:
            - The job must exist in the platform.
        """
        job = self.jobs.get(job_id)
        if not job:
            return { "success": False, "error": "Job not found" }
        return { "success": True, "data": job["status"] }

    def get_task_dependencies(self, task_id: str) -> dict:
        """
        Retrieve the dependencies for a task.

        Args:
            task_id (str): The ID of the task whose dependencies are to be retrieved.

        Returns:
            dict:
                - success: True, data: List[str] of dependency IDs (may be empty if no dependencies)
                - success: False, error: str description if task not found

        Constraints:
            - The specified task must exist in the system.
            - Enforced at update/creation: All dependencies reference valid tasks/jobs.
        """
        if task_id not in self.tasks:
            return { "success": False, "error": "Task not found" }
        dependencies = self.tasks[task_id]["dependency_ids"]
        return { "success": True, "data": dependencies }

    def get_job_dependencies(self, job_id: str) -> dict:
        """
        Retrieve the list of dependency IDs for a specified job.

        Args:
            job_id (str): The unique identifier for the job.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of dependency IDs (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Job does not exist"
            }

        Constraints:
            - The job must exist.
        """
        job = self.jobs.get(job_id)
        if not job:
            return { "success": False, "error": "Job does not exist" }

        dependencies = job.get("dependency_ids", [])
        return { "success": True, "data": dependencies }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve all information for a user by user ID.

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
                "error": str  # Error message (e.g., user not found)
            }

        Constraints:
            - The user_id must exist in the platform.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve all information for a project given its project_id.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": ProjectInfo  # all info for the project,
                }
                or
                {
                    "success": False,
                    "error": "Project not found"
                }

        Constraints:
            - The project_id must exist in the self.projects dictionary.
        """
        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": "Project not found"}
        return {"success": True, "data": project}

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Check whether a user's account is active and valid.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "account_status": str  # e.g., "active", "inactive", etc.
                        }
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": { "user_id": user_id, "account_status": user["account_status"] } }

    def update_task_status(self, task_id: str, new_status: str) -> dict:
        """
        Change the status of a task (only to approved values).

        Args:
            task_id (str): The unique identifier of the task to update.
            new_status (str): New status value ("open", "in progress", "completed").

        Returns:
            dict:
                - {"success": True, "message": "Task status updated to <new_status>"}
                - {"success": False, "error": "<reason>"}
    
        Constraints:
            - Task must exist in the system.
            - new_status must be in the set of approved values.
        """

        approved_statuses = {"open", "in progress", "completed"}

        if task_id not in self.tasks:
            return { "success": False, "error": "Task not found" }

        if new_status not in approved_statuses:
            return { "success": False, "error": "Invalid status value" }

        self.tasks[task_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Task status updated to {new_status}"
        }

    def update_job_status(self, job_id: str, new_status: str) -> dict:
        """
        Update the status of a job, only to approved status values.

        Args:
            job_id (str): The ID of the job to update.
            new_status (str): The desired status value ("open", "in progress", "completed").

        Returns:
            dict: 
              - On success: { "success": True, "message": "Job status updated." }
              - On error: { "success": False, "error": <reason> }

        Constraints:
            - job_id must reference an existing job.
            - new_status must be one of the approved status values.
        """
        APPROVED_JOB_STATUSES = {"open", "in progress", "completed"}

        if job_id not in self.jobs:
            return { "success": False, "error": "Job not found." }
        if new_status not in APPROVED_JOB_STATUSES:
            return { "success": False, "error": f"Invalid job status: {new_status}." }

        self.jobs[job_id]['status'] = new_status
        return { "success": True, "message": "Job status updated." }

    def assign_task_to_user(self, task_id: str, user_id: str) -> dict:
        """
        Assign or re-assign a task to a user with a valid account.

        Args:
            task_id (str): The ID of the task to be assigned.
            user_id (str): The ID of the user to assign the task to.

        Returns:
            dict: {
              "success": True,
              "message": "Task <task_id> assigned to user <user_id>."
            } on success,
            or {
              "success": False,
              "error": "<reason>"
            } on error.

        Constraints:
            - Task must exist.
            - User must exist.
            - User must have a valid account_status (e.g., 'active').
        """
        # Check for task existence
        if task_id not in self.tasks:
            return { "success": False, "error": f"Task with ID '{task_id}' does not exist." }

        # Check for user existence
        if user_id not in self.users:
            return { "success": False, "error": f"User with ID '{user_id}' does not exist." }

        # Check if user account is valid (assuming "active" is required)
        user_info = self.users[user_id]
        if user_info.get("account_status", "").lower() != "active":
            return { "success": False, "error": f"User '{user_id}' does not have an active account." }

        # Assign the task
        self.tasks[task_id]["assigned_user_id"] = user_id

        return {
            "success": True,
            "message": f"Task '{task_id}' assigned to user '{user_id}'."
        }

    def assign_job_to_user(self, job_id: str, user_id: str) -> dict:
        """
        Assign or re-assign a job to a user with a valid account.

        Args:
            job_id (str): The ID of the job to assign.
            user_id (str): The user ID to whom the job will be assigned.

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
            - The job must exist.
            - The user must exist and have a valid account status (e.g., "active").
        """
        job = self.jobs.get(job_id)
        if not job:
            return {"success": False, "error": f"Job {job_id} does not exist"}
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": f"User {user_id} does not exist"}
        if user.get("account_status", "").lower() != "active":
            return {"success": False, "error": f"User {user_id} does not have a valid (active) account"}

        job["assigned_user_id"] = user_id
        return {
            "success": True,
            "message": f"Job {job_id} assigned to user {user_id}"
        }


    def update_task_deadline(self, task_id: str, new_deadline: str) -> dict:
        """
        Set or modify a task's deadline.

        Args:
            task_id (str): The unique identifier of the task to update.
            new_deadline (str): The new deadline to assign. Must be a valid ISO 8601 time string.

        Returns:
            dict:
                On success: { "success": True, "message": "Task deadline updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The task must exist.
            - The new_deadline must be a valid time value (ISO 8601 string).
        """
        # Check if task exists
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task does not exist" }

        # Validate new_deadline (ISO 8601 time string)
        try:
            # Accept standard ISO 8601 strings, including a trailing 'Z' UTC marker.
            datetime.fromisoformat(new_deadline.replace("Z", "+00:00"))
        except Exception:
            return { "success": False, "error": "Invalid deadline format" }

        # Set the deadline
        task['deadline'] = new_deadline

        return { "success": True, "message": "Task deadline updated" }


    def update_job_deadline(self, job_id: str, new_deadline: str) -> Dict:
        """
        Set or modify the deadline for a job.

        Args:
            job_id (str): The unique identifier of the job to update.
            new_deadline (str): The new deadline value (must be a valid ISO 8601 date string).

        Returns:
            dict: {
                "success": True,
                "message": "Job deadline updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Job must exist.
            - new_deadline must be a valid time value (ISO 8601 string).
            - The job must belong to an existing project.
        """
        # Check job existence
        job = self.jobs.get(job_id)
        if not job:
            return {"success": False, "error": "Job does not exist."}

        # Check job's project validity
        project_id = job.get("project_id")
        if project_id not in self.projects:
            return {"success": False, "error": "Job is not associated with a valid project."}

        # Validate deadline string as ISO 8601
        try:
            _ = datetime.fromisoformat(new_deadline.replace("Z", "+00:00"))
        except Exception:
            return {"success": False, "error": "Deadline value is not a valid ISO 8601 datetime string."}

        # Update
        job["deadline"] = new_deadline

        return {"success": True, "message": "Job deadline updated."}

    def update_task_dependencies(self, task_id: str, dependency_ids: list) -> dict:
        """
        Update the dependency list for a task. All dependencies must refer to existing tasks or jobs.

        Args:
            task_id (str): The ID of the task to update.
            dependency_ids (List[str]): List of task IDs or job IDs to set as dependencies.

        Returns:
            dict: { "success": True, "message": ... } on success;
                  { "success": False, "error": ... } on error.

        Constraints:
            - task_id must exist in self.tasks.
            - Each ID in dependency_ids must exist in self.tasks or self.jobs.
        """
        if task_id not in self.tasks:
            return { "success": False, "error": f"Task '{task_id}' does not exist." }

        # Verify all dependency IDs exist in either tasks or jobs
        invalid_ids = [
            dep_id for dep_id in dependency_ids
            if dep_id not in self.tasks and dep_id not in self.jobs
        ]
        if invalid_ids:
            return { "success": False, "error": f"Invalid dependency IDs: {', '.join(invalid_ids)}." }

        # All constraints satisfied; update dependencies
        self.tasks[task_id]['dependency_ids'] = list(dependency_ids)
        return { "success": True, "message": f"Dependencies for task '{task_id}' updated." }

    def update_job_dependencies(self, job_id: str, new_dependency_ids: list) -> dict:
        """
        Update the dependency list for a given job.

        Args:
            job_id (str): The ID of the job whose dependencies should be updated.
            new_dependency_ids (list of str): List of task or job IDs this job should depend on.

        Returns:
            dict: {
                "success": True,
                "message": "Job dependencies updated."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints/Validation:
            - job_id must exist in self.jobs.
            - Each dependency_id in new_dependency_ids must exist in either self.jobs or self.tasks.
        """
        # Check job exists
        if job_id not in self.jobs:
            return { "success": False, "error": "Job does not exist." }

        # Validate all dependencies
        for dep_id in new_dependency_ids:
            if dep_id not in self.jobs and dep_id not in self.tasks:
                return { "success": False, "error": f"Dependency '{dep_id}' does not exist as a job or task." }

        # Update dependencies
        self.jobs[job_id]['dependency_ids'] = list(new_dependency_ids)

        return { "success": True, "message": "Job dependencies updated." }

    def create_task(
        self,
        task_id: str,
        title: str,
        description: str,
        assigned_user_id: str,
        status: str,
        deadline: str,
        dependency_ids: list,
        project_id: str
    ) -> dict:
        """
        Create and add a new task to the platform.
    
        Args:
            task_id (str): Unique identifier for the task.
            title (str): Title of the task.
            description (str): Description of task.
            assigned_user_id (str): User to assign the task. Must exist and have active account.
            status (str): Task status; must be "open", "in progress", or "completed".
            deadline (str): The deadline (ISO-formatted string).
            dependency_ids (List[str]): Task/job IDs this one depends on (each must exist).
            project_id (str): Project this task belongs to. Must exist.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Task created successfully." }
                On failure:
                    { "success": False, "error": "<description>" }
    
        Constraints:
            - Task ID must be unique.
            - Project ID must point to an existing project.
            - Assigned user must exist and be active.
            - Status must be among approved values.
            - Deadline must be a non-empty valid time value.
            - All dependencies must refer to existing task/job IDs.
        """
        # 1. Task ID uniqueness
        if task_id in self.tasks:
            return { "success": False, "error": "Task ID already exists." }

        # 2. Project existence
        if project_id not in self.projects:
            return { "success": False, "error": "Project ID does not exist." }

        # 3. User validity and activity
        user = self.users.get(assigned_user_id)
        if not user:
            return { "success": False, "error": "Assigned user does not exist." }
        if user["account_status"].lower() != "active":
            return { "success": False, "error": "Assigned user is not active." }

        # 4. Status validation
        allowed_status = {"open", "in progress", "completed"}
        if status not in allowed_status:
            return { "success": False, "error": "Invalid status value." }

        # 5. Deadline validation (must be a valid ISO 8601 time string)
        if not isinstance(deadline, str) or not deadline.strip():
            return { "success": False, "error": "Invalid or missing deadline." }
        try:
            datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        except Exception:
            return { "success": False, "error": "Invalid or missing deadline." }

        # 6. Dependency validation (must be existing task or job IDs)
        missing_deps = [
            dep_id for dep_id in dependency_ids
            if dep_id not in self.tasks and dep_id not in self.jobs
        ]
        if missing_deps:
            return {
                "success": False,
                "error": f"Dependency IDs not found: {', '.join(missing_deps)}"
            }

        # Create and add the task
        self.tasks[task_id] = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "assigned_user_id": assigned_user_id,
            "status": status,
            "deadline": deadline,
            "dependency_ids": list(dependency_ids),
            "project_id": project_id
        }
        return { "success": True, "message": "Task created successfully." }

    def create_job(
        self,
        job_id: str,
        title: str,
        description: str,
        assigned_user_id: str,
        status: str,
        deadline: str,
        dependency_ids: list,
        project_id: str
    ) -> dict:
        """
        Add a new job to the platform after validating assignment, deadline, dependencies, and project.

        Args:
            job_id (str): Unique identifier for the job
            title (str): Title of the job
            description (str): Description of the job
            assigned_user_id (str): ID of the user assigned to the job
            status (str): Initial status ("open", "in progress", "completed", etc.)
            deadline (str): Deadline (should be a valid time value, e.g., ISO string)
            dependency_ids (list): List of job/task IDs this job depends on
            project_id (str): ID of the project this job belongs to

        Returns:
            dict: Success or failure message
        Constraints:
            - job_id must be unique
            - assigned_user_id must exist and have a valid account
            - status must be an approved value
            - all dependencies must reference existing tasks or jobs
            - project_id must exist
            - deadline must be a valid non-empty string
        """

        APPROVED_STATUSES = {"open", "in progress", "completed"}

        # Check: Unique job_id
        if job_id in self.jobs:
            return {"success": False, "error": "Job ID already exists"}

        # Check: Project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        # Check: Assigned user exists and account is valid
        user = self.users.get(assigned_user_id)
        if not user:
            return {"success": False, "error": "Assigned user does not exist"}
        if user.get("account_status", "").lower() != "active":
            return {"success": False, "error": "Assigned user's account is not valid"}

        # Check: Status is allowed
        if status not in APPROVED_STATUSES:
            return {"success": False, "error": f"Status '{status}' is not an approved value"}

        # Check: Dependencies are all valid (refer to either task or job)
        for dep_id in dependency_ids:
            if dep_id not in self.tasks and dep_id not in self.jobs:
                return {"success": False, "error": f"Dependency ID '{dep_id}' does not exist"}

        # Check: Deadline must be a valid ISO 8601 datetime string
        if not isinstance(deadline, str) or not deadline.strip():
            return {"success": False, "error": "Deadline is not valid or empty"}
        try:
            datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        except Exception:
            return {"success": False, "error": "Deadline value is not a valid ISO 8601 datetime string."}

        # All checks passed, create the Job
        job_info = {
            "job_id": job_id,
            "title": title,
            "description": description,
            "assigned_user_id": assigned_user_id,
            "status": status,
            "deadline": deadline,
            "dependency_ids": list(dependency_ids),
            "project_id": project_id,
        }
        self.jobs[job_id] = job_info
        return {"success": True, "message": f"Job {job_id} created successfully"}

    def delete_task(self, task_id: str) -> dict:
        """
        Remove a task from the system.
    
        Args:
            task_id (str): The unique identifier of the task to delete.

        Returns:
            dict:
                { "success": True, "message": "Task <task_id> deleted." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - Task must exist.
            - Cannot delete a task if it is referenced as a dependency by any existing task or job.
        """
        # 1. Check if task exists
        if task_id not in self.tasks:
            return { "success": False, "error": f"Task {task_id} does not exist." }

        # 2. Check whether any task depends on this task
        for t in self.tasks.values():
            if task_id in t.get("dependency_ids", []):
                return {
                    "success": False,
                    "error": (
                        f"Cannot delete task {task_id}: it is a dependency for task {t['task_id']}."
                    )
                }

        # 3. Check whether any job depends on this task
        for j in self.jobs.values():
            if task_id in j.get("dependency_ids", []):
                return {
                    "success": False,
                    "error": (
                        f"Cannot delete task {task_id}: it is a dependency for job {j['job_id']}."
                    )
                }

        # 4. Remove the task
        del self.tasks[task_id]
        return { "success": True, "message": f"Task {task_id} deleted." }

    def delete_job(self, job_id: str) -> dict:
        """
        Remove a job from the system.
    
        Args:
            job_id (str): The ID of the job to be deleted.
    
        Returns:
            dict: {
                "success": True,
                "message": "Job <job_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Job not found"
            }
    
        Constraints:
            - The job must exist.
            - After deletion, no task or job should have this job's ID in its dependency_ids.
        """
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
    
        # Remove the job
        del self.jobs[job_id]
    
        # Remove this job_id from any dependency lists among all jobs
        for jb in self.jobs.values():
            if job_id in jb["dependency_ids"]:
                jb["dependency_ids"] = [dep for dep in jb["dependency_ids"] if dep != job_id]
    
        # Remove this job_id from any dependency lists among all tasks
        for tk in self.tasks.values():
            if job_id in tk["dependency_ids"]:
                tk["dependency_ids"] = [dep for dep in tk["dependency_ids"] if dep != job_id]
    
        return {"success": True, "message": f"Job {job_id} deleted."}

    def update_project_status(self, project_id: str, new_status: str) -> dict:
        """
        Change the status of a project.
    
        Args:
            project_id (str): The ID of the project to update.
            new_status (str): The new status value for the project.
        
        Returns:
            dict: {
                "success": True,
                "message": "Project status updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - Project with the given project_id must exist.
            - No explicit status whitelist for projects (as per current environment specification).
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}
        self.projects[project_id]["status"] = new_status
        return {"success": True, "message": "Project status updated."}

    def update_project_details(self, project_id: str, name: str = None, description: str = None) -> dict:
        """
        Edit the name and/or description of a project.

        Args:
            project_id (str): The project to update.
            name (str, optional): New name for the project.
            description (str, optional): New description for the project.

        Returns:
            dict: {
                "success": True,
                "message": "Updated fields for project <project_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - project_id must reference an existing project.
            - At least one of `name` or `description` must be provided.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        if name is None and description is None:
            return {"success": False, "error": "No details provided to update"}

        updated_fields = []
        if name is not None:
            self.projects[project_id]["name"] = name
            updated_fields.append("name")
        if description is not None:
            self.projects[project_id]["description"] = description
            updated_fields.append("description")

        return {
            "success": True,
            "message": f"Updated {', '.join(updated_fields)} for project {project_id}."
        }


class ProjectManagementPlatform(BaseEnv):
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

    def get_task_by_id(self, **kwargs):
        return self._call_inner_tool('get_task_by_id', kwargs)

    def get_job_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_by_id', kwargs)

    def list_tasks_for_project(self, **kwargs):
        return self._call_inner_tool('list_tasks_for_project', kwargs)

    def list_jobs_for_project(self, **kwargs):
        return self._call_inner_tool('list_jobs_for_project', kwargs)

    def list_tasks_assigned_to_user(self, **kwargs):
        return self._call_inner_tool('list_tasks_assigned_to_user', kwargs)

    def list_jobs_assigned_to_user(self, **kwargs):
        return self._call_inner_tool('list_jobs_assigned_to_user', kwargs)

    def get_task_status(self, **kwargs):
        return self._call_inner_tool('get_task_status', kwargs)

    def get_job_status(self, **kwargs):
        return self._call_inner_tool('get_job_status', kwargs)

    def get_task_dependencies(self, **kwargs):
        return self._call_inner_tool('get_task_dependencies', kwargs)

    def get_job_dependencies(self, **kwargs):
        return self._call_inner_tool('get_job_dependencies', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def update_task_status(self, **kwargs):
        return self._call_inner_tool('update_task_status', kwargs)

    def update_job_status(self, **kwargs):
        return self._call_inner_tool('update_job_status', kwargs)

    def assign_task_to_user(self, **kwargs):
        return self._call_inner_tool('assign_task_to_user', kwargs)

    def assign_job_to_user(self, **kwargs):
        return self._call_inner_tool('assign_job_to_user', kwargs)

    def update_task_deadline(self, **kwargs):
        return self._call_inner_tool('update_task_deadline', kwargs)

    def update_job_deadline(self, **kwargs):
        return self._call_inner_tool('update_job_deadline', kwargs)

    def update_task_dependencies(self, **kwargs):
        return self._call_inner_tool('update_task_dependencies', kwargs)

    def update_job_dependencies(self, **kwargs):
        return self._call_inner_tool('update_job_dependencies', kwargs)

    def create_task(self, **kwargs):
        return self._call_inner_tool('create_task', kwargs)

    def create_job(self, **kwargs):
        return self._call_inner_tool('create_job', kwargs)

    def delete_task(self, **kwargs):
        return self._call_inner_tool('delete_task', kwargs)

    def delete_job(self, **kwargs):
        return self._call_inner_tool('delete_job', kwargs)

    def update_project_status(self, **kwargs):
        return self._call_inner_tool('update_project_status', kwargs)

    def update_project_details(self, **kwargs):
        return self._call_inner_tool('update_project_details', kwargs)
