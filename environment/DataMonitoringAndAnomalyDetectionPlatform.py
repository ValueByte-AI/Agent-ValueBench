# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import time
from typing import Optional, Dict, Any
from typing import Dict, Any



class MonitoredStreamInfo(TypedDict):
    am_id: str                # Unique stream ID
    name: str
    source: str
    description: str
    active_sta: bool          # Whether the stream is actively monitored

class AnomalyInfo(TypedDict):
    anomaly_id: str
    stream_id: str            # Foreign key to MonitoredStream
    timestamp: float
    severity: str             # Should be one of: "low", "medium", "high"
    description: str
    sta: str                  # Status, should be one of: "open", "acknowledged", "resolved"

class DetectionConfigurationInfo(TypedDict):
    config_id: str
    stream_id: str            # Foreign key to MonitoredStream
    algorithm: str
    parameters: Dict[str, Any]
    threshold: float
    last_updated: float       # Unix timestamp

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Data Monitoring and Anomaly Detection Platform environment.
        """

        # Monitored Streams entity:
        # {am_id: MonitoredStreamInfo}
        self.monitored_streams: Dict[str, MonitoredStreamInfo] = {}

        # Anomalies entity:
        # {anomaly_id: AnomalyInfo}
        self.anomalies: Dict[str, AnomalyInfo] = {}

        # Detection Configurations entity:
        # {config_id: DetectionConfigurationInfo}
        self.detection_configurations: Dict[str, DetectionConfigurationInfo] = {}

        # Configuration update logs (for: 'Configuration updates must be logged')
        # Each log is a dict (structure to be defined upon implementation)
        self.configuration_logs: List[dict] = []

        # Constraints:
        # - Each Anomaly must be linked to a single MonitoredStream (via stream_id)
        # - Each MonitoredStream may have only one active DetectionConfiguration at a time
        # - Configuration updates must be logged (see self.configuration_logs)
        # - Severity values for anomalies must be in {"low", "medium", "high"}
        # - Status values for anomalies must be in {"open", "acknowledged", "resolved"}
        # - Only active MonitoredStreams (active_sta=True) can generate anomalies

    def list_anomalies(
        self, 
        stream_id: str = None, 
        severity: str = None, 
        status: str = None
    ) -> dict:
        """
        Retrieve the current list of detected anomalies, optionally filterable by stream_id, severity, or status.

        Args:
            stream_id (str, optional): Only include anomalies from this monitored stream.
            severity (str, optional): Only include anomalies of this severity ("low", "medium", "high").
            status (str, optional): Only include anomalies with this status ("open", "acknowledged", "resolved").

        Returns:
            dict: {
                "success": True,
                "data": List[AnomalyInfo]  # List of anomalies satisfying the filters (may be empty)
            }
            or {
                "success": False,
                "error": str  # Reason for error, e.g. invalid severity/status filter
            }

        Constraints:
            - severity, if provided, must be one of {"low", "medium", "high"}
            - status, if provided, must be one of {"open", "acknowledged", "resolved"}
        """
        allowed_severities = {"low", "medium", "high"}
        allowed_statuses = {"open", "acknowledged", "resolved"}

        if severity is not None and severity not in allowed_severities:
            return { "success": False, "error": f"Invalid severity filter: {severity}" }
        if status is not None and status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status filter: {status}" }

        result = []
        for anomaly in self.anomalies.values():
            if stream_id is not None and anomaly["stream_id"] != stream_id:
                continue
            if severity is not None and anomaly["severity"] != severity:
                continue
            if status is not None and anomaly["sta"] != status:
                continue
            result.append(anomaly)

        return { "success": True, "data": result }

    def get_anomaly_by_id(self, anomaly_id: str) -> dict:
        """
        Retrieve detailed information for a specific anomaly using its anomaly_id.

        Args:
            anomaly_id (str): Unique identifier of the anomaly to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": AnomalyInfo,  # If found
            }
            or
            {
                "success": False,
                "error": str,         # If not found
            }
        Constraints:
            - The anomaly_id must exist in the anomalies entity.
        """
        anomaly = self.anomalies.get(anomaly_id)
        if anomaly is None:
            return {
                "success": False,
                "error": f"Anomaly with id '{anomaly_id}' does not exist."
            }
        return {
            "success": True,
            "data": anomaly
        }

    def list_monitored_streams(self) -> dict:
        """
        Retrieve all monitored streams/metrics in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[MonitoredStreamInfo]  # List of all streams (can be empty)
            }

        Constraints:
            - No constraints; returns all monitored streams present in the system.
        """
        streams = list(self.monitored_streams.values())
        return { "success": True, "data": streams }

    def get_stream_by_id(self, am_id: str) -> dict:
        """
        Retrieve detailed information about a monitored stream based on its am_id.

        Args:
            am_id (str): The unique identifier of the monitored stream.

        Returns:
            dict:
                - If stream exists: {"success": True, "data": MonitoredStreamInfo}
                - If not found:     {"success": False, "error": "Stream with given am_id not found"}

        Constraints:
            - No permission or status requirement; this is a direct lookup by primary key.
        """
        stream = self.monitored_streams.get(am_id)
        if stream is not None:
            return {"success": True, "data": stream}
        else:
            return {"success": False, "error": "Stream with given am_id not found"}

    def list_stream_anomalies(self, stream_id: str) -> dict:
        """
        Retrieve all anomalies associated with the specified monitored stream.

        Args:
            stream_id (str): The unique ID of the monitored stream.

        Returns:
            dict:
                - {"success": True, "data": List[AnomalyInfo]}
                  Data is a possibly-empty list of anomalies for the stream.
                - {"success": False, "error": str}
                  If stream_id does not correspond to an existing MonitoredStream.

        Constraints:
            - stream_id must exist in the monitored_streams entity.
            - Returned anomalies have .stream_id matching the requested stream_id.
        """
        if stream_id not in self.monitored_streams:
            return { "success": False, "error": "Stream not found" }

        anomalies = [
            anomaly for anomaly in self.anomalies.values()
            if anomaly["stream_id"] == stream_id
        ]

        return { "success": True, "data": anomalies }

    def list_detection_configurations(self) -> dict:
        """
        Retrieve all detection configurations currently present in the system.

        Args:
            None

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[DetectionConfigurationInfo],  # List of all detection configurations (may be empty)
                }
                or, in case of storage errors:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }
        Constraints:
            - No special constraints; purely a read/query operation.
        """
        if not hasattr(self, 'detection_configurations'):
            return {"success": False, "error": "Configuration storage missing."}
    
        configs = list(self.detection_configurations.values())
        return {"success": True, "data": configs}

    def get_detection_configuration_by_stream(self, stream_id: str) -> dict:
        """
        Retrieve the currently active detection configuration for the given stream.

        Args:
            stream_id (str): The ID of the monitored data stream.

        Returns:
            dict: {
                "success": True,
                "data": DetectionConfigurationInfo,     # config for this stream_id
            }
            or
            {
                "success": False,
                "error": str    # Error message describing the problem
            }

        Constraints:
            - The MonitoredStream must exist.
            - Only one detection configuration is active per stream; if multiple, select the most recently updated.
        """
        # Check if the stream exists
        if stream_id not in self.monitored_streams:
            return { "success": False, "error": "Monitored stream does not exist" }

        # Collect all detection configurations for this stream
        configs = [
            config for config in self.detection_configurations.values()
            if config["stream_id"] == stream_id
        ]

        if not configs:
            return { "success": False, "error": "No detection configuration found for this stream" }

        # Select the config with the latest last_updated timestamp as "active"
        active_config = max(configs, key=lambda c: c["last_updated"])

        return { "success": True, "data": active_config }

    def get_configuration_update_logs(self) -> dict:
        """
        Retrieve the history/logs of all configuration updates for audit/review purposes.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],     # List of configuration update log entries (may be empty)
            }
        Constraints:
            - No parameters required. Returns all logged configuration update entries.
            - This operation simply returns all configuration logs regardless of their structure/content.
        """
        return {
            "success": True,
            "data": list(self.configuration_logs)  # Defensive copy; result may be empty
        }


    def update_detection_configuration(
        self,
        stream_id: str,
        algorithm: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None
    ) -> dict:
        """
        Update the detection configuration (algorithm, parameters, or threshold)
        for a specific monitored stream. The update is logged.

        Args:
            stream_id (str): ID of the monitored stream.
            algorithm (Optional[str]): New algorithm name (if updating).
            parameters (Optional[dict]): New parameters dictionary (if updating).
            threshold (Optional[float]): New threshold value (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Detection configuration updated and logged."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - The stream_id must correspond to an existing MonitoredStream.
            - The stream must have an active detection configuration.
            - Only specified fields may be updated.
            - Each update must be logged with before and after values and timestamp.
        """
        # Validate stream exists
        if stream_id not in self.monitored_streams:
            return {"success": False, "error": "Monitored stream does not exist"}

        # Find the currently active configuration for this stream, defined as
        # the most recently updated configuration.
        matching_configs = [
            (cid, info)
            for cid, info in self.detection_configurations.items()
            if info["stream_id"] == stream_id
        ]
        if not matching_configs:
            return {"success": False, "error": "Detection configuration for stream not found"}
        config_id, config = max(
            matching_configs,
            key=lambda item: item[1]["last_updated"]
        )

        # Only update fields requested
        updated_fields = {}
        before = {}
        after = {}

        if algorithm is not None:
            before["algorithm"] = config["algorithm"]
            config["algorithm"] = algorithm
            after["algorithm"] = algorithm
            updated_fields["algorithm"] = True

        if parameters is not None:
            before["parameters"] = config["parameters"]
            config["parameters"] = parameters
            after["parameters"] = parameters
            updated_fields["parameters"] = True

        if threshold is not None:
            before["threshold"] = config["threshold"]
            config["threshold"] = threshold
            after["threshold"] = threshold
            updated_fields["threshold"] = True

        if not updated_fields:
            return {"success": False, "error": "No update fields provided"}

        now = time.time()
        before["last_updated"] = config["last_updated"]
        config["last_updated"] = now
        after["last_updated"] = now

        # Log the update
        self.configuration_logs.append({
            "timestamp": now,
            "config_id": config_id,
            "stream_id": stream_id,
            "updated_fields": list(updated_fields.keys()),
            "before": before,
            "after": after
        })

        return {"success": True, "message": "Detection configuration updated and logged."}


    def add_detection_configuration(
        self,
        config_id: str,
        stream_id: str,
        algorithm: str,
        parameters: Dict[str, Any],
        threshold: float
    ) -> dict:
        """
        Add a new detection configuration for a given stream.
        The new config is set as active (the latest for that stream).
        Any prior config is kept but superseded by this one as the "active" config.
        The operation is logged.

        Args:
            config_id (str): Unique ID for the detection configuration.
            stream_id (str): ID of the monitored stream this config will be attached to.
            algorithm (str): Algorithm name to use for detection.
            parameters (dict): Algorithm parameters (as dict).
            threshold (float): Detection threshold.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Detection configuration <config_id> added and activated for stream <stream_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - config_id must be unique.
            - stream_id must exist.
            - Only one active config per stream (superseded by add).
            - Operation must be logged.
        """
        # Check config_id uniqueness
        if config_id in self.detection_configurations:
            return {"success": False, "error": "Configuration ID already exists."}

        # Check stream_id existence
        if stream_id not in self.monitored_streams:
            return {"success": False, "error": "Monitored stream does not exist."}

        # Set up configuration data
        now = time.time()
        config_info = {
            "config_id": config_id,
            "stream_id": stream_id,
            "algorithm": algorithm,
            "parameters": parameters,
            "threshold": threshold,
            "last_updated": now
        }

        # Add to configurations
        self.detection_configurations[config_id] = config_info

        # Log the configuration update
        log_entry = {
            "type": "add",
            "timestamp": now,
            "stream_id": stream_id,
            "config_id": config_id,
            "algorithm": algorithm,
            "parameters": parameters,
            "threshold": threshold,
            "action": "add_detection_configuration"
        }
        self.configuration_logs.append(log_entry)

        return {
            "success": True,
            "message": f"Detection configuration {config_id} added and activated for stream {stream_id}."
        }

    def acknowledge_anomaly(self, anomaly_id: str) -> dict:
        """
        Change the status of a specific anomaly from 'open' to 'acknowledged'.

        Args:
            anomaly_id (str): The unique identifier for the anomaly to acknowledge.

        Returns:
            dict: {
                "success": True,
                "message": "Anomaly <anomaly_id> acknowledged."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only anomalies in 'open' status may be acknowledged.
            - Anomaly must exist.
            - Status must remain within {'open', 'acknowledged', 'resolved'}.
        """
        anomaly = self.anomalies.get(anomaly_id)
        if anomaly is None:
            return {"success": False, "error": "Anomaly not found"}

        if anomaly['sta'] != "open":
            return {"success": False, "error": "Anomaly status is not 'open', cannot acknowledge"}

        anomaly['sta'] = "acknowledged"
        return {"success": True, "message": f"Anomaly {anomaly_id} acknowledged."}

    def resolve_anomaly(self, anomaly_id: str) -> dict:
        """
        Change the status (`sta`) of a specific anomaly to "resolved", allowed only if the current status
        is "open" or "acknowledged".

        Args:
            anomaly_id (str): The unique identifier of the anomaly to resolve.

        Returns:
            dict:
                - On success: {"success": True, "message": "Anomaly <id> marked as resolved"}
                - On error: {"success": False, "error": "<reason>"}

        Constraints:
            - The anomaly must exist.
            - Only allowed if current status (`sta`) is "open" or "acknowledged".
            - Target status value is "resolved".
        """

        anomaly = self.anomalies.get(anomaly_id)
        if anomaly is None:
            return {"success": False, "error": "Anomaly not found"}

        if anomaly["sta"] not in {"open", "acknowledged", "resolved"}:
            return {"success": False, "error": "Anomaly status is invalid in system"}

        if anomaly["sta"] == "resolved":
            return {"success": False, "error": "Anomaly is already resolved"}

        # Only proceed if status is "open" or "acknowledged"
        anomaly["sta"] = "resolved"
        # Note: If there's a timestamp for status change, could update here (not in entity)
        return {"success": True, "message": f"Anomaly {anomaly_id} marked as resolved"}

    def activate_monitored_stream(self, am_id: str) -> dict:
        """
        Activates monitoring for a given MonitoredStream by setting its active_sta attribute to True.

        Args:
            am_id (str): Unique stream ID to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Stream <am_id> activated."
            }
            or
            {
                "success": False,
                "error": "Monitored stream not found"
            }

        Constraints:
            - The stream must exist (am_id in self.monitored_streams).
            - Making already active streams active again is allowed and succeeds (idempotent).
        """
        stream = self.monitored_streams.get(am_id)
        if stream is None:
            return { "success": False, "error": "Monitored stream not found" }

        stream["active_sta"] = True
        return { "success": True, "message": f"Stream {am_id} activated." }

    def deactivate_monitored_stream(self, am_id: str) -> dict:
        """
        Deactivate monitoring for the specified stream by setting its 'active_sta' to False.

        Args:
            am_id (str): The unique identifier of the monitored stream to deactivate.

        Returns:
            dict:
                - On success: { "success": True, "message": "Monitored stream deactivated" }
                - On error:   { "success": False, "error": <reason> }

        Constraints:
            - The given am_id must exist in monitored_streams.
            - If the stream is already deactivated (active_sta==False), return error message.
        """
        stream = self.monitored_streams.get(am_id)
        if stream is None:
            return { "success": False, "error": "Monitored stream does not exist" }
        if not stream["active_sta"]:
            return { "success": False, "error": "Monitored stream is already deactivated" }
        stream["active_sta"] = False
        return { "success": True, "message": "Monitored stream deactivated" }

    def log_configuration_update(
        self,
        config_id: str,
        stream_id: str,
        event_type: str,
        old_value: dict,
        new_value: dict,
        timestamp: float,
        message: str = ""
    ) -> dict:
        """
        Record/log a configuration update event into the configuration change log.

        Args:
            config_id (str): ID of the configuration being updated.
            stream_id (str): ID of the associated monitored stream.
            event_type (str): Type of event (e.g., 'create', 'update', 'delete').
            old_value (dict): Previous config info (can be {} or None).
            new_value (dict): New config info after change (can be {} or None).
            timestamp (float): Unix timestamp of when this event happened.
            message (str, optional): Additional info (default: "")

        Returns:
            dict: 
              - On success: {"success": True, "message": "Configuration update logged successfully."}
              - On failure: {"success": False, "error": <str>} (e.g. missing required fields)

        Constraints:
            - Logs must provide clear traceable audit information.
            - No exception raising, always return dict.
        """
        if not config_id or not stream_id or not event_type or (timestamp is None):
            return {
                "success": False,
                "error": "Missing required log fields (config_id, stream_id, event_type, timestamp)."
            }

        log_entry = {
            "config_id": config_id,
            "stream_id": stream_id,
            "event_type": event_type,
            "old_value": old_value if old_value is not None else {},
            "new_value": new_value if new_value is not None else {},
            "timestamp": timestamp,
            "message": message
        }
        self.configuration_logs.append(log_entry)
        return {
            "success": True,
            "message": "Configuration update logged successfully."
        }


class DataMonitoringAndAnomalyDetectionPlatform(BaseEnv):
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

    def list_anomalies(self, **kwargs):
        return self._call_inner_tool('list_anomalies', kwargs)

    def get_anomaly_by_id(self, **kwargs):
        return self._call_inner_tool('get_anomaly_by_id', kwargs)

    def list_monitored_streams(self, **kwargs):
        return self._call_inner_tool('list_monitored_streams', kwargs)

    def get_stream_by_id(self, **kwargs):
        return self._call_inner_tool('get_stream_by_id', kwargs)

    def list_stream_anomalies(self, **kwargs):
        return self._call_inner_tool('list_stream_anomalies', kwargs)

    def list_detection_configurations(self, **kwargs):
        return self._call_inner_tool('list_detection_configurations', kwargs)

    def get_detection_configuration_by_stream(self, **kwargs):
        return self._call_inner_tool('get_detection_configuration_by_stream', kwargs)

    def get_configuration_update_logs(self, **kwargs):
        return self._call_inner_tool('get_configuration_update_logs', kwargs)

    def update_detection_configuration(self, **kwargs):
        return self._call_inner_tool('update_detection_configuration', kwargs)

    def add_detection_configuration(self, **kwargs):
        return self._call_inner_tool('add_detection_configuration', kwargs)

    def acknowledge_anomaly(self, **kwargs):
        return self._call_inner_tool('acknowledge_anomaly', kwargs)

    def resolve_anomaly(self, **kwargs):
        return self._call_inner_tool('resolve_anomaly', kwargs)

    def activate_monitored_stream(self, **kwargs):
        return self._call_inner_tool('activate_monitored_stream', kwargs)

    def deactivate_monitored_stream(self, **kwargs):
        return self._call_inner_tool('deactivate_monitored_stream', kwargs)

    def log_configuration_update(self, **kwargs):
        return self._call_inner_tool('log_configuration_update', kwargs)
