# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class UserInfo(TypedDict):
    _id: str
    username: str
    account_status: str
    registration_da: str  # Assuming 'registration_da' is a string timestamp

class ActivityEventInfo(TypedDict):
    event_id: str
    user_id: str
    event_type: str
    timestamp: float
    event_detail: str  # Could use Union[str, dict] if structure is defined

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for tracking user account activity events.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Activity events: {event_id: ActivityEventInfo}
        self.activity_events: Dict[str, ActivityEventInfo] = {}

        # Per-user ordered event timelines: {user_id: List[event_id]}, timestamps must be ordered
        self.user_events: Dict[str, List[str]] = {}

        self._recognized_event_types = [
            "login",
            "logout",
            "purchase",
            "account update",
        ]

        # Constraints:
        # - Each event must be associated with a valid user_id (user must exist)
        # - Timestamps must be accurate and stored in chronological order
        # - Only predefined event types (e.g., login, logout, purchase, account update) allowed in event_type
        # - Event timelines for a user must be retrievable and ordered by timestamp

    def _refresh_recognized_event_types_from_data(self) -> None:
        observed_types = sorted({
            event.get("event_type")
            for event in self.activity_events.values()
            if isinstance(event, dict) and isinstance(event.get("event_type"), str)
        })
        merged = list(self._recognized_event_types)
        for event_type in observed_types:
            if event_type not in merged:
                merged.append(event_type)
        self._recognized_event_types = merged

    def _get_predefined_event_types(self) -> list[str]:
        self._refresh_recognized_event_types_from_data()
        return list(self._recognized_event_types)

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                If success:
                    {"success": True, "data": UserInfo}
                If failure (user not found):
                    {"success": False, "error": "User not found"}
        Constraints:
            - user_id must exist in the self.users dictionary.
        """
        if not user_id or user_id not in self.users:
            return {"success": False, "error": "User not found"}
    
        return {"success": True, "data": self.users[user_id]}

    def list_all_users(self) -> dict:
        """
        Return a list of all users currently registered in the system.

        Args:
            None

        Returns:
            dict:
                "success": True,
                "data": List[UserInfo]  # All user info dicts (empty if no users)

        Constraints:
            - None (returns all loaded users, empty list if none exist).
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def get_event_timeline_for_user(self, user_id: str) -> dict:
        """
        Retrieve the user's stored event timeline in its current recorded order.

        Args:
            user_id (str): The ID of the user whose activity timeline is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivityEventInfo],  # current stored order (may be empty if no events)
            }
            or
            {
                "success": False,
                "error": str  # description of the error (e.g., user does not exist)
            }

        Constraints:
            - User must exist.
            - Timeline reflects the system's current recorded order for that user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        event_ids = self.user_events.get(user_id, [])
        events = [self.activity_events[eid] for eid in event_ids if eid in self.activity_events]

        return {"success": True, "data": events}

    def get_events_by_type_for_user(self, user_id: str, event_types: list) -> dict:
        """
        Retrieve all activity events for a user of the specified event types, preserving the current stored timeline order.

        Args:
            user_id (str): The user identifier whose events to query.
            event_types (list of str): Allowed event types to filter (e.g., "login", "logout", "purchase", "account update").

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": List[ActivityEventInfo]  # List can be empty if no match
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Error message (user not found, invalid event type, etc.)
                    }

        Constraints:
            - user_id must exist
            - All event_types must be among the system's predefined event types
            - Events are returned in the user's current stored order
        """
        allowed_types = set(self._get_predefined_event_types())

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if not isinstance(event_types, list):
            return {"success": False, "error": "event_types must be a list"}

        if any(et not in allowed_types for et in event_types):
            invalid = [et for et in event_types if et not in allowed_types]
            return {"success": False, "error": f"Invalid event types: {invalid}"}

        event_ids = self.user_events.get(user_id, [])
        matching_events = [
            self.activity_events[event_id]
            for event_id in event_ids
            if self.activity_events[event_id]["event_type"] in event_types
        ]

        return {"success": True, "data": matching_events}

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Fetch details of a particular activity event by its event_id.

        Args:
            event_id (str): Unique identifier for the activity event to fetch.

        Returns:
            dict: {
                "success": True,
                "data": ActivityEventInfo  # The activity event information.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Event not found"
            }

        Constraints:
            - The specified event_id must exist in the activity_events.
        """
        if event_id not in self.activity_events:
            return { "success": False, "error": "Event not found" }
        return { "success": True, "data": self.activity_events[event_id] }

    def list_predefined_event_types(self) -> dict:
        """
        List all event types allowed by the system.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of allowed event types (e.g., ["login", "logout", ...])
            }

        Constraints:
            - Event types are system-defined and not user-dependent.
        """
        allowed_event_types = self._get_predefined_event_types()
        return {
            "success": True,
            "data": allowed_event_types
        }

    def get_user_event_count_by_type(self, user_id: str) -> dict:
        """
        Returns the number of events per event_type for the given user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": {event_type (str): count (int), ...}
            }
            or
            {
                "success": False,
                "error": "User does not exist"
            }

        Constraints:
            - User must exist.
            - Counts only events belonging to the specified user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Use the user_events (timeline) if available for performance/ordering guarantees
        events = []
        if user_id in self.user_events:
            events = [self.activity_events[event_id]
                      for event_id in self.user_events[user_id]
                      if event_id in self.activity_events]
        else:
            # Fallback: get by scanning all events
            events = [
                event for event in self.activity_events.values()
                if event["user_id"] == user_id
            ]

        event_type_counts = {}
        for event in events:
            event_type = event["event_type"]
            if event_type not in event_type_counts:
                event_type_counts[event_type] = 0
            event_type_counts[event_type] += 1

        return { "success": True, "data": event_type_counts }

    def check_user_existence(self, user_id: str) -> dict:
        """
        Validate whether a given user_id exists and is active in the system.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                {
                    "success": True,
                    "exists": bool,  # True if user exists, else False
                    "active": bool   # True if user is active (account_status == "active"), else False
                }
        """
        user = self.users.get(user_id)
        if user is None:
            return {
                "success": True,
                "exists": False,
                "active": False
            }
        return {
            "success": True,
            "exists": True,
            "active": user.get("account_status", "").lower() == "active"
        }

    def add_activity_event(
        self,
        event_id: str,
        user_id: str,
        event_type: str,
        timestamp: float,
        event_detail: str
    ) -> dict:
        """
        Add a new activity event for a user, enforcing association, event type, and uniqueness constraints.

        Args:
            event_id (str): Unique identifier for the activity event.
            user_id (str): User ID associated with the event (must exist).
            event_type (str): Kind of activity ('login', 'logout', 'purchase', 'account update', etc.).
            timestamp (float): Timestamp of the event in seconds since epoch.
            event_detail (str): Additional context/details for this event.

        Returns:
            dict: {
                "success": True,
                "message": "Activity event added for user."
            }
            or
            {
                "success": False,
                "error": <error_message>
            }
        Constraints:
            - user_id must exist in self.users
            - event_id must not already exist in self.activity_events
            - event_type must be one of the predefined allowed types
            - Event added to self.user_events[user_id] and must maintain time order
            - Timestamps of events for a user should remain in chronological order
        """
        PREDEFINED_EVENT_TYPES = set(self._get_predefined_event_types())

        # 1. Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "Invalid user_id: user does not exist"}

        # 2. Check unique event_id
        if event_id in self.activity_events:
            return {"success": False, "error": "Event ID already exists"}

        # 3. Check event_type validity
        if event_type not in PREDEFINED_EVENT_TYPES:
            return {"success": False, "error": f"Invalid event type. Allowed: {sorted(PREDEFINED_EVENT_TYPES)}"}

        # 4. Basic timestamp validity (optional, but recommended)
        if not isinstance(timestamp, (float, int)) or timestamp < 0:
            return {"success": False, "error": "Invalid timestamp"}

        # 5. Construct the event object
        event_info: ActivityEventInfo = {
            "event_id": event_id,
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": float(timestamp),
            "event_detail": event_detail
        }

        # 6. Insert the event into global events registry
        self.activity_events[event_id] = event_info

        # 7. Insert the event into user's timeline in timestamp order (sorted insertion)
        if user_id not in self.user_events:
            self.user_events[user_id] = []

        user_event_ids = self.user_events[user_id]
        # Find insert position to maintain timestamp order
        inserted = False
        for idx, existing_event_id in enumerate(user_event_ids):
            existing_event = self.activity_events[existing_event_id]
            if event_info["timestamp"] < existing_event["timestamp"]:
                user_event_ids.insert(idx, event_id)
                inserted = True
                break
        if not inserted:
            user_event_ids.append(event_id)

        # Ensure user_events[user_id] remains strictly ordered by timestamp
        self.user_events[user_id] = user_event_ids

        return {"success": True, "message": "Activity event added for user."}

    def update_event_timestamp(self, event_id: str, new_timestamp: float) -> dict:
        """
        Modify the timestamp of a given activity event and reorder the user's event timeline if changed.

        Args:
            event_id (str): The unique identifier of the event to update.
            new_timestamp (float): The new timestamp to set for the event.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Event timestamp updated and timeline reordered"
                }
                OR
                {
                    "success": False,
                    "error": "reason"
                }
        Constraints:
            - The event_id must exist.
            - After updating, the user's timeline (user_events[user_id]) must be re-ordered in ascending timestamp order.
        """
        if event_id not in self.activity_events:
            return { "success": False, "error": "Event does not exist" }
    
        event = self.activity_events[event_id]
        old_timestamp = event["timestamp"]
        user_id = event["user_id"]

        # Update event timestamp
        event["timestamp"] = new_timestamp

        # Re-order user's event timeline, if exists
        if user_id not in self.user_events:
            # This should never occur if data integrity has been maintained,
            # but for safety, we return an error if timeline is missing
            return { "success": False, "error": "Event's user timeline missing" }
    
        # Get list of event ids and sort by their (possibly updated) timestamps
        event_ids = self.user_events[user_id]
        # Defensive: make sure all event_ids are in activity_events
        sortable = [
            (eid, self.activity_events[eid]["timestamp"])
            for eid in event_ids if eid in self.activity_events
        ]
        # Sort by timestamp ascending
        sortable.sort(key=lambda x: x[1])
        # Overwrite the timeline in order
        self.user_events[user_id] = [eid for eid, _ in sortable]

        return { "success": True, "message": "Event timestamp updated and timeline reordered" }

    def delete_activity_event(self, event_id: str) -> dict:
        """
        Remove an activity event from the system.

        Args:
            event_id (str): The unique identifier of the activity event to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Event deleted."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The activity event must exist.
            - All references to the event (in per-user timelines) must be removed.
        """
        event = self.activity_events.get(event_id)
        if not event:
            return {"success": False, "error": "Event does not exist."}

        user_id = event.get("user_id")
        if user_id not in self.users:
            return {"success": False, "error": "Associated user does not exist (data corruption)."}

        # Remove event from per-user timeline
        user_event_list = self.user_events.get(user_id, [])
        if event_id in user_event_list:
            user_event_list.remove(event_id)
            self.user_events[user_id] = user_event_list  # Update back in case of direct reference
        # If not present, skip silently (data inconsistency)

        # Remove the event record
        del self.activity_events[event_id]

        return {"success": True, "message": "Event deleted."}

    def edit_event_detail(self, event_id: str, new_event_detail: str) -> dict:
        """
        Update the event_detail field of an existing activity event.

        Args:
            event_id (str): The identifier of the activity event to update.
            new_event_detail (str): The new detail information to be stored for the event.

        Returns:
            dict: 
                {"success": True, "message": "Event detail updated."}
                or
                {"success": False, "error": "Event not found."}
    
        Constraints:
            - event_id must exist in the system.
            - Only event_detail is modified; other fields remain unchanged.
        """
        if event_id not in self.activity_events:
            return {"success": False, "error": "Event not found."}
    
        self.activity_events[event_id]["event_detail"] = new_event_detail
        return {"success": True, "message": "Event detail updated."}

    def bulk_delete_events_for_user(self, user_id: str, event_ids: list[str]) -> dict:
        """
        Remove multiple activity events for a given user.
    
        Args:
            user_id (str): The ID of the user whose events should be deleted.
            event_ids (List[str]): List of event IDs to delete.
    
        Returns:
            dict: {
                "success": True,
                "message": "N events deleted for user <user_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Provided user_id must exist.
            - Each event_id must exist, be associated with user_id, and be present in user's timeline.
            - Events will be deleted from both self.activity_events and self.user_events[user_id].
            - If event_ids is empty, operation succeeds ("0 events deleted for user ...").
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if user_id not in self.user_events:
            return { "success": True, "message": f"0 events deleted for user {user_id}" }

        # Validate all event_ids
        invalid_events = []
        non_user_events = []
        not_in_timeline = []
        for eid in event_ids:
            if eid not in self.activity_events:
                invalid_events.append(eid)
            elif self.activity_events[eid]['user_id'] != user_id:
                non_user_events.append(eid)
            elif eid not in self.user_events[user_id]:
                not_in_timeline.append(eid)

        if invalid_events:
            return { "success": False, "error": f"Event(s) do not exist: {invalid_events}" }
        if non_user_events:
            return { "success": False, "error": f"Event(s) not associated with user {user_id}: {non_user_events}" }
        if not_in_timeline:
            return { "success": False, "error": f"Event(s) not in user's timeline: {not_in_timeline}" }

        # Proceed to delete
        for eid in event_ids:
            del self.activity_events[eid]
            self.user_events[user_id].remove(eid)

        return { "success": True, "message": f"{len(event_ids)} events deleted for user {user_id}" }


class UserAccountActivityTrackingSystem(BaseEnv):
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
        if hasattr(env, "_refresh_recognized_event_types_from_data"):
            env._refresh_recognized_event_types_from_data()

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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_event_timeline_for_user(self, **kwargs):
        return self._call_inner_tool('get_event_timeline_for_user', kwargs)

    def get_events_by_type_for_user(self, **kwargs):
        return self._call_inner_tool('get_events_by_type_for_user', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_predefined_event_types(self, **kwargs):
        return self._call_inner_tool('list_predefined_event_types', kwargs)

    def get_user_event_count_by_type(self, **kwargs):
        return self._call_inner_tool('get_user_event_count_by_type', kwargs)

    def check_user_existence(self, **kwargs):
        return self._call_inner_tool('check_user_existence', kwargs)

    def add_activity_event(self, **kwargs):
        return self._call_inner_tool('add_activity_event', kwargs)

    def update_event_timestamp(self, **kwargs):
        return self._call_inner_tool('update_event_timestamp', kwargs)

    def delete_activity_event(self, **kwargs):
        return self._call_inner_tool('delete_activity_event', kwargs)

    def edit_event_detail(self, **kwargs):
        return self._call_inner_tool('edit_event_detail', kwargs)

    def bulk_delete_events_for_user(self, **kwargs):
        return self._call_inner_tool('bulk_delete_events_for_user', kwargs)
