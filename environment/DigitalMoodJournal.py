# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class UserInfo(TypedDict):
    _id: str           # Unique user identifier
    name: str
    account_sta: str   # Presumed to represent account status

class JournalEntryInfo(TypedDict, total=False):
    ntry_id: str
    user_id: str
    date: str
    mood_rating: int
    stress_level: int
    no: Optional[str]  # Optional note

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Digital mood tracking journal environment.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Maps to entity "User" with attributes: _id, name, account_sta

        # Journal Entries: {ntry_id: JournalEntryInfo}
        self.journal_entries: Dict[str, JournalEntryInfo] = {}
        # Maps to entity "JournalEntr" with attributes: ntry_id, user_id, date, mood_rating, stress_level, no

        # Constraints to enforce in logic:
        # - Each user can have at most one journal entry per date.
        # - Mood rating and stress level must be within an allowed range (e.g., 1–10).
        # - Journal entries must be associated with a valid user.

    def _get_user_record(self, user_id: str) -> Optional[UserInfo]:
        user = self.users.get(user_id)
        if user is not None:
            return user
        for candidate in self.users.values():
            if candidate.get("_id") == user_id:
                return candidate
        return None

    def _canonical_user_id(self, user_id: str) -> Optional[str]:
        user = self._get_user_record(user_id)
        if user is None:
            return None
        return user.get("_id")

    def _get_entry_record(self, ntry_id: str) -> Optional[JournalEntryInfo]:
        entry = self.journal_entries.get(ntry_id)
        if entry is not None:
            return entry
        for candidate in self.journal_entries.values():
            if candidate.get("ntry_id") == ntry_id:
                return candidate
        return None

    def _get_entry_storage_key(self, ntry_id: str) -> Optional[str]:
        if ntry_id in self.journal_entries:
            return ntry_id
        for key, candidate in self.journal_entries.items():
            if candidate.get("ntry_id") == ntry_id:
                return key
        return None

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by exact name match.

        Args:
            name (str): The user's name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of matching user info dicts
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. no user found with name
            }

        Constraints:
            - User names are not necessarily unique; may return multiple users for same name.
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        if not matches:
            return { "success": False, "error": "No user found with the specified name" }
        return { "success": True, "data": matches }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user profile information by unique user ID.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": UserInfo }
                - On failure:
                    { "success": False, "error": "User not found" }

        Constraints:
            - User ID must exist in the system.
        """
        user = self._get_user_record(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_journal_entries_for_user(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        List all journal entries for a given user, optionally filtered by a date range.

        Args:
            user_id (str): The user's unique identifier.
            start_date (Optional[str]): Start date (inclusive) in 'YYYY-MM-DD' format.
            end_date (Optional[str]): End date (inclusive) in 'YYYY-MM-DD' format.

        Returns:
            dict: {
                "success": True,
                "data": List[JournalEntryInfo],  # All (filtered) entries for the user
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - User must exist.
            - Filtering only includes entries with dates >= start_date and <= end_date if those are given.
        """
        canonical_user_id = self._canonical_user_id(user_id)
        if canonical_user_id is None:
            return { "success": False, "error": "User not found" }

        # Filtering function
        def entry_in_date_range(entry):
            date = entry.get("date")
            if start_date and date < start_date:
                return False
            if end_date and date > end_date:
                return False
            return True

        result = [
            entry for entry in self.journal_entries.values()
            if entry.get("user_id") == canonical_user_id and entry_in_date_range(entry)
        ]

        return { "success": True, "data": result }

    def get_journal_entry_by_date(self, user_id: str, date: str) -> dict:
        """
        Retrieve a user's journal entry for a specific date, if it exists.

        Args:
            user_id (str): Unique identifier of the user.
            date (str): The date (string, e.g. 'YYYY-MM-DD') to retrieve the entry for.

        Returns:
            dict:
                - If success: { "success": True, "data": JournalEntryInfo }
                - If failure: { "success": False, "error": str }

        Constraints:
            - Journal entries must be linked to an existing user.
            - Each user can have at most one journal entry per date.
        """
        canonical_user_id = self._canonical_user_id(user_id)
        if canonical_user_id is None:
            return { "success": False, "error": "User does not exist" }

        for entry in self.journal_entries.values():
            if entry.get("user_id") == canonical_user_id and entry.get("date") == date:
                return { "success": True, "data": entry }

        return { "success": False, "error": "Journal entry not found for user/date" }

    def get_journal_entry_by_id(self, ntry_id: str) -> dict:
        """
        Retrieve a single journal entry by its unique ID.

        Args:
            ntry_id (str): The unique journal entry identifier.

        Returns:
            dict: {
                "success": True,
                "data": JournalEntryInfo  # The journal entry data if found
            }
            or
            {
                "success": False,
                "error": str  # If not found, error description
            }

        Constraints:
            - ntry_id must exist in the journal_entries dictionary.
        """
        entry = self._get_entry_record(ntry_id)
        if entry is None:
            return { "success": False, "error": "Journal entry not found" }
        return { "success": True, "data": entry }

    def create_journal_entry(
        self,
        user_id: str,
        date: str,
        mood_rating: int,
        stress_level: int,
        note: Optional[str] = None
    ) -> dict:
        """
        Add a new journal entry for a user on a specified date, with ratings and optional note.
    
        Args:
            user_id (str): Identifier of the user creating the entry.
            date (str): Date of journal entry (e.g., 'YYYY-MM-DD').
            mood_rating (int): User's mood rating (1–10).
            stress_level (int): User's stress level (1–10).
            note (Optional[str]): Optional note.
        
        Returns:
            dict: 
                Success: { "success": True, "message": "Journal entry created successfully" }
                Error:   { "success": False, "error": <error reason> }
    
        Constraints:
            - user_id must exist.
            - At most one entry per user per date.
            - mood_rating and stress_level must be in [1, 10].
        """
        canonical_user_id = self._canonical_user_id(user_id)
        if canonical_user_id is None:
            return { "success": False, "error": "User does not exist" }

        # Check rating ranges
        if not (1 <= mood_rating <= 10):
            return { "success": False, "error": "Mood rating must be between 1 and 10" }
        if not (1 <= stress_level <= 10):
            return { "success": False, "error": "Stress level must be between 1 and 10" }

        # Check for existing entry by this user/date
        for entry in self.journal_entries.values():
            if entry.get("user_id") == canonical_user_id and entry.get("date") == date:
                return { "success": False, "error": "Journal entry already exists for this user and date" }

        # Generate a unique journal entry ID (simple: combine user_id, date, and a counter if needed)
        base_id = f"{canonical_user_id}_{date}"
        ntry_id = base_id
        counter = 1
        while ntry_id in self.journal_entries:
            ntry_id = f"{base_id}_{counter}"
            counter += 1

        entry_info = {
            "ntry_id": ntry_id,
            "user_id": canonical_user_id,
            "date": date,
            "mood_rating": mood_rating,
            "stress_level": stress_level,
        }
        if note is not None:
            entry_info["no"] = note

        self.journal_entries[ntry_id] = entry_info

        return { "success": True, "message": "Journal entry created successfully" }

    def update_journal_entry(
        self,
        ntry_id: str,
        mood_rating: int = None,
        stress_level: int = None,
        no: str = None,
        note: str = None,
        date: str = None,
    ) -> dict:
        """
        Edit an existing journal entry. Update any/all of mood_rating, stress_level, note, or date.

        Args:
            ntry_id (str): ID of the journal entry to update.
            mood_rating (Optional[int]): New mood rating (must be 1–10).
            stress_level (Optional[int]): New stress level (must be 1–10).
            no (Optional[str]): New note.
            date (Optional[str]): New date (format as existing; must not violate one-per-user-per-date).

        Returns:
            dict: {
                "success": True,
                "message": "Journal entry updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Journal entry must exist.
            - Associated user must exist.
            - Mood rating and stress level must be 1–10 if provided.
            - Only one entry per user per date (cannot set date to one already used by this user).
        """

        if no is None and note is not None:
            no = note

        # Check entry exists
        entry = self._get_entry_record(ntry_id)
        if not entry:
            return { "success": False, "error": "Journal entry not found." }

        user_id = entry["user_id"]
        if self._canonical_user_id(user_id) is None:
            return { "success": False, "error": "Associated user does not exist." }

        # Validate mood_rating
        if mood_rating is not None:
            if not (1 <= mood_rating <= 10):
                return { "success": False, "error": "Mood rating must be between 1 and 10." }

        # Validate stress_level
        if stress_level is not None:
            if not (1 <= stress_level <= 10):
                return { "success": False, "error": "Stress level must be between 1 and 10." }

        # Validate date uniqueness for user (if updating date)
        if date is not None:
            current_date = entry.get("date")
            if date != current_date:
                # Does this user have another entry on the new date?
                for je in self.journal_entries.values():
                    if je["user_id"] == user_id and je.get("date") == date and je.get("ntry_id") != ntry_id:
                        return {
                            "success": False,
                            "error": "User already has a journal entry for that date."
                        }

        # All validations passed, perform update
        if mood_rating is not None:
            entry["mood_rating"] = mood_rating
        if stress_level is not None:
            entry["stress_level"] = stress_level
        if no is not None:
            entry["no"] = no
        if date is not None:
            entry["date"] = date

        return {
            "success": True,
            "message": "Journal entry updated."
        }

    def delete_journal_entry(
        self,
        ntry_id: str = None,
        user_id: str = None,
        date: str = None,
    ) -> dict:
        """
        Remove a user's journal entry, either by entry ID (`ntry_id`) or by (`user_id`, `date`).
        Args:
            ntry_id (str, optional): The journal entry's unique identifier to delete.
            user_id (str, optional): The user's unique id (required if deleting by user/date).
            date (str, optional): The entry's date (required if deleting by user/date).
        Returns:
            dict: {
                "success": True,
                "message": "Journal entry deleted"
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Entry must exist.
            - If using user_id/date, user must exist.
        Notes:
            - If `ntry_id` is provided, deletion uses that.
            - If not, `user_id` and `date` must be provided.
            - If entry not found, returns error.
        """

        # Case 1: Delete by ntry_id
        if ntry_id is not None:
            storage_key = self._get_entry_storage_key(ntry_id)
            if storage_key is None:
                return {"success": False, "error": "Journal entry ID not found"}
            del self.journal_entries[storage_key]
            return {"success": True, "message": "Journal entry deleted by ID"}

        # Case 2: Delete by user_id and date
        if user_id is not None and date is not None:
            canonical_user_id = self._canonical_user_id(user_id)
            if canonical_user_id is None:
                return {"success": False, "error": "User not found"}
            found_id = None
            for eid, entry in self.journal_entries.items():
                if entry.get("user_id") == canonical_user_id and entry.get("date") == date:
                    found_id = eid
                    break
            if found_id is None:
                return {"success": False, "error": "Journal entry for user and date not found"}
            del self.journal_entries[found_id]
            return {"success": True, "message": "Journal entry deleted by user/date"}

        return {"success": False, "error": "Insufficient information to delete journal entry (provide ntry_id or user_id and date)"}


class DigitalMoodJournal(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_journal_entries_for_user(self, **kwargs):
        return self._call_inner_tool('get_journal_entries_for_user', kwargs)

    def get_journal_entry_by_date(self, **kwargs):
        return self._call_inner_tool('get_journal_entry_by_date', kwargs)

    def get_journal_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_journal_entry_by_id', kwargs)

    def create_journal_entry(self, **kwargs):
        return self._call_inner_tool('create_journal_entry', kwargs)

    def update_journal_entry(self, **kwargs):
        return self._call_inner_tool('update_journal_entry', kwargs)

    def delete_journal_entry(self, **kwargs):
        return self._call_inner_tool('delete_journal_entry', kwargs)
