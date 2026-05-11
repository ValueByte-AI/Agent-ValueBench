# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from datetime import datetime
from typing import Optional



class InnovationInfo(TypedDict):
    innovation_id: str
    title: str
    description: str
    industry_category: str    # References IndustryCategory.category_id
    development_status: str   # Should follow controlled vocabulary (e.g., "proposed", "in development", "completed")
    date_submitted: str
    submitter_id: str         # References User._id

class IndustryCategoryInfo(TypedDict):
    category_id: str
    category_name: str

class UserInfo(TypedDict):
    _id: str
    name: str
    role: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Innovations: {innovation_id: InnovationInfo}
        self.innovations: Dict[str, InnovationInfo] = {}

        # Industry categories: {category_id: IndustryCategoryInfo}
        self.industry_categories: Dict[str, IndustryCategoryInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each innovation must have a unique innovation_id or title
        # - industry_category must reference a valid category in industry_categories
        # - development_status should follow a controlled vocabulary (not enforced here)
        # - submitter_id should correspond to an entry in users (for accountability/auditing)

    def get_innovation_by_id(self, innovation_id: str) -> dict:
        """
        Retrieve innovation record by innovation_id.

        Args:
            innovation_id (str): Unique identifier of the innovation.

        Returns:
            dict:
              - On success: { "success": True, "data": InnovationInfo }
              - On failure: { "success": False, "error": "Innovation not found" }

        Constraints:
            - innovation_id must exist in the innovations repository.
        """
        innovation = self.innovations.get(innovation_id)
        if not innovation:
            return { "success": False, "error": "Innovation not found" }
        return { "success": True, "data": innovation }

    def get_innovation_by_title(self, title: str) -> dict:
        """
        Retrieve a single innovation record by its unique title.

        Args:
            title (str): The title of the innovation.

        Returns:
            dict:
              - On success: { "success": True, "data": InnovationInfo }
              - On failure: { "success": False, "error": str }
    
        Constraints:
            - Title must uniquely identify one innovation.
        """
        for innovation in self.innovations.values():
            if innovation["title"] == title:
                return {"success": True, "data": innovation}
        return {"success": False, "error": "Innovation with the specified title does not exist"}

    def list_all_innovations(self) -> dict:
        """
        Retrieve all innovation records in the system.

        Returns:
            dict:
                - success (bool): True if operation succeeds.
                - data (List[InnovationInfo]): List of all innovations (may be empty if none exist).

        Constraints:
            - Simply aggregates all data, no constraints to enforce here.
            - Does not perform permission checks.

        If there are no innovations, returns success with an empty list.
        """
        result = list(self.innovations.values())
        return {
            "success": True,
            "data": result
        }

    def list_innovations_by_category(self, category_id: str) -> dict:
        """
        List all innovations within the specified industry category.

        Args:
            category_id (str): The category ID to filter innovations by.

        Returns:
            dict: {
                "success": True,
                "data": List[InnovationInfo]  # All innovations within the category
            }
            or
            {
                "success": False,
                "error": str  # error description if category does not exist
            }

        Constraints:
            - category_id must exist in self.industry_categories.
        """
        if category_id not in self.industry_categories:
            return {"success": False, "error": "Industry category does not exist"}

        result = [
            innovation for innovation in self.innovations.values()
            if innovation["industry_category"] == category_id
        ]
        return {"success": True, "data": result}

    def list_innovations_by_status(self, development_status: str) -> dict:
        """
        List all innovations filtered by their development_status.

        Args:
            development_status (str): The status value to filter (e.g., "proposed", "in development", "completed").

        Returns:
            dict: {
                'success': True,
                'data': List[InnovationInfo],  # List may be empty if no matches
            }
            or
            {
                'success': False,
                'error': str  # Reason for failure
            }

        Constraints:
            - development_status should be a non-empty string.
            - Only exact (case-sensitive) matches will be returned.
        """
        if not isinstance(development_status, str) or not development_status.strip():
            return {"success": False, "error": "Invalid development_status: must be a non-empty string"}

        results = [
            innovation for innovation in self.innovations.values()
            if innovation["development_status"] == development_status
        ]
        return {"success": True, "data": results}

    def list_innovations_by_submitter(self, submitter_id: str) -> dict:
        """
        List all innovations submitted by a specific user.

        Args:
            submitter_id (str): The unique identifier for the submitting user.

        Returns:
            dict: {
                "success": True,
                "data": List[InnovationInfo],  # List of the user's submissions (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Description of why the query failed (e.g. user does not exist)
            }

        Constraints:
            - The submitter_id must correspond to an existing user (for accountability/auditing).
            - The returned list may be empty if no submissions exist for this user.
        """
        if submitter_id not in self.users:
            return {"success": False, "error": "Submitter not found"}

        result = [
            innovation for innovation in self.innovations.values()
            if innovation["submitter_id"] == submitter_id
        ]
        return {"success": True, "data": result}

    def list_industry_categories(self) -> dict:
        """
        Retrieve all valid industry categories defined in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[IndustryCategoryInfo]  # List of {category_id, category_name}, possibly empty if none
            }

        Constraints:
            - No inputs required.
            - Always returns all categories in the system.
        """
        categories = list(self.industry_categories.values())
        return { "success": True, "data": categories }

    def get_category_by_name(self, category_name: str) -> dict:
        """
        Retrieve information about an industry category given its name.

        Args:
            category_name (str): The name of the category to fetch (case-insensitive match).

        Returns:
            dict: 
                - { "success": True, "data": IndustryCategoryInfo } if found
                - { "success": False, "error": "Category not found" } otherwise

        Constraints:
            - Looks up category_name in a case-insensitive manner among stored industry categories.
        """
        for cat_info in self.industry_categories.values():
            if cat_info["category_name"].lower() == category_name.lower():
                return { "success": True, "data": cat_info }
        return { "success": False, "error": "Category not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user ID.

        Args:
            user_id (str): Unique identifier of the user (_id field).

        Returns:
            dict: 
                - If found: {"success": True, "data": UserInfo }
                - If not found: {"success": False, "error": "User not found"}
        Constraints:
            - The user_id must match an existing user in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        else:
            return {"success": True, "data": user}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by exact name match.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of user(s) with the given name. Empty list if not found.
            }
            or
            {
                "success": False,
                "error": str  # Description of input error.
            }

        Constraints:
            - If input name is empty or not a string, returns error.
            - Name match is case-sensitive and exact.
            - Name is not guaranteed to be unique; may return multiple users.
        """
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Invalid user name input" }

        matched_users = [
            user_info
            for user_info in self.users.values()
            if user_info["name"] == name
        ]

        return { "success": True, "data": matched_users }

    def list_all_users(self) -> dict:
        """
        List all users in the system, including role information.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],   # List of users (possibly empty)
            }
        """
        user_list = list(self.users.values())
        return {
            "success": True,
            "data": user_list
        }


    def add_innovation(
        self,
        title: str,
        description: str,
        industry_category: str,
        development_status: str,
        submitter_id: str
    ) -> dict:
        """
        Submit a new innovation.
    
        Args:
            title (str): The title of the innovation (must be unique).
            description (str): Description text.
            industry_category (str): category_id that must exist in industry_categories.
            development_status (str): Status string, e.g., "proposed", "in development", "completed".
            submitter_id (str): User._id of the submitter.

        Returns:
            dict: On success {
                      "success": True,
                      "message": "Innovation successfully added",
                      "innovation_id": <str>
                  }
                  On failure {
                      "success": False,
                      "error": <str>
                  }

        Constraints:
            - title must be unique (case-insensitive).
            - industry_category must exist.
            - submitter_id must exist.
        """
        # Uniqueness check for title (case-insensitive)
        for innov in self.innovations.values():
            if innov["title"].strip().lower() == title.strip().lower():
                return {"success": False, "error": "Innovation title already exists"}

        # Validate industry_category (must exist)
        if industry_category not in self.industry_categories:
            return {"success": False, "error": "Invalid industry category"}

        # Validate submitter_id (must exist)
        if submitter_id not in self.users:
            return {"success": False, "error": "Invalid submitter_id"}

        # Generate a unique innovation_id
        innovation_id = str(uuid.uuid4())

        # Set date_submitted to current UTC ISO format
        date_submitted = datetime.utcnow().isoformat()

        info = {
            "innovation_id": innovation_id,
            "title": title,
            "description": description,
            "industry_category": industry_category,
            "development_status": development_status,
            "date_submitted": date_submitted,
            "submitter_id": submitter_id
        }
        self.innovations[innovation_id] = info

        return {
            "success": True,
            "message": "Innovation successfully added",
            "innovation_id": innovation_id
        }

    def update_innovation_status(self, innovation_id: str, new_status: str) -> dict:
        """
        Change the development_status of an existing innovation.

        Args:
            innovation_id (str): The unique identifier of the innovation to be updated.
            new_status (str): The new development status to assign to the innovation.

        Returns:
            dict: {
                "success": True, "message": "Innovation status updated"
            }
            or
            {
                "success": False, "error": str  # Description of the error
            }

        Constraints:
            - The innovation_id must reference an existing innovation.
            - No strict enforcement of controlled vocabulary for development_status in this implementation.
        """
        if innovation_id not in self.innovations:
            return { "success": False, "error": "Innovation not found" }

        self.innovations[innovation_id]["development_status"] = new_status

        return { "success": True, "message": "Innovation status updated" }

    def update_innovation_category(self, innovation_id: str, new_category_id: str) -> dict:
        """
        Change the industry_category reference for a given innovation.

        Args:
            innovation_id (str): The ID of the innovation to update.
            new_category_id (str): The category_id of the new IndustryCategory.

        Returns:
            dict: {
                "success": True,
                "message": "Innovation industry_category updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - innovation_id must exist in the system.
            - new_category_id must reference a valid category in industry_categories.
            - The updated industry_category must be a valid reference.
        """
        if innovation_id not in self.innovations:
            return {"success": False, "error": "Innovation ID does not exist"}

        if new_category_id not in self.industry_categories:
            return {"success": False, "error": "New category ID does not exist"}

        self.innovations[innovation_id]["industry_category"] = new_category_id
        return {"success": True, "message": "Innovation industry_category updated successfully"}

    def delete_innovation(self, innovation_id: str) -> dict:
        """
        Remove an innovation from the system by its id.

        Args:
            innovation_id (str): The ID of the innovation to delete.

        Returns:
            dict:
                {"success": True, "message": "Innovation <id> deleted." }
                or
                {"success": False, "error": "Innovation not found" }

        Constraints:
            - The innovation_id must exist in self.innovations for deletion.
            - No dependencies require check on deletion.
        """
        if innovation_id not in self.innovations:
            return { "success": False, "error": "Innovation not found" }
    
        del self.innovations[innovation_id]
        return { "success": True, "message": f"Innovation {innovation_id} deleted." }

    def add_industry_category(self, category_id: str, category_name: str) -> dict:
        """
        Add a new industry category to the system.

        Args:
            category_id (str): Unique identifier for the category.
            category_name (str): Readable name for the category.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Industry category added successfully."
                    }
                On failure (duplicate id or invalid input):
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - category_id must be unique (not already in self.industry_categories).
            - category_id and category_name must be non-empty.
            - (Optional) category_name uniqueness is not enforced unless desired.
        """
        if not category_id or not category_name:
            return {
                "success": False,
                "error": "Category ID and name must be provided and non-empty."
            }
        if category_id in self.industry_categories:
            return {
                "success": False,
                "error": "Category ID already exists."
            }
        # Create category entry
        self.industry_categories[category_id] = {
            "category_id": category_id,
            "category_name": category_name
        }
        return {
            "success": True,
            "message": "Industry category added successfully."
        }

    def update_industry_category(self, category_id: str, category_name: str = None) -> dict:
        """
        Update the name or attributes of an existing industry category.

        Args:
            category_id (str): The unique ID of the industry category to update.
            category_name (str, optional): New name for the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category updated successfully"
            }
            or
            {
                "success": False,
                "error": "<description of problem>"
            }
    
        Constraints:
          - Updates only allowed for existing categories.
          - Only category_name can be changed (category_id is immutable).
          - If neither category_name nor other valid fields are provided, returns success but indicates nothing was changed.
        """
        if category_id not in self.industry_categories:
            return {"success": False, "error": "Category ID does not exist"}

        updated = False
        if category_name is not None:
            if self.industry_categories[category_id]["category_name"] != category_name:
                self.industry_categories[category_id]["category_name"] = category_name
                updated = True

        if updated:
            return {"success": True, "message": "Category updated successfully"}
        else:
            return {"success": True, "message": "No changes made to the category"}

    def delete_industry_category(self, category_id: str) -> dict:
        """
        Remove an industry category from the controlled vocabulary, provided it is not referenced
        by any innovation (enforces referential integrity).

        Args:
            category_id (str): The ID of the industry category to delete.

        Returns:
            dict: {
                "success": True,
                "message": str,             # Confirmation of deletion
            } or {
                "success": False,
                "error": str                # Description of error (not found, referential integrity, etc)
            }

        Constraints:
            - The category must exist.
            - Cannot delete a category referenced by any innovation
        """
        if category_id not in self.industry_categories:
            return { "success": False, "error": "Industry category does not exist." }

        # Check referential integrity: Is any innovation using this category?
        for innovation in self.innovations.values():
            if innovation["industry_category"] == category_id:
                return {
                    "success": False,
                    "error": (
                        "Cannot delete category; it is referenced by at least one innovation "
                        f"(e.g., innovation '{innovation['innovation_id']}')."
                    )
                }

        del self.industry_categories[category_id]
        return { "success": True, "message": f"Industry category '{category_id}' deleted." }

    def update_innovation_metadata(
        self,
        innovation_id: str,
        title: str = None,
        description: str = None,
        submitter_id: str = None
    ) -> dict:
        """
        Modify innovation fields such as title, description, or submitter.

        Args:
            innovation_id (str): The unique ID of the innovation to modify.
            title (str, optional): New title for the innovation. Must be unique across all innovations.
            description (str, optional): New description.
            submitter_id (str, optional): New submitter's user ID. Must reference an existing user.

        Returns:
            dict: 
                { "success": True, "message": "Innovation metadata updated successfully" }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - innovation_id must exist.
            - If updating title, the new title must be unique.
            - If updating submitter_id, must reference an existing user.
            - If no fields to update are provided, will succeed but do nothing.
        """
        # Check if innovation exists
        if innovation_id not in self.innovations:
            return { "success": False, "error": "Innovation not found" }

        innovation = self.innovations[innovation_id]

        # Check if title needs to be updated and if so, ensure uniqueness
        if title is not None:
            for other_id, other_innovation in self.innovations.items():
                if other_id != innovation_id and other_innovation["title"] == title:
                    return { "success": False, "error": "Title must be unique across all innovations" }
            innovation["title"] = title

        # Update description if provided
        if description is not None:
            innovation["description"] = description

        # Update submitter_id if provided and validate
        if submitter_id is not None:
            if submitter_id not in self.users:
                return { "success": False, "error": "Submitter ID does not reference a valid user" }
            innovation["submitter_id"] = submitter_id

        self.innovations[innovation_id] = innovation

        return { "success": True, "message": "Innovation metadata updated successfully" }

    def add_user(self, _id: str, name: str, role: str) -> dict:
        """
        Register a new user in the system.

        Args:
            _id (str): Unique user identifier.
            name (str): Full name of the user.
            role (str): Role assigned to the user.

        Returns:
            dict:
                - On success: { "success": True, "message": "User successfully added." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - _id must be unique (cannot add user if _id already exists).
            - _id, name, and role must be non-empty.
        """
        if not _id or not _id.strip():
            return { "success": False, "error": "User _id cannot be empty." }
        if not name or not name.strip():
            return { "success": False, "error": "User name cannot be empty." }
        if not role or not role.strip():
            return { "success": False, "error": "User role cannot be empty." }
    
        if _id in self.users:
            return { "success": False, "error": "User with this _id already exists." }
    
        self.users[_id] = {
            "_id": _id,
            "name": name,
            "role": role
        }
        return { "success": True, "message": "User successfully added." }

    def update_user_info(self, _id: str, name: str = None, role: str = None) -> dict:
        """
        Modify user name and/or role for an existing user.

        Args:
            _id (str): The unique identifier of the user to update.
            name (str, optional): The new name for the user.
            role (str, optional): The new role for the user.

        Returns:
            dict:
                On success:  {"success": True, "message": "User info updated for user <_id>"}
                On failure:  {"success": False, "error": "<reason>"}

        Constraints:
            - _id must reference an existing user.
            - At least one of name or role must be provided for update.
        """
        # Check existence
        if _id not in self.users:
            return { "success": False, "error": "User not found" }
    
        # Validation: At least one field to update
        if name is None and role is None:
            return { "success": False, "error": "No update fields provided (specify at least name or role)" }

        # Update fields as specified
        if name is not None:
            self.users[_id]["name"] = name
        if role is not None:
            self.users[_id]["role"] = role

        return { "success": True, "message": f"User info updated for user {_id}" }

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user from the system (admin action).
        Ensures no orphaned submitters: user cannot be deleted if they are referenced as submitter_id on any innovation.

        Args:
            user_id (str): The ID of the user to remove.

        Returns:
            dict: {
                "success": True,
                "message": "User <id> deleted."
            }
            or
            {
                "success": False,
                "error": "User not found" OR "Cannot delete user: user is the submitter for one or more innovations."
            }
    
        Constraints:
            - Cannot delete user if any innovation has submitter_id equal to user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
    
        # Check for orphaned submitters
        for innovation in self.innovations.values():
            if innovation.get("submitter_id") == user_id:
                return {
                    "success": False,
                    "error": "Cannot delete user: user is the submitter for one or more innovations."
                }
    
        del self.users[user_id]
        return {
            "success": True,
            "message": f"User {user_id} deleted."
        }


class InnovationsManagementSystem(BaseEnv):
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

    def get_innovation_by_id(self, **kwargs):
        return self._call_inner_tool('get_innovation_by_id', kwargs)

    def get_innovation_by_title(self, **kwargs):
        return self._call_inner_tool('get_innovation_by_title', kwargs)

    def list_all_innovations(self, **kwargs):
        return self._call_inner_tool('list_all_innovations', kwargs)

    def list_innovations_by_category(self, **kwargs):
        return self._call_inner_tool('list_innovations_by_category', kwargs)

    def list_innovations_by_status(self, **kwargs):
        return self._call_inner_tool('list_innovations_by_status', kwargs)

    def list_innovations_by_submitter(self, **kwargs):
        return self._call_inner_tool('list_innovations_by_submitter', kwargs)

    def list_industry_categories(self, **kwargs):
        return self._call_inner_tool('list_industry_categories', kwargs)

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def add_innovation(self, **kwargs):
        return self._call_inner_tool('add_innovation', kwargs)

    def update_innovation_status(self, **kwargs):
        return self._call_inner_tool('update_innovation_status', kwargs)

    def update_innovation_category(self, **kwargs):
        return self._call_inner_tool('update_innovation_category', kwargs)

    def delete_innovation(self, **kwargs):
        return self._call_inner_tool('delete_innovation', kwargs)

    def add_industry_category(self, **kwargs):
        return self._call_inner_tool('add_industry_category', kwargs)

    def update_industry_category(self, **kwargs):
        return self._call_inner_tool('update_industry_category', kwargs)

    def delete_industry_category(self, **kwargs):
        return self._call_inner_tool('delete_industry_category', kwargs)

    def update_innovation_metadata(self, **kwargs):
        return self._call_inner_tool('update_innovation_metadata', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

