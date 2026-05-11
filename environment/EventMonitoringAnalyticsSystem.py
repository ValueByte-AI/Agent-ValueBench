# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class EventInfo(TypedDict):
    event_id: str
    name: str
    description: str
    created_at: str
    metrics: List[str]  # List of metric names associated with the event

class MetricInfo(TypedDict):
    metric_name: str
    event_id: str
    unit: str
    description: str

class DataPointInfo(TypedDict):
    datapoint_id: str
    event_id: str
    timestamp: float
    metric_name: str
    value: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Event Monitoring and Analytics System stateful environment.
        """

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Metrics: {metric_id: MetricInfo}, where metric_id = f"{event_id}:{metric_name}"
        self.metrics: Dict[str, MetricInfo] = {}

        # DataPoints: {datapoint_id: DataPointInfo}
        self.datapoints: Dict[str, DataPointInfo] = {}
        self.deleted_event_graph_snapshots: Dict[str, Dict[str, object]] = {}

        # --- Constraints ---
        # - Each DataPoint must be associated with a valid event_id corresponding to an Event.
        # - Each DataPoint’s metric_name must correspond to a Metric associated with its event.
        # - Queries for graph points retrieve DataPoints filtered by event_id and, optionally, by timestamp or metric.
        # - Timestamps for DataPoints must be valid (monotonically increasing for a given metric/event combination, if required for time series).
        # - Events and metrics must be created before DataPoints can be recorded for them.

    def _get_deletion_snapshot_allowlist(self) -> set[str]:
        raw = getattr(self, "deletion_preserves_graph_snapshot_for_events", [])
        if isinstance(raw, list):
            return {event_id for event_id in raw if isinstance(event_id, str)}
        return set()

    def _ensure_deleted_graph_snapshots(self) -> Dict[str, Dict[str, object]]:
        snapshots = getattr(self, "deleted_event_graph_snapshots", None)
        if not isinstance(snapshots, dict):
            snapshots = {}
            self.deleted_event_graph_snapshots = snapshots
        return snapshots

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve metadata for a specific event by event_id.

        Args:
            event_id (str): The unique identifier of the event.

        Returns:
            dict: {
                'success': True,
                'data': EventInfo  # Metadata for the event if found
            }
            or
            {
                'success': False,
                'error': str  # Reason for failure
            }

        Constraints:
            - event_id must correspond to an existing Event in the system.
        """
        event_info = self.events.get(event_id)
        if event_info is None:
            return { "success": False, "error": "Event not found" }
        return { "success": True, "data": event_info }

    def list_events(self) -> dict:
        """
        Retrieve a list of all events and their metadata.

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo]  # List of all events (may be empty if none exist)
            }

        Notes:
            - No input parameters.
            - This operation simply returns all current events.
            - No error is returned if there are no events (data will be an empty list).
        """
        events_list = list(self.events.values())
        return {
            "success": True,
            "data": events_list
        }

    def get_metrics_by_event_id(self, event_id: str) -> dict:
        """
        Retrieve all MetricInfo dictionaries associated with a specific event.

        Args:
            event_id (str): The unique identifier of the event.

        Returns:
            dict:
                success: True and data: list of MetricInfo if event exists,
                        (data will be empty if no metrics found)
                On failure, success: False and error reason.
        Constraints:
            - event_id must exist in the system.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        # Collect all metrics with this event_id (iterate through self.metrics.values())
        metric_list = [
            metric_info for metric_info in self.metrics.values()
            if metric_info["event_id"] == event_id
        ]

        return {"success": True, "data": metric_list}

    def get_metric_info(self, event_id: str, metric_name: str) -> dict:
        """
        Retrieve the full metadata (MetricInfo) for a specific metric of a given event.

        Args:
            event_id (str): The unique ID of the event to which the metric belongs.
            metric_name (str): The metric's name.

        Returns:
            dict: {
                "success": True,
                "data": MetricInfo
            }
            or
            {
                "success": False,
                "error": str  # "Metric not found for event"
            }

        Constraints:
            - The metric must exist (identified by event_id and metric_name).
        """
        metric_id = f"{event_id}:{metric_name}"
        metric_info = self.metrics.get(metric_id)
        if metric_info is None:
            return {"success": False, "error": "Metric not found for event"}

        return {"success": True, "data": metric_info}

    def list_datapoints_by_event(
        self,
        event_id: str,
        metric_name: str = None,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Retrieve all datapoints for a given event, with optional filtering by metric name and timestamp range.

        Args:
            event_id (str): ID of the event whose datapoints are being queried.
            metric_name (str, optional): If provided, only datapoints with this metric_name are returned.
            start_time (float, optional): If provided, only datapoints with timestamp >= start_time are returned.
            end_time (float, optional): If provided, only datapoints with timestamp <= end_time are returned.

        Returns:
            dict:
              - {"success": True, "data": List[DataPointInfo]}
              - {"success": False, "error": str}

        Constraints:
            - event_id must refer to an existing event.
            - If metric_name is given, it must be associated with the event.
            - Time filters are optional; if set, must be float timestamps.
        """
        # Check if event exists
        if event_id not in self.events:
            return {"success": False, "error": "Event ID does not exist"}

        event_info = self.events[event_id]

        # If metric_name specified, check that it is attached to the event
        if metric_name is not None:
            if metric_name not in event_info.get("metrics", []):
                return {"success": False, "error": f"Metric '{metric_name}' not associated with event '{event_id}'"}

        # Filtering
        result = []
        for dp in self.datapoints.values():
            if dp["event_id"] != event_id:
                continue
            if metric_name is not None and dp["metric_name"] != metric_name:
                continue
            if start_time is not None and dp["timestamp"] < start_time:
                continue
            if end_time is not None and dp["timestamp"] > end_time:
                continue
            result.append(dp)

        return {"success": True, "data": result}

    def list_datapoints_by_metric(
        self, 
        event_id: str, 
        metric_name: str, 
        timestamp_from: float = None, 
        timestamp_to: float = None
    ) -> dict:
        """
        Retrieve all datapoints for a specific metric in an event, optionally filterable by timestamp.

        Args:
            event_id (str): The unique ID of the event.
            metric_name (str): The name of the metric associated with the event.
            timestamp_from (float, optional): Filter to datapoints with timestamp >= this value.
            timestamp_to (float, optional): Filter to datapoints with timestamp <= this value.

        Returns:
            dict: 
                { "success": True, "data": [List[DataPointInfo]] }
                or
                { "success": False, "error": "reason" }
    
        Constraints:
            - event_id must exist in the system.
            - metric (event_id + metric_name) must exist in the system.
            - Returns only DataPoints matching event_id and metric_name, filtered by the optional timestamp range.
        """
        # Check event existence
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        metric_id = f"{event_id}:{metric_name}"
        if metric_id not in self.metrics:
            return { "success": False, "error": "Metric does not exist for the specified event" }

        # Filtering
        result = []
        for dp in self.datapoints.values():
            if dp["event_id"] != event_id or dp["metric_name"] != metric_name:
                continue
            if timestamp_from is not None and dp["timestamp"] < timestamp_from:
                continue
            if timestamp_to is not None and dp["timestamp"] > timestamp_to:
                continue
            result.append(dp)

        return { "success": True, "data": result }

    def get_datapoint_by_id(self, datapoint_id: str) -> dict:
        """
        Fetch the attributes of a DataPoint by its unique datapoint_id.

        Args:
            datapoint_id (str): The identifier of the DataPoint to retrieve.

        Returns:
            dict:
                - If found: { "success": True, "data": DataPointInfo }
                - If not found: { "success": False, "error": "DataPoint not found" }
        """
        datapoint = self.datapoints.get(datapoint_id)
        if not datapoint:
            return { "success": False, "error": "DataPoint not found" }

        return { "success": True, "data": datapoint }

    def get_latest_datapoint(self, event_id: str, metric_name: str) -> dict:
        """
        Retrieve the most recent datapoint for a given event/metric pair.

        Args:
            event_id (str): The unique identifier for the event.
            metric_name (str): The name of the metric within the event.

        Returns:
            dict: {
                "success": True,
                "data": DataPointInfo  # The most recent datapoint info
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The event must exist.
            - The metric must exist for the specified event.
            - If there are no datapoints for this event/metric, return error.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event not found"}

        metric_id = f"{event_id}:{metric_name}"
        if metric_id not in self.metrics:
            return {"success": False, "error": "Metric not found for given event"}

        # Collect datapoints corresponding to event_id and metric_name
        filtered = [
            dp for dp in self.datapoints.values()
            if dp["event_id"] == event_id and dp["metric_name"] == metric_name
        ]

        if not filtered:
            return {"success": False, "error": "No datapoints found for specified event and metric"}

        # Find datapoint with latest (maximum) timestamp
        latest_dp = max(filtered, key=lambda dp: dp["timestamp"])
        return {"success": True, "data": latest_dp}

    def get_event_graph_points(
        self, 
        event_id: str,
        metric_names: List[str] = None,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Retrieve datapoints filtered and formatted for visualization for a specific event.

        Args:
            event_id (str): Event identifier.
            metric_names (List[str], optional): List of metric_names to restrict datapoints. 
                                                If None, include all metrics for the event.
            start_time (float, optional): Earliest timestamp to include (inclusive).
            end_time (float, optional): Latest timestamp to include (inclusive).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[DataPointInfo]  # May be empty. Sorted by timestamp ascending.
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The event_id must exist.
            - If metric_names provided, must be subset of event's metrics.
            - If specified, start_time must be <= end_time.
        """
        snapshot = None
        if event_id in self.events:
            event_info = self.events[event_id]
            event_metrics = set(event_info["metrics"])
            datapoint_source = list(self.datapoints.values())
        else:
            snapshot = self._ensure_deleted_graph_snapshots().get(event_id)
            if snapshot is None:
                return { "success": False, "error": "Event does not exist" }
            event_metrics = set(snapshot.get("metric_names", []))
            datapoint_source = list(snapshot.get("datapoints", []))

        # Validate metric_names
        if metric_names is not None:
            if not set(metric_names).issubset(event_metrics):
                return { "success": False, "error": "Some provided metric_names are not associated with this event" }
            metrics_filter = set(metric_names)
        else:
            metrics_filter = event_metrics

        # Validate time range
        if (start_time is not None) and (end_time is not None):
            if start_time > end_time:
                return { "success": False, "error": "start_time cannot be greater than end_time" }

        # Filter datapoints
        filtered = []
        for dp in datapoint_source:
            if dp["event_id"] != event_id:
                continue
            if dp["metric_name"] not in metrics_filter:
                continue
            if start_time is not None and dp["timestamp"] < start_time:
                continue
            if end_time is not None and dp["timestamp"] > end_time:
                continue
            filtered.append(dp)

        filtered.sort(key=lambda x: x["timestamp"])  # Ascending

        return {
            "success": True,
            "data": filtered
        }

    def create_event(
        self,
        event_id: str,
        name: str,
        description: str,
        created_at: str,
        metrics: list = None
    ) -> dict:
        """
        Create a new event with the specified metadata.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Human-readable event name.
            description (str): Description of the event.
            created_at (str): Creation timestamp (ISO/date string recommended).
            metrics (list, optional): List of metric names to associate at creation (may be empty/None).

        Returns:
            dict: {
                'success': True,
                'message': 'Event <event_id> created.'
            }
            or
            {
                'success': False,
                'error': <reason>
            }

        Constraints:
            - event_id must be unique in self.events.
            - All parameters except metrics are required.
            - If metrics is not provided, will be set as an empty list.
        """
        # Validate required arguments
        if not event_id or not name or not description or not created_at:
            return {
                "success": False,
                "error": "Missing required field (event_id, name, description, created_at are required)."
            }

        # Uniqueness check
        if event_id in self.events:
            return {
                "success": False,
                "error": "Event ID already exists."
            }

        # Accept empty metrics if not provided
        if metrics is None:
            metrics = []

        event_info: EventInfo = {
            "event_id": event_id,
            "name": name,
            "description": description,
            "created_at": created_at,
            "metrics": metrics
        }

        self.events[event_id] = event_info

        return {
            "success": True,
            "message": f"Event {event_id} created."
        }

    def create_metric(self, event_id: str, metric_name: str, unit: str, description: str) -> dict:
        """
        Create a new metric under an existing event.

        Args:
            event_id (str): The ID of the event to associate the metric with. Must already exist.
            metric_name (str): The unique name of the metric under this event.
            unit (str): The unit of the metric.
            description (str): Description of the metric.

        Returns:
            dict:
                On success: { "success": True, "message": "Metric created successfully" }
                On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - Event with event_id must exist.
            - (event_id, metric_name) combination must not already exist.
            - metric_name must be added to the EventInfo.metrics list if success.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        metric_id = f"{event_id}:{metric_name}"
        if metric_id in self.metrics:
            return {"success": False, "error": "Metric already exists for this event"}

        # Create the metric
        metric_info: MetricInfo = {
            "metric_name": metric_name,
            "event_id": event_id,
            "unit": unit,
            "description": description
        }
        self.metrics[metric_id] = metric_info

        # Add metric_name to the EventInfo.metrics list if not already present
        if metric_name not in self.events[event_id]["metrics"]:
            self.events[event_id]["metrics"].append(metric_name)

        return {"success": True, "message": "Metric created successfully"}

    def record_datapoint(
        self,
        event_id: str,
        metric_name: str,
        timestamp: float,
        value: float
    ) -> dict:
        """
        Add a new datapoint for the given event and metric at the specified timestamp.

        Args:
            event_id (str): ID of the event.
            metric_name (str): Name of the metric for this event.
            timestamp (float): UNIX timestamp at which value was observed.
            value (float): Value to record.

        Returns:
            dict: {
                "success": True,
                "message": "Datapoint recorded successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - event_id must exist in the environment.
            - metric (event_id, metric_name) must exist for the event.
            - timestamp must be > last timestamp for this event_id+metric_name (if any datapoints exist).
        """
        # Validate event_id
        if event_id not in self.events:
            return { "success": False, "error": "Event ID does not exist." }
    
        # Validate metric existence
        metric_id = f"{event_id}:{metric_name}"
        if metric_id not in self.metrics:
            return { "success": False, "error": "Metric does not exist for the specified event." }
    
        # Enforce timestamp monotonicity for event_id+metric_name
        relevant_datapoints = [
            dp for dp in self.datapoints.values()
            if dp["event_id"] == event_id and dp["metric_name"] == metric_name
        ]
        if relevant_datapoints:
            last_timestamp = max(dp["timestamp"] for dp in relevant_datapoints)
            if timestamp <= last_timestamp:
                return {
                    "success": False,
                    "error": "Timestamp must be greater than the last datapoint's timestamp for this event/metric."
                }
    
        # datpoint_id must be unique. We'll autogenerate a new ID.
        datapoint_id = str(uuid.uuid4())
        new_datapoint = {
            "datapoint_id": datapoint_id,
            "event_id": event_id,
            "timestamp": float(timestamp),
            "metric_name": metric_name,
            "value": float(value)
        }
        self.datapoints[datapoint_id] = new_datapoint

        return {
            "success": True,
            "message": "Datapoint recorded successfully."
        }

    def update_event_info(
        self, 
        event_id: str, 
        name: str = None, 
        description: str = None
    ) -> dict:
        """
        Modify the metadata for an existing event.

        Args:
            event_id (str): Unique identifier of the event to update.
            name (str, optional): New name for the event.
            description (str, optional): New description for the event.

        Returns:
            dict: 
                On success: {"success": True, "message": "Event info updated successfully"}
                On failure: {"success": False, "error": "reason"}

        Constraints:
            - The event with event_id must already exist.
            - Only 'name' and 'description' are updatable via this operation.
            - Does not update event_id, created_at, or metrics.
        """
        event = self.events.get(event_id)
        if event is None:
            return { "success": False, "error": "Event not found" }

        updated = False

        # Only update allowed metadata fields if new values provided
        if name is not None and name != event.get("name"):
            event["name"] = name
            updated = True
        if description is not None and description != event.get("description"):
            event["description"] = description
            updated = True

        if not updated:
            return { "success": False, "error": "No changes provided or values unchanged" }

        self.events[event_id] = event
        return { "success": True, "message": "Event info updated successfully" }

    def update_metric_info(
        self,
        event_id: str,
        metric_name: str,
        unit: str = None,
        description: str = None
    ) -> dict:
        """
        Modify metadata (unit, description) for an existing metric.

        Args:
            event_id (str): The event identifier that owns the metric.
            metric_name (str): Name of the metric to update.
            unit (str, optional): New unit string for the metric (if updating).
            description (str, optional): New description for the metric (if updating).

        Returns:
            dict: 
                On success: { "success": True, "message": "Metric metadata updated successfully." }
                On error:   { "success": False, "error": <reason> }

        Constraints:
            - The metric identified by (event_id, metric_name) must exist.
            - Only unit and description can be modified (not event_id or metric_name).
            - At least one updatable field (unit or description) must be provided.
        """
        metric_id = f"{event_id}:{metric_name}"
        if metric_id not in self.metrics:
            return {"success": False, "error": "Metric does not exist."}
    
        updatable = False
        if unit is not None:
            self.metrics[metric_id]['unit'] = unit
            updatable = True
        if description is not None:
            self.metrics[metric_id]['description'] = description
            updatable = True
        if not updatable:
            return {"success": False, "error": "No updatable fields provided (unit or description must be specified)."}

        return {"success": True, "message": "Metric metadata updated successfully."}

    def delete_event(self, event_id: str) -> dict:
        """
        Remove an event, as well as all metrics and datapoints associated with it.

        Args:
            event_id (str): The unique identifier of the event to delete.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Event and all associated metrics/data points deleted."
                }
                On error: {
                    "success": False,
                    "error": "Event does not exist."
                }

        Constraints:
            - Event must exist.
            - All metrics where metric_info.event_id == event_id are deleted.
            - All datapoints where datapoint_info.event_id == event_id are deleted.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }
    
        if event_id in self._get_deletion_snapshot_allowlist():
            snapshot_metrics = list(self.events[event_id].get("metrics", []))
            snapshot_datapoints = [
                copy.deepcopy(dp)
                for dp in self.datapoints.values()
                if dp["event_id"] == event_id
            ]
            self._ensure_deleted_graph_snapshots()[event_id] = {
                "metric_names": snapshot_metrics,
                "datapoints": snapshot_datapoints,
            }

        # Remove event
        del self.events[event_id]
    
        # Remove metrics for the event
        metrics_to_delete = [metric_id for metric_id, metric in self.metrics.items() if metric["event_id"] == event_id]
        for metric_id in metrics_to_delete:
            del self.metrics[metric_id]
    
        # Remove datapoints for the event
        datapoints_to_delete = [dp_id for dp_id, dp in self.datapoints.items() if dp["event_id"] == event_id]
        for dp_id in datapoints_to_delete:
            del self.datapoints[dp_id]
    
        return { "success": True, "message": "Event and all associated metrics/data points deleted." }

    def delete_datapoint(self, datapoint_id: str) -> dict:
        """
        Remove an existing DataPoint from the analytics system.

        Args:
            datapoint_id (str): The unique identifier for the DataPoint to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Datapoint <datapoint_id> deleted successfully"
            }
            or
            {
                "success": False,
                "error": "Datapoint not found"
            }

        Constraints:
            - The DataPoint must exist before it can be deleted.
        """
        if datapoint_id not in self.datapoints:
            return { "success": False, "error": "Datapoint not found" }

        del self.datapoints[datapoint_id]
        return { "success": True, "message": f"Datapoint {datapoint_id} deleted successfully" }

    def bulk_record_datapoints(self, datapoints: list) -> dict:
        """
        Efficiently add multiple datapoints for one or more events/metrics in a batch operation, with validation.

        Args:
            datapoints (list): List[dict] or List[DataPointInfo].
                Each element must contain: datapoint_id, event_id, timestamp, metric_name, value.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "<N> datapoints recorded successfully"
                    }
                On failure (validation error):
                    {
                        "success": False,
                        "error": "Detailed error message(s)"
                    }

        Constraints:
            - Each datapoint must refer to an existing event_id.
            - Each datapoint's metric_name must be registered to the event.
            - Each datapoint_id must be unique in the system and within the batch.
            - Optionally, timestamps for (event_id, metric_name) should be monotonically increasing.
            - If any validation fails, no datapoints from the batch are recorded.
        """
        errors = []
        seen_ids = set()
        # Pre-cache timestamps by (event_id, metric_name) for monotonic check
        latest_timestamps = {}

        # Build a (event_id, metric_name) -> latest timestamp map from existing datapoints
        for dp in self.datapoints.values():
            key = (dp["event_id"], dp["metric_name"])
            if key not in latest_timestamps or dp["timestamp"] > latest_timestamps[key]:
                latest_timestamps[key] = dp["timestamp"]

        # Collect new timestamps in batch for monotonic validation
        batch_latest_timestamps = latest_timestamps.copy()

        for idx, dp in enumerate(datapoints):
            dpid = dp.get("datapoint_id")
            eid = dp.get("event_id")
            metric = dp.get("metric_name")
            ts = dp.get("timestamp")
            value = dp.get("value")
            location = f"item#{idx} (datapoint_id={dpid})"

            # Check presence of all required fields
            for req in ("datapoint_id", "event_id", "metric_name", "timestamp", "value"):
                if req not in dp:
                    errors.append(f"{location}: Missing required field '{req}'.")
                    continue

            if dpid in seen_ids:
                errors.append(f"{location}: Duplicate datapoint_id within this batch.")
            if dpid in self.datapoints:
                errors.append(f"{location}: datapoint_id already exists in system.")

            seen_ids.add(dpid)

            # Validate event_id exists
            if eid not in self.events:
                errors.append(f"{location}: event_id '{eid}' does not exist.")

            # Validate metric existence for the event
            metric_id = f"{eid}:{metric}"
            if metric_id not in self.metrics:
                errors.append(f"{location}: metric '{metric}' for event_id '{eid}' does not exist.")

            # Optionally: Monotonic timestamp check (for each (event_id,metric_name))
            key = (eid, metric)
            last_ts = batch_latest_timestamps.get(key, float('-inf'))
            if not (isinstance(ts, float) or isinstance(ts, int)):
                errors.append(f"{location}: timestamp must be a float or int.")
            elif ts < last_ts:
                errors.append(f"{location}: timestamp {ts} is less than last recorded timestamp {last_ts} for this metric/event.")
            else:
                batch_latest_timestamps[key] = ts

        if errors:
            return { "success": False, "error": "; ".join(errors) }

        # If all valid, insert datapoints
        for dp in datapoints:
            self.datapoints[dp["datapoint_id"]] = {
                "datapoint_id": dp["datapoint_id"],
                "event_id": dp["event_id"],
                "timestamp": float(dp["timestamp"]),
                "metric_name": dp["metric_name"],
                "value": float(dp["value"])
            }

        return {
            "success": True,
            "message": f"{len(datapoints)} datapoints recorded successfully"
        }


class EventMonitoringAnalyticsSystem(BaseEnv):
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
            if key == "metrics" and isinstance(value, dict):
                normalized_metrics = {}
                for _raw_key, metric in value.items():
                    if isinstance(metric, dict):
                        event_id = metric.get("event_id")
                        metric_name = metric.get("metric_name")
                        if event_id is not None and metric_name is not None:
                            normalized_metrics[f"{event_id}:{metric_name}"] = copy.deepcopy(metric)
                        else:
                            normalized_metrics[_raw_key] = copy.deepcopy(metric)
                    else:
                        normalized_metrics[_raw_key] = copy.deepcopy(metric)
                setattr(env, key, normalized_metrics)
            else:
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

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def list_events(self, **kwargs):
        return self._call_inner_tool('list_events', kwargs)

    def get_metrics_by_event_id(self, **kwargs):
        return self._call_inner_tool('get_metrics_by_event_id', kwargs)

    def get_metric_info(self, **kwargs):
        return self._call_inner_tool('get_metric_info', kwargs)

    def list_datapoints_by_event(self, **kwargs):
        return self._call_inner_tool('list_datapoints_by_event', kwargs)

    def list_datapoints_by_metric(self, **kwargs):
        return self._call_inner_tool('list_datapoints_by_metric', kwargs)

    def get_datapoint_by_id(self, **kwargs):
        return self._call_inner_tool('get_datapoint_by_id', kwargs)

    def get_latest_datapoint(self, **kwargs):
        return self._call_inner_tool('get_latest_datapoint', kwargs)

    def get_event_graph_points(self, **kwargs):
        return self._call_inner_tool('get_event_graph_points', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def create_metric(self, **kwargs):
        return self._call_inner_tool('create_metric', kwargs)

    def record_datapoint(self, **kwargs):
        return self._call_inner_tool('record_datapoint', kwargs)

    def update_event_info(self, **kwargs):
        return self._call_inner_tool('update_event_info', kwargs)

    def update_metric_info(self, **kwargs):
        return self._call_inner_tool('update_metric_info', kwargs)

    def delete_event(self, **kwargs):
        return self._call_inner_tool('delete_event', kwargs)

    def delete_datapoint(self, **kwargs):
        return self._call_inner_tool('delete_datapoint', kwargs)

    def bulk_record_datapoints(self, **kwargs):
        return self._call_inner_tool('bulk_record_datapoints', kwargs)
