# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import uuid



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    account_sta: str  # possibly 'account_status'

class WatchlistInfo(TypedDict):
    watchlist_id: str
    user_id: str
    name: str
    notification_preferences: str   # format validation required
    callback_hook: str              # format validation required

class FinancialInstrumentInfo(TypedDict):
    instrument_id: str
    symbol: str
    name: str
    type: str
    mark: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Watchlists: {watchlist_id: WatchlistInfo}
        self.watchlists: Dict[str, WatchlistInfo] = {}

        # Watchlist Instruments: {watchlist_id: [instrument_id, ...]}
        self.watchlist_instruments: Dict[str, List[str]] = {}

        # Financial Instruments: {instrument_id: FinancialInstrumentInfo}
        self.financial_instruments: Dict[str, FinancialInstrumentInfo] = {}

        # Constraints:
        # - Each watchlist name must be unique per user.
        # - Each watchlist's callback_hook must be unique per user.
        # - A user can have multiple watchlists, each containing multiple financial instruments.
        # - callback_hook and notification_preferences must conform to system-supported formats.
        # - Only authenticated users can access or modify their own watchlists.

        self.authenticated_user_id: Optional[str] = None  # for authentication handling

    def get_authenticated_user(self) -> dict:
        """
        Retrieve information about the currently authenticated user.
    
        Args:
            None (uses self.authenticated_user_id)
        
        Returns:
            dict: 
                {
                    "success": True,
                    "data": UserInfo  # User information if authenticated
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason (not authenticated or user not found)
                }
        Constraints:
            - Only works if there is a currently authenticated user.
            - User must exist in self.users.
        """
        user_id = self.authenticated_user_id
        if user_id is None:
            return { "success": False, "error": "No user is currently authenticated" }
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "Authenticated user not found" }
        return { "success": True, "data": user_info }

    def list_user_watchlists(self) -> dict:
        """
        Retrieve all watchlists belonging to the currently authenticated user.

        Returns:
            dict: {
                "success": True,
                "data": List[WatchlistInfo],  # All user watchlists; empty list if none exist
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., not authenticated
            }

        Constraints:
            - Only the authenticated user's watchlists are returned.
            - Authentication required.
        """
        user_id = self.authenticated_user_id
        if user_id is None:
            return {
                "success": False,
                "error": "No authenticated user. Please authenticate before querying watchlists."
            }

        watchlists = [
            w for w in self.watchlists.values() 
            if w["user_id"] == user_id
        ]

        return {
            "success": True,
            "data": watchlists
        }

    def get_watchlist_by_id(self, watchlist_id: str) -> dict:
        """
        Fetch full details for a given watchlist_id (ownership and authentication enforced).

        Args:
            watchlist_id (str): The unique ID of the watchlist.

        Returns:
            dict: {
                "success": True,
                "data": WatchlistInfo
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - Only authenticated users can access their own watchlists.
            - Watchlist must exist for the provided ID.
        """
        # Check authentication
        if self.authenticated_user_id is None:
            return {"success": False, "error": "User not authenticated"}

        watchlist = self.watchlists.get(watchlist_id)
        if watchlist is None:
            return {"success": False, "error": "Watchlist not found"}

        if watchlist["user_id"] != self.authenticated_user_id:
            return {"success": False, "error": "Permission denied: watchlist does not belong to authenticated user"}

        return {"success": True, "data": watchlist}

    def get_watchlist_by_name(self, watchlist_name: str) -> dict:
        """
        Fetches the authenticated user's watchlist metadata by its name.

        Args:
            watchlist_name (str): Name of the watchlist to retrieve (must belong to the authenticated user).

        Returns:
            dict: {
                "success": True,
                "data": WatchlistInfo  # The watchlist's metadata
            }
            OR
            {
                "success": False,
                "error": str  # Explanation (not authenticated, not found, etc)
            }

        Constraints:
            - Only authenticated users can fetch their own watchlists.
            - Name lookup is case-sensitive and must be unique per user.
        """
        user_id = self.authenticated_user_id
        if not user_id:
            return { "success": False, "error": "User not authenticated" }
        for watchlist in self.watchlists.values():
            if watchlist["user_id"] == user_id and watchlist["name"] == watchlist_name:
                return { "success": True, "data": watchlist }
        return { "success": False, "error": f"Watchlist '{watchlist_name}' not found for user." }

    def get_watchlist_callbacks(self) -> dict:
        """
        List the callback_hook values of all watchlists for the authenticated user.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": List[str] }
                    # a list of callback_hook values (may be empty if no watchlists)
                On failure:
                    { "success": False, "error": str }
                    # e.g., "User not authenticated"

        Constraints:
            - Only the authenticated user's own watchlists are queried.
            - If the user has no watchlists, the data list is empty.
        """
        user_id = self.authenticated_user_id
        if not user_id or user_id not in self.users:
            return {"success": False, "error": "User not authenticated"}

        result = [
            watchlist["callback_hook"]
            for watchlist in self.watchlists.values()
            if watchlist["user_id"] == user_id
        ]
        return {"success": True, "data": result}

    def check_callback_uniqueness(self) -> dict:
        """
        Check if callback_hooks are unique across all watchlists of the authenticated user.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "unique": True           # If no duplicates
                }
            }
            or
            {
                "success": True,
                "data": {
                    "unique": False,
                    "duplicates": [str, ...] # List of duplicated callback_hook values
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g. user not authenticated
            }
        
        Constraints:
            - There must be an authenticated user.
            - Only that user's watchlists are checked.
            - All callback_hook values, including empty or None, are considered for uniqueness.
        """
        user_id = self.authenticated_user_id
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User not authenticated" }
    
        # Gather callback_hooks for this user
        hooks = []
        for wl in self.watchlists.values():
            if wl["user_id"] == user_id:
                hooks.append(wl["callback_hook"])
    
        seen = set()
        duplicates = set()
        for hook in hooks:
            if hook in seen:
                duplicates.add(hook)
            else:
                seen.add(hook)
    
        if not duplicates:
            return { "success": True, "data": { "unique": True } }
        else:
            return { "success": True, "data": { "unique": False, "duplicates": list(duplicates) } }

    def get_watchlist_notification_preferences(self) -> dict:
        """
        Retrieve the notification_preferences for each watchlist belonging to the currently authenticated user.

        Returns:
            dict: {
                "success": True,
                "data": List[{"watchlist_id": str, "name": str, "notification_preferences": str}]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only for authenticated user (self.authenticated_user_id must be set).
            - Only returns user's own watchlists.
            - If user has no watchlists, returns empty list on success.
        """
        user_id = self.authenticated_user_id
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "No authenticated user." }

        results = []
        for w in self.watchlists.values():
            if w["user_id"] == user_id:
                results.append({
                    "watchlist_id": w["watchlist_id"],
                    "name": w["name"],
                    "notification_preferences": w["notification_preferences"]
                })
        return { "success": True, "data": results }

    def list_watchlist_instruments(self, watchlist_id: str) -> dict:
        """
        List all instruments (with their info) contained in a specified watchlist.

        Args:
            watchlist_id (str): The ID of the watchlist whose instruments are to be listed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": [FinancialInstrumentInfo, ...]  # Instruments in the watchlist (may be empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., not authenticated, not found, no permission)
                    }

        Constraints:
            - Only the authenticated user can access their own watchlists.
            - Instruments that are no longer valid in the platform will be skipped.
        """
        if not self.authenticated_user_id:
            return {"success": False, "error": "User is not authenticated."}

        watchlist_info = self.watchlists.get(watchlist_id)
        if not watchlist_info:
            return {"success": False, "error": "Watchlist not found."}

        if watchlist_info["user_id"] != self.authenticated_user_id:
            return {"success": False, "error": "Permission denied: Watchlist does not belong to the authenticated user."}

        instrument_ids = self.watchlist_instruments.get(watchlist_id, [])
        result = []
        for instrument_id in instrument_ids:
            finfo = self.financial_instruments.get(instrument_id)
            if finfo:
                result.append(finfo)

        return {"success": True, "data": result}

    def get_financial_instrument_by_id(self, instrument_id: str) -> dict:
        """
        Retrieve details of a financial instrument by its instrument_id.

        Args:
            instrument_id (str): The unique ID of the financial instrument.

        Returns:
            dict: {
                "success": True,
                "data": FinancialInstrumentInfo
            }
            or
            {
                "success": False,
                "error": str  # If no instrument exists with the given ID
            }

        Constraints:
            - instrument_id must exist in the system.
        """
        fi = self.financial_instruments.get(instrument_id)
        if fi is None:
            return { "success": False, "error": "Financial instrument not found" }
        return { "success": True, "data": fi }

    def update_watchlist_callback_hook(self, watchlist_id: str, new_callback_hook: str) -> dict:
        """
        Update the callback_hook for a specific watchlist.
    
        Args:
            watchlist_id (str): The unique identifier for the target watchlist.
            new_callback_hook (str): The new callback_hook value to be set.

        Returns:
            dict: 
                On success: { "success": True, "message": "Callback hook updated successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - User must be authenticated and must own the watchlist.
            - callback_hook must be unique per user.
            - callback_hook must conform to system-supported format (here: non-empty string, possibly further validation).
        """
        user_id = self.authenticated_user_id
        if not user_id:
            return { "success": False, "error": "User not authenticated." }

        if watchlist_id not in self.watchlists:
            return { "success": False, "error": "Watchlist does not exist." }

        watchlist = self.watchlists[watchlist_id]
        if watchlist['user_id'] != user_id:
            return { "success": False, "error": "Permission denied. Cannot modify another user's watchlist." }

        # Format validation for new_callback_hook (simple placeholder: non-empty string; extend as needed)
        if not isinstance(new_callback_hook, str) or not new_callback_hook.strip():
            return { "success": False, "error": "Invalid callback_hook format." }

        # Uniqueness check among this user's watchlists, excluding the current watchlist
        for wl in self.watchlists.values():
            if wl['user_id'] == user_id and wl['watchlist_id'] != watchlist_id:
                if wl.get('callback_hook', None) == new_callback_hook:
                    return { "success": False, "error": "Callback hook must be unique per user." }
    
        # Update the callback_hook & (optionally) update 'modified' timestamp in a real implementation
        watchlist['callback_hook'] = new_callback_hook
        self.watchlists[watchlist_id] = watchlist  # Update dict

        return { "success": True, "message": "Callback hook updated successfully." }

    def update_watchlist_notification_preferences(self, watchlist_id: str, notification_preferences: str) -> dict:
        """
        Change the notification_preferences for a watchlist.

        Args:
            watchlist_id (str): The identifier for the watchlist to update.
            notification_preferences (str): The new notification preferences value.
                                           Must conform to supported format (here: non-empty string as a placeholder).

        Returns:
            dict: On success:
                     {
                         "success": True,
                         "message": "Notification preferences updated."
                     }
                  On failure:
                     {
                         "success": False,
                         "error": <reason>
                     }

        Constraints:
            - Only authenticated users can modify their own watchlists.
            - notification_preferences must pass format validation.
        """
        # Ensure user authenticated
        auth_user_id = self.authenticated_user_id
        if not auth_user_id:
            return { "success": False, "error": "Authentication required." }

        # Watchlist must exist
        watchlist = self.watchlists.get(watchlist_id)
        if not watchlist:
            return { "success": False, "error": "Watchlist does not exist." }

        # Must be owned by authenticated user
        if watchlist["user_id"] != auth_user_id:
            return { "success": False, "error": "Permission denied: Cannot modify others' watchlists." }

        # Validate notification_preferences (placeholder: must be a non-empty string)
        if not isinstance(notification_preferences, str) or not notification_preferences.strip():
            return { "success": False, "error": "Invalid notification_preferences format." }

        # Passed checks - update
        self.watchlists[watchlist_id]["notification_preferences"] = notification_preferences.strip()
        return { "success": True, "message": "Notification preferences updated." }

    def create_new_watchlist(self, name: str, notification_preferences: str, callback_hook: str) -> dict:
        """
        Add a new watchlist for the authenticated user (enforcing unique name and unique callback_hook per user).

        Args:
            name (str): Desired name of the watchlist (must be unique for this user)
            notification_preferences (str): Preferences for notifications (must be non-empty)
            callback_hook (str): Callback hook identifier/URL (must be unique for this user and non-empty)

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Watchlist '<name>' created successfully.",
                    "watchlist_id": <id>
                }
                Failure: {
                    "success": False,
                    "error": <reason>
                }
        Constraints:
            - Only authenticated users can create watchlists.
            - Watchlist name and callback_hook must each be unique per user.
            - notification_preferences and callback_hook must be non-empty strings (further format checks can be added).
        """
        user_id = self.authenticated_user_id
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "No authenticated user." }
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Watchlist name must be a non-empty string." }
        if not isinstance(notification_preferences, str) or not notification_preferences.strip():
            return { "success": False, "error": "Notification preferences must be a non-empty string." }
        if not isinstance(callback_hook, str) or not callback_hook.strip():
            return { "success": False, "error": "Callback hook must be a non-empty string." }    

        # Name uniqueness per user
        for w in self.watchlists.values():
            if w["user_id"] == user_id and w["name"].lower() == name.lower():
                return { "success": False, "error": "Watchlist name already exists for this user." }
            if w["user_id"] == user_id and w["callback_hook"] == callback_hook:
                return { "success": False, "error": "Callback hook already exists for another watchlist for this user." }

        watchlist_id = str(uuid.uuid4())
        new_watchlist: WatchlistInfo = {
            "watchlist_id": watchlist_id,
            "user_id": user_id,
            "name": name,
            "notification_preferences": notification_preferences,
            "callback_hook": callback_hook
        }
        self.watchlists[watchlist_id] = new_watchlist
        self.watchlist_instruments[watchlist_id] = []  # No instruments initially

        return {
            "success": True,
            "message": f"Watchlist '{name}' created successfully.",
            "watchlist_id": watchlist_id
        }

    def delete_watchlist(self, watchlist_id: str) -> dict:
        """
        Remove a watchlist belonging to the authenticated user.
    
        Args:
            watchlist_id (str): The ID of the watchlist to be deleted.

        Returns:
            dict: 
                On success: { "success": True, "message": "Watchlist deleted successfully." }
                On failure: { "success": False, "error": <error reason> }

        Constraints:
            - Only the authenticated user may delete their own watchlists.
            - Removes associated instrument links as well.
        """
        # Check authentication
        user_id = self.authenticated_user_id
        if user_id is None:
            return { "success": False, "error": "No authenticated user." }
    
        # Validate existence
        watchlist = self.watchlists.get(watchlist_id)
        if watchlist is None:
            return { "success": False, "error": "Watchlist does not exist." }
    
        # Validate ownership
        if watchlist["user_id"] != user_id:
            return { "success": False, "error": "Permission denied: Not your watchlist." }

        # Remove associated instruments
        if watchlist_id in self.watchlist_instruments:
            del self.watchlist_instruments[watchlist_id]
    
        # Remove the watchlist entry
        del self.watchlists[watchlist_id]
    
        return { "success": True, "message": "Watchlist deleted successfully." }

    def add_instrument_to_watchlist(self, watchlist_id: str, instrument_id: str) -> dict:
        """
        Add a financial instrument to the specified watchlist.

        Args:
            watchlist_id (str): The ID of the watchlist.
            instrument_id (str): The ID of the financial instrument to add.

        Returns:
            dict: {
                "success": True,
                "message": "Instrument added to watchlist."
            }
            or
            {
                "success": False,
                "error": str  # Description of failure reason
            }

        Constraints:
            - Only authenticated users can modify their own watchlists.
            - Both watchlist and instrument must exist.
            - An instrument can only be added once to each watchlist.
        """
        # Check authentication
        if not self.authenticated_user_id:
            return { "success": False, "error": "User not authenticated" }

        # Check watchlist existence and ownership
        wl = self.watchlists.get(watchlist_id)
        if not wl or wl["user_id"] != self.authenticated_user_id:
            return { "success": False, "error": "Watchlist not found or access denied" }

        # Check instrument existence
        if instrument_id not in self.financial_instruments:
            return { "success": False, "error": "Instrument not found" }

        # Check if instrument already in the watchlist
        wl_instruments = self.watchlist_instruments.setdefault(watchlist_id, [])
        if instrument_id in wl_instruments:
            return { "success": False, "error": "Instrument already in watchlist" }

        # Add instrument to watchlist
        wl_instruments.append(instrument_id)
        self.watchlist_instruments[watchlist_id] = wl_instruments

        return { "success": True, "message": "Instrument added to watchlist." }

    def remove_instrument_from_watchlist(self, watchlist_id: str, instrument_id: str) -> dict:
        """
        Remove a financial instrument from one of the authenticated user's watchlists.

        Args:
            watchlist_id (str): The unique ID of the watchlist to update.
            instrument_id (str): The unique ID of the instrument to remove.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Instrument <instrument_id> removed from watchlist <watchlist_id>" }
              - On failure: { "success": False, "error": str }

        Constraints:
            - Only the authenticated user can modify their own watchlists.
            - Instrument must actually be present in the watchlist.
        """
        # Authentication check
        if not self.authenticated_user_id:
            return {"success": False, "error": "User not authenticated"}

        # Watchlist existence and ownership check
        watchlist = self.watchlists.get(watchlist_id)
        if not watchlist:
            return {"success": False, "error": "Watchlist does not exist"}
        if watchlist["user_id"] != self.authenticated_user_id:
            return {"success": False, "error": "Permission denied: Cannot modify another user's watchlist"}

        # Watchlist contents check
        instrument_list = self.watchlist_instruments.get(watchlist_id, [])
        if instrument_id not in instrument_list:
            return {"success": False, "error": "Instrument not present in the watchlist"}

        # Remove the instrument
        instrument_list.remove(instrument_id)
        self.watchlist_instruments[watchlist_id] = instrument_list

        return {
            "success": True,
            "message": f"Instrument {instrument_id} removed from watchlist {watchlist_id}"
        }

    def set_authenticated_user(self, user_id: str) -> dict:
        """
        Authenticate a user in the system, setting them as the current context for
        subsequent user-specific operations.

        Args:
            user_id (str): The ID of the user to authenticate as.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "User set as authenticated"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - Only existing users can be set as authenticated.
            - The authenticated user determines access/authorization for all operations.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        self.authenticated_user_id = user_id
        return { "success": True, "message": "User set as authenticated" }

    def bulk_update_callback_hooks(self, updates: Dict[str, str]) -> dict:
        """
        Batch update callback_hooks for multiple watchlists to guarantee per-user uniqueness.

        Args:
            updates (Dict[str, str]): Mapping from watchlist_id to new callback_hook value.

        Returns:
            dict:
                success: True and success message, or False and error description.

        Constraints:
            - Authenticated user only allowed to modify their own watchlists.
            - All callback_hooks for a user must be unique after update (including not-updated watchlists).
            - Each callback_hook must conform to the system-supported format.
            - The operation is all-or-nothing: no update is applied if any error detected.

        Edge cases:
            - If updates dict is empty, return success.

        """
        # Check authentication
        user_id = self.authenticated_user_id
        if not user_id:
            return {"success": False, "error": "User not authenticated"}

        if not updates:
            return {"success": True, "message": "No updates provided"}

        # 1. Validate: Watchlists exist and belong to user
        user_watchlists = {
            wid: w for wid, w in self.watchlists.items() if w['user_id'] == user_id
        }

        # 2. Validate that all provided watchlist_ids exist and belong to user
        for wid in updates:
            if wid not in user_watchlists:
                return {
                    "success": False,
                    "error": f"Watchlist '{wid}' does not exist or not owned by user"
                }

        # 3. Prepare future callback_hook set
        # Gather all watchlists for user and their current callback_hooks
        current_hooks = {}
        for wid, w in user_watchlists.items():
            current_hooks[wid] = w["callback_hook"]

        # What would be the new hooks after updates?
        future_hooks = {}
        for wid in user_watchlists:
            future_hooks[wid] = updates.get(wid, current_hooks[wid])

        # 4. Validate: All callback_hooks must be unique in future set
        hooks_seen = set()
        for wid, hook in future_hooks.items():
            # Format validation (simple: must be non-empty string; more can be added as needed)
            if not isinstance(hook, str) or not hook.strip():
                return {
                    "success": False,
                    "error": f"Callback_hook for '{wid}' is not a valid non-empty string"
                }
            if hook in hooks_seen:
                return {
                    "success": False,
                    "error": (
                        f"Duplicate callback_hook '{hook}' would result for user,"
                        " which is not allowed"
                    )
                }
            hooks_seen.add(hook)

        # 5. If all is valid, update all in one go
        for wid, new_hook in updates.items():
            self.watchlists[wid]['callback_hook'] = new_hook

        return {
            "success": True,
            "message": f"Batch callback_hook updated for {len(updates)} watchlist(s)"
        }

    def rename_watchlist(self, watchlist_id: str, new_name: str) -> dict:
        """
        Change the name of a user's watchlist, ensuring the new name is unique per user.

        Args:
            watchlist_id (str): The ID of the watchlist to rename.
            new_name (str): The new unique name for the watchlist.

        Returns:
            dict: {
                "success": True,
                "message": str  # success confirmation
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only authenticated users can modify their own watchlists.
            - The new name must be unique among the user's watchlists.
            - The new name must not be empty or just whitespace.
        """
        # Authentication
        user_id = self.authenticated_user_id
        if not user_id:
            return { "success": False, "error": "User not authenticated" }

        # Watchlist existence and ownership check
        watchlist = self.watchlists.get(watchlist_id)
        if not watchlist:
            return { "success": False, "error": "Watchlist does not exist" }
        if watchlist["user_id"] != user_id:
            return { "success": False, "error": "Permission denied: not owner of watchlist" }

        # Name validation
        if not isinstance(new_name, str) or not new_name.strip():
            return { "success": False, "error": "Watchlist name cannot be empty or whitespace" }
        new_name = new_name.strip()

        # Name uniqueness constraint (per user)
        for w in self.watchlists.values():
            if w["user_id"] == user_id and w["name"] == new_name and w["watchlist_id"] != watchlist_id:
                return { "success": False, "error": "Watchlist name must be unique per user" }

        # Rename
        watchlist["name"] = new_name

        return {
            "success": True,
            "message": f"Watchlist {watchlist_id} renamed to '{new_name}'"
        }


class FinancialWatchlistManagementSystem(BaseEnv):
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

    def get_authenticated_user(self, **kwargs):
        return self._call_inner_tool('get_authenticated_user', kwargs)

    def list_user_watchlists(self, **kwargs):
        return self._call_inner_tool('list_user_watchlists', kwargs)

    def get_watchlist_by_id(self, **kwargs):
        return self._call_inner_tool('get_watchlist_by_id', kwargs)

    def get_watchlist_by_name(self, **kwargs):
        return self._call_inner_tool('get_watchlist_by_name', kwargs)

    def get_watchlist_callbacks(self, **kwargs):
        return self._call_inner_tool('get_watchlist_callbacks', kwargs)

    def check_callback_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_callback_uniqueness', kwargs)

    def get_watchlist_notification_preferences(self, **kwargs):
        return self._call_inner_tool('get_watchlist_notification_preferences', kwargs)

    def list_watchlist_instruments(self, **kwargs):
        return self._call_inner_tool('list_watchlist_instruments', kwargs)

    def get_financial_instrument_by_id(self, **kwargs):
        return self._call_inner_tool('get_financial_instrument_by_id', kwargs)

    def update_watchlist_callback_hook(self, **kwargs):
        return self._call_inner_tool('update_watchlist_callback_hook', kwargs)

    def update_watchlist_notification_preferences(self, **kwargs):
        return self._call_inner_tool('update_watchlist_notification_preferences', kwargs)

    def create_new_watchlist(self, **kwargs):
        return self._call_inner_tool('create_new_watchlist', kwargs)

    def delete_watchlist(self, **kwargs):
        return self._call_inner_tool('delete_watchlist', kwargs)

    def add_instrument_to_watchlist(self, **kwargs):
        return self._call_inner_tool('add_instrument_to_watchlist', kwargs)

    def remove_instrument_from_watchlist(self, **kwargs):
        return self._call_inner_tool('remove_instrument_from_watchlist', kwargs)

    def set_authenticated_user(self, **kwargs):
        return self._call_inner_tool('set_authenticated_user', kwargs)

    def bulk_update_callback_hooks(self, **kwargs):
        return self._call_inner_tool('bulk_update_callback_hooks', kwargs)

    def rename_watchlist(self, **kwargs):
        return self._call_inner_tool('rename_watchlist', kwargs)

