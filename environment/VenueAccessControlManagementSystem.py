# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime
from dateutil import parser as dateparser
from datetime import datetime



class EntranceInfo(TypedDict):
    entrance_id: str
    name: str
    zone: str
    access_technology: str      # technology_id
    operational_hours: List[str]  # List of schedule_id
    status: str                 # e.g., 'open', 'closed', 'maintenance'

class AccessTechnologyInfo(TypedDict):
    technology_id: str
    name: str
    configuration_detail: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    entrance_id: str
    start_time: str
    end_time: str
    special_use_case: str       # e.g., 'event', 'maintenance', '' for regular

class PersonnelInfo(TypedDict):
    personnel_id: str
    name: str
    role: str
    authorized_entrances: List[str]  # List of entrance_id

class _GeneratedEnvImpl:
    def __init__(self):
        # Entrances: {entrance_id: EntranceInfo}
        self.entrances: Dict[str, EntranceInfo] = {}
        # Access Technologies: {technology_id: AccessTechnologyInfo}
        self.access_technologies: Dict[str, AccessTechnologyInfo] = {}
        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}
        # Personnel: {personnel_id: PersonnelInfo}
        self.personnel: Dict[str, PersonnelInfo] = {}

        # Constraints (see state_space_definition / rules):
        # - Entrance operational hours must not overlap with maintenance windows for the same entrance.
        # - Only authorized personnel can modify entrance configurations.
        # - Access technology assigned to an entrance must be compatible with its type.
        # - Entry points cannot be set to operational if the associated technology is offline or under maintenance.

    def get_entrance_by_name(self, name: str) -> dict:
        """
        Retrieve all metadata/details of an entrance given its name.

        Args:
            name (str): The name of the entrance.

        Returns:
            dict: {
                "success": True,
                "data": EntranceInfo  # Entrance details matching the name
            }
            or
            {
                "success": False,
                "error": str  # If no such entrance exists
            }

        Notes:
            - Assumes entrance names are unique. If multiple entrances have the same name, returns the first match.
        """
        for entrance in self.entrances.values():
            if entrance["name"] == name:
                return {"success": True, "data": entrance}
        return {"success": False, "error": "No entrance found with given name"}

    def get_entrance_by_id(self, entrance_id: str) -> dict:
        """
        Retrieve all details of an entrance by its entrance_id.

        Args:
            entrance_id (str): The unique identifier of the entrance.

        Returns:
            dict: {
                "success": True,
                "data": EntranceInfo,  # Full details if found
            }
            OR
            {
                "success": False,
                "error": str  # 'Entrance not found' if not present
            }

        Constraints:
            - No authorization or operational constraints apply for read-only querying.
        """
        entrance = self.entrances.get(entrance_id)
        if entrance is None:
            return {"success": False, "error": "Entrance not found"}
        return {"success": True, "data": entrance}

    def list_all_entrances(self) -> dict:
        """
        Retrieve a list of all entrance points (with full metadata) in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EntranceInfo]  # List may be empty if no entrances exist
            }
        """
        entrances_list = list(self.entrances.values())
        return {
            "success": True,
            "data": entrances_list
        }

    def get_access_technology_status(self, technology_id: str) -> dict:
        """
        Retrieve the status and configuration details of an access technology.

        Args:
            technology_id (str): The unique identifier of the access technology.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "technology_id": str,
                    "name": str,
                    "status": str,  # e.g., 'online', 'maintenance', or 'unknown' if not set.
                    "configuration_detail": str
                }
            }
            or
            {
                "success": False,
                "error": str  # Error message if technology does not exist.
            }

        Notes:
            - No modification of state; only querying.
            - If the 'status' attribute is missing, return "unknown" for status.
        """
        tech = self.access_technologies.get(technology_id)
        if not tech:
            return {
                "success": False,
                "error": "Access technology does not exist"
            }
        status = tech.get("status")
        if status is None:
            injected_status = getattr(self, "_get_access_technology_status_state", None)
            if isinstance(injected_status, str) and injected_status:
                status = injected_status
            elif isinstance(injected_status, dict):
                if isinstance(injected_status.get(technology_id), str):
                    status = injected_status[technology_id]
                elif isinstance(injected_status.get("status"), str):
                    status = injected_status["status"]
        if status is None:
            status = "unknown"
        return {
            "success": True,
            "data": {
                "technology_id": tech["technology_id"],
                "name": tech["name"],
                "status": status,
                "configuration_detail": tech["configuration_detail"]
            }
        }

    def get_access_technology_by_id(self, technology_id: str) -> dict:
        """
        Retrieve access technology details by technology_id.

        Args:
            technology_id (str): Unique identifier for the access technology.

        Returns:
            dict: {
                "success": True,
                "data": AccessTechnologyInfo,  # The complete info for the access technology
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Access technology not found"
            }

        Constraints:
            - technology_id must exist in the system.
        """
        tech = self.access_technologies.get(technology_id)
        if tech is None:
            return {"success": False, "error": "Access technology not found"}
        return {"success": True, "data": tech}

    def get_entrance_schedules(self, entrance_id: str) -> dict:
        """
        Retrieve the schedules currently attached to a given entrance.

        Args:
            entrance_id (str): The unique identifier for the entrance.

        Returns:
            dict: {
                "success": True,
                "data": List[ScheduleInfo],  # Schedules currently referenced by the entrance's operational_hours list
            }
            or
            {
                "success": False,
                "error": str  # Description if entrance does not exist
            }
        Constraints:
            - The given entrance_id must exist in the system.
        """
        if entrance_id not in self.entrances:
            return {"success": False, "error": "Entrance does not exist."}
    
        active_schedule_ids = set(self.entrances[entrance_id].get("operational_hours", []))
        schedules = [
            copy.deepcopy(self.schedules[schedule_id])
            for schedule_id in self.entrances[entrance_id].get("operational_hours", [])
            if schedule_id in self.schedules
            and self.schedules[schedule_id].get("entrance_id") == entrance_id
            and schedule_id in active_schedule_ids
        ]
        return {"success": True, "data": schedules}

    def list_maintenance_windows_for_entrance(self, entrance_id: str) -> dict:
        """
        Get all maintenance-type schedules for a specific entrance.

        Args:
            entrance_id (str): Unique identifier of the entrance.

        Returns:
            dict: {
                "success": True,
                "data": List[ScheduleInfo]  # List of maintenance windows (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Entrance does not exist"
            }

        Constraints:
            - Entrance with the specified ID must exist.
            - Only schedules linked to the specified entrance and with special_use_case == "maintenance" are returned.
        """
        if entrance_id not in self.entrances:
            return { "success": False, "error": "Entrance does not exist" }

        maintenance_windows = [
            sched for sched in self.schedules.values()
            if sched["entrance_id"] == entrance_id and sched["special_use_case"] == "maintenance"
        ]

        return { "success": True, "data": maintenance_windows }

    def check_schedule_overlap(
        self, 
        entrance_id: str, 
        proposed_start_time: str, 
        proposed_end_time: str
    ) -> dict:
        """
        Check if the proposed operational period for an entrance overlaps with any of its maintenance windows.

        Args:
            entrance_id (str): The ID of the entrance to check against.
            proposed_start_time (str): The start time of the proposed period (ISO 8601 or comparable datetime string).
            proposed_end_time (str): The end time of the proposed period.

        Returns:
            dict:
                {
                    "success": True,
                    "overlaps": List[ScheduleInfo]  # All maintenance schedules that overlap with the proposed time
                }
            or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Entrance must exist.
            - Checks only against schedules with special_use_case == 'maintenance' for the given entrance.
            - If times overlap, the corresponding maintenance windows are returned.
        """
        if entrance_id not in self.entrances:
            return { "success": False, "error": "Entrance ID not found" }
    
        # Gather all maintenance windows for this entrance
        maintenance_schedules = [
            sched for sched in self.schedules.values()
            if sched["entrance_id"] == entrance_id and sched["special_use_case"] == "maintenance"
        ]

        # Helper for overlap. NOTE: assumes consistent and comparable time format (e.g. ISO)
        def times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
            # Overlap exists unless one ends before the other starts
            return not (end1 <= start2 or end2 <= start1)
    
        overlaps = []
        for sched in maintenance_schedules:
            if times_overlap(
                proposed_start_time, proposed_end_time,
                sched["start_time"], sched["end_time"]
            ):
                overlaps.append(sched)
    
        return { "success": True, "overlaps": overlaps }

    def get_personnel_by_id(self, personnel_id: str) -> dict:
        """
        Retrieve personnel details, including their role and authorized entrances.

        Args:
            personnel_id (str): The unique identifier of the personnel.

        Returns:
            dict: 
              - On success: {"success": True, "data": PersonnelInfo}
              - On failure: {"success": False, "error": "Personnel not found"}

        Constraints:
            - personnel_id must exist in the system.
        """
        personnel = self.personnel.get(personnel_id)
        if not personnel:
            return {"success": False, "error": "Personnel not found"}
        return {"success": True, "data": personnel}

    def verify_personnel_authorization(self, personnel_id: str, entrance_id: str) -> dict:
        """
        Check if the given personnel is authorized to modify the specified entrance.

        Args:
            personnel_id (str): ID of the personnel to check.
            entrance_id (str): ID of the entrance in question.

        Returns:
            dict:
                On success:
                    { "success": True, "data": True }  # if authorized
                    { "success": True, "data": False } # if not authorized
                On error:
                    { "success": False, "error": "<reason>" }
        Constraints:
            - Personnel must exist in the system.
            - Entrance must exist in the system.
            - Authorization is checked by whether entrance_id is in personnel['authorized_entrances'].
        """
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel not found" }
        if entrance_id not in self.entrances:
            return { "success": False, "error": "Entrance not found" }
        personnel_info = self.personnel[personnel_id]
        is_authorized = entrance_id in personnel_info.get("authorized_entrances", [])
        return { "success": True, "data": is_authorized }

    def get_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Retrieve full details of a schedule given its schedule_id.

        Args:
            schedule_id (str): The unique identifier for the schedule.

        Returns:
            dict: {
                "success": True,
                "data": ScheduleInfo
            }
            or
            {
                "success": False,
                "error": "Schedule not found"
            }
    
        Constraints:
            - Will only succeed if the schedule exists in the system.
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return { "success": False, "error": "Schedule not found" }
        return { "success": True, "data": schedule }

    def update_entrance_operational_hours(
        self,
        personnel_id: str,
        entrance_id: str,
        new_operational_schedule_ids: list
    ) -> dict:
        """
        Modify the list of operational schedules for a specified entrance. Replaces the current list
        with the provided list of schedule IDs. Only authorized personnel can modify.

        Args:
            personnel_id (str): The staff member attempting the modification.
            entrance_id (str): The target entrance's unique identifier.
            new_operational_schedule_ids (List[str]): The new set of operational schedule IDs to assign.

        Returns:
            dict: {
                'success': True, 'message': str    # if schedules updated
            }
            or
            dict: {
                'success': False, 'error': str     # on failure, with error reason
            }

        Constraints:
            - Only authorized personnel for the entrance may modify operational hours.
            - All new schedule IDs must exist and belong to the same entrance.
            - Proposed operational schedules must not overlap with maintenance windows.
        """
        # Check entrance exists
        if entrance_id not in self.entrances:
            return {"success": False, "error": "Entrance does not exist."}
        # Check personnel exists
        if personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel does not exist."}
        # Authorization check
        if entrance_id not in self.personnel[personnel_id]["authorized_entrances"]:
            return {"success": False, "error": "Personnel not authorized for this entrance."}
        # Validate each schedule
        operational_schedules = []
        for sid in new_operational_schedule_ids:
            sched = self.schedules.get(sid)
            if not sched:
                return {"success": False, "error": f"Schedule '{sid}' not found."}
            if sched["entrance_id"] != entrance_id:
                return {"success": False, "error": f"Schedule '{sid}' is not for the specified entrance."}
            if sched["special_use_case"] == "maintenance":
                return {"success": False, "error": "Cannot use maintenance window as operational schedule."}
            operational_schedules.append(sched)
        # Gather all maintenance windows for entrance
        maintenance_schedules = [
            s for s in self.schedules.values()
            if s["entrance_id"] == entrance_id and s["special_use_case"] == "maintenance"
        ]
        # Check for time overlap between each operational schedule and every maintenance window
        def time_overlap(s1, s2):
            # Assumes format "HH:MM" or "YYYY-MM-DD HH:MM"
            return not (s1["end_time"] <= s2["start_time"] or s1["start_time"] >= s2["end_time"])
        for op_sched in operational_schedules:
            for mw_sched in maintenance_schedules:
                if time_overlap(op_sched, mw_sched):
                    return {
                        "success": False,
                        "error": (
                            f"Operational schedule {op_sched['schedule_id']} "
                            f"overlaps maintenance window {mw_sched['schedule_id']}."
                        )
                    }
        # All checks passed, update entrance's operational hours
        self.entrances[entrance_id]["operational_hours"] = new_operational_schedule_ids
        return {
            "success": True,
            "message": f"Operational schedules for entrance '{entrance_id}' updated."
        }

    def set_entrance_status(self, entrance_id: str, new_status: str, personnel_id: str) -> dict:
        """
        Change the status of an entrance (e.g., 'open', 'closed', 'maintenance'), 
        ensuring that only authorized personnel can make changes and that relevant 
        technology/scheduling constraints are enforced.

        Args:
            entrance_id (str): The ID of the entrance to update.
            new_status (str): The new status ('open', 'closed', 'maintenance', ...).
            personnel_id (str): The ID of the personnel requesting the operation.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Status changed to <new_status> for entrance <entrance_id>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only authorized personnel may modify entrance configuration.
            - Cannot set status to 'open' unless associated technology is online/operational.
            - Cannot set status to 'open' if any active maintenance windows overlap for the entrance.
        """
        # Validate entrance existence
        entrance = self.entrances.get(entrance_id)
        if not entrance:
            return {"success": False, "error": "Entrance does not exist."}

        # Validate personnel
        personnel = self.personnel.get(personnel_id)
        if not personnel:
            return {"success": False, "error": "Personnel does not exist."}

        if entrance_id not in personnel.get("authorized_entrances", []):
            return {"success": False, "error": "Personnel not authorized for this entrance."}

        recognized_statuses = {"open", "closed", "maintenance"}
        if new_status not in recognized_statuses:
            return {"success": False, "error": f"Unrecognized status: {new_status}."}

        # Additional constraints only for 'open'
        if new_status == "open":
            # Check that access technology is functioning
            tech_id = entrance.get("access_technology")
            if not tech_id or tech_id not in self.access_technologies:
                return {"success": False, "error": "Associated access technology missing or invalid."}

            # Use internal call to get status of access technology (assuming method exists or is a status field)
            tech_status = None
            # Assume that get_access_technology_status returns {"success": ..., "status": ...}
            if hasattr(self, "get_access_technology_status"):
                info = self.get_access_technology_status(tech_id)
                if info.get("success"):
                    tech_status = info.get("data", {}).get("status")
                else:
                    return {"success": False, "error": f"Cannot determine access technology status: {info.get('error', '')}"}
            else:
                # Fallback or legacy: Check if tech info has a 'status' field
                tech_info = self.access_technologies.get(tech_id, {})
                tech_status = tech_info.get("status")
                if tech_status is None:
                    return {"success": False, "error": "Could not retrieve technology status."}

            if tech_status not in ("online", "operational"):
                return {"success": False, "error": "Access technology is not operational or is under maintenance."}

            # Check for active maintenance windows (if any maintenance schedule overlaps now)

            now = datetime.now()
            for sched_id in entrance.get("operational_hours", []):
                sched = self.schedules.get(sched_id)
                if sched and sched.get("special_use_case") == "maintenance":
                    try:
                        start = dateparser.parse(sched["start_time"])
                        end = dateparser.parse(sched["end_time"])
                        if start <= now <= end:
                            return {"success": False, "error": "Entrance is under a scheduled maintenance window."}
                    except Exception:
                        # If schedule time data is malformed, skip/ignore the check for this schedule
                        continue

        # All checks passed, set status
        entrance["status"] = new_status
        self.entrances[entrance_id] = entrance

        return {"success": True, "message": f"Status changed to {new_status} for entrance {entrance_id}"}

    def add_schedule_to_entrance(
        self,
        entrance_id: str,
        schedule_info: dict,
        personnel_id: str
    ) -> dict:
        """
        Add a new schedule period (for operation or special use) to a specific entrance.

        Args:
            entrance_id (str): Target entrance to update.
            schedule_info (dict): Fields: schedule_id, entrance_id (should match arg), start_time (HH:MM), end_time (HH:MM), special_use_case.
            personnel_id (str): The personnel requesting the addition (for authorization).

        Returns:
            dict: {
                "success": True,
                "message": "Schedule added to entrance"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints enforced:
            - Entrance must exist.
            - Personnel must exist and be authorized for this entrance.
            - New schedule_id must be unique.
            - schedule_info["entrance_id"] must match given entrance_id.
            - For non-maintenance schedules, must not overlap maintenance windows for this entrance.
        """
        # Check existence
        if entrance_id not in self.entrances:
            return { "success": False, "error": "Entrance does not exist" }
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel does not exist" }
        # Authorization
        if entrance_id not in self.personnel[personnel_id]["authorized_entrances"]:
            return { "success": False, "error": "Personnel not authorized for this entrance" }
        # Uniqueness of schedule_id
        schedule_id = schedule_info.get("schedule_id")
        if not schedule_id or schedule_id in self.schedules:
            return { "success": False, "error": "Schedule ID already exists or is missing" }
        # Check entrance_id matches between arguments and schedule_info
        if schedule_info.get("entrance_id") != entrance_id:
            return { "success": False, "error": "schedule_info's entrance_id does not match" }

        # Parse times for comparison (assume 'HH:MM' 24hr.)
        new_start = schedule_info.get("start_time")
        new_end = schedule_info.get("end_time")
        # Validation of time format
        try:
            fmt = "%H:%M"
            new_start_dt = datetime.strptime(new_start, fmt)
            new_end_dt = datetime.strptime(new_end, fmt)
        except Exception:
            return { "success": False, "error": "Invalid start_time or end_time format (should be HH:MM)" }

        # If not maintenance, check overlap with maintenance schedules on same entrance
        if schedule_info.get("special_use_case", "") != "maintenance":
            for s in self.schedules.values():
                if s["entrance_id"] == entrance_id and s.get("special_use_case", "") == "maintenance":
                    # Parse maintenance window times
                    try:
                        maint_start_dt = datetime.strptime(s["start_time"], fmt)
                        maint_end_dt = datetime.strptime(s["end_time"], fmt)
                    except Exception:
                        continue
                    # Test overlap: (start1 < end2) and (start2 < end1)
                    if (new_start_dt < maint_end_dt) and (maint_start_dt < new_end_dt):
                        return { 
                            "success": False, 
                            "error": "Schedule overlaps with a maintenance window"
                        }

        # Everything OK, add
        self.schedules[schedule_id] = schedule_info
        self.entrances[entrance_id]["operational_hours"].append(schedule_id)
        return {
            "success": True,
            "message": "Schedule added to entrance"
        }

    def remove_schedule_from_entrance(self, personnel_id: str, entrance_id: str, schedule_id: str) -> dict:
        """
        Remove an existing schedule from a specific entrance.

        Args:
            personnel_id (str): ID of the personnel attempting the operation.
            entrance_id (str): ID of the entrance.
            schedule_id (str): ID of the schedule to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule <schedule_id> removed from entrance <entrance_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only authorized personnel can modify entrance configurations.
            - Schedule must be associated with the specified entrance.
        """
        # Check personnel authorization
        personnel = self.personnel.get(personnel_id)
        if personnel is None:
            return {"success": False, "error": "Personnel not found"}
        if entrance_id not in personnel.get("authorized_entrances", []):
            return {"success": False, "error": "Personnel not authorized for this entrance"}
    
        # Check entrance and schedule existence
        entrance = self.entrances.get(entrance_id)
        if entrance is None:
            return {"success": False, "error": "Entrance not found"}
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule not found"}

        # Schedule must be part of entrance's operational_hours
        if schedule_id not in entrance.get("operational_hours", []):
            return {"success": False, "error": "Schedule not associated with this entrance"}

        # Perform removal from the entrance's active schedule list.
        entrance["operational_hours"].remove(schedule_id)

        # Keep schedule storage consistent with the entrance view so subsequent reads
        # do not expose schedules that were explicitly removed from the entrance.
        schedule_info = self.schedules.get(schedule_id)
        if schedule_info and schedule_info.get("entrance_id") == entrance_id:
            del self.schedules[schedule_id]

        return {
            "success": True,
            "message": f"Schedule {schedule_id} removed from entrance {entrance_id}"
        }

    def assign_access_technology_to_entrance(
        self,
        entrance_id: str,
        technology_id: str,
        personnel_id: str
    ) -> dict:
        """
        Assign a specified access technology to a given entrance,
        enforcing compatibility and personnel authorization constraints.

        Args:
            entrance_id (str): The identifier of the entrance to update.
            technology_id (str): The identifier of the access technology to assign.
            personnel_id (str): The identifier of the personnel requesting the assignment.

        Returns:
            dict: {
                "success": True,
                "message": "Access technology assigned to entrance successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only authorized personnel can modify entrance configurations.
            - Access technology assigned must be compatible with entrance type (to the extent info is available).
        """
        # Existence checks
        if entrance_id not in self.entrances:
            return { "success": False, "error": "Entrance not found." }
        if technology_id not in self.access_technologies:
            return { "success": False, "error": "Access technology not found." }
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel not found." }

        # Authorization check
        personnel_info = self.personnel[personnel_id]
        if entrance_id not in personnel_info.get("authorized_entrances", []):
            return { "success": False, "error": "Personnel not authorized to modify this entrance." }

        # Compatibility check (Stub: always return True as we lack specifics)
        # Here you might check whether the technology is compatible with entrance type/zone/etc.
        # Example logic placeholder:
        # compatible = self.is_technology_compatible_with_entrance(technology_id, entrance_id)
        compatible = True
        if not compatible:
            return { "success": False, "error": "Technology is not compatible with entrance type." }

        # State update
        self.entrances[entrance_id]["access_technology"] = technology_id

        return {
            "success": True,
            "message": f"Access technology '{technology_id}' assigned to entrance '{entrance_id}' successfully."
        }

    def set_access_technology_status(self, technology_id: str, new_status: str) -> dict:
        """
        Set the operational status of an access technology (e.g., 'maintenance', 'offline', 'online').

        Args:
            technology_id (str): ID of the access technology to update.
            new_status (str): The new operational status to set. Should be one of {'online', 'offline', 'maintenance'}.

        Returns:
            dict: {
                "success": True,
                "message": str,   # Summary of operation if successful,
            }
            or
            {
                "success": False,
                "error": str      # Error message if operation fails
            }

        Constraints:
            - The access technology must exist in the system.
            - Status must be one of the recognized strings.
            - This operation only changes technology status; impacts on entrances are handled elsewhere.
        """
        allowed_statuses = {"online", "offline", "maintenance"}
        at = self.access_technologies.get(technology_id)
        if not at:
            return { "success": False, "error": "Access technology not found" }
        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status value" }
        # Add 'status' field to AccessTechnology if not present
        if "status" not in at:
            at["status"] = "online"  # default initial status if missing
        at["status"] = new_status
        self.access_technologies[technology_id] = at
        return {
            "success": True,
            "message": f"Access technology status set to {new_status}."
        }

    def bulk_update_entrance_schedules(self, personnel_id: str, updates: list) -> dict:
        """
        Simultaneously update operational schedules for multiple entrances.

        Args:
            personnel_id (str): The identifier for the personnel trying to make the change.
            updates (list): Each element is a dict: {
                "entrance_id": str,
                "schedule_ids": List[str]
            }

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Bulk update complete for all entrances"}
                On failure:
                    {"success": False, "error": "reason"}
        Constraints:
            - Only authorized personnel can modify entrance configurations.
            - Schedule IDs must exist, belong to the correct entrance, and not overlap with maintenance for that entrance.
            - All entrances must exist.
            - No partial updates; if any error occurs with any update, no changes are applied.
        """
        # Step 1: Personnel check
        personnel = self.personnel.get(personnel_id)
        if not personnel:
            return {"success": False, "error": "Personnel not found"}

        # Collect entrance_ids to update and check authorizations
        entrance_ids_to_update = [entry.get("entrance_id") for entry in updates]
        for eid in entrance_ids_to_update:
            if eid not in self.entrances:
                return {"success": False, "error": f"Entrance not found: {eid}"}
            if eid not in personnel["authorized_entrances"]:
                return {"success": False, "error": f"Personnel not authorized for entrance: {eid}"}

        # Step 2: Validate all schedule IDs, schedule/entrance association, and constraints
        for entry in updates:
            eid = entry.get("entrance_id")
            schedule_ids = entry.get("schedule_ids", [])
            # Ensure all schedule_ids exist and belong to this entrance
            for sid in schedule_ids:
                sched = self.schedules.get(sid)
                if not sched:
                    return {"success": False, "error": f"Schedule not found: {sid}"}
                if sched["entrance_id"] != eid:
                    return {"success": False, "error": f"Schedule {sid} does not belong to entrance {eid}"}

            # Constraint: No operational/maintenance overlap for this entrance
            # Gather maintenance intervals for entrance
            maintenance_scheds = [
                self.schedules[sid] for sid in self.schedules
                if self.schedules[sid]["entrance_id"] == eid and
                   self.schedules[sid]["special_use_case"] == "maintenance"
            ]
            maintenance_intervals = [
                (ms['start_time'], ms['end_time']) for ms in maintenance_scheds
            ]
            # Gather operational intervals from new schedule_ids (not maintenance)
            operational_intervals = []
            for sid in schedule_ids:
                sched = self.schedules[sid]
                if sched["special_use_case"] != "maintenance":
                    operational_intervals.append((sched["start_time"], sched["end_time"], sid))

            # Check for overlap (start1 < end2 and start2 < end1 means overlap)
            for op_start, op_end, op_sid in operational_intervals:
                for m_start, m_end in maintenance_intervals:
                    if (op_start < m_end) and (m_start < op_end):
                        return {
                            "success": False,
                            "error": f"Operational schedule {op_sid} for entrance {eid} overlaps with maintenance window"
                        }

        # Step 3: All checks passed; perform updates
        for entry in updates:
            eid = entry["entrance_id"]
            self.entrances[eid]["operational_hours"] = entry["schedule_ids"]

        return {"success": True, "message": "Bulk update complete for all entrances"}

    def create_maintenance_window(
        self, 
        personnel_id: str, 
        entrance_id: str, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """
        Add a new maintenance window (schedule) to a specific entrance.

        Args:
            personnel_id (str): The ID of personnel requesting the operation.
            entrance_id (str): The entrance to add the maintenance window.
            start_time (str): Start time in ISO 8601 format.
            end_time (str): End time in ISO 8601 format.

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
            - Only authorized personnel can create maintenance windows for an entrance.
            - The maintenance window must not overlap with the entrance's operational hours.
            - Entrance and personnel must exist.
            - start_time must be before end_time.
        """
        # Check personnel existence
        if personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel does not exist."}

        if entrance_id not in self.entrances:
            return {"success": False, "error": "Entrance does not exist."}

        personnel = self.personnel[personnel_id]
        if entrance_id not in personnel["authorized_entrances"]:
            return {"success": False, "error": "Personnel not authorized for this entrance."}

        # Check time format and order (assume ISO8601 string, compare as strings or parse, here we use string for simplicity)
        if start_time >= end_time:
            return {"success": False, "error": "Start time must be before end time."}

        entrance = self.entrances[entrance_id]

        # Check overlap with operational hours (schedules of this entrance with special_use_case='')
        for sched_id in entrance["operational_hours"]:
            sched = self.schedules.get(sched_id)
            if sched is None:
                continue
            # Only compare to regular hours, not to other maintenance windows
            if sched["special_use_case"] not in ("", "none"):
                continue
            # Check overlap
            # overlap if (a_start < b_end and b_start < a_end)
            if (start_time < sched["end_time"]) and (sched["start_time"] < end_time):
                return {
                    "success": False,
                    "error": "Maintenance window overlaps with an operational schedule."
                }

        # Generate a unique schedule_id (e.g. "mnt-<entrance_id>-<N>")
        idx = 1
        while True:
            schedule_id = f"mnt-{entrance_id}-{idx}"
            if schedule_id not in self.schedules:
                break
            idx += 1

        # Create the maintenance schedule
        new_schedule = {
            "schedule_id": schedule_id,
            "entrance_id": entrance_id,
            "start_time": start_time,
            "end_time": end_time,
            "special_use_case": "maintenance"
        }

        # Add to self.schedules
        self.schedules[schedule_id] = new_schedule
        # Optionally add to entrance's operational_hours (assume all schedules, regardless of use case, are tracked there)
        self.entrances[entrance_id]["operational_hours"].append(schedule_id)

        return {
            "success": True,
            "message": f"Maintenance window created for entrance {entrance_id}."
        }

    def remove_maintenance_window(
        self, 
        personnel_id: str, 
        entrance_id: str, 
        schedule_id: str
    ) -> dict:
        """
        Remove a maintenance schedule from a specific entrance.

        Args:
            personnel_id (str): The ID of personnel attempting the operation (must be authorized).
            entrance_id (str): The entrance from which to remove the maintenance schedule.
            schedule_id (str): The schedule (maintenance window) to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance window removed from entrance."
            }
            OR
            {
                "success": False,
                "error": <explanation>
            }

        Constraints:
            - Only authorized personnel can modify entrance configurations.
            - Schedule must exist, be linked to the entrance, and be of 'maintenance' use case.
            - Schedule should be removed from both entrance's operational_hours and the system's schedules.
        """
        # Check personnel
        personnel = self.personnel.get(personnel_id)
        if not personnel:
            return { "success": False, "error": "Personnel not found." }
        if entrance_id not in personnel["authorized_entrances"]:
            return { "success": False, "error": "Personnel is not authorized for this entrance." }

        # Check entrance
        entrance = self.entrances.get(entrance_id)
        if not entrance:
            return { "success": False, "error": "Entrance not found." }

        # Check schedule
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return { "success": False, "error": "Schedule not found." }
        if schedule["entrance_id"] != entrance_id:
            return { "success": False, "error": "Schedule does not belong to this entrance." }
        if schedule.get("special_use_case", "") != "maintenance":
            return { "success": False, "error": "Schedule is not a maintenance window." }
        if schedule_id in entrance["operational_hours"]:
            entrance["operational_hours"].remove(schedule_id)
        # Remove the schedule entirely from the schedules store
        del self.schedules[schedule_id]

        return { "success": True, "message": "Maintenance window removed from entrance." }


class VenueAccessControlManagementSystem(BaseEnv):
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
            if key == "get_access_technology_status":
                setattr(env, "_get_access_technology_status_state", copy.deepcopy(value))
                continue
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

    def get_entrance_by_name(self, **kwargs):
        return self._call_inner_tool('get_entrance_by_name', kwargs)

    def get_entrance_by_id(self, **kwargs):
        return self._call_inner_tool('get_entrance_by_id', kwargs)

    def list_all_entrances(self, **kwargs):
        return self._call_inner_tool('list_all_entrances', kwargs)

    def get_access_technology_status(self, **kwargs):
        return self._call_inner_tool('get_access_technology_status', kwargs)

    def get_access_technology_by_id(self, **kwargs):
        return self._call_inner_tool('get_access_technology_by_id', kwargs)

    def get_entrance_schedules(self, **kwargs):
        return self._call_inner_tool('get_entrance_schedules', kwargs)

    def list_maintenance_windows_for_entrance(self, **kwargs):
        return self._call_inner_tool('list_maintenance_windows_for_entrance', kwargs)

    def check_schedule_overlap(self, **kwargs):
        return self._call_inner_tool('check_schedule_overlap', kwargs)

    def get_personnel_by_id(self, **kwargs):
        return self._call_inner_tool('get_personnel_by_id', kwargs)

    def verify_personnel_authorization(self, **kwargs):
        return self._call_inner_tool('verify_personnel_authorization', kwargs)

    def get_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_id', kwargs)

    def update_entrance_operational_hours(self, **kwargs):
        return self._call_inner_tool('update_entrance_operational_hours', kwargs)

    def set_entrance_status(self, **kwargs):
        return self._call_inner_tool('set_entrance_status', kwargs)

    def add_schedule_to_entrance(self, **kwargs):
        return self._call_inner_tool('add_schedule_to_entrance', kwargs)

    def remove_schedule_from_entrance(self, **kwargs):
        return self._call_inner_tool('remove_schedule_from_entrance', kwargs)

    def assign_access_technology_to_entrance(self, **kwargs):
        return self._call_inner_tool('assign_access_technology_to_entrance', kwargs)

    def set_access_technology_status(self, **kwargs):
        return self._call_inner_tool('set_access_technology_status', kwargs)

    def bulk_update_entrance_schedules(self, **kwargs):
        return self._call_inner_tool('bulk_update_entrance_schedules', kwargs)

    def create_maintenance_window(self, **kwargs):
        return self._call_inner_tool('create_maintenance_window', kwargs)

    def remove_maintenance_window(self, **kwargs):
        return self._call_inner_tool('remove_maintenance_window', kwargs)
