# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import re
import uuid



# Represents a collaborative project workspace containing related documents and a list of authorized users.
class ProjectInfo(TypedDict):
    project_id: str
    project_name: str
    project_description: str
    creation_date: str
    project_mem: List[str]  # List of authorized user IDs

# Holds information about a document/file uploaded to a project.
class DocumentInfo(TypedDict):
    document_id: str
    project_id: str
    file_name: str
    file_type: str
    upload_time: str
    uploader_user_id: str
    version_number: int
    file_conten: str  # File contents (string representation)

# Represents users in the system.
class UserInfo(TypedDict):
    user_id: str
    user_name: str
    user_role: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Project Document Management System stateful environment.
        """

        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints and rules:
        # - Documents must be associated with a valid project.
        # - Only authorized project members may upload documents to a project.
        # - File names should be unique within each project/version combination, or managed via versioning.
        # - Uploaded documents must have valid metadata (file name, type, etc.) and recorded upload time.
        # - Versioning should increment the document's version when the same file is uploaded multiple times.

    def get_project_by_name(self, project_name: str) -> dict:
        """
        Retrieve the complete information (including membership) for a project by its name.

        Args:
            project_name (str): The name of the project to query.

        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo
            }
            or
            {
                "success": False,
                "error": "Project not found"
            }

        Constraints:
            - Project names are assumed unique.
            - Returns first match if duplicates exist.
        """
        name = project_name.strip()
        for project in self.projects.values():
            if project["project_name"] == name:
                return { "success": True, "data": project }
        return { "success": False, "error": "Project not found" }

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve the project information using its unique project_id.

        Args:
            project_id (str): The unique identifier of the target project.

        Returns:
            dict: {
                "success": True,
                "data": ProjectInfo,  # Project metadata
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Project not found"
            }

        Constraints:
            - The project_id must exist in the system.
        """
        project = self.projects.get(project_id)
        if project is None:
            return { "success": False, "error": "Project not found" }
        else:
            return { "success": True, "data": project }

    def list_projects_for_user(self, user_id: str) -> dict:
        """
        List all projects that a specific user (by user_id) is a member of.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User ID does not exist" }

        user_projects = [
            project for project in self.projects.values()
            if user_id in project.get("project_mem", [])
        ]

        return { "success": True, "data": user_projects }

    def get_user_by_name(self, user_name: str) -> dict:
        """
        Retrieve user information (including roles) by user_name.

        Args:
            user_name (str): The username to look up.

        Returns:
            dict: If user exists:
                    {
                        "success": True,
                        "data": UserInfo
                    }
                  If user does not exist:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - Search is case-sensitive.
            - Assumes user_name is unique (returns the first match).
        """
        for user in self.users.values():
            if user["user_name"] == user_name:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo  # User information dictionary
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - None beyond existence of the user.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def is_user_project_member(self, user_id: str, project_id: str) -> dict:
        """
        Check whether the specified user_id is a member of the specified project_id.

        Args:
            user_id (str): The ID of the user.
            project_id (str): The ID of the project.

        Returns:
            dict: {
                "success": True,
                "is_member": bool   # True if user is member, False otherwise
            }
            or
            {
                "success": False,
                "error": str        # Reason for failure (e.g., project or user not found)
            }

        Constraints:
            - The project must exist in the system.
            - (Optional) If the user is not registered, return an error.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project not found" }
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        is_member = user_id in self.projects[project_id]["project_mem"]
        return { "success": True, "is_member": is_member }

    def list_documents_by_project(self, project_id: str) -> dict:
        """
        Retrieve all document metadata associated with the specified project_id.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict:
                - { "success": True, "data": List[DocumentInfo] }
                    On success; the list may be empty if no documents exist for the project.
                - { "success": False, "error": "Project does not exist" }
                    If the project_id is invalid.

        Constraints:
            - The provided project_id must exist in the system.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        docs = [
            doc_info
            for doc_info in self.documents.values()
            if doc_info["project_id"] == project_id
        ]

        return { "success": True, "data": docs }

    def get_document_by_filename(self, project_id: str, file_name: str) -> dict:
        """
        Retrieve all documents in a project by file_name (across all available versions).

        Args:
            project_id (str): The ID of the project to search within.
            file_name (str): The file name to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo]  # List of matching documents (may be multiple versions, or empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., project does not exist
            }

        Constraints:
            - Project must exist.
            - Returns all document versions matching the file_name within the specified project.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        results = [
            doc for doc in self.documents.values()
            if doc["project_id"] == project_id and doc["file_name"] == file_name
        ]

        return {"success": True, "data": results}

    def get_latest_document_version(self, project_id: str, file_name: str) -> dict:
        """
        Retrieve the most recent (highest version) document for the given project_id and file_name.

        Args:
            project_id (str): The ID of the project.
            file_name (str): The file name to look for (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": DocumentInfo     # The document with the highest version_number
            }
            or
            {
                "success": False,
                "error": str             # Description of error (project not found, document not found, etc.)
            }

        Constraints:
            - The project_id must exist.
            - The file_name must match an existing document in the project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        candidates = [
            doc for doc in self.documents.values()
            if doc["project_id"] == project_id and doc["file_name"] == file_name
        ]
        if not candidates:
            return { "success": False, "error": "No such document in project" }

        latest_document = max(candidates, key=lambda d: d["version_number"])

        return { "success": True, "data": latest_document }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve the full metadata and content for a specified document_id.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": DocumentInfo  # Full document metadata and contents
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - The given document_id must exist in the system.
        """
        document = self.documents.get(document_id)
        if document is None:
            return {
                "success": False,
                "error": "Document not found"
            }
        return {
            "success": True,
            "data": document
        }

    def upload_document(
        self,
        project_id: str,
        file_name: str,
        file_type: str,
        uploader_user_id: str,
        file_conten: str,
        upload_time: str
    ) -> dict:
        """
        Upload a new document or a new version of an existing document to a project.

        Args:
            project_id (str): The project to upload into.
            file_name (str): The name of the file to be uploaded.
            file_type (str): The file's type (e.g., pdf, docx).
            uploader_user_id (str): The user id performing the upload.
            file_conten (str): The file contents (stringified file).
            upload_time (str): The time of upload (ISO string or timestamp as string).

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "<description>",
                    "document_id": <document_id>
                }
                On failure: { "success": False, "error": <error message> }

        Constraints:
            - Project must exist.
            - Uploader must be a member of the project.
            - All required metadata must be present.
            - If file with same name exists in this project, increment version_number.
            - Else, new document version_number = 1.
        """
        # Validate input presence
        if not (project_id and file_name and file_type and uploader_user_id and file_conten and upload_time):
            return {"success": False, "error": "Missing required metadata or file content."}
        # Project existence
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}
        # Uploader existence and membership
        if uploader_user_id not in self.users:
            return {"success": False, "error": "Uploader user does not exist."}
        project_info = self.projects[project_id]
        if uploader_user_id not in project_info["project_mem"]:
            return {"success": False, "error": "Uploader is not a member of the specified project."}
        # Versioning: find all docs with same (project_id, file_name)
        existing_versions = [
            doc for doc in self.documents.values()
            if doc["project_id"] == project_id and doc["file_name"] == file_name
        ]
        if existing_versions:
            # Increment version
            latest_version = max(doc["version_number"] for doc in existing_versions)
            version_number = latest_version + 1
            action_str = "Uploaded new version of existing document."
        else:
            version_number = 1
            action_str = "Uploaded new document."
        # Generate unique document_id: "<project_id>_<file_name>_<version_number>_<upload_time>"
        base_doc_id = f"{project_id}_{file_name}_{version_number}_{upload_time}"
        # Optional: avoid whitespace and special characters in file_name/document_id if desired
        document_id = re.sub(r'[^A-Za-z0-9_.-]', '_', base_doc_id)
        # Compose DocumentInfo
        new_doc = {
            "document_id": document_id,
            "project_id": project_id,
            "file_name": file_name,
            "file_type": file_type,
            "upload_time": upload_time,
            "uploader_user_id": uploader_user_id,
            "version_number": version_number,
            "file_conten": file_conten
        }
        # Add to documents
        self.documents[document_id] = new_doc
        return {
            "success": True,
            "message": f"{action_str} (version {version_number}).",
            "document_id": document_id
        }

    def create_project(self, project_name: str, project_description: str, project_mem: list, creation_date: str) -> dict:
        """
        Create a new project with the given name, description, creation date, and member user IDs.

        Args:
            project_name (str): Name of the new project (must be unique).
            project_description (str): Description of the project.
            project_mem (List[str]): List of user_ids to include as project members.
            creation_date (str): Creation date of the project (ISO8601 or similar string).

        Returns:
            dict: {
                "success": True,
                "message": "Project created successfully",
                "project_id": <newly_generated_project_id>
            }
            or
            {
                "success": False,
                "error": <failure reason>
            }

        Constraints:
            - Project name must be unique.
            - All members must be registered users.
            - Member list must not be empty.
        """
        # Check uniqueness of project name
        for project in self.projects.values():
            if project["project_name"] == project_name:
                return { "success": False, "error": "Project name already exists" }

        # Validate project member user IDs
        if not isinstance(project_mem, list) or len(project_mem) == 0:
            return { "success": False, "error": "Project member list must not be empty" }

        invalid_users = [uid for uid in project_mem if uid not in self.users]
        if invalid_users:
            return { "success": False, "error": f"Invalid user_ids in member list: {invalid_users}" }

        # Generate a unique project_id
        project_id = str(uuid.uuid4())

        # Create and store the new project
        new_project = {
            "project_id": project_id,
            "project_name": project_name,
            "project_description": project_description,
            "creation_date": creation_date,
            "project_mem": project_mem.copy()  # store a copy
        }
        self.projects[project_id] = new_project

        return {
            "success": True,
            "message": "Project created successfully",
            "project_id": project_id
        }

    def add_user_to_project(self, project_id: str, user_id: str) -> dict:
        """
        Add a user as a member to an existing project.

        Args:
            project_id (str): The ID of the target project.
            user_id (str): The ID of the user to add.

        Returns:
            dict:
                - {"success": True, "message": "User <user_id> added to project <project_id>"}
                - {"success": False, "error": "<error reason>"}
    
        Constraints:
            - The project must exist.
            - The user must exist.
            - The user must not already be a project member.
        """
        # Check project exists
        if project_id not in self.projects:
            return {"success": False, "error": f"Project {project_id} does not exist"}

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": f"User {user_id} does not exist"}

        # Check if user already in project
        project = self.projects[project_id]
        if user_id in project["project_mem"]:
            return {"success": False, "error": f"User {user_id} is already a member of project {project_id}"}

        # Add user to project member list
        project["project_mem"].append(user_id)
        return {"success": True, "message": f"User {user_id} added to project {project_id}"}

    def remove_user_from_project(self, project_id: str, user_id: str) -> dict:
        """
        Remove a user's membership from a project.

        Args:
            project_id (str): The ID of the project.
            user_id (str): The ID of the user to remove.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> removed from project <project_id>"
            }
            or {
                "success": False,
                "error": error message
            }

        Constraints:
            - Project must exist.
            - User must exist.
            - User must be a current member of the project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": f"Project '{project_id}' does not exist." }
        if user_id not in self.users:
            return { "success": False, "error": f"User '{user_id}' does not exist." }

        project = self.projects[project_id]
        if user_id not in project["project_mem"]:
            return { "success": False, "error": f"User '{user_id}' is not a member of project '{project_id}'." }

        project["project_mem"].remove(user_id)
        # The project object in self.projects is updated, no need to reassign.

        return {
            "success": True,
            "message": f"User '{user_id}' removed from project '{project_id}'."
        }

    def register_user(self, user_id: str, user_name: str, user_role: str) -> dict:
        """
        Registers a new user in the system with the specified profile information.

        Args:
            user_id (str): Unique identifier for the user.
            user_name (str): Name of the user.
            user_role (str): Role of the user (e.g., member, admin).

        Returns:
            dict:
                - { "success": True, "message": "User registered successfully" }
                - { "success": False, "error": <reason> }

        Constraints:
            - user_id must be unique (not already registered)
            - user_id, user_name, and user_role must be non-empty
        """
        if not user_id or not user_name or not user_role:
            return { "success": False, "error": "All user profile fields must be provided and non-empty" }

        if user_id in self.users:
            return { "success": False, "error": "User ID already exists" }

        user_info = {
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role
        }

        self.users[user_id] = user_info
        return { "success": True, "message": "User registered successfully" }

    def update_document_metadata(
        self,
        document_id: str,
        updater_user_id: str,
        updates: dict
    ) -> dict:
        """
        Modify metadata (file_name, file_type, etc.) of an existing document.

        Args:
            document_id (str): The ID of the document to update.
            updater_user_id (str): The user requesting the metadata change.
            updates (dict): {field: new_value} for fields to modify (file_name, file_type, etc.).

        Returns:
            dict:
                - On success: { "success": True, "message": "Document metadata updated successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Document must exist.
            - Only authorized project members or admin users may update document metadata.
            - Changing file_name must not result in duplication within the same project/version.
            - Fields allowed to change: ["file_name", "file_type"].
            - upload_time, version_number, project_id, document_id, uploader_user_id, file_conten are not updatable.
        """
        # 1. Check document exists
        if document_id not in self.documents:
            return { "success": False, "error": "Document not found" }

        doc = self.documents[document_id]
        project_id = doc["project_id"]

        # 2. Verify updater is a project member or a system admin
        project = self.projects.get(project_id)
        if not project:
            return { "success": False, "error": "Associated project not found" }
        updater = self.users.get(updater_user_id)
        is_admin = isinstance(updater, dict) and updater.get("user_role") == "admin"
        if updater_user_id not in project["project_mem"] and not is_admin:
            return { "success": False, "error": "User not authorized to modify document metadata" }

        # 3. Determine allowed fields
        allowed_fields = ["file_name", "file_type"]
        to_update = {}
        for key, value in updates.items():
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' is not allowed to be updated" }
            to_update[key] = value

        if not to_update:
            return { "success": False, "error": "No valid fields specified for update" }

        # 4. If file_name is being changed, ensure uniqueness within project/version
        if "file_name" in to_update:
            new_name = to_update["file_name"]
            # Check for duplicate name in this project/version (excluding this document)
            for d in self.documents.values():
                if (
                    d["project_id"] == project_id
                    and d["version_number"] == doc["version_number"]
                    and d["file_name"] == new_name
                    and d["document_id"] != document_id
                ):
                    return { "success": False, "error": "Another document with the same file name exists in this project and version" }

        # 5. All checks passed, update fields
        for k, v in to_update.items():
            doc[k] = v

        self.documents[document_id] = doc

        return { "success": True, "message": "Document metadata updated successfully" }

    def delete_document(self, document_id: str) -> dict:
        """
        Remove (hard delete) a document from the system.

        Args:
            document_id (str): Unique identifier of the document to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Document deleted (id: <document_id>)"
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Document not found"
            }

        Constraints:
            - Document must exist to be deleted.
            - Hard delete (per schema; no 'archived'/'deleted' flag supported).
        """
        if document_id not in self.documents:
            return {
                "success": False,
                "error": "Document not found"
            }

        del self.documents[document_id]
        return {
            "success": True,
            "message": f"Document deleted (id: {document_id})"
        }


class ProjectDocumentManagementSystem(BaseEnv):
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

    def list_projects_for_user(self, **kwargs):
        return self._call_inner_tool('list_projects_for_user', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def is_user_project_member(self, **kwargs):
        return self._call_inner_tool('is_user_project_member', kwargs)

    def list_documents_by_project(self, **kwargs):
        return self._call_inner_tool('list_documents_by_project', kwargs)

    def get_document_by_filename(self, **kwargs):
        return self._call_inner_tool('get_document_by_filename', kwargs)

    def get_latest_document_version(self, **kwargs):
        return self._call_inner_tool('get_latest_document_version', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def upload_document(self, **kwargs):
        return self._call_inner_tool('upload_document', kwargs)

    def create_project(self, **kwargs):
        return self._call_inner_tool('create_project', kwargs)

    def add_user_to_project(self, **kwargs):
        return self._call_inner_tool('add_user_to_project', kwargs)

    def remove_user_from_project(self, **kwargs):
        return self._call_inner_tool('remove_user_from_project', kwargs)

    def register_user(self, **kwargs):
        return self._call_inner_tool('register_user', kwargs)

    def update_document_metadata(self, **kwargs):
        return self._call_inner_tool('update_document_metadata', kwargs)

    def delete_document(self, **kwargs):
        return self._call_inner_tool('delete_document', kwargs)
