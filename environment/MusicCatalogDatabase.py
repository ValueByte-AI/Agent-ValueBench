# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class ArtistInfo(TypedDict, total=False):
    artist_id: str
    name: str
    profile: str
    genre: str
    country: str
    years_active: str
    etc: Dict[str, Any]  # For additional artist metadata

class AlbumInfo(TypedDict, total=False):
    album_id: str
    artist_id: str  # Foreign key to Artist
    title: str
    release_date: str
    genre: str
    cover_art: str
    etc: Dict[str, Any]  # For additional album metadata

class TrackInfo(TypedDict, total=False):
    track_id: str
    album_id: str  # Foreign key to Album
    title: str
    duration: float
    track_number: int
    composer: str
    featuring_artists: List[str]
    etc: Dict[str, Any]  # For additional track metadata

class _GeneratedEnvImpl:
    def __init__(self):
        # Artists: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}

        # Albums: {album_id: AlbumInfo}
        self.albums: Dict[str, AlbumInfo] = {}

        # Tracks: {track_id: TrackInfo}
        self.tracks: Dict[str, TrackInfo] = {}

        # Constraints:
        # - Every album must link to a valid artist via artist_id.
        # - Every track must link to a valid album via album_id.
        # - Artist IDs, album IDs, and track IDs must be unique within their entities.
        # - Deleting an artist should cascade to albums and tracks (or disallow deletion if dependencies exist).
        # - Composite queries must resolve relationships correctly.

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve artist metadata/profile using artist_id.

        Args:
            artist_id (str): Unique identifier for the artist.

        Returns:
            dict:
                - On success: { "success": True, "data": ArtistInfo }
                - On failure: { "success": False, "error": "Artist not found" }

        Constraints:
            - artist_id must correspond to an existing artist in the database.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return {"success": False, "error": "Artist not found"}

        return {"success": True, "data": artist}

    def list_artists_by_ids(self, artist_ids: list) -> dict:
        """
        Retrieve metadata/profile for a list of artist_ids.

        Args:
            artist_ids (list of str): The artist_ids to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo],  # List of artist metadata; empty if none found.
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Only existing artist_ids will appear in the output.
            - Input must be a list of strings.
        """
        if not isinstance(artist_ids, list):
            return {"success": False, "error": "artist_ids must be a list"}
        if not all(isinstance(aid, str) for aid in artist_ids):
            return {"success": False, "error": "All artist_ids must be strings"}

        # Remove duplicates for efficiency
        unique_ids = set(artist_ids)
        result = [self.artists[aid] for aid in unique_ids if aid in self.artists]

        return {"success": True, "data": result}

    def get_albums_by_artist_id(self, artist_id: str) -> dict:
        """
        Retrieve all albums associated with a given artist_id.

        Args:
            artist_id (str): The unique ID of the artist.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": List[AlbumInfo]  # List may be empty if artist has no albums
                    }
                On error:
                    {
                      "success": False,
                      "error": str  # Explanation, e.g. artist not found
                    }
        Constraints:
            - artist_id must exist in self.artists.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": "Artist not found"}

        albums = [
            album_info for album_info in self.albums.values()
            if album_info.get("artist_id") == artist_id
        ]
        return {"success": True, "data": albums}

    def get_album_by_id(self, album_id: str) -> dict:
        """
        Retrieve album metadata/profile using the provided album_id.

        Args:
            album_id (str): Unique identifier for the desired album.

        Returns:
            dict:
              - On success: {"success": True, "data": AlbumInfo}
              - On failure: {"success": False, "error": "Album not found"}

        Constraints:
            - album_id must uniquely identify an existing album in the database.
        """
        album = self.albums.get(album_id)
        if album is None:
            return { "success": False, "error": "Album not found" }
        return { "success": True, "data": album }

    def get_tracks_by_album_id(self, album_id: str) -> dict:
        """
        Retrieve all tracks associated with a given album_id.

        Args:
            album_id (str): The ID of the album whose tracks should be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[TrackInfo]  # List of tracks (may be empty if no tracks belong to the album)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., album does not exist
            }

        Constraints:
            - album_id must exist in the catalog.
            - Only tracks whose album_id matches are considered.
        """
        if album_id not in self.albums:
            return {"success": False, "error": "Album does not exist"}

        tracks = [
            track_info for track_info in self.tracks.values()
            if track_info.get("album_id") == album_id
        ]

        return {"success": True, "data": tracks}

    def get_tracks_by_artist_id(self, artist_id: str) -> dict:
        """
        Retrieve all tracks for a given artist by traversing the albums.

        Args:
            artist_id (str): The unique identifier of the artist.

        Returns:
            dict:
                If artist exists:
                    { "success": True, "data": List[TrackInfo] }
                If artist does not exist:
                    { "success": False, "error": "Artist not found" }

        Constraints:
            - The specified artist_id must exist in the music catalog.
            - Traverses albums by that artist and returns all associated tracks.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Find all album_ids by this artist
        album_ids = [album["album_id"] for album in self.albums.values() if album.get("artist_id") == artist_id]

        # Accumulate tracks in those albums
        tracks = [
            track for track in self.tracks.values()
            if track.get("album_id") in album_ids
        ]

        return { "success": True, "data": tracks }

    def get_track_by_id(self, track_id: str) -> dict:
        """
        Retrieve metadata for a single track by its unique identifier.

        Args:
            track_id (str): The unique ID of the track to retrieve.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": TrackInfo (track metadata)
                  }
                - On failure (not found): {
                    "success": False,
                    "error": "Track not found"
                  }

        Constraints:
            - track_id must exist in the database.
        """
        track = self.tracks.get(track_id)
        if track is None:
            return { "success": False, "error": "Track not found" }
        return { "success": True, "data": track }

    def composite_artist_full_info(self, artist_id: str) -> dict:
        """
        Retrieve an artist's profile, all their albums, and all tracks associated with each album.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "artist": ArtistInfo,
                            "albums": [
                                {
                                    "album": AlbumInfo,
                                    "tracks": List[TrackInfo]
                                }, 
                                ...
                            ]
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Artist does not exist"
                    }

        Constraints:
            - The specified artist_id must exist in the database.
            - Only albums for the artist and their tracks are returned.
        """
        artist = self.artists.get(artist_id)
        if not artist:
            return { "success": False, "error": "Artist does not exist" }

        artist_albums = [album for album in self.albums.values() if album.get("artist_id") == artist_id]

        albums_with_tracks = []
        for album in artist_albums:
            album_id = album.get("album_id")
            tracks = [track for track in self.tracks.values() if track.get("album_id") == album_id]
            albums_with_tracks.append({
                "album": album,
                "tracks": tracks
            })

        result = {
            "artist": artist,
            "albums": albums_with_tracks
        }
        return {
            "success": True,
            "data": result
        }

    def add_artist(self, artist_info: dict) -> dict:
        """
        Add a new artist to the music catalog.

        Args:
            artist_info (dict): Dictionary with artist attributes, must include 'artist_id'.

        Returns:
            dict: {
                "success": True,
                "message": "Artist <artist_id> added"
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - artist_id must be present and unique within the catalog.
        """
        artist_id = artist_info.get("artist_id")
        if not artist_id or not isinstance(artist_id, str):
            return {"success": False, "error": "artist_id is required and must be a non-empty string"}
        if artist_id in self.artists:
            return {"success": False, "error": "Artist ID already exists"}

        # Store artist info
        self.artists[artist_id] = dict(artist_info)
        return {"success": True, "message": f"Artist {artist_id} added"}

    def update_artist(self, artist_id: str, updates: dict) -> dict:
        """
        Updates the metadata/profile of an existing artist.

        Args:
            artist_id (str): The unique ID of the artist to update.
            updates (dict): Fields and values to update for the artist.
                - Must not contain 'artist_id' (immutable).
                - Only known ArtistInfo fields (including 'etc') will be updated.

        Returns:
            dict:
                - On success: { "success": True, "message": "Artist <artist_id> updated." }
                - On error: { "success": False, "error": "Reason" }

        Constraints:
            - Artist must exist.
            - artist_id cannot be modified.
            - No operation if updates dict is empty or contains no valid keys.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Define updatable keys for the ArtistInfo structure
        allowed_keys = {"name", "profile", "genre", "country", "years_active", "etc"}
        updates = {k: v for k, v in updates.items() if k in allowed_keys and k != "artist_id"}

        if not updates:
            return { "success": False, "error": "No valid fields to update" }

        artist = self.artists[artist_id]

        for k, v in updates.items():
            if k == "etc":
                # If updating 'etc', merge nested dict if possible
                if "etc" not in artist or not isinstance(artist["etc"], dict):
                    artist["etc"] = {}
                if isinstance(v, dict):
                    artist["etc"].update(v)
                else:
                    artist["etc"] = v  # Replace entirely if not dict
            else:
                artist[k] = v

        self.artists[artist_id] = artist
        return { "success": True, "message": f"Artist {artist_id} updated." }

    def delete_artist(self, artist_id: str) -> dict:
        """
        Delete an artist and cascade delete all dependent albums and tracks.

        Args:
            artist_id (str): Unique identifier for the artist to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Artist and all associated albums and tracks deleted."
            }
            or
            {
                "success": False,
                "error": "Artist not found"
            }

        Constraints:
            - If artist exists, delete all albums belonging to the artist and all tracks belonging to those albums, then the artist record itself.
            - If artist does not exist: return error.
        """
        # Check if artist exists
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Find albums by this artist
        albums_to_delete = [album_id for album_id, album in self.albums.items()
                            if album.get("artist_id") == artist_id]

        # Collect track IDs to delete
        tracks_to_delete = []
        for album_id in albums_to_delete:
            tracks_in_album = [track_id for track_id, track in self.tracks.items()
                               if track.get("album_id") == album_id]
            tracks_to_delete.extend(tracks_in_album)

        # Delete tracks
        for track_id in tracks_to_delete:
            del self.tracks[track_id]

        # Delete albums
        for album_id in albums_to_delete:
            del self.albums[album_id]

        # Delete artist
        del self.artists[artist_id]

        return {
            "success": True,
            "message": "Artist and all associated albums and tracks deleted."
        }

    def add_album(self, album_info: AlbumInfo) -> dict:
        """
        Add a new album to the catalog.

        Args:
            album_info (AlbumInfo): Dictionary containing album metadata.
                Must include 'album_id' (unique) and 'artist_id' (existing).

        Returns:
            dict: 
                {"success": True, "message": "Album <album_id> added."}
                or
                {"success": False, "error": str}

        Constraints:
            - album_id must be unique (not yet in self.albums)
            - artist_id must exist in self.artists
        """
        # Validate required fields
        if "album_id" not in album_info or "artist_id" not in album_info:
            return {"success": False, "error": "album_id and artist_id are required to add an album."}

        album_id = album_info["album_id"]
        artist_id = album_info["artist_id"]

        if album_id in self.albums:
            return {"success": False, "error": f"Album ID '{album_id}' already exists."}
        if artist_id not in self.artists:
            return {"success": False, "error": f"Artist ID '{artist_id}' does not exist."}

        # Add (shallow copy for immutability of input)
        self.albums[album_id] = dict(album_info)
        return {"success": True, "message": f"Album '{album_id}' added."}

    def update_album(self, album_id: str, updates: dict) -> dict:
        """
        Update metadata fields for a specified album.

        Args:
            album_id (str): The unique ID of the album to update.
            updates (dict): Dictionary of AlbumInfo fields to update (e.g., title, release_date, genre, cover_art, artist_id, etc.).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Album updated successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Album must exist in catalog.
            - If changing artist_id, the new artist_id must exist.
            - Unknown fields in updates are ignored.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album not found." }
    
        album_info = self.albums[album_id]

        # List of allowed fields (from AlbumInfo definition)
        allowed_fields = set(['artist_id', 'title', 'release_date', 'genre', 'cover_art', 'etc'])

        # If artist_id is being updated, validate new artist_id exists
        if 'artist_id' in updates:
            new_artist_id = updates['artist_id']
            if new_artist_id != album_info.get('artist_id') and new_artist_id not in self.artists:
                return { "success": False, "error": "New artist_id does not exist." }

        updated = False
        for key, value in updates.items():
            if key in allowed_fields:
                # Special handling for 'etc' field if it's a dict for extended metadata
                if key == 'etc' and isinstance(value, dict):
                    if 'etc' not in album_info or not isinstance(album_info['etc'], dict):
                        album_info['etc'] = {}
                    album_info['etc'].update(value)
                    updated = True
                else:
                    album_info[key] = value
                    updated = True
            # else: ignore keys not in allowed_fields

        if updated:
            self.albums[album_id] = album_info  # Explicitly update (though dicts are mutable)
            return { "success": True, "message": "Album updated successfully." }
        else:
            return { "success": False, "error": "No valid fields to update." }

    def delete_album(self, album_id: str) -> dict:
        """
        Delete an album and cascade delete all dependent tracks.

        Args:
            album_id (str): The identifier of the album to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Album and all dependent tracks deleted successfully"
            }
            or
            {
                "success": False,
                "error": "Album does not exist"
            }

        Constraints:
            - Album must exist to be deleted.
            - All tracks referencing the album (album_id) are also deleted, to maintain constraints.
            - Guarantees: no orphaned tracks left after deletion.
        """
        if album_id not in self.albums:
            return {"success": False, "error": "Album does not exist"}

        # Delete all tracks associated with the album
        track_ids_to_delete = [track_id for track_id, track in self.tracks.items()
                               if track.get("album_id") == album_id]
        for track_id in track_ids_to_delete:
            del self.tracks[track_id]

        # Delete the album itself
        del self.albums[album_id]

        return {
            "success": True,
            "message": "Album and all dependent tracks deleted successfully"
        }

    def add_track(self, track_info: dict) -> dict:
        """
        Add a new track to the music catalog.
    
        Args:
            track_info (dict): Dictionary containing track metadata. Must contain at least:
                - track_id (str): Unique ID for the track
                - album_id (str): The album the track belongs to (must exist)
                - title (str): Track title (recommended)
                - duration (float): Duration in seconds (optional)
                - track_number (int): Position on album (optional)
                - composer (str): Composer info (optional)
                - featuring_artists (List[str]): Featuring artists (optional)
                - etc (dict): Any additional track metadata (optional)

        Returns:
            dict: 
                On success: { "success": True, "message": "Track <track_id> added successfully" }
                On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - track_id must not duplicate any existing track
            - album_id must point to an existing album
            - track_id and album_id must be provided in input
        """
        required_fields = ["track_id", "album_id"]
        missing_fields = [k for k in required_fields if k not in track_info or track_info[k] is None]
        if missing_fields:
            return { "success": False, "error": f"Missing required fields: {', '.join(missing_fields)}" }
    
        track_id = track_info["track_id"]
        album_id = track_info["album_id"]
    
        if track_id in self.tracks:
            return { "success": False, "error": "Track ID already exists" }
    
        if album_id not in self.albums:
            return { "success": False, "error": "Album ID does not exist" }
    
        # Initialize missing optional fields for TrackInfo to avoid KeyError elsewhere
        track_entry: TrackInfo = {
            "track_id": track_id,
            "album_id": album_id,
            "title": track_info.get("title", ""),
            "duration": track_info.get("duration", 0.0),
            "track_number": track_info.get("track_number", 0),
            "composer": track_info.get("composer", ""),
            "featuring_artists": track_info.get("featuring_artists", []),
            "etc": track_info.get("etc", {}),
        }
    
        # Add any extra keys from input
        for k, v in track_info.items():
            if k not in track_entry:
                track_entry[k] = v

        self.tracks[track_id] = track_entry

        return { "success": True, "message": f"Track {track_id} added successfully" }

    def update_track(self, track_id: str, updates: dict) -> dict:
        """
        Update the specified fields/metadata of a given track.

        Args:
            track_id (str): The ID of the track to update.
            updates (dict): Dictionary of fields and values to update (keys may include
                            title, duration, track_number, composer, featuring_artists, album_id, etc, or fields in 'etc').

        Returns:
            dict: On success:
                { "success": True, "message": "Track updated successfully." }
            On failure:
                { "success": False, "error": "<reason>" }

        Constraints:
            - The specified track must exist.
            - If album_id is being updated, it must reference an existing album.
            - Only valid fields for tracks may be updated; updating track_id itself is not permitted.
        """
        if track_id not in self.tracks:
            return { "success": False, "error": "Track does not exist." }

        track = self.tracks[track_id]

        # Fields allowed for top-level update
        allowed_fields = set([
            "album_id", "title", "duration", "track_number",
            "composer", "featuring_artists", "etc"
        ])

        # Do not allow updating track_id itself
        if "track_id" in updates:
            return { "success": False, "error": "Cannot update track_id." }

        # Handle album_id update constraint
        if "album_id" in updates:
            new_album_id = updates["album_id"]
            if new_album_id not in self.albums:
                return { "success": False, "error": "album_id does not reference an existing album." }
            # (No further action needed; allowed)

        # Apply updates
        for key, value in updates.items():
            if key in allowed_fields:
                # Handle special merge for 'etc'
                if key == "etc" and isinstance(value, dict):
                    if "etc" not in track or not isinstance(track["etc"], dict):
                        track["etc"] = {}
                    track["etc"].update(value)
                else:
                    track[key] = value
            else:
                return { "success": False, "error": f"Field '{key}' is not a valid updatable track field." }

        self.tracks[track_id] = track
        return { "success": True, "message": "Track updated successfully." }

    def delete_track(self, track_id: str) -> dict:
        """
        Delete a track from the catalog.

        Args:
            track_id (str): The unique identifier of the track to be deleted.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "Track <track_id> deleted."
                }
                On failure (track does not exist):
                {
                    "success": False,
                    "error": "Track with id <track_id> does not exist."
                }

        Constraints:
            - Track ID must exist in the catalog to be deleted.
            - No cascade or dependent check required for tracks.
        """
        if track_id not in self.tracks:
            return {
                "success": False,
                "error": f"Track with id {track_id} does not exist."
            }
    
        del self.tracks[track_id]
        return {
            "success": True,
            "message": f"Track {track_id} deleted."
        }


class MusicCatalogDatabase(BaseEnv):
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

    def list_artists_by_ids(self, **kwargs):
        return self._call_inner_tool('list_artists_by_ids', kwargs)

    def get_albums_by_artist_id(self, **kwargs):
        return self._call_inner_tool('get_albums_by_artist_id', kwargs)

    def get_album_by_id(self, **kwargs):
        return self._call_inner_tool('get_album_by_id', kwargs)

    def get_tracks_by_album_id(self, **kwargs):
        return self._call_inner_tool('get_tracks_by_album_id', kwargs)

    def get_tracks_by_artist_id(self, **kwargs):
        return self._call_inner_tool('get_tracks_by_artist_id', kwargs)

    def get_track_by_id(self, **kwargs):
        return self._call_inner_tool('get_track_by_id', kwargs)

    def composite_artist_full_info(self, **kwargs):
        return self._call_inner_tool('composite_artist_full_info', kwargs)

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

