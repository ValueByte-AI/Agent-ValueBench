# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from datetime import datetime



# User: _id, name, email, authentication_tokens, connected_services
class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    authentication_tokens: Dict[str, str]  # service_id -> token
    connected_services: List[str]  # List of authorized service_ids

# Service: service_id, name, service_type, capabilities
class ServiceInfo(TypedDict):
    service_id: str
    name: str
    service_type: str
    capabilities: List[str]

# Recipe: recipe_id, user_id, trigger, condition, action, enabled, created_at, last_executed_at
class RecipeInfo(TypedDict):
    recipe_id: str
    user_id: str
    trigger: str  # trigger_id
    condition: str  # serialized condition logic
    action: str  # action_id
    enabled: bool
    created_at: str
    last_executed_at: str

# Trigger: trigger_id, service_id, event_type, configuration
class TriggerInfo(TypedDict):
    trigger_id: str
    service_id: str
    event_type: str
    configuration: Dict[str, Any]

# Action: action_id, service_id, action_type, configuration
class ActionInfo(TypedDict):
    action_id: str
    service_id: str
    action_type: str
    configuration: Dict[str, Any]

# ExecutionLog: execution_id, recipe_id, executed_at, status, result
class ExecutionLogInfo(TypedDict):
    execution_id: str
    recipe_id: str
    executed_at: str
    status: str
    result: Any

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Services: {service_id: ServiceInfo}
        self.services: Dict[str, ServiceInfo] = {}
        # Recipes: {recipe_id: RecipeInfo}
        self.recipes: Dict[str, RecipeInfo] = {}
        # Triggers: {trigger_id: TriggerInfo}
        self.triggers: Dict[str, TriggerInfo] = {}
        # Actions: {action_id: ActionInfo}
        self.actions: Dict[str, ActionInfo] = {}
        # Execution logs: {execution_id: ExecutionLogInfo}
        self.execution_logs: Dict[str, ExecutionLogInfo] = {}

        # Constraints:
        # - A recipe can only use triggers and actions from services the user has connected/authorized.
        # - The platform must store valid authentication tokens for each connected service and user.
        # - Recipes execute only when their trigger event occurs and any specified condition is met.
        # - Actions may fail if service tokens are invalid or the external service is unavailable; such execution results should be logged.
        # - Recipes can be enabled or disabled by the user.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info and credentials by user ID.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User information if found
            }
            or
            {
                "success": False,
                "error": str  # "User not found"
            }

        Constraints:
            - The user ID must exist in the platform's user database.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def list_user_connected_services(self, user_id: str) -> dict:
        """
        List all external services connected/authorized by a specific user.

        Args:
            user_id (str): ID of the user whose connected services are being queried.

        Returns:
            dict: 
                {"success": True, "data": List[ServiceInfo]}      # If user found
                or
                {"success": False, "error": str}                  # If user not found

        Constraints:
            - The user must exist.
            - Only services listed in the user's connected_services will be returned (and only if found in the platform's service registry).
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        connected_services = []
        for service_id in user.get("connected_services", []):
            service = self.services.get(service_id)
            if service:
                connected_services.append(service)

        return {"success": True, "data": connected_services}

    def get_user_authentication_token(self, user_id: str, service_id: str) -> dict:
        """
        Retrieve the authentication token for the given user and service.

        Args:
            user_id (str): The unique ID of the user.
            service_id (str): The unique ID of the service.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": <token: str>
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - User must exist.
            - User must have connected the service (i.e., a token for that service must exist).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        token = user.get("authentication_tokens", {}).get(service_id)
        if not token:
            return { "success": False, "error": "Authentication token for service not found for this user" }

        return { "success": True, "data": token }

    def list_all_services(self) -> dict:
        """
        List all available services and integrations in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ServiceInfo]  # List of all registered services/integrations (possibly empty)
            }
        Constraints:
            - None. This is a simple, permissionless global query.
        """
        all_services = list(self.services.values())
        return {"success": True, "data": all_services}

    def get_service_by_id(self, service_id: str) -> dict:
        """
        Retrieve details of a service by its ID.

        Args:
            service_id (str): The unique identifier of the service.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": ServiceInfo  # The service metadata dictionary
                }
                On failure:
                {
                    "success": False,
                    "error": "Service not found"
                }

        Constraints:
            - No authentication/authorization required.
            - Fails if the service ID does not exist.
        """
        service = self.services.get(service_id)
        if not service:
            return { "success": False, "error": "Service not found" }
        return { "success": True, "data": service }

    def list_service_triggers(self, service_id: str) -> dict:
        """
        List all triggers provided by a given service.

        Args:
            service_id (str): The unique identifier of the service.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TriggerInfo]  # a list of triggers (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # error message if service_id does not exist
                }

        Constraints:
            - The specified service_id must exist in self.services.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service does not exist" }

        triggers = [
            trigger_info
            for trigger_info in self.triggers.values()
            if trigger_info["service_id"] == service_id
        ]
        return { "success": True, "data": triggers }

    def list_service_actions(self, service_id: str) -> dict:
        """
        List all actions that a given service can perform.

        Args:
            service_id (str): The unique identifier of the service.

        Returns:
            dict: {
                "success": True,
                "data": List[ActionInfo],  # List of ActionInfo dictionaries (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. service does not exist
            }

        Constraints:
            - The given service_id must exist in the platform.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service does not exist" }

        actions = [
            action_info
            for action_info in self.actions.values()
            if action_info["service_id"] == service_id
        ]

        return { "success": True, "data": actions }

    def get_trigger_by_id(self, trigger_id: str) -> dict:
        """
        Retrieve details about a specific trigger, including parameters/configuration.

        Args:
            trigger_id (str): The unique identifier of the trigger.

        Returns:
            dict: {
                "success": True,
                "data": TriggerInfo  # Details of the trigger
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g. trigger not found
            }

        Constraints:
            - The trigger_id must exist in the platform.
        """
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            return { "success": False, "error": "Trigger not found" }
        return { "success": True, "data": trigger }

    def get_action_by_id(self, action_id: str) -> dict:
        """
        Retrieve the details for a specific action (including type and configuration) by its action_id.

        Args:
            action_id (str): The unique identifier of the action to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ActionInfo  # The action's full metadata
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Action not found"
                    }
        Constraints:
            - The given action_id must exist in the actions dictionary.
        """
        if not action_id or action_id not in self.actions:
            return { "success": False, "error": "Action not found" }
        action_info = self.actions[action_id]
        return { "success": True, "data": action_info }

    def list_user_recipes(self, user_id: str) -> dict:
        """
        Fetch all recipes created by a user.

        Args:
            user_id (str): The unique id of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[RecipeInfo]  # Recipes created by this user (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. user not found
            }

        Constraints:
            - user_id must exist in the platform.
            - No further constraints apply (listing is allowed for own recipes).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        recipes = [
            recipe for recipe in self.recipes.values()
            if recipe["user_id"] == user_id
        ]

        return { "success": True, "data": recipes }

    def get_recipe_by_id(self, recipe_id: str) -> dict:
        """
        Retrieve the complete details and state of a recipe given its ID.

        Args:
            recipe_id (str): The unique identifier for the recipe.

        Returns:
            dict: {
                "success": True,
                "data": RecipeInfo,   # Full info for the recipe
            }
            or
            {
                "success": False,
                "error": str         # Reason for failure (e.g., not found)
            }

        Constraints:
            - The specified recipe_id must exist in the platform.
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return { "success": False, "error": "Recipe not found" }
        return { "success": True, "data": recipe }

    def list_recipe_execution_logs(self, recipe_id: str) -> dict:
        """
        Fetch all execution logs for a specific recipe.

        Args:
            recipe_id (str): The unique identifier of the recipe to fetch logs for.

        Returns:
            dict: 
             - On success: {"success": True, "data": List[ExecutionLogInfo]}
               (data may be an empty list if no logs are found)
             - On error: {"success": False, "error": str}
               (if the recipe does not exist)

        Constraints:
            - The given recipe must exist on the platform.
        """
        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe does not exist" }

        logs = [
            log for log in self.execution_logs.values()
            if log["recipe_id"] == recipe_id
        ]

        return { "success": True, "data": logs }

    def get_execution_log_by_id(self, execution_id: str) -> dict:
        """
        Retrieve status and result details for a specific recipe execution attempt.

        Args:
            execution_id (str): Unique identifier of the execution log entry.

        Returns:
            dict: {
                "success": True,
                "data": ExecutionLogInfo  # The log info if found
            }
            or
            {
                "success": False,
                "error": str  # Reason the log could not be found
            }
        """
        if execution_id not in self.execution_logs:
            return { "success": False, "error": "Execution log not found" }
        return { "success": True, "data": self.execution_logs[execution_id] }

    def check_recipe_enabled_status(self, recipe_id: str) -> dict:
        """
        Determine if a recipe is currently enabled or disabled.

        Args:
            recipe_id (str): The ID of the recipe to check.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {"recipe_id": str, "enabled": bool}
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # "Recipe not found"
                    }
        Constraints:
            - The recipe_id must exist in the platform's recipe registry.
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return {"success": False, "error": "Recipe not found"}
        return {
            "success": True,
            "data": {
                "recipe_id": recipe_id,
                "enabled": recipe.get("enabled", False)
            }
        }

    def check_user_service_authorization(self, user_id: str, service_id: str) -> dict:
        """
        Determines whether the specified user is authorized for the given service.

        Args:
            user_id (str): The ID of the user to check.
            service_id (str): The ID of the service to check.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "authorized": bool  # True if user authorized and has valid token, False otherwise
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Error description
                    }

        Constraints:
            - User must exist.
            - Service must exist.
            - User must have service_id in connected_services AND a valid (non-empty) authentication_token for service.
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check service exists
        service = self.services.get(service_id)
        if not service:
            return { "success": False, "error": "Service does not exist" }
    
        # Check authorization: service in connected_services
        if service_id not in user.get("connected_services", []):
            return { "success": True, "authorized": False }
    
        # Check that user has a non-empty token for the service
        token = user.get("authentication_tokens", {}).get(service_id)
        if not token:
            # No token or empty/None token (not valid)
            return { "success": True, "authorized": False }
    
        # All checks passed: user is authorized
        return { "success": True, "authorized": True }

    def connect_service_to_user(self, user_id: str, service_id: str, authentication_token: str) -> dict:
        """
        Add/authorize a service for a user, updating their connected_services and storing required authentication token.

        Args:
            user_id (str): The ID of the user.
            service_id (str): The ID of the service to connect/authorize.
            authentication_token (str): The authentication token for this service-user link.

        Returns:
            dict: {
                "success": True,
                "message": "Service connected to user"
            } 
            Or if failed:
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - User and service must exist.
            - Service may not already be connected to user (prevents duplicates).
            - Updates both user's connected_services and authentication_tokens.
        """
        # Input validation
        if not user_id or not service_id or not authentication_token:
            return {"success": False, "error": "Invalid input"}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        service = self.services.get(service_id)
        if not service:
            return {"success": False, "error": "Service not found"}

        if service_id in user.get("connected_services", []):
            return {"success": False, "error": "Service already connected to user"}

        # Update connected_services
        user["connected_services"].append(service_id)

        # Update authentication_tokens
        user["authentication_tokens"][service_id] = authentication_token

        # Persist change
        self.users[user_id] = user

        return {"success": True, "message": "Service connected to user"}

    def disconnect_service_from_user(self, user_id: str, service_id: str) -> dict:
        """
        Remove/deauthorize a service from a user's connected services.

        Args:
            user_id (str): The unique user identifier.
            service_id (str): The ID of the service to disconnect from the user.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Service disconnected from user" }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - User must exist.
            - Service must exist.
            - Service must be in the user's connected_services.
            - Authentication token for the service is removed from authentication_tokens if it exists.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if service_id not in self.services:
            return {"success": False, "error": "Service does not exist"}

        user = self.users[user_id]
        # Check if the service is actually connected
        if service_id not in user["connected_services"]:
            return {"success": False, "error": "Service not connected to user"}

        # Remove from connected_services list
        user["connected_services"].remove(service_id)

        # Remove authentication token if it exists
        if service_id in user["authentication_tokens"]:
            del user["authentication_tokens"][service_id]

        return {"success": True, "message": "Service disconnected from user"}

    def create_recipe(
        self,
        user_id: str,
        trigger_id: str,
        action_id: str,
        condition: str = "",
        enabled: bool = True,
    ) -> dict:
        """
        Create a new recipe for a user, specifying trigger, action, and any conditions.

        Args:
            user_id (str): The user creating the recipe.
            trigger_id (str): The trigger (event source) to use.
            action_id (str): The action to perform when triggered.
            condition (str): Serialized condition logic (optional).
            enabled (bool): Whether the recipe is enabled upon creation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Recipe created",
                        "recipe_id": <generated_id>,
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>,
                    }

        Constraints:
            - User must exist.
            - Trigger and action must exist.
            - Both trigger.service_id and action.service_id must be in user's connected_services.
            - Timestamps set to now (ISO 8601).
        """

        # Verify user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}

        # Verify trigger exists
        trigger = self.triggers.get(trigger_id)
        if trigger is None:
            return {"success": False, "error": "Trigger does not exist"}

        # Verify action exists
        action = self.actions.get(action_id)
        if action is None:
            return {"success": False, "error": "Action does not exist"}

        # Verify trigger's service is connected
        trigger_service_id = trigger.get("service_id")
        if trigger_service_id not in user.get("connected_services", []):
            return {"success": False, "error": "User has not connected the trigger's service"}

        # Verify action's service is connected
        action_service_id = action.get("service_id")
        if action_service_id not in user.get("connected_services", []):
            return {"success": False, "error": "User has not connected the action's service"}

        # Generate unique recipe_id
        recipe_id = str(uuid.uuid4())
        while recipe_id in self.recipes:
            recipe_id = str(uuid.uuid4())

        now_iso = datetime.utcnow().isoformat() + "Z"

        # Construct new recipe entry
        new_recipe = {
            "recipe_id": recipe_id,
            "user_id": user_id,
            "trigger": trigger_id,
            "condition": condition,
            "action": action_id,
            "enabled": enabled,
            "created_at": now_iso,
            "last_executed_at": "",  # Not executed yet
        }

        self.recipes[recipe_id] = new_recipe

        return {
            "success": True,
            "message": "Recipe created",
            "recipe_id": recipe_id,
        }

    def edit_recipe(
        self,
        recipe_id: str,
        trigger: str = None,
        condition: str = None,
        action: str = None,
        enabled: bool = None
    ) -> dict:
        """
        Modify fields of an existing recipe (trigger, action, condition, enabled flag).

        Args:
            recipe_id (str): ID of the recipe to modify.
            trigger (str, optional): New trigger_id to set.
            condition (str, optional): New serialized condition logic.
            action (str, optional): New action_id to set.
            enabled (bool, optional): Enable or disable the recipe.

        Returns:
            dict: Success/failure structure.
                On success: { "success": True, "message": "Recipe updated successfully" }
                On failure: { "success": False, "error": "..." }

        Constraints:
            - Recipe must exist.
            - If changing trigger or action, specified trigger/action must exist.
            - New trigger's and action's service must be in the user's connected_services.
            - enabled param, if present, must be bool.
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return { "success": False, "error": "Recipe not found" }
        user = self.users.get(recipe['user_id'])
        if user is None:
            return { "success": False, "error": "Associated user not found" }

        # Keep track of what is being updated
        updated_fields = []

        # Trigger update
        if trigger is not None:
            trigger_info = self.triggers.get(trigger)
            if trigger_info is None:
                return { "success": False, "error": f"Trigger {trigger} not found" }
            trigger_service_id = trigger_info['service_id']
            if trigger_service_id not in user['connected_services']:
                return { "success": False, "error": f"User has not connected service '{trigger_service_id}' required for the trigger" }
            recipe['trigger'] = trigger
            updated_fields.append('trigger')

        # Action update
        if action is not None:
            action_info = self.actions.get(action)
            if action_info is None:
                return { "success": False, "error": f"Action {action} not found" }
            action_service_id = action_info['service_id']
            if action_service_id not in user['connected_services']:
                return { "success": False, "error": f"User has not connected service '{action_service_id}' required for the action" }
            recipe['action'] = action
            updated_fields.append('action')

        # Condition update
        if condition is not None:
            recipe['condition'] = condition
            updated_fields.append('condition')

        # Enabled update
        if enabled is not None:
            if not isinstance(enabled, bool):
                return { "success": False, "error": "'enabled' must be a boolean value" }
            recipe['enabled'] = enabled
            updated_fields.append('enabled')

        if not updated_fields:
            return { "success": False, "error": "No update fields specified" }

        self.recipes[recipe_id] = recipe  # Optional since dict is mutable, included for clarity

        return {
            "success": True,
            "message": f"Recipe updated successfully ({', '.join(updated_fields)})"
        }

    def delete_recipe(self, recipe_id: str) -> dict:
        """
        Remove a recipe from the user's account.

        Args:
            recipe_id (str): The ID of the recipe to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Recipe deleted successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The recipe must exist to be deleted.
            - Does not delete associated execution logs or references.
        """
        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe does not exist." }
    
        del self.recipes[recipe_id]
        return { "success": True, "message": "Recipe deleted successfully" }

    def enable_recipe(self, recipe_id: str) -> dict:
        """
        Set a recipe's enabled state to True.

        Args:
            recipe_id (str): The unique identifier of the recipe to enable.

        Returns:
            dict: 
                On success: { "success": True, "message": "Recipe <recipe_id> enabled." }
                On failure: { "success": False, "error": "Recipe not found" }

        Constraints:
            - The recipe must exist within the platform.
            - This operation is idempotent: enabling an already enabled recipe is still a success.
        """
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return { "success": False, "error": "Recipe not found" }
    
        recipe["enabled"] = True
        self.recipes[recipe_id] = recipe  # technically not needed, but keeps pattern consistent
    
        return { "success": True, "message": f"Recipe {recipe_id} enabled." }

    def disable_recipe(self, recipe_id: str) -> dict:
        """
        Disable a recipe by setting its enabled state to False.

        Args:
            recipe_id (str): The ID of the recipe to disable.

        Returns:
            dict: {
                "success": True,
                "message": f"Recipe {recipe_id} has been disabled."
            }
            or
            {
                "success": False,
                "error": "Recipe not found"
            }

        Constraints:
            - Only an existing recipe can be disabled.
            - The operation is idempotent; if the recipe is already disabled, it remains so.
        """
        if recipe_id not in self.recipes:
            return {"success": False, "error": "Recipe not found"}
    
        self.recipes[recipe_id]["enabled"] = False
        return {
            "success": True,
            "message": f"Recipe {recipe_id} has been disabled."
        }

    def force_execute_recipe(self, recipe_id: str) -> dict:
        """
        Manually execute a recipe for testing or debugging purposes, regardless of whether it is enabled.
        Simulates trigger and action execution, and always logs the attempt/result.

        Args:
            recipe_id (str): The identifier of the recipe to be executed.

        Returns:
            dict: {
                "success": True,
                "message": "Recipe executed and logged",
                "execution_id": str  # id of the execution log entry
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The recipe must exist.
            - The trigger and action referenced in the recipe must exist.
            - The user must have the required services connected/authorized and associated tokens.
            - Regardless of success or failure, the execution attempt must be logged.
        """

        # 1. Recipe must exist
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "error": "Recipe does not exist"}

        status = "success"
        result = {
            "triggered_event": None,
            "action_performed": None,
            "details": {},
            "notes": "",
        }
        now = datetime.now().isoformat()
        user = self.users.get(recipe["user_id"])
        trigger = self.triggers.get(recipe["trigger"])
        action = self.actions.get(recipe["action"])

        if not user:
            status = "failure"
            result["notes"] = "User associated with recipe does not exist"
        elif not trigger:
            status = "failure"
            result["notes"] = "Trigger referenced by recipe does not exist"
        elif not action:
            status = "failure"
            result["notes"] = "Action referenced by recipe does not exist"
        else:
            result["triggered_event"] = trigger["event_type"]
            result["action_performed"] = action["action_type"]
            trigger_service_id = trigger["service_id"]
            action_service_id = action["service_id"]

            if (
                trigger_service_id not in user["connected_services"]
                or trigger_service_id not in user["authentication_tokens"]
            ):
                status = "failure"
                result["notes"] = (
                    "User has not connected or authorized trigger's service "
                    f"({trigger_service_id})"
                )
            elif (
                action_service_id not in user["connected_services"]
                or action_service_id not in user["authentication_tokens"]
            ):
                status = "failure"
                result["notes"] = (
                    "User has not connected or authorized action's service "
                    f"({action_service_id})"
                )
            else:
                result["details"] = {
                    "executed_for_testing": True,
                    "trigger_configuration": trigger["configuration"],
                    "action_configuration": action["configuration"],
                }

        # Log the execution
        execution_id = str(uuid.uuid4())
        self.execution_logs[execution_id] = {
            "execution_id": execution_id,
            "recipe_id": recipe_id,
            "executed_at": now,
            "status": status,
            "result": result,
        }

        recipe["last_executed_at"] = now

        if status == "success":
            return {
                "success": True,
                "message": "Recipe executed and logged",
                "execution_id": execution_id
            }
        else:
            return {
                "success": False,
                "error": result["notes"],
                "execution_id": execution_id
            }

    def log_recipe_execution(
        self,
        execution_id: str,
        recipe_id: str,
        executed_at: str,
        status: str,
        result: Any
    ) -> dict:
        """
        Record a new execution attempt in the platform's execution logs.

        Args:
            execution_id (str): Unique ID for this execution log entry.
            recipe_id (str): The recipe whose execution is being logged. Must exist.
            executed_at (str): Execution timestamp (ISO 8601 or similar string).
            status (str): Status of execution (e.g., 'success', 'failed').
            result (Any): Output or error/result object.

        Returns:
            dict: {
                "success": True,
                "message": "Recipe execution log recorded"
            }
            or
            {
                "success": False,
                "error": "failure reason"
            }

        Constraints:
            - recipe_id must exist in the system.
            - execution_id must be unique in execution_logs.
        """
        if execution_id in self.execution_logs:
            return { "success": False, "error": "Duplicate execution_id." }

        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe does not exist." }

        log_entry = {
            "execution_id": execution_id,
            "recipe_id": recipe_id,
            "executed_at": executed_at,
            "status": status,
            "result": result,
        }

        self.execution_logs[execution_id] = log_entry

        return { "success": True, "message": "Recipe execution log recorded" }

    def update_user_authentication_token(self, user_id: str, service_id: str, new_token: str) -> dict:
        """
        Update (or set) the authentication token for a specific user and connected service.

        Args:
            user_id (str): The user's unique identifier.
            service_id (str): The unique identifier for the service.
            new_token (str): The new authentication token.

        Returns:
            dict: {
                "success": True,
                "message": f"Authentication token updated for user {user_id} and service {service_id}"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User and service must exist.
            - Service must be connected to the user (in user['connected_services']).
            - Platform must keep the authentication token up-to-date for each such link.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        service = self.services.get(service_id)
        if service is None:
            return { "success": False, "error": "Service not found" }
        if service_id not in user.get('connected_services', []):
            return { "success": False, "error": "Service not connected for this user" }
        # Update the token
        user["authentication_tokens"][service_id] = new_token
        return {
            "success": True,
            "message": f"Authentication token updated for user {user_id} and service {service_id}"
        }

    def add_trigger_to_service(
        self,
        service_id: str,
        trigger_id: str,
        event_type: str,
        configuration: dict
    ) -> dict:
        """
        Register a new trigger under a service (admin/developer operation).

        Args:
            service_id (str): ID of the service to which the trigger will be added.
            trigger_id (str): Unique trigger ID for the new trigger.
            event_type (str): Type of event this trigger represents.
            configuration (dict): Trigger configuration parameters.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Trigger registered under service." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - service_id must exist in self.services.
            - trigger_id must not already exist in self.triggers (must be unique).
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service does not exist." }

        if trigger_id in self.triggers:
            return { "success": False, "error": "Trigger ID already exists." }

        # Add the new trigger
        self.triggers[trigger_id] = {
            "trigger_id": trigger_id,
            "service_id": service_id,
            "event_type": event_type,
            "configuration": configuration
        }

        return { "success": True, "message": "Trigger registered under service." }

    def add_action_to_service(
        self, 
        service_id: str, 
        action_id: str, 
        action_type: str, 
        configuration: dict
    ) -> dict:
        """
        Register a new action to a specified service (admin/developer operation).

        Args:
            service_id (str): The unique ID of the service to attach the action to.
            action_id (str): Unique identifier for the action.
            action_type (str): Type/name of the action; describes what it does.
            configuration (dict): Configuration data (parameters, templates, etc) for the action.

        Returns:
            dict: 
              On success:
                { "success": True, "message": "Action <action_id> added to service <service_id>" }
              On failure:
                { "success": False, "error": str }
    
        Constraints:
            - The service must exist.
            - The action_id must not already exist.
            - Action is attached to the given service_id and registered globally in platform.actions.
        """
        # Service existence check
        if service_id not in self.services:
            return {"success": False, "error": f"Service {service_id} does not exist"}

        # Duplicate action_id check
        if action_id in self.actions:
            return {"success": False, "error": f"Action ID {action_id} already exists"}

        # Minimal required fields check (these should normally be present given the signature)
        if not action_type or not isinstance(configuration, dict):
            return {"success": False, "error": "Invalid action_type or configuration"}

        # Register the new Action
        new_action = {
            "action_id": action_id,
            "service_id": service_id,
            "action_type": action_type,
            "configuration": configuration
        }
        self.actions[action_id] = new_action

        return {
            "success": True,
            "message": f"Action {action_id} added to service {service_id}"
        }

    def edit_trigger(self, trigger_id: str, service_id: str = None, event_type: str = None, configuration: dict = None) -> dict:
        """
        Modify configuration or meta info about a trigger.

        Args:
            trigger_id (str): The ID of the trigger to edit.
            service_id (str, optional): New service_id to associate with the trigger.
            event_type (str, optional): New event_type for the trigger.
            configuration (dict, optional): New configuration dictionary for the trigger.

        Returns:
            dict: On success: { "success": True, "message": "Trigger updated" }
                  On failure: { "success": False, "error": "reason" }

        Constraints:
            - trigger_id must correspond to an existing trigger.
            - If service_id is supplied, it must exist in self.services.
            - If configuration is supplied, it must be a dictionary.
        """
        # Check the trigger exists
        if trigger_id not in self.triggers:
            return { "success": False, "error": "Trigger does not exist" }

        # Check if service_id is provided, and if so, that it exists
        if service_id is not None and service_id not in self.services:
            return { "success": False, "error": "service_id does not exist" }

        # Check if configuration is provided, and is a dict
        if configuration is not None and not isinstance(configuration, dict):
            return { "success": False, "error": "configuration must be a dictionary" }

        trigger = self.triggers[trigger_id]

        if service_id is not None:
            trigger["service_id"] = service_id
        if event_type is not None:
            trigger["event_type"] = event_type
        if configuration is not None:
            trigger["configuration"] = configuration

        # Save the updated trigger
        self.triggers[trigger_id] = trigger

        return { "success": True, "message": "Trigger updated" }

    def edit_action(
        self, 
        action_id: str, 
        configuration: Dict[str, Any] = None, 
        action_type: str = None
    ) -> dict:
        """
        Modify configuration and/or meta info (e.g., action_type) of an existing action.

        Args:
            action_id (str): The ID of the action to edit.
            configuration (dict, optional): New configuration dictionary for the action.
            action_type (str, optional): New action_type for the action.

        Returns:
            dict: {
                "success": True,
                "message": "Action <action_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - action_id must exist.
            - configuration must be a dictionary (if provided).
            - At least one update must be provided.
        """
        if action_id not in self.actions:
            return {"success": False, "error": f"Action '{action_id}' does not exist."}

        if configuration is None and action_type is None:
            return {
                "success": False,
                "error": "No updates provided. Specify at least configuration or action_type."
            }

        updated = False
        # Only update provided fields
        if configuration is not None:
            if not isinstance(configuration, dict):
                return {
                    "success": False,
                    "error": "Configuration must be a dict."
                }
            self.actions[action_id]["configuration"] = configuration
            updated = True
        if action_type is not None:
            if not isinstance(action_type, str):
                return {
                    "success": False,
                    "error": "action_type must be a string."
                }
            self.actions[action_id]["action_type"] = action_type
            updated = True

        if updated:
            return {
                "success": True,
                "message": f"Action '{action_id}' updated successfully."
            }
        else:
            # This case is only reached if weird input disables the 'updated' flag
            return {
                "success": False,
                "error": "No valid updates applied to the action."
            }


class ConsumerAutomationPlatform(BaseEnv):
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

    def list_user_connected_services(self, **kwargs):
        return self._call_inner_tool('list_user_connected_services', kwargs)

    def get_user_authentication_token(self, **kwargs):
        return self._call_inner_tool('get_user_authentication_token', kwargs)

    def list_all_services(self, **kwargs):
        return self._call_inner_tool('list_all_services', kwargs)

    def get_service_by_id(self, **kwargs):
        return self._call_inner_tool('get_service_by_id', kwargs)

    def list_service_triggers(self, **kwargs):
        return self._call_inner_tool('list_service_triggers', kwargs)

    def list_service_actions(self, **kwargs):
        return self._call_inner_tool('list_service_actions', kwargs)

    def get_trigger_by_id(self, **kwargs):
        return self._call_inner_tool('get_trigger_by_id', kwargs)

    def get_action_by_id(self, **kwargs):
        return self._call_inner_tool('get_action_by_id', kwargs)

    def list_user_recipes(self, **kwargs):
        return self._call_inner_tool('list_user_recipes', kwargs)

    def get_recipe_by_id(self, **kwargs):
        return self._call_inner_tool('get_recipe_by_id', kwargs)

    def list_recipe_execution_logs(self, **kwargs):
        return self._call_inner_tool('list_recipe_execution_logs', kwargs)

    def get_execution_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_execution_log_by_id', kwargs)

    def check_recipe_enabled_status(self, **kwargs):
        return self._call_inner_tool('check_recipe_enabled_status', kwargs)

    def check_user_service_authorization(self, **kwargs):
        return self._call_inner_tool('check_user_service_authorization', kwargs)

    def connect_service_to_user(self, **kwargs):
        return self._call_inner_tool('connect_service_to_user', kwargs)

    def disconnect_service_from_user(self, **kwargs):
        return self._call_inner_tool('disconnect_service_from_user', kwargs)

    def create_recipe(self, **kwargs):
        return self._call_inner_tool('create_recipe', kwargs)

    def edit_recipe(self, **kwargs):
        return self._call_inner_tool('edit_recipe', kwargs)

    def delete_recipe(self, **kwargs):
        return self._call_inner_tool('delete_recipe', kwargs)

    def enable_recipe(self, **kwargs):
        return self._call_inner_tool('enable_recipe', kwargs)

    def disable_recipe(self, **kwargs):
        return self._call_inner_tool('disable_recipe', kwargs)

    def force_execute_recipe(self, **kwargs):
        return self._call_inner_tool('force_execute_recipe', kwargs)

    def log_recipe_execution(self, **kwargs):
        return self._call_inner_tool('log_recipe_execution', kwargs)

    def update_user_authentication_token(self, **kwargs):
        return self._call_inner_tool('update_user_authentication_token', kwargs)

    def add_trigger_to_service(self, **kwargs):
        return self._call_inner_tool('add_trigger_to_service', kwargs)

    def add_action_to_service(self, **kwargs):
        return self._call_inner_tool('add_action_to_service', kwargs)

    def edit_trigger(self, **kwargs):
        return self._call_inner_tool('edit_trigger', kwargs)

    def edit_action(self, **kwargs):
        return self._call_inner_tool('edit_action', kwargs)
