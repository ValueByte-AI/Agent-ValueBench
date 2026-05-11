# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import List, Dict
from datetime import datetime



class GameInfo(TypedDict):
    game_id: str
    title: str
    description: str
    release_date: str
    developer: str
    publisher: str
    tags: List[str]          # List of tag_ids
    platform: List[str]      # List of platform_ids

class TagInfo(TypedDict):
    tag_id: str
    tag_name: str

class PlatformInfo(TypedDict):
    platform_id: str
    platform_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Digital game catalog management environment.
        """

        # Games: {game_id: GameInfo}
        self.games: Dict[str, GameInfo] = {}

        # Tags: {tag_id: TagInfo}
        self.tags: Dict[str, TagInfo] = {}

        # Platforms: {platform_id: PlatformInfo}
        self.platforms: Dict[str, PlatformInfo] = {}

        # === Constraints from environment rules (enforced in methods later): ===
        # - Each game must have at least one title and one supported platform.
        # - tags and platforms for a game can be multiple and must come from the set of defined tags and platforms.
        # - Searches/filtering must only return games that match all queried tags and at least one specified platform.

    def list_all_games(self) -> dict:
        """
        Retrieve all games in the catalog.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # List of all game entries (could be empty if no games exist)
            }
        """
        return {
            "success": True,
            "data": list(self.games.values())
        }

    def get_game_by_id(self, game_id: str) -> dict:
        """
        Retrieve full metadata for a specific game given its game_id.
    
        Args:
            game_id (str): The unique identifier for the game.
    
        Returns:
            dict:
                - On success: { "success": True, "data": GameInfo }
                - On failure: { "success": False, "error": "Game not found" }
        """
        game_info = self.games.get(game_id)
        if game_info is None:
            return { "success": False, "error": "Game not found" }
        return { "success": True, "data": game_info }

    def search_games_by_title(self, search_string: str) -> dict:
        """
        Find all games whose titles match or contain a given search string (case-insensitive).

        Args:
            search_string (str): The search phrase to look for in game titles.
                - If empty, returns all games.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo]  # All matching games (possibly empty if no matches)
            }
        """
        if not isinstance(search_string, str):
            # Malformed input, treat as empty string (return everything)
            search_string = ""
        search_lower = search_string.lower()
        result = [
            game_info for game_info in self.games.values()
            if search_lower in game_info["title"].lower()
        ]
        return {"success": True, "data": result}

    def filter_games_by_tags(self, tag_ids: List[str]) -> dict:
        """
        Find all games containing all of the specified tags (AND logic).

        Args:
            tag_ids (List[str]): List of tag_ids to require for matched games.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],   # All games whose tag set includes all specified tag_ids
            }
            OR
            {
                "success": False,
                "error": str,             # If any tag_id is invalid/missing from catalog
            }

        Constraints:
            - All tag_ids must exist in the catalog (in self.tags).
            - Every returned game will contain *all* of tag_ids in its tags.
        """
        # Verify all tag_ids exist
        unknown_tags = [tid for tid in tag_ids if tid not in self.tags]
        if unknown_tags:
            return {
                "success": False,
                "error": f"Unknown tag_id(s): {', '.join(unknown_tags)}"
            }

        if not tag_ids:
            # No tags specified: return all games (vacuous truth)
            return {
                "success": True,
                "data": list(self.games.values())
            }

        # AND filter: a game matches if all tag_ids are in its tags field
        result = [
            game_info for game_info in self.games.values()
            if all(tag in game_info["tags"] for tag in tag_ids)
        ]

        return {
            "success": True,
            "data": result
        }

    def filter_games_by_platforms(self, platform_ids: List[str]) -> dict:
        """
        Find all games available on any of the specified platforms (OR logic).

        Args:
            platform_ids (List[str]): List of platform IDs to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # All games with at least one matching platform_id (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # On input error (unlikely)
            }

        Constraints:
            - Games must have at least one supported platform (enforced elsewhere).
            - Query logic: game matches if any platform_id from input is in its platform list.
        """
        if not isinstance(platform_ids, list):
            return {"success": False, "error": "platform_ids must be a list"}
    
        # Optional: if platform_ids is empty, we could return all games or none; here, let's return none.
        if not platform_ids:
            return {"success": True, "data": []}

        platform_id_set = set(platform_ids)
        result = [
            game_info for game_info in self.games.values()
            if set(game_info["platform"]) & platform_id_set
        ]
        return {"success": True, "data": result}

    def filter_games_by_tags_and_platforms(self, tags: list, platforms: list) -> dict:
        """
        Return all games that match all specified tags and are available on at least one specified platform.

        Args:
            tags (list of str): List of tag IDs. If empty, no tag filtering.
            platforms (list of str): List of platform IDs. If empty, no platform filtering.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[GameInfo],  # Games matching all tags and at least one platform
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (invalid tag_id/platform_id/etc)
                    }

        Constraints:
            - Every specified tag_id must exist in self.tags.
            - Every specified platform_id must exist in self.platforms.
            - Games must contain all specified tag_ids and at least one specified platform_id.
        """
        # Validate tag IDs
        for tag_id in tags:
            if tag_id not in self.tags:
                return {"success": False, "error": f"Tag ID '{tag_id}' does not exist."}
        # Validate platform IDs
        for platform_id in platforms:
            if platform_id not in self.platforms:
                return {"success": False, "error": f"Platform ID '{platform_id}' does not exist."}

        matching_games = []
        for game in self.games.values():
            # Check tags
            if tags:
                if not all(tag_id in game["tags"] for tag_id in tags):
                    continue  # Must have all queried tags
            # Check platforms
            if platforms:
                if not any(platform_id in game["platform"] for platform_id in platforms):
                    continue  # Must have at least one platform match
            matching_games.append(game)
        return {"success": True, "data": matching_games}

    def list_all_tags(self) -> dict:
        """
        Retrieve all defined tags in the catalog.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo]  # List of tag objects (tag_id and tag_name), possibly empty
            }
        """
        tags_list = list(self.tags.values())
        return {
            "success": True,
            "data": tags_list
        }

    def get_tag_by_id(self, tag_id: str) -> dict:
        """
        Retrieve the name and details for the specified tag_id.

        Args:
            tag_id (str): The unique identifier for the tag.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": TagInfo  # tag_id and tag_name
                }
                or
                {
                    "success": False,
                    "error": str  # error message if tag_id not found
                }
        Constraints:
            - tag_id must match an existing tag in the catalog.
        """
        tag = self.tags.get(tag_id)
        if tag is None:
            return { "success": False, "error": "Tag not found" }
        return { "success": True, "data": tag }

    def get_tag_id_by_name(self, tag_name: str) -> dict:
        """
        Find the tag_id corresponding to a tag name.

        Args:
            tag_name (str): The name of the tag to search for.

        Returns:
            dict:
                - On success: {"success": True, "data": tag_id}
                - On failure: {"success": False, "error": "Tag name not found"}

        Constraints:
            - Tag names are case-sensitive.
            - Only tags in the catalog are considered.
        """
        for tag_id, tag_info in self.tags.items():
            if tag_info["tag_name"] == tag_name:
                return {"success": True, "data": tag_id}
        return {"success": False, "error": "Tag name not found"}

    def list_all_platforms(self) -> dict:
        """
        Retrieve all video game platforms in the catalog.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PlatformInfo]  # Each has at least platform_id and platform_name
                }
        Notes:
            - Returns an empty list if no platforms are registered.
            - No input parameters or constraints apply.
        """
        platforms_list = list(self.platforms.values())
        return { "success": True, "data": platforms_list }

    def get_platform_by_id(self, platform_id: str) -> dict:
        """
        Retrieve the detailed info for the specified platform_id.

        Args:
            platform_id (str): The unique identifier of the platform.

        Returns:
            dict: {
                "success": True,
                "data": PlatformInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - platform_id must exist in the catalog.
        """
        platform = self.platforms.get(platform_id)
        if not platform:
            return {"success": False, "error": "Platform not found"}
        return {"success": True, "data": platform}

    def get_platform_id_by_name(self, platform_name: str) -> dict:
        """
        Retrieve the platform_id for a given platform name.

        Args:
            platform_name (str): The name of the platform to search for (exact match).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": str  # platform_id
                }
                OR
                {
                    "success": False,
                    "error": "Platform not found"
                }

        Constraints:
            - Only platforms already defined in the catalog will be considered.
            - Name match is case-sensitive.
        """
        for platform_id, platform_info in self.platforms.items():
            if platform_info["platform_name"] == platform_name:
                return { "success": True, "data": platform_id }
        return { "success": False, "error": "Platform not found" }

    def list_games_by_developer(self, developer: str) -> dict:
        """
        Return all games developed by a specified developer.

        Args:
            developer (str): The developer name to filter games by (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],    # All matching games (could be empty if none found)
            }
            OR
            {
                "success": False,
                "error": str               # Description of the error
            }

        Constraints:
            - If developer is not given or is empty, return an error.
            - Matching is case-insensitive.
        """
        if not developer or not isinstance(developer, str):
            return { "success": False, "error": "Developer name must be a non-empty string" }

        dev_normalized = developer.strip().lower()
        results = [
            game for game in self.games.values()
            if game.get("developer", "").strip().lower() == dev_normalized
        ]

        return { "success": True, "data": results }

    def list_games_by_publisher(self, publisher: str) -> dict:
        """
        Return all games published by the specified publisher.

        Args:
            publisher (str): The publisher name to filter games by.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # List of games' info (may be empty if no games found)
            }

        Constraints:
            - This operation does not fail if there are no matches; returns empty list instead.
            - Matching is case-sensitive on the 'publisher' string attribute.
        """
        result = [
            game_info for game_info in self.games.values()
            if game_info["publisher"] == publisher
        ]
        return { "success": True, "data": result }


    def list_games_by_release_date_range(self, start_date: str, end_date: str) -> dict:
        """
        List all games (GameInfo) released within the given date range [start_date, end_date], inclusive.

        Args:
            start_date (str): Start of the release date range (format: 'YYYY-MM-DD')
            end_date (str): End of the release date range (format: 'YYYY-MM-DD')

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Dates are compared in 'YYYY-MM-DD' string format (lexicographically).
            - Returns empty list if no games match the criteria.
            - Returns error if date format is invalid.
        """
        def is_valid_date(date_str: str) -> bool:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return True
            except Exception:
                return False

        if not (is_valid_date(start_date) and is_valid_date(end_date)):
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

        # Ensure start_date <= end_date; if not, return empty list (user's intent ambiguous)
        if start_date > end_date:
            return {"success": True, "data": []}

        result: List[GameInfo] = [
            game for game in self.games.values()
            if "release_date" in game and start_date <= game["release_date"] <= end_date
        ]

        return {"success": True, "data": result}

    def add_game(self,
                 game_id: str,
                 title: str,
                 description: str,
                 release_date: str,
                 developer: str,
                 publisher: str,
                 tags: list,
                 platform: list) -> dict:
        """
        Add a new game to the catalog with validated metadata.

        Args:
            game_id (str): Unique identifier for the game.
            title (str): Title of the game (must not be empty).
            description (str): Game description.
            release_date (str): Release date (format not enforced here).
            developer (str): Developer name.
            publisher (str): Publisher name.
            tags (list of str): List of tag_ids (must exist in catalog).
            platform (list of str): List of platform_ids (must exist in catalog, at least one required).

        Returns:
            dict: {
                "success": True,
                "message": "Game <game_id> added."
            }
            OR
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The game_id must be unique (not already in catalog).
            - Title must be provided (non-empty).
            - At least one platform must be provided.
            - All tag IDs and platform IDs must exist in catalog definitions.
        """
        # Validate game_id
        if not game_id or not isinstance(game_id, str):
            return {"success": False, "error": "Missing or invalid game_id."}
        if game_id in self.games:
            return {"success": False, "error": f"Game with id '{game_id}' already exists."}

        # Validate title
        if not title or not isinstance(title, str) or not title.strip():
            return {"success": False, "error": "Game title must be provided and non-empty."}

        # Validate platforms
        if not platform or not isinstance(platform, list) or len(platform) == 0:
            return {"success": False, "error": "At least one supported platform must be provided."}
        # Check platform existence
        invalid_platforms = [pid for pid in platform if pid not in self.platforms]
        if invalid_platforms:
            return {"success": False, "error": f"Invalid platform_id(s): {', '.join(invalid_platforms)}."}

        # Validate tags
        if not isinstance(tags, list):
            return {"success": False, "error": "Tags must be provided as a list."}
        invalid_tags = [tid for tid in tags if tid not in self.tags]
        if invalid_tags:
            return {"success": False, "error": f"Invalid tag_id(s): {', '.join(invalid_tags)}."}

        # All validations passed, construct and add the game
        self.games[game_id] = {
            "game_id": game_id,
            "title": title,
            "description": description,
            "release_date": release_date,
            "developer": developer,
            "publisher": publisher,
            "tags": tags,
            "platform": platform,
        }

        return {"success": True, "message": f"Game '{game_id}' added."}

    def update_game_metadata(
        self,
        game_id: str,
        title: str = None,
        description: str = None,
        release_date: str = None,
        developer: str = None,
        publisher: str = None,
        tags: list = None,
        platform: list = None
    ) -> dict:
        """
        Edit (update) metadata fields for an existing game entry.

        Args:
            game_id (str): The unique identifier of the game to update.
            title (str, optional): New title for the game.
            description (str, optional): New description.
            release_date (str, optional): New release date (format not enforced here).
            developer (str, optional): New developer.
            publisher (str, optional): New publisher.
            tags (list of str, optional): List of tag_ids to assign to the game.
            platform (list of str, optional): List of platform_ids the game supports.

        Returns:
            dict: {
                "success": True,
                "message": "Game metadata updated successfully"
            } on success,
            or {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - The specified game must exist.
            - At least one metadata field must be provided to update.
            - If tags/platform are provided, all IDs must be in the catalog.
            - After update, game must have at least one title and one supported platform.
        """
        # Check if game exists
        if game_id not in self.games:
            return { "success": False, "error": "Game not found" }

        # Ensure at least one updatable field was provided
        if all(
            v is None
            for v in [title, description, release_date, developer, publisher, tags, platform]
        ):
            return { "success": False, "error": "No fields specified for update" }

        game = self.games[game_id].copy()  # Work with a copy to avoid accidental partial update

        # Update fields if provided
        if title is not None:
            game["title"] = title
        if description is not None:
            game["description"] = description
        if release_date is not None:
            game["release_date"] = release_date
        if developer is not None:
            game["developer"] = developer
        if publisher is not None:
            game["publisher"] = publisher

        # If tags are provided, validate them
        if tags is not None:
            if not isinstance(tags, list):
                return { "success": False, "error": "Tags must be a list of tag_ids" }
            invalid_tags = [tag_id for tag_id in tags if tag_id not in self.tags]
            if invalid_tags:
                return { "success": False, "error": f"Invalid tag IDs: {invalid_tags}" }
            game["tags"] = tags

        # If platforms are provided, validate them
        if platform is not None:
            if not isinstance(platform, list):
                return { "success": False, "error": "Platform must be a list of platform_ids" }
            invalid_platforms = [pid for pid in platform if pid not in self.platforms]
            if invalid_platforms:
                return { "success": False, "error": f"Invalid platform IDs: {invalid_platforms}" }
            game["platform"] = platform

        # Constraint: Must have at least one title and one supported platform
        if not game.get("title") or not isinstance(game.get("title"), str) or not game.get("title").strip():
            return { "success": False, "error": "Game must have a non-empty title" }
        if not game.get("platform") or not isinstance(game.get("platform"), list) or len(game["platform"]) == 0:
            return { "success": False, "error": "Game must have at least one supported platform" }

        # All checks passed, write back
        self.games[game_id] = game

        return { "success": True, "message": "Game metadata updated successfully" }

    def remove_game(self, game_id: str) -> dict:
        """
        Remove a game from the catalog by its unique game_id.

        Args:
            game_id (str): The unique identifier of the game to remove.

        Returns:
            dict:
            - On success: { "success": True, "message": "Game <game_id> removed from catalog." }
            - On failure: { "success": False, "error": "Game with id <game_id> does not exist." }

        Constraints:
            - Only removes the game entry; does not affect tags or platforms.
            - If the game does not exist, operation fails gracefully.
        """
        if game_id not in self.games:
            return { "success": False, "error": f"Game with id {game_id} does not exist." }

        del self.games[game_id]
        return { "success": True, "message": f"Game {game_id} removed from catalog." }

    def add_tag(self, tag_id: str, tag_name: str) -> dict:
        """
        Add a new tag definition to the tag catalog.

        Args:
            tag_id (str): Unique identifier for the tag.
            tag_name (str): Display name of the tag.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Tag added successfully." }
                - On failure: { "success": False, "error": error_message }

        Constraints:
            - tag_id must be unique (not already present in self.tags).
            - tag_name may be repeated (not constrained).
        """
        if not tag_id or not isinstance(tag_id, str):
            return { "success": False, "error": "Tag ID must be a non-empty string." }
        if tag_id in self.tags:
            return { "success": False, "error": "Tag ID already exists." }
        if not tag_name or not isinstance(tag_name, str):
            return { "success": False, "error": "Tag name must be a non-empty string." }

        self.tags[tag_id] = {
            "tag_id": tag_id,
            "tag_name": tag_name
        }

        return { "success": True, "message": "Tag added successfully." }

    def update_tag(self, tag_id: str, tag_name: str = None) -> dict:
        """
        Edit the properties (currently only name) of an existing tag.

        Args:
            tag_id (str): The unique identifier of the tag to update.
            tag_name (str, optional): The new name for the tag. Must not be empty or already in use by another tag.

        Returns:
            dict:
                On success: { "success": True, "message": "Tag updated successfully" }
                On failure: { "success": False, "error": <reason> }
        Constraints:
            - tag_id must exist in the tag catalog.
            - tag_name (if provided) must not be empty and must not duplicate another tag's name.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag ID does not exist" }

        tag_info = self.tags[tag_id]
    
        if tag_name is not None:
            normalized_new_name = tag_name.strip()
            if not normalized_new_name:
                return { "success": False, "error": "Tag name must not be empty" }
            # Check if new name is used by another tag
            for tid, tinfo in self.tags.items():
                if tid != tag_id and tinfo["tag_name"].lower() == normalized_new_name.lower():
                    return { "success": False, "error": "Tag name already exists" }
            tag_info["tag_name"] = normalized_new_name

        self.tags[tag_id] = tag_info
        return { "success": True, "message": "Tag updated successfully" }

    def remove_tag(self, tag_id: str) -> dict:
        """
        Delete a tag from the catalog and remove all its references from each game's 'tags' field.

        Args:
            tag_id (str): The identifier of the tag to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Tag removed from catalog and all games" }
                On error:
                    { "success": False, "error": "Tag not found" }

        Constraints:
            - Tag must exist in the catalog.
            - Must remove the tag from every game's 'tags' list if present.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag not found" }

        # Remove the tag from the catalog
        del self.tags[tag_id]

        # Remove the tag_id from all games' tag lists
        for game in self.games.values():
            if tag_id in game['tags']:
                game['tags'] = [tid for tid in game['tags'] if tid != tag_id]

        return { "success": True, "message": "Tag removed from catalog and all games" }

    def add_platform(self, platform_id: str, platform_name: str) -> dict:
        """
        Add a new platform definition to the platform catalog.

        Args:
            platform_id (str): Unique identifier for the new platform.
            platform_name (str): Human-readable name for the platform.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Platform added successfully"
                }
                On failure:
                {
                    "success": False,
                    "error": <Reason - e.g., duplicate platform ID>
                }

        Constraints:
            - The platform_id must not already exist in the system.
            - (Optional) platform_name uniqueness is not enforced.
            - platform_id and platform_name must not be empty.
        """
        if not platform_id or not platform_name:
            return { "success": False, "error": "platform_id and platform_name must be non-empty" }

        if platform_id in self.platforms:
            return { "success": False, "error": "Platform ID already exists" }

        # (Optional) Platform name uniqueness check, not enforced by constraints, but could be warned about.
        # for p in self.platforms.values():
        #     if p["platform_name"].lower() == platform_name.lower():
        #         return { "success": False, "error": "Platform name already exists" }

        self.platforms[platform_id] = {
            "platform_id": platform_id,
            "platform_name": platform_name
        }
        return { "success": True, "message": "Platform added successfully" }

    def update_platform(self, platform_id: str, platform_name: str = None) -> dict:
        """
        Edit the properties (e.g., name) of an existing platform.

        Args:
            platform_id (str): The unique identifier for the platform to update.
            platform_name (str, optional): The new display name for the platform.

        Returns:
            dict:
                - On success: { "success": True, "message": "Platform updated successfully." }
                - On failure: { "success": False, "error": <error message> }

        Constraints:
            - The platform with the given platform_id must exist in the catalog.
            - At least one property must be provided to update.
            - Only edits platform_name (as that's the only modifiable attribute).
        """
        if platform_id not in self.platforms:
            return { "success": False, "error": "Platform does not exist." }
        if platform_name is None:
            return { "success": False, "error": "No property provided to update." }
    
        self.platforms[platform_id]['platform_name'] = platform_name
        return { "success": True, "message": "Platform updated successfully." }

    def remove_platform(self, platform_id: str) -> dict:
        """
        Delete a platform from the catalog and remove its references from all games.
        If removing the platform would leave any game with zero platforms, the operation fails,
        and no changes are made.

        Args:
            platform_id (str): The unique identifier for the platform to remove.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Platform <platform_id> removed and references deleted from games"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g. "Platform not found", "Cannot remove: would leave some games without any supported platform"
                    }

        Constraints:
            - Cannot remove a platform if doing so would leave any game with zero platforms.
            - All references in games must be removed as part of the operation.
        """
        # Check platform existence
        if platform_id not in self.platforms:
            return {"success": False, "error": "Platform not found"}

        # Identify games referencing this platform
        games_with_platform = [
            game_id for game_id, game_info in self.games.items()
            if platform_id in game_info.get("platform", [])
        ]

        # Check for games that would have zero platforms after removal
        games_would_be_empty = [
            game_id for game_id in games_with_platform
            if len(self.games[game_id]["platform"]) == 1
        ]
        if games_would_be_empty:
            return {
                "success": False,
                "error": (
                    "Cannot remove platform: removing it would leave the following games with no supported platform: "
                    + ", ".join(games_would_be_empty)
                )
            }

        # Remove platform from all games where present
        for game_id in games_with_platform:
            curr_platforms = self.games[game_id]["platform"]
            self.games[game_id]["platform"] = [pid for pid in curr_platforms if pid != platform_id]

        # Remove platform from platform catalog
        del self.platforms[platform_id]

        return {
            "success": True,
            "message": f"Platform {platform_id} removed and references deleted from games"
        }

    def assign_tags_to_game(self, game_id: str, tag_ids: list) -> dict:
        """
        Add one or more tags (by ID) to a game's metadata.

        Args:
            game_id (str): Unique identifier of the game.
            tag_ids (List[str]): List of tag IDs to assign.

        Returns:
            dict: {
                "success": True, "message": "Tags assigned to game <game_id>."
            }
            or
            {
                "success": False, "error": str
            }

        Constraints:
            - The specified game must exist in the catalog.
            - All tags must be present in the tag catalog (`self.tags`).
            - The resulting tag list for the game is deduplicated.
            - Tag addition is idempotent (no error on existing assignments).
        """
        # Validate game existence
        if game_id not in self.games:
            return {"success": False, "error": f"Game ID '{game_id}' does not exist."}

        # Handle empty tag list early (idempotent operation, ignore)
        if not tag_ids:
            return {"success": True, "message": f"No tags to assign for game {game_id}."}

        # Validate all tag_ids
        invalid_tags = [tag_id for tag_id in tag_ids if tag_id not in self.tags]
        if invalid_tags:
            return {
                "success": False,
                "error": f"The following tag IDs do not exist: {', '.join(invalid_tags)}"
            }

        # Add tags (deduplicated)
        existing_tags = set(self.games[game_id].get("tags", []))
        new_tags = set(tag_ids)
        updated_tags = list(existing_tags | new_tags)
        self.games[game_id]["tags"] = updated_tags

        return {
            "success": True,
            "message": f"Tags assigned to game {game_id}."
        }

    def assign_platforms_to_game(self, game_id: str, platform_ids: list[str]) -> dict:
        """
        Add one or more platforms to the supported platforms of a specified game.
        Validation:
          - The game must exist in the catalog.
          - Each platform_id must exist in the platform catalog.
          - Platforms are only added if not already in the game's supported list.
          - The game will always have at least one platform after this operation.

        Args:
            game_id (str): The ID of the game to update.
            platform_ids (List[str]): List of platform IDs to add.

        Returns:
            dict: {
              "success": True,
              "message": "Platforms assigned to game <game_id>"
            }
            or
            {
              "success": False,
              "error": <reason>
            }
        """
        if game_id not in self.games:
            return {"success": False, "error": f"Game with ID '{game_id}' does not exist"}

        if not isinstance(platform_ids, list):
            return {"success": False, "error": "platform_ids must be a list of platform IDs"}

        # Validate platform IDs
        invalid_pids = [pid for pid in platform_ids if pid not in self.platforms]
        if invalid_pids:
            return {
                "success": False,
                "error": f"The following platform IDs do not exist: {', '.join(invalid_pids)}"
            }

        game = self.games[game_id]
        original_platforms = set(game["platform"])

        # Add new platforms
        updated_platforms = original_platforms.union(platform_ids)
        game["platform"] = list(updated_platforms)

        return {
            "success": True,
            "message": f"Platforms assigned to game {game_id}"
        }

    def remove_tag_from_game(self, game_id: str, tag_id: str) -> dict:
        """
        Remove a tag (tag_id) from a particular game (game_id).

        Args:
            game_id (str): The unique ID of the game.
            tag_id (str): The unique ID of the tag to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Tag <tag_id> removed from game <game_id>."
            }
            or
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Game must exist.
            - Tag must exist in the catalog.
            - Tag must be currently assigned to the game.
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game does not exist." }
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist." }
        if tag_id not in self.games[game_id]["tags"]:
            return { "success": False, "error": "Tag is not assigned to this game." }
        self.games[game_id]["tags"].remove(tag_id)
        return {
            "success": True,
            "message": f"Tag {tag_id} removed from game {game_id}."
        }

    def remove_platform_from_game(self, game_id: str, platform_id: str) -> dict:
        """
        Removes a platform from a particular game, ensuring the game still has at least one platform.

        Args:
            game_id (str): The identifier of the game to update.
            platform_id (str): The identifier of the platform to remove.

        Returns:
            dict: 
                On success: { "success": True, "message": "Platform <platform_id> removed from game <game_id>." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Game must exist.
            - Platform must exist in platform catalog.
            - Platform must be associated with the game.
            - Game must have at least one platform after the operation; otherwise, the operation is not allowed.
        """
        # Check if the game exists
        if game_id not in self.games:
            return { "success": False, "error": f"Game with id '{game_id}' does not exist." }
    
        # Check if the platform exists
        if platform_id not in self.platforms:
            return { "success": False, "error": f"Platform with id '{platform_id}' does not exist." }
    
        game = self.games[game_id]
        current_platforms = game["platform"]

        # Check if platform is actually assigned to the game
        if platform_id not in current_platforms:
            return { "success": False, "error": f"Platform '{platform_id}' is not assigned to game '{game_id}'." }
    
        # Constraint: There must be at least one platform after removal
        if len(current_platforms) == 1:
            return { "success": False, "error": "Cannot remove the last platform from the game. Each game must have at least one supported platform." }

        # Perform removal
        game["platform"] = [pid for pid in current_platforms if pid != platform_id]
        # No need to update catalog if working on the dict reference

        return { "success": True, "message": f"Platform '{platform_id}' removed from game '{game_id}'." }


class DigitalGameCatalogManagementSystem(BaseEnv):
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

    def list_all_games(self, **kwargs):
        return self._call_inner_tool('list_all_games', kwargs)

    def get_game_by_id(self, **kwargs):
        return self._call_inner_tool('get_game_by_id', kwargs)

    def search_games_by_title(self, **kwargs):
        return self._call_inner_tool('search_games_by_title', kwargs)

    def filter_games_by_tags(self, **kwargs):
        return self._call_inner_tool('filter_games_by_tags', kwargs)

    def filter_games_by_platforms(self, **kwargs):
        return self._call_inner_tool('filter_games_by_platforms', kwargs)

    def filter_games_by_tags_and_platforms(self, **kwargs):
        return self._call_inner_tool('filter_games_by_tags_and_platforms', kwargs)

    def list_all_tags(self, **kwargs):
        return self._call_inner_tool('list_all_tags', kwargs)

    def get_tag_by_id(self, **kwargs):
        return self._call_inner_tool('get_tag_by_id', kwargs)

    def get_tag_id_by_name(self, **kwargs):
        return self._call_inner_tool('get_tag_id_by_name', kwargs)

    def list_all_platforms(self, **kwargs):
        return self._call_inner_tool('list_all_platforms', kwargs)

    def get_platform_by_id(self, **kwargs):
        return self._call_inner_tool('get_platform_by_id', kwargs)

    def get_platform_id_by_name(self, **kwargs):
        return self._call_inner_tool('get_platform_id_by_name', kwargs)

    def list_games_by_developer(self, **kwargs):
        return self._call_inner_tool('list_games_by_developer', kwargs)

    def list_games_by_publisher(self, **kwargs):
        return self._call_inner_tool('list_games_by_publisher', kwargs)

    def list_games_by_release_date_range(self, **kwargs):
        return self._call_inner_tool('list_games_by_release_date_range', kwargs)

    def add_game(self, **kwargs):
        return self._call_inner_tool('add_game', kwargs)

    def update_game_metadata(self, **kwargs):
        return self._call_inner_tool('update_game_metadata', kwargs)

    def remove_game(self, **kwargs):
        return self._call_inner_tool('remove_game', kwargs)

    def add_tag(self, **kwargs):
        return self._call_inner_tool('add_tag', kwargs)

    def update_tag(self, **kwargs):
        return self._call_inner_tool('update_tag', kwargs)

    def remove_tag(self, **kwargs):
        return self._call_inner_tool('remove_tag', kwargs)

    def add_platform(self, **kwargs):
        return self._call_inner_tool('add_platform', kwargs)

    def update_platform(self, **kwargs):
        return self._call_inner_tool('update_platform', kwargs)

    def remove_platform(self, **kwargs):
        return self._call_inner_tool('remove_platform', kwargs)

    def assign_tags_to_game(self, **kwargs):
        return self._call_inner_tool('assign_tags_to_game', kwargs)

    def assign_platforms_to_game(self, **kwargs):
        return self._call_inner_tool('assign_platforms_to_game', kwargs)

    def remove_tag_from_game(self, **kwargs):
        return self._call_inner_tool('remove_tag_from_game', kwargs)

    def remove_platform_from_game(self, **kwargs):
        return self._call_inner_tool('remove_platform_from_game', kwargs)

