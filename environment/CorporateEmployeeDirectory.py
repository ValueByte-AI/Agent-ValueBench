# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



# TypedDicts for all entities
class EmployeeInfo(TypedDict):
    employee_id: str
    name: str
    department_id: str
    role_id: str
    office_id: str
    contact_detail: str

class DepartmentInfo(TypedDict):
    department_id: str
    department_name: str

class OfficeInfo(TypedDict):
    office_id: str
    office_location: str

class RoleInfo(TypedDict):
    role_id: str
    role_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Employees: {employee_id: EmployeeInfo}
        self.employees: Dict[str, EmployeeInfo] = {}

        # Departments: {department_id: DepartmentInfo}
        self.departments: Dict[str, DepartmentInfo] = {}

        # Offices: {office_id: OfficeInfo}
        self.offices: Dict[str, OfficeInfo] = {}

        # Roles: {role_id: RoleInfo}
        self.roles: Dict[str, RoleInfo] = {}

        # Constraints:
        # - Each employee must belong to one department and one office location.
        # - Contact details must be unique for each employee.
        # - Employee records must be searchable and filterable by department and office location.

    def get_department_by_name(self, department_name: str) -> dict:
        """
        Retrieve department details (including department_id) using the department name.

        Args:
            department_name (str): The name of the department to search for.

        Returns:
            dict: {
                "success": True,
                "data": DepartmentInfo  # The matching department's details
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., department not found)
            }

        Constraints:
            - The department name must exist in the directory.
        """
        for dept in self.departments.values():
            if dept["department_name"] == department_name:
                return { "success": True, "data": dept }
        return { "success": False, "error": "Department not found" }

    def get_office_by_location(self, office_location: str) -> dict:
        """
        Retrieve office details (including office_id) by office location name.

        Args:
            office_location (str): The location name of the office to search for.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": OfficeInfo,  # Found office's info
                }
                OR
                {
                    "success": False,
                    "error": str  # E.g. "Office location not found"
                }

        Constraints:
            - Office location must exist in the directory.
        """
        if not office_location:
            return { "success": False, "error": "Office location not found" }

        for office in self.offices.values():
            if office.get("office_location") == office_location:
                return { "success": True, "data": office }
    
        return { "success": False, "error": "Office location not found" }

    def list_employees_by_department_and_office(self, department_id: str, office_id: str) -> dict:
        """
        Retrieve a list of employees who belong to a specific department and are based in a specific office.

        Args:
            department_id (str): The department's unique identifier.
            office_id (str): The office's unique identifier.

        Returns:
            dict: 
              Success: {
                  "success": True,
                  "data": List[EmployeeInfo]  # possibly empty if no employees match
              }
              Failure: {
                  "success": False,
                  "error": str  # e.g. 'Department not found' or 'Office not found'
              }

        Constraints:
            - Department and office must exist.
            - Only employees matching both department and office are listed.
        """
        if department_id not in self.departments:
            return { "success": False, "error": "Department not found" }
        if office_id not in self.offices:
            return { "success": False, "error": "Office not found" }

        employees = [
            emp for emp in self.employees.values()
            if emp['department_id'] == department_id and emp['office_id'] == office_id
        ]

        return { "success": True, "data": employees }

    def get_employee_contact_details(self, employee_id: str) -> dict:
        """
        Retrieves the contact details for a given employee based on their employee_id.

        Args:
            employee_id (str): The unique employee identifier.

        Returns:
            dict: {
                "success": True,
                "data": str  # The contact detail for the employee
            }
            or
            {
                "success": False,
                "error": str  # Error description if employee is not found
            }

        Constraints:
            - The employee must exist in the directory.
        """
        employee = self.employees.get(employee_id)
        if not employee:
            return { "success": False, "error": "Employee does not exist" }
        return { "success": True, "data": employee["contact_detail"] }

    def list_all_employees(self) -> dict:
        """
        Return the complete list of all employees with their main details.

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],  # All employees, may be empty
            }

        Notes:
            - If no employees exist, returns an empty list with success.
        """
        employees_list = list(self.employees.values())
        return { "success": True, "data": employees_list }

    def list_departments(self) -> dict:
        """
        Return a list of all departments in the organization.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[DepartmentInfo],  # List of departments, empty if none exist
                }
        """
        departments_list = list(self.departments.values())
        return { "success": True, "data": departments_list }

    def list_offices(self) -> dict:
        """
        Return a list of all office locations (OfficeInfo dicts).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[OfficeInfo]  # A list of all office records (may be empty if no offices exist)
            }
        """
        data = list(self.offices.values())
        return { "success": True, "data": data }

    def list_roles(self) -> dict:
        """
        Return a list of all roles/job functions in the corporate employee directory.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RoleInfo],  # May be empty if no roles defined
                }

        Constraints:
            None for this operation. All roles are returned as stored in the directory.
        """
        roles_list = list(self.roles.values())
        return { "success": True, "data": roles_list }

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve the full details of an employee by their unique employee_id.

        Args:
            employee_id (str): The unique identifier for the employee.

        Returns:
            dict: 
                { "success": True, "data": EmployeeInfo }
                or
                { "success": False, "error": "Employee not found" }

        Constraints:
            - employee_id must correspond to an existing employee.
            - Returns all fields in the EmployeeInfo record if found.
        """
        if not employee_id or employee_id not in self.employees:
            return { "success": False, "error": "Employee not found" }

        # Found, return info
        return { "success": True, "data": self.employees[employee_id] }

    def list_employees_by_department(self, department_id: str) -> dict:
        """
        List all employees who belong to the specified department.

        Args:
            department_id (str): The unique identifier of the department to filter employees by.

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],  # List of employees in the department (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of failure reason
            }

        Constraints:
            - department_id must exist in the directory.
            - Returns all employees whose department_id matches the input.
        """
        if department_id not in self.departments:
            return { "success": False, "error": "Department does not exist" }

        result = [
            employee for employee in self.employees.values()
            if employee["department_id"] == department_id
        ]

        return { "success": True, "data": result }

    def list_employees_by_office(self, office_id: str) -> dict:
        """
        Filter and list all employees within the specified office.

        Args:
            office_id (str): The unique identifier for the office location.

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],   # List of employee information (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., office does not exist)
            }

        Constraints:
            - The office with the given office_id must exist.
        """
        if office_id not in self.offices:
            return { "success": False, "error": "Office does not exist" }

        employees_in_office = [
            employee for employee in self.employees.values()
            if employee["office_id"] == office_id
        ]

        return { "success": True, "data": employees_in_office }

    def add_employee(
        self,
        employee_id: str,
        name: str,
        department_id: str,
        office_id: str,
        role_id: str,
        contact_detail: str
    ) -> dict:
        """
        Add a new employee to the directory.

        Args:
            employee_id (str): Unique identifier for the employee.
            name (str): Full name of the employee.
            department_id (str): Department the employee belongs to (must exist).
            office_id (str): Office location (must exist).
            role_id (str): Employee role (must exist).
            contact_detail (str): Unique contact information for the employee.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Employee <employee_id> added." }
                On failure:
                    { "success": False, "error": "<description>" }

        Constraints:
            - employee_id must be unique.
            - contact_detail must be unique.
            - department_id, office_id, and role_id must exist.
            - Each employee must belong to one department and one office.
        """
        if employee_id in self.employees:
            return {"success": False, "error": "Employee ID already exists."}

        if any(e["contact_detail"] == contact_detail for e in self.employees.values()):
            return {"success": False, "error": "Contact detail already in use by another employee."}

        if department_id not in self.departments:
            return {"success": False, "error": "Department ID does not exist."}

        if office_id not in self.offices:
            return {"success": False, "error": "Office ID does not exist."}

        if role_id not in self.roles:
            return {"success": False, "error": "Role ID does not exist."}

        employee_info: EmployeeInfo = {
            "employee_id": employee_id,
            "name": name,
            "department_id": department_id,
            "role_id": role_id,
            "office_id": office_id,
            "contact_detail": contact_detail,
        }

        self.employees[employee_id] = employee_info

        return {"success": True, "message": f"Employee {employee_id} added."}

    def update_employee_info(
        self,
        employee_id: str,
        name: str = None,
        department_id: str = None,
        role_id: str = None,
        office_id: str = None,
        contact_detail: str = None
    ) -> dict:
        """
        Modify an existing employee’s information. Enforces:
          - Updated department_id and office_id must exist in the directory.
          - Updated contact_detail must remain unique in the system.
        Only provided fields are updated; unspecified ones are unchanged.

        Args:
            employee_id (str): Employee to update.
            name (str, optional): New name.
            department_id (str, optional): New department assignment.
            role_id (str, optional): New role assignment.
            office_id (str, optional): New office location.
            contact_detail (str, optional): New unique contact.

        Returns:
            dict: {"success": True, "message": "..."} on success,
                  {"success": False, "error": "..."} on failure.
        """
        # Check if employee exists
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found."}

        emp = self.employees[employee_id]

        # Check department existence
        if department_id is not None and department_id not in self.departments:
            return {"success": False, "error": "Specified department_id does not exist."}

        # Check office existence
        if office_id is not None and office_id not in self.offices:
            return {"success": False, "error": "Specified office_id does not exist."}

        # Check role existence (can be None for optional)
        if role_id is not None and role_id not in self.roles:
            return {"success": False, "error": "Specified role_id does not exist."}

        # If updating contact_detail, check uniqueness
        if (
            contact_detail is not None and
            any(
                e["contact_detail"] == contact_detail and eid != employee_id
                for eid, e in self.employees.items()
            )
        ):
            return {"success": False, "error": "Contact detail must be unique."}

        # At least one field must be supplied to update
        if all(
            x is None for x in [name, department_id, role_id, office_id, contact_detail]
        ):
            return {"success": False, "error": "No fields given to update."}

        # Update fields
        if name is not None:
            emp["name"] = name
        if department_id is not None:
            emp["department_id"] = department_id
        if role_id is not None:
            emp["role_id"] = role_id
        if office_id is not None:
            emp["office_id"] = office_id
        if contact_detail is not None:
            emp["contact_detail"] = contact_detail

        self.employees[employee_id] = emp  # Save back (dict mutability, but explicit)

        return {"success": True, "message": "Employee information updated."}

    def delete_employee(self, employee_id: str) -> dict:
        """
        Remove an employee record from the directory.

        Args:
            employee_id (str): The unique identifier of the employee to be deleted.

        Returns:
            dict: {
                'success': True,
                'message': str  # On successful deletion.
            }
            or
            {
                'success': False,
                'error': str  # If the employee does not exist.
            }

        Constraints:
            - The employee must exist in the directory.
            - This operation does not affect department, office, or role entities.
        """
        if not employee_id or employee_id not in self.employees:
            return {"success": False, "error": "Employee not found."}

        del self.employees[employee_id]
        return {"success": True, "message": f"Employee {employee_id} deleted successfully."}

    def assign_employee_department(self, employee_id: str, department_id: str) -> dict:
        """
        Change the department assignment for an employee.

        Args:
            employee_id (str): The unique identifier for the employee whose department is to be changed.
            department_id (str): The unique identifier for the target department.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Department assignment updated for employee <employee_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The employee must exist.
            - The department must exist.
            - Each employee must belong to exactly one department.
        """
        # Check if the employee exists
        if employee_id not in self.employees:
            return { "success": False, "error": f"Employee '{employee_id}' does not exist" }
        # Check if the department exists
        if department_id not in self.departments:
            return { "success": False, "error": f"Department '{department_id}' does not exist" }

        employee = self.employees[employee_id]
        # Check if the department is already assigned
        if employee["department_id"] == department_id:
            return { "success": True, "message": f"Employee '{employee_id}' is already assigned to department '{department_id}'" }

        # Assign department
        employee["department_id"] = department_id
        return { "success": True, "message": f"Department assignment updated for employee '{employee_id}'" }

    def assign_employee_office(self, employee_id: str, office_id: str) -> dict:
        """
        Change the office assignment for an employee.

        Args:
            employee_id (str): The unique identifier of the employee.
            office_id (str): The unique identifier of the office to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Employee {employee_id} assigned to office {office_id}."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<description of error>"
                    }

        Constraints:
            - Employee must exist.
            - Office must exist.
            - Each employee must belong to one (and only one) office.
        """
        if employee_id not in self.employees:
            return { "success": False, "error": f"Employee with ID '{employee_id}' does not exist." }

        if office_id not in self.offices:
            return { "success": False, "error": f"Office with ID '{office_id}' does not exist." }

        self.employees[employee_id]["office_id"] = office_id

        return {
            "success": True,
            "message": f"Employee {employee_id} assigned to office {office_id}."
        }

    def assign_employee_role(self, employee_id: str, role_id: str) -> dict:
        """
        Change the role assignment for an employee.

        Args:
            employee_id (str): The employee whose role is to be changed.
            role_id (str): The new role_id to assign.

        Returns:
            dict: 
                On success: {"success": True, "message": "Role updated for employee <employee_id>."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The employee must exist in the directory.
            - The target role_id must exist in the system.
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee does not exist"}
        if role_id not in self.roles:
            return {"success": False, "error": "Role does not exist"}

        self.employees[employee_id]['role_id'] = role_id
        return {"success": True, "message": f"Role updated for employee {employee_id}."}


class CorporateEmployeeDirectory(BaseEnv):
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

    def get_department_by_name(self, **kwargs):
        return self._call_inner_tool('get_department_by_name', kwargs)

    def get_office_by_location(self, **kwargs):
        return self._call_inner_tool('get_office_by_location', kwargs)

    def list_employees_by_department_and_office(self, **kwargs):
        return self._call_inner_tool('list_employees_by_department_and_office', kwargs)

    def get_employee_contact_details(self, **kwargs):
        return self._call_inner_tool('get_employee_contact_details', kwargs)

    def list_all_employees(self, **kwargs):
        return self._call_inner_tool('list_all_employees', kwargs)

    def list_departments(self, **kwargs):
        return self._call_inner_tool('list_departments', kwargs)

    def list_offices(self, **kwargs):
        return self._call_inner_tool('list_offices', kwargs)

    def list_roles(self, **kwargs):
        return self._call_inner_tool('list_roles', kwargs)

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def list_employees_by_department(self, **kwargs):
        return self._call_inner_tool('list_employees_by_department', kwargs)

    def list_employees_by_office(self, **kwargs):
        return self._call_inner_tool('list_employees_by_office', kwargs)

    def add_employee(self, **kwargs):
        return self._call_inner_tool('add_employee', kwargs)

    def update_employee_info(self, **kwargs):
        return self._call_inner_tool('update_employee_info', kwargs)

    def delete_employee(self, **kwargs):
        return self._call_inner_tool('delete_employee', kwargs)

    def assign_employee_department(self, **kwargs):
        return self._call_inner_tool('assign_employee_department', kwargs)

    def assign_employee_office(self, **kwargs):
        return self._call_inner_tool('assign_employee_office', kwargs)

    def assign_employee_role(self, **kwargs):
        return self._call_inner_tool('assign_employee_role', kwargs)

