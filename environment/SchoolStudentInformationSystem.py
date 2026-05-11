# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Tuple, TypedDict



# Student entity -- state space: student_id, name, date_of_birth, contact_info, enrollment_status
class StudentInfo(TypedDict):
    student_id: str
    name: str
    date_of_birth: str
    contact_info: str
    enrollment_status: str

# Parent/guardian entity -- parent_id, name, contact_info
class ParentInfo(TypedDict):
    parent_id: str
    name: str
    contact_info: str

# ParentStudentLink -- parent_id, student_id
class ParentStudentLinkInfo(TypedDict):
    parent_id: str
    student_id: str

# Class entity -- class_id, subject, academic_year, teacher_id
class ClassInfo(TypedDict):
    class_id: str
    subject: str
    academic_year: str
    teacher_id: str

# Enrollment (Student enrollment in class) -- student_id, class_id
class EnrollmentInfo(TypedDict):
    student_id: str
    class_id: str

# Assessment entity -- assessment_id, class_id, type, date, description
class AssessmentInfo(TypedDict):
    assessment_id: str
    class_id: str
    type: str
    date: str
    description: str

# Grade entity -- student_id, assessment_id, grade_value, remark
class GradeInfo(TypedDict):
    student_id: str
    assessment_id: str
    grade_value: str
    remark: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        School Student Information System (SIS) environment state

        Constraints:
        - Only authorized parents/guardians can view the records of linked students.
        - Students must be enrolled in a class to have a grade/assessment for that class.
        - Each class is linked to a specific subject and academic period.
        - Grade records must reference valid students and assessments.
        """

        # Students: {student_id: StudentInfo}
        self.students: Dict[str, StudentInfo] = {}

        # Parents: {parent_id: ParentInfo}
        self.parents: Dict[str, ParentInfo] = {}

        # Parent-student links: List of ParentStudentLinkInfo
        self.parent_student_links: List[ParentStudentLinkInfo] = []

        # Classes: {class_id: ClassInfo}
        self.classes: Dict[str, ClassInfo] = {}

        # Enrollments: List of EnrollmentInfo (student_id, class_id pairs)
        self.enrollments: List[EnrollmentInfo] = []

        # Assessments: {assessment_id: AssessmentInfo}
        self.assessments: Dict[str, AssessmentInfo] = {}

        # Grades: List of GradeInfo (student_id, assessment_id, grade_value, remark)
        self.grades: List[GradeInfo] = []

    def get_parent_by_name(self, name: str) -> dict:
        """
        Retrieve all parent/guardian records matching the provided name.

        Args:
            name (str): The name of the parent/guardian to search for (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[ParentInfo],  # List of all matching parent records (can be empty if not found)
            }

        Constraints:
            - No authentication or authorization is required for this operation.
            - If no parent matches, returns an empty list.
            - Matches are by exact name comparison.
        """
        results = [
            parent_info for parent_info in self.parents.values()
            if parent_info["name"] == name
        ]
        return {
            "success": True,
            "data": results
        }

    def get_student_by_name(self, name: str) -> dict:
        """
        Retrieve all student record(s) with the given name.

        Args:
            name (str): The name to search for (match is case-sensitive and exact).

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "data": List[StudentInfo],  # May be empty if no match
                }
              - On error: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Input name must be a non-empty string.
            - May return multiple students for the same name (not unique).
        """
        if not isinstance(name, str) or name.strip() == "":
            return {"success": False, "error": "Invalid input: name must be a non-empty string"}

        results = [
            student_info for student_info in self.students.values()
            if student_info["name"] == name
        ]

        return {"success": True, "data": results}

    def list_parents_of_student(self, student_id: str) -> dict:
        """
        List all parents/guardians linked to a given student by their student_id.

        Args:
            student_id (str): The unique identifier for the student.

        Returns:
            dict: {
                "success": True,
                "data": List[ParentInfo]  # List of parent info dicts linked to this student (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., student does not exist
            }

        Constraints:
            - student_id must exist in the system.
            - Returns only parents with valid corresponding entries in the system.
        """

        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist"}

        # Get all parent_ids linked to this student
        parent_ids = [
            link["parent_id"]
            for link in self.parent_student_links
            if link["student_id"] == student_id
        ]

        # Get ParentInfo for valid parents only
        result = [
            self.parents[parent_id]
            for parent_id in parent_ids
            if parent_id in self.parents
        ]

        return {"success": True, "data": result}

    def list_students_of_parent(self, parent_id: str) -> dict:
        """
        List all students linked to a given parent by parent_id.

        Args:
            parent_id (str): Parent's unique identifier.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[StudentInfo]}  # List may be empty
                On error (e.g., parent_id not in system):
                    {"success": False, "error": str}
    
        Constraints:
            - parent_id must exist in self.parents.
            - Links to non-existent students are ignored/skipped.
        """
        if parent_id not in self.parents:
            return {"success": False, "error": "Parent does not exist"}

        linked_student_ids = [
            link['student_id']
            for link in self.parent_student_links
            if link['parent_id'] == parent_id
        ]
        students = [
            self.students[sid] for sid in linked_student_ids if sid in self.students
        ]

        return {"success": True, "data": students}

    def check_parent_student_link(self, parent_id: str, student_id: str) -> dict:
        """
        Verify if the given parent (parent_id) is linked to the given student (student_id).

        Args:
            parent_id (str): The unique identifier of the parent/guardian.
            student_id (str): The unique identifier of the student.

        Returns:
            dict:
                - On success: { "success": True, "linked": bool }
                - On error: { "success": False, "error": str }

        Constraints:
            - Both parent_id and student_id must exist in the system.
            - Checks direct parent-student links only.
        """
        if parent_id not in self.parents:
            return { "success": False, "error": "Parent does not exist" }
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        linked = any(
            link['parent_id'] == parent_id and link['student_id'] == student_id
            for link in self.parent_student_links
        )
        return { "success": True, "linked": linked }

    def get_student_enrollments(self, student_id: str) -> dict:
        """
        Get all class_ids that a student is currently enrolled in.

        Args:
            student_id (str): The ID of the student whose enrollments should be listed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[str],  # class_ids student is enrolled in (may be empty)
                    }
                On error:
                    {
                        "success": False,
                        "error": str,
                    }

        Constraints:
            - The student_id must exist in the system.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        enrolled_class_ids = [
            enrollment["class_id"]
            for enrollment in self.enrollments
            if enrollment["student_id"] == student_id
        ]
        return { "success": True, "data": enrolled_class_ids }

    def get_class_by_subject_and_student(self, student_id: str, subject: str) -> dict:
        """
        Retrieve the list of class_id(s) in which the specified student is enrolled for the given subject.

        Args:
            student_id (str): The ID of the student whose classes are to be retrieved.
            subject (str): The subject of interest (case-insensitive).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[str]  # class_id(s) the student is enrolled in for the subject
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # explanation, e.g. "Student does not exist"
                    }

        Constraints:
            - Student must exist in the system.
            - Only existing class records are considered.
            - Case-insensitive match on subject.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        subject_lc = subject.strip().lower()
        # Find all class_ids for this student
        enrolled_class_ids = [
            enrollment["class_id"]
            for enrollment in self.enrollments
            if enrollment["student_id"] == student_id
        ]

        # For all these class_ids, filter classes with matching subject
        matching_class_ids = []
        for class_id in enrolled_class_ids:
            class_info = self.classes.get(class_id)
            if class_info and class_info.get("subject", "").strip().lower() == subject_lc:
                matching_class_ids.append(class_id)
        # Return the result
        return { "success": True, "data": matching_class_ids }

    def get_class_info(self, class_id: str) -> dict:
        """
        Retrieve information about a class given its class_id.

        Args:
            class_id (str): The unique identifier for the class.

        Returns:
            dict: {
                "success": True,
                "data": ClassInfo  # metadata dictionary for the class
            }
            or
            {
                "success": False,
                "error": str  # if class not found
            }

        Constraints:
            - class_id must exist in the system.
        """
        if class_id not in self.classes:
            return {"success": False, "error": "Class ID does not exist"}

        return {"success": True, "data": self.classes[class_id]}

    def list_assessments_by_class_and_type(self, class_id: str, assessment_type: str) -> dict:
        """
        List all assessments of a given type (e.g., "exam") for a specific class.

        Args:
            class_id (str): ID of the class whose assessments to list.
            assessment_type (str): Type of assessment to filter by (e.g., "exam").

        Returns:
            dict: {
                "success": True,
                "data": List[AssessmentInfo],  # List of assessments matching class_id and type
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. class does not exist
            }

        Constraints:
            - class_id must exist.
        """
        # Check if class exists
        if class_id not in self.classes:
            return {"success": False, "error": "Class does not exist."}

        # Filter assessments by class_id and type (case-insensitive)
        matched = [
            info for info in self.assessments.values()
            if info["class_id"] == class_id and info["type"].lower() == assessment_type.lower()
        ]

        return {"success": True, "data": matched}

    def get_grade_for_assessment(self, student_id: str, assessment_id: str) -> dict:
        """
        Retrieve a student's grade record for a specific assessment.

        Args:
            student_id (str): The student's unique ID.
            assessment_id (str): The assessment's unique ID.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": GradeInfo  # The grade record
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }
        Constraints:
            - The student_id and assessment_id must exist in the system.
            - The grade record must exist for the given student and assessment.
        """
        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist"}
        if assessment_id not in self.assessments:
            return {"success": False, "error": "Assessment does not exist"}

        for grade in self.grades:
            if grade["student_id"] == student_id and grade["assessment_id"] == assessment_id:
                return {"success": True, "data": grade}

        return {"success": False, "error": "Grade record not found"}

    def get_grades_for_student_in_subject(self, student_id: str, subject: str) -> dict:
        """
        Get all grades awarded to a student in all classes for a particular subject.

        Args:
            student_id (str): The student's identifier.
            subject (str): The subject for which grades are requested.

        Returns:
            dict: {
                "success": True,
                "data": [GradeInfo, ...]  # List of matching grade records (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # If the student does not exist
            }

        Constraints:
            - The student must exist.
            - Only grades for classes and assessments in the given subject are included.
        """
        # Step 1: Validate the student exists
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        # Step 2: Find all classes for the subject
        class_ids_for_subject = [
            class_id for class_id, class_info in self.classes.items()
            if class_info['subject'] == subject
        ]
        if not class_ids_for_subject:
            # No classes for subject, return empty result
            return { "success": True, "data": [] }

        # Step 3: Find which of these classes the student is enrolled in
        enrolled_class_ids = {
            enrollment['class_id'] for enrollment in self.enrollments
            if enrollment['student_id'] == student_id and enrollment['class_id'] in class_ids_for_subject
        }
        if not enrolled_class_ids:
            # Not enrolled in any class for this subject
            return { "success": True, "data": [] }

        # Step 4: Find all assessments in those classes
        assessment_ids = [
            assessment_id for assessment_id, assessment in self.assessments.items()
            if assessment['class_id'] in enrolled_class_ids
        ]

        if not assessment_ids:
            return { "success": True, "data": [] }

        # Step 5: Find all grades for this student and these assessments
        result_grades = [
            grade for grade in self.grades
            if grade['student_id'] == student_id and grade['assessment_id'] in assessment_ids
        ]

        return { "success": True, "data": result_grades }

    def list_assessment_results_for_student_in_class(self, student_id: str, class_id: str) -> dict:
        """
        Get all assessment grades for a student in a given class.

        Args:
            student_id (str): Unique identifier for the student.
            class_id (str): Unique identifier for the class.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[GradeInfo]  # List of grade records (may be empty)
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Description of the error
                    }
        Constraints:
            - Both student and class must exist.
            - Student must be enrolled in the given class.
        """
        # Check that the student exists
        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist"}

        # Check that the class exists
        if class_id not in self.classes:
            return {"success": False, "error": "Class does not exist"}

        # Check student enrollment in class
        if not any(
            enroll["student_id"] == student_id and enroll["class_id"] == class_id
            for enroll in self.enrollments
        ):
            return {"success": False, "error": "Student is not enrolled in the specified class"}

        # Gather assessment IDs for this class
        assessment_ids = [
            assessment_id
            for assessment_id, assessment in self.assessments.items()
            if assessment["class_id"] == class_id
        ]

        # Gather GradeInfo for the student and those assessments
        results = [
            grade for grade in self.grades
            if grade["student_id"] == student_id and grade["assessment_id"] in assessment_ids
        ]

        return {"success": True, "data": results}

    def add_student(
        self,
        student_id: str,
        name: str,
        date_of_birth: str,
        contact_info: str,
        enrollment_status: str
    ) -> dict:
        """
        Add a new student to the SIS.

        Args:
            student_id (str): Unique ID for the student.
            name (str): Student's full name.
            date_of_birth (str): Student's date of birth.
            contact_info (str): Contact information.
            enrollment_status (str): Current enrollment status (e.g., active, withdrawn).

        Returns:
            dict: {
                "success": True, 
                "message": "Student added successfully"
            }
            OR
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - student_id must be unique in self.students.
            - All fields must be non-empty strings.
        """
        if not all([student_id, name, date_of_birth, contact_info, enrollment_status]):
            return {"success": False, "error": "All student fields are required and cannot be empty"}

        if student_id in self.students:
            return {"success": False, "error": "Student ID already exists"}

        self.students[student_id] = {
            "student_id": student_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "contact_info": contact_info,
            "enrollment_status": enrollment_status
        }
        return {"success": True, "message": "Student added successfully"}

    def add_parent(self, parent_id: str, name: str, contact_info: str) -> dict:
        """
        Add a new parent/guardian record to the system.

        Args:
            parent_id (str): Unique identifier for the parent.
            name (str): Parent's name.
            contact_info (str): Parent's contact information.

        Returns:
            dict: {
                "success": True,
                "message": "Parent <parent_id> added"
            } on success, or
            {
                "success": False,
                "error": <reason>
            } on failure.

        Constraints:
            - parent_id must not already exist.
            - parent_id, name, and contact_info should be non-empty.
        """
        if not parent_id or not name or not contact_info:
            return {"success": False, "error": "All fields (parent_id, name, contact_info) are required"}
        if parent_id in self.parents:
            return {"success": False, "error": "Parent ID already exists"}

        self.parents[parent_id] = {
            "parent_id": parent_id,
            "name": name,
            "contact_info": contact_info
        }
        return {"success": True, "message": f"Parent {parent_id} added"}

    def link_parent_to_student(self, parent_id: str, student_id: str) -> dict:
        """
        Create a parent-student relationship by linking a parent to a student.

        Args:
            parent_id (str): Unique identifier of the parent.
            student_id (str): Unique identifier of the student.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Parent linked to student successfully."
                }
                On failure,
                {
                    "success": False,
                    "error": <error reason>
                }

        Constraints:
            - Parent and student must both exist.
            - The parent-student link must not already exist.
        """
        # Check parent existence
        if parent_id not in self.parents:
            return { "success": False, "error": "Parent does not exist." }
        # Check student existence
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist." }
        # Check if link exists already
        for link in self.parent_student_links:
            if link["parent_id"] == parent_id and link["student_id"] == student_id:
                return { "success": False, "error": "Parent-student link already exists." }
        # Create the link
        new_link = {"parent_id": parent_id, "student_id": student_id}
        self.parent_student_links.append(new_link)
        return { "success": True, "message": "Parent linked to student successfully." }

    def enroll_student_in_class(self, student_id: str, class_id: str) -> dict:
        """
        Enroll a student in a particular class.

        Args:
            student_id (str): The student's unique identifier.
            class_id (str): The class's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The student and class must exist in the system.
            - The student must not already be enrolled in the specified class.
        """
        # Check if the student exists
        if student_id not in self.students:
            return { "success": False, "error": f"Student {student_id} does not exist." }
    
        # Check if the class exists
        if class_id not in self.classes:
            return { "success": False, "error": f"Class {class_id} does not exist." }

        # Check if the student is already enrolled in the class
        for enrollment in self.enrollments:
            if enrollment["student_id"] == student_id and enrollment["class_id"] == class_id:
                return { "success": False, "error": f"Student {student_id} is already enrolled in class {class_id}." }
    
        # Enroll the student
        self.enrollments.append({
            "student_id": student_id,
            "class_id": class_id
        })
        return { "success": True, "message": f"Student {student_id} enrolled in class {class_id}" }

    def add_class(self, class_id: str, subject: str, academic_year: str, teacher_id: str) -> dict:
        """
        Add a new class to the catalog.

        Args:
            class_id (str): Unique class identifier.
            subject (str): Subject name for the class.
            academic_year (str): Academic year string.
            teacher_id (str): Associated teacher's identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Class <class_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - class_id must be unique among all classes.
            - All parameters must be non-empty strings.
        """
        # Parameter validation
        if not all(isinstance(x, str) and x.strip() for x in [class_id, subject, academic_year, teacher_id]):
            return {"success": False, "error": "All class fields must be non-empty strings."}
    
        if class_id in self.classes:
            return {"success": False, "error": f"Class with id '{class_id}' already exists."}

        # Add class
        class_info = {
            "class_id": class_id,
            "subject": subject,
            "academic_year": academic_year,
            "teacher_id": teacher_id
        }
        self.classes[class_id] = class_info

        return {"success": True, "message": f"Class {class_id} added successfully."}

    def add_assessment(
        self,
        assessment_id: str,
        class_id: str,
        type: str,
        date: str,
        description: str
    ) -> dict:
        """
        Add a new assessment (exam, assignment, etc.) to a class.

        Args:
            assessment_id (str): Unique identifier for the assessment.
            class_id (str): The class to which the assessment belongs.
            type (str): The type of assessment (e.g., 'exam', 'assignment').
            date (str): The date of the assessment (format: 'YYYY-MM-DD' or similar).
            description (str): Description of the assessment.

        Returns:
            dict: {
                "success": True,
                "message": "Assessment added successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - assessment_id must be unique.
            - class_id must refer to an existing class.
            - All fields required.
        """
        if not assessment_id or not class_id:
            return { "success": False, "error": "Assessment ID and class ID are required." }

        if assessment_id in self.assessments:
            return { "success": False, "error": "Assessment ID already exists." }

        if class_id not in self.classes:
            return { "success": False, "error": "Class does not exist." }

        assessment_info: AssessmentInfo = {
            "assessment_id": assessment_id,
            "class_id": class_id,
            "type": type,
            "date": date,
            "description": description
        }
        self.assessments[assessment_id] = assessment_info
        return { "success": True, "message": "Assessment added successfully." }

    def assign_grade(
        self, 
        student_id: str, 
        assessment_id: str, 
        grade_value: str, 
        remark: str = ""
    ) -> dict:
        """
        Assign or update a grade for a student for a specific assessment.

        Args:
            student_id (str): The ID of the student.
            assessment_id (str): The ID of the assessment.
            grade_value (str): The grade value to assign (e.g., "A", "85", etc.).
            remark (str, optional): Comment or remark on the grade.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Grade assigned/updated for student X on assessment Y."
                } 
                or 
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The student_id must exist.
            - The assessment_id must exist.
            - The student must be enrolled in the class to which the assessment belongs.
            - Updates grade if it already exists, otherwise creates.
        """
        # Check that the student exists
        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist"}
    
        # Check that the assessment exists
        if assessment_id not in self.assessments:
            return {"success": False, "error": "Assessment does not exist"}
    
        # Get the class for the assessment
        assessment = self.assessments[assessment_id]
        assessment_class_id = assessment["class_id"]
    
        # Is the student enrolled in the class?
        is_enrolled = any(
            enrollment["student_id"] == student_id and enrollment["class_id"] == assessment_class_id
            for enrollment in self.enrollments
        )
        if not is_enrolled:
            return {"success": False, "error": "Student is not enrolled in the class for this assessment"}
    
        # Does the grade already exist?
        grade_found = False
        for grade in self.grades:
            if grade["student_id"] == student_id and grade["assessment_id"] == assessment_id:
                grade["grade_value"] = grade_value
                grade["remark"] = remark
                grade_found = True
                break
        if grade_found:
            return {
                "success": True,
                "message": f"Grade updated for student {student_id} on assessment {assessment_id}."
            }
        else:
            new_grade: GradeInfo = {
                "student_id": student_id,
                "assessment_id": assessment_id,
                "grade_value": grade_value,
                "remark": remark
            }
            self.grades.append(new_grade)
            return {
                "success": True,
                "message": f"Grade assigned for student {student_id} on assessment {assessment_id}."
            }

    def update_student_info(self, student_id: str, updates: dict) -> dict:
        """
        Edit student details such as contact info or enrollment status.

        Args:
            student_id (str): The unique ID of the student to update.
            updates (dict): Dictionary of field-value pairs to update. Allowed fields:
                            "name", "date_of_birth", "contact_info", "enrollment_status"
                            ("student_id" cannot be updated).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Student info updated"}
                On failure:
                    {"success": False, "error": "...error reason..."}

        Constraints:
            - Student must exist.
            - Only valid StudentInfo fields except 'student_id' can be updated.
        """
        if student_id not in self.students:
            return {"success": False, "error": "Student not found"}

        valid_fields = set(self.students[student_id].keys()) - {"student_id"}
        update_fields = set(updates.keys()) & valid_fields
        if not update_fields:
            return {"success": False, "error": "No valid fields to update"}
        for key in update_fields:
            self.students[student_id][key] = updates[key]
        return {"success": True, "message": "Student info updated"}

    def update_parent_info(
        self,
        parent_id: str,
        name: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Edit parent/guardian details.

        Args:
            parent_id (str): The ID of the parent to update.
            name (str, optional): New name of the parent. Only updates if provided.
            contact_info (str, optional): New contact info. Only updates if provided.

        Returns:
            dict:
                On success: { "success": True, "message": "Parent information updated" }
                On failure: { "success": False, "error": "Parent not found" }

        Constraints:
            - Only modifies the given fields on an existing parent.
            - parent_id must exist.
        """
        if parent_id not in self.parents:
            return { "success": False, "error": "Parent not found" }

        parent = self.parents[parent_id]
        updated = False

        if name is not None:
            parent["name"] = name
            updated = True

        if contact_info is not None:
            parent["contact_info"] = contact_info
            updated = True

        # Even if nothing is updated, it's still considered a successful (no-op) operation
        return { "success": True, "message": "Parent information updated" }

    def withdraw_student_from_class(self, student_id: str, class_id: str) -> dict:
        """
        Removes a student from a class enrollment.

        Args:
            student_id (str): The unique ID of the student to withdraw.
            class_id (str): The unique ID of the class to withdraw the student from.

        Returns:
            dict: 
             - If successful: { "success": True, "message": "Student <student_id> withdrawn from class <class_id>" }
             - On error: { "success": False, "error": "<description>" }
    
        Constraints:
            - The student and class must exist.
            - Student must currently be enrolled in the class.
        """
        if student_id not in self.students:
            return { "success": False, "error": f"Student {student_id} does not exist" }
        if class_id not in self.classes:
            return { "success": False, "error": f"Class {class_id} does not exist" }

        # Check for enrollment record
        enrollment_exists = False
        for enrollment in self.enrollments:
            if enrollment['student_id'] == student_id and enrollment['class_id'] == class_id:
                enrollment_exists = True
                break

        if not enrollment_exists:
            return { "success": False, "error": f"Student {student_id} is not enrolled in class {class_id}" }

        # Remove enrollment
        self.enrollments = [
            enrollment for enrollment in self.enrollments
            if not (enrollment['student_id'] == student_id and enrollment['class_id'] == class_id)
        ]

        return {
            "success": True,
            "message": f"Student {student_id} withdrawn from class {class_id}"
        }

    def delete_grade(self, student_id: str, assessment_id: str) -> dict:
        """
        Remove a grade record for a given student and assessment from the system.

        Args:
            student_id (str): The student's unique identifier.
            assessment_id (str): The unique identifier of the assessment.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Grade record successfully deleted." }
                - On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Only deletes if a grade record for (student_id, assessment_id) exists.
        """
        found = False
        new_grades = []
        for grade in self.grades:
            if not (grade['student_id'] == student_id and grade['assessment_id'] == assessment_id):
                new_grades.append(grade)
            else:
                found = True  # Mark that we are deleting at least one record

        if not found:
            return {"success": False, "error": "Grade record not found for the given student and assessment."}
        else:
            self.grades = new_grades
            return {"success": True, "message": "Grade record successfully deleted."}

    def unlink_parent_from_student(self, parent_id: str, student_id: str) -> dict:
        """
        Remove the parent-student link for the specified parent and student.

        Args:
            parent_id (str): The parent/guardian's ID.
            student_id (str): The student's ID.

        Returns:
            dict: On success, { "success": True, "message": str }.
                  On failure, { "success": False, "error": str }.

        Constraints:
            - The (parent_id, student_id) link must exist before it can be removed.
        """
        link_found = False
        for i, link in enumerate(self.parent_student_links):
            if link["parent_id"] == parent_id and link["student_id"] == student_id:
                link_found = True
                del self.parent_student_links[i]
                return {
                    "success": True,
                    "message": f"Parent-student link between parent '{parent_id}' and student '{student_id}' removed."
                }
        return {
            "success": False,
            "error": "Parent-student link does not exist."
        }


class SchoolStudentInformationSystem(BaseEnv):
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

    def get_parent_by_name(self, **kwargs):
        return self._call_inner_tool('get_parent_by_name', kwargs)

    def get_student_by_name(self, **kwargs):
        return self._call_inner_tool('get_student_by_name', kwargs)

    def list_parents_of_student(self, **kwargs):
        return self._call_inner_tool('list_parents_of_student', kwargs)

    def list_students_of_parent(self, **kwargs):
        return self._call_inner_tool('list_students_of_parent', kwargs)

    def check_parent_student_link(self, **kwargs):
        return self._call_inner_tool('check_parent_student_link', kwargs)

    def get_student_enrollments(self, **kwargs):
        return self._call_inner_tool('get_student_enrollments', kwargs)

    def get_class_by_subject_and_student(self, **kwargs):
        return self._call_inner_tool('get_class_by_subject_and_student', kwargs)

    def get_class_info(self, **kwargs):
        return self._call_inner_tool('get_class_info', kwargs)

    def list_assessments_by_class_and_type(self, **kwargs):
        return self._call_inner_tool('list_assessments_by_class_and_type', kwargs)

    def get_grade_for_assessment(self, **kwargs):
        return self._call_inner_tool('get_grade_for_assessment', kwargs)

    def get_grades_for_student_in_subject(self, **kwargs):
        return self._call_inner_tool('get_grades_for_student_in_subject', kwargs)

    def list_assessment_results_for_student_in_class(self, **kwargs):
        return self._call_inner_tool('list_assessment_results_for_student_in_class', kwargs)

    def add_student(self, **kwargs):
        return self._call_inner_tool('add_student', kwargs)

    def add_parent(self, **kwargs):
        return self._call_inner_tool('add_parent', kwargs)

    def link_parent_to_student(self, **kwargs):
        return self._call_inner_tool('link_parent_to_student', kwargs)

    def enroll_student_in_class(self, **kwargs):
        return self._call_inner_tool('enroll_student_in_class', kwargs)

    def add_class(self, **kwargs):
        return self._call_inner_tool('add_class', kwargs)

    def add_assessment(self, **kwargs):
        return self._call_inner_tool('add_assessment', kwargs)

    def assign_grade(self, **kwargs):
        return self._call_inner_tool('assign_grade', kwargs)

    def update_student_info(self, **kwargs):
        return self._call_inner_tool('update_student_info', kwargs)

    def update_parent_info(self, **kwargs):
        return self._call_inner_tool('update_parent_info', kwargs)

    def withdraw_student_from_class(self, **kwargs):
        return self._call_inner_tool('withdraw_student_from_class', kwargs)

    def delete_grade(self, **kwargs):
        return self._call_inner_tool('delete_grade', kwargs)

    def unlink_parent_from_student(self, **kwargs):
        return self._call_inner_tool('unlink_parent_from_student', kwargs)

