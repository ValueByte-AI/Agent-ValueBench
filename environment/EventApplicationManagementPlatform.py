# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
from datetime import datetime



# --- TypedDict definitions ---

class EventInfo(TypedDict):
    event_id: str
    title: str
    description: str
    location: str
    start_datetime: str
    end_datetime: str
    organizer_id: str
    participants: List[str]
    status: str

class ApplicationInfo(TypedDict):
    app_id: str
    name: str
    owner_id: str
    status: str
    creation_datetime: str

class ReportInfo(TypedDict):
    report_id: str
    app_id: str  # references Application.app_id
    content: str
    archive_status: str
    created_datetime: str
    archived_datetime: Optional[str]  # can be None if not archived

class FormInfo(TypedDict):
    form_id: str
    creator_id: str
    created_datetime: str
    linked_event_id: Optional[str]
    linked_app_id: Optional[str]
    status: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    email: str
    role: str
    active_status: str

# --- Environment class ---

class _GeneratedEnvImpl:
    def __init__(self):
        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}
        # Applications: {app_id: ApplicationInfo}
        self.applications: Dict[str, ApplicationInfo] = {}
        # Reports: {report_id: ReportInfo}
        self.reports: Dict[str, ReportInfo] = {}
        # Forms: {form_id: FormInfo}
        self.forms: Dict[str, FormInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each entity must have a unique identifier (event_id, app_id, etc.)
        # - Only reports with archive_status == "archived" are considered for 'last archived report' queries
        # - Form count is based on total records in the Form entity up to the current timestamp
        # - Relationships (e.g., Report.app_id references Application.app_id) must be preserved for queries
        # - Users may only access events, apps, and reports they are authorized to view

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the full details of an event given its unique event_id.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": EventInfo  # Full details of the event
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., event not found
                    }

        Constraints:
            - The event_id must exist in the system.
            - (No user authorization enforced due to lack of user/session context.)
        """
        event = self.events.get(event_id)
        if event is None:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def list_events_by_user(self, user_id: str) -> dict:
        """
        List events that a given user is authorized to view or is participating in.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist and be active.
            - Only events where user is organizer or a participant are considered "authorized".
        """
        user_info = self.users.get(user_id)
        if user_info is None or user_info.get("active_status") != "active":
            return { "success": False, "error": "User not found or not active" }

        events_list = [
            event_info for event_info in self.events.values()
            if (event_info["organizer_id"] == user_id or user_id in event_info["participants"])
        ]

        return { "success": True, "data": events_list }

    def get_application_by_id(self, app_id: str) -> dict:
        """
        Retrieve application details using the unique app_id.

        Args:
            app_id (str): The identifier for the application.

        Returns:
            dict:
                - On success: {"success": True, "data": ApplicationInfo}
                - On failure: {"success": False, "error": "Application does not exist"}

        Constraints:
            - app_id must exist in self.applications.
        """
        app_info = self.applications.get(app_id)
        if app_info is None:
            return {"success": False, "error": "Application does not exist"}
        return {"success": True, "data": app_info}

    def list_applications_by_user(self, user_id: str) -> dict:
        """
        List all applications owned by a given user.

        Args:
            user_id (str): The user ID to list applications for.

        Returns:
            dict:
                - If user is found: { "success": True, "data": List[ApplicationInfo] }
                - If user not found: { "success": False, "error": str }

        Constraints:
            - User ID must exist.
            - Returns only applications for which owner_id == user_id (ownership is used for access).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        user_applications = [
            app for app in self.applications.values()
            if app["owner_id"] == user_id
        ]
        return { "success": True, "data": user_applications }

    def get_report_by_id(self, report_id: str, user_id: str = None) -> dict:
        """
        Retrieve full details of a report given its report_id.
    
        Args:
            report_id (str): Unique ID of the report.
            user_id (str, optional): If provided, checks if the user is authorized to access the report.
    
        Returns:
            dict: {
                "success": True,
                "data": ReportInfo,
            }
            or
            {
                "success": False,
                "error": <reason>,
            }
    
        Constraints:
            - report_id must exist in the reports.
            - If user_id is provided, user must have access to this report ("Users may only access ...").
        """
        # Check existence
        report = self.reports.get(report_id)
        if report is None:
            return {"success": False, "error": "Report not found"}

        # Access control
        if user_id is not None:
            # Assume existence of access checker
            if not hasattr(self, 'check_user_access_to_entity'):
                return {"success": False, "error": "Access control not implemented"}
            access = self.check_user_access_to_entity(entity_type="report", entity_id=report_id, user_id=user_id)
            if not (
                isinstance(access, dict)
                and access.get("success")
                and access.get("authorized") is True
            ):
                return {"success": False, "error": "Access denied"}

        return {"success": True, "data": report}

    def list_reports_by_app_id(self, app_id: str) -> dict:
        """
        List all reports associated with a specific application by app_id.

        Args:
            app_id (str): The application ID for which to list reports.

        Returns:
            dict: {
                "success": True,
                "data": List[ReportInfo],  # All reports with specified app_id (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g., application does not exist)
            }

        Constraints:
            - app_id must exist in the system.
            - Only return reports where report["app_id"] == app_id.
        """
        if app_id not in self.applications:
            return {"success": False, "error": "Application does not exist"}

        reports = [
            report for report in self.reports.values()
            if report["app_id"] == app_id
        ]

        return {"success": True, "data": reports}

    def get_last_archived_report_by_app_id(self, app_id: str) -> dict:
        """
        Retrieve the most recently archived report for a given app_id.

        Args:
            app_id (str): The application ID whose archived reports are to be checked.

        Returns:
            dict:
                {
                    "success": True,
                    "data": ReportInfo  # The most recently archived report (full metadata)
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g. app_id not found or no archived report
                }

        Constraints:
            - Only reports with archive_status == "archived" are considered.
            - archived_datetime must not be None.
            - Report.app_id must reference an existing application.
        """
        if app_id not in self.applications:
            return { "success": False, "error": "Application does not exist" }

        # Find archived reports for this app_id
        archived_reports = [
            r for r in self.reports.values()
            if r["app_id"] == app_id and r["archive_status"] == "archived" and r["archived_datetime"] is not None
        ]
        if not archived_reports:
            return { "success": False, "error": "No archived report found for this app_id" }

        # Find the report with the latest archived_datetime
        latest_report = max(
            archived_reports,
            key=lambda r: r["archived_datetime"]
        )

        return { "success": True, "data": latest_report }

    def count_forms(self) -> dict:
        """
        Return the total number of forms created up to the current timestamp.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": int  # count of forms
            }

        Constraints:
            - Includes all forms present in the self.forms dictionary (no filtering).
        """
        total_forms = len(self.forms)
        return {"success": True, "data": total_forms}

    def get_form_by_id(self, form_id: str) -> dict:
        """
        Retrieve the details of a form by its unique form_id.

        Args:
            form_id (str): The unique identifier for the form.

        Returns:
            dict: {
                "success": True,
                "data": FormInfo  # Form details
            }
            or
            {
                "success": False,
                "error": "Form not found."
            }

        Constraints:
            - The form_id must exist in the platform's forms records.
        """
        if form_id not in self.forms:
            return { "success": False, "error": "Form not found." }

        return { "success": True, "data": self.forms[form_id] }

    def list_forms_by_creator(self, user_id: str) -> dict:
        """
        List all forms created by a specific user.

        Args:
            user_id (str): The user ID of the creator.

        Returns:
            dict: 
                - success: True, data: List[FormInfo] (may be empty if no forms)
                - success: False, error: str (if user does not exist or is inactive)

        Constraints:
            - User must exist in the system.
            - Only forms authored by the given user are listed.
            - If user is not active_status == "active", returns error.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }

        if user.get("active_status", "").lower() != "active":
            return { "success": False, "error": "User is not active" }

        matched_forms = [
            form_info for form_info in self.forms.values()
            if form_info.get("creator_id") == user_id
        ]

        return { "success": True, "data": matched_forms }

    def list_forms_by_event(self, event_id: str) -> dict:
        """
        List all forms linked to a specific event_id.

        Args:
            event_id (str): The unique ID of the event.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[FormInfo]  # List of forms linked to the event (empty if none)
                }
                OR
                {
                    "success": False,
                    "error": "Event does not exist"
                }

        Constraints:
            - event_id must refer to an existing event in the platform.
            - Only forms with linked_event_id exactly matching event_id are included.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        forms_linked = [
            form for form in self.forms.values()
            if form.get("linked_event_id") == event_id
        ]
        return {"success": True, "data": forms_linked}

    def list_forms_by_app(self, app_id: str) -> dict:
        """
        List all forms linked to a specific application (by app_id).

        Args:
            app_id (str): The application identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[FormInfo],  # All forms whose linked_app_id matches app_id
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. application does not exist)
            }

        Constraints:
            - app_id must exist in the platform (in self.applications).
            - Only forms with exactly linked_app_id == app_id are returned.
        """
        if app_id not in self.applications:
            return { "success": False, "error": "Application does not exist" }
    
        linked_forms = [
            form for form in self.forms.values()
            if form.get("linked_app_id") == app_id
        ]
        return {"success": True, "data": linked_forms}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user profile and status details by user_id.

        Args:
            user_id (str): The unique identifier of the user to retrieve.

        Returns:
            dict:
                - On success: {"success": True, "data": UserInfo}
                - On failure: {"success": False, "error": "User not found"}

        Constraints:
            - user_id must exist in the platform.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def check_user_access_to_entity(self, user_id: str, entity_type: str, entity_id: str) -> dict:
        """
        Verify whether a user is authorized to access a specific event, application, or report.

        Args:
            user_id (str): The user's unique identifier.
            entity_type (str): One of 'event', 'application', or 'report'.
            entity_id (str): The unique identifier for the target entity.

        Returns:
            dict: {
                "success": True,
                "authorized": True/False  # Whether the user is authorized
            }
            or
            {
                "success": False,
                "error": str  # Description of any error (e.g., unknown user or entity)
            }

        Constraints:
            - The user must exist and have active_status='active'.
            - Only authorized users (per entity rules) may access the entity:
                - Admins may access any entity.
                - Events: user is organizer or is listed as a participant.
                - Applications: user is owner.
                - Reports: user is owner of related application.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        if user_info["active_status"] != "active":
            return { "success": False, "error": "User is not active" }

        # Admins can access any entity
        if user_info["role"] == "admin":
            return { "success": True, "authorized": True }

        entity_type = entity_type.lower()
        if entity_type == "event":
            event = self.events.get(entity_id)
            if event is None:
                return { "success": False, "error": "Event not found" }
            if (user_id == event["organizer_id"]) or (user_id in event["participants"]):
                return { "success": True, "authorized": True }
            else:
                return { "success": True, "authorized": False }
        elif entity_type == "application":
            app = self.applications.get(entity_id)
            if app is None:
                return { "success": False, "error": "Application not found" }
            if user_id == app["owner_id"]:
                return { "success": True, "authorized": True }
            else:
                return { "success": True, "authorized": False }
        elif entity_type == "report":
            report = self.reports.get(entity_id)
            if report is None:
                return { "success": False, "error": "Report not found" }
            app_id = report["app_id"]
            app = self.applications.get(app_id)
            if app is None:
                return { "success": False, "error": "Related application not found" }
            if user_id == app["owner_id"]:
                return { "success": True, "authorized": True }
            else:
                return { "success": True, "authorized": False }
        else:
            return { "success": False, "error": "Unknown entity type" }

    def count_entities(self, entity_type: str) -> dict:
        """
        Counts the number of instances for a specified entity type.

        Args:
            entity_type (str): The type of entity to count ("Event", "Application", "Report", "Form").

        Returns:
            dict: { "success": True, "data": int } on success (with count as data),
                  { "success": False, "error": str } on error (if entity_type is unsupported).

        Constraints:
            - entity_type must be one of: "Event", "Application", "Report", "Form" (case-insensitive).
        """
        entity_map = {
            "event": self.events,
            "application": self.applications,
            "report": self.reports,
            "form": self.forms
        }
        etype = entity_type.strip().lower()
        if etype not in entity_map:
            return { "success": False, "error": f"Unsupported entity_type: {entity_type}" }
        count = len(entity_map[etype])
        return { "success": True, "data": count }

    def create_event(
        self,
        event_id: str,
        title: str,
        description: str,
        location: str,
        start_datetime: str,
        end_datetime: str,
        organizer_id: str,
        participants: list,
        status: str
    ) -> dict:
        """
        Add a new event record with all required fields and unique event_id.
    
        Args:
            event_id (str): Unique identifier for the event.
            title (str)
            description (str)
            location (str)
            start_datetime (str)
            end_datetime (str)
            organizer_id (str): User ID of the organizer (must exist).
            participants (List[str]): List of user_ids.
            status (str)
        
        Returns:
            dict:
              - { "success": True, "message": "Event created successfully." }
              - { "success": False, "error": "..." }
    
        Constraints:
          - event_id must be unique.
          - organizer_id must correspond to a known user.
          - Participants that do not exist are filtered out.
        """
        # Check for event_id uniqueness
        if event_id in self.events:
            return { "success": False, "error": "Event ID already exists." }

        # Check for required fields (all fields are required and should be non-empty for strings)
        required_fields = [
            ('event_id', event_id),
            ('title', title),
            ('description', description),
            ('location', location),
            ('start_datetime', start_datetime),
            ('end_datetime', end_datetime),
            ('organizer_id', organizer_id),
            ('participants', participants),
            ('status', status)
        ]
        for field, val in required_fields:
            if val is None or (isinstance(val, str) and val.strip() == ''):
                return { "success": False, "error": f"Missing required field: {field}" }

        # organizer_id must exist
        if organizer_id not in self.users:
            return { "success": False, "error": "Organizer user not found." }

        # Ensure participants is a list and filter for users that exist
        if not isinstance(participants, list):
            return { "success": False, "error": "Participants must be a list of user_ids." }
        valid_participants = [uid for uid in participants if uid in self.users]

        # Prepare event record
        new_event = {
            "event_id": event_id,
            "title": title,
            "description": description,
            "location": location,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "organizer_id": organizer_id,
            "participants": valid_participants,
            "status": status
        }
        self.events[event_id] = new_event

        return { "success": True, "message": "Event created successfully." }

    def update_event(self, event_id: str, updates: dict, user_id: str = None) -> dict:
        """
        Modify the details of an existing event.

        Args:
            event_id (str): Identifier of the event to update.
            updates (dict): Keys and new values for fields to update. (Must be valid EventInfo fields except 'event_id')
            user_id (str, optional): The user requesting the update. Used for permission checking.

        Returns:
            dict: {
                "success": True,
                "message": "Event updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Event must exist.
            - Only valid (mutable) EventInfo fields may be changed (not 'event_id').
            - User must be authorized to update this event (if user_id provided); authorized if user is event's organizer or is admin.
            - Data types should match expected types.
        """
        # 1. Check if event exists
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        event = self.events[event_id]

        # 2. Authorization check if user_id is given
        if user_id is not None:
            user = self.users.get(user_id)
            if not user or user.get("active_status", "") != "active":
                return {"success": False, "error": "Invalid or inactive user"}
            # Allow if organizer or admin
            if user_id != event["organizer_id"] and user.get("role") != "admin":
                return {"success": False, "error": "User is not authorized to update this event"}

        # 3. Immutable fields
        IMMUTABLE_FIELDS = {"event_id"}
        # Valid EventInfo fields
        VALID_FIELDS = set(event.keys()) - IMMUTABLE_FIELDS

        # 4. Check for invalid or immutable fields
        for field in updates:
            if field in IMMUTABLE_FIELDS:
                return {"success": False, "error": f"Field '{field}' cannot be updated"}
            if field not in VALID_FIELDS:
                return {"success": False, "error": f"Field '{field}' is not a valid Event field"}

        # 5. Data type and value checks
        # Optionally, type-check as per EventInfo, for now basic checks for participants as list
        if "participants" in updates and not isinstance(updates["participants"], list):
            return {"success": False, "error": "'participants' must be a list of user ids"}

        # 6. If no updates, treat as no-op
        if not updates:
            return {"success": False, "error": "No fields provided to update"}

        # 7. Apply updates
        for field, value in updates.items():
            event[field] = value

        # 8. Commit to self.events
        self.events[event_id] = event

        return {"success": True, "message": "Event updated successfully"}


    def archive_report(self, report_id: str) -> dict:
        """
        Mark a report's archive_status as 'archived' and set archived_datetime.

        Args:
            report_id (str): The unique identifier of the report to archive.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Report <report_id> archived successfully"
                  }
                - On failure: {
                    "success": False,
                    "error": "<reason>"
                  }

        Constraints:
            - The report must exist.
            - If already archived, operation is idempotent; archived_datetime will be updated to current time.
            - archived_datetime is set to current ISO 8601 timestamp.
        """
        report = self.reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report does not exist"}
    
        # Mark as archived regardless of previous state (idempotent)
        report['archive_status'] = 'archived'
        report['archived_datetime'] = datetime.utcnow().isoformat() + "Z"

        return {"success": True, "message": f"Report {report_id} archived successfully"}

    def create_report(
        self,
        report_id: str,
        app_id: str,
        content: str,
        archive_status: str,
        created_datetime: str,
        archived_datetime: Optional[str] = None
    ) -> dict:
        """
        Add a new report linked to an existing application.

        Args:
            report_id (str): Unique identifier for the new report.
            app_id (str): Must reference an existing application.
            content (str): The report content.
            archive_status (str): Initial report status ("active" or "archived").
            created_datetime (str): ISO-8601 creation timestamp.
            archived_datetime (Optional[str]): Set only if archive_status is "archived".

        Returns:
            dict:
                - success (bool): True if created, False otherwise.
                - message (str): Description if successful.
                - error (str): Description if failed.

        Constraints:
            - report_id must be unique.
            - app_id must exist in self.applications.
            - archive_status must be "active" or "archived".
            - archived_datetime must be set if status is "archived", None otherwise.
            - Relationships must be preserved.
        """
        # Check unique report_id
        if report_id in self.reports:
            return { "success": False, "error": "Report ID already exists." }

        # Check valid app_id
        if app_id not in self.applications:
            return { "success": False, "error": "Referenced application ID does not exist." }

        # Validate archive_status
        if archive_status not in ("active", "archived"):
            return { "success": False, "error": "Invalid archive status. Must be 'active' or 'archived'." }

        # Validate archived_datetime logic
        if archive_status == "archived":
            if archived_datetime is None:
                return { "success": False, "error": "Archived datetime must be provided if status is 'archived'." }
        else:  # archive_status == "active"
            archived_datetime = None

        # Create ReportInfo object
        report_info = {
            "report_id": report_id,
            "app_id": app_id,
            "content": content,
            "archive_status": archive_status,
            "created_datetime": created_datetime,
            "archived_datetime": archived_datetime,
        }

        self.reports[report_id] = report_info

        return { "success": True, "message": "Report created successfully." }

    def update_report(
        self,
        report_id: str,
        content: str = None,
        archive_status: str = None,
        archived_datetime: str = None,
        app_id: str = None
    ) -> dict:
        """
        Edit the content or metadata of an existing report.

        Args:
            report_id (str): ID of the report to update.
            content (str, optional): New content for the report.
            archive_status (str, optional): New archive status ("archived", "active", etc.).
            archived_datetime (str, optional): Archive datetime (should be set if status is "archived").
            app_id (str, optional): Change the associated application (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Report updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - report_id must exist.
            - If changing app_id, it must exist in applications.
            - Only actually provided fields are updated.
        """

        if report_id not in self.reports:
            return {"success": False, "error": "Report not found."}

        report = self.reports[report_id]
        changes = 0

        if content is not None:
            report["content"] = content
            changes += 1

        if archive_status is not None:
            report["archive_status"] = archive_status
            changes += 1
            # If status is "archived" and no datetime provided, set archived_datetime to now.
            if archive_status == "archived" and archived_datetime is None:
                report["archived_datetime"] = datetime.utcnow().isoformat() + "Z"
            elif archive_status != "archived":
                # If removed from archive, clear archived_datetime
                report["archived_datetime"] = None

        if archived_datetime is not None:
            report["archived_datetime"] = archived_datetime
            changes += 1

        if app_id is not None:
            if app_id not in self.applications:
                return {"success": False, "error": "Application ID does not exist."}
            report["app_id"] = app_id
            changes += 1

        if changes == 0:
            return {"success": True, "message": "No changes made to the report."}

        self.reports[report_id] = report
        return {"success": True, "message": "Report updated successfully"}

    def create_form(
        self,
        form_id: str,
        creator_id: str,
        created_datetime: str,
        status: str,
        linked_event_id: Optional[str] = None,
        linked_app_id: Optional[str] = None
    ) -> dict:
        """
        Add a new form to the platform, possibly linking it to an event or application.
        Args:
            form_id (str): Unique identifier for the form.
            creator_id (str): The user_id of the creator.
            created_datetime (str): The creation timestamp (ISO8601 or similar string).
            status (str): The form status.
            linked_event_id (Optional[str]): An event_id to link (if any; must exist if given).
            linked_app_id (Optional[str]): An app_id to link (if any; must exist if given).

        Returns:
            dict: {
                "success": True,
                "message": "Form created successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - form_id must be unique
            - creator_id must exist and be active
            - linked_event_id (if not None) must exist
            - linked_app_id (if not None) must exist
        """
        # Check for unique form_id
        if form_id in self.forms:
            return {"success": False, "error": "Form ID already exists"}
        # Check that creator exists and is active
        user_info = self.users.get(creator_id)
        if not user_info:
            return {"success": False, "error": "Creator user does not exist"}
        if user_info.get("active_status") != "active":
            return {"success": False, "error": "Creator user is not active"}
        # Check linked_event_id if provided
        if linked_event_id is not None and linked_event_id not in self.events:
            return {"success": False, "error": "Linked event does not exist"}
        # Check linked_app_id if provided
        if linked_app_id is not None and linked_app_id not in self.applications:
            return {"success": False, "error": "Linked application does not exist"}
        # Add form
        self.forms[form_id] = {
            "form_id": form_id,
            "creator_id": creator_id,
            "created_datetime": created_datetime,
            "linked_event_id": linked_event_id,
            "linked_app_id": linked_app_id,
            "status": status
        }
        return {"success": True, "message": "Form created successfully."}

    def update_form(
        self,
        form_id: str,
        status: str = None,
        linked_event_id: str = None,
        linked_app_id: str = None
    ) -> dict:
        """
        Modify a form's content, status, or linked entity references.

        Args:
            form_id (str): The unique identifier of the form to update.
            status (str, optional): New status for the form.
            linked_event_id (str, optional): Reference to a new (or cleared) event.
            linked_app_id (str, optional): Reference to a new (or cleared) application.

        Returns:
            dict: Success or failure payload:
                { "success": True, "message": "Form updated successfully." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - form_id must exist.
            - linked_event_id (if given and not None) must reference an existing event.
            - linked_app_id (if given and not None) must reference an existing application.
            - No effect and success if nothing to update.
        """
        # Check if form exists
        if form_id not in self.forms:
            return { "success": False, "error": "Form does not exist." }
        form = self.forms[form_id]
        updated = False

        # Validate linked_event_id if provided (and not clearing)
        if linked_event_id is not None:
            if linked_event_id != "":
                if linked_event_id not in self.events:
                    return { "success": False, "error": "Linked event does not exist." }
                if form["linked_event_id"] != linked_event_id:
                    form["linked_event_id"] = linked_event_id
                    updated = True
            else:
                if form["linked_event_id"] is not None:
                    form["linked_event_id"] = None
                    updated = True

        # Validate linked_app_id if provided (and not clearing)
        if linked_app_id is not None:
            if linked_app_id != "":
                if linked_app_id not in self.applications:
                    return { "success": False, "error": "Linked application does not exist." }
                if form["linked_app_id"] != linked_app_id:
                    form["linked_app_id"] = linked_app_id
                    updated = True
            else:
                if form["linked_app_id"] is not None:
                    form["linked_app_id"] = None
                    updated = True

        # Update status if provided
        if status is not None and form["status"] != status:
            form["status"] = status
            updated = True

        if not updated:
            return { "success": True, "message": "No changes made to the form." }

        # Save back (not strictly necessary as we're mutating the dict directly)
        self.forms[form_id] = form
        return { "success": True, "message": "Form updated successfully." }

    def create_application(
        self,
        app_id: str,
        name: str,
        owner_id: str,
        status: str,
        creation_datetime: str
    ) -> dict:
        """
        Add a new application to the platform.

        Args:
            app_id (str): Unique identifier for the application.
            name (str): Name of the application.
            owner_id (str): User ID of the application owner; must exist in users.
            status (str): Status of the application.
            creation_datetime (str): Creation datetime string.

        Returns:
            dict: {
                "success": True,
                "message": "Application created successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - app_id must be unique (not already exist).
            - owner_id must exist in users.
            - All parameters must be provided, non-empty.
        """
        if not all([app_id, name, owner_id, status, creation_datetime]):
            return { "success": False, "error": "All parameters must be provided and non-empty" }

        if app_id in self.applications:
            return { "success": False, "error": "Application ID already exists" }

        if owner_id not in self.users:
            return { "success": False, "error": "Owner user does not exist" }

        app_info = {
            "app_id": app_id,
            "name": name,
            "owner_id": owner_id,
            "status": status,
            "creation_datetime": creation_datetime
        }

        self.applications[app_id] = app_info

        return { "success": True, "message": "Application created successfully" }

    def update_application(
        self,
        app_id: str,
        user_id: str,
        name: str = None,
        owner_id: str = None,
        status: str = None
    ) -> dict:
        """
        Update fields (name, owner_id, status) of an existing application.

        Args:
            app_id (str): Application to update.
            user_id (str): User attempting the update (authorization checked).
            name (str, optional): New name for the application.
            owner_id (str, optional): New owner for the application.
            status (str, optional): New status for the application.

        Returns:
            dict: {
                "success": True,
                "message": "Application updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - app_id must exist.
            - user_id must exist, must be application owner or 'admin'.
            - User must be active.
            - creation_datetime is not modifiable.
            - No new identifier may be assigned (app_id unchangeable).
        """
        # Check application existence
        if app_id not in self.applications:
            return {"success": False, "error": "Application not found"}

        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        application = self.applications[app_id]
        user = self.users[user_id]

        # Check user is active
        if user.get("active_status", "") != "active":
            return {"success": False, "error": "User is not active"}

        # Authorization: owner or admin
        if not (user["role"] == "admin" or application["owner_id"] == user_id):
            return {"success": False, "error": "Permission denied"}

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if owner_id is not None:
            # Only allow updating owner if new owner exists and is active
            if owner_id not in self.users or self.users[owner_id].get("active_status", "") != "active":
                return {"success": False, "error": "New owner does not exist or is not active"}
            update_fields["owner_id"] = owner_id
        if status is not None:
            update_fields["status"] = status

        if not update_fields:
            return {"success": False, "error": "No updatable fields provided"}

        # Apply updates
        for k, v in update_fields.items():
            application[k] = v

        return {"success": True, "message": "Application updated successfully"}

    def delete_entity(self, entity_id: str) -> dict:
        """
        Remove an entity (Event, Application, Report, or Form) by its unique identifier.
        Enforces referential integrity: entities that are referenced by others cannot be deleted.

        Args:
            entity_id (str): The unique id of the entity to delete.

        Returns:
            dict: On success:
                { "success": True, "message": "<entity_type> <id> deleted successfully" }
            On failure:
                { "success": False, "error": "<reason>" }
    
        Constraints:
            - Event cannot be deleted if referenced as linked_event_id in any Form.
            - Application cannot be deleted if referenced as app_id in any Report or as linked_app_id in any Form.
            - Report and Form can be deleted if they exist.
            - If entity_id does not match any, return error.
        """
        # Check Event
        if entity_id in self.events:
            # Check for references in forms
            for form in self.forms.values():
                if form.get("linked_event_id") == entity_id:
                    return {
                        "success": False,
                        "error": "Cannot delete Event; referenced by a Form"
                    }
            del self.events[entity_id]
            return {
                "success": True,
                "message": f"Event {entity_id} deleted successfully"
            }
        # Check Application
        if entity_id in self.applications:
            # Check for references in reports
            for rpt in self.reports.values():
                if rpt.get("app_id") == entity_id:
                    return {
                        "success": False,
                        "error": "Cannot delete Application; referenced by a Report"
                    }
            # Check for references in forms
            for form in self.forms.values():
                if form.get("linked_app_id") == entity_id:
                    return {
                        "success": False,
                        "error": "Cannot delete Application; referenced by a Form"
                    }
            del self.applications[entity_id]
            return {
                "success": True,
                "message": f"Application {entity_id} deleted successfully"
            }
        # Check Report
        if entity_id in self.reports:
            del self.reports[entity_id]
            return {
                "success": True,
                "message": f"Report {entity_id} deleted successfully"
            }
        # Check Form
        if entity_id in self.forms:
            del self.forms[entity_id]
            return {
                "success": True,
                "message": f"Form {entity_id} deleted successfully"
            }
        # Not found
        return {
            "success": False,
            "error": "Entity not found"
        }

    def deactivate_user(self, user_id: str) -> dict:
        """
        Deactivate a user by setting their active_status to 'inactive'.

        Args:
            user_id (str): The unique identifier of the user to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> deactivated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, already inactive, etc.)
            }

        Constraints:
            - The user must exist in the system (user_id in self.users).
            - Does nothing if user is already inactive/archived.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        if user["active_status"].lower() in ("inactive", "archived"):
            return {"success": False, "error": f"User already {user['active_status']}"}

        user["active_status"] = "inactive"
        self.users[user_id] = user

        return {"success": True, "message": f"User {user_id} deactivated."}

    def restore_entity(self, entity_type: str, entity_id: str) -> dict:
        """
        Restore a previously deleted or archived entity, if supported.
        Supported:
            - Reports: archive_status == 'archived' -> 'active', archived_datetime = None
            - Users: active_status == 'inactive' -> 'active'
            - Events/Applications/Forms: status == 'archived'/'deleted' -> 'active' (if status field exists and marks inactivity)

        Args:
            entity_type (str): Type of entity ('event', 'application', 'report', 'form', 'user')
            entity_id (str): Unique identifier of the entity

        Returns:
            dict: {
                "success": True,
                "message": "<Entity> restored"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only archived/deleted/inactive entities can be restored.
            - Entities must exist.
            - If entity does not support restoration or is already active, return failure.
        """
        entity_type = entity_type.lower()
        if entity_type == "event":
            if entity_id not in self.events:
                return {"success": False, "error": "Event not found"}
            event = self.events[entity_id]
            status = event.get("status", "").lower()
            if status in ("archived", "deleted"):
                event["status"] = "active"
                return {"success": True, "message": "Event restored"}
            else:
                return {"success": False, "error": "Event is not archived or deleted"}
        elif entity_type == "application":
            if entity_id not in self.applications:
                return {"success": False, "error": "Application not found"}
            app = self.applications[entity_id]
            status = app.get("status", "").lower()
            if status in ("archived", "deleted"):
                app["status"] = "active"
                return {"success": True, "message": "Application restored"}
            else:
                return {"success": False, "error": "Application is not archived or deleted"}
        elif entity_type == "report":
            if entity_id not in self.reports:
                return {"success": False, "error": "Report not found"}
            report = self.reports[entity_id]
            if report.get("archive_status", "") == "archived":
                report["archive_status"] = "active"
                report["archived_datetime"] = None
                return {"success": True, "message": "Report restored"}
            else:
                return {"success": False, "error": "Report is not archived"}
        elif entity_type == "form":
            if entity_id not in self.forms:
                return {"success": False, "error": "Form not found"}
            form = self.forms[entity_id]
            status = form.get("status", "").lower()
            if status in ("archived", "deleted"):
                form["status"] = "active"
                return {"success": True, "message": "Form restored"}
            else:
                return {"success": False, "error": "Form is not archived or deleted"}
        elif entity_type == "user":
            if entity_id not in self.users:
                return {"success": False, "error": "User not found"}
            user = self.users[entity_id]
            if user.get("active_status", "").lower() == "inactive":
                user["active_status"] = "active"
                return {"success": True, "message": "User restored"}
            else:
                return {"success": False, "error": "User is already active"}
        else:
            return {"success": False, "error": "Unsupported entity type for restore operation"}


class EventApplicationManagementPlatform(BaseEnv):
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
            if key == "check_user_access_to_entity":
                setattr(env, "_check_user_access_to_entity_state", copy.deepcopy(value))
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

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_events_by_user(self, **kwargs):
        return self._call_inner_tool('list_events_by_user', kwargs)

    def get_application_by_id(self, **kwargs):
        return self._call_inner_tool('get_application_by_id', kwargs)

    def list_applications_by_user(self, **kwargs):
        return self._call_inner_tool('list_applications_by_user', kwargs)

    def get_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_report_by_id', kwargs)

    def list_reports_by_app_id(self, **kwargs):
        return self._call_inner_tool('list_reports_by_app_id', kwargs)

    def get_last_archived_report_by_app_id(self, **kwargs):
        return self._call_inner_tool('get_last_archived_report_by_app_id', kwargs)

    def count_forms(self, **kwargs):
        return self._call_inner_tool('count_forms', kwargs)

    def get_form_by_id(self, **kwargs):
        return self._call_inner_tool('get_form_by_id', kwargs)

    def list_forms_by_creator(self, **kwargs):
        return self._call_inner_tool('list_forms_by_creator', kwargs)

    def list_forms_by_event(self, **kwargs):
        return self._call_inner_tool('list_forms_by_event', kwargs)

    def list_forms_by_app(self, **kwargs):
        return self._call_inner_tool('list_forms_by_app', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_access_to_entity(self, **kwargs):
        return self._call_inner_tool('check_user_access_to_entity', kwargs)

    def count_entities(self, **kwargs):
        return self._call_inner_tool('count_entities', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def update_event(self, **kwargs):
        return self._call_inner_tool('update_event', kwargs)

    def archive_report(self, **kwargs):
        return self._call_inner_tool('archive_report', kwargs)

    def create_report(self, **kwargs):
        return self._call_inner_tool('create_report', kwargs)

    def update_report(self, **kwargs):
        return self._call_inner_tool('update_report', kwargs)

    def create_form(self, **kwargs):
        return self._call_inner_tool('create_form', kwargs)

    def update_form(self, **kwargs):
        return self._call_inner_tool('update_form', kwargs)

    def create_application(self, **kwargs):
        return self._call_inner_tool('create_application', kwargs)

    def update_application(self, **kwargs):
        return self._call_inner_tool('update_application', kwargs)

    def delete_entity(self, **kwargs):
        return self._call_inner_tool('delete_entity', kwargs)

    def deactivate_user(self, **kwargs):
        return self._call_inner_tool('deactivate_user', kwargs)

    def restore_entity(self, **kwargs):
        return self._call_inner_tool('restore_entity', kwargs)
