# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid
from typing import Optional, Dict
import copy



class UserInfo(TypedDict):
    _id: str  # State: user ID
    name: str
    role: str
    contact_info: str
    notification_preference: str  # Fixed typo from definition

class EventInfo(TypedDict):
    event_id: str  # State: event ID
    title: str
    description: str
    start_datetime: str  # ISO datetime string
    end_datetime: str    # ISO datetime string
    location: str
    event_type: str
    organizer_id: str

class ParticipantInfo(TypedDict):
    event_id: str
    user_id: str
    participation_status: str  # invited/confirmed/declined
    is_external: bool
    external_org_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing corporate calendar events and participation.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Participants: {event_id: [ParticipantInfo, ...]}
        self.participants: Dict[str, List[ParticipantInfo]] = {}

        # Constraints:
        # - No two events for the same user can overlap in time (conflict detection)
        # - Events must have at least one participant
        # - Event times must respect working hours and organizational constraints (if defined)
        # - External participants must be recorded for reference/notifications

    def _user_has_active_involvement(self, event_id: str, user_id: str) -> bool:
        event = self.events.get(event_id)
        if event and event.get("organizer_id") == user_id:
            return True
        for participant in self.participants.get(event_id, []):
            if (
                participant.get("is_external", False) is False
                and participant.get("user_id") == user_id
                and participant.get("participation_status") != "declined"
            ):
                return True
        return False

    def _parse_iso_datetime(self, value: str) -> datetime:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve a user's information by their name.

        Args:
            name (str): The name of the user to lookup.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo      # Info of the first user with the given name
            }
            or
            {
                "success": False,
                "error": str         # Description, e.g. user not found
            }

        Notes:
            - If multiple users share the same name, returns the first match found.
            - Matching is case-sensitive.
        """
        for user in self.users.values():
            if user["name"] == name:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information given a unique user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,   # User's information - if user is found
            }
            or
            {
                "success": False,
                "error": str,       # Error message if not found
            }

        Constraints:
            - user_id must exist in the system.
            - No authorization checks are enforced here.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User ID not found" }
        return { "success": True, "data": user }

    def list_users(self) -> dict:
        """
        Retrieve a list of all users in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # All user records (possibly empty)
            }
        """
        # Collect all user info records
        users_list = list(self.users.values())
        return {"success": True, "data": users_list}

    def get_events_for_user(self, user_id: str) -> dict:
        """
        List all events (with details and time) that a particular user is participating in.

        Args:
            user_id (str): The user ID whose events are to be retrieved.

        Returns:
            dict:
              - On success: { "success": True, "data": List[EventInfo] }
                  (List may be empty if user is not in any events)
              - On failure: { "success": False, "error": str }
                  (E.g., if user ID does not exist)

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = []
        for event_id, plist in self.participants.items():
            for pinfo in plist:
                if pinfo["user_id"] == user_id:
                    event_info = self.events.get(event_id)
                    if event_info is not None:
                        result.append(event_info)
                    # If event_info is None (somehow missing), silently skip

        return { "success": True, "data": result }


    def get_events_in_time_range_for_user(self, user_id: str, start_datetime: str, end_datetime: str) -> dict:
        """
        List events for a user within a specified time range.

        Args:
            user_id (str): The ID of the user to query for.
            start_datetime (str): Start of the interval, ISO format (inclusive).
            end_datetime (str): End of the interval, ISO format (exclusive).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[EventInfo],  # Events overlapping the interval for the user
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Only events for which the user is a participant are included.
            - Time intervals are compared as [event_start, event_end) and [start_datetime, end_datetime).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        try:
            query_start = self._parse_iso_datetime(start_datetime)
            query_end = self._parse_iso_datetime(end_datetime)
        except Exception:
            return {"success": False, "error": "Invalid datetime format"}

        relevant_event_ids = set()
        for event_id, plist in self.participants.items():
            for p in plist:
                if p["user_id"] == user_id and p["participation_status"] != "declined":
                    relevant_event_ids.add(event_id)
                    break  # Only need one matching participation

        results = []
        for event_id in relevant_event_ids:
            event = self.events.get(event_id)
            if not event:
                continue
            try:
                event_start = self._parse_iso_datetime(event["start_datetime"])
                event_end = self._parse_iso_datetime(event["end_datetime"])
            except Exception:
                continue  # skip malformed event times
        
            # [event_start, event_end) overlaps [query_start, query_end) if:
            # event_start < query_end AND event_end > query_start
            if event_start < query_end and event_end > query_start:
                results.append(event)

        results.sort(
            key=lambda event: (
                self._parse_iso_datetime(event["start_datetime"]),
                self._parse_iso_datetime(event["end_datetime"]),
                event["event_id"],
            )
        )

        return {"success": True, "data": results}

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the details of a specific event given its event_id.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict:
                - On success: {"success": True, "data": EventInfo}
                - On failure: {"success": False, "error": "Event not found"}

        Constraints:
            - The event must exist in the system.
        """
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def get_event_participants(self, event_id: str) -> dict:
        """
        Retrieve all participants (internal and external) for a specified event.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo]  # May be empty if no participants.
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., event does not exist.
            }

        Constraints:
            - The event must exist in the system.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}
    
        participants = self.participants.get(event_id, [])
        return {"success": True, "data": participants}


    def detect_conflicts_for_user(
        self, 
        user_id: str, 
        proposed_start_datetime: str, 
        proposed_end_datetime: str
    ) -> dict:
        """
        Check if a proposed event time range conflicts with any existing events for the specified user.

        Args:
            user_id (str): The user to check for scheduling conflicts.
            proposed_start_datetime (str): Proposed event start as ISO-formatted datetime string.
            proposed_end_datetime (str): Proposed event end as ISO-formatted datetime string.

        Returns:
            dict: {
                "success": True,
                "conflict": bool,
                "conflicting_events": List[EventInfo],  # All conflicting events for that user (possibly empty).
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - user_id must exist.
            - proposed_start_datetime must be strictly before proposed_end_datetime.
            - Uses time overlap: (event.start < proposed_end and event.end > proposed_start).
        """
        # Validate user_id
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Parse datetimes
        try:
            proposed_start = self._parse_iso_datetime(proposed_start_datetime)
            proposed_end = self._parse_iso_datetime(proposed_end_datetime)
        except Exception:
            return { "success": False, "error": "Invalid datetime format" }

        if proposed_start >= proposed_end:
            return { "success": False, "error": "Proposed start must be before end time" }

        # Find all events user is participating in
        conflicting_events: List[Dict[str, Any]] = []

        for event_id, participant_list in self.participants.items():
            # Check if user is a participant in this event (ignore "declined"? usually still blocks time if confirmed/invited)
            for participant in participant_list:
                if participant["user_id"] == user_id and participant["participation_status"] != "declined":
                    event = self.events.get(event_id)
                    if not event:
                        continue  # Defensive
                    try:
                        event_start = self._parse_iso_datetime(event["start_datetime"])
                        event_end = self._parse_iso_datetime(event["end_datetime"])
                    except Exception:
                        continue  # Malformed event, ignore

                    # Overlap: event_start < proposed_end and event_end > proposed_start
                    if (event_start < proposed_end) and (event_end > proposed_start):
                        conflicting_events.append(event)
                    break  # Found the user in this event. No need to check other participants

        return {
            "success": True,
            "conflict": len(conflicting_events) > 0,
            "conflicting_events": conflicting_events
        }

    def get_external_participants_for_event(self, event_id: str) -> dict:
        """
        List external participants and their organizations for a given event.

        Args:
            event_id (str): The ID of the event.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each with at least user_id, external_org_name, and participation_status
            }
            or
            {
                "success": False,
                "error": str  # Reason for error (e.g., event not found)
            }
        Constraints:
            - Event ID must refer to an existing event.
            - Only participants with is_external == True are returned.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event not found" }

        external_participants = []
        event_participants = self.participants.get(event_id, [])

        for participant in event_participants:
            if participant.get("is_external", False):
                external_participants.append({
                    "user_id": participant.get("user_id"),
                    "external_org_name": participant.get("external_org_name"),
                    "participation_status": participant.get("participation_status")
                })

        return { "success": True, "data": external_participants }

    def create_event(
        self,
        title: str,
        description: str,
        start_datetime: str,
        end_datetime: str,
        location: str,
        event_type: str,
        organizer_id: str
    ) -> dict:
        """
        Create a new event/meeting. Checks for organizer existence, valid times, and conflict with existing events.

        Args:
            title (str): Title of the event.
            description (str): Description of the event.
            start_datetime (str): ISO-formatted start datetime (e.g., '2023-05-01T14:00').
            end_datetime (str): ISO-formatted end datetime (e.g., '2023-05-01T15:00').
            location (str): Where the event will be held.
            event_type (str): Type/category of the event.
            organizer_id (str): User ID of the organizer.

        Returns:
            dict: On success -
                    { "success": True, "message": "...", "event_id": str }
                  On failure -
                    { "success": False, "error": str }
        Constraints:
            - Organizer user must exist.
            - Event time (start < end).
            - No time conflict with existing events for the organizer.
        """

        # 1. Validate organizer existence
        if organizer_id not in self.users:
            return { "success": False, "error": "Organizer user does not exist" }

        # 2. Validate start/end datetime
        try:
            start_dt = self._parse_iso_datetime(start_datetime)
            end_dt = self._parse_iso_datetime(end_datetime)
        except Exception:
            return { "success": False, "error": "Invalid datetime format" }
        if start_dt >= end_dt:
            return { "success": False, "error": "Event start time must be before end time" }

        # 3. Check conflicts against the organizer's existing scheduled commitments
        for existing_event_id, event in self.events.items():
            if self._user_has_active_involvement(existing_event_id, organizer_id):
                try:
                    exist_start = self._parse_iso_datetime(event['start_datetime'])
                    exist_end = self._parse_iso_datetime(event['end_datetime'])
                except Exception:
                    continue  # Ignore malformed events for robustness
                if not (end_dt <= exist_start or start_dt >= exist_end):
                    return {
                        "success": False,
                        "error": (
                            f"Organizer has a conflicting event "
                            f"({event['title']}) from {event['start_datetime']} to {event['end_datetime']}"
                        )
                    }

        # 4. Create unique event_id
        event_id = str(uuid.uuid4())
        while event_id in self.events:
            event_id = str(uuid.uuid4())

        event_info = {
            "event_id": event_id,
            "title": title,
            "description": description,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "location": location,
            "event_type": event_type,
            "organizer_id": organizer_id
        }
        self.events[event_id] = event_info
        # No participants added here; "Events must have at least one participant." checked elsewhere.

        return {
            "success": True,
            "message": "Event created successfully",
            "event_id": event_id
        }

    def add_participant_to_event(
        self,
        event_id: str,
        user_id: str,
        participation_status: str,
        is_external: bool,
        external_org_name: str
    ) -> dict:
        """
        Adds a user (internal or external) as a participant to an existing event.

        Args:
            event_id (str): ID of the event.
            user_id (str): ID of the participant (for external, may be synthetic/unique).
            participation_status (str): Participant's status in event ('invited', 'confirmed', 'declined').
            is_external (bool): Whether the participant is external to the organization.
            external_org_name (str): Name of the external organization (must be provided if is_external).

        Returns:
            dict:
                {"success": True, "message": "Participant added to event"}
                OR
                {"success": False, "error": <reason>}

        Constraints:
            - Event must exist.
            - For internal: user_id must exist in users.
            - participation_status must be 'invited', 'confirmed', or 'declined'
            - For external: external_org_name must be non-empty
            - A participant (by user_id) cannot be added to the same event more than once.
            - Events must have at least one participant after addition (always true for add).
        """
        valid_status = {"invited", "confirmed", "declined"}

        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        if not is_external and user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if participation_status not in valid_status:
            return {"success": False, "error": "Invalid participation status"}

        if is_external and not external_org_name:
            return {"success": False, "error": "External participants must have an organization name"}

        event_participants = self.participants.get(event_id, [])
        for p in event_participants:
            if p["user_id"] == user_id:
                return {"success": False, "error": "Participant already added to this event"}

        participant: ParticipantInfo = {
            "event_id": event_id,
            "user_id": user_id,
            "participation_status": participation_status,
            "is_external": is_external,
            "external_org_name": external_org_name if is_external else "",
        }
        event_participants.append(participant)
        self.participants[event_id] = event_participants

        return {"success": True, "message": "Participant added to event"}


    def create_event_with_participants(
        self,
        title: str,
        description: str,
        start_datetime: str,
        end_datetime: str,
        location: str,
        event_type: str,
        organizer_id: str,
        participants: list,
    ) -> dict:
        """
        Create an event and assign internal and/or external participants.
        Enforces:
          - Each event has at least one participant.
          - Internal participants cannot have time conflicts.
          - Organizer must exist.

        Args:
            title (str): Event title.
            description (str): Event description.
            start_datetime (str): Event start time (ISO format).
            end_datetime (str): Event end time (ISO format).
            location (str): Event location.
            event_type (str): Type of event.
            organizer_id (str): User ID of organizer (must be an internal user).
            participants (list): List of dict, each with keys:
                - For internal: {'user_id':..., 'participation_status':..., 'is_external': False}
                - For external: {'participation_status':..., 'is_external': True, 'external_org_name':...}

        Returns:
            dict: { "success": True, "message": ..., "event_id": ... }
                  or
                  { "success": False, "error": ... }
        """

        # Validate participants
        if not participants or len(participants) == 0:
            return { "success": False, "error": "At least one participant is required" }

        # Validate organizer
        if organizer_id not in self.users:
            return { "success": False, "error": "Organizer does not exist" }

        # Parse times
        try:
            new_start = self._parse_iso_datetime(start_datetime)
            new_end = self._parse_iso_datetime(end_datetime)
            if new_end <= new_start:
                return { "success": False, "error": "Event end time must be after start time" }
        except Exception:
            return { "success": False, "error": "Invalid time format" }

        # Validate and process participants, and check for conflicts for internals
        seen = set()  # Prevent duplicates
        participants_to_add = []
        for p in participants:
            is_external = p.get('is_external', False)
            if is_external:
                # Validate external
                org_name = p.get('external_org_name', "").strip()
                if not org_name:
                    return { "success": False, "error": "External participant missing organization name" }
                participation_status = p.get('participation_status', 'invited')
                key = ('external', org_name, participation_status)
                if key in seen:
                    continue
                seen.add(key)
                participant_info = {
                    "event_id": None, # to be filled after event creation
                    "user_id": "",    # not used for external
                    "participation_status": participation_status,
                    "is_external": True,
                    "external_org_name": org_name,
                }
                participants_to_add.append(participant_info)
            else:
                # Internal: must have valid user_id and no conflicts
                user_id = p.get('user_id')
                if not user_id or user_id not in self.users:
                    return { "success": False, "error": f"Invalid or missing internal user_id: {user_id}" }
                participation_status = p.get('participation_status', 'invited')
                key = ('internal', user_id, participation_status)
                if key in seen:
                    continue
                seen.add(key)
                if participation_status == "declined":
                    participant_info = {
                        "event_id": None,
                        "user_id": user_id,
                        "participation_status": participation_status,
                        "is_external": False,
                        "external_org_name": "",
                    }
                    participants_to_add.append(participant_info)
                    continue
                # Check time conflict for user
                for eid, event in self.events.items():
                    if self._user_has_active_involvement(eid, user_id):
                        # Fetch event times
                        ev_start = None
                        ev_end = None
                        try:
                            ev_start = self._parse_iso_datetime(event['start_datetime'])
                            ev_end = self._parse_iso_datetime(event['end_datetime'])
                        except Exception:
                            continue  # Ignore malformed
                        # Check overlap: [A,B) and [C,D) overlap iff A < D and C < B
                        if (new_start < ev_end) and (ev_start < new_end):
                            return { "success": False, "error": f"Time conflict for user_id {user_id} with event '{event['title']}'" }
                participant_info = {
                    "event_id": None,  # fill in after event creation
                    "user_id": user_id,
                    "participation_status": participation_status,
                    "is_external": False,
                    "external_org_name": "",
                }
                participants_to_add.append(participant_info)

        if len(participants_to_add) == 0:
            return { "success": False, "error": "No valid participants to add" }

        # Create event_id
        event_id = str(uuid.uuid4())
        event_info = {
            "event_id": event_id,
            "title": title,
            "description": description,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "location": location,
            "event_type": event_type,
            "organizer_id": organizer_id
        }
        self.events[event_id] = event_info

        # Add participants with correct event_id
        for p in participants_to_add:
            p["event_id"] = event_id
        self.participants[event_id] = participants_to_add

        return {
            "success": True,
            "message": f"Event '{title}' created with {len(participants_to_add)} participant(s)",
            "event_id": event_id
        }


    def update_event_time(
        self,
        event_id: str,
        new_start_datetime: Optional[str] = None,
        new_end_datetime: Optional[str] = None
    ) -> dict:
        """
        Change the start and/or end time of an existing event with conflict detection.

        Args:
            event_id (str): The unique ID of the event to change.
            new_start_datetime (str, optional): New start time as ISO format string.
            new_end_datetime (str, optional): New end time as ISO format string.

        Returns:
            dict: {
                "success": True,
                "message": "Event time updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - No two active internal participants for the event can overlap in time.
            - Event must already exist.
            - At least one new time must be provided and valid.
            - new_end > new_start
        """
        # 1. Check event exists
        if event_id not in self.events:
            return {"success": False, "error": "Event not found."}

        event = self.events[event_id]
        start_time = event["start_datetime"]
        end_time = event["end_datetime"]

        # 2. Compose and validate new times
        proposed_start = new_start_datetime if new_start_datetime else start_time
        proposed_end = new_end_datetime if new_end_datetime else end_time

        try:
            dt_start = self._parse_iso_datetime(proposed_start)
            dt_end = self._parse_iso_datetime(proposed_end)
        except Exception:
            return {"success": False, "error": "Invalid datetime format; must be ISO 8601 string."}

        if dt_end <= dt_start:
            return {"success": False, "error": "End datetime must be after start datetime."}

        # 3. Get the internal participants whose schedules must stay conflict-free.
        # Organizer ownership alone does not imply attendance in this environment.
        event_participants = self.participants.get(event_id, [])
        participant_user_ids = []
        for participant in event_participants:
            if participant.get("is_external", False) is True:
                continue
            if participant.get("participation_status") == "declined":
                continue
            user_id = participant["user_id"]
            if user_id not in participant_user_ids:
                participant_user_ids.append(user_id)

        # 4. For each participant, get their other events and check for time conflicts
        for user_id in participant_user_ids:
            for other_event_id, other_event in self.events.items():
                if other_event_id == event_id:
                    continue
                if not self._user_has_active_involvement(other_event_id, user_id):
                    continue
                # Compare time windows
                o_start = other_event["start_datetime"]
                o_end = other_event["end_datetime"]
                try:
                    o_dt_start = self._parse_iso_datetime(o_start)
                    o_dt_end = self._parse_iso_datetime(o_end)
                except Exception:
                    continue # corrupt event, skip

                # If (proposed_start < o_end) and (proposed_end > o_start): overlap
                if dt_start < o_dt_end and dt_end > o_dt_start:
                    user_name = self.users[user_id]["name"] if user_id in self.users else user_id
                    return {
                        "success": False,
                        "error": f"Time conflict for user: {user_name} with event {other_event_id}."
                    }

        # 5. Passed all checks, update event
        self.events[event_id]["start_datetime"] = proposed_start
        self.events[event_id]["end_datetime"] = proposed_end

        return {"success": True, "message": "Event time updated successfully."}

    def update_participation_status(self, event_id: str, user_id: str, new_status: str) -> dict:
        """
        Change a participant’s status (invited/confirmed/declined) for a particular event.

        Args:
            event_id (str): ID of the event the participant is part of.
            user_id (str): ID of the user (participant).
            new_status (str): New status to set ("invited", "confirmed", or "declined").

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "Participation status updated"
                }
                On failure:
                {
                    "success": False,
                    "error": str (reason for failure)
                }

        Constraints:
            - event_id and user_id combination must exist in participants.
            - new_status must be one of "invited", "confirmed", "declined".
        """
        valid_statuses = {"invited", "confirmed", "declined"}

        if new_status not in valid_statuses:
            return {"success": False, "error": "Invalid participation status"}

        if event_id not in self.participants:
            return {"success": False, "error": "Event or participant not found"}

        found = False
        for p in self.participants[event_id]:
            if p["user_id"] == user_id:
                p["participation_status"] = new_status
                found = True
                break

        if not found:
            return {"success": False, "error": "Participant not found for this event"}

        return {"success": True, "message": "Participation status updated"}

    def cancel_event(self, event_id: str) -> dict:
        """
        Remove (cancel) a scheduled event from the system.

        Args:
            event_id (str): The unique identifier for the event to be canceled.

        Returns:
            dict: {
                "success": True,
                "message": "Event cancelled successfully."
            }
            or
            {
                "success": False,
                "error": "Event does not exist."
            }

        Constraints:
            - If the event exists, it and all its participant links are deleted.
            - If the event does not exist, returns an error and does nothing.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }

        # Remove the event itself
        del self.events[event_id]

        # Remove all associated participants (if present)
        if event_id in self.participants:
            del self.participants[event_id]

        return { "success": True, "message": "Event cancelled successfully." }

    def remove_participant_from_event(self, event_id: str, user_id: str) -> dict:
        """
        Remove a user from a particular event’s participant list.

        Args:
            event_id (str): The ID of the event.
            user_id (str): The ID of the user to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Participant removed from event"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The event must exist.
            - The user must currently be a participant of the event.
            - The event must still have at least one participant after removal.
        """
        # Check event existence
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        # Check participant list for event
        if event_id not in self.participants:
            return { "success": False, "error": "No participants found for event" }

        # Find the participant entry (by user_id)
        participants_list = self.participants[event_id]
        idx_to_remove = None
        for idx, participant in enumerate(participants_list):
            if participant["user_id"] == user_id:
                idx_to_remove = idx
                break

        if idx_to_remove is None:
            return { "success": False, "error": "User is not a participant in the event" }

        if len(participants_list) <= 1:
            return { "success": False, "error": "Cannot remove participant: event must have at least one participant" }

        # Remove the participant
        del participants_list[idx_to_remove]
        self.participants[event_id] = participants_list

        return { "success": True, "message": "Participant removed from event" }

    def update_event_details(self, event_id: str, updates: dict) -> dict:
        """
        Modify event properties (title, description, location, event_type, organizer_id) for a specified event,
        without allowing changes to start_datetime or end_datetime.

        Args:
            event_id (str): The ID of the event to update.
            updates (dict): Dictionary of event attributes to update. 
                            Allowed fields: title, description, location, event_type, organizer_id.

        Returns:
            dict: {
                "success": True,
                "message": "Event details updated successfully."
            }
            or
            {
                "success": False,
                "error": "An error message describing the failure."
            }

        Constraints:
            - The event with event_id must exist.
            - Must NOT allow updating start_datetime or end_datetime.
            - Only allowed fields may be updated.
        """
        # Check if event exists
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }

        forbidden = {"start_datetime", "end_datetime"}
        allowed_fields = {"title", "description", "location", "event_type", "organizer_id"}
        # Check for forbidden fields
        for key in updates:
            if key in forbidden:
                return { "success": False, "error": f"Updating '{key}' is not allowed through this operation." }
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' cannot be updated." }

        # Do not update if nothing is provided
        if not updates:
            return { "success": False, "error": "No updatable event details provided." }

        # Perform the updates
        for key, value in updates.items():
            self.events[event_id][key] = value

        return { "success": True, "message": "Event details updated successfully." }

    def add_external_participant(
        self,
        event_id: str,
        external_participant_name: str,
        external_org_name: str,
        participation_status: str = "invited"
    ) -> dict:
        """
        Add a new external participant (with organization info) to an event for notifications and tracking.

        Args:
            event_id (str): The event to which the participant is to be added.
            external_participant_name (str): The name of the external participant.
            external_org_name (str): The organization name of the external participant.
            participation_status (str, optional): invited/confirmed/declined (default: invited).

        Returns:
            dict: {
                "success": True,
                "message": "External participant added to event."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Event must exist.
            - No duplicate external participant (same name and org) per event.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist."}

        participants = self.participants.get(event_id, [])
        # Check for duplicate by name+org where is_external is True
        for p in participants:
            if (
                p["is_external"] is True and
                p["user_id"] == external_participant_name and
                p["external_org_name"] == external_org_name
            ):
                return {
                    "success": False,
                    "error": "External participant with the same name and organization already added."
                }
    
        # Add the external participant
        new_participant: ParticipantInfo = {
            "event_id": event_id,
            "user_id": external_participant_name,  # user_id used for display/name purposes for externals
            "participation_status": participation_status,
            "is_external": True,
            "external_org_name": external_org_name
        }
        participants.append(new_participant)
        self.participants[event_id] = participants

        return {"success": True, "message": "External participant added to event."}

    def bulk_create_events(self, events_to_create: list) -> dict:
        """
        Create multiple events at once.

        Args:
            events_to_create (list): A list of dicts with each containing:
                - 'event_info': EventInfo or dict with event fields
                - 'participants': list of ParticipantInfo or dicts (must have at least one per event)

        Returns:
            dict: 
                On success (all events):
                    {
                        "success": True,
                        "message": "<N> events created successfully",
                        "event_ids": [event_id, ...]
                    }
                On partial/all failure:
                    {
                        "success": False,
                        "error": "Reason for failure",  # For granular errors, includes per-event messages
                        "results": [
                            { "event_id": ..., "success": True/False, "error": ...},
                            ...
                        ]
                    }

        Constraints:
            - No participant can be scheduled for overlapping events.
            - Events must have at least one participant.
        """

        def overlaps(start1, end1, start2, end2):
            # Both are ISO strings
            s1 = self._parse_iso_datetime(start1)
            e1 = self._parse_iso_datetime(end1)
            s2 = self._parse_iso_datetime(start2)
            e2 = self._parse_iso_datetime(end2)
            return s1 < e2 and s2 < e1

        results = []
        created_event_ids = []
        # To avoid race conditions within this batch, we track local changes before committing to self
        temp_events = copy.deepcopy(self.events)
        temp_participants = copy.deepcopy(self.participants)
        for evt in events_to_create:
            event_info = evt.get("event_info")
            participants = evt.get("participants", [])
            eid = event_info.get("event_id") if event_info else None

            # Basic checks
            if not event_info or not eid:
                results.append({"event_id": eid, "success": False, "error": "Missing event_info or event_id"})
                continue
            if eid in temp_events:
                results.append({"event_id": eid, "success": False, "error": "Event ID already exists"})
                continue
            if not participants or len(participants) == 0:
                results.append({"event_id": eid, "success": False, "error": "No participants provided"})
                continue

            # Check for conflicts per participant
            conflict = False
            p_user_ids = [p["user_id"] for p in participants if not p.get("is_external", False)]
            # For each participant (user), get all future/active events they're in and check overlap
            for uid in p_user_ids:
                # Find all events for this participant so far (existing + batch additions)
                their_events = []
                # Existing
                for peid, plist in temp_participants.items():
                    if temp_events.get(peid, {}).get("organizer_id") == uid:
                        their_events.append(temp_events.get(peid))
                        continue
                    if any(
                        pinfo.get("is_external", False) is False
                        and pinfo["user_id"] == uid
                        and pinfo.get("participation_status") != "declined"
                        for pinfo in plist
                    ):
                        their_events.append(temp_events.get(peid))
                # Batch to be added from current batch
                # (Avoid double counting; peid==eid means the current event)
                # Now check for overlap:
                for other_evt in their_events:
                    if other_evt is None: continue
                    if overlaps(event_info["start_datetime"], event_info["end_datetime"],
                                other_evt["start_datetime"], other_evt["end_datetime"]):
                        results.append({"event_id": eid, "success": False,
                            "error": f"Scheduling conflict for user {uid} with event {other_evt['event_id']}"})
                        conflict = True
                        break
                if conflict:
                    break
            if conflict:
                continue

            # (Optional: check working hours here if defined...)

            # Everything is good: add to local temp store
            temp_events[eid] = event_info
            temp_participants[eid] = participants
            results.append({"event_id": eid, "success": True})
            created_event_ids.append(eid)

        # Commit successful events to self
        for r in results:
            if r["success"]:
                eid = r["event_id"]
                self.events[eid] = temp_events[eid]
                self.participants[eid] = temp_participants[eid]
        all_success = all(r["success"] for r in results)
        if all_success:
            return {
                "success": True,
                "message": f"{len(created_event_ids)} events created successfully",
                "event_ids": created_event_ids
            }
        else:
            return {
                "success": False,
                "error": "One or more events could not be created. See details.",
                "results": results
            }


class CorporateCalendarSchedulingSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_users(self, **kwargs):
        return self._call_inner_tool('list_users', kwargs)

    def get_events_for_user(self, **kwargs):
        return self._call_inner_tool('get_events_for_user', kwargs)

    def get_events_in_time_range_for_user(self, **kwargs):
        return self._call_inner_tool('get_events_in_time_range_for_user', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def get_event_participants(self, **kwargs):
        return self._call_inner_tool('get_event_participants', kwargs)

    def detect_conflicts_for_user(self, **kwargs):
        return self._call_inner_tool('detect_conflicts_for_user', kwargs)

    def get_external_participants_for_event(self, **kwargs):
        return self._call_inner_tool('get_external_participants_for_event', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def add_participant_to_event(self, **kwargs):
        return self._call_inner_tool('add_participant_to_event', kwargs)

    def create_event_with_participants(self, **kwargs):
        return self._call_inner_tool('create_event_with_participants', kwargs)

    def update_event_time(self, **kwargs):
        return self._call_inner_tool('update_event_time', kwargs)

    def update_participation_status(self, **kwargs):
        return self._call_inner_tool('update_participation_status', kwargs)

    def cancel_event(self, **kwargs):
        return self._call_inner_tool('cancel_event', kwargs)

    def remove_participant_from_event(self, **kwargs):
        return self._call_inner_tool('remove_participant_from_event', kwargs)

    def update_event_details(self, **kwargs):
        return self._call_inner_tool('update_event_details', kwargs)

    def add_external_participant(self, **kwargs):
        return self._call_inner_tool('add_external_participant', kwargs)

    def bulk_create_events(self, **kwargs):
        return self._call_inner_tool('bulk_create_events', kwargs)
