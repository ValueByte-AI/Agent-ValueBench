# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional




class TaskInfo(TypedDict):
    task_id: str
    task_type: str
    initiator_id: str
    status: str
    result: Optional[str]  # actual type of result may vary
    created_at: str
    related_resource_id: str


class QuizInfo(TypedDict):
    quiz_id: str
    subject: str
    creator_id: str
    questions: List[str]
    creation_time: str
    assigned_to: List[str]


class UserInfo(TypedDict):
    _id: str
    role: str  # 'educator' or 'student'
    name: str
    associated_task: List[str]  # List of task_ids


class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for orchestrating and tracking asynchronous and interactive tasks
        on an educational platform.
        """

        # Tasks: {task_id: TaskInfo}
        # Represents any asynchronous action or request with tracking of type, creator, state, and result.
        self.tasks: Dict[str, TaskInfo] = {}

        # Quizzes: {quiz_id: QuizInfo}
        # Represents quiz resources tied to subjects and creators.
        self.quizzes: Dict[str, QuizInfo] = {}

        # Users: {_id: UserInfo}
        # Both educators and students, with roles and task associations.
        self.users: Dict[str, UserInfo] = {}

        # Constraints (documented for implementation):
        # - Each task must have a unique task_id.
        # - Only educators can initiate resource creation tasks (e.g., quiz generation).
        # - Task results may only be retrieved by authorized users (initiators or assignees).
        # - Every quiz is associated with a subject and must have a creator (educator).
        # - Task status transitions (e.g., pending → completed) must follow the system logic.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details by user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of why the operation failed (e.g., user not found)
            }

        Constraints:
            - The user ID must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user(s) information by their name.

        Args:
            name (str): The name of the user to find.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[UserInfo]  # List of user info dicts with given name
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g. not found)
                  }

        Constraints:
            - All users with the given name are returned.
            - If no user with that name exists, an error is returned.
        """
        if not name:
            return { "success": False, "error": "No user found with the given name" }

        matched_users = [user for user in self.users.values() if user["name"] == name]

        if not matched_users:
            return { "success": False, "error": "No user found with the given name" }

        return { "success": True, "data": matched_users }

    def list_user_tasks(self, user_id: str) -> dict:
        """
        List all tasks (full TaskInfo) associated with a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo],  # List of task dictionaries (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user not found)
            }

        Constraints:
            - User must exist.
            - Tasks returned must exist in the tasks registry.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Only include tasks that actually exist in self.tasks for data safety
        task_infos = [
            self.tasks[task_id]
            for task_id in user.get("associated_task", [])
            if task_id in self.tasks
        ]
        return { "success": True, "data": task_infos }

    def get_user_role(self, user_id: str) -> dict:
        """
        Query a user's role ('educator' or 'student') in the system.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
            {
                "success": True,
                "data": role (str)
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - User with the given user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
    
        role = user.get("role")
        if not role:
            return {"success": False, "error": "User role not assigned"}
    
        return {"success": True, "data": role}

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Retrieve details for a given task ID.
    
        Args:
            task_id (str): The unique identifier of the task to retrieve.
    
        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": TaskInfo  # All properties for the task.
                }
                On failure (e.g. task_id doesn't exist):
                {
                    "success": False,
                    "error": str  # "Task not found"
                }
        Constraints:
            - task_id must exist in the system.
            - No authorization is required to retrieve a task's basic info.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }
        return { "success": True, "data": task }

    def get_task_status(self, task_id: str) -> dict:
        """
        Return the current status of a task by its task_id.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            dict: {
                "success": True,
                "data": str  # The current status of the task.
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., task not found.
            }

        Constraints:
            - The task_id must exist in the system.
            - No authorization check is required for status query.
        """
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task not found" }

        return { "success": True, "data": task["status"] }

    def get_task_result(self, task_id: str, user_id: str) -> dict:
        """
        Retrieve the result/content of a given task.
        Only the task initiator or, if the task is associated with a resource (e.g., quiz), an authorized assignee may retrieve the result.

        Args:
            task_id (str): The task identifier.
            user_id (str): The ID of the user requesting the result.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": <task_result: Optional[str]>
                }
                Failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Task must exist.
            - User must exist.
            - The requester must be the task initiator or an explicitly authorized assignee for the resource.
        """
        # Check that user exists
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }

        # Check that task exists
        task = self.tasks.get(task_id)
        if task is None:
            return { "success": False, "error": "Task not found" }

        # Authorization (initiator)
        if task["initiator_id"] == user_id:
            return { "success": True, "data": task.get("result") }

        # Authorization (assignee for related resource, e.g., quiz)
        related_resource_id = task.get("related_resource_id")
        if related_resource_id:
            quiz = self.quizzes.get(related_resource_id)
            if quiz and user_id in quiz.get("assigned_to", []):
                return { "success": True, "data": task.get("result") }

        # Not authorized
        return { "success": False, "error": "User not authorized to access this task result" }

    def list_tasks_by_status(self, status: str) -> dict:
        """
        List all tasks filtered by a specific status.

        Args:
            status (str): The status value to filter tasks by (e.g., 'pending', 'completed').

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo],  # List of matching tasks (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., missing status)
            }

        Constraints:
            - Status must be specified (non-empty string).
        """
        if not status or not isinstance(status, str):
            return { "success": False, "error": "A valid task status must be specified." }
    
        filtered_tasks = [
            task_info for task_info in self.tasks.values()
            if task_info["status"] == status
        ]
        return { "success": True, "data": filtered_tasks }

    def list_tasks_by_type(self, task_type: str) -> dict:
        """
        List all tasks of a specific type (e.g., analytics, quiz generation).

        Args:
            task_type (str): The exact type of tasks to filter (case-sensitive).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[TaskInfo]  # List of task dicts matching the task_type
                }
                or
                {
                    "success": False,
                    "error": str  # If invalid input (e.g., blank task_type)
                }

        Constraints:
            - task_type must be a non-empty string.
            - No permission check: anyone can list.
        """
        if not isinstance(task_type, str) or not task_type.strip():
            return {"success": False, "error": "task_type must be a non-empty string."}

        filtered_tasks = [
            task_info for task_info in self.tasks.values()
            if task_info.get("task_type") == task_type
        ]
        return {"success": True, "data": filtered_tasks}

    def get_quiz_by_id(self, quiz_id: str) -> dict:
        """
        Retrieve all details of a given quiz using its quiz_id.

        Args:
            quiz_id (str): Unique identifier of the quiz.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": QuizInfo  # All attributes of the quiz
                }
                On failure:
                {
                    "success": False,
                    "error": "Quiz not found"
                }
        Constraints:
            - The quiz_id must exist in the system.
        """
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return {"success": False, "error": "Quiz not found"}

        return {"success": True, "data": quiz}

    def list_quizzes_by_creator(self, educator_id: str) -> dict:
        """
        List all quizzes created by a specific educator.

        Args:
            educator_id (str): The unique user ID of the educator.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[QuizInfo]  # List of quiz info dicts, can be empty if none created
                }
                or
                {
                    "success": False,
                    "error": str  # Error message, e.g. educator not found, not an educator, etc.
                }

        Constraints:
            - educator_id must exist and must refer to a user with role == 'educator'
            - Returns empty list if educator exists but has created no quizzes
        """
        user = self.users.get(educator_id)
        if not user:
            return {"success": False, "error": "Educator with given ID does not exist"}
        if user["role"] != "educator":
            return {"success": False, "error": "User is not an educator"}
        quizzes = [
            quiz_info
            for quiz_info in self.quizzes.values()
            if quiz_info["creator_id"] == educator_id
        ]
        return {"success": True, "data": quizzes}

    def list_quizzes_for_user(self, user_id: str) -> dict:
        """
        List all quizzes assigned to a specific user (typically a student).

        Args:
            user_id (str): The user ID of the student for whom to list assigned quizzes.

        Returns:
            dict: {
                "success": True,
                "data": List[QuizInfo],  # List of quizzes assigned to the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User not found"
            }

        Constraints:
            - user_id must exist in the system.
            - Quizzes are assigned only to students, but if queried for educators, returns empty list.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        quizzes_for_user = [
            quiz_info for quiz_info in self.quizzes.values()
            if user_id in quiz_info.get("assigned_to", [])
        ]

        return { "success": True, "data": quizzes_for_user }

    def create_task(
        self,
        task_id: str,
        task_type: str,
        initiator_id: str,
        created_at: str,
        related_resource_id: str = ""
    ) -> dict:
        """
        Initiate a new task (e.g., quiz generation or analysis).
        Enforces:
            - Unique task_id.
            - Only educators can initiate resource creation tasks (e.g., 'quiz_generation').
            - Initiator must be a valid user.
        Automatically sets initial status to 'pending' and result to None.
        Associates the task with the initiator's user profile.

        Args:
            task_id (str): Unique identifier for the task.
            task_type (str): Type of the task (e.g., 'quiz_generation', 'analysis').
            initiator_id (str): User ID of who initiates the task.
            created_at (str): Timestamp of creation.
            related_resource_id (str, optional): Associated resource.

        Returns:
            dict:
                { "success": True, "message": str } on success,
                or { "success": False, "error": str } describing failure.
        """

        # Check uniqueness of task_id
        if task_id in self.tasks:
            return { "success": False, "error": "Task ID already exists." }

        # Check initiator exists
        initiator = self.users.get(initiator_id)
        if not initiator:
            return { "success": False, "error": "Initiator does not exist." }

        # Resource creation restriction
        resource_creation_types = {"quiz_generation"}  # extend as needed
        if task_type in resource_creation_types and initiator["role"] != "educator":
            return {
                "success": False,
                "error": "Only educators can initiate resource creation tasks."
            }

        # Create the task
        new_task: TaskInfo = {
            "task_id": task_id,
            "task_type": task_type,
            "initiator_id": initiator_id,
            "status": "pending",
            "result": None,
            "created_at": created_at,
            "related_resource_id": related_resource_id
        }
        self.tasks[task_id] = new_task

        # Associate task with initiator
        initiator["associated_task"].append(task_id)

        return { "success": True, "message": f"Task {task_id} created successfully." }

    def update_task_status(self, task_id: str, new_status: str) -> dict:
        """
        Change the status of a task, ensuring the transition is valid per the allowed state machine.

        Args:
            task_id (str): The ID of the task to update.
            new_status (str): The new status to set.

        Returns:
            dict: {
                "success": True, "message": "Task status updated from <old> to <new>."
            }
            or
            {
                "success": False, "error": "<error description>"
            }

        Constraints:
            - Task must exist.
            - Status transitions must be valid as per system logic.
            - Typical statuses: pending → in_progress → completed/failed/cancelled, etc.
        """
        # Allowed transitions: (could be extended as per system requirements)
        allowed_transitions = {
            "pending": ["in_progress", "completed", "failed", "cancelled"],
            "in_progress": ["completed", "failed", "cancelled"],
            "completed": [],
            "failed": [],
            "cancelled": []
        }
        valid_statuses = set(allowed_transitions.keys())

        # 1. Task must exist
        task = self.tasks.get(task_id)
        if not task:
            return { "success": False, "error": "Task does not exist." }

        current_status = task["status"]

        # 2. Check if current status and new_status are valid
        if current_status not in valid_statuses:
            return { "success": False, "error": "Current status is invalid: '{}'".format(current_status) }

        if new_status not in valid_statuses:
            return { "success": False, "error": "Requested status '{}' is not recognized.".format(new_status) }

        # 3. No-op or already in desired status
        if current_status == new_status:
            return { "success": True, "message": f"Task already in status '{new_status}'." }

        # 4. Check allowed transitions
        if new_status not in allowed_transitions[current_status]:
            return {
                "success": False,
                "error": f"Cannot transition task from '{current_status}' to '{new_status}'."
            }

        # 5. Update status
        task["status"] = new_status

        return {
            "success": True,
            "message": f"Task status updated from '{current_status}' to '{new_status}'."
        }

    def set_task_result(self, task_id: str, result: str) -> dict:
        """
        Attach/store the result string to a completed task.

        Args:
            task_id (str): The unique identifier of the task.
            result (str): The result data to attach to the task.

        Returns:
            dict: On success:
                {"success": True, "message": "Result set for task <task_id>."}
                On failure:
                {"success": False, "error": "<reason>"}

        Constraints:
            - Task must exist.
            - Task status must be 'completed' to set result.
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        if task["status"] != "completed":
            return {"success": False, "error": "Task is not completed; cannot set result"}

        task["result"] = result
        return {"success": True, "message": f"Result set for task {task_id}."}

    def create_quiz(
        self,
        quiz_id: str,
        subject: str,
        creator_id: str,
        questions: list,
        creation_time: str,
        assigned_to: list
    ) -> dict:
        """
        Create a new quiz resource, linked to an educator and subject.

        Args:
            quiz_id (str): Unique identifier for the quiz.
            subject (str): The subject of the quiz.
            creator_id (str): Educator's user ID who creates the quiz.
            questions (List[str]): List of quiz questions.
            creation_time (str): Timestamp for quiz creation.
            assigned_to (List[str]): List of student IDs assigned to the quiz.

        Returns:
            dict: {
                "success": True,
                "message": "Quiz created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - quiz_id must be unique.
            - creator_id must refer to an existing educator.
            - subject and creator_id are required.
            - Each quiz must have a subject and a creator.
        """

        # Check for quiz_id uniqueness
        if quiz_id in self.quizzes:
            return { "success": False, "error": "Quiz ID already exists." }

        # Check creator existence
        creator_info = self.users.get(creator_id)
        if not creator_info:
            return { "success": False, "error": "Creator (educator) does not exist." }

        # Check creator role
        if creator_info.get('role') != 'educator':
            return { "success": False, "error": "Only educators can create quizzes." }

        # Validate subject and questions (subject is required)
        if not subject or not isinstance(subject, str):
            return { "success": False, "error": "Quiz subject is required." }
        if not isinstance(questions, list):
            return { "success": False, "error": "Questions must be a list." }

        # Create the quiz
        quiz_info = {
            "quiz_id": quiz_id,
            "subject": subject,
            "creator_id": creator_id,
            "questions": questions,
            "creation_time": creation_time,
            "assigned_to": assigned_to if isinstance(assigned_to, list) else []
        }
        self.quizzes[quiz_id] = quiz_info

        return { "success": True, "message": "Quiz created successfully." }

    def assign_quiz_to_students(self, quiz_id: str, student_ids: list) -> dict:
        """
        Assign an existing quiz to a list of students by updating the assigned_to field.

        Args:
            quiz_id (str): The ID of the quiz resource to assign.
            student_ids (List[str]): A list of student user IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Quiz assigned to students successfully"
            }
            or
            {
                "success": False,
                "error": "Error message"
            }

        Constraints:
            - The quiz must exist.
            - Each user in student_ids must exist and be of role 'student'.
            - Duplicate assignments are ignored (idempotent).
        """
        # Check quiz existence
        if quiz_id not in self.quizzes:
            return {"success": False, "error": "Quiz not found"}
        quiz = self.quizzes[quiz_id]
        # Validate students
        invalid_students = []
        for student_id in student_ids:
            user = self.users.get(student_id)
            if not user or user.get("role") != "student":
                invalid_students.append(student_id)
        if invalid_students:
            return {
                "success": False,
                "error": f"Invalid or non-student user IDs: {', '.join(invalid_students)}"
            }
        # Assign, ensuring no duplicates
        previous_assigned = set(quiz.get("assigned_to", []))
        quiz["assigned_to"] = list(previous_assigned.union(set(student_ids)))
        self.quizzes[quiz_id] = quiz  # update, although dict is mutable

        return {"success": True, "message": "Quiz assigned to students successfully"}

    def link_task_to_quiz(self, task_id: str, quiz_id: str) -> dict:
        """
        Links a resource creation task (e.g., quiz generation) to its resulting quiz
        by setting the related_resource_id field.

        Args:
            task_id (str): The unique ID of the resource creation (e.g., quiz generation) task.
            quiz_id (str): The unique ID of the quiz to link as the resource.

        Returns:
            dict: {
                "success": True,
                "message": "Task successfully linked to quiz."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The task_id must exist in the tasks dictionary.
            - The quiz_id must exist in the quizzes dictionary.
            - Only resource creation tasks (e.g., task_type == 'quiz_generation') may be linked to a quiz.
            - The related_resource_id must NOT already be set for the task.
            - Does not overwrite existing links.
        """
        # Check if the task exists
        task_info = self.tasks.get(task_id)
        if not task_info:
            return {"success": False, "error": "Task does not exist."}
    
        # Check if the quiz exists
        quiz_info = self.quizzes.get(quiz_id)
        if not quiz_info:
            return {"success": False, "error": "Quiz does not exist."}
    
        # Only resource creation tasks can be linked
        # Assuming 'quiz_generation' is the canonical task_type for quiz creation
        # (This could be refined if other types are supported)
        if task_info["task_type"] not in ["quiz_generation", "resource_creation"]:
            return {
                "success": False,
                "error": "Only resource creation tasks may be linked to quizzes."
            }

        # Prevent duplicate/overwrite links
        if task_info.get("related_resource_id"):
            return {
                "success": False,
                "error": "Task is already linked to a resource."
            }

        # Link
        task_info["related_resource_id"] = quiz_id
        self.tasks[task_id] = task_info

        return {
            "success": True,
            "message": "Task successfully linked to quiz."
        }

    def add_user(self, _id: str, role: str, name: str) -> dict:
        """
        Add a new user (educator or student) to the system.

        Args:
            _id (str): Unique identifier for the user.
            role (str): User's role, must be either 'educator' or 'student'.
            name (str): Name of the user.

        Returns:
            dict: {
                "success": True,
                "message": "User added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User ID (_id) must be unique across all users.
            - Role must be either 'educator' or 'student'.
            - User's name should not be empty.
            - Associated tasks are initialized empty.
        """
        if not _id or not isinstance(_id, str):
            return {"success": False, "error": "User ID must be a non-empty string."}
        if _id in self.users:
            return {"success": False, "error": "User ID already exists."}
        if role not in ("educator", "student"):
            return {"success": False, "error": "Role must be either 'educator' or 'student'."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "User name must be a non-empty string."}

        self.users[_id] = {
            "_id": _id,
            "role": role,
            "name": name,
            "associated_task": []
        }
        return {"success": True, "message": "User added successfully."}

    def associate_task_with_user(self, user_id: str, task_id: str, action: str) -> dict:
        """
        Associate (add) or dissociate (remove) a task_id with/from a user's associated_task list.

        Args:
            user_id (str): User _id (must exist).
            task_id (str): Task task_id (must exist).
            action (str): 'add' to associate, 'remove' to dissociate.

        Returns:
            dict: {
                "success": True,
                "message": "Task <task_id> added/removed for user <user_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User and task must both exist.
            - Only 'add' or 'remove' are accepted as action.
            - Adding an already-added task is a no-op (success).
            - Removing a non-associated task is a no-op (success).
        """
        if user_id not in self.users:
            return { "success": False, "error": f"User {user_id} does not exist." }
        if task_id not in self.tasks:
            return { "success": False, "error": f"Task {task_id} does not exist." }
        if action not in ["add", "remove"]:
            return { "success": False, "error": "Invalid action. Must be 'add' or 'remove'." }

        user_tasks = self.users[user_id]["associated_task"]

        if action == "add":
            if task_id not in user_tasks:
                user_tasks.append(task_id)
            return { "success": True, "message": f"Task {task_id} added for user {user_id}." }
        else:  # action == "remove"
            if task_id in user_tasks:
                user_tasks.remove(task_id)
            return { "success": True, "message": f"Task {task_id} removed for user {user_id}." }

    def remove_task(self, task_id: str) -> dict:
        """
        Delete a task from the system, if permissible.

        Args:
            task_id (str): The unique identifier of the task to remove.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Task <task_id> removed from the system." }
                - On failure: { "success": False, "error": str }

        Constraints:
            - The task must exist in the system.
            - Only tasks in a terminal state ("completed", "canceled") are eligible for removal.
            - All references to this task in UserInfo.associated_task lists must be removed to avoid dangling references.
        """

        # Check if task exists
        if task_id not in self.tasks:
            return { "success": False, "error": "Task does not exist." }

        # Only completed or canceled tasks may be removed
        terminal_statuses = {"completed", "canceled", "cancelled"}
        status = self.tasks[task_id]["status"]
        if status not in terminal_statuses:
            return { 
                "success": False,
                "error": f"Task status '{status}' does not permit removal. Only 'completed' or 'canceled' tasks can be removed." 
            }

        # Remove task from users' associated_task lists
        for user in self.users.values():
            if task_id in user["associated_task"]:
                user["associated_task"].remove(task_id)

        # Remove the task from tasks
        del self.tasks[task_id]

        return {
            "success": True,
            "message": f"Task {task_id} removed from the system."
        }


class EducationalPlatformWorkflowManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_user_tasks(self, **kwargs):
        return self._call_inner_tool('list_user_tasks', kwargs)

    def get_user_role(self, **kwargs):
        return self._call_inner_tool('get_user_role', kwargs)

    def get_task_by_id(self, **kwargs):
        return self._call_inner_tool('get_task_by_id', kwargs)

    def get_task_status(self, **kwargs):
        return self._call_inner_tool('get_task_status', kwargs)

    def get_task_result(self, **kwargs):
        return self._call_inner_tool('get_task_result', kwargs)

    def list_tasks_by_status(self, **kwargs):
        return self._call_inner_tool('list_tasks_by_status', kwargs)

    def list_tasks_by_type(self, **kwargs):
        return self._call_inner_tool('list_tasks_by_type', kwargs)

    def get_quiz_by_id(self, **kwargs):
        return self._call_inner_tool('get_quiz_by_id', kwargs)

    def list_quizzes_by_creator(self, **kwargs):
        return self._call_inner_tool('list_quizzes_by_creator', kwargs)

    def list_quizzes_for_user(self, **kwargs):
        return self._call_inner_tool('list_quizzes_for_user', kwargs)

    def create_task(self, **kwargs):
        return self._call_inner_tool('create_task', kwargs)

    def update_task_status(self, **kwargs):
        return self._call_inner_tool('update_task_status', kwargs)

    def set_task_result(self, **kwargs):
        return self._call_inner_tool('set_task_result', kwargs)

    def create_quiz(self, **kwargs):
        return self._call_inner_tool('create_quiz', kwargs)

    def assign_quiz_to_students(self, **kwargs):
        return self._call_inner_tool('assign_quiz_to_students', kwargs)

    def link_task_to_quiz(self, **kwargs):
        return self._call_inner_tool('link_task_to_quiz', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def associate_task_with_user(self, **kwargs):
        return self._call_inner_tool('associate_task_with_user', kwargs)

    def remove_task(self, **kwargs):
        return self._call_inner_tool('remove_task', kwargs)
