# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import List, Optional, Dict
import datetime



class EventInfo(TypedDict):
    event_id: str
    name: str
    description: str
    start_date: str  # e.g., "YYYY-MM-DD"
    end_date: str    # e.g., "YYYY-MM-DD"
    location: str

class ActivityInfo(TypedDict):
    activity_id: str
    event_id: str  # reference to parent Event
    name: str
    scheduled_date: str    # e.g., "YYYY-MM-DD"
    start_time: str        # e.g., "HH:MM"
    end_time: str          # e.g., "HH:MM"
    location: str
    assigned_resources: List[str]   # list of resource_ids
    description: str

class ResourceInfo(TypedDict):
    resource_id: str
    name: str
    type: str
    availability: List[str]   # e.g., ["2023-12-01 10:00-14:00", ...]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Event management scheduling environment.
        """

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Activities: {activity_id: ActivityInfo}
        self.activities: Dict[str, ActivityInfo] = {}

        # Resources: {resource_id: ResourceInfo}
        self.resources: Dict[str, ResourceInfo] = {}

        # === Constraints ===
        # - Activities must belong to a parent event.
        # - Activities cannot be scheduled outside the event’s start_date and end_date.
        # - Locations and resources allocated to activities must be available at the scheduled times.
        # - Activities on the same date and location/resource cannot overlap in time.

    def get_event_by_name(self, name: str) -> dict:
        """
        Retrieve the details of an event (event_id, name, description, start_date, end_date, location) by event name.

        Args:
            name (str): The name of the event to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": EventInfo,   # event details
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Event with this name not found"
            }

        Constraints:
            - Event names are matched exactly (case-sensitive).
        """
        for event in self.events.values():
            if event["name"] == name:
                return { "success": True, "data": event }
        return { "success": False, "error": "Event with this name not found" }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the details of an event using its event_id.

        Args:
            event_id (str): The unique identifier of the event.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": EventInfo
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
        if event is None:
            return { "success": False, "error": "Event not found" }
        return { "success": True, "data": event }

    def list_all_events(self) -> dict:
        """
        List all events managed in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # List of all event information (may be empty)
            }

        Constraints:
            - No input needed.
            - Always succeeds (returns empty list if no events exist).
        """
        all_events = list(self.events.values())
        return {"success": True, "data": all_events}

    def get_activities_by_event_id(self, event_id: str) -> dict:
        """
        Retrieve all activities scheduled under a specific event.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[ActivityInfo]  # May be empty if no activities scheduled under this event
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g. "Event does not exist"
                    }

        Constraints:
            - event_id must exist in self.events.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        activities = [
            activity for activity in self.activities.values()
            if activity['event_id'] == event_id
        ]

        return { "success": True, "data": activities }

    def get_activities_on_date(self, scheduled_date: str, event_id: str = None) -> dict:
        """
        Retrieve all activities scheduled on a specific date, optionally filtered by event_id.

        Args:
            scheduled_date (str): The target date in "YYYY-MM-DD" format.
            event_id (str, optional): If provided, filter to activities belonging only to this event.

        Returns:
            dict: {
                "success": True,
                "data": List[ActivityInfo],  # List of activities on that date (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the error
            }
        Constraints:
            - scheduled_date must be a non-empty string in "YYYY-MM-DD" format.
            - If event_id is provided, it is used as a filter; if it does not exist, simply yield no matches.
        """
        # Basic check for scheduled_date format: length == 10 and contains two '-'
        if not scheduled_date or not isinstance(scheduled_date, str) or len(scheduled_date) != 10 or scheduled_date.count('-') != 2:
            return { "success": False, "error": "Invalid or missing scheduled_date" }

        # Filtering
        if event_id:
            matching_activities = [
                activity for activity in self.activities.values()
                if activity["scheduled_date"] == scheduled_date and activity["event_id"] == event_id
            ]
        else:
            matching_activities = [
                activity for activity in self.activities.values()
                if activity["scheduled_date"] == scheduled_date
            ]

        return { "success": True, "data": matching_activities }

    def get_activity_by_id(self, activity_id: str) -> dict:
        """
        Retrieve the details of a specific activity by its activity_id.

        Args:
            activity_id (str): The unique identifier of the activity.

        Returns:
            dict: {
                "success": True,
                "data": ActivityInfo  # All information about the activity
            }
            or
            {
                "success": False,
                "error": "Activity not found"
            }

        Constraints:
            - None (query only; no state changes).
        """
        activity = self.activities.get(activity_id)
        if activity is None:
            return { "success": False, "error": "Activity not found" }
        return { "success": True, "data": activity }

    def get_activities_by_date_range(self, event_id: str, start_date: str, end_date: str) -> dict:
        """
        Retrieve all activities for a given event that are scheduled within the specified date range (inclusive).

        Args:
            event_id (str): ID of the parent event.
            start_date (str): Start date in "YYYY-MM-DD" format (inclusive).
            end_date (str): End date in "YYYY-MM-DD" format (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[ActivityInfo],   # List of activities matching criteria (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., event does not exist, invalid date range)
            }

        Constraints:
            - Event ID must exist.
            - start_date must be <= end_date.
            - Only include activities for this event within the date range.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        # Simple string comparison works due to YYYY-MM-DD format
        if start_date > end_date:
            return { "success": False, "error": "Invalid date range: start_date is after end_date" }

        # Retrieve all matching activities
        result = [
            activity for activity in self.activities.values()
            if activity["event_id"] == event_id and start_date <= activity["scheduled_date"] <= end_date
        ]

        return { "success": True, "data": result }

    def get_activities_by_location(self, location: str) -> dict:
        """
        Retrieve all activities scheduled in a particular location.

        Args:
            location (str): Location name or identifier.

        Returns:
            dict: {
               "success": True,
               "data": List[ActivityInfo]    # (possibly empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Location string must be non-empty.
            - Returns only activities whose 'location' attribute matches input.
        """
        if not location or not isinstance(location, str):
            return { "success": False, "error": "Invalid location input" }

        result = [
            act for act in self.activities.values()
            if act.get("location") == location
        ]
        return { "success": True, "data": result }

    def get_activity_resources(self, activity_id: str) -> dict:
        """
        List all detailed resource information assigned to a specific activity.

        Args:
            activity_id (str): The unique activity identifier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ResourceInfo]
                            # List of resource info assigned to the activity (empty if none)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": <error message>
                    }

        Constraints:
            - The activity_id must exist.
            - Only resources that still exist in the system are returned.
        """
        if activity_id not in self.activities:
            return { "success": False, "error": "Activity not found" }

        assigned_ids = self.activities[activity_id].get("assigned_resources", [])
        resources = [
            self.resources[res_id]
            for res_id in assigned_ids
            if res_id in self.resources
        ]
        return { "success": True, "data": resources }

    def get_resource_availability(self, resource_id: str) -> dict:
        """
        Retrieve the availability time slots for a specific resource.

        Args:
            resource_id (str): The unique identifier of the resource.

        Returns:
            dict:
                - If found: {
                    "success": True,
                    "data": List[str]  # List of availability time slots, e.g., ["2023-12-01 10:00-14:00", ...]
                  }
                - If not found: {
                    "success": False,
                    "error": "Resource not found"
                  }
        """
        resource = self.resources.get(resource_id)
        if resource is None:
            return { "success": False, "error": "Resource not found" }
    
        return { "success": True, "data": resource.get("availability", []) }


    def check_activity_time_conflicts(
        self,
        scheduled_date: str,
        start_time: str,
        end_time: str,
        location: str,
        assigned_resources: List[str],
        activity_id: Optional[str] = None
    ) -> dict:
        """
        Check for potential time/location/resource conflicts for a proposed activity schedule.

        Args:
            scheduled_date (str): Date of proposed activity ("YYYY-MM-DD").
            start_time (str): Start time ("HH:MM").
            end_time (str): End time ("HH:MM").
            location (str): Location of the activity.
            assigned_resources (List[str]): Resource IDs to assign.
            activity_id (str, optional): The activity being modified (to exclude from conflict checking).

        Returns:
            dict: {
                "success": True,
                "data": {
                    "location_conflicts": List[ActivityInfo],      # Activities in same location/date with overlapping times
                    "resource_conflicts": Dict[resource_id, List[ActivityInfo]]  # For each resource, list of conflicting activities
                }
            }
            or
            { "success": False, "error": str }
        Constraints:
            - Activities at the same location on the same date must not overlap in time.
            - Resources assigned to an activity must not be booked for overlapping activities.
            - Optionally, 'activity_id' can be provided to exclude from conflict checks (when editing).
        """

        def time_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
            # Times in "HH:MM"
            return not (end1 <= start2 or end2 <= start1)

        location_conflicts = []
        resource_conflicts: Dict[str, List[ActivityInfo]] = {res_id: [] for res_id in assigned_resources}

        for act in self.activities.values():
            if activity_id is not None and act["activity_id"] == activity_id:
                continue  # Exclude self

            if act["scheduled_date"] != scheduled_date:
                continue  # Wrong date

            # Check for location conflict
            if act["location"] == location:
                if time_overlap(start_time, end_time, act["start_time"], act["end_time"]):
                    location_conflicts.append(act)

            # Check for resource conflicts
            for res_id in assigned_resources:
                if res_id in act["assigned_resources"]:
                    if time_overlap(start_time, end_time, act["start_time"], act["end_time"]):
                        resource_conflicts[res_id].append(act)

        # Remove empty lists in resource_conflicts for clarity
        resource_conflicts = {k: v for k, v in resource_conflicts.items() if v}

        return {
            "success": True,
            "data": {
                "location_conflicts": location_conflicts,
                "resource_conflicts": resource_conflicts
            }
        }

    def add_event(
        self,
        event_id: str,
        name: str,
        description: str,
        start_date: str,
        end_date: str,
        location: str
    ) -> dict:
        """
        Create a new event in the system.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Name of the event.
            description (str): Description of the event.
            start_date (str): Event start date ("YYYY-MM-DD").
            end_date (str): Event end date ("YYYY-MM-DD").
            location (str): Location of the event.

        Returns:
            dict: {
                "success": True,
                "message": "Event <event_id> created successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - event_id must be unique.
            - start_date and end_date must be valid dates, and end_date >= start_date.
        """

        # Check for unique event_id
        if event_id in self.events:
            return {"success": False, "error": "event_id already exists"}

        # Basic input validation
        required = [event_id, name, description, start_date, end_date, location]
        if not all(required):
            return {"success": False, "error": "Missing required event attribute(s)"}

        # Date format and logical range checking
        try:
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return {"success": False, "error": "Date(s) must be in 'YYYY-MM-DD' format"}

        if end_dt < start_dt:
            return {"success": False, "error": "end_date cannot be before start_date"}

        # Store the event
        self.events[event_id] = {
            "event_id": event_id,
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "location": location
        }

        return {"success": True, "message": f"Event {event_id} created successfully"}

    def edit_event(
        self, 
        event_id: str, 
        name: str = None, 
        description: str = None, 
        start_date: str = None, 
        end_date: str = None, 
        location: str = None
    ) -> dict:
        """
        Modify details (name, description, start_date, end_date, location) of an existing event.

        Args:
            event_id (str): ID of the event to modify.
            name (str, optional): New event name.
            description (str, optional): New description.
            start_date (str, optional): New start date ("YYYY-MM-DD").
            end_date (str, optional): New end date ("YYYY-MM-DD").
            location (str, optional): New location string.

        Returns:
            dict: On success: { "success": True, "message": "Event updated successfully" }
                  On error: { "success": False, "error": "reason" }

        Constraints:
            - Event must exist.
            - If start_date or end_date are changed, all scheduled activities of this event must be within the new start/end range.
        """
        # 1. Check event existence
        event = self.events.get(event_id)
        if not event:
            return { "success": False, "error": "Event not found" }

        # 2. Determine what fields to update; nothing to do?
        if all(param is None for param in [name, description, start_date, end_date, location]):
            return { "success": True, "message": "No fields to update. Event unchanged." }

        # 3. Prepare new dates for constraint checking
        new_start = start_date if start_date is not None else event["start_date"]
        new_end = end_date if end_date is not None else event["end_date"]

        # 4. Validate date logic (ensure new_start <= new_end)
        if new_start > new_end:
            return { "success": False, "error": "Event start_date cannot be after end_date" }

        # 5. If event dates are changing, verify all activities remain in range
        for activity in self.activities.values():
            if activity["event_id"] == event_id:
                activity_date = activity["scheduled_date"]
                if not (new_start <= activity_date <= new_end):
                    return {
                        "success": False,
                        "error": (
                            f"Activity '{activity['name']}' scheduled on {activity_date} "
                            f"is outside new event date range {new_start} to {new_end}"
                        )
                    }

        # 6. Apply the updates
        if name is not None:
            event["name"] = name
        if description is not None:
            event["description"] = description
        if start_date is not None:
            event["start_date"] = start_date
        if end_date is not None:
            event["end_date"] = end_date
        if location is not None:
            event["location"] = location

        self.events[event_id] = event  # Save back (redundant for dict reference, but clear)

        return { "success": True, "message": "Event updated successfully" }

    def delete_event(self, event_id: str) -> dict:
        """
        Remove an event and all its activities from the system.

        Args:
            event_id (str): The unique identifier of the event to remove.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Event and associated activities deleted."}
                On failure:
                    {"success": False, "error": "Event does not exist."}

        Constraints:
            - If the event exists, all activities belonging to it (having event_id) are also removed.
            - No orphaned activities should remain.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist."}

        # Delete all associated activities
        activities_to_delete = [aid for aid, activity in self.activities.items() if activity["event_id"] == event_id]
        for aid in activities_to_delete:
            del self.activities[aid]

        # Delete the event
        del self.events[event_id]
        return {"success": True, "message": "Event and associated activities deleted."}

    def add_activity(
        self,
        activity_id: str,
        event_id: str,
        name: str,
        scheduled_date: str,
        start_time: str,
        end_time: str,
        location: str,
        assigned_resources: list,
        description: str
    ) -> dict:
        """
        Schedule a new activity under an event, with specified time, location, and resources.

        Args:
            activity_id (str): Unique activity identifier.
            event_id (str): Parent event ID.
            name (str): Activity name.
            scheduled_date (str): Date (YYYY-MM-DD).
            start_time (str): Start time (HH:MM).
            end_time (str): End time (HH:MM).
            location (str): Activity location.
            assigned_resources (list of str): List of resource_ids.
            description (str): Activity description.

        Returns:
            dict with "success": True/False and a "message"/"error".

        Constraints:
            - Activity IDs must be unique.
            - Provided event_id must exist.
            - scheduled_date must be within event's start_date and end_date (inclusive).
            - Resources and location must be available at scheduled time.
            - No overlap with other activities in the same location/resource.
            - All assigned_resources must exist.
        """

        # 1. Ensure unique activity_id
        if activity_id in self.activities:
            return {"success": False, "error": "Activity ID already exists."}

        # 2. Event existence check
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Parent event does not exist."}

        # 3. scheduled_date within event period
        try:
            date_fmt = "%Y-%m-%d"
            event_start = datetime.datetime.strptime(event["start_date"], date_fmt)
            event_end = datetime.datetime.strptime(event["end_date"], date_fmt)
            scheduled_dt = datetime.datetime.strptime(scheduled_date, date_fmt)
        except Exception:
            return {"success": False, "error": "Invalid date format."}

        if not (event_start <= scheduled_dt <= event_end):
            return {"success": False, "error": "Activity scheduled outside event's date range."}

        # 4. Validate time formatting and interval
        try:
            time_fmt = "%H:%M"
            st_time = datetime.datetime.strptime(start_time, time_fmt)
            en_time = datetime.datetime.strptime(end_time, time_fmt)
        except Exception:
            return {"success": False, "error": "Invalid time format."}

        if en_time <= st_time:
            return {"success": False, "error": "End time must be after start time."}

        # 5. Check assigned_resources exist
        for resource_id in assigned_resources:
            if resource_id not in self.resources:
                return {"success": False, "error": f"Resource '{resource_id}' does not exist."}

        # 6. Check for time conflicts at location and resources
        for act in self.activities.values():
            if act["scheduled_date"] != scheduled_date:
                continue

            # Check location conflict
            if act["location"] == location:
                existing_st = datetime.datetime.strptime(act["start_time"], time_fmt)
                existing_en = datetime.datetime.strptime(act["end_time"], time_fmt)
                # Overlap if intervals intersect
                if not (en_time <= existing_st or st_time >= existing_en):
                    return {"success": False, "error": "Time/location conflict with another activity."}

            # Check resource conflicts
            overlapping_resources = set(assigned_resources).intersection(set(act["assigned_resources"]))
            if overlapping_resources:
                existing_st = datetime.datetime.strptime(act["start_time"], time_fmt)
                existing_en = datetime.datetime.strptime(act["end_time"], time_fmt)
                if not (en_time <= existing_st or st_time >= existing_en):
                    return {"success": False, "error": f"Resource {list(overlapping_resources)[0]} has a time conflict."}

        # 7. Check resource availability
        # Assume resource["availability"] is a list of strings: "YYYY-MM-DD HH:MM-HH:MM"
        for resource_id in assigned_resources:
            resource = self.resources[resource_id]
            available = False
            for slot in resource.get("availability", []):
                try:
                    slot_date, slot_times = slot.split(" ")
                    slot_st, slot_en = slot_times.split("-")
                    slot_st_dt = datetime.datetime.strptime(slot_st, time_fmt)
                    slot_en_dt = datetime.datetime.strptime(slot_en, time_fmt)
                except Exception:
                    continue  # Skip invalid format slots

                if slot_date == scheduled_date and (st_time >= slot_st_dt and en_time <= slot_en_dt):
                    available = True
                    break
            if not available:
                return {"success": False, "error": f"Resource '{resource_id}' unavailable at scheduled time."}

        # 8. All constraints passed, add activity
        new_activity = {
            "activity_id": activity_id,
            "event_id": event_id,
            "name": name,
            "scheduled_date": scheduled_date,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "assigned_resources": assigned_resources[:],
            "description": description,
        }
        self.activities[activity_id] = new_activity

        return {"success": True, "message": "Activity scheduled successfully."}

    def edit_activity(
        self, 
        activity_id: str,
        name: str = None,
        scheduled_date: str = None,
        start_time: str = None,
        end_time: str = None,
        location: str = None,
        assigned_resources: list = None,
        description: str = None,
        event_id: str = None
    ) -> dict:
        """
        Modify the details, time, or resource assignments of an existing activity.

        Args:
            activity_id (str): ID of the activity to modify.
            name (str, optional): New name.
            scheduled_date (str, optional): "YYYY-MM-DD"
            start_time (str, optional): "HH:MM"
            end_time (str, optional): "HH:MM"
            location (str, optional): New location.
            assigned_resources (list of str, optional): List of resource_ids.
            description (str, optional): New description.
            event_id (str, optional): Change parent event.

        Returns:
            dict: {
              "success": True,
              "message": "Activity ... updated successfully."
            } or
            dict: {
              "success": False,
              "error": "Reason"
            }
        Constraints:
            - Activities must belong to an event.
            - Activities cannot be scheduled outside the event's start_date and end_date.
            - Locations/resources allocated to activities must be available at the time.
            - Activities on the same date and location/resource cannot overlap in time.
        """
        # 1. Existence check
        if activity_id not in self.activities:
            return {"success": False, "error": "Activity does not exist"}

        activity = self.activities[activity_id]
        old_event_id = activity["event_id"]

        # 2. Use the new values if supplied, else old
        updated_activity = {
            "activity_id": activity_id,
            "event_id": event_id if event_id is not None else activity["event_id"],
            "name": name if name is not None else activity["name"],
            "scheduled_date": scheduled_date if scheduled_date is not None else activity["scheduled_date"],
            "start_time": start_time if start_time is not None else activity["start_time"],
            "end_time": end_time if end_time is not None else activity["end_time"],
            "location": location if location is not None else activity["location"],
            "assigned_resources": assigned_resources if assigned_resources is not None else activity["assigned_resources"],
            "description": description if description is not None else activity["description"],
        }

        # 3. Check new parent event exists
        parent_event_id = updated_activity["event_id"]
        if parent_event_id not in self.events:
            return {"success": False, "error": "Parent event does not exist"}

        parent_event = self.events[parent_event_id]

        # 4. Scheduled date must be within event's dates
        event_start = parent_event["start_date"]
        event_end = parent_event["end_date"]
        sched_date = updated_activity["scheduled_date"]
        if sched_date < event_start or sched_date > event_end:
            return {"success": False, "error": "Activity must be scheduled within event's date range"}

        new_start = updated_activity["start_time"]
        new_end = updated_activity["end_time"]
        if new_start >= new_end:
            return {"success": False, "error": "Start time must be before end time"}

        # 5. If assigned_resources provided, check all exist
        for res_id in updated_activity["assigned_resources"]:
            if res_id not in self.resources:
                return {"success": False, "error": f"Assigned resource {res_id} does not exist"}

        # 6. Overlap checks
        for act in self.activities.values():
            if act["activity_id"] == activity_id:
                continue
            # List of possible conflict kinds:
            # (a) Same scheduled_date
            if act["scheduled_date"] != sched_date:
                continue
            # (b) Overlapping time
            other_start, other_end = act["start_time"], act["end_time"]
            if not (new_end <= other_start or new_start >= other_end):
                # (i) Same location
                if act["location"] == updated_activity["location"]:
                    return {"success": False, "error": "Time/location conflict with another activity"}
                # (ii) Resource conflict
                for res_id in updated_activity["assigned_resources"]:
                    if res_id in act["assigned_resources"]:
                        return {"success": False, "error": f"Resource {res_id} is already assigned at this time"}

        # 7. Resource availability check
        # (Basic check: is any event on same slot for this resource? Availability fields not deeply checked as format is ambiguous)
        # For a fuller check, the resource's own declared availabilities could be considered.
        # Here: All we can check with info at hand is "not double-booked" as above.

        # 8. All checks passed; update activity
        self.activities[activity_id] = updated_activity
        return {"success": True, "message": f"Activity {activity_id} updated successfully."}

    def delete_activity(self, activity_id: str) -> dict:
        """
        Remove an activity from an event.

        Args:
            activity_id (str): The ID of the activity to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Activity <activity_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Activity does not exist."
            }

        Constraints:
            - The activity to be deleted must exist.
            - Removes the activity from the system entirely.
            - Does not modify associated event or resources, but cleans up activity schedule.
        """
        if activity_id not in self.activities:
            return { "success": False, "error": "Activity does not exist." }

        del self.activities[activity_id]
        return { "success": True, "message": f"Activity {activity_id} deleted." }

    def assign_resource_to_activity(self, activity_id: str, resource_id: str) -> dict:
        """
        Assign a resource to an activity at its scheduled time.

        Args:
            activity_id (str): ID of the activity.
            resource_id (str): ID of the resource.

        Returns:
            dict: {
                "success": True,
                "message": "Resource assigned to activity."
            }
            or
            {
                "success": False,
                "error": str  # Error description.
            }

        Constraints:
            - Both IDs must exist.
            - Resource must be available for the entire timeslot of the activity.
            - Resource cannot be doubly-booked at overlapping times.
        """
        # Validate existence
        activity = self.activities.get(activity_id)
        if not activity:
            return {"success": False, "error": "Activity does not exist"}

        resource = self.resources.get(resource_id)
        if not resource:
            return {"success": False, "error": "Resource does not exist"}

        # Check if already assigned
        if resource_id in activity["assigned_resources"]:
            return {"success": True, "message": "Resource already assigned to activity."}

        # Parse activity timeslot
        act_date = activity["scheduled_date"]  # "YYYY-MM-DD"
        start_time = activity["start_time"]    # "HH:MM"
        end_time = activity["end_time"]        # "HH:MM"
        slot_start = f"{act_date} {start_time}"
        slot_end = f"{act_date} {end_time}"

        def times_overlap(start1, end1, start2, end2):
            return start1 < end2 and start2 < end1

        # Convert to comparable numbers (YYYYMMDDHHMM as integer for easy comparison)
        def slot_to_ints(slot):
            date, times = slot.split()
            h, m = times.split(":")
            dt = int(date.replace("-", ""))
            tm = int(h)*60 + int(m)
            return dt, tm

        act_dt, act_start_tm = slot_to_ints(slot_start)
        _, act_end_tm = slot_to_ints(slot_end)

        # Check the resource has at least one declared availability slot that fully covers the activity.
        available = False
        for avail in resource["availability"]:
            # Each avail: "YYYY-MM-DD HH:MM-HH:MM"
            try:
                parts = avail.split()
                av_date = parts[0]
                time_range = parts[1]
                av_start, av_end = time_range.split("-")
                av_slot_start = f"{av_date} {av_start}"
                av_slot_end = f"{av_date} {av_end}"
                av_dt, av_start_tm = slot_to_ints(av_slot_start)
                _, av_end_tm = slot_to_ints(av_slot_end)
                if av_dt != act_dt:
                    continue
                if act_start_tm >= av_start_tm and act_end_tm <= av_end_tm:
                    available = True
                    break
            except Exception:
                continue

        if not available:
            return {"success": False, "error": "Resource is not available for the entire activity timeslot"}

        # Assign resource
        activity["assigned_resources"].append(resource_id)

        return {"success": True, "message": "Resource assigned to activity."}

    def release_resource_from_activity(self, activity_id: str, resource_id: str) -> dict:
        """
        Remove a resource assignment from a specific activity.

        Args:
            activity_id (str): The ID of the activity.
            resource_id (str): The ID of the resource to be removed.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Resource released from activity" }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The activity must exist in the system.
            - The resource must exist in the system.
            - The resource must be currently assigned to the activity.
        """
        # Check if activity exists
        activity = self.activities.get(activity_id)
        if not activity:
            return { "success": False, "error": "Activity does not exist" }

        # Check if resource exists
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource does not exist" }

        # Check if resource is assigned to activity
        if resource_id not in activity["assigned_resources"]:
            return { "success": False, "error": "Resource is not assigned to this activity" }

        # Remove resource from assigned_resources
        activity["assigned_resources"] = [
            rid for rid in activity["assigned_resources"] if rid != resource_id
        ]
        # Persist the update (already in-place for the dict object)
        self.activities[activity_id] = activity

        return { "success": True, "message": "Resource released from activity" }

    def add_resource(self, resource_id: str, name: str, type: str, availability: list) -> dict:
        """
        Add a new resource to the system.

        Args:
            resource_id (str): Unique identifier for the resource.
            name (str): Human-readable name for the resource.
            type (str): Type of the resource (e.g., 'Room', 'Equipment', 'Staff').
            availability (List[str]): List of available time slots, e.g., ['2023-12-01 10:00-14:00', ...]

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Resource <resource_id> added successfully"
                }
            On failure:
                {
                    "success": False,
                    "error": error_message
                }
        Constraints:
            - resource_id must be unique across all resources.
        """
        if not isinstance(resource_id, str) or not resource_id:
            return { "success": False, "error": "Invalid or empty resource_id" }
        if resource_id in self.resources:
            return { "success": False, "error": f"Resource with ID {resource_id} already exists" }
        if not isinstance(name, str) or not name:
            return { "success": False, "error": "Invalid or empty name for resource" }
        if not isinstance(type, str) or not type:
            return { "success": False, "error": "Invalid or empty type for resource" }
        if not isinstance(availability, list):
            return { "success": False, "error": "Availability must be a list" }
        # No check on availability entry format, as it's not specified in detail

        self.resources[resource_id] = {
            "resource_id": resource_id,
            "name": name,
            "type": type,
            "availability": availability.copy()
        }
        return { "success": True, "message": f"Resource {resource_id} added successfully" }

    def edit_resource(
        self,
        resource_id: str,
        name: str = None,
        type: str = None,
        availability: list = None,
    ) -> dict:
        """
        Modify details or availability of a resource.

        Args:
            resource_id (str): The ID of the resource to edit.
            name (str, optional): New name for the resource.
            type (str, optional): New type for the resource.
            availability (List[str], optional): New availability list for the resource 
                                                (e.g., ["2024-06-12 09:00-17:00", ...]).

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Resource <resource_id> updated."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - resource_id must exist in system.
            - At least one attribute must be provided to update.
        """
        if resource_id not in self.resources:
            return {"success": False, "error": "Resource does not exist"}

        if name is None and type is None and availability is None:
            return {"success": False, "error": "No update attribute specified"}

        # Update attributes if supplied
        if name is not None:
            self.resources[resource_id]['name'] = name
        if type is not None:
            self.resources[resource_id]['type'] = type
        if availability is not None:
            self.resources[resource_id]['availability'] = availability

        return {"success": True, "message": f"Resource {resource_id} updated."}

    def delete_resource(self, resource_id: str) -> dict:
        """
        Remove a resource from the scheduling system, ensuring it is not assigned to any activity.

        Args:
            resource_id (str): The ID of the resource to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Resource <resource_id> deleted from the system."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Resource must exist in the resource pool.
            - Resource must NOT be assigned to any activity.
        """
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource does not exist." }

        # Check if the resource is assigned to any activity
        for activity in self.activities.values():
            if resource_id in activity.get("assigned_resources", []):
                return { 
                    "success": False, 
                    "error": f"Resource '{resource_id}' is currently assigned to an activity and cannot be deleted." 
                }

        del self.resources[resource_id]
        return { "success": True, "message": f"Resource '{resource_id}' deleted from the system." }


class EventManagementSchedulingSystem(BaseEnv):
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

    def get_event_by_name(self, **kwargs):
        return self._call_inner_tool('get_event_by_name', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_all_events(self, **kwargs):
        return self._call_inner_tool('list_all_events', kwargs)

    def get_activities_by_event_id(self, **kwargs):
        return self._call_inner_tool('get_activities_by_event_id', kwargs)

    def get_activities_on_date(self, **kwargs):
        return self._call_inner_tool('get_activities_on_date', kwargs)

    def get_activity_by_id(self, **kwargs):
        return self._call_inner_tool('get_activity_by_id', kwargs)

    def get_activities_by_date_range(self, **kwargs):
        return self._call_inner_tool('get_activities_by_date_range', kwargs)

    def get_activities_by_location(self, **kwargs):
        return self._call_inner_tool('get_activities_by_location', kwargs)

    def get_activity_resources(self, **kwargs):
        return self._call_inner_tool('get_activity_resources', kwargs)

    def get_resource_availability(self, **kwargs):
        return self._call_inner_tool('get_resource_availability', kwargs)

    def check_activity_time_conflicts(self, **kwargs):
        return self._call_inner_tool('check_activity_time_conflicts', kwargs)

    def add_event(self, **kwargs):
        return self._call_inner_tool('add_event', kwargs)

    def edit_event(self, **kwargs):
        return self._call_inner_tool('edit_event', kwargs)

    def delete_event(self, **kwargs):
        return self._call_inner_tool('delete_event', kwargs)

    def add_activity(self, **kwargs):
        return self._call_inner_tool('add_activity', kwargs)

    def edit_activity(self, **kwargs):
        return self._call_inner_tool('edit_activity', kwargs)

    def delete_activity(self, **kwargs):
        return self._call_inner_tool('delete_activity', kwargs)

    def assign_resource_to_activity(self, **kwargs):
        return self._call_inner_tool('assign_resource_to_activity', kwargs)

    def release_resource_from_activity(self, **kwargs):
        return self._call_inner_tool('release_resource_from_activity', kwargs)

    def add_resource(self, **kwargs):
        return self._call_inner_tool('add_resource', kwargs)

    def edit_resource(self, **kwargs):
        return self._call_inner_tool('edit_resource', kwargs)

    def delete_resource(self, **kwargs):
        return self._call_inner_tool('delete_resource', kwargs)
