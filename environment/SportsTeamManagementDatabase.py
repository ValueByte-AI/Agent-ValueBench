# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class PerformanceStats(TypedDict, total=False):
    # Placeholder for performance statistics structure (to be specified further)
    # Example: goals: int, assists: int, etc.
    pass

class PlayerInfo(TypedDict):
    player_id: str
    name: str
    date_of_birth: str
    team_id: str
    sport_id: str
    performance_stats: PerformanceStats

class TeamInfo(TypedDict):
    team_id: str
    name: str
    sport_id: str
    roster: List[str]  # List of player_ids

class TournamentInfo(TypedDict):
    tournament_id: str
    name: str
    sport_id: str
    participating_team_ids: List[str]
    participating_player_ids: List[str]
    date_range: str  # Could be more structured, e.g., (start, end) tuple

class SportInfo(TypedDict):
    sport_id: str
    name: str
    rules: str  # Might be expanded to more detailed structure

class _GeneratedEnvImpl:
    def __init__(self):
        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Tournaments: {tournament_id: TournamentInfo}
        self.tournaments: Dict[str, TournamentInfo] = {}

        # Sports: {sport_id: SportInfo}
        self.sports: Dict[str, SportInfo] = {}

        # Constraints:
        # - Each player may be affiliated with only one team per sport at a time.
        # - Players can participate in multiple tournaments, but only if their team is participating or the tournament allows individual entries.
        # - Performance stats must be updated in association with specific tournaments or matches.
        # - Each team competes in only one sport.
        # - Teams’ rosters must be consistent with tournament eligibility requirements.

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve full information about a player given their player_id.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo,   # Player information with all standard fields
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., player not found
            }
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player}

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Obtain team information by its team_id.

        Args:
            team_id (str): Unique identifier for the team.

        Returns:
            dict: 
                On success: { "success": True, "data": TeamInfo }
                On failure: { "success": False, "error": "Team not found" }
        Constraints:
            - The team_id must exist in the system.
        """
        team = self.teams.get(team_id)
        if team is None:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team }

    def get_sport_by_id(self, sport_id: str) -> dict:
        """
        Retrieve details of a sport using sport_id.

        Args:
            sport_id (str): The unique identifier of the sport.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SportInfo  # All information about the sport
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Sport not found"
                    }

        Constraints:
            - The sport_id must exist in the database.
        """
        sport = self.sports.get(sport_id)
        if not sport:
            return { "success": False, "error": "Sport not found" }
        return { "success": True, "data": sport }

    def get_tournament_by_id(self, tournament_id: str) -> dict:
        """
        Retrieve tournament details using its unique tournament_id.

        Args:
            tournament_id (str): The identifier for the tournament.

        Returns:
            dict: {
                "success": True,
                "data": TournamentInfo,    # Tournament data if found
            }
            or
            {
                "success": False,
                "error": str               # If tournament not found
            }

        Constraints:
            - Returns data only if tournament_id exists in the database.
        """
        if tournament_id not in self.tournaments:
            return {
                "success": False,
                "error": f"Tournament with id '{tournament_id}' does not exist"
            }
        return {
            "success": True,
            "data": self.tournaments[tournament_id]
        }

    def get_player_team(self, player_id: str) -> dict:
        """
        Retrieve the team record (TeamInfo) of the team to which a given player currently belongs.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": TeamInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The player must exist.
            - The player must be currently affiliated with a team.
            - The referenced team must exist in the database.
        """
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player not found"}

        team_id = player.get("team_id")
        if not team_id:
            return {"success": False, "error": "Player is not affiliated with any team"}

        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": "Player's team record not found"}

        return {"success": True, "data": team}

    def get_team_players(self, team_id: str) -> dict:
        """
        List all players in a specific team's roster.

        Args:
            team_id (str): The identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo]  # May be empty if roster is empty
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The provided team_id must exist in the database.
            - Only players whose ids are in the team's roster and present in self.players will be listed.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        roster_ids = self.teams[team_id].get("roster", [])

        players = [self.players[pid] for pid in roster_ids if pid in self.players]

        return { "success": True, "data": players }

    def get_player_tournaments(self, player_id: str) -> dict:
        """
        Return all tournaments a player is currently registered for (considering both team-based and individual entries).

        Args:
            player_id (str): The identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": List[TournamentInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Player with the given player_id must exist.
            - Tournaments include both team and individual player registrations.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player not found"}

        player = self.players[player_id]
        player_team_id = player.get("team_id", None)

        matched_tournaments = []
        for tournament in self.tournaments.values():
            if (
                player_id in tournament.get("participating_player_ids", [])
                or (player_team_id and player_team_id in tournament.get("participating_team_ids", []))
            ):
                matched_tournaments.append(tournament)

        return {"success": True, "data": matched_tournaments}

    def get_team_tournaments(self, team_id: str) -> dict:
        """
        List all tournaments a team is participating in.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": List[TournamentInfo]   # May be empty if not in any tournaments.
            }
            or
            {
                "success": False,
                "error": str  # E.g., "Team does not exist"
            }
        Constraints:
            - The specified team must exist in the database.
        """
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}
    
        tournaments = [
            tournament for tournament in self.tournaments.values()
            if team_id in tournament.get("participating_team_ids", [])
        ]
        return {"success": True, "data": tournaments}

    def get_sport_teams(self, sport_id: str) -> dict:
        """
        Retrieve a list of all teams that compete in a specified sport.

        Args:
            sport_id (str): The unique identifier of the sport.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[TeamInfo]  # List of teams for the sport, empty list if none
                  }
                - On error: {
                    "success": False,
                    "error": str  # Reason, e.g. sport does not exist
                  }
        Constraints:
            - The specified sport_id must exist in the database.
        """
        if sport_id not in self.sports:
            return {"success": False, "error": "Sport does not exist"}

        teams_in_sport = [
            team_info for team_info in self.teams.values()
            if team_info["sport_id"] == sport_id
        ]
        return {"success": True, "data": teams_in_sport}

    def get_tournament_players(self, tournament_id: str) -> dict:
        """
        List all players registered for a given tournament.

        Args:
            tournament_id (str): Unique ID of the tournament.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo]  # List of player information dictionaries
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., tournament not found
            }
        Constraints:
            - Tournament must exist in the database.
        """
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return { "success": False, "error": "Tournament not found" }
    
        player_infos = [
            self.players[pid]
            for pid in tournament.get("participating_player_ids", [])
            if pid in self.players
        ]
        return { "success": True, "data": player_infos }

    def get_tournament_teams(self, tournament_id: str) -> dict:
        """
        List all teams participating in a given tournament.
    
        Args:
            tournament_id (str): Identifier for the tournament.
    
        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": List[TeamInfo],  # List of participating teams' info (may be empty)
                }
                On failure,
                {
                    "success": False,
                    "error": str  # "Tournament not found"
                }
        Constraints:
            - The tournament must exist.
            - Only info for teams currently in the database will be returned.
        """
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament not found"}
    
        team_infos = [
            self.teams[team_id]
            for team_id in tournament["participating_team_ids"]
            if team_id in self.teams
        ]
        return {"success": True, "data": team_infos}

    def get_player_performance_stats(self, player_id: str, tournament_id: str = None, match_id: str = None) -> dict:
        """
        Fetch all available performance statistics for a player, optionally filtered by tournament or match.

        Args:
            player_id (str): The unique identifier of the player.
            tournament_id (str, optional): NOT SUPPORTED in current stats structure—will be ignored.
            match_id (str, optional): NOT SUPPORTED—will be ignored.

        Returns:
            dict:
                - On success: { "success": True, "data": performance_stats (dict, may be empty) }
                - On failure: { "success": False, "error": error message }
        Notes:
            - tournament_id and match_id filters are ignored since the present performance_stats structure on PlayerInfo is flat.
            - Returns all available performance stats for this player.
        """
        player = self.players.get(player_id)
        if not player:
            return { "success": False, "error": "Player not found" }

        stats = player.get("performance_stats", {})

        # Currently, we do not structure stats by tournament or match; future support possible.
        # We could log/warn if tournament_id/match_id is passed, but ignore for now.

        return { "success": True, "data": stats }

    def get_sport_rules(self, sport_id: str) -> dict:
        """
        Obtain the rules or description of a specified sport.

        Args:
            sport_id (str): The identifier for the sport.

        Returns:
            dict: {
                "success": True,
                "data": str,  # the rules/description of the sport
            }
            or
            {
                "success": False,
                "error": str  # Explanation if sport not found
            }

        Constraints:
            - The provided sport_id must exist in the database.
        """
        sport = self.sports.get(sport_id)
        if not sport:
            return {"success": False, "error": "Sport not found"}
        return {"success": True, "data": sport["rules"]}

    def update_player_team_affiliation(self, player_id: str, new_team_id: str) -> dict:
        """
        Change a player's team within a specific sport.
        Ensures the player is only affiliated with one team per sport at a time, and team & player are in the same sport.
        Updates old and new team rosters accordingly.

        Args:
            player_id (str): ID of the player to update.
            new_team_id (str): ID of the new team for the player.

        Returns:
            dict:
                On success: { "success": True, "message": "Player's team affiliation updated." }
                On failure: { "success": False, "error": "<reason>" }
        """
        player = self.players.get(player_id)
        if not player:
            return { "success": False, "error": "Player not found" }

        new_team = self.teams.get(new_team_id)
        if not new_team:
            return { "success": False, "error": "New team not found" }

        # Player and team must be for the same sport
        if player['sport_id'] != new_team['sport_id']:
            return { "success": False, "error": "Player and team are not in the same sport" }

        old_team_id = player.get('team_id')
        if old_team_id == new_team_id:
            return { "success": True, "message": "Player is already affiliated with the specified team." }

        # Remove from old team roster if affiliated
        if old_team_id and old_team_id in self.teams:
            old_team = self.teams[old_team_id]
            if player_id in old_team.get('roster', []):
                old_team['roster'].remove(player_id)

        # Add to new team roster if not already present
        if player_id not in new_team.get('roster', []):
            new_team['roster'].append(player_id)

        # Update player's team_id
        player['team_id'] = new_team_id

        return { "success": True, "message": "Player's team affiliation updated." }

    def update_team_roster(
        self,
        team_id: str,
        add_player_ids: list,
        remove_player_ids: list
    ) -> dict:
        """
        Add and/or remove players from a team's roster with eligibility and integrity checks.

        Args:
            team_id (str): The team to update.
            add_player_ids (list): List of player_ids to add to the team roster.
            remove_player_ids (list): List of player_ids to remove from the team roster.

        Returns:
            dict: {
                "success": True,
                "message": "Team roster updated"
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }
    
        Constraints:
            - team_id must exist.
            - Players to add/remove must exist.
            - Team may compete in only one sport.
            - Players can only belong to one team per sport.
            - Roster changes must not violate team-sport match.
            - No duplicate player_ids in roster.
        """
        # Check if team exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}
        team = self.teams[team_id]
        team_sport_id = team["sport_id"]

        # Prepare the new roster
        current_roster = set(team["roster"])
        add_set = set(add_player_ids)
        remove_set = set(remove_player_ids)
    
        # Validate players to add/remove
        for pid in add_set | remove_set:
            if pid not in self.players:
                return {"success": False, "error": f"Player {pid} does not exist."}

        # Adding: check that their sport matches, and they are not already on another team for this sport
        for pid in add_set:
            p = self.players[pid]
            # Player must be of same sport
            if p["sport_id"] != team_sport_id:
                return {"success": False, "error": f"Player {pid} is not in the team's sport."}
            # Check if player is already in another team for this sport (but allow if it's THIS team)
            if p["team_id"] and p["team_id"] != team_id:
                other_team = self.teams.get(p["team_id"])
                # Only conflict if the other team is same sport
                if other_team and other_team["sport_id"] == team_sport_id:
                    return {"success": False, "error": f"Player {pid} is already assigned to another team for this sport."}

        # Compute new roster: remove then add
        new_roster = (current_roster - remove_set) | add_set

        # Sanity: make sure no duplicates (set already, so OK)
        # Update team roster
        self.teams[team_id]["roster"] = list(new_roster)
    
        # For each player removed, update their team_id only if they belonged to this team already
        for pid in remove_set:
            if self.players[pid]["team_id"] == team_id:
                self.players[pid]["team_id"] = ""
        # For each player added, update their team_id accordingly
        for pid in add_set:
            self.players[pid]["team_id"] = team_id

        # (Tournament eligibility logic could go here, but is not specified in detail.)

        return {"success": True, "message": "Team roster updated"}

    def register_player_for_tournament(self, player_id: str, tournament_id: str) -> dict:
        """
        Registers a player for a tournament, validating:
        - The player exists.
        - The tournament exists.
        - The player is eligible based on team participation or individual entry rules.
        - The player is not already registered for this tournament.
        - The player's sport matches the tournament's sport.
    
        Args:
            player_id (str): ID of the player to register.
            tournament_id (str): ID of the tournament.

        Returns:
            dict: {
                "success": True,
                "message": "Player registered for tournament"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        """
        # Check existence
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player does not exist"}

        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament does not exist"}

        # Check sport match
        if player["sport_id"] != tournament["sport_id"]:
            return {"success": False, "error": "Player's sport and tournament's sport do not match"}

        # Already registered?
        if player_id in tournament["participating_player_ids"]:
            return {"success": False, "error": "Player is already registered for this tournament"}

        # Team participation
        team_id = player["team_id"]
        team_participating = team_id in tournament["participating_team_ids"]

        # If the player's team is participating: allow registration.
        if team_participating:
            tournament["participating_player_ids"].append(player_id)
            return {"success": True, "message": "Player registered for tournament (via team participation)"}

        # If not, check if tournament allows individual entry.
        # (We interpret presence of participating_player_ids as allowing this.)
        # Optionally, could add a flag to the TournamentInfo for individual entries, but per schema, proceed.
        if isinstance(tournament.get("participating_player_ids"), list):
            tournament["participating_player_ids"].append(player_id)
            return {"success": True, "message": "Player registered for tournament (individual entry allowed)"}
        else:
            return {
                "success": False,
                "error": "Tournament does not allow individual player entries and player's team is not participating"
            }

    def register_team_for_tournament(self, team_id: str, tournament_id: str) -> dict:
        """
        Add a team to a tournament, ensuring the team's sport matches the tournament's sport, 
        and the team isn't already registered for the tournament.

        Args:
            team_id (str): Unique ID of the team to be registered.
            tournament_id (str): Unique ID of the tournament.

        Returns:
            dict: 
                On success: {"success": True, "message": "Team <team_id> registered for tournament <tournament_id>."}
                On failure: {"success": False, "error": "<reason>"}
        Constraints:
            - Team and tournament must exist.
            - Team's sport_id must match tournament's sport_id.
            - Team must not already be in the list of participating_team_ids.
        """
        # Check team existence
        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": f"Team '{team_id}' does not exist."}

        # Check tournament existence
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": f"Tournament '{tournament_id}' does not exist."}

        # Check sport id match
        if team["sport_id"] != tournament["sport_id"]:
            return {
                "success": False,
                "error": (
                    f"Team's sport ('{team['sport_id']}') does not match Tournament's sport ('{tournament['sport_id']}')."
                )
            }

        # Check if already registered
        if team_id in tournament["participating_team_ids"]:
            return {
                "success": False,
                "error": f"Team '{team_id}' is already registered for tournament '{tournament_id}'."
            }

        # Register team
        tournament["participating_team_ids"].append(team_id)
        # No need to persist elsewhere—data is in memory and reference is maintained

        return {
            "success": True,
            "message": f"Team '{team_id}' registered for tournament '{tournament_id}'."
        }

    def update_player_performance_stats(
        self,
        player_id: str,
        tournament_id: str,
        new_stats: dict
    ) -> dict:
        """
        Set or modify a player's performance statistics for a specific tournament.

        Args:
            player_id (str): Player's unique identifier.
            tournament_id (str): Target tournament/event id.
            new_stats (dict): Dictionary with the stats to set for this player in this event.

        Returns:
            dict: {
                "success": True,
                "message": "...",
            }
            or
            {
                "success": False,
                "error": "...",
            }

        Constraints:
        - Both player and tournament must exist.
        - Player must be registered as a participant in the tournament.
        - Stats are stored/replaced for the (player, tournament) association.
        """
        # Validate player exists
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Player does not exist"}

        # Validate tournament exists
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament does not exist"}

        # Validate player participates in tournament
        if player_id not in tournament["participating_player_ids"]:
            return {"success": False, "error": "Player is not registered for this tournament"}

        # It's typical to store per-tournament stats as a mapping, e.g.:
        # player["performance_stats"][tournament_id] = new_stats
        # But class only shows a flat performance_stats field.
        # Safe option: treat performance_stats as {tournament_id: PerformanceStats}, and retrofit if needed.
        if not isinstance(player.get("performance_stats"), dict):
            player["performance_stats"] = {}

        # Update (overwrite) stats for this tournament
        player["performance_stats"][tournament_id] = new_stats.copy() if isinstance(new_stats, dict) else {}

        self.players[player_id] = player  # Not strictly needed for dict references, but for clarity.

        return {
            "success": True,
            "message": f"Performance stats updated for player {player_id} in tournament {tournament_id}."
        }

    def create_player(self, player_id: str, name: str, date_of_birth: str, team_id: str, sport_id: str, performance_stats: PerformanceStats = None) -> dict:
        """
        Add a new player record into the database.

        Args:
            player_id (str): Unique identifier of the player.
            name (str): Player's name.
            date_of_birth (str): Player's date of birth (format not enforced here).
            team_id (str): Identifier of the team to affiliate with.
            sport_id (str): Sport identifier.
            performance_stats (PerformanceStats, optional): Initial performance stats, defaults to empty dict.

        Returns:
            dict: {
                'success': True,
                'message': 'Player created successfully'
            }
            or
            {
                'success': False,
                'error': error_message
            }

        Constraints:
            - player_id must be unique.
            - team_id and sport_id must exist.
            - team and player must be for the same sport.
            - Each player may be affiliated with only one team per sport at a time.
        """
        # Check unique player_id
        if player_id in self.players:
            return {"success": False, "error": "Player ID already exists."}

        # Check if team_id exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}
        
        # Check if sport_id exists
        if sport_id not in self.sports:
            return {"success": False, "error": "Sport does not exist."}

        # Check if team is for the same sport
        team_info = self.teams[team_id]
        if team_info["sport_id"] != sport_id:
            return {"success": False, "error": "Team is not affiliated with the given sport."}

        # Default performance_stats
        if performance_stats is None:
            performance_stats = PerformanceStats()

        # Add player to self.players
        self.players[player_id] = {
            "player_id": player_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "team_id": team_id,
            "sport_id": sport_id,
            "performance_stats": performance_stats
        }

        # Optionally, update team's roster to include new player
        if player_id not in self.teams[team_id]["roster"]:
            self.teams[team_id]["roster"].append(player_id)

        return {"success": True, "message": "Player created successfully"}

    def create_team(self, team_id: str, name: str, sport_id: str, roster: list = None) -> dict:
        """
        Add a new team to the database.

        Args:
            team_id (str): Unique identifier for the team.
            name (str): Name of the team.
            sport_id (str): sport_id for the sport this team will compete in; must exist.
            roster (list, optional): List of player_ids initially on the team roster. Defaults to empty list.

        Returns:
            dict: {
                "success": True, "message": "Team created successfully."
            }
            or
            {
                "success": False, "error": <error_reason>
            }

        Constraints:
            - team_id must be unique.
            - sport_id must exist.
            - Each player in the roster must exist, must match sport_id, and must not already be on another team for this sport.
        """
        if team_id in self.teams:
            return {"success": False, "error": "Team ID already exists."}
        if sport_id not in self.sports:
            return {"success": False, "error": "Sport ID does not exist."}
        if roster is None:
            roster = []
        invalid_players = [pid for pid in roster if pid not in self.players]
        if invalid_players:
            return {"success": False, "error": f"Player(s) not found: {invalid_players}"}
        # Check sport match and solo team affiliation for this sport
        conflicted_players = []
        for pid in roster:
            player = self.players[pid]
            if player['sport_id'] != sport_id:
                conflicted_players.append(pid)
            elif player['team_id'] and player['team_id'] != team_id:
                # Check if player is already affiliated to another team in this sport
                # (player['team_id'] is not empty, and is not this team)
                # The constraint says only one team per sport!
                other_team = self.teams.get(player['team_id'])
                if other_team and other_team['sport_id'] == sport_id:
                    conflicted_players.append(pid)
        if conflicted_players:
            return {"success": False, "error": f"Conflicting affiliation or mismatched sport for player(s): {conflicted_players}"}
        # Create team
        self.teams[team_id] = {
            "team_id": team_id,
            "name": name,
            "sport_id": sport_id,
            "roster": roster.copy()
        }
        # Set each player's team_id to this team_id if not already set
        for pid in roster:
            self.players[pid]["team_id"] = team_id
        return {"success": True, "message": "Team created successfully."}

    def create_tournament(
        self,
        tournament_id: str,
        name: str,
        sport_id: str,
        participating_team_ids: list,
        participating_player_ids: list,
        date_range: str
    ) -> dict:
        """
        Add a new tournament to the database, enforcing uniqueness and entity validity.

        Args:
            tournament_id (str): Unique tournament identifier.
            name (str): Tournament name.
            sport_id (str): The sport's id for the tournament (must exist).
            participating_team_ids (list[str]): Team IDs participating in tournament (must exist, must match sport).
            participating_player_ids (list[str]): Player IDs participating (must exist, must be on a participating team or allowed as individual).
            date_range (str): Date range of the tournament.

        Returns:
            dict: { "success": True, "message": str } on success,
                  { "success": False, "error": str } on failure.

        Constraints:
            - tournament_id must be unique.
            - sport_id must exist.
            - Participating teams must exist and match sport_id.
            - Participating players must exist and their team must be one of participating teams, unless individual entry is allowed.
            - No duplicate IDs in lists.
        """
        if tournament_id in self.tournaments:
            return { "success": False, "error": f"Tournament ID '{tournament_id}' already exists" }

        if sport_id not in self.sports:
            return { "success": False, "error": f"Sport ID '{sport_id}' does not exist" }

        # Validate participating teams
        checked_team_ids = set()
        for team_id in participating_team_ids:
            if team_id in checked_team_ids:
                return { "success": False, "error": f"Duplicate team '{team_id}' in participating_team_ids" }
            checked_team_ids.add(team_id)
            team = self.teams.get(team_id)
            if not team:
                return { "success": False, "error": f"Participating team ID '{team_id}' does not exist" }
            if team["sport_id"] != sport_id:
                return { "success": False, "error": f"Team '{team_id}' does not match tournament sport_id '{sport_id}'" }

        # Validate participating players
        checked_player_ids = set()
        for player_id in participating_player_ids:
            if player_id in checked_player_ids:
                return { "success": False, "error": f"Duplicate player '{player_id}' in participating_player_ids" }
            checked_player_ids.add(player_id)
            player = self.players.get(player_id)
            if not player:
                return { "success": False, "error": f"Participating player ID '{player_id}' does not exist" }
            # If player is not unaffiliated, their team_id must be in the participating teams (or individual entry allowed)
            player_team_id = player.get("team_id")
            if player_team_id:
                if player_team_id not in participating_team_ids:
                    return { "success": False, "error": f"Player '{player_id}' is on team '{player_team_id}' which is not in participating_team_ids" }
            # else, consider it as individual entry possibility (allowed by rules)

        self.tournaments[tournament_id] = {
            "tournament_id": tournament_id,
            "name": name,
            "sport_id": sport_id,
            "participating_team_ids": list(participating_team_ids),
            "participating_player_ids": list(participating_player_ids),
            "date_range": date_range,
        }
        return { "success": True, "message": f"Tournament '{tournament_id}' created successfully" }

    def create_sport(self, sport_id: str, name: str, rules: str) -> dict:
        """
        Register a new sport in the database.

        Args:
            sport_id (str): Unique identifier for the sport.
            name (str): Name of the sport.
            rules (str): Rules or basic info about the sport.

        Returns:
            dict: {
                "success": True,
                "message": "Sport <sport_id> created."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., duplicate, invalid input)
            }

        Constraints:
            - sport_id must be unique.
            - All parameters must be non-empty strings.
        """

        # Validate input
        if not sport_id or not isinstance(sport_id, str):
            return {"success": False, "error": "Invalid or missing sport_id."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing name."}
        if not rules or not isinstance(rules, str):
            return {"success": False, "error": "Invalid or missing rules."}

        if sport_id in self.sports:
            return {"success": False, "error": "Sport with this id already exists."}

        sport_info = {
            "sport_id": sport_id,
            "name": name,
            "rules": rules
        }
        self.sports[sport_id] = sport_info

        return {"success": True, "message": f"Sport {sport_id} created."}


class SportsTeamManagementDatabase(BaseEnv):
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

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def get_sport_by_id(self, **kwargs):
        return self._call_inner_tool('get_sport_by_id', kwargs)

    def get_tournament_by_id(self, **kwargs):
        return self._call_inner_tool('get_tournament_by_id', kwargs)

    def get_player_team(self, **kwargs):
        return self._call_inner_tool('get_player_team', kwargs)

    def get_team_players(self, **kwargs):
        return self._call_inner_tool('get_team_players', kwargs)

    def get_player_tournaments(self, **kwargs):
        return self._call_inner_tool('get_player_tournaments', kwargs)

    def get_team_tournaments(self, **kwargs):
        return self._call_inner_tool('get_team_tournaments', kwargs)

    def get_sport_teams(self, **kwargs):
        return self._call_inner_tool('get_sport_teams', kwargs)

    def get_tournament_players(self, **kwargs):
        return self._call_inner_tool('get_tournament_players', kwargs)

    def get_tournament_teams(self, **kwargs):
        return self._call_inner_tool('get_tournament_teams', kwargs)

    def get_player_performance_stats(self, **kwargs):
        return self._call_inner_tool('get_player_performance_stats', kwargs)

    def get_sport_rules(self, **kwargs):
        return self._call_inner_tool('get_sport_rules', kwargs)

    def update_player_team_affiliation(self, **kwargs):
        return self._call_inner_tool('update_player_team_affiliation', kwargs)

    def update_team_roster(self, **kwargs):
        return self._call_inner_tool('update_team_roster', kwargs)

    def register_player_for_tournament(self, **kwargs):
        return self._call_inner_tool('register_player_for_tournament', kwargs)

    def register_team_for_tournament(self, **kwargs):
        return self._call_inner_tool('register_team_for_tournament', kwargs)

    def update_player_performance_stats(self, **kwargs):
        return self._call_inner_tool('update_player_performance_stats', kwargs)

    def create_player(self, **kwargs):
        return self._call_inner_tool('create_player', kwargs)

    def create_team(self, **kwargs):
        return self._call_inner_tool('create_team', kwargs)

    def create_tournament(self, **kwargs):
        return self._call_inner_tool('create_tournament', kwargs)

    def create_sport(self, **kwargs):
        return self._call_inner_tool('create_sport', kwargs)

