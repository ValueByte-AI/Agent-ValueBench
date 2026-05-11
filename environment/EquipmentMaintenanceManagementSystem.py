# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from collections import defaultdict



class MachineInfo(TypedDict):
    machine_id: str
    name: str
    model: str
    serial_number: str
    owner_user_id: str
    location: str
    status: str  # mapped from "sta"

class MaintenanceScheduleInfo(TypedDict):
    schedule_id: str
    machine_id: str
    scheduled_date: str
    maintenance_type: str
    assigned_technician_id: str
    status: str  # mapped from "sta"

class MaintenanceHistoryInfo(TypedDict):
    history_id: str
    machine_id: str
    maintenance_date: str
    maintenance_type: str
    technician_id: str
    notes: str  # mapped from "no"

class UserInfo(TypedDict):
    user_id: str  # mapped from "_id"
    name: str
    contact_details: str
    role: str  # mapped from "rol"

class _GeneratedEnvImpl:
    def __init__(self):
        # Machines: {machine_id: MachineInfo}
        self.machines: Dict[str, MachineInfo] = {}

        # Maintenance schedules: {schedule_id: MaintenanceScheduleInfo}
        self.maintenance_schedules: Dict[str, MaintenanceScheduleInfo] = {}

        # Maintenance history: {history_id: MaintenanceHistoryInfo}
        self.maintenance_histories: Dict[str, MaintenanceHistoryInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each machine must have a unique machine_id.
        # - A maintenance schedule can only be created for an existing machine.
        # - Each maintenance event (scheduled or historical) must reference a valid machine.
        # - Only authorized users (machine owners or assigned staff) can view or modify machine maintenance information.
        # - Maintenance schedules cannot overlap for the same machine unless specified as allowed.

    def _is_admin_user(self, user_id: str) -> bool:
        user = self.users.get(user_id)
        if not user:
            return False
        return str(user.get("role", "")).lower() in {"admin", "administrator", "superuser"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for a specific user by user_id.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            OR
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - The provided user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by user name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict:
                If found:
                    { "success": True, "data": List[UserInfo] }
                If not found:
                    { "success": False, "error": "No user found with the given name." }

        Notes:
            - User names are not guaranteed to be unique; all matches are returned.
        """
        matched_users = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]

        if not matched_users:
            return {"success": False, "error": "No user found with the given name."}

        return {"success": True, "data": matched_users}

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all users in the system.

        Args:
            None

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[UserInfo]  # List of user information dictionaries (may be empty if no users)
                }
        Constraints:
            - No constraints apply. Returns all users in the system.
        """
        result = list(self.users.values())
        return { "success": True, "data": result }

    def get_machine_by_id(self, machine_id: str) -> dict:
        """
        Retrieve machine details by machine_id.

        Args:
            machine_id (str): The ID of the machine to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": MachineInfo
            }
            or
            {
                "success": False,
                "error": "Machine not found"
            }

        Constraints:
            - The machine_id must exist in the system.
            - No authorization check is enforced (see notes).
        """
        machine = self.machines.get(machine_id)
        if not machine:
            return {"success": False, "error": "Machine not found"}

        return {"success": True, "data": machine}

    def list_machines_by_owner(self, owner_user_id: str) -> dict:
        """
        List all machines owned by a specific user.

        Args:
            owner_user_id (str): User ID of the owner.

        Returns:
            dict: {
                "success": True,
                "data": List[MachineInfo]  # List of machines (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # If user_id is not found
            }

        Constraints:
            - The user must exist in the system.
        """
        if owner_user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        machines = [
            machine_info
            for machine_info in self.machines.values()
            if machine_info["owner_user_id"] == owner_user_id
        ]
        return {"success": True, "data": machines}

    def list_all_machines(self) -> dict:
        """
        Retrieve a list of all machines in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MachineInfo],  # List of all MachineInfo dicts (may be empty)
            }

        Constraints:
            - No authorization is required for this operation.
            - If no machines exist, an empty list is returned.
        """
        all_machines = list(self.machines.values())
        return { "success": True, "data": all_machines }

    def get_maintenance_schedule_by_machine(self, machine_id: str) -> dict:
        """
        Retrieve all scheduled maintenance events for a given machine.

        Args:
            machine_id (str): The unique identifier of the target machine.

        Returns:
            dict:
                success (bool): True if retrieved successfully; False otherwise.
                data (List[MaintenanceScheduleInfo]): List of all matching scheduled maintenance events.
                error (str): Reason for failure (if any).

        Constraints:
            - machine_id must exist in the system.
            - (Authorization is not enforced here since user_id is not supplied.)
        """
        if machine_id not in self.machines:
            return {"success": False, "error": "Machine does not exist."}

        schedules = [
            sched for sched in self.maintenance_schedules.values()
            if sched["machine_id"] == machine_id
        ]
        return {"success": True, "data": schedules}

    def get_maintenance_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Retrieve details of a maintenance schedule using the given schedule_id.

        Args:
            schedule_id (str): The unique identifier of the maintenance schedule.

        Returns:
            dict: {
                "success": True,
                "data": MaintenanceScheduleInfo  # Details of the schedule
            }
            or
            {
                "success": False,
                "error": str  # Error reason if not found
            }

        Constraints:
            - schedule_id must exist in the system.
        """
        schedule = self.maintenance_schedules.get(schedule_id)
        if schedule is None:
            return {"success": False, "error": "Schedule not found"}
        return {"success": True, "data": schedule}

    def list_schedules_for_technician(self, technician_id: str) -> dict:
        """
        List all scheduled maintenance entries assigned to the specified technician.

        Args:
            technician_id (str): The user ID of the maintenance technician.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceScheduleInfo],  # List of schedules (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If technician does not exist
            }

        Constraints:
            - The technician_id must reference an existing user.
            - No additional authorization check is performed.
        """
        if technician_id not in self.users:
            return { "success": False, "error": "Technician does not exist" }

        schedules = [
            sched for sched in self.maintenance_schedules.values()
            if sched["assigned_technician_id"] == technician_id
        ]

        return { "success": True, "data": schedules }

    def get_maintenance_history_by_machine(self, machine_id: str, user_id: str) -> dict:
        """
        Retrieve the maintenance history for a specified machine, ensuring access is permitted
        only if the user is the machine owner or has been the maintenance technician for that machine.

        Args:
            machine_id (str): The machine whose maintenance history is to be retrieved.
            user_id (str): The user requesting the history.

        Returns:
            dict:
                On success:
                    { "success": True, "data": List[MaintenanceHistoryInfo] }
                On failure:
                    { "success": False, "error": str }
                
        Constraints:
            - Machine must exist.
            - Only the machine owner or a technician who has performed maintenance on the machine can view its history.
        """
        # Verify machine exists
        machine = self.machines.get(machine_id)
        if not machine:
            return {"success": False, "error": "Machine does not exist"}
    
        # Check user exists (optional strictness)
        if user_id not in self.users:
            return {"success": False, "error": "Requesting user does not exist"}

        # Check if user is the machine owner
        is_owner = machine["owner_user_id"] == user_id

        # Find maintenance history records for the machine
        histories = [
            h for h in self.maintenance_histories.values()
            if h["machine_id"] == machine_id
        ]

        # Check if the user has served as a technician for this machine
        is_technician = any(h["technician_id"] == user_id for h in histories)

        if not is_owner and not is_technician:
            return {
                "success": False,
                "error": "Not authorized to view maintenance history for this machine"
            }
        # Success: return all histories for this machine (may be empty)
        return {
            "success": True,
            "data": histories
        }

    def get_maintenance_history_by_id(self, history_id: str, requesting_user_id: str) -> dict:
        """
        Retrieve details of a maintenance history event by history_id,
        ensuring that the requesting user is authorized
        (machine owner or technician assigned to this event).

        Args:
            history_id (str): The unique maintenance history record ID.
            requesting_user_id (str): The user making the query.

        Returns:
            dict: Success: { "success": True, "data": MaintenanceHistoryInfo }
                  Failure: { "success": False, "error": str }

        Constraints:
            - The maintenance history event must exist.
            - Only machine owner or assigned technician can view this info.
        """
        # Check existence
        history = self.maintenance_histories.get(history_id)
        if not history:
            return { "success": False, "error": "Maintenance history event not found" }
    
        machine_id = history["machine_id"]
        machine = self.machines.get(machine_id)
        if not machine:
            return { "success": False, "error": "Associated machine not found" }
    
        user = self.users.get(requesting_user_id)
        if not user:
            return { "success": False, "error": "Requesting user not found" }
    
        # Authorization: Must be machine owner or the event's assigned technician
        if (
            requesting_user_id == machine["owner_user_id"]
            or requesting_user_id == history["technician_id"]
        ):
            return { "success": True, "data": history }
        else:
            return { "success": False, "error": "Not authorized to view this maintenance history event" }

    def check_user_authorization_for_machine(self, user_id: str, machine_id: str) -> dict:
        """
        Determine if a user has permission to view or modify a specific machine's maintenance info.

        Args:
            user_id (str): The user's unique identifier.
            machine_id (str): The machine's unique identifier.
    
        Returns:
            dict: {
                "success": True,
                "authorized": bool,
                "reason": str  # description of why/why not
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Authorization logic:
            - User is the machine owner.
            - OR user is assigned as a technician to a schedule for this machine.
            - OR user performed past maintenance (in history) for this machine.
            - OR user role is 'admin' (case-insensitive check, common admin/superuser roles).
        """

        # Check user and machine existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if machine_id not in self.machines:
            return { "success": False, "error": "Machine does not exist" }

        user = self.users[user_id]
        machine = self.machines[machine_id]

        # Check if user is the machine owner
        if machine["owner_user_id"] == user_id:
            return {
                "success": True,
                "authorized": True,
                "reason": "User is the machine owner."
            }

        # Check if user is admin/superuser role
        if user.get("role", "").lower() in {"admin", "administrator", "superuser"}:
            return {
                "success": True,
                "authorized": True,
                "reason": "User is an administrator."
            }

        # Check if user is assigned as technician to a schedule for this machine
        for schedule in self.maintenance_schedules.values():
            if schedule["machine_id"] == machine_id and schedule["assigned_technician_id"] == user_id:
                return {
                    "success": True,
                    "authorized": True,
                    "reason": "User is assigned as a technician for this machine in an upcoming schedule."
                }

        # Check if user performed past maintenance for this machine
        for history in self.maintenance_histories.values():
            if history["machine_id"] == machine_id and history["technician_id"] == user_id:
                return {
                    "success": True,
                    "authorized": True,
                    "reason": "User performed past maintenance for this machine."
                }

        # Not authorized
        return {
            "success": True,
            "authorized": False,
            "reason": "User is not authorized for this machine."
        }

    def find_overlapping_schedules(self, machine_id: str, start_date: str, end_date: str) -> dict:
        """
        Examine if a given machine has overlapping maintenance schedules within a given time window.

        Args:
            machine_id (str): The ID of the machine.
            start_date (str): Start of the time window (inclusive, 'YYYY-MM-DD').
            end_date (str): End of the time window (inclusive, 'YYYY-MM-DD').

        Returns:
            dict: {
                "success": True,
                "data": List[List[str]],  # List of overlapping schedule_id pairs (or groups). Empty list if none.
            }
            or
            {
                "success": False,
                "error": str  # reason
            }

        Constraints:
            - The machine must exist.
            - Dates should be in 'YYYY-MM-DD' format.
            - Only schedules for the machine within the window are checked.
            - Overlap: scheduled_date occurs more than once.
        """

        if machine_id not in self.machines:
            return { "success": False, "error": "Machine does not exist." }

        # Collect all schedules for the machine in the date window
        relevant_schedules = [
            sched for sched in self.maintenance_schedules.values()
            if sched["machine_id"] == machine_id
            and start_date <= sched["scheduled_date"] <= end_date
        ]

        # Group schedules by their scheduled_date

        date_to_schedules = defaultdict(list)
        for sched in relevant_schedules:
            date_to_schedules[sched["scheduled_date"]].append(sched["schedule_id"])

        # Find groups with more than 1 schedule (i.e., overlaps)
        overlaps = [
            group for group in date_to_schedules.values() if len(group) > 1
        ]

        return { "success": True, "data": overlaps }  # List of overlapping schedule_id lists

    def create_machine(
        self,
        machine_id: str,
        name: str,
        model: str,
        serial_number: str,
        owner_user_id: str,
        location: str,
        status: str
    ) -> dict:
        """
        Add a new machine to the system with the provided attributes.

        Args:
            machine_id (str): Unique identifier for the machine.
            name (str): Machine name.
            model (str): Machine model.
            serial_number (str): Serial number.
            owner_user_id (str): ID of the user who owns the machine.
            location (str): Physical location of the machine.
            status (str): Status of the machine.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Machine created successfully." }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - machine_id must be unique in the system.
            - owner_user_id must reference an existing user.
            - All fields must be provided (non-empty).
        """
        # Check for unique machine_id
        if not machine_id or machine_id in self.machines:
            return { "success": False, "error": "machine_id is missing or already exists." }

        # Check owner_user_id exists
        if not owner_user_id or owner_user_id not in self.users:
            return { "success": False, "error": "owner_user_id does not exist." }

        # Basic required fields check
        required_fields = [machine_id, name, model, serial_number, owner_user_id, location, status]
        if any(field is None or str(field).strip() == '' for field in required_fields):
            return { "success": False, "error": "All fields are required and must be non-empty." }

        machine: MachineInfo = {
            "machine_id": machine_id,
            "name": name,
            "model": model,
            "serial_number": serial_number,
            "owner_user_id": owner_user_id,
            "location": location,
            "status": status
        }
        self.machines[machine_id] = machine
        return { "success": True, "message": "Machine created successfully." }

    def update_machine_info(self, machine_id: str, updates: dict, requesting_user_id: str) -> dict:
        """
        Update details or status of an existing machine.

        Args:
            machine_id (str): The unique identifier of the machine to update.
            updates (dict): Fields to update with their new values.
                Allowed: name, model, serial_number, owner_user_id, location, status.
            requesting_user_id (str): The ID of the user attempting this operation.

        Returns:
            dict: {
                "success": True,
                "message": str  # Update status,
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., permission denied, not found, invalid field, etc.
            }

        Constraints:
            - Only the machine owner or an admin user can perform update.
            - The machine must exist.
            - Only mutable fields can be updated (machine_id is immutable).
            - All updated fields must be valid keys of MachineInfo except machine_id.
        """
        # Check machine existence
        machine = self.machines.get(machine_id)
        if not machine:
            return {"success": False, "error": "Machine not found"}

        # Authorization: owner or admin only
        user = self.users.get(requesting_user_id)
        if not user:
            return {"success": False, "error": "Requesting user not found"}
        is_owner = (machine['owner_user_id'] == requesting_user_id)
        is_admin = (user.get("role") == "admin")
        if not (is_owner or is_admin):
            return {"success": False, "error": "Permission denied"}

        # Validate updates
        mutable_fields = {"name", "model", "serial_number", "owner_user_id", "location", "status"}
        for field in updates:
            if field not in mutable_fields:
                return {"success": False, "error": f"Invalid field: {field}"}
    
        # Apply updates
        for field, value in updates.items():
            machine[field] = value

        self.machines[machine_id] = machine  # Redundant, but ensures state update

        return {"success": True, "message": "Machine info updated successfully"}

    def delete_machine(self, machine_id: str) -> dict:
        """
        Permanently remove a machine from the system as well as all associated maintenance schedules and maintenance history records.

        Args:
            machine_id (str): The unique identifier for the target machine.

        Returns:
            dict: {
                "success": True,
                "message": "Machine and associated schedules/histories deleted."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The machine must exist.
            - All maintenance schedules and histories referencing this machine will be deleted.
        """
        # Check if machine exists
        if machine_id not in self.machines:
            return { "success": False, "error": "Machine does not exist." }

        # Remove machine
        del self.machines[machine_id]

        # Remove all maintenance schedules associated with this machine
        schedules_to_delete = [
            schedule_id for schedule_id, sch in self.maintenance_schedules.items()
            if sch["machine_id"] == machine_id
        ]
        for schedule_id in schedules_to_delete:
            del self.maintenance_schedules[schedule_id]

        # Remove all maintenance history entries associated with this machine
        histories_to_delete = [
            history_id for history_id, hist in self.maintenance_histories.items()
            if hist["machine_id"] == machine_id
        ]
        for history_id in histories_to_delete:
            del self.maintenance_histories[history_id]

        return {
            "success": True,
            "message": "Machine and associated schedules/histories deleted."
        }

    def create_maintenance_schedule(
        self,
        schedule_id: str,
        machine_id: str,
        scheduled_date: str,
        maintenance_type: str,
        assigned_technician_id: str,
        status: str,
        request_user_id: str
    ) -> dict:
        """
        Add a new maintenance event (schedule) for a machine, ensuring:
            - schedule_id is unique,
            - referenced machine exists,
            - assigned technician exists,
            - no forbidden overlap with existing schedules for this machine/date,
            - the requesting user is authorized (machine owner or assigned technician).

        Args:
            schedule_id (str): Unique schedule identifier.
            machine_id (str): Target machine's id; must exist.
            scheduled_date (str): Date/time of maintenance (e.g., 'YYYY-MM-DD').
            maintenance_type (str): Type of maintenance planned.
            assigned_technician_id (str): User id of assigned technician.
            status (str): Schedule status.
            request_user_id (str): User requesting this operation (authorization checked).

        Returns:
            dict: 
                On success: {"success": True, "message": "Maintenance schedule created."}
                On failure: {"success": False, "error": str description}
        Constraints:
            - Schedule ids are unique.
            - Machine must exist.
            - Schedule cannot overlap another schedule for the same machine (same date).
            - Only machine owner, assigned technician, or an admin user can create a schedule.
            - Assigned technician must exist as a user.
        """
        # 1. Unique Schedule ID
        if schedule_id in self.maintenance_schedules:
            return {"success": False, "error": "Schedule ID already exists."}

        # 2. Machine Must Exist
        if machine_id not in self.machines:
            return {"success": False, "error": "Target machine does not exist."}

        # 3. Assigned Technician must exist
        if assigned_technician_id not in self.users:
            return {"success": False, "error": "Assigned technician does not exist."}

        # 4. Authorization: machine owner, assigned technician, or admin can add a schedule
        machine = self.machines[machine_id]
        if (
            request_user_id != machine["owner_user_id"]
            and request_user_id != assigned_technician_id
            and not self._is_admin_user(request_user_id)
        ):
            return {"success": False, "error": "User not authorized to create schedule for this machine."}

        # 5. No overlap: same machine and same scheduled_date
        for sched in self.maintenance_schedules.values():
            if sched["machine_id"] == machine_id and sched["scheduled_date"] == scheduled_date:
                return {"success": False, "error": "Overlapping maintenance schedule exists for this machine at that date."}

        # 6. Create and store the schedule
        new_schedule = {
            "schedule_id": schedule_id,
            "machine_id": machine_id,
            "scheduled_date": scheduled_date,
            "maintenance_type": maintenance_type,
            "assigned_technician_id": assigned_technician_id,
            "status": status
        }

        self.maintenance_schedules[schedule_id] = new_schedule

        return {"success": True, "message": "Maintenance schedule created."}

    def update_maintenance_schedule(
        self,
        user_id: str,
        schedule_id: str,
        scheduled_date: str = None,
        maintenance_type: str = None,
        assigned_technician_id: str = None,
        status: str = None
    ) -> dict:
        """
        Modify the date, type, technician, or status of an existing maintenance schedule.

        Args:
            user_id (str): The ID of the user requesting the change.
            schedule_id (str): The maintenance schedule to update.
            scheduled_date (str, optional): New scheduled date.
            maintenance_type (str, optional): New maintenance type.
            assigned_technician_id (str, optional): New assigned technician.
            status (str, optional): New schedule status.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance schedule updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only the machine owner, current assigned technician, or an admin user may modify the schedule.
            - Changing assigned_technician_id requires that the user exists.
            - Changing scheduled_date may not cause overlapping schedules for the same machine.
        """
        # Schedule must exist
        schedule = self.maintenance_schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Maintenance schedule not found."}

        # Get machine
        machine = self.machines.get(schedule["machine_id"])
        if not machine:
            return {"success": False, "error": "Machine for schedule not found."}

        # Only owner, technician, or admin can modify
        if (
            user_id not in [machine["owner_user_id"], schedule["assigned_technician_id"]]
            and not self._is_admin_user(user_id)
        ):
            return {"success": False, "error": "User not authorized to modify this schedule."}

        # Assignment to a non-existent technician is not allowed when changing the assignee.
        # This still permits callers to retain a legacy placeholder value already present
        # on the schedule (for example, "UNASSIGNED") while updating other fields.
        if assigned_technician_id is not None:
            if (
                assigned_technician_id != schedule["assigned_technician_id"]
                and assigned_technician_id not in self.users
            ):
                return {"success": False, "error": "Assigned technician does not exist."}

        # Overlap check (if date is changing)
        if scheduled_date and scheduled_date != schedule["scheduled_date"]:
            for other in self.maintenance_schedules.values():
                if (
                    other["machine_id"] == schedule["machine_id"] and
                    other["schedule_id"] != schedule_id and
                    other["scheduled_date"] == scheduled_date
                ):
                    return {"success": False, "error": "Overlapping maintenance schedule for this machine on the same date."}

        # Actual update
        if scheduled_date:
            schedule["scheduled_date"] = scheduled_date
        if maintenance_type:
            schedule["maintenance_type"] = maintenance_type
        if assigned_technician_id:
            schedule["assigned_technician_id"] = assigned_technician_id
        if status:
            schedule["status"] = status

        self.maintenance_schedules[schedule_id] = schedule
        return {"success": True, "message": "Maintenance schedule updated."}

    def cancel_maintenance_schedule(self, schedule_id: str, user_id: str) -> dict:
        """
        Cancel a planned maintenance event, changing its status to 'cancelled'.
        Args:
            schedule_id (str): The maintenance schedule to cancel.
            user_id (str): The user attempting the cancellation (for authorization check).

        Returns:
            dict:
                {"success": True, "message": "Maintenance schedule <id> cancelled."}
                or
                {"success": False, "error": "<reason>"}

        Constraints:
            - Schedule must exist.
            - User must exist.
            - Only authorized users can cancel: machine owner or assigned technician.
            - Schedule must not be already cancelled.
        """
        # Existence checks
        schedule = self.maintenance_schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Maintenance schedule not found."}
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        machine_id = schedule["machine_id"]
        machine = self.machines.get(machine_id)
        if not machine:
            return {"success": False, "error": "Associated machine does not exist."}

        # Authorization: owner or assigned technician
        if not (user_id == machine["owner_user_id"] or user_id == schedule["assigned_technician_id"]):
            return {"success": False, "error": "User not authorized to cancel this maintenance schedule."}

        # Already cancelled?
        if schedule.get("status", "").lower() == "cancelled":
            return {"success": False, "error": "Maintenance schedule is already cancelled."}

        # Proceed with cancellation
        schedule["status"] = "cancelled"
        self.maintenance_schedules[schedule_id] = schedule

        return {"success": True, "message": f"Maintenance schedule {schedule_id} cancelled."}

    def create_maintenance_history_entry(
        self,
        history_id: str,
        machine_id: str,
        maintenance_date: str,
        maintenance_type: str,
        technician_id: str,
        notes: str,
        requesting_user_id: str
    ) -> dict:
        """
        Add a new maintenance history record for a completed maintenance event.

        Args:
            history_id (str): Unique identifier for the maintenance history entry.
            machine_id (str): The ID of the maintained machine.
            maintenance_date (str): The date when maintenance occurred.
            maintenance_type (str): The type of maintenance performed.
            technician_id (str): The ID of the technician who performed the work.
            notes (str): Additional notes for the event.
            requesting_user_id (str): The user performing the operation (for authorization checking).

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance history entry created."
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - history_id must not already exist.
            - machine_id must exist.
            - technician_id must exist.
            - Only authorized users (machine owner or assigned technician/staff) can add entries.
        """

        if history_id in self.maintenance_histories:
            return {"success": False, "error": "History ID already exists."}

        if machine_id not in self.machines:
            return {"success": False, "error": "Machine does not exist."}

        if technician_id not in self.users:
            return {"success": False, "error": "Technician user does not exist."}

        # Authorization check
        machine = self.machines[machine_id]
        if requesting_user_id != machine['owner_user_id'] and requesting_user_id != technician_id:
            # If user is not owner nor assigned technician, check if they are staff
            user_info = self.users.get(requesting_user_id)
            if not user_info or user_info['role'] not in ['staff', 'admin', 'technician']:
                return {"success": False, "error": "Not authorized to add maintenance history for this machine."}

        entry: MaintenanceHistoryInfo = {
            "history_id": history_id,
            "machine_id": machine_id,
            "maintenance_date": maintenance_date,
            "maintenance_type": maintenance_type,
            "technician_id": technician_id,
            "notes": notes,
        }
        self.maintenance_histories[history_id] = entry

        return {"success": True, "message": "Maintenance history entry created."}

    def update_maintenance_history_entry(
        self,
        history_id: str,
        user_id: str,
        notes: str = None,
        maintenance_date: str = None,
        maintenance_type: str = None,
        technician_id: str = None
    ) -> dict:
        """
        Edit the notes or details of a historical maintenance event.

        Args:
            history_id (str): ID of the maintenance history entry to update.
            user_id (str):    ID of the user making the change (authorization required).
            notes (str, optional): Updated notes for the maintenance entry.
            maintenance_date (str, optional): Updated maintenance date.
            maintenance_type (str, optional): Updated type of maintenance.
            technician_id (str, optional): Updated technician id.

        Returns:
            dict: Success or error message.
                {
                    "success": True,
                    "message": "Maintenance history updated successfully."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Only the machine owner or the technician who performed the maintenance may update the history entry.
            - The referenced maintenance history must exist.
            - The referenced machine must exist.
            - At least one of ('notes', 'maintenance_date', 'maintenance_type', 'technician_id') must be provided.
        """
        if history_id not in self.maintenance_histories:
            return {"success": False, "error": "Maintenance history entry does not exist."}
        history = self.maintenance_histories[history_id]

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        user = self.users[user_id]

        machine_id = history["machine_id"]
        if machine_id not in self.machines:
            return {"success": False, "error": "Referenced machine does not exist."}
        machine = self.machines[machine_id]

        # Authorization: machine owner or the technician who performed the maintenance
        if not (user_id == machine["owner_user_id"] or user_id == history["technician_id"]):
            return {"success": False, "error": "User not authorized to update this maintenance history entry."}

        if all(
            v is None for v in [notes, maintenance_date, maintenance_type, technician_id]
        ):
            return {"success": False, "error": "No update fields provided."}

        updated = False

        if notes is not None:
            history["notes"] = notes
            updated = True
        if maintenance_date is not None:
            history["maintenance_date"] = maintenance_date
            updated = True
        if maintenance_type is not None:
            history["maintenance_type"] = maintenance_type
            updated = True
        if technician_id is not None:
            history["technician_id"] = technician_id
            updated = True

        if updated:
            self.maintenance_histories[history_id] = history
            return {"success": True, "message": "Maintenance history updated successfully."}
        else:
            return {"success": False, "error": "No fields updated."}

    def delete_maintenance_schedule(self, schedule_id: str, requesting_user_id: str) -> dict:
        """
        Remove a scheduled maintenance event by its schedule_id if the requesting user is authorized.

        Args:
            schedule_id (str): ID of the maintenance schedule to remove.
            requesting_user_id (str): ID of the user attempting the deletion.
    
        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Maintenance schedule deleted successfully"
                }
                Failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Schedule must exist.
            - Only machine owner or assigned technician can delete schedule.
        """
        schedule = self.maintenance_schedules.get(schedule_id)
        if not schedule:
            return { "success": False, "error": "Maintenance schedule does not exist" }

        machine_id = schedule["machine_id"]
        machine = self.machines.get(machine_id)
        if not machine:
            # Should not happen unless data is corrupted, but handle defensively
            return { "success": False, "error": "Machine referenced by schedule does not exist" }

        assigned_technician_id = schedule["assigned_technician_id"]
        owner_user_id = machine["owner_user_id"]
        if requesting_user_id not in [owner_user_id, assigned_technician_id]:
            return { "success": False, "error": "User not authorized to delete schedule" }

        del self.maintenance_schedules[schedule_id]
        return { "success": True, "message": "Maintenance schedule deleted successfully" }

    def assign_technician_to_schedule(self, user_id: str, schedule_id: str, technician_id: str) -> dict:
        """
        Assign or reassign a technician to a maintenance schedule.

        Args:
            user_id (str): The acting user's ID (must have permission to modify this schedule).
            schedule_id (str): The ID of the maintenance schedule to update.
            technician_id (str): The technician's user ID to assign.

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
            - Schedule and technician must exist.
            - Technician must have role "technician".
            - Only authorized users (owner, assigned technician, or admin) can modify schedule.
        """
        # Check schedule exists
        schedule = self.maintenance_schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Maintenance schedule does not exist."}

        machine_id = schedule["machine_id"]
        machine = self.machines.get(machine_id)
        if not machine:
            return {"success": False, "error": "Associated machine does not exist."}

        # Check acting user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Acting user does not exist."}

        # Check authorization: owner, current assigned technician, or admin
        if (
            user_id != machine["owner_user_id"]
            and user_id != schedule["assigned_technician_id"]
            and not self._is_admin_user(user_id)
        ):
            return {"success": False, "error": "User not authorized to assign technician to this schedule."}

        # Check technician exists
        tech = self.users.get(technician_id)
        if not tech:
            return {"success": False, "error": f"Technician user '{technician_id}' does not exist."}

        # Check role
        if tech["role"].lower() != "technician":
            return {"success": False, "error": f"User '{technician_id}' is not a technician."}

        # Assignment (idempotent)
        self.maintenance_schedules[schedule_id]["assigned_technician_id"] = technician_id

        return {
            "success": True,
            "message": f"Technician '{technician_id}' assigned to schedule '{schedule_id}'."
        }

    def create_user(
        self,
        user_id: str,
        name: str,
        contact_details: str,
        role: str
    ) -> dict:
        """
        Adds a new user to the system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): The user's name.
            contact_details (str): The user's contact information.
            role (str): The user's role within the system.

        Returns:
            dict: {
                "success": True,
                "message": "User created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must be unique.
            - All fields must be non-empty.
        """

        # Check for uniqueness
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists." }
        # Basic validation (all fields required)
        if not all([user_id, name, contact_details, role]):
            return { "success": False, "error": "All user fields (user_id, name, contact_details, role) must be provided and non-empty." }
        # Create and add the user
        user_info: UserInfo = {
            "user_id": user_id,
            "name": name,
            "contact_details": contact_details,
            "role": role
        }
        self.users[user_id] = user_info
        return { "success": True, "message": "User created successfully." }

    def update_user_info(
        self, 
        user_id: str, 
        name: str = None, 
        contact_details: str = None, 
        role: str = None
    ) -> dict:
        """
        Edit details of an existing user.

        Args:
            user_id (str): ID of the user to edit.
            name (str, optional): New name for the user.
            contact_details (str, optional): New contact details for the user.
            role (str, optional): New role for the user.

        Returns:
            dict: 
                - Success: {"success": True, "message": "User info updated successfully."}
                - Failure: {"success": False, "error": <reason>}

        Constraints:
            - user_id must exist.
            - At least one field must be provided to update.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        updated_fields = {}
        if name is not None:
            user["name"] = name
            updated_fields["name"] = name
        if contact_details is not None:
            user["contact_details"] = contact_details
            updated_fields["contact_details"] = contact_details
        if role is not None:
            user["role"] = role
            updated_fields["role"] = role

        if not updated_fields:
            return {"success": False, "error": "No update fields provided."}

        self.users[user_id] = user
        return {"success": True, "message": "User info updated successfully."}

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user from the system.

        Args:
            user_id (str): The user_id of the user to delete.

        Returns:
            dict: {
                "success": True,
                "message": "User deleted successfully"
            }
            or
            {
                "success": False,
                "error": Error message string
            }

        Constraints:
            - User must exist.
            - User must NOT be referenced as a machine owner,
              assigned technician in a schedule, or
              technician in maintenance history. If referenced, deletion is not allowed.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Check if user is referenced as owner in any machine
        for machine in self.machines.values():
            if machine["owner_user_id"] == user_id:
                return {
                    "success": False,
                    "error": "User cannot be deleted: referenced as machine owner"
                }
        # Check if user is referenced as assigned technician in any schedule
        for schedule in self.maintenance_schedules.values():
            if schedule["assigned_technician_id"] == user_id:
                return {
                    "success": False,
                    "error": "User cannot be deleted: referenced as assigned technician in maintenance schedule"
                }
        # Check if user is referenced as technician in any history entry
        for history in self.maintenance_histories.values():
            if history["technician_id"] == user_id:
                return {
                    "success": False,
                    "error": "User cannot be deleted: referenced as technician in maintenance history"
                }

        del self.users[user_id]
        return {
            "success": True,
            "message": "User deleted successfully"
        }


class EquipmentMaintenanceManagementSystem(BaseEnv):
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_machine_by_id(self, **kwargs):
        return self._call_inner_tool('get_machine_by_id', kwargs)

    def list_machines_by_owner(self, **kwargs):
        return self._call_inner_tool('list_machines_by_owner', kwargs)

    def list_all_machines(self, **kwargs):
        return self._call_inner_tool('list_all_machines', kwargs)

    def get_maintenance_schedule_by_machine(self, **kwargs):
        return self._call_inner_tool('get_maintenance_schedule_by_machine', kwargs)

    def get_maintenance_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_maintenance_schedule_by_id', kwargs)

    def list_schedules_for_technician(self, **kwargs):
        return self._call_inner_tool('list_schedules_for_technician', kwargs)

    def get_maintenance_history_by_machine(self, **kwargs):
        return self._call_inner_tool('get_maintenance_history_by_machine', kwargs)

    def get_maintenance_history_by_id(self, **kwargs):
        return self._call_inner_tool('get_maintenance_history_by_id', kwargs)

    def check_user_authorization_for_machine(self, **kwargs):
        return self._call_inner_tool('check_user_authorization_for_machine', kwargs)

    def find_overlapping_schedules(self, **kwargs):
        return self._call_inner_tool('find_overlapping_schedules', kwargs)

    def create_machine(self, **kwargs):
        return self._call_inner_tool('create_machine', kwargs)

    def update_machine_info(self, **kwargs):
        return self._call_inner_tool('update_machine_info', kwargs)

    def delete_machine(self, **kwargs):
        return self._call_inner_tool('delete_machine', kwargs)

    def create_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('create_maintenance_schedule', kwargs)

    def update_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('update_maintenance_schedule', kwargs)

    def cancel_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('cancel_maintenance_schedule', kwargs)

    def create_maintenance_history_entry(self, **kwargs):
        return self._call_inner_tool('create_maintenance_history_entry', kwargs)

    def update_maintenance_history_entry(self, **kwargs):
        return self._call_inner_tool('update_maintenance_history_entry', kwargs)

    def delete_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('delete_maintenance_schedule', kwargs)

    def assign_technician_to_schedule(self, **kwargs):
        return self._call_inner_tool('assign_technician_to_schedule', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)
