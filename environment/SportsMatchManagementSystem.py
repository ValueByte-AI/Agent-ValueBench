# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class MatchInfo(TypedDict):
    match_id: str
    date: str
    time: str
    location: str
    status: str
    team1_id: str
    team2_id: str
    score_team1: int
    score_team2: int
    statistics: Dict[str, Any]  # Maps team/player IDs to stats; structure may vary
    outcome: str

class TeamInfo(TypedDict):
    team_id: str
    name: str
    roster: List[str]  # List of player_ids
    coach: str
    league: str

class PlayerInfo(TypedDict):
    player_id: str
    name: str
    team_id: str
    position: str
    stats: Dict[str, Any]  # Player statistics

class _GeneratedEnvImpl:
    def __init__(self):
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Constraints:
        # - Each match must have two teams (team1_id ≠ team2_id).
        # - Scores and outcomes can only be set for matches with status = "completed".
        # - Match identifiers (match_id) are unique.
        # - Teams and players referenced in matches must exist.
        # - Statistics for a match must correspond to the participating teams and players.

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve all available details of a match, given its match_id.

        Args:
            match_id (str): Unique identifier for the match.

        Returns:
            dict: {
                "success": True,
                "data": MatchInfo  # The full match record
            }
            or
            {
                "success": False,
                "error": str  # "Match not found"
            }

        Constraints:
            - match_id must exist in the system.
        """
        match = self.matches.get(match_id)
        if match is None:
            return {"success": False, "error": "Match not found"}
        return {"success": True, "data": match}

    def get_match_score_and_outcome(self, match_id: str) -> dict:
        """
        Retrieve both teams’ scores and the match outcome for a given match_id.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "score_team1": int,
                            "score_team2": int,
                            "outcome": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str   # Reason for failure
                    }

        Constraints:
            - The match_id must exist in the system.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }

        result = {
            "score_team1": match["score_team1"],
            "score_team2": match["score_team2"],
            "outcome": match["outcome"]
        }
        return { "success": True, "data": result }

    def get_match_statistics(self, match_id: str) -> dict:
        """
        Retrieve the statistics dictionary for the match with the specified match_id.

        Args:
            match_id (str): Unique identifier for the match.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Any]  # The match statistics (may be empty dict if not yet set)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. match does not exist
            }
        Constraints:
            - match_id must exist in the system.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match does not exist" }
        return { "success": True, "data": match["statistics"] }

    def list_matches_by_status(self, status: str) -> dict:
        """
        Retrieve a list of matches filtered by their status.

        Args:
            status (str): The desired match status to filter by (e.g., "scheduled", "completed").

        Returns:
            dict:
                - success (bool): True if the operation is completed.
                - data (List[MatchInfo]): List of match info dicts where match['status'] == status.
            or
            dict:
                - success (bool): False for errors.
                - error (str): Error message.

        Constraints:
            - Returns an empty list if no matches have the provided status.
        """
        if not isinstance(status, str) or not status:
            return { "success": False, "error": "A valid match status string must be provided." }

        filtered_matches = [
            match_info for match_info in self.matches.values()
            if match_info.get("status") == status
        ]
        return { "success": True, "data": filtered_matches }

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve team details (name, roster, coach, league) given a team_id.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo  # All details for the team,
            }
            or
            {
                "success": False,
                "error": "Team not found"
            }

        Constraints:
            - The team_id must exist in the system.
        """
        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": "Team not found"}
        return {"success": True, "data": team}

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve player details and personal statistics for a given player_id.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict: 
                If player exists:
                    {
                        "success": True,
                        "data": PlayerInfo  # Player's details and statistics
                    }
                If player does not exist:
                    {
                        "success": False,
                        "error": "Player not found"
                    }
        Constraints:
            - player_id must exist in the system.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player not found" }
        return { "success": True, "data": player }

    def list_team_roster(self, team_id: str) -> dict:
        """
        List all players (player_id and name) belonging to the specified team.

        Args:
            team_id (str): Unique identifier of the team.

        Returns:
            dict:
                success: True/False
                data: list of dicts with 'player_id' and 'name' keys if successful
                error: error message string if not successful

        Constraints:
            - Specified team_id must exist.
            - Only players listed in the team's roster and present in the system will be returned.
        """
        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": "Team does not exist"}

        result = []
        for pid in team.get("roster", []):
            player = self.players.get(pid)
            if player:
                result.append({"player_id": pid, "name": player["name"]})
            # If player_id does not exist in system, skip it.

        return {"success": True, "data": result}

    def list_all_matches(self) -> dict:
        """
        Retrieve the full list of matches with their IDs and basic information.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict contains: match_id, date, time, location, status, team1_id, team2_id
            }

        If there are no matches, the data list is empty.

        Constraints:
            - None specific to operation beyond existing state.
        """
        matches_basic_info = [
            {
                "match_id": m["match_id"],
                "date": m["date"],
                "time": m["time"],
                "location": m["location"],
                "status": m["status"],
                "team1_id": m["team1_id"],
                "team2_id": m["team2_id"]
            }
            for m in self.matches.values()
        ]
        return { "success": True, "data": matches_basic_info }

    def list_matches_by_team(self, team_id: str) -> dict:
        """
        Retrieve all matches in which the specified team has participated.

        Args:
            team_id (str): Unique identifier for the team.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[MatchInfo], # each MatchInfo is a match the team played
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # "Team does not exist"
                    }

        Constraints:
            - The given team_id must exist in the system.
            - If no matches found for the team, returns an empty list.
        """
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        matches = [
            match
            for match in self.matches.values()
            if match["team1_id"] == team_id or match["team2_id"] == team_id
        ]
        return {"success": True, "data": matches}

    def create_match(
        self, 
        match_id: str, 
        date: str,
        time: str,
        location: str,
        status: str,
        team1_id: str,
        team2_id: str,
        score_team1: int = 0,
        score_team2: int = 0,
        statistics: Dict[str, Any] = None,
        outcome: str = ""
    ) -> dict:
        """
        Add a new match to the system.

        Args:
            match_id (str): Unique identifier for the match.
            date (str): Match date.
            time (str): Match time.
            location (str): Match location.
            status (str): Initial match status ('scheduled', 'completed', 'ongoing', etc.).
            team1_id (str): First team's ID.
            team2_id (str): Second team's ID.
            score_team1 (int, optional): Initial score for team1 (default 0).
            score_team2 (int, optional): Initial score for team2 (default 0).
            statistics (Dict[str, Any], optional): Initial statistics dictionary.
            outcome (str, optional): Initial match outcome, default empty.

        Returns:
            dict: 
            - On success: { "success": True, "message": "Match <match_id> created successfully." }
            - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - match_id must be unique.
            - team1_id and team2_id must exist and be different.
        """
        # Validate match_id uniqueness
        if match_id in self.matches:
            return {"success": False, "error": "A match with this match_id already exists."}
    
        # Validate teams exist
        if team1_id not in self.teams:
            return {"success": False, "error": f"Team1 with ID {team1_id} does not exist."}
        if team2_id not in self.teams:
            return {"success": False, "error": f"Team2 with ID {team2_id} does not exist."}
    
        # Validate teams are different
        if team1_id == team2_id:
            return {"success": False, "error": "A match must have two distinct teams (team1_id ≠ team2_id)."}

        # Default statistics
        if statistics is None:
            statistics = {}

        new_match: MatchInfo = {
            "match_id": match_id,
            "date": date,
            "time": time,
            "location": location,
            "status": status,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "score_team1": score_team1,
            "score_team2": score_team2,
            "statistics": statistics,
            "outcome": outcome,
        }

        self.matches[match_id] = new_match

        return {"success": True, "message": f"Match {match_id} created successfully."}

    def update_match_score_and_outcome(
        self,
        match_id: str,
        score_team1: int,
        score_team2: int,
        outcome: str
    ) -> dict:
        """
        Set or update the scores and outcome for a match (only if status is "completed").

        Args:
            match_id (str): Unique identifier for the match to be updated.
            score_team1 (int): New score for team 1.
            score_team2 (int): New score for team 2.
            outcome (str): The outcome of the match (e.g. "draw", "team1_win", "team2_win", etc.).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Scores and outcome updated for match <match_id>."
                }
                On failure: {
                    "success": False,
                    "error": <error reason>
                }

        Constraints:
            - Can only update if match exists and status is "completed".
        """
        match = self.matches.get(match_id)
        if match is None:
            return { "success": False, "error": "Match does not exist." }

        if match["status"] != "completed":
            return { "success": False, "error": "Cannot update score/outcome for a match that is not completed." }

        match["score_team1"] = score_team1
        match["score_team2"] = score_team2
        match["outcome"] = outcome

        return {
            "success": True,
            "message": f"Scores and outcome updated for match {match_id}."
        }

    def update_match_status(self, match_id: str, status: str) -> dict:
        """
        Change the status (e.g., scheduled, completed) of a match.

        Args:
            match_id (str): The unique ID of the match to update.
            status (str): The new status to set for the match.

        Returns:
            dict: {
                "success": True,
                "message": "Match status updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The match_id must exist in the system.
            - No explicit validation on status values, unless status vocabulary is predefined.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match ID not found."}

        self.matches[match_id]['status'] = status
        return {"success": True, "message": "Match status updated successfully."}

    def update_match_statistics(self, match_id: str, statistics: Dict[str, Any]) -> dict:
        """
        Update the statistics dictionary for a match, ensuring that all IDs referenced are valid teams/players
        participating in this match.

        Args:
            match_id (str): Identifier for the match to update.
            statistics (Dict[str, Any]): The new statistics data. Can map to team or player IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Match statistics updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - match_id must exist.
            - Statistics' keys (team/player ids) must be present and relevant,
              i.e., teams must be team1_id/team2_id of match; players must be in those teams' rosters.
        """
        # Check match existence
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match ID does not exist."}

        team1_id = match["team1_id"]
        team2_id = match["team2_id"]
        # Ensure both teams exist
        team1 = self.teams.get(team1_id)
        team2 = self.teams.get(team2_id)
        if not team1 or not team2:
            return {"success": False, "error": "Teams in match do not exist."}

        valid_team_ids = {team1_id, team2_id}
        # Rostered players for both teams
        valid_player_ids = set(team1["roster"]) | set(team2["roster"])

        def validate_refs(value):
            if isinstance(value, dict):
                if "team_id" in value:
                    team_ref = value["team_id"]
                    if team_ref not in valid_team_ids:
                        return f"Statistics reference invalid team_id '{team_ref}'."
                if "player_id" in value:
                    player_ref = value["player_id"]
                    if player_ref not in valid_player_ids or player_ref not in self.players:
                        return f"Statistics reference invalid player_id '{player_ref}'."
                for nested in value.values():
                    error = validate_refs(nested)
                    if error:
                        return error
            elif isinstance(value, list):
                for nested in value:
                    error = validate_refs(nested)
                    if error:
                        return error
            return None

        error = validate_refs(statistics)
        if error:
            return {"success": False, "error": error}

        # All references valid; perform update
        self.matches[match_id]["statistics"] = statistics

        return {"success": True, "message": "Match statistics updated."}

    def create_team(self, team_id: str, name: str, roster: list, coach: str, league: str) -> dict:
        """
        Add a new team to the system.

        Args:
            team_id (str): Unique identifier for the team.
            name (str): Team name.
            roster (List[str]): List of player_ids to place in the team's roster. All player_ids must exist.
            coach (str): Name of team's coach.
            league (str): Name of the league.

        Returns:
            dict: {
                "success": True,
                "message": "Team <team_id> created successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - team_id must be unique.
            - All player_ids in roster must exist in the system.
        """
        if team_id in self.teams:
            return {"success": False, "error": f"Team with id '{team_id}' already exists."}

        if not isinstance(roster, list):
            return {"success": False, "error": "Roster must be a list of player_ids."}

        invalid_players = [pid for pid in roster if pid not in self.players]
        if invalid_players:
            return {
                "success": False,
                "error": f"Roster includes non-existent player_ids: {invalid_players}"
            }

        team_info: TeamInfo = {
            "team_id": team_id,
            "name": name,
            "roster": roster,
            "coach": coach,
            "league": league
        }
        self.teams[team_id] = team_info
        return {"success": True, "message": f"Team '{team_id}' created successfully"}

    def update_team(
        self,
        team_id: str,
        name: str = None,
        roster: List[str] = None,
        coach: str = None,
        league: str = None
    ) -> dict:
        """
        Modify team details: name, roster (player IDs), coach, league.

        Args:
            team_id (str): The unique identifier for the team to update.
            name (str, optional): New name for the team.
            roster (List[str], optional): The updated player ID list for the team.
            coach (str, optional): Updated coach name.
            league (str, optional): Updated league name.

        Returns:
            dict: {
                "success": True,
                "message": "Team details updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The team must exist.
            - If roster is provided, all player_ids must exist.
            - Updates players' 'team_id' field if roster is changed.
        """
        # Check if team exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}

        team = self.teams[team_id]

        # Track if any updates provided
        updated = False

        if name is not None:
            team["name"] = name
            updated = True

        if coach is not None:
            team["coach"] = coach
            updated = True

        if league is not None:
            team["league"] = league
            updated = True

        if roster is not None:
            # Validate roster player_ids
            missing_players = [pid for pid in roster if pid not in self.players]
            if missing_players:
                return {
                    "success": False,
                    "error": f"The following player_ids do not exist: {missing_players}"
                }
            # Remove team assignment from players no longer in the roster
            prev_roster = set(team["roster"])
            new_roster = set(roster)
            remove_from_team = prev_roster - new_roster
            add_to_team = new_roster - prev_roster
            for pid in remove_from_team:
                if pid in self.players and self.players[pid]["team_id"] == team_id:
                    self.players[pid]["team_id"] = ""
            for pid in add_to_team:
                self.players[pid]["team_id"] = team_id
            # Set new roster
            team["roster"] = list(roster)
            updated = True

        if not updated:
            return {
                "success": False,
                "error": "No updates provided. Supply at least one field to update."
            }

        self.teams[team_id] = team
        return {
            "success": True,
            "message": "Team details updated successfully."
        }

    def create_player(
        self,
        player_id: str,
        name: str,
        team_id: str,
        position: str,
        stats: dict = None,
    ) -> dict:
        """
        Add a new player to the system and assign to a team.

        Args:
            player_id (str): Unique player identifier.
            name (str): Name of the player.
            team_id (str): Identifier of the team to which the player will be assigned.
            position (str): Player's position.
            stats (dict, optional): Initial statistics for the player. Defaults to empty dict.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> created and added to team <team_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints/rules enforced:
            - player_id must be unique.
            - team_id must exist.
            - Upon creation, player's ID will be appended to the team's roster.
        """

        if player_id in self.players:
            return {"success": False, "error": "Player ID already exists"}

        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        if not name or not position:
            return {"success": False, "error": "Player name and position must be provided"}

        if stats is None:
            stats = {}

        # Create PlayerInfo object
        player_info: PlayerInfo = {
            "player_id": player_id,
            "name": name,
            "team_id": team_id,
            "position": position,
            "stats": stats
        }

        # Add player to system
        self.players[player_id] = player_info
        # Append player_id to team roster
        if player_id not in self.teams[team_id]["roster"]:
            self.teams[team_id]["roster"].append(player_id)

        return {
            "success": True,
            "message": f"Player {player_id} created and added to team {team_id}"
        }

    def update_player_stats(self, player_id: str, stats: Dict[str, Any]) -> dict:
        """
        Update the statistics associated with an individual player.

        Args:
            player_id (str): The unique identifier of the player whose stats are to be updated.
            stats (Dict[str, Any]): The new statistics to update for the player.

        Returns:
            dict: {
                "success": True,
                "message": "Player statistics updated."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - The player with the given player_id must exist in the system.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist." }

        self.players[player_id]['stats'] = stats
        return { "success": True, "message": "Player statistics updated." }

    def delete_match(self, match_id: str) -> dict:
        """
        Remove a match from the system by its match_id (admin-level action).

        Args:
            match_id (str): Unique identifier of the match to remove.

        Returns:
            dict: 
                On success: {"success": True, "message": "Match <match_id> deleted successfully"}
                On failure: {"success": False, "error": "Match ID does not exist"}

        Constraints:
            - The match must exist in the system.
            - Cascading clean-up is triggered, but in current model, this just means deleting the match record.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match ID does not exist"}

        del self.matches[match_id]
        return {"success": True, "message": f"Match {match_id} deleted successfully"}

    def delete_team(self, team_id: str) -> dict:
        """
        Remove a team from the system by its team_id, if and only if:
          - it exists,
          - it is not referenced in any match (as team1_id or team2_id),
          - it has no players on its roster.

        Args:
            team_id (str): The ID of the team to delete.

        Returns:
            dict: { "success": True, "message": "Team <team_id> deleted." }
                  or { "success": False, "error": <reason> }

        Constraints:
            - Cannot delete a team that is referenced in any match.
            - Cannot delete a team that still has players in its roster.
        """
        # Check existence
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}

        # Check if referenced in any match
        for match in self.matches.values():
            if match["team1_id"] == team_id or match["team2_id"] == team_id:
                return {
                    "success": False,
                    "error": f"Team {team_id} is referenced in match {match['match_id']}."
                }

        # Check if there are any players still on the team
        for player in self.players.values():
            if player["team_id"] == team_id:
                return {
                    "success": False,
                    "error": f"Team {team_id} cannot be deleted because it still has players."
                }

        # All checks passed, safe to delete
        del self.teams[team_id]
        return {
            "success": True,
            "message": f"Team {team_id} deleted."
        }

    def delete_player(self, player_id: str) -> dict:
        """
        Remove a player from the system. This operation:
          - Deletes the player from self.players.
          - Removes the player from any team roster they are a part of.
          - Removes any references to the player in all matches' statistics.
    
        Args:
            player_id (str): The unique identifier of the player to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> deleted successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The player must exist in the system.
            - All references to the player in team rosters and match statistics are removed as part of cascade delete.
        """
        # Check if player exists
        if player_id not in self.players:
            return {"success": False, "error": f"Player '{player_id}' does not exist"}

        # Remove player from all team rosters
        for team in self.teams.values():
            if player_id in team["roster"]:
                team["roster"].remove(player_id)

        def remove_player_refs(value):
            if isinstance(value, dict):
                cleaned = {}
                for key, nested in value.items():
                    if key == "player_id" and nested == player_id:
                        return None
                    cleaned_nested = remove_player_refs(nested)
                    if cleaned_nested is not None:
                        cleaned[key] = cleaned_nested
                return cleaned
            if isinstance(value, list):
                cleaned_list = []
                for nested in value:
                    cleaned_nested = remove_player_refs(nested)
                    if cleaned_nested is not None:
                        cleaned_list.append(cleaned_nested)
                return cleaned_list
            return value

        # Remove the player's statistics from all matches
        for match in self.matches.values():
            if "statistics" in match and isinstance(match["statistics"], dict):
                if player_id in match["statistics"]:
                    del match["statistics"][player_id]
                match["statistics"] = remove_player_refs(match["statistics"])

        # Delete the player object
        del self.players[player_id]

        return {
            "success": True,
            "message": f"Player '{player_id}' deleted successfully"
        }


class SportsMatchManagementSystem(BaseEnv):
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

    def get_match_score_and_outcome(self, **kwargs):
        return self._call_inner_tool('get_match_score_and_outcome', kwargs)

    def get_match_statistics(self, **kwargs):
        return self._call_inner_tool('get_match_statistics', kwargs)

    def list_matches_by_status(self, **kwargs):
        return self._call_inner_tool('list_matches_by_status', kwargs)

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def list_team_roster(self, **kwargs):
        return self._call_inner_tool('list_team_roster', kwargs)

    def list_all_matches(self, **kwargs):
        return self._call_inner_tool('list_all_matches', kwargs)

    def list_matches_by_team(self, **kwargs):
        return self._call_inner_tool('list_matches_by_team', kwargs)

    def create_match(self, **kwargs):
        return self._call_inner_tool('create_match', kwargs)

    def update_match_score_and_outcome(self, **kwargs):
        return self._call_inner_tool('update_match_score_and_outcome', kwargs)

    def update_match_status(self, **kwargs):
        return self._call_inner_tool('update_match_status', kwargs)

    def update_match_statistics(self, **kwargs):
        return self._call_inner_tool('update_match_statistics', kwargs)

    def create_team(self, **kwargs):
        return self._call_inner_tool('create_team', kwargs)

    def update_team(self, **kwargs):
        return self._call_inner_tool('update_team', kwargs)

    def create_player(self, **kwargs):
        return self._call_inner_tool('create_player', kwargs)

    def update_player_stats(self, **kwargs):
        return self._call_inner_tool('update_player_stats', kwargs)

    def delete_match(self, **kwargs):
        return self._call_inner_tool('delete_match', kwargs)

    def delete_team(self, **kwargs):
        return self._call_inner_tool('delete_team', kwargs)

    def delete_player(self, **kwargs):
        return self._call_inner_tool('delete_player', kwargs)
