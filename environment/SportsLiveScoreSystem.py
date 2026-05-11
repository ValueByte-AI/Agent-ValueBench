# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class LeagueInfo(TypedDict):
    league_id: str
    name: str
    sport_type: str  # Fixed typo from "sport_typ"

class TeamInfo(TypedDict):
    team_id: str
    name: str
    league_id: str

class MatchInfo(TypedDict):
    match_id: str
    league_id: str
    team1_id: str
    team2_id: str
    status: str  # Should be one of: "scheduled", "live", "finished", "postponed"
    start_time: str
    live_score: str  # This could also be a more structured type
    ven: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for sports live score tracking.
        """

        # Leagues: {league_id: LeagueInfo}
        self.leagues: Dict[str, LeagueInfo] = {}
        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Constraints:
        # - A match can only have two teams associated at a time (team1_id, team2_id)
        # - The status of a match can only be among predefined states (e.g., "scheduled", "live", "finished", "postponed")
        # - Each team must belong to exactly one league
        # - A team's presence in a match must correspond to the correct league for the match

    def get_league_by_name(self, league_name: str) -> dict:
        """
        Retrieve league information and league_id by league name.

        Args:
            league_name (str): Name of the league to retrieve.

        Returns:
            dict: 
                - If found: {"success": True, "data": LeagueInfo}
                - If not found: {"success": False, "error": "League not found"}
                - If input invalid: {"success": False, "error": "Invalid league name"}

        Constraints:
            - League names must be compared exactly (case-sensitive).
            - Assumes league names are unique.
        """
        if not isinstance(league_name, str) or not league_name.strip():
            return {"success": False, "error": "Invalid league name"}
    
        for league in self.leagues.values():
            if league["name"] == league_name:
                return {"success": True, "data": league}
    
        return {"success": False, "error": "League not found"}

    def list_leagues(self) -> dict:
        """
        List all leagues in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LeagueInfo]
            }
            The list may be empty if no leagues are present.
        """
        leagues_list = list(self.leagues.values())
        return { "success": True, "data": leagues_list }

    def get_team_by_name(self, team_name: str) -> dict:
        """
        Retrieve a team's info and team_id by its name.

        Args:
            team_name (str): The name of the team to search for.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo  # The found team's info
            }
            or
            {
                "success": False,
                "error": "Team not found"
            }

        Notes:
            - Case-sensitive match on the team name.
            - Returns the first match if multiple teams share the name (assuming names are unique).
        """
        for team in self.teams.values():
            if team["name"] == team_name:
                return {"success": True, "data": team}
        return {"success": False, "error": "Team not found"}

    def list_teams_in_league(self, league_id: str) -> dict:
        """
        List all teams associated with a specific league.

        Args:
            league_id (str): The identifier of the league.

        Returns:
            dict: {
                "success": True,
                "data": List[TeamInfo],  # List of teams (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason: league does not exist
            }

        Constraints:
            - The league must exist in the system.
        """
        if league_id not in self.leagues:
            return { "success": False, "error": "League not found" }

        teams = [
            team_info
            for team_info in self.teams.values()
            if team_info["league_id"] == league_id
        ]
        return { "success": True, "data": teams }

    def list_matches_by_league_and_status(self, league_id: str, status: str) -> dict:
        """
        List all matches for a given league and status (e.g., all live matches in NFL).

        Args:
            league_id (str): The ID of the league to filter.
            status (str): The desired match status ("scheduled", "live", "finished", "postponed").

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of matches (may be empty if no matches)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - league_id must exist in self.leagues.
            - status must be one of the predefined valid statuses.
        """
        valid_statuses = {"scheduled", "live", "finished", "postponed"}

        if league_id not in self.leagues:
            return {"success": False, "error": "League does not exist"}

        if status not in valid_statuses:
            return {"success": False, "error": f"Invalid match status: {status}"}

        matches = [
            match for match in self.matches.values()
            if match["league_id"] == league_id and match["status"] == status
        ]

        return {"success": True, "data": matches}

    def list_matches_by_team(self, team_id: str) -> dict:
        """
        List all matches where the specified team participates (either as team1 or team2).

        Args:
            team_id (str): The identifier of the team.

        Returns:
            dict:
                - On success: {"success": True, "data": List[MatchInfo]}
                             (List may be empty if team has no matches)
                - On failure: {"success": False, "error": str}
                  (error reason, e.g., if team does not exist)

        Constraints:
            - The team_id must exist in the system.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team not found" }

        result = [
            match for match in self.matches.values()
            if match["team1_id"] == team_id or match["team2_id"] == team_id
        ]
        return { "success": True, "data": result }

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve all details of a match given its match_id.

        Args:
            match_id (str): The unique identifier of the match to retrieve.

        Returns:
            dict:
                success: True and data with MatchInfo if match exists,
                         otherwise success: False with an error message.
            Example success:
                {
                    "success": True,
                    "data": MatchInfo
                }
            Example failure:
                {
                    "success": False,
                    "error": "Match not found"
                }
        Constraints:
            - match_id must exist in the system.
        """
        match = self.matches.get(match_id)
        if match is None:
            return {"success": False, "error": "Match not found"}
        return {"success": True, "data": match}

    def get_match_live_score(self, match_id: str) -> dict:
        """
        Get the live score string for a specific match.

        Args:
            match_id (str): The ID of the match whose live score is requested.

        Returns:
            dict: {
                "success": True,
                "data": str  # The live score string (may be empty if not set)
            }
            or
            {
                "success": False,
                "error": str  # If match_id not found
            }
        Constraints:
            - match_id must refer to an existing match.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        # Return the live_score string (could be empty)
        return { "success": True, "data": match.get("live_score", "") }

    def list_live_scores_for_matches(self, match_ids: list[str]) -> dict:
        """
        Bulk retrieve live scores for a list of matches.

        Args:
            match_ids (List[str]): List of match IDs for which to fetch live scores.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": List[{"match_id": str, "live_score": str}]
                }
                On failure (if any match_id not found):
                {
                    "success": False,
                    "error": "The following match_ids do not exist: <list_as_string>"
                }

        Constraints:
            - Returns live scores for only existing match_ids.
            - If any match_id is invalid, returns error indicating which match_ids were invalid.
        """

        if not isinstance(match_ids, list):
            return { "success": False, "error": "Input match_ids must be a list of strings." }

        invalid_ids = [mid for mid in match_ids if mid not in self.matches]
        if invalid_ids:
            return {
                "success": False,
                "error": f"The following match_ids do not exist: {', '.join(invalid_ids)}"
            }
        result = [
            {
                "match_id": mid,
                "live_score": self.matches[mid].get("live_score", "")
            } for mid in match_ids
        ]
        return { "success": True, "data": result }

    def list_matches_filtered(self, filters: dict) -> dict:
        """
        Flexibly filter matches by arbitrary parameters such as league, team, and status.

        Args:
            filters (dict): Mapping of MatchInfo fields to values.
                Example: {"league_id": "L01", "status": "live", "team_id": "T10"}

                - 'team_id' will match if team is either team1 or team2 in the match.
                - Other keys must correspond to MatchInfo fields.

        Returns:
            dict:
                If successful:
                    { "success": True, "data": List[MatchInfo] }
                If filter key is invalid:
                    { "success": False, "error": "Invalid filter: <key>" }
    
        Constraints:
            - Filter keys must be among MatchInfo attributes or 'team_id'.
            - Returned matches must match all filter criteria (AND logic).
        """
        valid_match_keys = {
            "match_id", "league_id", "team1_id", "team2_id", "status", "start_time", "live_score", "ven"
        }
        filter_key_aliases = {"venue": "ven"}

        # Defensive: do not change the input dictionary (copy)
        filter_keys = list(filters.keys())
        for k in filter_keys:
            canonical_key = filter_key_aliases.get(k, k)
            if canonical_key not in valid_match_keys and canonical_key != "team_id":
                return { "success": False, "error": f"Invalid filter: {k}" }

        results = []
        for match in self.matches.values():
            match_ok = True
            for key, value in filters.items():
                canonical_key = filter_key_aliases.get(key, key)
                if canonical_key == "team_id":
                    # team_id must match either team1_id or team2_id
                    if value != match["team1_id"] and value != match["team2_id"]:
                        match_ok = False
                        break
                else:
                    if match.get(canonical_key) != value:
                        match_ok = False
                        break
            if match_ok:
                match_view = dict(match)
                if "ven" in match_view and "venue" not in match_view:
                    match_view["venue"] = match_view["ven"]
                results.append(match_view)

        return { "success": True, "data": results }

    def update_match_status(self, match_id: str, new_status: str) -> dict:
        """
        Change the status of a match, ensuring that the new status is one of:
        'scheduled', 'live', 'finished', or 'postponed'.

        Args:
            match_id (str): The unique ID of the match to update.
            new_status (str): The new status to set.

        Returns:
            dict: {
                'success': True,
                'message': str
            }
            or
            {
                'success': False,
                'error': str
            }

        Constraints:
            - The match specified by match_id must exist.
            - The new status must be one of the allowed states.
        """
        allowed_statuses = {"scheduled", "live", "finished", "postponed"}
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": "Invalid status value"}
        self.matches[match_id]["status"] = new_status
        return {"success": True, "message": "Match status updated successfully."}

    def update_match_score(self, match_id: str, live_score: str) -> dict:
        """
        Update the live score of a match.

        Args:
            match_id (str): The unique ID of the match whose score will be updated.
            live_score (str): The new live score to set for the match.

        Returns:
            dict: {
                "success": True,
                "message": "Live score updated for match <match_id>"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - match_id must exist in the system.
            - live_score must be a string (non-empty).
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }
        if not isinstance(live_score, str) or not live_score.strip():
            return { "success": False, "error": "Invalid live_score value" }

        # Update the score
        self.matches[match_id]["live_score"] = live_score
        return { "success": True, "message": f"Live score updated for match {match_id}" }

    def assign_teams_to_match(self, match_id: str, team1_id: str, team2_id: str) -> dict:
        """
        Change or set the team1_id and team2_id for the specified match,
        enforcing league/team assignment integrity constraints.

        Args:
            match_id (str): The ID of the match to update.
            team1_id (str): The ID of team 1 to assign.
            team2_id (str): The ID of team 2 to assign.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Teams assigned to match <match_id>." }
                - On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - Both teams and match must exist.
            - team1_id and team2_id must be different.
            - Both teams must belong to the same league as the match.
        """
        # Check match exists
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist." }
        # Check teams exist
        if team1_id not in self.teams:
            return { "success": False, "error": f"Team1 (ID: {team1_id}) does not exist." }
        if team2_id not in self.teams:
            return { "success": False, "error": f"Team2 (ID: {team2_id}) does not exist." }
        # Check they are different
        if team1_id == team2_id:
            return { "success": False, "error": "Cannot assign the same team to both slots of a match." }
    
        match_info = self.matches[match_id]
        match_league_id = match_info["league_id"]
        team1_league_id = self.teams[team1_id]["league_id"]
        team2_league_id = self.teams[team2_id]["league_id"]

        # Both teams must belong to the same league as the match
        if team1_league_id != match_league_id or team2_league_id != match_league_id:
            return { 
                "success": False, 
                "error": "Both teams must belong to the league associated with this match." 
            }

        # Update teams in the match
        match_info["team1_id"] = team1_id
        match_info["team2_id"] = team2_id
        return { "success": True, "message": f"Teams assigned to match {match_id}." }

    def create_match(
        self,
        match_id: str,
        league_id: str,
        team1_id: str,
        team2_id: str,
        status: str,
        start_time: str,
        live_score: str,
        ven: str
    ) -> dict:
        """
        Create a new match with provided details.
    
        Args:
            match_id (str): Unique identifier for the match.
            league_id (str): League identifier to which the match belongs.
            team1_id (str): First team's ID.
            team2_id (str): Second team's ID.
            status (str): Initial status, must be one of "scheduled", "live", "finished", "postponed".
            start_time (str): Scheduled start time.
            live_score (str): Initial score (can be empty or defaulted).
            ven (str): Venue information.
        
        Returns:
            dict: {
                "success": True,
                "message": "Match <match_id> created successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        
        Constraints:
            - match_id must be unique.
            - league_id must exist.
            - Both team1_id and team2_id must exist and be distinct.
            - Both teams must belong to the given league.
            - status must be one of allowed states.
        """
        allowed_status = {"scheduled", "live", "finished", "postponed"}

        if match_id in self.matches:
            return { "success": False, "error": "Match ID already exists" }
        if league_id not in self.leagues:
            return { "success": False, "error": "League does not exist" }
        if team1_id not in self.teams or team2_id not in self.teams:
            return { "success": False, "error": "One or both team IDs do not exist" }
        if team1_id == team2_id:
            return { "success": False, "error": "A match cannot have the same team playing both sides" }
        if self.teams[team1_id]['league_id'] != league_id or self.teams[team2_id]['league_id'] != league_id:
            return { "success": False, "error": "Both teams must belong to the specified league" }
        if status not in allowed_status:
            return { "success": False, "error": "Invalid match status" }
    
        self.matches[match_id] = {
            "match_id": match_id,
            "league_id": league_id,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "status": status,
            "start_time": start_time,
            "live_score": live_score,
            "ven": ven
        }

        return { "success": True, "message": f"Match {match_id} created successfully" }

    def update_match_time(self, match_id: str, start_time: str) -> dict:
        """
        Change the start time of a specified match.

        Args:
            match_id (str): The unique identifier of the match to update.
            start_time (str): The new start time. (Format not validated here.)

        Returns:
            dict: {
                "success": True,
                "message": "Match start time updated"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - match_id must exist in the system.
            - No time format enforcement and no restriction on status.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match ID does not exist"}

        self.matches[match_id]["start_time"] = start_time
        return {"success": True, "message": "Match start time updated"}

    def delete_match(self, match_id: str) -> dict:
        """
        Permanently remove a match from the system.

        Args:
            match_id (str): Unique identifier of the match to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Match <match_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Match not found."
            }

        Constraints:
            - The match must exist in the system in order to delete it.
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match not found." }
    
        del self.matches[match_id]
        return { "success": True, "message": f"Match {match_id} deleted." }


class SportsLiveScoreSystem(BaseEnv):
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

    def get_league_by_name(self, **kwargs):
        return self._call_inner_tool('get_league_by_name', kwargs)

    def list_leagues(self, **kwargs):
        return self._call_inner_tool('list_leagues', kwargs)

    def get_team_by_name(self, **kwargs):
        return self._call_inner_tool('get_team_by_name', kwargs)

    def list_teams_in_league(self, **kwargs):
        return self._call_inner_tool('list_teams_in_league', kwargs)

    def list_matches_by_league_and_status(self, **kwargs):
        return self._call_inner_tool('list_matches_by_league_and_status', kwargs)

    def list_matches_by_team(self, **kwargs):
        return self._call_inner_tool('list_matches_by_team', kwargs)

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def get_match_live_score(self, **kwargs):
        return self._call_inner_tool('get_match_live_score', kwargs)

    def list_live_scores_for_matches(self, **kwargs):
        return self._call_inner_tool('list_live_scores_for_matches', kwargs)

    def list_matches_filtered(self, **kwargs):
        return self._call_inner_tool('list_matches_filtered', kwargs)

    def update_match_status(self, **kwargs):
        return self._call_inner_tool('update_match_status', kwargs)

    def update_match_score(self, **kwargs):
        return self._call_inner_tool('update_match_score', kwargs)

    def assign_teams_to_match(self, **kwargs):
        return self._call_inner_tool('assign_teams_to_match', kwargs)

    def create_match(self, **kwargs):
        return self._call_inner_tool('create_match', kwargs)

    def update_match_time(self, **kwargs):
        return self._call_inner_tool('update_match_time', kwargs)

    def delete_match(self, **kwargs):
        return self._call_inner_tool('delete_match', kwargs)
