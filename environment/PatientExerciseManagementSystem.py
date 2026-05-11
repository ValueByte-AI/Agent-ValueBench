# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    medical_profile: str

class ExerciseInfo(TypedDict):
    exercise_id: str
    name: str
    description: str
    category_id: str

class ExerciseCategoryInfo(TypedDict):
    category_id: str
    category_name: str

class PatientExerciseAssignmentInfo(TypedDict):
    assignment_id: str
    patient_id: str
    exercise_id: str
    assigned_date: str
    prescribed_by: str
    status: str  # e.g., "active", "completed"

class ExerciseLogInfo(TypedDict):
    log_id: str
    patient_id: str
    exercise_id: str
    date: str
    duration: float
    repetitions: int
    notes: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State tracking for Patient Exercise Management System.

        Constraints:
        - Each exercise must belong to exactly one category.
        - Only assigned exercises should be logged as performed by a patient.
        - Each patient can only be assigned an exercise once at a given time unless re-prescribed.
        - Exercise logs must reference valid patient and exercise IDs.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}
        # Exercises: {exercise_id: ExerciseInfo}
        self.exercises: Dict[str, ExerciseInfo] = {}
        # Exercise Categories: {category_id: ExerciseCategoryInfo}
        self.exercise_categories: Dict[str, ExerciseCategoryInfo] = {}
        # Exercise Assignments: {assignment_id: PatientExerciseAssignmentInfo}
        self.assignments: Dict[str, PatientExerciseAssignmentInfo] = {}
        # Exercise Logs: {log_id: ExerciseLogInfo}
        self.exercise_logs: Dict[str, ExerciseLogInfo] = {}

    def get_patient_info(self, patient_id: str) -> dict:
        """
        Retrieve profile and medical information for a given patient by patient_id.
    
        Args:
            patient_id (str): Identifier of the patient.
        Returns:
            dict:
                - success: True and data: PatientInfo if found.
                - success: False and error: "Patient not found" if not found.
        Constraints:
            - The patient_id must exist in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def list_all_patients(self) -> dict:
        """
        Retrieve a list of all registered patients.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of all patients (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.patients.values())
        }

    def get_category_by_name(self, category_name: str) -> dict:
        """
        Look up and return the details for an exercise category given its name.

        Args:
            category_name (str): The name of the exercise category (e.g., "cardio").

        Returns:
            dict:
                success (bool): True if found, False otherwise.
                data (ExerciseCategoryInfo): On success, the matching category info.
                error (str): On failure, error message.

        Constraints:
            - Category names must match exactly (case-sensitive).
        """
        for cat in self.exercise_categories.values():
            if cat["category_name"] == category_name:
                return {"success": True, "data": cat}

        return {"success": False, "error": "Category not found"}

    def list_exercise_categories(self) -> dict:
        """
        Retrieve a list of all exercise categories in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ExerciseCategoryInfo],  # list of all exercise category dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # description of failure, if any issue occurs
            }

        Constraints:
            - None; simply returns all category records.
        """
        try:
            categories = list(self.exercise_categories.values())
            return { "success": True, "data": categories }
        except Exception as e:
            return { "success": False, "error": f"Unexpected error: {str(e)}" }

    def get_exercises_by_category(self, category_id: str) -> dict:
        """
        Retrieve all exercises belonging to a specified category_id.

        Args:
            category_id (str): The exercise category identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ExerciseInfo],  # All exercises with this category_id (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., 'Category does not exist'
            }

        Constraints:
            - The given category_id must exist in the system.
            - Exercises each have exactly one category (guaranteed by model).
        """
        if category_id not in self.exercise_categories:
            return {"success": False, "error": "Category does not exist"}

        result = [
            exercise for exercise in self.exercises.values()
            if exercise["category_id"] == category_id
        ]

        return {"success": True, "data": result}

    def get_exercise_info(self, exercise_id: str) -> dict:
        """
        Retrieve the details of a specific exercise by its exercise_id.

        Args:
            exercise_id (str): The unique ID of the exercise to retrieve.

        Returns:
            dict:
                - On success: {"success": True, "data": ExerciseInfo}
                - On failure: {"success": False, "error": "Exercise not found"}

        Constraints:
            - The exercise_id must exist in the system.
        """
        exercise = self.exercises.get(exercise_id)
        if exercise is None:
            return { "success": False, "error": "Exercise not found" }

        return { "success": True, "data": exercise }

    def list_patient_assignments(self, patient_id: str) -> dict:
        """
        List all current and past exercise assignments for a given patient.

        Args:
            patient_id (str): Unique identifier for the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientExerciseAssignmentInfo],  # All assignments (could be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error message if patient not found
            }

        Constraints:
            - The given patient_id must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient ID does not exist" }

        assignments = [
            assignment for assignment in self.assignments.values()
            if assignment["patient_id"] == patient_id
        ]

        return { "success": True, "data": assignments }

    def list_assignments_by_status(self, patient_id: str, status: str) -> dict:
        """
        List all exercise assignments for a given patient filtered by assignment status.

        Args:
            patient_id (str): ID of the patient whose assignments are to be listed.
            status (str): Assignment status to filter by (e.g., "active", "completed").

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": List[PatientExerciseAssignmentInfo]
                }
                If patient_id does not exist,
                {
                    "success": False,
                    "error": "Patient does not exist"
                }

        Constraints:
            - Patient must exist in system.
            - Assignments are filtered by exact status match (case-sensitive).
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        filtered = [
            assignment for assignment in self.assignments.values()
            if assignment["patient_id"] == patient_id and assignment["status"] == status
        ]
        return { "success": True, "data": filtered }

    def list_patient_exercises_by_category(self, patient_id: str, category_id: str) -> dict:
        """
        List all exercise assignments for a patient that are part of a specific exercise category.

        Args:
            patient_id (str): The identifier of the patient.
            category_id (str): The identifier of the exercise category.

        Returns:
            dict: 
                { "success": True, "data": List[PatientExerciseAssignmentInfo] }
                or
                { "success": False, "error": str }

        Constraints:
            - Patient must exist.
            - Category must exist.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        if category_id not in self.exercise_categories:
            return {"success": False, "error": "Category does not exist"}

        assignments_in_category = []
        for assignment in self.assignments.values():
            if assignment["patient_id"] != patient_id:
                continue
            exercise_id = assignment["exercise_id"]
            exercise_info = self.exercises.get(exercise_id)
            if exercise_info and exercise_info["category_id"] == category_id:
                assignments_in_category.append(assignment)
        return {"success": True, "data": assignments_in_category}

    def get_assignment_info(self, assignment_id: str) -> dict:
        """
        Retrieve details of a specific exercise assignment by assignment_id.

        Args:
            assignment_id (str): Unique ID for the exercise assignment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PatientExerciseAssignmentInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Assignment not found."
                    }

        Constraints:
            - assignment_id must exist in the system.
        """
        assignment = self.assignments.get(assignment_id)
        if assignment is None:
            return {"success": False, "error": "Assignment not found."}
        return {"success": True, "data": assignment}

    def list_patient_exercise_logs(self, patient_id: str) -> dict:
        """
        List all exercise log entries for the specified patient.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict:
                - If patient_id exists:
                    { "success": True, "data": List[ExerciseLogInfo] }
                - If patient_id does not exist:
                    { "success": False, "error": "Patient does not exist" }

        Constraints:
            - patient_id must exist in self.patients.
            - Returns all ExerciseLogInfo entries with matching patient_id.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        logs = [
            log
            for log in self.exercise_logs.values()
            if log["patient_id"] == patient_id
        ]
        return { "success": True, "data": logs }

    def list_logs_for_assignment(self, assignment_id: str) -> dict:
        """
        List all exercise log entries corresponding to a given assignment.

        Args:
            assignment_id (str): The unique ID of the patient-exercise assignment.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ExerciseLogInfo]  # List of logs where patient_id and exercise_id match assignment.
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error (e.g., assignment not found)
                }

        Constraints:
            - assignment_id must exist in self.assignments.
            - Output only includes logs where both patient_id and exercise_id match the assignment.
        """
        if assignment_id not in self.assignments:
            return {"success": False, "error": "Assignment not found"}

        assignment = self.assignments[assignment_id]
        patient_id = assignment["patient_id"]
        exercise_id = assignment["exercise_id"]

        logs = [
            log_info for log_info in self.exercise_logs.values()
            if log_info["patient_id"] == patient_id and log_info["exercise_id"] == exercise_id
        ]

        return {"success": True, "data": logs}

    def get_exercise_log_info(self, log_id: str) -> dict:
        """
        Retrieve details of a specific exercise log entry by its log_id.

        Args:
            log_id (str): The unique identifier for the exercise log entry.

        Returns:
            dict:
                - If found: { "success": True, "data": ExerciseLogInfo }
                - If not found: { "success": False, "error": "Log entry not found" }

        Constraints:
            - log_id must exist in the system.
            - No permission or patient/exercise validity checks are performed here.
        """
        log_info = self.exercise_logs.get(log_id)
        if log_info is None:
            return { "success": False, "error": "Log entry not found" }
        return { "success": True, "data": log_info }

    def assign_exercise_to_patient(
        self,
        patient_id: str,
        exercise_id: str,
        assigned_date: str,
        prescribed_by: str
    ) -> dict:
        """
        Assign an exercise to a patient, enforcing constraints:
        - Each patient can only be assigned an exercise once at a time unless re-prescribed.
        - Each exercise must belong to exactly one valid category.

        Args:
            patient_id (str): Unique ID of the patient.
            exercise_id (str): Unique ID of the exercise to assign.
            assigned_date (str): Date of assignment (ISO string).
            prescribed_by (str): Name/ID of prescriber.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Exercise assigned successfully",
                    "assignment_id": <new_assignment_id>
                }
                Failure: {
                    "success": False,
                    "error": <reason>
                }
        """
        # Check patient existence
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        # Check exercise existence
        if exercise_id not in self.exercises:
            return { "success": False, "error": "Exercise does not exist" }

        exercise = self.exercises[exercise_id]

        # Check exercise category existence/validity
        category_id = exercise.get("category_id")
        if (not category_id) or (category_id not in self.exercise_categories):
            return { "success": False, "error": "Exercise is not linked to a valid category" }
    
        # Check for existing active assignment of this exercise for the patient
        for assignment in self.assignments.values():
            if (assignment["patient_id"] == patient_id and
                assignment["exercise_id"] == exercise_id and
                assignment["status"] == "active"):
                return { "success": False, "error": "Active assignment for this exercise already exists for patient" }
    
        # Generate a unique assignment_id
        assignment_id = str(uuid.uuid4())

        new_assignment = {
            "assignment_id": assignment_id,
            "patient_id": patient_id,
            "exercise_id": exercise_id,
            "assigned_date": assigned_date,
            "prescribed_by": prescribed_by,
            "status": "active"
        }
        self.assignments[assignment_id] = new_assignment

        return {
            "success": True,
            "message": "Exercise assigned successfully",
            "assignment_id": assignment_id
        }

    def complete_exercise_assignment(self, assignment_id: str) -> dict:
        """
        Mark an exercise assignment as completed for a patient.

        Args:
            assignment_id (str): Unique identifier of the patient exercise assignment to complete.

        Returns:
            dict: {
                "success": True,
                "message": "Assignment <assignment_id> marked as completed."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Assignment must exist.
            - Assignment must not already be completed.
        """
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return { "success": False, "error": "Assignment not found." }
        if assignment["status"] == "completed":
            return { "success": False, "error": "Assignment is already completed." }
        assignment["status"] = "completed"
        # (Timestamps not tracked in this attribute. If the design includes completion time, update here.)
        self.assignments[assignment_id] = assignment  # Should not be necessary for dict, but for explicitness.
        return { "success": True, "message": f"Assignment {assignment_id} marked as completed." }

    def log_exercise_performance(
        self,
        log_id: str,
        patient_id: str,
        exercise_id: str,
        date: str,
        duration: float,
        repetitions: int,
        notes: str
    ) -> dict:
        """
        Add a new exercise performance log for a patient and exercise.

        Args:
            log_id (str): Unique identifier for the log entry.
            patient_id (str): Patient's ID.
            exercise_id (str): Exercise's ID.
            date (str): Date of performance (ISO format suggested).
            duration (float): Duration of the exercise (minutes).
            repetitions (int): Repetitions completed.
            notes (str): Free text notes.

        Returns:
            dict: {
                "success": True,
                "message": "Exercise performance logged successfully."
            }
            or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - log_id must be unique.
            - Both patient_id and exercise_id must be valid.
            - Only assigned exercises (active/completed) can be logged for the given patient.
            - Exercise logs must reference valid patient and exercise IDs.
            - Duration must be non-negative.
            - Repetitions must be non-negative.
        """
        if log_id in self.exercise_logs:
            return {"success": False, "error": "Log ID already exists."}

        if patient_id not in self.patients:
            return {"success": False, "error": "Invalid patient_id."}

        if exercise_id not in self.exercises:
            return {"success": False, "error": "Invalid exercise_id."}

        if duration < 0:
            return {"success": False, "error": "Duration cannot be negative."}
        if repetitions < 0:
            return {"success": False, "error": "Repetitions cannot be negative."}

        # Check if the patient has an assignment for this exercise
        assignment_found = False
        for a in self.assignments.values():
            if a['patient_id'] == patient_id and a['exercise_id'] == exercise_id:
                assignment_found = True
                break
        if not assignment_found:
            return {"success": False, "error": "No exercise assignment found for patient and exercise."}

        self.exercise_logs[log_id] = {
            "log_id": log_id,
            "patient_id": patient_id,
            "exercise_id": exercise_id,
            "date": date,
            "duration": duration,
            "repetitions": repetitions,
            "notes": notes
        }

        return {"success": True, "message": "Exercise performance logged successfully."}

    def update_exercise_log(
        self,
        log_id: str,
        duration: float = None,
        repetitions: int = None,
        notes: str = None
    ) -> dict:
        """
        Update (modify) the duration, repetitions, and/or notes for an existing exercise log entry.

        Args:
            log_id (str): Unique identifier of the exercise log to update.
            duration (float, optional): New duration value (minutes/hours as per system).
            repetitions (int, optional): New repetitions value.
            notes (str, optional): New notes.

        Returns:
            dict: {
                "success": True,
                "message": "Exercise log updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - log_id must exist in the system.
            - No constraint against updating any/all fields; type checking is performed.
            - If no fields are given, this is treated as a successful no-op.
        """
        log = self.exercise_logs.get(log_id)
        if log is None:
            return { "success": False, "error": "Exercise log does not exist." }

        updated = False

        if duration is not None:
            if not isinstance(duration, (int, float)):
                return { "success": False, "error": "Duration must be a number." }
            log["duration"] = float(duration)
            updated = True

        if repetitions is not None:
            if not isinstance(repetitions, int):
                return { "success": False, "error": "Repetitions must be an integer." }
            log["repetitions"] = repetitions
            updated = True

        if notes is not None:
            if not isinstance(notes, str):
                return { "success": False, "error": "Notes must be a string." }
            log["notes"] = notes
            updated = True

        # Even if nothing was updated, considered success (no-op)
        return { "success": True, "message": "Exercise log updated successfully." }


    def reassign_exercise(
        self, 
        patient_id: str, 
        exercise_id: str, 
        assigned_date: str, 
        prescribed_by: str
    ) -> dict:
        """
        Re-prescribe (assign again) an exercise to a patient, even if there is/was an existing assignment.
        Allowed per system rules, so long as the referenced patient and exercise exist.

        Args:
            patient_id (str): The patient to receive the new assignment.
            exercise_id (str): The exercise to assign.
            assigned_date (str): Date of (re-)assignment (format: YYYY-MM-DD or similar).
            prescribed_by (str): Identifier/name of the prescriber.

        Returns:
            dict: 
                Success:
                    {
                        "success": True, 
                        "message": "Exercise re-assigned to patient.",
                        "assignment_id": str  # The ID of the new assignment
                    }
                Failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Patient and exercise must exist.
            - Each assignment gets a new unique assignment_id.
            - Exercise must belong to exactly one category (enforced at exercise creation).
        """
        # Check patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        # Check exercise exists
        if exercise_id not in self.exercises:
            return {"success": False, "error": "Exercise does not exist"}
        # Generate a unique assignment_id
        while True:
            assignment_id = str(uuid.uuid4())
            if assignment_id not in self.assignments:
                break
        # Populate assignment info
        assignment_info = {
            "assignment_id": assignment_id,
            "patient_id": patient_id,
            "exercise_id": exercise_id,
            "assigned_date": assigned_date,
            "prescribed_by": prescribed_by,
            "status": "active"
        }
        self.assignments[assignment_id] = assignment_info
        return {
            "success": True,
            "message": "Exercise re-assigned to patient.",
            "assignment_id": assignment_id
        }

    def remove_exercise_assignment(self, assignment_id: str) -> dict:
        """
        Remove or cancel an exercise assignment for a patient.

        Args:
            assignment_id (str): The ID of the patient exercise assignment to remove.

        Returns:
            dict:
                - On success: {"success": True, "message": "Exercise assignment removed."}
                - On failure: {"success": False, "error": "Assignment does not exist."}

        Constraints:
            - Assignment must exist.
            - Removal is allowed regardless of assignment status or associated logs.
        """
        if assignment_id not in self.assignments:
            return {"success": False, "error": "Assignment does not exist."}

        del self.assignments[assignment_id]
        return {"success": True, "message": "Exercise assignment removed."}

    def delete_exercise_log(self, log_id: str) -> dict:
        """
        Permanently remove an exercise log entry.

        Args:
            log_id (str): The unique identifier of the exercise log to be deleted.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Exercise log <log_id> deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Exercise log with id <log_id> does not exist."
                    }

        Constraints:
            - The log_id must exist in the exercise_logs.
        """
        if log_id not in self.exercise_logs:
            return {
                "success": False,
                "error": f"Exercise log with id {log_id} does not exist."
            }

        del self.exercise_logs[log_id]
        return {
            "success": True,
            "message": f"Exercise log {log_id} deleted."
        }


class PatientExerciseManagementSystem(BaseEnv):
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

    def get_patient_info(self, **kwargs):
        return self._call_inner_tool('get_patient_info', kwargs)

    def list_all_patients(self, **kwargs):
        return self._call_inner_tool('list_all_patients', kwargs)

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def list_exercise_categories(self, **kwargs):
        return self._call_inner_tool('list_exercise_categories', kwargs)

    def get_exercises_by_category(self, **kwargs):
        return self._call_inner_tool('get_exercises_by_category', kwargs)

    def get_exercise_info(self, **kwargs):
        return self._call_inner_tool('get_exercise_info', kwargs)

    def list_patient_assignments(self, **kwargs):
        return self._call_inner_tool('list_patient_assignments', kwargs)

    def list_assignments_by_status(self, **kwargs):
        return self._call_inner_tool('list_assignments_by_status', kwargs)

    def list_patient_exercises_by_category(self, **kwargs):
        return self._call_inner_tool('list_patient_exercises_by_category', kwargs)

    def get_assignment_info(self, **kwargs):
        return self._call_inner_tool('get_assignment_info', kwargs)

    def list_patient_exercise_logs(self, **kwargs):
        return self._call_inner_tool('list_patient_exercise_logs', kwargs)

    def list_logs_for_assignment(self, **kwargs):
        return self._call_inner_tool('list_logs_for_assignment', kwargs)

    def get_exercise_log_info(self, **kwargs):
        return self._call_inner_tool('get_exercise_log_info', kwargs)

    def assign_exercise_to_patient(self, **kwargs):
        return self._call_inner_tool('assign_exercise_to_patient', kwargs)

    def complete_exercise_assignment(self, **kwargs):
        return self._call_inner_tool('complete_exercise_assignment', kwargs)

    def log_exercise_performance(self, **kwargs):
        return self._call_inner_tool('log_exercise_performance', kwargs)

    def update_exercise_log(self, **kwargs):
        return self._call_inner_tool('update_exercise_log', kwargs)

    def reassign_exercise(self, **kwargs):
        return self._call_inner_tool('reassign_exercise', kwargs)

    def remove_exercise_assignment(self, **kwargs):
        return self._call_inner_tool('remove_exercise_assignment', kwargs)

    def delete_exercise_log(self, **kwargs):
        return self._call_inner_tool('delete_exercise_log', kwargs)

