# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class RoadInfo(TypedDict):
    road_id: str
    name: str
    type: str
    status: str

class TrafficAlertInfo(TypedDict):
    alert_id: str
    road_id: str
    severity_level: str      # Must be one of: "low", "moderate", "high", "critical"
    alert_type: str
    timestamp: float         # Unix epoch time
    description: str
    active_status: bool      # True = current/active

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a Traffic Management System.
        """

        # Roads: {road_id: RoadInfo}
        # Road entity: road_id, name, type, status
        self.roads: Dict[str, RoadInfo] = {}

        # Alerts: {alert_id: TrafficAlertInfo}
        # TrafficAlert entity: alert_id, road_id (foreign key), severity_level, alert_type, timestamp, description, active_status
        self.alerts: Dict[str, TrafficAlertInfo] = {}

        # Constraints:
        # - Each TrafficAlert must be linked to a valid Road (road_id foreign key).
        # - Only alerts with active_status = True are current/active.
        # - severity_level must be {"low", "moderate", "high", "critical"} (ordered for prioritization).
        # - A road can have multiple overlapping alerts.
        # - Alert timestamps must be accurate and match system time requirements if filtering by recency.


    def list_all_roads(self) -> dict:
        """
        Retrieve all roads in the road network, including their identifiers and statuses.

        Returns:
            dict: {
                "success": True,
                "data": List[RoadInfo]  # List of road info dicts (may be empty if no roads in the network)
            }

        Constraints:
            - No input parameters.
            - No error cases, returns an empty list if there are no roads.
        """
        roads = list(self.roads.values())
        return {"success": True, "data": roads}

    def get_road_by_id(self, road_id: str) -> dict:
        """
        Retrieve detailed information about a specific road by road_id.

        Args:
            road_id (str): Unique identifier for the road.

        Returns:
            dict: {
                "success": True,
                "data": RoadInfo  # The road's information
            }
            OR
            {
                "success": False,
                "error": "Road not found"
            }

        Constraints:
            - road_id must exist in the system.
        """
        road_info = self.roads.get(road_id)
        if road_info is not None:
            return {"success": True, "data": road_info}
        else:
            return {"success": False, "error": "Road not found"}

    def list_all_alerts(self) -> dict:
        """
        Retrieve the complete list of all traffic alerts in the system, regardless of active_status.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TrafficAlertInfo]   # List of all traffic alerts (may be empty if no alerts exist)
            }
        """
        alerts_list = list(self.alerts.values())
        return {"success": True, "data": alerts_list}

    def list_active_alerts(self) -> dict:
        """
        Retrieve a list of all currently active (active_status=True) traffic alerts.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TrafficAlertInfo],  # All traffic alert infos where active_status == True
            }
            If none found, data will be an empty list.
        """
        active_alerts = [
            alert_info for alert_info in self.alerts.values()
            if alert_info["active_status"] is True
        ]
        return { "success": True, "data": active_alerts }

    def get_alert_by_id(self, alert_id: str) -> dict:
        """
        Retrieve full information for a specific traffic alert given its alert_id.

        Args:
            alert_id (str): The unique identifier of the traffic alert.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": TrafficAlertInfo
                }
                or
                {
                    "success": False,
                    "error": "Alert not found"
                }

        Constraints:
            - The alert must exist in the system (self.alerts).
        """
        alert = self.alerts.get(alert_id)
        if alert is None:
            return { "success": False, "error": "Alert not found" }

        return { "success": True, "data": alert }

    def get_alerts_for_road(self, road_id: str, active_only: bool = False) -> dict:
        """
        Retrieve a list of all alerts associated with a specific road.
    
        Args:
            road_id (str): The identifier of the road.
            active_only (bool, optional): If True, only include alerts which are currently active.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TrafficAlertInfo],  # All matching alerts (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # e.g. "Road ID not found"
                    }

        Constraints:
            - road_id must exist in the system.
            - If active_only, only include alerts where active_status==True.
        """
        if road_id not in self.roads:
            return { "success": False, "error": "Road ID not found" }

        alerts = [
            alert for alert in self.alerts.values()
            if alert["road_id"] == road_id and (not active_only or alert["active_status"])
        ]

        return { "success": True, "data": alerts }

    def get_active_alerts_for_road(self, road_id: str) -> dict:
        """
        Retrieve all currently active alerts (TrafficAlertInfo) for a given road_id.

        Args:
            road_id (str): The unique identifier of the road whose alerts are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[TrafficAlertInfo]  # Zero or more active alerts for this road
            }
            OR
            {
                "success": False,
                "error": str                     # Reason: e.g. road_id does not exist
            }

        Constraints:
            - The specified road_id must exist in the system.
            - Only active alerts (active_status == True) are returned.
        """
        if road_id not in self.roads:
            return {
                "success": False,
                "error": "Road ID does not exist."
            }

        result = [
            alert for alert in self.alerts.values()
            if alert["road_id"] == road_id and alert["active_status"] is True
        ]

        return {
            "success": True,
            "data": result
        }

    def get_roads_with_active_alerts(self) -> dict:
        """
        Returns all roads (as RoadInfo) that have one or more active alerts associated with them.
        Each road appears only once, even if it has multiple active alerts.

        Returns:
            dict: {
                "success": True,
                "data": List[RoadInfo],  # Roads with at least one active alert (may be empty)
            }

        Constraints:
            - Only alerts with active_status=True are considered.
            - Each TrafficAlert must be linked to a valid Road; skip alerts referencing missing roads.
            - Each road is listed at most once.
        """
        # Collect road_ids with at least one active alert
        active_road_ids = set(
            alert["road_id"]
            for alert in self.alerts.values()
            if alert["active_status"] is True
        )

        # Build list of RoadInfo (only for road_ids present in self.roads)
        roads_with_alerts = [
            self.roads[road_id]
            for road_id in active_road_ids
            if road_id in self.roads
        ]

        return {
            "success": True,
            "data": roads_with_alerts
        }

    def get_max_severity_for_road(self, road_id: str) -> dict:
        """
        For a given road, return the highest severity level present among its current active alerts.

        Args:
            road_id (str): Identifier of the target road.

        Returns:
            dict:
                On success: { "success": True, "data": str or None }
                    - "data" is the highest severity level as a string, or None if no active alerts.
                On failure: { "success": False, "error": str }

        Constraints:
            - Only alerts with active_status == True are considered.
            - Road must exist in the network.
            - Severity ordering: "low" < "moderate" < "high" < "critical"
        """
        severity_order = ["low", "moderate", "high", "critical"]

        if road_id not in self.roads:
            return { "success": False, "error": "Road does not exist" }

        active_alerts = [
            alert for alert in self.alerts.values()
            if alert["road_id"] == road_id and alert["active_status"] is True
        ]

        if not active_alerts:
            return { "success": True, "data": None }

        highest_severity = max(
            (alert["severity_level"] for alert in active_alerts),
            key=lambda sev: severity_order.index(sev)
        )

        return { "success": True, "data": highest_severity }

    def get_severity_ordering(self) -> dict:
        """
        Return the allowed set of severity levels with their prioritization ordering.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Ordered from lowest to highest priority
            }
        Constraints:
            - Severity levels and their order: ["low", "moderate", "high", "critical"]
        """
        severity_ordering = ["low", "moderate", "high", "critical"]
        return {
            "success": True,
            "data": severity_ordering
        }

    def get_ordered_roads_by_alert_severity(self) -> dict:
        """
        Returns a list of all roads that currently have at least one active alert,
        ordered by the highest alert severity assigned to that road (from critical to low).

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "road_info": RoadInfo,
                    "max_severity_level": str,  # One of: "critical", "high", "moderate", "low"
                }]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only current (active_status=True) alerts are considered.
            - Severity levels are ordered: low < moderate < high < critical.
            - Each returned road must exist in self.roads and have at least one active alert.
        """
        # Define severity ordering
        severity_order = {
            "low": 0,
            "moderate": 1,
            "high": 2,
            "critical": 3
        }
        # {road_id: [alert_severity_levels]}
        road_to_severities = {}

        # Collect active alerts by road
        for alert in self.alerts.values():
            if alert.get("active_status") is True:
                road_id = alert.get("road_id")
                severity_level = alert.get("severity_level")
                # Only consider valid severities and roads
                if road_id in self.roads and severity_level in severity_order:
                    road_to_severities.setdefault(road_id, []).append(severity_level)

        # Create result list with max severity for each road
        result = []
        for road_id, severities in road_to_severities.items():
            # Find the highest severity level for this road
            max_severity = max(severities, key=lambda s: severity_order[s])
            result.append({
                "road_info": self.roads[road_id],
                "max_severity_level": max_severity
            })

        # Sort the roads by max severity (critical first)
        result.sort(key=lambda x: severity_order[x["max_severity_level"]], reverse=True)

        return {"success": True, "data": result}

    def get_alerts_by_severity(
        self, 
        severity_level: str, 
        road_id: str = None, 
        active_status: bool = None
    ) -> dict:
        """
        Retrieve all alerts with the specified severity level.
        Optionally filter by road and/or alert activity status.
    
        Args:
            severity_level (str): One of "low", "moderate", "high", "critical"
            road_id (str, optional): Road ID to restrict results to.
            active_status (bool, optional): If specified, True to filter for active alerts, False for inactive.
        
        Returns:
            dict: {
                "success": True,
                "data": List[TrafficAlertInfo]  # list of matching alerts
            }
            or
            {
                "success": False,
                "error": str
            }
        
        Constraints:
            - severity_level must be valid.
            - If road_id is given, must be in self.roads.
        """
        valid_levels = {"low", "moderate", "high", "critical"}
        if severity_level not in valid_levels:
            return { "success": False, "error": "Invalid severity_level" }
        if road_id is not None and road_id not in self.roads:
            return { "success": False, "error": "Invalid road_id" }
    
        alerts = []
        for alert in self.alerts.values():
            if alert["severity_level"] != severity_level:
                continue
            if road_id is not None and alert["road_id"] != road_id:
                continue
            if active_status is not None and alert["active_status"] != active_status:
                continue
            alerts.append(alert)
    
        return { "success": True, "data": alerts }

    def create_road(self, road_id: str, name: str, type: str, status: str) -> dict:
        """
        Add a new road to the road network.

        Args:
            road_id (str): Unique identifier for the road.
            name (str): Name of the road.
            type (str): Type of road (e.g., highway, street).
            status (str): Operational status of the road.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Road <road_id> created successfully." }
                - On error: { "success": False, "error": "reason" }

        Constraints:
            - road_id must be unique (must not exist in self.roads).
            - All parameters must be provided.
        """
        if not all([road_id, name, type, status]):
            return { "success": False, "error": "All parameters must be provided and non-empty." }

        if road_id in self.roads:
            return { "success": False, "error": f"Road with id '{road_id}' already exists." }

        road_info = {
            "road_id": road_id,
            "name": name,
            "type": type,
            "status": status
        }
        self.roads[road_id] = road_info
        return { "success": True, "message": f"Road {road_id} created successfully." }

    def update_road_status(self, road_id: str, updates: dict) -> dict:
        """
        Update the operational status or attributes of a given road.

        Args:
            road_id (str): The identifier of the road to be updated.
            updates (dict): Key-value pairs of fields to update. Allowed keys: "status", "name", "type".

        Returns:
            dict:
                Success: { "success": True, "message": "Road <road_id> updated successfully." }
                Failure:
                    - { "success": False, "error": "Road not found." }
                    - { "success": False, "error": "Invalid attribute(s): ..." }
                    - { "success": False, "error": "No valid update field provided." }

        Constraints:
            - Road (road_id) must already exist.
            - Only 'status', 'name', and 'type' fields can be updated.
            - 'road_id' cannot be changed.
        """
        if road_id not in self.roads:
            return {"success": False, "error": "Road not found."}

        allowed_fields = {"status", "name", "type"}
        invalid_fields = [k for k in updates.keys() if k not in allowed_fields]
        if invalid_fields:
            return {"success": False, "error": f"Invalid attribute(s): {', '.join(invalid_fields)}"}

        # Filter to only allowed fields (should be unnecessary due to check above)
        updated_any = False
        for key in allowed_fields:
            if key in updates:
                self.roads[road_id][key] = updates[key]
                updated_any = True

        if not updated_any:
            return {"success": False, "error": "No valid update field provided."}

        return {"success": True, "message": f"Road {road_id} updated successfully."}

    def create_traffic_alert(
        self,
        alert_id: str,
        road_id: str,
        severity_level: str,
        alert_type: str,
        timestamp: float,
        description: str,
        active_status: bool
    ) -> dict:
        """
        Add a new traffic alert associated with a given road.

        Args:
            alert_id (str): Unique identifier for the alert.
            road_id (str): Identifier for the road this alert is associated with. Must exist.
            severity_level (str): One of {"low", "moderate", "high", "critical"}.
            alert_type (str): The type/category of alert (e.g., "accident", "closure").
            timestamp (float): Unix epoch time indicating when the alert was created.
            description (str): Description of the alert.
            active_status (bool): Whether the alert is currently active.

        Returns:
            dict: {
                "success": True,
                "message": "Traffic alert created."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - alert_id must be unique.
            - road_id must exist in the road network.
            - severity_level must be among allowed set.
        """
        # Constraint: alert_id uniqueness
        if alert_id in self.alerts:
            return { "success": False, "error": "Alert ID already exists" }

        # Constraint: road_id must be valid
        if road_id not in self.roads:
            return { "success": False, "error": "Invalid road_id (road does not exist)" }

        # Constraint: Valid severity_level
        valid_severity = {"low", "moderate", "high", "critical"}
        if severity_level not in valid_severity:
            return { "success": False, "error": "Invalid severity_level" }

        # Insert new alert
        self.alerts[alert_id] = {
            "alert_id": alert_id,
            "road_id": road_id,
            "severity_level": severity_level,
            "alert_type": alert_type,
            "timestamp": timestamp,
            "description": description,
            "active_status": active_status
        }
        return { "success": True, "message": "Traffic alert created." }

    def update_traffic_alert(
        self,
        alert_id: str,
        severity_level: str = None,
        alert_type: str = None,
        timestamp: float = None,
        description: str = None,
        active_status: bool = None,
        road_id: str = None
    ) -> dict:
        """
        Modify attributes of an existing traffic alert.

        Args:
            alert_id (str): Identifier for the alert to update.
            severity_level (str, optional): New severity ("low", "moderate", "high", "critical").
            alert_type (str, optional): New alert type.
            timestamp (float, optional): New timestamp (Unix epoch).
            description (str, optional): New description.
            active_status (bool, optional): New active status.
            road_id (str, optional): New road_id; must refer to an existing road.

        Returns:
            dict: { "success": True, "message": "..."} or { "success": False, "error": "..." }

        Constraints:
            - alert_id must exist.
            - If severity_level provided, must be valid value.
            - If road_id provided, must exist as a road.
            - If nothing is provided to update, returns an error.
        """
        if alert_id not in self.alerts:
            return { "success": False, "error": "Alert with given ID does not exist." }
    
        allowed_severity = {"low", "moderate", "high", "critical"}
        if severity_level is not None:
            if severity_level not in allowed_severity:
                return { "success": False, "error": "Invalid severity_level." }
    
        if active_status is not None and not isinstance(active_status, bool):
            return { "success": False, "error": "active_status must be a boolean." }
    
        if road_id is not None:
            if road_id not in self.roads:
                return { "success": False, "error": "Provided road_id does not exist." }
    
        # Check at least one field is provided for update
        if all(
            param is None
            for param in [severity_level, alert_type, timestamp, description, active_status, road_id]
        ):
            return { "success": False, "error": "No fields provided to update." }

        alert = self.alerts[alert_id]

        if severity_level is not None:
            alert["severity_level"] = severity_level
        if alert_type is not None:
            alert["alert_type"] = alert_type
        if timestamp is not None:
            alert["timestamp"] = timestamp
        if description is not None:
            alert["description"] = description
        if active_status is not None:
            alert["active_status"] = active_status
        if road_id is not None:
            alert["road_id"] = road_id

        self.alerts[alert_id] = alert  # Not strictly needed for dicts, but explicit.

        return { "success": True, "message": "Traffic alert updated successfully." }

    def deactivate_alert(self, alert_id: str) -> dict:
        """
        Deactivate (resolve/close) a traffic alert by setting its active_status to False.

        Args:
            alert_id (str): The unique identifier of the alert to deactivate.

        Returns:
            dict:
                Success: { "success": True, "message": "Alert <alert_id> deactivated." }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - The alert must exist.
            - The alert must be currently active (active_status == True).
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return {"success": False, "error": "Alert not found."}

        if alert["active_status"] is False:
            return {"success": False, "error": "Alert is already inactive."}

        alert["active_status"] = False
        self.alerts[alert_id] = alert  # Save back, in case objects need reinsertion

        return {"success": True, "message": f"Alert {alert_id} deactivated."}

    def activate_alert(self, alert_id: str) -> dict:
        """
        Set the active_status of a TrafficAlert to True (activate it).

        Args:
            alert_id (str): The unique identifier of the alert to activate.

        Returns:
            dict: 
                - On success: 
                    {
                        "success": True,
                        "message": "Alert <alert_id> activated"
                    }
                - On failure: 
                    {
                        "success": False,
                        "error": "Alert does not exist"
                    }

        Constraints:
            - The specified alert_id must exist in the alert records.
        """
        if alert_id not in self.alerts:
            return { "success": False, "error": "Alert does not exist" }

        self.alerts[alert_id]["active_status"] = True
        return { "success": True, "message": f"Alert {alert_id} activated" }

    def delete_alert(self, alert_id: str) -> dict:
        """
        Remove a traffic alert from the system completely.

        Args:
            alert_id (str): The unique identifier for the alert to be deleted.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Alert <alert_id> deleted successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Alert not found."
                    }

        Constraints:
            - The alert identified by alert_id must exist in the system to be deleted.
            - The alert is removed entirely from the self.alerts dictionary.
        """
        if alert_id not in self.alerts:
            return { "success": False, "error": "Alert not found." }

        del self.alerts[alert_id]
        return { "success": True, "message": f"Alert {alert_id} deleted successfully." }


class TrafficManagementSystem(BaseEnv):
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

    def list_all_roads(self, **kwargs):
        return self._call_inner_tool('list_all_roads', kwargs)

    def get_road_by_id(self, **kwargs):
        return self._call_inner_tool('get_road_by_id', kwargs)

    def list_all_alerts(self, **kwargs):
        return self._call_inner_tool('list_all_alerts', kwargs)

    def list_active_alerts(self, **kwargs):
        return self._call_inner_tool('list_active_alerts', kwargs)

    def get_alert_by_id(self, **kwargs):
        return self._call_inner_tool('get_alert_by_id', kwargs)

    def get_alerts_for_road(self, **kwargs):
        return self._call_inner_tool('get_alerts_for_road', kwargs)

    def get_active_alerts_for_road(self, **kwargs):
        return self._call_inner_tool('get_active_alerts_for_road', kwargs)

    def get_roads_with_active_alerts(self, **kwargs):
        return self._call_inner_tool('get_roads_with_active_alerts', kwargs)

    def get_max_severity_for_road(self, **kwargs):
        return self._call_inner_tool('get_max_severity_for_road', kwargs)

    def get_severity_ordering(self, **kwargs):
        return self._call_inner_tool('get_severity_ordering', kwargs)

    def get_ordered_roads_by_alert_severity(self, **kwargs):
        return self._call_inner_tool('get_ordered_roads_by_alert_severity', kwargs)

    def get_alerts_by_severity(self, **kwargs):
        return self._call_inner_tool('get_alerts_by_severity', kwargs)

    def create_road(self, **kwargs):
        return self._call_inner_tool('create_road', kwargs)

    def update_road_status(self, **kwargs):
        return self._call_inner_tool('update_road_status', kwargs)

    def create_traffic_alert(self, **kwargs):
        return self._call_inner_tool('create_traffic_alert', kwargs)

    def update_traffic_alert(self, **kwargs):
        return self._call_inner_tool('update_traffic_alert', kwargs)

    def deactivate_alert(self, **kwargs):
        return self._call_inner_tool('deactivate_alert', kwargs)

    def activate_alert(self, **kwargs):
        return self._call_inner_tool('activate_alert', kwargs)

    def delete_alert(self, **kwargs):
        return self._call_inner_tool('delete_alert', kwargs)

