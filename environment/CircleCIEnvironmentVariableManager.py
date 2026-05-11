# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
import datetime
from datetime import datetime
from typing import Dict



class EnvironmentVariableInfo(TypedDict):
    name: str
    value: str
    created_at: str
    updated_at: str
    # Optional: 'secret' flag could be added

class ScopeInfo(TypedDict):
    scope_id: str
    scope_type: str  # "project" or "context"
    name: str
    description: str

class BuildJobInfo(TypedDict):
    job_id: str
    scope_id: str
    triggered_by: str
    status: str
    associated_variables: List[str]  # List of variable names

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing CircleCI environment variables and scoping.
        """

        # Scopes: {scope_id: ScopeInfo}
        # Entity: Scope (cope_id, scope_type, name, description)
        self.scopes: Dict[str, ScopeInfo] = {}

        # Environment variables:
        # {scope_id: {variable_name: EnvironmentVariableInfo}}
        # Entity: EnvironmentVariable (name, value, created_at, updated_at)
        # Variable names are unique within their scope.
        self.variables: Dict[str, Dict[str, EnvironmentVariableInfo]] = {}

        # Build jobs: {job_id: BuildJobInfo}
        # Entity: BuildJob (job_id, scope_id, triggered_by, status, associated_variables)
        self.build_jobs: Dict[str, BuildJobInfo] = {}

        # Constraints reminder:
        # - Environment variable names must be unique within a given scope.
        # - Modifying a variable’s value updates it for all future jobs/workflows in the associated scope.
        # - Environment variable values are not retrievable if marked as 'secret' (modeling optional).
        # - Only users with sufficient permissions can add/update/remove variables (not modeled in state).
        # - Removing a variable detaches it from the scope and affects future builds.


    def get_scope_by_name(self, name: str) -> dict:
        """
        Retrieve details for a scope (project or context) by its name.

        Args:
            name (str): The name of the scope.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ScopeInfo  # Information about the matching scope
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Scope with the specified name does not exist"
                    }

        Constraints:
            - No guarantee scope names are unique; returns the first match found.
            - Permissions are not enforced in this method.
        """
        for scope in self.scopes.values():
            if scope["name"] == name:
                return {"success": True, "data": scope}
        return {"success": False, "error": "Scope with the specified name does not exist"}

    def get_scope_by_id(self, scope_id: str) -> dict:
        """
        Retrieve details for a scope using its unique id.

        Args:
            scope_id (str): The unique identifier for the scope.

        Returns:
            dict: 
              - If found: {"success": True, "data": ScopeInfo}
              - If not found: {"success": False, "error": "Scope not found"}

        Constraints:
            - Scope id must exist in the environment.
        """
        scope = self.scopes.get(scope_id)
        if scope is None:
            return {"success": False, "error": "Scope not found"}
        return {"success": True, "data": scope}

    def list_scopes(self) -> dict:
        """
        List all scopes (projects and contexts) currently managed.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ScopeInfo]  # All managed scopes, may be empty if none.
            }
        """
        result = list(self.scopes.values())
        return { "success": True, "data": result }

    def list_variables_in_scope(self, scope_id: str) -> dict:
        """
        Retrieve all environment variables (names and metadata) for the given scope.

        Args:
            scope_id (str): ID of the project or context whose variables are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[EnvironmentVariableInfo],  # May be empty if no variables assigned
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Scope does not exist"
            }

        Constraints:
            - The scope must exist.
            - All variables in the scope (if any) are returned.
        """
        if scope_id not in self.scopes:
            return {"success": False, "error": "Scope does not exist"}

        variables = list(self.variables.get(scope_id, {}).values())
        return {"success": True, "data": variables}

    def get_variable_info(self, scope_id: str, variable_name: str) -> dict:
        """
        Retrieve metadata and value for a variable by name within the specified scope.

        Args:
            scope_id (str): The unique ID of the scope (project/context).
            variable_name (str): The name of the environment variable.

        Returns:
            dict: 
              - If found (and not secret): { "success": True, "data": EnvironmentVariableInfo }
              - If found (but secret): { "success": True, "data": <metadata with value omitted> }
              - If not found: { "success": False, "error": str }

        Constraints:
            - Variable must exist in the given scope.
            - If the variable's 'secret' flag is set (if modeled), do not include value in result.
        """
        if scope_id not in self.variables:
            return {"success": False, "error": "Scope does not exist"}

        variable_dict = self.variables[scope_id]
        if variable_name not in variable_dict:
            return {"success": False, "error": "Variable does not exist in the specified scope"}

        var_info = variable_dict[variable_name]
        # Handle 'secret' variable, if this flag is present
        if 'secret' in var_info and var_info.get('secret', False):
            # Return all metadata except for 'value'
            data = {k: v for k, v in var_info.items() if k != "value"}
            data["value"] = None  # Explicitly indicate it's not accessible
            return {"success": True, "data": data}
        # Not secret: return full info
        return {"success": True, "data": var_info}

    def check_variable_exists(self, scope_id: str, variable_name: str) -> dict:
        """
        Determine if an environment variable with the given name exists in the specified scope.

        Args:
            scope_id (str): The identifier of the scope (project/context).
            variable_name (str): The name of the environment variable.

        Returns:
            dict:
                - If scope not found:
                    { "success": False, "error": "Scope not found" }
                - Else:
                    { "success": True, "data": bool }  # True if variable exists in scope, else False

        Constraints:
            - Scope must exist.
            - Variable names are checked case-sensitively and must be unique within their scope.
        """
        if scope_id not in self.scopes:
            return { "success": False, "error": "Scope not found" }

        exists = variable_name in self.variables.get(scope_id, {})
        return { "success": True, "data": exists }

    def is_variable_secret(self, scope_id: str, variable_name: str) -> dict:
        """
        Check if an environment variable in a given scope is marked as 'secret'.

        Args:
            scope_id (str): The scope identifier where the variable is defined.
            variable_name (str): The name of the variable to check.

        Returns:
            dict: {
                "success": True,
                "is_secret": bool  # True if marked secret, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # error message if scope or variable not found
            }

        Notes/Constraints:
            - If 'secret' flag is not present, the variable is considered not secret (False).
            - Returns error if scope or variable does not exist.
        """
        if scope_id not in self.variables:
            return {"success": False, "error": "Scope does not exist"}
        if variable_name not in self.variables[scope_id]:
            return {"success": False, "error": "Variable does not exist in scope"}
        var_info = self.variables[scope_id][variable_name]
        is_secret = bool(var_info.get("secret", False))
        return {"success": True, "is_secret": is_secret}

    def list_build_jobs_by_scope(self, scope_id: str) -> dict:
        """
        List all build jobs associated with a particular scope.

        Args:
            scope_id (str): Unique identifier of the scope (project or context).

        Returns:
            dict: {
                "success": True,
                "data": List[BuildJobInfo],  # List of build jobs (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. scope does not exist
            }

        Constraints:
            - The provided scope_id must exist in self.scopes.
        """
        if scope_id not in self.scopes:
            return { "success": False, "error": "Scope does not exist" }

        result = [
            job_info for job_info in self.build_jobs.values()
            if job_info["scope_id"] == scope_id
        ]

        return { "success": True, "data": result }

    def list_jobs_using_variable(self, scope_id: str, variable_name: str) -> dict:
        """
        List all build jobs that reference a specific environment variable in a given scope.

        Args:
            scope_id (str): The scope ID in which the variable is defined.
            variable_name (str): The name of the environment variable.

        Returns:
            dict: {
                "success": True,
                "data": List[BuildJobInfo],  # List of build jobs referencing the variable (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. scope or variable does not exist
            }

        Constraints:
            - The scope must exist.
            - The variable must exist in the given scope.
        """
        if scope_id not in self.scopes:
            return { "success": False, "error": "Scope does not exist" }
        if scope_id not in self.variables or variable_name not in self.variables[scope_id]:
            return { "success": False, "error": "Variable does not exist in scope" }

        matching_jobs = [
            job_info for job_info in self.build_jobs.values()
            if job_info["scope_id"] == scope_id and variable_name in job_info["associated_variables"]
        ]

        return { "success": True, "data": matching_jobs }


    def add_variable(self, scope_id: str, variable_name: str, value: str) -> dict:
        """
        Add a new environment variable to the specified scope.

        Args:
            scope_id (str): ID of the scope (project/context) to add the variable to.
            variable_name (str): Unique name for the variable within the scope.
            value (str): Value of the environment variable.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Variable '<variable_name>' added to scope '<scope_id>'."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Scope does not exist."
                    }
                    or
                    {
                        "success": False,
                        "error": "Variable name already exists in scope."
                    }

        Constraints:
            - Scope must exist.
            - Variable names must be unique within the scope.
        """
        if scope_id not in self.scopes:
            return { "success": False, "error": "Scope does not exist." }

        # Ensure variable names container exists for the scope
        if scope_id not in self.variables:
            self.variables[scope_id] = {}

        if variable_name in self.variables[scope_id]:
            return { "success": False, "error": "Variable name already exists in scope." }

        current_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        var_info = {
            "name": variable_name,
            "value": value,
            "created_at": current_time,
            "updated_at": current_time,
            # 'secret' and other optional fields omitted for base implementation
        }
        self.variables[scope_id][variable_name] = var_info

        return {
            "success": True,
            "message": f"Variable '{variable_name}' added to scope '{scope_id}'."
        }


    def update_variable_value(self, scope_id: str, variable_name: str, new_value: str) -> dict:
        """
        Change the value of an existing environment variable in a scope.

        Args:
            scope_id (str): The ID of the scope containing the variable (project or context).
            variable_name (str): The unique variable name within the scope.
            new_value (str): The new value to set for the variable.

        Returns:
            dict: {
                "success": True,
                "message": "Variable value updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. scope or variable does not exist
            }

        Constraints:
            - Scope must exist.
            - Variable must exist in specified scope.
            - On update, the variable's 'updated_at' field must be set to current timestamp.
            - Secret flag handling (not shown here) could restrict value updating.

        """
        # Check for scope existence
        if scope_id not in self.scopes:
            return { "success": False, "error": "Scope does not exist." }

        # Check variable existence in scope
        scope_vars = self.variables.get(scope_id)
        if not scope_vars or variable_name not in scope_vars:
            return { "success": False, "error": "Variable does not exist in this scope." }

        # Optionally check for 'secret' flag: (not modeled, but could be like:
        # if scope_vars[variable_name].get('secret'): ... )

        # Update value and updated_at
        scope_vars[variable_name]["value"] = new_value
        scope_vars[variable_name]["updated_at"] = str(time.time())

        return { "success": True, "message": "Variable value updated successfully." }

    def remove_variable(self, scope_id: str, variable_name: str) -> dict:
        """
        Delete/detach an environment variable from the given scope.

        Args:
            scope_id (str): The ID of the scope from which the variable should be removed.
            variable_name (str): The name of the variable to remove.

        Returns:
            dict:
                - On success: {"success": True, "message": "Variable '<name>' removed from scope '<scope_id>'."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - scope_id must exist in self.scopes.
            - variable_name must exist within self.variables[scope_id].
            - Removing detaches the variable from scope and affects future builds.
        """
        if scope_id not in self.scopes:
            return {"success": False, "error": f"Scope '{scope_id}' does not exist."}

        if scope_id not in self.variables or variable_name not in self.variables[scope_id]:
            return {"success": False, "error": f"Variable '{variable_name}' does not exist in scope '{scope_id}'."}

        del self.variables[scope_id][variable_name]

        return {
            "success": True,
            "message": f"Variable '{variable_name}' removed from scope '{scope_id}'."
        }

    def rename_variable(self, scope_id: str, old_name: str, new_name: str) -> dict:
        """
        Rename an environment variable within a scope, enforcing unique names per scope.

        Args:
            scope_id (str): The id of the scope (project or context)
            old_name (str): The current variable name
            new_name (str): The desired new variable name

        Returns:
            dict: Success or error message

        Constraints:
            - Scope must exist in self.scopes
            - Variable 'old_name' must exist in self.variables[scope_id]
            - Variable 'new_name' must not already exist in self.variables[scope_id]
            - Variable names are unique per scope
            - If any build job's 'associated_variables' contains old_name, update to new_name
            - Update updated_at timestamp
        """

        # Scope check
        if scope_id not in self.scopes:
            return {"success": False, "error": "Scope does not exist."}

        variables_in_scope = self.variables.get(scope_id, {})

        if old_name == new_name:
            return {"success": False, "error": "Old and new variable names are the same."}

        if old_name not in variables_in_scope:
            return {"success": False, "error": f"Variable '{old_name}' does not exist in scope."}

        if new_name in variables_in_scope:
            return {"success": False, "error": f"Variable name '{new_name}' already exists in scope."}

        # Rename variable
        var_info = variables_in_scope[old_name]
        var_info["name"] = new_name
        # Update updated_at
        var_info["updated_at"] = datetime.utcnow().isoformat()

        # Insert new variable and remove the old one
        variables_in_scope[new_name] = var_info
        del variables_in_scope[old_name]
        self.variables[scope_id] = variables_in_scope

        # Update all associated build jobs
        for job in self.build_jobs.values():
            if job["scope_id"] == scope_id:
                job["associated_variables"] = [
                    new_name if v == old_name else v for v in job["associated_variables"]
                ]

        return {
            "success": True,
            "message": f"Variable renamed from '{old_name}' to '{new_name}' in scope '{scope_id}'."
        }

    def set_variable_secret_flag(self, scope_id: str, variable_name: str, secret: bool) -> dict:
        """
        Mark or unmark an environment variable as 'secret' within a given scope.
        If variable does not support the 'secret' flag in its info, this key will be added.

        Args:
            scope_id (str): Scope identifier (project/context) containing the variable.
            variable_name (str): The name of the environment variable.
            secret (bool): True to mark as secret, False to unmark.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Variable 'X' in scope 'Y' marked (or unmarked) as secret."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }
        Constraints:
            - Variable must exist within given scope.
            - Scope must exist.
            - This operation adds or updates the 'secret' flag for the variable.
        """
        if scope_id not in self.scopes:
            return {"success": False, "error": "Scope does not exist."}
        if scope_id not in self.variables or variable_name not in self.variables[scope_id]:
            return {"success": False, "error": "Variable does not exist in given scope."}
    
        variable_info = self.variables[scope_id][variable_name]
        variable_info['secret'] = secret

        action = "marked as secret" if secret else "unmarked as secret"
        return {
            "success": True,
            "message": f"Variable '{variable_name}' in scope '{scope_id}' {action}."
        }


    def bulk_update_variables(self, scope_id: str, updates: Dict[str, str]) -> dict:
        """
        Update multiple variable values in a single operation for a given scope.

        Args:
            scope_id (str): The ID of the scope (project/context) in which the variables reside.
            updates (Dict[str, str]): A mapping from variable names to their new string values.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "Bulk updated X variable(s)."
                    }
                Failure (any missing variable, etc.):
                    {
                        "success": False,
                        "error": "Error message"
                    }

        Constraints:
            - All variable names in 'updates' must exist in the given scope.
            - 'updated_at' is set to current UTC time for updated variables.
            - If 'updates' is empty, succeeds with 0 updates.
            - If scope does not exist, fails.
            - No partial updates on error (all-or-nothing).
        """
        # Check scope existence
        if scope_id not in self.scopes:
            return {
                "success": False,
                "error": f"Scope '{scope_id}' does not exist."
            }
        if scope_id not in self.variables:
            # No variables at all in this scope
            if updates:
                missing_vars = list(updates.keys())
                return {
                    "success": False,
                    "error": f"Variable(s) not found in scope: {missing_vars}"
                }
            else:
                # nothing to update
                return {
                    "success": True,
                    "message": "Bulk updated 0 variable(s)."
                }

        scope_variables = self.variables[scope_id]
        missing_vars = [name for name in updates if name not in scope_variables]
        if missing_vars:
            return {
                "success": False,
                "error": f"Variable(s) not found in scope: {missing_vars}"
            }

        now = datetime.utcnow().isoformat()
        for name, value in updates.items():
            var_info = scope_variables[name]
            var_info["value"] = value
            var_info["updated_at"] = now
            # self.variables[scope_id][name] = var_info # Not strictly needed since dict is mutable

        return {
            "success": True,
            "message": f"Bulk updated {len(updates)} variable(s)."
        }

    def bulk_remove_variables(self, scope_id: str, variable_names: list) -> dict:
        """
        Remove several environment variables at once from a given scope.

        Args:
            scope_id (str): The ID of the scope (project/context) from which to remove variables.
            variable_names (List[str]): List of variable names (str) to remove from the scope.

        Returns:
            dict: {
                "success": True,
                "message": "Removed variables: [...]. Not found: [...]."
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Scope must exist.
            - Only removes variables present in the specified scope.
            - Variables not present are reported under 'Not found'.
        """
        if scope_id not in self.scopes:
            return {"success": False, "error": "Scope does not exist"}

        removed = []
        not_found = []

        # If scope has no variables at all, treat all as not found
        if scope_id not in self.variables:
            not_found = variable_names[:]
        else:
            for var_name in variable_names:
                if var_name in self.variables[scope_id]:
                    del self.variables[scope_id][var_name]
                    removed.append(var_name)
                else:
                    not_found.append(var_name)

        msg_list = []
        if removed:
            msg_list.append(f"Removed variables: {removed}")
        if not_found:
            msg_list.append(f"Not found: {not_found}")
        if not msg_list:
            msg_list.append("No variables specified for removal.")

        return {"success": True, "message": " ".join(msg_list)}


class CircleCIEnvironmentVariableManager(BaseEnv):
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

    def get_scope_by_name(self, **kwargs):
        return self._call_inner_tool('get_scope_by_name', kwargs)

    def get_scope_by_id(self, **kwargs):
        return self._call_inner_tool('get_scope_by_id', kwargs)

    def list_scopes(self, **kwargs):
        return self._call_inner_tool('list_scopes', kwargs)

    def list_variables_in_scope(self, **kwargs):
        return self._call_inner_tool('list_variables_in_scope', kwargs)

    def get_variable_info(self, **kwargs):
        return self._call_inner_tool('get_variable_info', kwargs)

    def check_variable_exists(self, **kwargs):
        return self._call_inner_tool('check_variable_exists', kwargs)

    def is_variable_secret(self, **kwargs):
        return self._call_inner_tool('is_variable_secret', kwargs)

    def list_build_jobs_by_scope(self, **kwargs):
        return self._call_inner_tool('list_build_jobs_by_scope', kwargs)

    def list_jobs_using_variable(self, **kwargs):
        return self._call_inner_tool('list_jobs_using_variable', kwargs)

    def add_variable(self, **kwargs):
        return self._call_inner_tool('add_variable', kwargs)

    def update_variable_value(self, **kwargs):
        return self._call_inner_tool('update_variable_value', kwargs)

    def remove_variable(self, **kwargs):
        return self._call_inner_tool('remove_variable', kwargs)

    def rename_variable(self, **kwargs):
        return self._call_inner_tool('rename_variable', kwargs)

    def set_variable_secret_flag(self, **kwargs):
        return self._call_inner_tool('set_variable_secret_flag', kwargs)

    def bulk_update_variables(self, **kwargs):
        return self._call_inner_tool('bulk_update_variables', kwargs)

    def bulk_remove_variables(self, **kwargs):
        return self._call_inner_tool('bulk_remove_variables', kwargs)
