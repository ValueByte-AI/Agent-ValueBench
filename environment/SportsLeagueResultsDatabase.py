# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class OrganizationInfo(TypedDict):
    organization_id: str
    name: str

class TournamentInfo(TypedDict):
    tournament_id: str
    name: str
    organization_id: str

class SeasonInfo(TypedDict):
    season_id: str
    tournament_id: str
    year: int
    start_date: str
    end_date: str

class TeamInfo(TypedDict):
    team_id: str
    name: str
    organization_id: str

class MatchInfo(TypedDict):
    match_id: str
    tournament_id: str
    season_id: str
    date: str
    team1_id: str
    team2_id: str
    team1_score: int
    team2_score: int
    status: str
    winner_team_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}
        
        # Tournaments: {tournament_id: TournamentInfo}
        self.tournaments: Dict[str, TournamentInfo] = {}
        
        # Seasons: {season_id: SeasonInfo}
        self.seasons: Dict[str, SeasonInfo] = {}
        
        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}
        
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Constraints:
        # - Each match is associated with exactly one tournament and one season.
        # - A match must have two valid teams as participants.
        # - Queries for "last matches" are based on match date or a defined chronological order.
        # - Teams must belong to the organization hosting the tournament.

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve information for a specific organization by its ID.

        Args:
            organization_id (str): The unique identifier of the organization.

        Returns:
            dict: {
                "success": True,
                "data": OrganizationInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., organization not found.
            }

        Constraints:
            - The organization_id must exist in the database.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization not found" }
        return { "success": True, "data": self.organizations[organization_id] }

    def list_organizations(self) -> dict:
        """
        List all organizations in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo]  # List of all organizations (empty list if none exist)
            }
        """
        organizations_list = list(self.organizations.values())
        return { "success": True, "data": organizations_list }

    def get_tournament_by_id(self, tournament_id: str) -> dict:
        """
        Retrieve information for a specific tournament by its tournament_id.

        Args:
            tournament_id (str): The unique identifier of the tournament.

        Returns:
            dict:
                success (bool): True if tournament found, False otherwise.
                data (TournamentInfo): Tournament information, present if successful.
                error (str): Error message if tournament not found.

        Constraints:
            - Tournament with the given ID must exist.
        """
        tournament = self.tournaments.get(tournament_id)
        if tournament is None:
            return { "success": False, "error": "Tournament not found" }
        return { "success": True, "data": tournament }

    def list_tournaments_by_organization(self, organization_id: str) -> dict:
        """
        List tournaments belonging to a given organization.

        Args:
            organization_id (str): The ID of the organization whose tournaments to list.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[TournamentInfo]  # list (may be empty) of tournaments under the organization
                  }
                - On failure: {
                    "success": False,
                    "error": str  # explanation, e.g. organization does not exist
                  }

        Constraints:
            - The provided organization_id must exist in the database.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        tournaments = [
            tournament_info
            for tournament_info in self.tournaments.values()
            if tournament_info["organization_id"] == organization_id
        ]
        return {"success": True, "data": tournaments}

    def get_season_by_id(self, season_id: str) -> dict:
        """
        Retrieve information for a specific season by its unique ID.

        Args:
            season_id (str): The ID of the season to retrieve.

        Returns:
            dict: {
                'success': True,
                'data': SeasonInfo
            }
            or
            {
                'success': False,
                'error': "Season not found"
            }
        """
        season = self.seasons.get(season_id)
        if not season:
            return { "success": False, "error": "Season not found" }
        return { "success": True, "data": season }

    def list_seasons_by_tournament(self, tournament_id: str) -> dict:
        """
        List all seasons for a given tournament.

        Args:
            tournament_id (str): The unique identifier of the tournament.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": List[SeasonInfo]  # possibly empty
                }
                Failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The tournament_id must exist in self.tournaments.
            - If no seasons, returns an empty list.
        """
        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament does not exist" }

        result = [
            season for season in self.seasons.values()
            if season["tournament_id"] == tournament_id
        ]
        return { "success": True, "data": result }

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve information for a specific team by team ID.

        Args:
            team_id (str): The unique identifier for the team.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo
            } on success; or
            {
                "success": False,
                "error": "Team not found"
            } if the team does not exist.

        Constraints:
            - Team ID must exist in self.teams.
        """
        team_info = self.teams.get(team_id)
        if team_info is None:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team_info }

    def list_teams_by_organization(self, organization_id: str) -> dict:
        """
        List all teams under the specified organization.

        Args:
            organization_id (str): The unique identifier of the organization.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TeamInfo],  # List of team info dicts (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # Error message (e.g., organization does not exist)
                    }

        Constraints:
            - The provided organization_id must exist in the database.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        teams = [
            team_info for team_info in self.teams.values()
            if team_info["organization_id"] == organization_id
        ]
        return { "success": True, "data": teams }

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve full details for a specific match by match ID.

        Args:
            match_id (str): The unique identifier of the match to retrieve.

        Returns:
            dict: 
                - On success: { "success": True, "data": MatchInfo }
                - On failure: { "success": False, "error": "Match not found" }

        Constraints:
            - match_id must exist in the self.matches dictionary.
        """
        match = self.matches.get(match_id)
        if match is None:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match }

    def list_matches_by_tournament_and_season(self, tournament_id: str, season_id: str) -> dict:
        """
        List all matches for a specified tournament and season.

        Args:
            tournament_id (str): The ID of the tournament.
            season_id (str): The ID of the season.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[MatchInfo]  # List of matches (can be empty if none found)
                    }
                - On failure (tournament or season not found):
                    {
                        "success": False,
                        "error": "Tournament or season not found"
                    }

        Constraints:
            - Both the specified tournament_id and season_id must exist.
            - The returned matches are all those whose tournament_id and season_id both match the inputs.
        """
        if tournament_id not in self.tournaments or season_id not in self.seasons:
            return {"success": False, "error": "Tournament or season not found"}

        result = [
            match_info for match_info in self.matches.values()
            if match_info["tournament_id"] == tournament_id and match_info["season_id"] == season_id
        ]
        return {"success": True, "data": result}

    def list_last_n_matches_by_tournament_and_season(self, tournament_id: str, season_id: str, n: int) -> dict:
        """
        Retrieve the chronologically last N matches (sorted by date descending) for a specified tournament and season.

        Args:
            tournament_id (str): The tournament to filter matches.
            season_id (str): The season to filter matches.
            n (int): Number of recent matches to return.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]  # At most N matches, sorted by date descending
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        Constraints:
            - tournament_id and season_id must exist.
            - n must be a positive integer (>0).
            - Will return as many results as exist, up to n (including 0).
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}
        if season_id not in self.seasons:
            return {"success": False, "error": "Season does not exist"}
        if not isinstance(n, int) or n <= 0:
            return {"success": False, "error": "Parameter n must be a positive integer"}

        # Collect all matches with desired tournament and season
        filtered_matches = [
            match for match in self.matches.values()
            if match["tournament_id"] == tournament_id and match["season_id"] == season_id
        ]

        # Sort by date descending (ISO format assumed: 'YYYY-MM-DD')
        filtered_matches.sort(key=lambda m: m["date"], reverse=True)

        last_n_matches = filtered_matches[:n]

        return {"success": True, "data": last_n_matches}

    def list_matches_for_team_in_season(self, team_id: str, season_id: str) -> dict:
        """
        List all matches involving a given team in a specified season.

        Args:
            team_id (str): The team's unique identifier.
            season_id (str): The season's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]  # List of matches where given team played in given season (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason: e.g., team or season does not exist
            }

        Constraints:
            - team_id must exist in the database.
            - season_id must exist in the database.
            - Only matches in the specified season involving the specified team are included.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }
        if season_id not in self.seasons:
            return { "success": False, "error": "Season does not exist" }

        matches = [
            match_info for match_info in self.matches.values()
            if match_info["season_id"] == season_id and (
                match_info["team1_id"] == team_id or match_info["team2_id"] == team_id
            )
        ]

        return { "success": True, "data": matches }

    def get_match_participants(self, match_id: str) -> dict:
        """
        Retrieve the teams that participated in a particular match.

        Args:
            match_id (str): The ID of the match whose participants are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "team1": TeamInfo,
                    "team2": TeamInfo
                }
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - match_id must exist in the database.
            - Both team1_id and team2_id must correspond to valid teams in the system.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}
    
        team1_id = match.get("team1_id")
        team2_id = match.get("team2_id")
        team1 = self.teams.get(team1_id)
        team2 = self.teams.get(team2_id)
        if not team1 or not team2:
            return {"success": False, "error": "One or both participating teams not found"}

        return {
            "success": True,
            "data": {
                "team1": team1,
                "team2": team2
            }
        }

    def get_match_result(self, match_id: str) -> dict:
        """
        Retrieve the score, status, and winner for a specific match.

        Args:
            match_id (str): Unique identifier of the match.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "match_id": str,
                    "team1_id": str,
                    "team2_id": str,
                    "team1_score": int,
                    "team2_score": int,
                    "status": str,
                    "winner_team_id": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Match not found"
            }

        Constraints:
            - The match with match_id must exist.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}
        result = {
            "match_id": match["match_id"],
            "team1_id": match["team1_id"],
            "team2_id": match["team2_id"],
            "team1_score": match["team1_score"],
            "team2_score": match["team2_score"],
            "status": match["status"],
            "winner_team_id": match["winner_team_id"],
        }
        return {"success": True, "data": result}

    def add_match(
        self,
        match_id: str,
        tournament_id: str,
        season_id: str,
        date: str,
        team1_id: str,
        team2_id: str,
        team1_score: int,
        team2_score: int,
        status: str,
        winner_team_id: str = ""
    ) -> dict:
        """
        Create a new match record.

        Args:
            match_id (str): Unique identifier for the match.
            tournament_id (str): ID of the tournament; must exist.
            season_id (str): ID of the season; must exist and belong to tournament.
            date (str): Date of the match.
            team1_id (str): ID of the first team; must exist; must belong to org of tournament.
            team2_id (str): ID of the second team; must exist, be different, also same org.
            team1_score (int): Score for team1.
            team2_score (int): Score for team2.
            status (str): Status of the match.
            winner_team_id (str, optional): Winning team. Must be team1_id or team2_id or empty.

        Returns:
            dict: Success or error with explanation.

        Constraints:
            - match_id must be unique
            - tournament_id must exist
            - season_id must exist and belong to tournament_id
            - teams must exist, be different, and belong to organization of tournament
            - winner_team_id (if provided and nonempty) must be one of the participants
        """
        # 1. Check unique match_id
        if match_id in self.matches:
            return {"success": False, "error": "Match ID already exists"}

        # 2. Check tournament exists
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament does not exist"}

        # 3. Check season exists and belongs to the tournament
        season = self.seasons.get(season_id)
        if not season:
            return {"success": False, "error": "Season does not exist"}
        if season["tournament_id"] != tournament_id:
            return {"success": False, "error": "Season does not belong to the specified tournament"}

        # 4. Check teams exist and are different
        team1 = self.teams.get(team1_id)
        team2 = self.teams.get(team2_id)
        if not team1 or not team2:
            return {"success": False, "error": "One or both teams do not exist"}
        if team1_id == team2_id:
            return {"success": False, "error": "A match must have two different teams"}

        # 5. Check teams are from the correct organization
        org_id = tournament["organization_id"]
        if team1["organization_id"] != org_id or team2["organization_id"] != org_id:
            return {"success": False, "error": "Both teams must belong to the tournament's organization"}

        # 6. Check winner_team_id is valid
        if winner_team_id and winner_team_id not in (team1_id, team2_id):
            return {"success": False, "error": "Winner team must be one of the participating teams, or empty"}

        # 7. Assemble and add match
        match_info = {
            "match_id": match_id,
            "tournament_id": tournament_id,
            "season_id": season_id,
            "date": date,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "status": status,
            "winner_team_id": winner_team_id
        }
        self.matches[match_id] = match_info
        return {"success": True, "message": "Match added successfully"}

    def update_match_result(
        self, 
        match_id: str, 
        team1_score: int, 
        team2_score: int, 
        status: str, 
        winner_team_id: str
    ) -> dict:
        """
        Update the scores, status, and winner for an existing match.

        Args:
            match_id (str): Identifier of the match to update.
            team1_score (int): New score for team 1 (must be >= 0).
            team2_score (int): New score for team 2 (must be >= 0).
            status (str): New status for the match (e.g., "completed").
            winner_team_id (str): Team id of the winner (must be either team1_id, team2_id, or "" for draw/undecided).

        Returns:
            dict: 
                - On success:
                    { "success": True, "message": "Match result updated" }
                - On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - The match must exist by match_id.
            - The winner_team_id must be team1_id, team2_id, or "".
            - Scores must be non-negative integers.
        """
        # 1. Check that the match exists
        if match_id not in self.matches:
            return { "success": False, "error": "Match ID does not exist" }
        match = self.matches[match_id]

        # 2. Validate winner_team_id
        accepted_winner_ids = [match["team1_id"], match["team2_id"], ""]
        if winner_team_id not in accepted_winner_ids:
            return { "success": False, "error": "winner_team_id must be one of: team1_id, team2_id, or ''" }

        # 3. Validate scores are int and non-negative
        if not (isinstance(team1_score, int) and isinstance(team2_score, int)):
            return { "success": False, "error": "Scores must be integers" }
        if team1_score < 0 or team2_score < 0:
            return { "success": False, "error": "Scores must be non-negative" }

        # 4. Update match info
        match["team1_score"] = team1_score
        match["team2_score"] = team2_score
        match["status"] = status
        match["winner_team_id"] = winner_team_id

        return { "success": True, "message": "Match result updated" }

    def delete_match(self, match_id: str) -> dict:
        """
        Remove a match from the database.

        Args:
            match_id (str): The unique identifier of the match to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Match <match_id> deleted"
            }
            or
            {
                "success": False,
                "error": "Match not found"
            }

        Constraints:
            - The match must exist in the database.
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match not found" }

        del self.matches[match_id]
        return { "success": True, "message": f"Match {match_id} deleted" }

    def add_team(self, team_id: str, name: str, organization_id: str) -> dict:
        """
        Add a new team to the specified organization.

        Args:
            team_id (str): The unique ID for the new team.
            name (str): The team's name.
            organization_id (str): The organization to which this team should be added.

        Returns:
            dict: 
                { "success": True, "message": "Team <team_id> added to organization <organization_id>." }
                OR
                { "success": False, "error": "<reason>" }

        Constraints:
            - team_id must be unique in the database.
            - organization_id must exist in organizations.
        """
        if team_id in self.teams:
            return { "success": False, "error": "Team ID already exists." }
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
    
        team_info: TeamInfo = {
            "team_id": team_id,
            "name": name,
            "organization_id": organization_id
        }
        self.teams[team_id] = team_info
        return { "success": True, "message": f"Team {team_id} added to organization {organization_id}." }

    def update_team_info(self, team_id: str, name: str = None, organization_id: str = None) -> dict:
        """
        Edit the details of a team, such as its name and/or organization affiliation.

        Args:
            team_id (str): Unique identifier of the team to update.
            name (str, optional): New name for the team.
            organization_id (str, optional): New organization ID to affiliate the team with.

        Returns:
            dict: 
                On success: { "success": True, "message": "Team info updated" }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - team_id must exist.
            - If organization_id is provided, it must correspond to an existing organization.
            - At least one of name or organization_id must be provided.
        """
        # Check that the team exists
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }
        # Check at least one field is supplied
        if name is None and organization_id is None:
            return { "success": False, "error": "No update information provided" }
        # If organization_id is to be updated, ensure it exists
        if organization_id is not None and organization_id not in self.organizations:
            return { "success": False, "error": "Target organization does not exist" }
        # Perform updates
        if name is not None:
            self.teams[team_id]["name"] = name
        if organization_id is not None:
            self.teams[team_id]["organization_id"] = organization_id
        return { "success": True, "message": "Team info updated" }

    def add_tournament(self, tournament_id: str, name: str, organization_id: str) -> dict:
        """
        Add a new tournament to an organization.

        Args:
            tournament_id (str): Unique identifier for the new tournament.
            name (str): Name of the tournament.
            organization_id (str): ID of the organization the tournament belongs to.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Tournament <tournament_id> added to organization <organization_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure (organization does not exist, or id already exists)."
                    }
        Constraints:
            - Tournament ID must be unique.
            - Organization ID must exist.
        """
        if tournament_id in self.tournaments:
            return {"success": False, "error": "Tournament id already exists."}

        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist."}

        self.tournaments[tournament_id] = {
            "tournament_id": tournament_id,
            "name": name,
            "organization_id": organization_id,
        }

        return {
            "success": True,
            "message": f"Tournament {tournament_id} added to organization {organization_id}."
        }

    def add_season(
        self,
        season_id: str,
        tournament_id: str,
        year: int,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Create a new season for a tournament.

        Args:
            season_id (str): Unique identifier for the season (must not exist).
            tournament_id (str): ID of the tournament to which the season belongs (must exist).
            year (int): The year of the season.
            start_date (str): Start date of the season.
            end_date (str): End date of the season.

        Returns:
            dict: {
                "success": True,
                "message": "Season added successfully"
            } on success, or
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - season_id must be unique (not already used).
            - tournament_id must exist.
        """

        if season_id in self.seasons:
            return { "success": False, "error": "Season ID already exists" }

        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament ID does not exist" }

        season_info = {
            "season_id": season_id,
            "tournament_id": tournament_id,
            "year": year,
            "start_date": start_date,
            "end_date": end_date
        }
        self.seasons[season_id] = season_info

        return { "success": True, "message": "Season added successfully" }

    def update_match_participants(self, match_id: str, team1_id: str, team2_id: str) -> dict:
        """
        Change which teams are participating in a specific match.

        Args:
            match_id (str): The ID of the match to update.
            team1_id (str): The new team 1 ID.
            team2_id (str): The new team 2 ID.

        Returns:
            dict: {
                "success": True,
                "message": "Match participants updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - match_id must exist
            - team1_id and team2_id must exist and must be different
            - Both teams must belong to the organization hosting the tournament for this match
        """
        # Check match exists
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match does not exist."}
    
        # Check teams exist
        team1 = self.teams.get(team1_id)
        team2 = self.teams.get(team2_id)
        if not team1:
            return {"success": False, "error": f"Team1 (id={team1_id}) does not exist."}
        if not team2:
            return {"success": False, "error": f"Team2 (id={team2_id}) does not exist."}
        if team1_id == team2_id:
            return {"success": False, "error": "A match must have two different teams."}
    
        # Tournament for this match
        tournament_id = match["tournament_id"]
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament for match does not exist."}
        org_id = tournament["organization_id"]
    
        # Teams must belong to hosting organization
        if team1["organization_id"] != org_id:
            return {
                "success": False,
                "error": f"Team1 (id={team1_id}) does not belong to the tournament's organization."
            }
        if team2["organization_id"] != org_id:
            return {
                "success": False,
                "error": f"Team2 (id={team2_id}) does not belong to the tournament's organization."
            }

        # Apply change
        match["team1_id"] = team1_id
        match["team2_id"] = team2_id
        # Optionally clear winner_team_id and scores if they are no longer valid
        match["winner_team_id"] = ""
        match["team1_score"] = 0
        match["team2_score"] = 0

        return {
            "success": True,
            "message": f"Match {match_id} participants updated to {team1_id} and {team2_id}."
        }

    def correct_match_date(self, match_id: str, new_date: str) -> dict:
        """
        Modify the date record of an existing match.

        Args:
            match_id (str): The unique identifier of the match to update.
            new_date (str): The new date to assign to the match (expected 'YYYY-MM-DD', but no full validation).

        Returns:
            dict: {
                "success": True,
                "message": "Match date updated successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The match with match_id must exist.
            - No required validation of date format unless specified. If 'new_date' is empty, fail.
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }
        if not isinstance(new_date, str) or not new_date:
            return { "success": False, "error": "Invalid or empty new_date provided" }

        self.matches[match_id]['date'] = new_date
        return { "success": True, "message": "Match date updated successfully" }


class SportsLeagueResultsDatabase(BaseEnv):
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

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_organizations(self, **kwargs):
        return self._call_inner_tool('list_organizations', kwargs)

    def get_tournament_by_id(self, **kwargs):
        return self._call_inner_tool('get_tournament_by_id', kwargs)

    def list_tournaments_by_organization(self, **kwargs):
        return self._call_inner_tool('list_tournaments_by_organization', kwargs)

    def get_season_by_id(self, **kwargs):
        return self._call_inner_tool('get_season_by_id', kwargs)

    def list_seasons_by_tournament(self, **kwargs):
        return self._call_inner_tool('list_seasons_by_tournament', kwargs)

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def list_teams_by_organization(self, **kwargs):
        return self._call_inner_tool('list_teams_by_organization', kwargs)

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def list_matches_by_tournament_and_season(self, **kwargs):
        return self._call_inner_tool('list_matches_by_tournament_and_season', kwargs)

    def list_last_n_matches_by_tournament_and_season(self, **kwargs):
        return self._call_inner_tool('list_last_n_matches_by_tournament_and_season', kwargs)

    def list_matches_for_team_in_season(self, **kwargs):
        return self._call_inner_tool('list_matches_for_team_in_season', kwargs)

    def get_match_participants(self, **kwargs):
        return self._call_inner_tool('get_match_participants', kwargs)

    def get_match_result(self, **kwargs):
        return self._call_inner_tool('get_match_result', kwargs)

    def add_match(self, **kwargs):
        return self._call_inner_tool('add_match', kwargs)

    def update_match_result(self, **kwargs):
        return self._call_inner_tool('update_match_result', kwargs)

    def delete_match(self, **kwargs):
        return self._call_inner_tool('delete_match', kwargs)

    def add_team(self, **kwargs):
        return self._call_inner_tool('add_team', kwargs)

    def update_team_info(self, **kwargs):
        return self._call_inner_tool('update_team_info', kwargs)

    def add_tournament(self, **kwargs):
        return self._call_inner_tool('add_tournament', kwargs)

    def add_season(self, **kwargs):
        return self._call_inner_tool('add_season', kwargs)

    def update_match_participants(self, **kwargs):
        return self._call_inner_tool('update_match_participants', kwargs)

    def correct_match_date(self, **kwargs):
        return self._call_inner_tool('correct_match_date', kwargs)

