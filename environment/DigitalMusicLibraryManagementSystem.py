# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict
from datetime import datetime



class TrackInfo(TypedDict):
    track_id: str
    title: str
    duration: int  # in seconds
    artist_id: str
    album_id: str
    genre: str
    release_date: str  # ISO 8601 date
    play_count: int
    last_played_at: str  # ISO 8601 datetime

class ArtistInfo(TypedDict):
    artist_id: str
    name: str

class AlbumInfo(TypedDict):
    album_id: str
    title: str
    release_date: str  # ISO 8601 date
    artist_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing a digital music library.
        """

        # Tracks: {track_id: TrackInfo}
        self.tracks: Dict[str, TrackInfo] = {}

        # Artists: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}

        # Albums: {album_id: AlbumInfo}
        self.albums: Dict[str, AlbumInfo] = {}

        # Constraints:
        # - Each track_id, artist_id, and album_id must be unique.
        # - Each track must reference a valid artist_id and (if applicable) album_id.
        # - Track durations should be positive numbers.
        # - Play count is non-negative and increments only upon playback events.

    def get_track_by_id(self, track_id: str) -> dict:
        """
        Retrieve the complete metadata (including duration) for a given track ID.

        Args:
            track_id (str): The unique identifier of the track.

        Returns:
            dict:
                - If the track exists:
                    { "success": True, "data": TrackInfo }
                - If the track does not exist:
                    { "success": False, "error": "Track not found" }
        """
        if track_id not in self.tracks:
            return { "success": False, "error": "Track not found" }
        return { "success": True, "data": self.tracks[track_id] }

    def get_track_duration(self, track_id: str) -> dict:
        """
        Return the duration (in seconds) of the track with the given track_id.

        Args:
            track_id (str): The unique identifier of the track.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": int }  # duration in seconds
                On failure:
                    { "success": False, "error": "Track does not exist" }

        Constraints:
            - track_id must exist in the library.
        """
        track = self.tracks.get(track_id)
        if not track:
            return { "success": False, "error": "Track does not exist" }
        return { "success": True, "data": track["duration"] }

    def list_all_tracks(self) -> dict:
        """
        Retrieve the full list of tracks in the music library.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TrackInfo]  # All tracks in the library; empty if none exist
                }
        """
        return {
            "success": True,
            "data": list(self.tracks.values())
        }

    def search_tracks_by_title(self, title: str) -> dict:
        """
        Find all tracks with a specified title (exact or partial, case-insensitive match).

        Args:
            title (str): The title or partial title to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TrackInfo]     # Tracks with title containing the search string (case-insensitive)
            }
            (No error output, always succeeds with possibly empty result)
        """
        search_lower = title.lower()
        matches = [
            track_info for track_info in self.tracks.values()
            if search_lower in track_info["title"].lower()
        ]
        return { "success": True, "data": matches }

    def search_tracks_by_artist_id(self, artist_id: str) -> dict:
        """
        List all tracks associated with a given artist.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict:
                - success: True and 'data' containing list of TrackInfo dicts for this artist.
                - success: False and 'error' message if artist does not exist.

        Constraints:
            - artist_id must exist in the system.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist" }

        tracks = [
            track
            for track in self.tracks.values()
            if track.get("artist_id") == artist_id
        ]

        return { "success": True, "data": tracks }

    def search_tracks_by_album_id(self, album_id: str) -> dict:
        """
        List all tracks that belong to a given album_id.

        Args:
            album_id (str): The album identifier for which to retrieve tracks.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[TrackInfo]   # May be empty if album has no tracks
                  }
                - On error: {
                    "success": False,
                    "error": "Album does not exist"
                  }

        Constraints:
            - album_id must exist in the system.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist" }

        result = [
            track_info for track_info in self.tracks.values()
            if track_info["album_id"] == album_id
        ]

        return { "success": True, "data": result }

    def search_tracks_by_genre(self, genre: str) -> dict:
        """
        Retrieve all tracks within a given genre (case-insensitive match).

        Args:
            genre (str): The genre string to match (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[TrackInfo]  # List of track info dicts for matching tracks (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for error (e.g., invalid genre)
            }

        Constraints:
            - Genre parameter must be a non-empty string.
        """
        if not isinstance(genre, str) or not genre.strip():
            return { "success": False, "error": "Genre must be a non-empty string" }
    
        genre_lower = genre.strip().lower()
        results = [
            track for track in self.tracks.values()
            if track["genre"].strip().lower() == genre_lower
        ]
        return { "success": True, "data": results }

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve artist information for a given artist_id.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": ArtistInfo  # artist information dictionary
                    }
                On failure:
                    {
                      "success": False,
                      "error": "Artist not found"
                    }
        Constraints:
            - artist_id must exist in the library.
            - Each artist_id is unique.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }
        return { "success": True, "data": artist }

    def list_all_artists(self) -> dict:
        """
        List all artists in the digital music library system.

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo]  # (possibly empty)
            }

        Constraints:
            - No error if no artists exist ("data" is an empty list).
        """
        artist_list = list(self.artists.values())
        return {
            "success": True,
            "data": artist_list
        }

    def get_album_by_id(self, album_id: str) -> dict:
        """
        Retrieve metadata for the specified album.

        Args:
            album_id (str): Unique identifier of the album.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "data": AlbumInfo  # album's metadata
                    }
                On failure (not found):
                    {
                      "success": False,
                      "error": "Album not found"
                    }

        Constraints:
            - album_id must exist in the system.
        """
        album = self.albums.get(album_id)
        if album is None:
            return { "success": False, "error": "Album not found" }
        return { "success": True, "data": album }

    def list_all_albums(self) -> dict:
        """
        List all albums present in the music library.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AlbumInfo],  # All album metadata (may be empty if no albums exist)
            }
        """
        # Retrieve all album entries as a list
        album_list = list(self.albums.values())
        return { "success": True, "data": album_list }

    def get_tracks_in_album(self, album_id: str) -> dict:
        """
        Retrieve all tracks belonging to a specific album.

        Args:
            album_id (str): The ID of the album.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TrackInfo]  # All tracks with the specified album_id
                    }
                On failure (invalid album_id):
                    {
                        "success": False,
                        "error": "Album does not exist"
                    }

        Constraints:
            - The album_id must exist in the albums dictionary.
            - Only tracks whose album_id matches the provided album_id are returned.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist" }

        tracks_in_album = [
            track_info for track_info in self.tracks.values()
            if track_info.get("album_id") == album_id
        ]

        return { "success": True, "data": tracks_in_album }


    def get_tracks_by_release_date_range(self, start_date: str, end_date: str) -> dict:
        """
        List tracks released within the specified release date range (inclusive).

        Args:
            start_date (str): ISO 8601 date string marking the start of the range (inclusive).
            end_date (str): ISO 8601 date string marking the end of the range (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[TrackInfo]  # All matching tracks (may be empty if no match)
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., invalid date format, start > end)
            }

        Constraints:
            - Dates must be in valid ISO 8601 date format (YYYY-MM-DD).
            - start_date cannot be after end_date.
        """
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            return { "success": False, "error": "Invalid date format. Use YYYY-MM-DD (ISO 8601)." }

        if start_dt > end_dt:
            return { "success": False, "error": "Start date cannot be after end date." }

        results = []
        for track in self.tracks.values():
            try:
                track_date = datetime.fromisoformat(track["release_date"])
                if start_dt <= track_date <= end_dt:
                    results.append(track)
            except Exception:
                # Ignore tracks with malformed release dates
                continue

        return { "success": True, "data": results }

    def get_playback_statistics_for_track(self, track_id: str) -> dict:
        """
        Retrieve the play count and last played time for a specific track.

        Args:
            track_id (str): The unique ID of the track.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "play_count": int,
                            "last_played_at": str  # ISO 8601 datetime
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Track not found"
                    }

        Constraints:
            - The track_id must exist in the library.
        """
        track = self.tracks.get(track_id)
        if not track:
            return { "success": False, "error": "Track not found" }
        return {
            "success": True,
            "data": {
                "play_count": track["play_count"],
                "last_played_at": track["last_played_at"]
            }
        }


    def increment_track_play_count(self, track_id: str) -> dict:
        """
        Register a playback event for the specified track.

        Args:
            track_id (str): The unique identifier of the track.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Playback registered: play_count incremented and last_played_at updated."
                }
                On failure:
                {
                    "success": False,
                    "error": "Track not found."
                }
    
        Constraints:
            - The specified track_id must exist in the system.
            - play_count is incremented by one (only upon playback).
            - last_played_at updated to the current timestamp in ISO 8601 format.
        """
        if track_id not in self.tracks:
            return {"success": False, "error": "Track not found."}

        # Access the track
        track = self.tracks[track_id]
        # Increment play_count
        track['play_count'] += 1
        # Update last_played_at to current time in ISO8601
        track['last_played_at'] = datetime.utcnow().isoformat() + "Z"
        # Save back (unnecessary for dict reference, but stylistic)
        self.tracks[track_id] = track

        return {
            "success": True,
            "message": "Playback registered: play_count incremented and last_played_at updated."
        }

    def add_new_track(
        self,
        track_id: str,
        title: str,
        duration: int,
        artist_id: str,
        album_id: str,
        genre: str,
        release_date: str,
        play_count: int = 0,
        last_played_at: str = ""
    ) -> dict:
        """
        Add a new track to the library, enforcing all uniqueness and reference constraints.

        Args:
            track_id (str): Unique identifier for the track.
            title (str): Track's title.
            duration (int): Track's duration in seconds (must be positive).
            artist_id (str): Valid artist ID.
            album_id (str): Album ID ("" or None if no album, otherwise must exist).
            genre (str): Genre of track.
            release_date (str): Release date (ISO 8601).
            play_count (int, optional): Non-negative play count (defaults to 0).
            last_played_at (str, optional): When track was last played (ISO 8601, defaults to "").

        Returns:
            dict:
                success: True if track added, False otherwise.
                message: Success description.
                error: (on failure) Reason it failed.

        Constraints:
            - track_id, artist_id, album_id must be unique in their entity sets.
            - duration must be positive.
            - artist_id must exist.
            - album_id (if not empty) must exist.
            - play_count must be non-negative.
        """
        # Check if track_id is unique
        if track_id in self.tracks:
            return {"success": False, "error": "Track ID already exists."}

        # Check that duration is positive
        if not isinstance(duration, int) or duration <= 0:
            return {"success": False, "error": "Duration must be a positive integer."}

        # Check that artist_id exists
        if artist_id not in self.artists:
            return {"success": False, "error": "Referenced artist_id does not exist."}

        # Check album_id (can be empty if not associated)
        if album_id and (album_id not in self.albums):
            return {"success": False, "error": "Referenced album_id does not exist."}

        # Play count must be non-negative integer
        if not isinstance(play_count, int) or play_count < 0:
            return {"success": False, "error": "Play count must be non-negative integer."}

        # Create track info dictionary
        track_info = {
            "track_id": track_id,
            "title": title,
            "duration": duration,
            "artist_id": artist_id,
            "album_id": album_id,
            "genre": genre,
            "release_date": release_date,
            "play_count": play_count,
            "last_played_at": last_played_at
        }

        # Add new track
        self.tracks[track_id] = track_info

        return {"success": True, "message": f"Track {track_id} added successfully"}

    def edit_track_metadata(self, track_id: str, **updates) -> dict:
        """
        Update information (such as title, genre, album, artist, duration, release_date) for a given track,
        enforcing system constraints.

        Args:
            track_id (str): Unique identifier of the track to update.
            **updates: Fields to update. Allowed keys: 'title', 'genre', 'album_id', 'artist_id', 'release_date', 'duration'

        Returns:
            dict: {
                "success": True,
                "message": "Track metadata updated successfully."
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - track_id must exist in the library.
            - duration must be a positive integer, if updated.
            - artist_id and album_id must reference valid artist/album if updated.
            - Only allowed fields can be updated; play_count and last_played_at are read-only here.
        """
        allowed_fields = {"title", "genre", "album_id", "artist_id", "release_date", "duration"}
    
        if track_id not in self.tracks:
            return { "success": False, "error": "Track does not exist." }
    
        track = self.tracks[track_id]
        for field, value in updates.items():
            if field not in allowed_fields:
                return { "success": False, "error": f"Field '{field}' cannot be updated." }
            if field == "duration":
                if not isinstance(value, int) or value <= 0:
                    return { "success": False, "error": "Duration must be a positive integer." }
            if field == "artist_id":
                if value not in self.artists:
                    return { "success": False, "error": "Artist does not exist." }
            if field == "album_id":
                if value not in self.albums:
                    return { "success": False, "error": "Album does not exist." }
    
        # Passed all checks, perform update
        for field, value in updates.items():
            track[field] = value

        return { "success": True, "message": "Track metadata updated successfully." }

    def delete_track(self, track_id: str) -> dict:
        """
        Remove a track from the system by its unique track_id.

        Args:
            track_id (str): The unique identifier for the track to be deleted.

        Returns:
            dict: On success,
                    {
                        "success": True,
                        "message": "Track <track_id> deleted"
                    }
                  On failure,
                    {
                        "success": False,
                        "error": "Track not found"
                    }

        Constraints:
            - The track_id must exist in the system for deletion.
        """
        if track_id not in self.tracks:
            return { "success": False, "error": "Track not found" }

        del self.tracks[track_id]
        return { "success": True, "message": f"Track {track_id} deleted" }

    def add_new_artist(self, artist_id: str, name: str) -> dict:
        """
        Adds a new artist to the library.

        Args:
            artist_id (str): The unique identifier for the artist (must not duplicate an existing artist).
            name (str): The name of the artist (should be non-empty).

        Returns:
            dict: 
                On success: { "success": True, "message": "Artist added successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - artist_id must be unique (not present in self.artists).
            - artist_id and name must be non-empty.
        """
        if not artist_id or not name:
            return {"success": False, "error": "artist_id and name must be non-empty"}
    
        if artist_id in self.artists:
            return {"success": False, "error": "artist_id already exists"}
    
        self.artists[artist_id] = {
            "artist_id": artist_id,
            "name": name
        }
        return {"success": True, "message": "Artist added successfully."}

    def edit_artist_metadata(self, artist_id: str, **kwargs) -> dict:
        """
        Update artist metadata (currently only 'name') for a given artist.

        Args:
            artist_id (str): Unique identifier of the artist to update.
            **kwargs: Key-value pairs of fields to update (currently only 'name' is allowed).

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the successful update
            }
            or
            {
                "success": False,
                "error": str  # Description of the error encountered
            }

        Constraints:
            - artist_id must exist in the system.
            - Only existing fields (currently only 'name') can be updated.
            - New name (if given) must be non-empty string.
        """
        if artist_id not in self.artists:
            return {"success": False, "error": "Artist ID does not exist."}

        allowed_fields = ["name"]
        if not kwargs:
            return {"success": False, "error": "No fields provided for update."}

        artist = self.artists[artist_id]
        updated_fields = []
        for key, value in kwargs.items():
            if key not in allowed_fields:
                return {"success": False, "error": f"Field '{key}' cannot be updated."}
            if key == "name":
                if not isinstance(value, str) or not value.strip():
                    return {"success": False, "error": "Artist name must be a non-empty string."}
                artist["name"] = value.strip()
                updated_fields.append("name")

        if not updated_fields:
            return {"success": False, "error": "No valid fields updated."}

        return {
            "success": True,
            "message": f"Artist '{artist_id}' updated: {', '.join(updated_fields)}."
        }

    def delete_artist(self, artist_id: str) -> dict:
        """
        Removes an artist from the system.

        Args:
            artist_id (str): The unique ID of the artist to delete.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Artist <artist_id> deleted." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The specified artist_id must exist.
            - Can only delete the artist if no tracks or albums reference this artist.
        """
        # Check if artist exists
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist." }

        # Check if any track references this artist
        for track in self.tracks.values():
            if track['artist_id'] == artist_id:
                return { "success": False, "error": "Cannot delete artist: tracks reference this artist." }

        # Check if any album references this artist
        for album in self.albums.values():
            if album['artist_id'] == artist_id:
                return { "success": False, "error": "Cannot delete artist: albums reference this artist." }

        # Passed checks, safe to delete
        del self.artists[artist_id]
        return { "success": True, "message": f"Artist {artist_id} deleted." }

    def add_new_album(self, album_id: str, title: str, release_date: str, artist_id: str) -> dict:
        """
        Add a new album to the music library with a unique album_id and a valid artist_id.

        Args:
            album_id (str): Unique identifier for the album.
            title (str): Album title.
            release_date (str): Album release date (ISO 8601 format recommended).
            artist_id (str): Identifier of the artist (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Album added (album_id=<album_id>)"
            }
            OR
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - album_id must be unique.
            - artist_id must refer to an existing artist.
        """
        # Check uniqueness of album_id
        if not album_id or album_id in self.albums:
            return { "success": False, "error": "album_id already exists or is invalid" }
        if not artist_id or artist_id not in self.artists:
            return { "success": False, "error": "artist_id does not exist" }
        if not title or not isinstance(title, str):
            return { "success": False, "error": "Invalid album title" }
        if not release_date or not isinstance(release_date, str):
            return { "success": False, "error": "Invalid release date" }

        self.albums[album_id] = {
            "album_id": album_id,
            "title": title,
            "release_date": release_date,
            "artist_id": artist_id
        }

        return { "success": True, "message": f"Album added (album_id={album_id})" }

    def edit_album_metadata(self, album_id: str, **kwargs) -> dict:
        """
        Update album metadata for the given album_id.

        Args:
            album_id (str): The unique identifier of the album to update.
            kwargs: Album fields to update. Only 'title', 'release_date', and 'artist_id' are allowed.

        Returns:
            dict: {
                "success": True,
                "message": "Album metadata updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - album_id must exist in library.
            - Only 'title', 'release_date', and 'artist_id' fields can be updated.
            - artist_id, if updated, must exist in artists.
            - album_id itself cannot be changed.
        """
        # Check if album exists
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist." }

        album = self.albums[album_id]
        allowed_fields = {"title", "release_date", "artist_id"}
        to_update = {}

        # Filter kwargs to allowed fields and collect values to update
        for k, v in kwargs.items():
            if k not in allowed_fields:
                return { "success": False, "error": f"Field '{k}' cannot be updated." }
            to_update[k] = v

        # If attempting to update artist_id: check if the new artist exists
        if "artist_id" in to_update:
            new_artist_id = to_update["artist_id"]
            if new_artist_id not in self.artists:
                return { "success": False, "error": "New artist_id does not exist." }

        # Perform the updates
        for key, value in to_update.items():
            album[key] = value

        # Save the updated album info
        self.albums[album_id] = album

        return { "success": True, "message": "Album metadata updated." }

    def delete_album(self, album_id: str) -> dict:
        """
        Remove an album from the system.

        Args:
            album_id (str): The unique identifier of the album to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Album <album_id> deleted successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        
        Constraints:
            - Album must exist.
            - Any tracks referencing this album should have their album_id cleared (set to empty string).
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album does not exist" }

        # Remove the album
        del self.albums[album_id]

        # Clear album_id from any tracks that referenced this album
        for track in self.tracks.values():
            if track.get("album_id") == album_id:
                track["album_id"] = ""

        return {
            "success": True,
            "message": f"Album {album_id} deleted successfully"
        }


class DigitalMusicLibraryManagementSystem(BaseEnv):
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

    def get_track_by_id(self, **kwargs):
        return self._call_inner_tool('get_track_by_id', kwargs)

    def get_track_duration(self, **kwargs):
        return self._call_inner_tool('get_track_duration', kwargs)

    def list_all_tracks(self, **kwargs):
        return self._call_inner_tool('list_all_tracks', kwargs)

    def search_tracks_by_title(self, **kwargs):
        return self._call_inner_tool('search_tracks_by_title', kwargs)

    def search_tracks_by_artist_id(self, **kwargs):
        return self._call_inner_tool('search_tracks_by_artist_id', kwargs)

    def search_tracks_by_album_id(self, **kwargs):
        return self._call_inner_tool('search_tracks_by_album_id', kwargs)

    def search_tracks_by_genre(self, **kwargs):
        return self._call_inner_tool('search_tracks_by_genre', kwargs)

    def get_artist_by_id(self, **kwargs):
        return self._call_inner_tool('get_artist_by_id', kwargs)

    def list_all_artists(self, **kwargs):
        return self._call_inner_tool('list_all_artists', kwargs)

    def get_album_by_id(self, **kwargs):
        return self._call_inner_tool('get_album_by_id', kwargs)

    def list_all_albums(self, **kwargs):
        return self._call_inner_tool('list_all_albums', kwargs)

    def get_tracks_in_album(self, **kwargs):
        return self._call_inner_tool('get_tracks_in_album', kwargs)

    def get_tracks_by_release_date_range(self, **kwargs):
        return self._call_inner_tool('get_tracks_by_release_date_range', kwargs)

    def get_playback_statistics_for_track(self, **kwargs):
        return self._call_inner_tool('get_playback_statistics_for_track', kwargs)

    def increment_track_play_count(self, **kwargs):
        return self._call_inner_tool('increment_track_play_count', kwargs)

    def add_new_track(self, **kwargs):
        return self._call_inner_tool('add_new_track', kwargs)

    def edit_track_metadata(self, **kwargs):
        return self._call_inner_tool('edit_track_metadata', kwargs)

    def delete_track(self, **kwargs):
        return self._call_inner_tool('delete_track', kwargs)

    def add_new_artist(self, **kwargs):
        return self._call_inner_tool('add_new_artist', kwargs)

    def edit_artist_metadata(self, **kwargs):
        return self._call_inner_tool('edit_artist_metadata', kwargs)

    def delete_artist(self, **kwargs):
        return self._call_inner_tool('delete_artist', kwargs)

    def add_new_album(self, **kwargs):
        return self._call_inner_tool('add_new_album', kwargs)

    def edit_album_metadata(self, **kwargs):
        return self._call_inner_tool('edit_album_metadata', kwargs)

    def delete_album(self, **kwargs):
        return self._call_inner_tool('delete_album', kwargs)

