# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime



class DeploymentMetadataInfo(TypedDict):
    version: str
    build_date: str
    git_commit_hash: str
    environment: str
    release_no: str

class ServiceInfo(TypedDict):
    service_id: str
    name: str
    operational_status: str
    last_health_check_timestamp: str  # ISO timestamp string
    deployment_metadata: DeploymentMetadataInfo

class HealthCheckResultInfo(TypedDict):
    service_id: str
    check_timestamp: str  # ISO timestamp string
    status: str
    detail: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Services: {service_id: ServiceInfo}
        # Maps each microservice instance by id to its metadata and health.
        self.services: Dict[str, ServiceInfo] = {}

        # Health check history: {service_id: [HealthCheckResultInfo, ...]}
        self.health_checks: Dict[str, List[HealthCheckResultInfo]] = {}

        # Constraints:
        # - Each service must accurately expose its current operational status and deployment metadata via designated endpoints.
        # - Health status reports must be up-to-date to support reliable diagnostics.
        # - Deployment metadata must be consistent with the actual software running on each service instance.
        # - Only authorized users or systems can retrieve sensitive metadata or health status details.

    def get_service_by_name(self, name: str) -> dict:
        """
        Fetch the service entity and metadata using the service's name.

        Args:
            name (str): The name of the service to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ServiceInfo,  # Full metadata for the found service
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Service not found"
                    }
        Constraints:
            - This function assumes service names are unique or returns the first match if multiple exist.
        """
        for service_info in self.services.values():
            if service_info["name"] == name:
                return { "success": True, "data": service_info }
        return { "success": False, "error": "Service not found" }

    def get_service_by_id(self, service_id: str) -> dict:
        """
        Fetch the service entity and associated deployment metadata using its unique service_id.
    
        Args:
            service_id (str): Unique identifier for the service.
    
        Returns:
            dict: 
              - If found: { "success": True, "data": ServiceInfo }
              - If not found: { "success": False, "error": "Service not found" }
    
        Constraints:
            - service_id must exist in the environment.
        """
        service = self.services.get(service_id)
        if service is None:
            return { "success": False, "error": "Service not found" }
        return { "success": True, "data": service }

    def list_all_services(self) -> dict:
        """
        List all registered microservices in the backend environment.

        Returns:
            dict: {
                "success": True,
                "data": List[ServiceInfo]   # List of service metadata objects. Empty list if no services.
            }
        """
        # Gather all ServiceInfo entries
        services_list = list(self.services.values())
        return { "success": True, "data": services_list }

    def get_service_operational_status(self, service_id: str) -> dict:
        """
        Retrieve the current operational status (e.g., 'up', 'degraded', 'down') of a given service.

        Args:
            service_id (str): The unique identifier of the target service.

        Returns:
            dict: {
                "success": True,
                "data": str  # The operational status string of the service
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. service not found
            }

        Constraints:
            - The service_id must reference an existing service.
            - The operational status returned should accurately reflect the current state in the service metadata.
        """
        service = self.services.get(service_id)
        if not service:
            return {"success": False, "error": "Service not found"}

        return {"success": True, "data": service["operational_status"]}

    def get_service_deployment_metadata(self, service_id: str) -> dict:
        """
        Retrieve deployment metadata (version, build date, git commit hash, environment, release number)
        for a specific service.

        Args:
            service_id (str): Unique identifier of the service.

        Returns:
            dict: 
                { "success": True, "data": DeploymentMetadataInfo }
                or
                { "success": False, "error": "Service not found" }

        Constraints:
            - The given service must exist in the backend.
            - If the service is not found, returns an error dict.
        """
        service = self.services.get(service_id)
        if not service:
            return { "success": False, "error": "Service not found" }

        return { "success": True, "data": service["deployment_metadata"] }

    def get_service_health_check_history(self, service_id: str) -> dict:
        """
        Retrieve the historical log of health check results for a given service.

        Args:
            service_id (str): The ID of the service to retrieve the health check history for.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[HealthCheckResultInfo],  # List of health check records (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # Reason why the operation failed (e.g., service does not exist)
                    }

        Constraints:
            - service_id must correspond to an existing service.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service does not exist" }

        history = self.health_checks.get(service_id, [])
        return { "success": True, "data": history }

    def get_latest_health_check_result(self, service_id: str) -> dict:
        """
        Fetch the most recent health check result for a given service.

        Args:
            service_id (str): The unique identifier of the service.

        Returns:
            dict: {
                "success": True,
                "data": HealthCheckResultInfo  # The most recent health check result
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The service should exist in the system.
            - There must be at least one health check result for the service.
        """
        if service_id not in self.services:
            return {"success": False, "error": "Service does not exist."}

        if service_id not in self.health_checks or not self.health_checks[service_id]:
            return {"success": False, "error": "No health check records found for this service."}

        # Find the result with the latest check_timestamp
        # Timestamps are in ISO string, lexicographical order is sufficient.
        latest_result = max(
            self.health_checks[service_id],
            key=lambda record: record["check_timestamp"]
        )

        return {"success": True, "data": latest_result}

    def get_health_check_detail_by_timestamp(self, service_id: str, check_timestamp: str) -> dict:
        """
        Retrieve the full detail of a health check result for a specific service at a particular timestamp.

        Args:
            service_id (str): The unique identifier of the service.
            check_timestamp (str): The ISO timestamp string of the health check to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": HealthCheckResultInfo  # The details of the requested health check result.
            }
            or
            {
                "success": False,
                "error": str  # Description of the failure: service or the requested check not found.
            }

        Constraints:
            - The provided service_id must exist.
            - The specified health check timestamp must exist in that service's health check history.
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service not found" }

        history = self.health_checks.get(service_id, [])
        for result in history:
            if result["check_timestamp"] == check_timestamp:
                return { "success": True, "data": result }

        return { "success": False, "error": "Health check at specified timestamp not found" }

    def check_metadata_consistency(self) -> dict:
        """
        Verify if the current service deployment metadata matches the actual running deployment for all services.
        This is a diagnostic/audit operation.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]: [
                    {
                        "service_id": str,
                        "is_consistent": bool,
                        "discrepancy": dict (optional, only if inconsistent)
                    },
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If no services are present, success with empty list.
            - This mock simply asserts stored deployment_metadata is "actual".
        """

        actual_store = getattr(self, "_actual_deployment_metadata", None)
        if isinstance(actual_store, str):
            try:
                actual_store = json.loads(actual_store)
            except Exception:
                actual_store = None
        if actual_store is not None and not isinstance(actual_store, dict):
            actual_store = None

        results = []
        for service_id, service_info in self.services.items():
            deployment_metadata = service_info["deployment_metadata"]
            actual_metadata = actual_store.get(service_id) if actual_store is not None else deployment_metadata.copy()
            is_consistent = deployment_metadata == actual_metadata
            discrepancy = {}
            if not is_consistent:
                discrepancy = {
                    "expected": {**deployment_metadata},
                    "actual": {**actual_metadata}
                }
        
            result = {
                "service_id": service_id,
                "is_consistent": is_consistent
            }
            if not is_consistent:
                result["discrepancy"] = discrepancy

            results.append(result)
    
        return { "success": True, "data": results }


    def trigger_health_check(self, service_id: str) -> dict:
        """
        Initiate an on-demand health check on a specified service; result is logged and service status is updated if needed.

        Args:
            service_id (str): The unique identifier of the service to health-check.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Operation description.
            }
            or
            {
                "success": False,
                "error": str,  # Description of error (e.g., service not found).
            }

        Constraints:
            - The service must exist.
            - Health check result is appended to health_checks history.
            - Service's last_health_check_timestamp is updated.
            - Service's operational_status may be updated to reflect latest check.
        """
        # Verify service exists
        if service_id not in self.services:
            return { "success": False, "error": "Service not found." }

        # Simulate health check (for demo: always "healthy")
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        status = "healthy"
        detail = "Automated health check passed."

        # Create new health check result entry
        health_check = {
            "service_id": service_id,
            "check_timestamp": now_iso,
            "status": status,
            "detail": detail,
        }

        # Append health check entry
        if service_id not in self.health_checks:
            self.health_checks[service_id] = []
        self.health_checks[service_id].append(health_check)

        # Update service's last_health_check_timestamp and potentially operational status
        self.services[service_id]["last_health_check_timestamp"] = now_iso
        self.services[service_id]["operational_status"] = status

        return {
            "success": True,
            "message": f"Health check triggered for service {service_id}."
        }

    def update_service_operational_status(
        self,
        service_id: str,
        new_status: str,
        requester_identity: str
    ) -> dict:
        """
        Change the operational status of a service, with proper validation and authorization.

        Args:
            service_id (str): The unique ID of the service.
            new_status (str): The new operational status to set.
            requester_identity (str): User or system requesting the change (for authorization).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Service status updated." }
                On failure:
                    { "success": False, "error": <reason str> }

        Constraints:
            - Only authorized users/systems can update service status.
            - Service must exist.
            - Status must be a valid option.
        """
        # Accept a few common operator-facing aliases and normalize them
        # to the internal status vocabulary used elsewhere in the environment.
        status_aliases = {
            "operational": "healthy",
        }
        normalized_status = status_aliases.get(new_status, new_status)

        # Define valid statuses
        valid_statuses = {"up", "healthy", "degraded", "down", "maintenance", "restricted"}

        # Example simple authorization check: only "admin" or "system" roles allowed
        authorized_identities = {"admin", "system"}

        # Check service existence
        if service_id not in self.services:
            return {"success": False, "error": "Service not found."}

        # Validate new_status
        if normalized_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'."}

        # Authorization check
        if requester_identity not in authorized_identities:
            return {"success": False, "error": "Unauthorized to update service status."}

        # Perform the update
        self.services[service_id]["operational_status"] = normalized_status

        return {"success": True, "message": "Service status updated."}

    def update_service_deployment_metadata(self, service_id: str, new_deployment_metadata: dict) -> dict:
        """
        Replace or modify the deployment metadata for a specified service.

        Args:
            service_id (str): ID of the target service instance.
            new_deployment_metadata (dict): New deployment metadata to set. Must contain:
                - version (str)
                - build_date (str)
                - git_commit_hash (str)
                - environment (str)
                - release_no (str)

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Deployment metadata updated for service <service_id>."}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - Service with the given service_id must exist.
            - All required deployment_metadata fields must be present.
            - Only authorized users/systems can invoke this operation (not enforced here).
        """
        # Check if service exists
        if service_id not in self.services:
            return {"success": False, "error": "Service not found."}

        required_fields = {"version", "build_date", "git_commit_hash", "environment", "release_no"}
        if not isinstance(new_deployment_metadata, dict):
            return {"success": False, "error": "Deployment metadata must be provided as a dict."}
        if not required_fields.issubset(set(new_deployment_metadata.keys())):
            missing = required_fields - set(new_deployment_metadata.keys())
            return {"success": False, "error": f"Missing required fields in deployment metadata: {', '.join(missing)}"}

        # Update service metadata
        self.services[service_id]["deployment_metadata"] = {
            "version": str(new_deployment_metadata["version"]),
            "build_date": str(new_deployment_metadata["build_date"]),
            "git_commit_hash": str(new_deployment_metadata["git_commit_hash"]),
            "environment": str(new_deployment_metadata["environment"]),
            "release_no": str(new_deployment_metadata["release_no"])
        }

        return {"success": True, "message": f"Deployment metadata updated for service {service_id}."}

    def delete_health_check_record(self, service_id: str, check_timestamps: list) -> dict:
        """
        Remove specific entries from a service's health check history.

        Args:
            service_id (str): ID of the service whose health check records to delete.
            check_timestamps (List[str]): List of ISO-formatted timestamps for records to remove.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "message": "Deleted X health check records for service 'Y'. Not found: [...]"
                    }
                - On partial success:
                    {
                      "success": True,
                      "message": "Deleted X health check records for service 'Y'. Not found: [...]"
                    }
                - On failure (e.g. service not found or no records present):
                    {
                      "success": False,
                      "error": "Reason for failure"
                    }

        Constraints:
            - The service must exist.
            - Only the requested timestamps for which records exist will be deleted.
            - If none matched, report as such (success: False).
        """
        if service_id not in self.services:
            return {"success": False, "error": f"Service '{service_id}' does not exist."}

        if service_id not in self.health_checks or not self.health_checks[service_id]:
            return {"success": False, "error": f"No health check records found for service '{service_id}'."}

        to_delete = set(check_timestamps)
        before_count = len(self.health_checks[service_id])

        # Partition records:
        remaining_records = []
        deleted_timestamps = []
        for rec in self.health_checks[service_id]:
            if rec["check_timestamp"] in to_delete:
                deleted_timestamps.append(rec["check_timestamp"])
            else:
                remaining_records.append(rec)

        # Update the health_check history for the service
        self.health_checks[service_id] = remaining_records

        deleted_count = len(deleted_timestamps)
        not_found = list(to_delete - set(deleted_timestamps))

        if deleted_count == 0:
            return {
                "success": False,
                "error": f"No matching health check records found for the given timestamps for service '{service_id}'."
            }

        msg = f"Deleted {deleted_count} health check record(s) for service '{service_id}'."
        if not_found:
            msg += f" Not found: {not_found}"

        return {
            "success": True,
            "message": msg
        }

    def force_metadata_consistency_sync(self) -> dict:
        """
        Force-synchronize the recorded deployment metadata with the actual running deployment metadata
        for all services in the backend. If recorded metadata for a service differs from the actual, it
        will be updated to match the actual state.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Description of how many services were synchronized (with reporting of any missing actual metadata)
                "updated_services": List[str],  # List of service_ids that were patched
                "missing_actual_metadata": List[str],  # service_ids for which actual metadata was not available (if any)
            }
            or
            {
                "success": False,
                "error": str  # Description of fatal/infrastructure error
            }

        Constraints:
            - The operation sets deployment_metadata per service to match the actual state,
              assuming self._actual_deployment_metadata is available per service_id.
            - If a service is missing actual metadata, it will be reported but not block others.
        """
        # Simulated store of actual deployment metadata (should be initialized elsewhere)
        if not hasattr(self, '_actual_deployment_metadata'):
            return { "success": False, "error": "Actual deployment metadata store not available on this backend instance." }
        actual_store = self._actual_deployment_metadata
        if isinstance(actual_store, str):
            try:
                actual_store = json.loads(actual_store)
            except Exception:
                return { "success": False, "error": "Actual deployment metadata store is malformed." }
        if not isinstance(actual_store, dict):
            return { "success": False, "error": "Actual deployment metadata store must be a mapping." }

        if not self.services:
            return { "success": True, "message": "No services present for synchronization.", "updated_services": [], "missing_actual_metadata": [] }

        updated_services = []
        missing_actual_metadata = []

        for service_id, service_info in self.services.items():
            # Does actual metadata exist for this service?
            actual_metadata = actual_store.get(service_id)
            if actual_metadata is None:
                missing_actual_metadata.append(service_id)
                continue

            # Compare recorded vs actual metadata
            if service_info["deployment_metadata"] != actual_metadata:
                # Replace recorded metadata with actual
                service_info["deployment_metadata"] = actual_metadata.copy()
                updated_services.append(service_id)
            # else: already in sync, no action

        message = f"Synchronization complete: {len(updated_services)} service(s) updated."
        if missing_actual_metadata:
            message += f" {len(missing_actual_metadata)} service(s) missing actual metadata, not synchronized."

        return {
            "success": True,
            "message": message,
            "updated_services": updated_services,
            "missing_actual_metadata": missing_actual_metadata,
        }


class WebServiceBackend(BaseEnv):
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
            if key == "_actual_deployment_metadata" and isinstance(value, str):
                try:
                    value = json.loads(value)
                except Exception:
                    pass
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

    def get_service_by_name(self, **kwargs):
        return self._call_inner_tool('get_service_by_name', kwargs)

    def get_service_by_id(self, **kwargs):
        return self._call_inner_tool('get_service_by_id', kwargs)

    def list_all_services(self, **kwargs):
        return self._call_inner_tool('list_all_services', kwargs)

    def get_service_operational_status(self, **kwargs):
        return self._call_inner_tool('get_service_operational_status', kwargs)

    def get_service_deployment_metadata(self, **kwargs):
        return self._call_inner_tool('get_service_deployment_metadata', kwargs)

    def get_service_health_check_history(self, **kwargs):
        return self._call_inner_tool('get_service_health_check_history', kwargs)

    def get_latest_health_check_result(self, **kwargs):
        return self._call_inner_tool('get_latest_health_check_result', kwargs)

    def get_health_check_detail_by_timestamp(self, **kwargs):
        return self._call_inner_tool('get_health_check_detail_by_timestamp', kwargs)

    def check_metadata_consistency(self, **kwargs):
        return self._call_inner_tool('check_metadata_consistency', kwargs)

    def trigger_health_check(self, **kwargs):
        return self._call_inner_tool('trigger_health_check', kwargs)

    def update_service_operational_status(self, **kwargs):
        return self._call_inner_tool('update_service_operational_status', kwargs)

    def update_service_deployment_metadata(self, **kwargs):
        return self._call_inner_tool('update_service_deployment_metadata', kwargs)

    def delete_health_check_record(self, **kwargs):
        return self._call_inner_tool('delete_health_check_record', kwargs)

    def force_metadata_consistency_sync(self, **kwargs):
        return self._call_inner_tool('force_metadata_consistency_sync', kwargs)
