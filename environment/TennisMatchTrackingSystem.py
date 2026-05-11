# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import datetime
import time
from typing import Optional



class PlayerInfo(TypedDict):
    player_id: str
    name: str
    ranking: int
    nationality: str

class ScoreInfo(TypedDict):
    match_id: str
    player_id: str
    sets: List[int]
    games_in_current_set: int
    points_in_current_game: int

class MatchInfo(TypedDict):
    match_id: str
    players: List[str]  # List of two player_ids
    scores: Dict[str, ScoreInfo]  # Mapping player_id → ScoreInfo
    status: str
    start_time: Optional[str]
    end_time: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Tennis match tracking system state management.
        """

        # Players: {player_id: PlayerInfo}
        # Represents the player roster.
        self.players: Dict[str, PlayerInfo] = {}

        # Matches: {match_id: MatchInfo}
        # Each match links to participating players, its scores, status, and timing.
        self.matches: Dict[str, MatchInfo] = {}

        # Scores: {match_id: {player_id: ScoreInfo}}
        # Scores are also accessible outside of matches for rapid lookup.
        self.scores: Dict[str, Dict[str, ScoreInfo]] = {}

        # Constraints:
        # - Each match must have exactly two players.
        # - Scores are tracked per player and updated according to tennis rules (points, games, sets).
        # - Status for each match must be one of: 'scheduled', 'ongoing', 'completed', 'canceled'.
        # - Players in a match must exist in the player roster.
        # - Matches can only be edited if their status is 'scheduled' or 'ongoing'.

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve complete information for a given match by its match_id.
    
        Args:
            match_id (str): Unique identifier of the tennis match.
        
        Returns:
            dict: {
                "success": True,
                "data": MatchInfo,  # Full match info on success
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. match not found
            }
        
        Constraints:
            - The specified match_id must exist in the matches dictionary.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match }

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve all available details about a player (name, ranking, nationality)
        given their player_id.

        Args:
            player_id (str): Unique identifier for the player.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo (if player exists)
            } or {
                "success": False,
                "error": str (if the player does not exist)
            }

        Constraints:
            - player_id must exist in the player roster.
        """
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player}

    def get_player_by_name(self, name: str) -> dict:
        """
        Find player(s) by name (case-insensitive exact match).

        Args:
            name (str): The full name of the player to look up.

        Returns:
            dict:
                - If found: {"success": True, "data": List[PlayerInfo]}  # All matching players
                - If not found: {"success": False, "error": "Player not found"}

        Notes:
            - Returns all players with the exact provided name (case-insensitive).
            - If multiple players have the same name, all are included in the list.
        """
        name_lower = name.strip().lower()
        matches = [
            player_info for player_info in self.players.values()
            if player_info["name"].strip().lower() == name_lower
        ]
        if not matches:
            return { "success": False, "error": "Player not found" }
        return { "success": True, "data": matches }

    def get_match_players(self, match_id: str) -> dict:
        """
        Retrieve the list of participating players' IDs and names for a given match.

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, str]]  # Each dict contains "player_id" and "name"
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The match must exist.
            - All player IDs in the match should exist in the player roster.

        Edge Cases:
            - If any player_id from the match does not exist in the roster, this will be indicated in the player entry as name=None.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        players_list = []
        for pid in match["players"]:
            player_info = self.players.get(pid)
            players_list.append({
                "player_id": pid,
                "name": player_info["name"] if player_info else None
            })
        return { "success": True, "data": players_list }

    def get_match_scores(self, match_id: str) -> dict:
        """
        Retrieve all scoring information (sets, games, points) for both players in a given match.

        Args:
            match_id (str): The unique identifier of the tennis match.

        Returns:
            dict:
                - { "success": True, "data": Dict[str, ScoreInfo] }
                  data: player_id → ScoreInfo for both players in the match
                - { "success": False, "error": str }
                  if match not found

        Constraints:
            - The specified match_id must exist in the system.

        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }

        # match["scores"] is already structured as player_id → ScoreInfo
        scores = match.get("scores", {})
        # Defensive: Ensure only the actual players' scores are included
        valid_scores = {pid: scores[pid] for pid in match["players"] if pid in scores}

        return { "success": True, "data": valid_scores }

    def get_player_score_in_match(self, match_id: str, player_id: str) -> dict:
        """
        Retrieve score details (ScoreInfo) for a specific player in a given match.

        Args:
            match_id (str): The identifier of the match.
            player_id (str): The identifier of the player.

        Returns:
            dict: 
            {
                "success": True,
                "data": ScoreInfo,
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - Both match and player must exist.
            - Player must be a participant in the match.
            - Score data must exist for player in match.
        """
        # Check match existence
        match = self.matches.get(match_id)
        if match is None:
            return {"success": False, "error": "Match does not exist."}

        # Check player existence
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}

        # Check player is in this match
        if player_id not in match['players']:
            return {"success": False, "error": "Player is not a participant in the match."}

        # Check score info exists
        score_info = match['scores'].get(player_id)
        if score_info is None:
            return {"success": False, "error": "Score data for player in match not found."}

        return {"success": True, "data": score_info}

    def list_all_matches(self) -> dict:
        """
        Returns a list of all matches in the system, with summary info for each match.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict includes match_id, status, and players (player_id + name)
            }

        If no matches exist, data is an empty list.
        """
        result = []
        for match in self.matches.values():
            # Build player summaries
            players_summary = []
            for pid in match['players']:
                player_info = self.players.get(pid)
                if player_info:
                    players_summary.append({
                        "player_id": pid,
                        "name": player_info["name"]
                    })
                else:
                    players_summary.append({
                        "player_id": pid,
                        "name": None  # Should not happen unless data is inconsistent
                    })
            result.append({
                "match_id": match["match_id"],
                "status": match["status"],
                "players": players_summary
            })
        return {
            "success": True,
            "data": result
        }

    def list_player_matches(self, player_id: str) -> dict:
        """
        List all matches in which a particular player (by player_id) participates.

        Args:
            player_id (str): The ID of the target player.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of matches the player is in (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. player does not exist
            }

        Constraints:
            - The given player_id must exist in the player roster.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        matches = [
            match_info for match_info in self.matches.values()
            if player_id in match_info["players"]
        ]

        return { "success": True, "data": matches }

    def get_match_status(self, match_id: str) -> dict:
        """
        Retrieve the current status (scheduled, ongoing, completed, canceled) of a given match.

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict:
                success: True and data: status (str) if match exists.
                success: False and error message if match does not exist.

        Constraints:
            - match_id must exist in the system.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match does not exist"}
        return {"success": True, "data": match["status"]}

    def update_match_score(
        self,
        match_id: str,
        player_id: str,
        sets: list,
        games_in_current_set: int,
        points_in_current_game: int
    ) -> dict:
        """
        Modify the score (sets, games, points) for a player in a given match.
        Allowed only when match status is 'scheduled' or 'ongoing'.
        Args:
            match_id (str): The identifier of the match to update.
            player_id (str): The identifier of the player whose score is being updated.
            sets (List[int]): List of set scores for the player.
            games_in_current_set (int): Number of games won in the current set.
            points_in_current_game (int): Points in the current game.
        Returns:
            dict: {
                "success": True,
                "message": "Score updated for player X in match Y."
            } on success,
            or {
                "success": False,
                "error": "Reason for failure"
            }
        Constraints:
            - Match must exist.
            - Player must exist and be part of the match.
            - Match status must be 'scheduled' or 'ongoing'.
            - Only valid, basic type values for scores accepted.
        """
        # Check match existence
        match = self.matches.get(match_id)
        if match is None:
            return { "success": False, "error": "Match does not exist." }

        # Check player is in match and exists
        if player_id not in match["players"]:
            return { "success": False, "error": "Player not part of specified match." }
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist in roster." }

        # Status check
        if match["status"] not in ("scheduled", "ongoing"):
            return { "success": False, "error": "Can only update scores if match is 'scheduled' or 'ongoing'." }

        # Basic type/structure checking
        if not isinstance(sets, list) or not all(isinstance(s, int) and s >= 0 for s in sets):
            return { "success": False, "error": "'sets' must be a list of non-negative integers." }
        if not isinstance(games_in_current_set, int) or games_in_current_set < 0:
            return { "success": False, "error": "'games_in_current_set' must be a non-negative integer." }
        if not isinstance(points_in_current_game, int) or points_in_current_game < 0:
            return { "success": False, "error": "'points_in_current_game' must be a non-negative integer." }

        # Update scores (in both match and global scores table)
        score_info = match["scores"].get(player_id)
        if not score_info:
            return { "success": False, "error": "Score entry for player not found in match." }

        score_info["sets"] = sets
        score_info["games_in_current_set"] = games_in_current_set
        score_info["points_in_current_game"] = points_in_current_game

        # Also update in the global scores table
        if match_id in self.scores and player_id in self.scores[match_id]:
            self.scores[match_id][player_id]["sets"] = sets
            self.scores[match_id][player_id]["games_in_current_set"] = games_in_current_set
            self.scores[match_id][player_id]["points_in_current_game"] = points_in_current_game

        return { 
            "success": True, 
            "message": f"Score updated for player {player_id} in match {match_id}." 
        }


    def start_match(self, match_id: str) -> dict:
        """
        Change a match’s status from 'scheduled' to 'ongoing' and set its start_time.

        Args:
            match_id (str): Unique identifier of the match to start.

        Returns:
            dict: {
                "success": True,
                "message": "Match <match_id> started."
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - Match must exist in the system.
            - Match status must be 'scheduled'.
            - Sets start_time to the current time in ISO 8601 format.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match does not exist." }
        if match["status"] != "scheduled":
            return { "success": False, "error": "Can only start matches with status 'scheduled'." }
        now_iso = datetime.datetime.now().isoformat()
        match["status"] = "ongoing"
        match["start_time"] = now_iso
        self.matches[match_id] = match  # (Not strictly needed, but for clarity)
        return { "success": True, "message": f"Match {match_id} started." }


    def complete_match(self, match_id: str, end_time: Optional[str] = None) -> dict:
        """
        Mark the specified match as completed and set its end_time.

        Args:
            match_id (str): Unique identifier of the match to complete.
            end_time (Optional[str]): End time string (ISO or other consistent format). If None, uses current system time (ISO8601).

        Returns:
            dict:
                - On success: {"success": True, "message": "Match <match_id> marked as completed."}
                - On error: {"success": False, "error": <reason>}
    
        Constraints:
            - Match must exist.
            - Status must be 'ongoing' to complete the match.
            - Status set to 'completed', end_time set to provided value or now.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": f"Match with id '{match_id}' does not exist."}

        if match['status'] != 'ongoing':
            return {"success": False, "error": f"Cannot complete match '{match_id}': match is not ongoing."}

        # Determine end time
        if end_time is None:
            # Use current UTC time in ISO8601 format
            end_time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        else:
            end_time_str = end_time

        # Update match data
        match['status'] = 'completed'
        match['end_time'] = end_time_str
        self.matches[match_id] = match

        return {"success": True, "message": f"Match '{match_id}' marked as completed."}

    def cancel_match(self, match_id: str) -> dict:
        """
        Change the status of the given match to 'canceled', if permitted.

        Args:
            match_id (str): The unique identifier of the match to cancel.

        Returns:
            dict:
                - On success: {"success": True, "message": "Match <id> canceled."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - The match must exist.
            - Only matches with status 'scheduled' or 'ongoing' can be canceled.
            - Completed or already canceled matches cannot be changed to 'canceled'.
        """
        match = self.matches.get(match_id)
        if match is None:
            return {"success": False, "error": "Match does not exist."}

        if match["status"] not in ("scheduled", "ongoing"):
            return {
                "success": False, 
                "error": f"Cannot cancel a match with status '{match['status']}'."
            }

        match["status"] = "canceled"
        return {"success": True, "message": f"Match {match_id} canceled."}

    def create_match(self, match_id: str, player1_id: str, player2_id: str) -> dict:
        """
        Add a new match to the system with exactly two players.

        Args:
            match_id (str): Unique identifier for the match.
            player1_id (str): The player_id for the first player.
            player2_id (str): The player_id for the second player.

        Returns:
            dict: 
                - On success: {"success": True, "message": "..."}
                - On error: {"success": False, "error": "<reason>"}
    
        Constraints:
            - Both player1_id and player2_id must exist in the player roster.
            - Match_id must be unique.
            - The two players must be distinct.
            - Each match must have exactly two players.
        """
        if match_id in self.matches:
            return {"success": False, "error": "Match ID already exists"}

        if player1_id == player2_id:
            return {"success": False, "error": "A match must have two distinct players"}

        if player1_id not in self.players:
            return {"success": False, "error": f"Player with id {player1_id} does not exist"}
        if player2_id not in self.players:
            return {"success": False, "error": f"Player with id {player2_id} does not exist"}

        # Initialize scores for both players
        scores = {
            player1_id: {
                "match_id": match_id,
                "player_id": player1_id,
                "sets": [],
                "games_in_current_set": 0,
                "points_in_current_game": 0,
            },
            player2_id: {
                "match_id": match_id,
                "player_id": player2_id,
                "sets": [],
                "games_in_current_set": 0,
                "points_in_current_game": 0,
            }
        }

        # Create and store the match
        match_info = {
            "match_id": match_id,
            "players": [player1_id, player2_id],
            "scores": scores,
            "status": "scheduled",
            "start_time": None,
            "end_time": None
        }

        self.matches[match_id] = match_info
        self.scores[match_id] = scores

        return {"success": True, "message": f"Match created with id {match_id}"}

    def edit_match_players(self, match_id: str, new_players: list) -> dict:
        """
        Change the list of players in a match (only if status is 'scheduled').

        Args:
            match_id (str): Identifier for the match to edit.
            new_players (list of str): List of exactly two player_ids (must exist).

        Returns:
            dict: 
              On success: { "success": True, "message": "Players updated for match <match_id>." }
              On failure: { "success": False, "error": <reason> }

        Constraints:
            - Can only edit if match status is 'scheduled'.
            - Exactly two unique player_ids required; both must exist in the player roster.
            - Also updates scores accordingly (resets scores for new players).
        """
        # Check match exists
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": f"Match {match_id} does not exist." }

        # Check match is in 'scheduled' state
        if match["status"] != "scheduled":
            return { "success": False, "error": "Players can only be edited if match is 'scheduled'." }

        # Validate new_players: must be a list of two unique strings, both players must exist
        if (not isinstance(new_players, list) or 
            len(new_players) != 2 or 
            not all(isinstance(pid, str) for pid in new_players) or
            len(set(new_players)) != 2):
            return { "success": False, "error": "Exactly two unique player_ids required." }

        # Check each player exists
        for pid in new_players:
            if pid not in self.players:
                return { "success": False, "error": f"Player {pid} does not exist in roster." }

        # Update match players
        match["players"] = new_players

        # Re-initialize scores for the new players in self.matches[match_id]["scores"] and self.scores[match_id]
        match["scores"] = {}
        self.scores[match_id] = {}
        for pid in new_players:
            score_info = {
                "match_id": match_id,
                "player_id": pid,
                "sets": [],
                "games_in_current_set": 0,
                "points_in_current_game": 0
            }
            match["scores"][pid] = score_info
            self.scores[match_id][pid] = score_info

        return { "success": True, "message": f"Players updated for match {match_id}." }

    def add_player(self, player_id: str, name: str, ranking: int, nationality: str) -> dict:
        """
        Register a new player in the roster.

        Args:
            player_id (str): Unique identifier for the player.
            name (str): The player's name.
            ranking (int): The player's ranking (should be non-negative).
            nationality (str): The player's nationality.

        Returns:
            dict:
                - {"success": True, "message": "Player added successfully"}
                - {"success": False, "error": <error reason>}

        Constraints:
            - player_id must be unique (not already present in the roster).
            - ranking should be non-negative.
        """
        if player_id in self.players:
            return {"success": False, "error": "Player with this ID already exists"}
        if not isinstance(ranking, int) or ranking < 0:
            return {"success": False, "error": "Ranking must be a non-negative integer"}

        player_info: PlayerInfo = {
            "player_id": player_id,
            "name": name,
            "ranking": ranking,
            "nationality": nationality
        }
        self.players[player_id] = player_info
        return {"success": True, "message": "Player added successfully"}

    def update_player_info(
        self, 
        player_id: str, 
        name: str = None, 
        ranking: int = None, 
        nationality: str = None
    ) -> dict:
        """
        Edit the player attributes (name, ranking, nationality) for an existing player.

        Args:
            player_id (str): Unique id of the player to update.
            name (str, optional): New name for the player.
            ranking (int, optional): New ranking for the player.
            nationality (str, optional): New nationality for the player.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Player info updated successfully" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Player with player_id must exist in the roster.
            - At least one updatable field must be provided.
            - If ranking is given, it must be an int.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player does not exist." }

        updates = {}
        if name is not None:
            if not isinstance(name, str):
                return { "success": False, "error": "Name must be a string." }
            updates["name"] = name
        if ranking is not None:
            if not isinstance(ranking, int):
                return { "success": False, "error": "Ranking must be an integer." }
            updates["ranking"] = ranking
        if nationality is not None:
            if not isinstance(nationality, str):
                return { "success": False, "error": "Nationality must be a string." }
            updates["nationality"] = nationality

        if not updates:
            return { "success": False, "error": "No attributes provided to update." }

        for k, v in updates.items():
            player[k] = v

        self.players[player_id] = player
        return { "success": True, "message": "Player info updated successfully" }

    def remove_player_from_roster(self, player_id: str) -> dict:
        """
        Remove a player from the player roster if and only if the player is not referenced by any matches.

        Args:
            player_id (str): The unique identifier of the player to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Player <player_id> removed from roster" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Player must exist in roster.
            - Player must not participate in any match (scheduled, ongoing, completed, or canceled).
            - Does not remove/rewrite historical scores or modify matches.
        """
        # Check if player exists
        if player_id not in self.players:
            return {"success": False, "error": f"Player {player_id} does not exist in roster"}

        # Check if player is in any match as a participant
        for match in self.matches.values():
            if player_id in match.get("players", []):
                return {"success": False, 
                        "error": f"Player {player_id} is still referenced in matches and cannot be removed"}

        # Remove from player roster
        del self.players[player_id]
        return {"success": True, "message": f"Player {player_id} removed from roster"}


class TennisMatchTrackingSystem(BaseEnv):
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

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_player_by_name(self, **kwargs):
        return self._call_inner_tool('get_player_by_name', kwargs)

    def get_match_players(self, **kwargs):
        return self._call_inner_tool('get_match_players', kwargs)

    def get_match_scores(self, **kwargs):
        return self._call_inner_tool('get_match_scores', kwargs)

    def get_player_score_in_match(self, **kwargs):
        return self._call_inner_tool('get_player_score_in_match', kwargs)

    def list_all_matches(self, **kwargs):
        return self._call_inner_tool('list_all_matches', kwargs)

    def list_player_matches(self, **kwargs):
        return self._call_inner_tool('list_player_matches', kwargs)

    def get_match_status(self, **kwargs):
        return self._call_inner_tool('get_match_status', kwargs)

    def update_match_score(self, **kwargs):
        return self._call_inner_tool('update_match_score', kwargs)

    def start_match(self, **kwargs):
        return self._call_inner_tool('start_match', kwargs)

    def complete_match(self, **kwargs):
        return self._call_inner_tool('complete_match', kwargs)

    def cancel_match(self, **kwargs):
        return self._call_inner_tool('cancel_match', kwargs)

    def create_match(self, **kwargs):
        return self._call_inner_tool('create_match', kwargs)

    def edit_match_players(self, **kwargs):
        return self._call_inner_tool('edit_match_players', kwargs)

    def add_player(self, **kwargs):
        return self._call_inner_tool('add_player', kwargs)

    def update_player_info(self, **kwargs):
        return self._call_inner_tool('update_player_info', kwargs)

    def remove_player_from_roster(self, **kwargs):
        return self._call_inner_tool('remove_player_from_roster', kwargs)

