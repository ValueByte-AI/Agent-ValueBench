# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class HealthInsurancePlanInfo(TypedDict):
    plan_id: str
    provider_id: str
    name: str
    description: str
    coverage_details: str
    price: float
    eligibility_criteria: str
    availability_status: str  # mapping from 'availability_sta'

class ProviderInfo(TypedDict):
    provider_id: str
    name: str
    contact_info: str
    accreditation_status: str  # mapping from 'accreditation_sta'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State representation for the Health Insurance Marketplace system.
        """

        # Health Insurance Plans: {plan_id: HealthInsurancePlanInfo}
        # Maps plan_id to details about insurance plans.
        self.plans: Dict[str, HealthInsurancePlanInfo] = {}

        # Providers: {provider_id: ProviderInfo}
        # Maps provider_id to details about each provider.
        self.providers: Dict[str, ProviderInfo] = {}

        # Constraints:
        # - Only plans with availability_status = "available" should be presented to users.
        # - Each HealthInsurancePlan must reference a valid Provider.
        # - Eligibility criteria must be satisfied before enrollment (used in other tasks).
        # - Prices must be non-negative.

    def list_all_plans(self) -> dict:
        """
        Retrieve the complete list of health insurance plans in the system,
        regardless of their availability status.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[HealthInsurancePlanInfo]  # May be empty if no plans are present
            }
        """
        plan_list = list(self.plans.values())
        return {"success": True, "data": plan_list}

    def get_plan_by_id(self, plan_id: str) -> dict:
        """
        Retrieve full details for a specific health insurance plan by its plan_id.

        Args:
            plan_id (str): The unique identifier for the health insurance plan.

        Returns:
            dict: 
              {
                "success": True,
                "data": HealthInsurancePlanInfo  # Dict of the plan details
              }
            or
              {
                "success": False,
                "error": str  # "Plan not found"
              }

        Constraints:
            - The plan_id must exist in the marketplace system.
            - No restriction on availability_status or eligibility for direct lookup.
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "Plan not found"}
        return {"success": True, "data": plan}

    def list_available_plans(self) -> dict:
        """
        List all health insurance plans where `availability_status` is "available".

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[HealthInsurancePlanInfo],  # List (possibly empty) of available plans
            }

        Constraints:
            - Only plans with availability_status == "available" are included.
        """
        available_plans = [
            plan_info for plan_info in self.plans.values()
            if plan_info.get("availability_status") == "available"
        ]
        return { "success": True, "data": available_plans }

    def filter_plans_by_price_range(self, min_price: float, max_price: float) -> dict:
        """
        Retrieve all available health insurance plans within the given price range [min_price, max_price], inclusive.

        Args:
            min_price (float): Minimum plan price (inclusive). Must be non-negative and <= max_price.
            max_price (float): Maximum plan price (inclusive). Must be non-negative and >= min_price.

        Returns:
            dict:
                - success: True and data: List[HealthInsurancePlanInfo] (plans in price range, may be empty)
                - success: False and error: str (if parameters invalid)

        Constraints:
            - Only plans with availability_status = "available" are considered.
            - Both min_price and max_price must be >= 0 and min_price <= max_price.
        """
        if min_price < 0 or max_price < 0:
            return {"success": False, "error": "Price range must be non-negative."}
        if min_price > max_price:
            return {"success": False, "error": "min_price must be less than or equal to max_price."}

        result = [
            plan for plan in self.plans.values()
            if plan["availability_status"] == "available"
               and min_price <= plan["price"] <= max_price
        ]
        return {"success": True, "data": result}

    def sort_plans_by_price(self, plan_ids: list, ascending: bool = True) -> dict:
        """
        Sort a given list of health insurance plans by their price.

        Args:
            plan_ids (list of str): List of plan_id values to consider.
            ascending (bool, optional): Sort order; True for ascending, False for descending. Default is True.

        Returns:
            dict:
              - On success:
                    {
                        "success": True,
                        "data": List[HealthInsurancePlanInfo]  # Sorted list of available HealthInsurancePlanInfo objects
                    }
              - On failure:
                    { "success": False, "error": str }

        Constraints:
          - Only plans with availability_status == "available" are included in the output.
          - Only valid plan_ids (existing in self.plans) are processed.
          - Prices are always non-negative.
        """
        valid_available_plans = []
        for pid in plan_ids:
            plan = self.plans.get(pid)
            if plan and plan["availability_status"] == "available":
                valid_available_plans.append(plan)

        if len(plan_ids) > 0 and len(valid_available_plans) == 0:
            return {
                "success": False,
                "error": "No valid and available plans found for the provided plan_ids."
            }

        sorted_plans = sorted(
            valid_available_plans,
            key=lambda x: x["price"],
            reverse=not ascending
        )

        return {
            "success": True,
            "data": sorted_plans
        }

    def filter_plans_by_eligibility(self, eligibility_criteria: str) -> dict:
        """
        List all available health insurance plans that match the specified eligibility criteria.

        Args:
            eligibility_criteria (str): The eligibility criteria to match plans against.

        Returns:
            dict: {
                "success": True,
                "data": List[HealthInsurancePlanInfo]  # List of matching plan dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. invalid/no criteria given
            }

        Constraints:
            - Only plans with availability_status == "available" are included in the results.
            - eligibility_criteria must match exactly (case-sensitive/string comparison).
        """
        if not eligibility_criteria or not isinstance(eligibility_criteria, str):
            return {"success": False, "error": "Invalid eligibility criteria input."}

        results = [
            plan for plan in self.plans.values()
            if plan["availability_status"] == "available" and plan["eligibility_criteria"] == eligibility_criteria
        ]

        return {"success": True, "data": results}

    def get_provider_by_id(self, provider_id: str) -> dict:
        """
        Retrieve details of a provider by their provider_id.

        Args:
            provider_id (str): Unique identifier for the provider.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ProviderInfo  # Provider's metadata
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Provider not found"
                    }

        Constraints:
            - provider_id must exist in the system.
        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider not found" }

        provider_info = self.providers[provider_id]
        return { "success": True, "data": provider_info }

    def list_all_providers(self) -> dict:
        """
        Retrieve the list of all providers in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo]  # May be empty if there are no providers
            }

        Constraints:
            - No special constraints. Simple comprehensive query of all provider records.
        """
        return {
            "success": True,
            "data": list(self.providers.values())
        }

    def filter_plans_by_provider(self, provider_id: str) -> dict:
        """
        Return all available health insurance plans offered by a specific provider.

        Args:
            provider_id (str): The provider's unique identifier.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[HealthInsurancePlanInfo]  # List of plan details (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Provider does not exist"
                    }

        Constraints:
            - Only plans with availability_status = "available" are included.
            - The provider_id must exist in the system.
        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        filtered = [
            plan_info for plan_info in self.plans.values()
            if plan_info["provider_id"] == provider_id and plan_info["availability_status"] == "available"
        ]

        return { "success": True, "data": filtered }

    def validate_plan_provider_reference(self) -> dict:
        """
        Check whether every health insurance plan references a valid provider.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict describes a plan with invalid provider_id:
                    # { "plan_id": str, "provider_id": str }
                    # List is empty if all plan provider references are valid.
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Each plan's provider_id must exist in self.providers.
        """
        invalid_refs = []
        for plan in self.plans.values():
            if plan["provider_id"] not in self.providers:
                invalid_refs.append({
                    "plan_id": plan["plan_id"],
                    "provider_id": plan["provider_id"],
                })
        return {"success": True, "data": invalid_refs}

    def add_plan(
        self,
        plan_id: str,
        provider_id: str,
        name: str,
        description: str,
        coverage_details: str,
        price: float,
        eligibility_criteria: str,
        availability_status: str
    ) -> dict:
        """
        Add a new health insurance plan to the system, enforcing the following constraints:
          - plan_id must be unique.
          - provider_id must exist in the system.
          - price must be non-negative.

        Args:
            plan_id (str): Unique identifier for the plan.
            provider_id (str): Provider's unique ID (must exist).
            name (str): Plan name.
            description (str): Description of the plan.
            coverage_details (str): Coverage details.
            price (float): Plan price (must be >= 0).
            eligibility_criteria (str): Eligibility requirements.
            availability_status (str): Plan availability status.

        Returns:
            dict: { "success": True, "message": "Plan <plan_id> added successfully." }
                  or
                  { "success": False, "error": "<reason>" }
        """
        # Check uniqueness of plan_id
        if plan_id in self.plans:
            return { "success": False, "error": f"Plan with id '{plan_id}' already exists." }

        # Check provider_id validity
        if provider_id not in self.providers:
            return { "success": False, "error": f"Provider with id '{provider_id}' does not exist." }

        # Check price constraint
        if not isinstance(price, (int, float)) or price < 0:
            return { "success": False, "error": "Plan price must be a non-negative number." }

        plan_info = {
            "plan_id": plan_id,
            "provider_id": provider_id,
            "name": name,
            "description": description,
            "coverage_details": coverage_details,
            "price": float(price),
            "eligibility_criteria": eligibility_criteria,
            "availability_status": availability_status
        }
        self.plans[plan_id] = plan_info

        return { "success": True, "message": f"Plan '{plan_id}' added successfully." }

    def update_plan_details(self, plan_id: str, updates: dict) -> dict:
        """
        Modify an existing health insurance plan's details.

        Args:
            plan_id (str): The ID of the plan to update.
            updates (dict): Dictionary of fields and new values.

        Returns:
            dict: {
                "success": True,
                "message": "Plan details updated."
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - Only allow modification of supported fields: name, description, coverage_details,
              price, eligibility_criteria, availability_status, provider_id.
            - If updating 'price', the value must be non-negative.
            - If updating 'provider_id', it must reference an existing provider.
            - Plan must exist.
        """
        allowed_fields = {
            "name", "description", "coverage_details", "price",
            "eligibility_criteria", "availability_status", "provider_id"
        }

        if plan_id not in self.plans:
            return { "success": False, "error": "Plan does not exist." }

        plan = self.plans[plan_id]
        for key in updates:
            if key not in allowed_fields:
                return { "success": False, "error": f"Invalid field for update: {key}" }

        # Check constraints on updates
        if "price" in updates:
            try:
                price_value = float(updates["price"])
                if price_value < 0:
                    return { "success": False, "error": "Price must be non-negative." }
            except Exception:
                return { "success": False, "error": "Price must be a number." }

        if "provider_id" in updates:
            if updates["provider_id"] not in self.providers:
                return { "success": False, "error": "Provided provider_id does not exist." }

        # Update allowed fields in plan
        for key, value in updates.items():
            # For price, ensure actual type is float
            if key == "price":
                plan["price"] = float(value)
            else:
                plan[key] = value

        return { "success": True, "message": "Plan details updated." }

    def remove_plan(self, plan_id: str) -> dict:
        """
        Delete a health insurance plan from the system by its plan_id.

        Args:
            plan_id (str): The unique identifier of the plan to remove.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "message": "Plan <plan_id> removed from the system."
                  }
                - On error (e.g., plan does not exist): {
                      "success": False,
                      "error": "Plan does not exist."
                  }

        Constraints:
            - Only existing plans can be removed.
        """
        if plan_id not in self.plans:
            return { "success": False, "error": "Plan does not exist." }

        del self.plans[plan_id]
        return { "success": True, "message": f"Plan {plan_id} removed from the system." }

    def add_provider(
        self,
        provider_id: str,
        name: str,
        contact_info: str,
        accreditation_status: str
    ) -> dict:
        """
        Add a new provider to the system.

        Args:
            provider_id (str): Unique identifier for the provider.
            name (str): Name of the provider.
            contact_info (str): Contact information for the provider.
            accreditation_status (str): Accreditation status for the provider.

        Returns:
            dict: 
                On success: { "success": True, "message": "Provider added successfully." }
                On error: { "success": False, "error": "Provider ID already exists." }

        Constraints:
            - provider_id must be unique in the system.
        """
        if provider_id in self.providers:
            return { "success": False, "error": "Provider ID already exists." }
    
        provider_info = {
            "provider_id": provider_id,
            "name": name,
            "contact_info": contact_info,
            "accreditation_status": accreditation_status
        }

        self.providers[provider_id] = provider_info

        return { "success": True, "message": "Provider added successfully." }

    def update_provider_details(
        self, 
        provider_id: str, 
        name: str = None, 
        contact_info: str = None, 
        accreditation_status: str = None
    ) -> dict:
        """
        Update details of a provider in the marketplace.

        Args:
            provider_id (str): The unique identifier of the provider to update.
            name (str, optional): New provider name.
            contact_info (str, optional): New contact information.
            accreditation_status (str, optional): New accreditation status.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Provider details updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The provider must exist.
            - Only name, contact_info, and accreditation_status may be updated.
        """
        provider = self.providers.get(provider_id)
        if not provider:
            return { "success": False, "error": "Provider not found." }

        updated = False
        if name is not None:
            provider["name"] = name
            updated = True
        if contact_info is not None:
            provider["contact_info"] = contact_info
            updated = True
        if accreditation_status is not None:
            provider["accreditation_status"] = accreditation_status
            updated = True

        if not updated:
            return { "success": True, "message": "No fields updated; nothing changed." }
    
        return { "success": True, "message": "Provider details updated." }

    def remove_provider(self, provider_id: str) -> dict:
        """
        Delete a provider from the system.

        Args:
            provider_id (str): The unique ID for the provider to remove.

        Returns:
            dict: 
                - {"success": True, "message": "Provider <provider_id> removed."}
                - {"success": False, "error": <reason>}
    
        Constraints:
            - If the provider is referenced by any existing HealthInsurancePlans,
              the operation fails and reports the error.
            - Otherwise, removes the provider from the system.

        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist." }
    
        referencing_plans = [
            plan_id for plan_id, plan in self.plans.items()
            if plan["provider_id"] == provider_id
        ]
        if referencing_plans:
            return {
                "success": False,
                "error": f"Provider is referenced by plans: {referencing_plans}. Remove or reassign these plans before deletion."
            }
    
        del self.providers[provider_id]
        return { "success": True, "message": f"Provider {provider_id} removed." }

    def batch_update_availability_status(self, plan_ids: list, new_status: str) -> dict:
        """
        Change the availability status of multiple plans at once.

        Args:
            plan_ids (list of str): List of plan IDs to update.
            new_status (str): The new value for 'availability_status' (e.g., "available", "unavailable").

        Returns:
            dict: {
                "success": True,
                "message": "Availability status updated for N plans: [...]"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - All plan IDs in `plan_ids` must exist.
            - The operation is atomic: if any invalid plan_id, no changes are made.
            - No restrictions are placed on allowed status values unless business rules enforce them.
        """
        if not isinstance(plan_ids, list) or not all(isinstance(pid, str) for pid in plan_ids):
            return {
                "success": False,
                "error": "plan_ids must be a list of strings"
            }
        if not plan_ids:
            return {
                "success": True,
                "message": "No plan_ids provided; no changes made."
            }

        missing_ids = [pid for pid in plan_ids if pid not in self.plans]
        if missing_ids:
            return {
                "success": False,
                "error": f"The following plan_ids do not exist: {missing_ids}"
            }

        # Optionally: Validate status (if only "available"/"unavailable" permitted)
        # allowed_statuses = {"available", "unavailable"}
        # if new_status not in allowed_statuses:
        #     return {
        #         "success": False,
        #         "error": f"Invalid availability_status '{new_status}'. Allowed: {list(allowed_statuses)}"
        #     }

        for pid in plan_ids:
            self.plans[pid]["availability_status"] = new_status

        return {
            "success": True,
            "message": f"Availability status updated to '{new_status}' for plans: {plan_ids}"
        }


class HealthInsuranceMarketplaceSystem(BaseEnv):
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

    def list_all_plans(self, **kwargs):
        return self._call_inner_tool('list_all_plans', kwargs)

    def get_plan_by_id(self, **kwargs):
        return self._call_inner_tool('get_plan_by_id', kwargs)

    def list_available_plans(self, **kwargs):
        return self._call_inner_tool('list_available_plans', kwargs)

    def filter_plans_by_price_range(self, **kwargs):
        return self._call_inner_tool('filter_plans_by_price_range', kwargs)

    def sort_plans_by_price(self, **kwargs):
        return self._call_inner_tool('sort_plans_by_price', kwargs)

    def filter_plans_by_eligibility(self, **kwargs):
        return self._call_inner_tool('filter_plans_by_eligibility', kwargs)

    def get_provider_by_id(self, **kwargs):
        return self._call_inner_tool('get_provider_by_id', kwargs)

    def list_all_providers(self, **kwargs):
        return self._call_inner_tool('list_all_providers', kwargs)

    def filter_plans_by_provider(self, **kwargs):
        return self._call_inner_tool('filter_plans_by_provider', kwargs)

    def validate_plan_provider_reference(self, **kwargs):
        return self._call_inner_tool('validate_plan_provider_reference', kwargs)

    def add_plan(self, **kwargs):
        return self._call_inner_tool('add_plan', kwargs)

    def update_plan_details(self, **kwargs):
        return self._call_inner_tool('update_plan_details', kwargs)

    def remove_plan(self, **kwargs):
        return self._call_inner_tool('remove_plan', kwargs)

    def add_provider(self, **kwargs):
        return self._call_inner_tool('add_provider', kwargs)

    def update_provider_details(self, **kwargs):
        return self._call_inner_tool('update_provider_details', kwargs)

    def remove_provider(self, **kwargs):
        return self._call_inner_tool('remove_provider', kwargs)

    def batch_update_availability_status(self, **kwargs):
        return self._call_inner_tool('batch_update_availability_status', kwargs)

