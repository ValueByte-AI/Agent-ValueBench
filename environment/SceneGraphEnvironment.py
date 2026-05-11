# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict, Any



# SceneObject TypedDict
class SceneObjectInfo(TypedDict):
    object_id: str
    geometry: str  # e.g., mesh identifier
    parent_id: Optional[str]  # None for root objects
    children_ids: List[str]
    transform: List[List[float]]  # 4x4 transformation matrix
    material_id: Optional[str]

# Material TypedDict
class MaterialInfo(TypedDict):
    material_id: str
    type: str  # e.g., 'metallic', 'wood'
    color: List[float]  # RGB or RGBA
    texture_id: Optional[str]
    finish_id: Optional[str]
    properties: Dict[str, float]  # e.g., {'reflectivity': 0.3, 'roughness': 0.5}

# Texture TypedDict
class TextureInfo(TypedDict):
    texture_id: str
    image_data: Any  # Could be bytes or image encoding
    mapping_type: str
    scale: float
    repeat: int

# Finish TypedDict
class FinishInfo(TypedDict):
    finish_id: str
    style: str  # e.g., 'metallic', 'matte'
    reflectivity: float
    roughness: float
    glossiness: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Scene Objects: {object_id: SceneObjectInfo}
        # Attributes: object_id, geometry, parent_id, children_ids, transform, material_id
        self.scene_objects: Dict[str, SceneObjectInfo] = {}

        # Materials: {material_id: MaterialInfo}
        # Attributes: material_id, type, color, texture_id, finish_id, properties
        self.materials: Dict[str, MaterialInfo] = {}

        # Textures: {texture_id: TextureInfo}
        # Attributes: texture_id, image_data, mapping_type, scale, repeat
        self.textures: Dict[str, TextureInfo] = {}

        # Finishes: {finish_id: FinishInfo}
        # Attributes: finish_id, style, reflectivity, roughness, glossiness
        self.finishes: Dict[str, FinishInfo] = {}

        # --- Constraints ---
        # - Each SceneObject must reference at most one Material at a time.
        # - Each Material can reference zero or one Texture, and zero or one Finish.
        # - Applying a new material replaces the previous material assignment for that SceneObject.
        # - Transformations (translate/rotate/scale) must be maintained relative to the object's parent.
        # - Material and finish properties must be compatible (e.g., wood material cannot have a metallic finish).

    def get_scene_object_by_id(self, object_id: str) -> dict:
        """
        Retrieve a SceneObject's attributes by object_id, including geometry, parent/children, transform, and material assignment.

        Args:
            object_id (str): The unique identifier of the scene object.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SceneObjectInfo  # The object's complete descriptor (may include material_id=None)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # "SceneObject not found"
                    }
        Constraints:
            - object_id must exist in the scene.
        """
        obj = self.scene_objects.get(object_id)
        if obj is None:
            return { "success": False, "error": "SceneObject not found" }
        return { "success": True, "data": obj }

    def list_scene_objects(self) -> dict:
        """
        List all SceneObjects in the scene.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SceneObjectInfo],  # May be empty if no objects are present
            }

        Constraints:
            - None. This is a pure query — no permissions nor object restrictions apply.
        """
        # Retrieve all SceneObjects as a list
        result = list(self.scene_objects.values())
        return { "success": True, "data": result }

    def get_material_by_id(self, material_id: str) -> dict:
        """
        Retrieve all properties of a Material given its material_id.
    
        Args:
            material_id (str): The unique identifier of the material to query.
    
        Returns:
            dict: 
                {
                    "success": True,
                    "data": MaterialInfo  # full properties of the material
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., material not found)
                }
    
        Constraints:
            - material_id must correspond to an existing Material in the system.
        """
        material = self.materials.get(material_id)
        if material is None:
            return {"success": False, "error": "Material not found"}
        return {"success": True, "data": material}

    def list_materials(self) -> dict:
        """
        List all defined materials in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MaterialInfo]  # List of all material definitions (possibly empty)
            }
        """
        materials_list = list(self.materials.values())
        return { "success": True, "data": materials_list }

    def get_texture_by_id(self, texture_id: str) -> dict:
        """
        Retrieve all Texture properties by texture_id.

        Args:
            texture_id (str): The unique identifier of the texture to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": TextureInfo         # Texture properties if found
            }
            or
            {
                "success": False,
                "error": str                # Reason for failure, e.g., texture not found
            }
        """
        texture = self.textures.get(texture_id)
        if texture is None:
            return { "success": False, "error": "Texture not found" }
        return { "success": True, "data": texture }

    def list_textures(self) -> dict:
        """
        List all available textures in the scene graph environment.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TextureInfo],  # List of textures (may be empty if none exist)
            }

        Constraints:
            - None (all textures are listed unfiltered)
        """
        textures_list = list(self.textures.values())
        return { "success": True, "data": textures_list }

    def get_finish_by_id(self, finish_id: str) -> dict:
        """
        Retrieve Finish information by finish_id.

        Args:
            finish_id (str): The unique identifier for the finish.

        Returns:
            dict: {
                "success": True,
                "data": FinishInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The finish_id must exist in the environment's finishes.
        """
        finish = self.finishes.get(finish_id)
        if finish is None:
            return { "success": False, "error": f"Finish with id '{finish_id}' does not exist." }
        return { "success": True, "data": finish }

    def list_finishes(self) -> dict:
        """
        List all defined finishes in the environment.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FinishInfo]  # List of all finishes (possibly empty)
            }
        """
        finishes_list = list(self.finishes.values())
        return {
            "success": True,
            "data": finishes_list
        }

    def get_parent_and_children(self, object_id: str) -> dict:
        """
        Retrieve the parent ID and list of direct children IDs for a given SceneObject.
    
        Args:
            object_id (str): The unique identifier of the SceneObject.
        
        Returns:
            dict: {
                "success": True,
                "data": {
                    "parent_id": Optional[str],   # None if root
                    "children_ids": List[str]     # List of direct children IDs
                }
            }
            or
            {
                "success": False,
                "error": "SceneObject not found"
            }
        
        Constraints:
            - The SceneObject identified by object_id must exist.
        """
        obj = self.scene_objects.get(object_id)
        if obj is None:
            return { "success": False, "error": "SceneObject not found" }
    
        return {
            "success": True,
            "data": {
                "parent_id": obj.get("parent_id"),
                "children_ids": obj.get("children_ids", []).copy()
            }
        }

    def check_material_finish_compatibility(self, material_id: str, finish_id: str) -> dict:
        """
        Check whether the specified material_id and finish_id are compatible.

        Args:
            material_id (str): The ID of the material to check.
            finish_id (str): The ID of the finish to check.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": { "compatible": bool }
                }
                or
                {
                    "success": False,
                    "error": str  # Description of why the check failed
                }

        Constraints:
            - Both material_id and finish_id must exist.
            - Compatibility: e.g., a wood material cannot have a metallic finish.
        """
        # Check existence
        material = self.materials.get(material_id)
        if not material:
            return { "success": False, "error": "Material not found" }

        finish = self.finishes.get(finish_id)
        if not finish:
            return { "success": False, "error": "Finish not found" }

        compatible = True
        # Only constraint specified: wood material cannot have metallic finish
        if material['type'] == 'wood' and finish['style'] == 'metallic':
            compatible = False

        return { "success": True, "data": { "compatible": compatible } }

    def assign_material_to_object(self, object_id: str, material_id: str) -> dict:
        """
        Assign or replace the material assignment for a SceneObject.

        Args:
            object_id (str): The ID of the SceneObject.
            material_id (str): The ID of the Material to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Material assigned to object."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - SceneObject must exist.
            - Material must exist.
            - Replaces any prior material (at most one material assignment).
        """
        if object_id not in self.scene_objects:
            return {"success": False, "error": "SceneObject does not exist"}
        if material_id not in self.materials:
            return {"success": False, "error": "Material does not exist"}

        self.scene_objects[object_id]["material_id"] = material_id
        return {"success": True, "message": "Material assigned to object."}

    def assign_texture_to_material(self, material_id: str, texture_id: str) -> dict:
        """
        Assign or replace the texture linked to a Material.

        Args:
            material_id (str): The ID of the material to assign the texture to.
            texture_id (str): The ID of the texture to assign.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Texture <texture_id> assigned to Material <material_id>."
                }
                On failure,
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - material_id must exist in the environment.
            - texture_id must exist in the environment.
            - Each Material can reference zero or one Texture; this operation replaces any previous assignment.
        """
        if material_id not in self.materials:
            return { "success": False, "error": f"Material '{material_id}' does not exist." }
        if texture_id not in self.textures:
            return { "success": False, "error": f"Texture '{texture_id}' does not exist." }

        self.materials[material_id]['texture_id'] = texture_id
        return {
            "success": True,
            "message": f"Texture '{texture_id}' assigned to Material '{material_id}'."
        }

    def assign_finish_to_material(self, material_id: str, finish_id: str) -> dict:
        """
        Assign or replace the finish linked to a Material, after checking compatibility.

        Args:
            material_id (str): ID of the Material to update.
            finish_id (str): ID of the Finish to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Finish assigned to material."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both the material and finish must exist.
            - Material type and finish style must be compatible (e.g., wood material cannot have metallic finish).
            - Assigning replaces any existing finish assignment.
        """
        # Check existence
        if material_id not in self.materials:
            return { "success": False, "error": "Material does not exist." }
        if finish_id not in self.finishes:
            return { "success": False, "error": "Finish does not exist." }

        material_info = self.materials[material_id]
        finish_info = self.finishes[finish_id]

        # Compatibility check (simplified rule: wood can't have metallic)
        if (material_info["type"].lower() == "wood" and finish_info["style"].lower() == "metallic"):
            return {
                "success": False,
                "error": "Incompatible: Wood material cannot have metallic finish."
            }

        # Assign (replace existing)
        material_info["finish_id"] = finish_id

        return { "success": True, "message": "Finish assigned to material." }

    def create_material(
        self,
        material_id: str,
        type: str,
        color: list,
        properties: dict,
        texture_id: str = None,
        finish_id: str = None
    ) -> dict:
        """
        Create and register a new Material with specified properties.

        Args:
            material_id (str): Unique ID for the new material.
            type (str): Material type, e.g., 'metallic', 'wood'.
            color (list[float]): List of color values (e.g., RGB[A]).
            properties (dict): Dictionary of material properties (e.g., reflectivity, roughness).
            texture_id (str, optional): Texture to assign (must exist or be None).
            finish_id (str, optional): Finish to assign (must exist or be None).

        Returns:
            dict: { "success": True, "message": "Material created" }
                  or { "success": False, "error": <reason> }

        Constraints:
            - material_id must be unique.
            - If texture_id is specified, it must exist.
            - If finish_id is specified, it must exist.
            - Finish must be compatible with the material type.
        """
        # Check uniqueness
        if material_id in self.materials:
            return { "success": False, "error": "Material ID already exists" }
        # Validate texture
        if texture_id is not None:
            if texture_id not in self.textures:
                return { "success": False, "error": "Texture does not exist" }
        # Validate finish
        if finish_id is not None:
            if finish_id not in self.finishes:
                return { "success": False, "error": "Finish does not exist" }
            # --- Compatibility check between material type and finish style ---
            # Example rule: wood material cannot have metallic finish
            finish_style = self.finishes[finish_id]['style']
            # If enforcing this:
            if (type == 'wood' and finish_style == 'metallic'):
                return {
                    "success": False,
                    "error": "Wood material cannot have a metallic finish"
                }
            # More rules can be added as needed

        # Register new material
        self.materials[material_id] = {
            'material_id': material_id,
            'type': type,
            'color': color,
            'texture_id': texture_id,
            'finish_id': finish_id,
            'properties': properties
        }
        return { "success": True, "message": "Material created" }

    def create_texture(
        self,
        texture_id: str,
        image_data: any,
        mapping_type: str,
        scale: float,
        repeat: int
    ) -> dict:
        """
        Create and add a new Texture to the environment.

        Args:
            texture_id (str): Unique identifier for the new texture.
            image_data (any): Texture's image data (bytes, array, etc.).
            mapping_type (str): Specifies how texture is mapped ('UV', 'planar', etc.).
            scale (float): Scaling factor for the texture mapping (must be > 0).
            repeat (int): Number of times the texture is repeated (must be >= 1).

        Returns:
            dict:
                - On success: { "success": True, "message": "Texture created successfully" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - texture_id must be unique (not already present in self.textures).
            - scale must be positive.
            - repeat must be at least 1.
        """
        # Check for unique texture_id
        if texture_id in self.textures:
            return { "success": False, "error": "Texture ID already exists" }
        if not isinstance(mapping_type, str) or not mapping_type:
            return { "success": False, "error": "mapping_type must be a non-empty string" }
        if not isinstance(scale, (float, int)) or scale <= 0:
            return { "success": False, "error": "scale must be a positive number" }
        if not isinstance(repeat, int) or repeat < 1:
            return { "success": False, "error": "repeat must be an integer >= 1" }

        texture_info = {
            "texture_id": texture_id,
            "image_data": image_data,
            "mapping_type": mapping_type,
            "scale": float(scale),
            "repeat": repeat
        }

        self.textures[texture_id] = texture_info

        return { "success": True, "message": "Texture created successfully" }

    def create_finish(
        self,
        finish_id: str,
        style: str,
        reflectivity: float,
        roughness: float,
        glossiness: float
    ) -> dict:
        """
        Create and register a new Finish with given properties.

        Args:
            finish_id (str): Unique identifier for the new finish.
            style (str): Style of the finish (e.g., 'metallic', 'matte').
            reflectivity (float): Surface reflectivity (should be >= 0).
            roughness (float): Surface roughness (should be >= 0).
            glossiness (float): Surface glossiness (should be >= 0).

        Returns:
            dict: {
                "success": True,
                "message": "Finish <finish_id> created successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - finish_id must not duplicate an existing finish.
            - reflectivity, roughness, glossiness should be non-negative.
        """
        if finish_id in self.finishes:
            return { "success": False, "error": f"Finish ID '{finish_id}' already exists" }

        if not isinstance(style, str) or not style:
            return { "success": False, "error": "Invalid style (must be non-empty string)" }

        for param, value in [('reflectivity', reflectivity), ('roughness', roughness), ('glossiness', glossiness)]:
            if not isinstance(value, (float, int)):
                return { "success": False, "error": f"{param.capitalize()} must be a number" }
            if value < 0:
                return { "success": False, "error": f"{param.capitalize()} must be non-negative" }

        finish_info = {
            "finish_id": finish_id,
            "style": style,
            "reflectivity": float(reflectivity),
            "roughness": float(roughness),
            "glossiness": float(glossiness)
        }
        self.finishes[finish_id] = finish_info

        return { "success": True, "message": f"Finish '{finish_id}' created successfully" }

    def remove_material_from_object(self, object_id: str) -> dict:
        """
        Unassign (remove) the material from the specified SceneObject, leaving it with no material.

        Args:
            object_id (str): The unique identifier of the SceneObject.

        Returns:
            dict: {
                "success": True,
                "message": "Material removed from object <object_id>"
            }
            or
            {
                "success": False,
                "error": str  # Description of why the operation failed (e.g., object does not exist)
            }

        Constraints:
            - The SceneObject must exist in the scene graph.
            - After this operation, the object's material_id will be None.
        """
        if object_id not in self.scene_objects:
            return {"success": False, "error": "SceneObject does not exist"}

        self.scene_objects[object_id]["material_id"] = None
        return {
            "success": True,
            "message": f"Material removed from object {object_id}"
        }

    def update_object_transform(self, object_id: str, transform: list) -> dict:
        """
        Change a SceneObject's transformation matrix (translate/rotate/scale).

        Args:
            object_id (str): ID of the SceneObject whose transform is to be updated.
            transform (list): New 4x4 transformation matrix (List[List[float]]).
    
        Returns:
            dict: {
                "success": True,
                "message": "Transformation updated for object <object_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - object_id must exist in the scene.
            - transform must be a 4x4 matrix of floats.
            - The transformation is stored as local to the object's parent.
        """
        if object_id not in self.scene_objects:
            return { "success": False, "error": f"SceneObject with id '{object_id}' does not exist" }
    
        # Validate 4x4 structure
        if (not isinstance(transform, list) or len(transform) != 4 or
            not all(isinstance(row, list) and len(row) == 4 for row in transform)):
            return { "success": False, "error": "Transform must be a 4x4 matrix (list of 4 lists, each of length 4)" }
    
        # Validate that all elements are floats or can be converted to floats
        try:
            float_matrix = [[float(cell) for cell in row] for row in transform]
        except (ValueError, TypeError):
            return { "success": False, "error": "All elements in transform must be floats" }

        # Perform update
        self.scene_objects[object_id]["transform"] = float_matrix

        return { "success": True, "message": f"Transformation updated for object {object_id}" }

    def remove_finish_from_material(self, material_id: str) -> dict:
        """
        Unassign (remove) the finish from a Material, if present.

        Args:
            material_id (str): The unique identifier for the Material.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Finish removed from material <material_id>"
                }
                On failure:
                {
                    "success": False,
                    "error": "Material does not exist"
                }
                or
                {
                    "success": False,
                    "error": "Material does not have a finish assigned"
                }

        Constraints:
            - Material must exist.
            - Removing a finish is a no-op if no finish is assigned (returns error).
        """
        material = self.materials.get(material_id)
        if material is None:
            return {"success": False, "error": "Material does not exist"}

        if material.get('finish_id') is None:
            return {"success": False, "error": "Material does not have a finish assigned"}

        material['finish_id'] = None
        return {"success": True, "message": f"Finish removed from material {material_id}"}

    def remove_texture_from_material(self, material_id: str) -> dict:
        """
        Unassign (remove) the texture from the specified Material, if present.

        Args:
            material_id (str): The unique identifier for the material.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message, even if no texture was assigned.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. material not found.
            }

        Constraints:
            - The material must exist.
            - It is valid to call this even if the material has no texture assigned.
        """
        if material_id not in self.materials:
            return {
                "success": False,
                "error": f"Material with id '{material_id}' does not exist."
            }

        material = self.materials[material_id]
        # Perform the unassignment (even if already None)
        material["texture_id"] = None
        self.materials[material_id] = material  # Save back, though not strictly needed for mutable dicts

        return {
            "success": True,
            "message": f"Texture removed from material '{material_id}'."
        }


class SceneGraphEnvironment(BaseEnv):
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

    def get_scene_object_by_id(self, **kwargs):
        return self._call_inner_tool('get_scene_object_by_id', kwargs)

    def list_scene_objects(self, **kwargs):
        return self._call_inner_tool('list_scene_objects', kwargs)

    def get_material_by_id(self, **kwargs):
        return self._call_inner_tool('get_material_by_id', kwargs)

    def list_materials(self, **kwargs):
        return self._call_inner_tool('list_materials', kwargs)

    def get_texture_by_id(self, **kwargs):
        return self._call_inner_tool('get_texture_by_id', kwargs)

    def list_textures(self, **kwargs):
        return self._call_inner_tool('list_textures', kwargs)

    def get_finish_by_id(self, **kwargs):
        return self._call_inner_tool('get_finish_by_id', kwargs)

    def list_finishes(self, **kwargs):
        return self._call_inner_tool('list_finishes', kwargs)

    def get_parent_and_children(self, **kwargs):
        return self._call_inner_tool('get_parent_and_children', kwargs)

    def check_material_finish_compatibility(self, **kwargs):
        return self._call_inner_tool('check_material_finish_compatibility', kwargs)

    def assign_material_to_object(self, **kwargs):
        return self._call_inner_tool('assign_material_to_object', kwargs)

    def assign_texture_to_material(self, **kwargs):
        return self._call_inner_tool('assign_texture_to_material', kwargs)

    def assign_finish_to_material(self, **kwargs):
        return self._call_inner_tool('assign_finish_to_material', kwargs)

    def create_material(self, **kwargs):
        return self._call_inner_tool('create_material', kwargs)

    def create_texture(self, **kwargs):
        return self._call_inner_tool('create_texture', kwargs)

    def create_finish(self, **kwargs):
        return self._call_inner_tool('create_finish', kwargs)

    def remove_material_from_object(self, **kwargs):
        return self._call_inner_tool('remove_material_from_object', kwargs)

    def update_object_transform(self, **kwargs):
        return self._call_inner_tool('update_object_transform', kwargs)

    def remove_finish_from_material(self, **kwargs):
        return self._call_inner_tool('remove_finish_from_material', kwargs)

    def remove_texture_from_material(self, **kwargs):
        return self._call_inner_tool('remove_texture_from_material', kwargs)

