# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional
import datetime
import uuid
from datetime import datetime



class CourseInfo(TypedDict):
    course_id: str
    title: str
    description: str
    instructor_id: str
    status: str
    created_date: str
    updated_date: str

class InstructorInfo(TypedDict):
    instructor_id: str
    name: str
    bio: str
    contact_info: str
    courses_taught: List[str]

class EnrollmentInfo(TypedDict):
    enrollment_id: str
    course_id: str
    student_id: str
    enrollment_status: str
    enrollment_date: str

class ResourceInfo(TypedDict):
    resource_id: str
    course_id: str
    type: str
    url: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        LMS Course Repository Environment

        Constraints/rules:
        - A course can only be removed if specific conditions are met (e.g., no active enrollments, or explicit permissions are granted).
        - Removing a course should also address (delete or reassign) its related resources and enrollments.
        - Each course must have a unique course_id.
        - Instructors must exist in the system before being assigned to a course.
        """

        # Courses: {course_id: CourseInfo}
        self.courses: Dict[str, CourseInfo] = {}

        # Instructors: {instructor_id: InstructorInfo}
        self.instructors: Dict[str, InstructorInfo] = {}

        # Enrollments: {enrollment_id: EnrollmentInfo}
        self.enrollments: Dict[str, EnrollmentInfo] = {}

        # Resources: {resource_id: ResourceInfo}
        self.resources: Dict[str, ResourceInfo] = {}

    def get_course_by_id(self, course_id: str) -> dict:
        """
        Retrieve full information for a specific course by course_id.

        Args:
            course_id (str): The unique identifier of the course.

        Returns:
            dict: {
                "success": True,
                "data": CourseInfo (if found)
            }
            or
            {
                "success": False,
                "error": "Course not found"
            }

        Constraints:
            - The course_id must exist in the course repository.
        """
        course = self.courses.get(course_id)
        if course is None:
            return { "success": False, "error": "Course not found" }
        return { "success": True, "data": course }

    def get_course_by_title(self, title: str) -> dict:
        """
        Retrieve information for a course by its title.

        Args:
            title (str): The title of the course to look up.

        Returns:
            dict: {
                "success": True,
                "data": CourseInfo  # course metadata if found
            }
            OR
            {
                "success": False,
                "error": str  # error message if course not found
            }
        Constraints:
            - Returns the first matching course (if multiple have the same title).
            - If not found, returns an error with success:False.
        """
        for course in self.courses.values():
            if course["title"] == title:
                return {"success": True, "data": course}
        return {"success": False, "error": "Course with specified title not found"}

    def list_courses(self) -> dict:
        """
        Retrieve a list of all courses in the repository.

        Returns:
            dict: {
                "success": True,
                "data": List[CourseInfo],  # List of all course info, may be empty if no courses
            }

        Constraints:
            - No constraints for reading/listing all courses.
        """
        all_courses = list(self.courses.values())
        return { "success": True, "data": all_courses }

    def get_courses_by_instructor(self, instructor_id: str) -> dict:
        """
        List all courses taught by a given instructor_id.

        Args:
            instructor_id (str): The instructor's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[CourseInfo],  # (Could be empty if no courses assigned)
            }
            or
            {
                "success": False,
                "error": str  # ("Instructor does not exist")
            }

        Constraints:
            - Instructor must exist in self.instructors.
        """
        if instructor_id not in self.instructors:
            return { "success": False, "error": "Instructor does not exist" }

        result = [
            course_info for course_info in self.courses.values()
            if course_info["instructor_id"] == instructor_id
        ]

        return { "success": True, "data": result }

    def get_enrollments_by_course(self, course_id: str) -> dict:
        """
        Retrieve a list of all enrollments for a specified course_id.

        Args:
            course_id (str): The unique identifier for the course.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[EnrollmentInfo],  # All enrollments for this course (may be empty)
                }
                - On failure: {
                    "success": False,
                    "error": str  # Description of the error, e.g., course does not exist
                }
    
        Constraints:
            - The given course_id must exist in the repository.
        """
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist" }

        enrollments = [
            enrollment for enrollment in self.enrollments.values()
            if enrollment["course_id"] == course_id
        ]

        return { "success": True, "data": enrollments }

    def get_active_enrollments_by_course(self, course_id: str) -> dict:
        """
        Retrieve all active enrollments for a given course.

        Args:
            course_id (str): The unique identifier of the course.

        Returns:
            dict: {
                "success": True,
                "data": List[EnrollmentInfo]  # List of enrollments where course_id matches and status is active
            }
            or
            {
                "success": False,
                "error": str  # Error message describing what went wrong
            }

        Notes:
            - "Active" enrollments are those whose enrollment_status is not "completed" or "cancelled".
            - Returns an empty list if no active enrollments are found for the course.
            - Returns an error if the course_id does not exist in the system.
        """
        if course_id not in self.courses:
            return {
                "success": False,
                "error": f"Course with id '{course_id}' does not exist"
            }

        active_enrollments = [
            enrollment for enrollment in self.enrollments.values()
            if enrollment["course_id"] == course_id and
               enrollment["enrollment_status"].lower() not in ("completed", "cancelled")
        ]

        return {
            "success": True,
            "data": active_enrollments
        }

    def get_resources_by_course(self, course_id: str) -> dict:
        """
        List all resources associated with a given course_id.

        Args:
            course_id (str): The ID of the course whose resources to retrieve.

        Returns:
            dict:
                - On success: { "success": True, "data": List[ResourceInfo] }
                - On failure: { "success": False, "error": "Course not found" }

        Constraints:
            - The course with the given course_id must exist.
        """
        if course_id not in self.courses:
            return { "success": False, "error": "Course not found" }

        resources = [
            resource_info
            for resource_info in self.resources.values()
            if resource_info["course_id"] == course_id
        ]

        return { "success": True, "data": resources }

    def get_instructor_by_id(self, instructor_id: str) -> dict:
        """
        Retrieve instructor information by instructor_id.

        Args:
            instructor_id (str): Unique identifier of the instructor.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": InstructorInfo  # Instructor's information
                }
                OR
                {
                    "success": False,
                    "error": "Instructor not found"
                }

        Constraints:
            - The instructor_id must exist in the repository.
        """
        if instructor_id in self.instructors:
            return {"success": True, "data": self.instructors[instructor_id]}
        else:
            return {"success": False, "error": "Instructor not found"}

    def check_instructor_exists(self, instructor_id: str) -> dict:
        """
        Check whether a given instructor_id exists in the instructor repository.

        Args:
            instructor_id (str): The ID of the instructor to check.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if instructor exists; False otherwise.
            }
            or (if input type is invalid)
            {
                "success": False,
                "error": str
            }

        Constraints:
            - No special constraints; just checks existence.
        """
        if not isinstance(instructor_id, str):
            return {"success": False, "error": "instructor_id must be a string"}
        exists = instructor_id in self.instructors
        return {"success": True, "exists": exists}

    def course_removal_conditions_met(self, course_id: str) -> dict:
        """
        Check if the course with the given course_id is eligible for removal,
        per the following constraint: the course has no active enrollments.

        Args:
            course_id (str): The ID of the course to check.

        Returns:
            dict: 
                - If course does not exist: {"success": False, "error": "Course does not exist"}
                - If course exists: {"success": True, "data": bool}
                    - data == True: Course can be removed (no active enrollments)
                    - data == False: Course cannot be removed (has active enrollments)
        """

        # Check course existence
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist" }

        # Search for active enrollments for this course
        for enrollment in self.enrollments.values():
            if enrollment["course_id"] == course_id and enrollment["enrollment_status"].lower() == "active":
                return { "success": True, "data": False }

        # No active enrollments found
        return { "success": True, "data": True }

    def delete_course(self, course_id: str) -> dict:
        """
        Remove a course from the system as well as all related enrollments and resources.

        Args:
            course_id (str): The ID of the course to remove.

        Returns:
            dict:
                - {"success": True, "message": "Course <id> and related data deleted successfully."}
                - {"success": False, "error": "<reason for failure>"}

        Constraints:
            - Can only delete course if 'course_removal_conditions_met(course_id)' returns True.
            - All related enrollments and resources are deleted as part of this operation.
            - Course must exist.
        """
        # Check if course exists
        if course_id not in self.courses:
            return { "success": False, "error": "Course does not exist" }

        # Check removal conditions (assume this method exists and returns bool or dict)
        # We call it and expect either a True, or a dict with success (for compatibility)
        removal_check = self.course_removal_conditions_met(course_id) \
            if hasattr(self, 'course_removal_conditions_met') else None
        if isinstance(removal_check, dict):
            if not removal_check.get('success', False):
                return { "success": False, "error": removal_check.get("error", "Removal conditions not met") }
        elif removal_check is not None and not removal_check:
            return { "success": False, "error": "Removal conditions not met for this course" }

        # Delete enrollments for this course
        if hasattr(self, 'delete_enrollments_by_course'):
            self.delete_enrollments_by_course(course_id)
        else:
            # Default: remove manually
            enrollment_ids_to_delete = [eid for eid, einfo in self.enrollments.items() if einfo["course_id"] == course_id]
            for eid in enrollment_ids_to_delete:
                del self.enrollments[eid]

        # Delete resources for this course
        if hasattr(self, 'delete_resources_by_course'):
            self.delete_resources_by_course(course_id)
        else:
            # Default: remove manually
            resource_ids_to_delete = [rid for rid, rinfo in self.resources.items() if rinfo["course_id"] == course_id]
            for rid in resource_ids_to_delete:
                del self.resources[rid]

        # Remove course_id from instructor's courses_taught
        course_info = self.courses[course_id]
        instructor_id = course_info['instructor_id']
        if instructor_id in self.instructors:
            if course_id in self.instructors[instructor_id]['courses_taught']:
                self.instructors[instructor_id]['courses_taught'].remove(course_id)

        # Finally, delete the course itself
        del self.courses[course_id]

        return { "success": True, "message": f"Course {course_id} and related data deleted successfully." }

    def delete_enrollments_by_course(self, course_id: str) -> dict:
        """
        Remove all enrollments associated with a given course_id.

        Args:
            course_id (str): The unique ID of the course for which enrollments should be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of how many enrollments were deleted
            }

        Constraints:
            - Removes all enrollment records where enrollment's course_id == the given course_id.
            - If there are no enrollments for the course, still returns success (message reflects this).
        """
        # Collect enrollment_ids to delete
        enrollment_ids_to_delete = [
            enrollment_id for enrollment_id, enrollment in self.enrollments.items()
            if enrollment["course_id"] == course_id
        ]

        num_deleted = len(enrollment_ids_to_delete)

        for eid in enrollment_ids_to_delete:
            del self.enrollments[eid]

        if num_deleted == 0:
            return {
                "success": True,
                "message": f"No enrollments found for course {course_id}. Nothing was deleted."
            }
        else:
            return {
                "success": True,
                "message": f"All ({num_deleted}) enrollments for course {course_id} deleted."
            }

    def delete_resources_by_course(self, course_id: str) -> dict:
        """
        Remove all resources associated with the given course_id.

        Args:
            course_id (str): The ID of the course whose resources should be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of resource deletions
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., course does not exist)
            }

        Constraints:
            - Course must exist in the repository.
            - All ResourceInfo entries with matching course_id will be removed.
        """
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist"}

        # Find resource_ids to delete
        to_delete = [rid for rid, res in self.resources.items() if res["course_id"] == course_id]

        for rid in to_delete:
            del self.resources[rid]

        return {
            "success": True,
            "message": f"All resources for course {course_id} deleted"
        }

    def reassign_resources_to_other_course(self, from_course_id: str, to_course_id: str) -> dict:
        """
        Reassign all resources from one course (from_course_id) to another (to_course_id).

        Args:
            from_course_id (str): The course ID whose resources will be transferred.
            to_course_id (str): The target course ID for resource reassignment.

        Returns:
            dict: {
                "success": True,
                "message": "N resources reassigned from <from_course_id> to <to_course_id>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Both the source and target course must exist.
            - If from_course_id == to_course_id, this is a no-op and succeeds.
            - Resource IDs remain unchanged.
        """
        if from_course_id not in self.courses:
            return { "success": False, "error": f"Source course_id '{from_course_id}' does not exist." }
        if to_course_id not in self.courses:
            return { "success": False, "error": f"Target course_id '{to_course_id}' does not exist." }
        if from_course_id == to_course_id:
            return { "success": True, "message": "Source and target course_id are the same. No action taken." }
    
        count = 0
        for resource in self.resources.values():
            if resource["course_id"] == from_course_id:
                resource["course_id"] = to_course_id
                count += 1

        return {
            "success": True,
            "message": f"{count} resource(s) reassigned from {from_course_id} to {to_course_id}."
        }

    def reassign_enrollments_to_other_course(self, source_course_id: str, target_course_id: str) -> dict:
        """
        Migrate all enrollments from one course to a replacement course.
    
        Args:
            source_course_id (str): The course ID from which enrollments are to be moved.
            target_course_id (str): The course ID to which enrollments are to be migrated.

        Returns:
            dict: {
                "success": True,
                "message": "Enrollments reassigned from <source_course_id> to <target_course_id>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Both source and target courses must exist.
            - An enrollment should not be migrated if it would create a duplicate
              (i.e., if that student is already enrolled in the target course).
            - Enrollment status, enrollment_id, and date remain unchanged;
              only course_id is modified.
        """
        # Check if both courses exist
        if source_course_id not in self.courses:
            return { "success": False, "error": f"Source course '{source_course_id}' does not exist" }
        if target_course_id not in self.courses:
            return { "success": False, "error": f"Target course '{target_course_id}' does not exist" }

        # Get all enrollments for the source course
        source_enrollments = [
            eid for eid, info in self.enrollments.items()
            if info["course_id"] == source_course_id
        ]

        if not source_enrollments:
            return { "success": True, "message": f"No enrollments found for course {source_course_id}. Nothing to reassign." }

        # Build set of student_ids already enrolled in the target course
        target_students = {
            info["student_id"]
            for info in self.enrollments.values()
            if info["course_id"] == target_course_id
        }

        reassigned_count = 0
        skipped_count = 0

        for eid in source_enrollments:
            enrollment = self.enrollments[eid]
            if enrollment["student_id"] in target_students:
                # Avoid duplicate enrollment for this student in target course
                skipped_count += 1
                continue
            self.enrollments[eid]["course_id"] = target_course_id
            reassigned_count += 1

        return {
            "success": True,
            "message": (
                f"Enrollments reassigned from {source_course_id} to {target_course_id}. "
                f"{reassigned_count} moved. {skipped_count} skipped to prevent duplicates."
            )
        }

    def add_course(
        self,
        course_id: str,
        title: str,
        description: str,
        instructor_id: str,
        status: str,
        created_date: str,
        updated_date: str
    ) -> dict:
        """
        Add a new course to the repository after validating unique course_id and instructor existence.

        Args:
            course_id (str): Unique identifier for the course.
            title (str): Course title.
            description (str): Course description.
            instructor_id (str): Instructor's unique identifier.
            status (str): Course status (e.g., active, archived).
            created_date (str): Course creation date.
            updated_date (str): Last update date.

        Returns:
            dict: {
                "success": True,
                "message": "Course added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - course_id must be unique (not already in self.courses)
            - instructor_id must exist in self.instructors
            - On success, instructor's courses_taught is updated
        """
        if course_id in self.courses:
            return {"success": False, "error": "Course ID already exists."}
        if instructor_id not in self.instructors:
            return {"success": False, "error": "Instructor does not exist."}
    
        new_course: CourseInfo = {
            "course_id": course_id,
            "title": title,
            "description": description,
            "instructor_id": instructor_id,
            "status": status,
            "created_date": created_date,
            "updated_date": updated_date
        }
        self.courses[course_id] = new_course

        # Update instructor's courses_taught field
        if "courses_taught" not in self.instructors[instructor_id]:
            self.instructors[instructor_id]["courses_taught"] = []
        self.instructors[instructor_id]["courses_taught"].append(course_id)

        return {"success": True, "message": "Course added successfully."}



    def update_course_info(
        self, 
        course_id: str, 
        title: Optional[str] = None, 
        description: Optional[str] = None, 
        instructor_id: Optional[str] = None, 
        status: Optional[str] = None
    ) -> dict:
        """
        Update the details of a course such as title, description, instructor_id, or status.
    
        Args:
            course_id (str): The unique identifier of the course to update.
            title (Optional[str]): New title for the course.
            description (Optional[str]): New description for the course.
            instructor_id (Optional[str]): New instructor ID for the course.
            status (Optional[str]): New status for the course ("active", "archived", etc.).
    
        Returns:
            dict: 
              On success:
                { "success": True, "message": "Course <course_id> updated successfully." }
              On failure:
                { "success": False, "error": "<error reason>" }
    
        Constraints:
            - Course must exist.
            - instructor_id, if changed, must exist.
            - At least one valid updatable field must be provided.
            - Updates the `updated_date` field to the current UTC date/time (ISO 8601).
        """
        if course_id not in self.courses:
            return { "success": False, "error": f"Course {course_id} does not exist." }
    
        course = self.courses[course_id]
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if instructor_id is not None:
            if instructor_id not in self.instructors:
                return { "success": False, "error": f"Instructor {instructor_id} does not exist." }
            updates["instructor_id"] = instructor_id
        if status is not None:
            updates["status"] = status

        # No fields to update?
        if not updates:
            return { "success": False, "error": "No updates provided." }
    
        # Apply updates
        previous_instructor_id = course.get("instructor_id")
        for k, v in updates.items():
            course[k] = v

        if "instructor_id" in updates and previous_instructor_id != instructor_id:
            if previous_instructor_id in self.instructors:
                old_courses = self.instructors[previous_instructor_id].get("courses_taught", [])
                if course_id in old_courses:
                    old_courses.remove(course_id)
            new_courses = self.instructors[instructor_id].setdefault("courses_taught", [])
            if course_id not in new_courses:
                new_courses.append(course_id)

        # Always update the updated_date timestamp
        course["updated_date"] = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

        return { "success": True, "message": f"Course {course_id} updated successfully." }

    def add_instructor(
        self,
        instructor_id: str,
        name: str,
        bio: str,
        contact_info: str,
        courses_taught: list
    ) -> dict:
        """
        Add a new instructor to the system.

        Args:
            instructor_id (str): Unique identifier for the instructor.
            name (str): Instructor's name.
            bio (str): Short biography.
            contact_info (str): Contact information.
            courses_taught (List[str]): List of course_ids the instructor teaches (must exist, can be []).

        Returns:
            dict: {
                "success": True,
                "message": "Instructor added successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - instructor_id must be unique.
            - All course_ids in courses_taught must exist.
        """
        if instructor_id in self.instructors:
            return {"success": False, "error": "Instructor with given ID already exists"}

        # Validate courses_taught
        invalid_courses = [cid for cid in courses_taught if cid not in self.courses]
        if invalid_courses:
            return {
                "success": False,
                "error": "One or more courses in courses_taught do not exist"
            }

        self.instructors[instructor_id] = {
            "instructor_id": instructor_id,
            "name": name,
            "bio": bio,
            "contact_info": contact_info,
            "courses_taught": courses_taught[:],  # Make a copy to preserve immutability
        }

        return {"success": True, "message": "Instructor added successfully"}

    def remove_instructor(self, instructor_id: str) -> dict:
        """
        Remove an instructor from the repository, only if they are not currently assigned to any courses.

        Args:
            instructor_id (str): Unique identifier of the instructor to be removed.

        Returns:
            dict: {
                "success": True,
                "message": f"Instructor {instructor_id} removed."
            }
            or
            {
                "success": False,
                "error": <reason>  # E.g., instructor assigned to courses, instructor does not exist, etc.
            }

        Constraints:
            - Instructor can only be removed if not assigned to any courses.
        """
        # Check if instructor exists
        if instructor_id not in self.instructors:
            return { "success": False, "error": f"Instructor {instructor_id} does not exist." }
    
        instructor_info = self.instructors[instructor_id]
        # Check via InstructorInfo.courses_taught (list of course_ids)
        if instructor_info.get("courses_taught"):
            if len(instructor_info["courses_taught"]) > 0:
                return {
                    "success": False,
                    "error": (
                        f"Instructor {instructor_id} cannot be removed because they are assigned to courses: "
                        f"{instructor_info['courses_taught']}"
                    )
                }
        # Double check CourseInfo, in case data is inconsistent
        assigned_courses = [
            c_id for c_id, c_info in self.courses.items()
            if c_info['instructor_id'] == instructor_id
        ]
        if assigned_courses:
            return {
                "success": False,
                "error": (
                    f"Instructor {instructor_id} cannot be removed because they are assigned to courses: "
                    f"{assigned_courses}"
                )
            }
    
        # Remove instructor
        del self.instructors[instructor_id]
        return { "success": True, "message": f"Instructor {instructor_id} removed." }

    def add_resource(
        self,
        resource_id: str,
        course_id: str,
        type: str,
        url: str,
        description: str
    ) -> dict:
        """
        Add a new resource to a course.

        Args:
            resource_id (str): Unique identifier for the new resource.
            course_id (str): Target course's unique identifier.
            type (str): Resource type (e.g., 'video', 'pdf', etc.).
            url (str): URL/location of the resource.
            description (str): Description of the resource.

        Returns:
            dict: {
                "success": True,
                "message": "Resource <resource_id> added to course <course_id>."
            } on success,
            {
                "success": False,
                "error": "reason"
            } on failure.

        Constraints:
            - resource_id must be unique (not already exist).
            - course_id must exist in the system.
        """
        if resource_id in self.resources:
            return {"success": False, "error": f"Resource ID '{resource_id}' already exists."}

        if course_id not in self.courses:
            return {"success": False, "error": f"Course ID '{course_id}' does not exist."}

        resource_info: ResourceInfo = {
            "resource_id": resource_id,
            "course_id": course_id,
            "type": type,
            "url": url,
            "description": description
        }

        self.resources[resource_id] = resource_info

        return {
            "success": True,
            "message": f"Resource '{resource_id}' added to course '{course_id}'."
        }

    def update_resource(self, resource_id: str, updates: dict) -> dict:
        """
        Update details of an existing course resource.

        Args:
            resource_id (str): Unique identifier for the resource to update.
            updates (dict): Fields to update (e.g., {'url': ..., 'description': ..., 'type': ..., 'course_id': ...})

        Returns:
            dict: 
                On success: { "success": True, "message": "Resource updated successfully" }
                On failure: { "success": False, "error": str }

        Constraints:
            - The resource must exist.
            - If updating 'course_id', the new course_id must exist.
            - No updates/no fields to update: return success but with message "No changes made".
        """
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource does not exist" }

        if not updates or not isinstance(updates, dict):
            return { "success": True, "message": "No changes made" }

        resource = self.resources[resource_id]
        allowed_fields = {'type', 'url', 'description', 'course_id'}

        made_change = False
        for key, value in updates.items():
            if key not in allowed_fields:
                continue  # Ignore unrecognized fields

            if key == 'course_id':
                if value not in self.courses:
                    return { "success": False, "error": f"Target course_id '{value}' does not exist" }
            if resource.get(key) != value:
                resource[key] = value
                made_change = True

        if made_change:
            self.resources[resource_id] = resource
            return { "success": True, "message": "Resource updated successfully" }
        else:
            return { "success": True, "message": "No changes made" }


    def add_enrollment(
        self,
        course_id: str,
        student_id: str,
        enrollment_status: str = "active",
        enrollment_date: str = None
    ) -> dict:
        """
        Enroll a student in a course.
    
        Args:
            course_id (str): The ID of the course for enrollment.
            student_id (str): The ID of the student to enroll.
            enrollment_status (str, optional): The enrollment status ("active" by default).
            enrollment_date (str, optional): The enrollment date (ISO8601 string); if None, uses current date.
        
        Returns:
            dict:
                { "success": True, "message": "Student <student_id> enrolled in course <course_id>." }
                -or-
                { "success": False, "error": <reason> }
    
        Constraints:
            - course_id must exist in the system.
            - No duplicate active enrollment for (course_id, student_id).
            - enrollment_id must be unique.
        """

        # Check for valid course_id
        if course_id not in self.courses:
            return {"success": False, "error": "Course does not exist."}
    
        # Prevent duplicate active enrollment
        for info in self.enrollments.values():
            if info["course_id"] == course_id and info["student_id"] == student_id and info["enrollment_status"] == "active":
                return {"success": False, "error": "Student is already actively enrolled in this course."}

        # Generate a unique enrollment_id
        enrollment_id = str(uuid.uuid4())

        # Set enrollment_date if omitted
        if enrollment_date is None:
            enrollment_date = datetime.utcnow().isoformat()

        enrollment_info = {
            "enrollment_id": enrollment_id,
            "course_id": course_id,
            "student_id": student_id,
            "enrollment_status": enrollment_status,
            "enrollment_date": enrollment_date,
        }

        self.enrollments[enrollment_id] = enrollment_info

        return {"success": True, "message": f"Student {student_id} enrolled in course {course_id}."}

    def remove_enrollment(self, enrollment_id: str) -> dict:
        """
        Remove a specific enrollment from the system by enrollment_id.

        Args:
            enrollment_id (str): Identifier for the enrollment to remove.

        Returns:
            dict:
                - If success: {"success": True, "message": "Enrollment <enrollment_id> removed from the system."}
                - If enrollment does not exist: {"success": False, "error": "Enrollment not found."}

        Constraints:
            - The enrollment must exist in the system to be removed.
        """
        if enrollment_id not in self.enrollments:
            return { "success": False, "error": "Enrollment not found." }
        del self.enrollments[enrollment_id]
        return { "success": True, "message": f"Enrollment {enrollment_id} removed from the system." }


class LMSCourseRepository(BaseEnv):
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
            if key in {
                "course_removal_conditions_met",
                "delete_enrollments_by_course",
                "delete_resources_by_course",
            }:
                setattr(env, f"_{key}_state", copy.deepcopy(value))
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

    def get_course_by_id(self, **kwargs):
        return self._call_inner_tool('get_course_by_id', kwargs)

    def get_course_by_title(self, **kwargs):
        return self._call_inner_tool('get_course_by_title', kwargs)

    def list_courses(self, **kwargs):
        return self._call_inner_tool('list_courses', kwargs)

    def get_courses_by_instructor(self, **kwargs):
        return self._call_inner_tool('get_courses_by_instructor', kwargs)

    def get_enrollments_by_course(self, **kwargs):
        return self._call_inner_tool('get_enrollments_by_course', kwargs)

    def get_active_enrollments_by_course(self, **kwargs):
        return self._call_inner_tool('get_active_enrollments_by_course', kwargs)

    def get_resources_by_course(self, **kwargs):
        return self._call_inner_tool('get_resources_by_course', kwargs)

    def get_instructor_by_id(self, **kwargs):
        return self._call_inner_tool('get_instructor_by_id', kwargs)

    def check_instructor_exists(self, **kwargs):
        return self._call_inner_tool('check_instructor_exists', kwargs)

    def course_removal_conditions_met(self, **kwargs):
        return self._call_inner_tool('course_removal_conditions_met', kwargs)

    def delete_course(self, **kwargs):
        return self._call_inner_tool('delete_course', kwargs)

    def delete_enrollments_by_course(self, **kwargs):
        return self._call_inner_tool('delete_enrollments_by_course', kwargs)

    def delete_resources_by_course(self, **kwargs):
        return self._call_inner_tool('delete_resources_by_course', kwargs)

    def reassign_resources_to_other_course(self, **kwargs):
        return self._call_inner_tool('reassign_resources_to_other_course', kwargs)

    def reassign_enrollments_to_other_course(self, **kwargs):
        return self._call_inner_tool('reassign_enrollments_to_other_course', kwargs)

    def add_course(self, **kwargs):
        return self._call_inner_tool('add_course', kwargs)

    def update_course_info(self, **kwargs):
        return self._call_inner_tool('update_course_info', kwargs)

    def add_instructor(self, **kwargs):
        return self._call_inner_tool('add_instructor', kwargs)

    def remove_instructor(self, **kwargs):
        return self._call_inner_tool('remove_instructor', kwargs)

    def add_resource(self, **kwargs):
        return self._call_inner_tool('add_resource', kwargs)

    def update_resource(self, **kwargs):
        return self._call_inner_tool('update_resource', kwargs)

    def add_enrollment(self, **kwargs):
        return self._call_inner_tool('add_enrollment', kwargs)

    def remove_enrollment(self, **kwargs):
        return self._call_inner_tool('remove_enrollment', kwargs)
