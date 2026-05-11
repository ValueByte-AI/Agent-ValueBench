# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



# Represents an emergency call/request from the public
class EmergencyRequestInfo(TypedDict):
    request_id: str
    address: str
    request_time: str  # Could be datetime or timestamp in real use
    priority: str
    status: str
    assigned_unit: Optional[str]  # unit_id, if assigned

# Represents a physical or personnel response resource
class ResponseUnitInfo(TypedDict):
    unit_id: str
    type: str
    status: str
    location: str
    assigned_request_id: Optional[str]  # request_id, if assigned

# Represents reference address/location information
class AddressInfo(TypedDict):
    address_id: str
    street: str
    city: str
    geo_coordinate: str  # Could be tuple[float, float] in real use

# Represents an individual responder, their qualifications and current unit assignment
class PersonnelInfo(TypedDict):
    personnel_id: str
    name: str
    qualification: str
    status: str
    assigned_unit_id: Optional[str]  # unit_id, if assigned

class _GeneratedEnvImpl:
    def __init__(self):
        # Emergency Requests: {request_id: EmergencyRequestInfo}
        self.emergency_requests: Dict[str, EmergencyRequestInfo] = {}
        # Response Units: {unit_id: ResponseUnitInfo}
        self.response_units: Dict[str, ResponseUnitInfo] = {}
        # Addresses: {address_id: AddressInfo}
        self.addresses: Dict[str, AddressInfo] = {}
        # Personnel: {personnel_id: PersonnelInfo}
        self.personnel: Dict[str, PersonnelInfo] = {}

        # Constraints:
        # - A response unit can only be dispatched if its status is "available".
        # - An emergency request must have a valid address before dispatch.
        # - A unit can only be assigned to one request at a time.
        # - The priority of requests may affect dispatch order if multiple simultaneous emergencies occur.

    def get_address_by_details(
        self, 
        street: Optional[str] = None, 
        city: Optional[str] = None, 
        geo_coordinate: Optional[str] = None
    ) -> dict:
        """
        Lookup address entities using street, city, and/or geo_coordinate.
        At least one filter criterion must be provided.

        Args:
            street (Optional[str]): Street name or part thereof to match.
            city (Optional[str]): City name to match.
            geo_coordinate (Optional[str]): Exact geo_coordinate string to match.

        Returns:
            dict: {
                "success": True,
                "data": List[AddressInfo]  # list of matching addresses
            }
            or
            {
                "success": False,
                "error": str  # e.g., "No matching address found" or "At least one detail must be provided"
            }

        Constraints:
            - At least one parameter (street, city, geo_coordinate) must be provided.
            - All provided criteria are matched using exact string matching (case sensitive).
        """
        if not street and not city and not geo_coordinate:
            return {
                "success": False,
                "error": "At least one detail (street, city, or geo_coordinate) must be provided"
            }
    
        results = []
        for address in self.addresses.values():
            if (
                (street is None or address['street'] == street) and
                (city is None or address['city'] == city) and
                (geo_coordinate is None or address['geo_coordinate'] == geo_coordinate)
            ):
                results.append(address)
    
        if not results:
            return {"success": False, "error": "No matching address found"}

        return {"success": True, "data": results}

    def list_all_addresses(self) -> dict:
        """
        List all registered addresses known by the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AddressInfo]  # list of all address information (can be empty)
            }
        """
        addresses = list(self.addresses.values())
        return { "success": True, "data": addresses }

    def get_emergency_request_by_address(self, address: str) -> dict:
        """
        Retrieve all ongoing or open emergency requests for a given address.

        Args:
            address (str): The address string for which to find linked emergency requests.

        Returns:
            dict: {
                "success": True,
                "data": List[EmergencyRequestInfo]  # All "open"/"ongoing" emergency requests for the address (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. invalid input)
            }

        Constraints:
            - Return requests only if their status is considered "open" or "ongoing".
            - Does not validate against the Address table; matches based on string equality with EmergencyRequestInfo['address'].
        """
        if not address or not isinstance(address, str):
            return {"success": False, "error": "A valid address must be provided."}

        # Define which statuses are considered "open" or "ongoing"
        ONGOING_STATUSES = {"open", "ongoing", "in progress", "pending", "active"}

        result = [
            req for req in self.emergency_requests.values()
            if req["address"] == address and req.get("status", "").lower() in ONGOING_STATUSES
        ]

        return {"success": True, "data": result}

    def get_emergency_request_by_id(self, request_id: str) -> dict:
        """
        Fetch the details of an emergency request using its request_id.

        Args:
            request_id (str): The unique identifier of the emergency request.

        Returns:
            dict: {
                "success": True,
                "data": EmergencyRequestInfo,    # Dictionary containing request details
            }
            or
            {
                "success": False,
                "error": str  # Reason the request could not be fulfilled
            }

        Constraints:
            - No special constraints; just checks existence.
        """
        request = self.emergency_requests.get(request_id)
        if request is None:
            return { "success": False, "error": "Emergency request not found" }
        return { "success": True, "data": request }

    def list_all_open_emergency_requests(self) -> dict:
        """
        List all emergency requests that are currently not resolved or closed.

        Returns:
            dict: {
                "success": True,
                "data": List[EmergencyRequestInfo],  # List of open requests
            }

            Always succeeds (returns empty list if no open requests found).

        Notes:
            - Any request whose status is NOT "resolved" or "closed" is considered open.
        """
        closed_statuses = {"resolved", "closed"}
        open_requests = [
            req for req in self.emergency_requests.values()
            if req.get("status", "").lower() not in closed_statuses
        ]
        return { "success": True, "data": open_requests }

    def list_available_response_units(self) -> dict:
        """
        Retrieve all response units that currently have status 'available'.
    
        Returns:
            dict: {
                "success": True,
                "data": List[ResponseUnitInfo]  # List of available units (possibly empty)
            }
    
        No constraints are enforced in this query operation; just a filter.
        """
        available_units = [
            unit_info for unit_info in self.response_units.values()
            if unit_info.get('status') == "available"
        ]
        return {"success": True, "data": available_units}

    def get_response_unit_by_id(self, unit_id: str) -> dict:
        """
        Fetch full details for a response unit given its unit_id.

        Args:
            unit_id (str): The unique identifier of the response unit.

        Returns:
            dict: {
                "success": True,
                "data": ResponseUnitInfo  # Full details of the unit.
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found.
            }

        Constraints:
            - The response unit with the specified unit_id must exist.
        """
        unit = self.response_units.get(unit_id)
        if not unit:
            return {"success": False, "error": "Response unit not found"}
        return {"success": True, "data": unit}

    def get_units_assigned_to_request(self, request_id: str) -> dict:
        """
        List all response units currently assigned to the specified emergency request.

        Args:
            request_id (str): The unique identifier of the emergency request.

        Returns:
            dict: {
                "success": True,
                "data": List[ResponseUnitInfo]  # May be empty if no units assigned
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g., request does not exist
            }

        Constraints:
            - request_id must exist among emergency requests.
        """
        if request_id not in self.emergency_requests:
            return {"success": False, "error": "Emergency request does not exist"}

        assigned_units = [
            unit_info for unit_info in self.response_units.values()
            if unit_info.get("assigned_request_id") == request_id
        ]
        return {"success": True, "data": assigned_units}

    def list_response_units_by_type(self, unit_type: str) -> dict:
        """
        Retrieve all response units of the given type.

        Args:
            unit_type (str): The type of the response unit (e.g., 'ambulance', 'fire truck', etc.)

        Returns:
            dict: {
                "success": True,
                "data": List[ResponseUnitInfo],  # May be empty if no units of given type exist
            }

        Constraints:
            - No special constraints; this is a direct filter on unit type.
        """
        result = [
            unit_info for unit_info in self.response_units.values()
            if unit_info["type"] == unit_type
        ]
        return { "success": True, "data": result }

    def check_unit_assignment_status(self, unit_id: str) -> dict:
        """
        Query whether a specific response unit is currently assigned, and to which request.

        Args:
            unit_id (str): The unique identifier of the response unit.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "assigned": bool,                    # Whether the unit is assigned to a request
                    "assigned_request_id": Optional[str] # request_id if assigned, else None
                }
            }
            OR
            {
                "success": False,
                "error": str  # Description of the error (e.g., unit does not exist)
            }

        Constraints:
            - The provided unit_id must exist in the system.
        """
        unit = self.response_units.get(unit_id)
        if unit is None:
            return { "success": False, "error": "Response unit not found" }

        assigned_request_id = unit.get("assigned_request_id")
        return {
            "success": True,
            "data": {
                "assigned": bool(assigned_request_id),
                "assigned_request_id": assigned_request_id if assigned_request_id else None
            }
        }

    def get_personnel_by_qualification(self, qualification: str) -> dict:
        """
        Retrieve all personnel who have a given qualification.

        Args:
            qualification (str): The qualification to filter personnel by (e.g., 'paramedic', 'firefighter').

        Returns:
            dict: {
                "success": True,
                "data": List[PersonnelInfo]  # list of personnel with the given qualification (may be empty)
            }
        """
        matched_personnel = [
            person for person in self.personnel.values()
            if person.get("qualification") == qualification
        ]

        return {
            "success": True,
            "data": matched_personnel
        }

    def get_personnel_assigned_to_unit(self, unit_id: str) -> dict:
        """
        List personnel currently assigned to a specific response unit.

        Args:
            unit_id (str): The unique identifier of the response unit.

        Returns:
            dict: {
                "success": True,
                "data": List[PersonnelInfo],  # Personnel currently assigned to this unit (possibly empty)
            }
            OR
            {
                "success": False,
                "error": str  # If the unit_id does not exist
            }

        Constraints:
            - The response unit must exist.
        """
        if unit_id not in self.response_units:
            return { "success": False, "error": "Response unit does not exist" }

        result = [
            p for p in self.personnel.values()
            if p.get("assigned_unit_id") == unit_id
        ]
        return { "success": True, "data": result }

    def create_emergency_request(self, address_id: str, request_time: str, priority: str, request_id: str = None) -> dict:
        """
        Open a new emergency request for a given address with specified time and priority.

        Args:
            address_id (str): Unique identifier for the address involved in the emergency.
            request_time (str): The time the request was made (ISO8601 or timestamp string).
            priority (str): Priority level for the emergency (e.g., "high", "medium", "low").
            request_id (str, optional): If provided, use this as the request_id; otherwise, generate a unique one.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Emergency request created with request_id <ID>"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Address must exist in the system.
            - request_id must be unique in the system.
        """
        # Validate address
        if address_id not in self.addresses:
            return { "success": False, "error": "Invalid address" }

        # Assign or generate unique request_id
        if request_id is None:
            # Generate a unique ID (simple numeric approach)
            base = "REQ"
            i = 1
            while f"{base}{i}" in self.emergency_requests:
                i += 1
            request_id = f"{base}{i}"
        else:
            if request_id in self.emergency_requests:
                return { "success": False, "error": "Request ID already exists" }

        # Build EmergencyRequestInfo
        emergency_request: EmergencyRequestInfo = {
            "request_id": request_id,
            "address": self.addresses[address_id]["street"],
            "request_time": request_time,
            "priority": priority,
            "status": "open",       # Default initial status
            "assigned_unit": None,  # None on creation
        }

        self.emergency_requests[request_id] = emergency_request

        return {
            "success": True,
            "message": f"Emergency request created with request_id {request_id}"
        }

    def assign_unit_to_emergency_request(self, request_id: str, unit_id: str) -> dict:
        """
        Dispatch a response unit to a request:
            - Assigns the response unit to the emergency request.
            - Updates both the unit and the request with the assignment.
            - Updates statuses as appropriate.

        Args:
            request_id (str): ID of the emergency request to assign a unit to.
            unit_id (str): ID of the response unit to assign.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message, on successful dispatch.
            }
            or
            {
                "success": False,
                "error": str    # Error message, if operation could not be completed.
            }

        Constraints:
            - The emergency request and unit must exist.
            - The response unit must have status "available".
            - The request's address must exist in the address book.
            - The response unit must not be assigned to another request.
            - The emergency request can have at most one assigned unit.
        """
        # 1. Check existence of request and unit
        req = self.emergency_requests.get(request_id)
        unit = self.response_units.get(unit_id)
        if req is None:
            return {"success": False, "error": "Emergency request not found"}
        if unit is None:
            return {"success": False, "error": "Response unit not found"}

        # 2. Check request's address validity
        # Address is a string field; must exist as an address value in self.addresses
        valid_address = any(
            addr["street"] == req["address"] or addr["address_id"] == req["address"]
            for addr in self.addresses.values()
        )
        if not valid_address:
            return {"success": False, "error": "Invalid or unknown address on emergency request"}

        # 3. Check if unit is available
        if unit["status"] != "available":
            return {"success": False, "error": "Response unit is not available"}

        # 4. Check if unit already assigned to another request
        if unit.get("assigned_request_id"):
            return {"success": False, "error": "Response unit is already assigned to another request"}

        # 5. Check if request already has a unit assigned
        if req.get("assigned_unit"):
            return {"success": False, "error": "Emergency request already has a unit assigned"}

        # 6. Perform the assignment: update both entities and statuses
        req["assigned_unit"] = unit_id
        # You may want to update request status, e.g., "assigned" or "dispatched"
        req["status"] = "assigned"
        unit["assigned_request_id"] = request_id
        unit["status"] = "dispatched"

        return {
            "success": True,
            "message": f"Unit {unit_id} assigned to emergency request {request_id}."
        }

    def update_emergency_request_status(self, request_id: str, new_status: str) -> dict:
        """
        Change the status of an emergency request.

        Args:
            request_id (str): The unique ID of the emergency request.
            new_status (str): The new status to be set (e.g., "in progress", "resolved").

        Returns:
            dict: {
                "success": True,
                "message": "Emergency request status updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The emergency request identified by request_id must exist.
            - No constraint on allowable status strings (trust user-provided status).
        """
        if request_id not in self.emergency_requests:
            return {"success": False, "error": "Emergency request does not exist."}

        self.emergency_requests[request_id]['status'] = new_status
        return {"success": True, "message": "Emergency request status updated."}

    def update_unit_status(self, unit_id: str, new_status: str) -> dict:
        """
        Update the status of a response unit.

        Args:
            unit_id (str): Unique identifier of the response unit.
            new_status (str): The new status to set (e.g., "dispatched", "busy", "available").

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Response unit status updated to <new_status>"}
                On failure:
                    {"success": False, "error": <reason>}
        
        Constraints:
            - The response unit must exist.
            - No restriction on new_status value in current environment.
        """
        if unit_id not in self.response_units:
            return {"success": False, "error": "Response unit does not exist"}

        self.response_units[unit_id]["status"] = new_status
        return {"success": True, "message": f"Response unit status updated to {new_status}"}

    def unassign_unit_from_request(self, unit_id: str) -> dict:
        """
        Remove the assignment of a unit from a request and set the unit's status as available.

        Args:
            unit_id (str): The ID of the response unit to unassign.

        Returns:
            dict: 
                On success: { "success": True, "message": "Unit unassigned from request and marked available." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The unit must exist.
            - The unit must currently be assigned to a request.
            - The assigned request must also exist and reference this unit.
        """
        # Check unit existence
        unit = self.response_units.get(unit_id)
        if not unit:
            return { "success": False, "error": "Unit not found." }
    
        request_id = unit.get("assigned_request_id")
        if not request_id:
            return { "success": False, "error": "Unit is not assigned to any request." }
    
        # Check that the emergency request exists
        request = self.emergency_requests.get(request_id)
        if not request:
            return { "success": False, "error": "Assigned request not found." }

        # Ensure this unit is the one currently assigned to the request
        if request.get("assigned_unit") != unit_id:
            return { "success": False, "error": "Unit assignment inconsistency detected." }
    
        # Unassign unit from request
        unit["assigned_request_id"] = None
        unit["status"] = "available"
        request["assigned_unit"] = None

        return { "success": True, "message": "Unit unassigned from request and marked available." }

    def update_personnel_assignment(self, personnel_id: str, unit_id: str) -> dict:
        """
        Assign or reassign a personnel to a unit.

        Args:
            personnel_id (str): The personnel to assign or reassign.
            unit_id (str): The target response unit ID to assign to. If empty string or None, unassigns from any unit.

        Returns:
            dict: {
                "success": True,
                "message": "Personnel <id> now assigned to unit <unit_id>" OR "Personnel <id> is now unassigned"
            }
            OR
            {
                "success": False,
                "error": <error_reason>
            }
        Constraints:
            - Personnel must exist.
            - If assigning (unit_id is not None/empty), unit must exist.
            - Assignment is always updated to target value.
        """
        # Check personnel exists
        if personnel_id not in self.personnel:
            return { "success": False, "error": f"Personnel '{personnel_id}' not found" }

        # Assigning to unit (not unassigning)
        if unit_id and unit_id.strip():
            if unit_id not in self.response_units:
                return { "success": False, "error": f"Response unit '{unit_id}' not found" }
            self.personnel[personnel_id]["assigned_unit_id"] = unit_id
            return { "success": True, "message": f"Personnel '{personnel_id}' now assigned to unit '{unit_id}'" }
        else:
            # Unassignment
            self.personnel[personnel_id]["assigned_unit_id"] = None
            return { "success": True, "message": f"Personnel '{personnel_id}' is now unassigned" }

    def update_emergency_request_priority(self, request_id: str, new_priority: str) -> dict:
        """
        Change the priority level of an ongoing emergency request.

        Args:
            request_id (str): The unique identifier for the emergency request to update.
            new_priority (str): The new priority level to set for the request.

        Returns:
            dict: {
                "success": True,
                "message": "Priority updated for request <request_id>"
            }
            or
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - The request_id must exist in the system.
            - The priority can always be changed (no status restriction).
        """
        if not request_id or request_id not in self.emergency_requests:
            return {"success": False, "error": "Emergency request not found"}

        # Normalize/validate new_priority if needed (skipped for now—could check allowed priorities)
        self.emergency_requests[request_id]["priority"] = new_priority

        return {
            "success": True,
            "message": f"Priority updated for request {request_id}"
        }


class EmergencyDispatchSystem(BaseEnv):
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

    def get_address_by_details(self, **kwargs):
        return self._call_inner_tool('get_address_by_details', kwargs)

    def list_all_addresses(self, **kwargs):
        return self._call_inner_tool('list_all_addresses', kwargs)

    def get_emergency_request_by_address(self, **kwargs):
        return self._call_inner_tool('get_emergency_request_by_address', kwargs)

    def get_emergency_request_by_id(self, **kwargs):
        return self._call_inner_tool('get_emergency_request_by_id', kwargs)

    def list_all_open_emergency_requests(self, **kwargs):
        return self._call_inner_tool('list_all_open_emergency_requests', kwargs)

    def list_available_response_units(self, **kwargs):
        return self._call_inner_tool('list_available_response_units', kwargs)

    def get_response_unit_by_id(self, **kwargs):
        return self._call_inner_tool('get_response_unit_by_id', kwargs)

    def get_units_assigned_to_request(self, **kwargs):
        return self._call_inner_tool('get_units_assigned_to_request', kwargs)

    def list_response_units_by_type(self, **kwargs):
        return self._call_inner_tool('list_response_units_by_type', kwargs)

    def check_unit_assignment_status(self, **kwargs):
        return self._call_inner_tool('check_unit_assignment_status', kwargs)

    def get_personnel_by_qualification(self, **kwargs):
        return self._call_inner_tool('get_personnel_by_qualification', kwargs)

    def get_personnel_assigned_to_unit(self, **kwargs):
        return self._call_inner_tool('get_personnel_assigned_to_unit', kwargs)

    def create_emergency_request(self, **kwargs):
        return self._call_inner_tool('create_emergency_request', kwargs)

    def assign_unit_to_emergency_request(self, **kwargs):
        return self._call_inner_tool('assign_unit_to_emergency_request', kwargs)

    def update_emergency_request_status(self, **kwargs):
        return self._call_inner_tool('update_emergency_request_status', kwargs)

    def update_unit_status(self, **kwargs):
        return self._call_inner_tool('update_unit_status', kwargs)

    def unassign_unit_from_request(self, **kwargs):
        return self._call_inner_tool('unassign_unit_from_request', kwargs)

    def update_personnel_assignment(self, **kwargs):
        return self._call_inner_tool('update_personnel_assignment', kwargs)

    def update_emergency_request_priority(self, **kwargs):
        return self._call_inner_tool('update_emergency_request_priority', kwargs)
