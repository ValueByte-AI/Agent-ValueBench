# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class TeamInfo(TypedDict):
    team_id: str             # Unique identifier for the team
    name: str
    sport_type: str
    league: str
    other_metadata: str

class MediaAssetInfo(TypedDict):
    media_id: str            # Unique identifier for the media asset
    file_path: str           # Path or location of the file
    media_type: str          # Type of media (e.g., photo, video)
    upload_date: str         # Date the media was uploaded
    category: str            # Category/tagging of media
    event_id: str            # Associated event ID (if any)
    description: str
    tags: List[str]          # Tags for search/categorization
    team_ids: List[str]      # Must be associated with at least one team

class EventInfo(TypedDict):
    event_id: str            # Unique identifier for the event
    name: str
    date: str
    location: str
    participating_team_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Teams: {team_id: TeamInfo}
        self.teams: Dict[str, TeamInfo] = {}

        # Media assets: {media_id: MediaAssetInfo}
        # Constraint: media_id must be unique; each asset must have at least one team in team_ids
        self.media_assets: Dict[str, MediaAssetInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Constraints (as reminders, not enforced here):
        # - Each MediaAsset must be linked to at least one team (team_ids non-empty)
        # - team_id and media_id must be unique
        # - Media retrieval must restrict access to only associated team's media
        # - MediaAssetInfo has metadata fields to enable robust categorization and search

    def get_team_by_id(self, team_id: str) -> dict:
        """
        Retrieve the full information of a team given its unique team_id.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict:
                - If team exists: { "success": True, "data": TeamInfo }
                - If not found:   { "success": False, "error": "Team not found" }
        """
        team = self.teams.get(team_id)
        if team is None:
            return { "success": False, "error": "Team not found" }
        return { "success": True, "data": team }

    def list_all_teams(self) -> dict:
        """
        Retrieve a list of all registered teams in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TeamInfo]  # All TeamInfo dicts (may be empty if no teams)
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - None specifically for this operation.
        """
        if not hasattr(self, 'teams') or self.teams is None:
            return { "success": False, "error": "Internal error: teams data not available" }
        teams_list = list(self.teams.values())
        return { "success": True, "data": teams_list }

    def get_media_by_team_id(self, team_id: str) -> dict:
        """
        Retrieve all media assets associated with a specified team_id.

        Args:
            team_id (str): The unique identifier of the team.

        Returns:
            dict: {
                "success": True,
                "data": List[MediaAssetInfo],  # List of matching media assets (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., team not found)
            }

        Constraints:
            - team_id must exist in the system.
            - Only return media assets that include the team_id in their team_ids field.
        """
        if team_id not in self.teams:
            return {"success": False, "error": "Team ID not found"}

        result = [
            asset for asset in self.media_assets.values()
            if team_id in asset.get("team_ids", [])
        ]
        return {"success": True, "data": result}

    def search_media_by_metadata(
        self,
        category: str = None,
        media_type: str = None,
        event_id: str = None,
        tags: List[str] = None,
        upload_date: str = None
    ) -> dict:
        """
        Search for media assets using optional filtering criteria.
        Filters can be any subset of: category, media_type, event_id, tags, upload_date.

        Args:
            category (str, optional): Restrict to media of this category.
            media_type (str, optional): Restrict to media of this type (e.g., photo, video).
            event_id (str, optional): Restrict to media linked to this event.
            tags (List[str], optional): Restrict to media containing ALL these tags.
            upload_date (str, optional): Restrict to media uploaded on this date (format: YYYY-MM-DD).

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": List[MediaAssetInfo],  # May be empty if no matches.
                    }
                On invalid/no criteria:
                    {
                      "success": False,
                      "error": str  # Explains problem
                    }

        Constraints:
            - Search uses AND logic: a media asset matches only if it satisfies every given filter.
            - For tags, asset must include ALL the specified tags.
        """

        if all(x is None for x in [category, media_type, event_id, tags, upload_date]):
            return {"success": False, "error": "No search criteria provided"}

        # Perform filtering
        results = []
        for media in self.media_assets.values():
            if category is not None and media.get("category") != category:
                continue
            if media_type is not None and media.get("media_type") != media_type:
                continue
            if event_id is not None and media.get("event_id") != event_id:
                continue
            if upload_date is not None and media.get("upload_date") != upload_date:
                continue
            if tags:
                asset_tags = set(media.get("tags", []))
                if not all(tag in asset_tags for tag in tags):
                    continue
            results.append(media)

        return {"success": True, "data": results}

    def get_media_by_event_id(self, event_id: str) -> dict:
        """
        Retrieve all media assets associated with a specific event_id.

        Args:
            event_id (str): The unique ID of the event whose media assets to retrieve.

        Returns:
            dict:
                success (bool): True if search completed.
                data (List[MediaAssetInfo]): List of all matching media assets (may be empty).
            or
                success (bool): False on error.
                error (str): Reason for failure.
    
        Constraints:
            - Only returns media assets where 'event_id' matches exactly.

            Edge cases:
            - If the given event_id does not exist, returns success with empty list.
            - If no media assets are linked to the given event_id, returns success with empty list.
        """
        # (Optional) Check if event exists; depending on design, can return error if event_id doesn't exist.
        # Here, we simply return empty if no such event (as the description doesn't require existence verification).
        media_list = [
            asset for asset in self.media_assets.values()
            if asset.get("event_id") == event_id
        ]
        return { "success": True, "data": media_list }

    def get_media_by_id(self, media_id: str) -> dict:
        """
        Retrieve the metadata and file location of a specific media asset by media_id.

        Args:
            media_id (str): The unique identifier of the media asset.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": MediaAssetInfo  # All metadata of the media asset
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Media asset not found"
                    }

        Constraints:
            - media_id must exist in the system.
        """
        if media_id not in self.media_assets:
            return { "success": False, "error": "Media asset not found" }
        return { "success": True, "data": self.media_assets[media_id] }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve event information for a given unique event_id.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict:
                - If found: { "success": True, "data": EventInfo }
                - If not found: { "success": False, "error": "Event not found." }

        Constraints:
            - event_id must exist in the system's event records.
        """
        event = self.events.get(event_id)
        if event is not None:
            return { "success": True, "data": event }
        else:
            return { "success": False, "error": "Event not found." }

    def list_media_associated_teams(self, media_id: str) -> dict:
        """
        List all team records (TeamInfo) associated with the specified media asset.

        Args:
            media_id (str): Unique identifier for the media asset.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[TeamInfo],  # List with team info of associated teams
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Media asset does not exist.",
                    }

        Constraints:
            - The media asset (media_id) must exist.
            - Result includes only teams which exist in the system.
        """
        if media_id not in self.media_assets:
            return { "success": False, "error": "Media asset does not exist." }

        media_asset = self.media_assets[media_id]
        associated_team_infos = []
        for team_id in media_asset.get("team_ids", []):
            if team_id in self.teams:
                associated_team_infos.append(self.teams[team_id])
            # If a team_id is missing from self.teams, skip (data issue).
        return {
            "success": True,
            "data": associated_team_infos
        }

    def validate_media_team_association(self, media_id: str, team_id: str) -> dict:
        """
        Confirm whether a given media asset is linked to a specific team.

        Args:
            media_id (str): Unique identifier for the media asset.
            team_id (str): Unique identifier for the team.

        Returns:
            dict: {
                "success": True,
                "data": bool   # True if linked, False if not linked
            }
            or,
            {
                "success": False,
                "error": str   # error description, e.g. if media or team not found
            }

        Constraints:
            - Both media_id and team_id must be valid (exist in the system).
            - Association means team_id appears in media_asset["team_ids"].
        """
        # Check that media exists
        media = self.media_assets.get(media_id)
        if media is None:
            return { "success": False, "error": "Media asset does not exist" }

        # Check that team exists
        if team_id not in self.teams:
            return { "success": False, "error": "Team does not exist" }

        # Validate association
        is_linked = team_id in media.get('team_ids', [])
        return { "success": True, "data": is_linked }

    def upload_media_asset(
        self,
        media_id: str,
        file_path: str,
        media_type: str,
        upload_date: str,
        category: str,
        description: str,
        tags: List[str],
        team_ids: List[str],
        event_id: str = None
    ) -> dict:
        """
        Add (upload) a new media asset to the system.

        Args:
            media_id (str): Unique ID for the media asset.
            file_path (str): File path or location.
            media_type (str): Type of media (photo, video, etc.).
            upload_date (str): Date the media was uploaded.
            category (str): Media category/tag.
            description (str): Descriptive text.
            tags (List[str]): Tags for search/categorization.
            team_ids (List[str]): IDs of teams this media is associated with; must contain at least one valid team.
            event_id (str, optional): ID of associated event, if any.

        Returns:
            dict: { "success": True, "message": ... } on success, or
                  { "success": False, "error": ... } on failure.

        Constraints:
            - Each MediaAsset must have a unique media_id.
            - Must be associated with at least one team (team_ids non-empty and all must exist).
            - If event_id is given (not None), it must exist.
        """
        # Check for unique media_id
        if media_id in self.media_assets:
            return { "success": False, "error": "Media ID already exists." }

        # team_ids must be non-empty and all team_ids must exist
        if not team_ids or not isinstance(team_ids, list):
            return { "success": False, "error": "At least one team_id must be provided and must be a list." }
        missing_teams = [tid for tid in team_ids if tid not in self.teams]
        if missing_teams:
            return { "success": False, "error": f"The following team_id(s) do not exist: {', '.join(missing_teams)}" }

        # If event_id is specified, check existence (optional)
        if event_id is not None and event_id != "":
            if event_id not in self.events:
                return { "success": False, "error": "Specified event_id does not exist." }

        # Add media asset
        asset_info: MediaAssetInfo = {
            "media_id": media_id,
            "file_path": file_path,
            "media_type": media_type,
            "upload_date": upload_date,
            "category": category,
            "event_id": event_id if event_id else "",
            "description": description,
            "tags": tags,
            "team_ids": team_ids
        }
        self.media_assets[media_id] = asset_info
        return { "success": True, "message": "Media asset uploaded successfully." }

    def update_media_metadata(
        self,
        media_id: str,
        category: str = None,
        tags: List[str] = None,
        description: str = None,
        team_ids: List[str] = None,
        event_id: str = None,
        file_path: str = None,
        media_type: str = None,
        upload_date: str = None
    ) -> dict:
        """
        Update the metadata fields of an existing media asset.
        Any non-None metadata fields will be updated for the specified asset.

        Args:
            media_id (str): The media asset's unique identifier.
            category (str, optional): New media category.
            tags (List[str], optional): New list of tags.
            description (str, optional): New description.
            team_ids (List[str], optional): New list of associated team IDs (must be valid, at least one).
            event_id (str, optional): New associated event ID (must exist if provided).
            file_path (str, optional): New file path/location.
            media_type (str, optional): New media type.
            upload_date (str, optional): New upload date.

        Returns:
            dict: {
                "success": True,
                "message": "Media asset metadata updated"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - media_id must exist.
            - If team_ids is updated, must be non-empty and all values exist in teams.
            - If event_id is updated and is not None, event_id must exist.
        """
        # Check if media asset exists
        if media_id not in self.media_assets:
            return {"success": False, "error": "Media asset does not exist"}

        asset = self.media_assets[media_id]
        updated = False

        # Category
        if category is not None:
            asset['category'] = category
            updated = True

        # Tags
        if tags is not None:
            asset['tags'] = tags
            updated = True

        # Description
        if description is not None:
            asset['description'] = description
            updated = True

        # Team IDs
        if team_ids is not None:
            if not team_ids or not isinstance(team_ids, list):
                return {"success": False, "error": "At least one valid team_id is required"}
            # Validate all team_ids exist
            for tid in team_ids:
                if tid not in self.teams:
                    return {"success": False, "error": f"Team ID '{tid}' does not exist"}
            asset['team_ids'] = team_ids
            updated = True

        # Event ID
        if event_id is not None:
            if event_id and event_id not in self.events:
                return {"success": False, "error": f"Event ID '{event_id}' does not exist"}
            asset['event_id'] = event_id
            updated = True

        # File path
        if file_path is not None:
            asset['file_path'] = file_path
            updated = True

        # Media type
        if media_type is not None:
            asset['media_type'] = media_type
            updated = True

        # Upload date
        if upload_date is not None:
            asset['upload_date'] = upload_date
            updated = True

        # After all updates, check constraint: must be linked to at least one team
        if not asset['team_ids']:
            return {"success": False, "error": "Each media asset must be associated with at least one team"}

        if updated:
            return {"success": True, "message": "Media asset metadata updated"}
        else:
            return {"success": True, "message": "No metadata fields were changed"}

    def delete_media_asset(self, media_id: str) -> dict:
        """
        Remove a media asset from the system by its media_id.

        Args:
            media_id (str): The unique identifier of the media asset to delete.

        Returns:
            dict: 
                On success: {"success": True, "message": "Media asset <media_id> deleted."}
                On failure: {"success": False, "error": "Media asset does not exist."}

        Constraints:
            - The specified media_id must exist in the media_assets dictionary.
            - No operation if the media_id does not exist; return an error message.
        """
        if media_id not in self.media_assets:
            return {"success": False, "error": "Media asset does not exist."}
        del self.media_assets[media_id]
        return {"success": True, "message": f"Media asset {media_id} deleted."}

    def link_media_to_team(self, media_id: str, team_id: str) -> dict:
        """
        Associate an existing media asset with an additional team.

        Args:
            media_id (str): The unique identifier of the media asset.
            team_id (str): The unique identifier of the team to be linked.

        Returns:
            dict: If successful,
                    {
                        "success": True,
                        "message": "Media asset <media_id> successfully linked to team <team_id>"
                    }
                  If an error occurs,
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Both media_id and team_id must exist.
            - Media asset must not already be associated with the team (no duplicates).
            - Each MediaAsset must have at least one team in its team_ids (always satisfied when linking).
        """
        # Check if media asset exists
        if media_id not in self.media_assets:
            return {"success": False, "error": f"Media asset '{media_id}' does not exist"}
        # Check if team exists
        if team_id not in self.teams:
            return {"success": False, "error": f"Team '{team_id}' does not exist"}
        media_asset = self.media_assets[media_id]
        # Check if already linked
        if team_id in media_asset["team_ids"]:
            return {"success": False, "error": f"Media asset '{media_id}' is already linked to team '{team_id}'"}
        # Link the team to the media asset
        media_asset["team_ids"].append(team_id)
        # Update the asset record
        self.media_assets[media_id] = media_asset
        return {
            "success": True,
            "message": f"Media asset '{media_id}' successfully linked to team '{team_id}'"
        }

    def unlink_media_from_team(self, media_id: str, team_id: str) -> dict:
        """
        Remove an association between a media asset and a team, ensuring that at least one team remains linked.

        Args:
            media_id (str): Unique identifier for the media asset.
            team_id (str): Unique identifier for the team to be unlinked.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Unlinked team <team_id> from media asset <media_id>." }
                On failure:
                    { "success": False, "error": <description of reason> }

        Constraints:
            - Each MediaAsset must always be linked to at least one team after the operation.
            - team_id must be present in the media asset's team_ids.
        """
        # Check media asset existence
        asset = self.media_assets.get(media_id)
        if asset is None:
            return { "success": False, "error": f"Media asset with ID '{media_id}' does not exist." }
    
        # Check team existence
        if team_id not in self.teams:
            return { "success": False, "error": f"Team with ID '{team_id}' does not exist." }
    
        # Check association
        if team_id not in asset['team_ids']:
            return { "success": False, "error": f"Team ID '{team_id}' is not associated with media asset '{media_id}'." }
    
        # Check constraint: at least one must remain
        if len(asset['team_ids']) == 1:
            return { "success": False, "error": "Cannot unlink the last remaining team from the media asset." }
    
        # Do the unlink
        asset['team_ids'].remove(team_id)
        # Update asset in store (since dict is mutable, this suffices)
        self.media_assets[media_id] = asset

        return { "success": True, "message": f"Unlinked team '{team_id}' from media asset '{media_id}'." }

    def add_team(
        self,
        team_id: str,
        name: str,
        sport_type: str,
        league: str,
        other_metadata: str
    ) -> dict:
        """
        Add a new sports team record to the system.

        Args:
            team_id (str): Unique identifier for the team.
            name (str): Name of the team.
            sport_type (str): Sport type for the team.
            league (str): League or division for the team.
            other_metadata (str): Any additional metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Team <team_id> added successfully."
            } on success,
            or
            {
                "success": False,
                "error": "Team ID already exists."
            } if duplicate team_id.

        Constraints:
            - team_id must be unique in the system.
        """
        if team_id in self.teams:
            return {"success": False, "error": "Team ID already exists."}

        team_info: TeamInfo = {
            "team_id": team_id,
            "name": name,
            "sport_type": sport_type,
            "league": league,
            "other_metadata": other_metadata
        }
        self.teams[team_id] = team_info
        return {"success": True, "message": f"Team {team_id} added successfully."}

    def update_team_info(
        self, 
        team_id: str, 
        name: str = None, 
        sport_type: str = None, 
        league: str = None, 
        other_metadata: str = None
    ) -> dict:
        """
        Update the metadata fields of an existing team.

        Args:
            team_id (str): Team identifier for the team to update. Must exist.
            name (str, optional): New team name.
            sport_type (str, optional): New sport type.
            league (str, optional): New league.
            other_metadata (str, optional): New other metadata string.

        Returns:
            dict: On success:
                { "success": True, "message": "Team info updated for team_id <team_id>" }
            On failure:
                { "success": False, "error": <error_message> }

        Constraints:
            - team_id must correspond to an existing team.
            - At least one field should be specified for update (name, sport_type, league, other_metadata).
            - Only these fields can be updated; team_id itself is not modifiable.
        """
        if team_id not in self.teams:
            return { "success": False, "error": f"Team with team_id '{team_id}' does not exist" }
    
        updatable = ["name", "sport_type", "league", "other_metadata"]
        updates = {}
        for key in updatable:
            val = locals()[key]
            if val is not None:
                updates[key] = val
    
        if not updates:
            return { "success": False, "error": "No fields provided for update" }
    
        # Update the team info
        for key, value in updates.items():
            self.teams[team_id][key] = value
    
        return { "success": True, "message": f"Team info updated for team_id '{team_id}'" }

    def add_event(
        self,
        event_id: str,
        name: str,
        date: str,
        location: str,
        participating_team_id: str
    ) -> dict:
        """
        Add a new event record to the system.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Event name.
            date (str): Event date (string format).
            location (str): Event location.
            participating_team_id (str): Team ID of the participating team.

        Returns:
            dict: 
                - { "success": True, "message": "Event added successfully" }
                - { "success": False, "error": "Event ID already exists" }
                - { "success": False, "error": "Participating team ID does not exist" }
    
        Constraints:
            - event_id must be unique.
            - participating_team_id must reference an existing team.
        """
        if event_id in self.events:
            return { "success": False, "error": "Event ID already exists" }
        if participating_team_id not in self.teams:
            return { "success": False, "error": "Participating team ID does not exist" }
    
        new_event: EventInfo = {
            "event_id": event_id,
            "name": name,
            "date": date,
            "location": location,
            "participating_team_id": participating_team_id
        }
        self.events[event_id] = new_event
        return { "success": True, "message": "Event added successfully" }

    def update_event_info(
        self,
        event_id: str,
        name: str = None,
        date: str = None,
        location: str = None,
        participating_team_id: str = None
    ) -> dict:
        """
        Update the information of an existing event (name, date, location, team).

        Args:
            event_id (str): Unique identifier for the event.
            name (str, optional): New name for the event.
            date (str, optional): New date for the event.
            location (str, optional): New location for the event.
            participating_team_id (str, optional): New participating team ID (must exist in teams if provided).

        Returns:
            dict:
                - If success: {"success": True, "message": "Event information updated successfully"}
                - If error: {"success": False, "error": <error_message>}

        Constraints:
            - event_id must correspond to an existing event.
            - If participating_team_id is provided, it must reference an existing team.
            - At least one updatable field must be provided.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        if not any([name, date, location, participating_team_id]):
            return {"success": False, "error": "No update fields provided"}

        event = self.events[event_id]

        if participating_team_id is not None:
            if participating_team_id not in self.teams:
                return {"success": False, "error": "Participating team does not exist"}
            event["participating_team_id"] = participating_team_id

        if name is not None:
            event["name"] = name
        if date is not None:
            event["date"] = date
        if location is not None:
            event["location"] = location

        self.events[event_id] = event  # Not strictly needed, but explicit update

        return {"success": True, "message": "Event information updated successfully"}


class SportsTeamMediaAssetManagementSystem(BaseEnv):
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

    def get_team_by_id(self, **kwargs):
        return self._call_inner_tool('get_team_by_id', kwargs)

    def list_all_teams(self, **kwargs):
        return self._call_inner_tool('list_all_teams', kwargs)

    def get_media_by_team_id(self, **kwargs):
        return self._call_inner_tool('get_media_by_team_id', kwargs)

    def search_media_by_metadata(self, **kwargs):
        return self._call_inner_tool('search_media_by_metadata', kwargs)

    def get_media_by_event_id(self, **kwargs):
        return self._call_inner_tool('get_media_by_event_id', kwargs)

    def get_media_by_id(self, **kwargs):
        return self._call_inner_tool('get_media_by_id', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_media_associated_teams(self, **kwargs):
        return self._call_inner_tool('list_media_associated_teams', kwargs)

    def validate_media_team_association(self, **kwargs):
        return self._call_inner_tool('validate_media_team_association', kwargs)

    def upload_media_asset(self, **kwargs):
        return self._call_inner_tool('upload_media_asset', kwargs)

    def update_media_metadata(self, **kwargs):
        return self._call_inner_tool('update_media_metadata', kwargs)

    def delete_media_asset(self, **kwargs):
        return self._call_inner_tool('delete_media_asset', kwargs)

    def link_media_to_team(self, **kwargs):
        return self._call_inner_tool('link_media_to_team', kwargs)

    def unlink_media_from_team(self, **kwargs):
        return self._call_inner_tool('unlink_media_from_team', kwargs)

    def add_team(self, **kwargs):
        return self._call_inner_tool('add_team', kwargs)

    def update_team_info(self, **kwargs):
        return self._call_inner_tool('update_team_info', kwargs)

    def add_event(self, **kwargs):
        return self._call_inner_tool('add_event', kwargs)

    def update_event_info(self, **kwargs):
        return self._call_inner_tool('update_event_info', kwargs)

