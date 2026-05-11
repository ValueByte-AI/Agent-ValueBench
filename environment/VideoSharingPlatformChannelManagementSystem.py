# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ChannelInfo(TypedDict):
    channel_id: str
    name: str
    profile_info: Dict[str, str]  # could include further structured information
    creation_date: str  # ISO formatted date string
    sta: str  # likely channel status (active, suspended, etc.)

class ChannelRelationshipInfo(TypedDict):
    channel_id: str
    related_channel_id: str
    relationship_type: str  # e.g., featured, related, recommended

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Video Sharing Platform Channel Management System state representation.
        """

        # Channels: {channel_id: ChannelInfo}
        # Represents a content creator’s channel and its metadata.
        self.channels: Dict[str, ChannelInfo] = {}

        # Channel relationships: List of ChannelRelationshipInfo
        # Each item is a directed relationship between channels.
        self.channel_relationships: List[ChannelRelationshipInfo] = []

        # Constraints:
        # - All featured/related/recommended relationships must reference valid channel_ids in self.channels.
        # - A channel cannot be featured/related to itself (channel_id != related_channel_id).
        # - relationship_type must be one of the allowed types (e.g., featured, related, recommended).
        # - profile_info must be up-to-date and non-null for public channels.

    def get_channel_by_id(self, channel_id: str) -> dict:
        """
        Retrieve full metadata for a single channel using its channel_id.

        Args:
            channel_id (str): The unique identifier of the channel.

        Returns:
            dict:
                - If found: { "success": True, "data": ChannelInfo }
                - If not found: { "success": False, "error": "Channel not found" }
        Constraints:
            - channel_id must exist in self.channels.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return { "success": False, "error": "Channel not found" }
        return { "success": True, "data": channel }

    def get_channels_by_ids(self, channel_ids: list[str]) -> dict:
        """
        Fetch metadata for a list of channel_ids.

        Args:
            channel_ids (List[str]): The list of unique channel IDs to fetch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ChannelInfo]  # May be empty if none found
                    }
        Notes:
            - Only channel_ids present in the system are returned.
            - If none are found, returns empty data list.
            - No error raised for missing IDs.
        """
        if not isinstance(channel_ids, list):
            return { "success": False, "error": "Input must be a list of channel IDs" }

        found_channels = []
        for cid in channel_ids:
            ci = self.channels.get(cid)
            if ci is not None:
                found_channels.append(ci)

        return { "success": True, "data": found_channels }

    def list_all_channels(self) -> dict:
        """
        Retrieve the metadata for all channels in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ChannelInfo]  # List of channel metadata (may be empty if no channels)
            }

        Constraints:
            - None (returns whatever is present in self.channels)
        """
        all_channels = list(self.channels.values())
        return { "success": True, "data": all_channels }

    def get_channel_by_name(self, name: str) -> dict:
        """
        Lookup channel metadata by channel name.

        Args:
            name (str): The channel name to look up.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ChannelInfo,  # metadata of the found channel
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Channel not found"
                    }
        Constraints:
            - If multiple channels have the same name, returns the first found.
            - Returns error if the name is empty or no match found.
        """
        if not name:
            return {"success": False, "error": "Channel not found"}

        for channel_info in self.channels.values():
            if channel_info["name"] == name:
                return {"success": True, "data": channel_info}
        return {"success": False, "error": "Channel not found"}

    def get_channels_by_status(self, status: str) -> dict:
        """
        Retrieve all channels whose `sta` (status) field matches the given status.

        Args:
            status (str): The status value to filter channels by (e.g., "active", "suspended").

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ChannelInfo]  # All matching channels (empty list if none)
                    }
        """
        matching_channels = [
            channel_info
            for channel_info in self.channels.values()
            if channel_info.get("sta") == status
        ]
        return { "success": True, "data": matching_channels }

    def get_channel_relationships_by_channel(self, channel_id: str) -> dict:
        """
        List all outgoing relationships (featured, related, recommended, etc.) for a given channel_id.

        Args:
            channel_id (str): The channel's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ChannelRelationshipInfo]  # all relationships where channel_id is source
            }
            or
            {
                "success": False,
                "error": str  # If the channel does not exist
            }

        Constraints:
            - The channel_id must exist in self.channels.
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }
    
        outgoing_relationships = [
            rel for rel in self.channel_relationships if rel['channel_id'] == channel_id
        ]
    
        return { "success": True, "data": outgoing_relationships }

    def get_channel_relationships_by_type(self, relationship_type: str) -> dict:
        """
        Retrieve all channel relationships in the system with the specified type.

        Args:
            relationship_type (str): The type of relationship to filter (e.g., 'featured', 'related', 'recommended').

        Returns:
            dict: {
                "success": True,
                "data": List[ChannelRelationshipInfo]  # All matching relationships (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description if input is invalid
            }

        Constraints:
            - relationship_type must be non-empty.
            - Only returns relationships where relationship_type matches.
        """
        if not relationship_type or not isinstance(relationship_type, str):
            return { "success": False, "error": "relationship_type must be a non-empty string" }

        result = [
            rel for rel in self.channel_relationships
            if rel["relationship_type"] == relationship_type
        ]
        return { "success": True, "data": result }

    def get_related_channels(self, channel_id: str, relationship_type: str) -> dict:
        """
        For a given channel_id, fetch all associated channels by specified relationship_type.

        Args:
            channel_id (str): The source channel's unique identifier.
            relationship_type (str): The relationship type ('featured', 'related', 'recommended', etc).

        Returns:
            dict: 
                - On success: { "success": True, "data": [ChannelInfo, ...] }
                - On failure: { "success": False, "error": str }

        Constraints:
            - channel_id must exist.
            - relationship_type must be valid (present in at least one relationship, or check against allowed types if such a set is maintained).
            - Excludes self-loops and relationships referencing non-existent channels.
        """
        # Ensure the channel exists
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist." }

        # Find all relationships for this channel_id and relationship_type
        related_channel_ids = [
            rel["related_channel_id"]
            for rel in self.channel_relationships
            if rel["channel_id"] == channel_id
            and rel["relationship_type"] == relationship_type
            and rel["related_channel_id"] != channel_id
            and rel["related_channel_id"] in self.channels
        ]

        # Collect ChannelInfo for each valid related_channel_id
        data = [self.channels[rcid] for rcid in related_channel_ids]

        return { "success": True, "data": data }

    def get_channels_with_relationship(self, channel_ids: list, relationship_type: str) -> dict:
        """
        For a list of channel_ids and a relationship_type, retrieve the set of related channels and their metadata.

        Args:
            channel_ids (List[str]): The channel_ids to be examined as sources of the relationship.
            relationship_type (str): The type of relationship to filter on (e.g., "featured", "related", "recommended").

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[ChannelInfo]  # List of metadata dicts for related channels (deduplicated)
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only retrieve related_channel_id where both relationship_type matches and channel_id is in the input list.
            - Only return metadata for valid channels (skip any dangling relationships).
            - Result does not include duplicates if there are multiple relationships pointing to the same channel.
        """
        if not isinstance(channel_ids, list) or not isinstance(relationship_type, str):
            return { "success": False, "error": "Invalid input type for channel_ids or relationship_type" }

        # Step 1: Find all relationships of given type and from any supplied channel_id
        related_ids = set()
        for rel in self.channel_relationships:
            if rel["channel_id"] in channel_ids and rel["relationship_type"] == relationship_type:
                # Avoid self-reference in results (shouldn't exist due to constraints, but defensive)
                if rel["related_channel_id"] != rel["channel_id"]:
                    related_ids.add(rel["related_channel_id"])
    
        # Step 2: Fetch metadata for all corresponding channels
        result = []
        for cid in related_ids:
            chan = self.channels.get(cid, None)
            if chan is not None:
                result.append(chan)

        return { "success": True, "data": result }

    def validate_channel_relationship_integrity(self) -> dict:
        """
        Checks all channel relationships for integrity violations:
          - References to invalid (nonexistent) channel IDs.
          - Self-referential relationships (where channel_id == related_channel_id).
          - Invalid relationship_type (should be one of "featured", "related", "recommended").

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        "invalid_relationships": List[ChannelRelationshipInfo],
                        "self_referential_relationships": List[ChannelRelationshipInfo],
                        "invalid_type_relationships": List[ChannelRelationshipInfo]
                    }
                }
            or
                {
                    "success": False,
                    "error": str
                }
        """
        valid_types = {"featured", "related", "recommended"}
        invalid_relationships = []
        self_ref_relationships = []
        invalid_type_relationships = []

        for rel in self.channel_relationships:
            # Check for invalid references
            if rel["channel_id"] not in self.channels or rel["related_channel_id"] not in self.channels:
                invalid_relationships.append(rel)
            # Check for self-referential relationships
            if rel["channel_id"] == rel["related_channel_id"]:
                self_ref_relationships.append(rel)
            # Check for invalid relationship types
            if rel["relationship_type"] not in valid_types:
                invalid_type_relationships.append(rel)

        return {
            "success": True,
            "data": {
                "invalid_relationships": invalid_relationships,
                "self_referential_relationships": self_ref_relationships,
                "invalid_type_relationships": invalid_type_relationships
            }
        }

    def is_channel_profile_up_to_date(self, channel_id: str) -> dict:
        """
        Verify if the specified channel's profile_info is non-null and contains
        substantive profile fields for public channels (status 'active').

        Args:
            channel_id (str): The unique identifier of the channel.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True iff profile_info contains at least one non-note, non-empty field for a public channel
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. channel not found)
            }

        Constraints:
            - Channel must exist.
            - Applies the check only for 'active' (public) channels.
        """
        channel = self.channels.get(channel_id)
        if channel is None:
            return {"success": False, "error": "Channel not found"}

        # Check if channel is 'active' (public)
        # If the channel is not public, by the constraint it's not required, but we'll still say the check passes.
        if channel.get("sta", "").lower() != "active":
            # Not required for non-public, return True (or could also return False with explanation)
            return {"success": True, "data": True}

        profile_info = channel.get("profile_info")
        if not isinstance(profile_info, dict) or not profile_info:
            return {"success": True, "data": False}

        has_substantive_field = False
        for value in profile_info.values():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue

        for key, value in profile_info.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(key, str) and key.endswith("_note"):
                continue
            has_substantive_field = True
            break

        return {"success": True, "data": has_substantive_field}

    def add_channel(
        self,
        channel_id: str,
        name: str,
        profile_info: Dict[str, str],
        creation_date: str,
        sta: str
    ) -> dict:
        """
        Add a new channel to the system with required metadata.

        Args:
            channel_id (str): Unique identifier for the channel.
            name (str): Channel name.
            profile_info (Dict[str, str]): Channel profile information. Must be non-null/non-empty for public channels (e.g., status 'active').
            creation_date (str): ISO formatted string for creation date.
            sta (str): Channel status ("active", "suspended", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Channel <channel_id> successfully added."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - channel_id must be unique.
            - For public channels (sta == "active"), profile_info must be non-null and non-empty.
        """
        # Check if channel_id already exists
        if channel_id in self.channels:
            return { "success": False, "error": "Channel ID already exists." }

        # For public channels, profile_info must be non-null and non-empty
        if sta == "active":
            if not isinstance(profile_info, dict) or not profile_info:
                return { "success": False, "error": "Profile info must be non-empty for public channels." }

        # Basic presence checks for required fields (should not be empty strings)
        if not channel_id or not name or not creation_date or not sta:
            return { "success": False, "error": "Missing required channel metadata." }

        # Construct and add the new channel
        channel_info: ChannelInfo = {
            "channel_id": channel_id,
            "name": name,
            "profile_info": profile_info,
            "creation_date": creation_date,
            "sta": sta
        }
        self.channels[channel_id] = channel_info

        return { "success": True, "message": f"Channel {channel_id} successfully added." }

    def update_channel_profile(self, channel_id: str, update_data: Dict[str, object]) -> dict:
        """
        Update the profile_info or metadata for a given channel.

        Args:
            channel_id (str): The identifier for the channel to update.
            update_data (Dict[str, object]): Dict of fields to update. Keys can include
                "name", "profile_info", "sta", etc. "profile_info" should be a dict.

        Returns:
            dict: {
                "success": True,
                "message": "Channel profile updated successfully"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The channel must exist.
            - profile_info must be non-null for public channels.
            - Only valid keys are updated.
        """
        # Check if channel exists
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel does not exist" }
    
        # Allowed keys for update
        valid_keys = {"name", "profile_info", "sta"}
    
        channel = self.channels[channel_id]
        modified = False

        for key in update_data:
            if key not in valid_keys:
                continue  # Ignore invalid keys
            # Optional: type checking for "profile_info"
            if key == "profile_info":
                if not isinstance(update_data[key], dict):
                    return { "success": False, "error": "profile_info must be a dictionary" }
            channel[key] = update_data[key]
            modified = True

        # Enforce that public channels have non-null profile_info
        if channel.get("sta", "active") == "active" and not channel.get("profile_info"):
            return { "success": False, "error": "Public channel's profile_info must be non-null" }
    
        self.channels[channel_id] = channel  # Update is in-place, but keep it explicit
    
        return { "success": True, "message": "Channel profile updated successfully" }

    def change_channel_status(self, channel_id: str, new_status: str) -> dict:
        """
        Update the status (sta) of a channel.

        Args:
            channel_id (str): The unique identifier of the channel.
            new_status (str): The new status value (e.g., 'active', 'suspended').

        Returns:
            dict: 
                On success: { "success": True, "message": "Status updated successfully" }
                On failure: { "success": False, "error": "Channel not found" }

        Constraints:
            - The channel must exist in the system.
            - No restriction on new_status value assumed unless specified.
        """
        if channel_id not in self.channels:
            return { "success": False, "error": "Channel not found" }

        self.channels[channel_id]['sta'] = new_status
        return { "success": True, "message": "Status updated successfully" }

    def delete_channel(self, channel_id: str) -> dict:
        """
        Remove a channel from the system and automatically clean up all associated channel relationships.

        Args:
            channel_id (str): The unique identifier of the channel to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Channel <channel_id> and all its relationships deleted."
            }
            or
            {
                "success": False,
                "error": "Channel does not exist."
            }

        Constraints:
            - Channel must exist to be deleted.
            - All relationships where this channel is channel_id or related_channel_id are also removed.
        """
        if channel_id not in self.channels:
            return {"success": False, "error": "Channel does not exist."}

        # Remove the channel itself
        del self.channels[channel_id]

        # Clean up all related relationships
        original_count = len(self.channel_relationships)
        self.channel_relationships = [
            rel for rel in self.channel_relationships
            if rel["channel_id"] != channel_id and rel["related_channel_id"] != channel_id
        ]

        purged = original_count - len(self.channel_relationships)

        return {
            "success": True,
            "message": f"Channel {channel_id} and all its relationships ({purged}) deleted."
        }

    def add_channel_relationship(
        self,
        channel_id: str,
        related_channel_id: str,
        relationship_type: str
    ) -> dict:
        """
        Create a new relationship (featured, related, recommended, etc.) between two channels,
        enforcing constraints:
            - Both channel_id and related_channel_id exist in the system.
            - channel_id != related_channel_id (no self-reference).
            - relationship_type is one of the allowed types ("featured", "related", "recommended").
            - Duplicate relationships (same channel_id, related_channel_id, relationship_type) are not allowed.

        Args:
            channel_id (str): The source/origin channel.
            related_channel_id (str): The destination/target channel.
            relationship_type (str): The type of relationship.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        # Allowed relationship types (could be attribute or config)
        allowed_types = {"featured", "related", "recommended"}
        # Validate both channel IDs
        if channel_id not in self.channels:
            return {"success": False, "error": "channel_id does not exist"}
        if related_channel_id not in self.channels:
            return {"success": False, "error": "related_channel_id does not exist"}
        # Prevent self-relationship
        if channel_id == related_channel_id:
            return {"success": False, "error": "A channel cannot be related to itself"}
        # Validate relationship type
        if relationship_type not in allowed_types:
            return {"success": False, "error": "Invalid relationship_type"}
        # Prevent duplicate relationship
        for rel in self.channel_relationships:
            if (rel["channel_id"] == channel_id and
                rel["related_channel_id"] == related_channel_id and
                rel["relationship_type"] == relationship_type):
                return {"success": False, "error": "This relationship already exists"}
        # Add new relationship
        new_rel = {
            "channel_id": channel_id,
            "related_channel_id": related_channel_id,
            "relationship_type": relationship_type
        }
        self.channel_relationships.append(new_rel)
        return {
            "success": True,
            "message": f"Relationship of type '{relationship_type}' from channel '{channel_id}' to channel '{related_channel_id}' added."
        }

    def remove_channel_relationship(self, channel_id: str, related_channel_id: str, relationship_type: str) -> dict:
        """
        Delete all existing relationships that match the specified (channel_id, related_channel_id, relationship_type).

        Args:
            channel_id (str): The source channel's ID.
            related_channel_id (str): The target channel's ID.
            relationship_type (str): The type of the relationship (e.g., featured, related, recommended).

        Returns:
            dict: {
                "success": True,
                "message": "Relationship removed successfully."
            }
            or
            {
                "success": False,
                "error": "Specified relationship does not exist."
            }

        Constraints:
            - Only removes relationships matching all three parameters.
            - If no such relationship exists, operation fails with error.
        """
        initial_count = len(self.channel_relationships)
        self.channel_relationships = [
            rel for rel in self.channel_relationships
            if not (
                rel["channel_id"] == channel_id and
                rel["related_channel_id"] == related_channel_id and
                rel["relationship_type"] == relationship_type
            )
        ]
        removed_count = initial_count - len(self.channel_relationships)
        if removed_count == 0:
            return { "success": False, "error": "Specified relationship does not exist." }
        return { "success": True, "message": "Relationship removed successfully." }

    def update_channel_relationship_type(
        self,
        channel_id: str,
        related_channel_id: str,
        new_relationship_type: str
    ) -> dict:
        """
        Change the relationship type of an existing channel-to-channel association.

        Args:
            channel_id (str): The channel initiating the relationship.
            related_channel_id (str): The related/target channel.
            new_relationship_type (str): The new relationship type ('featured', 'related', 'recommended').

        Returns:
            dict: Success or failure with a descriptive message.

        Constraints:
            - Both channel_id and related_channel_id must reference existing channels.
            - channel_id must not equal related_channel_id.
            - new_relationship_type must be a valid type.
            - The relationship must already exist to be updated.
        """
        valid_types = {"featured", "related", "recommended"}

        # Validate channels
        if channel_id not in self.channels or related_channel_id not in self.channels:
            return { "success": False, "error": "One or both channels do not exist." }

        # Prevent self-relationship
        if channel_id == related_channel_id:
            return { "success": False, "error": "A channel cannot relate to itself." }

        # Validate relationship type
        if new_relationship_type not in valid_types:
            return { "success": False, "error": f"Invalid relationship type: {new_relationship_type}." }

        # Find relationship
        for rel in self.channel_relationships:
            if (
                rel["channel_id"] == channel_id and
                rel["related_channel_id"] == related_channel_id
            ):
                old_type = rel["relationship_type"]
                rel["relationship_type"] = new_relationship_type
                return {
                    "success": True,
                    "message": f"Relationship type updated from {old_type} to {new_relationship_type}."
                }

        return { "success": False, "error": "Relationship does not exist between the given channels." }

    def bulk_update_channel_profiles(self, updates: Dict[str, Dict[str, str]]) -> dict:
        """
        Update the profile_info field for multiple channels at once.

        Args:
            updates (Dict[str, Dict[str, str]]): Mapping of channel_id to new profile_info dict.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success description, including counts
                "updated": List[str],  # List of channel_ids updated
                "failed": List[str],   # List of channel_ids not found
            }

        Constraints:
            - Only channels that exist in self.channels will be updated.
            - Nonexistent channel_ids are reported as failed.
        """
        updated = []
        failed = []
        for channel_id, new_profile in updates.items():
            if channel_id in self.channels:
                self.channels[channel_id]["profile_info"] = new_profile
                updated.append(channel_id)
            else:
                failed.append(channel_id)
        message = f"Updated {len(updated)} channel(s)."
        if failed:
            message += f" {len(failed)} channel(s) not found and not updated."
        return {
            "success": True,
            "message": message,
            "updated": updated,
            "failed": failed,
        }

    def repair_invalid_relationships(self) -> dict:
        """
        Remove or fix all relationships that violate constraints in channel_relationships.
        Constraints enforced:
          - Both channel_id and related_channel_id must exist in channels.
          - channel_id != related_channel_id (no self-relationships).
          - relationship_type must be among allowed types ('featured', 'related', 'recommended').

        Returns:
            dict: {
                "success": True,
                "message": str  # Summary of what was repaired/removed
            }
        """
        allowed_types = {"featured", "related", "recommended"}

        original_count = len(self.channel_relationships)
        removed_invalid_channels = 0
        removed_self_relationships = 0
        removed_invalid_types = 0

        valid_channel_ids = set(self.channels.keys())
        new_relationships = []

        for rel in self.channel_relationships:
            if rel["channel_id"] not in valid_channel_ids or rel["related_channel_id"] not in valid_channel_ids:
                removed_invalid_channels += 1
                continue
            if rel["channel_id"] == rel["related_channel_id"]:
                removed_self_relationships += 1
                continue
            if rel["relationship_type"] not in allowed_types:
                removed_invalid_types += 1
                continue
            new_relationships.append(rel)

        self.channel_relationships = new_relationships

        removed_total = (
            removed_invalid_channels + removed_self_relationships + removed_invalid_types
        )

        if removed_total == 0:
            msg = "No invalid relationships found; no action needed."
        else:
            msg = (
                f"Removed {removed_total} invalid relationships. "
                f"{removed_invalid_channels} had non-existent channels, "
                f"{removed_self_relationships} were self-relationships, "
                f"{removed_invalid_types} had invalid types."
            )
        return {"success": True, "message": msg}


class VideoSharingPlatformChannelManagementSystem(BaseEnv):
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

    def get_channel_by_id(self, **kwargs):
        return self._call_inner_tool('get_channel_by_id', kwargs)

    def get_channels_by_ids(self, **kwargs):
        return self._call_inner_tool('get_channels_by_ids', kwargs)

    def list_all_channels(self, **kwargs):
        return self._call_inner_tool('list_all_channels', kwargs)

    def get_channel_by_name(self, **kwargs):
        return self._call_inner_tool('get_channel_by_name', kwargs)

    def get_channels_by_status(self, **kwargs):
        return self._call_inner_tool('get_channels_by_status', kwargs)

    def get_channel_relationships_by_channel(self, **kwargs):
        return self._call_inner_tool('get_channel_relationships_by_channel', kwargs)

    def get_channel_relationships_by_type(self, **kwargs):
        return self._call_inner_tool('get_channel_relationships_by_type', kwargs)

    def get_related_channels(self, **kwargs):
        return self._call_inner_tool('get_related_channels', kwargs)

    def get_channels_with_relationship(self, **kwargs):
        return self._call_inner_tool('get_channels_with_relationship', kwargs)

    def validate_channel_relationship_integrity(self, **kwargs):
        return self._call_inner_tool('validate_channel_relationship_integrity', kwargs)

    def is_channel_profile_up_to_date(self, **kwargs):
        return self._call_inner_tool('is_channel_profile_up_to_date', kwargs)

    def add_channel(self, **kwargs):
        return self._call_inner_tool('add_channel', kwargs)

    def update_channel_profile(self, **kwargs):
        return self._call_inner_tool('update_channel_profile', kwargs)

    def change_channel_status(self, **kwargs):
        return self._call_inner_tool('change_channel_status', kwargs)

    def delete_channel(self, **kwargs):
        return self._call_inner_tool('delete_channel', kwargs)

    def add_channel_relationship(self, **kwargs):
        return self._call_inner_tool('add_channel_relationship', kwargs)

    def remove_channel_relationship(self, **kwargs):
        return self._call_inner_tool('remove_channel_relationship', kwargs)

    def update_channel_relationship_type(self, **kwargs):
        return self._call_inner_tool('update_channel_relationship_type', kwargs)

    def bulk_update_channel_profiles(self, **kwargs):
        return self._call_inner_tool('bulk_update_channel_profiles', kwargs)

    def repair_invalid_relationships(self, **kwargs):
        return self._call_inner_tool('repair_invalid_relationships', kwargs)
