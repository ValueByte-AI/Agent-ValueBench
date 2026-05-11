# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict
from datetime import datetime, timezone
import re

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import time
from typing import List, Dict, Any
from typing import Optional
import uuid



class SubredditInfo(TypedDict):
    ddit_id: str  # Subreddit ID (typo preserved from spec)
    name: str
    description: str
    is_tracked: bool

class RedditUserInfo(TypedDict):
    name: str
    user_id: str
    last_contacted_timestamp: str  # Could be float/timestamp type if needed
    opt_out: bool
    scraped_from_subredd: str  # subreddit_id

class DirectMessageInfo(TypedDict):
    message_id: str
    sender: str
    recipient_username: str
    content: str
    sent_timestamp: str  # or float, depending on usage
    delivery_status: str
    tailored_contex: str  # typo preserved from spec

class MessageTemplateInfo(TypedDict):
    mplate_id: str  # typo preserved from spec
    topic: str
    conten: str  # typo preserved from spec

class _GeneratedEnvImpl:
    def __init__(self):
        # Subreddits being tracked: {ddit_id: SubredditInfo}
        self.subreddits: Dict[str, SubredditInfo] = {}

        # Users scraped from subreddits: {user_id: RedditUserInfo}
        self.users: Dict[str, RedditUserInfo] = {}

        # Direct messages sent or pending: {message_id: DirectMessageInfo}
        self.direct_messages: Dict[str, DirectMessageInfo] = {}

        # Message templates for outreach: {mplate_id: MessageTemplateInfo}
        self.message_templates: Dict[str, MessageTemplateInfo] = {}

        # Constraints:
        # - Users must be scraped from tracked subreddits before messaging.
        # - No user should receive the same message multiple times within a certain period (anti-spam/rate limit).
        # - Users who have opted out (opt_out=True) must not be messaged.
        # - Only send messages to users who were collected via scraping and not already contacted recently.
        # - Message delivery must be logged for compliance and tracking purposes.

    def _find_subreddit(self, subreddit_ref: str):
        subreddit = self.subreddits.get(subreddit_ref)
        if subreddit:
            return subreddit
        for value in self.subreddits.values():
            if value.get("ddit_id") == subreddit_ref:
                return value
        return None

    def _parse_timestamp(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        try:
            return float(text)
        except (TypeError, ValueError):
            pass

        iso_text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(iso_text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()

    def _slug_tokens(self, value: Any) -> List[str]:
        text = re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()
        if not text:
            return []
        return [token for token in text.split() if token]

    def _build_auto_scrape_payload(self, subreddit: SubredditInfo, count: int) -> list[tuple[str, str]]:
        stopwords = {
            "a",
            "an",
            "and",
            "for",
            "from",
            "in",
            "of",
            "on",
            "our",
            "the",
            "to",
            "with",
        }
        name_tokens = self._slug_tokens(subreddit.get("name", ""))
        desc_tokens = self._slug_tokens(subreddit.get("description", ""))
        base_tokens = [token for token in name_tokens if token not in stopwords]
        if not base_tokens:
            base_tokens = [token for token in desc_tokens if token not in stopwords]
        if not base_tokens:
            base_tokens = self._slug_tokens(subreddit.get("ddit_id", ""))
        if not base_tokens:
            base_tokens = ["reddit", "user"]

        primary = "_".join(base_tokens[:2])
        theme_tokens: List[str] = []
        for token in desc_tokens:
            if token in stopwords or token in base_tokens or token in theme_tokens:
                continue
            theme_tokens.append(token)

        suffixes = theme_tokens + [
            "guide",
            "weekly",
            "crew",
            "insider",
            "fan",
            "explorer",
            "update",
            "friend",
        ]

        used_usernames = {user.get("name") for user in self.users.values()}
        used_user_ids = set(self.users.keys())
        generated: list[tuple[str, str]] = []
        user_index = 1
        suffix_index = 0
        subreddit_id = str(subreddit.get("ddit_id", "sub"))

        while len(generated) < count:
            suffix = suffixes[suffix_index] if suffix_index < len(suffixes) else f"user{suffix_index + 1}"
            raw_username = f"{primary}_{suffix}"
            username = re.sub(r"_+", "_", raw_username.strip("_"))
            if username in used_usernames:
                suffix_index += 1
                continue

            user_id = f"auto_{subreddit_id}_{user_index:03d}"
            while user_id in used_user_ids:
                user_index += 1
                user_id = f"auto_{subreddit_id}_{user_index:03d}"

            generated.append((username, user_id))
            used_usernames.add(username)
            used_user_ids.add(user_id)
            user_index += 1
            suffix_index += 1

        return generated

    def get_tracked_subreddits(self) -> dict:
        """
        Returns a list of all currently tracked subreddits (is_tracked=True).

        Args:
            None

        Returns:
            dict:
              - success (bool): Whether the query was successful.
              - data (List[SubredditInfo]): List of tracked subreddits. May be empty if none are tracked.

        Constraints:
            - Only subreddits with is_tracked == True are returned.
        """
        tracked = [
            subreddit for subreddit in self.subreddits.values()
            if subreddit.get("is_tracked", False)
        ]
        return { "success": True, "data": tracked }

    def get_subreddit_by_name(self, subreddit_name: str) -> dict:
        """
        Retrieve full information for a specific subreddit by its name.

        Args:
            subreddit_name (str): The name of the subreddit to retrieve.

        Returns:
            dict:
              - When found:
                    {
                        "success": True,
                        "data": SubredditInfo
                    }
              - When missing:
                    {
                        "success": False,
                        "error": "Subreddit not found"
                    }

        Constraints:
            - Subreddit 'name' must match exactly (case-sensitive).
            - Only one subreddit should exist for a given name.
        """
        for subreddit in self.subreddits.values():
            if subreddit['name'] == subreddit_name:
                return {"success": True, "data": subreddit}
        return {"success": False, "error": "Subreddit not found"}

    def get_users_scraped_from_subreddit(self, subreddit_id: str) -> dict:
        """
        List all RedditUser records whose 'scraped_from_subredd' matches the given subreddit_id.

        Args:
            subreddit_id (str): The unique ID ('ddit_id') of the subreddit.

        Returns:
            dict: {
                "success": True,
                "data": List[RedditUserInfo],  # All matching users (empty list if none)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - subreddit_id must correspond to a tracked subreddit.
        """
        subreddit = self._find_subreddit(subreddit_id)
        if subreddit is None or not subreddit.get("is_tracked", False):
            return {"success": False, "error": "Subreddit not found or not tracked"}
    
        users = [
            user
            for user in self.users.values()
            if user.get("scraped_from_subredd") == subreddit_id
        ]
        return {"success": True, "data": users}

    def get_user_by_name(self, username: str) -> dict:
        """
        Retrieve detailed RedditUserInfo by username.

        Args:
            username (str): The Reddit username to query.

        Returns:
            dict:
                {"success": True, "data": RedditUserInfo} if user is found
                {"success": False, "error": "User not found"} if not found

        Constraints:
            - Username comparison is exact and case-sensitive.
            - No permission or compliance restrictions on this information query.
        """
        for user_info in self.users.values():
            if user_info["name"] == username:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "User not found"}

    def get_user_eligibility_for_messaging(self, user_id: str, now_timestamp: float) -> dict:
        """
        Check whether a Reddit user is eligible to receive a direct message.
    
        Args:
            user_id (str): The Reddit user's unique ID.
            now_timestamp (float): The current Unix timestamp (seconds since epoch) for rate limit checks.
    
        Returns:
            dict: {
                "success": True,
                "eligible": bool,
                "reasons": List[str]  # Reasons for ineligibility or empty if eligible,
                "user_info": RedditUserInfo (if found, optional for auditing)
            }
            Or
            {
                "success": False,
                "error": str  # Error message if user not found
            }
        
        Constraints Checked:
            - User must exist in database (scraped from a tracked subreddit).
            - User must not be opted out (opt_out == True).
            - User must not have been contacted within RATE_LIMIT_SECONDS.
            - User must be scraped from a (currently) tracked subreddit (optional; if the subreddit was tracked when scraped).
        """
        RATE_LIMIT_SECONDS = 24 * 3600  # 24 hours anti-spam
        reasons = []
    
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found or not scraped from a tracked subreddit."}
    
        # 1. Check opt-out
        if user.get("opt_out", False):
            reasons.append("User has opted out of messaging.")

        # 2. Check scraped from a tracked subreddit (current tracking status)
        scraped_subredd_id = user.get("scraped_from_subredd")
        subreddit_info = self._find_subreddit(scraped_subredd_id)
        if not scraped_subredd_id or not subreddit_info or not subreddit_info.get("is_tracked", False):
            reasons.append("User was not scraped from a currently tracked subreddit.")
    
        # 3. Check recent message (rate limiting)
        last_contacted = user.get("last_contacted_timestamp")
        if last_contacted:
            try:
                lc_ts = self._parse_timestamp(last_contacted)
                if lc_ts is not None and now_timestamp - lc_ts < RATE_LIMIT_SECONDS:
                    reasons.append("User was contacted too recently (rate limit applies).")
            except Exception:
                # Last contacted format issue, treat as not contacted recently
                pass

        eligible = (len(reasons) == 0)
        return {
            "success": True,
            "eligible": eligible,
            "reasons": reasons,
            "user_info": user
        }


    def get_recent_messages_to_user(
        self,
        recipient_username: str,
        time_window_seconds: float
    ) -> dict:
        """
        Retrieve all recent DirectMessages sent to a specific user within a time window (in seconds, up to now).

        Args:
            recipient_username (str): The username to check messages for.
            time_window_seconds (float): The window (in seconds) to look back from current time.

        Returns:
            dict: {
                "success": True,
                "data": List[DirectMessageInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - time_window_seconds must be positive.
            - Returns all DirectMessageInfo for the recipient within the window.
            - If no messages, returns an empty list (success).
        """
        if not isinstance(recipient_username, str) or not recipient_username.strip():
            return { "success": False, "error": "Invalid recipient_username" }

        if not isinstance(time_window_seconds, (int,float)) or time_window_seconds <= 0:
            return { "success": False, "error": "Invalid time_window_seconds; must be positive." }

        parsed_timestamps = []
        for msg in self.direct_messages.values():
            try:
                parsed = self._parse_timestamp(msg.get("sent_timestamp"))
                if parsed is not None:
                    parsed_timestamps.append(parsed)
            except (ValueError, TypeError):
                continue
        now = max(parsed_timestamps) if parsed_timestamps else time.time()
        cutoff = now - time_window_seconds

        result = []
        for msg in self.direct_messages.values():
            if msg.get("recipient_username") != recipient_username:
                continue
            # Handle sent_timestamp being string/float
            sent_ts = msg.get("sent_timestamp")
            try:
                sent_ts_float = self._parse_timestamp(sent_ts)
            except (ValueError, TypeError):
                # Skip messages with non-numeric timestamp
                continue
            if sent_ts_float is None:
                continue
            if sent_ts_float >= cutoff:
                result.append(msg)

        return { "success": True, "data": result }

    def get_message_templates_by_topic(self, topic: str) -> dict:
        """
        List message templates available for a specific outreach topic.

        Args:
            topic (str): The outreach topic to filter message templates by.

        Returns:
            dict: {
                'success': True,
                'data': List[MessageTemplateInfo],  # List of templates matching the topic (possibly empty)
            }
            or
            {
                'success': False,
                'error': str  # Error description if input is invalid.
            }
        Constraints:
            - topic must be a non-empty string.
        """
        if not isinstance(topic, str) or not topic.strip():
            return { "success": False, "error": "Invalid or empty topic provided" }

        templates = [
            template for template in self.message_templates.values()
            if template.get("topic") == topic
        ]
        return { "success": True, "data": templates }

    def get_message_template_by_id(self, mplate_id: str) -> dict:
        """
        Retrieve a message template (with attributes: mplate_id, topic, conten; typos preserved) by its mplate_id.

        Args:
            mplate_id (str): The unique ID of the message template.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": MessageTemplateInfo  # Dict for the template (mplate_id, topic, conten)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Message template not found"
                    }
        """
        template = self.message_templates.get(mplate_id)
        if not template:
            return { "success": False, "error": "Message template not found" }
        return { "success": True, "data": template }

    def get_message_log(self, delivery_status: str = None) -> dict:
        """
        Retrieve the log of all direct messages, optionally filtered by delivery status.

        Args:
            delivery_status (str, optional): If provided, only messages with this
                delivery_status (e.g., 'sent', 'pending', 'failed') will be returned.

        Returns:
            dict: {
                "success": True,
                "data": List[DirectMessageInfo],  # List of messages (possibly filtered; empty list ok)
            }

        Notes:
            - If no filter is provided, all messages will be returned.
            - No error will be raised for missing/empty results.
            - Filtering is case sensitive as stored.
        """
        if delivery_status is not None:
            expected = str(delivery_status).strip().lower()
            result = [
                message for message in self.direct_messages.values()
                if str(message.get("delivery_status", "")).strip().lower() == expected
            ]
        else:
            result = list(self.direct_messages.values())
        return {"success": True, "data": result}

    def get_users_opted_out(self) -> dict:
        """
        Return a list of all users who have opted out (opt_out == True).

        Returns:
            dict: {
                "success": True,
                "data": List[RedditUserInfo]  # All users from self.users where opt_out is True.
            }

        Constraints:
            - Only users with opt_out set to True are included.
            - Runs a read-only query, cannot fail unless internal state is corrupted.
        """
        opted_out_users = [
            user_info for user_info in self.users.values()
            if user_info.get("opt_out", False) is True
        ]
        return { "success": True, "data": opted_out_users }

    def get_unmessaged_users_from_subreddit(self, subreddit_id: str) -> dict:
        """
        List users scraped from a given subreddit that have not yet been contacted.

        Args:
            subreddit_id (str): The ID of the subreddit (ddit_id) to search in.

        Returns:
            dict: {
                "success": True,
                "data": List[RedditUserInfo],  # Users where scraped_from_subredd == subreddit_id and last_contacted_timestamp is empty/None/zero
            }
            or
            {
                "success": False,
                "error": str  # If subreddit does not exist or is not tracked
            }

        Constraints:
            - subreddit_id must exist in self.subreddits and be marked is_tracked == True.
            - Only users scraped from specified subreddit and never messaged are included.
        """
        # Check subreddit existence and tracking
        sub_info = self._find_subreddit(subreddit_id)
        if not sub_info:
            return { "success": False, "error": "Subreddit does not exist." }
        if not sub_info.get("is_tracked", False):
            return { "success": False, "error": "Subreddit is not being tracked." }

        # Gather all users from this subreddit who have not been contacted
        unmessaged_users = []
        for user in self.users.values():
            if user.get("scraped_from_subredd") != subreddit_id:
                continue
            last_contacted = user.get("last_contacted_timestamp")
            normalized = str(last_contacted).strip() if last_contacted is not None else ""
            if (not normalized) or normalized == "0":
                unmessaged_users.append(user)

        return { "success": True, "data": unmessaged_users }

    def scrape_reddit_usernames(
        self,
        subreddit_id: str,
        usernames: Optional[list[str]] = None,
        user_ids: Optional[list[str]] = None,
        count: int = 3,
    ) -> dict:
        """
        Extract (simulate scraping) usernames from a specified subreddit and add RedditUserInfo records.
    
        Args:
            subreddit_id (str): The ddit_id of the subreddit to scrape from.
            usernames (list[str], optional): Explicit Reddit usernames to add. If omitted, the tool will auto-discover representative usernames from the tracked subreddit metadata.
            user_ids (list[str], optional): List of corresponding user IDs (must match usernames in order). If not provided, user_id will be set as username in manual mode, or auto-generated in discovery mode.
            count (int, optional): Number of representative users to auto-discover when usernames are omitted. Defaults to 3.
    
        Returns:
            dict: {
                "success": True,
                "added": List[RedditUserInfo],  # Users actually newly added to the system
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        
        Constraints:
            - The subreddit must exist and be tracked (`is_tracked` is True).
            - Only usernames not already present in self.users will be added.
        """
        # 1. Check subreddit exists and is tracked
        sub = self._find_subreddit(subreddit_id)
        if not sub:
            return { "success": False, "error": "Subreddit not found" }
        if not sub.get("is_tracked", False):
            return { "success": False, "error": "Subreddit is not tracked" }
        # 2. Prepare mapping of username to user_id.
        if usernames is None:
            if not isinstance(count, int) or count <= 0:
                return { "success": False, "error": "count must be a positive integer when usernames are omitted" }
            uname_uid = self._build_auto_scrape_payload(sub, count)
        else:
            if not usernames:
                return { "success": True, "added": [] }  # No users to add
            if user_ids:
                if len(user_ids) != len(usernames):
                    return { "success": False, "error": "Length of user_ids does not match usernames" }
                uname_uid = list(zip(usernames, user_ids))
            else:
                uname_uid = [(uname, uname) for uname in usernames]

        added = []
        for uname, uid in uname_uid:
            # Check if user already exists
            if uid in self.users:
                continue  # skip duplicate
            # Add user info (default values: opt_out=False, last_contacted_timestamp="", etc.)
            user_info = {
                "name": uname,
                "user_id": uid,
                "last_contacted_timestamp": "",  # never contacted
                "opt_out": False,
                "scraped_from_subredd": subreddit_id
            }
            self.users[uid] = user_info
            added.append(user_info)
    
        return { "success": True, "added": added }


    def send_direct_message(
        self,
        sender: str,
        recipient_username: str,
        content: str,
        tailored_contex: str,
        sent_timestamp: Optional[str] = None,
        cooldown_seconds: int = 86400
    ) -> dict:
        """
        Compose and send a DM to a user. This operation will:
          - Check eligibility (user exists, is scraped from tracked subreddit, not opted out, not recently contacted).
          - Create and log a DirectMessage object.
          - Update the user's `last_contacted_timestamp`.

        Args:
            sender (str): Username or ID of the sender.
            recipient_username (str): Reddit username of the recipient (must exist in the user database).
            content (str): The message content.
            tailored_contex (str): Context of the message, e.g. outreach topic.
            sent_timestamp (str, optional): Timestamp to log (defaults to now).
            cooldown_seconds (int): Minimum seconds since last contact before another message (default 86400; 24 hours).

        Returns:
            dict: {
                "success": True,
                "message": "Direct message sent to <recipient_username>"
            }
            OR
            {
                "success": False,
                "error": "<error description>"
            }

        Constraints:
            - Users must be scraped from tracked subreddits before messaging.
            - No user should receive the same message multiple times within a certain period (anti-spam/rate limit).
            - Users who have opted out (opt_out=True) must not be messaged.
            - Message delivery must be logged for compliance and tracking purposes.
            - last_contacted_timestamp must be updated.
        """
        # Locate user by username
        user_obj = None
        for user in self.users.values():
            if user["name"] == recipient_username:
                user_obj = user
                break

        if not user_obj:
            return {"success": False, "error": "Recipient user not found in database"}

        # Check: User was scraped from a tracked subreddit
        subreddit_id = user_obj.get("scraped_from_subredd")
        subreddit = self._find_subreddit(subreddit_id)
        if not (subreddit and subreddit.get("is_tracked", False)):
            return {
                "success": False,
                "error": "User was not scraped from a tracked subreddit or subreddit is not currently tracked"
            }

        # Check: User has not opted out
        if user_obj.get("opt_out", False):
            return {"success": False, "error": "User has opted out; cannot send them messages"}

        # Check: Cooldown period/rate-limit
        last_contact = self._parse_timestamp(user_obj.get("last_contacted_timestamp", "0") or "0") or 0.0
        if sent_timestamp is not None:
            parsed_now = self._parse_timestamp(sent_timestamp)
            if parsed_now is None:
                return {"success": False, "error": "Invalid sent_timestamp format"}
            now = parsed_now
            stored_timestamp = str(sent_timestamp)
        else:
            now = time.time()
            stored_timestamp = str(now)
        if last_contact > 0 and (now - last_contact) < cooldown_seconds:
            return {
                "success": False,
                "error": f"User was already contacted too recently (last: {last_contact}); cooldown is {cooldown_seconds} seconds"
            }

        # Check: No duplicate message recently sent (same content within cooldown)
        for msg in self.direct_messages.values():
            if (
                msg["recipient_username"] == recipient_username
                and msg["content"] == content
            ):
                # Compare time difference
                msg_time = self._parse_timestamp(msg.get("sent_timestamp", "0") or "0") or 0.0
                if (now - msg_time) < cooldown_seconds:
                    return {
                        "success": False,
                        "error": "This message was already sent to the user recently (anti-spam constraint)"
                    }

        # Compose the new DirectMessage object
        message_id = str(uuid.uuid4())
        dm_info = {
            "message_id": message_id,
            "sender": sender,
            "recipient_username": recipient_username,
            "content": content,
            "sent_timestamp": stored_timestamp,
            "delivery_status": "pending",
            "tailored_contex": tailored_contex,
        }
        self.direct_messages[message_id] = dm_info

        # Update the user's last_contacted_timestamp
        user_obj["last_contacted_timestamp"] = stored_timestamp

        return {
            "success": True,
            "message": f"Direct message sent to {recipient_username}",
            "message_id": message_id,
            "sent_timestamp": stored_timestamp,
            "delivery_status": "pending",
        }

    def log_message_delivery(
        self,
        message_id: str,
        delivery_status: str,
        sent_timestamp: Optional[str] = None,
    ) -> dict:
        """
        Record (update) the delivery status and sent timestamp for a DirectMessage.

        Args:
            message_id (str): The unique ID of the DirectMessage to update.
            delivery_status (str): The delivery status ("delivered", "failed", etc).
            sent_timestamp (str, optional): The time the delivery status was updated. If omitted, the current time is recorded automatically.

        Returns:
            dict: {
                "success": True,
                "message": "Delivery status for message <message_id> updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - message_id must exist in direct_messages.
            - The operation is used to maintain compliance/tracking logs.
        """
        if message_id not in self.direct_messages:
            return { "success": False, "error": "Message ID not found." }

        if sent_timestamp is None or not str(sent_timestamp).strip():
            sent_timestamp = str(time.time())

        self.direct_messages[message_id]["delivery_status"] = delivery_status
        self.direct_messages[message_id]["sent_timestamp"] = sent_timestamp

        return { "success": True, "message": f"Delivery status for message {message_id} updated." }

    def mark_user_opted_out(self, user_id: str) -> dict:
        """
        Set a Reddit user's opt_out status to True, making them ineligible for future outreach.

        Args:
            user_id (str): The unique Reddit user identifier.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "User marked as opted out."}
                - On error (user not found):
                    {"success": False, "error": "User not found."}
                - If already opted out (idempotent success):
                    {"success": True, "message": "User was already opted out."}
        Constraints:
            - User must exist in the system.
            - Opt_out is set to True, regardless of prior value.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
        if user["opt_out"]:
            return {"success": True, "message": "User was already opted out."}
        user["opt_out"] = True
        self.users[user_id] = user
        return {"success": True, "message": "User marked as opted out."}

    def add_tracked_subreddit(self, ddit_id: str, name: str, description: str) -> dict:
        """
        Mark a subreddit as tracked to allow subsequent scraping.

        Args:
            ddit_id (str): Unique subreddit ID.
            name (str): Subreddit display name.
            description (str): Subreddit description.

        Returns:
            dict:
                - On success: { "success": True, "message": "Subreddit <name> is now tracked." }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - If the subreddit with ddit_id is already tracked (is_tracked=True), do not add/modify and return error.
            - If the subreddit with ddit_id exists but is_tracked=False, set is_tracked=True and update details.
            - If ddit_id is new, add it as tracked.
        """

        # Basic input validation
        if not ddit_id or not name:
            return {"success": False, "error": "Subreddit ID and name are required."}

        existing = self.subreddits.get(ddit_id)
        if existing:
            if existing.get("is_tracked"):
                return {"success": False, "error": "Subreddit already tracked."}
            else:
                # Update to tracked and refresh name/description if needed
                existing.update({
                    "name": name,
                    "description": description,
                    "is_tracked": True
                })
                self.subreddits[ddit_id] = existing
                return {"success": True, "message": f"Subreddit {name} is now tracked."}
        else:
            # Add as tracked
            self.subreddits[ddit_id] = {
                "ddit_id": ddit_id,
                "name": name,
                "description": description,
                "is_tracked": True
            }
            return {"success": True, "message": f"Subreddit {name} is now tracked."}

    def remove_tracked_subreddit(self, ddit_id: str) -> dict:
        """
        Mark a subreddit as untracked, preventing further user scraping.

        Args:
            ddit_id (str): The unique ID of the subreddit to untrack.

        Returns:
            dict: {
                "success": True,
                "message": "Subreddit <ddit_id> marked as untracked."
            }
            or
            {
                "success": False,
                "error": "Subreddit not found" | "Subreddit is already untracked"
            }

        Constraints:
            - Subreddit must exist in database.
            - If subreddit is already untracked, operation fails.
        """
        subreddit = self.subreddits.get(ddit_id)
        if not subreddit:
            return { "success": False, "error": "Subreddit not found" }
        if not subreddit["is_tracked"]:
            return { "success": False, "error": "Subreddit is already untracked" }
        subreddit["is_tracked"] = False
        self.subreddits[ddit_id] = subreddit
        return { "success": True, "message": f"Subreddit {ddit_id} marked as untracked." }

    def create_message_template(self, mplate_id: str, topic: str, conten: str) -> dict:
        """
        Add a new message template for future outreach.

        Args:
            mplate_id (str): Unique message template ID (must not exist already).
            topic (str): The topic or context for this message template.
            conten (str): The message template content (body). Note: 'conten' typo preserved per schema.

        Returns:
            dict:
                On success: { "success": True, "message": "Message template '<mplate_id>' added." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - mplate_id must be unique within message_templates.
            - topic and conten cannot be empty.
        """
        if not mplate_id or not topic or not conten:
            return {"success": False, "error": "All fields (mplate_id, topic, conten) are required and must not be empty."}

        if mplate_id in self.message_templates:
            return {"success": False, "error": "Message template ID already exists."}
    
        self.message_templates[mplate_id] = {
            "mplate_id": mplate_id,
            "topic": topic,
            "conten": conten
        }

        return {"success": True, "message": f"Message template '{mplate_id}' added."}

    def update_message_template(self, mplate_id: str, topic: str = None, conten: str = None) -> dict:
        """
        Modify the topic and/or conten (content) of an existing message template.

        Args:
            mplate_id (str): ID of the message template to update.
            topic (str, optional): New topic for the template (if updating).
            conten (str, optional): New content for the template (if updating).

        Returns:
            dict:
                Success: { "success": True, "message": "Message template updated." }
                Failure: { "success": False, "error": <error_message> }

        Constraints:
            - mplate_id must exist in self.message_templates.
            - At least one of topic or conten should be provided for an actual update.
            - Will update only those fields that are non-None.
        """
        template = self.message_templates.get(mplate_id)
        if not template:
            return { "success": False, "error": "Message template not found." }

        if topic is None and conten is None:
            return { "success": False, "error": "No update parameters provided." }

        updated = False
        if topic is not None:
            template['topic'] = topic
            updated = True
        if conten is not None:
            template['conten'] = conten
            updated = True

        if updated:
            self.message_templates[mplate_id] = template
            return { "success": True, "message": "Message template updated." }
        else:
            # Should not reach here, but just in case
            return { "success": False, "error": "Nothing updated." }

    def delete_message_template(self, mplate_id: str) -> dict:
        """
        Remove a message template from the template catalog.
    
        Args:
            mplate_id (str): The ID of the message template to delete.

        Returns:
            dict: 
                - If successful: {
                    "success": True,
                    "message": "Message template <ID> deleted."
                  }
                - If not found: {
                    "success": False,
                    "error": "Message template not found."
                  }

        Constraints:
            - No restrictions on deleting a template, 
              but must exist in the catalog to delete.
        """
        if mplate_id not in self.message_templates:
            return {
                "success": False,
                "error": "Message template not found."
            }
        del self.message_templates[mplate_id]
        return {
            "success": True,
            "message": f"Message template {mplate_id} deleted."
        }

    def update_user_last_contacted(self, user_id: str, timestamp: str) -> dict:
        """
        Update the last_contacted_timestamp for the specified Reddit user.

        Args:
            user_id (str): Reddit user's unique ID.
            timestamp (str): New value for last_contacted_timestamp (ISO8601 or epoch string).

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "User last_contacted_timestamp updated"
                }
                OR
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The user with user_id must exist in the system database.
            - No side effects beyond updating last_contacted_timestamp for the user.

        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        self.users[user_id]["last_contacted_timestamp"] = timestamp
        return { "success": True, "message": "User last_contacted_timestamp updated" }

    def remove_user_from_database(self, user_id: str) -> dict:
        """
        Delete a RedditUser from the system.

        Args:
            user_id (str): The unique Reddit user ID to be removed.

        Returns:
            dict:
                - If successful: {"success": True, "message": "User <user_id> removed from database"}
                - If user not found: {"success": False, "error": "User not found"}

        Constraints:
            - The user must exist in the database.
            - Associated message logs are not deleted by this operation.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        del self.users[user_id]
        return {"success": True, "message": f"User {user_id} removed from database"}


class RedditUserInteractionManagementSystem(BaseEnv):
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

    def get_tracked_subreddits(self, **kwargs):
        return self._call_inner_tool('get_tracked_subreddits', kwargs)

    def get_subreddit_by_name(self, **kwargs):
        return self._call_inner_tool('get_subreddit_by_name', kwargs)

    def get_users_scraped_from_subreddit(self, **kwargs):
        return self._call_inner_tool('get_users_scraped_from_subreddit', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_eligibility_for_messaging(self, **kwargs):
        return self._call_inner_tool('get_user_eligibility_for_messaging', kwargs)

    def get_recent_messages_to_user(self, **kwargs):
        return self._call_inner_tool('get_recent_messages_to_user', kwargs)

    def get_message_templates_by_topic(self, **kwargs):
        return self._call_inner_tool('get_message_templates_by_topic', kwargs)

    def get_message_template_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_template_by_id', kwargs)

    def get_message_log(self, **kwargs):
        return self._call_inner_tool('get_message_log', kwargs)

    def get_users_opted_out(self, **kwargs):
        return self._call_inner_tool('get_users_opted_out', kwargs)

    def get_unmessaged_users_from_subreddit(self, **kwargs):
        return self._call_inner_tool('get_unmessaged_users_from_subreddit', kwargs)

    def scrape_reddit_usernames(self, **kwargs):
        return self._call_inner_tool('scrape_reddit_usernames', kwargs)

    def send_direct_message(self, **kwargs):
        return self._call_inner_tool('send_direct_message', kwargs)

    def log_message_delivery(self, **kwargs):
        return self._call_inner_tool('log_message_delivery', kwargs)

    def mark_user_opted_out(self, **kwargs):
        return self._call_inner_tool('mark_user_opted_out', kwargs)

    def add_tracked_subreddit(self, **kwargs):
        return self._call_inner_tool('add_tracked_subreddit', kwargs)

    def remove_tracked_subreddit(self, **kwargs):
        return self._call_inner_tool('remove_tracked_subreddit', kwargs)

    def create_message_template(self, **kwargs):
        return self._call_inner_tool('create_message_template', kwargs)

    def update_message_template(self, **kwargs):
        return self._call_inner_tool('update_message_template', kwargs)

    def delete_message_template(self, **kwargs):
        return self._call_inner_tool('delete_message_template', kwargs)

    def update_user_last_contacted(self, **kwargs):
        return self._call_inner_tool('update_user_last_contacted', kwargs)

    def remove_user_from_database(self, **kwargs):
        return self._call_inner_tool('remove_user_from_database', kwargs)
