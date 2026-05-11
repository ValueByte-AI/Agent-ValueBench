# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict



class DraftingElementInfo(TypedDict):
    element_id: str
    type: str  # e.g., 'line', 'circle', 'polygon', etc.
    layer_id: str
    attributes: Dict[str, Any]  # e.g., center_point, radius, length, corner_points, etc.
    unit: str

class PlanInfo(TypedDict):
    plan_id: str
    name: str
    list_of_element_ids: List[str]
    unit: str

class LayerInfo(TypedDict):
    layer_id: str
    name: str
    visibility_status: bool  # True for visible, False for hidden
    list_of_element_ids: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Architectural CAD drafting environment state.

        Constraints:
        - Drafting element attributes must conform to their type (e.g., circles require center and radius).
        - Units used by elements must match the plan’s unit system.
        - Elements added to a plan must be assigned to a valid layer.
        - No duplicate element_ids within a plan.
        - Layer visibility affects whether elements are displayed or edited.
        """

        # Drafting elements: {element_id: DraftingElementInfo}
        self.drafting_elements: Dict[str, DraftingElementInfo] = {}

        # Plans: {plan_id: PlanInfo}
        self.plans: Dict[str, PlanInfo] = {}

        # Layers: {layer_id: LayerInfo}
        self.layers: Dict[str, LayerInfo] = {}

    @staticmethod
    def _attributes_match_type(element_type: str, attributes: Dict[str, Any]) -> bool:
        if not isinstance(attributes, dict) or not attributes:
            return False
        if element_type == "circle":
            if "radius" not in attributes:
                return False
            return (
                "center" in attributes
                or "center_point" in attributes
                or (
                    "center_x" in attributes
                    and "center_y" in attributes
                )
            )
        if element_type == "line":
            return (
                ("start" in attributes and "end" in attributes)
                or ("start_point" in attributes and "end_point" in attributes)
                or "length" in attributes
            )
        if element_type == "polygon":
            return (
                "points" in attributes
                or "corner_points" in attributes
                or "vertices" in attributes
                or ("usage" in attributes and "area" in attributes)
                or ("sides" in attributes and "radius" in attributes)
            )
        return True

    def get_plan_info(self, plan_id: str) -> dict:
        """
        Retrieve full details of a plan, including plan_id, name, unit, and list of drafting elements.

        Args:
            plan_id (str): Unique identifier of the plan to query.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "plan_id": str,
                    "name": str,
                    "unit": str,
                    "elements": List[DraftingElementInfo]
                }
            }
            or
            {
                "success": False,
                "error": str  # Plan does not exist
            }

        Constraints:
            - plan_id must exist.
            - Only existing drafting elements (whose IDs are in the plan) are included in elements.
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return { "success": False, "error": "Plan does not exist" }
    
        # Gather info for each element in the plan
        elements = []
        for eid in plan["list_of_element_ids"]:
            element_info = self.drafting_elements.get(eid)
            if element_info:
                elements.append(element_info)

        result = {
            "plan_id": plan["plan_id"],
            "name": plan["name"],
            "unit": plan["unit"],
            "elements": elements
        }
        return { "success": True, "data": result }

    def get_all_layers(self, plan_id: str) -> dict:
        """
        Retrieve all layers associated with a specific plan. Each returned layer includes:
          - layer_id
          - name
          - visibility_status
          - list_of_element_ids (only those belonging to the specified plan)

        Args:
            plan_id (str): The ID of the plan to query.

        Returns:
            dict:
                - success: True and data list of LayerInfo dicts if plan exists.
                - success: False and error message otherwise.

        Constraints:
            - Only layers containing one or more elements present in the given plan are returned.
            - If the plan has no associated layers, returns an empty list as data.
        """
        if plan_id not in self.plans:
            return {"success": False, "error": "Plan does not exist"}

        plan = self.plans[plan_id]
        plan_element_ids = set(plan["list_of_element_ids"])

        layers_in_plan = []
        for layer in self.layers.values():
            # Intersection: which layer elements are in the plan
            elements_in_plan = [eid for eid in layer["list_of_element_ids"] if eid in plan_element_ids]
            if elements_in_plan:
                layer_info = {
                    "layer_id": layer["layer_id"],
                    "name": layer["name"],
                    "visibility_status": layer["visibility_status"],
                    "list_of_element_ids": elements_in_plan
                }
                layers_in_plan.append(layer_info)

        return {"success": True, "data": layers_in_plan}

    def get_layer_info(self, layer_id: str) -> dict:
        """
        Retrieve details of a specific layer, including its name, visibility status, and list of elements.

        Args:
            layer_id (str): The unique identifier of the layer to query.

        Returns:
            dict: {
                "success": True,
                "data": LayerInfo  # Dictionary of the layer information
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Layer does not exist"
            }

        Constraints:
            - The layer_id must exist in the environment.
        """
        layer = self.layers.get(layer_id)
        if not layer:
            return {"success": False, "error": "Layer does not exist"}
        return {"success": True, "data": layer}

    def get_visible_layers(self, plan_id: str) -> dict:
        """
        Return all layers in a given plan that are currently set to visible.

        Args:
            plan_id (str): The identifier of the plan for which to retrieve visible layers.

        Returns:
            dict: {
                "success": True,
                "data": List[LayerInfo],  # List of LayerInfo for each visible layer in the plan.
            }
            or
            {
                "success": False,
                "error": str  # Description of error if plan does not exist.
            }

        Constraints:
            - Only layers with at least one element belonging to the plan are considered.
            - Only layers with visibility_status == True are returned.
        """
        if plan_id not in self.plans:
            return {"success": False, "error": "Plan does not exist"}

        plan_info = self.plans[plan_id]
        plan_element_ids = set(plan_info["list_of_element_ids"])

        visible_layers = []
        for layer in self.layers.values():
            layer_element_ids = set(layer["list_of_element_ids"])
            if layer["visibility_status"] and plan_element_ids & layer_element_ids:
                visible_layers.append({
                    "layer_id": layer["layer_id"],
                    "name": layer["name"],
                    "visibility_status": layer["visibility_status"],
                    "list_of_element_ids": [
                        eid for eid in layer["list_of_element_ids"] if eid in plan_element_ids
                    ],
                })

        return {"success": True, "data": visible_layers}

    def get_drafting_element_info(self, element_id: str) -> dict:
        """
        Retrieve complete information and attributes for a drafting element by its element_id.

        Args:
            element_id (str): ID of the drafting element to fetch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": DraftingElementInfo  # All attributes for this drafting element
                    }
                On failure (non-existent element_id):
                    {
                        "success": False,
                        "error": "Drafting element with given element_id does not exist."
                    }

        Constraints:
            - element_id must exist in the drafting_elements dictionary.
        """
        if element_id not in self.drafting_elements:
            return {
                "success": False,
                "error": "Drafting element with given element_id does not exist."
            }
        return {
            "success": True,
            "data": self.drafting_elements[element_id]
        }

    def get_elements_by_type(
        self, 
        element_type: str, 
        plan_id: str = None, 
        layer_id: str = None
    ) -> dict:
        """
        Retrieve all drafting elements of a given type within the specified plan or layer.

        Args:
            element_type (str): The type of drafting element, e.g., 'circle', 'line', 'polygon'.
            plan_id (str, optional): The plan ID in which to search for elements.
            layer_id (str, optional): The layer ID in which to search for elements.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[DraftingElementInfo]  # All matching elements
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Must specify exactly one of `plan_id` or `layer_id`.
            - The specified plan or layer must exist.
            - Returns empty list if no elements of that type are present.

        Notes:
            - If both plan_id and layer_id are specified, returns an error.
            - If neither is specified, returns an error.
        """
        if not element_type:
            return { "success": False, "error": "Element type must be specified." }
    
        if (plan_id is None and layer_id is None) or (plan_id is not None and layer_id is not None):
            return { "success": False, "error": "Specify exactly one of plan_id or layer_id." }
    
        element_ids = []
        if plan_id is not None:
            if plan_id not in self.plans:
                return { "success": False, "error": "Plan does not exist." }
            element_ids = self.plans[plan_id]["list_of_element_ids"]
        elif layer_id is not None:
            if layer_id not in self.layers:
                return { "success": False, "error": "Layer does not exist." }
            element_ids = self.layers[layer_id]["list_of_element_ids"]

        result = [
            self.drafting_elements[e_id]
            for e_id in element_ids
            if e_id in self.drafting_elements and self.drafting_elements[e_id]["type"] == element_type
        ]
        return { "success": True, "data": result }

    def get_plan_unit(self, plan_id: str) -> dict:
        """
        Return the measurement unit system of a plan.

        Args:
            plan_id (str): The unique identifier for the architectural plan.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": str  # The unit system, e.g., 'mm', 'cm', 'in'
                }
                - On failure: {
                    "success": False,
                    "error": str  # Description of error, e.g. plan does not exist
                }

        Constraints:
            - The plan must exist in the environment.
        """
        if plan_id not in self.plans:
            return { "success": False, "error": "Plan does not exist" }

        unit = self.plans[plan_id]["unit"]
        return { "success": True, "data": unit }

    def get_layer_elements(self, layer_id: str) -> dict:
        """
        List all element_ids assigned to the given layer.

        Args:
            layer_id (str): Identifier of the layer.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[str] }  # List of element_ids in the layer (may be empty)
                - On failure:
                    { "success": False, "error": str }      # Error message, e.g. layer does not exist

        Constraints:
            - The layer_id must exist in the environment.
        """
        if layer_id not in self.layers:
            return { "success": False, "error": "Layer does not exist" }
        return { "success": True, "data": self.layers[layer_id]["list_of_element_ids"] }

    def check_element_id_exists(self, plan_id: str, element_id: str) -> dict:
        """
        Query whether a given element_id is already assigned within a plan.

        Args:
            plan_id (str): The ID of the plan to check within.
            element_id (str): The element ID to check for uniqueness.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True if element_id is present in the plan, else False
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Plan does not exist"
            }

        Constraints:
            - The plan must exist.
            - Checks only assignment within the plan's element list, not global element existence.
        """
        plan_info = self.plans.get(plan_id)
        if plan_info is None:
            return { "success": False, "error": "Plan does not exist" }
        exists = element_id in plan_info["list_of_element_ids"]
        return { "success": True, "data": exists }

    def add_drafting_element(self, plan_id: str, element_info: DraftingElementInfo) -> dict:
        """
        Add a new drafting element (e.g., circle, line, polygon) to the specified plan and assign it to
        the given layer.

        Args:
            plan_id (str): The plan to which the element will be added.
            element_info (DraftingElementInfo): The new element data, required keys --
                element_id: str (globally unique),
                type: str (e.g., 'line', 'circle', 'polygon'),
                layer_id: str (must exist),
                attributes: dict (type-dependent),
                unit: str (must match plan unit)

        Returns:
            dict: {
                "success": True,
                "message": "Drafting element <element_id> added to plan <plan_id> and layer <layer_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints Enforced:
            - No duplicate element_id in system or plan.
            - Layer and plan existence.
            - Element unit matches plan unit.
            - Type-attribute conformance.
            - Layer must exist prior.
        """

        eid = element_info.get("element_id")
        typ = element_info.get("type")
        layer_id = element_info.get("layer_id")
        attributes = element_info.get("attributes", {})
        unit = element_info.get("unit")

        # 1. Plan must exist
        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} does not exist."}

        # 2. Layer must exist
        if layer_id not in self.layers:
            return {"success": False, "error": f"Layer {layer_id} does not exist."}

        # 3. element_id must be globally unique
        if eid in self.drafting_elements:
            return {"success": False, "error": f"Element ID '{eid}' already exists."}

        # 4. element_id must not be in plan's list_of_element_ids
        if eid in self.plans[plan_id]["list_of_element_ids"]:
            return {"success": False, "error": f"Element ID '{eid}' already exists in plan {plan_id}."}

        # 5. Units must match
        plan_unit = self.plans[plan_id].get("unit")
        if unit != plan_unit:
            return {"success": False, "error": f"Element unit '{unit}' does not match plan unit '{plan_unit}'."}

        # 6. Basic attribute enforcement per type
        if not self._attributes_match_type(typ, attributes):
            return {
                "success": False,
                "error": f"Attributes do not conform to element type '{typ}'."
            }

        # 7. Update system: add element to the central registry, plan list, layer list
        self.drafting_elements[eid] = {
            "element_id": eid,
            "type": typ,
            "layer_id": layer_id,
            "attributes": attributes,
            "unit": unit
        }
        self.plans[plan_id]["list_of_element_ids"].append(eid)
        self.layers[layer_id]["list_of_element_ids"].append(eid)

        return {
            "success": True,
            "message": f"Drafting element '{eid}' added to plan '{plan_id}' and layer '{layer_id}'."
        }

    def update_drafting_element(
        self,
        element_id: str,
        new_type: str = None,
        new_attributes: dict = None,
        new_unit: str = None
    ) -> dict:
        """
        Modify the attributes and/or type of an existing drafting element.

        Args:
            element_id (str): The unique ID of the drafting element to update.
            new_type (str, optional): New type for the drafting element (e.g. 'circle').
            new_attributes (dict, optional): Attributes dictionary according to element type.
            new_unit (str, optional): New unit for the element.

        Returns:
            dict: {
                "success": True,
                "message": "Drafting element updated successfully"
            }
            or
            {
                "success": False,
                "error": reason
            }

        Constraints:
            - element_id must already exist.
            - If new_type or new_attributes are given, new_attributes must satisfy type constraints.
            - new_unit (if provided) must match the unit of the plan the element belongs to.
            - Elements must always belong to a valid layer (layer_id exists).
        """
        if element_id not in self.drafting_elements:
            return { "success": False, "error": "Drafting element does not exist" }
    
        old_elem = self.drafting_elements[element_id]
        updated_elem = old_elem.copy()
    
        # Check new unit compatibility with plan
        if new_unit is not None:
            # Find the plan that contains this element
            found_plan = None
            for plan in self.plans.values():
                if element_id in plan.get('list_of_element_ids', []):
                    found_plan = plan
                    break
            if not found_plan:
                return { "success": False, "error": "Element is not assigned to any plan." }
            if new_unit != found_plan["unit"]:
                return {
                    "success": False,
                    "error": f"Element unit '{new_unit}' does not match plan unit '{found_plan['unit']}'"
                }
            updated_elem["unit"] = new_unit

        # Update type if provided
        if new_type is not None:
            updated_elem["type"] = new_type

        # Update attributes if provided
        if new_attributes is not None:
            updated_elem["attributes"] = new_attributes

        # Validate layer exists
        layer_id = updated_elem["layer_id"]
        if layer_id not in self.layers:
            return { "success": False, "error": "Drafting element's layer does not exist." }

        # Validate attributes conform to type
        elem_type = updated_elem["type"]
        attr = updated_elem["attributes"]
        if not self._attributes_match_type(elem_type, attr):
            return {
                "success": False,
                "error": f"Attributes do not conform to element type '{elem_type}'"
            }
    
        # All checks passed, commit
        self.drafting_elements[element_id] = updated_elem

        return { "success": True, "message": "Drafting element updated successfully" }

    def delete_drafting_element(self, element_id: str) -> dict:
        """
        Remove a drafting element from the environment, including from any plan and associated layer.

        Args:
            element_id (str): The unique ID of the drafting element to remove.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Drafting element <element_id> deleted from plan and layer."}
                - On failure (element not found):
                    {"success": False, "error": "Drafting element does not exist."}

        Constraints:
            - Element ID must exist in the environment.
            - Remove element ID from any plan's and layer's list_of_element_ids.
            - Deletion should maintain integrity: no orphan references.
        """
        # Check existence
        if element_id not in self.drafting_elements:
            return {"success": False, "error": "Drafting element does not exist."}

        # Remove from Plans
        for plan in self.plans.values():
            if element_id in plan["list_of_element_ids"]:
                plan["list_of_element_ids"].remove(element_id)

        # Remove from Layers
        for layer in self.layers.values():
            if element_id in layer["list_of_element_ids"]:
                layer["list_of_element_ids"].remove(element_id)

        # Remove the element itself
        del self.drafting_elements[element_id]

        return {"success": True, "message": f"Drafting element {element_id} deleted from plan and layer."}

    def assign_element_to_layer(self, element_id: str, layer_id: str) -> dict:
        """
        Assign or move an existing drafting element to a different valid layer.

        Args:
            element_id (str): The ID of the drafting element to assign/move.
            layer_id (str): The ID of the target layer.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Element assigned to layer successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The drafting element (element_id) must exist.
            - The target layer (layer_id) must exist.
            - The element will be removed from its old layer and added to the new one.
            - No duplicate element IDs in layer's element list.
        """

        # Check if the drafting element exists
        if element_id not in self.drafting_elements:
            return {"success": False, "error": "Drafting element does not exist"}

        # Check if the target layer exists
        if layer_id not in self.layers:
            return {"success": False, "error": "Target layer does not exist"}

        # Get the drafting element's current layer, if any
        current_layer_id = self.drafting_elements[element_id]["layer_id"]

        # If already assigned to this layer, treat as success (no op)
        if current_layer_id == layer_id:
            return {"success": True, "message": "Element is already assigned to the target layer."}

        # Remove from old layer's list_of_element_ids, if the old layer exists in layers
        if current_layer_id in self.layers:
            try:
                self.layers[current_layer_id]["list_of_element_ids"].remove(element_id)
            except ValueError:
                pass  # Element was not listed in old layer, continue

        # Add to new layer's list_of_element_ids, avoid duplicates
        if element_id not in self.layers[layer_id]["list_of_element_ids"]:
            self.layers[layer_id]["list_of_element_ids"].append(element_id)

        # Update element's layer_id
        self.drafting_elements[element_id]["layer_id"] = layer_id

        return {"success": True, "message": "Element assigned to layer successfully."}

    def set_layer_visibility(self, layer_id: str, visibility_status: bool) -> dict:
        """
        Change the visibility status (visible/hidden) of a given layer.

        Args:
            layer_id (str): The identifier of the target layer.
            visibility_status (bool): Desired visibility status (True for visible, False for hidden).

        Returns:
            dict: {
                "success": True,
                "message": "Layer <layer_id> visibility set to <visibility_status>."
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Layer does not exist."
            }

        Constraints:
            - layer_id must exist.
            - Visibility may be set to its current value without error (idempotent).
        """
        if layer_id not in self.layers:
            return {"success": False, "error": "Layer does not exist."}

        self.layers[layer_id]["visibility_status"] = visibility_status

        return {
            "success": True,
            "message": f"Layer {layer_id} visibility set to {visibility_status}."
        }

    def create_layer(
        self,
        plan_id: str,
        name: str,
        visibility_status: bool = True
    ) -> dict:
        """
        Create a new layer within the specified plan.

        Args:
            plan_id (str): The plan in which to create the layer (must exist).
            name (str): The name for the new layer. (Should be unique for manageability.)
            visibility_status (bool, optional): Initial visibility status. Defaults to True.

        Returns:
            dict: {
                "success": True,
                "message": "Layer created",
                "layer_id": str,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The specified plan must exist.
            - Layer names in the environment should be unique.
        """
        # Check if plan exists
        if plan_id not in self.plans:
            return {"success": False, "error": "Plan does not exist."}

        # Enforce layer name uniqueness (environment-wide)
        for layer in self.layers.values():
            if layer["name"] == name:
                return {"success": False, "error": f"Layer with name '{name}' already exists."}

        # Generate unique layer_id
        base_id = f"{plan_id}_{name}".replace(" ", "_")
        candidate_id = base_id
        counter = 1
        while candidate_id in self.layers:
            candidate_id = f"{base_id}_{counter}"
            counter += 1
        layer_id = candidate_id

        # Create the layer
        self.layers[layer_id] = {
            "layer_id": layer_id,
            "name": name,
            "visibility_status": visibility_status,
            "list_of_element_ids": []
        }

        return {
            "success": True,
            "message": "Layer created",
            "layer_id": layer_id
        }

    def delete_layer(self, layer_id: str, remove_elements: bool = False) -> dict:
        """
        Remove a layer from the environment.
        Optionally, also remove all drafting elements assigned to this layer.

        Args:
            layer_id (str): The identifier of the layer to remove.
            remove_elements (bool): If True, also delete all elements belonging to this layer.
                                    If False (default), operation will fail if the layer has elements.

        Returns:
            dict: 
                On success: { "success": True, "message": "Layer <layer_id> deleted." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Cannot remove a layer with elements unless remove_elements=True.
            - Deleting elements also removes their references from plans/layers.
        """
        # Check layer existence
        if layer_id not in self.layers:
            return {"success": False, "error": f"Layer '{layer_id}' does not exist."}
    
        layer_info = self.layers[layer_id]
        elements_on_layer = list(layer_info['list_of_element_ids'])

        if elements_on_layer:
            if not remove_elements:
                return {
                    "success": False,
                    "error": f"Layer '{layer_id}' contains elements and cannot be deleted without remove_elements=True."
                }
            # Remove all elements: update self.drafting_elements, self.plans, other layers if needed
            for element_id in elements_on_layer:
                # Remove from drafting_elements
                if element_id in self.drafting_elements:
                    del self.drafting_elements[element_id]
                # Remove from all plans that reference this element
                for plan in self.plans.values():
                    if element_id in plan['list_of_element_ids']:
                        plan['list_of_element_ids'].remove(element_id)
                # Remove from all layers that reference this element (should only be this layer but safeguard)
                for lyr in self.layers.values():
                    if element_id in lyr['list_of_element_ids']:
                        lyr['list_of_element_ids'].remove(element_id)
    
        # Remove the layer
        del self.layers[layer_id]
        return {"success": True, "message": f"Layer '{layer_id}' deleted."}

    def create_plan(self, plan_id: str, name: str, unit: str) -> dict:
        """
        Create a new architectural plan with a unique id, name, and unit system.

        Args:
            plan_id (str): Unique identifier for the new plan.
            name (str): Name of the plan.
            unit (str): Unit system to use for this plan (e.g., 'meters', 'feet').

        Returns:
            dict: On success:
                { "success": True, "message": "Plan created successfully" }
            On error (e.g. plan_id exists):
                { "success": False, "error": "<reason>" }

        Constraints:
            - plan_id must be unique and not already in self.plans.
        """
        if plan_id in self.plans:
            return {"success": False, "error": "plan_id already exists."}
    
        plan_info: PlanInfo = {
            "plan_id": plan_id,
            "name": name,
            "list_of_element_ids": [],
            "unit": unit
        }
    
        self.plans[plan_id] = plan_info
        return {"success": True, "message": "Plan created successfully"}

    def delete_plan(self, plan_id: str) -> dict:
        """
        Remove an entire plan and all of its elements and layers from the environment.

        Args:
            plan_id (str): The ID of the plan to delete.

        Returns:
            dict:
                - success: True/False
                - message: Success message if successful
                - error: Error message if failed

        Constraints:
            - All drafting elements and their associations (including in layers) are removed.
            - Layers that no longer contain any elements are deleted.
            - The plan must exist.
        """
        if plan_id not in self.plans:
            return { "success": False, "error": "Plan does not exist." }

        plan = self.plans[plan_id]
        element_ids = set(plan.get("list_of_element_ids", []))
        associated_layers = {
            lid
            for lid, layer in self.layers.items()
            if any(eid in element_ids for eid in layer["list_of_element_ids"])
        }

        # Remove all elements and their references from layers
        for elem_id in element_ids:
            # Remove from drafting_elements, if exists
            if elem_id in self.drafting_elements:
                del self.drafting_elements[elem_id]

            # Remove from all layers' element lists
            for layer in self.layers.values():
                if elem_id in layer["list_of_element_ids"]:
                    layer["list_of_element_ids"].remove(elem_id)

        # Delete only layers that previously held elements from this plan and are now empty.
        empty_layers = [
            lid
            for lid in associated_layers
            if lid in self.layers and not self.layers[lid]["list_of_element_ids"]
        ]
        for lid in empty_layers:
            del self.layers[lid]

        # Remove plan itself
        del self.plans[plan_id]

        return { "success": True, "message": "Plan, its elements, and associated layers deleted." }


class ArchitecturalCADDraftingEnvironment(BaseEnv):
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

    def get_plan_info(self, **kwargs):
        return self._call_inner_tool('get_plan_info', kwargs)

    def get_all_layers(self, **kwargs):
        return self._call_inner_tool('get_all_layers', kwargs)

    def get_layer_info(self, **kwargs):
        return self._call_inner_tool('get_layer_info', kwargs)

    def get_visible_layers(self, **kwargs):
        return self._call_inner_tool('get_visible_layers', kwargs)

    def get_drafting_element_info(self, **kwargs):
        return self._call_inner_tool('get_drafting_element_info', kwargs)

    def get_elements_by_type(self, **kwargs):
        return self._call_inner_tool('get_elements_by_type', kwargs)

    def get_plan_unit(self, **kwargs):
        return self._call_inner_tool('get_plan_unit', kwargs)

    def get_layer_elements(self, **kwargs):
        return self._call_inner_tool('get_layer_elements', kwargs)

    def check_element_id_exists(self, **kwargs):
        return self._call_inner_tool('check_element_id_exists', kwargs)

    def add_drafting_element(self, **kwargs):
        return self._call_inner_tool('add_drafting_element', kwargs)

    def update_drafting_element(self, **kwargs):
        return self._call_inner_tool('update_drafting_element', kwargs)

    def delete_drafting_element(self, **kwargs):
        return self._call_inner_tool('delete_drafting_element', kwargs)

    def assign_element_to_layer(self, **kwargs):
        return self._call_inner_tool('assign_element_to_layer', kwargs)

    def set_layer_visibility(self, **kwargs):
        return self._call_inner_tool('set_layer_visibility', kwargs)

    def create_layer(self, **kwargs):
        return self._call_inner_tool('create_layer', kwargs)

    def delete_layer(self, **kwargs):
        return self._call_inner_tool('delete_layer', kwargs)

    def create_plan(self, **kwargs):
        return self._call_inner_tool('create_plan', kwargs)

    def delete_plan(self, **kwargs):
        return self._call_inner_tool('delete_plan', kwargs)
