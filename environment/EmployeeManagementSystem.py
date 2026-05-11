# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class ContactDetails(TypedDict, total=False):
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]

class EmployeeInfo(TypedDict):
    employee_id: str
    first_name: str
    last_name: str
    contact_details: ContactDetails
    position: str
    department: str
    employment_status: str
    date_of_hire: str  # renamed from date_of_h for clarity

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing employee records.
        """

        # Employees: {employee_id: EmployeeInfo}
        # Maps employee_id to all relevant personal and job-related information.
        self.employees: Dict[str, EmployeeInfo] = {}

        # Constraints:
        # - Each employee must have a unique employee_id (enforced by dict key usage)
        # - employment_status must be one of a predefined set (e.g., active, terminated, on leave)
        # - Contact details must include at least one means of communication (phone or email)
        # - Position and department must correspond to valid entries within the organization

    @staticmethod
    def _normalize_allowed_values(raw_values):
        if raw_values is None:
            return None
        if isinstance(raw_values, str):
            return {part.strip() for part in raw_values.split(",") if part.strip()}
        if isinstance(raw_values, (list, tuple, set)):
            return {str(part).strip() for part in raw_values if str(part).strip()}
        return None

    def list_all_employees(self) -> dict:
        """
        Retrieve the complete list of all employees in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],  # Every employee record. May be empty if none exist.
            }
        Constraints:
            - No constraints are violated or need enforcement for this operation.
        """
        result = list(self.employees.values())
        return { "success": True, "data": result }

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve the detailed employee record for a given employee_id.

        Args:
            employee_id (str): The employee's unique identifier.

        Returns:
            dict: 
                - {"success": True, "data": EmployeeInfo} if found
                - {"success": False, "error": "Employee ID not found"} otherwise

        Constraints:
            - employee_id must exist in the system.
        """
        employee = self.employees.get(employee_id)
        if employee is not None:
            return {"success": True, "data": employee}
        else:
            return {"success": False, "error": "Employee ID not found"}

    def list_employees_by_department(self, department: str) -> dict:
        """
        Retrieve a list of employees filtered by department.

        Args:
            department (str): Department name to filter employees.

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],  # List of matching employees (may be empty)
            }

        Notes:
            - If no employees are found in the specified department, data is an empty list.
            - No error occurs for missing/non-existent departments.
        """
        result = [
            emp for emp in self.employees.values()
            if emp["department"] == department
        ]
        return { "success": True, "data": result }

    def list_employees_by_status(self, employment_status: str) -> dict:
        """
        Retrieve a list of all employees filtered by employment_status.

        Args:
            employment_status (str): Employment status to filter by, e.g., "active", "terminated", "on leave".

        Returns:
            dict: 
                - On success: { "success": True, "data": List[EmployeeInfo] }
                - On error:   { "success": False, "error": str }

        Constraints:
            - employment_status must be a valid predefined status.
        """
        valid_statuses = {"active", "terminated", "on leave"}
        if employment_status not in valid_statuses:
            return { "success": False, "error": "Invalid employment status" }

        data = [
            emp for emp in self.employees.values()
            if emp["employment_status"] == employment_status
        ]

        return { "success": True, "data": data }

    def search_employees_by_name(self, name_query: str) -> dict:
        """
        Find employees by partial or full name match (first_name and/or last_name), case-insensitive.

        Args:
            name_query (str): Partial or full string to search (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo]  # All matching employees, could be empty
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid (e.g., empty query)
            }

        Constraints:
            - name_query must not be empty
            - Match on either first_name or last_name, case-insensitive, partial or full match
        """
        if not name_query or not name_query.strip():
            return { "success": False, "error": "Name query cannot be empty" }

        query = name_query.strip().lower()
        results = []
        for emp in self.employees.values():
            first = emp["first_name"].lower()
            last = emp["last_name"].lower()
            if query in first or query in last:
                results.append(emp)

        return { "success": True, "data": results }

    def get_employee_contact_details(self, employee_id: str) -> dict:
        """
        Retrieve the contact information for a given employee by employee_id.

        Args:
            employee_id (str): Unique identifier of the employee.

        Returns:
            dict: {
                "success": True,
                "data": ContactDetails
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. employee not found
            }

        Constraints:
            - employee_id must exist in the system.
            - Contact details should include at least a phone or email.
        """
        employee = self.employees.get(employee_id)
        if not employee:
            return {"success": False, "error": "Employee not found"}

        contact_details = employee.get("contact_details", {})
        return {"success": True, "data": contact_details}

    def list_all_departments(self) -> dict:
        """
        Get a list of all valid departments within the organization.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Valid department names available in the organization.
            }
        Notes:
            - If the environment provides a `valid_departments` whitelist, return that full
              declared department set so read and write tools share the same organization
              vocabulary.
            - Otherwise, fall back to the department values currently present on employee records.
        """
        valid_departments = self._normalize_allowed_values(getattr(self, "valid_departments", None))
        if valid_departments:
            return {"success": True, "data": sorted(valid_departments)}

        departments = set()
        for emp in self.employees.values():
            if emp.get("department"):
                departments.add(emp["department"])
        return {"success": True, "data": sorted(list(departments))}

    def list_all_positions(self) -> dict:
        """
        Returns a list of all unique positions currently assigned to employees.

        Returns:
            dict: {
                "success": True,
                "data": List[str]    # Unique positions; may be empty if no employees
            }
        Notes:
            - Positions are deduced from current employee records as there is no dedicated position list.
            - Only non-empty and non-null position strings are returned.
        """
        positions = set()
        for emp in self.employees.values():
            pos = emp.get("position", "").strip()
            if pos:
                positions.add(pos)
        return {
            "success": True,
            "data": list(sorted(positions))
        }

    def add_employee(
        self,
        employee_id: str,
        first_name: str,
        last_name: str,
        contact_details: ContactDetails,
        position: str,
        department: str,
        employment_status: str,
        date_of_hire: str
    ) -> dict:
        """
        Add a new employee record to the system.

        Args:
            employee_id (str): Unique identifier for the employee.
            first_name (str): First name of the employee.
            last_name (str): Last name of the employee.
            contact_details (ContactDetails): Employee's contact information, must include at least a phone or email.
            position (str): Position in the organization.
            department (str): Department name.
            employment_status (str): Employment status, must be one of: 'active', 'terminated', 'on leave'.
            date_of_hire (str): Date employee was hired.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - message (str): Success message (if succeeded).
                - error (str): Error description (if failed).

        Constraints:
            - employee_id must be unique.
            - employment_status must be one of predefined set.
            - contact_details must include at least one of phone or email.
            - position and department should be valid (not strictly enforced here).
        """
        valid_statuses = {'active', 'terminated', 'on leave'}

        if employee_id in self.employees:
            return { "success": False, "error": "Employee ID already exists." }
    
        if employment_status not in valid_statuses:
            return { "success": False, "error": "Invalid employment status." }

        if not (contact_details.get("phone") or contact_details.get("email")):
            return { "success": False, "error": "At least a phone or email must be provided in contact details." }

        # Construct and add the employee record
        employee_info: EmployeeInfo = {
            "employee_id": employee_id,
            "first_name": first_name,
            "last_name": last_name,
            "contact_details": contact_details,
            "position": position,
            "department": department,
            "employment_status": employment_status,
            "date_of_hire": date_of_hire
        }

        self.employees[employee_id] = employee_info

        return {
            "success": True,
            "message": f"Employee with ID {employee_id} added."
        }

    def update_employee_info(self, employee_id: str, updates: dict) -> dict:
        """
        Update details of an existing employee.

        Args:
            employee_id (str): The employee's unique identifier.
            updates (dict): Dictionary of fields to update. Allowed keys:
                - first_name
                - last_name
                - contact_details (dict)
                - position
                - department
                - employment_status
                - date_of_hire

        Returns:
            dict: {
                "success": True,
                "message": "Employee info updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - employee_id must exist.
            - employment_status (if present) must be in allowed set.
            - position/department (if present) must be valid.
            - contact_details (if present or if fields cleared) must have at least one means of communication (phone or email).
        """
        # Predefined sets for validation (stub here, should be present in real class)
        ALLOWED_STATUSES = {"active", "terminated", "on leave"}
        valid_departments = self._normalize_allowed_values(getattr(self, "valid_departments", None))
        valid_positions = self._normalize_allowed_values(getattr(self, "valid_positions", None))

        if employee_id not in self.employees:
            return { "success": False, "error": "Employee does not exist" }

        emp = self.employees[employee_id]

        # Validate and update each field
        if "employment_status" in updates:
            if updates["employment_status"] not in ALLOWED_STATUSES:
                return { "success": False, "error": "Invalid employment status" }
            emp["employment_status"] = updates["employment_status"]

        if "position" in updates:
            if valid_positions is not None and updates["position"] not in valid_positions:
                return { "success": False, "error": "Invalid position" }
            emp["position"] = updates["position"]

        if "department" in updates:
            if valid_departments is not None and updates["department"] not in valid_departments:
                return { "success": False, "error": "Invalid department" }
            emp["department"] = updates["department"]

        if "first_name" in updates and updates["first_name"]:
            emp["first_name"] = updates["first_name"]

        if "last_name" in updates and updates["last_name"]:
            emp["last_name"] = updates["last_name"]

        if "date_of_hire" in updates and updates["date_of_hire"]:
            emp["date_of_hire"] = updates["date_of_hire"]

        if "contact_details" in updates:
            contact_details = updates["contact_details"]
            # Apply update on a copy so we can validate first
            proposed_contact = emp["contact_details"].copy()
            proposed_contact.update(contact_details)
            # Validate at least phone or email
            if not (proposed_contact.get("phone") or proposed_contact.get("email")):
                return { "success": False, "error": "Contact details must include at least phone or email" }
            emp["contact_details"].update(contact_details)
        else:
            # If contact_details not in updates, still must ensure at least one remains
            contact = emp["contact_details"]
            if not (contact.get("phone") or contact.get("email")):
                return { "success": False, "error": "Contact details must include at least phone or email" }

        # Commit change
        self.employees[employee_id] = emp
        return { "success": True, "message": "Employee info updated" }

    def update_employee_status(self, employee_id: str, new_status: str) -> dict:
        """
        Change the employment_status of a specific employee, ensuring new_status is valid.

        Args:
            employee_id (str): The ID of the employee whose status should be updated.
            new_status (str): The new status to assign (must be a valid status).

        Returns:
            dict: {
                "success": True,
                "message": "Employment status updated for employee_id <...>"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., employee not found or invalid status
            }

        Constraints:
            - Employment status must be in valid_statuses (e.g., {"active", "terminated", "on leave"})
            - Employee must exist
        """
        # Define valid statuses if not already present
        valid_statuses = {"active", "terminated", "on leave"}

        # Check employee existence
        if employee_id not in self.employees:
            return { "success": False, "error": "Employee not found" }

        # Check status validity
        if new_status not in valid_statuses:
            return { "success": False, "error": "Invalid employment status" }

        # Update and return success
        self.employees[employee_id]["employment_status"] = new_status
        return {
            "success": True,
            "message": f"Employment status updated for employee_id {employee_id}"
        }

    def delete_employee(self, employee_id: str) -> dict:
        """
        Remove an employee record from the system.

        Args:
            employee_id (str): The unique identifier of the employee to delete.

        Returns:
            dict: 
                On success: 
                    {"success": True, "message": "Employee '<employee_id>' deleted successfully."}
                On error:
                    {"success": False, "error": "Employee not found."}

        Constraints:
            - The employee_id must exist in the system to perform deletion.
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found."}
    
        del self.employees[employee_id]
        return {"success": True, "message": f"Employee '{employee_id}' deleted successfully."}

    def update_employee_contact_details(
        self,
        employee_id: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None
    ) -> dict:
        """
        Update the phone, email, or address for a given employee.
        At least one of phone or email must be present after the update.

        Args:
            employee_id (str): ID of the employee to update.
            phone (Optional[str]): New phone number (set None to remove).
            email (Optional[str]): New email address (set None to remove).
            address (Optional[str]): New address (set None to remove).

        Returns:
            dict: {
                "success": True,
                "message": "Employee contact details updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Employee must exist.
            - After update, at least one of phone/email must be present and not empty.
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found."}

        contact = self.employees[employee_id]["contact_details"].copy()

        # Track whether any field is updated; optional, for stricter constraint
        updated_any = False

        if phone is not None:
            if phone == "":
                if "phone" in contact:
                    del contact["phone"]
                    updated_any = True
            else:
                contact["phone"] = phone
                updated_any = True

        if email is not None:
            if email == "":
                if "email" in contact:
                    del contact["email"]
                    updated_any = True
            else:
                contact["email"] = email
                updated_any = True

        if address is not None:
            if address == "":
                if "address" in contact:
                    del contact["address"]
                    updated_any = True
            else:
                contact["address"] = address
                updated_any = True

        # Enforce: At least one means of communication (phone or email)
        phone_ok = "phone" in contact and bool(contact["phone"])
        email_ok = "email" in contact and bool(contact["email"])
        if not (phone_ok or email_ok):
            return {
                "success": False,
                "error": "At least one means of communication (phone or email) must be present for an employee."
            }

        self.employees[employee_id]["contact_details"] = contact

        return {
            "success": True,
            "message": "Employee contact details updated successfully."
        }

    def transfer_employee_department(self, employee_id: str, new_department: str) -> dict:
        """
        Change the department of the specified employee to new_department,
        ensuring the target department is valid.

        Args:
            employee_id (str): The unique ID of the employee to update.
            new_department (str): The department to assign the employee to.

        Returns:
            dict: 
                - On success: 
                    {
                        "success": True,
                        "message": "Employee department updated to <new_department>."
                    }
                - On error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - The employee_id must exist.
            - The new_department must be a valid organization department.
        """

        valid_departments = self._normalize_allowed_values(getattr(self, "valid_departments", None))
        if not valid_departments:
            return { "success": False, "error": "Valid department list is not defined in the system." }

        if employee_id not in self.employees:
            return { "success": False, "error": "Employee with the given ID does not exist." }

        if new_department not in valid_departments:
            return { "success": False, "error": "Target department is not a valid organization department." }

        self.employees[employee_id]["department"] = new_department

        return {
            "success": True,
            "message": f"Employee department updated to {new_department}."
        }

    def change_employee_position(self, employee_id: str, new_position: str) -> dict:
        """
        Update the position (job role) of an employee, ensuring the new position is valid.

        Args:
            employee_id (str): The unique identifier for the employee to update.
            new_position (str): The new job position to assign.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Position updated for employee <employee_id>."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - employee_id must exist in the system.
            - new_position must be a valid position (must exist in self.valid_positions).
        """
        # Check 1: Employee existence
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee does not exist"}

        # Check 2: Position validity
        valid_positions = self._normalize_allowed_values(getattr(self, "valid_positions", None))
        if valid_positions is not None and new_position not in valid_positions:
            return {"success": False, "error": "Invalid position"}
        if valid_positions is None and not str(new_position).strip():
            return {"success": False, "error": "Invalid position"}

        # Update position
        self.employees[employee_id]["position"] = new_position

        return {
            "success": True,
            "message": f"Position updated for employee {employee_id}."
        }


class EmployeeManagementSystem(BaseEnv):
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

    def list_all_employees(self, **kwargs):
        return self._call_inner_tool('list_all_employees', kwargs)

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def list_employees_by_department(self, **kwargs):
        return self._call_inner_tool('list_employees_by_department', kwargs)

    def list_employees_by_status(self, **kwargs):
        return self._call_inner_tool('list_employees_by_status', kwargs)

    def search_employees_by_name(self, **kwargs):
        return self._call_inner_tool('search_employees_by_name', kwargs)

    def get_employee_contact_details(self, **kwargs):
        return self._call_inner_tool('get_employee_contact_details', kwargs)

    def list_all_departments(self, **kwargs):
        return self._call_inner_tool('list_all_departments', kwargs)

    def list_all_positions(self, **kwargs):
        return self._call_inner_tool('list_all_positions', kwargs)

    def add_employee(self, **kwargs):
        return self._call_inner_tool('add_employee', kwargs)

    def update_employee_info(self, **kwargs):
        return self._call_inner_tool('update_employee_info', kwargs)

    def update_employee_status(self, **kwargs):
        return self._call_inner_tool('update_employee_status', kwargs)

    def delete_employee(self, **kwargs):
        return self._call_inner_tool('delete_employee', kwargs)

    def update_employee_contact_details(self, **kwargs):
        return self._call_inner_tool('update_employee_contact_details', kwargs)

    def transfer_employee_department(self, **kwargs):
        return self._call_inner_tool('transfer_employee_department', kwargs)

    def change_employee_position(self, **kwargs):
        return self._call_inner_tool('change_employee_position', kwargs)
