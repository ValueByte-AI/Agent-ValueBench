# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime

VALID_REQUEST_STATUSES = {"open", "in progress", "closed", "resolved", "on hold"}



# Maps to "Request" entity (attributes: request_id, status, description, created_timestamp, updated_timestamp, requester_id)
class RequestInfo(TypedDict):
    request_id: str
    status: str
    description: str
    created_timestamp: str
    updated_timestamp: str
    requester_id: str

# Maps to "Requester" entity (attributes: requester_id, name, contact_info, department)
class RequesterInfo(TypedDict):
    requester_id: str
    name: str
    contact_info: str
    department: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Requests: {request_id: RequestInfo}
        self.requests: Dict[str, RequestInfo] = {}
        # Requesters: {requester_id: RequesterInfo}
        self.requesters: Dict[str, RequesterInfo] = {}

        # Constraints:
        # - Each request_id must be unique.
        # - The status attribute must be one of a predefined set (e.g., "open", "in progress", "closed", etc.).
        # - Each request must have valid, non-null requester information.
        # - Timestamps must accurately reflect creation and last update times.

    def get_request_by_id(self, request_id: str) -> dict:
        """
        Retrieve all metadata for a request given its unique request_id.

        Args:
            request_id (str): The unique identifier of the request to retrieve.

        Returns:
            dict:
                - On success: {"success": True, "data": RequestInfo}
                - On failure: {"success": False, "error": "Request not found"}

        Constraints:
            - The request_id must exist in the system.
        """
        if request_id not in self.requests:
            return {"success": False, "error": "Request not found"}

        return {"success": True, "data": self.requests[request_id]}

    def list_requests_by_ids(self, request_ids: list[str]) -> dict:
        """
        Retrieve request information for multiple requests based on their request_ids.

        Args:
            request_ids (list[str]): The list of request IDs to query.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RequestInfo]  # List of request info for existing requests only (empty if none found)
                }

        Notes:
            - Only returns info for request IDs that exist in the system.
            - If input list is empty or none found, returns success with empty list.
            - No error is returned for missing IDs; they are silently skipped.
        """
        if not isinstance(request_ids, list):
            return { "success": False, "error": "request_ids must be a list of request ID strings" }
    
        # Filter and collect only those request IDs that exist
        result = [
            self.requests[req_id]
            for req_id in request_ids
            if req_id in self.requests
        ]
        return { "success": True, "data": result }

    def get_requester_by_id(self, requester_id: str) -> dict:
        """
        Retrieve the details of a requester given their requester_id.

        Args:
            requester_id (str): Unique identifier of the requester.

        Returns:
            dict: {
                "success": True,
                "data": RequesterInfo  # Dict of requester's info (name, contact_info, department, etc.)
            }
            OR
            {
                "success": False,
                "error": str  # Error message if the requester is not found
            }

        Constraints:
            - requester_id must exist in the system.
        """
        requester = self.requesters.get(requester_id)
        if requester is None:
            return { "success": False, "error": "Requester not found" }
        return { "success": True, "data": requester }

    def list_all_requests(self) -> dict:
        """
        Retrieve information for all requests in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[RequestInfo],  # List of all RequestInfo entries in the system (may be empty if no requests)
            }
        """
        return {
            "success": True,
            "data": list(self.requests.values())
        }

    def list_requests_by_status(self, status: str) -> dict:
        """
        Retrieve all requests that have the specified status.

        Args:
            status (str): The status value to filter requests by. Must be one of the allowed statuses.

        Returns:
            dict:
              - On success:
                  {
                      "success": True,
                      "data": List[RequestInfo]  # All requests with the given status (may be empty)
                  }
              - On failure (invalid status):
                  {
                      "success": False,
                      "error": "Invalid status"
                  }

        Constraints:
            - status must be from the predefined allowed status set.
        """
        if status not in VALID_REQUEST_STATUSES:
            return {"success": False, "error": "Invalid status"}

        filtered_requests = [
            req for req in self.requests.values()
            if req["status"] == status
        ]
        return {"success": True, "data": filtered_requests}

    def list_requests_by_requester(self, requester_id: str) -> dict:
        """
        Retrieve all requests associated with a specific requester ID.

        Args:
            requester_id (str): The requester whose requests should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[RequestInfo],  # All RequestInfo dicts with requester_id equal to input (may be empty)
            }
            or {
                "success": False,
                "error": str  # Reason, e.g., requester not found
            }

        Constraints:
            - The requester_id must exist in the system.
        """
        if requester_id not in self.requesters:
            return { "success": False, "error": "Requester not found" }

        result = [
            request_info for request_info in self.requests.values()
            if request_info["requester_id"] == requester_id
        ]
        return { "success": True, "data": result }

    def get_request_status(self, request_id: str) -> dict:
        """
        Retrieve the current status of a request given its ID.

        Args:
            request_id (str): Unique identifier of the request.

        Returns:
            dict: {
                "success": True,
                "data": str  # Status of the request
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. request not found
            }

        Constraints:
            - The given request_id must exist in the system.
        """
        request = self.requests.get(request_id)
        if not request:
            return { "success": False, "error": "Request not found" }
        return { "success": True, "data": request["status"] }

    def create_request(
        self,
        request_id: str,
        status: str,
        description: str,
        requester_id: str
    ) -> dict:
        """
        Create a new request.

        Args:
            request_id (str): Unique identifier for the request.
            status (str): Status of the request. Must be one of allowed statuses.
            description (str): Description of the request.
            requester_id (str): ID of requester, must exist in system.

        Returns:
            dict:
                - On success: {"success": True, "message": "Request created successfully"}
                - On error: {"success": False, "error": <error message>}

        Constraints:
            - request_id must be unique.
            - status must be in allowed set.
            - requester_id must exist in self.requesters.
            - created_timestamp and updated_timestamp are both set to now (ISO string).
        """

        # Check that request_id is unique
        if request_id in self.requests:
            return {"success": False, "error": "Request ID already exists"}

        # Check that status is valid
        if status not in VALID_REQUEST_STATUSES:
            return {
                "success": False,
                "error": (
                    f"Status '{status}' is not valid. "
                    f"Allowed: {sorted(VALID_REQUEST_STATUSES)}"
                ),
            }

        # Check that requester_id exists
        if requester_id not in self.requesters:
            return {"success": False, "error": "Requester ID does not exist"}

        # Set timestamps
        now_str = datetime.utcnow().isoformat()

        new_request: RequestInfo = {
            "request_id": request_id,
            "status": status,
            "description": description,
            "created_timestamp": now_str,
            "updated_timestamp": now_str,
            "requester_id": requester_id
        }

        self.requests[request_id] = new_request

        return {"success": True, "message": "Request created successfully"}


    def update_request_status(self, request_id: str, new_status: str) -> dict:
        """
        Change the status of an existing request, enforcing allowed status values and updating the updated_timestamp.

        Args:
            request_id (str): Unique identifier of the request to update.
            new_status (str): Desired new status ("open", "in progress", "closed", etc.).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Status of request <id> updated to <status>."
                }
                On failure: {
                    "success": False,
                    "error": <description>
                }

        Constraints:
            - request_id must exist.
            - new_status must be in the allowed status set.
            - updated_timestamp must accurately reflect the update.
        """

        if request_id not in self.requests:
            return { "success": False, "error": "Request ID does not exist" }
        if new_status not in VALID_REQUEST_STATUSES:
            return {
                "success": False,
                "error": f"Invalid status. Allowed values: {sorted(VALID_REQUEST_STATUSES)}",
            }
    
        self.requests[request_id]["status"] = new_status
        self.requests[request_id]["updated_timestamp"] = datetime.utcnow().isoformat()

        return {
            "success": True,
            "message": f"Status of request {request_id} updated to {new_status}."
        }


    def update_request_description(self, request_id: str, new_description: str) -> dict:
        """
        Modify the description of a request by request_id and update its updated_timestamp.

        Args:
            request_id (str): Unique identifier of the request to modify.
            new_description (str): The new description string to set.

        Returns:
            dict:
                On success: {"success": True, "message": "Request description updated."}
                On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - The request with request_id must exist.
            - The updated_timestamp should be set to the current time (ISO format).
        """
        req = self.requests.get(request_id)
        if not req:
            return { "success": False, "error": "Request not found" }

        req['description'] = new_description
        req['updated_timestamp'] = datetime.utcnow().isoformat()
        return { "success": True, "message": "Request description updated." }

    def delete_request(self, request_id: str) -> dict:
        """
        Remove an existing request from the system.

        Args:
            request_id (str): The unique identifier of the request to delete.

        Returns:
            dict: 
                - { "success": True, "message": "Request <request_id> deleted successfully." }
                - { "success": False, "error": "Request not found." }

        Constraints:
            - The request must exist in the system (request_id in self.requests).
        """
        if request_id not in self.requests:
            return { "success": False, "error": "Request not found." }

        del self.requests[request_id]
        return { "success": True, "message": f"Request {request_id} deleted successfully." }

    def add_requester(
        self,
        requester_id: str,
        name: str,
        contact_info: str,
        department: str
    ) -> dict:
        """
        Add a new requester entity with all required non-null information.

        Args:
            requester_id (str): Unique identifier for the requester.
            name (str): Name of the requester (must be non-null and non-empty).
            contact_info (str): Contact information (must be non-null and non-empty).
            department (str): Department (must be non-null and non-empty).

        Returns:
            dict:
                On success: { "success": True, "message": "Requester added successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - requester_id must be unique.
            - All fields must be non-null and non-empty.
        """
        # Check for uniqueness
        if requester_id in self.requesters:
            return { "success": False, "error": "Requester ID already exists" }

        # Validate required fields are non-null and not empty strings
        for field_name, field_value in [
            ("requester_id", requester_id),
            ("name", name),
            ("contact_info", contact_info),
            ("department", department)
        ]:
            if field_value is None or str(field_value).strip() == "":
                return { "success": False, "error": f"Field '{field_name}' must be non-null and non-empty" }

        # Add the requester
        requester_info: RequesterInfo = {
            "requester_id": requester_id,
            "name": name,
            "contact_info": contact_info,
            "department": department
        }
        self.requesters[requester_id] = requester_info

        return { "success": True, "message": "Requester added successfully" }

    def update_requester_info(
        self, 
        requester_id: str, 
        name: str = None,
        contact_info: str = None,
        department: str = None
    ) -> dict:
        """
        Edit requester information (name, contact_info, department).

        Args:
            requester_id (str): ID of the requester to update.
            name (str, optional): New name for the requester.
            contact_info (str, optional): New contact info for the requester.
            department (str, optional): New department for the requester.

        Returns:
            dict:
                On success: { "success": True, "message": "Requester info updated." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - requester_id must exist in the system.
            - At least one of name, contact_info, department must be provided (not None).
        """
        # Check existence
        if requester_id not in self.requesters:
            return { "success": False, "error": "Requester ID does not exist." }
    
        # Check at least one updatable field provided
        if name is None and contact_info is None and department is None:
            return { "success": False, "error": "No update fields provided." }
    
        # Update fields if provided
        updated = False
        if name is not None:
            self.requesters[requester_id]['name'] = name
            updated = True
        if contact_info is not None:
            self.requesters[requester_id]['contact_info'] = contact_info
            updated = True
        if department is not None:
            self.requesters[requester_id]['department'] = department
            updated = True
    
        # If somehow nothing updated (no-op), still return success
        return { "success": True, "message": "Requester info updated." }


class RequestTrackingSystem(BaseEnv):
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

    def get_request_by_id(self, **kwargs):
        return self._call_inner_tool('get_request_by_id', kwargs)

    def list_requests_by_ids(self, **kwargs):
        return self._call_inner_tool('list_requests_by_ids', kwargs)

    def get_requester_by_id(self, **kwargs):
        return self._call_inner_tool('get_requester_by_id', kwargs)

    def list_all_requests(self, **kwargs):
        return self._call_inner_tool('list_all_requests', kwargs)

    def list_requests_by_status(self, **kwargs):
        return self._call_inner_tool('list_requests_by_status', kwargs)

    def list_requests_by_requester(self, **kwargs):
        return self._call_inner_tool('list_requests_by_requester', kwargs)

    def get_request_status(self, **kwargs):
        return self._call_inner_tool('get_request_status', kwargs)

    def create_request(self, **kwargs):
        return self._call_inner_tool('create_request', kwargs)

    def update_request_status(self, **kwargs):
        return self._call_inner_tool('update_request_status', kwargs)

    def update_request_description(self, **kwargs):
        return self._call_inner_tool('update_request_description', kwargs)

    def delete_request(self, **kwargs):
        return self._call_inner_tool('delete_request', kwargs)

    def add_requester(self, **kwargs):
        return self._call_inner_tool('add_requester', kwargs)

    def update_requester_info(self, **kwargs):
        return self._call_inner_tool('update_requester_info', kwargs)
