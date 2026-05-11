# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Union
from time import time
import time



class ComplaintCaseInfo(TypedDict):
    complaint_id: str
    customer_id: str
    status: str
    creation_timestamp: Union[str, float]
    resolution_timestamp: Union[str, float]
    assigned_employee_id: str

class ComplaintActionInfo(TypedDict):
    action_id: str
    complaint_id: str
    action_type: str
    action_timestamp: Union[str, float]
    employee_id: str
    action_detail: str

class EmployeeInfo(TypedDict):
    employee_id: str
    name: str
    role: str

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_information: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for customer complaint management.
        """

        # Complaint cases: {complaint_id: ComplaintCaseInfo}
        self.complaint_cases: Dict[str, ComplaintCaseInfo] = {}
        # Complaint actions: {action_id: ComplaintActionInfo}
        self.complaint_actions: Dict[str, ComplaintActionInfo] = {}
        # Employees: {employee_id: EmployeeInfo}
        self.employees: Dict[str, EmployeeInfo] = {}
        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Constraints:
        # - Each ComplaintCase must have a unique complaint_id.
        # - Each ComplaintAction must be linked to a valid ComplaintCase and Employee.
        # - ComplaintCase status must reflect a valid progression ("open", "in progress", "resolved", "closed").
        # - All actions must be timestamped and recorded in chronological order for each complaint.
        # - Once a ComplaintCase is resolved or closed, no further actions may be added unless reopened.

    def _get_effective_now(self):
        for field_name in ("current_time", "current_timestamp", "mock_current_time"):
            value = getattr(self, field_name, None)
            if value not in (None, ""):
                return value
        return time.time()

    @staticmethod
    def _timestamp_sort_key(value):
        if isinstance(value, (int, float)):
            return (0, float(value))
        if isinstance(value, str):
            try:
                return (0, datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
            except Exception:
                try:
                    return (0, float(value))
                except Exception:
                    return (1, value)
        return (1, str(value))

    def get_complaint_case_by_id(self, complaint_id: str) -> dict:
        """
        Retrieve the ComplaintCase information using its unique complaint_id.

        Args:
            complaint_id (str): The unique ID of the complaint case to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ComplaintCaseInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., case not found
            }

        Constraints:
            - The complaint_id must exist in the system.
        """
        case = self.complaint_cases.get(complaint_id)
        if case is None:
            return { "success": False, "error": "Complaint case not found" }
        return { "success": True, "data": case }

    def list_complaint_cases_by_customer(self, customer_id: str) -> dict:
        """
        List all ComplaintCases associated with a given customer_id.

        Args:
            customer_id (str): The ID of the customer.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ComplaintCaseInfo],  # List may be empty if no cases for customer
                    }
                - On failure (invalid customer_id):
                    {
                        "success": False,
                        "error": str,  # e.g. "Customer does not exist"
                    }

        Constraints:
            - customer_id must exist in the system.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}
        result = [
            case_info
            for case_info in self.complaint_cases.values()
            if case_info["customer_id"] == customer_id
        ]
        return {"success": True, "data": result}

    def list_complaint_cases_by_status(self, status: str) -> dict:
        """
        Retrieve all ComplaintCases filtered by their status.

        Args:
            status (str): The status to filter complaint cases by. Must be one of "open", "in progress", "resolved", or "closed".

        Returns:
            dict: {
                "success": True,
                "data": List[ComplaintCaseInfo],  # List of matching cases (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g. invalid status)
            }

        Constraints:
            - Status must be a valid complaint status ("open", "in progress", "resolved", "closed").
        """

        valid_statuses = {"open", "in progress", "resolved", "closed"}

        if not isinstance(status, str) or status.lower() not in valid_statuses:
            return { "success": False, "error": "Invalid status. Must be one of: open, in progress, resolved, closed." }

        filtered_cases = [
            case_info for case_info in self.complaint_cases.values()
            if case_info["status"].lower() == status.lower()
        ]
        return { "success": True, "data": filtered_cases }

    def get_all_complaint_actions_for_case(self, complaint_id: str) -> dict:
        """
        Retrieve all ComplaintActions linked to a specific complaint_id, sorted chronologically.

        Args:
            complaint_id (str): The ID of the complaint case.

        Returns:
            dict: {
                "success": True,
                "data": List[ComplaintActionInfo]  # sorted by action_timestamp ascending
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Complaint case not found"
            }

        Constraints:
            - The complaint_id must refer to an existing ComplaintCase.
            - Actions are sorted in increasing chronological order (by action_timestamp).
        """
        if complaint_id not in self.complaint_cases:
            return { "success": False, "error": "Complaint case not found" }

        actions = [
            action for action in self.complaint_actions.values()
            if action["complaint_id"] == complaint_id
        ]

        # Sort by action_timestamp - supports both float and (sortable) str timestamps.
        actions_sorted = sorted(
            actions,
            key=lambda act: act["action_timestamp"]
        )

        return { "success": True, "data": actions_sorted }

    def get_complaint_action_by_id(self, action_id: str) -> dict:
        """
        Retrieve a specific ComplaintAction by its action_id.

        Args:
            action_id (str): The unique identifier for the complaint action.

        Returns:
            dict: {
                "success": True,
                "data": ComplaintActionInfo
            }
            or
            {
                "success": False,
                "error": str  # Error message if action_id does not exist
            }
        """
        if action_id not in self.complaint_actions:
            return {
                "success": False,
                "error": "Action ID does not exist"
            }
        return {
            "success": True,
            "data": self.complaint_actions[action_id]
        }

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve Employee information using employee_id.

        Args:
            employee_id (str): The unique identifier of the employee.

        Returns:
            dict: {
                "success": True,
                "data": EmployeeInfo
            }
            or
            {
                "success": False,
                "error": "Employee not found"
            }

        Constraints:
            - Employee must exist in the system.
        """
        employee = self.employees.get(employee_id)
        if not employee:
            return { "success": False, "error": "Employee not found" }
        return { "success": True, "data": employee }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve Customer information using the specified customer ID.

        Args:
            customer_id (str): Unique identifier for the customer.

        Returns:
            dict: {
                "success": True,
                "data": CustomerInfo  # The customer information
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., "Customer not found"
            }

        Constraints:
            - The customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def get_assigned_employee_for_case(self, complaint_id: str) -> dict:
        """
        Retrieves the Employee information assigned to the specified ComplaintCase.

        Args:
            complaint_id (str): Unique identifier for the complaint case.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": EmployeeInfo  # Information of the assigned employee
                  }
                - On failure (case or employee missing): {
                    "success": False,
                    "error": str  # Reason for failure
                  }

        Constraints:
            - complaint_id must exist in the system.
            - The complaint case must have an assigned_employee_id that matches an employee in the system.
        """
        case = self.complaint_cases.get(complaint_id)
        if not case:
            return {"success": False, "error": "Complaint case does not exist."}

        assigned_employee_id = case.get("assigned_employee_id")
        if not assigned_employee_id:
            return {"success": False, "error": "No employee assigned to this complaint case."}

        employee = self.employees.get(assigned_employee_id)
        if not employee:
            return {"success": False, "error": "Assigned employee not found in the system."}

        return {"success": True, "data": employee}

    def get_complaint_case_status(self, complaint_id: str) -> dict:
        """
        Retrieve the current status ("open", "in progress", "resolved", "closed") of a ComplaintCase.

        Args:
            complaint_id (str): The unique identifier of the complaint case.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": <status: str>
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Complaint case not found"
                    }

        Constraints:
            - complaint_id must exist in the system.

        """
        case = self.complaint_cases.get(complaint_id)
        if case is None:
            return { "success": False, "error": "Complaint case not found" }
        return { "success": True, "data": case["status"] }

    def get_resolution_timeline_for_case(self, complaint_id: str) -> dict:
        """
        Produce a chronological (timestamped) list of all actions and status transitions for a ComplaintCase.
    
        Args:
            complaint_id (str): ID of the complaint case.
    
        Returns:
            dict: 
            - On success:
                {
                    "success": True,
                    "data": List[dict],   # Each dict: { "timestamp": ..., "event_type": ..., ... }
                }
            - On failure:
                {
                    "success": False,
                    "error": str,
                }
    
        Constraints:
          - ComplaintCase must exist.
          - All linked actions (by complaint_id) are included.
          - Status transitions at case creation and resolution/closure are included.
        """
        # Verify complaint case exists
        case = self.complaint_cases.get(complaint_id)
        if not case:
            return {"success": False, "error": "Complaint case not found"}

        case_actions = [
            action for action in self.complaint_actions.values()
            if action["complaint_id"] == complaint_id
        ]
        timeline = []
        creation_actor = case.get("created_by_employee_id", "")
        if creation_actor in (None, "") and case_actions:
            creation_actor = min(case_actions, key=lambda action: action["action_timestamp"]).get("employee_id", "")

        # Add initial case creation event (status is typically 'open')
        timeline.append({
            "timestamp": case["creation_timestamp"],
            "event_type": "status_change",
            "status": "open",  # At creation/init
            "description": "Complaint case created",
            "actor": creation_actor
        })

        # Collect all actions for the case and populate as timeline events
        for action in case_actions:
            timeline.append({
                "timestamp": action["action_timestamp"],
                "event_type": "action",
                "action_id": action["action_id"],
                "action_type": action["action_type"],
                "employee_id": action["employee_id"],
                "description": action["action_detail"]
            })

        # Try to reconstruct explicit status transitions (creation and resolution/closure for sure)
        # If resolution_timestamp exists, add as a status transition
        if case.get("resolution_timestamp"):
            timeline.append({
                "timestamp": case["resolution_timestamp"],
                "event_type": "status_change",
                "status": case["status"],
                "description": f"Complaint case marked as '{case['status']}'",
                "actor": case.get("assigned_employee_id", None)
            })

        # (Optionally, more refined status transitions can be listed if such histories are stored)

        # Sort timeline by timestamp (ascending order)
        timeline_sorted = sorted(timeline, key=lambda x: self._timestamp_sort_key(x["timestamp"]))

        return {
            "success": True,
            "data": timeline_sorted
        }

    def check_action_link_validity(self, action_id: str) -> dict:
        """
        Verify if a ComplaintAction is linked to valid ComplaintCase and Employee references.

        Args:
            action_id (str): The ID of the ComplaintAction to validate.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "complaint_id_valid": bool,
                            "employee_id_valid": bool
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Description of why validation could not be performed
                    }

        Constraints:
            - The ComplaintAction must exist.
            - Validity checked as:
                - complaint_id must exist in complaint_cases.
                - employee_id must exist in employees.
        """
        action = self.complaint_actions.get(action_id)
        if not action:
            return { "success": False, "error": "ComplaintAction does not exist" }

        complaint_id = action.get("complaint_id")
        employee_id = action.get("employee_id")

        complaint_valid = complaint_id in self.complaint_cases
        employee_valid = employee_id in self.employees

        return {
            "success": True,
            "data": {
                "complaint_id_valid": complaint_valid,
                "employee_id_valid": employee_valid
            }
        }

    def is_action_addable_to_case(self, complaint_id: str) -> dict:
        """
        Check if a new ComplaintAction can be added to the ComplaintCase identified by complaint_id.

        Args:
            complaint_id (str): The ID of the complaint case.

        Returns:
            dict:
                If complaint_id is valid:
                    {
                        "success": True,
                        "addable": bool,
                        "reason": str  # Explanation if not addable
                    }
                If complaint_id invalid:
                    {
                        "success": False,
                        "error": "Complaint case not found"
                    }
        Constraints:
            - ComplaintCase must exist.
            - If the status is "resolved" or "closed", actions cannot be added unless reopened.
            - If status is "open" or "in progress", actions may be added.
        """
        case = self.complaint_cases.get(complaint_id)
        if not case:
            return {
                "success": False,
                "error": "Complaint case not found"
            }
    
        status = case.get("status", "").lower()
        if status in ["resolved", "closed"]:
            return {
                "success": True,
                "addable": False,
                "reason": "Cannot add actions when status is resolved or closed unless reopened."
            }
        # We assume that all other statuses ("open", "in progress") are addable.
        return {
            "success": True,
            "addable": True,
            "reason": "Actions may be added in the current status."
        }

    def add_complaint_action(
        self,
        action_id: str,
        complaint_id: str,
        action_type: str,
        action_timestamp: 'Union[str, float]',
        employee_id: str,
        action_detail: str
    ) -> dict:
        """
        Add a new ComplaintAction (call, email, meeting, refund, etc.) for a given complaint_id and employee_id.

        Args:
            action_id (str): Unique identifier for the action.
            complaint_id (str): ID of the complaint to which this action belongs.
            action_type (str): Type of action ("call", "email", "meeting", "refund", etc.).
            action_timestamp (str|float): ISO timestamp or unix float.
            employee_id (str): The employee performing the action.
            action_detail (str): Details about the action.

        Returns:
            dict:
                On success: { "success": True, "message": "ComplaintAction <action_id> added to ComplaintCase <complaint_id>." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The complaint_id must exist.
            - The employee_id must exist.
            - action_id must not already exist.
            - ComplaintCase status must not be "resolved" or "closed".
            - action_timestamp must be >= any existing action_timestamp for this complaint (chronological order).
        """
        # Check action_id uniqueness
        if action_id in self.complaint_actions:
            return { "success": False, "error": f"Action ID '{action_id}' already exists." }

        # Check complaint existence
        complaint = self.complaint_cases.get(complaint_id)
        if not complaint:
            return { "success": False, "error": f"ComplaintCase '{complaint_id}' does not exist." }

        # Check employee existence
        if employee_id not in self.employees:
            return { "success": False, "error": f"Employee '{employee_id}' does not exist." }

        # Check complaint status
        if complaint["status"] in ["resolved", "closed"]:
            return {
                "success": False,
                "error": f"Cannot add action to ComplaintCase '{complaint_id}' with status '{complaint['status']}'."
            }

        # Chronological order: find latest action timestamp for this complaint
        case_actions = [
            a for a in self.complaint_actions.values() if a["complaint_id"] == complaint_id
        ]
        if case_actions:
            # Use float for timestamp comparison if possible, else compare as str
            def _to_float(ts):
                try:
                    return float(ts)
                except Exception:
                    return ts
            latest_action_ts = max(case_actions, key=lambda a: _to_float(a["action_timestamp"]))["action_timestamp"]
            if _to_float(action_timestamp) < _to_float(latest_action_ts):
                return {
                    "success": False,
                    "error": "Action timestamp must not be earlier than previous actions for this complaint."
                }

        # All constraints satisfied, add action
        new_action = {
            "action_id": action_id,
            "complaint_id": complaint_id,
            "action_type": action_type,
            "action_timestamp": action_timestamp,
            "employee_id": employee_id,
            "action_detail": action_detail
        }
        self.complaint_actions[action_id] = new_action
        return {
            "success": True,
            "message": f"ComplaintAction '{action_id}' added to ComplaintCase '{complaint_id}'."
        }


    def update_complaint_case_status(self, complaint_id: str, new_status: str) -> dict:
        """
        Change the status of a ComplaintCase, enforcing valid status progressions.

        Args:
            complaint_id (str): The ID of the ComplaintCase to update.
            new_status (str): The target status ("open", "in progress", "resolved", "closed").

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Status updated to '<new_status>' for complaint_id '<complaint_id>'."}
                On failure:
                    {"success": False, "error": "<reason>"}
    
        Constraints:
            - complaint_id must exist.
            - new_status must be in allowed statuses.
            - Valid status progression enforced:
              * "open" -> "in progress"
              * "in progress" -> "resolved"
              * "resolved" -> "closed"
            - Cannot step backwards except via explicit "reopen_complaint_case".
            - Setting to "resolved" or "closed" updates 'resolution_timestamp' to now.
        """

        allowed_statuses = ["open", "in progress", "resolved", "closed"]
        valid_transitions = {
            "open": ["in progress"],
            "in progress": ["resolved"],
            "resolved": ["closed"],
            # "closed": ["open"]  # Only allowed by 'reopen_complaint_case'
        }

        if complaint_id not in self.complaint_cases:
            return {"success": False, "error": f"ComplaintCase with id '{complaint_id}' does not exist."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Must be one of {allowed_statuses}."}
    
        current_status = self.complaint_cases[complaint_id]["status"]

        # Enforce valid transition
        if current_status == new_status:
            return {"success": True, "message": f"Status is already '{new_status}' for complaint_id '{complaint_id}'."}

        if current_status not in valid_transitions or new_status not in valid_transitions.get(current_status, []):
            return {
                "success": False,
                "error": f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed: {valid_transitions.get(current_status,[])}"
            }

        # Set new status
        self.complaint_cases[complaint_id]["status"] = new_status

        # Set resolution_timestamp if now resolved/closed
        if new_status in ["resolved", "closed"]:
            self.complaint_cases[complaint_id]["resolution_timestamp"] = self._get_effective_now()

        return {"success": True, "message": f"Status updated to '{new_status}' for complaint_id '{complaint_id}'."}

    def assign_employee_to_complaint_case(self, complaint_id: str, employee_id: str) -> dict:
        """
        Update the employee assignment for a specified ComplaintCase.

        Args:
            complaint_id (str): The ID of the complaint case to update.
            employee_id (str): The ID of the employee to assign.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Employee <employee_id> assigned to complaint <complaint_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error description>
                    }

        Constraints:
            - The complaint_id must exist in self.complaint_cases.
            - The employee_id must exist in self.employees.
        """
        if complaint_id not in self.complaint_cases:
            return { "success": False, "error": f"Complaint case {complaint_id} does not exist." }
        if employee_id not in self.employees:
            return { "success": False, "error": f"Employee {employee_id} does not exist." }

        self.complaint_cases[complaint_id]["assigned_employee_id"] = employee_id
        return {
            "success": True,
            "message": f"Employee {employee_id} assigned to complaint {complaint_id}."
        }

    def reopen_complaint_case(self, complaint_id: str) -> dict:
        """
        Reopen a previously resolved/closed ComplaintCase so that further actions may be added.

        Args:
            complaint_id (str): The unique ID of the complaint case to reopen.

        Returns:
            dict: {
                "success": True,
                "message": "Complaint case <complaint_id> reopened."
            }
            or
            {
                "success": False,
                "error": str
            }
        
        Constraints:
            - The complaint must exist.
            - Status must be "resolved" or "closed".
            - On success, set status to "open".
            - (Optionally) The resolution_timestamp is not cleared unless specified.
        """
        case = self.complaint_cases.get(complaint_id)
        if not case:
            return {"success": False, "error": "Complaint case does not exist."}
    
        if case["status"] not in ("resolved", "closed"):
            return {"success": False, "error": f"Complaint case is not resolved or closed (current status: {case['status']})."}
    
        case["status"] = "open"
        # Optionally leave resolution_timestamp as is (history)
        return {"success": True, "message": f"Complaint case {complaint_id} reopened."}

    def modify_complaint_action_details(
        self,
        action_id: str,
        action_type: str = None,
        action_timestamp: Union[str, float] = None,
        action_detail: str = None
    ) -> dict:
        """
        Edit details (action_type, action_timestamp, action_detail) of an existing ComplaintAction,
        if allowed by current ComplaintCase status and system rules.

        Args:
            action_id (str): The ComplaintAction to edit.
            action_type (str, optional): New action_type (if updating).
            action_timestamp (str or float, optional): New timestamp (if updating).
            action_detail (str, optional): New detailed description (if updating).

        Returns:
            dict: On success: { "success": True, "message": "ComplaintAction {action_id} updated successfully." }
                  On failure: { "success": False, "error": "reason" }

        Constraints:
            - The action must exist and must be linked to a valid ComplaintCase.
            - Modifications are forbidden if the ComplaintCase is "resolved" or "closed".
            - If action_timestamp is changed, chronological ordering of actions for this complaint must be preserved.
            - At least one updatable field must be provided.
        """
        # Check if action exists
        action = self.complaint_actions.get(action_id)
        if not action:
            return { "success": False, "error": f"ComplaintAction {action_id} does not exist." }

        complaint_id = action["complaint_id"]
        case = self.complaint_cases.get(complaint_id)
        if not case:
            return { "success": False, "error": f"Linked ComplaintCase {complaint_id} does not exist." }

        if case["status"] in ("resolved", "closed"):
            return { "success": False, "error": "Cannot modify actions for resolved or closed complaints." }

        # Check at least one field is attempted to be updated
        if action_type is None and action_timestamp is None and action_detail is None:
            return { "success": False, "error": "No update fields provided." }

        # Prepare potential new action data for checks
        new_action_type = action["action_type"] if action_type is None else action_type
        new_action_timestamp = action["action_timestamp"] if action_timestamp is None else action_timestamp
        new_action_detail = action["action_detail"] if action_detail is None else action_detail

        # If timestamp is being changed, validate chronological order among all actions for this complaint
        if action_timestamp is not None:
            # Find all actions linked to this complaint, sort by timestamp
            related_actions = [
                a for a in self.complaint_actions.values() if a["complaint_id"] == complaint_id and a["action_id"] != action_id
            ]
            # Convert all timestamps to float for comparison (assume float as canonical)
            try:
                new_ts = float(new_action_timestamp)
            except Exception:
                return { "success": False, "error": "Invalid new action_timestamp format." }

            for a in related_actions:
                try:
                    other_ts = float(a["action_timestamp"])
                except Exception:
                    return { "success": False, "error": "Invalid existing action_timestamp format." }
                # Chronological consistency: the action order is preserved.
                # For each other action, its timestamp must not be greater than the new timestamp if it comes before,
                # nor less if it comes after (keep stable ordering)
                if other_ts > new_ts and a["action_id"] < action_id:
                    return { "success": False, "error": "Changing timestamp would break chronological order (action earlier than previous actions)." }
                if other_ts < new_ts and a["action_id"] > action_id:
                    return { "success": False, "error": "Changing timestamp would break chronological order (action later than following actions)." }
                # NOTE: In reality, for strict chronological order, we might sort all and check order. For now, we keep logic simple.

        # Perform the updates
        if action_type is not None:
            action["action_type"] = action_type
        if action_timestamp is not None:
            action["action_timestamp"] = action_timestamp
        if action_detail is not None:
            action["action_detail"] = action_detail

        self.complaint_actions[action_id] = action  # Save back (though dict is mutable, standardize to write)

        return { "success": True, "message": f"ComplaintAction {action_id} updated successfully." }

    def delete_complaint_action(self, action_id: str) -> dict:
        """
        Remove an existing ComplaintAction, if permitted by constraints.
    
        Args:
            action_id (str): The ID of the ComplaintAction to delete.
    
        Returns:
            dict: 
              - On success: { "success": True, "message": "Complaint action <action_id> deleted successfully." }
              - On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - If the action_id does not exist, fail.
            - Cannot delete actions if the related ComplaintCase status is 'resolved' or 'closed'.
            - Cannot delete crucial historical records (interpreted as the sole action for the case).
        """
        # Check if the action exists
        if action_id not in self.complaint_actions:
            return { "success": False, "error": f"ComplaintAction '{action_id}' does not exist." }
    
        action = self.complaint_actions[action_id]
        complaint_id = action['complaint_id']
    
        # Check if the related complaint case exists
        if complaint_id not in self.complaint_cases:
            return { "success": False, "error": f"Linked ComplaintCase '{complaint_id}' does not exist." }
    
        complaint_case = self.complaint_cases[complaint_id]
        case_status = complaint_case['status'].lower()
        if case_status in ['resolved', 'closed']:
            return { "success": False, "error": f"Cannot delete actions for complaint case '{complaint_id}' because it is '{case_status}'." }
    
        # Find all actions for this complaint
        actions_for_case = [a for a in self.complaint_actions.values() if a['complaint_id'] == complaint_id]
        if len(actions_for_case) == 1:
            return { "success": False, "error": "Cannot delete the only historical action for a complaint case." }
    
        # Allow deletion
        del self.complaint_actions[action_id]
        return { "success": True, "message": f"Complaint action '{action_id}' deleted successfully." }

    def add_new_complaint_case(
        self,
        complaint_id: str,
        customer_id: str,
        assigned_employee_id: str = "",
        status: str = "open",
        creation_timestamp: 'Union[str, float]' = None,
        resolution_timestamp: 'Union[str, float]' = None
    ) -> dict:
        """
        Create and register a new ComplaintCase.
    
        Args:
            complaint_id (str): Unique identifier for the new case.
            customer_id (str): ID of the customer submitting the complaint (must exist).
            assigned_employee_id (str, optional): ID of the assigned employee (must exist if provided; can be empty/unassigned).
            status (str, optional): Initial status ('open' by default; must be valid starting status).
            creation_timestamp (str|float, optional): Timestamp of creation; autogenerated if None.
            resolution_timestamp (str|float, optional): Set only for immediate resolution; usually None on creation.

        Returns:
            dict:
                {"success": True, "message": "..."} on success;
                {"success": False, "error": "..."} on failure.

        Constraints:
            - Complaint ID must be unique.
            - Customer ID must exist.
            - assigned_employee_id must exist if provided (and not empty).
            - Status must be a valid starting status ('open', optionally 'in progress').
            - creation_timestamp auto-set if not provided.
        """

        # Unique complaint_id
        if complaint_id in self.complaint_cases:
            return {"success": False, "error": "complaint_id already exists"}

        # Valid customer
        if customer_id not in self.customers:
            return {"success": False, "error": "customer_id does not exist"}

        # Status
        valid_statuses = ["open", "in progress", "resolved", "closed"]
        starting_statuses = ["open", "in progress"]
        if status not in valid_statuses or status not in starting_statuses:
            return {
                "success": False,
                "error": f"Invalid initial status '{status}'. Must be one of {starting_statuses}"
            }

        # Employee (allow unassigned/empty)
        if assigned_employee_id and assigned_employee_id not in self.employees:
            return {"success": False, "error": "assigned_employee_id does not exist"}

        # Timestamp handling
        if creation_timestamp is None:
            creation_timestamp = self._get_effective_now()
        # Resolution usually empty at creation
        if not resolution_timestamp:
            resolution_timestamp = ""

        # Compose ComplaintCaseInfo
        case_info: ComplaintCaseInfo = {
            "complaint_id": complaint_id,
            "customer_id": customer_id,
            "status": status,
            "creation_timestamp": creation_timestamp,
            "resolution_timestamp": resolution_timestamp,
            "assigned_employee_id": assigned_employee_id
        }
        self.complaint_cases[complaint_id] = case_info
        return {"success": True, "message": f"Complaint case {complaint_id} created successfully."}

    def delete_complaint_case(self, complaint_id: str) -> dict:
        """
        Permanently remove a ComplaintCase and all related ComplaintActions.

        Args:
            complaint_id (str): The unique complaint case ID to delete.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "message": "ComplaintCase <id> and related actions deleted."
                    }
                - If complaint case not found:
                    {
                        "success": False,
                        "error": "ComplaintCase not found."
                    }

        Constraints:
            - Must ensure all related ComplaintActions are also removed.
            - If ComplaintCase does not exist, return an error.
            - No dangling actions should remain referencing the given complaint_id.
            - Admin-level operation, but permission not checked here.
        """
        if complaint_id not in self.complaint_cases:
            return { "success": False, "error": "ComplaintCase not found." }

        # Delete all actions related to this complaint_id
        actions_to_delete = [action_id for action_id, action in self.complaint_actions.items()
                             if action["complaint_id"] == complaint_id]
        for action_id in actions_to_delete:
            del self.complaint_actions[action_id]

        # Delete the complaint case
        del self.complaint_cases[complaint_id]

        return {
            "success": True,
            "message": f"ComplaintCase {complaint_id} and related actions deleted."
        }

    def update_complaint_case_assignment(self, complaint_id: str, employee_id: str) -> dict:
        """
        Change the assigned employee for a specific complaint case.

        Args:
            complaint_id (str): The ID of the complaint to update.
            employee_id (str): The new employee's ID to assign to the complaint.

        Returns:
            dict: {
                "success": True,
                "message": "Assigned employee <employee_id> to complaint case <complaint_id>."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., complaint or employee not found)
            }

        Constraints:
            - The complaint_id must exist in the system.
            - The employee_id must refer to a valid employee.
        """
        if complaint_id not in self.complaint_cases:
            return { "success": False, "error": "Complaint case does not exist" }
        if employee_id not in self.employees:
            return { "success": False, "error": "Employee does not exist" }
    
        self.complaint_cases[complaint_id]['assigned_employee_id'] = employee_id
        return {
            "success": True,
            "message": f"Assigned employee {employee_id} to complaint case {complaint_id}."
        }


class CustomerComplaintManagementSystem(BaseEnv):
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

    def get_complaint_case_by_id(self, **kwargs):
        return self._call_inner_tool('get_complaint_case_by_id', kwargs)

    def list_complaint_cases_by_customer(self, **kwargs):
        return self._call_inner_tool('list_complaint_cases_by_customer', kwargs)

    def list_complaint_cases_by_status(self, **kwargs):
        return self._call_inner_tool('list_complaint_cases_by_status', kwargs)

    def get_all_complaint_actions_for_case(self, **kwargs):
        return self._call_inner_tool('get_all_complaint_actions_for_case', kwargs)

    def get_complaint_action_by_id(self, **kwargs):
        return self._call_inner_tool('get_complaint_action_by_id', kwargs)

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def get_assigned_employee_for_case(self, **kwargs):
        return self._call_inner_tool('get_assigned_employee_for_case', kwargs)

    def get_complaint_case_status(self, **kwargs):
        return self._call_inner_tool('get_complaint_case_status', kwargs)

    def get_resolution_timeline_for_case(self, **kwargs):
        return self._call_inner_tool('get_resolution_timeline_for_case', kwargs)

    def check_action_link_validity(self, **kwargs):
        return self._call_inner_tool('check_action_link_validity', kwargs)

    def is_action_addable_to_case(self, **kwargs):
        return self._call_inner_tool('is_action_addable_to_case', kwargs)

    def add_complaint_action(self, **kwargs):
        return self._call_inner_tool('add_complaint_action', kwargs)

    def update_complaint_case_status(self, **kwargs):
        return self._call_inner_tool('update_complaint_case_status', kwargs)

    def assign_employee_to_complaint_case(self, **kwargs):
        return self._call_inner_tool('assign_employee_to_complaint_case', kwargs)

    def reopen_complaint_case(self, **kwargs):
        return self._call_inner_tool('reopen_complaint_case', kwargs)

    def modify_complaint_action_details(self, **kwargs):
        return self._call_inner_tool('modify_complaint_action_details', kwargs)

    def delete_complaint_action(self, **kwargs):
        return self._call_inner_tool('delete_complaint_action', kwargs)

    def add_new_complaint_case(self, **kwargs):
        return self._call_inner_tool('add_new_complaint_case', kwargs)

    def delete_complaint_case(self, **kwargs):
        return self._call_inner_tool('delete_complaint_case', kwargs)

    def update_complaint_case_assignment(self, **kwargs):
        return self._call_inner_tool('update_complaint_case_assignment', kwargs)
