# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



# User: _id, name, contact_info, account_sta
class UserInfo(TypedDict):
    _id: str
    name: str
    contact_info: str
    account_sta: str

# Medication: medication_id, user_id, name, dosage, instruction
class MedicationInfo(TypedDict):
    medication_id: str
    user_id: str
    name: str
    dosage: str
    instruction: str

# Reminder: reminder_id, user_id, medication_id, schedule_time, recurrence_pattern, active_sta
class ReminderInfo(TypedDict):
    reminder_id: str
    user_id: str
    medication_id: str
    schedule_time: str
    recurrence_pattern: str
    active_sta: str

# DoseEvent: event_id, user_id, medication_id, scheduled_time, taken_time, sta
class DoseEventInfo(TypedDict):
    event_id: str
    user_id: str
    medication_id: str
    scheduled_time: str
    taken_time: str
    sta: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Medications: {medication_id: MedicationInfo}
        self.medications: Dict[str, MedicationInfo] = {}
        # Reminders: {reminder_id: ReminderInfo}
        self.reminders: Dict[str, ReminderInfo] = {}
        # DoseEvents: {event_id: DoseEventInfo}
        self.dose_events: Dict[str, DoseEventInfo] = {}

        # Constraints:
        # - Each reminder must reference a valid user and medication.
        # - Reminder schedules must not overlap for the same medication and user.
        # - Only active reminders are retrieved for notification.
        # - Dose events are created/updated according to user interactions or reminder delivery.

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve detailed user information for a given user ID.

        Args:
            _id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User information if found
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if the ID does not exist
            }

        Constraints:
            - The user ID must exist in the system.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_medications_for_user(self, user_id: str) -> dict:
        """
        Retrieve all medications assigned to a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": List[MedicationInfo]  # all medications for the user (may be empty)
                  }
                - On failure: {
                      "success": False,
                      "error": str  # Reason, e.g., "User does not exist"
                  }

        Constraints:
            - The user_id must reference an existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            med_info for med_info in self.medications.values()
            if med_info["user_id"] == user_id
        ]

        return { "success": True, "data": result }

    def get_medication_by_id(self, medication_id: str) -> dict:
        """
        Retrieve details for a specific medication via medication ID.

        Args:
            medication_id (str): The unique identifier of the medication.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": MedicationInfo
                }
                On failure: {
                    "success": False,
                    "error": str ("Medication not found")
                }
        Constraints:
            - The medication_id must exist in the system.
        """
        medication = self.medications.get(medication_id)
        if medication is None:
            return {"success": False, "error": "Medication not found"}
        return {"success": True, "data": medication}

    def list_active_reminders_for_user(self, user_id: str) -> dict:
        """
        Retrieve all active medication reminders for a given user ID.

        Args:
            user_id (str): The user ID for which to list active reminders.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo]  # All active reminders for the user, or []
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Only reminders with active_sta == "active" are returned.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        active_reminders = [
            reminder for reminder in self.reminders.values()
            if reminder["user_id"] == user_id and reminder.get("active_sta") == "active"
        ]
        return {"success": True, "data": active_reminders}

    def list_reminders_for_user(self, user_id: str) -> dict:
        """
        Retrieve all reminders (active or inactive) for a user by their user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo], # empty list if none found
            }
            or
            {
                "success": False,
                "error": str  # e.g. user does not exist
            }

        Constraints:
            - user_id must refer to an existing user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        reminders = [
            reminder for reminder in self.reminders.values()
            if reminder['user_id'] == user_id
        ]

        return {"success": True, "data": reminders}

    def list_reminders_for_user_and_medication(self, user_id: str, medication_id: str) -> dict:
        """
        Retrieve all reminders for a given user ID and medication ID.

        Args:
            user_id (str): The user's unique identifier.
            medication_id (str): The medication's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo]  # List of matching reminders (possibly empty)
            }
            OR
            {
                "success": False,
                "error": str  # Error reason ("User not found", "Medication not found", etc)
            }

        Constraints:
            - The user must exist.
            - The medication must exist and be assigned to the user.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Check if medication exists and is assigned to this user
        medication = self.medications.get(medication_id)
        if not medication:
            return { "success": False, "error": "Medication not found" }
        if medication["user_id"] != user_id:
            return { "success": False, "error": "Medication does not belong to the user" }

        # Retrieve matching reminders
        matching_reminders = [
            reminder for reminder in self.reminders.values()
            if reminder["user_id"] == user_id and reminder["medication_id"] == medication_id
        ]

        return { "success": True, "data": matching_reminders }

    def get_reminder_by_id(self, reminder_id: str) -> dict:
        """
        Retrieve details for a specific reminder by its reminder ID.

        Args:
            reminder_id (str): The unique identifier of the reminder to retrieve.

        Returns:
            dict:
                - If found: { "success": True, "data": ReminderInfo }
                - If not found: { "success": False, "error": "Reminder not found" }

        Constraints:
            - The reminder with the given reminder_id must exist.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder not found" }
        return { "success": True, "data": reminder }

    def check_reminder_overlap(
        self,
        user_id: str,
        medication_id: str,
        schedule_time: str,
        recurrence_pattern: str,
        reminder_id: str = None
    ) -> dict:
        """
        Check if a new or modified reminder (proposed by user_id for a medication) would overlap
        with any existing reminders for that user and medication.

        Args:
            user_id (str): User ID to check reminders for.
            medication_id (str): Medication ID to check reminders for.
            schedule_time (str): Proposed scheduled time.
            recurrence_pattern (str): Proposed recurrence pattern.
            reminder_id (str, optional): If updating, the reminder being updated (excluded from check).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "overlap": bool,
                            "conflicting_reminders": List[ReminderInfo]
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Overlap means same user, same medication, identical schedule_time and recurrence_pattern, and active.
            - Only active reminders are checked.
            - When updating an existing reminder, it will not compare with itself.
        """

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if medication_id not in self.medications:
            return {"success": False, "error": "Medication does not exist"}
        # Only consider active reminders for overlap.
        conflicting = []
        for rem in self.reminders.values():
            if (
                rem["user_id"] == user_id and
                rem["medication_id"] == medication_id and
                rem["schedule_time"] == schedule_time and
                rem["recurrence_pattern"] == recurrence_pattern and
                rem["active_sta"] == "active" and
                (reminder_id is None or rem["reminder_id"] != reminder_id)
            ):
                conflicting.append(rem)
        overlap = len(conflicting) > 0
        return {
            "success": True,
            "data": {
                "overlap": overlap,
                "conflicting_reminders": conflicting
            }
        }

    def list_dose_events_for_user(self, user_id: str) -> dict:
        """
        Retrieve all historical dose events (DoseEventInfo) for a specified user.

        Args:
            user_id (str): The ID of the user whose dose events should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[DoseEventInfo]  # List of all DoseEventInfo for user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User not found"
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        events = [
            event for event in self.dose_events.values()
            if event["user_id"] == user_id
        ]

        return { "success": True, "data": events }

    def list_dose_events_for_user_and_medication(self, user_id: str, medication_id: str) -> dict:
        """
        Retrieve all dose events for the specified user and medication.

        Args:
            user_id (str): The user's unique identifier
            medication_id (str): The medication's unique identifier

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[DoseEventInfo]  # All matching dose events (possibly empty)
                }
                OR
                {
                    "success": False,
                    "error": str  # Explanation of problem (user/medication not found, etc)
                }

        Constraints:
            - user_id must exist in users
            - medication_id must exist in medications and belong to the given user_id
        """
        if user_id not in self.users:
            return {"success": False, "error": "User ID does not exist"}
        if medication_id not in self.medications:
            return {"success": False, "error": "Medication ID does not exist"}
        medication = self.medications[medication_id]
        if medication["user_id"] != user_id:
            return {"success": False, "error": "Medication does not belong to the user"}

        dose_events = [
            event for event in self.dose_events.values()
            if event["user_id"] == user_id and event["medication_id"] == medication_id
        ]
        return {"success": True, "data": dose_events}

    def get_dose_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the details for a specific dose event by its event_id.

        Args:
            event_id (str): Unique identifier for the dose event.

        Returns:
            dict: {
                "success": True,
                "data": DoseEventInfo  # All stored info for the dose event.
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. dose event not found.
            }

        Constraints:
            - event_id must exist in the system.
        """
        dose_event = self.dose_events.get(event_id)
        if not dose_event:
            return { "success": False, "error": "Dose event not found" }
        return { "success": True, "data": dose_event }


    def create_reminder(
        self,
        user_id: str,
        medication_id: str,
        schedule_time: str,
        recurrence_pattern: str,
        active_sta: str
    ) -> dict:
        """
        Add a new reminder for a user and medication, ensuring it does not overlap with existing reminders.

        Args:
            user_id (str): The user's unique identifier.
            medication_id (str): The medication's unique identifier.
            schedule_time (str): The scheduled time for the reminder (as string, e.g. ISO8601).
            recurrence_pattern (str): The recurrence rule.
            active_sta (str): The status of the reminder ("active", etc.).

        Returns:
            dict: { "success": True, "message": "Reminder created successfully." }
                  or { "success": False, "error": "Reason" }

        Constraints:
            - User must exist.
            - Medication must exist and must belong to user.
            - No overlapping reminders for the same medication and user.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check medication exists and belongs to user
        med = self.medications.get(medication_id)
        if not med or med["user_id"] != user_id:
            return {"success": False, "error": "Medication does not exist or does not belong to user."}

        # Check for overlaps (simplistic: same user_id, medication_id, schedule_time, recurrence_pattern AND active)
        for r in self.reminders.values():
            if (r["user_id"] == user_id and
                r["medication_id"] == medication_id and
                r["active_sta"] == "active" and
                r["schedule_time"] == schedule_time and
                r["recurrence_pattern"] == recurrence_pattern):
                return {"success": False, "error": "Overlapping reminder exists for this medication and schedule."}

        # Generate a unique reminder_id
        reminder_id = str(uuid.uuid4())

        reminder = {
            "reminder_id": reminder_id,
            "user_id": user_id,
            "medication_id": medication_id,
            "schedule_time": schedule_time,
            "recurrence_pattern": recurrence_pattern,
            "active_sta": active_sta
        }

        self.reminders[reminder_id] = reminder

        return {"success": True, "message": "Reminder created successfully."}

    def update_reminder_status(self, reminder_id: str, active_sta: str) -> dict:
        """
        Activate or deactivate a reminder by updating its 'active_sta' field.

        Args:
            reminder_id (str): The unique identifier of the reminder.
            active_sta (str): The desired status ("active" or "inactive").

        Returns:
            dict: On success: 
                { "success": True, "message": "Reminder <reminder_id> status updated to <active_sta>." }
                On failure:
                { "success": False, "error": "reason" }

        Constraints:
            - Reminder with given ID must exist.
            - 'active_sta' should be either 'active' or 'inactive'.
        """
        allowed_statuses = {'active', 'inactive'}

        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return {"success": False, "error": "Reminder not found"}

        if active_sta not in allowed_statuses:
            return {
                "success": False,
                "error": f"Invalid status '{active_sta}'. Allowed statuses: {', '.join(allowed_statuses)}"
            }

        reminder["active_sta"] = active_sta
        self.reminders[reminder_id] = reminder  # Explicitly set in case of in-place update
        return {
            "success": True,
            "message": f"Reminder {reminder_id} status updated to {active_sta}."
        }

    def update_reminder_time(
        self,
        reminder_id: str,
        schedule_time: str = None,
        recurrence_pattern: str = None
    ) -> dict:
        """
        Change the schedule_time and/or recurrence_pattern for an existing reminder,
        ensuring no overlap with other reminders for the same user and medication.

        Args:
            reminder_id (str): The ID of the reminder to update.
            schedule_time (str, optional): The new schedule time for the reminder.
            recurrence_pattern (str, optional): The new recurrence pattern.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder time updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The reminder must exist.
            - The new schedule/recurrence must not overlap with existing active reminders for the same user and medication (excluding self).
            - At least one of schedule_time or recurrence_pattern must be provided.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return {"success": False, "error": "Reminder not found."}

        if schedule_time is None and recurrence_pattern is None:
            return {"success": False, "error": "No update fields provided."}

        user_id = reminder["user_id"]
        medication_id = reminder["medication_id"]

        # Use the new values for checking, fallback to current if not provided
        new_schedule_time = schedule_time if schedule_time is not None else reminder["schedule_time"]
        new_recurrence_pattern = recurrence_pattern if recurrence_pattern is not None else reminder["recurrence_pattern"]

        # Check for overlapping with other active reminders
        for r in self.reminders.values():
            if r["reminder_id"] == reminder_id:
                continue  # skip self
            if r["user_id"] == user_id and r["medication_id"] == medication_id and r["active_sta"] == "active":
                # Overlap logic -- here simplified to identical schedule_time and recurrence_pattern
                if r["schedule_time"] == new_schedule_time and r["recurrence_pattern"] == new_recurrence_pattern:
                    return {
                        "success": False,
                        "error": "Updated schedule would overlap with an existing reminder."
                    }

        # Passed checks, update reminder
        if schedule_time is not None:
            reminder["schedule_time"] = schedule_time
        if recurrence_pattern is not None:
            reminder["recurrence_pattern"] = recurrence_pattern

        return {"success": True, "message": "Reminder time updated."}

    def delete_reminder(self, reminder_id: str) -> dict:
        """
        Remove a reminder from the system by its reminder_id.

        Args:
            reminder_id (str): The unique identifier for the reminder to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Reminder deleted successfully."
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Reminder not found."
                    }

        Constraints:
            - The reminder must exist in the system.
            - All other data remains unchanged.
        """
        if reminder_id not in self.reminders:
            return {
                "success": False,
                "error": "Reminder not found."
            }
        del self.reminders[reminder_id]
        return {
            "success": True,
            "message": "Reminder deleted successfully."
        }

    def create_dose_event(
        self,
        user_id: str,
        medication_id: str,
        scheduled_time: str,
        taken_time: str,
        sta: str
    ) -> dict:
        """
        Log a new dose event (occurrence of medication intake or missed dose).

        Args:
            user_id (str): ID of the user taking the medication.
            medication_id (str): Medication to which the dose belongs.
            scheduled_time (str): Scheduled time for the dose.
            taken_time (str): Actual time the dose was taken (empty string or None if missed).
            sta (str): Status string for the dose event ('taken', 'missed', etc).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Dose event created successfully.",
                    "event_id": <new_event_id>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - user_id must exist in self.users.
            - medication_id must exist in self.medications.
            - medication must belong to the given user (self.medications[medication_id]["user_id"]).
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        # Check if medication exists
        if medication_id not in self.medications:
            return {"success": False, "error": "Medication does not exist"}
        # Check medication ownership
        if self.medications[medication_id]["user_id"] != user_id:
            return {"success": False, "error": "Medication does not belong to the user"}

        # Create unique event_id (use count or uuid)
        event_id = str(uuid.uuid4())

        event_data: DoseEventInfo = {
            "event_id": event_id,
            "user_id": user_id,
            "medication_id": medication_id,
            "scheduled_time": scheduled_time,
            "taken_time": taken_time,
            "sta": sta
        }

        self.dose_events[event_id] = event_data

        return {
            "success": True,
            "message": "Dose event created successfully.",
            "event_id": event_id
        }

    def update_dose_event_status(self, event_id: str, taken_time: str = None, sta: str = None) -> dict:
        """
        Update the taken_time and/or status (sta) of a dose event.
        Reflects adherence or non-adherence.

        Args:
            event_id (str): ID of the dose event to update.
            taken_time (str, optional): The timestamp to record for when the dose was taken (or cleared).
            sta (str, optional): The new status for the event ("taken", "missed", etc.).

        Returns:
            dict:
                - {"success": True, "message": "Dose event updated."}
                - {"success": False, "error": "..."}
    
        Constraints:
            - event_id must exist in self.dose_events.
            - At least one of taken_time or sta must be provided.
        """
        if event_id not in self.dose_events:
            return { "success": False, "error": "Dose event not found." }
        if taken_time is None and sta is None:
            return { "success": False, "error": "Nothing to update." }

        if taken_time is not None:
            self.dose_events[event_id]['taken_time'] = taken_time
        if sta is not None:
            self.dose_events[event_id]['sta'] = sta

        return { "success": True, "message": "Dose event updated." }

    def create_medication(
        self,
        medication_id: str,
        user_id: str,
        name: str,
        dosage: str,
        instruction: str
    ) -> dict:
        """
        Add a new medication for the specified user.

        Args:
            medication_id (str): Unique identifier for the medication.
            user_id (str): ID of the user to whom the medication is assigned.
            name (str): Name of the medication.
            dosage (str): Dosage information.
            instruction (str): Use instructions.

        Returns:
            dict: {
                "success": True,
                "message": "Medication created for user."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - medication_id must be unique.
            - user_id must reference an existing user.
        """

        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
    
        # Check for unique medication_id
        if medication_id in self.medications:
            return {"success": False, "error": "Medication ID already exists."}

        # Optional: validate required fields are not empty
        if not all([medication_id, user_id, name, dosage, instruction]):
            return {"success": False, "error": "All fields are required."}

        # Create the MedicationInfo record
        med_info: MedicationInfo = {
            "medication_id": medication_id,
            "user_id": user_id,
            "name": name,
            "dosage": dosage,
            "instruction": instruction
        }
        self.medications[medication_id] = med_info

        return {"success": True, "message": "Medication created for user."}

    def update_medication(
        self, 
        medication_id: str, 
        name: str = None, 
        dosage: str = None, 
        instruction: str = None
    ) -> dict:
        """
        Update the details (name, dosage, instruction) for an existing medication.

        Args:
            medication_id (str): The medication's unique identifier.
            name (str, optional): New name of the medication.
            dosage (str, optional): New dosage instructions.
            instruction (str, optional): New instructions for use.

        Returns:
            dict: {
                "success": True, "message": "Medication updated successfully."
            } 
            or 
            {
                "success": False, "error": str
            }

        Constraints:
            - Medication must exist.
            - At least one updatable field must be provided.
            - Only fields 'name', 'dosage', 'instruction' can be updated.
        """
        if medication_id not in self.medications:
            return {"success": False, "error": "Medication does not exist."}

        if all(v is None for v in [name, dosage, instruction]):
            return {
                "success": False,
                "error": "No updatable fields provided. Specify at least one of: name, dosage, instruction."
            }

        med = self.medications[medication_id]
        updated = False
        if name is not None:
            med["name"] = name
            updated = True
        if dosage is not None:
            med["dosage"] = dosage
            updated = True
        if instruction is not None:
            med["instruction"] = instruction
            updated = True

        self.medications[medication_id] = med

        return {"success": True, "message": "Medication updated successfully."}

    def delete_medication(self, medication_id: str) -> dict:
        """
        Permanently remove a medication and all associated reminders and dose events.

        Args:
            medication_id (str): The unique ID of the medication to delete.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Medication and associated reminders/dose events deleted."
                }
                Failure: {
                    "success": False,
                    "error": "Medication not found."
                }

        Constraints:
            - Medication must exist.
            - Deletes all reminders and dose events referencing this medication.
        """
        if medication_id not in self.medications:
            return { "success": False, "error": "Medication not found." }

        # Delete medication
        del self.medications[medication_id]

        # Delete associated reminders
        reminders_to_delete = [rid for rid, reminder in self.reminders.items()
                               if reminder["medication_id"] == medication_id]
        for rid in reminders_to_delete:
            del self.reminders[rid]

        # Delete associated dose events
        dose_events_to_delete = [eid for eid, event in self.dose_events.items()
                                 if event["medication_id"] == medication_id]
        for eid in dose_events_to_delete:
            del self.dose_events[eid]

        return {
            "success": True,
            "message": "Medication and associated reminders/dose events deleted."
        }

    def create_user(
        self,
        _id: str,
        name: str,
        contact_info: str,
        account_sta: str
    ) -> dict:
        """
        Register a new user in the system.

        Args:
            _id (str): Unique user identifier.
            name (str): User's name.
            contact_info (str): User's contact info (e.g. email or phone).
            account_sta (str): User account status.

        Returns:
            dict: {
                "success": True,
                "message": "User created"
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g. user already exists, missing field)
            }

        Constraints:
            - _id must be unique.
            - All fields are required and should be non-empty.
        """
        # Check if user already exists
        if not _id or not name or not contact_info or not account_sta:
            return {"success": False, "error": "All fields (_id, name, contact_info, account_sta) are required and must be non-empty"}

        if _id in self.users:
            return {"success": False, "error": "User with this ID already exists"}

        user_info = {
            "_id": _id,
            "name": name,
            "contact_info": contact_info,
            "account_sta": account_sta,
        }
        self.users[_id] = user_info
        return {"success": True, "message": "User created"}

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Activate, suspend, or change the account status of a user.

        Args:
            user_id (str): The unique user identifier (_id).
            new_status (str): The status to set for the user's account (e.g., "active", "suspended").

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of update
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found
            }

        Constraints:
            - The user must exist.
            - No restriction on status values enforced (arbitrary string allowed).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        self.users[user_id]["account_sta"] = new_status
        return { "success": True, "message": "User account status updated." }


class MedicationManagementApplication(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_medications_for_user(self, **kwargs):
        return self._call_inner_tool('list_medications_for_user', kwargs)

    def get_medication_by_id(self, **kwargs):
        return self._call_inner_tool('get_medication_by_id', kwargs)

    def list_active_reminders_for_user(self, **kwargs):
        return self._call_inner_tool('list_active_reminders_for_user', kwargs)

    def list_reminders_for_user(self, **kwargs):
        return self._call_inner_tool('list_reminders_for_user', kwargs)

    def list_reminders_for_user_and_medication(self, **kwargs):
        return self._call_inner_tool('list_reminders_for_user_and_medication', kwargs)

    def get_reminder_by_id(self, **kwargs):
        return self._call_inner_tool('get_reminder_by_id', kwargs)

    def check_reminder_overlap(self, **kwargs):
        return self._call_inner_tool('check_reminder_overlap', kwargs)

    def list_dose_events_for_user(self, **kwargs):
        return self._call_inner_tool('list_dose_events_for_user', kwargs)

    def list_dose_events_for_user_and_medication(self, **kwargs):
        return self._call_inner_tool('list_dose_events_for_user_and_medication', kwargs)

    def get_dose_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_dose_event_by_id', kwargs)

    def create_reminder(self, **kwargs):
        return self._call_inner_tool('create_reminder', kwargs)

    def update_reminder_status(self, **kwargs):
        return self._call_inner_tool('update_reminder_status', kwargs)

    def update_reminder_time(self, **kwargs):
        return self._call_inner_tool('update_reminder_time', kwargs)

    def delete_reminder(self, **kwargs):
        return self._call_inner_tool('delete_reminder', kwargs)

    def create_dose_event(self, **kwargs):
        return self._call_inner_tool('create_dose_event', kwargs)

    def update_dose_event_status(self, **kwargs):
        return self._call_inner_tool('update_dose_event_status', kwargs)

    def create_medication(self, **kwargs):
        return self._call_inner_tool('create_medication', kwargs)

    def update_medication(self, **kwargs):
        return self._call_inner_tool('update_medication', kwargs)

    def delete_medication(self, **kwargs):
        return self._call_inner_tool('delete_medication', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_account_status(self, **kwargs):
        return self._call_inner_tool('update_user_account_status', kwargs)

