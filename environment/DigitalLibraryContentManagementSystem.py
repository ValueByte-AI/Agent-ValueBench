# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict



class CategoryInfo(TypedDict):
    category_id: str
    name: str
    description: str
    parent_category_id: Optional[str]
    is_education_related: bool

class DigitalResourceInfo(TypedDict):
    resource_id: str
    title: str
    author: str
    publication_date: str
    category_id: str
    content_type: str
    access_status: str

class PaginationStateInfo(TypedDict):
    page_number: int
    page_size: int
    filter_query: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for a digital library content management system.
        """

        # Categories: {category_id: CategoryInfo}
        # Attributes: category_id, name, description, parent_category_id, is_education_related
        self.categories: Dict[str, CategoryInfo] = {}

        # DigitalResources: {resource_id: DigitalResourceInfo}
        # Attributes: resource_id, title, author, publication_date, category_id, content_type, access_status
        self.resources: Dict[str, DigitalResourceInfo] = {}

        # Pagination states: For possible multi-session paging (keyed by session/user if desired)
        # Attributes: page_number, page_size, filter_query
        self.pagination_states: Dict[str, PaginationStateInfo] = {}

        # Constraints:
        # - Pagination must respect page size and page limit.
        # - Categories returned must match the filter.
        # - Each DigitalResource must belong to at least one valid Category.
        # - Categories may be nested (parent_category_id can reference another category).

    def _normalize_filter_kwargs(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        if len(filters) == 1 and isinstance(filters.get("filters"), dict):
            return filters["filters"]
        return filters

    def _filtered_categories(self, filter_query: str) -> list[CategoryInfo]:
        normalized = (filter_query or "").strip().lower()
        if normalized == "education_related":
            return [
                cat for cat in self.categories.values()
                if cat.get("is_education_related", False)
            ]
        if normalized:
            return [
                cat for cat in self.categories.values()
                if normalized in cat.get("name", "").lower()
                or normalized in cat.get("description", "").lower()
            ]
        return list(self.categories.values())

    def _resource_category_ids(self, resource: Dict[str, Any]) -> list[str]:
        category_ids = resource.get("category_ids")
        if isinstance(category_ids, list):
            return [category_id for category_id in category_ids if isinstance(category_id, str) and category_id]
        category_id = resource.get("category_id")
        if isinstance(category_id, str) and category_id:
            return [category_id]
        return []

    def _set_resource_category_ids(self, resource: Dict[str, Any], category_ids: list[str]) -> None:
        resource["category_ids"] = list(category_ids)
        resource["category_id"] = category_ids[0] if category_ids else None

    def filter_categories_by_attribute(self, **filters) -> dict:
        """
        Return categories matching the given attribute values.

        Args:
            **filters: Arbitrary keyword arguments corresponding to CategoryInfo attributes
                (e.g., is_education_related=True, name="Science")

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # Categories matching the filter (may be empty)
            }

        Constraints:
            - Category attribute values must match those provided in filters.
            - Unknown attributes are ignored for filtering; categories will not match unless the attribute exists with the corresponding value.
        """
        filters = self._normalize_filter_kwargs(filters)
        result = []
        for cat in self.categories.values():
            matched = True
            for key, val in filters.items():
                # Only filter on keys that exist in the category info
                if key in cat:
                    if cat[key] != val:
                        matched = False
                        break
                else:
                    matched = False
                    break
            if matched:
                result.append(cat)
        return { "success": True, "data": result }

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve metadata for a single category given its category_id.

        Args:
            category_id (str): Unique identifier of the category to retrieve.

        Returns:
            dict: 
            - If success: { "success": True, "data": CategoryInfo }
            - If category not found: { "success": False, "error": "Category not found" }

        Constraints:
            - The category_id must exist in the system.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }

        return { "success": True, "data": category }

    def list_categories_paginated(
        self, 
        page_number: int, 
        page_size: int, 
        filter_query: str = ""
    ) -> dict:
        """
        Retrieve a paginated list of categories, optionally filtering by name, description,
        or 'education_related' (filter_query == 'education_related' means only education-related categories).
    
        Args:
            page_number (int): The 1-based index of the desired results page (must be >= 1).
            page_size (int): Number of categories per page (must be >= 1).
            filter_query (str): Optional query string. If 'education_related', only categories where is_education_related==True are returned.
                                Otherwise, performs substring match on name or description.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": {
                        "categories": List[CategoryInfo], # paginated category info
                        "total_count": int,               # total number of items after filtering (all pages)
                        "page_number": int,               # current page
                        "page_size": int                  # page size
                    }
                }
                On error,
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Pagination must respect requested page size.
            - Only categories matching the filter are returned.
            - Page numbers/pages_size must be positive.
        """
        if page_number < 1 or page_size < 1:
            return { "success": False, "error": "Page number and page size must be positive integers" }

        filtered = self._filtered_categories(filter_query)

        total_count = len(filtered)
        start = (page_number - 1) * page_size
        end = start + page_size

        paginated = filtered[start:end] if start < total_count else []

        return {
            "success": True,
            "data": {
                "categories": paginated,
                "total_count": total_count,
                "page_number": page_number,
                "page_size": page_size
            }
        }

    def get_category_children(self, category_id: str) -> dict:
        """
        Return the list of subcategories (children) for a given category by category_id.

        Args:
            category_id (str): The category ID whose immediate children (subcategories) are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of child categories, empty if none
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "Category does not exist"
            }

        Constraints:
            - category_id must exist in the categories dictionary.
            - Only immediate children are returned (parent_category_id == category_id).
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        children = [
            cat_info
            for cat_info in self.categories.values()
            if cat_info.get("parent_category_id") == category_id
        ]

        return {"success": True, "data": children}

    def get_pagination_state(self, session_id: str) -> dict:
        """
        Retrieve the current pagination state (page number, page size, filter query) for a given session/user.

        Args:
            session_id (str): Identifier for the session or user.

        Returns:
            dict:
                - On success: {"success": True, "data": PaginationStateInfo}
                - On failure: {"success": False, "error": "Pagination state not found for session"}

        Constraints:
            - session_id must be present in the pagination state mapping.
        """
        state = self.pagination_states.get(session_id)
        if state is None:
            return {"success": False, "error": "Pagination state not found for session"}
        return {"success": True, "data": state}

    def list_resources_by_category(self, category_id: str) -> dict:
        """
        List all digital resources contained in a given category.

        Args:
            category_id (str): The unique identifier of the category to query.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[DigitalResourceInfo]  # Possibly empty if no resources
                  }
                - On failure: {
                      "success": False,
                      "error": str  # Description of the error such as category not found
                  }

        Constraints:
            - The specified category_id must exist in the system.
            - Only resources belonging to exactly this category_id are returned.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        resource_list = [
            resource_info for resource_info in self.resources.values()
            if category_id in self._resource_category_ids(resource_info)
        ]

        return { "success": True, "data": resource_list }

    def set_pagination_state(
        self,
        session_id: str,
        page_number: int,
        page_size: int,
        filter_query: str
    ) -> dict:
        """
        Update (or initialize) the pagination state for a given session/user.

        Args:
            session_id (str): Unique identifier for session/user.
            page_number (int): The page index (must be >= 1).
            page_size (int): Items per page (must be >= 1).
            filter_query (str): The filter string to apply (can be empty).

        Returns:
            dict: {
                "success": True,
                "message": "Pagination state updated for session_id <session_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - page_number and page_size must be positive integers.
            - session_id must be non-empty.
        """
        if not isinstance(session_id, str) or not session_id:
            return { "success": False, "error": "Invalid or empty session_id" }
        if not isinstance(page_number, int) or page_number < 1:
            return { "success": False, "error": "page_number must be an integer >= 1" }
        if not isinstance(page_size, int) or page_size < 1:
            return { "success": False, "error": "page_size must be an integer >= 1" }
        if not isinstance(filter_query, str):
            return { "success": False, "error": "filter_query must be a string" }

        self.pagination_states[session_id] = {
            "page_number": page_number,
            "page_size": page_size,
            "filter_query": filter_query
        }

        return {
            "success": True,
            "message": f"Pagination state updated for session_id {session_id}"
        }

    def next_page(self, state_key: str) -> dict:
        """
        Advance the pagination state for a given session/context (`state_key`) to the next page, 
        according to the current filter query and page size.

        Args:
            state_key (str): Key referencing the pagination state to advance.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of new page number
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Does not advance if already at last page.
            - Pagination state must exist.
            - Categories must be filtered per filter_query.
        """
        # Check pagination state
        if state_key not in self.pagination_states:
            return { "success": False, "error": "Pagination state key does not exist" }
        state = self.pagination_states[state_key]
        page_number = state["page_number"]
        page_size = state["page_size"]
        filter_query = state["filter_query"]

        filtered_categories = self._filtered_categories(filter_query)

        total_items = len(filtered_categories)
        if page_size <= 0:
            return { "success": False, "error": "Invalid page_size in pagination state" }
        total_pages = (total_items + page_size - 1) // page_size

        if total_pages == 0:
            # No items - nothing to advance
            return { "success": False, "error": "No categories to paginate" }

        if page_number >= total_pages:
            return { "success": False, "error": "Already at last page" }

        # Increment page number
        new_page_number = page_number + 1
        self.pagination_states[state_key]["page_number"] = new_page_number

        return { "success": True, "message": f"Pagination advanced to page {new_page_number}" }

    def reset_pagination(self, session_id: str) -> dict:
        """
        Reset or initialize pagination state for the given session/user to the first page
        and default parameters (page_size=20, filter_query="").

        Args:
            session_id (str): Unique identifier for session/user whose pagination is to be reset.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "message": "Pagination state reset to first page with default parameters."
                    }
                - If failed:
                    {
                        "success": False,
                        "error": "Session ID not provided."
                    }

        Constraints:
            - session_id must be provided and non-empty.
            - Reset pagination state to page_number=1, page_size=20, filter_query="".
        """
        if not session_id or not isinstance(session_id, str):
            return { "success": False, "error": "Session ID not provided." }

        default_state = {
            "page_number": 1,
            "page_size": 20,  # Default page size
            "filter_query": ""
        }
        self.pagination_states[session_id] = default_state
        return {
            "success": True,
            "message": "Pagination state reset to first page with default parameters."
        }

    def update_category_parent(self, category_id: str, parent_category_id: Optional[str]) -> dict:
        """
        Change or set the parent_category_id of a category.

        Args:
            category_id (str): The ID of the category to update.
            parent_category_id (Optional[str]): The new parent category ID, or None to unset.

        Returns:
            dict: {
                "success": True,
                "message": "Parent category updated for <category_id>."
            } or {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - category_id must exist.
            - parent_category_id must exist (if not None).
            - category cannot be its own parent.
            - Must not introduce a cycle (parent_category_id must not be a child/descendant of category_id).
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist."}
    
        if parent_category_id == category_id:
            return {"success": False, "error": "A category cannot be its own parent."}
    
        if parent_category_id is not None and parent_category_id not in self.categories:
            return {"success": False, "error": "Parent category does not exist."}
    
        # Check for potential cycles
        ancestor_id = parent_category_id
        while ancestor_id is not None:
            if ancestor_id == category_id:
                return {"success": False, "error": "Operation would create a cycle in the category hierarchy."}
            ancestor = self.categories.get(ancestor_id)
            if ancestor is None:
                break  # orphaned, impossible in current model, but safe
            ancestor_id = ancestor.get("parent_category_id")

        # All checks passed; update
        self.categories[category_id]["parent_category_id"] = parent_category_id
        return {"success": True, "message": f"Parent category updated for {category_id}."}

    def add_category(
        self,
        category_id: str,
        name: str,
        description: str,
        is_education_related: bool,
        parent_category_id: Optional[str] = None
    ) -> dict:
        """
        Create and add a new category to the library's set of categories.

        Args:
            category_id (str): Unique identifier for the category.
            name (str): The name of the category.
            description (str): Description text for the category.
            is_education_related (bool): Whether this category is education-related.
            parent_category_id (Optional[str]): ID of the parent category for nesting (can be None).

        Returns:
            dict: {
                "success": True,
                "message": "Category added successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - category_id must be unique.
            - parent_category_id, if provided, must reference an existing category.
        """
        if not category_id or not name or not description or (is_education_related is None):
            return { "success": False, "error": "Missing required fields." }

        if category_id in self.categories:
            return { "success": False, "error": "Category ID already exists." }

        if parent_category_id:
            if parent_category_id not in self.categories:
                return { "success": False, "error": "Parent category does not exist." }

        self.categories[category_id] = {
            "category_id": category_id,
            "name": name,
            "description": description,
            "parent_category_id": parent_category_id,
            "is_education_related": is_education_related
        }

        return { "success": True, "message": "Category added successfully." }

    def remove_category(self, category_id: str) -> dict:
        """
        Delete a category and handle orphaned resources or subcategories.
    
        Args:
            category_id (str): The ID of the category to be deleted.
    
        Returns:
            dict: 
                - success: True/False
                - message: Operation summary on success.
                - details: On success, contains:
                    - updated_subcategories: list of subcategories whose parent_category_id reset to None.
                    - orphaned_resources: list of resource_ids for resources that now have no valid category.
                - error: Description on failure.

        Constraints:
            - Each DigitalResource must belong to at least one valid Category.
            - Categories may be nested; subcategories' parent should be reset to None if their parent is deleted.
            - If any DigitalResource becomes orphaned, include their IDs in the result.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        # Remove the category
        del self.categories[category_id]

        # Update subcategories: reset parent_category_id if it references the removed category
        updated_subcategories = []
        for cid, cat_info in self.categories.items():
            if cat_info.get("parent_category_id") == category_id:
                self.categories[cid]["parent_category_id"] = None
                updated_subcategories.append(cid)

        # Find orphaned resources: resources whose remaining category associations become empty
        orphaned_resources = []
        for rid, res_info in self.resources.items():
            category_ids = self._resource_category_ids(res_info)
            if category_id not in category_ids:
                continue
            remaining_categories = [
                candidate for candidate in category_ids
                if candidate != category_id and candidate in self.categories
            ]
            if remaining_categories:
                self._set_resource_category_ids(res_info, remaining_categories)
            else:
                orphaned_resources.append(rid)
                if res_info.get("category_id") == category_id:
                    res_info["category_id"] = None

        message = (
            f"Category '{category_id}' removed. "
            f"{len(updated_subcategories)} subcategories updated. "
            f"{len(orphaned_resources)} resources orphaned."
        )

        return {
            "success": True,
            "message": message,
            "details": {
                "updated_subcategories": updated_subcategories,
                "orphaned_resources": orphaned_resources
            }
        }

    def add_resource_to_category(self, resource_id: str, category_id: str) -> dict:
        """
        Link a digital resource to a category.

        Args:
            resource_id (str): The resource to link.
            category_id (str): The target category.

        Returns:
            dict: {
                'success': True,
                'message': 'Resource <resource_id> linked to category <category_id>.'
            } or {
                'success': False,
                'error': <reason>
            }

        Constraints:
            - Both resource and category must exist.
            - Each resource must belong to at least one valid category.
        """
        if resource_id not in self.resources:
            return { "success": False, "error": f"Resource {resource_id} does not exist" }

        if category_id not in self.categories:
            return { "success": False, "error": f"Category {category_id} does not exist" }

        resource = self.resources[resource_id]
        category_ids = self._resource_category_ids(resource)
        if category_id not in category_ids:
            category_ids.append(category_id)
        self._set_resource_category_ids(resource, category_ids)

        return { 
            "success": True, 
            "message": f"Resource {resource_id} linked to category {category_id}." 
        }

    def remove_resource_from_category(self, resource_id: str, category_id: str) -> dict:
        """
        Unlink a resource from a specific category, ensuring the resource remains
        associated with at least one valid category.

        Args:
            resource_id (str): The unique identifier of the digital resource.
            category_id (str): The unique identifier of the category to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Resource unlinked from category"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Resource and category must both exist.
            - Resource must be associated with the specified category.
            - Resource must be associated with at least one valid category after removal.
        """
        # Check resource exists
        resource = self.resources.get(resource_id)
        if resource is None:
            return { "success": False, "error": "Resource does not exist" }

        # Check category exists
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        category_ids = self._resource_category_ids(resource)

        # Check resource is actually linked to this category
        if category_id not in category_ids:
            return { "success": False, "error": "Resource is not linked to the specified category" }

        # Check that removing would not leave resource with zero categories
        if len(category_ids) <= 1:
            return { "success": False, "error": "Resource must remain in at least one category" }

        # Remove the category association
        category_ids.remove(category_id)
        self._set_resource_category_ids(resource, category_ids)

        return { "success": True, "message": "Resource unlinked from category" }


class DigitalLibraryContentManagementSystem(BaseEnv):
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

    def filter_categories_by_attribute(self, **kwargs):
        return self._call_inner_tool('filter_categories_by_attribute', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_categories_paginated(self, **kwargs):
        return self._call_inner_tool('list_categories_paginated', kwargs)

    def get_category_children(self, **kwargs):
        return self._call_inner_tool('get_category_children', kwargs)

    def get_pagination_state(self, **kwargs):
        return self._call_inner_tool('get_pagination_state', kwargs)

    def list_resources_by_category(self, **kwargs):
        return self._call_inner_tool('list_resources_by_category', kwargs)

    def set_pagination_state(self, **kwargs):
        return self._call_inner_tool('set_pagination_state', kwargs)

    def next_page(self, **kwargs):
        return self._call_inner_tool('next_page', kwargs)

    def reset_pagination(self, **kwargs):
        return self._call_inner_tool('reset_pagination', kwargs)

    def update_category_parent(self, **kwargs):
        return self._call_inner_tool('update_category_parent', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def remove_category(self, **kwargs):
        return self._call_inner_tool('remove_category', kwargs)

    def add_resource_to_category(self, **kwargs):
        return self._call_inner_tool('add_resource_to_category', kwargs)

    def remove_resource_from_category(self, **kwargs):
        return self._call_inner_tool('remove_resource_from_category', kwargs)
