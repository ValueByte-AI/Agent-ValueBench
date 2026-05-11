# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class TagInfo(TypedDict):
    tag_id: str
    tag_name: str
    context_id: str

class ContextInfo(TypedDict):
    context_id: str
    context_name: str
    description: str

class ContentItemInfo(TypedDict):
    content_id: str
    title: str
    body: str
    metadata: dict

class ContentTagInfo(TypedDict):
    content_id: str
    tag_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Content Management System (CMS) with tag taxonomy.
        """

        # Tags: {tag_id: TagInfo}
        # Each tag belongs to exactly one context.
        self.tags: Dict[str, TagInfo] = {}

        # Contexts: {context_id: ContextInfo}
        # context_name must be unique.
        self.contexts: Dict[str, ContextInfo] = {}

        # Content Items: {content_id: ContentItemInfo}
        self.content_items: Dict[str, ContentItemInfo] = {}

        # ContentTags: List of content-tag associations (many-to-many)
        # Alternatively, could use mapping {content_id: List[tag_id]}
        self.content_tags: List[ContentTagInfo] = []

        # Constraints:
        # - Each tag must belong to exactly one context.
        # - tag_id is unique (tag_name unique within context is not enforced here).
        # - context_name must be unique.
        # - Only active/available tags should be returned in queries (add a field if supporting deactivation).

    def get_context_by_name(self, context_name: str) -> dict:
        """
        Retrieve the context information for a given unique context_name.

        Args:
            context_name (str): The unique name of the context.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": ContextInfo
                  }
                - On failure: {
                      "success": False,
                      "error": "Context name not found"
                  }

        Constraints:
            - Context names are unique.
        """
        for ctx in self.contexts.values():
            if ctx["context_name"] == context_name:
                return {"success": True, "data": ctx}
        return {"success": False, "error": "Context name not found"}

    def get_context_by_id(self, context_id: str) -> dict:
        """
        Retrieve context information by its unique context_id.

        Args:
            context_id (str): Unique identifier for the context.

        Returns:
            dict:
                - On success: {"success": True, "data": ContextInfo}
                - On error: {"success": False, "error": "Context not found"}

        Constraints:
            - context_id must exist in the environment's contexts.
        """
        context = self.contexts.get(context_id)
        if context is not None:
            return {"success": True, "data": context}
        else:
            return {"success": False, "error": "Context not found"}

    def list_all_contexts(self) -> dict:
        """
        Retrieve a list of all existing contexts.

        Returns:
            dict: {
                "success": True,
                "data": List[ContextInfo],  # List of all context metadata (may be empty)
            }
        """
        contexts_list = list(self.contexts.values())
        return {
            "success": True,
            "data": contexts_list
        }

    def list_tags_by_context_id(self, context_id: str) -> dict:
        """
        Retrieve all tags associated with the specified context_id.

        Args:
            context_id (str): The ID of the context whose tags will be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],  # List of tags (may be empty if no tags in this context)
            }
            or
            {
                "success": False,
                "error": str  # e.g. 'Context does not exist'
            }

        Constraints:
            - context_id must refer to an existing context (must be present in self.contexts).
        """
        if context_id not in self.contexts:
            return { "success": False, "error": "Context does not exist" }
    
        tags_in_context = [
            tag for tag in self.tags.values()
            if tag["context_id"] == context_id
        ]
        return { "success": True, "data": tags_in_context }

    def list_available_tags_by_context_name(self, context_name: str) -> dict:
        """
        Retrieve all active/available tags under a context specified by its name.

        Args:
            context_name (str): The unique name of the context to search for tags.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TagInfo]  # List of TagInfo, possibly empty
                }
                or
                {
                    "success": False,
                    "error": str  # Reason: context does not exist
                }

        Constraints:
            - context_name must exist (unique per environment definition).
            - Only tags explicitly marked as active/available should be returned (if using tag deactivation).
              Fallback: if no "active" field, assume tag is active.
        """
        # Find the context_id for the given context_name
        context_id = None
        for ctx in self.contexts.values():
            if ctx["context_name"] == context_name:
                context_id = ctx["context_id"]
                break
        if context_id is None:
            return {"success": False, "error": "Context with given name does not exist"}

        # Gather tags for this context_id that are active (or lack 'active' field)
        result = []
        for tag in self.tags.values():
            if tag["context_id"] != context_id:
                continue
            # Check 'active' field if present, or assume active if field not present
            if ("active" not in tag) or tag.get("active"):
                result.append(tag)

        return {"success": True, "data": result}

    def get_tag_by_id(self, tag_id: str) -> dict:
        """
        Retrieve tag info (including tag_name and context_id) given a tag_id.

        Args:
            tag_id (str): The identifier of the tag to retrieve.

        Returns:
            dict:
                - If successful: { "success": True, "data": TagInfo }
                - If the tag does not exist: { "success": False, "error": "Tag not found" }

        Constraints:
            - Tag must exist in the system.
            - (If supporting deactivation in the future: should only return if tag is active.)
        """
        tag = self.tags.get(tag_id)
        if tag is None:
            return { "success": False, "error": "Tag not found" }
        return { "success": True, "data": tag }

    def list_tags_by_tag_name(self, tag_name: str) -> dict:
        """
        Retrieve all tags matching the given tag_name (may be repeated in different contexts).

        Args:
            tag_name (str): The name of the tag to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],  # All tags with the given tag name (may be empty if none)
            }

        Constraints:
            - tag_name match is exact and case-sensitive.
            - If multiple tags have same name but are in different contexts, all are returned.
            - If supporting tag deactivation, only active tags should be returned
              (not applicable here since no such field).
        """
        matching_tags = [
            tag_info for tag_info in self.tags.values()
            if tag_info["tag_name"] == tag_name
        ]
        return {"success": True, "data": matching_tags}

    def list_all_available_tags(self) -> dict:
        """
        Retrieve a list of all tags in the system that are active/available.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],   # All active/available tags
            }
            or
            {
                "success": False,
                "error": str  # For unexpected internal failure
            }

        Constraints:
            - Only tags that are active/available should be returned.
            - If 'active' field is missing from tags, all are considered available.
        """
        try:
            available_tags = []
            for tag in self.tags.values():
                # If 'active' field exists, check it; otherwise, always include
                if "active" in tag:
                    if tag["active"]:
                        available_tags.append(tag)
                else:
                    available_tags.append(tag)
            return { "success": True, "data": available_tags }
        except Exception as e:
            return { "success": False, "error": f"Error listing available tags: {str(e)}" }

    def list_tags_by_content_id(self, content_id: str) -> dict:
        """
        Retrieve all tags (TagInfo) assigned to a given content item.

        Args:
            content_id (str): The ID of the content item.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[TagInfo] }
                      (List may be empty if no tags.)
                - On failure:
                    { "success": False, "error": str }

        Constraints:
            - content_id must exist in the CMS.
            - Only tags with valid tag_id in the system are returned.
        """
        if content_id not in self.content_items:
            return { "success": False, "error": "Content item does not exist" }

        tag_ids = [ct["tag_id"] for ct in self.content_tags if ct["content_id"] == content_id]
        result = [self.tags[tag_id] for tag_id in tag_ids if tag_id in self.tags]

        return { "success": True, "data": result }

    def get_content_by_id(self, content_id: str) -> dict:
        """
        Retrieve a content item's information by its content_id.

        Args:
            content_id (str): Unique identifier for the content item.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": ContentItemInfo,  # Information about the content item.
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason the content item could not be found.
                }

        Constraints:
            - content_id must exist in the environment's content_items.
        """
        content = self.content_items.get(content_id)
        if content is None:
            return {"success": False, "error": "Content item not found"}
        return {"success": True, "data": content}

    def list_content_by_tag_id(self, tag_id: str) -> dict:
        """
        Retrieve all content items associated with the given tag_id.

        Args:
            tag_id (str): The unique identifier for a tag.

        Returns:
            dict: {
                "success": True,
                "data": List[ContentItemInfo],  # List of content items linked to the tag (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. tag not found
            }

        Constraints:
            - tag_id must exist in the system.
            - Returns only content that is present in self.content_items.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag not found" }
    
        # Find all content_ids associated with this tag_id
        content_ids = [
            ct["content_id"] for ct in self.content_tags
            if ct["tag_id"] == tag_id
        ]

        # Collect all corresponding content items
        content_list = [
            self.content_items[cid] for cid in content_ids
            if cid in self.content_items
        ]

        return { "success": True, "data": content_list }

    def list_content_by_context_id(self, context_id: str) -> dict:
        """
        List all content items that are tagged with any tag in the specified context.

        Args:
            context_id (str): The context's unique identifier.

        Returns:
            dict: 
                - success: True and 'data': List[ContentItemInfo] if found (may be empty).
                - success: False and 'error' if the context does not exist.

        Constraints:
            - The given context_id must exist in the system.
            - If no tags exist in the context, or no content is tagged, return empty list.
        """
        if context_id not in self.contexts:
            return {"success": False, "error": "Context not found"}

        # Get all tag_ids in that context
        tag_ids = [tag["tag_id"] for tag in self.tags.values() if tag["context_id"] == context_id]
        if not tag_ids:
            return {"success": True, "data": []}

        # Get all content_ids that have at least one of these tags
        content_ids = set(
            ct["content_id"] for ct in self.content_tags if ct["tag_id"] in tag_ids
        )
        # Get the content items
        result = [
            self.content_items[c_id]
            for c_id in content_ids
            if c_id in self.content_items
        ]
        return {"success": True, "data": result}

    def add_context(self, context_id: str, context_name: str, description: str) -> dict:
        """
        Create a new context/category.
    
        Args:
            context_id (str): Unique identifier for the new context.
            context_name (str): Name for the new context (must be unique).
            description (str): Description of the context.

        Returns:
            dict:
              - On success: { "success": True, "message": "Context '<context_name>' added successfully." }
              - On failure (duplicate id or name): { "success": False, "error": <reason> }

        Constraints:
            - context_id must be unique among contexts.
            - context_name must be unique among contexts.
        """
        # Check uniqueness of context_id
        if context_id in self.contexts:
            return { "success": False, "error": "Context ID already exists" }
        # Check uniqueness of context_name
        for c in self.contexts.values():
            if c["context_name"] == context_name:
                return { "success": False, "error": "Context name already exists" }
        # Create new context
        context_info = {
            "context_id": context_id,
            "context_name": context_name,
            "description": description
        }
        self.contexts[context_id] = context_info
        return { "success": True, "message": f"Context '{context_name}' added successfully." }

    def update_context(self, context_id: str, context_name: str = None, description: str = None) -> dict:
        """
        Modify the name and/or description of an existing context.

        Args:
            context_id (str): The unique identifier for the target context.
            context_name (str, optional): New name for the context.
            description (str, optional): New description for the context.

        Returns:
            dict: On success:
                    { "success": True, "message": "Context updated successfully" }
                  On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - context_id must exist.
            - context_name (if provided) must be unique among all contexts.
            - At least one of context_name or description must be provided.
        """
        if context_id not in self.contexts:
            return {"success": False, "error": "Context does not exist"}

        if context_name is None and description is None:
            return {"success": False, "error": "No update parameters provided"}

        # Check uniqueness of context_name if being changed
        if context_name is not None:
            for cid, ctx in self.contexts.items():
                if cid != context_id and ctx["context_name"] == context_name:
                    return {"success": False, "error": "Context name must be unique"}

        # Perform updates
        if context_name is not None:
            self.contexts[context_id]["context_name"] = context_name
        if description is not None:
            self.contexts[context_id]["description"] = description

        return {"success": True, "message": "Context updated successfully"}

    def delete_context(self, context_id: str) -> dict:
        """
        Remove a context and all its associated tags. Also removes all ContentTag associations for those tags.
    
        Args:
            context_id (str): The identifier of the context to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Context and its tags deleted"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The context must exist.
            - All tags within the context will be deleted.
            - All content-tag associations for these tags will also be deleted.
        """
        # Check context existence
        if context_id not in self.contexts:
            return { "success": False, "error": "Context does not exist" }
    
        # Gather all tag_ids associated with this context
        tag_ids_to_delete = [tag_id for tag_id, tinfo in self.tags.items() if tinfo['context_id'] == context_id]

        # Remove those tags
        for tag_id in tag_ids_to_delete:
            if tag_id in self.tags:
                del self.tags[tag_id]
    
        # Remove content-tag associations for the deleted tags
        self.content_tags = [
            ct for ct in self.content_tags
            if ct['tag_id'] not in tag_ids_to_delete
        ]
    
        # Remove the context itself
        del self.contexts[context_id]
    
        return { "success": True, "message": "Context and its tags deleted" }

    def add_tag(self, tag_id: str, tag_name: str, context_id: str) -> dict:
        """
        Add a new tag under a specified context.

        Args:
            tag_id (str): Unique identifier for the new tag.
            tag_name (str): Name of the tag.
            context_id (str): The identifier of the context under which to add the tag.

        Returns:
            dict:
                - {"success": True, "message": "Tag <tag_id> added to context <context_id>."} on success.
                - {"success": False, "error": "..."} on failure.
        Constraints:
            - tag_id must be unique.
            - context_id must refer to an existing context.
            - Each tag must belong to exactly one context.
        """
        if not tag_id or not tag_name or not context_id:
            return {"success": False, "error": "tag_id, tag_name, and context_id must all be provided."}

        if context_id not in self.contexts:
            return {"success": False, "error": "Context does not exist."}

        if tag_id in self.tags:
            return {"success": False, "error": "Tag ID already exists."}

        # Add the new tag
        self.tags[tag_id] = {
            "tag_id": tag_id,
            "tag_name": tag_name,
            "context_id": context_id
        }

        return {
            "success": True,
            "message": f"Tag {tag_id} added to context {context_id}."
        }

    def update_tag(
        self,
        tag_id: str,
        tag_name: str = None,
        context_id: str = None,
        active: bool = None
    ) -> dict:
        """
        Modify a tag's name, context, or active/available status.

        Args:
            tag_id (str): The tag's unique identifier to update.
            tag_name (str, optional): New tag name (must be unique within the context).
            context_id (str, optional): New context ID for the tag.
            active (bool, optional): New availability status of the tag.

        Returns:
            dict: {
                "success": True,
                "message": "Tag updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - tag_id must exist
            - If context_id is given, it must exist in contexts
            - tag_name must be unique within its context (old or new, depending on context changed)
            - Only active/available tags are surfaced in queries (here we allow update)
        """

        # Ensure tag exists
        tag = self.tags.get(tag_id)
        if not tag:
            return {"success": False, "error": "Tag not found."}

        # Add 'active' to tag if missing (backwards compatibility)
        if "active" not in tag:
            tag["active"] = True

        # Prepare updated fields, use current if not provided
        new_tag_name = tag_name if tag_name is not None else tag["tag_name"]
        new_context_id = context_id if context_id is not None else tag["context_id"]

        # Validate context_id (if changed/provided)
        if context_id is not None and context_id not in self.contexts:
            return {"success": False, "error": "Provided context_id does not exist."}

        # Uniqueness check: tag name unique within its context
        for t in self.tags.values():
            if t is tag:
                continue  # skip self
            if (
                t.get("tag_name") == new_tag_name and
                t.get("context_id") == new_context_id
            ):
                return {
                    "success": False,
                    "error": "Tag name must be unique within the context."
                }

        # Apply updates
        tag["tag_name"] = new_tag_name
        tag["context_id"] = new_context_id
        if active is not None:
            tag["active"] = active

        return {
            "success": True,
            "message": "Tag updated successfully."
        }

    def delete_tag(self, tag_id: str) -> dict:
        """
        Remove a tag from the system by its tag_id. All content-tag associations involving
        this tag will also be removed.

        Args:
            tag_id (str): The unique identifier of the tag to delete.

        Returns:
            dict: 
              - { "success": True, "message": "Tag <tag_id> deleted." } on success.
              - { "success": False, "error": "Tag not found." } if tag does not exist.

        Constraints:
            - The tag must exist in the system.
            - All relationships (content_tags) involving this tag will be removed as well.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag not found." }

        # Remove the tag
        del self.tags[tag_id]

        # Remove all ContentTag associations involving this tag
        self.content_tags = [
            assoc for assoc in self.content_tags if assoc["tag_id"] != tag_id
        ]

        return { "success": True, "message": f"Tag {tag_id} deleted." }

    def activate_tag(self, tag_id: str) -> dict:
        """
        Set a tag's status to active/available.

        Args:
            tag_id (str): The unique identifier of the tag to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Tag <tag_id> activated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Tag must exist in the system.
            - Tag will have its 'active' status set to True (if the field is missing, it is added).
        """
        tag = self.tags.get(tag_id)
        if tag is None:
            return {"success": False, "error": "Tag with id '%s' does not exist." % tag_id}

        if "active" not in tag:
            tag["active"] = False

        if tag["active"]:
            return {"success": True, "message": f"Tag {tag_id} is already active."}

        tag["active"] = True
        self.tags[tag_id] = tag
        return {"success": True, "message": f"Tag {tag_id} activated."}

    def deactivate_tag(self, tag_id: str) -> dict:
        """
        Set a tag's status to inactive/unavailable.

        Args:
            tag_id (str): The ID of the tag to deactivate.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Tag {tag_id} has been deactivated" }
                On failure:
                    { "success": False, "error": "Tag not found" }
                    { "success": False, "error": "Tag is already inactive" }

        Constraints:
            - Tag must exist in the system.
            - If already inactive, return with informative error.
            - For backwards compatibility, if 'active' field is missing, assume tag is active.
        """
        tag = self.tags.get(tag_id)
        if not tag:
            return { "success": False, "error": "Tag not found" }
    
        # Ensure "active" field is present and default to True if missing
        if "active" not in tag:
            tag["active"] = True

        if tag["active"] is False:
            return { "success": False, "error": "Tag is already inactive" }
    
        tag["active"] = False
        return { "success": True, "message": f"Tag {tag_id} has been deactivated" }

    def add_content_item(self, content_id: str, title: str, body: str, metadata: dict) -> dict:
        """
        Create a new content item in the CMS.

        Args:
            content_id (str): Unique identifier for the content item.
            title (str): Title of the content item.
            body (str): Main content body.
            metadata (dict): Additional metadata information for the content item.

        Returns:
            dict: {
                "success": True,
                "message": "Content item created."
            }
            OR
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - content_id must be unique and not already exist in the system.
        """
        if content_id in self.content_items:
            return {"success": False, "error": "Content item with this ID already exists."}

        self.content_items[content_id] = {
            "content_id": content_id,
            "title": title,
            "body": body,
            "metadata": metadata if metadata is not None else {}
        }
        return {"success": True, "message": "Content item created."}

    def update_content_item(
        self,
        content_id: str,
        title: str = None,
        body: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Edit the properties (title, body, metadata) of an existing content item.

        Args:
            content_id (str): The ID of the content item to update.
            title (str, optional): New title (if provided).
            body (str, optional): New body (if provided).
            metadata (dict, optional): New metadata dictionary (if provided).

        Returns:
            dict:
                - "success": True and "message" on update
                - "success": False and "error" if content_id not found or invalid input

        Constraints:
            - content_id must refer to an existing content item.
            - If no fields are provided for update, still treat as a successful no-op.
            - Input types should match: title/body as string, metadata as dict when provided.
        """
        if content_id not in self.content_items:
            return {"success": False, "error": "Content item not found"}

        content = self.content_items[content_id]

        if title is not None:
            if not isinstance(title, str):
                return {"success": False, "error": "Title must be a string"}
            content["title"] = title

        if body is not None:
            if not isinstance(body, str):
                return {"success": False, "error": "Body must be a string"}
            content["body"] = body

        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "Metadata must be a dictionary"}
            content["metadata"] = metadata

        self.content_items[content_id] = content

        return {"success": True, "message": "Content item updated"}

    def delete_content_item(self, content_id: str) -> dict:
        """
        Remove a content item and its tag associations from the CMS.

        Args:
            content_id (str): The ID of the content item to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Content item <content_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Content item does not exist."
            }

        Constraints:
            - The specified content item must exist.
            - All tag associations (ContentTagInfo) for this content must also be removed.
        """
        if content_id not in self.content_items:
            return {"success": False, "error": "Content item does not exist."}

        # Remove the content item
        del self.content_items[content_id]
        # Remove any tag associations (ContentTagInfo) for this content_id
        self.content_tags = [
            ct for ct in self.content_tags if ct["content_id"] != content_id
        ]

        return {
            "success": True,
            "message": f"Content item {content_id} deleted successfully."
        }

    def add_tag_to_content(self, content_id: str, tag_id: str) -> dict:
        """
        Associate a tag with a content item.

        Args:
            content_id (str): The ID of the content item to tag.
            tag_id (str): The ID of the tag to associate.

        Returns:
            dict: 
                - On success:
                    {"success": True, "message": "Tag <tag_id> associated with content item <content_id>"}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - content_id must exist in content_items.
            - tag_id must exist in tags.
            - The (content_id, tag_id) association must not already exist.
        """
        # Check if content exists
        if content_id not in self.content_items:
            return { "success": False, "error": f"Content item '{content_id}' does not exist." }

        # Check if tag exists
        if tag_id not in self.tags:
            return { "success": False, "error": f"Tag '{tag_id}' does not exist." }

        # Check if association already exists
        for assoc in self.content_tags:
            if assoc['content_id'] == content_id and assoc['tag_id'] == tag_id:
                return { "success": False, "error": f"Tag '{tag_id}' is already associated with content item '{content_id}'." }

        # Add new ContentTag association
        self.content_tags.append({'content_id': content_id, 'tag_id': tag_id})

        return { 
            "success": True, 
            "message": f"Tag '{tag_id}' associated with content item '{content_id}'." 
        }

    def remove_tag_from_content(self, content_id: str, tag_id: str) -> dict:
        """
        Remove the association between a tag and a content item.

        Args:
            content_id (str): Identifier of the content item.
            tag_id (str): Identifier of the tag.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Tag <tag_id> removed from content <content_id>."}
                - On failure:
                    {"success": False, "error": "<error message>"}

        Constraints:
            - Both content_id and tag_id must exist.
            - The association must exist to be removed.
        """
        if content_id not in self.content_items or tag_id not in self.tags:
            return {"success": False, "error": "Content or tag does not exist."}

        found = False
        new_content_tags = []
        for assoc in self.content_tags:
            if assoc["content_id"] == content_id and assoc["tag_id"] == tag_id:
                found = True
                continue  # Exclude this association
            new_content_tags.append(assoc)

        if not found:
            return {
                "success": False,
                "error": f"Tag {tag_id} not associated with content {content_id}."
            }

        self.content_tags = new_content_tags
        return {
            "success": True,
            "message": f"Tag {tag_id} removed from content {content_id}."
        }


class CmsTagTaxonomyEnvironment(BaseEnv):
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

    def get_context_by_name(self, **kwargs):
        return self._call_inner_tool('get_context_by_name', kwargs)

    def get_context_by_id(self, **kwargs):
        return self._call_inner_tool('get_context_by_id', kwargs)

    def list_all_contexts(self, **kwargs):
        return self._call_inner_tool('list_all_contexts', kwargs)

    def list_tags_by_context_id(self, **kwargs):
        return self._call_inner_tool('list_tags_by_context_id', kwargs)

    def list_available_tags_by_context_name(self, **kwargs):
        return self._call_inner_tool('list_available_tags_by_context_name', kwargs)

    def get_tag_by_id(self, **kwargs):
        return self._call_inner_tool('get_tag_by_id', kwargs)

    def list_tags_by_tag_name(self, **kwargs):
        return self._call_inner_tool('list_tags_by_tag_name', kwargs)

    def list_all_available_tags(self, **kwargs):
        return self._call_inner_tool('list_all_available_tags', kwargs)

    def list_tags_by_content_id(self, **kwargs):
        return self._call_inner_tool('list_tags_by_content_id', kwargs)

    def get_content_by_id(self, **kwargs):
        return self._call_inner_tool('get_content_by_id', kwargs)

    def list_content_by_tag_id(self, **kwargs):
        return self._call_inner_tool('list_content_by_tag_id', kwargs)

    def list_content_by_context_id(self, **kwargs):
        return self._call_inner_tool('list_content_by_context_id', kwargs)

    def add_context(self, **kwargs):
        return self._call_inner_tool('add_context', kwargs)

    def update_context(self, **kwargs):
        return self._call_inner_tool('update_context', kwargs)

    def delete_context(self, **kwargs):
        return self._call_inner_tool('delete_context', kwargs)

    def add_tag(self, **kwargs):
        return self._call_inner_tool('add_tag', kwargs)

    def update_tag(self, **kwargs):
        return self._call_inner_tool('update_tag', kwargs)

    def delete_tag(self, **kwargs):
        return self._call_inner_tool('delete_tag', kwargs)

    def activate_tag(self, **kwargs):
        return self._call_inner_tool('activate_tag', kwargs)

    def deactivate_tag(self, **kwargs):
        return self._call_inner_tool('deactivate_tag', kwargs)

    def add_content_item(self, **kwargs):
        return self._call_inner_tool('add_content_item', kwargs)

    def update_content_item(self, **kwargs):
        return self._call_inner_tool('update_content_item', kwargs)

    def delete_content_item(self, **kwargs):
        return self._call_inner_tool('delete_content_item', kwargs)

    def add_tag_to_content(self, **kwargs):
        return self._call_inner_tool('add_tag_to_content', kwargs)

    def remove_tag_from_content(self, **kwargs):
        return self._call_inner_tool('remove_tag_from_content', kwargs)
