# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional



class ContactDetails(TypedDict, total=False):
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]

class ArtistInfo(TypedDict):
    artist_id: str
    name: str
    date_of_birth: str
    nationality: str
    biography: str
    contact_details: ContactDetails
    works: List[str]             # List of work_ids
    profile_pic: str             # URL or path

class WorkInfo(TypedDict):
    work_id: str
    artist_id: str
    title: str
    genre: str
    date_created: str
    description: str
    media_url: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Artists: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}

        # Works: {work_id: WorkInfo}
        self.works: Dict[str, WorkInfo] = {}

        # Constraints:
        # - Each artist has a unique artist_id
        # - Each work is associated with one artist (artist_id as foreign key)
        # - Deleting an artist may require handling associated works (cascade delete, orphaned records, or restrictions)
        # - Contact details must be stored securely and may have structure (see ContactDetails TypedDict)

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve the full profile information for a specific artist using artist_id.

        Args:
            artist_id (str): The unique ID of the artist to retrieve.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": ArtistInfo
                }
                On error: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - artist_id must exist in the database.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }
        return { "success": True, "data": artist }

    def search_artist_by_name(self, search_string: str) -> dict:
        """
        Retrieve list of artist profiles whose name matches or partially matches the search string.
        Partial matching is case-insensitive.

        Args:
            search_string (str): Substring to search for in artist names.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo],  # Full artist info dicts whose names match
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., invalid input type)
            }

        Constraints:
            - Name matching is case-insensitive and substring-based.
            - Returns empty list if no matches found.
            - Returns error if search_string is not a string.
        """
        if not isinstance(search_string, str):
            return { "success": False, "error": "Search string must be a string." }

        lower_search = search_string.strip().lower()
        result = [
            artist
            for artist in self.artists.values()
            if lower_search in artist["name"].lower()
        ]

        return { "success": True, "data": result }

    def list_all_artists(self) -> dict:
        """
        Retrieve all artists’ profiles currently in the database.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo],  # List may be empty if no artists present
            }
        """
        all_artists = list(self.artists.values())
        return { "success": True, "data": all_artists }

    def get_artist_contact_details(self, artist_id: str) -> dict:
        """
        Securely retrieve the contact details for an artist given their unique artist_id.

        Args:
            artist_id (str): The unique identifier of the artist.

        Returns:
            dict: {
                "success": True,
                "data": ContactDetails
            }
            or
            {
                "success": False,
                "error": "Artist not found"
            }

        Constraints:
            - The artist with given artist_id must exist.
            - Contact details are returned exactly as stored.
        """
        artist = self.artists.get(artist_id)
        if not artist:
            return {"success": False, "error": "Artist not found"}
        return {"success": True, "data": artist["contact_details"]}

    def get_works_by_artist_id(self, artist_id: str) -> dict:
        """
        Retrieve all works associated with a specific artist.

        Args:
            artist_id (str): Unique identifier for the artist.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[dict],  # List of work summaries, e.g., {work_id, title, genre, date_created}
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g., artist not found)
                }

        Constraints:
            - artist_id must exist in the database.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }
    
        # Retrieve all works where work["artist_id"] == artist_id
        works = [
            {
                "work_id": work["work_id"],
                "title": work["title"],
                "genre": work["genre"],
                "date_created": work["date_created"]
            }
            for work in self.works.values()
            if work["artist_id"] == artist_id
        ]

        return { "success": True, "data": works }

    def get_work_by_id(self, work_id: str) -> dict:
        """
        Retrieve all details for a specified work using `work_id`.

        Args:
            work_id (str): The unique identifier of the work.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": WorkInfo  # All fields for the work.
                }
                On failure:
                {
                    "success": False,
                    "error": "Work not found"
                }

        Constraints:
            - The work must exist in the database.
        """
        work = self.works.get(work_id)
        if not work:
            return { "success": False, "error": "Work not found" }
        return { "success": True, "data": work }

    def search_works_by_title(self, title_query: str) -> dict:
        """
        Search for works whose titles match or partially match the given query string (case-insensitive).

        Args:
            title_query (str): The string to search for within each work's title.

        Returns:
            dict: {
                "success": True,
                "data": List[WorkInfo],  # All works whose titles contain the query string
            }

        Notes:
            - Matching is performed case-insensitively.
            - If title_query is empty, all works are returned.
        """
        if not isinstance(title_query, str):
            return {
                "success": False,
                "error": "title_query must be a string"
            }

        query = title_query.strip().lower()
        # If query is empty, return all works (match all)
        if not query:
            result = list(self.works.values())
        else:
            result = [
                work for work in self.works.values()
                if query in work["title"].lower()
            ]

        return {
            "success": True,
            "data": result
        }

    def list_artist_works_detailed(self, artist_id: str) -> dict:
        """
        Retrieve a list of detailed WorkInfo for all works associated with the given artist.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict:
                "success": True, "data": List[WorkInfo]
                    - The list may be empty if the artist has no works.
                OR
                "success": False, "error": str
                    - e.g. "Artist not found"

        Constraints:
            - artist_id must exist in the database.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }
        # Retrieve all works for this artist
        works = [work for work in self.works.values() if work["artist_id"] == artist_id]
        return { "success": True, "data": works }

    def create_artist(
        self,
        artist_id: str,
        name: str,
        date_of_birth: str,
        nationality: str,
        biography: str,
        contact_details: Optional[dict] = None,
        profile_pic: str = ""
    ) -> dict:
        """
        Add a new artist to the database with provided profile information.

        Args:
            artist_id (str): Unique ID for the artist.
            name (str): Artist's full name.
            date_of_birth (str): Artist's birth date.
            nationality (str): Nationality of the artist.
            biography (str): Biographical text.
            contact_details (Optional[dict]): Contact information (may include email, phone, address).
            profile_pic (str): URL or path to artist's profile picture.

        Returns:
            dict:
                - On success: { "success": True, "message": "Artist created successfully." }
                - On failure: { "success": False, "error": "<error description>" }

        Constraints:
            - artist_id must be unique.
            - All required fields must be provided.
            - contact_details can be empty or partially filled.
        """
        required_fields = [artist_id, name, date_of_birth, nationality, biography]
        if any(field is None or (isinstance(field, str) and field.strip() == "") for field in required_fields):
            return {"success": False, "error": "Missing required artist profile information."}

        if artist_id in self.artists:
            return {"success": False, "error": "Artist with this artist_id already exists."}

        artist_info: ArtistInfo = {
            "artist_id": artist_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "nationality": nationality,
            "biography": biography,
            "contact_details": contact_details if contact_details is not None else {},
            "works": [],
            "profile_pic": profile_pic
        }

        self.artists[artist_id] = artist_info
        return {"success": True, "message": "Artist created successfully."}

    def update_artist(self, artist_id: str, updates: dict) -> dict:
        """
        Modify information for an existing artist, including biography, contact details, or other mutable fields.

        Args:
            artist_id (str): The unique ID of the artist to update.
            updates (dict): A dictionary of fields and their new values. Valid fields include:
                - name
                - date_of_birth
                - nationality
                - biography
                - contact_details (dict with keys email, phone, address)
                - profile_pic

        Returns:
            dict: {
                "success": True,
                "message": "Artist updated successfully."
            }
            or {
                "success": False,
                "error": str  # e.g., artist not found or invalid update fields
            }

        Constraints:
            - Cannot update artist_id.
            - Updates to contact_details must maintain structure.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found." }

        artist = self.artists[artist_id]
        allowed_fields = {"name", "date_of_birth", "nationality", "biography", "contact_details", "profile_pic"}

        # Check for invalid update keys
        for key in updates:
            if key not in allowed_fields:
                return { "success": False, "error": f"Invalid update field: {key}" }

        # Perform updates
        for key, value in updates.items():
            if key == "contact_details":
                if not isinstance(value, dict):
                    return { "success": False, "error": "contact_details must be a dictionary." }
                contact_allowed = {"email", "phone", "address"}
                # Only update valid keys in contact_details
                for ckey, cval in value.items():
                    if ckey in contact_allowed:
                        artist["contact_details"][ckey] = cval
                    else:
                        return { "success": False, "error": f"Invalid contact detail field: {ckey}" }
            else:
                artist[key] = value

        self.artists[artist_id] = artist
        return { "success": True, "message": "Artist updated successfully." }

    def delete_artist(self, artist_id: str) -> dict:
        """
        Remove an artist from the database.
        Restriction policy: Deletion only allowed if artist has no associated works.
        Handles referential integrity by prohibiting deletion if works exist.

        Args:
            artist_id (str): The unique identifier of the artist to delete.

        Returns:
            dict: {
                "success": True,
                "message": f"Artist {artist_id} deleted."
            }
            or
            {
                "success": False,
                "error": <description>
            }
        Constraints:
            - Artist must exist.
            - Artist can only be deleted if they have no associated works.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": "Artist does not exist."}

        # Check if artist has any associated works
        associated_works = [
            work_id for work_id, work in self.works.items()
            if work["artist_id"] == artist_id
        ]
        if associated_works:
            return {"success": False, "error": "Artist has associated works. Deletion not allowed."}

        # Delete artist
        del self.artists[artist_id]
        return {"success": True, "message": f"Artist {artist_id} deleted."}

    def update_artist_contact_details(self, artist_id: str, new_contact_details: ContactDetails) -> dict:
        """
        Securely update the contact details for an artist.

        Args:
            artist_id (str): Unique identifier of the artist whose contact details are to be updated.
            new_contact_details (ContactDetails): A dict possibly containing 'email', 'phone', and/or 'address' (all optional).
                                                  Fields not provided will remain unchanged.

        Returns:
            dict:
                - { "success": True, "message": "Contact details updated successfully." } on success
                - { "success": False, "error": <reason> } on error (e.g., artist not found)

        Constraints:
            - The artist must exist.
            - Only the fields 'email', 'phone', 'address' may be updated.
            - Partial updates are allowed.
        """
        allowed_fields = {"email", "phone", "address"}

        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found." }

        if not isinstance(new_contact_details, dict) or not any(k in allowed_fields for k in new_contact_details):
            return { "success": False, "error": "No valid contact detail fields provided." }

        artist = self.artists[artist_id]
        # Initialize contact_details if missing
        if "contact_details" not in artist or not isinstance(artist["contact_details"], dict):
            artist["contact_details"] = {}

        updated = False
        for field in allowed_fields:
            if field in new_contact_details:
                artist["contact_details"][field] = new_contact_details[field]
                updated = True

        if not updated:
            return { "success": False, "error": "No valid contact detail fields provided." }

        return { "success": True, "message": "Contact details updated successfully." }

    def create_work(
        self,
        work_id: str,
        artist_id: str,
        title: str,
        genre: str,
        date_created: str,
        description: str,
        media_url: str
    ) -> dict:
        """
        Add a new work to the database, linked to a specified artist.

        Args:
            work_id (str): Unique identifier for the work.
            artist_id (str): Existing artist's unique identifier to link this work.
            title (str)
            genre (str)
            date_created (str)
            description (str)
            media_url (str)

        Returns:
            dict: {
                "success": True,
                "message": "Work <work_id> created and linked to artist <artist_id>."
            }
            or
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - work_id must be unique in the database
            - artist_id must exist
            - The new work_id will be appended to artist's 'works' list
        """
        if work_id in self.works:
            return { "success": False, "error": f"Work with id '{work_id}' already exists." }
        if artist_id not in self.artists:
            return { "success": False, "error": f"Artist with id '{artist_id}' does not exist." }

        # Create WorkInfo dict
        new_work = {
            "work_id": work_id,
            "artist_id": artist_id,
            "title": title,
            "genre": genre,
            "date_created": date_created,
            "description": description,
            "media_url": media_url
        }
        self.works[work_id] = new_work

        # Link the new work to the artist's works list
        if "works" not in self.artists[artist_id]:
            self.artists[artist_id]["works"] = []
        self.artists[artist_id]["works"].append(work_id)

        return { "success": True, "message": f"Work '{work_id}' created and linked to artist '{artist_id}'." }

    def update_work(
        self,
        work_id: str,
        title: str = None,
        genre: str = None,
        date_created: str = None,
        description: str = None,
        media_url: str = None
    ) -> dict:
        """
        Modify the details of an existing work.

        Args:
            work_id (str): The unique identifier for the existing work.
            title (str, optional): New title for the work.
            genre (str, optional): New genre/category.
            date_created (str, optional): New creation date.
            description (str, optional): New description.
            media_url (str, optional): New media URL/location.

        Returns:
            dict: {
                "success": True,
                "message": "Work updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The work must exist.
            - Only the provided (non-None) allowed fields will be changed.
            - Do not allow changing artist_id with this operation.
            - At least one updatable field must be provided.
        """
        if work_id not in self.works:
            return {"success": False, "error": "Work does not exist"}

        updatable_fields = {
            "title": title,
            "genre": genre,
            "date_created": date_created,
            "description": description,
            "media_url": media_url
        }

        # Filter to only fields the user wants to update (not None)
        fields_to_update = {k: v for k, v in updatable_fields.items() if v is not None}

        if not fields_to_update:
            return {"success": False, "error": "No updatable fields provided"}

        # Update the work info
        for field, value in fields_to_update.items():
            self.works[work_id][field] = value

        return {"success": True, "message": "Work updated successfully"}

    def delete_work(self, work_id: str) -> dict:
        """
        Remove a work from the database and from its artist's work list.

        Args:
            work_id (str): The unique identifier of the work to remove.

        Returns:
            dict: 
                { "success": True, "message": "Work <work_id> deleted." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - If the work does not exist, failure.
            - Also remove the reference from the artist's works list if the artist exists.
            - If the artist does not exist, only remove the work.

        """
        if work_id not in self.works:
            return {"success": False, "error": "Work not found."}

        work_info = self.works[work_id]
        artist_id = work_info['artist_id']

        # Remove reference from artist's work list
        if artist_id in self.artists:
            artist = self.artists[artist_id]
            if work_id in artist["works"]:
                artist["works"].remove(work_id)

        # Now remove work from database
        del self.works[work_id]

        return {"success": True, "message": f"Work {work_id} deleted."}

    def reassign_work_artist(self, work_id: str, new_artist_id: str) -> dict:
        """
        Change the artist association of a work.

        Args:
            work_id (str): The ID of the work whose artist association must be changed.
            new_artist_id (str): The artist ID to assign the work to.

        Returns:
            dict: {
                "success": True,
                "message": "Work successfully reassigned to new artist."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - work_id must exist in the database.
            - new_artist_id must exist in the database.
            - The work's artist_id is updated.
            - The work is removed from the old artist's 'works' list and added to the new one.
        """
        # Check that the work exists
        if work_id not in self.works:
            return { "success": False, "error": "Work does not exist." }

        # Check that the new artist exists
        if new_artist_id not in self.artists:
            return { "success": False, "error": "Target artist does not exist." }

        work = self.works[work_id]
        old_artist_id = work["artist_id"]

        # No change needed if it's already assigned
        if old_artist_id == new_artist_id:
            return { "success": False, "error": "Work is already assigned to this artist." }

        # Update the work's artist_id
        work["artist_id"] = new_artist_id

        # Remove work from old_artist's works list, if present
        if old_artist_id in self.artists:
            old_artist_works = self.artists[old_artist_id]["works"]
            if work_id in old_artist_works:
                old_artist_works.remove(work_id)

        # Add work to new artist's works list, if not already present
        new_artist_works = self.artists[new_artist_id]["works"]
        if work_id not in new_artist_works:
            new_artist_works.append(work_id)

        return { "success": True, "message": "Work successfully reassigned to new artist." }


class ArtistManagementDatabase(BaseEnv):
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

    def search_artist_by_name(self, **kwargs):
        return self._call_inner_tool('search_artist_by_name', kwargs)

    def list_all_artists(self, **kwargs):
        return self._call_inner_tool('list_all_artists', kwargs)

    def get_artist_contact_details(self, **kwargs):
        return self._call_inner_tool('get_artist_contact_details', kwargs)

    def get_works_by_artist_id(self, **kwargs):
        return self._call_inner_tool('get_works_by_artist_id', kwargs)

    def get_work_by_id(self, **kwargs):
        return self._call_inner_tool('get_work_by_id', kwargs)

    def search_works_by_title(self, **kwargs):
        return self._call_inner_tool('search_works_by_title', kwargs)

    def list_artist_works_detailed(self, **kwargs):
        return self._call_inner_tool('list_artist_works_detailed', kwargs)

    def create_artist(self, **kwargs):
        return self._call_inner_tool('create_artist', kwargs)

    def update_artist(self, **kwargs):
        return self._call_inner_tool('update_artist', kwargs)

    def delete_artist(self, **kwargs):
        return self._call_inner_tool('delete_artist', kwargs)

    def update_artist_contact_details(self, **kwargs):
        return self._call_inner_tool('update_artist_contact_details', kwargs)

    def create_work(self, **kwargs):
        return self._call_inner_tool('create_work', kwargs)

    def update_work(self, **kwargs):
        return self._call_inner_tool('update_work', kwargs)

    def delete_work(self, **kwargs):
        return self._call_inner_tool('delete_work', kwargs)

    def reassign_work_artist(self, **kwargs):
        return self._call_inner_tool('reassign_work_artist', kwargs)

