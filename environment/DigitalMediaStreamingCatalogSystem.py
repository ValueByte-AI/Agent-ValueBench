# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class FormatInfo(TypedDict):
    format_id: str
    resolution: str  # e.g., SD, HD, 4K
    audio_languages: List[str]
    subtitle_languages: List[str]

class GenreInfo(TypedDict):
    genre_id: str
    name: str

class MediaItemInfo(TypedDict):
    media_id: str
    title: str
    type: str  # movie, series, episode, etc.
    genres: List[str]  # genre_ids
    formats: List[str]  # format_ids
    availability_status: str  # e.g., 'available', 'unavailable', 'expired'
    release_date: str
    description: str

class CatalogStateInfo(TypedDict):
    last_updated: str
    total_items: int
    current_offering: List[str]  # media_ids currently offered for viewing

class _GeneratedEnvImpl:
    def __init__(self):
        # Media items: {media_id: MediaItemInfo}
        self.media_items: Dict[str, MediaItemInfo] = {}

        # Formats: {format_id: FormatInfo}
        self.formats: Dict[str, FormatInfo] = {}

        # Genres: {genre_id: GenreInfo}
        self.genres: Dict[str, GenreInfo] = {}

        # Catalog state
        self.catalog_state: CatalogStateInfo = {
            "last_updated": "",
            "total_items": 0,
            "current_offering": []
        }
        
        # Constraints:
        # - Only items with availability_status = "available" are returned for viewing.
        # - Media items must be associated with at least one format describing their technical details.
        # - The catalog must not display items that are no longer licensed or currently unavailable.
        # - Filtering by resolution (e.g., HD) relies on the existence of a corresponding format in the item’s formats attribute.

    def list_available_media(self) -> dict:
        """
        Retrieve all media items with availability_status set to "available".

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MediaItemInfo]  # May be empty if no available items
                    }
        """
        available_items = [
            media_info for media_info in self.media_items.values()
            if media_info.get("availability_status") == "available"
        ]
        return {"success": True, "data": available_items}

    def list_media_by_type(self, media_type: str) -> dict:
        """
        Retrieve all available media items of a given type (e.g., movie, series, episode).

        Args:
            media_type (str): The media type to filter by ("movie", "series", etc).

        Returns:
            dict: {
                "success": True,
                "data": List[MediaItemInfo],  # List of available items of the specified type.
            }
            or
            {
                "success": False,
                "error": str  # Error message if type is invalid.
            }

        Constraints:
            - Only items with availability_status = "available" are returned.
            - Only items with at least one format (formats not empty) are included.
        """
        if not isinstance(media_type, str) or not media_type.strip():
            return { "success": False, "error": "Invalid media type" }
    
        result = [
            item for item in self.media_items.values()
            if item.get("type") == media_type
               and item.get("availability_status") == "available"
               and item.get("formats") and len(item.get("formats")) > 0
        ]

        return { "success": True, "data": result }

    def get_media_by_id(self, media_id: str) -> dict:
        """
        Retrieve metadata for a specific media item by its media_id.

        Args:
            media_id (str): The unique identifier for the desired media item.

        Returns:
            dict: {
                "success": True,
                "data": MediaItemInfo  # All metadata fields of the media item
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Media item not found"
            }

        Constraints:
            - Operation does not depend on availability_status; any item may be retrieved if it exists.
        """
        if media_id not in self.media_items:
            return { "success": False, "error": "Media item not found" }

        return { "success": True, "data": self.media_items[media_id] }

    def get_format_by_id(self, format_id: str) -> dict:
        """
        Retrieve format details by format_id.

        Args:
            format_id (str): The ID of the format to retrieve.

        Returns:
            dict:
                - If found: { "success": True, "data": FormatInfo }
                - If not found: { "success": False, "error": "Format not found" }

        Constraints:
            - Only retrieves information—no state is changed.
            - Returns error if format_id does not exist.
        """
        format_info = self.formats.get(format_id)
        if format_info is None:
            return { "success": False, "error": "Format not found" }
        return { "success": True, "data": format_info }

    def list_formats_for_media(self, media_id: str) -> dict:
        """
        List all formats (with detailed information) associated with a given media item.

        Args:
            media_id (str): The unique identifier of the media item.

        Returns:
            dict: {
                "success": True,
                "data": List[FormatInfo],  # List of associated formats (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error message if the media item does not exist
            }

        Constraints:
            - The media item specified by media_id must exist.
            - Format info is included only for formats that exist in the catalog.
        """
        media_item = self.media_items.get(media_id)
        if media_item is None:
            return {"success": False, "error": "Media item not found"}
    
        format_infos = []
        for fmt_id in media_item.get("formats", []):
            fmt_info = self.formats.get(fmt_id)
            if fmt_info is not None:
                format_infos.append(fmt_info)
        return {"success": True, "data": format_infos}

    def filter_media_by_format_resolution(self, resolution: str, media_ids: List[str] = None) -> dict:
        """
        Retrieve media items that have at least one format matching the desired resolution (e.g., 'HD').
        Filters from the provided list of media_ids if given, otherwise considers all items.
        Only includes items with availability_status 'available'.

        Args:
            resolution (str): Target resolution to filter by (case sensitive, e.g., 'HD', '4K').
            media_ids (List[str], optional): Restrict filtering to this set of media_ids; consider all if None.

        Returns:
            dict: {
                "success": True,
                "data": List[MediaItemInfo]  # List of media items passing the filter
            }
            OR
            {
                "success": False,
                "error": str  # Description if required parameters are missing or bad
            }
        Constraints:
            - Only includes items with availability_status 'available'.
            - Only includes media items with at least one format whose resolution matches.
            - Skips media_ids not present in system.
            - Skips media items with missing or corrupt formats.
        """
        if not isinstance(resolution, str) or not resolution.strip():
            return {"success": False, "error": "Resolution parameter is required and must be a string."}
    
        # Select media to check
        if media_ids is None:
            candidates = list(self.media_items.values())
        else:
            # Only consider media_ids present in the system
            candidates = [self.media_items[mid] for mid in media_ids if mid in self.media_items]
    
        filtered_media = []
        for media in candidates:
            if media.get("availability_status") != "available":
                continue  # only available items

            found_match = False
            for format_id in media.get("formats", []):
                fmt = self.formats.get(format_id)
                if not fmt:
                    continue  # skip missing formats
                if fmt.get("resolution") == resolution:
                    found_match = True
                    break
            if found_match:
                filtered_media.append(media)
    
        return {"success": True, "data": filtered_media}

    def list_media_by_genre(self, genre_id: str) -> dict:
        """
        Retrieve all available media items associated with a specified genre.

        Args:
            genre_id (str): The genre ID to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[MediaItemInfo],  # matching available media items
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only media with availability_status == "available" will be returned.
            - genre_id must exist in the catalog.
        """
        if genre_id not in self.genres:
            return {"success": False, "error": "Genre does not exist"}
        result = [
            item for item in self.media_items.values()
            if item["availability_status"] == "available" and genre_id in item["genres"]
        ]
        return {"success": True, "data": result}

    def get_genre_by_id(self, genre_id: str) -> dict:
        """
        Retrieve genre metadata by genre_id.

        Args:
            genre_id (str): The unique identifier of the genre to be retrieved.

        Returns:
            dict: 
                If found: { "success": True, "data": GenreInfo }
                If not found: { "success": False, "error": "Genre not found" }
        """
        genre = self.genres.get(genre_id)
        if genre is None:
            return { "success": False, "error": "Genre not found" }
        return { "success": True, "data": genre }

    def get_catalog_state(self) -> dict:
        """
        Return overall catalog statistics, including last_updated, total_items, and current_offering.

        Returns:
            dict: 
              {
                "success": True,
                "data": CatalogStateInfo  # Contains last_updated, total_items, current_offering
              }
              OR
              {
                "success": False,
                "error": str  # Description of error, if state is corrupted/unavailable
              }

        Constraints:
            - Read-only operation.
        """
        required_keys = {"last_updated", "total_items", "current_offering"}
        if not all(key in self.catalog_state for key in required_keys):
            return {
                "success": False,
                "error": "Catalog state is incomplete or corrupted."
            }
        return {
            "success": True,
            "data": self.catalog_state.copy()
        }

    def list_available_movies_by_resolution(self, resolution: str) -> dict:
        """
        Retrieve all available movies having at least one format with a matching resolution.

        Args:
            resolution (str): The desired format resolution (e.g., 'HD', '4K').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MediaItemInfo],  # Media items matching criteria
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Only include items with type='movie' and availability_status='available'.
            - At least one associated format must have resolution == specified.
            - Safely skip missing format_ids.
        """
        result = []
        for item in self.media_items.values():
            if item["type"] != "movie":
                continue
            if item["availability_status"] != "available":
                continue
            # Check if any of this item's formats match the resolution
            for format_id in item.get("formats", []):
                fmt = self.formats.get(format_id)
                if fmt and fmt.get("resolution") == resolution:
                    result.append(item)
                    break  # Only need one format match per media item

        return {"success": True, "data": result}

    def get_media_description(self, media_id: str) -> dict:
        """
        Get the title and description (summary) for a specific media item, only if it is currently available.

        Args:
            media_id (str): The unique identifier for the media item.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "title": str,
                            "description": str
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Only media items with availability_status == "available" can have their description fetched.
        """
        media_item = self.media_items.get(media_id)
        if media_item is None:
            return { "success": False, "error": "Media item not found" }
        if media_item["availability_status"] != "available":
            return { "success": False, "error": "Media item is not currently available" }
        return {
            "success": True,
            "data": {
                "title": media_item["title"],
                "description": media_item["description"]
            }
        }

    def update_media_availability(self, media_id: str, new_status: str) -> dict:
        """
        Change the availability_status of a media item.
    
        Args:
            media_id (str): The unique identifier of the media item.
            new_status (str): Target status ("available", "unavailable", "expired").
    
        Returns:
            dict: {
                "success": True,
                "message": "Availability status for media_id <media_id> updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - media_id must exist.
            - new_status must be 'available', 'unavailable', or 'expired'.
            - current_offering in catalog_state must reflect the updated availability.
        """
        if media_id not in self.media_items:
            return { "success": False, "error": "Media item not found." }
    
        allowed_statuses = {"available", "unavailable", "expired"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid new_status '{new_status}'. Allowed: {allowed_statuses}." }
    
        self.media_items[media_id]['availability_status'] = new_status
    
        # Maintain catalog_state.current_offering accordingly
        currently_offered = set(self.catalog_state.get('current_offering', []))
        if new_status == "available":
            if media_id not in currently_offered:
                currently_offered.add(media_id)
        else:
            if media_id in currently_offered:
                currently_offered.remove(media_id)
        self.catalog_state['current_offering'] = list(currently_offered)
    
        return {
            "success": True,
            "message": f"Availability status for media_id {media_id} updated to {new_status}."
        }

    def add_format_to_media(self, media_id: str, format_id: str) -> dict:
        """
        Associate a new format with a media item by adding format_id to its formats list.

        Args:
            media_id (str): The ID of the media item to update.
            format_id (str): The ID of the format to associate with the media item.

        Returns:
            dict: {
                "success": True,
                "message": "Format <format_id> added to media item <media_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - media_id must exist in the catalog.
            - format_id must exist in the formats catalog.
            - The format_id must not already be present in the media item's formats list.
        """
        if media_id not in self.media_items:
            return { "success": False, "error": f"Media item '{media_id}' does not exist." }
        if format_id not in self.formats:
            return { "success": False, "error": f"Format '{format_id}' does not exist." }

        media_item = self.media_items[media_id]
        if format_id in media_item["formats"]:
            return { "success": False, "error": f"Format '{format_id}' is already associated with media item '{media_id}'." }

        media_item["formats"].append(format_id)

        return { "success": True, "message": f"Format '{format_id}' added to media item '{media_id}'." }

    def remove_format_from_media(self, media_id: str, format_id: str) -> dict:
        """
        Remove an existing format from a media item's formats list.
    
        Args:
            media_id (str): ID of the target media item.
            format_id (str): ID of the format to remove.

        Returns:
            dict:
                Success: { "success": True, "message": "Format <format_id> removed from media item <media_id>." }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - media_id must exist in the catalog.
            - format_id must exist in the catalog.
            - format_id must be associated with the specified media item.
            - After removal, the media item must still have at least one format.
        """
        if media_id not in self.media_items:
            return { "success": False, "error": f"Media item '{media_id}' does not exist." }
        if format_id not in self.formats:
            return { "success": False, "error": f"Format '{format_id}' does not exist." }
    
        item = self.media_items[media_id]
        if format_id not in item["formats"]:
            return { "success": False, "error": f"Format '{format_id}' is not associated with media item '{media_id}'." }
        if len(item["formats"]) <= 1:
            return { "success": False, "error": "Media item must have at least one format. Cannot remove the only format." }
    
        item["formats"].remove(format_id)
        return { "success": True, "message": f"Format '{format_id}' removed from media item '{media_id}'." }

    def refresh_catalog_state(self) -> dict:
        """
        Updates the catalog state's last_updated timestamp, total_items, and current_offering list to reflect the current state.
    
        Process:
          - last_updated: Updated to the current system ISO timestamp.
          - total_items: Set to the total count of all media items.
          - current_offering: List of all media_ids where:
              - availability_status == "available"
              - formats list is not empty
    
        Returns:
            dict: {
                "success": True,
                "message": "Catalog state refreshed"
            }
        """

        # Update last_updated to current time in ISO format
        self.catalog_state["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # Update total_items
        self.catalog_state["total_items"] = len(self.media_items)

        # Update current_offering: only "available" items with non-empty formats list
        offering = []
        for mi in self.media_items.values():
            if mi["availability_status"] == "available" and mi["formats"]:
                offering.append(mi["media_id"])
        self.catalog_state["current_offering"] = offering

        return { "success": True, "message": "Catalog state refreshed" }

    def add_new_media_item(
        self,
        media_id: str,
        title: str,
        type: str,
        genres: list,
        formats: list,
        availability_status: str,
        release_date: str,
        description: str
    ) -> dict:
        """
        Add a new media item to the catalog with required metadata.

        Args:
            media_id (str): Unique identifier for the new media item.
            title (str): Title of the media item.
            type (str): Media type (e.g., 'movie', 'series', 'episode').
            genres (List[str]): List of genre_ids; all must exist in the catalog.
            formats (List[str]): List of format_ids; all must exist and list must be non-empty.
            availability_status (str): Availability status (e.g., 'available', 'unavailable', 'expired').
            release_date (str): Release date of the item.
            description (str): Media description.

        Returns:
            dict: 
                On success: {"success": True, "message": "Media item <media_id> added to catalog."}
                On failure: {"success": False, "error": "<error reason>"}

        Constraints:
            - media_id must be unique in catalog.
            - formats must exist and be non-empty (format_ids exist in catalog).
            - genres must exist (genre_ids exist in catalog).
            - Only accepts valid availability_status values.
        """

        # Check uniqueness
        if media_id in self.media_items:
            return {"success": False, "error": "Media ID already exists in the catalog."}

        # Validate formats
        if not formats or not isinstance(formats, list):
            return {"success": False, "error": "At least one valid format must be provided."}
        for fmt in formats:
            if fmt not in self.formats:
                return {"success": False, "error": f"Format ID '{fmt}' does not exist."}

        # Validate genres
        if not genres or not isinstance(genres, list):
            return {"success": False, "error": "At least one valid genre must be provided."}
        for genre in genres:
            if genre not in self.genres:
                return {"success": False, "error": f"Genre ID '{genre}' does not exist."}

        # Validate required metadata (simple checks)
        if not media_id or not title or not type or not release_date:
            return {"success": False, "error": "Missing required media metadata."}

        # Validate availability_status
        valid_status = {'available', 'unavailable', 'expired'}
        if availability_status not in valid_status:
            return {"success": False, "error": f"Invalid availability_status '{availability_status}'."}

        # Create new media item
        self.media_items[media_id] = {
            "media_id": media_id,
            "title": title,
            "type": type,
            "genres": genres,
            "formats": formats,
            "availability_status": availability_status,
            "release_date": release_date,
            "description": description,
        }
        # Update catalog state
        self.catalog_state["total_items"] += 1
        if availability_status == 'available':
            if media_id not in self.catalog_state["current_offering"]:
                self.catalog_state["current_offering"].append(media_id)
        # Not handling last_updated here (could be done with a timestamp if desired)

        return {"success": True, "message": f"Media item {media_id} added to catalog."}

    def update_media_metadata(
        self,
        media_id: str,
        title: str = None,
        description: str = None,
        genres: list = None,
        mtype: str = None,
        release_date: str = None,
    ) -> dict:
        """
        Update the metadata of a media item (by media_id) in the catalog.

        Args:
            media_id (str): The ID of the media item to update.
            title (str, optional): New title.
            description (str, optional): New description.
            genres (list[str], optional): New list of genre_ids.
            mtype (str, optional): New type (movie, series, episode, etc.).
            release_date (str, optional): New release date.

        Returns:
            dict:
                On success: { "success": True, "message": "Media item metadata updated." }
                On failure: { "success": False, "error": "Reason for failure" }

        Constraints:
            - media_id must exist in the catalog.
            - If genres is provided, all genre_ids must exist in self.genres.
            - At least one field to update must be provided.
        """
        # Check if media item exists
        item = self.media_items.get(media_id)
        if not item:
            return { "success": False, "error": "Media item not found." }

        fields_to_update = {}
        if title is not None:
            fields_to_update['title'] = title
        if description is not None:
            fields_to_update['description'] = description
        if genres is not None:
            if not isinstance(genres, list) or not all(isinstance(gid, str) for gid in genres):
                return { "success": False, "error": "Genres must be a list of genre_id strings." }
            # Verify that all genre_ids exist
            nonexistent = [gid for gid in genres if gid not in self.genres]
            if nonexistent:
                return { "success": False, "error": f"Genre IDs do not exist: {', '.join(nonexistent)}" }
            fields_to_update['genres'] = genres
        if mtype is not None:
            fields_to_update['type'] = mtype
        if release_date is not None:
            fields_to_update['release_date'] = release_date

        if not fields_to_update:
            return { "success": False, "error": "No fields provided to update." }

        # Update fields
        for k, v in fields_to_update.items():
            item[k] = v

        return { "success": True, "message": "Media item metadata updated." }

    def remove_media_item(self, media_id: str) -> dict:
        """
        Remove a media item with the given media_id from the catalog. Also updates
        catalog state to ensure no references linger and total_items is correct.

        Args:
            media_id (str): The unique identifier of the media item to remove.

        Returns:
            dict: 
              - On success:
                  {
                      "success": True,
                      "message": "Media item <media_id> has been removed from the catalog."
                  }
              - On error:
                  {
                      "success": False,
                      "error": "Media item not found."
                  }

        Constraints:
            - media_id must exist in self.media_items.
            - Removes from catalog_state.current_offering if present.
            - Updates catalog_state.total_items.
            - Does not affect formats or genres themselves.
        """
        if media_id not in self.media_items:
            return {"success": False, "error": "Media item not found."}
    
        # Remove from main item dictionary
        del self.media_items[media_id]
    
        # Remove from current offering if present
        if media_id in self.catalog_state["current_offering"]:
            self.catalog_state["current_offering"].remove(media_id)
    
        # Update total_items count
        self.catalog_state["total_items"] = len(self.media_items)
    
        return {
            "success": True,
            "message": f"Media item {media_id} has been removed from the catalog."
        }

    def add_new_format(
        self,
        format_id: str,
        resolution: str,
        audio_languages: list,
        subtitle_languages: list
    ) -> dict:
        """
        Add a new format to the formats registry for future media items.

        Args:
            format_id (str): Unique format identifier.
            resolution (str): Resolution (e.g., SD, HD, 4K).
            audio_languages (List[str]): Supported audio languages.
            subtitle_languages (List[str]): Supported subtitle languages.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Format <format_id> added." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - format_id must be unique.
            - All fields are required and must be of correct type.
        """
        if not isinstance(format_id, str) or not format_id:
            return { "success": False, "error": "format_id must be a non-empty string." }
        if not isinstance(resolution, str) or not resolution:
            return { "success": False, "error": "resolution must be a non-empty string." }
        if not isinstance(audio_languages, list) or not all(isinstance(lang, str) for lang in audio_languages):
            return { "success": False, "error": "audio_languages must be a list of strings." }
        if not isinstance(subtitle_languages, list) or not all(isinstance(lang, str) for lang in subtitle_languages):
            return { "success": False, "error": "subtitle_languages must be a list of strings." }
        if format_id in self.formats:
            return { "success": False, "error": "Format with this ID already exists." }

        self.formats[format_id] = {
            "format_id": format_id,
            "resolution": resolution,
            "audio_languages": audio_languages,
            "subtitle_languages": subtitle_languages
        }
        return { "success": True, "message": f"Format {format_id} added." }

    def update_format_info(
        self, 
        format_id: str, 
        resolution: str = None, 
        audio_languages: list = None, 
        subtitle_languages: list = None
    ) -> dict:
        """
        Change the details of an existing format (resolution, languages, etc.).

        Args:
            format_id (str): ID of the format to update.
            resolution (str, optional): New resolution value (e.g., SD, HD, 4K).
            audio_languages (List[str], optional): New list of audio languages.
            subtitle_languages (List[str], optional): New list of subtitle languages.

        Returns:
            dict: 
                { "success": True, "message": "Format info updated." }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - format_id must exist in the system.
            - Types for each field must match their specification.
        """
        # Check if the format exists
        if format_id not in self.formats:
            return { "success": False, "error": "Format ID does not exist." }
    
        fmt = self.formats[format_id]
        updated = False

        if resolution is not None:
            if not isinstance(resolution, str):
                return { "success": False, "error": "resolution must be a string." }
            fmt['resolution'] = resolution
            updated = True

        if audio_languages is not None:
            if not isinstance(audio_languages, list) or not all(isinstance(lang, str) for lang in audio_languages):
                return { "success": False, "error": "audio_languages must be a list of strings." }
            fmt['audio_languages'] = audio_languages
            updated = True

        if subtitle_languages is not None:
            if not isinstance(subtitle_languages, list) or not all(isinstance(lang, str) for lang in subtitle_languages):
                return { "success": False, "error": "subtitle_languages must be a list of strings." }
            fmt['subtitle_languages'] = subtitle_languages
            updated = True

        if not updated:
            return { "success": True, "message": "No changes made to format info." }

        self.formats[format_id] = fmt
        return { "success": True, "message": "Format info updated." }

    def add_new_genre(self, genre_id: str, name: str) -> dict:
        """
        Add a new genre to the genres registry.

        Args:
            genre_id (str): Unique identifier for the genre.
            name (str): Name of the genre.

        Returns:
            dict: {
                "success": True,
                "message": "Genre with id '<genre_id>' added."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - genre_id must not already exist.
            - genre_id and name must be non-empty (after stripping whitespace).
        """
        if not isinstance(genre_id, str) or not isinstance(name, str):
            return { "success": False, "error": "Invalid input types for genre_id or name" }
        genre_id = genre_id.strip()
        name = name.strip()
        if not genre_id:
            return { "success": False, "error": "Genre ID cannot be empty" }
        if not name:
            return { "success": False, "error": "Genre name cannot be empty" }
        if genre_id in self.genres:
            return { "success": False, "error": f"Genre ID '{genre_id}' already exists" }
    
        self.genres[genre_id] = {
            "genre_id": genre_id,
            "name": name
        }
        return { "success": True, "message": f"Genre with id '{genre_id}' added." }

    def update_genre_info(self, genre_id: str, name: str = None) -> dict:
        """
        Change the details (currently only name) of an existing genre.

        Args:
            genre_id (str): The identifier for the genre to update.
            name (str, optional): The updated name for the genre.

        Returns:
            dict: 
                { "success": True, "message": "Genre updated successfully." }
                OR
                { "success": False, "error": "Genre not found." }
                OR
                { "success": False, "error": "No update parameters provided." }

        Constraints:
            - The genre_id must exist.
            - If name is not provided, operation is a no-op/failure.
        """
        if genre_id not in self.genres:
            return { "success": False, "error": "Genre not found." }

        if name is None:
            return { "success": False, "error": "No update parameters provided." }

        # Update the name
        self.genres[genre_id]['name'] = name
        return { "success": True, "message": "Genre updated successfully." }


class DigitalMediaStreamingCatalogSystem(BaseEnv):
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

    def list_available_media(self, **kwargs):
        return self._call_inner_tool('list_available_media', kwargs)

    def list_media_by_type(self, **kwargs):
        return self._call_inner_tool('list_media_by_type', kwargs)

    def get_media_by_id(self, **kwargs):
        return self._call_inner_tool('get_media_by_id', kwargs)

    def get_format_by_id(self, **kwargs):
        return self._call_inner_tool('get_format_by_id', kwargs)

    def list_formats_for_media(self, **kwargs):
        return self._call_inner_tool('list_formats_for_media', kwargs)

    def filter_media_by_format_resolution(self, **kwargs):
        return self._call_inner_tool('filter_media_by_format_resolution', kwargs)

    def list_media_by_genre(self, **kwargs):
        return self._call_inner_tool('list_media_by_genre', kwargs)

    def get_genre_by_id(self, **kwargs):
        return self._call_inner_tool('get_genre_by_id', kwargs)

    def get_catalog_state(self, **kwargs):
        return self._call_inner_tool('get_catalog_state', kwargs)

    def list_available_movies_by_resolution(self, **kwargs):
        return self._call_inner_tool('list_available_movies_by_resolution', kwargs)

    def get_media_description(self, **kwargs):
        return self._call_inner_tool('get_media_description', kwargs)

    def update_media_availability(self, **kwargs):
        return self._call_inner_tool('update_media_availability', kwargs)

    def add_format_to_media(self, **kwargs):
        return self._call_inner_tool('add_format_to_media', kwargs)

    def remove_format_from_media(self, **kwargs):
        return self._call_inner_tool('remove_format_from_media', kwargs)

    def refresh_catalog_state(self, **kwargs):
        return self._call_inner_tool('refresh_catalog_state', kwargs)

    def add_new_media_item(self, **kwargs):
        return self._call_inner_tool('add_new_media_item', kwargs)

    def update_media_metadata(self, **kwargs):
        return self._call_inner_tool('update_media_metadata', kwargs)

    def remove_media_item(self, **kwargs):
        return self._call_inner_tool('remove_media_item', kwargs)

    def add_new_format(self, **kwargs):
        return self._call_inner_tool('add_new_format', kwargs)

    def update_format_info(self, **kwargs):
        return self._call_inner_tool('update_format_info', kwargs)

    def add_new_genre(self, **kwargs):
        return self._call_inner_tool('add_new_genre', kwargs)

    def update_genre_info(self, **kwargs):
        return self._call_inner_tool('update_genre_info', kwargs)

