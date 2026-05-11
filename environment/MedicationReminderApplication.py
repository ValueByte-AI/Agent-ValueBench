# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import List, Optional, Dict
import datetime
import uuid
from datetime import datetime, timedelta



class UserInfo(TypedDict):
    _id: str
    name: str
    contact_info: str
    notification_preference: str

class MedicationInfo(TypedDict):
    medication_id: str
    user_id: str
    name: str
    dosage: str
    form: str
    instruction: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    medication_id: str
    user_id: str
    start_date: str    # e.g. 'YYYY-MM-DD'
    end_date: str      # e.g. 'YYYY-MM-DD'
    frequency: str     # e.g. 'daily', 'twice a day', etc.
    times_of_day: List[str]  # e.g. ['08:00', '20:00']

class ReminderInfo(TypedDict):
    reminder_id: str
    schedule_id: str
    time: str         # e.g. 'YYYY-MM-DD HH:MM'
    status: str       # 'upcoming', 'sent', 'acknowledged', 'missed'

class DoseEventInfo(TypedDict):
    event_id: str
    schedule_id: str
    medication_id: str
    user_id: str
    datetime: str     # e.g. 'YYYY-MM-DD HH:MM'
    status: str       # 'taken', 'missed', 'skipped'

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Medications: {medication_id: MedicationInfo}
        self.medications: Dict[str, MedicationInfo] = {}

        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}

        # Reminders: {reminder_id: ReminderInfo}
        self.reminders: Dict[str, ReminderInfo] = {}

        # DoseEvents: {event_id: DoseEventInfo}
        self.dose_events: Dict[str, DoseEventInfo] = {}

        # Constraints:
        # - Reminders must be generated according to the defined schedule for each medication.
        # - Users can only create reminders for medications they have added.
        # - A DoseEvent is generated for each scheduled dose, and its status must be tracked.
        # - Reminders are only sent to users according to their notification preferences.
        # - Schedules must not overlap for the same medication in a conflicting manner 
        #   (e.g., cannot have two schedules for the same medication that would create simultaneous reminders).
        # - Completed or missed doses must be recorded to track adherence.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information for a user with the given name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            if a unique matching user is found, else
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Fails if no user with that name is found.
            - Fails if multiple users have the same name (no unique resolution).
        """
        # Find all users matching the provided name
        matches = [user for user in self.users.values() if user["name"] == name]

        if len(matches) == 0:
            return {"success": False, "error": "User not found"}
        elif len(matches) > 1:
            return {"success": False, "error": "Multiple users found with the given name"}
        else:
            return {"success": True, "data": matches[0]}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for the given user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success: { "success": True, "data": UserInfo }
                On failure: { "success": False, "error": "User not found" }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        user_info = self.users[user_id]
        return { "success": True, "data": user_info }

    def list_medications_for_user(self, user_id: str) -> dict:
        """
        List all medications registered by a user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MedicationInfo]  # a list of all medications registered by the user (may be empty).
                    }
                On failure (invalid user):
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        medications = [
            medication
            for medication in self.medications.values()
            if medication["user_id"] == user_id
        ]

        return {"success": True, "data": medications}

    def get_medication_by_id(self, medication_id: str) -> dict:
        """
        Retrieve details of a medication by medication_id.

        Args:
            medication_id (str): Unique identifier of the medication to retrieve.

        Returns:
            dict:
                - {"success": True, "data": MedicationInfo} if found.
                - {"success": False, "error": "Medication not found"} if medication_id does not exist.

        Constraints:
            - No additional constraints; simple lookup by ID.
        """
        if not medication_id or medication_id not in self.medications:
            return { "success": False, "error": "Medication not found" }
        return { "success": True, "data": self.medications[medication_id] }

    def list_schedules_for_medication(self, medication_id: str) -> dict:
        """
        List all schedules that have been set up for a specific medication.

        Args:
            medication_id (str): The unique identifier of the medication.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "data": List[ScheduleInfo],  # May be empty if no schedules exist
                }
              - On failure: {
                    "success": False,
                    "error": str  # Reason, e.g. "Medication does not exist"
                }
        Constraints:
            - The medication_id must exist in the system.
        """
        if medication_id not in self.medications:
            return { "success": False, "error": "Medication does not exist" }

        schedules = [
            schedule for schedule in self.schedules.values()
            if schedule["medication_id"] == medication_id
        ]
        return { "success": True, "data": schedules }

    def list_schedules_for_user(self, user_id: str) -> dict:
        """
        List all dosing schedules owned by a user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[ScheduleInfo]  # may be empty if the user has no schedules
                }
                On failure: {
                    "success": False,
                    "error": "User does not exist"
                }

        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        schedules = [
            schedule_info
            for schedule_info in self.schedules.values()
            if schedule_info["user_id"] == user_id
        ]

        return { "success": True, "data": schedules }

    def get_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Retrieve a specific medication schedule using its schedule_id.

        Args:
            schedule_id (str): The unique identifier for the schedule.

        Returns:
            dict:
              - On success:
                  {
                      "success": True,
                      "data": ScheduleInfo  # Information about the schedule
                  }
              - On failure (not found):
                  {
                      "success": False,
                      "error": "Schedule not found"
                  }

        Constraints:
            - The schedule_id must exist in the application.
    
        Edge/error cases:
            - If schedule_id does not correspond to any schedule, returns failure.
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found"}
        return {"success": True, "data": schedule}


    def check_schedule_overlap(
        self,
        medication_id: str,
        start_date: str,
        end_date: str,
        times_of_day: List[str],
        new_schedule_id: Optional[str] = None
    ) -> dict:
        """
        Check whether a proposed schedule for a medication overlaps in time with any
        existing schedules for the same medication that could generate simultaneous reminders.

        Args:
            medication_id (str): The medication ID the schedule is for.
            start_date (str): Proposed start date ('YYYY-MM-DD').
            end_date (str): Proposed end date ('YYYY-MM-DD').
            times_of_day (List[str]): List of times (e.g. ['08:00', '20:00']).
            new_schedule_id (Optional[str]): If checking an update, skip this schedule_id.

        Returns:
            dict: 
              - { "success": True, "overlap": bool, "conflicts": List[ScheduleInfo] }
              - { "success": False, "error": str }

        Constraints:
            - Schedules for the same medication cannot overlap in date/time.
            - Same date + at least one matching time counts as overlap, regardless of frequency.
        """

        # Simple date validation
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            if end_dt < start_dt:
                return { "success": False, "error": "end_date is before start_date" }
        except Exception:
            return { "success": False, "error": "Invalid start_date or end_date format" }

        if not isinstance(times_of_day, list) or not all(isinstance(t, str) for t in times_of_day):
            return { "success": False, "error": "times_of_day must be a list of time strings" }

        # Validate time format
        for t in times_of_day:
            try:
                datetime.strptime(t, "%H:%M")
            except Exception:
                return { "success": False, "error": f"Invalid time format in times_of_day: {t}" }

        # Medication must exist
        if medication_id not in self.medications:
            return { "success": False, "error": "Medication not found" }

        # Find conflicts
        conflicts = []
        for schedule in self.schedules.values():
            # Only check schedules for this medication, ignore same schedule on update
            if schedule["medication_id"] != medication_id:
                continue
            if new_schedule_id and schedule["schedule_id"] == new_schedule_id:
                continue

            # Check date overlap
            try:
                sched_start = datetime.strptime(schedule["start_date"], "%Y-%m-%d").date()
                sched_end = datetime.strptime(schedule["end_date"], "%Y-%m-%d").date()
            except Exception:
                continue  # Skip invalid schedule

            latest_start = max(start_dt, sched_start)
            earliest_end = min(end_dt, sched_end)
            if latest_start > earliest_end:
                continue  # No overlapping dates

            # Check time overlap
            existing_times = set(schedule.get("times_of_day", []))
            proposed_times = set(times_of_day)
            if existing_times & proposed_times:  # Any time-in-common means conflict
                conflicts.append(schedule)

        overlap_found = len(conflicts) > 0
        return { "success": True, "overlap": overlap_found, "conflicts": conflicts }

    def list_reminders_for_schedule(self, schedule_id: str) -> dict:
        """
        List all reminders already generated for a given schedule.

        Args:
            schedule_id (str): The ID of the schedule for which to list reminders.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo]  # List of reminders for this schedule (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if schedule doesn't exist
            }

        Constraints:
            - schedule_id must exist in the system.
        """
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule does not exist"}

        result = [
            reminder for reminder in self.reminders.values()
            if reminder["schedule_id"] == schedule_id
        ]

        return {"success": True, "data": result}

    def get_reminder_by_id(self, reminder_id: str) -> dict:
        """
        Retrieve the details of a reminder using its reminder_id.

        Args:
            reminder_id (str): The unique identifier for the reminder.

        Returns:
            dict: 
                - If found: {"success": True, "data": ReminderInfo}
                - If not found: {"success": False, "error": "Reminder not found"}
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return {"success": False, "error": "Reminder not found"}
        return {"success": True, "data": reminder}

    def list_upcoming_reminders_for_user(self, user_id: str) -> dict:
        """
        Retrieve all upcoming reminders for the specified user.

        Args:
            user_id (str): The identifier of the user whose reminders should be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo],  # List of upcoming reminders for the user
            }
            or
            {
                "success": False,
                "error": str  # error description, e.g. 'User not found'
            }

        Constraints:
            - The user must exist.
            - Only reminders associated with the user's schedules and with status 'upcoming' are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Gather all schedule IDs belonging to this user
        user_schedule_ids = {sched["schedule_id"] for sched in self.schedules.values() if sched["user_id"] == user_id}
        # Now find upcoming reminders for those schedules
        upcoming_reminders = [
            reminder for reminder in self.reminders.values()
            if reminder["schedule_id"] in user_schedule_ids and reminder["status"] == "upcoming"
        ]
        return {"success": True, "data": upcoming_reminders}

    def get_notification_preference_for_user(self, user_id: str) -> dict:
        """
        Retrieve the notification/reminder preference for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": str  # The notification_preference value
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "User not found"
            }

        Constraints:
            - user_id must correspond to an existing user.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user.get("notification_preference")}

    def list_dose_events_for_schedule(self, schedule_id: str) -> dict:
        """
        List all DoseEvent records tied to a specific schedule.

        Args:
            schedule_id (str): The unique identifier of the Schedule.

        Returns:
            dict: {
                "success": True,
                "data": List[DoseEventInfo]
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - schedule_id must exist in self.schedules.
        """
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule does not exist."}

        result = [
            event for event in self.dose_events.values()
            if event["schedule_id"] == schedule_id
        ]

        return {"success": True, "data": result}

    def get_dose_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve details for a DoseEvent by its event_id.

        Args:
            event_id (str): The unique ID of the DoseEvent.

        Returns:
            dict: {
                "success": True,
                "data": DoseEventInfo  # Full DoseEvent details if found
            }
            or
            {
                "success": False,
                "error": "DoseEvent not found"
            }

        Constraints:
            - event_id must exist in the DoseEvent database.
        """
        dose_event = self.dose_events.get(event_id)
        if not dose_event:
            return { "success": False, "error": "DoseEvent not found" }
        return { "success": True, "data": dose_event }

    def get_dose_adherence_summary(
        self, 
        schedule_id: str = None, 
        medication_id: str = None
    ) -> dict:
        """
        Summarize adherence for dose events associated with a given schedule or medication.

        Args:
            schedule_id (str, optional): Schedule ID to filter adherence events.
            medication_id (str, optional): Medication ID to filter adherence events.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "total": int,
                            "taken": int,
                            "missed": int,
                            "skipped": int,
                            "events_by_status": {
                                "taken": [DoseEventInfo, ...],
                                "missed": [DoseEventInfo, ...],
                                "skipped": [DoseEventInfo, ...]
                            }
                        }
                    }
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - Either schedule_id or medication_id must be provided.
            - Provided schedule_id or medication_id must exist if provided.
        """
        # Must provide at least one
        if not schedule_id and not medication_id:
            return { "success": False, "error": "You must specify schedule_id or medication_id." }

        # Validate existence of provided IDs
        if schedule_id and schedule_id not in self.schedules:
            return { "success": False, "error": f"Schedule ID '{schedule_id}' not found." }
        if medication_id and medication_id not in self.medications:
            return { "success": False, "error": f"Medication ID '{medication_id}' not found." }

        # Build filter
        def event_matches(event: DoseEventInfo) -> bool:
            if schedule_id and medication_id:
                return event["schedule_id"] == schedule_id and event["medication_id"] == medication_id
            elif schedule_id:
                return event["schedule_id"] == schedule_id
            elif medication_id:
                return event["medication_id"] == medication_id
            return False  # unreachable

        # Gather matching DoseEvents
        relevant_events = [
            event for event in self.dose_events.values()
            if event_matches(event)
        ]

        # Initialize stats
        result = {
            "total": len(relevant_events),
            "taken": 0,
            "missed": 0,
            "skipped": 0,
            "events_by_status": {
                "taken": [],
                "missed": [],
                "skipped": [],
            }
        }

        # Populate result
        for event in relevant_events:
            status = event.get("status")
            if status in ("taken", "missed", "skipped"):
                result[status] += 1
                result["events_by_status"][status].append(event)

        return { "success": True, "data": result }


    def add_medication_for_user(
        self,
        user_id: str,
        name: str,
        dosage: str,
        form: str,
        instruction: str
    ) -> dict:
        """
        Add/register a new medication to a user’s account.

        Args:
            user_id (str): The ID of the user.
            name (str): Name of the medication.
            dosage (str): Dosage details (e.g., '10 mg').
            form (str): Form (e.g., 'tablet', 'liquid').
            instruction (str): Special instructions.

        Returns:
            dict: 
              On success:
                {
                  "success": True,
                  "message": "Medication added",
                  "medication_id": <generated_id>
                }
              On error:
                {
                  "success": False,
                  "error": <reason>
                }

        Constraints:
            - user_id must exist.
            - All fields must be non-empty.
            - (Optional) Medication name for same user should be unique.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Check required fields are non-empty
        if not all([name, dosage, form, instruction]):
            return { "success": False, "error": "All medication fields must be provided and non-empty" }
    
        # Medication name uniqueness for a user (optional constraint)
        for med in self.medications.values():
            if med["user_id"] == user_id and med["name"].lower() == name.lower():
                return { "success": False, "error": "Medication name already exists for this user" }

        med_id = str(uuid.uuid4())
        med_info: MedicationInfo = {
            "medication_id": med_id,
            "user_id": user_id,
            "name": name,
            "dosage": dosage,
            "form": form,
            "instruction": instruction
        }
        self.medications[med_id] = med_info

        return {
            "success": True,
            "message": "Medication added",
            "medication_id": med_id
        }

    def add_schedule_for_medication(
        self,
        medication_id: str,
        user_id: str,
        start_date: str,
        end_date: str,
        frequency: str,
        times_of_day: list
    ) -> dict:
        """
        Create a dosing schedule for a user’s medication, ensuring no overlaps.

        Args:
            medication_id (str): ID of the medication to schedule.
            user_id (str): ID of the user.
            start_date (str): Start date, format 'YYYY-MM-DD'.
            end_date (str): End date, format 'YYYY-MM-DD'.
            frequency (str): Dosing frequency (e.g., 'daily', 'twice a day').
            times_of_day (List[str]): Times in 'HH:MM' format for doses.

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
        - Medication must exist and belong to the user.
        - No existing schedule for the same medication with overlapping date & time intervals.
        - Dates/times are assumed valid format.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check medication exists
        medication = self.medications.get(medication_id)
        if not medication:
            return {"success": False, "error": "Medication does not exist"}

        # Check medication belongs to user
        if medication["user_id"] != user_id:
            return {"success": False, "error": "User does not own this medication"}

        # Check for overlapping schedules for this medication and user
        for schedule in self.schedules.values():
            if (
                schedule["medication_id"] == medication_id and 
                schedule["user_id"] == user_id
            ):
                # Overlap if date ranges overlap and times_of_day intersect
                # Convert dates to comparable form
                if not (
                    end_date < schedule["start_date"] or start_date > schedule["end_date"]
                ):
                    # Date intervals overlap, now check for time collision
                    if set(schedule["times_of_day"]).intersection(set(times_of_day)):
                        return {
                            "success": False,
                            "error": "Schedule overlaps with an existing schedule for this medication"
                        }

        # Generate unique schedule_id
        schedule_id = str(uuid.uuid4())

        new_schedule = {
            "schedule_id": schedule_id,
            "medication_id": medication_id,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "times_of_day": times_of_day
        }
        self.schedules[schedule_id] = new_schedule

        return {
            "success": True,
            "message": f"Schedule created for medication {medication_id} and user {user_id}"
        }

    def update_schedule(
        self,
        schedule_id: str,
        frequency: str = None,
        times_of_day: list = None,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        Update details for a schedule, such as frequency, times, and date range.
    
        Args:
            schedule_id (str): The schedule to update.
            frequency (str, optional): New frequency value if updating.
            times_of_day (List[str], optional): New times of day if updating.
            start_date (str, optional): New start date (YYYY-MM-DD) if updating.
            end_date (str, optional): New end date (YYYY-MM-DD) if updating.
    
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
            - Schedule must exist.
            - Updates must not cause schedule overlap for the same medication.
            - If dates are updated, end_date >= start_date.
        """

        # Lookup
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule does not exist."}

        medication_id = schedule["medication_id"]
        user_id = schedule["user_id"]

        # Compose new field values
        new_start = start_date if start_date is not None else schedule["start_date"]
        new_end = end_date if end_date is not None else schedule["end_date"]
        new_times = times_of_day if times_of_day is not None else schedule["times_of_day"]
        new_frequency = frequency if frequency is not None else schedule["frequency"]

        # Validate date logic
        try:
            dt_start = datetime.strptime(new_start, "%Y-%m-%d")
            dt_end = datetime.strptime(new_end, "%Y-%m-%d")
            if dt_end < dt_start:
                return {"success": False, "error": "end_date cannot be before start_date."}
        except Exception:
            return {"success": False, "error": "Invalid date format for start_date or end_date. Expected YYYY-MM-DD."}

        # OVERLAP CHECK for same medication (excluding current schedule)
        for other in self.schedules.values():
            if other["schedule_id"] == schedule_id:
                continue
            if other["medication_id"] != medication_id or other["user_id"] != user_id:
                continue
            # If date ranges overlap
            try:
                o_start = datetime.strptime(other["start_date"], "%Y-%m-%d")
                o_end = datetime.strptime(other["end_date"], "%Y-%m-%d")
            except Exception:
                continue  # skip invalid
            if dt_start <= o_end and o_start <= dt_end:
                # Possible overlap in date range, check time-of-day overlap logic
                # (For simplicity, if frequency/times match at any, treat as overlap)
                if set(new_times) & set(other["times_of_day"]):
                    return {
                        "success": False,
                        "error": "Update would create overlapping schedule for the same medication."
                    }

        # Apply updates
        if frequency is not None:
            schedule["frequency"] = frequency
        if times_of_day is not None:
            schedule["times_of_day"] = times_of_day
        if start_date is not None:
            schedule["start_date"] = start_date
        if end_date is not None:
            schedule["end_date"] = end_date

        self.schedules[schedule_id] = schedule
        return {"success": True, "message": "Schedule updated successfully."}

    def remove_schedule(self, schedule_id: str) -> dict:
        """
        Remove an existing dosing schedule for a medication,
        including all associated reminders and dose events.

        Args:
            schedule_id (str): The unique ID of the schedule to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule and related reminders and dose events removed successfully."
            }
            or
            {
                "success": False,
                "error": "Schedule not found."
            }

        Constraints:
            - If the schedule_id does not exist, fail gracefully.
            - Remove all reminders and dose events associated with this schedule.
        """

        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule not found." }

        # Remove the schedule
        del self.schedules[schedule_id]

        # Remove all reminders linked to this schedule
        reminders_to_delete = [rid for rid, rem in self.reminders.items() if rem["schedule_id"] == schedule_id]
        for rid in reminders_to_delete:
            del self.reminders[rid]

        # Remove all dose events linked to this schedule
        dose_events_to_delete = [eid for eid, evt in self.dose_events.items() if evt["schedule_id"] == schedule_id]
        for eid in dose_events_to_delete:
            del self.dose_events[eid]

        return { "success": True, "message": "Schedule and related reminders and dose events removed successfully." }

    def generate_reminders_for_schedule(self, schedule_id: str) -> dict:
        """
        Generate and store reminders as per a given schedule.

        Args:
            schedule_id (str): The ID of the schedule for which reminders should be generated.

        Returns:
            dict: {
                "success": True,
                "message": "<N> reminders generated and stored."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Schedule must exist.
            - Reminders are generated for every (date, time) combo between start_date and end_date according to frequency and times_of_day.
            - Existing reminders for the same (schedule_id, time) should not be duplicated.
        """

        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule not found"}

        schedule = self.schedules[schedule_id]
        start_date = schedule["start_date"]
        end_date = schedule["end_date"]
        frequency = schedule["frequency"].lower()
        times_of_day = schedule.get("times_of_day", [])

        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if end_dt < start_dt:
                return {"success": False, "error": "Schedule end_date is before start_date"}
        except Exception:
            return {"success": False, "error": "Invalid start_date or end_date format"}

        # Frequency interpretation
        # Only basic handling: 'daily', 'twice a day', 'every n days'
        schedule_days = []
        day_delta = 1  # Default daily
        freq_type = None

        if "every" in frequency and "day" in frequency:
            # e.g. "every 3 days"
            try:
                n = int(frequency.split(" ")[1])
                day_delta = n
                freq_type = "every_n_days"
            except Exception:
                return {"success": False, "error": "Unsupported frequency string"}
        elif frequency == "daily" or "once" in frequency:
            freq_type = "daily"
            day_delta = 1
        elif "twice" in frequency:
            freq_type = "daily"
            day_delta = 1
        elif "weekly" in frequency:
            freq_type = "weekly"
            day_delta = 7
        else:
            freq_type = "daily"  # fallback

        # Build all reminder datetimes
        current_date = start_dt
        new_reminders = []
        reminder_id_counter = 0

        # Collect set of (schedule_id, time) already present to avoid duplicates
        existing_times = set(
            (r["schedule_id"], r["time"])
            for r in self.reminders.values()
            if r["schedule_id"] == schedule_id
        )

        while current_date <= end_dt:
            for t in times_of_day:
                # Compose full datetime string: 'YYYY-MM-DD HH:MM'
                time_str = f"{current_date.strftime('%Y-%m-%d')} {t}"
                key = (schedule_id, time_str)
                if key in existing_times:
                    continue  # Skip already existing
                reminder_id = f"rem-{schedule_id}-{current_date.strftime('%Y%m%d')}-{t.replace(':','')}"
                # Ensure uniqueness if used multiple times
                if reminder_id in self.reminders:
                    reminder_id = f"{reminder_id}-{reminder_id_counter}"
                    reminder_id_counter += 1
                reminder_info = {
                    "reminder_id": reminder_id,
                    "schedule_id": schedule_id,
                    "time": time_str,
                    "status": "upcoming",
                }
                self.reminders[reminder_id] = reminder_info
                new_reminders.append(reminder_id)
            if freq_type == "weekly":
                current_date += timedelta(weeks=1)
            else:
                current_date += timedelta(days=day_delta)

        return {
            "success": True,
            "message": f"{len(new_reminders)} reminders generated and stored."
        }

    def update_reminder_status(self, reminder_id: str, new_status: str) -> dict:
        """
        Update the status of a specific reminder by its ID.

        Args:
            reminder_id (str): The ID of the reminder to update.
            new_status (str): The new status for the reminder. Must be one of:
                'upcoming', 'sent', 'acknowledged', 'missed'.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Reminder status updated to <new_status>."}
                On failure:
                    {"success": False, "error": <reason>}
        Constraints:
            - reminder_id must exist in the system.
            - new_status must be one of the allowed reminder statuses.
        """
        allowed_statuses = {"upcoming", "sent", "acknowledged", "missed"}
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed values: {', '.join(allowed_statuses)}." }

        self.reminders[reminder_id]["status"] = new_status

        return { "success": True, "message": f"Reminder status updated to {new_status}." }

    def delete_reminder(self, reminder_id: str) -> dict:
        """
        Remove a specific reminder from the system.

        Args:
            reminder_id (str): The unique identifier of the reminder to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder <reminder_id> deleted."
            }
            or
            dict: {
                "success": False,
                "error": "Reminder not found."
            }

        Constraints:
            - Reminder with provided reminder_id must exist.
            - No further checks or cascading deletions are enforced by current constraints.
        """
        if reminder_id not in self.reminders:
            return {"success": False, "error": "Reminder not found."}

        del self.reminders[reminder_id]
        return {"success": True, "message": f"Reminder {reminder_id} deleted."}

    def create_dose_event(self, schedule_id: str, datetime: str, status: str) -> dict:
        """
        Create a new DoseEvent instance for a scheduled medication administration.

        Args:
            schedule_id (str): The identifier of the medication schedule.
            datetime (str): The date and time for the DoseEvent ('YYYY-MM-DD HH:MM').
            status (str): Status of the event ('taken', 'missed', or 'skipped').

        Returns:
            dict: {
                "success": True,
                "message": "DoseEvent created for schedule ... at ..."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The referenced schedule must exist.
            - There must not already be a DoseEvent for the same schedule_id and datetime.
            - Status must be 'taken', 'missed', or 'skipped'.
        """
        # Validate schedule exists
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule does not exist."}

        # Validate status
        valid_status = {"taken", "missed", "skipped"}
        if status not in valid_status:
            return {"success": False, "error": f"Invalid status '{status}'. Must be one of {valid_status}."}

        # Retrieve schedule
        schedule = self.schedules[schedule_id]

        # Check for duplicate event: same schedule_id and datetime
        for event in self.dose_events.values():
            if event["schedule_id"] == schedule_id and event["datetime"] == datetime:
                return {
                    "success": False,
                    "error": f"DoseEvent for this schedule at {datetime} already exists."
                }

        # Prepare DoseEventInfo
        # Generate unique event_id
        base_id = f"{schedule_id}_{datetime.replace(' ', '_').replace(':', '').replace('-', '')}"
        event_id = base_id
        suffix = 1
        # Ensure uniqueness in case of collision
        while event_id in self.dose_events:
            event_id = f"{base_id}_{suffix}"
            suffix += 1

        # Get medication_id and user_id from schedule
        medication_id = schedule["medication_id"]
        user_id = schedule["user_id"]

        new_event = {
            "event_id": event_id,
            "schedule_id": schedule_id,
            "medication_id": medication_id,
            "user_id": user_id,
            "datetime": datetime,
            "status": status
        }
        self.dose_events[event_id] = new_event

        return {
            "success": True,
            "message": f"DoseEvent created for schedule {schedule_id} at {datetime}"
        }

    def update_dose_event_status(self, event_id: str, new_status: str) -> dict:
        """
        Update the status of a given DoseEvent (to 'taken', 'missed', or 'skipped').

        Args:
            event_id (str): The unique identifier for the DoseEvent.
            new_status (str): The new status to set. Must be one of ['taken', 'missed', 'skipped'].

        Returns:
            dict:
                - On success: {"success": True, "message": "Dose event status updated"}
                - On error: {"success": False, "error": <reason>}

        Constraints:
            - The event_id must exist in self.dose_events.
            - The new_status must be an allowed value: 'taken', 'missed', or 'skipped'.
        """
        allowed_statuses = {'taken', 'missed', 'skipped'}
        if event_id not in self.dose_events:
            return {"success": False, "error": "DoseEvent not found"}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Must be one of {sorted(allowed_statuses)}"}

        self.dose_events[event_id]["status"] = new_status
        return {"success": True, "message": "Dose event status updated"}

    def record_completed_dose(self, event_id: str) -> dict:
        """
        Mark a DoseEvent as completed ('taken') for adherence.

        Args:
            event_id (str): The unique identifier for the DoseEvent to mark as completed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Dose event marked as taken"
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason why the update could not be performed
                    }

        Constraints:
            - The DoseEvent must exist.
            - A DoseEvent can only be marked as 'taken' if it is not already 'taken'.
            - Typically, only 'upcoming' or 'missed' statuses can be transitioned to 'taken'.
        """
        dose_event = self.dose_events.get(event_id)
        if not dose_event:
            return { "success": False, "error": "DoseEvent does not exist" }

        if dose_event["status"] == "taken":
            return { "success": False, "error": "DoseEvent already marked as taken" }

        if dose_event["status"] == "skipped":
            return { "success": False, "error": "Cannot mark a skipped DoseEvent as taken" }

        dose_event["status"] = "taken"
        self.dose_events[event_id] = dose_event

        return { "success": True, "message": "Dose event marked as taken" }

    def remove_medication_for_user(self, user_id: str, medication_id: str) -> dict:
        """
        Remove an existing medication from a user's account, including all related schedules,
        reminders, and dose events for that medication and user.

        Args:
            user_id (str): The user requesting the removal.
            medication_id (str): The medication to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Medication and related schedules removed for user."
            }
            or
            {
                "success": False,
                "error": "Description of the error"
            }

        Constraints:
            - Medication must exist and belong to the user.
            - Remove all associated schedules, reminders, and dose events.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check if medication exists
        med_info = self.medications.get(medication_id)
        if not med_info:
            return {"success": False, "error": "Medication does not exist"}
        if med_info["user_id"] != user_id:
            return {"success": False, "error": "Medication does not belong to the user"}

        # Find all schedules related to this medication and user
        related_schedule_ids = [
            sched_id for sched_id, sched in self.schedules.items()
            if sched["medication_id"] == medication_id and sched["user_id"] == user_id
        ]

        # Remove all related reminders and dose events, then schedules
        for schedule_id in related_schedule_ids:
            # Remove corresponding reminders
            reminders_to_delete = [
                rem_id for rem_id, rem in self.reminders.items()
                if rem["schedule_id"] == schedule_id
            ]
            for rem_id in reminders_to_delete:
                del self.reminders[rem_id]
        
            # Remove corresponding dose events
            dose_events_to_delete = [
                event_id for event_id, devent in self.dose_events.items()
                if devent["schedule_id"] == schedule_id and devent["medication_id"] == medication_id and devent["user_id"] == user_id
            ]
            for event_id in dose_events_to_delete:
                del self.dose_events[event_id]

            # Remove the schedule itself
            if schedule_id in self.schedules:
                del self.schedules[schedule_id]

        # Remove the medication itself
        del self.medications[medication_id]

        return {"success": True, "message": "Medication and related schedules removed for user."}

    def update_user_notification_preference(self, user_id: str, notification_preference: str) -> dict:
        """
        Update a user's notification/reminder preferences.

        Args:
            user_id (str): The user identifier whose preferences are being updated.
            notification_preference (str): The new notification/reminder preference (e.g., 'email', 'sms', 'push').

        Returns:
            dict:
                - On success: { "success": True, "message": "Notification preference updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        self.users[user_id]['notification_preference'] = notification_preference
        return { "success": True, "message": "Notification preference updated." }


class MedicationReminderApplication(BaseEnv):
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

    def list_medications_for_user(self, **kwargs):
        return self._call_inner_tool('list_medications_for_user', kwargs)

    def get_medication_by_id(self, **kwargs):
        return self._call_inner_tool('get_medication_by_id', kwargs)

    def list_schedules_for_medication(self, **kwargs):
        return self._call_inner_tool('list_schedules_for_medication', kwargs)

    def list_schedules_for_user(self, **kwargs):
        return self._call_inner_tool('list_schedules_for_user', kwargs)

    def get_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_id', kwargs)

    def check_schedule_overlap(self, **kwargs):
        return self._call_inner_tool('check_schedule_overlap', kwargs)

    def list_reminders_for_schedule(self, **kwargs):
        return self._call_inner_tool('list_reminders_for_schedule', kwargs)

    def get_reminder_by_id(self, **kwargs):
        return self._call_inner_tool('get_reminder_by_id', kwargs)

    def list_upcoming_reminders_for_user(self, **kwargs):
        return self._call_inner_tool('list_upcoming_reminders_for_user', kwargs)

    def get_notification_preference_for_user(self, **kwargs):
        return self._call_inner_tool('get_notification_preference_for_user', kwargs)

    def list_dose_events_for_schedule(self, **kwargs):
        return self._call_inner_tool('list_dose_events_for_schedule', kwargs)

    def get_dose_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_dose_event_by_id', kwargs)

    def get_dose_adherence_summary(self, **kwargs):
        return self._call_inner_tool('get_dose_adherence_summary', kwargs)

    def add_medication_for_user(self, **kwargs):
        return self._call_inner_tool('add_medication_for_user', kwargs)

    def add_schedule_for_medication(self, **kwargs):
        return self._call_inner_tool('add_schedule_for_medication', kwargs)

    def update_schedule(self, **kwargs):
        return self._call_inner_tool('update_schedule', kwargs)

    def remove_schedule(self, **kwargs):
        return self._call_inner_tool('remove_schedule', kwargs)

    def generate_reminders_for_schedule(self, **kwargs):
        return self._call_inner_tool('generate_reminders_for_schedule', kwargs)

    def update_reminder_status(self, **kwargs):
        return self._call_inner_tool('update_reminder_status', kwargs)

    def delete_reminder(self, **kwargs):
        return self._call_inner_tool('delete_reminder', kwargs)

    def create_dose_event(self, **kwargs):
        return self._call_inner_tool('create_dose_event', kwargs)

    def update_dose_event_status(self, **kwargs):
        return self._call_inner_tool('update_dose_event_status', kwargs)

    def record_completed_dose(self, **kwargs):
        return self._call_inner_tool('record_completed_dose', kwargs)

    def remove_medication_for_user(self, **kwargs):
        return self._call_inner_tool('remove_medication_for_user', kwargs)

    def update_user_notification_preference(self, **kwargs):
        return self._call_inner_tool('update_user_notification_preference', kwargs)
