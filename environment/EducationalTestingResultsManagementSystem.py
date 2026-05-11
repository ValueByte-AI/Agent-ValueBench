# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class StudentInfo(TypedDict):
    student_id: str
    name: str
    date_of_birth: str   # format: 'YYYY-MM-DD'
    contact_info: str

class ExamTypeInfo(TypedDict):
    exam_type_id: str
    name: str
    description: str

class TestResultInfo(TypedDict):
    test_result_id: str
    student_id: str
    exam_type_id: str
    test_date: str      # format: 'YYYY-MM-DD'
    score: float
    status: str
    institution_id: str

class InstitutionInfo(TypedDict):
    institution_id: str
    name: str
    address: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Students: {student_id: StudentInfo}
        self.students: Dict[str, StudentInfo] = {}

        # Exam types: {exam_type_id: ExamTypeInfo}
        self.exam_types: Dict[str, ExamTypeInfo] = {}

        # Test results: {test_result_id: TestResultInfo}
        self.test_results: Dict[str, TestResultInfo] = {}

        # Institutions: {institution_id: InstitutionInfo}
        self.institutions: Dict[str, InstitutionInfo] = {}

        # Constraints:
        # - A TestResult must reference a valid Student and a valid ExamType.
        # - Students may have multiple TestResults for different exam types and/or test dates.
        # - Access to TestResults may be restricted based on institutional permissions or student privacy settings.

    def get_student_by_id(self, student_id: str) -> dict:
        """
        Retrieve a student's details (name, date of birth, contact info, etc.) using their unique ID.

        Args:
            student_id (str): Unique identifier for the student.

        Returns:
            dict: {
                "success": True,
                "data": StudentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - student_id must exist in the system.
        """
        student = self.students.get(student_id)
        if student is None:
            return { "success": False, "error": "Student not found" }
        return { "success": True, "data": student }

    def get_student_by_name(self, name: str) -> dict:
        """
        Look up student record(s) using their name. May return multiple matches if more than one student
        shares the same name.

        Args:
            name (str): The full name of the student to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[StudentInfo]  # List of student info dicts with exact name match (may be empty)
                }

        Constraints:
            - Exact match on 'name' field.
            - No error if no student found: return empty list.
        """
        result = [
            student_info for student_info in self.students.values()
            if student_info["name"] == name
        ]
        return {
            "success": True,
            "data": result
        }

    def list_exam_types(self) -> dict:
        """
        Return all available standardized exam types.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ExamTypeInfo]  # A list (possibly empty) of all exam type records
            }

        Constraints:
            - No input.
            - No permission or access restrictions.
        """
        exam_type_list = list(self.exam_types.values())
        return {"success": True, "data": exam_type_list}

    def get_exam_type_by_name(self, name: str) -> dict:
        """
        Resolve an exam type's name (e.g., "TOEFL") to its corresponding exam_type_id and full info.

        Args:
            name (str): The name of the exam type (case-sensitive exact match).

        Returns:
            dict: {
                "success": True,
                "data": ExamTypeInfo  # All info for the matched exam type
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Notes:
            - If multiple exam types somehow share the same name, returns the first match.
            - Name matching is exact and case-sensitive.
        """
        for exam_type in self.exam_types.values():
            if exam_type['name'] == name:
                return { "success": True, "data": exam_type }
        return { "success": False, "error": "Exam type not found" }

    def list_student_test_results(self, student_id: str) -> dict:
        """
        Retrieve all test results (across all exam types and dates) for the specified student.

        Args:
            student_id (str): The unique identifier of the student.

        Returns:
            dict: {
                "success": True,
                "data": List[TestResultInfo],  # List of test results for this student (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. student does not exist
            }

        Constraints:
            - The provided student_id must exist in the system.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        results = [tr for tr in self.test_results.values() if tr["student_id"] == student_id]
        return { "success": True, "data": results }

    def list_test_results_by_exam(self, student_id: str, exam_type_id: str) -> dict:
        """
        Retrieve all test results for the specified student and exam type.

        Args:
            student_id (str): The ID of the student.
            exam_type_id (str): The ID of the exam type.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TestResultInfo],  # may be empty
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - student_id must refer to an existing student.
            - exam_type_id must refer to an existing exam type.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }
        if exam_type_id not in self.exam_types:
            return { "success": False, "error": "Exam type does not exist" }

        results = [
            result
            for result in self.test_results.values()
            if result["student_id"] == student_id and result["exam_type_id"] == exam_type_id
        ]

        return {
            "success": True,
            "data": results
        }

    def get_test_result_by_id(self, test_result_id: str) -> dict:
        """
        Retrieve details for a specific test result, given its test_result_id.

        Args:
            test_result_id (str): ID of the test result to retrieve.

        Returns:
            dict:
                - On success: {'success': True, 'data': TestResultInfo}
                - On failure (not found): {'success': False, 'error': 'Test result not found'}
        Constraints:
            - No permission/privacy checks are enforced in this method.
            - Only retrieves an existing record.
        """
        test_result = self.test_results.get(test_result_id)
        if not test_result:
            return {"success": False, "error": "Test result not found"}
        return {"success": True, "data": test_result}

    def get_institution_by_id(self, institution_id: str) -> dict:
        """
        Retrieve information about an educational institution by its institution_id.

        Args:
            institution_id (str): The unique ID of the institution.

        Returns:
            dict:
                On success: { "success": True, "data": InstitutionInfo }
                On failure: { "success": False, "error": "Institution not found" }

        Constraints:
            - The institution_id must exist in the system.
        """
        if institution_id not in self.institutions:
            return { "success": False, "error": "Institution not found" }

        return { "success": True, "data": self.institutions[institution_id] }

    def list_institutions(self) -> dict:
        """
        Return all institutions registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[InstitutionInfo]   # List of all institutions (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - None.
        """
        if not hasattr(self, "institutions"):
            return { "success": False, "error": "Institutions data not available" }

        institutions_list = list(self.institutions.values())
        return { "success": True, "data": institutions_list }

    def check_test_result_access_permissions(
        self, 
        test_result_id: str, 
        requester_type: str, 
        requester_id: str
    ) -> dict:
        """
        Determine if a student, institution, or other user has permission to access a particular test result.

        Args:
            test_result_id (str): The unique ID of the test result to check.
            requester_type (str): The type of requester ("student", "institution", etc.).
            requester_id (str): The unique ID of the requester (student_id or institution_id).

        Returns:
            dict: {
                "success": True,
                "data": {
                    "allowed": bool,
                    "reason": str (optional, if denied),
                },
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. test result not found)
            }

        Constraints:
            - Access allowed for:
                - The student referenced in the test result.
                - The institution referenced in the test result.
            - All other requesters are denied access.
        """
        # Check that the test result exists
        test_result = self.test_results.get(test_result_id)
        if not test_result:
            return { "success": False, "error": "Test result not found." }
    
        # Student access: student_id must match
        if requester_type == "student":
            if requester_id == test_result["student_id"]:
                return { "success": True, "data": { "allowed": True } }
            else:
                return {
                    "success": True,
                    "data": {
                        "allowed": False,
                        "reason": "Student may only access their own test results."
                    }
                }
    
        # Institution access: institution_id must match
        if requester_type == "institution":
            if requester_id == test_result["institution_id"]:
                return { "success": True, "data": { "allowed": True } }
            else:
                return {
                    "success": True,
                    "data": {
                        "allowed": False,
                        "reason": "Institution may only access test results reported to them."
                    }
                }
    
        # Unknown/unsupported requester type
        return {
            "success": True,
            "data": {
                "allowed": False,
                "reason": "Requester type not permitted to access this test result."
            }
        }

    def add_test_result(
        self,
        student_id: str,
        exam_type_id: str,
        test_date: str,
        score: float,
        status: str,
        institution_id: str = "",
        test_result_id: str = None
    ) -> dict:
        """
        Add a new test result for a student.

        Args:
            student_id (str): The student's unique ID (must exist).
            exam_type_id (str): The exam type's unique ID (must exist).
            test_date (str): Date of the exam ('YYYY-MM-DD').
            score (float): The student's score.
            status (str): Status string (e.g., 'valid', 'pending', etc.).
            institution_id (str): The institution's unique ID (optional; may be an empty string or unknown).
            test_result_id (str, optional): Unique ID for the test result (auto-generated if not provided).

        Returns:
            dict: {
                "success": True,
                "message": "Test result added successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - student_id must exist in students.
            - exam_type_id must exist in exam_types.
            - test_result_id must be unique.
        """

        # Check student
        if student_id not in self.students:
            return { "success": False, "error": "Referenced student_id does not exist." }

        # Check exam type
        if exam_type_id not in self.exam_types:
            return { "success": False, "error": "Referenced exam_type_id does not exist." }

        # Generate or check test_result_id
        if not test_result_id:
            test_result_id = str(uuid.uuid4())
        else:
            if test_result_id in self.test_results:
                return { "success": False, "error": "test_result_id already exists." }

        # Create new TestResultInfo
        new_result: TestResultInfo = {
            "test_result_id": test_result_id,
            "student_id": student_id,
            "exam_type_id": exam_type_id,
            "test_date": test_date,
            "score": score,
            "status": status,
            "institution_id": institution_id
        }
        self.test_results[test_result_id] = new_result
        return { "success": True, "message": "Test result added successfully." }

    def update_test_result(
        self,
        test_result_id: str,
        score: float = None,
        status: str = None,
        institution_id: str = None,
    ) -> dict:
        """
        Edit the details ('score', 'status', 'institution link', etc.) of an existing test result.

        Args:
            test_result_id (str): The ID of the test result to edit.
            score (float, optional): New score to assign.
            status (str, optional): Updated status (e.g. 'Complete', 'Pending', etc.).
            institution_id (str, optional): ID of the institution to link the result to.

        Returns:
            dict: {
                "success": True,
                "message": "Test result updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - The test_result_id must exist.
            - If institution_id is updated, it must reference an existing institution.
            - Score, if provided, must be a float.
            - Status, if provided, must be a non-empty string.
        """
        if test_result_id not in self.test_results:
            return {"success": False, "error": "Test result does not exist."}

        test_result = self.test_results[test_result_id]

        # Score validation if given
        if score is not None:
            try:
                test_result["score"] = float(score)
            except (TypeError, ValueError):
                return {"success": False, "error": "Invalid score value."}

        # Status validation if given
        if status is not None:
            if not isinstance(status, str) or not status.strip():
                return {"success": False, "error": "Status must be a non-empty string."}
            test_result["status"] = status.strip()

        # Institution validation if given
        if institution_id is not None:
            if institution_id not in self.institutions:
                return {"success": False, "error": "Institution does not exist."}
            test_result["institution_id"] = institution_id

        self.test_results[test_result_id] = test_result
        return {"success": True, "message": "Test result updated successfully."}

    def delete_test_result(self, test_result_id: str) -> dict:
        """
        Remove a test result from the system after checking it exists.

        Args:
            test_result_id (str): The unique identifier of the test result to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Test result deleted successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The test result with the given id must exist.
        """
        if test_result_id not in self.test_results:
            return { "success": False, "error": "TestResult with given id does not exist" }

        del self.test_results[test_result_id]
        return { "success": True, "message": "Test result deleted successfully" }

    def add_student(
        self,
        student_id: str,
        name: str,
        date_of_birth: str,
        contact_info: str
    ) -> dict:
        """
        Register a new student in the system.

        Args:
            student_id (str): Unique identifier for the student.
            name (str): The student's full name.
            date_of_birth (str): Student's date of birth ('YYYY-MM-DD').
            contact_info (str): Contact information for the student.

        Returns:
            dict: {
                "success": True,
                "message": "Student added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - student_id must be unique (must not already exist in self.students).
        """
        # Check mandatory fields
        if not (student_id and name and date_of_birth and contact_info):
            return {"success": False, "error": "All parameters are required."}

        # Check uniqueness
        if student_id in self.students:
            return {"success": False, "error": f"Student with id '{student_id}' already exists."}

        # (Optional) Basic date format validation (no exception raising)
        if len(date_of_birth) != 10 or date_of_birth[4] != '-' or date_of_birth[7] != '-':
            return {"success": False, "error": "date_of_birth must be in 'YYYY-MM-DD' format."}

        self.students[student_id] = {
            "student_id": student_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "contact_info": contact_info,
        }

        return {"success": True, "message": "Student added successfully."}

    def update_student_info(self, student_id: str, name: str = None, date_of_birth: str = None, contact_info: str = None) -> dict:
        """
        Update fields (name, date_of_birth, contact_info) for an existing student.

        Args:
            student_id (str): Unique identifier of the student to update.
            name (str, optional): New name for the student.
            date_of_birth (str, optional): New date of birth, format 'YYYY-MM-DD'.
            contact_info (str, optional): New contact info for the student.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Student information updated for student_id"}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - student_id must already exist.
            - Only known fields will be updated.
        """
        if student_id not in self.students:
            return {"success": False, "error": "Student not found"}

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if date_of_birth is not None:
            update_fields["date_of_birth"] = date_of_birth
        if contact_info is not None:
            update_fields["contact_info"] = contact_info

        if not update_fields:
            return {"success": False, "error": "No fields provided to update"}

        student_info = self.students[student_id]
        for key, value in update_fields.items():
            student_info[key] = value

        return {"success": True, "message": f"Student information updated for {student_id}"}

    def add_exam_type(self, exam_type_id: str, name: str, description: str) -> dict:
        """
        Add a new possible standardized exam (ExamType) to the system.

        Args:
            exam_type_id (str): Unique exam type identifier.
            name (str): Name of the exam (e.g., 'TOEFL', 'GRE').
            description (str): Description of the exam.

        Returns:
            dict: {
                "success": True,
                "message": "Exam type added successfully."
            }
            or
            {
                "success": False,
                "error": error message
            }

        Constraints:
            - exam_type_id must be unique in the system.
            - name and description should not be empty.
        """
        if not exam_type_id or not name or not description:
            return {
                "success": False,
                "error": "Exam type ID, name, and description must all be provided and non-empty."
            }

        if exam_type_id in self.exam_types:
            return {
                "success": False,
                "error": "Exam type ID already exists."
            }

        exam_type_info = {
            "exam_type_id": exam_type_id,
            "name": name,
            "description": description
        }

        self.exam_types[exam_type_id] = exam_type_info

        return {
            "success": True,
            "message": "Exam type added successfully."
        }

    def update_exam_type(
        self,
        exam_type_id: str,
        name: str = None,
        description: str = None
    ) -> dict:
        """
        Update the name and/or description of an existing exam type.

        Args:
            exam_type_id (str): The ID of the exam type to update.
            name (str, optional): New name for the exam type.
            description (str, optional): New description for the exam type.

        Returns:
            dict: 
                On success: { "success": True, "message": "Exam type updated successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - exam_type_id must refer to an existing exam type.
            - At least one of name or description must be provided.
            - Empty strings are not valid as new values.
        """
        if exam_type_id not in self.exam_types:
            return { "success": False, "error": "Exam type does not exist." }

        if name is None and description is None:
            return { "success": False, "error": "No update fields provided. Specify at least one attribute to update." }

        if name is not None:
            if not isinstance(name, str) or name.strip() == "":
                return { "success": False, "error": "Name must be a non-empty string." }
            self.exam_types[exam_type_id]['name'] = name

        if description is not None:
            if not isinstance(description, str) or description.strip() == "":
                return { "success": False, "error": "Description must be a non-empty string." }
            self.exam_types[exam_type_id]['description'] = description

        return { "success": True, "message": "Exam type updated successfully." }

    def add_institution(self, institution_id: str, name: str, address: str) -> dict:
        """
        Register a new institution in the system.

        Args:
            institution_id (str): Unique identifier for the institution.
            name (str): Name of the institution.
            address (str): Address of the institution.

        Returns:
            dict: {
                "success": True,
                "message": "Institution added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., institution ID already exists)
            }

        Constraints:
            - institution_id must be unique in the system (cannot overwrite existing).
        """
        if institution_id in self.institutions:
            return {"success": False, "error": "Institution ID already exists."}
        self.institutions[institution_id] = {
            "institution_id": institution_id,
            "name": name,
            "address": address
        }
        return {"success": True, "message": "Institution added successfully."}

    def update_institution_info(
        self,
        institution_id: str,
        name: str = None,
        address: str = None
    ) -> dict:
        """
        Update an institution's record (name/address).

        Args:
            institution_id (str): The ID of the institution record to update.
            name (str, optional): New institution name (if updating).
            address (str, optional): New institution address (if updating).

        Returns:
            dict: 
                { "success": True, "message": "Institution info updated." }
                or
                { "success": False, "error": <reason> }

        Constraints:
            - institution_id must exist in the system.
            - At least one of 'name' or 'address' must be provided.
            - Only 'name' and 'address' may be updated.
        """
        if institution_id not in self.institutions:
            return { "success": False, "error": "Institution does not exist." }

        if name is None and address is None:
            return { "success": False, "error": "No update fields provided." }

        modified = False
        institution = self.institutions[institution_id]

        if name is not None:
            institution["name"] = name
            modified = True
        if address is not None:
            institution["address"] = address
            modified = True

        # Update in the dict (redundant because it's a reference, but explicit)
        self.institutions[institution_id] = institution

        return { "success": True, "message": "Institution info updated." }


class EducationalTestingResultsManagementSystem(BaseEnv):
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

    def get_student_by_id(self, **kwargs):
        return self._call_inner_tool('get_student_by_id', kwargs)

    def get_student_by_name(self, **kwargs):
        return self._call_inner_tool('get_student_by_name', kwargs)

    def list_exam_types(self, **kwargs):
        return self._call_inner_tool('list_exam_types', kwargs)

    def get_exam_type_by_name(self, **kwargs):
        return self._call_inner_tool('get_exam_type_by_name', kwargs)

    def list_student_test_results(self, **kwargs):
        return self._call_inner_tool('list_student_test_results', kwargs)

    def list_test_results_by_exam(self, **kwargs):
        return self._call_inner_tool('list_test_results_by_exam', kwargs)

    def get_test_result_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_result_by_id', kwargs)

    def get_institution_by_id(self, **kwargs):
        return self._call_inner_tool('get_institution_by_id', kwargs)

    def list_institutions(self, **kwargs):
        return self._call_inner_tool('list_institutions', kwargs)

    def check_test_result_access_permissions(self, **kwargs):
        return self._call_inner_tool('check_test_result_access_permissions', kwargs)

    def add_test_result(self, **kwargs):
        return self._call_inner_tool('add_test_result', kwargs)

    def update_test_result(self, **kwargs):
        return self._call_inner_tool('update_test_result', kwargs)

    def delete_test_result(self, **kwargs):
        return self._call_inner_tool('delete_test_result', kwargs)

    def add_student(self, **kwargs):
        return self._call_inner_tool('add_student', kwargs)

    def update_student_info(self, **kwargs):
        return self._call_inner_tool('update_student_info', kwargs)

    def add_exam_type(self, **kwargs):
        return self._call_inner_tool('add_exam_type', kwargs)

    def update_exam_type(self, **kwargs):
        return self._call_inner_tool('update_exam_type', kwargs)

    def add_institution(self, **kwargs):
        return self._call_inner_tool('add_institution', kwargs)

    def update_institution_info(self, **kwargs):
        return self._call_inner_tool('update_institution_info', kwargs)
