# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    manager_id: str
    budget_amount: float
    status: str

class EmployeeInfo(TypedDict):
    employee_id: str
    full_name: str
    position: str
    department_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Departments: {department_id: DepartmentInfo}
        # State space: department_id, name, manager_id, budget_amount, status
        self.departments: Dict[str, DepartmentInfo] = {}

        # Employees: {employee_id: EmployeeInfo}
        # State space: employee_id, full_name, position, department_id
        self.employees: Dict[str, EmployeeInfo] = {}

        # Constraints:
        # - Each department must have a unique name.
        # - Each department has at most one assigned manager.
        # - Budget allocations must be non-negative.
        # - Only active employees may be assigned as managers.
        # - Departments must have a budget allocated on creation.
        # - Employees can manage at most one department at a time.
        self._is_employee_active_state = None

    def _resolve_employee_active(self, employee_id: str) -> dict:
        employee = self.employees.get(employee_id)
        if not employee:
            return {"success": False, "error": "Employee not found"}

        state = self._is_employee_active_state
        if isinstance(state, dict):
            if employee_id in state:
                return {"success": True, "data": bool(state[employee_id])}
        elif isinstance(state, str):
            lowered = state.strip().lower()
            if lowered in {"true", "false"}:
                return {"success": True, "data": lowered == "true"}
        elif isinstance(state, bool):
            return {"success": True, "data": state}

        status = employee.get("status", "active")
        return {"success": True, "data": str(status).lower() == "active"}

    def get_department_by_name(self, name: str) -> dict:
        """
        Retrieve the details of a department by its unique name.

        Args:
            name (str): The unique name of the department to query.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": DepartmentInfo  # Department information dictionary
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Department not found"
                    }

        Constraints:
            - Department names are unique; will match at most one department.
        """
        for dept_info in self.departments.values():
            if dept_info["name"] == name:
                return { "success": True, "data": dept_info }
        return { "success": False, "error": "Department not found" }

    def get_department_by_id(self, department_id: str) -> dict:
        """
        Retrieve department details by department_id.

        Args:
            department_id (str): The unique identifier for the department.

        Returns:
            dict: {
                "success": True,
                "data": DepartmentInfo
            }
            or
            {
                "success": False,
                "error": "Department not found"
            }

        Constraints:
            - department_id must exist in the system.
        """
        department = self.departments.get(department_id)
        if department is None:
            return {"success": False, "error": "Department not found"}
        return {"success": True, "data": department}

    def get_department_budget(self, department_id: str = None, name: str = None) -> dict:
        """
        Retrieve the budget_amount for a specified department by department_id or name.

        Args:
            department_id (str, optional): The unique identifier of the department.
            name (str, optional): The name of the department.

        Returns:
            dict: 
                { "success": True, "data": <budget_amount (float)> }
                or 
                { "success": False, "error": <error_message> }

        Constraints:
            - At least one of department_id or name must be provided.
            - Department name is globally unique.
        """
        # Validate input
        if not department_id and not name:
            return { "success": False, "error": "Either department_id or name must be provided." }
    
        dept = None

        # Prefer department_id if provided
        if department_id:
            dept = self.departments.get(department_id)
            if not dept:
                return { "success": False, "error": "Department with given id does not exist." }
        elif name:
            for d in self.departments.values():
                if d["name"] == name:
                    dept = d
                    break
            if not dept:
                return { "success": False, "error": "Department with given name does not exist." }

        # (Possible additional check: status is 'deleted'?)
        return { "success": True, "data": dept["budget_amount"] }

    def list_departments(self) -> dict:
        """
        List all departments and their details (department_id, name, manager_id, budget_amount, status).

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[DepartmentInfo]  # List may be empty if no departments exist
            }
        """
        departments_list = list(self.departments.values())
        return { "success": True, "data": departments_list }

    def get_department_manager(self, department_id: str) -> dict:
        """
        Retrieve the manager's employee information for the given department.

        Args:
            department_id (str): The unique identifier of the department.

        Returns:
            dict: {
                "success": True,
                "data": EmployeeInfo  # Manager information for department
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. department not found or no manager assigned
            }

        Constraints:
            - Department must exist.
            - Department must have a manager assigned.
        """
        # Check if department exists
        dept = self.departments.get(department_id)
        if not dept:
            return { "success": False, "error": "Department not found" }
    
        manager_id = dept.get("manager_id")
        if not manager_id:
            return { "success": False, "error": "Manager not assigned for this department" }

        manager = self.employees.get(manager_id)
        if not manager:
            return { "success": False, "error": "Manager information not found in employees" }

        return { "success": True, "data": manager }

    def is_department_name_unique(self, name: str) -> dict:
        """
        Check whether a given department name is unique (not currently in use).

        Args:
            name (str): Department name to check.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if unique, False if in use
                }

        Note:
            - Name uniqueness is enforced across all departments, regardless of status.
            - Name comparison is case-sensitive unless further specified.
        """
        for dept in self.departments.values():
            if dept["name"] == name:
                return {"success": True, "data": False}
        return {"success": True, "data": True}

    def get_employee_by_name(self, full_name: str) -> dict:
        """
        Retrieve an employee's information by their full name.

        Args:
            full_name (str): The full name of the employee.

        Returns:
            dict: 
                If one match: {
                    "success": True,
                    "data": EmployeeInfo
                }
                If zero matches or ambiguous name: {
                    "success": False,
                    "error": "No employee found with the given name" or "Multiple employees found with the given name"
                }

        Notes/Constraints:
            - Employee names are not guaranteed to be unique; error is returned if multiple matches found.
        """
        matches = [emp for emp in self.employees.values() if emp["full_name"] == full_name]

        if not matches:
            return { "success": False, "error": "No employee found with the given name" }
        if len(matches) > 1:
            return { "success": False, "error": "Multiple employees found with the given name" }
        return { "success": True, "data": matches[0] }

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve an employee's information from the system given the employee_id.

        Args:
            employee_id (str): The unique identifier of the employee.

        Returns:
            dict: {
                "success": True,
                "data": EmployeeInfo  # information of the found employee
            }
            or
            {
                "success": False,
                "error": "Employee not found"  # if the given ID does not exist
            }

        Constraints:
            - No constraints affect this query operation; simply lookup by key.
        """
        employee = self.employees.get(employee_id)
        if not employee:
            return {"success": False, "error": "Employee not found"}
        return {"success": True, "data": employee}

    def list_employees(self) -> dict:
        """
        List all employees and their current department assignments.

        Args:
            None

        Returns:
            dict: {
               "success": True,
               "data": List[EmployeeInfo]  # all employee entries (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.employees.values())
        }

    def is_employee_active(self, employee_id: str) -> dict:
        """
        Check if the specified employee is active (eligible to be assigned as a manager).

        Args:
            employee_id (str): Unique ID of the employee to check.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool,  # True if employee is active, False otherwise
                }
                or
                {
                    "success": False,
                    "error": str  # If employee does not exist or status attribute missing
                }

        Constraints:
            - Only active employees may be assigned as managers.
            - Employee must exist.
            - If active status cannot be determined, treat as not active.
        """
        return self._resolve_employee_active(employee_id)

    def get_employee_managed_department(self, employee_id: str) -> dict:
        """
        Determine which department (if any) the given employee is managing.
    
        Args:
            employee_id (str): The unique ID of the employee.
    
        Returns:
            dict:
                - success: True if query processed; False if employee not found.
                - data: DepartmentInfo if the employee manages a department, else None.
                - error: Only present if employee does not exist.
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee does not exist"}

        for dept in self.departments.values():
            if dept["manager_id"] == employee_id:
                return {"success": True, "data": dept}

        return {"success": True, "data": None}

    def list_active_employees(self) -> dict:
        """
        List all employees currently eligible to be assigned as managers
        (i.e., employees with 'active' status if such a status attribute exists;
        otherwise, returns all employees).

        Returns:
            dict:
            {
                "success": True,
                "data": List[EmployeeInfo]  # active employees only, or all if no 'status' info
            }
            OR
            {
                "success": False,
                "error": str  # description of error
            }

        Constraints:
            - If EmployeeInfo records have 'status' or 'active' fields, only return those matching 'active'.
            - If there is no such field, return all employees.
        """
        # Check if there are any employees:
        if not self.employees:
            return {"success": True, "data": []}

        # Determine if employee status field exists
        example_employee = next(iter(self.employees.values()))
        status_field = None
        for key in example_employee:
            if key.lower() == "status":
                status_field = key
                break
            if key.lower() == "active":
                status_field = key
                break

        # Filter only by 'active' status if such field exists
        if status_field:
            active_emps = [
                emp for emp in self.employees.values()
                if str(emp.get(status_field, "")).lower() == "active"
            ]
        else:
            active_emps = list(self.employees.values())

        return {"success": True, "data": active_emps}

    def create_department(self,
                         name: str,
                         manager_id: str,
                         budget_amount: float,
                         status: str) -> dict:
        """
        Establish a new department with the specified name, manager, budget, and status.

        Args:
            name (str): Proposed department name. Must be unique across all departments.
            manager_id (str): Employee to assign as manager. Use an empty string to create the department without an initial manager; a non-empty manager must be active and must not already manage another department.
            budget_amount (float): Initial budget allocation. Must be zero or positive.
            status (str): Initial lifecycle status ("active","inactive", etc.)

        Returns:
            dict: {
                "success": True,
                "message": str,
                "department_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Department name must be unique.
            - Budget amount must be non-negative.
            - Manager (if specified) must be an existing (and active) employee not already managing another department.
            - Each manager can only manage at most one department at a time.
        """
        # Check unique name
        if any(dept['name'] == name for dept in self.departments.values()):
            return {"success": False, "error": "Department name must be unique"}

        # Check budget
        if not isinstance(budget_amount, (int, float)) or budget_amount < 0:
            return {"success": False, "error": "Budget amount must be non-negative"}

        # Check manager_id validity and eligibility if a manager is provided.
        if manager_id:
            if manager_id not in self.employees:
                return {"success": False, "error": "Manager does not exist"}
            status_check = self._resolve_employee_active(manager_id)
            if (not status_check.get("success")) or (not status_check.get("data", False)):
                return {"success": False, "error": "Manager is not active"}

            if any(dept.get('manager_id') == manager_id for dept in self.departments.values()):
                return {"success": False, "error": "Employee is already managing another department"}

        # Generate unique department_id (can do simple auto-increment or UUID)
        department_id = str(uuid.uuid4())

        department_info: DepartmentInfo = {
            "department_id": department_id,
            "name": name,
            "manager_id": manager_id,
            "budget_amount": float(budget_amount),
            "status": status
        }

        self.departments[department_id] = department_info

        return {
            "success": True,
            "message": f"Department '{name}' created successfully.",
            "department_id": department_id
        }

    def assign_department_manager(self, department_id: str, employee_id: str) -> dict:
        """
        Assign an eligible employee as the manager of a department.

        Args:
            department_id (str): ID of the department to assign the manager to.
            employee_id (str): ID of the employee to assign as manager.

        Returns:
            dict: 
                On success: { "success": True, "message": "Employee X assigned as manager for department Y." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - The department must exist and be active.
            - The employee must exist and be active.
            - The employee must not already manage any department.
            - Each department can have at most one assigned manager.
        """
        # Check department existence
        dept = self.departments.get(department_id)
        if dept is None:
            return {"success": False, "error": "Department does not exist."}
        if dept["status"].lower() != "active":
            return {"success": False, "error": "Department is not active."}

        # Check employee existence
        emp = self.employees.get(employee_id)
        if emp is None:
            return {"success": False, "error": "Employee does not exist."}

        # Auxiliary: check if employee is active
        # Let's assume that "active" might be encoded, e.g., as a status field on EmployeeInfo.
        # As per provided definition, EmployeeInfo has no status. But as the constraint dictates,
        # We will assume that "position" being non-empty and employee being present means active.
        # But more robustly, suppose EmployeeInfo has a 'status' field in actual implementation.

        # If is_employee_active op exists, use it in code:
        status_check = self._resolve_employee_active(employee_id)
        if (not status_check.get("success")) or (not status_check.get("data", False)):
            return {"success": False, "error": "Employee is not active."}

        # Employee must not already manage another department
        for d in self.departments.values():
            if d.get("manager_id") == employee_id:
                return {"success": False, "error": "Employee already manages another department."}

        # Assign as manager
        prev_manager_id = dept.get("manager_id")
        self.departments[department_id]["manager_id"] = employee_id

        return {
            "success": True,
            "message": f"Employee {employee_id} assigned as manager for department {department_id}."
        }

    def remove_department_manager(self, department_id: str) -> dict:
        """
        Remove the current manager from a department.

        Args:
            department_id (str): The unique identifier of the department.

        Returns:
            dict:
                - On success: { "success": True, "message": "Manager removed from department <department_id>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The department must exist.
            - If the department currently has no manager assigned, returns failure.
        """
        dept = self.departments.get(department_id)
        if dept is None:
            return { "success": False, "error": "Department does not exist" }

        if not dept.get("manager_id"):
            return { "success": False, "error": "Department currently has no manager assigned" }

        dept["manager_id"] = ""
        # Update the departments state (in place is sufficient since dicts are mutable)
        self.departments[department_id] = dept

        return { "success": True, "message": f"Manager removed from department {department_id}" }

    def update_department_budget(self, department_id: str, new_budget_amount: float) -> dict:
        """
        Change the budget allocation of a department. The new budget must be non-negative.

        Args:
            department_id (str): The ID of the department whose budget is to be changed.
            new_budget_amount (float): The new budget value. Must be non-negative.

        Returns:
            dict: {
                "success": True,
                "message": "Budget for department <name> updated to <amount>."
            }
            or
            {
                "success": False,
                "error": "Description of the failure."
            }

        Constraints:
            - department_id must exist in the system.
            - new_budget_amount >= 0
        """
        dept = self.departments.get(department_id)
        if not dept:
            return { "success": False, "error": f"Department with id '{department_id}' does not exist." }
        if new_budget_amount < 0:
            return { "success": False, "error": "Budget allocation must be non-negative." }
        dept['budget_amount'] = float(new_budget_amount)
        return {
            "success": True,
            "message": f"Budget for department '{dept['name']}' updated to {float(new_budget_amount)}."
        }

    def rename_department(self, department_id: str, new_name: str) -> dict:
        """
        Rename a department to a new unique name.

        Args:
            department_id (str): ID of the department to rename.
            new_name (str): The new unique department name.

        Returns:
            dict: {
                "success": True,
                "message": "Department renamed from <old_name> to <new_name>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Department ID must exist.
            - New name must be unique among all departments.
        """
        # Check if department exists
        dept = self.departments.get(department_id)
        if not dept:
            return {"success": False, "error": "Department not found"}

        # Check if new_name is different
        old_name = dept["name"]
        if new_name == old_name:
            return {"success": True, "message": f"Department name is already '{new_name}'"}

        # Check uniqueness of new_name
        for d in self.departments.values():
            if d["name"] == new_name:
                return {"success": False, "error": "A department with this name already exists"}

        # Apply name change
        dept["name"] = new_name
        self.departments[department_id] = dept

        return {
            "success": True,
            "message": f"Department renamed from '{old_name}' to '{new_name}'"
        }

    def update_department_status(self, department_id: str, new_status: str) -> dict:
        """
        Change the lifecycle status of a department (active, inactive, deleted).

        Args:
            department_id (str): The identifier of the department to update.
            new_status (str): The new status value, must be one of "active", "inactive", "deleted".

        Returns:
            dict: {
                "success": True,
                "message": "Department status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - department must exist.
            - new_status must be one of: "active", "inactive", "deleted".
        """
        allowed_statuses = {"active", "inactive", "deleted"}

        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": "Invalid status. Must be one of 'active', 'inactive', 'deleted'."}

        self.departments[department_id]["status"] = new_status

        return {"success": True, "message": f"Department status updated to {new_status}."}

    def reallocate_manager(self, employee_id: str, new_department_id: str) -> dict:
        """
        Change which department an employee manages, respecting constraints:
          - An employee can manage at most one department.
          - Only active employees may be assigned as managers.
          - A department can have at most one assigned manager.
    
        Args:
            employee_id (str): The ID of the employee to be reassigned as a manager.
            new_department_id (str): The ID of the department to assign as manager.
    
        Returns:
            dict: {
                "success": True,
                "message": "Employee <eid> reassigned as manager to department <did>."
            }
            or failure dict:
            {
                "success": False,
                "error": <description>
            }
        """
        # Check employee exists
        employee = self.employees.get(employee_id)
        if not employee:
            return {"success": False, "error": "Employee does not exist."}
    
        # Assume 'active' status means 'position' field is not 'inactive' or similar.
        # But there's no explicit 'status' field for employees; check anyway.
        status_check = self._resolve_employee_active(employee_id)
        if (not status_check.get("success")) or (not status_check.get("data", False)):
            return {"success": False, "error": "Employee is not active and cannot be assigned as manager."}
    
        # Check new department exists
        new_department = self.departments.get(new_department_id)
        if not new_department:
            return {"success": False, "error": "Target department does not exist."}
    
        # Check if this department already has a manager (and if so, is it the same employee?)
        current_manager_id = new_department.get("manager_id")
        if current_manager_id and current_manager_id != "" and current_manager_id != employee_id:
            return {"success": False, "error": "Target department already has a different manager."}
    
        # Check if employee is already managing another department and (if so) remove as manager
        # (assuming employee can only manage 1 at a time)
        for dept in self.departments.values():
            if dept.get("manager_id") == employee_id:
                dept["manager_id"] = ""
    
        # Assign employee as manager to new department
        new_department["manager_id"] = employee_id

        return {
            "success": True,
            "message": f"Employee {employee_id} reassigned as manager to department {new_department_id}."
        }

    def delete_department(self, department_id: str) -> dict:
        """
        Mark a department as deleted by updating its status to 'deleted'.
    
        Args:
            department_id (str): The unique identifier for the department to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Department <name> marked as deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Department must exist.
            - If already deleted, return error and do not repeat.
            - Department is not physically removed; only 'status' is set to 'deleted'.
        """
        dept = self.departments.get(department_id)
        if not dept:
            return {"success": False, "error": "Department does not exist."}
        if dept["status"].lower() == "deleted":
            return {"success": False, "error": f"Department '{dept['name']}' is already marked as deleted."}
        # Mark as deleted
        dept["status"] = "deleted"
        self.departments[department_id] = dept
        return {"success": True, "message": f"Department '{dept['name']}' marked as deleted."}

    def transfer_employee(self, employee_id: str, target_department_id: str) -> dict:
        """
        Move an employee from their current department to another department.

        Args:
            employee_id (str): ID of the employee to transfer.
            target_department_id (str): ID of the department to transfer the employee to.

        Returns:
            dict: {
                "success": True,
                "message": <success_message>
            } on success,
            {
                "success": False,
                "error": <reason>
            } on failure.

        Constraints:
            - employee_id must exist.
            - target_department_id must exist.
            - Employee must not already be in the target department.
        """
        # Check employee exists
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee ID does not exist"}

        # Check target department exists
        if target_department_id not in self.departments:
            return {"success": False, "error": "Target department ID does not exist"}

        employee_info = self.employees[employee_id]

        # Are they already in this department?
        if employee_info["department_id"] == target_department_id:
            return {"success": False, "error": "Employee is already in the target department"}

        # Perform transfer
        old_department_id = employee_info["department_id"]
        self.employees[employee_id]["department_id"] = target_department_id

        return {
            "success": True,
            "message": f"Employee {employee_id} transferred from department {old_department_id} to {target_department_id}."
        }

    def add_employee(
        self, 
        employee_id: str, 
        full_name: str, 
        position: str, 
        department_id: str
    ) -> dict:
        """
        Add a new employee to the system.

        Args:
            employee_id (str): Unique identifier for the employee.
            full_name (str): Full name of the employee.
            position (str): Position or job title.
            department_id (str): The department the employee belongs to.

        Returns:
            dict: {
                "success": True,
                "message": "Employee added successfully"
            }
            or
            {
                "success": False,
                "error": <str error reason>
            }

        Constraints:
            - employee_id must be unique within the system.
            - department_id must refer to an existing department.
        """
        if employee_id in self.employees:
            return { "success": False, "error": "Employee with this ID already exists." }

        if department_id not in self.departments:
            return { "success": False, "error": "Department does not exist." }

        self.employees[employee_id] = {
            "employee_id": employee_id,
            "full_name": full_name,
            "position": position,
            "department_id": department_id
        }
        return { "success": True, "message": "Employee added successfully" }

    def update_employee_info(self, employee_id: str, full_name: str = None, position: str = None, department_id: str = None) -> dict:
        """
        Modify the details (full_name, position, department_id) of an existing employee.

        Args:
            employee_id (str): The ID of the employee to modify.
            full_name (str, optional): New full name for the employee.
            position (str, optional): New position for the employee.
            department_id (str, optional): New department ID to assign the employee.

        Returns:
            dict: {
                "success": True,
                "message": "Employee information updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - employee_id must exist in the system.
            - If department_id is specified, it must exist in the departments.
            - At least one of the fields must be provided for update.
        """
        # Check employee existence
        if employee_id not in self.employees:
            return { "success": False, "error": "Employee not found." }

        if full_name is None and position is None and department_id is None:
            return { "success": False, "error": "No update fields provided." }

        employee = self.employees[employee_id]

        # Update fields if provided
        if full_name is not None:
            if not isinstance(full_name, str) or full_name.strip() == "":
                return { "success": False, "error": "Invalid full name." }
            employee["full_name"] = full_name.strip()

        if position is not None:
            if not isinstance(position, str) or position.strip() == "":
                return { "success": False, "error": "Invalid position." }
            employee["position"] = position.strip()

        if department_id is not None:
            if department_id not in self.departments:
                return { "success": False, "error": "Target department does not exist." }
            employee["department_id"] = department_id

        # Save changes
        self.employees[employee_id] = employee

        return { "success": True, "message": "Employee information updated." }

    def remove_employee(self, employee_id: str) -> dict:
        """
        Remove an employee from the system.

        Args:
            employee_id (str): The ID of the employee to remove.

        Returns:
            dict: 
              - success=True, with message on successful removal.
              - success=False, with error if the employee does not exist.

        Constraints:
            - If the employee is assigned as manager in any department, 
              set the department's manager_id to "" upon removal to maintain referential integrity.
            - Other attributes or references to the employee must not remain in the system.
        """
        if employee_id not in self.employees:
            return { "success": False, "error": "Employee not found" }

        # Unset as manager in any department
        for dept in self.departments.values():
            if dept.get("manager_id") == employee_id:
                dept["manager_id"] = ""

        del self.employees[employee_id]
        return { "success": True, "message": f"Employee {employee_id} removed from system" }


class OrganizationalDepartmentManagementSystem(BaseEnv):
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
            if key == "is_employee_active":
                env._is_employee_active_state = copy.deepcopy(value)
                continue
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

    def get_department_by_id(self, **kwargs):
        return self._call_inner_tool('get_department_by_id', kwargs)

    def get_department_budget(self, **kwargs):
        return self._call_inner_tool('get_department_budget', kwargs)

    def list_departments(self, **kwargs):
        return self._call_inner_tool('list_departments', kwargs)

    def get_department_manager(self, **kwargs):
        return self._call_inner_tool('get_department_manager', kwargs)

    def is_department_name_unique(self, **kwargs):
        return self._call_inner_tool('is_department_name_unique', kwargs)

    def get_employee_by_name(self, **kwargs):
        return self._call_inner_tool('get_employee_by_name', kwargs)

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def list_employees(self, **kwargs):
        return self._call_inner_tool('list_employees', kwargs)

    def is_employee_active(self, **kwargs):
        return self._call_inner_tool('is_employee_active', kwargs)

    def get_employee_managed_department(self, **kwargs):
        return self._call_inner_tool('get_employee_managed_department', kwargs)

    def list_active_employees(self, **kwargs):
        return self._call_inner_tool('list_active_employees', kwargs)

    def create_department(self, **kwargs):
        return self._call_inner_tool('create_department', kwargs)

    def assign_department_manager(self, **kwargs):
        return self._call_inner_tool('assign_department_manager', kwargs)

    def remove_department_manager(self, **kwargs):
        return self._call_inner_tool('remove_department_manager', kwargs)

    def update_department_budget(self, **kwargs):
        return self._call_inner_tool('update_department_budget', kwargs)

    def rename_department(self, **kwargs):
        return self._call_inner_tool('rename_department', kwargs)

    def update_department_status(self, **kwargs):
        return self._call_inner_tool('update_department_status', kwargs)

    def reallocate_manager(self, **kwargs):
        return self._call_inner_tool('reallocate_manager', kwargs)

    def delete_department(self, **kwargs):
        return self._call_inner_tool('delete_department', kwargs)

    def transfer_employee(self, **kwargs):
        return self._call_inner_tool('transfer_employee', kwargs)

    def add_employee(self, **kwargs):
        return self._call_inner_tool('add_employee', kwargs)

    def update_employee_info(self, **kwargs):
        return self._call_inner_tool('update_employee_info', kwargs)

    def remove_employee(self, **kwargs):
        return self._call_inner_tool('remove_employee', kwargs)
