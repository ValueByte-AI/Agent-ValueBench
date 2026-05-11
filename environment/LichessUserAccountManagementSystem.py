# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional



class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    registration_date: str
    profile_bio: str
    profile_avatar: str
    country: str
    account_status: str
    social_links: Dict[str, str]  # e.g., {'twitter': 'handle'}
    preferences: Dict[str, str]   # assuming serialized preferences

class RatingInfo(TypedDict):
    _id: str         # user_id
    variant: str
    rating: float
    rating_deviation: float
    games_played_in_variant: int

class GameInfo(TypedDict):
    game_id: str
    white_user_id: str
    black_user_id: str
    variant: str
    result: str
    moves: List[str]
    start_time: str
    end_time: str
    event_type: str
    is_rated: bool

class UserStatisticsInfo(TypedDict):
    _id: str    # user_id
    total_games: int
    wins: int
    draws: int
    losses: int
    win_rate: float
    longest_streak: int
    current_streak: int
    average_opponent_rating: float
    most_played_variant: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Lichess user account management system state.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Constraints: usernames must be unique; account_status governs visibility/access

        # Ratings: {user_id: {variant: RatingInfo}}
        self.ratings: Dict[str, Dict[str, RatingInfo]] = {}
        # Constraint: Each Rating is unique per (user_id, variant)

        # Games: {game_id: GameInfo}
        self.games: Dict[str, GameInfo] = {}
        # Constraint: Games must reference valid, existing users as participants

        # UserStatistics: {user_id: UserStatisticsInfo}
        self.user_statistics: Dict[str, UserStatisticsInfo] = {}
        # Constraint: UserStatistics must be kept in sync as new games are added

        # Constraints summary:
        # - Rating unique per (user_id, variant)
        # - Usernames unique
        # - Game participants reference real users
        # - User stats derived/synced from games
        # - Account status controls access

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve the full profile and account information for a specific username.

        Args:
            username (str): The unique username to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": UserInfo    # The full profile and account info
                }
                or
                {
                    "success": False,
                    "error": "Username does not exist"
                }

        Constraints:
            - Username must exist and be unique in the system.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "Username does not exist" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the full profile and account information for a user by their unique user id.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo  # The user's full profile and account info
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user_id must correspond to an existing user in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def check_username_exists(self, username: str) -> dict:
        """
        Check if the given username is registered (i.e., exists in the system).

        Args:
            username (str): The username to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if the username exists, False otherwise
            }

        Constraints:
            - Usernames are unique.
            - Comparison is exact, case-sensitive.
        """
        exists = any(user_info["username"] == username for user_info in self.users.values())
        return { "success": True, "data": exists }

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Retrieve the current account status of a user by their user_id.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # The user's current account status
            }
            or
            {
                "success": False,
                "error": str  # Error message if the user does not exist
            }

        Constraints:
            - The user_id must correspond to an existing user in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        account_status = user.get("account_status", None)
        return {"success": True, "data": account_status}

    def get_user_ratings(self, user_id: str) -> dict:
        """
        Retrieve all rating records for a user across chess variants.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[RatingInfo]  # List of all variant ratings for this user (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g. user does not exist
                    }
        Constraints:
            - The user_id must exist in users.
            - Returns an empty list in "data" if user has no ratings.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        ratings = list(self.ratings.get(user_id, {}).values())

        return { "success": True, "data": ratings }

    def get_user_rating_by_variant(self, user_id: str, variant: str) -> dict:
        """
        Retrieve a specific user's rating and rating-related statistics for a given chess variant.
    
        Args:
            user_id (str): The user's unique identifier.
            variant (str): Name of the chess variant (e.g., 'blitz', 'bullet').
        
        Returns:
            dict: {
                "success": True,
                "data": RatingInfo
            }
            or
            {
                "success": False,
                "error": str
            }
        
        Constraints:
            - The user must exist.
            - The rating entry for the specified (user_id, variant) must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        if user_id not in self.ratings or variant not in self.ratings[user_id]:
            return {"success": False, "error": "No rating found for specified variant."}
        rating_info = self.ratings[user_id][variant]
        return {"success": True, "data": rating_info}

    def get_user_statistics(self, user_id: str) -> dict:
        """
        Retrieve aggregated chess activity statistics for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserStatisticsInfo  # Dictionary containing aggregated statistics
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure ("User does not exist", "No statistics found for user")
                    }

        Constraints:
            - User must exist.
            - User must have statistics (should always be true if kept in sync).

        Edge cases:
            - If either user or statistics are missing, return proper error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if user_id not in self.user_statistics:
            return { "success": False, "error": "No statistics found for user" }
        stats = self.user_statistics[user_id]
        return { "success": True, "data": stats }

    def get_games_by_user(self, user_id: str) -> dict:
        """
        List all games played by a user, as either white or black participant.

        Args:
            user_id (str): The ID of the user whose games will be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[GameInfo],  # All games where user is white_user_id or black_user_id
            }
            OR
            {
                "success": False,
                "error": str  # Error message if user does not exist
            }

        Constraints:
            - user_id must reference a valid, existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        result = [
            game for game in self.games.values()
            if game["white_user_id"] == user_id or game["black_user_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_games_by_user_and_variant(self, user_id: str, variant: str) -> dict:
        """
        List all games played by a user in a specific chess variant.

        Args:
            user_id (str): The ID of the user (must exist in the system).
            variant (str): The chess variant to filter for (e.g., 'blitz').

        Returns:
            dict:
                "success": True,
                "data": List[GameInfo]  # All games involving this user and this variant (may be empty)
            or
                "success": False,
                "error": str  # Reason for failure (e.g., user not found)

        Constraints:
            - user_id must refer to an existing user.
            - Only games with this user as white or black, and with the specified variant, are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        result = []
        for game in self.games.values():
            if ((game['white_user_id'] == user_id or game['black_user_id'] == user_id)
                and game['variant'] == variant):
                result.append(game)

        return {"success": True, "data": result}

    def get_game_by_id(self, game_id: str) -> dict:
        """
        Retrieve the full record of a specific game by its game_id.

        Args:
            game_id (str): The unique identifier of the game to retrieve.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": GameInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Game with given game_id does not exist"
                    }
        """
        if game_id not in self.games:
            return { "success": False, "error": "Game with given game_id does not exist" }

        return { "success": True, "data": self.games[game_id] }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all user profiles in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # All users' profiles (empty list if no users).
            }

        Constraints:
            - No constraints relevant (simply reads all UserInfo in self.users).
            - Includes all users, regardless of their account_status.
        """
        all_users = list(self.users.values())
        return {
            "success": True,
            "data": all_users
        }

    def get_user_social_links(self, user_id: str) -> dict:
        """
        Retrieve all social link information for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, str],  # The user's social links, e.g., {"twitter": "handle"}
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "User not found"
            }

        Constraints:
            - The user_id must reference an existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        social_links = self.users[user_id].get("social_links", {})
        return { "success": True, "data": social_links }

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Retrieve a user's chess and account preferences.

        Args:
            user_id (str): The ID of the user whose preferences are to be fetched.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, str] # user preferences (possibly empty dict)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User with the given ID must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user.get("preferences", {}) }

    def update_user_profile(
        self,
        user_id: str,
        display_name: str = None,
        profile_bio: str = None,
        profile_avatar: str = None,
        country: str = None
    ) -> dict:
        """
        Modify a user’s profile information (display name, bio, avatar, country, etc.).

        Args:
            user_id (str): ID of the user to update.
            display_name (str, optional): New display name.
            profile_bio (str, optional): New profile biography.
            profile_avatar (str, optional): New profile avatar URL.
            country (str, optional): New country string.

        Returns:
            dict: {
                "success": True,
                "message": "Updated profile for user <username>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only existing users may be updated.
            - Does NOT update username or account status.
            - Updates only accepted for 'active' accounts.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        if user.get("account_status") != "active":
            return { "success": False, "error": "Profile updates allowed only for active accounts" }

        changes = []
        if display_name is not None and display_name != user.get("display_name"):
            user["display_name"] = display_name
            changes.append("display_name")
        if profile_bio is not None and profile_bio != user.get("profile_bio"):
            user["profile_bio"] = profile_bio
            changes.append("profile_bio")
        if profile_avatar is not None and profile_avatar != user.get("profile_avatar"):
            user["profile_avatar"] = profile_avatar
            changes.append("profile_avatar")
        if country is not None and country != user.get("country"):
            user["country"] = country
            changes.append("country")

        if not changes:
            return { "success": True, "message": f"No profile fields were changed for user {user.get('username')}" }

        self.users[user_id] = user
        return { "success": True, "message": f"Updated profile fields {changes} for user {user.get('username')}" }

    def change_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Update the account_status of a user (e.g., to active, banned, or closed).

        Args:
            user_id (str): The unique identifier of the user to be updated.
            new_status (str): The new account status to be set.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Account status updated to <new_status> for user <user_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
              
        Constraints:
            - User must exist.
            - Optionally, account_status should be one of allowed values ('active', 'banned', 'closed').
            - The change must be reflected in self.users.
        """
        allowed_statuses = {"active", "banned", "closed"}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid account status '{new_status}'"}

        self.users[user_id]["account_status"] = new_status

        return {
            "success": True,
            "message": f"Account status updated to {new_status} for user {user_id}"
        }

    def add_or_update_user_rating(
        self,
        user_id: str,
        variant: str,
        rating: float,
        rating_deviation: float,
        games_played_in_variant: int
    ) -> dict:
        """
        Add a new rating entry for a (user, variant) pair, or update the rating if it already exists.

        Args:
            user_id (str): The unique ID of the user.
            variant (str): The chess variant (e.g., 'blitz', 'bullet').
            rating (float): The user's rating for this variant.
            rating_deviation (float): The rating deviation (uncertainty).
            games_played_in_variant (int): Number of games played in this variant.

        Returns:
            dict: {
                "success": True,
                "message": "Rating added/updated for user and variant"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }
    
        Constraints:
            - user_id must exist in self.users
            - Each (user_id, variant) combination is unique in self.ratings
        """
        # Validate user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not variant or not isinstance(variant, str):
            return { "success": False, "error": "Variant must be a non-empty string" }
        if games_played_in_variant < 0:
            return { "success": False, "error": "games_played_in_variant must be non-negative" }

        if user_id not in self.ratings:
            self.ratings[user_id] = {}

        rating_entry = {
            "_id": user_id,
            "variant": variant,
            "rating": rating,
            "rating_deviation": rating_deviation,
            "games_played_in_variant": games_played_in_variant
        }

        self.ratings[user_id][variant] = rating_entry

        return {
            "success": True,
            "message": f"Rating added/updated for user '{user_id}' and variant '{variant}'"
        }

    def add_game_record(
        self,
        game_id: str,
        white_user_id: str,
        black_user_id: str,
        variant: str,
        result: str,
        moves: list,
        start_time: str,
        end_time: str,
        event_type: str,
        is_rated: bool
    ) -> dict:
        """
        Add a new chess game to the system, verifying users exist and updating ratings and statistics.

        Args:
            game_id (str): Unique identifier for the new game.
            white_user_id (str): User ID for white pieces.
            black_user_id (str): User ID for black pieces.
            variant (str): The variant of chess played.
            result (str): Result of the game ("1-0", "0-1", "1/2-1/2", etc).
            moves (list): List of moves made in the game.
            start_time (str): Game start time.
            end_time (str): Game end time.
            event_type (str): Type of chess event (tournament, casual, etc.).
            is_rated (bool): Whether the game affects ratings.

        Returns:
            dict: {"success": True, "message": str} or {"success": False, "error": str}

        Constraints:
            - Games must reference valid/existing users as participants.
            - Game ID must be unique.
            - UserStatistics must be kept in sync as new games are added.
            - Ratings are managed per-user and per-variant.
        """
        # Check for unique game_id
        if game_id in self.games:
            return {"success": False, "error": "Game ID already exists"}

        # Check users exist
        if white_user_id not in self.users:
            return {"success": False, "error": "White user does not exist"}
        if black_user_id not in self.users:
            return {"success": False, "error": "Black user does not exist"}

        # Add the game record
        game_record: GameInfo = {
            "game_id": game_id,
            "white_user_id": white_user_id,
            "black_user_id": black_user_id,
            "variant": variant,
            "result": result,
            "moves": moves,
            "start_time": start_time,
            "end_time": end_time,
            "event_type": event_type,
            "is_rated": is_rated
        }
        self.games[game_id] = game_record

        # If is_rated, ensure both users have RatingInfo for this variant, create if not exist
        if is_rated:
            for user_id in [white_user_id, black_user_id]:
                if user_id not in self.ratings:
                    self.ratings[user_id] = {}
                if variant not in self.ratings[user_id]:
                    self.ratings[user_id][variant] = {
                        "_id": user_id,
                        "variant": variant,
                        "rating": 1500.0,
                        "rating_deviation": 350.0,
                        "games_played_in_variant": 0
                    }
                # Increment games played count
                self.ratings[user_id][variant]["games_played_in_variant"] += 1
                # NOTE: Proper rating change not implemented here

        # Update user statistics for both users (ensure UserStatistics entry exists)
        for user_id, color in [(white_user_id, "white"), (black_user_id, "black")]:
            stats = self.user_statistics.get(user_id)
            if not stats:
                # Default statistics (first game)
                stats = {
                    "_id": user_id,
                    "total_games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "win_rate": 0.0,
                    "longest_streak": 0,
                    "current_streak": 0,
                    "average_opponent_rating": 0.0,
                    "most_played_variant": variant
                }
                self.user_statistics[user_id] = stats

            stats["total_games"] += 1

            # Determine win/draw/loss for this user
            # Assume result format is "1-0" -> white wins, "0-1" -> black wins, "1/2-1/2" -> draw
            outcome = None
            if result == "1-0":
                winner = "white"
            elif result == "0-1":
                winner = "black"
            elif result in ["1/2-1/2", "0.5-0.5", "draw"]:
                winner = "draw"
            else:
                winner = None  # unknown, don't update WDL

            if winner == color:
                stats["wins"] += 1
                stats["current_streak"] = stats.get("current_streak", 0) + 1
                stats["longest_streak"] = max(stats["longest_streak"], stats["current_streak"])
            elif winner == "draw":
                stats["draws"] += 1
                stats["current_streak"] = 0
            elif winner is not None:
                stats["losses"] += 1
                stats["current_streak"] = 0

            # Re-calculate win_rate
            if stats["total_games"] > 0:
                stats["win_rate"] = stats["wins"] / stats["total_games"]

            # Update most_played_variant (simple logic: override or count separately in a real system)
            stats["most_played_variant"] = variant

            # Update average_opponent_rating if rating info exists
            opponent_id = black_user_id if user_id == white_user_id else white_user_id
            # Try to get opponent's rating for this variant
            opp_rating = self.ratings.get(opponent_id, {}).get(variant, {}).get("rating")
            if opp_rating is not None:
                prev_avg = stats["average_opponent_rating"]
                n = stats["total_games"]
                stats["average_opponent_rating"] = (prev_avg * (n - 1) + opp_rating) / n

        return {"success": True, "message": f"Game record {game_id} added, stats updated for users."}

    def update_user_statistics(self, user_id: str) -> dict:
        """
        Refresh or correct statistics for a specific user after game results.

        Args:
            user_id (str): The unique identifier for the user whose stats are to be updated.

        Returns:
            dict:
                success (bool): True if stats updated, False if error.
                message (str): Success message if successful.
                error (str): Error description if unsuccessful.

        Constraints:
            - User must exist.
            - UserStatistics entry will be created/updated.
            - Stats calculated from all games in self.games where user participated.
        """

        if user_id not in self.users:
            return {"success": False, "error": f"User '{user_id}' does not exist."}

        # Fetch all games involving user
        user_games = [
            game for game in self.games.values()
            if game["white_user_id"] == user_id or game["black_user_id"] == user_id
        ]

        total_games = len(user_games)
        wins = draws = losses = 0
        win_rate = 0.0
        streak = 0
        longest_streak = 0
        current_streak = 0
        prev_result = None
        opponent_ratings = []
        variant_counts = {}

        for game in sorted(user_games, key=lambda g: g["end_time"]):
            result = None  # win/draw/loss from this user's perspective
            if game["result"] == "1-0":
                if game["white_user_id"] == user_id:
                    result = 'win'
                else:
                    result = 'loss'
            elif game["result"] == "0-1":
                if game["black_user_id"] == user_id:
                    result = 'win'
                else:
                    result = 'loss'
            elif game["result"] == "1/2-1/2":
                result = 'draw'
            else:
                result = 'draw'  # Unknown/unexpected, be conservative

            # Win/loss/draw stats
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1
            else:
                draws += 1

            # Streak calculation (current and longest)--only over wins
            if result == 'win':
                if prev_result == 'win':
                    streak += 1
                else:
                    streak = 1
                if streak > longest_streak:
                    longest_streak = streak
                prev_result = 'win'
            else:
                streak = 0
                prev_result = result

            # For current_streak, count consecutive latest results starting from last game
            # Do separate pass after loop

            # Opponent rating collection
            if game["white_user_id"] == user_id:
                opp_id = game["black_user_id"]
            else:
                opp_id = game["white_user_id"]
            # Try to get opponent's preferred rating (e.g., in this variant)
            variant = game["variant"]
            if opp_id in self.ratings and variant in self.ratings[opp_id]:
                opponent_ratings.append(self.ratings[opp_id][variant]["rating"])
            # Variant played
            variant_counts[variant] = variant_counts.get(variant, 0) + 1

        # Calculate current streak (from most recent game)
        current_streak = 0
        for game in sorted(user_games, key=lambda g: g["end_time"], reverse=True):
            if game["result"] == "1-0":
                usr_win = (game["white_user_id"] == user_id)
            elif game["result"] == "0-1":
                usr_win = (game["black_user_id"] == user_id)
            elif game["result"] == "1/2-1/2":
                usr_win = None  # Draw
            else:
                usr_win = None

            if usr_win is True:
                current_streak += 1
            else:
                break

        average_opponent_rating = (
            sum(opponent_ratings) / len(opponent_ratings)
            if opponent_ratings else 0.0
        )
        most_played_variant = (
            max(variant_counts.items(), key=lambda item: item[1])[0]
            if variant_counts else ""
        )

        win_rate = (wins / total_games) if total_games > 0 else 0.0

        stats: UserStatisticsInfo = {
            "_id": user_id,
            "total_games": total_games,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_rate": win_rate,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "average_opponent_rating": average_opponent_rating,
            "most_played_variant": most_played_variant,
        }
        self.user_statistics[user_id] = stats

        return {
            "success": True,
            "message": f"Statistics updated for user {user_id}"
        }

    def add_user_profile_social_link(self, user_id: str, platform: str, link: str) -> dict:
        """
        Add or update a link to a user's social profile.

        Args:
            user_id (str): The unique ID of the user.
            platform (str): Social media/network platform name (e.g., 'twitter').
            link (str): The URL or handle for the user's profile on that platform.

        Returns:
            dict: {
                "success": True,
                "message": "Social link for <platform> added/updated for user <username>."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - user_id must exist in the system.
            - platform and link cannot be empty.
            - User account_status cannot be 'banned' or 'closed'.
        """
        # User existence check
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        # Platform/link validation
        if not isinstance(platform, str) or not platform.strip():
            return {"success": False, "error": "Platform name cannot be empty."}
        if not isinstance(link, str) or not link.strip():
            return {"success": False, "error": "Social link cannot be empty."}
        # Account status check
        if user.get("account_status", "").lower() in ("banned", "closed"):
            return {"success": False, "error": "User account status does not permit profile modification."}
        # Add/update social link
        if "social_links" not in user or user["social_links"] is None:
            user["social_links"] = {}
        user["social_links"][platform] = link
        # Update back (if data model does not use ref)
        self.users[user_id] = user
        uname = user.get("username", user_id)
        return {"success": True, "message": f"Social link for {platform} added/updated for user {uname}."}

    def update_user_preferences(self, user_id: str, preferences_update: Dict[str, str]) -> dict:
        """
        Update or personalize user preferences/settings.

        Args:
            user_id (str): The unique id of the user whose preferences will be updated.
            preferences_update (Dict[str, str]): Dictionary of preference keys and their new values to update for the user.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "User preferences updated"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The user must exist.
            - User must have 'active' account_status to update preferences.
            - Only updates/merges the provided keys; unmentioned keys remain unchanged.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User does not exist"}

        if user_info.get("account_status") != "active":
            return {"success": False, "error": "User account is not active; preferences cannot be updated"}

        # Merge/Update preferences
        if not isinstance(user_info["preferences"], dict):
            user_info["preferences"] = {}
        user_info["preferences"].update(preferences_update)

        # Save back (dict is mutable, but for clarity)
        self.users[user_id] = user_info

        return {"success": True, "message": "User preferences updated"}


class LichessUserAccountManagementSystem(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_username_exists(self, **kwargs):
        return self._call_inner_tool('check_username_exists', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def get_user_ratings(self, **kwargs):
        return self._call_inner_tool('get_user_ratings', kwargs)

    def get_user_rating_by_variant(self, **kwargs):
        return self._call_inner_tool('get_user_rating_by_variant', kwargs)

    def get_user_statistics(self, **kwargs):
        return self._call_inner_tool('get_user_statistics', kwargs)

    def get_games_by_user(self, **kwargs):
        return self._call_inner_tool('get_games_by_user', kwargs)

    def get_games_by_user_and_variant(self, **kwargs):
        return self._call_inner_tool('get_games_by_user_and_variant', kwargs)

    def get_game_by_id(self, **kwargs):
        return self._call_inner_tool('get_game_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_user_social_links(self, **kwargs):
        return self._call_inner_tool('get_user_social_links', kwargs)

    def get_user_preferences(self, **kwargs):
        return self._call_inner_tool('get_user_preferences', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def change_user_account_status(self, **kwargs):
        return self._call_inner_tool('change_user_account_status', kwargs)

    def add_or_update_user_rating(self, **kwargs):
        return self._call_inner_tool('add_or_update_user_rating', kwargs)

    def add_game_record(self, **kwargs):
        return self._call_inner_tool('add_game_record', kwargs)

    def update_user_statistics(self, **kwargs):
        return self._call_inner_tool('update_user_statistics', kwargs)

    def add_user_profile_social_link(self, **kwargs):
        return self._call_inner_tool('add_user_profile_social_link', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)
