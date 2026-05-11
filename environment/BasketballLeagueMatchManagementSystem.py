# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class MatchInfo(TypedDict):
    match_id: str
    date: str
    team_home_id: str
    team_away_id: str
    score_home: int
    score_away: int
    status: str  # e.g., "scheduled", "completed"
    summary: str
    event_timeline: List[str]  # list of event_ids

class TeamInfo(TypedDict):
    team_id: str
    name: str
    roster: List[str]  # list of player_ids

class PlayerInfo(TypedDict):
    player_id: str
    name: str
    team_id: str
    stats: Dict[str, Any]  # stats keyed by match_id or stat type

class EventInfo(TypedDict):
    event_id: str
    match_id: str
    event_type: str
    timestamp: float
    involved_player_ids: List[str]
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # --- Constraints (annotated for future business logic) ---
        # - Every match must have exactly two participating teams.
        # - Team rosters must only include registered league players.
        # - Scores, summaries, and statistics are only available for completed matches.
        # - Event timelines are chronological and consistent with match duration.
        # - Player statistics are attributed per-match and updated upon match completion.

    def get_match_summary(self, match_id: str) -> dict:
        """
        Retrieve the summary field for a specific match by match_id.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict: 
                - { "success": True, "data": { "match_id": str, "summary": str } }
                  if the match exists and is completed.
                - { "success": False, "error": str }
                  if the match does not exist or the match is not completed.

        Constraints:
            - The match must exist.
            - Summaries are only available for matches with status == "completed".
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        if match.get("status") != "completed":
            return { "success": False, "error": "Summary only available for completed matches" }
        return {
            "success": True,
            "data": {
                "match_id": match_id,
                "summary": match.get("summary", "")
            }
        }

    def get_match_info(self, match_id: str) -> dict:
        """
        Retrieve all details for a specific match by match_id.

        Args:
            match_id (str): The unique identifier for the match.

        Returns:
            dict: 
                Success: { "success": True, "data": MatchInfo }
                Failure: { "success": False, "error": "Match not found" }

        Constraints:
            - match_id must exist in the system.
        """
        match_info = self.matches.get(match_id)
        if not match_info:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match_info }

    def get_match_status(self, match_id: str) -> dict:
        """
        Query the current status ("scheduled", "completed") of a match.

        Args:
            match_id (str): The unique identifier of the match to query.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status string (e.g., "scheduled", "completed")
            }
            OR
            {
                "success": False,
                "error": str  # Description of the error, e.g., "Match not found"
            }
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}
        return {"success": True, "data": match["status"]}

    def list_matches_by_status(self, status: str = None) -> dict:
        """
        List all matches, or those with a given status ("scheduled", "completed").

        Args:
            status (str, optional): If specified, filter matches by this status. Valid values (by convention): "scheduled", "completed".
    
        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of MatchInfo dicts (empty list if none found)
            }
        Notes:
            - If status is None or not provided, all matches are listed.
            - Status filtering is case-sensitive per data.
        """
        if status is None:
            matches = list(self.matches.values())
        else:
            matches = [
                match for match in self.matches.values()
                if match["status"] == status
            ]

        return {"success": True, "data": matches}

    def get_match_score(self, match_id: str) -> dict:
        """
        Retrieve the home and away scores for the specified match.

        Args:
            match_id (str): Unique identifier for the basketball match.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": {
                          "score_home": int,
                          "score_away": int
                      }
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Reason for failure (e.g., not found or not completed)
                    }

        Constraints:
            - The specified match must exist.
            - Scores are only available if match status is "completed".
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match does not exist" }

        if match['status'] != "completed":
            return { "success": False, "error": "Scores available only for completed matches" }

        return {
            "success": True,
            "data": {
                "score_home": match['score_home'],
                "score_away": match['score_away']
            }
        }

    def get_team_info(self, team_id: str) -> dict:
        """
        Retrieve details of a team, including team_id, name, and roster (list of player_ids).

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": TeamInfo  # Dict with keys 'team_id', 'name', 'roster'
                  }
                - On failure: {
                      "success": False,
                      "error": "Team not found"
                  }
        """
        team = self.teams.get(team_id)
        if not team:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team }

    def list_team_roster(self, team_id: str) -> dict:
        """
        Get the current roster (full PlayerInfo list) for a given team.

        Args:
            team_id (str): Unique team identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[PlayerInfo],  # List of player info dicts currently on the team's roster
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the error, e.g., team not found
            }

        Constraints:
            - The team must exist.
            - Roster will only include registered league players (if a data anomaly occurs, non-existent players are ignored).
        """
        team = self.teams.get(team_id)
        if not team:
            return {"success": False, "error": "Team does not exist."}
    
        roster_player_infos = []
        for pid in team["roster"]:
            player = self.players.get(pid)
            if player:
                roster_player_infos.append(player)
            # If player is not found, skip; data anomaly, but not a blocking error.

        return {"success": True, "data": roster_player_infos}

    def get_player_info(self, player_id: str) -> dict:
        """
        Retrieve individual player details along with associated team information.

        Args:
            player_id (str): Unique player identifier.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "player_info": PlayerInfo,
                    "team_info": TeamInfo or None
                }
            }
            or
            {
                "success": False,
                "error": "Player not found"
            }

        Constraints:
            - Returns player info if found.
            - Returns team info if the player's team_id entry exists, otherwise team_info is None.
        """
        player_info = self.players.get(player_id)
        if not player_info:
            return { "success": False, "error": "Player not found" }
        team_info = self.teams.get(player_info["team_id"])
        return {
            "success": True,
            "data": {
                "player_info": player_info,
                "team_info": team_info if team_info else None
            }
        }

    def get_player_stats_for_match(self, player_id: str, match_id: str) -> dict:
        """
        Retrieve the statistics for a specific player in a specific match.

        Args:
            player_id (str): The ID of the player.
            match_id (str): The ID of the match.

        Returns:
            dict: {
                "success": True,
                "data": dict  # The player's stats for the match
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - Player and match must exist.
            - Match status must be "completed" for stats to be available.
            - Player's stats for that match must exist.
        """
        # Check if player exists
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        # Check if match exists
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}

        match_info = self.matches[match_id]

        # Check if match is completed
        if match_info["status"] != "completed":
            return {"success": False, "error": "Statistics available only for completed matches"}

        # Get player's stats for the match
        player_info = self.players[player_id]
        stats = player_info.get("stats", {})
        match_stats = stats.get(match_id)

        if match_stats is None:
            return {"success": False, "error": "No statistics found for player in specified match"}

        return {"success": True, "data": match_stats}

    def get_match_event_timeline(self, match_id: str, with_details: bool = False) -> dict:
        """
        Retrieve the chronological list of event_ids, or event details, for a given match.

        Args:
            match_id (str): Unique identifier of the match to query.
            with_details (bool, optional): If True, returns list of event details (EventInfo);
                                           if False, returns only event_ids. Default is False.

        Returns:
            dict:
              On success:
                {
                    "success": True,
                    "data": List[str] | List[EventInfo],  # List of event_ids or list of event details
                }
              On failure:
                {
                    "success": False,
                    "error": str  # Error reason, e.g., "Match not found"
                }
        Constraints:
            - Provided match_id must exist.
        Notes:
            - If event_id in timeline is missing from the event store, it is skipped.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        event_ids = match.get("event_timeline", [])
        if with_details:
            details = [
                self.events[event_id]
                for event_id in event_ids
                if event_id in self.events
            ]
            return { "success": True, "data": details }
        else:
            return { "success": True, "data": event_ids }

    def get_event_info(self, event_id: str) -> dict:
        """
        Retrieve all fields for a specified event (basket, foul, substitution, etc.) by event_id.

        Args:
            event_id (str): The event's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": EventInfo
            }
            or
            {
                "success": False,
                "error": "Event not found"
            }
    
        Constraints:
            - event_id must exist in system.
        """
        event = self.events.get(event_id)
        if not event:
            return { "success": False, "error": "Event not found" }
        return { "success": True, "data": event }

    def list_all_matches(self) -> dict:
        """
        List all matches in the basketball league system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of all MatchInfo dicts (empty if none exist)
            }

        Constraints:
            - None. Returns all matches, regardless of status.
        """
        matches_list = list(self.matches.values())
        return { "success": True, "data": matches_list }

    def list_matches_by_team(self, team_id: str) -> dict:
        """
        Get all matches in which the specified team participated.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": List[MatchInfo]  # List of all matches where team_id == team_home_id or team_away_id
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Reason for failure, e.g., team does not exist
                    }

        Constraints:
            - The provided team_id must correspond to an existing team in the system.
        """
        if team_id not in self.teams:
            return { "success": False, "error": f"Team with id '{team_id}' does not exist" }

        matches = [
            match_info
            for match_info in self.matches.values()
            if match_info["team_home_id"] == team_id or match_info["team_away_id"] == team_id
        ]

        return { "success": True, "data": matches }

    def update_match_score(self, match_id: str, score_home: int, score_away: int) -> dict:
        """
        Modify the home and away scores for a specific match.
        Allowed only if the match exists, is completed, and the new scores are valid (non-negative integers).

        Args:
            match_id (str): Unique identifier of the match to update.
            score_home (int): New score for the home team (must be non-negative).
            score_away (int): New score for the away team (must be non-negative).

        Returns:
            dict: 
                { "success": True, "message": "Match scores updated." }
                OR
                { "success": False, "error": <reason str> }

        Constraints:
            - Match must exist.
            - Match status must be "completed".
            - Scores must be non-negative integers.
        """
        # Check for existence
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found." }

        # Check status constraint
        if match["status"] != "completed":
            return { "success": False, "error": "Scores can only be updated for completed matches." }

        # Validate scores
        if not (isinstance(score_home, int) and isinstance(score_away, int)):
            return { "success": False, "error": "Scores must be integers." }
        if score_home < 0 or score_away < 0:
            return { "success": False, "error": "Scores must be non-negative integers." }

        # Update scores
        match["score_home"] = score_home
        match["score_away"] = score_away
        self.matches[match_id] = match

        return { "success": True, "message": "Match scores updated." }

    def enter_match_summary(self, match_id: str, summary: str) -> dict:
        """
        Set or update the summary field for a match.
        Only allowed if the match status is 'completed'.

        Args:
            match_id (str): Unique identifier for the match.
            summary (str): The summary to set for the match.

        Returns:
            dict: {
                "success": True,
                "message": "Summary updated for match <match_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The match must exist.
            - The match status must be 'completed'.
        """

        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist"}

        match_info = self.matches[match_id]
        if match_info["status"] != "completed":
            return {"success": False, "error": "Match summary can only be set for completed matches"}

        match_info["summary"] = summary
        self.matches[match_id] = match_info

        return {"success": True, "message": f"Summary updated for match {match_id}"}

    def change_match_status(self, match_id: str, new_status: str) -> dict:
        """
        Update the status of a match (e.g., from 'scheduled' to 'completed'), enforcing constraints:
          - match_id must exist
          - new_status must be 'scheduled' or 'completed'
          - If setting to 'completed', both participating teams must exist

        Args:
            match_id (str): The unique identifier of the match to update.
            new_status (str): The updated status value ("scheduled", "completed").

        Returns:
            dict: {
                "success": True,
                "message": "Match status updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match not found."}
    
        match_info = self.matches[match_id]
        valid_statuses = {"scheduled", "completed"}
        if new_status not in valid_statuses:
            return {"success": False, "error": "Invalid status value."}
    
        # On completion, verify both teams exist and are set.
        if new_status == "completed":
            team_home_id = match_info.get("team_home_id")
            team_away_id = match_info.get("team_away_id")
            if not team_home_id or not team_away_id:
                return {"success": False, "error": "Both participating teams must be set before completing match."}
            if team_home_id not in self.teams or team_away_id not in self.teams:
                return {"success": False, "error": "One or both participating teams do not exist."}

        match_info["status"] = new_status
        self.matches[match_id] = match_info
        return {"success": True, "message": "Match status updated."}

    def update_player_stats_for_match(
        self, 
        player_id: str, 
        match_id: str, 
        new_stats: dict
    ) -> dict:
        """
        Update a player's statistics for a specific match. This can only be performed if the match is completed.

        Args:
            player_id (str): ID of the player to update.
            match_id (str): ID of the completed match.
            new_stats (dict): Dictionary of stat type(s) and new values, e.g. {"points": 28, "rebounds": 11}

        Returns:
            dict: 
                On success: { "success": True, "message": "Player statistics updated for match" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The player and match must exist.
            - The match must be completed.
            - Stats are attributed per-match.
            - Optionally, ensure the player is in one of the participating teams (recommended for data consistency).
        """
        # Existence checks
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }
        if not isinstance(new_stats, dict) or not new_stats:
            return { "success": False, "error": "Provided statistics must be a non-empty dictionary" }

        match = self.matches[match_id]

        # Ensure match is completed
        if match["status"] != "completed":
            return { "success": False, "error": "Cannot update stats: match is not completed" }

        # Optional: ensure the player participated in the match
        team_home_id = match["team_home_id"]
        team_away_id = match["team_away_id"]
        home_roster = self.teams.get(team_home_id, {}).get("roster", [])
        away_roster = self.teams.get(team_away_id, {}).get("roster", [])
        if player_id not in home_roster and player_id not in away_roster:
            return { "success": False, "error": "Player did not participate in this match" }

        player_info = self.players[player_id]
        stats_for_match = player_info.get("stats", {}).get(match_id, {})

        # Update with new/modified stats (merge)
        updated_stats = dict(stats_for_match)
        updated_stats.update(new_stats)
        # Write back to player's stats dictionary
        if "stats" not in player_info:
            player_info["stats"] = {}
        player_info["stats"][match_id] = updated_stats

        # Save back
        self.players[player_id] = player_info

        return { "success": True, "message": "Player statistics updated for match" }

    def add_event_to_match(
        self,
        match_id: str,
        event_id: str,
        event_type: str,
        timestamp: float,
        involved_player_ids: list,
        description: str
    ) -> dict:
        """
        Add a new event to the specified match's event timeline, maintaining chronological order.

        Args:
            match_id (str): Match to which the event belongs.
            event_id (str): Unique identifier for the new event.
            event_type (str): Type of event (e.g., 'basket', 'foul').
            timestamp (float): Timestamp of the event (seconds since match start).
            involved_player_ids (List[str]): Player IDs involved in the event.
            description (str): Description of the event.

        Returns:
            dict: {
                "success": True,
                "message": "Event added to match timeline."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The match must exist.
            - event_id must be unique and not already in events.
            - All involved_player_ids must correspond to existing players.
            - Timeline must remain sorted by event timestamp.
        """
        # Check match existence
        if match_id not in self.matches:
            return {"success": False, "error": "Match not found"}

        # Check unique event_id
        if event_id in self.events:
            return {"success": False, "error": "Event ID already exists"}

        # Validate involved_player_ids
        for pid in involved_player_ids:
            if pid not in self.players:
                return {"success": False, "error": f"Involved player id '{pid}' does not exist"}

        # Create new event
        new_event = {
            "event_id": event_id,
            "match_id": match_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "involved_player_ids": involved_player_ids,
            "description": description
        }
        # Add to global event registry
        self.events[event_id] = new_event

        # Insert event_id into the event timeline in the correct order by timestamp
        match_info = self.matches[match_id]
        timeline = match_info["event_timeline"]

        # Gather current events and their timestamps for ordering
        updated_timeline_events = []
        inserted = False
        for eid in timeline:
            current_event = self.events.get(eid)
            if not inserted and current_event and timestamp < current_event["timestamp"]:
                updated_timeline_events.append(event_id)
                inserted = True
            updated_timeline_events.append(eid)
        if not inserted:
            updated_timeline_events.append(event_id)
        match_info["event_timeline"] = updated_timeline_events

        return {"success": True, "message": "Event added to match timeline."}

    def update_team_roster(self, team_id: str, new_roster: list[str]) -> dict:
        """
        Change the player roster for a team. Roster must only include valid registered players.
        Each affected player's team_id will be updated to reflect the new team.

        Args:
            team_id (str): The unique identifier of the team whose roster is to be set.
            new_roster (List[str]): List of player_ids to assign as the team's new roster.

        Returns:
            dict: {
                "success": True, "message": "Team roster updated successfully."
            }
            or
            {
                "success": False, "error": <reason>
            }

        Constraints:
            - team_id must exist.
            - All player_ids must be registered in the league.
            - No duplicate player_ids in the roster.
        """
        # Check if team exists
        if team_id not in self.teams:
            return {"success": False, "error": "Team does not exist."}
    
        # Ensure no duplicates in roster
        if len(new_roster) != len(set(new_roster)):
            return {"success": False, "error": "Roster contains duplicate player_ids."}
    
        # Check every player_id is registered
        for pid in new_roster:
            if pid not in self.players:
                return {"success": False, "error": f"Player ID '{pid}' is not registered in the league."}

        # Remove players from this team's old roster (set their team association if they're not on new_roster)
        old_roster = set(self.teams[team_id]["roster"])
        new_roster_set = set(new_roster)

        removed_players = old_roster - new_roster_set
        for pid in removed_players:
            # Only dissociate if this player is in players, double check
            if pid in self.players and self.players[pid]["team_id"] == team_id:
                self.players[pid]["team_id"] = ""  # or None, representing free agent

        # Add/update new players: set team_id in PlayerInfo if not already matching
        for pid in new_roster:
            if self.players[pid]["team_id"] != team_id:
                self.players[pid]["team_id"] = team_id

        # Assign the new roster to the team
        self.teams[team_id]["roster"] = list(new_roster)

        return {"success": True, "message": "Team roster updated successfully."}

    def correct_event_timeline_order(self, match_id: str) -> dict:
        """
        Reorder or fix the event timeline for a match if out-of-order events are detected.

        Args:
            match_id (str): The match identifier whose timeline is to be corrected.
    
        Returns:
            dict: {
                "success": True,
                "message": "Event timeline corrected for match {match_id}"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. match not found, missing event)
            }
        Constraints:
            - The match with match_id must exist.
            - All event_ids in the match's event_timeline must exist in the events record.
            - The timeline will be reordered chronologically by event timestamp.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": f"Match with id {match_id} does not exist" }

        event_ids = match.get("event_timeline", [])

        # Gather (event_id, timestamp) tuples
        event_tuples = []
        for eid in event_ids:
            event = self.events.get(eid)
            if not event:
                return { "success": False, "error": f"Event {eid} not found for match {match_id}" }
            event_tuples.append((eid, event["timestamp"]))

        # Sort by timestamp
        sorted_events = sorted(event_tuples, key=lambda x: x[1])
        sorted_event_ids = [eid for eid, _ in sorted_events]

        # Update the match's event_timeline if changed
        match["event_timeline"] = sorted_event_ids
        self.matches[match_id] = match

        return {
            "success": True,
            "message": f"Event timeline corrected for match {match_id}"
        }

    def assign_player_to_team(self, player_id: str, team_id: str) -> dict:
        """
        Add a registered player to a team's roster, respecting registration constraints.

        Args:
            player_id (str): The ID of the player to assign.
            team_id (str): The ID of the target team.

        Returns:
            dict: {
                "success": True,
                "message": "Player <player_id> assigned to team <team_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both player and team must exist.
            - Team roster must only include registered league players.
            - Player is listed on only one team at a time.
            - Prevent duplicate entries.
            - Remove player from any previous team's roster if present.
        """
        # Existence checks
        if team_id not in self.teams:
            return {"success": False, "error": f"Team ID '{team_id}' does not exist"}
        if player_id not in self.players:
            return {"success": False, "error": f"Player ID '{player_id}' does not exist"}

        # Remove player from any previous team's roster
        old_team_id = self.players[player_id].get('team_id')
        if old_team_id and old_team_id in self.teams and player_id in self.teams[old_team_id]['roster']:
            self.teams[old_team_id]['roster'].remove(player_id)

        # Prevent duplicate entries in target team roster
        if player_id in self.teams[team_id]['roster']:
            return {"success": False, "error": f"Player '{player_id}' is already in team '{team_id}' roster"}

        # Add player to target team
        self.teams[team_id]['roster'].append(player_id)
        # Update player's team_id
        self.players[player_id]['team_id'] = team_id

        return {"success": True, "message": f"Player '{player_id}' assigned to team '{team_id}'"}


class BasketballLeagueMatchManagementSystem(BaseEnv):
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

    def get_match_summary(self, **kwargs):
        return self._call_inner_tool('get_match_summary', kwargs)

    def get_match_info(self, **kwargs):
        return self._call_inner_tool('get_match_info', kwargs)

    def get_match_status(self, **kwargs):
        return self._call_inner_tool('get_match_status', kwargs)

    def list_matches_by_status(self, **kwargs):
        return self._call_inner_tool('list_matches_by_status', kwargs)

    def get_match_score(self, **kwargs):
        return self._call_inner_tool('get_match_score', kwargs)

    def get_team_info(self, **kwargs):
        return self._call_inner_tool('get_team_info', kwargs)

    def list_team_roster(self, **kwargs):
        return self._call_inner_tool('list_team_roster', kwargs)

    def get_player_info(self, **kwargs):
        return self._call_inner_tool('get_player_info', kwargs)

    def get_player_stats_for_match(self, **kwargs):
        return self._call_inner_tool('get_player_stats_for_match', kwargs)

    def get_match_event_timeline(self, **kwargs):
        return self._call_inner_tool('get_match_event_timeline', kwargs)

    def get_event_info(self, **kwargs):
        return self._call_inner_tool('get_event_info', kwargs)

    def list_all_matches(self, **kwargs):
        return self._call_inner_tool('list_all_matches', kwargs)

    def list_matches_by_team(self, **kwargs):
        return self._call_inner_tool('list_matches_by_team', kwargs)

    def update_match_score(self, **kwargs):
        return self._call_inner_tool('update_match_score', kwargs)

    def enter_match_summary(self, **kwargs):
        return self._call_inner_tool('enter_match_summary', kwargs)

    def change_match_status(self, **kwargs):
        return self._call_inner_tool('change_match_status', kwargs)

    def update_player_stats_for_match(self, **kwargs):
        return self._call_inner_tool('update_player_stats_for_match', kwargs)

    def add_event_to_match(self, **kwargs):
        return self._call_inner_tool('add_event_to_match', kwargs)

    def update_team_roster(self, **kwargs):
        return self._call_inner_tool('update_team_roster', kwargs)

    def correct_event_timeline_order(self, **kwargs):
        return self._call_inner_tool('correct_event_timeline_order', kwargs)

    def assign_player_to_team(self, **kwargs):
        return self._call_inner_tool('assign_player_to_team', kwargs)

