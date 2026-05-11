# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class ProjectInfo(TypedDict):
    project_id: str
    project_name: str
    description: str
    created_date: str
    owner_user_id: str
    member_user_id: List[str]  # List of user IDs

class DatasetInfo(TypedDict):
    dataset_id: str
    dataset_name: str
    description: str
    file_format: str
    upload_date: str
    uploader_user_id: str
    associated_project_id: List[str]  # Datasets may belong to multiple projects
    metadata: Dict[str, Any]
    file_location: str

class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    role: str
    account_status: str

class PermissionInfo(TypedDict):
    _id: str
    project_id: str
    access_level: str  # e.g., "read", "write", "admin"

class _GeneratedEnvImpl:
    def __init__(self):
        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Datasets: {dataset_id: DatasetInfo}
        self.datasets: Dict[str, DatasetInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Permissions: {_id: PermissionInfo}
        self.permissions: Dict[str, PermissionInfo] = {}

        # Constraints:
        # - Only users with appropriate write/upload permission on a project can upload datasets to it.
        # - Dataset names should be unique within a project.
        # - Each dataset must be associated with at least one project.
        # - File formats must be from a supported list (e.g., CSV, TXT, XLSX, etc.).
        # - Uploaded files must be stored and retrievable via their file_location attribute.

    def get_project_by_name(self, project_name: str) -> dict:
        """
        Retrieve information for a project using its name.

        Args:
            project_name (str): The name of the project to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo  # if found
            }
            or
            {
                "success": False,
                "error": str  # if no such project
            }

        Constraints:
            - Project name must match exactly.
            - If multiple projects have the same name, returns the first found.
        """
        for project in self.projects.values():
            if project["project_name"] == project_name:
                return {"success": True, "data": project}
        return {"success": False, "error": "Project with given name not found"}

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve project information by project_id.

        Args:
            project_id (str): The unique identifier of the project.

        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo  # Project's information
            }
            or
            {
                "success": False,
                "error": str  # "Project not found" if not in self.projects
            }

        Constraints:
            - The given project_id must exist in the repository.
        """
        project = self.projects.get(project_id)
        if project is None:
            return { "success": False, "error": "Project not found" }
        return { "success": True, "data": project }

    def list_project_datasets(self, project_id: str) -> dict:
        """
        List all datasets associated with a given project.

        Args:
            project_id (str): The unique ID of the project to list datasets for.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": List[DatasetInfo]
                  }
                - If project does not exist: {
                      "success": False,
                      "error": "Project not found"
                  }

        Constraints:
            - The project with given ID must exist in the repository.
            - Only lists datasets where the project_id is present in their associated_project_id.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        datasets = [
            dataset_info for dataset_info in self.datasets.values()
            if project_id in dataset_info["associated_project_id"]
        ]
        return {"success": True, "data": datasets}

    def get_dataset_by_name_and_project(self, dataset_name: str, project_id: str) -> dict:
        """
        Retrieve a dataset by its name within a specific project, for conflict detection.

        Args:
            dataset_name (str): The name of the dataset (case-sensitive).
            project_id (str): The project in which to search for the dataset.

        Returns:
            dict:
                - If found: {"success": True, "data": DatasetInfo}
                - If not found: {"success": True, "data": None}
                - If error: {"success": False, "error": "reason"}

        Constraints:
            - project_id must exist.
            - Only checks for dataset_name within the project's datasets.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        for dataset in self.datasets.values():
            if dataset["dataset_name"] == dataset_name and project_id in dataset["associated_project_id"]:
                return {"success": True, "data": dataset}

        return {"success": True, "data": None}

    def list_supported_file_formats(self) -> dict:
        """
        Return the list of permissible file formats for dataset uploads.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of supported file format strings
            }

        No input parameters.
        This is a static/system-level info query operation.
        """
        # Define supported formats in accordance with the constraint description.
        supported_formats = ["CSV", "TXT", "XLSX", "JSON", "TSV"]
        return { "success": True, "data": supported_formats }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve detailed information about a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # All attributes of the user
            }
            or
            {
                "success": False,
                "error": str  # 'User not found' if user_id does not exist
            }

        Constraints:
            - The user with the given user_id must exist.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_permissions_for_project(self, user_id: str, project_id: str) -> dict:
        """
        Retrieve a user's permission level for a specific project.

        Args:
            user_id (str): The unique identifier of the user.
            project_id (str): The unique identifier of the project.

        Returns:
            dict:
                success (bool): True if the query was performed successfully, otherwise False.
                data (List[PermissionInfo]): List of permissions for this user and project
                    (may be empty if none found), if success is True.
                error (str): If success is False, description of the error.

        Constraints:
            - Both user and project must exist in the system.
            - Extract all PermissionInfo where project_id and _id (user_id) both match.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist." }

        perms = [
            perm for perm in self.permissions.values()
            if perm["project_id"] == project_id and perm["_id"] == user_id
        ]

        return { "success": True, "data": perms }

    def get_dataset_by_id(self, dataset_id: str) -> dict:
        """
        Retrieve all metadata and info for a dataset by its unique ID.

        Args:
            dataset_id (str): The unique identifier for the dataset.

        Returns:
            dict: {
                "success": True,
                "data": DatasetInfo  # All metadata for the dataset
            }
            or
            {
                "success": False,
                "error": str  # "Dataset not found" if the ID is missing
            }

        Constraints:
            - The dataset_id must be present in the system.
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"success": False, "error": "Dataset not found"}
        return {"success": True, "data": dataset}

    def list_project_members(self, project_id: str, return_profiles: bool = False) -> dict:
        """
        List all user IDs or user profiles who are members of a specific project.

        Args:
            project_id (str): The identifier of the project.
            return_profiles (bool): If True, return full user profiles; otherwise just user IDs.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": List[str or UserInfo],  # List of user IDs or UserInfo dicts
                }
                On error:
                {
                    "success": False,
                    "error": str  # Explanation of the failure.
                }

        Constraints:
            - The project ID must exist.
            - If a member user ID doesn't exist in self.users, that entry is skipped.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project not found" }

        member_ids = self.projects[project_id].get("member_user_id", [])
        if not isinstance(member_ids, list):
            member_ids = []

        if return_profiles:
            data = [self.users[uid] for uid in member_ids if uid in self.users]
        else:
            data = [uid for uid in member_ids if uid in self.users]

        return { "success": True, "data": data }

    def upload_dataset_to_project(
        self,
        uploader_user_id: str,
        dataset_name: str,
        description: str,
        file_format: str,
        project_ids: list,
        file_location: str,
        metadata: dict,
        upload_date: str
    ) -> dict:
        """
        Create and upload a new dataset, associating it with one or more projects, storing file metadata and location.
        Constraints:
          - Uploader must exist and have 'write' or 'admin' permission on all specified projects.
          - Each project must exist.
          - Dataset name must be unique within each associated project.
          - File format must be from supported list.
          - Must associate with at least one project.
          - Uploaded file metadata and location recorded.

        Args:
            uploader_user_id (str): User uploading the dataset (must exist and have permission)
            dataset_name (str): Unique within each associated project.
            description (str): Dataset description.
            file_format (str): File format (must be supported).
            project_ids (list of str): One or more IDs of the projects for association.
            file_location (str): Location of the uploaded file.
            metadata (dict): Misc metadata fields.
            upload_date (str): Upload date string.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        # Supported formats, could be a class/static variable elsewhere
        SUPPORTED_FORMATS = ['CSV', 'TXT', 'XLSX', 'TSV', 'JSON']
    
        # Check user exists
        if uploader_user_id not in self.users:
            return {"success": False, "error": "Uploader user not found."}
    
        # Check project IDs validity and that list is non-empty
        if not project_ids or not isinstance(project_ids, list):
            return {"success": False, "error": "At least one valid project_id must be provided."}
        for pid in project_ids:
            if pid not in self.projects:
                return {"success": False, "error": f"Project '{pid}' not found."}
    
        # Check file format is supported
        if file_format.upper() not in SUPPORTED_FORMATS:
            return {"success": False, "error": f"File format '{file_format}' is not supported."}

        # Check dataset name uniqueness within each project
        for existing in self.datasets.values():
            if existing["dataset_name"] == dataset_name and set(project_ids).intersection(set(existing["associated_project_id"])):
                return {"success": False, "error": f"Dataset name '{dataset_name}' already exists in one of the specified projects."}
    
        # Check uploader permissions for all target projects
        for pid in project_ids:
            permitted = False
            for perm in self.permissions.values():
                if perm["project_id"] == pid and perm["_id"] == uploader_user_id:
                    if perm["access_level"] in ("write", "admin"):
                        permitted = True
                        break
            if not permitted:
                return {"success": False, "error": f"User lacks write/admin permission on project '{pid}'."}
    
        # Everything is valid, create dataset_id (simple autoinc)
        dataset_id = f"ds_{len(self.datasets)+1}"
        new_dataset = DatasetInfo(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            description=description,
            file_format=file_format.upper(),
            upload_date=upload_date,
            uploader_user_id=uploader_user_id,
            associated_project_id=project_ids,
            metadata=metadata,
            file_location=file_location,
        )
        self.datasets[dataset_id] = new_dataset
        return {"success": True, "message": "Dataset uploaded and associated with project(s)." }

    def associate_dataset_with_additional_project(self, dataset_id: str, additional_project_ids: list) -> dict:
        """
        Adds an existing dataset to additional project(s) by updating its associated_project_id list.

        Args:
            dataset_id (str): The dataset to update.
            additional_project_ids (list of str): List of project IDs to associate with the dataset.

        Returns:
            dict: Either {
                "success": True,
                "message": "Dataset associated with specified projects."
            }
            or
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - The dataset must exist.
            - Additional projects must exist.
            - Projects are only added if not already present in the dataset's associated_project_id attribute.
            - No duplicate project IDs.
        """
        # Check that dataset exists
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"success": False, "error": "Dataset does not exist."}
        # Validate additional_project_ids and existence
        valid_project_ids = []
        for proj_id in additional_project_ids:
            if proj_id not in self.projects:
                return {"success": False, "error": f"Project '{proj_id}' does not exist."}
            if proj_id not in dataset["associated_project_id"]:
                valid_project_ids.append(proj_id)
        if not valid_project_ids:
            return {"success": True, "message": "No new associations made; all given projects were already associated."}
        # Update dataset
        dataset["associated_project_id"].extend(valid_project_ids)
        # Optionally, remove duplicates if somehow present (shouldn't be, just in case)
        dataset["associated_project_id"] = list(dict.fromkeys(dataset["associated_project_id"]))
        return {"success": True, "message": "Dataset associated with specified projects."}

    def update_dataset_metadata(
        self,
        dataset_id: str,
        description: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Change the description and/or metadata dictionary of a dataset.

        Args:
            dataset_id (str): Identifier of the dataset to update.
            description (str, optional): New description text. If None, leaves unchanged.
            metadata (dict, optional): New metadata dict to merge into the current one. Keys will overwrite any existing keys.

        Returns:
            dict: {
                "success": True,
                "message": "Dataset metadata updated successfully."
            }
            or
            {
                "success": False,
                "error": reason for failure
            }

        Constraints:
            - Dataset must exist.
            - At least one of description or metadata must be provided.
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"success": False, "error": "Dataset not found."}
        if description is None and metadata is None:
            return {"success": False, "error": "No update fields provided."}
        if description is not None:
            dataset["description"] = description
        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "metadata field must be a dictionary."}
            dataset["metadata"].update(metadata)
        return {"success": True, "message": "Dataset metadata updated successfully."}

    def add_user_permission_to_project(
        self,
        user_id: str,
        project_id: str,
        access_level: str
    ) -> dict:
        """
        Grant a user a specific permission ('read', 'write', 'admin') for a project.

        Args:
            user_id (str): ID of the user to grant permission to.
            project_id (str): Project in which the permission is to be granted.
            access_level (str): The level of access to grant (supported: 'read', 'write', 'admin').

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            On failure:
            dict: {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist.
            - project_id must exist.
            - access_level must be one of ('read', 'write', 'admin').
            - Do not add duplicate permissions for the same user-project pair.
        """
        SUPPORTED_LEVELS = {"read", "write", "admin"}

        if user_id not in self.users:
            return { "success": False, "error": f"User '{user_id}' does not exist." }
        if project_id not in self.projects:
            return { "success": False, "error": f"Project '{project_id}' does not exist." }
        if access_level not in SUPPORTED_LEVELS:
            return { "success": False, "error": f"Invalid access_level '{access_level}'. Supported: read, write, admin." }

        # Check for existing permission (user-project pair)
        for perm in self.permissions.values():
            if perm["_id"] == user_id and perm["project_id"] == project_id:
                return { "success": False, "error": f"User '{user_id}' already has permission for project '{project_id}'." }

        # Add the permission
        new_perm: PermissionInfo = {
            "_id": user_id,
            "project_id": project_id,
            "access_level": access_level
        }
        perm_key = f"{user_id}:{project_id}"
        self.permissions[perm_key] = new_perm

        return {
            "success": True,
            "message": f"Permission '{access_level}' granted to user '{user_id}' on project '{project_id}'."
        }

    def remove_dataset_from_project(self, dataset_id: str, project_id: str) -> dict:
        """
        Disassociate a dataset from a project. Cannot result in the dataset having zero project associations.

        Args:
            dataset_id (str): The ID of the dataset to modify.
            project_id (str): The ID of the project to remove association.

        Returns:
            dict: 
                {"success": True, "message": "Dataset disassociated from project."}
                or
                {"success": False, "error": "<reason>"}

        Constraints:
            - The dataset must continue to be associated with at least one project after removal.
            - Both dataset and project must exist.
            - The dataset must currently be associated with the project.
        """
        if dataset_id not in self.datasets:
            return {"success": False, "error": "Dataset does not exist."}
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}

        dataset_info = self.datasets[dataset_id]
        if project_id not in dataset_info["associated_project_id"]:
            return {"success": False, "error": "Dataset is not associated with this project."}

        if len(dataset_info["associated_project_id"]) == 1:
            return {"success": False, "error": "Cannot remove last project association from dataset."}

        # Remove the project_id from associated_project_id list
        dataset_info["associated_project_id"].remove(project_id)
        return {"success": True, "message": "Dataset disassociated from project."}

    def remove_dataset(self, dataset_id: str, request_user_id: str) -> dict:
        """
        Delete a dataset from the repository if the requesting user is the uploader with suitable permission, 
        or has admin rights (admin role or project admin), as required.

        Args:
            dataset_id (str): The ID of the dataset to remove.
            request_user_id (str): The ID of the user making the deletion request.

        Returns:
            dict: 
                {"success": True, "message": "..."} on successful removal
                {"success": False, "error": "..."} on failure (not found or permissions issue)

        Constraints:
            - Dataset must exist.
            - User must exist.
            - User must be uploader with sufficient access OR
              have "admin" role OR
              have "admin" permission for at least one associated project.
            - Dataset is deleted from the repository.
        """
        # Validate dataset existence
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"success": False, "error": f"Dataset {dataset_id} does not exist."}

        # Validate user existence
        user = self.users.get(request_user_id)
        if not user:
            return {"success": False, "error": f"User {request_user_id} does not exist."}

        # System admin role: always allowed
        if user.get("role", "").lower() == "admin":
            del self.datasets[dataset_id]
            return {"success": True, "message": f"Dataset {dataset_id} removed successfully."}

        # Check if user is the uploader
        is_uploader = dataset.get("uploader_user_id") == request_user_id

        # Gather relevant project permissions for user
        permitted = False
        for pid in dataset.get("associated_project_id", []):
            # Find permission entries for this user and project
            for perm in self.permissions.values():
                if (
                    perm["project_id"] == pid
                    and perm["_id"] == request_user_id   # permission "_id" is user ID per PermissionInfo
                ):
                    if perm["access_level"].lower() == "admin":
                        permitted = True
                        break
            if permitted:
                break

        # Additional: uploader with at least "write" permission is sufficient (not just "admin")
        if not permitted and is_uploader:
            for pid in dataset.get("associated_project_id", []):
                for perm in self.permissions.values():
                    if (
                        perm["project_id"] == pid
                        and perm["_id"] == request_user_id
                    ):
                        if perm["access_level"].lower() in ("write", "admin"):
                            permitted = True
                            break
                if permitted:
                    break

        if permitted or is_uploader and permitted:
            del self.datasets[dataset_id]
            return {"success": True, "message": f"Dataset {dataset_id} removed successfully."}
        else:
            return {"success": False, "error": "Permission denied: only an admin or uploader with suitable project permission may delete this dataset."}


class ScientificDataRepositorySystem(BaseEnv):
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

    def get_project_by_name(self, **kwargs):
        return self._call_inner_tool('get_project_by_name', kwargs)

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def list_project_datasets(self, **kwargs):
        return self._call_inner_tool('list_project_datasets', kwargs)

    def get_dataset_by_name_and_project(self, **kwargs):
        return self._call_inner_tool('get_dataset_by_name_and_project', kwargs)

    def list_supported_file_formats(self, **kwargs):
        return self._call_inner_tool('list_supported_file_formats', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_permissions_for_project(self, **kwargs):
        return self._call_inner_tool('get_user_permissions_for_project', kwargs)

    def get_dataset_by_id(self, **kwargs):
        return self._call_inner_tool('get_dataset_by_id', kwargs)

    def list_project_members(self, **kwargs):
        return self._call_inner_tool('list_project_members', kwargs)

    def upload_dataset_to_project(self, **kwargs):
        return self._call_inner_tool('upload_dataset_to_project', kwargs)

    def associate_dataset_with_additional_project(self, **kwargs):
        return self._call_inner_tool('associate_dataset_with_additional_project', kwargs)

    def update_dataset_metadata(self, **kwargs):
        return self._call_inner_tool('update_dataset_metadata', kwargs)

    def add_user_permission_to_project(self, **kwargs):
        return self._call_inner_tool('add_user_permission_to_project', kwargs)

    def remove_dataset_from_project(self, **kwargs):
        return self._call_inner_tool('remove_dataset_from_project', kwargs)

    def remove_dataset(self, **kwargs):
        return self._call_inner_tool('remove_dataset', kwargs)

