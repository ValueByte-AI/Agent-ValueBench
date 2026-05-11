# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Tuple, TypedDict
from typing import List, Dict, Any
import uuid



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    account_sta: str  # Account status

class SubscriptionInfo(TypedDict):
    subscription_id: str
    user_id: str
    channel_type: str
    status: str

class EventTypeInfo(TypedDict):
    event_type_id: str
    event_type_name: str
    description: str

class NotificationPreferenceInfo(TypedDict):
    subscription_id: str
    event_type_id: str
    is_enabled: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        SaaS notification preference management system.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Subscriptions: {subscription_id: SubscriptionInfo}
        self.subscriptions: Dict[str, SubscriptionInfo] = {}

        # Event types: {event_type_id: EventTypeInfo}
        self.event_types: Dict[str, EventTypeInfo] = {}

        # Notification preferences: {(subscription_id, event_type_id): NotificationPreferenceInfo}
        # - Each (subscription_id, event_type_id) is unique.
        self.notification_preferences: Dict[Tuple[str, str], NotificationPreferenceInfo] = {}

        # Constraint notes:
        # - Preference changes apply only to the specified subscription (not globally).
        # - Disabling an event notification type does not affect other types/subscriptions.
        # - User must have an active subscription to update preferences.
        # - Each (subscription_id, event_type_id) pair is unique.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's information by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,
            }
            or
            {
                "success": False,
                "error": "User not found",
            }

        Constraints:
            - Returns user info if the user_id exists.
            - Returns an error if the user_id does not exist.
        """
        if user_id in self.users:
            return { "success": True, "data": self.users[user_id] }
        else:
            return { "success": False, "error": "User not found" }

    def get_user_by_email(self, email: str) -> dict:
        """
        Retrieve a user's information given their email address.

        Args:
            email (str): The user's email address.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,
            }
            OR
            {
                "success": False,
                "error": str,  # Reason, e.g. user not found or invalid input
            }

        Constraints:
            - Email must be non-empty.
        """

        if not email or not isinstance(email, str):
            return { "success": False, "error": "Invalid email address" }

        for user in self.users.values():
            if user.get('email', '').lower() == email.lower():
                return { "success": True, "data": user }

        return { "success": False, "error": "User not found for the provided email address" }

    def list_user_subscriptions(self, user_id: str) -> dict:
        """
        List all subscriptions belonging to a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[SubscriptionInfo]
                    }
                - On failure (user does not exist):
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - Only includes subscriptions of the specified user.
            - User must exist; otherwise, error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_subscriptions = [
            sub_info for sub_info in self.subscriptions.values()
            if sub_info["user_id"] == user_id
        ]
        return { "success": True, "data": user_subscriptions }

    def get_subscription_by_id(self, subscription_id: str) -> dict:
        """
        Retrieve details of a single subscription using subscription_id.

        Args:
            subscription_id (str): The ID of the subscription to fetch.

        Returns:
            dict: {
                "success": True,
                "data": SubscriptionInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., "Subscription not found")
            }

        Constraints:
            - Returns information for the specified subscription_id if it exists.
            - No creation or modification performed.
        """
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            return {"success": False, "error": "Subscription not found"}

        return {"success": True, "data": subscription}

    def check_subscription_active(self, subscription_id: str) -> dict:
        """
        Check if a particular subscription is currently active.

        Args:
            subscription_id (str): The subscription ID to check.

        Returns:
            dict: 
                On success: { "success": True, "data": bool }
                    - data=True if the subscription is currently active.
                    - data=False if subscription exists but is not active.
                On failure: { "success": False, "error": str }
                    - error contains the reason (e.g., subscription does not exist).

        Constraints:
            - The subscription must exist in the system.
            - 'Active' is defined as the subscription's status == "active" (case insensitive).
        """
        sub = self.subscriptions.get(subscription_id)
        if sub is None:
            return { "success": False, "error": "Subscription does not exist" }

        is_active = str(sub.get("status", "")).lower() == "active"
        return { "success": True, "data": is_active }

    def list_all_event_types(self) -> dict:
        """
        Retrieve a list of all definable notification event types in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EventTypeInfo]  # May be empty if no event types defined
            }
        """
        return {
            "success": True,
            "data": list(self.event_types.values())
        }

    def get_event_type_by_name(self, event_type_name: str) -> dict:
        """
        Retrieve event type details given its name.

        Args:
            event_type_name (str): Name of the event type (e.g., "account verification").

        Returns:
            dict: {
                "success": True,
                "data": EventTypeInfo,  # Event type details if found.
            }
            or
            {
                "success": False,
                "error": str  # "Event type not found", "Invalid event type name", etc.
            }

        Constraints:
            - Returns the first event type with that name.
            - Case-sensitive (unless spec says otherwise).
            - Event type name must not be empty.
        """
        if not event_type_name or not isinstance(event_type_name, str):
            return { "success": False, "error": "Invalid event type name" }
        for event_type in self.event_types.values():
            if event_type["event_type_name"] == event_type_name:
                return { "success": True, "data": event_type }
        return { "success": False, "error": "Event type not found" }

    def get_event_type_by_id(self, event_type_id: str) -> dict:
        """
        Retrieve the event type details for the given event_type_id.

        Args:
            event_type_id (str): The unique identifier of the event type.

        Returns:
            dict: {
                "success": True,
                "data": EventTypeInfo  # Event type details
            }
            or
            {
                "success": False,
                "error": str  # Reason why retrieval failed (not found)
            }

        Constraints:
            - event_type_id must exist in the event types map.
        """
        if event_type_id not in self.event_types:
            return { "success": False, "error": "Event type not found" }

        return { "success": True, "data": self.event_types[event_type_id] }

    def get_notification_preference(self, subscription_id: str, event_type_id: str) -> dict:
        """
        Retrieve the notification preference (is_enabled) for a specific (subscription_id, event_type_id) pair.

        Args:
            subscription_id (str): The subscription identifier.
            event_type_id (str): The event type identifier.

        Returns:
            dict: {
                "success": True,
                "data": NotificationPreferenceInfo   # {subscription_id, event_type_id, is_enabled}
            }
            or
            {
                "success": False,
                "error": str  # If the notification preference pair does not exist.
            }

        Constraints:
            - The (subscription_id, event_type_id) pair must exist in the notification_preferences.
        """
        key = (subscription_id, event_type_id)
        if key not in self.notification_preferences:
            return {"success": False, "error": "Notification preference for the given subscription and event type not found."}

        preference = self.notification_preferences[key]
        return {"success": True, "data": preference}

    def list_preferences_for_subscription(self, subscription_id: str) -> dict:
        """
        Retrieve all notification preferences (across all event types) for a given subscription.

        Args:
            subscription_id (str): The ID of the subscription to query.

        Returns:
            dict: {
                "success": True,
                "data": List[NotificationPreferenceInfo],
            }
            or
            {
                "success": False,
                "error": str,  # e.g. "Subscription does not exist"
            }

        Constraints:
            - The subscription must exist in the system.
            - Only preferences tied to this subscription (not others) are returned.
        """
        if subscription_id not in self.subscriptions:
            return {"success": False, "error": "Subscription does not exist"}

        result = [
            pref for (sub_id, _), pref in self.notification_preferences.items()
            if sub_id == subscription_id
        ]
        return {"success": True, "data": result}

    def set_notification_preference(
        self,
        subscription_id: str,
        event_type_id: str,
        is_enabled: bool
    ) -> dict:
        """
        Enable or disable notifications for a specific (subscription_id, event_type_id) pair.

        Args:
            subscription_id (str): The subscription to update.
            event_type_id (str): The event type to update.
            is_enabled (bool): Whether notifications should be enabled.

        Returns:
            dict: {
                "success": True,
                "message": "Notification preference updated"
            }
            or
            {
                "success": False,
                "error": "Reason"
            }

        Constraints:
            - Only updates the specified notification preference, not other event types/subscriptions.
            - The subscription must exist and be active.
            - The event type must exist.
            - A notification preference for this (subscription_id, event_type_id) must already exist.
        """
        # Check subscription exists
        if subscription_id not in self.subscriptions:
            return {"success": False, "error": "Subscription does not exist"}

        sub = self.subscriptions[subscription_id]
        # Check subscription is active
        if sub.get("status") != "active":
            return {"success": False, "error": "Subscription is not active"}

        # Check event type exists
        if event_type_id not in self.event_types:
            return {"success": False, "error": "Event type does not exist"}

        pref_key = (subscription_id, event_type_id)
        # Confirm notification preference exists
        if pref_key not in self.notification_preferences:
            return {"success": False, "error": "Notification preference does not exist"}

        self.notification_preferences[pref_key]["is_enabled"] = is_enabled
        return {"success": True, "message": "Notification preference updated"}


    def bulk_update_preferences(self, subscription_id: str, updates: List[Dict[str, Any]]) -> dict:
        """
        Update (enable/disable) notification preferences for multiple event types in a single subscription.

        Args:
            subscription_id (str): The subscription whose preferences are being updated.
            updates (List[Dict]): Each dict contains:
                - event_type_id (str): ID of the event type to update.
                - is_enabled (bool): Desired preference state.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "Updated n preferences for subscription <id>"
                }
                On failure:
                {
                    "success": False,
                    "error": <error string>
                }
            - If mixed (partial update): report which were changed, which failed with reasons.

        Constraints:
          - Subscription must exist and be ACTIVE.
          - Each (subscription_id, event_type_id) must already exist in notification_preferences.
          - Disables/enables apply only to the specified subscription/event types.
          - Invalid event types, or missing NotificationPreference entries are reported and skipped.
        """
        # Check subscription existence and status
        if subscription_id not in self.subscriptions:
            return { "success": False, "error": "Subscription not found" }
        sub_info = self.subscriptions[subscription_id]
        if sub_info['status'].lower() != "active":
            return { "success": False, "error": "Subscription is not active" }

        updated = 0
        errors = []
        for item in updates:
            event_type_id = item.get("event_type_id")
            is_enabled = item.get("is_enabled")
        
            if event_type_id not in self.event_types:
                errors.append(f"Unknown event_type_id: {event_type_id}")
                continue

            np_key = (subscription_id, event_type_id)
            if np_key not in self.notification_preferences:
                errors.append(f"No notification preference for event_type_id={event_type_id} in this subscription")
                continue

            # Update the is_enabled field
            self.notification_preferences[np_key]["is_enabled"] = bool(is_enabled)
            updated += 1

        if errors and updated == 0:
            return {
                "success": False,
                "error": "No preferences updated: " + "; ".join(errors)
            }
        elif errors:
            return {
                "success": True,
                "message": f"Updated {updated} preferences for subscription {subscription_id}. Some updates skipped: {'; '.join(errors)}"
            }

        return {
            "success": True,
            "message": f"Updated {updated} preferences for subscription {subscription_id}"
        }

    def create_notification_preference(
        self, 
        subscription_id: str, 
        event_type_id: str, 
        is_enabled: bool
    ) -> dict:
        """
        Create a new notification preference for a (subscription_id, event_type_id) pair if not existing.

        Args:
            subscription_id (str): The subscription to associate the preference with.
            event_type_id (str): The event type for the notification preference.
            is_enabled (bool): Whether notifications are enabled for this type in this subscription.

        Returns:
            dict: {
                "success": True,
                "message": "Notification preference created for subscription_id X and event_type_id Y."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only create if such a preference does not already exist.
            - Subscription must exist and be 'active'.
            - Event type must exist.
            - Preference applies to given subscription only.
        """
        # Ensure subscription exists and is active
        sub = self.subscriptions.get(subscription_id)
        if sub is None:
            return { "success": False, "error": "Subscription does not exist" }
        if sub["status"] != "active":
            return { "success": False, "error": "Subscription is not active" }
    
        # Ensure event type exists
        if event_type_id not in self.event_types:
            return { "success": False, "error": "Event type does not exist" }

        key = (subscription_id, event_type_id)
        if key in self.notification_preferences:
            return { "success": False, "error": "Notification preference already exists for this (subscription_id, event_type_id)" }
    
        self.notification_preferences[key] = {
            "subscription_id": subscription_id,
            "event_type_id": event_type_id,
            "is_enabled": is_enabled
        }
        return {
            "success": True,
            "message": f"Notification preference created for subscription_id {subscription_id} and event_type_id {event_type_id}."
        }

    def delete_notification_preference(self, subscription_id: str, event_type_id: str) -> dict:
        """
        Remove a notification preference entry for the given (subscription_id, event_type_id) pair.

        Args:
            subscription_id (str): The ID of the subscription.
            event_type_id (str): The ID of the event type.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Preference removed for (subscription_id, event_type_id)"
                  }
                - On failure: {
                    "success": False,
                    "error": "<Reason>"
                  }

        Constraints:
            - Only affects the specified (subscription_id, event_type_id) pair.
            - If entry does not exist, return a failure message.
        """
        key = (subscription_id, event_type_id)
        if key not in self.notification_preferences:
            return {
                "success": False,
                "error": f"Preference for subscription_id '{subscription_id}' and event_type_id '{event_type_id}' does not exist."
            }
        del self.notification_preferences[key]
        return {
            "success": True,
            "message": f"Preference removed for (subscription_id: {subscription_id}, event_type_id: {event_type_id})"
        }

    def update_subscription_status(self, subscription_id: str, new_status: str) -> dict:
        """
        Change the status of a subscription (e.g., activate/deactivate).

        Args:
            subscription_id (str): The unique identifier of the subscription to update.
            new_status (str): The new status value for the subscription.

        Returns:
            dict: On success: {
                "success": True,
                "message": "Subscription <subscription_id> status updated to <new_status>"
            }
            On error: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The subscription_id must exist in the system.
            - The status field is updated regardless of its prior value.
        """
        if subscription_id not in self.subscriptions:
            return { "success": False, "error": "Subscription does not exist" }
    
        self.subscriptions[subscription_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Subscription {subscription_id} status updated to {new_status}"
        }

    def add_new_subscription(
        self, 
        user_id: str, 
        channel_type: str, 
        status: str = "active", 
        subscription_id: str = None
    ) -> dict:
        """
        Add a new notification subscription for a user (e.g., a new channel like push, SMS).

        Args:
            user_id (str): The user who will own the subscription.
            channel_type (str): Notification channel type (e.g., 'email', 'SMS', 'push').
            status (str): Status of the subscription, default is 'active'.
            subscription_id (str, optional): Optional explicit ID; if None, a unique one is generated.

        Returns:
            dict: 
                - On success: { "success": True, "message": "...", "subscription_id": str }
                - On failure: { "success": False, "error": str }
    
        Constraints:
            - User must exist.
            - User cannot have more than one subscription with the same channel_type.
            - subscription_id must be unique.
        """
        # Check that the user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Enforce one subscription per user/channel_type
        for s in self.subscriptions.values():
            if s["user_id"] == user_id and s["channel_type"] == channel_type:
                return { "success": False, "error": "User already has a subscription for this channel" }
    
        # Generate unique subscription_id if not provided
        if subscription_id is None:
            subscription_id = str(uuid.uuid4())
        elif subscription_id in self.subscriptions:
            return { "success": False, "error": "Provided subscription_id already exists" }
    
        # Create the new subscription
        new_subscription = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "channel_type": channel_type,
            "status": status
        }
        self.subscriptions[subscription_id] = new_subscription

        return { "success": True, "message": "Subscription added", "subscription_id": subscription_id }


class SaaSNotificationPreferenceSystem(BaseEnv):
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
            if key == "users" and isinstance(value, dict):
                normalized = {}
                for _, user in value.items():
                    if isinstance(user, dict) and user.get("_id"):
                        normalized[user["_id"]] = copy.deepcopy(user)
                setattr(env, key, normalized)
                continue
            if key == "subscriptions" and isinstance(value, dict):
                normalized = {}
                for _, sub in value.items():
                    if isinstance(sub, dict) and sub.get("subscription_id"):
                        normalized[sub["subscription_id"]] = copy.deepcopy(sub)
                setattr(env, key, normalized)
                continue
            if key == "event_types" and isinstance(value, dict):
                normalized = {}
                for _, event_type in value.items():
                    if isinstance(event_type, dict) and event_type.get("event_type_id"):
                        normalized[event_type["event_type_id"]] = copy.deepcopy(event_type)
                setattr(env, key, normalized)
                continue
            if key == "notification_preferences" and isinstance(value, dict):
                normalized = {}
                for _, pref in value.items():
                    if isinstance(pref, dict) and pref.get("subscription_id") and pref.get("event_type_id"):
                        normalized[(pref["subscription_id"], pref["event_type_id"])] = copy.deepcopy(pref)
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def list_user_subscriptions(self, **kwargs):
        return self._call_inner_tool('list_user_subscriptions', kwargs)

    def get_subscription_by_id(self, **kwargs):
        return self._call_inner_tool('get_subscription_by_id', kwargs)

    def check_subscription_active(self, **kwargs):
        return self._call_inner_tool('check_subscription_active', kwargs)

    def list_all_event_types(self, **kwargs):
        return self._call_inner_tool('list_all_event_types', kwargs)

    def get_event_type_by_name(self, **kwargs):
        return self._call_inner_tool('get_event_type_by_name', kwargs)

    def get_event_type_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_type_by_id', kwargs)

    def get_notification_preference(self, **kwargs):
        return self._call_inner_tool('get_notification_preference', kwargs)

    def list_preferences_for_subscription(self, **kwargs):
        return self._call_inner_tool('list_preferences_for_subscription', kwargs)

    def set_notification_preference(self, **kwargs):
        return self._call_inner_tool('set_notification_preference', kwargs)

    def bulk_update_preferences(self, **kwargs):
        return self._call_inner_tool('bulk_update_preferences', kwargs)

    def create_notification_preference(self, **kwargs):
        return self._call_inner_tool('create_notification_preference', kwargs)

    def delete_notification_preference(self, **kwargs):
        return self._call_inner_tool('delete_notification_preference', kwargs)

    def update_subscription_status(self, **kwargs):
        return self._call_inner_tool('update_subscription_status', kwargs)

    def add_new_subscription(self, **kwargs):
        return self._call_inner_tool('add_new_subscription', kwargs)
