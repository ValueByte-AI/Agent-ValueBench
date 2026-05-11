# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime, timedelta, timezone



# User entity - maps _id (Steam ID) to profile data
class UserInfo(TypedDict):
    _id: str                # Steam ID
    display_name: str
    account_status: str
    account_creation_date: str  # Renamed for clarity

# Friendship entity - stores friendship relationships (bidirectional, symmetric)
class FriendshipInfo(TypedDict):
    friendship_id: str
    _id_1: str              # One user's Steam ID
    user_id_2: str          # The other user's Steam ID
    status: str
    date_friended: str

# Friend request entity - each friend request is auditable and captures workflow metadata
class FriendRequestInfo(TypedDict):
    requester_id: str
    recipient_id: str
    status: str
    request_date: str
    response_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Steam social network friend management system.
        """

        # Users: {_id (Steam ID): UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Friendships: {friendship_id: FriendshipInfo}
        # Each friendship should be symmetric (if (A, B) exists, (B, A) may or may not be separately stored,
        # but always query directionally).
        self.friendships: Dict[str, FriendshipInfo] = {}

        # Friend requests: {(requester_id, recipient_id, request_date): FriendRequestInfo}
        # For simplicity, index by composite key of requester, recipient, and request_date (unique per request).
        self.friend_requests: Dict[str, FriendRequestInfo] = {}

        # Constraints:
        # - Friendships are only established when a request is accepted.
        # - A user cannot be friends with themselves.
        # - Friendship relationships are symmetric: if A is friends with B, B is friends with A.
        # - Only users with valid, active accounts can initiate or accept friend requests.

    def _find_friend_request_key(
        self,
        requester_id: str,
        recipient_id: str,
        request_date: str,
    ) -> str | None:
        composite_key = f"{requester_id}|{recipient_id}|{request_date}"
        if composite_key in self.friend_requests:
            return composite_key
        for key, request in self.friend_requests.items():
            if (
                request.get("requester_id") == requester_id
                and request.get("recipient_id") == recipient_id
                and request.get("request_date") == request_date
            ):
                return key
        return None

    @staticmethod
    def _parse_iso_timestamp(value: str) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _format_iso_timestamp(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        iso = dt.astimezone(timezone.utc).isoformat()
        if iso.endswith("+00:00"):
            return iso[:-6] + "Z"
        return iso

    def _next_system_iso_timestamp(self) -> str:
        timestamps: list[datetime] = []
        for user in self.users.values():
            parsed = self._parse_iso_timestamp(user.get("account_creation_date"))
            if parsed is not None:
                timestamps.append(parsed)
        for request in self.friend_requests.values():
            for field in ("request_date", "response_date"):
                parsed = self._parse_iso_timestamp(request.get(field, ""))
                if parsed is not None:
                    timestamps.append(parsed)
        for friendship in self.friendships.values():
            parsed = self._parse_iso_timestamp(friendship.get("date_friended", ""))
            if parsed is not None:
                timestamps.append(parsed)

        if timestamps:
            return self._format_iso_timestamp(max(timestamps) + timedelta(seconds=1))
        return "1970-01-01T00:00:01Z"

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve the profile and account status for a given Steam user by _id.

        Args:
            _id (str): The Steam ID of the user to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # dict of user's profile and account status
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User not found"
            }
        Constraints:
            - Returns user info for an existing user with _id; fails if user does not exist.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_friends_by_user(self, user_id: str) -> dict:
        """
        List all friends' Steam IDs for the given user_id.

        Args:
            user_id (str): The Steam ID of the user whose friends are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of friends' Steam IDs
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure ("User does not exist")
            }

        Constraints:
            - The user must exist in the system.
            - Friendships are bidirectional: find friendships where user_id is either _id_1 or user_id_2, status is 'accepted'/'active'.
            - Returned friend IDs are sorted for deterministic output.
        """
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        # Get all friendships where user_id is a participant and status is accepted/active
        friend_ids = set()
        for fs in self.friendships.values():
            if fs["status"] not in ("accepted", "active"):  # Accept both labelings if possible
                continue
            if fs["_id_1"] == user_id:
                if fs["user_id_2"] != user_id:  # No self-friendship per constraints
                    friend_ids.add(fs["user_id_2"])
            elif fs["user_id_2"] == user_id:
                if fs["_id_1"] != user_id:
                    friend_ids.add(fs["_id_1"])
        return {"success": True, "data": sorted(friend_ids)}

    def get_friendship_info_between_users(self, user_id_1: str, user_id_2: str) -> dict:
        """
        Retrieve friendship metadata (status, date_friended, etc.) between two users, order-insensitive.

        Args:
            user_id_1 (str): Steam ID of the first user.
            user_id_2 (str): Steam ID of the second user.

        Returns:
            dict: {
                "success": True,
                "data": FriendshipInfo  # friendship info if friendship exists
            }
            or
            {
                "success": False,
                "error": str  # description of why the friendship info can't be found
            }

        Constraints:
            - Users cannot be friends with themselves.
            - Friendship symmetric: (A, B) == (B, A)
        """
        if user_id_1 == user_id_2:
            return {"success": False, "error": "A user cannot be friends with themselves."}

        found = None
        for friendship in self.friendships.values():
            if (
                (friendship["_id_1"] == user_id_1 and friendship["user_id_2"] == user_id_2) or
                (friendship["_id_1"] == user_id_2 and friendship["user_id_2"] == user_id_1)
            ):
                found = friendship
                break

        if found:
            return {"success": True, "data": found}
        else:
            return {"success": False, "error": "Friendship does not exist between specified users."}

    def get_date_became_friends(self, user_id_1: str, user_id_2: str) -> dict:
        """
        Returns the date two users became friends, if such a friendship exists and is active.

        Args:
            user_id_1 (str): Steam ID of first user
            user_id_2 (str): Steam ID of second user

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "date_became_friends": <str>  # ISO date string
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": <str>  # Error message
                }

        Constraints:
            - Both users must exist.
            - Users must not be the same.
            - Only return date if an active friendship exists between them.
        """
        # User existence
        if user_id_1 not in self.users or user_id_2 not in self.users:
            return { "success": False, "error": "One or both users do not exist." }
        if user_id_1 == user_id_2:
            return { "success": False, "error": "A user cannot be friends with themselves." }

        # Search for friendship (friendship is symmetric)
        for friendship in self.friendships.values():
            ids = {friendship["_id_1"], friendship["user_id_2"]}
            if {user_id_1, user_id_2} == ids:
                if friendship.get("status") == "active":
                    return {
                        "success": True,
                        "data": { "date_became_friends": friendship.get("date_friended") }
                    }
        return { "success": False, "error": "No active friendship exists between the users." }

    def list_friend_requests_for_user(self, user_id: str) -> dict:
        """
        List all friend requests received or sent by the specified user.

        Args:
            user_id (str): The Steam ID of the user to query.

        Returns:
            dict: {
                "success": True,
                "data": List[FriendRequestInfo],  # May be empty if no requests
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., user does not exist
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        requests = [
            info for info in self.friend_requests.values()
            if info["requester_id"] == user_id or info["recipient_id"] == user_id
        ]
        return { "success": True, "data": requests }

    def get_friend_request_info(self, requester_id: str, recipient_id: str, request_date: str = None) -> dict:
        """
        Retrieve information for a specific friend request between two users.

        Args:
            requester_id (str): The Steam ID of the user who sent the request.
            recipient_id (str): The Steam ID of the intended recipient.
            request_date (str, optional): The date of the request (exact match). 
                If omitted, retrieves the most recent friend request between the two users.

        Returns:
            dict: {
                "success": True,
                "data": FriendRequestInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. if request not found)
            }

        Constraints:
            - Looks up by requester_id, recipient_id, and optionally request_date.
            - If request_date is omitted, retrieves the latest request between the pair.
        """
        # Collect all requests between these two users (directional)
        requests = [
            req_info for req_info in self.friend_requests.values()
            if req_info["requester_id"] == requester_id and req_info["recipient_id"] == recipient_id
        ]

        if not requests:
            return { "success": False, "error": "No matching friend request found" }

        if request_date is not None:
            for req in requests:
                if req["request_date"] == request_date:
                    return { "success": True, "data": req }
            return { "success": False, "error": "No matching friend request found for given request_date" }

        # No request_date given: pick the most recent by request_date
        # Assuming ISO 8601 format strings for dates (lex order = chronological)
        most_recent = max(requests, key=lambda r: r["request_date"])
        return { "success": True, "data": most_recent }


    def send_friend_request(self, requester_id: str, recipient_id: str) -> dict:
        """
        Initiate a new friend request from one user to another, if allowed.

        Args:
            requester_id (str): Steam ID of the user sending the request.
            recipient_id (str): Steam ID of the intended recipient.
    
        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "message": "Friend request sent from <requester_id> to <recipient_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Both users must exist and have active accounts (account_status == 'active').
            - Users cannot send friend requests to themselves.
            - Users cannot send duplicate requests if a pending request (in either direction) exists.
            - Users cannot send a request if already friends.
        """
        # Check both users exist
        if requester_id not in self.users:
            return {"success": False, "error": f"Requester user '{requester_id}' does not exist"}
        if recipient_id not in self.users:
            return {"success": False, "error": f"Recipient user '{recipient_id}' does not exist"}
    
        # Check both users are active
        if self.users[requester_id]["account_status"] != "active":
            return {"success": False, "error": "Requester account is not active"}
        if self.users[recipient_id]["account_status"] != "active":
            return {"success": False, "error": "Recipient account is not active"}
    
        # Prevent self-requests
        if requester_id == recipient_id:
            return {"success": False, "error": "Cannot send friend request to oneself"}
    
        # Check for existing friendship
        for friendship in self.friendships.values():
            if ((friendship["_id_1"] == requester_id and friendship["user_id_2"] == recipient_id) or
                (friendship["_id_1"] == recipient_id and friendship["user_id_2"] == requester_id)):
                if friendship["status"] == "active":
                    return {"success": False, "error": "Users are already friends"}

        # Check for existing pending friend requests (in either direction)
        for fr in self.friend_requests.values():
            if ((fr["requester_id"] == requester_id and fr["recipient_id"] == recipient_id) or
                (fr["requester_id"] == recipient_id and fr["recipient_id"] == requester_id)):
                if fr["status"] == "pending":
                    return {"success": False, "error": "A pending friend request already exists between these users"}

        # Create the friend request
        now_iso = self._next_system_iso_timestamp()
        # For uniqueness in key, use tuple or stringified (requester_id, recipient_id, now_iso)
        composite_key = f"{requester_id}|{recipient_id}|{now_iso}"
        friend_request = {
            "requester_id": requester_id,
            "recipient_id": recipient_id,
            "status": "pending",
            "request_date": now_iso,
            "response_date": ""
        }
        self.friend_requests[composite_key] = friend_request

        return {
            "success": True,
            "message": f"Friend request sent from {requester_id} to {recipient_id}"
        }

    def accept_friend_request(
        self,
        requester_id: str,
        recipient_id: str,
        request_date: str,
        response_date: str = "",
    ) -> dict:
        """
        Accept a pending friend request, creating a friendship as per constraints.

        Args:
            requester_id (str): The Steam ID of the user who sent the friend request.
            recipient_id (str): The Steam ID of the user accepting the friend request.
            request_date (str): The ISO date/time string when the request was sent (unique per request).
            response_date (str, optional): The ISO date/time string when the request is accepted.
                If omitted or empty, the system records the current system timestamp automatically.

        Returns:
            dict: 
                On success: {"success": True, "message": "Friend request accepted and friendship created."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Only users with valid, active accounts can accept friend requests.
            - Cannot be friends with oneself.
            - Friendships are only stored if a request is accepted.
            - Friendship relationship is symmetric.
        """
        # Find friend request
        fr_key = self._find_friend_request_key(requester_id, recipient_id, request_date)
        friend_request = self.friend_requests.get(fr_key)
        if not friend_request:
            return {"success": False, "error": "Friend request does not exist."}
        if friend_request["status"] != "pending":
            return {"success": False, "error": "Friend request is not pending."}

        # Check users exist
        user1 = self.users.get(requester_id)
        user2 = self.users.get(recipient_id)
        if not user1 or not user2:
            return {"success": False, "error": "One or both users do not exist."}

        # Check accounts are active
        if user1["account_status"] != "active" or user2["account_status"] != "active":
            return {"success": False, "error": "One or both users are not active."}

        # Cannot be friends with self
        if requester_id == recipient_id:
            return {"success": False, "error": "A user cannot be friends with themselves."}

        # Check for existing friendship (friendship is bidirectional, check both orders)
        already_friends = any(
            (
                (finfo["_id_1"] == requester_id and finfo["user_id_2"] == recipient_id) or
                (finfo["_id_1"] == recipient_id and finfo["user_id_2"] == requester_id)
            ) and finfo["status"] == "active"
            for finfo in self.friendships.values()
        )
        if already_friends:
            return {"success": False, "error": "Users are already friends."}

        # Accept the friend request
        if not isinstance(response_date, str) or not response_date:
            response_date = self._next_system_iso_timestamp()
        friend_request["status"] = "accepted"
        friend_request["response_date"] = response_date
        self.friend_requests[fr_key] = friend_request

        # Create friendship_id as canonical: smaller_id|larger_id
        sorted_ids = sorted([requester_id, recipient_id])
        friendship_id = f"{sorted_ids[0]}|{sorted_ids[1]}"
        friendship_info = {
            "friendship_id": friendship_id,
            "_id_1": sorted_ids[0],
            "user_id_2": sorted_ids[1],
            "status": "active",
            "date_friended": response_date,
        }
        self.friendships[friendship_id] = friendship_info

        return {"success": True, "message": "Friend request accepted and friendship created."}

    def decline_friend_request(self, requester_id: str, recipient_id: str) -> dict:
        """
        Decline or ignore a pending friend request without creating a friendship.

        Args:
            requester_id (str): ID of the user who sent the friend request.
            recipient_id (str): ID of the user who received the friend request.

        Returns:
            dict:
                - On success: { "success": True, "message": "Friend request declined." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only users with valid, active accounts can decline friend requests.
            - The request must exist and be pending.
            - The system records an ISO 8601 response_date automatically when the decline is applied.
        """

        # Check if recipient exists and is active
        recipient = self.users.get(recipient_id)
        if not recipient or recipient.get("account_status") != "active":
            return { "success": False, "error": "Recipient account does not exist or is not active." }

        # Search for most recent pending request from requester_id to recipient_id
        # As friend_requests are keyed by composite requester_id|recipient_id|request_date
        pending_requests = []
        for fr in self.friend_requests.values():
            if (fr["requester_id"] == requester_id 
                and fr["recipient_id"] == recipient_id
                and fr["status"] == "pending"):
                pending_requests.append(fr)
        if not pending_requests:
            return { "success": False, "error": "No pending friend request from requester to recipient." }
        # If multiple, decline the most recent (by request_date)
        # Assume ISO string; sort descending
        pending_requests.sort(key=lambda fr: fr["request_date"], reverse=True)
        to_decline = pending_requests[0]
        # Update request status and store a deterministic ISO 8601 response timestamp.
        to_decline["status"] = "declined"
        to_decline["response_date"] = self._next_system_iso_timestamp()

        return { "success": True, "message": "Friend request declined." }

    def remove_friend(self, user_id_1: str, user_id_2: str) -> dict:
        """
        Terminate (delete) the friendship between two distinct users, if it exists.

        Args:
            user_id_1 (str): Steam ID of the first user.
            user_id_2 (str): Steam ID of the second user.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Friendship between user_id_1 and user_id_2 has been removed." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Both user IDs must exist.
            - Users must not be the same.
            - Friendship must exist (regardless of order of user IDs).
        """
        # Check that both users exist
        if user_id_1 not in self.users or user_id_2 not in self.users:
            return {"success": False, "error": "One or both users do not exist."}

        # Check that user IDs are not the same
        if user_id_1 == user_id_2:
            return {"success": False, "error": "A user cannot be friends with themselves."}

        # Find the friendship in either direction
        friendship_id_to_remove = None
        for fid, f_info in self.friendships.items():
            ids_set = {f_info["_id_1"], f_info["user_id_2"]}
            if {user_id_1, user_id_2} == ids_set:
                friendship_id_to_remove = fid
                break

        if not friendship_id_to_remove:
            return {"success": False, "error": "No friendship exists between the given users."}

        # Remove the friendship
        del self.friendships[friendship_id_to_remove]

        return {
            "success": True,
            "message": f"Friendship between {user_id_1} and {user_id_2} has been removed."
        }

    def update_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Change the status of a user's account.

        Args:
            user_id (str): The Steam ID of the user whose account status should be changed.
            new_status (str): The new status to assign (e.g., "active", "suspended", "banned").

        Returns:
            dict: {
                "success": True,
                "message": "Account status updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the failure.
            }

        Constraints:
            - The user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Optionally, enforce allowed status values
        allowed_statuses = {"active", "suspended", "banned"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status value: {new_status}" }

        self.users[user_id]["account_status"] = new_status
        return { "success": True, "message": "Account status updated successfully" }

    def cancel_sent_friend_request(self, requester_id: str, recipient_id: str, request_date: str) -> dict:
        """
        Withdraw a pending friend request that the user has previously sent.

        Args:
            requester_id (str): Steam ID of user withdrawing sent request.
            recipient_id (str): Steam ID of target user.
            request_date (str): Date string of when the request was sent (unique identifier).

        Returns:
            dict:
                - On success: { "success": True, "message": "Friend request cancelled successfully." }
                - On error: { "success": False, "error": "Error message." }

        Constraints:
            - Only the original requester can cancel their own request.
            - Both users must exist and be in active account status.
            - The friend request must exist and be in 'pending' status to be cancelled.
            - The system records an ISO 8601 response_date automatically when the cancellation is applied.
        """
        # Check user existence and account status
        req_user = self.users.get(requester_id)
        rec_user = self.users.get(recipient_id)
        if not req_user or not rec_user:
            return {"success": False, "error": "Requester or recipient does not exist."}
        if req_user["account_status"] != "active":
            return {"success": False, "error": "Only users with active accounts can cancel sent requests."}
        if rec_user["account_status"] != "active":
            return {"success": False, "error": "Only users with active accounts can cancel sent requests."}

        # Build friend request lookup key and find the request
        req_key = self._find_friend_request_key(requester_id, recipient_id, request_date)
        req_info = self.friend_requests.get(req_key)
        if not req_info:
            return {"success": False, "error": "No such friend request found."}

        # Ensure it is pending
        if req_info["status"] != "pending":
            return {"success": False, "error": "Friend request is not pending and cannot be cancelled."}

        # Mark as "cancelled" (or 'withdrawn'), and set a deterministic ISO 8601 response_date.
        req_info["status"] = "cancelled"
        req_info["response_date"] = self._next_system_iso_timestamp()

        # Update in storage
        self.friend_requests[req_key] = req_info

        return {"success": True, "message": "Friend request cancelled successfully."}

    def edit_friendship_metadata(self, friendship_id: str, metadata_updates: dict) -> dict:
        """
        Edit metadata fields of a friendship (admin/system-level operation).

        Args:
            friendship_id (str): The unique ID of the friendship to modify.
            metadata_updates (dict): Key-value pairs of metadata fields to update.
                                    Allowed fields: "date_friended", "status".

        Returns:
            dict:
                On success: { "success": True, "message": "Friendship <id> metadata updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - friendship_id must exist.
            - Only "date_friended" and "status" fields can be edited.
            - Friendship participants (_id_1, user_id_2) cannot be modified.
            - At least one allowed field must be provided for update.
        """
        # Check that the friendship exists
        if friendship_id not in self.friendships:
            return { "success": False, "error": "Friendship not found" }

        allowed_fields = {"date_friended", "status"}
        if not metadata_updates:
            return { "success": False, "error": "No metadata updates provided" }

        # Check that all update fields are allowed
        invalid_fields = [k for k in metadata_updates.keys() if k not in allowed_fields]
        if invalid_fields:
            return {
                "success": False,
                "error": f"Cannot update fields: {', '.join(invalid_fields)}"
            }

        # Apply metadata updates
        for field, value in metadata_updates.items():
            self.friendships[friendship_id][field] = value

        return {
            "success": True,
            "message": f"Friendship {friendship_id} metadata updated"
        }


class SteamFriendManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_friends_by_user(self, **kwargs):
        return self._call_inner_tool('list_friends_by_user', kwargs)

    def get_friendship_info_between_users(self, **kwargs):
        return self._call_inner_tool('get_friendship_info_between_users', kwargs)

    def get_date_became_friends(self, **kwargs):
        return self._call_inner_tool('get_date_became_friends', kwargs)

    def list_friend_requests_for_user(self, **kwargs):
        return self._call_inner_tool('list_friend_requests_for_user', kwargs)

    def get_friend_request_info(self, **kwargs):
        return self._call_inner_tool('get_friend_request_info', kwargs)

    def send_friend_request(self, **kwargs):
        return self._call_inner_tool('send_friend_request', kwargs)

    def accept_friend_request(self, **kwargs):
        return self._call_inner_tool('accept_friend_request', kwargs)

    def decline_friend_request(self, **kwargs):
        return self._call_inner_tool('decline_friend_request', kwargs)

    def remove_friend(self, **kwargs):
        return self._call_inner_tool('remove_friend', kwargs)

    def update_account_status(self, **kwargs):
        return self._call_inner_tool('update_account_status', kwargs)

    def cancel_sent_friend_request(self, **kwargs):
        return self._call_inner_tool('cancel_sent_friend_request', kwargs)

    def edit_friendship_metadata(self, **kwargs):
        return self._call_inner_tool('edit_friendship_metadata', kwargs)
