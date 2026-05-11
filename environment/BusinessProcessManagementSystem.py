# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any, Optional
import time
import uuid



class ProcessInfo(TypedDict):
    process_id: str
    name: str
    start_time: str
    end_time: Optional[str]
    status: str
    participant: str  # assuming participant is a single user_id (may be List[str] if clarified)

class TaskInfo(TypedDict):
    task_id: str
    process_id: str
    assigned_to: str  # could be user_id or role
    start_time: str
    end_time: Optional[str]
    status: str
    form_id: Optional[str]

class FormInfo(TypedDict):
    form_id: str
    name: str
    description: str
    structure: Any  # renamed from struc, assumed dict

class FormActionInfo(TypedDict):
    action_id: str
    form_id: str
    task_id: str
    user_id: str
    submit_timestamp: str
    status: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    role: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Business Process Management System (BPMS) environment instance.

        Constraints:
        - A FormAction is only considered "completed" if its status indicates completion.
        - Each Task may have at most one form action in progress at a time.
        - Users can only act on tasks assigned to them or roles they are authorized for.
        - Processes can only be marked complete if all required tasks (and associated forms) are completed.
        """

        # Processes: {process_id: ProcessInfo}
        self.processes: Dict[str, ProcessInfo] = {}
        # Tasks: {task_id: TaskInfo}
        self.tasks: Dict[str, TaskInfo] = {}
        # Forms: {form_id: FormInfo}
        self.forms: Dict[str, FormInfo] = {}
        # FormActions: {action_id: FormActionInfo}
        self.form_actions: Dict[str, FormActionInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

    def get_form_actions_by_status(self, status: str) -> dict:
        """
        Retrieve all form action records filtered by a specific status (e.g., 'completed', 'in_progress').

        Args:
            status (str): The status value to filter form actions.

        Returns:
            dict: {
                "success": True,
                "data": List[FormActionInfo],  # Form actions matching the status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., input type)
            }

        Constraints:
            - None for query. Returns an empty list if no form actions match.
        """
        if not isinstance(status, str) or not status:
            return {"success": False, "error": "Status must be a non-empty string"}

        result = [
            fa for fa in self.form_actions.values() if fa.get("status") == status
        ]

        return {"success": True, "data": result}

    def count_form_actions_by_status(self, status: str) -> dict:
        """
        Count the number of FormAction entries with the given status.

        Args:
            status (str): The status value to filter FormActions by.

        Returns:
            dict:
                {
                    "success": True,
                    "data": int  # The count of FormActions with the specified status
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for error (e.g., invalid input)
                }

        Constraints:
            - If status is empty or None, returns an error.
        """
        if not status or not isinstance(status, str):
            return { "success": False, "error": "Status must be a non-empty string" }

        count = sum(
            1 for fa in self.form_actions.values()
            if fa["status"] == status
        )
        return { "success": True, "data": count }

    def get_all_form_actions(self) -> dict:
        """
        Retrieve all form action records in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FormActionInfo],  # All form action records (can be an empty list)
            }

        Constraints:
            - No filtering or permission restrictions; returns all form actions.
        """
        all_actions = list(self.form_actions.values())
        return { "success": True, "data": all_actions }

    def get_form_action_by_id(self, action_id: str) -> dict:
        """
        Retrieve a specific FormAction by its unique action_id.

        Args:
            action_id (str): The ID of the form action to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": FormActionInfo
            }
            or
            {
                "success": False,
                "error": "FormAction not found"
            }
        """
        if action_id not in self.form_actions:
            return { "success": False, "error": "FormAction not found" }

        return {
            "success": True,
            "data": self.form_actions[action_id],
        }

    def get_tasks_by_process(self, process_id: str) -> dict:
        """
        Retrieve all tasks (TaskInfo) associated with a given process_id.

        Args:
            process_id (str): Identifier for the process.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo],  # List of all tasks for the process_id (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if process not found
            }

        Constraints:
            - The process_id must exist in the BPMS.
        """
        if process_id not in self.processes:
            return { "success": False, "error": "Process does not exist" }

        result = [
            task for task in self.tasks.values()
            if task["process_id"] == process_id
        ]
        return { "success": True, "data": result }

    def get_forms_by_task(self, task_id: str) -> dict:
        """
        Retrieve the form attached to a specific task, if any.

        Args:
            task_id (str): The identifier of the task.

        Returns:
            dict:
                - On success and form exists: { "success": True, "data": FormInfo }
                - On success but no form attached: { "success": True, "data": None }
                - On error (task not found): { "success": False, "error": "Task does not exist" }
                - On error (form_id assigned but form missing): { "success": False, "error": "Form not found" }
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task does not exist" }
        form_id = task.get("form_id")
        if form_id is None:
            return { "success": True, "data": None }
        form = self.forms.get(form_id)
        if not form:
            return { "success": False, "error": "Form not found" }
        return { "success": True, "data": form }

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Retrieve full details for a specific task by its task_id.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            dict:
                - If the task exists:
                    {"success": True, "data": TaskInfo}
                - If the task does not exist:
                    {"success": False, "error": "Task not found"}
        """
        task = self.tasks.get(task_id)
        if task is None:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "data": task}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve details for a specific user by user_id.

        Args:
            user_id (str): The identifier of the user to retrieve.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On user not found: { "success": False, "error": "User not found" }

        Constraints:
            - No additional constraints; simply fetch user if they exist.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_process_by_id(self, process_id: str) -> dict:
        """
        Retrieve the details for a specific process.

        Args:
            process_id (str): The unique identifier of the process.

        Returns:
            dict:
                - If found: {
                      "success": True,
                      "data": ProcessInfo
                  }
                - If not found: {
                      "success": False,
                      "error": "Process not found"
                  }
        Constraints:
            - The process_id must exist in the system.
        """
        process = self.processes.get(process_id)
        if process is None:
            return {"success": False, "error": "Process not found"}
        return {"success": True, "data": process}

    def get_process_status(self, process_id: str) -> dict:
        """
        Query the current status of a process.

        Args:
            process_id (str): The unique identifier of the process.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": {
                        "process_id": str,
                        "status": str
                    }
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The process_id must exist in the system.
        """
        process = self.processes.get(process_id)
        if not process:
            return {"success": False, "error": "Process not found"}

        return {
            "success": True,
            "data": {
                "process_id": process_id,
                "status": process["status"]
            }
        }

    def get_task_status(self, task_id: str) -> dict:
        """
        Query the current status of a task.

        Args:
            task_id (str): The ID of the task whose status is being queried.

        Returns:
            dict: 
                On success: { "success": True, "data": <task_status: str> }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The task_id must exist in the system.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }
        status = task.get("status")
        return { "success": True, "data": status }

    def list_all_processes(self) -> dict:
        """
        List all business process instances in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProcessInfo],  # List of all tracked process information (may be empty)
            }

        Constraints:
            - This is a simple listing operation; no constraints apply.
        """
        return {
            "success": True,
            "data": list(self.processes.values())
        }

    def list_all_users(self) -> dict:
        """
        List all registered users in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all users (empty if none exist)
            }
        """
        user_list = list(self.users.values())
        return {"success": True, "data": user_list}

    def get_tasks_assigned_to_user(self, assignee_id: str) -> dict:
        """
        List all tasks assigned to the given user or role.

        Args:
            assignee_id (str): The user_id or role to find tasks for.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo]  # List of matching tasks (can be empty)
            }
        """
        result = [
            task_info for task_info in self.tasks.values()
            if task_info["assigned_to"] == assignee_id
        ]
        return { "success": True, "data": result }

    def get_pending_form_action_for_task(self, task_id: str) -> dict:
        """
        Retrieve the in-progress (not 'completed') form action for a given task.

        Args:
            task_id (str): The ID of the task to query.

        Returns:
            dict: {
                "success": True,
                "data": FormActionInfo | None  # returns the in-progress form action, or None if not found
            }
            or
            {
                "success": False,
                "error": str  # error message, e.g., task does not exist
            }

        Constraints:
            - Task must exist.
            - Only one pending form action should exist per task (enforced by environment).
            - "Completed" status is determined by FormAction.status == "completed".
        """
        if task_id not in self.tasks:
            return { "success": False, "error": "Task does not exist" }

        # Look for form action for this task that is not completed
        for fa in self.form_actions.values():
            if fa["task_id"] == task_id and fa["status"] != "completed":
                return { "success": True, "data": fa }

        # None found
        return { "success": True, "data": None }

    def assign_task_to_user(self, task_id: str, user_or_role: str) -> dict:
        """
        Assign or reassign a task to a user or role.

        Args:
            task_id (str): The unique identifier of the task to assign.
            user_or_role (str): The user_id or role name to assign the task to.

        Returns:
            dict: {
                "success": True,
                "message": "Task <task_id> assigned to <user_or_role>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The given task must exist.
            - The user_or_role must match either an existing user_id or an existing user role.
            - Updates the task's assigned_to field.
        """
        # Check if task exists
        if task_id not in self.tasks:
            return {"success": False, "error": f"Task {task_id} does not exist."}

        # Check if user_or_role is a valid user_id
        if user_or_role in self.users:
            valid = True
        else:
            # Check if user_or_role matches any user's role in the environment
            valid = any(user["role"] == user_or_role for user in self.users.values())

        if not valid:
            return {"success": False, "error": f"User or role '{user_or_role}' does not exist in the system."}

        # Update the assigned_to field on the task
        self.tasks[task_id]["assigned_to"] = user_or_role

        return {
            "success": True,
            "message": f"Task {task_id} assigned to {user_or_role}."
        }

    def start_form_action(self, task_id: str, user_id: str) -> dict:
        """
        Initiate a form action for a task, provided no other action is in progress and user is authorized.

        Args:
            task_id (str): The ID of the task for which to start the form action.
            user_id (str): The user initiating the form action.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Form action initiated.",
                        "action_id": str,
                        "form_action": FormActionInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - The task and user must exist.
            - The task must have an attached form.
            - No other form action is in progress for the task.
            - User must be assigned to the task or have the authorized role.
        """

        # 1. Validate task and user exist
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task does not exist."}
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # 2. Validate task has attached form
        form_id = task.get("form_id")
        if not form_id:
            return {"success": False, "error": "Task has no attached form."}
        form = self.forms.get(form_id)
        if not form:
            return {"success": False, "error": "Form does not exist."}

        # 3. Ensure no other form action is in progress for this task
        in_progress_statuses = {"in_progress", "open", "pending"}  # non-completed statuses
        for action in self.form_actions.values():
            if (
                action["task_id"] == task_id
                and action["status"] not in {"completed", "complete", "finished"}  # not completed
            ):
                return {
                    "success": False,
                    "error": "A form action is already in progress for this task."
                }

        # 4. Check authorization (assigned_to is user or user's role)
        assigned_to = task.get("assigned_to")
        if assigned_to != user_id and assigned_to != user.get("role"):
            return {
                "success": False,
                "error": "User is not authorized to start a form action for this task."
            }

        # 5. Create new FormAction
        # Generate unique action_id
        action_id = f"FA-{str(uuid.uuid4())[:8]}"
        submit_timestamp = str(time.time())
        form_action = {
            "action_id": action_id,
            "form_id": form_id,
            "task_id": task_id,
            "user_id": user_id,
            "submit_timestamp": submit_timestamp,
            "status": "in_progress"
        }
        self.form_actions[action_id] = form_action

        return {
            "success": True,
            "message": "Form action initiated.",
            "action_id": action_id,
            "form_action": form_action
        }

    def complete_form_action(self, action_id: str) -> dict:
        """
        Mark a form action as completed by updating its status to "completed".
    
        Args:
            action_id (str): The unique identifier of the form action to mark as completed.
    
        Returns:
            dict: On success,
                { "success": True, "message": "Form action marked as completed." }
            On failure,
                { "success": False, "error": "<reason>" }
    
        Constraints:
            - Only update if the specified form action exists and is not already "completed".
            - Status is set to the literal string "completed".
        """
        form_action = self.form_actions.get(action_id)
        if not form_action:
            return { "success": False, "error": "Form action does not exist." }
        if form_action["status"] == "completed":
            return { "success": False, "error": "Form action is already completed." }
    
        form_action["status"] = "completed"
        # Optionally, could update timestamp (not in requirements)
        self.form_actions[action_id] = form_action
        return { "success": True, "message": "Form action marked as completed." }

    def set_task_status(self, task_id: str, status: str) -> dict:
        """
        Change the status of a task (e.g., to "in_progress", "completed").
        If setting to "completed", and the task has an associated form, the related FormAction(s) for this task must all be completed.
    
        Args:
            task_id (str): ID of the task to update.
            status (str): The new status string. E.g., "in_progress", "completed".

        Returns:
            dict: {
                "success": True, 
                "message": "Task status updated to <status>."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - If completing a task that has a form, all form actions for the task must be marked completed (status == "completed").
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found."}

        task = self.tasks[task_id]

        # If setting to completed, and this task has a form, check all related form actions are completed
        if status == "completed" and task.get("form_id"):
            # Find all form actions for this task
            incomplete_actions = [
                fa for fa in self.form_actions.values()
                if fa["task_id"] == task_id and fa["status"] != "completed"
            ]
            if incomplete_actions:
                return {
                    "success": False,
                    "error": (
                        "Cannot mark task as completed: not all associated form actions are completed."
                    )
                }

        # (Optional) You might want to check for valid status values; omitted unless specified.

        previous_status = task["status"]
        if previous_status == status:
            return {"success": False, "error": f"Task already has status '{status}'."}

        # Update the status
        self.tasks[task_id]["status"] = status

        return {
            "success": True, 
            "message": f"Task status updated to '{status}'."
        }

    def set_process_status(self, process_id: str, new_status: str) -> dict:
        """
        Change the status of a process. 
        If setting status to 'completed', validates that all tasks and related forms are completed.

        Args:
            process_id (str): The ID of the process to update.
            new_status (str): The new status to assign to the process (e.g., 'completed').

        Returns:
            dict: {
                'success': True,
                'message': 'Process <process_id> status set to <new_status>.'
            }
            or
            {
                'success': False,
                'error': '<error_reason>'
            }

        Constraints:
            - Cannot set to 'completed' unless:
                - All tasks for the process are completed (status contains 'completed')
                - Each task with a form_id has a completed FormAction (status contains 'completed')
        """
        # Check process exists
        if process_id not in self.processes:
            return { "success": False, "error": "Process does not exist" }

        # If new_status is 'completed', check constraints
        if new_status.lower() == "completed":
            # Find all tasks for this process
            process_tasks = [task for task in self.tasks.values() if task["process_id"] == process_id]

            for task in process_tasks:
                # Check task status for completion
                if "completed" not in task["status"].lower():
                    return { "success": False, "error": f"Task {task['task_id']} is not completed." }
                # If task is associated with a form, check for completed form action
                if task.get("form_id"):
                    # Find all FormActions for this task and form
                    actions = [
                        fa for fa in self.form_actions.values()
                        if fa["task_id"] == task["task_id"] and fa["form_id"] == task["form_id"]
                    ]
                    # At least one FormAction for this task/form must be completed
                    if not any("completed" in fa["status"].lower() for fa in actions):
                        return { "success": False, "error": f"Form for Task {task['task_id']} is not completed." }

        # Passed checks, can set status
        self.processes[process_id]["status"] = new_status
        return { "success": True, "message": f"Process {process_id} status set to {new_status}." }

    def update_user_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's status.

        Args:
            user_id (str): The unique identifier of the user.
            new_status (str): The new status to assign to the user (e.g., "active", "suspended", etc.).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Status for user <user_id> updated to <new_status>."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - user_id must exist in the system.
            - Any string is permitted as a status value (no validation on allowed statuses).
        """
        user = self.users.get(user_id)
        if user is None:
            return {
                "success": False,
                "error": "User not found"
            }
        user["status"] = new_status
        return {
            "success": True,
            "message": f"Status for user {user_id} updated to {new_status}."
        }

    def update_form_action_status(self, action_id: str, new_status: str) -> dict:
        """
        Change the status of a specific form action.

        Args:
            action_id (str): The identifier of the form action to update.
            new_status (str): The new status to assign (e.g., "in_progress", "cancelled", "completed").

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Form action status updated."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Form action not found."
                    }

        Constraints:
            - The form action with the given action_id must exist.
            - No further state changes or validations are enforced by this operation.
        """
        if action_id not in self.form_actions:
            return { "success": False, "error": "Form action not found." }

        self.form_actions[action_id]["status"] = new_status
        return { "success": True, "message": "Form action status updated." }

    def add_new_process(self, process_id: str, name: str, start_time: str, participant: str, status: str = "active") -> dict:
        """
        Add (initiate) a new process instance.

        Args:
            process_id (str): Unique identifier for the process.
            name (str): Human-readable name of the process.
            start_time (str): ISO format timestamp when process is created.
            participant (str): user_id of main participant of process.
            status (str, optional): Initial status of the process (default 'active').

        Returns:
            dict: {
                "success": True,
                "message": "Process <ID> created successfully"
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - process_id must be unique.
            - participant must be an existing valid user_id.
            - Required fields must be provided and not empty.
        """
        # Validate required fields
        if not process_id or not name or not start_time or not participant:
            return {"success": False, "error": "Missing required process fields."}

        # Check for process_id uniqueness
        if process_id in self.processes:
            return {"success": False, "error": f"Process ID '{process_id}' already exists."}

        # Validate participant user_id
        if participant not in self.users:
            return {"success": False, "error": f"Participant user_id '{participant}' does not exist."}

        # Create process entry
        self.processes[process_id] = {
            "process_id": process_id,
            "name": name,
            "start_time": start_time,
            "end_time": None,
            "status": status,
            "participant": participant
        }

        return {"success": True, "message": f"Process '{process_id}' created successfully."}

    def add_new_task(
        self, 
        task_id: str,
        process_id: str,
        assigned_to: str,
        start_time: str,
        status: str,
        end_time: Optional[str] = None,
        form_id: Optional[str] = None
    ) -> dict:
        """
        Add a new task to a business process.

        Args:
            task_id (str): Unique identifier for the new task.
            process_id (str): Identifier of the parent process (must exist).
            assigned_to (str): User ID or role to assign the task.
            start_time (str): The starting timestamp of the task.
            status (str): Status of the task (e.g., "pending").
            end_time (Optional[str]): The ending timestamp of the task (default None).
            form_id (Optional[str]): Form to associate with the task (default None).

        Returns:
            dict: 
                On success: {"success": True, "message": "..."}
                On failure: {"success": False, "error": "..."}
        
        Constraints:
            - task_id must be unique.
            - process_id must exist.
        """
        if task_id in self.tasks:
            return {"success": False, "error": "Task ID already exists"}
        if process_id not in self.processes:
            return {"success": False, "error": "Process does not exist"}

        task_info: TaskInfo = {
            "task_id": task_id,
            "process_id": process_id,
            "assigned_to": assigned_to,
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
            "form_id": form_id
        }
        self.tasks[task_id] = task_info
        return {"success": True, "message": f"Task {task_id} added to process {process_id}"}

    def add_new_form(
        self,
        form_id: str,
        name: str,
        description: str,
        structure: Any
    ) -> dict:
        """
        Register a new form template.

        Args:
            form_id (str): Unique identifier for the new form.
            name (str): Name of the form.
            description (str): Description of the form.
            structure (Any): The structure/definition of the form (fields, datatypes, etc.)

        Returns:
            dict: {
                "success": True,
                "message": "Form registered successfully"
            }
            or
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - form_id must be unique within the system.
            - Required fields must be non-empty strings (name, description, form_id).
        """
        # Check form_id uniqueness
        if not form_id or form_id in self.forms:
            return { "success": False, "error": "Form ID already exists or is invalid" }
    
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Name must be a non-empty string" }
    
        if not isinstance(description, str) or not description.strip():
            return { "success": False, "error": "Description must be a non-empty string" }

        # Structure can be any, but should not be None for basic validation
        if structure is None:
            return { "success": False, "error": "Structure must be provided" }

        new_form: FormInfo = {
            "form_id": form_id,
            "name": name,
            "description": description,
            "structure": structure
        }
        self.forms[form_id] = new_form

        return { "success": True, "message": "Form registered successfully" }

    def delete_form_action(self, action_id: str) -> dict:
        """
        Remove a form action record by its action_id, if permitted.

        Args:
            action_id (str): The unique identifier of the form action to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Form action <action_id> deleted."
            } or {
                "success": False,
                "error": <description of the error>
            }

        Constraints:
            - Cannot delete a FormAction if it is 'completed' (i.e., if status == 'completed').
            - Fails if action_id does not exist.
        """
        form_action = self.form_actions.get(action_id)
        if form_action is None:
            return { "success": False, "error": "Form action not found." }
    
        # Only allow deletion if not completed. Assuming 'completed' is the status keyword.
        if form_action.get("status") == "completed":
            return { "success": False, "error": "Cannot delete a completed form action." }

        del self.form_actions[action_id]
        return { "success": True, "message": f"Form action {action_id} deleted." }

    def reassign_process_participant(self, process_id: str, new_participant) -> dict:
        """
        Change the participant(s) responsible for a process.

        Args:
            process_id (str): Identifier of the process to update.
            new_participant (Union[str, List[str]]): The user_id(s) of the new participant(s). Can be a single user_id or a list of user_ids.

        Returns:
            dict: {
                "success": True,
                "message": "Reassigned participant(s) for process <process_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - `process_id` must exist
            - All specified user_id(s) must exist
            - The participant can be a string or a list of strings, system adapts records as such.
        """
        # Check process exists
        if process_id not in self.processes:
            return {"success": False, "error": "Process does not exist"}

        # Normalize new_participant to a list of user_ids
        if isinstance(new_participant, str):
            participant_ids = [new_participant]
        elif isinstance(new_participant, list) and all(isinstance(u, str) for u in new_participant):
            participant_ids = new_participant
        else:
            return {"success": False, "error": "Invalid participant format; must be user_id or list of user_ids"}

        # Check all user_ids exist
        for user_id in participant_ids:
            if user_id not in self.users:
                return {"success": False, "error": f"User ID '{user_id}' does not exist"}

        # Store as string if only one participant, else as list
        process_info = self.processes[process_id]
        if len(participant_ids) == 1:
            process_info["participant"] = participant_ids[0]
        else:
            process_info["participant"] = participant_ids

        self.processes[process_id] = process_info

        return {"success": True, "message": f"Reassigned participant(s) for process {process_id}"}


class BusinessProcessManagementSystem(BaseEnv):
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

    def get_form_actions_by_status(self, **kwargs):
        return self._call_inner_tool('get_form_actions_by_status', kwargs)

    def count_form_actions_by_status(self, **kwargs):
        return self._call_inner_tool('count_form_actions_by_status', kwargs)

    def get_all_form_actions(self, **kwargs):
        return self._call_inner_tool('get_all_form_actions', kwargs)

    def get_form_action_by_id(self, **kwargs):
        return self._call_inner_tool('get_form_action_by_id', kwargs)

    def get_tasks_by_process(self, **kwargs):
        return self._call_inner_tool('get_tasks_by_process', kwargs)

    def get_forms_by_task(self, **kwargs):
        return self._call_inner_tool('get_forms_by_task', kwargs)

    def get_task_by_id(self, **kwargs):
        return self._call_inner_tool('get_task_by_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_process_by_id(self, **kwargs):
        return self._call_inner_tool('get_process_by_id', kwargs)

    def get_process_status(self, **kwargs):
        return self._call_inner_tool('get_process_status', kwargs)

    def get_task_status(self, **kwargs):
        return self._call_inner_tool('get_task_status', kwargs)

    def list_all_processes(self, **kwargs):
        return self._call_inner_tool('list_all_processes', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_tasks_assigned_to_user(self, **kwargs):
        return self._call_inner_tool('get_tasks_assigned_to_user', kwargs)

    def get_pending_form_action_for_task(self, **kwargs):
        return self._call_inner_tool('get_pending_form_action_for_task', kwargs)

    def assign_task_to_user(self, **kwargs):
        return self._call_inner_tool('assign_task_to_user', kwargs)

    def start_form_action(self, **kwargs):
        return self._call_inner_tool('start_form_action', kwargs)

    def complete_form_action(self, **kwargs):
        return self._call_inner_tool('complete_form_action', kwargs)

    def set_task_status(self, **kwargs):
        return self._call_inner_tool('set_task_status', kwargs)

    def set_process_status(self, **kwargs):
        return self._call_inner_tool('set_process_status', kwargs)

    def update_user_status(self, **kwargs):
        return self._call_inner_tool('update_user_status', kwargs)

    def update_form_action_status(self, **kwargs):
        return self._call_inner_tool('update_form_action_status', kwargs)

    def add_new_process(self, **kwargs):
        return self._call_inner_tool('add_new_process', kwargs)

    def add_new_task(self, **kwargs):
        return self._call_inner_tool('add_new_task', kwargs)

    def add_new_form(self, **kwargs):
        return self._call_inner_tool('add_new_form', kwargs)

    def delete_form_action(self, **kwargs):
        return self._call_inner_tool('delete_form_action', kwargs)

    def reassign_process_participant(self, **kwargs):
        return self._call_inner_tool('reassign_process_participant', kwargs)

