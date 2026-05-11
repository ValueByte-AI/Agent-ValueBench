# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Union



class WebServiceInfo(TypedDict):
    # Represents entity: WebService
    service_id: str
    name: str
    description: str
    metadata: Dict[str, str]
    operational_status: str  # Must be one of {"operational", "degraded", "down", "unknown"}
    health_metrics: Dict[str, Union[str, float]]
    last_checked_time: Union[float, str]  # Accepts timestamp or ISO-formatted date string

class _GeneratedEnvImpl:
    def __init__(self):
        # Registered web services: {service_id: WebServiceInfo}
        self.web_services: Dict[str, WebServiceInfo] = {}

        # Constraints:
        # - service_id must be unique across all web services
        # - operational_status is restricted to a defined set (e.g., "operational", "degraded", "down", "unknown")
        # - metadata and health_metrics should be updatable based on monitoring/reporting
        # - only registered web services can be queried or updated

    def get_service_by_id(self, service_id: str) -> dict:
        """
        Retrieve the full information (status, description, metadata, metrics, etc.) of a web service
        given its unique service_id.

        Args:
            service_id (str): The unique identifier for the web service.

        Returns:
            dict: 
                { "success": True, "data": WebServiceInfo } on success,
                { "success": False, "error": str } if service_id does not exist.

        Constraints:
            - Only registered web services can be queried.
        """
        service_info = self.web_services.get(service_id)
        if service_info is None:
            return { "success": False, "error": "Service ID not found" }
        return { "success": True, "data": service_info }

    def list_all_services(self) -> dict:
        """
        Retrieve a list of all registered web services with their full information.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[WebServiceInfo]  # List of registered web services, possibly empty
            }

        Notes:
            - If no web services are registered, returns an empty list in 'data'.
            - No error should occur in normal operation.
        """
        data = list(self.web_services.values())
        return {"success": True, "data": data}

    def get_operational_status(self, service_id: str) -> dict:
        """
        Query the current operational_status of a web service by service_id.

        Args:
            service_id (str): The unique identifier for the web service.

        Returns:
            dict: 
                - If success: { "success": True, "data": str }
                      where data is the operational status (e.g., "operational")
                - If failure: { "success": False, "error": str }
                      describing why the operation failed (e.g., service not registered)

        Constraints:
            - The queried service_id must be registered (exist in the registry).
        """
        if service_id not in self.web_services:
            return { "success": False, "error": "Service ID not registered" }

        status = self.web_services[service_id]["operational_status"]
        return { "success": True, "data": status }

    def get_health_metrics(self, service_id: str) -> dict:
        """
        Retrieve the current health metrics for a registered web service.

        Args:
            service_id (str): The unique ID of the web service.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": Dict[str, Union[str, float]]  # The health_metrics field
                    }
                On failure (service not found):
                    {
                        "success": False,
                        "error": "Service not found"
                    }

        Constraints:
            - Only registered services can be queried.
        """
        service = self.web_services.get(service_id)
        if not service:
            return { "success": False, "error": "Service not found" }
        return { "success": True, "data": service["health_metrics"] }

    def get_metadata(self, service_id: str) -> dict:
        """
        Retrieve the metadata dictionary for the web service specified by service_id.

        Args:
            service_id (str): Unique identifier of the web service.

        Returns:
            dict:
              - success: True, data: metadata dictionary (possibly empty) if service found
              - success: False, error: description if service is not registered

        Constraints:
            - Only registered web services can be queried by service_id.
        """
        service = self.web_services.get(service_id)
        if service is None:
            return { "success": False, "error": "Service not registered" }
        return { "success": True, "data": service.get("metadata", {}) }

    def get_last_checked_time(self, service_id: str) -> dict:
        """
        Retrieve the last_checked_time for the given web service.

        Args:
            service_id (str): The unique identifier for the web service.

        Returns:
            dict: {
                "success": True,
                "data": last_checked_time (float or str: timestamp or ISO date),
            }
            or
            {
                "success": False,
                "error": str  # Reason why last_checked_time could not be retrieved.
            }

        Constraints:
            - Service must be registered (service_id exists in the system).
        """
        service = self.web_services.get(service_id)
        if not service:
            return { "success": False, "error": "Service not found" }

        # Defensive: ensure field exists
        last_checked_time = service.get("last_checked_time", None)
        if last_checked_time is None:
            return { "success": False, "error": "No last_checked_time available for this service" }

        return { "success": True, "data": last_checked_time }

    def is_service_registered(self, service_id: str) -> dict:
        """
        Check whether the provided service_id corresponds to a registered web service.

        Args:
            service_id (str): The unique identifier for the web service.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "registered": bool  # True if registered, False otherwise
                }
            }

        Constraints:
            - service_id must be compared against registered web services.
            - This query does not expose service details.
        """
        registered = service_id in self.web_services
        return {
            "success": True,
            "data": {
                "registered": registered
            }
        }

    def register_web_service(
        self,
        service_id: str,
        name: str,
        description: str,
        metadata: Dict[str, str],
        operational_status: str,
        health_metrics: Dict[str, 'Union[str, float]'],
        last_checked_time: 'Union[float, str]'
    ) -> dict:
        """
        Register a new web service with a unique service_id and initial attributes.

        Args:
            service_id (str): Unique identifier for the web service.
            name (str): Name of the web service.
            description (str): Description of the web service.
            metadata (Dict[str, str]): Metadata key-value pairs for the service.
            operational_status (str): Service status; must be one of {"operational", "degraded", "down", "unknown"}.
            health_metrics (Dict[str, Union[str, float]]): Health metric values.
            last_checked_time (float or str): Timestamp or ISO-formatted string for last check.

        Returns:
            dict: On success -> { "success": True, "message": "Web service registered successfully." }
                  On failure -> { "success": False, "error": <reason> }

        Constraints:
            - service_id must be unique (cannot already exist).
            - operational_status must be one of the defined valid statuses.
        """
        allowed_statuses = {"operational", "degraded", "down", "unknown"}

        if service_id in self.web_services:
            return { "success": False, "error": "A service with this ID already exists." }

        if operational_status not in allowed_statuses:
            return { "success": False, "error": "Invalid operational_status value." }

        self.web_services[service_id] = {
            "service_id": service_id,
            "name": name,
            "description": description,
            "metadata": metadata,
            "operational_status": operational_status,
            "health_metrics": health_metrics,
            "last_checked_time": last_checked_time
        }
        return { "success": True, "message": "Web service registered successfully." }

    def unregister_web_service(self, service_id: str) -> dict:
        """
        Remove (unregister) a web service from the registry by service_id.

        Args:
            service_id (str): The unique identifier of the web service to remove.

        Returns:
            dict:
                - On success: {"success": True, "message": "Web service '<service_id>' unregistered successfully."}
                - On failure: {"success": False, "error": "Web service '<service_id>' is not registered."}

        Constraints:
            - Only registered web services can be unregistered.
            - No exception is raised; always returns success/error dictionary.
        """
        if service_id not in self.web_services:
            return { "success": False, "error": f"Web service '{service_id}' is not registered." }
        del self.web_services[service_id]
        return { "success": True, "message": f"Web service '{service_id}' unregistered successfully." }

    def update_operational_status(self, service_id: str, operational_status: str) -> dict:
        """
        Modify the operational_status field of a registered web service.

        Args:
            service_id (str): Unique identifier of the web service.
            operational_status (str): The new operational status to set.
                Must be one of: {"operational", "degraded", "down", "unknown"}.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Operational status updated."}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Only registered web services can be updated.
            - operational_status must be an allowed value.
        """
        allowed_statuses = {"operational", "degraded", "down", "unknown"}

        if service_id not in self.web_services:
            return { "success": False, "error": "Service not found" }

        if operational_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid operational_status. Allowed values: {', '.join(allowed_statuses)}" }

        self.web_services[service_id]["operational_status"] = operational_status
        return { "success": True, "message": "Operational status updated." }

    def update_health_metrics(self, service_id: str, new_health_metrics: Dict[str, 'Union[str, float]']) -> dict:
        """
        Update the health_metrics dictionary for a registered web service.

        Args:
            service_id (str): Unique identifier of the web service.
            new_health_metrics (Dict[str, Union[str, float]]): 
                The new health metrics to set (will replace the old dict).

        Returns:
            dict: {
                "success": True,
                "message": "Health metrics updated for service <service_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only registered web services (existing service_id) can be updated.
            - health_metrics will be replaced (not partially merged).
        """
        if service_id not in self.web_services:
            return {"success": False, "error": f"Service ID '{service_id}' is not registered."}
        if not isinstance(new_health_metrics, dict):
            return {"success": False, "error": "new_health_metrics must be a dictionary."}

        self.web_services[service_id]['health_metrics'] = new_health_metrics
        return {
            "success": True,
            "message": f"Health metrics updated for service '{service_id}'."
        }

    def update_metadata(self, service_id: str, metadata: Dict[str, str]) -> dict:
        """
        Update (merge) the metadata dictionary for a given web service.

        Args:
            service_id (str): Unique identifier of the web service.
            metadata (Dict[str, str]): Metadata to update (string keys and values). Existing keys will be overwritten.

        Returns:
            dict: {
                "success": True,
                "message": "Metadata updated for service <service_id>"
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Only registered web services can be updated.
            - Metadata dictionary keys and values must be strings.
        """
        ws = self.web_services.get(service_id)
        if ws is None:
            return {"success": False, "error": f"Service with id {service_id} not found"}

        # Input validation: ensure all keys and values are strings
        if not isinstance(metadata, dict):
            return {"success": False, "error": "Provided metadata must be a dictionary"}
        for k, v in metadata.items():
            if not isinstance(k, str) or not isinstance(v, str):
                return {"success": False, "error": "All metadata keys and values must be strings"}

        ws["metadata"].update(metadata)
        return {"success": True, "message": f"Metadata updated for service {service_id}"}

    def update_last_checked_time(self, service_id: str, last_checked_time: 'float|str') -> dict:
        """
        Set or update the last_checked_time for a registered web service.

        Args:
            service_id (str): Unique identifier of the web service to update.
            last_checked_time (float or str): The new timestamp. Can be a Unix timestamp (float)
                or ISO-formatted date string.

        Returns:
            dict: {
                "success": True,
                "message": "last_checked_time updated for service {service_id}"
            }
            or
            {
                "success": False,
                "error": Error description
            }

        Constraints:
            - Only registered web services can be updated.
            - last_checked_time should be float or str (timestamp or ISO string).
        """
        if service_id not in self.web_services:
            return {"success": False, "error": "Service not registered"}

        if not isinstance(last_checked_time, (float, str)):
            return {
                "success": False,
                "error": "last_checked_time must be float (timestamp) or ISO string"
            }

        self.web_services[service_id]['last_checked_time'] = last_checked_time
        return {
            "success": True,
            "message": f"last_checked_time updated for service {service_id}"
        }

    def update_service_info(self, service_id: str, name: str = None, description: str = None) -> dict:
        """
        Update the 'name' and/or 'description' fields for a registered web service.
        Only 'name' and 'description' are mutable via this call, all other fields
        are ignored.

        Args:
            service_id (str): The unique ID of the web service to update.
            name (str, optional): New name for the service.
            description (str, optional): New description for the service.

        Returns:
            dict: {
                "success": True,
                "message": "Fields updated for service <service_id>"
            } on success, OR:
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only registered web services can be updated.
            - At least one mutable field ('name' or 'description') must be provided.
            - Other fields will be ignored.
        """
        if service_id not in self.web_services:
            return { "success": False, "error": "Service not registered" }
    
        if name is None and description is None:
            return { 
                "success": False, 
                "error": "No fields to update; provide at least 'name' or 'description'" 
            }
    
        updated_fields = []
        if name is not None:
            self.web_services[service_id]['name'] = name
            updated_fields.append('name')
        if description is not None:
            self.web_services[service_id]['description'] = description
            updated_fields.append('description')
    
        if updated_fields:
            upd_str = ", ".join(updated_fields)
            return {
                "success": True,
                "message": f"Fields updated for service {service_id}: {upd_str}"
            }
        # (Should not get here — caught by earlier logic)
        return { "success": False, "error": "No valid fields provided to update" }


class WebServiceMonitoringRegistry(BaseEnv):
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

    def get_service_by_id(self, **kwargs):
        return self._call_inner_tool('get_service_by_id', kwargs)

    def list_all_services(self, **kwargs):
        return self._call_inner_tool('list_all_services', kwargs)

    def get_operational_status(self, **kwargs):
        return self._call_inner_tool('get_operational_status', kwargs)

    def get_health_metrics(self, **kwargs):
        return self._call_inner_tool('get_health_metrics', kwargs)

    def get_metadata(self, **kwargs):
        return self._call_inner_tool('get_metadata', kwargs)

    def get_last_checked_time(self, **kwargs):
        return self._call_inner_tool('get_last_checked_time', kwargs)

    def is_service_registered(self, **kwargs):
        return self._call_inner_tool('is_service_registered', kwargs)

    def register_web_service(self, **kwargs):
        return self._call_inner_tool('register_web_service', kwargs)

    def unregister_web_service(self, **kwargs):
        return self._call_inner_tool('unregister_web_service', kwargs)

    def update_operational_status(self, **kwargs):
        return self._call_inner_tool('update_operational_status', kwargs)

    def update_health_metrics(self, **kwargs):
        return self._call_inner_tool('update_health_metrics', kwargs)

    def update_metadata(self, **kwargs):
        return self._call_inner_tool('update_metadata', kwargs)

    def update_last_checked_time(self, **kwargs):
        return self._call_inner_tool('update_last_checked_time', kwargs)

    def update_service_info(self, **kwargs):
        return self._call_inner_tool('update_service_info', kwargs)

