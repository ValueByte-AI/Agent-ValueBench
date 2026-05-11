# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



# TypedDicts for state space entities

class ResourceInfo(TypedDict):
    resource_id: str
    name: str
    type: str
    location: str
    availability_status: str

class EventInfo(TypedDict):
    event_id: str
    title: str
    description: str
    start_time: str
    end_time: str
    location: str
    organizer_id: str
    resource_ids: List[str]
    participants: List[str]

class UserInfo(TypedDict):
    user_id: str
    name: str
    role: str
    contact_info: str
    account_status: str

class SessionInfo(TypedDict):
    session_id: str
    user_id: str
    authentication_status: str
    last_active: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment to manage events, resources, users, and sessions for scheduling/booking.
        """

        # Resources: {resource_id: ResourceInfo}
        self.resources: Dict[str, ResourceInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}

        # Constraints:
        # - Only authenticated users can access event and resource details.
        # - Resource availability_status must be updated in real time to reflect bookings.
        # - An event must reference valid resource_ids that exist in self.resources.
        # - Each session is associated with exactly one user and expires after inactivity or logout.

    def _resource_linked_to_other_event(self, resource_id: str, excluding_event_id: str = None) -> bool:
        for event_id, event in self.events.items():
            if excluding_event_id is not None and event_id == excluding_event_id:
                continue
            if resource_id in event.get("resource_ids", []):
                return True
        return False

    def _resource_can_be_assigned(self, resource_id: str, excluding_event_id: str = None) -> bool:
        resource = self.resources.get(resource_id)
        if not resource:
            return False

        status = resource.get("availability_status")
        if status == "available":
            return True
        if status == "booked":
            # Allow resources pre-booked through `book_resource` if no other event
            # currently owns them, and allow resources already attached to the event
            # being updated.
            return not self._resource_linked_to_other_event(resource_id, excluding_event_id)
        return False

    def _mark_resource_booked(self, resource_id: str) -> None:
        resource = self.resources.get(resource_id)
        if resource and resource.get("availability_status") == "available":
            resource["availability_status"] = "booked"

    def _release_resource_if_unused(self, resource_id: str) -> None:
        resource = self.resources.get(resource_id)
        if not resource:
            return
        if self._resource_linked_to_other_event(resource_id):
            return
        if resource.get("availability_status") == "booked":
            resource["availability_status"] = "available"

    def check_authentication_status(self, session_id: str = None, user_id: str = None) -> dict:
        """
        Determines if a session or user is currently authenticated.
    
        Args:
            session_id (str, optional): The session ID to check authentication for.
            user_id (str, optional): The user ID to check authentication for (checks for any active session).
    
        Returns:
            dict: {
                "success": True,
                "data": {
                    "authenticated": bool,
                    "session_id": str or None,
                    "user_id": str or None,
                    "reason": str
                }
            }
            OR
            { "success": False, "error": str }
    
        Constraints:
            - At least one of session_id or user_id must be provided.
            - A session is considered authenticated if authentication_status == "authenticated".
        """
        if not session_id and not user_id:
            return {
                "success": False,
                "error": "Must provide either session_id or user_id."
            }

        # If session_id is provided, check that session.
        if session_id:
            session = self.sessions.get(session_id)
            if not session:
                return {
                    "success": False,
                    "error": f"Session with id '{session_id}' does not exist."
                }
            if session["authentication_status"] == "authenticated":
                return {
                    "success": True,
                    "data": {
                        "authenticated": True,
                        "session_id": session_id,
                        "user_id": session["user_id"],
                        "reason": "Session is authenticated."
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "authenticated": False,
                        "session_id": session_id,
                        "user_id": session["user_id"],
                        "reason": f"Session authentication_status is '{session['authentication_status']}'."
                    }
                }
        # Otherwise, check for any active/authenticated session for given user_id.
        if user_id:
            found_session = None
            for s in self.sessions.values():
                if s["user_id"] == user_id and s["authentication_status"] == "authenticated":
                    found_session = s
                    break
            if found_session:
                return {
                    "success": True,
                    "data": {
                        "authenticated": True,
                        "session_id": found_session["session_id"],
                        "user_id": user_id,
                        "reason": "User has an authenticated session."
                    }
                }
            else:
                # Check if user exists
                if user_id not in self.users:
                    return {
                        "success": False,
                        "error": f"User with id '{user_id}' does not exist."
                    }
                return {
                    "success": True,
                    "data": {
                        "authenticated": False,
                        "session_id": None,
                        "user_id": user_id,
                        "reason": "User has no authenticated session."
                    }
                }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for the specified user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On error:   { "success": False, "error": "User not found" }

        Constraints:
            - user_id must exist in self.users.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_session(self, session_id: str) -> dict:
        """
        Retrieve the user information associated with a valid, authenticated session ID.

        Args:
            session_id (str): The session identifier.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - session_id must exist in the system.
            - Only authenticated sessions ('authentication_status' == 'authenticated') are allowed.
            - The associated user must exist.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist"}

        if session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "Session is not authenticated"}

        user_id = session.get("user_id")
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Associated user does not exist"}

        return {"success": True, "data": user}

    def list_all_resources(self, session_id: str) -> dict:
        """
        List all resources (rooms, equipment, etc.) tracked by the system.

        Args:
            session_id (str): The session identifier of the requesting user.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[ResourceInfo]  # May be empty if no resources
                }
                or
                {
                    "success": False,
                    "error": str  # Reason: invalid session, not authenticated, etc.
                }

        Constraints:
            - Only authenticated users (active session, authentication_status == 'authenticated') can access resource details.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Invalid or expired session."}
        if session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User not authenticated."}

        resource_list = list(self.resources.values())
        return {"success": True, "data": resource_list}

    def list_available_resources(self, session_id: str) -> dict:
        """
        List all resources currently available for booking (filtered by availability_status).

        Args:
            session_id (str): The current user's session identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ResourceInfo],  # List may be empty if nothing available.
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (authentication/session issue)
                    }
             
        Constraints:
            - Only authenticated users (via valid session with 'authenticated' status) can list resources.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Invalid or expired session."}
        if session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User is not authenticated."}

        available_resources = [
            resource
            for resource in self.resources.values()
            if resource.get("availability_status") == "available"
        ]
        return {"success": True, "data": available_resources}

    def get_resource_by_id(self, session_id: str, resource_id: str) -> dict:
        """
        Retrieve the details of a resource by resource_id.

        Args:
            session_id (str): The session of the requesting user.
            resource_id (str): The ID of the resource to retrieve.

        Returns:
            dict:
              - If authenticated and resource exists:
                  {
                      "success": True,
                      "data": ResourceInfo
                  }
              - If session invalid or not authenticated:
                  {
                      "success": False,
                      "error": "User not authenticated"
                  }
              - If resource not found:
                  {
                      "success": False,
                      "error": "Resource not found"
                  }

        Constraints:
            - Only authenticated users can access resource details.
            - Session must exist and be authenticated.
        """
        # Check session
        session = self.sessions.get(session_id)
        if not session or session.get("authentication_status") != "authenticated":
            return { "success": False, "error": "User not authenticated" }

        resource = self.resources.get(resource_id)
        if not resource:
            return { "success": False, "error": "Resource not found" }

        return { "success": True, "data": resource }

    def list_all_events(self, session_id: str) -> dict:
        """
        Retrieve all scheduled events in the system.

        Args:
            session_id (str): The ID of the user session requesting the event list.
    
        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # List of all events (can be empty if none).
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not authenticated, invalid session, etc.)
            }

        Constraints:
            - Only authenticated users (with valid session and authentication_status == "authenticated") can access event details.
        """
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Invalid or expired session." }
        if session.get("authentication_status") != "authenticated":
            return { "success": False, "error": "User not authenticated." }

        event_list = list(self.events.values())
        return { "success": True, "data": event_list }

    def get_event_by_id(self, session_id: str, event_id: str) -> dict:
        """
        Retrieve all details of an event given its event_id. Only authenticated users can perform this operation.

        Args:
            session_id (str): The session identifier of the requesting user.
            event_id (str): The unique identifier of the target event.

        Returns:
            dict: On success:
                    { "success": True, "data": EventInfo }
                  On failure:
                    { "success": False, "error": "Event not found" | "User not authenticated" | "Invalid or expired session" }

        Constraints:
            - Only authenticated users (session with 'authentication_status' == 'authenticated') can access event details.
            - The event must exist (event_id in self.events).
        """
        session = self.sessions.get(session_id)
        if not session or session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User not authenticated"}

        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}

        return {"success": True, "data": event}

    def get_event_resources(self, event_id: str, session_id: str) -> dict:
        """
        Lists all resource information linked to the given event by resource_ids.

        Args:
            event_id (str): ID of the event to query.
            session_id (str): Session ID of the requesting user. Must be authenticated.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo]  # List of matched resources (may be empty if event has no resources)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (authentication required, not found, etc.)
            }

        Constraints:
            - Only authenticated users (authentication_status == 'authenticated') can use this.
            - Event must exist.
            - All referenced resource_ids in the event must exist.
        """
        # Session exist and authenticated check
        session = self.sessions.get(session_id)
        if not session or session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "Authentication required."}

        # Event exists
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found."}

        resource_infos = []
        for rid in event.get("resource_ids", []):
            resource = self.resources.get(rid)
            if not resource:
                # This should not happen if constraints are enforced elsewhere, but we check anyway
                return {"success": False, "error": f"Resource '{rid}' not found for this event."}
            resource_infos.append(resource)

        return {"success": True, "data": resource_infos}

    def get_active_session_by_user(self, user_id: str) -> dict:
        """
        Retrieve the active session (if any) for a user_id.

        Args:
            user_id (str): The ID of the user for whom to find an active session.

        Returns:
            dict: {
                "success": True,
                "data": SessionInfo  # The user's active session data
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - The user must exist.
            - A session is "active" if authentication_status is "active" or "authenticated".
            - Each session is associated with exactly one user.
            - If multiple active sessions exist, return the one with the latest last_active timestamp.
        """

        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Consider a session active if authentication_status is "active" or "authenticated"
        active_sessions = [
            session for session in self.sessions.values()
            if session["user_id"] == user_id and session["authentication_status"] in ("active", "authenticated")
        ]

        if not active_sessions:
            return {"success": False, "error": "No active session for this user"}

        # If several, pick the one with the latest last_active timestamp (lexicographically for ISO 8601 string)
        active_sessions.sort(key=lambda s: s["last_active"], reverse=True)
        return {"success": True, "data": active_sessions[0]}

    def get_session_info(self, session_id: str) -> dict:
        """
        Retrieve session details by session_id.

        Args:
            session_id (str): The unique session identifier to look up.

        Returns:
            dict: 
                { "success": True, "data": SessionInfo } if session is found
                { "success": False, "error": "Session not found" } if no such session exists

        Constraints:
            - Only looks up by provided session_id; does not check active/expired/authenticated status.
        """
        session_info = self.sessions.get(session_id)
        if session_info is None:
            return { "success": False, "error": "Session not found" }
        return { "success": True, "data": session_info }

    def create_event(
        self,
        session_id: str,
        title: str,
        description: str,
        start_time: str,
        end_time: str,
        location: str,
        organizer_id: str,
        resource_ids: List[str],
        participants: List[str]
    ) -> dict:
        """
        Schedule a new event, referencing resources and participants.
        Ensures:
          - Only authenticated users (session_id) can create,
          - All resource_ids exist,
          - Organizer and participants are valid user_ids.

        Args:
            session_id (str): Calling user's session token (must be authenticated)
            title (str): Event title
            description (str): Event description
            start_time (str): Event start time (ISO string)
            end_time (str): Event end time (ISO string)
            location (str): Event location string
            organizer_id (str): User ID creating event
            resource_ids (List[str]): List of resource IDs to link
            participants (List[str]): List of user IDs as event participants

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Event created", "event_id": <new_event_id> }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Only authenticated users (session_id with authentication_status=="authenticated") may create.
            - All resource_ids must exist.
            - Organizer and participants user_ids must exist.
        """
        # Check session authentication
        session = self.sessions.get(session_id)
        if session is None or session["authentication_status"] != "authenticated":
            return { "success": False, "error": "User not authenticated or session invalid." }

        # Organizer validity
        if organizer_id not in self.users:
            return { "success": False, "error": "Invalid organizer_id." }

        # Participants validity
        invalid_participants = [uid for uid in participants if uid not in self.users]
        if invalid_participants:
            return { "success": False, "error": f"Invalid participant user_ids: {invalid_participants}" }

        # Resource validity
        invalid_resources = [rid for rid in resource_ids if rid not in self.resources]
        if invalid_resources:
            return { "success": False, "error": f"Invalid resource_ids: {invalid_resources}" }
        blocked_resources = [rid for rid in resource_ids if not self._resource_can_be_assigned(rid)]
        if blocked_resources:
            return { "success": False, "error": f"Resources are not available for assignment: {blocked_resources}" }

        # Generate unique event_id (simple increment or UUID)
        event_id = str(uuid.uuid4())

        # Construct event info
        event_info: EventInfo = {
            "event_id": event_id,
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "organizer_id": organizer_id,
            "resource_ids": resource_ids,
            "participants": participants,
        }

        # Add event to system
        self.events[event_id] = event_info
        for resource_id in resource_ids:
            self._mark_resource_booked(resource_id)

        return { "success": True, "message": "Event created", "event_id": event_id }

    def book_resource(self, resource_id: str, session_id: str, start_time: str, end_time: str) -> dict:
        """
        Books a resource (sets its status to 'booked') for a specific time interval if it is available,
        and the requesting user is authenticated.

        Args:
            resource_id (str): The ID of the resource to book.
            session_id (str): The session of the requesting user (must be active and authenticated).
            start_time (str): Booking interval start time (string).
            end_time (str): Booking interval end time (string).

        Returns:
            dict: 
                On success:
                    {'success': True, 'message': "Resource <id> has been booked from <start> to <end>."}
                On failure:
                    {'success': False, 'error': "<reason>"}

        Constraints:
            - Only authenticated users can perform bookings.
            - Resource must exist and be available (availability_status == 'available').
            - Session must be valid and authenticated.
            - No resource double-booking (simple availability_status).
        """
        # Check session validity and authentication
        session = self.sessions.get(session_id)
        if not session or session["authentication_status"] != "authenticated":
            return {"success": False, "error": "Session is not valid or user not authenticated."}

        # Check resource existence
        resource = self.resources.get(resource_id)
        if not resource:
            return {"success": False, "error": "Resource does not exist."}

        # Check resource availability
        if resource.get("availability_status") != "available":
            return {"success": False, "error": "Resource is not available for booking."}

        # Input validation for start_time/end_time (not parsed, just ensure not empty)
        if not start_time or not end_time:
            return {"success": False, "error": "Start time and end time are required."}

        # Book the resource (set status)
        resource["availability_status"] = "booked"

        # Resource status updated, reflecting new reservation. (No explicit reservation log here.)
        return {
            "success": True,
            "message": f"Resource {resource_id} has been booked from {start_time} to {end_time}."
        }

    def release_resource(self, resource_id: str) -> dict:
        """
        Mark a resource as 'available' after event completion or cancellation.

        Args:
            resource_id (str): The unique identifier of the resource to release.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Resource <resource_id> released and marked as available." }
              - On failure: { "success": False, "error": "Resource not found." }

        Constraints:
            - The resource must exist in the system.
            - The resource's availability_status will be set to 'available' upon success.
        """
        resource = self.resources.get(resource_id)
        if not resource:
            return { "success": False, "error": "Resource not found." }

        resource["availability_status"] = "available"
        return { "success": True, "message": f"Resource {resource_id} released and marked as available." }

    def update_resource_status(self, resource_id: str, new_status: str) -> dict:
        """
        Change a resource's availability_status to a new value.

        Args:
            resource_id (str): The unique identifier of the resource to update.
            new_status (str): The new availability_status (e.g., 'available', 'booked', 'maintenance', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Resource availability_status updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # reason for failure, e.g. resource_id does not exist
            }

        Constraints:
            - resource_id must exist.
            - No explicit status value validation or permission checks are implemented unless specified elsewhere.
            - Should ideally reflect booking status, but operation allows manual updating.
        """
        resource = self.resources.get(resource_id)
        if not resource:
            return {"success": False, "error": "Resource does not exist."}

        resource["availability_status"] = new_status
        return {"success": True, "message": "Resource availability_status updated successfully."}

    def expire_session(self, session_id: str) -> dict:
        """
        Expire a session due to inactivity or logout.
        Updates the session's authentication_status to 'expired'.

        Args:
            session_id (str): The ID of the session to expire.

        Returns:
            dict: {
                "success": True,
                "message": "Session expired successfully."
            }
            or
            {
                "success": False,
                "error": "Session does not exist."
            }

        Constraints:
            - session_id must exist in the system.
            - This operation is idempotent (expiring an already expired session has no adverse effect).
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session does not exist."}

        self.sessions[session_id]["authentication_status"] = "expired"
        return {"success": True, "message": "Session expired successfully."}

    def add_participant_to_event(self, session_id: str, event_id: str, user_id: str) -> dict:
        """
        Add a user (user_id) as a participant to an event (event_id).

        Args:
            session_id (str): Current session—must be authenticated.
            event_id (str): Event to which the participant is added.
            user_id (str): User to be added as a participant.

        Returns:
            dict:
                Success: { "success": True, "message": "<user> added as participant to <event>" }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - Only authenticated users (session) may perform this operation.
            - Event and user must exist.
            - User must not already be a participant of the event.
        """
        # Check session validity
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Invalid session." }
        if session["authentication_status"] != "authenticated":
            return { "success": False, "error": "User not authenticated." }

        # Check event
        event = self.events.get(event_id)
        if not event:
            return { "success": False, "error": "Event does not exist." }

        # Check user
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        # Check if user already a participant
        if user_id in event["participants"]:
            return { "success": False, "error": "User is already a participant in this event." }

        # Add participant
        event["participants"].append(user_id)

        return { "success": True, "message": f"User {user_id} added as a participant to event {event_id}." }

    def remove_participant_from_event(self, event_id: str, user_id: str) -> dict:
        """
        Remove a user (user_id) as a participant from an event (event_id).

        Args:
            event_id (str): The unique identifier of the event.
            user_id (str): The unique identifier of the user to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "User removed from event participants." }
                On failure: { "success": False, "error": str }

        Constraints:
            - The event must exist.
            - The user must exist.
            - The user must be a participant of the event.
        """
        # Check if event exists
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        event = self.events[event_id]
        # Check if user is a participant
        if user_id not in event["participants"]:
            return { "success": False, "error": "User is not a participant of the event." }
        # Remove user from participants
        event["participants"].remove(user_id)
        return { "success": True, "message": "User removed from event participants." }

    def update_event(
        self, 
        session_id: str, 
        event_id: str, 
        title: str = None, 
        description: str = None,
        start_time: str = None,
        end_time: str = None,
        location: str = None,
        organizer_id: str = None,
        resource_ids: List[str] = None,
        participants: List[str] = None
    ) -> dict:
        """
        Update an event's details. Only authenticated users may update an event.
        Only fields specified are updated; others remain unchanged.

        Args:
            session_id (str): Session identifier for authentication.
            event_id (str): Identifier of the event to update.
            title (str): New title for the event (optional).
            description (str): New description (optional).
            start_time (str): Updated start time (optional).
            end_time (str): Updated end time (optional).
            location (str): Updated location (optional).
            organizer_id (str): Updated organizer (optional).
            resource_ids (List[str]): Updated list of linked resources (optional).
            participants (List[str]): Updated list of participants (optional).

        Returns:
            dict: 
                On success: { "success": True, "message": "Event updated successfully." }
                On error: { "success": False, "error": "reason" }

        Constraints:
            - Only authenticated users can update events.
            - resource_ids (if updated) must reference valid resources.
            - Event must exist.
        """
        # Check session
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist."}
        if session.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User not authenticated."}
    
        # Check event
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event does not exist."}

        old_resource_ids = event.get("resource_ids", []).copy()

        # Validate resource_ids if provided
        if resource_ids is not None:
            for r_id in resource_ids:
                if r_id not in self.resources:
                    return {"success": False, "error": f"Resource {r_id} does not exist."}
                if not self._resource_can_be_assigned(r_id, excluding_event_id=event_id):
                    return {"success": False, "error": f"Resource {r_id} is not available for assignment."}

        # Update fields if provided
        if title is not None:
            event["title"] = title
        if description is not None:
            event["description"] = description
        if start_time is not None:
            event["start_time"] = start_time
        if end_time is not None:
            event["end_time"] = end_time
        if location is not None:
            event["location"] = location
        if organizer_id is not None:
            event["organizer_id"] = organizer_id
        if resource_ids is not None:
            event["resource_ids"] = resource_ids.copy()
        if participants is not None:
            event["participants"] = participants.copy()

        if resource_ids is not None:
            new_resource_ids = event.get("resource_ids", [])
            for resource_id in old_resource_ids:
                if resource_id not in new_resource_ids:
                    self._release_resource_if_unused(resource_id)
            for resource_id in new_resource_ids:
                self._mark_resource_booked(resource_id)
    
        return {"success": True, "message": "Event updated successfully."}

    def cancel_event(self, session_id: str, event_id: str) -> dict:
        """
        Cancel a scheduled event and release all associated resources.

        Args:
            session_id (str): The current user's session for authentication.
            event_id (str): The identifier for the event to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Event canceled and resources released."
            }
            or
            dict: {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Only authenticated sessions may cancel events.
            - All resources associated with the event are released (availability_status updated to 'available').
            - Event must exist.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found."}
        if session["authentication_status"] != "authenticated":
            return {"success": False, "error": "User is not authenticated."}
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found."}

        resource_ids = event.get("resource_ids", []).copy()

        # Remove the event first so release checks observe the post-cancellation state.
        self.events.pop(event_id)

        freed_resources = []
        for resource_id in resource_ids:
            resource = self.resources.get(resource_id)
            if resource:
                before_status = resource.get("availability_status")
                self._release_resource_if_unused(resource_id)
                if before_status == "booked" and resource.get("availability_status") == "available":
                    freed_resources.append(resource_id)

        return {
            "success": True,
            "message": f"Event canceled and resources released: {', '.join(freed_resources) if freed_resources else 'none'}."
        }


class EventSchedulingAndResourceBookingSystem(BaseEnv):
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

    def check_authentication_status(self, **kwargs):
        return self._call_inner_tool('check_authentication_status', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_session(self, **kwargs):
        return self._call_inner_tool('get_user_by_session', kwargs)

    def list_all_resources(self, **kwargs):
        return self._call_inner_tool('list_all_resources', kwargs)

    def list_available_resources(self, **kwargs):
        return self._call_inner_tool('list_available_resources', kwargs)

    def get_resource_by_id(self, **kwargs):
        return self._call_inner_tool('get_resource_by_id', kwargs)

    def list_all_events(self, **kwargs):
        return self._call_inner_tool('list_all_events', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def get_event_resources(self, **kwargs):
        return self._call_inner_tool('get_event_resources', kwargs)

    def get_active_session_by_user(self, **kwargs):
        return self._call_inner_tool('get_active_session_by_user', kwargs)

    def get_session_info(self, **kwargs):
        return self._call_inner_tool('get_session_info', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def book_resource(self, **kwargs):
        return self._call_inner_tool('book_resource', kwargs)

    def release_resource(self, **kwargs):
        return self._call_inner_tool('release_resource', kwargs)

    def update_resource_status(self, **kwargs):
        return self._call_inner_tool('update_resource_status', kwargs)

    def expire_session(self, **kwargs):
        return self._call_inner_tool('expire_session', kwargs)

    def add_participant_to_event(self, **kwargs):
        return self._call_inner_tool('add_participant_to_event', kwargs)

    def remove_participant_from_event(self, **kwargs):
        return self._call_inner_tool('remove_participant_from_event', kwargs)

    def update_event(self, **kwargs):
        return self._call_inner_tool('update_event', kwargs)

    def cancel_event(self, **kwargs):
        return self._call_inner_tool('cancel_event', kwargs)
