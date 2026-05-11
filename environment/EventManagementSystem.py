# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import List, Dict, Any
from datetime import datetime



# Represents participant information
class ParticipantInfo(TypedDict):
    participant_id: str
    name: str
    contact_info: str
    role: str

# Represents location information
class LocationInfo(TypedDict):
    location_id: str
    name: str
    address: str
    capacity: int

# Represents event information
class EventInfo(TypedDict):
    event_id: str
    name: str
    date: str  # should be validated as a proper date string
    category: str
    description: str
    location_id: str
    participant_ids: List[str]  # multiple participants

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for event management.
        """

        # Events: {event_id: EventInfo}
        # Maps event_id to its logistics and descriptive attributes.
        self.events: Dict[str, EventInfo] = {}

        # Participants: {participant_id: ParticipantInfo}
        # Maps participant_id to details about event participants.
        self.participants: Dict[str, ParticipantInfo] = {}

        # Locations: {location_id: LocationInfo}
        # Maps location_id to venue/space details.
        self.locations: Dict[str, LocationInfo] = {}

        # -- Constraints --
        # - Each event must have a unique event_id.
        # - Event dates must be valid calendar dates.
        # - An event category must be from a controlled list (e.g., performance art, conference, meeting, etc.).
        # - Event participants and locations referenced must exist.
        # - Locations cannot have conflicting events at overlapping times.
        self._default_event_categories: List[str] = [
            "performance art",
            "conference",
            "meeting",
            "workshop",
            "seminar",
            "webinar",
            "exhibition",
            "community activity",
        ]

    def _parse_controlled_categories(self, raw: Any) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, (list, tuple, set)):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                return []
            parsed = None
            if text.startswith("[") or text.startswith("(") or text.startswith("{"):
                try:
                    parsed = ast.literal_eval(text)
                except Exception:
                    parsed = None
            if isinstance(parsed, (list, tuple, set)):
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [part.strip() for part in text.split(",") if part.strip()]
        return []

    def _get_effective_event_categories(self) -> List[str]:
        raw_state = None
        if hasattr(self, "_get_event_categories_state"):
            raw_state = self._get_event_categories_state
        elif hasattr(self, "event_categories"):
            raw_state = self.event_categories

        categories = self._parse_controlled_categories(raw_state) or list(self._default_event_categories)
        for event in self.events.values():
            category = str(event.get("category", "")).strip()
            if category:
                categories.append(category)

        deduped: List[str] = []
        seen = set()
        for category in categories:
            if category not in seen:
                deduped.append(category)
                seen.add(category)
        return deduped

    @staticmethod
    def _validate_time_string(ts: str) -> bool:
        if len(ts) != 5 or ts[2] != ":":
            return False
        try:
            hour, minute = int(ts[:2]), int(ts[3:])
            return 0 <= hour < 24 and 0 <= minute < 60
        except Exception:
            return False

    @staticmethod
    def _normalize_time_window(start_time: str = None, end_time: str = None):
        if start_time is None and end_time is None:
            return True, None, None, None
        if start_time is None or end_time is None:
            return False, None, None, "Both start_time and end_time must be provided together"
        if not (_GeneratedEnvImpl._validate_time_string(start_time) and _GeneratedEnvImpl._validate_time_string(end_time)):
            return False, None, None, "Invalid start_time or end_time format (expected HH:MM)"
        if start_time >= end_time:
            return False, None, None, "start_time must be before end_time"
        return True, start_time, end_time, None

    @staticmethod
    def _times_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
        return (start_a < end_b) and (start_b < end_a)

    def _find_location_conflict(
        self,
        location_id: str,
        date: str,
        start_time: str = None,
        end_time: str = None,
        exclude_event_id: str = None,
    ):
        for event in self.events.values():
            if exclude_event_id is not None and event.get("event_id") == exclude_event_id:
                continue
            if event["location_id"] != location_id or event["date"] != date:
                continue

            existing_start = event.get("start_time")
            existing_end = event.get("end_time")
            if start_time is None or end_time is None:
                return event
            if existing_start is None or existing_end is None:
                return event
            if not (self._validate_time_string(existing_start) and self._validate_time_string(existing_end)):
                return event
            if self._times_overlap(start_time, end_time, existing_start, existing_end):
                return event
        return None

    def list_events(self) -> dict:
        """
        Retrieve the full list of events in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],  # List of all event records (can be empty).
            }
        """
        return {
            "success": True,
            "data": list(self.events.values())
        }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the details of a specific event by its event_id.

        Args:
            event_id (str): The unique identifier of the event to look up.

        Returns:
            dict:
                - On success: {"success": True, "data": EventInfo}
                - On failure: {"success": False, "error": "Event not found"}

        Constraints:
            - Returns error if event_id is not found.
        """
        event = self.events.get(event_id)
        if event is None:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def find_events_by_date(self, date: str) -> dict:
        """
        Retrieve all events scheduled for a specific date.

        Args:
            date (str): The date string to search for (should match EventInfo['date'] format).

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # List of event info dictionaries for events on that date
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The date string must be non-empty.
            - Returns empty list if no events found for that date.
        """
        if not date or not isinstance(date, str):
            return { "success": False, "error": "Date must be a non-empty string" }

        result = [event for event in self.events.values() if event["date"] == date]

        return { "success": True, "data": result }

    def find_events_by_category(self, category: str) -> dict:
        """
        Retrieve all events of a specific category.

        Args:
            category (str): The category to search for.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[EventInfo]  # All events matching the given category
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., invalid category)
                }

        Constraints:
            - Category must be from the controlled list: performance art, conference, meeting, workshop, seminar, etc.
        """
        controlled_categories = {"performance art", "conference", "meeting", "workshop", "seminar"}
        if category not in controlled_categories:
            return {"success": False, "error": "Invalid category. Must be one of: " + ", ".join(sorted(controlled_categories))}

        result = [
            event_info for event_info in self.events.values()
            if event_info.get("category") == category
        ]
        return {"success": True, "data": result}

    def find_events_by_date_and_category(self, date: str, category: str) -> dict:
        """
        Retrieve all events that match both the given date and the given category.
    
        Args:
            date (str): The event date to match (should be in the format used by EventInfo['date']).
            category (str): The event category to match.
    
        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],  # List of events matching both date and category. Empty if none found.
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Returned events must have their 'date' and 'category' fields matching the parameters.
            - If a controlled category list exists (e.g., self.get_event_categories), only allow categories from that list.
        """
        # Optional: verify if categories are validated by a controlled list
        if hasattr(self, "get_event_categories"):
            valid_resp = self.get_event_categories()
            if valid_resp["success"]:
                valid_categories = valid_resp["data"]
                if category not in valid_categories:
                    return {"success": False, "error": f"Category '{category}' is not valid."}

        results = [
            event for event in self.events.values()
            if event["date"] == date and event["category"] == category
        ]
        return {"success": True, "data": results}

    def get_events_at_location_on_date(self, location_id: str, date: str) -> dict:
        """
        Retrieve all events scheduled at the given location on the specified date.

        Args:
            location_id (str): The ID of the location to check.
            date (str): The date to check (as a string formatted as in stored events).

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # List may be empty if no events found
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. location does not exist
            }

        Constraints:
            - location_id must exist in the system.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }

        matching_events = [
            event for event in self.events.values()
            if event["location_id"] == location_id and event["date"] == date
        ]

        return { "success": True, "data": matching_events }

    def list_participants(self) -> dict:
        """
        Retrieve the list of all participants in the event management system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo]  # List of all participant info dictionaries. May be empty if no participants.
            }
        """
        participants_list = list(self.participants.values())
        return { "success": True, "data": participants_list }

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Fetch the information of a participant by participant_id.

        Args:
            participant_id (str): The unique identifier of the participant.

        Returns:
            dict: {
                "success": True,
                "data": ParticipantInfo  # Matching participant's info
            }
            or
            {
                "success": False,
                "error": str  # If the participant is not found
            }
        Constraints:
            - participant_id must exist in the participants mapping.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": "Participant not found"}

        return {"success": True, "data": self.participants[participant_id]}

    def list_locations(self) -> dict:
        """
        Retrieve all locations available in the system.
    
        Args:
            None

        Returns:
            dict: {
                'success': True,
                'data': List[LocationInfo]  # List of all locations (may be empty)
            }
    
        Constraints:
            - No input parameters or validation required.
            - Listing is always permissible; empty list is a valid result.
        """
        locations_list = list(self.locations.values())
        return {
            "success": True,
            "data": locations_list
        }

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Fetch details of a location by location_id.

        Args:
            location_id (str): Unique identifier for the location.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": LocationInfo  # Location's details
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Location not found"
                    }
        """
        location = self.locations.get(location_id)
        if location is None:
            return { "success": False, "error": "Location not found" }
    
        return { "success": True, "data": location }

    def get_participants_for_event(self, event_id: str) -> dict:
        """
        List all participants involved in a specific event.

        Args:
            event_id (str): Unique identifier for the event.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ParticipantInfo]  # List of participant details
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if event not found
                }

        Constraints:
          - The specified event_id must exist in the system.
          - All participant IDs referenced by the event should also exist.
          - If one or more participant_ids in the event do not exist in self.participants, they are ignored.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event not found" }

        event_info = self.events[event_id]
        participant_ids = event_info.get("participant_ids", [])

        participant_list = [
            self.participants[pid]
            for pid in participant_ids
            if pid in self.participants
        ]

        return { "success": True, "data": participant_list }

    def get_events_for_participant(self, participant_id: str) -> dict:
        """
        List all events a participant is involved in.

        Args:
            participant_id (str): The unique ID of the participant.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # Events where the participant appears (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # "Participant does not exist"
            }

        Constraints:
            - The participant_id must exist in the system.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": "Participant does not exist"}

        events = [
            event for event in self.events.values()
            if participant_id in event.get("participant_ids", [])
        ]
        return {"success": True, "data": events}

    def check_location_availability(self, location_id: str, date: str, start_time: str, end_time: str) -> dict:
        """
        Check if a location is available (no conflicting events) for a specified date and time slot.

        Args:
            location_id (str): ID of the location to check.
            date (str): Target date in "YYYY-MM-DD" format.
            start_time (str): Start of time slot in "HH:MM" 24-hour format.
            end_time (str): End of time slot in "HH:MM" 24-hour format.

        Returns:
            dict: {
                "success": True,
                "available": bool,  # True if available, False if not
                "conflicts": List[EventInfo]  # List of conflicting events (if any)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Location must exist.
            - Returns True if no overlapping events at the time/date, else False.
            - Expects EventInfo to have start_time/end_time (if missing, cannot fully perform).
        """
        # Check if location exists
        if location_id not in self.locations:
            return {"success": False, "error": "Location does not exist"}

        ok, normalized_start, normalized_end, error = self._normalize_time_window(start_time, end_time)
        if not ok:
            return {"success": False, "error": error}

        # Find events at the location and date
        conflicts = []
        for ev in self.events.values():
            if ev["location_id"] == location_id and ev["date"] == date:
                ev_start = ev.get("start_time")
                ev_end = ev.get("end_time")
                if ev_start is None or ev_end is None:
                    conflicts.append(ev)
                    continue
                if not (self._validate_time_string(ev_start) and self._validate_time_string(ev_end)):
                    conflicts.append(ev)
                    continue
                if self._times_overlap(normalized_start, normalized_end, ev_start, ev_end):
                    conflicts.append(ev)

        if conflicts:
            return {"success": True, "available": False, "conflicts": conflicts}
        else:
            return {"success": True, "available": True, "conflicts": []}

    def get_event_categories(self) -> dict:
        """
        Retrieve the list of valid/controlled event categories.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of allowed category names (may be empty but should reflect current system state)
            }

        Constraints:
            - Returned list should match the controlled event categories enforced in the system.
        """
        return {"success": True, "data": self._get_effective_event_categories()}


    def add_event(
        self,
        event_id: str,
        name: str,
        date: str,
        category: str,
        description: str,
        location_id: str,
        participant_ids: List[str],
        start_time: str = None,
        end_time: str = None
    ) -> dict:
        """
        Create a new event with the specified details, enforcing all event constraints.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Name/title of the event.
            date (str): Event date (should be valid calendar date, e.g., YYYY-MM-DD).
            category (str): Event category (must be in allowed categories).
            description (str): Description of the event.
            location_id (str): ID of the location/venue for the event.
            participant_ids (List[str]): List of participant IDs involved in the event.

        Returns:
            dict: On success,
                { "success": True, "message": "Event <event_id> added successfully" }
                  On failure, 
                { "success": False, "error": "Reason for failure" }

        Constraints:
            - event_id must be unique.
            - date must be a valid date string.
            - category must be in the controlled list of event categories.
            - participant_ids and location_id must reference existing participants/locations.
            - Locations may not have conflicting (overlapping date) events.
        """
        # Check unique event_id
        if event_id in self.events:
            return {"success": False, "error": "event_id already exists"}

        # Validate date
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "error": "Invalid date format, expected YYYY-MM-DD"}

        # Validate category
        allowed_categories_res = self.get_event_categories() if hasattr(self, 'get_event_categories') else {"success": True, "data": []}
        allowed_categories = allowed_categories_res.get("data", []) if allowed_categories_res.get("success") else []
        if category not in allowed_categories:
            return {"success": False, "error": f"Category '{category}' is not allowed"}

        ok, normalized_start, normalized_end, error = self._normalize_time_window(start_time, end_time)
        if not ok:
            return {"success": False, "error": error}

        # Check location exists
        if location_id not in self.locations:
            return {"success": False, "error": f"location_id '{location_id}' does not exist"}

        # Check all participants exist
        for pid in participant_ids:
            if pid not in self.participants:
                return {"success": False, "error": f"participant_id '{pid}' does not exist"}

        conflict = self._find_location_conflict(location_id, date, normalized_start, normalized_end)
        if conflict is not None:
            return {"success": False, "error": f"Location '{location_id}' is already booked for date '{date}'"}

        # All checks passed, add event
        event_info = {
            "event_id": event_id,
            "name": name,
            "date": date,
            "category": category,
            "description": description,
            "location_id": location_id,
            "participant_ids": participant_ids
        }
        if normalized_start is not None and normalized_end is not None:
            event_info["start_time"] = normalized_start
            event_info["end_time"] = normalized_end
        self.events[event_id] = event_info

        return {"success": True, "message": f"Event '{event_id}' added successfully"}

    def update_event(
        self,
        event_id: str,
        name: str = None,
        date: str = None,
        category: str = None,
        description: str = None,
        location_id: str = None,
        participant_ids: list = None,
        start_time: str = None,
        end_time: str = None
    ) -> dict:
        """
        Update attributes of an existing event, with constraint validation.
    
        Args:
            event_id (str): The ID of the event to be updated.
            name (str, optional): New name for the event.
            date (str, optional): New date for the event (must be valid date string: YYYY-MM-DD).
            category (str, optional): New event category (must be valid from controlled list).
            description (str, optional): New description for the event.
            location_id (str, optional): New location ID (must exist).
            participant_ids (List[str], optional): New list of participant IDs (all must exist).
        
        Returns:
            dict: On success: {"success": True, "message": "Event updated successfully" }
                  On failure: {"success": False, "error": <reason> }
        Constraints:
            - Event with event_id must exist.
            - New date must be valid calendar date.
            - New category must be in controlled categories.
            - New location_id must exist and have no conflicting event at this date.
            - All participant_ids must exist.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event not found" }
        event = self.events[event_id]

        # Validate date
        if date is not None:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return { "success": False, "error": "Invalid date format (expected YYYY-MM-DD)" }

        # Validate category
        if category is not None:
            allowed_categories_res = self.get_event_categories() if hasattr(self, 'get_event_categories') else {"success": True, "data": []}
            allowed_categories = allowed_categories_res.get("data", []) if allowed_categories_res.get("success") else []
            if category not in allowed_categories:
                return { "success": False, "error": f"Invalid category. Allowed: {sorted(allowed_categories)}" }

        # Validate new location
        new_location_id = location_id if location_id is not None else event["location_id"]
        if new_location_id not in self.locations:
            return { "success": False, "error": "Specified location does not exist" }

        # Validate participant ids
        if participant_ids is not None:
            not_found = [pid for pid in participant_ids if pid not in self.participants]
            if not_found:
                return { "success": False, "error": f"Participant(s) not found: {not_found}" }

        ok, normalized_start, normalized_end, error = self._normalize_time_window(start_time, end_time)
        if not ok:
            return {"success": False, "error": error}

        # Date for checking overlap
        new_date = date if date is not None else event["date"]
        new_start = normalized_start if normalized_start is not None else event.get("start_time")
        new_end = normalized_end if normalized_end is not None else event.get("end_time")

        # Location conflict check
        conflict = self._find_location_conflict(
            new_location_id,
            new_date,
            new_start,
            new_end,
            exclude_event_id=event_id,
        )
        if conflict is not None:
            return {
                "success": False,
                "error": f"Location conflict: event '{conflict['name']}' already scheduled at this location on {new_date}"
            }

        # All checks passed; apply updates
        if name is not None:
            event["name"] = name
        if date is not None:
            event["date"] = date
        if category is not None:
            event["category"] = category
        if description is not None:
            event["description"] = description
        if location_id is not None:
            event["location_id"] = location_id
        if participant_ids is not None:
            event["participant_ids"] = participant_ids
        if normalized_start is not None and normalized_end is not None:
            event["start_time"] = normalized_start
            event["end_time"] = normalized_end

        self.events[event_id] = event
        return { "success": True, "message": "Event updated successfully" }

    def remove_event(self, event_id: str) -> dict:
        """
        Delete an event from the system.

        Args:
            event_id (str): Unique identifier of the event to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "Event <event_id> removed successfully." }
                On failure: { "success": False, "error": "Event not found." }

        Constraints:
            - The event_id must refer to an existing event.
            - No effect if the event does not exist.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event not found." }

        del self.events[event_id]
        return { "success": True, "message": f"Event {event_id} removed successfully." }

    def add_participant(
        self,
        participant_id: str,
        name: str,
        contact_info: str,
        role: str
    ) -> dict:
        """
        Adds a new participant to the event management system.
    
        Args:
            participant_id (str): Unique ID for the participant.
            name (str): Name of the participant.
            contact_info (str): Contact information for the participant.
            role (str): Role of the participant in events.
        
        Returns:
            dict: {
                "success": True,
                "message": "Participant added successfully."
            }
            OR
            {
                "success": False,
                "error": "Participant ID already exists."
            }
    
        Constraints:
            - participant_id must be unique in the system.
        """
        if participant_id in self.participants:
            return {
                "success": False,
                "error": "Participant ID already exists."
            }

        participant: ParticipantInfo = {
            "participant_id": participant_id,
            "name": name,
            "contact_info": contact_info,
            "role": role
        }
        self.participants[participant_id] = participant
        return {
            "success": True,
            "message": "Participant added successfully."
        }

    def update_participant(
        self, 
        participant_id: str, 
        name: str = None, 
        contact_info: str = None, 
        role: str = None
    ) -> dict:
        """
        Modify details of an existing participant.

        Args:
            participant_id (str): The ID of the participant to update.
            name (str, optional): New name for the participant (if any).
            contact_info (str, optional): New contact information (if any).
            role (str, optional): New role assignment (if any).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Participant updated successfully" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - participant_id must exist in the system.
            - At least one of the fields (name, contact_info, role) must be provided.
            - Only provided fields are updated.

        """
        # Check participant exists
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant does not exist." }
    
        # Check any updatable field is provided
        if all(x is None for x in [name, contact_info, role]):
            return { "success": False, "error": "No update fields provided." }

        # Update fields
        if name is not None:
            self.participants[participant_id]["name"] = name
        if contact_info is not None:
            self.participants[participant_id]["contact_info"] = contact_info
        if role is not None:
            self.participants[participant_id]["role"] = role

        return { "success": True, "message": "Participant updated successfully" }

    def remove_participant(self, participant_id: str) -> dict:
        """
        Remove a participant from the system and from any events to which they are assigned.

        Args:
            participant_id (str): The ID of the participant to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Participant '<id>' removed and unassigned from events."
            }
            or
            {
                "success": False,
                "error": "<reason participant could not be removed>"
            }

        Constraints:
            - Only removes existing participants.
            - Participant is also removed from all events where referenced.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": f"Participant '{participant_id}' does not exist."}

        # Remove from all events' participant lists
        for event in self.events.values():
            if participant_id in event["participant_ids"]:
                event["participant_ids"].remove(participant_id)

        del self.participants[participant_id]

        return {
            "success": True,
            "message": f"Participant '{participant_id}' removed and unassigned from events."
        }

    def add_location(self, location_id: str, name: str, address: str, capacity: int) -> dict:
        """
        Add a new location/venue.

        Args:
            location_id (str): Unique identifier for the new location.
            name (str): Name of the location/venue.
            address (str): Address for the location.
            capacity (int): Maximum number of people (must be positive integer).

        Returns:
            dict: {
                "success": True,
                "message": "Location added successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - location_id must be unique.
            - capacity must be a positive integer.
            - name and address must not be empty.
        """
        # Validate uniqueness
        if location_id in self.locations:
            return {"success": False, "error": "Location ID already exists."}

        # Validate fields
        if not (isinstance(name, str) and name.strip()):
            return {"success": False, "error": "Name must be a non-empty string."}
        if not (isinstance(address, str) and address.strip()):
            return {"success": False, "error": "Address must be a non-empty string."}
        if not (isinstance(capacity, int) and capacity > 0):
            return {"success": False, "error": "Capacity must be a positive integer."}

        # Create and add location
        location_info = {
            "location_id": location_id,
            "name": name,
            "address": address,
            "capacity": capacity
        }
        self.locations[location_id] = location_info

        return {"success": True, "message": "Location added successfully."}

    def update_location(
        self,
        location_id: str,
        name: str = None,
        address: str = None,
        capacity: int = None
    ) -> dict:
        """
        Edit details of an existing location.

        Args:
            location_id (str): The location to update (must exist).
            name (str, optional): New name for the location.
            address (str, optional): New address for the location.
            capacity (int, optional): New capacity (must be positive integer, if provided).

        Returns:
            dict: 
              - On success: { "success": True, "message": "Location updated successfully." }
              - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Location must exist.
            - Only the specified fields will be updated.
            - Capacity, if provided, must be a positive integer.
        """
        loc = self.locations.get(location_id)
        if loc is None:
            return { "success": False, "error": "Location does not exist." }
    
        fields_updated = False
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return { "success": False, "error": "Invalid name value." }
            loc["name"] = name.strip()
            fields_updated = True

        if address is not None:
            if not isinstance(address, str) or not address.strip():
                return { "success": False, "error": "Invalid address value." }
            loc["address"] = address.strip()
            fields_updated = True

        if capacity is not None:
            if not isinstance(capacity, int) or capacity <= 0:
                return { "success": False, "error": "Capacity must be a positive integer." }
            loc["capacity"] = capacity
            fields_updated = True

        if not fields_updated:
            return { "success": False, "error": "No valid fields to update provided." }

        # Store back (not strictly needed for dict reference, but for clarity)
        self.locations[location_id] = loc
        return { "success": True, "message": "Location updated successfully." }

    def remove_location(self, location_id: str) -> dict:
        """
        Remove a location/venue from the system.
    
        Args:
            location_id (str): The ID of the location to remove.
    
        Returns:
            dict:
                - success: True if the location was removed, with a success message.
                - success: False and an error message if:
                    - The location does not exist.
                    - The location is still referenced by one or more events.

        Constraints:
            - Cannot remove a location if it is referenced by any event.
            - The location must exist.
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location does not exist."}

        # Check if any event references this location
        for event in self.events.values():
            if event.get("location_id") == location_id:
                return {
                    "success": False,
                    "error": "Location is still referenced by one or more events."
                }

        # Safe to remove
        del self.locations[location_id]
        return {
            "success": True,
            "message": f"Location {location_id} removed successfully."
        }

    def assign_participant_to_event(self, event_id: str, participant_id: str) -> dict:
        """
        Add an existing participant to an event’s participant list.

        Args:
            event_id (str): ID of the event.
            participant_id (str): ID of the participant to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Participant <id> assigned to event <id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - Event must exist.
            - Participant must exist.
            - Participant must not already be assigned to the event.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        if participant_id not in self.participants:
            return { "success": False, "error": "Participant does not exist" }

        event = self.events[event_id]
        if participant_id in event["participant_ids"]:
            return { "success": False, "error": "Participant is already assigned to this event" }

        event["participant_ids"].append(participant_id)
        return { "success": True, "message": f"Participant {participant_id} assigned to event {event_id}." }

    def remove_participant_from_event(self, event_id: str, participant_id: str) -> dict:
        """
        Remove a participant from an event’s participant list.

        Args:
            event_id (str): ID of the event.
            participant_id (str): Participant's ID to remove.

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

        Constraints:
            - Event must exist.
            - Participant must exist.
            - Participant must be currently assigned to event to remove.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant does not exist." }
    
        event = self.events[event_id]
        if participant_id not in event["participant_ids"]:
            return { "success": False, "error": "Participant is not assigned to this event." }
    
        event["participant_ids"].remove(participant_id)
        return { "success": True, "message": f"Participant {participant_id} removed from event {event_id}." }


class EventManagementSystem(BaseEnv):
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
            if key == "get_event_categories":
                setattr(env, "_get_event_categories_state", copy.deepcopy(value))
            else:
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

    def list_events(self, **kwargs):
        return self._call_inner_tool('list_events', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def find_events_by_date(self, **kwargs):
        return self._call_inner_tool('find_events_by_date', kwargs)

    def find_events_by_category(self, **kwargs):
        return self._call_inner_tool('find_events_by_category', kwargs)

    def find_events_by_date_and_category(self, **kwargs):
        return self._call_inner_tool('find_events_by_date_and_category', kwargs)

    def get_events_at_location_on_date(self, **kwargs):
        return self._call_inner_tool('get_events_at_location_on_date', kwargs)

    def list_participants(self, **kwargs):
        return self._call_inner_tool('list_participants', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def list_locations(self, **kwargs):
        return self._call_inner_tool('list_locations', kwargs)

    def get_location_by_id(self, **kwargs):
        return self._call_inner_tool('get_location_by_id', kwargs)

    def get_participants_for_event(self, **kwargs):
        return self._call_inner_tool('get_participants_for_event', kwargs)

    def get_events_for_participant(self, **kwargs):
        return self._call_inner_tool('get_events_for_participant', kwargs)

    def check_location_availability(self, **kwargs):
        return self._call_inner_tool('check_location_availability', kwargs)

    def get_event_categories(self, **kwargs):
        return self._call_inner_tool('get_event_categories', kwargs)

    def add_event(self, **kwargs):
        return self._call_inner_tool('add_event', kwargs)

    def update_event(self, **kwargs):
        return self._call_inner_tool('update_event', kwargs)

    def remove_event(self, **kwargs):
        return self._call_inner_tool('remove_event', kwargs)

    def add_participant(self, **kwargs):
        return self._call_inner_tool('add_participant', kwargs)

    def update_participant(self, **kwargs):
        return self._call_inner_tool('update_participant', kwargs)

    def remove_participant(self, **kwargs):
        return self._call_inner_tool('remove_participant', kwargs)

    def add_location(self, **kwargs):
        return self._call_inner_tool('add_location', kwargs)

    def update_location(self, **kwargs):
        return self._call_inner_tool('update_location', kwargs)

    def remove_location(self, **kwargs):
        return self._call_inner_tool('remove_location', kwargs)

    def assign_participant_to_event(self, **kwargs):
        return self._call_inner_tool('assign_participant_to_event', kwargs)

    def remove_participant_from_event(self, **kwargs):
        return self._call_inner_tool('remove_participant_from_event', kwargs)
