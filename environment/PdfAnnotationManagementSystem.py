# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any
import datetime



# Document entity: document_id, name, file_path, upload_date
class DocumentInfo(TypedDict):
    document_id: str
    name: str
    file_path: str
    upload_date: str

# Page entity: document_id, page_number, page_id
class PageInfo(TypedDict):
    document_id: str
    page_number: int
    page_id: str

# Annotation entity: annotation_id, document_id, page_number, annotation_type, position, author, content, created_at, modified_at
class AnnotationInfo(TypedDict):
    annotation_id: str
    document_id: str
    page_number: int
    annotation_type: str
    position: Any  # More detail on position structure could be specified if known, else Any
    author: str
    content: str
    created_at: str
    modified_at: str

# User entity: user_id, name, email
class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing PDF documents, pages, annotations, and user metadata.
        """

        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # Pages: {page_id: PageInfo}
        self.pages: Dict[str, PageInfo] = {}

        # Annotations: {annotation_id: AnnotationInfo}
        self.annotations: Dict[str, AnnotationInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - An annotation must be uniquely tied to a specific document and page.
        # - Annotation positions must be valid within the bounds of the referenced page.
        # - Only defined annotation types (e.g., circle, highlight, comment) are permitted.
        # - No two annotations share the same annotation_id.
        # - Document and page identifiers must correspond to existing documents and pages.

    def get_document_by_name(self, name: str) -> dict:
        """
        Retrieve document metadata (including document_id) for a document by its name.

        Args:
            name (str): The name of the document to search for.

        Returns:
            dict:
                If document with given name found:
                    {
                        "success": True,
                        "data": DocumentInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Document not found"
                    }
        Constraints:
            - Returns the first document found with the given name.
            - Document names are assumed to be unique; if multiple exist, only the first is returned.
        """
        for doc in self.documents.values():
            if doc["name"] == name:
                return {"success": True, "data": doc}
        return {"success": False, "error": "Document not found"}

    def list_all_documents(self) -> dict:
        """
        List basic information for all documents in the system.

        Args:
            None

        Returns:
            dict:
                success (bool): True if retrieval is successful.
                data (List[DocumentInfo]): A list of document information dictionaries. Empty if no documents exist.
        """
        docs = list(self.documents.values())
        return {"success": True, "data": docs}

    def get_page_by_document_and_number(self, document_id: str, page_number: int) -> dict:
        """
        Retrieve the PageInfo (including page_id) given a document_id and page_number.

        Args:
            document_id (str): The unique identifier of the PDF document.
            page_number (int): The page number within the document.

        Returns:
            dict: {
                "success": True,
                "data": PageInfo,    # If the page exists.
            }
            or
            {
                "success": False,
                "error": str         # Error message such as "Page not found".
            }

        Constraints:
            - Document and page identifiers must correspond to existing documents and pages.
        """
        for page_info in self.pages.values():
            if page_info["document_id"] == document_id and page_info["page_number"] == page_number:
                return {"success": True, "data": page_info}
        return {"success": False, "error": "Page not found for the given document_id and page_number"}

    def list_pages_for_document(self, document_id: str) -> dict:
        """
        Retrieve all pages belonging to a specific document.

        Args:
            document_id (str): The unique identifier of the document.

        Returns:
            dict: {
                "success": True,
                "data": List[PageInfo]  # All pages for the specified document (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. document does not exist
            }

        Constraints:
            - document_id must correspond to an existing document.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        pages = [
            page_info for page_info in self.pages.values()
            if page_info["document_id"] == document_id
        ]
        return {"success": True, "data": pages}

    def list_annotations_by_document_and_page(self, document_id: str, page_number: int) -> dict:
        """
        Retrieve all annotations for a specified document and page.

        Args:
            document_id (str): The ID of the document.
            page_number (int): The page number within the document.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[AnnotationInfo] }
                - On failure (document or page missing):
                    { "success": False, "error": "<reason>" }

        Constraints:
            - document_id must exist in self.documents.
            - (document_id, page_number) must correspond to an existing page in self.pages.
        """
        # Check that the document exists
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist" }

        # Check if the page exists for the document_id and page_number
        page_exists = any(
            (page_info["document_id"] == document_id and page_info["page_number"] == page_number)
            for page_info in self.pages.values()
        )
        if not page_exists:
            return { "success": False, "error": "Page does not exist for this document" }

        # Find all annotations matching document_id and page_number
        result = [
            annotation for annotation in self.annotations.values()
            if annotation["document_id"] == document_id and annotation["page_number"] == page_number
        ]
        return { "success": True, "data": result }

    def filter_annotations_by_type(self, annotation_type: str) -> dict:
        """
        Filter all annotations in the system that match the specified annotation_type.

        Args:
            annotation_type (str): The type of annotation to filter for (e.g., "circle").

        Returns:
            dict: {
                "success": True,
                "data": List[AnnotationInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only defined annotation types are permitted. If the type is not defined, operation fails.
        """
        # Acquire the list of defined annotation types, using the built-in method if available
        if hasattr(self, "list_defined_annotation_types"):
            defined_types_result = self.list_defined_annotation_types()
            if not defined_types_result.get("success", False):
                return {"success": False, "error": "Unable to determine defined annotation types"}
            defined_types = defined_types_result.get("data", [])
        else:
            # Hardcode common example types, as fallback
            defined_types = ["circle", "highlight", "comment"]

        if annotation_type not in defined_types:
            return {"success": False, "error": "Annotation type not defined"}

        result = [
            annotation_info
            for annotation_info in self.annotations.values()
            if annotation_info["annotation_type"] == annotation_type
        ]
        return {"success": True, "data": result}

    def get_annotation_by_id(self, annotation_id: str) -> dict:
        """
        Retrieve the full metadata/details for a specific annotation by its annotation_id.

        Args:
            annotation_id (str): The unique identifier of the annotation to retrieve.

        Returns:
            dict:
                If annotation exists:
                    { "success": True, "data": AnnotationInfo }
                If not found:
                    { "success": False, "error": "Annotation not found" }
        Constraints:
            - annotation_id must exist in self.annotations.
        """
        annotation = self.annotations.get(annotation_id)
        if annotation is None:
            return { "success": False, "error": "Annotation not found" }
        return { "success": True, "data": annotation }

    def list_defined_annotation_types(self) -> dict:
        """
        Retrieve all permitted annotation types in the system.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[str]  # List of defined annotation types
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error (e.g., not configured)
                }

        Notes:
            - Only the defined annotation types (e.g., circle, highlight, comment) are valid in the system.
            - If enumeration is not available in system, the function returns commonly accepted defaults.
        """

        # Ideally: Defined types could be in system config; fallback to hardcoded if not set.
        # Example: self.annotation_types = ['circle', 'highlight', 'comment']
        annotation_types = getattr(self, 'annotation_types', None)
        if annotation_types is None:
            # Provide a default if not set
            annotation_types = ['circle', 'highlight', 'comment']

        if not isinstance(annotation_types, list) or not annotation_types:
            return {"success": False, "error": "No annotation types are defined in the system."}

        return {"success": True, "data": annotation_types}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info by user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User metadata if found
            }
            or
            {
                "success": False,
                "error": str      # Error message if not found
            }

        Constraints:
            - The user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User ID does not exist"}
        return {"success": True, "data": user}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info(s) by user name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict:
                - If at least one user is found with the provided name:
                    {"success": True, "data": List[UserInfo]}
                - If no user found:
                    {"success": False, "error": "User not found"}

        Notes:
            - Multiple users can share the same name; all matches will be returned in a list.
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info['name'] == name
        ]
        if matches:
            return {"success": True, "data": matches}
        else:
            return {"success": False, "error": "User not found"}

    def list_annotations_by_author(self, author_id: str) -> dict:
        """
        Retrieve all annotations created by a specified author (user).

        Args:
            author_id (str): The user_id of the author whose annotations are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[AnnotationInfo],  # All annotations with author == author_id (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If the specified author/user does not exist
            }

        Constraints:
            - The author_id must exist in the user registry.
            - Only annotations where annotation["author"] == author_id are returned.
        """
        if author_id not in self.users:
            return {"success": False, "error": "Author (user) not found"}

        results = [
            annotation for annotation in self.annotations.values()
            if annotation["author"] == author_id
        ]

        return {"success": True, "data": results}

    def add_annotation(
        self,
        annotation_id: str,
        document_id: str,
        page_number: int,
        annotation_type: str,
        position: any,
        author: str,
        content: str,
        created_at: str,
        modified_at: str
    ) -> dict:
        """
        Add a new annotation to a specific document and page, ensuring:
          - annotation_id is unique,
          - annotation_type is valid,
          - referenced document/page exist,
          - author exists,
          - (optionally) position is valid within page bounds.

        Args:
            annotation_id (str): Unique identifier for annotation.
            document_id (str): ID of the document.
            page_number (int): Page number within the document.
            annotation_type (str): Annotation type (must be defined/supported).
            position (Any): Position information (structure may vary).
            author (str): User ID of the authoring user.
            content (str): Annotation content.
            created_at (str): Creation timestamp.
            modified_at (str): Modification timestamp.

        Returns:
            dict: {
                "success": True,
                "message": "Annotation added successfully."
            }
            or
            {
                "success": False,
                "error": Reason for failure
            }

        Constraints:
            - annotation_id must be unique
            - document_id must exist
            - (document_id, page_number) must exist as a page
            - annotation_type must be defined
            - author must be a real user
            - (position should be valid if position spec is available)
        """
        # 1. Check unique annotation_id
        if annotation_id in self.annotations:
            return {"success": False, "error": "Annotation ID already exists."}
    
        # 2. Validate document_id
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist."}

        # 3. Validate (document_id, page_number) exists as a page
        page_found = None
        for page in self.pages.values():
            if page["document_id"] == document_id and page["page_number"] == page_number:
                page_found = page
                break
        if not page_found:
            return {"success": False, "error": "Specified page not found for document."}

        # 4. Validate annotation_type
        if hasattr(self, "list_defined_annotation_types"):
            type_result = self.list_defined_annotation_types()
            if type_result.get("success", False):
                allowed_types = type_result.get("data", [])
            else:
                allowed_types = []
        else:
            allowed_types = ["circle", "highlight", "comment"]  # fallback if method unavailable
        if annotation_type not in allowed_types:
            return {"success": False, "error": f"Annotation type '{annotation_type}' is not supported."}
    
        # 5. Validate author (user_id)
        if author not in self.users:
            return {"success": False, "error": "Author (user) does not exist."}
    
        # 6. Optionally, validate position (spec not available, so skipped here)
        # Here you could insert a stub or actual position validator

        # 7. Build annotation entry
        annotation_entry = {
            "annotation_id": annotation_id,
            "document_id": document_id,
            "page_number": page_number,
            "annotation_type": annotation_type,
            "position": position,
            "author": author,
            "content": content,
            "created_at": created_at,
            "modified_at": modified_at
        }
        # 8. Insert
        self.annotations[annotation_id] = annotation_entry
        return {"success": True, "message": "Annotation added successfully."}

    def remove_annotation(self, annotation_id: str) -> dict:
        """
        Delete an annotation entry given its annotation_id.

        Args:
            annotation_id (str): The unique identifier of the annotation to delete.

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "message": "Annotation <annotation_id> removed successfully"
                }
              - On failure: {
                    "success": False,
                    "error": "Annotation not found"
                }

        Constraints:
            - The annotation_id must exist in the system for deletion.
            - Annotation removal should not impact document/page integrity.
        """
        if annotation_id not in self.annotations:
            return { "success": False, "error": "Annotation not found" }

        del self.annotations[annotation_id]
        return { "success": True, "message": f"Annotation {annotation_id} removed successfully" }

    def modify_annotation(
        self,
        annotation_id: str,
        annotation_type: str = None,
        position: Any = None,
        content: str = None,
        author: str = None,
    ) -> dict:
        """
        Update fields ('annotation_type', 'position', 'content', 'author') of an existing annotation.
        Only provided (non-None) fields are updated.

        Args:
            annotation_id (str): The ID of the annotation to update.
            annotation_type (str, optional): New annotation type (must be allowed).
            position (Any, optional): New position (format should match system expectations).
            content (str, optional): New annotation content.
            author (str, optional): New author ID.

        Returns:
            dict: Success or failure message.
                On success: {"success": True, "message": "Annotation updated successfully"}
                On failure: {"success": False, "error": "reason"}

        Constraints:
            - 'annotation_id' must exist.
            - Only updates allowed fields (type, position, content, author).
            - If 'annotation_type' is provided, must be among allowed types.
            - Updates 'modified_at' timestamp to now on success.
        """

        if annotation_id not in self.annotations:
            return {"success": False, "error": "Annotation does not exist"}

        annotation = self.annotations[annotation_id]
        updated = False

        # Validate and update annotation_type if provided
        if annotation_type is not None:
            # We assume get list of types via list_defined_annotation_types operation
            allowed_types = set([
                "circle", "highlight", "comment"
            ])
            if hasattr(self, "list_defined_annotation_types"):
                type_res = self.list_defined_annotation_types()
                if type_res["success"]:
                    allowed_types = set(type_res["data"])
            if annotation_type not in allowed_types:
                return {"success": False, "error": "Invalid annotation type"}
            annotation["annotation_type"] = annotation_type
            updated = True

        # Validate and update position if provided
        if position is not None:
            # For now, accept any non-None position (since structure is unknown)
            # If further validation required, add here.
            annotation["position"] = position
            updated = True

        # Update content if provided
        if content is not None:
            annotation["content"] = content
            updated = True

        # Update author if provided (but check if user exists)
        if author is not None:
            if author not in self.users:
                return {"success": False, "error": "Author (user) does not exist"}
            annotation["author"] = author
            updated = True

        if not updated:
            return {"success": False, "error": "No updatable fields provided"}

        # Update modified_at
        annotation["modified_at"] = datetime.datetime.now().isoformat()

        self.annotations[annotation_id] = annotation
        return {"success": True, "message": "Annotation updated successfully"}

    def add_document(self, document_id: str, name: str, file_path: str, upload_date: str) -> dict:
        """
        Adds/registers a new PDF document in the system.

        Args:
            document_id (str): Unique identifier for the document.
            name (str): Name of the document.
            file_path (str): Path or URI to the PDF file.
            upload_date (str): Upload timestamp (ISO-8601 string recommended).

        Returns:
            dict: 
                On success: { "success": True, "message": "Document '<name>' added successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - document_id must be unique in the system.
            - All fields are required and must be non-empty strings.
        """
        # Input validation: required and non-empty fields
        if not all([document_id, name, file_path, upload_date]):
            return {
                "success": False,
                "error": "All fields (document_id, name, file_path, upload_date) are required and must not be empty."
            }

        # Constraint: document_id uniqueness
        if document_id in self.documents:
            return {
                "success": False,
                "error": f"Document with id '{document_id}' already exists."
            }

        doc_info = {
            "document_id": document_id,
            "name": name,
            "file_path": file_path,
            "upload_date": upload_date
        }
        self.documents[document_id] = doc_info

        return {
            "success": True,
            "message": f"Document '{name}' added successfully."
        }

    def remove_document(self, document_id: str, remove_associated: bool = True) -> dict:
        """
        Remove a document from the system.

        Args:
            document_id (str): The ID of the document to remove.
            remove_associated (bool): If True (default), remove all associated pages and annotations.
                If False, will error if associated pages or annotations exist.

        Returns:
            dict: {
                "success": True,
                "message": Description of what was removed
            }
            or
            {
                "success": False,
                "error": Error message
            }

        Constraints:
            - If remove_associated=False, refuse removal if pages or annotations reference the document.
            - If remove_associated=True, remove document, all its pages, and annotations for any of those pages.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        # Find associated pages and annotations
        associated_pages = [page_id for page_id, page in self.pages.items() if page["document_id"] == document_id]
        associated_annotations = [ann_id for ann_id, ann in self.annotations.items() if ann["document_id"] == document_id]

        if not remove_associated:
            if associated_pages or associated_annotations:
                return {
                    "success": False,
                    "error": (
                        "Cannot remove document: associated pages and/or annotations exist. "
                        "Set remove_associated=True to delete them as well."
                    )
                }

        # Remove annotations
        removed_annotations_count = 0
        for ann_id in associated_annotations:
            del self.annotations[ann_id]
            removed_annotations_count += 1

        # Remove pages
        removed_pages_count = 0
        for page_id in associated_pages:
            del self.pages[page_id]
            removed_pages_count += 1

        # Remove the document itself
        del self.documents[document_id]

        return {
            "success": True,
            "message": (
                f"Removed document '{document_id}'"
                + (f", {removed_pages_count} pages, and {removed_annotations_count} annotations" if remove_associated else "")
            )
        }

    def add_page(self, document_id: str, page_number: int, page_id: str) -> dict:
        """
        Add a new page entry for a given document.

        Args:
            document_id (str): The ID of the document to which this page belongs.
            page_number (int): The page number within the document.
            page_id (str): Unique identifier for the new page.

        Returns:
            dict: {
                "success": True,
                "message": "Page added successfully."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - The specified document_id must exist.
            - page_id must be unique (not already used in self.pages).
            - (document_id, page_number) combination must not already exist in self.pages.
        """
        # Check document exists
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist." }

        # Check page_id uniqueness
        if page_id in self.pages:
            return { "success": False, "error": "Page ID already exists." }

        # Check for duplicate (document_id, page_number)
        for page in self.pages.values():
            if page["document_id"] == document_id and page["page_number"] == page_number:
                return { "success": False, "error": "Page with this document_id and page_number already exists." }

        # Add Page
        self.pages[page_id] = {
            "document_id": document_id,
            "page_number": page_number,
            "page_id": page_id
        }

        return { "success": True, "message": "Page added successfully." }

    def remove_page(self, page_id: str, cascade_annotations: bool = False) -> dict:
        """
        Remove a page entry identified by page_id from the system.
        Optionally, remove all annotations on this page as well if cascade_annotations is True.

        Args:
            page_id (str): The unique page identifier.
            cascade_annotations (bool): Whether to remove all annotations on this page. Default: False.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Page <page_id> removed."
                          or
                        "message": "Page <page_id> and <N> annotations removed."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
    
        Constraints:
            - Page must exist.
            - If there are annotations on the page and cascade_annotations is False, do not remove and return error.
            - When removing, maintain annotation and page integrity (no annotation may exist for a non-existent page).
        """
        if page_id not in self.pages:
            return { "success": False, "error": "Page does not exist." }
    
        page_info = self.pages[page_id]
        document_id = page_info["document_id"]
        page_number = page_info["page_number"]

        # Find all annotation_ids on this page
        annotations_on_page = [
            annotation_id
            for annotation_id, ann in self.annotations.items()
            if ann["document_id"] == document_id and ann["page_number"] == page_number
        ]

        if annotations_on_page and not cascade_annotations:
            return {
                "success": False,
                "error": "Page has annotations. Use cascade_annotations=True to remove them along with the page."
            }

        # Remove annotations if cascade is enabled
        num_annotations_removed = 0
        if cascade_annotations:
            for annotation_id in annotations_on_page:
                del self.annotations[annotation_id]
                num_annotations_removed += 1

        # Remove the page itself
        del self.pages[page_id]

        if num_annotations_removed > 0:
            return {
                "success": True,
                "message": f"Page {page_id} and {num_annotations_removed} annotation(s) removed."
            }
        else:
            return {
                "success": True,
                "message": f"Page {page_id} removed."
            }

    def add_user(self, user_id: str, name: str, email: str) -> dict:
        """
        Register a new user in the system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): Full name of the user.
            email (str): Email address of the user.

        Returns:
            dict: {
                "success": True,
                "message": "User added successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - user_id must not already exist in the system.
            - All input fields must be non-empty.
        """
        # Validate non-empty fields
        if not user_id or not name or not email:
            return { "success": False, "error": "All fields (user_id, name, email) must be provided and non-empty." }

        # Check uniqueness
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists." }

        # Add user
        self.users[user_id] = {
            "user_id": user_id,
            "name": name,
            "email": email
        }

        return { "success": True, "message": "User added successfully." }

    def remove_user(self, user_id: str) -> dict:
        """
        Deletes a user from the system.

        Args:
            user_id (str): The unique ID of the user to remove.

        Returns:
            dict: 
              On success: { "success": True, "message": "User <user_id> removed." }
              On failure: { "success": False, "error": "User does not exist." }

        Constraints:
            - If user_id does not exist, operation fails.
            - No checks on downstream annotation references (removal always permitted).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        del self.users[user_id]
        return { "success": True, "message": f"User {user_id} removed." }


class PdfAnnotationManagementSystem(BaseEnv):
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
            if key == "list_defined_annotation_types":
                if isinstance(value, str):
                    parsed_types = [item.strip() for item in value.split(",") if item.strip()]
                elif isinstance(value, (list, tuple, set)):
                    parsed_types = [item for item in value if isinstance(item, str) and item.strip()]
                else:
                    parsed_types = []
                if parsed_types:
                    setattr(env, "annotation_types", parsed_types)
                continue
            if key == "annotations" and isinstance(value, dict):
                normalized_annotations = {}
                for annotation_key, annotation in value.items():
                    if isinstance(annotation, dict):
                        annotation_id = annotation.get("annotation_id") or annotation_key
                        normalized_annotations[annotation_id] = copy.deepcopy(annotation)
                    else:
                        normalized_annotations[annotation_key] = copy.deepcopy(annotation)
                setattr(env, key, normalized_annotations)
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

    def get_document_by_name(self, **kwargs):
        return self._call_inner_tool('get_document_by_name', kwargs)

    def list_all_documents(self, **kwargs):
        return self._call_inner_tool('list_all_documents', kwargs)

    def get_page_by_document_and_number(self, **kwargs):
        return self._call_inner_tool('get_page_by_document_and_number', kwargs)

    def list_pages_for_document(self, **kwargs):
        return self._call_inner_tool('list_pages_for_document', kwargs)

    def list_annotations_by_document_and_page(self, **kwargs):
        return self._call_inner_tool('list_annotations_by_document_and_page', kwargs)

    def filter_annotations_by_type(self, **kwargs):
        return self._call_inner_tool('filter_annotations_by_type', kwargs)

    def get_annotation_by_id(self, **kwargs):
        return self._call_inner_tool('get_annotation_by_id', kwargs)

    def list_defined_annotation_types(self, **kwargs):
        return self._call_inner_tool('list_defined_annotation_types', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_annotations_by_author(self, **kwargs):
        return self._call_inner_tool('list_annotations_by_author', kwargs)

    def add_annotation(self, **kwargs):
        return self._call_inner_tool('add_annotation', kwargs)

    def remove_annotation(self, **kwargs):
        return self._call_inner_tool('remove_annotation', kwargs)

    def modify_annotation(self, **kwargs):
        return self._call_inner_tool('modify_annotation', kwargs)

    def add_document(self, **kwargs):
        return self._call_inner_tool('add_document', kwargs)

    def remove_document(self, **kwargs):
        return self._call_inner_tool('remove_document', kwargs)

    def add_page(self, **kwargs):
        return self._call_inner_tool('add_page', kwargs)

    def remove_page(self, **kwargs):
        return self._call_inner_tool('remove_page', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def remove_user(self, **kwargs):
        return self._call_inner_tool('remove_user', kwargs)
