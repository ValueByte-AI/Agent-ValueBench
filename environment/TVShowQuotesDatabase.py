# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



class TVShowInfo(TypedDict):
    show_id: str
    title: str
    genre: str
    description: str

class SeasonInfo(TypedDict):
    season_id: str
    show_id: str
    season_number: int
    year: int

class EpisodeInfo(TypedDict):
    episode_id: str
    season_id: str
    episode_number: int
    title: str
    air_date: str

class QuoteInfo(TypedDict, total=False):
    quote_id: str
    episode_id: str
    character_id: str
    text: str
    timestamp: Optional[float]  # optional

class CharacterInfo(TypedDict):
    character_id: str
    name: str
    show_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Shows: {show_id: TVShowInfo}
        self.shows: Dict[str, TVShowInfo] = {}

        # Seasons: {season_id: SeasonInfo}
        # Each season must be associated with a TV show (via show_id)
        # season_number must be unique within its parent TV show
        self.seasons: Dict[str, SeasonInfo] = {}

        # Episodes: {episode_id: EpisodeInfo}
        # Each episode must be associated with a season (via season_id)
        # episode_number must be unique within its parent season
        self.episodes: Dict[str, EpisodeInfo] = {}

        # Quotes: {quote_id: QuoteInfo}
        # Each quote must be associated with an episode (via episode_id) and a character (via character_id)
        self.quotes: Dict[str, QuoteInfo] = {}

        # Characters: {character_id: CharacterInfo}
        # Each character is associated with a TV show (via show_id)
        self.characters: Dict[str, CharacterInfo] = {}

        # Constraints:
        # - Each season must be associated with a TV show.
        # - Each episode must be associated with a season.
        # - Each quote must be associated with an episode and a character.
        # - season_number must be unique within a show.
        # - episode_number must be unique within a season.

    def get_show_by_title(self, title: str) -> dict:
        """
        Retrieve TV show information matching the given title.

        Args:
            title (str): The TV show's title to search for.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": TVShowInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Show not found"
                    }
        Constraints:
            - Title matching is case-sensitive.
            - Returns the first show found with the exact title match.
        """
        for show in self.shows.values():
            if show["title"] == title:
                return {"success": True, "data": show}
        return {"success": False, "error": "Show not found"}

    def list_shows(self) -> dict:
        """
        Retrieve a list of all TV shows in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TVShowInfo]  # a list of TVShowInfo dicts (may be empty)
            }

        No constraints or errors unless internal state is corrupted.
        """
        result = list(self.shows.values())
        return {"success": True, "data": result}

    def get_season_by_number(self, season_number: int, show_id: Optional[str] = None) -> dict:
        """
        Retrieve all seasons matching a given season number; optionally restrict to a specific show.

        Args:
            season_number (int): The target season number to search for.
            show_id (Optional[str]): If provided, restrict search to this TV show.

        Returns:
            dict: {
                "success": True,
                "data": List[SeasonInfo]  # All matching seasons (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # error description
            }

        Constraints:
            - If show_id is provided, it must exist in the database.
            - season_number must be an integer.
        """
        if not isinstance(season_number, int):
            return {"success": False, "error": "season_number must be an integer"}

        if show_id is not None and show_id not in self.shows:
            return {"success": False, "error": "show_id does not exist"}

        result = [
            season for season in self.seasons.values()
            if season["season_number"] == season_number and (show_id is None or season["show_id"] == show_id)
        ]

        return {"success": True, "data": result}

    def list_seasons_for_show(self, show_id: str) -> dict:
        """
        Retrieve all seasons for a specific TV show.

        Args:
            show_id (str): The unique identifier for the TV show.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[SeasonInfo],  # May be empty if no seasons
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure ("TV show not found")
                    }

        Constraints:
            - The TV show (show_id) must exist.
        """
        if show_id not in self.shows:
            return {"success": False, "error": "TV show not found"}

        seasons = [
            season for season in self.seasons.values()
            if season["show_id"] == show_id
        ]
        return {"success": True, "data": seasons}

    def get_episodes_by_season(self, season_id: str) -> dict:
        """
        Retrieve all episodes that belong to a specific season.

        Args:
            season_id (str): The ID of the season for which to retrieve episodes.

        Returns:
            dict: {
                "success": True,
                "data": List[EpisodeInfo],  # All episodes in the specified season (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. if season_id does not exist
            }

        Constraints:
            - The provided season_id must exist in the database.
        """
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        episodes = [
            episode_info for episode_info in self.episodes.values()
            if episode_info["season_id"] == season_id
        ]
        return {"success": True, "data": episodes}

    def get_episode_by_number(self, season_id: str, episode_number: int) -> dict:
        """
        Retrieve a specific episode (metadata) by its number within a given season.

        Args:
            season_id (str): The ID of the season.
            episode_number (int): The episode number within that season.

        Returns:
            dict:
                {
                    "success": True,
                    "data": EpisodeInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - season_id must exist.
            - episode_number must match a unique episode in that season.
        """
        if season_id not in self.seasons:
            return { "success": False, "error": "Season does not exist" }
    
        for episode in self.episodes.values():
            if episode["season_id"] == season_id and episode["episode_number"] == episode_number:
                return { "success": True, "data": episode }
    
        return { "success": False, "error": "No such episode in the specified season" }

    def get_quotes_by_episode(self, episode_id: str) -> dict:
        """
        Retrieve all quotes that belong to a specific episode.

        Args:
            episode_id (str): The unique identifier of the episode.

        Returns:
            dict: {
                "success": True,
                "data": List[QuoteInfo],  # All quotes belonging to the given episode (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., episode does not exist
            }

        Constraints:
            - episode_id must exist in the database.
        """
        if episode_id not in self.episodes:
            return { "success": False, "error": "Episode does not exist" }

        quotes = [q for q in self.quotes.values() if q["episode_id"] == episode_id]
        return { "success": True, "data": quotes }

    def get_quotes_by_season(self, season_id: str) -> dict:
        """
        Retrieve all quotes for the given season (aggregating via the season's episodes).

        Args:
            season_id (str): The ID of the season.

        Returns:
            dict: {
                "success": True,
                "data": List[QuoteInfo],  # List of quotes for all episodes in the season
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Season does not exist"
            }
        Constraints:
            - The season with the given season_id must exist.
        """
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        # Find all episode_ids belonging to this season
        episode_ids = [
            eid for eid, epinfo in self.episodes.items()
            if epinfo["season_id"] == season_id
        ]
        # Now aggregate all quotes from those episodes
        quotes = [
            quote for quote in self.quotes.values()
            if quote["episode_id"] in episode_ids
        ]
        return {"success": True, "data": quotes}

    def get_quotes_by_show(self, show_id: str) -> dict:
        """
        Retrieve all quotes associated with a given TV show.

        Args:
            show_id (str): The unique identifier of the TV show.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[QuoteInfo]  # All quotes for the show's episodes (may be empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g. show not found)
                    }

        Constraints:
            - The given TV show must exist in the database.
        """
        if show_id not in self.shows:
            return {"success": False, "error": "TV show does not exist"}

        # Find all season_ids for this show
        season_ids = [season_id for season_id, season in self.seasons.items() if season["show_id"] == show_id]
        if not season_ids:
            return {"success": True, "data": []}

        # Find all episode_ids for these seasons
        episode_ids = [episode_id for episode_id, episode in self.episodes.items() if episode["season_id"] in season_ids]
        if not episode_ids:
            return {"success": True, "data": []}

        # Find all quotes for these episodes
        quotes = [quote for quote in self.quotes.values() if quote["episode_id"] in episode_ids]

        return {"success": True, "data": quotes}

    def get_quotes_by_character(self, character_id: str) -> dict:
        """
        Retrieve all quotes spoken by a specific character.

        Args:
            character_id (str): The unique identifier of the character.

        Returns:
            dict:
                - On success: {"success": True, "data": List[QuoteInfo]}
                - On failure (character_id not found): {"success": False, "error": str}

        Constraints:
            - The character_id must exist in the database.
            - If the character exists but has no quotes, returns an empty list in data.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character not found"}

        matching_quotes = [
            quote for quote in self.quotes.values()
            if quote.get("character_id") == character_id
        ]
        return {"success": True, "data": matching_quotes}

    def get_character_by_name(self, name: str) -> dict:
        """
        Retrieve a character info object by character name.

        Args:
            name (str): The full name of the character to look up.

        Returns:
            dict:
                {
                    "success": True,
                    "data": CharacterInfo
                }
                OR
                {
                    "success": False,
                    "error": "Character not found"
                }

        Notes:
            - If multiple characters share the same name, returns the first match encountered.
            - Name comparison is case-sensitive.
        """
        if not name:
            return { "success": False, "error": "Character name not provided" }
        for character in self.characters.values():
            if character["name"] == name:
                return { "success": True, "data": character }
        return { "success": False, "error": "Character not found" }

    def list_characters_for_show(self, show_id: str) -> dict:
        """
        Retrieve all characters that appear in a particular show.

        Args:
            show_id (str): The unique identifier for the TV show.

        Returns:
            dict: {
                "success": True,
                "data": List[CharacterInfo]
            }
            or
            {
                "success": False,
                "error": str  # "Show not found"
            }

        Constraints:
            - The show_id must reference an existing show in the database.
            - Characters are matched by the show_id attribute.
        """
        if show_id not in self.shows:
            return { "success": False, "error": "Show not found" }

        result = [
            character
            for character in self.characters.values()
            if character["show_id"] == show_id
        ]
        return { "success": True, "data": result }

    def get_quote_by_id(self, quote_id: str) -> dict:
        """
        Retrieve the details of a quote by its unique ID.

        Args:
            quote_id (str): The identifier of the quote to retrieve.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": QuoteInfo    # Dictionary of quote's details
                    }
                Else:
                    {
                        "success": False,
                        "error": "Quote not found"
                    }

        Constraints:
            - quote_id must exist in the database.
        """
        quote = self.quotes.get(quote_id)
        if not quote:
            return { "success": False, "error": "Quote not found" }
        return { "success": True, "data": quote }

    def add_tv_show(self, show_id: str, title: str, genre: str, description: str) -> dict:
        """
        Add a new TV show to the database.

        Args:
            show_id (str): Unique identifier for the TV show.
            title (str): Title of the TV show.
            genre (str): Genre of the TV show.
            description (str): Description of the TV show.

        Returns:
            dict: {
                "success": True,
                "message": "TV show added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - show_id must be unique.
            - All fields must be non-empty strings.
        """
        # Check for required fields and non-empty values
        for field_name, value in [("show_id", show_id), ("title", title), ("genre", genre), ("description", description)]:
            if not isinstance(value, str) or not value.strip():
                return {
                    "success": False,
                    "error": f"Required field '{field_name}' is missing or empty."
                }
        # Check uniqueness of show_id
        if show_id in self.shows:
            return {"success": False, "error": "show_id already exists."}

        # Add the new TV show
        self.shows[show_id] = {
            "show_id": show_id,
            "title": title,
            "genre": genre,
            "description": description,
        }
        return {"success": True, "message": "TV show added successfully."}

    def edit_tv_show(
        self,
        show_id: str,
        title: str = None,
        genre: str = None,
        description: str = None
    ) -> dict:
        """
        Update the attributes (title, genre, description) of a TV show.
    
        Args:
            show_id (str): Identifier for the TV show to update.
            title (str, optional): New title (if updating).
            genre (str, optional): New genre (if updating).
            description (str, optional): New description (if updating).
    
        Returns:
            dict: {
                "success": True,
                "message": "TV show updated"
            } 
            OR
            {
                "success": False,
                "error": "TV show not found"
            }

        Constraints:
            - show_id must exist in database.
            - Only title, genre, and description can be updated.
        """
        if show_id not in self.shows:
            return {"success": False, "error": "TV show not found"}

        updated = False
        show = self.shows[show_id]
        if title is not None:
            show["title"] = title
            updated = True
        if genre is not None:
            show["genre"] = genre
            updated = True
        if description is not None:
            show["description"] = description
            updated = True

        # Silent no-op if nothing is changed (still a success)
        return {"success": True, "message": "TV show updated"}

    def delete_tv_show(self, show_id: str) -> dict:
        """
        Remove a TV show and all associated data: its seasons, all episodes in those seasons,
        all quotes in those episodes, and all characters of the show.

        Args:
            show_id (str): The unique ID of the TV show to delete.

        Returns:
            dict: {
                "success": True,
                "message": "TV show <show_id> and all associated data deleted"
            }
            or
            {
                "success": False,
                "error": "TV show not found"
            }

        Constraints:
            - TV show must exist.
            - All related data (seasons, episodes, quotes, characters) must be deleted as well.
        """
        if show_id not in self.shows:
            return {"success": False, "error": "TV show not found"}

        # Gather all seasons belonging to the show
        seasons_to_delete = [season_id for season_id, season in self.seasons.items()
                             if season["show_id"] == show_id]

        # Gather all episodes belonging to those seasons
        episodes_to_delete = [episode_id for episode_id, episode in self.episodes.items()
                              if episode["season_id"] in seasons_to_delete]

        # Gather all quotes belonging to those episodes
        quotes_to_delete = [quote_id for quote_id, quote in self.quotes.items()
                            if quote.get("episode_id") in episodes_to_delete]

        # Gather all characters belonging to the show
        characters_to_delete = [character_id for character_id, character in self.characters.items()
                                if character["show_id"] == show_id]

        # Delete all quotes
        for quote_id in quotes_to_delete:
            del self.quotes[quote_id]
        # Delete all episodes
        for episode_id in episodes_to_delete:
            del self.episodes[episode_id]
        # Delete all seasons
        for season_id in seasons_to_delete:
            del self.seasons[season_id]
        # Delete all characters
        for character_id in characters_to_delete:
            del self.characters[character_id]
        # Delete the show itself
        del self.shows[show_id]

        return {
            "success": True,
            "message": f"TV show {show_id} and all associated data deleted"
        }

    def add_season(
        self, 
        season_id: str, 
        show_id: str, 
        season_number: int, 
        year: int
    ) -> dict:
        """
        Add a new season to a TV show, ensuring the season_number is unique within the show.

        Args:
            season_id (str): Unique identifier for the new season.
            show_id (str): Identifier for the TV show to which this season belongs.
            season_number (int): Season number (must be unique within the show).
            year (int): Year this season was released.

        Returns:
            dict: 
                Success: {"success": True, "message": "Season added successfully."}
                Failure: {"success": False, "error": <reason>}
    
        Constraints:
            - show_id must exist.
            - season_id must be unique.
            - season_number must be unique within the show.
        """
        # Validate show existence
        if show_id not in self.shows:
            return {"success": False, "error": "Show does not exist."}

        # Check season_id uniqueness
        if season_id in self.seasons:
            return {"success": False, "error": "Season ID already exists."}

        # Enforce season_number uniqueness within the show
        for s in self.seasons.values():
            if s["show_id"] == show_id and s["season_number"] == season_number:
                return {"success": False, "error": "Season number already exists for this show."}

        # Type checks (defensive, if required)
        if not isinstance(season_number, int) or not isinstance(year, int):
            return {"success": False, "error": "season_number and year must be integers."}

        # Add season
        self.seasons[season_id] = {
            "season_id": season_id,
            "show_id": show_id,
            "season_number": season_number,
            "year": year
        }

        return {"success": True, "message": "Season added successfully."}

    def edit_season(
        self, 
        season_id: str, 
        updated_fields: dict
    ) -> dict:
        """
        Update attributes of a season.

        Args:
            season_id (str): ID of the season to update.
            updated_fields (dict): Dictionary with keys as updatable field names
                ('show_id', 'season_number', 'year') and new values.

        Returns:
            dict: {
                "success": True,
                "message": "Season updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - season_id must exist.
            - If changing show_id, the new show must exist.
            - season_number must be unique within its parent show.
            - Each season must be associated with a TV show.
        """
        # Check season exists
        if season_id not in self.seasons:
            return { "success": False, "error": "Season does not exist" }
    
        season = self.seasons[season_id]
        original_show_id = season["show_id"]
        original_season_number = season["season_number"]

        # Compute the new or current parent show ID and season number
        new_show_id = updated_fields.get("show_id", season["show_id"])
        new_season_number = updated_fields.get("season_number", season["season_number"])

        # Validate new show
        if new_show_id != original_show_id or "show_id" in updated_fields:
            if new_show_id not in self.shows:
                return { "success": False, "error": "Target show does not exist" }

        # season_number must be unique within the (possibly new) show, except for this season
        for s_id, s in self.seasons.items():
            if (
                s_id != season_id
                and s["show_id"] == new_show_id
                and s["season_number"] == new_season_number
            ):
                return { "success": False, "error": "season_number already exists in the target show" }
        # Validate season_number (for basic plausibility)
        if "season_number" in updated_fields:
            if not isinstance(new_season_number, int) or new_season_number <= 0:
                return { "success": False, "error": "season_number must be a positive integer" }
        # Validate year (if provided)
        if "year" in updated_fields:
            if not isinstance(updated_fields["year"], int) or updated_fields["year"] < 1800:
                return { "success": False, "error": "Invalid year" }
        # At least one actual change
        updated = False
        for key in ["show_id", "season_number", "year"]:
            if key in updated_fields:
                if season.get(key) != updated_fields[key]:
                    season[key] = updated_fields[key]
                    updated = True
        if not updated:
            return { "success": False, "error": "No changes provided" }

        self.seasons[season_id] = season
        return { "success": True, "message": "Season updated successfully" }

    def delete_season(self, season_id: str) -> dict:
        """
        Remove a season and all its episodes and quotes.

        Args:
            season_id (str): The ID of the season to be deleted.

        Returns:
            dict:
                - success: True if deletion was successful, False otherwise
                - message: Success message (if successful)
                - error: Error reason (if failed)

        Constraints:
            - The season must exist.
            - All episodes associated with the season must be deleted.
            - All quotes associated with those episodes must be deleted (no orphans).
        """
        # Check the season exists
        if season_id not in self.seasons:
            return { "success": False, "error": "Season does not exist" }

        # Find all episodes tied to this season
        episode_ids = [ep_id for ep_id, ep in self.episodes.items()
                       if ep["season_id"] == season_id]

        # Remove all quotes linked to these episodes
        delete_quote_ids = [
            qid for qid, quote in self.quotes.items()
            if quote.get("episode_id") in episode_ids
        ]
        for qid in delete_quote_ids:
            del self.quotes[qid]

        # Delete the episodes
        for ep_id in episode_ids:
            del self.episodes[ep_id]

        # Delete the season
        del self.seasons[season_id]

        return {
            "success": True,
            "message": "Season and all associated episodes and quotes deleted"
        }

    def add_episode(
        self,
        episode_id: str,
        season_id: str,
        episode_number: int,
        title: str,
        air_date: str
    ) -> dict:
        """
        Add a new episode to a season.

        Args:
            episode_id (str): Unique identifier for the new episode.
            season_id (str): The id of the season the episode belongs to.
            episode_number (int): The number of the episode within the season. Must be unique in the season.
            title (str): Title of the episode.
            air_date (str): Air date for the episode.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Episode added: <episode_id>" }
                On failure:
                    { "success": False, "error": <error_reason> }

        Constraints:
            - season_id must exist.
            - episode_id must be unique.
            - episode_number must be unique within the given season.
        """
        # Check if season exists
        if season_id not in self.seasons:
            return {"success": False, "error": f"Season {season_id} does not exist."}

        # Check if episode_id is unique
        if episode_id in self.episodes:
            return {"success": False, "error": f"Episode ID {episode_id} already exists."}

        # Check if episode_number is unique within the season
        for epi in self.episodes.values():
            if epi["season_id"] == season_id and epi["episode_number"] == episode_number:
                return {
                    "success": False,
                    "error": f"Episode number {episode_number} already exists in season {season_id}."
                }

        # Add the episode
        episode_info: EpisodeInfo = {
            "episode_id": episode_id,
            "season_id": season_id,
            "episode_number": episode_number,
            "title": title,
            "air_date": air_date
        }
        self.episodes[episode_id] = episode_info

        return {"success": True, "message": f"Episode added: {episode_id}"}

    def edit_episode(
        self,
        episode_id: str,
        season_id: str = None,
        episode_number: int = None,
        title: str = None,
        air_date: str = None
    ) -> dict:
        """
        Update the attributes (season_id, episode_number, title, air_date) of an existing episode.

        Args:
            episode_id (str): ID of the episode to update (required).
            season_id (str, optional): If set, the new season for this episode. Must exist.
            episode_number (int, optional): If set, the new episode number. Must be unique within the season.
            title (str, optional): If set, the new title of the episode.
            air_date (str, optional): If set, the new air date.

        Returns:
            dict: Success or error message.

        Constraints:
            - The target episode must exist.
            - If season_id is set, it must exist in the database.
            - The (season_id, episode_number) combination must be unique.
            - If neither season_id nor episode_number is set, use current values to check uniqueness.
            - No error if no update fields provided (no-op).
        """
        # Check episode existence
        if episode_id not in self.episodes:
            return {"success": False, "error": "Episode does not exist."}
        episode = self.episodes[episode_id]

        # Determine the target season and episode_number
        target_season_id = season_id if season_id is not None else episode['season_id']
        target_episode_number = episode_number if episode_number is not None else episode['episode_number']

        # Check if target season exists
        if target_season_id not in self.seasons:
            return {"success": False, "error": "Target season does not exist."}

        # Check uniqueness of episode_number in the target season (except itself)
        for eid, ep in self.episodes.items():
            if (
                eid != episode_id and
                ep['season_id'] == target_season_id and
                ep['episode_number'] == target_episode_number
            ):
                return {"success": False, "error": "Episode number already exists in the target season."}

        # Perform updates
        if season_id is not None:
            episode['season_id'] = season_id
        if episode_number is not None:
            episode['episode_number'] = episode_number
        if title is not None:
            episode['title'] = title
        if air_date is not None:
            episode['air_date'] = air_date

        self.episodes[episode_id] = episode

        return {"success": True, "message": "Episode updated successfully."}

    def delete_episode(self, episode_id: str) -> dict:
        """
        Remove an episode and all associated quotes.

        Args:
            episode_id (str): The unique identifier of the episode to delete.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "message": "Episode <episode_id> and all associated quotes deleted successfully."
                    }
                - If the episode does not exist:
                    {
                        "success": False,
                        "error": "Episode does not exist"
                    }

        Constraints:
            - Episode must exist to be deleted.
            - All quotes associated with this episode are also deleted.
        """
        if episode_id not in self.episodes:
            return { "success": False, "error": "Episode does not exist" }
    
        # Delete the episode
        del self.episodes[episode_id]
    
        # Collect all associated quotes to delete
        quotes_to_delete = [qid for qid, q in self.quotes.items() if q.get("episode_id") == episode_id]
        for qid in quotes_to_delete:
            del self.quotes[qid]
    
        return {
            "success": True,
            "message": f"Episode {episode_id} and all associated quotes deleted successfully."
        }

    def add_character(self, character_id: str, name: str, show_id: str) -> dict:
        """
        Add a new character to a specific TV show.

        Args:
            character_id (str): Unique identifier for the character.
            name (str): Name of the character.
            show_id (str): The show ID to associate the character with.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Character added successfully"
                }
            or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - character_id must be unique.
            - show_id must refer to an existing TV show.
        """
        if show_id not in self.shows:
            return { "success": False, "error": "Show ID does not exist" }
        if character_id in self.characters:
            return { "success": False, "error": "Character ID already exists" }

        self.characters[character_id] = {
            "character_id": character_id,
            "name": name,
            "show_id": show_id
        }
        return { "success": True, "message": "Character added successfully" }

    def edit_character(self, character_id: str, name: str = None, show_id: str = None) -> dict:
        """
        Update attributes of a character. 
        At least one of 'name' or 'show_id' must be provided.

        Args:
            character_id (str): The ID of the character to update.
            name (str, optional): New name for the character.
            show_id (str, optional): New show_id to associate the character with.

        Returns:
            dict: {
                "success": True,
                "message": "Character updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
        - character_id must exist.
        - If show_id is provided, it must exist as a TV show.
        - At least one of name or show_id must be provided (otherwise, return error).
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character ID does not exist."}

        if name is None and show_id is None:
            return {"success": False, "error": "No update fields provided. Must specify at least 'name' or 'show_id'."}

        if show_id is not None and show_id not in self.shows:
            return {"success": False, "error": "Provided show_id does not exist."}

        if name is not None:
            self.characters[character_id]["name"] = name
        if show_id is not None:
            self.characters[character_id]["show_id"] = show_id

        return {"success": True, "message": "Character updated successfully."}

    def delete_character(self, character_id: str) -> dict:
        """
        Remove a character from the database.

        Args:
            character_id (str): The ID of the character to delete.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success message including character name
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure
            }

        Constraints:
            - Character must exist.
            - Character cannot be deleted if any quotes reference it, to avoid orphaned quotes.
        """
        # Check if character exists
        character = self.characters.get(character_id)
        if not character:
            return { "success": False, "error": "Character does not exist" }

        # Check if any quotes reference this character
        for quote in self.quotes.values():
            if quote.get("character_id") == character_id:
                return {
                    "success": False,
                    "error": "Cannot delete character: one or more quotes are associated with this character"
                }

        # Delete character
        del self.characters[character_id]
        return {
            "success": True,
            "message": f"Character '{character['name']}' deleted"
        }

    def add_quote(
        self, 
        quote_id: str, 
        episode_id: str, 
        character_id: str, 
        text: str, 
        timestamp: Optional[float] = None
    ) -> dict:
        """
        Add a new quote to the database, linked to an episode and character.

        Args:
            quote_id (str): Unique identifier for the quote.
            episode_id (str): The ID of the episode to associate this quote with.
            character_id (str): The ID of the character who said the quote.
            text (str): The content of the quote.
            timestamp (Optional[float]): (Optional) Timestamp within episode.

        Returns:
            dict: {
                "success": True,
                "message": "Quote added successfully"
            } on success;
            {
                "success": False,
                "error": <reason>
            } on failure.

        Constraints:
            - quote_id must not already exist
            - episode_id must exist
            - character_id must exist
            - Each quote must be associated with an episode and a character
        """
        if quote_id in self.quotes:
            return { "success": False, "error": "Quote ID already exists" }
        if episode_id not in self.episodes:
            return { "success": False, "error": "Episode ID does not exist" }
        if character_id not in self.characters:
            return { "success": False, "error": "Character ID does not exist" }
        if not text or not text.strip():
            return { "success": False, "error": "Quote text must not be empty" }

        quote_info: QuoteInfo = {
            "quote_id": quote_id,
            "episode_id": episode_id,
            "character_id": character_id,
            "text": text.strip()
        }
        if timestamp is not None:
            quote_info["timestamp"] = timestamp

        self.quotes[quote_id] = quote_info
        return { "success": True, "message": "Quote added successfully" }

    def edit_quote(self, quote_id: str, text: Optional[str] = None, timestamp: Optional[float] = None) -> dict:
        """
        Update the text and/or timestamp of a quote.

        Args:
            quote_id (str): The ID of the quote to edit.
            text (Optional[str]): The new text of the quote (if updating).
            timestamp (Optional[float]): The new timestamp of the quote (if updating/nullifying).

        Returns:
            dict:
                - On success: { "success": True, "message": "Quote updated successfully" }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The quote_id must exist in the quotes database.
            - At least one of text or timestamp must be provided.
            - If provided, text must be a non-empty string.
            - If provided, timestamp must be a float or None.
        """
        if quote_id not in self.quotes:
            return {"success": False, "error": "Quote not found"}

        if text is None and timestamp is None:
            return {"success": False, "error": "No update parameters provided"}

        # Validate text
        if text is not None:
            if not isinstance(text, str) or not text.strip():
                return {"success": False, "error": "Invalid text value"}
            self.quotes[quote_id]["text"] = text

        # Validate timestamp
        if timestamp is not None:
            if not (isinstance(timestamp, float) or timestamp is None):
                return {"success": False, "error": "Invalid timestamp value"}
            self.quotes[quote_id]["timestamp"] = timestamp

        return {"success": True, "message": "Quote updated successfully"}

    def delete_quote(self, quote_id: str) -> dict:
        """
        Remove a quote from the database.

        Args:
            quote_id (str): The identifier of the quote to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "Quote deleted successfully." }
                On failure: { "success": False, "error": "Quote does not exist." }

        Constraints:
            - The quote_id must exist in the database.
        """
        if quote_id not in self.quotes:
            return { "success": False, "error": "Quote does not exist." }

        del self.quotes[quote_id]
        return { "success": True, "message": "Quote deleted successfully." }


class TVShowQuotesDatabase(BaseEnv):
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

    def list_shows(self, **kwargs):
        return self._call_inner_tool('list_shows', kwargs)

    def get_season_by_number(self, **kwargs):
        return self._call_inner_tool('get_season_by_number', kwargs)

    def list_seasons_for_show(self, **kwargs):
        return self._call_inner_tool('list_seasons_for_show', kwargs)

    def get_episodes_by_season(self, **kwargs):
        return self._call_inner_tool('get_episodes_by_season', kwargs)

    def get_episode_by_number(self, **kwargs):
        return self._call_inner_tool('get_episode_by_number', kwargs)

    def get_quotes_by_episode(self, **kwargs):
        return self._call_inner_tool('get_quotes_by_episode', kwargs)

    def get_quotes_by_season(self, **kwargs):
        return self._call_inner_tool('get_quotes_by_season', kwargs)

    def get_quotes_by_show(self, **kwargs):
        return self._call_inner_tool('get_quotes_by_show', kwargs)

    def get_quotes_by_character(self, **kwargs):
        return self._call_inner_tool('get_quotes_by_character', kwargs)

    def get_character_by_name(self, **kwargs):
        return self._call_inner_tool('get_character_by_name', kwargs)

    def list_characters_for_show(self, **kwargs):
        return self._call_inner_tool('list_characters_for_show', kwargs)

    def get_quote_by_id(self, **kwargs):
        return self._call_inner_tool('get_quote_by_id', kwargs)

    def add_tv_show(self, **kwargs):
        return self._call_inner_tool('add_tv_show', kwargs)

    def edit_tv_show(self, **kwargs):
        return self._call_inner_tool('edit_tv_show', kwargs)

    def delete_tv_show(self, **kwargs):
        return self._call_inner_tool('delete_tv_show', kwargs)

    def add_season(self, **kwargs):
        return self._call_inner_tool('add_season', kwargs)

    def edit_season(self, **kwargs):
        return self._call_inner_tool('edit_season', kwargs)

    def delete_season(self, **kwargs):
        return self._call_inner_tool('delete_season', kwargs)

    def add_episode(self, **kwargs):
        return self._call_inner_tool('add_episode', kwargs)

    def edit_episode(self, **kwargs):
        return self._call_inner_tool('edit_episode', kwargs)

    def delete_episode(self, **kwargs):
        return self._call_inner_tool('delete_episode', kwargs)

    def add_character(self, **kwargs):
        return self._call_inner_tool('add_character', kwargs)

    def edit_character(self, **kwargs):
        return self._call_inner_tool('edit_character', kwargs)

    def delete_character(self, **kwargs):
        return self._call_inner_tool('delete_character', kwargs)

    def add_quote(self, **kwargs):
        return self._call_inner_tool('add_quote', kwargs)

    def edit_quote(self, **kwargs):
        return self._call_inner_tool('edit_quote', kwargs)

    def delete_quote(self, **kwargs):
        return self._call_inner_tool('delete_quote', kwargs)

