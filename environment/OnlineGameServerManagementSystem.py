# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import time



class GameServerInfo(TypedDict):
    ver_id: str
    region: str  # region_id
    status: str
    configuration: str  # could be JSON string or a more detailed TypedDict; kept as str for now
    assigned_event: Optional[str]  # event_id or None
    uptime: float  # in seconds or hours
    performance_metric: float  # e.g., average latency, load

class RegionInfo(TypedDict):
    region_id: str
    name: str
    server_id: str  # could be a list, but as per the schema, this is a single server_id

class EventInfo(TypedDict):
    event_id: str
    name: str
    start_time: float  # epoch timestamp
    end_time: float    # epoch timestamp
    assigned_server_id: str

class AdministratorInfo(TypedDict):
    admin_id: str
    name: str
    permission: str  # simple permission role label (e.g., "admin", "viewer", etc.)

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing online game server instances, regions, events, and administrators.
        """
        # Game servers: {ver_id: GameServerInfo}
        self.servers: Dict[str, GameServerInfo] = {}

        # Regions: {region_id: RegionInfo}
        self.regions: Dict[str, RegionInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # Administrators: {admin_id: AdministratorInfo}
        self.administrators: Dict[str, AdministratorInfo] = {}

        # Constraints (see environment rules):
        # - A server must be assigned to exactly one region at any given time.
        # - Servers can only be started if their status is "stopped" or "idle".
        # - Resource availability in a region may limit the number of servers that can be started simultaneously.
        # - Only administrators with proper permissions can start or stop servers.
        # - Performance and uptime must be logged for each server session.
        # - Servers assigned to an event should not be stopped until the event ends.

    @staticmethod
    def _normalize_optional_reference(value):
        if value is None:
            return None
        if isinstance(value, str) and value.strip().lower() in {"", "none"}:
            return None
        return value

    def get_server_by_id(self, ver_id: str) -> dict:
        """
        Retrieve detailed information about a specific game server given its ver_id.

        Args:
            ver_id (str): The unique identifier for the game server.

        Returns:
            dict:
                Success case:
                    {
                        "success": True,
                        "data": GameServerInfo  # Detailed info about the game server
                    }
                Failure case:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g., server not found)
                    }
        Constraints:
            - No permissions required.
            - Returns error if ver_id is not found.
        """
        if ver_id not in self.servers:
            return {"success": False, "error": "Server with given ver_id does not exist"}

        return {"success": True, "data": self.servers[ver_id]}

    def list_servers_in_region(self, region_id: str) -> dict:
        """
        Retrieve all servers currently assigned to a specific region.

        Args:
            region_id (str): The ID of the region.

        Returns:
            dict: {
                "success": True,
                "data": List[GameServerInfo]  # List of server info (could be empty)
            }
            or
            {
                "success": False,
                "error": "Region does not exist"
            }

        Constraints:
            - region_id must exist in the system.
            - Returns all servers where server["region"] == region_id.
        """
        if region_id not in self.regions:
            return {"success": False, "error": "Region does not exist"}

        result = [
            server_info
            for server_info in self.servers.values()
            if server_info["region"] == region_id
        ]

        return {"success": True, "data": result}

    def get_server_status(self, ver_id: str) -> dict:
        """
        Query the current operational status of a game server.

        Args:
            ver_id (str): Unique identifier of the server.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": {
                          "ver_id": <ver_id>,
                          "status": <status_string>
                      }
                    }
                If the server does not exist:
                    {
                      "success": False,
                      "error": "Server not found"
                    }
        Constraints:
            - The server with the given ver_id must exist in the environment.
            - No permission checks for status query.
        """
        server = self.servers.get(ver_id)
        if server is None:
            return { "success": False, "error": "Server not found" }
        return {
            "success": True,
            "data": {
                "ver_id": ver_id,
                "status": server["status"]
            }
        }

    def get_server_uptime_and_performance(self, ver_id: str) -> dict:
        """
        Retrieve the uptime and performance metrics for a specified server.

        Args:
            ver_id (str): The unique server ID.

        Returns:
            dict:
                - On success:
                  {
                    "success": True,
                    "data": {
                        "uptime": float,
                        "performance_metric": float
                    }
                  }
                - On failure:
                  {
                    "success": False,
                    "error": str  # Reason for failure, e.g., server not found.
                  }

        Constraints:
            - The server with the given ver_id must exist in the system.
        """
        server = self.servers.get(ver_id)
        if not server:
            return { "success": False, "error": "Server not found" }
        # Defensive: Ensure the required keys are present
        if "uptime" not in server or "performance_metric" not in server:
            return { "success": False, "error": "Server data incomplete" }
        return {
            "success": True,
            "data": {
                "uptime": server["uptime"],
                "performance_metric": server["performance_metric"]
            }
        }

    def get_region_by_name(self, name: str) -> dict:
        """
        Retrieve region information by its human-readable name.

        Args:
            name (str): The human-readable name of the region.

        Returns:
            dict: {
                "success": True,
                "data": RegionInfo  # Information on the matching region
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g. region not found
            }

        Constraints:
            - No special constraints; if multiple regions share a name, the first match is returned.
            - If not found, returns a failure message.
        """
        for region_info in self.regions.values():
            if region_info["name"] == name:
                return {"success": True, "data": region_info}
        return {"success": False, "error": "Region not found"}

    def get_region_by_id(self, region_id: str) -> dict:
        """
        Retrieve region information by its unique region_id.

        Args:
            region_id (str): Unique identifier for the region.

        Returns:
            dict: 
                - { "success": True, "data": RegionInfo } if the region is found.
                - { "success": False, "error": "Region not found" } otherwise.

        Constraints:
            - The region_id must exist in the environment.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region not found" }

        return {
            "success": True,
            "data": self.regions[region_id]
        }

    def check_region_capacity(self, region_id: str) -> dict:
        """
        Determine if a region has resource availability to start another server.

        Args:
            region_id (str): The ID of the region to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "can_start": bool,
                    "current_running": int,   # number of servers currently running in the region
                    "max_capacity": int
                }
            }
            or
            {
                "success": False,
                "error": str  # reason (e.g. Region not found)
            }
    
        Constraints:
            - If region_id does not exist, return failure.
            - Uses a default max region capacity (e.g., 5) if not specified elsewhere.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region not found" }
    
        # Placeholder: max servers per region
        max_capacity = 5

        # Count running/started servers in the region
        running_statuses = {"running", "started"}  # Use all statuses indicating "started"
        current_running = sum(
            1 for server in self.servers.values()
            if server["region"] == region_id and server["status"] in running_statuses
        )
        can_start = current_running < max_capacity
        return {
            "success": True,
            "data": {
                "can_start": can_start,
                "current_running": current_running,
                "max_capacity": max_capacity
            }
        }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve information about a specific gameplay event.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": EventInfo  # The full info dictionary for the event
                }
                On error: {
                    "success": False,
                    "error": str  # Description of the error, e.g., if event not found
                }

        Constraints:
            - event_id must exist in the system.
        """
        event = self.events.get(event_id)
        if event is None:
            return { "success": False, "error": "Event not found" }
        return { "success": True, "data": event }

    def get_event_by_server_id(self, server_id: str) -> dict:
        """
        Retrieve the event (if any) currently assigned to a given server.
    
        Args:
            server_id (str): The ID of the game server to query.
    
        Returns:
            dict:
                {
                    "success": True,
                    "data": List[EventInfo]  # List with one EventInfo, or empty if no event assigned
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g., server not found or event not found
                }
    
        Constraints:
            - Returns empty list if the server has no assigned event.
            - If server_id does not exist, returns error.
            - If event is assigned but does not exist in event registry, returns error.
        """
        server = self.servers.get(server_id)
        if not server:
            return {"success": False, "error": "Server not found"}

        event_id = self._normalize_optional_reference(server.get("assigned_event"))
        if not event_id:
            return {"success": True, "data": []}

        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Assigned event not found in event registry"}
    
        return {"success": True, "data": [event]}

    def get_admin_permissions(self, admin_id: str) -> dict:
        """
        Query the permission level (e.g., admin, viewer) of the given administrator.

        Args:
            admin_id (str): The unique administrator ID.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": {
                          "admin_id": str,
                          "permission": str
                      }
                  }
                - On failure: {
                      "success": False,
                      "error": "Administrator not found"
                  }
        Constraints:
            - admin_id must exist in the administrator records.
        """
        admin = self.administrators.get(admin_id)
        if admin is None:
            return {"success": False, "error": "Administrator not found"}

        return {
            "success": True,
            "data": {
                "admin_id": admin_id,
                "permission": admin["permission"]
            }
        }

    def list_admins(self) -> dict:
        """
        List all registered administrators with their admin_id, name, and permission/role.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AdministratorInfo]
            }
            If no admins are in the system, data will be an empty list.

        Constraints:
            - No permissions check required.
            - No arguments needed.
        """
        result = list(self.administrators.values())
        return { "success": True, "data": result }

    def start_server(self, server_id: str, admin_id: str) -> dict:
        """
        Attempt to start a server if it is in 'stopped' or 'idle' status, assigned to a valid region,
        and the administrator has 'admin' permissions (or higher). Also enforces regional capacity constraints.

        Args:
            server_id (str): The ID of the game server to start.
            admin_id (str): The administrator requesting the operation.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Server <id> started" }
                On failure:
                    { "success": False, "error": "reason for failure" }

        Constraints:
            - The server must exist.
            - The admin must exist and have permission 'admin'.
            - The server must be in 'stopped' or 'idle' status.
            - The server must be assigned to an existing region.
            - The region may have a running server cap (simulate as max 5 servers running per region).
        """
        # Check admin existence and permission
        admin = self.administrators.get(admin_id)
        if not admin:
            return {"success": False, "error": "Administrator not found"}
        if admin['permission'] != 'admin':
            return {"success": False, "error": "Permission denied"}

        # Check server existence
        server = self.servers.get(server_id)
        if not server:
            return {"success": False, "error": "Server not found"}

        # Check server status
        if server['status'] not in ("stopped", "idle"):
            return {"success": False, "error": f"Server status must be 'stopped' or 'idle' (current: '{server['status']}')"}

        # Check server assigned to a region
        region_id = server.get('region')
        if not region_id or region_id not in self.regions:
            return {"success": False, "error": "Server not assigned to a valid region"}

        # Check region running server cap (simulate: max 5 running servers per region)
        running_statuses = {"running", "active"}
        running_servers_in_region = sum(
            1 for srv in self.servers.values()
            if srv['region'] == region_id and srv['status'] in running_statuses
        )
        if running_servers_in_region >= 5:
            return {"success": False, "error": f"Region '{region_id}' has reached running server capacity (5)"}

        # Change server status to "running"
        self.servers[server_id]['status'] = "running"
        # Optionally, set/modify uptime and performance_metric as needed (not specified here)

        return {"success": True, "message": f"Server '{server_id}' started"}

    def stop_server(self, ver_id: str, admin_id: str) -> dict:
        """
        Stop a game server, ensuring:
          - The server exists.
          - The administrator exists and has proper permissions (must be 'admin').
          - The server is not currently assigned to an ongoing event (event's end_time > now).
          - The server's status is not already "stopped".

        Args:
            ver_id (str): ID of the server to stop.
            admin_id (str): ID of the administrator requesting the operation.

        Returns:
            dict: On success:
                { "success": True, "message": "Server <ver_id> stopped." }
                  On failure:
                { "success": False, "error": "<reason>" }
        """

        # Check server exists
        server = self.servers.get(ver_id)
        if not server:
            return { "success": False, "error": "Server not found." }

        # Check administrator exists and permission
        admin = self.administrators.get(admin_id)
        if not admin:
            return { "success": False, "error": "Administrator not found." }
        if admin["permission"] != "admin":
            return { "success": False, "error": "Permission denied. Admin privileges required." }

        # Check if server is already stopped
        if server["status"] == "stopped":
            return { "success": False, "error": f"Server {ver_id} is already stopped." }

        # If assigned to an event, check event status
        assigned_event_id = server.get("assigned_event")
        if assigned_event_id:
            event = self.events.get(assigned_event_id)
            now = time.time()
            if event:
                if event["assigned_server_id"] == ver_id and event["end_time"] > now:
                    return {
                        "success": False,
                        "error": f"Server is assigned to ongoing event '{event['name']}'. Cannot stop until event ends."
                    }
    
        # Change server status to "stopped"
        server["status"] = "stopped"

        # Optionally: log this fact (not specified in detail here)
        # self.log_server_session(ver_id, "stopped", admin_id, now)

        return { "success": True, "message": f"Server {ver_id} stopped." }

    def assign_server_to_region(self, ver_id: str, region_id: str) -> dict:
        """
        Assign a server to a specific region, ensuring one-to-one mapping.

        Args:
            ver_id (str): The unique identifier of the game server to be assigned.
            region_id (str): The unique identifier of the target region.

        Returns:
            dict:
                - success: True/False
                - message or error: description of operation result

        Constraints:
            - A server must be assigned to exactly one region at any given time.
            - Each region can only have one server (one-to-one).
            - If server already has this region, operation is idempotent success.
            - If region already has a different server, refuse with error.
        """
        # Check if server exists
        if ver_id not in self.servers:
            return {"success": False, "error": f"Server {ver_id} does not exist."}
        # Check if region exists
        if region_id not in self.regions:
            return {"success": False, "error": f"Region {region_id} does not exist."}

        server_info = self.servers[ver_id]
        region_info = self.regions[region_id]

        # Check if the server is already assigned to this region (idempotency)
        if server_info['region'] == region_id:
            # Also, ensure the region's server_id matches
            if region_info['server_id'] == ver_id:
                return {
                    "success": True,
                    "message": f"Server {ver_id} is already assigned to region {region_id}."
                }
    
        # If the region already has a different server assigned, refuse
        if region_info['server_id'] != "" and region_info['server_id'] != ver_id:
            return {
                "success": False,
                "error": f"Region {region_id} is already assigned to server {region_info['server_id']}."
            }

        # Find the region to which this server is currently assigned (if different), and unassign from there
        old_region_id = server_info['region']
        if old_region_id and old_region_id != region_id:
            # Unassign from the old region
            if old_region_id in self.regions:
                if self.regions[old_region_id]['server_id'] == ver_id:
                    self.regions[old_region_id]['server_id'] = ""

        # Assign server to new region
        server_info['region'] = region_id
        self.servers[ver_id] = server_info
        self.regions[region_id]['server_id'] = ver_id

        return {
            "success": True,
            "message": f"Server {ver_id} assigned to region {region_id}."
        }

    def unassign_server_from_region(self, ver_id: str) -> dict:
        """
        Remove a server's region assignment (for migration or maintenance).

        Args:
            ver_id (str): Unique identifier of the game server to unassign from its region.

        Returns:
            dict: {
                "success": True,
                "message": "Server <ver_id> has been unassigned from its region."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The server must exist.
            - The server must currently be assigned to a region.
            - This may temporarily leave the server with no region (permitted for migration/maintenance).
            - If the region references the server, update region accordingly.
        """
        # Check server existence
        if ver_id not in self.servers:
            return { "success": False, "error": "Server does not exist." }
    
        server = self.servers[ver_id]
        region_id = server.get("region")

        if not region_id:
            return { "success": False, "error": f"Server {ver_id} is not currently assigned to any region." }
    
        # Remove server's region assignment
        server["region"] = None

        # Also clear region's reference to server, if applicable
        region_info = self.regions.get(region_id)
        if region_info and region_info.get("server_id") == ver_id:
            region_info["server_id"] = ""  # Or None, depending on schema; use "" here to avoid None type in typed dict
    
        return {
            "success": True,
            "message": f"Server {ver_id} has been unassigned from its region."
        }

    def assign_server_to_event(self, ver_id: str, event_id: str) -> dict:
        """
        Assign (link) a game server to a specific gameplay event.

        Args:
            ver_id (str): ID of the server to assign.
            event_id (str): ID of the event.

        Returns:
            dict: {
                "success": True,
                "message": "Server <ver_id> assigned to event <event_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both server and event must exist.
            - A server can only be assigned to one event at any time.
            - An event can only have one assigned server at any time.
            - Assignment should be mutual and consistent.
        """
        # Check server exists
        if ver_id not in self.servers:
            return { "success": False, "error": f"Server '{ver_id}' does not exist." }
        # Check event exists
        if event_id not in self.events:
            return { "success": False, "error": f"Event '{event_id}' does not exist." }

        server = self.servers[ver_id]
        event = self.events[event_id]

        # Check if server already assigned to a different event
        current_assigned_event = self._normalize_optional_reference(server.get("assigned_event"))
        current_assigned_server = self._normalize_optional_reference(event.get("assigned_server_id"))

        if current_assigned_event is not None and current_assigned_event != event_id:
            return {
                "success": False,
                "error": f"Server '{ver_id}' already assigned to event '{current_assigned_event}'."
            }
        # Check if event already has a different server assigned
        if current_assigned_server is not None and current_assigned_server != ver_id:
            return {
                "success": False,
                "error": f"Event '{event_id}' already has server '{current_assigned_server}' assigned."
            }

        # Assign
        server['assigned_event'] = event_id
        event['assigned_server_id'] = ver_id

        return {
            "success": True,
            "message": f"Server '{ver_id}' assigned to event '{event_id}'."
        }


    def remove_server_event_assignment(self, server_id: str) -> dict:
        """
        Unassign a server from any attached event, ensuring that the event has ended.
    
        Args:
            server_id (str): The unique ID of the server to unassign from its event.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of operation performed
            }
            or
            {
                "success": False,
                "error": str  # Description of failure reason
            }

        Constraints:
            - If the server is assigned to an event, unassignment should only occur 
              if the event's end_time has already passed.
            - Handles missing server or event data robustly.
        """
        # Check if server exists
        server = self.servers.get(server_id)
        if not server:
            return { "success": False, "error": "Server does not exist" }
    
        event_id = self._normalize_optional_reference(server.get("assigned_event"))
        if not event_id:
            return { "success": False, "error": "Server is not assigned to any event" }

        # Check if event exists
        event = self.events.get(event_id)
        if not event:
            return { "success": False, "error": f"Assigned event '{event_id}' does not exist" }

        now = time.time()
        if event["end_time"] > now:
            return { 
                "success": False, 
                "error": f"Cannot unassign server from event '{event_id}' before it ends (ends at {event['end_time']}, now {now})"
            }

        # Unassign event from server
        server["assigned_event"] = None

        # Unassign server from event's assignment (if this server is the assigned one)
        if event.get("assigned_server_id") == server_id:
            event["assigned_server_id"] = None

        return {
            "success": True,
            "message": f"Server '{server_id}' unassigned from event '{event_id}'"
        }

    def log_server_session(self, ver_id: str, uptime: float, performance_metric: float) -> dict:
        """
        Record or update the performance and uptime data for a given game server session.
    
        Args:
            ver_id (str): Unique identifier of the game server.
            uptime (float): Uptime value (should be non-negative).
            performance_metric (float): Performance metric value (should be non-negative).

        Returns:
            dict: 
                On success: { "success": True, "message": "Server session log updated." }
                On failure: { "success": False, "error": error_message }
    
        Constraints:
            - Server with the given ver_id must exist.
            - Uptime and performance_metric must be non-negative numbers.
        """
        server = self.servers.get(ver_id)
        if server is None:
            return { "success": False, "error": "Server does not exist." }
        if not isinstance(uptime, (int, float)) or uptime < 0:
            return { "success": False, "error": "Invalid uptime value." }
        if not isinstance(performance_metric, (int, float)) or performance_metric < 0:
            return { "success": False, "error": "Invalid performance metric value." }
    
        server["uptime"] = uptime
        server["performance_metric"] = performance_metric
        # State is modified directly in self.servers

        return { "success": True, "message": "Server session log updated." }

    def change_server_status(self, server_id: str, new_status: str, admin_id: str) -> dict:
        """
        Directly update a server’s status (e.g., idle, running, stopped) for administrative overrides.

        Args:
            server_id (str): The game server (ver_id) to update.
            new_status (str): The new status for the server ("idle", "running", "stopped").
            admin_id (str): The admin requesting the change (permission check enforced).

        Returns:
            dict: {
                "success": True,
                "message": "Server status updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Admin must exist and have "admin" permission.
            - Server must exist.
            - Allowed status values: "idle", "running", "stopped".
            - If server is assigned to an active event, cannot set to "stopped" before event ends.
        """
        # Validate admin
        admin = self.administrators.get(admin_id)
        if admin is None:
            return {"success": False, "error": "Administrator does not exist."}
        if admin["permission"] != "admin":
            return {"success": False, "error": "Permission denied. Admin privileges required."}
    
        # Validate server
        server = self.servers.get(server_id)
        if server is None:
            return {"success": False, "error": "Server does not exist."}

        # Validate new_status
        allowed_statuses = {"idle", "running", "stopped"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed: {allowed_statuses}"}

        # If server assigned to an event, and new_status is "stopped", check event end
        event_id = self._normalize_optional_reference(server.get("assigned_event"))
        if event_id:
            event = self.events.get(event_id)
            now = time.time()
            if event and new_status == "stopped" and now < event["end_time"]:
                return {"success": False, "error": "Cannot stop server: assigned to an active event."}

        # All checks passed; update status
        server["status"] = new_status
        self.servers[server_id] = server  # Not strictly needed, but explicit

        return {"success": True, "message": "Server status updated successfully."}

    def add_new_server(
        self, 
        ver_id: str, 
        region_id: str, 
        configuration: str, 
        status: str = "stopped",
        assigned_event: str = None,
        uptime: float = 0.0,
        performance_metric: float = 0.0
    ) -> dict:
        """
        Create and register a new game server instance.

        Args:
            ver_id (str): Unique ID for the server.
            region_id (str): ID of the region in which to register the server (must exist).
            configuration (str): Configuration details (hardware/software etc.).
            status (str, optional): Initial server status ("stopped"/"idle", etc.). Default is "stopped".
            assigned_event (str, optional): Initial event assignment (event_id) or None. Default is None.
            Sentinel values like "none" and "" are treated as unassigned.
            uptime (float, optional): Initial uptime for the server. Default is 0.0.
            performance_metric (float, optional): Initial performance metric. Default is 0.0.

        Returns:
            dict: {
                "success": True,
                "message": "Server <ver_id> added to region <region_id>."
            }
            OR
            {
                "success": False,
                "error": "...reason..."
            }

        Constraints:
            - ver_id must be unique across servers.
            - region_id must exist in self.regions.
            - Server will be assigned exactly to one region.
        """
        if not ver_id or not region_id or not configuration:
            return { "success": False, "error": "ver_id, region_id, and configuration are required." }

        if ver_id in self.servers:
            return { "success": False, "error": f"Server with ver_id '{ver_id}' already exists." }

        if region_id not in self.regions:
            return { "success": False, "error": f"Region '{region_id}' does not exist." }

        normalized_assigned_event = self._normalize_optional_reference(assigned_event)

        self.servers[ver_id] = {
            "ver_id": ver_id,
            "region": region_id,
            "status": status,
            "configuration": configuration,
            "assigned_event": normalized_assigned_event,
            "uptime": uptime,
            "performance_metric": performance_metric,
        }

        return {
            "success": True,
            "message": f"Server {ver_id} added to region {region_id}."
        }

    def remove_server(self, ver_id: str, admin_id: str) -> dict:
        """
        Permanently delete a server record, only if performed by an admin with proper permissions,
        and only if the server is not assigned to an active event.
    
        Args:
            ver_id (str): The ID of the server to remove.
            admin_id (str): The ID of the administrator requesting the operation.
        Returns:
            dict: {
                "success": True,
                "message": "Server <ver_id> removed successfully"
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only administrators with permission "admin" can remove servers.
            - If the server is assigned to an event (assigned_event is not None), it cannot be removed.
            - Removes server from servers dict; also removes server assignment from regions/events if present.
        """
        # Admin permission check
        admin = self.administrators.get(admin_id)
        if not admin:
            return {"success": False, "error": "Administrator not found"}
        if admin.get("permission") != "admin":
            return {"success": False, "error": "Permission denied: admin rights required"}

        # Server existence check
        server = self.servers.get(ver_id)
        if not server:
            return {"success": False, "error": f"Server '{ver_id}' does not exist"}

        # Block removal if assigned to an event
        if self._normalize_optional_reference(server.get("assigned_event")):
            return {
                "success": False,
                "error": f"Server '{ver_id}' is assigned to an event and cannot be removed"
            }

        # Remove server assignment from regions (cleanup)
        for region in self.regions.values():
            if region.get("server_id") == ver_id:
                region["server_id"] = ""  # Or set to None, depending on usage

        # Remove server assignment from any event (historical/corner-case cleanup)
        for event in self.events.values():
            if event.get("assigned_server_id") == ver_id:
                event["assigned_server_id"] = ""  # Or set to None if preferred

        # Remove server itself
        del self.servers[ver_id]

        return {"success": True, "message": f"Server '{ver_id}' removed successfully"}

    def update_admin_permissions(self, admin_id: str, new_permission: str) -> dict:
        """
        Change an administrator's permission level.

        Args:
            admin_id (str): The ID of the administrator whose permissions are to be changed.
            new_permission (str): The new permission level (role label) to be assigned (e.g., "admin", "viewer").

        Returns:
            dict: 
                - On success: {"success": True, "message": "Permission level updated for admin <admin_id>."}
                - On error: {"success": False, "error": <reason>}

        Constraints:
            - The admin_id must exist in the administrators registry.
            - No validation is performed on the permission level unless specified elsewhere.
        """
        if admin_id not in self.administrators:
            return {"success": False, "error": "Administrator not found."}
    
        self.administrators[admin_id]["permission"] = new_permission
        return {
            "success": True,
            "message": f"Permission level updated for admin {admin_id}."
        }


class OnlineGameServerManagementSystem(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "servers" and isinstance(copied, dict):
                for server in copied.values():
                    if isinstance(server, dict):
                        if server.get("region") == "none":
                            server["region"] = None
                        if server.get("assigned_event") == "none":
                            server["assigned_event"] = None
            elif key == "regions" and isinstance(copied, dict):
                for region in copied.values():
                    if isinstance(region, dict) and region.get("server_id") == "none":
                        region["server_id"] = ""
            elif key == "events" and isinstance(copied, dict):
                for event in copied.values():
                    if isinstance(event, dict) and event.get("assigned_server_id") == "none":
                        event["assigned_server_id"] = None
            setattr(env, key, copied)

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

    def get_server_by_id(self, **kwargs):
        return self._call_inner_tool('get_server_by_id', kwargs)

    def list_servers_in_region(self, **kwargs):
        return self._call_inner_tool('list_servers_in_region', kwargs)

    def get_server_status(self, **kwargs):
        return self._call_inner_tool('get_server_status', kwargs)

    def get_server_uptime_and_performance(self, **kwargs):
        return self._call_inner_tool('get_server_uptime_and_performance', kwargs)

    def get_region_by_name(self, **kwargs):
        return self._call_inner_tool('get_region_by_name', kwargs)

    def get_region_by_id(self, **kwargs):
        return self._call_inner_tool('get_region_by_id', kwargs)

    def check_region_capacity(self, **kwargs):
        return self._call_inner_tool('check_region_capacity', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def get_event_by_server_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_server_id', kwargs)

    def get_admin_permissions(self, **kwargs):
        return self._call_inner_tool('get_admin_permissions', kwargs)

    def list_admins(self, **kwargs):
        return self._call_inner_tool('list_admins', kwargs)

    def start_server(self, **kwargs):
        return self._call_inner_tool('start_server', kwargs)

    def stop_server(self, **kwargs):
        return self._call_inner_tool('stop_server', kwargs)

    def assign_server_to_region(self, **kwargs):
        return self._call_inner_tool('assign_server_to_region', kwargs)

    def unassign_server_from_region(self, **kwargs):
        return self._call_inner_tool('unassign_server_from_region', kwargs)

    def assign_server_to_event(self, **kwargs):
        return self._call_inner_tool('assign_server_to_event', kwargs)

    def remove_server_event_assignment(self, **kwargs):
        return self._call_inner_tool('remove_server_event_assignment', kwargs)

    def log_server_session(self, **kwargs):
        return self._call_inner_tool('log_server_session', kwargs)

    def change_server_status(self, **kwargs):
        return self._call_inner_tool('change_server_status', kwargs)

    def add_new_server(self, **kwargs):
        return self._call_inner_tool('add_new_server', kwargs)

    def remove_server(self, **kwargs):
        return self._call_inner_tool('remove_server', kwargs)

    def update_admin_permissions(self, **kwargs):
        return self._call_inner_tool('update_admin_permissions', kwargs)
