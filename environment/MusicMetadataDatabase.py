# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



# --- State Space entities as TypedDicts ---

class ArtistInfo(TypedDict):
    artist_id: str
    name: str
    birth_date: str
    country: str
    # Additional attributes possible ('etc.')

class AlbumInfo(TypedDict):
    album_id: str
    title: str
    release_date: str
    artist_id: str
    genre: str
    # Additional attributes possible ('etc.')

class TrackInfo(TypedDict):
    track_id: str
    title: str
    duration: float  # in seconds or minutes
    album_id: str
    track_number: int
    # Additional attributes possible ('etc.')

class CreditInfo(TypedDict):
    credit_id: str
    artist_id: str
    entity_type: str  # 'track' or 'album'
    entity_id: str    # refers to track_id or album_id
    role: str
    # Additional attributes possible ('etc.')

# --- Music metadata environment class ---

class _GeneratedEnvImpl:
    def __init__(self):
        # Artists: key = artist_id, value = ArtistInfo
        self.artists: Dict[str, ArtistInfo] = {}

        # Albums: key = album_id, value = AlbumInfo
        self.albums: Dict[str, AlbumInfo] = {}

        # Tracks: key = track_id, value = TrackInfo
        self.tracks: Dict[str, TrackInfo] = {}

        # Credits: key = credit_id, value = CreditInfo
        self.credits: Dict[str, CreditInfo] = {}

        # Constraints:
        # - Each credit must reference a valid artist and a valid track or album.
        # - An artist can have multiple credits on multiple tracks or albums, potentially with different roles.
        # - artist_id, album_id, and track_id must be unique within their respective entities.

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve detailed information for a given artist_id.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict: 
                { "success": True, "data": ArtistInfo }
                    - If the artist_id exists.
                { "success": False, "error": "Artist not found" }
                    - If the artist_id does not exist.
                
        Constraints:
            - artist_id must exist in the database.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }
        return { "success": True, "data": artist }

    def list_all_artists(self) -> dict:
        """
        Return metadata for all artists in the database.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo],   # List of all artists, empty if none.
            }
        """
        return {
            "success": True,
            "data": list(self.artists.values())
        }

    def search_artist_by_name(self, name_query: str) -> dict:
        """
        Search for artists whose names contain the given query substring (case-insensitive).

        Args:
            name_query (str): The substring to search for within artist names.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo],  # List of matching artists (may be empty).
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g., if invalid input.
            }

        Constraints:
            - Search is case-insensitive and matches if the query is a substring of the artist's name.
            - If name_query is an empty string, returns an empty list (no match).
        """
        if not isinstance(name_query, str):
            return {"success": False, "error": "Query must be a string"}

        if name_query.strip() == "":
            # Explicit policy: empty query returns no matches (not all artists)
            return {"success": True, "data": []}

        lowered_query = name_query.lower()
        results = [
            artist_info for artist_info in self.artists.values()
            if lowered_query in artist_info["name"].lower()
        ]
        return {"success": True, "data": results}

    def get_album_by_id(self, album_id: str) -> dict:
        """
        Retrieve metadata for a specific album by its album_id.

        Args:
            album_id (str): Unique identifier of the album.

        Returns:
            dict: {
                "success": True,
                "data": AlbumInfo  # Metadata dictionary for the album
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., album not found
            }

        Constraints:
            - album_id must exist in the albums dictionary.
        """
        album_info = self.albums.get(album_id)
        if not album_info:
            return { "success": False, "error": "Album not found" }
        return { "success": True, "data": album_info }

    def list_albums_by_artist(self, artist_id: str) -> dict:
        """
        List all albums created by a specific artist.

        Args:
            artist_id (str): Unique identifier for the artist.

        Returns:
            dict: {
                "success": True,
                "data": List[AlbumInfo], # possibly empty if no albums,
            }
            or
            {
                "success": False,
                "error": str  # Reason: artist not found
            }

        Constraints:
            - artist_id must exist in the database.
            - Each album in result will have album_info["artist_id"] == artist_id.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": "Artist not found"}

        albums = [
            album_info for album_info in self.albums.values()
            if album_info["artist_id"] == artist_id
        ]
        return {"success": True, "data": albums}

    def get_track_by_id(self, track_id: str) -> dict:
        """
        Retrieve the metadata for a specific track by its unique track_id.

        Args:
            track_id (str): The unique identifier for the track.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": TrackInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Track not found"
                    }

        Constraints:
            - track_id must exist in the database (self.tracks).
        """
        if track_id in self.tracks:
            return {
                "success": True,
                "data": self.tracks[track_id]
            }
        else:
            return {
                "success": False,
                "error": "Track not found"
            }

    def list_tracks_by_album(self, album_id: str) -> dict:
        """
        List all tracks that belong to a given album.

        Args:
            album_id (str): The album's unique identifier.

        Returns:
            dict:
                success (bool): True if album found; False if not.
                data (List[TrackInfo]): List of tracks for the album if successful.
                error (str, optional): Error message if album does not exist.

        Constraints:
            - The specified album_id must exist in the database.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist" }

        tracks = [
            track_info for track_info in self.tracks.values()
            if track_info['album_id'] == album_id
        ]
        return { "success": True, "data": tracks }

    def get_credit_by_id(self, credit_id: str) -> dict:
        """
        Retrieve details of a credit by its credit_id.

        Args:
            credit_id (str): The unique identifier of the credit.

        Returns:
            dict: {
                "success": True,
                "data": CreditInfo  # The credit information dictionary
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., credit not found)
            }
        Constraints:
            - credit_id must exist in the database.
        """
        credit = self.credits.get(credit_id)
        if credit is None:
            return {"success": False, "error": "Credit not found"}
        return {"success": True, "data": credit}

    def list_credits_by_artist(self, artist_id: str) -> dict:
        """
        List all credits (across tracks and albums) for a specific artist_id.

        Args:
            artist_id (str): The unique identifier of the artist whose credits are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[CreditInfo],  # List of all credits for the given artist (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Artist not found"
            }

        Constraints:
            - The artist_id must exist in the artists database.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": "Artist not found"}

        credits = [
            credit for credit in self.credits.values()
            if credit.get("artist_id") == artist_id
        ]

        return {"success": True, "data": credits}

    def list_credits_by_track(self, track_id: str) -> dict:
        """
        List all artist credits for a specific track.

        Args:
            track_id (str): The identifier of the track to query credits for.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[CreditInfo]  # List may be empty if no credits
                  }
                - On failure (e.g., invalid track_id): {
                    "success": False,
                    "error": str
                  }
        Constraints:
            - The provided track_id must exist in the database.
        """
        if track_id not in self.tracks:
            return {"success": False, "error": "Track ID does not exist"}

        credits = [
            credit_info for credit_info in self.credits.values()
            if credit_info["entity_type"] == "track" and credit_info["entity_id"] == track_id
        ]

        return {"success": True, "data": credits}

    def list_credits_by_album(self, album_id: str) -> dict:
        """
        List all artist credits associated with a specific album_id.

        Args:
            album_id (str): The album's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[CreditInfo],  # List of matching credits, empty if none
            }
            OR
            {
                "success": False,
                "error": str  # Description of the error, e.g., album does not exist
            }

        Constraints:
            - The referenced album_id must exist.
            - Only credits where entity_type == 'album' and entity_id == album_id are returned.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist" }

        result = [
            credit for credit in self.credits.values()
            if credit.get("entity_type") == "album" and credit.get("entity_id") == album_id
        ]
        return { "success": True, "data": result }

    def list_credits_by_artist_and_role(self, artist_id: str, role: str) -> dict:
        """
        List all credits for a given artist, filtered by the provided role.

        Args:
            artist_id (str): The unique identifier of the artist.
            role (str): The credit role to filter (e.g., 'composer', 'performer').

        Returns:
            dict: {
                "success": True,
                "data": List[CreditInfo]  # List of matching credits (may be empty if none match)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., "Artist does not exist")
            }

        Constraints:
            - The artist_id must exist in the system.
            - Credit list is filtered to only credits matching both artist_id and role.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist" }

        filtered_credits = [
            credit for credit in self.credits.values()
            if credit["artist_id"] == artist_id and credit["role"] == role
        ]
        return {"success": True, "data": filtered_credits}

    def validate_artist_id_exists(self, artist_id: str) -> dict:
        """
        Check if the specified artist_id exists in the artists database.

        Args:
            artist_id (str): The unique artist identifier to look up.

        Returns:
            dict: {
                "success": True,
                "exists": bool   # True if artist_id exists, False otherwise
            }
        """
        exists = artist_id in self.artists
        return {"success": True, "exists": exists}

    def validate_album_id_exists(self, album_id: str) -> dict:
        """
        Check if a given album_id exists in the albums database.

        Args:
            album_id (str): The unique identifier of the album to validate.

        Returns:
            dict: {
                "success": True,
                "data": { "exists": bool }  # True if album_id exists, else False
            }

        Constraints:
            - album_id is unique, so existence is a simple membership query.
            - If album_id is empty or None, treat as does not exist.
        """
        # Check for empty or None album_id edge case
        if not album_id:
            return { "success": True, "data": { "exists": False } }

        exists = album_id in self.albums
        return { "success": True, "data": { "exists": exists } }

    def validate_track_id_exists(self, track_id: str) -> dict:
        """
        Check if a given track_id exists in the database.

        Args:
            track_id (str): The ID of the track to validate.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if track_id exists, False otherwise
            }

        Constraints:
            - None specific for this operation; just checks existence.
        """
        exists = track_id in self.tracks
        return { "success": True, "exists": exists }

    def add_artist(self, artist_id: str, name: str, birth_date: str, country: str, **kwargs) -> dict:
        """
        Add a new artist to the database.

        Args:
            artist_id (str): Unique identifier for the artist.
            name (str): Artist or group name.
            birth_date (str): Birth date.
            country (str): Country.
            **kwargs: Additional arbitrary artist attributes.

        Returns:
            dict: {
                "success": True,
                "message": "Artist added successfully"
            }
            or
            {
                "success": False,
                "error": "Artist ID already exists"
            }

        Constraints:
            - artist_id must be unique across artists.
            - Required fields: artist_id, name, birth_date, country.
        """
        if artist_id in self.artists:
            return { "success": False, "error": "Artist ID already exists" }
        if not artist_id or not name or not birth_date or not country:
            return { "success": False, "error": "Missing required artist attributes" }
    
        artist_info = {
            "artist_id": artist_id,
            "name": name,
            "birth_date": birth_date,
            "country": country,
        }
        # Add any additional attributes
        artist_info.update(kwargs)
        self.artists[artist_id] = artist_info
        return { "success": True, "message": "Artist added successfully" }

    def update_artist(self, artist_id: str, updates: dict) -> dict:
        """
        Update an existing artist's metadata by applying the given updates.

        Args:
            artist_id (str): Unique identifier of the artist to update.
            updates (dict): Dictionary mapping field names to new values. Cannot update 'artist_id'.

        Returns:
            dict: {
                "success": True,
                "message": "Artist <artist_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - artist_id must exist in the database.
            - Only valid/mutable fields can be updated. 'artist_id' field is immutable.
            - All updated fields must exist in the ArtistInfo schema.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        if not updates:
            return { "success": True, "message": f"Artist {artist_id} updated successfully (no changes)." }

        immutable_fields = {"artist_id"}
        valid_fields = set(self.artists[artist_id].keys()) - immutable_fields
        invalid_fields = [field for field in updates if field not in valid_fields]

        if invalid_fields:
            return {
                "success": False,
                "error": f"Invalid update field(s): {', '.join(invalid_fields)}"
            }

        for key, value in updates.items():
            self.artists[artist_id][key] = value

        return {
            "success": True,
            "message": f"Artist {artist_id} updated successfully."
        }

    def delete_artist(self, artist_id: str, cascade: bool = False) -> dict:
        """
        Remove an artist and all associated credits.
        Optionally cascade to remove albums and tracks (and their credits) associated with this artist.

        Args:
            artist_id (str): The unique identifier for the artist to remove.
            cascade (bool): If True, also remove albums, tracks, and their credits for this artist.

        Returns:
            dict: 
              - On success:
                  {
                      "success": True,
                      "message": "Artist <artist_id> and associated credits deleted",
                      "credits_deleted": [credit_ids],
                      "albums_deleted": [album_ids],  # If cascade==True, else []
                      "tracks_deleted": [track_ids],  # If cascade==True, else []
                  }
              - On failure:
                  { "success": False, "error": "reason" }

        Constraints:
            - artist_id must exist.
            - All credits referencing artist are removed.
            - If cascade, albums/tracks (and their credits) are also deleted.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": f"Artist '{artist_id}' does not exist"}

        # Delete all credits with this artist_id
        credits_to_delete = [cid for cid, c in self.credits.items() if c["artist_id"] == artist_id]
        for cid in credits_to_delete:
            del self.credits[cid]

        albums_deleted = []
        tracks_deleted = []

        if cascade:
            # Delete all albums by this artist, and tracks in those albums
            albums_to_delete = [aid for aid, a in self.albums.items() if a["artist_id"] == artist_id]
            for aid in albums_to_delete:
                # Delete credits referencing this album
                album_credits = [cid for cid, c in self.credits.items()
                                 if c["entity_type"] == "album" and c["entity_id"] == aid]
                for cid in album_credits:
                    del self.credits[cid]
                # Delete all tracks in this album
                tracks_in_album = [tid for tid, t in self.tracks.items() if t["album_id"] == aid]
                for tid in tracks_in_album:
                    # Delete credits referencing this track
                    track_credits = [cid for cid, c in self.credits.items()
                                     if c["entity_type"] == "track" and c["entity_id"] == tid]
                    for cid in track_credits:
                        del self.credits[cid]
                    tracks_deleted.append(tid)
                    del self.tracks[tid]
                albums_deleted.append(aid)
                del self.albums[aid]

        # Delete the artist itself
        del self.artists[artist_id]

        return {
            "success": True,
            "message": f"Artist '{artist_id}' and associated credits deleted"
                       + (", along with albums and tracks" if cascade else ""),
            "credits_deleted": credits_to_delete,
            "albums_deleted": albums_deleted,
            "tracks_deleted": tracks_deleted,
        }

    def add_album(self, album_info: dict) -> dict:
        """
        Add a new album to the database.

        Args:
            album_info (dict): Dictionary matching AlbumInfo (album_id, title, release_date, artist_id, genre, ...)

        Returns:
            dict:
                {"success": True, "message": "Album added: <album_id>"} on success
                {"success": False, "error": <reason>} on failure

        Constraints:
            - album_id must be globally unique in albums.
            - artist_id must refer to an existing artist.
            - Required fields: album_id, title, release_date, artist_id, genre
        """
        required_keys = ["album_id", "title", "release_date", "artist_id", "genre"]
        for key in required_keys:
            if key not in album_info or not album_info[key]:
                return {"success": False, "error": f"Missing or empty required album field: {key}"}

        album_id = album_info["album_id"]
        artist_id = album_info["artist_id"]

        if album_id in self.albums:
            return {"success": False, "error": f"Album ID already exists: {album_id}"}

        if artist_id not in self.artists:
            return {"success": False, "error": f"Artist ID does not exist: {artist_id}"}

        self.albums[album_id] = AlbumInfo(**album_info)  # strict
        return {"success": True, "message": f"Album added: {album_id}"}

    def update_album(self, album_id: str, updates: dict) -> dict:
        """
        Update the metadata of an album.

        Args:
            album_id (str): The unique ID of the album to update.
            updates (dict): Field-value pairs mapping album attributes to their new values.

        Returns:
            dict:
                - On success: { "success": True, "message": "Album <album_id> updated successfully" }
                - On failure: { "success": False, "error": "...reason..." }

        Constraints:
            - album_id must exist in self.albums.
            - Only valid album attributes (except 'album_id') may be updated.
            - If updating artist_id, the new artist_id must exist in self.artists.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album ID not found" }

        album = self.albums[album_id]
        allowed_fields = set(album.keys()) - {"album_id"}
        invalid_fields = [field for field in updates if field not in allowed_fields]
        if invalid_fields:
            return { "success": False, "error": f"Invalid field(s): {', '.join(invalid_fields)}" }

        # Check if artist_id is to be updated and it's valid
        if "artist_id" in updates:
            new_artist_id = updates["artist_id"]
            if new_artist_id not in self.artists:
                return { "success": False, "error": "New artist_id does not exist" }

        # Update fields
        for key, value in updates.items():
            album[key] = value

        # No further consistency checks needed under current constraints
        return { "success": True, "message": f"Album {album_id} updated successfully" }

    def delete_album(self, album_id: str) -> dict:
        """
        Remove an album and all associated tracks and credits in the system.

        Args:
            album_id (str): The unique identifier of the album to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Album, associated tracks and their credits deleted." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Album must exist in the database.
            - All tracks with this album_id are deleted.
            - All credits referencing the album or any associated track are deleted.
        """
        # 1. Check if album exists
        if album_id not in self.albums:
            return {"success": False, "error": "Album does not exist"}

        # 2. Find all tracks belonging to this album
        tracks_to_delete = [track_id for track_id, track in self.tracks.items() if track["album_id"] == album_id]
    
        # 3. Find all credits referencing this album (entity_type == 'album', entity_id == album_id)
        credits_to_delete = [credit_id for credit_id, credit in self.credits.items()
                             if (credit["entity_type"] == "album" and credit["entity_id"] == album_id)]

        # 4. For all tracks, also find credits referencing these tracks (entity_type == 'track', entity_id in tracks_to_delete)
        track_credits_to_delete = [
            credit_id for credit_id, credit in self.credits.items()
            if credit["entity_type"] == "track" and credit["entity_id"] in tracks_to_delete
        ]

        # 5. Delete the album
        del self.albums[album_id]

        # 6. Delete all tracks belonging to this album
        for track_id in tracks_to_delete:
            del self.tracks[track_id]

        # 7. Delete all credits referencing this album or album's tracks
        for credit_id in credits_to_delete + track_credits_to_delete:
            del self.credits[credit_id]

        return {"success": True, "message": "Album, associated tracks and their credits deleted."}

    def add_track(
        self,
        track_id: str,
        title: str,
        duration: float,
        album_id: str,
        track_number: int,
        **kwargs
    ) -> dict:
        """
        Add a new track with a unique track_id and a valid existing album_id.

        Args:
            track_id (str): Unique identifier for the new track.
            title (str): Track title.
            duration (float): Duration of the track (in seconds or minutes).
            album_id (str): ID of the album the track belongs to.
            track_number (int): Position of the track in the album.
            **kwargs: Additional optional fields accepted in TrackInfo.

        Returns:
            dict: {
                "success": True,
                "message": "Track <track_id> added successfully"
            }
            OR
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - track_id must be unique (not already present in self.tracks).
            - album_id must exist in self.albums.
            - All required fields (track_id, title, duration, album_id, track_number) must be provided and valid.
        """

        # Check presence of required fields (should not be None or empty for IDs/title)
        if not track_id:
            return { "success": False, "error": "Missing required field: track_id" }
        if not title:
            return { "success": False, "error": "Missing required field: title" }
        if duration is None:
            return { "success": False, "error": "Missing required field: duration" }
        if not album_id:
            return { "success": False, "error": "Missing required field: album_id" }
        if track_number is None:
            return { "success": False, "error": "Missing required field: track_number" }

        # Constraint 1: track_id must be unique
        if track_id in self.tracks:
            return { "success": False, "error": "Track ID already exists" }

        # Constraint 2: album_id must exist
        if album_id not in self.albums:
            return { "success": False, "error": "Album ID does not exist" }

        # Construct new TrackInfo dict
        new_track = {
            "track_id": track_id,
            "title": title,
            "duration": duration,
            "album_id": album_id,
            "track_number": track_number
        }
        # Add additional fields from kwargs if present (handled by 'etc.' in TrackInfo)
        new_track.update(kwargs)

        self.tracks[track_id] = new_track

        return { "success": True, "message": f"Track {track_id} added successfully" }

    def update_track(self, track_id: str, updates: dict) -> dict:
        """
        Update metadata of an existing track.

        Args:
            track_id (str): Unique ID of the track to update.
            updates (dict): Key-value pairs of TrackInfo fields to update.
                            Keys must not include 'track_id' (which is immutable).

        Returns:
            dict: On success:
                    {
                      "success": True,
                      "message": "Track <track_id> updated successfully."
                    }
                  On failure:
                    {
                      "success": False,
                      "error": str  # Reason for failure
                    }

        Constraints:
            - track_id must exist in self.tracks.
            - Cannot update track_id itself.
            - If album_id is provided, it must refer to an existing album.
            - Only valid TrackInfo keys can be updated.
        """
        if track_id not in self.tracks:
            return {"success": False, "error": "Track does not exist."}

        if not isinstance(updates, dict) or not updates:
            return {"success": False, "error": "No update data provided."}

        # Fields allowed to update
        allowed_fields = set(self.tracks[track_id].keys()) - {"track_id"}

        # Check for illegal update keys
        for k in updates:
            if k == "track_id":
                return {"success": False, "error": "track_id cannot be modified."}
            if k not in allowed_fields:
                return {"success": False, "error": f"Field '{k}' cannot be updated."}

        # Special check: album_id (must exist if present)
        if "album_id" in updates:
            new_album_id = updates["album_id"]
            if new_album_id not in self.albums:
                return {"success": False, "error": "album_id does not refer to an existing album."}

        # Perform updates
        for k, v in updates.items():
            self.tracks[track_id][k] = v

        return {"success": True, "message": f"Track {track_id} updated successfully."}

    def delete_track(self, track_id: str) -> dict:
        """
        Remove a track (by track_id) and all associated credits from the database.

        Args:
            track_id (str): The unique identifier for the track to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Track and associated credits deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Track does not exist."
            }

        Constraints:
            - The track with the given track_id must exist.
            - All credits referencing this track (entity_type='track', entity_id==track_id) must be deleted as well.
        """

        if track_id not in self.tracks:
            return { "success": False, "error": "Track does not exist." }

        # Remove the track
        del self.tracks[track_id]

        # Find credit_ids to remove
        credits_to_remove = [
            credit_id for credit_id, credit in self.credits.items()
            if credit['entity_type'] == 'track' and credit['entity_id'] == track_id
        ]

        # Remove all related credits
        for credit_id in credits_to_remove:
            del self.credits[credit_id]

        return { "success": True, "message": "Track and associated credits deleted successfully." }

    def add_credit(
        self,
        credit_id: str,
        artist_id: str,
        entity_type: str,
        entity_id: str,
        role: str,
        **extra_fields
    ) -> dict:
        """
        Add a new credit entry, ensuring valid artist_id and referenced entity (track or album).

        Args:
            credit_id (str): The unique ID for the new credit.
            artist_id (str): The ID of the artist to credit.
            entity_type (str): Either 'track' or 'album'.
            entity_id (str): The ID of the track or album being credited.
            role (str): The role (e.g., 'composer', 'performer').
            extra_fields: Additional fields for extensibility.

        Returns:
            dict: On success:
                { "success": True, "message": "Credit added successfully" }
                  On failure:
                { "success": False, "error": "<reason>" }

        Constraints:
            - credit_id must be unique.
            - artist_id must exist in artists.
            - entity_type must be 'track' or 'album'.
            - entity_id must exist in the correct collection.
        """
        # Check credit_id uniqueness
        if credit_id in self.credits:
            return { "success": False, "error": "credit_id already exists" }

        # Check artist reference
        if artist_id not in self.artists:
            return { "success": False, "error": "artist_id does not exist" }

        # Check entity_type validity and entity existence
        if entity_type == "track":
            if entity_id not in self.tracks:
                return { "success": False, "error": "track_id does not exist" }
        elif entity_type == "album":
            if entity_id not in self.albums:
                return { "success": False, "error": "album_id does not exist" }
        else:
            return { "success": False, "error": "entity_type must be 'track' or 'album'" }

        # Build new credit info
        credit: CreditInfo = {
            "credit_id": credit_id,
            "artist_id": artist_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "role": role
        }
        # Add extra optional fields if present
        credit.update(extra_fields)

        # Add to credits collection
        self.credits[credit_id] = credit

        return { "success": True, "message": "Credit added successfully" }

    def update_credit(self, credit_id: str, updates: dict) -> dict:
        """
        Update information for an existing credit.

        Args:
            credit_id (str): ID of the credit to update.
            updates (dict): Dictionary of fields to update (e.g., artist_id, entity_type, entity_id, role).

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of successful operation
            }
            OR
            dict: {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - credit_id must exist.
            - If updating artist_id, new artist_id must exist in self.artists.
            - If updating entity_type/entity_id, new entity_type must be 'track' or 'album',
              and new entity_id must be present in self.tracks or self.albums accordingly.
            - Extra/unrecognized fields in updates are ignored.
            - At least one valid field must be present; otherwise, operation is no-op but successful.
        """

        if credit_id not in self.credits:
            return { "success": False, "error": "Credit ID does not exist." }

        credit = self.credits[credit_id]
        updated_fields = []

        # Validate and update artist_id if requested
        if "artist_id" in updates:
            artist_id = updates["artist_id"]
            if artist_id not in self.artists:
                return { "success": False, "error": f"Artist ID '{artist_id}' does not exist." }
            credit["artist_id"] = artist_id
            updated_fields.append("artist_id")

        # Validate and update entity_type/entity_id
        entity_type = credit.get("entity_type")
        entity_id = credit.get("entity_id")
        change_entity_type = "entity_type" in updates
        change_entity_id = "entity_id" in updates

        # Work out new values that would be set
        new_entity_type = updates.get("entity_type", entity_type)
        new_entity_id = updates.get("entity_id", entity_id)

        if change_entity_type or change_entity_id:
            # Validate new_entity_type
            if new_entity_type not in ("track", "album"):
                return { "success": False, "error": f"entity_type must be 'track' or 'album', got '{new_entity_type}'." }
            # Validate new_entity_id
            if new_entity_type == "track":
                if new_entity_id not in self.tracks:
                    return { "success": False, "error": f"Track ID '{new_entity_id}' does not exist." }
            elif new_entity_type == "album":
                if new_entity_id not in self.albums:
                    return { "success": False, "error": f"Album ID '{new_entity_id}' does not exist." }
            credit["entity_type"] = new_entity_type
            credit["entity_id"] = new_entity_id
            if change_entity_type: updated_fields.append("entity_type")
            if change_entity_id: updated_fields.append("entity_id")

        # Update role if requested
        if "role" in updates:
            credit["role"] = updates["role"]
            updated_fields.append("role")

        # Optionally, update any other fields ("etc." fields)
        for field, value in updates.items():
            if field in ("artist_id", "entity_type", "entity_id", "role"):
                continue  # already handled above
            credit[field] = value
            updated_fields.append(field)

        if not updated_fields:
            return { "success": True, "message": "No updates performed (nothing to change)." }

        return {
            "success": True,
            "message": (
                f"Credit '{credit_id}' updated for field(s): {', '.join(updated_fields)}."
            ),
        }

    def delete_credit(self, credit_id: str) -> dict:
        """
        Remove a credit entry from the music metadata database.

        Args:
            credit_id (str): The unique identifier of the credit to remove.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Credit deleted successfully."}
                On failure (not found):
                    {"success": False, "error": "Credit not found."}

        Constraints:
            - The supplied credit_id must exist in the credits.
            - Only the corresponding credit is deleted; no cascading effects.
        """
        if credit_id not in self.credits:
            return {"success": False, "error": "Credit not found."}

        del self.credits[credit_id]
        return {"success": True, "message": "Credit deleted successfully."}

    def merge_artists(self, source_artist_id: str, target_artist_id: str) -> dict:
        """
        Merge two artist entries:
        - All albums and credits referencing `source_artist_id` are reassigned to `target_artist_id`.
        - Source artist record is deleted.
        - Avoids duplicate credits (no repeated artist/entity/role triples).
    
        Args:
            source_artist_id (str): The ID of the artist to be merged (deleted).
            target_artist_id (str): The ID of the artist to merge into (will remain).

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Artist merged: <source> -> <target>"
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
          - Both artist IDs must exist and be different.
          - Prevents duplicate credits and avoids dangling artist references.
        """
        if source_artist_id == target_artist_id:
            return { "success": False, "error": "Source and target artist IDs must be different" }

        if source_artist_id not in self.artists:
            return { "success": False, "error": f"Source artist_id '{source_artist_id}' does not exist" }

        if target_artist_id not in self.artists:
            return { "success": False, "error": f"Target artist_id '{target_artist_id}' does not exist" }

        # Reassign albums
        for album in self.albums.values():
            if album["artist_id"] == source_artist_id:
                album["artist_id"] = target_artist_id

        # Avoid duplicated credits: track all (artist_id, entity_type, entity_id, role) tuples for the target
        existing_credits = set((
            ci["artist_id"], ci["entity_type"], ci["entity_id"], ci["role"]
            ) for ci in self.credits.values())

        source_credit_ids = [cid for cid, ci in self.credits.items() if ci["artist_id"] == source_artist_id]
        for credit_id in source_credit_ids:
            credit = self.credits[credit_id]
            new_tuple = (target_artist_id, credit["entity_type"], credit["entity_id"], credit["role"])
            if new_tuple in existing_credits:
                # This exact credit for target already exists, so remove the duplicated source credit
                del self.credits[credit_id]
            else:
                # Reassign credit's artist_id to target
                credit["artist_id"] = target_artist_id
                existing_credits.add(new_tuple)

        # Finally, delete the source artist
        del self.artists[source_artist_id]

        return { "success": True, "message": f"Artist merged: {source_artist_id} -> {target_artist_id}" }

    def split_artist(
        self, 
        original_artist_id: str, 
        new_artist_info: dict, 
        credits_to_transfer: list
    ) -> dict:
        """
        Split an artist record into two distinct artists, reassigning specified credits to the new artist.

        Args:
            original_artist_id (str): The ID of the artist to split.
            new_artist_info (dict): Metadata for the new artist. Must include a unique artist_id.
            credits_to_transfer (list): List of credit_id strings belonging to original_artist_id
                                       that are to be reassigned to the new artist.

        Returns:
            dict: On success,
              {
                  "success": True,
                  "message": str (description)
              }
              On failure,
              {
                  "success": False,
                  "error": str (reason)
              }

        Constraints:
            - original_artist_id must exist.
            - new_artist_info['artist_id'] must not already exist.
            - Each credit_id in credits_to_transfer must exist and belong to original_artist_id.
            - Only specified credits are reassigned.
            - All artist IDs remain unique.
        """
        # 1. Validate original artist existence
        if original_artist_id not in self.artists:
            return { "success": False, "error": "Original artist_id does not exist." }
    
        # 2. Validate new artist_id uniqueness
        new_artist_id = new_artist_info.get('artist_id')
        if not new_artist_id or new_artist_id in self.artists:
            return { "success": False, "error": "New artist_id is missing or already exists." }
    
        # 3. Validate specified credits
        invalid_credits = []
        for cid in credits_to_transfer:
            credit = self.credits.get(cid)
            if credit is None or credit['artist_id'] != original_artist_id:
                invalid_credits.append(cid)
        if invalid_credits:
            return { 
                "success": False, 
                "error": f"The following credit_ids are invalid or do not belong to the original artist: {invalid_credits}"
            }
        
        # 4. Add the new artist
        self.artists[new_artist_id] = new_artist_info.copy()
    
        # 5. Reassign credits as needed
        for cid in credits_to_transfer:
            self.credits[cid]['artist_id'] = new_artist_id

        return {
            "success": True,
            "message": f"Artist {original_artist_id} split. New artist {new_artist_id} created, {len(credits_to_transfer)} credits reassigned."
        }


class MusicMetadataDatabase(BaseEnv):
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

    def list_all_artists(self, **kwargs):
        return self._call_inner_tool('list_all_artists', kwargs)

    def search_artist_by_name(self, **kwargs):
        return self._call_inner_tool('search_artist_by_name', kwargs)

    def get_album_by_id(self, **kwargs):
        return self._call_inner_tool('get_album_by_id', kwargs)

    def list_albums_by_artist(self, **kwargs):
        return self._call_inner_tool('list_albums_by_artist', kwargs)

    def get_track_by_id(self, **kwargs):
        return self._call_inner_tool('get_track_by_id', kwargs)

    def list_tracks_by_album(self, **kwargs):
        return self._call_inner_tool('list_tracks_by_album', kwargs)

    def get_credit_by_id(self, **kwargs):
        return self._call_inner_tool('get_credit_by_id', kwargs)

    def list_credits_by_artist(self, **kwargs):
        return self._call_inner_tool('list_credits_by_artist', kwargs)

    def list_credits_by_track(self, **kwargs):
        return self._call_inner_tool('list_credits_by_track', kwargs)

    def list_credits_by_album(self, **kwargs):
        return self._call_inner_tool('list_credits_by_album', kwargs)

    def list_credits_by_artist_and_role(self, **kwargs):
        return self._call_inner_tool('list_credits_by_artist_and_role', kwargs)

    def validate_artist_id_exists(self, **kwargs):
        return self._call_inner_tool('validate_artist_id_exists', kwargs)

    def validate_album_id_exists(self, **kwargs):
        return self._call_inner_tool('validate_album_id_exists', kwargs)

    def validate_track_id_exists(self, **kwargs):
        return self._call_inner_tool('validate_track_id_exists', kwargs)

    def add_artist(self, **kwargs):
        return self._call_inner_tool('add_artist', kwargs)

    def update_artist(self, **kwargs):
        return self._call_inner_tool('update_artist', kwargs)

    def delete_artist(self, **kwargs):
        return self._call_inner_tool('delete_artist', kwargs)

    def add_album(self, **kwargs):
        return self._call_inner_tool('add_album', kwargs)

    def update_album(self, **kwargs):
        return self._call_inner_tool('update_album', kwargs)

    def delete_album(self, **kwargs):
        return self._call_inner_tool('delete_album', kwargs)

    def add_track(self, **kwargs):
        return self._call_inner_tool('add_track', kwargs)

    def update_track(self, **kwargs):
        return self._call_inner_tool('update_track', kwargs)

    def delete_track(self, **kwargs):
        return self._call_inner_tool('delete_track', kwargs)

    def add_credit(self, **kwargs):
        return self._call_inner_tool('add_credit', kwargs)

    def update_credit(self, **kwargs):
        return self._call_inner_tool('update_credit', kwargs)

    def delete_credit(self, **kwargs):
        return self._call_inner_tool('delete_credit', kwargs)

    def merge_artists(self, **kwargs):
        return self._call_inner_tool('merge_artists', kwargs)

    def split_artist(self, **kwargs):
        return self._call_inner_tool('split_artist', kwargs)

