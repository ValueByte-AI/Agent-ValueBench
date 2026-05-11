# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import time
from typing import Dict



class MeasurementInfo(TypedDict):
    measurement_id: str
    name: str
    description: str

class DataPointInfo(TypedDict):
    datapoint_id: str
    measurement_id: str
    timestamp: float
    value: float
    tags: Dict[str, str]
    source_id: str

class QueryInfo(TypedDict):
    query_id: str
    query_string: str
    associated_measurements: List[str]
    filters: Dict[str, Any]
    last_run_time: float

class WebhookInfo(TypedDict):
    webhook_id: str
    url: str
    associated_query_ids: List[str]
    status: str
    last_trigger_time: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Simulates a time series database system state.
        Entities:
          - Measurement (measurement_id, name, description)
          - DataPoint (datapoint_id, measurement_id, timestamp, value, tags, source_id)
          - Query (query_id, query_string, associated_measurements, filters, last_run_time)
          - Webhook (webhook_id, url, associated_query_ids, status, last_trigger_time)
        """

        # {measurement_id: MeasurementInfo}
        self.measurements: Dict[str, MeasurementInfo] = {}

        # {datapoint_id: DataPointInfo}
        self.datapoints: Dict[str, DataPointInfo] = {}

        # {query_id: QueryInfo}
        self.queries: Dict[str, QueryInfo] = {}

        # {webhook_id: WebhookInfo}
        self.webhooks: Dict[str, WebhookInfo] = {}

        # Constraints:
        # - Each DataPoint is uniquely timestamped within its Measurement.
        # - Webhooks may only be triggered by successful or relevant query results.
        # - Queries may reference one or more Measurements and may be filtered by time, tags, or other criteria.
        # - Data retrieved for "latest results" must be ordered by timestamp descending and limited to the most recent entries per query.
        # - Values and tags for DataPoints must follow measurement-specific schema (if enforced).

    @staticmethod
    def _coerce_query_condition_value(raw_value: Any) -> Any:
        if isinstance(raw_value, (int, float)):
            return raw_value
        if not isinstance(raw_value, str):
            return raw_value
        text = raw_value.strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            return text[1:-1]
        try:
            return float(text)
        except Exception:
            return text

    def _resolve_datapoint_field_value(self, datapoint: DataPointInfo, field_name: str) -> Any:
        if field_name in datapoint:
            return datapoint[field_name]
        return datapoint.get("tags", {}).get(field_name)

    def _datapoint_matches_field_condition(self, datapoint: DataPointInfo, field_name: str, expected: Any) -> bool:
        actual_value = self._resolve_datapoint_field_value(datapoint, field_name)
        if actual_value is None:
            return False

        if isinstance(expected, str):
            expr = expected.strip()
            match = re.match(r"^(>=|<=|>|<|==|=)\s*(.+)$", expr)
            if match:
                operator, raw_value = match.groups()
                target_value = self._coerce_query_condition_value(raw_value)
                try:
                    actual_num = float(actual_value)
                    target_num = float(target_value)
                except Exception:
                    actual_num = actual_value
                    target_num = target_value
                if operator == ">":
                    return actual_num > target_num
                if operator == ">=":
                    return actual_num >= target_num
                if operator == "<":
                    return actual_num < target_num
                if operator == "<=":
                    return actual_num <= target_num
                return actual_num == target_num
            return str(actual_value) == expr

        return actual_value == expected

    def _extract_query_predicate(self, query_string: str):
        if not isinstance(query_string, str) or not query_string.strip():
            return None
        candidate = query_string.strip()
        where_match = re.search(r"\bWHERE\b\s+(.+)$", candidate, flags=re.IGNORECASE)
        if where_match:
            candidate = where_match.group(1).strip()
        predicate_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(>=|<=|>|<|==|=)\s*(.+?)\s*$", candidate)
        if not predicate_match:
            return None
        field_name, operator, raw_value = predicate_match.groups()
        return field_name, f"{operator}{raw_value}"

    def _evaluate_query_results(
        self,
        *,
        measurement_ids: list[str],
        filters: dict | None = None,
        query_string: str | None = None,
    ) -> list[DataPointInfo]:
        valid_measurements = [m for m in measurement_ids if m in self.measurements]
        if not valid_measurements:
            return []

        filters_to_apply = dict(filters or {})
        candidate_datapoints = [
            dp for dp in self.datapoints.values()
            if dp["measurement_id"] in valid_measurements
        ]

        time_start = filters_to_apply.get("time_start")
        time_end = filters_to_apply.get("time_end")
        tag_filters = filters_to_apply.get("tags") or filters_to_apply.get("tag_filters") or {}
        source_id = filters_to_apply.get("source_id")

        additional_field_filters = {
            key: value
            for key, value in filters_to_apply.items()
            if key not in {"time_start", "time_end", "tags", "tag_filters", "source_id", "measurements", "limit"}
        }

        predicate = self._extract_query_predicate(query_string)

        def matches(dp: DataPointInfo) -> bool:
            if time_start is not None and dp["timestamp"] < time_start:
                return False
            if time_end is not None and dp["timestamp"] > time_end:
                return False
            if source_id is not None and dp["source_id"] != source_id:
                return False
            for tag_key, tag_value in tag_filters.items():
                if dp.get("tags", {}).get(tag_key) != tag_value:
                    return False
            for field_name, expected in additional_field_filters.items():
                if not self._datapoint_matches_field_condition(dp, field_name, expected):
                    return False
            if predicate is not None:
                field_name, expected = predicate
                if not self._datapoint_matches_field_condition(dp, field_name, expected):
                    return False
            return True

        results = [dp for dp in candidate_datapoints if matches(dp)]
        results.sort(key=lambda item: item["timestamp"], reverse=True)
        limit = filters_to_apply.get("limit")
        if isinstance(limit, int) and limit > 0:
            results = results[:limit]
        return results

    def get_measurement_by_name(self, name: str) -> dict:
        """
        Retrieve metadata and ID for a measurement given its name.

        Args:
            name (str): The measurement name to search for.

        Returns:
            dict: 
                - On success: {"success": True, "data": MeasurementInfo}
                - On failure: {"success": False, "error": "Measurement not found"}

        Notes:
            - If multiple measurements share the same name, the first found will be returned.
            - Measurement names are not guaranteed to be unique unless enforced elsewhere.
        """
        for measurement in self.measurements.values():
            if measurement["name"] == name:
                return {"success": True, "data": measurement}
        return {"success": False, "error": "Measurement not found"}

    def get_measurement_by_id(self, measurement_id: str) -> dict:
        """
        Retrieve metadata for a measurement by its unique ID.

        Args:
            measurement_id (str): The unique identifier of the measurement.

        Returns:
            dict: {
                "success": True,
                "data": MeasurementInfo
            } on success,
            or
            {
                "success": False,
                "error": "Measurement not found"
            } if the measurement does not exist.

        Constraints:
            - The measurement_id must exist in the database.
        """
        measurement = self.measurements.get(measurement_id)
        if measurement is None:
            return { "success": False, "error": "Measurement not found" }
        return { "success": True, "data": measurement }

    def list_measurements(self) -> dict:
        """
        Get a list of all measurements registered in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MeasurementInfo]  # All registered measurements (empty list if none)
            }

        Constraints:
            - Returns all MeasurementInfo entries in the system.
        """
        measurements_list = list(self.measurements.values())
        return {"success": True, "data": measurements_list}

    def get_datapoints_by_measurement(
        self,
        measurement_id: str,
        start_time: float = None,
        end_time: float = None,
        tag_filters: Dict[str, str] = None
    ) -> dict:
        """
        Fetch all DataPoints for a given measurement, optionally filtered by:
            - time window (start_time <= timestamp <= end_time)
            - tags (must match all key-value pairs exactly if provided)

        Args:
            measurement_id (str): The measurement ID whose data points are desired.
            start_time (float, optional): If specified, lower bound (inclusive) for timestamps.
            end_time (float, optional): If specified, upper bound (inclusive) for timestamps.
            tag_filters (Dict[str, str], optional): If specified, filters for exact tag key-value matches.

        Returns:
            dict: 
                { "success": True, "data": List[DataPointInfo] }  # May be empty if no matches.
                or 
                { "success": False, "error": str }
        
        Constraints:
            - The specified measurement_id must exist in the database.
            - Tag matching uses exact equality for all provided filters.
        """
        # Check that the measurement exists
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement does not exist" }
    
        result = []
        for dp in self.datapoints.values():
            if dp["measurement_id"] != measurement_id:
                continue
            if start_time is not None and dp["timestamp"] < start_time:
                continue
            if end_time is not None and dp["timestamp"] > end_time:
                continue
            if tag_filters:
                tags_ok = True
                for k, v in tag_filters.items():
                    if k not in dp["tags"] or dp["tags"][k] != v:
                        tags_ok = False
                        break
                if not tags_ok:
                    continue
            result.append(dp)
        return { "success": True, "data": result }

    def get_latest_datapoints_by_measurement(self, measurement_id: str, limit: int = None) -> dict:
        """
        Retrieve the most recent DataPoints for a specific measurement, sorted by timestamp descending.

        Args:
            measurement_id (str): The unique ID of the measurement.
            limit (int, optional): The maximum number of datapoints to return. If None, returns all.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[DataPointInfo], # ordered by timestamp descending; may be empty
                }
                On error: {
                    "success": False,
                    "error": str, # e.g., "Measurement not found"
                }
    
        Constraints:
            - measurement_id must exist in self.measurements
            - Only datapoints belonging to the measurement_id are returned
        """
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement not found" }

        # Select datapoints for this measurement
        datapoints = [
            dp for dp in self.datapoints.values()
            if dp["measurement_id"] == measurement_id
        ]
        # Sort by timestamp, newest first
        datapoints_sorted = sorted(datapoints, key=lambda dp: dp["timestamp"], reverse=True)

        # Apply limit if provided
        if limit is not None:
            datapoints_sorted = datapoints_sorted[:limit]

        return { "success": True, "data": datapoints_sorted }

    def get_query_by_id(self, query_id: str) -> dict:
        """
        Retrieve full details of a query using its query_id.

        Args:
            query_id (str): Unique identifier of the query.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": QueryInfo  # Dictionary of full query details
                }
                On failure (query not found):
                {
                    "success": False,
                    "error": "Query not found"
                }

        Constraints:
            - query_id must exist in the database.
        """
        if query_id not in self.queries:
            return {"success": False, "error": "Query not found"}
        return {"success": True, "data": self.queries[query_id]}

    def list_queries_by_measurement(self, measurement_id: str) -> dict:
        """
        List all queries that reference the given measurement_id.

        Args:
            measurement_id (str): The ID of the measurement to search queries for.

        Returns:
            dict: {
                "success": True,
                "data": List[QueryInfo],  # May be empty if no queries found
            }
            or
            {
                "success": False,
                "error": str  # If the measurement does not exist
            }

        Constraints:
            - The measurement_id must exist in the system.
        """
        if measurement_id not in self.measurements:
            return {"success": False, "error": "Measurement not found"}

        result = [
            query_info for query_info in self.queries.values()
            if measurement_id in query_info.get("associated_measurements", [])
        ]

        return {"success": True, "data": result}

    def list_queries_by_webhook(self, webhook_id: str) -> dict:
        """
        List all QueryInfo dicts associated with the given webhook_id.

        Args:
            webhook_id (str): The identifier of the webhook.

        Returns:
            dict: {
                "success": True,
                "data": List[QueryInfo],  # All currently existing queries for the webhook (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g. 'Webhook not found'
            }

        Constraints:
            - webhook_id must exist in the system.
            - Only currently existing queries are returned.
        """
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return { "success": False, "error": "Webhook not found" }

        associated_query_ids = webhook.get("associated_query_ids", [])
        result = [self.queries[qid] for qid in associated_query_ids if qid in self.queries]

        return { "success": True, "data": result }

    def get_webhook_by_id(self, webhook_id: str) -> dict:
        """
        Retrieve a webhook's configuration using its webhook_id.

        Args:
            webhook_id (str): The unique identifier of the webhook.

        Returns:
            dict: 
                - On success: {"success": True, "data": WebhookInfo}
                - On failure: {"success": False, "error": "Webhook not found"}

        Constraints:
            - webhook_id must exist in the webhooks dictionary.
        """
        webhook = self.webhooks.get(webhook_id)
        if webhook is None:
            return {"success": False, "error": "Webhook not found"}
        return {"success": True, "data": webhook}

    def list_webhooks(self) -> dict:
        """
        List all webhooks and their details currently present in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[WebhookInfo]  # List containing each webhook's info (empty if none exist)
            }
        """
        webhooks_list = list(self.webhooks.values())
        return { "success": True, "data": webhooks_list }

    def run_query(
        self,
        query_id: str = None,
        query_string: str = None,
        filters: dict = None
    ) -> dict:
        """
        Execute a query against the time series database, specified by either stored query_id or provided query_string plus filters.

        Args:
            query_id (str, optional): The ID of a persisted query to execute.
            query_string (str, optional): Ad hoc query string (not actually parsed in this simple implementation).
            filters (dict, optional): Filters to apply if using query_string (e.g., time range, tags).

        Returns:
            dict:
                - On success: { "success": True, "data": List[DataPointInfo] }
                - On error:   { "success": False, "error": str }
        Constraints:
            - Must specify either query_id or query_string, not both.
            - If using query_id, query must exist.
            - Only datapoints in existing measurements will be returned.
            - Filters can include:
                - "time_start": float (optional)
                - "time_end": float (optional)
                - "tags": dict (optional): key-value pairs to match
                - "source_id": str (optional)
        """
        # Validate parameters
        if (query_id is None) == (query_string is None):
            return {"success": False, "error": "Specify exactly one of query_id or query_string."}

        if query_id is not None:
            # Stored query
            if query_id not in self.queries:
                return {"success": False, "error": "Query ID not found."}
            query_info = self.queries[query_id]
            measurements = query_info["associated_measurements"]
            filters_to_apply = query_info.get("filters", {})
            query_string_to_apply = query_info.get("query_string", "")
        else:
            filters_to_apply = dict(filters or {})
            measurements = filters_to_apply.pop("measurements", list(self.measurements.keys()))
            query_string_to_apply = query_string

        result = self._evaluate_query_results(
            measurement_ids=measurements,
            filters=filters_to_apply,
            query_string=query_string_to_apply,
        )
        return {"success": True, "data": result}

    def get_latest_query_results(self, query_id: str) -> dict:
        """
        Retrieve the latest (most recent) result set of DataPoints for a given query, ordered by timestamp descending.

        Args:
            query_id (str): The ID of the query whose latest results to retrieve.

        Returns:
            dict: On success,
                { "success": True, "data": List[DataPointInfo] }
              On failure,
                { "success": False, "error": str }

        Constraints:
            - Results must be filtered by the query's filters and associated_measurements.
            - Results must be sorted by timestamp descending.
        """
        # 1. Query existence check
        if query_id not in self.queries:
            return {"success": False, "error": "Query does not exist"}

        query_info = self.queries[query_id]
        datapoints = self._evaluate_query_results(
            measurement_ids=query_info.get("associated_measurements", []),
            filters=query_info.get("filters", {}),
            query_string=query_info.get("query_string", ""),
        )
        return {"success": True, "data": datapoints}

    def insert_datapoint(
        self,
        datapoint_id: str,
        measurement_id: str,
        timestamp: float,
        value: float,
        tags: Dict[str, str],
        source_id: str
    ) -> dict:
        """
        Add a new DataPoint to a measurement, enforcing unique timestamp constraint per measurement.

        Args:
            datapoint_id (str): Unique identifier for this DataPoint.
            measurement_id (str): The measurement/table to insert into (must exist).
            timestamp (float): Timestamp for the DataPoint (must be unique within measurement).
            value (float): The data value.
            tags (Dict[str, str]): Metadata key-value pairs.
            source_id (str): Source identifier.

        Returns:
            dict: {
              "success": True,
              "message": "DataPoint inserted successfully"
            }
            or
            {
              "success": False,
              "error": <reason>
            }

        Constraints:
            - The measurement_id must exist.
            - Datapoint timestamp must be unique inside its measurement.
            - datapoint_id must not already exist.
        """
        # Check measurement exists
        if measurement_id not in self.measurements:
            return {"success": False, "error": f"Measurement '{measurement_id}' does not exist"}
    
        # Check datapoint_id uniqueness
        if datapoint_id in self.datapoints:
            return {"success": False, "error": f"DataPoint ID '{datapoint_id}' already exists"}

        # Check for timestamp uniqueness in the given measurement
        for dp in self.datapoints.values():
            if dp["measurement_id"] == measurement_id and dp["timestamp"] == timestamp:
                return {
                    "success": False,
                    "error": f"Timestamp {timestamp} already exists in measurement '{measurement_id}'"
                }
    
        # Insert the datapoint
        self.datapoints[datapoint_id] = {
            "datapoint_id": datapoint_id,
            "measurement_id": measurement_id,
            "timestamp": timestamp,
            "value": value,
            "tags": dict(tags),  # copy to avoid accidental mutability
            "source_id": source_id,
        }

        return {"success": True, "message": "DataPoint inserted successfully"}

    def insert_measurement(self, measurement_id: str, name: str, description: str) -> dict:
        """
        Register a new measurement in the system.

        Args:
            measurement_id (str): Unique identifier for the measurement.
            name (str): Human-readable name for the measurement.
            description (str): Measurement description.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Measurement <measurement_id> inserted." }
                - On failure:
                    { "success": False, "error": "..." }

        Constraints:
            - measurement_id must be unique within self.measurements.
            - Does not enforce name uniqueness or other schema.
        """
        if not measurement_id or not name or not description:
            return {"success": False, "error": "measurement_id, name, and description are required."}
        if measurement_id in self.measurements:
            return {"success": False, "error": "Measurement with this ID already exists."}

        self.measurements[measurement_id] = {
            "measurement_id": measurement_id,
            "name": name,
            "description": description
        }
        return {
            "success": True,
            "message": f"Measurement {measurement_id} inserted."
        }

    def insert_query(
        self,
        query_id: str,
        query_string: str,
        associated_measurements: list,
        filters: dict = None,
        last_run_time: float = 0.0
    ) -> dict:
        """
        Add a new query definition to the system.

        Args:
            query_id (str): Unique ID for the query. Must not already exist.
            query_string (str): The query string or logic.
            associated_measurements (List[str]): List of measurement_ids the query references. All must exist.
            filters (Dict[str, Any], optional): Filtering options for the query. Defaults to empty dict.
            last_run_time (float, optional): Initial value; defaults to 0.0.

        Returns:
            dict: {
                "success": True,
                "message": "Query <id> inserted."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Query ID must not already exist.
            - All associated measurement IDs must exist.
            - Filters may be omitted (treated as empty dict).
        """
        # Validate required inputs
        if not isinstance(query_id, str) or not query_id:
            return { "success": False, "error": "Invalid or empty query_id" }
        if not isinstance(query_string, str) or not query_string:
            return { "success": False, "error": "Invalid or empty query_string" }
        if not isinstance(associated_measurements, list):
            return { "success": False, "error": "associated_measurements must be a list of measurement IDs" }

        # Check for query_id uniqueness
        if query_id in self.queries:
            return { "success": False, "error": "Query ID already exists" }

        # Check all measurements exist
        missing = [m for m in associated_measurements if m not in self.measurements]
        if missing:
            return {
                "success": False,
                "error": f"Some measurement IDs do not exist: {missing}"
            }

        # Default filters if not present
        if filters is None:
            filters = {}

        self.queries[query_id] = {
            "query_id": query_id,
            "query_string": query_string,
            "associated_measurements": associated_measurements,
            "filters": filters,
            "last_run_time": last_run_time
        }

        return { "success": True, "message": f"Query {query_id} inserted." }

    def insert_webhook(
        self,
        webhook_id: str,
        url: str,
        associated_query_ids: list,
        status: str = "active",
        last_trigger_time: float = 0.0,
    ) -> dict:
        """
        Register a new webhook and associate it with queries.

        Args:
            webhook_id (str): Unique identifier for the webhook.
            url (str): The webhook's endpoint URL.
            associated_query_ids (List[str]): List of existing query IDs to associate this webhook with.
            status (str): The status for the webhook (default 'active').
            last_trigger_time (float): Timestamp for last trigger (default 0.0).

        Returns:
            dict: {
                "success": True,
                "message": "Webhook registered and associated with queries."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The webhook_id must be unique (not already in self.webhooks).
            - All associated_query_ids must exist in self.queries.
        """
        # Check uniqueness of webhook_id
        if webhook_id in self.webhooks:
            return {"success": False, "error": "Webhook ID already exists."}

        # Check all associated_query_ids exist
        missing_queries = [qid for qid in associated_query_ids if qid not in self.queries]
        if missing_queries:
            return {
                "success": False,
                "error": f"Associated query IDs do not exist: {missing_queries}"
            }

        webhook_info = {
            "webhook_id": webhook_id,
            "url": url,
            "associated_query_ids": associated_query_ids,
            "status": status,
            "last_trigger_time": last_trigger_time
        }
        self.webhooks[webhook_id] = webhook_info

        return {"success": True, "message": "Webhook registered and associated with queries."}

    def update_query_last_run_time(self, query_id: str, last_run_time: float) -> dict:
        """
        Update the last_run_time for the query with the provided query_id.

        Args:
            query_id (str): The unique identifier of the query to update.
            last_run_time (float): The timestamp (Unix epoch) representing the new last_run_time.

        Returns:
            dict: 
                { "success": True, "message": "Query last_run_time updated" }
                or
                { "success": False, "error": "Query not found" }

        Constraints:
            - The query_id must exist in the system.
            - last_run_time should be a float (Unix timestamp).
        """
        if query_id not in self.queries:
            return { "success": False, "error": "Query not found" }

        self.queries[query_id]["last_run_time"] = last_run_time
        return { "success": True, "message": "Query last_run_time updated" }


    def trigger_webhook(self, webhook_id: str) -> dict:
        """
        Attempt to explicitly trigger the webhook if any associated query has a successful/relevant result.
        On success, updates last_trigger_time and status.
    
        Args:
            webhook_id (str): ID of the webhook to trigger.
    
        Returns:
            dict:
                success (bool): True if webhook triggered, False otherwise.
                message (str): Success message, if any.
                error (str): Error message, if any.
    
        Constraints:
            - Webhooks can only be triggered if at least one associated query returns a relevant result (at least one datapoint for its associated measurement(s)).
            - Updates last_trigger_time and webhook status upon success.
        """

        # 1. Check if the webhook exists
        webhook = self.webhooks.get(webhook_id)
        if webhook is None:
            return {"success": False, "error": "Webhook does not exist."}

        if not webhook["associated_query_ids"]:
            return {"success": False, "error": "Webhook has no associated queries."}

        at_least_one_relevant = False

        for query_id in webhook["associated_query_ids"]:
            query = self.queries.get(query_id)
            if query is None:
                continue
            results = self._evaluate_query_results(
                measurement_ids=query.get("associated_measurements", []),
                filters=query.get("filters", {}),
                query_string=query.get("query_string", ""),
            )
            if results:
                at_least_one_relevant = True
                break

        if not at_least_one_relevant:
            return {"success": False, "error": "No associated queries had relevant results; webhook not triggered."}

        # Update webhook status & last_trigger_time
        self.webhooks[webhook_id]["last_trigger_time"] = time.time()
        self.webhooks[webhook_id]["status"] = "triggered"

        return {"success": True, "message": "Webhook triggered and last_trigger_time updated."}

    def update_webhook_status(self, webhook_id: str, status: str) -> dict:
        """
        Change the status of a webhook (e.g., active, inactive, disabled).

        Args:
            webhook_id (str): The unique identifier of the webhook to update.
            status (str): The new status to set (e.g., 'active', 'inactive', 'disabled', etc.).

        Returns:
            dict: 
              - { "success": True, "message": "Webhook status updated." } on success
              - { "success": False, "error": <reason> } on failure

        Constraints:
            - The webhook must exist.
            - Status must be a non-empty string (no schema restrictions specified).
        """
        if webhook_id not in self.webhooks:
            return { "success": False, "error": "Webhook ID does not exist." }
        if not isinstance(status, str) or status.strip() == "":
            return { "success": False, "error": "Status must be a non-empty string." }
        self.webhooks[webhook_id]["status"] = status
        return {"success": True, "message": "Webhook status updated."}

    def delete_datapoint(self, datapoint_id: str) -> dict:
        """
        Remove a datapoint by its unique datapoint_id.

        Args:
            datapoint_id (str): The unique identifier of the datapoint to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Datapoint <datapoint_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Datapoint <datapoint_id> does not exist."
            }

        Constraints:
            - The datapoint_id must exist in the database system.
            - No cascading or measurement-level changes occur.
        """
        if datapoint_id not in self.datapoints:
            return { "success": False, "error": f"Datapoint {datapoint_id} does not exist." }

        del self.datapoints[datapoint_id]
        return { "success": True, "message": f"Datapoint {datapoint_id} deleted." }

    def delete_measurement(self, measurement_id: str) -> dict:
        """
        Remove a measurement and all associated datapoints from the system.

        Args:
            measurement_id (str): Unique identifier for the measurement to remove.

        Returns:
            dict:
                - If successful:
                    {"success": True, "message": "Measurement and associated datapoints deleted."}
                - If measurement_id does not exist:
                    {"success": False, "error": "Measurement does not exist."}

        Constraints:
            - All DataPoints with the specified measurement_id will be removed.
            - Queries or webhooks referencing this measurement are not modified.
        """
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement does not exist." }

        # Remove the measurement
        del self.measurements[measurement_id]

        # Gather and remove all associated datapoints
        removed_datapoints = [
            dp_id for dp_id, dp in self.datapoints.items()
            if dp["measurement_id"] == measurement_id
        ]
        for dp_id in removed_datapoints:
            del self.datapoints[dp_id]

        return {
            "success": True,
            "message": f"Measurement and {len(removed_datapoints)} associated datapoints deleted."
        }

    def delete_query(self, query_id: str) -> dict:
        """
        Remove a persistently saved query by its query_id.

        Args:
            query_id (str): The ID of the query to delete.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Query <query_id> deleted." }
              - On failure: { "success": False, "error": "Query <query_id> does not exist." }

        Constraints:
            - The query must exist.
            - If the query is referenced by any webhooks, it should be removed from their associated_query_ids.
        """
        if query_id not in self.queries:
            return { "success": False, "error": f"Query {query_id} does not exist." }

        # Remove the query
        del self.queries[query_id]

        # Clean up this query ID from any webhooks' associated_query_ids
        for webhook_info in self.webhooks.values():
            if query_id in webhook_info["associated_query_ids"]:
                webhook_info["associated_query_ids"] = [
                    qid for qid in webhook_info["associated_query_ids"] if qid != query_id
                ]

        return { "success": True, "message": f"Query {query_id} deleted." }

    def delete_webhook(self, webhook_id: str) -> dict:
        """
        Remove a webhook from the system by its webhook_id.

        Args:
            webhook_id (str): The unique identifier of the webhook to remove.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Webhook <webhook_id> deleted" }
                - On failure: { "success": False, "error": "Webhook not found" }

        Constraints:
            - The webhook must exist in the system.
        """
        if webhook_id not in self.webhooks:
            return { "success": False, "error": "Webhook not found" }

        del self.webhooks[webhook_id]
        return { "success": True, "message": f"Webhook {webhook_id} deleted" }


class TimeSeriesDatabaseSystem(BaseEnv):
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

    def get_measurement_by_name(self, **kwargs):
        return self._call_inner_tool('get_measurement_by_name', kwargs)

    def get_measurement_by_id(self, **kwargs):
        return self._call_inner_tool('get_measurement_by_id', kwargs)

    def list_measurements(self, **kwargs):
        return self._call_inner_tool('list_measurements', kwargs)

    def get_datapoints_by_measurement(self, **kwargs):
        return self._call_inner_tool('get_datapoints_by_measurement', kwargs)

    def get_latest_datapoints_by_measurement(self, **kwargs):
        return self._call_inner_tool('get_latest_datapoints_by_measurement', kwargs)

    def get_query_by_id(self, **kwargs):
        return self._call_inner_tool('get_query_by_id', kwargs)

    def list_queries_by_measurement(self, **kwargs):
        return self._call_inner_tool('list_queries_by_measurement', kwargs)

    def list_queries_by_webhook(self, **kwargs):
        return self._call_inner_tool('list_queries_by_webhook', kwargs)

    def get_webhook_by_id(self, **kwargs):
        return self._call_inner_tool('get_webhook_by_id', kwargs)

    def list_webhooks(self, **kwargs):
        return self._call_inner_tool('list_webhooks', kwargs)

    def run_query(self, **kwargs):
        return self._call_inner_tool('run_query', kwargs)

    def get_latest_query_results(self, **kwargs):
        return self._call_inner_tool('get_latest_query_results', kwargs)

    def insert_datapoint(self, **kwargs):
        return self._call_inner_tool('insert_datapoint', kwargs)

    def insert_measurement(self, **kwargs):
        return self._call_inner_tool('insert_measurement', kwargs)

    def insert_query(self, **kwargs):
        return self._call_inner_tool('insert_query', kwargs)

    def insert_webhook(self, **kwargs):
        return self._call_inner_tool('insert_webhook', kwargs)

    def update_query_last_run_time(self, **kwargs):
        return self._call_inner_tool('update_query_last_run_time', kwargs)

    def trigger_webhook(self, **kwargs):
        return self._call_inner_tool('trigger_webhook', kwargs)

    def update_webhook_status(self, **kwargs):
        return self._call_inner_tool('update_webhook_status', kwargs)

    def delete_datapoint(self, **kwargs):
        return self._call_inner_tool('delete_datapoint', kwargs)

    def delete_measurement(self, **kwargs):
        return self._call_inner_tool('delete_measurement', kwargs)

    def delete_query(self, **kwargs):
        return self._call_inner_tool('delete_query', kwargs)

    def delete_webhook(self, **kwargs):
        return self._call_inner_tool('delete_webhook', kwargs)
