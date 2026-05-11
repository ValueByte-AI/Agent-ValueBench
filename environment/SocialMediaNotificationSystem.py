# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
from datetime import datetime
import uuid
from typing import Dict



class UserInfo(TypedDict):
    _id: str
    username: str
    notification_preference: str

class EventInfo(TypedDict):
    event_id: str
    event_type: str
    actor_id: str
    target_id: str
    related_content_id: str
    timestamp: str  # ISO format string for datetime

class NotificationInfo(TypedDict):
    notification_id: str
    recipient_user_id: str
    event_id: str
    delivery_status: str      # e.g. "pending", "delivered", "failed"
    viewed_status: str        # e.g. "unread", "read"
    delivered_at: Optional[str]  # ISO string or None
    viewed_at: Optional[str]     # ISO string or None

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: str  # ISO format string for datetime
    read_status: str  # e.g. "unread", "read"

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Notifications: {notification_id: NotificationInfo}
        self.notifications: Dict[str, NotificationInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # Constraints:
        # - Each notification is linked to a specific event and recipient user.
        # - A notification’s viewed_status can only be set after it is delivered.
        # - Fetching missed notifications means retrieving notifications where delivery_status is "delivered"
        #   but viewed_status is "unread" or "unviewed" for the user.
        # - Messages can only be marked as "read" by the intended recipient.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve a user's details given their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict:
                - If found: {"success": True, "data": UserInfo (dict)}
                - If not found: {"success": False, "error": "User not found"}

        Constraints:
            - Usernames are assumed to be unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's details (UserInfo dict) by their unique _id.

        Args:
            user_id (str): The unique user ID.

        Returns:
            dict:
                {"success": True, "data": UserInfo} if found,
                {"success": False, "error": "User not found"} otherwise.

        Constraints:
            - User ID must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_user_notification_preference(self, user_id: str = None, username: str = None) -> dict:
        """
        Retrieve the notification preference setting of a user.
    
        Args:
            user_id (str, optional): The unique user ID.
            username (str, optional): The user's username.
        
        Returns:
            dict: 
                On success: 
                    { "success": True, "data": <notification_preference_value> }
                On failure:
                    { "success": False, "error": <reason> }
                
        Constraints:
            - Exactly one of user_id or username must be provided.
            - User must exist.
        """
        # Ensure only one kind of identifier is provided
        if (user_id is None and username is None) or (user_id is not None and username is not None):
            return {
                "success": False,
                "error": "Must provide exactly one of user_id or username"
            }
    
        user = None
        if user_id is not None:
            user = self.users.get(user_id)
            if not user:
                return { "success": False, "error": "User ID not found" }
        else:
            # username is not None
            user = next((u for u in self.users.values() if u['username'] == username), None)
            if not user:
                return { "success": False, "error": "Username not found" }
    
        return { "success": True, "data": user['notification_preference'] }

    def get_events_for_user(self, user_id: str) -> dict:
        """
        Retrieve all events associated with a user, either as actor or target.

        Args:
            user_id (str): ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # May be empty if user has no associated events
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., "User not found"
            }

        Constraints:
            - The user must exist in the system.
            - Fetch events where the user is either actor_id or target_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        result = [
            event for event in self.events.values()
            if event["actor_id"] == user_id or event["target_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_notifications_for_user(self, user_id: str) -> dict:
        """
        Retrieve all notifications for a given user by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                success (bool): True if operation succeeded, False otherwise.
                data (List[NotificationInfo]): List of notifications (possibly empty) for the user if successful.
                error (str): Error message if failed.

        Constraints:
            - user_id must exist in the system (self.users).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        notifications = [
            notification for notification in self.notifications.values()
            if notification["recipient_user_id"] == user_id
        ]
        return { "success": True, "data": notifications }

    def get_notifications_by_status(
        self,
        user_id: str,
        delivery_status: Optional[str] = None,
        viewed_status: Optional[str] = None
    ) -> dict:
        """
        Retrieve notifications for a user filtered by delivery_status and/or viewed_status.

        Args:
            user_id (str): The recipient user's ID.
            delivery_status (Optional[str]): If provided, filter by this delivery_status value.
            viewed_status (Optional[str]): If provided, filter by this viewed_status value.

        Returns:
            dict:
            - If success: { "success": True, "data": List[NotificationInfo] }, possibly empty list.
            - If failure: { "success": False, "error": str } (e.g., user does not exist)

        Constraints:
            - User must exist.
            - Will only return notifications for the given user and optional statuses.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        results = []
        for notification in self.notifications.values():
            if notification["recipient_user_id"] != user_id:
                continue
            if delivery_status is not None and notification["delivery_status"] != delivery_status:
                continue
            if viewed_status is not None and notification["viewed_status"] != viewed_status:
                continue
            results.append(notification)

        return {"success": True, "data": results}

    def get_missed_notifications_for_user(self, user_id: str) -> dict:
        """
        Fetch all "missed" notifications (delivered but not viewed) for a user.

        Args:
            user_id (str): The user ID whose missed notifications are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[NotificationInfo]  # List of missed notifications, possibly empty
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - User must exist.
            - "Missed" = delivery_status=="delivered" and viewed_status in {"unread", "unviewed"}
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        missed = [
            notif for notif in self.notifications.values()
            if notif["recipient_user_id"] == user_id
               and notif["delivery_status"] == "delivered"
               and notif["viewed_status"] in {"unread", "unviewed"}
        ]

        return { "success": True, "data": missed }

    def get_notification_details(self, notification_id: str) -> dict:
        """
        Retrieve detailed information for a notification with the given notification_id.

        Args:
            notification_id (str): The unique id of the notification to query.

        Returns:
            dict: {
                "success": True,
                "data": NotificationInfo  # Notification details if found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. notification not found
            }

        Constraints:
            - The notification_id must exist in the system.
        """
        notification = self.notifications.get(notification_id)
        if not notification:
            return {"success": False, "error": "Notification not found"}

        return {"success": True, "data": notification}

    def get_messages_for_user(self, user_id: str) -> dict:
        """
        Retrieve all messages received by a user.

        Args:
            user_id (str): The unique identifier of the user whose messages are to be retrieved.

        Returns:
            dict:
                success (bool): True if query succeeds, else False.
                data (List[MessageInfo]): List of message information objects (possibly empty if no messages found).
                error (str, optional): Error message if operation fails (e.g., user does not exist).

        Constraints:
            - The user must exist in the system (users dictionary).
            - Returns all MessageInfo where recipient_id == user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        messages = [
            message for message in self.messages.values()
            if message["recipient_id"] == user_id
        ]
        return {"success": True, "data": messages}

    def get_unread_messages_for_user(self, user_id: str) -> dict:
        """
        Retrieve messages for a user that have not yet been read (read_status = "unread").

        Args:
            user_id (str): The ID of the user to fetch unread messages for.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # List of unread messages for the user (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if user does not exist
            }

        Constraints:
            - User with user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            message for message in self.messages.values()
            if message["recipient_id"] == user_id and message["read_status"] == "unread"
        ]
        return { "success": True, "data": result }

    def get_message_details(self, message_id: str) -> dict:
        """
        Retrieve the content and status information of a message by its unique message_id.

        Args:
            message_id (str): Unique identifier of the message to retrieve.

        Returns:
            dict:
              - On success: {"success": True, "data": MessageInfo}
              - On failure (not found): {"success": False, "error": "Message not found"}

        Constraints:
            - Returns only the message's information based on ID (no read permission checking required).
        """
        message = self.messages.get(message_id)
        if not message:
            return {"success": False, "error": "Message not found"}
        return {"success": True, "data": message}


    def mark_notification_as_viewed(self, notification_id: str) -> dict:
        """
        Marks a notification's viewed_status as 'read' if it has already been delivered.

        Args:
            notification_id (str): The unique ID of the notification to update.

        Returns:
            dict: {
                "success": True,
                "message": "Notification marked as read."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only possible if the notification exists and its delivery_status is 'delivered'.
            - Updates the viewed_at timestamp to current time.
        """
        notif = self.notifications.get(notification_id)
        if notif is None:
            return {"success": False, "error": "Notification not found"}

        if notif["delivery_status"] != "delivered":
            return {
                "success": False,
                "error": "Notification must be delivered before it can be marked as read"
            }

        notif["viewed_status"] = "read"
        notif["viewed_at"] = datetime.utcnow().isoformat() + "Z"

        return {"success": True, "message": "Notification marked as read."}

    def mark_message_as_read(self, message_id: str, user_id: str) -> dict:
        """
        Mark a message as 'read' if and only if the requesting user is the message's recipient.

        Args:
            message_id (str): The identifier of the message to update.
            user_id (str): The ID of the user attempting to mark the message as read.

        Returns:
            dict: {
                "success": True,
                "message": "Message marked as read."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, not the recipient)
            }

        Constraints:
            - Operation permitted only for the message's recipient.
        """
        message = self.messages.get(message_id)
        if not message:
            return {"success": False, "error": "Message not found."}

        if message["recipient_id"] != user_id:
            return {"success": False, "error": "Permission denied. Only the recipient can mark this message as read."}

        message["read_status"] = "read"
        return {"success": True, "message": "Message marked as read."}


    def trigger_notification_for_event(self, event_id: str) -> dict:
        """
        Create and deliver a new notification for a specific event to the corresponding recipient.

        Args:
            event_id (str): The ID of the event that triggers the notification.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Notification delivered",
                        "notification": <NotificationInfo>,
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The event must exist.
            - The target_id of the event must point to an existing user (as notification recipient).
            - Each notification is linked to the event and recipient.
        """
        # 1. Check that the event exists
        event = self.events.get(event_id)
        if not event:
            return { "success": False, "error": "Event does not exist" }

        # 2. Get recipient (target_id) and check user exists
        recipient_id = event.get("target_id")
        if not recipient_id or recipient_id not in self.users:
            return { "success": False, "error": "Recipient user does not exist" }

        # 3. Generate notification_id
        notification_id = str(uuid.uuid4())

        now = datetime.utcnow().isoformat() + 'Z'

        notification_info: NotificationInfo = {
            "notification_id": notification_id,
            "recipient_user_id": recipient_id,
            "event_id": event_id,
            "delivery_status": "delivered",
            "viewed_status": "unread",
            "delivered_at": now,
            "viewed_at": None,
        }

        self.notifications[notification_id] = notification_info

        return {
            "success": True,
            "message": "Notification delivered",
            "notification": notification_info,
        }


    def update_notification_delivery_status(self, notification_id: str, new_delivery_status: str) -> dict:
        """
        Change the delivery_status of a notification. If setting to "delivered",
        set the delivered_at field to the current time (ISO format) if it is not already set.

        Args:
            notification_id (str): The ID of the notification to update.
            new_delivery_status (str): The new status to assign (e.g., "pending", "delivered", "failed").

        Returns:
            dict:
                - On success: {"success": True, "message": "..."}
                - On failure: {"success": False, "error": "..."}
        Constraints:
            - Notification must exist.
            - If status is set to "delivered", set delivered_at to current time if not already present.
            - If status is changed from "delivered" to something else, clear delivered_at.
        """
        notif: Dict = self.notifications.get(notification_id)
        if notif is None:
            return {"success": False, "error": "Notification not found"}

        previous_status = notif["delivery_status"]
        notif["delivery_status"] = new_delivery_status

        if new_delivery_status == "delivered":
            # Only set delivered_at if not already set
            if notif.get("delivered_at") is None:
                notif["delivered_at"] = datetime.utcnow().isoformat() + "Z"
        else:
            # If the status is changed from "delivered" to something else, clear delivered_at
            if previous_status == "delivered":
                notif["delivered_at"] = None

        # Save back (not strictly needed for references)
        self.notifications[notification_id] = notif

        return {
            "success": True,
            "message": f"Notification delivery_status updated to {new_delivery_status}"
        }


    def update_notification_viewed_status(self, notification_id: str, new_status: str) -> dict:
        """
        Change the viewed_status of a notification if it exists and is already delivered.

        Args:
            notification_id (str): The ID of the notification to update.
            new_status (str): The value to set for viewed_status (expected: "read" or "unread").

        Returns:
            dict:
                - On success: { "success": True, "message": ... }
                - On failure: { "success": False, "error": ... }

        Constraints:
            - viewed_status can only be set if delivery_status is "delivered".
            - notification_id must exist.
            - viewed_at is updated to current time in ISO format if the status changes.
        """
        notif = self.notifications.get(notification_id)
        if notif is None:
            return { "success": False, "error": "Notification does not exist." }

        if notif["delivery_status"] != "delivered":
            return { "success": False, "error": "Cannot set viewed_status before delivery." }

        if notif["viewed_status"] == new_status:
            return { "success": True, "message": "Notification already has the desired viewed_status." }

        # Optionally, validate allowed viewed_status values
        if new_status not in ("unread", "read"):
            return { "success": False, "error": f"Invalid viewed_status: {new_status}" }

        notif["viewed_status"] = new_status
        notif["viewed_at"] = datetime.utcnow().isoformat() + "Z"

        return { "success": True, "message": "Viewed status updated successfully." }

    def delete_notification(self, notification_id: str) -> dict:
        """
        Permanently remove a notification from the system.

        Args:
            notification_id (str): The ID of the notification to delete.

        Returns:
            dict: 
                - If successful:
                    { "success": True, "message": "Notification <notification_id> deleted" }
                - If not found:
                    { "success": False, "error": "Notification not found" }

        Constraints:
            - Only deletes if the notification exists.
            - This is an admin or system maintenance operation (no permission checks).
            - No error is raised; gracefully handles not found case.
        """
        if notification_id not in self.notifications:
            return { "success": False, "error": "Notification not found" }
    
        del self.notifications[notification_id]
        return { "success": True, "message": f"Notification {notification_id} deleted" }

    def delete_message(self, message_id: str) -> dict:
        """
        Permanently remove a message from the system (admin or system maintenance action).

        Args:
            message_id (str): The ID of the message to delete.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Message deleted successfully."
                }
                or
                {
                    "success": False,
                    "error": "Message not found."
                }

        Constraints:
            - Message must exist to be deleted.
            - This is an admin/system maintenance action; no user permission checks.
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message not found."}

        self.messages.pop(message_id)
        return {"success": True, "message": "Message deleted successfully."}


class SocialMediaNotificationSystem(BaseEnv):
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

    def get_user_notification_preference(self, **kwargs):
        return self._call_inner_tool('get_user_notification_preference', kwargs)

    def get_events_for_user(self, **kwargs):
        return self._call_inner_tool('get_events_for_user', kwargs)

    def get_notifications_for_user(self, **kwargs):
        return self._call_inner_tool('get_notifications_for_user', kwargs)

    def get_notifications_by_status(self, **kwargs):
        return self._call_inner_tool('get_notifications_by_status', kwargs)

    def get_missed_notifications_for_user(self, **kwargs):
        return self._call_inner_tool('get_missed_notifications_for_user', kwargs)

    def get_notification_details(self, **kwargs):
        return self._call_inner_tool('get_notification_details', kwargs)

    def get_messages_for_user(self, **kwargs):
        return self._call_inner_tool('get_messages_for_user', kwargs)

    def get_unread_messages_for_user(self, **kwargs):
        return self._call_inner_tool('get_unread_messages_for_user', kwargs)

    def get_message_details(self, **kwargs):
        return self._call_inner_tool('get_message_details', kwargs)

    def mark_notification_as_viewed(self, **kwargs):
        return self._call_inner_tool('mark_notification_as_viewed', kwargs)

    def mark_message_as_read(self, **kwargs):
        return self._call_inner_tool('mark_message_as_read', kwargs)

    def trigger_notification_for_event(self, **kwargs):
        return self._call_inner_tool('trigger_notification_for_event', kwargs)

    def update_notification_delivery_status(self, **kwargs):
        return self._call_inner_tool('update_notification_delivery_status', kwargs)

    def update_notification_viewed_status(self, **kwargs):
        return self._call_inner_tool('update_notification_viewed_status', kwargs)

    def delete_notification(self, **kwargs):
        return self._call_inner_tool('delete_notification', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

