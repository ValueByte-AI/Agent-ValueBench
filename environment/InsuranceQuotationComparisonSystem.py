# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    selected_plan_ids: List[str]
    comparison_history: List[List[str]]  # Each comparison is a list of plan_ids

class InsurancePlanInfo(TypedDict):
    plan_id: str
    provider_id: str
    plan_name: str
    features: Any  # Could be dict or str describing plan characteristics
    coverage_details: Any  # Could be dict or str
    premium_amount: float
    term_length: int
    eligibility_criteria: Any  # Could be dict or str

class ProviderInfo(TypedDict):
    provider_id: str
    provider_name: str
    contact_info: str
    rating: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing insurance quotations, plans, and user plan comparison/selection.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Insurance Plans: {plan_id: InsurancePlanInfo}
        self.insurance_plans: Dict[str, InsurancePlanInfo] = {}

        # Providers: {provider_id: ProviderInfo}
        self.providers: Dict[str, ProviderInfo] = {}

        # Constraints:
        # - Users can only compare plans present in their selected_plan_ids.
        # - Each insurance plan must be associated with a valid provider.
        # - Insurance plans compared must exist and be currently available (not discontinued).

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details, including selected plans and comparison history, by user ID.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": UserInfo
                }
                On failure: {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if user is not None:
            return { "success": True, "data": user }
        else:
            return { "success": False, "error": "User not found" }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all users in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of all users' information (may be empty)
            }

        Constraints:
            - None; this operation simply lists all users present in the system.
        """
        users_list = list(self.users.values())
        return {
            "success": True,
            "data": users_list
        }

    def get_selected_plan_ids_for_user(self, user_id: str) -> dict:
        """
        Retrieve the list of currently selected insurance plan IDs for a given user.

        Args:
            user_id (str): The user's unique identifier (_id)

        Returns:
            dict: {
                "success": True,
                "data": List[str]     # The list of selected insurance plan IDs (possibly empty)
            }
            or
            {
                "success": False,
                "error": str          # Error description if user not found
            }

        Constraints:
            - The user_id must exist in the system.
            - Returns an empty list if the user has no selected plans.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user.get("selected_plan_ids", [])}

    def get_comparison_history_for_user(self, user_id: str) -> dict:
        """
        Retrieve the full comparison history for a given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[List[str]] }
                    "data" is a list of each user's past plan comparison, where each element is a list of plan_ids.
                - On failure: { "success": False, "error": str }
                    The error describes why the operation failed (e.g., user not found).

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user.get("comparison_history", []) }

    def get_insurance_plan_by_id(self, plan_id: str) -> dict:
        """
        Retrieve all details for a particular insurance plan by its plan_id.

        Args:
            plan_id (str): The unique identifier of the insurance plan.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": InsurancePlanInfo  # All information about the plan
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., "Insurance plan not found"
                    }

        Constraints:
            - The plan_id must exist in the system.
        """
        plan_info = self.insurance_plans.get(plan_id)
        if plan_info is None:
            return { "success": False, "error": "Insurance plan not found" }
        return { "success": True, "data": plan_info }

    def get_multiple_insurance_plans_by_ids(self, plan_ids: List[str]) -> dict:
        """
        Retrieve full details for multiple insurance plans by a list of plan_ids.

        Args:
            plan_ids (List[str]): List of plan_id strings to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[InsurancePlanInfo]  # Only plans that exist, have valid provider, and are available.
            }

        Constraints:
            - Only return plans that exist in the system and are associated with a valid provider.
            - Discontinued plans are assumed not to be present in self.insurance_plans.
            - If no plan_ids are found, return an empty list.
        """
        found_plans = []
        for plan_id in plan_ids:
            plan = self.insurance_plans.get(plan_id)
            if plan:
                # Check provider association constraint
                provider_id = plan.get("provider_id")
                if provider_id in self.providers and not plan.get("is_discontinued", False):
                    found_plans.append(plan)
                # If provider is missing, skip this plan
        return {
            "success": True,
            "data": found_plans
        }

    def check_plan_availability(self, plan_id: str) -> dict:
        """
        Check if a given insurance plan exists and is currently available (not discontinued).

        Args:
            plan_id (str): The unique identifier of the insurance plan.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if plan exists and is available, otherwise False
                }
            No error is produced; operation is always successful.

        Constraints:
            - A plan is available if:
                - It exists in self.insurance_plans
                - It is not marked as discontinued (expects 'is_discontinued' on the plan info; if missing, plan is considered available)
        """
        plan = self.insurance_plans.get(plan_id)
        if not plan:
            return { "success": True, "data": False }
        # Check for discontinuation
        if "is_discontinued" in plan and plan["is_discontinued"]:
            return { "success": True, "data": False }
        return { "success": True, "data": True }

    def get_provider_by_id(self, provider_id: str) -> dict:
        """
        Retrieve provider information for a given provider_id.

        Args:
            provider_id (str): The unique identifier of the provider.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ProviderInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Provider not found"
                    }
        Constraints:
            - The provider_id must exist in the system.
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return { "success": False, "error": "Provider not found" }
        return { "success": True, "data": provider }

    def get_providers_for_plans(self, plan_ids: list) -> dict:
        """
        Retrieve provider information for a group of plans.

        Args:
            plan_ids (List[str]): List of insurance plan IDs to retrieve provider info for.

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo],  # Unique providers offering the plans,
            }
            or
            {
                "success": False,
                "error": str  # if input is not a list
            }

        Constraints:
            - Only plans that exist and whose providers exist are considered.
            - Each provider appears at most once in the result.
            - If no plans or valid providers found, returns empty list for "data".
        """
        if not isinstance(plan_ids, list):
            return {"success": False, "error": "Input must be a list of plan IDs."}

        provider_ids = set()
        for plan_id in plan_ids:
            plan = self.insurance_plans.get(plan_id)
            if plan:
                provider_id = plan.get('provider_id')
                if provider_id and provider_id in self.providers:
                    provider_ids.add(provider_id)

        providers_result = [self.providers[pid] for pid in provider_ids]

        return {"success": True, "data": providers_result}

    def validate_plan_provider_association(self, plan_id: str) -> dict:
        """
        Verify that the provider_id associated with the specified insurance plan exists
        in the system's list of providers.

        Args:
            plan_id (str): The ID of the insurance plan to validate.

        Returns:
            dict: 
                - If the plan does not exist: {"success": False, "error": "Plan does not exist" }
                - If the plan exists, and provider is found: {"success": True, "data": True }
                - If the plan exists, but provider does not exist: {"success": True, "data": False }

        Constraints:
            - Each insurance plan must be associated with a valid provider.
        """
        plan = self.insurance_plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "Plan does not exist"}

        provider_id = plan["provider_id"]
        exists = provider_id in self.providers

        return {"success": True, "data": exists}

    def add_to_selected_plan_ids(self, user_id: str, plan_id: str) -> dict:
        """
        Add an insurance plan to a user's selected_plan_ids list.

        Args:
            user_id (str): User identifier.
            plan_id (str): Insurance plan identifier.

        Returns:
            dict:
                On success: { "success": True, "message": "Plan added to user's selected plans." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - Plan must exist in the system and be available.
            - Plan must be associated with a valid provider.
            - Plan must not already be selected by the user.
        """

        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        plan = self.insurance_plans.get(plan_id)
        if not plan:
            return { "success": False, "error": "Insurance plan does not exist." }

        provider_id = plan.get("provider_id")
        if provider_id not in self.providers:
            return { "success": False, "error": "Plan's provider does not exist." }
        if plan.get("is_discontinued", False):
            return { "success": False, "error": "Insurance plan is not currently available." }

        if plan_id in user["selected_plan_ids"]:
            return { "success": False, "error": "Plan already in user's selected plans." }

        user["selected_plan_ids"].append(plan_id)
        return { "success": True, "message": "Plan added to user's selected plans." }

    def remove_from_selected_plan_ids(self, user_id: str, plan_id: str) -> dict:
        """
        Remove an insurance plan from a user's selected_plan_ids.

        Args:
            user_id (str): The unique identifier of the user.
            plan_id (str): The unique identifier of the insurance plan to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Plan <plan_id> removed from user <user_id>'s selections."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User must exist.
            - plan_id must be in the user's selected_plan_ids.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": f"User {user_id} does not exist." }
    
        if plan_id not in user["selected_plan_ids"]:
            return { "success": False, "error": f"Plan {plan_id} is not in user {user_id}'s selections." }
    
        # Remove the plan_id
        user["selected_plan_ids"].remove(plan_id)

        return { "success": True, "message": f"Plan {plan_id} removed from user {user_id}'s selections." }

    def store_comparison_in_history(self, user_id: str, plan_ids: list) -> dict:
        """
        Save a set of compared plan IDs as a new entry in the user’s comparison_history.

        Args:
            user_id (str): The unique ID of the user making the comparison.
            plan_ids (List[str]): List of insurance plan IDs being compared.

        Returns:
            dict: {
                "success": True,
                "message": "Comparison stored in history."
            }
            or
            {
                "success": False,
                "error": <error reason string>
            }

        Constraints & checks:
            - User must exist.
            - All plan_ids must be in user's selected_plan_ids.
            - All plan_ids must exist in self.insurance_plans (available).
            - Plan IDs should be a non-empty list and all unique.
        """
        # Validate user
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Validate plan_ids is a non-empty list of strings and unique
        if not isinstance(plan_ids, list) or len(plan_ids) == 0 or not all(isinstance(pid, str) for pid in plan_ids):
            return {"success": False, "error": "plan_ids must be a non-empty list of plan ID strings"}
        if len(plan_ids) != len(set(plan_ids)):
            return {"success": False, "error": "plan_ids must be unique"}

        # Validate all plan_ids are in user's selected_plan_ids
        not_selected = [pid for pid in plan_ids if pid not in user["selected_plan_ids"]]
        if not_selected:
            return {"success": False, "error": f"Plans not selected by user: {not_selected}"}

        # Validate plans exist and are available
        not_found = [pid for pid in plan_ids if pid not in self.insurance_plans]
        if not_found:
            return {"success": False, "error": f"Plans not found or not available: {not_found}"}
        unavailable = [pid for pid in plan_ids if self.insurance_plans[pid].get("is_discontinued", False)]
        if unavailable:
            return {"success": False, "error": f"Plans not found or not available: {unavailable}"}

        # Append to comparison_history
        user["comparison_history"].append(plan_ids[:])  # Copy list to avoid mutation from caller
        return {"success": True, "message": "Comparison stored in history."}

    def create_new_user(self, _id: str, name: str) -> dict:
        """
        Add a new user to the system.

        Args:
            _id (str): Unique identifier for the user.
            name (str): Name of the user.

        Returns:
            dict: {
                "success": True,
                "message": "User <_id> created successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. duplicate _id
            }

        Constraints:
            - The _id must be unique in the system.
        """
        if not _id or not isinstance(_id, str):
            return {"success": False, "error": "Invalid or missing user _id."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing user name."}
        if _id in self.users:
            return {"success": False, "error": "User with this _id already exists."}
    
        self.users[_id] = {
            "_id": _id,
            "name": name,
            "selected_plan_ids": [],
            "comparison_history": []
        }
        return {"success": True, "message": f"User {_id} created successfully."}

    def add_new_insurance_plan(
        self,
        plan_id: str,
        provider_id: str,
        plan_name: str,
        features: Any,
        coverage_details: Any,
        premium_amount: float,
        term_length: int,
        eligibility_criteria: Any
    ) -> dict:
        """
        Add a new insurance plan to the system.

        Args:
            plan_id (str): Unique identifier for the new insurance plan.
            provider_id (str): Provider's unique identifier. Must exist in providers.
            plan_name (str): Human-readable plan name.
            features (Any): Features or characteristics of the plan.
            coverage_details (Any): Description/details of coverage.
            premium_amount (float): Premium amount for the plan.
            term_length (int): Term length in months/years (as defined by the system).
            eligibility_criteria (Any): Eligibility criteria for the plan.

        Returns:
            dict: {
                "success": True,
                "message": "Insurance plan <plan_id> added."
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - plan_id must be unique.
            - provider_id must reference a valid provider.
        """

        # Check that the plan_id is unique
        if plan_id in self.insurance_plans:
            return { "success": False, "error": "Plan ID already exists" }

        # Ensure provider_id is valid
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider ID does not exist" }

        # Create the plan
        plan_info: InsurancePlanInfo = {
            "plan_id": plan_id,
            "provider_id": provider_id,
            "plan_name": plan_name,
            "features": features,
            "coverage_details": coverage_details,
            "premium_amount": premium_amount,
            "term_length": term_length,
            "eligibility_criteria": eligibility_criteria
        }

        # Add to system
        self.insurance_plans[plan_id] = plan_info

        return { "success": True, "message": f"Insurance plan {plan_id} added." }

    def discontinue_insurance_plan(self, plan_id: str) -> dict:
        """
        Mark an insurance plan as discontinued/unavailable in the system.

        Args:
            plan_id (str): The unique identifier of the insurance plan to discontinue.

        Returns:
            dict: {
                "success": True,
                "message": "Plan <plan_id> marked as discontinued."
            }
            OR
            {
                "success": False,
                "error": "Insurance plan does not exist."
            }

        Constraints:
            - The insurance plan must exist in the system.
            - If the plan is already discontinued, this is treated as a no-op.
            - The function adds or updates an 'is_discontinued' flag in the plan info.
        """
        plan = self.insurance_plans.get(plan_id)
        if not plan:
            return { "success": False, "error": "Insurance plan does not exist." }
        # Update or add the discontinued flag
        if plan.get("is_discontinued", False):
            # Already discontinued
            return { "success": True, "message": f"Plan {plan_id} was already discontinued." }
        plan["is_discontinued"] = True
        self.insurance_plans[plan_id] = plan
        return { "success": True, "message": f"Plan {plan_id} marked as discontinued." }

    def update_provider_info(
        self,
        provider_id: str,
        provider_name: str = None,
        contact_info: str = None,
        rating: float = None
    ) -> dict:
        """
        Update an existing provider's information in the system.

        Args:
            provider_id (str): The unique ID of the provider to update.
            provider_name (str, optional): New name for the provider.
            contact_info (str, optional): New contact information.
            rating (float, optional): New provider rating.

        Returns:
            dict: {
                "success": True,
                "message": "Provider info updated successfully."
            }
            or
            {
                "success": False,
                "error": "<description of problem>"
            }

        Constraints:
            - The provider must exist in the system.
            - At least one field to update must be provided.
            - If rating is provided, it must be a float (or can be cast to float).
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return { "success": False, "error": "Provider not found." }

        # Check at least one update parameter is provided
        if provider_name is None and contact_info is None and rating is None:
            return { "success": False, "error": "No update fields provided." }

        if provider_name is not None:
            provider["provider_name"] = provider_name
        if contact_info is not None:
            provider["contact_info"] = contact_info
        if rating is not None:
            try:
                provider["rating"] = float(rating)
            except Exception:
                return { "success": False, "error": "Invalid rating value." }

        self.providers[provider_id] = provider
        return { "success": True, "message": "Provider info updated successfully." }

    def add_new_provider(
        self,
        provider_id: str,
        provider_name: str,
        contact_info: str,
        rating: float
    ) -> dict:
        """
        Add a new provider to the system.

        Args:
            provider_id (str): Unique identifier for the provider.
            provider_name (str): Name of the provider.
            contact_info (str): Provider's contact information.
            rating (float): Provider's rating.

        Returns:
            dict: {
                "success": True,
                "message": "Provider added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - provider_id must be unique (not already in the system).
            - All fields must be supplied and of appropriate type.
        """
        # Check for uniqueness
        if provider_id in self.providers:
            return {"success": False, "error": "Provider ID already exists"}
    
        # Basic validation
        if not isinstance(provider_id, str) or not provider_id.strip():
            return {"success": False, "error": "Provider ID must be a non-empty string"}
        if not isinstance(provider_name, str) or not provider_name.strip():
            return {"success": False, "error": "Provider name must be a non-empty string"}
        if not isinstance(contact_info, str) or not contact_info.strip():
            return {"success": False, "error": "Contact info must be a non-empty string"}
        try:
            rating_val = float(rating)
        except Exception:
            return {"success": False, "error": "Rating must be a valid float value"}
    
        # Construct ProviderInfo
        provider_info: ProviderInfo = {
            "provider_id": provider_id,
            "provider_name": provider_name,
            "contact_info": contact_info,
            "rating": rating_val
        }
        self.providers[provider_id] = provider_info

        return {"success": True, "message": "Provider added successfully"}


class InsuranceQuotationComparisonSystem(BaseEnv):
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

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_selected_plan_ids_for_user(self, **kwargs):
        return self._call_inner_tool('get_selected_plan_ids_for_user', kwargs)

    def get_comparison_history_for_user(self, **kwargs):
        return self._call_inner_tool('get_comparison_history_for_user', kwargs)

    def get_insurance_plan_by_id(self, **kwargs):
        return self._call_inner_tool('get_insurance_plan_by_id', kwargs)

    def get_multiple_insurance_plans_by_ids(self, **kwargs):
        return self._call_inner_tool('get_multiple_insurance_plans_by_ids', kwargs)

    def check_plan_availability(self, **kwargs):
        return self._call_inner_tool('check_plan_availability', kwargs)

    def get_provider_by_id(self, **kwargs):
        return self._call_inner_tool('get_provider_by_id', kwargs)

    def get_providers_for_plans(self, **kwargs):
        return self._call_inner_tool('get_providers_for_plans', kwargs)

    def validate_plan_provider_association(self, **kwargs):
        return self._call_inner_tool('validate_plan_provider_association', kwargs)

    def add_to_selected_plan_ids(self, **kwargs):
        return self._call_inner_tool('add_to_selected_plan_ids', kwargs)

    def remove_from_selected_plan_ids(self, **kwargs):
        return self._call_inner_tool('remove_from_selected_plan_ids', kwargs)

    def store_comparison_in_history(self, **kwargs):
        return self._call_inner_tool('store_comparison_in_history', kwargs)

    def create_new_user(self, **kwargs):
        return self._call_inner_tool('create_new_user', kwargs)

    def add_new_insurance_plan(self, **kwargs):
        return self._call_inner_tool('add_new_insurance_plan', kwargs)

    def discontinue_insurance_plan(self, **kwargs):
        return self._call_inner_tool('discontinue_insurance_plan', kwargs)

    def update_provider_info(self, **kwargs):
        return self._call_inner_tool('update_provider_info', kwargs)

    def add_new_provider(self, **kwargs):
        return self._call_inner_tool('add_new_provider', kwargs)
