# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
from datetime import datetime
from typing import List, Dict
from typing import List, Dict, Any



class MatchInfo(TypedDict):
    match_id: str
    teams: List[str]
    sport_type: str
    start_time: str  # ISO8601 datetime string or timestamp
    competition: str
    location: str
    outcome: Optional[str]  # Could be None if not completed
    bookmaker_odd: List[str]  # List of odds_id associated with this match

class BookmakerInfo(TypedDict):
    bookmaker_id: str
    name: str
    supported_sports: List[str]
    country: str

class OddsInfo(TypedDict):
    odds_id: str
    match_id: str
    bookmaker_id: str
    odds_type: str
    odds_value: float
    timestamp: str  # ISO8601 datetime string or timestamp

class _GeneratedEnvImpl:
    def __init__(self):
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Bookmakers: {bookmaker_id: BookmakerInfo}
        self.bookmakers: Dict[str, BookmakerInfo] = {}

        # Odds: {odds_id: OddsInfo}
        self.odds: Dict[str, OddsInfo] = {}

        # --- Constraints & Filtering Support (see rules below) ---
        # - Every Match must have at least one associated Odds entry.
        # - Each Odds entry must reference a valid match and valid bookmaker.
        # - Retrieval and filtering by time range, sport type, and bookmaker are essential operations (to be implemented).
        # - Odds for the same match may differ by bookmaker and over time; historical odds should be preserved or versioned.

    def get_bookmaker_by_name(self, name: str) -> dict:
        """
        Retrieve bookmaker info by bookmaker name.

        Args:
            name (str): The name of the bookmaker to search for.

        Returns:
            dict: 
                success: True and the BookmakerInfo if found;
                success: False and error message if not found.

        Constraints:
            - Bookmaker name is matched exactly (case-sensitive).
            - Returns the first match found if multiple bookmakers have the same name.
        """
        for bookmaker in self.bookmakers.values():
            if bookmaker["name"] == name:
                return { "success": True, "data": bookmaker }
        return { "success": False, "error": "Bookmaker not found" }

    def list_all_bookmakers(self) -> dict:
        """
        List all registered bookmakers in the system.

        Args:
            None

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[BookmakerInfo]  # All bookmakers, may be empty if none registered
                }
        """
        return {
            "success": True,
            "data": list(self.bookmakers.values())
        }


    def list_matches_by_time_sport_bookmaker(
        self, 
        start_time: str, 
        end_time: str, 
        sport_type: str, 
        bookmaker_id: str
    ) -> dict:
        """
        Retrieve all matches whose:
          - start_time is within [start_time, end_time] (inclusive),
          - sport_type equals the given sport_type,
          - have at least one associated Odds entry from the given bookmaker.
    
        Args:
            start_time (str): ISO8601 datetime string, inclusive lower bound for match's start_time.
            end_time (str): ISO8601 datetime string, inclusive upper bound.
            sport_type (str): Required sport type for matches.
            bookmaker_id (str): Bookmaker ID that must be represented in the match's odds.

        Returns:
            dict: 
              - {"success": True, "data": List[MatchInfo]}
                (even if the list is empty; this is not an error)
              - {"success": False, "error": <str>} if severe error arises.
        Constraints:
            - Returns only matches that satisfy all three conditions.
            - Bookmaker does not need to exist in the system to return empty list (not an error).
            - Time strings must be properly formatted ISO8601; otherwise, return error.
        """

        # Validate time strings
        try:
            t_start = datetime.fromisoformat(start_time)
            t_end = datetime.fromisoformat(end_time)
        except Exception:
            return {"success": False, "error": "Invalid time format; expected ISO8601 datetime strings."}
    
        # Sport_type and bookmaker_id as string, no additional validation required.
        matches_result: List[Dict] = []
        # Precompute matching odds_ids for bookmaker to avoid redundant checks
        bookmaker_odds_ids = {odds_id for odds_id, odds in self.odds.items() if odds["bookmaker_id"] == bookmaker_id}

        for match in self.matches.values():
            # Check sport_type
            if match["sport_type"] != sport_type:
                continue
            # Check start_time range
            try:
                match_time = datetime.fromisoformat(match["start_time"])
            except Exception:
                continue  # skip matches with invalid date
            if not (t_start <= match_time <= t_end):
                continue
            # Check if any of this match's bookmaker_odd refers to bookmaker_id
            if any(odds_id in bookmaker_odds_ids for odds_id in match.get("bookmaker_odd", [])):
                matches_result.append(match)
        return {"success": True, "data": matches_result}


    def list_matches_by_time_range(self, start_time: str, end_time: str) -> dict:
        """
        Retrieve all matches with start_time between the specified time interval [start_time, end_time] (inclusive).

        Args:
            start_time (str): Start of the interval (ISO8601 datetime string).
            end_time (str): End of the interval (ISO8601 datetime string).

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # Possibly empty.
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - start_time and end_time must be valid ISO8601 datetime strings.
            - start_time must be <= end_time.
        """
        try:
            dt_start = datetime.fromisoformat(start_time)
            dt_end = datetime.fromisoformat(end_time)
        except Exception:
            return {
                "success": False,
                "error": "Invalid time format. Use ISO8601 datetime strings."
            }

        if dt_start > dt_end:
            return {
                "success": False,
                "error": "start_time must be less than or equal to end_time."
            }

        found_matches: List[Dict[str, Any]] = []
        for match in self.matches.values():
            try:
                match_dt = datetime.fromisoformat(match["start_time"])
            except Exception:
                # Skip matches with invalid datetime
                continue
            if dt_start <= match_dt <= dt_end:
                found_matches.append(match)

        return {
            "success": True,
            "data": found_matches
        }

    def list_matches_by_sport_type(self, sport_type: str) -> dict:
        """
        Retrieve all matches (MatchInfo) of a specified sport type.

        Args:
            sport_type (str): The type of sport to filter matches (e.g., "football").

        Returns:
            dict: 
                - On success: {"success": True, "data": List[MatchInfo]}
                - On failure: {"success": False, "error": str}

        Constraints:
            - sport_type must be a non-empty string
            - Returns empty list if no matches found for sport_type
        """
        if not isinstance(sport_type, str) or not sport_type.strip():
            return {"success": False, "error": "Invalid or empty sport_type provided."}

        result = [
            match for match in self.matches.values()
            if match["sport_type"] == sport_type
        ]

        return {"success": True, "data": result}

    def list_matches_by_bookmaker(self, bookmaker_id: str) -> dict:
        """
        Retrieve all matches that have odds provided by the specified bookmaker.

        Args:
            bookmaker_id (str): The ID of the bookmaker.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # May be empty if bookmaker has provided no odds
            }
            or 
            {
                "success": False,
                "error": str  # Reason, e.g., "Bookmaker not found"
            }

        Constraints:
            - The bookmaker_id must exist in the system.
            - Each returned match must have at least one odds entry by this bookmaker.
        """
        if bookmaker_id not in self.bookmakers:
            return { "success": False, "error": "Bookmaker not found" }

        # Find all odds entries from this bookmaker
        match_ids = set(
            odds_info["match_id"]
            for odds_info in self.odds.values()
            if odds_info["bookmaker_id"] == bookmaker_id
        )

        # Retrieve the actual matches (ignore matches that may not exist, though this should not happen if constraints are enforced)
        result = [
            self.matches[match_id]
            for match_id in match_ids
            if match_id in self.matches
        ]

        return { "success": True, "data": result }

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve complete details of a match by its match_id.

        Args:
            match_id (str): The identifier of the match to look up.

        Returns:
            dict: {
                "success": True,
                "data": MatchInfo  # Match information dictionary
            }
            or
            {
                "success": False,
                "error": "Match not found"
            }

        Constraints:
            - match_id must exist in the matches dictionary.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
    
        return { "success": True, "data": match }

    def get_odds_for_match_bookmaker(self, match_id: str, bookmaker_id: str) -> dict:
        """
        Retrieve all odds entries for a specific match and bookmaker, sorted by timestamp (ascending).

        Args:
            match_id (str): ID of the match.
            bookmaker_id (str): ID of the bookmaker.

        Returns:
            dict: {
                "success": True,
                "data": List[OddsInfo]  # Sorted by timestamp (oldest first, can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The match and bookmaker must exist.
            - Sorting is by timestamp; timestamps are assumed ISO8601 or numeric.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}
        if bookmaker_id not in self.bookmakers:
            return {"success": False, "error": "Bookmaker does not exist"}

        relevant_odds = [
            odds_info for odds_info in self.odds.values()
            if odds_info['match_id'] == match_id and odds_info['bookmaker_id'] == bookmaker_id
        ]

        # Sort by timestamp (ISO8601 strings or numerics are lexicographically sortable)
        relevant_odds.sort(key=lambda o: o["timestamp"])

        return {"success": True, "data": relevant_odds}

    def get_most_recent_odds_for_match_bookmaker(self, match_id: str, bookmaker_id: str) -> dict:
        """
        Retrieve the most recently updated odds entry for a given match and bookmaker.

        Args:
            match_id (str): The ID of the match.
            bookmaker_id (str): The ID of the bookmaker.

        Returns:
            dict: {
                "success": True,
                "data": OddsInfo,  # The most recent odds entry
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. not found or invalid IDs)
            }

        Constraints:
            - The match_id and bookmaker_id must both be valid (present in the system).
            - If no odds entries exist for this match and bookmaker, failure is returned.
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match ID does not exist" }
        if bookmaker_id not in self.bookmakers:
            return { "success": False, "error": "Bookmaker ID does not exist" }

        relevant_odds = [
            odds for odds in self.odds.values()
            if odds["match_id"] == match_id and odds["bookmaker_id"] == bookmaker_id
        ]

        if not relevant_odds:
            return { "success": False, "error": "No odds entry found for given match and bookmaker" }

        # Find the odds with the latest timestamp (assuming ISO8601 or numerically sorting strings is safe)
        most_recent_odds = max(relevant_odds, key=lambda o: o["timestamp"])

        return { "success": True, "data": most_recent_odds }

    def get_historical_odds_for_match(self, match_id: str) -> dict:
        """
        Retrieve all historical (versioned) odds for the specified match_id across all bookmakers,
        ordered by their timestamp (ascending).

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict: {
                "success": True,
                "data": List[OddsInfo]  # May be empty if no odds found for match
            }
            OR
            {
                "success": False,
                "error": str  # Description (e.g., "Match not found")
            }

        Constraints:
            - match_id must exist in self.matches.
            - Results are ordered by timestamp (ascending).
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match not found"}

        # Collect all odds for this match_id
        odds_list = [
            odds_info for odds_info in self.odds.values()
            if odds_info["match_id"] == match_id
        ]

        # Sort odds by timestamp (assuming ISO8601 string comparison will suffice)
        odds_list.sort(key=lambda o: o["timestamp"])

        return {"success": True, "data": odds_list}

    def get_match_outcome(self, match_id: str) -> dict:
        """
        Return the outcome/result of the given match.

        Args:
            match_id (str): Unique identifier of the match.

        Returns:
            dict:
              {
                "success": True,
                "data": {
                    "match_id": str,
                    "outcome": Optional[str]  # None if match not completed yet
                }
              }
              OR
              {
                "success": False,
                "error": str  # "Match not found"
              }

        Constraints:
            - The provided match_id must exist in the system.
            - If the outcome is not yet determined, it may be None.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }

        return {
            "success": True,
            "data": {
                "match_id": match_id,
                "outcome": match.get("outcome")
            }
        }

    def add_match(
        self,
        match_id: str,
        teams: list,
        sport_type: str,
        start_time: str,
        competition: str,
        location: str,
        bookmaker_odd: list,
        outcome: str = None
    ) -> dict:
        """
        Add a new match with required details and associate it with at least one existing odds entry.

        Args:
            match_id (str): Unique match identifier.
            teams (List[str]): List of team/participant names.
            sport_type (str): Category of the sport.
            start_time (str): ISO8601 datetime or timestamp for match start.
            competition (str): Competition or league.
            location (str): Physical or virtual location.
            bookmaker_odd (List[str]): List of odds_ids (must already exist in the system), must reference this match.
            outcome (str, optional): Outcome if already known.

        Returns:
            dict: {
                "success": True,
                "message": "Match <match_id> added with odds entries."
            }
            OR
            dict: {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - match_id must be unique (not already in self.matches).
            - bookmaker_odd must be a non-empty list of odds_ids, each of which:
                * exists in self.odds
                * references this match_id and a valid bookmaker
        """
        # Check if match_id already exists
        if match_id in self.matches:
            return { "success": False, "error": "A match with this match_id already exists." }

        # bookmaker_odd must be a non-empty list
        if not isinstance(bookmaker_odd, list) or not bookmaker_odd:
            return { "success": False, "error": "At least one odds_id must be associated with the match." }

        # Validate all odds_ids
        for odds_id in bookmaker_odd:
            if odds_id not in self.odds:
                return { "success": False, "error": f"Odds entry {odds_id} does not exist." }
            odds_entry = self.odds[odds_id]
            # The odds entry must reference this match
            if odds_entry["match_id"] != match_id:
                return { "success": False, "error": f"Odds entry {odds_id} does not reference the provided match_id." }
            # Odds entry's bookmaker must exist
            if odds_entry["bookmaker_id"] not in self.bookmakers:
                return { "success": False, "error": f"Odds entry {odds_id} references non-existent bookmaker." }

        # Create and save the match info
        match_info = {
            "match_id": match_id,
            "teams": teams,
            "sport_type": sport_type,
            "start_time": start_time,
            "competition": competition,
            "location": location,
            "outcome": outcome,
            "bookmaker_odd": bookmaker_odd
        }
        self.matches[match_id] = match_info

        return {
            "success": True,
            "message": f"Match {match_id} added with odds entries."
        }

    def add_bookmaker(self, bookmaker_id: str, name: str, supported_sports: list, country: str) -> dict:
        """
        Register a new bookmaker.

        Args:
            bookmaker_id (str): Unique ID for the bookmaker.
            name (str): Human-readable name of the bookmaker.
            supported_sports (List[str]): List of sports this bookmaker covers (must be non-empty).
            country (str): Country of operation.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Bookmaker <name> added."}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - bookmaker_id must be unique.
            - supported_sports must be a non-empty list.
            - Each required field must be non-empty.
        """
        if not bookmaker_id or not isinstance(bookmaker_id, str):
            return {"success": False, "error": "Invalid bookmaker_id."}

        if bookmaker_id in self.bookmakers:
            return {"success": False, "error": "Bookmaker ID already exists."}

        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid bookmaker name."}

        # Optionally enforce name uniqueness
        if any(bk["name"] == name for bk in self.bookmakers.values()):
            return {"success": False, "error": "Bookmaker name already exists."}

        if not isinstance(supported_sports, list) or len(supported_sports) == 0 \
                or not all(isinstance(s, str) and s for s in supported_sports):
            return {"success": False, "error": "supported_sports must be a non-empty list of strings."}

        if not country or not isinstance(country, str):
            return {"success": False, "error": "Invalid country."}

        bookmaker_info = {
            "bookmaker_id": bookmaker_id,
            "name": name,
            "supported_sports": supported_sports,
            "country": country
        }

        self.bookmakers[bookmaker_id] = bookmaker_info
        return {"success": True, "message": f"Bookmaker {name} added."}

    def add_odds_entry(
        self, 
        odds_id: str, 
        match_id: str, 
        bookmaker_id: str, 
        odds_type: str, 
        odds_value: float, 
        timestamp: str
    ) -> dict:
        """
        Add a new odds entry for a match, bookmaker, and odds type, with the supplied timestamp.

        Args:
            odds_id (str): Unique identifier for this odds entry.
            match_id (str): Match to which this odds entry pertains (must exist).
            bookmaker_id (str): Bookmaker offering the odds (must exist).
            odds_type (str): Type/category of odds (e.g., 'win', 'draw', 'loss').
            odds_value (float): Value for these odds (e.g., 3.25).
            timestamp (str): ISO8601 timestamp for when the odds were recorded.

        Returns:
            dict: {
                "success": True,
                "message": "Odds entry added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - odds_id must be unique (not already present).
            - match_id must exist in self.matches.
            - bookmaker_id must exist in self.bookmakers.
            - On success, the new entry is added to self.odds, and odds_id is appended to the match's bookmaker_odd list.
        """
        # Uniqueness check
        if odds_id in self.odds:
            return {"success": False, "error": "odds_id already exists."}
        # Validate match_id
        if match_id not in self.matches:
            return {"success": False, "error": "Invalid match_id."}
        # Validate bookmaker_id
        if bookmaker_id not in self.bookmakers:
            return {"success": False, "error": "Invalid bookmaker_id."}

        # Compose new OddsInfo entry
        odds_entry = {
            "odds_id": odds_id,
            "match_id": match_id,
            "bookmaker_id": bookmaker_id,
            "odds_type": odds_type,
            "odds_value": odds_value,
            "timestamp": timestamp
        }
        # Add to odds dictionary
        self.odds[odds_id] = odds_entry

        # Also update the match's bookmaker_odd list
        if "bookmaker_odd" in self.matches[match_id]:
            self.matches[match_id]["bookmaker_odd"].append(odds_id)
        else:
            self.matches[match_id]["bookmaker_odd"] = [odds_id]

        return {"success": True, "message": "Odds entry added successfully."}

    def update_odds_entry(
        self,
        odds_id: str,
        odds_value: float,
        timestamp: str
    ) -> dict:
        """
        Update an existing odds entry's value by creating a new version (preserving history).
    
        Args:
            odds_id (str): The identifier of the odds entry to update.
            odds_value (float): The new odds value.
            timestamp (str): ISO8601 timestamp for the new version.

        Returns:
            dict: {
                "success": True,
                "message": "Odds updated (new version created)",
                "new_odds_id": str,
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the failure.
            }
    
        Constraints:
            - The odds entry to update must exist.
            - The updated odds value and timestamp are required.
            - This preserves the old odds as history (does not overwrite).
            - The new odds_id is auto-generated as "<old_odds_id>-vN".
        """
        old_odds = self.odds.get(odds_id)
        if not old_odds:
            return {"success": False, "error": "Odds entry not found"}

        # Determine the next version number for this odds entry
        # Scan odds dict for entries with prefix odds_id
        base_id = odds_id
        version_prefix = base_id + "-v"
        version_nums = [
            int(o_id[len(version_prefix):])
            for o_id in self.odds.keys()
            if o_id.startswith(version_prefix) and o_id[len(version_prefix):].isdigit()
        ]
        if version_nums:
            next_version = max(version_nums) + 1
        else:
            next_version = 1
        new_odds_id = f"{base_id}-v{next_version}"

        # Build new OddsInfo
        new_odds = {
            "odds_id": new_odds_id,
            "match_id": old_odds["match_id"],
            "bookmaker_id": old_odds["bookmaker_id"],
            "odds_type": old_odds["odds_type"],
            "odds_value": odds_value,
            "timestamp": timestamp
        }

        # Add new odds entry
        self.odds[new_odds_id] = new_odds

        # Optionally, in the associated MatchInfo, add the new odds_id
        match = self.matches.get(old_odds["match_id"])
        if not match:
            return {"success": False, "error": "Associated match not found"}
        if new_odds_id not in match["bookmaker_odd"]:
            match["bookmaker_odd"].append(new_odds_id)

        return {
            "success": True,
            "message": "Odds updated (new version created)",
            "new_odds_id": new_odds_id
        }

    def set_match_outcome(self, match_id: str, outcome: str) -> dict:
        """
        Record or update the outcome of a match.
    
        Args:
            match_id (str): The unique identifier of the match.
            outcome (str): The outcome to record (e.g., "Team A win", "draw", "cancelled").
    
        Returns:
            dict: {
                "success": True,
                "message": "Outcome set/updated for match {match_id}"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - The match must exist in the system.
            - Outcome must be a non-empty string.
        """
        # Check if match exists
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}
    
        # Validate outcome
        if not outcome or not isinstance(outcome, str) or outcome.strip() == "":
            return {"success": False, "error": "Outcome must be specified"}
    
        # Update outcome
        match["outcome"] = outcome.strip()
        self.matches[match_id] = match  # Explicit for clarity, though dict is mutable

        return {"success": True, "message": f"Outcome set/updated for match {match_id}"}

    def delete_odds_entry(self, odds_id: str) -> dict:
        """
        Remove an odds entry from the system.
        Maintains integrity: a match must have at least one associated odds entry;
        if this is the last odds entry for the match, operation fails.

        Args:
            odds_id (str): Unique identifier of the odds entry to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of operation
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - An odds entry cannot be deleted if it is the only one associated with its match.
            - The specified odds_id must exist in the system.
        """
        if odds_id not in self.odds:
            return { "success": False, "error": "Odds entry not found." }

        odds_info = self.odds[odds_id]
        match_id = odds_info.get("match_id")

        if match_id not in self.matches:
            return { "success": False, "error": "Associated match not found for this odds entry." }

        match_info = self.matches[match_id]
        bookmaker_odd_list = match_info.get("bookmaker_odd", [])

        # Check if odds_id is in bookmaker_odd list for the match
        if odds_id not in bookmaker_odd_list:
            return { "success": False, "error": "Inconsistent state: Odds entry not linked to match." }

        # Check if this is the only odds left for the match
        if len(bookmaker_odd_list) <= 1:
            return {
                "success": False,
                "error": "Cannot delete the last odds entry for this match; each match must have at least one odds entry."
            }

        # Remove the odds_id from the bookmaker_odd list of the match
        match_info["bookmaker_odd"] = [oid for oid in bookmaker_odd_list if oid != odds_id]

        # Remove the odds entry
        del self.odds[odds_id]

        return {
            "success": True,
            "message": f"Odds entry '{odds_id}' has been deleted successfully."
        }

    def remove_match(self, match_id: str) -> dict:
        """
        Remove a match and all associated odds entries from the system.

        Args:
            match_id (str): Unique identifier of the match to remove.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Match <match_id> and associated odds entries removed."
                  }
                - On failure: {
                    "success": False,
                    "error": "Match <match_id> does not exist."
                  }

        Constraints:
            - The match must exist in the system.
            - All associated odds entries (odds['match_id'] == match_id) are also removed.
        """
        if match_id not in self.matches:
            return {"success": False, "error": f"Match {match_id} does not exist."}

        # Remove associated odds entries
        odds_to_remove = [odds_id for odds_id, odds in self.odds.items() if odds["match_id"] == match_id]
        for odds_id in odds_to_remove:
            del self.odds[odds_id]

        # Remove the match itself
        del self.matches[match_id]

        return {
            "success": True,
            "message": f"Match {match_id} and associated odds entries removed."
        }

    def remove_bookmaker(self, bookmaker_id: str) -> dict:
        """
        Remove a bookmaker and all associated odds entries from the system.

        Args:
            bookmaker_id (str): The unique identifier of the bookmaker to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Bookmaker <id> and related odds entries removed"
            }
            or
            {
                "success": False,
                "error": <error-message str>
            }

        Constraints:
            - Cannot remove a bookmaker if doing so would leave any match with no odds entries.
        """
        # Check bookmaker existence
        if bookmaker_id not in self.bookmakers:
            return {"success": False, "error": "Bookmaker does not exist"}

        # Find all odds_ids associated with this bookmaker
        odds_to_remove = [odds_id for odds_id, o in self.odds.items() if o["bookmaker_id"] == bookmaker_id]

        # Track match odds counts if these odds are removed
        # match_odds_remain: match_id -> set of odds_ids remaining post-removal
        affected_matches = set()
        for odds_id in odds_to_remove:
            affected_matches.add(self.odds[odds_id]["match_id"])
        # For each affected match, check if orphaned
        matches_without_odds = []
        for match_id in affected_matches:
            odds_in_match = [odds_id for odds_id in self.matches[match_id].get("bookmaker_odd", [])]
            # How many odds will remain after removal?
            remaining = [oid for oid in odds_in_match if oid not in odds_to_remove]
            if len(remaining) == 0:
                matches_without_odds.append(match_id)
        if matches_without_odds:
            return {
                "success": False,
                "error": (
                    f"Cannot remove bookmaker: removing odds would orphan matches with no odds left: "
                    f"{matches_without_odds}"
                )
            }

        # Proceed with removal: delete odds entries from self.odds and from each match's bookmaker_odd list
        for odds_id in odds_to_remove:
            match_id = self.odds[odds_id]["match_id"]
            # Remove odds_id from the match's bookmaker_odd list
            if odds_id in self.matches[match_id]["bookmaker_odd"]:
                self.matches[match_id]["bookmaker_odd"].remove(odds_id)
            # Remove from odds dict
            del self.odds[odds_id]

        # Remove bookmaker
        del self.bookmakers[bookmaker_id]

        return {
            "success": True,
            "message": f"Bookmaker {bookmaker_id} and related odds entries removed"
        }


class SportsBettingAggregatorSystem(BaseEnv):
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

    def get_bookmaker_by_name(self, **kwargs):
        return self._call_inner_tool('get_bookmaker_by_name', kwargs)

    def list_all_bookmakers(self, **kwargs):
        return self._call_inner_tool('list_all_bookmakers', kwargs)

    def list_matches_by_time_sport_bookmaker(self, **kwargs):
        return self._call_inner_tool('list_matches_by_time_sport_bookmaker', kwargs)

    def list_matches_by_time_range(self, **kwargs):
        return self._call_inner_tool('list_matches_by_time_range', kwargs)

    def list_matches_by_sport_type(self, **kwargs):
        return self._call_inner_tool('list_matches_by_sport_type', kwargs)

    def list_matches_by_bookmaker(self, **kwargs):
        return self._call_inner_tool('list_matches_by_bookmaker', kwargs)

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def get_odds_for_match_bookmaker(self, **kwargs):
        return self._call_inner_tool('get_odds_for_match_bookmaker', kwargs)

    def get_most_recent_odds_for_match_bookmaker(self, **kwargs):
        return self._call_inner_tool('get_most_recent_odds_for_match_bookmaker', kwargs)

    def get_historical_odds_for_match(self, **kwargs):
        return self._call_inner_tool('get_historical_odds_for_match', kwargs)

    def get_match_outcome(self, **kwargs):
        return self._call_inner_tool('get_match_outcome', kwargs)

    def add_match(self, **kwargs):
        return self._call_inner_tool('add_match', kwargs)

    def add_bookmaker(self, **kwargs):
        return self._call_inner_tool('add_bookmaker', kwargs)

    def add_odds_entry(self, **kwargs):
        return self._call_inner_tool('add_odds_entry', kwargs)

    def update_odds_entry(self, **kwargs):
        return self._call_inner_tool('update_odds_entry', kwargs)

    def set_match_outcome(self, **kwargs):
        return self._call_inner_tool('set_match_outcome', kwargs)

    def delete_odds_entry(self, **kwargs):
        return self._call_inner_tool('delete_odds_entry', kwargs)

    def remove_match(self, **kwargs):
        return self._call_inner_tool('remove_match', kwargs)

    def remove_bookmaker(self, **kwargs):
        return self._call_inner_tool('remove_bookmaker', kwargs)

