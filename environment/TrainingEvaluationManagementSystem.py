# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



# Represents an individual enrolled in the training program
class ParticipantInfo(TypedDict):
    participant_id: str
    name: str
    contact_info: str
    enrollment_status: str

# Represents a training session held as part of the program
class SessionInfo(TypedDict):
    session_id: str
    date: str  # Expected to be ISO format or similar
    topic: str
    instructor_id: str

# Represents a specific criterion for evaluations (e.g., Communication, Teamwork)
class EvaluationCriterionInfo(TypedDict):
    criterion_id: str
    name: str
    description: str

# Represents a score given to a participant for a specific criterion in a session
class EvaluationInfo(TypedDict):
    evaluation_id: str
    session_id: str
    participant_id: str
    criterion_id: str
    score: float
    evaluator_id: str
    timestamp: str  # or float for epoch timestamp

# Represents an instructor
class InstructorInfo(TypedDict):
    instructor_id: str
    name: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for training program participant evaluation management.

        Constraints:
        - Each Evaluation links a participant, session, and criterion, and contains a single score.
        - Score values must be within an allowed range (e.g., 0–10).
        - Sessions must have valid dates and cannot be duplicated.
        - Evaluations can only be recorded for participants enrolled in the program and for criteria defined in the system.
        """

        # Participants: {participant_id: ParticipantInfo}
        self.participants: Dict[str, ParticipantInfo] = {}

        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}

        # Evaluation Criteria: {criterion_id: EvaluationCriterionInfo}
        self.evaluation_criteria: Dict[str, EvaluationCriterionInfo] = {}

        # Evaluations: {evaluation_id: EvaluationInfo}
        self.evaluations: Dict[str, EvaluationInfo] = {}

        # Instructors: {instructor_id: InstructorInfo}
        self.instructors: Dict[str, InstructorInfo] = {}

    def get_session_by_date(self, date: str) -> dict:
        """
        Retrieve the session (session_id, topic, and instructor info) for the specified date.

        Args:
            date (str): ISO-formatted date string to look up the session.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": {
                        "session_id": str,
                        "topic": str,
                        "instructor_id": str,
                        "instructor_name": str
                    }
                }
                Failure: {
                    "success": False,
                    "error": "No session found for the specified date" | "Instructor not found"
                }

        Constraints:
            - At most one session per date (as per system constraints).
            - Instructor information is returned alongside session info.
        """
        # Find session with given date
        for session in self.sessions.values():
            if session["date"] == date:
                instructor_id = session.get("instructor_id")
                instructor_info = self.instructors.get(instructor_id)
                if not instructor_info:
                    return {
                        "success": False,
                        "error": "Instructor not found"
                    }
                return {
                    "success": True,
                    "data": {
                        "session_id": session["session_id"],
                        "topic": session["topic"],
                        "instructor_id": instructor_id,
                        "instructor_name": instructor_info["name"]
                    }
                }

        return {
            "success": False,
            "error": "No session found for the specified date"
        }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve all information for a given session_id.

        Args:
            session_id (str): The unique identifier of the session.

        Returns:
            dict: {
                "success": True,
                "data": SessionInfo
            }
            or
            {
                "success": False,
                "error": str  # "Session not found"
            }

        Constraints:
            - The session_id must exist in the system.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session not found" }
        return { "success": True, "data": session }

    def list_all_sessions(self) -> dict:
        """
        List all sessions in the training program.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SessionInfo]  # List of all session records (may be empty list)
            }

        Constraints:
            - None (query only, no constraints apply to the operation itself)
        """
        sessions_list = list(self.sessions.values())
        return { "success": True, "data": sessions_list }

    def list_enrolled_participants(self) -> dict:
        """
        Retrieve all participants with an active/enrolled status.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo],  # All participants where enrollment_status == "enrolled"
            }

        Constraints:
            - Only participants with 'enrollment_status' equal to "enrolled" are returned.
        """
        # The status to be considered as enrolled/active
        ENROLLED_STATUS = "enrolled"

        enrolled_participants = [
            participant for participant in self.participants.values()
            if participant.get("enrollment_status", "").lower() == ENROLLED_STATUS
        ]

        return {"success": True, "data": enrolled_participants}

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve information for a participant by participant_id.

        Args:
            participant_id (str): The unique ID of the participant.

        Returns:
            dict: {
                "success": True,
                "data": ParticipantInfo  # Information about the participant
            }
            OR
            {
                "success": False,
                "error": str  # Error message if participant_id is not found
            }

        Constraints:
            - The participant_id must exist in the system.
        """
        participant = self.participants.get(participant_id)
        if participant is None:
            return { "success": False, "error": "Participant not found" }
        return { "success": True, "data": participant }

    def list_evaluation_criteria(self) -> dict:
        """
        List all evaluation criteria defined in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[EvaluationCriterionInfo],  # May be empty if no criteria exist
            }
        """
        result = list(self.evaluation_criteria.values())
        return {
            "success": True,
            "data": result
        }

    def get_criterion_by_name(self, criterion_name: str) -> dict:
        """
        Retrieve the evaluation criterion details based on the specified criterion name.

        Args:
            criterion_name (str): The name of the evaluation criterion.

        Returns:
            dict: If found,
                {
                    "success": True,
                    "data": EvaluationCriterionInfo
                }
                If not found,
                {
                    "success": False,
                    "error": "Criterion with the specified name does not exist."
                }

        Constraints:
            - Name must match exactly.
            - Returns the first match if multiple criteria share the same name (should be unique).
        """
        for criterion in self.evaluation_criteria.values():
            if criterion["name"] == criterion_name:
                return { "success": True, "data": criterion }
        return { "success": False, "error": "Criterion with the specified name does not exist." }

    def get_evaluations_for_participant(
        self,
        participant_id: str,
        session_id: str = None,
        criterion_id: str = None
    ) -> dict:
        """
        Retrieve all evaluations for a given participant, optionally filtered by session or evaluation criterion.

        Args:
            participant_id (str): ID of the participant whose evaluations to retrieve.
            session_id (str, optional): If provided, filter evaluations to this session only.
            criterion_id (str, optional): If provided, filter evaluations to this criterion only.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": List[EvaluationInfo]}
                    (List may be empty if no matching evaluations.)
                On failure:
                    {"success": False, "error": <reason>}
        Constraints:
            - Participant must exist in the system.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": "Participant does not exist"}

        results = [
            eval_info for eval_info in self.evaluations.values()
            if eval_info["participant_id"] == participant_id
            and (session_id is None or eval_info["session_id"] == session_id)
            and (criterion_id is None or eval_info["criterion_id"] == criterion_id)
        ]
        return {"success": True, "data": results}

    def get_evaluations_for_session(self, session_id: str) -> dict:
        """
        List all evaluations recorded for a specific session.

        Args:
            session_id (str): Unique identifier of the session.

        Returns:
            dict: {
                "success": True,
                "data": List[EvaluationInfo]  # List of evaluations for the session (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., session does not exist)
            }
    
        Constraints:
            - The session_id must refer to an existing session in the system.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }

        session_evaluations = [
            eval_info
            for eval_info in self.evaluations.values()
            if eval_info["session_id"] == session_id
        ]

        return { "success": True, "data": session_evaluations }

    def get_evaluations_by_criterion(self, criterion_id: str) -> dict:
        """
        Retrieve all evaluation records related to the specified evaluation criterion.

        Args:
            criterion_id (str): Unique identifier for the evaluation criterion.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[EvaluationInfo]  # possibly empty if no evaluations found
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure ("Criterion not found")
                  }

        Constraints:
            - criterion_id must exist in the system.
        """
        if criterion_id not in self.evaluation_criteria:
            return { "success": False, "error": "Criterion not found" }

        result = [
            evaluation
            for evaluation in self.evaluations.values()
            if evaluation["criterion_id"] == criterion_id
        ]

        return { "success": True, "data": result }

    def get_evaluator_by_id(self, instructor_id: str) -> dict:
        """
        Fetch instructor/evaluator information given an instructor_id.

        Args:
            instructor_id (str): Unique identifier for the instructor/evaluator.

        Returns:
            dict:
                - {"success": True, "data": InstructorInfo}
                  if the instructor is found
                - {"success": False, "error": "Instructor not found"}
                  if not present in the system

        Constraints:
            - instructor_id must exist in the system.
        """
        if instructor_id in self.instructors:
            return {"success": True, "data": self.instructors[instructor_id]}
        else:
            return {"success": False, "error": "Instructor not found"}

    def get_evaluation_by_id(self, evaluation_id: str) -> dict:
        """
        Retrieve the full details of a specific evaluation record by its ID.

        Args:
            evaluation_id (str): The unique identifier of the evaluation to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": EvaluationInfo  # All details about the evaluation
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Evaluation not found"
                    }
        """
        evaluation = self.evaluations.get(evaluation_id)
        if evaluation is None:
            return { "success": False, "error": "Evaluation not found" }
        else:
            return { "success": True, "data": evaluation }

    def add_evaluation(
        self,
        participant_id: str,
        session_id: str,
        criterion_id: str,
        score: float,
        evaluator_id: str,
        timestamp: str,
        evaluation_id: str = None
    ) -> dict:
        """
        Record a new evaluation for a participant, session, and criterion, specifying score and evaluator.

        Args:
            participant_id (str): ID of the participant being evaluated.
            session_id (str): ID of the session.
            criterion_id (str): ID of the evaluation criterion.
            score (float): Score assigned (must be between 0 and 10 inclusive).
            evaluator_id (str): ID of the instructor/evaluator.
            timestamp (str): Time when the evaluation is recorded.
            evaluation_id (str, optional): If not supplied, generated automatically.

        Returns:
            dict: {
                "success": True,
                "message": "Evaluation successfully recorded for participant <id> in session <id>."
            }
            or
            dict: {
                "success": False,
                "error": str
            }

        Constraints:
            - Participant, session, criterion, and evaluator must exist.
            - Participant must be enrolled.
            - Score must be in [0, 10].
            - Cannot record duplicate evaluation for the same (participant_id, session_id, criterion_id).
        """
        # Check participant exists and is enrolled
        p = self.participants.get(participant_id)
        if not p:
            return { "success": False, "error": "Participant does not exist." }
        if str(p.get("enrollment_status", "")).lower() != "enrolled":
            return { "success": False, "error": "Participant is not currently enrolled." }

        # Check session exists
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist." }
        # Check criterion exists
        if criterion_id not in self.evaluation_criteria:
            return { "success": False, "error": "Evaluation criterion does not exist." }
        # Check evaluator exists
        if evaluator_id not in self.instructors:
            return { "success": False, "error": "Evaluator (instructor) does not exist." }

        # Check score in range
        if not (0 <= score <= 10):
            return { "success": False, "error": "Score must be between 0 and 10." }

        # Check for duplicate evaluation (same participant, session, criterion)
        for ev in self.evaluations.values():
            if (
                ev["participant_id"] == participant_id and
                ev["session_id"] == session_id and
                ev["criterion_id"] == criterion_id
            ):
                return { "success": False, "error": "An evaluation for this participant, session, and criterion already exists." }

        # Generate evaluation_id if not given
        if not evaluation_id:
            evaluation_id = str(uuid.uuid4())

        # Add to evaluations
        self.evaluations[evaluation_id] = {
            "evaluation_id": evaluation_id,
            "participant_id": participant_id,
            "session_id": session_id,
            "criterion_id": criterion_id,
            "score": score,
            "evaluator_id": evaluator_id,
            "timestamp": timestamp,
        }

        return {
            "success": True,
            "message": f"Evaluation successfully recorded for participant {participant_id} in session {session_id}."
        }

    def update_evaluation_score(self, evaluation_id: str, new_score: float) -> dict:
        """
        Modify the score in an existing evaluation record.

        Args:
            evaluation_id (str): The unique ID of the evaluation record to update.
            new_score (float): The new score to set (must be between 0 and 10 inclusive).

        Returns:
            dict: {
                "success": True,
                "message": "Evaluation score updated successfully.",
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Evaluation must exist.
            - Score must be within the allowed range 0–10 inclusive.
        """
        # Check existence
        if evaluation_id not in self.evaluations:
            return { "success": False, "error": "Evaluation ID does not exist." }

        # Validate score range (assuming 0–10 as per the specification)
        if not (0 <= new_score <= 10):
            return { "success": False, "error": "Score must be between 0 and 10 inclusive." }

        # Update score
        self.evaluations[evaluation_id]["score"] = new_score

        # (Optional: Could update timestamp to now, if that were part of the requirements)

        return { "success": True, "message": "Evaluation score updated successfully." }

    def delete_evaluation(self, evaluation_id: str) -> dict:
        """
        Remove an evaluation record from the system by its unique evaluation_id.

        Args:
            evaluation_id (str): The unique identifier of the evaluation record to be deleted.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Evaluation record deleted."}
                - On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - Only deletes an existing evaluation.
        """
        if evaluation_id not in self.evaluations:
            return {"success": False, "error": "Evaluation does not exist."}
        del self.evaluations[evaluation_id]
        return {"success": True, "message": "Evaluation record deleted."}

    def add_session(self, session_id: str, date: str, topic: str, instructor_id: str) -> dict:
        """
        Register a new training session.

        Args:
            session_id (str): Unique identifier for the session.
            date (str): Session date (should be in ISO format, e.g., '2023-05-15').
            topic (str): The topic/title of the session.
            instructor_id (str): Instructor responsible for the session. Must exist.

        Returns:
            dict: 
                On success: { "success": True, "message": "Session <session_id> added successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - session_id must be unique.
            - instructor_id must exist.
            - date must be present/valid (ISO format if possible).
            - topic must be non-empty.
            - Sessions cannot be duplicated.
        """
        # Check for session_id uniqueness
        if session_id in self.sessions:
            return { "success": False, "error": "Session ID already exists." }

        # Basic validation for required fields
        if not (date and isinstance(date, str)):
            return { "success": False, "error": "Date is required and must be a non-empty string." }
        if not (topic and isinstance(topic, str)):
            return { "success": False, "error": "Topic is required and must be a non-empty string." }
        if not (instructor_id and isinstance(instructor_id, str)):
            return { "success": False, "error": "Instructor ID is required and must be a non-empty string." }

        # Check instructor exists
        if instructor_id not in self.instructors:
            return { "success": False, "error": "Instructor does not exist." }

        # Check for duplicate sessions (same date & instructor)
        for sess in self.sessions.values():
            if sess["date"] == date and sess["instructor_id"] == instructor_id:
                return { "success": False, "error": "A session with this date and instructor already exists." }

        # Optionally, validate date format (ISO). Skipping actual parse for brevity, but could use datetime.fromisoformat

        # Add the new session
        self.sessions[session_id] = {
            "session_id": session_id,
            "date": date,
            "topic": topic,
            "instructor_id": instructor_id
        }

        return { "success": True, "message": f"Session {session_id} added successfully." }

    def update_session(
        self,
        session_id: str,
        date: str = None,
        topic: str = None,
        instructor_id: str = None
    ) -> dict:
        """
        Update the information for an existing session (date, topic, instructor).

        Args:
            session_id (str): The ID of the session to update (required).
            date (str, optional): The new date for the session.
            topic (str, optional): The new topic for the session.
            instructor_id (str, optional): The new instructor ID.

        Returns:
            dict: {
                "success": True,
                "message": "Session <session_id> updated successfully."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - session_id must exist.
            - Sessions must not duplicate an existing (date + topic) combination (except itself).
            - instructor_id (if provided) must exist.
            - At least one of date, topic, or instructor_id must be provided for update.
        """
        # Check session exists
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found."}
    
        session = self.sessions[session_id]

        # If nothing to update
        if date is None and topic is None and instructor_id is None:
            return {"success": False, "error": "No fields to update were provided."}

        # Determine new values (use current if not provided)
        new_date = date if date is not None else session["date"]
        new_topic = topic if topic is not None else session["topic"]

        # Check for duplicate session (date + topic), excluding itself
        for sid, sess in self.sessions.items():
            if sid != session_id and sess["date"] == new_date and sess["topic"] == new_topic:
                return {"success": False, "error": "A session with the same date and topic already exists."}

        # Optionally update instructor
        if instructor_id is not None:
            if instructor_id not in self.instructors:
                return {"success": False, "error": "Instructor ID does not exist."}
            session["instructor_id"] = instructor_id

        # Update date and topic
        if date is not None:
            session["date"] = date
        if topic is not None:
            session["topic"] = topic

        # Commit changes
        self.sessions[session_id] = session

        return {"success": True, "message": f"Session {session_id} updated successfully."}

    def enroll_participant(self, participant_id: str) -> dict:
        """
        Change the enrollment status of a participant to 'enrolled'.

        Args:
            participant_id (str): The ID of the participant to enroll.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Participant <id> successfully enrolled." }
              - On error: { "success": False, "error": reason }

        Constraints:
            - Participant must exist in the system.
            - If already enrolled, does not change status and returns error.
        """
        participant = self.participants.get(participant_id)
        if not participant:
            return { "success": False, "error": "Participant not found." }

        if participant.get("enrollment_status") == "enrolled":
            return { "success": False, "error": "Participant is already enrolled." }

        participant["enrollment_status"] = "enrolled"
        self.participants[participant_id] = participant
        return {
            "success": True,
            "message": f"Participant {participant_id} successfully enrolled."
        }

    def unenroll_participant(self, participant_id: str) -> dict:
        """
        Mark a participant as not enrolled/inactive.

        Args:
            participant_id (str): The ID of the participant to unenroll.

        Returns:
            dict: {
                "success": True,
                "message": "Participant marked as not enrolled."
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., participant not found)
            }

        Constraints:
            - Participant must exist.
            - Updates the 'enrollment_status' to 'inactive'.
        """
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant not found" }

        # Mark as inactive (not enrolled)
        self.participants[participant_id]["enrollment_status"] = "inactive"
        return { "success": True, "message": "Participant marked as not enrolled." }

    def add_evaluation_criterion(self, criterion_id: str, name: str, description: str) -> dict:
        """
        Add a new evaluation criterion to the system.

        Args:
            criterion_id (str): Unique identifier for the new criterion.
            name (str): Name of the evaluation criterion.
            description (str): Description of the evaluation criterion.

        Returns:
            dict: {
                "success": True,
                "message": "Evaluation criterion added successfully."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - criterion_id must be unique (not already in self.evaluation_criteria).
            - criterion_id and name must be non-empty strings.
        """
        if not criterion_id or not name:
            return {
                "success": False,
                "error": "criterion_id and name must be provided and non-empty."
            }
        if criterion_id in self.evaluation_criteria:
            return {
                "success": False,
                "error": "Criterion ID already exists."
            }
        self.evaluation_criteria[criterion_id] = {
            "criterion_id": criterion_id,
            "name": name,
            "description": description
        }
        return {
            "success": True,
            "message": "Evaluation criterion added successfully."
        }

    def update_evaluation_criterion(
        self, 
        criterion_id: str, 
        name: str = None, 
        description: str = None
    ) -> dict:
        """
        Update the name and/or description of an existing evaluation criterion.

        Args:
            criterion_id (str): The ID of the evaluation criterion to update.
            name (str, optional): New name for the criterion.
            description (str, optional): New description for the criterion.

        Returns:
            dict: 
                - On success:
                    { "success": True, "message": "Evaluation criterion updated" }
                - On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The criterion must exist in the system.
            - At least one of the parameters (name, description) must be supplied.
        """
        if criterion_id not in self.evaluation_criteria:
            return { "success": False, "error": "Criterion does not exist" }
        if name is None and description is None:
            return { "success": False, "error": "No update parameters provided" }
    
        criterion = self.evaluation_criteria[criterion_id]
        if name is not None:
            criterion["name"] = name
        if description is not None:
            criterion["description"] = description

        self.evaluation_criteria[criterion_id] = criterion
        return { "success": True, "message": "Evaluation criterion updated" }

    def add_instructor(self, instructor_id: str, name: str, contact_info: str) -> dict:
        """
        Register a new instructor.
    
        Args:
            instructor_id (str): Unique identifier for the instructor.
            name (str): Name of the instructor.
            contact_info (str): Instructor's contact information.
    
        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "Instructor added successfully."
                }
                On failure: {
                    "success": False, 
                    "error": str
                }
    
        Constraints:
            - instructor_id must be unique in the system.
        """
        # Check for duplicate instructor
        if instructor_id in self.instructors:
            return {"success": False, "error": "Instructor ID already exists."}

        # Optional: Validate non-empty fields
        if not instructor_id or not name:
            return {"success": False, "error": "Instructor ID and name are required."}
    
        instructor_info = {
            "instructor_id": instructor_id,
            "name": name,
            "contact_info": contact_info
        }
        self.instructors[instructor_id] = instructor_info
        return {"success": True, "message": "Instructor added successfully."}

    def update_instructor(
        self,
        instructor_id: str,
        name: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Update the instructor's information (name and/or contact_info).

        Args:
            instructor_id (str): The unique identifier for the instructor to update.
            name (str, optional): New name for the instructor.
            contact_info (str, optional): New contact information for the instructor.

        Returns:
            dict:
                - On success: { "success": True, "message": "Instructor info updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - instructor_id must exist in the system.
            - At least one update field must be provided.
            - instructor_id itself is not changed.
        """
        instructor = self.instructors.get(instructor_id)
        if not instructor:
            return { "success": False, "error": "Instructor not found." }

        if name is None and contact_info is None:
            return { "success": False, "error": "No update data provided." }

        updated = False
        if name is not None:
            instructor["name"] = name
            updated = True
        if contact_info is not None:
            instructor["contact_info"] = contact_info
            updated = True

        if updated:
            self.instructors[instructor_id] = instructor
            return { "success": True, "message": "Instructor info updated." }
        else:
            # Fallback, though this path is unlikely
            return { "success": False, "error": "No fields updated." }


class TrainingEvaluationManagementSystem(BaseEnv):
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

    def get_session_by_date(self, **kwargs):
        return self._call_inner_tool('get_session_by_date', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def list_all_sessions(self, **kwargs):
        return self._call_inner_tool('list_all_sessions', kwargs)

    def list_enrolled_participants(self, **kwargs):
        return self._call_inner_tool('list_enrolled_participants', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def list_evaluation_criteria(self, **kwargs):
        return self._call_inner_tool('list_evaluation_criteria', kwargs)

    def get_criterion_by_name(self, **kwargs):
        return self._call_inner_tool('get_criterion_by_name', kwargs)

    def get_evaluations_for_participant(self, **kwargs):
        return self._call_inner_tool('get_evaluations_for_participant', kwargs)

    def get_evaluations_for_session(self, **kwargs):
        return self._call_inner_tool('get_evaluations_for_session', kwargs)

    def get_evaluations_by_criterion(self, **kwargs):
        return self._call_inner_tool('get_evaluations_by_criterion', kwargs)

    def get_evaluator_by_id(self, **kwargs):
        return self._call_inner_tool('get_evaluator_by_id', kwargs)

    def get_evaluation_by_id(self, **kwargs):
        return self._call_inner_tool('get_evaluation_by_id', kwargs)

    def add_evaluation(self, **kwargs):
        return self._call_inner_tool('add_evaluation', kwargs)

    def update_evaluation_score(self, **kwargs):
        return self._call_inner_tool('update_evaluation_score', kwargs)

    def delete_evaluation(self, **kwargs):
        return self._call_inner_tool('delete_evaluation', kwargs)

    def add_session(self, **kwargs):
        return self._call_inner_tool('add_session', kwargs)

    def update_session(self, **kwargs):
        return self._call_inner_tool('update_session', kwargs)

    def enroll_participant(self, **kwargs):
        return self._call_inner_tool('enroll_participant', kwargs)

    def unenroll_participant(self, **kwargs):
        return self._call_inner_tool('unenroll_participant', kwargs)

    def add_evaluation_criterion(self, **kwargs):
        return self._call_inner_tool('add_evaluation_criterion', kwargs)

    def update_evaluation_criterion(self, **kwargs):
        return self._call_inner_tool('update_evaluation_criterion', kwargs)

    def add_instructor(self, **kwargs):
        return self._call_inner_tool('add_instructor', kwargs)

    def update_instructor(self, **kwargs):
        return self._call_inner_tool('update_instructor', kwargs)

