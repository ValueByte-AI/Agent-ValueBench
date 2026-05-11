# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class MaterialInfo(TypedDict):
    material_id: str
    title: str
    type: str
    authors: List[str]
    publication_year: int
    metadata: Dict[str, str]  # e.g., subject, publisher

class CopyInfo(TypedDict):
    copy_id: str
    material_id: str
    collection_id: str
    status: str  # e.g., 'available', 'checked out', 'reserved', 'missing'
    acquisition_date: str
    location: str

class CollectionInfo(TypedDict):
    collection_id: str
    name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Materials: {material_id: MaterialInfo}
        self.materials: Dict[str, MaterialInfo] = {}

        # Copies/Items: {copy_id: CopyInfo}
        self.copies: Dict[str, CopyInfo] = {}

        # Collections: {collection_id: CollectionInfo}
        self.collections: Dict[str, CollectionInfo] = {}

        # --- Constraints ---
        # - Each copy (item) must be associated with an existing material record.
        # - A copy must belong to one and only one collection.
        # - Material identifiers (material_id, serial ID, etc.) must be unique.
        # - Collections must exist before items can be assigned to them.
        # - Item status must reflect its availability or circulation state.

    def get_material_by_id(self, material_id: str) -> dict:
        """
        Retrieve bibliographic information for a material using its unique material_id.

        Args:
            material_id (str): The unique identifier for the material.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": MaterialInfo  # All metadata about the material
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Material not found"
                    }

        Constraints:
            - material_id must exist in the system.
        """
        if material_id not in self.materials:
            return { "success": False, "error": "Material not found" }
        return { "success": True, "data": self.materials[material_id] }

    def get_material_by_title(self, title: str) -> dict:
        """
        Search for material(s) by exact title and retrieve their details.

        Args:
            title (str): The title to search for materials.

        Returns:
            dict: {
                "success": True,
                "data": List[MaterialInfo]  # List of matching material records (may be empty if no match)
            }
            or
            {
                "success": False,
                "error": str  # Reason for error (e.g., invalid input)
            }

        Constraints:
            - Title should be a non-empty string.
            - Returns all materials whose title exactly matches the query.
        """
        if not isinstance(title, str) or not title.strip():
            return { "success": False, "error": "Title must be a non-empty string" }

        result = [
            material_info
            for material_info in self.materials.values()
            if material_info["title"] == title
        ]
        return { "success": True, "data": result }

    def list_all_materials(self) -> dict:
        """
        List all material records in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MaterialInfo]  # List of all materials in the system (may be empty).
            }

        Constraints:
            None (simple retrieval/query; no modification).
        """
        all_materials = list(self.materials.values())
        return {
            "success": True,
            "data": all_materials
        }

    def get_collection_by_name(self, name: str) -> dict:
        """
        Retrieve collection information using the collection's name.

        Args:
            name (str): The name of the collection to look up.

        Returns:
            dict: 
                - On success: { "success": True, "data": CollectionInfo }
                - On failure: { "success": False, "error": "Collection not found" }
        Constraints:
            - No constraint enforces uniqueness on collection name, so returns the first found.
        """
        for collection in self.collections.values():
            if collection["name"] == name:
                return {"success": True, "data": collection}
        return {"success": False, "error": "Collection not found"}

    def get_collection_by_id(self, collection_id: str) -> dict:
        """
        Retrieve collection details using the collection_id.

        Args:
            collection_id (str): The unique identifier for the collection.

        Returns:
            dict: 
                - On success:
                    { "success": True, "data": CollectionInfo }
                - On failure:
                    { "success": False, "error": "Collection not found" }

        Constraints:
            - The collection_id must exist in the system.
        """
        collection = self.collections.get(collection_id)
        if collection is not None:
            return { "success": True, "data": collection }
        else:
            return { "success": False, "error": "Collection not found" }

    def list_all_collections(self) -> dict:
        """
        List all defined collections in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[CollectionInfo]  # List of all collections (possibly empty)
            }
        """
        all_collections = list(self.collections.values())
        return { "success": True, "data": all_collections }

    def get_copy_by_id(self, copy_id: str) -> dict:
        """
        Retrieve the metadata of a specific copy (item) by its copy_id.
    
        Args:
            copy_id (str): The unique identifier of the item/copy.

        Returns:
            dict:
              - On success: { "success": True, "data": CopyInfo }
              - On failure: { "success": False, "error": "Copy not found" }
        Constraints:
            - The copy_id must exist in the library's record of copies/items.
        """
        if not copy_id or copy_id not in self.copies:
            return { "success": False, "error": "Copy not found" }
        return { "success": True, "data": self.copies[copy_id] }

    def list_copies_by_material(self, material_id: str) -> dict:
        """
        List all copy records (items) associated with a given material_id.

        Args:
            material_id (str): Unique identifier of the material.

        Returns:
            dict:
              - success: True if operation succeeded; False if material_id does not exist.
              - data: List of CopyInfo objects (may be empty if no copies exist).
              - error: Optional error message if operation failed.

        Constraints:
            - material_id must exist in the materials catalog.
        """
        if material_id not in self.materials:
            return { "success": False, "error": "Material ID does not exist." }

        result = [
            copy_info for copy_info in self.copies.values()
            if copy_info["material_id"] == material_id
        ]
        return { "success": True, "data": result }

    def list_copies_by_collection(self, collection_id: str) -> dict:
        """
        List all copies/items assigned to a specified collection.

        Args:
            collection_id (str): The identifier of the collection.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[CopyInfo]  # All item records in the collection (may be empty),
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason, e.g., collection does not exist.
                }

        Constraints:
            - The specified collection must exist.
        """
        if collection_id not in self.collections:
            return { "success": False, "error": "Collection does not exist" }

        items = [
            copy_info for copy_info in self.copies.values()
            if copy_info["collection_id"] == collection_id
        ]

        return { "success": True, "data": items }

    def check_material_id_unique(self, material_id: str) -> dict:
        """
        Check whether a given material_id is unique in the system.

        Args:
            material_id (str): The material ID to check for uniqueness.

        Returns:
            dict: {
                'success': True,
                'unique': bool  # True if not present in the catalog, False otherwise
            }
            Or, if input is invalid:
            {
                'success': False,
                'error': str
            }

        Constraints:
            - material_id must be a non-empty string.
        """
        if not material_id or not isinstance(material_id, str):
            return { "success": False, "error": "Invalid material_id provided." }
    
        is_unique = material_id not in self.materials
        return { "success": True, "unique": is_unique }

    def check_copy_id_unique(self, copy_id: str) -> dict:
        """
        Check whether the provided copy_id is unique in the system.

        Args:
            copy_id (str): The proposed identifier for a copy (item).

        Returns:
            dict: {
                "success": True,
                "data": bool   # True if unique (not found), False if already exists
            }
            or
            {
                "success": False,
                "error": str   # If input is invalid (e.g., empty string)
            }

        Constraints:
            - copy_id should not be empty.
            - Does not modify system state.
        """
        if not isinstance(copy_id, str) or copy_id.strip() == "":
            return {"success": False, "error": "copy_id must be a non-empty string"}
        is_unique = copy_id not in self.copies
        return {"success": True, "data": is_unique}

    def get_copies_by_status(self, status: str) -> dict:
        """
        List all copies filtered by the provided status.

        Args:
            status (str): The status to filter copies by. Must be one of:
                          'available', 'checked out', 'reserved', 'missing'.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[CopyInfo]  # May be empty if no matching copies.
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g. invalid status.
                  }

        Constraints:
            - The status must be one of the allowed statuses.
        """
        allowed_statuses = {"available", "checked out", "reserved", "missing"}
        if status not in allowed_statuses:
            return {"success": False, "error": "Invalid status"}
    
        result = [
            copy_info for copy_info in self.copies.values()
            if copy_info["status"] == status
        ]
        return {"success": True, "data": result}

    def add_material(
        self,
        material_id: str,
        title: str,
        type: str,
        authors: list,
        publication_year: int,
        metadata: dict
    ) -> dict:
        """
        Add a new material record to the library catalog.

        Args:
            material_id (str): Unique identifier for the material.
            title (str): Material title.
            type (str): Material type (e.g., 'Book', 'Serial', 'Media').
            authors (List[str]): List of authors.
            publication_year (int): Year of publication.
            metadata (Dict[str, str]): Optional additional metadata (e.g., subject, publisher).

        Returns:
            dict: {
                "success": True,
                "message": "Material added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - material_id must be unique.
            - All required fields must be non-empty.
        """
        # Check material_id uniqueness
        if material_id in self.materials:
            return { "success": False, "error": "Material ID already exists." }
        if not material_id or not isinstance(material_id, str):
            return { "success": False, "error": "Material ID must be a non-empty string." }
        if not title or not isinstance(title, str):
            return { "success": False, "error": "Title must be a non-empty string." }
        if not type or not isinstance(type, str):
            return { "success": False, "error": "Type must be a non-empty string." }
        if (
            not isinstance(authors, list)
            or not authors
            or not all(isinstance(a, str) and a.strip() for a in authors)
        ):
            return { "success": False, "error": "Authors must be a non-empty list of non-empty strings." }
        if not isinstance(publication_year, int):
            return { "success": False, "error": "Publication year must be an integer." }
        if not isinstance(metadata, dict):
            return { "success": False, "error": "Metadata must be a dictionary." }

        self.materials[material_id] = {
            "material_id": material_id,
            "title": title,
            "type": type,
            "authors": authors,
            "publication_year": publication_year,
            "metadata": metadata
        }
        return { "success": True, "message": "Material added successfully." }

    def add_copy(
        self,
        copy_id: str,
        material_id: str,
        collection_id: str,
        status: str,
        acquisition_date: str,
        location: str
    ) -> dict:
        """
        Add a new copy/item associated with an existing material and assign it to an existing collection.

        Args:
            copy_id (str): Unique identifier for this copy.
            material_id (str): ID of an existing material to associate.
            collection_id (str): ID of existing collection to assign this copy.
            status (str): Initial status of the copy (e.g., 'available').
            acquisition_date (str): Acquisition date string.
            location (str): Location within library.

        Returns:
            dict: Success or error information.
                { "success": True, "message": "Copy added successfully." }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - copy_id must be unique.
            - material_id must exist in catalog.
            - collection_id must exist in catalog.
            - Item is assigned to exactly one collection.
        """
        # Check unique copy_id
        if copy_id in self.copies:
            return { "success": False, "error": "Copy ID already exists." }
        # Check material_id exists
        if material_id not in self.materials:
            return { "success": False, "error": "Material ID does not exist." }
        # Check collection_id exists
        if collection_id not in self.collections:
            return { "success": False, "error": "Collection ID does not exist." }

        new_copy: CopyInfo = {
            "copy_id": copy_id,
            "material_id": material_id,
            "collection_id": collection_id,
            "status": status,
            "acquisition_date": acquisition_date,
            "location": location,
        }
        self.copies[copy_id] = new_copy
        return { "success": True, "message": "Copy added successfully." }

    def add_collection(self, collection_id: str, name: str, description: str) -> dict:
        """
        Create a new collection in the catalog.

        Args:
            collection_id (str): Unique identifier for the collection.
            name (str): Name of the collection.
            description (str): Description of the collection.

        Returns:
            dict: {
                'success': True,
                'message': "Collection added successfully"
            }
            or
            {
                'success': False,
                'error': <error details>
            }

        Constraints:
            - collection_id must be unique.
        """
        if collection_id in self.collections:
            return {
                "success": False,
                "error": "A collection with this collection_id already exists."
            }

        self.collections[collection_id] = {
            "collection_id": collection_id,
            "name": name,
            "description": description
        }

        return {
            "success": True,
            "message": "Collection added successfully"
        }

    def update_copy_status(self, copy_id: str, new_status: str) -> dict:
        """
        Change the status of a copy/item in the library catalog.

        Args:
            copy_id (str): The identifier for the copy/item.
            new_status (str): The desired status to assign.
                Allowed values: 'available', 'checked out', 'reserved', 'missing'.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Status of copy <copy_id> updated to <new_status>." }
                On error:
                    { "success": False, "error": "Reason for failure." }

        Constraints:
            - copy_id must exist in the system.
            - new_status must be a valid status value.
        """
        allowed_statuses = {'available', 'checked out', 'reserved', 'missing'}
        if copy_id not in self.copies:
            return { "success": False, "error": "Copy not found." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status value." }
        self.copies[copy_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Status of copy {copy_id} updated to {new_status}."
        }

    def update_copy_location(self, copy_id: str, new_location: str) -> dict:
        """
        Change the location metadata of a copy.

        Args:
            copy_id (str): The unique identifier of the copy/item to update.
            new_location (str): The new location to assign to the copy.

        Returns:
            dict:
                - If successful: { "success": True, "message": "Copy location updated." }
                - If copy not found: { "success": False, "error": "Copy not found." }

        Constraints:
            - The specified copy_id must exist in the system.
        """
        if copy_id not in self.copies:
            return { "success": False, "error": "Copy not found." }
        self.copies[copy_id]["location"] = new_location
        return { "success": True, "message": "Copy location updated." }

    def update_material_metadata(self, material_id: str, metadata_updates: Dict[str, str]) -> dict:
        """
        Update metadata (such as subject, publisher, etc.) for an existing material.

        Args:
            material_id (str): The unique identifier of the material to update.
            metadata_updates (Dict[str, str]): Key-value pairs to update/add in the material's metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Metadata updated for material <material_id>"
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - Material with given material_id must exist.
            - Existing metadata keys may be overwritten; new keys are added.
        """
        material = self.materials.get(material_id)
        if material is None:
            return { "success": False, "error": "Material does not exist" }
        if not isinstance(material.get("metadata"), dict):
            material["metadata"] = {}
        # Perform update
        material["metadata"].update(metadata_updates)
        return { "success": True, "message": f"Metadata updated for material {material_id}" }

    def assign_copy_to_collection(self, copy_id: str, new_collection_id: str) -> dict:
        """
        Reassign a copy/item (identified by copy_id) to a different collection (new_collection_id).
        Enforces that each copy belongs to exactly one (existing) collection.

        Args:
            copy_id (str): The unique identifier of the copy/item to reassign.
            new_collection_id (str): The collection_id of the new collection.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation that the copy was reassigned
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - copy_id must exist in the catalog.
            - new_collection_id must exist in the collections.
            - Each copy belongs to exactly one collection.
        """
        if copy_id not in self.copies:
            return {"success": False, "error": "Copy/item not found"}
        if new_collection_id not in self.collections:
            return {"success": False, "error": "Target collection does not exist"}
        current_collection_id = self.copies[copy_id]["collection_id"]
        if current_collection_id == new_collection_id:
            return {
                "success": True, 
                "message": "Copy is already assigned to the specified collection"
            }
        self.copies[copy_id]["collection_id"] = new_collection_id
        return {"success": True, "message": "Copy reassigned to new collection"}

    def delete_copy(self, copy_id: str) -> dict:
        """
        Remove a copy/item from the catalog.

        Args:
            copy_id (str): The identifier of the copy/item to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Copy <copy_id> deleted."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The copy_id must exist in the catalog for deletion.
        """
        if copy_id not in self.copies:
            return {"success": False, "error": f"Copy with id '{copy_id}' does not exist."}

        del self.copies[copy_id]
        return {"success": True, "message": f"Copy '{copy_id}' deleted."}

    def delete_material(self, material_id: str) -> dict:
        """
        Remove a material record from the catalog, if it is not referenced by any existing copies.

        Args:
            material_id (str): The unique identifier of the material to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Material <material_id> successfully deleted."
            }
            OR
            {
                "success": False,
                "error": "Material not found."
            }
            OR
            {
                "success": False,
                "error": "Material is still referenced by existing copies."
            }

        Constraints:
            - Cannot delete a material that is referenced by one or more copies.
        """
        if material_id not in self.materials:
            return { "success": False, "error": "Material not found." }

        # Check if any copies reference this material
        for copy_info in self.copies.values():
            if copy_info["material_id"] == material_id:
                return {
                    "success": False,
                    "error": "Material is still referenced by existing copies."
                }

        # Safe to delete
        del self.materials[material_id]
        return {
            "success": True,
            "message": f"Material {material_id} successfully deleted."
        }

    def delete_collection(self, collection_id: str) -> dict:
        """
        Remove a collection from the system.

        Args:
            collection_id (str): The unique identifier of the collection to remove.

        Returns:
            dict: 
                - {"success": True, "message": "Collection <collection_id> successfully deleted."}
                - {"success": False, "error": "<reason>"}

        Constraints:
            - The collection must exist.
            - The collection must not have any member copies/items (enforced by checking for any copy with that collection_id).
            - Member copies must be reassigned or removed before deleting the collection.
        """
        if collection_id not in self.collections:
            return {"success": False, "error": "Collection does not exist."}

        member_copies = [
            copy for copy in self.copies.values()
            if copy["collection_id"] == collection_id
        ]
        if member_copies:
            return {
                "success": False,
                "error": "Collection cannot be deleted: it still contains one or more copies/items."
            }

        del self.collections[collection_id]
        return {
            "success": True,
            "message": f"Collection {collection_id} successfully deleted."
        }


class LibraryCatalogManagementSystem(BaseEnv):
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

    def get_material_by_id(self, **kwargs):
        return self._call_inner_tool('get_material_by_id', kwargs)

    def get_material_by_title(self, **kwargs):
        return self._call_inner_tool('get_material_by_title', kwargs)

    def list_all_materials(self, **kwargs):
        return self._call_inner_tool('list_all_materials', kwargs)

    def get_collection_by_name(self, **kwargs):
        return self._call_inner_tool('get_collection_by_name', kwargs)

    def get_collection_by_id(self, **kwargs):
        return self._call_inner_tool('get_collection_by_id', kwargs)

    def list_all_collections(self, **kwargs):
        return self._call_inner_tool('list_all_collections', kwargs)

    def get_copy_by_id(self, **kwargs):
        return self._call_inner_tool('get_copy_by_id', kwargs)

    def list_copies_by_material(self, **kwargs):
        return self._call_inner_tool('list_copies_by_material', kwargs)

    def list_copies_by_collection(self, **kwargs):
        return self._call_inner_tool('list_copies_by_collection', kwargs)

    def check_material_id_unique(self, **kwargs):
        return self._call_inner_tool('check_material_id_unique', kwargs)

    def check_copy_id_unique(self, **kwargs):
        return self._call_inner_tool('check_copy_id_unique', kwargs)

    def get_copies_by_status(self, **kwargs):
        return self._call_inner_tool('get_copies_by_status', kwargs)

    def add_material(self, **kwargs):
        return self._call_inner_tool('add_material', kwargs)

    def add_copy(self, **kwargs):
        return self._call_inner_tool('add_copy', kwargs)

    def add_collection(self, **kwargs):
        return self._call_inner_tool('add_collection', kwargs)

    def update_copy_status(self, **kwargs):
        return self._call_inner_tool('update_copy_status', kwargs)

    def update_copy_location(self, **kwargs):
        return self._call_inner_tool('update_copy_location', kwargs)

    def update_material_metadata(self, **kwargs):
        return self._call_inner_tool('update_material_metadata', kwargs)

    def assign_copy_to_collection(self, **kwargs):
        return self._call_inner_tool('assign_copy_to_collection', kwargs)

    def delete_copy(self, **kwargs):
        return self._call_inner_tool('delete_copy', kwargs)

    def delete_material(self, **kwargs):
        return self._call_inner_tool('delete_material', kwargs)

    def delete_collection(self, **kwargs):
        return self._call_inner_tool('delete_collection', kwargs)
