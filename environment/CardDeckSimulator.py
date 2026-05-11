# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
import uuid
from typing import Optional, List, Dict
import random



class DeckInfo(TypedDict):
    deck_id: str
    card_list: List[str]  # ordered list of card_ids
    name: str
    creation_tim: str     # assumed to be a timestamp string (copied typo for direct mapping)

class CardInfo(TypedDict):
    card_id: str
    suit: str
    rank: str
    deck_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Decks: {deck_id: DeckInfo}
        # Each deck maintains a sequence (card_list) of card_ids and its metadata.
        self.decks: Dict[str, DeckInfo] = {}

        # Cards: {card_id: CardInfo}
        # Each card is linked to its deck via deck_id.
        self.cards: Dict[str, CardInfo] = {}

        # Constraints:
        # - Each deck contains zero or more cards, each uniquely identified by card_id.
        # - Card order in each deck (as stored in card_list) matters; shuffling alters this order.
        # - Cards can be added or removed from decks, even after creation.
        # - No duplicates of suit+rank in a deck unless a customization explicitly allows it.
        # - Deck operations (shuffle, remove, deal) must respect the current state of cards.

    def list_decks(self) -> dict:
        """
        List all decks currently in the simulator along with their basic metadata.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict contains: deck_id, name, creation_tim
            }

            If no decks exist, returns data as an empty list.

        Constraints:
            - No input parameters.
        """
        decks_metadata = [
            {
                "deck_id": deck_info["deck_id"],
                "name": deck_info["name"],
                "creation_tim": deck_info["creation_tim"]
            }
            for deck_info in self.decks.values()
        ]
        return { "success": True, "data": decks_metadata }

    def get_deck_info(self, deck_id: str) -> dict:
        """
        Retrieve complete metadata (including card order) for a specific deck.

        Args:
            deck_id (str): Unique identifier for the deck.

        Returns:
            dict: {
                "success": True,
                "data": DeckInfo,   # Complete metadata for the deck, including card_list (order)
            }
            or
            {
                "success": False,
                "error": str,       # Reason (e.g., deck does not exist)
            }

        Constraints:
            - Deck must exist in the simulator.

        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck does not exist" }
        return { "success": True, "data": self.decks[deck_id] }

    def get_deck_card_list(self, deck_id: str) -> dict:
        """
        Retrieve the ordered list of card_ids for a given deck.

        Args:
            deck_id (str): The identifier of the deck to query.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # Ordered list of card_ids in the deck (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # An error description, e.g., deck not found
            }

        Constraints:
            - The deck with the given deck_id must exist.
        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck does not exist" }
        card_list = self.decks[deck_id]["card_list"]
        return { "success": True, "data": card_list.copy() }

    def get_card_info(self, card_id: str) -> dict:
        """
        Retrieve full information for a card (suit, rank, deck membership) by card_id.

        Args:
            card_id (str): The unique identifier of the card.

        Returns:
            dict: On success:
                      {
                        "success": True,
                        "data": CardInfo  # All info for the card
                      }
                  On error (card_id not found):
                      {
                        "success": False,
                        "error": "Card not found"
                      }
        Constraints:
            - card_id must exist in the simulator.
        """
        card = self.cards.get(card_id)
        if card is None:
            return { "success": False, "error": "Card not found" }
        return { "success": True, "data": card }

    def list_cards_in_deck(self, deck_id: str, suit: str = None, rank: str = None) -> dict:
        """
        List all CardInfo entries for cards currently in the specified deck, in their deck order.
        Supports optional filtering by suit and/or rank.

        Args:
            deck_id (str): The deck whose cards to list.
            suit (str, optional): Only return cards with this suit (if provided).
            rank (str, optional): Only return cards with this rank (if provided).

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": [CardInfo, ...]  # In card_list deck order, filtered as requested.
                  }
                - On error: {
                      "success": False,
                      "error": <error message>
                  }

        Constraints:
            - deck_id must exist in self.decks.
            - Only cards currently in this deck as per deck's card_list should be returned.
            - Filtering by suit/rank is applied to cards in this deck only.
        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck does not exist" }

        deck = self.decks[deck_id]
        card_infos = []
        for card_id in deck['card_list']:
            card_info = self.cards.get(card_id)
            if card_info is None:
                continue  # Should not happen, but ignore missing cards for robustness
            if card_info["deck_id"] != deck_id:
                continue  # Card no longer in this deck (consistency check)
            if suit is not None and card_info["suit"] != suit:
                continue
            if rank is not None and card_info["rank"] != rank:
                continue
            card_infos.append(card_info)

        return { "success": True, "data": card_infos }

    def check_card_in_deck(
        self,
        deck_id: str,
        card_id: str = None,
        suit: str = None,
        rank: str = None
    ) -> dict:
        """
        Determine whether a given card (by card_id or suit+rank) exists in the specified deck.

        Args:
            deck_id (str): The deck to search within.
            card_id (str, optional): The card's unique identifier (priority over suit+rank).
            suit (str, optional): Suit of the card (required with rank if card_id not given).
            rank (str, optional): Rank of the card (required with suit if card_id not given).

        Returns:
            dict:
                - success (bool): Whether the check was performed.
                - data (bool): True if the card exists in the deck; False otherwise.
                - error (str): Present (and success=False) if input is invalid or deck does not exist.

        Constraints:
            - Deck must exist.
            - Must provide either card_id OR both suit and rank.
            - Only current members of deck's card_list count for presence.
        """
        if deck_id not in self.decks:
            return {"success": False, "error": "Deck not found"}

        card_list = self.decks[deck_id]["card_list"]

        if card_id is not None:
            # Check by card_id
            found = card_id in card_list
            return {"success": True, "data": found}

        elif suit is not None and rank is not None:
            # Check by suit and rank
            for cid in card_list:
                card = self.cards.get(cid)
                if card and card["suit"] == suit and card["rank"] == rank:
                    return {"success": True, "data": True}
            return {"success": True, "data": False}

        else:
            return {
                "success": False,
                "error": "Must provide either card_id or both suit and rank"
            }

    def find_duplicate_cards(self, deck_id: str) -> dict:
        """
        Detect cards with duplicate (suit, rank) combinations within the specified deck.
        Returns the suit+rank and associated card_ids for each duplicate group.

        Args:
            deck_id (str): The deck to check for duplicates.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, List[str]],  # "suit|rank": [card_ids, ...] where len > 1
            }
            Or, if deck does not exist:
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only cards present in the deck's current card_list are considered.
            - If no duplicates are found, data will be an empty dict.
        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck not found" }

        card_ids_in_deck = self.decks[deck_id]["card_list"]
        suit_rank_to_ids = {}

        for card_id in card_ids_in_deck:
            card_info = self.cards.get(card_id)
            if not card_info:
                continue  # Ignore cards that are missing (corrupted deck state)
            suit_rank = (card_info["suit"], card_info["rank"])
            if suit_rank not in suit_rank_to_ids:
                suit_rank_to_ids[suit_rank] = []
            suit_rank_to_ids[suit_rank].append(card_id)

        # Filter to only show (suit, rank) where duplicates exist
        duplicates = {}
        for (suit, rank), ids in suit_rank_to_ids.items():
            if len(ids) <= 1:
                continue
            duplicates[f"{suit}|{rank}"] = ids

        return { "success": True, "data": duplicates }

    def count_cards_in_deck(self, deck_id: str) -> dict:
        """
        Return the number of cards currently in the specified deck.

        Args:
            deck_id (str): The identifier of the deck.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": int,  # Number of cards in the current deck (possibly 0)
                }
                OR
                {
                    "success": False,
                    "error": str  # Error message if deck not found
                }

        Constraints:
            - The deck_id must exist in the simulator's decks.
        """
        deck = self.decks.get(deck_id)
        if deck is None:
            return { "success": False, "error": "Deck not found" }

        card_count = len(deck["card_list"])
        return { "success": True, "data": card_count }


    def create_deck(self,
                    deck_id: str,
                    name: Optional[str] = "",
                    initial_cards: Optional[List[Dict[str, str]]] = None,
                    allow_duplicates: bool = False
                    ) -> dict:
        """
        Instantiate a new deck and optionally initialize with a default or custom set of cards.

        Args:
            deck_id (str): Unique identifier for the new deck.
            name (str, optional): Friendly name for the deck.
            initial_cards (list of dict, optional): Each dict must have 'suit' and 'rank'. Card_id will be auto-generated.
                If None, deck is empty. If 'default' (str), create standard 52-card set.
            allow_duplicates (bool, optional): If True, allows duplicate (suit, rank) in this deck.

        Returns:
            dict: {
                "success": True,
                "message": "Deck created.",
                "deck_id": deck_id
            }
            or
            {
                "success": False,
                "error": error_message
            }

        Constraints:
            - No duplicate deck_id.
            - No (suit, rank) duplicates in initial_cards unless allow_duplicates is True.
            - Card_id is globally unique (per card).
        """

        if deck_id in self.decks:
            return { "success": False, "error": "Deck with this id already exists." }

        card_list = []
        creation_time = str(time.time())

        # Handle initial_cards (None/empty → empty, 'default' → standard 52 card set)
        if initial_cards is None:
            initial_cards = []

        # If initializing with 'default'
        if isinstance(initial_cards, str) and initial_cards.lower() == "default":
            suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
            ranks = [str(n) for n in range(2, 11)] + ['Jack', 'Queen', 'King', 'Ace']
            cards_to_add = []
            for suit in suits:
                for rank in ranks:
                    cards_to_add.append({'suit': suit, 'rank': rank})
            initial_cards = cards_to_add

        # Build the list, check for duplicates as needed
        seen = set()
        for card in initial_cards:
            suit = card.get("suit")
            rank = card.get("rank")
            if not suit or not rank:
                return { "success": False, "error": "Each initial card must have 'suit' and 'rank'." }
            key = (suit, rank)
            if not allow_duplicates and key in seen:
                return { "success": False, "error": f"Duplicate card in initial_cards: {suit} {rank}" }
            seen.add(key)
            # Generate globally unique card_id
            card_id = str(uuid.uuid4())
            # Add to self.cards
            self.cards[card_id] = {
                "card_id": card_id,
                "suit": suit,
                "rank": rank,
                "deck_id": deck_id
            }
            card_list.append(card_id)

        # Create the DeckInfo
        self.decks[deck_id] = {
            "deck_id": deck_id,
            "card_list": card_list,
            "name": name or "",
            "creation_tim": creation_time
        }

        return {
            "success": True,
            "message": "Deck created.",
            "deck_id": deck_id
        }

    def remove_card_from_deck(
        self,
        deck_id: str,
        card_id: str = None,
        suit: str = None,
        rank: str = None,
    ) -> dict:
        """
        Remove a specific card from a deck.

        Args:
            deck_id (str): The deck to remove the card from.
            card_id (str, optional): ID of the card to remove.
            suit (str, optional): Card suit (e.g., 'Hearts').
            rank (str, optional): Card rank (e.g., 'Ace', '10', 'Jack').

        Returns:
            dict: {
                "success": True,
                "message": "Removed card <card_id> from deck <deck_id>"
            } or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - deck must exist
            - card_id must identify an existing card in that deck OR
              suit and rank must match at least one existing card in that deck.
            - Only the first suit/rank match is removed.
            - Removes the card from both `deck.card_list` and `self.cards`.
        """
        # 1. Deck exists?
        if deck_id not in self.decks:
            return {"success": False, "error": "Deck does not exist"}

        # 2. Must specify either card_id or suit+rank
        if not card_id and (not suit or not rank):
            return {"success": False, "error": "Must specify card_id or (suit and rank)"}

        deck = self.decks[deck_id]

        # 3. Locate card to remove
        actual_card_id = None
        # Use card_id if provided and exists
        if card_id:
            # Card must exist
            card = self.cards.get(card_id)
            if not card or card['deck_id'] != deck_id:
                return {"success": False, "error": "Card does not exist in specified deck"}
            actual_card_id = card_id
        else:
            # Find first card in deck's card_list with matching suit & rank
            for cid in deck['card_list']:
                card = self.cards.get(cid)
                if card and card['deck_id'] == deck_id and card['suit'] == suit and card['rank'] == rank:
                    actual_card_id = cid
                    break
            if not actual_card_id:
                return {"success": False, "error": "No card with given suit and rank found in that deck"}

        # 4. Remove from deck's card_list (if present)
        if actual_card_id in deck['card_list']:
            deck['card_list'].remove(actual_card_id)
        else:
            # Should not happen unless state is corrupt
            return {"success": False, "error": "Inconsistent state: card not present in deck's card order"}

        # 5. Remove from self.cards
        if actual_card_id in self.cards:
            del self.cards[actual_card_id]

        # Operation success
        return {"success": True, "message": f"Removed card {actual_card_id} from deck {deck_id}"}

    def remove_cards_by_rank(self, deck_id: str, ranks: list) -> dict:
        """
        Remove all cards of specified rank(s) from the deck with ID deck_id.

        Args:
            deck_id (str): The deck to remove cards from.
            ranks (list of str): The card ranks to remove (e.g., ["Jack", "Ace"]).

        Returns:
            dict: {
                "success": True,
                "message": "Removed N cards of ranks [ranks] from deck [deck_id]"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - If deck does not exist, fail with error message.
            - If ranks param is not a non-empty list of strings, fail.
            - Only cards currently present in the specified deck are affected.
            - Card order in deck is maintained for remaining cards.
        """
        if deck_id not in self.decks:
            return {"success": False, "error": f"Deck '{deck_id}' does not exist"}

        if not isinstance(ranks, list) or not all(isinstance(r, str) for r in ranks) or not ranks:
            return {"success": False, "error": "Parameter 'ranks' must be a non-empty list of strings"}

        deck = self.decks[deck_id]
        old_card_list = deck['card_list']
        cards_to_remove = []
        remaining_card_list = []

        # Find all cards in this deck matching the specified ranks
        for card_id in old_card_list:
            card_info = self.cards.get(card_id)
            if card_info and card_info["deck_id"] == deck_id and card_info["rank"] in ranks:
                cards_to_remove.append(card_id)
            else:
                remaining_card_list.append(card_id)

        # Remove these card_ids from the deck's card_list
        self.decks[deck_id]['card_list'] = remaining_card_list

        # Remove the CardInfo objects themselves (since each card_id is unique per deck)
        for card_id in cards_to_remove:
            if card_id in self.cards:
                del self.cards[card_id]

        return {
            "success": True,
            "message": f"Removed {len(cards_to_remove)} cards of ranks {ranks} from deck '{deck_id}'"
        }

    def remove_cards_by_suit(self, deck_id: str, suit: str) -> dict:
        """
        Remove all cards of the specified suit from the given deck.

        Args:
            deck_id (str): The ID of the deck to operate on.
            suit (str): The suit to remove (e.g., 'Spades', 'Hearts', ...).

        Returns:
            dict: {
                "success": True,
                "message": "Removed X cards of suit Y from deck Z"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Deck must exist.
            - All cards of the given suit will be removed from the deck and the environment (no card duplication).
            - Operation is idempotent: removing a suit that's not present is still successful.
        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck not found" }

        card_list = self.decks[deck_id]['card_list']
        to_remove = []
        for card_id in card_list:
            card_info = self.cards.get(card_id)
            if card_info and card_info.get('suit') == suit:
                to_remove.append(card_id)
        # Remove from card_list
        self.decks[deck_id]['card_list'] = [cid for cid in card_list if cid not in to_remove]
        # Remove cards from environment
        for card_id in to_remove:
            self.cards.pop(card_id, None)
        return {
            "success": True,
            "message": f"Removed {len(to_remove)} cards of suit {suit} from deck {deck_id}"
        }

    def add_card_to_deck(
        self,
        deck_id: str,
        card_id: str,
        suit: str = None,
        rank: str = None,
        position: int = None
    ) -> dict:
        """
        Add a new or existing card to the specified position in a deck,
        enforcing the no-duplicate (suit+rank) constraint.
    
        Args:
            deck_id (str): The ID of the target deck.
            card_id (str): The unique identifier for the card.
            suit (str, optional): The card's suit (required if new card).
            rank (str, optional): The card's rank (required if new card).
            position (int, optional): Position to insert (0-based). Defaults to end of card_list.
        
        Returns:
            dict: Success structure (see below).
                {
                    "success": True,
                    "message": str
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Target deck must exist.
            - No duplicate (suit, rank) allowed within a deck.
            - If card_id not in self.cards, suit & rank are required.
            - Card inserted at position (append if out of bounds or not provided).
        """
        # 1. Deck existence
        if deck_id not in self.decks:
            return { "success": False, "error": f"Deck '{deck_id}' does not exist" }
    
        deck = self.decks[deck_id]
        deck_cards = deck['card_list']

        # 2. Card existence and info
        card_info = self.cards.get(card_id, None)
        is_new_card = card_info is None

        if is_new_card:
            # Need suit and rank for new card
            if suit is None or rank is None:
                return {
                    "success": False,
                    "error": "suit and rank are required to create a new card"
                }
            # Check for duplicate suit+rank in the deck (no duplicates allowed)
            for cid in deck_cards:
                cinfo = self.cards[cid]
                if cinfo['suit'] == suit and cinfo['rank'] == rank:
                    return {
                        "success": False,
                        "error": f"Deck '{deck_id}' already contains a card with suit '{suit}' and rank '{rank}'"
                    }
            # Create the new card
            card_info = {
                "card_id": card_id,
                "suit": suit,
                "rank": rank,
                "deck_id": deck_id
            }
            self.cards[card_id] = card_info
        else:
            # Card exists, check duplicate suit+rank in this deck
            card_suit = card_info['suit']
            card_rank = card_info['rank']
            for cid in deck_cards:
                cinfo = self.cards[cid]
                if cinfo['suit'] == card_suit and cinfo['rank'] == card_rank:
                    return {
                        "success": False,
                        "error": f"Deck '{deck_id}' already contains a card with suit '{card_suit}' and rank '{card_rank}'"
                    }
            # Move card from old deck (if present), update deck_id
            old_deck_id = card_info.get('deck_id')
            if old_deck_id and old_deck_id in self.decks:
                old_card_list = self.decks[old_deck_id]['card_list']
                if card_id in old_card_list:
                    old_card_list.remove(card_id)
            card_info['deck_id'] = deck_id

        # 3. Insert card_id into card_list at correct position
        if position is None or not isinstance(position, int) or position < 0 or position > len(deck_cards):
            deck['card_list'].append(card_id)
            pos = len(deck_cards) - 1
        else:
            deck['card_list'].insert(position, card_id)
            pos = position

        return {
            "success": True,
            "message": f"Card '{card_id}' added to deck '{deck_id}' at position {pos}"
        }


    def shuffle_deck(self, deck_id: str) -> dict:
        """
        Randomly reorder the card_list of a specified deck.

        Args:
            deck_id (str): The unique identifier for the deck to shuffle.

        Returns:
            dict: On success, {
                      "success": True,
                      "message": "Deck shuffled successfully."
                  }
                  On failure, {
                      "success": False,
                      "error": <reason>
                  }

        Constraints:
            - The deck must exist.
            - Only the order of card_list is changed.
            - No cards are added or removed.
        """
        if deck_id not in self.decks:
            return {"success": False, "error": "Deck does not exist."}

        card_list = self.decks[deck_id]["card_list"]
        # Shuffle in-place (safe for empty and singleton lists)
        random.shuffle(card_list)
        self.decks[deck_id]["card_list"] = card_list  # Not necessary (list is mutable), for clarity

        return {"success": True, "message": "Deck shuffled successfully."}

    def deal_cards_from_deck(
        self,
        deck_id: str,
        count: int = 1,
        position = "top"  # Can be "top" or integer index (0-based)
    ) -> dict:
        """
        Remove and return one or more cards from the specified deck.

        Args:
            deck_id (str): The deck to deal cards from.
            count (int, default=1): Number of cards to deal.
            position (Union[str, int], default="top"):
                - If "top" (default), deal cards starting from the top (index 0).
                - If integer, starting index in deck's card_list.

        Returns:
            dict: If successful:
                {
                    "success": True,
                    "dealt_cards": List[CardInfo]
                }
                If error:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Deck must exist and have enough cards.
            - Position must be valid ("top" or integer in range).
            - `count` must be > 0 and not exceed available cards from position.

        Notes:
            - Dealt cards are removed from the deck's sequence.
            - Cards remain in global cards, but are no longer included in the deck's card_list.
        """
        # Check deck exists
        if deck_id not in self.decks:
            return {"success": False, "error": "Deck does not exist"}

        card_list = self.decks[deck_id]["card_list"]

        # Validate count
        if not isinstance(count, int) or count < 1:
            return {"success": False, "error": "Invalid card count"}

        # Determine start index
        if position == "top":
            start = 0
        elif isinstance(position, int):
            if position < 0 or position >= len(card_list):
                return {"success": False, "error": "Position out of range"}
            start = position
        else:
            return {"success": False, "error": "Invalid position parameter"}

        # Check enough cards to deal
        if start + count > len(card_list):
            return {"success": False, "error": "Not enough cards to deal from specified position"}

        # Remove cards and collect their info
        dealt_ids = card_list[start:start + count]
        dealt_cards = [self.cards[card_id] for card_id in dealt_ids]

        # Remove from the deck's card_list
        # (Delete the slice)
        del card_list[start:start + count]
        # Update card_list in deck info
        self.decks[deck_id]["card_list"] = card_list

        # If you want to mark dealt cards as out-of-deck, you could set their deck_id = None
        # for card_id in dealt_ids:
        #     self.cards[card_id]["deck_id"] = None

        return {"success": True, "dealt_cards": dealt_cards}

    def empty_deck(self, deck_id: str) -> dict:
        """
        Remove all cards from a deck, leaving it empty (without deleting the deck).

        Args:
            deck_id (str): Identifier of the deck to be emptied.

        Returns:
            dict: {
                "success": True,
                "message": "All cards removed from deck <deck_id>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The deck with the given deck_id must exist.
            - The deck remains; only its cards are removed.
            - All CardInfo entries belonging to this deck_id are removed from self.cards and the deck's card_list is emptied.
        """
        if deck_id not in self.decks:
            return {"success": False, "error": f"Deck '{deck_id}' does not exist."}

        # Remove cards associated with this deck
        removed_card_ids = [card_id for card_id, card in self.cards.items() if card["deck_id"] == deck_id]
    
        for card_id in removed_card_ids:
            del self.cards[card_id]

        # Empty the card list of the deck
        self.decks[deck_id]["card_list"] = []

        return {"success": True, "message": f"All cards removed from deck '{deck_id}'."}

    def delete_deck(self, deck_id: str, delete_cards: bool = False) -> dict:
        """
        Permanently remove a deck, and optionally its cards, from the simulator.

        Args:
            deck_id (str): The ID of the deck to remove.
            delete_cards (bool, optional): If True, also remove all cards belonging to this deck. If False, cards are left in the simulator (potentially with invalid deck_id).

        Returns:
            dict:
                On success:
                  { "success": True, "message": "Deleted deck <deck_id> (and its cards if applicable)." }
                On failure:
                  { "success": False, "error": "<reason>" }

        Constraints:
            - Deck must exist.
            - Card deletion only affects cards belonging to this deck.
        """
        if deck_id not in self.decks:
            return { "success": False, "error": "Deck does not exist" }
    
        # Remove deck from self.decks
        del self.decks[deck_id]

        deleted_card_count = 0
        if delete_cards:
            # Find and delete cards that belong to this deck
            card_ids_to_delete = [card_id for card_id, card_info in self.cards.items()
                                  if card_info["deck_id"] == deck_id]
            for card_id in card_ids_to_delete:
                del self.cards[card_id]
                deleted_card_count += 1

            return {
                "success": True,
                "message": f"Deleted deck {deck_id} and its {deleted_card_count} card(s)."
            }
        else:
            # Option: Remove only the deck, cards with the deck_id can remain (could be considered 'orphaned')
            return {
                "success": True,
                "message": f"Deleted deck {deck_id}; cards remain in simulator."
            }


class CardDeckSimulator(BaseEnv):
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

    def list_decks(self, **kwargs):
        return self._call_inner_tool('list_decks', kwargs)

    def get_deck_info(self, **kwargs):
        return self._call_inner_tool('get_deck_info', kwargs)

    def get_deck_card_list(self, **kwargs):
        return self._call_inner_tool('get_deck_card_list', kwargs)

    def get_card_info(self, **kwargs):
        return self._call_inner_tool('get_card_info', kwargs)

    def list_cards_in_deck(self, **kwargs):
        return self._call_inner_tool('list_cards_in_deck', kwargs)

    def check_card_in_deck(self, **kwargs):
        return self._call_inner_tool('check_card_in_deck', kwargs)

    def find_duplicate_cards(self, **kwargs):
        return self._call_inner_tool('find_duplicate_cards', kwargs)

    def count_cards_in_deck(self, **kwargs):
        return self._call_inner_tool('count_cards_in_deck', kwargs)

    def create_deck(self, **kwargs):
        return self._call_inner_tool('create_deck', kwargs)

    def remove_card_from_deck(self, **kwargs):
        return self._call_inner_tool('remove_card_from_deck', kwargs)

    def remove_cards_by_rank(self, **kwargs):
        return self._call_inner_tool('remove_cards_by_rank', kwargs)

    def remove_cards_by_suit(self, **kwargs):
        return self._call_inner_tool('remove_cards_by_suit', kwargs)

    def add_card_to_deck(self, **kwargs):
        return self._call_inner_tool('add_card_to_deck', kwargs)

    def shuffle_deck(self, **kwargs):
        return self._call_inner_tool('shuffle_deck', kwargs)

    def deal_cards_from_deck(self, **kwargs):
        return self._call_inner_tool('deal_cards_from_deck', kwargs)

    def empty_deck(self, **kwargs):
        return self._call_inner_tool('empty_deck', kwargs)

    def delete_deck(self, **kwargs):
        return self._call_inner_tool('delete_deck', kwargs)
