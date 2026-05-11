# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional
import time
import uuid
import datetime
from datetime import datetime



class DocumentInfo(TypedDict):
    document_id: str
    title: str
    document_type: str
    content: str
    version_id: str
    status: str
    created_at: str
    updated_at: str

class DocumentVersionInfo(TypedDict):
    version_id: str
    document_id: str
    version_number: int
    content_snapshot: str
    created_at: str
    author_id: str

class UserInfo(TypedDict):
    user_id: str  # from "_id"
    name: str
    role: str
    department: str

class PermissionInfo(TypedDict):
    permission_id: str
    user_id: str
    document_id: str
    access_level: str  # e.g., 'read', 'write', 'admin'

class ReviewInfo(TypedDict):
    review_id: str   # from "view_id"
    document_id: str
    reviewer_id: str
    status: str
    initiated_at: str
    completed_at: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # Document versions: {version_id: DocumentVersionInfo}
        self.document_versions: Dict[str, DocumentVersionInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Permissions: {permission_id: PermissionInfo}
        self.permissions: Dict[str, PermissionInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        self.reviews: Dict[str, ReviewInfo] = {}

        # --- Constraints (expressed as comments) ---
        # - Users can only access documents if they have explicit permission at the appropriate access level.
        # - Document version history: edits produce new versions, never overwrite previous versions.
        # - Actions taken on confidential/controlled documents must be logged.
        # - Only users with 'reviewer' or 'auditor' in their role can participate in reviews.
        # - Documents may be linked to one or more review/audit records.

    def _is_confidential_or_controlled(self, document_id: str) -> bool:
        doc = self.documents.get(document_id)
        if not doc:
            return False
        doc_type = str(doc.get("document_type", "")).lower()
        status = str(doc.get("status", "")).lower()
        return doc_type in {"confidential", "controlled"} or status in {"confidential", "controlled"}

    def _ensure_document_access_logs(self) -> Dict[str, list]:
        logs = getattr(self, "document_access_logs", {})
        if isinstance(logs, dict):
            normalized = {}
            for document_id, entries in logs.items():
                if isinstance(entries, list):
                    normalized[document_id] = copy.deepcopy(entries)
            self.document_access_logs = normalized
            return normalized
        self.document_access_logs = {}
        return self.document_access_logs

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the full user information by their unique user_id.
    
        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
              On success: { "success": True, "data": UserInfo }
              On failure: { "success": False, "error": "User not found" }
    
        Constraints:
            - No special permission constraints; any user_id may be looked up.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve a user object by matching the user's name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo       # If found
            }
            or
            {
                "success": False,
                "error": str           # Error message, if not found or invalid input
            }

        Constraints:
            - The name must not be empty.
            - Returns the first user with matching name, if multiple users share the same name.
        """
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or empty user name provided." }

        for user in self.users.values():
            if user["name"] == name:
                return { "success": True, "data": user }

        return { "success": False, "error": f"User with name '{name}' not found." }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve detailed information for a document given its document_id.

        Args:
            document_id (str): The unique identifier of the document.

        Returns:
            dict:
                On success:
                    { "success": True, "data": DocumentInfo }
                On failure:
                    { "success": False, "error": "Document not found" }

        Constraints:
            - No permission check is performed in this operation;
              this is for direct metadata retrieval.
        """
        doc = self.documents.get(document_id)
        if doc is None:
            return { "success": False, "error": "Document not found" }
        return { "success": True, "data": doc }

    def get_document_by_title(self, title: str) -> dict:
        """
        Find a document (or documents) and its metadata given its title.

        Args:
            title (str): The title of the document to search for.

        Returns:
            dict:
                - If found:
                    {
                        "success": True,
                        "data": DocumentInfo or List[DocumentInfo]  # If multiple found, returns all.
                    }
                - If not found:
                    {
                        "success": False,
                        "error": "Document not found"
                    }

        Notes:
            - Document titles may not be unique; if multiple documents have the same title,
              all matching documents are returned as a list.
            - No permission enforcement is performed for this system-level query.
        """
        results = [
            doc for doc in self.documents.values()
            if doc["title"] == title
        ]

        if not results:
            return { "success": False, "error": "Document not found" }
        elif len(results) == 1:
            return { "success": True, "data": results[0] }
        else:
            return { "success": True, "data": results }

    def list_documents_by_type(self, document_type: str) -> dict:
        """
        Retrieve all documents of a given type.

        Args:
            document_type (str): The type of documents to list (e.g., 'policy', 'minutes', 'compliance record').

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo],  # List of documents matching the given type.
            }
            or
            {
                "success": False,
                "error": str  # Error message if input is invalid.
            }

        Constraints:
            - document_type must be a non-empty string.
            - No access checks or versioning involved in this operation.
        """
        if not isinstance(document_type, str) or not document_type.strip():
            return {"success": False, "error": "document_type must be a non-empty string"}
    
        matches = [
            doc for doc in self.documents.values()
            if doc.get("document_type") == document_type
        ]
        return {"success": True, "data": matches}

    def list_user_permissions_for_document(self, user_id: str, document_id: str) -> dict:
        """
        Get a list of a user's explicit permission records for a specified document.

        Args:
            user_id (str): The unique identifier of the user.
            document_id (str): The unique identifier of the document.

        Returns:
            dict: {
                "success": True,
                "data": List[PermissionInfo]  # List of all explicit permissions (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., unknown user or document)
            }

        Constraints:
            - Both user_id and document_id must exist in the database.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist" }
    
        perms = [
            perm
            for perm in self.permissions.values()
            if perm["user_id"] == user_id and perm["document_id"] == document_id
        ]

        return { "success": True, "data": perms }

    def check_user_permission_for_document(self, user_id: str, document_id: str, access_level: str) -> dict:
        """
        Verify whether a user has at least the given level of access ('read', 'write', 'admin')
        to a specific document.

        Args:
            user_id (str): ID of the user to check.
            document_id (str): ID of the document in question.
            access_level (str): The required access level ('read', 'write', or 'admin').

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": {
                        "permitted": bool,  # True if user has required (or higher) permission, False otherwise
                        "granted_level": str or None  # The highest granted level, or None if no permission
                    }
                }
                On error,
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., invalid user/document/access_level)
                }

        Constraints:
            - User and document must exist.
            - only considers explicit permissions assigned to the user for the document.
            - Access level hierarchy: admin > write > read.
        """
        valid_levels = ["read", "write", "admin"]
        level_rank = {level: idx for idx, level in enumerate(valid_levels)}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}
        if access_level not in valid_levels:
            return {"success": False, "error": "Invalid access level requested"}

        # Find all permissions for this user+document
        perms = [
            p for p in self.permissions.values()
            if p["user_id"] == user_id and p["document_id"] == document_id
        ]
        if not perms:
            return {
                "success": True,
                "data": {"permitted": False, "granted_level": None}
            }

        # Determine the highest granted level
        highest_level = None
        for p in perms:
            pl = p["access_level"]
            if pl in valid_levels:
                if (highest_level is None) or (level_rank[pl] > level_rank[highest_level]):
                    highest_level = pl

        if highest_level is None:
            # Permissions exist but have invalid levels (shouldn't happen)
            return {
                "success": True,
                "data": {"permitted": False, "granted_level": None}
            }

        if level_rank[highest_level] >= level_rank[access_level]:
            permitted = True
        else:
            permitted = False

        return {
            "success": True,
            "data": {
                "permitted": permitted,
                "granted_level": highest_level
            }
        }

    def get_document_versions(self, document_id: str) -> dict:
        """
        Retrieve all version records for a specified document.

        Args:
            document_id (str): The unique ID of the document.

        Returns:
            dict:
                - success (bool): Indicates if the operation succeeded.
                - data (list[DocumentVersionInfo]): List of all version records for this document if successful.
                - error (str, optional): Error message if the document does not exist.

        Constraints:
            - Document must exist in the system.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        versions = [
            dv for dv in self.document_versions.values()
            if dv["document_id"] == document_id
        ]

        return {"success": True, "data": versions}

    def get_latest_document_version(self, document_id: str) -> dict:
        """
        Retrieve the most recent DocumentVersionInfo (content and metadata) for a specified document.

        Args:
            document_id (str): Unique identifier of the document.

        Returns:
            dict: 
              - On success: {"success": True, "data": DocumentVersionInfo}
              - On failure: {"success": False, "error": <reason>}

        Constraints:
            - Document ID must exist.
            - Must have at least one version for the document.
            - Returns the version with the highest version_number.
        """
        if document_id not in self.documents:
            return { "success": False, "error": "Document not found" }

        versions = [
            v for v in self.document_versions.values()
            if v['document_id'] == document_id
        ]

        if not versions:
            return { "success": False, "error": "No versions available for this document" }

        # Find version with highest version_number
        latest_version = max(versions, key=lambda v: v['version_number'])
        return { "success": True, "data": latest_version }

    def get_document_reviews(self, document_id: str) -> dict:
        """
        List all review/audit records linked to a specific document.

        Args:
            document_id (str): The unique ID of the document.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": List[ReviewInfo]  # All reviews tied to the provided document (may be empty)
                }
                Failure: {
                    "success": False,
                    "error": "Document does not exist"
                }
        Constraints:
            - document_id must exist in the system.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        reviews_for_doc = [
            review for review in self.reviews.values()
            if review["document_id"] == document_id
        ]
        return {"success": True, "data": reviews_for_doc}

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve details about a specific review or audit by its review ID.
    
        Args:
            review_id (str): The unique identifier for the review or audit.
        
        Returns:
            dict: 
              - {"success": True, "data": ReviewInfo} if the review exists.
              - {"success": False, "error": str} if no such review exists.
    
        Constraints:
            - review_id must exist in the system; otherwise, an error is returned.
        """
        review = self.reviews.get(review_id)
        if review is None:
            return {"success": False, "error": "Review with the specified ID does not exist."}
        return {"success": True, "data": review}

    def list_documents_accessible_by_user(self, user_id: str) -> dict:
        """
        Returns a list of all documents (with metadata) the user with user_id has at least 'read' access to.

        Args:
            user_id (str): Identifier of the user whose document access is being queried.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo]  # All documents the user can access with at least 'read' permission.
            }
            or
            {
                "success": False,
                "error": str  # e.g. user does not exist
            }

        Constraints:
            - User must exist in the system.
            - Only permissions with access_level in {'read','write','admin'} count.
            - Ignores permissions for documents that do not exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        allowed_levels = {"read", "write", "admin"}
        accessible_docs = set()

        for perm in self.permissions.values():
            if perm["user_id"] == user_id and perm["access_level"] in allowed_levels:
                doc_id = perm["document_id"]
                if doc_id in self.documents:
                    accessible_docs.add(doc_id)

        # Retrieve DocumentInfo for each accessible document
        result = [self.documents[doc_id] for doc_id in accessible_docs]

        return {"success": True, "data": result}

    def get_document_access_log(self, document_id: str) -> dict:
        """
        Retrieve the access log/history for a confidential or controlled document.

        Args:
            document_id (str): The ID of the document whose access log is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # List of log entries (may be empty if no logs)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. document not found or not confidential/controlled
            }

        Constraints:
            - The document must exist.
            - Logging is only applicable to 'confidential' or 'controlled' documents.
            - If no log exists, return an empty list as success.
        """
        # Check document existence
        doc = self.documents.get(document_id)
        if not doc:
            return { "success": False, "error": "Document not found" }

        # Check if the document is confidential or controlled
        if not self._is_confidential_or_controlled(document_id):
            return { "success": False, "error": "Document is not confidential or controlled" }

        logs = self._ensure_document_access_logs().get(document_id, [])
        return { "success": True, "data": logs }

    def log_document_access(
        self,
        user_id: str,
        document_id: str,
        action: str,
        timestamp: Optional[str] = None
    ) -> dict:
        """
        Record/log that a user has accessed a confidential or controlled document.

        Args:
            user_id (str): ID of the user accessing the document.
            document_id (str): ID of the accessed document.
            action (str): Nature of the access ('read', 'edit', etc.).
            timestamp (Optional[str]): ISO 8601 or string representation of the time of access. If None, current time is used.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Document access logged"
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Only documents marked as confidential or controlled (by 'status') are logged.
            - Both user and document must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}
        if not self._is_confidential_or_controlled(document_id):
            return {"success": False, "error": "Document is not confidential or controlled; access logging not required"}
        if not timestamp:
            timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        logs = self._ensure_document_access_logs()
        logs.setdefault(document_id, [])
        logs[document_id].append(
            {
                "user_id": user_id,
                "document_id": document_id,
                "action": action,
                "timestamp": timestamp,
            }
        )
        return {"success": True, "message": "Document access logged"}

    def create_document_version(
        self,
        document_id: str,
        new_content: str,
        author_id: str
    ) -> dict:
        """
        Save a new version of a document when its content is edited (never overwriting older versions).

        Args:
            document_id (str): ID of the document to update.
            new_content (str): New content for the document.
            author_id (str): ID of the user making the edit.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Document version created",
                        "data": { ...DocumentVersionInfo... }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - Document must exist.
            - Author (user) must exist.
            - Author must have 'write' or 'admin' permission for this document.
            - A new DocumentVersion record is created, not overwriting old.
            - The document's version_id, content, and updated_at are updated.
            - Version numbers are monotonically incremented per document.
        """

        # Check document exists
        doc = self.documents.get(document_id)
        if not doc:
            return { "success": False, "error": "Document does not exist" }

        # Check author exists
        if author_id not in self.users:
            return { "success": False, "error": "Author (user) does not exist" }

        # Check author permission
        allowed = False
        for perm in self.permissions.values():
            if (
                perm["user_id"] == author_id
                and perm["document_id"] == document_id
                and perm["access_level"] in ("write", "admin")
            ):
                allowed = True
                break
        if not allowed:
            return { "success": False, "error": "User does not have permission to edit this document" }

        # Determine the new version number
        prev_versions = [
            v for v in self.document_versions.values()
            if v["document_id"] == document_id
        ]
        if prev_versions:
            latest_version_number = max(v["version_number"] for v in prev_versions)
            new_version_number = latest_version_number + 1
        else:
            new_version_number = 1  # First version

        now_str = str(int(time.time()))
        new_version_id = str(uuid.uuid4())

        # Create the new version record
        new_version: DocumentVersionInfo = {
            "version_id": new_version_id,
            "document_id": document_id,
            "version_number": new_version_number,
            "content_snapshot": new_content,
            "created_at": now_str,
            "author_id": author_id
        }
        self.document_versions[new_version_id] = new_version

        # Update the DocumentInfo for current version
        doc["version_id"] = new_version_id
        doc["content"] = new_content
        doc["updated_at"] = now_str
        self.documents[document_id] = doc  # update

        return {
            "success": True,
            "message": "Document version created",
            "data": new_version
        }

    def grant_document_permission(self, user_id: str, document_id: str, access_level: str) -> dict:
        """
        Assign or update a user's permissions (read/write/admin) for a document.

        Args:
            user_id (str): The user's unique ID.
            document_id (str): The document's unique ID.
            access_level (str): The permission level to grant. Must be one of 'read', 'write', 'admin'.

        Returns:
            dict: {
                "success": True,
                "message": "Permission granted/updated for user X on document Y as Z."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - user_id must exist.
            - document_id must exist.
            - access_level must be valid.
            - Update permission if already present; otherwise, create a new permission entry.
        """
        valid_levels = {"read", "write", "admin"}
        level = access_level.lower()
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist." }
        if level not in valid_levels:
            return { "success": False, "error": "Invalid access level. Must be 'read', 'write', or 'admin'." }
    
        # Check if permission already exists
        existing_permission_id = None
        for pid, info in self.permissions.items():
            if info["user_id"] == user_id and info["document_id"] == document_id:
                existing_permission_id = pid
                break

        if existing_permission_id:
            self.permissions[existing_permission_id]["access_level"] = level
            return {
                "success": True,
                "message": f"Permission updated for user {user_id} on document {document_id} to access level '{level}'."
            }
        else:
            new_permission_id = f"perm_{len(self.permissions)+1:06d}"
            self.permissions[new_permission_id] = {
                "permission_id": new_permission_id,
                "user_id": user_id,
                "document_id": document_id,
                "access_level": level
            }
            return {
                "success": True,
                "message": f"Permission granted for user {user_id} on document {document_id} as '{level}'."
            }

    def revoke_document_permission(self, user_id: str, document_id: str, access_level: str = None) -> dict:
        """
        Remove or downgrade a user's permission for a document.

        Args:
            user_id (str): The ID of the user whose permission is to be removed or downgraded.
            document_id (str): The ID of the document.
            access_level (str, optional): If provided, downgrade to this access level.
                Valid values: 'read', 'write', 'admin'. If not provided, permission is removed.

        Returns:
            dict: 
              - Success (revoke): {"success": True, "message": "..."}
              - Success (downgrade): {"success": True, "message": "..."}
              - Failure: {"success": False, "error": "..."}
        Constraints:
            - User and document must exist.
            - Permission between user and document must exist.
            - Downgrade access_level must be valid and different from current.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": f"User '{user_id}' does not exist"}
        # Check if document exists
        if document_id not in self.documents:
            return {"success": False, "error": f"Document '{document_id}' does not exist"}
        # Find permission object
        permission_id = None
        for pid, perm in self.permissions.items():
            if perm["user_id"] == user_id and perm["document_id"] == document_id:
                permission_id = pid
                break
        if permission_id is None:
            return {"success": False, "error": f"No permission found for user '{user_id}' on document '{document_id}'"}
        if access_level is None:
            # Remove the permission
            del self.permissions[permission_id]
            return {
                "success": True,
                "message": f"Permission revoked for user '{user_id}' on document '{document_id}'"
            }
        # Check if access_level is valid
        valid_levels = {"read", "write", "admin"}
        if access_level not in valid_levels:
            return {"success": False, "error": f"Invalid access_level '{access_level}'"}
        # If same level, no operation
        current_level = self.permissions[permission_id]["access_level"]
        if current_level == access_level:
            return {
                "success": True,
                "message": f"User '{user_id}' already has '{access_level}' access to document '{document_id}' (no downgrade needed)"
            }
        # Downgrade to new level
        self.permissions[permission_id]["access_level"] = access_level
        return {
            "success": True,
            "message": f"Permission level for user '{user_id}' on document '{document_id}' set to '{access_level}'"
        }

    def initiate_document_review(
        self,
        document_id: str,
        reviewer_id: str,
        status: str = "initiated",
        initiated_at: str = None
    ) -> dict:
        """
        Start a new review/audit for a document, assigning a qualified reviewer/auditor.

        Args:
            document_id (str): The ID of the document to review.
            reviewer_id (str): The ID of the user to assign as reviewer.
            status (str, optional): Initial review status (default: "initiated").
            initiated_at (str, optional): Timestamp of initiation (default: current ISO time if not provided).

        Returns:
            dict: {
                "success": True,
                "message": str,
                "review_id": str,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - document_id must reference an existing document.
            - reviewer_id must reference an existing user whose role includes 'reviewer' or 'auditor'.
            - On creation, completed_at is empty.
        """

        # Check if document exists
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        # Check if reviewer exists
        if reviewer_id not in self.users:
            return {"success": False, "error": "Reviewer (user) does not exist"}

        role = self.users[reviewer_id].get("role", "").lower()
        if "reviewer" not in role and "auditor" not in role:
            return {"success": False, "error": "User's role is not authorized for document review"}

        # Prepare timestamps
        if initiated_at is None:
            # Use current UTC time in ISO format
            initiated_at = datetime.utcnow().isoformat()

        completed_at = ""

        # Generate a unique review_id
        new_numeric_id = len(self.reviews) + 1
        review_id = f"review_{new_numeric_id}"

        # Prepare review info
        review_info = {
            "review_id": review_id,
            "document_id": document_id,
            "reviewer_id": reviewer_id,
            "status": status,
            "initiated_at": initiated_at,
            "completed_at": completed_at,
        }

        self.reviews[review_id] = review_info

        return {
            "success": True,
            "message": f"Review has been initiated for document {document_id} by reviewer {reviewer_id}",
            "review_id": review_id,
        }


    def update_review_status(self, review_id: str, new_status: str, user_id: str) -> dict:
        """
        Change the status of an ongoing review (e.g., from pending to completed), enforcing that only
        users with role 'reviewer' or 'auditor' may perform this action. If setting status to 'completed',
        sets completed_at; if reverting, clears it.

        Args:
            review_id (str): Review identifier to update.
            new_status (str): The new status to set.
            user_id (str): User requesting the status change.

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
        Constraints:
            - Only users with 'reviewer' or 'auditor' roles may update reviews.
            - If status transitions to 'completed', set completed_at = now.
            - If status transitions away from 'completed', clear completed_at.
            - Review must exist.
            - User must exist.
        """
        # Check review exists
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review not found" }

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Enforce permission: only reviewer/auditor roles may update
        role = user.get("role", "").lower()
        if ("reviewer" not in role) and ("auditor" not in role):
            return {
                "success": False,
                "error": "Permission denied: only reviewer or auditor may update review status."
            }

        old_status = review["status"]
        review["status"] = new_status

        # Handle completed_at update
        if new_status.lower() == "completed":
            # Set current ISO timestamp
            review["completed_at"] = datetime.utcnow().isoformat(timespec="seconds")
        else:
            review["completed_at"] = ""

        self.reviews[review_id] = review

        if old_status == new_status:
            return {
                "success": True,
                "message": f"Review status was already '{new_status}'. No change made."
            }
        else:
            return {
                "success": True,
                "message": f"Review status updated from '{old_status}' to '{new_status}'."
            }

    def link_review_to_document(self, review_id: str, document_id: str) -> dict:
        """
        Associate an existing review/audit process with a document.
    
        Args:
            review_id (str): The identifier of the review/audit record to link.
            document_id (str): The identifier of the document to be associated.

        Returns:
            dict: 
                On success: {"success": True, "message": "Review linked to document."}
                On error:   {"success": False, "error": "<reason>"}

        Constraints:
            - Both review and document must exist.
            - Updates the 'document_id' field of the review to the specified document.
            - Operation is idempotent if already linked.
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review does not exist."}
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist."}

        review = self.reviews[review_id]
        if review["document_id"] == document_id:
            return {"success": True, "message": "Review already linked to document."}

        review["document_id"] = document_id
        # Optionally update in self.reviews for completeness
        self.reviews[review_id] = review
        return {"success": True, "message": "Review linked to document."}


    def edit_document_content(self, document_id: str, user_id: str, new_content: str) -> dict:
        """
        Update a document's content, creating a new version and logging the action if confidential/controlled.

        Args:
            document_id (str): The id of the document to update.
            user_id (str): The user making the edit.
            new_content (str): The new content for the document.

        Returns:
            dict: 
                On success: {"success": True, "message": "Document updated and new version created (version_id: ...)."}
                On failure: {"success": False, "error": <reason str>}
    
        Constraints:
            - User must exist and have 'write' or 'admin' permission for the document.
            - Every edit produces a new DocumentVersion; previous versions are preserved.
            - Confidential/controlled documents have edit action logged.
            - Document's content, version_id, and updated_at are updated for latest state.
        """
        # Existence checks
        doc = self.documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Document not found"}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Permission check (must have 'write' or 'admin' access)
        user_perms = [
            p for p in self.permissions.values()
            if p["user_id"] == user_id and p["document_id"] == document_id and p["access_level"] in ("write", "admin")
        ]
        if not user_perms:
            return {"success": False, "error": "Permission denied: user lacks write/admin access to document"}

        # Determine version number
        prev_versions = [
            v for v in self.document_versions.values() if v["document_id"] == document_id
        ]
        max_version_number = max([v["version_number"] for v in prev_versions], default=0)
        new_version_number = max_version_number + 1

        # Generate new version_id
        new_version_id = str(uuid.uuid4())

        now_str = str(int(time.time()))

        # Create new document version
        new_doc_version = {
            "version_id": new_version_id,
            "document_id": document_id,
            "version_number": new_version_number,
            "content_snapshot": new_content,
            "created_at": now_str,
            "author_id": user_id
        }
        self.document_versions[new_version_id] = new_doc_version

        # Update the document record (content, version_id, updated_at)
        doc["content"] = new_content
        doc["version_id"] = new_version_id
        doc["updated_at"] = now_str
        self.documents[document_id] = doc

        # If confidential/controlled, log the access
        conf_types = ["confidential", "controlled"]
        is_confidential = (
            doc.get("document_type", "").lower() in conf_types or
            doc.get("status", "").lower() in conf_types
        )
        if is_confidential:
            self.log_document_access(
                user_id=user_id,
                document_id=document_id,
                action="edit",
                timestamp=now_str
            )

        return {
            "success": True,
            "message": f"Document updated and new version created (version_id: {new_version_id})."
        }

    def assign_reviewer_to_review(self, review_id: str, user_id: str) -> dict:
        """
        Assign an eligible user (with 'reviewer' or 'auditor' in their role) to a pending review.

        Args:
            review_id (str): ID of the review to assign.
            user_id (str): ID of the user to be assigned as reviewer.

        Returns:
            dict: 
                Success: { "success": True, "message": ... }
                Failure: { "success": False, "error": ... }
    
        Constraints:
            - The given review_id must exist.
            - The review's status must be 'pending'.
            - The given user_id must exist.
            - The user's role must include 'reviewer' or 'auditor'.
        """
        # Check if the review exists
        if review_id not in self.reviews:
            return { "success": False, "error": "Review does not exist." }
        review = self.reviews[review_id]
    
        # Check if the user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        user = self.users[user_id]
    
        # Check if the review status is 'pending'
        if review["status"].lower() != "pending":
            return { "success": False, "error": "Review is not pending and cannot be assigned a reviewer." }
    
        # Check if the user has 'reviewer' or 'auditor' in their role
        role = user["role"].lower()
        if "reviewer" not in role and "auditor" not in role:
            return { "success": False, "error": "User is not eligible to be a reviewer (role must include 'reviewer' or 'auditor')." }
    
        # Assign the user as the reviewer
        review["reviewer_id"] = user_id
        # Optionally, you could update any relevant timestamps if needed here
    
        # Persist the change
        self.reviews[review_id] = review
    
        return {
            "success": True,
            "message": f"User {user_id} assigned as reviewer to review {review_id}."
        }

    def delete_document(self, user_id: str, document_id: str) -> dict:
        """
        Remove a document (and all related records) from the system.
        Only users with explicit 'admin' permission for the document may perform this operation.

        Args:
            user_id (str): The user requesting deletion.
            document_id (str): The ID of the document to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Document <document_id> and all related records deleted."
            } on success,
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - The document must exist.
            - The user must exist and have 'admin' access for this document.
            - All document versions, permissions, and reviews linked to this document are removed.
            - Access action is logged if the document type is 'confidential' or 'controlled'.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        # Check document exists
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist."}
        # Check for admin permission for this document
        has_admin = any(
            p["user_id"] == user_id and p["document_id"] == document_id and p["access_level"] == "admin"
            for p in self.permissions.values()
        )
        if not has_admin:
            return {"success": False, "error": "User does not have admin permission for this document."}

        doc_info = self.documents[document_id]

        # Log deletion if confidential or controlled
        if self._is_confidential_or_controlled(document_id):
            self.log_document_access(user_id=user_id, document_id=document_id, action="delete")

        # Delete document versions
        to_remove_versions = [vid for vid, v in self.document_versions.items() if v["document_id"] == document_id]
        for vid in to_remove_versions:
            del self.document_versions[vid]

        # Delete permissions
        to_remove_perms = [pid for pid, p in self.permissions.items() if p["document_id"] == document_id]
        for pid in to_remove_perms:
            del self.permissions[pid]

        # Delete reviews
        to_remove_revs = [rid for rid, r in self.reviews.items() if r["document_id"] == document_id]
        for rid in to_remove_revs:
            del self.reviews[rid]

        # Finally delete the document
        del self.documents[document_id]

        return {
            "success": True,
            "message": f"Document {document_id} and all related records deleted."
        }

    def unlink_review_from_document(self, review_id: str) -> dict:
        """
        Remove the association between a review and its linked document.

        Args:
            review_id (str): Identifier of the review/audit to be unlinked.

        Returns:
            dict: {
                "success": True,
                "message": "Review unlinked from document."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Review must exist.
            - If review is not currently linked to any document, operation is a no-op but returns success.
            - Review is maintained in the system, but after this, its 'document_id' is None.
        """
        review_info = self.reviews.get(review_id)
        if not review_info:
            return { "success": False, "error": "Review not found." }
    
        if review_info["document_id"] is None:
            # Already unlinked; treat as idempotent/no-op
            return { "success": True, "message": "Review was already unlinked from document." }
    
        review_info["document_id"] = None
        self.reviews[review_id] = review_info  # This line is not strictly needed with dicts/mutable
        return { "success": True, "message": "Review unlinked from document." }


class CorporatePolicyDocumentManagementSystem(BaseEnv):
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
        def _normalize_document_access_logs(raw_logs, documents):
            if raw_logs in (None, "", []):
                return {}
            parsed = raw_logs
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except json.JSONDecodeError:
                    return {}
            if isinstance(parsed, dict):
                normalized = {}
                for document_id, entries in parsed.items():
                    if isinstance(entries, str):
                        try:
                            entries = json.loads(entries)
                        except json.JSONDecodeError:
                            continue
                    if isinstance(entries, list):
                        normalized[document_id] = copy.deepcopy(entries)
                return normalized
            if isinstance(parsed, list):
                grouped = {}
                known_document_ids = list(documents.keys())
                for entry in parsed:
                    if not isinstance(entry, dict):
                        continue
                    document_id = entry.get("document_id")
                    if not document_id and len(known_document_ids) == 1:
                        document_id = known_document_ids[0]
                    if not document_id:
                        continue
                    entry = copy.deepcopy(entry)
                    entry["document_id"] = document_id
                    grouped.setdefault(document_id, []).append(entry)
                return grouped
            return {}

        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            if key == "document_access_logs":
                setattr(
                    env,
                    key,
                    _normalize_document_access_logs(value, getattr(env, "documents", {})),
                )
                continue
            if key == "log_document_access":
                normalized = _normalize_document_access_logs(value, getattr(env, "documents", {}))
                if normalized:
                    existing = getattr(env, "document_access_logs", {})
                    if not isinstance(existing, dict):
                        existing = {}
                    for document_id, entries in normalized.items():
                        existing.setdefault(document_id, [])
                        existing[document_id].extend(copy.deepcopy(entries))
                    setattr(env, "document_access_logs", existing)
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def get_document_by_title(self, **kwargs):
        return self._call_inner_tool('get_document_by_title', kwargs)

    def list_documents_by_type(self, **kwargs):
        return self._call_inner_tool('list_documents_by_type', kwargs)

    def list_user_permissions_for_document(self, **kwargs):
        return self._call_inner_tool('list_user_permissions_for_document', kwargs)

    def check_user_permission_for_document(self, **kwargs):
        return self._call_inner_tool('check_user_permission_for_document', kwargs)

    def get_document_versions(self, **kwargs):
        return self._call_inner_tool('get_document_versions', kwargs)

    def get_latest_document_version(self, **kwargs):
        return self._call_inner_tool('get_latest_document_version', kwargs)

    def get_document_reviews(self, **kwargs):
        return self._call_inner_tool('get_document_reviews', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def list_documents_accessible_by_user(self, **kwargs):
        return self._call_inner_tool('list_documents_accessible_by_user', kwargs)

    def get_document_access_log(self, **kwargs):
        return self._call_inner_tool('get_document_access_log', kwargs)

    def create_document_version(self, **kwargs):
        return self._call_inner_tool('create_document_version', kwargs)

    def grant_document_permission(self, **kwargs):
        return self._call_inner_tool('grant_document_permission', kwargs)

    def revoke_document_permission(self, **kwargs):
        return self._call_inner_tool('revoke_document_permission', kwargs)

    def initiate_document_review(self, **kwargs):
        return self._call_inner_tool('initiate_document_review', kwargs)

    def update_review_status(self, **kwargs):
        return self._call_inner_tool('update_review_status', kwargs)

    def link_review_to_document(self, **kwargs):
        return self._call_inner_tool('link_review_to_document', kwargs)

    def edit_document_content(self, **kwargs):
        return self._call_inner_tool('edit_document_content', kwargs)

    def assign_reviewer_to_review(self, **kwargs):
        return self._call_inner_tool('assign_reviewer_to_review', kwargs)

    def delete_document(self, **kwargs):
        return self._call_inner_tool('delete_document', kwargs)

    def unlink_review_from_document(self, **kwargs):
        return self._call_inner_tool('unlink_review_from_document', kwargs)
