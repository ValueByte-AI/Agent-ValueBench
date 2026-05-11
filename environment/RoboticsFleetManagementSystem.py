# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime, timezone
import time
from datetime import datetime
from typing import Optional, Dict



class RobotInfo(TypedDict):
    robot_id: str
    health_status: str
    current_location: str
    operational_status: str
    last_check_in_time: str  # Timestamp in string format

class ActivityLogEntry(TypedDict):
    robot_id: str
    timestamp: str  # Could also be float (UNIX time), using str for generality
    activity_type: str
    detail: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for robotics fleet management.
        """
        # Robots: {robot_id: RobotInfo}
        self.robots: Dict[str, RobotInfo] = {}
        # Activity logs: List of all log entries for all robots
        self.activity_logs: List[ActivityLogEntry] = []

        # Constraints:
        # - Only registered robots (existing in self.robots) can be queried or commanded
        # - Health status must be periodically updated and always reflect the latest diagnostic report
        # - Each activity log entry must be associated with a valid robot_id and timestamp
        # - Commands can only be issued to robots in an appropriate operational status (e.g., not under maintenance or out of service)

    def is_robot_registered(self, robot_id: str) -> dict:
        """
        Check whether a given robot_id exists among registered robots.

        Args:
            robot_id (str): Identifier of the robot to check.

        Returns:
            dict: {
                "success": True,
                "registered": bool  # True if in self.robots, False otherwise
            }

        Notes:
            - A robot_id that is None or empty is considered not registered.
            - No error is raised for non-existence, as this is an existence check.
        """
        if not robot_id or not isinstance(robot_id, str):
            return {"success": True, "registered": False}
        return {"success": True, "registered": robot_id in self.robots}

    def get_robot_info(self, robot_id: str) -> dict:
        """
        Retrieve all configuration and status details for a given robot_id.

        Args:
            robot_id (str): Unique identifier of the robot.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": RobotInfo
                    }
                On failure (robot not found):
                    {
                        "success": False,
                        "error": "Robot not registered"
                    }

        Constraints:
            - Only registered robots (present in self.robots) can be queried.
        """
        if robot_id not in self.robots:
            return {
                "success": False,
                "error": "Robot not registered"
            }
        return {
            "success": True,
            "data": self.robots[robot_id]
        }

    def get_health_status(self, robot_id: str) -> dict:
        """
        Fetch the current health_status value for a given robot.

        Args:
            robot_id (str): The identifier of the robot to query.

        Returns:
            dict:
              - On success:
                  {"success": True, "data": str}  # The health_status value
              - On failure:
                  {"success": False, "error": str}  # E.g., robot not registered

        Constraints:
            - Only registered robots (existing in the robots database) can be queried.
        """
        if robot_id not in self.robots:
            return {"success": False, "error": "Robot not registered"}
        health_status = self.robots[robot_id].get("health_status")
        if health_status is None:
            return {"success": False, "error": "Health status attribute missing"}
        return {"success": True, "data": health_status}

    def get_location(self, robot_id: str) -> dict:
        """
        Fetch the current location for a robot.

        Args:
            robot_id (str): Unique identifier of the robot.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": <current_location:str> }
                On failure:
                    { "success": False, "error": "Robot not registered" }

        Constraints:
            - Only registered robots (i.e., robot_id in self.robots) can be queried.
        """
        if robot_id not in self.robots:
            return { "success": False, "error": "Robot not registered" }

        location = self.robots[robot_id]["current_location"]
        return { "success": True, "data": location }

    def get_operational_status(self, robot_id: str) -> dict:
        """
        Retrieve the current operational_status for a specified robot.

        Args:
            robot_id (str): Unique identifier for the robot.

        Returns:
            dict:
                On success: { "success": True, "data": <operational_status_str> }
                On failure (robot not found): { "success": False, "error": "Robot not registered" }
    
        Constraints:
            - Only registered robots may be queried.
        """
        if robot_id not in self.robots:
            return { "success": False, "error": "Robot not registered" }

        return { "success": True, "data": self.robots[robot_id]["operational_status"] }

    def get_last_check_in_time(self, robot_id: str) -> dict:
        """
        Retrieve the most recent check-in timestamp for a robot.

        Args:
            robot_id (str): The unique identifier of the robot.

        Returns:
            dict: {
                "success": True,
                "data": str,  # The last check-in time as a string (timestamp)
            }
            Or
            {
                "success": False,
                "error": str  # Description of error, e.g. "Robot not registered"
            }

        Constraints:
            - Only registered robots (existing in the database) can be queried.
        """
        robot = self.robots.get(robot_id)
        if not robot:
            return {
                "success": False,
                "error": "Robot not registered"
            }
        last_check_in = robot.get("last_check_in_time")
        if last_check_in is None:
            return {
                "success": False,
                "error": "No check-in record for the robot"
            }
        return {
            "success": True,
            "data": last_check_in
        }

    def list_all_robots(self) -> dict:
        """
        List the robot_ids (and brief info) of all registered robots in the fleet.

        Returns:
            dict: {
                "success": True,
                "data": List[dict(robot_id, health_status, operational_status, current_location, last_check_in_time)]
            }

        Notes:
            - If no robots are registered, returns an empty list in 'data'.
            - This operation does not error; the system is always considered initialized.
        """
        # Define brief info fields
        brief_fields = ["robot_id", "health_status", "operational_status", "current_location", "last_check_in_time"]

        result_list = [
            {k: info[k] for k in brief_fields}
            for info in self.robots.values()
        ]

        return {"success": True, "data": result_list}

    def list_activity_logs_for_robot(self, robot_id: str) -> dict:
        """
        Retrieve all activity log entries associated with the specified robot.

        Args:
            robot_id (str): The unique ID of the robot.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ActivityLogEntry]  # May be empty if no logs for the robot
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason robot is not registered
                    }

        Constraints:
            - Only registered robots (existing in self.robots) can be queried.
        """
        if robot_id not in self.robots:
            return { "success": False, "error": "Robot not registered" }

        logs = [
            entry for entry in self.activity_logs
            if entry["robot_id"] == robot_id
        ]
        return { "success": True, "data": logs }

    def get_latest_activity_log(self, robot_id: str, activity_type: str = None) -> dict:
        """
        Retrieve the latest activity log entry for the specified robot.
        If activity_type is provided, filter logs to only that activity type.

        Args:
            robot_id (str): The robot whose logs to query.
            activity_type (str, optional): If specified, only consider logs of this type.

        Returns:
            dict: {
                "success": True,
                "data": ActivityLogEntry | None  # Log entry dict, or None if not found
            }
            OR
            {
                "success": False,
                "error": str  # e.g., robot not registered
            }

        Constraints:
            - Only registered robots can be queried.
        """
        if robot_id not in self.robots:
            return {"success": False, "error": "Robot not registered"}

        # Filter logs for robot_id (and activity type if provided)
        matching_logs = [
            log for log in self.activity_logs
            if log["robot_id"] == robot_id and (activity_type is None or log["activity_type"] == activity_type)
        ]
        if not matching_logs:
            return {"success": True, "data": None}

        # Find the log with the latest timestamp (timestamps are strings, but assumed sortable)
        # If timestamps might not be sortable, a conversion (e.g., to float) would be required.
        latest_log = max(matching_logs, key=lambda log: log["timestamp"])
        return {"success": True, "data": latest_log}

    def list_robots_by_operational_status(self, operational_status: str) -> dict:
        """
        Retrieve all robots currently in a specified operational status.

        Args:
            operational_status (str): The target operational status (e.g., 'active', 'under maintenance').

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[RobotInfo],  # List of robots in this status (may be empty)
                }
        Constraints:
            - Only registered robots are queried.
            - If no robots match, returns an empty list.
        """
        robots_matched = [
            robot_info for robot_info in self.robots.values()
            if robot_info["operational_status"] == operational_status
        ]
        return { "success": True, "data": robots_matched }

    def update_health_status(self, robot_id: str, health_status: str) -> dict:
        """
        Update the health_status value for a specific robot. 
        Args:
            robot_id (str): The unique identifier for the robot.
            health_status (str): The new health status report for the robot.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Health status updated for robot <robot_id>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only registered robots (existing in self.robots) can be updated.
            - The new health status will reflect the latest diagnostics.
        """
        # Check valid input
        if not robot_id or robot_id not in self.robots:
            return {"success": False, "error": "Robot not registered"}

        if not isinstance(health_status, str) or not health_status.strip():
            return {"success": False, "error": "Invalid health status"}

        # Update the health_status
        self.robots[robot_id]['health_status'] = health_status

        # Optionally update last_check_in_time? Not specified by operation; skipping.

        return {
            "success": True,
            "message": f"Health status updated for robot {robot_id}"
        }

    def update_location(self, robot_id: str, new_location: str) -> dict:
        """
        Manually set or record a new current_location for a registered robot.

        Args:
            robot_id (str): The robot's unique identifier.
            new_location (str): The new location to assign to the robot.

        Returns:
            dict: {
                "success": True,
                "message": "Robot location updated"
            }
            or
            {
                "success": False,
                "error": "Robot not registered"
            }

        Constraints:
            - Only registered robots can have their location updated.
            - Each activity log entry created will be associated with a valid robot_id and current timestamp.
        """
        if robot_id not in self.robots:
            return { "success": False, "error": "Robot not registered" }

        # Update location
        self.robots[robot_id]['current_location'] = new_location

        # Log the update
        timestamp = datetime.now(timezone.utc).isoformat()
        activity_entry = {
            "robot_id": robot_id,
            "timestamp": timestamp,
            "activity_type": "location_update",
            "detail": f"Location manually set to '{new_location}'"
        }
        self.activity_logs.append(activity_entry)

        return { "success": True, "message": "Robot location updated" }

    def update_operational_status(self, robot_id: str, new_operational_status: str) -> dict:
        """
        Change the operational_status for a robot, enforcing constraints:
        - Only registered robots can be updated.
        - Cannot change status if robot is currently 'under maintenance' or 'out of service'.

        Args:
            robot_id (str): The identifier of the robot.
            new_operational_status (str): The new operational status to set.

        Returns:
            dict: 
                Success: { "success": True, "message": ... }
                Failure: { "success": False, "error": ... }
        """
        if robot_id not in self.robots:
            return { "success": False, "error": f"Robot '{robot_id}' is not registered." }

        current_status = self.robots[robot_id]["operational_status"]

        if current_status in ("under maintenance", "out of service"):
            return {
                "success": False,
                "error": f"Cannot change operational status: robot is currently '{current_status}'."
            }
        if new_operational_status == current_status:
            return {
                "success": True,
                "message": f"Robot '{robot_id}' already has operational_status '{new_operational_status}'."
            }

        self.robots[robot_id]["operational_status"] = new_operational_status
        return {
            "success": True,
            "message": f"Operational status updated for robot '{robot_id}' to '{new_operational_status}'."
        }

    def add_activity_log_entry(
        self, 
        robot_id: str, 
        timestamp: str, 
        activity_type: str, 
        detail: str
    ) -> dict:
        """
        Append a new activity log entry for a robot, ensuring robot_id and timestamp validity.

        Args:
            robot_id (str): The identifier for the robot to which this log entry belongs.
            timestamp (str): The time the activity occurred (as a string).
            activity_type (str): The type of the activity/event.
            detail (str): A description or detail of the activity.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Activity log entry added for robot <robot_id>." }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Only registered robots (existing in self.robots) can be logged.
            - Each activity log entry must be associated with a valid robot_id and a non-empty timestamp.
        """
        # Constraint: robot_id must exist
        if robot_id not in self.robots:
            return { "success": False, "error": f"Robot ID '{robot_id}' is not registered." }
        # Constraint: timestamp presence & not empty
        if not isinstance(timestamp, str) or not timestamp.strip():
            return { "success": False, "error": "Invalid or empty timestamp." }
        # Optionally check activity_type and detail presence; treat as always present (empty string OK)
        entry: ActivityLogEntry = {
            "robot_id": robot_id,
            "timestamp": timestamp,
            "activity_type": activity_type,
            "detail": detail,
        }
        self.activity_logs.append(entry)
        return { "success": True, "message": f"Activity log entry added for robot {robot_id}." }


    def issue_command_to_robot(self, robot_id: str, command: str) -> dict:
        """
        Issue an operational command to the specified robot if it is registered and in a suitable operational status.
    
        Args:
            robot_id (str): Unique identifier of the robot to receive the command.
            command (str): The command to be issued to the robot.
    
        Returns:
            dict: {
                "success": True,
                "message": "Command <command> issued to robot <robot_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Only registered robots can be commanded.
            - Robot must not be under 'maintenance' or 'out_of_service' status in order to accept commands.
            - Each command issued is recorded in the activity log with type 'command_issued'.
        """

        # Check if robot is registered
        if robot_id not in self.robots:
            return {"success": False, "error": f"Robot '{robot_id}' is not registered."}

        robot = self.robots[robot_id]
        # Define forbidden statuses.
        forbidden_statuses = {
            "maintenance",
            "under maintenance",
            "out_of_service",
            "out of service",
        }

        if robot["operational_status"].lower() in forbidden_statuses:
            return {
                "success": False,
                "error": f"Cannot issue command: Robot '{robot_id}' is in '{robot['operational_status']}' status."
            }
    
        # Check for empty command
        if not command or not command.strip():
            return {"success": False, "error": "Command cannot be empty."}

        # All checks pass: log the command
        timestamp = str(time.time())
        self.activity_logs.append({
            "robot_id": robot_id,
            "timestamp": timestamp,
            "activity_type": "command_issued",
            "detail": command
        })

        return {
            "success": True,
            "message": f"Command '{command}' issued to robot '{robot_id}'."
        }


    def check_in_robot(self, robot_id: str, health_status: Optional[str] = None) -> Dict[str, str]:
        """
        Updates the robot's last_check_in_time to the current timestamp.
        Optionally refreshes the health_status if a new diagnostic value is provided.
        Also records an activity log entry for the check-in.

        Args:
            robot_id (str): The identifier of the robot to check-in.
            health_status (Optional[str]): Optional new health_status to set from diagnostics.

        Returns:
            dict: {
                "success": True,
                "message": "Robot <robot_id> checked in, last_check_in_time updated"
            }
            or
            {
                "success": False,
                "error": "Robot not registered"
            }

        Constraints:
            - Robot must be registered (exist in the system).
            - If health_status is given, must update it to reflect latest diagnosis.
            - Each activity log must be associated with valid robot_id and timestamp.
        """
        if robot_id not in self.robots:
            return {"success": False, "error": "Robot not registered"}

        now_str = datetime.utcnow().isoformat() + 'Z'  # Standard UTC ISO format

        # Update robot info
        self.robots[robot_id]["last_check_in_time"] = now_str

        detail_msg = f"Checked in at {now_str}"
        if health_status is not None:
            self.robots[robot_id]["health_status"] = health_status
            detail_msg += f"; health_status updated to {health_status}"

        # Activity log
        log_entry = {
            "robot_id": robot_id,
            "timestamp": now_str,
            "activity_type": "check-in",
            "detail": detail_msg
        }
        self.activity_logs.append(log_entry)

        return {
            "success": True,
            "message": f"Robot {robot_id} checked in, last_check_in_time updated"
        }


class RoboticsFleetManagementSystem(BaseEnv):
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

    def is_robot_registered(self, **kwargs):
        return self._call_inner_tool('is_robot_registered', kwargs)

    def get_robot_info(self, **kwargs):
        return self._call_inner_tool('get_robot_info', kwargs)

    def get_health_status(self, **kwargs):
        return self._call_inner_tool('get_health_status', kwargs)

    def get_location(self, **kwargs):
        return self._call_inner_tool('get_location', kwargs)

    def get_operational_status(self, **kwargs):
        return self._call_inner_tool('get_operational_status', kwargs)

    def get_last_check_in_time(self, **kwargs):
        return self._call_inner_tool('get_last_check_in_time', kwargs)

    def list_all_robots(self, **kwargs):
        return self._call_inner_tool('list_all_robots', kwargs)

    def list_activity_logs_for_robot(self, **kwargs):
        return self._call_inner_tool('list_activity_logs_for_robot', kwargs)

    def get_latest_activity_log(self, **kwargs):
        return self._call_inner_tool('get_latest_activity_log', kwargs)

    def list_robots_by_operational_status(self, **kwargs):
        return self._call_inner_tool('list_robots_by_operational_status', kwargs)

    def update_health_status(self, **kwargs):
        return self._call_inner_tool('update_health_status', kwargs)

    def update_location(self, **kwargs):
        return self._call_inner_tool('update_location', kwargs)

    def update_operational_status(self, **kwargs):
        return self._call_inner_tool('update_operational_status', kwargs)

    def add_activity_log_entry(self, **kwargs):
        return self._call_inner_tool('add_activity_log_entry', kwargs)

    def issue_command_to_robot(self, **kwargs):
        return self._call_inner_tool('issue_command_to_robot', kwargs)

    def check_in_robot(self, **kwargs):
        return self._call_inner_tool('check_in_robot', kwargs)
