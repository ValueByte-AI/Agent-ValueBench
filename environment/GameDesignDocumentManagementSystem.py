# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# Entity: Game
class GameInfo(TypedDict):
    game_id: str
    name: str
    description: str

# Entity: GameVersion (fix typo from "GameVersio"); also "status" corrected from "sta"
class GameVersionInfo(TypedDict):
    version_id: str
    game_id: str
    genre: str
    difficulty: str
    change_log: str
    status: str

# Entity: Character
class CharacterInfo(TypedDict):
    character_id: str
    name: str
    description: str

# Entity: Ability (fix typo from "Abil")
class AbilityInfo(TypedDict):
    ability_id: str
    name: str
    description: str

# Relationship: VersionCharacter
class VersionCharacterInfo(TypedDict):
    version_id: str
    character_id: str

# Relationship: CharacterAbility (fix typo from "CharacterAbil")
class CharacterAbilityInfo(TypedDict):
    character_id: str
    ability_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Games: {game_id: GameInfo}
        self.games: Dict[str, GameInfo] = {}

        # Game Versions: {version_id: GameVersionInfo}
        self.game_versions: Dict[str, GameVersionInfo] = {}

        # Characters: {character_id: CharacterInfo}
        self.characters: Dict[str, CharacterInfo] = {}

        # Abilities: {ability_id: AbilityInfo}
        self.abilities: Dict[str, AbilityInfo] = {}

        # Mapping: List of characters present per version
        # [VersionCharacterInfo]
        self.version_characters: List[VersionCharacterInfo] = []

        # Mapping: List of abilities per character (across any version or as reusable abilities)
        # [CharacterAbilityInfo]
        self.character_abilities: List[CharacterAbilityInfo] = []

        # Constraints:
        # - Each game version must have a valid genre and difficulty setting.
        # - Each character in a game version should reference valid abilities.
        # - Characters and abilities must be definable independently and reusable across versions/games.
        # - Versioning allows multiple variants of a game, each with distinct configurations.
        # - No two game versions of the same game can have the same combination of genre and difficulty.

    def get_game_by_name(self, name: str) -> dict:
        """
        Retrieve game information by its name.

        Args:
            name (str): The name of the game to search for.

        Returns:
            dict: {
                "success": True,
                "data": GameInfo  # Information about the matched game
            }
            or
            {
                "success": False,
                "error": str  # "Game not found"
            }

        Constraints:
            - Game names are assumed to be unique for querying purposes.
        """
        if not name:
            return { "success": False, "error": "Game not found" }

        for game in self.games.values():
            if game["name"] == name:
                return { "success": True, "data": game }
        return { "success": False, "error": "Game not found" }

    def list_games(self) -> dict:
        """
        List all games managed in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # All games' details (possibly empty)
            }
        """
        games_list = list(self.games.values())
        return { "success": True, "data": games_list }

    def get_version_by_id(self, version_id: str) -> dict:
        """
        Retrieve metadata for a specific game version by its unique version_id.

        Args:
            version_id (str): The unique identifier of the game version.

        Returns:
            dict:
                Success: { "success": True, "data": GameVersionInfo }
                Failure: { "success": False, "error": "Game version does not exist" }

        Constraints:
            - version_id must exist in the system.
        """
        if version_id not in self.game_versions:
            return { "success": False, "error": "Game version does not exist" }
        return { "success": True, "data": self.game_versions[version_id] }

    def list_versions_for_game(self, game_id: str) -> dict:
        """
        List all game versions/iterations for the given game_id.

        Args:
            game_id (str): The unique identifier of the game.

        Returns:
            dict: {
                "success": True,
                "data": List[GameVersionInfo]  # List of versions for this game. May be empty.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The provided game_id must exist in the system.
        """
        if game_id not in self.games:
            return {"success": False, "error": "Game ID does not exist"}

        result = [
            game_version for game_version in self.game_versions.values()
            if game_version["game_id"] == game_id
        ]

        return {"success": True, "data": result}

    def find_version_by_genre_difficulty(self, game_id: str, genre: str, difficulty: str) -> dict:
        """
        Checks if a specific game already has a version with the given combination of genre and difficulty.

        Args:
            game_id (str): Unique identifier for the game.
            genre (str): Genre to check.
            difficulty (str): Difficulty setting to check.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": GameVersionInfo | None  # The version info if found; otherwise None.
                }
                On error: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - game_id must exist in self.games.
            - Returns the first matching GameVersionInfo if present, otherwise data=None.
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game ID does not exist." }

        for version in self.game_versions.values():
            if (
                version["game_id"] == game_id and
                version["genre"] == genre and
                version["difficulty"] == difficulty
            ):
                return { "success": True, "data": version }
        return { "success": True, "data": None }

    def list_characters(self) -> dict:
        """
        Retrieve the list of all characters defined in the system.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[CharacterInfo]  # May be empty if no characters exist
                }
        """
        character_list = list(self.characters.values())
        return { "success": True, "data": character_list }

    def get_character_by_name(self, name: str) -> dict:
        """
        Retrieve character details by the character's name.

        Args:
            name (str): The character's name to search for.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CharacterInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Character not found"
                    }
                If input is missing/empty:
                    {
                        "success": False,
                        "error": "Character name must be provided"
                    }

        Constraints:
            - Character is uniquely identified by character_id; names may not be unique, but this method returns the first match.
        """
        if not name or not isinstance(name, str):
            return {
                "success": False,
                "error": "Character name must be provided"
            }
        for character in self.characters.values():
            if character["name"] == name:
                return {
                    "success": True,
                    "data": character
                }
        return {
            "success": False,
            "error": "Character not found"
        }

    def list_abilities(self) -> dict:
        """
        List all abilities present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AbilityInfo],  # List of all abilities in the system (may be empty)
            }
        """
        abilities_list = list(self.abilities.values())
        return {"success": True, "data": abilities_list}

    def get_ability_by_name(self, name: str) -> dict:
        """
        Retrieve ability details by ability name.
    
        Args:
            name (str): The exact name of the ability to search for.
        
        Returns:
            dict: {
                "success": True,
                "data": AbilityInfo  # Ability details if found
            }
            OR
            {
                "success": False,
                "error": str  # 'Ability not found' or input error
            }
        Constraints:
            - Ability name match is case-sensitive and requires exact equality.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or empty ability name"}

        for ability in self.abilities.values():
            if ability["name"] == name:
                return {"success": True, "data": ability}

        return {"success": False, "error": "Ability not found"}

    def list_characters_in_version(self, version_id: str) -> dict:
        """
        List all characters present in a particular game version.

        Args:
            version_id (str): The ID of the game version.

        Returns:
            dict: 
                - On success: { "success": True, "data": List[CharacterInfo] }
                - On failure: { "success": False, "error": str }

        Constraints:
            - The specified version_id must exist in the system.
            - If no characters are assigned to the version, data will be an empty list.
        """
        if version_id not in self.game_versions:
            return { "success": False, "error": "Game version does not exist" }

        character_ids = [vc["character_id"] for vc in self.version_characters if vc["version_id"] == version_id]
        # It's possible some character_ids are not present in self.characters due to deletions, but that's not required to handle here.
        characters = [self.characters[cid] for cid in character_ids if cid in self.characters]

        return { "success": True, "data": characters }

    def list_abilities_for_character(self, character_id: str) -> dict:
        """
        List all abilities (with metadata) assigned to a specific character.

        Args:
            character_id (str): Unique identifier of the character.

        Returns:
            dict:
                - { "success": True, "data": List[AbilityInfo] }
                  On success, 'data' is a list of abilities (may be empty if none are assigned).
                - { "success": False, "error": str }
                  If character does not exist.

        Constraints:
            - character_id must refer to an existing character.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist" }

        ability_ids = [
            ca["ability_id"]
            for ca in self.character_abilities
            if ca["character_id"] == character_id
        ]
        # Get only abilities that still exist in the abilities dictionary
        result = [
            self.abilities[aid]
            for aid in ability_ids
            if aid in self.abilities
        ]

        return { "success": True, "data": result }

    def list_abilities_for_character_in_version(self, character_id: str, version_id: str) -> dict:
        """
        List all abilities a character has within the context of a specific game version.

        Args:
            character_id (str): ID of the character.
            version_id (str): ID of the game version.

        Returns:
            dict:
                success (bool): Operation success.
                data (List[AbilityInfo]): List of ability info dicts this character has if present in the version, else empty or error.
                error (str): If failure, reason for failure.

        Constraints:
            - character_id and version_id must both exist.
            - The character must be assigned to the given version (present in version_characters).
            - All returned abilities must exist in self.abilities.
        """
        # Check character exists
        if character_id not in self.characters:
            return { "success": False, "error": f"Character {character_id} does not exist." }
        # Check version exists
        if version_id not in self.game_versions:
            return { "success": False, "error": f"Game version {version_id} does not exist." }
        # Check character assigned to version
        if not any(vc['character_id'] == character_id and vc['version_id'] == version_id for vc in self.version_characters):
            return { "success": False, "error": f"Character {character_id} is not assigned to version {version_id}." }
        # Find all ability_ids for this character
        ability_ids = [ca['ability_id'] for ca in self.character_abilities if ca['character_id'] == character_id]
        # Only return abilities that exist
        ability_infos = [self.abilities[aid] for aid in ability_ids if aid in self.abilities]
        return { "success": True, "data": ability_infos }

    def create_game(self, game_id: str, name: str, description: str) -> dict:
        """
        Add a new game to the system.

        Args:
            game_id (str): A unique identifier for the new game.
            name (str): The name of the game.
            description (str): A short description for the game.

        Returns:
            dict: {
                "success": True,
                "message": "Game '<name>' created successfully."
            }
            or
            {
                "success": False,
                "error": str  # If the game_id already exists or required fields are empty.
            }

        Constraints:
            - The game_id must be unique.
            - Name and description should not be empty.
        """
        if not game_id or not name or not description:
            return { "success": False, "error": "game_id, name, and description must be non-empty." }

        if game_id in self.games:
            return { "success": False, "error": "Game with this ID already exists." }

        self.games[game_id] = {
            "game_id": game_id,
            "name": name,
            "description": description
        }

        return {
            "success": True,
            "message": f"Game '{name}' created successfully."
        }

    def create_game_version(
        self,
        version_id: str,
        game_id: str,
        genre: str,
        difficulty: str,
        change_log: str,
        status: str
    ) -> dict:
        """
        Add a new version for a game, specifying genre and difficulty, ensuring uniqueness of (genre, difficulty) per game.

        Args:
            version_id (str): Unique identifier for the new game version.
            game_id (str): Identifier of the game to attach the new version to.
            genre (str): Genre of the game version (must be non-empty).
            difficulty (str): Difficulty setting (must be non-empty).
            change_log (str): Changelog or description of changes.
            status (str): Status of the game version (e.g., 'draft', 'released').

        Returns:
            dict: 
                { "success": True, "message": "Game version created successfully." }
                or 
                { "success": False, "error": <reason> }

        Constraints:
            - game_id must exist.
            - genre and difficulty must be provided (non-empty).
            - version_id must be unique.
            - No other game version for the same game has the same (genre, difficulty).
        """

        # Check for valid game
        if game_id not in self.games:
            return { "success": False, "error": "Game ID does not exist." }

        # Validate genre and difficulty
        if not genre or not genre.strip():
            return { "success": False, "error": "Genre must be provided and non-empty." }
        if not difficulty or not difficulty.strip():
            return { "success": False, "error": "Difficulty must be provided and non-empty." }

        # Check for unique version_id
        if version_id in self.game_versions:
            return { "success": False, "error": "Version ID already exists." }

        # Check uniqueness of (genre, difficulty) for this game
        for gv in self.game_versions.values():
            if gv["game_id"] == game_id and gv["genre"] == genre and gv["difficulty"] == difficulty:
                return { "success": False, "error": "A version with this genre and difficulty already exists for the game." }

        # Create the GameVersionInfo entry
        new_version = {
            "version_id": version_id,
            "game_id": game_id,
            "genre": genre,
            "difficulty": difficulty,
            "change_log": change_log,
            "status": status
        }
        self.game_versions[version_id] = new_version

        return { "success": True, "message": "Game version created successfully." }

    def create_character(self, character_id: str, name: str, description: str) -> dict:
        """
        Add a new character to the system.

        Args:
            character_id (str): Unique identifier for the character.
            name (str): Name of the character.
            description (str): Description of the character.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Character '<name>' created with id <character_id>."
                }
                On failure (e.g., duplicate ID or missing field),
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - character_id must be unique.
            - All fields must be provided and non-empty.
        """
        if not character_id or not name or not description:
            return {"success": False, "error": "All character fields (id, name, description) must be provided and non-empty."}
        if character_id in self.characters:
            return {"success": False, "error": "Character ID already exists."}
        character_info: CharacterInfo = {
            "character_id": character_id,
            "name": name,
            "description": description
        }
        self.characters[character_id] = character_info
        return {"success": True, "message": f"Character '{name}' created with id {character_id}."}

    def create_ability(self, ability_id: str, name: str, description: str) -> dict:
        """
        Add a new ability entity to the system.

        Args:
            ability_id (str): Unique identifier for the ability.
            name (str): Name of the ability.
            description (str): Description of the ability.

        Returns:
            dict: {
                "success": True,
                "message": "Ability created successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - ability_id must be unique in the system.
        """
        if ability_id in self.abilities:
            return {"success": False, "error": "Ability ID already exists"}
        self.abilities[ability_id] = {
            "ability_id": ability_id,
            "name": name,
            "description": description
        }
        return {"success": True, "message": "Ability created successfully"}

    def assign_character_to_version(self, version_id: str, character_id: str) -> dict:
        """
        Link an existing character to a specific game version.

        Args:
            version_id (str): The ID of the game version.
            character_id (str): The ID of the character to assign.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Character assigned to version successfully." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The version_id and character_id must exist.
            - The character must not already be assigned to this version.
        """

        if version_id not in self.game_versions:
            return { "success": False, "error": "Game version does not exist." }

        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist." }

        # Check for existing assignment
        for assoc in self.version_characters:
            if assoc["version_id"] == version_id and assoc["character_id"] == character_id:
                return { "success": False, "error": "Character is already assigned to this version." }
    
        # Assign character to version
        self.version_characters.append({
            "version_id": version_id,
            "character_id": character_id
        })

        return { "success": True, "message": "Character assigned to version successfully." }

    def assign_ability_to_character(self, character_id: str, ability_id: str) -> dict:
        """
        Assign an existing ability to a character.

        Args:
            character_id (str): The ID of the character to assign the ability to.
            ability_id (str): The ID of the ability to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Ability assigned to character."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - character_id must exist in self.characters.
            - ability_id must exist in self.abilities.
            - Prevent duplicate assignment.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist."}
        if ability_id not in self.abilities:
            return {"success": False, "error": "Ability does not exist."}
        for ca in self.character_abilities:
            if ca["character_id"] == character_id and ca["ability_id"] == ability_id:
                return {"success": False, "error": "Ability already assigned to character."}
        self.character_abilities.append({"character_id": character_id, "ability_id": ability_id})
        return {"success": True, "message": "Ability assigned to character."}

    def assign_multiple_abilities_to_character(self, character_id: str, ability_ids: List[str]) -> dict:
        """
        Assign multiple existing abilities to a character atomically.

        Args:
            character_id (str): The ID of the character to receive the abilities.
            ability_ids (List[str]): Ability IDs to assign in this batch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "<n> abilities assigned to character."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure."
                    }

        Constraints:
            - character_id must exist in self.characters.
            - ability_ids must be a non-empty list of unique ability IDs.
            - Every ability_id must exist in self.abilities.
            - Prevent duplicate assignment.
            - The operation is atomic: if any requested assignment is invalid, no assignment is applied.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist."}
        if not isinstance(ability_ids, list) or not ability_ids:
            return {"success": False, "error": "ability_ids must be a non-empty list."}
        if any(not isinstance(ability_id, str) or not ability_id for ability_id in ability_ids):
            return {"success": False, "error": "Each ability_id must be a non-empty string."}
        if len(set(ability_ids)) != len(ability_ids):
            return {"success": False, "error": "Duplicate ability IDs are not allowed in a batch assignment."}

        missing = [ability_id for ability_id in ability_ids if ability_id not in self.abilities]
        if missing:
            return {"success": False, "error": f"Abilities do not exist: {missing}"}

        existing = {
            ca["ability_id"]
            for ca in self.character_abilities
            if ca["character_id"] == character_id
        }
        duplicates = [ability_id for ability_id in ability_ids if ability_id in existing]
        if duplicates:
            return {"success": False, "error": f"Abilities already assigned to character: {duplicates}"}

        for ability_id in ability_ids:
            self.character_abilities.append({"character_id": character_id, "ability_id": ability_id})
        return {
            "success": True,
            "message": f"{len(ability_ids)} abilities assigned to character."
        }

    def remove_character_from_version(self, version_id: str, character_id: str) -> dict:
        """
        Detach a character from a specific game version.

        Args:
            version_id (str): The game version from which the character should be removed.
            character_id (str): The character to remove from the game version.

        Returns:
            dict: On success,
                {"success": True, "message": "Character <character_id> removed from version <version_id>" }
            On failure,
                {"success": False, "error": "reason" }

        Constraints:
            - The version_id must exist in self.game_versions.
            - The character_id must exist in self.characters.
            - The association (version_id, character_id) must exist.
        """
        if version_id not in self.game_versions:
            return {"success": False, "error": "Invalid version ID"}
        if character_id not in self.characters:
            return {"success": False, "error": "Invalid character ID"}
    
        found = False
        for idx, vc in enumerate(self.version_characters):
            if vc["version_id"] == version_id and vc["character_id"] == character_id:
                found = True
                del self.version_characters[idx]
                break

        if not found:
            return {"success": False, "error": "Character not assigned to version"}
    
        return {"success": True, "message": f"Character {character_id} removed from version {version_id}"}

    def remove_ability_from_character(self, character_id: str, ability_id: str) -> dict:
        """
        Unassign (remove) an ability from a character.

        Args:
            character_id (str): The ID of the character.
            ability_id (str): The ID of the ability to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Ability removed from character."
            }
            OR
            {
                "success": False,
                "error": reason string
            }

        Constraints:
            - character_id must exist in self.characters.
            - ability_id must exist in self.abilities.
            - The (character_id, ability_id) mapping must exist in self.character_abilities.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist."}

        if ability_id not in self.abilities:
            return {"success": False, "error": "Ability does not exist."}

        found = False
        for idx, mapping in enumerate(self.character_abilities):
            if mapping["character_id"] == character_id and mapping["ability_id"] == ability_id:
                found = True
                del self.character_abilities[idx]
                break

        if not found:
            return {
                "success": False,
                "error": "Ability is not assigned to the character."
            }

        return {
            "success": True,
            "message": "Ability removed from character."
        }

    def update_game_version_metadata(
        self,
        version_id: str,
        genre: str = None,
        difficulty: str = None,
        change_log: str = None,
        status: str = None
    ) -> dict:
        """
        Edit a game version's metadata fields: genre, difficulty, change_log, or status.
        Enforces that (genre, difficulty) combination is unique per game.

        Args:
            version_id (str): The version to update.
            genre (str, optional): New genre. If given, must not duplicate another version's (game_id, genre, difficulty).
            difficulty (str, optional): New difficulty. Ditto.
            change_log (str, optional): New changelog notes.
            status (str, optional): New status.

        Returns:
            dict:
                On success: { "success": True, "message": "Updated: <fields>..." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - A version's (genre, difficulty) for the same game cannot duplicate that of another version.
            - Each genre and difficulty must be a non-empty string if updated.
            - At least one field must be updated.
        """
        if version_id not in self.game_versions:
            return { "success": False, "error": "Game version not found." }

        version = self.game_versions[version_id]
        fields_updated = []

        # Collect potential new values
        new_genre = genre if genre is not None else version['genre']
        new_difficulty = difficulty if difficulty is not None else version['difficulty']

        # Validate proper inputs if being changed
        if genre is not None and not (isinstance(genre, str) and genre.strip()):
            return { "success": False, "error": "Genre must be a non-empty string." }
        if difficulty is not None and not (isinstance(difficulty, str) and difficulty.strip()):
            return { "success": False, "error": "Difficulty must be a non-empty string." }
        if genre is None and difficulty is None and change_log is None and status is None:
            return { "success": False, "error": "No fields specified for update." }
    
        # Enforce (game_id, genre, difficulty) unique combo for this game
        if genre is not None or difficulty is not None:
            game_id = version['game_id']
            for v_id, v_info in self.game_versions.items():
                if v_id == version_id:
                    continue  # Skip self
                if v_info['game_id'] == game_id:
                    if (v_info['genre'] == new_genre and v_info['difficulty'] == new_difficulty):
                        return { "success": False, "error": "Another version of this game already uses that (genre, difficulty) combination." }

        # Apply updates
        if genre is not None:
            version['genre'] = genre
            fields_updated.append("genre")
        if difficulty is not None:
            version['difficulty'] = difficulty
            fields_updated.append("difficulty")
        if change_log is not None:
            version['change_log'] = change_log
            fields_updated.append("change_log")
        if status is not None:
            version['status'] = status
            fields_updated.append("status")

        if not fields_updated:
            return { "success": False, "error": "No fields were updated." }

        return {
            "success": True,
            "message": f"Updated: {', '.join(fields_updated)} for version {version_id}"
        }

    def delete_game_version(self, version_id: str) -> dict:
        """
        Remove a game version and its associations (VersionCharacter) if it exists.

        Args:
            version_id (str): The unique ID of the game version to delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Game version <version_id> deleted successfully" }
                On failure: { "success": False, "error": "Game version <version_id> does not exist" }

        Constraints:
            - Only the specified GameVersion and its VersionCharacter associations are removed.
            - Characters and abilities themselves are NOT deleted.
            - If version_id is not found, return an error.
        """
        if version_id not in self.game_versions:
            return { "success": False, "error": f"Game version {version_id} does not exist" }

        # Remove the GameVersion entry
        del self.game_versions[version_id]

        # Remove all VersionCharacter associations for this version
        self.version_characters = [
            vc for vc in self.version_characters
            if vc["version_id"] != version_id
        ]

        # No need to alter characters or abilities themselves (by requirements)
        return {
            "success": True,
            "message": f"Game version {version_id} deleted successfully"
        }

    def delete_character(self, character_id: str) -> dict:
        """
        Remove a character from the system if it is not referenced in any live version.

        Args:
            character_id (str): The unique ID of the character to delete.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Character <name> (<character_id>) deleted."
                    }
                - On error:
                    {
                        "success": False,
                        "error": "<error description>"
                    }

        Constraints:
            - Character must not be referenced in any "live" game version.
            - Removes all ability assignments for this character.
            - Removes all dangling version-character associations for this character.
        """
        char_info = self.characters.get(character_id)
        if not char_info:
            return { "success": False, "error": "Character not found." }

        # Find if character is present in any live versions
        for vc in self.version_characters:
            if vc["character_id"] == character_id:
                version_id = vc["version_id"]
                gv = self.game_versions.get(version_id)
                if gv and gv.get("status", "").lower() == "live":
                    game_name = self.games[gv["game_id"]]["name"] if gv["game_id"] in self.games else gv["game_id"]
                    return {
                        "success": False,
                        "error": f"Character '{char_info['name']}' is used in live version '{version_id}' of game '{game_name}'."
                    }

        # Passed: safe to delete
        del self.characters[character_id]

        # Remove from character_abilities
        self.character_abilities = [
            ca for ca in self.character_abilities if ca["character_id"] != character_id
        ]
        # Remove from version_characters (in case of any dangling assignments)
        self.version_characters = [
            vc for vc in self.version_characters if vc["character_id"] != character_id
        ]

        return {
            "success": True,
            "message": f"Character '{char_info['name']}' ({character_id}) deleted."
        }

    def delete_ability(self, ability_id: str) -> dict:
        """
        Remove an ability from the system if it is not referenced by any character.

        Args:
            ability_id (str): The ID of the ability to remove.

        Returns:
            dict:
                - On success:
                    {'success': True, 'message': 'Ability deleted successfully'}
                - On failure (not found or still referenced):
                    {'success': False, 'error': str}

        Constraints:
            - The ability must not be referenced by any character in the system.
            - If the ability does not exist, should fail.
        """
        # Check if the ability exists
        if ability_id not in self.abilities:
            return { "success": False, "error": "Ability does not exist" }

        # Check if any character references this ability
        for ca in self.character_abilities:
            if ca['ability_id'] == ability_id:
                return { 
                    "success": False, 
                    "error": "Ability is still assigned to one or more characters"
                }

        # Safe to delete
        del self.abilities[ability_id]
        return { "success": True, "message": "Ability deleted successfully" }


class GameDesignDocumentManagementSystem(BaseEnv):
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
        init_config = copy.deepcopy(init_config)
        for state_key, id_field in (
            ("games", "game_id"),
            ("game_versions", "version_id"),
            ("characters", "character_id"),
            ("abilities", "ability_id"),
        ):
            records = init_config.get(state_key)
            if isinstance(records, dict):
                init_config[state_key] = {
                    (record.get(id_field) if isinstance(record, dict) and record.get(id_field) else key): record
                    for key, record in records.items()
                }
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

    def get_game_by_name(self, **kwargs):
        return self._call_inner_tool('get_game_by_name', kwargs)

    def list_games(self, **kwargs):
        return self._call_inner_tool('list_games', kwargs)

    def get_version_by_id(self, **kwargs):
        return self._call_inner_tool('get_version_by_id', kwargs)

    def list_versions_for_game(self, **kwargs):
        return self._call_inner_tool('list_versions_for_game', kwargs)

    def find_version_by_genre_difficulty(self, **kwargs):
        return self._call_inner_tool('find_version_by_genre_difficulty', kwargs)

    def list_characters(self, **kwargs):
        return self._call_inner_tool('list_characters', kwargs)

    def get_character_by_name(self, **kwargs):
        return self._call_inner_tool('get_character_by_name', kwargs)

    def list_abilities(self, **kwargs):
        return self._call_inner_tool('list_abilities', kwargs)

    def get_ability_by_name(self, **kwargs):
        return self._call_inner_tool('get_ability_by_name', kwargs)

    def list_characters_in_version(self, **kwargs):
        return self._call_inner_tool('list_characters_in_version', kwargs)

    def list_abilities_for_character(self, **kwargs):
        return self._call_inner_tool('list_abilities_for_character', kwargs)

    def list_abilities_for_character_in_version(self, **kwargs):
        return self._call_inner_tool('list_abilities_for_character_in_version', kwargs)

    def create_game(self, **kwargs):
        return self._call_inner_tool('create_game', kwargs)

    def create_game_version(self, **kwargs):
        return self._call_inner_tool('create_game_version', kwargs)

    def create_character(self, **kwargs):
        return self._call_inner_tool('create_character', kwargs)

    def create_ability(self, **kwargs):
        return self._call_inner_tool('create_ability', kwargs)

    def assign_character_to_version(self, **kwargs):
        return self._call_inner_tool('assign_character_to_version', kwargs)

    def assign_ability_to_character(self, **kwargs):
        return self._call_inner_tool('assign_ability_to_character', kwargs)

    def assign_multiple_abilities_to_character(self, **kwargs):
        return self._call_inner_tool('assign_multiple_abilities_to_character', kwargs)

    def remove_character_from_version(self, **kwargs):
        return self._call_inner_tool('remove_character_from_version', kwargs)

    def remove_ability_from_character(self, **kwargs):
        return self._call_inner_tool('remove_ability_from_character', kwargs)

    def update_game_version_metadata(self, **kwargs):
        return self._call_inner_tool('update_game_version_metadata', kwargs)

    def delete_game_version(self, **kwargs):
        return self._call_inner_tool('delete_game_version', kwargs)

    def delete_character(self, **kwargs):
        return self._call_inner_tool('delete_character', kwargs)

    def delete_ability(self, **kwargs):
        return self._call_inner_tool('delete_ability', kwargs)
