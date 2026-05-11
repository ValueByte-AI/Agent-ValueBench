# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from typing import Optional, Dict, Any




class ThemeInfo(TypedDict):
    theme_id: str
    name: str
    weight: float
    description: str
    created_by: str
    active_status: bool  # represents whether the theme is active


class TextDocumentInfo(TypedDict):
    document_id: str
    content: str
    date_added: str
    source: str
    processed_status: bool  # represents if the document has been processed


class ThemeAssignmentInfo(TypedDict):
    document_id: str
    theme_id: str
    score: float
    timestamp: str


class UserInfo(TypedDict):
    _id: str
    name: str
    role: str
    preference: str  # or Dict[str, Any], depending on detail


class _GeneratedEnvImpl:
    def __init__(self):
        # Themes: {theme_id: ThemeInfo}
        # Entity: Theme (theme_id, name, weight, description, created_by, active_status)
        self.themes: Dict[str, ThemeInfo] = {}

        # Documents: {document_id: TextDocumentInfo}
        # Entity: TextDocument (document_id, content, date_added, source, processed_status)
        self.documents: Dict[str, TextDocumentInfo] = {}

        # Users: {user_id: UserInfo}
        # Entity: User (_id, name, role, preference)
        self.users: Dict[str, UserInfo] = {}

        # Theme assignments: List of ThemeAssignmentInfo entries
        # Entity: ThemeAssignment (document_id, theme_id, score, timestamp)
        self.theme_assignments: List[ThemeAssignmentInfo] = []

        # === Constraints ===
        # - Theme names must be unique for each user or project scope.
        # - Theme weights must be within an allowed range (e.g., 0.0 to 1.0).
        # - Only active themes can be used in text analysis.
        # - Text documents can be assigned to multiple themes.
        # - Users can only modify or remove themes they created or have permission for.

    def get_theme_by_name(self, name: str, created_by: str) -> dict:
        """
        Retrieve a theme by (name, created_by user/project).

        Args:
            name (str): The name of the theme.
            created_by (str): User ID or project to scope the search.

        Returns:
            dict:
                - If found: {"success": True, "data": ThemeInfo}
                - If not found: {"success": False, "error": "Theme not found"}
                - If input invalid: {"success": False, "error": "Missing 'name' or 'created_by' parameter."}

        Constraints:
            - Theme names must be unique per user/project.
        """
        if not name or not created_by:
            return { "success": False, "error": "Missing 'name' or 'created_by' parameter." }
    
        for theme in self.themes.values():
            if theme["name"] == name and theme["created_by"] == created_by:
                return { "success": True, "data": theme }

        return { "success": False, "error": "Theme not found" }

    def list_user_themes(self, user_id: str) -> dict:
        """
        List all themes created by a specific user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ThemeInfo],  # List of themes created by the user (could be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of failure (e.g., user does not exist)
            }

        Constraints:
            - The user must exist in the system.
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        themes = [theme for theme in self.themes.values() if theme["created_by"] == user_id]
        return { "success": True, "data": themes }

    def get_theme_by_id(self, theme_id: str) -> dict:
        """
        Retrieve theme information given a theme_id.

        Args:
            theme_id (str): The unique identifier of the theme.

        Returns:
            dict: {
                "success": True,
                "data": ThemeInfo
            } if theme_id exists,
            or
            {
                "success": False,
                "error": str
            } if not found.

        Constraints:
            - theme_id must exist.
            - No permission or status checks are required.
        """
        theme = self.themes.get(theme_id)
        if not theme:
            return {"success": False, "error": "Theme not found"}

        return {"success": True, "data": theme}

    def list_active_themes(self) -> dict:
        """
        Return all active themes available for analysis.

        Returns:
            dict: {
                "success": True,
                "data": List[ThemeInfo],  # List of active themes (may be empty)
            }

        No inputs. No user/permission restrictions.
        If there are no active themes, returns an empty list.
        """
        active_themes = [
            theme_info for theme_info in self.themes.values()
            if theme_info.get("active_status", False) is True
        ]
        return { "success": True, "data": active_themes }

    def get_theme_weight(self, theme_id: str) -> dict:
        """
        Retrieve the weight (value between allowed bounds) for a given theme.

        Args:
            theme_id (str): The identifier of the theme to query.

        Returns:
            dict: {
                "success": True,
                "data": float  # Theme weight
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. theme not found
            }

        Constraints:
            - Theme must exist in the system. If not, returns an error.
            - Weight is returned regardless of other flags (e.g., active).
        """
        theme = self.themes.get(theme_id)
        if not theme:
            return { "success": False, "error": "Theme not found" }
        return { "success": True, "data": theme["weight"] }

    def list_themes_by_status(self, active_status: bool) -> dict:
        """
        List all themes filtered by their active_status.

        Args:
            active_status (bool): If True, list only active themes; if False, list only inactive themes.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[ThemeInfo],  # List of themes with matching status (may be empty)
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Description of the error
                    }
    
        Constraints:
            - active_status must be a boolean value.
            - Returns all themes matching the requested status.
        """
        if not isinstance(active_status, bool):
            return {"success": False, "error": "active_status must be a boolean."}

        result = [
            theme for theme in self.themes.values()
            if theme.get("active_status", False) == active_status
        ]
        return {"success": True, "data": result}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Get user profile and permissions by user_id.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            dict: 
                - Success: {"success": True, "data": UserInfo}
                - Failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The user must exist in the system.
            - Role is returned as the user's permission indicator (explicit permission structure may be queried elsewhere).
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found."}
        return {"success": True, "data": user}

    def get_user_permissions(self, user_id: str) -> dict:
        """
        Query what theme-related actions a user can perform.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of allowed theme-related actions for this user
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. user not found
            }

        Permissions model (example):
            - 'admin': can perform all theme-related operations
            - 'editor': can add, update, remove, activate/deactivate themes they created
            - 'viewer': can view/list themes only
            - Unknown role: no permissions
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        role = user.get("role", "")
        # Define permissions for roles
        permissions_map = {
            "admin": [
                "add_theme",
                "update_theme",
                "remove_theme",
                "set_theme_active_status",
                "assign_theme_to_document",
                "update_theme_assignment_score",
                "remove_theme_assignment",
                "list_user_themes",
                "list_active_themes",
                "get_theme_by_id",
                "get_theme_by_name",
                "list_themes_by_status",
                "get_theme_weight",
                "list_theme_assignments_for_document",
                "list_documents_by_theme",
            ],
            "editor": [
                "add_theme",
                "update_theme",           # (on themes they created)
                "remove_theme",           # (on themes they created)
                "set_theme_active_status",# (on themes they created)
                "assign_theme_to_document",
                "update_theme_assignment_score",
                "remove_theme_assignment",
                "list_user_themes",
                "list_active_themes",
                "get_theme_by_id",
                "get_theme_by_name",
                "list_themes_by_status",
                "get_theme_weight",
                "list_theme_assignments_for_document",
                "list_documents_by_theme",
            ],
            "viewer": [
                "list_user_themes",
                "list_active_themes",
                "get_theme_by_id",
                "get_theme_by_name",
                "list_themes_by_status",
                "get_theme_weight",
                "list_theme_assignments_for_document",
                "list_documents_by_theme",
            ]
        }

        allowed_actions = permissions_map.get(role, [])
        return { "success": True, "data": allowed_actions }

    def list_documents(self) -> dict:
        """
        List all text documents currently stored in the system.

        Returns:
            dict: 
                - "success": True
                - "data": List[TextDocumentInfo] (May be empty if no documents exist.)
        """
        # Gather all documents
        all_documents = list(self.documents.values())
        return {
            "success": True,
            "data": all_documents
        }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve the full content and metadata for a text document by its ID.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": TextDocumentInfo
                }
                On failure:
                {
                    "success": False,
                    "error": "Document not found"
                }

        Constraints:
            - Document must exist in the system; otherwise, failure is returned.
            - No permission check is enforced for document retrieval.
        """
        doc = self.documents.get(document_id)
        if doc is None:
            return {"success": False, "error": "Document not found"}
        return {"success": True, "data": doc}

    def list_theme_assignments_for_document(self, document_id: str) -> dict:
        """
        List all assigned themes (with scores and assignment info) for a document.

        Args:
            document_id (str): The unique identifier of the text document.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ThemeAssignmentInfo],  # List of all assignments (may be empty)
                }
                OR
                {
                    "success": False,
                    "error": str  # If document does not exist
                }

        Constraints:
            - document_id must exist in the documents store.
        """
        # Check if the document exists
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist" }

        # List all theme assignments for this document
        data = [
            assignment for assignment in self.theme_assignments 
            if assignment["document_id"] == document_id
        ]

        return { "success": True, "data": data }

    def list_documents_by_theme(self, theme_id: str) -> dict:
        """
        List all documents associated with a specific theme.

        Args:
            theme_id (str): The theme's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[TextDocumentInfo],
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - The theme must exist.
            - Only existing documents are returned (ignore assignments to missing documents).
        """
        if theme_id not in self.themes:
            return { "success": False, "error": "Theme does not exist" }

        # Collect all document_ids associated with this theme
        associated_doc_ids = {
            assignment["document_id"] for assignment in self.theme_assignments
            if assignment["theme_id"] == theme_id
        }

        # Retrieve document information for each id (filter-out missing docs)
        documents = [
            self.documents[doc_id]
            for doc_id in associated_doc_ids
            if doc_id in self.documents
        ]

        return { "success": True, "data": documents }

    def check_theme_edit_permission(self, user_id: str, theme_id: str) -> dict:
        """
        Verify if a user can edit or remove a specific theme.

        Args:
            user_id (str): The user's unique ID.
            theme_id (str): The theme's unique ID.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "can_edit": bool
                }
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Users can only modify or remove themes they created,
              or if they have required permission (e.g., are admin).
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        theme = self.themes.get(theme_id)
        if not theme:
            return {"success": False, "error": "Theme not found"}

        # Permission check:
        can_edit = False
        if theme["created_by"] == user_id:
            can_edit = True
        elif user.get("role", "").lower() == "admin":
            can_edit = True

        return {"success": True, "data": {"can_edit": can_edit}}


    def add_theme(
        self,
        name: str,
        weight: float,
        description: str,
        created_by: str,
        active_status: bool
    ) -> Dict[str, Any]:
        """
        Create and register a new theme with uniqueness and weight validation.

        Args:
            name (str): Name of the theme (must be unique per user).
            weight (float): Weight for the theme, in [0.0, 1.0].
            description (str): Text description for the theme.
            created_by (str): User ID of the creator.
            active_status (bool): Whether the theme is active.

        Returns:
            dict: {
                "success": True,
                "message": "Theme added.",
                "theme_id": <theme_id>
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Theme name unique per user (created_by).
            - Weight in [0.0, 1.0].
            - User must exist.
        """
        # User existence check
        if created_by not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Name uniqueness for user
        for theme in self.themes.values():
            if theme["name"].lower() == name.lower() and theme["created_by"] == created_by:
                return { "success": False, "error": "Theme name already exists for this user." }

        # Weight range check
        if not (0.0 <= weight <= 1.0):
            return { "success": False, "error": "Weight must be between 0.0 and 1.0." }

        # Generate theme ID
        theme_id = str(uuid.uuid4())

        # Create and register Theme
        self.themes[theme_id] = {
            "theme_id": theme_id,
            "name": name,
            "weight": float(weight),
            "description": description,
            "created_by": created_by,
            "active_status": bool(active_status)
        }

        return {
            "success": True,
            "message": "Theme added.",
            "theme_id": theme_id
        }

    def update_theme(
        self,
        theme_id: str,
        user_id: str,
        name: str = None,
        weight: float = None,
        description: str = None,
        active_status: bool = None
    ) -> dict:
        """
        Modify theme properties (name, weight, description, active_status), if permitted.

        Args:
            theme_id (str): The ID of the theme to update.
            user_id (str): The ID of the user attempting the update.
            name (str, optional): New theme name.
            weight (float, optional): New weight (must be 0.0 to 1.0).
            description (str, optional): New theme description.
            active_status (bool, optional): New activation status.

        Returns:
            dict: On success,
                { "success": True, "message": "Theme updated successfully." }
            On failure,
                { "success": False, "error": str }

        Constraints:
            - User must be theme creator or have permission to edit.
            - Theme name must be unique for the user.
            - Weight must be between 0.0 and 1.0.
        """
        # Does theme exist?
        theme = self.themes.get(theme_id)
        if not theme:
            return {"success": False, "error": "Theme not found."}

        # User exists?
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # Permission check: the theme creator or an admin may edit.
        is_admin = user.get("role", "").lower() == "admin"
        if theme["created_by"] != user_id and not is_admin:
            return {"success": False, "error": "User not authorized to edit this theme."}

        # If updating name, check for uniqueness (must be unique for the user)
        owner_id = theme["created_by"]

        if name is not None:
            for t in self.themes.values():
                if (
                    t["theme_id"] != theme_id and
                    t["name"] == name and
                    t["created_by"] == owner_id
                ):
                    return {"success": False, "error": "Theme name must be unique for this user."}

            if not name.strip():
                return {"success": False, "error": "Theme name cannot be empty."}

        # Weight check
        if weight is not None:
            if not (0.0 <= weight <= 1.0):
                return {"success": False, "error": "Weight must be between 0.0 and 1.0."}

        # No-ops are allowed; otherwise update fields
        updated_fields = []
        if name is not None and theme["name"] != name:
            theme["name"] = name
            updated_fields.append("name")
        if weight is not None and theme["weight"] != weight:
            theme["weight"] = weight
            updated_fields.append("weight")
        if description is not None and theme["description"] != description:
            theme["description"] = description
            updated_fields.append("description")
        if active_status is not None and theme["active_status"] != active_status:
            theme["active_status"] = active_status
            updated_fields.append("active_status")

        # Actually update the main dict (since theme is a ref, it's updated in place)
        self.themes[theme_id] = theme

        return {
            "success": True,
            "message": "Theme updated successfully." if updated_fields else "No changes made to theme."
        }

    def remove_theme(self, theme_id: str, user_id: str) -> dict:
        """
        Remove (deactivate) a theme if the requesting user has permission.

        Args:
            theme_id (str): The ID of the theme to remove.
            user_id (str): The ID of the user requesting the removal.

        Returns:
            dict:
                On success: { "success": True, "message": "Theme deactivated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only the theme creator or a user with admin role may remove a theme.
            - If successful, sets the theme's active_status to False (deactivation).
            - If theme does not exist, or user does not exist, or no permission, fail.
        """
        if theme_id not in self.themes:
            return { "success": False, "error": "Theme does not exist" }
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        theme_info = self.themes[theme_id]
        user_info = self.users[user_id]
        creator_id = theme_info["created_by"]

        # Permission check: admin or creator can remove
        is_admin = user_info.get("role", "").lower() == "admin"
        if not (user_id == creator_id or is_admin):
            return { "success": False, "error": "Permission denied: only the theme creator or an admin can remove this theme" }

        # Deactivate the theme (don't hard-delete for safety/history)
        if not theme_info["active_status"]:
            return { "success": False, "error": "Theme is already inactive" }
    
        self.themes[theme_id]["active_status"] = False
        return { "success": True, "message": "Theme deactivated" }

    def set_theme_active_status(self, theme_id: str, active_status: bool, user_id: str) -> dict:
        """
        Activate or deactivate a theme for future use.

        Args:
            theme_id (str): The ID of the theme to modify.
            active_status (bool): Desired status (True to activate, False to deactivate).
            user_id (str): ID of the user requesting the status change.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - The theme must exist in the system.
            - Only the theme creator, or a user with appropriate permissions ("admin" role), can change its activation status.
        """
        # Check if the theme exists
        theme = self.themes.get(theme_id)
        if theme is None:
            return {"success": False, "error": "Theme not found."}

        # Check if the user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found."}

        # Permission: Only creator or admin can change theme status
        if user['_id'] != theme['created_by'] and user['role'].lower() != 'admin':
            return {"success": False, "error": "Permission denied. Only the theme creator or an admin can change theme status."}

        # If status not changing, consider it a successful no-op
        if theme['active_status'] == active_status:
            return {"success": True, "message": f"Theme already {'active' if active_status else 'inactive'}."}

        # Set theme status
        theme['active_status'] = active_status
        self.themes[theme_id] = theme  # Not strictly necessary, but explicit

        return {
            "success": True,
            "message": f"Theme {'activated' if active_status else 'deactivated'} successfully."
        }

    def assign_theme_to_document(
        self,
        document_id: str,
        theme_id: str,
        score: float,
        timestamp: str
    ) -> dict:
        """
        Assign a theme to a document (with score and timestamp).

        Args:
            document_id (str): ID of the document to assign.
            theme_id (str): ID of the theme to assign.
            score (float): Score for this assignment.
            timestamp (str): Timestamp of the assignment (ISO string or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Theme assigned to document successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Theme must exist and be active.
            - Document must exist.
            - No explicit restriction on duplicate assignments or score range.
        """
        if document_id not in self.documents:
            return { "success": False, "error": "Document not found." }
        if theme_id not in self.themes:
            return { "success": False, "error": "Theme not found." }
        theme_info = self.themes[theme_id]
        if not theme_info.get("active_status", False):
            return { "success": False, "error": "Theme is not active and cannot be assigned." }
        # Assignment is allowed (duplicates OK by default)
        assignment = {
            "document_id": document_id,
            "theme_id": theme_id,
            "score": score,
            "timestamp": timestamp
        }
        self.theme_assignments.append(assignment)
        return { "success": True, "message": "Theme assigned to document successfully." }

    def update_theme_assignment_score(
        self,
        document_id: str,
        theme_id: str,
        new_score: float,
        timestamp: str
    ) -> dict:
        """
        Update the score for an existing theme assignment (document_id, theme_id).

        Args:
            document_id (str): ID of the text document.
            theme_id (str): ID of the theme.
            new_score (float): The new score to set for this assignment.
            timestamp (str): The timestamp for the update (e.g., ISO 8601 string).

        Returns:
            dict:
                On Success:
                    {"success": True, "message": "Theme assignment score updated successfully."}
                On Failure:
                    {"success": False, "error": "Theme assignment not found."}

        Constraints:
            - Assignment (document_id, theme_id) must exist in self.theme_assignments.
            - No new assignment is created if not found.
            - No permission checks are enforced here.
        """
        assignment_found = False
        for assignment in self.theme_assignments:
            if assignment["document_id"] == document_id and assignment["theme_id"] == theme_id:
                assignment["score"] = new_score
                assignment["timestamp"] = timestamp
                assignment_found = True
                break

        if not assignment_found:
            return {"success": False, "error": "Theme assignment not found."}
        else:
            return {"success": True, "message": "Theme assignment score updated successfully."}

    def remove_theme_assignment(self, document_id: str, theme_id: str) -> dict:
        """
        Remove the assignment of a theme from a document.

        Args:
            document_id (str): The ID of the document to remove the assignment from.
            theme_id    (str): The ID of the theme to unassign from the document.

        Returns:
            dict: {
                "success": True,
                "message": "Theme assignment removed."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The document and theme must both exist.
            - There must exist at least one assignment to remove.
            - All assignments matching (document_id, theme_id) are removed.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist."}

        if theme_id not in self.themes:
            return {"success": False, "error": "Theme does not exist."}

        initial_count = len(self.theme_assignments)
        self.theme_assignments = [
            ta for ta in self.theme_assignments
            if not (ta["document_id"] == document_id and ta["theme_id"] == theme_id)
        ]
        removed_count = initial_count - len(self.theme_assignments)

        if removed_count == 0:
            return {"success": False, "error": "No such theme assignment found for the document."}

        return {"success": True, "message": "Theme assignment removed."}

    def add_text_document(
        self,
        document_id: str,
        content: str,
        date_added: str,
        source: str,
        processed_status: bool = False
    ) -> dict:
        """
        Add a new text document to the system.

        Args:
            document_id (str): Unique identifier for the document.
            content (str): Main text content of the document.
            date_added (str): Timestamp when the document is added (ISO 8601 string preferred).
            source (str): Origin/source for the document.
            processed_status (bool, optional): Whether the document is processed. Defaults to False.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Document added successfully."
                }
                On failure:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - document_id must be unique across all documents.
            - content and document_id are required (non-empty).
        """
        if not document_id or not isinstance(document_id, str):
            return {"success": False, "error": "document_id is required and must be a non-empty string."}
        if not content or not isinstance(content, str):
            return {"success": False, "error": "content is required and must be a non-empty string."}
        if document_id in self.documents:
            return {"success": False, "error": f"Document with id '{document_id}' already exists."}
        if not isinstance(date_added, str) or not date_added:
            return {"success": False, "error": "date_added is required and must be a non-empty string."}
        if not isinstance(source, str) or not source:
            return {"success": False, "error": "source is required and must be a non-empty string."}

        new_doc: TextDocumentInfo = {
            "document_id": document_id,
            "content": content,
            "date_added": date_added,
            "source": source,
            "processed_status": processed_status
        }
        self.documents[document_id] = new_doc
        return {"success": True, "message": "Document added successfully."}

    def update_text_document(
        self,
        document_id: str,
        content: str = None,
        source: str = None,
        processed_status: bool = None
    ) -> dict:
        """
        Modify content or metadata of an existing document.

        Args:
            document_id (str): The identifier of the document to be updated.
            content (str, optional): New content for the text document.
            source (str, optional): New source value.
            processed_status (bool, optional): New processed status.

        Returns:
            dict: {
                "success": True,
                "message": "Text document updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Document with specified ID must exist.
            - Only valid fields (content, source, processed_status) are updatable.
            - If no fields are provided for update, operation fails.
            - processed_status, if provided, must be boolean.
        """
        doc = self.documents.get(document_id)
        if doc is None:
            return {"success": False, "error": "Document does not exist."}

        updated = False

        if content is not None:
            if not isinstance(content, str):
                return {"success": False, "error": "content must be a string."}
            doc["content"] = content
            updated = True

        if source is not None:
            if not isinstance(source, str):
                return {"success": False, "error": "source must be a string."}
            doc["source"] = source
            updated = True

        if processed_status is not None:
            if not isinstance(processed_status, bool):
                return {"success": False, "error": "processed_status must be a boolean."}
            doc["processed_status"] = processed_status
            updated = True

        if not updated:
            return {"success": False, "error": "No valid update fields specified."}

        self.documents[document_id] = doc
        return {"success": True, "message": "Text document updated successfully."}

    def delete_text_document(self, document_id: str) -> dict:
        """
        Remove a text document from the system (hard delete).
        Also removes any theme assignments associated with the document.

        Args:
            document_id (str): The unique identifier of the text document to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Document deleted."
            }
            or
            {
                "success": False,
                "error": "Document not found."
            }

        Constraints:
            - Removes the document from the documents store.
            - Removes all theme assignments referencing this document.
            - If the document does not exist, fails gracefully.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document not found."}

        # Delete the document itself
        del self.documents[document_id]

        # Remove all theme assignments related to this document
        self.theme_assignments = [
            ta for ta in self.theme_assignments if ta["document_id"] != document_id
        ]

        return {"success": True, "message": "Document deleted."}


class TextAnalyticsSystem(BaseEnv):
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

    def get_theme_by_name(self, **kwargs):
        return self._call_inner_tool('get_theme_by_name', kwargs)

    def list_user_themes(self, **kwargs):
        return self._call_inner_tool('list_user_themes', kwargs)

    def get_theme_by_id(self, **kwargs):
        return self._call_inner_tool('get_theme_by_id', kwargs)

    def list_active_themes(self, **kwargs):
        return self._call_inner_tool('list_active_themes', kwargs)

    def get_theme_weight(self, **kwargs):
        return self._call_inner_tool('get_theme_weight', kwargs)

    def list_themes_by_status(self, **kwargs):
        return self._call_inner_tool('list_themes_by_status', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_permissions(self, **kwargs):
        return self._call_inner_tool('get_user_permissions', kwargs)

    def list_documents(self, **kwargs):
        return self._call_inner_tool('list_documents', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def list_theme_assignments_for_document(self, **kwargs):
        return self._call_inner_tool('list_theme_assignments_for_document', kwargs)

    def list_documents_by_theme(self, **kwargs):
        return self._call_inner_tool('list_documents_by_theme', kwargs)

    def check_theme_edit_permission(self, **kwargs):
        return self._call_inner_tool('check_theme_edit_permission', kwargs)

    def add_theme(self, **kwargs):
        return self._call_inner_tool('add_theme', kwargs)

    def update_theme(self, **kwargs):
        return self._call_inner_tool('update_theme', kwargs)

    def remove_theme(self, **kwargs):
        return self._call_inner_tool('remove_theme', kwargs)

    def set_theme_active_status(self, **kwargs):
        return self._call_inner_tool('set_theme_active_status', kwargs)

    def assign_theme_to_document(self, **kwargs):
        return self._call_inner_tool('assign_theme_to_document', kwargs)

    def update_theme_assignment_score(self, **kwargs):
        return self._call_inner_tool('update_theme_assignment_score', kwargs)

    def remove_theme_assignment(self, **kwargs):
        return self._call_inner_tool('remove_theme_assignment', kwargs)

    def add_text_document(self, **kwargs):
        return self._call_inner_tool('add_text_document', kwargs)

    def update_text_document(self, **kwargs):
        return self._call_inner_tool('update_text_document', kwargs)

    def delete_text_document(self, **kwargs):
        return self._call_inner_tool('delete_text_document', kwargs)
