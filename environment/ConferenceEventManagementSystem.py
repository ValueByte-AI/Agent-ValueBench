# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# Domain entity
class DomainInfo(TypedDict):
    domain_id: str
    domain_name: str
    description: str
    related_events: List[str]

# Theme entity
class ThemeInfo(TypedDict):
    theme_id: str
    theme_name: str
    description: str
    related_domains: List[str]
    related_events: List[str]

# Event entity
class EventInfo(TypedDict):
    event_id: str
    event_name: str
    domain_id: str
    theme_id: str
    schedule_id: str
    description: str
    organizer_id: str
    status: str

# Schedule entity
class ScheduleInfo(TypedDict):
    schedule_id: str
    event_id: str
    date: str
    time: str
    location: str
    session_list: List[str]

# Speaker entity
class SpeakerInfo(TypedDict):
    speaker_id: str
    name: str
    bio: str
    event_ids: List[str]
    topic: str

# Attendee entity
class AttendeeInfo(TypedDict):
    attendee_id: str
    name: str
    company: str
    registered_event_ids: List[str]
    attendance_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Domains: {domain_id: DomainInfo}
        self.domains: Dict[str, DomainInfo] = {}
        # Themes: {theme_id: ThemeInfo}
        self.themes: Dict[str, ThemeInfo] = {}
        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}
        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}
        # Speakers: {speaker_id: SpeakerInfo}
        self.speakers: Dict[str, SpeakerInfo] = {}
        # Attendees: {attendee_id: AttendeeInfo}
        self.attendees: Dict[str, AttendeeInfo] = {}

        # Constraints:
        # - All IDs referenced (domain_id, theme_id, event_id, etc.) must correspond to existing entities.
        # - Each event must be linked to a valid domain and theme.
        # - Updates or deletions must maintain referential integrity across entities 
        #   (e.g., removing a domain should not orphan any event).
        # - Access to entity details may be governed by user roles (organizer, speaker, attendee).

    def get_domain_by_id(self, domain_id: str) -> dict:
        """
        Retrieve all details for a specific domain given its domain_id.

        Args:
            domain_id (str): The unique identifier of the domain.

        Returns:
            dict: 
              - On success: { "success": True, "data": DomainInfo }
              - On failure: { "success": False, "error": "Domain not found" }

        Constraints:
            - domain_id must exist in the domains store.
        """
        data = self.domains.get(domain_id)
        if data is None:
            return { "success": False, "error": "Domain not found" }
        return { "success": True, "data": data }

    def get_theme_by_id(self, theme_id: str) -> dict:
        """
        Retrieve all details for a specific theme given its theme_id.

        Args:
            theme_id (str): The unique identifier of the theme.

        Returns:
            dict: {
                "success": True,
                "data": <ThemeInfo>
            }
            or
            {
                "success": False,
                "error": "Theme not found"
            }

        Constraints:
            - The theme_id must exist in the system.
        """
        if theme_id not in self.themes:
            return {"success": False, "error": "Theme not found"}
        return {"success": True, "data": self.themes[theme_id]}

    def list_domains(self) -> dict:
        """
        List all domains in the system with their complete details.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainInfo]  # List of all domain info (may be empty if no domains exist)
            }
        Constraints:
            - None for this operation (just a data dump).
        """
        return {
            "success": True,
            "data": list(self.domains.values())
        }

    def list_themes(self) -> dict:
        """
        List all themes in the system with full details.

        Args:
            None

        Returns:
            dict:
                "success": True if operation completed, always true for this operation.
                "data": List[ThemeInfo] - List of all theme records (possibly empty).
        """
        themes_list = list(self.themes.values())
        return {
            "success": True,
            "data": themes_list
        }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve full details of a specific event given its event_id.

        Args:
            event_id (str): The unique identifier of the event to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": EventInfo  # Event details as a dict
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Event not found"
                    }

        Constraints:
            - The event_id must exist in the system.
        """
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def list_events(
        self, 
        status: str = None, 
        domain_id: str = None, 
        theme_id: str = None
    ) -> dict:
        """
        List all events in the system with optional filtering by status, domain, or theme.

        Args:
            status (str, optional): Filter events by status (e.g., 'active', 'cancelled').
            domain_id (str, optional): Filter events by this domain_id. Must exist if provided.
            theme_id (str, optional): Filter events by this theme_id. Must exist if provided.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "data": List[EventInfo]  # List of event info dicts matching all provided filters.
                    }
                If error:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., non-existent domain or theme)
                    }

        Constraints:
            - If domain_id is provided, it must correspond to an existing domain.
            - If theme_id is provided, it must correspond to an existing theme.
        """

        # Validate filters
        if domain_id is not None and domain_id not in self.domains:
            return { "success": False, "error": f"Domain '{domain_id}' does not exist" }
        if theme_id is not None and theme_id not in self.themes:
            return { "success": False, "error": f"Theme '{theme_id}' does not exist" }

        result = []
        for event in self.events.values():
            if status is not None and event["status"] != status:
                continue
            if domain_id is not None and event["domain_id"] != domain_id:
                continue
            if theme_id is not None and event["theme_id"] != theme_id:
                continue
            result.append(event)

        return { "success": True, "data": result }

    def list_events_by_domain(self, domain_id: str) -> dict:
        """
        Retrieve all events associated with a specific domain_id.

        Args:
            domain_id (str): The ID of the domain for which to list events.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],  # EventInfo list associated with the domain (can be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid domain_id)
            }

        Constraints:
            - The domain_id must exist in the system.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain does not exist"}

        events = [event for event in self.events.values() if event["domain_id"] == domain_id]
        return {"success": True, "data": events}

    def list_events_by_theme(self, theme_id: str) -> dict:
        """
        Retrieve all events associated with the specified theme_id.

        Args:
            theme_id (str): The ID of the theme to query events for.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[EventInfo]  # List of matching events (may be empty if no events)
                }
                or
                {
                    "success": False,
                    "error": str  # Why the operation failed, e.g., theme does not exist
                }

        Constraints:
            - theme_id must exist in the system.
            - Returns all events whose 'theme_id' field matches the supplied theme_id.
        """
        if theme_id not in self.themes:
            return {"success": False, "error": "Theme does not exist"}

        matching_events = [event for event in self.events.values() if event["theme_id"] == theme_id]

        return {"success": True, "data": matching_events}

    def get_schedule_by_event_id(self, event_id: str) -> dict:
        """
        Fetch the schedule information for a given event_id.

        Args:
            event_id (str): The unique identifier of the event.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": ScheduleInfo }
                - On failure:
                    {"success": False, "error": str }

        Constraints:
            - The event_id must exist.
            - The event's schedule_id must point to an existing schedule.
        """
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}

        schedule_id = event.get("schedule_id")
        if not schedule_id:
            return {"success": False, "error": "Event has no associated schedule_id"}

        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found for event"}

        return {"success": True, "data": schedule}

    def get_speaker_by_id(self, speaker_id: str) -> dict:
        """
        Retrieve details for a specific speaker using their speaker_id.

        Args:
            speaker_id (str): The unique identifier of the speaker.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": SpeakerInfo   # Details of the requested speaker.
                }
                On failure: {
                    "success": False,
                    "error": "Speaker not found"
                }

        Constraints:
            - The speaker_id must exist in the system.
        """
        speaker = self.speakers.get(speaker_id)
        if speaker is None:
            return { "success": False, "error": "Speaker not found" }
        return { "success": True, "data": speaker }

    def list_speakers_for_event(self, event_id: str) -> dict:
        """
        List all speakers associated with a given event by event_id.

        Args:
            event_id (str): The unique identifier of the event.

        Returns:
            dict: {
                "success": True,
                "data": List[SpeakerInfo]  # List of speakers (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if event does not exist
            }

        Constraints:
            - The provided event_id must exist in the system.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        speakers = [
            speaker_info
            for speaker_info in self.speakers.values()
            if event_id in speaker_info.get("event_ids", [])
        ]

        return { "success": True, "data": speakers }

    def get_attendee_by_id(self, attendee_id: str) -> dict:
        """
        Retrieve the details of a specific attendee by their attendee_id.

        Args:
            attendee_id (str): The unique identifier of the attendee.

        Returns:
            dict: {
                "success": True,
                "data": AttendeeInfo  # Attendee details if found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. attendee not found
            }

        Constraints:
            - attendee_id must exist in the system.
        """
        attendee = self.attendees.get(attendee_id)
        if attendee is None:
            return { "success": False, "error": "Attendee not found" }
        return { "success": True, "data": attendee }

    def list_attendees_for_event(self, event_id: str) -> dict:
        """
        List all attendees registered for a specific event.

        Args:
            event_id (str): The event identifier to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[AttendeeInfo],  # All attendees whose registered_event_ids contain event_id
            }
            or
            {
                "success": False,
                "error": str  # If the event_id does not exist
            }

        Constraints:
            - event_id must exist in self.events.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event ID does not exist." }

        attendees_list = [
            attendee for attendee in self.attendees.values()
            if event_id in attendee.get("registered_event_ids", [])
        ]
        return { "success": True, "data": attendees_list }

    def list_events_for_attendee(self, attendee_id: str) -> dict:
        """
        List all events that an attendee is registered for, given the attendee_id.

        Args:
            attendee_id (str): The unique identifier of the attendee.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[EventInfo],  # May be empty if not attending any events
                  }
                - On failure: {
                    "success": False,
                    "error": "Attendee does not exist"
                  }

        Constraints:
            - attendee_id must exist in self.attendees.
            - Only return events which actually exist in self.events (skip missing/invalid event_ids).
        """
        attendee = self.attendees.get(attendee_id)
        if not attendee:
            return { "success": False, "error": "Attendee does not exist" }

        event_infos = [
            self.events[event_id] for event_id in attendee.get('registered_event_ids', [])
            if event_id in self.events
        ]

        return { "success": True, "data": event_infos }

    def get_related_themes_for_domain(self, domain_id: str) -> dict:
        """
        List all themes associated with a domain via related_domains and related_events relationships.

        Args:
            domain_id (str): The ID of the domain for which to find related themes.

        Returns:
            dict: {
                "success": True,
                "data": List[ThemeInfo],  # List of matching ThemeInfo dicts; empty if none
            }
            or
            {
                "success": False,
                "error": str  # if domain_id does not exist
            }

        Constraints:
            - domain_id must refer to an existing domain.
            - Theme is related if domain_id is in related_domains, or
              if theme_id is attached to an event whose domain_id matches.
            - No duplicates in the result.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain does not exist"}

        related_theme_ids = set()
        # 1. Themes with this domain_id in related_domains
        for theme_id, theme in self.themes.items():
            if domain_id in theme.get("related_domains", []):
                related_theme_ids.add(theme_id)

        # 2. Themes associated with events of this domain
        for event in self.events.values():
            if event.get("domain_id") == domain_id:
                theme_id = event.get("theme_id")
                if theme_id in self.themes:
                    related_theme_ids.add(theme_id)

        result = [self.themes[theme_id] for theme_id in related_theme_ids]
        return {"success": True, "data": result}

    def get_related_domains_for_theme(self, theme_id: str) -> dict:
        """
        List all domains associated with a specified theme via its related_domains list.

        Args:
            theme_id (str): The unique id for the theme whose related domains are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainInfo],  # List of domain info dicts (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str,  # Theme not found
            }

        Constraints:
            - The theme_id must exist in the system.
            - Only domains whose IDs exist in self.domains will be returned.
        """
        theme = self.themes.get(theme_id)
        if not theme:
            return { "success": False, "error": "Theme not found" }

        related_domains = []
        for domain_id in theme.get("related_domains", []):
            domain_info = self.domains.get(domain_id)
            if domain_info:
                related_domains.append(domain_info)
            # Silently skip any non-existent domain_ids
    
        return { "success": True, "data": related_domains }

    def get_sessions_by_schedule_id(self, schedule_id: str) -> dict:
        """
        Retrieve all session details (session_list) for the specified schedule_id.

        Args:
            schedule_id (str): Unique identifier for the schedule.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of session identifiers/details (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., schedule_id not found)
            }

        Constraints:
            - The schedule_id must reference an existing schedule.
        """
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            return { "success": False, "error": "Schedule ID not found" }

        return { "success": True, "data": schedule.get("session_list", []) }

    def update_domain(
        self,
        domain_id: str,
        domain_name: str = None,
        description: str = None,
        related_events: list = None
    ) -> dict:
        """
        Modify the attributes or associations of a domain.

        Args:
            domain_id (str): The ID of the domain to update.
            domain_name (str, optional): New name for the domain.
            description (str, optional): New description for the domain.
            related_events (list, optional): New list of related event IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Domain updated successfully"
            } on success,
            or
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - domain_id must exist in the system.
            - Any event_id in related_events must correspond to an existing event.
            - Updates must maintain referential integrity.
        """
        # Check that the domain exists
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain does not exist" }

        domain_info = self.domains[domain_id]

        # Validate related_events
        if related_events is not None:
            for event_id in related_events:
                if event_id not in self.events:
                    return { "success": False, "error": f"Related event '{event_id}' does not exist" }

        # Apply the updates
        if domain_name is not None:
            domain_info['domain_name'] = domain_name
        if description is not None:
            domain_info['description'] = description
        if related_events is not None:
            domain_info['related_events'] = list(related_events)  # Ensure it's a list copy

        # Save updated info back (not strictly necessary for dicts but for structure)
        self.domains[domain_id] = domain_info
        return { "success": True, "message": "Domain updated successfully" }

    def delete_domain(self, domain_id: str) -> dict:
        """
        Remove a domain from the system, ensuring referential integrity:
        - Cannot delete if any event references the domain.
        - Cleans up references from themes' related_domains lists.

        Args:
            domain_id (str): The ID of the domain to delete.

        Returns:
            dict: Success or error message.

        Constraints:
            - The domain must exist.
            - Cannot delete if any event has domain_id == domain_id.
            - After deletion, remove from all themes' related_domains.
        """
        # Check if domain exists
        if domain_id not in self.domains:
            return {"success": False, "error": f"Domain '{domain_id}' does not exist."}

        # Ensure no event references this domain
        for event in self.events.values():
            if event["domain_id"] == domain_id:
                return {
                    "success": False,
                    "error": f"Cannot delete domain '{domain_id}': it is referenced by event '{event['event_id']}'."
                }

        # Remove domain_id from related_domains of all themes
        for theme in self.themes.values():
            if domain_id in theme["related_domains"]:
                theme["related_domains"] = [d for d in theme["related_domains"] if d != domain_id]

        # Remove domain itself
        del self.domains[domain_id]

        return {"success": True, "message": f"Domain '{domain_id}' deleted."}

    def update_theme(
        self,
        theme_id: str,
        theme_name: str = None,
        description: str = None,
        related_domains: list = None,
        related_events: list = None
    ) -> dict:
        """
        Modify the attributes or associations of a theme.

        Args:
            theme_id (str): The ID of the theme to modify.
            theme_name (str, optional): New name for the theme.
            description (str, optional): New description.
            related_domains (List[str], optional): Updated list of domain IDs associated with this theme.
            related_events (List[str], optional): Updated list of event IDs associated with this theme.

        Returns:
            dict: {
                "success": True,
                "message": "Theme updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - theme_id must exist.
            - Related domain_ids and event_ids must exist if provided.
            - Updates must be mirrored in associated entities to maintain referential integrity.
            - At least one attribute must be provided for update.
        """
        # Check if theme_id exists
        if theme_id not in self.themes:
            return {"success": False, "error": "Theme ID does not exist."}

        theme = self.themes[theme_id]
        touched = False

        # Update theme_name if provided
        if theme_name is not None:
            theme["theme_name"] = theme_name
            touched = True

        # Update description if provided
        if description is not None:
            theme["description"] = description
            touched = True

        # Update related_domains if provided
        if related_domains is not None:
            # Validate all domain_ids exist
            invalid_domains = [d for d in related_domains if d not in self.domains]
            if invalid_domains:
                return {
                    "success": False,
                    "error": f"The following domain IDs do not exist: {invalid_domains}"
                }
            # Remove this theme_id from previous domains' related_themes
            previous_domains = set(theme["related_domains"])
            new_domains = set(related_domains)
            for d_id in previous_domains - new_domains:
                if d_id in self.domains:
                    if "related_themes" in self.domains[d_id]:
                        if theme_id in self.domains[d_id]["related_themes"]:
                            self.domains[d_id]["related_themes"].remove(theme_id)
                    # If related_themes doesn't exist, skip (tolerate as per current schema)
            # Add this theme_id to new domains' related_themes
            for d_id in new_domains:
                if "related_themes" not in self.domains[d_id]:
                    self.domains[d_id]["related_themes"] = []
                if theme_id not in self.domains[d_id]["related_themes"]:
                    self.domains[d_id]["related_themes"].append(theme_id)
            # Update theme object
            theme["related_domains"] = related_domains
            touched = True

        # Update related_events if provided
        if related_events is not None:
            # Validate all event_ids exist
            invalid_events = [e for e in related_events if e not in self.events]
            if invalid_events:
                return {
                    "success": False,
                    "error": f"The following event IDs do not exist: {invalid_events}"
                }
            # Remove this theme_id from previous events' related_themes if such structure exists
            previous_events = set(theme["related_events"])
            new_events = set(related_events)
            # No cross-references in current schema for Event => Theme, so skip
            # Update theme object
            theme["related_events"] = related_events
            touched = True

        if not touched:
            return {
                "success": False,
                "error": "No attributes provided to update."
            }

        self.themes[theme_id] = theme

        return {
            "success": True,
            "message": "Theme updated successfully."
        }

    def delete_theme(self, theme_id: str) -> dict:
        """
        Remove a theme from the system. Deletion is only allowed if no events currently reference this theme (referential integrity).

        Args:
            theme_id (str): The unique ID of the theme to delete.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Theme <theme_id> deleted."}
                - On failure:
                    {"success": False, "error": "reason"}
    
        Constraints:
            - Theme must exist.
            - No event should reference this theme (i.e., for all events, event['theme_id'] != theme_id).
        """
        # Check if theme exists
        if theme_id not in self.themes:
            return {"success": False, "error": f"Theme {theme_id} does not exist."}

        # Check for referential integrity: any event references this theme?
        for event in self.events.values():
            if event["theme_id"] == theme_id:
                return {
                    "success": False,
                    "error": f"Cannot delete theme {theme_id}: it is still referenced by event {event['event_id']}."
                }

        # Remove from self.themes
        del self.themes[theme_id]

        # Optionally: cleanup theme_id from related_events of domains (not needed per current attributes)
        # Remove theme_id from any related_events in the theme's related_domains, if such cross-linking exists
        # but none is in the present model (Theme maintains links, not domain)

        return {"success": True, "message": f"Theme {theme_id} deleted."}

    def update_event(self, event_id: str, update_fields: dict) -> dict:
        """
        Modify the details of an event.

        Args:
            event_id (str): The ID of the event to modify.
            update_fields (dict): A dictionary of fields to update in the event (keys may include: 
                                  event_name, description, domain_id, theme_id, schedule_id, organizer_id, status).

        Returns:
            dict: Success or failure information.
                On success: { "success": True, "message": "Event <event_id> updated successfully" }
                On error:   { "success": False, "error": <reason> }

        Constraints:
            - All referenced IDs (domain_id, theme_id, schedule_id) must exist in their respective entities.
            - If domain_id or theme_id changes, referential integrity must be maintained for related_events in Domain/Theme.
        """
        # Check if event exists
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        event = self.events[event_id]
        old_domain_id = event["domain_id"]
        old_theme_id = event["theme_id"]
        old_schedule_id = event["schedule_id"]

        # Pre-check validity of referenced IDs (if being changed)
        if "domain_id" in update_fields:
            new_domain_id = update_fields["domain_id"]
            if new_domain_id not in self.domains:
                return {"success": False, "error": f"Domain ID '{new_domain_id}' does not exist"}
        else:
            new_domain_id = old_domain_id

        if "theme_id" in update_fields:
            new_theme_id = update_fields["theme_id"]
            if new_theme_id not in self.themes:
                return {"success": False, "error": f"Theme ID '{new_theme_id}' does not exist"}
        else:
            new_theme_id = old_theme_id

        if "schedule_id" in update_fields:
            new_schedule_id = update_fields["schedule_id"]
            if new_schedule_id not in self.schedules:
                return {"success": False, "error": f"Schedule ID '{new_schedule_id}' does not exist"}
        else:
            new_schedule_id = old_schedule_id

        # Update referential integrity for domain_id if changed
        if new_domain_id != old_domain_id:
            # Remove event from old domain's related_events
            if event_id in self.domains[old_domain_id]["related_events"]:
                self.domains[old_domain_id]["related_events"].remove(event_id)
            # Add event to new domain's related_events
            if event_id not in self.domains[new_domain_id]["related_events"]:
                self.domains[new_domain_id]["related_events"].append(event_id)
            event["domain_id"] = new_domain_id

        # Update referential integrity for theme_id if changed
        if new_theme_id != old_theme_id:
            if event_id in self.themes[old_theme_id]["related_events"]:
                self.themes[old_theme_id]["related_events"].remove(event_id)
            if event_id not in self.themes[new_theme_id]["related_events"]:
                self.themes[new_theme_id]["related_events"].append(event_id)
            event["theme_id"] = new_theme_id

        # Update schedule_id if changed (no referential links maintained for schedule, just validity check)
        if new_schedule_id != old_schedule_id:
            event["schedule_id"] = new_schedule_id

        # Update other fields
        for key in ["event_name", "description", "organizer_id", "status"]:
            if key in update_fields:
                event[key] = update_fields[key]

        # Ensure event is updated in storage
        self.events[event_id] = event

        return {"success": True, "message": f"Event {event_id} updated successfully"}

    def delete_event(self, event_id: str) -> dict:
        """
        Delete an event by its ID, ensuring referential integrity by:
          - Removing the event from `self.events`.
          - Updating all related Domains (remove event_id from related_events).
          - Updating all related Themes (remove event_id from related_events).
          - Deleting the associated Schedule (if any).
          - Updating all Speakers (remove event_id from event_ids).
          - Updating all Attendees (remove event_id from registered_event_ids).

        Args:
            event_id (str): The ID of the event to be deleted.

        Returns:
            dict:
                On success: { "success": True, "message": "Event <event_id> deleted successfully" }
                On failure: { "success": False, "error": "Event does not exist" }

        Constraints:
            - Event must exist.
            - Referential integrity must be preserved across domains, themes, schedules, speakers, attendees.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }
    
        # Remove from domain's related_events
        domain_id = self.events[event_id]["domain_id"]
        if domain_id in self.domains:
            domain_events = self.domains[domain_id]["related_events"]
            if event_id in domain_events:
                domain_events.remove(event_id)
    
        # Remove from theme's related_events
        theme_id = self.events[event_id]["theme_id"]
        if theme_id in self.themes:
            theme_events = self.themes[theme_id]["related_events"]
            if event_id in theme_events:
                theme_events.remove(event_id)
    
        # Remove & delete associated schedule
        schedule_id = self.events[event_id]["schedule_id"]
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
    
        # Remove event from speakers' event_ids
        for speaker in self.speakers.values():
            if event_id in speaker["event_ids"]:
                speaker["event_ids"].remove(event_id)

        # Remove event from attendees' registered_event_ids
        for attendee in self.attendees.values():
            if event_id in attendee["registered_event_ids"]:
                attendee["registered_event_ids"].remove(event_id)

        # Delete the event itself
        del self.events[event_id]
    
        return { "success": True, "message": f"Event {event_id} deleted successfully" }

    def create_event(
        self,
        event_id: str,
        event_name: str,
        domain_id: str,
        theme_id: str,
        schedule_id: str,
        description: str,
        organizer_id: str,
        status: str
    ) -> dict:
        """
        Add a new event to the system, ensuring it is linked to existing valid domain and theme.

        Args:
            event_id (str): Unique identifier for the event.
            event_name (str): Name of the event.
            domain_id (str): Existing domain's ID to link to the event.
            theme_id (str): Existing theme's ID to link to the event.
            schedule_id (str): Schedule ID to associate with the event (should exist in schedules or be managed separately).
            description (str): Description of the event.
            organizer_id (str): ID of the event organizer.
            status (str): Status string for the event (e.g., "upcoming", "active", etc.).

        Returns:
            dict: Success or failure with explanation/message.

        Constraints:
            - event_id must be unique (must not exist in events).
            - domain_id must exist in domains.
            - theme_id must exist in themes.
            - On success, update related_events in DomainInfo and ThemeInfo.
        """
        # Check if event_id is unique
        if event_id in self.events:
            return { "success": False, "error": "Event ID already exists." }

        # Check that domain_id exists
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain ID does not exist." }

        # Check that theme_id exists
        if theme_id not in self.themes:
            return { "success": False, "error": "Theme ID does not exist." }

        # (Optional) Check that schedule_id is unique or not in use by another event
        # (Here we assume it's acceptable to let schedule creation be handled elsewhere)

        # Create the new event
        event_info = {
            "event_id": event_id,
            "event_name": event_name,
            "domain_id": domain_id,
            "theme_id": theme_id,
            "schedule_id": schedule_id,
            "description": description,
            "organizer_id": organizer_id,
            "status": status
        }
        self.events[event_id] = event_info

        # Update Domain: add event_id to related_events if not already present
        if event_id not in self.domains[domain_id]["related_events"]:
            self.domains[domain_id]["related_events"].append(event_id)

        # Update Theme: add event_id to related_events if not already present
        if event_id not in self.themes[theme_id]["related_events"]:
            self.themes[theme_id]["related_events"].append(event_id)

        return {
            "success": True,
            "message": f"Event {event_id} created successfully."
        }

    def update_schedule(
        self,
        schedule_id: str,
        date: str = None,
        time: str = None,
        location: str = None,
        session_list: list = None
    ) -> dict:
        """
        Adjust the timing, location, or sessions of a schedule.

        Args:
            schedule_id (str): The unique ID of the schedule to update.
            date (str, optional): New date for the schedule.
            time (str, optional): New time for the schedule.
            location (str, optional): New location for the schedule.
            session_list (List[str], optional): New list of session names/IDs.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - schedule_id must exist.
            - session_list (if provided) must be a list of strings.
            - If no valid fields are provided to update, fail.
        """
        # Check whether schedule exists
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule does not exist."}

        schedule = self.schedules[schedule_id]
        updated = False

        # Validate session_list if provided
        if session_list is not None:
            if not isinstance(session_list, list) or not all(isinstance(s, str) for s in session_list):
                return {"success": False, "error": "session_list must be a list of strings."}
            schedule["session_list"] = session_list
            updated = True

        if date is not None:
            schedule["date"] = date
            updated = True
        if time is not None:
            schedule["time"] = time
            updated = True
        if location is not None:
            schedule["location"] = location
            updated = True

        if not updated:
            return {"success": False, "error": "No valid fields provided to update."}

        self.schedules[schedule_id] = schedule  # Update in-place, but explicitly overwrite for clarity

        return {"success": True, "message": "Schedule updated successfully."}

    def update_speaker(
        self,
        speaker_id: str,
        name: str = None,
        bio: str = None,
        event_ids: list = None,
        topic: str = None
    ) -> dict:
        """
        Update a speaker's information, associated event IDs, or topic.

        Args:
            speaker_id (str): Unique identifier of the speaker to update.
            name (str, optional): New name for the speaker.
            bio (str, optional): New biography for the speaker.
            event_ids (list[str], optional): List of event IDs to associate with the speaker.
            topic (str, optional): New topic for the speaker.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Speaker updated successfully."}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - speaker_id must exist.
            - If provided, every event_id in event_ids must exist in the system.
            - No update is made if none of the optional fields is provided.
        """
        # Check existence
        if speaker_id not in self.speakers:
            return {"success": False, "error": "Speaker not found."}

        speaker = self.speakers[speaker_id]

        # Track if anything is updated
        updated = False

        # Update fields if provided
        if name is not None:
            speaker['name'] = name
            updated = True
        if bio is not None:
            speaker['bio'] = bio
            updated = True
        if event_ids is not None:
            # Validate event IDs
            for eid in event_ids:
                if eid not in self.events:
                    return {
                        "success": False,
                        "error": f"Event ID '{eid}' does not exist in the system."
                    }
            speaker['event_ids'] = event_ids
            updated = True
        if topic is not None:
            speaker['topic'] = topic
            updated = True

        if not updated:
            return {"success": False, "error": "No fields specified for update."}

        self.speakers[speaker_id] = speaker
        return {"success": True, "message": "Speaker updated successfully."}

    def update_attendee(
        self,
        attendee_id: str,
        name: str = None,
        company: str = None,
        registered_event_ids: list = None,
        attendance_status: str = None
    ) -> dict:
        """
        Modify attendee details, registered events, or attendance status.

        Args:
            attendee_id (str): Unique identifier of the attendee to update.
            name (str, optional): New name of the attendee.
            company (str, optional): New company of the attendee.
            registered_event_ids (List[str], optional): List of event IDs the attendee should be registered for.
            attendance_status (str, optional): Updated attendance status.

        Returns:
            dict:
                On success: { "success": True, "message": "Attendee updated" }
                On failure: { "success": False, "error": "<description>" }

        Constraints:
            - The attendee must exist.
            - If provided, all event_ids in `registered_event_ids` must exist in the system.
            - No partial updates if event_ids are invalid.
        """
        if attendee_id not in self.attendees:
            return {"success": False, "error": "Attendee does not exist"}

        # Check event IDs, if provided
        if registered_event_ids is not None:
            invalid_events = [eid for eid in registered_event_ids if eid not in self.events]
            if invalid_events:
                return {
                    "success": False,
                    "error": f"The following event_ids do not exist: {invalid_events}"
                }

        attendee = self.attendees[attendee_id]
        updated = False

        if name is not None:
            attendee["name"] = name
            updated = True
        if company is not None:
            attendee["company"] = company
            updated = True
        if registered_event_ids is not None:
            attendee["registered_event_ids"] = registered_event_ids
            updated = True
        if attendance_status is not None:
            attendee["attendance_status"] = attendance_status
            updated = True

        if updated:
            return {"success": True, "message": "Attendee updated"}
        else:
            return {"success": True, "message": "No changes made to attendee"}

    def register_attendee_for_event(self, attendee_id: str, event_id: str) -> dict:
        """
        Registers an attendee for an event. Adds the event_id to the attendee's registered_event_ids list,
        ensuring no duplicate registrations, and maintains referential integrity.

        Args:
            attendee_id (str): The unique identifier of the attendee.
            event_id (str): The unique identifier of the event.

        Returns:
            dict:
                - On success: {"success": True, "message": "Attendee registered for event."}
                - On failure: {"success": False, "error": str}
    
        Constraints:
            - Both attendee_id and event_id must exist.
            - Attendee must not already be registered for the event.
        """
        attendee = self.attendees.get(attendee_id)
        if attendee is None:
            return {"success": False, "error": "Attendee ID does not exist."}

        event = self.events.get(event_id)
        if event is None:
            return {"success": False, "error": "Event ID does not exist."}

        if event_id in attendee["registered_event_ids"]:
            return {"success": False, "error": "Attendee already registered for this event."}

        attendee["registered_event_ids"].append(event_id)
        return {"success": True, "message": "Attendee registered for event."}

    def unregister_attendee_from_event(self, attendee_id: str, event_id: str) -> dict:
        """
        Remove an attendee from an event, ensuring referential integrity.

        Args:
            attendee_id (str): The unique ID of the attendee to unregister.
            event_id (str): The unique ID of the event from which to unregister the attendee.

        Returns:
            dict: {
                "success": True,
                "message": "Attendee <attendee_id> unregistered from event <event_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Both attendee_id and event_id must exist.
            - The attendee must currently be registered for the event.
            - Reference integrity must be maintained after the operation.
        """
        # Check if attendee exists
        attendee = self.attendees.get(attendee_id)
        if attendee is None:
            return { "success": False, "error": f"Attendee '{attendee_id}' does not exist." }

        # Check if event exists
        if event_id not in self.events:
            return { "success": False, "error": f"Event '{event_id}' does not exist." }

        # Check registration
        if event_id not in attendee["registered_event_ids"]:
            return { "success": False, "error": f"Attendee '{attendee_id}' is not registered for event '{event_id}'." }

        # Remove the event from the attendee's registered_event_ids
        attendee["registered_event_ids"].remove(event_id)

        return {
            "success": True,
            "message": f"Attendee '{attendee_id}' unregistered from event '{event_id}'."
        }


class ConferenceEventManagementSystem(BaseEnv):
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

    def get_domain_by_id(self, **kwargs):
        return self._call_inner_tool('get_domain_by_id', kwargs)

    def get_theme_by_id(self, **kwargs):
        return self._call_inner_tool('get_theme_by_id', kwargs)

    def list_domains(self, **kwargs):
        return self._call_inner_tool('list_domains', kwargs)

    def list_themes(self, **kwargs):
        return self._call_inner_tool('list_themes', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_events(self, **kwargs):
        return self._call_inner_tool('list_events', kwargs)

    def list_events_by_domain(self, **kwargs):
        return self._call_inner_tool('list_events_by_domain', kwargs)

    def list_events_by_theme(self, **kwargs):
        return self._call_inner_tool('list_events_by_theme', kwargs)

    def get_schedule_by_event_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_event_id', kwargs)

    def get_speaker_by_id(self, **kwargs):
        return self._call_inner_tool('get_speaker_by_id', kwargs)

    def list_speakers_for_event(self, **kwargs):
        return self._call_inner_tool('list_speakers_for_event', kwargs)

    def get_attendee_by_id(self, **kwargs):
        return self._call_inner_tool('get_attendee_by_id', kwargs)

    def list_attendees_for_event(self, **kwargs):
        return self._call_inner_tool('list_attendees_for_event', kwargs)

    def list_events_for_attendee(self, **kwargs):
        return self._call_inner_tool('list_events_for_attendee', kwargs)

    def get_related_themes_for_domain(self, **kwargs):
        return self._call_inner_tool('get_related_themes_for_domain', kwargs)

    def get_related_domains_for_theme(self, **kwargs):
        return self._call_inner_tool('get_related_domains_for_theme', kwargs)

    def get_sessions_by_schedule_id(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_schedule_id', kwargs)

    def update_domain(self, **kwargs):
        return self._call_inner_tool('update_domain', kwargs)

    def delete_domain(self, **kwargs):
        return self._call_inner_tool('delete_domain', kwargs)

    def update_theme(self, **kwargs):
        return self._call_inner_tool('update_theme', kwargs)

    def delete_theme(self, **kwargs):
        return self._call_inner_tool('delete_theme', kwargs)

    def update_event(self, **kwargs):
        return self._call_inner_tool('update_event', kwargs)

    def delete_event(self, **kwargs):
        return self._call_inner_tool('delete_event', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def update_schedule(self, **kwargs):
        return self._call_inner_tool('update_schedule', kwargs)

    def update_speaker(self, **kwargs):
        return self._call_inner_tool('update_speaker', kwargs)

    def update_attendee(self, **kwargs):
        return self._call_inner_tool('update_attendee', kwargs)

    def register_attendee_for_event(self, **kwargs):
        return self._call_inner_tool('register_attendee_for_event', kwargs)

    def unregister_attendee_from_event(self, **kwargs):
        return self._call_inner_tool('unregister_attendee_from_event', kwargs)

