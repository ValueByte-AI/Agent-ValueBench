# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class TVShowInfo(TypedDict):
    show_id: str
    title: str
    description: str
    genres: List[str]              # List of genre_id
    cast: List[str]                # List of cast_id
    release_year: int
    show_similarity_ids: List[str] # List of similar show_id
    cover_image_url: str

class GenreInfo(TypedDict):
    genre_id: str
    name: str
    description: str

class CastMemberInfo(TypedDict):
    cast_id: str
    name: str
    role: str

class SeasonInfo(TypedDict):
    season_id: str
    show_id: str
    season_number: int
    total_episodes: int

class EpisodeInfo(TypedDict):
    episode_id: str
    season_id: str
    episode_number: int
    title: str
    description: str
    stream_url: str
    duration: float   # duration in minutes or seconds

class UserInfo(TypedDict, total=False):
    user_id: str
    preferences: List[str]         # List of genre_id
    watch_history: List[str]       # List of episode_id

class _GeneratedEnvImpl:
    def __init__(self):
        # TV Shows: {show_id: TVShowInfo}
        self.tv_shows: Dict[str, TVShowInfo] = {}

        # Genres: {genre_id: GenreInfo}
        self.genres: Dict[str, GenreInfo] = {}

        # Cast Members: {cast_id: CastMemberInfo}
        self.cast_members: Dict[str, CastMemberInfo] = {}

        # Seasons: {season_id: SeasonInfo}
        self.seasons: Dict[str, SeasonInfo] = {}

        # Episodes: {episode_id: EpisodeInfo}
        self.episodes: Dict[str, EpisodeInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each episode must be linked to exactly one season, and each season to exactly one show.
        # - Shows may belong to multiple genres and genres may include multiple shows.
        # - Show similarity must use a defined measure (e.g., shared genres or editorial curation).
        # - Streaming URLs must remain accessible and valid for episodes offered on the platform.

    def get_show_by_title(self, title: str) -> dict:
        """
        Retrieve metadata for a TV show(s) given its title (case-insensitive, trimmed).

        Args:
            title (str): The title of the TV show to search (case-insensitive).

        Returns:
            dict:
                - success: True, data: List[TVShowInfo] matching the title (may be empty).
                - success: False, error: "Show not found" if no match.

        Constraints:
            - No explicit uniqueness of show titles.
            - Matching is case-insensitive and ignores leading/trailing spaces.
        """
        search_title = title.strip().lower()
        matched_shows = [
            show_info for show_info in self.tv_shows.values()
            if show_info["title"].strip().lower() == search_title
        ]

        if not matched_shows:
            return { "success": False, "error": "Show not found" }
        return { "success": True, "data": matched_shows }

    def get_show_details(self, show_id: str) -> dict:
        """
        Fetch full details for a given show using show_id, including genres, cast,
        release year, description, and similarity list.

        Args:
            show_id (str): The unique identifier for the TV show.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "show_id": str,
                    "title": str,
                    "description": str,
                    "release_year": int,
                    "cover_image_url": str,
                    "genres": List[dict],         # Each dict: {genre_id, name, description}
                    "cast": List[dict],           # Each dict: {cast_id, name, role}
                    "similar_shows": List[dict],  # Each dict: {show_id, title}
                }
            } on success,

            or

            { "success": False, "error": str } on failure (e.g., show not found).

        Constraints:
            - If a genre/cast member/similar show is missing from relevant dictionary, skip it.
        """
        show = self.tv_shows.get(show_id)
        if not show:
            return { "success": False, "error": "Show not found" }

        # Get genre info
        genres = []
        for genre_id in show.get("genres", []):
            genre = self.genres.get(genre_id)
            if genre:
                genres.append({
                    "genre_id": genre["genre_id"],
                    "name": genre["name"],
                    "description": genre["description"]
                })

        # Get cast info
        cast = []
        for cast_id in show.get("cast", []):
            cast_member = self.cast_members.get(cast_id)
            if cast_member:
                cast.append({
                    "cast_id": cast_member["cast_id"],
                    "name": cast_member["name"],
                    "role": cast_member["role"]
                })

        # Get similar shows' simple info
        similar_shows = []
        for similar_id in show.get("show_similarity_ids", []):
            similar_show = self.tv_shows.get(similar_id)
            if similar_show:
                similar_shows.append({
                    "show_id": similar_show["show_id"],
                    "title": similar_show["title"]
                })

        details = {
            "show_id": show["show_id"],
            "title": show["title"],
            "description": show["description"],
            "release_year": show["release_year"],
            "cover_image_url": show["cover_image_url"],
            "genres": genres,
            "cast": cast,
            "similar_shows": similar_shows
        }

        return {"success": True, "data": details}

    def get_similar_shows_by_similarity_ids(self, show_id: str) -> dict:
        """
        Retrieve TV shows similar to the given show, based on the 'show_similarity_ids'
        field of that show.

        Args:
            show_id (str): The ID of the show for which to find similar shows.

        Returns:
            dict:
                success: True if retrieval was successful, False otherwise
                data: List[TVShowInfo] of similar shows (may be empty)
                error: (on failure) error message

        Constraints:
            - The show_id must exist in the catalog.
            - Returns only existing, valid similar show entries.
        """
        # Check if the provided show_id exists
        if show_id not in self.tv_shows:
            return { "success": False, "error": "Show not found" }

        show_info = self.tv_shows[show_id]
        sim_ids = show_info.get("show_similarity_ids", [])
        result = []

        for sim_id in sim_ids:
            if sim_id in self.tv_shows:
                result.append(self.tv_shows[sim_id])

        return { "success": True, "data": result }

    def get_shows_by_genre(self, genre_ids: list) -> dict:
        """
        Fetch all TV shows belonging to one or more specified genres.

        Args:
            genre_ids (List[str]): List of genre_id values (must exist in catalog).

        Returns:
            dict: {
                "success": True,
                "data": List[TVShowInfo],
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - All provided genre_ids must exist in the genres collection.
            - Returns all shows where at least one of their genres matches any genre_id.
            - If genre_ids is empty, returns empty list.
        """
        # Validate genre_ids
        if not isinstance(genre_ids, list):
            return {"success": False, "error": "genre_ids must be a list of genre_id strings"}
        if not all(isinstance(gid, str) for gid in genre_ids):
            return {"success": False, "error": "Each genre_id must be a string"}

        if len(genre_ids) == 0:
            return { "success": True, "data": [] }
    
        invalid_genres = [gid for gid in genre_ids if gid not in self.genres]
        if invalid_genres:
            return {
                "success": False,
                "error": f"Invalid genre_id(s): {', '.join(invalid_genres)}"
            }

        genre_set = set(genre_ids)
        result = [
            show for show in self.tv_shows.values()
            if genre_set.intersection(set(show.get("genres", [])))
        ]
        return { "success": True, "data": result }

    def get_genres_for_show(self, show_id: str) -> dict:
        """
        Return the list of GenreInfo objects for a given show_id.

        Args:
            show_id (str): The ID of the TV show to query.

        Returns:
            dict: {
                "success": True,
                "data": List[GenreInfo]  # List of genre info objects for the show (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # "Show not found"
            }

        Constraints:
            - The show_id must exist in the catalog.
            - Nonexistent genre_ids in the show's genres list are ignored/skipped.
        """
        show = self.tv_shows.get(show_id)
        if not show:
            return { "success": False, "error": "Show not found" }
        genre_ids = show.get("genres", [])
        genres = [self.genres[g_id] for g_id in genre_ids if g_id in self.genres]
        return { "success": True, "data": genres }

    def get_cast_for_show(self, show_id: str) -> dict:
        """
        Retrieve cast details (CastMemberInfo) for all cast members of a show.

        Args:
            show_id (str): The ID of the TV show.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[CastMemberInfo]  # details of all cast in the show
                }
                or
                {
                    "success": False,
                    "error": str  # Show does not exist
                }

        Constraints:
            - Only shows that exist can be queried.
            - If referenced cast members are missing, they are skipped.
        """
        show = self.tv_shows.get(show_id)
        if not show:
            return { "success": False, "error": "Show does not exist" }

        cast_ids = show.get("cast", [])
        cast_info_list = [
            self.cast_members[cast_id]
            for cast_id in cast_ids
            if cast_id in self.cast_members
        ]
        return { "success": True, "data": cast_info_list }

    def get_seasons_for_show(self, show_id: str) -> dict:
        """
        Retrieve all seasons (SeasonInfo) of the specified show, ordered by season_number.

        Args:
            show_id (str): Identifier of the TV show.

        Returns:
            dict: {
                "success": True,
                "data": List[SeasonInfo],  # Ordered by season_number, possibly empty if no seasons
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., show does not exist
            }

        Constraints:
            - The show_id must exist in the catalog.
            - Return an empty list if the show exists but has no seasons.
            - List must be ordered by season_number.
        """
        if show_id not in self.tv_shows:
            return { "success": False, "error": "Show does not exist" }

        seasons = [
            season_info
            for season_info in self.seasons.values()
            if season_info["show_id"] == show_id
        ]
        # Order by season_number
        seasons_ordered = sorted(seasons, key=lambda s: s["season_number"])

        return { "success": True, "data": seasons_ordered }

    def get_season_by_number(self, show_id: str, season_number: int) -> dict:
        """
        Retrieve a specific season for a given show by show_id and season_number.

        Args:
            show_id (str): The unique identifier of the TV show.
            season_number (int): The ordinal number of the season.

        Returns:
            dict: {
                "success": True,
                "data": SeasonInfo,    # metadata for the requested season
            }
            OR
            {
                "success": False,
                "error": str           # explanation (e.g., "No such season for show")
            }

        Constraints:
            - Returns the first matching season found for the specified show_id and season_number.
            - Returns failure if no such matching season exists.
        """
        for season in self.seasons.values():
            if season['show_id'] == show_id and season['season_number'] == season_number:
                return { "success": True, "data": season }
        return { "success": False, "error": "No such season for show" }

    def get_episodes_for_season(self, season_id: str) -> dict:
        """
        Fetch all episodes for a particular season, ordered by episode_number.

        Args:
            season_id (str): The season's unique identifier.

        Returns:
            dict:
                - success: True/False
                - data: List[EpisodeInfo] (if success) (may be empty)
                - error: str (if not success)
        Constraints:
            - season_id must exist in self.seasons.
            - Episodes are ordered by episode_number ascending.
        """
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        episodes = [
            episode_info for episode_info in self.episodes.values()
            if episode_info["season_id"] == season_id
        ]
        episodes_sorted = sorted(episodes, key=lambda ep: ep["episode_number"])

        return {"success": True, "data": episodes_sorted}

    def get_episode_stream_urls_for_season(self, season_id: str) -> dict:
        """
        Given a season_id, fetch the streaming URLs for all episodes in that season.

        Args:
            season_id (str): The ID of the season for which to retrieve episode stream URLs.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[Dict[str, str]]
                            # Each dict contains { "episode_id": ..., "episode_number": ..., "stream_url": ... }
                            # List may be empty if the season has no episodes.
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # e.g. "Season not found"
                    }

        Constraints:
            - The provided season_id must exist.
            - Will not check stream URL validity here; only returns what is stored.
        """
        if season_id not in self.seasons:
            return { "success": False, "error": "Season not found" }

        result = [
            {
                "episode_id": ep_info["episode_id"],
                "episode_number": ep_info["episode_number"],
                "stream_url": ep_info["stream_url"]
            }
            for ep_info in self.episodes.values()
            if ep_info["season_id"] == season_id
        ]

        return { "success": True, "data": result }

    def validate_stream_url_accessibility(self, episode_ids: list) -> dict:
        """
        Verify that the streaming URLs for the given set of episodes are currently valid and accessible.

        Args:
            episode_ids (List[str]): List of episode_id for which to check stream URL accessibility.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, bool]  # episode_id -> True (accessible) or False (not accessible/invalid id/missing url)
            }

        Constraints:
            - Invalid or missing episode IDs are marked as inaccessible (False).
            - Streaming URLs that are missing, empty, or do not start with "http"/"https" are considered not accessible.

        Notes:
            - Accessibility simulation: For demonstration, only URLs that start with "http://" or "https://" are considered accessible.
        """
        result = {}
        for eid in episode_ids:
            ep_info = self.episodes.get(eid)
            if not ep_info:
                result[eid] = False
                continue
            url = ep_info.get("stream_url", "")
            # Simulate accessibility by simple check
            if isinstance(url, str) and url.startswith(("http://", "https://")) and len(url) > len("http://"):
                result[eid] = True
            else:
                result[eid] = False
        return { "success": True, "data": result }

    def get_user_watch_history(self, user_id: str) -> dict:
        """
        Retrieve the watch history (list of episode_ids) for a user.
    
        Args:
            user_id (str): The identifier of the user.
    
        Returns:
            dict:
                - { "success": True, "data": List[str] } if user exists. (data is a possibly empty list of episode_ids)
                - { "success": False, "error": str } if user_id not found.
    
        Constraints:
            - User must exist in the system.
            - If a user has no watch_history, returns an empty list.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        watch_history = user.get("watch_history", [])
        return { "success": True, "data": watch_history }

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Retrieve the preferred genres (genre_id list) for the specified user.

        Args:
            user_id (str): The ID of the user to query.

        Returns:
            dict:
                success: True, data: List[str] -- preferred genre IDs, or empty list if none.
                success: False, error: str -- e.g., "User not found"

        Constraints:
            - user_id must exist in the users dictionary.
            - If user exists but has no preferences recorded, returns empty list.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        preferences = user.get("preferences", [])
        if not isinstance(preferences, list):
            # Defensive: if corrupted data, treat as empty
            preferences = []
        return { "success": True, "data": preferences }

    def record_user_watch_episode(self, user_id: str, episode_id: str) -> dict:
        """
        Add an episode to a user's watch history (mark as watched).

        Args:
            user_id (str): The user's unique identifier.
            episode_id (str): The episode's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Episode added to user's watch history."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The user and episode must both exist.
            - The episode should not appear multiple times in the user's history.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}
        if episode_id not in self.episodes:
            return {"success": False, "error": "Episode not found."}

        user_info = self.users[user_id]
        if "watch_history" not in user_info or not isinstance(user_info["watch_history"], list):
            user_info["watch_history"] = []

        # Remove if it's already in the history, then add to the end
        if episode_id in user_info["watch_history"]:
            user_info["watch_history"].remove(episode_id)

        user_info["watch_history"].append(episode_id)
        return {"success": True, "message": "Episode added to user's watch history."}

    def update_user_preferences(self, user_id: str, new_preferences: list) -> dict:
        """
        Modify the set of genre_ids representing a user's preferred genres.

        Args:
            user_id (str): The identifier of the user.
            new_preferences (List[str]): The new list of genre_ids representing the user's preferences.

        Returns:
            dict: {
                "success": True,
                "message": "User preferences updated."
            }
            or
            {
                "success": False,
                "error": "Descriptive error message"
            }

        Constraints:
            - user_id must exist in the users dictionary.
            - Each genre_id in new_preferences must exist in genres.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Validate all genre_ids
        for genre_id in new_preferences:
            if genre_id not in self.genres:
                return { "success": False, "error": f"Genre '{genre_id}' does not exist." }

        # Update user preferences
        self.users[user_id]["preferences"] = list(new_preferences)

        return { "success": True, "message": "User preferences updated." }

    def add_show_similarity_relation(self, base_show_id: str, similar_show_id: str) -> dict:
        """
        Add a similarity relationship from 'base_show_id' to 'similar_show_id'.
        This adds 'similar_show_id' to the 'show_similarity_ids' list of the base show.

        Args:
            base_show_id (str): The main show_id to which a similar show will be added.
            similar_show_id (str): The show_id to add as a similar show.

        Returns:
            dict: {
                "success": True,
                "message": "Similarity relation added between <base_show_id> and <similar_show_id>"
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Both show IDs must exist in the catalog.
            - A show cannot be made similar to itself.
            - No duplicate similarity entries for the same show.
        """
        # Check both shows exist
        if base_show_id not in self.tv_shows:
            return {"success": False, "error": f"Base show_id '{base_show_id}' does not exist."}
        if similar_show_id not in self.tv_shows:
            return {"success": False, "error": f"Similar show_id '{similar_show_id}' does not exist."}
        # No self-similarity
        if base_show_id == similar_show_id:
            return {"success": False, "error": "A show cannot be marked similar to itself."}
        # No duplicates
        current_similars = self.tv_shows[base_show_id].get("show_similarity_ids", [])
        if similar_show_id in current_similars:
            return {"success": False, "error": f"Show '{similar_show_id}' is already marked as similar to '{base_show_id}'."}

        # Add the relation
        current_similars.append(similar_show_id)
        self.tv_shows[base_show_id]["show_similarity_ids"] = current_similars

        return {
            "success": True,
            "message": f"Similarity relation added between '{base_show_id}' and '{similar_show_id}'."
        }

    def remove_show_similarity_relation(self, source_show_id: str, target_show_id: str) -> dict:
        """
        Remove a show_id from another show's similarity list.

        Args:
            source_show_id (str): The show whose similarity list is to be updated.
            target_show_id (str): The show to remove from the similarity list.

        Returns:
            dict: {
                "success": True,
                "message": "Show similarity removed from list."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Both show IDs must exist in the catalog.
            - The similarity relation must exist before removal.
        """
        # Check if both shows exist
        if source_show_id not in self.tv_shows:
            return {"success": False, "error": f"Source show_id '{source_show_id}' does not exist."}
        if target_show_id not in self.tv_shows:
            return {"success": False, "error": f"Target show_id '{target_show_id}' does not exist."}

        similarity_list = self.tv_shows[source_show_id].get("show_similarity_ids", [])
        if target_show_id not in similarity_list:
            return {"success": False, "error": f"Target show_id '{target_show_id}' is not in {source_show_id}'s similarity list."}

        # Remove the target show_id from the list
        similarity_list.remove(target_show_id)
        self.tv_shows[source_show_id]["show_similarity_ids"] = similarity_list

        return {"success": True, "message": "Show similarity removed from list."}

    def update_episode_stream_url(self, episode_id: str, new_stream_url: str) -> dict:
        """
        Update the stream_url for a specific episode.

        Args:
            episode_id (str): The ID of the episode to update.
            new_stream_url (str): The new streaming URL to set for the episode.

        Returns:
            dict:
                On success: { "success": True, "message": "Stream URL updated for episode <episode_id>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The episode must exist in the catalog.
            - The new streaming URL must be non-empty (basic validation).
            - (Not checked here) URL accessibility should be ensured elsewhere.
        """
        episode = self.episodes.get(episode_id)
        if not episode:
            return { "success": False, "error": "Episode with given ID does not exist" }

        if not new_stream_url or not isinstance(new_stream_url, str):
            return { "success": False, "error": "Provided streaming URL is invalid or empty" }

        # Update and persist the change
        episode["stream_url"] = new_stream_url

        return { "success": True, "message": f"Stream URL updated for episode {episode_id}" }

    def add_new_show(
        self,
        show_id: str,
        title: str,
        description: str,
        genres: list,
        cast: list,
        release_year: int,
        show_similarity_ids: list,
        cover_image_url: str
    ) -> dict:
        """
        Add a new TV show to the catalog with all associated metadata.

        Args:
            show_id (str): Unique ID for the TV show.
            title (str): Title of the show.
            description (str): Description/summary of the show.
            genres (List[str]): List of genre_ids for the show (must exist).
            cast (List[str]): List of cast_ids for the show (must exist).
            release_year (int): Release year of the show.
            show_similarity_ids (List[str]): List of similar show_ids (should exist).
            cover_image_url (str): URL for the show's cover image.

        Returns:
            dict: {
                "success": True,
                "message": "Show <title> (<show_id>) added"
            }
            or
            {
                "success": False,
                "error": "...reason..."
            }

        Constraints:
            - show_id must be unique.
            - genres must refer to existing genre_ids.
            - cast must refer to existing cast_ids.
            - show_similarity_ids should refer to existing show_ids (warnings if not).
        """
        if show_id in self.tv_shows:
            return { "success": False, "error": f"Show ID '{show_id}' already exists in the catalog." }

        # Validate genres
        nonexistent_genres = [gid for gid in genres if gid not in self.genres]
        if nonexistent_genres:
            return { "success": False, "error": f"Genre IDs do not exist: {nonexistent_genres}" }

        # Validate cast
        nonexistent_cast = [cid for cid in cast if cid not in self.cast_members]
        if nonexistent_cast:
            return { "success": False, "error": f"Cast member IDs do not exist: {nonexistent_cast}" }

        # Validate similar show IDs: keep valid ones and warn about missing ids.
        nonexistent_similars = [sid for sid in show_similarity_ids if sid not in self.tv_shows]
        valid_similarity_ids = [sid for sid in show_similarity_ids if sid in self.tv_shows]
    
        # Add new show
        self.tv_shows[show_id] = {
            "show_id": show_id,
            "title": title,
            "description": description,
            "genres": genres,
            "cast": cast,
            "release_year": release_year,
            "show_similarity_ids": valid_similarity_ids,
            "cover_image_url": cover_image_url
        }

        response = {
            "success": True,
            "message": f"Show '{title}' ({show_id}) added"
        }
        if nonexistent_similars:
            response["warnings"] = [f"Similar show IDs ignored because they do not exist: {nonexistent_similars}"]
        return response

    def add_new_season(self, season_id: str, show_id: str, season_number: int, total_episodes: int) -> dict:
        """
        Add a new season to an existing TV show.

        Args:
            season_id (str): Unique identifier for the new season.
            show_id (str): Identifier of the TV show to which the season will be added.
            season_number (int): The season's sequential number for the show.
            total_episodes (int): The total number of episodes in this season.

        Returns:
            dict: {
                "success": True,
                "message": "Season added to show <show_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - show_id must exist in self.tv_shows.
            - season_id must be unique.
            - Optionally, season_number for the given show should not already exist.
        """
        if season_id in self.seasons:
            return {"success": False, "error": f"Season ID '{season_id}' already exists."}
        if show_id not in self.tv_shows:
            return {"success": False, "error": f"Show ID '{show_id}' does not exist."}

        for s in self.seasons.values():
            if s["show_id"] == show_id and s["season_number"] == season_number:
                return {
                    "success": False,
                    "error": f"Show '{show_id}' already has a season number {season_number}."
                }

        season_info: SeasonInfo = {
            "season_id": season_id,
            "show_id": show_id,
            "season_number": season_number,
            "total_episodes": total_episodes
        }
        self.seasons[season_id] = season_info
        return {"success": True, "message": f"Season {season_number} (ID: {season_id}) added to show {show_id}."}

    def add_new_episode(
        self,
        episode_id: str,
        season_id: str,
        episode_number: int,
        title: str,
        description: str,
        stream_url: str,
        duration: float
    ) -> dict:
        """
        Add a new episode to a season, ensuring all links and constraints.

        Args:
            episode_id (str): Unique identifier for the episode.
            season_id (str): Identifier for the season this episode belongs to.
            episode_number (int): The episode's number within the season (must be unique in the season).
            title (str): Episode title.
            description (str): Episode description.
            stream_url (str): Streaming URL (must not be empty, and not in use by another episode).
            duration (float): Duration in minutes or seconds.

        Returns:
            dict: On success:
                {"success": True, "message": "Episode <episode_id> added to season <season_id>." }
            On failure:
                {"success": False, "error": "reason" }

        Constraints checked:
            - episode_id must be unique.
            - season_id must exist and be linked to a show.
            - episode_number must be unique in the season.
            - stream_url must be non-empty (not validated for accessibility here), and not duplicated in another episode.
            - Update the season's total_episodes if necessary.
        """
        # Episode id must be unique
        if episode_id in self.episodes:
            return {"success": False, "error": "Episode ID already exists"}

        # Season id must exist
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        # Episode number must be unique within this season
        for ep in self.episodes.values():
            if ep["season_id"] == season_id and ep["episode_number"] == episode_number:
                return {"success": False, "error": f"Episode number {episode_number} already exists in this season"}

        # Stream URL must be non-empty
        if not stream_url or not isinstance(stream_url, str) or stream_url.strip() == "":
            return {"success": False, "error": "Stream URL is empty or invalid"}
    
        # Stream URL must not already be in use by another episode
        for ep in self.episodes.values():
            if ep["stream_url"] == stream_url:
                return {"success": False, "error": "Stream URL already in use by another episode"}

        # All fields provided; construct and add EpisodeInfo
        episode_info = {
            "episode_id": episode_id,
            "season_id": season_id,
            "episode_number": episode_number,
            "title": title,
            "description": description,
            "stream_url": stream_url,
            "duration": duration
        }
        self.episodes[episode_id] = episode_info

        # Update season's total_episodes if necessary
        season = self.seasons[season_id]
        if episode_number > season["total_episodes"]:
            season["total_episodes"] = episode_number

        return {
            "success": True,
            "message": f"Episode {episode_id} added to season {season_id}."
        }

    def delete_show(self, show_id: str) -> dict:
        """
        Remove a show and all its related seasons/episodes and similarity references from the catalog.

        Args:
            show_id (str): The unique identifier of the TV show to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Show and all related data deleted."
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Remove all related seasons and episodes.
            - Remove show_id from all other shows' similarity lists.
            - Do NOT delete CastMember or Genre entities.
            - If show does not exist, return error.
        """
        # Check if show exists
        if show_id not in self.tv_shows:
            return { "success": False, "error": "Show does not exist" }

        # Delete all seasons associated with this show
        seasons_to_delete = [sid for sid, season in self.seasons.items() if season['show_id'] == show_id]
        episodes_deleted = 0
        for sid in seasons_to_delete:
            # Delete all episodes under this season
            episode_ids = [eid for eid, ep in self.episodes.items() if ep['season_id'] == sid]
            episodes_deleted += len(episode_ids)
            for eid in episode_ids:
                del self.episodes[eid]
            # Delete season itself
            del self.seasons[sid]

        # Remove this show from all other shows' show_similarity_ids lists
        for other_show in self.tv_shows.values():
            if show_id in other_show.get('show_similarity_ids', []):
                other_show['show_similarity_ids'] = [sid for sid in other_show['show_similarity_ids'] if sid != show_id]

        # Delete the show itself
        del self.tv_shows[show_id]

        return { "success": True, "message": "Show and all related data deleted." }

    def delete_episode(self, episode_id: str) -> dict:
        """
        Remove an episode from the catalog (admin operation).

        Args:
            episode_id (str): The unique identifier of the episode to delete.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Episode <episode_id> deleted."
                }
                OR
                {
                    "success": False,
                    "error": "Episode does not exist."
                }

        Constraints:
            - Episode must exist.
            - Episode will be removed from all user watch_history if present (to avoid dangling references).
        """
        if episode_id not in self.episodes:
            return { "success": False, "error": "Episode does not exist." }

        # Remove episode
        del self.episodes[episode_id]

        # Clean up from user watch history
        for user in self.users.values():
            if "watch_history" in user and episode_id in user["watch_history"]:
                user["watch_history"] = [eid for eid in user["watch_history"] if eid != episode_id]

        return { "success": True, "message": f"Episode {episode_id} deleted." }

    def correct_metadata(
        self, 
        entity_type: str, 
        entity_id: str, 
        updates: dict
    ) -> dict:
        """
        Edit and fix existing metadata for any catalog entity (tv_show, genre, cast_member, season, episode).
    
        Args:
            entity_type (str): One of "tv_show", "genre", "cast_member", "season", "episode".
            entity_id (str): The unique ID of the entity (show_id, genre_id, etc.).
            updates (dict): A dictionary mapping attribute names to new values to update.

        Returns:
            dict: 
                On success: {"success": True, "message": "Entity metadata updated successfully."}
                On error:   {"success": False, "error": <reason>}

        Constraints:
            - entity_type must be valid.
            - entity_id must exist for that type.
            - May only update mutable non-ID attributes.
            - Updates to unrecognized or forbidden attributes are ignored.
        """
        # Map entity_type to storage dict and id key
        entity_map = {
            "tv_show":   (self.tv_shows,      "show_id"),
            "genre":     (self.genres,        "genre_id"),
            "cast_member": (self.cast_members, "cast_id"),
            "season":    (self.seasons,       "season_id"),
            "episode":   (self.episodes,      "episode_id"),
        }
        if entity_type not in entity_map:
            return { "success": False, "error": "Invalid entity_type." }
        store, id_key = entity_map[entity_type]
        # Lookup entity
        if entity_id not in store:
            return { "success": False, "error": f"{entity_type} with given ID not found." }
        if not isinstance(updates, dict) or not updates:
            return { "success": False, "error": "No updates provided or update format invalid." }
        # Immutable/forbidden fields
        forbidden_fields = [id_key]
        # Perform update, only for allowed and existing attributes
        updated = False
        entity_info = store[entity_id]
        for field, value in updates.items():
            if field in forbidden_fields:
                continue  # skip immutable
            if field not in entity_info:
                continue  # skip non-existent
            entity_info[field] = value
            updated = True
        if not updated:
            return { "success": False, "error": "No valid updatable attributes in updates." }
        return { "success": True, "message": "Entity metadata updated successfully." }


class TVShowCatalogStreamingPlatform(BaseEnv):
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

    def get_show_by_title(self, **kwargs):
        return self._call_inner_tool('get_show_by_title', kwargs)

    def get_show_details(self, **kwargs):
        return self._call_inner_tool('get_show_details', kwargs)

    def get_similar_shows_by_similarity_ids(self, **kwargs):
        return self._call_inner_tool('get_similar_shows_by_similarity_ids', kwargs)

    def get_shows_by_genre(self, **kwargs):
        return self._call_inner_tool('get_shows_by_genre', kwargs)

    def get_genres_for_show(self, **kwargs):
        return self._call_inner_tool('get_genres_for_show', kwargs)

    def get_cast_for_show(self, **kwargs):
        return self._call_inner_tool('get_cast_for_show', kwargs)

    def get_seasons_for_show(self, **kwargs):
        return self._call_inner_tool('get_seasons_for_show', kwargs)

    def get_season_by_number(self, **kwargs):
        return self._call_inner_tool('get_season_by_number', kwargs)

    def get_episodes_for_season(self, **kwargs):
        return self._call_inner_tool('get_episodes_for_season', kwargs)

    def get_episode_stream_urls_for_season(self, **kwargs):
        return self._call_inner_tool('get_episode_stream_urls_for_season', kwargs)

    def validate_stream_url_accessibility(self, **kwargs):
        return self._call_inner_tool('validate_stream_url_accessibility', kwargs)

    def get_user_watch_history(self, **kwargs):
        return self._call_inner_tool('get_user_watch_history', kwargs)

    def get_user_preferences(self, **kwargs):
        return self._call_inner_tool('get_user_preferences', kwargs)

    def record_user_watch_episode(self, **kwargs):
        return self._call_inner_tool('record_user_watch_episode', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def add_show_similarity_relation(self, **kwargs):
        return self._call_inner_tool('add_show_similarity_relation', kwargs)

    def remove_show_similarity_relation(self, **kwargs):
        return self._call_inner_tool('remove_show_similarity_relation', kwargs)

    def update_episode_stream_url(self, **kwargs):
        return self._call_inner_tool('update_episode_stream_url', kwargs)

    def add_new_show(self, **kwargs):
        return self._call_inner_tool('add_new_show', kwargs)

    def add_new_season(self, **kwargs):
        return self._call_inner_tool('add_new_season', kwargs)

    def add_new_episode(self, **kwargs):
        return self._call_inner_tool('add_new_episode', kwargs)

    def delete_show(self, **kwargs):
        return self._call_inner_tool('delete_show', kwargs)

    def delete_episode(self, **kwargs):
        return self._call_inner_tool('delete_episode', kwargs)

    def correct_metadata(self, **kwargs):
        return self._call_inner_tool('correct_metadata', kwargs)
