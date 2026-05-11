# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from datetime import datetime
from collections import defaultdict



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    account_status: str  # from "account_sta"

class ShortenedLinkInfo(TypedDict):
    link_id: str
    short_url: str
    original_url: str
    owner_user_id: str
    created_at: str
    is_active: bool  # from "is_activ"

class ClickEventInfo(TypedDict):
    event_id: str  # from "vent_id"
    link_id: str
    timestamp: str
    referrer: str
    device_type: str
    country: str
    ip_address: str
    user_agent: str  # from "user_agen"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a URL analytics and shortening platform.
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Shortened Links: {link_id: ShortenedLinkInfo}
        self.links: Dict[str, ShortenedLinkInfo] = {}

        # Click Events: {event_id: ClickEventInfo}
        self.click_events: Dict[str, ClickEventInfo] = {}

        # Constraints:
        # - Each ShortenedLink must be associated with one User (owner_user_id in users)
        # - ClickEvents must always reference a valid ShortenedLink (link_id in links)
        # - Only active ShortenedLinks (is_active) can register ClickEvents
        # - Data privacy: Only owner may access full ClickEvent analytics/details
        # - Duplicate ClickEvents (same timestamp, link_id, ip_address) may be filtered or flagged

    def get_user_by_username(self, username: str) -> dict:
        """
        Look up and retrieve a user's information by their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict:
                On success:
                    { "success": True, "data": UserInfo }
                On failure:
                    { "success": False, "error": "User not found" }

        Constraints:
            - Usernames are assumed to be unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve full user information using the unique user identifier.

        Args:
            user_id (str): The user's unique identifier (_id).

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - Returns user info only if user exists in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def list_user_links(self, user_id: str) -> dict:
        """
        List all ShortenedLinks owned by the specified user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ShortenedLinkInfo],  # all links owned by user (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # 'User not found'
            }

        Constraints:
            - The user_id must reference an existing user in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        user_links = [
            link_info
            for link_info in self.links.values()
            if link_info["owner_user_id"] == user_id
        ]
        return { "success": True, "data": user_links }

    def get_link_by_short_url(self, short_url: str) -> dict:
        """
        Retrieve metadata for a shortened link by its custom or platform-generated short_url.

        Args:
            short_url (str): The short URL string to search for.

        Returns:
            dict: {
                "success": True,
                "data": ShortenedLinkInfo,     # metadata for the shortened link
            }
            or
            {
                "success": False,
                "error": str  # If the short_url does not exist in the platform
            }
        Constraints:
            - Each short_url is expected to be unique within the platform.
        """
        for link_info in self.links.values():
            if link_info["short_url"] == short_url:
                return { "success": True, "data": link_info }
        return { "success": False, "error": "Short URL not found" }

    def get_link_by_id(self, link_id: str) -> dict:
        """
        Fetch the details (metadata) of a ShortenedLink using its link_id.

        Args:
            link_id (str): The unique identifier of the ShortenedLink.

        Returns:
            dict:
                - On success: { "success": True, "data": ShortenedLinkInfo }
                - On failure: { "success": False, "error": "Link ID does not exist" }
        """
        if link_id not in self.links:
            return { "success": False, "error": "Link ID does not exist" }
        return { "success": True, "data": self.links[link_id] }

    def check_link_ownership(self, user_id: str, link_id: str) -> dict:
        """
        Verify if a given user is the owner of a particular ShortenedLink.

        Args:
            user_id (str): The ID of the user to check.
            link_id (str): The ID of the shortened link to check.

        Returns:
            dict: {
                "success": True,
                "is_owner": bool  # True if the user owns the link, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. user or link does not exist
            }

        Constraints:
            - The user must exist in the system.
            - The link must exist in the system.
        """
        if link_id not in self.links:
            return { "success": False, "error": "ShortenedLink does not exist" }
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        is_owner = self.links[link_id]["owner_user_id"] == user_id
        return { "success": True, "is_owner": is_owner }

    def get_link_status(self, link_id: str) -> dict:
        """
        Return the current activation status ('is_active') of the specified shortened link.

        Args:
            link_id (str): The identifier of the shortened link to query.

        Returns:
            dict: {
                "success": True,
                "data": {"link_id": str, "is_active": bool},
            }
            or
            {
                "success": False,
                "error": str  # e.g., 'Shortened link not found'
            }

        Constraints:
            - The provided link_id must exist in the platform.
            - No ownership/privacy check is required for status-only query.
        """
        link = self.links.get(link_id)
        if not link:
            return { "success": False, "error": "Shortened link not found" }

        return {
            "success": True,
            "data": {
                "link_id": link_id,
                "is_active": link["is_active"]
            }
        }

    def list_link_click_events(self, link_id: str, requesting_user_id: str) -> dict:
        """
        Retrieve all ClickEvents (detailed) associated with a given ShortenedLink, 
        enforcing privacy constraints (only the link owner may access).

        Args:
            link_id (str): The link whose events are to be listed.
            requesting_user_id (str): The user performing the query (for privacy enforcement).

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[ClickEventInfo]}
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - link_id must exist in links.
            - Only the owner of the link (owner_user_id) can access analytics.
        """
        # Check if link exists
        link = self.links.get(link_id)
        if not link:
            return {"success": False, "error": "ShortenedLink does not exist"}

        # Privacy: Only the owner may access analytics
        if link["owner_user_id"] != requesting_user_id:
            return {"success": False, "error": "Permission denied: only owner may access link analytics"}

        # Gather ClickEvents
        events = [
            event for event in self.click_events.values()
            if event["link_id"] == link_id
        ]

        return {"success": True, "data": events}

    def count_click_events_by_country(self, link_id: str) -> dict:
        """
        Aggregate and count ClickEvents for a given ShortenedLink grouped by country.

        Args:
            link_id (str): The identifier of the ShortenedLink.

        Returns:
            dict:
                - success: True, data: Dict[str, int]
                    (country code/name -> click count) on success.
                - success: False, error: str
                    if provided link_id does not exist.

        Constraints:
            - The given link_id must exist in the system.
            - Aggregates all ClickEvents related to the link, regardless of activity status.
        """
        if link_id not in self.links:
            return { "success": False, "error": "Shortened link does not exist" }

        country_counts: Dict[str, int] = {}
        for event in self.click_events.values():
            if event["link_id"] == link_id:
                country = event["country"]
                if country not in country_counts:
                    country_counts[country] = 1
                else:
                    country_counts[country] += 1

        return { "success": True, "data": country_counts }

    def get_link_total_clicks(self, link_id: str) -> dict:
        """
        Compute the total number of ClickEvents (clicks) for a specific ShortenedLink.

        Args:
            link_id (str): The identifier for the ShortenedLink.

        Returns:
            dict: {
                "success": True,
                "data": int  # Total click count for this link_id
            }
            or
            {
                "success": False,
                "error": str  # If the link_id does not exist
            }

        Constraints:
            - The link_id must reference an existing ShortenedLink.
            - Includes all clicks for the link (regardless of active status).
        """
        if link_id not in self.links:
            return { "success": False, "error": "Link does not exist" }

        total = sum(1 for event in self.click_events.values() if event["link_id"] == link_id)
        return { "success": True, "data": total }

    def list_links_by_activity_status(self, user_id: str, is_active: bool) -> dict:
        """
        Retrieve all active or inactive shortened links for a specific user.

        Args:
            user_id (str): The ID of the user whose links are requested.
            is_active (bool): True for active links, False for inactive links.

        Returns:
            dict: {
                "success": True,
                "data": List[ShortenedLinkInfo]  # (possibly empty if no matching links)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist in the system.
            - Only links belonging to this user are considered.
            - Only links matching the specified activity status are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        filtered_links = [
            link_info for link_info in self.links.values()
            if link_info["owner_user_id"] == user_id and link_info["is_active"] == is_active
        ]

        return { "success": True, "data": filtered_links }

    def get_unique_click_events(self, link_id: str) -> dict:
        """
        Retrieve the unique ClickEvents for a given ShortenedLink, where uniqueness is
        determined by (timestamp, link_id, ip_address).

        Args:
            link_id (str): The ID of the shortened link for which to deduplicate ClickEvents.

        Returns:
            dict: {
                "success": True,
                "data": List[ClickEventInfo],  # List of unique click events.
            }
            or
            {
                "success": False,
                "error": str  # E.g., "ShortenedLink does not exist"
            }

        Constraints:
            - The specified link_id must reference an existing ShortenedLink.
            - For deduplication, only one ClickEvent with a given (timestamp, link_id, ip_address) is kept.
        """
        if link_id not in self.links:
            return {"success": False, "error": "ShortenedLink does not exist"}

        seen = set()
        unique_events = []
        for event in self.click_events.values():
            if event['link_id'] != link_id:
                continue
            dedup_key = (event['timestamp'], event['link_id'], event['ip_address'])
            if dedup_key not in seen:
                seen.add(dedup_key)
                unique_events.append(event)

        return {"success": True, "data": unique_events}


    def create_shortened_link(
        self, 
        owner_user_id: str, 
        original_url: str, 
        short_url: str
    ) -> dict:
        """
        Register a new ShortenedLink for an owner user, mapped to an original URL.

        Args:
            owner_user_id (str): User ID of the link owner (must exist).
            original_url (str): Destination URL to shorten.
            short_url (str): The desired short URL identifier (must be unique).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Shortened link created",
                        "link_id": <generated_link_id>,
                        "short_url": <short_url>
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - owner_user_id must reference an existing user.
            - short_url (and link_id) must be globally unique in self.links.
            - Each ShortenedLink is associated with one owner user.
        """
        # Check if the user exists
        if owner_user_id not in self.users:
            return { "success": False, "error": "Owner user does not exist." }
    
        # Ensure the short_url is not already in use
        for link in self.links.values():
            if link["short_url"] == short_url:
                return { "success": False, "error": "Short URL already in use." }
    
        # Generate unique link_id
        link_id = str(uuid.uuid4())
        while link_id in self.links:
            link_id = str(uuid.uuid4())

        # Prepare the ShortenedLinkInfo record
        now = datetime.utcnow().isoformat()
        shortened_link_info = {
            "link_id": link_id,
            "short_url": short_url,
            "original_url": original_url,
            "owner_user_id": owner_user_id,
            "created_at": now,
            "is_active": True,
        }
        self.links[link_id] = shortened_link_info

        return {
            "success": True,
            "message": "Shortened link created",
            "link_id": link_id,
            "short_url": short_url
        }

    def deactivate_shortened_link(self, link_id: str) -> dict:
        """
        Set a ShortenedLink's status to inactive (is_active=False).

        Args:
            link_id (str): The unique identifier of the shortened link.

        Returns:
            dict: {
                "success": True,
                "message": "ShortenedLink '<link_id>' has been deactivated."
            }
            or
            {
                "success": False,
                "error": "ShortenedLink not found." | "ShortenedLink is already inactive."
            }

        Constraints:
            - The link_id must exist.
            - If already inactive, return an error.
        """
        link_info = self.links.get(link_id)
        if not link_info:
            return { "success": False, "error": "ShortenedLink not found." }
        if link_info["is_active"] is False:
            return { "success": False, "error": "ShortenedLink is already inactive." }
        link_info["is_active"] = False
        self.links[link_id] = link_info  # Redundant for mutable dicts, but explicit.
        return {
            "success": True,
            "message": f"ShortenedLink '{link_id}' has been deactivated."
        }

    def activate_shortened_link(self, link_id: str) -> dict:
        """
        Set a ShortenedLink's status to active (is_active=True).

        Args:
            link_id (str): The ID of the ShortenedLink to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Shortened link <link_id> has been activated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - link_id must correspond to an existing ShortenedLink.
            - Operation is idempotent: activating an already-active link is still a success.
        """
        link = self.links.get(link_id)
        if not link:
            return { "success": False, "error": "Shortened link not found." }

        link["is_active"] = True
        return {
            "success": True,
            "message": f"Shortened link {link_id} has been activated."
        }

    def register_click_event(
        self,
        event_id: str,
        link_id: str,
        timestamp: str,
        referrer: str,
        device_type: str,
        country: str,
        ip_address: str,
        user_agent: str,
    ) -> dict:
        """
        Register a new ClickEvent if the link is active, valid, and no duplicate event exists.

        Args:
            event_id (str): Unique identifier for the ClickEvent.
            link_id (str): The shortened link identifier this event is for.
            timestamp (str): The timestamp of the click (ISO8601 or compatible).
            referrer (str): The referrer URL or identifier.
            device_type (str): The type of device (e.g., 'mobile', 'desktop').
            country (str): The country where the click was generated.
            ip_address (str): The IP address of the click source.
            user_agent (str): The browser or app user-agent string.

        Returns:
            dict: On success,
                { "success": True, "message": "ClickEvent registered" }
                On failure,
                { "success": False, "error": "reason for failure" }

        Constraints:
            - link_id must exist.
            - Link must be active (is_active == True).
            - event_id must be unique (not used).
            - Deduplication: no existing ClickEvent with same (timestamp, link_id, ip_address)
            - ClickEvent must reference a valid ShortenedLink.
        """
        # Validate link existence
        if link_id not in self.links:
            return { "success": False, "error": "ShortenedLink does not exist" }

        # Validate link is active
        link_info = self.links[link_id]
        if not link_info.get("is_active", False):
            return { "success": False, "error": "ShortenedLink is not active" }

        # Check event_id uniqueness
        if event_id in self.click_events:
            return { "success": False, "error": "ClickEvent with this event_id already exists" }

        # Deduplication: no identical (timestamp, link_id, ip_address)
        for ev in self.click_events.values():
            if (
                ev["timestamp"] == timestamp
                and ev["link_id"] == link_id
                and ev["ip_address"] == ip_address
            ):
                return { "success": False, "error": "Duplicate ClickEvent detected (timestamp, link_id, ip_address)" }

        # All checks passed; register the event
        new_event = {
            "event_id": event_id,
            "link_id": link_id,
            "timestamp": timestamp,
            "referrer": referrer,
            "device_type": device_type,
            "country": country,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        self.click_events[event_id] = new_event

        return { "success": True, "message": "ClickEvent registered" }

    def flag_duplicate_click_event(self, event_id: str = None) -> dict:
        """
        Mark or log ClickEvents identified as duplicates for future analytics accuracy or review.

        Args:
            event_id (str, optional): If provided, only scans for and flags duplicates matching this ClickEvent.
                If None, scans the whole click event set for duplicates system-wide.

        Returns:
            dict: 
            {
                "success": True,
                "message": "<X click event(s) flagged as duplicate>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Duplicates are defined as events with identical (link_id, timestamp, ip_address)
            - At least two events in such a group are required for flagging
            - "is_duplicate": True is set in ClickEventInfo for flagged events
        """
        # Helper to mark a group as duplicates, returns count newly flagged
        def mark_group_as_duplicate(group_ids):
            count = 0
            for eid in group_ids:
                event = self.click_events[eid]
                if not event.get("is_duplicate", False):
                    event["is_duplicate"] = True
                    count += 1
            return count

        if event_id:
            if event_id not in self.click_events:
                return {"success": False, "error": "ClickEvent not found"}

            target = self.click_events[event_id]
            key = (target["link_id"], target["timestamp"], target["ip_address"])
            matches = [
                eid for eid, ev in self.click_events.items()
                if (ev["link_id"], ev["timestamp"], ev["ip_address"]) == key
            ]
            if len(matches) < 2:
                return {"success": True, "message": "No duplicate events found to flag"}
            flagged = mark_group_as_duplicate(matches)
            return {"success": True, "message": f"{flagged} click event(s) flagged as duplicate"}
        else:
            # System-wide scan: group by compound key
            groups = defaultdict(list)
            for eid, ev in self.click_events.items():
                key = (ev["link_id"], ev["timestamp"], ev["ip_address"])
                groups[key].append(eid)
            total_flagged = 0
            for ids in groups.values():
                if len(ids) >= 2:
                    total_flagged += mark_group_as_duplicate(ids)
            return {"success": True, "message": f"{total_flagged} click event(s) flagged as duplicate"}

    def delete_shortened_link(self, link_id: str, request_user_id: str) -> dict:
        """
        Remove a ShortenedLink and all its associated analytics data.
        Only the owner of the link may perform this operation.

        Args:
            link_id (str): The unique identifier for the ShortenedLink to delete.
            request_user_id (str): The user requesting the deletion. Must be the link owner.

        Returns:
            dict: {
                "success": True,
                "message": "ShortenedLink and all associated analytics removed."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only the owner of the link may delete it.
            - All ClickEvents associated with the link must be deleted as well.
        """
        # Check if the link exists
        link = self.links.get(link_id)
        if link is None:
            return {"success": False, "error": "ShortenedLink does not exist."}

        # Check if request_user_id matches the owner of the link
        if link["owner_user_id"] != request_user_id:
            return {"success": False, "error": "Permission denied. Only the owner can delete this link."}

        # Remove ClickEvents associated with this link
        to_delete = [event_id for event_id, ce in self.click_events.items() if ce["link_id"] == link_id]
        for event_id in to_delete:
            del self.click_events[event_id]

        # Remove the link itself
        del self.links[link_id]

        return {"success": True, "message": "ShortenedLink and all associated analytics removed."}

    def anonymize_click_events(self) -> dict:
        """
        Remove or mask sensitive data (such as IP address and user agent) from all ClickEvents for privacy.

        Anonymized fields:
            - ip_address: Masked as 'ANONYMIZED'
            - user_agent: Masked as 'ANONYMIZED'

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the operation performed
            }

        Constraints:
            - Must only mask intended fields; do not delete ClickEvents or alter primary keys.
            - Can be invoked multiple times safely (idempotent).
        """
        num_events = 0
        for event in self.click_events.values():
            if event.get("ip_address") != "ANONYMIZED" or event.get("user_agent") != "ANONYMIZED":
                event["ip_address"] = "ANONYMIZED"
                event["user_agent"] = "ANONYMIZED"
                num_events += 1

        if len(self.click_events) == 0:
            return {
                "success": True,
                "message": "No ClickEvents to anonymize."
            }
        else:
            return {
                "success": True,
                "message": f"{num_events} ClickEvents have been anonymized."
            }

    def transfer_link_ownership(self, link_id: str, new_owner_user_id: str) -> dict:
        """
        Change the owner of the specified ShortenedLink to a different user.

        Args:
            link_id (str): The ID of the shortened link whose owner is being changed.
            new_owner_user_id (str): The ID of the new owner user.

        Returns:
            dict: {
                "success": True,
                "message": str  # A message describing the ownership transfer.
            }
            or
            {
                "success": False,
                "error": str  # Error message if link/user does not exist or is already owned by the target user.
            }

        Constraints:
            - The link must exist in the system.
            - The new user must exist in the system.
            - Each ShortenedLink must have a valid owner.
        """
        if link_id not in self.links:
            return {"success": False, "error": "ShortenedLink does not exist."}

        if new_owner_user_id not in self.users:
            return {"success": False, "error": "New owner user does not exist."}

        link_info = self.links[link_id]
        if link_info["owner_user_id"] == new_owner_user_id:
            return {"success": False, "error": "ShortenedLink is already owned by the specified user."}

        # Perform ownership transfer
        link_info["owner_user_id"] = new_owner_user_id
        self.links[link_id] = link_info

        return {
            "success": True,
            "message": f"Ownership of link {link_id} transferred to user {new_owner_user_id}"
        }

    def remove_click_event(self, event_id: str) -> dict:
        """
        Delete a specific ClickEvent record (admin or via privacy request).

        Args:
            event_id (str): The unique ID of the ClickEvent to delete.

        Returns:
            dict: {
                "success": True,
                "message": "ClickEvent <event_id> has been removed."
            }
            or
            {
                "success": False,
                "error": "ClickEvent not found."
            }

        Constraints:
            - The event_id must exist in click_events.
        """
        if event_id not in self.click_events:
            return {
                "success": False,
                "error": "ClickEvent not found."
            }
        del self.click_events[event_id]
        return {
            "success": True,
            "message": f"ClickEvent {event_id} has been removed."
        }


class URLAnalyticsShorteningPlatform(BaseEnv):
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

    def list_user_links(self, **kwargs):
        return self._call_inner_tool('list_user_links', kwargs)

    def get_link_by_short_url(self, **kwargs):
        return self._call_inner_tool('get_link_by_short_url', kwargs)

    def get_link_by_id(self, **kwargs):
        return self._call_inner_tool('get_link_by_id', kwargs)

    def check_link_ownership(self, **kwargs):
        return self._call_inner_tool('check_link_ownership', kwargs)

    def get_link_status(self, **kwargs):
        return self._call_inner_tool('get_link_status', kwargs)

    def list_link_click_events(self, **kwargs):
        return self._call_inner_tool('list_link_click_events', kwargs)

    def count_click_events_by_country(self, **kwargs):
        return self._call_inner_tool('count_click_events_by_country', kwargs)

    def get_link_total_clicks(self, **kwargs):
        return self._call_inner_tool('get_link_total_clicks', kwargs)

    def list_links_by_activity_status(self, **kwargs):
        return self._call_inner_tool('list_links_by_activity_status', kwargs)

    def get_unique_click_events(self, **kwargs):
        return self._call_inner_tool('get_unique_click_events', kwargs)

    def create_shortened_link(self, **kwargs):
        return self._call_inner_tool('create_shortened_link', kwargs)

    def deactivate_shortened_link(self, **kwargs):
        return self._call_inner_tool('deactivate_shortened_link', kwargs)

    def activate_shortened_link(self, **kwargs):
        return self._call_inner_tool('activate_shortened_link', kwargs)

    def register_click_event(self, **kwargs):
        return self._call_inner_tool('register_click_event', kwargs)

    def flag_duplicate_click_event(self, **kwargs):
        return self._call_inner_tool('flag_duplicate_click_event', kwargs)

    def delete_shortened_link(self, **kwargs):
        return self._call_inner_tool('delete_shortened_link', kwargs)

    def anonymize_click_events(self, **kwargs):
        return self._call_inner_tool('anonymize_click_events', kwargs)

    def transfer_link_ownership(self, **kwargs):
        return self._call_inner_tool('transfer_link_ownership', kwargs)

    def remove_click_event(self, **kwargs):
        return self._call_inner_tool('remove_click_event', kwargs)

