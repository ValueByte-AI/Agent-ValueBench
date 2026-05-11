# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
from typing import List, Optional
from datetime import datetime
import datetime



# Each station available on the platform, with metadata and popularity indicators.
class RadioStationInfo(TypedDict):
    station_id: str
    name: str
    genre: str
    streaming_url: str
    popularity_index: float
    is_featured: bool
    is_trending: bool
    description: str

# Represents the current list of 'featured' stations shown on the home page and the order in which they appear.
class FeaturedStationsInfo(TypedDict):
    station_ids: List[str]       # List of featured station_ids in display order
    display_position: List[int]  # Display order for each station
    update_time: str             # Timestamp or ISO date string

# Represents stations designated as trending, likely influenced by real-time or recent user behaviors.
class TrendingStationsInfo(TypedDict):
    station_ids: List[str]       # List of trending station_ids
    update_time: str             # Timestamp or ISO date string

# Represents a user and their preferences or usage history.
class UserInfo(TypedDict, total=False):
    _id: str
    listening_history: List[str]             # List of station_ids or session/activity descriptors
    genre_preference: Optional[List[str]]    # List of preferred genres

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for Online Radio Streaming Platform.
        """

        # All radio stations: {station_id: RadioStationInfo}
        self.stations: Dict[str, RadioStationInfo] = {}

        # Featured stations configuration
        self.featured_stations: FeaturedStationsInfo = {
            "station_ids": [],
            "display_position": [],
            "update_time": ""
        }

        # Trending stations configuration
        self.trending_stations: TrendingStationsInfo = {
            "station_ids": [],
            "update_time": ""
        }

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Only valid (active) stations with streaming URLs may be featured or trending.
        # - Popularity index is regularly updated from listening activity.
        # - The featured/trending station lists have a finite display size (e.g., top N).
        # - Station genres are drawn from a fixed set for filtering/curation.
        # - The same station cannot appear more than once in a given ranked/curated list.

    def get_featured_stations(self) -> dict:
        """
        Retrieve the current list of featured stations, including station IDs, display order, and update time.

        Args:
            None

        Returns:
            dict:
              On success:
                 {
                     "success": True,
                     "data": FeaturedStationsInfo
                 }
              On failure:
                 {
                     "success": False,
                     "error": str
                 }

        Notes:
            - Resulting FeaturedStationsInfo will always include keys: station_ids (list), display_position (list), update_time (str).
            - No permissions or station validation are performed in this query operation.
        """
        if not isinstance(self.featured_stations, dict):
            return { "success": False, "error": "Featured stations info unavailable." }
        # Ensure expected keys are present
        for key in ['station_ids', 'display_position', 'update_time']:
            if key not in self.featured_stations:
                return { "success": False, "error": f"Featured stations info missing key: {key}" }

        return {
            "success": True,
            "data": self.featured_stations
        }

    def get_trending_stations(self) -> dict:
        """
        Retrieve the current list of trending station IDs and their update time.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": TrendingStationsInfo  # station_ids (List[str]), update_time (str)
            }
            or
            {
                "success": False,
                "error": str
            }
        Notes:
            - The trending stations list may be empty if no stations are currently trending.
            - Does not check station validity (assumed to be handled during trending list update).
        """
        # Simply return the trending stations info
        return {
            "success": True,
            "data": {
                "station_ids": self.trending_stations.get("station_ids", []),
                "update_time": self.trending_stations.get("update_time", "")
            }
        }

    def get_station_by_id(self, station_id: str) -> dict:
        """
        Retrieve the full metadata of a radio station given its station_id.

        Args:
            station_id (str): The unique identifier of the station.

        Returns:
            dict: {
                "success": True,
                "data": RadioStationInfo    # If found, full station metadata
            }
            or
            {
                "success": False,
                "error": str                # If not found, reason string
            }

        Constraints:
            - Station must exist in the system.
        """
        if station_id not in self.stations:
            return { "success": False, "error": "Station does not exist" }

        return { "success": True, "data": self.stations[station_id] }

    def list_all_stations(self) -> dict:
        """
        Retrieve metadata for all radio stations registered on the platform.

        Args:
            None

        Returns:
            dict:
            {
                "success": True,
                "data": List[RadioStationInfo]
            }
            If there are no radio stations, the data list will be empty.

        Constraints:
            - Includes all registered stations, regardless of validity or status flags.
        """
        result = list(self.stations.values())
        return { "success": True, "data": result }

    def list_stations_by_genre(self, genre: str) -> dict:
        """
        Retrieve all radio stations with a given genre.

        Args:
            genre (str): The station genre to filter by.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RadioStationInfo],  # List of matching stations (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Error description if genre argument is missing/invalid
                }

        Constraints:
            - The genre string must be provided (non-empty).
            - Result does not check for genre validity against the platform's set, just matches.
            - Returns all stations with genre equal to input.
        """
        if not isinstance(genre, str) or not genre.strip():
            return { "success": False, "error": "Genre must be a non-empty string." }

        matched = [
            station_info
            for station_info in self.stations.values()
            if station_info.get("genre") == genre
        ]
        return { "success": True, "data": matched }

    def get_station_genres(self) -> dict:
        """
        Retrieve the full set of unique, valid genres supported by the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # Sorted list of unique genres in platform,
            }

        Constraints:
            - Genres are drawn from station records on the platform.
            - May return empty list if there are no stations.
        """
        # Collect unique genres from all stations
        genres = set()
        for station in self.stations.values():
            genre = station.get("genre", "")
            if genre:
                genres.add(genre)
        genre_list = sorted(list(genres))
        return { "success": True, "data": genre_list }

    def get_station_popularity_ranking(self) -> dict:
        """
        Retrieve a ranking of stations by their popularity_index, descending (most popular first).

        Args:
            None.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RadioStationInfo]  # List of stations sorted by popularity_index descending.
                }
                or
                {
                    "success": False,
                    "error": str  # Only if no stations present (unlikely).
                }

        Constraints:
            - Only stations with a valid (non-empty) streaming_url are included.
            - No duplicate stations in the result.
        """
        valid_stations = [
            station for station in self.stations.values()
            if station["streaming_url"] and isinstance(station["popularity_index"], (int, float))
        ]

        # Sort stations descending by popularity_index
        ranked_stations = sorted(
            valid_stations,
            key=lambda s: s["popularity_index"],
            reverse=True
        )

        return {
            "success": True,
            "data": ranked_stations
        }

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve a user's information, including listening history and genre preferences.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - User must exist in the system for this operation to succeed.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_valid_stations(self) -> dict:
        """
        Retrieve all 'valid' (active and streamable) stations eligible for curation.
        A station is considered valid if its 'streaming_url' is a non-empty string.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RadioStationInfo]  # List of valid station infos (possibly empty)
            }

        Constraints:
            - Only stations with a non-empty streaming_url are included.
        """
        valid_stations = [
            station
            for station in self.stations.values()
            if isinstance(station.get("streaming_url", ""), str) and station.get("streaming_url", "").strip() != ""
        ]
        return { "success": True, "data": valid_stations }

    def get_station_status(self, station_id: str) -> dict:
        """
        Check if a given station is currently active/valid (has a non-empty streaming URL).

        Args:
            station_id (str): The unique identifier of the radio station.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": { "station_id": ..., "is_valid": bool }
                    }
                If station does not exist:
                    {
                        "success": False,
                        "error": "Station not found"
                    }

        Constraints:
            - Station is valid only if it exists and has a non-empty streaming_url.
        """
        station = self.stations.get(station_id)
        if station is None:
            return { "success": False, "error": "Station not found" }

        streaming_url = station.get("streaming_url", "")
        is_valid = bool(streaming_url and streaming_url.strip())

        return {
            "success": True,
            "data": {
                "station_id": station_id,
                "is_valid": is_valid
            }
        }

    def get_user_personalized_recommendations(self, user_id: str, max_results: int = 10) -> dict:
        """
        Retrieve a personalized list of recommended radio stations for a user,
        based on their listening history and genre preferences.

        Args:
            user_id (str): The user's unique identifier.
            max_results (int): Maximum number of recommendations (default: 10).

        Returns:
            dict: {
                "success": True,
                "data": List[RadioStationInfo],  # List of recommended stations (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason why recommendations could not be generated
            }

        Constraints:
            - User must exist.
            - Only valid (active, has non-empty streaming_url) stations are recommended.
            - No duplicates in recommendations.
            - Recommendations should prioritize genre preferences and novelty.
            - Recommendations should be at most 'max_results' long.
        """
        # 1. User lookup
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        # 2. Gather user preferences
        preferred_genres = user.get("genre_preference", [])
        listened_station_ids = set(user.get("listening_history", []))

        # Helper: find valid stations
        def is_valid_station(station: RadioStationInfo) -> bool:
            return bool(station["streaming_url"].strip())

        # 3. Build pool of all valid stations
        valid_stations = [
            s for s in self.stations.values() if is_valid_station(s)
        ]

        # Do not recommend stations the user already listened to
        not_listened = [s for s in valid_stations if s["station_id"] not in listened_station_ids]

        # 4. Recommendation construction
        recommendations = []
        selected_ids = set()  # To prevent duplicates

        # a. Priority 1: Preferred genre & not listened
        if preferred_genres:
            preferred_genre_set = set(preferred_genres)
            preferred = [s for s in not_listened if s["genre"] in preferred_genre_set]
            # Sort by popularity
            preferred.sort(key=lambda x: -x.get("popularity_index", 0))
            for s in preferred:
                if s["station_id"] not in selected_ids and len(recommendations) < max_results:
                    recommendations.append(s)
                    selected_ids.add(s["station_id"])

        # b. Priority 2: Trending stations not already added
        if len(recommendations) < max_results:
            for station_id in self.trending_stations["station_ids"]:
                if (station_id not in selected_ids and
                    station_id not in listened_station_ids and
                    station_id in self.stations):
                    s = self.stations[station_id]
                    if is_valid_station(s):
                        recommendations.append(s)
                        selected_ids.add(s["station_id"])
                        if len(recommendations) >= max_results:
                            break

        # c. Priority 3: Fill with other valid stations by popularity
        if len(recommendations) < max_results:
            remaining = [s for s in not_listened
                         if s["station_id"] not in selected_ids]
            remaining.sort(key=lambda x: -x.get("popularity_index", 0))
            for s in remaining:
                if len(recommendations) >= max_results:
                    break
                recommendations.append(s)
                selected_ids.add(s["station_id"])

        return {"success": True, "data": recommendations[:max_results]}


    def update_featured_stations(
        self, 
        station_ids: List[str], 
        display_position: Optional[List[int]] = None, 
        update_time: Optional[str] = None
    ) -> dict:
        """
        Update the platform’s featured stations list and their display order.

        Args:
            station_ids (List[str]):
                Ordered list of station IDs to be featured (no duplicates allowed).
            display_position (Optional[List[int]]):
                Display order for each station (must match length of station_ids). If None, will use default sequential ordering.
            update_time (Optional[str]):
                ISO update timestamp. If None, set to current UTC time.

        Returns:
            dict: {
                "success": True,
                "message": "Featured stations updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only valid (active) stations with a non-empty streaming URL may be featured.
            - Station IDs must exist.
            - No duplicate stations in the list.
            - station_ids and display_position (if given) must be same length.
        """
        if not isinstance(station_ids, list) or not station_ids:
            return {"success": False, "error": "station_ids must be a non-empty list."}
        if len(station_ids) != len(set(station_ids)):
            return {"success": False, "error": "Duplicate station IDs in station_ids list."}
        # Validate station IDs and station eligibility
        for sid in station_ids:
            s = self.stations.get(sid)
            if not s:
                return {"success": False, "error": f"Station ID '{sid}' does not exist."}
            if not s['streaming_url'].strip():
                return {"success": False, "error": f"Station '{sid}' does not have a valid streaming URL."}
        # Validate display_position
        if display_position is not None:
            if not isinstance(display_position, list) or len(display_position) != len(station_ids):
                return {"success": False, "error": "display_position must be a list of the same length as station_ids."}
        else:
            display_position = list(range(1, len(station_ids)+1))
        # Set update time
        if update_time is None:
            update_time = datetime.datetime.utcnow().isoformat()
        # Update featured stations
        self.featured_stations["station_ids"] = list(station_ids)
        self.featured_stations["display_position"] = list(display_position)
        self.featured_stations["update_time"] = update_time
        # Mark stations as featured / unfeature others
        for sid, station in self.stations.items():
            station['is_featured'] = (sid in station_ids)
        return {"success": True, "message": "Featured stations updated."}

    def update_trending_stations(self, top_n: int = 10) -> dict:
        """
        Update the trending stations list using popularity_index (e.g., top N).
        Only valid (active) stations with streaming URLs are eligible.
        Sets 'is_trending' in each RadioStationInfo accordingly.
        TrendingStationsInfo is updated, including update_time.

        Args:
            top_n (int): Number of trending stations to select (default 10).

        Returns:
            dict: 
                - On success: {"success": True, "message": "Trending stations updated successfully"}
                - On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - Only valid stations with streaming URLs may be trending.
            - Trending list has finite size (top_n).
            - No station repeats in trending.
        """

        # Filter valid stations (active with valid streaming URL)
        valid_station_list = [
            station for station in self.stations.values()
            if station.get("streaming_url") and station.get("streaming_url").strip()
        ]

        if not valid_station_list:
            return { "success": False, "error": "No valid stations to select as trending" }

        # Sort by popularity_index descending, pick top N (no repeats)
        sorted_stations = sorted(
            valid_station_list, 
            key=lambda s: s.get("popularity_index", 0), 
            reverse=True
        )

        trending_station_ids = []
        seen = set()
        for station in sorted_stations:
            sid = station["station_id"]
            if sid not in seen:
                trending_station_ids.append(sid)
                seen.add(sid)
            if len(trending_station_ids) >= top_n:
                break

        # Set is_trending flags in stations
        for sid, info in self.stations.items():
            info["is_trending"] = (sid in trending_station_ids)

        # Update TrendingStationsInfo
        self.trending_stations["station_ids"] = trending_station_ids
        self.trending_stations["update_time"] = datetime.datetime.now().isoformat()

        return { "success": True, "message": "Trending stations updated successfully" }

    def add_radio_station(
        self,
        station_id: str,
        name: str,
        genre: str,
        streaming_url: str,
        popularity_index: float = 0.0,
        is_featured: bool = False,
        is_trending: bool = False,
        description: str = ""
    ) -> dict:
        """
        Add a new radio station with specified metadata to the station catalog.

        Args:
            station_id (str): Unique ID for the station (must not already exist).
            name (str): Human-readable station name.
            genre (str): Station genre (should be a valid genre if enforced).
            streaming_url (str): The stream URL for this station (must be non-empty).
            popularity_index (float, optional): Defaults to 0.0.
            is_featured (bool, optional): Whether the station is currently featured. Defaults to False.
            is_trending (bool, optional): Whether the station is currently trending. Defaults to False.
            description (str, optional): Short station description.

        Returns:
            dict: {
                "success": True,
                "message": "Radio station added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - station_id must be unique.
            - streaming_url must be non-empty.
            - Only valid (active) stations with streaming URLs allowed.
        """

        # Uniqueness check
        if station_id in self.stations:
            return {"success": False, "error": "station_id already exists"}

        # streaming_url must be non-empty
        if not isinstance(streaming_url, str) or not streaming_url.strip():
            return {"success": False, "error": "streaming_url must be a non-empty string"}

        # Minimal validation (optional: enforce genre)
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "name must be a non-empty string"}

        if not isinstance(genre, str) or not genre.strip():
            return {"success": False, "error": "genre must be a non-empty string"}

        if not isinstance(popularity_index, (int, float)):
            return {"success": False, "error": "popularity_index must be a number"}

        # Construct station info
        station_info = {
            "station_id": station_id,
            "name": name,
            "genre": genre,
            "streaming_url": streaming_url,
            "popularity_index": float(popularity_index),
            "is_featured": bool(is_featured),
            "is_trending": bool(is_trending),
            "description": description
        }

        self.stations[station_id] = station_info

        return {"success": True, "message": "Radio station added successfully."}

    def update_radio_station(self, station_id: str, update_data: dict) -> dict:
        """
        Modify metadata (such as name, genre, url, etc.) or status (is_featured, is_trending) of an existing radio station.

        Args:
            station_id (str): Unique station identifier (must already exist).
            update_data (dict): Fields and new values to update. Allowed keys:
                'name', 'genre', 'streaming_url', 'popularity_index',
                'is_featured', 'is_trending', 'description'

        Returns:
            dict: 
                On success: { "success": True, "message": "Station updated successfully" }
                On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Cannot update station_id.
            - Genre (if provided) must be valid (if genre set known, else accept any).
            - Streaming URL (if provided) must be non-empty string.
            - Only defined fields may be updated; must provide at least one updatable field.
        """
        # Check station exists
        if station_id not in self.stations:
            return { "success": False, "error": "Station does not exist" }

        # Set of fields that are allowed to be updated
        updatable_fields = {
            "name", "genre", "streaming_url", "popularity_index",
            "is_featured", "is_trending", "description"
        }

        # Filter actual update fields
        real_update_fields = {k: v for k, v in update_data.items() if k in updatable_fields}
        if not real_update_fields:
            return { "success": False, "error": "No updatable fields provided" }

        # (Optional) If station genres set (e.g., self.genres), enforce; otherwise, skip
        if 'genre' in real_update_fields:
            if hasattr(self, 'genres') and real_update_fields['genre'] not in getattr(self, 'genres'):
                return { "success": False, "error": "Invalid genre provided" }

        # Streaming URL should be a non-empty string if present
        if 'streaming_url' in real_update_fields:
            url = real_update_fields['streaming_url']
            if not isinstance(url, str) or not url.strip():
                return { "success": False, "error": "Invalid streaming_url provided" }

        # Type checks for booleans
        if 'is_featured' in real_update_fields and not isinstance(real_update_fields['is_featured'], bool):
            return { "success": False, "error": "is_featured must be boolean" }
        if 'is_trending' in real_update_fields and not isinstance(real_update_fields['is_trending'], bool):
            return { "success": False, "error": "is_trending must be boolean" }

        # Update the station info in place
        for k, v in real_update_fields.items():
            self.stations[station_id][k] = v

        return { "success": True, "message": "Station updated successfully" }

    def remove_radio_station(self, station_id: str) -> dict:
        """
        Remove a radio station from the catalog (fully deletes station entry), and cleans up its presence from
        featured and trending lists.

        Args:
            station_id (str): The unique identifier of the radio station to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Station <station_id> removed from catalog."
            }
            or
            {
                "success": False,
                "error": "<error_reason>"
            }

        Constraints:
            - Can only remove stations that exist in the catalog.
            - Station must also be removed from featured and trending station lists.
            - No lingering references in curated lists.
        """
        # Check input
        if not isinstance(station_id, str):
            return {"success": False, "error": "station_id must be a string"}

        # Check station existence
        if station_id not in self.stations:
            return {"success": False, "error": f"Station {station_id} does not exist in catalog"}

        # Remove from catalog
        del self.stations[station_id]

        # Remove from featured stations
        if station_id in self.featured_stations["station_ids"]:
            idx = self.featured_stations["station_ids"].index(station_id)
            self.featured_stations["station_ids"].pop(idx)
            if idx < len(self.featured_stations["display_position"]):
                self.featured_stations["display_position"].pop(idx)

        # Remove from trending stations
        if station_id in self.trending_stations["station_ids"]:
            self.trending_stations["station_ids"].remove(station_id)

        # Success message
        return {"success": True, "message": f"Station {station_id} removed from catalog."}

    def update_station_popularity(self, station_id: str, delta_popularity: float) -> dict:
        """
        Adjust a station's popularity index based on new listening activity.

        Args:
            station_id (str): Unique identifier of the station.
            delta_popularity (float): Amount to increment (or decrement) the popularity index.

        Returns:
            dict: {
                "success": True, 
                "message": "Popularity index updated successfully."
            }
            or
            dict: {
                "success": False,
                "error": str  # Reason for failure (station not found, invalid, etc.)
            }

        Constraints:
            - Station must exist in the platform catalog.
            - Station must be valid (active; streaming_url is present and non-empty).
            - The updated popularity_index must remain >= 0.
        """
        station = self.stations.get(station_id)
        if not station:
            return { "success": False, "error": "Station not found." }
        if not station.get("streaming_url"):
            return { "success": False, "error": "Station streaming URL missing or invalid." }

        old_popularity = station.get("popularity_index", 0.0)
        new_popularity = old_popularity + delta_popularity

        # Ensure non-negative (assuming popularity_index cannot be negative)
        if new_popularity < 0:
            new_popularity = 0.0

        station["popularity_index"] = new_popularity

        return { "success": True, "message": "Popularity index updated successfully." }

    def update_user_listening_history(self, user_id: str, station_ids: list) -> dict:
        """
        Append station_ids to a user's listening history for personalization and statistics.

        Args:
            user_id (str): ID of the user whose history to update.
            station_ids (List[str]): List of station IDs to append to the user's listening history.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "message": "Appended N stations to user's listening history."
                }
                Failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - User must exist.
            - All station_ids must correspond to existing stations.
            - If user's listening_history is missing, initialize it as an empty list.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        # Check if all station_ids are valid
        invalid_ids = [sid for sid in station_ids if sid not in self.stations]
        if invalid_ids:
            return {"success": False, "error": f"Invalid station_ids: {invalid_ids}"}

        user = self.users[user_id]
        if "listening_history" not in user or not isinstance(user["listening_history"], list):
            user["listening_history"] = []
        user["listening_history"].extend(station_ids)
        return {
            "success": True,
            "message": f"Appended {len(station_ids)} station(s) to user's listening history."
        }

    def update_user_genre_preference(self, user_id: str, genres: list) -> dict:
        """
        Add or modify the genre preferences for a user profile.

        Args:
            user_id (str): Unique user identifier.
            genres (list of str): List of genre strings to record as user preferences.

        Returns:
            dict: 
                On success: { "success": True, "message": "User genre preference updated." }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - Genres (if an allowed genres set exists on self) must be drawn from the fixed genre set.
            - Genres list must be a list of non-empty strings.
        """
        # Validate user
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }

        # Validate genres
        if not isinstance(genres, list) or not all(isinstance(g, str) and g for g in genres):
            return { "success": False, "error": "Invalid genres list: must be a list of non-empty strings" }

        # If fixed genre set is available, validate
        allowed_genres = getattr(self, "allowed_genres", None)
        if allowed_genres is not None:
            invalid = [g for g in genres if g not in allowed_genres]
            if invalid:
                return { "success": False, "error": f"Invalid genres: {invalid}. Allowed: {list(allowed_genres)}" }
    
        # Update genre preference
        self.users[user_id]["genre_preference"] = genres

        return { "success": True, "message": "User genre preference updated." }


class OnlineRadioStreamingPlatform(BaseEnv):
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

    def get_featured_stations(self, **kwargs):
        return self._call_inner_tool('get_featured_stations', kwargs)

    def get_trending_stations(self, **kwargs):
        return self._call_inner_tool('get_trending_stations', kwargs)

    def get_station_by_id(self, **kwargs):
        return self._call_inner_tool('get_station_by_id', kwargs)

    def list_all_stations(self, **kwargs):
        return self._call_inner_tool('list_all_stations', kwargs)

    def list_stations_by_genre(self, **kwargs):
        return self._call_inner_tool('list_stations_by_genre', kwargs)

    def get_station_genres(self, **kwargs):
        return self._call_inner_tool('get_station_genres', kwargs)

    def get_station_popularity_ranking(self, **kwargs):
        return self._call_inner_tool('get_station_popularity_ranking', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_valid_stations(self, **kwargs):
        return self._call_inner_tool('get_valid_stations', kwargs)

    def get_station_status(self, **kwargs):
        return self._call_inner_tool('get_station_status', kwargs)

    def get_user_personalized_recommendations(self, **kwargs):
        return self._call_inner_tool('get_user_personalized_recommendations', kwargs)

    def update_featured_stations(self, **kwargs):
        return self._call_inner_tool('update_featured_stations', kwargs)

    def update_trending_stations(self, **kwargs):
        return self._call_inner_tool('update_trending_stations', kwargs)

    def add_radio_station(self, **kwargs):
        return self._call_inner_tool('add_radio_station', kwargs)

    def update_radio_station(self, **kwargs):
        return self._call_inner_tool('update_radio_station', kwargs)

    def remove_radio_station(self, **kwargs):
        return self._call_inner_tool('remove_radio_station', kwargs)

    def update_station_popularity(self, **kwargs):
        return self._call_inner_tool('update_station_popularity', kwargs)

    def update_user_listening_history(self, **kwargs):
        return self._call_inner_tool('update_user_listening_history', kwargs)

    def update_user_genre_preference(self, **kwargs):
        return self._call_inner_tool('update_user_genre_preference', kwargs)
