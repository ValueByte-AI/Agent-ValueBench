# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ArtistInfo(TypedDict):
    artist_id: str
    name: str
    biography: str
    birthdate: str    # ISO date string
    deathdate: str    # ISO date string (or empty if alive)
    nationality: str

class ArtworkInfo(TypedDict):
    artwork_id: str
    title: str
    year_created: int
    medium: str
    dimensions: str
    artist_id: str   # Must correspond to a valid ArtistInfo

class TagInfo(TypedDict):
    tag_id: str
    name: str
    description: str

class ArtworkTagInfo(TypedDict):
    artwork_id: str
    tag_id: str

class TagRelationshipInfo(TypedDict):
    source_tag_id: str
    target_tag_id: str
    relationship_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Artists: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}
        # Artworks: {artwork_id: ArtworkInfo}
        self.artworks: Dict[str, ArtworkInfo] = {}
        # Tags: {tag_id: TagInfo}
        self.tags: Dict[str, TagInfo] = {}
        # ArtworkTags: list of (artwork_id, tag_id)
        self.artwork_tags: List[ArtworkTagInfo] = []
        # TagRelationships: list of (source_tag_id, target_tag_id, relationship_type)
        self.tag_relationships: List[TagRelationshipInfo] = []

        # Constraints:
        # - Each artwork must be linked to a valid artist (artist_id in artists)
        # - Tag relationships must reference valid tags on both ends
        # - artist_id, artwork_id, and tag_id are unique in their respective dictionaries
        # - An artwork may have zero or more tags via artwork_tags
        # - Tags may relate to other tags in various ways (relationship_type)

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve the ArtistInfo object corresponding to the given artist_id.

        Args:
            artist_id (str): The unique identifier of the artist.

        Returns:
            dict: {
                "success": True,
                "data": ArtistInfo,
            }
            or
            {
                "success": False,
                "error": "Artist not found"
            }

        Constraints:
            - artist_id must exist in the system.
        """
        if not artist_id or artist_id not in self.artists:
            return {"success": False, "error": "Artist not found"}
        return {"success": True, "data": self.artists[artist_id]}

    def list_artworks_by_artist(self, artist_id: str) -> dict:
        """
        Retrieve all artworks created by the specified artist.

        Args:
            artist_id (str): The unique ID of the artist.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtworkInfo]  # List of artworks by the artist (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If the artist_id does not exist
            }

        Constraints:
            - artist_id must exist in the system.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist ID not found" }
    
        artworks = [
            artwork for artwork in self.artworks.values()
            if artwork["artist_id"] == artist_id
        ]
        return { "success": True, "data": artworks }

    def get_artwork_by_id(self, artwork_id: str) -> dict:
        """
        Retrieve the ArtworkInfo object for a given artwork_id.

        Args:
            artwork_id (str): The unique identifier of the artwork.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": ArtworkInfo
                    }
                - On failure (artwork not found):
                    {
                        "success": False,
                        "error": "Artwork not found"
                    }

        Constraints:
            - artwork_id must exist in the system.
        """
        if artwork_id in self.artworks:
            return {"success": True, "data": self.artworks[artwork_id]}
        else:
            return {"success": False, "error": "Artwork not found"}

    def list_tags_for_artwork(self, artwork_id: str) -> dict:
        """
        List all TagInfo objects assigned to a given artwork.

        Args:
            artwork_id (str): The artwork's unique identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TagInfo]  # All tags assigned to the artwork (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The artwork_id must exist in the system.
            - Tags attached to the artwork must exist in the tags dictionary.
        """
        if artwork_id not in self.artworks:
            return {"success": False, "error": "Artwork does not exist"}

        # Get tag_ids linked to this artwork
        tag_ids = [at["tag_id"] for at in self.artwork_tags if at["artwork_id"] == artwork_id]

        # Collect valid tags' info
        tags = [self.tags[tid] for tid in tag_ids if tid in self.tags]

        return {"success": True, "data": tags}

    def list_tags_for_artist(self, artist_id: str) -> dict:
        """
        List all TagInfo objects associated with any artwork created by the given artist_id.

        Args:
            artist_id (str): The unique identifier for the artist.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],  # List may be empty if the artist has no tagged artworks.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., artist not found.
            }

        Constraints:
            - artist_id must exist in the artists collection.
            - Returns only tags currently present in the tags collection.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Get all artworks created by this artist
        artwork_ids = [
            artwork["artwork_id"]
            for artwork in self.artworks.values()
            if artwork["artist_id"] == artist_id
        ]
        if not artwork_ids:
            return { "success": True, "data": [] }

        # Find all tag_ids linked to these artworks
        tag_ids = {
            at["tag_id"]
            for at in self.artwork_tags
            if at["artwork_id"] in artwork_ids
        }
        # Gather TagInfo objects for these tag_ids (filter out missing tags just in case)
        tags = [
            self.tags[tag_id]
            for tag_id in tag_ids
            if tag_id in self.tags
        ]
        return { "success": True, "data": tags }

    def get_tag_by_id(self, tag_id: str) -> dict:
        """
        Retrieve the TagInfo object for a given tag_id.

        Args:
            tag_id (str): The unique identifier for the tag.

        Returns:
            dict:
                - On success: {"success": True, "data": TagInfo}
                - On failure: {"success": False, "error": "Tag not found"}

        Constraints:
            - tag_id must exist in the tags dictionary.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag not found" }
        return { "success": True, "data": self.tags[tag_id] }

    def list_tag_relationships(self) -> dict:
        """
        Retrieve all tag-to-tag relationship records defined in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TagRelationshipInfo],  # All tag relationship objects; may be empty if none exist
            }

        Constraints:
            - Tag relationships are assumed to be valid (refer to valid tags on both ends).
            - No input error is possible.
        """
        return {
            "success": True,
            "data": list(self.tag_relationships)
        }

    def list_relationships_for_tag(self, tag_id: str) -> dict:
        """
        Retrieve all TagRelationshipInfo objects where the given tag_id is either the source or target.

        Args:
            tag_id (str): The ID of the tag to find relationships for.

        Returns:
            dict: {
                "success": True,
                "data": List[TagRelationshipInfo]  # May be empty if no relationships
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Tag does not exist"
            }

        Constraints:
            - tag_id must exist in self.tags.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist" }

        relationships = [
            rel for rel in self.tag_relationships
            if rel["source_tag_id"] == tag_id or rel["target_tag_id"] == tag_id
        ]

        return { "success": True, "data": relationships }

    def get_all_artists(self) -> dict:
        """
        List all artists in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo]  # All artist metadata; empty if none
            }
        Constraints:
            - No input parameters
            - Always succeeds, may return an empty list if no artists exist
        """
        artists_list = list(self.artists.values())
        return {"success": True, "data": artists_list}

    def get_all_artworks(self) -> dict:
        """
        List all ArtworkInfo objects currently in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtworkInfo],  # List of all artworks, may be empty if none exist
            }

        Constraints:
            - None. Returns all artworks present; empty list if no artworks are in the system.
        """
        return { "success": True, "data": list(self.artworks.values()) }

    def get_all_tags(self) -> dict:
        """
        List all TagInfo objects (all tags) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo]  # List of all tag info entries (possibly empty)
            }
        """
        all_tags = list(self.tags.values())
        return { "success": True, "data": all_tags }

    def add_artist(
        self,
        artist_id: str,
        name: str,
        biography: str,
        birthdate: str,
        deathdate: str,
        nationality: str
    ) -> dict:
        """
        Add a new artist to the system, enforcing uniqueness of artist_id.

        Args:
            artist_id (str): Unique identifier for the artist.
            name (str): The artist's full name.
            biography (str): Biographical information.
            birthdate (str): Birth date in ISO format (YYYY-MM-DD).
            deathdate (str): Death date in ISO format (empty string if alive).
            nationality (str): Nationality.

        Returns:
            dict: {
                "success": True,
                "message": "Artist added successfully."
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - artist_id must be unique across all artists in the system.
        """
        if artist_id in self.artists:
            return { "success": False, "error": "Artist ID already exists." }

        # Construct artist info
        artist_info: ArtistInfo = {
            "artist_id": artist_id,
            "name": name,
            "biography": biography,
            "birthdate": birthdate,
            "deathdate": deathdate,
            "nationality": nationality
        }
        self.artists[artist_id] = artist_info

        return { "success": True, "message": "Artist added successfully." }

    def update_artist(
        self,
        artist_id: str,
        name: str = None,
        biography: str = None,
        birthdate: str = None,
        deathdate: str = None,
        nationality: str = None,
    ) -> dict:
        """
        Update information for an existing artist.

        Args:
            artist_id (str): ID of the artist to update (must already exist).
            name (str, optional): New name of the artist.
            biography (str, optional): New biography.
            birthdate (str, optional): New birthdate (ISO string).
            deathdate (str, optional): New deathdate (ISO string or empty).
            nationality (str, optional): New nationality.

        Returns:
            dict: {
                "success": True,
                "message": "Artist updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - artist_id must exist and is immutable.
            - Only provided fields are updated; others left unchanged.
            - Unknown fields are ignored.
        """
        # Locate artist
        artist = self.artists.get(artist_id)
        if not artist:
            return { "success": False, "error": "Artist with specified ID does not exist" }

        updated = False
        if name is not None:
            artist["name"] = name
            updated = True
        if biography is not None:
            artist["biography"] = biography
            updated = True
        if birthdate is not None:
            artist["birthdate"] = birthdate
            updated = True
        if deathdate is not None:
            artist["deathdate"] = deathdate
            updated = True
        if nationality is not None:
            artist["nationality"] = nationality
            updated = True

        if not updated:
            return { "success": False, "error": "No updatable fields provided" }

        # No need to return artist data, just confirm update
        return { "success": True, "message": "Artist updated successfully" }

    def add_artwork(
        self,
        artwork_id: str,
        title: str,
        year_created: int,
        medium: str,
        dimensions: str,
        artist_id: str
    ) -> dict:
        """
        Adds a new artwork with the specified data, referencing a valid artist.

        Args:
            artwork_id (str): Unique ID of the new artwork.
            title (str): Title of the artwork.
            year_created (int): Year the artwork was created.
            medium (str): Medium of the artwork (e.g., 'oil on canvas').
            dimensions (str): Dimensions/size (e.g., '90x60 cm').
            artist_id (str): ID of the artist; must exist in the system.

        Returns:
            dict: {
                "success": True,
                "message": "Artwork <artwork_id> added."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The provided artwork_id must be unique system-wide.
            - artist_id must already be present in `self.artists`.
        """
        if artwork_id in self.artworks:
            return { "success": False, "error": "Artwork ID already exists" }
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist ID does not exist" }

        artwork_info: ArtworkInfo = {
            "artwork_id": artwork_id,
            "title": title,
            "year_created": year_created,
            "medium": medium,
            "dimensions": dimensions,
            "artist_id": artist_id
        }
        self.artworks[artwork_id] = artwork_info
        return { "success": True, "message": f"Artwork {artwork_id} added." }

    def update_artwork(
        self, 
        artwork_id: str,
        title: str = None,
        year_created: int = None,
        medium: str = None,
        dimensions: str = None,
        artist_id: str = None
    ) -> dict:
        """
        Update information for an existing artwork.
    
        Args:
            artwork_id (str): ID of the artwork to update.
            title (str, optional): New title (if provided).
            year_created (int, optional): New year_created (if provided).
            medium (str, optional): New medium (if provided).
            dimensions (str, optional): New dimensions (if provided).
            artist_id (str, optional): New artist_id (if provided). Must be a valid artist.
        
        Returns:
            dict: {
                "success": True,
                "message": "Artwork <ID> updated successfully"
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }
        Constraints:
            - Artwork must exist.
            - If artist_id is changed, it must correspond to an existing artist.
        """
        if artwork_id not in self.artworks:
            return { "success": False, "error": "Artwork does not exist" }
    
        updates = {}
        if title is not None:
            updates["title"] = title
        if year_created is not None:
            updates["year_created"] = year_created
        if medium is not None:
            updates["medium"] = medium
        if dimensions is not None:
            updates["dimensions"] = dimensions
        if artist_id is not None:
            if artist_id not in self.artists:
                return { "success": False, "error": "Artist does not exist" }
            updates["artist_id"] = artist_id

        if not updates:
            return { "success": True, "message": f"No updates provided for artwork {artwork_id}" }

        self.artworks[artwork_id].update(updates)
        return { "success": True, "message": f"Artwork {artwork_id} updated successfully" }

    def add_tag(self, tag_id: str, name: str, description: str) -> dict:
        """
        Add a new tag to the collection, enforcing uniqueness of tag_id.

        Args:
            tag_id (str): Unique identifier for the tag.
            name (str): Name of the tag.
            description (str): Description of the tag.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Tag <tag_id> added successfully." }
                - On failure: { "success": False, "error": "Tag ID already exists." }

        Constraints:
            - tag_id must be unique (not present in self.tags)
        """
        if tag_id in self.tags:
            return { "success": False, "error": "Tag ID already exists." }
        self.tags[tag_id] = {
            "tag_id": tag_id,
            "name": name,
            "description": description
        }
        return { "success": True, "message": f"Tag {tag_id} added successfully." }

    def update_tag(self, tag_id: str, name: str = None, description: str = None) -> dict:
        """
        Update tag information (name and/or description) given a tag ID.

        Args:
            tag_id (str): Unique identifier for the tag to update.
            name (str, optional): New name for the tag.
            description (str, optional): New description for the tag.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Tag <tag_id> updated successfully." }
                On failure:
                    { "success": False, "error": <error_message> }

        Constraints:
            - tag_id must exist in the system.
            - At least one of 'name' or 'description' must be provided.
        """
        tag = self.tags.get(tag_id)
        if tag is None:
            return {"success": False, "error": "Tag not found."}

        if name is None and description is None:
            return {"success": False, "error": "No update fields provided."}

        if name is not None:
            tag["name"] = name
        if description is not None:
            tag["description"] = description

        return {"success": True, "message": f"Tag {tag_id} updated successfully."}

    def assign_tag_to_artwork(self, artwork_id: str, tag_id: str) -> dict:
        """
        Link a tag to an artwork by creating an ArtworkTagInfo entry.

        Args:
            artwork_id (str): Unique identifier of the artwork.
            tag_id (str): Unique identifier of the tag.

        Returns:
            dict:
                - If success: { "success": True, "message": "Tag assigned to artwork." }
                - If failure (invalid artwork/tag, or relation exists): 
                  { "success": False, "error": <reason> }

        Constraints:
            - artwork_id must exist in the system.
            - tag_id must exist in the system.
            - The combination (artwork_id, tag_id) must not already exist.
        """
        if artwork_id not in self.artworks:
            return { "success": False, "error": "Artwork not found" }
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag not found" }
        for rel in self.artwork_tags:
            if rel["artwork_id"] == artwork_id and rel["tag_id"] == tag_id:
                return { "success": False, "error": "Tag is already assigned to this artwork" }
        self.artwork_tags.append({
            "artwork_id": artwork_id,
            "tag_id": tag_id
        })
        return { "success": True, "message": "Tag assigned to artwork." }

    def remove_tag_from_artwork(self, artwork_id: str, tag_id: str) -> dict:
        """
        Unlink (remove) a tag from an artwork.

        Args:
            artwork_id (str): ID of the artwork.
            tag_id (str): ID of the tag.

        Returns:
            dict: {
                "success": True,
                "message": "Tag removed from artwork"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Both artwork and tag must exist.
            - The tag must already be assigned to the artwork.
        """
        if artwork_id not in self.artworks:
            return {"success": False, "error": "Artwork does not exist"}
        if tag_id not in self.tags:
            return {"success": False, "error": "Tag does not exist"}

        found = False
        for i, at in enumerate(self.artwork_tags):
            if at['artwork_id'] == artwork_id and at['tag_id'] == tag_id:
                found = True
                del self.artwork_tags[i]
                return {"success": True, "message": "Tag removed from artwork"}
        if not found:
            return {"success": False, "error": "Tag is not assigned to artwork"}

    def add_tag_relationship(self, source_tag_id: str, target_tag_id: str, relationship_type: str) -> dict:
        """
        Create a new relationship between two tags.
    
        Args:
            source_tag_id (str): The unique ID of the source tag.
            target_tag_id (str): The unique ID of the target tag.
            relationship_type (str): The type of relationship (e.g., 'parent', 'synonym').
    
        Returns:
            dict: {
                "success": True,
                "message": "Tag relationship added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Both source_tag_id and target_tag_id must reference existing TagInfo entries.
            - The relationship (source_tag_id, target_tag_id, relationship_type) must not already exist.
            - source_tag_id and target_tag_id should be different.
        """
        if source_tag_id not in self.tags:
            return {"success": False, "error": "Source tag does not exist."}
        if target_tag_id not in self.tags:
            return {"success": False, "error": "Target tag does not exist."}
        if source_tag_id == target_tag_id:
            return {"success": False, "error": "Source and target tags must be different."}
        # Prevent duplicate relationships
        for rel in self.tag_relationships:
            if (
                rel["source_tag_id"] == source_tag_id and
                rel["target_tag_id"] == target_tag_id and
                rel["relationship_type"] == relationship_type
            ):
                return {"success": False, "error": "Tag relationship already exists."}
        # Create and add the tag relationship
        new_relationship = {
            "source_tag_id": source_tag_id,
            "target_tag_id": target_tag_id,
            "relationship_type": relationship_type
        }
        self.tag_relationships.append(new_relationship)
        return {"success": True, "message": "Tag relationship added successfully."}

    def remove_tag_relationship(self, source_tag_id: str, target_tag_id: str, relationship_type: str) -> dict:
        """
        Delete the tag relationship specified by source tag id, target tag id, and relationship type.

        Args:
            source_tag_id (str): ID of the source tag.
            target_tag_id (str): ID of the target tag.
            relationship_type (str): The type of relationship (e.g., "parent", "synonym").

        Returns:
            dict:
                - On success: { "success": True, "message": "Tag relationship removed successfully." }
                - On failure: { "success": False, "error": "Tag relationship not found." }

        Constraints:
            - Only removes the relationship if an exact match exists.
            - No error if the tag ids themselves do not exist (only cares about relationship entry).
        """
        found = False
        for i, rel in enumerate(self.tag_relationships):
            if (rel["source_tag_id"] == source_tag_id and
                rel["target_tag_id"] == target_tag_id and
                rel["relationship_type"] == relationship_type):
                found = True
                del self.tag_relationships[i]
                break

        if found:
            return { "success": True, "message": "Tag relationship removed successfully." }
        else:
            return { "success": False, "error": "Tag relationship not found." }

    def delete_artist(self, artist_id: str) -> dict:
        """
        Remove an artist from the system by artist_id.

        Args:
            artist_id (str): The unique identifier of the artist to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Artist <artist_id> deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The artist_id must exist.
            - No artwork can reference the artist_id after deletion (enforced: if artworks exist for artist, prevent deletion).
        """
        if artist_id not in self.artists:
            return {"success": False, "error": f"Artist '{artist_id}' does not exist."}
    
        # Check for artworks referencing this artist
        referenced_artworks = [
            artwork for artwork in self.artworks.values() if artwork["artist_id"] == artist_id
        ]
        if referenced_artworks:
            return {
                "success": False,
                "error": f"Cannot delete artist '{artist_id}': artworks exist for this artist."
            }

        # Safe to delete
        del self.artists[artist_id]
        return {"success": True, "message": f"Artist '{artist_id}' deleted."}

    def delete_artwork(self, artwork_id: str) -> dict:
        """
        Remove an artwork given its ID and all artwork-tag relationships (tags assigned to that artwork).

        Args:
            artwork_id (str): The unique identifier of the artwork to delete.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Artwork <artwork_id> and related tags deleted"}
                - On failure: {"success": False, "error": "Artwork does not exist"}

        Constraints:
            - The artwork must exist.
            - All artwork-tag references for the artwork should also be removed.
        """
        if artwork_id not in self.artworks:
            return {"success": False, "error": "Artwork does not exist"}

        # Remove the artwork
        del self.artworks[artwork_id]

        # Remove all related artwork-tag assignments
        original_count = len(self.artwork_tags)
        self.artwork_tags = [
            at for at in self.artwork_tags if at["artwork_id"] != artwork_id
        ]
        removed_count = original_count - len(self.artwork_tags)

        return {
            "success": True,
            "message": f"Artwork {artwork_id} and {removed_count} related tags deleted"
        }

    def delete_tag(self, tag_id: str) -> dict:
        """
        Remove a tag from the collection along with any associated tag relationships and artwork-tag assignments.

        Args:
            tag_id (str): Unique identifier of the tag to remove.

        Returns:
            dict:
              - On success:
                  { "success": True, "message": "Tag and associated relationships/artwork-tag assignments deleted." }
              - On failure:
                  { "success": False, "error": "<reason>" }
    
        Constraints:
          - Tag must exist.
          - Remove all relationships in which this tag is either source or target.
          - Remove all assignments of this tag to any artwork.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist." }
    
        # Remove the tag
        del self.tags[tag_id]

        # Remove all artwork-tag assignments involving this tag
        self.artwork_tags = [
            at for at in self.artwork_tags if at["tag_id"] != tag_id
        ]

        # Remove all tag relationships where this tag is source or target
        self.tag_relationships = [
            rel for rel in self.tag_relationships
            if rel["source_tag_id"] != tag_id and rel["target_tag_id"] != tag_id
        ]
    
        return {
            "success": True,
            "message": "Tag and associated relationships/artwork-tag assignments deleted."
        }


class ArtCollectionManagementSystem(BaseEnv):
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

    def get_artist_by_id(self, **kwargs):
        return self._call_inner_tool('get_artist_by_id', kwargs)

    def list_artworks_by_artist(self, **kwargs):
        return self._call_inner_tool('list_artworks_by_artist', kwargs)

    def get_artwork_by_id(self, **kwargs):
        return self._call_inner_tool('get_artwork_by_id', kwargs)

    def list_tags_for_artwork(self, **kwargs):
        return self._call_inner_tool('list_tags_for_artwork', kwargs)

    def list_tags_for_artist(self, **kwargs):
        return self._call_inner_tool('list_tags_for_artist', kwargs)

    def get_tag_by_id(self, **kwargs):
        return self._call_inner_tool('get_tag_by_id', kwargs)

    def list_tag_relationships(self, **kwargs):
        return self._call_inner_tool('list_tag_relationships', kwargs)

    def list_relationships_for_tag(self, **kwargs):
        return self._call_inner_tool('list_relationships_for_tag', kwargs)

    def get_all_artists(self, **kwargs):
        return self._call_inner_tool('get_all_artists', kwargs)

    def get_all_artworks(self, **kwargs):
        return self._call_inner_tool('get_all_artworks', kwargs)

    def get_all_tags(self, **kwargs):
        return self._call_inner_tool('get_all_tags', kwargs)

    def add_artist(self, **kwargs):
        return self._call_inner_tool('add_artist', kwargs)

    def update_artist(self, **kwargs):
        return self._call_inner_tool('update_artist', kwargs)

    def add_artwork(self, **kwargs):
        return self._call_inner_tool('add_artwork', kwargs)

    def update_artwork(self, **kwargs):
        return self._call_inner_tool('update_artwork', kwargs)

    def add_tag(self, **kwargs):
        return self._call_inner_tool('add_tag', kwargs)

    def update_tag(self, **kwargs):
        return self._call_inner_tool('update_tag', kwargs)

    def assign_tag_to_artwork(self, **kwargs):
        return self._call_inner_tool('assign_tag_to_artwork', kwargs)

    def remove_tag_from_artwork(self, **kwargs):
        return self._call_inner_tool('remove_tag_from_artwork', kwargs)

    def add_tag_relationship(self, **kwargs):
        return self._call_inner_tool('add_tag_relationship', kwargs)

    def remove_tag_relationship(self, **kwargs):
        return self._call_inner_tool('remove_tag_relationship', kwargs)

    def delete_artist(self, **kwargs):
        return self._call_inner_tool('delete_artist', kwargs)

    def delete_artwork(self, **kwargs):
        return self._call_inner_tool('delete_artwork', kwargs)

    def delete_tag(self, **kwargs):
        return self._call_inner_tool('delete_tag', kwargs)

