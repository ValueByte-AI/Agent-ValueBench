# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class PlaylistTrackEntryInfo(TypedDict):
    playlist_id: str
    track_id: str
    position: int
    date_added: str
    added_by: str  # user_id

class PlaylistInfo(TypedDict):
    playlist_id: str
    title: str
    description: str
    creation_date: str
    owner_id: str
    visibility: str    # e.g., 'public', 'private'
    shared_with: List[str]  # list of user_ids
    track_entries: List[PlaylistTrackEntryInfo]  # ordered

class TrackInfo(TypedDict):
    track_id: str
    title: str
    artist: str
    album: str
    duration: float  # seconds
    genre: str
    release_date: str
    track_metadata: dict

class UserInfo(TypedDict):
    user_id: str
    username: str
    email: str
    account_status: str
    playlists: List[str]  # playlist_ids
    library: List[str]    # track_ids

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for music streaming playlist management.
        """

        # Playlists: {playlist_id: PlaylistInfo}
        self.playlists: Dict[str, PlaylistInfo] = {}

        # Tracks: {track_id: TrackInfo}
        self.tracks: Dict[str, TrackInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each playlist has a unique playlist_id.
        # - Tracks may appear in multiple playlists and in multiple positions within a playlist.
        # - Only users with appropriate permissions can retrieve or modify private playlists.
        # - The ordering of tracks in a playlist is preserved.
        # - Metadata for both playlists and tracks is fully retrievable and updatable.

    def get_playlist_metadata(self, playlist_id: str) -> dict:
        """
        Retrieve playlist metadata, including the standard fields
        (playlist_id, title, description, owner, creation date, visibility,
        shared_with, and track_count) plus any additional playlist-level
        metadata stored alongside the playlist record.

        Args:
            playlist_id (str): The unique identifier of the playlist.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "playlist_id": str,
                    "title": str,
                    "description": str,
                    "owner_id": str,
                    "creation_date": str,
                    "visibility": str,
                    "shared_with": List[str],
                    "track_count": int,
                    ...additional playlist metadata fields...
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The playlist_id must exist in the system.
        """

        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return { "success": False, "error": "Playlist does not exist" }

        metadata = {
            "playlist_id": playlist["playlist_id"],
            "title": playlist["title"],
            "description": playlist["description"],
            "owner_id": playlist["owner_id"],
            "creation_date": playlist["creation_date"],
            "visibility": playlist["visibility"],
            "shared_with": copy.deepcopy(playlist["shared_with"]),
            "track_count": len(playlist.get("track_entries", []))
        }

        for key, value in playlist.items():
            if key in metadata or key == "track_entries":
                continue
            metadata[key] = copy.deepcopy(value)

        return { "success": True, "data": metadata }

    def get_playlist_track_entries(self, playlist_id: str) -> dict:
        """
        Retrieve the ordered list of track entry descriptors for the specified playlist.

        Args:
            playlist_id (str): The unique playlist identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[PlaylistTrackEntryInfo],  # Ordered list of track entry descriptors
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. playlist not found
            }

        Constraints:
            - The playlist with the given playlist_id must exist.
            - Returns entries in stored (ordered) form, with position values
              reflecting the playlist's current 0-based ordering.
        """
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return {"success": False, "error": "Playlist not found"}

        # Ensure we return a copy of the entries list to avoid accidental outside mutation
        track_entries = list(playlist.get("track_entries", []))

        return {"success": True, "data": track_entries}

    def get_playlist_tracks_detailed(self, playlist_id: str, user_id: str = None) -> dict:
        """
        Retrieve the ordered list of detailed track metadata for all tracks in a playlist.

        Args:
            playlist_id (str): The playlist's unique identifier to retrieve tracks for.
            user_id (str, optional): The requesting user's id, used for access control.

        Returns:
            dict:
                success: True and "data": List[TrackInfo] (ordered as in the playlist)
                OR
                success: False and "error": str
    
        Constraints:
            - Playlist must exist.
            - If the playlist is 'private', only its owner or users in 'shared_with' can access it.
            - Only tracks with an existing track_id in the global catalog will appear in the result (missing entries are skipped).
            - Returned order matches the playlist's track_entries order.
        """
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return {"success": False, "error": "Playlist does not exist"}

        # Access control
        if playlist["visibility"] == "private":
            # Must have user context and user must be allowed
            if not user_id:
                return {"success": False, "error": "Access denied: private playlist"}
            if user_id != playlist["owner_id"] and user_id not in playlist["shared_with"]:
                return {"success": False, "error": "Access denied: private playlist"}

        ordered_track_infos = []
        for entry in playlist["track_entries"]:
            track = self.tracks.get(entry["track_id"])
            if track:
                ordered_track_infos.append(track)

        return {"success": True, "data": ordered_track_infos}

    def get_track_metadata(self, track_id: str) -> dict:
        """
        Retrieve full metadata for a track by track_id.

        Args:
            track_id (str): The unique identifier of the track.

        Returns:
            dict:
                - {"success": True, "data": TrackInfo} if the track exists.
                - {"success": False, "error": "Track not found"} if not found.

        Constraints:
            - Track with given track_id must exist.
            - No permission needed for this read operation.
        """
        track = self.tracks.get(track_id)
        if track is None:
            return {"success": False, "error": "Track not found"}
        return {"success": True, "data": track}

    def get_user_info(self, user_id: str = None, username: str = None) -> dict:
        """
        Retrieve user metadata by user_id or username.

        Args:
            user_id (str, optional): The unique identifier for the user.
            username (str, optional): The username for the user.
                At least one identifier must be provided.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": UserInfo
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Either user_id or username must be provided.
            - If user_id is given it takes precedence over username.
        """
        if user_id is None and username is None:
            return {
                "success": False,
                "error": "Either user_id or username must be provided."
            }

        # user_id takes precedence
        if user_id is not None:
            user = self.users.get(user_id)
            if user is not None:
                return {
                    "success": True,
                    "data": user
                }

        if username is not None:
            # Search for username in users
            for u in self.users.values():
                if u["username"] == username:
                    return {
                        "success": True,
                        "data": u
                    }

        # Not found
        return {
            "success": False,
            "error": "User not found."
        }

    def check_playlist_access(self, playlist_id: str, user_id: str) -> dict:
        """
        Determine whether a specific user has permission to view or modify a playlist.

        Args:
            playlist_id (str): The ID of the playlist to check.
            user_id (str): The user whose access is being checked.

        Returns:
            dict: 
              On success:
                {
                    "success": True,
                    "can_access": bool,      # True if the user has access, False otherwise
                    "reason": str            # Explanation of access decision
                }
              On error:
                {
                    "success": False,
                    "error": str             # Description of the failure (playlist or user not found)
                }
    
        Rules:
            - Playlist must exist.
            - User must exist.
            - If playlist visibility is 'public', all users can access.
            - If playlist visibility is 'private', only the owner or users in 'shared_with' can access.
        """
        # Validate playlist existence
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return {"success": False, "error": "Playlist does not exist"}

        # Validate user existence
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        # Access logic
        if playlist["visibility"] == "public":
            return {"success": True, "can_access": True, "reason": "Playlist is public"}

        # Private playlist: check ownership or sharing
        if user_id == playlist["owner_id"]:
            return {"success": True, "can_access": True, "reason": "User is the playlist owner"}

        if user_id in playlist.get("shared_with", []):
            return {"success": True, "can_access": True, "reason": "Playlist is shared with the user"}

        return {"success": True, "can_access": False, "reason": "Private playlist not shared with the user and user is not the owner"}

    def search_playlists(
        self,
        title: str = None,
        owner_id: str = None,
        shared_with: str = None,
        visibility: str = None,
        description_keyword: str = None
    ) -> dict:
        """
        Search for playlists matching provided criteria. All parameters are optional—will match all playlists if no filters are provided.

        Args:
            title (str, optional): Case-insensitive substring must appear in playlist's title.
            owner_id (str, optional): Playlist's owner_id must match.
            shared_with (str, optional): Playlist must be shared with this user_id.
            visibility (str, optional): Playlist's visibility must match.
            description_keyword (str, optional): Case-insensitive substring must appear in playlist’s description.

        Returns:
            dict: {
                'success': True,
                'data': [PlaylistInfo, ...]  # list of matching playlists, may be empty
            } on success,
            or
            {
                'success': False,
                'error': <error string>
            } if error (parameter type invalid).
        Constraints:
            - Substring/title/description search is case-insensitive.
            - Only playlists matching all provided non-None criteria are returned.
            - Will not enforce authorization checks for private playlists at the search API level.
        """
        try:
            playlists = list(self.playlists.values())
            result = []
            for pl in playlists:
                if title is not None:
                    if title.lower() not in pl["title"].lower():
                        continue
                if owner_id is not None:
                    if pl["owner_id"] != owner_id:
                        continue
                if shared_with is not None:
                    if shared_with not in pl["shared_with"]:
                        continue
                if visibility is not None:
                    if pl["visibility"] != visibility:
                        continue
                if description_keyword is not None:
                    if description_keyword.lower() not in pl["description"].lower():
                        continue
                result.append(pl)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": "Internal error: " + str(e)}

    def search_tracks(
        self,
        title: str = None,
        artist: str = None,
        album: str = None,
        genre: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Search for tracks by title, artist, album, genre, or metadata fields.

        Args:
            title (str, optional): Title (substring match, case-insensitive).
            artist (str, optional): Artist (substring match, case-insensitive).
            album (str, optional): Album (substring match, case-insensitive).
            genre (str, optional): Genre (substring match, case-insensitive).
            metadata (dict, optional): Dict of metadata fields to match (exact match per field).

        Returns:
            dict:
              - On success:
                  {"success": True, "data": [TrackInfo, ...]}  # List may be empty if no matches.
              - On error:
                  {"success": False, "error": "reason"}

        Constraints:
            - At least one search parameter must be provided (title, artist, album, genre, metadata).
        """
        if not any([title, artist, album, genre, metadata]):
            return {"success": False, "error": "At least one search parameter must be provided."}

        def matches(track: TrackInfo) -> bool:
            if title and title.lower() not in track.get("title", "").lower():
                return False
            if artist and artist.lower() not in track.get("artist", "").lower():
                return False
            if album and album.lower() not in track.get("album", "").lower():
                return False
            if genre and genre.lower() not in track.get("genre", "").lower():
                return False
            if metadata:
                for k, v in metadata.items():
                    track_meta_value = track.get("track_metadata", {}).get(k)
                    if track_meta_value != v:
                        return False
            return True

        results = [track for track in self.tracks.values() if matches(track)]
        return {"success": True, "data": results}

    def list_user_playlists(self, user_id: str) -> dict:
        """
        Get all playlists owned or accessible (via sharing or public visibility) by the specified user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[PlaylistInfo]  # May be empty if no playlists are found.
            }
            or
            {
                "success": False,
                "error": str  # If the user does not exist.
            }

        Constraints:
            - The user must exist.
            - Playlists must be owned, shared with, or public to be included.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        accessible_playlists = []
        for pl in self.playlists.values():
            if (
                pl["owner_id"] == user_id
                or user_id in pl.get("shared_with", [])
                or pl.get("visibility") == "public"
            ):
                accessible_playlists.append(pl)

        return {"success": True, "data": accessible_playlists}

    def get_all_tracks_in_library(self, user_id: str, with_metadata: bool = False) -> dict:
        """
        List all track IDs or (optionally) full metadata for all tracks in a user’s personal library.

        Args:
            user_id (str): ID of the user whose library to list.
            with_metadata (bool): If True, return detailed metadata for each track; else, return just IDs.

        Returns:
            dict: {
                "success": True,
                "data": List[str] | List[TrackInfo],  # Track IDs or full metadata, may be empty list
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - User must exist in the system.
            - Only tracks that exist in the global track list are returned in metadata mode.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        track_ids = user.get("library", [])

        if with_metadata:
            # Only return track info for existing tracks
            tracks_data = [
                self.tracks[tid]
                for tid in track_ids
                if tid in self.tracks
            ]
            return { "success": True, "data": tracks_data }
        else:
            return { "success": True, "data": track_ids }

    def update_playlist_metadata(
        self, 
        playlist_id: str, 
        requester_id: str, 
        title: str = None,
        description: str = None,
        visibility: str = None
    ) -> dict:
        """
        Modify metadata fields (title, description, visibility) of an existing playlist,
        provided the requester is the playlist owner.

        Args:
            playlist_id (str): Target playlist ID.
            requester_id (str): User performing the action (for ownership verification).
            title (str, optional): New title for the playlist.
            description (str, optional): New description for the playlist.
            visibility (str, optional): New visibility; must be either 'public' or 'private'.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Playlist metadata updated successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Playlist must exist.
            - Only the playlist owner may update metadata.
            - If visibility is provided, it must be 'public' or 'private'.
            - At least one updatable field must be specified.
        """
        playlist = self.playlists.get(playlist_id)
        if playlist is None:
            return { "success": False, "error": "Playlist does not exist." }
    
        if playlist["owner_id"] != requester_id:
            return { "success": False, "error": "Permission denied. Only the owner can update playlist metadata." }

        # Track if any field was actually updated
        updates = {}

        if title is not None:
            playlist["title"] = title
            updates["title"] = title
        if description is not None:
            playlist["description"] = description
            updates["description"] = description
        if visibility is not None:
            if visibility not in ("public", "private"):
                return { "success": False, "error": "Invalid visibility. Must be 'public' or 'private'." }
            playlist["visibility"] = visibility
            updates["visibility"] = visibility

        if not updates:
            return { "success": False, "error": "No fields provided to update." }
    
        # Persist the changes
        self.playlists[playlist_id] = playlist

        return { "success": True, "message": "Playlist metadata updated successfully." }

    def add_track_to_playlist(
        self,
        playlist_id: str,
        track_id: str,
        added_by: str,
        position: int = None
    ) -> dict:
        """
        Insert a track into a playlist at a given position (0-based, before that index), or append if position is None.
        Updates the playlist's track_entries while preserving order; updates positions. 
        Allows multiple instances of the same track in the same playlist.

        Args:
            playlist_id (str): Playlist to add to.
            track_id (str): Track to add.
            added_by (str): User (user_id) making the change.
            position (int, optional): Position to insert at (0-based). If None, appends to end.

        Returns:
            dict: {
                "success": True,
                "message": "Track added to playlist at position X."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Playlist, Track, and User must exist.
            - User must be owner or have write-access to playlist (shared/private).
            - Position must be in [0, len(playlist.track_entries)] if specified.
            - Playlist's order is preserved and stored positions remain contiguous
              0-based indices after the insertion.
        """
        # Check entities exist
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return {"success": False, "error": "Playlist does not exist."}
        track = self.tracks.get(track_id)
        if not track:
            return {"success": False, "error": "Track does not exist."}
        user = self.users.get(added_by)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # Permissions: Owner or shared access (write), depending on visibility
        if playlist["visibility"] == "private":
            if playlist["owner_id"] != added_by and added_by not in playlist.get("shared_with", []):
                return {"success": False, "error": "User does not have permission to modify this playlist."}

        # Get track entries as list
        track_entries = playlist["track_entries"]
        n = len(track_entries)

        # Validate position
        if position is not None:
            if not isinstance(position, int) or position < 0 or position > n:
                return {"success": False, "error": f"Position must be between 0 and {n} (inclusive)."}


        # Prepare new entry for the track
        new_entry = {
            "playlist_id": playlist_id,
            "track_id": track_id,
            "position": 0,  # will be set later
            "date_added": datetime.now().isoformat(timespec="seconds"),
            "added_by": added_by,
        }

        # Determine insert/appending index
        if position is None:
            insert_idx = n  # Append
        else:
            insert_idx = position

        # Insert the item
        # We'll temporarily ignore the position field, and set positions after
        track_entries.insert(insert_idx, new_entry)

        # Persist stored positions as contiguous 0-based ordinals so callers can
        # reuse the observed positions with this tool's documented insert API.
        for idx, entry in enumerate(track_entries):
            entry["position"] = idx

        # Save back (not necessary, since list is mutable, but for consistency)
        playlist["track_entries"] = track_entries

        return {
            "success": True,
            "message": f"Track added to playlist at position {insert_idx}."
        }

    def remove_track_from_playlist(self, playlist_id: str, position: int, requesting_user_id: str) -> dict:
        """
        Remove the track entry at a given position in a playlist.

        Args:
            playlist_id (str): The ID of the playlist to modify.
            position (int): The one-based position (1 = first) of the track entry to remove.
            requesting_user_id (str): The user initiating the removal, for permission check.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - Only the playlist owner or a user in 'shared_with' can modify a private playlist.
            - Playlist and position must exist.
            - Playlist ordering must be preserved post-removal.
        """
        # 1. Playlist existence
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return { "success": False, "error": "Playlist does not exist" }

        # 2. Permission check
        is_owner = requesting_user_id == playlist["owner_id"]
        is_shared = requesting_user_id in playlist.get("shared_with", [])
        if playlist.get("visibility") == "private" and not (is_owner or is_shared):
            return { "success": False, "error": "Permission denied to modify this private playlist" }

        # 3. Validate position (assume one-based)
        entries = playlist.get("track_entries", [])
        if not entries:
            return { "success": False, "error": "Playlist is empty" }
        if not (1 <= position <= len(entries)):
            return { "success": False, "error": "Invalid position: out of range" }

        # 4. Remove the track entry at that position (positions are 1-based, Python list is 0-based)
        removed_entry = entries.pop(position - 1)

        # 5. Recompute positions to stay 1-based and contiguous
        for idx, entry in enumerate(entries):
            entry["position"] = idx + 1
        # Persist update
        playlist["track_entries"] = entries

        return {
            "success": True,
            "message": f"Track at position {position} removed from playlist {playlist_id}."
        }

    def reorder_playlist_tracks(self, playlist_id: str, new_order: list) -> dict:
        """
        Reorganize the order of tracks in a playlist.

        Args:
            playlist_id (str): The ID of the playlist to reorder.
            new_order (list of str): A list of track_id strings in the desired new order.
                This list must be a permutation of the current playlist's track_ids, with no repeats.

        Returns:
            dict: {
                "success": True,
                "message": "Playlist track order updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The playlist must exist.
            - new_order must be a permutation of current track_ids in the playlist (no missing or extra tracks, no duplicates).
            - Positions are updated and must be contiguous integers starting at 1.
            - Metadata (date_added, added_by) for each entry is preserved, only order/position is changed.
        """
        # Playlist existence check
        if playlist_id not in self.playlists:
            return { "success": False, "error": "Playlist does not exist." }

        playlist = self.playlists[playlist_id]
        current_entries = playlist["track_entries"]

        # Get current track_ids in order
        current_track_ids = [entry["track_id"] for entry in current_entries]

        # Validate permutation and uniqueness
        if sorted(current_track_ids) != sorted(new_order):
            return {
                "success": False,
                "error": "new_order must be a permutation of the current playlist's tracks (no duplicates, no missing/extra tracks)."
            }

        # Map track_id to entry for fast lookup
        trackid_to_entry = {entry["track_id"]: entry.copy() for entry in current_entries}

        # Build the reordered list
        reordered_entries = []
        for pos, tid in enumerate(new_order, 1):
            entry = trackid_to_entry[tid]
            entry["position"] = pos
            reordered_entries.append(entry)

        # Update the playlist's track_entries
        playlist["track_entries"] = reordered_entries

        return {
            "success": True,
            "message": "Playlist track order updated."
        }

    def update_track_metadata(self, track_id: str, metadata_updates: dict) -> dict:
        """
        Edit metadata fields (artist, title, genre, etc.) for a specific track.

        Args:
            track_id (str): The unique identifier of the track to update.
            metadata_updates (dict): Key-value pairs of track fields to update. 
                Allowed fields: title, artist, album, duration, genre, release_date, track_metadata (dict)

        Returns:
            dict: 
                - On success: { "success": True, "message": "Track metadata updated for track_id=..." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - Only valid fields present in TrackInfo can be updated (except track_id).
            - type-safety: will ignore updates where supplied value is obviously wrong type.
        """
        if track_id not in self.tracks:
            return { "success": False, "error": "Track does not exist" }

        track = self.tracks[track_id]

        allowed_fields = {"title", "artist", "album", "duration", "genre", "release_date", "track_metadata"}
        updated = False
        for key, value in metadata_updates.items():
            if key not in allowed_fields:
                continue  # ignore unknown fields
            if key == "duration" and not isinstance(value, (int, float)):
                continue  # skip invalid type
            if key == "track_metadata":
                if not isinstance(value, dict):
                    continue
                track["track_metadata"].update(value)
                updated = True
                continue
            # Otherwise basic assignment
            track[key] = value
            updated = True

        if updated:
            return { "success": True, "message": f"Track metadata updated for track_id={track_id}" }
        else:
            return { "success": False, "error": "No valid fields updated" }

    def share_playlist_with_user(self, playlist_id: str, target_user_id: str, requesting_user_id: str) -> dict:
        """
        Grant another user access to a playlist (add target_user_id to shared_with).
        Only the playlist owner can share their playlist with others.

        Args:
            playlist_id (str): The unique id of the playlist to share.
            target_user_id (str): The user id to share the playlist with.
            requesting_user_id (str): The user id performing the operation (must be playlist owner).

        Returns:
            dict: 
              - On success: { "success": True, "message": "Playlist shared with user." }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Playlist must exist.
            - Target user must exist.
            - Requesting user must exist.
            - Only playlist owner may share the playlist.
            - User should not be added multiple times to shared_with.
        """
        # Check playlist exists
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return { "success": False, "error": "Playlist does not exist." }
    
        # Check requesting user exists
        if requesting_user_id not in self.users:
            return { "success": False, "error": "Requesting user does not exist." }
    
        # Check target user exists
        if target_user_id not in self.users:
            return { "success": False, "error": "Target user does not exist." }
    
        # Only owner allowed to share
        if playlist["owner_id"] != requesting_user_id:
            return { "success": False, "error": "Only the playlist owner can share the playlist." }
    
        # If the playlist is already visible to everyone (public), perhaps return a different message,
        # but per spec, we simply add to shared_with if not present.
        if target_user_id in playlist["shared_with"]:
            return { "success": True, "message": "User already has access to the playlist." }
    
        playlist["shared_with"].append(target_user_id)
        return { "success": True, "message": "Playlist shared with user." }

    def unshare_playlist_with_user(
        self,
        playlist_id: str,
        target_user_id: str,
        requesting_user_id: str
    ) -> dict:
        """
        Revoke another user’s access to a shared playlist.

        Args:
            playlist_id (str): ID of the playlist to modify.
            target_user_id (str): User ID to revoke access from.
            requesting_user_id (str): User ID requesting the revocation (should be owner).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User access revoked from playlist" }
                On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - Playlist must exist.
            - Only the playlist owner can revoke sharing.
            - User to unshare with must exist and must already have access.
            - Playlist's "shared_with" will be updated accordingly.
            - No changes if attempting to unshare a user who isn't shared.
        """
        # Playlist existence check
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return { "success": False, "error": "Playlist does not exist" }

        # Target user existence check
        if target_user_id not in self.users:
            return { "success": False, "error": "Target user does not exist" }

        # Requesting user existence check
        if requesting_user_id not in self.users:
            return { "success": False, "error": "Requesting user does not exist" }

        # Ownership check
        if playlist["owner_id"] != requesting_user_id:
            return { "success": False, "error": "Permission denied: only playlist owner can revoke access" }
    
        # Sharing list check
        if target_user_id not in playlist["shared_with"]:
            return { "success": False, "error": "Target user does not have shared access for this playlist" }

        # Remove user from shared_with list
        playlist["shared_with"].remove(target_user_id)
        # Change will be reflected in self.playlists since playlist is a reference

        return { "success": True, "message": "User access revoked from playlist" }

    def create_playlist(
        self,
        playlist_id: str,
        title: str,
        description: str,
        creation_date: str,
        owner_id: str,
        visibility: str,
        shared_with: list,
        track_entries: list
    ) -> dict:
        """
        Create a new playlist with specified metadata and track entries.

        Args:
            playlist_id (str): Unique identifier for the playlist (must not exist already).
            title (str): Playlist title.
            description (str): Playlist description.
            creation_date (str): ISO timestamp string.
            owner_id (str): User ID of the playlist owner (must exist).
            visibility (str): Playlist visibility ('public' or 'private').
            shared_with (List[str]): List of user IDs the playlist is shared with.
            track_entries (List[dict]): List of track entry dicts, each with:
                - track_id (must exist)
                - position (int, unique per playlist)
                - date_added (str)
                - added_by (user_id, must exist)

        Returns:
            dict: {"success": True, "message": "..."}
                  or {"success": False, "error": "<reason>"}

        Constraints:
            - playlist_id must be unique.
            - owner_id must exist in users.
            - shared_with user_ids must exist.
            - Each track_entry's track_id must exist in tracks.
            - Each track_entry's added_by must exist in users.
            - Each position in track_entries must be unique.
        """
        # Check playlist_id is unique
        if playlist_id in self.playlists:
            return {"success": False, "error": "Playlist ID already exists."}

        # Check owner
        if owner_id not in self.users:
            return {"success": False, "error": "Owner user ID does not exist."}

        # Check shared_with users existence
        for uid in shared_with:
            if uid not in self.users:
                return {"success": False, "error": f"Shared user ID {uid} does not exist."}

        # Validate track_entries and store as PlaylistTrackEntryInfo objects
        added_positions = set()
        valid_entries = []
        for entry in track_entries:
            # Check presence of all required keys
            for key in ["track_id", "position", "date_added", "added_by"]:
                if key not in entry:
                    return {"success": False, "error": f"Missing '{key}' in track entry."}

            track_id = entry["track_id"]
            position = entry["position"]
            date_added = entry["date_added"]
            added_by = entry["added_by"]

            if track_id not in self.tracks:
                return {"success": False, "error": f"Track ID {track_id} does not exist."}
            if added_by not in self.users:
                return {"success": False, "error": f"Added_by user {added_by} does not exist."}
            if position in added_positions:
                return {"success": False, "error": f"Duplicate position {position} in track entries."}

            added_positions.add(position)
            valid_entries.append({
                "playlist_id": playlist_id,
                "track_id": track_id,
                "position": position,
                "date_added": date_added,
                "added_by": added_by
            })

        # Build the PlaylistInfo structure
        playlist_info = {
            "playlist_id": playlist_id,
            "title": title,
            "description": description,
            "creation_date": creation_date,
            "owner_id": owner_id,
            "visibility": visibility,
            "shared_with": shared_with.copy(),
            "track_entries": sorted(valid_entries, key=lambda x: x["position"])
        }

        # Add the playlist to the catalog
        self.playlists[playlist_id] = playlist_info

        # Add this playlist to owner's playlists, preserving list
        if playlist_id not in self.users[owner_id]["playlists"]:
            self.users[owner_id]["playlists"].append(playlist_id)

        return {"success": True, "message": f"Playlist {playlist_id} created."}

    def delete_playlist(self, playlist_id: str, requester_id: str) -> dict:
        """
        Remove a playlist from the system.
        Only the playlist owner or a user with admin rights may delete.

        Args:
            playlist_id (str): The ID of the playlist to delete.
            requester_id (str): The user performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": "Playlist deleted (<playlist_id>) successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Playlist must exist.
            - Requester must exist and either be playlist owner or have account_status=='admin'.
            - Playlist must be removed from all users' 'playlists' lists.
        """
        if playlist_id not in self.playlists:
            return {"success": False, "error": "Playlist does not exist"}

        if requester_id not in self.users:
            return {"success": False, "error": "Requester does not exist"}

        playlist = self.playlists[playlist_id]
        owner_id = playlist["owner_id"]

        requester = self.users[requester_id]

        # Check permissions: owner or admin
        if requester_id != owner_id and requester.get("account_status", "").lower() != "admin":
            return {"success": False, "error": "Permission denied: only owner or admin can delete playlist"}

        # Remove playlist from owner's and any shared user's playlist lists
        for user in self.users.values():
            if "playlists" in user and playlist_id in user["playlists"]:
                user["playlists"] = [pid for pid in user["playlists"] if pid != playlist_id]

        # Remove the playlist entry itself
        del self.playlists[playlist_id]

        return {"success": True, "message": f"Playlist deleted ({playlist_id}) successfully"}

    def add_track_to_user_library(self, user_id: str, track_id: str) -> dict:
        """
        Add a track to the personal library collection of the specified user.

        Args:
            user_id (str): The ID of the user whose library to update.
            track_id (str): The ID of the track to add.

        Returns:
            dict:
                On success: { "success": True, "message": "Track <track_id> added to user <user_id> library." }
                On error:   { "success": False, "error": "..." }

        Constraints:
            - The user must exist.
            - The track must exist.
            - The track should not be present in the user's library more than once.
            - Idempotent: If the track is already in the library, return success with appropriate message.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if track_id not in self.tracks:
            return { "success": False, "error": "Track does not exist." }

        user_info = self.users[user_id]

        if track_id in user_info["library"]:
            return {
                "success": True,
                "message": f"Track {track_id} is already in user {user_id}'s library."
            }

        user_info["library"].append(track_id)
        # No need to update self.users[user_id] again as the object is mutable.

        return {
            "success": True,
            "message": f"Track {track_id} added to user {user_id} library."
        }

    def remove_track_from_user_library(self, user_id: str, track_id: str) -> dict:
        """
        Remove a track from a user's personal library collection.

        Args:
            user_id (str): ID of the user whose library to modify.
            track_id (str): ID of the track to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Track <track_id> removed from user <user_id>'s library."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - User must exist.
            - Track must exist.
            - Track must be present in user's library.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if track_id not in self.tracks:
            return {"success": False, "error": "Track does not exist."}

        user_info = self.users[user_id]
        if track_id not in user_info["library"]:
            return {"success": False, "error": "Track is not in user's library."}

        user_info["library"].remove(track_id)
        # No need to update self.users[user_id] explicitly because user_info is a reference
        return {
            "success": True,
            "message": f"Track {track_id} removed from user {user_id}'s library."
        }

    def update_playlist_sharing(
        self,
        playlist_id: str,
        user_id: str,
        shared_with: list = None,
        visibility: str = None,
    ) -> dict:
        """
        Bulk update the 'shared_with' list or toggle playlist public/private status.

        Args:
            playlist_id (str): Target playlist ID.
            user_id (str): The user attempting the update (must be owner).
            shared_with (Optional[list]): A new list of user_ids to share with (replaces current sharing list if provided).
            visibility (Optional[str]): Set playlist visibility ("public" or "private").

        Returns:
            dict: {
                "success": True,
                "message": "Playlist sharing properties updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only the playlist owner can perform this operation.
            - Playlist must exist.
            - supplied user_ids in shared_with must exist.
            - Visibility, if provided, must be 'public' or 'private'.
            - At least one of shared_with or visibility must be provided.
        """
        # Check playlist existence
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return {"success": False, "error": "Playlist does not exist"}

        # Check permission (owner)
        if playlist["owner_id"] != user_id:
            return {"success": False, "error": "Permission denied: Only owner can update sharing"}

        # Make sure something is being modified
        if shared_with is None and visibility is None:
            return {"success": False, "error": "No update parameters provided"}

        # Track whether any update happens
        changed = False

        # Validate and update shared_with
        if shared_with is not None:
            # Validate each user_id exists
            for suid in shared_with:
                if suid not in self.users:
                    return {"success": False, "error": f"User id '{suid}' in shared_with does not exist"}
            playlist["shared_with"] = list(shared_with)
            changed = True

        # Validate and update visibility
        if visibility is not None:
            if visibility not in ("public", "private"):
                return {"success": False, "error": "Invalid visibility. Must be 'public' or 'private'"}
            playlist["visibility"] = visibility
            changed = True

        if changed:
            return {"success": True, "message": "Playlist sharing properties updated"}
        else:
            # Should not happen due to above check, but keep for logical completeness
            return {"success": False, "error": "No update performed"}


class MusicStreamingPlaylistManagementSystem(BaseEnv):
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

    def get_playlist_metadata(self, **kwargs):
        return self._call_inner_tool('get_playlist_metadata', kwargs)

    def get_playlist_track_entries(self, **kwargs):
        return self._call_inner_tool('get_playlist_track_entries', kwargs)

    def get_playlist_tracks_detailed(self, **kwargs):
        return self._call_inner_tool('get_playlist_tracks_detailed', kwargs)

    def get_track_metadata(self, **kwargs):
        return self._call_inner_tool('get_track_metadata', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def check_playlist_access(self, **kwargs):
        return self._call_inner_tool('check_playlist_access', kwargs)

    def search_playlists(self, **kwargs):
        return self._call_inner_tool('search_playlists', kwargs)

    def search_tracks(self, **kwargs):
        return self._call_inner_tool('search_tracks', kwargs)

    def list_user_playlists(self, **kwargs):
        return self._call_inner_tool('list_user_playlists', kwargs)

    def get_all_tracks_in_library(self, **kwargs):
        return self._call_inner_tool('get_all_tracks_in_library', kwargs)

    def update_playlist_metadata(self, **kwargs):
        return self._call_inner_tool('update_playlist_metadata', kwargs)

    def add_track_to_playlist(self, **kwargs):
        return self._call_inner_tool('add_track_to_playlist', kwargs)

    def remove_track_from_playlist(self, **kwargs):
        return self._call_inner_tool('remove_track_from_playlist', kwargs)

    def reorder_playlist_tracks(self, **kwargs):
        return self._call_inner_tool('reorder_playlist_tracks', kwargs)

    def update_track_metadata(self, **kwargs):
        return self._call_inner_tool('update_track_metadata', kwargs)

    def share_playlist_with_user(self, **kwargs):
        return self._call_inner_tool('share_playlist_with_user', kwargs)

    def unshare_playlist_with_user(self, **kwargs):
        return self._call_inner_tool('unshare_playlist_with_user', kwargs)

    def create_playlist(self, **kwargs):
        return self._call_inner_tool('create_playlist', kwargs)

    def delete_playlist(self, **kwargs):
        return self._call_inner_tool('delete_playlist', kwargs)

    def add_track_to_user_library(self, **kwargs):
        return self._call_inner_tool('add_track_to_user_library', kwargs)

    def remove_track_from_user_library(self, **kwargs):
        return self._call_inner_tool('remove_track_from_user_library', kwargs)

    def update_playlist_sharing(self, **kwargs):
        return self._call_inner_tool('update_playlist_sharing', kwargs)
