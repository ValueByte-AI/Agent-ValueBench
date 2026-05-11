# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
from datetime import datetime



class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    account_status: str  # assumed fixed from 'account_sta'

class SubscriptionPlanInfo(TypedDict):
    plan_id: str
    name: str
    billing_cycle: str  # e.g., 'monthly', 'quarterly', 'yearly'
    price: float
    features: List[str]  # assuming it's a list of features

class SubscriptionInfo(TypedDict):
    subscription_id: str
    customer_id: str
    plan_id: str
    start_date: str  # ISO format or similar
    end_date: Optional[str]  # may be None for ongoing
    renewal_cycle: str
    status: str  # e.g., 'active', 'cancelled', 'paused'
    payment_schedule: str  # more detail may be needed

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for tracking customers, plans, and subscriptions.
        """

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Subscription Plans: {plan_id: SubscriptionPlanInfo}
        self.plans: Dict[str, SubscriptionPlanInfo] = {}

        # Subscriptions: {subscription_id: SubscriptionInfo}
        self.subscriptions: Dict[str, SubscriptionInfo] = {}

        # Constraints:
        # - A customer can have multiple subscriptions but not duplicate ACTIVE subscriptions to the same plan.
        # - Subscription start_date must not be after end_date if end_date is set.
        # - Renewal cycles must match the plan’s defined billing cycle.
        # - Only subscriptions with appropriate status (e.g., 'active') trigger billing and service access.
        # - Subscription plans must exist before customers can be assigned to them.

    @staticmethod
    def _ordinal_suffix(day: int) -> str:
        if 10 <= day % 100 <= 20:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    @classmethod
    def _payment_schedule_for_cycle(cls, subscription: SubscriptionInfo, billing_cycle: str) -> str:
        normalized = (billing_cycle or "").strip().lower()
        if normalized == "monthly":
            start_date = subscription.get("start_date")
            try:
                day = datetime.fromisoformat(start_date).day
                return f"{day}{cls._ordinal_suffix(day)} of month"
            except Exception:
                return "monthly"
        if normalized == "yearly":
            return "annually"
        if normalized == "quarterly":
            return "quarterly"
        if normalized == "weekly":
            return "weekly"
        if normalized == "daily":
            return "daily"
        return billing_cycle

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve detailed account information for a specific customer.

        Args:
            customer_id (str): The unique identifier for the customer.

        Returns:
            dict:
                - On success: { "success": True, "data": CustomerInfo }
                - On failure: { "success": False, "error": "Customer not found" }

        Constraints:
            - The customer with the provided ID must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def list_all_customers(self) -> dict:
        """
        Return the list of all registered customers.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo]  # List of all customers (possibly empty)
            }
        """
        all_customers = list(self.customers.values())
        return { "success": True, "data": all_customers }

    def check_customer_account_status(self, customer_id: str) -> dict:
        """
        Query a customer's account status by customer_id.

        Args:
            customer_id (str): The ID of the customer whose status is requested.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str  # The customer's account_status
                    }
                On failure (e.g., customer_id not found):
                    {
                        "success": False,
                        "error": str  # Error message
                    }

        Constraints:
            - customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer does not exist"}
        return {"success": True, "data": customer["account_status"]}

    def get_plan_by_id(self, plan_id: str) -> dict:
        """
        Retrieve full information for a subscription plan by its plan_id.

        Args:
            plan_id (str): The unique identifier for the subscription plan.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": SubscriptionPlanInfo,  # Plan info dictionary
                }
                or
                {
                    "success": False,
                    "error": str  # If plan_id not found
                }

        Constraints:
            - No modification, just fetch. Returns error if plan not found.
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return { "success": False, "error": "Plan not found" }
        return { "success": True, "data": plan }

    def get_plan_by_billing_cycle(self, billing_cycle: str) -> dict:
        """
        Retrieve all subscription plans that match the specified billing cycle.

        Args:
            billing_cycle (str): The billing cycle to search for (e.g., 'monthly', 'quarterly', 'yearly').

        Returns:
            dict: {
                "success": True,
                "data": List[SubscriptionPlanInfo],  # List of matching plan info dicts
            }
            or
            {
                "success": False,
                "error": str  # Only if billing_cycle is not a string or missing
            }

        Constraints:
            - No particular constraints on billing cycle values (returns empty if no matches).
        """
        if not isinstance(billing_cycle, str) or not billing_cycle.strip():
            return {"success": False, "error": "Invalid billing_cycle parameter."}

        matches = [
            plan_info
            for plan_info in self.plans.values()
            if plan_info["billing_cycle"] == billing_cycle
        ]
        return {"success": True, "data": matches}

    def list_all_plans(self) -> dict:
        """
        Retrieve all subscription plans available in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SubscriptionPlanInfo],  # List with info for each plan (possibly empty if none)
            }
        Notes:
            - No input is required.
            - No constraints apply; always returns success with a list.
        """
        plans_list = list(self.plans.values())
        return { "success": True, "data": plans_list }

    def list_customer_subscriptions(self, customer_id: str) -> dict:
        """
        Retrieve all subscriptions associated with the given customer_id.

        Args:
            customer_id (str): The unique identifier for the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[SubscriptionInfo],  # List of subscriptions for the customer (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., customer not found
            }

        Constraints:
            - customer_id must exist in the system.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}

        result = [
            subscription_info
            for subscription_info in self.subscriptions.values()
            if subscription_info["customer_id"] == customer_id
        ]

        return {"success": True, "data": result}

    def get_subscription_by_id(self, subscription_id: str) -> dict:
        """
        Retrieve full information for a subscription by its subscription_id.

        Args:
            subscription_id (str): The unique identifier of the subscription.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SubscriptionInfo  # Full info for the subscription
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Subscription not found"
                    }
        """
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            return { "success": False, "error": "Subscription not found" }
        return { "success": True, "data": subscription }

    def list_active_subscriptions_for_customer_plan(self, customer_id: str, plan_id: str) -> dict:
        """
        Return all active subscriptions for a customer to a given plan.

        Args:
            customer_id (str): Unique identifier for the customer.
            plan_id (str): Unique identifier for the subscription plan.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[SubscriptionInfo]  # list of active subscriptions (may be empty)
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason: customer or plan not found
                }

        Constraints:
            - The customer and plan must both exist in the system.
            - "Active" subscriptions are those whose status == 'active'.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist" }
        if plan_id not in self.plans:
            return { "success": False, "error": "Subscription plan does not exist" }

        active_subs = [
            sub for sub in self.subscriptions.values()
            if sub["customer_id"] == customer_id
               and sub["plan_id"] == plan_id
               and sub["status"] == "active"
        ]
        return { "success": True, "data": active_subs }

    def get_subscription_status(self, subscription_id: str) -> dict:
        """
        Query the status of a specific subscription by its subscription_id.

        Args:
            subscription_id (str): The unique identifier of the subscription.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": { "subscription_id": str, "status": str }
                    }
                On failure (subscription not found):
                    {
                        "success": False,
                        "error": "Subscription not found"
                    }

        Constraints:
            - The provided subscription_id must exist in the system.
        """
        sub = self.subscriptions.get(subscription_id)
        if not sub:
            return {"success": False, "error": "Subscription not found"}
        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "status": sub["status"]
            }
        }

    def add_subscription_plan(
        self,
        plan_id: str,
        name: str,
        billing_cycle: str,
        price: float,
        features: list
    ) -> dict:
        """
        Add a new subscription plan to the environment.

        Args:
            plan_id (str): Unique plan identifier.
            name (str): Subscription plan name.
            billing_cycle (str): Billing recurrence ('monthly', 'yearly', etc.).
            price (float): Price per billing cycle (must be positive).
            features (List[str]): List of feature descriptions.

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
            - plan_id must be unique (not already present in self.plans).
            - price must be positive.
            - billing_cycle should be a non-empty string.
            - features should be a list of strings.
            - name must be a non-empty string.
        """
        # Check for duplicate plan_id
        if plan_id in self.plans:
            return {"success": False, "error": "Plan with this plan_id already exists"}

        if not isinstance(plan_id, str) or not plan_id.strip():
            return {"success": False, "error": "plan_id must be a non-empty string"}
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "name must be a non-empty string"}
        if not isinstance(billing_cycle, str) or not billing_cycle.strip():
            return {"success": False, "error": "billing_cycle must be a non-empty string"}
        if not isinstance(price, (int, float)) or price <= 0:
            return {"success": False, "error": "price must be a positive number"}
        if not isinstance(features, list) or not all(isinstance(f, str) for f in features):
            return {"success": False, "error": "features must be a list of strings"}

        self.plans[plan_id] = {
            "plan_id": plan_id,
            "name": name,
            "billing_cycle": billing_cycle,
            "price": price,
            "features": features,
        }

        return {"success": True, "message": f"Subscription plan {plan_id} added."}

    def update_subscription_plan(
        self,
        plan_id: str,
        name: str = None,
        billing_cycle: str = None,
        price: float = None,
        features: Optional[list] = None
    ) -> dict:
        """
        Modify the properties of an existing subscription plan.

        Args:
            plan_id (str): The ID of the subscription plan to modify.
            name (str, optional): New name for the plan.
            billing_cycle (str, optional): New billing cycle ('monthly', 'quarterly', 'yearly', etc.).
            price (float, optional): New price for the plan (must be non-negative).
            features (list, optional): New list of features for the plan.

        Returns:
            dict: {
                "success": True,
                "message": "Subscription plan updated"
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - The plan must exist.
            - price, if provided, must be >= 0.
            - billing_cycle, if provided, should be non-empty string.
            - At least one field must be provided to update.
        """
        # Check the plan exists
        if plan_id not in self.plans:
            return { "success": False, "error": "Subscription plan not found" }

        if all(param is None for param in [name, billing_cycle, price, features]):
            return { "success": False, "error": "No updates specified" }

        plan = self.plans[plan_id]

        # Field validations
        if price is not None:
            if not isinstance(price, (int, float)) or price < 0:
                return { "success": False, "error": "Price must be a non-negative number" }
            plan['price'] = float(price)
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return { "success": False, "error": "Name must be a non-empty string" }
            plan['name'] = name.strip()
        if billing_cycle is not None:
            if not isinstance(billing_cycle, str) or not billing_cycle.strip():
                return { "success": False, "error": "Billing cycle must be a non-empty string" }
            plan['billing_cycle'] = billing_cycle.strip()
        if features is not None:
            if not isinstance(features, list):
                return { "success": False, "error": "Features must be a list of strings" }
            plan['features'] = features

        self.plans[plan_id] = plan

        return { "success": True, "message": "Subscription plan updated" }

    def delete_subscription_plan(self, plan_id: str) -> dict:
        """
        Remove a subscription plan from the environment.
        Prevents deletion if there are any active subscriptions for this plan.

        Args:
            plan_id (str): Unique identifier of the plan to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Plan <plan_id> deleted."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Cannot delete a plan if any active subscription exists for that plan.
            - Plan must exist to be deletable.
        """
        if plan_id not in self.plans:
            return {"success": False, "error": "Plan does not exist."}

        for sub in self.subscriptions.values():
            if sub["plan_id"] == plan_id and sub["status"] == "active":
                return {"success": False, "error": "Active subscriptions exist for this plan."}

        del self.plans[plan_id]
        return {"success": True, "message": f"Plan {plan_id} deleted."}

    def create_subscription(
        self,
        subscription_id: str,
        customer_id: str,
        plan_id: str,
        start_date: str,
        end_date: Optional[str],
        renewal_cycle: str,
        status: str,
        payment_schedule: str
    ) -> dict:
        """
        Create a new subscription for a specified customer and plan, enforcing all validation constraints.

        Args:
            subscription_id (str): Unique identifier for this subscription.
            customer_id (str): The customer to assign the subscription to.
            plan_id (str): The plan for the subscription.
            start_date (str): Subscription start date, ISO format.
            end_date (Optional[str]): Optional subscription end date (None for ongoing).
            renewal_cycle (str): Renewal cycle (should match plan's billing_cycle).
            status (str): Initial subscription status (e.g. 'active', 'paused', etc.).
            payment_schedule (str): The payment schedule string.

        Returns:
            dict: {
                "success": True,
                "message": "Subscription created for customer <customer_id> on plan <plan_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Customer and plan must exist.
            - No duplicate active subscription for same customer and plan.
            - start_date <= end_date (if end_date is set).
            - renewal_cycle must match plan's billing_cycle.
        """
        # 1. Customer existence check
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}
        # 2. Plan existence check
        if plan_id not in self.plans:
            return {"success": False, "error": "Subscription plan not found"}
        # 3. Duplicate subscription check (active)
        for sub in self.subscriptions.values():
            if (
                sub["customer_id"] == customer_id
                and sub["plan_id"] == plan_id
                and sub["status"] == "active"
            ):
                return {
                    "success": False,
                    "error": "Customer already has an active subscription to this plan"
                }
        # 4. Date order check
        if end_date is not None:
            try:
                sd = datetime.fromisoformat(start_date)
                ed = datetime.fromisoformat(end_date)
                if sd > ed:
                    return {
                        "success": False,
                        "error": "start_date cannot be after end_date"
                    }
            except Exception:
                return {"success": False, "error": "Invalid date format supplied"}
        # 5. Renewal cycle matches plan's billing_cycle
        plan = self.plans[plan_id]
        if renewal_cycle != plan["billing_cycle"]:
            return {
                "success": False,
                "error": "Renewal cycle does not match plan's billing cycle"
            }
        # 6. subscription_id uniqueness (not in constraints, but makes sense)
        if subscription_id in self.subscriptions:
            return {
                "success": False,
                "error": "Subscription ID already exists"
            }
        # 7. Create and store
        new_sub: SubscriptionInfo = {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "plan_id": plan_id,
            "start_date": start_date,
            "end_date": end_date,
            "renewal_cycle": renewal_cycle,
            "status": status,
            "payment_schedule": payment_schedule
        }
        self.subscriptions[subscription_id] = new_sub
        return {
            "success": True,
            "message": f"Subscription created for customer {customer_id} on plan {plan_id}."
        }

    def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Cancel a subscription by updating its status to "cancelled",
        thus ending recurring billing and service access.

        Args:
            subscription_id (str): The unique identifier for the subscription.

        Returns:
            dict:
                - On success: { "success": True, "message": "Subscription <id> cancelled." }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Subscription must exist.
            - Should only allow cancellation if not already "cancelled".
            - After cancellation, status will be "cancelled".
        """
        sub = self.subscriptions.get(subscription_id)
        if not sub:
            return { "success": False, "error": "Subscription not found." }
        if sub["status"] == "cancelled":
            return { "success": False, "error": "Subscription already cancelled." }

        sub["status"] = "cancelled"
        # (Optional: We could update end_date here if business logic requires, but the operation description does not state that.)
        return { "success": True, "message": f"Subscription {subscription_id} cancelled." }

    def pause_subscription(self, subscription_id: str) -> dict:
        """
        Temporarily suspend a subscription by setting its status to "paused".

        Args:
            subscription_id (str): The ID of the subscription to pause.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Subscription paused."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - Subscription must exist.
            - Only subscriptions with status 'active' can be paused.
            - Cannot pause an already paused or cancelled subscription.
        """
        sub = self.subscriptions.get(subscription_id)
        if sub is None:
            return {"success": False, "error": "Subscription not found."}
    
        current_status = sub["status"]
        if current_status == "paused":
            return {"success": False, "error": "Subscription is already paused."}
        if current_status == "cancelled":
            return {"success": False, "error": "Cancelled subscriptions cannot be paused."}
        if current_status != "active":
            return {"success": False, "error": f"Cannot pause subscription with status '{current_status}'."}

        sub["status"] = "paused"
        self.subscriptions[subscription_id] = sub  # Explicitly assign in case storage requires sync

        return {"success": True, "message": "Subscription paused."}

    def update_subscription_dates(
        self,
        subscription_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Change the start and/or end date of an existing subscription.

        Args:
            subscription_id (str): ID of the subscription to update.
            start_date (Optional[str]): New start date (ISO format). If None, do not change.
            end_date (Optional[str]): New end date (ISO format). If None, do not change.

        Returns:
            dict:
              On success: { "success": True, "message": "Subscription dates updated successfully." }
              On failure: { "success": False, "error": <reason> }

        Constraints:
            - subscription_id must exist.
            - If both start_date and end_date are set (after update), start_date must not be after end_date.
            - Dates should be in string format (ISO). No type parsing/error if not.
        """
        if subscription_id not in self.subscriptions:
            return { "success": False, "error": "Subscription does not exist." }
    
        sub = self.subscriptions[subscription_id]
        new_start = start_date if start_date is not None else sub["start_date"]
        new_end = end_date if end_date is not None else sub["end_date"]

        # Constraint: start_date must not be after end_date (if end_date is set)
        # We'll do a string comparison first, but try to use the ISO standard (YYYY-MM-DD...)
        if new_end is not None:
            # Compare the string dates (assuming ISO format)
            if new_start > new_end:
                return { "success": False, "error": "start_date must not be after end_date." }

        if start_date is not None:
            sub["start_date"] = start_date
        if end_date is not None:
            sub["end_date"] = end_date
    
        self.subscriptions[subscription_id] = sub

        return { "success": True, "message": "Subscription dates updated successfully." }

    def change_renewal_cycle(self, subscription_id: str, new_renewal_cycle: str) -> dict:
        """
        Modify the renewal cycle for a subscription, ensuring it matches the plan's billing cycle.
        When the cycle changes, the visible payment_schedule is synchronized to the new cadence.

        Args:
            subscription_id (str): The unique identifier of the subscription to modify.
            new_renewal_cycle (str): The new renewal cycle value to set (should match plan's billing_cycle).

        Returns:
            dict: {
                "success": True,
                "message": "Renewal cycle updated for subscription <subscription_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The subscription must exist.
            - The associated plan must exist.
            - The new renewal cycle must exactly match the plan's billing_cycle.
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return { "success": False, "error": f"Subscription '{subscription_id}' does not exist" }
    
        plan_id = subscription.get("plan_id")
        plan = self.plans.get(plan_id)
        if not plan:
            return { "success": False, "error": f"Associated plan '{plan_id}' does not exist" }
    
        expected_cycle = plan.get("billing_cycle")
        if new_renewal_cycle != expected_cycle:
            return {
                "success": False,
                "error": f"Renewal cycle must match the plan's billing cycle ('{expected_cycle}')"
            }

        subscription["renewal_cycle"] = new_renewal_cycle
        subscription["payment_schedule"] = self._payment_schedule_for_cycle(subscription, new_renewal_cycle)
        self.subscriptions[subscription_id] = subscription
        return {
            "success": True,
            "message": f"Renewal cycle updated for subscription '{subscription_id}'"
        }

    def delete_subscription(self, subscription_id: str) -> dict:
        """
        Permanently remove a subscription from the system.

        Args:
            subscription_id (str): The unique subscription ID to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Subscription <id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Subscription not found."
            }

        Constraints:
            - Subscription must exist in the system.
            - Operation is admin-level (permissions presumed elsewhere).
        """
        if subscription_id not in self.subscriptions:
            return { "success": False, "error": "Subscription not found." }

        del self.subscriptions[subscription_id]

        return {
            "success": True,
            "message": f"Subscription {subscription_id} deleted successfully."
        }

    def reactivate_subscription(self, subscription_id: str) -> dict:
        """
        Reactivate a subscription (set its status to 'active') if currently 'cancelled' or 'paused',
        subject to constraints:
          - Subscription must exist.
          - Must be in 'cancelled' or 'paused' status (NOT already 'active').
          - Associated plan must exist.
          - If end_date is set, start_date must not be after end_date.
          - (Optionally) If end_date is set and in the past, reactivation is not allowed.

        Args:
            subscription_id (str): The unique ID of the subscription to reactivate.

        Returns:
            dict: {
                "success": True,
                "message": "Subscription <id> has been reactivated (status set to active)"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}

        current_status = subscription["status"]
        if current_status == "active":
            return {"success": False, "error": "Subscription is already active"}
        if current_status not in ("paused", "cancelled"):
            return {"success": False, "error": f"Cannot reactivate subscription from status: {current_status}"}

        # Check plan existence
        plan_id = subscription["plan_id"]
        if plan_id not in self.plans:
            return {"success": False, "error": "Associated subscription plan does not exist"}

        # Date validity: start_date must not be after end_date if end_date is set

        start_date_str = subscription["start_date"]
        end_date_str = subscription.get("end_date", None)

        try:
            start_date = datetime.fromisoformat(start_date_str)
            if end_date_str is not None:
                end_date = datetime.fromisoformat(end_date_str)
                if start_date > end_date:
                    return {"success": False, "error": "Invalid subscription dates: start_date is after end_date"}
        except Exception:
            return {"success": False, "error": "Invalid date format in subscription data"}

        # Reactivate
        subscription["status"] = "active"
        self.subscriptions[subscription_id] = subscription  # Defensive update

        return {"success": True, "message": f"Subscription {subscription_id} has been reactivated (status set to active)"}

    def change_subscription_plan(self, subscription_id: str, new_plan_id: str) -> dict:
        """
        Switch an active subscription to a different plan (upgrade/downgrade operation).

        Args:
            subscription_id (str): The subscription to change.
            new_plan_id (str): The target plan ID to switch to.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Subscription switched to new plan."}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints/enforcement:
            - Subscription must exist and must be active.
            - New plan must exist.
            - Cannot result in the customer having duplicate active subscriptions to the same plan.
            - The subscription's renewal_cycle must match the new plan's billing_cycle (update if needed).
            - If the billing cadence changes, the subscription's payment_schedule is synchronized as well.
        """
        # Validate subscription exists
        if subscription_id not in self.subscriptions:
            return {"success": False, "error": "Subscription does not exist"}

        sub = self.subscriptions[subscription_id]

        # Check subscription status
        if sub["status"] != "active":
            return {"success": False, "error": "Subscription is not active and cannot be changed"}

        # Validate plan exists
        if new_plan_id not in self.plans:
            return {"success": False, "error": "New plan does not exist"}

        current_plan_id = sub["plan_id"]
        if new_plan_id == current_plan_id:
            return {"success": False, "error": "Subscription is already on the specified plan"}

        customer_id = sub["customer_id"]

        # Ensure no duplicate active subscriptions for this customer and new_plan_id
        for other_sub in self.subscriptions.values():
            if (other_sub["subscription_id"] != subscription_id and
                other_sub["customer_id"] == customer_id and
                other_sub["plan_id"] == new_plan_id and
                other_sub["status"] == "active"):
                return {"success": False, "error": "Customer already has an active subscription to the target plan"}

        # Enforce renewal cycle matches new plan's billing cycle
        new_billing_cycle = self.plans[new_plan_id]["billing_cycle"]
        if sub["renewal_cycle"] != new_billing_cycle:
            sub["renewal_cycle"] = new_billing_cycle  # Update to match plan
            sub["payment_schedule"] = self._payment_schedule_for_cycle(sub, new_billing_cycle)

        # Update plan association
        sub["plan_id"] = new_plan_id

        # Save the update
        self.subscriptions[subscription_id] = sub

        return {"success": True, "message": "Subscription switched to new plan."}


class SubscriptionManagementSystem(BaseEnv):
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

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_all_customers(self, **kwargs):
        return self._call_inner_tool('list_all_customers', kwargs)

    def check_customer_account_status(self, **kwargs):
        return self._call_inner_tool('check_customer_account_status', kwargs)

    def get_plan_by_id(self, **kwargs):
        return self._call_inner_tool('get_plan_by_id', kwargs)

    def get_plan_by_billing_cycle(self, **kwargs):
        return self._call_inner_tool('get_plan_by_billing_cycle', kwargs)

    def list_all_plans(self, **kwargs):
        return self._call_inner_tool('list_all_plans', kwargs)

    def list_customer_subscriptions(self, **kwargs):
        return self._call_inner_tool('list_customer_subscriptions', kwargs)

    def get_subscription_by_id(self, **kwargs):
        return self._call_inner_tool('get_subscription_by_id', kwargs)

    def list_active_subscriptions_for_customer_plan(self, **kwargs):
        return self._call_inner_tool('list_active_subscriptions_for_customer_plan', kwargs)

    def get_subscription_status(self, **kwargs):
        return self._call_inner_tool('get_subscription_status', kwargs)

    def add_subscription_plan(self, **kwargs):
        return self._call_inner_tool('add_subscription_plan', kwargs)

    def update_subscription_plan(self, **kwargs):
        return self._call_inner_tool('update_subscription_plan', kwargs)

    def delete_subscription_plan(self, **kwargs):
        return self._call_inner_tool('delete_subscription_plan', kwargs)

    def create_subscription(self, **kwargs):
        return self._call_inner_tool('create_subscription', kwargs)

    def cancel_subscription(self, **kwargs):
        return self._call_inner_tool('cancel_subscription', kwargs)

    def pause_subscription(self, **kwargs):
        return self._call_inner_tool('pause_subscription', kwargs)

    def update_subscription_dates(self, **kwargs):
        return self._call_inner_tool('update_subscription_dates', kwargs)

    def change_renewal_cycle(self, **kwargs):
        return self._call_inner_tool('change_renewal_cycle', kwargs)

    def delete_subscription(self, **kwargs):
        return self._call_inner_tool('delete_subscription', kwargs)

    def reactivate_subscription(self, **kwargs):
        return self._call_inner_tool('reactivate_subscription', kwargs)

    def change_subscription_plan(self, **kwargs):
        return self._call_inner_tool('change_subscription_plan', kwargs)
