# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class PlayerInfo(TypedDict):
    player_id: str
    username: str
    rating: int

class GameInfo(TypedDict):
    game_id: str
    white_player_id: str
    black_player_id: str
    timestamp: str  # e.g., ISO8601 datetime string
    moves: List[str]  # List of move strings in SAN/algebraic notation
    result: str  # e.g., "1-0", "0-1", "1/2-1/2", "aborted"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Online chess platform game database environment.
        """

        # Players: {player_id: PlayerInfo}
        # State space entity: Player (player_id, username, rating)
        self.players: Dict[str, PlayerInfo] = {}

        # Games: {game_id: GameInfo}
        # State space entity: Game (game_id, white_player_id, black_player_id, timestamp, moves, result)
        self.games: Dict[str, GameInfo] = {}

        # Constraints:
        # - Every game must have valid player references for both white and black.
        # - Game IDs are unique.
        # - Move lists must be valid chess move sequences.
        # - Result must be a valid chess outcome (e.g., "1-0", "0-1", "1/2-1/2", "aborted", etc.).

    def get_game_by_id(self, game_id: str) -> dict:
        """
        Retrieve the complete game information for a given game_id.

        Args:
            game_id (str): The unique identifier of the chess game.

        Returns:
            dict: {
                "success": True,
                "data": GameInfo,   # The full game data
            }
            or
            {
                "success": False,
                "error": str        # "Game not found"
            }

        Constraints:
            - The provided game_id must exist in the database.
        """
        game = self.games.get(game_id)
        if game is None:
            return {"success": False, "error": "Game not found"}
        return {"success": True, "data": game}

    def get_game_moves(self, game_id: str) -> dict:
        """
        Retrieve the list of moves (in notation) for a given game_id.

        Args:
            game_id (str): The unique ID of the chess game.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of move strings (possibly empty if no moves)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., game not found
            }

        Constraints:
            - The given game_id must exist in the game database.
        """
        game = self.games.get(game_id)
        if not game:
            return {"success": False, "error": "Game ID not found"}
        return {"success": True, "data": game["moves"]}

    def get_game_result(self, game_id: str) -> dict:
        """
        Retrieve the final result/outcome of the game for the specified game_id.

        Args:
            game_id (str): The unique identifier of the chess game.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": str  # The game's result field, e.g., "1-0", "0-1", "1/2-1/2", "aborted"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # E.g., "Game ID does not exist"
                    }
        Constraints:
            - The specified game_id must exist in the game database.
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game ID does not exist" }

        result = self.games[game_id]["result"]
        return { "success": True, "data": result }

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve platform user (Player) information given a player_id.

        Args:
            player_id (str): The unique identifier for the player.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo  # The player's complete info
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., player does not exist
            }

        Constraints:
            - The player_id must exist in self.players.
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player does not exist"}
        return {"success": True, "data": player}

    def get_player_by_username(self, username: str) -> dict:
        """
        Retrieve PlayerInfo using the username.

        Args:
            username (str): The unique username of the player.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PlayerInfo  # Information of the matched player
                    }
                On error (not found):
                    {
                        "success": False,
                        "error": "Player not found"
                    }
        Constraints:
            - Username is expected to be unique across all players.
        """
        for player in self.players.values():
            if player["username"] == username:
                return {"success": True, "data": player}
        return {"success": False, "error": "Player not found"}

    def list_games_for_player(self, player_id: str = None, username: str = None) -> dict:
        """
        Retrieve all games played by a player (as white or black), given player_id or username.

        Args:
            player_id (str, optional): The unique id of the player.
            username (str, optional): The username of the player.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo]  # All games where the player was white or black
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (player not found, missing/conflicting ids)
            }

        Constraints:
            - At least one of player_id or username must be provided.
            - If both are provided they must refer to the same player.
            - The player must exist in the database.
        """
        # Input validation
        if not player_id and not username:
            return { "success": False, "error": "Must provide either player_id or username." }
    
        # Identify player
        found_player = None

        if player_id and username:
            # Both provided: check consistency
            player_info = self.players.get(player_id)
            if not player_info:
                return { "success": False, "error": "No player with specified player_id." }
            if player_info["username"] != username:
                return { "success": False, "error": "player_id and username refer to different players." }
            found_player = player_info

        elif player_id:
            player_info = self.players.get(player_id)
            if not player_info:
                return { "success": False, "error": "No player with specified player_id." }
            found_player = player_info

        else:  # username only
            for p in self.players.values():
                if p["username"] == username:
                    found_player = p
                    break
            if not found_player:
                return { "success": False, "error": "No player with specified username." }

        # Get all games where this player played as white or black
        pid = found_player["player_id"]
        games = [
            game for game in self.games.values()
            if game["white_player_id"] == pid or game["black_player_id"] == pid
        ]

        return { "success": True, "data": games }

    def get_recent_games_for_player(self, player_id: str) -> dict:
        """
        Retrieve a list of games played by the given player, sorted by timestamp descending (most recent first).

        Args:
            player_id (str): The ID of the player to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # List of games with this player, sorted by timestamp descending.
            }
            or
            {
                "success": False,
                "error": str  # 'Player does not exist'
            }

        Constraints:
            - Player ID must exist in players.
            - Returned list is sorted most recent first (timestamp descending).
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        relevant_games = [
            game_info for game_info in self.games.values()
            if game_info['white_player_id'] == player_id or game_info['black_player_id'] == player_id
        ]

        # Timestamps are ISO8601 strings, so can compare/sort lexicographically (descending)
        relevant_games_sorted = sorted(
            relevant_games,
            key=lambda g: g['timestamp'],
            reverse=True
        )

        return { "success": True, "data": relevant_games_sorted }

    def validate_game_integrity(self, game_id: str) -> dict:
        """
        Check if a game references valid players, contains a plausible move list, and a valid result.

        Args:
            game_id (str): ID of the game to validate.

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        "valid": bool,              # True if game passes all integrity checks
                        "problems": List[str],      # List of problems found (empty if valid)
                    }
                }
                or
                {
                    "success": False,
                    "error": str                   # Explanation if operation cannot proceed (e.g., game_id invalid)
                }

        Constraints:
            - Game must exist.
            - Both player references (white and black) must exist.
            - Move list must be a list of plausible (string) moves.
            - Result must be a valid chess outcome ("1-0", "0-1", "1/2-1/2", "aborted").
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game not found" }

        game = self.games[game_id]
        problems = []

        # Check player references
        if game["white_player_id"] not in self.players:
            problems.append("White player ID does not exist: {}".format(game["white_player_id"]))
        if game["black_player_id"] not in self.players:
            problems.append("Black player ID does not exist: {}".format(game["black_player_id"]))

        # Check move list is a list of strings, optionally allow empty games (aborted, etc)
        if not isinstance(game["moves"], list):
            problems.append("Move list is not a list.")
        elif not all(isinstance(move, str) and move.strip() != "" for move in game["moves"]):
            problems.append("Move list contains non-string or empty moves.")
        else:
            irregular_tokens = [
                move
                for move in game["moves"]
                if move.startswith(("ERR_", "SYS_")) or "0x" in move
            ]
            if irregular_tokens:
                problems.append(
                    "Move list contains irregular system tokens: " + ", ".join(irregular_tokens)
                )

        # Result validity
        valid_results = {"1-0", "0-1", "1/2-1/2", "aborted"}
        if game["result"] not in valid_results:
            problems.append(f'Result "{game["result"]}" is not valid.')

        is_valid = len(problems) == 0

        return {
            "success": True,
            "data": {
                "valid": is_valid,
                "problems": problems
            }
        }

    def add_new_game(
        self, 
        game_id: str, 
        white_player_id: str, 
        black_player_id: str, 
        timestamp: str, 
        moves: list, 
        result: str
    ) -> dict:
        """
        Add a new game record to the database after validating:
          - Unique game_id
          - Existing player references for both sides
          - Moves is a non-empty list of strings (basic validation)
          - Result is an accepted chess outcome
    
        Args:
            game_id (str): Unique identifier for the chess game.
            white_player_id (str): Player ID of the white side.
            black_player_id (str): Player ID of the black side.
            timestamp (str): Timestamp in ISO8601 format.
            moves (List[str]): List of move strings (in SAN or algebraic notation).
            result (str): Result of the game ("1-0", "0-1", "1/2-1/2", "aborted", etc.).
    
        Returns:
            dict:
                {"success": True, "message": "Game record added."}
                or
                {"success": False, "error": <reason>}
    
        Constraints:
            - game_id must be unique.
            - Both player IDs must exist in self.players.
            - moves must be a non-empty list of strings.
            - result must be a valid chess result.
        """
        # Check game_id uniqueness
        if game_id in self.games:
            return {"success": False, "error": "Game ID already exists."}
    
        # Check both players exist
        if white_player_id not in self.players:
            return {"success": False, "error": "White player ID does not exist."}
        if black_player_id not in self.players:
            return {"success": False, "error": "Black player ID does not exist."}
    
        # Moves validation: non-empty list of strings
        if not isinstance(moves, list) or not all(isinstance(m, str) for m in moves):
            return {"success": False, "error": "Moves must be a list of strings."}
        if len(moves) == 0:
            return {"success": False, "error": "Moves list cannot be empty."}
    
        # Acceptable result values
        valid_results = {"1-0", "0-1", "1/2-1/2", "aborted"}
        if result not in valid_results:
            return {"success": False, "error": f"Result '{result}' is not valid."}
    
        # Construct and store the new game
        self.games[game_id] = {
            "game_id": game_id,
            "white_player_id": white_player_id,
            "black_player_id": black_player_id,
            "timestamp": timestamp,
            "moves": moves.copy(),
            "result": result
        }
    
        return {"success": True, "message": "Game record added."}

    def update_game_moves(self, game_id: str, moves: list) -> dict:
        """
        Update the moves list for a specific game, for correction or modification.

        Args:
            game_id (str): Unique identifier for the game to update.
            moves (List[str]): The new move list (each a string in SAN/algebraic notation).

        Returns:
            dict: {
                "success": True,
                "message": "Moves updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Game ID must exist.
            - Moves list must be a list of strings (only basic type/format check, full chess legality not enforced here).
            - Game's player references and result remain unchanged.
        """
        # Check game exists
        if game_id not in self.games:
            return { "success": False, "error": "Game not found." }

        # Basic validation for moves (must be a list of non-empty strings)
        if not isinstance(moves, list):
            return { "success": False, "error": "Moves must be provided as a list." }
        if not all(isinstance(move, str) and move.strip() for move in moves):
            return { "success": False, "error": "All moves must be non-empty strings." }

        # (The detailed legality of the move sequence cannot be validated here.)

        # Perform the update
        self.games[game_id]["moves"] = moves

        return { "success": True, "message": "Moves updated successfully." }

    def update_game_result(self, game_id: str, result: str) -> dict:
        """
        Update the final result of a specific game (to correct mistakes or adjudicate).

        Args:
            game_id (str): The unique identifier of the game to update.
            result (str): The new game result value ("1-0", "0-1", "1/2-1/2", "aborted", etc.).

        Returns:
            dict:
                On success: { "success": True, "message": "Game result updated successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Game must exist.
            - Result must be a valid chess outcome.
        """
        valid_results = {"1-0", "0-1", "1/2-1/2", "aborted"}
        if game_id not in self.games:
            return {"success": False, "error": "Game ID does not exist."}
        if result not in valid_results:
            return {"success": False, "error": "Invalid result value."}

        self.games[game_id]["result"] = result
        return {"success": True, "message": "Game result updated successfully."}


    def add_new_player(self, username: str, rating: int) -> dict:
        """
        Add a new player to the player database with a given username and rating.

        Args:
            username (str): The desired unique username for the player.
            rating (int): The initial rating for the player (must be non-negative).

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Player <username> added with id <player_id>"}
                - On failure:
                    {"success": False, "error": "<reason>"}
        Constraints:
            - username must be unique in self.players (no two players with the same username)
            - rating must be non-negative
            - player_id must be globally unique
        """
        # Check username uniqueness
        if any(p["username"] == username for p in self.players.values()):
            return {"success": False, "error": "Username already exists"}

        # Check rating validity
        if not isinstance(rating, int) or rating < 0:
            return {"success": False, "error": "Rating must be a non-negative integer"}

        player_id = str(uuid.uuid4())
        while player_id in self.players:
            player_id = str(uuid.uuid4())

        player_info = {
            "player_id": player_id,
            "username": username,
            "rating": rating
        }
        self.players[player_id] = player_info

        return {"success": True, "message": f"Player {username} added with id {player_id}"}

    def update_player_info(self, player_id: str, username: str = None, rating: int = None) -> dict:
        """
        Modify a player’s username and/or rating.

        Args:
            player_id (str): The ID of the player to update.
            username (str, optional): New username. If None, username is not changed.
            rating (int, optional): New rating. If None, rating is not changed.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Player info updated"
                }
                or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Player must exist in the database (player_id in self.players).
            - At least one of username or rating must be provided.
            - rating, if set, must be integer.
            - username, if set, must be string.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }

        if username is None and rating is None:
            return { "success": False, "error": "No update fields provided" }

        if username is not None and not isinstance(username, str):
            return { "success": False, "error": "Invalid username type; must be string" }

        if rating is not None and not isinstance(rating, int):
            return { "success": False, "error": "Invalid rating type; must be int" }

        player = self.players[player_id]
        if username is not None:
            player["username"] = username
        if rating is not None:
            player["rating"] = rating

        self.players[player_id] = player  # Actually not required but explicit

        return { "success": True, "message": "Player info updated" }

    def delete_game_by_id(self, game_id: str) -> dict:
        """
        Remove a game from the database by its ID.

        Args:
            game_id (str): Unique identifier of the game to delete.

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Game <game_id> deleted." }
                On failure: 
                    { "success": False, "error": "Game ID not found." }

        Constraints:
            - The specified game_id must exist in the games database.
            - This operation does not affect any players (they aren't deleted/modified).
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game ID not found." }

        del self.games[game_id]
        return { "success": True, "message": f"Game {game_id} deleted." }

    def delete_player_by_id(self, player_id: str) -> dict:
        """
        Remove a player from the system by their player_id.
        If the player is referenced in any games as either white or black, prevent deletion.

        Args:
            player_id (str): The unique identifier for the player to be deleted.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Player deleted successfully."}
                - On failure:
                    {"success": False, "error": "Reason for failure (not found, referenced in games, etc.)"}
    
        Constraints:
            - Player must exist.
            - Player must not be referenced in any games as white or black.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}

        for game in self.games.values():
            if game["white_player_id"] == player_id or game["black_player_id"] == player_id:
                return {
                    "success": False,
                    "error": "Player is referenced in existing games and cannot be deleted."
                }
        del self.players[player_id]
        return {"success": True, "message": "Player deleted successfully."}

    def correct_game_player_reference(self, game_id: str, color: str, new_player_id: str) -> dict:
        """
        Update the white or black player reference in a game after validating that both
        the game and the player exist, and the color is either 'white' or 'black'.
    
        Args:
            game_id (str): The ID of the game to update.
            color (str): Which player to update: 'white' or 'black'.
            new_player_id (str): The new player_id to set.
    
        Returns:
            dict: {
                "success": True,
                "message": "Player reference updated for game <game_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The game must exist.
            - The new player must exist.
            - The color must be 'white' or 'black'.
            - After update, both player references should still be valid.
        """
        # Check if the game exists
        if game_id not in self.games:
            return {"success": False, "error": "Game does not exist"}
    
        # Check that the color is valid
        if color not in ("white", "black"):
            return {"success": False, "error": "Color must be 'white' or 'black'"}
    
        # Check player exists
        if new_player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}
    
        game = self.games[game_id]
    
        # Perform the update
        if color == "white":
            old_player_id = game["white_player_id"]
            game["white_player_id"] = new_player_id
        else:
            old_player_id = game["black_player_id"]
            game["black_player_id"] = new_player_id

        # You could check if after update, both player references refer to existing players
        # (but since new_player_id is checked, only need to double-check the other one)
        other_player_id = game["black_player_id"] if color == "white" else game["white_player_id"]
        if other_player_id not in self.players:
            # Restore the old reference and error
            if color == "white":
                game["white_player_id"] = old_player_id
            else:
                game["black_player_id"] = old_player_id
            return { "success": False, "error": "Other player reference is now invalid" }
    
        return {
            "success": True,
            "message": f"Player reference for '{color}' updated in game {game_id}."
        }


class ChessGameDatabase(BaseEnv):
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

    def get_game_by_id(self, **kwargs):
        return self._call_inner_tool('get_game_by_id', kwargs)

    def get_game_moves(self, **kwargs):
        return self._call_inner_tool('get_game_moves', kwargs)

    def get_game_result(self, **kwargs):
        return self._call_inner_tool('get_game_result', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_player_by_username(self, **kwargs):
        return self._call_inner_tool('get_player_by_username', kwargs)

    def list_games_for_player(self, **kwargs):
        return self._call_inner_tool('list_games_for_player', kwargs)

    def get_recent_games_for_player(self, **kwargs):
        return self._call_inner_tool('get_recent_games_for_player', kwargs)

    def validate_game_integrity(self, **kwargs):
        return self._call_inner_tool('validate_game_integrity', kwargs)

    def add_new_game(self, **kwargs):
        return self._call_inner_tool('add_new_game', kwargs)

    def update_game_moves(self, **kwargs):
        return self._call_inner_tool('update_game_moves', kwargs)

    def update_game_result(self, **kwargs):
        return self._call_inner_tool('update_game_result', kwargs)

    def add_new_player(self, **kwargs):
        return self._call_inner_tool('add_new_player', kwargs)

    def update_player_info(self, **kwargs):
        return self._call_inner_tool('update_player_info', kwargs)

    def delete_game_by_id(self, **kwargs):
        return self._call_inner_tool('delete_game_by_id', kwargs)

    def delete_player_by_id(self, **kwargs):
        return self._call_inner_tool('delete_player_by_id', kwargs)

    def correct_game_player_reference(self, **kwargs):
        return self._call_inner_tool('correct_game_player_reference', kwargs)
