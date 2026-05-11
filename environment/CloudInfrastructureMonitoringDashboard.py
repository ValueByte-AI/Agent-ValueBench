# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class CloudServiceInfo(TypedDict):
    service_id: str  # normalized from 'vice_id'
    name: str
    type: str
    status: str
    region: str

class MetricInfo(TypedDict):
    metric_id: str
    name: str
    category: str
    unit: str

class MetricRecordInfo(TypedDict):
    metric_id: str
    service_id: str
    timestamp: float  # can also use int, but float for sub-second precision
    value: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for the cloud infrastructure monitoring dashboard.
        """
        # CloudService entity: {service_id: CloudServiceInfo}
        self.cloud_services: Dict[str, CloudServiceInfo] = {}

        # Metric entity: {metric_id: MetricInfo}
        self.metrics: Dict[str, MetricInfo] = {}

        # MetricRecord entity:
        # Dict[service_id, Dict[metric_id, List[MetricRecordInfo]]]
        # Stores metric readings indexed for efficient time-range queries per service/metric.
        self.metric_records: Dict[str, Dict[str, List[MetricRecordInfo]]] = {}

        # Constraints:
        # - Metric values must be timestamped and associated with both a service and a metric type.
        # - Metric data must be queryable over arbitrary time ranges.
        # - Only active (monitored) cloud services generate new metric records.

    def get_cloud_service_by_name(self, name: str) -> dict:
        """
        Retrieve cloud service metadata and service_id by its name.

        Args:
            name (str): The name of the cloud service to query.

        Returns:
            dict: {
                "success": True,
                "data": CloudServiceInfo  # Metadata including service_id
            }
            or
            {
                "success": False,
                "error": str  # Reason cloud service was not found
            }

        Constraints:
            - Service must exist with the given name.
        """
        for service in self.cloud_services.values():
            if service["name"] == name:
                return { "success": True, "data": service }
        return { "success": False, "error": "Cloud service not found" }

    def list_cloud_services(self) -> dict:
        """
        Returns all registered cloud services and their metadata.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CloudServiceInfo]  # May be empty if no cloud services are present
            }
        """
        services = list(self.cloud_services.values())
        return { "success": True, "data": services }

    def get_service_metrics(self, service_id: str) -> dict:
        """
        Retrieve all metrics (with metadata) associated with a given cloud service.

        Args:
            service_id (str): The cloud service identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[MetricInfo],  # the list of metrics collected/associated with the service.
            }
            or
            {
                "success": False,
                "error": str  # reason, e.g. service does not exist
            }

        Constraints:
            - The specified service_id must exist in cloud_services.
            - Returns all metrics for which there are metric records for the service.
        """
        if service_id not in self.cloud_services:
            return { "success": False, "error": "Service does not exist" }

        # If no records exist for the service, return empty list
        records_by_metric = self.metric_records.get(service_id, {})
        metric_ids = list(records_by_metric.keys())
        metrics_info = [self.metrics[metric_id] for metric_id in metric_ids if metric_id in self.metrics]

        return { "success": True, "data": metrics_info }

    def list_metrics_by_category(self, category: str) -> dict:
        """
        List all metrics (with metadata) filtered by their category.

        Args:
            category (str): The category to filter metrics by (e.g., "scalability", "availability").

        Returns:
            dict: {
                "success": True,
                "data": List[MetricInfo],  # List of metrics in the specified category (could be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Description of error, e.g. "Invalid category"
            }

        Constraints:
            - Category matching is case-sensitive.
        """
        if not isinstance(category, str) or not category:
            return {"success": False, "error": "Invalid or missing category"}

        result = [
            metric_info
            for metric_info in self.metrics.values()
            if metric_info["category"] == category
        ]

        return {"success": True, "data": result}

    def get_metric_by_name_or_id(self, metric_id: str = None, name: str = None) -> dict:
        """
        Retrieve details of a metric by its name or metric_id.
        At least one of metric_id or name must be provided.

        Args:
            metric_id (str, optional): The ID of the metric to retrieve.
            name (str, optional): The name of the metric to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": MetricInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If both metric_id and name are provided, metric_id takes precedence.
            - If metric not found, return error.
        """
        # Priority to ID
        if metric_id is not None:
            if metric_id in self.metrics:
                return { "success": True, "data": self.metrics[metric_id] }
            else:
                return { "success": False, "error": f"Metric with ID '{metric_id}' not found" }
        elif name is not None:
            for metric in self.metrics.values():
                if metric["name"] == name:
                    return { "success": True, "data": metric }
            return { "success": False, "error": f"Metric with name '{name}' not found" }
        else:
            return { "success": False, "error": "Either metric_id or name must be provided" }

    def query_metric_records_time_range(
        self,
        service_id: str,
        metric_id: str,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Retrieve all MetricRecordInfo for the given service_id and metric_id where the
        timestamp is within [start_time, end_time] (inclusive).

        Args:
            service_id (str): The ID of the monitored cloud service.
            metric_id (str): The ID of the metric type.
            start_time (float): Beginning of time range (inclusive).
            end_time (float): End of time range (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[MetricRecordInfo]  # List of matching records (empty if none found)
            }
            or {
                "success": False,
                "error": str  # Description of error encountered
            }

        Constraints:
            - service_id and metric_id must exist.
            - start_time must be <= end_time.
        """
        if service_id not in self.cloud_services:
            return {"success": False, "error": "Service ID does not exist"}
        if metric_id not in self.metrics:
            return {"success": False, "error": "Metric ID does not exist"}
        if start_time > end_time:
            return {"success": False, "error": "start_time cannot be greater than end_time"}
        service_metric_records = self.metric_records.get(service_id, {}).get(metric_id, [])
        filtered_records = [
            record for record in service_metric_records
            if start_time <= record["timestamp"] <= end_time
        ]
        return {"success": True, "data": filtered_records}

    def get_service_status(self, service_id: str) -> dict:
        """
        Query the current status (active/inactive) of a cloud service.

        Args:
            service_id (str): The identifier of the cloud service.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "service_id": str,
                    "status": str  # Status value as stored, e.g. "active", "inactive"
                }
            }
            or {
                "success": False,
                "error": str  # Description of the error: service not found
            }

        Constraints:
            - Service must exist in the monitoring dashboard.
        """
        if service_id not in self.cloud_services:
            return { "success": False, "error": "Cloud service not found" }

        status = self.cloud_services[service_id].get("status", None)
        return { "success": True, "data": {"service_id": service_id, "status": status} }

    def list_metric_records_for_service(
        self,
        service_id: str,
        metric_id: str = None,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Retrieve all metric records for a given service.

        Args:
            service_id (str): ID of the service whose records to fetch.
            metric_id (str, optional): Only include records for this metric (if provided).
            start_time (float, optional): Only include records with timestamp >= start_time.
            end_time (float, optional): Only include records with timestamp <= end_time.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[MetricRecordInfo]}
                - On error:
                    {"success": False, "error": str}

        Constraints:
            - service_id must be valid (exist in cloud_services).
            - Time window must be respected if specified.
        """
        if service_id not in self.cloud_services:
            return {"success": False, "error": "Service not found"}

        # Service may have no metric records
        service_metrics = self.metric_records.get(service_id, {})
        results = []

        metrics_to_check = [metric_id] if metric_id else list(service_metrics.keys())

        for mid in metrics_to_check:
            records = service_metrics.get(mid, [])
            for rec in records:
                ts = rec.get("timestamp")
                if start_time is not None and ts < start_time:
                    continue
                if end_time is not None and ts > end_time:
                    continue
                results.append(rec)

        return {"success": True, "data": results}

    def add_cloud_service(
        self, 
        service_id: str, 
        name: str, 
        type: str, 
        status: str, 
        region: str
    ) -> dict:
        """
        Add a new cloud service to the monitoring dashboard.

        Args:
            service_id (str): Unique identifier for the cloud service.
            name (str): Display name of the cloud service.
            type (str): Service type (e.g., Compute, Storage).
            status (str): Status of the service (e.g., "active", "inactive", etc.).
            region (str): Region/location of the cloud service.

        Returns:
            dict:
                - On success: 
                    { "success": True, "message": "Cloud service <name> added." }
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - service_id must be unique across the environment.
            - All parameters must be supplied and non-empty.
        """
        if not (service_id and name and type and status and region):
            return { "success": False, "error": "All fields must be provided and non-empty." }
        if service_id in self.cloud_services:
            return { "success": False, "error": f"Service ID '{service_id}' already exists." }

        service_info: CloudServiceInfo = {
            "service_id": service_id,
            "name": name,
            "type": type,
            "status": status,
            "region": region
        }
        self.cloud_services[service_id] = service_info

        # Optionally, create an empty slot for metric records for this service
        if service_id not in self.metric_records:
            self.metric_records[service_id] = {}

        return { "success": True, "message": f"Cloud service '{name}' added." }

    def update_cloud_service_status(self, service_id: str, new_status: str) -> dict:
        """
        Change the status of a cloud service (e.g., activate, deactivate monitoring).

        Args:
            service_id (str): The unique identifier of the cloud service to update.
            new_status (str): The new status to assign to the cloud service.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "message": "Cloud service status updated."
                    }
                On failure (e.g., invalid service_id):
                    {
                      "success": False,
                      "error": <str>
                    }

        Constraints:
            - The service must exist in the monitoring dashboard.
            - No assumptions are made about the allowed status values (any string is accepted).
        """
        if service_id not in self.cloud_services:
            return { "success": False, "error": "Cloud service does not exist." }

        self.cloud_services[service_id]['status'] = new_status
        return { "success": True, "message": "Cloud service status updated." }

    def add_metric(
        self,
        metric_id: str,
        name: str,
        category: str,
        unit: str,
    ) -> dict:
        """
        Register a new metric to be collected.

        Args:
            metric_id (str): Unique identifier for the metric.
            name (str): Name of the metric.
            category (str): Category of the metric (e.g., scalability, availability).
            unit (str): Unit of the metric.

        Returns:
            dict:
                - On success: { "success": True, "message": "Metric registered successfully." }
                - On failure: { "success": False, "error": "Reason for failure" }

        Constraints:
            - metric_id must be unique.
            - name must not be empty.
            - All parameters must be non-empty.

        """
        if not all([metric_id, name, category, unit]):
            return { "success": False, "error": "All parameters (metric_id, name, category, unit) are required." }

        if metric_id in self.metrics:
            return { "success": False, "error": f"Metric with id '{metric_id}' already exists." }

        # Optional: Enforce unique metric name (comment out if not desired)
        for m in self.metrics.values():
            if m["name"] == name:
                return { "success": False, "error": f"Metric name '{name}' already exists." }

        # Register the new metric
        self.metrics[metric_id] = {
            "metric_id": metric_id,
            "name": name,
            "category": category,
            "unit": unit
        }

        return { "success": True, "message": "Metric registered successfully." }

    def add_metric_record(
        self,
        service_id: str,
        metric_id: str,
        timestamp: float,
        value: float
    ) -> dict:
        """
        Add a new metric record for a given service and metric type at a specific timestamp.

        Args:
            service_id (str): The ID of the cloud service to associate with this record.
            metric_id (str): The ID of the metric to associate.
            timestamp (float): The measurement time (Unix timestamp, float).
            value (float): The value of the metric.

        Returns:
            dict: {
                "success": True,
                "message": "Metric record added."
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - Service must exist and be active.
            - Metric must exist.
            - Metric record is appended (not unique).
        """
        # Check service exists
        service_info = self.cloud_services.get(service_id)
        if not service_info:
            return {"success": False, "error": f"Service '{service_id}' does not exist."}
        # Check service is active
        if service_info["status"].lower() != "active":
            return {"success": False, "error": f"Service '{service_id}' is not active."}
        # Check metric exists
        metric_info = self.metrics.get(metric_id)
        if not metric_info:
            return {"success": False, "error": f"Metric '{metric_id}' does not exist."}
    
        # Create the metric record
        record: MetricRecordInfo = {
            "service_id": service_id,
            "metric_id": metric_id,
            "timestamp": timestamp,
            "value": value
        }
        if service_id not in self.metric_records:
            self.metric_records[service_id] = {}
        if metric_id not in self.metric_records[service_id]:
            self.metric_records[service_id][metric_id] = []
        self.metric_records[service_id][metric_id].append(record)
        return {"success": True, "message": "Metric record added."}

    def remove_metric_record(self, service_id: str, metric_id: str, timestamp: float) -> dict:
        """
        Delete a specific metric record for a given service, metric, and timestamp.

        Args:
            service_id (str): The cloud service identifier.
            metric_id (str): The metric identifier.
            timestamp (float): The timestamp of the record to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "Metric record removed successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The record must exist under the given service_id and metric_id with the exact timestamp.
        """
        # Check if service exists in metric records
        if service_id not in self.metric_records:
            return { "success": False, "error": "No metric records found for service_id." }

        # Check if metric_id exists for this service_id
        if metric_id not in self.metric_records[service_id]:
            return { "success": False, "error": "No metric records found for metric_id under this service." }

        records = self.metric_records[service_id][metric_id]
        # Find record with exact timestamp
        index = next((i for i, rec in enumerate(records) if rec["timestamp"] == timestamp), None)
        if index is None:
            return { "success": False, "error": "Metric record with given timestamp not found." }

        # Remove the record
        del records[index]

        return { "success": True, "message": "Metric record removed successfully." }

    def remove_cloud_service(self, service_id: str) -> dict:
        """
        Permanently delete the specified cloud service and all associated metric data.

        Args:
            service_id (str): The unique identifier of the cloud service to remove.

        Returns:
            dict: {
                "success": True,
                "message": str  # On successful deletion
            }
            or
            {
                "success": False,
                "error": str  # On failure (e.g., service not found)
            }

        Constraints:
            - If the specified service_id does not exist, an error is returned.
            - All metric records for this service are removed.
        """
        if service_id not in self.cloud_services:
            return { "success": False, "error": "Cloud service not found" }

        # Remove service
        del self.cloud_services[service_id]

        # Remove all metric records for this service (if any exist)
        if service_id in self.metric_records:
            del self.metric_records[service_id]

        return {
            "success": True,
            "message": f"Cloud service {service_id} and all associated metric data removed."
        }


class CloudInfrastructureMonitoringDashboard(BaseEnv):
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

    def get_cloud_service_by_name(self, **kwargs):
        return self._call_inner_tool('get_cloud_service_by_name', kwargs)

    def list_cloud_services(self, **kwargs):
        return self._call_inner_tool('list_cloud_services', kwargs)

    def get_service_metrics(self, **kwargs):
        return self._call_inner_tool('get_service_metrics', kwargs)

    def list_metrics_by_category(self, **kwargs):
        return self._call_inner_tool('list_metrics_by_category', kwargs)

    def get_metric_by_name_or_id(self, **kwargs):
        return self._call_inner_tool('get_metric_by_name_or_id', kwargs)

    def query_metric_records_time_range(self, **kwargs):
        return self._call_inner_tool('query_metric_records_time_range', kwargs)

    def get_service_status(self, **kwargs):
        return self._call_inner_tool('get_service_status', kwargs)

    def list_metric_records_for_service(self, **kwargs):
        return self._call_inner_tool('list_metric_records_for_service', kwargs)

    def add_cloud_service(self, **kwargs):
        return self._call_inner_tool('add_cloud_service', kwargs)

    def update_cloud_service_status(self, **kwargs):
        return self._call_inner_tool('update_cloud_service_status', kwargs)

    def add_metric(self, **kwargs):
        return self._call_inner_tool('add_metric', kwargs)

    def add_metric_record(self, **kwargs):
        return self._call_inner_tool('add_metric_record', kwargs)

    def remove_metric_record(self, **kwargs):
        return self._call_inner_tool('remove_metric_record', kwargs)

    def remove_cloud_service(self, **kwargs):
        return self._call_inner_tool('remove_cloud_service', kwargs)

