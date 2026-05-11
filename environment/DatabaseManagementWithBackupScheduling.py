# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import uuid
from datetime import datetime
import time
from typing import Optional



# Data entity: data_id, name, owner, last_modified, size
class DataEntityInfo(TypedDict):
    data_id: str
    name: str
    owner: str
    last_modified: str  # ISO timestamp string
    size: float

# BackupSchedule entity: schedule_id, data_id, time_of_day, frequency, status
class BackupScheduleInfo(TypedDict):
    schedule_id: str
    data_id: str
    time_of_day: str  # e.g., "22:00"
    frequency: str    # e.g., "daily", "weekly"
    status: str       # e.g., "active", "inactive"

# BackupJob entity: job_id, schedule_id, data_id, scheduled_time, actual_start_time, status, completion_time, result
class BackupJobInfo(TypedDict, total=False):
    job_id: str
    schedule_id: str
    data_id: str
    scheduled_time: str          # ISO timestamp string
    actual_start_time: Optional[str]
    status: str                  # e.g., "scheduled", "running", "completed", "failed"
    completion_time: Optional[str]
    result: Optional[str]        # e.g., "success", "error: disk full"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Database Management System with automated backup scheduling.
        """

        # Data entities: {data_id: DataEntityInfo}
        self.data_entities: Dict[str, DataEntityInfo] = {}

        # Backup schedules: {schedule_id: BackupScheduleInfo}
        self.backup_schedules: Dict[str, BackupScheduleInfo] = {}

        # Backup jobs: {job_id: BackupJobInfo}
        self.backup_jobs: Dict[str, BackupJobInfo] = {}

        # Constraints:
        # - Each BackupSchedule must be linked to a valid DataEntity.
        # - Certain guarded windows (currently daily 00:00) allow only one active
        #   schedule across the entire system.
        # - Otherwise, overlap checks are enforced per data entity.
        # - BackupJobs are created according to their associated BackupSchedule definitions.
        # - BackupJobs transition through defined statuses (e.g., scheduled → running → completed/failed).

    def get_data_by_id(self, data_id: str) -> dict:
        """
        Retrieve the details of a data entity given its data_id.

        Args:
            data_id (str): The identifier of the data entity to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": DataEntityInfo  # Info about the data entity
            }
            or
            {
                "success": False,
                "error": str  # If data_id does not exist
            }

        Constraints:
            - data_id must exist in the system.
        """
        if data_id not in self.data_entities:
            return {"success": False, "error": "Data entity not found"}
        return {"success": True, "data": self.data_entities[data_id]}

    def list_all_data_entities(self) -> dict:
        """
        List all data entities managed by the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[DataEntityInfo]  # List of all data entities (could be empty)
            }
            or
            {
                "success": False,
                "error": str  # Only if an unexpected error occurred (not expected)
            }

        Constraints:
            - None specific; readonly operation.
        """
        data_list = list(self.data_entities.values())
        return {"success": True, "data": data_list}

    def get_data_by_name(self, name: str) -> dict:
        """
        Query a data entity by its human-readable name.

        Args:
            name (str): The name of the data entity to search for.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": DataEntityInfo  # The matching data entity's information.
                    }
                - On failure (not found):
                    {
                        "success": False,
                        "error": "No data entity with the specified name found"
                    }

        Notes:
            - If multiple entities have the same name, the first one found is returned.
            - The match is case-sensitive.
        """
        for data_entity in self.data_entities.values():
            if data_entity["name"] == name:
                return { "success": True, "data": data_entity }
        return { "success": False, "error": "No data entity with the specified name found" }

    def list_backup_schedules_for_data(self, data_id: str) -> dict:
        """
        List all backup schedules associated with a given data_id.

        Args:
            data_id (str): The unique ID of the data entity.

        Returns:
            dict: {
                "success": True,
                "data": List[BackupScheduleInfo]  # May be empty if no schedules exist for data_id
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Data entity does not exist"
            }

        Constraints:
            - The data_id must exist in self.data_entities.
        """
        if data_id not in self.data_entities:
            return {"success": False, "error": "Data entity does not exist"}
    
        schedules = [
            schedule for schedule in self.backup_schedules.values()
            if schedule['data_id'] == data_id
        ]
        return {"success": True, "data": schedules}

    def get_backup_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Retrieve details of a backup schedule given its schedule_id.

        Args:
            schedule_id (str): The unique identifier of the backup schedule to retrieve.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": BackupScheduleInfo  # The schedule's information
                }
                On failure (e.g., schedule_id does not exist):
                {
                    "success": False,
                    "error": "Schedule not found"
                }

        Constraints:
            - schedule_id must exist in the backup_schedules.
        """
        schedule = self.backup_schedules.get(schedule_id)
        if schedule is None:
            return { "success": False, "error": "Schedule not found" }
        return { "success": True, "data": schedule }

    def _is_globally_guarded_slot(self, time_of_day: str, frequency: str) -> bool:
        return time_of_day == "00:00" and frequency == "daily"

    def _find_active_schedule_conflicts(
        self,
        data_id: str,
        time_of_day: str,
        frequency: str,
        exclude_schedule_id: Optional[str] = None
    ) -> list[BackupScheduleInfo]:
        conflicts: list[BackupScheduleInfo] = []
        check_globally = self._is_globally_guarded_slot(time_of_day, frequency)
        for current_schedule_id, schedule in self.backup_schedules.items():
            if exclude_schedule_id is not None and current_schedule_id == exclude_schedule_id:
                continue
            if (
                schedule.get("status", "active") == "active"
                and schedule["time_of_day"] == time_of_day
                and schedule["frequency"] == frequency
                and (check_globally or schedule["data_id"] == data_id)
            ):
                conflicts.append(schedule)
        return conflicts

    def check_overlapping_schedules(self, data_id: str, time_of_day: str, frequency: str) -> dict:
        """
        Determine whether placing or keeping a schedule for a given data_id at a specified
        time_of_day and frequency would conflict with active schedules.
    
        Args:
            data_id (str): The identifier of the data entity to check.
            time_of_day (str): The backup time (e.g., "22:00").
            frequency (str): The recurrence period (e.g., "daily", "weekly").
    
        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[BackupScheduleInfo]  # matching active conflicts (may be empty)
                  }
                - On error: {
                    "success": False,
                    "error": str
                  }
        Constraints:
            - Only 'active' schedules are considered.
            - The daily 00:00 slot is treated as a system-wide guarded window.
            - Other slots are checked within the same data entity.
            - If data_id does not exist, it's an error.
        """
        if data_id not in self.data_entities:
            return { "success": False, "error": "Data entity does not exist" }

        overlaps = self._find_active_schedule_conflicts(data_id, time_of_day, frequency)
        return { "success": True, "data": overlaps }

    def list_backup_jobs_for_data(self, data_id: str) -> dict:
        """
        List all backup jobs executed/created for a specific data entity (data_id).

        Args:
            data_id (str): The identifier of the data entity.

        Returns:
            dict: {
                "success": True,
                "data": List[BackupJobInfo]  # List of backup jobs for this data entity (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., data entity does not exist)
            }

        Constraints:
            - The provided data_id must exist in the system.
        """
        if data_id not in self.data_entities:
            return { "success": False, "error": "Data entity does not exist" }

        jobs = [
            job_info for job_info in self.backup_jobs.values()
            if job_info["data_id"] == data_id
        ]

        return { "success": True, "data": jobs }

    def list_backup_jobs_for_schedule(self, schedule_id: str) -> dict:
        """
        List all backup jobs triggered by a specific backup schedule.

        Args:
            schedule_id (str): The identifier of the backup schedule.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[BackupJobInfo],    # List of backup jobs associated with the schedule (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str    # Reason for failure, e.g. "Backup schedule does not exist"
                }

        Constraints:
            - The specified schedule_id must exist in the environment.
        """
        if schedule_id not in self.backup_schedules:
            return {"success": False, "error": "Backup schedule does not exist"}

        jobs = [
            job_info for job_info in self.backup_jobs.values()
            if job_info.get("schedule_id") == schedule_id
        ]
        return {"success": True, "data": jobs}

    def get_backup_job_by_id(self, job_id: str) -> dict:
        """
        Retrieve detailed information about a specific backup job given its job_id.

        Args:
            job_id (str): The unique identifier for the backup job.

        Returns:
            dict: {
                "success": True,
                "data": BackupJobInfo  # All metadata of the backup job
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. job not found
            }

        Constraints:
            - job_id must exist in the system.
        """
        backup_job = self.backup_jobs.get(job_id)
        if not backup_job:
            return { "success": False, "error": "Backup job not found" }
        return { "success": True, "data": backup_job }

    def create_backup_schedule(
        self,
        data_id: str,
        time_of_day: str,
        frequency: str,
        status: str
    ) -> dict:
        """
        Create a new backup schedule for a data entity.

        Args:
            data_id (str): The ID of the data entity to back up.
            time_of_day (str): Time for the backup (e.g., '22:00').
            frequency (str): Frequency of the backup (e.g., 'daily', 'weekly').
            status (str): Initial status of the backup schedule ('active' or 'inactive').

        Returns:
            dict: {
                "success": True,
                "message": "Backup schedule created",
                "schedule_id": <newly_created_schedule_id>
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - data_id must exist in data_entities.
            - The daily 00:00 slot can have only one active BackupSchedule system-wide.
            - Other slots disallow overlap only within the same data entity.
        """
        # Check data entity exists
        if data_id not in self.data_entities:
            return { "success": False, "error": "Data entity does not exist" }

        # Constraint: the guarded daily 00:00 slot is system-wide; other slots are per data entity.
        if status == "active":
            conflicts = self._find_active_schedule_conflicts(data_id, time_of_day, frequency)
            if conflicts:
                return {
                    "success": False,
                    "error": "An active overlapping backup schedule already exists at the same time and frequency."
                }

        # Generate unique schedule_id
        schedule_id = f"sched_{uuid.uuid4().hex[:8]}"

        schedule_info = {
            "schedule_id": schedule_id,
            "data_id": data_id,
            "time_of_day": time_of_day,
            "frequency": frequency,
            "status": status
        }
        self.backup_schedules[schedule_id] = schedule_info

        return {
            "success": True,
            "message": "Backup schedule created",
            "schedule_id": schedule_id
        }

    def modify_backup_schedule(
        self,
        schedule_id: str,
        time_of_day: Optional[str] = None,
        frequency: Optional[str] = None,
        status: Optional[str] = None
    ) -> dict:
        """
        Edit the time_of_day, frequency, or status of an existing backup schedule.
    
        Args:
            schedule_id (str): The backup schedule to modify.
            time_of_day (Optional[str]): New time of day (e.g., "02:00").
            frequency (Optional[str]): New frequency (e.g., "daily", "weekly").
            status (Optional[str]): New status (e.g., "active", "inactive").
    
        Returns:
            dict: {
                "success": True,
                "message": "Backup schedule modified successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - schedule_id must exist.
            - BackupSchedule must remain linked to a valid DataEntity.
            - The daily 00:00 slot can have only one active BackupSchedule system-wide.
            - Other slots disallow overlap only within the same data entity.
            - At least one of time_of_day, frequency, or status must be provided.
        """
        if schedule_id not in self.backup_schedules:
            return {"success": False, "error": "BackupSchedule does not exist."}
    
        if not any([time_of_day, frequency, status]):
            return {"success": False, "error": "No fields provided to modify."}

        schedule = self.backup_schedules[schedule_id]
        data_id = schedule["data_id"]

        # Check DataEntity existence (should always be true if valid schedule, but be safe)
        if data_id not in self.data_entities:
            return {"success": False, "error": "Associated DataEntity does not exist."}

        # Prepare new values for check
        new_time = time_of_day if time_of_day is not None else schedule["time_of_day"]
        new_freq = frequency if frequency is not None else schedule["frequency"]
        new_status = status if status is not None else schedule["status"]

        # Guarded windows are system-wide; other overlap checks remain per data entity.
        if new_status == "active":
            conflicts = self._find_active_schedule_conflicts(
                data_id,
                new_time,
                new_freq,
                exclude_schedule_id=schedule_id,
            )
            if conflicts:
                return {
                    "success": False,
                    "error": "BackupSchedule would overlap with another active schedule at the same time and frequency."
                }

        # Optionally, check that status is valid
        if status is not None:
            if status not in ("active", "inactive"):
                return {"success": False, "error": "Status must be 'active' or 'inactive'."}

        # Apply modifications
        if time_of_day is not None:
            schedule["time_of_day"] = time_of_day
        if frequency is not None:
            schedule["frequency"] = frequency
        if status is not None:
            schedule["status"] = status

        self.backup_schedules[schedule_id] = schedule

        return {
            "success": True,
            "message": "Backup schedule modified successfully."
        }

    def delete_backup_schedule(self, schedule_id: str) -> dict:
        """
        Remove (cancel) a backup schedule from the system by schedule_id.
        Also deletes all BackupJob records associated with this schedule.

        Args:
            schedule_id (str): The unique identifier of the backup schedule to remove.

        Returns:
            dict:
                Success: { "success": True, "message": "Backup schedule deleted" }
                Failure: { "success": False, "error": "Backup schedule does not exist" }

        Constraints:
            - schedule_id must exist in the system.
            - Deletes related BackupJob entries for this schedule.
        """
        if schedule_id not in self.backup_schedules:
            return { "success": False, "error": "Backup schedule does not exist" }

        # Remove backup schedule
        del self.backup_schedules[schedule_id]

        # Remove associated backup jobs
        jobs_to_delete = [job_id for job_id, job in self.backup_jobs.items() if job.get('schedule_id') == schedule_id]
        for job_id in jobs_to_delete:
            del self.backup_jobs[job_id]

        return { "success": True, "message": "Backup schedule deleted" }

    def set_schedule_status(self, schedule_id: str, status: str) -> dict:
        """
        Activate or deactivate a backup schedule (toggle between 'active' and 'inactive').

        Args:
            schedule_id (str): Identifier of the BackupSchedule to update.
            status (str): Target status ("active" or "inactive").

        Returns:
            dict: {
                "success": True,
                "message": "Schedule status updated to <status>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Schedule must exist.
            - Status must be "active" or "inactive".
        """
        if schedule_id not in self.backup_schedules:
            return { "success": False, "error": "Schedule does not exist" }
        if status not in ("active", "inactive"):
            return { "success": False, "error": "Invalid status. Must be 'active' or 'inactive'" }
        if status == "active":
            schedule = self.backup_schedules[schedule_id]
            conflicts = self._find_active_schedule_conflicts(
                schedule["data_id"],
                schedule["time_of_day"],
                schedule["frequency"],
                exclude_schedule_id=schedule_id,
            )
            if conflicts:
                return {
                    "success": False,
                    "error": "Schedule cannot be activated because another active schedule already occupies the same time and frequency."
                }
        self.backup_schedules[schedule_id]["status"] = status
        return { "success": True, "message": f"Schedule status updated to {status}" }


    def manually_trigger_backup_job(self, schedule_id: str, data_id: str) -> dict:
        """
        Immediately start a backup job for a given schedule and data entity (outside of scheduled time).

        Args:
            schedule_id (str): The backup schedule to use for this manual job.
            data_id (str): The data entity to back up.

        Returns:
            dict: On success:
                    {
                        "success": True,
                        "message": "Backup job manually triggered with job_id=<job_id>"
                    }
                  On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - BackupSchedule must exist and be "active".
            - DataEntity must exist and match the schedule's data_id.
            - Creates and starts a BackupJob immediately (status: "running"),
              with both scheduled_time and actual_start_time set to now.
            - Completes only job creation; actual backup completion is separate.
        """
        # Check schedule exists
        schedule = self.backup_schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Backup schedule does not exist"}
        # Check data exists
        data = self.data_entities.get(data_id)
        if not data:
            return {"success": False, "error": "Data entity does not exist"}
        # Schedule's data_id must match provided data_id
        if schedule["data_id"] != data_id:
            return {"success": False, "error": "Backup schedule is not linked to provided data entity"}
        # Schedule must be 'active'
        if schedule["status"] != "active":
            return {"success": False, "error": "Backup schedule is not active"}
    
        now_iso = datetime.utcnow().isoformat()
        job_id = str(uuid.uuid4())

        new_job: BackupJobInfo = {
            "job_id": job_id,
            "schedule_id": schedule_id,
            "data_id": data_id,
            "scheduled_time": now_iso,
            "actual_start_time": now_iso,
            "status": "running",
            # completion_time and result are absent now
        }

        self.backup_jobs[job_id] = new_job

        return {
            "success": True,
            "message": f"Backup job manually triggered with job_id={job_id}"
        }

    def update_backup_job_status(
        self,
        job_id: str,
        new_status: str,
        actual_start_time: Optional[str] = None,
        completion_time: Optional[str] = None,
        result: Optional[str] = None
    ) -> dict:
        """
        Manually adjust the status of a backup job.
    
        Args:
            job_id (str): The job to update.
            new_status (str): The new status ("scheduled", "running", "completed", "failed").
            actual_start_time (Optional[str]): Set if status moves to "running".
            completion_time (Optional[str]): Set if status moves to "completed"/"failed".
            result (Optional[str]): Result information for completed/failed jobs.

        Returns:
            dict: Success or failure information.

        Constraints:
            - The job must exist.
            - Only valid transitions are allowed:
                "scheduled" → "running"
                "running" → "completed"/"failed"
                "failed" → "scheduled" (reset)
            - Updates appropriate timestamps and result fields.
        """

        VALID_STATUSES = {"scheduled", "running", "completed", "failed"}
        if job_id not in self.backup_jobs:
            return {"success": False, "error": "Backup job not found"}

        if new_status not in VALID_STATUSES:
            return {"success": False, "error": "Invalid status value"}

        job = self.backup_jobs[job_id]
        current_status = job["status"]

        # Allowed transitions
        allowed = False
        if current_status == "scheduled" and new_status == "running":
            allowed = True
        elif current_status == "running" and new_status in {"completed", "failed"}:
            allowed = True
        elif current_status == "failed" and new_status == "scheduled":
            allowed = True  # Reset
        elif current_status == new_status:
            allowed = True  # Idempotent
        else:
            allowed = False
        if not allowed:
            return {"success": False, "error": f"Cannot change status from '{current_status}' to '{new_status}'"}

        # Status update logic
        job["status"] = new_status

        # Handle timestamp fields
        # Update actual_start_time if moving to running
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        if new_status == "running":
            job["actual_start_time"] = actual_start_time if actual_start_time is not None else now_iso
            job.pop("completion_time", None)
            job.pop("result", None)
        elif new_status in {"completed", "failed"}:
            job["completion_time"] = completion_time if completion_time is not None else now_iso
            if result is not None:
                job["result"] = result
        elif new_status == "scheduled":
            # Reset: Remove start/completion/result so job can be retried
            job.pop("actual_start_time", None)
            job.pop("completion_time", None)
            job.pop("result", None)

        return {"success": True, "message": f"Backup job '{job_id}' status updated to '{new_status}' successfully"}

    def delete_backup_job(self, job_id: str) -> dict:
        """
        Remove a backup job record from the backup job history.

        Args:
            job_id (str): The unique identifier of the backup job to be deleted.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Backup job <job_id> deleted."
                    }
                On failure (backup job does not exist):
                    {
                        "success": False,
                        "error": "Backup job not found."
                    }

        Constraints:
            - The backup job must exist in the system to be deleted.
            - No status or dependency checks are required for deletion.
        """
        if job_id not in self.backup_jobs:
            return {"success": False, "error": "Backup job not found."}
        del self.backup_jobs[job_id]
        return {"success": True, "message": f"Backup job {job_id} deleted."}

    def create_data_entity(
        self, 
        data_id: str, 
        name: str, 
        owner: str, 
        last_modified: str, 
        size: float
    ) -> dict:
        """
        Add a new data entity to the database management system.

        Args:
            data_id (str): Unique identifier for the data entity.
            name (str): Name of the data entity.
            owner (str): Owner of the data entity.
            last_modified (str): Last modified time (ISO timestamp).
            size (float): Size of the data entity.

        Returns:
            dict: {
                "success": True,
                "message": "Data entity <data_id> created."
            }
            or
            {
                "success": False,
                "error": "Data entity with this ID already exists."
            }
    
        Constraints:
            - data_id must be unique within self.data_entities.
        """
        if data_id in self.data_entities:
            return { "success": False, "error": "Data entity with this ID already exists." }
    
        self.data_entities[data_id] = {
            "data_id": data_id,
            "name": name,
            "owner": owner,
            "last_modified": last_modified,
            "size": size
        }
    
        return { "success": True, "message": f"Data entity {data_id} created." }


    def modify_data_entity(self, data_id: str, name: Optional[str] = None, owner: Optional[str] = None) -> dict:
        """
        Update metadata (name, owner) for an existing data entity.

        Args:
            data_id (str): Identifier for the data entity to modify.
            name (Optional[str]): New name for the data entity (if any).
            owner (Optional[str]): New owner for the data entity (if any).

        Returns:
            dict:
                On success: { "success": True, "message": "Data entity updated successfully" }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - data_id must exist in the data_entities.
            - At least one of `name` or `owner` must be provided.
            - Updates last_modified timestamp to current time.
        """
        # Check if data entity exists
        entity = self.data_entities.get(data_id)
        if not entity:
            return { "success": False, "error": "Data entity not found" }
    
        # Check if there is anything to update
        if name is None and owner is None:
            return { "success": False, "error": "No fields to update (name and owner not provided)" }
    
        # Perform the update(s)
        updated = False
        if name is not None:
            entity["name"] = name
            updated = True
        if owner is not None:
            entity["owner"] = owner
            updated = True

        if updated:
            entity["last_modified"] = datetime.utcnow().isoformat()
            self.data_entities[data_id] = entity
            return { "success": True, "message": "Data entity updated successfully" }
        else:
            return { "success": False, "error": "Nothing was updated" }

    def delete_data_entity(self, data_id: str) -> dict:
        """
        Remove a data entity and all associated backup schedules and backup jobs.

        Args:
            data_id (str): The identifier of the data entity to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Data entity and all associated schedules and jobs deleted."
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The data entity must exist.
            - All associated BackupSchedule and BackupJob records (by data_id and schedule_id) are also deleted.
        """
        if data_id not in self.data_entities:
            return {"success": False, "error": "Data entity does not exist."}

        # Find and delete all backup schedules for this data_id
        schedule_ids_to_delete = [
            schedule_id
            for schedule_id, schedule in self.backup_schedules.items()
            if schedule['data_id'] == data_id
        ]

        # Remove the backup schedules
        for schedule_id in schedule_ids_to_delete:
            del self.backup_schedules[schedule_id]

        # Find and delete all backup jobs for this data_id or schedules
        job_ids_to_delete = [
            job_id
            for job_id, job in self.backup_jobs.items()
            if job.get('data_id') == data_id or job.get('schedule_id') in schedule_ids_to_delete
        ]

        for job_id in job_ids_to_delete:
            del self.backup_jobs[job_id]

        # Remove the data entity itself
        del self.data_entities[data_id]

        return {
            "success": True,
            "message": "Data entity and all associated schedules and jobs deleted."
        }


class DatabaseManagementWithBackupScheduling(BaseEnv):
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

    def get_data_by_id(self, **kwargs):
        return self._call_inner_tool('get_data_by_id', kwargs)

    def list_all_data_entities(self, **kwargs):
        return self._call_inner_tool('list_all_data_entities', kwargs)

    def get_data_by_name(self, **kwargs):
        return self._call_inner_tool('get_data_by_name', kwargs)

    def list_backup_schedules_for_data(self, **kwargs):
        return self._call_inner_tool('list_backup_schedules_for_data', kwargs)

    def get_backup_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_backup_schedule_by_id', kwargs)

    def check_overlapping_schedules(self, **kwargs):
        return self._call_inner_tool('check_overlapping_schedules', kwargs)

    def list_backup_jobs_for_data(self, **kwargs):
        return self._call_inner_tool('list_backup_jobs_for_data', kwargs)

    def list_backup_jobs_for_schedule(self, **kwargs):
        return self._call_inner_tool('list_backup_jobs_for_schedule', kwargs)

    def get_backup_job_by_id(self, **kwargs):
        return self._call_inner_tool('get_backup_job_by_id', kwargs)

    def create_backup_schedule(self, **kwargs):
        return self._call_inner_tool('create_backup_schedule', kwargs)

    def modify_backup_schedule(self, **kwargs):
        return self._call_inner_tool('modify_backup_schedule', kwargs)

    def delete_backup_schedule(self, **kwargs):
        return self._call_inner_tool('delete_backup_schedule', kwargs)

    def set_schedule_status(self, **kwargs):
        return self._call_inner_tool('set_schedule_status', kwargs)

    def manually_trigger_backup_job(self, **kwargs):
        return self._call_inner_tool('manually_trigger_backup_job', kwargs)

    def update_backup_job_status(self, **kwargs):
        return self._call_inner_tool('update_backup_job_status', kwargs)

    def delete_backup_job(self, **kwargs):
        return self._call_inner_tool('delete_backup_job', kwargs)

    def create_data_entity(self, **kwargs):
        return self._call_inner_tool('create_data_entity', kwargs)

    def modify_data_entity(self, **kwargs):
        return self._call_inner_tool('modify_data_entity', kwargs)

    def delete_data_entity(self, **kwargs):
        return self._call_inner_tool('delete_data_entity', kwargs)
