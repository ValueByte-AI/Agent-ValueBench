# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ServerInfo(TypedDict):
    server_id: str
    hostname: str
    ip_address: str
    location: str
    operational_status: str

class PerformanceMetricInfo(TypedDict):
    server_id: str
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float

class ServiceInfo(TypedDict):
    service_id: str
    server_id: str
    service_name: str
    status: str

class AlertThresholdInfo(TypedDict):
    server_id: str
    metric_type: str
    threshold_value: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for tracking operational health and metrics of servers.
        """

        # Servers: {server_id: ServerInfo}
        self.servers: Dict[str, ServerInfo] = {}

        # Performance metrics: {server_id: [PerformanceMetricInfo, ...]}
        self.performance_metrics: Dict[str, List[PerformanceMetricInfo]] = {}

        # Services: {service_id: ServiceInfo}
        self.services: Dict[str, ServiceInfo] = {}

        # Alert Thresholds: {server_id: {metric_type: AlertThresholdInfo}}
        self.alert_thresholds: Dict[str, Dict[str, AlertThresholdInfo]] = {}

        # Constraints:
        # - Each server must have at least one associated performance metric entry.
        # - Service status must be up-to-date for accurate health reporting.
        # - Operational status of a server is determined from recent performance metrics and service health.
        # - Alert thresholds are enforced when metrics exceed defined values (alerts generated).

    def get_server_by_hostname(self, hostname: str) -> dict:
        """
        Retrieve server info by hostname.

        Args:
            hostname (str): The hostname to search for.

        Returns:
            dict: On success:
                    {
                        "success": True,
                        "data": ServerInfo  # Info of the matching server
                    }
                  On failure:
                    {
                        "success": False,
                        "error": "Server with the specified hostname does not exist"
                    }

        Constraints:
            - Hostname must match exactly with an existing server.
            - Returns the first match found (hostnames should be unique).
        """
        for server_info in self.servers.values():
            if server_info["hostname"] == hostname:
                return { "success": True, "data": server_info }
        return { "success": False, "error": "Server with the specified hostname does not exist" }

    def get_server_info(self, server_id: str) -> dict:
        """
        Retrieve all static and current information about a server given its server_id.

        Args:
            server_id (str): The unique ID of the server.

        Returns:
            dict: {
                "success": True,
                "data": ServerInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - server_id must exist in the system.
        """
        if server_id not in self.servers:
            return { "success": False, "error": "Server not found" }

        return { "success": True, "data": self.servers[server_id] }

    def get_latest_performance_metric(self, server_id: str) -> dict:
        """
        Retrieve the most recent performance metric record for a server.

        Args:
            server_id (str): The unique identifier of the server.

        Returns:
            dict: 
                - On success: {"success": True, "data": PerformanceMetricInfo}
                - On failure: {"success": False, "error": str}

        Constraints:
            - The server must exist.
            - There must be at least one performance metric entry for the server.
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server does not exist."}
    
        metrics = self.performance_metrics.get(server_id)
        if not metrics or len(metrics) == 0:
            return {"success": False, "error": "No performance metrics found for the server."}
    
        # Find the metric record with the latest timestamp
        latest_metric = max(metrics, key=lambda rec: rec["timestamp"])
        return {"success": True, "data": latest_metric}

    def get_all_performance_metrics(self, server_id: str) -> dict:
        """
        Get historical list of all performance metrics for a specified server.

        Args:
            server_id (str): Unique identifier for the target server.

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceMetricInfo]   # all metrics for the server; may be empty
            }
            or
            {
                "success": False,
                "error": str    # reason for failure (e.g., server not found)
            }

        Constraints:
            - The server_id must correspond to an existing server.
            - Each server is expected to have at least one performance metric,
              but if not, this returns an empty list for data.
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server not found"}

        metrics = self.performance_metrics.get(server_id, [])
        return {"success": True, "data": metrics}

    def get_services_by_server(self, server_id: str) -> dict:
        """
        List all services and their current status for a given server.

        Args:
            server_id (str): The unique ID of the server whose services are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ServiceInfo],  # List may be empty if no services
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Server not found"
            }

        Constraints:
            - The server_id must exist in the registered servers.
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server not found"}

        services = [
            service_info for service_info in self.services.values()
            if service_info["server_id"] == server_id
        ]

        return {"success": True, "data": services}

    def get_service_status(self, service_id: str = None, service_name: str = None) -> dict:
        """
        Get the status (e.g., up/down) of a particular service by its ID or name.

        Args:
            service_id (str, optional): Unique identifier of the service. Takes precedence if provided.
            service_name (str, optional): Name of the service (not necessarily unique across servers).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": <ServiceInfo>  # Full service info including status
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for error (not found, ambiguous, etc.)
                    }

        Constraints:
            - If multiple services share the name, the operation is ambiguous and fails.
            - At least one of service_id or service_name must be provided.
        """
        # Must provide at least one identifier
        if not service_id and not service_name:
            return {"success": False, "error": "Must provide service_id or service_name."}

        if service_id:
            # Lookup by service_id
            service = self.services.get(service_id)
            if not service:
                return {"success": False, "error": f"No service found with service_id '{service_id}'."}
            return {"success": True, "data": service}

        # Lookup by name (may be ambiguous)
        matching_services = [s for s in self.services.values() if s["service_name"] == service_name]
        if not matching_services:
            return {"success": False, "error": f"No service found with service_name '{service_name}'."}
        if len(matching_services) > 1:
            return {"success": False, "error": f"Multiple services found with service_name '{service_name}'. Please use service_id for disambiguation."}

        # Exactly one match
        return {"success": True, "data": matching_services[0]}

    def get_operational_status(self, server_id: str) -> dict:
        """
        Retrieve the computed operational status for the specified server, derived from its most recent performance metrics and service health.

        Args:
            server_id (str): The unique identifier of the server.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "server_id": <str>,
                            "operational_status": <str>,
                            "latest_metric": <PerformanceMetricInfo | None>,
                            "service_statuses": [<dict: {service_id, service_name, status}>, ...]
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - The server must exist.
            - The server must have at least one performance metric entry.
        """
        # Check server existence
        if server_id not in self.servers:
            return {"success": False, "error": "Server does not exist"}

        # Check for at least one performance metric
        metrics = self.performance_metrics.get(server_id)
        if not metrics or len(metrics) == 0:
            return {"success": False, "error": "No performance metrics for the server"}

        # Find the latest performance metric
        latest_metric = max(metrics, key=lambda m: m["timestamp"])

        # Gather all service statuses for this server
        service_statuses = [
            {
                "service_id": svc["service_id"],
                "service_name": svc["service_name"],
                "status": svc["status"]
            }
            for svc in self.services.values()
            if svc["server_id"] == server_id
        ]

        # Get current operational status
        operational_status = self.servers[server_id].get("operational_status", "unknown")

        return {
            "success": True,
            "data": {
                "server_id": server_id,
                "operational_status": operational_status,
                "latest_metric": latest_metric,
                "service_statuses": service_statuses
            }
        }

    def get_alert_thresholds_for_server(self, server_id: str) -> dict:
        """
        List all alert thresholds configured for a server.

        Args:
            server_id (str): The unique identifier of the server.

        Returns:
            dict: {
                "success": True,
                "data": List[AlertThresholdInfo],  # Empty list if no thresholds configured
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., server does not exist
            }

        Constraints:
            - The server_id must correspond to an existing server.
            - Returns all AlertThresholdInfo objects for the server, or an empty list if none.
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server does not exist"}

        # Fetch alert thresholds dictionary for the server, default to empty
        thresholds_dict = self.alert_thresholds.get(server_id, {})
        result = list(thresholds_dict.values())

        return {"success": True, "data": result}

    def check_alerts_for_server(self, server_id: str) -> dict:
        """
        Compare the most recent performance metrics with alert thresholds for a given server.
        Returns a list of active alerts (where current metric exceeds threshold).

        Args:
            server_id (str): ID of the server to check for alerts.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict: {
                    "metric_type": str,
                    "actual_value": float,
                    "threshold_value": float,
                    "timestamp": float
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The server must exist and have at least one performance metric entry.
            - No alert if no thresholds configured or all metrics below/equal threshold.
        """

        if server_id not in self.servers:
            return { "success": False, "error": "Server does not exist" }

        metrics = self.performance_metrics.get(server_id, [])
        if not metrics:
            return { "success": False, "error": "No performance metrics for server" }

        # Get most recent metric by timestamp
        latest_metric = max(metrics, key=lambda x: x["timestamp"])

        server_thresholds = self.alert_thresholds.get(server_id, {})
        if not server_thresholds:
            # No thresholds -> no alerts
            return { "success": True, "data": [] }

        metric_types = ["cpu_usage", "memory_usage", "disk_usage", "network_usage"]

        alerts = []
        for metric_type in metric_types:
            threshold_info = server_thresholds.get(metric_type)
            if not threshold_info:
                continue  # No threshold set for this metric

            threshold_value = threshold_info["threshold_value"]
            actual_value = latest_metric.get(metric_type)
            if actual_value is None:
                continue  # Metric missing in the latest entry, skip

            if actual_value > threshold_value:
                alerts.append({
                    "metric_type": metric_type,
                    "actual_value": actual_value,
                    "threshold_value": threshold_value,
                    "timestamp": latest_metric["timestamp"]
                })

        return { "success": True, "data": alerts }

    def update_service_status(self, service_id: str, status: str) -> dict:
        """
        Change or edit the operational status of a service running on a server.

        Args:
            service_id (str): The unique identifier of the service to update.
            status (str): The new status to set for the service (e.g., "running", "stopped", "failed", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Service status updated"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., service not found
            }

        Constraints:
            - The service must exist in the monitoring system.
            - Assumes no restriction on allowed 'status' values unless otherwise specified.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service ID not found" }
    
        self.services[service_id]["status"] = status
        return { "success": True, "message": "Service status updated" }

    def add_performance_metric(
        self,
        server_id: str,
        timestamp: float,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        network_usage: float
    ) -> dict:
        """
        Add a new performance metric record for a specified server.

        Args:
            server_id (str): The identifier of the server.
            timestamp (float): Unix timestamp of the metric record.
            cpu_usage (float): CPU usage percentage or value.
            memory_usage (float): Memory usage percentage or value.
            disk_usage (float): Disk usage percentage or value.
            network_usage (float): Network usage metric.

        Returns:
            dict: 
                On success: { "success": True, "message": "Performance metric added for server <server_id>." }
                On failure: { "success": False, "error": str }

        Constraints:
            - The server must exist in the system.
            - There is no check for duplicate timestamp or metric values.
            - Does not raise exceptions; returns error dict on failure.
        """
        if server_id not in self.servers:
            return {"success": False, "error": f"Server ID {server_id} does not exist."}

        metric: PerformanceMetricInfo = {
            "server_id": server_id,
            "timestamp": timestamp,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_usage": network_usage
        }
        if server_id not in self.performance_metrics:
            self.performance_metrics[server_id] = []
        self.performance_metrics[server_id].append(metric)
        return {"success": True, "message": f"Performance metric added for server {server_id}."}

    def set_alert_threshold(
        self,
        server_id: str,
        metric_type: str,
        threshold_value: float
    ) -> dict:
        """
        Configure or update the threshold for a server's specific performance metric.

        Args:
            server_id (str): Target server identifier.
            metric_type (str): One of ['cpu_usage', 'memory_usage', 'disk_usage', 'network_usage'].
            threshold_value (float): Non-negative threshold value.

        Returns:
            dict: {
                "success": True,
                "message": Threshold set or updated successfully.
            }
            or
            {
                "success": False,
                "error": Error message if input or operation is invalid.
            }

        Constraints:
            - server_id must exist.
            - metric_type must be valid.
            - threshold_value must be non-negative.
        """
        valid_metrics = {"cpu_usage", "memory_usage", "disk_usage", "network_usage"}

        if server_id not in self.servers:
            return {"success": False, "error": "Server does not exist."}

        if metric_type not in valid_metrics:
            return {"success": False, "error": f"Invalid metric_type: {metric_type}."}

        if not isinstance(threshold_value, (int, float)) or threshold_value < 0:
            return {"success": False, "error": "Threshold value must be a non-negative number."}

        if server_id not in self.alert_thresholds:
            self.alert_thresholds[server_id] = {}

        self.alert_thresholds[server_id][metric_type] = {
            "server_id": server_id,
            "metric_type": metric_type,
            "threshold_value": float(threshold_value)
        }

        return {
            "success": True,
            "message": f"Alert threshold for {metric_type} on server {server_id} set to {threshold_value}."
        }

    def set_operational_status(self, server_id: str, operational_status: str) -> dict:
        """
        Directly updates the operational status of the given server, if allowed.
    
        Args:
            server_id (str): The identifier of the server.
            operational_status (str): The new operational status to set (manual override).
        
        Returns:
            dict: {
                "success": True,
                "message": "Operational status updated." 
            } on success,
            or
            {
                "success": False,
                "error": <reason>,
            } on failure.
        
        Constraints:
            - Server must exist in the environment.
            - Operational status should be a non-empty string.
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server not found."}
    
        if not isinstance(operational_status, str) or not operational_status.strip():
            return {"success": False, "error": "Invalid operational status value."}
    
        self.servers[server_id]["operational_status"] = operational_status.strip()
        return {"success": True, "message": f"Operational status for server '{server_id}' updated to '{operational_status.strip()}'."}

    def refresh_service_status(self, server_id: str) -> dict:
        """
        Force refresh (simulate polling) of all services on a given server for up-to-date health reporting.

        Args:
            server_id (str): The ID of the server whose services should be polled/refreshed.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Service statuses refreshed for server <server_id>"}
                On failure:
                    {"success": False, "error": "reason"}
        Constraints:
            - Server must exist in self.servers.
            - The operation ensures that service statuses are current (simulated here).
        """
        if server_id not in self.servers:
            return {"success": False, "error": "Server does not exist"}

        # Find all service_ids for this server
        refreshed_count = 0
        for service in self.services.values():
            if service["server_id"] == server_id:
                # Simulate polling (in a real system, update status here)
                # For demo: set status to itself (no actual hardware to poll)
                service["status"] = service["status"]
                refreshed_count += 1

        if refreshed_count == 0:
            return {
                "success": True,
                "message": f"No services to refresh on server {server_id} (operation succeeded)"
            }
        else:
            return {
                "success": True,
                "message": f"Service statuses refreshed for server {server_id}"
            }


class ServerMonitoringSystem(BaseEnv):
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

    def get_server_by_hostname(self, **kwargs):
        return self._call_inner_tool('get_server_by_hostname', kwargs)

    def get_server_info(self, **kwargs):
        return self._call_inner_tool('get_server_info', kwargs)

    def get_latest_performance_metric(self, **kwargs):
        return self._call_inner_tool('get_latest_performance_metric', kwargs)

    def get_all_performance_metrics(self, **kwargs):
        return self._call_inner_tool('get_all_performance_metrics', kwargs)

    def get_services_by_server(self, **kwargs):
        return self._call_inner_tool('get_services_by_server', kwargs)

    def get_service_status(self, **kwargs):
        return self._call_inner_tool('get_service_status', kwargs)

    def get_operational_status(self, **kwargs):
        return self._call_inner_tool('get_operational_status', kwargs)

    def get_alert_thresholds_for_server(self, **kwargs):
        return self._call_inner_tool('get_alert_thresholds_for_server', kwargs)

    def check_alerts_for_server(self, **kwargs):
        return self._call_inner_tool('check_alerts_for_server', kwargs)

    def update_service_status(self, **kwargs):
        return self._call_inner_tool('update_service_status', kwargs)

    def add_performance_metric(self, **kwargs):
        return self._call_inner_tool('add_performance_metric', kwargs)

    def set_alert_threshold(self, **kwargs):
        return self._call_inner_tool('set_alert_threshold', kwargs)

    def set_operational_status(self, **kwargs):
        return self._call_inner_tool('set_operational_status', kwargs)

    def refresh_service_status(self, **kwargs):
        return self._call_inner_tool('refresh_service_status', kwargs)

