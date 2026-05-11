# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import time
import uuid



# VehicleInfo: vehicle state
class VehicleInfo(TypedDict):
    vehicle_id: str
    status: str  # e.g., "started", "stopped"
    battery_level: float
    last_command: str
    location: str  # could be enhanced to a tuple for coordinates
    performance_metric: float

# CommandLogEntry: command history for one or more vehicles
class CommandLogEntry(TypedDict):
    command_id: str
    vehicle_ids: List[str]
    command_type: str
    timestamp: str  # or float, depending on the implementation
    issued_by: str
    outcome: str

# FleetInfo: records set of vehicles under management
class FleetInfo(TypedDict, total=False):
    list_of_vehicle_ids: List[str]
    fleet_status: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for the autonomous vehicle fleet management environment.
        """

        # Vehicles: {vehicle_id: VehicleInfo}
        # Maps vehicle_id to their operational and resource state.
        self.vehicles: Dict[str, VehicleInfo] = {}

        # Command logs: {command_id: CommandLogEntry}
        # Tracks commands issued, per command_id, including targeted vehicle_ids.
        self.command_logs: Dict[str, CommandLogEntry] = {}

        # Fleet management: single record capturing all vehicle IDs and optional fleet status.
        self.fleet: FleetInfo = {"list_of_vehicle_ids": []}

        # Constraints:
        # - Each vehicle’s status can only be set to “started” if it is currently “stopped”.
        # - Battery levels must be current and kept updated before/after ops.
        # - Commands must be logged with timestamp and vehicle_ids.
        # - No command may be issued to a non-existent vehicle (vehicle_id must be in self.vehicles).

    def _effective_fleet_vehicle_ids(self) -> List[str]:
        """Return the active fleet composition used by fleet-level operations."""
        configured_ids = self.fleet.get("list_of_vehicle_ids", [])
        if configured_ids:
            return [vehicle_id for vehicle_id in configured_ids if vehicle_id in self.vehicles]
        return list(self.vehicles.keys())

    def get_vehicle_by_id(self, vehicle_id: str) -> dict:
        """
        Retrieve all operational and resource information for a given vehicle.

        Args:
            vehicle_id (str): The ID of the vehicle to query.

        Returns:
            dict: {
                "success": True,
                "data": VehicleInfo  # All fields for the vehicle
            }
            or
            {
                "success": False,
                "error": str  # Reason vehicle could not be retrieved (e.g., does not exist)
            }

        Constraints:
            - The vehicle_id must exist in the vehicle registry.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return { "success": False, "error": "Vehicle ID does not exist" }
        return { "success": True, "data": vehicle }

    def get_vehicle_status(self, vehicle_id: str) -> dict:
        """
        Get the current operational status ("started", "stopped") of a specific vehicle.

        Args:
            vehicle_id (str): Unique ID of the vehicle whose status is being queried.

        Returns:
            dict: 
             - On success: { "success": True, "data": <status: str> }
             - On failure: { "success": False, "error": "Vehicle not found" }
    
        Constraints:
            - The vehicle_id must exist in the registry (self.vehicles).
        """
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            return { "success": False, "error": "Vehicle not found" }
        return { "success": True, "data": vehicle['status'] }

    def get_vehicle_battery_level(self, vehicle_id: str) -> dict:
        """
        Query the current battery level of a specific vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict:
                {
                    "success": True,
                    "data": float  # The current battery level of the vehicle
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if the vehicle does not exist
                }

        Constraints:
            - The vehicle_id must correspond to an existing vehicle in the registry.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle does not exist" }
        battery_level = self.vehicles[vehicle_id]["battery_level"]
        return { "success": True, "data": battery_level }

    def list_all_vehicles(self) -> dict:
        """
        Retrieve all vehicles currently under management in the fleet.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[VehicleInfo]  # List of all vehicle records (may be empty)
            }

        Constraints:
            - None (simple state query).
        """
        fleet_vehicle_ids = self._effective_fleet_vehicle_ids()
        return {
            "success": True,
            "data": [self.vehicles[vehicle_id] for vehicle_id in fleet_vehicle_ids]
        }

    def list_vehicles_by_status(self, status: str) -> dict:
        """
        List all vehicles with a specified operational status.

        Args:
            status (str): The target status string to filter vehicles by (e.g., "started", "stopped").

        Returns:
            dict: {
                "success": True,
                "data": List[VehicleInfo]  # List of matching vehicles, possibly empty
            }
        Notes:
            - If no vehicles match, 'data' is an empty list; the call is still considered successful.
            - No error is returned for unknown statuses; simply no vehicles are found.
        """
        fleet_vehicle_ids = set(self._effective_fleet_vehicle_ids())
        result = [
            vehicle_info for vehicle_id, vehicle_info in self.vehicles.items()
            if vehicle_id in fleet_vehicle_ids and vehicle_info["status"] == status
        ]
        return { "success": True, "data": result }

    def get_fleet_info(self) -> dict:
        """
        Get a summary of the fleet: all vehicle_ids and (optional) the fleet's status.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "list_of_vehicle_ids": List[str],    # vehicle IDs (empty if none)
                    "fleet_status": Optional[str],       # fleet status or None
                }
            }
            On error (should not normally occur):
            {
                "success": False,
                "error": str
            }
        """
        # Defensive: Ensure structure is correct even if self.fleet was tampered with.
        vehicle_ids = self._effective_fleet_vehicle_ids()
        fleet_status = self.fleet.get("fleet_status", None)

        return {
            "success": True,
            "data": {
                "list_of_vehicle_ids": vehicle_ids,
                "fleet_status": fleet_status
            }
        }

    def get_vehicle_performance_metric(self, vehicle_id: str) -> dict:
        """
        Query the performance metric for a specific vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": float  # Performance metric value
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Vehicle not found"
                    }

        Constraints:
            - The vehicle must exist in the registry.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle not found" }
        performance_metric = self.vehicles[vehicle_id]["performance_metric"]
        return { "success": True, "data": performance_metric }

    def get_vehicle_location(self, vehicle_id: str) -> dict:
        """
        Get the last known location of a vehicle by its vehicle_id.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: 
                - On success: { "success": True, "data": <location: str> }
                - On failure: { "success": False, "error": "Vehicle not found" }

        Constraints:
            - The vehicle_id must exist in the vehicles registry.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return { "success": False, "error": "Vehicle not found" }
        return { "success": True, "data": vehicle.get("location", "") }

    def get_commands_for_vehicle(self, vehicle_id: str) -> dict:
        """
        Retrieve all command log entries pertaining to a specific vehicle,
        including timestamps and outcomes.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: {
                "success": True,
                "data": List[CommandLogEntry]  # May be empty if no commands found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., vehicle does not exist
            }

        Constraints:
            - The specified vehicle_id must exist in the vehicle registry.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle does not exist" }

        result = [
            log for log in self.command_logs.values()
            if vehicle_id in log.get("vehicle_ids", [])
        ]

        return { "success": True, "data": result }

    def get_command_log_by_id(self, command_id: str) -> dict:
        """
        Fetch details of a single command log entry via command_id.

        Args:
            command_id (str): Unique identifier of the command log entry.

        Returns:
            dict:
                - If found: { "success": True, "data": CommandLogEntry }
                - If not found: { "success": False, "error": "Command log entry not found" }
        """
        entry = self.command_logs.get(command_id)
        if entry is None:
            return {"success": False, "error": "Command log entry not found"}
        return {"success": True, "data": entry}


    def start_vehicle(self, vehicle_id: str, issued_by: str) -> dict:
        """
        Change a vehicle's status to "started" if it is currently "stopped", update battery, and log the operation.
    
        Args:
            vehicle_id (str): The unique identifier of the vehicle to be started.
            issued_by (str): Identifier or username for the command issuer (used in logging).
    
        Returns:
            dict: {
                "success": True,
                "message": "Vehicle <vehicle_id> started."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - Vehicle must exist in the self.vehicles registry.
            - Vehicle status can only transition to "started" if currently "stopped".
            - Battery level must be updated before and after the operation.
            - Operation must be logged with a timestamp and vehicle_ids.
        """
        # Check if vehicle exists
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": "Vehicle does not exist."}

        if vehicle_id not in self._effective_fleet_vehicle_ids():
            return {"success": False, "error": "Vehicle is not part of the active fleet"}
    
        # Check status
        if vehicle["status"] != "stopped":
            return {"success": False, "error": f"Vehicle status must be 'stopped' to start. Current status: {vehicle['status']}"}
    
        # Battery update simulation BEFORE
        # Here we can simulate battery check or refresh, or simply record the event. For simplicity, no value change.
        vehicle["battery_level"] = vehicle["battery_level"]  # No-op (placeholder for real update)

        # Perform state change
        vehicle["status"] = "started"
        vehicle["last_command"] = "start"
    
        # Battery update simulation AFTER
        # For realism, starting a vehicle may consume a little battery (e.g., -1%)
        vehicle["battery_level"] = max(0.0, vehicle["battery_level"] - 1.0)
    
        # Log the command
        command_id = str(uuid.uuid4())
        timestamp = str(time.time())
        command_entry = {
            "command_id": command_id,
            "vehicle_ids": [vehicle_id],
            "command_type": "start",
            "timestamp": timestamp,
            "issued_by": issued_by,
            "outcome": "success"
        }
        self.command_logs[command_id] = command_entry

        return {"success": True, "message": f"Vehicle {vehicle_id} started."}


    def stop_vehicle(self, vehicle_id: str, issued_by: str) -> dict:
        """
        Change a vehicle's status to "stopped" if it is currently "started".
        Update battery level (to represent immediate measurement, can be expanded), set last_command, and log operation.

        Args:
            vehicle_id (str): The unique identifier of the vehicle to stop.
            issued_by (str): Identifier of the operator issuing the command.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Vehicle <vehicle_id> stopped and logged successfully"
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Vehicle must exist.
            - Vehicle must be in "started" state.
            - Battery level must be up-to-date (here, simulated as unchanged or refreshed).
            - Command must be logged with current timestamp and all appropriate fields.
        """

        # Check vehicle existence
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": "Vehicle does not exist"}

        # Check vehicle is started
        if vehicle["status"] != "started":
            return {"success": False, "error": "Vehicle is not in 'started' status"}

        # Update vehicle status and last_command
        vehicle["status"] = "stopped"
        vehicle["last_command"] = "stop"

        # Battery level should be current; here we assume it's always up to date
        # To simulate a reading, you could assign a new value if needed.

        # Log the command
        command_id = str(uuid.uuid4())
        cur_time = str(time.time())  # Use string to match type hint, or use float if preferred
        self.command_logs[command_id] = {
            "command_id": command_id,
            "vehicle_ids": [vehicle_id],
            "command_type": "stop",
            "timestamp": cur_time,
            "issued_by": issued_by,
            "outcome": "success"
        }

        # Update in place
        self.vehicles[vehicle_id] = vehicle

        return {"success": True, "message": f"Vehicle {vehicle_id} stopped and logged successfully"}

    def batch_start_vehicles(self, vehicle_ids: List[str], issued_by: str) -> dict:
        """
        Start multiple vehicles in a single operation.

        Args:
            vehicle_ids (List[str]): List of vehicle IDs to be started.
            issued_by (str): User or system issuing the command.

        Returns:
            dict: {
                "success": True,
                "message": "Vehicles successfully started: [id1, id2, ...]"
            }
            or
            {
                "success": False,
                "error": "reason including vehicle_ids which failed validation"
            }

        Constraints:
            - Vehicles must exist in the fleet (self.vehicles).
            - Each vehicle status must be "stopped" to be started.
            - Battery levels must be accurate before and after (simulate a battery drop, e.g., -0.5% for start).
            - All started vehicles must be logged in a command log entry.
            - Operation is atomic: if any vehicle fails (not found or not stopped), none are started.
        """
        # Validate input
        if not vehicle_ids:
            return {"success": False, "error": "No vehicle IDs provided"}

        nonexistent_ids = [vid for vid in vehicle_ids if vid not in self.vehicles]
        if nonexistent_ids:
            return {"success": False, "error": f"Vehicles not found: {nonexistent_ids}"}

        inactive_ids = [vid for vid in vehicle_ids if vid not in self._effective_fleet_vehicle_ids()]
        if inactive_ids:
            return {"success": False, "error": f"Vehicles not in active fleet: {inactive_ids}"}

        not_stopped = [
            vid for vid in vehicle_ids
            if self.vehicles[vid]['status'] != 'stopped'
        ]
        if not_stopped:
            return {"success": False, "error": f"Vehicles not in 'stopped' status: {not_stopped}"}

        # All validations pass; perform the operation atomically
        for vid in vehicle_ids:
            # Simulate battery drop by 0.5 on start
            self.vehicles[vid]['battery_level'] = max(0.0, self.vehicles[vid]['battery_level'] - 0.5)
            self.vehicles[vid]['status'] = 'started'
            self.vehicles[vid]['last_command'] = 'start'

        # Log command
        command_id = f"cmd_{int(time.time()*1000)}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        log_entry = {
            "command_id": command_id,
            "vehicle_ids": vehicle_ids,
            "command_type": "batch_start",
            "timestamp": timestamp,
            "issued_by": issued_by,
            "outcome": "success"
        }
        self.command_logs[command_id] = log_entry

        return {
            "success": True,
            "message": f"Vehicles successfully started: {vehicle_ids}"
        }

    def update_vehicle_battery_level(self, vehicle_id: str, new_battery_level: float) -> dict:
        """
        Refresh or set the battery level of the specified vehicle to a new reading.

        Args:
            vehicle_id (str): The ID of the vehicle to update.
            new_battery_level (float): The new battery level to set (should be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Battery level updated for vehicle <vehicle_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - vehicle_id must be present in the vehicle registry.
            - Battery level must be non-negative.
        """
        if vehicle_id not in self.vehicles:
            return {"success": False, "error": f"Vehicle '{vehicle_id}' does not exist"}

        if not isinstance(new_battery_level, (float, int)):
            return {"success": False, "error": "Battery level must be a number"}

        if new_battery_level < 0:
            return {"success": False, "error": "Battery level must be non-negative"}

        self.vehicles[vehicle_id]["battery_level"] = float(new_battery_level)
        return {
            "success": True,
            "message": f"Battery level updated for vehicle {vehicle_id}"
        }

    def log_command(
        self,
        command_id: str,
        vehicle_ids: list,
        command_type: str,
        timestamp: str,
        issued_by: str,
        outcome: str
    ) -> dict:
        """
        Create and store a new command log entry.

        Args:
            command_id (str): Unique identifier for the command log entry.
            vehicle_ids (List[str]): List of vehicle IDs this command was issued to.
            command_type (str): Command type, e.g. 'start', 'stop'.
            timestamp (str): Timestamp of command issuance.
            issued_by (str): Identifier for who issued the command.
            outcome (str): Outcome/result of the command.

        Returns:
            dict: {
                'success': True,
                'message': str  # Confirmation message
            }
            or
            {
                'success': False,
                'error': str  # Description of error
            }

        Constraints:
            - command_id must be unique (not already in log)
            - All vehicle_ids must exist in self.vehicles
            - vehicle_ids must not be empty
        """
        if not isinstance(vehicle_ids, list) or not vehicle_ids:
            return { "success": False, "error": "vehicle_ids must be a non-empty list." }
        if command_id in self.command_logs:
            return { "success": False, "error": f"command_id '{command_id}' already exists." }
        invalid_ids = [vid for vid in vehicle_ids if vid not in self.vehicles]
        if invalid_ids:
            return { "success": False, "error": f"Invalid vehicle_ids: {invalid_ids}." }

        entry = {
            "command_id": command_id,
            "vehicle_ids": vehicle_ids.copy(),
            "command_type": command_type,
            "timestamp": timestamp,
            "issued_by": issued_by,
            "outcome": outcome
        }
        self.command_logs[command_id] = entry
        return { "success": True, "message": f"Command log entry created for command_id {command_id}." }

    def update_vehicle_performance_metric(self, vehicle_id: str, new_metric: float) -> dict:
        """
        Record new performance metric data for a given vehicle.

        Args:
            vehicle_id (str): Unique identifier of the vehicle whose metric should be updated.
            new_metric (float): New performance metric value.

        Returns:
            dict: {
                "success": True,
                "message": "Performance metric updated for vehicle <vehicle_id>"
            }
            or
            {
                "success": False,
                "error": "Reason (e.g., vehicle does not exist, invalid metric)"
            }

        Constraints:
            - vehicle_id must exist in self.vehicles.
            - new_metric should be a valid number (float/int).
        """
        # Check vehicle existence
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle does not exist" }

        # Check metric validity
        if not isinstance(new_metric, (float, int)):
            return { "success": False, "error": "Provided performance metric is not a number" }

        self.vehicles[vehicle_id]["performance_metric"] = float(new_metric)
        return {
            "success": True,
            "message": f"Performance metric updated for vehicle {vehicle_id}"
        }

    def update_vehicle_location(self, vehicle_id: str, location: str) -> dict:
        """
        Set or update the location attribute for a given vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle to update.
            location (str): The new location (coordinate or descriptor string).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Vehicle location updated." }
                On failure:
                    { "success": False, "error": "Vehicle does not exist." }

        Constraints:
            - Vehicle with vehicle_id must exist in the registry.
        """
        if vehicle_id not in self.vehicles:
            return {"success": False, "error": "Vehicle does not exist."}

        self.vehicles[vehicle_id]["location"] = location
        return {"success": True, "message": "Vehicle location updated."}

    def add_vehicle_to_fleet(self, vehicle_id: str) -> dict:
        """
        Add a new vehicle to the managed fleet, modifying list_of_vehicle_ids.

        Args:
            vehicle_id (str): The unique identifier of the vehicle to add.

        Returns:
            dict: {
                "success": True,
                "message": "Vehicle <vehicle_id> added to fleet"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The vehicle_id must exist in self.vehicles (registry).
            - The vehicle_id must not already be in the fleet.
            - Duplicates are NOT allowed in list_of_vehicle_ids.
        """
        # Check if vehicle exists
        if vehicle_id not in self.vehicles:
            return {"success": False, "error": "Vehicle does not exist"}
    
        # Check if already in the fleet
        current_ids = self.fleet.get("list_of_vehicle_ids", [])
        if vehicle_id in current_ids:
            return {"success": False, "error": "Vehicle already in fleet"}

        # Add to fleet
        current_ids.append(vehicle_id)
        self.fleet["list_of_vehicle_ids"] = current_ids
    
        return {"success": True, "message": f"Vehicle {vehicle_id} added to fleet"}

    def remove_vehicle_from_fleet(self, vehicle_id: str) -> dict:
        """
        Remove a vehicle from the managed fleet.

        Args:
            vehicle_id (str): The identifier of the vehicle to remove from the fleet.

        Returns:
            dict: {
                "success": True,
                "message": "Vehicle <vehicle_id> removed from fleet."
            }
            or
            {
                "success": False,
                "error": "Vehicle <vehicle_id> is not in the fleet."
            }

        Constraints:
            - The vehicle_id must currently be present in the fleet's list_of_vehicle_ids.
            - No action if vehicle_id is not part of the fleet (return error).
        """
        fleet_list = self.fleet.get("list_of_vehicle_ids", [])
        if vehicle_id not in fleet_list:
            return { "success": False, "error": f"Vehicle {vehicle_id} is not in the fleet." }
        # Remove the vehicle from the fleet list
        updated_list = [vid for vid in fleet_list if vid != vehicle_id]
        self.fleet["list_of_vehicle_ids"] = updated_list
        return { "success": True, "message": f"Vehicle {vehicle_id} removed from fleet." }

    def set_fleet_status(self, fleet_status: str) -> dict:
        """
        Set or update the optional global fleet_status for the group.

        Args:
            fleet_status (str): The status string to set for the fleet.

        Returns:
            dict: {
                "success": True,
                "message": "Fleet status updated to <fleet_status>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Input `fleet_status` must be a non-empty string.
            - Updates the singleton self.fleet["fleet_status"] value.
        """
        if not isinstance(fleet_status, str) or not fleet_status.strip():
            return { "success": False, "error": "Invalid fleet_status" }

        self.fleet["fleet_status"] = fleet_status.strip()
        return {
            "success": True,
            "message": f"Fleet status updated to {self.fleet['fleet_status']}"
        }


class AutonomousVehicleFleetManagementSystem(BaseEnv):
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

    def get_vehicle_by_id(self, **kwargs):
        return self._call_inner_tool('get_vehicle_by_id', kwargs)

    def get_vehicle_status(self, **kwargs):
        return self._call_inner_tool('get_vehicle_status', kwargs)

    def get_vehicle_battery_level(self, **kwargs):
        return self._call_inner_tool('get_vehicle_battery_level', kwargs)

    def list_all_vehicles(self, **kwargs):
        return self._call_inner_tool('list_all_vehicles', kwargs)

    def list_vehicles_by_status(self, **kwargs):
        return self._call_inner_tool('list_vehicles_by_status', kwargs)

    def get_fleet_info(self, **kwargs):
        return self._call_inner_tool('get_fleet_info', kwargs)

    def get_vehicle_performance_metric(self, **kwargs):
        return self._call_inner_tool('get_vehicle_performance_metric', kwargs)

    def get_vehicle_location(self, **kwargs):
        return self._call_inner_tool('get_vehicle_location', kwargs)

    def get_commands_for_vehicle(self, **kwargs):
        return self._call_inner_tool('get_commands_for_vehicle', kwargs)

    def get_command_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_command_log_by_id', kwargs)

    def start_vehicle(self, **kwargs):
        return self._call_inner_tool('start_vehicle', kwargs)

    def stop_vehicle(self, **kwargs):
        return self._call_inner_tool('stop_vehicle', kwargs)

    def batch_start_vehicles(self, **kwargs):
        return self._call_inner_tool('batch_start_vehicles', kwargs)

    def update_vehicle_battery_level(self, **kwargs):
        return self._call_inner_tool('update_vehicle_battery_level', kwargs)

    def log_command(self, **kwargs):
        return self._call_inner_tool('log_command', kwargs)

    def update_vehicle_performance_metric(self, **kwargs):
        return self._call_inner_tool('update_vehicle_performance_metric', kwargs)

    def update_vehicle_location(self, **kwargs):
        return self._call_inner_tool('update_vehicle_location', kwargs)

    def add_vehicle_to_fleet(self, **kwargs):
        return self._call_inner_tool('add_vehicle_to_fleet', kwargs)

    def remove_vehicle_from_fleet(self, **kwargs):
        return self._call_inner_tool('remove_vehicle_from_fleet', kwargs)

    def set_fleet_status(self, **kwargs):
        return self._call_inner_tool('set_fleet_status', kwargs)
