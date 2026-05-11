# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class EmployeeInfo(TypedDict):
    employee_id: str
    name: str
    department: str
    position: str
    status: str

class AppraisalPeriodInfo(TypedDict):
    period_id: str
    start_date: str
    end_date: str
    label: str

class ReviewerInfo(TypedDict):
    reviewer_id: str
    name: str
    position: str

class PerformanceRecordInfo(TypedDict):
    employee_id: str
    period_id: str
    competency: str
    score: float
    reviewer_id: str
    comment: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Employees: {employee_id: EmployeeInfo}
        self.employees: Dict[str, EmployeeInfo] = {}

        # Appraisal Periods: {period_id: AppraisalPeriodInfo}
        self.periods: Dict[str, AppraisalPeriodInfo] = {}

        # Reviewers: {reviewer_id: ReviewerInfo}
        self.reviewers: Dict[str, ReviewerInfo] = {}

        # Performance Records: [PerformanceRecordInfo]
        self.performance_records: List[PerformanceRecordInfo] = []

        # Constraints:
        # - Each PerformanceRecord must be associated with exactly one employee and one appraisal period.
        # - Valid competencies are predefined and standardized.
        # - Performance scores must be within a valid range (e.g., 0-5).
        # - Only active employees can receive new performance records for current or future periods.

    def _configured_competencies(self):
        competencies = getattr(self, "competencies", None)
        if competencies is None:
            return None
        if isinstance(competencies, str):
            return {part.strip() for part in competencies.split(",") if part.strip()}
        if isinstance(competencies, (list, tuple, set)):
            return {str(part).strip() for part in competencies if str(part).strip()}
        return None
        # - Each employee can have at most one score per competency per appraisal period.

    def _is_active_status(self, status) -> bool:
        normalized = str(status or "").strip().lower()
        return normalized == "active" or normalized.startswith("active-")

    def get_employee_by_name(self, name: str) -> dict:
        """
        Retrieve employee(s) info (id, department, position, status) by exact employee name.

        Args:
            name (str): The full name of the employee to search.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # list of {employee_id, department, position, status}
            }
            or
            {
                "success": False,
                "error": "No employee found with the given name"
            }

        Notes:
            - If multiple employees share the same name, all are returned.
            - Name matching is case-sensitive and exact.
        """
        matches = [
            {
                "employee_id": emp["employee_id"],
                "department": emp["department"],
                "position": emp["position"],
                "status": emp["status"],
            }
            for emp in self.employees.values()
            if emp["name"] == name
        ]

        if not matches:
            return {"success": False, "error": "No employee found with the given name"}
        return {"success": True, "data": matches}

    def get_employee_by_id(self, employee_id: str) -> dict:
        """
        Retrieve info for a specific employee using employee_id.

        Args:
            employee_id (str): The unique identifier for the employee.
    
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
            - employee_id must reference an employee present in the system.
        """
        if employee_id in self.employees:
            return { "success": True, "data": self.employees[employee_id] }
        else:
            return { "success": False, "error": "Employee not found" }

    def list_all_employees(self) -> dict:
        """
        Returns a list of all employees in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EmployeeInfo],  # All employees (may be empty if none present)
            }

        Constraints:
            - None; returns all employees regardless of status.
        """
        all_employees = list(self.employees.values())
        return {
            "success": True,
            "data": all_employees
        }

    def get_appraisal_period_by_label(self, label: str) -> dict:
        """
        Retrieve the appraisal period information (id, date range, etc.) for a given label.

        Args:
            label (str): The label of the appraisal period (e.g., "first quarter", "2024 H1").

        Returns:
            dict:
                - If found: {"success": True, "data": AppraisalPeriodInfo}
                - If not found: {"success": False, "error": "No appraisal period found for label: <label>"}
        """
        for period in self.periods.values():
            if period["label"] == label:
                return { "success": True, "data": period }
        return { "success": False, "error": f"No appraisal period found for label: {label}" }

    def get_appraisal_period_by_id(self, period_id: str) -> dict:
        """
        Retrieve the appraisal period information by its period_id.

        Args:
            period_id (str): The unique ID of the appraisal period.

        Returns:
            dict: {
                "success": True,
                "data": AppraisalPeriodInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., appraisal period not found)
            }

        Constraints:
            - The appraisal period ID must exist in the system.
        """
        if period_id not in self.periods:
            return {"success": False, "error": "Appraisal period not found"}

        return {"success": True, "data": self.periods[period_id]}

    def list_appraisal_periods(self) -> dict:
        """
        List all defined appraisal periods.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AppraisalPeriodInfo]  # May be empty if no periods defined
            }
        """
        periods_list = list(self.periods.values())
        return { "success": True, "data": periods_list }

    def list_all_competencies(self) -> dict:
        """
        Get the standardized list of valid competencies used for scoring.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # standardized competency names, possibly empty if none defined
            }

        Notes:
            - Returns an empty list if no competencies are defined.
        """
        # If self.competencies doesn't exist, define it as empty for robustness
        competencies = getattr(self, "competencies", [])
        return {"success": True, "data": competencies}

    def get_performance_record(self, employee_id: str, period_id: str, competency: str) -> dict:
        """
        Retrieve the performance record(s) for a given employee_id, period_id, and competency.

        Args:
            employee_id (str): The employee's unique ID.
            period_id (str): The appraisal period's unique ID.
            competency (str): The standardized competency being assessed.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": [PerformanceRecordInfo, ...]  # List (normally 0 or 1 record)
                  }
                - On error: {
                      "success": False,
                      "error": str  # Reason for error.
                  }

        Constraints:
            - Employee ID and Period ID must exist.
            - Competency must be a valid, standardized competency.
            - Returns at most one record, as per system constraints.
        """
        # Check employee existence
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee ID does not exist"}

        # Check period existence
        if period_id not in self.periods:
            return {"success": False, "error": "Appraisal period ID does not exist"}

        # Check valid competency
        allowed_competencies = self._configured_competencies()
        if allowed_competencies is not None and competency not in allowed_competencies:
            return {"success": False, "error": "Invalid competency"}

        # Find matching record(s)
        data = [
            record for record in self.performance_records
            if record["employee_id"] == employee_id and
               record["period_id"] == period_id and
               record["competency"] == competency
        ]

        return {"success": True, "data": data}

    def get_employee_performance_for_period(self, employee_id: str, period_id: str) -> dict:
        """
        Retrieve all performance records for a given employee during a specific appraisal period.

        Args:
            employee_id (str): The unique identifier of the employee.
            period_id (str): The unique identifier of the appraisal period.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[PerformanceRecordInfo]  # May be empty if no records exist
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Description of the error (e.g., employee or period does not exist)
                    }
        Constraints:
            - employee_id must exist in self.employees
            - period_id must exist in self.periods
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee does not exist"}
        if period_id not in self.periods:
            return {"success": False, "error": "Appraisal period does not exist"}

        filtered_records = [
            record for record in self.performance_records
            if record["employee_id"] == employee_id and record["period_id"] == period_id
        ]

        return {"success": True, "data": filtered_records}

    def get_reviewer_by_id(self, reviewer_id: str) -> dict:
        """
        Retrieve reviewer information by reviewer_id.

        Args:
            reviewer_id (str): Unique identifier of the reviewer.

        Returns:
            dict:
                - If found:
                    { "success": True, "data": ReviewerInfo }
                - If not found:
                    { "success": False, "error": "Reviewer not found" }
        """
        reviewer = self.reviewers.get(reviewer_id)
        if reviewer is not None:
            return { "success": True, "data": reviewer }
        else:
            return { "success": False, "error": "Reviewer not found" }

    def get_reviews_by_reviewer(self, reviewer_id: str) -> dict:
        """
        List all performance records reviewed by a specific reviewer.

        Args:
            reviewer_id (str): The unique identifier for the reviewer.

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceRecordInfo]  # All records reviewed by this reviewer (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Description of error (e.g., reviewer not found)
            }

        Constraints:
            - Reviewer must exist in the system.
        """
        if reviewer_id not in self.reviewers:
            return { "success": False, "error": "Reviewer does not exist" }

        reviewed_records = [
            record for record in self.performance_records
            if record["reviewer_id"] == reviewer_id
        ]

        return { "success": True, "data": reviewed_records }

    def check_employee_active_status(self, employee_id: str) -> dict:
        """
        Return whether an employee’s status is active for eligibility in current/future periods.

        Args:
            employee_id (str): The unique ID of the employee.

        Returns:
            dict: {
                "success": True,
                "is_active": bool  # True if employee is active, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Explanation if employee not found
            }

        Constraints:
            - Employee must exist in the system. If not, fail gracefully.
        """
        employee = self.employees.get(employee_id)
        if not employee:
            return { "success": False, "error": "Employee not found" }
    
        is_active = self._is_active_status(employee.get("status", ""))
        return { "success": True, "is_active": is_active }

    def add_performance_record(
        self,
        employee_id: str,
        period_id: str,
        competency: str,
        score: float,
        reviewer_id: str,
        comment: str = ""
    ) -> dict:
        """
        Create a new performance record for an employee in a given appraisal period and competency.

        Args:
            employee_id (str): The employee being assessed.
            period_id (str): The appraisal period.
            competency (str): The competency being evaluated.
            score (float): Performance score (valid range: 0-5).
            reviewer_id (str): Reviewer conducting the assessment.
            comment (str, optional): Additional comments.

        Returns:
            dict: Result dict; on success {"success": True, "message": ...},
                  on failure {"success": False, "error": ...}

        Constraints:
            - Employee, period, and reviewer must exist.
            - Employee must be active. Active-prefixed statuses such as
              'Active-Standard' and 'Active-Accelerated' also qualify.
            - Competency must be in the predefined list.
            - Score must be between 0 and 5 (inclusive).
            - Only one record per (employee, period, competency).
            - Only active employees can receive records for current or future periods.
        """
        # Check if employee exists and is active
        emp = self.employees.get(employee_id)
        if not emp:
            return { "success": False, "error": "Employee does not exist." }
        if not self._is_active_status(emp.get("status", "")):
            return { "success": False, "error": "Employee is not active." }

        # Check if appraisal period exists
        period = self.periods.get(period_id)
        if not period:
            return { "success": False, "error": "Appraisal period does not exist." }

        # Validate period date format without tying behavior to the machine's
        # current clock; formal cases intentionally use historical labels.
        try:
            datetime.strptime(period["start_date"], "%Y-%m-%d")
        except Exception:
            return { "success": False, "error": "Invalid period start date format." }

        # Check if reviewer exists
        if reviewer_id not in self.reviewers:
            return { "success": False, "error": "Reviewer does not exist." }

        # Check competency validity
        valid_competencies = self._configured_competencies()
        if valid_competencies is not None and competency not in valid_competencies:
            return { "success": False, "error": f"Competency '{competency}' is not valid." }
        if valid_competencies is None and not str(competency).strip():
            return { "success": False, "error": "Competency must be a non-empty string." }

        # Check score range (0-5 assumed)
        if not (0 <= score <= 5):
            return { "success": False, "error": "Score must be between 0 and 5." }

        # Ensure only one record per employee/period/competency
        exists = any(
            rec["employee_id"] == employee_id and
            rec["period_id"] == period_id and
            rec["competency"] == competency
            for rec in self.performance_records
        )
        if exists:
            return { "success": False, "error": "Performance record for this competency and period already exists for this employee." }

        # All checks passed, add the record
        new_record = {
            "employee_id": employee_id,
            "period_id": period_id,
            "competency": competency,
            "score": score,
            "reviewer_id": reviewer_id,
            "comment": comment or "",
        }
        self.performance_records.append(new_record)
        return { "success": True, "message": "Performance record added successfully." }

    def update_performance_record(
        self,
        employee_id: str,
        period_id: str,
        competency: str,
        score: float = None,
        comment: str = None
    ) -> dict:
        """
        Modify the score and/or comment on an existing performance record.

        Args:
            employee_id (str): The ID of the employee whose record is to be updated.
            period_id (str): The appraisal period ID of the record.
            competency (str): The competency area to update.
            score (float, optional): The new score (must be 0-5, if provided).
            comment (str, optional): The new comment.

        Returns:
            dict: {
                "success": True,
                "message": "Performance record updated"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Record must exist (employee, period, competency).
            - Score (if provided) must be in valid range (0-5 inclusive).
            - At least one of score or comment must be provided.
        """
        if score is None and comment is None:
            return {"success": False, "error": "No update fields provided; specify score and/or comment."}

        # Find target record
        rec = None
        for record in self.performance_records:
            if (record["employee_id"] == employee_id 
                and record["period_id"] == period_id 
                and record["competency"] == competency):
                rec = record
                break

        if rec is None:
            return {"success": False, "error": "Performance record not found."}

        # Check score constraints if being updated
        if score is not None:
            if not (0.0 <= score <= 5.0):
                return {"success": False, "error": "Score must be between 0 and 5."}
            rec["score"] = score

        # Update comment if provided
        if comment is not None:
            rec["comment"] = comment

        return {"success": True, "message": "Performance record updated"}

    def delete_performance_record(self, employee_id: str, period_id: str, competency: str) -> dict:
        """
        Remove a performance record for a specific employee, period, and competency.

        Args:
            employee_id (str): The unique identifier for the employee.
            period_id (str): The unique identifier for the appraisal period.
            competency (str): The standardized competency for which the record is stored.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Performance record deleted for employee {employee_id}, period {period_id}, competency {competency}"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Performance record not found for the given employee, period, and competency"
                    }

        Constraints:
            - Operation only affects records that match all three keys (employee_id, period_id, competency).
            - No exception is raised, only structured error reporting.
        """
        idx_to_delete = None
        for idx, record in enumerate(self.performance_records):
            if (
                record['employee_id'] == employee_id
                and record['period_id'] == period_id
                and record['competency'] == competency
            ):
                idx_to_delete = idx
                break

        if idx_to_delete is not None:
            del self.performance_records[idx_to_delete]
            return {
                "success": True,
                "message": f"Performance record deleted for employee {employee_id}, period {period_id}, competency {competency}"
            }
        else:
            return {
                "success": False,
                "error": "Performance record not found for the given employee, period, and competency"
            }

    def add_employee(
        self,
        employee_id: str,
        name: str,
        department: str,
        position: str,
        status: str
    ) -> dict:
        """
        Register a new employee in the system.

        Args:
            employee_id (str): Unique identifier for the employee.
            name (str): Employee's full name.
            department (str): Department the employee belongs to.
            position (str): Position/title of the employee.
            status (str): Employment status (e.g., 'active', 'inactive'). 

        Returns:
            dict: {
                "success": True,
                "message": "Employee {employee_id} added successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - employee_id must be unique. If duplicate, operation fails.
        """
        # Check uniqueness of employee_id
        if not employee_id or employee_id in self.employees:
            return {
                "success": False,
                "error": "Employee ID is missing or already exists."
            }

        # Minimal robustness: check all key fields
        if not (name and department and position and status):
            return {
                "success": False,
                "error": "Missing required employee information."
            }

        self.employees[employee_id] = {
            "employee_id": employee_id,
            "name": name,
            "department": department,
            "position": position,
            "status": status
        }
        return {
            "success": True,
            "message": f"Employee {employee_id} added successfully."
        }

    def update_employee_status(self, employee_id: str, new_status: str) -> dict:
        """
        Changes the employment status of the specified employee.

        Args:
            employee_id (str): The unique identifier of the employee.
            new_status (str): The new employment status (e.g., 'active', 'inactive', 'terminated').

        Returns:
            dict: {
                "success": True,
                "message": "Employee status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - employee_id must exist in the system.
            - No restriction on new_status value unless predefined statuses are enforced.
        """
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee ID does not exist"}

        self.employees[employee_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Employee status updated to {new_status}"
        }

    def add_appraisal_period(
        self,
        period_id: str,
        start_date: str,
        end_date: str,
        label: str
    ) -> dict:
        """
        Create a new appraisal period in the system.

        Args:
            period_id (str): Unique identifier for the appraisal period.
            start_date (str): Start date for the appraisal period (e.g., 'YYYY-MM-DD').
            end_date (str): End date for the appraisal period (e.g., 'YYYY-MM-DD').
            label (str): Display label for the appraisal period (e.g., "Q1 2024").

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Appraisal period '<label>' added."
                    }
                On failure (e.g., period_id already exists):
                    {
                        "success": False,
                        "error": "Appraisal period with this period_id already exists."
                    }

        Constraints:
            - period_id must not already exist in the system.
            - No other constraints (no overlapping checks, etc.).
        """

        if period_id in self.periods:
            return {
                "success": False,
                "error": "Appraisal period with this period_id already exists."
            }

        self.periods[period_id] = {
            "period_id": period_id,
            "start_date": start_date,
            "end_date": end_date,
            "label": label
        }

        return {
            "success": True,
            "message": f"Appraisal period '{label}' added."
        }

    def update_appraisal_period(
        self,
        period_id: str,
        start_date: str = None,
        end_date: str = None,
        label: str = None
    ) -> dict:
        """
        Edit date range and/or label of an existing appraisal period.

        Args:
            period_id (str): The identifier of the appraisal period to update.
            start_date (str, optional): New start date ("YYYY-MM-DD"), if updating.
            end_date (str, optional): New end date ("YYYY-MM-DD"), if updating.
            label (str, optional): New label, if updating.

        Returns:
            dict: {
                "success": True,
                "message": "Appraisal period updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - period_id must exist.
            - If provided, start_date and end_date must be valid and start_date <= end_date.
        """
        if period_id not in self.periods:
            return { "success": False, "error": "Appraisal period not found." }
    
        period = self.periods[period_id]

        # Only update fields that are provided
        updated = False

        if start_date is not None:
            # Basic format check: "YYYY-MM-DD"
            if len(start_date) != 10 or start_date[4] != "-" or start_date[7] != "-":
                return { "success": False, "error": "Invalid start_date format. Use YYYY-MM-DD." }
            period["start_date"] = start_date
            updated = True

        if end_date is not None:
            if len(end_date) != 10 or end_date[4] != "-" or end_date[7] != "-":
                return { "success": False, "error": "Invalid end_date format. Use YYYY-MM-DD." }
            period["end_date"] = end_date
            updated = True

        # Ensure start <= end if both are present now (either updated or previously existed)
        s_date = period["start_date"]
        e_date = period["end_date"]
        if s_date > e_date:
            return { "success": False, "error": "start_date cannot be later than end_date." }

        if label is not None:
            period["label"] = label
            updated = True

        if not updated:
            return { "success": False, "error": "No fields to update were provided." }

        self.periods[period_id] = period

        return { "success": True, "message": "Appraisal period updated successfully." }

    def add_reviewer(self, reviewer_id: str, name: str, position: str) -> dict:
        """
        Add a new reviewer entity to the system.

        Args:
            reviewer_id (str): Unique identifier for the reviewer.
            name (str): Name of the reviewer.
            position (str): Position/title of the reviewer.

        Returns:
            dict:
                - On success: { "success": True, "message": "Reviewer added successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - reviewer_id must be unique in the system.
            - All inputs should be non-empty strings.
        """
        if not reviewer_id or not isinstance(reviewer_id, str):
            return {"success": False, "error": "Reviewer ID must be a non-empty string."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Reviewer name must be a non-empty string."}
        if not position or not isinstance(position, str):
            return {"success": False, "error": "Reviewer position must be a non-empty string."}
        if reviewer_id in self.reviewers:
            return {"success": False, "error": "Reviewer with this ID already exists."}
    
        new_reviewer: ReviewerInfo = {
            "reviewer_id": reviewer_id,
            "name": name,
            "position": position
        }
        self.reviewers[reviewer_id] = new_reviewer
        return {"success": True, "message": "Reviewer added successfully."}

    def update_reviewer(self, reviewer_id: str, name: str = None, position: str = None) -> dict:
        """
        Modify reviewer information (name and/or position).
    
        Args:
            reviewer_id (str): The ID of the reviewer to modify.
            name (str, optional): New name for the reviewer.
            position (str, optional): New position for the reviewer.

        Returns:
            dict: 
                - {"success": True, "message": "Reviewer updated successfully."}
                - {"success": False, "error": <reason>} if reviewer does not exist
                  or no updatable fields provided.

        Constraints:
            - reviewer_id must already exist in self.reviewers.
            - At least one of 'name' or 'position' must be provided for update.
            - Only allows editing of name and position.

        """
        if reviewer_id not in self.reviewers:
            return {"success": False, "error": "Reviewer not found."}

        if name is None and position is None:
            return {"success": False, "error": "No updatable fields provided."}

        if name is not None:
            self.reviewers[reviewer_id]["name"] = name

        if position is not None:
            self.reviewers[reviewer_id]["position"] = position

        return {"success": True, "message": "Reviewer updated successfully."}


class EmployeePerformanceManagementSystem(BaseEnv):
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

    def get_employee_by_name(self, **kwargs):
        return self._call_inner_tool('get_employee_by_name', kwargs)

    def get_employee_by_id(self, **kwargs):
        return self._call_inner_tool('get_employee_by_id', kwargs)

    def list_all_employees(self, **kwargs):
        return self._call_inner_tool('list_all_employees', kwargs)

    def get_appraisal_period_by_label(self, **kwargs):
        return self._call_inner_tool('get_appraisal_period_by_label', kwargs)

    def get_appraisal_period_by_id(self, **kwargs):
        return self._call_inner_tool('get_appraisal_period_by_id', kwargs)

    def list_appraisal_periods(self, **kwargs):
        return self._call_inner_tool('list_appraisal_periods', kwargs)

    def list_all_competencies(self, **kwargs):
        return self._call_inner_tool('list_all_competencies', kwargs)

    def get_performance_record(self, **kwargs):
        return self._call_inner_tool('get_performance_record', kwargs)

    def get_employee_performance_for_period(self, **kwargs):
        return self._call_inner_tool('get_employee_performance_for_period', kwargs)

    def get_reviewer_by_id(self, **kwargs):
        return self._call_inner_tool('get_reviewer_by_id', kwargs)

    def get_reviews_by_reviewer(self, **kwargs):
        return self._call_inner_tool('get_reviews_by_reviewer', kwargs)

    def check_employee_active_status(self, **kwargs):
        return self._call_inner_tool('check_employee_active_status', kwargs)

    def add_performance_record(self, **kwargs):
        return self._call_inner_tool('add_performance_record', kwargs)

    def update_performance_record(self, **kwargs):
        return self._call_inner_tool('update_performance_record', kwargs)

    def delete_performance_record(self, **kwargs):
        return self._call_inner_tool('delete_performance_record', kwargs)

    def add_employee(self, **kwargs):
        return self._call_inner_tool('add_employee', kwargs)

    def update_employee_status(self, **kwargs):
        return self._call_inner_tool('update_employee_status', kwargs)

    def add_appraisal_period(self, **kwargs):
        return self._call_inner_tool('add_appraisal_period', kwargs)

    def update_appraisal_period(self, **kwargs):
        return self._call_inner_tool('update_appraisal_period', kwargs)

    def add_reviewer(self, **kwargs):
        return self._call_inner_tool('add_reviewer', kwargs)

    def update_reviewer(self, **kwargs):
        return self._call_inner_tool('update_reviewer', kwargs)
