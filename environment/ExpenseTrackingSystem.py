# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict, Any
from datetime import datetime
import re



class ExpenseInfo(TypedDict):
    expense_id: str
    user_id: str
    amount: float
    description: str
    category: str  # stores category_id
    date: str      # ISO 8601 timestamp or similar string

class UserInfo(TypedDict):
    user_id: str
    name: str      # or username
    account_status: str

class CategoryInfo(TypedDict):
    category_id: str
    category_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Expense Tracking System stateful environment.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}

        # Expenses: {expense_id: ExpenseInfo}
        self.expenses: Dict[str, ExpenseInfo] = {}

        # Constraints:
        # - Each expense must be associated with exactly one user (user_id exists in users)
        # - Each expense must have a category from categories (category_id exists in categories)
        # - Expense date must be a valid timestamp string
        # - Amount must be a positive number
        # - Expenses can be filtered/retrieved by category and date

    def list_expenses_by_category_and_date(
        self,
        categories,      # List[str] or str
        start_date: str = None,
        end_date: str = None,
        date: str = None
    ) -> dict:
        """
        List all expenses filtered by specified category (or categories) and by an exact date or a date range.

        Args:
            categories (Union[List[str], str]): Category ID(s) to filter by. Can be a single category_id or a list of category_ids.
            start_date (str, optional): ISO date string representing interval lower-bound (inclusive). Default None.
            end_date (str, optional): ISO date string representing interval upper-bound (inclusive). Default None.
            date (str, optional): ISO date string for matching exact date (overrides range if provided). Default None.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ExpenseInfo]
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - All category IDs given must exist in the system.
            - If category/filter is empty or invalid, error.
            - Filtering is inclusive; date comparisons are string-based (ISO 8601 format assumed).

        Notes:
            - If both `date` and [start_date/end_date] are provided, `date` takes precedence.
            - If only categories are provided, all expenses in those categories are returned.
        """
        # Normalize categories parameter to list
        if isinstance(categories, str):
            categories = [categories]
        elif not isinstance(categories, list):
            return {"success": False, "error": "categories must be string or list of strings"}

        # Validate that all category_ids exist
        missing_categories = [cat for cat in categories if cat not in self.categories]
        if missing_categories:
            return {"success": False, "error": f"Category ID(s) not found: {', '.join(missing_categories)}"}

        matching_expenses = []
        for expense in self.expenses.values():
            # Filter by category
            if expense["category"] not in categories:
                continue

            expense_date = expense["date"]
        
            # Apply date filters
            if date is not None:
                if expense_date != date:
                    continue
            else:
                if start_date and expense_date < start_date:
                    continue
                if end_date and expense_date > end_date:
                    continue

            matching_expenses.append(expense)

        return {"success": True, "data": matching_expenses}

    def list_categories(self) -> dict:
        """
        Retrieve all defined expense categories.

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of categories, each with category_id and category_name
            }

            If no categories have been defined, the list will be empty but returned as a success.
        """
        categories_list = list(self.categories.values())
        return {
            "success": True,
            "data": categories_list
        }

    def get_user_info(self, user_id: str = None, username: str = None) -> dict:
        """
        Retrieve user information by user_id (unique) or by username (may not be unique).
    
        Args:
            user_id (str, optional): The unique user ID.
            username (str, optional): The username (i.e., name field).
    
        Returns:
            dict: On success: {"success": True, "data": UserInfo}
                  On failure: {"success": False, "error": str}
    
        Constraints:
            - At least one of user_id or username must be provided (non-empty).
            - If both provided, priority is given to user_id.
            - If username is not unique, the first found user is returned.
        """
        if not user_id and not username:
            return {
                "success": False,
                "error": "Either user_id or username must be provided"
            }

        if user_id:
            user = self.users.get(user_id)
            if user is not None:
                return {"success": True, "data": user}
            # user_id given, but not found: no need to consider username
            return {"success": False, "error": "User not found"}

        # search by username
        for user in self.users.values():
            if user.get("name") == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_expense_by_id(self, expense_id: str) -> dict:
        """
        Retrieve all details for a specific expense entry by its ID.

        Args:
            expense_id (str): Unique identifier for the expense.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ExpenseInfo  # complete details for the expense
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Expense not found"
                    }

        Constraints:
            - Expense must exist in the system.
        """
        expense = self.expenses.get(expense_id)
        if expense is None:
            return { "success": False, "error": "Expense not found" }
        return { "success": True, "data": expense }


    def summarize_expenses_by_category_and_date(
        self,
        category_ids: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Produce a financial summary (total amount) for expenses in specified categories
        within a date range (inclusive).

        Args:
            category_ids (List[str]): List of category IDs to include.
            start_date (str): ISO 8601 string, inclusive lower bound for date filtering.
            end_date (str): ISO 8601 string, inclusive upper bound for date filtering.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "total_amount": float  # sum of 'amount' across matching expenses
                }
            }
            or
            {
                "success": False,
                "error": str  # error message
            }

        Constraints:
            - All provided category_ids must exist.
            - start_date and end_date must be valid and start_date <= end_date.
        """

        # Validate input: non-empty category_ids
        if not isinstance(category_ids, list) or not category_ids:
            return {"success": False, "error": "No categories specified."}
        missing = [cid for cid in category_ids if cid not in self.categories]
        if missing:
            return {"success": False, "error": f"Category IDs do not exist: {missing}"}
        # Validate and parse dates
        try:
            date_start = datetime.fromisoformat(start_date)
            date_end = datetime.fromisoformat(end_date)
        except Exception:
            return {"success": False, "error": "start_date or end_date is not a valid ISO date string."}
        if date_start > date_end:
            return {"success": False, "error": "start_date must not be after end_date."}

        # Filter and aggregate expenses
        total = 0.0
        for expense in self.expenses.values():
            if expense["category"] not in category_ids:
                continue
            try:
                expense_date = datetime.fromisoformat(expense["date"])
            except Exception:
                continue  # Skip malformed dates in expenses
            if date_start <= expense_date <= date_end:
                amount = expense.get("amount", 0.0)
                if isinstance(amount, (int, float)) and amount > 0:
                    total += amount

        return {
            "success": True,
            "data": {
                "total_amount": round(total, 2)
            }
        }

    def list_all_expenses_for_user(self, user_id: str) -> dict:
        """
        List all expenses recorded by the specified user.

        Args:
            user_id (str): The identifier of the user whose expenses are to be listed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ExpenseInfo]
                    }
                - On failure (user not found):
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - user_id must exist in the users.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        expenses = [
            expense for expense in self.expenses.values()
            if expense["user_id"] == user_id
        ]
        return {"success": True, "data": expenses}


    def add_expense(
        self,
        expense_id: str,
        user_id: str,
        amount: float,
        description: str,
        category: str,
        date: str
    ) -> dict:
        """
        Create a new expense entry with validation.

        Args:
            expense_id (str): Unique identifier for this expense.
            user_id (str): The user's ID (must exist).
            amount (float): Amount spent (must be positive).
            description (str): Description of the expense.
            category (str): Category ID for this expense (must exist).
            date (str): Timestamp (ISO 8601 string preferred).

        Returns:
            dict: {
                "success": True,
                "message": "Expense added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - The user_id must exist.
            - The category must exist.
            - Amount must be positive.
            - Date must be a valid timestamp string (ISO 8601).
            - expense_id must be unique.
        """

        # expense_id must be unique
        if expense_id in self.expenses:
            return {"success": False, "error": "Expense ID already exists."}

        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User ID does not exist."}

        # Check category existence
        if category not in self.categories:
            return {"success": False, "error": "Category ID does not exist."}

        # Check amount positivity
        if not (isinstance(amount, (int, float)) and amount > 0):
            return {"success": False, "error": "Amount must be a positive number."}

        # Simple ISO 8601 validation
        try:
            datetime.fromisoformat(date)
        except Exception:
            return {"success": False, "error": "Date is not a valid ISO 8601 timestamp."}

        # Create the expense entry
        expense: ExpenseInfo = {
            "expense_id": expense_id,
            "user_id": user_id,
            "amount": float(amount),
            "description": description,
            "category": category,
            "date": date
        }
        self.expenses[expense_id] = expense

        return {"success": True, "message": f"Expense {expense_id} added successfully."}

    def update_expense(
        self,
        expense_id: str,
        amount: float = None,
        category: str = None,
        description: str = None,
        date: str = None
    ) -> dict:
        """
        Modify details of an existing expense.
        Only updates provided fields. All constraints are enforced.

        Args:
            expense_id (str): Identifier of the expense to update.
            amount (float, optional): New amount (>0).
            category (str, optional): New category_id (must exist in categories).
            description (str, optional): New description.
            date (str, optional): New date (should be a valid timestamp string, e.g. ISO 8601).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Expense updated successfully"}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - Only provided fields are updated.
            - Expense must exist.
            - Amount must be positive if given.
            - Category must exist if given.
            - Date must be a valid timestamp string if given (basic ISO 8601 check).
        """
        # Check if expense exists
        if expense_id not in self.expenses:
            return {"success": False, "error": "Expense not found"}

        expense = self.expenses[expense_id]

        # Check and update amount
        if amount is not None:
            if not (isinstance(amount, (int, float)) and amount > 0):
                return {"success": False, "error": "Amount must be a positive number"}
            expense["amount"] = float(amount)

        # Check and update category
        if category is not None:
            if category not in self.categories:
                return {"success": False, "error": "Category does not exist"}
            expense["category"] = category

        # Update description
        if description is not None:
            expense["description"] = description

        # Check and update date
        if date is not None:
            if not isinstance(date, str):
                return {"success": False, "error": "Date must be a valid ISO 8601 string"}
            try:
                datetime.fromisoformat(date.replace("Z", "+00:00"))
            except Exception:
                return {"success": False, "error": "Date must be a valid ISO 8601 string"}
            expense["date"] = date

        # Save changes
        self.expenses[expense_id] = expense

        return {"success": True, "message": "Expense updated successfully"}

    def delete_expense(self, expense_id: str) -> dict:
        """
        Remove a specific expense from the system.

        Args:
            expense_id (str): The unique identifier of the expense to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Expense deleted successfully."
            }
            OR
            {
                "success": False,
                "error": "Expense not found."
            }

        Constraints:
            - The expense to be deleted must exist in the system.
        """
        if expense_id not in self.expenses:
            return {"success": False, "error": "Expense not found."}
    
        del self.expenses[expense_id]
        return {"success": True, "message": "Expense deleted successfully."}

    def add_category(self, category_id: str, category_name: str) -> dict:
        """
        Adds a new category to the list of valid expense categories.
    
        Args:
            category_id (str): Unique identifier for the new category.
            category_name (str): Human-readable name for the category.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Category added successfully." }
                On failure:
                    { "success": False, "error": "reason" }
    
        Constraints:
            - category_id must be unique.
            - category_name should not duplicate an existing name (for clarity).
            - category_id and category_name must not be empty.
        """
        # Check for empty or None category_id/category_name
        if not category_id or not isinstance(category_id, str):
            return { "success": False, "error": "Invalid or empty category_id" }
        if not category_name or not isinstance(category_name, str):
            return { "success": False, "error": "Invalid or empty category_name" }

        # Check for existing category_id
        if category_id in self.categories:
            return { "success": False, "error": "Category ID already exists" }

        # Check for duplicate category_name (case-insensitive)
        for cat in self.categories.values():
            if cat["category_name"].strip().lower() == category_name.strip().lower():
                return { "success": False, "error": "Category name already exists" }

        self.categories[category_id] = {
            "category_id": category_id,
            "category_name": category_name,
        }
        return { "success": True, "message": "Category added successfully." }

    def update_category(self, category_id: str, category_name: str) -> dict:
        """
        Rename or otherwise modify an existing expense category.

        Args:
            category_id (str): The ID of the category to modify.
            category_name (str): The new name for the category.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Category updated successfully"
                }
                On failure: {
                    "success": False,
                    "error": <description>
                }
        Constraints:
            - category_id must exist in self.categories.
            - category_name must be a non-empty string.
            - Only category_name can be modified; category_id stays unchanged.
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        if not isinstance(category_name, str) or not category_name.strip():
            return {"success": False, "error": "Category name must be a non-empty string"}

        # Update the category name
        self.categories[category_id]['category_name'] = category_name.strip()
        return {"success": True, "message": "Category updated successfully"}

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a category from the system, and delete all expenses associated with it.

        Args:
            category_id (str): The ID of the category to be deleted.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "message": "Category deleted. <N> associated expenses removed."
                  }
                - On failure: {
                      "success": False,
                      "error": str  # description of error (e.g., category not found)
                  }

        Constraints:
            - The category must exist.
            - All expenses associated with this category will be deleted as well.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist." }

        # Find associated expenses
        to_delete = [eid for eid, einfo in self.expenses.items() if einfo["category"] == category_id]
        num_deleted = len(to_delete)

        for eid in to_delete:
            del self.expenses[eid]

        # Delete category
        del self.categories[category_id]

        return {
            "success": True,
            "message": f"Category deleted. {num_deleted} associated expenses removed."
        }


class ExpenseTrackingSystem(BaseEnv):
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

    def list_expenses_by_category_and_date(self, **kwargs):
        return self._call_inner_tool('list_expenses_by_category_and_date', kwargs)

    def list_categories(self, **kwargs):
        return self._call_inner_tool('list_categories', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_expense_by_id(self, **kwargs):
        return self._call_inner_tool('get_expense_by_id', kwargs)

    def summarize_expenses_by_category_and_date(self, **kwargs):
        return self._call_inner_tool('summarize_expenses_by_category_and_date', kwargs)

    def list_all_expenses_for_user(self, **kwargs):
        return self._call_inner_tool('list_all_expenses_for_user', kwargs)

    def add_expense(self, **kwargs):
        return self._call_inner_tool('add_expense', kwargs)

    def update_expense(self, **kwargs):
        return self._call_inner_tool('update_expense', kwargs)

    def delete_expense(self, **kwargs):
        return self._call_inner_tool('delete_expense', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)
