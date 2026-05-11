# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict



class SceneInfo(TypedDict):
    scene_id: str
    name: str
    metadata: Dict[str, Any]
    object_ids: List[str]  # List of ARObject object_ids contained in this scene

class ARObjectInfo(TypedDict):
    object_id: str
    scene_id: str
    file_reference: str
    position: List[float]      # [x, y, z]
    scale: List[float]         # [sx, sy, sz], must be non-negative
    rotation: List[float]      # [rx, ry, rz] or quaternion; format enforcement required elsewhere
    metadata: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        AR scene management state: tracks scenes and their contained AR objects.
        """

        # Scenes: {scene_id: SceneInfo}
        self.scenes: Dict[str, SceneInfo] = {}

        # ARObjects: {object_id: ARObjectInfo}
        # (object_id must be unique within its scene; uniqueness constraint enforced on operations)
        self.objects: Dict[str, ARObjectInfo] = {}

        # Constraints:
        # - object_id must be unique within its scene
        # - Objects can only be added to existing scenes
        # - Removing an object detaches it from the scene but does not affect other objects
        # - Attribute values for position, scale, and rotation must follow valid formats (e.g. scale non-negative)
        # - Scene and AR object metadata must persist across editing sessions

    def _is_object_referenced_elsewhere(self, object_id: str, excluding_scene_id: str) -> bool:
        for scene in self.scenes.values():
            if scene["scene_id"] == excluding_scene_id:
                continue
            if object_id in scene.get("object_ids", []):
                return True
        return False

    def get_scene_by_id(self, scene_id: str) -> dict:
        """
        Retrieve the full details (SceneInfo dictionary) of a scene given its scene_id.

        Args:
            scene_id (str): The unique identifier for the target scene.

        Returns:
            dict: {
                "success": True,
                "data": SceneInfo,  # Complete info of the scene if found
            }
            or
            {
                "success": False,
                "error": str  # "Scene not found"
            }
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            return { "success": False, "error": "Scene not found" }
        return { "success": True, "data": scene }

    def list_all_scenes(self) -> dict:
        """
        Retrieve a list of all AR scenes in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SceneInfo]  # List of all scenes (may be empty if none exist)
            }
        """
        all_scenes = list(self.scenes.values())
        return {
            "success": True,
            "data": all_scenes
        }

    def get_scene_object_ids(self, scene_id: str) -> dict:
        """
        Retrieve the list of object_ids contained in a specific scene.

        Args:
            scene_id (str): The identifier of the scene.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[str],  # List of object_ids (may be empty if no objects)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # "Scene does not exist"
                    }
        Constraints:
            - The scene_id must refer to an existing scene in the environment.
        """
        scene = self.scenes.get(scene_id)
        if not scene:
            return { "success": False, "error": "Scene does not exist" }
        return { "success": True, "data": list(scene["object_ids"]) }

    def get_object_by_id(self, object_id: str) -> dict:
        """
        Retrieve the full ARObjectInfo for a given object_id.

        Args:
            object_id (str): The identifier of the AR object to retrieve.

        Returns:
            dict: 
                - { "success": True, "data": ARObjectInfo } if object exists
                - { "success": False, "error": "Object not found" } if it doesn't

        Constraints:
            - object_id must exist in the system.
        """
        obj = self.objects.get(object_id)
        if obj is None:
            return { "success": False, "error": "Object not found" }
        return { "success": True, "data": obj }

    def list_objects_in_scene(self, scene_id: str) -> dict:
        """
        Retrieve full details (ARObjectInfo dicts) of all ARObjects in a specific scene.

        Args:
            scene_id (str): The identifier of the target AR scene.

        Returns:
            dict:
                - success: True and data: List[ARObjectInfo] if scene exists (may be empty if none in scene).
                - success: False and error: error message if scene not found.

        Constraints:
            - The specified scene_id must exist.
            - Only objects listed in the scene's object_ids and present in self.objects are returned.
        """
        if scene_id not in self.scenes:
            return {"success": False, "error": "Scene not found"}

        scene_info = self.scenes[scene_id]
        object_details = [
            self.objects[obj_id]
            for obj_id in scene_info["object_ids"]
            if obj_id in self.objects
        ]

        return {"success": True, "data": object_details}

    def check_object_id_uniqueness(self, scene_id: str, object_id: str) -> dict:
        """
        Check whether a given object_id is unique within the specified scene.

        Args:
            scene_id (str): The identifier of the scene to check within.
            object_id (str): The object_id to check for uniqueness.

        Returns:
            dict:
              - If scene does not exist: {"success": False, "error": "Scene does not exist"}
              - If scene exists: {"success": True, "is_unique": bool}
                'is_unique' is True if object_id is NOT present in scene's object_ids, else False.

        Constraints:
            - Only checks against the provided scene.
            - Scene must exist.
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            return {"success": False, "error": "Scene does not exist"}

        is_unique = object_id not in scene["object_ids"]
        return {"success": True, "is_unique": is_unique}

    def validate_transform_attributes(
        self,
        position: list,
        scale: list,
        rotation: list
    ) -> dict:
        """
        Validate that position, scale, and rotation attributes are correctly formatted and within allowed value ranges.

        Args:
            position (list of float): [x, y, z] coordinates. Must be of length 3, floats.
            scale (list of float): [sx, sy, sz] scale factors. Must be of length 3, non-negative floats.
            rotation (list of float): [rx, ry, rz] rotation (Euler angles assumed). Must be of length 3, floats.

        Returns:
            dict: {
                "success": True,
                "data": { "valid": True }
            }
            or (if invalid)
            {
                "success": True,
                "data": { "valid": False, "reason": "<reason>" }
            }

        Constraints:
            - Position, scale, and rotation must each be a list of 3 floats.
            - Scale must be non-negative.
        """

        # Helper function
        def is_float_list(val, length):
            if not isinstance(val, list):
                return False
            if len(val) != length:
                return False
            return all(isinstance(x, (float, int)) for x in val)

        # Validate position
        if not is_float_list(position, 3):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Position must be a list of 3 numbers."
                }
            }
        # Validate scale
        if not is_float_list(scale, 3):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Scale must be a list of 3 numbers."
                }
            }
        if any(s < 0 for s in scale):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Scale values must be non-negative."
                }
            }
        # Validate rotation
        if not is_float_list(rotation, 3):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Rotation must be a list of 3 numbers."
                }
            }

        return {
            "success": True,
            "data": { "valid": True }
        }

    def get_scene_metadata(self, scene_id: str) -> dict:
        """
        Retrieve the metadata dictionary for a specified scene.

        Args:
            scene_id (str): The unique identifier for the scene.

        Returns:
            dict: If successful,
                    {"success": True, "data": <scene metadata dict>}
                  If scene not found,
                    {"success": False, "error": "Scene not found"}
    
        Constraints:
            - The scene_id must exist in the environment.
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            return {"success": False, "error": "Scene not found"}
        return {"success": True, "data": scene["metadata"]}

    def get_object_metadata(self, object_id: str) -> dict:
        """
        Retrieve the metadata dictionary for the specified ARObject.

        Args:
            object_id (str): The unique identifier of the ARObject.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": Dict[str, Any]  # The metadata dictionary for the ARObject
                }
                On failure: {
                    "success": False,
                    "error": "Object ID does not exist"
                }
        Constraints:
            - object_id must exist in self.objects.
        """
        ar_object = self.objects.get(object_id)
        if not ar_object:
            return { "success": False, "error": "Object ID does not exist" }
        return { "success": True, "data": ar_object["metadata"] }

    def remove_object_from_scene(self, scene_id: str, object_id: str) -> dict:
        """
        Detach the specified ARObject from the given scene and remove its reference.
        Does not affect other objects.

        Args:
            scene_id (str): The ID of the scene from which to remove the object.
            object_id (str): The ID of the ARObject to remove.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Object <object_id> removed from scene <scene_id>."
                }
            or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Scene must exist.
            - Object must exist and be part of the specified scene.
        """
        # Check that the scene exists
        if scene_id not in self.scenes:
            return { "success": False, "error": f"Scene {scene_id} does not exist." }
    
        scene = self.scenes[scene_id]

        # Verify the object exists and is referenced by the scene.
        if object_id not in self.objects:
            return { "success": False, "error": f"Object {object_id} does not exist." }

        if object_id not in scene["object_ids"]:
            return { "success": False, "error": f"Object {object_id} does not belong to scene {scene_id}." }
    
        # Remove the object's reference from scene's object_ids
        scene["object_ids"].remove(object_id)

        # Remove the object entry itself only if no other scene still references it.
        if not self._is_object_referenced_elsewhere(object_id, excluding_scene_id=scene_id):
            del self.objects[object_id]

        return {
            "success": True,
            "message": f"Object {object_id} removed from scene {scene_id}."
        }

    def add_object_to_scene(
        self,
        scene_id: str,
        object_id: str,
        file_reference: str,
        position: list,
        scale: list,
        rotation: list,
        metadata: dict
    ) -> dict:
        """
        Instantiate and attach a new ARObject to an existing scene.
    
        Args:
            scene_id (str): ID of the scene to add the object to.
            object_id (str): Unique identifier for the new object (within the scene).
            file_reference (str): File/model reference for the AR object.
            position (list of float): [x, y, z] coordinates.
            scale (list of float): [sx, sy, sz], must be non-negative.
            rotation (list of float): [rx, ry, rz] or quaternion.
            metadata (dict): Additional metadata for the object.
    
        Returns:
            dict: 
              - { "success": True, "message": "ARObject <object_id> added to scene <scene_id>" }
              - or { "success": False, "error": "reason" }
    
        Constraints:
            - scene_id must exist.
            - object_id must be unique within its scene.
            - scale must be a list of 3 non-negative floats.
        """
        # Check scene existence
        if scene_id not in self.scenes:
            return { "success": False, "error": f"Scene {scene_id} does not exist" }

        # Check object_id uniqueness within scene
        for obj in self.objects.values():
            if obj['scene_id'] == scene_id and obj['object_id'] == object_id:
                return { "success": False, "error": f"Object ID {object_id} already exists in scene {scene_id}" }

        # Do not allow a new object to overwrite an existing object record referenced elsewhere.
        if object_id in self.objects:
            return { "success": False, "error": f"Object ID {object_id} already exists in the system" }

        # Validate position format
        if not (isinstance(position, list) and len(position) == 3 and all(isinstance(x, (int, float)) for x in position)):
            return { "success": False, "error": "Position must be a list of 3 numerical values" }

        # Validate scale format and non-negativity
        if not (isinstance(scale, list) and len(scale) == 3 and all(isinstance(x, (int, float)) for x in scale) and all(x >= 0 for x in scale)):
            return { "success": False, "error": "Scale must be a list of 3 non-negative numerical values" }

        # Validate rotation format
        if not (isinstance(rotation, list) and len(rotation) == 3 and all(isinstance(x, (int, float)) for x in rotation)):
            return { "success": False, "error": "Rotation must be a list of 3 numerical values" }

        # Build ARObject
        obj_info = {
            "object_id": object_id,
            "scene_id": scene_id,
            "file_reference": file_reference,
            "position": position,
            "scale": scale,
            "rotation": rotation,
            "metadata": metadata if isinstance(metadata, dict) else {}
        }
        self.objects[object_id] = obj_info

        # Attach object_id to scene
        self.scenes[scene_id]["object_ids"].append(object_id)

        return {
            "success": True,
            "message": f"ARObject {object_id} added to scene {scene_id}"
        }

    def update_object_attributes(
        self,
        object_id: str,
        position: list = None,
        scale: list = None,
        rotation: list = None,
        file_reference: str = None,
    ) -> dict:
        """
        Change an ARObject’s attributes (position, scale, rotation, file_reference) while validating constraints.

        Args:
            object_id (str): The ID of the ARObject to update.
            position (list, optional): [x, y, z] position values.
            scale (list, optional): [sx, sy, sz] scale values, must be all non-negative.
            rotation (list, optional): [rx, ry, rz] rotation values.
            file_reference (str, optional): Path or reference to the asset file.

        Returns:
            dict: {
                "success": True,
                "message": "Object attributes updated"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - object_id must exist.
            - scale must be all non-negative numbers.
            - position, scale, rotation (if provided) must be lists of 3 floats each.
            - file_reference, if provided, must be a string.
        """

        if object_id not in self.objects:
            return { "success": False, "error": "Object not found" }

        obj = self.objects[object_id]

        # Validate and update position
        if position is not None:
            if (
                not isinstance(position, list) or
                len(position) != 3 or
                not all(isinstance(v, (int, float)) for v in position)
            ):
                return {"success": False, "error": "Position must be a list of 3 numbers"}
            obj["position"] = [float(v) for v in position]

        # Validate and update scale
        if scale is not None:
            if (
                not isinstance(scale, list) or
                len(scale) != 3 or
                not all(isinstance(v, (int, float)) for v in scale)
            ):
                return {"success": False, "error": "Scale must be a list of 3 numbers"}
            if any(v < 0 for v in scale):
                return {"success": False, "error": "Scale values must be non-negative"}
            obj["scale"] = [float(v) for v in scale]

        # Validate and update rotation
        if rotation is not None:
            if (
                not isinstance(rotation, list) or
                len(rotation) != 3 or
                not all(isinstance(v, (int, float)) for v in rotation)
            ):
                return {"success": False, "error": "Rotation must be a list of 3 numbers"}
            obj["rotation"] = [float(v) for v in rotation]

        # Validate and update file_reference
        if file_reference is not None:
            if not isinstance(file_reference, str):
                return {"success": False, "error": "file_reference must be a string"}
            obj["file_reference"] = file_reference

        # Persist the update
        self.objects[object_id] = obj

        return { "success": True, "message": "Object attributes updated" }

    def update_scene_metadata(self, scene_id: str, new_metadata: Dict[str, Any]) -> dict:
        """
        Modify or add metadata entries for a specified scene.
        The new_metadata entries will update (overwrite or add to) the existing scene metadata.

        Args:
            scene_id (str): The unique identifier for the scene whose metadata is to be updated.
            new_metadata (Dict[str, Any]): Dictionary of new or updated metadata entries. Keys will overwrite or add to existing metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Scene metadata updated."
            }
            or
            {
                "success": False,
                "error": "Scene does not exist"
            }

        Constraints:
            - The target scene must already exist.
            - Metadata changes persist in the system.
        """
        if scene_id not in self.scenes:
            return { "success": False, "error": "Scene does not exist" }
    
        # Update scene metadata
        self.scenes[scene_id]['metadata'].update(new_metadata)
        return { "success": True, "message": "Scene metadata updated." }

    def update_object_metadata(self, object_id: str, new_metadata: Dict[str, Any]) -> dict:
        """
        Modify or add metadata entries to a specific ARObject, persisting changes.
    
        Args:
            object_id (str): The unique identifier of the AR object whose metadata is to be updated.
            new_metadata (Dict[str, Any]): Dictionary of metadata entries to add or update (key-value pairs).
    
        Returns:
            dict: {
                "success": True,
                "message": "Metadata updated for object <object_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The provided object_id must exist.
            - The update should preserve all other existing metadata entries unless overwritten.
            - New metadata entries are added, existing ones are updated in place.
        """
        if object_id not in self.objects:
            return { "success": False, "error": "Object does not exist" }
        if not isinstance(new_metadata, dict):
            return { "success": False, "error": "New metadata must be a dictionary" }

        obj = self.objects[object_id]
        # Update or add metadata entries
        obj["metadata"].update(new_metadata)
        # Persist the change
        self.objects[object_id] = obj

        return { "success": True, "message": f"Metadata updated for object {object_id}" }

    def delete_scene(self, scene_id: str) -> dict:
        """
        Permanently remove a scene and all its associated ARObjects.

        Args:
            scene_id (str): The ID of the scene to be removed.

        Returns:
            dict:
                - On success: { "success": True, "message": "Scene <scene_id> and all associated ARObjects deleted" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The scene must exist.
            - All ARObjects belonging to the scene must be deleted.
            - No effect on other scenes or unrelated ARObjects.
        """
        if scene_id not in self.scenes:
            return { "success": False, "error": f"Scene {scene_id} does not exist" }

        # Retrieve object_ids associated with this scene
        object_ids = self.scenes[scene_id]["object_ids"][:]

        # Remove scene entry first so shared object reference checks look at the remaining scenes.
        del self.scenes[scene_id]

        # Remove ARObjects that are no longer referenced by any remaining scene.
        for object_id in object_ids:
            if object_id in self.objects and not self._is_object_referenced_elsewhere(object_id, excluding_scene_id=""):
                del self.objects[object_id]

        return {
            "success": True,
            "message": f"Scene {scene_id} and all associated ARObjects deleted"
        }

    def duplicate_scene(self, source_scene_id: str, new_scene_id: str) -> dict:
        """
        Create a copy of an existing scene and all its AR objects with a new scene_id.
    
        Args:
            source_scene_id (str): The scene_id of the scene to duplicate.
            new_scene_id (str): The scene_id for the duplicated scene (must not already exist).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Scene duplicated successfully",
                        "new_scene_id": <new_scene_id>,
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - `source_scene_id` must exist in the state.
            - `new_scene_id` must not already exist.
            - All objects are duplicated, with new object_ids unique within the new scene.
        """
        # Check source scene exists
        if source_scene_id not in self.scenes:
            return { "success": False, "error": "Source scene does not exist." }

        # Check new_scene_id does not exist
        if new_scene_id in self.scenes:
            return { "success": False, "error": "New scene_id already exists." }
    
        source_scene = self.scenes[source_scene_id]
        new_object_ids = []
        obj_id_mapping = {}  # map old obj_id -> new obj_id

        # Duplicate each object in the source scene
        for obj_id in source_scene["object_ids"]:
            if obj_id not in self.objects:
                # Defensive: corrupt state, skip this object
                continue
            orig_obj_info = self.objects[obj_id]
            # Construct new unique object_id: new_scene_id + '_' + orig_id
            new_obj_id = f"{new_scene_id}_{obj_id}"
            # Ensure no collision globally (should not normally occur)
            if new_obj_id in self.objects:
                # Generate alternative id
                suffix = 1
                candidate = f"{new_obj_id}_{suffix}"
                while candidate in self.objects:
                    suffix += 1
                    candidate = f"{new_obj_id}_{suffix}"
                new_obj_id = candidate
            obj_id_mapping[obj_id] = new_obj_id
            new_object_ids.append(new_obj_id)
            # Copy ARObjectInfo and update scene_id and object_id
            new_obj_info = copy.deepcopy(orig_obj_info)
            new_obj_info["object_id"] = new_obj_id
            new_obj_info["scene_id"] = new_scene_id
            # Add to system
            self.objects[new_obj_id] = new_obj_info

        # Duplicate the scene info
        new_scene_info = copy.deepcopy(source_scene)
        new_scene_info["scene_id"] = new_scene_id
        # Optional: maybe update the name to reflect duplication
        new_scene_info["name"] = source_scene["name"] + " (Copy)"
        new_scene_info["object_ids"] = new_object_ids

        self.scenes[new_scene_id] = new_scene_info

        return {
            "success": True,
            "message": "Scene duplicated successfully",
            "new_scene_id": new_scene_id
        }


class ARSceneManagementSystem(BaseEnv):
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

    def get_scene_by_id(self, **kwargs):
        return self._call_inner_tool('get_scene_by_id', kwargs)

    def list_all_scenes(self, **kwargs):
        return self._call_inner_tool('list_all_scenes', kwargs)

    def get_scene_object_ids(self, **kwargs):
        return self._call_inner_tool('get_scene_object_ids', kwargs)

    def get_object_by_id(self, **kwargs):
        return self._call_inner_tool('get_object_by_id', kwargs)

    def list_objects_in_scene(self, **kwargs):
        return self._call_inner_tool('list_objects_in_scene', kwargs)

    def check_object_id_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_object_id_uniqueness', kwargs)

    def validate_transform_attributes(self, **kwargs):
        return self._call_inner_tool('validate_transform_attributes', kwargs)

    def get_scene_metadata(self, **kwargs):
        return self._call_inner_tool('get_scene_metadata', kwargs)

    def get_object_metadata(self, **kwargs):
        return self._call_inner_tool('get_object_metadata', kwargs)

    def remove_object_from_scene(self, **kwargs):
        return self._call_inner_tool('remove_object_from_scene', kwargs)

    def add_object_to_scene(self, **kwargs):
        return self._call_inner_tool('add_object_to_scene', kwargs)

    def update_object_attributes(self, **kwargs):
        return self._call_inner_tool('update_object_attributes', kwargs)

    def update_scene_metadata(self, **kwargs):
        return self._call_inner_tool('update_scene_metadata', kwargs)

    def update_object_metadata(self, **kwargs):
        return self._call_inner_tool('update_object_metadata', kwargs)

    def delete_scene(self, **kwargs):
        return self._call_inner_tool('delete_scene', kwargs)

    def duplicate_scene(self, **kwargs):
        return self._call_inner_tool('duplicate_scene', kwargs)
