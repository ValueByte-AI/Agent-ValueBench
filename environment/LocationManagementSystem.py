# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict, Tuple
from collections import deque



class LocationInfo(TypedDict):
    location_id: str
    parent_location_id: Optional[str]
    level: int
    prop: dict  # Additional meta-data for the location

class LocationNameInfo(TypedDict):
    location_id: str
    language: str
    name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing hierarchical locations and their multilingual names.

        Constraints:
        - Each location_id must be unique.
        - parent_location_id refers to another valid location or None (for root).
        - level reflects the depth in the hierarchy and must be consistent within the structure.
        - No cycles in parent-child links (tree/DAG).
        - Name retrieval only for supported languages per location.
        """

        # Locations: {location_id: LocationInfo}
        # Fields: location_id, parent_location_id, level, prop
        self.locations: Dict[str, LocationInfo] = {}

        # Location names: {(location_id, language): LocationNameInfo}
        # Fields: location_id, language, name
        self.location_names: Dict[Tuple[str, str], LocationNameInfo] = {}


    def get_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve all metadata (LocationInfo) for a given location_id.

        Args:
            location_id (str): Unique identifier for the location.

        Returns:
            dict: {
                "success": True,
                "data": LocationInfo,  # If location_id is found
            }
            or
            {
                "success": False,
                "error": str  # If the location_id does not exist
            }

        Constraints:
            - location_id must exist in the environment.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }

        return { "success": True, "data": self.locations[location_id] }

    def get_location_name(self, location_id: str, language: str) -> dict:
        """
        Retrieve the name of a location in the specified language, if available.

        Args:
            location_id (str): The unique identifier of the location.
            language (str): The language code to retrieve the name in.

        Returns:
            dict: 
               - On success: {
                    "success": True,
                    "data": LocationNameInfo
                 }
               - On failure (location/language not found): {
                    "success": False,
                    "error": str
                 }

        Constraints:
            - location_id must exist in the system.
            - Name retrieval only succeeds for supported languages per location (i.e., entry must exist in location_names).
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location does not exist"}

        key = (location_id, language)
        if key in self.location_names:
            return {"success": True, "data": self.location_names[key]}
        else:
            return {"success": False, "error": "Name for this language/location is not available"}

    def get_child_locations(self, location_id: str) -> dict:
        """
        List all direct child locations for a given location_id.

        Args:
            location_id (str): The ID of the parent location.

        Returns:
            dict: 
                - { "success": True, "data": [LocationInfo, ...] } on success (data may be empty if no children),
                - { "success": False, "error": "Location not found" } if location_id is invalid.

        Constraints:
            - location_id must exist in the system.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }

        children = [
            location_info
            for location_info in self.locations.values()
            if location_info["parent_location_id"] == location_id
        ]
        return { "success": True, "data": children }

    def get_parent_location(self, location_id: str) -> dict:
        """
        Retrieve the immediate parent LocationInfo of the given location_id.

        Args:
            location_id (str): The location's unique identifier.

        Returns:
            dict:
                - {"success": True, "data": LocationInfo} if parent exists
                - {"success": True, "data": None} if location is root (no parent)
                - {"success": False, "error": str} if location_id invalid or parent data missing

        Constraints:
            - location_id must exist in the system.
            - Parent location_id (if present) must exist, else error.
        """
        # Check if the location_id exists.
        location = self.locations.get(location_id)
        if not location:
            return {"success": False, "error": "Location ID does not exist"}

        parent_location_id = location.get("parent_location_id")
        if parent_location_id is None:
            # Root location: no parent
            return {"success": True, "data": None}

        parent_info = self.locations.get(parent_location_id)
        if not parent_info:
            return {"success": False, "error": "Parent location data missing"}
        return {"success": True, "data": parent_info}

    def get_ancestor_locations(self, location_id: str) -> dict:
        """
        Retrieve all ancestor locations up to the root for the given location_id.

        Args:
            location_id (str): The ID of the location from which to start tracing ancestors.

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo],  # Ordered from immediate parent to root (excluding the input location)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. location not found, hierarchy error
            }

        Constraints:
            - The location_id must exist.
            - No cycles in the hierarchy (if a cycle is detected, error reported).
        """

        if location_id not in self.locations:
            return {"success": False, "error": "Location not found"}

        ancestor_list = []
        visited = set()
        current_id = location_id

        while True:
            loc_info = self.locations.get(current_id)
            if not loc_info:
                # Shouldn't happen, means corrupt hierarchy
                return {"success": False, "error": "Hierarchy corrupt: missing parent location"}
            parent_id = loc_info.get("parent_location_id")
            if parent_id is None:
                # Reached root
                break
            if parent_id in visited:
                return {"success": False, "error": "Cycle detected in hierarchy"}
            if parent_id not in self.locations:
                return {"success": False, "error": "Hierarchy corrupt: missing ancestor location"}
            ancestor_list.append(self.locations[parent_id])
            visited.add(parent_id)
            current_id = parent_id

        return {"success": True, "data": ancestor_list}

    def get_descendant_locations(self, location_id: str) -> dict:
        """
        Retrieve all descendant locations (at any depth) for a given location_id.

        Args:
            location_id (str): The unique identifier of the location whose descendants are to be found.

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # All descendant locations. May be empty if none.
            }
            or
            {
                "success": False,
                "error": str  # Description of the reason for failure
            }

        Constraints:
            - location_id must exist in self.locations.
            - Structure is acyclic; traversal is guaranteed to terminate.
        """
        if location_id not in self.locations:
            return { "success": False, "error": f"Location '{location_id}' does not exist" }

        descendants = []
        to_visit = [location_id]
        visited = set()

        while to_visit:
            current_id = to_visit.pop()
            # Find direct children
            children = [
                loc for loc in self.locations.values()
                if loc["parent_location_id"] == current_id
            ]
            for child in children:
                cid = child["location_id"]
                if cid not in visited:
                    descendants.append(child)
                    to_visit.append(cid)
                    visited.add(cid)
        return { "success": True, "data": descendants }

    def list_locations_by_level(self, level: int) -> dict:
        """
        Retrieve all locations at a specific hierarchy level.

        Args:
            level (int): The hierarchical level to retrieve locations for (typically 0 or positive).

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # List of LocationInfo for the given level (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. invalid level
            }

        Constraints:
            - The input `level` must be a non-negative integer.
            - Output is the full info for all locations with that level.
        """
        if not isinstance(level, int) or level < 0:
            return {"success": False, "error": "Invalid input: level must be a non-negative integer."}

        results = [
            location_info
            for location_info in self.locations.values()
            if location_info["level"] == level
        ]
        return {"success": True, "data": results}

    def get_hierarchical_structure(self, location_id: str, language: str = None) -> dict:
        """
        Retrieve the full hierarchical subtree starting from the specified location_id, including for each node:
            - All location info
            - Optionally the location name in a specified language (if available)
            - Children recursively

        Args:
            location_id (str): Root location for the hierarchy query.
            language (str, optional): If supplied, provide the name in this language (if defined) per location.

        Returns:
            dict: {
                "success": True,
                "data": <tree-structured dict rooted at location_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Root location must exist.
            - Each child is included under 'children'.
            - If language is requested, include 'name' field in each node where available.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }

        def build_subtree(loc_id):
            loc_info = dict(self.locations[loc_id])  # Copy fields
            # Optionally add name
            if language is not None:
                name_info = self.location_names.get((loc_id, language))
                if name_info:
                    loc_info['name'] = name_info['name']
            # Find children
            children = [
                build_subtree(child_id)
                for child_id, child_info in self.locations.items()
                if child_info['parent_location_id'] == loc_id
            ]
            loc_info['children'] = children
            return loc_info

        tree = build_subtree(location_id)
        return { "success": True, "data": tree }

    def is_supported_language_for_location(self, location_id: str, language: str) -> dict:
        """
        Check if a specified language is supported (i.e., a name exists) for a location.

        Args:
            location_id (str): Unique location identifier.
            language (str): Language code to check.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": { "supported": bool }
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Fails if location_id does not exist.
            - Supported means a LocationName exists for (location_id, language).
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }

        supported = (location_id, language) in self.location_names
        return {
            "success": True,
            "data": { "supported": supported }
        }

    def add_location(
        self,
        location_id: str,
        parent_location_id: Optional[str],
        level: int,
        prop: dict
    ) -> dict:
        """
        Add a new location to the system, ensuring uniqueness and correct hierarchy constraints.

        Args:
            location_id (str): Unique identifier for the location.
            parent_location_id (Optional[str]): ID of the parent location, or None for root.
            level (int): The depth in the hierarchy. Should be 0 for root, else parent's level + 1.
            prop (dict): Meta-data for the location.

        Returns:
            dict: {
                "success": True,
                "message": "Location <location_id> added."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - location_id must be unique (not already in self.locations).
            - parent_location_id must be None (for root) or an existing location_id.
            - level must be 0 if root, else parent level + 1.
            - parent_location_id cannot be the same as location_id (no cycles).
        """
        # Enforce uniqueness of location_id
        if location_id in self.locations:
            return {"success": False, "error": "Location ID already exists."}

        # Root node
        if parent_location_id is None:
            if level != 0:
                return {"success": False, "error": "Level must be 0 for root location."}
        else:
            # parent_location_id must not be same as location_id
            if parent_location_id == location_id:
                return {"success": False, "error": "A location cannot be its own parent."}
            if parent_location_id not in self.locations:
                return {"success": False, "error": "Parent location does not exist."}
            parent_level = self.locations[parent_location_id]['level']
            if level != parent_level + 1:
                return {"success": False, "error": "Level must be parent's level + 1."}

        # Add location
        self.locations[location_id] = {
            "location_id": location_id,
            "parent_location_id": parent_location_id,
            "level": level,
            "prop": prop if prop is not None else {}
        }
        return {"success": True, "message": f"Location {location_id} added."}

    def update_location(
        self,
        location_id: str, 
        parent_location_id: Optional[str] = None, 
        level: Optional[int] = None,
        prop: Optional[dict] = None
    ) -> dict:
        """
        Update the metadata, parent, or level of an existing location.

        Args:
            location_id (str): The unique ID of the location to update.
            parent_location_id (Optional[str]): New parent location ID (None for root).
            level (Optional[int]): New hierarchy level for this location.
            prop (Optional[dict]): New property dictionary for this location.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Location updated." }
              - On failure: { "success": False, "error": <reason str> }

        Constraints:
            - location_id must exist.
            - parent_location_id must exist or be None, but not self.
            - Level consistent: if parent is specified, level == parent's level + 1.
            - No cycles can be introduced by reparenting.
        """
        # Check that the location exists
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist." }

        # Prepare update
        loc = self.locations[location_id]
        orig_parent = loc["parent_location_id"]
        orig_level = loc["level"]

        # Handle parent update
        if parent_location_id is not None:
            if parent_location_id == location_id:
                return { "success": False, "error": "Location cannot be its own parent." }
            if parent_location_id is not None and parent_location_id not in self.locations:
                return { "success": False, "error": "Parent location does not exist." }
            # Check for cycle: walk up from proposed parent to root;
            ancestor = parent_location_id
            while ancestor is not None:
                if ancestor == location_id:
                    return { "success": False, "error": "Cycle detected; cannot reparent." }
                ancestor = self.locations[ancestor]["parent_location_id"]

        # Handle level update consistency
        new_level = orig_level
        if level is not None:
            if not isinstance(level, int) or level < 0:
                return { "success": False, "error": "Level must be a non-negative integer." }
            new_level = level
        if parent_location_id is not None:
            if parent_location_id is None:
                expected_level = 0
            else:
                expected_level = self.locations[parent_location_id]["level"] + 1
            if level is not None and new_level != expected_level:
                return { "success": False, "error": "Level inconsistent with parent." }
            elif level is None and new_level != expected_level:
                new_level = expected_level  # auto-fix if only parent is set (optional)
        # If only level is supplied and parent not changing, check consistency with current parent:
        elif level is not None and orig_parent is not None:
            expected_level = self.locations[orig_parent]["level"] + 1
            if new_level != expected_level:
                return { "success": False, "error": "Level inconsistent with parent." }
        elif level is not None and orig_parent is None:
            if new_level != 0:
                return { "success": False, "error": "Root location must have level 0." }

        # Update prop if provided
        if prop is not None:
            loc["prop"] = prop

        # Update parent if provided
        if parent_location_id is not None:
            loc["parent_location_id"] = parent_location_id

        # Update level if provided (or auto-fixed above)
        if new_level != orig_level:
            loc["level"] = new_level

        # Write back
        self.locations[location_id] = loc

        return { "success": True, "message": "Location updated." }

    def delete_location(self, location_id: str) -> dict:
        """
        Removes a location and all its descendants from the system (cascading delete).
        Also removes all associated LocationNameInfo for those locations.

        Args:
            location_id (str): The unique ID of the location to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Location <id> and its descendants deleted." }
                - On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - location_id must exist.
            - All descendants are removed recursively (cascading delete).
            - All names for deleted locations are also removed.
            - No cycles are assumed in parent-child relationships.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }
    
        # Find all descendant location_ids recursively, including self
        to_delete = set()
        def collect_descendants(lid: str):
            to_delete.add(lid)
            for child_id, info in self.locations.items():
                if info["parent_location_id"] == lid:
                    collect_descendants(child_id)
        collect_descendants(location_id)

        # Delete from self.locations
        for lid in to_delete:
            self.locations.pop(lid, None)
    
        # Delete all names associated with deleted locations
        names_to_delete = [key for key in self.location_names if key[0] in to_delete]
        for key in names_to_delete:
            self.location_names.pop(key, None)

        return { 
            "success": True, 
            "message": f"Location '{location_id}' and {len(to_delete)-1} descendant(s) deleted." 
        }

    def add_location_name(self, location_id: str, language: str, name: str) -> dict:
        """
        Add a name for a location in a given language.

        Args:
            location_id (str): Unique identifier of the location.
            language (str): Language code (e.g., "en", "fr") for the name.
            name (str): Name of the location in the specified language.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Location name added for location_id in language."}
                On failure:
                    {"success": False, "error": <reason>}
        Constraints:
            - location_id must exist in self.locations.
            - (location_id, language) must NOT already exist in self.location_names.
            - No explicit restriction on language code or name in the environment.
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location does not exist."}

        key = (location_id, language)
        if key in self.location_names:
            return {"success": False, "error": "Name for location in this language already exists."}

        self.location_names[key] = {
            "location_id": location_id,
            "language": language,
            "name": name
        }

        return {"success": True, "message": f"Location name added for {location_id} in {language}."}

    def update_location_name(self, location_id: str, language: str, name: str) -> dict:
        """
        Update the name for a given location in a specific language.

        Args:
            location_id (str): Unique identifier of the location.
            language (str): Target language for which the name is being updated.
            name (str): The new name for the location.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Location name updated for location_id <location_id> in language <language>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Location name for this language does not exist."
                    }

        Constraints:
            - The (location_id, language) entry must already exist.
            - Only supported languages for a location may be updated.
        """
        key = (location_id, language)
        if key not in self.location_names:
            return {
                "success": False,
                "error": "Location name for this language does not exist."
            }
        self.location_names[key]["name"] = name
        return {
            "success": True,
            "message": f"Location name updated for location_id {location_id} in language {language}."
        }

    def delete_location_name(self, location_id: str, language: str) -> dict:
        """
        Remove the name for a location in a specific language.

        Args:
            location_id (str): The unique identifier for the location.
            language (str): The language code of the name to remove.

        Returns:
            dict: {
                "success": True,
                "message": f"Location name deleted for location_id={location_id}, language={language}"
            }
            or
            {
                "success": False,
                "error": "Location name in specified language does not exist"
            }

        Constraints:
            - The (location_id, language) pair must exist in location_names to be removed.
            - Operation does not affect location hierarchy or other languages.
        """
        key = (location_id, language)
        if key not in self.location_names:
            return { "success": False, "error": "Location name in specified language does not exist" }

        del self.location_names[key]
        return {
            "success": True,
            "message": f"Location name deleted for location_id={location_id}, language={language}"
        }

    def move_location(self, location_id: str, new_parent_location_id: Optional[str]) -> dict:
        """
        Change the parent of a location, ensuring no cycles, correct hierarchy, and correct level adjustment.

        Args:
            location_id (str): The location to move.
            new_parent_location_id (Optional[str]): The new parent location's ID, or None for root.

        Returns:
            dict: 
                { "success": True, "message": "Location moved successfully." }
                OR
                { "success": False, "error": str }

        Constraints:
            - Both IDs must exist (unless new_parent_location_id is None, which means move to root).
            - Cannot move under self or any descendant (must not introduce cycle).
            - Level of moved node and all descendants must update.
            - If new_parent_location_id is None, level must be 0.
        """
        # Check location exists
        if location_id not in self.locations:
            return {"success": False, "error": "Location to move does not exist."}

        # Can't move under self
        if new_parent_location_id == location_id:
            return {"success": False, "error": "Cannot set a location as its own parent."}
    
        # Check new parent exists, unless moving to root
        if new_parent_location_id is not None and new_parent_location_id not in self.locations:
            return {"success": False, "error": "New parent location does not exist."}
    
        # Get list of all descendants of location_id (for cycle check and re-leveling)
        def get_all_descendants(loc_id):
            descendants = set()
            stack = [loc_id]
            while stack:
                current = stack.pop()
                child_ids = [
                    l_id for l_id, info in self.locations.items()
                    if info['parent_location_id'] == current
                ]
                descendants.update(child_ids)
                stack.extend(child_ids)
            return descendants

        descendants = get_all_descendants(location_id)
        # Moving under own descendant = cycle!
        if new_parent_location_id in descendants:
            return {"success": False, "error": "Cannot move location under one of its descendants (cycle detected)."}

        # Compute new level for moved node
        if new_parent_location_id is None:
            new_level = 0
        else:
            new_level = self.locations[new_parent_location_id]['level'] + 1

        level_delta = new_level - self.locations[location_id]['level']

        # Move location: set new parent and update level
        self.locations[location_id]['parent_location_id'] = new_parent_location_id
        self.locations[location_id]['level'] = new_level

        # Update levels for all descendants (by the level difference)
        queue = deque([(location_id, new_level)])  # (node_id, node_level)

        while queue:
            current_id, current_level = queue.popleft()
            # All direct children
            children = [
                l_id for l_id, info in self.locations.items()
                if info['parent_location_id'] == current_id
            ]
            for child_id in children:
                # Child level = parent level + 1
                self.locations[child_id]['level'] = self.locations[current_id]['level'] + 1
                queue.append((child_id, self.locations[child_id]['level']))

        return {"success": True, "message": "Location moved successfully."}

    def validate_hierarchy(self, starting_location_id: str = None) -> dict:
        """
        Validate the acyclicity and level consistency of the location hierarchy or a subtree.

        Args:
            starting_location_id (str, optional): Starting node for subtree validation.
                If None, checks the entire structure.

        Returns:
            dict: On success:
                      { "success": True, "message": "Hierarchy is acyclic and levels are consistent." }
                  On failure:
                      { "success": False, "error": <description(s)> }
        Constraints:
            - No cycles allowed in the hierarchy (tree/DAG).
            - Each location's `level` must be one more than its parent (or 0 for root).
            - parent_location_id must be either None (root) or a valid location_id.
        """
        # Build parent-child mapping
        children_map = {}
        for loc_id, loc in self.locations.items():
            parent = loc['parent_location_id']
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(loc_id)

        def get_roots():
            return children_map.get(None, [])

        # Which nodes to validate
        if starting_location_id:
            if starting_location_id not in self.locations:
                return {
                    "success": False, 
                    "error": f"Starting location_id '{starting_location_id}' does not exist."
                }
            roots = [starting_location_id]
        else:
            roots = get_roots()

        cyclic = False
        invalid_level_ids = []
        referenced_parent_missing = []
        visited = set()
        rec_stack = set()

        def dfs(loc_id, expected_level):
            nonlocal cyclic
            if loc_id in rec_stack:
                cyclic = True
                return
            loc = self.locations[loc_id]
            parent = loc['parent_location_id']
            actual_level = loc['level']
            if parent is None:
                if actual_level != 0:
                    invalid_level_ids.append(loc_id)
            else:
                if parent not in self.locations:
                    referenced_parent_missing.append(loc_id)
                else:
                    parent_level = self.locations[parent]['level']
                    if actual_level != parent_level + 1:
                        invalid_level_ids.append(loc_id)
            visited.add(loc_id)
            rec_stack.add(loc_id)
            for child_id in children_map.get(loc_id, []):
                dfs(child_id, actual_level + 1)
            rec_stack.remove(loc_id)

        for root_id in roots:
            dfs(root_id, 0)

        # Also check for disconnected cycles or orphans that were not visited
        if not starting_location_id:
            for loc_id in self.locations:
                if loc_id not in visited:
                    # Try to visit (could be disconnected component or orphan/cycle)
                    dfs(loc_id, 0)

        errors = []
        if cyclic:
            errors.append("Cycle detected in the location hierarchy.")
        if invalid_level_ids:
            errors.append(f"Locations with invalid level assignments: {invalid_level_ids}")
        if referenced_parent_missing:
            errors.append(f"Locations referencing missing parents: {referenced_parent_missing}")

        if errors:
            return {
                "success": False,
                "error": "; ".join(errors)
            }
        else:
            return {
                "success": True,
                "message": "Hierarchy is acyclic and levels are consistent."
            }


class LocationManagementSystem(BaseEnv):
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
            if key == "location_names" and isinstance(value, dict):
                normalized_location_names = {}
                for original_key, name_info in value.items():
                    if (
                        isinstance(name_info, dict)
                        and isinstance(name_info.get("location_id"), str)
                        and isinstance(name_info.get("language"), str)
                    ):
                        normalized_key = (name_info["location_id"], name_info["language"])
                    else:
                        normalized_key = original_key
                    normalized_location_names[normalized_key] = copy.deepcopy(name_info)
                setattr(env, key, normalized_location_names)
                continue
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

    def get_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_location_by_id', kwargs)

    def get_location_name(self, **kwargs):
        return self._call_inner_tool('get_location_name', kwargs)

    def get_child_locations(self, **kwargs):
        return self._call_inner_tool('get_child_locations', kwargs)

    def get_parent_location(self, **kwargs):
        return self._call_inner_tool('get_parent_location', kwargs)

    def get_ancestor_locations(self, **kwargs):
        return self._call_inner_tool('get_ancestor_locations', kwargs)

    def get_descendant_locations(self, **kwargs):
        return self._call_inner_tool('get_descendant_locations', kwargs)

    def list_locations_by_level(self, **kwargs):
        return self._call_inner_tool('list_locations_by_level', kwargs)

    def get_hierarchical_structure(self, **kwargs):
        return self._call_inner_tool('get_hierarchical_structure', kwargs)

    def is_supported_language_for_location(self, **kwargs):
        return self._call_inner_tool('is_supported_language_for_location', kwargs)

    def add_location(self, **kwargs):
        return self._call_inner_tool('add_location', kwargs)

    def update_location(self, **kwargs):
        return self._call_inner_tool('update_location', kwargs)

    def delete_location(self, **kwargs):
        return self._call_inner_tool('delete_location', kwargs)

    def add_location_name(self, **kwargs):
        return self._call_inner_tool('add_location_name', kwargs)

    def update_location_name(self, **kwargs):
        return self._call_inner_tool('update_location_name', kwargs)

    def delete_location_name(self, **kwargs):
        return self._call_inner_tool('delete_location_name', kwargs)

    def move_location(self, **kwargs):
        return self._call_inner_tool('move_location', kwargs)

    def validate_hierarchy(self, **kwargs):
        return self._call_inner_tool('validate_hierarchy', kwargs)
