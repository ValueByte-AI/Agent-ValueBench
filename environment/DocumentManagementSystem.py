# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict
import time
import uuid
from typing import Dict, Any, Optional



class DocumentInfo(TypedDict):
    document_id: str
    filename: str
    format: str
    size: int
    upload_date: str
    owner_id: str
    current_version_id: str
    metadata: Dict[str, Any]

class DocumentVersionInfo(TypedDict):
    version_id: str
    document_id: str
    version_number: int
    format: str
    created_at: str
    file_location: str
    created_by: str
    metadata: Dict[str, Any]

class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    permission: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # DocumentVersions: {version_id: DocumentVersionInfo}
        self.document_versions: Dict[str, DocumentVersionInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Only users with appropriate permissions can upload, download, or convert files.
        # - Each document may have multiple versions distinguished by version number.
        # - Format conversion creates new document version (does NOT overwrite original).
        # - Document filenames must be unique per user or within a defined scope.

    def _sync_document_fields_from_version(self, document_id: str, version_id: str) -> None:
        document = self.documents.get(document_id)
        version = self.document_versions.get(version_id)
        if not document or not version:
            return
        document["current_version_id"] = version_id
        document["format"] = version.get("format", document.get("format"))

    def get_user_info(self, _id: str = None, name: str = None) -> dict:
        """
        Retrieve detailed information and permission level for a user by their unique id or by name.
    
        Args:
            _id (str, optional): The user's unique identifier.
            name (str, optional): The user's name (may return multiple users if names are not unique).
    
        Returns:
            dict:
                success: True, data: UserInfo or list of UserInfo (for name search, could be empty list)
                success: False, error: reason string

        Constraints:
            - If both _id and name are None, returns an error.
            - If both are provided, user id (_id) is prioritized for search.
            - If user with that _id or name is not found, error message.
            - Name searches may return multiple users.
        """
        if _id is None and name is None:
            return {"success": False, "error": "No user identifier provided. Please specify _id or name."}

        if _id is not None:
            user = self.users.get(_id)
            if user is None:
                return {"success": False, "error": f"No user found for id '{_id}'."}
            return {"success": True, "data": user}

        # Otherwise, name search
        result = [u for u in self.users.values() if u["name"] == name]
        if not result:
            return {"success": False, "error": f"No user found with name '{name}'."}
        # If only one user with that name, return singular, else list
        if len(result) == 1:
            return {"success": True, "data": result[0]}
        else:
            # Multiple users with same name
            return {"success": True, "data": result}

    def check_user_permission(self, user_id: str, operation: str) -> dict:
        """
        Check if the specified user has permission to perform the given operation.

        Args:
            user_id (str): The unique user identifier.
            operation (str): The operation to check ('upload', 'download', 'convert').

        Returns:
            dict:
                - If the user exists and the operation is recognized:
                    {
                        "success": True,
                        "has_permission": bool,
                        "permission": str  # user's permission level
                    }
                - If the user does not exist or operation is invalid:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Operations must be in {'upload', 'download', 'convert'}.
            - Only users with sufficient permissions may do action.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        valid_operations = {"upload", "download", "convert"}
        if operation not in valid_operations:
            return {"success": False, "error": f"Invalid operation '{operation}'."}

        user_permission = self.users[user_id].get("permission", None)
        if user_permission is None:
            return {"success": False, "error": "Permission for user is undefined."}

        # Permission mapping (example; can be changed as needed)
        permission_map = {
            "admin": {"upload", "download", "convert"},
            "editor": {"upload"},
            "viewer": {"download"},
            "upload": {"upload"},
            "download": {"download"},
            "convert": {"convert"},
        }
        allowed_ops = permission_map.get(user_permission, set())

        has_perm = operation in allowed_ops

        return {
            "success": True,
            "has_permission": has_perm,
            "permission": user_permission,
        }

    def list_user_documents(self, user_id: str) -> dict:
        """
        List all documents owned by the specified user.

        Args:
            user_id (str): The identifier for the user.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[DocumentInfo]  # List of document info (can be empty if user owns none)
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., user not found)
                }

        Constraints:
            - Returns all documents where DocumentInfo["owner_id"] == user_id
            - Fails if user does not exist in the system
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        documents = [
            doc for doc in self.documents.values()
            if doc["owner_id"] == user_id
        ]
        return { "success": True, "data": documents }

    def find_document_by_filename(self, filename: str, owner_id: str = None) -> dict:
        """
        Retrieve a document's metadata using the filename, possibly filtered by owner.

        Args:
            filename (str): The target filename to search for.
            owner_id (str, optional): If provided, restrict search to documents owned by this user.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo]  # List of matching documents (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If owner_id is supplied, it must exist in self.users.
            - Document filenames are unique per user or scope; search accordingly.
        """
        if not isinstance(filename, str) or filename == "":
            return {"success": False, "error": "A valid filename must be provided"}

        if owner_id is not None:
            if owner_id not in self.users:
                return {"success": False, "error": "Owner (user) not found"}

            matches = [
                doc for doc in self.documents.values()
                if doc["filename"] == filename and doc["owner_id"] == owner_id
            ]
        else:
            matches = [
                doc for doc in self.documents.values()
                if doc["filename"] == filename
            ]

        return {"success": True, "data": matches}

    def filter_documents_by_format(self, format: str, user_id: str = None) -> dict:
        """
        List documents filtered by file format. Optionally filter only documents belonging to a specific user.

        Args:
            format (str): The desired file format to filter documents by (e.g., "PDF").
            user_id (str, optional): If provided, only list documents for this user; otherwise, list for all users.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo]  # May be empty if no matches
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. user not found
            }

        Constraints:
            - If user_id is provided, fails if user does not exist.
            - Case-insensitive match for format for usability.
        """
        if not format or not isinstance(format, str):
            return { "success": True, "data": [] }  # Graceful: no format means no results

        match_format = format.strip().lower()

        filtered_docs = []
        if user_id:
            if user_id not in self.users:
                return { "success": False, "error": "User not found" }
            filtered_docs = [
                doc for doc in self.documents.values()
                if doc["owner_id"] == user_id and doc["format"].lower() == match_format
            ]
        else:
            filtered_docs = [
                doc for doc in self.documents.values()
                if doc["format"].lower() == match_format
            ]

        return { "success": True, "data": filtered_docs }

    def get_document_versions(self, document_id: str) -> dict:
        """
        Retrieve all versions associated with the given document.

        Args:
            document_id (str): The ID of the document to retrieve versions for.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentVersionInfo],  # List of matching versions (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # If the document_id is invalid or document doesn't exist
            }

        Constraints:
            - The document with the given document_id must exist in the system.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        versions = [
            version_info for version_info in self.document_versions.values()
            if version_info["document_id"] == document_id
        ]

        return {"success": True, "data": versions}

    def get_current_document_version(self, document_id: str) -> dict:
        """
        Get metadata for the current (latest) version of a document.

        Args:
            document_id (str): The unique identifier of the document.

        Returns:
            dict: {
                "success": True,
                "data": DocumentVersionInfo (info on current/latest version)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. document or version not found)
            }

        Constraints:
            - document_id must exist in the system.
            - The document must have a current_version_id referencing an existing version.
        """
        doc = self.documents.get(document_id)
        if not doc:
            return { "success": False, "error": "Document does not exist" }

        version_id = doc.get("current_version_id")
        if not version_id:
            return { "success": False, "error": "Current version not set for this document" }

        version_info = self.document_versions.get(version_id)
        if not version_info:
            return { "success": False, "error": "Current version information not found" }

        return { "success": True, "data": version_info }

    def check_filename_uniqueness(self, filename: str, owner_id: str) -> dict:
        """
        Verify that the given filename is unique for the user (owner_id).

        Args:
            filename (str): The filename to check for uniqueness.
            owner_id (str): The user for which the filename uniqueness is checked.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if unique, False if filename exists for this user
            }
            OR
            {
                "success": False,
                "error": str  # error description
            }

        Constraints:
            - The given user must exist.
            - Filenames are unique per user.
        """
        if not isinstance(filename, str) or filename.strip() == "":
            return {"success": False, "error": "Filename must be a non-empty string."}
        if owner_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        for doc in self.documents.values():
            if doc["owner_id"] == owner_id and doc["filename"] == filename:
                return {"success": True, "data": False}
        return {"success": True, "data": True}

    def convert_document_format(self, document_id: str, target_format: str, user_id: str) -> dict:
        """
        Convert a document’s format, creating a new DocumentVersion.
        Only users with correct permissions ("convert" or "admin") can perform this operation.

        Args:
            document_id (str): ID of the document to convert.
            target_format (str): Format to convert to (e.g., 'docx').
            user_id (str): User performing the action.

        Returns:
            dict: {
                "success": True,
                "message": "Document converted and new version created",
                "new_version_id": <version_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        Constraints:
            - Only users with 'convert' or 'admin' permission can perform conversion.
            - The document must exist.
            - A new DocumentVersion is added, and the Document's current_version_id is updated.
        """

        # User validation
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        if user.get("permission") not in ["convert", "admin"]:
            return {"success": False, "error": "User does not have permission to convert documents"}

        # Document validation
        doc = self.documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Document does not exist"}

        # Get current/latest version number
        current_version_id = doc.get("current_version_id")
        if current_version_id not in self.document_versions:
            return {"success": False, "error": "Current version information missing or corrupted"}

        # Find all versions of this document to determine latest version number
        versions = [
            v for v in self.document_versions.values()
            if v["document_id"] == document_id
        ]
        if not versions:
            return {"success": False, "error": "No existing document versions found"}

        max_version_num = max(v["version_number"] for v in versions)
        new_version_num = max_version_num + 1

        # Generate new DocumentVersion
        new_version_id = str(uuid.uuid4())
        new_file_location = f"/files/{document_id}_v{new_version_num}.{target_format.lower()}"

        # Use simulated "now" as ISO 8601 string
        created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        new_version: DocumentVersionInfo = {
            "version_id": new_version_id,
            "document_id": document_id,
            "version_number": new_version_num,
            "format": target_format,
            "created_at": created_at,
            "file_location": new_file_location,
            "created_by": user_id,
            "metadata": copy.deepcopy(doc.get("metadata", {})),
        }
        self.document_versions[new_version_id] = new_version

        # Update document's current_version_id and format
        self._sync_document_fields_from_version(document_id, new_version_id)

        return {
            "success": True,
            "message": f"Document converted to {target_format} and new version created",
            "new_version_id": new_version_id
        }


    def upload_document(
        self,
        user_id: str,
        filename: str,
        format: str,
        size: int,
        upload_date: str,
        file_location: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Upload a new document to the system.

        Args:
            user_id (str): Uploader's user ID.
            filename (str): File name to upload (must be unique for this user).
            format (str): Document file format (e.g., 'pdf', 'docx').
            size (int): Size of the document in bytes.
            upload_date (str): Timestamp of upload.
            file_location (str): Physical location of uploaded file (storage path).
            metadata (dict, optional): Additional document metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Document uploaded successfully.",
                "document_id": <str>,
                "version_id": <str>
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Only users with appropriate 'upload' permission can upload documents.
            - Filename must be unique for the user.
            - Creates the initial version record with version_number=1.
        """
        # 1. User existence and permission check
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        permission_result = self.check_user_permission(user_id=user_id, operation="upload")
        if not permission_result.get("success") or not permission_result.get("has_permission"):
            return {"success": False, "error": "User lacks permission to upload documents."}

        # 2. Filename uniqueness for this user
        for doc in self.documents.values():
            if doc["owner_id"] == user_id and doc["filename"] == filename:
                return {"success": False, "error": "Filename already exists for this user."}

        # 3. Generate IDs
        document_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())

        # 4. Set up document info
        document_info = {
            "document_id": document_id,
            "filename": filename,
            "format": format,
            "size": size,
            "upload_date": upload_date,
            "owner_id": user_id,
            "current_version_id": version_id,
            "metadata": metadata or {}
        }

        # 5. Set up initial document version info
        version_info = {
            "version_id": version_id,
            "document_id": document_id,
            "version_number": 1,
            "format": format,
            "created_at": upload_date,
            "file_location": file_location,
            "created_by": user_id,
            "metadata": copy.deepcopy(metadata or {}),
        }

        # 6. Store
        self.documents[document_id] = document_info
        self.document_versions[version_id] = version_info

        return {
            "success": True,
            "message": "Document uploaded successfully.",
            "document_id": document_id,
            "version_id": version_id
        }

    def upload_new_document_version(
        self,
        document_id: str,
        file_location: str,
        format: str,
        created_by: str,
        created_at: str,
        size: int,
        metadata: dict = None
    ) -> dict:
        """
        Add a new version for an existing document.

        Args:
            document_id: The ID of the document to add a version for.
            file_location: Location/path for the uploaded file.
            format: File format (e.g., "PDF").
            created_by: User ID uploading the version.
            created_at: Upload timestamp (ISO string).
            size: Integer file size in bytes.
            metadata: Optional dictionary of version/file metadata.

        Returns:
            dict: {
                "success": True,
                "message": "New version uploaded successfully",
                "version_id": <new_version_id>
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The document must exist.
            - The user must exist and have permission ("upload" or "edit" in their 'permission' field).
            - Version numbers are per-document, incremented.
            - The new version gets a new unique version_id.
        """
        # Check document exists
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        # Check user exists
        user = self.users.get(created_by)
        if not user:
            return {"success": False, "error": "User does not exist"}

        # Permission check: allow roles like 'admin', 'editor', 'upload', or similar
        if user["permission"] not in ["admin", "editor", "upload"]:
            return {"success": False, "error": "User does not have permission to upload document versions"}

        # Get latest version number
        versions = [v for v in self.document_versions.values() if v["document_id"] == document_id]
        if versions:
            latest_version_number = max(v["version_number"] for v in versions)
        else:
            latest_version_number = 0  # If somehow no versions exist (shouldn't happen for existing documents)

        new_version_number = latest_version_number + 1

        # Generate unique version_id (simple: docid_verN or use uuid)
        new_version_id = str(uuid.uuid4())

        # Compose DocumentVersionInfo
        new_version_info = {
            "version_id": new_version_id,
            "document_id": document_id,
            "version_number": new_version_number,
            "format": format,
            "created_at": created_at,
            "file_location": file_location,
            "created_by": created_by,
            "metadata": copy.deepcopy(metadata or {}),
        }
        self.document_versions[new_version_id] = new_version_info

        # Update document's current version, size, format, upload_date, possibly metadata
        doc = self.documents[document_id]
        doc["current_version_id"] = new_version_id
        doc["size"] = size
        doc["format"] = format
        doc["upload_date"] = created_at
        if metadata is not None:
            doc["metadata"].update(metadata)

        return {
            "success": True,
            "message": "New version uploaded successfully",
            "version_id": new_version_id
        }

    def download_document_version(self, user_id: str, version_id: str) -> dict:
        """
        Download a specific version of a document.

        Args:
            user_id (str): The user requesting to download the document version.
            version_id (str): The specific document version's ID.

        Returns:
            dict: {
                "success": True,
                "message": "File ready for download.",
                "file_location": str,     # Path/location of the file
                "filename": str           # The filename of the document
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Version must exist.
            - User must have permission ('download', 'admin'), or be the owner of the document.
        """
        # Check that user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist."}

        # Check that the version exists
        version = self.document_versions.get(version_id)
        if version is None:
            return {"success": False, "error": "Document version does not exist."}

        # Check that the document exists and belongs to some owner
        document = self.documents.get(version["document_id"])
        if document is None:
            return {"success": False, "error": "Associated document does not exist."}

        # Permission check (allow if user is owner or has download/admin permission)
        allowed_permissions = {"admin", "download"}
        if (
            user["permission"] not in allowed_permissions
            and user["_id"] != document["owner_id"]
        ):
            return {"success": False, "error": "Permission denied."}

        # Success; simulate 'download' by returning file_location and filename
        return {
            "success": True,
            "message": "File ready for download.",
            "file_location": version["file_location"],
            "filename": document["filename"],
        }

    def update_document_metadata(
        self,
        user_id: str,
        document_id: str = None,
        version_id: str = None,
        metadata_updates: dict = None
    ) -> dict:
        """
        Modify metadata (such as tags or notes) for a document or a specific version.

        Args:
            user_id (str): ID of the user requesting the update.
            document_id (str, optional): Document to update. Required if version_id is not given.
            version_id (str, optional): Document version to update. Overrides document_id if given.
            metadata_updates (dict): Dict of updates {key: value} to apply.

        Returns:
            dict: {
                "success": True,
                "message": "Metadata updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The document or version must exist.
            - The user must exist and have permission to update the metadata.
            - Only document owner or users with suitable permission ('admin'/'editor') can edit.
            - If `version_id` is given and DocumentVersion has no metadata field, return error.
        """
        # Validate user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        user = self.users[user_id]
        allowed_perms = {"admin", "editor"}

        # Validate metadata_updates
        if not isinstance(metadata_updates, dict) or not metadata_updates:
            return {"success": False, "error": "Invalid or missing metadata updates."}

        # ---- Update on Version ----
        if version_id:
            if version_id not in self.document_versions:
                return {"success": False, "error": "Document version does not exist."}
            version = self.document_versions[version_id]
            doc_id = version["document_id"]
            # Check document existence for ownership
            if doc_id not in self.documents:
                return {"success": False, "error": "Associated document not found."}
            doc = self.documents[doc_id]

            if not (
                user["_id"] == doc["owner_id"]
                or user["permission"] in allowed_perms
            ):
                return {"success": False, "error": "Permission denied."}

            # Check if version supports metadata (common: may need an extension)
            if not isinstance(version.get("metadata"), dict):
                version["metadata"] = {}
            version["metadata"].update(metadata_updates)
            if not isinstance(doc.get("metadata"), dict):
                doc["metadata"] = {}
            doc["metadata"].update(metadata_updates)
            return {"success": True, "message": "Metadata updated successfully."}

        # ---- Update on Document ----
        if document_id:
            if document_id not in self.documents:
                return {"success": False, "error": "Document does not exist."}
            doc = self.documents[document_id]
            if not (
                user["_id"] == doc["owner_id"]
                or user["permission"] in allowed_perms
            ):
                return {"success": False, "error": "Permission denied."}

            if not isinstance(doc["metadata"], dict):
                doc["metadata"] = {}

            doc["metadata"].update(metadata_updates)
            return {"success": True, "message": "Metadata updated successfully."}

        return {"success": False, "error": "Either document_id or version_id must be provided."}

    def delete_document(self, document_id: str, user_id: str) -> dict:
        """
        Remove a document and all its versions from the system. Only admins or the document's owner
        can perform this operation.

        Args:
            document_id (str): The unique identifier of the document to delete.
            user_id (str): ID of the user performing the deletion.

        Returns:
            dict: On success:
                { "success": True, "message": "Document and all versions deleted successfully." }
            On failure:
                { "success": False, "error": "<reason>" }

        Constraints:
            - Only users with 'admin' permission or the document's owner can delete the document.
            - All versions of the document are deleted.
        """

        # Check if user exists
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found." }

        # Check if document exists
        document = self.documents.get(document_id)
        if document is None:
            return { "success": False, "error": "Document not found." }

        # Permission check: admin or document owner
        if not (user['permission'] == 'admin' or user['_id'] == document['owner_id']):
            return { "success": False, "error": "Permission denied. Only admin or document owner can delete this document." }

        # Delete all document versions
        to_delete = [v_id for v_id, ver in self.document_versions.items() if ver['document_id'] == document_id]
        for v_id in to_delete:
            del self.document_versions[v_id]

        # Delete the document
        del self.documents[document_id]

        return { "success": True, "message": "Document and all versions deleted successfully." }

    def delete_document_version(self, user_id: str, version_id: str) -> dict:
        """
        Remove a specific version of a document. 

        Args:
            user_id (str): User requesting the operation.
            version_id (str): The document version to delete.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Document version deleted."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - User must exist and have permission (permission == 'admin' or 'editor').
            - The version must exist.
            - At least one version must remain for the document (cannot delete last version).
            - If deleting the current version, current_version_id must be set to the latest remaining version.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        if user["permission"] not in ("admin", "editor"):
            return {"success": False, "error": "Permission denied"}

        version_info = self.document_versions.get(version_id)
        if not version_info:
            return {"success": False, "error": "Version not found"}

        document_id = version_info["document_id"]
        # Collect all versions for this document
        versions = [
            v for v in self.document_versions.values()
            if v["document_id"] == document_id
        ]
        if len(versions) <= 1:
            return {"success": False, "error": "Cannot delete the last version of a document"}

        # Remove the version
        del self.document_versions[version_id]

        # If this was the current version, find the one with highest version_number as new current
        doc = self.documents.get(document_id)
        if doc:
            if doc["current_version_id"] == version_id:
                # get versions after deletion
                remaining_versions = [
                    v for v in versions if v["version_id"] != version_id
                ]
                if remaining_versions:
                    # Set to the highest version_number
                    new_current = max(remaining_versions, key=lambda v: v["version_number"])
                    self._sync_document_fields_from_version(document_id, new_current["version_id"])

        return {"success": True, "message": "Document version deleted."}

    def restore_previous_document_version(
        self, user_id: str, document_id: str, version_id: str
    ) -> dict:
        """
        Set a previous DocumentVersion as current for a document.

        Args:
            user_id (str): User performing the operation.
            document_id (str): The target document.
            version_id (str): The version to promote to 'current'.

        Returns:
            dict: 
              Success: { "success": True, "message": str }
              Failure: { "success": False, "error": str }

        Constraints:
            - Only users with 'admin' or 'editor' permissions can restore versions.
            - Document and version must exist.
            - Version must belong to the document.
            - Version must not already be the current one.
        """
        # Check user exists and permissions
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        if user["permission"] not in ("admin", "editor"):
            return {"success": False, "error": "Permission denied"}

        # Check document exists
        document = self.documents.get(document_id)
        if not document:
            return {"success": False, "error": "Document does not exist"}

        # Check version exists
        version = self.document_versions.get(version_id)
        if not version:
            return {"success": False, "error": "Version does not exist"}

        # Check version is associated with document
        if version["document_id"] != document_id:
            return {"success": False, "error": "Version does not belong to the document"}

        # Check if already current
        if document["current_version_id"] == version_id:
            return {"success": False, "error": "Version is already current"}

        # Perform the version restoration
        self._sync_document_fields_from_version(document_id, version_id)

        return {
            "success": True,
            "message": f"Version {version_id} is now current for document {document_id}"
        }


class DocumentManagementSystem(BaseEnv):
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

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def check_user_permission(self, **kwargs):
        return self._call_inner_tool('check_user_permission', kwargs)

    def list_user_documents(self, **kwargs):
        return self._call_inner_tool('list_user_documents', kwargs)

    def find_document_by_filename(self, **kwargs):
        return self._call_inner_tool('find_document_by_filename', kwargs)

    def filter_documents_by_format(self, **kwargs):
        return self._call_inner_tool('filter_documents_by_format', kwargs)

    def get_document_versions(self, **kwargs):
        return self._call_inner_tool('get_document_versions', kwargs)

    def get_current_document_version(self, **kwargs):
        return self._call_inner_tool('get_current_document_version', kwargs)

    def check_filename_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_filename_uniqueness', kwargs)

    def convert_document_format(self, **kwargs):
        return self._call_inner_tool('convert_document_format', kwargs)

    def upload_document(self, **kwargs):
        return self._call_inner_tool('upload_document', kwargs)

    def upload_new_document_version(self, **kwargs):
        return self._call_inner_tool('upload_new_document_version', kwargs)

    def download_document_version(self, **kwargs):
        return self._call_inner_tool('download_document_version', kwargs)

    def update_document_metadata(self, **kwargs):
        return self._call_inner_tool('update_document_metadata', kwargs)

    def delete_document(self, **kwargs):
        return self._call_inner_tool('delete_document', kwargs)

    def delete_document_version(self, **kwargs):
        return self._call_inner_tool('delete_document_version', kwargs)

    def restore_previous_document_version(self, **kwargs):
        return self._call_inner_tool('restore_previous_document_version', kwargs)
