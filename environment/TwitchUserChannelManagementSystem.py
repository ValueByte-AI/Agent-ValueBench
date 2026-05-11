# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import uuid
from datetime import datetime
from typing import Optional, Dict
from datetime import datetime, timezone
import time



class UserInfo(TypedDict):
    _id: str
    username: str
    profile_metadata: dict
    account_type: str  # "streamer" or "viewer"
    channel_id: Optional[str]  # May be None if user has no channel

class ChannelInfo(TypedDict):
    channel_id: str
    user_id: str
    channel_metadata: dict
    current_status: str  # "live" or "offline"
    current_stream_id: Optional[str]  # None if no stream is live

class StreamInfo(TypedDict):
    stream_id: str
    channel_id: str
    start_time: str
    end_time: Optional[str]
    status: str  # "live" or "offline"
    preview_image_url: str
    stream_metadata: dict

class BroadcastInfo(TypedDict):
    broadcast_id: str
    channel_id: str
    stream_id: str
    archive_url: str
    created_at: str
    metadata: dict

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Channels: {channel_id: ChannelInfo}
        self.channels: Dict[str, ChannelInfo] = {}
        # Streams (live or archived): {stream_id: StreamInfo}
        self.streams: Dict[str, StreamInfo] = {}
        # Past broadcasts: {broadcast_id: BroadcastInfo}
        self.broadcasts: Dict[str, BroadcastInfo] = {}

        # Constraints:
        # - Each channel is associated with exactly one user.
        # - A channel may have zero or one live stream at a time.
        # - Stream previews are updated in real time only when the channel is live.
        # - Only streams/broadcasts belonging to the queried channel/user are visible in their profile.

    @staticmethod
    def _is_null_like_stream_id(value: Any) -> bool:
        return value in (None, "", "null", "None")

    def _recalculate_channel_storage_usage(self, channel_id: str) -> None:
        channel = self.channels.get(channel_id)
        if not channel:
            return
        metadata = channel.get("channel_metadata")
        if not isinstance(metadata, dict):
            return
        total_size = 0
        for broadcast in self.broadcasts.values():
            if broadcast.get("channel_id") != channel_id:
                continue
            size = broadcast.get("metadata", {}).get("size_gb", 0)
            if isinstance(size, (int, float)):
                total_size += size
        metadata["storage_used_gb"] = total_size

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve the user profile and core metadata using their username.

        Args:
            username (str): The Twitch user's username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo, # On success
            }
            or
            {
                "success": False,
                "error": str, # e.g. "User not found"
            }

        Notes:
            - Username comparison is case-sensitive. If case-insensitive match is required, modify logic accordingly.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve the full user profile for the given unique user _id.

        Args:
            _id (str): Unique user identifier.

        Returns:
            dict: 
                - If successful:
                    {
                      "success": True,
                      "data": UserInfo  # Complete profile info as dict
                    }
                - If not found:
                    {
                      "success": False,
                      "error": "User does not exist"
                    }
        Constraints:
            - The _id must exist in the users dictionary.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }
        return { "success": True, "data": user }

    def list_users_by_account_type(self, account_type: str) -> dict:
        """
        List all users filtered by account type.

        Args:
            account_type (str): The type of account to filter by ("streamer" or "viewer").

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]
            }
            or
            {
                "success": False,
                "error": str  # e.g. invalid account type
            }

        Constraints:
            - account_type must be "streamer" or "viewer".
            - If no user of the type exists, return empty data list with success True.
        """
        allowed_types = {"streamer", "viewer"}
        if account_type not in allowed_types:
            return { "success": False, "error": "Invalid account type" }

        result = [
            user for user in self.users.values()
            if user["account_type"] == account_type
        ]
        return { "success": True, "data": result }

    def get_channel_by_user_id(self, user_id: str) -> dict:
        """
        Look up a channel owned by the specified user_id.

        Args:
            user_id (str): The user_id of the channel owner.

        Returns:
            dict:
              - If found: {"success": True, "data": ChannelInfo}
              - If not found: {"success": False, "error": "No channel found for user_id"}

        Constraints:
            - Each channel is associated with exactly one user.
        """
        for channel in self.channels.values():
            if channel["user_id"] == user_id:
                return {"success": True, "data": channel}
        return {"success": False, "error": "No channel found for user_id"}

    def get_channel_by_id(self, channel_id: str) -> dict:
        """
        Retrieve the channel information by its unique channel_id.

        Args:
            channel_id (str): The unique identifier of the channel.

        Returns:
            dict: 
                - On success: { "success": True, "data": ChannelInfo }
                - On failure: { "success": False, "error": "Channel not found" }

        Constraints:
            - Only returns the channel info if it exists in the system.
        """
        channel_info = self.channels.get(channel_id)
        if not channel_info:
            return { "success": False, "error": "Channel not found" }

        return { "success": True, "data": channel_info }

    def get_channel_status(self, channel_id: str) -> dict:
        """
        Query the current live/offline status of a channel.

        Args:
            channel_id (str): The unique identifier of the channel.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "channel_id": str,
                            "current_status": str  # "live" or "offline"
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - channel_id must exist in the system.
        """
        channel = self.channels.get(channel_id)
        if not channel:
            return { "success": False, "error": "Channel does not exist" }

        return {
            "success": True,
            "data": {
                "channel_id": channel_id,
                "current_status": channel["current_status"]
            }
        }

    def get_current_stream_by_channel_id(self, channel_id: str) -> dict:
        """
        Fetch the currently live stream (if any) for a specified channel.

        Args:
            channel_id (str): The ID of the channel to query.

        Returns:
            dict: {
                "success": True,
                "data": StreamInfo or None  # StreamInfo if a live stream exists, otherwise None
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., channel does not exist
            }

        Constraints:
            - Each channel may have 0 or 1 live stream at a time.
            - Only the stream with status "live" is considered.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return {"success": False, "error": "Channel does not exist"}

        current_stream_id = channel.get("current_stream_id")
        if channel.get("current_status") != "live" or not current_stream_id:
            return {"success": True, "data": None}

        stream = self.streams.get(current_stream_id)
        if not stream or stream.get("status") != "live":
            return {"success": True, "data": None}  # Data inconsistency fallback

        return {"success": True, "data": stream}

    def get_most_recent_stream_by_channel_id(self, channel_id: str) -> dict:
        """
        Retrieve the most recently started stream (live or offline) for a given channel.

        Args:
            channel_id (str): The channel's unique identifier.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": StreamInfo or None  # StreamInfo of the most recently started stream, or None if no streams for this channel
                }
                On failure: {
                    "success": False,
                    "error": str  # Error message (e.g., invalid channel id)
                }

        Constraints:
            - Only considers streams with matching channel_id.
        """
        if channel_id not in self.channels:
            return {"success": False, "error": "Channel does not exist"}

        # Gather all streams for this channel
        channel_streams = [
            stream for stream in self.streams.values()
            if stream["channel_id"] == channel_id
        ]
        if not channel_streams:
            return {"success": True, "data": None}

        # Pick the stream with the latest start_time
        # Assuming start_time is an ISO8601 string or similar sortable format.
        most_recent_stream = max(channel_streams, key=lambda s: s["start_time"])
        return {"success": True, "data": most_recent_stream}

    def get_stream_by_id(self, stream_id: str) -> dict:
        """
        Retrieve stream details by stream_id.

        Args:
            stream_id (str): The unique identifier of the stream session.

        Returns:
            dict: {
                "success": True,
                "data": StreamInfo  # The stream's information, if found.
            }
            or
            {
                "success": False,
                "error": "Stream not found"
            }

        Constraints:
            - Only streams existing in the system can be accessed.
        """
        if not stream_id or stream_id not in self.streams:
            return { "success": False, "error": "Stream not found" }
        return { "success": True, "data": self.streams[stream_id] }

    def get_stream_preview_url(self, stream_id: str) -> dict:
        """
        Retrieve the latest preview image URL for the given stream.

        Args:
            stream_id (str): The unique id of the stream.

        Returns:
            dict:
                {
                    "success": True,
                    "data": str  # preview_image_url for the stream
                }
                or
                {
                    "success": False,
                    "error": str  # Error reason, such as stream not found
                }
        Constraints:
            - Stream must exist in self.streams.
        """
        stream_info = self.streams.get(stream_id)
        if not stream_info:
            return {"success": False, "error": "Stream not found"}
        return {"success": True, "data": stream_info["preview_image_url"]}

    def get_latest_stream_preview_for_username(self, username: str) -> dict:
        """
        Fetch the most recent (live or latest archived) stream preview image URL 
        for the channel owned by the given username.

        Args:
            username (str): The Twitch username whose channel's latest preview is requested.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "preview_image_url": str,
                    "source": "live" or "archived",
                    "stream_id": str
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only return streams belonging to the user's channel.
            - Prefer live preview; otherwise, return most recent archived/ended stream preview.
        """
        # 1. Find user
        user = next((u for u in self.users.values() if u["username"] == username), None)
        if user is None:
            return {"success": False, "error": "User not found"}
        channel_id = user.get("channel_id")
        if not channel_id:
            return {"success": False, "error": "User does not have a channel"}
        # 2. Find channel
        channel = self.channels.get(channel_id)
        if not channel:
            return {"success": False, "error": "Channel not found"}
        # 3. If live, get live preview image
        if channel["current_status"] == "live" and channel["current_stream_id"]:
            stream = self.streams.get(channel["current_stream_id"])
            if stream and stream["status"] == "live":
                return {
                    "success": True,
                    "data": {
                        "preview_image_url": stream["preview_image_url"],
                        "source": "live",
                        "stream_id": stream["stream_id"]
                    }
                }
        # 4. If not live, find latest ended/any stream for this channel
        streams = [
            s for s in self.streams.values()
            if s["channel_id"] == channel_id
        ]
        if not streams:
            return {"success": False, "error": "No streams found for this channel"}
        # Find stream with latest start_time
        try:
            latest_stream = max(
                streams,
                key=lambda s: s["start_time"] if s["start_time"] is not None else ""
            )
            return {
                "success": True,
                "data": {
                    "preview_image_url": latest_stream["preview_image_url"],
                    "source": "archived" if latest_stream["status"] != "live" else "live",
                    "stream_id": latest_stream["stream_id"]
                }
            }
        except Exception:
            return {"success": False, "error": "Unable to determine latest stream preview"}

    def list_streams_by_channel_id(self, channel_id: str) -> dict:
        """
        Return all stream sessions for a specified channel, ordered by start_time.

        Args:
            channel_id (str): The ID of the channel whose streams to list.

        Returns:
            dict: {
                "success": True,
                "data": List[StreamInfo],  # Stream infos in ascending order of start_time
            }
            or
            {
                "success": False,
                "error": str  # Description of why the request failed
            }

        Constraints:
            - The channel_id must exist in the system.
            - Only streams belonging to the given channel are returned.
            - The result is ordered chronologically by start_time.
        """
        if channel_id not in self.channels:
            return {"success": False, "error": "Channel does not exist"}

        # Filter streams by channel_id
        matching_streams = [
            stream for stream in self.streams.values()
            if stream["channel_id"] == channel_id
        ]

        # Sort streams by start_time (ISO string, so lexicographical order works)
        matching_streams.sort(key=lambda x: x.get("start_time", ""))

        return {"success": True, "data": matching_streams}

    def list_broadcasts_by_channel_id(self, channel_id: str) -> dict:
        """
        List all archived broadcasts for a specified channel.

        Args:
            channel_id (str): The unique identifier for the channel.

        Returns:
            dict: {
                "success": True,
                "data": List[BroadcastInfo]  # List of broadcast info. Can be empty if no broadcasts.
            }
            or
            {
                "success": False,
                "error": str  # On error, e.g., if the channel does not exist.
            }

        Constraints:
            - The given channel_id must exist.
            - Only broadcasts belonging to the channel are returned.
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }

        result = [
            binfo for binfo in self.broadcasts.values()
            if binfo["channel_id"] == channel_id
        ]
        return { "success": True, "data": result }

    def get_broadcast_by_id(self, broadcast_id: str) -> dict:
        """
        Retrieve broadcast (archive) information for the specified broadcast_id.

        Args:
            broadcast_id (str): The unique identifier of the broadcast to look up.

        Returns:
            dict:
                - On success:
                  {"success": True, "data": BroadcastInfo}
                - On failure (not found):
                  {"success": False, "error": "Broadcast not found"}
        Constraints:
            - Only a broadcast with the given ID is returned, if it exists.
        """
        broadcast = self.broadcasts.get(broadcast_id)
        if broadcast is None:
            return {"success": False, "error": "Broadcast not found"}
        return {"success": True, "data": broadcast}

    def get_broadcasts_for_stream_id(self, stream_id: str) -> dict:
        """
        List all broadcasts related to a specific stream.

        Args:
            stream_id (str): The unique ID of the stream to search broadcasts for.

        Returns:
            dict: {
                "success": True,
                "data": List[BroadcastInfo]  # List of broadcasts associated with the stream
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. stream does not exist)
            }

        Constraints:
            - Only broadcasts whose stream_id matches the provided stream_id are returned.
            - If the stream_id is invalid (does not exist), an error is returned.
        """
        if stream_id not in self.streams:
            return {"success": False, "error": "Stream does not exist"}

        matching_broadcasts = [
            broadcast_info for broadcast_info in self.broadcasts.values()
            if broadcast_info["stream_id"] == stream_id
        ]

        return {"success": True, "data": matching_broadcasts}

    def get_channel_metadata(self, channel_id: str) -> dict:
        """
        Retrieve the metadata/settings for a specific channel given by its channel_id.

        Args:
            channel_id (str): The ID of the channel whose metadata/settings are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": dict  # The channel_metadata dictionary (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason why metadata could not be retrieved (e.g. channel not found)
            }

        Constraints:
            - Channel must exist in the system.
        """
        channel = self.channels.get(channel_id)
        if not channel:
            return {"success": False, "error": "Channel not found"}
    
        # Safely return the metadata; if it's None, return an empty dict.
        metadata = channel.get("channel_metadata") if channel.get("channel_metadata") is not None else {}
        return {"success": True, "data": metadata}

    def get_user_profile_metadata(self, user_id: str) -> dict:
        """
        Return the detailed profile metadata for a user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                Success: { "success": True, "data": <profile_metadata dict> }
                Failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user must exist in the system.
            - Only the user's own profile_metadata is returned.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user.get("profile_metadata", {}) }

    def update_user_profile_metadata(self, user_id: str, new_profile_metadata: dict) -> dict:
        """
        Edit or modify a user's profile metadata.

        Args:
            user_id (str): The user ID of the user whose profile metadata should be updated.
            new_profile_metadata (dict): The new profile metadata to assign (full replacement).

        Returns:
            dict: {
                "success": True,
                "message": "User profile metadata updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - User with user_id must exist.
            - new_profile_metadata must be a dict.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found."}
        if not isinstance(new_profile_metadata, dict):
            return {"success": False, "error": "Invalid metadata format."}
        user["profile_metadata"] = new_profile_metadata
        return {"success": True, "message": "User profile metadata updated."}

    def update_channel_metadata(self, channel_id: str, new_metadata: dict) -> dict:
        """
        Update the metadata/settings for a channel.

        Args:
            channel_id (str): The ID of the channel to update.
            new_metadata (dict): The new metadata/settings for the channel.

        Returns:
            dict:
                - {"success": True, "message": "Channel metadata updated."}
                - {"success": False, "error": "Channel not found"}
                - {"success": False, "error": "Invalid metadata"}
    
        Constraints:
            - The specified channel must exist in the system.
        """
        if channel_id not in self.channels:
            return {"success": False, "error": "Channel not found"}
        if not isinstance(new_metadata, dict):
            return {"success": False, "error": "Invalid metadata"}

        self.channels[channel_id]["channel_metadata"] = new_metadata
        return {"success": True, "message": "Channel metadata updated."}


    def start_stream(
        self,
        channel_id: str,
        preview_image_url: Optional[str] = None,
        stream_metadata: Optional[Dict] = None
    ) -> dict:
        """
        Set a channel and a stream as live by creating a new stream session.

        Args:
            channel_id (str): The channel's unique identifier to start the stream on.
            preview_image_url (Optional[str]): The URL of the stream's preview image (can default to a placeholder).
            stream_metadata (Optional[dict]): Metadata for the new stream (may be empty).

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Stream started on channel <channel_id> with stream_id <stream_id>"}
                - On failure:
                    {"success": False, "error": "reason"}

        Constraints:
            - Channel must exist.
            - Channel must NOT already have a live stream (enforced: only one live stream per channel).
            - Stream info and channel state must be updated atomically.
        """
        # Check if channel exists
        ch = self.channels.get(channel_id)
        if not ch:
            return {"success": False, "error": "Channel does not exist"}

        # Check whether a real live stream already exists for this channel.
        live_stream = next(
            (
                stream for stream in self.streams.values()
                if stream.get("channel_id") == channel_id and stream.get("status") == "live"
            ),
            None,
        )
        if live_stream is not None:
            ch["current_status"] = "live"
            ch["current_stream_id"] = live_stream["stream_id"]
            self.channels[channel_id] = ch
            return {"success": False, "error": "Channel already has a live stream"}

        # If the public channel state claims a stale stream reference while no live stream exists,
        # normalize it so start_stream matches the externally visible offline state.
        if ch.get("current_status") != "live":
            if self._is_null_like_stream_id(ch.get("current_stream_id")) or ch.get("current_stream_id") not in self.streams:
                ch["current_stream_id"] = None
        elif self._is_null_like_stream_id(ch.get("current_stream_id")):
            ch["current_status"] = "offline"
            ch["current_stream_id"] = None

        # Generate new stream_id
        stream_id = str(uuid.uuid4())
        start_time = datetime.utcnow().isoformat() + "Z"
        preview_url = preview_image_url if preview_image_url else "https://twitch.tv/placeholder_preview.jpg"
        metadata = stream_metadata if stream_metadata else {}

        # Create new stream entry
        stream_info = {
            "stream_id": stream_id,
            "channel_id": channel_id,
            "start_time": start_time,
            "end_time": None,
            "status": "live",
            "preview_image_url": preview_url,
            "stream_metadata": metadata
        }
        self.streams[stream_id] = stream_info

        # Update channel status
        ch["current_status"] = "live"
        ch["current_stream_id"] = stream_id
        self.channels[channel_id] = ch  # Save back in case of dict copy (if necessary)

        return {
            "success": True,
            "message": f"Stream started on channel {channel_id} with stream_id {stream_id}"
        }


    def end_stream(self, channel_id: str) -> dict:
        """
        Mark a currently live stream as ended for the given channel.

        Args:
            channel_id (str): The ID of the channel whose current live stream is to be ended.

        Returns:
            dict: {
                "success": True,
                "message": "Stream [stream_id] ended for channel [channel_id]"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The channel must exist.
            - The channel must currently be live (`current_status` == 'live') and have a valid `current_stream_id`.
            - The stream must exist in the streams dictionary.
            - Updates both stream and channel states atomically.
        """
        # Check if channel exists
        channel = self.channels.get(channel_id)
        if not channel:
            return { "success": False, "error": "Channel does not exist" }

        if channel["current_status"] != "live" or not channel["current_stream_id"]:
            return { "success": False, "error": "Channel is not currently streaming" }

        stream_id = channel["current_stream_id"]
        stream = self.streams.get(stream_id)
        if not stream or stream["status"] != "live":
            return { "success": False, "error": "Live stream not found or already ended" }

        # Set stream's status to 'offline' and record end time (UTC ISO 8601)
        now = datetime.now(timezone.utc).isoformat()
        stream["status"] = "offline"
        stream["end_time"] = now

        # Update channel status
        channel["current_status"] = "offline"
        channel["current_stream_id"] = None

        return {
            "success": True,
            "message": f"Stream {stream_id} ended for channel {channel_id}"
        }

    def update_stream_preview(self, stream_id: str, new_preview_image_url: str) -> dict:
        """
        Update the preview image URL for a live stream.

        Args:
            stream_id (str): The ID of the stream to update.
            new_preview_image_url (str): The new URL of the preview image.

        Returns:
            dict: {
                "success": True,
                "message": "Preview image updated for stream <stream_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Can only update the preview for a stream if its status is "live".
            - The stream_id must exist.
        """
        stream = self.streams.get(stream_id)
        if not stream:
            return { "success": False, "error": "Stream does not exist." }

        if stream['status'] != "live":
            return { "success": False, "error": "Can only update the preview image for a live stream." }

        stream['preview_image_url'] = new_preview_image_url
        return {
            "success": True,
            "message": f"Preview image updated for stream {stream_id}."
        }


    def archive_stream_to_broadcast(self, stream_id: str) -> dict:
        """
        Convert a completed (ended) stream session into a saved broadcast archive.

        Args:
            stream_id (str): The identifier of the stream session to archive.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Stream archived as broadcast",
                    "broadcast_id": str
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only completed (not live, end_time set) streams may be archived.
            - Only one broadcast is permitted per stream.
            - The referenced stream and its channel must exist.
        """
        # 1. Check that the stream exists
        stream_info = self.streams.get(stream_id)
        if not stream_info:
            return { "success": False, "error": "Stream does not exist" }

        # 2. Check that the stream is associated with a real channel
        channel_id = stream_info.get("channel_id")
        if not channel_id or channel_id not in self.channels:
            return { "success": False, "error": "Invalid or missing channel for this stream" }

        # 3. Stream must have ended (not "live" and end_time set)
        if stream_info["status"] == "live" or not stream_info.get("end_time"):
            return { "success": False, "error": "Stream is not completed and cannot be archived" }

        # 4. Ensure this stream isn't already archived
        for broadcast in self.broadcasts.values():
            if broadcast["stream_id"] == stream_id:
                return { "success": False, "error": "Broadcast already exists for this stream" }

        # 5. Generate broadcast_id, archive_url, created_at
        broadcast_id = f"broadcast_{stream_id}"
        archive_url = f"/archive/{broadcast_id}.mp4"
        created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        # Optional: copy over relevant metadata
        metadata = dict(stream_info.get("stream_metadata", {}))

        broadcast_info = {
            "broadcast_id": broadcast_id,
            "channel_id": channel_id,
            "stream_id": stream_id,
            "archive_url": archive_url,
            "created_at": created_at,
            "metadata": metadata
        }

        self.broadcasts[broadcast_id] = broadcast_info

        return {
            "success": True,
            "message": "Stream archived as broadcast",
            "broadcast_id": broadcast_id
        }

    def delete_broadcast(self, broadcast_id: str) -> dict:
        """
        Remove (or hide) an archived broadcast from a channel.

        Args:
            broadcast_id (str): The unique identifier of the broadcast to remove.

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "Broadcast <broadcast_id> deleted."
                }
                On failure: {
                    "success": False, 
                    "error": "Broadcast not found"
                }

        Constraints:
            - The broadcast must exist in the system.
            - No permission or ownership check is enforced.
            - Channel storage accounting is recalculated after deletion.
        """
        if broadcast_id not in self.broadcasts:
            return { "success": False, "error": "Broadcast not found" }

        channel_id = self.broadcasts[broadcast_id]["channel_id"]
        del self.broadcasts[broadcast_id]
        self._recalculate_channel_storage_usage(channel_id)

        return { "success": True, "message": f"Broadcast {broadcast_id} deleted." }

    def transfer_channel_ownership(self, channel_id: str, new_user_id: str) -> dict:
        """
        Change the user associated with a specific channel_id (admin function).

        Args:
            channel_id (str): The identifier of the channel.
            new_user_id (str): The user ID of the new owner.

        Returns:
            dict:
                - On success: 
                    {"success": True, "message": "Channel ownership transferred: channel <channel_id> now belongs to user <new_user_id>."}
                - On failure: 
                    {"success": False, "error": "<reason>"}
        Constraints:
            - Channel must exist.
            - New user must exist.
            - Each channel is associated with exactly one user.
            - User may have more than one channel. User's channel_id attribute is optional and may be updated if relevant.
        """
        if channel_id not in self.channels:
            return {"success": False, "error": f"Channel '{channel_id}' does not exist."}
        if new_user_id not in self.users:
            return {"success": False, "error": f"User '{new_user_id}' does not exist."}
    
        channel_info = self.channels[channel_id]
        old_user_id = channel_info['user_id']

        if old_user_id == new_user_id:
            return {"success": False, "error": f"Channel '{channel_id}' is already owned by user '{new_user_id}'."}

        # Update the channel's user_id to the new owner
        channel_info['user_id'] = new_user_id
        self.channels[channel_id] = channel_info

        # Remove channel reference from the old owner if it's listed as their current main channel
        if old_user_id in self.users:
            old_user = self.users[old_user_id]
            if old_user.get('channel_id') == channel_id:
                old_user['channel_id'] = None
                self.users[old_user_id] = old_user

        # Optionally set the new user's main channel if they have none
        new_user = self.users[new_user_id]
        if new_user.get('channel_id') is None:
            new_user['channel_id'] = channel_id
            self.users[new_user_id] = new_user

        return {
            "success": True,
            "message": f"Channel ownership transferred: channel '{channel_id}' now belongs to user '{new_user_id}'."
        }

    def add_new_user(
        self,
        _id: str,
        username: str,
        profile_metadata: dict,
        account_type: str
    ) -> dict:
        """
        Register a new user on the platform.

        Args:
            _id (str): The unique user ID (must not already exist).
            username (str): The display username (must not already exist).
            profile_metadata (dict): User profile details.
            account_type (str): One of "streamer" or "viewer".

        Returns:
            dict: {
                "success": True,
                "message": str  # Success confirmation
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - _id and username must be unique among users.
            - account_type must be "streamer" or "viewer".
            - New user will not have an associated channel yet (channel_id is None).
        """
        # Validate required fields
        if not _id or not username or not profile_metadata or not account_type:
            return {"success": False, "error": "All fields (_id, username, profile_metadata, account_type) are required."}
        # Check account_type validity
        if account_type not in {"streamer", "viewer"}:
            return {"success": False, "error": "Invalid account_type. Must be 'streamer' or 'viewer'."}
        # Check for uniqueness of _id
        if _id in self.users:
            return {"success": False, "error": f"User ID '{_id}' already exists."}
        # Check for uniqueness of username
        for user in self.users.values():
            if user["username"] == username:
                return {"success": False, "error": f"Username '{username}' already exists."}
        # Create new user
        user_info = {
            "_id": _id,
            "username": username,
            "profile_metadata": profile_metadata,
            "account_type": account_type,
            "channel_id": None
        }
        self.users[_id] = user_info
        return {"success": True, "message": f"User '{username}' registered successfully."}

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user and all associated data (channel, streams, broadcasts) from the system.

        Args:
            user_id (str): Unique identifier for the user to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "User and all associated data deleted successfully."
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User not found."
            }

        Constraints:
            - If the user has a channel, all data (channel, streams, broadcasts) must also be deleted.
            - If the user does not exist, operation fails cleanly.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        user_info = self.users[user_id]
        channel_id = user_info.get("channel_id")

        # Remove user
        del self.users[user_id]

        if channel_id and channel_id in self.channels:
            # Remove the channel
            del self.channels[channel_id]

            # Remove all associated streams
            streams_to_remove = [sid for sid, si in self.streams.items() if si["channel_id"] == channel_id]
            for sid in streams_to_remove:
                del self.streams[sid]

            # Remove all associated broadcasts
            broadcasts_to_remove = [bid for bid, bi in self.broadcasts.items() if bi["channel_id"] == channel_id]
            for bid in broadcasts_to_remove:
                del self.broadcasts[bid]

        return {"success": True, "message": "User and all associated data deleted successfully."}


class TwitchUserChannelManagementSystem(BaseEnv):
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

    def list_users_by_account_type(self, **kwargs):
        return self._call_inner_tool('list_users_by_account_type', kwargs)

    def get_channel_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_channel_by_user_id', kwargs)

    def get_channel_by_id(self, **kwargs):
        return self._call_inner_tool('get_channel_by_id', kwargs)

    def get_channel_status(self, **kwargs):
        return self._call_inner_tool('get_channel_status', kwargs)

    def get_current_stream_by_channel_id(self, **kwargs):
        return self._call_inner_tool('get_current_stream_by_channel_id', kwargs)

    def get_most_recent_stream_by_channel_id(self, **kwargs):
        return self._call_inner_tool('get_most_recent_stream_by_channel_id', kwargs)

    def get_stream_by_id(self, **kwargs):
        return self._call_inner_tool('get_stream_by_id', kwargs)

    def get_stream_preview_url(self, **kwargs):
        return self._call_inner_tool('get_stream_preview_url', kwargs)

    def get_latest_stream_preview_for_username(self, **kwargs):
        return self._call_inner_tool('get_latest_stream_preview_for_username', kwargs)

    def list_streams_by_channel_id(self, **kwargs):
        return self._call_inner_tool('list_streams_by_channel_id', kwargs)

    def list_broadcasts_by_channel_id(self, **kwargs):
        return self._call_inner_tool('list_broadcasts_by_channel_id', kwargs)

    def get_broadcast_by_id(self, **kwargs):
        return self._call_inner_tool('get_broadcast_by_id', kwargs)

    def get_broadcasts_for_stream_id(self, **kwargs):
        return self._call_inner_tool('get_broadcasts_for_stream_id', kwargs)

    def get_channel_metadata(self, **kwargs):
        return self._call_inner_tool('get_channel_metadata', kwargs)

    def get_user_profile_metadata(self, **kwargs):
        return self._call_inner_tool('get_user_profile_metadata', kwargs)

    def update_user_profile_metadata(self, **kwargs):
        return self._call_inner_tool('update_user_profile_metadata', kwargs)

    def update_channel_metadata(self, **kwargs):
        return self._call_inner_tool('update_channel_metadata', kwargs)

    def start_stream(self, **kwargs):
        return self._call_inner_tool('start_stream', kwargs)

    def end_stream(self, **kwargs):
        return self._call_inner_tool('end_stream', kwargs)

    def update_stream_preview(self, **kwargs):
        return self._call_inner_tool('update_stream_preview', kwargs)

    def archive_stream_to_broadcast(self, **kwargs):
        return self._call_inner_tool('archive_stream_to_broadcast', kwargs)

    def delete_broadcast(self, **kwargs):
        return self._call_inner_tool('delete_broadcast', kwargs)

    def transfer_channel_ownership(self, **kwargs):
        return self._call_inner_tool('transfer_channel_ownership', kwargs)

    def add_new_user(self, **kwargs):
        return self._call_inner_tool('add_new_user', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)
