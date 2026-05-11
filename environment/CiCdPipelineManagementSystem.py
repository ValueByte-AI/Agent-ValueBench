# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from typing import List, Dict, Any
import time



# TypedDict definitions for each entity

class RepositoryInfo(TypedDict):
    repository_id: str
    name: str
    url: str
    status: str

class BuildStepInfo(TypedDict):
    step_id: str
    build_definition_id: str
    command: str
    order: int

class BuildDefinitionInfo(TypedDict):
    build_definition_id: str
    name: str
    repository_id: str
    branch: str
    build_steps: List[str]  # ordered list of step_ids
    status: str

class BuildHistoryInfo(TypedDict):
    build_id: str
    build_definition_id: str
    trigger_time: str
    status: str
    log: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        CI/CD pipeline management system environment.
        """

        # Repositories: {repository_id: RepositoryInfo}
        self.repositories: Dict[str, RepositoryInfo] = {}

        # Build definitions: {build_definition_id: BuildDefinitionInfo}
        self.build_definitions: Dict[str, BuildDefinitionInfo] = {}

        # Build steps: {step_id: BuildStepInfo}
        self.build_steps: Dict[str, BuildStepInfo] = {}

        # Build history: {build_id: BuildHistoryInfo}
        self.build_history: Dict[str, BuildHistoryInfo] = {}

        # --- Constraints Rules ---
        # - Each BuildDefinition must reference a valid Repository and branch.
        # - BuildSteps for a BuildDefinition must be ordered and non-duplicated in sequence.
        # - Only one name per BuildDefinition (uniqueness required by environment policy).
        # - Cannot assign a build definition to a repository or branch which does not exist.
        # - Updating a BuildDefinition may trigger validation or require permissions.

    def _get_ordered_build_step_commands(self, build_definition_id: str) -> list[str]:
        build_def = self.build_definitions.get(build_definition_id)
        if not build_def:
            return []
        commands = []
        for step_id in build_def.get("build_steps", []):
            step = self.build_steps.get(step_id)
            if step:
                commands.append(step.get("command", ""))
        return commands

    def get_build_definition_by_id(self, build_definition_id: str) -> dict:
        """
        Retrieve details of a build definition given its build_definition_id.

        Args:
            build_definition_id (str): The unique identifier for the build definition.

        Returns:
            dict:
                - {"success": True, "data": BuildDefinitionInfo} if found
                - {"success": False, "error": "Build definition not found"} if not found

        Constraints:
            - build_definition_id must exist in self.build_definitions.
        """
        build_def = self.build_definitions.get(build_definition_id)
        if build_def is None:
            return {
                "success": False,
                "error": "Build definition not found"
            }
        return {
            "success": True,
            "data": build_def
        }

    def find_build_definition_by_name(self, name: str) -> dict:
        """
        Find a build definition by its unique name.

        Args:
            name (str): The name of the build definition to search for.

        Returns:
            dict: {
                "success": True,
                "data": BuildDefinitionInfo,  # The build definition info, if found
            }
            or
            {
                "success": False,
                "error": str  # If not found
            }

        Constraints:
            - Only one build definition can have a given name (enforced by environment policy).
        """
        for build_def in self.build_definitions.values():
            if build_def["name"] == name:
                return { "success": True, "data": build_def }
        return { "success": False, "error": "Build definition with the given name does not exist" }

    def list_all_build_definitions(self) -> dict:
        """
        Retrieve all build definitions present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[BuildDefinitionInfo],  # List of all build definitions (may be empty if none are defined)
            }
        """
        all_defs = list(self.build_definitions.values())
        return {"success": True, "data": all_defs}

    def list_all_repositories(self) -> dict:
        """
        Retrieve all repositories in the CI/CD management system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RepositoryInfo]  # List of all repositories (may be empty)
            }

        Constraints:
            - None. This is a read-only operation that returns all known repositories.
        """
        result = list(self.repositories.values())
        return { "success": True, "data": result }

    def get_repository_by_name(self, name: str) -> dict:
        """
        Retrieve repository information using its name.

        Args:
            name (str): The name of the repository to look up.

        Returns:
            dict: {
                "success": True,
                "data": RepositoryInfo
            }
            or
            {
                "success": False,
                "error": str  # If the repository is not found
            }

        Constraints:
            - Repository names are unique within the environment.
        """
        for repo in self.repositories.values():
            if repo["name"] == name:
                return {"success": True, "data": repo}
        return {"success": False, "error": "Repository not found"}

    def get_repository_by_id(self, repository_id: str) -> dict:
        """
        Retrieve repository information by its repository_id.

        Args:
            repository_id (str): The unique identifier for the repository.

        Returns:
            dict: {
                "success": True,
                "data": RepositoryInfo,  # Repository information if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if the repository is not found
            }

        Constraints:
            - The repository_id must exist in the repositories collection.
        """
        repo = self.repositories.get(repository_id)
        if repo is not None:
            return {"success": True, "data": repo}
        else:
            return {"success": False, "error": "Repository not found"}

    def list_branches_for_repository(self, repository_id: str) -> dict:
        """
        List all available branch names for a given repository, based on branches
        referenced by existing build definitions.

        Args:
            repository_id (str): The unique identifier of the repository.

        Returns:
            dict:
                - success (bool): True if repository exists, False otherwise.
                - data (List[str]): List of unique branch names for this repository,
                                    possibly empty if no branches found.
                - error (str): Error message, populated only if success is False.

        Constraints:
            - The repository must exist.
            - Branches are inferred from build definitions referencing the repository.
        """
        if repository_id not in self.repositories:
            return {"success": False, "error": "Repository does not exist"}

        branches = {
            bd["branch"]
            for bd in self.build_definitions.values()
            if bd["repository_id"] == repository_id
        }
        return {"success": True, "data": sorted(branches)}

    def get_build_steps_for_definition(self, build_definition_id: str) -> dict:
        """
        Retrieve the ordered list of build steps (including command details) for a specified build definition.

        Args:
            build_definition_id (str): Unique identifier of the build definition.

        Returns:
            dict:
                - success: True/False
                - data: On success, List[BuildStepInfo] ordered as in BuildDefinition['build_steps']
                - error: On failure, error message

        Constraints:
            - BuildDefinition must exist.
            - Only steps referenced in build_steps will be returned, in their specified order.
        """
        build_def = self.build_definitions.get(build_definition_id)
        if not build_def:
            return { "success": False, "error": "BuildDefinition does not exist" }

        step_ids = build_def.get('build_steps', [])
        result_steps = []
        for step_id in step_ids:
            step_info = self.build_steps.get(step_id)
            if step_info:
                result_steps.append(step_info)
            # If a step_id does not exist in build_steps, skip it silently.
            # Alternatively, could report error if strict consistency required.

        return {"success": True, "data": result_steps}

    def get_build_step_by_id(self, step_id: str) -> dict:
        """
        Retrieve the details of a build step given its step_id.

        Args:
            step_id (str): The unique identifier of the build step.

        Returns:
            dict: {
                "success": True,
                "data": BuildStepInfo    # The build step's information
            }
            or
            {
                "success": False,
                "error": str             # If the build step does not exist
            }

        Constraints:
            - The build step (step_id) must exist in the system.
        """
        build_step = self.build_steps.get(step_id)
        if build_step is None:
            return { "success": False, "error": "Build step does not exist" }

        return { "success": True, "data": build_step }

    def check_build_definition_name_uniqueness(self, name: str) -> dict:
        """
        Verify whether a given build definition name is unique in the system.

        Args:
            name (str): The name to check for uniqueness among build definitions.

        Returns:
            dict: {
                "success": True,
                "data": { "is_unique": bool }
            }
            Returns 'is_unique': True if no existing BuildDefinition uses that name,
            otherwise False.

        Constraints:
            - Names are considered case-sensitive (unless documented otherwise).
            - All current build definition names must be unique.
        """
        # BuildDefinition name uniqueness check (case-sensitive)
        for defn in self.build_definitions.values():
            if defn["name"] == name:
                return {"success": True, "data": {"is_unique": False}}
        return {"success": True, "data": {"is_unique": True}}

    def get_build_history_for_definition(self, build_definition_id: str) -> dict:
        """
        Retrieve all build execution history records for a given build definition.

        Args:
            build_definition_id (str): The ID of the build definition to query.

        Returns:
            dict:
                - success: True/False
                - data: List[BuildHistoryInfo] if success (may be empty)
                - error: str if not success

        Constraints:
            - build_definition_id must exist in build_definitions.
        """
        if build_definition_id not in self.build_definitions:
            return {"success": False, "error": "BuildDefinition does not exist"}
    
        history = [
            build_info 
            for build_info in self.build_history.values()
            if build_info["build_definition_id"] == build_definition_id
        ]
        return {"success": True, "data": history}

    def update_build_definition_metadata(
        self,
        build_definition_id: str,
        name: str = None,
        repository_id: str = None,
        branch: str = None,
        status: str = None
    ) -> dict:
        """
        Update the name, repository_id, branch, or status of a build definition.

        Args:
            build_definition_id (str): ID of the build definition to update.
            name (str, optional): New name for the build definition (must be unique).
            repository_id (str, optional): New repository_id (must exist).
            branch (str, optional): New branch name (must exist in the repository).
            status (str, optional): New status.

        Returns:
            dict: { "success": True, "message": str } or { "success": False, "error": str }

        Constraints:
            - BuildDefinition must exist.
            - Name must be unique among all BuildDefinitions.
            - repository_id must exist in repositories if provided.
            - (If supported) branch must exist in the repository if provided.
            - Only supplied fields are updated.
        """
        bd = self.build_definitions.get(build_definition_id)
        if not bd:
            return { "success": False, "error": "Build definition not found" }

        # Name uniqueness
        if name is not None:
            for other_bd_id, other_bd in self.build_definitions.items():
                if other_bd_id != build_definition_id and other_bd['name'] == name:
                    return { "success": False, "error": f"Build definition name '{name}' already exists" }
            bd['name'] = name

        # Repository and branch validation
        if repository_id is not None:
            repo = self.repositories.get(repository_id)
            if not repo:
                return { "success": False, "error": f"Repository '{repository_id}' not found" }
            bd['repository_id'] = repository_id

            # Optional: validate branch—if list of branches is tracked.
            # Example: if self.list_branches_for_repository exists, use it. Otherwise, skip.
            if branch is not None:
                if hasattr(self, "list_branches_for_repository"):
                    r = self.list_branches_for_repository(repository_id)
                    if not r.get("success", False) or branch not in r.get("data", []):
                        return { "success": False, "error": f"Branch '{branch}' not found in repository '{repository_id}'" }
                bd['branch'] = branch
            elif branch is None and 'branch' not in bd:
                bd['branch'] = ""  # If field is required for completeness

        elif branch is not None:
            # Update branch only; must check it on current repo if possible
            current_repo_id = bd['repository_id']
            if hasattr(self, "list_branches_for_repository"):
                r = self.list_branches_for_repository(current_repo_id)
                if not r.get("success", False) or branch not in r.get("data", []):
                    return { "success": False, "error": f"Branch '{branch}' not found in repository '{current_repo_id}'" }
            bd['branch'] = branch

        # Status update
        if status is not None:
            bd['status'] = status

        # Save back (since dict is mutable, this is not strictly necessary)
        self.build_definitions[build_definition_id] = bd

        return { "success": True, "message": "Build definition metadata updated successfully" }

    def set_build_steps_for_definition(self, build_definition_id: str, steps: list) -> dict:
        """
        Assigns a new ordered list of build steps (by step_ids or command dicts) to the specified build definition,
        ensuring no duplicates and correct ordering.

        Args:
            build_definition_id (str): The ID of the build definition to update.
            steps (List[Union[str, dict]]): The new ordered build steps, each either:
                - a step_id (str) referencing an existing BuildStep for this definition, or
                - a dict: { "command": <command_str> }, in which case a new BuildStep is created and added.

        Returns:
            dict: On success: { "success": True, "message": "Successfully set build steps for build definition <id>" }
                  On failure: { "success": False, "error": <reason> }

        Constraints:
            - BuildDefinition must exist.
            - All step_ids must reference BuildSteps for this build_definition_id only.
            - Commands will create new BuildSteps.
            - The resulting step list must have no duplicates (by step_id).
            - BuildSteps must have correct sequential order fields.
        """
        bd = self.build_definitions.get(build_definition_id)
        if not bd:
            return { "success": False, "error": "BuildDefinition not found" }

        new_step_ids = []
        seen_step_ids = set()
        step_objs = []

        for idx, step in enumerate(steps):
            if isinstance(step, str):
                # Treat as a step_id
                step_obj = self.build_steps.get(step)
                if not step_obj:
                    return { "success": False, "error": f"Step ID {step} does not exist" }
                if step_obj["build_definition_id"] != build_definition_id:
                    return { "success": False, "error": f"Step ID {step} does not belong to the target BuildDefinition" }
                step_id = step
            elif isinstance(step, dict) and "command" in step:
                # Create new BuildStep
                new_step_id = str(uuid.uuid4())
                # Set order in the position in the list
                new_step_obj = {
                    "step_id": new_step_id,
                    "build_definition_id": build_definition_id,
                    "command": step["command"],
                    "order": idx + 1
                }
                self.build_steps[new_step_id] = new_step_obj
                step_obj = new_step_obj
                step_id = new_step_id
            else:
                return { "success": False, "error": f"Invalid step entry at position {idx}. Must be step_id or {{'command': ...}}" }

            if step_id in seen_step_ids:
                return { "success": False, "error": f"Duplicate build step ID {step_id} in requested build step list." }
            seen_step_ids.add(step_id)
            new_step_ids.append(step_id)
            step_objs.append(step_obj)

        # All checks pass, assign new ordered step IDs to the build_definition
        # Also, update 'order' in BuildStep objects to reflect their position
        for position, step_id in enumerate(new_step_ids, start=1):
            self.build_steps[step_id]["order"] = position

        bd["build_steps"] = new_step_ids

        return { "success": True, "message": f"Successfully set build steps for build definition {build_definition_id}" }

    def add_build_step_to_definition(
        self,
        build_definition_id: str,
        command: str,
        position: int = None
    ) -> dict:
        """
        Add and position a new build step to a build definition.

        Args:
            build_definition_id (str): The ID of the build definition to modify.
            command (str): The shell command for the build step.
            position (int, optional): 0-based desired position to insert. If out of range or not set, appends to end.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Build step added", "step_id": <new_step_id> }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The build definition must exist.
            - The build step will be inserted at the specified position; all subsequent step orders will be updated.
            - Build steps must remain uniquely ordered.
            - The command must not be empty.
        """
        # Validate build_definition_id
        build_def = self.build_definitions.get(build_definition_id)
        if build_def is None:
            return {"success": False, "error": "Build definition not found"}

        # Validate command
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "Command must be a non-empty string"}

        # Prepare new step_id (ensure unique)
        # Use simple monotonic id: step-<number>
        existing_ids = set(self.build_steps.keys())
        new_id_base = 1
        while True:
            step_id_candidate = f"step-{new_id_base}"
            if step_id_candidate not in existing_ids:
                break
            new_id_base += 1
        new_step_id = step_id_candidate

        # Setup insert position
        steps_list = build_def["build_steps"]
        if position is None or not isinstance(position, int) or position < 0 or position > len(steps_list):
            position = len(steps_list)  # append to end

        # Insert the new step_id into build_steps at the right position
        steps_list = steps_list[:position] + [new_step_id] + steps_list[position:]

        # Update orders for all build steps belonging to this definition
        for idx, sid in enumerate(steps_list, start=1):
            # If sid exists, just update the order
            if sid in self.build_steps:
                self.build_steps[sid]["order"] = idx
            # For our new step, create BuildStepInfo
            if sid == new_step_id:
                self.build_steps[sid] = {
                    "step_id": sid,
                    "build_definition_id": build_definition_id,
                    "command": command,
                    "order": idx
                }

        # Persist the new sequence in the definition
        self.build_definitions[build_definition_id]["build_steps"] = steps_list

        return {
            "success": True,
            "message": "Build step added",
            "step_id": new_step_id
        }

    def remove_build_step_from_definition(self, build_definition_id: str, step_id: str) -> dict:
        """
        Remove a build step from the specified build definition's workflow.

        Args:
            build_definition_id (str): The ID of the build definition.
            step_id (str): The ID of the build step to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Build step removed from build definition workflow." }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Both build_definition_id and step_id must exist.
            - The step must belong to the specified build definition.
            - The step must exist in the build_steps list of the build definition.
            - After removal, the list remains ordered.
        """
        # Check build definition
        bdef = self.build_definitions.get(build_definition_id)
        if bdef is None:
            return { "success": False, "error": "Build definition does not exist." }

        # Check build step
        step = self.build_steps.get(step_id)
        if step is None:
            return { "success": False, "error": "Build step does not exist." }

        # Check step belongs to build definition
        if step["build_definition_id"] != build_definition_id:
            return { "success": False, "error": "Build step does not belong to the specified build definition." }

        # Check step is in build definition's workflow
        if step_id not in bdef["build_steps"]:
            return { "success": False, "error": "Build step is not part of the build definition's workflow." }

        # Remove the step from the workflow list and reindex the remaining orders.
        bdef["build_steps"] = [sid for sid in bdef["build_steps"] if sid != step_id]
        for idx, remaining_step_id in enumerate(bdef["build_steps"], start=1):
            if remaining_step_id in self.build_steps:
                self.build_steps[remaining_step_id]["order"] = idx
        self.build_definitions[build_definition_id] = bdef  # Persist change

        # (Optional: do not delete step itself, only remove from workflow)

        return { "success": True, "message": "Build step removed from build definition workflow." }

    def reorder_build_steps_for_definition(self, build_definition_id: str, new_order: list) -> dict:
        """
        Change the sequence/order of the steps within a build definition.
    
        Args:
            build_definition_id (str): The unique identifier for the build definition to modify.
            new_order (List[str]): The new ordered list of step_ids (strings) representing the desired build step sequence.
        
        Returns:
            dict: {
                "success": True,
                "message": "Build steps reordered successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error.
            }
        
        Constraints:
            - build_definition_id must exist.
            - new_order must be a permutation of the build_definition's current build_steps (no missing or extra step_ids, no duplicates).
            - All step_ids in new_order must belong to the build definition.
            - The order field in each BuildStepInfo is updated to reflect the new sequence (starting from 1).
        """
        # Check for build definition existence
        if build_definition_id not in self.build_definitions:
            return { "success": False, "error": "Build definition does not exist." }
    
        build_def = self.build_definitions[build_definition_id]
        current_steps = build_def["build_steps"]
    
        # Check that new_order is a non-duplicate permutation of current_steps
        if (set(new_order) != set(current_steps)) or (len(new_order) != len(current_steps)):
            return {
                "success": False,
                "error": "New order must be a non-duplicate permutation of the existing build steps."
            }
    
        # Ensure all step_ids actually belong to this definition
        for step_id in new_order:
            if step_id not in self.build_steps:
                return { "success": False, "error": f"Step ID '{step_id}' does not exist." }
            if self.build_steps[step_id]["build_definition_id"] != build_definition_id:
                return { "success": False, "error": f"Step ID '{step_id}' does not belong to this build definition." }
    
        # Update build definition
        self.build_definitions[build_definition_id]["build_steps"] = list(new_order)
    
        # Update order field of each BuildStepInfo (order starts at 1)
        for idx, step_id in enumerate(new_order):
            self.build_steps[step_id]["order"] = idx + 1

        return { "success": True, "message": "Build steps reordered successfully." }

    def validate_build_definition_update(
        self,
        build_definition_id: str,
        proposed_metadata: dict,
        permission_token: str = ""
    ) -> dict:
        """
        Perform validation checks before allowing a build definition update.

        Args:
            build_definition_id (str): The ID of the build definition to validate an update for.
            proposed_metadata (dict): Dict with proposed updates (may contain 'name', 'repository_id', 'branch', 'build_steps').
            permission_token (str, optional): Token for checking update permissions.

        Returns:
            dict:
                { "success": True, "message": "Validation passed" }
                or
                { "success": False, "error": "<reason>" }

        Validation Constraints:
            - Repository (repository_id) must exist.
            - Branch must exist in the repository.
            - BuildDefinition name must remain unique.
            - BuildSteps must be ordered, unique, belong to the build_definition_id, and not have duplicate order values.
            - Permission token check (if implemented).
        """
        # Permission check (dummy logic: only "admin" passes)
        if permission_token and permission_token != "admin":
            return {
                "success": False,
                "error": "Permission denied"
            }

        # Must have a target build definition to update
        if build_definition_id not in self.build_definitions:
            return {
                "success": False,
                "error": "BuildDefinition does not exist"
            }

        # Unpack relevant fields (fall back to previous values if not overridden)
        current = self.build_definitions[build_definition_id]

        name = proposed_metadata.get("name", current["name"])
        repository_id = proposed_metadata.get("repository_id", current["repository_id"])
        branch = proposed_metadata.get("branch", current["branch"])
        build_steps = proposed_metadata.get("build_steps", current["build_steps"])

        # Repository existence check
        repo = self.repositories.get(repository_id)
        if not repo:
            return {
                "success": False,
                "error": f"Repository '{repository_id}' does not exist"
            }

        # Branch existence check - simulate branches as a list in repo info if present
        # We try repo["branches"], default to allowing 'main' branch
        branches = repo.get("branches", ["main"])
        if branch not in branches:
            return {
                "success": False,
                "error": f"Branch '{branch}' does not exist in repository '{repository_id}'"
            }

        # Name uniqueness check (must be unique among all build_definitions with different id)
        for bd_id, bd in self.build_definitions.items():
            if bd_id != build_definition_id and bd["name"] == name:
                return {
                    "success": False,
                    "error": "BuildDefinition name already exists"
                }

        # Build step checks
        step_ids_seen = set()
        order_seen = set()
        expected_num = len(build_steps)
        for step_id in build_steps:
            # Existence
            step = self.build_steps.get(step_id)
            if not step:
                return {
                    "success": False,
                    "error": f"BuildStep '{step_id}' does not exist"
                }
            # Ownership
            if step["build_definition_id"] != build_definition_id:
                return {
                    "success": False,
                    "error": f"BuildStep '{step_id}' does not belong to the BuildDefinition"
                }
            # Duplicate step IDs
            if step_id in step_ids_seen:
                return {
                    "success": False,
                    "error": f"Duplicate BuildStep id '{step_id}' in build_steps"
                }
            step_ids_seen.add(step_id)
            # Duplicate or invalid order values
            order = step["order"]
            if order in order_seen:
                return {
                    "success": False,
                    "error": f"Duplicate BuildStep order '{order}'"
                }
            order_seen.add(order)

        # Check ordering: orders should be 1, 2, ..., N (or strictly increasing)
        if order_seen:
            min_order = min(order_seen)
            max_order = max(order_seen)
            if sorted(order_seen) != list(range(min_order, max_order + 1)):
                return {
                    "success": False,
                    "error": f"BuildStep order values must be contiguous (got {sorted(order_seen)})"
                }

        return {
            "success": True,
            "message": "Validation passed"
        }

    def create_build_step(
        self,
        step_id: str,
        command: str,
        order: int,
        build_definition_id: str = None
    ) -> dict:
        """
        Create a new build step and optionally link it to a build definition.

        Args:
            step_id (str): Unique identifier for the step (must not already exist).
            command (str): The command this build step will execute.
            order (int): The sequence order for the step (if linking to a definition).
            build_definition_id (str, optional): If provided, link step to this build definition (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Created build step <step_id>."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - step_id must be unique.
            - If build_definition_id is provided:
                - It must exist.
                - The order value must not duplicate any existing step in the build definition.
                - The step_id is added to build_steps of build definition in correct order position.
        """
        # Check step_id uniqueness
        if step_id in self.build_steps:
            return {"success": False, "error": "step_id already exists"}

        # Prepare build_step_info
        build_step_info: BuildStepInfo = {
            "step_id": step_id,
            "build_definition_id": build_definition_id if build_definition_id else "",
            "command": command,
            "order": order,
        }

        # If linking to a build definition
        if build_definition_id:
            if build_definition_id not in self.build_definitions:
                return {"success": False, "error": "build_definition_id does not exist"}

            # Check for order duplication
            for existing_sid in self.build_definitions[build_definition_id]["build_steps"]:
                if self.build_steps[existing_sid]["order"] == order:
                    return {
                        "success": False,
                        "error": f"A build step with order {order} already exists in build definition"
                    }
            # Add to build_steps database first
            self.build_steps[step_id] = build_step_info

            # Insert into build definition's build_steps list maintaining sequence
            # Find insertion point
            steps_with_orders = [
                (self.build_steps[sid]["order"], sid)
                for sid in self.build_definitions[build_definition_id]["build_steps"]
            ]
            steps_with_orders.append((order, step_id))
            steps_with_orders.sort()
            new_step_ids = [sid for (_order_val, sid) in steps_with_orders]
            self.build_definitions[build_definition_id]["build_steps"] = new_step_ids

        else:
            # Not linked: just create step with empty build_definition_id
            self.build_steps[step_id] = build_step_info

        return {"success": True, "message": f"Created build step {step_id}."}

    def delete_build_step(self, step_id: str) -> dict:
        """
        Remove a build step from the system, including removing it from any build definition referencing it.
    
        Args:
            step_id (str): The identifier of the build step to delete.
    
        Returns:
            dict: {
                "success": True,
                "message": "Build step <step_id> deleted from system and build definitions."
            }
            OR
            {
                "success": False,
                "error": "Build step does not exist."
            }
    
        Constraints:
            - The step must exist to be deleted.
            - Remove the step from all build definitions' build_steps lists that reference it.
            - This operation must maintain list order for remaining steps.
        """
        if step_id not in self.build_steps:
            return {"success": False, "error": "Build step does not exist."}

        # Remove step from all build definitions' build_steps lists, if present
        for definition in self.build_definitions.values():
            if step_id in definition["build_steps"]:
                definition["build_steps"] = [sid for sid in definition["build_steps"] if sid != step_id]
                for idx, remaining_step_id in enumerate(definition["build_steps"], start=1):
                    if remaining_step_id in self.build_steps:
                        self.build_steps[remaining_step_id]["order"] = idx

        # Remove from build_steps storage
        del self.build_steps[step_id]

        return {
            "success": True,
            "message": f"Build step {step_id} deleted from system and build definitions."
        }


    def create_build_definition(
        self,
        name: str,
        repository_id: str,
        branch: str,
        build_steps: List[Dict[str, Any]],
        status: str = "active"
    ) -> dict:
        """
        Add a new build definition to the system with specified metadata and steps.

        Args:
            name (str): Name for the build definition (must be unique).
            repository_id (str): The ID of the repository to associate.
            branch (str): The branch in the repository to target (must be non-empty).
            build_steps (List[Dict]): List of steps, each dict with keys 'command' (str), and 'order' (int).
            status (str): BuildDefinition status (optional; defaults to 'active').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Build definition created",
                        "build_definition_id": <str>
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - Name must be unique among all build definitions.
            - repository_id must exist.
            - branch must be non-empty.
            - build_steps must be a non-empty ordered list, with unique 'order' values.
            - Each step must contain at least 'command' (str) and 'order' (int).
            - Each BuildDefinition, BuildStep gets a unique ID (generated).
        """
        # Name uniqueness
        for bd in self.build_definitions.values():
            if bd["name"] == name:
                return {"success": False, "error": "Build definition name already exists"}

        # Repository existence
        if repository_id not in self.repositories:
            return {"success": False, "error": "Repository does not exist"}

        # Branch non-empty
        if not isinstance(branch, str) or not branch.strip():
            return {"success": False, "error": "Branch must be a non-empty string"}

        # build_steps validation
        if not isinstance(build_steps, list) or not build_steps:
            return {"success": False, "error": "Build steps must be a non-empty list"}

        observed_orders = set()
        command_required_keys = {"command", "order"}
        step_ids: List[str] = []

        for step in build_steps:
            if not isinstance(step, dict):
                return {"success": False, "error": "Each build step must be a dict"}
            if not command_required_keys.issubset(step.keys()):
                return {"success": False, "error": "Each build step must have 'command' and 'order'"}
            if not isinstance(step["command"], str) or not step["command"].strip():
                return {"success": False, "error": "Each step's 'command' must be a non-empty string"}
            if not isinstance(step["order"], int):
                return {"success": False, "error": "Step 'order' must be an integer"}
            if step["order"] in observed_orders:
                return {"success": False, "error": f"Duplicate step order: {step['order']}"}
            observed_orders.add(step["order"])

        # Generate build_definition_id
        build_definition_id = str(uuid.uuid4())

        # Create BuildSteps
        for step in sorted(build_steps, key=lambda x: x["order"]):
            step_id = str(uuid.uuid4())
            step_ids.append(step_id)
            self.build_steps[step_id] = {
                "step_id": step_id,
                "build_definition_id": build_definition_id,
                "command": step["command"],
                "order": step["order"],
            }

        # Store BuildDefinition
        self.build_definitions[build_definition_id] = {
            "build_definition_id": build_definition_id,
            "name": name,
            "repository_id": repository_id,
            "branch": branch,
            "build_steps": step_ids,
            "status": status,
        }

        return {
            "success": True,
            "message": "Build definition created",
            "build_definition_id": build_definition_id
        }

    def delete_build_definition(self, build_definition_id: str) -> dict:
        """
        Remove a build definition from the system, including its associated build steps.

        Args:
            build_definition_id (str): The ID of the build definition to delete.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Build definition <id> deleted." }
                - On error: { "success": False, "error": str }

        Constraints:
            - Build definition must exist.
            - All associated build steps must also be deleted.
            - Build history for the build definition is preserved (not deleted) for audit purposes.
        """
        if build_definition_id not in self.build_definitions:
            return { "success": False, "error": "Build definition does not exist." }
    
        # Delete associated build steps
        build_def_info = self.build_definitions[build_definition_id]
        for step_id in build_def_info.get("build_steps", []):
            if step_id in self.build_steps:
                del self.build_steps[step_id]
    
        # Delete the build definition
        del self.build_definitions[build_definition_id]

        return {
            "success": True,
            "message": f"Build definition {build_definition_id} deleted."
        }


    def trigger_build(self, build_definition_id: str) -> dict:
        """
        Manually queue a build for the specified build definition.
    
        Args:
            build_definition_id (str): ID of the build definition to trigger.
    
        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Build manually triggered.",
                        "build_id": str,  # the new build ID
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
    
        Constraints:
            - The build definition must exist.
            - The linked repository (and branch) must exist.
            - The linked repository and build definition must both be active.
            - The build definition must have at least one build step.
            - Known blocking steps (for example unresolved strict lint gates or
              the beta-audit tool) prevent the build from being queued until the
              pipeline is modified.
        """
        # 1. Check if build definition exists
        build_def = self.build_definitions.get(build_definition_id)
        if not build_def:
            return {"success": False, "error": "Build definition does not exist."}

        # 2. Check if repository exists
        repo_id = build_def.get("repository_id")
        repository = self.repositories.get(repo_id)
        if not repository:
            return {"success": False, "error": "Build definition references a nonexistent repository."}
        if repository.get("status") != "active":
            return {"success": False, "error": "Cannot trigger a build for a non-active repository."}
        if build_def.get("status") != "active":
            return {"success": False, "error": "Cannot trigger a build for an inactive build definition."}

        commands = self._get_ordered_build_step_commands(build_definition_id)
        if not commands:
            return {"success": False, "error": "Cannot trigger a build without any configured build steps."}

        if any(command.strip() == "./run-beta-audit-tool.sh" for command in commands):
            return {
                "success": False,
                "error": "Build would fail because the beta-audit-tool step is still present and timing out."
            }

        strict_lint_indexes = [
            idx for idx, command in enumerate(commands)
            if command.strip() == "npm run lint -- --max-warnings=0"
        ]
        if strict_lint_indexes:
            has_prior_autofix = any(
                ("lint --fix" in command) or ("prettier --write" in command)
                for idx, command in enumerate(commands)
                if idx < strict_lint_indexes[0]
            )
            if not has_prior_autofix:
                return {
                    "success": False,
                    "error": "Build would fail because the strict lint gate still runs before any formatting fix step."
                }

        # Optionally, check for branch validity, if branches are tracked; omitted if not implemented.

        # 3. Generate new unique build_id
        build_id = str(uuid.uuid4())
        # 4. Compose build history entry
        trigger_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        build_history = {
            "build_id": build_id,
            "build_definition_id": build_definition_id,
            "trigger_time": trigger_time,
            "status": "queued",  # standard initial state
            "log": "",  # No log yet
        }
        # 5. Record in build history
        self.build_history[build_id] = build_history

        return {
            "success": True,
            "message": "Build manually triggered.",
            "build_id": build_id,
        }

    def set_repository_status(self, repository_id: str, status: str) -> dict:
        """
        Update the status field of a repository.

        Args:
            repository_id (str): Unique ID of the repository to update.
            status (str): New status to assign (e.g., "active", "archived").

        Returns:
            dict: {
                "success": True,
                "message": "Repository status updated successfully"
            }
            or
            {
                "success": False,
                "error": "Repository does not exist"
            }

        Constraints:
            - Repository with the given ID must exist in self.repositories.
        """
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }

        self.repositories[repository_id]["status"] = status
        return { "success": True, "message": "Repository status updated successfully" }


class CiCdPipelineManagementSystem(BaseEnv):
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
            if key == "list_branches_for_repository":
                setattr(env, "_branch_inventory_state", copy.deepcopy(value))
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

    def get_build_definition_by_id(self, **kwargs):
        return self._call_inner_tool('get_build_definition_by_id', kwargs)

    def find_build_definition_by_name(self, **kwargs):
        return self._call_inner_tool('find_build_definition_by_name', kwargs)

    def list_all_build_definitions(self, **kwargs):
        return self._call_inner_tool('list_all_build_definitions', kwargs)

    def list_all_repositories(self, **kwargs):
        return self._call_inner_tool('list_all_repositories', kwargs)

    def get_repository_by_name(self, **kwargs):
        return self._call_inner_tool('get_repository_by_name', kwargs)

    def get_repository_by_id(self, **kwargs):
        return self._call_inner_tool('get_repository_by_id', kwargs)

    def list_branches_for_repository(self, **kwargs):
        return self._call_inner_tool('list_branches_for_repository', kwargs)

    def get_build_steps_for_definition(self, **kwargs):
        return self._call_inner_tool('get_build_steps_for_definition', kwargs)

    def get_build_step_by_id(self, **kwargs):
        return self._call_inner_tool('get_build_step_by_id', kwargs)

    def check_build_definition_name_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_build_definition_name_uniqueness', kwargs)

    def get_build_history_for_definition(self, **kwargs):
        return self._call_inner_tool('get_build_history_for_definition', kwargs)

    def update_build_definition_metadata(self, **kwargs):
        return self._call_inner_tool('update_build_definition_metadata', kwargs)

    def set_build_steps_for_definition(self, **kwargs):
        return self._call_inner_tool('set_build_steps_for_definition', kwargs)

    def add_build_step_to_definition(self, **kwargs):
        return self._call_inner_tool('add_build_step_to_definition', kwargs)

    def remove_build_step_from_definition(self, **kwargs):
        return self._call_inner_tool('remove_build_step_from_definition', kwargs)

    def reorder_build_steps_for_definition(self, **kwargs):
        return self._call_inner_tool('reorder_build_steps_for_definition', kwargs)

    def validate_build_definition_update(self, **kwargs):
        return self._call_inner_tool('validate_build_definition_update', kwargs)

    def create_build_step(self, **kwargs):
        return self._call_inner_tool('create_build_step', kwargs)

    def delete_build_step(self, **kwargs):
        return self._call_inner_tool('delete_build_step', kwargs)

    def create_build_definition(self, **kwargs):
        return self._call_inner_tool('create_build_definition', kwargs)

    def delete_build_definition(self, **kwargs):
        return self._call_inner_tool('delete_build_definition', kwargs)

    def trigger_build(self, **kwargs):
        return self._call_inner_tool('trigger_build', kwargs)

    def set_repository_status(self, **kwargs):
        return self._call_inner_tool('set_repository_status', kwargs)
