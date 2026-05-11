# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class FacilityInfo(TypedDict):
    facility_id: str
    name: str
    type: str
    location: str
    current_condition: str

class MaintenanceTaskInfo(TypedDict):
    task_id: str
    facility_id: str
    task_type: str
    scheduled_time: str
    status: str
    assigned_personnel_id: str

class MaintenanceEventInfo(TypedDict):
    event_id: str
    task_id: str
    facility_id: str
    completed_time: str
    performed_by_personnel_id: str

class PersonnelInfo(TypedDict):
    personnel_id: str
    name: str
    role: str
    availability_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Facility Maintenance Management System State:
        - facilities: Tracks all physical assets (Facility).
        - maintenance_tasks: Tracks scheduled/planned work (MaintenanceTask).
        - maintenance_events: Records historical/completed maintenance (MaintenanceEvent).
        - personnel: Staff members and their availability (Personnel).
        """

        # Facilities: {facility_id: FacilityInfo}
        self.facilities: Dict[str, FacilityInfo] = {}

        # Maintenance Tasks: {task_id: MaintenanceTaskInfo}
        self.maintenance_tasks: Dict[str, MaintenanceTaskInfo] = {}

        # Maintenance Events: {event_id: MaintenanceEventInfo}
        self.maintenance_events: Dict[str, MaintenanceEventInfo] = {}

        # Personnel: {personnel_id: PersonnelInfo}
        self.personnel: Dict[str, PersonnelInfo] = {}

        # Constraints:
        # - MaintenanceTask must reference a valid Facility.
        # - Only available Personnel can be assigned to a MaintenanceTask.
        # - MaintenanceEvent can only be created for scheduled MaintenanceTasks.
        # - Task completion timestamps must be recorded accurately for historical queries.
        # - Each MaintenanceEvent is associated with exactly one MaintenanceTask and Facility.

    def get_facility_by_name(self, name: str) -> dict:
        """
        Retrieve detailed info for a facility using its name.

        Args:
            name (str): The name of the facility to search for (e.g., 'swimming pool').

        Returns:
            dict: 
                {
                    "success": True,
                    "data": FacilityInfo,   # facility details if found
                }
                or
                {
                    "success": False,
                    "error": str            # reason, e.g., "Facility not found"
                }
        """
        for facility in self.facilities.values():
            if facility["name"] == name:
                return {"success": True, "data": facility}
        return {"success": False, "error": "Facility not found"}

    def list_facilities_by_type(self, facility_type: str) -> dict:
        """
        Retrieve all facilities with the given type.

        Args:
            facility_type (str): The facility type to filter by (e.g. 'building', 'pool', 'equipment').

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[FacilityInfo]  # All matching facilities; possibly empty
                }

        Constraints:
            - No constraints other than matching 'type' field.
            - If no facilities found, "data" will be empty.
        """
        if not isinstance(facility_type, str) or not facility_type.strip():
            # Consider an empty or non-string input as invalid
            return { "success": False, "error": "Facility type must be a non-empty string." }

        result = [
            facility for facility in self.facilities.values()
            if facility["type"] == facility_type
        ]
        return { "success": True, "data": result }

    def get_facility_by_id(self, facility_id: str) -> dict:
        """
        Retrieve facility information using its unique ID.

        Args:
            facility_id (str): The unique identifier of the facility to retrieve.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": FacilityInfo  # All details of the facility
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Facility not found"
                    }

        Constraints:
            - Facility must exist in the system (lookup by facility_id).
        """
        facility = self.facilities.get(facility_id)
        if facility is None:
            return { "success": False, "error": "Facility not found" }
        return { "success": True, "data": facility }

    def list_tasks_for_facility(self, facility_id: str) -> dict:
        """
        List all maintenance tasks (scheduled or completed) for a specific facility.

        Args:
            facility_id (str): The ID of the facility whose tasks are to be listed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MaintenanceTaskInfo],  # List of tasks for this facility (possibly empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., facility not found)
                    }

        Constraints:
            - The specified facility_id must exist in the system.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        tasks = [
            task_info for task_info in self.maintenance_tasks.values()
            if task_info["facility_id"] == facility_id
        ]
        return {"success": True, "data": tasks}

    def filter_tasks_by_type_and_time(
        self,
        facility_id: str,
        task_type: str,
        scheduled_time_range: tuple
    ) -> dict:
        """
        Filter MaintenanceTasks for a facility by task_type and scheduled_time window.

        Args:
            facility_id (str): The ID of the facility to filter tasks for.
            task_type (str): The task type to match (exact string match).
            scheduled_time_range (tuple): (start_time, end_time) as ISO8601 strings.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[MaintenanceTaskInfo],  # List may be empty
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - facility_id must reference an existing Facility.
            - start_time must be less than or equal to end_time.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        if not (
            isinstance(scheduled_time_range, tuple) and
            len(scheduled_time_range) == 2
        ):
            return {"success": False, "error": "scheduled_time_range must be a tuple of (start_time, end_time)"}

        start_time, end_time = scheduled_time_range

        # String comparison is valid for properly formatted ISO8601 timestamps.
        if start_time > end_time:
            return {"success": False, "error": "Invalid time range: start_time is after end_time"}

        # Filter tasks
        filtered_tasks = []
        for task in self.maintenance_tasks.values():
            if (
                task["facility_id"] == facility_id and
                task["task_type"] == task_type and
                start_time <= task["scheduled_time"] <= end_time
            ):
                filtered_tasks.append(task)

        return {"success": True, "data": filtered_tasks}

    def get_task_by_id(self, task_id: str) -> dict:
        """
        Retrieve detailed info for a maintenance task given its task_id.

        Args:
            task_id (str): The unique identifier of the maintenance task.

        Returns:
            dict: {
                "success": True,
                "data": MaintenanceTaskInfo,
            }
            or
            {
                "success": False,
                "error": "Task not found"
            }

        Constraints:
            - The task_id must exist in the maintenance_tasks record.
        """
        task_info = self.maintenance_tasks.get(task_id)
        if not task_info:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "data": task_info}

    def list_events_for_task(self, task_id: str) -> dict:
        """
        Retrieve all maintenance events linked to a particular maintenance task.

        Args:
            task_id (str): The ID of the maintenance task.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceEventInfo]  # List of event info (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., task does not exist
            }

        Constraints:
            - Fails if task_id does not exist in current maintenance tasks.
            - Otherwise, returns all events linked to the given task.
        """
        if task_id not in self.maintenance_tasks:
            return {"success": False, "error": "Task not found"}

        results = [
            event_info for event_info in self.maintenance_events.values()
            if event_info["task_id"] == task_id
        ]
        return {"success": True, "data": results}

    def filter_events_by_time(self, completed_time: str) -> dict:
        """
        Retrieve maintenance events whose completed_time matches the specified timestamp.

        Args:
            completed_time (str): The completion timestamp to match (exact value).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[MaintenanceEventInfo]  # List may be empty if no events match
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Description of validation error
                    }
        Constraints:
            - completed_time must be provided and non-empty.
            - Returns only exact matches on completed_time.
        """
        if not completed_time or not isinstance(completed_time, str):
            return {"success": False, "error": "completed_time parameter must be a non-empty string"}

        matches = [
            event_info
            for event_info in self.maintenance_events.values()
            if event_info.get("completed_time") == completed_time
        ]

        return {"success": True, "data": matches}

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve details for a specific maintenance event using its event_id.
    
        Args:
            event_id (str): Unique identifier for the MaintenanceEvent.
        
        Returns:
            dict: {
                "success": True,
                "data": MaintenanceEventInfo
            }
            or
            {
                "success": False,
                "error": "MaintenanceEvent not found"
            }
    
        Constraints:
            - Returns full MaintenanceEventInfo if found.
            - If no such event exists, returns a failure with error message.
        """
        event = self.maintenance_events.get(event_id)
        if event is not None:
            return {"success": True, "data": event}
        else:
            return {"success": False, "error": "MaintenanceEvent not found"}

    def list_tasks_assigned_to_personnel(self, personnel_id: str) -> dict:
        """
        Find all maintenance tasks assigned to a specific personnel.

        Args:
            personnel_id (str): The unique ID of the personnel.

        Returns:
            dict:
              - success: True/False
              - data: List of MaintenanceTaskInfo assigned to this personnel (if success)
              - error: Error message (if failure)

        Constraints:
            - personnel_id must exist in the personnel database.
        """
        if personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel not found"}

        assigned_tasks = [
            task_info for task_info in self.maintenance_tasks.values()
            if task_info["assigned_personnel_id"] == personnel_id
        ]
        return {"success": True, "data": assigned_tasks}

    def get_personnel_by_id(self, personnel_id: str) -> dict:
        """
        Retrieve detailed info for a personnel/staff member by their unique ID.

        Args:
            personnel_id (str): The unique identifier for the personnel.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": PersonnelInfo
                }
                Failure: {
                    "success": False,
                    "error": "Personnel ID not found"
                }
        Constraints:
            - The provided personnel_id must exist in the system.
        """
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel ID not found" }
        personnel_info = self.personnel[personnel_id]
        return { "success": True, "data": personnel_info }

    def check_personnel_availability(self, personnel_id: str) -> dict:
        """
        Check and return the current availability status of a staff member.

        Args:
            personnel_id (str): The ID of the personnel to check.

        Returns:
            dict: 
                - If personnel exists: { "success": True, "data": <availability_status (str)> }
                - If not found: { "success": False, "error": "Personnel not found" }

        Constraints:
            - personnel_id must exist in the system.
        """
        personnel = self.personnel.get(personnel_id)
        if not personnel:
            return {"success": False, "error": "Personnel not found"}
        return {"success": True, "data": personnel["availability_status"]}

    def create_maintenance_task(
        self,
        task_id: str,
        facility_id: str,
        task_type: str,
        scheduled_time: str,
        assigned_personnel_id: str,
    ) -> dict:
        """
        Schedule a new maintenance task for a facility.

        Args:
            task_id (str): Unique identifier for the maintenance task.
            facility_id (str): Facility to assign the task to.
            task_type (str): Type of maintenance work.
            scheduled_time (str): Scheduled date/time for the task.
            assigned_personnel_id (str): Personnel to assign.

        Returns:
            dict:
                { "success": True, "message": "Maintenance task created." }
                or
                { "success": False, "error": <reason> }

        Constraints:
            - Facility must exist.
            - Personnel must exist and be "available".
            - MaintenanceTask ID must be unique.
            - Only available personnel can be assigned.
        """
        # Check for unique task_id
        if task_id in self.maintenance_tasks:
            return {"success": False, "error": "Task ID already exists."}

        # Facility existence
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist."}

        # Personnel existence
        if assigned_personnel_id not in self.personnel:
            return {"success": False, "error": "Personnel does not exist."}

        # Personnel availability
        personnel = self.personnel[assigned_personnel_id]
        if personnel.get("availability_status", "").lower() != "available":
            return {"success": False, "error": "Personnel not available."}

        # Create the MaintenanceTask
        self.maintenance_tasks[task_id] = {
            "task_id": task_id,
            "facility_id": facility_id,
            "task_type": task_type,
            "scheduled_time": scheduled_time,
            "status": "scheduled",
            "assigned_personnel_id": assigned_personnel_id,
        }

        return {"success": True, "message": "Maintenance task created."}

    def assign_personnel_to_task(self, task_id: str, personnel_id: str) -> dict:
        """
        Assign or re-assign available personnel to a scheduled maintenance task.

        Args:
            task_id (str): The ID of the maintenance task.
            personnel_id (str): The ID of the personnel to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Personnel <id> assigned to task <id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Both task and personnel must exist.
            - Personnel must have availability_status 'available'.
            - (Recommended) Task status should be 'scheduled' to allow (re-)assignment.
        """
        # Check task existence
        if task_id not in self.maintenance_tasks:
            return {"success": False, "error": f"MaintenanceTask '{task_id}' does not exist."}

        # Check personnel existence
        if personnel_id not in self.personnel:
            return {"success": False, "error": f"Personnel '{personnel_id}' does not exist."}

        # Check personnel availability
        if self.personnel[personnel_id]['availability_status'] != 'available':
            return {"success": False, "error": f"Personnel '{personnel_id}' is not available."}

        # Optional: check task status (should be scheduled)
        task_info = self.maintenance_tasks[task_id]
        if task_info.get('status', '').lower() != 'scheduled':
            return {"success": False, "error": f"Task '{task_id}' is not in a scheduled state for assignment."}

        # Assign personnel
        self.maintenance_tasks[task_id]['assigned_personnel_id'] = personnel_id

        return {"success": True,
                "message": f"Personnel '{personnel_id}' assigned to task '{task_id}'."}

    def update_task_status(self, task_id: str, new_status: str) -> dict:
        """
        Change the status of a maintenance task.

        Args:
            task_id (str): The identifier of the maintenance task.
            new_status (str): The status to set (e.g., "scheduled", "in progress", "completed").

        Returns:
            dict:
                { "success": True, "message": "Task status updated successfully" }
                or
                { "success": False, "error": <reason> }

        Constraints:
            - The specified task_id must exist in the system.
            - Status should be a recognized status string.
        """
        # Allowed status values reflect operational scheduling, delay, and safety-hold workflows.
        allowed_statuses = {
            "scheduled",
            "in progress",
            "completed",
            "delayed",
            "suspended",
            "cancelled",
        }

        if task_id not in self.maintenance_tasks:
            return {"success": False, "error": "Task ID does not exist"}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Status '{new_status}' is not recognized"}

        self.maintenance_tasks[task_id]["status"] = new_status
        return {"success": True, "message": "Task status updated successfully"}


    def record_maintenance_event(
        self,
        task_id: str,
        performed_by_personnel_id: str,
        completed_time: str
    ) -> dict:
        """
        Log the completion of a maintenance task as a MaintenanceEvent,
        linked to the related facility and personnel.

        Args:
            task_id (str): ID of the MaintenanceTask being completed.
            performed_by_personnel_id (str): ID of Personnel performing the task.
            completed_time (str): Completion timestamp (ISO or Unix string).

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance event recorded for task <task_id> (event_id: <event_id>)"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - MaintenanceEvent can only be created for scheduled MaintenanceTasks.
            - Task must reference valid Facility.
            - Personnel must match assigned_personnel_id in the task.
            - Each event is associated with exactly one task and one facility.
        """
        task = self.maintenance_tasks.get(task_id)
        if not task:
            return { "success": False, "error": "MaintenanceTask does not exist" }

        if task["status"].lower() != "scheduled":
            return { "success": False, "error": "MaintenanceEvent can only be recorded for scheduled tasks" }

        if task["facility_id"] not in self.facilities:
            return { "success": False, "error": "Associated Facility does not exist" }

        if performed_by_personnel_id != task.get("assigned_personnel_id"):
            return { "success": False, "error": "Personnel is not assigned to this task" }

        if performed_by_personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel does not exist" }

        # Generate a unique event_id
        event_id = str(uuid.uuid4())

        # Create the MaintenanceEvent
        event_info = {
            "event_id": event_id,
            "task_id": task_id,
            "facility_id": task["facility_id"],
            "completed_time": completed_time,
            "performed_by_personnel_id": performed_by_personnel_id
        }
        self.maintenance_events[event_id] = event_info

        # Update MaintenanceTask status to "completed"
        self.maintenance_tasks[task_id]["status"] = "completed"

        # Optionally, update personnel's availability to "available" (optional rule)
        # self.personnel[performed_by_personnel_id]["availability_status"] = "available"

        return {
            "success": True,
            "message": f"Maintenance event recorded for task {task_id} (event_id: {event_id})"
        }

    def update_facility_condition(self, facility_id: str, new_condition: str) -> dict:
        """
        Change the current_condition attribute of a facility.

        Args:
            facility_id (str): The unique identifier of the facility to update.
            new_condition (str): The new condition description for the facility.

        Returns:
            dict: {
                "success": True,
                "message": "Facility condition updated."
            } on success,
            {
                "success": False,
                "error": "Facility does not exist."
            } if the facility_id is not in the system.

        Constraints:
            - Facility must exist in the system.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist."}
        self.facilities[facility_id]["current_condition"] = new_condition
        return {"success": True, "message": "Facility condition updated."}

    def update_personnel_availability_status(self, personnel_id: str, new_status: str) -> dict:
        """
        Set or update the availability status of a staff member.

        Args:
            personnel_id (str): The unique ID of the personnel whose availability is to be updated.
            new_status (str): The new availability status value.

        Returns:
            dict: {
                "success": True,
                "message": "Personnel availability status updated."
            }
            or
            {
                "success": False,
                "error": "Personnel not found."
            }

        Constraints:
            - The given personnel_id must exist in the personnel records.
            - No restrictions on new_status value are imposed by the system rules.
        """
        if personnel_id not in self.personnel:
            return { "success": False, "error": "Personnel not found." }
    
        self.personnel[personnel_id]["availability_status"] = new_status
        return { "success": True, "message": "Personnel availability status updated." }

    def delete_maintenance_task(self, task_id: str) -> dict:
        """
        Remove a scheduled or incomplete maintenance task from the system.

        Args:
            task_id (str): Unique identifier of the maintenance task.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance task <task_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Task must exist.
            - Cannot delete task if a MaintenanceEvent references it (i.e., it is completed).
        """
        if task_id not in self.maintenance_tasks:
            return {
                "success": False,
                "error": f"Maintenance task '{task_id}' does not exist."
            }
        # Check if any event is linked to this task
        for event in self.maintenance_events.values():
            if event["task_id"] == task_id:
                return {
                    "success": False,
                    "error": f"Cannot delete maintenance task '{task_id}' because it has a completion event recorded."
                }

        # Perform deletion
        del self.maintenance_tasks[task_id]
        return {
            "success": True,
            "message": f"Maintenance task '{task_id}' deleted successfully."
        }

    def delete_maintenance_event(self, event_id: str) -> dict:
        """
        Remove a maintenance event by its event_id.

        Args:
            event_id (str): Unique identifier of the maintenance event to be removed.

        Returns:
            dict: 
                - On success: 
                    {"success": True, "message": "Maintenance event <event_id> deleted."}
                - On failure: 
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The event must exist.
            - Deletion is for record correction and is allowed, but does not update linked task/facility automatically.
        """
        if event_id not in self.maintenance_events:
            return { "success": False, "error": "Maintenance event does not exist." }
    
        del self.maintenance_events[event_id]
        return { "success": True, "message": f"Maintenance event {event_id} deleted." }


class FacilityMaintenanceManagementSystem(BaseEnv):
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

    def get_facility_by_name(self, **kwargs):
        return self._call_inner_tool('get_facility_by_name', kwargs)

    def list_facilities_by_type(self, **kwargs):
        return self._call_inner_tool('list_facilities_by_type', kwargs)

    def get_facility_by_id(self, **kwargs):
        return self._call_inner_tool('get_facility_by_id', kwargs)

    def list_tasks_for_facility(self, **kwargs):
        return self._call_inner_tool('list_tasks_for_facility', kwargs)

    def filter_tasks_by_type_and_time(self, **kwargs):
        return self._call_inner_tool('filter_tasks_by_type_and_time', kwargs)

    def get_task_by_id(self, **kwargs):
        return self._call_inner_tool('get_task_by_id', kwargs)

    def list_events_for_task(self, **kwargs):
        return self._call_inner_tool('list_events_for_task', kwargs)

    def filter_events_by_time(self, **kwargs):
        return self._call_inner_tool('filter_events_by_time', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_tasks_assigned_to_personnel(self, **kwargs):
        return self._call_inner_tool('list_tasks_assigned_to_personnel', kwargs)

    def get_personnel_by_id(self, **kwargs):
        return self._call_inner_tool('get_personnel_by_id', kwargs)

    def check_personnel_availability(self, **kwargs):
        return self._call_inner_tool('check_personnel_availability', kwargs)

    def create_maintenance_task(self, **kwargs):
        return self._call_inner_tool('create_maintenance_task', kwargs)

    def assign_personnel_to_task(self, **kwargs):
        return self._call_inner_tool('assign_personnel_to_task', kwargs)

    def update_task_status(self, **kwargs):
        return self._call_inner_tool('update_task_status', kwargs)

    def record_maintenance_event(self, **kwargs):
        return self._call_inner_tool('record_maintenance_event', kwargs)

    def update_facility_condition(self, **kwargs):
        return self._call_inner_tool('update_facility_condition', kwargs)

    def update_personnel_availability_status(self, **kwargs):
        return self._call_inner_tool('update_personnel_availability_status', kwargs)

    def delete_maintenance_task(self, **kwargs):
        return self._call_inner_tool('delete_maintenance_task', kwargs)

    def delete_maintenance_event(self, **kwargs):
        return self._call_inner_tool('delete_maintenance_event', kwargs)
