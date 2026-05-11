# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class BoardInfo(TypedDict):
    board_id: str
    name: str
    description: str
    owner_user_id: str

class ColumnInfo(TypedDict):
    column_id: str
    board_id: str
    name: str
    position: int  # Unique within board

class CardInfo(TypedDict):
    card_id: str
    board_id: str
    column_id: str
    title: str
    description: str
    assigned_user_id: str
    status: str
    position: int  # Ordering within column

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str
    role: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Kanban board environment.
        """

        # Boards: {board_id: BoardInfo}
        self.boards: Dict[str, BoardInfo] = {}

        # Columns: {column_id: ColumnInfo}
        self.columns: Dict[str, ColumnInfo] = {}

        # Cards: {card_id: CardInfo}
        self.cards: Dict[str, CardInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Non-state initialization flags/options that may be injected by cases.
        self.feature_flags: Dict[str, Any] = {}

        # Constraints:
        # - Cards must belong to a valid board and a valid column within that board.
        # - Card movement may trigger status updates or notifications.
        # - Only authorized users can move cards.
        # - Column positions should be unique within a board.
        # - Card positions must be maintained within columns for ordering.

    def get_board_by_id(self, board_id: str) -> dict:
        """
        Retrieve detailed information for a specific board using board_id.

        Args:
            board_id (str): The unique identifier for the board.

        Returns:
            dict:
              - success (bool): True if found, False otherwise.
              - data (BoardInfo): On success, the board details.
              - error (str): On failure, an error message.

        Constraints:
            - board_id must correspond to an existing board.
        """
        if board_id not in self.boards:
            return { "success": False, "error": "Board not found" }

        return { "success": True, "data": self.boards[board_id] }

    def list_boards_by_user(self, user_id: str) -> dict:
        """
        List all boards owned (and accessible) by the specified user.

        Args:
            user_id (str): The user ID.

        Returns:
            dict: {
                "success": True,
                "data": List[BoardInfo], # List of boards owned by the user (may be empty).
            }
            or
            {
                "success": False,
                "error": str, # e.g., "User does not exist"
            }

        Constraints:
            - User must exist.
            - Boards returned are those where user is owner. (If enhanced access logic exists, include here.)
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            board_info for board_info in self.boards.values()
            if board_info["owner_user_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_column_by_id(self, column_id: str) -> dict:
        """
        Retrieve details for a specific column using column_id.

        Args:
            column_id (str): The unique identifier for the column.

        Returns:
            dict: {
                "success": True,
                "data": ColumnInfo  # The column information
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., column not found
            }

        Constraints:
            - The column with the given column_id must exist in the system.
        """
        column_info = self.columns.get(column_id)
        if column_info is None:
            return { "success": False, "error": "Column not found" }

        return { "success": True, "data": column_info }

    def list_columns_by_board(self, board_id: str) -> dict:
        """
        List all columns for a given board, ordered by position.

        Args:
            board_id (str): The ID of the board whose columns are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ColumnInfo],  # Ordered list of columns (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error message if board does not exist
            }

        Constraints:
            - Board must exist in the system.
            - Columns are filtered for the board_id and ordered by position (ascending).
        """
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist" }

        columns = [
            column for column in self.columns.values()
            if column["board_id"] == board_id
        ]
        columns.sort(key=lambda col: col["position"])
        return { "success": True, "data": columns }

    def get_card_by_id(self, card_id: str) -> dict:
        """
        Retrieve a card's details by its unique card_id.

        Args:
            card_id (str): The unique identifier of the card.

        Returns:
            dict: {
                "success": True,
                "data": CardInfo,  # The card's info if found
            }
            or
            {
                "success": False,
                "error": str  # "Card not found" if id is missing
            }

        Constraints:
            - The card_id must exist in the Kanban system.
        """
        card = self.cards.get(card_id)
        if card is None:
            return {"success": False, "error": "Card not found"}
        return {"success": True, "data": card}

    def list_cards_by_column(self, column_id: str) -> dict:
        """
        List all cards in the specified column, ordered by their position.

        Args:
            column_id (str): The ID of the column.

        Returns:
            dict: {
                "success": True,
                "data": List[CardInfo],  # Cards belonging to the column in position order.
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., column not found)
            }

        Constraints:
            - The given column_id must exist in the system.
            - Cards are sorted by the 'position' field in ascending order.
        """
        if column_id not in self.columns:
            return { "success": False, "error": "Column does not exist" }

        cards_in_column = [
            card for card in self.cards.values()
            if card["column_id"] == column_id
        ]
        sorted_cards = sorted(cards_in_column, key=lambda c: c["position"])

        return { "success": True, "data": sorted_cards }

    def list_cards_by_board(self, board_id: str) -> dict:
        """
        List all cards contained within a specific board.

        Args:
            board_id (str): The ID of the board to retrieve cards from.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[CardInfo],  # List of cards for the board (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error, e.g. board does not exist
                }

        Constraints:
            - The board with the provided board_id must exist.
        """
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist" }

        cards_in_board = [
            card_info for card_info in self.cards.values()
            if card_info["board_id"] == board_id
        ]

        return { "success": True, "data": cards_in_board }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve full user information using user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            } if the user is found,
            otherwise {
                "success": False,
                "error": "User not found"
            }
        Constraints:
            - The user must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def check_user_authorization_for_card_action(self, user_id: str, card_id: str) -> dict:
        """
        Verify if a user is authorized to move or edit a card.

        Args:
            user_id (str): ID of the user.
            card_id (str): ID of the card.

        Returns:
            dict: {
                "success": True,
                "authorized": bool,
                "reason": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User and card must exist.
            - Only board owners, assigned users, or admins can move/edit a card.
        """
        auth_mode = str(self.feature_flags.get("check_user_authorization_for_card_action", "")).strip().lower()
        if auth_mode in {"authorized", "enabled", "allow_all", "always"}:
            return { "success": True, "authorized": True, "reason": f"Authorization override '{auth_mode}' active" }

        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check card exists
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card does not exist" }

        # Check board exists
        board_id = card["board_id"]
        board = self.boards.get(board_id)
        if not board:
            return { "success": False, "error": "Board does not exist" }

        # Authorization checks
        # Admins can do anything
        if user.get("role", "").lower() == "admin":
            return { "success": True, "authorized": True, "reason": "User is admin" }

        # Board owner can operate any card in their board
        if user_id == board["owner_user_id"]:
            return { "success": True, "authorized": True, "reason": "User is board owner" }

        # Assigned user can operate their card
        if user_id == card.get("assigned_user_id", ""):
            return { "success": True, "authorized": True, "reason": "User is assigned to this card" }

        # Otherwise unauthorized
        return { "success": True, "authorized": False, "reason": "User lacks permission for this card" }

    def validate_column_in_board(self, column_id: str, board_id: str) -> dict:
        """
        Check if a given column_id exists within a specified board.

        Args:
            column_id (str): The unique identifier for the column.
            board_id (str): The unique identifier for the board.

        Returns:
            dict: 
                On success: { "success": True, "data": { "valid": True } }
                On error: { "success": False, "error": <reason> }

        Constraints:
            - Both the board and column must exist.
            - The column must belong to the specified board.
        """
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist" }
        if column_id not in self.columns:
            return { "success": False, "error": "Column does not exist" }

        column = self.columns[column_id]
        if column["board_id"] != board_id:
            return { "success": False, "error": "Column does not belong to the specified board" }

        return { "success": True, "data": { "valid": True } }

    def validate_card_in_column_and_board(self, card_id: str, column_id: str, board_id: str) -> dict:
        """
        Ensure a card belongs to a specific column and board.

        Args:
            card_id (str): The card's unique identifier.
            column_id (str): The column's unique identifier in which the card should be.
            board_id (str): The board's unique identifier in which the card should be.

        Returns:
            dict: 
              - { "success": True, "data": True } if the card belongs to the specified column and board
              - { "success": True, "data": False } if the card does not belong to the specified column/board
              - { "success": False, "error": str } if input entities are not found

        Constraints:
            - Card must exist.
            - Column must exist.
            - Board must exist.
        """
        if card_id not in self.cards:
            return { "success": False, "error": "Card not found" }
        if column_id not in self.columns:
            return { "success": False, "error": "Column not found" }
        if board_id not in self.boards:
            return { "success": False, "error": "Board not found" }
    
        card_info = self.cards[card_id]
        if card_info["column_id"] == column_id and card_info["board_id"] == board_id:
            return { "success": True, "data": True }
        else:
            return { "success": True, "data": False }

    def get_next_card_position_in_column(self, column_id: str) -> dict:
        """
        Determines the next available position value for a card in the specified column.
        The next position is (current maximum position in the column) + 1.
        If there are no cards in the column, position starts at 1.

        Args:
            column_id (str): The ID of the target column.

        Returns:
            dict:
                On success: { "success": True, "data": int }
                On failure (e.g. invalid column): { "success": False, "error": str }

        Constraints:
            - column_id must refer to an existing column.
        """
        if column_id not in self.columns:
            return {"success": False, "error": "Column does not exist."}

        positions = [
            card_info["position"] for card_info in self.cards.values()
            if card_info["column_id"] == column_id
        ]
        next_position = max(positions) + 1 if positions else 1

        return {"success": True, "data": next_position}

    def get_column_position_in_board(self, column_id: str) -> dict:
        """
        Get the numerical position of a column in the board workflow.

        Args:
            column_id (str): The identifier for the column.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "column_id": str,
                    "board_id": str,
                    "position": int,
                }
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. 'Column does not exist'
            }

        Constraints:
            - The column_id must exist in the system.
            - The returned position is unique within its board.
        """
        column = self.columns.get(column_id)
        if column is None:
            return { "success": False, "error": "Column does not exist" }
        return {
            "success": True,
            "data": {
                "column_id": column_id,
                "board_id": column["board_id"],
                "position": column["position"],
            }
        }

    def list_users_by_board(self, board_id: str) -> dict:
        """
        List all users who are participants/collaborators in a board.

        Args:
            board_id (str): The ID of the board.

        Returns:
            dict:
                - On success: {"success": True, "data": List[UserInfo]}
                - On failure: {"success": False, "error": "Board does not exist"}

        Constraints:
            - User is a participant if they are (1) the board owner,
              or (2) assigned to any card on the board.
            - Users are unique in the result.
        """
        if board_id not in self.boards:
            return {"success": False, "error": "Board does not exist"}

        ordered_user_ids = []
        seen = set()

        def add_user(user_id: str):
            if user_id and user_id not in seen and user_id in self.users:
                ordered_user_ids.append(user_id)
                seen.add(user_id)

        # Board owner is always listed first.
        add_user(self.boards[board_id]["owner_user_id"])

        # Then preserve first-seen card order for assigned collaborators on the board.
        board_cards = [
            card for card in self.cards.values()
            if card["board_id"] == board_id and card["assigned_user_id"]
        ]
        board_cards.sort(key=lambda card: (card["column_id"], card["position"], card["card_id"]))
        for card in board_cards:
            add_user(card["assigned_user_id"])

        user_list = [self.users[user_id] for user_id in ordered_user_ids]

        return {"success": True, "data": user_list}

    def move_card_to_column(
        self,
        card_id: str,
        target_column_id: str,
        user_id: str
    ) -> dict:
        """
        Move a card to a different column within the same board.
        Updates the card's column_id and assigns the next position at the end of the target column.

        Args:
            card_id (str): The ID of the card to move.
            target_column_id (str): The ID of the column to move the card into.
            user_id (str): The ID of the user attempting the operation.

        Returns:
            dict: {
                "success": True,
                "message": "Card moved to column."
            } on success,
            or {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - Card and target column must exist and be in the same board.
            - Only authorized users can move cards.
            - Card positions are unique and maintained within columns.
            - May trigger status updates or notifications.
        """
        # Validate card existence
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card does not exist." }

        # Validate target column existence
        column = self.columns.get(target_column_id)
        if not column:
            return { "success": False, "error": "Target column does not exist." }

        # Validate card and column are in the same board
        if card["board_id"] != column["board_id"]:
            return { "success": False, "error": "Card and column are not in the same board." }

        # Authorize user
        # Assume existence of check_user_authorization_for_card_action(user_id, card_id, action)
        auth_hook = getattr(self, "check_user_authorization_for_card_action", None)
        if callable(auth_hook):
            auth_result = auth_hook(user_id, card_id)
            if not (isinstance(auth_result, dict) and auth_result.get("success", False)):
                error_msg = auth_result.get("error", "User is not authorized to move this card.")
                return { "success": False, "error": error_msg }
            if not auth_result.get("authorized", False):
                return { "success": False, "error": auth_result.get("reason", "User is not authorized to move this card.") }
        else:
            # Default: permit any user if method not implemented
            pass

        # Assign position = next unused position in destination column
        current_positions = [
            info["position"] for info in self.cards.values()
            if info["column_id"] == target_column_id
        ]
        next_position = (max(current_positions) + 1) if current_positions else 1

        # Move card: update column_id and position
        card["column_id"] = target_column_id
        card["position"] = next_position

        # Optionally: trigger status update on move
        status_hook = getattr(self, "trigger_card_status_update_on_move", None)
        if callable(status_hook):
            _ = status_hook(card_id, target_column_id)

        # Optionally: notify users
        notify_hook = getattr(self, "notify_users_on_card_movement", None)
        if callable(notify_hook):
            _ = notify_hook(card_id)

        return { "success": True, "message": f"Card '{card_id}' moved to column '{target_column_id}' at position {next_position}." }

    def update_card_position_in_column(self, card_id: str, new_position: int) -> dict:
        """
        Change a card’s order within its column. The card will be moved to the given position,
        and all other cards will be shifted to maintain unique, sequential positions within the column.

        Args:
            card_id (str): The card to reposition within its column.
            new_position (int): The target position (1-based index) within the column.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Card position updated in column" }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Card must exist and belong to a valid column/board.
            - Position must be within 1..N, where N is number of cards in column.
            - Positions after update are sequential and unique.

        Notes:
            - No exceptions are raised; errors are reported in the returned dict.
        """
        # Validate card exists
        card_info = self.cards.get(card_id)
        if not card_info:
            return { "success": False, "error": "Card does not exist" }

        column_id = card_info["column_id"]
        board_id = card_info["board_id"]

        # Validate column exists and belongs to board
        column_info = self.columns.get(column_id)
        if not column_info or column_info["board_id"] != board_id:
            return { "success": False, "error": "Card's column or board is invalid" }

        # Get all cards in this column, sorted by position
        cards_in_column = [
            c for c in self.cards.values() if c["column_id"] == column_id
        ]
        if not cards_in_column:
            return { "success": False, "error": "No cards found in the column" }

        cards_in_column.sort(key=lambda x: x["position"])

        N = len(cards_in_column)
        # Check position bounds
        if new_position < 1 or new_position > N:
            return { "success": False, "error": f"New position {new_position} is out of range (1..{N})" }

        # Save the ordering (excluding the moved card)
        cards_in_column_id_order = [c for c in cards_in_column if c["card_id"] != card_id]

        # Insert the moved card at required position
        # new_position is 1-based; so insert at new_position-1
        insert_idx = new_position - 1
        moved_card = card_info.copy()
        cards_in_new_order = (
            cards_in_column_id_order[:insert_idx]
            + [moved_card]
            + cards_in_column_id_order[insert_idx:]
        )

        # Re-assign positions sequentially
        for idx, c in enumerate(cards_in_new_order):
            self.cards[c["card_id"]]["position"] = idx + 1
        self.cards[card_id]["position"] = new_position

        return { "success": True, "message": "Card position updated in column" }

    def trigger_card_status_update_on_move(self, card_id: str, target_column_id: str) -> dict:
        """
        Update the card's status if moving to a column implies a status change (e.g., "In Progress","Done").

        Args:
            card_id (str): The card being moved.
            target_column_id (str): The column to which the card is being moved.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Card status updated to <status>" | "Card status unchanged"
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Card and Column must exist.
            - Card must belong to the same board as the column.
            - Status only updated if moving into a special-named column.
        """
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card not found" }
        column = self.columns.get(target_column_id)
        if not column:
            return { "success": False, "error": "Target column not found" }
        if card["board_id"] != column["board_id"]:
            return { "success": False, "error": "Card and column do not belong to the same board" }

        # Determine the new status based on target column's name
        col_name = column["name"].strip().lower()
        status_map = {
            "in progress": "In Progress",
            "done": "Done",
            # Add other mappings if needed
        }
        new_status = status_map.get(col_name, None)

        if new_status and card["status"] != new_status:
            card["status"] = new_status  # update in self.cards dict
            return {
                "success": True,
                "message": f"Card status updated to {new_status}"
            }
        else:
            return {
                "success": True,
                "message": "Card status unchanged"
            }

    def notify_users_on_card_movement(self, card_id: str) -> dict:
        """
        Generate notifications for relevant users when a card is moved.

        Args:
            card_id (str): The ID of the card that has been moved.

        Returns:
            dict: {
                "success": True,
                "message": "Notifications sent to: [list of user display names or IDs]"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Card must exist.
            - Notifies both assigned user and board owner (if distinct).
            - No notifications are sent if neither can be found.
        """
        # Validate card existence
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card not found"}

        board_id = card.get("board_id")
        board = self.boards.get(board_id)
        if not board:
            return {"success": False, "error": "Associated board not found"}

        assigned_user_id = card.get("assigned_user_id")
        owner_user_id = board.get("owner_user_id")

        notified_users = []
        notified_user_ids = set()

        # Notify assigned user if exists
        assigned_user = self.users.get(assigned_user_id)
        if assigned_user:
            notified_users.append(assigned_user["name"])
            notified_user_ids.add(assigned_user_id)
            # Optionally: self.notifications.append({...}) if notifications were persisted

        # Notify board owner if not already notified
        if owner_user_id and owner_user_id not in notified_user_ids:
            owner_user = self.users.get(owner_user_id)
            if owner_user:
                notified_users.append(owner_user["name"])
                notified_user_ids.add(owner_user_id)
                # Optionally: self.notifications.append({...})

        if not notified_users:
            return {"success": False, "error": "No valid users to notify (assigned user and board owner missing)"}

        # Simulated notification action (could be persisted/extended)
        return {
            "success": True,
            "message": f"Notifications sent to: {', '.join(notified_users)}"
        }

    def create_card(
        self,
        card_id: str,
        board_id: str,
        column_id: str,
        title: str,
        description: str,
        assigned_user_id: str,
        status: str,
        position: int
    ) -> dict:
        """
        Add a new card to a column in a board at a specific position.

        Args:
            card_id (str): Unique card identifier.
            board_id (str): Board where card will be created.
            column_id (str): Column (must belong to board) for card placement.
            title (str): Title of the card/task.
            description (str): Text description.
            assigned_user_id (str): User assigned to card (empty or valid user).
            status (str): Initial card status.
            position (int): Intended order/position in column (0-based).

        Returns:
            dict:
                On success: { "success": True, "message": "Card created in column X at position Y" }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - card_id must be unique.
            - board_id and column_id must exist, column must belong to board.
            - assigned_user_id must be empty or valid user_id.
            - position must be valid (0 <= position <= len(cards in column)).
            - Cards in column maintain ordering; on conflicting position, shift existing cards accordingly.
        """
        # Check card_id uniqueness
        if card_id in self.cards:
            return { "success": False, "error": "Card ID already exists." }

        # Check board existence
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist." }

        # Check column existence and belonging to board
        column_info = self.columns.get(column_id)
        if not column_info:
            return { "success": False, "error": "Column does not exist." }
        if column_info["board_id"] != board_id:
            return { "success": False, "error": "Column does not belong to board." }

        # Assigned user validation (allow empty string, else must exist)
        if assigned_user_id and assigned_user_id not in self.users:
            return { "success": False, "error": "Assigned user does not exist." }

        # Get cards currently in the column (ordered by position)
        cards_in_column = [
            c for c in self.cards.values()
            if c["column_id"] == column_id and c["board_id"] == board_id
        ]
        cards_in_column.sort(key=lambda x: x["position"])

        if position < 0 or position > len(cards_in_column):
            return { "success": False, "error": "Position is out of bounds." }

        # Shift cards at and after the insertion position
        for c in cards_in_column:
            if c["position"] >= position:
                c["position"] += 1

        # Create new card
        new_card: CardInfo = {
            "card_id": card_id,
            "board_id": board_id,
            "column_id": column_id,
            "title": title,
            "description": description,
            "assigned_user_id": assigned_user_id,
            "status": status,
            "position": position
        }
        self.cards[card_id] = new_card

        return {
            "success": True,
            "message": f"Card '{card_id}' created in column '{column_id}' at position {position}."
        }

    def delete_card(self, card_id: str) -> dict:
        """
        Remove a card from the board and its column.
        Also reorders the remaining cards in the column to maintain contiguous positions.

        Args:
            card_id (str): The unique identifier of the card to delete.

        Returns:
            dict:
                - success: True and message if deletion was successful
                - success: False and error message otherwise

        Constraints:
            - Card must exist.
            - After deletion, card positions within the same column must remain contiguous (0, 1, 2, ...).
        """
        # Check if card exists
        card_info = self.cards.get(card_id)
        if not card_info:
            return { "success": False, "error": "Card does not exist." }
    
        column_id = card_info["column_id"]
        # Remove the card
        del self.cards[card_id]

        # Get all cards in the same column (after deletion)
        cards_in_column = [
            card for card in self.cards.values()
            if card["column_id"] == column_id
        ]
        # Sort by current position just in case
        cards_in_column.sort(key=lambda x: x["position"])
        # Reassign positions to be contiguous
        for idx, card in enumerate(cards_in_column):
            if card["position"] != idx:
                card["position"] = idx

        return {"success": True, "message": "Card deleted."}

    def update_card_details(
        self,
        card_id: str,
        title: str = None,
        description: str = None,
        assigned_user_id: str = None
    ) -> dict:
        """
        Edit the title, description, and/or assignee of a card.

        Args:
            card_id (str): The ID of the card to update.
            title (str, optional): New title for the card.
            description (str, optional): New description for the card.
            assigned_user_id (str, optional): User ID to assign the card to.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Card details updated." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The card must exist.
            - If assigned_user_id is provided, the corresponding user must exist.
            - At least one of title, description, assigned_user_id must be provided.
        """
        # Check card existence
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card does not exist."}

        # Check if any field to update is provided
        if title is None and description is None and assigned_user_id is None:
            return {"success": False, "error": "No new details provided to update."}

        # Empty string is a valid way to keep/unset assignee on this board.
        if assigned_user_id is not None and assigned_user_id != "" and assigned_user_id not in self.users:
            return {"success": False, "error": "Assigned user does not exist."}

        # Update the card fields if provided
        if title is not None:
            card["title"] = title
        if description is not None:
            card["description"] = description
        if assigned_user_id is not None:
            card["assigned_user_id"] = assigned_user_id

        self.cards[card_id] = card  # Save changes

        return {"success": True, "message": "Card details updated."}

    def reorder_cards_in_column(self, column_id: str) -> dict:
        """
        Reassigns positions for all cards in the specified column to ensure they are unique and sequential
        (starting at 1, no gaps), resolving any duplicates or gaps after card moves.

        Args:
            column_id (str): The ID of the column to reorder cards in.

        Returns:
            dict: {
                "success": True,
                "message": f"Cards in column {column_id} reordered successfully"
            }
            or
            {
                "success": False,
                "error": "Reason description"
            }

        Constraints:
            - The column_id must exist.
            - All cards in the column will be assigned new positions (1, 2, ..., N) by current sort order.
        """
        if column_id not in self.columns:
            return { "success": False, "error": "Column does not exist" }

        # Find all cards in the column
        cards_in_column = [
            card_info for card_info in self.cards.values()
            if card_info["column_id"] == column_id
        ]

        # If there are no cards, it's a valid operation (nothing to do)
        if not cards_in_column:
            return { "success": True, "message": f"No cards to reorder in column {column_id}." }

        # Sort cards by current position, use card_id as secondary for stable ordering
        cards_in_column.sort(key=lambda c: (c["position"], c["card_id"]))

        # Reassign positions sequentially (start from 1)
        for new_pos, card in enumerate(cards_in_column, start=1):
            card["position"] = new_pos
            # Persist the change in the main structure
            self.cards[card["card_id"]] = card

        return { "success": True, "message": f"Cards in column {column_id} reordered successfully" }

    def create_column(self, board_id: str, name: str, position: int) -> dict:
        """
        Add a new column (workflow stage) to a specific board at a given position.

        Args:
            board_id (str): The ID of the board.
            name (str): New column's name.
            position (int): Desired unique position of the column in the board.

        Returns:
            dict: {
                "success": True,
                "message": "Column created",
                "column_id": str  # The new column's ID
            }
            or
            {
                "success": False,
                "error": str  # Error message explaining why creation failed
            }

        Constraints:
            - Board must exist.
            - Position must be unique among all columns in the board.
        """
        # Check if board exists
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist" }

        # Check for unique position within the board
        for col in self.columns.values():
            if col["board_id"] == board_id and col["position"] == position:
                return { "success": False, "error": "Position already used by another column in this board" }

        # Generate unique column_id
        column_id = str(uuid.uuid4())

        # Create the column entry
        column_info = {
            "column_id": column_id,
            "board_id": board_id,
            "name": name,
            "position": position
        }
        self.columns[column_id] = column_info

        return { "success": True, "message": "Column created", "column_id": column_id }

    def delete_column(self, column_id: str) -> dict:
        """
        Remove a column from a board.
        Appropriately handles any cards remaining in the column (deletes them).
        After removal, maintains column positions uniqueness within the board.

        Args:
            column_id (str): The unique identifier of the column to delete.

        Returns:
            dict: 
              - { "success": True, "message": "Column <column_id> deleted and <N> cards handled." }
              - { "success": False, "error": "<reason>" }

        Constraints:
            - If the column does not exist, returns error.
            - All cards in the column are also deleted.
            - Column positions remain unique/sequential within the board.
        """
        # Check if column exists
        column_info = self.columns.get(column_id)
        if column_info is None:
            return {"success": False, "error": "Column not found."}

        board_id = column_info["board_id"]

        # Find all cards in this column
        cards_to_delete = [card_id for card_id, card_info in self.cards.items()
                           if card_info["column_id"] == column_id]
        num_cards = len(cards_to_delete)
        for card_id in cards_to_delete:
            del self.cards[card_id]

        # Delete the column
        del self.columns[column_id]

        # Reorder the remaining columns in this board to have sequential and unique positions
        # Fetch columns in the board, sort by their position, reassign sequential positions starting from 1
        remaining_columns = [
            (col_id, col_info) for col_id, col_info in self.columns.items()
            if col_info["board_id"] == board_id
        ]
        # Sort by current position
        remaining_columns.sort(key=lambda x: x[1]["position"])
        # Re-assign positions
        for idx, (col_id, col_info) in enumerate(remaining_columns, start=1):
            col_info["position"] = idx
            self.columns[col_id] = col_info

        return {
            "success": True,
            "message": f"Column {column_id} deleted and {num_cards} cards handled."
        }

    def reorder_columns_in_board(self, board_id: str) -> dict:
        """
        Reassigns positions for all columns in the specified board to ensure unique, sequential ordering
        after insertions or moves.

        Args:
            board_id (str): The ID of the board whose columns are to be reordered.

        Returns:
            dict: {
              "success": True,
              "message": "Columns in board {board_id} reordered successfully."
            }
            OR
            {
              "success": False,
              "error": "Board not found"
            }

        Constraints:
            - Column positions are made unique and sequential (0, 1, 2, ...) within the board.
            - If the board does not exist, return error.
        """
        if board_id not in self.boards:
            return {"success": False, "error": "Board not found"}

        # Gather all columns for this board
        columns_in_board = [
            c for c in self.columns.values() if c['board_id'] == board_id
        ]

        # Sort by current position (and column_id for determinism in case of ties)
        columns_in_board.sort(key=lambda c: (c['position'], c['column_id']))

        # Reassign positions to 0, 1, 2, ... in sorted order
        for idx, column in enumerate(columns_in_board):
            if column['position'] != idx:
                column['position'] = idx
                self.columns[column['column_id']]['position'] = idx

        return {
            "success": True,
            "message": f"Columns in board {board_id} reordered successfully."
        }

    def assign_user_to_card(self, card_id: str, user_id: str) -> dict:
        """
        Set or change the assigned_user_id for a specified card.

        Args:
            card_id (str): The ID of the card to modify.
            user_id (str): The ID of the user to assign to the card.

        Returns:
            dict: Success with message, or failure with error explanation.
                Example:
                    { "success": True, "message": "User assigned to card successfully." }
                    { "success": False, "error": "Card does not exist." }
                    { "success": False, "error": "User does not exist." }

        Constraints:
            - The card must exist.
            - The user must exist.
            - Updates card's 'assigned_user_id' to the new user.
        """
        if card_id not in self.cards:
            return { "success": False, "error": "Card does not exist." }
        if user_id != "" and user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        self.cards[card_id]["assigned_user_id"] = user_id
        return { "success": True, "message": "User assigned to card successfully." }

    def create_board(self, board_id: str, name: str, description: str, owner_user_id: str) -> dict:
        """
        Add a new board with the given owner.

        Args:
            board_id (str): Unique identifier for the new board.
            name (str): Name of the board.
            description (str): Description of the board.
            owner_user_id (str): User ID of the board's owner.

        Returns:
            dict: {
                "success": True,
                "message": "Board created successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The board_id must be unique.
            - The owner_user_id must correspond to an existing user.
        """
        if board_id in self.boards:
            return {"success": False, "error": "Board ID already exists."}

        if owner_user_id not in self.users:
            return {"success": False, "error": "Owner user does not exist."}

        self.boards[board_id] = {
            "board_id": board_id,
            "name": name,
            "description": description,
            "owner_user_id": owner_user_id
        }

        return {"success": True, "message": "Board created successfully."}

    def delete_board(self, board_id: str) -> dict:
        """
        Remove an entire board and all associated columns and cards.

        Args:
            board_id (str): The ID of the board to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Board and all associated columns and cards deleted."
            }
            or
            {
                "success": False,
                "error": "Board does not exist."
            }

        Constraints:
            - All columns and cards belonging to the board will also be deleted.
            - No error is raised for columns/cards if none exist.
        """
        # Check if board exists
        if board_id not in self.boards:
            return { "success": False, "error": "Board does not exist." }

        # Delete columns belonging to this board
        columns_to_delete = [col_id for col_id, col in self.columns.items() if col["board_id"] == board_id]
        for col_id in columns_to_delete:
            del self.columns[col_id]

        # Delete cards belonging to this board
        cards_to_delete = [card_id for card_id, card in self.cards.items() if card["board_id"] == board_id]
        for card_id in cards_to_delete:
            del self.cards[card_id]

        # Delete the board itself
        del self.boards[board_id]

        return { "success": True, "message": "Board and all associated columns and cards deleted." }


class KanbanBoardProjectManagementSystem(BaseEnv):
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
        if not hasattr(env, "feature_flags") or not isinstance(env.feature_flags, dict):
            env.feature_flags = {}
        for key, value in init_config.items():
            current = getattr(env, key, None)
            if callable(current) and not callable(value):
                env.feature_flags[key] = copy.deepcopy(value)
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

    def get_board_by_id(self, **kwargs):
        return self._call_inner_tool('get_board_by_id', kwargs)

    def list_boards_by_user(self, **kwargs):
        return self._call_inner_tool('list_boards_by_user', kwargs)

    def get_column_by_id(self, **kwargs):
        return self._call_inner_tool('get_column_by_id', kwargs)

    def list_columns_by_board(self, **kwargs):
        return self._call_inner_tool('list_columns_by_board', kwargs)

    def get_card_by_id(self, **kwargs):
        return self._call_inner_tool('get_card_by_id', kwargs)

    def list_cards_by_column(self, **kwargs):
        return self._call_inner_tool('list_cards_by_column', kwargs)

    def list_cards_by_board(self, **kwargs):
        return self._call_inner_tool('list_cards_by_board', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_authorization_for_card_action(self, **kwargs):
        return self._call_inner_tool('check_user_authorization_for_card_action', kwargs)

    def validate_column_in_board(self, **kwargs):
        return self._call_inner_tool('validate_column_in_board', kwargs)

    def validate_card_in_column_and_board(self, **kwargs):
        return self._call_inner_tool('validate_card_in_column_and_board', kwargs)

    def get_next_card_position_in_column(self, **kwargs):
        return self._call_inner_tool('get_next_card_position_in_column', kwargs)

    def get_column_position_in_board(self, **kwargs):
        return self._call_inner_tool('get_column_position_in_board', kwargs)

    def list_users_by_board(self, **kwargs):
        return self._call_inner_tool('list_users_by_board', kwargs)

    def move_card_to_column(self, **kwargs):
        return self._call_inner_tool('move_card_to_column', kwargs)

    def update_card_position_in_column(self, **kwargs):
        return self._call_inner_tool('update_card_position_in_column', kwargs)

    def trigger_card_status_update_on_move(self, **kwargs):
        return self._call_inner_tool('trigger_card_status_update_on_move', kwargs)

    def notify_users_on_card_movement(self, **kwargs):
        return self._call_inner_tool('notify_users_on_card_movement', kwargs)

    def create_card(self, **kwargs):
        return self._call_inner_tool('create_card', kwargs)

    def delete_card(self, **kwargs):
        return self._call_inner_tool('delete_card', kwargs)

    def update_card_details(self, **kwargs):
        return self._call_inner_tool('update_card_details', kwargs)

    def reorder_cards_in_column(self, **kwargs):
        return self._call_inner_tool('reorder_cards_in_column', kwargs)

    def create_column(self, **kwargs):
        return self._call_inner_tool('create_column', kwargs)

    def delete_column(self, **kwargs):
        return self._call_inner_tool('delete_column', kwargs)

    def reorder_columns_in_board(self, **kwargs):
        return self._call_inner_tool('reorder_columns_in_board', kwargs)

    def assign_user_to_card(self, **kwargs):
        return self._call_inner_tool('assign_user_to_card', kwargs)

    def create_board(self, **kwargs):
        return self._call_inner_tool('create_board', kwargs)

    def delete_board(self, **kwargs):
        return self._call_inner_tool('delete_board', kwargs)
