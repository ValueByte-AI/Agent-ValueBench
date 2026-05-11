# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, Any, TypedDict



class FaceEntryInfo(TypedDict, total=False):
    face_uid: str
    biometric_data: str  # Represents facial template, image, or encoded features
    registration_timestamp: str
    metadata: Optional[Dict[str, Any]]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a face recognition database system.
        """

        # Face entries: {face_uid: FaceEntryInfo}
        # - Maps each unique face_uid to its registration data, biometric data, and optional metadata
        self.face_entries: Dict[str, FaceEntryInfo] = {}

        # Constraints:
        # - Each face_uid is unique within the system.
        # - Biometric data must be associated with every face_uid.
        # - Metadata is optional, but must be allowed and retrievable if present.
        # - Deleting a face entry must remove all its biometric data and metadata.

    def list_face_uids(self) -> dict:
        """
        Retrieve a list of all currently registered face_uids in the face recognition database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # list of all current face_uids, may be empty
            }

        Constraints:
            - face_uids are unique and maintained by the system.
            - If no faces are registered, an empty list is returned.
        """
        face_uids = list(self.face_entries.keys())
        return { "success": True, "data": face_uids }

    def get_face_entry(self, face_uid: str) -> dict:
        """
        Retrieve the complete FaceEntryInfo for the specified face_uid.

        Args:
            face_uid (str): Unique identifier for the face entry.

        Returns:
            dict: {
                "success": True,
                "data": FaceEntryInfo,  # Full information for the face_uid.
            }
            or
            {
                "success": False,
                "error": str  # Describes the error, e.g., entry not found
            }

        Constraints:
            - face_uid must uniquely exist in the system.
        """
        entry = self.face_entries.get(face_uid)
        if entry is None:
            return { "success": False, "error": "Face entry not found" }

        return { "success": True, "data": entry }

    def search_face_entries_by_metadata(self, search_criteria: Dict[str, Any]) -> dict:
        """
        Find all face entries whose metadata include all the specific key-value pairs provided.

        Args:
            search_criteria (Dict[str, Any]):
                The metadata key-value pairs to match (e.g., {"name": "Alice", "access_level": 3}).
                If empty, returns all face entries that have any metadata.

        Returns:
            dict with:
                - "success": True
                - "data": List[FaceEntryInfo] (matching face entries; may be empty)

        Constraints:
            - An entry matches only if its metadata includes all key-value pairs in search_criteria.
            - If entry's metadata is None/missing, it will not match.
        """
        result = []
        for entry in self.face_entries.values():
            metadata = entry.get("metadata")
            if metadata is not None:
                # If search_criteria is empty, match all entries with any metadata
                if not search_criteria:
                    result.append(entry)
                else:
                    # Check all k/v pairs in search_criteria match in metadata
                    if all(metadata.get(k) == v for k, v in search_criteria.items()):
                        result.append(entry)
        return { "success": True, "data": result }

    def get_metadata_for_face_uid(self, face_uid: str) -> dict:
        """
        Retrieve the metadata dictionary (if present) for a specific face_uid.

        Args:
            face_uid (str): The unique identifier for the face entry.

        Returns:
            dict: {
                "success": True,
                "data": Optional[Dict[str, Any]],  # Metadata dictionary or None if not present
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., face_uid not found
            }

        Constraints:
            - face_uid must exist in the database.
            - Metadata is optional; if not present, 'data' will be None.
        """
        if face_uid not in self.face_entries:
            return { "success": False, "error": "face_uid not found" }

        face_entry = self.face_entries[face_uid]
        metadata = face_entry.get("metadata", None)
        return { "success": True, "data": metadata }

    def exists_face_uid(self, face_uid: str) -> dict:
        """
        Check whether a given face_uid exists in the system.

        Args:
            face_uid (str): Unique identifier for the face entry.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if the face_uid exists, False otherwise
            }
        """
        exists = face_uid in self.face_entries
        return { "success": True, "data": exists }

    def register_new_face_entry(
        self, 
        face_uid: str, 
        biometric_data: str, 
        registration_timestamp: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Registers a new face entry in the database with a unique face_uid, associated biometric data, registration timestamp, 
        and optional metadata.

        Args:
            face_uid (str): Unique identifier for the face (must not exist).
            biometric_data (str): Facial biometric data (required, cannot be None or empty).
            registration_timestamp (str): ISO8601 or other formatted registration timestamp.
            metadata (Optional[Dict[str, Any]]): Optional metadata dictionary.

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "<face_uid> registered successfully" }
                On failure: 
                    { "success": False, "error": "reason" }

        Constraints:
            - face_uid must be unique in the system.
            - biometric_data is required (must not be None or empty).
            - metadata is optional.
        """
        if face_uid in self.face_entries:
            return { "success": False, "error": "face_uid already exists" }
        if not biometric_data or not isinstance(biometric_data, str):
            return { "success": False, "error": "biometric_data is required and must be a non-empty string" }

        entry: FaceEntryInfo = {
            "face_uid": face_uid,
            "biometric_data": biometric_data,
            "registration_timestamp": registration_timestamp
        }
        if metadata is not None:
            entry["metadata"] = metadata

        self.face_entries[face_uid] = entry

        return { "success": True, "message": f"{face_uid} registered successfully" }

    def update_face_metadata(self, face_uid: str, metadata: dict) -> dict:
        """
        Add or modify metadata for an existing face_uid.

        Args:
            face_uid (str): Unique identifier of the face entry to update.
            metadata (dict): Metadata fields to add or update (merges with existing).

        Returns:
            dict:
                - On success: { "success": True, "message": "Metadata updated for face_uid <face_uid>" }
                - On failure: { "success": False, "error": "Face UID not found" }

        Constraints:
            - face_uid must exist in the system.
            - Metadata may be created if not already present.
        """
        entry = self.face_entries.get(face_uid)
        if not entry:
            return { "success": False, "error": "Face UID not found" }

        # Initialize or update metadata
        if entry.get("metadata") is None:
            entry["metadata"] = {}

        # Merge/overwrite metadata fields
        entry["metadata"].update(metadata)

        return { "success": True, "message": f"Metadata updated for face_uid {face_uid}" }

    def delete_face_entry(self, face_uid: str) -> dict:
        """
        Delete the face entry for the given face_uid, ensuring all associated biometric data
        and metadata are also removed.

        Args:
            face_uid (str): The unique identifier of the face entry to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Face entry deleted successfully." }
                - On failure: { "success": False, "error": "Face UID does not exist." }

        Constraints:
            - If the face_uid does not exist, the operation fails.
            - All associated data (biometric_data, metadata) are deleted.
        """
        if face_uid not in self.face_entries:
            return { "success": False, "error": "Face UID does not exist." }

        del self.face_entries[face_uid]
        return { "success": True, "message": "Face entry deleted successfully." }

    def update_biometric_data(self, face_uid: str, new_biometric_data: str) -> dict:
        """
        Replace the biometric data for a given face_uid.

        Args:
            face_uid (str): Unique identifier of the face entry.
            new_biometric_data (str): New biometric data string to store.

        Returns:
            dict:
              - On success: {"success": True, "message": "Biometric data updated for face_uid <face_uid>"}
              - On failure (face_uid does not exist): {"success": False, "error": "Face UID not found"}
              - On invalid biometric data: {"success": False, "error": "Invalid biometric data"}

        Constraints:
            - face_uid must exist in the system.
            - new_biometric_data must be non-empty (str).
        """
        if face_uid not in self.face_entries:
            return {"success": False, "error": "Face UID not found"}

        if not isinstance(new_biometric_data, str) or not new_biometric_data.strip():
            return {"success": False, "error": "Invalid biometric data"}

        self.face_entries[face_uid]['biometric_data'] = new_biometric_data
        return {"success": True, "message": f"Biometric data updated for face_uid {face_uid}"}


class FaceRecognitionDatabaseSystem(BaseEnv):
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

    def list_face_uids(self, **kwargs):
        return self._call_inner_tool('list_face_uids', kwargs)

    def get_face_entry(self, **kwargs):
        return self._call_inner_tool('get_face_entry', kwargs)

    def search_face_entries_by_metadata(self, **kwargs):
        return self._call_inner_tool('search_face_entries_by_metadata', kwargs)

    def get_metadata_for_face_uid(self, **kwargs):
        return self._call_inner_tool('get_metadata_for_face_uid', kwargs)

    def exists_face_uid(self, **kwargs):
        return self._call_inner_tool('exists_face_uid', kwargs)

    def register_new_face_entry(self, **kwargs):
        return self._call_inner_tool('register_new_face_entry', kwargs)

    def update_face_metadata(self, **kwargs):
        return self._call_inner_tool('update_face_metadata', kwargs)

    def delete_face_entry(self, **kwargs):
        return self._call_inner_tool('delete_face_entry', kwargs)

    def update_biometric_data(self, **kwargs):
        return self._call_inner_tool('update_biometric_data', kwargs)

