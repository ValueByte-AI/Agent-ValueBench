# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime



# Entity: Course
class CourseInfo(TypedDict):
    course_id: str
    course_name: str
    description: str
    modules: List[str]           # List of module_ids
    content_struc: str           # Description or serialized structure

# Entity: Module
class ModuleInfo(TypedDict):
    module_id: str
    course_id: str
    title: str
    lesson: List[str]            # List of lesson_ids

# Entity: Lesson
class LessonInfo(TypedDict):
    lesson_id: str
    module_id: str
    title: str
    resources: List[str]         # List of resource identifiers

# Entity: Assignment
class AssignmentInfo(TypedDict):
    assignment_id: str
    course_id: str               # May also be module_id; can be None if not linked at course level
    module_id: str               # May be empty for course-wide assignment
    description: str
    due_date: str                # Assume ISO date string

# Entity: Student
class StudentInfo(TypedDict):
    student_id: str
    name: str
    email: str
    status: str

# Entity: Enrollment
class EnrollmentInfo(TypedDict):
    enrollment_id: str
    student_id: str
    course_id: str
    enrollment_status: str
    enrollment_date: str         # Assume ISO date string

# Entity: Progress
class ProgressInfo(TypedDict):
    progress_id: str
    student_id: str
    course_id: str
    completed_lessons: List[str]
    completed_assignments: List[str]
    overall_completion_percentage: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Courses: {course_id: CourseInfo}
        self.courses: Dict[str, CourseInfo] = {}

        # Modules: {module_id: ModuleInfo}
        self.modules: Dict[str, ModuleInfo] = {}

        # Lessons: {lesson_id: LessonInfo}
        self.lessons: Dict[str, LessonInfo] = {}

        # Assignments: {assignment_id: AssignmentInfo}
        self.assignments: Dict[str, AssignmentInfo] = {}

        # Students: {student_id: StudentInfo}
        self.students: Dict[str, StudentInfo] = {}

        # Enrollments: {enrollment_id: EnrollmentInfo}
        self.enrollments: Dict[str, EnrollmentInfo] = {}

        # Progress records: {progress_id: ProgressInfo}
        self.progress: Dict[str, ProgressInfo] = {}

        # Constraints:
        # - Only enrolled students can have detailed progress tracked for a course.
        # - Courses consist of modules, which consist of lessons.
        # - Assignments may be associated with courses or modules.
        # - Progress must not exceed 100% and is always calculated based on defined course content.
        # - All referenced entities (course, student) must exist for valid enrollment and progress records.

    @staticmethod
    def _is_active_enrollment_status(status: str) -> bool:
        return (status or "").strip().lower() in {"active", "enrolled"}

    def _next_enrollment_timestamp(self) -> str:
        timestamps = []
        for enrollment in self.enrollments.values():
            raw = enrollment.get("enrollment_date")
            if not raw or not isinstance(raw, str):
                continue
            text = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
            try:
                dt = datetime.datetime.fromisoformat(text)
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            timestamps.append(dt)
        base = max(timestamps) + datetime.timedelta(seconds=1) if timestamps else datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        return base.isoformat().replace("+00:00", "Z")

    def get_course_by_name(self, course_name: str) -> dict:
        """
        Retrieve detailed course info (CourseInfo) and course_id using the course's name.

        Args:
            course_name (str): The name of the course to search for.

        Returns:
            dict:
              Success:
                {
                  "success": True,
                  "data": CourseInfo  # The first course found where course_name matches exactly.
                }
              Failure:
                {
                  "success": False,
                  "error": str  # "Course not found"
                }

        Notes:
            - If multiple courses have the same name, only the first match is returned.
            - Course name match is case-sensitive and must be exact.
        """
        for course in self.courses.values():
            if course["course_name"] == course_name:
                return { "success": True, "data": course }
        return { "success": False, "error": "Course not found" }

    def get_course_details(self, course_id: str) -> dict:
        """
        Fetch all properties of a course given its course_id, including module references and content structure.

        Args:
            course_id (str): The unique identifier of the course.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": CourseInfo  # Dict with course attributes
                }
                On failure: {
                    "success": False,
                    "error": str  # "Course not found"
                }

        Constraints:
            - The course_id must exist in the LMS.
        """
        course = self.courses.get(course_id)
        if not course:
            return {"success": False, "error": "Course not found"}
        return {"success": True, "data": course}

    def list_course_modules(self, course_id: str) -> dict:
        """
        List all modules (their IDs and titles) that belong to the specified course.

        Args:
            course_id (str): The unique course identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[{"module_id": str, "title": str}]
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Course must exist.
            - Modules listed should exist in the system; missing module IDs are skipped.
        """
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist"}

        course_info = self.courses[course_id]
        module_ids = course_info.get("modules", [])

        modules_list = []
        for mid in module_ids:
            module = self.modules.get(mid)
            if module:
                modules_list.append({
                    "module_id": module["module_id"],
                    "title": module["title"]
                })
            # Silently skip module_ids not found in self.modules

        return {"success": True, "data": modules_list}

    def get_module_details(self, module_id: str) -> dict:
        """
        Retrieve detailed information about a module given its module_id.
    
        Args:
            module_id (str): The unique identifier for the module.
        
        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": ModuleInfo  # Details of the module
                }
                On failure: {
                    "success": False,
                    "error": str
                }
            
        Constraints:
            - module_id must exist in the system.
        """
        module = self.modules.get(module_id)
        if not module:
            return {"success": False, "error": "Module not found"}
        return {"success": True, "data": module}

    def list_module_lessons(self, module_id: str) -> dict:
        """
        List all lessons (lesson_id and title) for a given module.

        Args:
            module_id (str): The ID of the module for which lessons are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[{"lesson_id": str, "title": str}]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The given module_id must exist in the system.
            - Only lessons that exist in the lessons dictionary will be included in the result.
        """
        if module_id not in self.modules:
            return { "success": False, "error": "Module not found" }

        module_info = self.modules[module_id]
        lesson_ids = module_info.get("lesson", [])
        result = []

        for lesson_id in lesson_ids:
            lesson = self.lessons.get(lesson_id)
            if lesson is not None:
                result.append({
                    "lesson_id": lesson_id,
                    "title": lesson.get("title", "")
                })

        return { "success": True, "data": result }

    def get_lesson_details(self, lesson_id: str) -> dict:
        """
        Retrieve all properties of a lesson (e.g., resources, title) by lesson_id.

        Args:
            lesson_id (str): Unique identifier for the lesson.

        Returns:
            dict: {
                "success": True,
                "data": LessonInfo,    # The lesson's property dict
            }
            or
            {
                "success": False,
                "error": str           # Error message (e.g., not found)
            }

        Constraints:
            - lesson_id must exist in the system.
        """
        lesson = self.lessons.get(lesson_id)
        if not lesson:
            return { "success": False, "error": "Lesson not found" }
        return { "success": True, "data": lesson }

    def list_course_assignments(self, course_id: str, module_id: str = None) -> dict:
        """
        Retrieve all assignments associated with a given course, optionally filtering by module.

        Args:
            course_id (str): The ID of the course whose assignments are to be listed.
            module_id (str, optional): If provided, further filters assignments to those associated with this module.

        Returns:
            dict: {
                "success": True,
                "data": List[AssignmentInfo]  # Assignments list (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: missing course or invalid module
            }

        Constraints:
            - course_id must exist.
            - If module_id is provided, it must exist.
        """
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist" }

        if module_id is not None and module_id not in self.modules:
            return { "success": False, "error": "Module does not exist" }

        # Gather all assignments with the matching course_id
        assignments = [
            assignment for assignment in self.assignments.values()
            if assignment['course_id'] == course_id
               and (module_id is None or assignment['module_id'] == module_id)
        ]

        return {"success": True, "data": assignments}

    def get_assignment_details(self, assignment_id: str) -> dict:
        """
        Retrieve the full details of an assignment by its assignment_id.

        Args:
            assignment_id (str): The unique identifier of the assignment.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": AssignmentInfo
                }
                On failure:
                {
                    "success": False,
                    "error": "Assignment not found"
                }

        Constraints:
            - The assignment_id must exist in the system.
            - No side effects; this is a pure query operation.
        """
        if assignment_id not in self.assignments:
            return { "success": False, "error": "Assignment not found" }
        return { "success": True, "data": self.assignments[assignment_id] }

    def get_student_by_id(self, student_id: str) -> dict:
        """
        Fetch basic student info for the provided student_id.

        Args:
            student_id (str): Unique identifier representing the student.

        Returns:
            dict: {
                "success": True,
                "data": StudentInfo,
            }
            or
            {
                "success": False,
                "error": "Student not found"
            }

        Constraints:
            - The given student_id must exist in the system.
        """
        student = self.students.get(student_id)
        if student is None:
            return {"success": False, "error": "Student not found"}
        return {"success": True, "data": student}

    def list_student_enrollments(self, student_id: str) -> dict:
        """
        List all enrollments for a student, including course_ids and enrollment statuses.

        Args:
            student_id (str): The student ID to query.

        Returns:
            dict: {
                "success": True,
                "data": List[EnrollmentInfo]  # List of enrollment records (may be empty if none)
            }
            OR
            {
                "success": False,
                "error": str  # Explanation of error, e.g. student does not exist
            }

        Constraints:
            - student_id must exist in the LMS.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }
    
        enrollments = [
            enrollment
            for enrollment in self.enrollments.values()
            if enrollment["student_id"] == student_id
        ]
        return { "success": True, "data": enrollments }

    def get_enrollment_status(self, student_id: str, course_id: str) -> dict:
        """
        Check if a student is enrolled in a given course and retrieve enrollment details.

        Args:
            student_id (str): Unique identifier for the student.
            course_id (str): Unique identifier for the course.

        Returns:
            dict:
                {"success": True, "data": EnrollmentInfo}  # If found
                OR
                {"success": False, "error": str}           # If student or course does not exist, or not enrolled.

        Constraints:
            - The student and course must both exist.
            - If enrolled multiple times, the latest enrollment by enrollment_date is returned.
        """
        # Verify student existence
        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist"}

        # Verify course existence
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist"}

        # Find enrollments for student-course pair
        matching_enrollments = [
            e for e in self.enrollments.values()
            if e["student_id"] == student_id and e["course_id"] == course_id
        ]
        if not matching_enrollments:
            return {"success": False, "error": "Student is not enrolled in the specified course"}

        # If multiple, return latest by enrollment_date (assuming ISO string, so string-wise max works)
        latest_enrollment = max(matching_enrollments, key=lambda e: e["enrollment_date"])

        return {"success": True, "data": latest_enrollment}

    def get_student_progress_in_course(self, student_id: str, course_id: str) -> dict:
        """
        Retrieve the progress record for a student in a given course.

        Args:
            student_id (str): The student's unique identifier.
            course_id (str): The course's unique identifier.

        Returns:
            dict:
                - On success: { "success": True, "data": ProgressInfo }
                - On failure: { "success": False, "error": str }

        Constraints:
            - Both student and course must exist.
            - Student must be enrolled in the course.
            - Only enrolled students have progress tracked for a course.
        """
        # Check if student exists
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }
        # Check if course exists
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist" }

        # Check that the student is enrolled in the course (enrollment_status can matter)
        enrolled = any(
            enroll['student_id'] == student_id
            and enroll['course_id'] == course_id
            and self._is_active_enrollment_status(enroll.get('enrollment_status'))
            for enroll in self.enrollments.values()
        )
        if not enrolled:
            return { "success": False, "error": "Student is not enrolled in the specified course" }

        # Find progress record (should be only one)
        for progress in self.progress.values():
            if progress['student_id'] == student_id and progress['course_id'] == course_id:
                return { "success": True, "data": progress }
        return { "success": False, "error": "No progress record found for the student in this course" }

    def list_all_courses(self) -> dict:
        """
        Retrieve basic info (course_id, course_name, description) for all courses in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, str]],
                    # Each dict contains: course_id, course_name, description
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - No constraints—retrieves all available course records.
        """
        result = []
        for course in self.courses.values():
            result.append({
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "description": course["description"]
            })
        return { "success": True, "data": result }

    def list_students_in_course(self, course_id: str) -> dict:
        """
        List all students (student_id and name) enrolled in a specific course.

        Args:
            course_id (str): Identifier of the course.

        Returns:
            dict: {
                "success": True,
                "data": [
                    {"student_id": str, "name": str},
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - The course must exist.
            - Only students with an enrollment for the course are listed, and only if the student exists.
        """
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist"}

        # Find enrollments linked to the course_id
        students_list = []
        for enrollment in self.enrollments.values():
            if enrollment["course_id"] == course_id:
                student_id = enrollment["student_id"]
                student = self.students.get(student_id)
                if student is not None:
                    students_list.append({
                        "student_id": student_id,
                        "name": student["name"]
                    })
        return {"success": True, "data": students_list}

    def get_progress_details(self, progress_id: str) -> dict:
        """
        Retrieve detailed information about a progress record.

        Args:
            progress_id (str): The unique identifier for the progress record.

        Returns:
            dict: {
                "success": True,
                "data": ProgressInfo,  # The progress record details
            }
            or
            {
                "success": False,
                "error": str  # Reason e.g. record not found or unlinked entities
            }

        Constraints:
            - The progress record must exist.
            - The referenced student and course should exist (robustness).
        """
        progress = self.progress.get(progress_id)
        if not progress:
            return {"success": False, "error": "Progress record not found"}

        # Robustness: referenced student and course must exist
        student_id = progress["student_id"]
        course_id = progress["course_id"]
        if student_id not in self.students:
            return {"success": False, "error": f"Referenced student '{student_id}' does not exist"}
        if course_id not in self.courses:
            return {"success": False, "error": f"Referenced course '{course_id}' does not exist"}

        return {"success": True, "data": progress}

    def enroll_student_in_course(self, student_id: str, course_id: str) -> dict:
        """
        Enroll a student in a course, creating a new enrollment record if both entities exist and not already enrolled.

        Args:
            student_id (str): The unique identifier of the student.
            course_id (str): The unique identifier of the course.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Student <student_id> enrolled in course <course_id>."
                }
                On failure,
                {
                    "success": False,
                    "error": "<error message>"
                }

        Constraints:
            - Both student and course must exist.
            - Cannot enroll the same student in the same course more than once.
        """

        # Check student existence
        if student_id not in self.students:
            return {"success": False, "error": f"Student '{student_id}' does not exist."}
        # Check course existence
        if course_id not in self.courses:
            return {"success": False, "error": f"Course '{course_id}' does not exist."}
        # Check existing enrollment state. Active/enrolled records block duplicates;
        # previously inactive records are reactivated in place.
        for enr in self.enrollments.values():
            if enr["student_id"] == student_id and enr["course_id"] == course_id:
                if self._is_active_enrollment_status(enr.get("enrollment_status")):
                    return {"success": False, "error": f"Student '{student_id}' is already enrolled in course '{course_id}'."}
                enr["enrollment_status"] = "active"
                enr["enrollment_date"] = self._next_enrollment_timestamp()
                if not any(
                    progress["student_id"] == student_id and progress["course_id"] == course_id
                    for progress in self.progress.values()
                ):
                    progress_id = f"progress_{student_id}_{course_id}"
                    suffix = 1
                    while progress_id in self.progress:
                        progress_id = f"progress_{student_id}_{course_id}_{suffix}"
                        suffix += 1
                    self.progress[progress_id] = {
                        "progress_id": progress_id,
                        "student_id": student_id,
                        "course_id": course_id,
                        "completed_lessons": [],
                        "completed_assignments": [],
                        "overall_completion_percentage": 0.0,
                    }
                return {
                    "success": True,
                    "message": f"Student '{student_id}' enrolled in course '{course_id}'."
                }
        # Generate unique enrollment_id
        enrollment_id = f"enr_{student_id}_{course_id}"
        suffix = 1
        while enrollment_id in self.enrollments:
            # In rare cases of repeat (unlikely), append a numeric suffix
            enrollment_id = f"enr_{student_id}_{course_id}_{suffix}"
            suffix += 1
        # Set enrollment data
        enrollment_info = {
            "enrollment_id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "enrollment_status": "active",
            "enrollment_date": self._next_enrollment_timestamp()
        }
        self.enrollments[enrollment_id] = enrollment_info
        if not any(
            progress["student_id"] == student_id and progress["course_id"] == course_id
            for progress in self.progress.values()
        ):
            progress_id = f"progress_{student_id}_{course_id}"
            suffix = 1
            while progress_id in self.progress:
                progress_id = f"progress_{student_id}_{course_id}_{suffix}"
                suffix += 1
            self.progress[progress_id] = {
                "progress_id": progress_id,
                "student_id": student_id,
                "course_id": course_id,
                "completed_lessons": [],
                "completed_assignments": [],
                "overall_completion_percentage": 0.0,
            }
        return {
            "success": True,
            "message": f"Student '{student_id}' enrolled in course '{course_id}'."
        }

    def unenroll_student_from_course(self, student_id: str, course_id: str) -> dict:
        """
        Remove a student's enrollment from a course and remove their progress record for the course.

        Args:
            student_id (str): ID of the student to unenroll.
            course_id (str): ID of the course from which to unenroll the student.

        Returns:
            dict: {
                "success": True,
                "message": "Student unenrolled from course."
            }
            or
            {
                "success": False,
                "error": str  # Description of error/failure
            }

        Constraints:
            - Student and course must both exist.
            - Only enrolled students can have detailed progress, so their progress record must be deleted/disabled on unenrollment.
        """
        # Verify student exists
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist." }
        # Verify course exists
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist." }
    
        # Find enrollment record
        enrollment_id_to_remove = None
        for enrollment_id, enrollment in self.enrollments.items():
            if enrollment["student_id"] == student_id and enrollment["course_id"] == course_id:
                enrollment_id_to_remove = enrollment_id
                break
        if enrollment_id_to_remove is None:
            return { "success": False, "error": "Enrollment does not exist." }

        # Remove the enrollment record
        del self.enrollments[enrollment_id_to_remove]

        # Remove any progress record for this student and course
        progress_ids_to_remove = []
        for progress_id, prog in self.progress.items():
            if prog["student_id"] == student_id and prog["course_id"] == course_id:
                progress_ids_to_remove.append(progress_id)
        for pid in progress_ids_to_remove:
            del self.progress[pid]
    
        return { "success": True, "message": "Student unenrolled from course." }

    def add_completed_lesson_to_progress(self, student_id: str, course_id: str, lesson_id: str) -> dict:
        """
        Mark a lesson as completed in the student's course progress (if enrolled and all entities exist).
    
        Args:
            student_id (str): The student's unique identifier.
            course_id (str): The course's unique identifier.
            lesson_id (str): The lesson's unique identifier.
    
        Returns:
            dict: {
                "success": True,
                "message": "Lesson marked as completed in progress record."
            }
            or
            {
                "success": False,
                "error": "<description>"
            }
    
        Constraints:
            - Only enrolled students can have progress tracked.
            - Lesson must exist and be part of the course.
            - Progress must not exceed 100% and is calculated on defined course content.
        """

        # Check existence of student, course, lesson
        if student_id not in self.students:
            return {"success": False, "error": "Student does not exist."}
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist."}
        if lesson_id not in self.lessons:
            return {"success": False, "error": "Lesson does not exist."}

        # Check that lesson belongs to course (via module)
        lesson_info = self.lessons[lesson_id]
        module_id = lesson_info["module_id"]
        if module_id not in self.modules or self.modules[module_id]["course_id"] != course_id:
            return {"success": False, "error": "Lesson does not belong to the specified course."}

        # Check for active enrollment
        enrolled = False
        for enrollment in self.enrollments.values():
            if (
                enrollment["student_id"] == student_id and
                enrollment["course_id"] == course_id and
                self._is_active_enrollment_status(enrollment.get("enrollment_status"))
            ):
                enrolled = True
                break
        if not enrolled:
            return {"success": False, "error": "Student is not actively enrolled in this course."}

        # Find corresponding progress record
        progress_record = None
        for progress in self.progress.values():
            if progress["student_id"] == student_id and progress["course_id"] == course_id:
                progress_record = progress
                break
        if not progress_record:
            return {"success": False, "error": "No progress record found for this student in course."}

        # Add completed lesson if not already in the list
        if lesson_id not in progress_record["completed_lessons"]:
            progress_record["completed_lessons"].append(lesson_id)

        # Calculate total number of lessons in the course
        course_module_ids = self.courses[course_id]["modules"]
        all_lessons = []
        for mid in course_module_ids:
            if mid in self.modules:
                all_lessons.extend(self.modules[mid]["lesson"])
        total_lessons = len(all_lessons) if all_lessons else 0

        # Update overall_completion_percentage
        if total_lessons > 0:
            completed_count = len(set(progress_record["completed_lessons"]) & set(all_lessons))
            percent = (completed_count / total_lessons) * 100
            if percent > 100:
                percent = 100.0  # Enforce constraint
            progress_record["overall_completion_percentage"] = percent
        else:
            progress_record["overall_completion_percentage"] = 0.0

        return {"success": True, "message": "Lesson marked as completed in progress record."}

    def add_completed_assignment_to_progress(self, student_id: str, course_id: str, assignment_id: str) -> dict:
        """
        Mark an assignment as completed in the student's course progress, only if student,
        course, and assignment exist, the student is actively enrolled in the course,
        and the assignment is actually part of the course/modules.

        Args:
            student_id (str): ID of the student.
            course_id (str): ID of the course.
            assignment_id (str): ID of the assignment to mark completed.

        Returns:
            dict: {
                "success": True,
                "message": "Assignment marked as completed for student in course progress."
            }
            OR
            {
                "success": False,
                "error": str  # Failure reason (nonexistent student, not enrolled, etc.)
            }

        Constraints:
            - Only enrolled students can have progress records.
            - Assignment must be linked to course/modules; no duplicates in completed_assignments.
        """
        # 1. Existence checks
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist." }
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist." }
        if assignment_id not in self.assignments:
            return { "success": False, "error": "Assignment does not exist." }

        # 2. Enrollment check (must be enrolled in this course)
        is_enrolled = False
        for enrollment in self.enrollments.values():
            if (enrollment["student_id"] == student_id and
                enrollment["course_id"] == course_id and
                self._is_active_enrollment_status(enrollment.get("enrollment_status"))):
                is_enrolled = True
                break
        if not is_enrolled:
            return { "success": False, "error": "Student is not actively enrolled in this course." }

        # 3. Progress record lookup
        progress_record = None
        for progress in self.progress.values():
            if progress["student_id"] == student_id and progress["course_id"] == course_id:
                progress_record = progress
                break
        if progress_record is None:
            return { "success": False, "error": "No progress record found for this student and course." }

        # 4. Assignment association validation (assignment for this course or its modules)
        assignment = self.assignments[assignment_id]
        is_valid_assignment = False
        if assignment["course_id"] == course_id:
            is_valid_assignment = True
        elif assignment["module_id"]:
            module_id = assignment["module_id"]
            if module_id in self.modules and self.modules[module_id]["course_id"] == course_id:
                is_valid_assignment = True
        if not is_valid_assignment:
            return { "success": False, "error": "Assignment is not linked to the specified course or its modules." }

        # 5. Check for duplicate/completed
        if assignment_id in progress_record["completed_assignments"]:
            return { "success": False, "error": "Assignment already marked as completed in progress." }

        # 6. Mark as completed
        progress_record["completed_assignments"].append(assignment_id)
        # Optionally, recalculate completion percentage here if needed.

        return {
            "success": True,
            "message": "Assignment marked as completed for student in course progress."
        }

    def update_progress_percentage(self, progress_id: str, new_percentage: float) -> dict:
        """
        Update the overall completion percentage for a student's progress record in a course.

        Args:
            progress_id (str): The unique identifier for the progress record.
            new_percentage (float): The new completion percentage to set (must be between 0 and 100).

        Returns:
            dict: Success or error message.
                - { "success": True, "message": "Progress updated successfully." }
                - { "success": False, "error": "<reason>" }

        Constraints:
            - Progress percentage must not exceed 100% or be negative.
            - The referenced progress record must exist.
            - The referenced student and course must exist.
            - The student must be currently enrolled in the course.
        """
        # 1. Find the progress record.
        progress = self.progress.get(progress_id)
        if progress is None:
            return { "success": False, "error": "Progress record not found." }

        student_id = progress["student_id"]
        course_id = progress["course_id"]

        # 2. Validate percentage range
        if not (0.0 <= new_percentage <= 100.0):
            return { "success": False, "error": "Completion percentage must be between 0 and 100." }

        # 3. Check student and course existence
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist." }
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist." }

        # 4. Ensure student is enrolled in course (look for active enrollment)
        enrolled = False
        for enrollment in self.enrollments.values():
            if (
                enrollment["student_id"] == student_id and
                enrollment["course_id"] == course_id and
                self._is_active_enrollment_status(enrollment.get("enrollment_status"))
            ):
                enrolled = True
                break
        if not enrolled:
            return { "success": False, "error": "Student is not actively enrolled in the course." }

        # 5. Perform update
        progress["overall_completion_percentage"] = new_percentage

        # 6. Return result
        return { "success": True, "message": "Progress updated successfully." }

    def create_course(
        self,
        course_id: str,
        course_name: str,
        description: str,
        content_struc: str,
        modules: list = None
    ) -> dict:
        """
        Create a new course with initial details.

        Args:
            course_id (str): Unique identifier for the new course.
            course_name (str): The name/title of the course.
            description (str): A brief description of the course.
            content_struc (str): Description/serialized structure of course content.
            modules (list, optional): List of initial module_ids (default is empty list).

        Returns:
            dict: {
                "success": True,
                "message": "Course created successfully."
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - Course ID must be unique (not already used by an existing course).
            - Does not verify that modules exist at creation; referential checks are deferred.
        """
        if course_id in self.courses:
            return {"success": False, "error": "Course with given ID already exists."}

        if modules is None:
            modules = []

        self.courses[course_id] = {
            "course_id": course_id,
            "course_name": course_name,
            "description": description,
            "modules": modules,
            "content_struc": content_struc
        }

        return {"success": True, "message": "Course created successfully."}

    def add_module_to_course(self, course_id: str, module_id: str, title: str = None) -> dict:
        """
        Add a new or existing module to a course.

        Args:
            course_id (str): The id of the course to which the module should be added.
            module_id (str): The id of the module to add.
            title (str, optional): If creating a new module, a title for the module.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Module added to course."}
                On failure:
                    {"success": False, "error": "Description of the error."}

        Constraints:
            - The course must exist.
            - A module may not belong to more than one course.
            - The module is added only once to the course's module list.
            - If creating a new module, a title is set (or placeholder if not provided).
        """
        # Check that course exists
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist."}

        # If the module already exists
        if module_id in self.modules:
            module = self.modules[module_id]
            source_course_id = module.get("course_id")
            relocatable = source_course_id in {"unassigned", "", None, "POOL_99"}
            if source_course_id != course_id and not relocatable:
                return {"success": False, "error": "Module already assigned to another course."}
            if source_course_id != course_id and relocatable:
                if source_course_id in self.courses and module_id in self.courses[source_course_id].get("modules", []):
                    self.courses[source_course_id]["modules"].remove(module_id)
                module["course_id"] = course_id
            # Avoid duplicate
            if module_id in self.courses[course_id]["modules"]:
                return {"success": False, "error": "Module already part of this course."}
            self.courses[course_id]["modules"].append(module_id)
            return {"success": True, "message": "Existing module added to course."}

        # Create a new module
        if not title:
            title = f"Module {module_id}"
        new_module = {
            "module_id": module_id,
            "course_id": course_id,
            "title": title,
            "lesson": []
        }
        self.modules[module_id] = new_module
        self.courses[course_id]["modules"].append(module_id)
        return {"success": True, "message": "New module created and added to course."}

    def add_lesson_to_module(self, module_id: str, lesson_id: str) -> dict:
        """
        Add a lesson to a module in an existing course structure.

        Args:
            module_id (str): The ID of the module to which the lesson is to be added.
            lesson_id (str): The ID of the lesson to add.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "message": "Lesson <lesson_id> added to module <module_id>"
                }
              - On failure: {
                    "success": False,
                    "error": "reason"
                }
        Constraints:
            - Both the module and lesson must exist.
            - The lesson cannot be already present in the module's lesson list.
            - The lesson's module_id should be updated to this module if mismatched.
        """
        # Check if module exists
        if module_id not in self.modules:
            return {"success": False, "error": f"Module {module_id} does not exist"}
    
        # Check if lesson exists
        if lesson_id not in self.lessons:
            return {"success": False, "error": f"Lesson {lesson_id} does not exist"}
    
        module = self.modules[module_id]
        lesson = self.lessons[lesson_id]

        # Check if lesson already in module's lesson list
        if lesson_id in module.get("lesson", []):
            return {"success": False, "error": f"Lesson {lesson_id} is already in module {module_id}"}

        # Append the lesson to the module's lesson list
        module.setdefault("lesson", []).append(lesson_id)
        self.modules[module_id] = module

        # Ensure the lesson's module_id matches this module
        if lesson.get("module_id") != module_id:
            lesson["module_id"] = module_id
            self.lessons[lesson_id] = lesson

        return {"success": True, "message": f"Lesson {lesson_id} added to module {module_id}"}

    def create_assignment(
        self,
        assignment_id: str,
        course_id: str = "",
        module_id: str = "",
        description: str = "",
        due_date: str = ""
    ) -> dict:
        """
        Create a new assignment and link it to either a course or a module.
    
        Args:
            assignment_id (str): Unique identifier for the assignment.
            course_id (str): Course to which this assignment belongs (may be empty if module_id provided).
            module_id (str): Module to which this assignment belongs (may be empty if course_id provided).
            description (str): Assignment description.
            due_date (str): Due date (ISO format).

        Returns:
            dict: {
                "success": True,
                "message": "Assignment <assignment_id> has been created."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - assignment_id must be unique.
            - At least one of course_id or module_id must be provided and must exist.
            - If both are given, both must exist.
        """
        # Check uniqueness
        if assignment_id in self.assignments:
            return {"success": False, "error": "Assignment ID already exists."}

        # Validate linkage at least one exists
        if not course_id and not module_id:
            return {"success": False, "error": "Must provide either a course_id or module_id."}

        # Validate referenced entities
        if course_id and course_id not in self.courses:
            return {"success": False, "error": f"Course ID '{course_id}' does not exist."}
        if module_id and module_id not in self.modules:
            return {"success": False, "error": f"Module ID '{module_id}' does not exist."}

        # Create the assignment
        assignment_info = {
            "assignment_id": assignment_id,
            "course_id": course_id if course_id else "",
            "module_id": module_id if module_id else "",
            "description": description,
            "due_date": due_date
        }
        self.assignments[assignment_id] = assignment_info

        return {"success": True, "message": f"Assignment {assignment_id} has been created."}

    def create_student(self, student_id: str, name: str, email: str, status: str) -> dict:
        """
        Create a new student record in the system.

        Args:
            student_id (str): Unique identifier for the student.
            name (str): Full name of the student.
            email (str): Student's email address.
            status (str): Status of the student (e.g., 'active', 'inactive').

        Returns:
            dict: {
                "success": True,
                "message": "Student <student_id> created successfully."
            }
            or
            {
                "success": False,
                "error": "Student ID already exists." or other error reason
            }

        Constraints:
            - student_id must be unique in the system.
            - All fields are required and must be non-empty.
        """
        if not student_id or not name or not email or not status:
            return {
                "success": False,
                "error": "All student fields (id, name, email, status) must be provided and non-empty."
            }
        if student_id in self.students:
            return {
                "success": False,
                "error": "Student ID already exists."
            }
        self.students[student_id] = {
            "student_id": student_id,
            "name": name,
            "email": email,
            "status": status
        }
        return {
            "success": True,
            "message": f"Student {student_id} created successfully."
        }


class LearningManagementSystem(BaseEnv):
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

    def get_course_by_name(self, **kwargs):
        return self._call_inner_tool('get_course_by_name', kwargs)

    def get_course_details(self, **kwargs):
        return self._call_inner_tool('get_course_details', kwargs)

    def list_course_modules(self, **kwargs):
        return self._call_inner_tool('list_course_modules', kwargs)

    def get_module_details(self, **kwargs):
        return self._call_inner_tool('get_module_details', kwargs)

    def list_module_lessons(self, **kwargs):
        return self._call_inner_tool('list_module_lessons', kwargs)

    def get_lesson_details(self, **kwargs):
        return self._call_inner_tool('get_lesson_details', kwargs)

    def list_course_assignments(self, **kwargs):
        return self._call_inner_tool('list_course_assignments', kwargs)

    def get_assignment_details(self, **kwargs):
        return self._call_inner_tool('get_assignment_details', kwargs)

    def get_student_by_id(self, **kwargs):
        return self._call_inner_tool('get_student_by_id', kwargs)

    def list_student_enrollments(self, **kwargs):
        return self._call_inner_tool('list_student_enrollments', kwargs)

    def get_enrollment_status(self, **kwargs):
        return self._call_inner_tool('get_enrollment_status', kwargs)

    def get_student_progress_in_course(self, **kwargs):
        return self._call_inner_tool('get_student_progress_in_course', kwargs)

    def list_all_courses(self, **kwargs):
        return self._call_inner_tool('list_all_courses', kwargs)

    def list_students_in_course(self, **kwargs):
        return self._call_inner_tool('list_students_in_course', kwargs)

    def get_progress_details(self, **kwargs):
        return self._call_inner_tool('get_progress_details', kwargs)

    def enroll_student_in_course(self, **kwargs):
        return self._call_inner_tool('enroll_student_in_course', kwargs)

    def unenroll_student_from_course(self, **kwargs):
        return self._call_inner_tool('unenroll_student_from_course', kwargs)

    def add_completed_lesson_to_progress(self, **kwargs):
        return self._call_inner_tool('add_completed_lesson_to_progress', kwargs)

    def add_completed_assignment_to_progress(self, **kwargs):
        return self._call_inner_tool('add_completed_assignment_to_progress', kwargs)

    def update_progress_percentage(self, **kwargs):
        return self._call_inner_tool('update_progress_percentage', kwargs)

    def create_course(self, **kwargs):
        return self._call_inner_tool('create_course', kwargs)

    def add_module_to_course(self, **kwargs):
        return self._call_inner_tool('add_module_to_course', kwargs)

    def add_lesson_to_module(self, **kwargs):
        return self._call_inner_tool('add_lesson_to_module', kwargs)

    def create_assignment(self, **kwargs):
        return self._call_inner_tool('create_assignment', kwargs)

    def create_student(self, **kwargs):
        return self._call_inner_tool('create_student', kwargs)
