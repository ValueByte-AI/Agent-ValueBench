# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class DeviceInfo(TypedDict):
    device_id: str
    location: str
    status: str
    installation_date: str  # was 'installation_da' in state space

class SensorInfo(TypedDict):
    sensor_id: str
    sensor_type: str
    device_id: str
    status: str
    calibration_info: str  # Could be dict if calibration details are complex

class MeasurementInfo(TypedDict):
    measurement_id: str
    device_id: str
    sensor_id: str
    timestamp: float  # or str, but float typically for time-series
    value: float
    unit: str  # was 'un' in state space

class _GeneratedEnvImpl:
    def __init__(self):
        """
        IoT sensor data management system environment state.
        """

        # Devices: {device_id: DeviceInfo}
        # Entity: Device (device_id, location, status, installation_date)
        self.devices: Dict[str, DeviceInfo] = {}

        # Sensors: {sensor_id: SensorInfo}
        # Entity: Sensor (sensor_id, sensor_type, device_id, status, calibration_info)
        self.sensors: Dict[str, SensorInfo] = {}

        # Measurements: {measurement_id: MeasurementInfo}
        # Entity: Measurement (measurement_id, device_id, sensor_id, timestamp, value, unit)
        self.measurements: Dict[str, MeasurementInfo] = {}

        # Constraints:
        # - Each sensor is uniquely associated with a device.
        # - Measurements must be linked to valid sensor and device IDs.
        # - Timestamps of measurements should be in chronological order per sensor (no duplicate timestamps for the same sensor).
        # - Device and sensor statuses reflect operational (active/inactive/faulty) conditions and affect data collection.


    def get_device_by_id(self, device_id: str) -> dict:
        """
        Retrieve metadata and status for a device given its device_id.

        Args:
            device_id (str): The identifier of the device to lookup.

        Returns:
            dict: {
                "success": True,
                "data": DeviceInfo  # The device's metadata and status info
            }
            or
            {
                "success": False,
                "error": "Device not found"
            }

        Constraints:
            - The provided device_id must exist within the system's device dictionary.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device not found" }
        return { "success": True, "data": self.devices[device_id] }

    def list_all_devices(self) -> dict:
        """
        Retrieve all devices and their properties from the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo]  # List of all device info (possibly empty if no devices)
            }
        """
        return {
            "success": True,
            "data": list(self.devices.values())
        }

    def get_sensors_by_device(self, device_id: str) -> dict:
        """
        List all sensors physically associated with a given device_id.

        Args:
            device_id (str): The ID of the device.

        Returns:
            dict: {
                "success": True,
                "data": List[SensorInfo]  # List may be empty if no sensors are associated.
            }
            or
            {
                "success": False,
                "error": "Device does not exist"
            }

        Constraints:
            - device_id must exist in the system.
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device does not exist" }

        sensors = [
            sensor_info for sensor_info in self.sensors.values()
            if sensor_info["device_id"] == device_id
        ]

        return { "success": True, "data": sensors }

    def get_sensors_by_type(self, sensor_type: str) -> dict:
        """
        Retrieve all sensors filtered by the given sensor_type.

        Args:
            sensor_type (str): The type of sensors to retrieve (e.g., 'temperature', 'humidity').

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[SensorInfo]  # List of matching sensors (may be empty if no matches)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error (e.g., invalid sensor_type)
                }

        Constraints:
            - sensor_type must not be empty.
        """
        if not sensor_type or not isinstance(sensor_type, str):
            return {"success": False, "error": "sensor_type must be a non-empty string"}

        results = [
            sensor_info
            for sensor_info in self.sensors.values()
            if sensor_info.get("sensor_type") == sensor_type
        ]
        return {"success": True, "data": results}

    def get_device_status(self, device_id: str) -> dict:
        """
        Retrieve the operational status (active/inactive/faulty) of the specified device.

        Args:
            device_id (str): Unique identifier of the device.

        Returns:
            dict: {
                "success": True,
                "data": { "device_id": str, "status": str }
            }
            or
            {
                "success": False,
                "error": "Device not found"
            }

        Constraints:
            - The device with the given device_id must exist.
        """
        device = self.devices.get(device_id)
        if not device:
            return { "success": False, "error": "Device not found" }
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "status": device.get("status", "Unknown")
            }
        }

    def get_sensor_by_id(self, sensor_id: str) -> dict:
        """
        Retrieve sensor details by sensor_id.

        Args:
            sensor_id (str): The ID of the sensor to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": SensorInfo }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - sensor_id must exist in the system's sensors.
            - No exceptions are raised; errors are reported via the return dict.
        """
        if sensor_id not in self.sensors:
            return { "success": False, "error": "Sensor ID does not exist." }

        return { "success": True, "data": self.sensors[sensor_id] }

    def get_sensor_status(self, sensor_id: str) -> dict:
        """
        Retrieve the operational status of a specific sensor by its sensor_id.

        Args:
            sensor_id (str): The unique identifier of the sensor.

        Returns:
            dict: 
                - If found: {"success": True, "data": <status str>}
                - If not found: {"success": False, "error": "Sensor not found"}
        """
        sensor_info = self.sensors.get(sensor_id)
        if not sensor_info:
            return { "success": False, "error": "Sensor not found" }

        return { "success": True, "data": sensor_info["status"] }

    def get_measurements_by_device_and_type_and_time_range(
        self,
        device_id: str,
        sensor_type: str,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Fetch all measurement records for a given device, filtered by sensor type and a timestamp interval.

        Args:
            device_id (str): ID of the target device.
            sensor_type (str): Type of sensor to consider (e.g., 'temperature').
            start_time (float): Start of the timestamp interval (inclusive).
            end_time (float): End of the timestamp interval (inclusive).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[MeasurementInfo]
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Device with device_id must exist.
            - Only measurements from sensors of the specified type and device are considered.
            - Measurements' timestamps are filtered between start_time and end_time (inclusive).
        """
        if device_id not in self.devices:
            return { "success": False, "error": "Device does not exist." }

        # Get all sensor_ids for this device and sensor_type
        valid_sensor_ids = [
            sensor_id for sensor_id, info in self.sensors.items()
            if info["device_id"] == device_id and info["sensor_type"] == sensor_type
        ]

        if not valid_sensor_ids:
            # No sensors of that type for the device – still success, empty data
            return { "success": True, "data": [] }

        # Find all measurements with:
        # - correct device_id
        # - sensor_id in valid_sensor_ids
        # - start_time <= timestamp <= end_time
        results = [
            m for m in self.measurements.values()
            if m["device_id"] == device_id
            and m["sensor_id"] in valid_sensor_ids
            and start_time <= m["timestamp"] <= end_time
        ]

        return { "success": True, "data": results }

    def get_measurements_by_sensor_and_time_range(self, sensor_id: str, start_time: float, end_time: float) -> dict:
        """
        Fetch all measurements for a specified sensor_id, filtered by a timestamp range.

        Args:
            sensor_id (str): The ID of the sensor to fetch measurements for.
            start_time (float): Start of timestamp range (inclusive).
            end_time (float): End of timestamp range (inclusive).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[MeasurementInfo]  # may be empty
                }
                or 
                {
                    "success": False,
                    "error": str  # Explanation, e.g. "Sensor not found"
                }
        Constraints:
            - sensor_id must exist in the system.
            - Returns all measurement records where:
                - measurement["sensor_id"] == sensor_id
                - start_time <= measurement["timestamp"] <= end_time
        """
        if sensor_id not in self.sensors:
            return { "success": False, "error": "Sensor not found" }

        # It's possible that start_time > end_time, but we just return an empty list as result.
        filtered_measurements = [
            m for m in self.measurements.values()
            if m["sensor_id"] == sensor_id
            and start_time <= m["timestamp"] <= end_time
        ]

        return { "success": True, "data": filtered_measurements }

    def get_latest_measurement_for_sensor(self, sensor_id: str) -> dict:
        """
        Retrieve the most recent (i.e., with the latest timestamp) measurement for a given sensor_id.

        Args:
            sensor_id (str): The ID of the sensor whose latest measurement is queried.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": MeasurementInfo or None  # None if no measurements for this sensor
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., sensor does not exist
                    }
        Constraints:
            - The sensor must exist in the system.
        """
        # Check if sensor exists
        if sensor_id not in self.sensors:
            return { "success": False, "error": "Sensor does not exist" }

        # Filter measurements for this sensor
        measurements = [
            m for m in self.measurements.values()
            if m["sensor_id"] == sensor_id
        ]
        if not measurements:
            return { "success": True, "data": None }

        # Find measurement with latest timestamp
        latest_measurement = max(measurements, key=lambda m: m["timestamp"])
        return { "success": True, "data": latest_measurement }

    def get_measurement_history_for_sensor(self, sensor_id: str) -> dict:
        """
        Retrieve the chronological sequence of all measurements for the given sensor_id.

        Args:
            sensor_id (str): The ID of the sensor to query measurement history for.

        Returns:
            dict: {
                "success": True,
                "data": List[MeasurementInfo],  # Ordered chronologically by timestamp (ascending)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. sensor not found
            }

        Constraints:
            - Sensor must exist in the system.
            - Returned list is sorted by timestamp ascending.
        """
        if sensor_id not in self.sensors:
            return { "success": False, "error": "Sensor not found" }

        measurements = [
            m for m in self.measurements.values()
            if m["sensor_id"] == sensor_id
        ]
        measurements.sort(key=lambda x: x["timestamp"])
        return { "success": True, "data": measurements }

    def add_device(
        self, 
        device_id: str, 
        location: str, 
        status: str, 
        installation_date: str
    ) -> dict:
        """
        Add a new IoT device to the system.
    
        Args:
            device_id (str): Unique identifier for the device.
            location (str): Device location.
            status (str): Device operational status, must be "active", "inactive", or "faulty".
            installation_date (str): Date of device installation (format not enforced).
    
        Returns:
            dict: 
                Success: { "success": True, "message": "Device added: <device_id>" }
                Failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Device ID must be unique in the system.
            - Status must be one of: "active", "inactive", "faulty".
            - All fields are required (non-empty).
        """
        ALLOWED_STATUSES = {"active", "inactive", "faulty"}
    
        if not all([device_id, location, status, installation_date]):
            return { "success": False, "error": "Missing required parameter(s)" }
    
        if device_id in self.devices:
            return { "success": False, "error": "Device ID already exists" }
    
        if status not in ALLOWED_STATUSES:
            return { "success": False, "error": "Invalid status" }
    
        device_info: DeviceInfo = {
            "device_id": device_id,
            "location": location,
            "status": status,
            "installation_date": installation_date
        }
    
        self.devices[device_id] = device_info
    
        return { "success": True, "message": f"Device added: {device_id}" }

    def update_device_status(self, device_id: str, new_status: str) -> dict:
        """
        Change the status (active/inactive/faulty) of an existing device.

        Args:
            device_id (str): The unique ID of the device to update.
            new_status (str): The new status value ("active", "inactive", or "faulty").

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Device <device_id> status updated to <new_status>." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - device_id must exist in the system.
            - new_status must be one of {"active", "inactive", "faulty"}.
        """
        allowed_statuses = {"active", "inactive", "faulty"}
        if device_id not in self.devices:
            return { "success": False, "error": f"Device '{device_id}' does not exist." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed: {allowed_statuses}." }

        self.devices[device_id]["status"] = new_status
        return { "success": True, "message": f"Device '{device_id}' status updated to '{new_status}'." }

    def add_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        device_id: str,
        status: str,
        calibration_info: str
    ) -> dict:
        """
        Register a new sensor and associate it with an existing device.

        Args:
            sensor_id (str): Unique sensor identifier.
            sensor_type (str): Type of the sensor (e.g., temperature).
            device_id (str): Existing device's ID to associate with the sensor.
            status (str): Initial status of the sensor (e.g., active/inactive).
            calibration_info (str): Calibration information for the sensor.

        Returns:
            dict: {
                "success": True,
                "message": "Sensor <sensor_id> registered and associated with device <device_id>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - sensor_id must be unique (not already registered).
            - device_id must point to an existing device.
            - New sensor's device association is immutable after creation (implicit).
        """
        if sensor_id in self.sensors:
            return {"success": False, "error": f"Sensor ID '{sensor_id}' already exists."}

        if device_id not in self.devices:
            return {"success": False, "error": f"Device ID '{device_id}' does not exist."}

        sensor_info = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "device_id": device_id,
            "status": status,
            "calibration_info": calibration_info
        }
        self.sensors[sensor_id] = sensor_info

        return {
            "success": True,
            "message": f"Sensor '{sensor_id}' registered and associated with device '{device_id}'."
        }

    def update_sensor_status(self, sensor_id: str, new_status: str) -> dict:
        """
        Change the operational status of a sensor.

        Args:
            sensor_id (str): The unique identifier of the sensor to update.
            new_status (str): The new operational status. Must be one of "active", "inactive", "faulty".

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "message": "Sensor status updated to <new_status> for sensor <sensor_id>"
                }
                On failure:
                {
                    "success": False,
                    "error": "reason for failure"
                }

        Constraints:
            - sensor_id must exist in the system.
            - new_status must be one of the allowed states ("active", "inactive", "faulty").
        """
        allowed_statuses = {"active", "inactive", "faulty"}
        if sensor_id not in self.sensors:
            return {"success": False, "error": f"Sensor with id {sensor_id} does not exist"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Must be one of {allowed_statuses}"}
    
        # Update status
        self.sensors[sensor_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Sensor status updated to {new_status} for sensor {sensor_id}"
        }

    def calibrate_sensor(self, sensor_id: str, calibration_info: str) -> dict:
        """
        Update the calibration information for a specified sensor.

        Args:
            sensor_id (str): Unique identifier of the sensor to calibrate.
            calibration_info (str): New calibration information as a string.

        Returns:
            dict:
              - On success:
                    {
                        "success": True,
                        "message": "Calibration info updated for sensor <sensor_id>"
                    }
              - On failure (sensor not found):
                    {
                        "success": False,
                        "error": "Sensor not found"
                    }

        Constraints:
            - Sensor must exist in the system.
            - No restriction on sensor status for calibration.
        """
        if sensor_id not in self.sensors:
            return { "success": False, "error": "Sensor not found" }

        self.sensors[sensor_id]['calibration_info'] = calibration_info

        return {
            "success": True,
            "message": f"Calibration info updated for sensor {sensor_id}"
        }

    def add_measurement(
        self,
        measurement_id: str,
        device_id: str,
        sensor_id: str,
        timestamp: float,
        value: float,
        unit: str
    ) -> dict:
        """
        Add a new measurement for a specific sensor and device.

        Args:
            measurement_id (str): Unique identifier for the measurement.
            device_id (str): ID of the device collecting the measurement.
            sensor_id (str): ID of the sensor generating the measurement.
            timestamp (float): Timestamp for the measurement (unix time).
            value (float): Value of the measurement.
            unit (str): Measurement unit.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Measurement <id> added."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - Device and sensor IDs must exist.
            - The sensor must be associated with the device.
            - measurement_id must be unique.
            - Timestamps for the same sensor must be unique (no duplicate <sensor_id, timestamp> pairs).
            - Device and sensor statuses must be "active".
        """
        # Check if measurement_id already exists
        if measurement_id in self.measurements:
            return {"success": False, "error": f"Measurement ID {measurement_id} already exists."}

        # Check if device exists
        if device_id not in self.devices:
            return {"success": False, "error": f"Device ID {device_id} does not exist."}

        # Check if sensor exists
        if sensor_id not in self.sensors:
            return {"success": False, "error": f"Sensor ID {sensor_id} does not exist."}

        sensor_info = self.sensors[sensor_id]
        # Check if this sensor belongs to the given device
        if sensor_info["device_id"] != device_id:
            return {"success": False, "error": f"Sensor ID {sensor_id} is not associated with device ID {device_id}."}

        # Check device and sensor are 'active'
        device_status = self.devices[device_id]["status"]
        sensor_status = sensor_info["status"]
        if device_status != "active":
            return {"success": False, "error": f"Device ID {device_id} is not active. Status: {device_status}"}
        if sensor_status != "active":
            return {"success": False, "error": f"Sensor ID {sensor_id} is not active. Status: {sensor_status}"}

        # Check for duplicate timestamp for the sensor
        for m in self.measurements.values():
            if m["sensor_id"] == sensor_id and m["timestamp"] == timestamp:
                return {"success": False, "error": f"Measurement for sensor ID {sensor_id} already exists at timestamp {timestamp}."}

        # Create and add the measurement
        measurement = {
            "measurement_id": measurement_id,
            "device_id": device_id,
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "value": value,
            "unit": unit
        }
        self.measurements[measurement_id] = measurement
        return {"success": True, "message": f"Measurement {measurement_id} added."}

    def delete_measurement(self, measurement_id: str) -> dict:
        """
        Remove a measurement from the system by its measurement_id, if allowed by data retention policy.

        Args:
            measurement_id (str): The unique identifier of the measurement to delete.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Measurement <measurement_id> deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Measurement not found."
                    }

        Constraints:
            - Measurement must exist in the system.
            - (If implemented) Data retention policy must allow deletion.
        """
        # Check existence
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement not found." }
        # (Optional: Add policy check here if system is extended in future)
        del self.measurements[measurement_id]
        return { "success": True, "message": f"Measurement {measurement_id} deleted." }


class IoTSensorDataManagementSystem(BaseEnv):
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

    def get_device_by_id(self, **kwargs):
        return self._call_inner_tool('get_device_by_id', kwargs)

    def list_all_devices(self, **kwargs):
        return self._call_inner_tool('list_all_devices', kwargs)

    def get_sensors_by_device(self, **kwargs):
        return self._call_inner_tool('get_sensors_by_device', kwargs)

    def get_sensors_by_type(self, **kwargs):
        return self._call_inner_tool('get_sensors_by_type', kwargs)

    def get_device_status(self, **kwargs):
        return self._call_inner_tool('get_device_status', kwargs)

    def get_sensor_by_id(self, **kwargs):
        return self._call_inner_tool('get_sensor_by_id', kwargs)

    def get_sensor_status(self, **kwargs):
        return self._call_inner_tool('get_sensor_status', kwargs)

    def get_measurements_by_device_and_type_and_time_range(self, **kwargs):
        return self._call_inner_tool('get_measurements_by_device_and_type_and_time_range', kwargs)

    def get_measurements_by_sensor_and_time_range(self, **kwargs):
        return self._call_inner_tool('get_measurements_by_sensor_and_time_range', kwargs)

    def get_latest_measurement_for_sensor(self, **kwargs):
        return self._call_inner_tool('get_latest_measurement_for_sensor', kwargs)

    def get_measurement_history_for_sensor(self, **kwargs):
        return self._call_inner_tool('get_measurement_history_for_sensor', kwargs)

    def add_device(self, **kwargs):
        return self._call_inner_tool('add_device', kwargs)

    def update_device_status(self, **kwargs):
        return self._call_inner_tool('update_device_status', kwargs)

    def add_sensor(self, **kwargs):
        return self._call_inner_tool('add_sensor', kwargs)

    def update_sensor_status(self, **kwargs):
        return self._call_inner_tool('update_sensor_status', kwargs)

    def calibrate_sensor(self, **kwargs):
        return self._call_inner_tool('calibrate_sensor', kwargs)

    def add_measurement(self, **kwargs):
        return self._call_inner_tool('add_measurement', kwargs)

    def delete_measurement(self, **kwargs):
        return self._call_inner_tool('delete_measurement', kwargs)

