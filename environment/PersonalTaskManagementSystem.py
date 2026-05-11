# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
import uuid
from datetime import datetime




class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    preference: Union[str, dict]  # Assuming 'preference' (typically user settings)


class TaskInfo(TypedDict):
    task_id: str
    user_id: str
    project_id: str
    content: str
    due_date: str           # ISO 8601 or date string
    priority: int
    labels: List[str]       # List of label_ids
    status: str             # E.g., 'active', 'completed', 'deleted'
    created_at: str         # Timestamp string
    completed_at: str       # Timestamp string
    ord: int                # Ordering within a project


class ProjectInfo(TypedDict):
    project_id: str
    user_id: str
    name: str
    description: str
    archived: bool
    ord: int                # Ordering among user's projects


class LabelInfo(TypedDict):
    label_id: str
    user_id: str
    name: str


class _GeneratedEnvImpl:
    """
    State for personal task management (Todoist-like).
    Constraints:
    - Each task must belong to exactly one user.
    - Each project and label is scoped to a single user.
    - Tasks must have a valid status (e.g., 'active', 'completed', 'deleted').
    - Deleting or archiving a project affects its contained tasks according to user settings.
    - Task ordering must be preserved within each project.
    - Only active (not deleted or archived) tasks appear in a user's default task list.
    """

    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Tasks: {task_id: TaskInfo}
        self.tasks: Dict[str, TaskInfo] = {}

        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Labels: {label_id: LabelInfo}
        self.labels: Dict[str, LabelInfo] = {}

    def get_user_by_email(self, email: str) -> dict:
        """
        Retrieve user information by email address.

        Args:
            email (str): The email address of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User info if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Returns the first user matched by email.
            - Email must be provided (non-empty).
        """
        if not email or not isinstance(email, str):
            return { "success": False, "error": "Email must be provided." }

        for user in self.users.values():
            if user["email"].lower() == email.lower():
                return { "success": True, "data": user }

        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for a given user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User info dictionary
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g., 'User not found')
            }

        Constraints:
            - Returns user info if the user_id exists, otherwise returns error.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def list_user_tasks(self, user_id: str) -> dict:
        """
        Retrieve all tasks (with full metadata) that belong to the given user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                - On success: { "success": True, "data": List[TaskInfo] }
                    (all tasks for the user, may be empty)
                - On failure: { "success": False, "error": str }
                    (e.g., if user is not found)

        Constraints:
            - user_id must exist in the system.
            - Returns all kinds of tasks (regardless of status).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [task for task in self.tasks.values() if task["user_id"] == user_id]
        return { "success": True, "data": result }

    def list_user_projects(self, user_id: str) -> dict:
        """
        Retrieve all projects for a given user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: 
                - If user exists: { "success": True, "data": List[ProjectInfo] }
                - If user does not exist: { "success": False, "error": "User does not exist" }
        Constraints:
            - The user_id must exist in the system.
            - Returned projects are those where project['user_id'] == user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        projects = [
            project for project in self.projects.values()
            if project["user_id"] == user_id
        ]
        return { "success": True, "data": projects }

    def list_user_labels(self, user_id: str) -> dict:
        """
        Retrieve all labels for a given user.

        Args:
            user_id (str): The user's unique ID.

        Returns:
            dict: 
                { "success": True, "data": List[LabelInfo] }
                if user exists,
                or
                { "success": False, "error": "User does not exist" }
                if user_id is invalid.

        Constraints:
            - Only labels belonging to the given user_id are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_labels = [
            label_info for label_info in self.labels.values()
            if label_info["user_id"] == user_id
        ]
        return { "success": True, "data": user_labels }

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Fetch details of a specific task by its ID.

        Args:
            task_id (str): The unique identifier for the task.

        Returns:
            dict: 
                Success: { "success": True, "data": TaskInfo }
                Failure: { "success": False, "error": "Task not found" }

        Constraints:
            - The task with the specified task_id must exist in self.tasks.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }
        return { "success": True, "data": task }

    def list_tasks_by_status(self, user_id: str, status: str) -> dict:
        """
        Retrieve all tasks for a specific user filtered by given status ('active', 'completed', 'deleted').

        Args:
            user_id (str): The ID of the user whose tasks are to be queried.
            status (str): The status to filter by ('active', 'completed', 'deleted').

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo]  # May be empty if no tasks with the given status
            }
            or
            {
                "success": False,
                "error": str  # Error message specifying the problem
            }

        Constraints:
            - The user must exist.
            - Status must be one of the allowed statuses: 'active', 'completed', 'deleted'.
        """
        allowed_statuses = {"active", "completed", "deleted"}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if status not in allowed_statuses:
            return {"success": False, "error": "Invalid status"}

        result = [
            task for task in self.tasks.values()
            if task["user_id"] == user_id and task["status"] == status
        ]

        return {"success": True, "data": result}

    def list_tasks_by_project(self, user_id: str, project_id: str) -> dict:
        """
        Retrieve all tasks (with metadata) under a particular project for a user.

        Args:
            user_id (str): The user's ID.
            project_id (str): The project's ID.

        Returns:
            dict: 
                success (bool), 
                data (List[TaskInfo]) if successful (may be empty if no tasks), 
                or error (str) if user/project ID is invalid or permissions violated.

        Constraints:
            - The project must exist and belong to the given user.
            - Only tasks that match the given user ID and project ID are returned.
            - Tasks of any status are included.
        """
        # Check that user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check that project exists
        project = self.projects.get(project_id)
        if project is None:
            return { "success": False, "error": "Project does not exist" }

        # Check that project belongs to user
        if project["user_id"] != user_id:
            return { "success": False, "error": "Project does not belong to user" }

        # List all tasks for this user & project
        tasks = [
            task for task in self.tasks.values()
            if task["user_id"] == user_id and task["project_id"] == project_id
        ]

        return { "success": True, "data": tasks }

    def list_tasks_by_label(self, user_id: str, label_id: str) -> dict:
        """
        Retrieve all tasks for the specified user associated with the specified label.

        Args:
            user_id (str): The ID of the user.
            label_id (str): The ID of the label.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[TaskInfo]  # May be empty if no tasks found
                  }
                - On failure: {
                      "success": False,
                      "error": "<reason>"
                  }

        Constraints:
            - The user must exist.
            - The label must exist and must belong to the user.
        """
        # Validate user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Validate label existence and scope
        label = self.labels.get(label_id)
        if not label or label["user_id"] != user_id:
            return { "success": False, "error": "Label does not exist for this user" }

        # Find all tasks for this user associated with the label
        tasks_with_label = [
            task for task in self.tasks.values()
            if task["user_id"] == user_id and label_id in task.get("labels", [])
        ]

        return { "success": True, "data": tasks_with_label }

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Fetch details of a specific project by its ID.

        Args:
            project_id (str): Unique identifier of the project.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ProjectInfo  # Project details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Project not found"
                    }

        Constraints:
            - The given project_id must exist in the system.
        """
        project = self.projects.get(project_id)
        if project is None:
            return { "success": False, "error": "Project not found" }
        return { "success": True, "data": project }

    def get_label_by_id(self, label_id: str) -> dict:
        """
        Fetch details of a specific label by its ID.

        Args:
            label_id (str): The unique identifier of the label.

        Returns:
            dict: 
                - If found: { "success": True, "data": LabelInfo }
                - If not found: { "success": False, "error": "Label not found" }

        Constraints:
            - label_id must exist in self.labels.
        """
        if label_id not in self.labels:
            return { "success": False, "error": "Label not found" }
        return { "success": True, "data": self.labels[label_id] }

    def list_tasks_sorted_by_order(self, project_id: str) -> dict:
        """
        Retrieve all tasks belonging to the specified project, sorted by their 'ord' field.

        Args:
            project_id (str): The ID of the project for which to list the tasks.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo]  # Tasks in the project sorted by 'ord' (ascending)
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., project does not exist)
            }

        Constraints:
            - The provided project_id must exist.
            - All tasks with this project_id are included, regardless of status.
            - Returned list is sorted by 'ord' ascending.
        """
        if project_id not in self.projects:
            return {
                "success": False,
                "error": "Project does not exist"
            }

        tasks_in_project = [
            task for task in self.tasks.values()
            if task["project_id"] == project_id
        ]
        tasks_sorted = sorted(tasks_in_project, key=lambda t: t["ord"])
        return {
            "success": True,
            "data": tasks_sorted
        }

    def list_active_tasks(self, user_id: str) -> dict:
        """
        Fetch all active tasks for a given user that are not in archived projects.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo]  # Active tasks in non-archived projects
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user must exist.
            - Only tasks with 'status' == 'active' and NOT in archived projects are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        active_tasks = []
        for task in self.tasks.values():
            # User filter
            if task["user_id"] != user_id:
                continue
            # Active status filter
            if task["status"] != "active":
                continue
            # Project existence and not archived
            proj_id = task["project_id"]
            project = self.projects.get(proj_id)
            if project is None:
                continue  # skip tasks whose project metadata is missing (data problem)
            if project["archived"]:
                continue
            active_tasks.append(task)

        return {"success": True, "data": active_tasks}

    def add_task(
        self, 
        user_id: str, 
        project_id: str, 
        content: str, 
        due_date: str = "",
        priority: int = 1,
        labels: list = None,
        ord: int = None
    ) -> dict:
        """
        Create a new task in a specified project for a specific user.

        Args:
            user_id (str): The ID of the user.
            project_id (str): The ID of the project under which to create the task.
            content (str): The task content/description (required, non-empty).
            due_date (str): (Optional) Due date (string).
            priority (int): (Optional) Task priority (default 1).
            labels (List[str]): (Optional) List of label_ids (must belong to user).
            ord (int): (Optional) The intended order in project (0-based), or append at end if None.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Task created",
                    "task_id": ...,
                    "task": <TaskInfo>
                  }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - Project must exist and be owned by user.
            - All label_ids (if any) must exist and be owned by user.
            - Content cannot be empty.
            - Task ord will be handled so project task order is preserved.
        """

        # Parameter safety
        if labels is None:
            labels = []

        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check project existence & ownership
        project = self.projects.get(project_id)
        if not project or project["user_id"] != user_id:
            return { "success": False, "error": "Project does not exist or does not belong to user" }

        # Validate content
        if not isinstance(content, str) or not content.strip():
            return { "success": False, "error": "Task content must be a non-empty string" }

        # Validate labels existence & ownership
        for label_id in labels:
            label = self.labels.get(label_id)
            if not label or label["user_id"] != user_id:
                return { "success": False, "error": f"Label '{label_id}' does not exist or is not owned by user" }

        # Gather current tasks in this project, sorted by ord
        project_tasks = [t for t in self.tasks.values() 
                         if t["project_id"] == project_id and t["user_id"] == user_id and t["status"] != "deleted"]
        project_tasks.sort(key=lambda t: t["ord"])

        # Determine ord (ordering in project)
        if ord is None or ord < 0 or ord > len(project_tasks):
            ord = len(project_tasks)  # append at end

        # Shift tasks ord if inserting in the middle
        for t in project_tasks[::-1]:
            if t["ord"] >= ord:
                t["ord"] += 1

        # Generate task_id
        task_id = str(uuid.uuid4())
        while task_id in self.tasks:
            task_id = str(uuid.uuid4())

        # Construct TaskInfo
        now_str = datetime.utcnow().isoformat() + "Z"
        task_info = {
            "task_id": task_id,
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "due_date": due_date,
            "priority": int(priority) if isinstance(priority, int) else 1,
            "labels": labels,
            "status": "active",
            "created_at": now_str,
            "completed_at": "",
            "ord": ord
        }

        # Add new task to self.tasks
        self.tasks[task_id] = task_info

        return {
            "success": True,
            "message": "Task created",
            "task_id": task_id,
            "task": task_info
        }

    def edit_task(
        self,
        task_id: str,
        content: str = None,
        due_date: str = None,
        priority: int = None,
        labels: list = None,
        project_id: str = None,
    ) -> dict:
        """
        Update content, due date, priority, labels, or project of an existing task.

        Args:
            task_id (str): The ID of the task to update.
            content (str, optional): New content for the task.
            due_date (str, optional): New due date.
            priority (int, optional): New priority (integer).
            labels (list, optional): List of new label_ids (strings).
            project_id (str, optional): New project_id to move the task to.

        Returns:
            dict: {
                "success": True,
                "message": "Task updated successfully"
              }
              or
              {
                "success": False,
                "error": <reason>
              }

        Constraints:
            - Task must exist and not be deleted.
            - If project_id is changed, new project must exist and belong to the same user.
            - If labels are updated, all labels must exist and be owned by the task's user.
            - Only properties supplied (not None) are updated.
            - Task ordering ('ord') will be assigned appropriately if project changes.
        """

        # Check if task exists
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task does not exist" }
        if task['status'] == 'deleted':
            return { "success": False, "error": "Cannot edit a deleted task" }

        user_id = task['user_id']

        # Update content
        if content is not None:
            task['content'] = content

        # Update due_date
        if due_date is not None:
            task['due_date'] = due_date

        # Update priority
        if priority is not None:
            if not isinstance(priority, int) or priority < 1:
                return { "success": False, "error": "Invalid priority value" }
            task['priority'] = priority

        # Update labels
        if labels is not None:
            # Verify all labels exist and belong to user
            if not isinstance(labels, list):
                return { "success": False, "error": "Labels must be a list" }
            for label_id in labels:
                label = self.labels.get(label_id)
                if not label or label['user_id'] != user_id:
                    return { "success": False, "error": f"Invalid label: {label_id}" }
            task['labels'] = labels

        # Update project_id
        if project_id is not None and project_id != task['project_id']:
            new_project = self.projects.get(project_id)
            if not new_project or new_project['user_id'] != user_id:
                return { "success": False, "error": "Target project does not exist or not owned by user" }
            # Remove from old project's order, add to new project
            # Assign to the end of new project's tasks (max ord + 1)
            new_project_task_ords = [
                t['ord'] for t in self.tasks.values()
                if t['project_id'] == project_id and t['user_id'] == user_id
            ]
            new_ord = (max(new_project_task_ords) + 1) if new_project_task_ords else 1
            task['ord'] = new_ord
            task['project_id'] = project_id

        # Commit changes
        self.tasks[task_id] = task
        return { "success": True, "message": "Task updated successfully" }


    def complete_task(self, task_id: str) -> dict:
        """
        Marks the specified task as completed by:
            - Setting its status to 'completed'
            - Updating the completed_at timestamp to current time (UTC)
    
        Args:
            task_id (str): The unique identifier for the task to complete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Task marked as completed" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Task must exist.
            - Task must not be already completed or deleted.
            - Only updates status and completed_at.
        """
        if task_id not in self.tasks:
            return { "success": False, "error": "Task not found" }

        task = self.tasks[task_id]
        if task["status"] == "deleted":
            return { "success": False, "error": "Cannot complete a deleted task" }
        if task["status"] == "completed":
            return { "success": False, "error": "Task is already completed" }

        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat() + "Z"

        self.tasks[task_id] = task  # Not strictly needed with mutable dict, but for clarity

        return { "success": True, "message": "Task marked as completed" }

    def delete_task(self, task_id: str) -> dict:
        """
        Mark the specified task as 'deleted' and remove it from all active lists.

        Args:
            task_id (str): The ID of the task to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Task marked as deleted and removed from active lists."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, already deleted, etc.)
            }

        Constraints:
            - Task must exist.
            - Cannot delete a task that is already deleted.
            - Task status must be set to 'deleted'.
            - Only tasks with status other than 'deleted' can be deleted.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }
        if task["status"] == "deleted":
            return { "success": False, "error": "Task is already deleted" }
        task["status"] = "deleted"
        # Optionally, could clear or update 'completed_at' or related info for bookkeeping
        self.tasks[task_id] = task
        return { "success": True, "message": "Task marked as deleted and removed from active lists." }

    def restore_task(self, task_id: str) -> dict:
        """
        Change the status of a “deleted” task back to “active”.

        Args:
            task_id (str): Unique identifier of the task to restore.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Task restored to active status" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Task must exist.
            - Task must have status "deleted".
            - Should not restore to "active" if the parent project is archived.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }

        if task["status"] != "deleted":
            return { "success": False, "error": "Task is not deleted and cannot be restored" }

        project_id = task["project_id"]
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Associated project not found" }
        if project.get("archived", False):
            return { "success": False, "error": "Cannot restore task into an archived project" }

        # Restore task
        task["status"] = "active"
        # (Optionally, could clear completed_at, but that's not required by spec.)

        self.tasks[task_id] = task

        return { "success": True, "message": "Task restored to active status" }

    def reorder_tasks_within_project(self, project_id: str, task_id_order: list) -> dict:
        """
        Adjust the relative ordering ("ord") of all tasks within a given project.

        Args:
            project_id (str): The project whose tasks are to be reordered.
            task_id_order (list of str): List of task IDs (within project) in desired order. All active, non-deleted tasks must be present and appear once.

        Returns:
            dict: {
                "success": True,
                "message": "Tasks within project reordered successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Project must exist.
            - All specified task_ids must belong to the project and exist, status not 'deleted'.
            - Duplicate task IDs in input are not allowed.
            - All active (status != 'deleted') tasks for the project must be included in task_id_order (no missing/extra).
            - The ord field for each task is updated to their position (starting from 1).
        """
        # Check if project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}
    
        # Gather active (not deleted) tasks within project
        tasks_in_project = [
            task for task in self.tasks.values()
            if task["project_id"] == project_id and task["status"] != "deleted"
        ]
        task_ids_in_project = set(task["task_id"] for task in tasks_in_project)

        input_task_ids = list(task_id_order)
        if len(input_task_ids) != len(set(input_task_ids)):
            return {"success": False, "error": "Duplicate task IDs provided."}
    
        # Ensure all relevant task IDs are covered, and no extras
        if set(input_task_ids) != task_ids_in_project:
            return {
                "success": False,
                "error": (
                    "Input task ID list does not match all active tasks in project. "
                    "Include all task IDs for active (not deleted) tasks exactly once."
                )
            }

        # Reorder: assign ord = (index + 1)
        for idx, task_id in enumerate(input_task_ids):
            self.tasks[task_id]["ord"] = idx + 1

        return {
            "success": True,
            "message": "Tasks within project reordered successfully."
        }

    def add_project(
        self,
        user_id: str,
        name: str,
        description: str = "",
        archived: bool = False
    ) -> dict:
        """
        Create a new project for a user.

        Args:
            user_id (str): ID of the user who will own the project.
            name (str): Project name (should not be empty).
            description (str, optional): Text description (default: '').
            archived (bool, optional): If the project is initially archived (default: False).

        Returns:
            dict: {
                "success": True,
                "message": "Project <name> created.",
                "project": ProjectInfo
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist.
            - Each project is scoped to a single user.
            - Project ordering ('ord') must be preserved; new project should be last (max ord + 1 for this user).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if not name or not name.strip():
            return { "success": False, "error": "Project name must not be empty" }

        # Find max 'ord' among this user's projects to append last
        user_projects = [
            p for p in self.projects.values() if p['user_id'] == user_id
        ]
        max_ord = max([p['ord'] for p in user_projects], default=0)
        new_ord = max_ord + 1

        # Generate project_id (e.g., 'proj_<N+1>')
        existing_ids = set(self.projects.keys())
        num = 1
        while True:
            project_id = f"proj_{num}"
            if project_id not in existing_ids:
                break
            num += 1

        project: ProjectInfo = {
            "project_id": project_id,
            "user_id": user_id,
            "name": name.strip(),
            "description": description,
            "archived": archived,
            "ord": new_ord
        }

        self.projects[project_id] = project

        return {
            "success": True,
            "message": f"Project '{name.strip()}' created.",
            "project": project
        }

    def archive_project(self, project_id: str) -> dict:
        """
        Archives a project by setting its 'archived' property to True.
        Optionally handles contained tasks as per user settings (not implemented; tasks remain unchanged).

        Args:
            project_id (str): The ID of the project to archive.

        Returns:
            dict:
                On success: { "success": True, "message": "Project archived successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The project must exist.
            - If already archived, inform of no action.
            - Contained tasks are unaffected unless user settings specify otherwise (not implemented).
        """
        # Verify project exists
        project = self.projects.get(project_id)
        if project is None:
            return { "success": False, "error": "Project does not exist." }
    
        if project["archived"]:
            return { "success": False, "error": "Project is already archived." }
    
        # Archive the project
        project["archived"] = True
        self.projects[project_id] = project  # Not necessary, but keeps style consistent

        # Handle tasks: in a full implementation, would check user settings. Here, do nothing.
        # Example:
        # user_id = project["user_id"]
        # user_settings = self.users[user_id].get("preference", {})
        # # Apply actions to contained tasks as per settings...

        return { "success": True, "message": "Project archived successfully." }

    def delete_project(self, project_id: str, policy_on_tasks: str = "delete") -> dict:
        """
        Remove a project from the system.
        Optionally applies an action to all tasks within the project:
            - 'delete' (default): mark all contained tasks as deleted.
            - 'archive': mark all contained tasks as completed.
            - 'leave': leave tasks status unchanged.

        Args:
            project_id (str): The ID of the project to delete.
            policy_on_tasks (str, optional): What to do with contained tasks.
                Must be one of {'delete', 'archive', 'leave'}.

        Returns:
            dict:
                - On success: { "success": True, "message": str }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Project must exist.
            - Project and its tasks must be correctly updated.
            - Only valid policy_on_tasks values are accepted.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }

        if policy_on_tasks not in {"delete", "archive", "leave"}:
            return { "success": False, "error": "Invalid policy_on_tasks. Use 'delete', 'archive', or 'leave'." }

        # Remove the project
        project = self.projects.pop(project_id)
        affected_tasks = [task for task in self.tasks.values() if task["project_id"] == project_id]

        if policy_on_tasks == "delete":
            for task in affected_tasks:
                task["status"] = "deleted"
        elif policy_on_tasks == "archive":
            for task in affected_tasks:
                task["status"] = "completed"
        # else: leave tasks unchanged

        task_action = {
            "delete": "marked as deleted",
            "archive": "marked as completed",
            "leave": "left unchanged"
        }[policy_on_tasks]

        return {
            "success": True,
            "message": f"Project '{project.get('name', project_id)}' deleted and {len(affected_tasks)} tasks {task_action}."
        }

    def edit_project(
        self,
        project_id: str,
        name: str = None,
        description: str = None
    ) -> dict:
        """
        Modify the name and/or description of an existing project.

        Args:
            project_id (str): The unique ID of the project to edit.
            name (str, optional): New name for the project. If None, name is not changed.
            description (str, optional): New description for the project. If None, description is not changed.

        Returns:
            dict: {
                "success": True,
                "message": "Project edited successfully"
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., project not found or no fields provided
            }

        Constraints:
            - The project must exist.
            - At least one of name or description must be provided to update.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project not found" }
        if name is None and description is None:
            return { "success": False, "error": "No changes specified (name or description required)" }

        project = self.projects[project_id]
        if name is not None:
            project['name'] = name
        if description is not None:
            project['description'] = description
        return { "success": True, "message": "Project edited successfully" }


    def add_label(self, user_id: str, name: str) -> dict:
        """
        Create a new label for the user.

        Args:
            user_id (str): The ID of the user for whom the label is created.
            name (str): The desired label name (must be unique for this user).

        Returns:
            dict:
                On success: { "success": True, "message": "Label '<name>' created for user <user_id>." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - user_id must exist in self.users.
            - label names must be unique per user.
        """
        # Check for user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Ensure label name is unique per user
        for label in self.labels.values():
            if label["user_id"] == user_id and label["name"] == name:
                return { "success": False, "error": f"Label '{name}' already exists for this user." }

        # Generate a unique label_id (use uuid4 string)
        label_id = str(uuid.uuid4())
        label_info = {
            "label_id": label_id,
            "user_id": user_id,
            "name": name
        }
        self.labels[label_id] = label_info

        return { "success": True, "message": f"Label '{name}' created for user {user_id}." }

    def edit_label(self, label_id: str, new_name: str) -> dict:
        """
        Change the name of an existing label.

        Args:
            label_id (str): The ID of the label to edit.
            new_name (str): The new name to set for the label.

        Returns:
            dict:
                On success: { "success": True, "message": "Label name updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - label_id must exist.
            - new_name must not be empty.
            - (Optional) Uniqueness of label name per user is not enforced here.

        """
        label = self.labels.get(label_id)
        if label is None:
            return { "success": False, "error": "Label not found" }

        if not isinstance(new_name, str) or not new_name.strip():
            return { "success": False, "error": "New name must be a non-empty string" }

        label["name"] = new_name.strip()
        return { "success": True, "message": "Label name updated" }

    def delete_label(self, label_id: str) -> dict:
        """
        Remove a label from the user's workspace and from all associated tasks.

        Args:
            label_id (str): The ID of the label to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Label deleted and removed from all tasks."
            }
            or
            {
                "success": False,
                "error": "Label does not exist."
            }

        Constraints:
            - Label must exist.
            - Removes label from all tasks of the associated user.
            - Only modifies tasks belonging to the label's user.
        """
        if label_id not in self.labels:
            return { "success": False, "error": "Label does not exist." }
    
        # Get the user_id of the label to scope task modifications
        label_info = self.labels[label_id]
        user_id = label_info["user_id"]

        # Remove label_id from all tasks (of the label's user) where it appears
        for task in self.tasks.values():
            if task["user_id"] == user_id and label_id in task["labels"]:
                task["labels"] = [lid for lid in task["labels"] if lid != label_id]

        # Remove the label from labels dict
        del self.labels[label_id]

        return { "success": True, "message": "Label deleted and removed from all tasks." }

    def purge_completed_or_deleted_tasks(self, user_id: str) -> dict:
        """
        Permanently remove all tasks for the given user that are marked as 'completed' or 'deleted'.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Purged N completed or deleted tasks for user <user_id>"
                    }
                - On failure (e.g., user does not exist):
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - Only tasks belonging to the specified user are affected.
            - Only tasks with status 'completed' or 'deleted' are purged.
            - Other users' tasks are not affected.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        to_purge = [tid for tid, task in self.tasks.items()
                    if task["user_id"] == user_id and task["status"] in ("completed", "deleted")]
        purge_count = len(to_purge)

        for tid in to_purge:
            del self.tasks[tid]

        return {
            "success": True,
            "message": f"Purged {purge_count} completed or deleted tasks for user {user_id}"
        }

    def batch_update_task_status(self, task_ids: list, new_status: str) -> dict:
        """
        Set the status for multiple tasks in a batch (e.g., mark multiple tasks as deleted or completed).

        Args:
            task_ids (list of str): List of task IDs to update.
            new_status (str): The status to set. Must be one of 'active', 'completed', 'deleted'.

        Returns:
            dict:
              On success:
                {
                  "success": True,
                  "message": "N tasks updated to status '<new_status>'"
                }
              On failure:
                {
                  "success": False,
                  "error": "Error message"
                }
        Constraints:
            - Each task_id must exist in the system.
            - The new_status must be a valid status: 'active', 'completed', 'deleted'.
        """
        valid_statuses = {"active", "completed", "deleted"}
        if new_status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status '{new_status}'. Valid options: {', '.join(sorted(valid_statuses))}."
            }

        if not isinstance(task_ids, list) or not all(isinstance(tid, str) for tid in task_ids):
            return { "success": False, "error": "task_ids must be a list of strings." }

        # Check that all task_ids exist
        missing = [tid for tid in task_ids if tid not in self.tasks]
        if missing:
            return {
                "success": False,
                "error": f"The following task_id(s) were not found: {', '.join(missing)}"
            }

        # Perform update
        count = 0
        for tid in task_ids:
            self.tasks[tid]["status"] = new_status
            count += 1

        return {
            "success": True,
            "message": f"{count} task(s) updated to status '{new_status}'."
        }


class PersonalTaskManagementSystem(BaseEnv):
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

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_tasks(self, **kwargs):
        return self._call_inner_tool('list_user_tasks', kwargs)

    def list_user_projects(self, **kwargs):
        return self._call_inner_tool('list_user_projects', kwargs)

    def list_user_labels(self, **kwargs):
        return self._call_inner_tool('list_user_labels', kwargs)

    def get_task_by_id(self, **kwargs):
        return self._call_inner_tool('get_task_by_id', kwargs)

    def list_tasks_by_status(self, **kwargs):
        return self._call_inner_tool('list_tasks_by_status', kwargs)

    def list_tasks_by_project(self, **kwargs):
        return self._call_inner_tool('list_tasks_by_project', kwargs)

    def list_tasks_by_label(self, **kwargs):
        return self._call_inner_tool('list_tasks_by_label', kwargs)

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def get_label_by_id(self, **kwargs):
        return self._call_inner_tool('get_label_by_id', kwargs)

    def list_tasks_sorted_by_order(self, **kwargs):
        return self._call_inner_tool('list_tasks_sorted_by_order', kwargs)

    def list_active_tasks(self, **kwargs):
        return self._call_inner_tool('list_active_tasks', kwargs)

    def add_task(self, **kwargs):
        return self._call_inner_tool('add_task', kwargs)

    def edit_task(self, **kwargs):
        return self._call_inner_tool('edit_task', kwargs)

    def complete_task(self, **kwargs):
        return self._call_inner_tool('complete_task', kwargs)

    def delete_task(self, **kwargs):
        return self._call_inner_tool('delete_task', kwargs)

    def restore_task(self, **kwargs):
        return self._call_inner_tool('restore_task', kwargs)

    def reorder_tasks_within_project(self, **kwargs):
        return self._call_inner_tool('reorder_tasks_within_project', kwargs)

    def add_project(self, **kwargs):
        return self._call_inner_tool('add_project', kwargs)

    def archive_project(self, **kwargs):
        return self._call_inner_tool('archive_project', kwargs)

    def delete_project(self, **kwargs):
        return self._call_inner_tool('delete_project', kwargs)

    def edit_project(self, **kwargs):
        return self._call_inner_tool('edit_project', kwargs)

    def add_label(self, **kwargs):
        return self._call_inner_tool('add_label', kwargs)

    def edit_label(self, **kwargs):
        return self._call_inner_tool('edit_label', kwargs)

    def delete_label(self, **kwargs):
        return self._call_inner_tool('delete_label', kwargs)

    def purge_completed_or_deleted_tasks(self, **kwargs):
        return self._call_inner_tool('purge_completed_or_deleted_tasks', kwargs)

    def batch_update_task_status(self, **kwargs):
        return self._call_inner_tool('batch_update_task_status', kwargs)

