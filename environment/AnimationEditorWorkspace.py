# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid



# TypedDicts representing workspace entities

class AnimationSequenceInfo(TypedDict):
    sequence_id: str
    name: str
    metadata: Any
    timeline_id_list: List[str]

class TimelineInfo(TypedDict):
    timeline_id: str
    sequence_id: str
    keyframe_id_list: List[str]
    event_id_list: List[str]

class KeyframeInfo(TypedDict):
    keyframe_id: str
    timeline_id: str
    frame_number: int
    prop: Any

class EventInfo(TypedDict):
    event_id: str
    timeline_id: str
    name: str
    frame_number: int
    param: Any

class AssetInfo(TypedDict):
    asset_id: str
    type: str
    uri: str
    metadata: Any

class ProjectInfo(TypedDict):
    project_id: str
    sequence_id_list: List[str]
    asset_id_list: List[str]
    metadata: Any

class _GeneratedEnvImpl:
    def __init__(self):
        # Animation Sequences: {sequence_id: AnimationSequenceInfo}
        self.sequences: Dict[str, AnimationSequenceInfo] = {}
        # Timelines: {timeline_id: TimelineInfo}
        self.timelines: Dict[str, TimelineInfo] = {}
        # Keyframes: {keyframe_id: KeyframeInfo}
        self.keyframes: Dict[str, KeyframeInfo] = {}
        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}
        # Assets: {asset_id: AssetInfo}
        self.assets: Dict[str, AssetInfo] = {}
        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}
        
        # Constraint annotations:
        # - Sequence names must be unique within a project.
        # - Each timeline is associated with exactly one sequence.
        # - Keyframes in a timeline must have unique frame numbers.
        # - Events in a timeline must reference valid frame numbers.
        # - Assets must exist to be referenced by sequences, keyframes, or events.

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve project information by project_id, including lists of sequences and assets.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": ProjectInfo
                    }
                On error:
                    {
                      "success": False,
                      "error": str
                    }

        Constraints:
            - The project_id must exist in self.projects.
        """
        if not isinstance(project_id, str) or not project_id:
            return { "success": False, "error": "Invalid project_id provided." }
    
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": f"Project with id '{project_id}' does not exist." }
    
        return { "success": True, "data": project }

    def list_sequences_in_project(self, project_id: str) -> dict:
        """
        List all animation sequences (full metadata) associated with the specified project.

        Args:
            project_id (str): The project identifier.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[AnimationSequenceInfo],  # May be empty if project has no sequences
                }
                - On failure: {
                    "success": False,
                    "error": str,  # "Project not found"
                }

        Constraints:
            - The project_id must refer to an existing project.
            - Sequence IDs referenced in the project that do not exist in self.sequences are silently ignored.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project not found" }

        sequence_id_list = self.projects[project_id].get("sequence_id_list", [])
        result = []
        for seq_id in sequence_id_list:
            seq_info = self.sequences.get(seq_id)
            if seq_info is not None:
                result.append(seq_info)

        return { "success": True, "data": result }

    def get_sequence_by_name(self, project_id: str, name: str) -> dict:
        """
        Retrieve an AnimationSequence by its unique name within a specific project.

        Args:
            project_id (str): The ID of the project in which to search for the sequence.
            name (str): The name of the animation sequence to look up.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": AnimationSequenceInfo,
                  }
                - On failure: {
                      "success": False,
                      "error": str,
                  }

        Constraints:
            - Sequence names are unique within a project.
            - Project must exist.
        """

        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": "Project does not exist"}

        for seq_id in project["sequence_id_list"]:
            seq = self.sequences.get(seq_id)
            if seq and seq["name"] == name:
                return {"success": True, "data": seq}

        return {"success": False, "error": "No such sequence exists by that name in this project"}

    def get_sequence_by_id(self, sequence_id: str) -> dict:
        """
        Retrieve a sequence's full information using its unique id.

        Args:
            sequence_id (str): The unique identifier of the animation sequence.

        Returns:
            dict: 
                - { "success": True, "data": AnimationSequenceInfo } if found
                - { "success": False, "error": "Sequence not found" } if not found

        Constraints:
            - The sequence must exist in the workspace.
        """
        seq = self.sequences.get(sequence_id)
        if seq is None:
            return { "success": False, "error": "Sequence not found" }
        return { "success": True, "data": seq }

    def list_timelines_for_sequence(self, sequence_id: str) -> dict:
        """
        Retrieve all timelines associated with the specified animation sequence.

        Args:
            sequence_id (str): The unique identifier of the animation sequence.

        Returns:
            dict:
                - If sequence exists:
                    { "success": True, "data": List[TimelineInfo] }
                - If sequence does not exist:
                    { "success": False, "error": "Sequence does not exist" }

        Constraints:
            - The sequence_id must exist in the workspace.
            - Returns all timelines where timeline.sequence_id == sequence_id.
        """
        if sequence_id not in self.sequences:
            return {"success": False, "error": "Sequence does not exist"}

        timelines = [
            timeline for timeline in self.timelines.values()
            if timeline["sequence_id"] == sequence_id
        ]
        return {"success": True, "data": timelines}

    def get_timeline_by_id(self, timeline_id: str) -> dict:
        """
        Retrieve timeline details using the given timeline_id.

        Args:
            timeline_id (str): The unique identifier of the timeline.

        Returns:
            dict:
                - success: True and data containing TimelineInfo if found
                - success: False and error message if timeline_id not found

        Constraints:
            - The timeline must exist (present in self.timelines).
        """
        timeline = self.timelines.get(timeline_id)
        if timeline is None:
            return { "success": False, "error": "Timeline not found" }
        return { "success": True, "data": timeline }

    def list_keyframes_in_timeline(self, timeline_id: str) -> dict:
        """
        List all keyframes within a single timeline.

        Args:
            timeline_id (str): The unique identifier of the timeline to query.

        Returns:
            dict: {
                "success": True,
                "data": List[KeyframeInfo],  # List of keyframe info in the timeline (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. timeline does not exist
            }

        Constraints:
            - Timeline must exist in workspace.
        """
        if timeline_id not in self.timelines:
            return { "success": False, "error": "Timeline does not exist" }

        timeline = self.timelines[timeline_id]
        keyframe_id_list = timeline.get("keyframe_id_list", [])

        keyframes = [
            self.keyframes[keyframe_id]
            for keyframe_id in keyframe_id_list
            if keyframe_id in self.keyframes
        ]

        return { "success": True, "data": keyframes }

    def get_asset_by_id(self, asset_id: str) -> dict:
        """
        Retrieve asset details by asset_id.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": AssetInfo   # The asset metadata dictionary
                    }
                On failure:
                    {
                        "success": False,
                        "error": str        # Description of the error (e.g., "Asset not found")
                    }
        Constraints:
            - The given asset_id must exist in the workspace.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset not found"}
        return {"success": True, "data": asset}

    def list_project_assets(self, project_id: str) -> dict:
        """
        List all assets associated with a given project.

        Args:
            project_id (str): The unique identifier of the project.
    
        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of assets for the project (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of failure, e.g., project does not exist
            }

        Constraints:
            - The project must exist in the workspace.
            - Only assets present in self.assets and listed in the project's asset_id_list are returned.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        asset_id_list = self.projects[project_id].get("asset_id_list", [])
        asset_list = [
            self.assets[asset_id]
            for asset_id in asset_id_list
            if asset_id in self.assets
        ]
        return { "success": True, "data": asset_list }

    def create_sequence(self, project_id: str, name: str, metadata: Any = None) -> dict:
        """
        Create a new animation sequence (with a unique name) in a specific project.

        Args:
            project_id (str): ID of the project where the sequence will be created.
            name (str): Desired sequence name (must be unique within the project).
            metadata (Any, optional): Optional metadata for the sequence.

        Returns:
            dict: Either:
                {"success": True, "message": "Sequence created successfully", "sequence_id": <sequence_id>}
            or
                {"success": False, "error": <reason>}
    
        Constraints:
            - Project with project_id must exist.
            - Sequence name must be unique within the project.
        """
        # Check if project exists
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project does not exist"}

        # Check for name uniqueness within the project
        for seq_id in project["sequence_id_list"]:
            sequence = self.sequences.get(seq_id)
            if sequence and sequence["name"] == name:
                return {"success": False, "error": "Sequence name already exists in project"}
    
        # Generate unique sequence_id (simple approach: use prefix + count)
        sequence_id = f"seq_{uuid.uuid4().hex[:8]}"
        while sequence_id in self.sequences:
            sequence_id = f"seq_{uuid.uuid4().hex[:8]}"

        # Build and save sequence info
        sequence_info = AnimationSequenceInfo(
            sequence_id=sequence_id,
            name=name,
            metadata=metadata,
            timeline_id_list=[],
        )
        self.sequences[sequence_id] = sequence_info

        # Add sequence to project
        project["sequence_id_list"].append(sequence_id)

        return {
            "success": True,
            "message": "Sequence created successfully",
            "sequence_id": sequence_id
        }

    def add_sequence_to_project(self, project_id: str, sequence_id: str) -> dict:
        """
        Add an existing sequence to a project's sequence list, if not already present.

        Args:
            project_id (str): ID of the target project.
            sequence_id (str): ID of the sequence to add.

        Returns:
            dict: {
                "success": True,
                "message": "Sequence added to project."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Project must exist.
            - Sequence must exist.
            - Sequence can only be added once to a project.
        """
        # Check if project exists
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found."}

        # Check if sequence exists
        if sequence_id not in self.sequences:
            return {"success": False, "error": "Sequence not found."}

        # Check if sequence is already associated with project
        project = self.projects[project_id]
        if sequence_id in project["sequence_id_list"]:
            return {"success": False, "error": "Sequence already in project."}

        # Add sequence to project
        project["sequence_id_list"].append(sequence_id)

        return {"success": True, "message": "Sequence added to project."}

    def create_timeline_for_sequence(self, sequence_id: str) -> dict:
        """
        Create a new timeline and associate it with the specified animation sequence.

        Args:
            sequence_id (str): The ID of the AnimationSequence to attach the new timeline to.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Timeline created and associated with sequence.",
                    "timeline_id": <str>
                }
            On failure:
                {
                    "success": False,
                    "error": <str, explanation>
                }

        Constraints:
            - The given sequence_id must exist.
            - Each timeline must have a unique timeline_id.
            - The new timeline is associated with exactly one sequence.
        """

        # Sequence must exist
        if sequence_id not in self.sequences:
            return {"success": False, "error": "Animation sequence does not exist."}

        # Generate unique timeline_id
        for _ in range(5):  # try up to 5 times to get a unique id
            timeline_id = "tl_" + uuid.uuid4().hex[:12]
            if timeline_id not in self.timelines:
                break
        else:
            return {"success": False, "error": "Failed to generate unique timeline ID."}

        # Create TimelineInfo
        timeline_info = {
            "timeline_id": timeline_id,
            "sequence_id": sequence_id,
            "keyframe_id_list": [],
            "event_id_list": []
        }

        # Add to timelines
        self.timelines[timeline_id] = timeline_info

        # Add timeline_id to sequence's timeline_id_list
        self.sequences[sequence_id]["timeline_id_list"].append(timeline_id)

        return {
            "success": True,
            "message": f"Timeline created and associated with sequence.",
            "timeline_id": timeline_id
        }

    def set_sequence_metadata(self, sequence_id: str, metadata: Any) -> dict:
        """
        Set or update metadata for an animation sequence.

        Args:
            sequence_id (str): The unique identifier of the animation sequence.
            metadata (Any): The metadata to set/update for the sequence.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Metadata updated for sequence <sequence_id>."}
                - On failure: {"success": False, "error": "Sequence not found."}

        Constraints:
            - The specified sequence_id must exist in the workspace.
        """
        if sequence_id not in self.sequences:
            return {"success": False, "error": "Sequence not found."}
    
        self.sequences[sequence_id]["metadata"] = metadata
        return {"success": True, "message": f"Metadata updated for sequence {sequence_id}."}

    def rename_sequence(self, project_id: str, sequence_id: str, new_name: str) -> dict:
        """
        Rename an existing sequence, enforcing uniqueness of name within the project.

        Args:
            project_id (str): The ID of the project containing the sequence.
            sequence_id (str): The sequence to rename.
            new_name (str): The new unique name for the sequence.

        Returns:
            dict: {
                "success": True,
                "message": str  # Operation description
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - Sequence names must be unique within a project.
            - Target project and sequence must exist and be valid.
        """
        # Check project exists
        project = self.projects.get(project_id)
        if project is None:
            return {"success": False, "error": f"Project '{project_id}' does not exist."}
    
        # Check sequence exists
        if sequence_id not in self.sequences:
            return {"success": False, "error": f"Sequence '{sequence_id}' does not exist."}
        if sequence_id not in project["sequence_id_list"]:
            return {"success": False, "error": f"Sequence '{sequence_id}' is not part of project '{project_id}'."}

        # Check uniqueness of the new name in this project
        for sid in project["sequence_id_list"]:
            if sid == sequence_id:
                continue
            seq_info = self.sequences.get(sid)
            if seq_info and seq_info["name"] == new_name:
                return {
                    "success": False,
                    "error": f"A sequence with name '{new_name}' already exists in project '{project_id}'."
                }
    
        # Perform rename
        sequence_info = self.sequences[sequence_id]
        old_name = sequence_info["name"]
        sequence_info["name"] = new_name

        return {
            "success": True,
            "message": f"Sequence '{old_name}' has been renamed to '{new_name}' in project '{project_id}'."
        }

    def delete_sequence(self, sequence_id: str) -> dict:
        """
        Remove a sequence from the workspace, including:
        - Removing from self.sequences.
        - Removing from the containing project's sequence_id_list.
        - Deleting associated timelines, their keyframes, and events.

        Args:
            sequence_id (str): The ID of the sequence to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Sequence deleted."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Sequence must exist.
            - Remove all associated timelines, keyframes, events.
            - Remove references from all projects.
        """
        # 1. Check if the sequence exists
        if sequence_id not in self.sequences:
            return {"success": False, "error": "Sequence does not exist."}

        # 2. Remove sequence_id from all projects' sequence_id_list
        for project in self.projects.values():
            if sequence_id in project["sequence_id_list"]:
                project["sequence_id_list"].remove(sequence_id)

        # 3. Delete associated timelines, keyframes, and events
        sequence_info = self.sequences[sequence_id]
        timeline_ids = sequence_info.get("timeline_id_list", [])

        for timeline_id in timeline_ids:
            # Delete keyframes in this timeline
            timeline_info = self.timelines.get(timeline_id)
            if timeline_info:
                for keyframe_id in timeline_info.get("keyframe_id_list", []):
                    if keyframe_id in self.keyframes:
                        del self.keyframes[keyframe_id]
                for event_id in timeline_info.get("event_id_list", []):
                    if event_id in self.events:
                        del self.events[event_id]
                # Delete the timeline itself
                del self.timelines[timeline_id]

        # 4. Delete the sequence itself
        del self.sequences[sequence_id]

        return {"success": True, "message": "Sequence deleted."}

    def add_timeline_to_sequence(self, sequence_id: str, timeline_id: str) -> dict:
        """
        Add an existing timeline to the specified animation sequence's timeline list.

        Args:
            sequence_id (str): ID of the animation sequence to update.
            timeline_id (str): ID of the timeline to add.

        Returns:
            dict: {
                "success": True,
                "message": "Timeline added to sequence."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Both sequence and timeline must exist.
            - Timeline must already be associated with the same sequence (timeline_info["sequence_id"] == sequence_id).
            - Timeline must not already be in the sequence's timeline list.
            - Each timeline is associated with exactly one sequence.
        """
        if sequence_id not in self.sequences:
            return { "success": False, "error": "Sequence ID does not exist." }
        if timeline_id not in self.timelines:
            return { "success": False, "error": "Timeline ID does not exist." }
        sequence_info = self.sequences[sequence_id]
        timeline_info = self.timelines[timeline_id]

        # Ensure timeline is associated with this sequence
        if timeline_info["sequence_id"] != sequence_id:
            return { "success": False, "error": "Timeline is not associated with this sequence." }

        # Check for duplicate
        if timeline_id in sequence_info["timeline_id_list"]:
            return { "success": False, "error": "Timeline already present in sequence." }

        # Add timeline_id
        sequence_info["timeline_id_list"].append(timeline_id)
        return { "success": True, "message": "Timeline added to sequence." }

    def remove_sequence_from_project(self, project_id: str, sequence_id: str) -> dict:
        """
        Remove a given sequence (sequence_id) from a specific project's (project_id) sequence collection.
    
        Args:
            project_id (str): The ID of the target project.
            sequence_id (str): The ID of the sequence to remove.
    
        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message on success.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., missing project/sequence).
            }
    
        Constraints:
            - Project must exist.
            - Sequence must exist.
            - Sequence must be in the project's sequence list.
            - Only removes the reference; does not delete the sequence.
        """
        # Check if project exists
        if project_id not in self.projects:
            return {"success": False, "error": f"Project {project_id} does not exist."}
    
        # Check if sequence exists
        if sequence_id not in self.sequences:
            return {"success": False, "error": f"Sequence {sequence_id} does not exist."}
    
        project = self.projects[project_id]
        if sequence_id not in project["sequence_id_list"]:
            return {
                "success": False,
                "error": f"Sequence {sequence_id} is not part of project {project_id}."
            }
    
        # Remove the sequence from the project's list
        project["sequence_id_list"].remove(sequence_id)
        return {
            "success": True,
            "message": f"Sequence {sequence_id} removed from project {project_id}."
        }

    def duplicate_sequence(
        self, 
        project_id: str, 
        source_sequence_id: str, 
        new_sequence_name: str
    ) -> dict:
        """
        Copy an existing animation sequence, including its timelines, keyframes, and events.
        The duplicate is assigned a new unique sequence_id and placed in the specified project under a unique name.
    
        Args:
            project_id (str): ID of the project in which to duplicate the sequence.
            source_sequence_id (str): The ID of the sequence to copy.
            new_sequence_name (str): The desired unique name for the new sequence.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Sequence duplicated successfully",
                    "new_sequence_id": str
                }
            OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Project must exist.
            - Source sequence must exist.
            - New sequence name must NOT be used by any sequence in the target project.
            - All timelines, keyframes, and events are deeply copied with new IDs referencing the duplicate sequence/timeline.
        """
        # Check project existence
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project does not exist"}
    
        # Check source sequence existence
        source_seq = self.sequences.get(source_sequence_id)
        if not source_seq:
            return {"success": False, "error": "Source sequence does not exist"}
    
        # Sequence name uniqueness in project
        for seq_id in project["sequence_id_list"]:
            seq = self.sequences.get(seq_id)
            if seq and seq["name"] == new_sequence_name:
                return {"success": False, "error": "A sequence with this name already exists in the project"}

        # Generate new sequence_id
        new_seq_id = str(uuid.uuid4())
        new_timeline_ids = []
        old_to_new_timeline = {}
        old_to_new_keyframe = {}
        old_to_new_event = {}

        # Duplicating timelines
        for old_timeline_id in source_seq["timeline_id_list"]:
            old_timeline = self.timelines.get(old_timeline_id)
            if not old_timeline:
                continue  # skip missing timelines
        
            # Create new timeline id
            new_timeline_id = str(uuid.uuid4())
            old_to_new_timeline[old_timeline_id] = new_timeline_id
            new_timeline_ids.append(new_timeline_id

            )

            # Duplicate keyframes with new ids
            new_keyframe_ids = []
            for old_kf_id in old_timeline["keyframe_id_list"]:
                old_kf = self.keyframes.get(old_kf_id)
                if not old_kf:
                    continue
                new_kf_id = str(uuid.uuid4())
                old_to_new_keyframe[old_kf_id] = new_kf_id
                new_keyframe_ids.append(new_kf_id)
                self.keyframes[new_kf_id] = KeyframeInfo(
                    keyframe_id=new_kf_id,
                    timeline_id=new_timeline_id,
                    frame_number=old_kf["frame_number"],
                    prop=old_kf["prop"]
                )

            # Duplicate events with new ids
            new_event_ids = []
            for old_ev_id in old_timeline["event_id_list"]:
                old_ev = self.events.get(old_ev_id)
                if not old_ev:
                    continue
                new_ev_id = str(uuid.uuid4())
                old_to_new_event[old_ev_id] = new_ev_id
                new_event_ids.append(new_ev_id)
                self.events[new_ev_id] = EventInfo(
                    event_id=new_ev_id,
                    timeline_id=new_timeline_id,
                    name=old_ev["name"],
                    frame_number=old_ev["frame_number"],
                    param=old_ev["param"]
                )

            # Create new timeline
            self.timelines[new_timeline_id] = TimelineInfo(
                timeline_id=new_timeline_id,
                sequence_id=new_seq_id,
                keyframe_id_list=new_keyframe_ids,
                event_id_list=new_event_ids
            )

        # Create new sequence info
        self.sequences[new_seq_id] = AnimationSequenceInfo(
            sequence_id=new_seq_id,
            name=new_sequence_name,
            metadata=source_seq["metadata"],
            timeline_id_list=new_timeline_ids
        )

        # Add new sequence to project
        project["sequence_id_list"].append(new_seq_id)
    
        return {
            "success": True,
            "message": "Sequence duplicated successfully",
            "new_sequence_id": new_seq_id
        }


class AnimationEditorWorkspace(BaseEnv):
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

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def list_sequences_in_project(self, **kwargs):
        return self._call_inner_tool('list_sequences_in_project', kwargs)

    def get_sequence_by_name(self, **kwargs):
        return self._call_inner_tool('get_sequence_by_name', kwargs)

    def get_sequence_by_id(self, **kwargs):
        return self._call_inner_tool('get_sequence_by_id', kwargs)

    def list_timelines_for_sequence(self, **kwargs):
        return self._call_inner_tool('list_timelines_for_sequence', kwargs)

    def get_timeline_by_id(self, **kwargs):
        return self._call_inner_tool('get_timeline_by_id', kwargs)

    def list_keyframes_in_timeline(self, **kwargs):
        return self._call_inner_tool('list_keyframes_in_timeline', kwargs)

    def get_asset_by_id(self, **kwargs):
        return self._call_inner_tool('get_asset_by_id', kwargs)

    def list_project_assets(self, **kwargs):
        return self._call_inner_tool('list_project_assets', kwargs)

    def create_sequence(self, **kwargs):
        return self._call_inner_tool('create_sequence', kwargs)

    def add_sequence_to_project(self, **kwargs):
        return self._call_inner_tool('add_sequence_to_project', kwargs)

    def create_timeline_for_sequence(self, **kwargs):
        return self._call_inner_tool('create_timeline_for_sequence', kwargs)

    def set_sequence_metadata(self, **kwargs):
        return self._call_inner_tool('set_sequence_metadata', kwargs)

    def rename_sequence(self, **kwargs):
        return self._call_inner_tool('rename_sequence', kwargs)

    def delete_sequence(self, **kwargs):
        return self._call_inner_tool('delete_sequence', kwargs)

    def add_timeline_to_sequence(self, **kwargs):
        return self._call_inner_tool('add_timeline_to_sequence', kwargs)

    def remove_sequence_from_project(self, **kwargs):
        return self._call_inner_tool('remove_sequence_from_project', kwargs)

    def duplicate_sequence(self, **kwargs):
        return self._call_inner_tool('duplicate_sequence', kwargs)

