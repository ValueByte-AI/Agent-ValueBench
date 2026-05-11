# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict, Any
import time
import uuid



class TournamentInfo(TypedDict):
    tournament_id: str
    name: str
    start_date: str
    end_date: str
    location: str
    metadata: Dict[str, Any]
    logo_id: Optional[str]

class LogoInfo(TypedDict):
    logo_id: str
    image_data: str  # Could be a raw string, URL, or file path
    file_type: str
    uploaded_at: str

class ParticipantInfo(TypedDict, total=False):
    participant_id: str
    name: str
    team_name: Optional[str]
    tournament_id: str
    role: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    tournament_id: str
    match_times: List[str]
    bracket_structure: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing esports tournaments, participants, branding assets, and event schedules.

        Constraints:
        - Each tournament may have at most one primary logo associated.
        - Logos (branding assets) must be uploaded and available before they can be linked to tournaments.
        - Tournament IDs must be unique.
        - Schedule and participant records must reference existing tournaments.
        """
        # Tournaments: {tournament_id: TournamentInfo}
        #   - tournament_id, name, start_date, end_date, location, metadata, logo_id
        self.tournaments: Dict[str, TournamentInfo] = {}

        # Logos: {logo_id: LogoInfo}
        #   - logo_id, image_data, file_type, uploaded_at
        self.logos: Dict[str, LogoInfo] = {}

        # Participants: {participant_id: ParticipantInfo}
        #   - participant_id, name, team_name (optional), tournament_id, role
        self.participants: Dict[str, ParticipantInfo] = {}

        # Schedules: {schedule_id: ScheduleInfo}
        #   - schedule_id, tournament_id, match_times, bracket_structure
        self.schedules: Dict[str, ScheduleInfo] = {}

    def get_tournament_by_id(self, tournament_id: str) -> dict:
        """
        Retrieve TournamentInfo details for the given tournament_id.

        Args:
            tournament_id (str): Unique tournament identifier.

        Returns:
            dict: 
            - On success: { "success": True, "data": TournamentInfo }
            - On failure: { "success": False, "error": "Tournament not found" }

        Constraints:
            - tournament_id must exist in the system.
        """
        tournament = self.tournaments.get(tournament_id)
        if tournament is None:
            return { "success": False, "error": "Tournament not found" }
        return { "success": True, "data": tournament }

    def get_logo_id_for_tournament(self, tournament_id: str) -> dict:
        """
        Retrieve the logo_id associated with a specific tournament_id.

        Args:
            tournament_id (str): The ID of the tournament.

        Returns:
            dict: {
                "success": True,
                "data": str or None  # logo_id if exists, or None if no logo linked
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Tournament does not exist"
            }

        Constraints:
            - Tournament ID must exist in the system.
            - Each tournament may have at most one primary logo associated.
        """
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return { "success": False, "error": "Tournament does not exist" }

        return { "success": True, "data": tournament.get("logo_id") }

    def get_logo_by_id(self, logo_id: str) -> dict:
        """
        Retrieve logo metadata (LogoInfo) for the specified logo_id.

        Args:
            logo_id (str): Unique identifier for the logo asset.

        Returns:
            dict: {
                "success": True,
                "data": LogoInfo  # logo metadata,
            }
            or
            {
                "success": False,
                "error": str  # error description, e.g., if logo_id does not exist.
            }

        Constraints:
            - The specified logo_id must exist in the system.
        """
        logo = self.logos.get(logo_id)
        if logo is None:
            return {"success": False, "error": "Logo not found"}
        return {"success": True, "data": logo}

    def list_tournaments(self) -> dict:
        """
        List all tournaments and their basic info.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TournamentInfo],  # A list of tournament objects (empty if none)
            }

        Constraints:
            - No constraints apply for listing; all tournaments in the system are returned.
        """
        tournament_list = list(self.tournaments.values())
        return { "success": True, "data": tournament_list }

    def list_logos(self) -> dict:
        """
        Lists all logo (branding asset) records available in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[LogoInfo]  # List of all logo info records (may be empty)
            }
        Constraints:
            - No input required.
            - Always succeeds (returns all logos or empty list).
        """
        return {
            "success": True,
            "data": list(self.logos.values())
        }

    def get_schedule_by_tournament_id(self, tournament_id: str) -> dict:
        """
        Retrieve schedule and bracket information for a specified tournament.

        Args:
            tournament_id (str): Unique identifier for the tournament.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ScheduleInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message
                    }

        Constraints:
            - tournament_id must exist.
            - Schedule must exist for the given tournament_id.
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        for schedule in self.schedules.values():
            if schedule["tournament_id"] == tournament_id:
                return {"success": True, "data": schedule}

        return {"success": False, "error": "No schedule found for this tournament"}

    def list_participants_by_tournament(self, tournament_id: str) -> dict:
        """
        Get all participants for a specific tournament.

        Args:
            tournament_id (str): The unique identifier of the tournament.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo]  # List (possibly empty) of all participants for that tournament.
            }
            or
            {
                "success": False,
                "error": str  # Description if the tournament does not exist.
            }

        Constraints:
            - Tournament must exist.
            - Participants are filtered by matching tournament_id.
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        participant_list = [
            participant_info
            for participant_info in self.participants.values()
            if participant_info.get("tournament_id") == tournament_id
        ]
        return {"success": True, "data": participant_list}

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve participant information given a participant_id.

        Args:
            participant_id (str): The unique identifier for the participant.

        Returns:
            dict:
                On success:
                    { "success": True, "data": ParticipantInfo }
                On error (not found):
                    { "success": False, "error": "Participant not found" }
        Constraints:
            - The participant_id must exist in the self.participants dictionary.
        """
        participant = self.participants.get(participant_id)
        if participant is not None:
            return { "success": True, "data": participant }
        else:
            return { "success": False, "error": "Participant not found" }


    def upload_logo(self, image_data: str, file_type: str) -> dict:
        """
        Add a new logo asset (image_data, file_type) to the system.

        Args:
            image_data (str): The content, URL, or file path of the logo image.
            file_type (str): The file type of the logo (e.g., 'png', 'jpg').

        Returns:
            dict: 
            On success:
              {
                "success": True,
                "message": "Logo uploaded successfully.",
                "logo_id": str  # The unique id of the uploaded logo
              }
            On failure:
              {
                "success": False,
                "error": str  # Description of the error
              }

        Constraints:
          - Both image_data and file_type must be non-empty.
          - logo_id must be unique in the system.
        """

        if not image_data or not isinstance(image_data, str):
            return {"success": False, "error": "Invalid or missing image_data."}
        if not file_type or not isinstance(file_type, str):
            return {"success": False, "error": "Invalid or missing file_type."}

        # Generate a unique logo_id using uuid4
        for _ in range(5):  # Retry up to 5 times in the rare event of a collision
            logo_id = str(uuid.uuid4())
            if logo_id not in self.logos:
                break
        else:
            return {"success": False, "error": "Failed to generate a unique logo_id."}

        uploaded_at = str(time.time())

        logo_info = {
            "logo_id": logo_id,
            "image_data": image_data,
            "file_type": file_type,
            "uploaded_at": uploaded_at
        }
        self.logos[logo_id] = logo_info

        return {
            "success": True,
            "message": "Logo uploaded successfully.",
            "logo_id": logo_id
        }

    def link_logo_to_tournament(self, tournament_id: str, logo_id: str) -> dict:
        """
        Associate an existing logo with a tournament, replacing any prior association.

        Args:
            tournament_id (str): The tournament to attach the logo.
            logo_id (str): The logo to be linked as branding asset.

        Returns:
            dict: {
                "success": True,
                "message": "Logo {logo_id} linked to tournament {tournament_id}."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Tournament must exist.
            - Logo must exist and be uploaded already.
            - Each tournament may have at most one primary logo (this will overwrite any previous).
        """
        if tournament_id not in self.tournaments:
            return { "success": False, "error": f"Tournament {tournament_id} does not exist" }
        if logo_id not in self.logos:
            return { "success": False, "error": f"Logo {logo_id} does not exist" }

        self.tournaments[tournament_id]["logo_id"] = logo_id

        return {
            "success": True,
            "message": f"Logo {logo_id} linked to tournament {tournament_id}."
        }

    def create_tournament(
        self,
        tournament_id: str,
        name: str,
        start_date: str,
        end_date: str,
        location: str,
        metadata: dict,
        logo_id: Optional[str] = None
    ) -> dict:
        """
        Add a new tournament record with the required fields.

        Args:
            tournament_id (str): Unique tournament identifier.
            name (str): Tournament name.
            start_date (str): Tournament start date (format: YYYY-MM-DD, ISO, etc.).
            end_date (str): Tournament end date.
            location (str): Tournament venue/location.
            metadata (dict): Additional event metadata.
            logo_id (Optional[str], default=None): Optionally associate a logo (must already exist).

        Returns:
            dict: {
                "success": True,
                "message": "Tournament created successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Tournament ID must be unique.
            - If logo_id is provided, it must exist in the branding assets (logos).
            - At creation, no primary logo is required.
        """
        # Check for uniqueness of tournament_id
        if tournament_id in self.tournaments:
            return { "success": False, "error": "Tournament ID already exists" }

        # If logo_id is provided, check existence
        if logo_id is not None:
            if logo_id not in self.logos:
                return { "success": False, "error": "Provided logo_id does not exist" }

        # Prepare tournament info
        tournament_info: TournamentInfo = {
            "tournament_id": tournament_id,
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "metadata": metadata,
            "logo_id": logo_id
        }

        self.tournaments[tournament_id] = tournament_info

        return { "success": True, "message": "Tournament created successfully" }

    def update_tournament_info(
        self,
        tournament_id: str,
        name: str = None,
        start_date: str = None,
        end_date: str = None,
        location: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Modify an existing tournament's metadata.
    
        Args:
            tournament_id (str): ID of the tournament to modify.
            name (str, optional): New name for the tournament.
            start_date (str, optional): New start date.
            end_date (str, optional): New end date.
            location (str, optional): New location.
            metadata (dict, optional): New metadata dictionary (replacing existing).
        
        Returns:
            dict: {
                "success": True,
                "message": "Tournament info updated for <tournament_id>"
            } on success,
            or {
                "success": False,
                "error": <error_reason>
            } on error.
        
        Constraints:
            - Tournament must exist.
            - Only allowed fields (`name`, `start_date`, `end_date`, `location`, `metadata`) may be updated.
            - `tournament_id` is immutable.
            - If no updatable fields are provided, update is a no-op but still "successful".
        """
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist"}

        tournament = self.tournaments[tournament_id]
        updated = False

        if name is not None:
            tournament["name"] = name
            updated = True
        if start_date is not None:
            tournament["start_date"] = start_date
            updated = True
        if end_date is not None:
            tournament["end_date"] = end_date
            updated = True
        if location is not None:
            tournament["location"] = location
            updated = True
        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "Metadata must be a dictionary"}
            tournament["metadata"] = metadata
            updated = True

        self.tournaments[tournament_id] = tournament

        return {
            "success": True,
            "message": (
                f"Tournament info updated for {tournament_id}"
                if updated else f"No fields updated for {tournament_id}"
            )
        }

    def add_participant(
        self,
        participant_id: str,
        name: str,
        tournament_id: str,
        role: str,
        team_name: Optional[str] = None,
    ) -> dict:
        """
        Register a new participant to a tournament.

        Args:
            participant_id (str): Unique identifier for the participant.
            name (str): Name of the participant.
            tournament_id (str): ID of the tournament the participant will join. Must exist.
            role (str): Participant's role in the tournament.
            team_name (Optional[str]): Team name (optional).

        Returns:
            dict: {
                "success": True,
                "message": "Participant <participant_id> added to tournament <tournament_id>."
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - participant_id must be unique.
            - tournament_id must exist.
        """
        if participant_id in self.participants:
            return {"success": False, "error": "Participant ID already exists."}
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament ID does not exist."}
        if not name or not participant_id or not role:
            return {"success": False, "error": "Missing required participant fields."}

        participant: ParticipantInfo = {
            "participant_id": participant_id,
            "name": name,
            "tournament_id": tournament_id,
            "role": role
        }
        if team_name is not None:
            participant["team_name"] = team_name

        self.participants[participant_id] = participant
        return {
            "success": True,
            "message": f"Participant {participant_id} added to tournament {tournament_id}."
        }

    def update_participant_info(
        self,
        participant_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        team_name: Optional[str] = None
    ) -> dict:
        """
        Update the details for a participant: name, role, team_name.

        Args:
            participant_id (str): The participant's unique ID.
            name (Optional[str]): New name (if updating).
            role (Optional[str]): New role (if updating).
            team_name (Optional[str]): New team name (if updating; can be set to None for no team).

        Returns:
            dict: {
                "success": True,
                "message": "Participant info updated for participant_id <id>"
            } or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only provided fields are updated.
            - Participant must exist.
            - At least one updatable field should be provided.
            - Does not update participant_id or tournament_id.
        """
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant not found." }

        if name is None and role is None and team_name is None:
            return { "success": False, "error": "No update fields provided." }

        if name is not None:
            self.participants[participant_id]["name"] = name
        if role is not None:
            self.participants[participant_id]["role"] = role
        if team_name is not None:
            self.participants[participant_id]["team_name"] = team_name

        return {
            "success": True,
            "message": f"Participant info updated for participant_id {participant_id}"
        }

    def create_or_update_schedule(
        self,
        schedule_id: str,
        tournament_id: str,
        match_times: list,
        bracket_structure: dict
    ) -> dict:
        """
        Create a new schedule or update an existing schedule for a tournament.
    
        Args:
            schedule_id (str): Identifier for the schedule. Unique if creating new.
            tournament_id (str): The tournament's unique identifier (must exist).
            match_times (List[str]): List of match time strings.
            bracket_structure (Dict[str, Any]): Dictionary for bracket organization.

        Returns:
            dict: {
                "success": True,
                "message": description
            }
            or
            {
                "success": False,
                "error": error description
            }
    
        Constraints:
            - The referenced tournament_id must exist.
            - schedule_id must be unique if creating new.
            - schedule_id may be updated if it exists.
            - match_times must be a list; bracket_structure must be a dict.
        """
        # Validate tournament existence
        if tournament_id not in self.tournaments:
            return {"success": False, "error": "Tournament does not exist."}

        if not isinstance(match_times, list):
            return {"success": False, "error": "match_times must be a list."}
        if not isinstance(bracket_structure, dict):
            return {"success": False, "error": "bracket_structure must be a dictionary."}

        schedule_data = {
            "schedule_id": schedule_id,
            "tournament_id": tournament_id,
            "match_times": match_times,
            "bracket_structure": bracket_structure
        }

        if schedule_id in self.schedules:
            # Update existing schedule
            self.schedules[schedule_id].update(schedule_data)
            return {
                "success": True,
                "message": f"Schedule '{schedule_id}' updated for tournament '{tournament_id}'."
            }
        else:
            # Create new schedule
            self.schedules[schedule_id] = schedule_data
            return {
                "success": True,
                "message": f"Schedule '{schedule_id}' created for tournament '{tournament_id}'."
            }

    def remove_logo_from_tournament(self, tournament_id: str) -> dict:
        """
        Unlink/remove the logo association from a specified tournament.

        Args:
            tournament_id (str): The unique identifier for the tournament.

        Returns:
            dict: {
                "success": True,
                "message": "Logo unlinked from tournament."
            }
            or
            {
                "success": False,
                "error": "Tournament does not exist."
            }

        Constraints:
            - Tournament must exist.
            - The logo itself is not deleted, only the association (logo_id) is unset in the tournament.
        """
        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament does not exist." }
        # Unlink the logo if it was set
        self.tournaments[tournament_id]["logo_id"] = None
        return { "success": True, "message": "Logo unlinked from tournament." }

    def delete_logo(self, logo_id: str) -> dict:
        """
        Remove a logo asset from the system if it is not used (not linked to any tournament).

        Args:
            logo_id (str): The unique identifier of the logo to be deleted.
    
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Logo {logo_id} deleted from the system."
                    }
                On failure (logo in use or not found):
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - Logo must exist in the system.
            - Logo must not be linked as the primary logo (`logo_id`) of any tournament.
        """
        # Check if logo exists
        if logo_id not in self.logos:
            return { "success": False, "error": "Logo not found." }

        # Check if the logo is currently used in any tournament
        for tournament in self.tournaments.values():
            if tournament.get("logo_id") == logo_id:
                return {
                    "success": False,
                    "error": "Logo is currently linked to a tournament and cannot be deleted."
                }

        # Remove the logo
        del self.logos[logo_id]
        return {
            "success": True,
            "message": f"Logo {logo_id} deleted from the system."
        }

    def delete_tournament(self, tournament_id: str) -> dict:
        """
        Permanently remove a tournament from the system, including its references in participants and schedules.

        Args:
            tournament_id (str): Unique tournament ID to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Tournament <id> and all its references have been removed"
            }
            OR
            {
                "success": False,
                "error": str  # Reason why deletion failed
            }

        Constraints & Details:
            - Tournament must exist to be deleted.
            - All participants and schedules referencing this tournament will be removed.
            - The linked logo asset will NOT be deleted from the system, only the association.
            - Leaves logo asset for possible re-use elsewhere.
        """
        # Check if tournament exists
        if tournament_id not in self.tournaments:
            return { "success": False, "error": "Tournament does not exist" }

        # Remove all participants referencing this tournament
        participant_ids_to_remove = [
            pid for pid, pinfo in self.participants.items()
            if pinfo.get("tournament_id") == tournament_id
        ]
        for pid in participant_ids_to_remove:
            del self.participants[pid]

        # Remove all schedules referencing this tournament
        schedule_ids_to_remove = [
            sid for sid, sinfo in self.schedules.items()
            if sinfo.get("tournament_id") == tournament_id
        ]
        for sid in schedule_ids_to_remove:
            del self.schedules[sid]

        # Remove the tournament itself
        del self.tournaments[tournament_id]

        # Note: logo asset is NOT deleted; only its reference from tournament is removed above

        return {
            "success": True,
            "message": f"Tournament {tournament_id} and all its references have been removed"
        }

    def delete_participant(self, participant_id: str) -> dict:
        """
        Remove a participant from the tournament system by their participant_id.

        Args:
            participant_id (str): The unique identifier for the participant to be removed.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Participant <participant_id> removed from tournament."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Participant <participant_id> does not exist."
                    }

        Constraints:
            - The participant must exist in the system to be removed.
        """
        if participant_id not in self.participants:
            return { "success": False, "error": f"Participant {participant_id} does not exist." }
    
        del self.participants[participant_id]
        return { "success": True, "message": f"Participant {participant_id} removed from tournament." }

    def delete_schedule(self, schedule_id: str) -> dict:
        """
        Delete a tournament schedule by its schedule_id.

        Args:
            schedule_id (str): The unique identifier of the schedule to delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Schedule deleted successfully" }
                On failure: { "success": False, "error": "Schedule not found" }

        Constraints:
            - The schedule must exist to be deleted.
        """
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule not found" }
    
        del self.schedules[schedule_id]
        return { "success": True, "message": "Schedule deleted successfully" }


class EsportsTournamentManagementSystem(BaseEnv):
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

    def get_tournament_by_id(self, **kwargs):
        return self._call_inner_tool('get_tournament_by_id', kwargs)

    def get_logo_id_for_tournament(self, **kwargs):
        return self._call_inner_tool('get_logo_id_for_tournament', kwargs)

    def get_logo_by_id(self, **kwargs):
        return self._call_inner_tool('get_logo_by_id', kwargs)

    def list_tournaments(self, **kwargs):
        return self._call_inner_tool('list_tournaments', kwargs)

    def list_logos(self, **kwargs):
        return self._call_inner_tool('list_logos', kwargs)

    def get_schedule_by_tournament_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_tournament_id', kwargs)

    def list_participants_by_tournament(self, **kwargs):
        return self._call_inner_tool('list_participants_by_tournament', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def upload_logo(self, **kwargs):
        return self._call_inner_tool('upload_logo', kwargs)

    def link_logo_to_tournament(self, **kwargs):
        return self._call_inner_tool('link_logo_to_tournament', kwargs)

    def create_tournament(self, **kwargs):
        return self._call_inner_tool('create_tournament', kwargs)

    def update_tournament_info(self, **kwargs):
        return self._call_inner_tool('update_tournament_info', kwargs)

    def add_participant(self, **kwargs):
        return self._call_inner_tool('add_participant', kwargs)

    def update_participant_info(self, **kwargs):
        return self._call_inner_tool('update_participant_info', kwargs)

    def create_or_update_schedule(self, **kwargs):
        return self._call_inner_tool('create_or_update_schedule', kwargs)

    def remove_logo_from_tournament(self, **kwargs):
        return self._call_inner_tool('remove_logo_from_tournament', kwargs)

    def delete_logo(self, **kwargs):
        return self._call_inner_tool('delete_logo', kwargs)

    def delete_tournament(self, **kwargs):
        return self._call_inner_tool('delete_tournament', kwargs)

    def delete_participant(self, **kwargs):
        return self._call_inner_tool('delete_participant', kwargs)

    def delete_schedule(self, **kwargs):
        return self._call_inner_tool('delete_schedule', kwargs)

