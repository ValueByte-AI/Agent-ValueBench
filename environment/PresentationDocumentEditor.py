# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict
import uuid
from typing import Any, Dict, Optional



class DocumentInfo(TypedDict):
    document_id: str
    name: str
    list_of_slide_ids: List[str]
    list_of_master_ids: List[str]
    metadata: Dict[str, Any]

class SlideInfo(TypedDict):
    slide_id: str
    document_id: str
    content_elements: Any  # could be List[Dict] or another suitable type
    applied_master_id: str
    slide_order: int
    metadata: Dict[str, Any]

class MasterSlideInfo(TypedDict):
    master_id: str
    document_id: str
    layout_definition: Any  # likely Dict or str, depends on format
    theme: Any  # likely Dict or str
    associated_slide_ids: List[str]
    metadata: Dict[str, Any]

class ResourceInfo(TypedDict):
    resource_id: str
    type: str
    data: Any  # raw data or reference, type depends on use-case
    associated_slide_ids: List[str]
    associated_master_ids: List[str]
    metadata: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Presentation Document Editor environment state.
        """
        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}
        # Slides: {slide_id: SlideInfo}
        self.slides: Dict[str, SlideInfo] = {}
        # Master Slides: {master_id: MasterSlideInfo}
        self.masters: Dict[str, MasterSlideInfo] = {}
        # Resources: {resource_id: ResourceInfo}
        self.resources: Dict[str, ResourceInfo] = {}

        # Constraints:
        # - Each slide must be associated with a single document.
        # - Each master slide must be associated with a single document.
        # - document.list_of_master_ids must reference valid masters.
        # - Document’s masters can be retrieved without loading slide content.

    def get_document_by_name(self, name: str) -> dict:
        """
        Retrieve a document's details by its name.

        Args:
            name (str): The exact name of the document to look up.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": DocumentInfo  # Document info dictionary if found
                }
                or
                {
                    "success": False,
                    "error": str  # Reason, e.g., document not found
                }

        Constraints:
            - Document name comparison is case-sensitive and must be exact.
            - If multiple documents have the same name (should not happen), the first found is returned.
        """
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid document name" }

        for document in self.documents.values():
            if document["name"] == name:
                return { "success": True, "data": document }

        return { "success": False, "error": "Document not found" }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve a document's details using its document_id.

        Args:
            document_id (str): The unique identifier of the document.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": DocumentInfo  # Whole info dict for the document
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Document not found"
                    }

        Constraints:
            - document_id must exist in the system.
        """
        doc = self.documents.get(document_id)
        if doc is None:
            return { "success": False, "error": "Document not found" }
        return { "success": True, "data": doc }

    def list_documents(self) -> dict:
        """
        Retrieve all presentation documents present in the environment.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[DocumentInfo],  # List of document info (may be empty if no documents)
                }

        This operation does not fail; if there are no documents, data is an empty list.
        """
        documents_list = list(self.documents.values())
        return { "success": True, "data": documents_list }

    def list_masters_for_document(self, document_id: str) -> dict:
        """
        Retrieve all master slides (MasterSlideInfo dicts) associated with a document, given its document_id.

        Args:
            document_id (str): The unique identifier of the document.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MasterSlideInfo],  # One per valid master referenced by the document
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason (e.g., document does not exist)
                    }

        Constraints:
            - The document must exist.
            - Only valid (existing in self.masters) master slides referenced by document are included.
        """
        doc = self.documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Document does not exist"}

        master_ids = doc.get("list_of_master_ids", [])
        masters_found = [
            self.masters[mid] for mid in master_ids if mid in self.masters
        ]

        return {"success": True, "data": masters_found}

    def get_master_slide_by_id(self, master_id: str) -> dict:
        """
        Retrieve a master slide's metadata/info given its master_id.

        Args:
            master_id (str): The unique identifier of the master slide to fetch.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": MasterSlideInfo
                }
                On failure: {
                    "success": False,
                    "error": "Master slide not found"
                }

        Constraints:
            - master_id must correspond to a known master slide.
        """
        if master_id not in self.masters:
            return { "success": False, "error": "Master slide not found" }
        return { "success": True, "data": self.masters[master_id] }

    def list_slides_for_document(self, document_id: str) -> dict:
        """
        Retrieve all slides (metadata) belonging to a document identified by document_id.

        Args:
            document_id (str): The ID of the document to query.

        Returns:
            dict: {
                "success": True,
                "data": List[SlideInfo]   # List of slides for the document (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., document does not exist)
            }

        Constraints:
            - The specified document_id must exist in the editor.
            - Only slides belonging to the document are included in the result.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        slides = [
            slide_info for slide_info in self.slides.values()
            if slide_info["document_id"] == document_id
        ]

        return {"success": True, "data": slides}

    def get_slide_by_id(self, slide_id: str) -> dict:
        """
        Retrieve a slide (with metadata and content) by its unique slide_id.

        Args:
            slide_id (str): The unique identifier of the slide.

        Returns:
            dict: {
                "success": True,
                "data": SlideInfo  # Slide information (including metadata and content)
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g., "Slide not found"
            }
    
        Constraints:
            - slide_id must exist in the editor's slides.
        """
        slide = self.slides.get(slide_id)
        if slide is None:
            return { "success": False, "error": "Slide not found" }
        return { "success": True, "data": slide }

    def list_resources_for_document(self, document_id: str) -> dict:
        """
        Retrieve all resources associated with any slide or master of a document.

        Args:
            document_id (str): The unique identifier of the document to query.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo],   # All resources associated (may be empty)
            }
            or
            {
                "success": False,
                "error": str,  # If document does not exist
            }

        Constraints:
            - The document must exist.
            - Resources are included if they are linked to at least one slide or master in the document.
            - Duplicate resources (associated to both a slide and master for the doc) are returned only once.
        """
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist" }

        # Gather all slide and master IDs for this document
        slide_ids = set(self.documents[document_id].get("list_of_slide_ids", []))
        master_ids = set(self.documents[document_id].get("list_of_master_ids", []))

        # Find all resources linked to any of these slides or masters
        result = []
        seen_resource_ids = set()
        for resource in self.resources.values():
            # Check slide association
            if any(sid in slide_ids for sid in resource.get("associated_slide_ids", [])):
                if resource["resource_id"] not in seen_resource_ids:
                    result.append(resource)
                    seen_resource_ids.add(resource["resource_id"])
                continue  # Don't need to check master_ids if already included

            # Check master association
            if any(mid in master_ids for mid in resource.get("associated_master_ids", [])):
                if resource["resource_id"] not in seen_resource_ids:
                    result.append(resource)
                    seen_resource_ids.add(resource["resource_id"])

        return { "success": True, "data": result }

    def get_resource_by_id(self, resource_id: str) -> dict:
        """
        Retrieve details about a resource by its resource_id.

        Args:
            resource_id (str): The unique identifier for the resource.

        Returns:
            dict: {
                "success": True,
                "data": ResourceInfo  # resource details
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Resource not found"
            }

        Constraints:
            - The resource must exist in the environment.
        """
        if resource_id not in self.resources:
            return {"success": False, "error": "Resource not found"}
        return {"success": True, "data": self.resources[resource_id]}

    def list_slides_for_master(self, master_id: str) -> dict:
        """
        Retrieve all slide IDs for slides that use the given master slide.

        Args:
            master_id (str): The ID of the master slide.

        Returns:
            dict: 
                - If found: { "success": True, "data": List[str] }
                - If master not found: { "success": False, "error": "Master slide does not exist" }

        Constraints:
            - The master_id must exist in the environment.
        """
        if master_id not in self.masters:
            return { "success": False, "error": "Master slide does not exist" }

        associated_slide_ids = self.masters[master_id].get("associated_slide_ids", [])
        return { "success": True, "data": list(associated_slide_ids) }

    def check_master_ids_valid_for_document(self, document_id: str) -> dict:
        """
        Check whether all master_ids referenced in a document are valid MasterSlide entities.

        Args:
            document_id (str): The ID of the document to check.

        Returns:
            dict:
                success: True/False
                data: {
                    "all_valid": bool,
                    "invalid_master_ids": List[str]
                }
                OR
                error: str (if document does not exist)

        Constraints:
            - The document must exist.
        """
        doc = self.documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Document not found"}

        master_ids = doc.get("list_of_master_ids", [])
        invalid_master_ids = [mid for mid in master_ids if mid not in self.masters]

        return {
            "success": True,
            "data": {
                "all_valid": len(invalid_master_ids) == 0,
                "invalid_master_ids": invalid_master_ids
            }
        }

    def get_slide_master(self, slide_id: str) -> dict:
        """
        Retrieve the master slide applied to the given slide.

        Args:
            slide_id (str): Identifier of the slide.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": MasterSlideInfo  # Master slide applied to the slide
                  }
                - On error: {
                      "success": False,
                      "error": str  # Description of the error
                  }

        Constraints:
            - The slide must exist.
            - The slide must have an applied_master_id that refers to a valid master slide.
        """
        slide = self.slides.get(slide_id)
        if not slide:
            return { "success": False, "error": "Slide does not exist." }
        applied_master_id = slide.get("applied_master_id")
        if not applied_master_id:
            return { "success": False, "error": "No master slide applied to this slide." }
        master = self.masters.get(applied_master_id)
        if not master:
            return { "success": False, "error": "Applied master slide does not exist." }
        return { "success": True, "data": master }

    def get_slide_order_in_document(self, document_id: str) -> dict:
        """
        Get the order/position for all slides in a specified document.
    
        Args:
            document_id (str): The id of the document whose slides' order is to be retrieved.
    
        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, Any]],  # [{"slide_id": str, "slide_order": int}, ...]
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., document does not exist)
            }
    
        Constraints:
            - document_id must exist.
            - Only slides referenced by the document and actually belonging to it are returned.
        """
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist" }

        # Get list of slide_ids for the document
        document = self.documents[document_id]
        result = []
        for slide_id in document.get("list_of_slide_ids", []):
            slide_info = self.slides.get(slide_id)
            # Check the slide actually belongs to the document (redundancy check for integrity)
            if slide_info and slide_info["document_id"] == document_id:
                result.append({
                    "slide_id": slide_id,
                    "slide_order": slide_info["slide_order"]
                })
        # Optionally, sort by slide_order
        result.sort(key=lambda x: x["slide_order"])
        return { "success": True, "data": result }

    def add_document(self, document_id: str, name: str, metadata: Dict[str, Any] = None) -> dict:
        """
        Create a new document in the editor.

        Args:
            document_id (str): Unique identifier for the new document.
            name (str): Name of the document.
            metadata (Dict[str, Any], optional): Optional metadata dictionary for the document.

        Returns:
            dict: {
                "success": True,
                "message": "Document added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., document_id conflict)
            }

        Constraints:
            - The document_id must be unique (not already present).
            - Masters/slides lists are initialized empty.
        """
        if document_id in self.documents:
            return { "success": False, "error": "Document with this ID already exists." }
    
        document_info = {
            "document_id": document_id,
            "name": name,
            "list_of_slide_ids": [],
            "list_of_master_ids": [],
            "metadata": metadata if metadata is not None else {}
        }
        self.documents[document_id] = document_info

        return { "success": True, "message": "Document added successfully." }

    def remove_document(self, document_id: str) -> dict:
        """
        Delete a document and all its associated slides, master slides, and resources.
        - Slides: Remove all slides belonging to the document.
        - Masters: Remove all master slides belonging to the document.
        - Resources: Remove associations with deleted slides/masters. 
          Delete the resource itself if it is not associated with any slides or masters afterwards.
    
        Args:
            document_id (str): ID of the document to remove.
    
        Returns:
            dict: {
                "success": True,
                "message": "Document and all associated data removed."
            }
            or
            {
                "success": False,
                "error": str
            }
        """

        # 1. Check document exists
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        # 2. Gather related slides and masters
        slide_ids_to_remove = [sid for sid, slide in self.slides.items() if slide["document_id"] == document_id]
        master_ids_to_remove = [mid for mid, master in self.masters.items() if master["document_id"] == document_id]

        # 3. Remove slides
        for sid in slide_ids_to_remove:
            self.slides.pop(sid, None)

        # 4. Remove masters
        for mid in master_ids_to_remove:
            self.masters.pop(mid, None)

        # 5. Remove references in resources
        resource_ids_to_delete = []
        for r_id, resource in list(self.resources.items()):
            # Remove slide/master ids associated with this document
            orig_slide_ids = resource.get("associated_slide_ids", [])
            orig_master_ids = resource.get("associated_master_ids", [])

            new_slide_ids = [sid for sid in orig_slide_ids if sid not in slide_ids_to_remove]
            new_master_ids = [mid for mid in orig_master_ids if mid not in master_ids_to_remove]
            resource["associated_slide_ids"] = new_slide_ids
            resource["associated_master_ids"] = new_master_ids

            # If resource is left unassociated, delete it
            if not new_slide_ids and not new_master_ids:
                resource_ids_to_delete.append(r_id)

        # Actually delete unreferenced resources
        for r_id in resource_ids_to_delete:
            self.resources.pop(r_id, None)

        # 6. Remove document itself
        self.documents.pop(document_id, None)

        return {
            "success": True,
            "message": "Document and all associated slides, masters, and resources removed."
        }


    def add_master_to_document(
        self,
        document_id: str,
        layout_definition: Any,
        theme: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Create a new master slide and associate it with a document.

        Args:
            document_id (str): ID of the document to add the master slide to.
            layout_definition (Any): The layout definition for the master slide.
            theme (Any): Theme data for the master slide.
            metadata (Optional[Dict[str, Any]]): Optional metadata for the master slide.

        Returns:
            dict: {
                "success": True,
                "message": "Master slide added to document",
                "master_id": <new_master_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The given document must exist.
            - The new master slide gets a unique master_id.
            - The document's list_of_master_ids is updated.
        """
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        new_master_id = str(uuid.uuid4())
        if new_master_id in self.masters:
            # Extremely rare, but check to avoid collision (regenerate once)
            new_master_id = str(uuid.uuid4())

        master_info = {
            "master_id": new_master_id,
            "document_id": document_id,
            "layout_definition": layout_definition,
            "theme": theme,
            "associated_slide_ids": [],
            "metadata": metadata if metadata is not None else {}
        }

        # Add to masters
        self.masters[new_master_id] = master_info

        # Update document's master id list
        doc = self.documents[document_id]
        if "list_of_master_ids" not in doc:
            doc["list_of_master_ids"] = []
        doc["list_of_master_ids"].append(new_master_id)

        return {
            "success": True,
            "message": "Master slide added to document",
            "master_id": new_master_id
        }

    def remove_master_from_document(self, document_id: str, master_id: str) -> dict:
        """
        Delete a master slide from the specified document and remove its association from all slides.
        Sets applied_master_id to "" on affected slides.

        Args:
            document_id (str): The ID of the document.
            master_id (str): The ID of the master slide to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Master slide removed from document, associations updated."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Document must exist.
            - Master must exist and belong to the document.
            - Master must be referenced in document's list_of_master_ids.
            - Affected slides must have their applied_master_id cleared.
            - Master is removed from self.masters and document's master list.
        """
        # Check document exists
        doc = self.documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Document does not exist."}
        # Check master exists
        master = self.masters.get(master_id)
        if not master:
            return {"success": False, "error": "Master slide does not exist."}
        # Ensure ownership
        if master["document_id"] != document_id:
            return {"success": False, "error": "Master does not belong to the specified document."}
        # Is the master currently listed for the document?
        if master_id not in doc["list_of_master_ids"]:
            return {"success": False, "error": "Master is not associated with the document."}
        # Remove master from document's master list
        doc["list_of_master_ids"] = [mid for mid in doc["list_of_master_ids"] if mid != master_id]
        self.documents[document_id] = doc  # update saved

        # Remove master assignment from all slides associated with this master and in this document
        for slide_id in master.get("associated_slide_ids", []):
            slide = self.slides.get(slide_id)
            if slide and slide["document_id"] == document_id and slide["applied_master_id"] == master_id:
                slide["applied_master_id"] = ""  # Or None if that's a better null value
                self.slides[slide_id] = slide  # update saved

        # Remove master from masters registry
        del self.masters[master_id]

        return {
            "success": True,
            "message": "Master slide removed from document, associations updated."
        }

    def update_master_slide(
        self,
        master_id: str,
        layout_definition: Any = None,
        theme: Any = None,
        metadata: dict = None
    ) -> dict:
        """
        Modify layout, theme, or metadata of an existing master slide.
    
        Args:
            master_id (str): The ID of the master slide to update.
            layout_definition (Any, optional): New layout definition to apply.
            theme (Any, optional): New theme to apply.
            metadata (dict, optional): New metadata dictionary to apply.

        Returns:
            dict: {
                "success": True,
                "message": "Master slide updated successfully."
            }
            or
            {
                "success": False,
                "error": "Master slide not found."
            }

        Constraints:
            - master_id must refer to an existing master slide.
            - Only supplied attributes are updated; unspecified ones are left unchanged.
            - If no updatable attributes are supplied, the call is a no-op (still success).
        """
        if master_id not in self.masters:
            return {"success": False, "error": "Master slide not found."}
    
        master = self.masters[master_id]
        changed = False

        if layout_definition is not None:
            master["layout_definition"] = layout_definition
            changed = True
        if theme is not None:
            master["theme"] = theme
            changed = True
        if metadata is not None:
            master["metadata"] = metadata
            changed = True

        msg = "Master slide updated successfully." if changed else "No fields updated (no-op)."
        return {"success": True, "message": msg}

    def add_slide_to_document(
        self,
        document_id: str,
        slide_id: str,
        content_elements: Any,
        applied_master_id: str,
        slide_order: int,
        metadata: dict = None
    ) -> dict:
        """
        Adds a new slide to the specified document at the given order, applying the specified master slide.

        Args:
            document_id (str): The target document ID.
            slide_id (str): The unique new slide ID.
            content_elements (Any): Slide content.
            applied_master_id (str): The master slide to apply (must belong to the document).
            slide_order (int): The (1-based) position for the new slide.
            metadata (dict): Optional slide metadata.

        Returns:
            dict: success True/False, message or error.
                On success: {
                    "success": True,
                    "message": "Slide <slide_id> added to document <document_id> at order <slide_order>."
                }
                On error: {
                    "success": False,
                    "error": "Reason"
                }

        Constraints:
            - document_id must exist.
            - slide_id must be unique.
            - applied_master_id must exist, and must belong to document_id.
            - slide_order must be in [1, len(list_of_slide_ids)+1]
        """
        # Check document exists
        if document_id not in self.documents:
            return { "success": False, "error": f"Document {document_id} does not exist." }

        # Check slide_id does not exist
        if slide_id in self.slides:
            return { "success": False, "error": f"Slide ID {slide_id} already exists." }

        document = self.documents[document_id]
        slide_ids = document["list_of_slide_ids"]

        # Check slide_order validity
        if not isinstance(slide_order, int) or slide_order < 1 or slide_order > len(slide_ids) + 1:
            return {
                "success": False,
                "error": (
                    f"Slide order {slide_order} is invalid. Must be between 1 and {len(slide_ids)+1} (inclusive)."
                )
            }

        # Check applied_master_id validity
        if applied_master_id not in self.masters:
            return { "success": False, "error": f"Applied master ID {applied_master_id} does not exist." }
        master_info = self.masters[applied_master_id]
        if master_info["document_id"] != document_id:
            return { "success": False, "error": f"Applied master does not belong to the document." }

        # Prepare slide metadata
        if metadata is None:
            metadata = {}

        # Reorder existing slides after the insertion point (increment their slide_order)
        for sid in slide_ids[slide_order-1:]:  # slides at and after the insert point
            self.slides[sid]["slide_order"] += 1

        # Build SlideInfo entry for the new slide
        new_slide_info = {
            "slide_id": slide_id,
            "document_id": document_id,
            "content_elements": content_elements,
            "applied_master_id": applied_master_id,
            "slide_order": slide_order,
            "metadata": metadata
        }
        self.slides[slide_id] = new_slide_info

        # Insert slide_id into the document's list_of_slide_ids at slide_order-1 (0-based index)
        slide_ids.insert(slide_order-1, slide_id)

        # Also add this slide to the master slide's associated_slide_ids
        if slide_id not in master_info["associated_slide_ids"]:
            master_info["associated_slide_ids"].append(slide_id)

        return {
            "success": True,
            "message": f"Slide {slide_id} added to document {document_id} at order {slide_order}."
        }

    def remove_slide_from_document(self, document_id: str, slide_id: str) -> dict:
        """
        Remove a slide from a document and update all relevant references.

        Args:
            document_id (str): The ID of the document.
            slide_id (str): The ID of the slide to remove.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success info
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - The document must exist.
            - The slide must exist and belong to the stated document.
            - Updates all references: master's associated_slide_ids, resource's associated_slide_ids, and removes slide.
        """
        # Check document existence
        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist."}
        doc = self.documents[document_id]

        # Check slide existence
        if slide_id not in self.slides:
            return {"success": False, "error": "Slide does not exist."}
        slide = self.slides[slide_id]

        # Validate slide belongs to document
        if slide["document_id"] != document_id:
            return {"success": False, "error": "Slide does not belong to provided document."}

        if slide_id not in doc["list_of_slide_ids"]:
            return {"success": False, "error": "Slide is not listed in the provided document."}

        # Remove slide from document's slide list
        doc["list_of_slide_ids"] = [
            sid for sid in doc["list_of_slide_ids"] if sid != slide_id
        ]

        # Remove slide from masters' associated_slide_ids
        for master in self.masters.values():
            if master["document_id"] == document_id:
                if slide_id in master["associated_slide_ids"]:
                    master["associated_slide_ids"] = [
                        sid for sid in master["associated_slide_ids"] if sid != slide_id
                    ]

        # Remove slide from all associated resource's associated_slide_ids
        for resource in self.resources.values():
            if slide_id in resource.get("associated_slide_ids", []):
                resource["associated_slide_ids"] = [
                    sid for sid in resource["associated_slide_ids"] if sid != slide_id
                ]

        # Delete the slide entry
        del self.slides[slide_id]

        return {
            "success": True,
            "message": f"Slide '{slide_id}' removed from document '{document_id}' and all references updated."
        }

    def update_slide_content(
        self, 
        slide_id: str, 
        new_content_elements: Any = None, 
        new_metadata: Dict[str, Any] = None
    ) -> dict:
        """
        Change the content elements and/or metadata of an existing slide.

        Args:
            slide_id (str): Identifier of the slide to update.
            new_content_elements (Any, optional): New value for content_elements; if None, content is unchanged.
            new_metadata (Dict[str, Any], optional): New metadata dictionary; if None, metadata is unchanged. An empty dict clears metadata; otherwise keys provided overwrite/update existing metadata and null values remove keys.

        Returns:
            dict: 
                On success: { "success": True, "message": "Slide content updated successfully" }
                On failure: { "success": False, "error": "Slide not found" }

        Constraints:
            - The slide must exist.
            - At least one of content or metadata must be provided for change.
        """
        if slide_id not in self.slides:
            return { "success": False, "error": "Slide not found" }

        updated = False
        slide_info = self.slides[slide_id]

        if new_content_elements is not None:
            slide_info["content_elements"] = new_content_elements
            updated = True

        if new_metadata is not None:
            if new_metadata == {}:
                slide_info["metadata"] = {}
            else:
                metadata = slide_info.setdefault("metadata", {})
                for key, value in new_metadata.items():
                    if value is None:
                        metadata.pop(key, None)
                    else:
                        metadata[key] = value
            updated = True

        if updated:
            self.slides[slide_id] = slide_info
            return { "success": True, "message": "Slide content updated successfully" }
        else:
            return { "success": True, "message": "No change to slide content or metadata" }

    def set_slide_master(self, slide_id: str, master_id: str) -> dict:
        """
        Assign or change the master slide for a specific slide.

        Args:
            slide_id (str): The identifier of the slide to update.
            master_id (str): The identifier of the master slide to assign.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message,
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., slide/master missing, or document mismatch)
            }

        Constraints:
            - Both slide and master must exist.
            - Slide and master must belong to the same document.
            - Slide association with masters must be updated consistently.
        """
        # Check slide
        slide = self.slides.get(slide_id)
        if not slide:
            return {"success": False, "error": "Slide not found"}

        # Check master
        master = self.masters.get(master_id)
        if not master:
            return {"success": False, "error": "Master slide not found"}

        # Check document consistency
        if slide["document_id"] != master["document_id"]:
            return {
                "success": False,
                "error": "Slide and master slide do not belong to the same document"
            }

        prev_master_id = slide.get("applied_master_id")
        # If already set correctly, nothing more to do except ensure associated lists are correct
        if prev_master_id == master_id:
            # Make sure the association exists
            if slide_id not in master["associated_slide_ids"]:
                master["associated_slide_ids"].append(slide_id)
            return {
                "success": True,
                "message": "Slide is already assigned to this master slide"
            }

        # Remove from previous master's associated_slide_ids (if needed)
        if prev_master_id and prev_master_id in self.masters:
            prev_master = self.masters[prev_master_id]
            if slide_id in prev_master["associated_slide_ids"]:
                prev_master["associated_slide_ids"].remove(slide_id)

        # Set the new master for the slide
        slide["applied_master_id"] = master_id

        # Add to new master's associated_slide_ids if not already present
        if slide_id not in master["associated_slide_ids"]:
            master["associated_slide_ids"].append(slide_id)

        return {
            "success": True,
            "message": f"Master slide {master_id} has been assigned to slide {slide_id}"
        }

    def reorder_slides_in_document(self, document_id: str, new_slide_order: list) -> dict:
        """
        Rearrange the order of slides within a document.

        Args:
            document_id (str): The ID of the document whose slides are to be reordered.
            new_slide_order (List[str]): List of slide IDs in the desired new order.

        Returns:
            dict: {
                "success": True,
                "message": "Slides reordered successfully"
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Document must exist.
            - All slide IDs in new_slide_order must belong to the document.
            - No extra, missing, or duplicate slide IDs.
            - Updates DocumentInfo.list_of_slide_ids and each SlideInfo.slide_order accordingly.
        """
        # Validate document existence
        doc_info = self.documents.get(document_id)
        if not doc_info:
            return {"success": False, "error": "Document does not exist"}

        original_ids = doc_info["list_of_slide_ids"]

        # Validate that new_slide_order is a permutation of the current list_of_slide_ids (no missing, no extra, no duplicates)
        if sorted(original_ids) != sorted(new_slide_order):
            return {
                "success": False,
                "error": "new_slide_order must contain exactly all slide IDs of the document with no extra/missing IDs"
            }

        # Validate all slide IDs belong to this document
        for sid in new_slide_order:
            slide_info = self.slides.get(sid)
            if not slide_info or slide_info["document_id"] != document_id:
                return {
                    "success": False,
                    "error": f"Invalid slide ID in new_slide_order: {sid} (missing or not part of the document)"
                }

        # Perform the reordering
        doc_info["list_of_slide_ids"] = new_slide_order.copy()  # Update order in Document

        # Update slide_order field in each SlideInfo
        for idx, sid in enumerate(new_slide_order):
            self.slides[sid]["slide_order"] = idx + 1

        return {"success": True, "message": "Slides reordered successfully"}

    def add_resource(
        self,
        resource_id: str,
        type: str,
        data: Any,
        associated_slide_ids: List[str],
        associated_master_ids: List[str],
        metadata: Dict[str, Any] = None
    ) -> dict:
        """
        Add a resource (e.g., image, text) to the environment and associate it with specific slides and/or master slides.

        Args:
            resource_id (str): Unique identifier for the new resource.
            type (str): The type of resource (e.g. 'image', 'text').
            data (Any): The data/content of the resource.
            associated_slide_ids (List[str]): List of slide IDs to associate with this resource.
            associated_master_ids (List[str]): List of master slide IDs to associate with this resource.
            metadata (Dict[str, Any], optional): Additional metadata for this resource.

        Returns:
            dict:
                On success:
                  {"success": True, "message": "Resource <resource_id> added and associated with slides and/or masters."}
                On failure:
                  {"success": False, "error": <reason>}

        Constraints:
            - resource_id must be unique.
            - All associated_slide_ids must exist in self.slides.
            - All associated_master_ids must exist in self.masters.
        """
        if resource_id in self.resources:
            return {"success": False, "error": f"Resource ID '{resource_id}' already exists."}

        invalid_slide_ids = [sid for sid in associated_slide_ids if sid not in self.slides]
        if invalid_slide_ids:
            return {"success": False, "error": f"Slide IDs do not exist: {invalid_slide_ids}"}

        invalid_master_ids = [mid for mid in associated_master_ids if mid not in self.masters]
        if invalid_master_ids:
            return {"success": False, "error": f"Master IDs do not exist: {invalid_master_ids}"}

        resource_info = {
            "resource_id": resource_id,
            "type": type,
            "data": data,
            "associated_slide_ids": associated_slide_ids.copy(),
            "associated_master_ids": associated_master_ids.copy(),
            "metadata": metadata if metadata is not None else {}
        }

        self.resources[resource_id] = resource_info

        assoc_msg = []
        if associated_slide_ids:
            assoc_msg.append(f"slides {associated_slide_ids}")
        if associated_master_ids:
            assoc_msg.append(f"masters {associated_master_ids}")
        assoc_str = " and ".join(assoc_msg) if assoc_msg else "none"

        return {
            "success": True,
            "message": f"Resource '{resource_id}' added and associated with {assoc_str}."
        }

    def remove_resource(self, resource_id: str) -> dict:
        """
        Delete a resource and remove its associations from all slides and master slides.

        Args:
            resource_id (str): The unique id of the resource to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Resource deleted and associations removed"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The resource must exist in self.resources.
            - Remove resource_id from any SlideInfo.associated_slide_ids and MasterSlideInfo.associated_master_ids.
            - Clean up all associations; do not leave dangling references.
        """
        # Check if resource exists
        resource = self.resources.get(resource_id)
        if not resource:
            return {"success": False, "error": "Resource does not exist"}

        # Remove reference from associated slides
        for slide_id in resource.get("associated_slide_ids", []):
            slide = self.slides.get(slide_id)
            if slide and "associated_slide_ids" in slide:
                if resource_id in slide["associated_slide_ids"]:
                    slide["associated_slide_ids"].remove(resource_id)

        # Remove reference from associated masters
        for master_id in resource.get("associated_master_ids", []):
            master = self.masters.get(master_id)
            if master and "associated_master_ids" in master:
                if resource_id in master["associated_master_ids"]:
                    master["associated_master_ids"].remove(resource_id)

        # Remove resource from resources dict
        del self.resources[resource_id]

        return {"success": True, "message": "Resource deleted and associations removed"}

    def associate_resource_with_slide(self, resource_id: str, slide_id: str) -> dict:
        """
        Link an existing resource to a slide.

        Args:
            resource_id (str): The ID of the resource to associate.
            slide_id (str): The ID of the slide to link to.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <resource_id> associated with slide <slide_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Both resource and slide must exist.
            - An association should not duplicate (operation is idempotent).
        """
        if resource_id not in self.resources:
            return {"success": False, "error": f"Resource {resource_id} does not exist."}
        if slide_id not in self.slides:
            return {"success": False, "error": f"Slide {slide_id} does not exist."}

        associated_slides = self.resources[resource_id].get("associated_slide_ids", [])
        if slide_id in associated_slides:
            return {"success": True, "message": f"Resource {resource_id} is already associated with slide {slide_id}."}

        associated_slides.append(slide_id)
        self.resources[resource_id]["associated_slide_ids"] = associated_slides

        return {"success": True, "message": f"Resource {resource_id} associated with slide {slide_id}."}

    def associate_resource_with_master(self, resource_id: str, master_id: str) -> dict:
        """
        Link an existing resource to a master slide.

        Args:
            resource_id (str): The ID of the resource to associate.
            master_id (str): The ID of the master slide to associate with.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <resource_id> associated with master slide <master_id>."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraint:
            - Both resource_id and master_id must exist.
            - Duplicate associations are ignored.
        """
        if resource_id not in self.resources:
            return {"success": False, "error": f"Resource {resource_id} does not exist."}
        if master_id not in self.masters:
            return {"success": False, "error": f"Master slide {master_id} does not exist."}

        resource = self.resources[resource_id]
        if master_id in resource["associated_master_ids"]:
            # Already associated, no change needed.
            return {
                "success": True,
                "message": f"Resource {resource_id} is already associated with master slide {master_id}."
            }

        resource["associated_master_ids"].append(master_id)
        return {
            "success": True,
            "message": f"Resource {resource_id} associated with master slide {master_id}."
        }


class PresentationDocumentEditor(BaseEnv):
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

    def get_document_by_name(self, **kwargs):
        return self._call_inner_tool('get_document_by_name', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def list_documents(self, **kwargs):
        return self._call_inner_tool('list_documents', kwargs)

    def list_masters_for_document(self, **kwargs):
        return self._call_inner_tool('list_masters_for_document', kwargs)

    def get_master_slide_by_id(self, **kwargs):
        return self._call_inner_tool('get_master_slide_by_id', kwargs)

    def list_slides_for_document(self, **kwargs):
        return self._call_inner_tool('list_slides_for_document', kwargs)

    def get_slide_by_id(self, **kwargs):
        return self._call_inner_tool('get_slide_by_id', kwargs)

    def list_resources_for_document(self, **kwargs):
        return self._call_inner_tool('list_resources_for_document', kwargs)

    def get_resource_by_id(self, **kwargs):
        return self._call_inner_tool('get_resource_by_id', kwargs)

    def list_slides_for_master(self, **kwargs):
        return self._call_inner_tool('list_slides_for_master', kwargs)

    def check_master_ids_valid_for_document(self, **kwargs):
        return self._call_inner_tool('check_master_ids_valid_for_document', kwargs)

    def get_slide_master(self, **kwargs):
        return self._call_inner_tool('get_slide_master', kwargs)

    def get_slide_order_in_document(self, **kwargs):
        return self._call_inner_tool('get_slide_order_in_document', kwargs)

    def add_document(self, **kwargs):
        return self._call_inner_tool('add_document', kwargs)

    def remove_document(self, **kwargs):
        return self._call_inner_tool('remove_document', kwargs)

    def add_master_to_document(self, **kwargs):
        return self._call_inner_tool('add_master_to_document', kwargs)

    def remove_master_from_document(self, **kwargs):
        return self._call_inner_tool('remove_master_from_document', kwargs)

    def update_master_slide(self, **kwargs):
        return self._call_inner_tool('update_master_slide', kwargs)

    def add_slide_to_document(self, **kwargs):
        return self._call_inner_tool('add_slide_to_document', kwargs)

    def remove_slide_from_document(self, **kwargs):
        return self._call_inner_tool('remove_slide_from_document', kwargs)

    def update_slide_content(self, **kwargs):
        return self._call_inner_tool('update_slide_content', kwargs)

    def set_slide_master(self, **kwargs):
        return self._call_inner_tool('set_slide_master', kwargs)

    def reorder_slides_in_document(self, **kwargs):
        return self._call_inner_tool('reorder_slides_in_document', kwargs)

    def add_resource(self, **kwargs):
        return self._call_inner_tool('add_resource', kwargs)

    def remove_resource(self, **kwargs):
        return self._call_inner_tool('remove_resource', kwargs)

    def associate_resource_with_slide(self, **kwargs):
        return self._call_inner_tool('associate_resource_with_slide', kwargs)

    def associate_resource_with_master(self, **kwargs):
        return self._call_inner_tool('associate_resource_with_master', kwargs)
