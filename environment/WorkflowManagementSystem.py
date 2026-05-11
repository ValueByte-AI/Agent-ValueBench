# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, Any, TypedDict
from collections import defaultdict
import datetime
from collections import defaultdict, deque



class TaskInfo(TypedDict):
    task_id: str
    status: str
    evaluation_result: Optional[Any]
    creation_time: str
    update_time: str
    owner: str
    metadata: Dict[str, Any]

class TaskDependencyInfo(TypedDict):
    parent_task_id: str
    child_task_id: str
    dependency_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Workflow Management System stateful environment.

        Constraints:
        - Each task_id must be unique.
        - Evaluation results may only be present for tasks that have completed execution.
        - Status values follow a lifecycle (e.g., pending, running, completed, failed).
        - Task dependencies must not form cycles (no dependency loops allowed).
        """

        # Tasks: {task_id: TaskInfo}
        # - task_id, status, evaluation_result, creation_time, update_time, owner, metadata
        self.tasks: Dict[str, TaskInfo] = {}

        # Task Dependencies: List of TaskDependencyInfo
        # - parent_task_id, child_task_id, dependency_type
        self.task_dependencies: List[TaskDependencyInfo] = []

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Retrieve the full metadata for a specific task by task_id.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            dict: {
                "success": True,
                "data": TaskInfo,  # Metadata for the task
            }
            or
            {
                "success": False,
                "error": str  # "Task not found" if the task does not exist
            }

        Constraints:
            - Each task_id must be unique.
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}

        return {"success": True, "data": self.tasks[task_id]}

    def get_evaluation_result(self, task_id: str) -> dict:
        """
        Get the evaluation result for a task (if present).

        Args:
            task_id (str): The unique identifier for the task.

        Returns:
            dict: 
                On success (result available):
                    { "success": True, "data": <evaluation_result> }
                On failure (task not found or result not present):
                    { "success": False, "error": <reason> }

        Constraints:
            - Task must exist.
            - Evaluation results are available for terminal tasks that already carry one
              (for example, completed or failed tasks).
        """
        task = self.tasks.get(task_id)
        if task is None:
            return { "success": False, "error": "Task does not exist" }
        if task["status"] not in {"completed", "failed"} or task["evaluation_result"] is None:
            return { "success": False, "error": "No evaluation result available" }
        return { "success": True, "data": task["evaluation_result"] }

    def get_multiple_evaluation_results(self, task_ids: List[str]) -> dict:
        """
        Retrieve evaluation results for multiple tasks by their IDs.

        Args:
            task_ids (List[str]): List of task IDs.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict: { "task_id": ..., "evaluation_result": ... } or { "task_id": ..., "error": ... }
            }

        Notes/Constraints:
            - If a task_id does not exist, output { "task_id": <id>, "error": "Task not found" }.
            - If the evaluation result is not available (absent or task not terminal), output { "task_id": <id>, "error": "No evaluation result available" }.
            - Only return the evaluation_result if the corresponding field is present and the task status is terminal ("completed" or "failed").
        """
        results = []
        for tid in task_ids:
            task = self.tasks.get(tid)
            if not task:
                results.append({"task_id": tid, "error": "Task not found"})
                continue

            if task["status"] not in {"completed", "failed"} or task["evaluation_result"] is None:
                results.append({"task_id": tid, "error": "No evaluation result available"})
                continue

            results.append({
                "task_id": tid,
                "evaluation_result": task["evaluation_result"]
            })
        return {"success": True, "data": results}

    def list_all_tasks(self) -> dict:
        """
        Retrieve all tasks present in the workflow management system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo],  # List (possibly empty) of all TaskInfo objects
            }
        """
        all_tasks = list(self.tasks.values())
        return {
            "success": True,
            "data": all_tasks
        }

    def filter_tasks_by_status(self, status: str) -> dict:
        """
        List all tasks matching a particular status (e.g., pending, running, completed, failed).

        Args:
            status (str): The target status to filter on.

        Returns:
            dict: {
                "success": True,
                "data": list of TaskInfo (may be empty if no match)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., status not recognized)
            }

        Constraints:
            - Status must be one of the allowed lifecycle values.
        """
        allowed_statuses = {"pending", "running", "completed", "failed"}
        if status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status: '{status}'. Allowed values: {sorted(allowed_statuses)}" }
    
        filtered = [
            task_info for task_info in self.tasks.values()
            if task_info["status"] == status
        ]
        return { "success": True, "data": filtered }

    def filter_tasks_by_owner(self, owner: str) -> dict:
        """
        Get all tasks belonging to a specific owner.

        Args:
            owner (str): The owner/user whose tasks to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[TaskInfo]  # All tasks owned by the specified owner. Empty list if none found.
            }

        Constraints:
            - Returns all tasks where the TaskInfo.owner matches the given owner exactly.
            - Returns empty list if no tasks for given owner are present.
        """
        if not isinstance(owner, str) or owner == "":
            # We treat blank or non-string owner as legitimate; simply return empty list.
            return {"success": True, "data": []}
    
        result = [
            task for task in self.tasks.values()
            if task['owner'] == owner
        ]
        return {"success": True, "data": result}

    def get_task_dependencies(self, task_id: str) -> dict:
        """
        Retrieve direct dependencies (parents and/or children) for a given task.

        Args:
            task_id (str): The task ID to query dependencies for.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "data": {
                            "parents": List[TaskDependencyInfo],   # Where task_id is child (dependencies it has)
                            "children": List[TaskDependencyInfo]   # Where task_id is parent (dependencies it provides)
                        }
                    }
                Failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., task not found)
                    }

        Constraints:
            - task_id must exist in the system, else return error.
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task ID does not exist"}

        parents = [
            dep for dep in self.task_dependencies if dep["child_task_id"] == task_id
        ]
        children = [
            dep for dep in self.task_dependencies if dep["parent_task_id"] == task_id
        ]
        return {
            "success": True,
            "data": {
                "parents": parents,
                "children": children
            }
        }

    def get_all_downstream_tasks(self, task_id: str) -> dict:
        """
        Recursively retrieve all tasks (as TaskInfo) that are downstream
        (dependent on) the specified task.

        Args:
            task_id (str): The source/parent task ID.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TaskInfo]  # List of all unique downstream task infos
                    }
                On failure (invalid task ID):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - task_id must exist in self.tasks.
            - No cycles are permitted in dependencies (per environment guarantees).
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task ID does not exist"}

        # Build a map: parent -> list of children
        children_map = {}
        for dep in self.task_dependencies:
            parent = dep["parent_task_id"]
            child = dep["child_task_id"]
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(child)

        result_ids = set()
        stack = [task_id]
        visited = set([task_id])

        while stack:
            current = stack.pop()
            for child in children_map.get(current, []):
                if child not in visited:
                    result_ids.add(child)
                    visited.add(child)
                    stack.append(child)

        # Collect TaskInfo for all found task_ids
        downstream_tasks = [self.tasks[tid] for tid in result_ids if tid in self.tasks]

        return {"success": True, "data": downstream_tasks}

    def check_task_exists(self, task_id: str) -> dict:
        """
        Check whether a given task_id exists in the workflow system.

        Args:
            task_id (str): The ID of the task to check.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": bool  # True if task_id exists, False otherwise
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - task_id must be a non-empty string.
        """
        if not isinstance(task_id, str) or not task_id.strip():
            return { "success": False, "error": "Invalid task_id" }

        exists = task_id in self.tasks
        return { "success": True, "data": exists }

    def detect_dependency_cycles(self) -> dict:
        """
        Check if the current task dependency graph contains any cycles.
    
        Returns:
            dict: {
                "success": True,
                "data": bool  # True if a cycle is detected, False otherwise
            }
        Notes:
            - This checks the acyclicity of the current dependencies (integrity check).
            - Will return False for empty or acyclic graphs.
            - No constraints are violated by this operation itself; it's for checking.
        """
        # Build adjacency list
        adjacency = defaultdict(list)
        for dep in self.task_dependencies:
            adjacency[dep['parent_task_id']].append(dep['child_task_id'])

        # DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(v):
            visited.add(v)
            rec_stack.add(v)
            for neighbor in adjacency[v]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle detected
                    return True
            rec_stack.remove(v)
            return False

        # Check all tasks (even those with no outgoing dependencies)
        all_tasks = set(self.tasks.keys())
        all_tasks.update(dep['parent_task_id'] for dep in self.task_dependencies)
        all_tasks.update(dep['child_task_id'] for dep in self.task_dependencies)

        for task_id in all_tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    return {"success": True, "data": True}

        return {"success": True, "data": False}

    def create_task(
        self,
        task_id: str,
        owner: str,
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
        creation_time: Optional[str] = None,
        update_time: Optional[str] = None
    ) -> dict:
        """
        Add a new task with a unique task_id and initial metadata.

        Args:
            task_id (str): Unique identifier for the task.
            owner (str): The owner of the task.
            status (str, optional): Initial status value (default 'pending'). Must be a valid status.
            metadata (Dict[str, Any], optional): Arbitrary metadata for the task.
            creation_time (str, optional): Creation time in ISO format. If omitted, uses now.
            update_time (str, optional): Update time in ISO format. If omitted, uses now.

        Returns:
            dict: Success or error message.

        Constraints:
            - task_id must be unique.
            - status must be in allowed lifecycle values.
            - evaluation_result must be None at creation.
        """

        allowed_statuses = {"pending", "running", "completed", "failed"}

        # Validation
        if not task_id or not isinstance(task_id, str):
            return {"success": False, "error": "Invalid or missing task_id"}
        if task_id in self.tasks:
            return {"success": False, "error": f"Task ID '{task_id}' already exists"}
        if status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{status}'. Allowed: {sorted(allowed_statuses)}"}
        if not owner or not isinstance(owner, str):
            return {"success": False, "error": "Invalid or missing owner"}
        if metadata is None:
            metadata = {}

        # Set creation and update times if not given
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        if creation_time is None:
            creation_time = now
        if update_time is None:
            update_time = now

        task_info: TaskInfo = {
            "task_id": task_id,
            "status": status,
            "evaluation_result": None,
            "creation_time": creation_time,
            "update_time": update_time,
            "owner": owner,
            "metadata": metadata,
        }

        self.tasks[task_id] = task_info

        return {"success": True, "message": f"Task '{task_id}' created"}

    def update_task_status(self, task_id: str, new_status: str) -> dict:
        """
        Change the status of a specified task, following valid lifecycle transitions.

        Args:
            task_id (str): Unique ID of the task to update.
            new_status (str): The new status for the task (e.g., 'pending', 'running', 'completed', 'failed').

        Returns:
            dict: {
                "success": True,
                "message": "Task <task_id> status updated to <new_status>."
            } on success,
            or
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - Task must exist.
            - new_status must be a valid status.
            - Status transition must follow allowed lifecycle.
            - update_time must be set to current (ISO8601) time on change.
        """

        VALID_STATUSES = ["pending", "running", "completed", "failed"]
        ALLOWED_TRANSITIONS = {
            "pending": ["running", "completed", "failed"],
            "running": ["completed", "failed"],
            "completed": [],
            "failed": ["pending", "running"],
        }

        if not isinstance(task_id, str) or not task_id:
            return {"success": False, "error": "Invalid task_id."}
        if not isinstance(new_status, str) or new_status not in VALID_STATUSES:
            return {"success": False, "error": "Invalid new_status."}

        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found."}

        old_status = task["status"]
        if new_status == old_status:
            return {"success": True, "message": f"Task '{task_id}' status is already '{new_status}'."}

        if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
            return {"success": False, "error": f"Illegal status transition from '{old_status}' to '{new_status}'."}

        # Perform the status update
        task["status"] = new_status
        task["update_time"] = datetime.datetime.utcnow().isoformat() + "Z"

        return {
            "success": True,
            "message": f"Task '{task_id}' status updated from '{old_status}' to '{new_status}'."
        }

    def set_evaluation_result(self, task_id: str, evaluation_result: Any) -> dict:
        """
        Attach/set the evaluation result for a completed task, enforcing that evaluation
        results may only be present for tasks that have completed execution.

        Args:
            task_id (str): The unique ID of the task.
            evaluation_result (Any): The evaluation result to be stored.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Evaluation result set for task <task_id>"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Task must exist.
            - Task status must be terminal ('completed' or 'failed') to set an evaluation result.
            - On success, the evaluation_result is saved for the task.
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task does not exist"}
        if task["status"] not in {"completed", "failed"}:
            return {"success": False, "error": "Evaluation result can only be set for completed or failed tasks"}
        task["evaluation_result"] = evaluation_result
        task["update_time"] = datetime.datetime.utcnow().isoformat() + "Z"
        return {"success": True, "message": f"Evaluation result set for task {task_id}"}

    def delete_task(self, task_id: str) -> dict:
        """
        Remove an existing task from the system and clean up all related dependencies.

        Args:
            task_id (str): Unique identifier of the task to delete.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Task <task_id> and related dependencies deleted." }
                - On failure: { "success": False, "error": "Task <task_id> does not exist." }

        Constraints:
            - Task must exist.
            - All dependencies involving the task (as parent or child) are removed.
        """
        if task_id not in self.tasks:
            return { "success": False, "error": f"Task {task_id} does not exist." }

        # Remove the task from tasks dictionary
        del self.tasks[task_id]

        # Remove all dependencies involving this task
        original_count = len(self.task_dependencies)
        self.task_dependencies = [
            dep for dep in self.task_dependencies
            if dep['parent_task_id'] != task_id and dep['child_task_id'] != task_id
        ]
        removed_count = original_count - len(self.task_dependencies)

        return {
            "success": True,
            "message": f"Task {task_id} and {removed_count} related dependencies deleted."
        }

    def add_task_dependency(self, parent_task_id: str, child_task_id: str, dependency_type: str) -> dict:
        """
        Add a dependency from parent_task_id to child_task_id, enforcing that no cycles are created.

        Args:
            parent_task_id (str): The ID of the parent (upstream) task.
            child_task_id (str): The ID of the child (downstream) task.
            dependency_type (str): The type of the dependency relationship.

        Returns:
            dict:
                - On success: {"success": True, "message": "..."}
                - On failure: {"success": False, "error": "..."}
        Constraints:
            - Both task IDs must exist in the system.
            - Cannot add a dependency forming a cycle.
            - No duplicate dependencies.
            - Cannot add self-dependency.
        """
        # Check existence of tasks
        if parent_task_id not in self.tasks:
            return {"success": False, "error": f"Parent task '{parent_task_id}' does not exist"}
        if child_task_id not in self.tasks:
            return {"success": False, "error": f"Child task '{child_task_id}' does not exist"}

        # Cannot add self-dependency
        if parent_task_id == child_task_id:
            return {"success": False, "error": "Cannot add self-dependency"}

        # Check for duplicate dependency
        for dep in self.task_dependencies:
            if (dep["parent_task_id"] == parent_task_id and
                dep["child_task_id"] == child_task_id and
                dep["dependency_type"] == dependency_type):
                return {"success": False, "error": "Dependency already exists"}

        # Build adjacency list, including proposed new dependency
        adj = defaultdict(list)
        for dep in self.task_dependencies:
            adj[dep["parent_task_id"]].append(dep["child_task_id"])
        # Add the proposed dependency
        adj[parent_task_id].append(child_task_id)

        # Cycle detection (DFS)
        def has_cycle_dfs():
            visited = set()
            rec_stack = set()
            def dfs(node):
                visited.add(node)
                rec_stack.add(node)
                for nbr in adj[node]:
                    if nbr not in visited:
                        if dfs(nbr):
                            return True
                    elif nbr in rec_stack:
                        return True
                rec_stack.remove(node)
                return False

            for task in self.tasks:
                if task not in visited:
                    if dfs(task):
                        return True
            return False

        if has_cycle_dfs():
            return {"success": False, "error": "Dependency not added: would introduce a cycle"}

        # All checks passed, add the dependency
        dep_info = {
            "parent_task_id": parent_task_id,
            "child_task_id": child_task_id,
            "dependency_type": dependency_type,
        }
        self.task_dependencies.append(dep_info)

        return {
            "success": True,
            "message": f"Dependency added: {parent_task_id} -> {child_task_id} (type: {dependency_type})"
        }

    def remove_task_dependency(
        self,
        parent_task_id: str,
        child_task_id: str,
        dependency_type: str
    ) -> dict:
        """
        Remove a dependency of the specified type between the given parent and child tasks.

        Args:
            parent_task_id (str): The task ID of the parent in the dependency.
            child_task_id (str): The task ID of the child in the dependency.
            dependency_type (str): The type of dependency to remove.

        Returns:
            dict:
                Success: { "success": True, "message": "Dependency removed successfully." }
                Failure:
                    - { "success": False, "error": "Specified dependency does not exist." }
                    - { "success": False, "error": "Parent task does not exist." }
                    - { "success": False, "error": "Child task does not exist." }

        Constraints:
            - Both parent and child tasks must exist.
            - Only removes the specified dependency (matching all three attributes).
        """
        # Check that both tasks exist
        if parent_task_id not in self.tasks:
            return { "success": False, "error": "Parent task does not exist." }
        if child_task_id not in self.tasks:
            return { "success": False, "error": "Child task does not exist." }

        dependency_found = False
        for i, dep in enumerate(self.task_dependencies):
            if (dep["parent_task_id"] == parent_task_id and
                dep["child_task_id"] == child_task_id and
                dep["dependency_type"] == dependency_type):
                # Found, remove and break
                dependency_found = True
                del self.task_dependencies[i]
                break

        if not dependency_found:
            return { "success": False, "error": "Specified dependency does not exist." }

        return { "success": True, "message": "Dependency removed successfully." }

    def update_task_metadata(
        self,
        task_id: str,
        metadata_update: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Patch or update the metadata dictionary for an existing task.

        Args:
            task_id (str): ID of the task to patch/update.
            metadata_update (Dict[str, Any], optional): Canonical dictionary of key-value pairs to update/insert.
            metadata (Dict[str, Any], optional): Accepted alias for metadata_update.
            new_metadata (Dict[str, Any], optional): Accepted alias for metadata_update.

        Returns:
            dict: {
                "success": True,
                "message": "Task metadata updated for task_id <task_id>"
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - task_id must exist in self.tasks
            - One of metadata_update / metadata / new_metadata must be a dictionary (may be empty)
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}

        provided_updates = [
            candidate
            for candidate in (metadata, new_metadata, metadata_update)
            if candidate is not None
        ]
        if not provided_updates:
            return {"success": False, "error": "Provided metadata update is not a dict"}
        if any(not isinstance(candidate, dict) for candidate in provided_updates):
            return {"success": False, "error": "Provided metadata update is not a dict"}

        merged_update: Dict[str, Any] = {}
        for candidate in provided_updates:
            merged_update.update(candidate)

        # Update the current metadata, patch semantics
        current_metadata = self.tasks[task_id]["metadata"]
        if not isinstance(current_metadata, dict):
            current_metadata = {}

        current_metadata.update(merged_update)
        self.tasks[task_id]["metadata"] = current_metadata

        return {"success": True, "message": f"Task metadata updated for task_id {task_id}"}

    def bulk_update_task_status(self, task_ids: list, new_status: str) -> dict:
        """
        Update the status of a batch of tasks given their IDs.

        Args:
            task_ids (list of str): List of task IDs to update.
            new_status (str): The target status to set for these tasks.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of what was updated (how many, details)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
          - Each task_id must exist in the system.
          - Status values must be one of ("pending", "running", "completed", "failed").
          - TaskInfo.update_time should be updated to current UTC ISO timestamp for updated tasks.
        """

        ALLOWED_STATUSES = {"pending", "running", "completed", "failed"}
        if not isinstance(task_ids, list) or not all(isinstance(tid, str) for tid in task_ids):
            return {"success": False, "error": "task_ids must be a list of strings"}

        if new_status not in ALLOWED_STATUSES:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed statuses: {list(ALLOWED_STATUSES)}"}

        updated = []
        not_found = []

        now = datetime.datetime.utcnow().isoformat() + "Z"

        for tid in task_ids:
            task = self.tasks.get(tid)
            if task is None:
                not_found.append(tid)
            else:
                task["status"] = new_status
                task["update_time"] = now
                updated.append(tid)

        if not updated:
            return {"success": False, "error": "None of the provided task_ids were found."}

        msg = f"Updated status of {len(updated)} task(s) to '{new_status}'."
        if not_found:
            msg += f" The following task_ids were not found and not updated: {not_found}"

        return {"success": True, "message": msg}


class WorkflowManagementSystem(BaseEnv):
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

    def get_evaluation_result(self, **kwargs):
        return self._call_inner_tool('get_evaluation_result', kwargs)

    def get_multiple_evaluation_results(self, **kwargs):
        return self._call_inner_tool('get_multiple_evaluation_results', kwargs)

    def list_all_tasks(self, **kwargs):
        return self._call_inner_tool('list_all_tasks', kwargs)

    def filter_tasks_by_status(self, **kwargs):
        return self._call_inner_tool('filter_tasks_by_status', kwargs)

    def filter_tasks_by_owner(self, **kwargs):
        return self._call_inner_tool('filter_tasks_by_owner', kwargs)

    def get_task_dependencies(self, **kwargs):
        return self._call_inner_tool('get_task_dependencies', kwargs)

    def get_all_downstream_tasks(self, **kwargs):
        return self._call_inner_tool('get_all_downstream_tasks', kwargs)

    def check_task_exists(self, **kwargs):
        return self._call_inner_tool('check_task_exists', kwargs)

    def detect_dependency_cycles(self, **kwargs):
        return self._call_inner_tool('detect_dependency_cycles', kwargs)

    def create_task(self, **kwargs):
        return self._call_inner_tool('create_task', kwargs)

    def update_task_status(self, **kwargs):
        return self._call_inner_tool('update_task_status', kwargs)

    def set_evaluation_result(self, **kwargs):
        return self._call_inner_tool('set_evaluation_result', kwargs)

    def delete_task(self, **kwargs):
        return self._call_inner_tool('delete_task', kwargs)

    def add_task_dependency(self, **kwargs):
        return self._call_inner_tool('add_task_dependency', kwargs)

    def remove_task_dependency(self, **kwargs):
        return self._call_inner_tool('remove_task_dependency', kwargs)

    def update_task_metadata(self, **kwargs):
        return self._call_inner_tool('update_task_metadata', kwargs)

    def bulk_update_task_status(self, **kwargs):
        return self._call_inner_tool('bulk_update_task_status', kwargs)
