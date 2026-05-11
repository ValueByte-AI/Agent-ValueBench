# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from collections import defaultdict



class SchoolInfo(TypedDict):
    school_id: str
    name: str
    address: str  # 'add' typo corrected to 'address'

class InstructorInfo(TypedDict):
    instructor_id: str
    name: str
    contact_info: str
    employment_status: str  # 'employment_sta' typo corrected

class ClassInfo(TypedDict):
    class_id: str
    subject: str
    grade_level: str
    school_id: str

class ScheduleInfo(TypedDict):
    schedule_id: str
    class_id: str
    instructor_id: str
    date: str  # e.g., "2024-06-01"
    start_time: str  # "HH:MM"
    end_time: str
    room_num: str

class StudentInfo(TypedDict):
    student_id: str
    name: str
    enrolled_class_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Schools: {school_id: SchoolInfo}
        self.schools: Dict[str, SchoolInfo] = {}

        # Instructors: {instructor_id: InstructorInfo}
        self.instructors: Dict[str, InstructorInfo] = {}

        # Classes: {class_id: ClassInfo}
        self.classes: Dict[str, ClassInfo] = {}

        # Schedules: {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}

        # Students: {student_id: StudentInfo}
        self.students: Dict[str, StudentInfo] = {}

        # Constraints:
        # - Every scheduled class must link to an existing class, instructor, and school.
        # - An instructor can only teach one class at the same time.
        # - Schedules cannot overlap for the same classroom.
        # - Classes must be associated with a valid school.

    def get_school_by_name(self, name: str) -> dict:
        """
        Retrieve school information (including school_id) for the given school name.

        Args:
            name (str): The name of the school to search for.

        Returns:
            dict: {
                "success": True,
                "data": SchoolInfo  # Including school_id, name, address
            }
            or
            {
                "success": False,
                "error": str  # Error description: not found or ambiguity
            }

        Constraints:
            - If no school matches, return error.
            - If multiple schools with the same name, return ambiguous error.
            - Name comparison is exact (case-sensitive).
        """
        matches = [school for school in self.schools.values() if school["name"] == name]

        if len(matches) == 0:
            return { "success": False, "error": "School not found" }
        if len(matches) > 1:
            return { "success": False, "error": "Multiple schools found with the given name" }
        return { "success": True, "data": matches[0] }

    def get_instructor_by_name(self, names) -> dict:
        """
        Retrieve the profile(s) and instructor_id(s) for given instructor name(s).

        Args:
            names ( Union[str, list[str]] ): A single instructor name or a list of instructor names to match exactly.

        Returns:
            dict:
                - If success: {
                      "success": True,
                      "data": List[InstructorInfo]  # All matching instructors for all provided names.
                  }
                - If error (e.g., no names provided): {
                      "success": False,
                      "error": str
                  }

        Notes:
            - Matching is case-sensitive and exact.
            - Names may correspond to multiple instructors (results may contain duplicates).
            - If no matches are found, returns an empty list (success).
        """
        # Normalize input to a list of names
        if isinstance(names, str):
            search_names = [names]
        elif isinstance(names, list):
            if not names:
                return {"success": False, "error": "No instructor names provided."}
            search_names = names
        else:
            return {"success": False, "error": "Invalid input for instructor names."}
    
        results = [
            instructor for instructor in self.instructors.values()
            if instructor["name"] in search_names
        ]
        return {"success": True, "data": results}

    def list_classes_by_school(self, school_id: str) -> dict:
        """
        List all academic classes (ClassInfo) associated with a specific school.

        Args:
            school_id (str): The unique identifier of the school.

        Returns:
            dict: {
                "success": True,
                "data": List[ClassInfo],  # all classes for this school, list may be empty
            }
            OR
            {
                "success": False,
                "error": str  # Description of error, e.g., school does not exist.
            }

        Constraints:
            - school_id must exist in the system.
            - Only includes classes belonging to the specified school.
        """
        if school_id not in self.schools:
            return {"success": False, "error": "School does not exist"}

        result = [
            class_info
            for class_info in self.classes.values()
            if class_info["school_id"] == school_id
        ]
        return {"success": True, "data": result}

    def list_schedules_by_school(self, school_id: str) -> dict:
        """
        Retrieve all schedules linked to a specific school.

        Args:
            school_id (str): The unique identifier for the school.

        Returns:
            dict: 
                - Success: { "success": True, "data": List[ScheduleInfo] }
                - Failure: { "success": False, "error": str }

        Constraints:
            - The given school_id must exist in the system.
            - All schedules returned correspond to classes associated with this school.
        """
        if school_id not in self.schools:
            return { "success": False, "error": "School does not exist" }

        # 1. Find all class_ids in this school.
        relevant_class_ids = [class_id for class_id, class_info in self.classes.items()
                              if class_info["school_id"] == school_id]

        # 2. Find all schedules for those class_ids.
        result = [schedule for schedule in self.schedules.values()
                  if schedule["class_id"] in relevant_class_ids]

        return { "success": True, "data": result }

    def list_schedules_by_class(self, class_id: str) -> dict:
        """
        Retrieve all schedules associated with the specified class_id.

        Args:
            class_id (str): The unique identifier for the class.

        Returns:
            dict: 
                - If the class exists:
                    { "success": True, "data": List[ScheduleInfo] }
                - If the class does not exist:
                    { "success": False, "error": "Class does not exist" }
        Constraints:
            - The class_id must exist in the system.
        """
        if class_id not in self.classes:
            return { "success": False, "error": "Class does not exist" }
    
        result = [
            schedule for schedule in self.schedules.values()
            if schedule["class_id"] == class_id
        ]
        return { "success": True, "data": result }

    def list_schedules_by_instructor(self, instructor_id: str) -> dict:
        """
        Retrieve all schedules assigned to a given instructor.

        Args:
            instructor_id (str): The unique ID of the instructor.

        Returns:
            dict: {
                "success": True,
                "data": List[ScheduleInfo],  # List of schedule info dictionaries (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Instructor does not exist."
            }

        Constraints:
            - instructor_id must exist in the system.
        """
        if instructor_id not in self.instructors:
            return { "success": False, "error": "Instructor does not exist." }
    
        result = [
            sched for sched in self.schedules.values()
            if sched["instructor_id"] == instructor_id
        ]
        return { "success": True, "data": result }

    def list_schedules_by_date(self, date: str) -> dict:
        """
        Retrieve all schedule records conducted on the specified date.

        Args:
            date (str): The date in "YYYY-MM-DD" format.

        Returns:
            dict: {
                "success": True,
                "data": List[ScheduleInfo],  # List of all ScheduleInfo for the date (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. missing or invalid date)
            }

        Constraints:
            - The date must be provided and should be in "YYYY-MM-DD" format.
        """
        if not date or not isinstance(date, str):
            return {"success": False, "error": "Date parameter is required as a string."}
        # Basic format validation: YYYY-MM-DD
        parts = date.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            return {"success": False, "error": "Date format must be 'YYYY-MM-DD'."}

        schedules_on_date = [
            s for s in self.schedules.values()
            if s["date"] == date
        ]
        return {"success": True, "data": schedules_on_date}

    def filter_schedules(
        self,
        school_id: str = None,
        instructor_id: str = None,
        class_id: str = None,
        date: str = None
    ) -> dict:
        """
        Retrieve schedules matching any combination of school, instructor, class, and date criteria.

        Args:
            school_id (str, optional): School ID to filter on.
            instructor_id (str, optional): Instructor ID to filter on.
            class_id (str, optional): Class ID to filter on.
            date (str, optional): Date (YYYY-MM-DD) to filter on.

        Returns:
            dict: {
                'success': True,
                'data': List[ScheduleInfo]  # All matching schedules
            }
        Notes:
            - If a filter parameter is not provided, it is ignored.
            - Filtering by school_id will match only schedules whose associated class belongs to that school.
            - If a provided ID does not exist, it simply returns no matches (not an error).
        """

        # Helper: Build set of matching class_ids by school, if school_id is given
        school_class_ids = None
        if school_id is not None:
            school_class_ids = set(
                cid for cid, class_info in self.classes.items()
                if class_info["school_id"] == school_id
            )
            # If no classes match school, filter yields nothing for this filter.

        matched = []
        for sched in self.schedules.values():
            if school_id is not None:
                # Must filter by class_id belonging to the school
                if sched["class_id"] not in school_class_ids:
                    continue
            if instructor_id is not None and sched["instructor_id"] != instructor_id:
                continue
            if class_id is not None and sched["class_id"] != class_id:
                continue
            if date is not None and sched["date"] != date:
                continue
            matched.append(sched.copy())
        return {"success": True, "data": matched}

    def get_class_by_id(self, class_id: str) -> dict:
        """
        Retrieve details of a class given its class_id.

        Args:
            class_id (str): The unique identifier of the class.

        Returns:
            dict:
                - If found: { "success": True, "data": ClassInfo }
                - If not found: { "success": False, "error": "Class not found" }
        """
        class_info = self.classes.get(class_id)
        if class_info is None:
            return { "success": False, "error": "Class not found" }
        return { "success": True, "data": class_info }

    def get_instructor_by_id(self, instructor_id: str) -> dict:
        """
        Retrieve instructor details by their unique instructor_id.

        Args:
            instructor_id (str): The unique identifier for the instructor.

        Returns:
            dict: {
                "success": True,
                "data": InstructorInfo  # Instructor details (name, contact_info, employment_status, instructor_id)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., instructor not found
            }

        Constraints:
            - instructor_id must exist in the system.
        """
        instructor = self.instructors.get(instructor_id)
        if instructor is None:
            return {"success": False, "error": "Instructor not found"}
        return {"success": True, "data": instructor}

    def get_student_by_id(self, student_id: str) -> dict:
        """
        Retrieve details of a student by their `student_id`.

        Args:
            student_id (str): Unique identifier for the student.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": StudentInfo  # student details
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Student does not exist"
                    }

        Constraints:
            - The specified student_id must exist in the system.
        """
        student = self.students.get(student_id)
        if not student:
            return { "success": False, "error": "Student does not exist" }

        return { "success": True, "data": student }

    def list_students_by_class(self, class_id: str) -> dict:
        """
        List all students enrolled in a particular class.

        Args:
            class_id (str): The ID of the class for which to list students.

        Returns:
            dict: {
                "success": True,
                "data": List[StudentInfo],  # List of enrolled students (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. class ID does not exist
            }

        Constraints:
            - The class_id must exist in the system.
        """
        if class_id not in self.classes:
            return { "success": False, "error": "Class not found" }

        enrolled_students = [
            student_info
            for student_info in self.students.values()
            if student_info["enrolled_class_id"] == class_id
        ]

        return { "success": True, "data": enrolled_students }

    def get_schedule_by_id(self, schedule_id: str) -> dict:
        """
        Retrieve the full details of a schedule entry given its `schedule_id`.

        Args:
            schedule_id (str): The unique identifier of the schedule entry.

        Returns:
            dict: {
                "success": True,
                "data": ScheduleInfo  # The matching schedule's information
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure ("Schedule not found")
            }

        Constraints:
            - The schedule with the provided ID must exist in the system.
        """
        schedule = self.schedules.get(schedule_id)
        if schedule:
            return {"success": True, "data": schedule}
        else:
            return {"success": False, "error": "Schedule not found"}

    def create_school(self, school_id: str, name: str, address: str) -> dict:
        """
        Create a new school entry in the system.

        Args:
            school_id (str): Unique identifier for the new school.
            name (str): Name of the school.
            address (str): Address of the school.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "School <name> (ID: <school_id>) created successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }
        Constraints:
            - school_id must be unique.
            - school_id, name, and address must be non-empty.
        """
        if not school_id or not name or not address:
            return { "success": False, "error": "school_id, name, and address must all be provided and non-empty" }
        if school_id in self.schools:
            return { "success": False, "error": "School ID already exists" }
        school_info = {
            "school_id": school_id,
            "name": name,
            "address": address
        }
        self.schools[school_id] = school_info
        return {
            "success": True,
            "message": f"School {name} (ID: {school_id}) created successfully."
        }

    def update_school_details(self, school_id: str, name: str = None, address: str = None) -> dict:
        """
        Update the name and/or address of an existing school.

        Args:
            school_id (str): The unique identifier of the school to update.
            name (str, optional): The new name for the school (if changing).
            address (str, optional): The new address for the school (if changing).

        Returns:
            dict: {
                "success": True,
                "message": "School details updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The school must exist in the system (school_id must be valid).
            - At least one of name or address must be provided (no-op otherwise).
        """
        if school_id not in self.schools:
            return {"success": False, "error": "School not found"}

        if name is None and address is None:
            return {"success": False, "error": "Nothing to update: no name or address provided"}

        if name is not None:
            self.schools[school_id]["name"] = name
        if address is not None:
            self.schools[school_id]["address"] = address

        return {"success": True, "message": "School details updated successfully"}

    def delete_school(self, school_id: str) -> dict:
        """
        Remove a school and all dependent entities (admin-level).
        Deletes:
          - The school itself
          - All classes associated with this school
          - All schedules for those classes
          - All students enrolled in those classes

        Args:
            school_id (str): The unique ID of the school to delete.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of what was deleted
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The school must exist in self.schools
            - All classes, schedules, and students dependent should be deleted
        """
        if school_id not in self.schools:
            return {"success": False, "error": "School does not exist"}

        # Find classes associated with this school
        classes_to_delete = [cid for cid, cinfo in self.classes.items() if cinfo["school_id"] == school_id]

        # Find schedules and students associated with these classes
        schedules_to_delete = []
        students_to_delete = []
        for class_id in classes_to_delete:
            # Delete schedules linked to this class
            schedules_to_delete += [sid for sid, sinfo in self.schedules.items() if sinfo["class_id"] == class_id]
            # Delete students enrolled in this class
            students_to_delete += [sid for sid, sinfo in self.students.items() if sinfo["enrolled_class_id"] == class_id]

        # Delete schedules
        for schedule_id in schedules_to_delete:
            if schedule_id in self.schedules:
                del self.schedules[schedule_id]

        # Delete students
        for student_id in students_to_delete:
            if student_id in self.students:
                del self.students[student_id]

        # Delete classes
        for class_id in classes_to_delete:
            if class_id in self.classes:
                del self.classes[class_id]

        # Finally, delete the school
        del self.schools[school_id]

        return {
            "success": True,
            "message": f"School '{school_id}' and all associated classes ({len(classes_to_delete)}), schedules ({len(schedules_to_delete)}), and students ({len(students_to_delete)}) have been deleted."
        }

    def create_instructor(
        self,
        instructor_id: str,
        name: str,
        contact_info: str,
        employment_status: str
    ) -> dict:
        """
        Adds a new instructor to the school management system.

        Args:
            instructor_id (str): Unique identifier for the instructor.
            name (str): Full name of the instructor.
            contact_info (str): Contact information (e.g., email or phone).
            employment_status (str): Employment status (e.g., 'Active', 'On Leave').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Instructor <instructor_id> added"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The instructor_id must be unique in the system.
            - All parameters should be non-empty.
        """
        # Validate that the instructor_id is unique
        if instructor_id in self.instructors:
            return {
                "success": False,
                "error": f"Instructor with id '{instructor_id}' already exists"
            }

        # Validate required fields
        if not all([
            instructor_id and instructor_id.strip(),
            name and name.strip(),
            contact_info and contact_info.strip(),
            employment_status and employment_status.strip()
        ]):
            return {
                "success": False,
                "error": "All fields (instructor_id, name, contact_info, employment_status) are required and must be non-empty"
            }

        # Create and add the instructor
        instructor_info = {
            "instructor_id": instructor_id,
            "name": name,
            "contact_info": contact_info,
            "employment_status": employment_status
        }
        self.instructors[instructor_id] = instructor_info

        return {
            "success": True,
            "message": f"Instructor {instructor_id} added"
        }

    def update_instructor_info(
        self,
        instructor_id: str,
        name: str = None,
        contact_info: str = None,
        employment_status: str = None
    ) -> dict:
        """
        Update the profile fields (name, contact_info) or employment status of an instructor.

        Args:
            instructor_id (str): Unique identifier of the instructor to update.
            name (str, optional): New name for the instructor.
            contact_info (str, optional): New contact information.
            employment_status (str, optional): Updated employment status.

        Returns:
            dict: 
                On success: { "success": True, "message": "Instructor info updated" }
                On failure: { "success": False, "error": "Reason for failure" }
    
        Constraints:
            - The instructor must exist.
            - At least one field to update must be supplied.
        """
        if instructor_id not in self.instructors:
            return { "success": False, "error": "Instructor does not exist" }
    
        # Check any updatable field is provided
        if name is None and contact_info is None and employment_status is None:
            return { "success": False, "error": "No update fields provided" }
    
        updated = False
        instructor = self.instructors[instructor_id]
    
        if name is not None:
            instructor["name"] = name
            updated = True
        if contact_info is not None:
            instructor["contact_info"] = contact_info
            updated = True
        if employment_status is not None:
            instructor["employment_status"] = employment_status
            updated = True
    
        if updated:
            self.instructors[instructor_id] = instructor  # update dict (redundant but explicit)
            return { "success": True, "message": "Instructor info updated" }
        else:
            return { "success": False, "error": "No valid update performed" }

    def delete_instructor(self, instructor_id: str) -> dict:
        """
        Remove an instructor from the system if they have no associated schedules.

        Args:
            instructor_id (str): The unique ID of the instructor to remove.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Instructor <id> deleted." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - Cannot delete if the instructor is referenced by any schedule.
        """
        if instructor_id not in self.instructors:
            return { "success": False, "error": "Instructor not found" }
    
        # Dependency check: is instructor referenced by any schedule?
        for sch in self.schedules.values():
            if sch.get("instructor_id") == instructor_id:
                return {
                    "success": False,
                    "error": "Instructor is assigned to active schedules and cannot be deleted"
                }
    
        del self.instructors[instructor_id]
        return { "success": True, "message": f"Instructor {instructor_id} deleted." }

    def create_class(
        self,
        class_id: str,
        subject: str,
        grade_level: str,
        school_id: str
    ) -> dict:
        """
        Add a new academic class to a school.

        Args:
            class_id (str): Unique class identifier.
            subject (str): Subject for the class.
            grade_level (str): Grade level for the class.
            school_id (str): The school this class belongs to.

        Returns:
            dict: {
                "success": True,
                "message": "Class <class_id> created successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
        - class_id must be unique.
        - school_id must reference an existing school.
        - All arguments must be non-empty.
        """
        # Validate required fields
        if not all([class_id, subject, grade_level, school_id]):
            return {"success": False, "error": "All class fields are required."}

        # Ensure class_id uniqueness
        if class_id in self.classes:
            return {"success": False, "error": f"Class '{class_id}' already exists."}

        # Ensure school exists
        if school_id not in self.schools:
            return {"success": False, "error": f"School '{school_id}' does not exist."}

        # Prepare and insert new class
        new_class = {
            "class_id": class_id,
            "subject": subject,
            "grade_level": grade_level,
            "school_id": school_id,
        }
        self.classes[class_id] = new_class

        return {
            "success": True,
            "message": f"Class '{class_id}' created successfully."
        }

    def update_class_info(
        self,
        class_id: str,
        subject: str = None,
        grade_level: str = None
    ) -> dict:
        """
        Update the subject and/or grade level of a class.

        Args:
            class_id (str): The unique ID of the class to update.
            subject (str, optional): The new subject for the class.
            grade_level (str, optional): The new grade level for the class.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "<fields updated>"
                }
                On error:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - class_id must exist in the system.
            - At least one of subject or grade_level must be provided.
            - Only 'subject' and/or 'grade_level' may be updated.
        """
        if class_id not in self.classes:
            return {"success": False, "error": "Class not found"}

        if subject is None and grade_level is None:
            return {
                "success": False,
                "error": "No update fields provided. Specify subject and/or grade_level."
            }

        class_info = self.classes[class_id]
        updated_fields = []

        if subject is not None:
            if not isinstance(subject, str):
                return {"success": False, "error": "Subject must be a string"}
            class_info["subject"] = subject
            updated_fields.append("subject")
    
        if grade_level is not None:
            if not isinstance(grade_level, str):
                return {"success": False, "error": "Grade level must be a string"}
            class_info["grade_level"] = grade_level
            updated_fields.append("grade_level")

        self.classes[class_id] = class_info  # Update the dict

        msg = f"Class {class_id} updated: {', '.join(updated_fields)}."
        return {"success": True, "message": msg}

    def delete_class(self, class_id: str) -> dict:
        """
        Remove a class entry from the system after checking dependencies.

        Args:
            class_id (str): The unique identifier for the class to delete.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Class <class_id> deleted."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "<reason why deletion failed>"
                    }

        Constraints:
            - Class must exist.
            - Cannot delete if any schedules reference this class.
            - Cannot delete if any student is enrolled in this class.
        """

        # Check if class exists
        if class_id not in self.classes:
            return {"success": False, "error": "Class does not exist."}

        # Check for dependent schedules
        for sched in self.schedules.values():
            if sched["class_id"] == class_id:
                return {
                    "success": False,
                    "error": "Cannot delete class: schedules exist for this class."
                }
    
        # Check for enrolled students
        for student in self.students.values():
            if student["enrolled_class_id"] == class_id:
                return {
                    "success": False,
                    "error": "Cannot delete class: students are enrolled in this class."
                }
    
        # Passed checks, safe to delete
        del self.classes[class_id]
        return {"success": True, "message": f"Class {class_id} deleted."}

    def create_schedule(
        self,
        schedule_id: str,
        class_id: str,
        instructor_id: str,
        date: str,
        start_time: str,
        end_time: str,
        room_num: str
    ) -> dict:
        """
        Add a new schedule entry, enforcing:
          - schedule_id uniqueness,
          - valid class, instructor, and school links,
          - no time overlap for instructor or room (on same date).
    
        Args:
            schedule_id (str): Unique identifier for the new schedule.
            class_id (str): Existing class to schedule.
            instructor_id (str): Instructor for the class.
            date (str): Date of the schedule, e.g., "2024-06-01".
            start_time (str): "HH:MM" (24h format).
            end_time (str): "HH:MM".
            room_num (str): Room to assign.
        Returns:
            dict: {
                "success": True,
                "message": "Schedule created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        Constraints:
            - schedule_id must be unique.
            - class_id, instructor_id, school for class must exist.
            - instructor cannot have overlapping schedules for the same time/date.
            - room cannot be double-booked for overlapping times on the same date.
        """

        def time_overlap(s1, e1, s2, e2):
            # Returns True if (s1, e1) and (s2, e2) overlap
            return not (e1 <= s2 or e2 <= s1)

        # Uniqueness of schedule_id
        if schedule_id in self.schedules:
            return {"success": False, "error": "Schedule ID already exists."}

        # class_id must exist
        class_info = self.classes.get(class_id)
        if not class_info:
            return {"success": False, "error": "Class ID does not exist."}

        # instructor_id must exist
        if instructor_id not in self.instructors:
            return {"success": False, "error": "Instructor ID does not exist."}

        # Class's school must exist
        school_id = class_info.get("school_id")
        if not school_id or school_id not in self.schools:
            return {"success": False, "error": "School for the class does not exist."}

        # Valid times
        if start_time >= end_time:
            return {"success": False, "error": "Start time must be before end time."}

        # Check for instructor overlap and room overlap
        for sched in self.schedules.values():
            if sched["date"] != date:
                continue  # Only overlapping if same date

            # Instructor overlap
            if sched["instructor_id"] == instructor_id:
                if time_overlap(start_time, end_time, sched["start_time"], sched["end_time"]):
                    return {
                        "success": False,
                        "error": "Instructor has overlapping schedule at this time."
                    }
            # Room overlap
            if sched["room_num"] == room_num:
                if time_overlap(start_time, end_time, sched["start_time"], sched["end_time"]):
                    return {
                        "success": False,
                        "error": "Room is already booked for this time."
                    }

        # All checks passed, create the schedule
        self.schedules[schedule_id] = {
            "schedule_id": schedule_id,
            "class_id": class_id,
            "instructor_id": instructor_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "room_num": room_num
        }
        return {"success": True, "message": "Schedule created successfully."}

    def update_schedule(
        self,
        schedule_id: str,
        date: str = None,
        start_time: str = None,
        end_time: str = None,
        instructor_id: str = None,
        room_num: str = None
    ) -> dict:
        """
        Modify the date, time, instructor, or classroom for a scheduled class.

        Args:
            schedule_id (str): The ID of the schedule to update.
            date (str, optional): New date ("YYYY-MM-DD").
            start_time (str, optional): New start time ("HH:MM").
            end_time (str, optional): New end time ("HH:MM").
            instructor_id (str, optional): New instructor ID.
            room_num (str, optional): New classroom number.

        Returns:
            dict: {
                "success": True,
                "message": str  # on success
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - The schedule must exist.
            - Updated instructor must exist, and not have overlap at the new time.
            - Room cannot have a conflicting schedule at the new time.
            - The linked class must exist and be bound to a real school.
        """
        # 1. Check schedule exists
        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule does not exist."}
        schedule = self.schedules[schedule_id].copy()

        # If no updates provided, fail early
        if all(arg is None for arg in [date, start_time, end_time, instructor_id, room_num]):
            return {"success": False, "error": "No update parameters provided."}

        # Prepare proposed new values
        new_date = date if date is not None else schedule["date"]
        new_start = start_time if start_time is not None else schedule["start_time"]
        new_end = end_time if end_time is not None else schedule["end_time"]
        new_instructor = instructor_id if instructor_id is not None else schedule["instructor_id"]
        new_room = room_num if room_num is not None else schedule["room_num"]

        # Check class exists and valid school
        class_id = schedule["class_id"]
        if class_id not in self.classes:
            return {"success": False, "error": "Associated class does not exist."}
        school_id = self.classes[class_id]["school_id"]
        if school_id not in self.schools:
            return {"success": False, "error": "Associated school does not exist."}

        # Check instructor exists (if changed)
        if new_instructor not in self.instructors:
            return {"success": False, "error": "Instructor does not exist."}

        # Simple time parsing helper
        def time_overlap(start1, end1, start2, end2):
            return not (end1 <= start2 or end2 <= start1)  # if intervals overlap

        # Check instructor conflict
        for sid, sched in self.schedules.items():
            if sid == schedule_id:
                continue
            if (
                sched["date"] == new_date
                and sched["instructor_id"] == new_instructor
                and time_overlap(sched["start_time"], sched["end_time"], new_start, new_end)
            ):
                return {
                    "success": False,
                    "error": f"Instructor {new_instructor} has another class scheduled at that time."
                }

        # Check classroom conflict
        for sid, sched in self.schedules.items():
            if sid == schedule_id:
                continue
            if (
                sched["date"] == new_date
                and sched["room_num"] == new_room
                and time_overlap(sched["start_time"], sched["end_time"], new_start, new_end)
            ):
                return {
                    "success": False,
                    "error": f"Room {new_room} is already in use at that time."
                }

        # All checks passed, update schedule
        schedule["date"] = new_date
        schedule["start_time"] = new_start
        schedule["end_time"] = new_end
        schedule["instructor_id"] = new_instructor
        schedule["room_num"] = new_room
        self.schedules[schedule_id] = schedule

        return {"success": True, "message": "Schedule updated successfully."}

    def delete_schedule(self, schedule_id: str) -> dict:
        """
        Remove a schedule entry from the system.

        Args:
            schedule_id (str): The unique identifier of the schedule to delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Schedule deleted successfully." }
                On failure: { "success": False, "error": "Schedule not found." }

        Constraints:
            - The schedule_id must exist in the system.
        """
        if schedule_id not in self.schedules:
            return { "success": False, "error": "Schedule not found." }
    
        del self.schedules[schedule_id]
        return { "success": True, "message": "Schedule deleted successfully." }

    def enroll_student(self, student_id: str, name: str, enrolled_class_id: str) -> dict:
        """
        Enroll a student in a class.

        Args:
            student_id (str): Unique identifier for the student.
            name (str): Student's name.
            enrolled_class_id (str): The class ID into which the student is to be enrolled.

        Returns:
            dict: Success or failure of enrollment.
                On success: { "success": True, "message": "Student enrolled in class successfully" }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - The class must exist.
            - The student ID must be unique (not already present in the system).
        """
        # Check 1: Class must exist
        if enrolled_class_id not in self.classes:
            return { "success": False, "error": "Class does not exist" }

        # Check 2: Student ID must be unique
        if student_id in self.students:
            return { "success": False, "error": "Student ID already exists" }

        # Create StudentInfo entry
        student_info = {
            "student_id": student_id,
            "name": name,
            "enrolled_class_id": enrolled_class_id
        }
        self.students[student_id] = student_info

        return { "success": True, "message": "Student enrolled in class successfully" }

    def update_student_info(
        self,
        student_id: str,
        name: str = None,
        enrolled_class_id: str = None
    ) -> dict:
        """
        Update a student's name and/or change their class enrollment.

        Args:
            student_id (str): The unique identifier for the student.
            name (str, optional): New name for the student. If None, the name is not changed.
            enrolled_class_id (str, optional): New class to enroll the student in. If None, class is not changed.

        Returns:
            dict:
                On success: { "success": True, "message": "Student information updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - student_id must exist in the system.
            - If changing enrolled_class_id, new class_id must exist in self.classes.
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student does not exist" }

        if name is None and enrolled_class_id is None:
            return { "success": True, "message": "No updates provided" }

        # Only update if new name is given
        if name is not None:
            self.students[student_id]["name"] = name

        # Only update if a new (and valid) class id is given
        if enrolled_class_id is not None:
            if enrolled_class_id not in self.classes:
                return { "success": False, "error": "Target class does not exist" }
            self.students[student_id]["enrolled_class_id"] = enrolled_class_id

        return { "success": True, "message": "Student information updated" }

    def remove_student(self, student_id: str) -> dict:
        """
        Delete a student entry from the system.

        Args:
            student_id (str): The unique identifier of the student to remove.

        Returns:
            dict:
                - { "success": True, "message": "Student <student_id> removed." } if successful.
                - { "success": False, "error": "Student not found." } if student does not exist.

        Constraints:
            - Student must exist to be removed.
            - No additional checks are applied regarding class enrollment for removal (per current system rules).
        """
        if student_id not in self.students:
            return { "success": False, "error": "Student not found." }
        del self.students[student_id]
        return { "success": True, "message": f"Student {student_id} removed." }

    def resolve_schedule_conflicts(
        self, 
        instructor_id: str = None, 
        room_num: str = None, 
        date: str = None
    ) -> dict:
        """
        Adjust or reassign conflicting schedules for a classroom or instructor.
        At least one of instructor_id or room_num must be provided.
        Optionally, provide a date (YYYY-MM-DD) to restrict the resolution.

        Args:
            instructor_id (str, optional): The instructor to check for scheduling conflicts.
            room_num (str, optional): The classroom to check for conflicts.
            date (str, optional): The date (YYYY-MM-DD) to restrict the resolution.

        Returns:
            dict: 
                { "success": True, "message": "Resolved schedule conflicts for ..." }
                or
                { "success": False, "error": "Reason for failure" }

        Constraints:
            - Schedules cannot overlap for the same instructor or room at the same time.
            - When conflicts are found (i.e., multiple overlapping schedules), only retain the earliest, remove the rest within the conflict window.
        """
        if not instructor_id and not room_num:
            return { "success": False, "error": "Must provide at least instructor_id or room_num" }

        # Collect relevant schedules
        relevant_schedules = []
        for sched in self.schedules.values():
            if date and sched["date"] != date:
                continue
            if instructor_id and sched["instructor_id"] == instructor_id:
                relevant_schedules.append(sched)
            elif room_num and sched["room_num"] == room_num:
                relevant_schedules.append(sched)

        if not relevant_schedules:
            return { "success": False, "error": "No matching schedules found for the given scope." }

        # Helper: check time overlap
        def time_overlap(start1, end1, start2, end2):
            return not (end1 <= start2 or start1 >= end2)
    
        # We will process one dimension at a time (instructor or room), combining if both provided
        resolved_ids = set()
        # Sort by date, then by start_time
        relevant_schedules.sort(key=lambda x: (x["date"], x["start_time"]))
    
        # Keep track for reporting
        removed_ids = []

        if instructor_id:
            # Group by date
            schedules_by_date = {}
            for sched in relevant_schedules:
                if sched["instructor_id"] != instructor_id:
                    continue
                schedules_by_date.setdefault(sched["date"], []).append(sched)
            # For each date, resolve overlaps
            for sch_date, sch_list in schedules_by_date.items():
                # sort by start_time
                sch_list.sort(key=lambda x: x["start_time"])
                active = []
                for sched in sch_list:
                    overlap = False
                    for a in active:
                        if time_overlap(sched["start_time"], sched["end_time"], a["start_time"], a["end_time"]):
                            overlap = True
                            break
                    if not overlap:
                        active.append(sched)
                    else:
                        # Remove this conflicting schedule
                        removed_ids.append(sched["schedule_id"])
            # Delete in self.schedules
            for sid in removed_ids:
                self.schedules.pop(sid, None)

        if room_num:
            # Group by date
            schedules_by_date = {}
            for sched in relevant_schedules:
                if sched["room_num"] != room_num:
                    continue
                schedules_by_date.setdefault(sched["date"], []).append(sched)
            # For each date, resolve overlaps
            for sch_date, sch_list in schedules_by_date.items():
                # sort by start_time
                sch_list.sort(key=lambda x: x["start_time"])
                active = []
                for sched in sch_list:
                    overlap = False
                    for a in active:
                        if time_overlap(sched["start_time"], sched["end_time"], a["start_time"], a["end_time"]):
                            overlap = True
                            break
                    if not overlap:
                        active.append(sched)
                    else:
                        # Remove this conflicting schedule
                        removed_ids.append(sched["schedule_id"])
            for sid in removed_ids:
                self.schedules.pop(sid, None)

        if removed_ids:
            return {
                "success": True,
                "message": f"Resolved schedule conflicts. Removed conflicting schedules: {removed_ids}"
            }
        else:
            return {
                "success": True,
                "message": "No schedule conflicts detected; nothing changed."
            }

    def validate_schedule_constraints(self) -> dict:
        """
        Verify all current schedules for compliance with system constraints.

        Returns:
            dict:
                - If all constraints are satisfied:
                    { "success": True, "message": "All schedule constraints are satisfied." }
                - Else:
                    { "success": False, "error": "Descriptive error(s)" }

        Constraints validated:
            1. Every scheduled class must link to an existing class, instructor, and school.
            2. An instructor can only teach one class at the same time.
            3. Schedules cannot overlap for the same classroom (room_num).
            4. Classes must be associated with a valid school.
        """
        errors = []

        # Constraint 1: Every scheduled class must link to an existing class, instructor, and school
        for schedule in self.schedules.values():
            class_id = schedule["class_id"]
            instructor_id = schedule["instructor_id"]

            if class_id not in self.classes:
                errors.append(f"Schedule {schedule['schedule_id']} references non-existent class {class_id}.")
                continue  # Cannot check school_id if class does not exist

            if instructor_id not in self.instructors:
                errors.append(f"Schedule {schedule['schedule_id']} references non-existent instructor {instructor_id}.")

            school_id = self.classes[class_id]["school_id"]
            if school_id not in self.schools:
                errors.append(
                    f"Schedule {schedule['schedule_id']} (class {class_id}) references non-existent school {school_id}."
                )

        # Constraint 2: An instructor can only teach one class at the same time
        # For each instructor, collect their schedules by date, check for overlapping times

        def time_overlap(t1_start, t1_end, t2_start, t2_end):
            # "09:00" <= t2_end and "09:30" >= t1_start => overlap
            return not (t1_end <= t2_start or t2_end <= t1_start)

        instructor_schedules = defaultdict(lambda: defaultdict(list))  # {instructor_id: {date: [schedule, ...]}}
        for schedule in self.schedules.values():
            instructor_id = schedule["instructor_id"]
            date = schedule["date"]
            instructor_schedules[instructor_id][date].append(schedule)

        for instructor_id, date_scheds in instructor_schedules.items():
            for date, sched_list in date_scheds.items():
                sched_list_sorted = sorted(sched_list, key=lambda s: s["start_time"])
                n = len(sched_list_sorted)
                for i in range(n):
                    for j in range(i + 1, n):
                        s1 = sched_list_sorted[i]
                        s2 = sched_list_sorted[j]
                        if time_overlap(s1["start_time"], s1["end_time"], s2["start_time"], s2["end_time"]):
                            errors.append(
                                f"Instructor {instructor_id} has overlapping schedules {s1['schedule_id']} and {s2['schedule_id']} on {date}."
                            )

        # Constraint 3: Schedules cannot overlap for the same classroom
        room_schedules = defaultdict(lambda: defaultdict(list))  # {room_num: {date: [schedule, ...]}}
        for schedule in self.schedules.values():
            room_num = schedule["room_num"]
            date = schedule["date"]
            room_schedules[room_num][date].append(schedule)

        for room_num, date_scheds in room_schedules.items():
            for date, sched_list in date_scheds.items():
                sched_list_sorted = sorted(sched_list, key=lambda s: s["start_time"])
                n = len(sched_list_sorted)
                for i in range(n):
                    for j in range(i + 1, n):
                        s1 = sched_list_sorted[i]
                        s2 = sched_list_sorted[j]
                        if time_overlap(s1["start_time"], s1["end_time"], s2["start_time"], s2["end_time"]):
                            errors.append(
                                f"Room {room_num} has overlapping schedules {s1['schedule_id']} and {s2['schedule_id']} on {date}."
                            )

        # Constraint 4: Classes must be associated with a valid school
        for class_id, class_info in self.classes.items():
            school_id = class_info["school_id"]
            if school_id not in self.schools:
                errors.append(f"Class {class_id} is associated with non-existent school {school_id}.")

        if errors:
            return { "success": False, "error": "; ".join(errors) }
        return { "success": True, "message": "All schedule constraints are satisfied." }


class SchoolManagementSystem(BaseEnv):
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

    def get_school_by_name(self, **kwargs):
        return self._call_inner_tool('get_school_by_name', kwargs)

    def get_instructor_by_name(self, **kwargs):
        return self._call_inner_tool('get_instructor_by_name', kwargs)

    def list_classes_by_school(self, **kwargs):
        return self._call_inner_tool('list_classes_by_school', kwargs)

    def list_schedules_by_school(self, **kwargs):
        return self._call_inner_tool('list_schedules_by_school', kwargs)

    def list_schedules_by_class(self, **kwargs):
        return self._call_inner_tool('list_schedules_by_class', kwargs)

    def list_schedules_by_instructor(self, **kwargs):
        return self._call_inner_tool('list_schedules_by_instructor', kwargs)

    def list_schedules_by_date(self, **kwargs):
        return self._call_inner_tool('list_schedules_by_date', kwargs)

    def filter_schedules(self, **kwargs):
        return self._call_inner_tool('filter_schedules', kwargs)

    def get_class_by_id(self, **kwargs):
        return self._call_inner_tool('get_class_by_id', kwargs)

    def get_instructor_by_id(self, **kwargs):
        return self._call_inner_tool('get_instructor_by_id', kwargs)

    def get_student_by_id(self, **kwargs):
        return self._call_inner_tool('get_student_by_id', kwargs)

    def list_students_by_class(self, **kwargs):
        return self._call_inner_tool('list_students_by_class', kwargs)

    def get_schedule_by_id(self, **kwargs):
        return self._call_inner_tool('get_schedule_by_id', kwargs)

    def create_school(self, **kwargs):
        return self._call_inner_tool('create_school', kwargs)

    def update_school_details(self, **kwargs):
        return self._call_inner_tool('update_school_details', kwargs)

    def delete_school(self, **kwargs):
        return self._call_inner_tool('delete_school', kwargs)

    def create_instructor(self, **kwargs):
        return self._call_inner_tool('create_instructor', kwargs)

    def update_instructor_info(self, **kwargs):
        return self._call_inner_tool('update_instructor_info', kwargs)

    def delete_instructor(self, **kwargs):
        return self._call_inner_tool('delete_instructor', kwargs)

    def create_class(self, **kwargs):
        return self._call_inner_tool('create_class', kwargs)

    def update_class_info(self, **kwargs):
        return self._call_inner_tool('update_class_info', kwargs)

    def delete_class(self, **kwargs):
        return self._call_inner_tool('delete_class', kwargs)

    def create_schedule(self, **kwargs):
        return self._call_inner_tool('create_schedule', kwargs)

    def update_schedule(self, **kwargs):
        return self._call_inner_tool('update_schedule', kwargs)

    def delete_schedule(self, **kwargs):
        return self._call_inner_tool('delete_schedule', kwargs)

    def enroll_student(self, **kwargs):
        return self._call_inner_tool('enroll_student', kwargs)

    def update_student_info(self, **kwargs):
        return self._call_inner_tool('update_student_info', kwargs)

    def remove_student(self, **kwargs):
        return self._call_inner_tool('remove_student', kwargs)

    def resolve_schedule_conflicts(self, **kwargs):
        return self._call_inner_tool('resolve_schedule_conflicts', kwargs)

    def validate_schedule_constraints(self, **kwargs):
        return self._call_inner_tool('validate_schedule_constraints', kwargs)

