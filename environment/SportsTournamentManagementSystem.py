# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict



class PlayerInfo(TypedDict):
    player_id: str
    name: str
    team_id: str
    profile_detail: str

class TournamentInfo(TypedDict):
    tournament_id: str
    name: str
    structure: str
    location: str

class SeasonInfo(TypedDict):
    season_id: str
    year: int
    tournament_id: str

class PlayerStatisticsInfo(TypedDict):
    player_id: str
    tournament_id: str
    season_id: str
    stat_type: str
    stat_val: float

class TeamInfo(TypedDict, total=False):  # optional (for extensibility)
    team_id: str
    team_name: str
    players: List[str]  # list of player_ids

class _GeneratedEnvImpl:
    def __init__(self):
        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Tournaments: {tournament_id: TournamentInfo}
        self.tournaments: Dict[str, TournamentInfo] = {}

        # Seasons: {season_id: SeasonInfo}
        self.seasons: Dict[str, SeasonInfo] = {}

        # PlayerStatistics: List of records, each stats entry links to player/tournament/season
        self.player_statistics: List[PlayerStatisticsInfo] = []

        # Teams (optional, for extensibility): {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # -- Constraints (to enforce in business logic) --
        # 1. Each PlayerStatistics record must reference a valid player, tournament, and season.
        # 2. Season must be associated with a specific tournament.
        # 3. Players can participate in multiple tournaments and seasons.
        # 4. Statistical data for players is segregated by tournament and season.
        # 5. Requests for statistics must specify player_id, tournament_id, and season_id for accurate retrieval.

    def _remove_player_from_current_team(self, player_id: str) -> None:
        player = self.players.get(player_id)
        if not player:
            return
        old_team_id = player.get("team_id")
        if not old_team_id or old_team_id not in self.teams:
            return
        team_players = self.teams[old_team_id].setdefault("players", [])
        if player_id in team_players:
            team_players.remove(player_id)

    def _assign_player_to_team(self, player_id: str, team_id: str) -> None:
        player = self.players.get(player_id)
        if not player:
            return
        self._remove_player_from_current_team(player_id)
        player["team_id"] = team_id
        if team_id and team_id in self.teams:
            team_players = self.teams[team_id].setdefault("players", [])
            if player_id not in team_players:
                team_players.append(player_id)

    def get_player_info(self, player_id: str) -> dict:
        """
        Retrieve a player's profile/details by player_id.

        Args:
            player_id (str): Unique identifier of the player.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": PlayerInfo  # Player's information
                }
                OR
                {
                    "success": False,
                    "error": str  # Error reason, e.g., player not found
                }
        Constraints:
            - The specified player_id must exist in the system.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        return { "success": True, "data": self.players[player_id] }

    def get_tournament_info(self, tournament_id: str) -> dict:
        """
        Retrieve details of a tournament by its tournament_id.

        Args:
            tournament_id (str): The unique identifier for the tournament.

        Returns:
            dict: {
                "success": True,
                "data": TournamentInfo,  # Tournament's details on success
            }
            or
            {
                "success": False,
                "error": str  # Error message if tournament not found
            }

        Constraints:
            - Tournament ID must exist in the system.
        """
        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament not found" }

        return {
            "success": True,
            "data": self.tournaments[tournament_id]
        }

    def get_season_info(self, season_id: str) -> dict:
        """
        Retrieve information about a season by its season_id.

        Args:
            season_id (str): The unique identifier for the season.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SeasonInfo
                    }
                On failure (season not found):
                    {
                        "success": False,
                        "error": "Season not found"
                    }

        Constraints:
            - The season_id must exist in the system.
        """
        if season_id not in self.seasons:
            return { "success": False, "error": "Season not found" }
        return { "success": True, "data": self.seasons[season_id] }

    def list_player_statistics(
        self,
        player_id: str,
        tournament_id: str = None,
        season_id: str = None
    ) -> dict:
        """
        List all PlayerStatistics records for a specific player.
        Optionally filter by tournament_id and/or season_id.

        Args:
            player_id (str): The player's unique identifier. Required.
            tournament_id (str, optional): Tournament to filter by. Defaults to None.
            season_id (str, optional): Season to filter by. Defaults to None.

        Returns:
            dict: 
              - On success: { "success": True, "data": List[PlayerStatisticsInfo] }
              - On failure (invalid player): { "success": False, "error": str }

        Constraints:
          - The player_id must exist in the system.
          - Records are filtered first by player_id, then further by tournament_id and/or season_id if those are provided.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        stats = [
            stat for stat in self.player_statistics
            if stat["player_id"] == player_id
            and (tournament_id is None or stat["tournament_id"] == tournament_id)
            and (season_id is None or stat["season_id"] == season_id)
        ]
        return { "success": True, "data": stats }

    def get_player_statistics(
        self, 
        player_id: str, 
        tournament_id: str, 
        season_id: str
    ) -> dict:
        """
        Retrieve all statistics entries for a player in a specific tournament and season.

        Args:
            player_id (str): ID of the player.
            tournament_id (str): ID of the tournament.
            season_id (str): ID of the season.

        Returns:
            dict:
                - On Success: {
                      "success": True,
                      "data": List[PlayerStatisticsInfo]
                  }
                - On Failure: {
                      "success": False,
                      "error": str
                  }
        Constraints:
            - player_id must exist in the players registry.
            - tournament_id must exist in the tournaments registry.
            - season_id must exist in the seasons registry.
            - The season must be associated with the tournament.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        season = self.seasons[season_id]
        if season["tournament_id"] != tournament_id:
            return {"success": False, "error": "Season is not associated with the provided tournament"}

        stats = [
            stat for stat in self.player_statistics
            if stat["player_id"] == player_id 
            and stat["tournament_id"] == tournament_id 
            and stat["season_id"] == season_id
        ]

        return {"success": True, "data": stats}

    def list_tournaments_by_player(self, player_id: str) -> dict:
        """
        Get all tournaments (with metadata) in which a given player has participated.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": List[TournamentInfo],  # List of tournaments (no duplicates)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., unknown player_id
            }

        Constraints:
            - The player must exist (`player_id` in self.players).
            - Only tournaments present in the system are returned.
            - Each tournament is listed once, even if player has stats in multiple seasons.

        Notes:
            - If the player has no tournament participation, returns empty list.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        # Gather unique tournament_ids where given player has PlayerStatistics
        tournament_ids = set(
            stat["tournament_id"]
            for stat in self.player_statistics
            if stat["player_id"] == player_id and stat["tournament_id"] in self.tournaments
        )

        result = [self.tournaments[tid] for tid in tournament_ids]
        return {"success": True, "data": result}

    def list_seasons_by_tournament(self, tournament_id: str) -> dict:
        """
        List all seasons (SeasonInfo) associated with a particular tournament.

        Args:
            tournament_id (str): The tournament's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[SeasonInfo],  # List of SeasonInfo for matched seasons (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. tournament does not exist)
            }

        Constraints:
            - The tournament_id must correspond to an existing tournament.
            - Only seasons with matching tournament_id will be listed.
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        matched_seasons = [
            season for season in self.seasons.values()
            if season["tournament_id"] == tournament_id
        ]

        return {"success": True, "data": matched_seasons}

    def list_players_by_team(self, team_id: str) -> dict:
        """
        List all players for a specified team_id.

        Args:
            team_id (str): The ID of the team to query.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo],  # List of PlayerInfo dicts for players on the team
            }
            or
            {
                "success": False,
                "error": str  # e.g. 'Team does not exist'
            }

        Constraints:
            - The specified team_id must exist.
            - Player-team association is determined via the PlayerInfo 'team_id' field.
            - Returns an empty list if the team exists but has no players assigned.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        result = [player_info for player_info in self.players.values() if player_info["team_id"] == team_id]

        return { "success": True, "data": result }

    def get_team_info(self, team_id: str) -> dict:
        """
        Retrieve team information by team_id.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict:
                {
                    "success": True,
                    "data": TeamInfo  # team information dictionary, if found
                }
                or
                {
                    "success": False,
                    "error": str  # error message, e.g., "Team not found"
                }

        Constraints:
            - Team must exist in the system (self.teams).
            - No permissions or reference checks required.
        """
        team_info = self.teams.get(team_id)
        if team_info is None:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team_info }

    def validate_player_statistic_references(
        self,
        player_id: str,
        tournament_id: str,
        season_id: str
    ) -> dict:
        """
        Check that the given PlayerStatistics references exist:
        - player_id is in players
        - tournament_id is in tournaments
        - season_id is in seasons

        Args:
            player_id (str): Player identifier to check.
            tournament_id (str): Tournament identifier to check.
            season_id (str): Season identifier to check.

        Returns:
            dict: If all exist:
                {
                  "success": True,
                  "data": {
                      "player": True,
                      "tournament": True,
                      "season": True
                  }
                }
            If any are missing:
                {
                  "success": False,
                  "error": {
                      "player": bool,
                      "tournament": bool,
                      "season": bool
                  }
                }

        Constraints:
            - IDs must reference existing entities for valid PlayerStatistics.
        """
        exists = {
            "player": player_id in self.players,
            "tournament": tournament_id in self.tournaments,
            "season": season_id in self.seasons
        }
        if all(exists.values()):
            return { "success": True, "data": exists }
        else:
            return { "success": False, "error": exists }

    def add_player_statistic(
        self,
        player_id: str,
        tournament_id: str,
        season_id: str,
        stat_type: str,
        stat_val: float
    ) -> dict:
        """
        Insert a new PlayerStatistics record for a player in a specified tournament and season, after validating all references.

        Args:
            player_id (str): ID of the player.
            tournament_id (str): ID of the tournament.
            season_id (str): ID of the season.
            stat_type (str): The type of statistic (e.g., "goals", "assists").
            stat_val (float): The value of the statistic.

        Returns:
            dict:
                { "success": True, "message": "Player statistic added." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - player_id must exist in self.players.
            - tournament_id must exist in self.tournaments.
            - season_id must exist in self.seasons AND be associated with tournament_id.
            - stat_val must be a number (float or int).
        """
        # Validate player
        if player_id not in self.players:
            return {"success": False, "error": "Invalid player_id: player does not exist."}
        # Validate tournament
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Invalid tournament_id: tournament does not exist."}
        # Validate season
        if season_id not in self.seasons:
            return {"success": False, "error": "Invalid season_id: season does not exist."}
        # Check that season is associated with the given tournament
        season_info = self.seasons[season_id]
        if season_info["tournament_id"] != tournament_id:
            return {"success": False, "error": "Season is not associated with the given tournament."}
        # Validate stat_val is a number
        if not isinstance(stat_val, (int, float)):
            return {"success": False, "error": "stat_val must be a numeric type."}

        # Add the statistic
        stat_record: PlayerStatisticsInfo = {
            "player_id": player_id,
            "tournament_id": tournament_id,
            "season_id": season_id,
            "stat_type": stat_type,
            "stat_val": float(stat_val)
        }
        self.player_statistics.append(stat_record)
        return {"success": True, "message": "Player statistic added."}

    def update_player_statistic(
        self,
        player_id: str,
        tournament_id: str,
        season_id: str,
        stat_type: str,
        stat_val: float
    ) -> dict:
        """
        Modify an existing PlayerStatistics record's stat_val by specifying
        player_id, tournament_id, season_id, and stat_type.

        Args:
            player_id (str): ID of the player.
            tournament_id (str): ID of the tournament.
            season_id (str): ID of the season.
            stat_type (str): Type of statistic to update.
            stat_val (float): The new statistic value.

        Returns:
            dict: {
                "success": True,
                "message": "Player statistic updated successfully"
            }
            or
            {
                "success": False,
                "error": "PlayerStatistics record not found"
            }

        Constraints:
            - Only updates if the record exists. Does not create new entries.
            - The specified record must exactly match all provided keys.
        """
        for stats in self.player_statistics:
            if (
                stats["player_id"] == player_id and
                stats["tournament_id"] == tournament_id and
                stats["season_id"] == season_id and
                stats["stat_type"] == stat_type
            ):
                stats["stat_val"] = stat_val
                return { "success": True, "message": "Player statistic updated successfully" }

        return { "success": False, "error": "PlayerStatistics record not found" }

    def delete_player_statistic(
        self,
        player_id: str,
        tournament_id: str,
        season_id: str,
        stat_type: str
    ) -> dict:
        """
        Remove a PlayerStatistics record for a player in a particular tournament/season/stat_type.

        Args:
            player_id (str): The player's unique identifier.
            tournament_id (str): The tournament's unique identifier.
            season_id (str): The season's unique identifier.
            stat_type (str): The type of statistic to remove.

        Returns:
            dict:
                On success: {"success": True, "message": "Player statistic removed."}
                On failure: {"success": False, "error": "Player statistic not found."}

        Constraints:
            - The statistic is identified by (player_id, tournament_id, season_id, stat_type).
            - No exception is raised on not found; a proper message is returned.
        """
        found = False
        # Search for the record's index
        for idx, stat in enumerate(self.player_statistics):
            if (stat['player_id'] == player_id and
                stat['tournament_id'] == tournament_id and
                stat['season_id'] == season_id and
                stat['stat_type'] == stat_type):
                # found, delete it
                del self.player_statistics[idx]
                found = True
                break
    
        if found:
            return {"success": True, "message": "Player statistic removed."}
        else:
            return {"success": False, "error": "Player statistic not found."}

    def add_player(
        self,
        player_id: str,
        name: str,
        team_id: str,
        profile_detail: str
    ) -> dict:
        """
        Add a new player profile to the system.

        Args:
            player_id (str): Unique identifier for the new player.
            name (str): Name of the player.
            team_id (str): Associated team identifier (can be empty or None if not assigned).
            profile_detail (str): Additional profile details as string.

        Returns:
            dict: {
                "success": True,
                "message": "Player added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - player_id must be unique (no duplicate).
            - If team_id is provided and teams module is active, optionally check team exists.
        """
        # Uniqueness constraint
        if player_id in self.players:
            return {"success": False, "error": "Player ID already exists."}

        # [Optional: Check that team_id exists if teams are enforced]
        # If you want to strictly check teams and team_id is not blank/null:
        if team_id and self.teams and team_id not in self.teams:
            return {"success": False, "error": f"Team ID '{team_id}' does not exist."}

        self.players[player_id] = {
            "player_id": player_id,
            "name": name,
            "team_id": team_id,
            "profile_detail": profile_detail,
        }
        if team_id:
            team_players = self.teams[team_id].setdefault("players", [])
            if player_id not in team_players:
                team_players.append(player_id)
        return {"success": True, "message": "Player added successfully."}

    def update_player_info(self, player_id: str, name: str = None, team_id: str = None, profile_detail: str = None) -> dict:
        """
        Modify fields in a player's profile.

        Args:
            player_id (str): Identifier for the player whose profile will be updated.
            name (str, optional): New name for the player.
            team_id (str, optional): Updated team ID for the player.
            profile_detail (str, optional): Updated profile detail string.

        Returns:
            dict: {
                "success": True,
                "message": "Player profile updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., player not found, no fields provided)
            }

        Constraints:
            - player_id must exist in the system.
            - No fields (other than player_id) results in failure.
            - Only valid fields (name, team_id, profile_detail) may be updated.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if team_id is not None:
            current_team_id = self.players[player_id].get("team_id")
            # Allow callers to preserve an existing team reference even if the
            # backing team registry is absent from the current state.
            if team_id and team_id not in self.teams and team_id != current_team_id:
                return { "success": False, "error": "Team not found" }
            update_fields["team_id"] = team_id
        if profile_detail is not None:
            update_fields["profile_detail"] = profile_detail

        if not update_fields:
            return { "success": False, "error": "No fields provided for update" }

        # Perform update
        if "team_id" in update_fields:
            new_team_id = update_fields["team_id"]
            if new_team_id:
                self._assign_player_to_team(player_id, new_team_id)
            else:
                self._remove_player_from_current_team(player_id)
                self.players[player_id]["team_id"] = new_team_id

        for field, value in update_fields.items():
            if field == "team_id":
                continue
            self.players[player_id][field] = value

        return { "success": True, "message": "Player profile updated successfully" }

    def add_tournament(
        self,
        tournament_id: str,
        name: str,
        structure: str,
        location: str
    ) -> dict:
        """
        Add a new tournament to the management system.

        Args:
            tournament_id (str): Unique identifier for the tournament.
            name (str): Tournament name.
            structure (str): Tournament format (e.g., 'round robin', 'knockout').
            location (str): Location of the tournament.

        Returns:
            dict: {
                "success": True,
                "message": "Tournament <tournament_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - tournament_id must be unique (must not already exist in the system).
            - All provided parameters must be non-empty strings.
        """
        if not (tournament_id and name and structure and location):
            return {
                "success": False,
                "error": "All fields (tournament_id, name, structure, location) are required and cannot be empty."
            }

        if tournament_id in self.tournaments:
            return {
                "success": False,
                "error": "Tournament with this ID already exists."
            }

        tournament_info = {
            "tournament_id": tournament_id,
            "name": name,
            "structure": structure,
            "location": location
        }
        self.tournaments[tournament_id] = tournament_info
        return {
            "success": True,
            "message": f"Tournament {tournament_id} added successfully."
        }

    def update_tournament_info(
        self,
        tournament_id: str,
        name: str = None,
        structure: str = None,
        location: str = None
    ) -> dict:
        """
        Edit details of an existing tournament.

        Args:
            tournament_id (str): Unique tournament ID to update.
            name (str, optional): New name for the tournament.
            structure (str, optional): New format/structure for the tournament.
            location (str, optional): New location for the tournament.

        Returns:
            dict: {
                "success": True,
                "message": "Tournament information updated."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - Tournament with tournament_id must exist.
            - Only provided attributes will be updated.
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        tournament = self.tournaments[tournament_id]
        update_fields = {}

        if name is not None:
            tournament["name"] = name
            update_fields["name"] = name
        if structure is not None:
            tournament["structure"] = structure
            update_fields["structure"] = structure
        if location is not None:
            tournament["location"] = location
            update_fields["location"] = location

        if not update_fields:
            return {
                "success": False,
                "error": "No fields to update were provided"
            }

        self.tournaments[tournament_id] = tournament
        return {
            "success": True,
            "message": f"Tournament information updated: {', '.join(update_fields.keys())}."
        }

    def add_season(self, season_id: str, year: int, tournament_id: str) -> dict:
        """
        Add a new season record and associate it with a tournament.

        Args:
            season_id (str): Unique identifier for the season.
            year (int): Year of the season.
            tournament_id (str): Identifier of the tournament to associate with.

        Returns:
            dict: {
                "success": True,
                "message": "Season added and associated with tournament."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - season_id must be unique.
            - tournament_id must reference an existing tournament.
        """
        if not season_id or not isinstance(year, int) or not tournament_id:
            return {"success": False, "error": "Invalid or missing input data."}

        if season_id in self.seasons:
            return {"success": False, "error": "Season ID already exists."}

        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Associated tournament does not exist."}

        self.seasons[season_id] = {
            "season_id": season_id,
            "year": year,
            "tournament_id": tournament_id
        }
        return {"success": True, "message": "Season added and associated with tournament."}

    def update_season(
        self,
        season_id: str,
        year: int = None,
        tournament_id: str = None
    ) -> dict:
        """
        Modify details of a season: update the year and/or change tournament association.

        Args:
            season_id (str): Unique identifier for the season to update.
            year (int, optional): New year value for the season.
            tournament_id (str, optional): New tournament association. Must exist.

        Returns:
            dict: {
                "success": True,
                "message": "Season updated successfully."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - season_id must refer to an existing season.
            - If updating tournament_id, it must refer to an existing tournament.
            - At least one of 'year' or 'tournament_id' must be provided.
        """
        # Check existence
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist."}

        # Check at least one field to update
        if year is None and tournament_id is None:
            return {"success": False, "error": "No fields to update specified."}

        # If updating tournament association, check existence
        if tournament_id is not None:
            if tournament_id not in self.tournaments:
                return {"success": False, "error": "Tournament does not exist."}
            self.seasons[season_id]["tournament_id"] = tournament_id

        if year is not None:
            self.seasons[season_id]["year"] = year

        return {"success": True, "message": "Season updated successfully."}

    def add_team(self, team_id: str, team_name: str, players: list = None) -> dict:
        """
        Add a new team to the tournament management system.

        Args:
            team_id (str): Unique identifier for the team.
            team_name (str): Name of the team.
            players (list, optional): List of player_ids to assign to this team. All player_ids must exist.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Team added successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - team_id must not already exist.
            - If 'players' is given, all player_ids must exist in the system.
        """
        if team_id in self.teams:
            return { "success": False, "error": "Team ID already exists." }

        if players is not None:
            invalid_players = [pid for pid in players if pid not in self.players]
            if invalid_players:
                return { "success": False, "error": f"Invalid player_ids: {invalid_players}" }

        team_info = {
            "team_id": team_id,
            "team_name": team_name
        }
        if players is not None:
            team_info["players"] = players.copy()  # avoid referencing mutable external list

        self.teams[team_id] = team_info
        if players is not None:
            for player_id in players:
                self._assign_player_to_team(player_id, team_id)

        return { "success": True, "message": "Team added successfully." }


    def update_team_info(
        self,
        team_id: str,
        team_name: Optional[str] = None,
        players: Optional[List[str]] = None
    ) -> dict:
        """
        Edit fields of an existing team (name, player roster).

        Args:
            team_id (str): Unique identifier of the team to update.
            team_name (Optional[str]): New name for the team (if updating).
            players (Optional[List[str]]): New roster of player IDs (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Team info updated successfully."
            } on success,
            or {
                "success": False,
                "error": <error description>
            } if team does not exist or invalid player IDs.

        Constraints:
            - team_id must exist in the system.
            - If players is updated, all IDs must correspond to existing players.
            - If both fields are omitted, no change is made but still succeeds.
        """
        # Check team exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}

        # If updating roster, validate player IDs
        if players is not None:
            invalid_ids = [pid for pid in players if pid not in self.players]
            if invalid_ids:
                return {
                    "success": False,
                    "error": f"Invalid player IDs: {invalid_ids}"
                }
            current_players = set(self.teams[team_id].get("players", []))
            new_players = list(players)
            new_player_set = set(new_players)

            for player_id in current_players - new_player_set:
                if self.players.get(player_id, {}).get("team_id") == team_id:
                    self.players[player_id]["team_id"] = ""

            self.teams[team_id]["players"] = []
            for player_id in new_players:
                self._assign_player_to_team(player_id, team_id)

        # Update team name
        if team_name is not None:
            self.teams[team_id]["team_name"] = team_name

        return {"success": True, "message": "Team info updated successfully."}


class SportsTournamentManagementSystem(BaseEnv):
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

    def get_player_info(self, **kwargs):
        return self._call_inner_tool('get_player_info', kwargs)

    def get_tournament_info(self, **kwargs):
        return self._call_inner_tool('get_tournament_info', kwargs)

    def get_season_info(self, **kwargs):
        return self._call_inner_tool('get_season_info', kwargs)

    def list_player_statistics(self, **kwargs):
        return self._call_inner_tool('list_player_statistics', kwargs)

    def get_player_statistics(self, **kwargs):
        return self._call_inner_tool('get_player_statistics', kwargs)

    def list_tournaments_by_player(self, **kwargs):
        return self._call_inner_tool('list_tournaments_by_player', kwargs)

    def list_seasons_by_tournament(self, **kwargs):
        return self._call_inner_tool('list_seasons_by_tournament', kwargs)

    def list_players_by_team(self, **kwargs):
        return self._call_inner_tool('list_players_by_team', kwargs)

    def get_team_info(self, **kwargs):
        return self._call_inner_tool('get_team_info', kwargs)

    def validate_player_statistic_references(self, **kwargs):
        return self._call_inner_tool('validate_player_statistic_references', kwargs)

    def add_player_statistic(self, **kwargs):
        return self._call_inner_tool('add_player_statistic', kwargs)

    def update_player_statistic(self, **kwargs):
        return self._call_inner_tool('update_player_statistic', kwargs)

    def delete_player_statistic(self, **kwargs):
        return self._call_inner_tool('delete_player_statistic', kwargs)

    def add_player(self, **kwargs):
        return self._call_inner_tool('add_player', kwargs)

    def update_player_info(self, **kwargs):
        return self._call_inner_tool('update_player_info', kwargs)

    def add_tournament(self, **kwargs):
        return self._call_inner_tool('add_tournament', kwargs)

    def update_tournament_info(self, **kwargs):
        return self._call_inner_tool('update_tournament_info', kwargs)

    def add_season(self, **kwargs):
        return self._call_inner_tool('add_season', kwargs)

    def update_season(self, **kwargs):
        return self._call_inner_tool('update_season', kwargs)

    def add_team(self, **kwargs):
        return self._call_inner_tool('add_team', kwargs)

    def update_team_info(self, **kwargs):
        return self._call_inner_tool('update_team_info', kwargs)
