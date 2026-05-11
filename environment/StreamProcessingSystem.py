# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict
import time
from typing import Dict, Any



# Represents an incoming data source (stream)
class StreamInfo(TypedDict):
    stream_id: str
    source_info: str
    configuration: Dict[str, Any]
    active_state: str

# Represents a single data entry in a stream
class EventInfo(TypedDict):
    stream_id: str
    event_id: str
    timestamp: float
    data_fields: Dict[str, Any]

# Represents a time-bounded window of events
class WindowInfo(TypedDict):
    window_id: str
    stream_id: str
    start_time: float
    end_time: float
    events: List[str]  # List of Event IDs

# Stores the result of an aggregation operation
class AggregationResultInfo(TypedDict):
    window_id: str
    metric_name: str
    result_value: float
    computed_at: float

# Defines the processing logic (filters, aggregations)
class ProcessingRuleInfo(TypedDict):
    rule_id: str
    stream_id: str
    filter_criteria: Dict[str, Any]
    aggregation_type: str
    window_size: float
    target_field: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The stream processing system environment state.
        """

        # Streams: {stream_id: StreamInfo}
        self.streams: Dict[str, StreamInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Windows: {window_id: WindowInfo}
        self.windows: Dict[str, WindowInfo] = {}

        # Aggregation Results: {window_id: List[AggregationResultInfo]}
        self.aggregations: Dict[str, List[AggregationResultInfo]] = {}

        # Processing Rules: {rule_id: ProcessingRuleInfo}
        self.processing_rules: Dict[str, ProcessingRuleInfo] = {}

        # Constraints:
        # - Only events within the configured window (e.g., last 10 minutes) are considered for current aggregations and processing.
        # - Each stream has independent processing state and configuration.
        # - Aggregations are recorded/updated as new events arrive and windows advance.
        # - Filtering and aggregations are determined by active ProcessingRules per stream.
        # - Expired events (older than the window) must be efficiently discarded from memory/state.

    @staticmethod
    def _field_matches_ops(value: Any, ops: Any) -> bool:
        if isinstance(ops, dict):
            for op, compare_value in ops.items():
                if op == "eq":
                    if value != compare_value:
                        return False
                elif op == "neq":
                    if value == compare_value:
                        return False
                elif op == "gt":
                    if not (value > compare_value):
                        return False
                elif op == "gte":
                    if not (value >= compare_value):
                        return False
                elif op == "lt":
                    if not (value < compare_value):
                        return False
                elif op == "lte":
                    if not (value <= compare_value):
                        return False
                elif op == "in":
                    if not isinstance(compare_value, (list, tuple, set)):
                        return False
                    if value not in compare_value:
                        return False
                elif op == "nin":
                    if not isinstance(compare_value, (list, tuple, set)):
                        return False
                    if value in compare_value:
                        return False
                else:
                    return False
            return True
        return value == ops

    def _event_matches_filter_criteria(self, event: EventInfo, filter_criteria: Dict[str, Any]) -> bool:
        for field, ops in (filter_criteria or {}).items():
            if field not in event["data_fields"]:
                return False
            if not self._field_matches_ops(event["data_fields"][field], ops):
                return False
        return True

    @staticmethod
    def _timestamp_in_window(timestamp: float, start_time: float, end_time: float) -> bool:
        return start_time <= timestamp < end_time

    def _event_ids_for_stream_window(
        self,
        stream_id: str,
        start_time: float,
        end_time: float,
    ) -> List[str]:
        return [
            event_id
            for event_id, event in self.events.items()
            if event["stream_id"] == stream_id
            and self._timestamp_in_window(event["timestamp"], start_time, end_time)
        ]

    def _window_event_records(self, window: WindowInfo) -> List[EventInfo]:
        seen_event_ids = set()
        event_records: List[EventInfo] = []
        start_time = window["start_time"]
        end_time = window["end_time"]
        stream_id = window["stream_id"]

        for event_id in window.get("events", []):
            event = self.events.get(event_id)
            if (
                event is not None
                and event["stream_id"] == stream_id
                and self._timestamp_in_window(event["timestamp"], start_time, end_time)
                and event_id not in seen_event_ids
            ):
                seen_event_ids.add(event_id)
                event_records.append(event)

        for event_id in self._event_ids_for_stream_window(stream_id, start_time, end_time):
            if event_id in seen_event_ids:
                continue
            event = self.events.get(event_id)
            if event is not None:
                seen_event_ids.add(event_id)
                event_records.append(event)

        return event_records

    def _find_processing_rule_for_stream(self, stream_id: str):
        for rule in self.processing_rules.values():
            if rule["stream_id"] == stream_id:
                return rule
        return None

    def _store_aggregation_result(
        self,
        window_id: str,
        metric_name: str,
        result_value: float,
        computed_at: float,
    ) -> None:
        aggregation_info = {
            "window_id": window_id,
            "metric_name": metric_name,
            "result_value": result_value,
            "computed_at": computed_at,
        }
        if window_id not in self.aggregations:
            self.aggregations[window_id] = []

        for idx, existing in enumerate(self.aggregations[window_id]):
            if existing["metric_name"] == metric_name:
                self.aggregations[window_id][idx] = aggregation_info
                return

        self.aggregations[window_id].append(aggregation_info)

    @staticmethod
    def _compute_aggregation_value(
        aggregation_type: str,
        target_field: str,
        events: List[EventInfo],
    ):
        agg_type_lc = aggregation_type.lower()
        present_values = [
            event["data_fields"][target_field]
            for event in events
            if target_field in event["data_fields"]
        ]

        if agg_type_lc == "count":
            return True, "", len(present_values), f"count_{target_field}"

        if not present_values:
            return False, "No eligible events with the target field for aggregation.", None, None

        numeric_values = [value for value in present_values if isinstance(value, (int, float))]
        if not numeric_values:
            return False, "No eligible events with the target field for aggregation.", None, None

        if agg_type_lc == "sum":
            return True, "", sum(numeric_values), f"sum_{target_field}"
        if agg_type_lc in {"avg", "average"}:
            return True, "", sum(numeric_values) / len(numeric_values), f"{agg_type_lc}_{target_field}"
        if agg_type_lc == "min":
            return True, "", min(numeric_values), f"min_{target_field}"
        if agg_type_lc == "max":
            return True, "", max(numeric_values), f"max_{target_field}"

        return False, f"Aggregation type '{aggregation_type}' not supported.", None, None

    def get_stream_info(self, stream_id: str) -> dict:
        """
        Retrieve metadata and configuration for a specific stream by stream_id.

        Args:
            stream_id (str): The unique identifier of the stream to query.

        Returns:
            dict: {
                "success": True,
                "data": StreamInfo,      # Full metadata/configuration of the stream
              }
              OR
              {
                "success": False,
                "error": str             # Reason for failure, e.g. stream not found
              }

        Constraints:
            - stream_id must exist in the system for a successful result.
        """
        stream = self.streams.get(stream_id)
        if stream is None:
            return {"success": False, "error": "Stream ID does not exist"}
        return {"success": True, "data": stream}

    def list_streams(self) -> dict:
        """
        List all currently registered data streams.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[StreamInfo]
                    }
                (The list may be empty if there are no streams.)
        """
        streams_list = list(self.streams.values())
        return {
            "success": True,
            "data": streams_list
        }

    def get_processing_rule(self, rule_id: str = None, stream_id: str = None) -> dict:
        """
        Retrieve the active processing rule, identified by rule_id or stream_id.

        Args:
            rule_id (str, optional): Unique identifier of the processing rule.
            stream_id (str, optional): Stream ID for which to retrieve the rule.

        Returns:
            dict:
                - On success: { "success": True, "data": ProcessingRuleInfo }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - At least one of rule_id or stream_id must be provided.
            - If both are provided, rule_id takes precedence.
            - If stream_id is used, returns the first matching rule for the stream.
        """
        if rule_id:
            rule = self.processing_rules.get(rule_id)
            if rule:
                return {"success": True, "data": rule}
            else:
                return {"success": False, "error": "Processing rule not found"}
        elif stream_id:
            for rule in self.processing_rules.values():
                if rule["stream_id"] == stream_id:
                    return {"success": True, "data": rule}
            return {"success": False, "error": "Processing rule not found"}
        else:
            return {"success": False, "error": "Must specify rule_id or stream_id"}

    def list_processing_rules_for_stream(self, stream_id: str) -> dict:
        """
        List all processing rules currently associated with a specific stream.

        Args:
            stream_id (str): The unique identifier of the stream.

        Returns:
            dict: {
                "success": True,
                "data": List[ProcessingRuleInfo],  # List of processing rules for the stream, may be empty.
            }
            or
            {
                "success": False,
                "error": str  # "Stream does not exist"
            }

        Constraints:
            - The stream must exist in the stream processing system.
            - Returns all (possibly zero) processing rules configured for the stream.
        """
        if stream_id not in self.streams:
            return { "success": False, "error": "Stream does not exist" }

        rules = [
            rule_info for rule_info in self.processing_rules.values()
            if rule_info["stream_id"] == stream_id
        ]
        return { "success": True, "data": rules }

    def get_events_in_window(
        self, 
        window_id: str = None, 
        stream_id: str = None, 
        start_time: float = None, 
        end_time: float = None
    ) -> dict:
        """
        Retrieve all events belonging to a specified stream within a window.
    
        You may provide either:
          - window_id (str): Identifier of the window. Retrieves window by id and returns all events inside it (restricted to the window's stream).
          - OR stream_id (str), start_time (float), end_time (float): Explicit time interval for stream filtering.
    
        Args:
            window_id (str, optional): ID of the window to look up.
            stream_id (str, optional): Stream ID to use when querying by interval.
            start_time (float, optional): Inclusive window start timestamp.
            end_time (float, optional): Inclusive window end timestamp.
    
        Returns:
            dict:
              success: True/False
              data: List[EventInfo] (on success)
              error: str (on failure)
        """
        # Route 1: by window_id
        if window_id is not None:
            window = self.windows.get(window_id)
            if window is None:
                return {"success": False, "error": "Window ID does not exist"}
            return {"success": True, "data": self._window_event_records(window)}

        # Route 2: stream_id + interval
        if stream_id is not None and start_time is not None and end_time is not None:
            if stream_id not in self.streams:
                return {"success": False, "error": f"Stream ID '{stream_id}' does not exist"}
            result = [
                event for event in self.events.values()
                if event["stream_id"] == stream_id
                and start_time <= event["timestamp"] <= end_time
            ]
            return {"success": True, "data": result}

        # Not enough parameters
        return {"success": False, "error": "Must provide either window_id or (stream_id, start_time, end_time)"}

    def get_events_by_filter(
        self,
        stream_id: str,
        filter_criteria: dict,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Retrieve all events in the specified stream that meet filter criteria
        within the given time window.

        Args:
            stream_id (str): The stream identifier.
            filter_criteria (dict): Filtering logic on data_fields, e.g. {"temperature": {"gt": 30}}.
            start_time (float): Start of the time window (inclusive).
            end_time (float): End of the time window (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[EventInfo],  # All matching event records
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - Only events from the specified stream and within [start_time, end_time] are considered.
        """
        if stream_id not in self.streams:
            return { "success": False, "error": "Stream does not exist" }

        results = []
        for event in self.events.values():
            if (
                event['stream_id'] == stream_id and
                start_time <= event['timestamp'] <= end_time
            ):
                if self._event_matches_filter_criteria(event, filter_criteria):
                    results.append(event)
        return { "success": True, "data": results }

    def get_current_windows_for_stream(self, stream_id: str) -> dict:
        """
        List all active time windows (WindowInfo dicts) currently associated with the given stream ID.

        Args:
            stream_id (str): The ID of the stream.

        Returns:
            dict: {
                "success": True,
                "data": List[WindowInfo],  # All WindowInfo for this stream (can be empty if no windows)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. stream does not exist.
            }

        Constraints:
            - The stream_id must exist in self.streams.
        """
        if stream_id not in self.streams:
            return { "success": False, "error": "Stream does not exist" }
        windows = [
            window_info
            for window_info in self.windows.values()
            if window_info["stream_id"] == stream_id
        ]
        return { "success": True, "data": windows }

    def get_window_info(self, window_id: str) -> dict:
        """
        Retrieve details of a specific window by its window_id.

        Args:
            window_id (str): The identifier of the window.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": WindowInfo  # Dictionary with window details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Window not found"
                    }
        Constraints:
            - window_id must exist in the system.
        """
        window_info = self.windows.get(window_id)
        if window_info is None:
            return {
                "success": False,
                "error": "Window not found"
            }
        return {
            "success": True,
            "data": window_info
        }

    def get_aggregation_results(self, window_id: str, metric_name: str) -> dict:
        """
        Retrieve the latest aggregation result for a given window and metric.

        Args:
            window_id (str): The ID of the window.
            metric_name (str): The name of the metric to retrieve (e.g., 'average_humidity').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AggregationResultInfo  # The most recent result for the metric in this window
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Explanation (e.g., window or metric not found)
                    }

        Constraints:
            - window_id must exist.
            - metric_name must exist for the specified window_id.
            - If multiple results for the same metric, return the latest one (by computed_at).
        """
        agg_list = self.aggregations.get(window_id)
        if agg_list is None or not agg_list:
            return { "success": False, "error": "No aggregation results found for the specified window_id." }

        # Filter for metric_name
        matching = [
            agg for agg in agg_list if agg["metric_name"] == metric_name
        ]
        if not matching:
            return { "success": False, "error": f"No aggregation result found for metric '{metric_name}' in window '{window_id}'." }

        # Return the latest by computed_at
        latest = max(matching, key=lambda x: x["computed_at"])
        return { "success": True, "data": latest }

    def event_belongs_to_window(self, event_id: str, window_id: str) -> dict:
        """
        Confirm whether a specific event (by event_id) is part of a given window (by window_id).

        Args:
            event_id (str): The unique identifier for the event.
            window_id (str): The unique identifier for the window.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if the event belongs to the window, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Both event_id and window_id must exist in the system.
        """
        if window_id not in self.windows:
            return { "success": False, "error": "Window does not exist" }
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        window = self.windows[window_id]
        belongs = event_id in window["events"]
        return { "success": True, "data": belongs }

    def insert_event(self, event_id: str, stream_id: str, timestamp: float, data_fields: Dict[str, Any]) -> dict:
        """
        Add a new event to a stream.

        Args:
            event_id (str): Unique identifier for the event.
            stream_id (str): Identifier of the stream to insert into (must exist).
            timestamp (float): Event's timestamp.
            data_fields (Dict[str, Any]): Key-value data associated with the event.

        Returns:
            dict: {
                "success": True,
                "message": "Event <event_id> inserted into stream <stream_id>."
            }
            or
            {
                "success": False,
                "error": "reason",
            }

        Constraints:
            - event_id must be unique.
            - stream_id must exist in self.streams.
        """

        # Check if stream exists
        if stream_id not in self.streams:
            return {"success": False, "error": f"Stream '{stream_id}' does not exist."}

        # Check that event_id is unique
        if event_id in self.events:
            return {"success": False, "error": f"Event ID '{event_id}' already exists."}

        # Basic parameter validation
        if not isinstance(data_fields, dict):
            return {"success": False, "error": "data_fields must be a dictionary of event fields."}

        # Insert the event
        event_info: EventInfo = {
            "stream_id": stream_id,
            "event_id": event_id,
            "timestamp": timestamp,
            "data_fields": data_fields
        }
        self.events[event_id] = event_info

        return {"success": True, "message": f"Event '{event_id}' inserted into stream '{stream_id}'."}

    def create_processing_rule(
        self,
        rule_id: str,
        stream_id: str,
        filter_criteria: dict,
        aggregation_type: str,
        window_size: float,
        target_field: str
    ) -> dict:
        """
        Define and register a new processing rule for a stream.

        Args:
            rule_id (str): Unique identifier for the processing rule.
            stream_id (str): Stream to which this rule will be applied. Must exist.
            filter_criteria (dict): Filtering key-value conditions.
            aggregation_type (str): Aggregation type ('sum', 'avg', 'count', etc.).
            window_size (float): Window size in seconds; must be > 0.
            target_field (str): Name of the event data field for aggregation.

        Returns:
            dict:
                - {"success": True, "message": "Processing rule <rule_id> created for stream <stream_id>."}
                - {"success": False, "error": "..."} on error

        Constraints:
            - rule_id must be unique.
            - stream_id must refer to an existing stream.
            - window_size > 0.
            - aggregation_type and target_field should be non-empty.
        """
        if rule_id in self.processing_rules:
            return {"success": False, "error": f"Processing rule with id '{rule_id}' already exists."}
        if stream_id not in self.streams:
            return {"success": False, "error": f"Stream with id '{stream_id}' does not exist."}
        if not isinstance(window_size, (float, int)) or window_size <= 0:
            return {"success": False, "error": "window_size must be a positive number."}
        if not aggregation_type or not isinstance(aggregation_type, str):
            return {"success": False, "error": "aggregation_type must be a non-empty string."}
        if not target_field or not isinstance(target_field, str):
            return {"success": False, "error": "target_field must be a non-empty string."}
        if not isinstance(filter_criteria, dict):
            return {"success": False, "error": "filter_criteria must be a dict."}

        rule_info = {
            "rule_id": rule_id,
            "stream_id": stream_id,
            "filter_criteria": filter_criteria,
            "aggregation_type": aggregation_type,
            "window_size": float(window_size),
            "target_field": target_field
        }
        self.processing_rules[rule_id] = rule_info
        return {
            "success": True,
            "message": f"Processing rule '{rule_id}' created for stream '{stream_id}'."
        }

    def update_processing_rule(
        self,
        rule_id: str,
        filter_criteria: dict = None,
        aggregation_type: str = None,
        window_size: float = None,
        target_field: str = None,
    ) -> dict:
        """
        Modify an existing processing rule's attributes.
    
        Args:
            rule_id (str): The identifier of the processing rule to update.
            filter_criteria (dict, optional): New filter criteria (replaces existing).
            aggregation_type (str, optional): New aggregation type.
            window_size (float, optional): New window size.
            target_field (str, optional): New target field.
        
        Returns:
            dict: {
                "success": True,
                "message": "Processing rule <rule_id> updated"
            }
            or
            {
                "success": False,
                "error": error message
            }
        Constraints:
            - The rule must exist.
            - At least one update field must be provided.
            - Only provided fields are changed.
        """
        if rule_id not in self.processing_rules:
            return { "success": False, "error": f"Processing rule '{rule_id}' does not exist" }

        update_fields = {
            "filter_criteria": filter_criteria,
            "aggregation_type": aggregation_type,
            "window_size": window_size,
            "target_field": target_field
        }
        updated = False

        for field, value in update_fields.items():
            if value is not None:
                if field == "window_size":
                    value = float(value)
                self.processing_rules[rule_id][field] = value
                updated = True

        if not updated:
            return {
                "success": False,
                "error": "No valid attributes provided to update"
            }

        return {
            "success": True,
            "message": f"Processing rule '{rule_id}' updated"
        }

    def advance_window(self, window_id: str) -> dict:
        """
        Move a stream window's time bounds (start_time, end_time) forward by its window size,
        update its event membership, and trigger recomputation of aggregations as per stream's
        ProcessingRule.

        Args:
            window_id (str): The unique ID of the window to advance.

        Returns:
            dict:
            - On success: { "success": True, "message": "Window advanced and computations updated." }
            - On failure: { "success": False, "error": str }
    
        Constraints:
            - window_id must refer to an existing window.
            - ProcessingRule (if any) is used to determine window size and aggregation.
            - The time window must slide forward by its configured size.
            - Events are included if stream_id matches, and event.timestamp in [start_time, end_time).
            - Aggregations are computed if ProcessingRule exists for this stream.
        """

        # --- Check window existence ---
        window = self.windows.get(window_id)
        if window is None:
            return { "success": False, "error": "Window ID not found." }
    
        stream_id = window["stream_id"]

        # Find relevant processing rule for the stream (if any)
        rule = self._find_processing_rule_for_stream(stream_id)

        if rule is None:
            return { "success": False, "error": "No processing rule found for the stream associated with this window." }

        window_size = rule["window_size"]
        current_interval_event_ids = self._event_ids_for_stream_window(
            stream_id,
            window["start_time"],
            window["end_time"],
        )

        # Newly added windows start empty. The first advance should ingest the
        # current interval before subsequent advances slide the time bounds.
        if not window.get("events") and current_interval_event_ids:
            event_ids_in_window = current_interval_event_ids
            computed_at = window["end_time"]
        else:
            old_start, old_end = window["start_time"], window["end_time"]
            new_start = old_start + window_size
            new_end = old_end + window_size
            window["start_time"] = new_start
            window["end_time"] = new_end
            event_ids_in_window = self._event_ids_for_stream_window(stream_id, new_start, new_end)
            computed_at = new_end

        window["events"] = event_ids_in_window

        # Expire only events that are older than all active windows for this stream
        # and are no longer referenced by any window.
        referenced_event_ids = {
            event_id
            for active_window in self.windows.values()
            if active_window["stream_id"] == stream_id
            for event_id in active_window["events"]
        }
        min_active_start = min(
            active_window["start_time"]
            for active_window in self.windows.values()
            if active_window["stream_id"] == stream_id
        )
        expired_eids = [
            eid
            for eid, ev in self.events.items()
            if ev["stream_id"] == stream_id
            and ev["timestamp"] < min_active_start
            and eid not in referenced_event_ids
        ]
        for eid in expired_eids:
            del self.events[eid]

        # Trigger aggregation if specified in the processing rule
        aggregation_type = rule.get("aggregation_type")
        target_field = rule.get("target_field")

        result_value = None
        metric_name = None

        if aggregation_type and target_field:
            eligible_events = [
                event
                for eid in event_ids_in_window
                for event in [self.events.get(eid)]
                if event is not None and self._event_matches_filter_criteria(event, rule.get("filter_criteria", {}))
            ]
            ok, _, result_value, metric_name = self._compute_aggregation_value(
                aggregation_type,
                target_field,
                eligible_events,
            )
            if not ok:
                result_value = None
                metric_name = None
        
            # Store aggregation result if valid
            if result_value is not None and metric_name is not None:
                self._store_aggregation_result(window_id, metric_name, result_value, computed_at)

        return { "success": True, "message": "Window advanced and computations updated." }


    def compute_aggregation_for_window(self, window_id: str) -> dict:
        """
        Perform or update an aggregation (e.g., avg, sum) over all eligible events in a window, 
        based on that stream's active processing rule.
    
        Args:
            window_id (str): The ID of the window to aggregate over.
    
        Returns:
            dict: 
                - On Success: { "success": True, "message": f"Aggregation '{agg_type}' computed for window {window_id}." }
                - On Failure: { "success": False, "error": "Reason" }
        Constraints:
            - Window must exist, and have associated stream_id.
            - Stream must have an active processing rule.
            - Only events in window and passing filter_criteria are considered.
            - Target field must exist in at least one event.
        """
        # 1. Validate window
        window_info = self.windows.get(window_id)
        if window_info is None:
            return { "success": False, "error": "Window does not exist." }
        stream_id = window_info.get("stream_id")
        if stream_id is None:
            return { "success": False, "error": "Window missing associated stream_id." }

        # 2. Find active processing rule for this stream
        rule = self._find_processing_rule_for_stream(stream_id)
        if rule is None:
            return { "success": False, "error": "No processing rule defined for stream." }
        agg_type = rule["aggregation_type"]
        target_field = rule["target_field"]
        filter_criteria = rule.get("filter_criteria", {})

        # 3. Gather filtered events
        eligible_events = []
        for event in self._window_event_records(window_info):
            if self._event_matches_filter_criteria(event, filter_criteria):
                eligible_events.append(event)

        # 4. Perform aggregation
        ok, error, result_value, metric_name = self._compute_aggregation_value(
            agg_type,
            target_field,
            eligible_events,
        )
        if not ok:
            return {"success": False, "error": error}

        # 6. Store or update aggregation result
        computed_at = window_info["end_time"]
        self._store_aggregation_result(window_id, metric_name, result_value, computed_at)

        return {
            "success": True,
            "message": f"Aggregation '{agg_type.lower()}' computed for window {window_id} on field '{target_field}'.",
            "data": {
                "window_id": window_id,
                "metric_name": metric_name,
                "result_value": result_value,
                "computed_at": computed_at,
            },
        }

    def add_window(
        self,
        window_id: str,
        stream_id: str,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Create and initialize a new time-bounded window for a given stream.

        Args:
            window_id (str): Unique identifier for the new window.
            stream_id (str): The ID of the stream to attach the window to.
            start_time (float): Unix timestamp representing window start.
            end_time (float): Unix timestamp representing window end.

        Returns:
            dict: {
                "success": True,
                "message": "Window <window_id> created for stream <stream_id> from <start_time> to <end_time>"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., non-unique window_id, stream does not exist, invalid interval)
            }

        Constraints:
            - `window_id` must be unique.
            - `stream_id` must exist.
            - `start_time` < `end_time`.
        """
        # Check window ID uniqueness
        if window_id in self.windows:
            return {"success": False, "error": f"Window ID '{window_id}' already exists."}

        # Check that stream exists
        if stream_id not in self.streams:
            return {"success": False, "error": f"Stream ID '{stream_id}' does not exist."}

        # Valid time interval
        if not (isinstance(start_time, (int, float)) and isinstance(end_time, (int, float))):
            return {"success": False, "error": "Start time and end time must be numeric timestamps."}

        if start_time >= end_time:
            return {"success": False, "error": "Start time must be less than end time."}

        # Add the window
        self.windows[window_id] = {
            "window_id": window_id,
            "stream_id": stream_id,
            "start_time": start_time,
            "end_time": end_time,
            "events": []
        }

        return {
            "success": True,
            "message": f"Window '{window_id}' created for stream '{stream_id}' from {float(start_time)} to {float(end_time)}."
        }

    def expire_old_events(self) -> dict:
        """
        Remove all events from memory/state that no longer fall within any active window for any stream.

        - An event is considered expired if it is not contained (by timestamp and by inclusion in the window's events list)
          within the [start_time, end_time] of any active window.
        - Removes event IDs from windows' 'events' lists if the event no longer fits in their [start_time, end_time].
        - Fully removes events from self.events if they're not referenced from any active window.
        - Idempotent: does nothing if no events are expired.

        Returns:
            dict: {
                "success": True,
                "message": "Old events expired"
            }
        """
        # 1. Remove expired events from each window's 'events' list
        for window in self.windows.values():
            valid_event_ids = []
            for event_id in window['events']:
                event = self.events.get(event_id)
                if event is not None and window['start_time'] <= event['timestamp'] <= window['end_time']:
                    valid_event_ids.append(event_id)
                # else: event is expired for this window and will be removed from the window's event list
            window['events'] = valid_event_ids

        # 2. Remove events no longer referenced by any window
        # Find all event_ids referenced by current windows
        referenced_event_ids = set()
        for window in self.windows.values():
            referenced_event_ids.update(window['events'])

        # All currently stored event IDs
        all_event_ids = set(self.events.keys())
        # Events to delete: no longer referenced
        to_delete_ids = all_event_ids - referenced_event_ids

        for event_id in to_delete_ids:
            del self.events[event_id]

        return {
            "success": True,
            "message": "Old events expired"
        }

    def delete_processing_rule(self, rule_id: str) -> dict:
        """
        Remove a processing rule from a stream.

        Args:
            rule_id (str): Identifier of the processing rule to delete.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Processing rule <rule_id> successfully deleted."
                }
                On failure:
                {
                    "success": False,
                    "error": "Processing rule <rule_id> does not exist."
                }

        Constraints:
            - The rule_id must exist in self.processing_rules.
            - Only removes rule from self.processing_rules; no further clean-up enforced here.
        """
        if rule_id not in self.processing_rules:
            return { "success": False, "error": f"Processing rule {rule_id} does not exist." }

        del self.processing_rules[rule_id]
        return { "success": True, "message": f"Processing rule {rule_id} successfully deleted." }

    def remove_window(self, window_id: str) -> dict:
        """
        Delete an obsolete or completed window and any associated aggregations.

        Args:
            window_id (str): The ID of the window to remove.

        Returns:
            dict:
                - {"success": True, "message": "Window and aggregations removed."}
                - {"success": False, "error": "Window does not exist."}

        Constraints:
            - The window must exist to be removed.
            - Removes both window info and any aggregations related to it.
            - Does NOT delete the actual event objects.
        """
        if window_id not in self.windows:
            return {"success": False, "error": "Window does not exist."}

        del self.windows[window_id]

        if window_id in self.aggregations:
            del self.aggregations[window_id]

        return {
            "success": True, 
            "message": f"Window '{window_id}' and associated aggregations removed."
        }


class StreamProcessingSystem(BaseEnv):
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

    def get_stream_info(self, **kwargs):
        return self._call_inner_tool('get_stream_info', kwargs)

    def list_streams(self, **kwargs):
        return self._call_inner_tool('list_streams', kwargs)

    def get_processing_rule(self, **kwargs):
        return self._call_inner_tool('get_processing_rule', kwargs)

    def list_processing_rules_for_stream(self, **kwargs):
        return self._call_inner_tool('list_processing_rules_for_stream', kwargs)

    def get_events_in_window(self, **kwargs):
        return self._call_inner_tool('get_events_in_window', kwargs)

    def get_events_by_filter(self, **kwargs):
        return self._call_inner_tool('get_events_by_filter', kwargs)

    def get_current_windows_for_stream(self, **kwargs):
        return self._call_inner_tool('get_current_windows_for_stream', kwargs)

    def get_window_info(self, **kwargs):
        return self._call_inner_tool('get_window_info', kwargs)

    def get_aggregation_results(self, **kwargs):
        return self._call_inner_tool('get_aggregation_results', kwargs)

    def event_belongs_to_window(self, **kwargs):
        return self._call_inner_tool('event_belongs_to_window', kwargs)

    def insert_event(self, **kwargs):
        return self._call_inner_tool('insert_event', kwargs)

    def create_processing_rule(self, **kwargs):
        return self._call_inner_tool('create_processing_rule', kwargs)

    def update_processing_rule(self, **kwargs):
        return self._call_inner_tool('update_processing_rule', kwargs)

    def advance_window(self, **kwargs):
        return self._call_inner_tool('advance_window', kwargs)

    def compute_aggregation_for_window(self, **kwargs):
        return self._call_inner_tool('compute_aggregation_for_window', kwargs)

    def add_window(self, **kwargs):
        return self._call_inner_tool('add_window', kwargs)

    def expire_old_events(self, **kwargs):
        return self._call_inner_tool('expire_old_events', kwargs)

    def delete_processing_rule(self, **kwargs):
        return self._call_inner_tool('delete_processing_rule', kwargs)

    def remove_window(self, **kwargs):
        return self._call_inner_tool('remove_window', kwargs)
