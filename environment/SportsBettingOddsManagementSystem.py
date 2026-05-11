# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from collections import defaultdict



class MatchInfo(TypedDict):
    match_id: str
    league_id: str
    sport_type: str
    start_time: str
    teams: List[str]
    sta: str  # status

class LeagueInfo(TypedDict):
    league_id: str
    league_name: str
    country: str
    sport_typ: str  # sport_type

class OddsInfo(TypedDict):
    match_id: str
    market_type: str
    selection: str
    odds_value: float
    provider: str
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing sports betting odds, matches, and leagues.
        """

        # Matches: {match_id: MatchInfo}
        # Derived from entity 'Match' with attributes (match_id, league_id, sport_type, start_time, teams, sta)
        self.matches: Dict[str, MatchInfo] = {}

        # Leagues: {league_id: LeagueInfo}
        # Derived from entity 'League' with attributes (league_id, league_name, country, sport_typ)
        self.leagues: Dict[str, LeagueInfo] = {}

        # Odds: List[OddsInfo]
        # Derived from entity 'Odds' with attributes (match_id, market_type, selection, odds_value, provider, timestamp)
        self.odds: List[OddsInfo] = []

        # Constraints:
        # - Odds must be linked to existing matches (referential integrity).
        # - Matches must be linked to a valid league.
        # - Only the latest odds per match/market/provider are returned for queries about "latest odds".
        # - Each match may have odds for multiple markets and selections (e.g., home win, draw, away win).

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve the details of a match given a match_id.

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict: {
                "success": True,
                "data": MatchInfo  # The match record
            }
            OR
            {
                "success": False,
                "error": str  # Error message if match not found
            }

        Constraints:
            - The match_id must exist in the system (referential integrity).
        """

        if match_id not in self.matches:
            return {"success": False, "error": "Match not found"}
        return {"success": True, "data": self.matches[match_id]}

    def list_matches_by_league(self, league_id: str) -> dict:
        """
        List all matches that belong to the given league_id.

        Args:
            league_id (str): The unique identifier of the league.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]   # list of matches (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "League not found"
            }

        Constraints:
            - league_id must correspond to an existing league.
        """
        if league_id not in self.leagues:
            return {"success": False, "error": "League not found"}

        matches = [
            match_info
            for match_info in self.matches.values()
            if match_info["league_id"] == league_id
        ]

        return {"success": True, "data": matches}

    def get_league_by_id(self, league_id: str) -> dict:
        """
        Retrieve league information by its unique league_id.

        Args:
            league_id (str): The unique identifier for the league.

        Returns:
            dict: {
                "success": True,
                "data": LeagueInfo
            }
            or
            {
                "success": False,
                "error": "League ID not found"
            }

        Constraints:
            - The given league_id must exist in the system.
        """
        league = self.leagues.get(league_id)
        if league is None:
            return {"success": False, "error": "League ID not found"}
        return {"success": True, "data": league}

    def get_league_by_name_and_country(self, league_name: str, country: str) -> dict:
        """
        Retrieve league info by league_name and country.

        Args:
            league_name (str): The name of the league (must match exactly).
            country (str): The country name (must match exactly).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": LeagueInfo  # Matching league info
                    }
                On failure:
                    {
                        "success": False,
                        "error": "League not found"
                    }

        Constraints:
            - league_name and country must both match for the same league.
        """
        for league in self.leagues.values():
            if league["league_name"] == league_name and league["country"] == country:
                return { "success": True, "data": league }
        return { "success": False, "error": "League not found" }

    def list_leagues_by_sport_and_country(self, sport_type: str = None, country: str = None) -> dict:
        """
        List leagues filtered by sport_type and/or country.

        Args:
            sport_type (str, optional): Sport type to filter by. If None, do not filter on sport_type.
            country (str, optional): Country to filter by. If None, do not filter on country.

        Returns:
            dict: {
                "success": True,
                "data": List[LeagueInfo],  # Filtered (possibly empty) list of leagues
            }

        Constraints:
            - If both arguments are None, all leagues are returned.
            - Filtering is an AND condition if both are specified.
            - No error is raised if no leagues match; data will be an empty list.
        """
        leagues = list(self.leagues.values())
        if sport_type is not None:
            leagues = [lg for lg in leagues if lg.get("sport_typ") == sport_type]
        if country is not None:
            leagues = [lg for lg in leagues if lg.get("country") == country]
        return { "success": True, "data": leagues }

    def get_matches_by_league_name_and_country(self, league_name: str, country: str) -> dict:
        """
        List all matches in a league specified by league_name and country.

        Args:
            league_name (str): The name of the league (e.g., "Serie A").
            country (str): The country of the league (e.g., "Brazil").

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]  # All matches in the specified league (may be empty if no matches)
            }
            or
            {
                "success": False,
                "error": str  # If league does not exist
            }

        Constraints:
            - Matches returned only if league exists for both league_name and country.
            - Multiple leagues with same name and country are supported.
            - If no matches are found, data is an empty list.
        """
        # Find all leagues matching name and country
        matching_league_ids = [
            league["league_id"]
            for league in self.leagues.values()
            if league["league_name"] == league_name and league["country"] == country
        ]

        if not matching_league_ids:
            return {
                "success": False,
                "error": "No league found with the specified name and country"
            }

        # Get all matches with these league_ids
        result = [
            match for match in self.matches.values()
            if match["league_id"] in matching_league_ids
        ]

        return {
            "success": True,
            "data": result
        }

    def get_latest_odds_for_match(self, match_id: str) -> dict:
        """
        Retrieve the latest odds entries for a given match_id, for all markets and providers.

        Args:
            match_id (str): The match identifier to query odds for.

        Returns:
            dict: {
                "success": True,
                "data": List[OddsInfo]  # May be empty if no odds found for this match
            }
            or
            {
                "success": False,
                "error": str  # If match does not exist
            }

        Constraints:
            - Only the latest odds per match/market_type/selection/provider are returned.
            - match_id must correspond to an existing match.
        """
        # Check referential integrity
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}


        # Group: (market_type, selection, provider) : latest OddsInfo
        latest_odds = {}

        for odds in self.odds:
            if odds["match_id"] != match_id:
                continue
            group_key = (odds["market_type"], odds["selection"], odds["provider"])
            # Always pick the one with latest timestamp
            existing = latest_odds.get(group_key)
            if (existing is None or odds["timestamp"] > existing["timestamp"]):
                latest_odds[group_key] = odds

        result = list(latest_odds.values())

        return {"success": True, "data": result}

    def get_latest_odds_for_match_market(self, match_id: str, market_type: str) -> dict:
        """
        Retrieve the latest (by timestamp) odds for a specific match and market_type, for all providers and selections.

        Args:
            match_id (str): Identifier of the match.
            market_type (str): Betting market type (e.g., "1X2", "Over/Under").

        Returns:
            dict: If success:
                {
                    "success": True,
                    "data": List[OddsInfo]  # Latest odds per (provider, selection)
                }
                If failure:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - match_id must exist.
            - Only the latest odds per (provider, selection) (by timestamp) are returned.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}

        # Filter odds with matching match_id and market_type
        filtered_odds = [
            o for o in self.odds
            if o["match_id"] == match_id and o["market_type"] == market_type
        ]

        # Only the latest odds per (provider, selection)
        odds_latest = {}
        for o in filtered_odds:
            key = (o["provider"], o["selection"])
            # Parse timestamp as comparable string, assuming ISO8601 or similar sortable format
            if key not in odds_latest or o["timestamp"] > odds_latest[key]["timestamp"]:
                odds_latest[key] = o

        latest_odds_list = list(odds_latest.values())

        return {"success": True, "data": latest_odds_list}

    def get_latest_odds_for_match_market_provider(
        self, match_id: str, market_type: str, provider: str
    ) -> dict:
        """
        Retrieve the latest odds entry for a specific match, market_type, and provider.

        Args:
            match_id (str): Identifier for the match.
            market_type (str): Betting market (e.g., 'Winner', 'Draw', etc).
            provider (str): Odds provider's name.

        Returns:
            dict: {
                "success": True,
                "data": OddsInfo,  # The latest odds entry matching criteria
            }
            or
            {
                "success": False,
                "error": str  # e.g. if not found or invalid match_id
            }

        Constraints:
            - match_id must exist in self.matches (referential integrity).
            - Only the odds with the latest timestamp per match/market_type/provider are returned.
        """
        if match_id not in self.matches:
            return { "success": False, "error": "match_id does not exist" }

        # Filter odds that match all three criteria
        relevant_odds = [
            o for o in self.odds
            if o["match_id"] == match_id and o["market_type"] == market_type and o["provider"] == provider
        ]
        if not relevant_odds:
            return { "success": False, "error": "No odds entry found for the specified match, market, and provider" }

        # Find the odds with the latest timestamp (assuming lexicographic comparison is valid for timestamps)
        latest_odds = max(relevant_odds, key=lambda o: o["timestamp"])

        return { "success": True, "data": latest_odds }

    def list_odds_for_match_all_versions(self, match_id: str) -> dict:
        """
        List all historical odds entries (not just latest) for a match, across all markets and providers.

        Args:
            match_id (str): Identifier of the match to fetch odds history for.

        Returns:
            dict: {
                "success": True,
                "data": List[OddsInfo],  # List of all matching odds entries (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Match does not exist"
            }

        Constraints:
            - odds must be linked to existing matches (referential integrity).
            - If match_id does not exist, return error.
            - Returns all versions (not just latest) for all markets/providers.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}

        result = [
            odds_entry
            for odds_entry in self.odds
            if odds_entry["match_id"] == match_id
        ]
        return {"success": True, "data": result}

    def get_match_status(self, match_id: str) -> dict:
        """
        Retrieve the current status ('sta') of a match.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status value (e.g., scheduled, ongoing, finished)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, such as "Match not found"
            }

        Constraints:
            - The match_id must exist in the environment. Returns error if not found.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}
    
        return {"success": True, "data": match["sta"]}

    def add_match(
        self,
        match_id: str,
        league_id: str,
        sport_type: str,
        start_time: str,
        teams: list,
        sta: str,
    ) -> dict:
        """
        Add a new match to the system and link it to a valid league.

        Args:
            match_id (str): Unique identifier for the match (must not already exist).
            league_id (str): The league the match belongs to (must exist).
            sport_type (str): Type of sport.
            start_time (str): Start time of the match.
            teams (List[str]): List of teams involved in the match (typically length 2).
            sta (str): Status of the match.

        Returns:
            dict: 
                On success: { "success": True, "message": "Match <match_id> added to league <league_id>." }
                On error:   { "success": False, "error": "Error reason" }

        Constraints:
            - match_id must be unique.
            - league_id must exist.
        """
        # Check match_id uniqueness.
        if match_id in self.matches:
            return { "success": False, "error": f"Match ID '{match_id}' already exists." }

        # Check league_id validity.
        if league_id not in self.leagues:
            return { "success": False, "error": f"League ID '{league_id}' does not exist." }

        # Basic validation for teams field
        if not isinstance(teams, list) or not all(isinstance(t, str) for t in teams) or len(teams) < 2:
            return { "success": False, "error": "Teams should be a list of at least two team names (str)." }

        match_info: MatchInfo = {
            "match_id": match_id,
            "league_id": league_id,
            "sport_type": sport_type,
            "start_time": start_time,
            "teams": teams,
            "sta": sta,
        }
        self.matches[match_id] = match_info

        return {
            "success": True,
            "message": f"Match '{match_id}' added to league '{league_id}'."
        }

    def add_league(self, league_id: str, league_name: str, country: str, sport_typ: str) -> dict:
        """
        Add a new league to the system.

        Args:
            league_id (str): Unique identifier for the league.
            league_name (str): Name of the league.
            country (str): Country in which the league is based.
            sport_typ (str): Sport type associated with the league.

        Returns:
            dict: 
                On success: { "success": True, "message": "League <league_id> added." }
                On failure: { "success": False, "error": "reason for failure" }

        Constraints:
            - league_id must be unique.
            - All fields must be non-empty strings.
        """
        # Basic input validation
        if not all(isinstance(arg, str) and arg.strip() for arg in [league_id, league_name, country, sport_typ]):
            return { "success": False, "error": "All fields must be non-empty strings." }

        if league_id in self.leagues:
            return { "success": False, "error": f"League ID '{league_id}' already exists." }

        league_info = {
            "league_id": league_id,
            "league_name": league_name,
            "country": country,
            "sport_typ": sport_typ
        }

        self.leagues[league_id] = league_info

        return { "success": True, "message": f"League '{league_id}' added." }

    def add_odds_entry(
        self,
        match_id: str,
        market_type: str,
        selection: str,
        odds_value: float,
        provider: str,
        timestamp: str
    ) -> dict:
        """
        Insert a new odds entry for a specified match.
        Ensures referential integrity: the match must exist.

        Args:
            match_id (str): ID of the match (must exist)
            market_type (str): The betting market (e.g., '1X2')
            selection (str): The selection/outcome (e.g., 'home win')
            odds_value (float): Odds value for this entry
            provider (str): Name/id of the odds provider
            timestamp (str): Timestamp for this odds entry

        Returns:
            dict: 
                If success:
                    {"success": True, "message": "Odds entry added for match <match_id>."}
                If failure (e.g. match does not exist):
                    {"success": False, "error": "Match does not exist for match_id <match_id>."}
        """
        if match_id not in self.matches:
            return {"success": False, "error": f"Match does not exist for match_id {match_id}."}

        odds_entry: OddsInfo = {
            "match_id": match_id,
            "market_type": market_type,
            "selection": selection,
            "odds_value": odds_value,
            "provider": provider,
            "timestamp": timestamp,
        }
        self.odds.append(odds_entry)
        return {"success": True, "message": f"Odds entry added for match {match_id}."}

    def update_odds_entry(
        self,
        match_id: str,
        market_type: str,
        selection: str,
        provider: str,
        odds_value: float,
        timestamp: str
    ) -> dict:
        """
        Update the odds_value and timestamp for an existing odds entry 
        (by match_id, market_type, selection, provider). Only updates if an entry exists.

        Args:
            match_id (str): Match identifier (must exist).
            market_type (str): Market type (e.g. "1X2").
            selection (str): Selection (e.g. "Home", "Draw", "Away").
            provider (str): Provider identifier.
            odds_value (float): New odds value (should be positive).
            timestamp (str): New timestamp (ISO8601).

        Returns:
            dict: {
                "success": True,
                "message": "Odds entry updated for match/market_type/selection/provider.",
            }
            or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Odds must reference an existing match.
            - Only updates if the specified odds entry exists. Does not insert new.
            - Only the latest entry per (match_id, market_type, selection, provider) is considered for update.
            - odds_value must be positive.
        """
        # Check match referential integrity
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}

        # Validate odds_value
        if odds_value <= 0:
            return {"success": False, "error": "Odds value must be positive"}

        # Gather matching odds entries
        candidate_indices = [
            i for i, o in enumerate(self.odds)
            if o["match_id"] == match_id and
               o["market_type"] == market_type and
               o["selection"] == selection and
               o["provider"] == provider
        ]
        if not candidate_indices:
            return {"success": False, "error": "Odds entry does not exist"}

        # Find the entry with the latest timestamp (lexicographically max)
        latest_index = max(
            candidate_indices, 
            key=lambda idx: self.odds[idx]["timestamp"]
        )

        # Update that entry
        self.odds[latest_index]["odds_value"] = odds_value
        self.odds[latest_index]["timestamp"] = timestamp

        return {
            "success": True,
            "message": (
                f"Odds entry updated for match {match_id}, market {market_type}, "
                f"selection {selection}, provider {provider}."
            )
        }

    def remove_odds_entry(
        self,
        match_id: str,
        market_type: str,
        selection: str,
        provider: str,
        timestamp: str
    ) -> dict:
        """
        Remove a specific odds entry identified by (match_id, market_type, selection, provider, timestamp).
    
        Args:
            match_id (str): ID of the match related to the odds entry.
            market_type (str): Type of betting market (e.g., '1X2', 'Over/Under').
            selection (str): The specific bet selection (e.g., 'home', 'draw', 'away').
            provider (str): Odds provider identifier.
            timestamp (str): The exact timestamp of the odds entry to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Odds entry removed."
            }
            or
            {
                "success": False,
                "error": "Odds entry not found."
            }

        Constraints:
            - Only removes the entry matching all provided parameters.
            - If not found, returns failure.
        """
        for idx, odds in enumerate(self.odds):
            if (
                odds["match_id"] == match_id and
                odds["market_type"] == market_type and
                odds["selection"] == selection and
                odds["provider"] == provider and
                odds["timestamp"] == timestamp
            ):
                del self.odds[idx]
                return { "success": True, "message": "Odds entry removed." }
        return { "success": False, "error": "Odds entry not found." }

    def correct_match_league_affiliation(self, match_id: str, new_league_id: str) -> dict:
        """
        Update the league affiliation (league_id) of a match.
    
        Args:
            match_id (str): Unique identifier of the match to update.
            new_league_id (str): The correct league_id to associate with the match.
    
        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Match's league affiliation updated." }
                On failure:
                    { "success": False, "error": "reason" }
    
        Constraints:
            - The match identified by match_id must exist.
            - The league identified by new_league_id must exist.
            - Only the league_id attribute of the match is changed.
        """
        # Check match exists
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }

        # Check new league exists
        if new_league_id not in self.leagues:
            return { "success": False, "error": "League does not exist" }

        # Update league_id
        self.matches[match_id]["league_id"] = new_league_id

        return { "success": True, "message": "Match's league affiliation updated." }

    def update_match_status(self, match_id: str, new_status: str) -> dict:
        """
        Change the status of a match (e.g., scheduled, ongoing, finished, etc.).

        Args:
            match_id (str): The unique identifier of the match to update.
            new_status (str): The new status value for the match.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Status for match <match_id> updated to <new_status>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Match with id <match_id> does not exist"
                    }

        Constraints:
            - The match_id must correspond to an existing match in the system.
            - No validation is performed on new_status values.
        """
        if match_id not in self.matches:
            return {
                "success": False,
                "error": f"Match with id {match_id} does not exist"
            }
        self.matches[match_id]['sta'] = new_status
        return {
            "success": True,
            "message": f"Status for match {match_id} updated to {new_status}"
        }


class SportsBettingOddsManagementSystem(BaseEnv):
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

    def list_matches_by_league(self, **kwargs):
        return self._call_inner_tool('list_matches_by_league', kwargs)

    def get_league_by_id(self, **kwargs):
        return self._call_inner_tool('get_league_by_id', kwargs)

    def get_league_by_name_and_country(self, **kwargs):
        return self._call_inner_tool('get_league_by_name_and_country', kwargs)

    def list_leagues_by_sport_and_country(self, **kwargs):
        return self._call_inner_tool('list_leagues_by_sport_and_country', kwargs)

    def get_matches_by_league_name_and_country(self, **kwargs):
        return self._call_inner_tool('get_matches_by_league_name_and_country', kwargs)

    def get_latest_odds_for_match(self, **kwargs):
        return self._call_inner_tool('get_latest_odds_for_match', kwargs)

    def get_latest_odds_for_match_market(self, **kwargs):
        return self._call_inner_tool('get_latest_odds_for_match_market', kwargs)

    def get_latest_odds_for_match_market_provider(self, **kwargs):
        return self._call_inner_tool('get_latest_odds_for_match_market_provider', kwargs)

    def list_odds_for_match_all_versions(self, **kwargs):
        return self._call_inner_tool('list_odds_for_match_all_versions', kwargs)

    def get_match_status(self, **kwargs):
        return self._call_inner_tool('get_match_status', kwargs)

    def add_match(self, **kwargs):
        return self._call_inner_tool('add_match', kwargs)

    def add_league(self, **kwargs):
        return self._call_inner_tool('add_league', kwargs)

    def add_odds_entry(self, **kwargs):
        return self._call_inner_tool('add_odds_entry', kwargs)

    def update_odds_entry(self, **kwargs):
        return self._call_inner_tool('update_odds_entry', kwargs)

    def remove_odds_entry(self, **kwargs):
        return self._call_inner_tool('remove_odds_entry', kwargs)

    def correct_match_league_affiliation(self, **kwargs):
        return self._call_inner_tool('correct_match_league_affiliation', kwargs)

    def update_match_status(self, **kwargs):
        return self._call_inner_tool('update_match_status', kwargs)

