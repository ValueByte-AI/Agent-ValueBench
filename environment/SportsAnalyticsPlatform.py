# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any, Optional



# --- TypedDict definitions for each entity ---

class TeamInfo(TypedDict):
    team_id: str        # formerly "am_id"
    name: str
    roster: List[str]   # list of player_ids (current roster)
    coach: str
    league: str         # formerly "leag"
    roster_history: List[Dict[str, Any]]  # list of {"timestamp": ..., "roster": List[str]}

class PlayerInfo(TypedDict):
    player_id: str
    name: str
    team_id: str
    position: str
    stats_overview: Dict[str, Any]

class EventInfo(TypedDict):
    event_id: str
    name: str
    match_id: str
    timestamp: float
    event_type: str

class MatchInfo(TypedDict):
    match_id: str
    date: str
    participating_team_ids: List[str]
    location: str
    result: Optional[Dict[str, Any]]  # structure will depend on sport

class PlayerPerformanceInfo(TypedDict):
    player_id: str
    event_id: str
    match_id: str
    metrics: Dict[str, Any]   # expects at least "speed", "scores", "passes", "spatial_coordinates", "actions"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for sports analytics with teams, players, matches, events, and player performance data.
        """

        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Player performances: {(player_id, event_id, match_id): PlayerPerformanceInfo}
        self.player_performances: Dict[tuple, PlayerPerformanceInfo] = {}

        # Constraints:
        #  - Players can only appear in PlayerPerformance if they are rostered on team at event time (track roster_history).
        #  - Events must be linked to a valid match and have a valid timestamp.
        #  - PlayerPerformance must reference valid player_id, event_id, and match_id.
        #  - Heatmap visualizations require metrics["spatial_coordinates"] in PlayerPerformance.
        #  - Teams may change rosters over time; historic roster data is tracked in TeamInfo.roster_history.


    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve full team information, including roster and roster history, given a team ID.

        Args:
            team_id (str): The team identifier.

        Returns:
            dict: {
                "success": True,
                "data": TeamInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The team must exist in self.teams.
        """
        team = self.teams.get(team_id)
        if team is None:
            return {"success": False, "error": f"Team with id '{team_id}' does not exist."}
        return {"success": True, "data": team}

    def get_team_roster_at_time(self, team_id: str, timestamp: float) -> dict:
        """
        Get the roster (list of player_ids) for a team as of a specific timestamp.

        Args:
            team_id (str): The ID of the team to query.
            timestamp (float): The timestamp (event time) for historic roster lookup.

        Returns:
            dict:
                - success: True, data: List[str] (roster at/before timestamp).
                - success: False, error: str.

        Constraints:
            - team must exist.
            - historic roster entry (roster_history) must exist at or before timestamp.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        team_info = self.teams[team_id]
        roster_history = team_info.get("roster_history", [])

        # Find latest roster entry at or before timestamp
        valid_entries = [
            entry for entry in roster_history
            if "timestamp" in entry and entry["timestamp"] <= timestamp
        ]
        if not valid_entries:
            return { "success": False, "error": "No roster history available at or before the given timestamp" }

        # Sort and get the most recent one
        latest_entry = max(valid_entries, key=lambda x: x["timestamp"])
        roster = latest_entry.get("roster", [])

        return { "success": True, "data": roster }

    def get_players_by_team(self, team_id: str) -> dict:
        """
        Retrieve all current PlayerInfo dicts for players on the given team's current roster.

        Args:
            team_id (str): Unique ID of the team whose current roster is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo],  # player info for all rostered players (may be empty if no players)
            }
            or
            {
                "success": False,
                "error": str  # why the request failed (e.g., team not found)
            }

        Constraints:
            - team_id must exist in the self.teams dictionary.
            - Only pulls current roster (not historic rosters).
            - Skips/ignores player_ids in the roster which do not exist in self.players.
        """
        if team_id not in self.teams:
            return { "success": False, "error": "Team not found" }

        roster_player_ids = self.teams[team_id].get("roster", [])

        players_info = []
        for pid in roster_player_ids:
            player = self.players.get(pid)
            if player is not None:
                players_info.append(player)

        return { "success": True, "data": players_info }

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Fetch a player's details and overview statistics by their player ID.

        Args:
            player_id (str): The unique identifier for the player.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": PlayerInfo  # full player information dictionary
                }
                On failure:
                {
                    "success": False,
                    "error": "Player not found"
                }

        Constraints:
            - The player_id must exist in the platform.
        """
        player = self.players.get(player_id)
        if player is None:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player}

    def get_events_by_ids(self, event_ids: list) -> dict:
        """
        Retrieve events and their details (including match and timestamps) for a list of event IDs.

        Args:
            event_ids (list): List of event_id strings to query.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],            # List of EventInfo for found event_ids.
                "missing_event_ids": List[str],     # event_ids not found in self.events (empty if all found)
            }
            or
            {
                "success": False,
                "error": str                        # Error message if input is invalid.
            }

        Constraints:
            - Returned events must exist in self.events.
            - If input is not a list or is empty, failure.
        """
        if not isinstance(event_ids, list) or not event_ids:
            return {
                "success": False,
                "error": "Invalid input: event_ids must be a non-empty list."
            }
    
        result = []
        missing = []
        for eid in event_ids:
            if eid in self.events:
                result.append(self.events[eid])
            else:
                missing.append(eid)
        return {
            "success": True,
            "data": result,
            "missing_event_ids": missing
        }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve details for a single event by its unique event_id.

        Args:
            event_id (str): The identifier for the event to look up.

        Returns:
            dict: {"success": True, "data": EventInfo} if event found,
                  {"success": False, "error": "Event not found"} if not found.
        """
        event = self.events.get(event_id)
        if event is None:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Retrieve full details of a match (participating teams, date, location, result) by match ID.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict:
                {
                    "success": True,
                    "data": MatchInfo
                }
                OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The match with the given match_id must exist in the platform.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match }

    def get_player_performance(self, player_id: str, event_id: str, match_id: str) -> dict:
        """
        Fetch a PlayerPerformance record for a specific player, event, and match.

        Args:
            player_id (str): The player's unique identifier.
            event_id (str): The event's unique identifier.
            match_id (str): The match's unique identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PlayerPerformanceInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error description
                    }

        Constraints:
            - The (player_id, event_id, match_id) tuple must identify a stored player_performance record.
            - event_id must exist in self.events.
            - The read is allowed even when the referenced player catalog entry or match link is missing,
              so corrupted records can still be inspected and repaired.
        """
        if event_id not in self.events:
            return { "success": False, "error": f"Event '{event_id}' does not exist." }

        key = (player_id, event_id, match_id)
        if key not in self.player_performances:
            return { "success": False, "error": "Player performance record does not exist for the specified player, event, and match." }

        return { "success": True, "data": self.player_performances[key] }

    def get_team_player_performances_for_events(self, team_id: str, event_ids: list) -> dict:
        """
        Retrieve all PlayerPerformance records (with all metrics, including spatial_coordinates) for all members
        of a team during the listed events.

        Args:
            team_id (str): The team ID.
            event_ids (list of str): List of event IDs.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerPerformanceInfo],  # List of matching player performances
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., invalid team_id or event_id)
            }

        Constraints:
            - Players can only appear if they were rostered on the team at the time of the event (checked via roster_history).
            - PlayerPerformance must exist and reference valid player_id, event_id, and match_id.
            - Event must exist and have valid match link and timestamp.
            - PlayerPerformance metrics must include "spatial_coordinates".
        """
        # Validate team_id
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        team_info = self.teams[team_id]
        # Validate events
        event_id_to_info = {}
        for eid in event_ids:
            if eid not in self.events:
                return {"success": False, "error": f"Event {eid} does not exist"}
            event_id_to_info[eid] = self.events[eid]

        result = []

        # Find rostered players at each event time using roster_history
        # Cache roster_at_event_time for each event
        def get_roster_at_time(roster_history, timestamp):
            rostered = []
            latest_time = None
            for entry in roster_history:
                entry_time = entry["timestamp"]
                if entry_time <= timestamp:
                    if latest_time is None or entry_time > latest_time:
                        rostered = entry["roster"]
                        latest_time = entry_time
            return set(rostered) if rostered else set()

        for eid, event_info in event_id_to_info.items():
            match_id = event_info["match_id"]
            event_time = event_info["timestamp"]
            # Get roster at event time
            roster_at_event_time = get_roster_at_time(team_info.get("roster_history", []), event_time)
            for player_id in roster_at_event_time:
                perf_key = (player_id, eid, match_id)
                if perf_key in self.player_performances:
                    perf = self.player_performances[perf_key]
                    metrics = perf.get("metrics", {})
                    if "spatial_coordinates" in metrics:
                        result.append(perf)

        return {"success": True, "data": result}

    def has_player_performance_spatial_coordinates(
        self,
        performance_keys: list
    ) -> dict:
        """
        For each provided (player_id, event_id, match_id) tuple, check whether the corresponding
        PlayerPerformance entry contains the 'spatial_coordinates' field in its metrics.

        Args:
            performance_keys (list of tuple): Each tuple is (player_id, event_id, match_id) identifying a PlayerPerformance.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "player_id|event_id|match_id": bool,
                    ...
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Notes/Constraints:
            - If the PlayerPerformance entry does not exist, result for that key is False.
            - Input must be a non-empty list of tuples.
        """
        if not isinstance(performance_keys, list) or not performance_keys:
            return {"success": False, "error": "performance_keys must be a non-empty list of (player_id, event_id, match_id) tuples."}

        result = {}
        for key in performance_keys:
            # Validate the key is the correct tuple form
            if not ((isinstance(key, tuple) or isinstance(key, list)) and len(key) == 3):
                result[str(key)] = False
                continue
            normalized_key = tuple(key)
            result_key = "|".join(str(part) for part in normalized_key)
            perf_info = self.player_performances.get(normalized_key)
            if perf_info and isinstance(perf_info.get("metrics", None), dict) and "spatial_coordinates" in perf_info["metrics"]:
                result[result_key] = True
            else:
                result[result_key] = False

        return {"success": True, "data": result}

    def generate_team_event_heatmap(self, team_id: str, event_ids: List[str]) -> dict:
        """
        Aggregate and transform spatial_coordinates from PlayerPerformance records into
        a heatmap visualization structure for a given team and set of event IDs.

        Args:
            team_id (str): The team for which the heatmap will be generated.
            event_ids (List[str]): List of event IDs from which PlayerPerformance data should be aggregated.

        Returns:
            dict: {
                "success": True,
                "data": heatmap, # dict structure, e.g. {"points": List[coordinates], "total": int}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only include PlayerPerformance records referencing valid players rostered for the team at event time.
            - Only aggregate spatial_coordinates found in qualifying PlayerPerformance records.
            - If team or any event is missing, operation fails.
        """

        # Validate team
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist"}

        # Validate event_ids
        invalid_event_ids = [eid for eid in event_ids if eid not in self.events]
        if invalid_event_ids:
            return {"success": False, "error": f"Event(s) do not exist: {', '.join(invalid_event_ids)}"}

        # Aggregate spatial_coordinates
        heatmap_points = []

        for pf_key, pf_info in self.player_performances.items():
            player_id = pf_info["player_id"]
            event_id = pf_info["event_id"]
            match_id = pf_info["match_id"]

            # Only consider requested events
            if event_id not in event_ids:
                continue

            # Check Player is valid
            if player_id not in self.players:
                continue  # ignore invalid player record

            player_info = self.players[player_id]

            # Check Event is valid
            if event_id not in self.events:
                continue
        
            event_info = self.events[event_id]
            event_timestamp = event_info["timestamp"]

            # Check player was rostered in the team at the time of the event
            team_info = self.teams[team_id]
            # Find the roster at the time of the event
            roster_history = team_info.get("roster_history", [])
            roster_at_time = None
            for entry in sorted(roster_history, key=lambda x: x["timestamp"], reverse=True):
                if event_timestamp >= entry["timestamp"]:
                    roster_at_time = entry["roster"]
                    break
            # Fallback: use current roster if history is missing (platform is permissive)
            if roster_at_time is None:
                roster_at_time = team_info.get("roster", [])

            # Check if player was on roster at event time
            if player_id not in roster_at_time:
                continue

            # Check spatial_coordinates in metrics
            metrics = pf_info.get("metrics", {})
            spatial_coords = metrics.get("spatial_coordinates")
            if spatial_coords is None:
                continue  # skip record without spatial_coordinates

            heatmap_points.append(spatial_coords)

        heatmap = {
            "points": heatmap_points,
            "total": len(heatmap_points)
        }

        return {"success": True, "data": heatmap}

    def validate_event_and_match_links(self) -> dict:
        """
        Confirm that all events are associated with a valid match and have valid timestamps.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "invalid_events": List[Dict[str, str]]  # Each dict: {"event_id": ..., "error": ...}
                }
            }

        Constraints:
            - Each event must reference an existing match (match_id in self.matches).
            - Each event must have a valid timestamp (float, and >0).
        """
        invalid_events = []

        for event_id, event in self.events.items():
            issues = []
            # Check match_id is valid
            if event.get("match_id") not in self.matches:
                issues.append("Invalid match_id")
            # Check timestamp is valid (float and >0)
            ts = event.get("timestamp")
            if not isinstance(ts, (int, float)) or ts <= 0:
                issues.append("Invalid timestamp")
            if issues:
                invalid_events.append({"event_id": event_id, "error": ", ".join(issues)})

        return { "success": True, "data": { "invalid_events": invalid_events } }

    def list_all_teams(self) -> dict:
        """
        Retrieve the list of all teams in the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[TeamInfo]  # List of all teams (may be empty if no teams present)
            }

        Constraints:
            - None. Simple enumeration of all teams tracked.
        """
        teams_list = list(self.teams.values())
        return { "success": True, "data": teams_list }

    def list_all_players(self) -> dict:
        """
        List all registered players in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo]  # May be empty if no players are registered
            }
        """
        player_list = list(self.players.values())
        return { "success": True, "data": player_list }

    def list_all_matches(self) -> dict:
        """
        List all recorded matches in the analytics platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of all match info (may be empty if none recorded)
            }
        """
        result = list(self.matches.values())
        return { "success": True, "data": result }

    def update_team_roster(self, team_id: str, player_id: str, action: str, timestamp: float) -> dict:
        """
        Change a team’s current roster by adding or removing a player.
        This updates both the team's roster and its roster_history for historic accuracy.

        Args:
            team_id (str): ID of the team to modify.
            player_id (str): ID of the player to add/remove.
            action (str): "add" or "remove".
            timestamp (float): Time of the roster change.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success description
            }
            or
            {
                "success": False,
                "error": str  # Description of error/constraint failure
            }

        Constraints:
            - team_id must exist.
            - player_id must exist.
            - For add: player not already in roster.
            - For remove: player must be in roster.
            - roster_history is updated with the new roster and timestamp.
        """
        if team_id not in self.teams:
            return { "success": False, "error": f"Team {team_id} does not exist" }
        if player_id not in self.players:
            return { "success": False, "error": f"Player {player_id} does not exist" }
        if action not in ("add", "remove"):
            return { "success": False, "error": "Action must be 'add' or 'remove'" }

        team_info = self.teams[team_id]
        roster = team_info["roster"]

        if action == "add":
            if player_id in roster:
                return { "success": False, "error": "Player already in roster" }
            roster.append(player_id)
            # Update player's team_id
            self.players[player_id]["team_id"] = team_id
            msg = f"Player {player_id} added to team {team_id}'s roster"

        elif action == "remove":
            if player_id not in roster:
                return { "success": False, "error": "Player not in roster" }
            roster.remove(player_id)
            # Optionally clear player's team association (or mark as free agent)
            self.players[player_id]["team_id"] = ""
            msg = f"Player {player_id} removed from team {team_id}'s roster"

        # Update roster history for historic queries/constraints
        entry = {
            "timestamp": timestamp,
            "roster": roster.copy()
        }
        team_info.setdefault("roster_history", []).append(entry)

        return { "success": True, "message": msg }

    def add_roster_history_entry(self, team_id: str, timestamp: float, roster: list) -> dict:
        """
        Add a roster snapshot to a team's roster_history for historic roster queries.

        Args:
            team_id (str): The team to update.
            timestamp (float): The point in time (as a Unix timestamp) for the roster snapshot.
            roster (List[str]): List of player_ids representing the roster at the timestamp.

        Returns:
            dict: {
                "success": True,
                "message": "Roster history entry added to team <team_id>."
            }
            or in case of error:
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Team must exist.
            - All player_ids in roster must exist in self.players.
            - roster must be a list of strings (player_ids).
        """
        # Check team existence
        if team_id not in self.teams:
            return {"success": False, "error": "Team not found"}

        # Validate roster format
        if not isinstance(roster, list) or not all(isinstance(pid, str) for pid in roster):
            return {"success": False, "error": "Roster must be a list of player_ids (str)"}

        # Validate players
        unknown_players = [pid for pid in roster if pid not in self.players]
        if unknown_players:
            return {"success": False, "error": f"Unknown player_id(s): {unknown_players}"}

        # Add to roster_history
        roster_entry = {
            "timestamp": timestamp,
            "roster": roster.copy()
        }
        self.teams[team_id]["roster_history"].append(roster_entry)

        return {"success": True, "message": f"Roster history entry added to team {team_id}."}

    def add_player_performance(
        self,
        player_id: str,
        event_id: str,
        match_id: str,
        metrics: Dict[str, Any]
    ) -> dict:
        """
        Insert a new PlayerPerformance entry for a specific (player, event, match).
    
        Args:
            player_id (str): The player's unique identifier.
            event_id (str): The event's unique identifier.
            match_id (str): The match's unique identifier.
            metrics (Dict[str, Any]): Performance data for the player in this event/match.
    
        Returns:
            dict:
                On success:
                    {"success": True, "message": "PlayerPerformance entry added"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Player, event, and match must exist.
            - Event must belong to the specified match.
            - Player must be on their team's roster at event timestamp.
            - No duplicate PlayerPerformance entry (player_id, event_id, match_id).
        """

        # Validate entities exist
        if player_id not in self.players:
            return {"success": False, "error": "Player not found"}
        if event_id not in self.events:
            return {"success": False, "error": "Event not found"}
        if match_id not in self.matches:
            return {"success": False, "error": "Match not found"}

        # Validate event belongs to given match
        event = self.events[event_id]
        if event["match_id"] != match_id:
            return {"success": False, "error": "Event is not part of the specified match"}

        # Validate performance not already recorded
        key = (player_id, event_id, match_id)
        if key in self.player_performances:
            return {"success": False, "error": "PlayerPerformance already exists for these IDs"}

        # Find player's team
        player = self.players[player_id]
        team_id = player["team_id"]
        if team_id not in self.teams:
            return {"success": False, "error": "Player's team not found"}

        # Get event time
        event_time = event["timestamp"]

        # Look up roster at event_time in team.roster_history
        team = self.teams[team_id]
        roster_history = team.get("roster_history", [])
        roster_at_time = None
        # Get latest roster at or before event_time
        for rh in sorted(roster_history, key=lambda r: r["timestamp"], reverse=True):
            if rh["timestamp"] <= event_time:
                roster_at_time = rh["roster"]
                break
        if roster_at_time is None:
            # If no historic entry, fall back to current roster (if any)
            roster_at_time = team.get("roster", [])
        if player_id not in roster_at_time:
            return {"success": False, "error": "Player was not on the team roster at event time"}

        # All checks passed: add entry
        self.player_performances[key] = {
            "player_id": player_id,
            "event_id": event_id,
            "match_id": match_id,
            "metrics": metrics
        }

        return {"success": True, "message": "PlayerPerformance entry added"}

    def update_player_performance_metrics(
        self, 
        player_id: str, 
        event_id: str, 
        match_id: str, 
        metrics_update: Dict[str, Any]
    ) -> dict:
        """
        Update the metrics (including possibly spatial_coordinates or any other keys) for an existing PlayerPerformance record.

        Args:
            player_id (str): The ID of the player.
            event_id (str): The event ID.
            match_id (str): The match ID.
            metrics_update (Dict[str, Any]): Dictionary of metrics to update (merged into existing metrics).

        Returns:
            dict:
                { "success": True, "message": "PlayerPerformance metrics updated successfully." }
                OR
                { "success": False, "error": "PlayerPerformance record not found." }

        Constraints:
            - PlayerPerformance record for the given (player_id, event_id, match_id) must exist.
            - Only provided keys are updated (existing metrics keys are merged/overwritten).
        """
        key = (player_id, event_id, match_id)
        if key not in self.player_performances:
            return { "success": False, "error": "PlayerPerformance record not found." }

        # Update metrics field
        self.player_performances[key]["metrics"].update(metrics_update)
        return { "success": True, "message": "PlayerPerformance metrics updated successfully." }

    def add_event(self, event_id: str, name: str, match_id: str, timestamp: float, event_type: str) -> dict:
        """
        Add a new event with all required attributes to the analytics platform.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Event name/description.
            match_id (str): ID of the associated match (must exist).
            timestamp (float): Event timestamp (Unix time, must be valid).
            event_type (str): Type of event (e.g., goal, save).

        Returns:
            dict: Success or failure information. Success gives message. Failure gives error reason.

        Constraints:
            - event_id must be unique (cannot already exist).
            - match_id must exist in the platform.
            - timestamp must be a float (non-negative).
            - All fields required.
        """
        # Mandatory parameter check
        if not all([event_id, name, match_id, event_type]):
            return {"success": False, "error": "All fields are required."}
        if not isinstance(timestamp, (int, float)):
            return {"success": False, "error": "Timestamp must be a numeric value."}
        if timestamp < 0:
            return {"success": False, "error": "Timestamp must be non-negative."}

        if event_id in self.events:
            return {"success": False, "error": "Event ID already exists."}

        if match_id not in self.matches:
            return {"success": False, "error": "Linked match does not exist."}

        # Construct and add the event
        event_info = {
            "event_id": event_id,
            "name": name,
            "match_id": match_id,
            "timestamp": float(timestamp),
            "event_type": event_type
        }
        self.events[event_id] = event_info
        return {"success": True, "message": "Event added successfully."}

    def update_event_information(
        self,
        event_id: str,
        name: str = None,
        match_id: str = None,
        timestamp: float = None,
        event_type: str = None
    ) -> dict:
        """
        Modify event details, such as match, name, timestamp, or type.

        Args:
            event_id (str): The ID of the event to modify.
            name (str, optional): New name for the event.
            match_id (str, optional): New match_id to associate with the event (must exist).
            timestamp (float, optional): New event timestamp (Unix time, must be non-negative).
            event_type (str, optional): New event type.

        Returns:
            dict: {
                "success": True,
                "message": "Event updated successfully."
            } OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Event must exist.
            - If match_id is changed, new match_id must already exist.
            - timestamp, if specified, must be non-negative.
            - At least one update field must be provided.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event not found." }

        event = self.events[event_id]
        updated = False

        if name is not None:
            event["name"] = name
            updated = True

        if match_id is not None:
            if match_id not in self.matches:
                return { "success": False, "error": "match_id does not exist." }
            event["match_id"] = match_id
            updated = True

        if timestamp is not None:
            if not isinstance(timestamp, (int, float)) or timestamp < 0:
                return { "success": False, "error": "Invalid timestamp." }
            event["timestamp"] = timestamp
            updated = True

        if event_type is not None:
            event["event_type"] = event_type
            updated = True

        if not updated:
            return { "success": False, "error": "No valid update parameters provided." }

        self.events[event_id] = event
        return { "success": True, "message": "Event updated successfully." }

    def update_player_info(
        self,
        player_id: str,
        position: str = None,
        stats_overview: dict = None,
        team_id: str = None,
        name: str = None
    ) -> dict:
        """
        Modify a player's information (position, stats_overview, team_id, name).

        Args:
            player_id (str): ID of player to update (required).
            position (str, optional): New position.
            stats_overview (dict, optional): Updated stats_overview dictionary.
            team_id (str, optional): New team assignment (team must exist).
            name (str, optional): New player name.

        Returns:
            dict: Success or error status.

        Constraints:
            - player_id must exist.
            - If updating team_id: new team must exist, update rosters accordingly.
            - All fields are optional (at least one must be provided to update).
        """
        # Check player exists
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
    
        player = self.players[player_id]
        updates = []

        # Update position
        if position is not None:
            player["position"] = position
            updates.append("position")

        # Update stats_overview
        if stats_overview is not None:
            player["stats_overview"] = stats_overview
            updates.append("stats_overview")

        # Update name
        if name is not None:
            player["name"] = name
            updates.append("name")

        # Update team assignment (and fix team rosters)
        if team_id is not None:
            if team_id not in self.teams:
                return { "success": False, "error": "Team does not exist" }
            old_team_id = player["team_id"]
            if old_team_id != team_id:
                # Remove from old team roster if present
                if old_team_id in self.teams:
                    old_roster = self.teams[old_team_id].get("roster", [])
                    if player_id in old_roster:
                        old_roster.remove(player_id)
                # Add to new team roster if not already present
                new_roster = self.teams[team_id].setdefault("roster", [])
                if player_id not in new_roster:
                    new_roster.append(player_id)
                # Update in player info
                player["team_id"] = team_id
                updates.append("team_id")
    
        if not updates:
            return { "success": True, "message": "No attributes updated (idempotent)." }

        return { "success": True, "message": "Player info updated successfully." }

    def update_match_info(
        self,
        match_id: str,
        date: str = None,
        participating_team_ids: list = None,
        location: str = None,
        result: dict = None,
    ) -> dict:
        """
        Update match details such as participating teams, result, or date.

        Args:
            match_id (str): Identifier of the match to update.
            date (str, optional): New date for the match.
            participating_team_ids (List[str], optional): New list of team IDs.
            location (str, optional): New location for the match.
            result (dict, optional): New match result data.

        Returns:
            dict: 
              On success: { "success": True, "message": "Match info updated for match_id <id>" }
              On failure: { "success": False, "error": <reason> }

        Constraints:
            - match_id must exist in current matches.
            - If participating_team_ids provided, all team_ids must exist in teams.
            - Only updates fields that are explicitly provided/non-None.
        """
        # Validation for match existence
        if match_id not in self.matches:
            return { "success": False, "error": f"Match with id '{match_id}' does not exist." }

        match_info = self.matches[match_id]

        # Validate participating_team_ids if given
        if participating_team_ids is not None:
            if not isinstance(participating_team_ids, list):
                return { "success": False, "error": "participating_team_ids must be a list." }
            missing_teams = [tid for tid in participating_team_ids if tid not in self.teams]
            if missing_teams:
                return { "success": False, "error": f"Team IDs not found: {missing_teams}" }
            match_info["participating_team_ids"] = participating_team_ids

        if date is not None:
            if not isinstance(date, str):
                return { "success": False, "error": "date must be a string." }
            match_info["date"] = date

        if location is not None:
            if not isinstance(location, str):
                return { "success": False, "error": "location must be a string." }
            match_info["location"] = location

        if result is not None:
            if not isinstance(result, dict) and result is not None:
                return { "success": False, "error": "result must be a dictionary or None." }
            match_info["result"] = result

        self.matches[match_id] = match_info
        return { "success": True, "message": f"Match info updated for match_id {match_id}" }

    def remove_player_performance(self, player_id: str, event_id: str, match_id: str) -> dict:
        """
        Delete a PlayerPerformance record matching the identifiers (player_id, event_id, match_id).

        Args:
            player_id (str): ID of the player.
            event_id (str): ID of the event.
            match_id (str): ID of the match.

        Returns:
            dict: {
                "success": True,
                "message": "Player performance removed."
            }
            or
            {
                "success": False,
                "error": "Player performance not found."
            }
    
        Constraints:
            - The (player_id, event_id, match_id) record must exist in player_performances.
            - No exceptions are raised; errors are reported in the returned dict.
        """
        key = (player_id, event_id, match_id)
        if key not in self.player_performances:
            return { "success": False, "error": "Player performance not found." }
        del self.player_performances[key]
        return { "success": True, "message": "Player performance removed." }

    def remove_event(self, event_id: str) -> dict:
        """
        Delete an event entry from the platform. Also removes any PlayerPerformance entries
        that reference this event for consistency.

        Args:
            event_id (str): The ID of the event to delete.

        Returns:
            dict: {
                "success": True,
                "message": f"Event {event_id} and associated player performances deleted."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The event must exist.
            - All PlayerPerformance entries referencing this event will also be deleted (data integrity).
        """
        if event_id not in self.events:
            return { "success": False, "error": f"Event {event_id} does not exist." }
    
        # Remove the event itself
        del self.events[event_id]

        # Remove associated player performances
        to_remove = [
            key for key in self.player_performances 
            if key[1] == event_id
        ]
        for key in to_remove:
            del self.player_performances[key]

        return {
            "success": True,
            "message": f"Event {event_id} and {len(to_remove)} associated player performances deleted."
        }


class SportsAnalyticsPlatform(BaseEnv):
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
            if key == "player_performances" and isinstance(value, dict):
                normalized = {}
                for perf in value.values():
                    if not isinstance(perf, dict):
                        continue
                    player_id = perf.get("player_id")
                    event_id = perf.get("event_id")
                    match_id = perf.get("match_id")
                    if player_id and event_id and match_id:
                        normalized[(player_id, event_id, match_id)] = copy.deepcopy(perf)
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

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def get_team_roster_at_time(self, **kwargs):
        return self._call_inner_tool('get_team_roster_at_time', kwargs)

    def get_players_by_team(self, **kwargs):
        return self._call_inner_tool('get_players_by_team', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def get_events_by_ids(self, **kwargs):
        return self._call_inner_tool('get_events_by_ids', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def get_player_performance(self, **kwargs):
        return self._call_inner_tool('get_player_performance', kwargs)

    def get_team_player_performances_for_events(self, **kwargs):
        return self._call_inner_tool('get_team_player_performances_for_events', kwargs)

    def has_player_performance_spatial_coordinates(self, **kwargs):
        return self._call_inner_tool('has_player_performance_spatial_coordinates', kwargs)

    def generate_team_event_heatmap(self, **kwargs):
        return self._call_inner_tool('generate_team_event_heatmap', kwargs)

    def validate_event_and_match_links(self, **kwargs):
        return self._call_inner_tool('validate_event_and_match_links', kwargs)

    def list_all_teams(self, **kwargs):
        return self._call_inner_tool('list_all_teams', kwargs)

    def list_all_players(self, **kwargs):
        return self._call_inner_tool('list_all_players', kwargs)

    def list_all_matches(self, **kwargs):
        return self._call_inner_tool('list_all_matches', kwargs)

    def update_team_roster(self, **kwargs):
        return self._call_inner_tool('update_team_roster', kwargs)

    def add_roster_history_entry(self, **kwargs):
        return self._call_inner_tool('add_roster_history_entry', kwargs)

    def add_player_performance(self, **kwargs):
        return self._call_inner_tool('add_player_performance', kwargs)

    def update_player_performance_metrics(self, **kwargs):
        return self._call_inner_tool('update_player_performance_metrics', kwargs)

    def add_event(self, **kwargs):
        return self._call_inner_tool('add_event', kwargs)

    def update_event_information(self, **kwargs):
        return self._call_inner_tool('update_event_information', kwargs)

    def update_player_info(self, **kwargs):
        return self._call_inner_tool('update_player_info', kwargs)

    def update_match_info(self, **kwargs):
        return self._call_inner_tool('update_match_info', kwargs)

    def remove_player_performance(self, **kwargs):
        return self._call_inner_tool('remove_player_performance', kwargs)

    def remove_event(self, **kwargs):
        return self._call_inner_tool('remove_event', kwargs)
