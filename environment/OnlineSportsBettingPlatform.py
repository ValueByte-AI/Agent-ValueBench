# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# Match entity from: match_id, sport_type, start_time, participant_ids, sta
class MatchInfo(TypedDict):
    match_id: str
    sport_type: str
    start_time: str
    participant_ids: List[str]
    status: str  # live status (extracted from 'sta')

# Participant entity from: participant_id, name, type (team/player), country
class ParticipantInfo(TypedDict):
    participant_id: str
    name: str
    type: str  # "team" or "player"
    country: str

# Market entity from: market_id, match_id, market_type (e.g. winner, score), bookmaker_id, odd
class MarketInfo(TypedDict):
    market_id: str
    match_id: str
    market_type: str
    bookmaker_id: str
    odds: float  # 'odd' mapped to 'odds'

# Bookmaker entity from: bookmaker_id, name
class BookmakerInfo(TypedDict):
    bookmaker_id: str
    name: str

# Bet entity from: bet_id, user_id, match_id, market_id, odds, amount, timestamp
class BetInfo(TypedDict):
    bet_id: str
    user_id: str
    match_id: str
    market_id: str
    odds: float
    amount: float
    timestamp: str

# User entity from: user_id, name
class UserInfo(TypedDict):
    user_id: str
    name: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Matches: {match_id: MatchInfo}
        self.matches: Dict[str, MatchInfo] = {}

        # Participants: {participant_id: ParticipantInfo}
        self.participants: Dict[str, ParticipantInfo] = {}

        # Markets: {market_id: MarketInfo}
        self.markets: Dict[str, MarketInfo] = {}

        # Bookmakers: {bookmaker_id: BookmakerInfo}
        self.bookmakers: Dict[str, BookmakerInfo] = {}

        # Bets: {bet_id: BetInfo}
        self.bets: Dict[str, BetInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Odds can only be retrieved for matches where status is "ongoing" or "upcoming".
        # - Markets and odds are bookmaker-specific; users must specify the bookmaker (e.g. Bildbet).
        # - Bets can only be placed if the match has not started or is within live-betting periods, depending on market type.

    def get_bookmaker_by_name(self, name: str) -> dict:
        """
        Retrieve a bookmaker's information using its name.

        Args:
            name (str): The name of the bookmaker to find (e.g., "Bildbet").

        Returns:
            dict:
              - On success: {"success": True, "data": BookmakerInfo}
              - On failure: {"success": False, "error": "Bookmaker not found"}

        Constraints:
            - Match must be exact (case-sensitive).
        """
        for bookmaker in self.bookmakers.values():
            if bookmaker['name'] == name:
                return {"success": True, "data": bookmaker}
        return {"success": False, "error": "Bookmaker not found"}

    def list_matches(self) -> dict:
        """
        Retrieve information on all matches stored in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo]  # List of all matches (may be empty if no matches exist)
            }
        """
        return {
            "success": True,
            "data": list(self.matches.values())
        }

    def list_matches_by_status(self, status: str) -> dict:
        """
        Retrieve all matches filtered by their live status (e.g. 'ongoing', 'upcoming').

        Args:
            status (str): The status to filter matches by. Example: "ongoing", "upcoming", "finished", etc.

        Returns:
            dict: {
                "success": True,
                "data": List[MatchInfo],  # List of MatchInfo dicts with the given status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error explanation (e.g., missing parameter)
            }

        Notes:
            - Returns empty list if no matches are found with the given status.
            - No special permissions required.
        """
        if not isinstance(status, str) or not status:
            return { "success": False, "error": "A valid status string must be provided" }

        matches = [match for match in self.matches.values() if match.get('status') == status]
        return { "success": True, "data": matches }

    def get_match_by_id(self, match_id: str) -> dict:
        """
        Return all information about a given match.

        Args:
            match_id (str): The unique identifier of the match to look up.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": MatchInfo
                }
                On failure:
                {
                    "success": False,
                    "error": "Match not found"
                }

        Constraints:
            - The match_id must exist in the system. No restrictions on status or other properties.
        """
        match_info = self.matches.get(match_id)
        if match_info is None:
            return { "success": False, "error": "Match not found" }
        return { "success": True, "data": match_info }

    def list_markets_by_bookmaker(self, bookmaker_id: str) -> dict:
        """
        Retrieve all market entries being offered by a specific bookmaker.

        Args:
            bookmaker_id (str): The unique ID of the bookmaker.

        Returns:
            dict:
                - If the bookmaker exists:
                    {
                        "success": True,
                        "data": List[MarketInfo]  # All MarketInfo entries with the given bookmaker_id
                    }
                - If the bookmaker does not exist:
                    {
                        "success": False,
                        "error": "Bookmaker does not exist"
                    }

        Constraints:
            - bookmaker_id must exist in the platform.
        """
        if bookmaker_id not in self.bookmakers:
            return {"success": False, "error": "Bookmaker does not exist"}

        markets = [
            market for market in self.markets.values()
            if market['bookmaker_id'] == bookmaker_id
        ]
        return {"success": True, "data": markets}

    def list_markets_for_match(self, match_id: str) -> dict:
        """
        Retrieve all markets associated with a given match.

        Args:
            match_id (str): Unique identifier of the match.

        Returns:
            dict:
                If success:
                    {
                        "success": True,
                        "data": List[MarketInfo]  # List of associated markets, may be empty
                    }
                If failure (e.g., match does not exist):
                    {
                        "success": False,
                        "error": "Match does not exist"
                    }
        Constraints:
            - match_id must exist in self.matches
        """
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist" }

        result = [
            market for market in self.markets.values()
            if market["match_id"] == match_id
        ]

        return { "success": True, "data": result }

    def get_market_by_id(self, market_id: str) -> dict:
        """
        Retrieve detailed information for a specific betting market.

        Args:
            market_id (str): The unique identifier of the market.

        Returns:
            dict: 
                - On success: {"success": True, "data": MarketInfo}
                - On failure: {"success": False, "error": "Market not found"}

        Constraints:
            - The market must exist.
        """
        market = self.markets.get(market_id)
        if market is None:
            return { "success": False, "error": "Market not found" }
        return { "success": True, "data": market }

    def get_odds_for_market(self, market_id: str) -> dict:
        """
        Return the current odds for the specified market, only if its associated match is "ongoing" or "upcoming".

        Args:
            market_id (str): The ID of the market.

        Returns:
            dict: 
             - On success: { "success": True, "data": { "odds": float } }
             - On failure: { "success": False, "error": <error_reason> }

        Constraints:
            - Market must exist.
            - Associated match must exist.
            - Match status must be "ongoing" or "upcoming".
        """
        market = self.markets.get(market_id)
        if not market:
            return { "success": False, "error": "Market does not exist." }

        match_id = market["match_id"]
        match = self.matches.get(match_id)
        if not match:
            return { "success": False, "error": "Associated match does not exist." }

        if match["status"] not in ("ongoing", "upcoming"):
            return { "success": False, "error": "Odds can only be retrieved for matches with status 'ongoing' or 'upcoming'." }

        return { "success": True, "data": { "odds": market["odds"] } }

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve details (name, type, country) for a participant (team/player) given their participant_id.

        Args:
            participant_id (str): The unique ID of the participant.

        Returns:
            dict: {
                "success": True,
                "data": ParticipantInfo  # Contains participant_id, name, type, country
            }
            or
            {
                "success": False,
                "error": str  # Description such as "Participant not found"
            }

        Constraints:
            - The participant_id must exist in the platform.
        """
        participant = self.participants.get(participant_id)
        if participant is None:
            return {"success": False, "error": "Participant not found"}
        return {"success": True, "data": participant}

    def list_participants_for_match(self, match_id: str) -> dict:
        """
        Get details for all participants in a specific match.

        Args:
            match_id (str): Unique identifier of the match.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ParticipantInfo]  # Participants found in self.participants
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., match not found)
                }

        Constraints:
            - The provided match_id must exist in the system.
            - Missing participant_ids (not present in self.participants) are ignored.
        """
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Match not found"}

        result = [
            self.participants[pid]
            for pid in match.get("participant_ids", [])
            if pid in self.participants
        ]

        return {"success": True, "data": result}

    def list_users(self) -> dict:
        """
        List all user accounts in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all user info records (may be empty)
            }
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve info for a particular user by user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": UserInfo  # User information dict
                }
                or
                {
                    "success": False,
                    "error": str  # Error description if user_id not found
                }

        Constraints:
            - user_id must exist in the platform.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User ID not found" }
        return { "success": True, "data": user }

    def list_bets_by_user(self, user_id: str) -> dict:
        """
        Retrieve all bets placed by a specific user.

        Args:
            user_id (str): The ID of the user whose bets are to be listed.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[BetInfo],  # List of bets placed by the user (may be empty)
                }
                OR
                {
                    "success": False,
                    "error": str  # Error description if user does not exist
                }

        Constraints:
            - The user must exist in the platform.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_bets = [
            bet for bet in self.bets.values()
            if bet["user_id"] == user_id
        ]
        return { "success": True, "data": user_bets }

    def list_bets_for_match(self, match_id: str) -> dict:
        """
        Retrieve all bets placed on the specified match.

        Args:
            match_id (str): The unique identifier of the match.

        Returns:
            dict: {
                "success": True,
                "data": List[BetInfo],  # List of bets placed on the match (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - The given match_id must exist in the platform.
        """
        if match_id not in self.matches:
            return {"success": False, "error": "Match does not exist."}

        bets = [
            bet for bet in self.bets.values()
            if bet['match_id'] == match_id
        ]
        return {"success": True, "data": bets}

    def place_bet(
        self,
        user_id: str,
        market_id: str,
        odds: float,
        amount: float,
        timestamp: str
    ) -> dict:
        """
        Record a new bet for a user on a specific market with the chosen odds and wager amount.

        Args:
            user_id (str): The ID of the user placing the bet.
            market_id (str): The ID of the market to bet on.
            odds (float): The odds to lock in for the bet (must match market odds).
            amount (float): The wager amount (must be positive).
            timestamp (str): The time the bet is placed.

        Returns:
            dict: Success or failure with reason. On success: {"success": True, "message": ..., "bet_id": ...}
                  On error: {"success": False, "error": ...}

        Constraints:
            - user_id and market_id must exist.
            - market's associated match must be "upcoming" or "ongoing".
            - odds must match current market odds.
            - amount must be positive.
            - unique bet_id generated for the bet.
        """
        # 1. Validate user
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # 2. Validate market
        market = self.markets.get(market_id)
        if not market:
            return {"success": False, "error": "Market does not exist."}

        # 3. Validate market's match
        match_id = market["match_id"]
        match = self.matches.get(match_id)
        if not match:
            return {"success": False, "error": "Associated match does not exist."}

        # 4. Validate match status for bet placement
        status = match.get("status", "").lower()
        if status not in ("upcoming", "ongoing"):
            return {"success": False, "error": "Bets can only be placed on upcoming or ongoing matches."}

        # 5. Odds must match current odds for this market
        if market["odds"] != odds:
            return {"success": False, "error": "Provided odds do not match current market odds."}

        # 6. Amount must be positive
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {"success": False, "error": "Wager amount must be positive."}

        # 7. Generate unique bet_id (simple auto-increment based on length)
        # For robustness, check for collisions and increment if needed (simple integer suffix)
        base_id = f"bet_{len(self.bets) + 1}"
        bet_id = base_id
        suffix = 1
        while bet_id in self.bets:
            bet_id = f"{base_id}_{suffix}"
            suffix += 1

        # 8. Record the bet
        new_bet = {
            "bet_id": bet_id,
            "user_id": user_id,
            "match_id": match_id,
            "market_id": market_id,
            "odds": odds,
            "amount": amount,
            "timestamp": timestamp
        }
        self.bets[bet_id] = new_bet

        return {
            "success": True,
            "message": "Bet placed successfully.",
            "bet_id": bet_id
        }

    def cancel_bet(self, bet_id: str) -> dict:
        """
        Cancel/void an existing bet if rules allow (e.g., before match starts or during live-betting).

        Args:
            bet_id (str): The Bet ID to cancel.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Bet <bet_id> canceled successfully." }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Bet must exist.
            - The match associated with the bet must not have started (status == "upcoming"),
              OR if the market type is "live", the match status must be "ongoing".
            - Otherwise, cannot cancel.
        """
        bet_info = self.bets.get(bet_id)
        if bet_info is None:
            return { "success": False, "error": "Bet does not exist." }
    
        match_id = bet_info["match_id"]
        market_id = bet_info["market_id"]
        match_info = self.matches.get(match_id)
        if match_info is None:
            return { "success": False, "error": "Associated match does not exist." }
        market_info = self.markets.get(market_id)
        if market_info is None:
            return { "success": False, "error": "Associated market does not exist." }

        match_status = match_info.get("status", "")
        market_type = market_info.get("market_type", "").lower()

        # Check cancellation rules
        if match_status == "upcoming":
            # Always allow cancellation before match starts
            self.bets.pop(bet_id)
            return { "success": True, "message": f"Bet {bet_id} canceled successfully." }
        elif market_type == "live" and match_status == "ongoing":
            # Allow cancellation during live for live markets
            self.bets.pop(bet_id)
            return { "success": True, "message": f"Bet {bet_id} canceled successfully during live event." }
        else:
            return { "success": False, 
                     "error": "Bet cannot be canceled after match has started unless market type is live and match is ongoing." }

    def update_odds_for_market(self, market_id: str, bookmaker_id: str, new_odds: float) -> dict:
        """
        Update the offered odds for a specific market; this is a bookmaker-level operation.

        Args:
            market_id (str): The unique identifier for the market to update.
            bookmaker_id (str): The unique identifier of the bookmaker (must match the market's bookmaker).
            new_odds (float): The new odds value (must be > 0).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Updated odds for market <market_id> (bookmaker <bookmaker_id>)"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<description>"
                    }

        Constraints:
            - The market must exist.
            - The bookmaker must exist.
            - The specified market must be associated with the specified bookmaker.
            - The new odds must be a positive float.
        """
        # Validate market_id
        market = self.markets.get(market_id)
        if market is None:
            return {"success": False, "error": f"Market with id '{market_id}' does not exist"}

        # Validate bookmaker_id exists
        if bookmaker_id not in self.bookmakers:
            return {"success": False, "error": f"Bookmaker with id '{bookmaker_id}' does not exist"}

        # Validate market is associated with bookmaker
        if market["bookmaker_id"] != bookmaker_id:
            return {"success": False, "error": f"Market '{market_id}' is not associated with bookmaker '{bookmaker_id}'"}

        # Validate odds
        if not isinstance(new_odds, (int, float)) or new_odds <= 0:
            return {"success": False, "error": "New odds must be a positive number"}

        # Update
        market["odds"] = new_odds
        self.markets[market_id] = market

        return {
            "success": True,
            "message": f"Updated odds for market {market_id} (bookmaker {bookmaker_id})"
        }

    def add_market(
        self,
        market_id: str,
        match_id: str,
        market_type: str,
        bookmaker_id: str,
        odds: float
    ) -> dict:
        """
        Add a new betting market to a match for a given bookmaker.

        Args:
            market_id (str): Unique identifier for the market (must not already exist).
            match_id (str): The match that the market is for (must exist).
            market_type (str): Type of betting market (e.g., winner, score).
            bookmaker_id (str): Bookmaker providing this market (must exist).
            odds (float): Odds for this market.

        Returns:
            dict: {
                "success": True,
                "message": "Market added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - market_id must be unique
            - match_id must exist
            - bookmaker_id must exist
        """
        if market_id in self.markets:
            return { "success": False, "error": "Market ID already exists." }
        if match_id not in self.matches:
            return { "success": False, "error": "Match does not exist." }
        if bookmaker_id not in self.bookmakers:
            return { "success": False, "error": "Bookmaker does not exist." }
        # Add the market
        self.markets[market_id] = {
            "market_id": market_id,
            "match_id": match_id,
            "market_type": market_type,
            "bookmaker_id": bookmaker_id,
            "odds": odds
        }
        return { "success": True, "message": "Market added successfully." }

    def update_match_status(self, match_id: str, new_status: str) -> dict:
        """
        Change the status (e.g., from "upcoming" to "ongoing"/"finished") for a match.
        This is typically an admin or system operation.

        Args:
            match_id (str): The ID of the match to update.
            new_status (str): Target status ("upcoming", "ongoing", "finished", ...).

        Returns:
            dict: 
                On success: { "success": True, "message": "Match status updated to <new_status>." }
                On error: { "success": False, "error": "<reason>" }

        Constraints:
            - match_id must refer to an existing match.
            - new_status should be a valid status value (allowed: "upcoming", "ongoing", "finished").
        """

        allowed_statuses = {"upcoming", "ongoing", "finished"}

        if match_id not in self.matches:
            return {"success": False, "error": "Match not found."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status value '{new_status}'."}

        current_status = self.matches[match_id].get("status")
        if current_status == new_status:
            return {"success": True, "message": f"Status already set to '{new_status}'."}

        self.matches[match_id]["status"] = new_status

        return {"success": True, "message": f"Match status updated to '{new_status}'."}

    def add_match(
        self,
        match_id: str,
        sport_type: str,
        start_time: str,
        participant_ids: list,
        status: str
    ) -> dict:
        """
        Register a new sporting match in the system.

        Args:
            match_id (str): Unique identifier for the match (must not already exist).
            sport_type (str): Type of sport (e.g., "soccer").
            start_time (str): Scheduled start time.
            participant_ids (list of str): List of participant IDs (must all exist).
            status (str): Match status (e.g., "upcoming", "ongoing").

        Returns:
            dict: On success: { "success": True, "message": "Match added successfully." }
                  On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - match_id must be unique.
            - All participant_ids must exist.
            - Required parameters must be provided with correct types.
        """
        # Validate uniqueness
        if match_id in self.matches:
            return { "success": False, "error": "Match ID already exists." }

        # Validate participant_ids
        if not isinstance(participant_ids, list) or len(participant_ids) == 0:
            return { "success": False, "error": "participant_ids must be a non-empty list of strings." }
        for pid in participant_ids:
            if pid not in self.participants:
                return { "success": False, "error": f"Participant ID '{pid}' does not exist." }

        # Basic argument validation
        if not all(isinstance(arg, str) for arg in [match_id, sport_type, start_time, status]):
            return { "success": False, "error": "Invalid arguments: all arguments except participant_ids must be strings." }

        # Register match
        self.matches[match_id] = {
            "match_id": match_id,
            "sport_type": sport_type,
            "start_time": start_time,
            "participant_ids": participant_ids,
            "status": status,
        }

        return { "success": True, "message": "Match added successfully." }

    def add_bookmaker(self, bookmaker_id: str, name: str) -> dict:
        """
        Register a new bookmaker in the system.

        Args:
            bookmaker_id (str): Unique identifier for the bookmaker.
            name (str): Human-readable name for the bookmaker.

        Returns:
            dict:
                On success: { "success": True, "message": "Bookmaker added successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - bookmaker_id must be unique (not already in the system).
            - name must be unique (case-insensitive, not used by another bookmaker).
            - bookmaker_id and name must not be empty.
        """
        # Basic validation
        if not bookmaker_id or not name:
            return { "success": False, "error": "bookmaker_id and name must be provided and non-empty." }
    
        # Check for unique bookmaker_id
        if bookmaker_id in self.bookmakers:
            return { "success": False, "error": "Bookmaker ID already exists." }
    
        # Check for unique name (case-insensitive)
        for bm in self.bookmakers.values():
            if bm["name"].strip().lower() == name.strip().lower():
                return { "success": False, "error": "Bookmaker name already exists." }
    
        # Add bookmaker
        self.bookmakers[bookmaker_id] = {
            "bookmaker_id": bookmaker_id,
            "name": name.strip(),
        }
        return { "success": True, "message": "Bookmaker added successfully." }

    def add_participant(
        self, participant_id: str, name: str, type: str, country: str
    ) -> dict:
        """
        Adds a new participant (team or player) to the platform.

        Args:
            participant_id (str): Unique identifier for the participant.
            name (str): Name of the participant.
            type (str): Type of the participant ("team" or "player").
            country (str): Country of the participant.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - message (str): Success message (if success).
                - error (str): Error message (if not successful).

        Constraints:
            - participant_id must be unique (not already used).
            - type must be either "team" or "player".
            - All arguments must be non-empty strings.
        """
        if not participant_id or not name or not type or not country:
            return {"success": False, "error": "All participant fields must be provided and non-empty."}

        if participant_id in self.participants:
            return {"success": False, "error": "Participant ID already exists."}

        if type not in ("team", "player"):
            return {"success": False, "error": "Participant type must be 'team' or 'player'."}

        participant_info = {
            "participant_id": participant_id,
            "name": name,
            "type": type,
            "country": country,
        }
        self.participants[participant_id] = participant_info
        return {"success": True, "message": "Participant added successfully."}

    def add_user(self, user_id: str, name: str) -> dict:
        """
        Add a new user to the platform.

        Args:
            user_id (str): The unique identifier for the user.
            name (str): The display name of the user.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "User added successfully."
                }
                or
                {
                    "success": False,
                    "error": "reason for failure"
                }
        Constraints:
            - user_id must be unique (not already present in self.users).
            - Both user_id and name must be non-empty strings.
        """
        if not isinstance(user_id, str) or not user_id.strip():
            return {"success": False, "error": "Missing or invalid user_id"}
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Missing or invalid user name"}
        if user_id in self.users:
            return {"success": False, "error": "User ID already exists"}

        user_info = {
            "user_id": user_id,
            "name": name
        }
        self.users[user_id] = user_info
        return {"success": True, "message": "User added successfully."}


class OnlineSportsBettingPlatform(BaseEnv):
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

    def list_matches(self, **kwargs):
        return self._call_inner_tool('list_matches', kwargs)

    def list_matches_by_status(self, **kwargs):
        return self._call_inner_tool('list_matches_by_status', kwargs)

    def get_match_by_id(self, **kwargs):
        return self._call_inner_tool('get_match_by_id', kwargs)

    def list_markets_by_bookmaker(self, **kwargs):
        return self._call_inner_tool('list_markets_by_bookmaker', kwargs)

    def list_markets_for_match(self, **kwargs):
        return self._call_inner_tool('list_markets_for_match', kwargs)

    def get_market_by_id(self, **kwargs):
        return self._call_inner_tool('get_market_by_id', kwargs)

    def get_odds_for_market(self, **kwargs):
        return self._call_inner_tool('get_odds_for_market', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def list_participants_for_match(self, **kwargs):
        return self._call_inner_tool('list_participants_for_match', kwargs)

    def list_users(self, **kwargs):
        return self._call_inner_tool('list_users', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_bets_by_user(self, **kwargs):
        return self._call_inner_tool('list_bets_by_user', kwargs)

    def list_bets_for_match(self, **kwargs):
        return self._call_inner_tool('list_bets_for_match', kwargs)

    def place_bet(self, **kwargs):
        return self._call_inner_tool('place_bet', kwargs)

    def cancel_bet(self, **kwargs):
        return self._call_inner_tool('cancel_bet', kwargs)

    def update_odds_for_market(self, **kwargs):
        return self._call_inner_tool('update_odds_for_market', kwargs)

    def add_market(self, **kwargs):
        return self._call_inner_tool('add_market', kwargs)

    def update_match_status(self, **kwargs):
        return self._call_inner_tool('update_match_status', kwargs)

    def add_match(self, **kwargs):
        return self._call_inner_tool('add_match', kwargs)

    def add_bookmaker(self, **kwargs):
        return self._call_inner_tool('add_bookmaker', kwargs)

    def add_participant(self, **kwargs):
        return self._call_inner_tool('add_participant', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

