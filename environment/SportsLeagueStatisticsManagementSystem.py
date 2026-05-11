# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any, Optional



# Entity: League (league_id, name, sport_type)
class LeagueInfo(TypedDict):
    league_id: str
    name: str
    sport_type: str

# Entity: Season (season_id, league_id, year)
class SeasonInfo(TypedDict):
    season_id: str
    league_id: str
    year: int

# Entity: Tournament (tournament_id, league_id, season_id, name, start_date, end_date)
class TournamentInfo(TypedDict):
    tournament_id: str
    league_id: str
    season_id: str
    name: str
    start_date: str  # ISO 8601 date string
    end_date: str    # ISO 8601 date string

# Entity: Team (team_id, name, league_id)
class TeamInfo(TypedDict):
    team_id: str
    name: str
    league_id: str

# Entity: Player (player_id, name, team_id, active_status)
class PlayerInfo(TypedDict):
    player_id: str
    name: str
    team_id: str  # current team assignment
    active_status: bool

# Entity: PlayerTournamentStats (player_id, tournament_id, season_id, team_id, metrics)
class PlayerTournamentStatsInfo(TypedDict):
    player_id: str
    tournament_id: str
    season_id: str
    team_id: str
    metrics: Dict[str, Any]  # e.g. {'points': 30, 'assists': 2, ...}

class _GeneratedEnvImpl:
    def __init__(self):
        # League: {league_id: LeagueInfo}
        self.leagues: Dict[str, LeagueInfo] = {}

        # Season: {season_id: SeasonInfo}
        self.seasons: Dict[str, SeasonInfo] = {}

        # Tournament: {tournament_id: TournamentInfo}
        self.tournaments: Dict[str, TournamentInfo] = {}

        # Team: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Player: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # PlayerTournamentStats: {(player_id, tournament_id): PlayerTournamentStatsInfo}
        # (For lookup, keys are 'player_id|tournament_id')
        self.player_tournament_stats: Dict[str, PlayerTournamentStatsInfo] = {}

        # Constraints:
        # - Each tournament is uniquely associated with a league and a season.
        # - Players must be assigned to only one team at a time per tournament/season.
        # - Rankings of "top players" are computed based on defined statistical metrics (e.g., points scored).
        # - Only active players are considered in rankings unless specified otherwise.

    def get_league_by_name(self, name: str) -> dict:
        """
        Retrieve league information by league name.

        Args:
            name (str): The name of the league to look up.

        Returns:
            dict: {
                "success": True,
                "data": LeagueInfo,  # League information if found
            }
            OR
            {
                "success": False,
                "error": str  # e.g. "League not found"
            }

        Constraints:
            - League name must exist in the environment.
            - Returns the first match if multiple exist (assuming league names are unique).
        """
        for league in self.leagues.values():
            if league['name'] == name:
                return {"success": True, "data": league}
        return {"success": False, "error": "League not found"}

    def get_league_by_id(self, league_id: str) -> dict:
        """
        Retrieve league details using the league_id.

        Args:
            league_id (str): Unique identifier for the league.

        Returns:
            dict: {
                "success": True,
                "data": LeagueInfo  # Dictionary of league information
            }
            or
            {
                "success": False,
                "error": str  # "League not found"
            }
        """
        league = self.leagues.get(league_id)
        if league is None:
            return {"success": False, "error": "League not found"}
        return {"success": True, "data": league}

    def get_season_by_league_and_year(self, league_id: str, year: int) -> dict:
        """
        Retrieve season information for a given league and year.

        Args:
            league_id (str): The league identifier to search for.
            year (int): The year of the season.

        Returns:
            dict:
                - success=True: {"success": True, "data": SeasonInfo}
                - success=False: {"success": False, "error": str}

        Constraints:
            - league_id must exist in the system.
            - If no season exists for the given league and year, return an error.
        """
        if league_id not in self.leagues:
            return {"success": False, "error": "League does not exist"}

        for season in self.seasons.values():
            if season['league_id'] == league_id and season['year'] == year:
                return {"success": True, "data": season}

        return {"success": False, "error": "No season found for the given league and year"}

    def list_tournaments_by_league_and_season(self, league_id: str, season_id: str) -> dict:
        """
        List all tournaments that are associated with the specified league and season.

        Args:
            league_id (str): The ID of the league.
            season_id (str): The ID of the season.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TournamentInfo]  # All tournaments in given league and season (can be empty)
                }
            or
                {
                    "success": False,
                    "error": str  # Reason why operation failed (e.g. invalid league_id/season_id)
                }

        Constraints:
            - league_id must refer to an existing league.
            - season_id must refer to an existing season.
        """
        if league_id not in self.leagues:
            return {"success": False, "error": "League does not exist"}
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}

        tournaments = [
            tinfo for tinfo in self.tournaments.values()
            if tinfo["league_id"] == league_id and tinfo["season_id"] == season_id
        ]
        return {"success": True, "data": tournaments}

    def get_tournament_by_id(self, tournament_id: str) -> dict:
        """
        Retrieve details for a tournament using its tournament_id.

        Args:
            tournament_id (str): The unique identifier of the tournament.

        Returns:
            dict: 
              - If tournament exists:
                    {"success": True, "data": TournamentInfo}
              - If not found:
                    {"success": False, "error": "Tournament not found"}
        """
        tournament_info = self.tournaments.get(tournament_id)
        if tournament_info is not None:
            return {"success": True, "data": tournament_info}
        else:
            return {"success": False, "error": "Tournament not found"}

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve player information using player_id.

        Args:
            player_id (str): The unique identifier for the player.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo  # player's full information
            }
            OR
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

    def get_players_by_team(self, team_id: str) -> dict:
        """
        List all players belonging to a specific team.

        Args:
            team_id (str): The identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The given team_id must exist in the system.
            - Returns all players whose current team assignment matches the given team_id.
        """
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        players = [
            player_info for player_info in self.players.values()
            if player_info["team_id"] == team_id
        ]
        return {"success": True, "data": players}

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve team details using the provided team_id.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo  # Team details if found
            }
            OR
            {
                "success": False,
                "error": str  # If team_id not found
            }
    
        Constraints:
            - team_id must exist in the system.
        """
        team = self.teams.get(team_id)
        if team is None:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team }

    def get_stats_for_tournament(
        self,
        tournament_id: str,
        team_id: Optional[str] = None,
        only_active: Optional[bool] = True
    ) -> dict:
        """
        Retrieve all PlayerTournamentStatsInfo for the given tournament_id.
        Optionally filter by team_id (only that team) and/or only include active players.

        Args:
            tournament_id (str): Tournament for which to retrieve stats.
            team_id (Optional[str]): If set, only include stats where team_id matches.
            only_active (Optional[bool]): If True (default), only include active players.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerTournamentStatsInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Tournament must exist.
            - Players must be active if only_active is True.
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        result = []
        for stats in self.player_tournament_stats.values():
            if stats["tournament_id"] != tournament_id:
                continue
            if team_id is not None and stats["team_id"] != team_id:
                continue
            pid = stats["player_id"]
            player_info = self.players.get(pid)
            if only_active:
                if not player_info or not player_info.get("active_status", False):
                    continue # skip inactive or missing player
            result.append(stats)

        return {"success": True, "data": result}

    def get_stats_for_player_in_tournament(self, player_id: str, tournament_id: str) -> dict:
        """
        Retrieve PlayerTournamentStats for a specific player in a specified tournament.

        Args:
            player_id (str): Unique identifier for the player.
            tournament_id (str): Unique identifier for the tournament.

        Returns:
            dict: 
                - On success: { "success": True, "data": PlayerTournamentStatsInfo }
                - On failure: { "success": False, "error": "No stats found for player in tournament" }

        Constraints:
            - The stats entry must exist for the (player_id, tournament_id) pair.
        """
        key = f"{player_id}|{tournament_id}"
        if key not in self.player_tournament_stats:
            return { "success": False, "error": "No stats found for player in tournament" }
    
        return { "success": True, "data": self.player_tournament_stats[key] }

    def get_top_players_for_tournament(
        self,
        tournament_id: str,
        metric: str,
        top_n: int,
        include_inactive: bool = False
    ) -> dict:
        """
        Compute and return the top N players for a tournament based on a given statistical metric.

        Args:
            tournament_id (str): The target tournament's ID.
            metric (str): The statistical metric/key to rank by (e.g., 'points').
            top_n (int): Number of top players to return (largest values first).
            include_inactive (bool): If True, include inactive players; if False, only active players. Default: False.

        Returns:
            dict: {
                "success": True,
                "data": [
                    {
                        "player_id": str,
                        "player_info": PlayerInfo,
                        "stats_info": PlayerTournamentStatsInfo,
                        "metric_value": Any
                    },
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only stats for the given tournament_id are considered.
            - Only active players (unless include_inactive is True).
            - If top_n <= 0, data will be an empty list.
            - Tournament must exist.
        """
        # Check tournament existence
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        if top_n <= 0:
            return {"success": True, "data": []}

        # Gather player-tournament stats for the tournament
        stats_entries = [
            stats for stats in self.player_tournament_stats.values()
            if stats["tournament_id"] == tournament_id
        ]

        results = []
        for stats in stats_entries:
            player_id = stats["player_id"]
            player_info = self.players.get(player_id)
            if not player_info:
                continue  # player not in system (data integrity issue—skip)

            # Check active status unless including inactive
            if not include_inactive and not player_info.get("active_status", False):
                continue

            metric_value = stats["metrics"].get(metric)
            if metric_value is None:
                continue  # Player has no value for this metric

            results.append({
                "player_id": player_id,
                "player_info": player_info,
                "stats_info": stats,
                "metric_value": metric_value
            })

        # Sort by metric_value descending
        results_sorted = sorted(results, key=lambda x: x["metric_value"], reverse=True)

        # Only return up to top N
        top_results = results_sorted[:top_n]

        return {
            "success": True,
            "data": top_results
        }

    def get_top_players_for_tournaments(
        self, 
        tournament_ids: list, 
        metric: str, 
        top_n: int = 3, 
        include_inactive: bool = False
    ) -> dict:
        """
        For a set of tournaments, return the top players per tournament based on the given statistical metric.
    
        Args:
            tournament_ids (List[str]): List of tournament IDs to consider.
            metric (str): The metric to rank by (e.g., 'points', 'goals').
            top_n (int, optional): Number of top players to return per tournament. Default is 3.
            include_inactive (bool, optional): Whether to include inactive players. Default is False.
        
        Returns:
            dict: {
                "success": True,
                "data": {
                    tournament_id1: [PlayerTournamentStatsInfo, ...],  # Sorted by metric desc, up to top_n
                    tournament_id2: [...],
                    ...
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Each tournament must exist.
            - Only active players are considered unless include_inactive is True.
            - If metric is missing in metrics dict for a player, treat as zero.
        """
        result = {}
        # Validate and process each tournament_id
        for tid in tournament_ids:
            if tid not in self.tournaments:
                # Tournament does not exist, skip or could add empty list
                result[tid] = []
                continue

            # Gather all player stats for this tournament
            stats_for_tournament = [
                pts for pts in self.player_tournament_stats.values()
                if pts['tournament_id'] == tid
            ]

            if not stats_for_tournament:
                result[tid] = []
                continue

            filtered_stats = []
            for pts in stats_for_tournament:
                player_id = pts['player_id']
                player_info = self.players.get(player_id)
                if not player_info:
                    continue  # player not found (data inconsistency)
                if not include_inactive and not player_info.get('active_status', False):
                    continue  # skip inactive players

                # The metric may be missing in stats: treat as 0
                metric_value = pts['metrics'].get(metric, 0)
                # Copy and attach the metric value for sorting
                pts_with_value = dict(pts)
                pts_with_value['_metric_value_for_sorting'] = metric_value
                filtered_stats.append(pts_with_value)

            # Sort descending by metric value
            sorted_stats = sorted(
                filtered_stats, 
                key=lambda x: x['_metric_value_for_sorting'], 
                reverse=True
            )

            # Remove the temporary field before returning
            top_stats = [
                {k: v for k, v in pts.items() if k != '_metric_value_for_sorting'} 
                for pts in sorted_stats[:top_n]
            ]

            result[tid] = top_stats

        return { "success": True, "data": result }

    def get_player_active_status(self, player_id: str) -> dict:
        """
        Retrieve the active/inactive status for a specific player.

        Args:
            player_id (str): Unique identifier of the player.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": {
                        "player_id": str,
                        "active_status": bool
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": "Player does not exist"
                }

        Constraints:
            - The player must exist in the system.
        """
        player = self.players.get(player_id)
        if player is None:
            return { "success": False, "error": "Player does not exist" }
        return {
            "success": True,
            "data": {
                "player_id": player_id,
                "active_status": player["active_status"]
            }
        }

    def update_player_stats_for_tournament(
        self, player_id: str, tournament_id: str, metrics_update: Dict[str, Any]
    ) -> dict:
        """
        Update or add new statistics in PlayerTournamentStats for a specific player in a tournament.

        Args:
            player_id (str): ID of the player whose stats are to be updated.
            tournament_id (str): ID of the tournament.
            metrics_update (Dict[str, Any]): Dictionary of metrics to update/add (e.g., {"points": 10, "assists": 3})

        Returns:
            dict:
                - On success: { "success": True, "message": "Player tournament statistics updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - player_id and tournament_id must exist in the system.
            - PlayerTournamentStats is created if not existing, with appropriate season_id and team_id.
            - Only one PlayerTournamentStats per (player_id, tournament_id).
            - metrics_update must be a non-empty dict.
        """
        # Check basic validity
        if player_id not in self.players:
            return {"success": False, "error": "Player not found."}
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament not found."}
        if not isinstance(metrics_update, dict) or not metrics_update:
            return {"success": False, "error": "metrics_update must be a non-empty dictionary."}
    
        # Get composite key
        key = f"{player_id}|{tournament_id}"

        tournament_info = self.tournaments[tournament_id]
        season_id = tournament_info["season_id"]

        # Get current team assignment for player
        player_info = self.players[player_id]
        team_id = player_info["team_id"]

        # Update or create stats
        if key in self.player_tournament_stats:
            # Update metrics (merge/override)
            current_stats = self.player_tournament_stats[key]
            current_metrics = current_stats.get("metrics", {})
            current_metrics.update(metrics_update)
            current_stats["metrics"] = current_metrics
            # Optionally refresh other fields if player has switched teams
            current_stats["team_id"] = team_id
            current_stats["season_id"] = season_id
            self.player_tournament_stats[key] = current_stats
        else:
            # Create new stats record
            self.player_tournament_stats[key] = {
                "player_id": player_id,
                "tournament_id": tournament_id,
                "season_id": season_id,
                "team_id": team_id,
                "metrics": metrics_update.copy(),
            }

        return {"success": True, "message": "Player tournament statistics updated."}

    def set_player_active_status(self, player_id: str, active_status: bool) -> dict:
        """
        Activate or deactivate a player in the system.

        Args:
            player_id (str): The ID of the player whose status is to be changed.
            active_status (bool): True to mark the player active, False to mark inactive.

        Returns:
            dict: {
                "success": True,
                "message": "Player {player_id} active_status updated to {active_status}"
            }
            or
            {
                "success": False,
                "error": "Player not found" or "active_status must be a boolean"
            }

        Constraints:
            - player_id must exist in the system.
            - active_status must be a boolean value.
        """
        if player_id not in self.players:
            return {
                "success": False,
                "error": "Player not found"
            }
        if not isinstance(active_status, bool):
            return {
                "success": False,
                "error": "active_status must be a boolean"
            }
        self.players[player_id]['active_status'] = active_status
        return {
            "success": True,
            "message": f"Player {player_id} active_status updated to {active_status}"
        }

    def assign_player_to_team(
        self, 
        player_id: str, 
        team_id: str, 
        tournament_id: str, 
        season_id: str
    ) -> dict:
        """
        Assign (or reassign) a player to a team for the specified tournament and season,
        ensuring all structural and uniqueness constraints are enforced.

        Args:
            player_id (str): The unique ID of the player.
            team_id (str): The unique ID of the team.
            tournament_id (str): The unique ID of the tournament.
            season_id (str): The unique ID of the season.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - All referenced entities must exist.
            - Players may be assigned to only one team per tournament/season.
            - The team must participate in the same league as the tournament/season.
        """
        # Check if player exists
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }

        # Check if team exists
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        # Check if tournament exists
        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament does not exist" }

        # Check if season exists
        if season_id not in self.seasons:
            return { "success": False, "error": "Season does not exist" }

        # Check league association
        tournament = self.tournaments[tournament_id]
        team = self.teams[team_id]

        if tournament["league_id"] != team["league_id"]:
            return {
                "success": False,
                "error": "Team and tournament are in different leagues"
            }

        if tournament["season_id"] != season_id:
            return {
                "success": False,
                "error": "Tournament is not associated with the specified season"
            }

        # Enforce uniqueness: one team per player per tournament/season
        key = f"{player_id}|{tournament_id}"
        stats_info = self.player_tournament_stats.get(key)
        if stats_info:
            # Already assigned for this tournament/season
            if stats_info["team_id"] == team_id:
                self.players[player_id]["team_id"] = team_id
                return {
                    "success": True,
                    "message": (
                        f"Player {player_id} is already assigned to team {team_id} "
                        f"for tournament {tournament_id}, season {season_id}"
                    )
                }
            else:
                # Reassigning to new team
                stats_info["team_id"] = team_id
                stats_info["season_id"] = season_id  # Ensure correct season is set
                self.player_tournament_stats[key] = stats_info
                self.players[player_id]["team_id"] = team_id
                return {
                    "success": True,
                    "message": (
                        f"Player {player_id} reassigned to team {team_id} "
                        f"for tournament {tournament_id}, season {season_id}"
                    )
                }
        else:
            # No stats for this (player, tournament) — create new assignment
            self.player_tournament_stats[key] = {
                "player_id": player_id,
                "tournament_id": tournament_id,
                "season_id": season_id,
                "team_id": team_id,
                "metrics": {}
            }
            self.players[player_id]["team_id"] = team_id
            return {
                "success": True,
                "message": (
                    f"Player {player_id} assigned to team {team_id} "
                    f"for tournament {tournament_id}, season {season_id}"
                )
            }

    def add_new_tournament(self, tournament_id: str, league_id: str, season_id: str, name: str, start_date: str, end_date: str) -> dict:
        """
        Add a new tournament to a league and season.

        Args:
            tournament_id (str): Unique identifier for the tournament.
            league_id (str): League to which the tournament belongs (must exist).
            season_id (str): Season associated with the tournament (must exist and belong to this league).
            name (str): Tournament name.
            start_date (str): Start date (ISO 8601, e.g., '2023-08-10').
            end_date (str): End date (ISO 8601, e.g., '2023-08-20').

        Returns:
            dict: { "success": True, "message": ... } on success,
                  { "success": False, "error": <reason> } on error.

        Constraints:
            - tournament_id must be unique.
            - league_id and season_id must exist.
            - season_id must belong to league_id.
            - start_date <= end_date in date ordering.
        """
        # Check unique tournament_id
        if tournament_id in self.tournaments:
            return {"success": False, "error": "Tournament ID already exists."}

        # Check league exists
        if league_id not in self.leagues:
            return {"success": False, "error": "League does not exist."}

        # Check season exists
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist."}

        # Check season belongs to league
        season_info = self.seasons[season_id]
        if season_info['league_id'] != league_id:
            return {"success": False, "error": "Season does not belong to specified league."}

        # Check nonempty fields
        if not name or not start_date or not end_date:
            return {"success": False, "error": "Required fields (name, start_date, or end_date) are missing."}

        # Check start_date <= end_date (lexical order suffices for ISO8601)
        if start_date > end_date:
            return {"success": False, "error": "Start date must not be after end date."}

        # Insert the new tournament
        self.tournaments[tournament_id] = {
            "tournament_id": tournament_id,
            "league_id": league_id,
            "season_id": season_id,
            "name": name,
            "start_date": start_date,
            "end_date": end_date
        }

        return {
            "success": True,
            "message": f"Tournament '{name}' added to league '{league_id}' and season '{season_id}'."
        }

    def add_new_player(self, player_id: str, name: str, team_id: str, active_status: bool = True) -> dict:
        """
        Add a new player to the system with initial team assignment.

        Args:
            player_id (str): Unique identifier for the new player.
            name (str): Player's name.
            team_id (str): Team ID to assign the player to initially.
            active_status (bool, optional): Player's active status (default: True).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Player <player_id> added to team <team_id>."
                    }
                On error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The player_id must be unique in the system.
            - The team_id must correspond to an existing team.
            - Player must have a name.
            - Player can only be assigned to one team at the point of creation.
        """
        if not player_id or not name or not team_id:
            return { "success": False, "error": "Missing required player_id, name, or team_id." }

        if player_id in self.players:
            return { "success": False, "error": f"Player with ID '{player_id}' already exists." }

        if team_id not in self.teams:
            return { "success": False, "error": f"Team with ID '{team_id}' does not exist." }

        player_info = {
            "player_id": player_id,
            "name": name,
            "team_id": team_id,
            "active_status": active_status
        }
        self.players[player_id] = player_info
        return { "success": True, "message": f"Player {player_id} added to team {team_id}." }

    def add_new_team(self, team_id: str, name: str, league_id: str) -> dict:
        """
        Add a new team to a league.

        Args:
            team_id (str): Unique identifier for the new team.
            name (str): Name of the new team.
            league_id (str): Identifier of the league to which the team is to be added.

        Returns:
            dict: {
                "success": True,
                "message": "Team added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - league_id must reference an existing league.
            - team_id must be unique among all teams.
            - No other team in that league may have the same name.
        """
        if not team_id or not isinstance(team_id, str):
            return {"success": False, "error": "team_id must be a non-empty string"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "name must be a non-empty string"}
        if not league_id or not isinstance(league_id, str):
            return {"success": False, "error": "league_id must be a non-empty string"}
        if league_id not in self.leagues:
            return {"success": False, "error": f"League '{league_id}' does not exist."}
        if team_id in self.teams:
            return {"success": False, "error": f"Team ID '{team_id}' already exists."}
        for existing_team in self.teams.values():
            if existing_team["league_id"] == league_id and existing_team["name"].lower() == name.lower():
                return {"success": False, "error": f"A team named '{name}' already exists in league '{league_id}'."}

        self.teams[team_id] = {
            "team_id": team_id,
            "name": name,
            "league_id": league_id,
        }
        return {"success": True, "message": "Team added successfully."}


class SportsLeagueStatisticsManagementSystem(BaseEnv):
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
            if key == "player_tournament_stats" and isinstance(value, dict):
                normalized = {}
                for original_key, stats_info in value.items():
                    if isinstance(stats_info, dict):
                        player_id = stats_info.get("player_id")
                        tournament_id = stats_info.get("tournament_id")
                        if player_id and tournament_id:
                            normalized[f"{player_id}|{tournament_id}"] = copy.deepcopy(stats_info)
                            continue
                    normalized[original_key] = copy.deepcopy(stats_info)
                setattr(env, key, normalized)
                continue
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

    def get_league_by_name(self, **kwargs):
        return self._call_inner_tool('get_league_by_name', kwargs)

    def get_league_by_id(self, **kwargs):
        return self._call_inner_tool('get_league_by_id', kwargs)

    def get_season_by_league_and_year(self, **kwargs):
        return self._call_inner_tool('get_season_by_league_and_year', kwargs)

    def list_tournaments_by_league_and_season(self, **kwargs):
        return self._call_inner_tool('list_tournaments_by_league_and_season', kwargs)

    def get_tournament_by_id(self, **kwargs):
        return self._call_inner_tool('get_tournament_by_id', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_players_by_team(self, **kwargs):
        return self._call_inner_tool('get_players_by_team', kwargs)

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def get_stats_for_tournament(self, **kwargs):
        return self._call_inner_tool('get_stats_for_tournament', kwargs)

    def get_stats_for_player_in_tournament(self, **kwargs):
        return self._call_inner_tool('get_stats_for_player_in_tournament', kwargs)

    def get_top_players_for_tournament(self, **kwargs):
        return self._call_inner_tool('get_top_players_for_tournament', kwargs)

    def get_top_players_for_tournaments(self, **kwargs):
        return self._call_inner_tool('get_top_players_for_tournaments', kwargs)

    def get_player_active_status(self, **kwargs):
        return self._call_inner_tool('get_player_active_status', kwargs)

    def update_player_stats_for_tournament(self, **kwargs):
        return self._call_inner_tool('update_player_stats_for_tournament', kwargs)

    def set_player_active_status(self, **kwargs):
        return self._call_inner_tool('set_player_active_status', kwargs)

    def assign_player_to_team(self, **kwargs):
        return self._call_inner_tool('assign_player_to_team', kwargs)

    def add_new_tournament(self, **kwargs):
        return self._call_inner_tool('add_new_tournament', kwargs)

    def add_new_player(self, **kwargs):
        return self._call_inner_tool('add_new_player', kwargs)

    def add_new_team(self, **kwargs):
        return self._call_inner_tool('add_new_team', kwargs)
