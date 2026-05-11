# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Tuple, List, TypedDict
import datetime
from typing import List, Dict, Optional
from datetime import datetime
import time
from uuid import uuid4
import uuid
from typing import Dict



# Represents a single piece of machinery
class EquipmentInfo(TypedDict):
    equipment_id: str
    equipment_type: str
    operational_status: str
    location: str

# Represents an adjustable parameter for a specific equipment item
class EquipmentParameterInfo(TypedDict):
    equipment_id: str
    parameter_name: str
    current_value: float
    setpoint_value: float
    unit: str

# Encapsulates scheduled parameter adjustments
class ScheduleInfo(TypedDict):
    schedule_id: str
    equipment_id: str
    parameter_name: str
    target_value: float
    start_time: str
    end_time: str
    state: str

# Tracks scheduling and execution of maintenance events
class MaintenanceEventInfo(TypedDict):
    maintenance_id: str
    equipment_id: str
    event_type: str
    scheduled_time: str
    actual_time: str
    state: str

# Records all changes to equipment parameters
class ParameterChangeLogInfo(TypedDict):
    log_id: str
    equipment_id: str
    parameter_name: str
    old_value: float
    new_value: float
    change_time: str
    changed_by: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Equipment: {equipment_id: EquipmentInfo}
        self.equipment: Dict[str, EquipmentInfo] = {}

        # Equipment Parameters: {(equipment_id, parameter_name): EquipmentParameterInfo}
        self.parameters: Dict[Tuple[str, str], EquipmentParameterInfo] = {}

        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}

        # Maintenance Events: {maintenance_id: MaintenanceEventInfo}
        self.maintenance_events: Dict[str, MaintenanceEventInfo] = {}

        # Parameter Change Logs: {log_id: ParameterChangeLogInfo}
        self.parameter_change_logs: Dict[str, ParameterChangeLogInfo] = {}

        # Optional externally injected safe parameter range state.
        self._safe_parameter_range_state = None

        # Constraints:
        # - Parameter adjustments must respect safe operating ranges for each equipment and parameter.
        # - Schedules may not overlap in conflicting ways for the same parameter on the same piece of equipment.
        # - All parameter changes must be logged.
        # - Maintenance events can require the equipment to be in a specific operational status before execution.
        # - The real-time state must always reflect either an active schedule or the most recent parameter update.

    @staticmethod
    def _normalize_iso_datetime(value: str):
        if not isinstance(value, str):
            raise ValueError("Invalid datetime value")
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        return datetime.fromisoformat(normalized)

    @staticmethod
    def _is_safe_range_dict(value: Any) -> bool:
        return isinstance(value, dict) and "min_value" in value and "max_value" in value

    def _active_schedule_states(self):
        return {"scheduled", "ongoing", "pending", "active"}

    def _inactive_schedule_states(self):
        return {"cancelled", "canceled", "completed"}

    def get_equipment_info(self, equipment_id: str) -> dict:
        """
        Retrieve detailed information about a specific piece of equipment by its ID.

        Args:
            equipment_id (str): Unique identifier of the equipment.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": EquipmentInfo
                }
                OR
                {
                    "success": False,
                    "error": "Equipment ID not found"
                }

        Constraints:
            - The equipment_id must exist in the system.
        """
        if equipment_id not in self.equipment:
            return {"success": False, "error": "Equipment ID not found"}
        return {"success": True, "data": self.equipment[equipment_id]}

    def list_equipment(self) -> dict:
        """
        List all equipment units with their summary information.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EquipmentInfo],  # List of all equipment summary info (may be empty)
            }

        Notes:
            - Returns an empty list if there is no equipment present.
        """
        equipment_list = list(self.equipment.values())
        return {
            "success": True,
            "data": equipment_list
        }

    def get_equipment_operational_status(self, equipment_id: str) -> dict:
        """
        Retrieve the current operational status of a specific equipment.

        Args:
            equipment_id (str): The unique identifier for the equipment.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "equipment_id": str,
                            "operational_status": str
                        }
                    }
                On failure (equipment not found):
                    {
                        "success": False,
                        "error": "Equipment not found"
                    }

        Constraints:
            - The equipment_id must exist in the equipment list.
        """
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment not found" }
        eq = self.equipment[equipment_id]
        return {
            "success": True,
            "data": {
                "equipment_id": equipment_id,
                "operational_status": eq["operational_status"]
            }
        }

    def get_equipment_parameters(self, equipment_id: str) -> dict:
        """
        Retrieve all adjustable parameters for a given equipment, including their current and setpoint values.

        Args:
            equipment_id (str): ID of the equipment to query.

        Returns:
            dict: {
                "success": True,
                "data": List[EquipmentParameterInfo],  # Parameters for this equipment (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason if the equipment ID does not exist
            }

        Constraints:
            - equipment_id must exist in self.equipment.
        """
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment does not exist" }

        parameters = [
            param_info for (eq_id, _), param_info in self.parameters.items()
            if eq_id == equipment_id
        ]

        return { "success": True, "data": parameters }

    def get_parameter_info(self, equipment_id: str, parameter_name: str) -> dict:
        """
        Retrieve detailed information for a specific parameter of a given equipment.

        Args:
            equipment_id (str): The unique identifier of the equipment.
            parameter_name (str): The name of the parameter to look up.

        Returns:
            dict: {
                "success": True,
                "data": EquipmentParameterInfo  # If parameter exists for this equipment
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (equipment or parameter not found)
            }

        Constraints:
            - Both the equipment and parameter must exist.
        """
        if equipment_id not in self.equipment:
            return {"success": False, "error": f"Equipment '{equipment_id}' does not exist."}

        key = (equipment_id, parameter_name)
        if key not in self.parameters:
            return {
                "success": False,
                "error": f"Parameter '{parameter_name}' does not exist for equipment '{equipment_id}'."
            }

        return {
            "success": True,
            "data": self.parameters[key]
        }

    def get_safe_parameter_range(self, equipment_id: str, parameter_name: str) -> dict:
        """
        Retrieve the allowable (safe) operating range for a parameter on a specific equipment unit.
    
        Args:
            equipment_id (str): The unique ID of the equipment.
            parameter_name (str): The parameter to query for safe range.
        
        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "min_value": float,
                        "max_value": float
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }
            
        Constraints:
            - The equipment_id must exist in the system.
            - The parameter must exist for the equipment.
            - If the safe range cannot be found, return error.
        """
        if equipment_id not in self.equipment:
            return {"success": False, "error": "Equipment not found"}

        if (equipment_id, parameter_name) not in self.parameters:
            return {"success": False, "error": "Parameter does not exist for specified equipment"}

        parsed_override = self._resolve_safe_parameter_range_override(equipment_id, parameter_name)
        if parsed_override is not None:
            return {"success": True, "data": parsed_override}

        # (For this simulation, use a hardcoded safe range lookup - in real system this would come from DB/config)
        SAFE_PARAMETER_RANGES = {
            # Example: {(equipment_type, parameter_name): (min, max)}
            # These would need to be realistic per environment
            ("Pump", "Pressure"): (1.0, 10.0),
            ("Pump", "Speed"): (500.0, 3600.0),
            ("Oven", "Temperature"): (100.0, 450.0),
            ("Oven", "Humidity"): (0.0, 100.0),
            # Add more as needed
        }
        equipment_type = self.equipment[equipment_id]["equipment_type"]
        key = (equipment_type, parameter_name)
        if key not in SAFE_PARAMETER_RANGES:
            return {"success": False, "error": "Safe range not defined for this equipment and parameter"}
        min_value, max_value = SAFE_PARAMETER_RANGES[key]
        return {
            "success": True,
            "data": {
                "min_value": min_value,
                "max_value": max_value
            }
        }

    def _resolve_safe_parameter_range_override(self, equipment_id: str, parameter_name: str):
        raw_state = getattr(self, "_safe_parameter_range_state", None)
        if raw_state is None:
            return None

        parsed_state = raw_state
        if isinstance(parsed_state, str):
            try:
                parsed_state = json.loads(parsed_state)
            except Exception:
                return None

        if isinstance(parsed_state, dict):
            if self._is_safe_range_dict(parsed_state):
                return {
                    "min_value": float(parsed_state["min_value"]),
                    "max_value": float(parsed_state["max_value"]),
                }

            key = f"{equipment_id}:{parameter_name}"
            nested = parsed_state.get(key)
            if self._is_safe_range_dict(nested):
                return {
                    "min_value": float(nested["min_value"]),
                    "max_value": float(nested["max_value"]),
                }

            equipment_mapping = parsed_state.get(equipment_id)
            if isinstance(equipment_mapping, dict):
                nested = equipment_mapping.get(parameter_name)
                if self._is_safe_range_dict(nested):
                    return {
                        "min_value": float(nested["min_value"]),
                        "max_value": float(nested["max_value"]),
                    }
        return None

    def list_active_schedules(self, equipment_id: str, parameter_name: str = None) -> dict:
        """
        Retrieve all currently active (ongoing/future) schedules for a specific equipment.
        Optionally filter by parameter name.

        Args:
            equipment_id (str): The equipment to retrieve schedules for.
            parameter_name (str, optional): If given, filter to schedules for this parameter.

        Returns:
            dict:
                success: True if query ran, False if error (e.g. equipment not found).
                data: list of ScheduleInfo (may be empty if no matches).

        Constraints:
            - Equipment must exist.
            - Only schedules in 'scheduled', 'ongoing', or where end_time > now are returned.
        """

        # Validate equipment exists
        if equipment_id not in self.equipment:
            return {"success": False, "error": f"Equipment '{equipment_id}' does not exist"}

        results = []
        for schedule in self.schedules.values():
            if schedule["equipment_id"] != equipment_id:
                continue
            if parameter_name and schedule["parameter_name"] != parameter_name:
                continue

            state = schedule.get("state", "").lower()
            include = state in self._active_schedule_states()
            if include:
                results.append(schedule)

        return {"success": True, "data": results}


    def check_schedule_conflicts(
        self,
        equipment_id: str,
        parameter_name: str,
        start_time: str,
        end_time: str,
        ignore_schedule_id: Optional[str] = None,
    ) -> dict:
        """
        Check if a proposed parameter adjustment schedule for the given equipment and parameter
        will conflict (overlap in time) with existing schedules.

        Args:
            equipment_id (str): The equipment ID.
            parameter_name (str): The parameter name.
            start_time (str): Proposed schedule start time (ISO 8601 string).
            end_time (str): Proposed schedule end time (ISO 8601 string).
            ignore_schedule_id (Optional[str]): Schedule ID to ignore (e.g., if updating an existing one).

        Returns:
            dict:
              Success, possible conflict:
                {"success": True, "data": {"conflict": True, "conflicting_schedules": [ScheduleInfo, ...]}}
              Success, no conflict:
                {"success": True, "data": {"conflict": False}}
              Failure (invalid input):
                {"success": False, "error": <error message>}

        Constraints:
          - Considers only schedules with matching equipment_id and parameter_name,
            and with states not in ("canceled", "completed").
          - Two schedules "overlap" if intervals [start, end) intersect.
          - start_time must be < end_time.
        """
        # Validate time format and logical interval
        try:
            start_dt = self._normalize_iso_datetime(start_time)
            end_dt = self._normalize_iso_datetime(end_time)
        except Exception:
            return {"success": False, "error": "Invalid time format; must be ISO 8601."}
        if start_dt >= end_dt:
            return {"success": False, "error": "Start time must be before end time."}

        conflicts: List[ScheduleInfo] = []
        for s in self.schedules.values():
            if (
                s["equipment_id"] == equipment_id
                and s["parameter_name"] == parameter_name
                and str(s.get("state", "")).lower() in self._active_schedule_states()
                and (ignore_schedule_id is None or s["schedule_id"] != ignore_schedule_id)
            ):
                try:
                    s_start = self._normalize_iso_datetime(s["start_time"])
                    s_end = self._normalize_iso_datetime(s["end_time"])
                except Exception:
                    continue  # Skip invalid schedule entries

                # Intervals overlap iff: not (end <= s_start or start >= s_end)
                if not (end_dt <= s_start or start_dt >= s_end):
                    conflicts.append(s)

        if conflicts:
            return {
                "success": True,
                "data": {"conflict": True, "conflicting_schedules": conflicts}
            }
        else:
            return {
                "success": True,
                "data": {"conflict": False}
            }

    def get_maintenance_events(self, equipment_id: str) -> dict:
        """
        List scheduled and past maintenance events for a specific equipment.

        Args:
            equipment_id (str): The ID of the equipment whose maintenance events should be returned.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceEventInfo]  # May be empty if no events
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., "Equipment not found"
            }

        Constraints:
            - equipment_id must exist in the system.
        """
        if equipment_id not in self.equipment:
            return {"success": False, "error": "Equipment not found"}

        result = [
            event for event in self.maintenance_events.values()
            if event["equipment_id"] == equipment_id
        ]

        return {"success": True, "data": result}

    def get_parameter_change_history(self, equipment_id: str, parameter_name: str) -> dict:
        """
        Retrieve the history/log of parameter changes for a specific equipment parameter.

        Args:
            equipment_id (str): Unique identifier for the equipment.
            parameter_name (str): The parameter name whose change history is requested.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": List[ParameterChangeLogInfo]  # May be empty if no changes
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure (equipment or parameter does not exist)
                }

        Constraints:
            - The equipment_id must exist in the system.
            - The parameter_name for this equipment must exist in the system.
        """
        # Check equipment
        if equipment_id not in self.equipment:
            return { "success": False, "error": f"Equipment ID '{equipment_id}' does not exist." }
        # Check parameter for equipment
        if (equipment_id, parameter_name) not in self.parameters:
            return { "success": False, "error": f"Parameter '{parameter_name}' for equipment '{equipment_id}' does not exist." }
        # Collect logs
        result = [
            log for log in self.parameter_change_logs.values()
            if log["equipment_id"] == equipment_id and log["parameter_name"] == parameter_name
        ]
        return { "success": True, "data": result }

    def set_equipment_parameter(
        self,
        equipment_id: str,
        parameter_name: str,
        new_value: float,
        changed_by: str
    ) -> dict:
        """
        Immediately update parameter value for specified equipment, ensuring safe range and logging.

        Args:
            equipment_id (str): ID of the target equipment.
            parameter_name (str): The parameter name to update.
            new_value (float): The value to set.
            changed_by (str): Identifier for the actor making the change (user/system).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Parameter updated and logged successfully"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Equipment and parameter must exist.
            - New value must respect the safe range for the parameter.
            - All value changes must be logged (ParameterChangeLog).
            - Real-time parameter state must reflect the update.
        """

        # 1. Check equipment exists
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment not found" }

        param_key = (equipment_id, parameter_name)
        if param_key not in self.parameters:
            return { "success": False, "error": "Parameter not found for this equipment" }

        # 2. Fetch safe range using get_safe_parameter_range (must exist in class)
        if not hasattr(self, "get_safe_parameter_range"):
            return { "success": False, "error": "Safe parameter range mechanism not available" }

        safe_range_res = self.get_safe_parameter_range(equipment_id, parameter_name)
        if not safe_range_res.get("success"):
            return { "success": False, "error": "Safe range retrieval failed: " + safe_range_res.get("error", "") }
        safe_min = safe_range_res["data"]["min_value"]
        safe_max = safe_range_res["data"]["max_value"]

        # 3. Value must be within safe range
        if new_value < safe_min or new_value > safe_max:
            return {
                "success": False,
                "error": f"Value {new_value} out of safe range [{safe_min}, {safe_max}] for parameter '{parameter_name}'"
            }

        # 4. Update parameter value & setpoint
        param_info = self.parameters[param_key]
        old_value = param_info["current_value"]
        param_info["current_value"] = new_value
        param_info["setpoint_value"] = new_value  # Assume immediate action is also setpoint

        # 5. Add a ParameterChangeLog record
        log_id = str(uuid4())
        log_entry = {
            "log_id": log_id,
            "equipment_id": equipment_id,
            "parameter_name": parameter_name,
            "old_value": old_value,
            "new_value": new_value,
            "change_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "changed_by": changed_by,
        }
        self.parameter_change_logs[log_id] = log_entry

        # 6. Real-time state assumed up-to-date because parameter info updated
        return {
            "success": True,
            "message": "Parameter updated and logged successfully"
        }

    def schedule_parameter_adjustment(
        self,
        equipment_id: str,
        parameter_name: str,
        target_value: float,
        start_time: str,
        end_time: str,
        state: str
    ) -> dict:
        """
        Schedule a future or recurrent parameter adjustment for an equipment/parameter,
        with specified start/end time and schedule state.
    
        Args:
            equipment_id (str): The identifier of the equipment.
            parameter_name (str): Name of the parameter to adjust.
            target_value (float): The setpoint value to assign in the schedule.
            start_time (str): ISO-formatted start time of the scheduled adjustment.
            end_time (str): ISO-formatted end time of the scheduled adjustment.
            state (str): Initial schedule state ("pending", "active", etc.)
    
        Returns:
            dict:
                - On success: {"success": True, "message": "Scheduled parameter adjustment <schedule_id> created."}
                - On error: {"success": False, "error": str}
        Constraints:
            - Equipment and parameter must exist.
            - Target value must be within safe operating range.
            - Schedule times must be valid (start < end).
            - No conflicting/overlapping schedule for same equipment + parameter.
        """

        # Existence checks
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment does not exist." }
    
        if (equipment_id, parameter_name) not in self.parameters:
            return { "success": False, "error": "Parameter does not exist for this equipment." }
    
        # Time validity
        try:
            start_dt = self._normalize_iso_datetime(start_time)
            end_dt = self._normalize_iso_datetime(end_time)
        except Exception:
            return {"success": False, "error": "Invalid datetime format for start_time or end_time."}
        if start_dt >= end_dt:
            return {"success": False, "error": "start_time must be before end_time."}
    
        # Check safe operating range, if get_safe_parameter_range is available
        safe_range_method = getattr(self, "get_safe_parameter_range", None)
        if safe_range_method:
            safe_range_result = safe_range_method(equipment_id, parameter_name)
            if not safe_range_result.get("success", False):
                return {"success": False, "error": "Could not determine safe parameter range."}
            safe_min = safe_range_result["data"].get("min_value")
            safe_max = safe_range_result["data"].get("max_value")
            if target_value < safe_min or target_value > safe_max:
                return {
                    "success": False,
                    "error": f"Target value {target_value} not in safe range [{safe_min}, {safe_max}]."
                }
    
        conflict_result = self.check_schedule_conflicts(
            equipment_id=equipment_id,
            parameter_name=parameter_name,
            start_time=start_time,
            end_time=end_time,
        )
        if not conflict_result.get("success"):
            return {"success": False, "error": conflict_result.get("error", "Unable to validate schedule conflicts.")}
        if conflict_result["data"].get("conflict"):
            return {
                "success": False,
                "error": "Conflicting schedule exists for this parameter on the equipment."
            }

        # Generate unique schedule_id
        schedule_id = str(uuid.uuid4())
        new_schedule = {
            "schedule_id": schedule_id,
            "equipment_id": equipment_id,
            "parameter_name": parameter_name,
            "target_value": target_value,
            "start_time": start_time,
            "end_time": end_time,
            "state": state
        }
        self.schedules[schedule_id] = new_schedule

        return {
            "success": True,
            "message": f"Scheduled parameter adjustment {schedule_id} created."
        }

    def update_schedule(
        self,
        schedule_id: str,
        target_value: float = None,
        start_time: str = None,
        end_time: str = None,
        state: str = None
    ) -> dict:
        """
        Modify an existing schedule for a parameter adjustment (update timing, target value, or state).

        Args:
            schedule_id (str): Identifier for the schedule to update.
            target_value (float, optional): New value to adjust parameter to.
            start_time (str, optional): New start time for the schedule (ISO format).
            end_time (str, optional): New end time for the schedule (ISO format).
            state (str, optional): New state for the schedule (if allowed to be updated).

        Returns:
            dict: {
                "success": True,
                "message": "Schedule updated successfully"
            } OR {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The updated target_value must be within the safe range for the parameter (if provided).
            - The updated start_time/end_time must not cause schedule overlaps/conflicts for the same equipment and parameter.
            - Schedule must exist and be in updatable state.
            - At least one field must be provided for update.
        """
        # 1. Schedule exists?
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found"}

        # 2. State allows modification? (Assume allowed if state not in ['completed', 'canceled'])
        if str(schedule["state"]).lower() in ("completed", "canceled", "cancelled"):
            return {"success": False, "error": "Cannot modify a completed or canceled schedule"}

        # 3. At least one update provided
        if all(x is None for x in (target_value, start_time, end_time, state)):
            return {"success": False, "error": "No update parameters provided"}

        equipment_id = schedule["equipment_id"]
        parameter_name = schedule["parameter_name"]

        # 4. Check target_value within safe parameter range (if updating)
        if target_value is not None:
            safe_range = self.get_safe_parameter_range(equipment_id, parameter_name)
            if not safe_range.get("success"):
                return {"success": False, "error": "Unable to retrieve safe parameter range"}
            min_val = safe_range["data"]["min_value"]
            max_val = safe_range["data"]["max_value"]
            if not (min_val <= target_value <= max_val):
                return {"success": False, "error": f"Target value {target_value} out of safe range [{min_val}, {max_val}]"}

        # 5. Check schedule timing for conflicts (if updating start/end times)
        new_start = start_time if start_time is not None else schedule["start_time"]
        new_end = end_time if end_time is not None else schedule["end_time"]

        # Only check if updating time or target_value, because both can affect concurrent effect
        if start_time is not None or end_time is not None or target_value is not None:
            conflict_result = self.check_schedule_conflicts(
                equipment_id=equipment_id,
                parameter_name=parameter_name,
                start_time=new_start,
                end_time=new_end,
                ignore_schedule_id=schedule_id,
            )
            if not conflict_result.get("success"):
                return {"success": False, "error": conflict_result.get("error", "Unable to validate schedule conflicts")}
            if conflict_result["data"].get("conflict"):
                conflict_id = conflict_result["data"]["conflicting_schedules"][0]["schedule_id"]
                return {"success": False, "error": f"Schedule time overlaps with existing schedule {conflict_id}"}

        # 6. Perform updates
        if target_value is not None:
            schedule["target_value"] = target_value
        if start_time is not None:
            schedule["start_time"] = start_time
        if end_time is not None:
            schedule["end_time"] = end_time
        if state is not None:  # Assume free-form or validate as necessary
            schedule["state"] = state

        # Commit changes
        self.schedules[schedule_id] = schedule

        return {"success": True, "message": "Schedule updated successfully"}

    def cancel_schedule(self, schedule_id: str) -> dict:
        """
        Cancel (deactivate) an existing parameter adjustment schedule.

        Args:
            schedule_id (str): The ID of the schedule to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Schedule <schedule_id> cancelled."
            }
            or
            {
                "success": False,
                "error": "Schedule not found."
            }

        Constraints:
            - The schedule is not deleted for audit/history; its 'state' is set to 'cancelled'.
            - If the schedule is already cancelled, the operation is idempotent and considered successful.
            - System must preserve schedule info for operational optimization and audit.
        """
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            return { "success": False, "error": "Schedule not found." }
    
        if str(schedule.get("state", "")).lower() in {"cancelled", "canceled"}:
            return { "success": True, "message": f"Schedule {schedule_id} was already cancelled." }
    
        schedule["state"] = "cancelled"
        self.schedules[schedule_id] = schedule  # (dict is mutable, but explicit for clarity)

        return { "success": True, "message": f"Schedule {schedule_id} cancelled." }

    def log_parameter_change(
        self,
        equipment_id: str,
        parameter_name: str,
        old_value: float,
        new_value: float,
        change_time: str,
        changed_by: str
    ) -> dict:
        """
        Records a parameter change event in the historical logs.

        Args:
            equipment_id (str): The equipment involved in the change.
            parameter_name (str): The parameter that was changed.
            old_value (float): Value before the change.
            new_value (float): Value after the change.
            change_time (str): Timestamp of the change (ISO string or system format).
            changed_by (str): Who/what made the change.

        Returns:
            dict: {
                "success": True,
                "message": "Parameter change logged with id <log_id>"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - equipment_id and parameter_name must exist in the system.
            - change_time and changed_by must be provided and non-empty.
            - Values old_value and new_value must be floats.
            - Log ID is system-generated and unique.
        """
        if equipment_id not in self.equipment:
            return {"success": False, "error": f"Equipment '{equipment_id}' does not exist."}

        if (equipment_id, parameter_name) not in self.parameters:
            return {"success": False, "error": f"Parameter '{parameter_name}' for equipment '{equipment_id}' does not exist."}

        if change_time is None or str(change_time).strip() == "":
            return {"success": False, "error": "change_time must be provided and non-empty."}

        if changed_by is None or str(changed_by).strip() == "":
            return {"success": False, "error": "changed_by must be provided and non-empty."}

        # Defensive float conversion
        try:
            old_val = float(old_value)
            new_val = float(new_value)
        except Exception:
            return {"success": False, "error": "old_value and new_value must be floats."}

        # Auto-generate unique log_id
        log_id = str(uuid.uuid4())

        new_log: ParameterChangeLogInfo = {
            "log_id": log_id,
            "equipment_id": equipment_id,
            "parameter_name": parameter_name,
            "old_value": old_val,
            "new_value": new_val,
            "change_time": change_time,
            "changed_by": changed_by
        }

        self.parameter_change_logs[log_id] = new_log

        return {"success": True, "message": f"Parameter change logged with id {log_id}"}

    def force_update_operational_status(self, equipment_id: str, new_status: str) -> dict:
        """
        Forcibly update the operational status of a specified equipment.

        Args:
            equipment_id (str): The unique identifier of the equipment whose status should be changed.
            new_status (str): The desired operational status (e.g., 'idle', 'stopped').

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Operational status of equipment {equipment_id} updated to {new_status}"
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The equipment must exist in the system.
            - No explicit validation on status value; assumed to be controlled by caller.
            - The real-time state of the equipment is updated immediately.
        """
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return {"success": False, "error": f"Equipment '{equipment_id}' not found."}

        previous_status = equipment.get("operational_status")
        equipment["operational_status"] = new_status

        # Optionally could return previous vs new, but keeping concise per standard
        return {
            "success": True,
            "message": f"Operational status of equipment '{equipment_id}' updated to '{new_status}'."
        }

    def trigger_maintenance_event(self, maintenance_id: str, action: str, actual_time: str = None) -> dict:
        """
        Mark a maintenance event as started or completed, updating state and timestamps.

        Args:
            maintenance_id (str): The unique ID of the maintenance event to update.
            action (str): Either 'start' or 'complete', specifying which marker to perform.
            actual_time (str, optional): The timestamp at which the action occurs; required for 'complete', optional for 'start'.

        Returns:
            dict: 
                On success: {"success": True, "message": "Maintenance event marked as <state>."}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - Must check if action is valid.
            - Equipment may need to be in the proper operational_status before 'start' (if event_type or other field constrains).
            - For 'complete', event must be already in progress/in the correct state.
            - Updates actual_time and state on the event record.
        """

        # Check maintenance event exists
        event = self.maintenance_events.get(maintenance_id)
        if event is None:
            for candidate in self.maintenance_events.values():
                if isinstance(candidate, dict) and candidate.get("maintenance_id") == maintenance_id:
                    event = candidate
                    break
        if event is None:
            return {"success": False, "error": "Maintenance event not found."}

        equipment_id = event["equipment_id"]
        # Check associated equipment exists
        if equipment_id not in self.equipment:
            return {"success": False, "error": "Associated equipment not found."}
        equipment = self.equipment[equipment_id]

        # Action validation
        if action not in ("start", "complete"):
            return {"success": False, "error": "Invalid action type."}

        # Determine status checks (example: 'start' may require equipment to be 'idle' or 'stopped')
        required_status = "idle"  # This could vary with event_type; hardcoded here as example
        if action == "start":
            # Example check for operational_status; in real system may depend on event_type
            if event["state"] not in ("scheduled", "pending"):  # Only allow start if scheduled/pending
                return {"success": False, "error": f"Cannot start this maintenance event; current state: {event['state']}"}
            # Set state to in_progress, update actual_time
            event["state"] = "in_progress"
            if actual_time:
                event["actual_time"] = actual_time
            # else, leave unchanged or set to current real time if available (not specified here)

            self.maintenance_events[maintenance_id] = event
            return {"success": True, "message": "Maintenance event marked as in progress."}

        elif action == "complete":
            if event["state"] != "in_progress":
                return {"success": False, "error": f"Cannot complete maintenance event; not in progress (current state: {event['state']})."}
            # actual_time is required for completion
            if not actual_time:
                return {"success": False, "error": "actual_time is required to mark maintenance as completed."}
            event["state"] = "completed"
            event["actual_time"] = actual_time
            self.maintenance_events[maintenance_id] = event
            return {"success": True, "message": "Maintenance event marked as completed."}


    def refresh_real_time_state(self) -> dict:
        """
        Force an update so the equipment's real-time parameter value reflects the current
        active schedule or the most recent manual setpoint.

        All parameter changes made in this process will be logged, per environment constraints.
        Updates:
          - If a parameter has an active schedule at the current time, sets the real-time value to the schedule's target_value.
          - Else, ensures the real-time value equals the setpoint_value.
          - Changes are logged in parameter_change_logs.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Real-time parameter state refreshed for all equipment."
                }
        """
        now_ts = time.time()
        now_str = datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S")
        updated = 0

        for param_key, param_info in self.parameters.items():
            equipment_id = param_info["equipment_id"]
            parameter_name = param_info["parameter_name"]
            current_value = param_info["current_value"]

            # Find all schedules for this parameter with state "active" and current time in interval
            active_schedule = None
            for schedule in self.schedules.values():
                if (schedule["equipment_id"] == equipment_id and
                    schedule["parameter_name"] == parameter_name and
                    schedule["state"] == "active"):
                
                    try:
                        sched_start = datetime.fromisoformat(schedule["start_time"])
                        sched_end = datetime.fromisoformat(schedule["end_time"])
                        if sched_start <= datetime.fromtimestamp(now_ts) <= sched_end:
                            active_schedule = schedule
                            break  # Take the first valid active schedule
                    except Exception:
                        continue  # Skip schedules with invalid time format

            new_value = None
            if active_schedule is not None:
                new_value = active_schedule["target_value"]
            else:
                # Fallback to manual setpoint
                new_value = param_info["setpoint_value"]

            if current_value != new_value:
                # Update parameter real-time value
                old_value = param_info["current_value"]
                param_info["current_value"] = new_value

                # Log parameter change
                log_id = f"log_{len(self.parameter_change_logs) + 1}_{int(time.time()*1000)}"
                self.parameter_change_logs[log_id] = {
                    "log_id": log_id,
                    "equipment_id": equipment_id,
                    "parameter_name": parameter_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_time": now_str,
                    "changed_by": "system_refresh"
                }
                updated += 1

        return {
            "success": True,
            "message": f"Real-time parameter state refreshed for all equipment. {updated} parameter(s) updated."
        }


class IndustrialEquipmentControlSystem(BaseEnv):
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
            if key == "equipment" and isinstance(value, dict):
                normalized_equipment = {}
                for record in value.values():
                    if not isinstance(record, dict):
                        continue
                    equipment_id = record.get("equipment_id")
                    if equipment_id:
                        normalized_equipment[equipment_id] = copy.deepcopy(record)
                setattr(env, key, normalized_equipment)
                continue

            if key == "parameters" and isinstance(value, dict):
                normalized_parameters = {}
                for record in value.values():
                    if not isinstance(record, dict):
                        continue
                    equipment_id = record.get("equipment_id")
                    parameter_name = record.get("parameter_name")
                    if equipment_id and parameter_name:
                        normalized_parameters[(equipment_id, parameter_name)] = copy.deepcopy(record)
                setattr(env, key, normalized_parameters)
                continue

            if key == "schedules" and isinstance(value, dict):
                normalized_schedules = {}
                for record in value.values():
                    if not isinstance(record, dict):
                        continue
                    schedule_id = record.get("schedule_id")
                    if schedule_id:
                        normalized_schedules[schedule_id] = copy.deepcopy(record)
                setattr(env, key, normalized_schedules)
                continue

            if key == "maintenance_events" and isinstance(value, dict):
                normalized_events = {}
                for record in value.values():
                    if not isinstance(record, dict):
                        continue
                    maintenance_id = record.get("maintenance_id")
                    if maintenance_id:
                        normalized_events[maintenance_id] = copy.deepcopy(record)
                setattr(env, key, normalized_events)
                continue

            if key == "parameter_change_logs" and isinstance(value, dict):
                normalized_logs = {}
                for record in value.values():
                    if not isinstance(record, dict):
                        continue
                    log_id = record.get("log_id")
                    if log_id:
                        normalized_logs[log_id] = copy.deepcopy(record)
                setattr(env, key, normalized_logs)
                continue

            if key in {"get_safe_parameter_range", "safe_parameter_ranges"}:
                setattr(env, "_safe_parameter_range_state", copy.deepcopy(value))
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

    def get_equipment_info(self, **kwargs):
        return self._call_inner_tool('get_equipment_info', kwargs)

    def list_equipment(self, **kwargs):
        return self._call_inner_tool('list_equipment', kwargs)

    def get_equipment_operational_status(self, **kwargs):
        return self._call_inner_tool('get_equipment_operational_status', kwargs)

    def get_equipment_parameters(self, **kwargs):
        return self._call_inner_tool('get_equipment_parameters', kwargs)

    def get_parameter_info(self, **kwargs):
        return self._call_inner_tool('get_parameter_info', kwargs)

    def get_safe_parameter_range(self, **kwargs):
        return self._call_inner_tool('get_safe_parameter_range', kwargs)

    def list_active_schedules(self, **kwargs):
        return self._call_inner_tool('list_active_schedules', kwargs)

    def check_schedule_conflicts(self, **kwargs):
        return self._call_inner_tool('check_schedule_conflicts', kwargs)

    def get_maintenance_events(self, **kwargs):
        return self._call_inner_tool('get_maintenance_events', kwargs)

    def get_parameter_change_history(self, **kwargs):
        return self._call_inner_tool('get_parameter_change_history', kwargs)

    def set_equipment_parameter(self, **kwargs):
        return self._call_inner_tool('set_equipment_parameter', kwargs)

    def schedule_parameter_adjustment(self, **kwargs):
        return self._call_inner_tool('schedule_parameter_adjustment', kwargs)

    def update_schedule(self, **kwargs):
        return self._call_inner_tool('update_schedule', kwargs)

    def cancel_schedule(self, **kwargs):
        return self._call_inner_tool('cancel_schedule', kwargs)

    def log_parameter_change(self, **kwargs):
        return self._call_inner_tool('log_parameter_change', kwargs)

    def force_update_operational_status(self, **kwargs):
        return self._call_inner_tool('force_update_operational_status', kwargs)

    def trigger_maintenance_event(self, **kwargs):
        return self._call_inner_tool('trigger_maintenance_event', kwargs)

    def refresh_real_time_state(self, **kwargs):
        return self._call_inner_tool('refresh_real_time_state', kwargs)
