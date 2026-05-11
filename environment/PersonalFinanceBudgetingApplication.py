# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



# Entity: User
class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    account_status: str  # 'account_sta' assumed to be 'account_status'

# Entity: Budget
class BudgetInfo(TypedDict):
    budget_id: str
    user_id: str
    name: str
    period_type: str
    start_date: str
    end_date: str  # 'end_da' assumed to be 'end_date'

# Entity: Category
class CategoryInfo(TypedDict):
    category_id: str
    name: str
    description: str

# Entity: BudgetCategoryAllocation
class BudgetCategoryAllocationInfo(TypedDict):
    allocation_id: str
    budget_id: str
    category_id: str
    budgeted_amount: float

# Entity: Transaction
class TransactionInfo(TypedDict):
    transaction_id: str
    user_id: str
    amount: float
    date: str
    category_id: str
    description: str


class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for personal finance budgeting and tracking.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Budgets: {budget_id: BudgetInfo}
        self.budgets: Dict[str, BudgetInfo] = {}

        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}

        # BudgetCategoryAllocations: {allocation_id: BudgetCategoryAllocationInfo}
        self.budget_category_allocations: Dict[str, BudgetCategoryAllocationInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Constraints:
        # - Each Budget belongs to a User.
        # - Each Budget has one or more BudgetCategoryAllocations, referencing Categories.
        # - Allocated budgeted_amounts cannot be negative.
        # - Transactions assigned to categories must reference valid Category and User.
        # - Reporting and queries are filtered per-user for privacy.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by exact user name.

        Args:
            name (str): The user's name (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User details if found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found
            }

        Notes:
            - Search is case-sensitive and returns the first user match if duplicates exist.
            - Does not reveal users to unauthorized parties as privacy control is assumed handled externally.

        """
        for user in self.users.values():
            if user["name"] == name:
                return {
                    "success": True,
                    "data": user
                }
        return {
            "success": False,
            "error": "User not found"
        }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user id.

        Args:
            user_id (str): The unique identifier of a user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User info dictionary
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., "User not found"
            }

        Constraints:
            - Returns info for a single user by id.
            - Fails if no user is found with the given id.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_budgets_for_user(self, user_id: str) -> dict:
        """
        List all budgets owned by the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[BudgetInfo]  # List of the user's budgets (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - Only budgets belonging to the user are returned (privacy).
            - User must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_budgets = [
            budget_info
            for budget_info in self.budgets.values()
            if budget_info["user_id"] == user_id
        ]

        return {"success": True, "data": user_budgets}

    def get_budget_by_name_for_user(self, user_id: str, budget_name: str) -> dict:
        """
        Retrieve the budget with a specific name for the given user.

        Args:
            user_id (str): The unique ID of the user.
            budget_name (str): The name of the budget to retrieve.

        Returns:
            dict:
                On success:
                    {"success": True, "data": BudgetInfo}
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - Query is filtered per-user (privacy).
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        for budget in self.budgets.values():
            if budget["user_id"] == user_id and budget["name"] == budget_name:
                return {"success": True, "data": budget}

        return {"success": False, "error": "Budget not found for user"}

    def list_categories(self) -> dict:
        """
        Retrieve all defined spending categories.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # List of all categories, possibly empty
            }

        Constraints:
            - No user restriction; returns all categories in the system.
        """
        categories_list = list(self.categories.values())
        return { "success": True, "data": categories_list }

    def get_category_by_name(self, name: str) -> dict:
        """
        Retrieve a category's info by its name.

        Args:
            name (str): The name of the category to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CategoryInfo  # the matching category's info
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Category not found"
                    }
        Constraints:
            - No specific constraints; matches the first category with the given name.
            - Category names are assumed to be unique, or first found is returned.
        """
        for category in self.categories.values():
            if category["name"] == name:
                return {"success": True, "data": category}
        return {"success": False, "error": "Category not found"}

    def list_budget_category_allocations(self, budget_id: str) -> dict:
        """
        Retrieve all budget allocations (BudgetCategoryAllocationInfo) for the specified budget.

        Args:
            budget_id (str): The unique identifier for the budget.

        Returns:
            dict: {
                "success": True,
                "data": List[BudgetCategoryAllocationInfo]  # possibly empty,
            }
            or
            {
                "success": False,
                "error": str  # error message if budget not found
            }

        Constraints:
            - The given budget_id must exist in the system.
            - Returns all allocations that reference this budget_id.
        """
        if budget_id not in self.budgets:
            return {"success": False, "error": "Budget not found"}

        allocations = [
            alloc for alloc in self.budget_category_allocations.values()
            if alloc["budget_id"] == budget_id
        ]
        return {"success": True, "data": allocations}

    def get_budget_category_allocation(self, budget_id: str, category_id: str) -> dict:
        """
        Retrieve a specific BudgetCategoryAllocation for a given budget and category.

        Args:
            budget_id (str): The ID of the budget.
            category_id (str): The ID of the category.

        Returns:
            dict: {
                "success": True,
                "data": BudgetCategoryAllocationInfo  # The allocation details if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. no allocation found
            }

        Constraints:
            - The allocation must exist for the given budget_id and category_id.
        """
        for allocation in self.budget_category_allocations.values():
            if allocation["budget_id"] == budget_id and allocation["category_id"] == category_id:
                return { "success": True, "data": allocation }
        return { "success": False, "error": "No allocation found for the given budget and category." }

    def get_allocated_amounts_for_budget_categories(self, budget_id: str, category_ids: List[str]) -> dict:
        """
        Get budgeted (allocated) amounts for the specified categories within the given budget.

        Args:
            budget_id (str): The ID of the budget to query.
            category_ids (List[str]): List of category IDs to fetch allocations for.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict: {"category_id": str, "budgeted_amount": float}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - budget_id must exist.
            - Only allocations matching both budget_id and a category_id in category_ids are returned.
            - Missing category_ids in allocations are silently omitted from results.
        """
        if budget_id not in self.budgets:
            return {"success": False, "error": "Budget does not exist"}

        if not category_ids:
            # Valid: just return empty list
            return {"success": True, "data": []}

        results = []
        category_id_set = set(category_ids)
        for alloc in self.budget_category_allocations.values():
            if alloc["budget_id"] == budget_id and alloc["category_id"] in category_id_set:
                results.append({
                    "category_id": alloc["category_id"],
                    "budgeted_amount": alloc["budgeted_amount"]
                })

        return {"success": True, "data": results}

    def list_transactions_for_user(self, user_id: str) -> dict:
        """
        List all transactions for a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[TransactionInfo]
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - Only transactions corresponding to the given user ID are returned.
            - Returns an empty list if user exists but has no transactions.
            - Returns error if user ID is invalid (user does not exist).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_transactions = [
            txn for txn in self.transactions.values()
            if txn["user_id"] == user_id
        ]

        return { "success": True, "data": user_transactions }

    def get_transactions_by_category(self, user_id: str, category_id: str) -> dict:
        """
        Retrieve all transactions for a specific user associated with a specific category.

        Args:
            user_id (str): The user's unique identifier.
            category_id (str): The category's unique identifier.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[TransactionInfo]  # all transactions belonging to that user and category
                }
                On failure: {
                    "success": False,
                    "error": str  # reason for failure
                }

        Constraints:
            - The user_id must exist in the users.
            - The category_id must exist in the categories.
            - Only transactions for that user and category are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        user_category_transactions = [
            tx for tx in self.transactions.values()
            if tx["user_id"] == user_id and tx["category_id"] == category_id
        ]

        return {"success": True, "data": user_category_transactions}

    def get_total_spent_in_category_in_budget(self, budget_id: str, category_id: str) -> dict:
        """
        Compute the total amount spent for a category within a specific budget's period.

        Args:
            budget_id (str): The ID of the budget in question.
            category_id (str): The spending category to sum for.

        Returns:
            dict:
                On success:
                    {"success": True, "data": {"total_spent": float}}
                If budget or category not found:
                    {"success": False, "error": str}

        Constraints:
            - Only consider transactions for the user owning the budget, during the period [start_date, end_date], and for the given category.
            - Transactions outside this period, or belonging to a different user or category, must be excluded.
        """
        # Validate budget existence
        budget = self.budgets.get(budget_id)
        if not budget:
            return {"success": False, "error": "Budget not found"}

        # Validate category existence
        if category_id not in self.categories:
            return {"success": False, "error": "Category not found"}

        user_id = budget["user_id"]
        start_date = budget["start_date"]
        end_date = budget["end_date"]

        total_spent = 0.0
        for transaction in self.transactions.values():
            # Filter by all constraints
            if (
                transaction["user_id"] == user_id and
                transaction["category_id"] == category_id and
                start_date <= transaction["date"] <= end_date
            ):
                total_spent += transaction["amount"]

        return {"success": True, "data": {"total_spent": total_spent}}

    def summarize_budget_vs_spend_for_user(self, user_id: str) -> dict:
        """
        Generate a report for a user's budgets showing planned (budgeted) vs. actual spending per category.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                'success': True,
                'data': List[
                    {
                        'budget_id': str,
                        'budget_name': str,
                        'period_type': str,
                        'start_date': str,
                        'end_date': str,
                        'categories': List[
                            {
                                'category_id': str,
                                'category_name': str,
                                'category_description': str,
                                'planned_amount': float,
                                'actual_spent': float
                            }
                        ]
                    }
                ]
            }
            or
            {
                'success': False,
                'error': str
            }
        Constraints:
            - Only considers budgets belonging to the given user.
            - For each allocation, reports both planned and actual (transactions by the same user, category, and within the budget's dates).
            - Ignores (skips) allocations with invalid category references.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Find all budgets for this user
        budgets = [b for b in self.budgets.values() if b["user_id"] == user_id]
        summary_list = []

        for budget in budgets:
            budget_allocs = [
                alloc for alloc in self.budget_category_allocations.values()
                if alloc["budget_id"] == budget["budget_id"]
            ]

            categories_summary = []

            # Parse budget start and end date
            start_date = budget["start_date"]
            end_date = budget["end_date"]

            for alloc in budget_allocs:
                cat_id = alloc["category_id"]
                # Skip allocation if category doesn't exist
                if cat_id not in self.categories:
                    continue
                cat = self.categories[cat_id]
                planned_amount = alloc["budgeted_amount"]

                # Compute actual spent: sum transaction amounts by this user, same category, date in [start_date, end_date]
                total_spent = 0.0
                for t in self.transactions.values():
                    if (
                        t["user_id"] == user_id and
                        t["category_id"] == cat_id and
                        start_date <= t["date"] <= end_date
                    ):
                        total_spent += t["amount"]

                categories_summary.append({
                    "category_id": cat_id,
                    "category_name": cat["name"],
                    "category_description": cat["description"],
                    "planned_amount": planned_amount,
                    "actual_spent": total_spent
                })

            summary_list.append({
                "budget_id": budget["budget_id"],
                "budget_name": budget["name"],
                "period_type": budget["period_type"],
                "start_date": start_date,
                "end_date": end_date,
                "categories": categories_summary
            })

        return {"success": True, "data": summary_list}

    def create_budget(
        self,
        user_id: str,
        name: str,
        period_type: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Create a new budget for the given user.

        Args:
            user_id (str): The owner's user ID.
            name (str): Descriptive name of the budget.
            period_type (str): Period type (e.g., "monthly").
            start_date (str): Start date for the budget (format not validated here).
            end_date (str): End date for the budget.

        Returns:
            dict: {
                "success": True,
                "message": "Budget created",
                "budget_id": <str>  # Unique id for the new budget
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - The user must exist.
            - Budget id is automatically generated to ensure uniqueness.
            - Name, period_type, start_date, end_date must not be empty.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Basic validation for required fields
        if not all([name, period_type, start_date, end_date]):
            return {"success": False, "error": "All fields are required"}

        # Generate unique budget_id
        budget_id = str(uuid.uuid4())
        while budget_id in self.budgets:
            budget_id = str(uuid.uuid4())

        # Create and store the budget
        new_budget = {
            "budget_id": budget_id,
            "user_id": user_id,
            "name": name,
            "period_type": period_type,
            "start_date": start_date,
            "end_date": end_date,
        }
        self.budgets[budget_id] = new_budget

        return {
            "success": True,
            "message": "Budget created",
            "budget_id": budget_id
        }

    def update_budget(
        self,
        budget_id: str,
        name: str = None,
        period_type: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        Modify details (e.g., period, name) of an existing budget.

        Args:
            budget_id (str): The ID of the budget to modify.
            name (str, optional): New name for the budget.
            period_type (str, optional): New period type (e.g. 'monthly').
            start_date (str, optional): New start date for the budget.
            end_date (str, optional): New end date for the budget.

        Returns:
            dict: {
                "success": True,
                "message": "Budget updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
        Constraints:
            - Only existing budgets can be updated.
            - Only provided fields are updated.
            - No update on 'budget_id' or 'user_id'.
            - At least one updatable field must be provided.
        """
        if budget_id not in self.budgets:
            return {"success": False, "error": "Budget not found."}
    
        updatable_fields = {"name": name, "period_type": period_type, "start_date": start_date, "end_date": end_date}
        # Remove fields not provided (remain as None)
        updates = {k: v for k, v in updatable_fields.items() if v is not None}
    
        if not updates:
            return {"success": False, "error": "No updatable fields provided."}
    
        # Update only the provided fields
        for field, value in updates.items():
            self.budgets[budget_id][field] = value

        return {"success": True, "message": "Budget updated successfully."}

    def delete_budget(self, budget_id: str) -> dict:
        """
        Delete a budget and all associated BudgetCategoryAllocations.

        Args:
            budget_id (str): The ID of the budget to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Budget and its allocations deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Budget not found."
                    }

        Constraints:
            - The budget must exist.
            - All BudgetCategoryAllocations associated with this budget are removed.
        """
        if budget_id not in self.budgets:
            return { "success": False, "error": "Budget not found." }

        # Delete associated budget category allocations
        allocations_to_delete = [
            alloc_id 
            for alloc_id, alloc_info in self.budget_category_allocations.items()
            if alloc_info['budget_id'] == budget_id
        ]
        for alloc_id in allocations_to_delete:
            del self.budget_category_allocations[alloc_id]

        # Delete the budget itself
        del self.budgets[budget_id]

        return {
            "success": True,
            "message": "Budget and its allocations deleted."
        }

    def create_category(self, category_id: str, name: str, description: str) -> dict:
        """
        Create a new spending category.

        Args:
            category_id (str): Unique identifier for the category.
            name (str): Name of the new category.
            description (str): Description of the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category created successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - category_id must be unique.
            - name must be unique across all categories.
        """
        # Check uniqueness of ID
        if category_id in self.categories:
            return {"success": False, "error": "Category ID already exists"}

        # Check uniqueness of name
        for cat in self.categories.values():
            if cat["name"] == name:
                return {"success": False, "error": "Category name already exists"}
    
        # Create the new category
        self.categories[category_id] = {
            "category_id": category_id,
            "name": name,
            "description": description
        }

        return {"success": True, "message": "Category created successfully"}

    def update_category(
        self,
        category_id: str,
        name: str = None,
        description: str = None
    ) -> dict:
        """
        Modify the details of an existing category.

        Args:
            category_id (str): The ID of the category to update.
            name (str, optional): New name for the category.
            description (str, optional): New description for the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category updated successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - category_id must exist in the categories dictionary.
            - At least one of name or description should be provided to update.
            - Silent on empty string handling; will allow (empty name/desc are permitted).
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category not found" }

        if name is None and description is None:
            return { "success": False, "error": "No update fields provided" }

        if name is not None:
            self.categories[category_id]["name"] = name
        if description is not None:
            self.categories[category_id]["description"] = description

        return { "success": True, "message": "Category updated successfully" }

    def create_budget_category_allocation(
        self, allocation_id: str, budget_id: str, category_id: str, budgeted_amount: float
    ) -> dict:
        """
        Create a new BudgetCategoryAllocation record.

        Args:
            allocation_id (str): Unique identifier for this budget allocation.
            budget_id (str): Identifier of the Budget to allocate for (must exist).
            category_id (str): Identifier of the Category (must exist).
            budgeted_amount (float): Amount to allocate; must be non-negative.

        Returns:
            dict:
                - On success: { "success": True, "message": "Budget category allocation created successfully." }
                - On failure: { "success": False, "error": "Reason for failure" }

        Constraints:
            - allocation_id must be unique.
            - budget_id must exist.
            - category_id must exist.
            - budgeted_amount cannot be negative.
        """
        if allocation_id in self.budget_category_allocations:
            return { "success": False, "error": "Allocation ID already exists." }
        if budget_id not in self.budgets:
            return { "success": False, "error": "Budget ID does not exist." }
        if category_id not in self.categories:
            return { "success": False, "error": "Category ID does not exist." }
        if budgeted_amount < 0:
            return { "success": False, "error": "Budgeted amount cannot be negative." }

        allocation = {
            "allocation_id": allocation_id,
            "budget_id": budget_id,
            "category_id": category_id,
            "budgeted_amount": budgeted_amount,
        }
        self.budget_category_allocations[allocation_id] = allocation

        return {
            "success": True,
            "message": "Budget category allocation created successfully."
        }

    def update_budget_category_allocation(self, allocation_id: str, budgeted_amount: float) -> dict:
        """
        Update the budgeted amount for a category allocation.

        Args:
            allocation_id (str): The ID of the allocation to update.
            budgeted_amount (float): The new budgeted amount. Must be non-negative.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Budgeted amount updated successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - budgeted_amount must not be negative.
            - allocation_id must refer to a valid allocation.
        """
        # Check if allocation exists
        allocation = self.budget_category_allocations.get(allocation_id)
        if allocation is None:
            return {"success": False, "error": "Allocation ID does not exist"}

        # Check if amount is valid and non-negative
        if not isinstance(budgeted_amount, (int, float)):
            return {"success": False, "error": "Budgeted amount must be a number"}
        if budgeted_amount < 0:
            return {"success": False, "error": "Budgeted amount must not be negative"}

        # Update the allocation
        allocation["budgeted_amount"] = float(budgeted_amount)
        # Could also update any modification timestamps if tracked

        return {"success": True, "message": "Budgeted amount updated successfully."}

    def delete_budget_category_allocation(self, allocation_id: str) -> dict:
        """
        Remove a category allocation from a budget.

        Args:
            allocation_id (str): The unique ID of the allocation to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Budget category allocation deleted."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The allocation_id must exist in the system.
        """
        if allocation_id not in self.budget_category_allocations:
            return { "success": False, "error": "Allocation ID does not exist." }
    
        del self.budget_category_allocations[allocation_id]
        return { "success": True, "message": "Budget category allocation deleted." }

    def create_transaction(
        self,
        user_id: str,
        amount: float,
        date: str,
        category_id: str,
        description: str
    ) -> dict:
        """
        Add a new income or expense transaction, assigning it to a user and category.

        Args:
            user_id (str): ID of the user who made the transaction (must exist).
            amount (float): Amount of the transaction (negative for expense, positive for income).
            date (str): Date of transaction (ISO format string preferred).
            category_id (str): Category of the transaction (must exist).
            description (str): Optional text describing the transaction.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction created (id: ...)"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must reference an existing user
            - category_id must reference an existing category
            - amount must be a float
            - transaction_id must be unique
        """
        # Validate user
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Validate category
        if category_id not in self.categories:
            return { "success": False, "error": "Category not found" }

        # Validate amount
        try:
            amount_val = float(amount)
        except (ValueError, TypeError):
            return { "success": False, "error": "Amount must be a number" }

        # Minimal check for date (should be string, could add stricter date validation if required)
        if not isinstance(date, str) or not date.strip():
            return { "success": False, "error": "Date is required" }

        # Generate a unique transaction_id
        idx = len(self.transactions) + 1
        transaction_id = f"txn_{idx}"
        while transaction_id in self.transactions:
            idx += 1
            transaction_id = f"txn_{idx}"

        # Construct TransactionInfo
        transaction: TransactionInfo = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount_val,
            "date": date,
            "category_id": category_id,
            "description": description if isinstance(description, str) else "",
        }

        self.transactions[transaction_id] = transaction

        return {
            "success": True,
            "message": f"Transaction created (id: {transaction_id})"
        }

    def update_transaction(
        self, 
        transaction_id: str, 
        amount: float = None, 
        description: str = None, 
        category_id: str = None
    ) -> dict:
        """
        Modify details of a transaction: amount, description, and/or category.

        Args:
            transaction_id (str): The ID of the transaction to update.
            amount (float, optional): The new transaction amount.
            description (str, optional): The new description.
            category_id (str, optional): The new category ID (must reference a valid category).

        Returns:
            dict:
                - On success: { "success": True, "message": "Transaction updated successfully" }
                - On failure: { "success": False, "error": "Reason for failure" }

        Constraints:
            - transaction_id must reference an existing transaction.
            - If provided, category_id must reference an existing category.
            - Only updates provided fields.
        """
        # Check transaction exists
        if transaction_id not in self.transactions:
            return { "success": False, "error": "Transaction does not exist" }
    
        transaction = self.transactions[transaction_id]
        # Validate and update amount
        if amount is not None:
            try:
                transaction['amount'] = float(amount)
            except (TypeError, ValueError):
                return { "success": False, "error": "Invalid amount value" }
        # Validate and update category
        if category_id is not None:
            if category_id not in self.categories:
                return { "success": False, "error": "Category does not exist" }
            transaction['category_id'] = category_id
        # Update description
        if description is not None:
            transaction['description'] = str(description)
        # Write back (dict is mutable in-place, but for clarity)
        self.transactions[transaction_id] = transaction

        return { "success": True, "message": "Transaction updated successfully" }

    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Remove a transaction from the system.

        Args:
            transaction_id (str): The unique identifier of the transaction to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Transaction not found."
            }

        Constraints:
            - Transaction must exist in the system to be deleted.
            - No references need updating and no cascade effect.
        """
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Transaction not found."}
        del self.transactions[transaction_id]
        return {"success": True, "message": "Transaction deleted successfully."}


class PersonalFinanceBudgetingApplication(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_budgets_for_user(self, **kwargs):
        return self._call_inner_tool('list_budgets_for_user', kwargs)

    def get_budget_by_name_for_user(self, **kwargs):
        return self._call_inner_tool('get_budget_by_name_for_user', kwargs)

    def list_categories(self, **kwargs):
        return self._call_inner_tool('list_categories', kwargs)

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def list_budget_category_allocations(self, **kwargs):
        return self._call_inner_tool('list_budget_category_allocations', kwargs)

    def get_budget_category_allocation(self, **kwargs):
        return self._call_inner_tool('get_budget_category_allocation', kwargs)

    def get_allocated_amounts_for_budget_categories(self, **kwargs):
        return self._call_inner_tool('get_allocated_amounts_for_budget_categories', kwargs)

    def list_transactions_for_user(self, **kwargs):
        return self._call_inner_tool('list_transactions_for_user', kwargs)

    def get_transactions_by_category(self, **kwargs):
        return self._call_inner_tool('get_transactions_by_category', kwargs)

    def get_total_spent_in_category_in_budget(self, **kwargs):
        return self._call_inner_tool('get_total_spent_in_category_in_budget', kwargs)

    def summarize_budget_vs_spend_for_user(self, **kwargs):
        return self._call_inner_tool('summarize_budget_vs_spend_for_user', kwargs)

    def create_budget(self, **kwargs):
        return self._call_inner_tool('create_budget', kwargs)

    def update_budget(self, **kwargs):
        return self._call_inner_tool('update_budget', kwargs)

    def delete_budget(self, **kwargs):
        return self._call_inner_tool('delete_budget', kwargs)

    def create_category(self, **kwargs):
        return self._call_inner_tool('create_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def create_budget_category_allocation(self, **kwargs):
        return self._call_inner_tool('create_budget_category_allocation', kwargs)

    def update_budget_category_allocation(self, **kwargs):
        return self._call_inner_tool('update_budget_category_allocation', kwargs)

    def delete_budget_category_allocation(self, **kwargs):
        return self._call_inner_tool('delete_budget_category_allocation', kwargs)

    def create_transaction(self, **kwargs):
        return self._call_inner_tool('create_transaction', kwargs)

    def update_transaction(self, **kwargs):
        return self._call_inner_tool('update_transaction', kwargs)

    def delete_transaction(self, **kwargs):
        return self._call_inner_tool('delete_transaction', kwargs)

