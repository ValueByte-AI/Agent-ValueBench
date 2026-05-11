# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



# Vehicle entity and attributes
class VehicleInfo(TypedDict):
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: str
    specs: Dict[str, Any]           # Spec details (parameter_name: definition/spec)
    operational_param: Dict[str, Any]  # Current operational parameters (parameter_name: value)

# OperationalParameter entity and attributes
class OperationalParameterInfo(TypedDict):
    vehicle_id: str
    parameter_name: str
    value: float
    timestamp: str  # ISO string or epoch

# MaintenanceRecord entity and attributes
class MaintenanceRecordInfo(TypedDict):
    cord_id: str
    vehicle_id: str
    service_type: str
    date: str   # ISO string
    description: str
    performed_by: str

# DiagnosticRecord entity and attributes
class DiagnosticRecordInfo(TypedDict):
    cord_id: str
    vehicle_id: str
    diagnostic_code: str
    date: str   # ISO string
    description: str
    resolved: bool

class _GeneratedEnvImpl:
    def __init__(self):
        # Vehicles: {vehicle_id: VehicleInfo}
        self.vehicles: Dict[str, VehicleInfo] = {}
        # Operational Parameters: {vehicle_id: List[OperationalParameterInfo]}
        self.operational_parameters: Dict[str, List[OperationalParameterInfo]] = {}
        # Maintenance Records: {cord_id: MaintenanceRecordInfo}
        self.maintenance_records: Dict[str, MaintenanceRecordInfo] = {}
        # Diagnostic Records: {cord_id: DiagnosticRecordInfo}
        self.diagnostic_records: Dict[str, DiagnosticRecordInfo] = {}

        # --- Constraints (to enforce in future methods): ---
        # - Each vehicle_id must be unique and correspond to a registered vehicle.
        # - Only valid operational parameters can be queried or updated per vehicle (as defined in specs).
        # - Maintenance and diagnostic records must reference a valid vehicle.
        # - Operational parameter queries must return the most recent value (unless a historical query is explicitly requested).

    def get_vehicle_info(self, vehicle_id: str) -> dict:
        """
        Retrieve all information and specifications for a given vehicle_id.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: {
                "success": True,
                "data": VehicleInfo  # Complete vehicle information and specs
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., "Vehicle ID does not exist")
            }

        Constraints:
            - The vehicle_id must correspond to a registered vehicle.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            return {
                "success": False,
                "error": "Vehicle ID does not exist"
            }
        return {
            "success": True,
            "data": vehicle
        }

    def list_all_vehicles(self) -> dict:
        """
        Return a list of all registered vehicles in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[VehicleInfo]  # List of registered vehicle info (may be empty)
            }
        """
        vehicle_list = list(self.vehicles.values())
        return { "success": True, "data": vehicle_list }

    def get_vehicle_specs(self, vehicle_id: str) -> dict:
        """
        Retrieve the full dictionary of valid operational parameters (specs) for a given vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict:
                On success:
                    { "success": True, "data": Dict[str, Any] }  # specs dictionary (parameter_name: specification)
                On failure:
                    { "success": False, "error": "Vehicle does not exist" }

        Constraints:
            - The referenced vehicle_id must exist in the system.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return { "success": False, "error": "Vehicle does not exist" }
        specs = vehicle.get("specs", {})
        return { "success": True, "data": specs }

    def validate_vehicle_id(self, vehicle_id: str) -> dict:
        """
        Check if a vehicle_id exists and is currently registered in the system.

        Args:
            vehicle_id (str): The unique identifier of the vehicle to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if registered, False if not
            }

        Notes:
            - No error is returned if the vehicle does not exist; "data" is simply False.
            - Assumes vehicle_id is a string.
        """
        if not isinstance(vehicle_id, str):
            return { "success": False, "error": "vehicle_id must be a string" }

        exists = vehicle_id in self.vehicles
        return { "success": True, "data": exists }

    def validate_operational_parameter(self, vehicle_id: str, parameter_name: str) -> dict:
        """
        Check if a given operational parameter name is valid for the specified vehicle according to the vehicle's specs.

        Args:
            vehicle_id (str): Unique identifier for the vehicle.
            parameter_name (str): The operational parameter name to validate.

        Returns:
            dict: {
                "success": True,
                "valid": bool   # True if parameter_name is defined for this vehicle, otherwise False
            }
            or
            {
                "success": False,
                "error": str    # Error description, e.g. vehicle not found
            }

        Constraints:
            - vehicle_id must exist in the vehicles dict.
            - Validity is determined by whether parameter_name exists as a key in vehicle's specs.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}

        is_valid = parameter_name in vehicle.get("specs", {})
        return {"success": True, "valid": is_valid}

    def get_operational_param_latest(self, vehicle_id: str, parameter_name: str) -> dict:
        """
        Retrieve the most recent value and timestamp for a specified operational parameter of a vehicle.

        Args:
            vehicle_id (str): The unique ID of the vehicle.
            parameter_name (str): The operational parameter's name.

        Returns:
            dict: {
                "success": True,
                "data": {"value": float, "timestamp": str}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Vehicle must be registered (exists in self.vehicles).
            - parameter_name must be a valid operational parameter for the vehicle (as per its 'specs').
            - Returns the latest (most recently timestamped) value for that parameter; if no value found, returns error.
        """
        # Check vehicle existence
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            return {"success": False, "error": "Vehicle ID does not exist"}

        # Check if parameter is valid per specs
        if parameter_name not in vehicle.get("specs", {}):
            return {"success": False, "error": "Invalid operational parameter for this vehicle"}

        # Get operational parameter records for vehicle
        param_history = self.operational_parameters.get(vehicle_id, [])
        # Filter for the desired parameter_name
        filtered = [
            p for p in param_history
            if p["parameter_name"] == parameter_name
        ]
        if not filtered:
            return {"success": False, "error": "No records found for this parameter"}

        # Find the latest by timestamp (assuming ISO string or epoch, lexically sortable)
        # If timestamps are ISO strings, sorting works; if epoch, strings still sort correctly.

        latest = max(filtered, key=lambda p: p["timestamp"])
        return {
            "success": True,
            "data": {"value": latest["value"], "timestamp": latest["timestamp"]}
        }

    def get_operational_param_history(self, vehicle_id: str, parameter_name: str) -> dict:
        """
        Retrieve the full history (values/timestamps) of a specified operational parameter for a given vehicle.

        Args:
            vehicle_id (str): The vehicle's unique identifier.
            parameter_name (str): The name of the operational parameter.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[OperationalParameterInfo]  # May be empty if no history.
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., unknown vehicle or invalid parameter.
                    }

        Constraints:
            - vehicle_id must refer to a registered vehicle.
            - parameter_name must be a valid parameter for the vehicle (per vehicle's specs).
            - Only returns records for the specific vehicle and parameter.
        """
        if vehicle_id not in self.vehicles:
            return {"success": False, "error": "Unknown vehicle_id"}
    
        vehicle_info = self.vehicles[vehicle_id]
        if parameter_name not in vehicle_info.get("specs", {}):
            return {"success": False, "error": "Invalid operational parameter for vehicle"}

        # Fetch all records for the vehicle, filter by parameter_name
        history = []
        for param_record in self.operational_parameters.get(vehicle_id, []):
            if param_record["parameter_name"] == parameter_name:
                history.append(param_record)

        return {"success": True, "data": history}

    def get_latest_operational_params_all(self, vehicle_id: str) -> dict:
        """
        Retrieve the latest value and timestamp of all operational parameters defined in the given vehicle's specs.

        Args:
            vehicle_id (str): The vehicle whose operational parameters to query.

        Returns:
            dict: 
                Success:
                {
                    "success": True,
                    "data": {
                        parameter_name: {
                            "value": float or None,
                            "timestamp": str or None
                        },
                        ... for all parameters in specs
                    }
                }
                Failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - vehicle_id must correspond to a registered vehicle.
            - Only parameters valid per vehicle's specs are included.
            - If no history exists for a parameter, its value and timestamp are None.
        """
        # Check vehicle exists
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": "Vehicle not found"}

        specs = vehicle.get("specs", {})
        param_names = list(specs.keys())

        # Fetch all parameter history for this vehicle, if any
        param_history = self.operational_parameters.get(vehicle_id, [])

        # Build for each parameter the latest value (if available)
        latest_map = {name: {"value": None, "timestamp": None} for name in param_names}
        # We'll traverse in reversed history to try find latest fast, 
        # but since timestamps are not guaranteed in order, we must compare
        for name in param_names:
            latest_rec = None
            for rec in param_history:
                if rec["parameter_name"] == name:
                    # Find the latest timestamp
                    if (latest_rec is None) or (rec["timestamp"] > latest_rec["timestamp"]):
                        latest_rec = rec
            if latest_rec:
                latest_map[name] = {
                    "value": latest_rec["value"],
                    "timestamp": latest_rec["timestamp"]
                }

        return {"success": True, "data": latest_map}

    def get_maintenance_records(self, vehicle_id: str) -> dict:
        """
        Retrieve all maintenance records associated with a specified vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceRecordInfo],  # List of records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason, e.g. "Vehicle not found"
            }

        Constraints:
            - vehicle_id must correspond to a registered vehicle.
        """
        if vehicle_id not in self.vehicles:
            return {"success": False, "error": "Vehicle not found"}

        records = [
            record for record in self.maintenance_records.values()
            if record["vehicle_id"] == vehicle_id
        ]

        return {"success": True, "data": records}

    def get_diagnostic_records(self, vehicle_id: str) -> dict:
        """
        Retrieve all diagnostic records associated with a specific vehicle.

        Args:
            vehicle_id (str): The unique identifier of the vehicle.

        Returns:
            dict: 
                - If vehicle exists:
                    {
                      "success": True,
                      "data": List[DiagnosticRecordInfo]  # List may be empty if no records.
                    }
                - If vehicle_id not found:
                    {
                      "success": False,
                      "error": "Vehicle ID not found"
                    }

        Constraints:
            - The vehicle_id must correspond to a registered vehicle.
            - Only diagnostic records referencing this vehicle_id are returned.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle ID not found" }

        # Collect records with matching vehicle_id
        result = [
            record for record in self.diagnostic_records.values()
            if record["vehicle_id"] == vehicle_id
        ]
        return { "success": True, "data": result }

    def get_maintenance_record_by_id(self, cord_id: str) -> dict:
        """
        Retrieve a single maintenance record by its unique ID (cord_id).

        Args:
            cord_id (str): The unique maintenance record identifier.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": MaintenanceRecordInfo  # The full info dict for the maintenance record.
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if not found.
                }

        Constraints:
            - The cord_id must exist in maintenance_records.
        """
        record = self.maintenance_records.get(cord_id)
        if record is None:
            return { "success": False, "error": f"Maintenance record with cord_id '{cord_id}' does not exist." }
        return { "success": True, "data": record }

    def get_diagnostic_record_by_id(self, cord_id: str) -> dict:
        """
        Retrieve a single diagnostic record by its unique cord_id.

        Args:
            cord_id (str): The unique identifier of the diagnostic record.

        Returns:
            dict: {
                "success": True,
                "data": DiagnosticRecordInfo
            }
            or
            {
                "success": False,
                "error": str  # If the record is not found
            }

        Constraints:
            - cord_id must exist in the diagnostic records.
        """
        record = self.diagnostic_records.get(cord_id)
        if not record:
            return { "success": False, "error": "Diagnostic record not found" }
        return { "success": True, "data": record }

    def log_operational_parameter(
        self,
        vehicle_id: str,
        parameter_name: str,
        value: float,
        timestamp: str
    ) -> dict:
        """
        Add (log) a new operational parameter measurement for a vehicle. 
        Validation includes existence of the vehicle and parameter_name within its specs.

        Args:
            vehicle_id (str): The ID of the vehicle.
            parameter_name (str): Name of the operational parameter.
            value (float): The measured value.
            timestamp (str): Measurement timestamp (ISO format or epoch).

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Operational parameter logged for vehicle <vehicle_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - vehicle_id must exist and be unique.
            - parameter_name must be defined in specs for the vehicle.
        """
        # 1. Vehicle existence check
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": f"Vehicle ID '{vehicle_id}' does not exist." }
    
        vehicle = self.vehicles[vehicle_id]
        # 2. Parameter validity check in specs
        if parameter_name not in vehicle.get("specs", {}):
            return { "success": False, "error": f"Parameter '{parameter_name}' is not valid for vehicle '{vehicle_id}'." }
        # 3. Value type check (optional but safe)
        if not isinstance(value, (float, int)):
            return { "success": False, "error": "Value must be a number (float or int)." }

        # 4. Add the operational parameter record
        param_info = {
            "vehicle_id": vehicle_id,
            "parameter_name": parameter_name,
            "value": float(value),
            "timestamp": timestamp
        }
        if vehicle_id not in self.operational_parameters:
            self.operational_parameters[vehicle_id] = []
        self.operational_parameters[vehicle_id].append(param_info)

        # 5. Update the vehicle's current operational_param value for this parameter
        vehicle["operational_param"][parameter_name] = float(value)

        return { "success": True, "message": f"Operational parameter '{parameter_name}' logged for vehicle '{vehicle_id}'." }

    def add_maintenance_record(
        self,
        cord_id: str,
        vehicle_id: str,
        service_type: str,
        date: str,
        description: str,
        performed_by: str
    ) -> dict:
        """
        Add a new maintenance record to a vehicle.

        Args:
            cord_id (str): Unique identifier for this maintenance record.
            vehicle_id (str): Vehicle to which this record is attached.
            service_type (str): The type of maintenance performed.
            date (str): Date/time when the service occurred (ISO formatted string).
            description (str): Description/details of the maintenance event.
            performed_by (str): The person/entity that performed the maintenance.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance record added for vehicle X"
            }
            or
            {
                "success": False,
                "error": str (reason for failure)
            }

        Constraints:
            - vehicle_id must exist in the vehicles database.
            - cord_id for maintenance record must be unique.
        """

        if vehicle_id not in self.vehicles:
            return {"success": False, "error": "Vehicle not found"}

        if cord_id in self.maintenance_records:
            return {"success": False, "error": "Record ID already exists"}

        new_record = {
            "cord_id": cord_id,
            "vehicle_id": vehicle_id,
            "service_type": service_type,
            "date": date,
            "description": description,
            "performed_by": performed_by
        }

        self.maintenance_records[cord_id] = new_record

        return {
            "success": True,
            "message": f"Maintenance record added for vehicle {vehicle_id}"
        }

    def update_maintenance_record(
        self,
        cord_id: str,
        service_type: str = None,
        date: str = None,
        description: str = None,
        performed_by: str = None
    ) -> dict:
        """
        Update the details (service_type, date, description, performed_by) of an existing maintenance record.

        Args:
            cord_id (str): Unique identifier for the maintenance record to update.
            service_type (str, optional): New service type.
            date (str, optional): New date (ISO string).
            description (str, optional): New description.
            performed_by (str, optional): New performer (name/ID).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Maintenance record updated successfully"}
                On error:
                    {"success": False, "error": <reason>}

        Constraints:
            - cord_id must reference an existing maintenance record.
            - Only mutable fields (service_type, date, description, performed_by) can be updated.
            - vehicle_id and cord_id cannot be updated.
            - At least one mutable field must be provided for update.
        """
        # Check if the maintenance record exists
        if cord_id not in self.maintenance_records:
            return { "success": False, "error": "Maintenance record not found" }

        mutable_fields = {
            'service_type': service_type,
            'date': date,
            'description': description,
            'performed_by': performed_by
        }
        # Filter for only actually provided (not None) fields
        fields_to_update = {k: v for k, v in mutable_fields.items() if v is not None}

        if not fields_to_update:
            return { "success": False, "error": "No updatable fields provided" }

        record = self.maintenance_records[cord_id]
        for field, value in fields_to_update.items():
            record[field] = value

        # Save the updated record (dicts are mutable, this updates self.maintenance_records in place)
        return { "success": True, "message": "Maintenance record updated successfully" }

    def add_diagnostic_record(
        self,
        vehicle_id: str,
        diagnostic_code: str,
        date: str,
        description: str,
        resolved: bool,
        cord_id: str = None
    ) -> dict:
        """
        Add a new diagnostic record to a vehicle.

        Args:
            vehicle_id (str): Target vehicle's ID (must be registered).
            diagnostic_code (str): Diagnostic code identifier.
            date (str): ISO timestamp of diagnosis.
            description (str): Description of the diagnostic occurrence.
            resolved (bool): Whether the diagnostic issue has been resolved.
            cord_id (str, optional): Unique diagnostic record ID; autogenerated if not provided.

        Returns:
            dict:
                - On success: { "success": True, "message": "Diagnostic record added for vehicle <vehicle_id>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - vehicle_id must exist as a registered vehicle.
            - cord_id must be unique among diagnostic records (if provided).
        """
        # Check valid vehicle
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle does not exist" }

        # Generate unique cord_id if not provided
        if not cord_id:
            base = "diagrec"
            num = 1
            while True:
                generated = f"{base}-{num}"
                if generated not in self.diagnostic_records:
                    cord_id = generated
                    break
                num += 1
        else:
            if cord_id in self.diagnostic_records:
                return { "success": False, "error": "cord_id already exists" }

        # Build diagnostic record
        record = {
            "cord_id": cord_id,
            "vehicle_id": vehicle_id,
            "diagnostic_code": diagnostic_code,
            "date": date,
            "description": description,
            "resolved": resolved
        }

        self.diagnostic_records[cord_id] = record

        return { "success": True, "message": f"Diagnostic record added for vehicle {vehicle_id}" }

    def update_diagnostic_record_resolution(self, cord_id: str, resolved: bool) -> dict:
        """
        Update the 'resolved' status of a diagnostic record.

        Args:
            cord_id (str): The unique identifier for the diagnostic record.
            resolved (bool): The new value for the resolved field (True/False).

        Returns:
            dict: {
                "success": True,
                "message": "Diagnostic record resolution status updated."
            } on success,
            or
            {
                "success": False,
                "error": <description>
            } on failure.

        Constraints:
            - Diagnostic record (cord_id) must exist.
            - 'resolved' parameter must be of type bool.
        """
        if cord_id not in self.diagnostic_records:
            return {"success": False, "error": "Diagnostic record not found."}
        if not isinstance(resolved, bool):
            return {"success": False, "error": "Resolved must be a boolean."}

        self.diagnostic_records[cord_id]["resolved"] = resolved
        return {"success": True, "message": "Diagnostic record resolution status updated."}

    def register_new_vehicle(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: int,
        vin: str,
        specs: dict,
        operational_param: dict
    ) -> dict:
        """
        Add a new vehicle to the system with provided specifications and operational parameters.

        Args:
            vehicle_id (str): Unique ID for the new vehicle.
            make (str): Manufacturer name.
            model (str): Model name.
            year (int): Year of manufacture.
            vin (str): Vehicle Identification Number (should be unique).
            specs (dict): Specifications dictionary (parameter_name: definition).
            operational_param (dict): Initial operational parameters (parameter_name: value).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Vehicle registered successfully"}
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - vehicle_id must be unique.
            - vin should not match any existing vehicle.
            - specs and operational_param must be dict.
        """
        # Check required fields
        if not (vehicle_id and make and model and vin and isinstance(year, int)):
            return {"success": False, "error": "Missing or invalid required vehicle attributes"}

        if not isinstance(specs, dict) or not isinstance(operational_param, dict):
            return {"success": False, "error": "Specs and operational_param must be dictionaries"}

        # Constraint: vehicle_id must be unique
        if vehicle_id in self.vehicles:
            return {"success": False, "error": "Vehicle ID already exists"}

        # (Extra): Check VIN uniqueness
        for v in self.vehicles.values():
            if v.get("vin") == vin:
                return {"success": False, "error": "VIN already exists for another vehicle"}

        # Register the vehicle
        self.vehicles[vehicle_id] = {
            "vehicle_id": vehicle_id,
            "make": make,
            "model": model,
            "year": year,
            "vin": vin,
            "specs": specs,
            "operational_param": operational_param
        }

        # Optionally, initialize operational parameter history storage
        if vehicle_id not in self.operational_parameters:
            self.operational_parameters[vehicle_id] = []

        return {"success": True, "message": "Vehicle registered successfully"}

    def remove_vehicle(self, vehicle_id: str) -> dict:
        """
        Remove a vehicle by vehicle_id and cascade-delete all associated operational,
        maintenance, and diagnostic records.

        Args:
            vehicle_id (str): Unique identifier of the vehicle to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Vehicle and all associated records removed."
            }
            or
            {
                "success": False,
                "error": "Vehicle ID does not exist."
            }

        Constraints:
            - The vehicle_id must exist in the registered vehicles.
            - All associated operational parameters, maintenance, and diagnostic records
              should be deleted as well.
            - After this operation, the vehicle_id should not exist anywhere in the system.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle ID does not exist." }

        # Remove the vehicle itself
        del self.vehicles[vehicle_id]

        # Remove operational parameters history
        if vehicle_id in self.operational_parameters:
            del self.operational_parameters[vehicle_id]

        # Remove all maintenance records associated with this vehicle
        maintenance_to_remove = [cord_id for cord_id, record in self.maintenance_records.items() if record["vehicle_id"] == vehicle_id]
        for cord_id in maintenance_to_remove:
            del self.maintenance_records[cord_id]

        # Remove all diagnostic records associated with this vehicle
        diagnostic_to_remove = [cord_id for cord_id, record in self.diagnostic_records.items() if record["vehicle_id"] == vehicle_id]
        for cord_id in diagnostic_to_remove:
            del self.diagnostic_records[cord_id]

        return { "success": True, "message": "Vehicle and all associated records removed." }

    def update_vehicle_specs(self, vehicle_id: str, new_specs: dict) -> dict:
        """
        Modify the specifications (specs) or valid parameter set for an existing vehicle.

        Args:
            vehicle_id (str): Unique identifier for the target vehicle.
            new_specs (dict): Dictionary of new or updated specifications to set for the vehicle.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Vehicle specs updated for vehicle_id XYZ." }
                On failure:
                    { "success": False, "error": "Vehicle not found." }
                    { "success": False, "error": "Invalid specs format." }

        Constraints:
            - The vehicle_id must exist in the system.
            - new_specs must be a valid dictionary.
        """
        if vehicle_id not in self.vehicles:
            return { "success": False, "error": "Vehicle not found." }
        if not isinstance(new_specs, dict):
            return { "success": False, "error": "Invalid specs format." }

        self.vehicles[vehicle_id]["specs"] = new_specs
        return { "success": True, "message": f"Vehicle specs updated for vehicle_id {vehicle_id}." }


class AutomotiveServiceManagementSystem(BaseEnv):
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

    def get_vehicle_info(self, **kwargs):
        return self._call_inner_tool('get_vehicle_info', kwargs)

    def list_all_vehicles(self, **kwargs):
        return self._call_inner_tool('list_all_vehicles', kwargs)

    def get_vehicle_specs(self, **kwargs):
        return self._call_inner_tool('get_vehicle_specs', kwargs)

    def validate_vehicle_id(self, **kwargs):
        return self._call_inner_tool('validate_vehicle_id', kwargs)

    def validate_operational_parameter(self, **kwargs):
        return self._call_inner_tool('validate_operational_parameter', kwargs)

    def get_operational_param_latest(self, **kwargs):
        return self._call_inner_tool('get_operational_param_latest', kwargs)

    def get_operational_param_history(self, **kwargs):
        return self._call_inner_tool('get_operational_param_history', kwargs)

    def get_latest_operational_params_all(self, **kwargs):
        return self._call_inner_tool('get_latest_operational_params_all', kwargs)

    def get_maintenance_records(self, **kwargs):
        return self._call_inner_tool('get_maintenance_records', kwargs)

    def get_diagnostic_records(self, **kwargs):
        return self._call_inner_tool('get_diagnostic_records', kwargs)

    def get_maintenance_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_maintenance_record_by_id', kwargs)

    def get_diagnostic_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_diagnostic_record_by_id', kwargs)

    def log_operational_parameter(self, **kwargs):
        return self._call_inner_tool('log_operational_parameter', kwargs)

    def add_maintenance_record(self, **kwargs):
        return self._call_inner_tool('add_maintenance_record', kwargs)

    def update_maintenance_record(self, **kwargs):
        return self._call_inner_tool('update_maintenance_record', kwargs)

    def add_diagnostic_record(self, **kwargs):
        return self._call_inner_tool('add_diagnostic_record', kwargs)

    def update_diagnostic_record_resolution(self, **kwargs):
        return self._call_inner_tool('update_diagnostic_record_resolution', kwargs)

    def register_new_vehicle(self, **kwargs):
        return self._call_inner_tool('register_new_vehicle', kwargs)

    def remove_vehicle(self, **kwargs):
        return self._call_inner_tool('remove_vehicle', kwargs)

    def update_vehicle_specs(self, **kwargs):
        return self._call_inner_tool('update_vehicle_specs', kwargs)

