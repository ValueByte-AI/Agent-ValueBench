# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, Any, TypedDict
from datetime import datetime
from typing import Optional, Dict, Any



class CategoryGroupInfo(TypedDict):
    group_id: str
    name: str
    description: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class CategoryInfo(TypedDict):
    category_id: str
    group_id: str
    name: str
    description: str
    metadata: Dict[str, Any]
    parent_category_id: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Chatbot backend category management environment.
        """

        # Category Groups: {group_id: CategoryGroupInfo}
        # Maps each group_id to CategoryGroup including metadata, timestamps
        self.category_groups: Dict[str, CategoryGroupInfo] = {}

        # Categories: {category_id: CategoryInfo}
        # Maps each category_id to Category including parent_category_id and group membership
        self.categories: Dict[str, CategoryInfo] = {}

        # Constraints:
        # - group_id and category_id must be unique within the system
        # - CategoryGroup can have zero or more Categories
        # - parent_category_id, if present, must reference a valid Category in the same group
        # - Updates to category metadata should not break group-category relationships

    def list_all_category_groups(self) -> dict:
        """
        Retrieve a list of all CategoryGroups available in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryGroupInfo],  # May be an empty list if no groups exist
            }

        Constraints:
            - None (this is a simple read/query operation).
        """
        data = list(self.category_groups.values())
        return {
            "success": True,
            "data": data
        }

    def get_category_group_by_id(self, group_id: str) -> dict:
        """
        Retrieve full information for a specific CategoryGroup given its group_id.

        Args:
            group_id (str): The unique identifier of the CategoryGroup.

        Returns:
            dict: {
                "success": True,
                "data": CategoryGroupInfo
            }
            OR
            {
                "success": False,
                "error": str  # Reason the lookup failed
            }

        Constraints:
            - The group_id must exist in the system.
        """
        group = self.category_groups.get(group_id)
        if group is not None:
            return {"success": True, "data": group}
        else:
            return {"success": False, "error": "Category group with given group_id does not exist"}

    def list_categories_by_group(self, group_id: str) -> dict:
        """
        Retrieve all Category entities belonging to the specified CategoryGroup.

        Args:
            group_id (str): Unique identifier of the CategoryGroup.

        Returns:
            dict:
                On Success: {
                    "success": True,
                    "data": List[CategoryInfo],  # All categories belonging to this group (empty list if none)
                }
                On Failure: {
                    "success": False,
                    "error": str  # E.g., 'CategoryGroup does not exist'
                }

        Constraints:
            - group_id must refer to an existing CategoryGroup in the system.
        """
        if group_id not in self.category_groups:
            return {"success": False, "error": "CategoryGroup does not exist"}

        data = [
            category_info for category_info in self.categories.values()
            if category_info["group_id"] == group_id
        ]
        return {"success": True, "data": data}

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve all available information for a Category specified by its category_id.

        Args:
            category_id (str): Unique identifier for the target Category.

        Returns:
            dict: 
                - On success: { "success": True, "data": CategoryInfo }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - The category_id must exist in the management system.
        """
        category = self.categories.get(category_id)
        if category is None:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def list_child_categories(self, group_id: str, parent_category_id: str) -> dict:
        """
        Retrieve all child categories under the specified parent_category_id within a specific group.

        Args:
            group_id (str): The ID of the category group.
            parent_category_id (str): The category_id of the parent category.

        Returns:
            dict:
             - On success: {
                   "success": True,
                   "data": List[CategoryInfo]
               }
             - On error: {
                   "success": False,
                   "error": str
               }

        Constraints:
            - group_id must exist in the system.
            - parent_category_id must exist and belong to the given group.
        """
        if group_id not in self.category_groups:
            return { "success": False, "error": "Group ID does not exist" }

        parent = self.categories.get(parent_category_id)
        if not parent or parent["group_id"] != group_id:
            return { "success": False, "error": "Parent Category ID does not exist in the specified group" }

        children = [
            cat_info for cat_info in self.categories.values()
            if cat_info["group_id"] == group_id and cat_info.get("parent_category_id") == parent_category_id
        ]

        return { "success": True, "data": children }

    def check_group_id_uniqueness(self, group_id: str) -> dict:
        """
        Check whether the provided group_id is unique in the system, meaning it does not exist already.

        Args:
            group_id (str): The candidate group ID to check.

        Returns:
            dict: {
                "success": True,
                "unique": bool   # True if group_id does not exist, False otherwise
            }
            or
            {
                "success": False,
                "error": str     # Description of the error if input is invalid
            }

        Constraints:
            - group_id must be a non-empty string.
            - group_id is considered unique if it is not present in self.category_groups.
        """
        if not isinstance(group_id, str) or not group_id.strip():
            return { "success": False, "error": "Invalid group_id" }
        is_unique = group_id not in self.category_groups
        return { "success": True, "unique": is_unique }

    def check_category_id_uniqueness(self, category_id: str) -> dict:
        """
        Verify whether a category_id is unique in the system.

        Args:
            category_id (str): The category ID to check for uniqueness.

        Returns:
            dict:
                - If input valid: { "success": True, "data": bool }
                  (True if unique/not present; False if already used)
                - On invalid input: { "success": False, "error": str }

        Constraints:
            - category_id must be non-empty string.
        """
        if not category_id or not isinstance(category_id, str):
            return { "success": False, "error": "category_id is required." }

        is_unique = category_id not in self.categories
        return { "success": True, "data": is_unique }

    def validate_category_parent_reference(self, parent_category_id: Optional[str], group_id: str) -> dict:
        """
        Verify that a parent_category_id, if specified, exists
        and is in the same group as indicated by group_id.

        Args:
            parent_category_id (Optional[str]): The candidate parent category's ID, or None/empty if no parent.
            group_id (str): The group ID that the child category would belong to.

        Returns:
            dict: {
                "success": True,
                "valid": bool,
                "reason": str  # Short description for validation result.
            }

        Constraints:
            - If parent_category_id is None or empty, the reference is valid.
            - If parent_category_id is provided, it must exist in self.categories and its group_id must match the provided group_id.
        """
        if not parent_category_id:
            return { "success": True, "valid": True, "reason": "No parent_category_id specified; reference is trivially valid." }
    
        parent = self.categories.get(parent_category_id)
        if not parent:
            return { "success": True, "valid": False, "reason": f"Parent category ID '{parent_category_id}' does not exist." }
        if parent["group_id"] != group_id:
            return { "success": True, "valid": False, "reason": f"Parent category group_id '{parent['group_id']}' does not match specified group_id '{group_id}'." }

        return { "success": True, "valid": True, "reason": "Parent category exists and is in the same group." }


    def add_category_group(
        self,
        group_id: str,
        name: str,
        description: str,
        metadata: dict
    ) -> dict:
        """
        Create and register a new CategoryGroup with a unique group_id.

        Args:
            group_id (str): Unique identifier for the category group.
            name (str): Human-readable group name.
            description (str): Description of the category group.
            metadata (dict): Arbitrary metadata for the group.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "CategoryGroup <group_id> created successfully" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - group_id must be unique.
            - created_at and updated_at are set to current UTC time.
        """
        if not isinstance(metadata, dict):
            return {"success": False, "error": "metadata must be a dictionary"}

        if group_id in self.category_groups:
            return {"success": False, "error": "Group ID already exists"}

        now_iso = datetime.utcnow().isoformat() + "Z"  # Append 'Z' for UTC

        group_info: CategoryGroupInfo = {
            "group_id": group_id,
            "name": name,
            "description": description,
            "metadata": metadata,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self.category_groups[group_id] = group_info

        return {
            "success": True,
            "message": f"CategoryGroup {group_id} created successfully"
        }


    def update_category_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Update information or metadata for an existing CategoryGroup.

        Args:
            group_id (str): The ID of the CategoryGroup to update.
            name (Optional[str]): If given, update the name.
            description (Optional[str]): If given, update the description.
            metadata (Optional[Dict[str, Any]]): If given, replace (not merge) the metadata dictionary.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "CategoryGroup {group_id} updated successfully" }
                On error:
                    { "success": False, "error": "reason" }

        Constraints:
            - group_id must refer to an existing CategoryGroup.
            - Metadata, if updated, must be a dict.
            - updated_at timestamp is always refreshed to current UTC time.
            - group_id itself cannot be changed.
        """
        if group_id not in self.category_groups:
            return { "success": False, "error": "CategoryGroup not found" }

        group = self.category_groups[group_id]

        updated = False
        if name is not None:
            group["name"] = name
            updated = True
        if description is not None:
            group["description"] = description
            updated = True
        if metadata is not None:
            if not isinstance(metadata, dict):
                return { "success": False, "error": "metadata must be a dictionary" }
            group["metadata"] = metadata
            updated = True

        # Always update the updated_at timestamp if anything is changed
        if updated:
            group["updated_at"] = datetime.utcnow().isoformat()

        self.category_groups[group_id] = group

        return {
            "success": True,
            "message": f"CategoryGroup {group_id} updated successfully"
        }

    def delete_category_group(self, group_id: str, delete_categories: bool = False) -> dict:
        """
        Remove a CategoryGroup by group_id.
        Optionally also deletes all Categories belonging to that group.

        Args:
            group_id (str): The unique identifier of the CategoryGroup to delete.
            delete_categories (bool, optional): If True, also deletes all categories in the group.
                If False and group contains categories, fails with error.
    
        Returns:
            dict:
                - On success with no categories: {
                    "success": True,
                    "message": "CategoryGroup deleted",
                    "deleted_categories": []
                  }
                - On success with deleted categories: {
                    "success": True,
                    "message": "CategoryGroup and categories deleted",
                    "deleted_categories": [list of deleted category_ids]
                  }
                - On failure: {
                    "success": False,
                    "error": reason
                  }

        Constraints:
            - group_id must exist.
            - If group contains categories, must set delete_categories=True to also remove them.
            - Never leaves orphan Categories without a group.
        """
        if group_id not in self.category_groups:
            return {"success": False, "error": "CategoryGroup does not exist"}

        # Find all associated category_ids
        category_ids_in_group = [
            cat_id for cat_id, cat_info in self.categories.items()
            if cat_info["group_id"] == group_id
        ]

        if category_ids_in_group and not delete_categories:
            return {
                "success": False,
                "error": "CategoryGroup contains categories. Set delete_categories=True to delete group and all its categories."
            }

        # Delete categories if flagged
        deleted_cats = []
        if delete_categories:
            for cat_id in category_ids_in_group:
                del self.categories[cat_id]
                deleted_cats.append(cat_id)

        # Now delete the group
        del self.category_groups[group_id]

        msg = "CategoryGroup and categories deleted" if deleted_cats else "CategoryGroup deleted"

        return {
            "success": True,
            "message": msg,
            "deleted_categories": deleted_cats
        }

    def add_category(
        self,
        category_id: str,
        group_id: str,
        name: str,
        description: str,
        metadata: dict,
        parent_category_id: Optional[str] = None,
    ) -> dict:
        """
        Create and register a new Category within a CategoryGroup.

        Args:
            category_id (str): Unique identifier for the category.
            group_id (str): Identifier of the CategoryGroup.
            name (str): Name of the category.
            description (str): Description of the category.
            metadata (dict): Metadata associated with the category.
            parent_category_id (Optional[str]): (Optional) ID of the parent category (must be in same group if provided).

        Returns:
            dict: Success message or error with reason.

        Constraints:
            - category_id must be unique.
            - group_id must exist.
            - If given, parent_category_id must exist and belong to the same group.
        """
        # Check category_id uniqueness
        if category_id in self.categories:
            return {"success": False, "error": "Category ID already exists."}

        # Check that target group_id exists
        if group_id not in self.category_groups:
            return {"success": False, "error": "Group ID does not exist."}

        # If parent_category_id is provided, validate it
        if parent_category_id:
            parent = self.categories.get(parent_category_id)
            if parent is None:
                return {
                    "success": False,
                    "error": f"Parent category ID {parent_category_id} does not exist."
                }
            if parent["group_id"] != group_id:
                return {
                    "success": False,
                    "error": f"Parent category ID {parent_category_id} does not belong to group {group_id}."
                }

        category_info: CategoryInfo = {
            "category_id": category_id,
            "group_id": group_id,
            "name": name,
            "description": description,
            "metadata": metadata,
            "parent_category_id": parent_category_id,
        }
        self.categories[category_id] = category_info

        return {
            "success": True,
            "message": f"Category {category_id} added to group {group_id}"
        }

    def update_category(
        self,
        category_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        parent_category_id: Optional[str] = None
    ) -> dict:
        """
        Update one or more fields of an existing category.

        Args:
            category_id (str): The ID of the category to update.
            name (Optional[str]): New name (if updating).
            description (Optional[str]): New description (if updating).
            metadata (Optional[dict]): New metadata dictionary to merge/update (if any).
            parent_category_id (Optional[str]): New parent category id (if updating).

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
            - `category_id` must already exist.
            - If `parent_category_id` is given and not None, must:
                - Reference a valid category in the same group.
                - Not create cyclic hierarchy.
            - Cannot break group-category relationships.
        """
        # Check if category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category not found"}

        category = self.categories[category_id]
        group_id = category["group_id"]

        # Validate new parent_category_id if provided
        if parent_category_id is not None:
            if parent_category_id == category_id:
                return {"success": False, "error": "A category cannot be its own parent"}
            if parent_category_id not in self.categories:
                return {"success": False, "error": "Parent category does not exist"}
            parent_category = self.categories[parent_category_id]
            if parent_category["group_id"] != group_id:
                return {"success": False, "error": "Parent category must be in the same group"}

            # Check for cycles in the parent chain
            ancestor_id = parent_category_id
            while ancestor_id:
                if ancestor_id == category_id:
                    return {"success": False, "error": "Cyclic parent relationship detected"}
                ancestor = self.categories[ancestor_id]
                ancestor_id = ancestor.get("parent_category_id")

        # Perform updates
        updated = False
        if name is not None:
            category["name"] = name
            updated = True
        if description is not None:
            category["description"] = description
            updated = True
        if metadata is not None:
            # Merge/update metadata, do not overwrite unless that's intended
            if not isinstance(metadata, dict):
                return {"success": False, "error": "metadata must be a dict"}
            category["metadata"].update(metadata)
            updated = True
        if parent_category_id is not None:
            category["parent_category_id"] = parent_category_id
            updated = True

        if updated:
            # Optionally update timestamps, e.g., in related CategoryGroup (not specified here)
            return {"success": True, "message": "Category updated successfully"}
        else:
            return {"success": False, "error": "No fields specified for update"}

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a Category from the system.
    
        Args:
            category_id (str): ID of the category to delete.
    
        Returns:
            dict: 
                - {
                    "success": True,
                    "message": "Category <category_id> deleted."
                  }
                - {
                    "success": False,
                    "error": "Category does not exist"
                  }
    
        Constraints:
            - If the category has child categories, they are orphaned (their parent_category_id is set to None).
            - Group-category linkage is not broken by deletion.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }
    
        # Orphan all children of this category
        for cat in self.categories.values():
            if cat.get("parent_category_id") == category_id:
                cat["parent_category_id"] = None

        # Delete the category itself
        del self.categories[category_id]
    
        return { "success": True, "message": f"Category {category_id} deleted." }

    def update_category_metadata(self, category_id: str, new_metadata: dict) -> dict:
        """
        Modify the metadata field of an existing Category while maintaining integrity constraints.

        Args:
            category_id (str): Unique identifier for the category whose metadata should be updated.
            new_metadata (dict): New metadata dictionary to assign to the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category metadata updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - category_id must exist.
            - Only the metadata field will be changed for the given category.
            - Update must not break group-category relationships, but changing metadata alone does not do so.
        """
        if not isinstance(new_metadata, dict):
            return {"success": False, "error": "Provided new_metadata must be a dictionary"}
        category = self.categories.get(category_id)
        if category is None:
            return {"success": False, "error": "Category not found"}

        # Only change the metadata.
        category['metadata'] = new_metadata

        # (No relational links can be harmed by this action)
        return {"success": True, "message": "Category metadata updated"}

    def reparent_category(self, category_id: str, new_parent_category_id: str) -> dict:
        """
        Change a Category's parent_category_id, updating the hierarchy, but only if the new parent is valid.

        Args:
            category_id (str): The ID of the category to reparent.
            new_parent_category_id (str): The ID of the new parent category (can be empty or None for no parent/top-level).

        Returns:
            dict: {
                "success": True,
                "message": "Category reparented successfully"
            } or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The category must exist.
            - If new_parent_category_id is not None/blank, it must reference an existing Category in the same group.
            - Cannot introduce cycles in category hierarchy (category cannot be made child of itself or any of its descendants).
        """
        # Check the category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist"}

        category = self.categories[category_id]
        group_id = category["group_id"]

        # Handle 'removal' of parent (root/top-level)
        if not new_parent_category_id:
            self.categories[category_id]["parent_category_id"] = None
            return {"success": True, "message": "Category reparented successfully"}

        # Check that new parent exists
        if new_parent_category_id not in self.categories:
            return {"success": False, "error": "New parent category does not exist"}

        new_parent = self.categories[new_parent_category_id]

        # Check that new parent is in the same group
        if new_parent["group_id"] != group_id:
            return {"success": False, "error": "New parent category is not in the same group"}

        # Check for cycles: walk up from new_parent to root, ensure we don't see category_id
        check_id = new_parent_category_id
        while check_id:
            if check_id == category_id:
                return {"success": False, "error": "Reparenting would create a cycle in the category hierarchy"}
            parent_id = self.categories[check_id].get("parent_category_id")
            check_id = parent_id if parent_id else None

        # All checks passed, perform the update
        self.categories[category_id]["parent_category_id"] = new_parent_category_id
        return {"success": True, "message": "Category reparented successfully"}


class ChatbotCategoryManagementSystem(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "category_groups" and isinstance(copied, dict):
                normalized = {}
                for raw_key, group_info in copied.items():
                    if not isinstance(group_info, dict):
                        continue
                    public_group_id = group_info.get("group_id")
                    normalized[public_group_id or raw_key] = group_info
                copied = normalized
            setattr(env, key, copied)

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

    def list_all_category_groups(self, **kwargs):
        return self._call_inner_tool('list_all_category_groups', kwargs)

    def get_category_group_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_group_by_id', kwargs)

    def list_categories_by_group(self, **kwargs):
        return self._call_inner_tool('list_categories_by_group', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_child_categories(self, **kwargs):
        return self._call_inner_tool('list_child_categories', kwargs)

    def check_group_id_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_group_id_uniqueness', kwargs)

    def check_category_id_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_category_id_uniqueness', kwargs)

    def validate_category_parent_reference(self, **kwargs):
        return self._call_inner_tool('validate_category_parent_reference', kwargs)

    def add_category_group(self, **kwargs):
        return self._call_inner_tool('add_category_group', kwargs)

    def update_category_group(self, **kwargs):
        return self._call_inner_tool('update_category_group', kwargs)

    def delete_category_group(self, **kwargs):
        return self._call_inner_tool('delete_category_group', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)

    def update_category_metadata(self, **kwargs):
        return self._call_inner_tool('update_category_metadata', kwargs)

    def reparent_category(self, **kwargs):
        return self._call_inner_tool('reparent_category', kwargs)
