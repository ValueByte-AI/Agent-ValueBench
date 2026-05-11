# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
import re



class SongInfo(TypedDict):
    song_id: str
    title: str
    release_date: str  # ISO date string
    duration: float
    genre: str
    popularity: float
    album_id: str

class ArtistInfo(TypedDict):
    artist_id: str
    name: str
    bio: str
    popularity: float

class AlbumInfo(TypedDict):
    album_id: str
    title: str
    release_date: str  # ISO date string
    cover_image: str
    artist_id: str

class SongArtistRelationshipInfo(TypedDict):
    song_id: str
    artist_id: str
    role: str  # e.g., "primary artist", "featured artist"

class UserInfo(TypedDict):
    _id: str
    username: str
    account_status: str
    search_history: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Songs catalog: {song_id: SongInfo}
        self.songs: Dict[str, SongInfo] = {}

        # Artists registry: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}

        # Albums registry: {album_id: AlbumInfo}
        self.albums: Dict[str, AlbumInfo] = {}

        # Song-Artist relationships: list of SongArtistRelationshipInfo
        self.song_artist_relationships: List[SongArtistRelationshipInfo] = []

        # Users registry: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # --- Constraints (documented for reference) ---
        # - Each song must be associated with at least one artist.
        # - release_date for songs and albums must be a valid date and used for sorting.
        # - Artist names are not unique; disambiguation may be required.
        # - A song can belong to only one album, but an artist can be associated with multiple songs and albums.
        # - Search and sorting functionalities must access up-to-date metadata.

    def search_artist_by_name(self, name: str) -> dict:
        """
        Search for artists by artist name (supports partial and case-insensitive matches).
        Returns a list of ArtistInfo dicts with artist_id and associated metadata.

        Args:
            name (str): Full or partial name of the artist to search (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ArtistInfo]  # List of matching artists, can be empty if no matches
            }
        """
        # Prepare for case-insensitive, partial match search
        keyword = name.strip().lower()
        result = [
            artist_info for artist_info in self.artists.values()
            if keyword in artist_info["name"].lower()
        ]

        return {
            "success": True,
            "data": result
        }

    def get_artist_by_id(self, artist_id: str) -> dict:
        """
        Retrieve detailed metadata for a given artist_id.

        Args:
            artist_id (str): Unique identifier of the artist.

        Returns:
            dict:
                If artist exists:
                    {
                        "success": True,
                        "data": ArtistInfo
                    }
                If artist does not exist:
                    {
                        "success": False,
                        "error": "Artist not found"
                    }
        Constraints:
            - artist_id must exist in the platform's artist registry.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }
        return { "success": True, "data": artist }

    def list_songs_by_artist_id(self, artist_id: str, role: str = None) -> dict:
        """
        List all songs associated with an artist via SongArtistRelationship.
        Optionally filter by role (e.g., "primary artist", "featured artist").

        Args:
            artist_id (str): The ID of the artist to query.
            role (str, optional): Filter by role in the relationship. If None, include all roles.

        Returns:
            dict: {
                "success": True,
                "data": [SongInfo, ...]  # List of associated song metadata (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., "Artist does not exist"
            }

        Constraints:
            - The artist_id must exist in the artists dictionary.
            - Any valid relationship matching the artist_id is considered.
            - Only include songs existing in the current catalog.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist" }

        # Collect song_ids for this artist (optionally filter by role)
        if role is not None:
            song_ids = [
                rel["song_id"]
                for rel in self.song_artist_relationships
                if rel["artist_id"] == artist_id and rel["role"] == role
            ]
        else:
            song_ids = [
                rel["song_id"]
                for rel in self.song_artist_relationships
                if rel["artist_id"] == artist_id
            ]
        # Deduplicate in case of multiple relationships (unlikely but safe)
        song_ids = list(set(song_ids))

        # Get metadata for songs found in the catalog
        songs = [
            self.songs[song_id]
            for song_id in song_ids
            if song_id in self.songs
        ]

        return { "success": True, "data": songs }

    def get_song_artist_relationships_by_artist_id(self, artist_id: str) -> dict:
        """
        Retrieve all SongArtistRelationship entries for a specific artist.

        Args:
            artist_id (str): The ID of the artist for whom relationships are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[SongArtistRelationshipInfo]  # All matching relationships (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # If artist does not exist
            }

        Constraints:
            - artist_id must exist in the system.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        relationships = [
            rel for rel in self.song_artist_relationships
            if rel["artist_id"] == artist_id
        ]

        return { "success": True, "data": relationships }

    def get_song_by_id(self, song_id: str) -> dict:
        """
        Fetch full song metadata from the catalog for a given song_id.

        Args:
            song_id (str): The unique identifier of the song to retrieve.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": SongInfo
                }
                On failure: {
                    "success": False,
                    "error": "Song not found"
                }

        Constraints:
            - song_id must exist in the catalog.
        """
        song = self.songs.get(song_id)
        if song is None:
            return {"success": False, "error": "Song not found"}
        return {"success": True, "data": song}

    def get_songs_by_album_id(self, album_id: str) -> dict:
        """
        List all songs in a specified album.

        Args:
            album_id (str): The album's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[SongInfo]  # songs in the album, empty if none found
            }
            or
            {
                "success": False,
                "error": str  # error description, e.g., album not found
            }
        Constraints:
            - album_id must exist in albums registry.
        """
        if album_id not in self.albums:
            return { "success": False, "error": "Album not found" }

        songs_in_album = [
            song_info for song_info in self.songs.values()
            if song_info["album_id"] == album_id
        ]

        return { "success": True, "data": songs_in_album }

    def get_album_by_id(self, album_id: str) -> dict:
        """
        Fetch full album metadata by album_id.
    
        Args:
            album_id (str): The unique ID of the album to retrieve.
    
        Returns:
            dict: {
                "success": True,
                "data": AlbumInfo,      # Album metadata if found
            }
            or
            {
                "success": False,
                "error": str           # "Album not found"
            }
    
        Constraints:
            - Returns only if album_id exists.
        """
        if album_id not in self.albums:
            return {"success": False, "error": "Album not found"}
    
        return {"success": True, "data": self.albums[album_id]}

    def list_albums_by_artist_id(self, artist_id: str) -> dict:
        """
        List all albums associated with the specified artist.

        Args:
            artist_id (str): ID of the artist whose albums are to be listed.

        Returns:
            dict:
                "success": True and "data": List[AlbumInfo] upon successful retrieval (may be empty if none)
                OR
                "success": False and "error": str if artist does not exist
        Constraints:
            - artist_id must exist in the platform.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist" }

        albums = [
            album_info for album_info in self.albums.values()
            if album_info["artist_id"] == artist_id
        ]
        return { "success": True, "data": albums }

    def search_song_by_title(
        self, 
        title: str, 
        artist_id: str = None, 
        album_id: str = None, 
        genre: str = None
    ) -> dict:
        """
        Search for songs by their title, with optional filtering by artist, album, or genre.

        Args:
            title (str): The song title or partial title to search for (case-insensitive, substring match).
            artist_id (str, optional): If provided, only include songs associated with this artist.
            album_id (str, optional): If provided, only include songs from this album.
            genre (str, optional): If provided, only include songs of this genre.

        Returns:
            dict:
                If successful,
                    {
                        "success": True,
                        "data": List[SongInfo],  # list may be empty if no matches found
                    }
                If failure,
                    {
                        "success": False,
                        "error": str,
                    }
        Constraints:
            - Songs must always be associated with at least one artist.
            - All filters are optional.
            - Search is case-insensitive and substring-based.
        """
        if title is None:
            return { "success": False, "error": "Title search query must be provided." }

        # Filter the songs by substring match (case-insensitive)
        matched_songs = [
            song for song in self.songs.values()
            if title.lower() in song["title"].lower()
        ]

        # Filter by genre if provided
        if genre is not None:
            matched_songs = [song for song in matched_songs if song["genre"].lower() == genre.lower()]

        # Filter by album_id if provided
        if album_id is not None:
            matched_songs = [song for song in matched_songs if song["album_id"] == album_id]

        # Filter by artist_id if provided
        if artist_id is not None:
            # Build a lookup: song_id => True if the song has this artist
            songs_with_artist = set(
                rel["song_id"] for rel in self.song_artist_relationships
                if rel["artist_id"] == artist_id
            )
            matched_songs = [song for song in matched_songs if song["song_id"] in songs_with_artist]

        return { "success": True, "data": matched_songs }

    def sort_songs_by_release_date(self, song_ids: list, order: str) -> dict:
        """
        Sort the given list of song IDs by their release_date (ascending or descending).

        Args:
            song_ids (list of str): List of song IDs to be sorted.
            order (str): 'asc' for earliest first, 'desc' for latest first. Case-insensitive.

        Returns:
            dict: 
                - On success: { "success": True, "data": [SongInfo, ...] } (sorted list of song metadata)
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - All song_ids must exist.
            - 'order' must be 'asc' or 'desc' (case-insensitive).
            - release_date must be parsed and sorted as dates.
        """

        # Validate order
        order = order.lower()
        if order not in ("asc", "desc"):
            return { "success": False, "error": "Invalid order parameter; must be 'asc' or 'desc'." }
    
        # Validate song IDs and collect SongInfo
        songs_to_sort = []
        invalid_ids = []
        for sid in song_ids:
            song = self.songs.get(sid)
            if not song:
                invalid_ids.append(sid)
            else:
                songs_to_sort.append(song)
        if invalid_ids:
            return { "success": False, "error": f"Invalid song_id(s): {', '.join(invalid_ids)}" }

        # Helper for sorting: convert ISO date string to datetime
        def parse_date(song):
            try:
                return datetime.datetime.fromisoformat(song["release_date"])
            except Exception:
                # Treat invalid date as the minimum (for asc), or maximum (for desc)
                return datetime.datetime.min if order == "asc" else datetime.datetime.max

        reverse = order == "desc"
        sorted_songs = sorted(songs_to_sort, key=parse_date, reverse=reverse)

        return { "success": True, "data": sorted_songs }

    def get_latest_song_by_artist_id(self, artist_id: str) -> dict:
        """
        Retrieve the most recently released song for the specified artist.

        Args:
            artist_id (str): The unique id of the artist.

        Returns:
            dict: {
                "success": True,
                "data": SongInfo    # Song metadata of most recently released song
            }
            or
            {
                "success": False,
                "error": str        # Reason for failure ("Artist not found", "Artist has no songs")
            }

        Constraints:
            - Artist must exist in the platform.
            - If artist has no associated songs, operation fails gracefully.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Find all song_ids for this artist from song_artist_relationships
        song_ids = [
            rel["song_id"]
            for rel in self.song_artist_relationships
            if rel["artist_id"] == artist_id
        ]
        # Remove duplicates, if any
        song_ids = list(set(song_ids))

        # Get SongInfo for those song_ids, ignoring missing or removed songs
        songs = [self.songs[sid] for sid in song_ids if sid in self.songs]

        if not songs:
            return { "success": False, "error": "Artist has no songs" }

        # Sort by release_date descending (ISO date string supports this)
        songs_sorted = sorted(songs, key=lambda s: s["release_date"], reverse=True)
        latest_song = songs_sorted[0]

        return { "success": True, "data": latest_song }

    def list_all_genres(self) -> dict:
        """
        Retrieve a list of all unique, non-blank music genres available on the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Unique genre names (may be empty if no songs or no genres present)
            }
        """
        # Gather all unique, non-blank genres from songs
        genres = set()
        for song in self.songs.values():
            genre = (song.get("genre") or "").strip()
            if genre:
                genres.add(genre)
        return {
            "success": True,
            "data": sorted(genres)
        }

    def get_song_popularity(self, song_id: str) -> dict:
        """
        Retrieve the current popularity metric for a given song.

        Args:
            song_id (str): The unique identifier of the song.

        Returns:
            dict: {
                "success": True,
                "data": float  # Popularity metric of the song
            }
            or
            {
                "success": False,
                "error": str  # Error message if song is not found
            }

        Constraints:
            - song_id must refer to an existing song in the catalog.
        """
        song = self.songs.get(song_id)
        if not song:
            return { "success": False, "error": "Song not found" }
        return { "success": True, "data": song["popularity"] }

    def get_album_release_date(self, album_id: str) -> dict:
        """
        Retrieve the release date for a specified album.

        Args:
            album_id (str): The unique identifier for the album.

        Returns:
            dict: 
             - If the album exists:
                 { "success": True, "data": str }  # data is the album release date (ISO string)
             - If the album does not exist:
                 { "success": False, "error": "Album not found" }

        Constraints:
            - The specified album_id must exist in the album registry.
        """
        album = self.albums.get(album_id)
        if not album:
            return { "success": False, "error": "Album not found" }
        return { "success": True, "data": album["release_date"] }

    def get_artist_popularity(self, artist_id: str) -> dict:
        """
        Retrieve the popularity metric for a given artist.

        Args:
            artist_id (str): Unique identifier for the artist.

        Returns:
            dict: 
                On success: {"success": True, "data": <popularity (float)> }
                On failure: {"success": False, "error": "Artist not found"}

        Constraints:
            - artist_id must exist in the artist registry.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }

        return { "success": True, "data": artist["popularity"] }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user info by username, including search history and account status.

        Args:
            username (str): The username to look up.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }
    
        Constraints:
            - Username comparison is case-sensitive.
            - Returns complete UserInfo (including search_history and account_status).
        """
        if not username:
            return { "success": False, "error": "User not found" }
    
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_search_history(self, username: str) -> dict:
        """
        Retrieve a user's search history (list of search query strings).

        Args:
            username (str): The username of the user whose history is queried.

        Returns:
            dict: 
            {
                "success": True,
                "data": List[str]  # List of search query strings, possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g. user not found
            }
    
        Constraints:
            - Username must exist in the platform.
        """
        user_info = None
        for u in self.users.values():
            if u["username"] == username:
                user_info = u
                break
        if user_info is None:
            return { "success": False, "error": "User does not exist" }
        return { "success": True, "data": user_info.get("search_history", []) }

    def update_song_metadata(
        self,
        song_id: str,
        title: str = None,
        release_date: str = None,
        genre: str = None,
        popularity: float = None,
        duration: float = None,
        album_id: str = None
    ) -> dict:
        """
        Edit metadata of a song by its song_id.
    
        Args:
            song_id (str): The ID of the song to update.
            title (str, optional): New title.
            release_date (str, optional): New release date (ISO format, "YYYY-MM-DD").
            genre (str, optional): New genre.
            popularity (float, optional): New popularity score.
            duration (float, optional): New song duration (seconds, float).
            album_id (str, optional): New album ID to associate song with.

        Returns:
            dict, with keys:
                - success (bool): True if operation succeeded, else False.
                - message (str): Success message if successful.
                - error (str): Error message if unsuccessful.

        Constraints:
            - song_id must exist.
            - release_date (if given) must be a valid ISO date.
            - album_id (if given) must exist.
            - At least one valid field must be provided to update.
        """

        if song_id not in self.songs:
            return {"success": False, "error": "Song does not exist"}

        song = self.songs[song_id]
        fields_to_update = {}

        if title is not None:
            fields_to_update["title"] = title

        if release_date is not None:
            try:
                # Accept YYYY-MM-DD only
                datetime.datetime.strptime(release_date, "%Y-%m-%d")
                fields_to_update["release_date"] = release_date
            except Exception:
                return {"success": False, "error": "Invalid release_date format"}

        if genre is not None:
            fields_to_update["genre"] = genre

        if popularity is not None:
            try:
                popularity_val = float(popularity)
                fields_to_update["popularity"] = popularity_val
            except Exception:
                return {"success": False, "error": "Invalid popularity value"}

        if duration is not None:
            try:
                duration_val = float(duration)
                fields_to_update["duration"] = duration_val
            except Exception:
                return {"success": False, "error": "Invalid duration value"}

        if album_id is not None:
            if album_id not in self.albums:
                return {"success": False, "error": "Album does not exist"}
            fields_to_update["album_id"] = album_id

        if not fields_to_update:
            return {"success": False, "error": "No valid fields to update"}

        # Update the fields atomically
        for key, value in fields_to_update.items():
            song[key] = value

        return {"success": True, "message": "Song metadata updated successfully."}

    def update_artist_metadata(self, artist_id: str, name: str = None, bio: str = None, popularity: float = None) -> dict:
        """
        Edit artist info (name, bio, popularity).
    
        Args:
            artist_id (str): The ID of the artist to update.
            name (str, optional): New artist name (if updating).
            bio (str, optional): New artist bio (if updating).
            popularity (float, optional): New popularity score (if updating).
    
        Returns:
            dict:
                - success (bool): Operation status.
                - message (str): Success message if operation succeeded.
                - error (str): Error message if failed.
    
        Constraints:
            - artist_id must exist in the registry.
            - At least one of name, bio, or popularity must be provided.
            - If popularity is given, it must be a float >= 0.
        """
        # Check artist_id exists
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist does not exist" }
    
        if name is None and bio is None and popularity is None:
            return { "success": False, "error": "No fields provided to update" }
    
        artist = self.artists[artist_id]
        changed = False

        if name is not None:
            artist["name"] = name
            changed = True
        if bio is not None:
            artist["bio"] = bio
            changed = True
        if popularity is not None:
            # Check type and validity
            try:
                pop_val = float(popularity)
                if pop_val < 0:
                    return { "success": False, "error": "Popularity cannot be negative" }
                artist["popularity"] = pop_val
                changed = True
            except Exception:
                return { "success": False, "error": "Popularity must be a float" }
    
        if not changed:
            return { "success": False, "error": "No valid updates performed" }
    
        return { "success": True, "message": "Artist metadata updated." }

    def update_album_metadata(
        self,
        album_id: str,
        title: str = None,
        release_date: str = None,
        cover_image: str = None,
        artist_id: str = None
    ) -> dict:
        """
        Edit album details such as title, cover image, release_date, and artist_id.

        Args:
            album_id (str): The unique ID of the album to update.
            title (str, optional): New title for the album.
            release_date (str, optional): New release date (ISO date string).
            cover_image (str, optional): New cover image reference.
            artist_id (str, optional): New artist_id to associate with this album.

        Returns:
            dict: {
                "success": True,
                "message": "Album metadata updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - album_id must exist in the albums registry.
            - If artist_id is updated, it must exist in the artists registry.
            - If release_date is updated, it should be a valid ISO date string.
            - At least one field must be specified for update.
        """

        # Check album exists
        if album_id not in self.albums:
            return {"success": False, "error": "Album does not exist"}

        # No fields provided
        if all(arg is None for arg in [title, release_date, cover_image, artist_id]):
            return {"success": False, "error": "No metadata fields specified for update"}

        # Validate artist_id if updating
        if artist_id is not None and artist_id not in self.artists:
            return {"success": False, "error": "Artist does not exist"}

        # Validate release_date if updating (sanity check for ISO format)
        if release_date is not None:
            try:
                datetime.date.fromisoformat(release_date)
            except Exception:
                return {"success": False, "error": "release_date must be a valid ISO date string (YYYY-MM-DD)"}

        album = self.albums[album_id]
        if title is not None:
            album["title"] = title
        if release_date is not None:
            album["release_date"] = release_date
        if cover_image is not None:
            album["cover_image"] = cover_image
        if artist_id is not None:
            album["artist_id"] = artist_id

        # Save back (not strictly necessary for dict in-place, but explicit)
        self.albums[album_id] = album

        return {"success": True, "message": "Album metadata updated successfully"}

    def add_song(
        self,
        song_info: SongInfo,
        artist_relationships: List[SongArtistRelationshipInfo]
    ) -> dict:
        """
        Add a new song to the catalog, ensuring it is associated with at least one artist.

        Args:
            song_info (SongInfo): The metadata for the new song (all fields required).
            artist_relationships (List[SongArtistRelationshipInfo]): List of artist associations
                (each must match the new song's song_id and reference valid artist_id).

        Returns:
            dict: {
                "success": True,
                "message": "Song added to catalog and associated with artists."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - song_id must be unique.
            - At least one artist association must be provided, and all artist_ids must exist.
            - album_id (if not empty) must exist.
            - release_date must be a valid ISO format date.
            - Each relationship's song_id must match the song being added.
        """

        # Check for required fields in song_info
        required_song_fields = [
            "song_id", "title", "release_date", "duration", "genre", "popularity", "album_id"
        ]
        for field in required_song_fields:
            if field not in song_info:
                return {"success": False, "error": f"Missing field in song_info: {field}"}

        song_id = song_info["song_id"]
        album_id = song_info["album_id"]
        release_date = song_info["release_date"]

        # song_id must be unique
        if song_id in self.songs:
            return {"success": False, "error": "Song with this song_id already exists."}

        # Check release_date is valid ISO string
        try:
            datetime.datetime.fromisoformat(release_date)
        except Exception:
            return {"success": False, "error": "release_date is not a valid ISO date string."}

        # album_id must exist (unless explicitly allowed to be empty/None)
        if album_id and album_id not in self.albums:
            return {"success": False, "error": "Referenced album_id does not exist."}

        # At least one artist association
        if not artist_relationships or not isinstance(artist_relationships, list):
            return {"success": False, "error": "At least one artist association must be provided."}

        # Validate artist associations
        for assoc in artist_relationships:
            if assoc.get("song_id") != song_id:
                return {"success": False, "error": "All artist associations must reference the correct song_id."}
            artist_id = assoc.get("artist_id")
            if not artist_id or artist_id not in self.artists:
                return {"success": False, "error": f"Artist_id '{artist_id}' in associations does not exist."}
            # Optionally: check role is present and non-empty
            if not assoc.get("role") or not isinstance(assoc.get("role"), str):
                return {"success": False, "error": "Each association must include a valid, non-empty 'role'."}

        # Add the song
        self.songs[song_id] = dict(song_info)

        # Add the artist-song associations
        for assoc in artist_relationships:
            self.song_artist_relationships.append(dict(assoc))

        return {
            "success": True,
            "message": "Song added to catalog and associated with artists."
        }

    def add_artist(
        self,
        artist_id: str,
        name: str,
        bio: str,
        popularity: float
    ) -> dict:
        """
        Add a new artist entry to the platform.

        Args:
            artist_id (str): Unique identifier for the artist.
            name (str): Artist's name (need not be unique).
            bio (str): Short biography or description.
            popularity (float): Popularity score.

        Returns:
            dict: {
                "success": True,
                "message": "Artist added successfully."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - artist_id must be unique (not already in self.artists).
            - All fields must be provided and be of correct type.
        """
        # Uniqueness check
        if not artist_id or artist_id in self.artists:
            return {"success": False, "error": "Artist with this ID already exists or invalid artist_id."}

        # Validate required fields
        if (name is None) or (bio is None):
            return {"success": False, "error": "Missing required field(s) name or bio."}

        try:
            pop_val = float(popularity)
        except Exception:
            return {"success": False, "error": "Invalid popularity value; must be a float."}

        self.artists[artist_id] = {
            "artist_id": artist_id,
            "name": name,
            "bio": bio,
            "popularity": pop_val
        }

        return {"success": True, "message": "Artist added successfully."}

    def add_album(self, album_id: str, title: str, release_date: str, cover_image: str, artist_id: str) -> dict:
        """
        Create a new album entity, associated with a given artist.

        Args:
            album_id (str): Unique identifier for the new album (must not already exist).
            title (str): Album title.
            release_date (str): Album release date (ISO date string).
            cover_image (str): Cover image URL or identifier.
            artist_id (str): The artist's unique id the album is associated with (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Album <album_id> created successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error.
            }

        Constraints:
            - The album_id must not already exist.
            - The artist_id must exist in the platform.
            - The release_date must be a valid, non-empty ISO date string.
        """
        if not album_id or album_id in self.albums:
            return {"success": False, "error": "Album id already exists or is invalid."}
        if not artist_id or artist_id not in self.artists:
            return {"success": False, "error": "Artist id does not exist."}
        # Basic ISO date validation (YYYY-MM-DD)
        if not isinstance(release_date, str) or not re.match(r"\d{4}-\d{2}-\d{2}", release_date):
            return {"success": False, "error": "Invalid release_date format. Expected YYYY-MM-DD."}

        new_album: AlbumInfo = {
            "album_id": album_id,
            "title": title,
            "release_date": release_date,
            "cover_image": cover_image,
            "artist_id": artist_id,
        }
        self.albums[album_id] = new_album
        return {"success": True, "message": f"Album {album_id} created successfully."}

    def associate_song_with_artist(self, song_id: str, artist_id: str, role: str) -> dict:
        """
        Add a relationship entry between a song and an artist, specifying the role.

        Args:
            song_id (str): ID of the song.
            artist_id (str): ID of the artist.
            role (str): Role string (e.g., "primary artist", "featured artist")

        Returns:
            dict: {
                "success": True,
                "message": "Relationship added successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - song_id must exist in self.songs
            - artist_id must exist in self.artists
            - The specific (song_id, artist_id, role) relationship must not already exist
        """
        # Check if song exists
        if song_id not in self.songs:
            return { "success": False, "error": "Song ID does not exist" }
        # Check if artist exists
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist ID does not exist" }
        # Check for duplicate relationship
        for rel in self.song_artist_relationships:
            if rel["song_id"] == song_id and rel["artist_id"] == artist_id and rel["role"] == role:
                return { "success": False, "error": "Relationship already exists" }
        # Add the relationship
        new_rel = {
            "song_id": song_id,
            "artist_id": artist_id,
            "role": role
        }
        self.song_artist_relationships.append(new_rel)
        return { "success": True, "message": "Relationship added successfully" }

    def remove_song(self, song_id: str) -> dict:
        """
        Delete a song from the catalog and remove its artist relationships.

        Args:
            song_id (str): The unique identifier for the song to remove.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Song and its relationships removed successfully."
                    }
                On failure (song does not exist):
                    {
                        "success": False,
                        "error": "Song not found."
                    }

        Constraints:
            - Removes SongInfo entry from the catalog.
            - Removes all SongArtistRelationship entries for this song_id.
        """
        if song_id not in self.songs:
            return { "success": False, "error": "Song not found." }

        # Remove song from catalog
        del self.songs[song_id]

        # Remove all song-artist relationships for that song
        before_count = len(self.song_artist_relationships)
        self.song_artist_relationships = [
            rel for rel in self.song_artist_relationships
            if rel['song_id'] != song_id
        ]
        # Optionally: Remove from other indices/caches if implemented

        return { "success": True, "message": "Song and its relationships removed successfully." }

    def remove_artist(self, artist_id: str) -> dict:
        """
        Remove an artist from the platform and dissociate from all songs and albums.

        Args:
            artist_id (str): Artist ID to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Artist <artist_id> removed and dissociated from all songs/albums."
            } OR {
                "success": False,
                "error": <error-reason>
            }

        Constraints:
            - Cannot remove an artist if their removal would leave any song without at least one artist.
            - All SongArtistRelationships with this artist are removed.
            - For all albums where artist_id matches, dissociate by setting artist_id to empty string.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist not found" }

        # Find all song_ids this artist is associated with
        songs_to_check = set(
            rel['song_id'] for rel in self.song_artist_relationships
            if rel['artist_id'] == artist_id
        )

        # For each of those songs, make sure removing this artist doesn't leave the song orphaned
        orphaned_songs = []
        for song_id in songs_to_check:
            # artists associated with this song, except the artist we want to remove
            associated_artists = [
                rel['artist_id'] for rel in self.song_artist_relationships
                if rel['song_id'] == song_id and rel['artist_id'] != artist_id
            ]
            if not associated_artists:
                song_title = self.songs[song_id]['title'] if song_id in self.songs else song_id
                orphaned_songs.append(song_title)

        if orphaned_songs:
            return {
                "success": False,
                "error": f"Cannot remove artist; would orphan songs: {orphaned_songs}"
            }

        # Remove SongArtistRelationships for this artist
        self.song_artist_relationships = [
            rel for rel in self.song_artist_relationships
            if rel['artist_id'] != artist_id
        ]

        # Dissociate artist from any albums (set to empty string)
        for album in self.albums.values():
            if album['artist_id'] == artist_id:
                album['artist_id'] = ''

        # Remove artist from artists registry
        del self.artists[artist_id]

        return {
            "success": True,
            "message": f"Artist {artist_id} removed and dissociated from all songs/albums."
        }

    def remove_album(self, album_id: str) -> dict:
        """
        Remove an album by its album_id and dissociate all contained songs.
        Also removes SongArtistRelationships associated with those songs.

        Args:
            album_id (str): The ID of the album to remove.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of removal
            }
            OR
            {
                "success": False,
                "error": str     # Error reason
            }

        Constraints:
            - The album must exist.
            - All songs belonging to this album are removed.
            - Associated entries in song_artist_relationships are also removed.
        """
        if album_id not in self.albums:
            return { "success": False, "error": f"Album '{album_id}' does not exist." }
    
        # Identify all song IDs belonging to this album
        songs_to_remove = [song_id for song_id, info in self.songs.items()
                           if info["album_id"] == album_id]
    
        # Remove those songs from the songs dictionary
        for song_id in songs_to_remove:
            self.songs.pop(song_id, None)
            # Remove any relationships for these songs
            self.song_artist_relationships = [
                rel for rel in self.song_artist_relationships 
                if rel["song_id"] != song_id
            ]
    
        # Finally, remove the album itself
        self.albums.pop(album_id, None)
    
        return {
            "success": True,
            "message": f"Album '{album_id}' and all associated songs removed."
        }

    def update_user_search_history(
        self, 
        user_id: str, 
        add_entry: str = None, 
        add_entries: list = None, 
        clear: bool = False
    ) -> dict:
        """
        Add (append) new entries or clear a user's search history.

        Args:
            user_id (str): Identifier for the user whose history is to be updated.
            add_entry (str, optional): Single search query to be appended.
            add_entries (list of str, optional): Multiple search queries to be appended.
            clear (bool, optional): If True, search history is cleared before any additions. Default is False.

        Returns:
            dict: {
                "success": True,
                "message": "User search history updated.",
            }
            or 
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - If neither add_entry/add_entries nor clear is passed, returns error.
            - If both clear and add_* are passed, performs clear before additions.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }

        # Check what action(s) were requested
        to_add = []

        if add_entry is not None:
            if isinstance(add_entry, str) and add_entry.strip():
                to_add.append(add_entry.strip())
        if add_entries is not None and isinstance(add_entries, list):
            to_add.extend([s.strip() for s in add_entries if isinstance(s, str) and s.strip()])

        if not clear and not to_add:
            return { "success": False, "error": "No update action specified" }

        # Clear history if requested
        if clear:
            user["search_history"] = []

        # Append new entries
        if to_add:
            user["search_history"].extend(to_add)

        return { "success": True, "message": "User search history updated." }


class OnlineMusicStreamingPlatform(BaseEnv):
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

    def search_artist_by_name(self, **kwargs):
        return self._call_inner_tool('search_artist_by_name', kwargs)

    def get_artist_by_id(self, **kwargs):
        return self._call_inner_tool('get_artist_by_id', kwargs)

    def list_songs_by_artist_id(self, **kwargs):
        return self._call_inner_tool('list_songs_by_artist_id', kwargs)

    def get_song_artist_relationships_by_artist_id(self, **kwargs):
        return self._call_inner_tool('get_song_artist_relationships_by_artist_id', kwargs)

    def get_song_by_id(self, **kwargs):
        return self._call_inner_tool('get_song_by_id', kwargs)

    def get_songs_by_album_id(self, **kwargs):
        return self._call_inner_tool('get_songs_by_album_id', kwargs)

    def get_album_by_id(self, **kwargs):
        return self._call_inner_tool('get_album_by_id', kwargs)

    def list_albums_by_artist_id(self, **kwargs):
        return self._call_inner_tool('list_albums_by_artist_id', kwargs)

    def search_song_by_title(self, **kwargs):
        return self._call_inner_tool('search_song_by_title', kwargs)

    def sort_songs_by_release_date(self, **kwargs):
        return self._call_inner_tool('sort_songs_by_release_date', kwargs)

    def get_latest_song_by_artist_id(self, **kwargs):
        return self._call_inner_tool('get_latest_song_by_artist_id', kwargs)

    def list_all_genres(self, **kwargs):
        return self._call_inner_tool('list_all_genres', kwargs)

    def get_song_popularity(self, **kwargs):
        return self._call_inner_tool('get_song_popularity', kwargs)

    def get_album_release_date(self, **kwargs):
        return self._call_inner_tool('get_album_release_date', kwargs)

    def get_artist_popularity(self, **kwargs):
        return self._call_inner_tool('get_artist_popularity', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_search_history(self, **kwargs):
        return self._call_inner_tool('get_user_search_history', kwargs)

    def update_song_metadata(self, **kwargs):
        return self._call_inner_tool('update_song_metadata', kwargs)

    def update_artist_metadata(self, **kwargs):
        return self._call_inner_tool('update_artist_metadata', kwargs)

    def update_album_metadata(self, **kwargs):
        return self._call_inner_tool('update_album_metadata', kwargs)

    def add_song(self, **kwargs):
        return self._call_inner_tool('add_song', kwargs)

    def add_artist(self, **kwargs):
        return self._call_inner_tool('add_artist', kwargs)

    def add_album(self, **kwargs):
        return self._call_inner_tool('add_album', kwargs)

    def associate_song_with_artist(self, **kwargs):
        return self._call_inner_tool('associate_song_with_artist', kwargs)

    def remove_song(self, **kwargs):
        return self._call_inner_tool('remove_song', kwargs)

    def remove_artist(self, **kwargs):
        return self._call_inner_tool('remove_artist', kwargs)

    def remove_album(self, **kwargs):
        return self._call_inner_tool('remove_album', kwargs)

    def update_user_search_history(self, **kwargs):
        return self._call_inner_tool('update_user_search_history', kwargs)

