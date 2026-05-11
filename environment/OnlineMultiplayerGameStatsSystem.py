# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class PlayerInfo(TypedDict):
    player_id: str
    username: str
    profile_data: Dict[str, Any]
    achievements: List[str]  # List of achievement_ids

class MatchInfo(TypedDict):
    match_id: str
    game_title: str
    start_time: float  # Timestamp
    end_time: float    # Timestamp
    duration: float    # Duration in seconds
    outcome: str
    match_data: Dict[str, Any]

class PlayerMatchParticipationInfo(TypedDict):
    player_id: str
    match_id: str
    stats_in_match: Dict[str, Any]  # Such as kills, deaths, score
    role: str
    team: str

class AchievementInfo(TypedDict):
    achievement_id: str
    player_id: str
    achievement_type: str
    date_earned: float    # Timestamp

class _GeneratedEnvImpl:
    def __init__(self):
        # Players: {player_id: PlayerInfo}
        self.players: Dict[str, PlayerInfo] = {}

        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Participations: {match_id: [PlayerMatchParticipationInfo]}
        # (Associates players with matches and their match-specific stats)
        self.participations: Dict[str, List[PlayerMatchParticipationInfo]] = {}

        # Achievements: {achievement_id: AchievementInfo}
        self.achievements: Dict[str, AchievementInfo] = {}

        # Constraint notes:
        # - Each match must be linked to at least one player via PlayerMatchParticipationInfo
        # - Match durations are computed as end_time - start_time and must be non-negative
        # - Player statistics in a match are only valid if the player is associated with that match
        # - Only completed matches (with valid start and end times) are included when querying durations

    def get_player_by_username(self, username: str) -> dict:
        """
        Retrieve the player profile by username.

        Args:
            username (str): The username to query.

        Returns:
            dict: {
                "success": True,
                "data": PlayerInfo,  # The matched player's info
            }
            or
            {
                "success": False,
                "error": str  # Reason why player could not be retrieved
            }

        Constraints:
            - Usernames are assumed unique in the player base.
        """
        for player in self.players.values():
            if player["username"] == username:
                return { "success": True, "data": player }
        return { "success": False, "error": f"Player with username '{username}' not found" }

    def get_player_by_id(self, player_id: str) -> dict:
        """
        Retrieve the player profile for a specified player_id.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict:
                - On success: {"success": True, "data": PlayerInfo}
                - On failure: {"success": False, "error": "Player not found"}

        Constraints:
            - The given player_id must exist in the player mapping.
        """
        player_info = self.players.get(player_id)
        if player_info is None:
            return {"success": False, "error": "Player not found"}
        return {"success": True, "data": player_info}

    def list_player_match_participations(self, player_id: str) -> dict:
        """
        List all matches in which the given player has participated,
        returning participation details (roles, stats, etc.).

        Args:
            player_id (str): The ID of the player.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PlayerMatchParticipationInfo]  # (List may be empty)
                }
            or
                {
                    "success": False,
                    "error": str  # Reason: e.g. "Player not found"
                }

        Constraints:
            - Player must exist.
            - Only participations linked to player_id are included.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player not found"}

        participations_list = []
        for match_participations in self.participations.values():
            for participation in match_participations:
                if participation["player_id"] == player_id:
                    participations_list.append(participation)

        return {"success": True, "data": participations_list}

    def filter_participations_by_game_title(self, player_id: str, game_title: str) -> dict:
        """
        Retrieve a list of PlayerMatchParticipationInfo for the given player,
        filtered to only include matches with the specified game_title.

        Args:
            player_id (str): The player's unique ID to filter participations for.
            game_title (str): The game title to filter matches by.

        Returns:
            dict:
                success: True/False
                data: list of PlayerMatchParticipationInfo for this player and game_title (may be empty)
                error: present only on failure
        Constraints:
            - player_id must exist in the system.
            - If no participations or no matches for the game_title, result list is empty.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player not found"}
    
        filtered_participations = []
        for match_id, participation_list in self.participations.items():
            # Only check participations for this player
            for participation in participation_list:
                if participation["player_id"] != player_id:
                    continue
                match_info = self.matches.get(match_id)
                if match_info is None:
                    # Corrupt/missing data, skip this participation
                    continue
                if match_info["game_title"] == game_title:
                    filtered_participations.append(participation)
    
        return {"success": True, "data": filtered_participations}

    def get_match_info(self, match_id: str) -> dict:
        """
        Retrieve the full details of a match given its match_id.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict:
                On Success:
                    {
                        "success": True,
                        "data": MatchInfo  # Dictionary with all details about the match
                    }
                On Failure:
                    {
                        "success": False,
                        "error": "Match not found"
                    }

        Constraints:
            - The match_id must exist in the matches dictionary.
            - No validation of participations, duration, or completion status is required for this query.
        """
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match }

    def get_match_duration(self, match_id: str) -> dict:
        """
        Return the duration (in seconds) of a match if it is completed (i.e., has valid start and end times,
        and duration >= 0).

        Args:
            match_id (str): The ID of the match to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": float,  # Duration in seconds
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # Reason why duration could not be returned.
                    }

        Constraints:
            - Match must exist.
            - Match must have valid, non-None numeric start_time and end_time.
            - Duration must be non-negative.
            - Only completed matches are eligible.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match does not exist"}

        start_time = match.get("start_time")
        end_time = match.get("end_time")
        duration = match.get("duration")

        # Check for valid start and end times: not None and numeric
        if (
            start_time is None or end_time is None
            or not isinstance(start_time, (int, float))
            or not isinstance(end_time, (int, float))
        ):
            return {"success": False, "error": "Match is not completed"}

        # Check: end_time should be >= start_time, duration >= 0
        computed_duration = end_time - start_time

        if computed_duration < 0:
            return {"success": False, "error": "Match is not completed"}

        # Use the stored duration if it's valid and matches the computation
        if duration is not None and isinstance(duration, (int, float)):
            # Optional: sanity-check that stored duration matches computed_duration
            if abs(duration - computed_duration) > 1e-3:
                # Stick with computed_duration (for safety)
                return {"success": True, "data": computed_duration}
            return {"success": True, "data": duration}
        else:
            return {"success": True, "data": computed_duration}

    def get_latest_completed_match(self, player_id: str, game_title: str = None) -> dict:
        """
        Find the most recent completed match for the specified player. Optionally filter by game_title.

        Args:
            player_id (str): The ID of the player.
            game_title (str, optional): Specific game title to filter matches by. If None, all games are considered.

        Returns:
            dict: 
                If success:
                    {
                        "success": True,
                        "data": MatchInfo | None  # Info of most recent completed match, or None if not found
                    }
                If failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - player_id must exist in self.players.
            - Only matches where the player participated, that are completed (start and end time valid, duration >= 0), are considered.
            - If game_title is given, only matches for that title are considered.
        """
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist"}

        found_matches = []
        # Find all participations for this player
        for match_id, participations in self.participations.items():
            for ppm in participations:
                if ppm["player_id"] == player_id:
                    # Get the match info
                    match = self.matches.get(match_id)
                    if not match:
                        continue
                    # must have valid start_time, end_time, duration
                    start = match.get("start_time")
                    end = match.get("end_time")
                    duration = match.get("duration")
                    if (
                        isinstance(start, (float, int)) and
                        isinstance(end, (float, int)) and
                        isinstance(duration, (float, int)) and
                        duration >= 0 and
                        end > start  # End time is after start
                    ):
                        if game_title is None or match.get("game_title") == game_title:
                            found_matches.append(match)
                    # Only completed matches considered
                    break  # Participation found for this match; no need to check others

        if not found_matches:
            return {"success": True, "data": None}
        # Pick the most recent one (latest end_time)
        latest_match = max(found_matches, key=lambda m: m["end_time"])
        return {"success": True, "data": latest_match}

    def list_player_achievements(self, player_id: str) -> dict:
        """
        Retrieve all achievements earned by a player.

        Args:
            player_id (str): The unique identifier of the player.

        Returns:
            dict: {
                "success": True,
                "data": List[AchievementInfo],  # A list of achievements (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., player not found
            }

        Constraints:
            - player_id must exist in the system.
            - Only achievements earned by the specified player are returned.
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }

        # Fetch achievements directly related to this player
        achievements_list = [
            achievement for achievement in self.achievements.values()
            if achievement["player_id"] == player_id
        ]
        return { "success": True, "data": achievements_list }

    def get_achievement_info(self, achievement_id: str) -> dict:
        """
        Retrieve the details of an achievement using its achievement_id.

        Args:
            achievement_id (str): The unique ID of the achievement.

        Returns:
            dict: {
              "success": True,
              "data": AchievementInfo  # if found
            } or {
              "success": False,
              "error": str  # If achievement_id does not exist
            }

        Constraints:
            - The achievement_id must exist in the 'achievements' dictionary.
        """
        achievement = self.achievements.get(achievement_id)
        if not achievement:
            return { "success": False, "error": "Achievement not found" }
        return { "success": True, "data": achievement }

    def add_player(self, player_id: str, username: str, profile_data: dict) -> dict:
        """
        Add a new player profile to the system.

        Args:
            player_id (str): Unique player identifier.
            username (str): Desired unique username.
            profile_data (dict): Arbitrary player profile metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Player <username> added."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - player_id must be unique in the system.
            - username must be unique in the system.
            - Achievements is initialized as an empty list.
        """
        # Check required fields
        if not player_id or not isinstance(player_id, str):
            return {"success": False, "error": "player_id must be a non-empty string"}
        if not username or not isinstance(username, str):
            return {"success": False, "error": "username must be a non-empty string"}
        if not isinstance(profile_data, dict):
            return {"success": False, "error": "profile_data must be a dictionary"}
    
        if player_id in self.players:
            return {"success": False, "error": "player_id already exists"}
        # Enforce username uniqueness
        for p in self.players.values():
            if p["username"] == username:
                return {"success": False, "error": "username already exists"}

        new_player = {
            "player_id": player_id,
            "username": username,
            "profile_data": profile_data,
            "achievements": []
        }
        self.players[player_id] = new_player

        return {"success": True, "message": f"Player {username} added."}

    def update_player_profile(self, player_id: str, profile_data: dict) -> dict:
        """
        Update the profile data for a player.

        Args:
            player_id (str): The unique ID of the player whose profile is to be updated.
            profile_data (dict): The profile data to update. Should be a dictionary.

        Returns:
            dict: {
                "success": True,
                "message": "Player profile updated"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - The player must exist.
            - profile_data must be a dictionary.
            - Updates only the profile_data field (merging into any existing keys).
        """
        if player_id not in self.players:
            return { "success": False, "error": "Player not found" }
        if not isinstance(profile_data, dict):
            return { "success": False, "error": "profile_data must be a dictionary" }

        # Merge the existing profile_data with the new one.
        # A None value explicitly deletes the key from the stored profile.
        current_profile = self.players[player_id].get("profile_data", {})
        if not isinstance(current_profile, dict):
            # This should not occur, but defensively
            current_profile = {}

        for key, value in profile_data.items():
            if value is None:
                current_profile.pop(key, None)
            else:
                current_profile[key] = value
        self.players[player_id]["profile_data"] = current_profile

        return { "success": True, "message": "Player profile updated" }

    def add_match(
        self,
        match_id: str,
        game_title: str,
        start_time: float,
        end_time: float,
        outcome: str,
        match_data: Dict[str, Any]
    ) -> dict:
        """
        Insert a new match into the system.

        Args:
            match_id (str): Unique identifier for the match.
            game_title (str): Title of the game for this match.
            start_time (float): Unix timestamp when match started.
            end_time (float): Unix timestamp when match ended.
            outcome (str): Match outcome (win/lose/draw/etc).
            match_data (Dict): Additional match metadata.

        Returns:
            dict: {"success": True, "message": "Match <id> added."}
                  or
                  {"success": False, "error": "<reason>"}

        Constraints:
            - match_id must be unique.
            - start_time and end_time must be valid numbers and end_time >= start_time.
            - duration is computed as end_time - start_time and must be non-negative.
            - Match can be added before participations exist.
        """
        if not match_id or match_id in self.matches:
            return {"success": False, "error": "Match ID already exists or is invalid."}
        if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
            return {"success": False, "error": "Invalid start_time or end_time."}
        if end_time < start_time:
            return {"success": False, "error": "Match end_time cannot be earlier than start_time."}

        duration = end_time - start_time

        # Construct the MatchInfo dict
        match_info: MatchInfo = {
            "match_id": match_id,
            "game_title": game_title,
            "start_time": float(start_time),
            "end_time": float(end_time),
            "duration": float(duration),
            "outcome": outcome,
            "match_data": match_data
        }

        self.matches[match_id] = match_info

        # Ensure participations entry exists, even if empty (no participations yet)
        if match_id not in self.participations:
            self.participations[match_id] = []

        return {"success": True, "message": f"Match {match_id} added."}

    def update_match_info(self, match_id: str, updates: Dict[str, Any]) -> dict:
        """
        Update the properties or outcome of a match.

        Args:
            match_id (str): The identifier of the match to update.
            updates (dict): Key-value pairs of match fields to update. 
                Valid fields: game_title, start_time, end_time, outcome, match_data

        Returns:
            dict: {
                "success": True,
                "message": "Match information updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only fields belonging to MatchInfo can be updated.
            - If start_time or end_time are updated, duration is recomputed as end_time - start_time.
            - The duration must not be negative.
            - If match_id does not exist, operation fails.
        """
        # Validate match existence
        if match_id not in self.matches:
            return {"success": False, "error": "Match not found"}

        # Allowed fields to update
        allowed_fields = {"game_title", "start_time", "end_time", "outcome", "match_data"}
        match = self.matches[match_id]

        old_start = match["start_time"]
        old_end = match["end_time"]

        # Apply only allowed updates
        for key in updates.keys():
            if key not in allowed_fields:
                continue  # ignore silently
            match[key] = updates[key]

        # Recompute duration if timing fields changed
        start_time = match.get("start_time", old_start)
        end_time = match.get("end_time", old_end)

        # If either changed, recompute duration
        if ("start_time" in updates) or ("end_time" in updates):
            duration = end_time - start_time
            if duration < 0:
                # Revert changes before returning error
                match["start_time"] = old_start
                match["end_time"] = old_end
                match["duration"] = old_end - old_start
                return {
                    "success": False,
                    "error": "Invalid start_time/end_time: duration would be negative"
                }
            else:
                match["duration"] = duration

        self.matches[match_id] = match
        return {"success": True, "message": "Match information updated successfully"}

    def add_player_match_participation(
        self, 
        player_id: str, 
        match_id: str, 
        stats_in_match: dict, 
        role: str, 
        team: str
    ) -> dict:
        """
        Link a player to a match with statistics for that match.
    
        Args:
            player_id (str): ID of the player
            match_id (str): ID of the match
            stats_in_match (dict): Dictionary of stats (e.g., kills, deaths, score) for the player in this match
            role (str): The role of the player in that match
            team (str): The team name or id for that player in the match

        Returns:
            dict: 
                - {"success": True, "message": "Player participation added to match."}
                - or {"success": False, "error": <reason>}

        Constraints:
            - player_id must exist in players.
            - match_id must exist in matches.
            - The same player cannot be linked to the same match more than once.
            - All attributes must be provided.
        """
        # Validate player existence
        if player_id not in self.players:
            return { "success": False, "error": "Player does not exist" }
        # Validate match existence
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }
        # Validate not already linked
        participation_list = self.participations.get(match_id, [])
        for participation in participation_list:
            if participation["player_id"] == player_id:
                return { "success": False, "error": "Player already linked to this match" }
        # Create the participation record
        new_participation = {
            "player_id": player_id,
            "match_id": match_id,
            "stats_in_match": stats_in_match if stats_in_match is not None else {},
            "role": role,
            "team": team
        }
        participation_list.append(new_participation)
        self.participations[match_id] = participation_list
        return { "success": True, "message": "Player participation added to match." }

    def update_player_match_stats(
        self,
        player_id: str,
        match_id: str,
        stats_update: dict
    ) -> dict:
        """
        Update the statistics (stats_in_match) for a specific player in a specific match.

        Args:
            player_id (str): Unique identifier for the player.
            match_id (str): Unique identifier for the match.
            stats_update (dict): Dictionary of stat fields and values to update.

        Returns:
            dict: {
                "success": True,
                "message": "Player match stats updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - player_id and match_id must exist.
            - Player must be participating in the match (PlayerMatchParticipationInfo exists).
            - Only updates provided fields; other stats remain unchanged.
        """

        # Validate match exists
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist."}

        # Validate player exists
        if player_id not in self.players:
            return {"success": False, "error": "Player does not exist."}

        # Validate stats_update format
        if not isinstance(stats_update, dict) or not stats_update:
            return {"success": False, "error": "Invalid stats_update (must be non-empty dict)."}

        # Retrieve participations list for the match
        participations = self.participations.get(match_id)
        if not participations:
            return {"success": False, "error": "No participations found for match."}

        # Find PlayerMatchParticipation for the player
        for participation in participations:
            if participation["player_id"] == player_id:
                # Update stats_in_match
                if "stats_in_match" not in participation or not isinstance(participation["stats_in_match"], dict):
                    participation["stats_in_match"] = {}
                participation["stats_in_match"].update(stats_update)
                return {
                    "success": True,
                    "message": "Player match stats updated successfully."
                }

        # Player is not participating in this match
        return {"success": False, "error": "Player is not participating in the specified match."}

    def add_achievement(
        self,
        achievement_id: str,
        player_id: str,
        achievement_type: str,
        date_earned: float,
    ) -> dict:
        """
        Add a new achievement record for a player.

        Args:
            achievement_id (str): Unique identifier for the achievement.
            player_id (str): The player who earned the achievement. Must exist in players.
            achievement_type (str): The type/category of the achievement.
            date_earned (float): The timestamp when the achievement was earned.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Achievement added for player <player_id>" }
                On failure:
                    { "success": False, "error": "<reason>" }
    
        Constraints:
            - achievement_id must be unique.
            - player_id must already exist in the system.
            - The achievement is linked to the player in both achievements dict and player's achievement list.
        """

        if not achievement_id or not player_id or not achievement_type or date_earned is None:
            return { "success": False, "error": "Missing required input data" }

        if achievement_id in self.achievements:
            return { "success": False, "error": f"Achievement ID '{achievement_id}' already exists" }

        if player_id not in self.players:
            return { "success": False, "error": f"Player with ID '{player_id}' does not exist" }

        achievement_info: AchievementInfo = {
            "achievement_id": achievement_id,
            "player_id": player_id,
            "achievement_type": achievement_type,
            "date_earned": date_earned
        }

        self.achievements[achievement_id] = achievement_info

        # Add achievement to player's achievements list if not present
        if achievement_id not in self.players[player_id]["achievements"]:
            self.players[player_id]["achievements"].append(achievement_id)
    
        return { "success": True, "message": f"Achievement added for player {player_id}" }

    def remove_achievement(self, achievement_id: str) -> dict:
        """
        Removes an achievement from a player and from the system.

        Args:
            achievement_id (str): The ID of the achievement to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Achievement removed from player."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - The achievement must exist in the system.
            - The player associated with the achievement must exist to remove the reference from their achievement list.
        """
        # Check if achievement exists
        if achievement_id not in self.achievements:
            return { "success": False, "error": "Achievement does not exist." }

        achievement = self.achievements[achievement_id]
        player_id = achievement["player_id"]

        # Remove from self.achievements
        del self.achievements[achievement_id]

        # Remove from player's achievements list if player exists
        if player_id not in self.players:
            return { "success": False, "error": "Associated player does not exist, achievement entry removed from system." }

        achievements_list = self.players[player_id].get("achievements", [])
        if achievement_id in achievements_list:
            achievements_list.remove(achievement_id)
            self.players[player_id]["achievements"] = achievements_list

        return { "success": True, "message": "Achievement removed from player." }


class OnlineMultiplayerGameStatsSystem(BaseEnv):
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
            if key == "participations" and isinstance(value, dict):
                normalized = {}
                for bucket_key, bucket_value in value.items():
                    if not isinstance(bucket_value, list):
                        continue
                    for participation in copy.deepcopy(bucket_value):
                        if not isinstance(participation, dict):
                            continue
                        match_id = participation.get("match_id") or bucket_key
                        if not match_id:
                            continue
                        normalized.setdefault(match_id, []).append(participation)
                setattr(env, key, normalized)
            else:
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

    def get_player_by_username(self, **kwargs):
        return self._call_inner_tool('get_player_by_username', kwargs)

    def get_player_by_id(self, **kwargs):
        return self._call_inner_tool('get_player_by_id', kwargs)

    def list_player_match_participations(self, **kwargs):
        return self._call_inner_tool('list_player_match_participations', kwargs)

    def filter_participations_by_game_title(self, **kwargs):
        return self._call_inner_tool('filter_participations_by_game_title', kwargs)

    def get_match_info(self, **kwargs):
        return self._call_inner_tool('get_match_info', kwargs)

    def get_match_duration(self, **kwargs):
        return self._call_inner_tool('get_match_duration', kwargs)

    def get_latest_completed_match(self, **kwargs):
        return self._call_inner_tool('get_latest_completed_match', kwargs)

    def list_player_achievements(self, **kwargs):
        return self._call_inner_tool('list_player_achievements', kwargs)

    def get_achievement_info(self, **kwargs):
        return self._call_inner_tool('get_achievement_info', kwargs)

    def add_player(self, **kwargs):
        return self._call_inner_tool('add_player', kwargs)

    def update_player_profile(self, **kwargs):
        return self._call_inner_tool('update_player_profile', kwargs)

    def add_match(self, **kwargs):
        return self._call_inner_tool('add_match', kwargs)

    def update_match_info(self, **kwargs):
        return self._call_inner_tool('update_match_info', kwargs)

    def add_player_match_participation(self, **kwargs):
        return self._call_inner_tool('add_player_match_participation', kwargs)

    def update_player_match_stats(self, **kwargs):
        return self._call_inner_tool('update_player_match_stats', kwargs)

    def add_achievement(self, **kwargs):
        return self._call_inner_tool('add_achievement', kwargs)

    def remove_achievement(self, **kwargs):
        return self._call_inner_tool('remove_achievement', kwargs)
